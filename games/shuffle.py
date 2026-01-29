"""
Game Playlists (Shuffle Mode)
=============================
Playlist descriptors for game shuffle mode. These are NOT Game subclasses —
the main loop detects them via hasattr(item_class, 'games') and picks a
random game from the list to instantiate.
"""


class GamePlaylist:
    """Base class for game playlists."""
    name = "Game Playlist"
    description = "A curated mix of games"
    category = "game_mix"
    games = []


class AllGames(GamePlaylist):
    name = "ALL GAMES"
    description = "Every single-player game, shuffled"
    # Populated dynamically in games/__init__.py after ALL_GAMES is built
    games = []


class ArcadeMix(GamePlaylist):
    name = "ARCADE MIX"
    description = "Classic arcade cabinet games"

    @classmethod
    def _init_games(cls):
        from games import (Snake, Breakout, Invaders, Tetris, Asteroids,
                           Frogger, PacMan, NightDriver, Pong, Galaga,
                           Centipede, DigDug, LodeRunner, DonkeyKong,
                           QBert, Bomberman, LunarLander)
        cls.games = [Snake, Breakout, Invaders, Tetris, Asteroids,
                     Frogger, PacMan, NightDriver, Pong, Galaga,
                     Centipede, DigDug, LodeRunner, DonkeyKong,
                     QBert, Bomberman, LunarLander]


class QuickPlay(GamePlaylist):
    name = "QUICK PLAY"
    description = "Fast, pick-up-and-play games"

    @classmethod
    def _init_games(cls):
        from games import Snake, Flappy, Stack, GeometryDash, StickRunner, Breakout
        cls.games = [Snake, Flappy, Stack, GeometryDash, StickRunner, Breakout]


class Shooters(GamePlaylist):
    name = "SHOOTERS"
    description = "Space shooters and blasters"

    @classmethod
    def _init_games(cls):
        from games import Invaders, Galaga, Centipede, Asteroids, SpaceCruise
        cls.games = [Invaders, Galaga, Centipede, Asteroids, SpaceCruise]


class Puzzle(GamePlaylist):
    name = "PUZZLE"
    description = "Brain teasers and puzzle games"

    @classmethod
    def _init_games(cls):
        from games import Tetris, Game2048, PipeDream, LightsOut
        cls.games = [Tetris, Game2048, PipeDream, LightsOut]


class Classics(GamePlaylist):
    name = "CLASSICS"
    description = "All-time classic games"

    @classmethod
    def _init_games(cls):
        from games import PacMan, Snake, Breakout, Frogger, Pong
        cls.games = [PacMan, Snake, Breakout, Frogger, Pong]


# Initialize games lists for playlists with static lists
def _init_all_playlists():
    for cls in [ArcadeMix, QuickPlay, Shooters, Puzzle, Classics]:
        cls._init_games()

_init_all_playlists()
