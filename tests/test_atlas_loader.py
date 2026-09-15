"""Tests for the atlas loader (visuals/atlas.py).

The world atlas npz decompresses to ~1.3 GB, which cannot fit in a Pi's
RAM — the loader unpacks members to raw .npy files once, then loads them
resident, bit-packing the two huge sparse masks so they fit too. Sampling a
memmap instead meant scattered page faults off the SD card on every pan, so
"is this array actually in RAM" is a behaviour worth pinning down. These
tests exercise that machinery on a small synthetic npz so they run
everywhere (CI has no atlas data).
"""
import os

import numpy as np
import pytest

from visuals.atlas import _load_atlas_arrays, _unpack_atlas, _unpack_dir_for


@pytest.fixture
def small_npz(tmp_path):
    path = str(tmp_path / "atlas_test.npz")
    rng = np.random.default_rng(7)
    np.savez_compressed(
        path,
        grid=rng.integers(0, 255, (200, 300), dtype=np.uint8).reshape(200, 300),
        elev=rng.integers(-500, 4000, (100, 150)).astype(np.int16),
        bounds=np.array([-90, 90, -180, 180], dtype=np.float32),
        scalar=np.float32(0.04),
        names=np.array(["ALPHA", "BETA"], dtype=object),
    )
    return path


def _eager(path):
    d = np.load(path, allow_pickle=True)
    return {k: d[k] for k in d.files}


def test_load_matches_eager(small_npz):
    mm = _load_atlas_arrays(small_npz)
    eager = _eager(small_npz)
    assert set(mm) == set(eager)
    for k in eager:
        a, b = eager[k], mm[k]
        if a.dtype == object:
            assert list(a) == list(b)
        else:
            assert np.array_equal(np.asarray(a), np.asarray(b)), k


def test_grids_are_resident_not_mapped(small_npz):
    # The point of the loader: the arrays the renderer samples every frame
    # are real in-RAM copies. A memmap here means panning faults pages off
    # the SD card and the cabinet hitches.
    mm = _load_atlas_arrays(small_npz)
    assert type(mm["grid"]) is np.ndarray
    assert type(mm["elev"]) is np.ndarray
    assert not isinstance(mm["grid"], np.memmap)


def test_oversized_grid_spills_to_memmap(small_npz, monkeypatch):
    # Budget exhausted: fall back to a memmap rather than failing to load.
    import visuals.atlas as A
    monkeypatch.setattr(A, "_RESIDENT_BUDGET", 0)
    mm = _load_atlas_arrays(small_npz)
    assert isinstance(mm["grid"], np.memmap)
    assert np.array_equal(np.asarray(mm["grid"]), _eager(small_npz)["grid"])


def test_second_load_skips_unpack(small_npz):
    _load_atlas_arrays(small_npz)
    udir = _unpack_dir_for(small_npz)
    mtimes = {f: os.path.getmtime(os.path.join(udir, f)) for f in os.listdir(udir)}
    _load_atlas_arrays(small_npz)
    for f, m in mtimes.items():
        assert os.path.getmtime(os.path.join(udir, f)) == m, f"{f} re-unpacked"


def test_truncated_member_self_heals(small_npz):
    mm = _load_atlas_arrays(small_npz)
    expected = np.asarray(mm["grid"]).copy()
    del mm  # release the mmap before truncating on platforms that care
    victim = os.path.join(_unpack_dir_for(small_npz), "grid.npy")
    with open(victim, "r+b") as f:
        f.truncate(10)
    mm = _load_atlas_arrays(small_npz)
    assert np.array_equal(np.asarray(mm["grid"]), expected)


def test_full_disk_refuses_and_falls_back(small_npz, monkeypatch):
    import visuals.atlas as A

    class _Usage:
        free = 0

    monkeypatch.setattr(A.shutil, "disk_usage", lambda _p: _Usage())
    monkeypatch.setattr(A, "_member_unpacked", lambda *_a: False)
    assert _unpack_atlas(small_npz, _unpack_dir_for(small_npz)) is False

    # The loader falls back to a working eager load
    atlas = _load_atlas_arrays(small_npz)
    assert np.asarray(atlas["grid"]).shape == (200, 300)
    assert not any(isinstance(v, np.memmap) for v in atlas.values())


def test_unwritable_location_falls_back(small_npz, monkeypatch):
    import visuals.atlas as A

    monkeypatch.setattr(
        A, "_unpack_atlas",
        lambda *_a, **_k: (_ for _ in ()).throw(OSError("read-only")))
    atlas = _load_atlas_arrays(small_npz)
    assert set(atlas) == {"grid", "elev", "bounds", "scalar", "names"}
    assert not any(isinstance(v, np.memmap) for v in atlas.values())


# ── Bit-packed sparse masks ──────────────────────────────────────────
# roads and rails are dense uint8 masks of ~522 MB each that are almost all
# zeros. Packed one bit per pixel they fit in RAM; the risk is that the
# unpack-on-sample arithmetic quietly disagrees with plain indexing, which
# would corrupt exactly the zoomed-in road overlay nobody tests by eye.

@pytest.fixture
def mask_npz(tmp_path):
    path = str(tmp_path / "atlas_masks.npz")
    rng = np.random.default_rng(11)
    h, w = 300, 501          # width deliberately not a multiple of 8
    roads = np.zeros((h, w), dtype=np.uint8)
    roads[rng.integers(0, h, 900), rng.integers(0, w, 900)] = 255
    np.savez_compressed(
        path,
        roads=roads,
        grid=rng.integers(0, 255, (h, w), dtype=np.uint8),
        bounds=np.array([-90, 90, -180, 180], dtype=np.float32),
    )
    return path, roads


def test_bitmask_sampling_matches_dense(mask_npz):
    from visuals.atlas import _BitMask, _sample, _sample_at

    path, roads = mask_npz
    atlas = _load_atlas_arrays(path)
    assert isinstance(atlas["roads"], _BitMask)
    assert atlas["roads"].shape == roads.shape
    # One bit per pixel, so 8x smaller than the dense mask (rounded up).
    assert atlas["roads"].nbytes == roads.shape[0] * ((roads.shape[1] + 7) // 8)

    bounds = (-90, 90, -180, 180)
    expected = (roads != 0).astype(np.uint8)
    for clat, clon, vdeg in [(0, 0, 4.0), (37.9, -121.3, 1.0),
                             (-33.9, 151.2, 0.5), (0, 179.5, 3.0)]:
        got = _sample(atlas["roads"], bounds, clat, clon, vdeg)
        ref = _sample(expected, bounds, clat, clon, vdeg)
        assert np.array_equal(got, ref), (clat, clon, vdeg)

    lats = np.linspace(-80, 80, 64).reshape(-1, 1) * np.ones((1, 64))
    lons = np.ones((64, 1)) * np.linspace(-170, 170, 64).reshape(1, -1)
    assert np.array_equal(_sample_at(atlas["roads"], bounds, lats, lons),
                          _sample_at(expected, bounds, lats, lons))


def test_bitmask_cache_is_reused_and_self_heals(mask_npz):
    from visuals.atlas import _bitmask_cache_path, _sample

    path, roads = mask_npz
    _load_atlas_arrays(path)
    cache = _bitmask_cache_path(_unpack_dir_for(path), "roads")
    assert os.path.exists(cache), "packed mask was not cached"

    mtime = os.path.getmtime(cache)
    _load_atlas_arrays(path)
    assert os.path.getmtime(cache) == mtime, "packed mask was rebuilt"

    # A truncated cache must be rebuilt, not crash the whole atlas.
    with open(cache, "r+b") as f:
        f.truncate(12)
    atlas = _load_atlas_arrays(path)
    bounds = (-90, 90, -180, 180)
    assert np.array_equal(_sample(atlas["roads"], bounds, 0, 0, 4.0),
                          _sample((roads != 0).astype(np.uint8),
                                  bounds, 0, 0, 4.0))
