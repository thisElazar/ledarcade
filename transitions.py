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


class RandomDissolve(Transition):
    """Random pixels flip from old to new frame."""

    name = "Random Dissolve"
    duration = 1.5

    def __init__(self):
        super().__init__()
        self._pixel_order = None

    def reset(self):
        super().reset()
        # Generate shuffled list of all pixel coordinates
        self._pixel_order = [(x, y) for y in range(GRID_SIZE) for x in range(GRID_SIZE)]
        random.shuffle(self._pixel_order)

    def draw(self, display, get_old_frame, get_new_frame):
        old_frame = get_old_frame()
        new_frame = get_new_frame()

        # Number of pixels that should show new frame
        num_new = int(self.progress * GRID_SIZE * GRID_SIZE)

        # Create set of coordinates showing new frame for fast lookup
        new_pixels = set(self._pixel_order[:num_new])

        display.clear()
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if (x, y) in new_pixels:
                    display.set_pixel(x, y, new_frame[y][x])
                else:
                    display.set_pixel(x, y, old_frame[y][x])


class DitherDissolve(Transition):
    """Ordered 4x4 Bayer dither pattern reveals new image."""

    name = "Dither Dissolve"
    duration = 1.5

    # Standard Bayer 4x4 dither matrix
    BAYER_MATRIX = [
        [0,  8,  2, 10],
        [12, 4, 14,  6],
        [3, 11,  1,  9],
        [15, 7, 13,  5],
    ]

    def draw(self, display, get_old_frame, get_new_frame):
        old_frame = get_old_frame()
        new_frame = get_new_frame()

        # Threshold scales from 0 to 16 based on progress
        threshold = self.progress * 16

        display.clear()
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                # Get dither value at this position (tiles the 4x4 pattern)
                dither_value = self.BAYER_MATRIX[y % 4][x % 4]

                if threshold > dither_value:
                    display.set_pixel(x, y, new_frame[y][x])
                else:
                    display.set_pixel(x, y, old_frame[y][x])


class HorizontalWipe(Transition):
    """Reveal new image from left to right."""

    name = "Horizontal Wipe"
    duration = 1.0

    def draw(self, display, get_old_frame, get_new_frame):
        old_frame = get_old_frame()
        new_frame = get_new_frame()
        threshold = int(self.progress * GRID_SIZE)

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if x < threshold:
                    display.set_pixel(x, y, new_frame[y][x])
                else:
                    display.set_pixel(x, y, old_frame[y][x])


class VerticalWipe(Transition):
    """Reveal new image from top to bottom."""

    name = "Vertical Wipe"
    duration = 1.0

    def draw(self, display, get_old_frame, get_new_frame):
        old_frame = get_old_frame()
        new_frame = get_new_frame()
        threshold = int(self.progress * GRID_SIZE)

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if y < threshold:
                    display.set_pixel(x, y, new_frame[y][x])
                else:
                    display.set_pixel(x, y, old_frame[y][x])


class IrisWipe(Transition):
    """Circular reveal from center outward."""

    name = "Iris Wipe"
    duration = 1.2

    def draw(self, display, get_old_frame, get_new_frame):
        old_frame = get_old_frame()
        new_frame = get_new_frame()
        center_x, center_y = 32, 32
        radius = self.progress * 45

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                dx = x - center_x
                dy = y - center_y
                distance = math.sqrt(dx * dx + dy * dy)
                if distance < radius:
                    display.set_pixel(x, y, new_frame[y][x])
                else:
                    display.set_pixel(x, y, old_frame[y][x])


class CRTOff(Transition):
    """Classic CRT TV turn-off effect - vertical collapse to line, then horizontal to point."""

    name = "CRT Off"
    duration = 1.5

    def draw(self, display, get_old_frame, get_new_frame):
        p = self.progress
        display.clear(Colors.BLACK)

        if p < 0.5:
            # First half: old image collapses vertically to horizontal line at y=32
            frame = get_old_frame()
            collapse = p / 0.5  # 0 to 1
            half_height = int((1.0 - collapse) * 32)
            if half_height < 1:
                half_height = 1

            center_y = GRID_SIZE // 2
            for y in range(GRID_SIZE):
                dist_from_center = y - center_y
                if abs(dist_from_center) <= half_height:
                    src_y = center_y + int(dist_from_center * 32 / half_height)
                    src_y = max(0, min(GRID_SIZE - 1, src_y))
                    brightness = 1.0 + collapse * 0.5
                    for x in range(GRID_SIZE):
                        r, g, b = frame[src_y][x]
                        r = min(255, int(r * brightness))
                        g = min(255, int(g * brightness))
                        b = min(255, int(b * brightness))
                        display.set_pixel(x, y, (r, g, b))
        elif p < 0.55:
            # Bright horizontal line
            center_y = GRID_SIZE // 2
            for x in range(GRID_SIZE):
                display.set_pixel(x, center_y, Colors.WHITE)
        elif p < 0.75:
            # Line shrinks horizontally to center point
            shrink = (p - 0.55) / 0.2
            half_width = int((1.0 - shrink) * 32)
            center_x = GRID_SIZE // 2
            center_y = GRID_SIZE // 2
            for x in range(center_x - half_width, center_x + half_width + 1):
                if 0 <= x < GRID_SIZE:
                    display.set_pixel(x, center_y, Colors.WHITE)
        elif p < 0.8:
            # Brief black pause
            pass
        else:
            # New image expands from center
            frame = get_new_frame()
            expand = (p - 0.8) / 0.2
            half_height = max(1, int(expand * 32))

            center_y = GRID_SIZE // 2
            for y in range(GRID_SIZE):
                dist_from_center = y - center_y
                if abs(dist_from_center) <= half_height:
                    src_y = center_y + int(dist_from_center * 32 / half_height)
                    src_y = max(0, min(GRID_SIZE - 1, src_y))
                    brightness = 1.0 + (1.0 - expand) * 0.5
                    for x in range(GRID_SIZE):
                        r, g, b = frame[src_y][x]
                        r = min(255, int(r * brightness))
                        g = min(255, int(g * brightness))
                        b = min(255, int(b * brightness))
                        display.set_pixel(x, y, (r, g, b))


class Scanline(Transition):
    """Reveals new image row by row with bright scan line at edge."""

    name = "Scanline"
    duration = 1.2

    def draw(self, display, get_old_frame, get_new_frame):
        old_frame = get_old_frame()
        new_frame = get_new_frame()
        scan_row = int(self.progress * GRID_SIZE)

        for y in range(GRID_SIZE):
            if y < scan_row:
                for x in range(GRID_SIZE):
                    display.set_pixel(x, y, new_frame[y][x])
            elif y == scan_row:
                for x in range(GRID_SIZE):
                    r, g, b = new_frame[y][x]
                    r = min(255, int(r * 1.5) + 80)
                    g = min(255, int(g * 1.5) + 80)
                    b = min(255, int(b * 1.5) + 80)
                    display.set_pixel(x, y, (r, g, b))
            else:
                for x in range(GRID_SIZE):
                    r, g, b = old_frame[y][x]
                    r = int(r * 0.7)
                    g = int(g * 0.7)
                    b = int(b * 0.7)
                    display.set_pixel(x, y, (r, g, b))


class Pixelate(Transition):
    """Mosaic effect - old image pixelates, swaps to new, then de-pixelates."""

    name = "Pixelate"
    duration = 1.5

    def draw(self, display, get_old_frame, get_new_frame):
        p = self.progress

        if p < 0.5:
            frame = get_old_frame()
            block_size = int(1 + (p / 0.5) * 7)
        else:
            frame = get_new_frame()
            block_size = int(8 - ((p - 0.5) / 0.5) * 7)

        block_size = max(1, min(8, block_size))

        for by in range(0, GRID_SIZE, block_size):
            for bx in range(0, GRID_SIZE, block_size):
                r_sum, g_sum, b_sum = 0, 0, 0
                count = 0

                for y in range(by, min(by + block_size, GRID_SIZE)):
                    for x in range(bx, min(bx + block_size, GRID_SIZE)):
                        r, g, b = frame[y][x]
                        r_sum += r
                        g_sum += g
                        b_sum += b
                        count += 1

                if count > 0:
                    avg_color = (r_sum // count, g_sum // count, b_sum // count)
                    for y in range(by, min(by + block_size, GRID_SIZE)):
                        for x in range(bx, min(bx + block_size, GRID_SIZE)):
                            display.set_pixel(x, y, avg_color)


class Blinds(Transition):
    """Vertical blinds flip to reveal new image with staggered timing."""

    name = "Blinds"
    duration = 1.5

    def draw(self, display, get_old_frame, get_new_frame):
        old_frame = get_old_frame()
        new_frame = get_new_frame()

        num_blinds = 8
        blind_width = GRID_SIZE // num_blinds

        for i in range(num_blinds):
            flip_start = i / (num_blinds + 2)
            flip_end = flip_start + 0.15

            x_start = i * blind_width
            x_end = x_start + blind_width

            if self.progress < flip_start:
                for y in range(GRID_SIZE):
                    for x in range(x_start, x_end):
                        display.set_pixel(x, y, old_frame[y][x])
            elif self.progress < flip_end:
                mid_x = x_start + blind_width // 2
                for y in range(GRID_SIZE):
                    for x in range(x_start, x_end):
                        if x == mid_x or x == mid_x - 1:
                            display.set_pixel(x, y, (255, 255, 255))
                        else:
                            display.set_pixel(x, y, (40, 40, 40))
            else:
                for y in range(GRID_SIZE):
                    for x in range(x_start, x_end):
                        display.set_pixel(x, y, new_frame[y][x])


# List of available transition types - add new ones here
TRANSITION_TYPES = [
    FadeToBlack,
    RandomDissolve,
    DitherDissolve,
    HorizontalWipe,
    VerticalWipe,
    IrisWipe,
    CRTOff,
    Scanline,
    Pixelate,
    Blinds,
]

# Enabled transitions - loaded from persistent settings
_enabled_transitions = None


def _load_enabled_transitions():
    """Load enabled transitions from persistent settings."""
    global _enabled_transitions
    import settings
    names = settings.get_enabled_transition_names()
    if names is None:
        # All enabled by default
        _enabled_transitions = set(TRANSITION_TYPES)
    else:
        # Map names back to classes
        name_to_class = {t.name: t for t in TRANSITION_TYPES}
        _enabled_transitions = set()
        for name in names:
            if name in name_to_class:
                _enabled_transitions.add(name_to_class[name])
        # Ensure at least one is enabled
        if not _enabled_transitions:
            _enabled_transitions = set(TRANSITION_TYPES)


def _save_enabled_transitions():
    """Save enabled transitions to persistent settings."""
    import settings
    if _enabled_transitions is None or _enabled_transitions == set(TRANSITION_TYPES):
        # All enabled - save as None (default)
        settings.set_enabled_transition_names(None)
    else:
        names = [t.name for t in _enabled_transitions]
        settings.set_enabled_transition_names(names)


def get_enabled_transitions() -> set:
    """Return the set of currently enabled transition classes."""
    global _enabled_transitions
    if _enabled_transitions is None:
        _load_enabled_transitions()
    return _enabled_transitions


def set_transition_enabled(transition_class, enabled: bool):
    """Enable or disable a transition type."""
    global _enabled_transitions
    if _enabled_transitions is None:
        _load_enabled_transitions()
    if enabled:
        _enabled_transitions.add(transition_class)
    else:
        # Don't allow disabling all transitions - keep at least one
        if len(_enabled_transitions) > 1:
            _enabled_transitions.discard(transition_class)
    _save_enabled_transitions()


def random_transition() -> Transition:
    """Create a random transition instance from enabled transitions."""
    enabled = list(get_enabled_transitions())
    if not enabled:
        enabled = [FadeToBlack]  # fallback
    cls = random.choice(enabled)
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
