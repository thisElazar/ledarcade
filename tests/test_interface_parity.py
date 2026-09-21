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
PLATFORM_ONLY = {"set_safety", "set_gamma", "set_mirror", "render"}


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


def test_site_shared_js_font_matches_sim():
    """site/shared.js draws the homepage scene plates with its own copy of the
    font, stored as row bitmasks. It had drifted to 42 uppercase-only glyphs and
    no drawTextRaw at all, so any lowercase or symbol would have silently
    vanished the moment a JS scene drew one.
    """
    import json
    import os
    import re

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(root, "site", "shared.js"), encoding="utf-8") as f:
        src = f.read()
    literal = re.search(r"const FONT = (\{.*?\n\});", src, re.S).group(1)
    table = json.loads(re.sub(r",(\s*\})", r"\1", literal))

    expected = {ch: [int(row, 2) for row in rows]
                for ch, rows in arcade._FONT_3X5.items()}
    assert table == expected, "site/shared.js FONT has drifted from arcade._FONT_3X5"
    for method in ("drawTextRaw(", "drawTextClipped("):
        assert method in src, f"site/shared.js Display is missing {method})"


def test_no_module_carries_its_own_font():
    """One font, one source of truth.

    Marquee scrolling needs a glyph clipped to a single column, which
    draw_text_small cannot do, so ten visuals each pasted their own copy of the
    font table and trimmed it. They drifted: characters went missing ('%' and
    '=' in BAKING), and '(' ')' '/' ended up drawn differently from the rest of
    the cabinet -- visible in the same string, since _draw_scrolling_text falls
    back to draw_text_small whenever the text happens to fit. Display now has
    draw_text_clipped, so nothing needs a private copy.
    """
    import ast
    import glob
    import os

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    offenders = []
    for path in sorted(glob.glob(os.path.join(root, "visuals", "*.py"))
                       + glob.glob(os.path.join(root, "games", "*.py"))):
        with open(path, encoding="utf-8") as f:
            tree = ast.parse(f.read())
        # ast.walk, not tree.body: rudiments.py and chordchart.py each hid a
        # font dict *inside a method*, where a module-level scan never saw it.
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Dict):
                continue
            for target in node.targets:
                if isinstance(target, ast.Name) and "FONT" in target.id.upper():
                    offenders.append(f"{os.path.basename(path)}:{node.lineno} ({target.id})")
    assert not offenders, (
        "these modules define their own font table instead of importing "
        f"arcade._FONT_3X5: {offenders}. Use display.draw_text_clipped() for "
        "marquee text rather than reaching into the glyphs."
    )


def test_catalog_names_are_renderable():
    """The emulator draws its menu from site/catalog.json, and a character the
    font lacks draws nothing while still advancing the cursor — a hole in the
    middle of the word. The cabinet strips accents when it builds each painting
    class's name (visuals/painting.py), so site/generate_catalog.py has to strip
    them too; it once did not, and 11 paintings read 'CAF  TERRACE AT NIGHT'.
    """
    import json
    import os

    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "site", "catalog.json")
    with open(path, encoding="utf-8") as f:
        catalog = json.load(f)

    font = set(arcade._FONT_3X5)
    unrenderable = []
    for category in catalog["categories"]:
        for item in category.get("items", []):
            missing = {c for c in item["name"] if c.upper() not in font and c not in font}
            if missing:
                unrenderable.append((item["name"], "".join(sorted(missing))))
    assert not unrenderable, (
        "catalog.json names the emulator cannot draw: "
        f"{unrenderable}. Regenerate with site/generate_catalog.py."
    )


def test_emulator_touch_buttons_reach_both_actions():
    """On a phone the two on-screen buttons are the only buttons. They once both
    sent Space, which made the right button (and hold-both-to-exit) unreachable."""
    from _harness import emulator_js
    js = emulator_js()
    assert "[[btnL, ' '], [btnR, 'z']]" in js, (
        "emulator.html touch buttons must map btnL -> Space (action_l) and "
        "btnR -> Z (action_r)")
