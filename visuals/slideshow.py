"""
Visual Playlists (Slideshows)
=============================
Auto-cycling visual playlists that rotate through curated sets of visuals.
Hold 2 seconds to exit back to menu (handled by main loop).
"""

import random
from visuals import Visual
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
    category = "wildcard"
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
        'mechanics': 1,  # show less often
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
    category = "wildcard"

    def _get_visual_classes(self):
        from visuals import Spidey, Batman
        return [Spidey, Batman]


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
    category = "wildcard"

    def _get_visual_classes(self):
        from visuals import (Attractors, DblPendulum, Neurons,
                             OrbitsSolar, OrbitsMulti, OrbitsBelt,
                             EMMotor, EMCircuit, EMFreeAir,
                             FluidTunnel, FluidInk, FluidMixing,
                             TuringSpots, TuringStripes, TuringCoral,
                             TuringWorms, Mitosis, Earth, Molecule)
        return [Attractors, DblPendulum, Neurons,
                OrbitsSolar, OrbitsMulti, OrbitsBelt,
                EMMotor, EMCircuit, EMFreeAir,
                FluidTunnel, FluidInk, FluidMixing,
                TuringSpots, TuringStripes, TuringCoral,
                TuringWorms, Mitosis, Earth, Molecule]
