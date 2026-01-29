"""
Visual Playlists (Slideshows)
=============================
Auto-cycling visual playlists that rotate through curated sets of visuals.
Hold 2 seconds to exit back to menu (handled by main loop).
"""

import random
from visuals import Visual


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
        # Don't pass input to child — avoids confusing palette changes during auto-cycle
        return False


# ---------------------------------------------------------------------------
# Playlist subclasses
# ---------------------------------------------------------------------------

class AllVisuals(Slideshow):
    name = "ALL VISUALS"
    description = "Every non-utility visual, shuffled"

    def _get_visual_classes(self):
        from visuals import ALL_VISUALS
        return [v for v in ALL_VISUALS
                if not issubclass(v, Slideshow)
                and getattr(v, 'category', '') != 'utility']


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
        from visuals import Mario, Sonic
        return [Mario, Sonic]


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
