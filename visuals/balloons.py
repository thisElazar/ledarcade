"""Balloons visual – a cheerful bundle of colorful balloons floating and swaying."""

import math
import random

from . import Visual, Display, Colors, GRID_SIZE

# Color palettes
PALETTES = [
    # Pastel
    [
        (255, 182, 193),  # pink
        (173, 216, 230),  # light blue
        (255, 255, 153),  # light yellow
        (177, 225, 168),  # light green
        (221, 160, 221),  # plum
        (255, 218, 185),  # peach
        (176, 224, 230),  # powder blue
        (255, 200, 200),  # salmon pink
    ],
    # Primary
    [
        (220, 30, 30),
        (30, 100, 220),
        (230, 200, 20),
        (20, 180, 40),
        (200, 50, 200),
        (240, 130, 20),
        (20, 200, 200),
        (220, 60, 60),
    ],
    # Neon
    [
        (255, 0, 100),
        (0, 255, 180),
        (255, 255, 0),
        (0, 150, 255),
        (255, 0, 255),
        (0, 255, 60),
        (255, 100, 0),
        (100, 0, 255),
    ],
    # Warm
    [
        (220, 50, 30),
        (240, 130, 20),
        (250, 200, 30),
        (200, 40, 80),
        (230, 80, 50),
        (240, 170, 50),
        (180, 30, 60),
        (250, 160, 80),
    ],
]

START_BALLOONS = 8
MAX_BALLOONS = 50
MIN_BALLOONS = 1
ANCHOR_X = GRID_SIZE // 2
ANCHOR_Y = GRID_SIZE - 8  # bundle tie-point near bottom


class Balloons(Visual):
    name = "BALLOONS"
    description = "Colorful balloons floating as a bundle"
    category = "household"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.palette_idx = 0
        self._prev_up = False
        self._prev_down = False
        self._init_balloons()

    def _init_balloons(self):
        self.balloons = []
        for i in range(START_BALLOONS):
            self._add_balloon()

    def _add_balloon(self):
        pal = PALETTES[self.palette_idx]
        n = len(self.balloons)
        angle = random.uniform(0, math.pi * 2)
        dist = random.uniform(6, 14)
        bx = ANCHOR_X + math.cos(angle) * dist + random.uniform(-3, 3)
        by = ANCHOR_Y - 18 + math.sin(angle) * dist * 0.5 + random.uniform(-4, 4)
        self.balloons.append({
            'x': float(bx),
            'y': float(by),
            'vx': random.uniform(-3, 3),
            'vy': random.uniform(-6, -1),
            'radius': random.choice([3, 3, 4, 4, 4, 5]),
            'color': pal[n % len(pal)],
            'phase': random.uniform(0, math.pi * 2),
        })

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Button press = gust
        if input_state.action_l or input_state.action_r:
            for b in self.balloons:
                b['vx'] += random.uniform(-12, 12)
                b['vy'] += random.uniform(-14, -4)
            consumed = True

        # Up/Down cycle palette (debounced — only on fresh press)
        up_now = input_state.up
        down_now = input_state.down
        if up_now and not self._prev_up:
            self.palette_idx = (self.palette_idx + 1) % len(PALETTES)
            self._apply_palette()
            consumed = True
        if down_now and not self._prev_down:
            self.palette_idx = (self.palette_idx - 1) % len(PALETTES)
            self._apply_palette()
            consumed = True
        self._prev_up = up_now
        self._prev_down = down_now

        # Right = add balloon, Left = remove balloon
        if input_state.right and len(self.balloons) < MAX_BALLOONS:
            self._add_balloon()
            consumed = True
        if input_state.left and len(self.balloons) > MIN_BALLOONS:
            self.balloons.pop(random.randrange(len(self.balloons)))
            consumed = True

        return consumed

    def _apply_palette(self):
        pal = PALETTES[self.palette_idx]
        for i, b in enumerate(self.balloons):
            b['color'] = pal[i % len(pal)]

    def update(self, dt: float):
        self.time += dt

        for b in self.balloons:
            # Buoyancy – gentle upward pull
            b['vy'] -= 8.0 * dt

            # Wind sway – sinusoidal horizontal force
            b['vx'] += math.sin(self.time * 1.2 + b['phase']) * 6.0 * dt

            # String pull toward anchor – keeps the bundle together
            dx = ANCHOR_X - b['x']
            dy = ANCHOR_Y - 12 - b['y']  # target slightly above anchor
            dist = math.sqrt(dx * dx + dy * dy) + 0.01
            pull = 3.0  # spring strength
            b['vx'] += (dx / dist) * pull * dt
            b['vy'] += (dy / dist) * pull * dt

            # Damping
            b['vx'] *= 0.97
            b['vy'] *= 0.97

            # Integrate position
            b['x'] += b['vx'] * dt
            b['y'] += b['vy'] * dt

            # Wall bounce
            r = b['radius']
            if b['x'] - r < 0:
                b['x'] = float(r)
                b['vx'] = abs(b['vx']) * 0.6
            elif b['x'] + r >= GRID_SIZE:
                b['x'] = float(GRID_SIZE - 1 - r)
                b['vx'] = -abs(b['vx']) * 0.6
            if b['y'] - r < 0:
                b['y'] = float(r)
                b['vy'] = abs(b['vy']) * 0.6
            elif b['y'] + r >= GRID_SIZE:
                b['y'] = float(GRID_SIZE - 1 - r)
                b['vy'] = -abs(b['vy']) * 0.6

        # Balloon-to-balloon repulsion
        for i in range(len(self.balloons)):
            for j in range(i + 1, len(self.balloons)):
                a = self.balloons[i]
                bb = self.balloons[j]
                dx = a['x'] - bb['x']
                dy = a['y'] - bb['y']
                dist = math.sqrt(dx * dx + dy * dy) + 0.01
                min_dist = a['radius'] + bb['radius'] + 1
                if dist < min_dist:
                    overlap = min_dist - dist
                    nx = dx / dist
                    ny = dy / dist
                    force = overlap * 15.0  # spring pushback
                    a['vx'] += nx * force * dt
                    a['vy'] += ny * force * dt
                    bb['vx'] -= nx * force * dt
                    bb['vy'] -= ny * force * dt

    def draw(self):
        self.display.clear()

        # Sort by y for depth (lower y = further back, draw first)
        ordered = sorted(self.balloons, key=lambda b: b['y'])

        # Draw strings first (behind balloons)
        for b in ordered:
            bx, by = int(b['x']), int(b['y'])
            self.display.draw_line(bx, by + b['radius'], ANCHOR_X, ANCHOR_Y,
                                   (100, 100, 100))

        # Draw balloons
        for b in ordered:
            bx, by = int(b['x']), int(b['y'])
            r = b['radius']
            c = b['color']

            # Balloon body
            self.display.draw_circle(bx, by, r, c, filled=True)

            # Shine highlight – 1px at upper-left
            hx = bx - max(1, r // 2)
            hy = by - max(1, r // 2)
            if 0 <= hx < GRID_SIZE and 0 <= hy < GRID_SIZE:
                hr = min(255, c[0] + 80)
                hg = min(255, c[1] + 80)
                hb = min(255, c[2] + 80)
                self.display.set_pixel(hx, hy, (hr, hg, hb))

        # Small bow/knot at anchor
        self.display.set_pixel(ANCHOR_X, ANCHOR_Y, (180, 140, 60))
        self.display.set_pixel(ANCHOR_X - 1, ANCHOR_Y + 1, (160, 120, 50))
        self.display.set_pixel(ANCHOR_X + 1, ANCHOR_Y + 1, (160, 120, 50))
