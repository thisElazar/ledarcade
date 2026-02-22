"""
FIBONACCI - Phyllotaxis sunflower
==================================
Seeds spiral outward using the golden angle (137.508 deg),
filling the display in a continuous bloom.

Controls:
  Up/Down    - Cycle palette
  Left/Right - Adjust speed
  Button     - Reset with new scale
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE


def _hsv(h, s, v):
    c = v * s
    x = c * (1 - abs((h * 6) % 2 - 1))
    m = v - c
    if h < 1/6:   r, g, b = c, x, 0
    elif h < 2/6: r, g, b = x, c, 0
    elif h < 3/6: r, g, b = 0, c, x
    elif h < 4/6: r, g, b = 0, x, c
    elif h < 5/6: r, g, b = x, 0, c
    else:          r, g, b = c, 0, x
    return (int((r + m) * 255), int((g + m) * 255), int((b + m) * 255))


GOLDEN_ANGLE = 137.508  # degrees

# Palettes: each is a function (t in 0..1) -> (r,g,b)
PALETTE_NAMES = ['RAINBOW', 'WARM', 'COOL', 'GOLD', 'NEON', 'EARTH']


def _pal_rainbow(t):
    return _hsv(t % 1.0, 0.9, 1.0)


def _pal_warm(t):
    return _hsv((t * 0.15) % 1.0, 0.95, 1.0)


def _pal_cool(t):
    return _hsv((0.5 + t * 0.2) % 1.0, 0.85, 0.95)


def _pal_gold(t):
    # Gold to brown gradient
    v = 0.5 + 0.5 * math.sin(t * math.pi * 2)
    return (int(200 + 55 * v), int(150 + 70 * v), int(20 + 40 * v))


def _pal_neon(t):
    return _hsv((t * 0.5) % 1.0, 1.0, 1.0)


def _pal_earth(t):
    # Green-brown-orange
    return _hsv((0.08 + t * 0.12) % 1.0, 0.7, 0.6 + 0.3 * math.sin(t * 4))


PALETTES = [_pal_rainbow, _pal_warm, _pal_cool, _pal_gold, _pal_neon, _pal_earth]

MAX_SEEDS = 1600
HOLD_TIME = 2.0
FADE_TIME = 0.8
GLOW_TIME = 0.3


class Fibonacci(Visual):
    name = "FIBONACCI"
    description = "Sunflower phyllotaxis"
    category = "math"

    def reset(self):
        self.time = 0.0
        self.seed_count = 0.0
        self.speed = 1.0
        self.palette_idx = 0
        self.scale = 1.6 + random.random() * 0.3
        self.overlay_timer = 0.0
        self._state = 'build'  # build | hold | fade
        self._hold_timer = 0.0
        self._fade_timer = 0.0

    def handle_input(self, input_state):
        consumed = False
        if input_state.up_pressed:
            self.palette_idx = (self.palette_idx - 1) % len(PALETTES)
            self.overlay_timer = 2.0
            consumed = True
        if input_state.down_pressed:
            self.palette_idx = (self.palette_idx + 1) % len(PALETTES)
            self.overlay_timer = 2.0
            consumed = True
        if input_state.left:
            self.speed = max(0.2, self.speed - 0.1)
            consumed = True
        if input_state.right:
            self.speed = min(4.0, self.speed + 0.1)
            consumed = True
        if input_state.action_l or input_state.action_r:
            self.scale = 1.4 + random.random() * 0.5
            self.seed_count = 0.0
            self._state = 'build'
            self._hold_timer = 0.0
            self._fade_timer = 0.0
            consumed = True
        return consumed

    def update(self, dt):
        self.time += dt
        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

        if self._state == 'build':
            self.seed_count = min(MAX_SEEDS, self.seed_count + self.speed * 120 * dt)
            if self.seed_count >= MAX_SEEDS:
                self._state = 'hold'
                self._hold_timer = HOLD_TIME
        elif self._state == 'hold':
            self._hold_timer -= dt
            if self._hold_timer <= 0:
                self._state = 'fade'
                self._fade_timer = FADE_TIME
        elif self._state == 'fade':
            self._fade_timer -= dt
            if self._fade_timer <= 0:
                # Auto-reset with new palette and slight scale variation
                self.palette_idx = (self.palette_idx + 1) % len(PALETTES)
                self.scale = 1.4 + random.random() * 0.5
                self.seed_count = 0.0
                self._state = 'build'

    def draw(self):
        d = self.display
        d.clear()

        count = int(self.seed_count)
        cx, cy = 32, 30
        pal = PALETTES[self.palette_idx]

        # Fade alpha for fade-out state
        fade_alpha = 1.0
        if self._state == 'fade':
            fade_alpha = max(0.0, self._fade_timer / FADE_TIME)

        for n in range(1, count + 1):
            angle = math.radians(n * GOLDEN_ANGLE)
            radius = self.scale * math.sqrt(n)
            px = int(cx + radius * math.cos(angle))
            py = int(cy + radius * math.sin(angle))
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                hue_t = (n / 200.0) % 1.0
                r, g, b = pal(hue_t)

                # Glow effect on newest seeds
                age = (count - n) / 120.0  # ~seconds since placed
                if age < GLOW_TIME:
                    glow = 1.0 - age / GLOW_TIME
                    r = min(255, int(r + (255 - r) * glow))
                    g = min(255, int(g + (255 - g) * glow))
                    b = min(255, int(b + (255 - b) * glow))

                # Apply fade-out
                if fade_alpha < 1.0:
                    r = int(r * fade_alpha)
                    g = int(g * fade_alpha)
                    b = int(b * fade_alpha)

                d.set_pixel(px, py, (r, g, b))

        # Palette label
        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            c = (int(200 * alpha), int(200 * alpha), int(200 * alpha))
            d.draw_text_small(2, 2, PALETTE_NAMES[self.palette_idx], c)
