"""
Fluid - Stable Fluids Solver (numpy-accelerated)
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
import numpy as np
from . import Visual, Display, Colors, GRID_SIZE

N = GRID_SIZE
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

# Precompute palette arrays for fast LUT drawing
_PAL_ARRAYS = [np.array(p, dtype=np.float64) for p in PALETTES]

# Precompute interior coordinate meshgrid (reused by advect / stirring)
_I_COORDS = np.arange(1, N + 1, dtype=np.float64)
_J_COORDS = np.arange(1, N + 1, dtype=np.float64)
_II, _JJ = np.meshgrid(_I_COORDS, _J_COORDS, indexing='ij')


def _new_field():
    return np.zeros((S, S), dtype=np.float64)


# ── Shared Stam solver (numpy) ──────────────────────────────────

def _set_bnd(b, x):
    """Set boundary conditions. b=1 for x-vel, b=2 for y-vel, b=0 for scalar."""
    if b == 1:
        x[0, 1:N+1] = -x[1, 1:N+1]
        x[N+1, 1:N+1] = -x[N, 1:N+1]
    else:
        x[0, 1:N+1] = x[1, 1:N+1]
        x[N+1, 1:N+1] = x[N, 1:N+1]

    if b == 2:
        x[1:N+1, 0] = -x[1:N+1, 1]
        x[1:N+1, N+1] = -x[1:N+1, N]
    else:
        x[1:N+1, 0] = x[1:N+1, 1]
        x[1:N+1, N+1] = x[1:N+1, N]

    x[0, 0] = 0.5 * (x[1, 0] + x[0, 1])
    x[0, N+1] = 0.5 * (x[1, N+1] + x[0, N])
    x[N+1, 0] = 0.5 * (x[N, 0] + x[N+1, 1])
    x[N+1, N+1] = 0.5 * (x[N, N+1] + x[N+1, N])


def _diffuse(b, x, x0, diff, dt, iters=4):
    a = dt * diff * N * N
    if a < 0.00001:
        x[:] = x0
        return
    inv = 1.0 / (1 + 4 * a)
    for _ in range(iters):
        x[1:N+1, 1:N+1] = (x0[1:N+1, 1:N+1] + a * (
            x[0:N, 1:N+1] + x[2:N+2, 1:N+1] +
            x[1:N+1, 0:N] + x[1:N+1, 2:N+2]
        )) * inv
        _set_bnd(b, x)


def _advect(b, d, d0, u, v, dt):
    dt0 = dt * N
    # Backtrack positions
    x = _II - dt0 * u[1:N+1, 1:N+1]
    y = _JJ - dt0 * v[1:N+1, 1:N+1]
    np.clip(x, 0.5, N + 0.5, out=x)
    np.clip(y, 0.5, N + 0.5, out=y)

    i0 = x.astype(np.intp)
    j0 = y.astype(np.intp)
    s1 = x - i0
    s0 = 1.0 - s1
    t1 = y - j0
    t0 = 1.0 - t1

    d[1:N+1, 1:N+1] = (
        s0 * (t0 * d0[i0, j0] + t1 * d0[i0, j0 + 1]) +
        s1 * (t0 * d0[i0 + 1, j0] + t1 * d0[i0 + 1, j0 + 1]))
    _set_bnd(b, d)


def _project(u, v, p, div, iters=6):
    h = 1.0 / N
    div[1:N+1, 1:N+1] = -0.5 * h * (
        u[2:N+2, 1:N+1] - u[0:N, 1:N+1] +
        v[1:N+1, 2:N+2] - v[1:N+1, 0:N])
    p[1:N+1, 1:N+1] = 0.0
    _set_bnd(0, div)
    _set_bnd(0, p)

    for _ in range(iters):
        p[1:N+1, 1:N+1] = (
            div[1:N+1, 1:N+1] +
            p[0:N, 1:N+1] + p[2:N+2, 1:N+1] +
            p[1:N+1, 0:N] + p[1:N+1, 2:N+2]) * 0.25
        _set_bnd(0, p)

    u[1:N+1, 1:N+1] -= 0.5 * (p[2:N+2, 1:N+1] - p[0:N, 1:N+1]) * N
    v[1:N+1, 1:N+1] -= 0.5 * (p[1:N+1, 2:N+2] - p[1:N+1, 0:N]) * N
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
    pal_arr = _PAL_ARRAYS[palette_idx]
    n_colors = len(pal_arr)

    t = np.clip(dens[1:N+1, 1:N+1] * 0.3, 0.0, 1.0)
    idx_f = t * (n_colors - 1)
    lo = idx_f.astype(np.intp)
    hi = np.minimum(lo + 1, n_colors - 1)
    frac = (idx_f - lo)[:, :, np.newaxis]
    colors = pal_arr[lo] + (pal_arr[hi] - pal_arr[lo]) * frac
    # Transpose to [j, i, c] for row-major buffer writes
    pixels = np.clip(colors.transpose(1, 0, 2), 0, 255).astype(np.uint8)

    buf = display.buffer
    for j in range(N):
        row = buf[j]
        prow = pixels[j]
        for i in range(N):
            p = prow[i]
            row[i] = (int(p[0]), int(p[1]), int(p[2]))


# ── Obstacle shapes ───────────────────────────────────────────────

OBSTACLE_NAMES = ['circle', 'square', 'wedge']


def _make_obstacle(shape_idx):
    """Create obstacle mask for the given shape."""
    obs = np.zeros((S, S), dtype=bool)
    cx, cy = N // 3, N // 2

    shape = OBSTACLE_NAMES[shape_idx % len(OBSTACLE_NAMES)]
    if shape == 'circle':
        r = 4
        dx = _II - cx
        dy = _JJ - cy
        obs[1:N+1, 1:N+1] = (dx * dx + dy * dy) <= r * r
    elif shape == 'square':
        hw = 4
        obs[1:N+1, 1:N+1] = (np.abs(_II - cx) <= hw) & (np.abs(_JJ - cy) <= hw)
    elif shape == 'wedge':
        dx = _II - cx
        dy = _JJ - cy
        obs[1:N+1, 1:N+1] = (dx >= -2) & (dx <= 6) & (np.abs(dy) <= np.maximum(0, (dx + 3) * 0.6))
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
        self.u[1, 1:N+1] = 3.0
        jj = np.arange(1, N + 1)
        mask = ((jj + int(self.time * 8)) % 6 < 2)
        self.dens[1, 1:N+1] = np.where(mask, 3.0, self.dens[1, 1:N+1])

    def _apply_obstacle(self):
        self.u[self.obstacle] = 0.0
        self.v[self.obstacle] = 0.0
        self.dens[self.obstacle] *= 0.5

    def update(self, dt: float):
        self.time += dt
        sim_dt = 0.1

        self.u_prev[:] = 0.0
        self.v_prev[:] = 0.0
        self.dens_prev[:] = 0.0

        self._add_forces()
        _velocity_step(self.u, self.v, self.u_prev, self.v_prev,
                       self.viscosity, sim_dt)
        _density_step(self.dens, self.dens_prev, self.u, self.v,
                      self.diffusion, sim_dt)
        self._apply_obstacle()

        self.dens *= 0.995

    def draw(self):
        _draw_density(self.display, self.dens, self.palette_idx)
        # Draw obstacle pixels
        obs_ij = np.argwhere(self.obstacle[1:N+1, 1:N+1])
        for k in range(len(obs_ij)):
            self.display.set_pixel(int(obs_ij[k, 0]), int(obs_ij[k, 1]), (60, 60, 70))


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
        i_lo = max(1, cx - 2)
        i_hi = min(N, cx + 2) + 1
        j_lo = max(1, cy - 2)
        j_hi = min(N, cy + 2) + 1
        self.dens[i_lo:i_hi, j_lo:j_hi] += 5.0
        angle = random.uniform(0, 2 * math.pi)
        force = random.uniform(2, 5)
        self.u[i_lo:i_hi, j_lo:j_hi] += force * math.cos(angle)
        self.v[i_lo:i_hi, j_lo:j_hi] += force * math.sin(angle)

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

        self.u_prev[:] = 0.0
        self.v_prev[:] = 0.0
        self.dens_prev[:] = 0.0

        self._add_forces()
        _velocity_step(self.u, self.v, self.u_prev, self.v_prev,
                       self.viscosity, sim_dt)
        _density_step(self.dens, self.dens_prev, self.u, self.v,
                      self.diffusion, sim_dt)

        self.dens *= 0.995

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

# Precompute palette arrays for mixing
_MIX_PAL_ARRAYS = [
    {'a': np.array(p['a'], dtype=np.float64),
     'b': np.array(p['b'], dtype=np.float64),
     'bg': np.array(p['bg'], dtype=np.float64)}
    for p in MIX_PALETTES
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
        self.dens_a[1:half+1, 1:N+1] = 2.0
        self.dens_b[half+1:N+1, 1:N+1] = 2.0
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
        ax = cx + r_stir * math.cos(self.stir_angle)
        ay = cy + r_stir * math.sin(self.stir_angle)
        bx = cx - r_stir * math.cos(self.stir_angle)
        by = cy - r_stir * math.sin(self.stir_angle)

        strength = 2.0
        radius_sq = 36  # 6*6
        u_int = self.u[1:N+1, 1:N+1]
        v_int = self.v[1:N+1, 1:N+1]

        # Vortex A (counter-clockwise)
        dx_a = _II - ax
        dy_a = _JJ - ay
        d2_a = dx_a * dx_a + dy_a * dy_a
        mask_a = (d2_a < radius_sq) & (d2_a > 0.5)
        inv_a = np.where(mask_a, strength / (d2_a + 2.0), 0.0)
        u_int += -dy_a * inv_a
        v_int += dx_a * inv_a

        # Vortex B (clockwise)
        dx_b = _II - bx
        dy_b = _JJ - by
        d2_b = dx_b * dx_b + dy_b * dy_b
        mask_b = (d2_b < radius_sq) & (d2_b > 0.5)
        inv_b = np.where(mask_b, strength / (d2_b + 2.0), 0.0)
        u_int += dy_b * inv_b
        v_int += -dx_b * inv_b

    def _replenish_edges(self):
        """Keep fluid A on left edge and fluid B on right edge."""
        np.maximum(self.dens_a[1, 1:N+1], 1.5, out=self.dens_a[1, 1:N+1])
        np.maximum(self.dens_b[N, 1:N+1], 1.5, out=self.dens_b[N, 1:N+1])

    def update(self, dt: float):
        self.time += dt
        sim_dt = 0.1

        self.u_prev[:] = 0.0
        self.v_prev[:] = 0.0
        self.dens_a_prev[:] = 0.0
        self.dens_b_prev[:] = 0.0

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
        pal = _MIX_PAL_ARRAYS[self.palette_idx]
        ca = pal['a']
        cb = pal['b']
        bg = pal['bg']

        da = np.clip(self.dens_a[1:N+1, 1:N+1] * 0.3, 0.0, 1.0)
        db = np.clip(self.dens_b[1:N+1, 1:N+1] * 0.3, 0.0, 1.0)

        colors = bg + (ca - bg) * da[:, :, np.newaxis] + (cb - bg) * db[:, :, np.newaxis]
        pixels = np.clip(colors.transpose(1, 0, 2), 0, 255).astype(np.uint8)

        buf = self.display.buffer
        for j in range(N):
            row = buf[j]
            prow = pixels[j]
            for i in range(N):
                p = prow[i]
                row[i] = (int(p[0]), int(p[1]), int(p[2]))
