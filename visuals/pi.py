"""
PI - Irrational beauty
========================
Two equal-length arms rotate from a shared pivot: inner at rate 1,
outer at rate pi. Because pi is irrational, the traced path never
closes -- creating an ever-more-intricate pattern of near-misses.

Controls:
  Up/Down    - Cycle palette
  Left/Right - Rotation speed
  Button     - Toggle arms / reset trail
"""

import math
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


PALETTE_NAMES = ['RAINBOW', 'FIRE', 'OCEAN', 'VIOLET', 'ICE', 'MONO']


def _pal_rainbow(t):
    return _hsv(t % 1.0, 0.9, 1.0)


def _pal_fire(t):
    return _hsv((t * 0.12) % 1.0, 1.0, 1.0)


def _pal_ocean(t):
    return _hsv((0.5 + t * 0.15) % 1.0, 0.9, 0.9)


def _pal_violet(t):
    return _hsv((0.7 + t * 0.15) % 1.0, 0.85, 0.95)


def _pal_ice(t):
    return _hsv((0.5 + t * 0.08) % 1.0, 0.5, 0.8 + 0.2 * t)


def _pal_mono(t):
    v = int(180 + 75 * t)
    return (v, v, v)


PALETTES = [_pal_rainbow, _pal_fire, _pal_ocean, _pal_violet, _pal_ice, _pal_mono]

MAX_TRAIL = 2500
ARM_LEN = 14.0  # pixels — two arms fill nicely in 64x64


class Pi(Visual):
    name = "PI"
    description = "Irrational beauty"
    category = "math"

    def reset(self):
        self.time = 0.0
        self.theta = 0.0
        self.speed = 1.0
        self.palette_idx = 0
        self.show_arms = True
        self.overlay_timer = 0.0
        self.trail = []  # list of (x, y) in pixel coords

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
            self.speed = max(0.1, self.speed - 0.1)
            consumed = True
        if input_state.right:
            self.speed = min(5.0, self.speed + 0.1)
            consumed = True
        if input_state.action_l or input_state.action_r:
            if self.trail:
                # First press: toggle arms
                self.show_arms = not self.show_arms
            else:
                self.show_arms = True
            # If arms already toggled off, reset trail
            if not self.show_arms:
                pass  # just toggled off
            consumed = True
        return consumed

    def update(self, dt):
        self.time += dt
        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

        # Advance angle
        self.theta += self.speed * dt * 0.8

        # Compute tip position
        cx, cy = 32.0, 30.0
        L = ARM_LEN
        tip_x = cx + L * math.cos(self.theta) + L * math.cos(math.pi * self.theta)
        tip_y = cy + L * math.sin(self.theta) + L * math.sin(math.pi * self.theta)

        # Add to trail (subpixel stored as float, draw as int)
        self.trail.append((tip_x, tip_y))
        if len(self.trail) > MAX_TRAIL:
            self.trail = self.trail[-MAX_TRAIL:]

    def draw(self):
        d = self.display
        d.clear()

        pal = PALETTES[self.palette_idx]
        n = len(self.trail)

        # Draw trail with age-based fading and hue shift
        for i, (tx, ty) in enumerate(self.trail):
            px, py = int(tx), int(ty)
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                # age: 0.0 = oldest, 1.0 = newest
                age = i / n if n > 1 else 1.0
                # Hue position shifts along trail length
                hue_t = (i / 400.0) % 1.0
                r, g, b = pal(hue_t)
                # Fade: oldest points dim, newest bright
                bright = 0.15 + 0.85 * age
                r = int(r * bright)
                g = int(g * bright)
                b = int(b * bright)
                d.set_pixel(px, py, (r, g, b))

        # Draw arms
        if self.show_arms:
            cx, cy = 32.0, 30.0
            L = ARM_LEN
            # Joint (end of inner arm)
            jx = cx + L * math.cos(self.theta)
            jy = cy + L * math.sin(self.theta)
            # Tip
            tip_x = jx + L * math.cos(math.pi * self.theta)
            tip_y = jy + L * math.sin(math.pi * self.theta)

            # Dim arm lines
            arm_color = (50, 50, 60)
            d.draw_line(int(cx), int(cy), int(jx), int(jy), arm_color)
            d.draw_line(int(jx), int(jy), int(tip_x), int(tip_y), arm_color)

            # Pivot dot
            d.set_pixel(int(cx), int(cy), (120, 120, 140))
            # Joint dot — bright
            d.set_pixel(int(jx), int(jy), (200, 200, 255))
            # Tip dot — brightest
            d.set_pixel(int(tip_x), int(tip_y), (255, 255, 255))

        # Tiny label
        d.draw_text_small(2, 58, "PI", (80, 80, 100))

        # Palette overlay
        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            c = (int(200 * alpha), int(200 * alpha), int(200 * alpha))
            d.draw_text_small(2, 2, PALETTE_NAMES[self.palette_idx], c)
