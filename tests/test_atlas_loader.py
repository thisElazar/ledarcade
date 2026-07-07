"""Tests for the atlas memmap loader (visuals/atlas.py).

The world atlas npz decompresses to ~1.3 GB, which cannot fit in a Pi's
RAM — the loader unpacks members to raw .npy files once and memory-maps
them on every load. These tests exercise that machinery on a small
synthetic npz so they run everywhere (CI has no atlas data).
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


def test_mmap_load_matches_eager(small_npz):
    mm = _load_atlas_arrays(small_npz)
    eager = _eager(small_npz)
    assert set(mm) == set(eager)
    for k in eager:
        a, b = eager[k], mm[k]
        if a.dtype == object:
            assert list(a) == list(b)
        else:
            assert np.array_equal(np.asarray(a), np.asarray(b)), k
    # The big numeric grids must actually be memory-mapped
    assert isinstance(mm["grid"], np.memmap)
    assert isinstance(mm["elev"], np.memmap)


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
