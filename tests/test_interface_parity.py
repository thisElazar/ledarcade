"""Guard against sim/hardware interface drift.

The desktop sim (`arcade.Display`) and the cabinet driver (`hardware.HardwareDisplay`)
implement the same drawing interface by hand — nothing enforces it. If a method is
added to the sim and used by a visual but forgotten on HardwareDisplay, the sim (and
this whole test suite, which runs the sim) passes green while the *cabinet* crashes.

This test is the one guard that catches that hardware-only failure mode.
"""
import arcade
import hardware


def _public_methods(cls):
    return {
        name
        for name in dir(cls)
        if not name.startswith("_") and callable(getattr(cls, name))
    }


def test_hardware_display_covers_sim_interface():
    sim = _public_methods(arcade.Display)
    hw = _public_methods(hardware.HardwareDisplay)
    missing = sim - hw
    assert not missing, (
        "HardwareDisplay is missing methods the sim Display exposes: "
        f"{sorted(missing)}. A visual using these would crash on the cabinet "
        "while passing in the desktop sim."
    )


# ── Beyond method names: three platform layers, held against each other ──
#
# The sim, the cabinet driver and the web emulator's shim are hand-copied. The
# checks below compare them structurally (signatures, fields, constants) and
# behaviourally (same drawing calls -> same pixels).

import inspect

import pytest

from _harness import (
    INPUT_FIELDS, get_hw_display, get_sim_display, load_emulator_shim,
)

GRID = arcade.GRID_SIZE

# Display methods that exist only to drive one platform's output device, so the
# other layers legitimately lack them.
PLATFORM_ONLY = {"set_safety", "set_gamma", "render"}


def _drawing_api(cls):
    return _public_methods(cls) - PLATFORM_ONLY


def _call_shape(fn):
    """Parameter names + which have defaults — what a caller depends on."""
    params = list(inspect.signature(fn).parameters.values())[1:]  # drop self
    return [(p.name, p.default is not inspect.Parameter.empty) for p in params]


def test_emulator_display_covers_sim_drawing_api():
    emu = load_emulator_shim()["Display"]
    missing = _drawing_api(arcade.Display) - _public_methods(emu)
    assert not missing, (
        f"The web emulator's Display (site/emulator.html) lacks {sorted(missing)}. "
        "Any visual calling these crashes in the browser while passing here."
    )


@pytest.mark.parametrize("name", sorted(_drawing_api(arcade.Display)))
def test_display_signatures_match(name):
    sim = _call_shape(getattr(arcade.Display, name))
    hw = _call_shape(getattr(hardware.HardwareDisplay, name))
    assert sim == hw, f"Display.{name}: sim {sim} != cabinet {hw}"
    emu_fn = getattr(load_emulator_shim()["Display"], name, None)
    if emu_fn is not None:  # absence is reported by the coverage test above
        emu = _call_shape(emu_fn)
        # The emulator may make an argument optional, never required or renamed.
        assert [n for n, _ in emu] == [n for n, _ in sim], (
            f"Display.{name}: emulator params {emu} != sim {sim}")
        for (_, sim_opt), (pname, emu_opt) in zip(sim, emu):
            assert emu_opt or not sim_opt, (
                f"Display.{name}: '{pname}' is optional in the sim but required "
                "in the emulator")


def _colors(cls):
    return {k: v for k, v in vars(cls).items() if k.isupper()}


def test_colors_match_across_platforms():
    sim = _colors(arcade.Colors)
    assert _colors(hardware.Colors) == sim, "hardware.Colors drifted from arcade.Colors"
    emu = _colors(load_emulator_shim()["Colors"])
    assert emu == sim, (
        "emulator Colors drifted from arcade.Colors: "
        f"{sorted(set(sim.items()) ^ set(emu.items()))}")


def _input_state_classes():
    return {
        "sim": arcade.InputState,
        "cabinet": hardware.InputState,
        "emulator": load_emulator_shim()["InputState"],
    }


@pytest.mark.parametrize("platform", ["sim", "cabinet", "emulator"])
def test_input_state_has_exactly_the_shared_fields(platform):
    state = _input_state_classes()[platform]()
    assert set(vars(state)) == set(INPUT_FIELDS), (
        f"{platform} InputState fields differ from the shared set. A field added "
        "to one platform must be added to all three (and to tests/_harness.py).")
    assert all(v is False for v in vars(state).values())


@pytest.mark.parametrize("platform", ["sim", "cabinet", "emulator"])
def test_input_state_derived_properties(platform):
    cls = _input_state_classes()[platform]
    for up, down, left, right in [(0, 0, 0, 0), (1, 0, 0, 0), (0, 1, 0, 0),
                                  (0, 0, 1, 0), (0, 0, 0, 1), (1, 1, 1, 1),
                                  (1, 0, 0, 1)]:
        s = cls()
        s.up, s.down, s.left, s.right = map(bool, (up, down, left, right))
        assert s.dx == right - left
        assert s.dy == down - up
        assert bool(s.any_direction) == bool(up or down or left or right)


def test_emulator_js_writes_every_input_field():
    """The browser copies key state into the Python InputState by name, in a
    string. A field missing there stays False forever — silently."""
    from _harness import emulator_js
    js = emulator_js()
    missing = [f for f in INPUT_FIELDS if f"_input.{f}=" not in js]
    assert not missing, f"emulator.html never sets _input.{missing}"


def test_game_states_match_emulator():
    emu = load_emulator_shim()["GameState"]
    assert [m.name for m in emu] == [m.name for m in arcade.GameState]


# ── Same drawing calls, same pixels ─────────────────────────────────

def _draw_reference_scene(d, colors):
    d.clear()
    d.clear(colors.BLUE)
    d.draw_rect(2, 2, 20, 10, colors.RED)
    d.draw_rect(30, 4, 12, 12, colors.GREEN, filled=False)
    d.draw_rect(-5, -5, 10, 10, colors.YELLOW)          # clipped top-left
    d.draw_rect(60, 60, 10, 10, colors.CYAN)            # clipped bottom-right
    d.draw_line(0, 0, 63, 63, colors.WHITE)
    d.draw_line(63, 10, 0, 40, colors.ORANGE)
    d.draw_line(-10, 30, 80, 35, colors.PINK)           # runs off both edges
    d.draw_circle(32, 32, 9, colors.MAGENTA)
    d.draw_circle(50, 20, 6, colors.LIME, filled=True)
    d.draw_circle(0, 63, 8, colors.PURPLE, filled=True)  # clipped
    d.draw_text_small(1, 50, "Parity 0123 ?!", colors.WHITE)
    if hasattr(d, "draw_text_raw"):
        d.draw_text_raw(1, 57, "Ab #b", colors.GRAY)
    for x, y in [(-1, 0), (0, -1), (64, 0), (0, 64), (10 ** 6, 5)]:
        d.set_pixel(x, y, colors.RED)                   # must be ignored
    d.set_pixel(63, 0, (1, 2, 3))


def _snapshot(d):
    return [[tuple(int(c) for c in d.get_pixel(x, y)) for x in range(GRID)]
            for y in range(GRID)]


def _diff(a, b):
    return [(x, y, a[y][x], b[y][x]) for y in range(GRID) for x in range(GRID)
            if a[y][x] != b[y][x]]


def test_sim_and_cabinet_draw_identical_pixels():
    sim, hw = get_sim_display(), get_hw_display()
    _draw_reference_scene(sim, arcade.Colors)
    _draw_reference_scene(hw, hardware.Colors)
    d = _diff(_snapshot(sim), _snapshot(hw))
    assert not d, f"{len(d)} pixels differ, first: {d[:5]} (x, y, sim, cabinet)"


def test_sim_and_emulator_draw_identical_pixels():
    ns = load_emulator_shim()
    sim, emu = get_sim_display(), ns["Display"]()
    _draw_reference_scene(sim, arcade.Colors)
    _draw_reference_scene(emu, ns["Colors"])
    d = _diff(_snapshot(sim), _snapshot(emu))
    assert not d, f"{len(d)} pixels differ, first: {d[:5]} (x, y, sim, emulator)"


@pytest.mark.parametrize("platform", ["sim", "cabinet", "emulator"])
def test_out_of_bounds_get_pixel_is_black(platform):
    d = {"sim": get_sim_display, "cabinet": get_hw_display,
         "emulator": lambda: load_emulator_shim()["Display"]()}[platform]()
    for x, y in [(-1, 0), (0, -1), (GRID, 0), (0, GRID)]:
        assert tuple(d.get_pixel(x, y)) == (0, 0, 0)


# ── Font ────────────────────────────────────────────────────────────

def test_cabinet_font_matches_sim():
    assert hardware._FONT_3X5 == arcade._FONT_3X5


def test_emulator_font_matches_sim():
    """A glyph missing from the emulator's table is skipped without error, so
    text like '50%' or 'A=440' silently loses characters in the browser."""
    emu = load_emulator_shim()["FONT_3X5"]
    sim = arcade._FONT_3X5
    missing = "".join(sorted(set(sim) - set(emu)))
    assert not missing, f"emulator font lacks glyphs: {missing!r}"
    differ = [k for k in sim if list(emu[k]) != list(sim[k])]
    assert not differ, f"emulator glyphs drawn differently: {differ}"


def test_emulator_touch_buttons_reach_both_actions():
    """On a phone the two on-screen buttons are the only buttons. They once both
    sent Space, which made the right button (and hold-both-to-exit) unreachable."""
    from _harness import emulator_js
    js = emulator_js()
    assert "[[btnL, ' '], [btnR, 'z']]" in js, (
        "emulator.html touch buttons must map btnL -> Space (action_l) and "
        "btnR -> Z (action_r)")
