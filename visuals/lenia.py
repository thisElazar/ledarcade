"""
Lenia - Continuous Cellular Automaton
======================================
Lenia is a continuous generalization of Conway's Game of Life.
Cells have continuous values 0.0-1.0, with a smooth bell-shaped
kernel and growth function.

Simulated at 128x128 with R=13 kernel, downsampled to 64x64 for display.

Controls (LENIA):
  Up/Down  - Cycle color palette
  Button   - Re-seed grid

Controls (LENIA LAB):
  Left/Right - Adjust mu (growth center)
  Up/Down    - Adjust sigma (growth width)
  Button     - Cycle palette + reseed
  Both       - Commit params to settings
"""

import numpy as np
from . import Visual, Display, GRID_SIZE
from .turing import PALETTES, _PAL_ARRAYS
import settings

N = GRID_SIZE       # Display resolution (64)
SIM = 128           # Internal simulation resolution
R = 13              # Kernel radius (proper scale for 128x128)


def _bell(x, mu, sigma):
    """Bell-shaped function."""
    return np.exp(-((x - mu) ** 2) / (2.0 * sigma ** 2))


def _make_kernel(R):
    """Create ring-shaped bell kernel."""
    y, x = np.mgrid[-R:R+1, -R:R+1]
    dist = np.sqrt(x * x + y * y) / R
    kernel = _bell(dist, 0.5, 0.15)
    kernel[dist > 1.0] = 0.0
    kernel /= kernel.sum()
    return kernel


def _init_lenia_grid():
    """Initialize 128x128 grid with 35% random soup."""
    grid = np.zeros((SIM, SIM), dtype=np.float64)
    mask = np.random.random((SIM, SIM)) < 0.35
    grid[mask] = np.random.random(mask.sum())
    return grid


# Precompute kernel and its FFT at SIM resolution
_KERNEL = _make_kernel(R)
_KERNEL_PAD = np.zeros((SIM, SIM), dtype=np.float64)
_kh, _kw = _KERNEL.shape
_KERNEL_PAD[:_kh, :_kw] = _KERNEL
_KERNEL_PAD = np.roll(np.roll(_KERNEL_PAD, -(_kh // 2), axis=0),
                       -(_kw // 2), axis=1)
_KERNEL_FFT = np.fft.rfft2(_KERNEL_PAD)


def _step_lenia(grid, mu, sigma, dt, steps):
    """Run steps iterations of Lenia using FFT convolution at 128x128."""
    kfft = _KERNEL_FFT
    for _ in range(steps):
        gfft = np.fft.rfft2(grid)
        potential = np.fft.irfft2(gfft * kfft, s=(SIM, SIM))
        growth = 2.0 * np.exp(-((potential - mu) ** 2) / (2.0 * sigma ** 2)) - 1.0
        grid = np.clip(grid + dt * growth, 0.0, 1.0)
    return grid


def _downsample(grid):
    """2x2 average downsample from SIM (128) to N (64)."""
    return grid.reshape(N, SIM // N, N, SIM // N).mean(axis=(1, 3))


def _draw_lenia(display, grid, palette_idx):
    """Downsample and draw through a color palette (vectorized)."""
    small = _downsample(grid)
    pal_arr = _PAL_ARRAYS[palette_idx]
    n_colors = len(pal_arr)
    t = np.clip(small, 0.0, 1.0)
    idx_f = t * (n_colors - 1)
    lo = idx_f.astype(np.intp)
    hi = np.minimum(lo + 1, n_colors - 1)
    frac = (idx_f - lo)[:, :, np.newaxis]
    colors = pal_arr[lo] + (pal_arr[hi] - pal_arr[lo]) * frac
    pixels = np.clip(colors, 0, 255).astype(np.uint8)
    for y in range(N):
        row = pixels[y]
        for x in range(N):
            p = row[x]
            display.set_pixel(x, y, (int(p[0]), int(p[1]), int(p[2])))


# Named regions in mu x sigma space (tuned for R=13 on 128x128)
_REGIONS = [
    ('SPARSE LIFE',   0.10, 0.14, 0.012, 0.022),
    ('SMOOTH FLOW',   0.14, 0.18, 0.014, 0.028),
    ('DENSE BLOBS',   0.10, 0.16, 0.030, 0.060),
    ('CRAWLERS',      0.18, 0.24, 0.025, 0.050),
    ('CHAOTIC',       0.16, 0.22, 0.040, 0.070),
    ('TURBULENCE',    0.22, 0.28, 0.050, 0.080),
]


def _nearest_region(mu, sigma):
    for name, mu_lo, mu_hi, s_lo, s_hi in _REGIONS:
        if mu_lo <= mu <= mu_hi and s_lo <= sigma <= s_hi:
            return name
    if mu > 0.40 or sigma < 0.008:
        return 'VOID'
    return ''


class Lenia(Visual):
    name = "LENIA"
    description = "Continuous cellular automaton"
    category = "automata"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.mu = settings.get('lenia_lab_mu', 0.15)
        self.sigma = settings.get('lenia_lab_sigma', 0.022)
        self.palette_idx = settings.get('lenia_lab_palette', 0) % len(PALETTES)
        self.dt = 0.1
        self.steps_per_frame = 2
        self.grid = _init_lenia_grid()
        self._both_pressed_prev = False
        self._dead_frames = 0

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.up_pressed:
            self.palette_idx = (self.palette_idx + 1) % len(PALETTES)
            consumed = True
        if input_state.down_pressed:
            self.palette_idx = (self.palette_idx - 1) % len(PALETTES)
            consumed = True
        both = input_state.action_l and input_state.action_r
        if not both and (input_state.action_l or input_state.action_r):
            if not self._both_pressed_prev:
                self.grid = _init_lenia_grid()
                self._dead_frames = 0
                consumed = True
        self._both_pressed_prev = both
        return consumed

    def update(self, dt: float):
        self.time += dt
        self.grid = _step_lenia(self.grid, self.mu, self.sigma,
                                 self.dt, self.steps_per_frame)
        if self.grid.sum() < 2.0:
            self._dead_frames += 1
            if self._dead_frames > 3:
                self.grid = _init_lenia_grid()
                self._dead_frames = 0
        else:
            self._dead_frames = 0

    def draw(self):
        _draw_lenia(self.display, self.grid, self.palette_idx)


class LeniaLab(Visual):
    name = "LENIA LAB"
    description = "Explore Lenia parameter space"
    category = "automata"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.mu = settings.get('lenia_lab_mu', 0.15)
        self.sigma = settings.get('lenia_lab_sigma', 0.022)
        self.palette_idx = settings.get('lenia_lab_palette', 0) % len(PALETTES)
        self.dt = 0.1
        self.steps_per_frame = 2
        self.grid = _init_lenia_grid()
        self._dead_frames = 0
        self.param_overlay_timer = 2.0
        self.saved_timer = 0.0
        self.confirm_timer = 0.0
        self._both_held_prev = False

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.left_pressed:
            self.mu = max(0.05, round(self.mu - 0.005, 3))
            self.param_overlay_timer = 2.0
            consumed = True
        if input_state.right_pressed:
            self.mu = min(0.50, round(self.mu + 0.005, 3))
            self.param_overlay_timer = 2.0
            consumed = True
        if input_state.up_pressed:
            self.sigma = min(0.100, round(self.sigma + 0.002, 3))
            self.param_overlay_timer = 2.0
            consumed = True
        if input_state.down_pressed:
            self.sigma = max(0.008, round(self.sigma - 0.002, 3))
            self.param_overlay_timer = 2.0
            consumed = True
        both_held = input_state.action_l_held and input_state.action_r_held
        both_released = self._both_held_prev and not both_held
        if both_released:
            self.confirm_timer = 3.0
            consumed = True
        elif self.confirm_timer > 0 and not both_held:
            if input_state.action_r:
                settings.set('lenia_lab_mu', round(self.mu, 3))
                settings.set('lenia_lab_sigma', round(self.sigma, 3))
                settings.set('lenia_lab_palette', self.palette_idx)
                self.saved_timer = 1.5
                self.confirm_timer = 0.0
                consumed = True
            elif input_state.action_l:
                self.confirm_timer = 0.0
                consumed = True
        elif not both_held:
            if input_state.action_l or input_state.action_r:
                self.palette_idx = (self.palette_idx + 1) % len(PALETTES)
                self.grid = _init_lenia_grid()
                consumed = True
        self._both_held_prev = both_held
        return consumed

    def update(self, dt: float):
        self.time += dt
        self.grid = _step_lenia(self.grid, self.mu, self.sigma,
                                 self.dt, self.steps_per_frame)
        if self.grid.sum() < 2.0:
            self._dead_frames += 1
            if self._dead_frames > 3:
                self.grid = _init_lenia_grid()
                self._dead_frames = 0
        else:
            self._dead_frames = 0
        if self.param_overlay_timer > 0:
            self.param_overlay_timer = max(0.0, self.param_overlay_timer - dt)
        if self.saved_timer > 0:
            self.saved_timer = max(0.0, self.saved_timer - dt)
        if self.confirm_timer > 0:
            self.confirm_timer = max(0.0, self.confirm_timer - dt)

    def draw(self):
        _draw_lenia(self.display, self.grid, self.palette_idx)

        if self.param_overlay_timer > 0:
            alpha = min(1.0, self.param_overlay_timer / 0.5)
            c = (int(255 * alpha), int(255 * alpha), int(255 * alpha))
            region = _nearest_region(self.mu, self.sigma)
            if region:
                self.display.draw_text_small(2, 2, region, c)
                self.display.draw_text_small(2, 8, "mu=%.3f" % self.mu, c)
                self.display.draw_text_small(2, 14, "sig=%.3f" % self.sigma, c)
            else:
                self.display.draw_text_small(2, 2, "mu=%.3f" % self.mu, c)
                self.display.draw_text_small(2, 8, "sig=%.3f" % self.sigma, c)

        if self.confirm_timer > 0 and self.saved_timer <= 0:
            alpha = min(1.0, self.confirm_timer / 0.5)
            c = (int(255 * alpha), int(220 * alpha), int(80 * alpha))
            self.display.draw_text_small(2, 20, "SAVE?", c)
        if self.saved_timer > 0:
            alpha = min(1.0, self.saved_timer / 0.5)
            c = (int(80 * alpha), int(255 * alpha), int(80 * alpha))
            self.display.draw_text_small(2, 20, "SAVED", c)
