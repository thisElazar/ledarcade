"""
Orbits - N-Body Gravity Simulation
====================================
Bodies orbit, slingshot, and merge under Newtonian gravity.
Velocity Verlet integration with softened potential prevents
singularities. Trails fade behind each body.

Two standalone visuals:
  Solar System   - Sun + planets in near-circular orbits
  N-Body         - Equal-mass bodies in gravitational dance

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

# Planet names and short facts for FOLLOW mode labels
_PLANET_NAMES = ["MERCURY", "VENUS", "EARTH", "MARS",
                 "JUPITER", "SATURN", "URANUS", "NEPTUNE"]
_PLANET_FACTS = [
    "88 DAY ORBIT",   # Mercury
    "HOTTEST WORLD",  # Venus
    "365 DAY ORBIT",  # Earth
    "THE RED PLANET", # Mars (13 chars)
    "GAS GIANT",      # Jupiter
    "RING SYSTEM",    # Saturn
    "ICE GIANT",      # Uranus
    "8TH PLANET",     # Neptune
]

# View modes
_VIEW_FULL = 0
_VIEW_INNER = 1
_VIEW_FOLLOW = 2
_VIEW_COUNT = 3


class OrbitsSolar(Visual):
    name = "SOLAR SYSTEM"
    description = "Sun and planets"
    category = "science_macro"
    TRAIL_LENGTH = 80

    def __init__(self, display: Display):
        super().__init__(display)

    # palette_idx 0 = realistic solar colors, 1+ = from PALETTES
    _N_PALETTES = 1 + len(PALETTES)

    def reset(self):
        self.time = 0.0
        self.speed = 1.0
        self.palette_idx = 0
        self.dt_sim = 0.0005
        self.steps_per_frame = 8

        # Camera state
        self.cx, self.cy = GRID_SIZE / 2, GRID_SIZE / 2
        self.cam_x = self.cx
        self.cam_y = self.cy
        self.cam_scale = 1.0
        self.target_cam_x = self.cx
        self.target_cam_y = self.cy
        self.target_cam_scale = 1.0

        # View cycling
        self.view_mode = _VIEW_FULL
        self.view_timer = 0.0        # time spent in current view
        self.view_cycle_delay = 8.0  # seconds per auto-cycle
        self.auto_pause_timer = 0.0  # >0 means auto-cycle paused
        self.follow_planet_idx = 0   # which planet to follow (0=Mercury)
        self.label_timer = 0.0       # toggles name vs fact

        # Background stars
        self.stars = []
        for _ in range(40):
            self.stars.append((
                random.randint(0, GRID_SIZE - 1),
                random.randint(0, GRID_SIZE - 1),
                random.randint(15, 50),
                random.uniform(0, 2 * math.pi),  # twinkle phase
            ))

        # Comet state
        self.comet = None             # active comet dict or None
        self.comet_cooldown = random.uniform(30.0, 45.0)

        self._init_bodies()

    def _init_bodies(self):
        self.bodies = []

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

    # ── Camera ───────────────────────────────────────────────────

    def _world_to_screen(self, wx, wy):
        """Transform world coordinates to screen pixel coordinates."""
        sx = (wx - self.cam_x) * self.cam_scale + GRID_SIZE / 2
        sy = (wy - self.cam_y) * self.cam_scale + GRID_SIZE / 2
        return sx, sy

    def _set_view_targets(self):
        """Set target camera position and scale for the current view mode."""
        if self.view_mode == _VIEW_FULL:
            self.target_cam_x = self.cx
            self.target_cam_y = self.cy
            self.target_cam_scale = 1.0
        elif self.view_mode == _VIEW_INNER:
            self.target_cam_x = self.cx
            self.target_cam_y = self.cy
            self.target_cam_scale = 2.5
        elif self.view_mode == _VIEW_FOLLOW:
            # Follow a specific planet (body index = planet_idx + 1)
            body_idx = self.follow_planet_idx + 1
            if body_idx < len(self.bodies):
                b = self.bodies[body_idx]
                self.target_cam_x = b.x
                self.target_cam_y = b.y
            self.target_cam_scale = 3.5

    def _advance_view(self):
        """Move to the next view mode."""
        if self.view_mode == _VIEW_FOLLOW:
            # Cycle to next planet, or wrap to FULL view
            self.follow_planet_idx += 1
            if self.follow_planet_idx >= len(SOLAR_PLANETS):
                self.follow_planet_idx = 0
                self.view_mode = _VIEW_FULL
        else:
            self.view_mode = (self.view_mode + 1) % _VIEW_COUNT
            if self.view_mode == _VIEW_FOLLOW:
                self.follow_planet_idx = 0
        self.view_timer = 0.0
        self.label_timer = 0.0
        self._set_view_targets()

    # ── Input ────────────────────────────────────────────────────

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.up_pressed:
            self.palette_idx = (self.palette_idx + 1) % self._N_PALETTES
            consumed = True
        if input_state.down_pressed:
            self.palette_idx = (self.palette_idx - 1) % self._N_PALETTES
            consumed = True
        if input_state.left:
            self.speed = max(0.2, self.speed - 0.1)
            consumed = True
        if input_state.right:
            self.speed = min(3.0, self.speed + 0.1)
            consumed = True
        if input_state.action_l or input_state.action_r:
            self._advance_view()
            self.auto_pause_timer = 15.0  # pause auto-cycle for 15s
            consumed = True
        return consumed

    def _get_body_color(self, idx):
        """Get body color: palette 0 = realistic, 1+ = from PALETTES."""
        if self.palette_idx == 0:
            return self.body_colors[idx]
        pal = PALETTES[self.palette_idx - 1]
        return pal[idx % len(pal)]

    # ── Update ───────────────────────────────────────────────────

    def update(self, dt: float):
        self.time += dt

        # Physics
        h = self.dt_sim * self.speed
        _verlet_step(self.bodies, h, self.steps_per_frame)
        self._pin_sun()
        _record_trails(self.bodies, self.TRAIL_LENGTH)

        # View auto-cycling
        self.view_timer += dt
        if self.auto_pause_timer > 0:
            self.auto_pause_timer -= dt
        elif self.view_timer >= self.view_cycle_delay:
            self._advance_view()

        # Keep follow-mode camera locked on moving planet
        if self.view_mode == _VIEW_FOLLOW:
            body_idx = self.follow_planet_idx + 1
            if body_idx < len(self.bodies):
                b = self.bodies[body_idx]
                self.target_cam_x = b.x
                self.target_cam_y = b.y

        # Label timer (name vs fact toggle every 4s)
        self.label_timer += dt

        # Smooth camera interpolation
        lerp_f = min(1.0, 3.0 * dt)
        self.cam_x += (self.target_cam_x - self.cam_x) * lerp_f
        self.cam_y += (self.target_cam_y - self.cam_y) * lerp_f
        self.cam_scale += (self.target_cam_scale - self.cam_scale) * lerp_f

        # Comet update
        self._update_comet(dt)

    def _update_comet(self, dt):
        """Spawn and move cosmetic comet."""
        if self.comet is None:
            self.comet_cooldown -= dt
            if self.comet_cooldown <= 0:
                self._spawn_comet()
        else:
            c = self.comet
            c['life'] -= dt
            if c['life'] <= 0:
                self.comet = None
                self.comet_cooldown = random.uniform(30.0, 45.0)
                return
            c['x'] += c['vx'] * dt
            c['y'] += c['vy'] * dt
            # Record trail
            c['trail'].append((c['x'], c['y']))
            if len(c['trail']) > 6:
                c['trail'].pop(0)

    def _spawn_comet(self):
        """Spawn a comet from a random screen edge."""
        edge = random.randint(0, 3)
        if edge == 0:    # top
            x, y = random.uniform(0, 63), -2.0
            vx = random.uniform(-8, 8)
            vy = random.uniform(15, 25)
        elif edge == 1:  # bottom
            x, y = random.uniform(0, 63), 65.0
            vx = random.uniform(-8, 8)
            vy = random.uniform(-25, -15)
        elif edge == 2:  # left
            x, y = -2.0, random.uniform(0, 63)
            vx = random.uniform(15, 25)
            vy = random.uniform(-8, 8)
        else:            # right
            x, y = 65.0, random.uniform(0, 63)
            vx = random.uniform(-25, -15)
            vy = random.uniform(-8, 8)
        self.comet = {
            'x': x, 'y': y, 'vx': vx, 'vy': vy,
            'life': 3.0, 'trail': [],
        }

    # ── Draw ─────────────────────────────────────────────────────

    def draw(self):
        self.display.clear(Colors.BLACK)

        self._draw_stars()
        self._draw_orbital_paths()
        self._draw_trails()
        self._draw_bodies_solar()
        self._draw_comet()
        if self.view_mode == _VIEW_FOLLOW:
            self._draw_planet_label()

    def _draw_stars(self):
        """Background star field at fixed screen positions (no camera)."""
        t = self.time
        for sx, sy, brightness, phase in self.stars:
            b = brightness * (0.5 + 0.5 * math.sin(t * 1.5 + phase))
            bv = int(max(0, min(255, b)))
            self.display.set_pixel(sx, sy, (bv, bv, bv))

    def _draw_orbital_paths(self):
        """Faint dotted circles showing orbital paths."""
        n_dots = 20
        dim = (15, 15, 25)
        for orbit_r, _color, _dr, _mass in SOLAR_PLANETS:
            for k in range(n_dots):
                angle = 2 * math.pi * k / n_dots
                wx = self.cx + orbit_r * math.cos(angle)
                wy = self.cy + orbit_r * math.sin(angle)
                sx, sy = self._world_to_screen(wx, wy)
                ix, iy = int(sx), int(sy)
                if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                    self.display.set_pixel(ix, iy, dim)

    def _draw_trails(self):
        """Draw body trails through camera transform."""
        for idx, b in enumerate(self.bodies):
            color = self._get_body_color(idx)
            trail_len = len(b.trail)
            if trail_len == 0:
                continue
            for i, (tx, ty) in enumerate(b.trail):
                sx, sy = self._world_to_screen(tx, ty)
                ix, iy = int(sx), int(sy)
                if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                    t = (i + 1) / trail_len
                    dim = (
                        int(color[0] * t * 0.35),
                        int(color[1] * t * 0.35),
                        int(color[2] * t * 0.35),
                    )
                    self.display.set_pixel(ix, iy, dim)

    def _draw_bodies_solar(self):
        """Draw sun and planets with enhanced zoom rendering."""
        for idx, b in enumerate(self.bodies):
            color = self._get_body_color(idx)
            base_r = self.body_draw_radii[idx]
            effective_r = max(1, int(base_r * self.cam_scale))

            sx, sy = self._world_to_screen(b.x, b.y)
            ix, iy = int(sx), int(sy)

            # Skip if completely off-screen (with margin for large bodies)
            margin = effective_r + 3
            if ix < -margin or ix >= GRID_SIZE + margin:
                continue
            if iy < -margin or iy >= GRID_SIZE + margin:
                continue

            # Sun (index 0): pulsing glow
            if idx == 0:
                self._draw_sun(ix, iy, effective_r, color)
                continue

            # Saturn (planet index 5, body index 6): rings
            if idx == 6 and effective_r >= 2:
                self._draw_saturn(ix, iy, effective_r, color)
                continue

            # Jupiter (planet index 4, body index 5): banding
            if idx == 5 and effective_r >= 3:
                self._draw_jupiter(ix, iy, effective_r, color)
                continue

            # Normal planet rendering
            if effective_r <= 1:
                if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                    self.display.set_pixel(ix, iy, color)
            else:
                self.display.draw_circle(ix, iy, effective_r, color, filled=True)
                if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                    bright = (
                        min(255, color[0] + 60),
                        min(255, color[1] + 60),
                        min(255, color[2] + 60),
                    )
                    self.display.set_pixel(ix, iy, bright)

    def _draw_sun(self, ix, iy, effective_r, color):
        """Draw the sun with a pulsing glow ring."""
        # Core
        self.display.draw_circle(ix, iy, effective_r, color, filled=True)
        if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
            bright = (
                min(255, color[0] + 60),
                min(255, color[1] + 60),
                min(255, color[2] + 60),
            )
            self.display.set_pixel(ix, iy, bright)

        # Pulsing glow ring when zoomed enough
        if effective_r >= 3:
            pulse = 0.7 + 0.3 * math.sin(self.time * 3.0)
            glow_r = effective_r + 1
            # Draw ring pixels (unfilled circle approximation)
            for angle_step in range(max(16, glow_r * 8)):
                a = 2 * math.pi * angle_step / max(16, glow_r * 8)
                gx = ix + int(round(glow_r * math.cos(a)))
                gy = iy + int(round(glow_r * math.sin(a)))
                if 0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE:
                    gv = int(color[0] * 0.4 * pulse)
                    gc = (gv, int(gv * 0.85), int(gv * 0.2))
                    self.display.set_pixel(gx, gy, gc)
            # Second glow ring slightly further out
            glow_r2 = effective_r + 2
            for angle_step in range(max(16, glow_r2 * 8)):
                a = 2 * math.pi * angle_step / max(16, glow_r2 * 8)
                gx = ix + int(round(glow_r2 * math.cos(a)))
                gy = iy + int(round(glow_r2 * math.sin(a)))
                if 0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE:
                    gv = int(color[0] * 0.2 * pulse)
                    gc = (gv, int(gv * 0.85), int(gv * 0.15))
                    self.display.set_pixel(gx, gy, gc)

    def _draw_saturn(self, ix, iy, effective_r, color):
        """Draw Saturn with horizontal ring line."""
        # Body
        self.display.draw_circle(ix, iy, effective_r, color, filled=True)
        if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
            bright = (
                min(255, color[0] + 60),
                min(255, color[1] + 60),
                min(255, color[2] + 60),
            )
            self.display.set_pixel(ix, iy, bright)
        # Ring: horizontal line through center, extending 2px beyond body
        ring_color = (
            min(255, color[0] + 30),
            min(255, color[1] + 30),
            min(255, color[2] + 20),
        )
        ring_ext = effective_r + 2
        for rx in range(ix - ring_ext, ix + ring_ext + 1):
            if 0 <= rx < GRID_SIZE and 0 <= iy < GRID_SIZE:
                # Only draw ring pixels outside the body circle
                if abs(rx - ix) > effective_r:
                    self.display.set_pixel(rx, iy, ring_color)

    def _draw_jupiter(self, ix, iy, effective_r, color):
        """Draw Jupiter with alternating tan/brown banding."""
        tan = (210, 180, 130)
        brown = (160, 110, 60)
        # Draw filled circle with banding: alternate rows
        for dy in range(-effective_r, effective_r + 1):
            # Horizontal extent at this y
            dx_max = int(math.sqrt(max(0, effective_r * effective_r - dy * dy)))
            row_color = tan if (dy % 2 == 0) else brown
            py = iy + dy
            if py < 0 or py >= GRID_SIZE:
                continue
            for dx in range(-dx_max, dx_max + 1):
                px = ix + dx
                if 0 <= px < GRID_SIZE:
                    self.display.set_pixel(px, py, row_color)
        # Bright center
        if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
            self.display.set_pixel(ix, iy, (230, 200, 150))

    def _draw_comet(self):
        """Draw cosmetic comet with fading blue-white trail."""
        if self.comet is None:
            return
        c = self.comet
        # Trail (screen-space, not camera-transformed — comets are foreground)
        trail_len = len(c['trail'])
        for i, (tx, ty) in enumerate(c['trail']):
            px, py = int(tx), int(ty)
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                t = (i + 1) / max(1, trail_len)
                # Blue-white fade
                r = int(100 * t)
                g = int(140 * t)
                b = int(200 * t)
                self.display.set_pixel(px, py, (r, g, b))
        # Head: bright white
        hx, hy = int(c['x']), int(c['y'])
        if 0 <= hx < GRID_SIZE and 0 <= hy < GRID_SIZE:
            self.display.set_pixel(hx, hy, (255, 255, 255))

    def _draw_planet_label(self):
        """Show planet name or fact at bottom in FOLLOW mode."""
        idx = self.follow_planet_idx
        if idx < 0 or idx >= len(_PLANET_NAMES):
            return
        # Toggle between name and fact every 4 seconds
        show_fact = (int(self.label_timer / 4.0) % 2) == 1
        if show_fact:
            text = _PLANET_FACTS[idx]
        else:
            text = _PLANET_NAMES[idx]
        self.display.draw_text_small(2, 58, text, (180, 180, 180))


# ── OrbitsMulti ──────────────────────────────────────────────────

class OrbitsMulti(Visual):
    name = "3 BODY PROBLEM"
    description = "Gravitational dance"
    category = "science_macro"
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

