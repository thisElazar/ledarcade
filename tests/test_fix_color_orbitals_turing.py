"""
Tests for three label/text fixes:

1. colortheory.py — Color Wheel page: the 'Y' primary marker sat at hue 120
   (renders pure green) instead of hue 60 (yellow). Tint/Shade page: the
   3-letter hue names didn't match the hues _hsv_to_rgb() actually renders
   for several slots (150, 180, 270, 300, 330).
2. orbitals.py — hybrid example-molecule scenes (CO2, BF3, NH3, H2O) drew
   the raw internal 'mix' id (e.g. 'sp3_h2o') instead of a clean
   hybridization label.
3. turingmachine.py — prog_desc was computed but never drawn anywhere.
"""

import colorsys

import pytest

from tests._harness import get_sim_display
from arcade import InputState
from visuals.colortheory import ColorTheory, _hsv_to_rgb
from visuals.orbitals import Orbitals, SCENES
from visuals.turingmachine import TuringMachine, PROGRAMS


def _capture(monkeypatch, display):
    """Record every draw_text_small / draw_text_clipped call as (x, y, text, color)."""
    calls = []

    def fake_small(x, y, text, color):
        calls.append((x, y, text, color))

    def fake_clipped(x, y, text, color, x0, x1):
        calls.append((x, y, text, color))

    monkeypatch.setattr(display, "draw_text_small", fake_small)
    monkeypatch.setattr(display, "draw_text_clipped", fake_clipped)
    return calls


# ── Task 1a: Color Wheel 'Y' marker ──────────────────────────────────────

class TestColorWheelYellowMarker:
    def test_y_marker_is_yellow_not_green(self, monkeypatch):
        display = get_sim_display()
        visual = ColorTheory(display)
        visual.reset()
        visual.page = 1  # COLOR WHEEL

        calls = _capture(monkeypatch, display)
        visual.draw()

        y_calls = [c for c in calls if c[2] == 'Y']
        assert len(y_calls) == 1, f"expected exactly one 'Y' label, got {y_calls}"
        _, _, _, color = y_calls[0]

        yellow = _hsv_to_rgb(60, 1.0, 1.0)
        green = _hsv_to_rgb(120, 1.0, 1.0)
        assert color == yellow, f"'Y' marker color {color} should be yellow {yellow}"
        assert color != green, "'Y' marker must not render as green"

    def test_y_marker_position_matches_hue_60(self, monkeypatch):
        """The label's angular position must correspond to the wheel's hue-60 slot."""
        import math
        display = get_sim_display()
        visual = ColorTheory(display)
        visual.reset()
        visual.page = 1

        calls = _capture(monkeypatch, display)
        visual.draw()

        r_calls = [c for c in calls if c[2] == 'R']
        y_calls = [c for c in calls if c[2] == 'Y']
        b_calls = [c for c in calls if c[2] == 'B']
        assert r_calls and y_calls and b_calls

        cx, cy, r_outer = 31, 32, 18
        label_r = r_outer + 3
        # offset_deg is 0 at time=0 with no hue_offset
        expected_idx = 2  # hue 60 / 30
        angle_rad = math.radians(expected_idx * 30)
        exp_x = int(cx + label_r * math.cos(angle_rad)) - 1
        exp_y = int(cy + label_r * math.sin(angle_rad)) - 2

        x, y, _, _ = y_calls[0]
        assert (x, y) == (exp_x, exp_y), (
            f"'Y' label at ({x},{y}), expected ({exp_x},{exp_y}) for hue-60 slot"
        )


# ── Task 1b: Tint/Shade hue names ────────────────────────────────────────

def _expected_family(hue_deg):
    """Classic 30-degree color-wheel family name for a hue, derived independently
    from the module's own _hsv_to_rgb via colorsys, not from colortheory.py's list."""
    rgb = _hsv_to_rgb(hue_deg, 1.0, 1.0)
    r, g, b = [c / 255.0 for c in rgb]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    deg = round((h * 360) / 30) * 30 % 360
    families = {
        0: 'RED', 30: 'ORG', 60: 'YEL', 90: 'YGR', 120: 'GRN', 150: 'SPR',
        180: 'CYN', 210: 'SKY', 240: 'BLU', 270: 'VIO', 300: 'MAG', 330: 'ROS',
    }
    return families[deg]


class TestTintShadeHueNames:
    def test_every_slot_name_matches_rendered_hue(self, monkeypatch):
        display = get_sim_display()
        visual = ColorTheory(display)
        visual.reset()
        visual.page = 8  # TINT/SHADE

        seen = {}
        for i in range(12):
            visual.sub_index = i
            calls = _capture(monkeypatch, display)
            visual.draw()
            label_calls = [c for c in calls if c[0] == 2 and c[1] == 9]
            assert len(label_calls) == 1, f"slot {i}: expected one hue-name label, got {label_calls}"
            name = label_calls[0][2]
            seen[i] = name

            hue = (i * 30) % 360
            expected = _expected_family(hue)
            assert name.upper() == expected, (
                f"slot {i} (hue {hue}) drawn as {name!r}, "
                f"but _hsv_to_rgb renders family {expected!r}"
            )
            assert len(name) == 3, f"slot {i} name {name!r} is not 3 letters"
            assert name == name.upper(), f"slot {i} name {name!r} is not upper case"

        # Names must be unambiguous (no slot reused for two different hues).
        assert len(set(seen.values())) == len(seen), f"duplicate hue names: {seen}"


# ── Task 2: orbitals hybrid label ────────────────────────────────────────

class TestOrbitalsHybridLabel:
    @pytest.mark.parametrize("mol_name", ["CO2", "BF3", "NH3", "H2O"])
    def test_hybrid_label_has_no_underscore(self, monkeypatch, mol_name):
        display = get_sim_display()
        visual = Orbitals(display)
        visual.reset()

        scene = next(s for s in SCENES
                     if s.get('type') == 'hybrid' and s['name'] == mol_name)

        calls = _capture(monkeypatch, display)

        # Drive through all three label-cycle phases (name / desc / mix).
        for label_timer in (0.0, 5.0, 10.0):
            visual.label_timer = label_timer
            calls.clear()
            visual._draw_labels(scene)
            for (_, _, text, _) in calls:
                assert '_' not in text, (
                    f"{mol_name}: drawn label {text!r} contains an underscore"
                )

    def test_hybrid_label_shows_clean_hybridization(self, monkeypatch):
        """Phase 2 (the old 'scene[mix].upper()' slot) should show a clean
        hybridization code such as 'SP3', not 'SP3_H2O'."""
        display = get_sim_display()
        visual = Orbitals(display)
        visual.reset()

        scene = next(s for s in SCENES
                     if s.get('type') == 'hybrid' and s['name'] == 'H2O')

        calls = _capture(monkeypatch, display)
        visual.label_timer = 10.0  # phase 2
        visual._draw_labels(scene)

        assert len(calls) == 1
        text = calls[0][2]
        assert text.upper() == 'SP3', f"expected clean 'SP3' label, got {text!r}"

    def test_molecule_name_is_shown_in_phase_0(self, monkeypatch):
        """Sanity check: the molecule name (CO2/BF3/NH3/H2O) is already drawn
        elsewhere (phase 0), so task 2 doesn't need to add it."""
        display = get_sim_display()
        visual = Orbitals(display)
        visual.reset()

        scene = next(s for s in SCENES
                     if s.get('type') == 'hybrid' and s['name'] == 'H2O')

        calls = _capture(monkeypatch, display)
        visual.label_timer = 0.0  # phase 0
        visual._draw_labels(scene)

        assert any(c[2] == 'H2O' for c in calls), \
            "expected molecule name 'H2O' to be drawn in phase 0"


# ── Task 3: turingmachine program description ────────────────────────────

class TestTuringDescriptionDrawn:
    def test_description_drawn_after_selecting_program(self, monkeypatch):
        display = get_sim_display()
        visual = TuringMachine(display)
        visual.reset()

        # Move to the "ADD" program (short desc: "Unary 3 + 4", fits in 64px).
        input_state = InputState()
        input_state.down_pressed = True
        for _ in range(4):
            visual.handle_input(input_state)

        name, desc, _, _ = PROGRAMS[visual.program_index]
        assert name == "ADD"

        calls = _capture(monkeypatch, display)
        visual.draw()

        matches = [c for c in calls if c[2].strip().upper() == desc.upper()]
        assert matches, (
            f"description {desc!r} was not drawn after selecting program {name!r}; "
            f"drawn texts: {[c[2] for c in calls]}"
        )

    def test_long_description_scrolled_window_drawn(self, monkeypatch):
        """For a description too long for 64px, some window of it must still
        be drawn (via the scrolling text pattern)."""
        display = get_sim_display()
        visual = TuringMachine(display)
        visual.reset()

        input_state = InputState()
        input_state.down_pressed = True
        visual.handle_input(input_state)  # -> BB-3

        name, desc, _, _ = PROGRAMS[visual.program_index]
        assert name == "BB-3"
        assert len(desc) * 4 > 60, "test assumes this description needs scrolling"

        calls = _capture(monkeypatch, display)
        visual.draw()

        # Our capture records draw_text_clipped calls with the full (unclipped)
        # text argument, matching the codebase's existing marquee pattern
        # (see visuals/latindna.py _draw_desc).
        matches = [c for c in calls if c[2].strip().upper() == desc.upper()]
        assert matches, (
            f"long description {desc!r} was not drawn (not even its scrolled window); "
            f"drawn texts: {[c[2] for c in calls]}"
        )

    def test_no_behaviour_change_to_machine_state(self):
        """Drawing the description must not affect stepping/tape/head state."""
        display = get_sim_display()
        visual = TuringMachine(display)
        visual.reset()

        input_state = InputState()
        input_state.down_pressed = True
        visual.handle_input(input_state)

        state_before = (visual.state, visual.head_pos, dict(visual.tape),
                         visual.step_count)
        visual.draw()
        visual.draw()
        state_after = (visual.state, visual.head_pos, dict(visual.tape),
                        visual.step_count)
        assert state_before == state_after
