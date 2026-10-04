"""GRAND MUSEUM's secret switch room and the visibility levers it holds."""
import math
from unittest import mock

import pytest

import catalog
import levers
import settings
from arcade import InputState
import visuals.gallery3d as g

KONAMI = "up up down down left right left right".split()


class _Disp:
    def __getattr__(self, name):
        return lambda *a, **k: None


@pytest.fixture
def museum(sandbox):
    with mock.patch.object(g._Gallery3DBase, "_load_textures", lambda self: None):
        m = g.GalleryMuseum(_Disp())
    m.auto_walk = False
    return m


def _step(m, n=1, **keys):
    for _ in range(n):
        inp = InputState()
        for k, v in keys.items():
            setattr(inp, k, v)
        m.handle_input(inp)
        m.update(1 / 30)


def _push(m):
    m.px, m.py, m.pa = 4.5, 12.4, math.pi / 2       # starting chamber, facing the south wall
    _step(m, 5, up=True)


def test_after_hours_lives_in_memory_only(sandbox):
    levers.set_after_hours(True)
    assert levers.after_hours()
    assert "after_hours" not in settings._settings  # a reboot switches it off


def test_code_is_the_konami_code():
    assert levers.code_matches(KONAMI)
    assert not levers.code_matches(KONAMI[:-1] + ["up"])
    assert len(KONAMI) == levers.CODE_LENGTH


def test_mature_items_need_after_hours_and_never_shuffle(sandbox, monkeypatch):
    from games import ALL_GAMES
    from games.doom import Doom
    from games.shuffle import AllGames
    monkeypatch.setattr(Doom, "menu_visible", staticmethod(lambda: True))  # engine "installed"
    unique = catalog.GAME_CATEGORY_MAP["unique"]
    try:
        catalog.register_games(ALL_GAMES)
        assert Doom not in unique.items
        levers.set_after_hours(True)
        assert catalog.sync_conditional_items() is True
        assert Doom in unique.items
        assert Doom not in AllGames.games
        monkeypatch.setattr(Doom, "menu_visible", staticmethod(lambda: False))
        assert catalog.sync_conditional_items() is True   # no engine, no listing
        assert Doom not in unique.items
    finally:
        levers.set_after_hours(False)
        monkeypatch.undo()
        catalog.register_games(ALL_GAMES)


def test_push_wall_slides_to_the_back_wall_and_closes_on_reset(museum):
    m = museum
    assert m.MAP[13][4] == 1
    _push(m)
    assert m._block_y is not None and m.MAP[13][4] == 0
    _step(m, 120)
    assert m._block_y is None and m._rest == (4, 21) and m.MAP[21][4] == 1
    m._party = True
    m.reset()                                         # leaving the museum
    assert m.MAP[13][4] == 1 and m.MAP[21][4] == 0 and m._rest is None
    assert not m._party


def test_auto_walk_never_opens_it(museum):
    m = museum
    m.auto_walk = True
    m.px, m.py, m.pa = 4.5, 12.4, math.pi / 2
    for _ in range(600):
        m.update(1 / 30)
    assert m.MAP[13][4] == 1 and m._block_y is None and m._rest is None


def test_sliding_block_is_solid(museum):
    m = museum
    _push(m)
    by = m._block_y
    assert m._solid(4.5, by + 0.5, 0.25)
    assert not m._solid(4.5, 12.5, 0.25)


def test_levers(museum):
    m = museum
    _push(m)
    _step(m, 120)
    m.px, m.py, m.pa = 2.5, 19.5, math.pi              # PARTY button, west wall
    _step(m, 1, action_l=True)
    assert m._party
    m.px, m.py, m.pa = 6.5, 19.5, 0.0                  # AFTER HOURS, east wall
    _step(m, 1, action_l=True)
    for d in ["up"] * 8:
        _step(m, 1, **{d + "_pressed": True})
    assert not levers.after_hours() and m._plate_msg == "LOCKED"
    _step(m, 1, action_r=True)
    for d in KONAMI:
        _step(m, 1, **{d + "_pressed": True, d: True})
    assert levers.after_hours()
    _step(m, 5, right=True)                            # stick still held after the last move
    assert (m.px, m.py, m.pa) == (6.5, 19.5, 0.0)      # the stick was a keypad, not movement
    _step(m, 1)
    _step(m, 5, right=True)                            # released and pushed again: it turns
    assert m.pa > 0
    m.pa = 0.0
    _step(m, 1, action_l=True)                         # pulling it again needs no code
    assert not levers.after_hours()


def test_web_emulator_without_levers_keeps_the_wall_shut(museum, monkeypatch):
    monkeypatch.setattr(g, "_levers", None)        # the emulator doesn't bundle levers.py
    m = museum
    _push(m)
    _step(m, 30, up=True, action_l=True)
    assert m.MAP[13][4] == 1 and m._block_y is None


def test_switch_room_draws_lit_and_unlit(museum):
    m = museum
    _push(m)
    _step(m, 120)
    assert all(m.MAP[y][x] == m._TORCH for x, y in m._TORCH_CELLS)
    for on in (False, True):
        m._party = on
        levers.set_after_hours(on)
        for pose in [(4.5, 17.0, math.pi / 2), (5.5, 19.5, math.pi), (3.0, 19.5, 0.0),
                     (2.5, 17.2, -math.pi / 2), (4.5, 12.0, math.pi / 2)]:
            m.px, m.py, m.pa = pose
            m.draw()                                   # torches, conduit, plaque, levers
