"""Headless smoke tests for every visual and game.

These do not check that anything *looks* right — that stays a human-on-the-cabinet
check, forever. They catch the class of bug a cloud runner *can* catch: a visual or
game that crashes on construction or in its first frames, a playlist that references
a renamed class, or an import that breaks the whole catalog (white screen on boot).

Each item is constructed against a real headless Display and run for a few frames,
exactly the way the main loop drives it.
"""
import pytest

from arcade import Display, InputState
from visuals import ALL_VISUALS
from games import ALL_GAMES

FRAMES = 10
DT = 1.0 / 30.0

# Playlists live in ALL_GAMES alongside real games; they're flagged by a `games`
# attribute and are driven differently (the menu picks a game *from* them).
REAL_GAMES = [g for g in ALL_GAMES if not hasattr(g, "games")]
PLAYLISTS = [g for g in ALL_GAMES if hasattr(g, "games")]

_display = None


def _get_display():
    """One shared headless Display for the whole session (pygame.init is once-only)."""
    global _display
    if _display is None:
        _display = Display()
    return _display


@pytest.mark.parametrize("cls", ALL_VISUALS, ids=lambda c: c.__name__)
def test_visual_constructs_and_runs(cls):
    obj = cls(_get_display())  # __init__ also calls reset()
    for _ in range(FRAMES):
        obj.update(DT)
        obj.draw()


@pytest.mark.parametrize("cls", REAL_GAMES, ids=lambda c: c.__name__)
def test_game_constructs_and_runs(cls):
    inp = InputState()
    obj = cls(_get_display())
    for _ in range(FRAMES):
        obj.update(inp, DT)
        obj.draw()


@pytest.mark.parametrize("cls", PLAYLISTS, ids=lambda c: c.__name__)
def test_playlist_is_populated_and_constructible(cls):
    # _init_all_playlists() swallows ImportError silently, so a renamed/removed game
    # leaves `.games` empty and selecting the playlist on a cabinet crashes on
    # random.choice([]). Assert it's populated and every member actually constructs.
    assert cls.games, f"{cls.__name__}.games is empty — a broken import in _init_games?"
    display = _get_display()
    for game_cls in cls.games:
        game_cls(display)
