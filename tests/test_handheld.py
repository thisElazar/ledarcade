"""HANDHELD: the two-button -> Game Boy control mapping, the downscalers, and
(when PyBoy is installed) a full run of the original test ROM from
tools/build_gb_rom.py. No commercial ROMs are involved anywhere."""
import numpy as np
import pytest

import games.handheld as hh
from arcade import GameState, InputState
from games.handheld import Controls, Handheld
from tools.build_gb_rom import build
from _harness import get_sim_display

DT = 1 / 60


def _inp(L=False, R=False, *dirs):
    return dict(up='up' in dirs, down='down' in dirs, left='left' in dirs,
                right='right' in dirs, L=L, R=R)


def _run(c, frames):
    """Feed (inp, n) pairs; returns the GB buttons held on each frame."""
    out = []
    for inp, n in frames:
        for _ in range(n):
            out.append(c.update(inp, DT))
            c.frames_elapsed(1)
    return out


def test_stick_is_the_dpad():
    assert Controls().update(_inp(False, False, 'up', 'left'), DT) == {'up', 'left'}


def test_one_button_reaches_the_game_after_the_chord_window():
    held = _run(Controls(), [(_inp(L=True), 8)])
    assert held[0] == set()                         # still might become L+R
    assert held[-1] == {'b'}
    held = _run(Controls(), [(_inp(R=True), 8)])
    assert held[-1] == {'a'}


def test_a_quick_tap_still_presses_the_button():
    held = _run(Controls(), [(_inp(R=True), 1), (_inp(), 3)])
    assert {'a'} in held[1:]


def test_tap_both_is_start_and_hold_is_not():
    held = _run(Controls(), [(_inp(True, True), 6), (_inp(), 2)])
    assert any('start' in h for h in held) and not any(h & {'a', 'b'} for h in held)
    held = _run(Controls(), [(_inp(True, True), 60), (_inp(), 2)])   # 1 s: on its way to quit
    assert not any('start' in h for h in held)


def test_both_plus_stick_is_select_or_view():
    c = Controls()
    held = _run(c, [(_inp(True, True), 2), (_inp(True, True, 'down'), 2), (_inp(), 2)])
    assert any('select' in h for h in held)
    assert not any('start' in h or 'down' in h for h in held)       # the chord ate it
    c = Controls()
    _run(c, [(_inp(True, True), 2)])
    c.update(_inp(True, True, 'up'), DT)
    assert c.toggle_view


def test_holding_b_then_pressing_a_is_a_plus_b():
    held = _run(Controls(), [(_inp(L=True), 8), (_inp(True, True), 3)])
    assert held[-1] == {'a', 'b'}


def test_the_button_that_started_the_game_is_ignored():
    held = _run(Controls(held_l=True), [(_inp(L=True), 10), (_inp(), 2)])
    assert not any(held)


def test_downscalers_fill_the_panel():
    screen = np.zeros((144, 160, 4), np.uint8)
    screen[..., :3] = 200
    z = hh.render_zoom(screen, 32, 16)
    f = hh.render_fit(screen)
    assert z.shape == f.shape == (64, 64, 3)
    assert (z == 200).all()
    assert (f[3:61] == 200).all() and (f[:3] == 0).all()


def test_sprite_focus_ignores_hidden_sprites():
    oam = bytearray(160)                            # all at (0, 0): off screen
    assert hh.sprite_focus(oam, 0x83) is None
    oam[0:2] = bytes((16 + 50, 8 + 100))
    assert hh.sprite_focus(oam, 0x83) == (104.0, 54.0)
    assert hh.sprite_focus(oam, 0x81) is None       # sprites switched off


def test_rom_header_title(tmp_path):
    p = tmp_path / 'x.gb'
    p.write_bytes(build())
    assert hh.rom_title(str(p)) == 'LEDTEST'


def test_hidden_without_roms(sandbox, monkeypatch, tmp_path):
    monkeypatch.setattr(hh, 'ROM_DIR', str(tmp_path / 'none'))
    assert not hh._available()
    assert Handheld(get_sim_display()).state == GameState.GAME_OVER


def test_plays_the_test_rom(sandbox, monkeypatch, tmp_path):
    pytest.importorskip('pyboy')
    (tmp_path / 'ledtest.gb').write_bytes(build())
    monkeypatch.setattr(hh, 'ROM_DIR', str(tmp_path))
    g = Handheld(get_sim_display())
    assert g.state == GameState.PLAYING

    def step(n=1, **kw):
        for _ in range(n):
            i = InputState()
            for k, v in kw.items():
                setattr(i, k, v)
            g.update(i, DT)
            g.draw()

    step(action_r=True, action_r_held=True)
    step(1)
    mem = g._emu.pb.memory
    step(260)                                       # boot animation
    x0 = mem[0xFE01]
    step(30, right=True)
    assert mem[0xFE01] - x0 >= 25                   # the hero walked right
    bgp = mem[0xFF47]
    step(1, action_l=True, action_r=True, action_l_held=True, action_r_held=True)
    step(5, action_l_held=True, action_r_held=True)
    step(10)
    assert mem[0xFF47] == bgp ^ 0xFF                # START inverted the palette
    assert g._panel.any()
    g.close()
    assert (tmp_path / 'ledtest.gb.state').exists()
    g = Handheld(get_sim_display())
    assert g._menu.value(1) == 'RESUME'
