"""
Fluid - Stable Fluids Solver
==============================
Jos Stam's "Stable Fluids" on a 64x64 grid: semi-Lagrangian
advection with Gauss-Seidel pressure projection.

Three standalone visuals share the solver:
  Wind Tunnel  - Flow past obstacle, vortex shedding
  Ink Drops    - Colored density injected at random points
  Fluid Mix    - Two colored fluids stirred together

Controls:
  Up/Down    - Cycle color palette
  Left/Right - Adjust viscosity
  Space      - Variant-specific action
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE

N = GRID_SIZE
# Use index (i, j) -> i + j*(N+2) on a padded grid of size (N+2)*(N+2)
S = N + 2  # Padded grid side length

PALETTES = [
    # Smoke: black -> blue -> white
    [(0, 0, 0), (10, 20, 60), (30, 80, 150), (100, 180, 220), (200, 230, 255), (255, 255, 255)],
    # Fire
    [(0, 0, 0), (60, 0, 0), (200, 50, 0), (255, 150, 0), (255, 240, 50), (255, 255, 200)],
    # Neon
    [(0, 0, 0), (0, 40, 80), (0, 150, 150), (80, 255, 80), (255, 255, 0), (255, 100, 255)],
    # Ocean
    [(0, 0, 10), (0, 20, 80), (0, 80, 160), (0, 180, 200), (100, 255, 220), (255, 255, 255)],
    # Monochrome
    [(0, 0, 0), (40, 40, 40), (90, 90, 90), (150, 150, 150), (210, 210, 210), (255, 255, 255)],
]


def IX(i, j):
    return i + j * S


# ── Shared Stam solver ────────────────────────────────────────────

def _set_bnd(b, x):
    """Set boundary conditions. b=1 for x-vel, b=2 for y-vel, b=0 for scalar."""
    for i in range(1, N + 1):
        x[IX(0, i)]     = -x[IX(1, i)] if b == 1 else x[IX(1, i)]
        x[IX(N + 1, i)] = -x[IX(N, i)] if b == 1 else x[IX(N, i)]
        x[IX(i, 0)]     = -x[IX(i, 1)] if b == 2 else x[IX(i, 1)]
        x[IX(i, N + 1)] = -x[IX(i, N)] if b == 2 else x[IX(i, N)]

    x[IX(0, 0)]         = 0.5 * (x[IX(1, 0)] + x[IX(0, 1)])
    x[IX(0, N + 1)]     = 0.5 * (x[IX(1, N + 1)] + x[IX(0, N)])
    x[IX(N + 1, 0)]     = 0.5 * (x[IX(N, 0)] + x[IX(N + 1, 1)])
    x[IX(N + 1, N + 1)] = 0.5 * (x[IX(N, N + 1)] + x[IX(N + 1, N)])


def _diffuse(b, x, x0, diff, dt, iters=4):
    a = dt * diff * N * N
    if a < 0.00001:
        for i in range(S * S):
            x[i] = x0[i]
        return
    for _ in range(iters):
        for j in range(1, N + 1):
            for i in range(1, N + 1):
                idx = IX(i, j)
                x[idx] = (x0[idx] + a * (
                    x[IX(i - 1, j)] + x[IX(i + 1, j)] +
                    x[IX(i, j - 1)] + x[IX(i, j + 1)]
                )) / (1 + 4 * a)
        _set_bnd(b, x)


def _advect(b, d, d0, u, v, dt):
    dt0 = dt * N
    for j in range(1, N + 1):
        for i in range(1, N + 1):
            idx = IX(i, j)
            x = i - dt0 * u[idx]
            y = j - dt0 * v[idx]

            x = max(0.5, min(N + 0.5, x))
            y = max(0.5, min(N + 0.5, y))

            i0 = int(x)
            j0 = int(y)
            i1 = i0 + 1
            j1 = j0 + 1

            s1 = x - i0
            s0 = 1 - s1
            t1 = y - j0
            t0 = 1 - t1

            d[idx] = (s0 * (t0 * d0[IX(i0, j0)] + t1 * d0[IX(i0, j1)]) +
                      s1 * (t0 * d0[IX(i1, j0)] + t1 * d0[IX(i1, j1)]))
    _set_bnd(b, d)


def _project(u, v, p, div, iters=6):
    h = 1.0 / N
    for j in range(1, N + 1):
        for i in range(1, N + 1):
            idx = IX(i, j)
            div[idx] = -0.5 * h * (
                u[IX(i + 1, j)] - u[IX(i - 1, j)] +
                v[IX(i, j + 1)] - v[IX(i, j - 1)])
            p[idx] = 0.0
    _set_bnd(0, div)
    _set_bnd(0, p)

    for _ in range(iters):
        for j in range(1, N + 1):
            for i in range(1, N + 1):
                idx = IX(i, j)
                p[idx] = (div[idx] +
                          p[IX(i - 1, j)] + p[IX(i + 1, j)] +
                          p[IX(i, j - 1)] + p[IX(i, j + 1)]) / 4.0
        _set_bnd(0, p)

    for j in range(1, N + 1):
        for i in range(1, N + 1):
            idx = IX(i, j)
            u[idx] -= 0.5 * (p[IX(i + 1, j)] - p[IX(i - 1, j)]) * N
            v[idx] -= 0.5 * (p[IX(i, j + 1)] - p[IX(i, j - 1)]) * N
    _set_bnd(1, u)
    _set_bnd(2, v)


def _velocity_step(u, v, u0, v0, viscosity, dt, iters=6):
    """Full velocity step: diffuse, project, advect, project."""
    _diffuse(1, u0, u, viscosity, dt)
    _diffuse(2, v0, v, viscosity, dt)
    _project(u0, v0, u, v, iters)
    _advect(1, u, u0, u0, v0, dt)
    _advect(2, v, v0, u0, v0, dt)
    _project(u, v, u0, v0, iters)


def _density_step(d, d0, u, v, diffusion, dt):
    """Full density step: diffuse, advect."""
    _diffuse(0, d0, d, diffusion, dt)
    _advect(0, d, d0, u, v, dt)


def _draw_density(display, dens, palette_idx):
    """Map density field to palette and draw."""
    palette = PALETTES[palette_idx]
    n_colors = len(palette)

    for j in range(N):
        for i in range(N):
            d = dens[IX(i + 1, j + 1)]
            if d < 0:
                d = 0
            t = min(1.0, d * 0.3)

            idx_f = t * (n_colors - 1)
            lo = int(idx_f)
            hi = min(lo + 1, n_colors - 1)
            frac = idx_f - lo
            c0 = palette[lo]
            c1 = palette[hi]
            r = int(c0[0] + (c1[0] - c0[0]) * frac)
            g = int(c0[1] + (c1[1] - c0[1]) * frac)
            b = int(c0[2] + (c1[2] - c0[2]) * frac)
            display.set_pixel(i, j, (r, g, b))


def _new_field():
    return [0.0] * (S * S)


# ── Obstacle shapes ───────────────────────────────────────────────

OBSTACLE_NAMES = ['circle', 'square', 'wedge']


def _make_obstacle(shape_idx):
    """Create obstacle mask for the given shape."""
    obs = [False] * (S * S)
    cx, cy = N // 3, N // 2

    shape = OBSTACLE_NAMES[shape_idx % len(OBSTACLE_NAMES)]
    if shape == 'circle':
        r = 4
        for j in range(1, N + 1):
            for i in range(1, N + 1):
                dx = i - cx
                dy = j - cy
                if dx * dx + dy * dy <= r * r:
                    obs[IX(i, j)] = True
    elif shape == 'square':
        hw = 4
        for j in range(1, N + 1):
            for i in range(1, N + 1):
                if abs(i - cx) <= hw and abs(j - cy) <= hw:
                    obs[IX(i, j)] = True
    elif shape == 'wedge':
        # Airfoil-like wedge pointing left
        for j in range(1, N + 1):
            for i in range(1, N + 1):
                dx = i - cx
                dy = j - cy
                # Wedge: widens rightward
                if -2 <= dx <= 6 and abs(dy) <= max(0, (dx + 3) * 0.6):
                    obs[IX(i, j)] = True
    return obs


# ── FluidTunnel ───────────────────────────────────────────────────

class FluidTunnel(Visual):
    name = "WIND TUNNEL"
    description = "Flow past obstacle"
    category = "science"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.palette_idx = 0
        self.viscosity = 0.0001
        self.diffusion = 0.0001
        self.shape_idx = 0
        self._init_fields()

    def _init_fields(self):
        self.u = _new_field()
        self.v = _new_field()
        self.u_prev = _new_field()
        self.v_prev = _new_field()
        self.dens = _new_field()
        self.dens_prev = _new_field()
        self.obstacle = _make_obstacle(self.shape_idx)

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.up_pressed:
            self.palette_idx = (self.palette_idx + 1) % len(PALETTES)
            consumed = True
        if input_state.down_pressed:
            self.palette_idx = (self.palette_idx - 1) % len(PALETTES)
            consumed = True
        if input_state.left:
            self.viscosity = max(0.00001, self.viscosity * 0.8)
            consumed = True
        if input_state.right:
            self.viscosity = min(0.01, self.viscosity * 1.25)
            consumed = True
        if input_state.action_l or input_state.action_r:
            self.shape_idx = (self.shape_idx + 1) % len(OBSTACLE_NAMES)
            self._init_fields()
            consumed = True
        return consumed

    def _add_forces(self):
        speed = 3.0
        for j in range(1, N + 1):
            idx = IX(1, j)
            self.u[idx] = speed
            if (j + int(self.time * 8)) % 6 < 2:
                self.dens[idx] = 3.0

    def _apply_obstacle(self):
        for j in range(1, N + 1):
            for i in range(1, N + 1):
                idx = IX(i, j)
                if self.obstacle[idx]:
                    self.u[idx] = 0.0
                    self.v[idx] = 0.0
                    self.dens[idx] *= 0.5

    def update(self, dt: float):
        self.time += dt
        sim_dt = 0.1

        for i in range(S * S):
            self.u_prev[i] = 0.0
            self.v_prev[i] = 0.0
            self.dens_prev[i] = 0.0

        self._add_forces()
        _velocity_step(self.u, self.v, self.u_prev, self.v_prev,
                       self.viscosity, sim_dt)
        _density_step(self.dens, self.dens_prev, self.u, self.v,
                      self.diffusion, sim_dt)
        self._apply_obstacle()

        for i in range(S * S):
            self.dens[i] *= 0.995

    def draw(self):
        _draw_density(self.display, self.dens, self.palette_idx)
        # Draw obstacle
        for j in range(N):
            for i in range(N):
                if self.obstacle[IX(i + 1, j + 1)]:
                    self.display.set_pixel(i, j, (60, 60, 70))


# ── FluidInk ─────────────────────────────────────────────────────

class FluidInk(Visual):
    name = "INK DROPS"
    description = "Swirling ink drops"
    category = "science"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.palette_idx = 0
        self.viscosity = 0.0001
        self.diffusion = 0.0001
        self._init_fields()

    def _init_fields(self):
        self.u = _new_field()
        self.v = _new_field()
        self.u_prev = _new_field()
        self.v_prev = _new_field()
        self.dens = _new_field()
        self.dens_prev = _new_field()

    def _add_ink_drop(self, cx=None, cy=None):
        """Add an ink drop at given position or random."""
        if cx is None:
            cx = random.randint(N // 4, 3 * N // 4)
        if cy is None:
            cy = random.randint(N // 4, 3 * N // 4)
        for dj in range(-2, 3):
            for di in range(-2, 3):
                i = cx + di
                j = cy + dj
                if 1 <= i <= N and 1 <= j <= N:
                    self.dens[IX(i, j)] += 5.0
        angle = random.uniform(0, 2 * math.pi)
        force = random.uniform(2, 5)
        for dj in range(-2, 3):
            for di in range(-2, 3):
                i = cx + di
                j = cy + dj
                if 1 <= i <= N and 1 <= j <= N:
                    idx = IX(i, j)
                    self.u[idx] += force * math.cos(angle)
                    self.v[idx] += force * math.sin(angle)

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.up_pressed:
            self.palette_idx = (self.palette_idx + 1) % len(PALETTES)
            consumed = True
        if input_state.down_pressed:
            self.palette_idx = (self.palette_idx - 1) % len(PALETTES)
            consumed = True
        if input_state.left:
            self.viscosity = max(0.00001, self.viscosity * 0.8)
            consumed = True
        if input_state.right:
            self.viscosity = min(0.01, self.viscosity * 1.25)
            consumed = True
        if input_state.action_l or input_state.action_r:
            self._add_ink_drop()
            consumed = True
        return consumed

    def _add_forces(self):
        if random.random() < 0.08:
            self._add_ink_drop()

    def update(self, dt: float):
        self.time += dt
        sim_dt = 0.1

        for i in range(S * S):
            self.u_prev[i] = 0.0
            self.v_prev[i] = 0.0
            self.dens_prev[i] = 0.0

        self._add_forces()
        _velocity_step(self.u, self.v, self.u_prev, self.v_prev,
                       self.viscosity, sim_dt)
        _density_step(self.dens, self.dens_prev, self.u, self.v,
                      self.diffusion, sim_dt)

        for i in range(S * S):
            self.dens[i] *= 0.995

    def draw(self):
        _draw_density(self.display, self.dens, self.palette_idx)


# ── FluidMixing ──────────────────────────────────────────────────

# Separate palettes for the two-fluid mixing visualization
MIX_PALETTES = [
    # Warm vs Cool
    {'a': (220, 60, 30), 'b': (30, 80, 220), 'bg': (5, 5, 10)},
    # Green vs Magenta
    {'a': (40, 220, 60), 'b': (220, 40, 180), 'bg': (5, 5, 5)},
    # Orange vs Cyan
    {'a': (240, 160, 30), 'b': (30, 200, 220), 'bg': (5, 5, 8)},
    # Gold vs Purple
    {'a': (255, 200, 50), 'b': (120, 40, 200), 'bg': (5, 3, 8)},
    # Red vs Green
    {'a': (220, 40, 40), 'b': (40, 200, 80), 'bg': (5, 5, 5)},
]


class FluidMixing(Visual):
    name = "FLUID MIX"
    description = "Two fluids mixing"
    category = "science"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.palette_idx = 0
        self.viscosity = 0.001
        self.diffusion = 0.0002
        self._init_fields()

    def _init_fields(self):
        self.u = _new_field()
        self.v = _new_field()
        self.u_prev = _new_field()
        self.v_prev = _new_field()
        # Two density fields
        self.dens_a = _new_field()
        self.dens_b = _new_field()
        self.dens_a_prev = _new_field()
        self.dens_b_prev = _new_field()
        # Initialize: left half = fluid A, right half = fluid B
        half = N // 2
        for j in range(1, N + 1):
            for i in range(1, N + 1):
                if i <= half:
                    self.dens_a[IX(i, j)] = 2.0
                else:
                    self.dens_b[IX(i, j)] = 2.0
        # Stirring vortex state
        self.stir_angle = 0.0

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.up_pressed:
            self.palette_idx = (self.palette_idx + 1) % len(MIX_PALETTES)
            consumed = True
        if input_state.down_pressed:
            self.palette_idx = (self.palette_idx - 1) % len(MIX_PALETTES)
            consumed = True
        if input_state.left:
            self.viscosity = max(0.00001, self.viscosity * 0.8)
            consumed = True
        if input_state.right:
            self.viscosity = min(0.01, self.viscosity * 1.25)
            consumed = True
        if input_state.action_l or input_state.action_r:
            self._init_fields()
            consumed = True
        return consumed

    def _add_stirring(self):
        """Two counter-rotating vortex forces that slowly drift."""
        cx, cy = N // 2, N // 2
        self.stir_angle += 0.015
        r_stir = N * 0.22
        # Vortex A
        ax = cx + r_stir * math.cos(self.stir_angle)
        ay = cy + r_stir * math.sin(self.stir_angle)
        # Vortex B (opposite side)
        bx = cx - r_stir * math.cos(self.stir_angle)
        by = cy - r_stir * math.sin(self.stir_angle)

        strength = 2.0
        radius = 6
        for j in range(1, N + 1):
            for i in range(1, N + 1):
                idx = IX(i, j)
                # Vortex A (counter-clockwise)
                dx_a = i - ax
                dy_a = j - ay
                d2_a = dx_a * dx_a + dy_a * dy_a
                if d2_a < radius * radius and d2_a > 0.5:
                    inv = strength / (d2_a + 2.0)
                    self.u[idx] += -dy_a * inv
                    self.v[idx] += dx_a * inv
                # Vortex B (clockwise)
                dx_b = i - bx
                dy_b = j - by
                d2_b = dx_b * dx_b + dy_b * dy_b
                if d2_b < radius * radius and d2_b > 0.5:
                    inv = strength / (d2_b + 2.0)
                    self.u[idx] += dy_b * inv
                    self.v[idx] += -dx_b * inv

    def _replenish_edges(self):
        """Keep fluid A on left edge and fluid B on right edge to prevent runaway."""
        for j in range(1, N + 1):
            # Left edge: replenish fluid A
            idx_l = IX(1, j)
            self.dens_a[idx_l] = max(self.dens_a[idx_l], 1.5)
            # Right edge: replenish fluid B
            idx_r = IX(N, j)
            self.dens_b[idx_r] = max(self.dens_b[idx_r], 1.5)

    def update(self, dt: float):
        self.time += dt
        sim_dt = 0.1

        for i in range(S * S):
            self.u_prev[i] = 0.0
            self.v_prev[i] = 0.0
            self.dens_a_prev[i] = 0.0
            self.dens_b_prev[i] = 0.0

        self._add_stirring()
        self._replenish_edges()

        # Velocity step (shared by both densities)
        _velocity_step(self.u, self.v, self.u_prev, self.v_prev,
                       self.viscosity, sim_dt)

        # Density steps for both fluids
        _density_step(self.dens_a, self.dens_a_prev, self.u, self.v,
                      self.diffusion, sim_dt)
        _density_step(self.dens_b, self.dens_b_prev, self.u, self.v,
                      self.diffusion, sim_dt)

    def draw(self):
        pal = MIX_PALETTES[self.palette_idx]
        ca = pal['a']
        cb = pal['b']
        bg = pal['bg']

        for j in range(N):
            for i in range(N):
                da = self.dens_a[IX(i + 1, j + 1)]
                db = self.dens_b[IX(i + 1, j + 1)]
                if da < 0:
                    da = 0
                if db < 0:
                    db = 0
                # Normalize
                ta = min(1.0, da * 0.3)
                tb = min(1.0, db * 0.3)

                # Blend: background + fluid_a color + fluid_b color
                r = int(bg[0] + (ca[0] - bg[0]) * ta + (cb[0] - bg[0]) * tb)
                g = int(bg[1] + (ca[1] - bg[1]) * ta + (cb[1] - bg[1]) * tb)
                b = int(bg[2] + (ca[2] - bg[2]) * ta + (cb[2] - bg[2]) * tb)
                r = max(0, min(255, r))
                g = max(0, min(255, g))
                b = max(0, min(255, b))
                self.display.set_pixel(i, j, (r, g, b))
