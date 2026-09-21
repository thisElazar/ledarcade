"""Regression tests for three legend-audit fixes:

1. LightsOut.best_level and FifteenPuzzle.best_moves must survive the shell
   building a new instance every time the game is launched (moved to
   class-level state).
2. Network's HUD must not draw a `p=` label while in Barabasi-Albert mode,
   since that model never reads rewire_p.
3. Chess/Othello draw_game_over() must not draw its own 'BTN:AGAIN' line —
   the shell already draws an '>AGAIN  MENU' selector row at that y for
   2-player games.
"""
from arcade import InputState
from games.lightsout import LightsOut
from games.fifteenpuzzle import FifteenPuzzle
from games.chess import Chess
from games.othello import Othello
from visuals.network import Network
from _harness import get_sim_display

DT = 1.0 / 30.0


def _input(**kwargs):
    s = InputState()
    for k, v in kwargs.items():
        setattr(s, k, v)
    return s


def _spy_text(display, monkeypatch):
    """Monkeypatch display.draw_text_small to record every drawn string."""
    recorded = []
    real = display.draw_text_small

    def spy(x, y, text, color):
        recorded.append(text)
        return real(x, y, text, color)

    monkeypatch.setattr(display, "draw_text_small", spy)
    return recorded


# ── Task 1: best values survive relaunch ───────────────────────────────

def test_lightsout_best_level_survives_new_instance(monkeypatch):
    display = get_sim_display()
    LightsOut.best_level = 0  # known starting point regardless of test order

    game = LightsOut(display)
    game.level = 3
    # Set up a board that's solved by toggling the cursor cell (its own
    # toggle() / check_win() code path, exactly as a real move would).
    game.grid = [[False] * 5 for _ in range(5)]
    for c, r in [(2, 2), (1, 2), (3, 2), (2, 1), (2, 3)]:
        game.grid[r][c] = True
    game.cursor_x, game.cursor_y = 2, 2
    game.toggle_flash = 0

    game.update(_input(action_l=True), DT)

    assert game.solved
    assert LightsOut.best_level == 3

    # Simulate the shell building a brand new instance for a relaunch.
    game2 = LightsOut(display)
    assert game2.best_level == 3

    recorded = _spy_text(display, monkeypatch)
    game2.draw()
    assert any(t == "BEST:L3" for t in recorded), recorded


def test_fifteenpuzzle_best_moves_survives_new_instance(monkeypatch):
    display = get_sim_display()
    FifteenPuzzle.best_moves = 999

    game = FifteenPuzzle(display)
    # Solved layout, but one move away: empty at (3,2) instead of (3,3).
    game.board = [[r * 4 + c + 1 for c in range(4)] for r in range(4)]
    game.board[3][3] = 0
    game.board[3][2] = 0
    game.board[3][3] = 15
    game.empty_row, game.empty_col = 3, 2
    game.moves = 0
    game.won = False
    game.move_cooldown = 0

    game.update(_input(left=True), DT)

    assert game.won
    assert game.moves == 1
    assert FifteenPuzzle.best_moves == 1

    # Simulate the shell building a brand new instance for a relaunch.
    game2 = FifteenPuzzle(display)
    assert game2.best_moves == 1

    recorded = _spy_text(display, monkeypatch)
    game2.draw()
    assert any(t == "B:1" for t in recorded), recorded


def test_lightsout_reset_does_not_clear_best(monkeypatch):
    display = get_sim_display()
    LightsOut.best_level = 5
    game = LightsOut(display)
    game.reset()
    assert game.best_level == 5


def test_fifteenpuzzle_reset_does_not_clear_best(monkeypatch):
    display = get_sim_display()
    FifteenPuzzle.best_moves = 7
    game = FifteenPuzzle(display)
    game.reset()
    assert game.best_moves == 7


# ── Task 2: Network HUD hides p= in Barabasi-Albert mode ───────────────

def test_network_hides_p_label_in_ba_mode(monkeypatch):
    display = get_sim_display()
    net = Network(display)
    net.reset()

    net.model = 1  # Barabasi-Albert
    net._generate()
    recorded = _spy_text(display, monkeypatch)
    net.draw()
    assert not any(t.startswith("p=") for t in recorded), recorded


def test_network_shows_p_label_in_watts_strogatz_mode(monkeypatch):
    display = get_sim_display()
    net = Network(display)
    net.reset()

    net.model = 0  # Watts-Strogatz
    net._generate()
    recorded = _spy_text(display, monkeypatch)
    net.draw()
    assert any(t.startswith("p=") for t in recorded), recorded


# ── Task 3: Chess/Othello draw_game_over drops its own BTN:AGAIN ───────

def test_chess_draw_game_over_has_no_btn_again(monkeypatch):
    display = get_sim_display()
    game = Chess(display)
    game.is_checkmate = True
    game.game_over_reason = "WHITE WINS!"

    recorded = _spy_text(display, monkeypatch)
    game.draw_game_over()
    assert not any("BTN:AGAIN" in t for t in recorded), recorded


def test_othello_draw_game_over_has_no_btn_again(monkeypatch):
    display = get_sim_display()
    game = Othello(display)
    game.winner = None
    game.game_over_reason = "DRAW 32-32"

    recorded = _spy_text(display, monkeypatch)
    game.draw_game_over()
    assert not any("BTN:AGAIN" in t for t in recorded), recorded
