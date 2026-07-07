"""Guards for the shell's terminal-state contract.

The shells take over (game-over screen, initials, leaderboard) when a game's
state enters TERMINAL_STATES. Before this guard existed, the shells checked
GAME_OVER alone, so the four winnable games (pong, breakout, arkanoid,
bloonstd) froze on GameState.WIN with no score recorded and no way out short
of the hold-both-buttons exit.
"""
import re
from pathlib import Path

from arcade import GameState, TERMINAL_STATES

REPO = Path(__file__).resolve().parent.parent
SHELLS = ["run_hardware.py", "run_arcade.py", "arcade.py"]


def test_win_and_game_over_are_terminal():
    assert GameState.GAME_OVER in TERMINAL_STATES
    assert GameState.WIN in TERMINAL_STATES


def test_shells_branch_on_terminal_states():
    for shell in SHELLS:
        src = (REPO / shell).read_text()
        assert "state in TERMINAL_STATES" in src, (
            f"{shell} no longer branches on TERMINAL_STATES; a game that "
            f"sets GameState.WIN will freeze with no game-over screen"
        )
        assert "state == GameState.GAME_OVER" not in src, (
            f"{shell} compares against GAME_OVER directly; use "
            f"`state in TERMINAL_STATES` so WIN is handled too"
        )


def test_games_only_enter_states_the_shell_handles():
    # A game may sit in PLAYING/PAUSED (shell keeps driving it) or end in a
    # terminal state (shell takes over). Any other assignment means the shell
    # polls a frozen game forever.
    assign = re.compile(r"\.state\s*=\s*GameState\.(\w+)")
    handled = {"PLAYING", "PAUSED"} | {s.name for s in TERMINAL_STATES}
    for path in sorted((REPO / "games").glob("*.py")):
        for name in assign.findall(path.read_text()):
            assert name in handled, (
                f"{path.name} sets GameState.{name}, which no shell handles"
            )
