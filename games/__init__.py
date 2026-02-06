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
from .mspacman import MsPacMan
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
from .agario import Agario
from .galaga import Galaga
from .defender import Defender
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
from .pool import Pool
from .burgertime import BurgerTime
from .dnd import DnD
from .bowling import Bowling
from .darts import Darts
from .shuffleboard import Shuffleboard
from .pinball import Pinball
from .fifteenpuzzle import FifteenPuzzle
from .simon import Simon
from .bopit import BopIt
from .mastermind import Mastermind
from .rushhour import RushHour
from .shuffle import (
    AllGames, ArcadeMix, QuickPlay, Shooters, Puzzle, Classics,
)

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
    MsPacMan,
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
    Agario,
    Galaga,
    Defender,
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
    Pool,
    BurgerTime,
    Bowling,
    DnD,
    Darts,
    Shuffleboard,
    Pinball,
    FifteenPuzzle,
    Simon,
    BopIt,
    Mastermind,
    RushHour,
    AllGames,
    ArcadeMix,
    QuickPlay,
    Shooters,
    Puzzle,
    Classics,
]

# Populate AllGames with all single-player, non-playlist games
AllGames.games = [g for g in ALL_GAMES
                  if getattr(g, 'category', '') != '2_player'
                  and not hasattr(g, 'games')]

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
    'MsPacMan',
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
    'Agario',
    'Galaga',
    'Defender',
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
    'Pool',
    'BurgerTime',
    'Bowling',
    'DnD',
    'Darts',
    'Shuffleboard',
    'Pinball',
    'FifteenPuzzle',
    'Simon',
    'BopIt',
    'Mastermind',
    'RushHour',
    'ALL_GAMES',
    'AllGames',
    'ArcadeMix',
    'QuickPlay',
    'Shooters',
    'Puzzle',
    'Classics',
]
