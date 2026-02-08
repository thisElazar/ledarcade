"""
LED Arcade Visuals Package
==========================
Collection of visual effects and animations for the 64x64 LED matrix.
These are non-interactive displays meant for ambiance, art, or demonstrations.
"""

from abc import ABC, abstractmethod
from typing import Tuple

# Import the display system from arcade
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from arcade import Display, Colors, GRID_SIZE


class Visual(ABC):
    """Base class for all visual effects."""

    name: str = "Unnamed Visual"
    description: str = ""

    def __init__(self, display: Display):
        self.display = display
        self.time = 0.0  # Total elapsed time
        self.wants_exit = False  # Set True to return to menu
        self.reset()

    @abstractmethod
    def reset(self):
        """Reset the visual to initial state."""
        pass

    @abstractmethod
    def update(self, dt: float):
        """Update visual state. dt is delta time in seconds."""
        self.time += dt

    @abstractmethod
    def draw(self):
        """Draw the visual to the display."""
        pass

    def handle_input(self, input_state) -> bool:
        """
        Optional: Handle input for interactive visuals.
        Return True if input was consumed, False otherwise.
        Default implementation does nothing.
        """
        return False

    def _draw_loading(self, progress, label=""):
        """Draw a universal loading screen with green progress bar.

        Args:
            progress: 0.0 to 1.0 fill amount
            label: optional text shown below the title (e.g. "HEROES")
        """
        self.display.clear()
        self.display.draw_text_small(2, 20, self.name, (200, 160, 40))
        if label:
            self.display.draw_text_small(2, 28, label, (180, 180, 180))
        bar_x, bar_y, bar_w, bar_h = 4, 38, 56, 6
        self.display.draw_rect(bar_x, bar_y, bar_w, bar_h, (80, 80, 80),
                               filled=False)
        fill_w = int((bar_w - 2) * max(0.0, min(1.0, progress)))
        if fill_w > 0:
            self.display.draw_rect(bar_x + 1, bar_y + 1, fill_w, bar_h - 2,
                                   (0, 200, 0))


# Import all visuals
from .plasma import Plasma
from .starfield import Starfield
from .fire import Fire
from .matrix import Matrix
from .life import Life
from .clock import Clock
from .weather import Weather
from .dvd import DVD
from .lava import Lava
from .slime import Slime
from .solitaire import Solitaire
from .polaroid import Polaroid
from .road import Road
from .bml import BML
from .highway import Highway
from .intersection import Intersection
from .roundabout import Roundabout
from .interchange import Interchange
from .greenwave import GreenWave
from .merge import Merge
from .waterlilies import WaterLilies
from .starrynight import StarryNight
from .mobius import Mobius
from .lake import Lake
from .quarks import Quarks
from .hodge import Hodge
from .faders import Faders
from .ripples import Ripples
from .aurora import Aurora
from .gyre import Gyre
from .rug import Rug
from .trance import Trance
from .wolfram import Wolfram
from .mitosis import Mitosis
from .boids import Boids
from .attractors import Attractors
from .flux import Flux
from .cat import Cat
from .xorpattern import XORPattern
from .twister import Twister
from .rotozoom import Rotozoom
from .rainbow import Rainbow
from .moire import Moire
from .cylon import Cylon
from .sinescroller import SineScroller
from .mondrian import Mondrian
from .copperbars import CopperBars
from .greatwave import GreatWave
from .gallery3d import (GalleryArt, GallerySprites, GalleryAutomata,
                        GalleryScience, GalleryDigital, GalleryEffects,
                        GallerySalon, GallerySMB3, GalleryKirby,
                        GalleryArt as Gallery3D)
from .win95maze import Win95Maze
from .demonspirals import DemonSpirals
from .particlelife import ParticleLife
from .fireflies import Fireflies
from .starwarsca import StarWarsCA
from .truchet import Truchet
from .sandpile import Sandpile
from .scream import Scream
from .mario import Mario
from .sonic import Sonic
from .link import Link
from .metroid import MetroidChase
from .yoshi import Yoshi
from .kirby import Kirby
from .spidey import Spidey
from .batman import Batman
from .greenlantern import GreenLantern
from .megaman import MegaMan
from .settings import Settings
from .gamma import Gamma
from .timers import Timers
from .effects import Effects
from .testpattern import TestPattern
from .about import About
from .sysinfo import SysInfo
from .credits import Credits
from .controls import Controls
from .inputtest import InputTest
from .shutdown import Shutdown
from .refresh import Refresh
from .newtoncradle import NewtonCradle
from .dblpendulum import DblPendulum
from .orbits import OrbitsSolar, OrbitsMulti, OrbitsBelt
from .emfield import Coulomb
from .wavetank import WaveTank
from .optics import Optics
from .radioactive import Radioactive
from .turing import TuringPatterns
from .neurons import Neurons
from .fluid import FluidTunnel, FluidInk, FluidMixing
from .earth import Earth
from .molecule import Molecule
from .lattice import Lattice
from .proteins import Proteins
from .periodic import Periodic
from .microscope import Microscope
from .cell import Cell
from .dna import DNA
from .spectroscope import Spectroscope
from .oscilloscope import Oscilloscope
from .chladni import Chladni
from .theremin import Theremin
from .equalizer import Equalizer
from .metronome import Metronome
from .turntable import Turntable
from .drummachine import DrumMachine
from .jukebox import Jukebox
from .synthesizer import Synthesizer
from .watchgears import WatchGears
from .camshaft import Camshaft
from .grandfather import GrandfatherClock
from .locomotive import Locomotive
from .modelt import ModelT
from .beamengine import BeamEngine
from .singer import Singer
from .projector import Projector
from .typewriter import Typewriter
from .musicbox import MusicBox
from .pianoroll import PianoRoll
from .gutenberg import GutenbergPress
from .orrery import Orrery
from .gyroscope import Gyroscope
from .curta import Curta
from .loom import Loom
from .jacquard import Jacquard
from .gramophone import Gramophone
from .hurdygurdy import HurdyGurdy
from .antikythera import Antikythera
from .astrolabe import Astrolabe
from .archimedes import Archimedes
from .wondercabinet import (WonderGlow, WonderMarquee, WonderCrawl,
                            WonderSlide, WonderDrop, WonderSpin,
                            WonderPacMan, WonderInvaders, WonderTetris,
                            WonderMatrix, WonderNeon, WonderFilm,
                            WonderRetroTV, WonderDK, WonderFrogger,
                            WonderLife, WonderHodge, WonderStarWars,
                            WonderBoids, WonderSlime, WonderDiffusion,
                            WonderBrain, WonderFlow, WonderSand,
                            WonderPong, WonderSega, WonderPS1,
                            WonderInsertCoin, WonderCreeper, WonderNyanCat,
                            WonderC64, WonderGameBoy, WonderDOS,
                            WonderBSOD, WonderLoading, WonderColorBars,
                            WonderVHS, WonderBoing,
                            WonderNES, WonderN64, WonderAtari,
                            WonderBreakout, WonderSnake, WonderAsteroids,
                            WonderDoom, WonderPipe, WonderWinXP,
                            WonderGlitch, WonderTypewriter, WonderZoom,
                            WonderVinyl, WonderCassette)
from .agariodemo import AgarioDemo
from .arkanoid_demo import ArkanoidDemo
from .asteroidsdemo import AsteroidsDemo
from .bombermandemo import BombermanDemo
from .bowlingdemo import BowlingDemo
from .breakoutdemo import BreakoutDemo
from .burgertimedemo import BurgerTimeDemo
from .centipededemo import CentipedeDemo
from .checkersdemo import CheckersDemo
from .chessdemo import ChessDemo
from .dartsdemo import DartsDemo
from .defenderdemo import DefenderDemo
from .digdugdemo import DigDugDemo
from .donkeykongdemo import DonkeyKongDemo
from .flappydemo import FlappyDemo
from .froggerdemo import FroggerDemo
from .galagademo import GalagaDemo
from .game2048demo import Game2048Demo
from .geometrydemo import GeometryDemo
from .indy500demo import Indy500Demo
from .invadersdemo import InvadersDemo
from .jezzballdemo import JezzBallDemo
from .lightsoutdemo import LightsOutDemo
from .loderunnerdemo import LodeRunnerDemo
from .lunarlanderdemo import LunarLanderDemo
from .monstermazedemo import MonsterMazeDemo
from .mspacmandemo import MsPacManDemo
from .nightdriverdemo import NightDriverDemo
from .othellodemo import OthelloDemo
from .pacmandemo import PacManDemo
from .pinballdemo import PinballDemo
from .pipedreamdemo import PipeDreamDemo
from .pongdemo import PongDemo
from .qbertdemo import QBertDemo
from .skifreedemo import SkiFreeDemo
from .snakedemo import SnakeDemo
from .spacecruisedemo import SpaceCruiseDemo
from .stackdemo import StackDemo
from .stickrunnerdemo import StickRunnerDemo
from .tetrisdemo import TetrisDemo
from .trashblasterdemo import TrashBlasterDemo
from .slideshow import (
    Slideshow, AllVisuals, Chill, Energy, ArtGallery,
    SpriteGallery, SuperheroGallery, Demoscene, Complexity,
    ScienceLab, Title, Demos, MusicMix,
)

# List of all available visuals
ALL_VISUALS = [
    Plasma,
    Starfield,
    Fire,
    Matrix,
    Life,
    Clock,
    Weather,
    DVD,
    Lava,
    Slime,
    Solitaire,
    Polaroid,
    Road,
    WaterLilies,
    StarryNight,
    Mobius,
    Lake,
    Quarks,
    Hodge,
    Faders,
    Ripples,
    Aurora,
    Gyre,
    Rug,
    Trance,
    Wolfram,
    Mitosis,
    Boids,
    Attractors,
    Flux,
    Cat,
    XORPattern,
    Twister,
    Rotozoom,
    Rainbow,
    Moire,
    Cylon,
    SineScroller,
    Mondrian,
    CopperBars,
    GreatWave,
    GalleryArt,
    GallerySprites,
    GalleryAutomata,
    GalleryScience,
    GalleryDigital,
    GalleryEffects,
    GallerySalon,
    GallerySMB3,
    GalleryKirby,
    Win95Maze,
    DemonSpirals,
    ParticleLife,
    Fireflies,
    StarWarsCA,
    Truchet,
    Sandpile,
    Scream,
    Mario,
    Sonic,
    Link,
    MetroidChase,
    Yoshi,
    Kirby,
    Spidey,
    Batman,
    GreenLantern,
    MegaMan,
    Settings,
    Gamma,
    Timers,
    Effects,
    TestPattern,
    About,
    SysInfo,
    Credits,
    Controls,
    InputTest,
    Shutdown,
    Refresh,
    NewtonCradle,
    DblPendulum,
    OrbitsSolar,
    OrbitsMulti,
    OrbitsBelt,
    Coulomb,
    WaveTank,
    Optics,
    Radioactive,
    TuringPatterns,
    Neurons,
    FluidTunnel,
    FluidInk,
    FluidMixing,
    Earth,
    Molecule,
    Lattice,
    Proteins,
    Periodic,
    Microscope,
    Cell,
    DNA,
    Spectroscope,
    Oscilloscope,
    Chladni,
    Theremin,
    Equalizer,
    Metronome,
    Turntable,
    DrumMachine,
    Jukebox,
    Synthesizer,
    WatchGears,
    Camshaft,
    GrandfatherClock,
    Locomotive,
    ModelT,
    BeamEngine,
    Singer,
    Projector,
    Typewriter,
    MusicBox,
    PianoRoll,
    GutenbergPress,
    Orrery,
    Gyroscope,
    Curta,
    Loom,
    Jacquard,
    Gramophone,
    HurdyGurdy,
    Antikythera,
    Astrolabe,
    Archimedes,
    WonderGlow,
    WonderMarquee,
    WonderCrawl,
    WonderSlide,
    WonderDrop,
    WonderSpin,
    WonderPacMan,
    WonderInvaders,
    WonderTetris,
    WonderMatrix,
    WonderNeon,
    WonderFilm,
    WonderRetroTV,
    WonderDK,
    WonderFrogger,
    WonderLife,
    WonderHodge,
    WonderStarWars,
    WonderBoids,
    WonderSlime,
    WonderDiffusion,
    WonderBrain,
    WonderFlow,
    WonderSand,
    WonderPong,
    WonderSega,
    WonderPS1,
    WonderInsertCoin,
    WonderCreeper,
    WonderNyanCat,
    WonderC64,
    WonderGameBoy,
    WonderDOS,
    WonderBSOD,
    WonderLoading,
    WonderColorBars,
    WonderVHS,
    WonderBoing,
    WonderNES,
    WonderN64,
    WonderAtari,
    WonderBreakout,
    WonderSnake,
    WonderAsteroids,
    WonderDoom,
    WonderPipe,
    WonderWinXP,
    WonderGlitch,
    WonderTypewriter,
    WonderZoom,
    WonderVinyl,
    WonderCassette,
    BML,
    Highway,
    Intersection,
    Roundabout,
    Interchange,
    GreenWave,
    Merge,
    # Slideshows (visual playlists)
    Title,
    AllVisuals,
    Chill,
    Energy,
    ArtGallery,
    SpriteGallery,
    SuperheroGallery,
    Demoscene,
    Complexity,
    ScienceLab,
    MusicMix,
    # Individual game demos
    AgarioDemo,
    ArkanoidDemo,
    AsteroidsDemo,
    BombermanDemo,
    BowlingDemo,
    BreakoutDemo,
    BurgerTimeDemo,
    CentipedeDemo,
    CheckersDemo,
    ChessDemo,
    DartsDemo,
    DefenderDemo,
    DigDugDemo,
    DonkeyKongDemo,
    FlappyDemo,
    FroggerDemo,
    GalagaDemo,
    Game2048Demo,
    GeometryDemo,
    Indy500Demo,
    InvadersDemo,
    JezzBallDemo,
    LightsOutDemo,
    LodeRunnerDemo,
    LunarLanderDemo,
    MonsterMazeDemo,
    MsPacManDemo,
    NightDriverDemo,
    OthelloDemo,
    PacManDemo,
    PinballDemo,
    PipeDreamDemo,
    PongDemo,
    QBertDemo,
    SkiFreeDemo,
    SnakeDemo,
    SpaceCruiseDemo,
    StackDemo,
    StickRunnerDemo,
    TetrisDemo,
    TrashBlasterDemo,
    # Demo slideshow (plays all demos)
    Demos,
]

__all__ = [
    'Visual',
    'Display',
    'Colors',
    'GRID_SIZE',
    'ALL_VISUALS',
    'Plasma',
    'Starfield',
    'Fire',
    'Matrix',
    'Life',
    'Clock',
    'Weather',
    'DVD',
    'Lava',
    'Slime',
    'Solitaire',
    'Polaroid',
    'Road',
    'WaterLilies',
    'StarryNight',
    'Mobius',
    'Lake',
    'Quarks',
    'Hodge',
    'Faders',
    'Ripples',
    'Aurora',
    'Gyre',
    'Rug',
    'Trance',
    'Wolfram',
    'Mitosis',
    'Boids',
    'Attractors',
    'Flux',
    'Cat',
    'XORPattern',
    'Twister',
    'Rotozoom',
    'Rainbow',
    'Moire',
    'Cylon',
    'SineScroller',
    'Mondrian',
    'CopperBars',
    'GreatWave',
    'GalleryArt',
    'GallerySprites',
    'GalleryAutomata',
    'GalleryScience',
    'GalleryDigital',
    'GalleryEffects',
    'GallerySalon',
    'GallerySMB3',
    'GalleryKirby',
    'Gallery3D',
    'Win95Maze',
    'DemonSpirals',
    'ParticleLife',
    'Fireflies',
    'StarWarsCA',
    'Truchet',
    'Sandpile',
    'Scream',
    'Mario',
    'Sonic',
    'Link',
    'MetroidChase',
    'Yoshi',
    'Kirby',
    'Spidey',
    'Batman',
    'GreenLantern',
    'MegaMan',
    'Settings',
    'Gamma',
    'Timers',
    'TestPattern',
    'About',
    'SysInfo',
    'Credits',
    'Controls',
    'InputTest',
    'Shutdown',
    'Refresh',
    'NewtonCradle',
    'DblPendulum',
    'OrbitsSolar',
    'OrbitsMulti',
    'OrbitsBelt',
    'Coulomb',
    'WaveTank',
    'Optics',
    'Radioactive',
    'TuringPatterns',
    'Neurons',
    'FluidTunnel',
    'FluidInk',
    'FluidMixing',
    'Earth',
    'Molecule',
    'Lattice',
    'Proteins',
    'Periodic',
    'Microscope',
    'Cell',
    'DNA',
    'Spectroscope',
    'Oscilloscope',
    'Chladni',
    'Theremin',
    'Equalizer',
    'Metronome',
    'Turntable',
    'DrumMachine',
    'Jukebox',
    'Synthesizer',
    'WatchGears',
    'Camshaft',
    'GrandfatherClock',
    'Locomotive',
    'ModelT',
    'BeamEngine',
    'Singer',
    'Projector',
    'Typewriter',
    'MusicBox',
    'PianoRoll',
    'GutenbergPress',
    'Orrery',
    'Gyroscope',
    'Curta',
    'Loom',
    'Jacquard',
    'Gramophone',
    'HurdyGurdy',
    'Antikythera',
    'Astrolabe',
    'Archimedes',
    'BML',
    'Highway',
    'Intersection',
    'Roundabout',
    'Interchange',
    'GreenWave',
    'Merge',
    'Slideshow',
    'AllVisuals',
    'Chill',
    'Energy',
    'ArtGallery',
    'SpriteGallery',
    'SuperheroGallery',
    'Demoscene',
    'Complexity',
    'ScienceLab',
    'MusicMix',
    'Demos',
    'AgarioDemo',
    'DefenderDemo',
    'MonsterMazeDemo',
]
