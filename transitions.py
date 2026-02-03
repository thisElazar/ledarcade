"""
Screensaver Transitions
=======================
Transition effects for cycling between idle screen visuals.

To add a new transition:
1. Create a class extending Transition
2. Implement update(dt) -> bool (return True when complete)
3. Implement draw(display, get_old_frame, get_new_frame)
4. Add to TRANSITION_TYPES list

get_old_frame and get_new_frame are callables that return the current
frame buffer as a 64x64 list of (r,g,b) tuples when called.
"""

import random
import math
from arcade import Colors, GRID_SIZE


class Transition:
    """Base class for visual transitions."""

    name = "Transition"
    duration = 1.0  # total transition time in seconds

    def __init__(self):
        self.progress = 0.0  # 0.0 to 1.0

    def reset(self):
        self.progress = 0.0

    def update(self, dt) -> bool:
        """Update transition state. Returns True when complete."""
        self.progress += dt / self.duration
        if self.progress >= 1.0:
            self.progress = 1.0
            return True
        return False

    def draw(self, display, get_old_frame, get_new_frame):
        """Draw the transition frame. Override in subclasses."""
        raise NotImplementedError


class FadeToBlack(Transition):
    """Fade out to black, then fade in new visual."""

    name = "Fade to Black"
    duration = 1.2  # 0.5s out + 0.2s hold + 0.5s in

    def draw(self, display, get_old_frame, get_new_frame):
        p = self.progress

        if p < 0.4:
            # Fade out old visual (0.0 - 0.4)
            fade = 1.0 - (p / 0.4)
            frame = get_old_frame()
        elif p < 0.6:
            # Hold black (0.4 - 0.6)
            fade = 0.0
            frame = None
        else:
            # Fade in new visual (0.6 - 1.0)
            fade = (p - 0.6) / 0.4
            frame = get_new_frame()

        display.clear(Colors.BLACK)
        if frame and fade > 0:
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    r, g, b = frame[y][x]
                    r = int(r * fade)
                    g = int(g * fade)
                    b = int(b * fade)
                    if r > 0 or g > 0 or b > 0:
                        display.set_pixel(x, y, (r, g, b))


# List of available transition types - add new ones here
TRANSITION_TYPES = [
    FadeToBlack,
]


def random_transition() -> Transition:
    """Create a random transition instance."""
    cls = random.choice(TRANSITION_TYPES)
    return cls()


class TransitionManager:
    """
    Manages transitions between idle screen visuals.

    Usage:
        tm = TransitionManager()

        # In idle loop:
        if time_to_switch:
            tm.start(new_visual)

        if tm.transitioning:
            tm.update(dt)
            tm.draw(display, old_visual, new_visual)
        else:
            current_visual.draw()
    """

    def __init__(self):
        self.transitioning = False
        self.transition = None
        self._old_visual = None
        self._new_visual = None
        self._old_frame = None  # cached frame buffer

    def start(self, old_visual, new_visual):
        """Begin a transition from old_visual to new_visual."""
        self.transitioning = True
        self.transition = random_transition()
        self.transition.reset()
        self._old_visual = old_visual
        self._new_visual = new_visual
        self._old_frame = None

    def update(self, dt) -> bool:
        """
        Update transition. Returns True when transition completes.
        When complete, transitioning is set to False.
        """
        if not self.transitioning:
            return False

        done = self.transition.update(dt)
        if done:
            self.transitioning = False
            self._old_visual = None
            self._old_frame = None
            return True
        return False

    def draw(self, display):
        """Draw the current transition frame."""
        if not self.transitioning:
            return

        def get_old_frame():
            # Cache old frame since visual may be gone
            if self._old_frame is None and self._old_visual:
                self._old_frame = self._capture_frame(display, self._old_visual)
            return self._old_frame or self._black_frame()

        def get_new_frame():
            if self._new_visual:
                return self._capture_frame(display, self._new_visual)
            return self._black_frame()

        self.transition.draw(display, get_old_frame, get_new_frame)

    def _capture_frame(self, display, visual):
        """Render a visual and capture its frame buffer."""
        visual.draw()
        # Copy the frame buffer
        frame = []
        for y in range(GRID_SIZE):
            row = []
            for x in range(GRID_SIZE):
                row.append(display.get_pixel(x, y))
            frame.append(row)
        return frame

    def _black_frame(self):
        """Return a black frame buffer."""
        return [[(0, 0, 0) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
