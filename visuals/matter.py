"""
STATES OF MATTER - Temperature-Driven Particle Simulation
==========================================================
~50 particles transition between solid, liquid, and gas states
based on temperature. Demonstrates molecular behavior at each phase.
"""

import math
import random
from . import Visual, Display, Colors

NUM_PARTICLES = 50
WORK_W = 60  # leave 4px for temp bar on right
WORK_H = 64

# Temperature color ramp (blue -> cyan -> green -> yellow -> orange -> red)
TEMP_RAMP = [
    (0.0,  (40, 80, 200)),
    (0.2,  (40, 180, 220)),
    (0.4,  (40, 200, 100)),
    (0.6,  (200, 200, 40)),
    (0.8,  (220, 140, 40)),
    (1.0,  (220, 50, 30)),
]

PALETTES = [
    ('CLASSIC', None),  # use temp ramp
    ('ICE',     (100, 180, 255)),
    ('FIRE',    (255, 120, 40)),
    ('NEON',    (0, 255, 180)),
]


def _temp_color(t):
    """Interpolate temperature ramp color."""
    t = max(0.0, min(1.0, t))
    for i in range(len(TEMP_RAMP) - 1):
        t0, c0 = TEMP_RAMP[i]
        t1, c1 = TEMP_RAMP[i + 1]
        if t <= t1:
            f = (t - t0) / (t1 - t0) if t1 > t0 else 0
            return (int(c0[0] + (c1[0] - c0[0]) * f),
                    int(c0[1] + (c1[1] - c0[1]) * f),
                    int(c0[2] + (c1[2] - c0[2]) * f))
    return TEMP_RAMP[-1][1]


class MatterPhases(Visual):
    name = "MATTER"
    description = "States of matter: solid, liquid, gas"
    category = "science"

    def reset(self):
        self.time = 0.0
        self.temp = 0.15  # start solid
        self.palette_idx = 0
        self.show_labels = True
        self.overlay_timer = 0.0
        # Particles: [x, y, vx, vy]
        self.particles = []
        # Grid positions for solid state
        cols = 7
        rows = NUM_PARTICLES // cols + 1
        gx0 = (WORK_W - cols * 8) // 2
        gy0 = (WORK_H - rows * 8) // 2
        for i in range(NUM_PARTICLES):
            r = i // cols
            c = i % cols
            x = gx0 + c * 8 + 4.0
            y = gy0 + r * 8 + 4.0
            self.particles.append([x, y, 0.0, 0.0])
        self.grid_positions = [(p[0], p[1]) for p in self.particles]

    def handle_input(self, input_state):
        consumed = False
        # Temperature adjustment (held)
        if input_state.left:
            self.temp = max(0.0, self.temp - 0.008)
            consumed = True
        if input_state.right:
            self.temp = min(1.0, self.temp + 0.008)
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
            self.show_labels = not self.show_labels
            consumed = True
        return consumed

    def update(self, dt):
        self.time += dt
        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

        t = self.temp
        # Blend factors for transition zones
        solid_f = max(0.0, min(1.0, (0.33 - t) / 0.05)) if t < 0.38 else 0.0
        gas_f = max(0.0, min(1.0, (t - 0.66) / 0.05)) if t > 0.61 else 0.0
        liquid_f = 1.0 - solid_f - gas_f

        gravity = 0.3 * (1.0 - gas_f)
        brownian = 20.0 * liquid_f + 80.0 * gas_f
        damping = 0.95 - 0.1 * gas_f

        for i, p in enumerate(self.particles):
            x, y, vx, vy = p

            # Solid: spring force toward grid position
            if solid_f > 0:
                gx, gy = self.grid_positions[i]
                vx += (gx - x) * 2.0 * solid_f * dt * 60
                vy += (gy - y) * 2.0 * solid_f * dt * 60
                # Small jitter
                vx += random.uniform(-0.5, 0.5) * solid_f
                vy += random.uniform(-0.5, 0.5) * solid_f

            # Liquid/gas: gravity + brownian
            if liquid_f > 0 or gas_f > 0:
                vy += gravity * dt * 60
                vx += random.uniform(-1, 1) * brownian * dt
                vy += random.uniform(-1, 1) * brownian * dt

            # Soft repulsion between particles
            for j in range(i + 1, len(self.particles)):
                ox, oy = self.particles[j][0], self.particles[j][1]
                ddx = x - ox
                ddy = y - oy
                dist2 = ddx * ddx + ddy * ddy + 0.01
                if dist2 < 64:  # repel within 8px
                    force = (1.0 - dist2 / 64) * 2.0
                    inv_d = 1.0 / math.sqrt(dist2)
                    fx = ddx * inv_d * force * dt * 60
                    fy = ddy * inv_d * force * dt * 60
                    vx += fx
                    vy += fy
                    self.particles[j][2] -= fx
                    self.particles[j][3] -= fy

            # Damping
            vx *= damping
            vy *= damping

            # Velocity cap
            max_v = 3.0 + 5.0 * gas_f
            speed = math.sqrt(vx * vx + vy * vy)
            if speed > max_v:
                vx = vx / speed * max_v
                vy = vy / speed * max_v

            # Move
            x += vx * dt * 60
            y += vy * dt * 60

            # Wall bounce
            if x < 1:
                x = 1; vx = abs(vx) * 0.5
            if x > WORK_W - 2:
                x = WORK_W - 2; vx = -abs(vx) * 0.5
            if y < 1:
                y = 1; vy = abs(vy) * 0.5
            if y > WORK_H - 2:
                y = WORK_H - 2; vy = -abs(vy) * 0.5

            p[0], p[1], p[2], p[3] = x, y, vx, vy

    def draw(self):
        d = self.display
        d.clear()

        # --- Particles ---
        pal_name, pal_color = PALETTES[self.palette_idx]
        for p in self.particles:
            px, py = int(p[0]), int(p[1])
            if pal_color:
                c = pal_color
            else:
                c = _temp_color(self.temp)
            d.set_pixel(px, py, c)

        # --- Temperature bar (right edge, 2px wide) ---
        for y in range(64):
            t_at = 1.0 - y / 63.0
            c = _temp_color(t_at)
            dim = (c[0] // 3, c[1] // 3, c[2] // 3)
            d.set_pixel(62, y, dim)
            d.set_pixel(63, y, dim)
        # White marker at current temp
        marker_y = int((1.0 - self.temp) * 63)
        d.set_pixel(62, marker_y, Colors.WHITE)
        d.set_pixel(63, marker_y, Colors.WHITE)

        # --- Labels ---
        if self.show_labels:
            if self.temp < 0.33:
                state = "SOLID"
            elif self.temp < 0.66:
                state = "LIQUID"
            else:
                state = "GAS"
            d.draw_text_small(2, 58, state, Colors.WHITE)

        # --- Palette overlay ---
        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            c = (int(200 * alpha), int(200 * alpha), int(200 * alpha))
            d.draw_text_small(2, 2, pal_name, c)
