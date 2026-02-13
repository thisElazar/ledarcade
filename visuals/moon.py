"""
MOON PHASES - Lunar Phase Visualization
========================================
Displays the 8 phases of the Moon with realistic shadow rendering,
twinkling background stars, and crater texture.
"""

import math
import random
from . import Visual, Display, Colors

# ---------------------------------------------------------------------------
# Phase data
# ---------------------------------------------------------------------------
PHASES = [
    ('NEW MOON',         0.0),
    ('WAXING CRESCENT',  math.pi * 0.25),
    ('FIRST QUARTER',    math.pi * 0.5),
    ('WAXING GIBBOUS',   math.pi * 0.75),
    ('FULL MOON',        math.pi),
    ('WANING GIBBOUS',   math.pi * 1.25),
    ('LAST QUARTER',     math.pi * 1.5),
    ('WANING CRESCENT',  math.pi * 1.75),
]

# Day in the 29.5-day synodic cycle for each phase
PHASE_DAYS = [0, 3.7, 7.4, 11.1, 14.8, 18.5, 22.1, 25.8]

# ---------------------------------------------------------------------------
# Palettes: (lit_base, dark_surface, name)
# ---------------------------------------------------------------------------
PALETTES = [
    ('SILVER',     (200, 200, 210), (15, 15, 25)),
    ('GOLD',       (220, 200, 130), (20, 18, 10)),
    ('BLOOD MOON', (200, 60, 40),   (30, 8, 5)),
    ('BLUE MOON',  (140, 170, 220), (10, 12, 30)),
]

# Crater positions relative to center (dx, dy, dim_amount)
CRATERS = [
    (-6, -8, 0.70), (4, -5, 0.75), (-3, 2, 0.65),
    (8, 4, 0.72),  (-9, 7, 0.68), (2, 10, 0.74),
    (6, -12, 0.71), (-4, -14, 0.73),
]

# Moon parameters
MOON_R = 22
CX, CY = 32, 28


class MoonPhases(Visual):
    name = "MOON PHASES"
    description = "Lunar phase cycle with realistic shadows"
    category = "science"

    def reset(self):
        self.time = 0.0
        self.phase_idx = 0
        self.palette_idx = 0
        self.auto_cycle = True
        self.cycle_timer = 0.0
        self.cycle_duration = 4.0
        self.overlay_timer = 0.0
        self.label_timer = 0.0
        self.scroll_offset = 0.0
        # Smooth transition
        self.phase_angle = PHASES[0][1]
        self.target_angle = PHASES[0][1]
        # Background stars
        self.stars = [(random.randint(0, 63), random.randint(0, 63),
                       random.uniform(0, math.pi * 2), random.uniform(0.3, 1.0))
                      for _ in range(40)]

    def handle_input(self, input_state):
        consumed = False
        if input_state.left_pressed:
            self.phase_idx = (self.phase_idx - 1) % len(PHASES)
            self.target_angle = PHASES[self.phase_idx][1]
            self.cycle_timer = 0.0
            self.label_timer = 0.0
            self.scroll_offset = 0.0
            consumed = True
        if input_state.right_pressed:
            self.phase_idx = (self.phase_idx + 1) % len(PHASES)
            self.target_angle = PHASES[self.phase_idx][1]
            self.cycle_timer = 0.0
            self.label_timer = 0.0
            self.scroll_offset = 0.0
            consumed = True
        if input_state.up_pressed:
            self.palette_idx = (self.palette_idx - 1) % len(PALETTES)
            self.overlay_timer = 2.0
            consumed = True
        if input_state.down_pressed:
            self.palette_idx = (self.palette_idx + 1) % len(PALETTES)
            self.overlay_timer = 2.0
            consumed = True
        if input_state.action_l or input_state.action_r:
            self.auto_cycle = not self.auto_cycle
            consumed = True
        return consumed

    def update(self, dt):
        self.time += dt
        self.label_timer += dt
        self.scroll_offset += dt * 20

        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

        # Auto-cycle
        if self.auto_cycle:
            self.cycle_timer += dt
            if self.cycle_timer >= self.cycle_duration:
                self.cycle_timer = 0.0
                self.phase_idx = (self.phase_idx + 1) % len(PHASES)
                self.target_angle = PHASES[self.phase_idx][1]
                self.label_timer = 0.0
                self.scroll_offset = 0.0

        # Smooth angle transition
        diff = self.target_angle - self.phase_angle
        # Handle wrap-around
        if diff > math.pi:
            diff -= 2 * math.pi
        elif diff < -math.pi:
            diff += 2 * math.pi
        self.phase_angle += diff * min(1.0, dt * 4.0)

    def draw(self):
        d = self.display
        d.clear((3, 3, 12))

        # --- Background stars ---
        for sx, sy, phase, brightness in self.stars:
            # Skip stars behind the moon
            dx = sx - CX
            dy = sy - CY
            if dx * dx + dy * dy < (MOON_R + 2) ** 2:
                continue
            twinkle = 0.5 + 0.5 * math.sin(self.time * 1.5 + phase)
            v = int(40 + 160 * brightness * twinkle)
            d.set_pixel(sx, sy, (v, v, v))

        # --- Moon rendering ---
        pal_name, lit_base, dark_base = PALETTES[self.palette_idx]
        angle = self.phase_angle

        # Build crater lookup
        crater_set = {}
        for cdx, cdy, dim in CRATERS:
            crater_set[(cdx, cdy)] = dim

        r2 = MOON_R * MOON_R
        cos_a = math.cos(angle)

        for dy in range(-MOON_R, MOON_R + 1):
            half_w_sq = r2 - dy * dy
            if half_w_sq < 0:
                continue
            half_w = math.sqrt(half_w_sq)
            term_x = cos_a * half_w

            for dx in range(int(-half_w), int(half_w) + 1):
                # Determine lit or dark
                if angle <= math.pi:
                    # Waxing: lit if dx >= term_x (right side lit)
                    lit = dx >= term_x
                else:
                    # Waning: lit if dx <= -term_x (left side lit)
                    lit = dx <= -cos_a * half_w

                if lit:
                    base = lit_base
                    # Surface shading: slight falloff at edges
                    dist_frac = math.sqrt(dx * dx + dy * dy) / MOON_R
                    shade = 1.0 - 0.2 * dist_frac
                    # Crater dimming
                    crater_dim = crater_set.get((dx, dy), 1.0)
                    shade *= crater_dim
                    c = (min(255, int(base[0] * shade)),
                         min(255, int(base[1] * shade)),
                         min(255, int(base[2] * shade)))
                else:
                    c = dark_base

                d.set_pixel(CX + dx, CY + dy, c)

        # --- Label ---
        phase_name = PHASES[self.phase_idx][0]
        day = PHASE_DAYS[self.phase_idx]
        phase_cycle = int(self.label_timer / 4) % 2
        if phase_cycle == 0:
            label = phase_name
        else:
            label = f"DAY {day:.0f} OF 29"

        # Reset scroll when phase changes
        if not hasattr(self, '_last_label_phase') or self._last_label_phase != phase_cycle:
            self._last_label_phase = phase_cycle
            self.scroll_offset = 0

        max_chars = 14
        if len(label) > max_chars:
            padded = label + "    " + label
            total_w = len(label + "    ") * 4
            offset = int(self.scroll_offset) % total_w
            d.draw_text_small(2 - offset, 58, padded, Colors.WHITE)
        else:
            d.draw_text_small(2, 58, label, Colors.WHITE)

        # --- Palette overlay ---
        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            c = (int(200 * alpha), int(200 * alpha), int(200 * alpha))
            d.draw_text_small(2, 2, pal_name, c)
