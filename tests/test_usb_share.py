"""USB Share copies art between the cabinet's data/ and a stick without duplicates."""
import os

from PIL import Image

from visuals.usb_share import merge, MAX_DIM


def _png(path, color):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.new("RGB", (64, 64), color).save(path)


def _gif(path, colors):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    frames = [Image.new("RGB", (64, 64), c) for c in colors]
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=100, loop=0)


def _cabinet(root):
    _png(os.path.join(root, "paint", "paint_001.png"), (255, 0, 0))
    _gif(os.path.join(root, "paint_gif", "cat.gif"), [(0, 255, 0), (0, 0, 255)])
    _png(os.path.join(root, "paint_gif", "proj_001", "frame_000.png"), (1, 2, 3))
    _png(os.path.join(root, "paint_gif", "proj_001", "frame_001.png"), (4, 5, 6))


def _listing(root):
    return sorted(os.path.relpath(os.path.join(d, f), root)
                  for d, _, files in os.walk(root) for f in files)


def test_send_then_get_back_makes_no_duplicates(tmp_path):
    cab, stick = str(tmp_path / "cab"), str(tmp_path / "stick")
    _cabinet(cab)
    before = _listing(cab)

    assert merge(cab, stick) == {"copied": 3, "skipped": 0, "bad": 0}
    assert merge(stick, cab) == {"copied": 0, "skipped": 3, "bad": 0}
    assert merge(cab, stick) == {"copied": 0, "skipped": 3, "bad": 0}
    assert _listing(cab) == before
    assert _listing(stick) == before


def test_same_art_under_a_different_name_is_skipped(tmp_path):
    cab, stick = str(tmp_path / "cab"), str(tmp_path / "stick")
    _cabinet(cab)
    merge(cab, stick)
    os.rename(os.path.join(stick, "paint_gif", "cat.gif"), os.path.join(stick, "paint_gif", "kitty.gif"))
    os.rename(os.path.join(stick, "paint_gif", "proj_001"), os.path.join(stick, "paint_gif", "proj_009"))

    assert merge(stick, cab)["copied"] == 0


def test_name_clash_with_different_art_gets_a_new_name(tmp_path):
    cab, other = str(tmp_path / "cab"), str(tmp_path / "other")
    _cabinet(cab)
    _png(os.path.join(other, "paint", "paint_001.png"), (9, 9, 9))
    _gif(os.path.join(other, "paint_gif", "cat.gif"), [(9, 9, 9)])
    _png(os.path.join(other, "paint_gif", "proj_001", "frame_000.png"), (9, 9, 9))

    assert merge(other, cab)["copied"] == 3
    files = _listing(cab)
    assert "paint/paint_002.png" in files
    assert "paint_gif/cat-2.gif" in files
    assert "paint_gif/proj_002/frame_000.png" in files
    # Originals untouched
    assert Image.open(os.path.join(cab, "paint", "paint_001.png")).getpixel((0, 0)) == (255, 0, 0)


def test_junk_on_a_stick_is_rejected(tmp_path):
    stick, cab = str(tmp_path / "stick"), str(tmp_path / "cab")
    os.makedirs(os.path.join(stick, "paint_gif"))
    with open(os.path.join(stick, "paint_gif", "broken.gif"), "wb") as f:
        f.write(b"GIF89a not really")
    Image.new("RGB", (64, 64)).save(os.path.join(stick, "paint_gif", "png_in_disguise.gif"), "PNG")
    Image.new("RGB", (MAX_DIM + 1, 8)).save(os.path.join(stick, "paint_gif", "huge.gif"))
    with open(os.path.join(stick, "paint_gif", "._cat.gif"), "wb") as f:  # macOS resource fork
        f.write(b"\0" * 10)
    _gif(os.path.join(stick, "paint_gif", "my cool anim!.gif"), [(1, 1, 1)])

    assert merge(stick, cab) == {"copied": 1, "skipped": 0, "bad": 3}
    assert _listing(cab) == ["paint_gif/my-cool-anim.gif"]


def test_usb_share_is_only_in_the_menu_while_a_stick_is_present(monkeypatch):
    import catalog
    from visuals import ALL_VISUALS
    from visuals.usb_share import UsbShare

    present = False
    monkeypatch.setattr(UsbShare, "menu_visible", staticmethod(lambda: present))
    utility = catalog.VISUAL_CATEGORY_MAP["utility"]
    try:
        catalog.register_visuals(ALL_VISUALS)
        assert UsbShare not in utility.items

        present = True
        assert catalog.sync_conditional_items() is True
        assert UsbShare in utility.items
        assert utility.items == sorted(utility.items, key=lambda c: c.name.upper())
        assert catalog.sync_conditional_items() is False  # no change, no churn

        present = False
        assert catalog.sync_conditional_items() is True
        assert UsbShare not in utility.items
    finally:
        monkeypatch.undo()
        catalog.register_visuals(ALL_VISUALS)
