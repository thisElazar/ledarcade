"""
Orbits - N-Body Gravity Simulation
====================================
Bodies orbit, slingshot, and merge under Newtonian gravity.
Velocity Verlet integration with softened potential prevents
singularities. Trails fade behind each body.

Three standalone visuals:
  Solar System   - Sun + planets in near-circular orbits
  N-Body         - Equal-mass bodies in gravitational dance
  Asteroid Belt  - Star + planet + 40-50 asteroids in a ring

Controls:
  Up/Down    - Cycle color palette
  Left/Right - Adjust simulation speed
  Space      - Reshuffle / cycle body count
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE

# Softening length squared (prevents 1/r^2 singularity)
SOFTENING2 = 4.0

# Gravitational constant (tuned for display)
G_CONST = 800.0

# Merge distance squared
MERGE_DIST2 = 9.0

PALETTES = [
    # Solar: yellow sun, rocky to icy
    [(255, 220, 50), (200, 100, 50), (150, 150, 180), (80, 160, 255), (100, 200, 100), (220, 180, 120)],
    # Neon
    [(255, 50, 100), (50, 255, 150), (100, 100, 255), (255, 255, 50), (255, 100, 255), (50, 255, 255)],
    # Fire
    [(255, 80, 0), (255, 160, 0), (255, 255, 50), (200, 50, 0), (255, 200, 100), (255, 120, 50)],
    # Ice
    [(150, 200, 255), (80, 150, 255), (200, 230, 255), (50, 100, 200), (180, 220, 255), (100, 180, 240)],
    # Candy
    [(255, 100, 150), (150, 100, 255), (100, 255, 200), (255, 200, 100), (200, 150, 255), (255, 150, 200)],
]


# ── Shared physics ────────────────────────────────────────────────

class Body:
    __slots__ = ('x', 'y', 'vx', 'vy', 'ax', 'ay', 'mass', 'radius', 'trail', 'color_idx')

    def __init__(self, x, y, vx, vy, mass, color_idx=0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.ax = 0.0
        self.ay = 0.0
        self.mass = mass
        self.radius = max(1, int(math.sqrt(mass) * 0.8))
        self.trail = []
        self.color_idx = color_idx


def _compute_accelerations(bodies, softening2=SOFTENING2):
    n = len(bodies)
    for b in bodies:
        b.ax = 0.0
        b.ay = 0.0
    for i in range(n):
        bi = bodies[i]
        for j in range(i + 1, n):
            bj = bodies[j]
            dx = bj.x - bi.x
            dy = bj.y - bi.y
            dist2 = dx * dx + dy * dy + softening2
            inv_dist = 1.0 / math.sqrt(dist2)
            inv_dist3 = inv_dist * inv_dist * inv_dist
            f = G_CONST * inv_dist3
            fx = f * dx
            fy = f * dy
            bi.ax += fx * bj.mass
            bi.ay += fy * bj.mass
            bj.ax -= fx * bi.mass
            bj.ay -= fy * bi.mass


def _merge_bodies(bodies):
    """Merge bodies that are very close, conserving momentum."""
    to_remove = set()
    n = len(bodies)
    for i in range(n):
        if i in to_remove:
            continue
        bi = bodies[i]
        for j in range(i + 1, n):
            if j in to_remove:
                continue
            bj = bodies[j]
            dx = bj.x - bi.x
            dy = bj.y - bi.y
            dist2 = dx * dx + dy * dy
            min_r = (bi.radius + bj.radius) * 0.8
            if dist2 < max(MERGE_DIST2, min_r * min_r):
                total_mass = bi.mass + bj.mass
                bi.vx = (bi.vx * bi.mass + bj.vx * bj.mass) / total_mass
                bi.vy = (bi.vy * bi.mass + bj.vy * bj.mass) / total_mass
                bi.x = (bi.x * bi.mass + bj.x * bj.mass) / total_mass
                bi.y = (bi.y * bi.mass + bj.y * bj.mass) / total_mass
                bi.mass = total_mass
                bi.radius = max(1, int(math.sqrt(total_mass) * 0.8))
                to_remove.add(j)
    if to_remove:
        bodies[:] = [b for i, b in enumerate(bodies) if i not in to_remove]


def _verlet_step(bodies, h, steps, softening2=SOFTENING2):
    """Velocity Verlet integration for *steps* sub-steps."""
    for _ in range(steps):
        _compute_accelerations(bodies, softening2)
        for b in bodies:
            b.vx += 0.5 * h * b.ax
            b.vy += 0.5 * h * b.ay
            b.x += h * b.vx
            b.y += h * b.vy
        _compute_accelerations(bodies, softening2)
        for b in bodies:
            b.vx += 0.5 * h * b.ax
            b.vy += 0.5 * h * b.ay


def _record_trails(bodies, trail_length):
    for b in bodies:
        b.trail.append((b.x, b.y))
        if len(b.trail) > trail_length:
            b.trail.pop(0)


def _draw_bodies(display, bodies, palette_idx):
    palette = PALETTES[palette_idx]

    for b in bodies:
        color = palette[b.color_idx % len(palette)]

        # Draw trail
        trail_len = len(b.trail)
        for i, (tx, ty) in enumerate(b.trail):
            ix, iy = int(tx), int(ty)
            if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                t = (i + 1) / trail_len
                dim = (
                    int(color[0] * t * 0.4),
                    int(color[1] * t * 0.4),
                    int(color[2] * t * 0.4),
                )
                display.set_pixel(ix, iy, dim)

        # Draw body
        ix, iy = int(b.x), int(b.y)
        if b.radius <= 1:
            if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                display.set_pixel(ix, iy, color)
        else:
            display.draw_circle(ix, iy, b.radius, color, filled=True)
            if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                bright = (min(255, color[0] + 80), min(255, color[1] + 80), min(255, color[2] + 80))
                display.set_pixel(ix, iy, bright)


# ── OrbitsSolar ───────────────────────────────────────────────────

# Real solar system planet data:
#   (orbit_px, color, draw_radius, mass)
# Orbits compressed to fit 64x64: Mercury at 5px, Neptune at 28px
# Masses negligible so planets don't perturb each other
SOLAR_PLANETS = [
    # Mercury — small, gray
    (5,  (160, 160, 160),    1, 0.01),
    # Venus — pale yellow
    (7,  (230, 210, 160),    1, 0.01),
    # Earth — blue
    (9,  (50, 140, 255),     1, 0.01),
    # Mars — red-orange
    (11, (210, 80, 40),      1, 0.01),
    # Jupiter — tan/orange (biggest planet)
    (16, (200, 160, 100),    2, 0.01),
    # Saturn — gold
    (20, (220, 190, 120),    2, 0.01),
    # Uranus — light cyan
    (24, (160, 220, 230),    1, 0.01),
    # Neptune — deep blue
    (28, (60, 100, 220),     1, 0.01),
]

SUN_COLOR = (255, 220, 50)
SUN_MASS = 50.0  # Heavy so circular velocity formula works cleanly


class OrbitsSolar(Visual):
    name = "SOLAR SYSTEM"
    description = "Sun and planets"
    category = "science"
    TRAIL_LENGTH = 80

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed = 1.0
        self.dt_sim = 0.0005
        self.steps_per_frame = 8
        self._init_bodies()

    def _init_bodies(self):
        self.bodies = []
        self.cx, self.cy = GRID_SIZE / 2, GRID_SIZE / 2

        # Sun (index 0)
        sun = Body(self.cx, self.cy, 0, 0, SUN_MASS, 0)
        self.bodies.append(sun)

        # Planet colors and draw radii (parallel to self.bodies, index 0 = sun)
        self.body_colors = [SUN_COLOR]
        self.body_draw_radii = [3]

        # Place each planet at exact circular orbit
        for orbit_r, color, draw_r, mass in SOLAR_PLANETS:
            angle = random.uniform(0, 2 * math.pi)
            x = self.cx + orbit_r * math.cos(angle)
            y = self.cy + orbit_r * math.sin(angle)
            # Exact circular velocity: v = sqrt(G * M_sun / r)
            v = math.sqrt(G_CONST * SUN_MASS / orbit_r)
            vx = -v * math.sin(angle)
            vy = v * math.cos(angle)
            self.bodies.append(Body(x, y, vx, vy, mass, 0))
            self.body_colors.append(color)
            self.body_draw_radii.append(draw_r)

    def _pin_sun(self):
        """Keep the sun fixed at center."""
        sun = self.bodies[0]
        sun.x = self.cx
        sun.y = self.cy
        sun.vx = 0.0
        sun.vy = 0.0

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.left:
            self.speed = max(0.2, self.speed - 0.1)
            consumed = True
        if input_state.right:
            self.speed = min(3.0, self.speed + 0.1)
            consumed = True
        if input_state.action_l or input_state.action_r:
            self._init_bodies()
            consumed = True
        return consumed

    def update(self, dt: float):
        self.time += dt
        h = self.dt_sim * self.speed
        _verlet_step(self.bodies, h, self.steps_per_frame)
        self._pin_sun()
        _record_trails(self.bodies, self.TRAIL_LENGTH)

    def draw(self):
        self.display.clear(Colors.BLACK)

        for idx, b in enumerate(self.bodies):
            color = self.body_colors[idx]
            draw_r = self.body_draw_radii[idx]

            # Draw trail
            trail_len = len(b.trail)
            if trail_len > 0:
                for i, (tx, ty) in enumerate(b.trail):
                    ix, iy = int(tx), int(ty)
                    if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                        t = (i + 1) / trail_len
                        dim = (
                            int(color[0] * t * 0.35),
                            int(color[1] * t * 0.35),
                            int(color[2] * t * 0.35),
                        )
                        self.display.set_pixel(ix, iy, dim)

            # Draw body
            ix, iy = int(b.x), int(b.y)
            if draw_r <= 1:
                if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                    self.display.set_pixel(ix, iy, color)
            else:
                self.display.draw_circle(ix, iy, draw_r, color, filled=True)
                if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                    bright = (
                        min(255, color[0] + 60),
                        min(255, color[1] + 60),
                        min(255, color[2] + 60),
                    )
                    self.display.set_pixel(ix, iy, bright)


# ── OrbitsMulti ──────────────────────────────────────────────────

class OrbitsMulti(Visual):
    name = "3 BODY PROBLEM"
    description = "Gravitational dance"
    category = "science"
    TRAIL_LENGTH = 120
    SOFT2 = 25.0       # Higher softening → gentler close passes
    MIN_MASS = 3.0     # Below this, full merge
    DEBRIS_LIFE = 50   # Frames before debris fades

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed = 1.0
        self.palette_idx = 1  # Neon looks good for this
        self.dt_sim = 0.0005
        self.steps_per_frame = 8
        self.debris = []      # [(x, y, vx, vy, color, life)]
        self._init_bodies()

    def _init_bodies(self):
        self.bodies = []
        self.debris = []
        cx, cy = GRID_SIZE / 2, GRID_SIZE / 2

        for i in range(3):
            angle = 2 * math.pi * i / 3 + random.uniform(-0.2, 0.2)
            r = 20
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            v_mag = math.sqrt(G_CONST * 10.0 * 2 / (2 * r + 2)) * 0.65
            vx = -v_mag * math.sin(angle) + random.uniform(-0.5, 0.5)
            vy = v_mag * math.cos(angle) + random.uniform(-0.5, 0.5)
            self.bodies.append(Body(x, y, vx, vy, 10.0, i % 6))

    def _handle_collisions(self):
        """Partial mass transfer + debris sparks on close approach."""
        bodies = self.bodies
        n = len(bodies)
        to_remove = set()

        for i in range(n):
            if i in to_remove:
                continue
            bi = bodies[i]
            for j in range(i + 1, n):
                if j in to_remove:
                    continue
                bj = bodies[j]
                dx = bj.x - bi.x
                dy = bj.y - bi.y
                dist2 = dx * dx + dy * dy
                touch = (bi.radius + bj.radius) * 0.9
                if dist2 >= touch * touch:
                    continue

                # Pick smaller body
                if bi.mass <= bj.mass:
                    smaller, larger = bi, bj
                    sign = 1
                else:
                    smaller, larger = bj, bi
                    sign = -1

                if smaller.mass < self.MIN_MASS:
                    # Full merge
                    total = larger.mass + smaller.mass
                    larger.vx = (larger.vx * larger.mass + smaller.vx * smaller.mass) / total
                    larger.vy = (larger.vy * larger.mass + smaller.vy * smaller.mass) / total
                    larger.x = (larger.x * larger.mass + smaller.x * smaller.mass) / total
                    larger.y = (larger.y * larger.mass + smaller.y * smaller.mass) / total
                    larger.mass = total
                    larger.radius = max(1, int(math.sqrt(total) * 0.8))
                    to_remove.add(bodies.index(smaller))
                else:
                    # Partial transfer: 20% of smaller → debris sparks
                    transfer = smaller.mass * 0.2
                    smaller.mass -= transfer
                    smaller.radius = max(1, int(math.sqrt(smaller.mass) * 0.8))

                    # Spawn debris sparks
                    palette = PALETTES[self.palette_idx]
                    mid_x = (bi.x + bj.x) / 2
                    mid_y = (bi.y + bj.y) / 2
                    for _ in range(4):
                        a = random.uniform(0, 2 * math.pi)
                        spd = random.uniform(15, 35)
                        c = palette[random.randint(0, len(palette) - 1)]
                        self.debris.append([
                            mid_x, mid_y,
                            spd * math.cos(a), spd * math.sin(a),
                            c, self.DEBRIS_LIFE,
                        ])

                    # Deflection impulse — push apart
                    dist = math.sqrt(dist2) + 0.1
                    push = 10.0
                    nx, ny = dx / dist, dy / dist
                    bi.vx -= push * nx * sign
                    bi.vy -= push * ny * sign
                    bj.vx += push * nx * sign
                    bj.vy += push * ny * sign

        if to_remove:
            self.bodies = [b for i, b in enumerate(bodies) if i not in to_remove]

    def _apply_edge_force(self):
        """Push bodies toward screen center when they stray too far."""
        margin = 12.0
        strength = 80.0
        cx, cy = GRID_SIZE / 2, GRID_SIZE / 2
        for b in self.bodies:
            # How deep into the margin zone (0 = inside safe area, 1 = at edge)
            t = 0.0
            if b.x < margin:
                t = max(t, (margin - b.x) / margin)
            elif b.x > GRID_SIZE - margin:
                t = max(t, (b.x - (GRID_SIZE - margin)) / margin)
            if b.y < margin:
                t = max(t, (margin - b.y) / margin)
            elif b.y > GRID_SIZE - margin:
                t = max(t, (b.y - (GRID_SIZE - margin)) / margin)
            if t > 0:
                # Vector toward center
                dx = cx - b.x
                dy = cy - b.y
                dist = math.sqrt(dx * dx + dy * dy) + 0.1
                force = strength * t * t
                b.vx += (dx / dist) * force * self.dt_sim * self.speed
                b.vy += (dy / dist) * force * self.dt_sim * self.speed

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.up_pressed:
            self.palette_idx = (self.palette_idx + 1) % len(PALETTES)
            consumed = True
        if input_state.down_pressed:
            self.palette_idx = (self.palette_idx - 1) % len(PALETTES)
            consumed = True
        if input_state.left:
            self.speed = max(0.2, self.speed - 0.1)
            consumed = True
        if input_state.right:
            self.speed = min(3.0, self.speed + 0.1)
            consumed = True
        if input_state.action_l or input_state.action_r:
            self._init_bodies()
            consumed = True
        return consumed

    def update(self, dt: float):
        self.time += dt
        h = self.dt_sim * self.speed
        _verlet_step(self.bodies, h, self.steps_per_frame, self.SOFT2)
        self._apply_edge_force()
        self._handle_collisions()
        _record_trails(self.bodies, self.TRAIL_LENGTH)

        # Update debris (purely visual, no gravity)
        new_debris = []
        for d in self.debris:
            d[0] += d[2] * h * 8  # x += vx
            d[1] += d[3] * h * 8  # y += vy
            d[5] -= 1             # life--
            if d[5] > 0:
                new_debris.append(d)
        self.debris = new_debris

        # Reset when down to 1 body
        if len(self.bodies) < 2:
            self._init_bodies()

    def draw(self):
        self.display.clear(Colors.BLACK)
        _draw_bodies(self.display, self.bodies, self.palette_idx)

        # Draw debris sparks
        for d in self.debris:
            ix, iy = int(d[0]), int(d[1])
            if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                t = d[5] / self.DEBRIS_LIFE
                c = d[4]
                color = (int(c[0] * t), int(c[1] * t), int(c[2] * t))
                self.display.set_pixel(ix, iy, color)


# ── OrbitsBelt ───────────────────────────────────────────────────

class OrbitsBelt(Visual):
    name = "SPACE DUST"
    description = "Planets and asteroids"
    category = "science"
    TRAIL_LENGTH = 30

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed = 1.0
        self.palette_idx = 0
        self.dt_sim = 0.0005
        self.steps_per_frame = 8
        self._init_bodies()

    def _init_bodies(self):
        self.bodies = []
        cx, cy = GRID_SIZE / 2, GRID_SIZE / 2

        # 2-3 large planets scattered around center
        n_planets = random.randint(2, 3)
        for p in range(n_planets):
            r = random.uniform(8, 16)
            angle = 2 * math.pi * p / n_planets + random.uniform(-0.3, 0.3)
            px = cx + r * math.cos(angle)
            py = cy + r * math.sin(angle)
            # Give planets some orbital velocity around the center of mass
            v_mag = random.uniform(8, 15)
            pvx = -v_mag * math.sin(angle) + random.uniform(-1, 1)
            pvy = v_mag * math.cos(angle) + random.uniform(-1, 1)
            self.bodies.append(Body(px, py, pvx, pvy, 5.0, p))

        # Asteroid belt: 40-50 small bodies in a ring band
        n_asteroids = random.randint(40, 50)
        belt_inner = 18
        belt_outer = 27
        for i in range(n_asteroids):
            r = random.uniform(belt_inner, belt_outer)
            angle = random.uniform(0, 2 * math.pi)
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            # Gentle orbital velocity
            v_mag = random.uniform(4, 10)
            vx = -v_mag * math.sin(angle) + random.uniform(-1, 1)
            vy = v_mag * math.cos(angle) + random.uniform(-1, 1)
            mass = random.uniform(0.05, 0.2)
            self.bodies.append(Body(x, y, vx, vy, mass, (i % 4) + 2))

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.up_pressed:
            self.palette_idx = (self.palette_idx + 1) % len(PALETTES)
            consumed = True
        if input_state.down_pressed:
            self.palette_idx = (self.palette_idx - 1) % len(PALETTES)
            consumed = True
        if input_state.left:
            self.speed = max(0.2, self.speed - 0.1)
            consumed = True
        if input_state.right:
            self.speed = min(3.0, self.speed + 0.1)
            consumed = True
        if input_state.action_l or input_state.action_r:
            self._init_bodies()
            consumed = True
        return consumed

    def update(self, dt: float):
        self.time += dt
        h = self.dt_sim * self.speed
        _verlet_step(self.bodies, h, self.steps_per_frame)
        _merge_bodies(self.bodies)
        _record_trails(self.bodies, self.TRAIL_LENGTH)
        # Respawn if too few bodies remain
        if len(self.bodies) < 5:
            self._init_bodies()

    def draw(self):
        self.display.clear(Colors.BLACK)
        _draw_bodies(self.display, self.bodies, self.palette_idx)
