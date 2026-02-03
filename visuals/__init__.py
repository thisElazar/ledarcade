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
from .emfield import EMMotor, EMCircuit, EMFreeAir
from .turing import TuringSpots, TuringStripes, TuringCoral, TuringWorms
from .neurons import Neurons
from .fluid import FluidTunnel, FluidInk, FluidMixing
from .earth import Earth
from .molecule import Molecule
from .metronome import Metronome
from .watchgears import WatchGears
from .camshaft import Camshaft
from .grandfather import GrandfatherClock
from .locomotive import Locomotive
from .modelt import ModelT
from .singer import Singer
from .projector import Projector
from .testrig import TestRig
from .typewriter import Typewriter
from .musicbox import MusicBox
from .gutenberg import GutenbergPress
from .pacmandemo import PacManDemo
from .arkanoid_demo import ArkanoidDemo
from .lunarlanderdemo import LunarLanderDemo
from .pinballdemo import PinballDemo
from .burgertimedemo import BurgerTimeDemo
from .loderunnerdemo import LodeRunnerDemo
from .pipedreamdemo import PipeDreamDemo
from .shuffledemo import ShuffleDemo
from .slideshow import (
    Slideshow, AllVisuals, Chill, Energy, ArtGallery,
    SpriteGallery, SuperheroGallery, Demoscene, Complexity,
    ScienceLab, Demos,
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
    EMMotor,
    EMCircuit,
    EMFreeAir,
    TuringSpots,
    TuringStripes,
    TuringCoral,
    TuringWorms,
    Neurons,
    FluidTunnel,
    FluidInk,
    FluidMixing,
    Earth,
    Molecule,
    Metronome,
    WatchGears,
    Camshaft,
    GrandfatherClock,
    Locomotive,
    ModelT,
    Singer,
    Projector,
    TestRig,
    Typewriter,
    MusicBox,
    GutenbergPress,
    BurgerTimeDemo,
    LodeRunnerDemo,
    ShuffleDemo,
    PipeDreamDemo,
    AllVisuals,
    Chill,
    Energy,
    ArtGallery,
    SpriteGallery,
    SuperheroGallery,
    Demoscene,
    Complexity,
    ScienceLab,
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
    'EMMotor',
    'EMCircuit',
    'EMFreeAir',
    'TuringSpots',
    'TuringStripes',
    'TuringCoral',
    'TuringWorms',
    'Neurons',
    'FluidTunnel',
    'FluidInk',
    'FluidMixing',
    'Earth',
    'Molecule',
    'Metronome',
    'WatchGears',
    'Camshaft',
    'GrandfatherClock',
    'Locomotive',
    'ModelT',
    'Singer',
    'Projector',
    'TestRig',
    'Typewriter',
    'MusicBox',
    'GutenbergPress',
    'BurgerTimeDemo',
    'LodeRunnerDemo',
    'ShuffleDemo',
    'PipeDreamDemo',
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
    'Demos',
]
