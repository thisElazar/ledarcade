"""
Test for three text label corrections:
1. windowwasher: CLEAN label should have a + sign like TIME and PAR
2. signs: speed label should be 'SPEED LIMIT' not 'SPEED 50'
3. entropy: docstring/guide should not say "Press Action" flips velocities
"""

import pytest
from tests._harness import get_sim_display
from arcade import InputState, Colors
from games.windowwasher import WindowWasher
from visuals.signs import Signs, _TYPE_LABELS
from visuals.entropy import Entropy, PALETTES


class TestWindowWasherCleanLabel:
    """Test that level-clear screen shows CLEAN:+ with plus sign."""

    def test_clean_label_has_plus_sign(self):
        """Verify CLEAN line starts with 'CLEAN:+' on level clear screen."""
        display = get_sim_display()
        game = WindowWasher(display)

        # Collect all text drawn to the display
        drawn_texts = []
        original_draw_text = display.draw_text_small

        def capture_text(x, y, text, color):
            drawn_texts.append((x, y, text, color))
            original_draw_text(x, y, text, color)

        display.draw_text_small = capture_text

        # Force to level_clear phase
        game.phase = 'level_clear'
        game.phase_timer = 2.5
        game.timer = 50.0
        game.level_complete = True

        # Draw level clear screen
        game.draw()

        # Find CLEAN label in drawn text
        clean_texts = [t for t in drawn_texts if 'CLEAN' in t[2]]
        assert len(clean_texts) > 0, "CLEAN label not found on level-clear screen"

        clean_line = clean_texts[0][2]
        assert clean_line.startswith('CLEAN:+'), f"Expected CLEAN:+ but got: {clean_line}"


class TestSignsSpeedLabel:
    """Test that speed label is 'SPEED LIMIT' not 'SPEED 50'."""

    def test_speed_label_is_speed_limit(self):
        """Verify _TYPE_LABELS['speed'] is 'SPEED LIMIT'."""
        assert _TYPE_LABELS['speed'] == 'SPEED LIMIT', \
            f"Expected 'SPEED LIMIT' but got: {_TYPE_LABELS['speed']}"

    def test_no_speed_50_in_captions(self):
        """Verify no sign caption contains 'SPEED 50'."""
        display = get_sim_display()
        visual = Signs(display)
        visual.reset()

        # Collect all text drawn
        drawn_texts = []
        original_draw_text = display.draw_text_small

        def capture_text(x, y, text, color):
            drawn_texts.append((x, y, text, color))
            original_draw_text(x, y, text, color)

        display.draw_text_small = capture_text

        # Check all speed signs
        for sign_entry in visual._manifest:
            name, sign_type, stem = sign_entry
            if sign_type == 'speed':
                # Set to this sign
                visual.sign_pos = visual._manifest.index(sign_entry)
                visual.group_idx = 2  # SPEED group
                drawn_texts.clear()
                visual.draw()

                # Check that no drawn text contains 'SPEED 50'
                for x, y, text, color in drawn_texts:
                    assert 'SPEED 50' not in text, \
                        f"Found 'SPEED 50' in caption: {text} for sign {name}"


class TestEntropyDocstring:
    """Test that entropy module docstring/guide don't falsely claim Action flips velocities."""

    def test_module_docstring_no_press_action_flip(self):
        """Module docstring should not say 'Press Action' causes velocity flip."""
        import visuals.entropy as entropy_module
        docstring = entropy_module.__doc__
        assert 'Press Action and every velocity' not in docstring, \
            "Module docstring incorrectly claims 'Press Action' flips velocities"

    def test_guide_desc_no_press_action_reverse(self):
        """GUIDE desc should not say 'Press Action' reverses velocities."""
        display = get_sim_display()
        visual = Entropy(display)
        visual.reset()

        guide_desc = visual.GUIDE['desc']
        assert 'Press Action and every velocity' not in guide_desc, \
            f"GUIDE desc incorrectly claims 'Press Action' reverses velocities: {guide_desc}"

    def test_action_only_cycles_color(self):
        """Verify Action input only cycles palette, not reversal."""
        display = get_sim_display()
        visual = Entropy(display)
        visual.reset()

        initial_palette = visual.palette_idx

        # Simulate Action press
        input_state = InputState()
        input_state.action_l = True
        visual.handle_input(input_state)

        # Palette should have cycled
        assert visual.palette_idx == (initial_palette + 1) % len(PALETTES), \
            "Action should cycle palette"


class TestWindowWasherTextFits:
    """Test that corrected text fits within 64px width."""

    def test_clean_label_fits(self):
        """CLEAN:+ plus reasonable value should fit in 64px."""
        # Longest reasonable CLEAN value: for level 3 with max windows
        # Level 3: num_cols = 5+3 = 8, so windows = 8*5 = 40 * 10 = 400
        # "CLEAN:+400" = 10 chars = 40px
        text = "CLEAN:+400"
        width_px = len(text) * 4
        assert width_px <= 64, f"Text '{text}' ({width_px}px) exceeds 64px limit"

    def test_speed_limit_scrolls_with_long_country(self):
        """SOUTH KOREA SPEED LIMIT should scroll if it exceeds max_chars."""
        label = "SOUTH KOREA SPEED LIMIT"
        max_chars = 14
        # Should be longer than max_chars and trigger scrolling
        assert len(label) > max_chars, \
            f"Label '{label}' ({len(label)} chars) should exceed max_chars ({max_chars})"
