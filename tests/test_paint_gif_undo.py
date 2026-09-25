"""Undo in the GIF maker.

An artist lost a frame to a paint-bucket fill that undo could not reverse. Fill
sets `painting` off after one pass so it fires once, but the still-held button
re-triggered it every tick, pushing a fresh snapshot of the already-filled
canvas each time and flushing the pre-fill snapshot off the 16-deep stack.
"""
import pytest

from arcade import InputState
from visuals import paint_gif
from visuals.paint_gif import PaintGif, TOOL_FILL, TOOL_MARKER
from tests._harness import get_sim_display, make_input

DT = 1 / 30


def _gif():
    pg = PaintGif(get_sim_display())
    pg.reset()
    return pg


def _hold(pg, ticks, held=True):
    pg.handle_input(make_input(InputState, action_l_held=held))
    for _ in range(ticks):
        pg.update(DT)


def test_fill_undo_survives_a_held_button(sandbox):
    pg = _gif()
    pg.tool = TOOL_FILL
    assert pg.canvas[pg.cy][pg.cx] is None

    _hold(pg, 60)  # hold for two seconds, well past the old 16-snapshot cap
    assert pg.canvas[pg.cy][pg.cx] is not None, "fill did not fire"
    assert len(pg.undo_stacks[0]) == 1, "held button re-snapshotted the fill"

    _hold(pg, 1, held=False)
    pg._do_undo()
    assert pg.canvas[pg.cy][pg.cx] is None, "undo did not reverse the fill"


def test_fill_fires_again_on_next_press(sandbox):
    pg = _gif()
    pg.tool = TOOL_FILL
    _hold(pg, 10)
    _hold(pg, 1, held=False)
    pg.color_idx = (pg.color_idx + 1) % len(paint_gif.PALETTE)
    _hold(pg, 10)
    assert pg.canvas[pg.cy][pg.cx] == paint_gif.PALETTE[pg.color_idx]
    assert len(pg.undo_stacks[0]) == 2


def test_snapshot_skips_unchanged_canvas(sandbox):
    pg = _gif()
    pg._snapshot()
    pg._snapshot()
    assert len(pg.undo_stacks[0]) == 1


def test_undo_depth_and_global_cap(sandbox, monkeypatch):
    pg = _gif()
    pg.tool = TOOL_MARKER
    for i in range(paint_gif.FRAME_UNDO_MAX + 10):
        pg.canvas[0][0] = (i, 0, 0)  # make each snapshot distinct
        pg._snapshot()
    assert len(pg.undo_stacks[0]) == paint_gif.FRAME_UNDO_MAX

    monkeypatch.setattr(paint_gif, "TOTAL_UNDO_MAX", 40)
    pg._add_frame()
    for i in range(30):
        pg.canvas[0][0] = (0, i, 0)
        pg._snapshot()
    total = sum(len(s) for s in pg.undo_stacks.values())
    assert total == 40
    # The cap always trims the deepest stack, so the two frames even out
    assert len(pg.undo_stacks[0]) == 20
    assert len(pg.undo_stacks[1]) == 20
