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
from .slimelab import SlimeLab
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
from .painting import PAINTING_VISUALS
from .plates import Haeckel, Audubon, Merian, Redoute, Gould
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
from .mitosislab import MitosisLab
from .balloons import Balloons
from .boids import Boids
from .boidslab import BoidsLab
from .attractors import Attractors
from .flux import Flux
from .cat import Cat
from .aquarium import Aquarium
from .xorpattern import XORPattern
from .twister import Twister
from .rotozoom import Rotozoom
from .rainbow import Rainbow
from .moire import Moire
from .cylon import Cylon
from .sinescroller import SineScroller
from .copperbars import CopperBars
from .gallery3d import (GalleryArt, GallerySprites, GalleryAutomata,
                        GalleryScience, GalleryDigital, GalleryEffects,
                        GallerySalon, GalleryMuseum,
                        GalleryArt as Gallery3D)
from .win95maze import Win95Maze
from .demonspirals import DemonSpirals
from .particlelife import ParticleLife
from .fireflies import Fireflies
from .starwarsca import StarWarsCA
from .truchet import Truchet
from .sandpile import Sandpile
from .settings import Settings
from .gamma import Gamma
from .timers import Timers
from .effects import Effects
from .testpattern import TestPattern
from .about import About
from .sysinfo import SysInfo
from .credits import Credits
from .stats import Stats
from .controls import Controls
from .shutdown import Shutdown
from .wifi_config import WiFiConfig
from .refresh import Refresh
from .idlemix import IdleMix
from .paint import Paint
from .paint_gif import PaintGif
from .newtoncradle import NewtonCradle
from .dblpendulum import DblPendulum
from .orbits import OrbitsSolar, OrbitsMulti, OrbitsBelt
from .emfield import Coulomb
from .wavetank import WaveTank
from .optics import Optics
from .radioactive import Radioactive
from .turing import TuringPatterns
from .grayscott import GrayScott
from .hodgelab import HodgeLab
from .ruglab import RugLab
from .cycliclab import CyclicLab
from .quarkslab import QuarksLab
from .lenia import Lenia, LeniaLab
from .neurons import Neurons
from .fluid import FluidTunnel, FluidInk, FluidMixing
from .earth import Earth
from .molecule import Molecule
from .lattice import Lattice
from .proteins import Proteins
from .peptides import Peptides
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
from .chordchart import ChordChart
from .rudiments import DrumRudiments
from .latindna import LatinDNA
from .latingrooves import LatinGrooves
from .sauces import Sauces
from .flavors import Flavors
from .baking import Baking
from .pantry import Pantry
from .pasta import Pasta
from .spices import Spices
from .knife import Knife
from .knots import Knots
from .colortheory import ColorTheory
from .butcher import Butcher
from .scales import Scales
from .circle5ths import CircleOfFifths
from .clouds import Clouds
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
from .frozen_lake import FrozenLake
from .crystallize import Crystallize
from .drift import DriftVisual
from .drift3d import Drift3D
from .wondercabinet import (WonderGlow, WonderMarquee, WonderCrawl,
                            WonderSlide, WonderDrop, WonderSpin,
                            WonderPacMan, WonderInvaders, WonderTetris,
                            WonderMatrix, WonderNeon, WonderFilm,
                            WonderRetroTV, WonderDK, WonderFrogger,
                            WonderLife, WonderHodge, WonderStarWars,
                            WonderBoids, WonderSlime, WonderDiffusion,
                            WonderBrain, WonderFlow, WonderSand,
                            WonderSauron, WonderPong, WonderSega, WonderPS1,
                            WonderInsertCoin, WonderCreeper, WonderNyanCat,
                            WonderC64, WonderGameBoy, WonderDOS,
                            WonderBSOD, WonderLoading, WonderColorBars,
                            WonderVHS, WonderBoing,
                            WonderNES, WonderN64, WonderAtari,
                            WonderBreakout, WonderSnake, WonderAsteroids,
                            WonderDoom, WonderPipe, WonderWinXP,
                            WonderGlitch, WonderTypewriter, WonderZoom,
                            WonderVinyl, WonderCassette,
                            WonderVertigo, WonderStargate, WonderPsycho,
                            WonderNosferatu, WonderJaws, WonderShining,
                            WonderET, WonderAlien, WonderExorcist,
                            WonderTerminator, WonderGodzilla,
                            WonderBladeRunner, WonderCloseEncounters,
                            WonderTron, WonderJurassicPark,
                            WonderIndiana, WonderMetropolis,
                            WonderKingKong, WonderWizardOz,
                            WonderGhostbusters)
from .agariodemo import AgarioDemo
from .arkanoid_demo import ArkanoidDemo
from .bloonsdemo import BloonsDemo
from .bloonstddemo import BloonsTDDemo
from .asteroidsdemo import AsteroidsDemo
from .bombermandemo import BombermanDemo
from .bowlingdemo import BowlingDemo
from .breakoutdemo import BreakoutDemo
from .burgertimedemo import BurgerTimeDemo
from .centipededemo import CentipedeDemo
from .checkersdemo import CheckersDemo
from .chessdemo import ChessDemo
from .connect4demo import Connect4Demo
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
from .mancalademo import MancalaDemo
from .monstermazedemo import MonsterMazeDemo
from .mspacmandemo import MsPacManDemo
from .nightdriverdemo import NightDriverDemo
from .othellodemo import OthelloDemo
from .pacmandemo import PacManDemo
from .pinballdemo import PinballDemo
from .pipedreamdemo import PipeDreamDemo
from .pooldemo import PoolDemo
from .pongdemo import PongDemo
from .qbertdemo import QBertDemo
from .shuffleboarddemo import ShuffleboardDemo
from .skifreedemo import SkiFreeDemo
from .snakedemo import SnakeDemo
from .spacecruisedemo import SpaceCruiseDemo
from .stackdemo import StackDemo
from .stickrunnerdemo import StickRunnerDemo
from .tetrisdemo import TetrisDemo
from .trashblasterdemo import TrashBlasterDemo
from .moon import MoonPhases
from .constellations import Constellations
from .fractals import Fractals
from .primes import Primes
from .fibonacci import Fibonacci
from .pi import Pi
from .solids import Solids
from .tessellations import Tessellations
from .spirograph import Spirograph
from .watercycle import WaterCycle
from .flags import Flags
from .weaving import Weaving
from .signs import Signs
from .matter import MatterPhases
from .slideshow import (
    Slideshow, AllVisuals, Chill, Energy, ArtGallery,
    Demoscene, Complexity,
    ScienceLab, Title, Demos, MusicMix, Customs, Education,
    Naturalist,
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
    SlimeLab,
    Solitaire,
    Polaroid,
    Road,
    Mobius,
    Lake,
    Quarks,
    QuarksLab,
    Hodge,
    Faders,
    Ripples,
    Aurora,
    Gyre,
    Rug,
    Trance,
    Wolfram,
    Mitosis,
    MitosisLab,
    Balloons,
    Boids,
    BoidsLab,
    Attractors,
    Flux,
    FrozenLake,
    Crystallize,
    Cat,
    Aquarium,
    XORPattern,
    Twister,
    Rotozoom,
    Rainbow,
    Moire,
    Cylon,
    SineScroller,
    CopperBars,
    GalleryArt,
    GallerySprites,
    GalleryAutomata,
    GalleryScience,
    GalleryDigital,
    GalleryEffects,
    GallerySalon,
    GalleryMuseum,
    *PAINTING_VISUALS,
    Haeckel,
    Audubon,
    Merian,
    Redoute,
    Gould,
    Win95Maze,
    DemonSpirals,
    ParticleLife,
    Fireflies,
    StarWarsCA,
    Truchet,
    Sandpile,
    Settings,
    Gamma,
    Timers,
    Effects,
    TestPattern,
    About,
    SysInfo,
    Credits,
    Stats,
    Controls,
    Shutdown,
    WiFiConfig,
    Refresh,
    IdleMix,
    Paint,
    PaintGif,
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
    GrayScott,
    HodgeLab,
    RugLab,
    CyclicLab,
    Lenia,
    LeniaLab,
    Neurons,
    FluidTunnel,
    FluidInk,
    FluidMixing,
    Earth,
    Molecule,
    Lattice,
    Proteins,
    Peptides,
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
    ChordChart,
    DrumRudiments,
    LatinDNA,
    LatinGrooves,
    Sauces,
    Flavors,
    Baking,
    Pantry,
    Pasta,
    Spices,
    Knife,
    Knots,
    ColorTheory,
    Butcher,
    Scales,
    CircleOfFifths,
    Clouds,
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
    DriftVisual,
    Drift3D,
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
    WonderSauron,
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
    WonderVertigo,
    WonderStargate,
    WonderPsycho,
    WonderNosferatu,
    WonderJaws,
    WonderShining,
    WonderET,
    WonderAlien,
    WonderExorcist,
    WonderTerminator,
    WonderGodzilla,
    WonderBladeRunner,
    WonderCloseEncounters,
    WonderTron,
    WonderJurassicPark,
    WonderIndiana,
    WonderMetropolis,
    WonderKingKong,
    WonderWizardOz,
    WonderGhostbusters,
    BML,
    Highway,
    Intersection,
    Roundabout,
    Interchange,
    GreenWave,
    Merge,
    MoonPhases,
    Constellations,
    Fractals,
    Primes,
    Fibonacci,
    Pi,
    Solids,
    Tessellations,
    Spirograph,
    WaterCycle,
    Flags,
    Weaving,
    Signs,
    MatterPhases,
    # Slideshows (visual playlists)
    Title,
    AllVisuals,
    Chill,
    Energy,
    ArtGallery,
    Demoscene,
    Complexity,
    ScienceLab,
    MusicMix,
    Customs,
    Education,
    Naturalist,
    Demos,
    # Individual game demos
    AgarioDemo,
    ArkanoidDemo,
    AsteroidsDemo,
    BloonsDemo,
    BloonsTDDemo,
    BombermanDemo,
    BowlingDemo,
    BreakoutDemo,
    BurgerTimeDemo,
    CentipedeDemo,
    CheckersDemo,
    ChessDemo,
    Connect4Demo,
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
    MancalaDemo,
    MonsterMazeDemo,
    MsPacManDemo,
    NightDriverDemo,
    OthelloDemo,
    PacManDemo,
    PinballDemo,
    PipeDreamDemo,
    PoolDemo,
    PongDemo,
    QBertDemo,
    ShuffleboardDemo,
    SkiFreeDemo,
    SnakeDemo,
    SpaceCruiseDemo,
    StackDemo,
    StickRunnerDemo,
    TetrisDemo,
    TrashBlasterDemo,
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
    'PAINTING_VISUALS',
    'Haeckel',
    'Audubon',
    'Merian',
    'Redoute',
    'Gould',
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
    'Balloons',
    'Boids',
    'Attractors',
    'Flux',
    'Cat',
    'Aquarium',
    'XORPattern',
    'Twister',
    'Rotozoom',
    'Rainbow',
    'Moire',
    'Cylon',
    'SineScroller',
    'CopperBars',
    'GalleryArt',
    'GallerySprites',
    'GalleryAutomata',
    'GalleryScience',
    'GalleryDigital',
    'GalleryEffects',
    'GallerySalon',
    'GalleryMuseum',
    'Gallery3D',
    'Win95Maze',
    'DemonSpirals',
    'ParticleLife',
    'Fireflies',
    'StarWarsCA',
    'Truchet',
    'Sandpile',
    'Settings',
    'Gamma',
    'Timers',
    'TestPattern',
    'About',
    'SysInfo',
    'Credits',
    'Stats',
    'Controls',
    'Shutdown',
    'Refresh',
    'IdleMix',
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
    'GrayScott',
    'HodgeLab',
    'RugLab',
    'CyclicLab',
    'Lenia',
    'LeniaLab',
    'Neurons',
    'FluidTunnel',
    'FluidInk',
    'FluidMixing',
    'Earth',
    'Molecule',
    'Lattice',
    'Proteins',
    'Peptides',
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
    'ChordChart',
    'DrumRudiments',
    'LatinDNA',
    'LatinGrooves',
    'Sauces',
    'Flavors',
    'Baking',
    'Pantry',
    'Pasta',
    'Spices',
    'Knife',
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
    'Crystallize',
    'DriftVisual',
    'Drift3D',
    'BML',
    'Highway',
    'Intersection',
    'Roundabout',
    'Interchange',
    'GreenWave',
    'Merge',
    'MoonPhases',
    'Constellations',
    'Fractals',
    'Primes',
    'Fibonacci',
    'Pi',
    'Solids',
    'Tessellations',
    'Spirograph',
    'WaterCycle',
    'Flags',
    'Signs',
    'MatterPhases',
    'Slideshow',
    'AllVisuals',
    'Chill',
    'Energy',
    'ArtGallery',
    'Demoscene',
    'Complexity',
    'ScienceLab',
    'MusicMix',
    'Customs',
    'Education',
    'Naturalist',
    'Demos',
    'AgarioDemo',
    'DefenderDemo',
    'MonsterMazeDemo',
]

# Load local/personal visuals (copyrighted content, user add-ons)
try:
    from .local import LOCAL_VISUALS
    ALL_VISUALS.extend(LOCAL_VISUALS)
except Exception:
    pass
