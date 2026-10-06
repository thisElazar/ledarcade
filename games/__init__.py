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
from .monstermaze import MonsterMaze
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
from .portal import Portal
from .bloons import Bloons
from .bloonstd import BloonsTD
from .sandgame import SandGame
from .drift import Drift
from .lasermirrors import LaserMirrors
from .windowwasher import WindowWasher
from .fishing import Fishing
from .fortress import Fortress
from .doom import Doom
from .handheld import Handheld
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
    MonsterMaze,
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
    Portal,
    Bloons,
    BloonsTD,
    SandGame,
    Drift,
    LaserMirrors,
    WindowWasher,
    Fishing,
    Fortress,
    Doom,
    Handheld,
    AllGames,
    ArcadeMix,
    QuickPlay,
    Shooters,
    Puzzle,
    Classics,
]

# AllGames.games is populated by catalog.register_games() after dev_only
# filtering, so dev_only games don't leak into the shuffle playlist.

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
    'MonsterMaze',
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
    'Portal',
    'Bloons',
    'BloonsTD',
    'SandGame',
    'Drift',
    'LaserMirrors',
    'WindowWasher',
    'Fishing',
    'Fortress',
    'Doom',
    'Handheld',
    'ALL_GAMES',
    'AllGames',
    'ArcadeMix',
    'QuickPlay',
    'Shooters',
    'Puzzle',
    'Classics',
]
