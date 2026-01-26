"""
LED Arcade Games Package
========================
Collection of classic arcade games for the 64x64 LED matrix.
"""

from .snake import Snake
from .breakout import Breakout
from .pong import Pong
from .invaders import Invaders
from .tetris import Tetris
from .asteroids import Asteroids
from .flappy import Flappy
from .jezzball import JezzBall
from .frogger import Frogger
from .pacman import PacMan
from .chess import Chess
from .trashblaster import TrashBlaster
from .spacecruise import SpaceCruise

# List of all available games
ALL_GAMES = [
    Snake,
    Pong,
    Breakout,
    Invaders,
    Tetris,
    Asteroids,
    Flappy,
    JezzBall,
    Frogger,
    PacMan,
    Chess,
    TrashBlaster,
    SpaceCruise,
]

__all__ = [
    'Snake',
    'Pong',
    'Breakout',
    'Invaders',
    'Tetris',
    'Asteroids',
    'Flappy',
    'JezzBall',
    'Frogger',
    'PacMan',
    'Chess',
    'TrashBlaster',
    'SpaceCruise',
    'ALL_GAMES',
]
