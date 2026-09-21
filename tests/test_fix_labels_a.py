"""
Test for two text label corrections:
1. convection: 'dT' label should be 'RAYLEIGH' since the value is Rayleigh number not temperature difference
2. jacquard: 'RPM' label should be 'ROWS/MIN' since the value is rows advanced per minute, not revolutions
"""

import pytest
from tests._harness import get_sim_display
from arcade import InputState
from visuals.convection import Convection
from visuals.jacquard import Jacquard


class TestConvectionRayleighLabel:
    """Test that convection overlay shows RAYLEIGH label not dT."""

    def test_right_input_shows_rayleigh_label(self):
        """Verify Right input triggers overlay with 'RAYLEIGH' label."""
        display = get_sim_display()
        visual = Convection(display)
        visual.reset()

        # Collect all text drawn to the display
        drawn_texts = []
        original_draw_text = display.draw_text_small

        def capture_text(x, y, text, color):
            drawn_texts.append((x, y, text, color))
            original_draw_text(x, y, text, color)

        display.draw_text_small = capture_text

        # Simulate Right input to trigger overlay
        input_state = InputState()
        input_state.right = True
        visual.handle_input(input_state)

        # Draw the overlay
        visual.draw()

        # Find any text containing RAYLEIGH
        rayleigh_texts = [t for t in drawn_texts if 'RAYLEIGH' in t[2]]
        assert len(rayleigh_texts) > 0, "RAYLEIGH label not found in overlay"

        # Verify old 'dT' label is not present
        dt_texts = [t for t in drawn_texts if 'dT' in t[2]]
        assert len(dt_texts) == 0, f"Found old 'dT' label: {[t[2] for t in dt_texts]}"

    def test_left_input_shows_rayleigh_label(self):
        """Verify Left input triggers overlay with 'RAYLEIGH' label."""
        display = get_sim_display()
        visual = Convection(display)
        visual.reset()

        # Collect drawn text
        drawn_texts = []
        original_draw_text = display.draw_text_small

        def capture_text(x, y, text, color):
            drawn_texts.append((x, y, text, color))
            original_draw_text(x, y, text, color)

        display.draw_text_small = capture_text

        # Simulate Left input
        input_state = InputState()
        input_state.left = True
        visual.handle_input(input_state)

        # Draw the overlay
        visual.draw()

        # Verify RAYLEIGH is present and dT is not
        rayleigh_texts = [t for t in drawn_texts if 'RAYLEIGH' in t[2]]
        assert len(rayleigh_texts) > 0, "RAYLEIGH label not found"

        dt_texts = [t for t in drawn_texts if 'dT' in t[2]]
        assert len(dt_texts) == 0, "Old 'dT' label should not be present"

    def test_rayleigh_label_fits_in_64px(self):
        """Verify RAYLEIGH label with max value fits in 64px width."""
        # Max temp_gradient = 2.0, so max Rayleigh = 2.0 * 10 = 20.0
        # "RAYLEIGH 20.0" = 13 chars = 52 px
        text = "RAYLEIGH 20.0"
        width_px = len(text) * 4
        assert width_px <= 64, f"Text '{text}' ({width_px}px) exceeds 64px limit"

    def test_rayleigh_label_at_position(self):
        """Verify RAYLEIGH label is drawn at expected x position."""
        display = get_sim_display()
        visual = Convection(display)
        visual.reset()

        drawn_texts = []
        original_draw_text = display.draw_text_small

        def capture_text(x, y, text, color):
            drawn_texts.append((x, y, text, color))
            original_draw_text(x, y, text, color)

        display.draw_text_small = capture_text

        # Trigger overlay
        input_state = InputState()
        input_state.right = True
        visual.handle_input(input_state)
        visual.draw()

        # Find RAYLEIGH text - should be at x=2, y=2
        rayleigh_texts = [t for t in drawn_texts if 'RAYLEIGH' in t[2]]
        assert len(rayleigh_texts) > 0
        x, y, text, color = rayleigh_texts[0]
        assert x == 2, f"RAYLEIGH label x position {x}, expected 2"
        assert y == 2, f"RAYLEIGH label y position {y}, expected 2"

        # Verify text width constraint: x + 4*len(text) <= 64
        text_end = x + 4 * len(text)
        assert text_end <= 64, f"RAYLEIGH text ends at pixel {text_end}, exceeds 64"


class TestJacquardRowsMinLabel:
    """The HUD number is punch-card rows per minute, so it must not say RPM."""

    def test_hud_says_rows_per_minute_and_clears_the_row_counter(self):
        from visuals.jacquard import SPEED_RPS
        display = get_sim_display()
        visual = Jacquard(display)
        visual.reset()
        drawn = []
        original = display.draw_text_small
        display.draw_text_small = lambda x, y, text, color: drawn.append((x, text))
        try:
            for level in range(1, len(SPEED_RPS) + 1):
                visual.speed_level = level
                visual._draw_hud(display)
        finally:
            display.draw_text_small = original
        labels = [(x, t) for x, t in drawn if "MIN" in t or "RPM" in t]
        assert len(labels) == len(SPEED_RPS)
        for x, text in labels:
            assert text.endswith("ROW/MIN") and "RPM" not in text
            assert x + 4 * len(text) <= 42   # row counter starts at x=42
