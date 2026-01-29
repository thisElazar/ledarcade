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
from .connect4 import Connect4
from .checkers import Checkers
from .othello import Othello
from .game2048 import Game2048
from .lightsout import LightsOut
from .pipedream import PipeDream
from .nightdriver import NightDriver
from .lunarlander import LunarLander
from .indy500 import Indy500
from .stickrunner import StickRunner
from .stack import Stack
from .geometrydash import GeometryDash
from .galaga import Galaga
from .centipede import Centipede
from .mancala import Mancala
from .go import Go
from .digdug import DigDug
from .loderunner import LodeRunner
from .donkeykong import DonkeyKong
from .qbert import QBert
from .bomberman import Bomberman
from .arkanoid import Arkanoid
from .skifree import SkiFree

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
    Connect4,
    Checkers,
    Othello,
    Game2048,
    LightsOut,
    PipeDream,
    NightDriver,
    LunarLander,
    Indy500,
    StickRunner,
    Stack,
    GeometryDash,
    Galaga,
    Centipede,
    Mancala,
    Go,
    DigDug,
    LodeRunner,
    DonkeyKong,
    QBert,
    Bomberman,
    Arkanoid,
    SkiFree,
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
    'Connect4',
    'Checkers',
    'Othello',
    'Game2048',
    'LightsOut',
    'PipeDream',
    'NightDriver',
    'LunarLander',
    'Indy500',
    'StickRunner',
    'Stack',
    'GeometryDash',
    'Galaga',
    'Centipede',
    'Mancala',
    'Go',
    'DigDug',
    'LodeRunner',
    'DonkeyKong',
    'QBert',
    'Bomberman',
    'Arkanoid',
    'SkiFree',
    'ALL_GAMES',
]
