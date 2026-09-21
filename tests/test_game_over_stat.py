"""The `game_over_stat()` hook: a single-player game's one extra line on the
shell's game-over screen.

Before this hook, the shell's game-over screen (`draw_action_selection` in
run_hardware.py/run_arcade.py, and the base `Game.draw_game_over` used by
arcade.py's own simple runner) never called a game's `draw_game_over()`
override, so ~30 single-player games' LEVEL/LINES/HEIGHT-style stats never
reached the panel. This hook lets a game contribute one short string instead.
"""
import arcade
import run_arcade
import run_hardware
from arcade import Colors
from _harness import get_sim_display

STAT = "LEVEL:3"


class StubGame(arcade.Game):
    """Minimal concrete Game — doesn't override game_over_stat."""

    def reset(self):
        pass

    def update(self, input_state, dt):
        pass

    def draw(self):
        pass


class StatGame(StubGame):
    def game_over_stat(self):
        return STAT


class NoHookGame:
    """A game object that predates the hook entirely (no game_over_stat)."""
    name = "OLD GAME"


def capture_draws(display, monkeypatch):
    calls = []
    real = display.draw_text_small

    def spy(x, y, text, color):
        calls.append((x, y, text, color))
        return real(x, y, text, color)

    monkeypatch.setattr(display, "draw_text_small", spy)
    return calls


# ── base Game class hook ────────────────────────────────────────────

def test_default_game_over_stat_is_none():
    display = get_sim_display()
    g = StubGame(display)
    assert g.game_over_stat() is None


# ── arcade.py's own draw_game_over (simple runner) ──────────────────

def test_arcade_draw_game_over_draws_stat(monkeypatch):
    display = get_sim_display()
    calls = capture_draws(display, monkeypatch)
    g = StatGame(display)
    g.score = 42
    g.draw_game_over(0)

    stat_calls = [c for c in calls if c[2] == STAT]
    assert len(stat_calls) == 1, calls
    x, y, text, color = stat_calls[0]
    assert color == Colors.GRAY
    # Clear of SCORE (y=30, 5px font) above and the options (y=44) below.
    assert y >= 35
    assert y + 5 <= 44


def test_arcade_draw_game_over_none_stat_draws_nothing_extra(monkeypatch):
    display = get_sim_display()
    calls = capture_draws(display, monkeypatch)
    g = StubGame(display)
    g.draw_game_over(0)

    texts = [c[2] for c in calls]
    assert texts == ["GAME OVER", "SCORE:0", ">PLAY AGAIN", " MENU"]


# ── run_hardware.py / run_arcade.py draw_action_selection ───────────

import pytest


@pytest.mark.parametrize("runner", [run_hardware, run_arcade])
@pytest.mark.parametrize("made_leaderboard,rank", [(False, -1), (True, 3)])
def test_draw_action_selection_draws_stat(monkeypatch, runner, made_leaderboard, rank):
    display = get_sim_display()
    calls = capture_draws(display, monkeypatch)
    runner.draw_action_selection(display, 0, 100, made_leaderboard=made_leaderboard,
                                  rank=rank, stat=STAT)

    stat_calls = [c for c in calls if c[2] == STAT]
    assert len(stat_calls) == 1, calls
    x, y, text, color = stat_calls[0]
    assert color == Colors.GRAY
    # Must clear the SCORE line above (y=22 plain / y=18 leaderboard, 5px font)
    # and the first option row below (y=40).
    score_y = 18 if made_leaderboard else 22
    assert y >= score_y + 5
    assert y + 5 <= 40


@pytest.mark.parametrize("runner", [run_hardware, run_arcade])
@pytest.mark.parametrize("made_leaderboard,rank", [(False, -1), (True, 3)])
def test_draw_action_selection_none_stat_draws_nothing_extra(monkeypatch, runner,
                                                               made_leaderboard, rank):
    display = get_sim_display()
    calls = capture_draws(display, monkeypatch)
    runner.draw_action_selection(display, 0, 100, made_leaderboard=made_leaderboard,
                                  rank=rank, stat=None)

    texts = [c[2] for c in calls]
    assert STAT not in texts
    assert all(t != "" for t in texts)


@pytest.mark.parametrize("runner", [run_hardware, run_arcade])
def test_game_lacking_hook_does_not_crash(monkeypatch, runner):
    display = get_sim_display()
    obj = NoHookGame()
    # This mirrors exactly what the call sites in run_hardware.py/run_arcade.py do.
    stat = getattr(obj, "game_over_stat", lambda: None)()
    assert stat is None
    # And feeding that through must not raise either.
    runner.draw_action_selection(display, 0, 100, stat=stat)
