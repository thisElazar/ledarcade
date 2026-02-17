"""
Visual Playlists (Slideshows)
=============================
Auto-cycling visual playlists that rotate through curated sets of visuals.
Hold 2 seconds to exit back to menu (handled by main loop).
"""

import os
import random
from . import Visual, GRID_SIZE
from arcade import InputState

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

GIF_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "paint_gif")


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
        elif self._child:
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
                             Flux, Weather, Boids, Lava, Gyre)
        return [Lake, Aurora, Starfield, Fireflies, Ripples,
                Flux, Weather, Boids, Lava, Gyre]


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
    description = "Famous paintings slideshow"

    def reset(self):
        self._show_nameplate = False  # user-controlled, persists across paintings
        super().reset()

    def _get_visual_classes(self):
        from visuals.painting import PAINTING_VISUALS
        return list(PAINTING_VISUALS)

    def _advance(self):
        """Pick next painting, skip randomize, carry overlay state."""
        if not self._queue:
            self._queue = self._get_visual_classes()
            random.shuffle(self._queue)
        if self._queue:
            cls = self._queue.pop()
            self._child = cls(self.display)
            self._child.reset()
            # Inherit nameplate state from previous painting
            self._child._show_overlay = self._show_nameplate
            self._child._overlay_alpha = 1.0 if self._show_nameplate else 0.0
            self._child._overlay_time = 0.0
            self._cycle_timer = 0.0

    def handle_input(self, input_state):
        # Button: skip to next painting
        if input_state.action_l or input_state.action_r:
            self._advance()
            return True
        # Any joystick press: toggle nameplate for current and future paintings
        if (input_state.up_pressed or input_state.down_pressed
                or input_state.left_pressed or input_state.right_pressed):
            self._show_nameplate = not self._show_nameplate
            if self._child and hasattr(self._child, '_show_overlay'):
                self._child._show_overlay = self._show_nameplate
                self._child._overlay_time = 0.0
            return True
        # Consume held joystick so menu doesn't see it
        if input_state.any_direction:
            return True
        return False


class Naturalist(Slideshow):
    name = "NATURALIST"
    description = "Scientific illustrations shuffled"
    category = "visual_mix"
    cycle_interval = 25.0

    def reset(self):
        self._show_nameplate = False
        super().reset()

    def _get_visual_classes(self):
        from visuals.plates import Haeckel, Audubon, Merian, Redoute, Gould
        return [Haeckel, Audubon, Merian, Redoute, Gould]

    def _advance(self):
        """Pick next collection, carry overlay state."""
        if not self._queue:
            self._queue = self._get_visual_classes()
            random.shuffle(self._queue)
        if self._queue:
            cls = self._queue.pop()
            self._child = cls(self.display)
            self._child.reset()
            # Inherit nameplate state from previous
            self._child._show_overlay = self._show_nameplate
            self._child._overlay_alpha = 1.0 if self._show_nameplate else 0.0
            self._child._overlay_time = 0.0
            self._cycle_timer = 0.0

    def handle_input(self, input_state):
        # Button: skip to next collection
        if input_state.action_l or input_state.action_r:
            self._advance()
            return True
        # Any joystick press: toggle nameplate
        if (input_state.up_pressed or input_state.down_pressed
                or input_state.left_pressed or input_state.right_pressed):
            self._show_nameplate = not self._show_nameplate
            if self._child and hasattr(self._child, '_show_overlay'):
                self._child._show_overlay = self._show_nameplate
                self._child._overlay_time = 0.0
            return True
        if input_state.any_direction:
            return True
        return False


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
                             Coulomb, WaveTank, Optics, Radioactive,
                             FluidTunnel, FluidInk, FluidMixing,
                             TuringPatterns, Mitosis, Earth, Molecule,
                             DNA, Spectroscope, Oscilloscope, Chladni)
        return [Attractors, DblPendulum, Neurons,
                OrbitsSolar, OrbitsMulti, OrbitsBelt,
                Coulomb, WaveTank, Optics, Radioactive,
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
                             Theremin, Gramophone, Synthesizer, ChordChart)
        return [MusicBox, Metronome, HurdyGurdy, Equalizer,
                Turntable, PianoRoll, DrumMachine, Jukebox,
                Theremin, Gramophone, Synthesizer, ChordChart]


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


# ---------------------------------------------------------------------------
# GIF Player — displays an exported GIF on the LED panel
# ---------------------------------------------------------------------------

class GifPlayer(Visual):
    """Plays a single GIF file frame-by-frame on the display."""

    name = "GIF"
    description = "Plays an animated GIF"
    category = "utility"

    _gif_path = None  # set by factory or subclass

    def reset(self):
        self.frames = []   # list of [(r,g,b) or None per pixel] row-major
        self.frame_idx = 0
        self.fps = 6
        self.timer = 0.0
        self._load()

    def _load(self):
        if not HAS_PIL or not self._gif_path or not os.path.exists(self._gif_path):
            return
        img = Image.open(self._gif_path)
        # Extract FPS from GIF duration
        duration = img.info.get('duration', 166)  # ms per frame
        if duration > 0:
            self.fps = max(1, min(24, round(1000 / duration)))
        try:
            while True:
                frame = img.convert("RGB")
                if frame.size != (GRID_SIZE, GRID_SIZE):
                    frame = frame.resize((GRID_SIZE, GRID_SIZE), Image.NEAREST)
                pixels = []
                for y in range(GRID_SIZE):
                    row = []
                    for x in range(GRID_SIZE):
                        r, g, b = frame.getpixel((x, y))
                        row.append((r, g, b) if (r or g or b) else None)
                    pixels.append(row)
                self.frames.append(pixels)
                img.seek(img.tell() + 1)
        except EOFError:
            pass

    def update(self, dt):
        self.time += dt
        if not self.frames:
            return
        self.timer += dt
        interval = 1.0 / self.fps
        if self.timer >= interval:
            self.timer -= interval
            self.frame_idx = (self.frame_idx + 1) % len(self.frames)

    def draw(self):
        self.display.clear()
        if not self.frames:
            self.display.draw_text_small(2, 28, "NO GIF", (255, 0, 0))
            return
        frame = self.frames[self.frame_idx]
        for y in range(GRID_SIZE):
            row = frame[y]
            for x in range(GRID_SIZE):
                pixel = row[x]
                if pixel:
                    self.display.set_pixel(x, y, pixel)

    def handle_input(self, input_state):
        return False


def _make_gif_visual(path):
    """Factory: create a GifPlayer subclass bound to a specific file."""
    gif_name = os.path.splitext(os.path.basename(path))[0].upper()

    class _Gif(GifPlayer):
        name = gif_name
        _gif_path = path
    return _Gif


class Customs(Slideshow):
    name = "CUSTOMS"
    description = "Your exported GIF animations"
    category = "visual_mix"
    cycle_interval = 15.0  # shorter cycle for user art

    def _get_visual_classes(self):
        if not os.path.isdir(GIF_DIR):
            return []
        gifs = sorted(f for f in os.listdir(GIF_DIR) if f.endswith(".gif"))
        return [_make_gif_visual(os.path.join(GIF_DIR, g)) for g in gifs]

    def _advance(self):
        """Pick next GIF; show message if none found."""
        if not self._queue:
            self._queue = self._get_visual_classes()
            random.shuffle(self._queue)
        if self._queue:
            cls = self._queue.pop()
            self._child = cls(self.display)
            self._child.reset()
            self._cycle_timer = 0.0
        else:
            self._child = None
            self._cycle_timer = 0.0

    def draw(self):
        if self._child:
            self._child.draw()
        else:
            self.display.clear()
            self.display.draw_text_small(2, 24, "NO GIFS", (180, 180, 180))
            self.display.draw_text_small(2, 34, "EXPORT FROM", (100, 100, 100))
            self.display.draw_text_small(2, 42, "PAINT GIF", (100, 100, 100))


class Education(Slideshow):
    name = "EDUCATION"
    description = "School-friendly educational visuals"
    category = "visual_mix"
    cycle_interval = 30.0

    def _get_visual_classes(self):
        from visuals import (
            MoonPhases, Constellations, Fractals, WaterCycle, Flags,
            MatterPhases, OrbitsSolar, OrbitsMulti, DNA, Periodic,
            Spectroscope, Microscope, Cell, Molecule, Chladni, Coulomb,
            Optics, WaveTank, Life, TuringPatterns, Boids, Orrery,
            Antikythera, Astrolabe,
        )
        return [
            MoonPhases, Constellations, Fractals, WaterCycle, Flags,
            MatterPhases, OrbitsSolar, OrbitsMulti, DNA, Periodic,
            Spectroscope, Microscope, Cell, Molecule, Chladni, Coulomb,
            Optics, WaveTank, Life, TuringPatterns, Boids, Orrery,
            Antikythera, Astrolabe,
        ]
