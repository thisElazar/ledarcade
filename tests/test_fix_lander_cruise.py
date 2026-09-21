"""Tests for the HUD-vs-crash-test mismatch in LunarLander and the missing
letters in SpaceCruise's floating combo text (see fix_brief.md).
"""
from tests._harness import get_sim_display

from games.lunarlander import LunarLander
from games.spacecruise import SpaceCruise
from arcade import Colors


def _recording_draw_text_small(display):
    """Monkeypatch-style wrapper: returns (calls, wrapped_fn)."""
    calls = []
    original = display.draw_text_small

    def wrapped(x, y, text, color):
        calls.append((x, y, text, color))
        return original(x, y, text, color)

    return calls, wrapped


# ── Task 1: LunarLander HUD speed indicator ─────────────────────────────

def test_speed_indicator_red_when_lateral_only_unsafe(monkeypatch):
    """vx alone exceeds MAX_LATERAL_SPEED, vy is fine -- the crash test would
    kill this landing (abs(vx) > MAX_LATERAL_SPEED), so the HUD arrow must be
    drawn in the danger color, not green.
    """
    display = get_sim_display()
    game = LunarLander(display)

    game.vx = 15.0  # > MAX_LATERAL_SPEED (12.0)
    game.vy = 3.0   # > 2 so the 'v' arrow is drawn; well within MAX_LANDING_SPEED (18.0)

    calls, wrapped = _recording_draw_text_small(display)
    monkeypatch.setattr(display, "draw_text_small", wrapped)

    game.draw_hud()

    arrow_calls = [c for c in calls if c[2] in ("v", "^")]
    assert arrow_calls, "expected the vertical speed arrow to be drawn"
    for (_, _, _, color) in arrow_calls:
        assert color == game.DANGER_COLOR, (
            f"lateral speed {game.vx} exceeds MAX_LATERAL_SPEED but arrow drew {color}"
        )


def test_speed_indicator_green_when_both_safe(monkeypatch):
    display = get_sim_display()
    game = LunarLander(display)

    game.vx = 2.0
    game.vy = 3.0  # > 2 so arrow draws; within MAX_LANDING_SPEED

    calls, wrapped = _recording_draw_text_small(display)
    monkeypatch.setattr(display, "draw_text_small", wrapped)

    game.draw_hud()

    arrow_calls = [c for c in calls if c[2] in ("v", "^")]
    assert arrow_calls, "expected the vertical speed arrow to be drawn"
    for (_, _, _, color) in arrow_calls:
        assert color == Colors.GREEN


# ── Task 2: SpaceCruise floating "MISS!" text ───────────────────────────

def test_miss_floating_text_draws_every_character(monkeypatch):
    """Every character of 'MISS!' must reach the display, not just '!'."""
    display = get_sim_display()
    game = SpaceCruise(display)

    seen_pixels = []
    original_set_pixel = display.set_pixel

    def recording_set_pixel(x, y, color):
        seen_pixels.append((x, y, color))
        return original_set_pixel(x, y, color)

    monkeypatch.setattr(display, "set_pixel", recording_set_pixel)

    # Directly trigger the dropped-combo path.
    game.combo_first_number = 5
    game.crosshair_x = 30
    game.crosshair_y = 30
    game._process_miss()
    game._process_miss()
    game._process_miss()  # third miss drops the combo and spawns "MISS!"

    assert any(t.text == "MISS!" for t in game.floating_texts)

    game.draw()

    # For each of M, I, S, S, !  at its expected column, at least one pixel of
    # that color must have been drawn (i.e. the glyph rendered, not skipped).
    text_obj = next(t for t in game.floating_texts if t.text == "MISS!")
    fade = 1.0 - (text_obj.time / text_obj.duration)
    expected_color = tuple(int(c * fade) for c in text_obj.color)
    x_pos = int(text_obj.x)

    for i, ch in enumerate("MISS!"):
        col_x = x_pos + i * 4
        drawn_in_column = [
            p for p in seen_pixels
            if col_x <= p[0] < col_x + 4 and p[2] == expected_color
        ]
        assert drawn_in_column, f"character '{ch}' at column {i} (x={col_x}) never drew a pixel"
