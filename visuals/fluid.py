"""
Fluid - Stable Fluids Solver (numpy-accelerated)
==============================
Jos Stam's "Stable Fluids" on a 64x64 grid: semi-Lagrangian
advection with Gauss-Seidel pressure projection.

Five standalone visuals share the solver:
  Wind Tunnel  - Flow past obstacle, vortex shedding
  Ink Drops    - Colored density injected at random points
  Color Mix    - Two colored fluids stirred together
  Fluid Play   - Joystick-driven cursor drags through fluid
  Fluid Sculpt - Move obstacle through constant flow

Controls:
  Up/Down    - Cycle color palette / viz mode
  Left/Right - Adjust viscosity (Tunnel/Ink) / move cursor (Play/Sculpt)
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


def _draw_density(display, dens, palette_idx, scale=0.3, sqrt_map=False):
    """Map density field to palette and draw."""
    pal_arr = _PAL_ARRAYS[palette_idx]
    n_colors = len(pal_arr)

    t = np.clip(dens[1:N+1, 1:N+1] * scale, 0.0, 1.0)
    if sqrt_map:
        np.sqrt(t, out=t)
    idx_f = t * (n_colors - 1)
    lo = idx_f.astype(np.intp)
    hi = np.minimum(lo + 1, n_colors - 1)
    frac = (idx_f - lo)[:, :, np.newaxis]
    colors = pal_arr[lo] + (pal_arr[hi] - pal_arr[lo]) * frac
    pixels = np.clip(colors, 0, 255).astype(np.uint8)

    for i in range(N):
        col = pixels[i]
        for j in range(N):
            p = col[j]
            display.set_pixel(i, j, (int(p[0]), int(p[1]), int(p[2])))


# ── Velocity / Vorticity visualization helpers ────────────────────

# Velocity palettes (magnitude → color)
VEL_PALETTES = {
    'RAINBOW': np.array([
        (0, 0, 0), (0, 0, 180), (0, 180, 255),
        (0, 255, 80), (255, 255, 0), (255, 100, 0), (255, 255, 255),
    ], dtype=np.float64),
    'INFERNO': np.array([
        (0, 0, 4), (40, 11, 84), (101, 21, 110),
        (159, 42, 99), (212, 72, 66), (245, 125, 21),
        (252, 210, 37), (252, 255, 164),
    ], dtype=np.float64),
    'ELECTRIC': np.array([
        (0, 0, 0), (20, 0, 60), (60, 0, 160),
        (160, 0, 255), (255, 0, 200), (255, 100, 100), (255, 255, 255),
    ], dtype=np.float64),
}

VEL_PALETTE_NAMES = list(VEL_PALETTES.keys())
_VEL_PALETTE = VEL_PALETTES['RAINBOW']  # default for legacy callers

# Direction hue wheels (angle → color, brightness from magnitude)
DIR_PALETTES = {
    'RAINBOW': np.array([
        (255, 0, 0), (255, 180, 0), (0, 255, 0), (0, 255, 200),
        (0, 100, 255), (120, 0, 255), (255, 0, 180), (255, 0, 0),
    ], dtype=np.float64),
    'WARM-COOL': np.array([
        (255, 60, 0), (255, 200, 60), (200, 255, 120), (60, 220, 200),
        (0, 100, 255), (40, 0, 180), (180, 0, 120), (255, 60, 0),
    ], dtype=np.float64),
    'NEON': np.array([
        (255, 0, 100), (255, 0, 255), (100, 0, 255), (0, 80, 255),
        (0, 255, 200), (0, 255, 0), (255, 255, 0), (255, 0, 100),
    ], dtype=np.float64),
}

DIR_PALETTE_NAMES = list(DIR_PALETTES.keys())

# Vorticity palettes (diverging: negative curl → zero → positive curl)
VORT_PALETTES = {
    'FIRE-ICE': np.array([
        (0, 120, 255), (0, 50, 180), (12, 8, 16),
        (180, 40, 0), (255, 120, 0),
    ], dtype=np.float64),
    'CYAN-MAG': np.array([
        (0, 255, 255), (0, 100, 140), (8, 8, 12),
        (140, 0, 100), (255, 0, 255),
    ], dtype=np.float64),
    'GOLD-TEAL': np.array([
        (0, 200, 180), (0, 80, 100), (10, 8, 8),
        (120, 80, 0), (255, 200, 40),
    ], dtype=np.float64),
}

VORT_PALETTE_NAMES = list(VORT_PALETTES.keys())
_VORT_PALETTE = VORT_PALETTES['FIRE-ICE']  # default for legacy callers


def _draw_velocity(display, u, v, palette=None):
    """Map velocity magnitude to palette and draw."""
    pal = palette if palette is not None else _VEL_PALETTE
    mag = np.sqrt(u[1:N+1, 1:N+1]**2 + v[1:N+1, 1:N+1]**2)
    t = np.clip(mag * 0.3, 0.0, 1.0)
    np.sqrt(t, out=t)
    n_colors = len(pal)
    idx_f = t * (n_colors - 1)
    lo = idx_f.astype(np.intp)
    hi = np.minimum(lo + 1, n_colors - 1)
    frac = (idx_f - lo)[:, :, np.newaxis]
    colors = pal[lo] + (pal[hi] - pal[lo]) * frac
    pixels = np.clip(colors, 0, 255).astype(np.uint8)
    for i in range(N):
        col = pixels[i]
        for j in range(N):
            p = col[j]
            display.set_pixel(i, j, (int(p[0]), int(p[1]), int(p[2])))


def _draw_velocity_direction(display, u, v, palette=None):
    """Map velocity direction to hue, magnitude to brightness."""
    pal = palette if palette is not None else DIR_PALETTES['RAINBOW']
    uu = u[1:N+1, 1:N+1]
    vv = v[1:N+1, 1:N+1]
    mag = np.sqrt(uu**2 + vv**2)
    brightness = np.clip(mag * 0.4, 0.0, 1.0)
    np.sqrt(brightness, out=brightness)

    # Angle → 0..1 mapped to hue wheel
    angle = np.arctan2(vv, uu)  # -pi..pi
    t = (angle / (2 * np.pi) + 0.5) % 1.0  # 0..1
    n_colors = len(pal)
    idx_f = t * (n_colors - 1)
    lo = idx_f.astype(np.intp)
    hi = np.minimum(lo + 1, n_colors - 1)
    frac = (idx_f - lo)[:, :, np.newaxis]
    hue_colors = pal[lo] + (pal[hi] - pal[lo]) * frac

    colors = hue_colors * brightness[:, :, np.newaxis]
    pixels = np.clip(colors, 0, 255).astype(np.uint8)
    for i in range(N):
        col = pixels[i]
        for j in range(N):
            p = col[j]
            display.set_pixel(i, j, (int(p[0]), int(p[1]), int(p[2])))


def _draw_vorticity(display, u, v, palette=None):
    """Map vorticity (curl) to diverging palette and draw."""
    pal = palette if palette is not None else _VORT_PALETTE
    # curl = dv/dx - du/dy (central differences on interior)
    dvdx = (v[2:N+2, 1:N+1] - v[0:N, 1:N+1]) * 0.5
    dudy = (u[1:N+1, 2:N+2] - u[1:N+1, 0:N]) * 0.5
    curl = dvdx - dudy
    # Map to 0..1 with 0.5 = zero curl
    t = np.clip(curl * 0.5 + 0.5, 0.0, 1.0)
    n_colors = len(pal)
    idx_f = t * (n_colors - 1)
    lo = idx_f.astype(np.intp)
    hi = np.minimum(lo + 1, n_colors - 1)
    frac = (idx_f - lo)[:, :, np.newaxis]
    colors = pal[lo] + (pal[hi] - pal[lo]) * frac
    pixels = np.clip(colors, 0, 255).astype(np.uint8)
    for i in range(N):
        col = pixels[i]
        for j in range(N):
            p = col[j]
            display.set_pixel(i, j, (int(p[0]), int(p[1]), int(p[2])))


# ── Obstacle shapes ───────────────────────────────────────────────

OBSTACLE_NAMES = [
    'circle', 'square', 'wedge',
    'airfoil', 'diamond', 'plate',
    'arrow', 'cross', 'elbow',
    'tesla',
]


def _make_obstacle(shape_idx):
    """Create obstacle mask for the given shape."""
    obs = np.zeros((S, S), dtype=bool)
    cx, cy = N // 3, N // 2
    dx = _II - cx
    dy = _JJ - cy

    shape = OBSTACLE_NAMES[shape_idx % len(OBSTACLE_NAMES)]
    if shape == 'circle':
        obs[1:N+1, 1:N+1] = (dx * dx + dy * dy) <= 16  # r=4
    elif shape == 'square':
        obs[1:N+1, 1:N+1] = (np.abs(dx) <= 4) & (np.abs(dy) <= 4)
    elif shape == 'wedge':
        obs[1:N+1, 1:N+1] = (dx >= -2) & (dx <= 6) & (np.abs(dy) <= np.maximum(0, (dx + 3) * 0.6))
    elif shape == 'airfoil':
        # Elliptical nose + linear taper tail
        nose = (dx >= -3) & (dx <= 0) & (dy * dy <= 9.0 * np.maximum(0, 1 - (dx / 3.0) ** 2))
        tail = (dx > 0) & (dx <= 8) & (np.abs(dy) <= 3.0 * (1 - dx / 8.0))
        obs[1:N+1, 1:N+1] = nose | tail
    elif shape == 'diamond':
        obs[1:N+1, 1:N+1] = (np.abs(dx) + np.abs(dy)) <= 5
    elif shape == 'plate':
        # Thin flat plate perpendicular to flow
        obs[1:N+1, 1:N+1] = (np.abs(dx) <= 1) & (np.abs(dy) <= 6)
    elif shape == 'arrow':
        # Triangle pointing into flow + rectangular tail
        tri = (dx >= -5) & (dx <= 3) & (np.abs(dy) <= (dx + 5) * 0.5)
        tail = (dx > 3) & (dx <= 8) & (np.abs(dy) <= 1)
        obs[1:N+1, 1:N+1] = tri | tail
    elif shape == 'cross':
        horiz = (np.abs(dx) <= 6) & (np.abs(dy) <= 1)
        vert = (np.abs(dx) <= 1) & (np.abs(dy) <= 4)
        obs[1:N+1, 1:N+1] = horiz | vert
    elif shape == 'elbow':
        vert_bar = (dx >= -1) & (dx <= 1) & (dy >= -5) & (dy <= 5)
        horiz_bar = (dx >= -1) & (dx <= 6) & (dy >= 3) & (dy <= 5)
        obs[1:N+1, 1:N+1] = vert_bar | horiz_bar
    elif shape == 'tesla':
        # Tesla valve: channel walls + asymmetric hook-vane baffles
        # Top/bottom channel walls
        walls = (_JJ <= 16) | (_JJ >= 48)
        # Vane 1: from top wall, angling down toward center
        y1 = 16.0 + (_II - 16)
        v1 = (np.abs(_JJ - y1) <= 1.5) & (_II >= 16) & (_II <= 30) & (_JJ >= 16)
        # Hook 1: horizontal shelf at vane tip, extends right
        h1 = (np.abs(_JJ - 30) <= 1.5) & (_II >= 28) & (_II <= 36)
        # Vane 2: from bottom wall, angling up toward center
        y2 = 48.0 - (_II - 36)
        v2 = (np.abs(_JJ - y2) <= 1.5) & (_II >= 36) & (_II <= 50) & (_JJ <= 48)
        # Hook 2: horizontal shelf at vane tip, extends right
        h2 = (np.abs(_JJ - 34) <= 1.5) & (_II >= 48) & (_II <= 56)
        obs[1:N+1, 1:N+1] = walls | v1 | h1 | v2 | h2
    return obs


# ── FluidTunnel ───────────────────────────────────────────────────

class FluidTunnel(Visual):
    name = "WIND TUNNEL"
    description = "Flow past obstacle"
    category = "science"

    def __init__(self, display: Display):
        super().__init__(display)

    # viz_mode: 0..len(PALETTES)-1 = density palettes, then velocity, then vorticity
    _N_VIZ_MODES = len(PALETTES) + 2

    def reset(self):
        self.time = 0.0
        self.viz_mode = 0
        self.viscosity = 0.0002
        self.diffusion = 0.0001
        self.shape_idx = 0
        self.overlay_text = ""
        self.overlay_timer = 0.0
        self._init_fields()

    def _init_fields(self):
        self.u = _new_field()
        self.v = _new_field()
        self.u_prev = _new_field()
        self.v_prev = _new_field()
        self.dens = _new_field()
        self.dens_prev = _new_field()
        self.obstacle = _make_obstacle(self.shape_idx)
        # Start with uniform rightward flow so advection kicks in immediately
        self.u[1:N+1, 1:N+1] = 3.0
        self._apply_obstacle()

    def _viz_mode_name(self):
        if self.viz_mode < len(PALETTES):
            names = ['THERMAL', 'FIRE', 'NEON', 'OCEAN', 'MONO']
            return names[self.viz_mode]
        elif self.viz_mode == len(PALETTES):
            return 'VELOCITY'
        else:
            return 'VORTICITY'

    # Re = U * L / viscosity.  U = 3.0 (inflow), L = 8/N (circle diameter).
    _RE_UL = 3.0 * 8.0 / N
    _VISC_MIN = 0.00005
    _VISC_MAX = 0.002

    def _re_label(self):
        re = self._RE_UL / self.viscosity
        return 'Re=%d' % int(re)

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.up_pressed:
            self.viz_mode = (self.viz_mode + 1) % self._N_VIZ_MODES
            self.overlay_text = self._viz_mode_name()
            self.overlay_timer = 2.0
            consumed = True
        if input_state.down_pressed:
            self.viz_mode = (self.viz_mode - 1) % self._N_VIZ_MODES
            self.overlay_text = self._viz_mode_name()
            self.overlay_timer = 2.0
            consumed = True
        if input_state.left:
            self.viscosity = min(self._VISC_MAX, self.viscosity * 1.25)
            self.overlay_text = self._re_label()
            self.overlay_timer = 2.0
            consumed = True
        if input_state.right:
            self.viscosity = max(self._VISC_MIN, self.viscosity * 0.8)
            self.overlay_text = self._re_label()
            self.overlay_timer = 2.0
            consumed = True
        if input_state.action_l or input_state.action_r:
            self.shape_idx = (self.shape_idx + 1) % len(OBSTACLE_NAMES)
            self._init_fields()
            self.overlay_text = OBSTACLE_NAMES[self.shape_idx].upper()
            self.overlay_timer = 2.0
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
        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

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
        if self.viz_mode < len(PALETTES):
            _draw_density(self.display, self.dens, self.viz_mode,
                          scale=0.2, sqrt_map=True)
        elif self.viz_mode == len(PALETTES):
            _draw_velocity(self.display, self.u, self.v)
        else:
            _draw_vorticity(self.display, self.u, self.v)
        # Draw obstacle pixels
        obs_ij = np.argwhere(self.obstacle[1:N+1, 1:N+1])
        for k in range(len(obs_ij)):
            self.display.set_pixel(int(obs_ij[k, 0]), int(obs_ij[k, 1]), (60, 60, 70))
        # Transient parameter overlay
        if self.overlay_timer > 0 and self.overlay_text:
            alpha = min(1.0, self.overlay_timer / 0.5)
            c = (int(255 * alpha), int(255 * alpha), int(255 * alpha))
            self.display.draw_text_small(2, 2, self.overlay_text, c)


# ── FluidInk ─────────────────────────────────────────────────────

class FluidInk(Visual):
    name = "INK DROPS"
    description = "Swirling ink drops"
    category = "science"

    _N_VIZ_MODES = len(PALETTES) + 2

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.viz_mode = 0
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
            self.viz_mode = (self.viz_mode + 1) % self._N_VIZ_MODES
            consumed = True
        if input_state.down_pressed:
            self.viz_mode = (self.viz_mode - 1) % self._N_VIZ_MODES
            consumed = True
        if input_state.left:
            self.viscosity = min(0.01, self.viscosity * 1.25)
            consumed = True
        if input_state.right:
            self.viscosity = max(0.00001, self.viscosity * 0.8)
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
        if self.viz_mode < len(PALETTES):
            _draw_density(self.display, self.dens, self.viz_mode)
        elif self.viz_mode == len(PALETTES):
            _draw_velocity(self.display, self.u, self.v)
        else:
            _draw_vorticity(self.display, self.u, self.v)


# ── FluidMixing ──────────────────────────────────────────────────

# Paint-like mixing palettes
# Each pair produces a vivid, recognizable secondary color
PAINT_PALETTES = [
    # Vermillion + Ultramarine -> rich Purple
    {'a': (255, 50, 10), 'b': (10, 30, 255)},
    # Cadmium Yellow + Cerulean -> army Green
    {'a': (255, 210, 0), 'b': (0, 80, 255)},
    # Scarlet + Amber -> burnt Orange
    {'a': (230, 30, 10), 'b': (255, 200, 0)},
    # Cyan + Magenta -> vivid Blue
    {'a': (0, 230, 255), 'b': (255, 0, 220)},
]

_PAINT_PAL_ARRAYS = [
    {'a': np.array(p['a'], dtype=np.float64),
     'b': np.array(p['b'], dtype=np.float64)}
    for p in PAINT_PALETTES
]

# Starting split patterns for visual variety
_INIT_PATTERNS = [
    'spiral', 'diagonal', 'concentric',
    'horizontal', 'quadrant', 'vertical',
]


class FluidMixing(Visual):
    name = "COLOR MIX"
    description = "Paint colors mixing"
    category = "science"

    _N_VIZ_MODES = len(PAINT_PALETTES)

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.viz_mode = 0
        self.viscosity = 0.002
        self.diffusion = 0.00005
        self.stir_speed = 1.0
        self.pattern_idx = 0
        self.mixed_time = 0.0
        self.fade_alpha = 1.0
        self.state = 'mixing'
        self._init_fields()

    def _init_fields(self):
        self.u = _new_field()
        self.v = _new_field()
        self.u_prev = _new_field()
        self.v_prev = _new_field()
        self.dens_a = _new_field()
        self.dens_b = _new_field()
        self.dens_a_prev = _new_field()
        self.dens_b_prev = _new_field()

        cx, cy = N / 2.0, N / 2.0
        pattern = _INIT_PATTERNS[self.pattern_idx % len(_INIT_PATTERNS)]

        if pattern == 'diagonal':
            mask = _II + _JJ < N + 1
            self.dens_a[1:N+1, 1:N+1] = np.where(mask, 3.0, 0.0)
            self.dens_b[1:N+1, 1:N+1] = np.where(~mask, 3.0, 0.0)
        elif pattern == 'concentric':
            dist = np.sqrt((_II - cx)**2 + (_JJ - cy)**2)
            self.dens_a[1:N+1, 1:N+1] = np.where(dist < N * 0.32, 3.5, 0.0)
            self.dens_b[1:N+1, 1:N+1] = np.where(dist >= N * 0.32, 2.5, 0.0)
        elif pattern == 'horizontal':
            half = N // 2
            self.dens_a[1:N+1, 1:half+1] = 3.0
            self.dens_b[1:N+1, half+1:N+1] = 3.0
        elif pattern == 'quadrant':
            qa = ((_II < cx) & (_JJ < cy)) | ((_II >= cx) & (_JJ >= cy))
            self.dens_a[1:N+1, 1:N+1] = np.where(qa, 3.0, 0.0)
            self.dens_b[1:N+1, 1:N+1] = np.where(~qa, 3.0, 0.0)
        elif pattern == 'vertical':
            half = N // 2
            self.dens_a[1:half+1, 1:N+1] = 3.0
            self.dens_b[half+1:N+1, 1:N+1] = 3.0
        elif pattern == 'spiral':
            angle = np.arctan2(_JJ - cy, _II - cx)
            dist = np.sqrt((_II - cx)**2 + (_JJ - cy)**2)
            spiral = np.sin(angle * 2 + dist * 0.3)
            self.dens_a[1:N+1, 1:N+1] = np.where(spiral > 0, 3.0, 0.0)
            self.dens_b[1:N+1, 1:N+1] = np.where(spiral <= 0, 3.0, 0.0)

        # Store initial pigment totals for conservation
        self.total_a0 = self.dens_a[1:N+1, 1:N+1].sum()
        self.total_b0 = self.dens_b[1:N+1, 1:N+1].sum()

        self.fade_alpha = 1.0
        self.state = 'mixing'
        self.mixed_time = 0.0
        self.age = 0.0

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.up_pressed:
            self.viscosity = min(0.008, self.viscosity * 1.4)
            consumed = True
        if input_state.down_pressed:
            self.viscosity = max(0.0003, self.viscosity / 1.4)
            consumed = True
        if input_state.left:
            self.stir_speed = max(0.25, self.stir_speed - 0.25)
            consumed = True
        if input_state.right:
            self.stir_speed = min(3.0, self.stir_speed + 0.25)
            consumed = True
        if input_state.action_l or input_state.action_r:
            self.pattern_idx += 1
            self.viz_mode = (self.viz_mode + 1) % self._N_VIZ_MODES
            self._init_fields()
            consumed = True
        return consumed

    def _add_stirring(self):
        """Organic paint-stirring: wandering vortices on Lissajous paths
        plus slow folding shear for natural-looking streaks."""
        t = self.time
        cx, cy = N / 2.0, N / 2.0

        # Gentle ramp-up: quadratic ease-in over ~8 seconds
        ramp = min(1.0, self.age * 0.12)
        ramp *= ramp
        ramp *= self.stir_speed

        # Three vortices on different Lissajous orbits
        vortex_params = [
            # (orbit_x, orbit_y, freq_x, freq_y, phase, strength, radius)
            (0.30, 0.25, 0.40, 0.60, 0.0, 3.0, 8.0),    # large figure-8
            (0.22, 0.28, 0.55, 0.35, 2.1, -2.2, 10.0),   # reverse orbit
            (0.18, 0.18, 0.70, 0.50, 4.2, 1.8, 6.0),     # small wanderer
        ]

        u_int = self.u[1:N+1, 1:N+1]
        v_int = self.v[1:N+1, 1:N+1]

        for ox, oy, fx, fy, phase, strength, radius in vortex_params:
            vx = cx + N * ox * math.sin(fx * t + phase)
            vy = cy + N * oy * math.cos(fy * t + phase)
            dx = _II - vx
            dy = _JJ - vy
            d2 = dx * dx + dy * dy
            r2 = radius * radius
            force = np.where(d2 < r2 * 2,
                             strength * ramp * np.exp(-d2 / (r2 * 0.5)), 0.0)
            u_int += -dy * force / (d2 + 4.0)
            v_int += dx * force / (d2 + 4.0)

        # Slow large-scale folding (shear) for paint-like stretching
        shear_y = 0.4 * ramp * math.sin(t * 0.25)
        u_int += shear_y * ((_JJ - cy) / (N * 0.5))
        shear_x = 0.3 * ramp * math.cos(t * 0.18)
        v_int += shear_x * ((_II - cx) / (N * 0.5))

    def update(self, dt: float):
        self.time += dt
        sim_dt = 0.1

        if self.state == 'fading':
            self.dens_a *= 0.92
            self.dens_b *= 0.92
            self.fade_alpha -= dt * 0.8
            if self.fade_alpha <= 0.0:
                self.pattern_idx += 1
                self.viz_mode = (self.viz_mode + 1) % self._N_VIZ_MODES
                self._init_fields()
            return

        self.age += dt

        self.u_prev[:] = 0.0
        self.v_prev[:] = 0.0
        self.dens_a_prev[:] = 0.0
        self.dens_b_prev[:] = 0.0

        self._add_stirring()

        _velocity_step(self.u, self.v, self.u_prev, self.v_prev,
                       self.viscosity, sim_dt)
        _density_step(self.dens_a, self.dens_a_prev, self.u, self.v,
                      self.diffusion, sim_dt)
        _density_step(self.dens_b, self.dens_b_prev, self.u, self.v,
                      self.diffusion, sim_dt)

        # Pigment conservation: zero ghost cells, rescale interior
        # to preserve exact initial totals (closed system)
        for dens, total0 in ((self.dens_a, self.total_a0),
                             (self.dens_b, self.total_b0)):
            dens[0, :] = 0.0;  dens[N+1, :] = 0.0
            dens[:, 0] = 0.0;  dens[:, N+1] = 0.0
            interior = dens[1:N+1, 1:N+1]
            current = interior.sum()
            if current > 0.01:
                interior *= total0 / current

        # Detect fully mixed -> fade out and cycle to next palette/pattern
        total = self.dens_a[1:N+1, 1:N+1] + self.dens_b[1:N+1, 1:N+1] + 0.001
        ratio = self.dens_a[1:N+1, 1:N+1] / total
        if np.var(ratio) < 0.003:
            self.mixed_time += dt
            if self.mixed_time > 4.0:
                self.state = 'fading'
                self.fade_alpha = 1.0
        else:
            self.mixed_time = 0.0

    def draw(self):
        pal = _PAINT_PAL_ARRAYS[self.viz_mode]
        ca = pal['a']
        cb = pal['b']

        da = self.dens_a[1:N+1, 1:N+1]
        db = self.dens_b[1:N+1, 1:N+1]

        # Total density -> brightness (sqrt curve for paint-like richness)
        total = da + db
        brightness = np.clip(total * 0.25, 0.0, 1.0)
        np.sqrt(brightness, out=brightness)

        # Color ratio determines hue (A vs B)
        ratio_a = da / (total + 0.01)
        mixed = ca * ratio_a[:, :, np.newaxis] + cb * (1.0 - ratio_a[:, :, np.newaxis])

        # Paint-like subtractive darkening where colors overlap
        # overlap = 1.0 at 50/50 mix, 0.0 at pure A or pure B
        overlap = 4.0 * ratio_a * (1.0 - ratio_a)
        darken = 1.0 - 0.20 * overlap

        colors = mixed * (brightness * darken)[:, :, np.newaxis]

        if self.fade_alpha < 1.0:
            colors *= max(0.0, self.fade_alpha)

        pixels = np.clip(colors, 0, 255).astype(np.uint8)

        for i in range(N):
            col = pixels[i]
            for j in range(N):
                p = col[j]
                self.display.set_pixel(i, j, (int(p[0]), int(p[1]), int(p[2])))


# ── FluidPlay ────────────────────────────────────────────────────

# Rainbow hue colors for dye trail (cycling)
_PLAY_HUES = [
    (255, 40, 40),    # red
    (255, 180, 0),    # orange
    (40, 255, 40),    # green
    (0, 160, 255),    # blue
    (200, 60, 255),   # purple
]


class FluidPlay(Visual):
    name = "FLUID PLAY"
    description = "Drag through fluid"
    category = "science"

    # Viz modes: 3 velocity, 3 direction, 3 vorticity
    _VIZ_MODES = (
        [('vel', name) for name in VEL_PALETTE_NAMES] +
        [('dir', name) for name in DIR_PALETTE_NAMES] +
        [('vort', name) for name in VORT_PALETTE_NAMES]
    )
    _N_VIZ_MODES = len(_VIZ_MODES)
    _CURSOR_SPEED = 40.0  # px/s
    _FORCE_RADIUS = 4.5
    _FORCE_STRENGTH = 8.0
    _IDLE_THRESHOLD = 3.0

    _NOTES = [
        ("NAVIER-STOKES EQUATIONS", (255, 200, 100)),
        ("DESCRIBE ALL FLUID MOTION", (180, 220, 255)),
        ("JOS STAM STABLE FLUIDS 1999", (255, 255, 255)),
        ("SEMI-LAGRANGIAN ADVECTION", (180, 220, 255)),
        ("DRAG CURSOR TO INJECT FORCE", (150, 255, 150)),
        ("BUTTON CYCLES VIEW MODE", (150, 255, 150)),
        ("VISCOSITY DAMPS MOTION", (180, 220, 255)),
        ("REYNOLDS NUMBER = INERTIA / VISCOSITY", (255, 200, 100)),
    ]

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.viz_mode = 0  # VEL RAINBOW default
        self.viscosity = 0.0002
        self.diffusion = 0.00005
        self.cx = float(N // 2)
        self.cy = float(N // 2)
        self.hue_idx = 0.0
        self.idle_timer = 0.0
        self._input_dx = 0
        self._input_dy = 0
        self.overlay_text = ""
        self.overlay_timer = 0.0
        # Notes
        self.show_notes = False
        self.notes_scroll_offset = 0.0
        self.notes_segments = []
        self.notes_scroll_len = 1
        self._both_pressed_prev = False
        self._build_notes_segments()
        self._init_fields()

    def _init_fields(self):
        self.u = _new_field()
        self.v = _new_field()
        self.u_prev = _new_field()
        self.v_prev = _new_field()
        self.dens = _new_field()
        self.dens_prev = _new_field()

    def _build_notes_segments(self):
        sep = '  --  '
        sep_color = (60, 55, 50)
        segments = []
        px_off = 0
        for i, (text, color) in enumerate(self._NOTES):
            if i > 0:
                segments.append((px_off, sep, sep_color))
                px_off += len(sep) * 4
            segments.append((px_off, text, color))
            px_off += len(text) * 4
        segments.append((px_off, sep, sep_color))
        px_off += len(sep) * 4
        self.notes_segments = segments
        self.notes_scroll_len = px_off

    def _draw_notes(self):
        d = self.display
        scroll_x = int(self.notes_scroll_offset) % self.notes_scroll_len
        for copy in (0, self.notes_scroll_len):
            for seg_off, text, color in self.notes_segments:
                px = 2 + seg_off + copy - scroll_x
                text_w = len(text) * 4
                if px + text_w < 0 or px > 64:
                    continue
                d.draw_text_small(px, 58, text, color)

    def _viz_mode_name(self):
        kind, name = self._VIZ_MODES[self.viz_mode]
        if kind == 'vel':
            return 'VEL ' + name
        elif kind == 'dir':
            return 'DIR ' + name
        else:
            return 'VORT ' + name

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Joystick: purely cursor movement (applied in update)
        self._input_dx = input_state.dx
        self._input_dy = input_state.dy

        # Both buttons: toggle notes
        both = input_state.action_l and input_state.action_r
        if both and not self._both_pressed_prev:
            self.show_notes = not self.show_notes
            self.notes_scroll_offset = 0.0
            if self.show_notes:
                self._build_notes_segments()
            consumed = True
        elif input_state.action_l or input_state.action_r:
            if not both:
                # Single button: cycle viz mode
                self.viz_mode = (self.viz_mode + 1) % self._N_VIZ_MODES
                self.overlay_text = self._viz_mode_name()
                self.overlay_timer = 2.0
                consumed = True
        self._both_pressed_prev = both

        return consumed

    def _inject_force_and_dye(self, dx, dy, dt):
        """Inject force + dye at cursor position along motion direction."""
        ci = int(self.cx)
        cj = int(self.cy)
        r = int(self._FORCE_RADIUS)
        i_lo = max(1, ci - r)
        i_hi = min(N, ci + r) + 1
        j_lo = max(1, cj - r)
        j_hi = min(N, cj + r) + 1

        # Distance mask
        ii = np.arange(i_lo, i_hi, dtype=np.float64)
        jj = np.arange(j_lo, j_hi, dtype=np.float64)
        di, dj = np.meshgrid(ii - self.cx, jj - self.cy, indexing='ij')
        d2 = di * di + dj * dj
        r2 = self._FORCE_RADIUS ** 2
        mask = np.exp(-d2 / (r2 * 0.4))

        speed = math.sqrt(dx * dx + dy * dy)
        if speed > 0.01:
            # Force proportional to cursor speed
            strength = self._FORCE_STRENGTH * min(speed / self._CURSOR_SPEED, 2.0)
            self.u[i_lo:i_hi, j_lo:j_hi] += dx / speed * strength * mask
            self.v[i_lo:i_hi, j_lo:j_hi] += dy / speed * strength * mask

        # Dye injection (rainbow cycling)
        hue = _PLAY_HUES[int(self.hue_idx) % len(_PLAY_HUES)]
        # Use density as brightness
        self.dens[i_lo:i_hi, j_lo:j_hi] += 4.0 * mask

    def _auto_perturb(self):
        """Gentle random perturbation when idle."""
        cx = random.randint(N // 4, 3 * N // 4)
        cy = random.randint(N // 4, 3 * N // 4)
        angle = random.uniform(0, 2 * math.pi)
        r = 5
        i_lo = max(1, cx - r)
        i_hi = min(N, cx + r) + 1
        j_lo = max(1, cy - r)
        j_hi = min(N, cy + r) + 1

        ii = np.arange(i_lo, i_hi, dtype=np.float64)
        jj = np.arange(j_lo, j_hi, dtype=np.float64)
        di, dj = np.meshgrid(ii - cx, jj - cy, indexing='ij')
        d2 = di * di + dj * dj
        mask = np.exp(-d2 / 12.0)

        # Vortex (tangential force)
        strength = random.uniform(1.5, 3.0)
        self.u[i_lo:i_hi, j_lo:j_hi] += -dj * strength * mask / (d2 + 2.0)
        self.v[i_lo:i_hi, j_lo:j_hi] += di * strength * mask / (d2 + 2.0)
        # Small dye drop
        self.dens[i_lo:i_hi, j_lo:j_hi] += 2.0 * mask

    def update(self, dt: float):
        self.time += dt
        sim_dt = 0.1
        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)
        if self.show_notes:
            self.notes_scroll_offset += dt * 20

        # Hue cycling
        self.hue_idx += dt * 0.8

        # Move cursor from held joystick
        if self._input_dx != 0 or self._input_dy != 0:
            move_dx = self._input_dx * self._CURSOR_SPEED * dt
            move_dy = self._input_dy * self._CURSOR_SPEED * dt
            self.cx = max(1.0, min(float(N), self.cx + move_dx))
            self.cy = max(1.0, min(float(N), self.cy + move_dy))
            self._inject_force_and_dye(move_dx, move_dy, dt)
            self.idle_timer = 0.0

        # Idle auto-activity
        self.idle_timer += dt
        if self.idle_timer > self._IDLE_THRESHOLD:
            if random.random() < dt * 0.8:
                self._auto_perturb()

        self.u_prev[:] = 0.0
        self.v_prev[:] = 0.0
        self.dens_prev[:] = 0.0

        _velocity_step(self.u, self.v, self.u_prev, self.v_prev,
                       self.viscosity, sim_dt)
        _density_step(self.dens, self.dens_prev, self.u, self.v,
                      self.diffusion, sim_dt)
        self.dens *= 0.997

    def draw(self):
        kind, name = self._VIZ_MODES[self.viz_mode]
        if kind == 'vel':
            _draw_velocity(self.display, self.u, self.v,
                           VEL_PALETTES[name])
        elif kind == 'dir':
            _draw_velocity_direction(self.display, self.u, self.v,
                                     DIR_PALETTES[name])
        else:
            _draw_vorticity(self.display, self.u, self.v,
                            VORT_PALETTES[name])

        # Draw cursor as bright dot
        ci = max(0, min(N - 1, int(self.cx) - 1))
        cj = max(0, min(N - 1, int(self.cy) - 1))
        self.display.set_pixel(ci, cj, (255, 255, 255))

        # Notes
        if self.show_notes:
            self._draw_notes()

        # Overlay
        if self.overlay_timer > 0 and self.overlay_text:
            alpha = min(1.0, self.overlay_timer / 0.5)
            c = (int(255 * alpha), int(255 * alpha), int(255 * alpha))
            self.display.draw_text_small(2, 2, self.overlay_text, c)


# ── FluidSculpt ──────────────────────────────────────────────────

def _make_obstacle_at(shape_idx, ox, oy):
    """Create obstacle mask centered at (ox, oy) with small radius."""
    obs = np.zeros((S, S), dtype=bool)
    dx = _II - ox
    dy = _JJ - oy

    shape = OBSTACLE_NAMES[shape_idx % len(OBSTACLE_NAMES)]
    if shape == 'circle':
        obs[1:N+1, 1:N+1] = (dx * dx + dy * dy) <= 12  # r~3.5
    elif shape == 'square':
        obs[1:N+1, 1:N+1] = (np.abs(dx) <= 3) & (np.abs(dy) <= 3)
    elif shape == 'wedge':
        obs[1:N+1, 1:N+1] = (dx >= -2) & (dx <= 5) & (np.abs(dy) <= np.maximum(0, (dx + 2) * 0.5))
    elif shape == 'airfoil':
        nose = (dx >= -2) & (dx <= 0) & (dy * dy <= 4.0 * np.maximum(0, 1 - (dx / 2.0) ** 2))
        tail = (dx > 0) & (dx <= 6) & (np.abs(dy) <= 2.0 * (1 - dx / 6.0))
        obs[1:N+1, 1:N+1] = nose | tail
    elif shape == 'diamond':
        obs[1:N+1, 1:N+1] = (np.abs(dx) + np.abs(dy)) <= 4
    elif shape == 'plate':
        obs[1:N+1, 1:N+1] = (np.abs(dx) <= 1) & (np.abs(dy) <= 5)
    elif shape == 'arrow':
        tri = (dx >= -4) & (dx <= 2) & (np.abs(dy) <= (dx + 4) * 0.4)
        tail = (dx > 2) & (dx <= 6) & (np.abs(dy) <= 1)
        obs[1:N+1, 1:N+1] = tri | tail
    elif shape == 'cross':
        horiz = (np.abs(dx) <= 5) & (np.abs(dy) <= 1)
        vert = (np.abs(dx) <= 1) & (np.abs(dy) <= 3)
        obs[1:N+1, 1:N+1] = horiz | vert
    elif shape == 'elbow':
        vert_bar = (dx >= -1) & (dx <= 1) & (dy >= -4) & (dy <= 4)
        horiz_bar = (dx >= -1) & (dx <= 5) & (dy >= 2) & (dy <= 4)
        obs[1:N+1, 1:N+1] = vert_bar | horiz_bar
    elif shape == 'tesla':
        # Simplified Tesla valve for moveable obstacle
        walls = (np.abs(dy) >= 4) & (np.abs(dx) <= 6)
        vane = (np.abs(dy - dx * 0.5) <= 1) & (np.abs(dx) <= 4)
        obs[1:N+1, 1:N+1] = walls | vane
    return obs


class FluidSculpt(Visual):
    name = "WIND TUNNEL LAB"
    description = "Move obstacle in flow"
    category = "science"

    _VIZ_MODES = (
        [('vel', name) for name in VEL_PALETTE_NAMES] +
        [('dir', 'DIRECTION')] +
        [('vort', name) for name in VORT_PALETTE_NAMES]
    )
    _N_VIZ_MODES = len(_VIZ_MODES)
    _CURSOR_SPEED = 30.0

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.viz_mode = 0
        self.viscosity = 0.0002
        self.diffusion = 0.0001
        self.shape_idx = 0
        self.cx = float(N // 3)
        self.cy = float(N // 2)
        self._input_dx = 0
        self._input_dy = 0
        self._both_pressed_prev = False
        self.overlay_text = ""
        self.overlay_timer = 0.0
        self._init_fields()

    def _init_fields(self):
        self.u = _new_field()
        self.v = _new_field()
        self.u_prev = _new_field()
        self.v_prev = _new_field()
        self.dens = _new_field()
        self.dens_prev = _new_field()
        self.obstacle = _make_obstacle_at(self.shape_idx, self.cx, self.cy)
        # Start with uniform rightward flow
        self.u[1:N+1, 1:N+1] = 3.0
        self._apply_obstacle()

    def _rebuild_obstacle(self):
        self.obstacle = _make_obstacle_at(self.shape_idx, self.cx, self.cy)

    def _viz_mode_name(self):
        kind, name = self._VIZ_MODES[self.viz_mode]
        if kind == 'vel':
            return 'VEL ' + name
        elif kind == 'dir':
            return 'DIR ' + name
        else:
            return 'VORT ' + name

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Joystick: purely obstacle movement (applied in update)
        self._input_dx = input_state.dx
        self._input_dy = input_state.dy

        # Both buttons: cycle obstacle shape
        both = input_state.action_l and input_state.action_r
        if both and not self._both_pressed_prev:
            self.shape_idx = (self.shape_idx + 1) % len(OBSTACLE_NAMES)
            self._rebuild_obstacle()
            self.overlay_text = OBSTACLE_NAMES[self.shape_idx].upper()
            self.overlay_timer = 2.0
            consumed = True
        elif input_state.action_l or input_state.action_r:
            if not both:
                # Single button: cycle viz mode
                self.viz_mode = (self.viz_mode + 1) % self._N_VIZ_MODES
                self.overlay_text = self._viz_mode_name()
                self.overlay_timer = 2.0
                consumed = True
        self._both_pressed_prev = both

        return consumed

    def _add_inflow(self):
        """Continuous rightward inflow on left edge."""
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
        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

        # Move obstacle from held joystick
        if self._input_dx != 0 or self._input_dy != 0:
            self.cx = max(4.0, min(float(N - 4),
                          self.cx + self._input_dx * self._CURSOR_SPEED * dt))
            self.cy = max(4.0, min(float(N - 4),
                          self.cy + self._input_dy * self._CURSOR_SPEED * dt))
            self._rebuild_obstacle()

        self.u_prev[:] = 0.0
        self.v_prev[:] = 0.0
        self.dens_prev[:] = 0.0

        self._add_inflow()
        _velocity_step(self.u, self.v, self.u_prev, self.v_prev,
                       self.viscosity, sim_dt)
        _density_step(self.dens, self.dens_prev, self.u, self.v,
                      self.diffusion, sim_dt)
        self._apply_obstacle()
        self.dens *= 0.995

    def draw(self):
        kind, name = self._VIZ_MODES[self.viz_mode]
        if kind == 'vel':
            _draw_velocity(self.display, self.u, self.v,
                           VEL_PALETTES[name])
        elif kind == 'dir':
            _draw_velocity_direction(self.display, self.u, self.v,
                                     DIR_PALETTES[name])
        else:
            _draw_vorticity(self.display, self.u, self.v,
                            VORT_PALETTES[name])

        # Draw obstacle pixels
        obs_ij = np.argwhere(self.obstacle[1:N+1, 1:N+1])
        for k in range(len(obs_ij)):
            self.display.set_pixel(int(obs_ij[k, 0]), int(obs_ij[k, 1]), (60, 60, 70))

        # Overlay
        if self.overlay_timer > 0 and self.overlay_text:
            alpha = min(1.0, self.overlay_timer / 0.5)
            c = (int(255 * alpha), int(255 * alpha), int(255 * alpha))
            self.display.draw_text_small(2, 2, self.overlay_text, c)
