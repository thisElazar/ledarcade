"""
STATES OF MATTER - Particle Simulation with Emergent Phases
============================================================
~60 particles with soft pairwise attraction + repulsion.  Phases emerge:
  Solid — lattice holds its shape mid-screen (bonds resist gravity)
  Liquid — bonds break, particles fall and pool at the bottom
  Gas   — thermal energy overwhelms everything, particles fill the chamber
"""

import math
import random
from . import Visual, Display, Colors

NUM_PARTICLES = 60
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

# Pair potential parameters — soft repulsion + parabolic attractive well.
# Much gentler than Lennard-Jones, stable at game-loop timestep (1/60s).
R_EQ   = 4.0   # Equilibrium distance (pixels) — pair spacing
R_CUT  = 9.0   # Attraction cutoff distance
K_REP  = 2.5   # Repulsive spring constant (r < R_EQ)
WELL   = 1.5   # Attractive well depth (R_EQ < r < R_CUT)
R_RANGE = R_CUT - R_EQ

# Gravity — peaks in liquid phase, fades in gas phase.
# In a 64px container, gas thermal energy >> gravitational PE,
# so effectively zero gravity for gas is the right visual.
GRAVITY = 0.80


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
    category = "science_micro"

    def reset(self):
        self.time = 0.0
        self.temp = 0.15  # start solid
        self.palette_idx = 0
        self.show_labels = True
        self.overlay_timer = 0.0

        # Build hexagonal lattice — roughly square block, centered
        self.particles = []  # [x, y, vx, vy]
        spacing = R_EQ
        row_h = spacing * 0.866
        cols = round(math.sqrt(NUM_PARTICLES * 0.866))
        rows = (NUM_PARTICLES + cols - 1) // cols
        lattice_w = (cols - 1) * spacing + spacing * 0.5
        lattice_h = (rows - 1) * row_h
        gx0 = (WORK_W - lattice_w) / 2.0
        gy0 = (WORK_H - lattice_h) / 2.0  # vertically centered
        for i in range(NUM_PARTICLES):
            r = i // cols
            c = i % cols
            x = gx0 + c * spacing + (spacing * 0.5 if r % 2 else 0.0)
            y = gy0 + r * row_h
            self.particles.append([x, y, 0.0, 0.0])

    def handle_input(self, input_state):
        consumed = False
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
        # Thermal noise — cubic so solid is calm, gas is wild
        thermal_noise = t * t * t * 200.0
        # Heavy damping at low T (lattice settles), lighter at high T
        damping = 0.88 + 0.10 * t
        # Gravity: 0 in solid, peaks in liquid, fades in gas
        grav_rise = max(0.0, min(1.0, (t - 0.25) / 0.25))
        grav_fade = max(0.0, min(1.0, (t - 0.60) / 0.30))
        gravity = GRAVITY * grav_rise * (1.0 - grav_fade)
        # Velocity cap scales with temperature
        max_v = 1.5 + 10.0 * t
        max_v2 = max_v * max_v

        particles = self.particles
        n = len(particles)
        dt60 = dt * 60
        cut2 = R_CUT * R_CUT
        _sqrt = math.sqrt

        # --- Pair forces: soft repulsion + attractive well ---
        for i in range(n):
            p = particles[i]
            pxi, pyi = p[0], p[1]
            for j in range(i + 1, n):
                q = particles[j]
                dx = pxi - q[0]
                dy = pyi - q[1]
                r2 = dx * dx + dy * dy
                if r2 < 0.25:
                    r2 = 0.25
                if r2 < cut2:
                    r = _sqrt(r2)
                    if r < R_EQ:
                        # Linear repulsion (pushes apart when too close)
                        f = K_REP * (R_EQ - r) / r
                    else:
                        # Parabolic attractive well (pulls together)
                        wp = (r - R_EQ) / R_RANGE
                        f = -WELL * 4.0 * wp * (1.0 - wp) / r
                    fx = f * dx * dt60
                    fy = f * dy * dt60
                    p[2] += fx;  p[3] += fy
                    q[2] -= fx;  q[3] -= fy

        # --- Gravity, noise, damping, integration ---
        for p in particles:
            p[3] += gravity * dt60
            p[2] += random.uniform(-1, 1) * thermal_noise * dt
            p[3] += random.uniform(-1, 1) * thermal_noise * dt
            p[2] *= damping
            p[3] *= damping

            spd2 = p[2] * p[2] + p[3] * p[3]
            if spd2 > max_v2:
                scale = max_v / _sqrt(spd2)
                p[2] *= scale
                p[3] *= scale

            p[0] += p[2] * dt60
            p[1] += p[3] * dt60

            if p[0] < 1:
                p[0] = 1; p[2] = abs(p[2]) * 0.5
            if p[0] > WORK_W - 2:
                p[0] = WORK_W - 2; p[2] = -abs(p[2]) * 0.5
            if p[1] < 1:
                p[1] = 1; p[3] = abs(p[3]) * 0.5
            if p[1] > WORK_H - 2:
                p[1] = WORK_H - 2; p[3] = -abs(p[3]) * 0.5

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
