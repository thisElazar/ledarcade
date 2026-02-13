"""
WATER CYCLE - Animated Hydrological Cycle
==========================================
~70 particles cycle through ocean, evaporation, cloud, rain/snow,
and runoff states in a scenic landscape.
"""

import math
import random
from . import Visual, Display, Colors

# ---------------------------------------------------------------------------
# Particle states
# ---------------------------------------------------------------------------
OCEAN = 0
EVAPORATE = 1
CLOUD = 2
RAIN = 3
SNOW = 4
RUNOFF = 5

STATE_NAMES = ['OCEAN', 'EVAPORATE', 'CLOUD', 'RAIN', 'SNOW', 'RUNOFF']

NUM_PARTICLES = 70

# Scene geometry
SUN_X, SUN_Y = 8, 8
CLOUD_Y_MIN, CLOUD_Y_MAX = 14, 22
MOUNTAIN_PEAK_X, MOUNTAIN_PEAK_Y = 52, 16
MOUNTAIN_BASE_Y = 50
GROUND_Y = 50
OCEAN_Y = 55
OCEAN_LEFT = 0
OCEAN_RIGHT = 35

# River waypoints (from mountain base to ocean)
RIVER_PATH = [(52, 50), (46, 52), (40, 54), (35, 55)]

# Labels with positions
LABELS = [
    ('EVAPORATION',   4, 42),
    ('CONDENSATION', 14, 10),
    ('PRECIPITATION', 28, 30),
    ('COLLECTION',   10, 52),
]


class WaterCycle(Visual):
    name = "WATER CYCLE"
    description = "Animated hydrological cycle"
    category = "science"

    def reset(self):
        self.time = 0.0
        self.speed = 1.0
        self.show_labels = True
        self.overlay_timer = 0.0
        self.label_phase = 0
        self.label_timer = 0.0
        # Initialize particles in ocean
        self.particles = []
        for _ in range(NUM_PARTICLES):
            p = self._make_ocean_particle()
            self.particles.append(p)

    def _make_ocean_particle(self):
        return {
            'x': random.uniform(OCEAN_LEFT + 2, OCEAN_RIGHT),
            'y': random.uniform(OCEAN_Y, 63),
            'vx': 0, 'vy': 0,
            'state': OCEAN,
            'timer': random.uniform(0, 3),
            'color': (40, 80 + random.randint(0, 40), 200),
        }

    def handle_input(self, input_state):
        consumed = False
        if input_state.up_pressed:
            self.speed = min(2.0, self.speed + 0.25)
            self.overlay_timer = 2.0
            consumed = True
        if input_state.down_pressed:
            self.speed = max(0.5, self.speed - 0.25)
            self.overlay_timer = 2.0
            consumed = True
        if input_state.action_l or input_state.action_r:
            self.show_labels = not self.show_labels
            consumed = True
        return consumed

    def update(self, dt):
        self.time += dt
        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

        self.label_timer += dt * self.speed
        self.label_phase = int(self.label_timer / 3.0) % len(LABELS)

        sdt = dt * self.speed
        for p in self.particles:
            self._update_particle(p, sdt)

    def _update_particle(self, p, dt):
        s = p['state']
        p['timer'] -= dt

        if s == OCEAN:
            # Bob in ocean
            p['x'] += math.sin(self.time * 2 + p['y']) * 0.1
            p['y'] = max(OCEAN_Y, min(63, p['y'] + math.sin(self.time * 3 + p['x']) * 0.05))
            if p['timer'] <= 0 and random.random() < 0.02:
                p['state'] = EVAPORATE
                p['vy'] = -0.3 - random.uniform(0, 0.3)
                p['vx'] = random.uniform(-0.1, 0.1)
                p['timer'] = random.uniform(3, 6)

        elif s == EVAPORATE:
            p['y'] += p['vy'] * dt * 60
            p['x'] += p['vx'] * dt * 60
            # Lighten color as it rises
            frac = max(0, min(1, (OCEAN_Y - p['y']) / (OCEAN_Y - CLOUD_Y_MAX)))
            p['color'] = (int(40 + 160 * frac), int(120 + 135 * frac), int(200 + 55 * frac))
            if p['y'] <= CLOUD_Y_MAX:
                p['state'] = CLOUD
                p['y'] = random.uniform(CLOUD_Y_MIN, CLOUD_Y_MAX)
                p['vx'] = 0.2 + random.uniform(0, 0.3)
                p['timer'] = random.uniform(4, 8)
                p['color'] = (200, 200, 210)

        elif s == CLOUD:
            p['x'] += p['vx'] * dt * 60
            p['y'] += math.sin(self.time + p['x'] * 0.1) * 0.02
            if p['x'] > 62:
                p['x'] = 2
            if p['timer'] <= 0:
                # Near mountain -> snow, otherwise rain
                if p['x'] > 42:
                    p['state'] = SNOW
                    p['vy'] = 0.2
                    p['color'] = (220, 220, 240)
                else:
                    p['state'] = RAIN
                    p['vy'] = 1.5 + random.uniform(0, 0.5)
                    p['color'] = (60, 100, 220)
                p['vx'] = random.uniform(-0.05, 0.05)
                p['timer'] = 0

        elif s == RAIN:
            p['y'] += p['vy'] * dt * 60
            p['x'] += p['vx'] * dt * 60
            # Check if hit ground/ocean
            ground = self._ground_height(p['x'])
            if p['y'] >= ground:
                p['y'] = ground
                if p['x'] < OCEAN_RIGHT + 5:
                    # Hit ocean directly
                    self._reset_ocean(p)
                else:
                    p['state'] = RUNOFF
                    p['vx'] = -0.3
                    p['vy'] = 0.1
                    p['timer'] = random.uniform(2, 5)
                    p['color'] = (60, 130, 200)

        elif s == SNOW:
            p['y'] += p['vy'] * dt * 60
            p['x'] += math.sin(self.time * 2 + p['y']) * 0.15 * dt * 60
            ground = self._ground_height(p['x'])
            if p['y'] >= ground:
                p['y'] = ground
                p['state'] = RUNOFF
                p['vx'] = -0.4
                p['vy'] = 0.1
                p['timer'] = random.uniform(2, 5)
                p['color'] = (60, 150, 200)

        elif s == RUNOFF:
            # Flow along ground toward ocean
            p['x'] += p['vx'] * dt * 60
            target_y = self._ground_height(p['x'])
            p['y'] += (target_y - p['y']) * 0.1
            if p['x'] <= OCEAN_RIGHT or p['timer'] <= 0:
                self._reset_ocean(p)

    def _ground_height(self, x):
        """Get ground level at x coordinate."""
        # Mountain slope (right side)
        if x > 42:
            slope = min(1.0, (x - 42) / (MOUNTAIN_PEAK_X - 42))
            return MOUNTAIN_BASE_Y - (MOUNTAIN_BASE_Y - MOUNTAIN_PEAK_Y) * math.sqrt(1 - slope)
        # Gentle hills
        return GROUND_Y + math.sin(x * 0.15) * 2

    def _reset_ocean(self, p):
        p['x'] = random.uniform(OCEAN_LEFT + 2, OCEAN_RIGHT)
        p['y'] = random.uniform(OCEAN_Y, 63)
        p['state'] = OCEAN
        p['vx'] = 0
        p['vy'] = 0
        p['timer'] = random.uniform(1, 4)
        p['color'] = (40, 80 + random.randint(0, 40), 200)

    def draw(self):
        d = self.display
        d.clear()

        # --- Sky gradient ---
        for y in range(GROUND_Y):
            t = y / GROUND_Y
            r = int(10 + 30 * t)
            g = int(15 + 50 * t)
            b = int(40 + 80 * t)
            for x in range(64):
                d.set_pixel(x, y, (r, g, b))

        # --- Sun ---
        d.draw_circle(SUN_X, SUN_Y, 4, (255, 220, 60), filled=True)
        # Rays
        ray_c = (255, 200, 40)
        for i in range(8):
            a = self.time * 0.3 + i * math.pi / 4
            rx = SUN_X + int(7 * math.cos(a))
            ry = SUN_Y + int(7 * math.sin(a))
            d.set_pixel(rx, ry, ray_c)

        # --- Mountain ---
        for x in range(42, 63):
            top = int(self._ground_height(x))
            for y in range(top, GROUND_Y + 3):
                if y - top < 4:
                    # Snow cap
                    d.set_pixel(x, y, (200, 210, 220))
                else:
                    d.set_pixel(x, y, (80, 70, 60))

        # --- Ground / hills ---
        for x in range(42):
            top = int(self._ground_height(x))
            for y in range(top, OCEAN_Y):
                d.set_pixel(x, y, (40, 120 + (y % 3) * 10, 30))

        # --- Ocean ---
        for y in range(OCEAN_Y, 64):
            for x in range(OCEAN_RIGHT + 8):
                wave = math.sin(self.time * 2 + x * 0.3) * 1.5
                if y >= OCEAN_Y + wave:
                    depth = (y - OCEAN_Y) / 9
                    b = int(140 - depth * 50)
                    d.set_pixel(x, y, (20, 40 + int(depth * 20), max(80, b)))

        # --- River ---
        for i in range(len(RIVER_PATH) - 1):
            x1, y1 = RIVER_PATH[i]
            x2, y2 = RIVER_PATH[i + 1]
            d.draw_line(x1, y1, x2, y2, (40, 90, 180))

        # --- Particles ---
        for p in self.particles:
            px, py = int(p['x']), int(p['y'])
            if 0 <= px < 64 and 0 <= py < 64:
                c = p['color']
                d.set_pixel(px, py, c)
                # Rain streaks
                if p['state'] == RAIN and py > 1:
                    d.set_pixel(px, py - 1, (c[0] // 2, c[1] // 2, c[2] // 2))

        # --- Labels ---
        if self.show_labels:
            lbl_text, lbl_x, lbl_y = LABELS[self.label_phase]
            fade = min(1.0, (self.label_timer % 3.0) / 0.5)
            if (self.label_timer % 3.0) > 2.5:
                fade = max(0.0, (3.0 - self.label_timer % 3.0) / 0.5)
            c = (int(220 * fade), int(220 * fade), int(220 * fade))
            # Scroll long labels
            max_chars = 14
            if len(lbl_text) > max_chars:
                scroll = int(self.time * 15) % (len(lbl_text + "   ") * 4)
                padded = lbl_text + "   " + lbl_text
                d.draw_text_small(lbl_x - scroll, lbl_y, padded, c)
            else:
                d.draw_text_small(lbl_x, lbl_y, lbl_text, c)

        # --- Speed overlay ---
        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            c = (int(200 * alpha), int(200 * alpha), int(200 * alpha))
            d.draw_text_small(2, 2, f"SPEED {self.speed:.1f}X", c)
