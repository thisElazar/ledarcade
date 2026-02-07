"""
Visual Playlists (Slideshows)
=============================
Auto-cycling visual playlists that rotate through curated sets of visuals.
Hold 2 seconds to exit back to menu (handled by main loop).
"""

import random
from . import Visual
from arcade import InputState


def _randomize_style(visual):
    """Simulate random up-presses to randomize a visual's palette/style."""
    fake = InputState()
    presses = random.randint(0, 10)
    for _ in range(presses):
        fake.reset()
        fake.up_pressed = True
        visual.handle_input(fake)


class Slideshow(Visual):
    """Base class for visual playlists that auto-cycle through visuals."""

    name = "Slideshow"
    description = "Auto-cycling visual playlist"
    category = "visual_mix"
    cycle_interval = 30.0  # seconds between visual changes

    # Subclasses override this with a list of visual classes
    visual_classes = []

    def _get_visual_classes(self):
        """Hook for dynamic visual lists. Override in subclasses."""
        return list(self.visual_classes)

    def reset(self):
        self._queue = []
        self._child = None
        self._cycle_timer = 0.0
        self._advance()

    def _advance(self):
        """Pick the next visual from the shuffled queue."""
        if not self._queue:
            self._queue = self._get_visual_classes()
            random.shuffle(self._queue)
        if self._queue:
            cls = self._queue.pop()
            self._child = cls(self.display)
            self._child.reset()
            _randomize_style(self._child)
            self._cycle_timer = 0.0

    def update(self, dt):
        self.time += dt
        self._cycle_timer += dt
        if self._cycle_timer >= self.cycle_interval:
            self._advance()
        if self._child:
            self._child.update(dt)

    def draw(self):
        if self._child:
            self._child.draw()

    def handle_input(self, input_state):
        # Single button press skips to next visual
        if input_state.action_l or input_state.action_r:
            self._advance()
            return True
        # Pass only left/right (time controls) to child, block up/down (style)
        if not self._child:
            return False
        if not (input_state.left_pressed or input_state.right_pressed or
                input_state.left or input_state.right):
            return False
        filtered = InputState()
        filtered.left = input_state.left
        filtered.right = input_state.right
        filtered.left_pressed = input_state.left_pressed
        filtered.right_pressed = input_state.right_pressed
        return self._child.handle_input(filtered)


# ---------------------------------------------------------------------------
# Playlist subclasses
# ---------------------------------------------------------------------------

class AllVisuals(Slideshow):
    name = "ALL VISUALS"
    description = "Every non-utility visual, shuffled"

    # Category weights: higher = more frequent in rotation
    CATEGORY_WEIGHTS = {
        'automata': 4,
        'science': 4,
        'digital': 3,
        'nature': 3,
        'sprites': 3,
        'household': 3,
        'art': 2,
        'superheroes': 2,
        'road_rail': 2,
        'mechanics': 1,  # show less often
        'music': 3,
    }

    def _get_visual_classes(self):
        from visuals import ALL_VISUALS
        result = []
        for v in ALL_VISUALS:
            if issubclass(v, Slideshow):
                continue
            cat = getattr(v, 'category', '')
            if cat == 'utility':
                continue
            weight = self.CATEGORY_WEIGHTS.get(cat, 2)
            result.extend([v] * weight)
        return result


class Chill(Slideshow):
    name = "CHILL"
    description = "Relaxing, ambient visuals"

    def _get_visual_classes(self):
        from visuals import (Lake, Aurora, Starfield, Fireflies, Ripples,
                             Flux, Weather, Boids, WaterLilies, StarryNight)
        return [Lake, Aurora, Starfield, Fireflies, Ripples,
                Flux, Weather, Boids, WaterLilies, StarryNight]


class Energy(Slideshow):
    name = "ENERGY"
    description = "High-energy, intense visuals"

    def _get_visual_classes(self):
        from visuals import (Fire, Plasma, Trance, Rotozoom, Matrix,
                             Twister, CopperBars, Rainbow, Cylon, SineScroller)
        return [Fire, Plasma, Trance, Rotozoom, Matrix,
                Twister, CopperBars, Rainbow, Cylon, SineScroller]


class ArtGallery(Slideshow):
    name = "ART GALLERY"
    description = "Famous paintings and art reproductions"

    def _get_visual_classes(self):
        from visuals import GreatWave, Mondrian, Scream, StarryNight, WaterLilies
        return [GreatWave, Mondrian, Scream, StarryNight, WaterLilies]


class SpriteGallery(Slideshow):
    name = "SPRITE GALLERY"
    description = "Classic game character sprites"

    def _get_visual_classes(self):
        from visuals import Mario, Sonic, Link, MetroidChase, Yoshi, Kirby, MegaMan
        return [Mario, Sonic, Link, MetroidChase, Yoshi, Kirby, MegaMan]


class SuperheroGallery(Slideshow):
    name = "SUPERHEROES"
    description = "Superhero sprite animations"

    def _get_visual_classes(self):
        from visuals import Spidey, Batman, GreenLantern
        return [Spidey, Batman, GreenLantern]


class Demoscene(Slideshow):
    name = "DEMOSCENE"
    description = "Old-school demo effects"

    def _get_visual_classes(self):
        from visuals import (Fire, Plasma, Rotozoom, SineScroller, Twister,
                             CopperBars, Cylon, Trance, Moire, XORPattern)
        return [Fire, Plasma, Rotozoom, SineScroller, Twister,
                CopperBars, Cylon, Trance, Moire, XORPattern]


class Complexity(Slideshow):
    name = "COMPLEXITY"
    description = "Complex systems and emergent behavior"

    def _get_visual_classes(self):
        from visuals import (Rug, Quarks, Hodge, Ripples, Flux, Slime,
                             DemonSpirals, Life, ParticleLife, Aurora,
                             Gyre, Boids, Sandpile, Fireflies)
        return [Rug, Quarks, Hodge, Ripples, Flux, Slime,
                DemonSpirals, Life, ParticleLife, Aurora,
                Gyre, Boids, Sandpile, Fireflies]


class ScienceLab(Slideshow):
    name = "SCIENCE LAB"
    description = "Physics and biology simulations"

    def _get_visual_classes(self):
        from visuals import (Attractors, DblPendulum, Neurons,
                             OrbitsSolar, OrbitsMulti, OrbitsBelt,
                             Coulomb, WaveTank, Optics,
                             PendulumWave, Radioactive,
                             FluidTunnel, FluidInk, FluidMixing,
                             TuringPatterns, Mitosis, Earth, Molecule,
                             DNA, Spectroscope, Oscilloscope, Chladni)
        return [Attractors, DblPendulum, Neurons,
                OrbitsSolar, OrbitsMulti, OrbitsBelt,
                Coulomb, WaveTank, Optics,
                PendulumWave, Radioactive,
                FluidTunnel, FluidInk, FluidMixing,
                TuringPatterns, Mitosis, Earth, Molecule,
                DNA, Spectroscope, Oscilloscope, Chladni]


class Title(Slideshow):
    name = "TITLE"
    description = "Wonder Cabinet title screens"
    category = "visual_mix"

    def _get_visual_classes(self):
        import inspect
        import visuals.wondercabinet as wc
        return [obj for _, obj in inspect.getmembers(wc, inspect.isclass)
                if issubclass(obj, Visual) and obj is not Visual]


class MusicMix(Slideshow):
    name = "MUSIC MIX"
    description = "All music visuals"
    category = "visual_mix"

    def _get_visual_classes(self):
        from visuals import (MusicBox, Metronome, HurdyGurdy, Equalizer,
                             Turntable, PianoRoll, DrumMachine, Jukebox,
                             Theremin, Gramophone, Synthesizer)
        return [MusicBox, Metronome, HurdyGurdy, Equalizer,
                Turntable, PianoRoll, DrumMachine, Jukebox,
                Theremin, Gramophone, Synthesizer]


class Demos(Slideshow):
    name = "ALL"
    description = "AI plays all classic games"
    category = "demos"
    cycle_interval = 60.0  # Give each demo a full minute

    def _get_visual_classes(self):
        # Original 12 demos
        from visuals.pacmandemo import PacManDemo
        from visuals.tetrisdemo import TetrisDemo
        from visuals.snakedemo import SnakeDemo
        from visuals.invadersdemo import InvadersDemo
        from visuals.froggerdemo import FroggerDemo
        from visuals.breakoutdemo import BreakoutDemo
        from visuals.galagademo import GalagaDemo
        from visuals.defenderdemo import DefenderDemo
        from visuals.centipededemo import CentipedeDemo
        from visuals.donkeykongdemo import DonkeyKongDemo
        from visuals.qbertdemo import QBertDemo
        from visuals.asteroidsdemo import AsteroidsDemo
        from visuals.flappydemo import FlappyDemo
        # Batch 2: 8 more demos
        from visuals.pongdemo import PongDemo
        from visuals.mspacmandemo import MsPacManDemo
        from visuals.digdugdemo import DigDugDemo
        from visuals.bombermandemo import BombermanDemo
        from visuals.arkanoid_demo import ArkanoidDemo
        from visuals.game2048demo import Game2048Demo
        from visuals.geometrydemo import GeometryDemo
        from visuals.lunarlanderdemo import LunarLanderDemo
        # Batch 3: 8 more demos
        from visuals.skifreedemo import SkiFreeDemo
        from visuals.burgertimedemo import BurgerTimeDemo
        from visuals.loderunnerdemo import LodeRunnerDemo
        from visuals.nightdriverdemo import NightDriverDemo
        from visuals.pinballdemo import PinballDemo
        from visuals.stackdemo import StackDemo
        from visuals.jezzballdemo import JezzBallDemo
        from visuals.indy500demo import Indy500Demo
        # Batch 4: 8 more demos
        from visuals.spacecruisedemo import SpaceCruiseDemo
        from visuals.trashblasterdemo import TrashBlasterDemo
        from visuals.stickrunnerdemo import StickRunnerDemo
        from visuals.pipedreamdemo import PipeDreamDemo
        from visuals.lightsoutdemo import LightsOutDemo
        from visuals.bowlingdemo import BowlingDemo
        from visuals.dartsdemo import DartsDemo
        # Board games (historical AI)
        from visuals.chessdemo import ChessDemo
        from visuals.checkersdemo import CheckersDemo
        from visuals.othellodemo import OthelloDemo
        from visuals.agariodemo import AgarioDemo
        return [
            # Classic arcade
            PacManDemo, MsPacManDemo, GalagaDemo, DefenderDemo, InvadersDemo,
            CentipedeDemo, DonkeyKongDemo, QBertDemo, FroggerDemo, DigDugDemo,
            BurgerTimeDemo,
            # Action/puzzle
            TetrisDemo, BreakoutDemo, ArkanoidDemo, AsteroidsDemo, BombermanDemo,
            # Modern/casual
            FlappyDemo, Game2048Demo, SnakeDemo, StackDemo, GeometryDemo, AgarioDemo,
            # Racing/sports
            Indy500Demo, PongDemo, BowlingDemo, DartsDemo,
            # Simulation/other
            LunarLanderDemo, PinballDemo, SkiFreeDemo, NightDriverDemo,
            LodeRunnerDemo, JezzBallDemo, SpaceCruiseDemo, TrashBlasterDemo,
            StickRunnerDemo, PipeDreamDemo, LightsOutDemo,
            # Board games
            ChessDemo, CheckersDemo, OthelloDemo,
        ]
