"""
Turing - Reaction-Diffusion Patterns (numpy-accelerated)
======================================
Gray-Scott model generates organic patterns from two interacting chemicals.
Four standalone visuals each lock to a specific pattern family:
  Spots, Stripes/Lines, Coral, and Worms.

Left/Right adjusts feed rate F within the family range (k adjusts
proportionally), keeping the pattern in-family but morphing.

Controls:
  Up/Down    - Cycle color palette
  Left/Right - Adjust F parameter within family range
  Space      - Re-seed grid
"""

import random
import numpy as np
from . import Visual, Display, Colors, GRID_SIZE

# Diffusion rates
DU = 0.16
DV = 0.08

PALETTES = [
    # Ocean: deep blue to white
    [(5, 10, 40), (10, 40, 120), (20, 100, 180), (80, 200, 220), (200, 255, 255), (255, 255, 255)],
    # Fire: black to yellow
    [(10, 5, 0), (80, 10, 0), (200, 50, 0), (255, 150, 0), (255, 230, 50), (255, 255, 200)],
    # Forest
    [(5, 15, 5), (10, 60, 20), (30, 130, 40), (80, 200, 60), (180, 240, 100), (240, 255, 200)],
    # Purple
    [(10, 0, 20), (40, 0, 80), (100, 20, 160), (180, 80, 220), (220, 160, 255), (255, 230, 255)],
    # Grayscale
    [(10, 10, 10), (50, 50, 50), (100, 100, 100), (160, 160, 160), (210, 210, 210), (255, 255, 255)],
    # Thermal
    [(0, 0, 40), (0, 0, 150), (0, 180, 180), (0, 255, 0), (255, 255, 0), (255, 0, 0)],
]

# Precompute palette arrays for vectorized color mapping
_PAL_ARRAYS = [np.array(p, dtype=np.float64) for p in PALETTES]

N = GRID_SIZE
S = N + 2  # Padded grid side length


# ── Shared Gray-Scott solver (numpy) ──────────────────────────────

def _wrap_boundaries(x):
    """Copy interior edges to padding cells for toroidal wrapping."""
    x[0, 1:N+1] = x[N, 1:N+1]
    x[N+1, 1:N+1] = x[1, 1:N+1]
    x[1:N+1, 0] = x[1:N+1, N]
    x[1:N+1, N+1] = x[1:N+1, 1]
    x[0, 0] = x[N, N]
    x[0, N+1] = x[N, 1]
    x[N+1, 0] = x[1, N]
    x[N+1, N+1] = x[1, 1]


def _init_grid():
    """Initialize U=1, V=0 with random seed patches of V."""
    u = np.ones((S, S), dtype=np.float64)
    v = np.zeros((S, S), dtype=np.float64)

    n_seeds = random.randint(3, 6)
    for _ in range(n_seeds):
        cx = random.randint(5, N - 6)
        cy = random.randint(5, N - 6)
        r = random.randint(2, 4)
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if dx * dx + dy * dy <= r * r:
                    xi = (cx + dx) % N + 1
                    yi = (cy + dy) % N + 1
                    v[yi, xi] = 0.5 + random.uniform(-0.05, 0.05)
                    u[yi, xi] = 0.5 + random.uniform(-0.05, 0.05)
    _wrap_boundaries(u)
    _wrap_boundaries(v)
    return u, v


def _step_gray_scott(u, v, f, k, steps):
    """Run *steps* iterations of the Gray-Scott reaction-diffusion (numpy)."""
    du = DU
    dv = DV
    I = slice(1, N + 1)
    Im = slice(0, N)
    Ip = slice(2, N + 2)

    for _ in range(steps):
        _wrap_boundaries(u)
        _wrap_boundaries(v)

        u_c = u[I, I].copy()
        v_c = v[I, I].copy()

        lap_u = u[Im, I] + u[Ip, I] + u[I, Im] + u[I, Ip] - 4.0 * u_c
        lap_v = v[Im, I] + v[Ip, I] + v[I, Im] + v[I, Ip] - 4.0 * v_c

        uvv = u_c * v_c * v_c

        u[I, I] = u_c + du * lap_u - uvv + f * (1.0 - u_c)
        v[I, I] = v_c + dv * lap_v + uvv - (f + k) * v_c

    return u, v


def _draw_turing(display, v, palette_idx):
    """Draw V concentration through a color palette (vectorized)."""
    pal_arr = _PAL_ARRAYS[palette_idx]
    n_colors = len(pal_arr)

    t = np.clip(v[1:N+1, 1:N+1], 0.0, 1.0)
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


# ── Base class (not exported) ─────────────────────────────────────

class _TuringBase(Visual):
    """Shared logic for all Turing pattern visuals."""

    # Subclasses override these
    _f_center = 0.035
    _k_center = 0.065
    _f_min = 0.030
    _f_max = 0.042
    _k_min = 0.060
    _k_max = 0.070

    def __init__(self, display: Display):
        super().__init__(display)

    def _get_notes(self):
        """Return list of (text, color) tuples. Subclasses override."""
        return [("TURING PATTERN", (255, 255, 255))]

    def _build_notes_segments(self):
        sep = '  --  '
        sep_color = (60, 55, 50)
        segments = []
        px_off = 0
        for i, (text, color) in enumerate(self._get_notes()):
            if i > 0:
                segments.append((px_off, sep, sep_color))
                px_off += len(sep) * 4
            segments.append((px_off, text, color))
            px_off += len(text) * 4
        segments.append((px_off, sep, sep_color))
        px_off += len(sep) * 4
        self.notes_segments = segments
        self.notes_scroll_len = px_off

    def reset(self):
        self.time = 0.0
        self.palette_idx = 0
        self.steps_per_frame = 8
        self.f = self._f_center
        self.k = self._k_center
        self.u, self.v = _init_grid()
        self.show_notes = False
        self.notes_scroll_offset = 0.0
        self.param_overlay_timer = 0.0
        self._build_notes_segments()
        self._both_pressed_prev = False

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.up_pressed:
            self.palette_idx = (self.palette_idx + 1) % len(PALETTES)
            if self.show_notes:
                self._build_notes_segments()
            consumed = True
        if input_state.down_pressed:
            self.palette_idx = (self.palette_idx - 1) % len(PALETTES)
            if self.show_notes:
                self._build_notes_segments()
            consumed = True
        if input_state.left_pressed:
            # Decrease F, adjust k proportionally
            self.f = max(self._f_min, self.f - 0.001)
            t = (self.f - self._f_min) / max(0.001, self._f_max - self._f_min)
            self.k = self._k_min + t * (self._k_max - self._k_min)
            self.param_overlay_timer = 2.0
            consumed = True
        if input_state.right_pressed:
            # Increase F, adjust k proportionally
            self.f = min(self._f_max, self.f + 0.001)
            t = (self.f - self._f_min) / max(0.001, self._f_max - self._f_min)
            self.k = self._k_min + t * (self._k_max - self._k_min)
            self.param_overlay_timer = 2.0
            consumed = True
        # Both buttons simultaneously toggles notes
        both = input_state.action_l and input_state.action_r
        if both and not self._both_pressed_prev:
            self.show_notes = not self.show_notes
            self.notes_scroll_offset = 0.0
            if self.show_notes:
                self._build_notes_segments()
            consumed = True
        elif input_state.action_l or input_state.action_r:
            if not both:
                self.u, self.v = _init_grid()
                consumed = True
        self._both_pressed_prev = both
        return consumed

    def update(self, dt: float):
        self.time += dt
        self.u, self.v = _step_gray_scott(self.u, self.v, self.f, self.k,
                                           self.steps_per_frame)
        if self.show_notes:
            self.notes_scroll_offset += dt * 18
        if self.param_overlay_timer > 0:
            self.param_overlay_timer = max(0.0, self.param_overlay_timer - dt)

    def draw(self):
        _draw_turing(self.display, self.v, self.palette_idx)
        if self.show_notes:
            self._draw_notes()
        if self.param_overlay_timer > 0:
            self._draw_param_overlay()

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

    def _draw_param_overlay(self):
        alpha = min(1.0, self.param_overlay_timer / 0.5)
        c = (int(255 * alpha), int(255 * alpha), int(255 * alpha))
        text = "F=%.3f K=%.3f" % (self.f, self.k)
        self.display.draw_text_small(2, 2, text, c)


# ── Exported visuals ──────────────────────────────────────────────

class TuringSpots(_TuringBase):
    name = "TURING SPOTS"
    description = "Reaction-diffusion spots"
    category = "science"
    _f_center = 0.035
    _k_center = 0.065
    _f_min = 0.030
    _f_max = 0.042
    _k_min = 0.060
    _k_max = 0.070

    def _get_notes(self):
        mid = PALETTES[self.palette_idx][3]
        return [
            ("TURING SPOTS", (255, 255, 255)),
            ("GRAY-SCOTT MODEL", mid),
            ("TWO CHEMICALS REACT AND DIFFUSE", mid),
            ("F CONTROLS FEED RATE", (255, 255, 255)),
            ("K CONTROLS REMOVAL RATE", (255, 255, 255)),
            ("SAME MATH MAKES LEOPARD SPOTS", mid),
            ("ALAN TURING 1952", (255, 255, 255)),
        ]


class TuringStripes(_TuringBase):
    name = "TURING LINES"
    description = "Reaction-diffusion stripes"
    category = "science"
    _f_center = 0.025
    _k_center = 0.056
    _f_min = 0.020
    _f_max = 0.032
    _k_min = 0.050
    _k_max = 0.062

    def _get_notes(self):
        mid = PALETTES[self.palette_idx][3]
        return [
            ("TURING STRIPES", (255, 255, 255)),
            ("GRAY-SCOTT MODEL", mid),
            ("STRIPES FORM AT HIGHER FEED RATES", mid),
            ("SEEN IN ZEBRAFISH PIGMENTATION", mid),
            ("ALAN TURING 1952", (255, 255, 255)),
        ]


class TuringCoral(_TuringBase):
    name = "TURING CORAL"
    description = "Reaction-diffusion coral"
    category = "science"
    _f_center = 0.029
    _k_center = 0.057
    _f_min = 0.024
    _f_max = 0.036
    _k_min = 0.052
    _k_max = 0.063

    def _get_notes(self):
        mid = PALETTES[self.palette_idx][3]
        return [
            ("TURING CORAL", (255, 255, 255)),
            ("GRAY-SCOTT MODEL", mid),
            ("BRANCHING CORAL-LIKE GROWTH", mid),
            ("REACTION-DIFFUSION INSTABILITY", mid),
            ("ALAN TURING 1952", (255, 255, 255)),
        ]


class TuringWorms(_TuringBase):
    name = "TURING WORMS"
    description = "Reaction-diffusion worms"
    category = "science"
    _f_center = 0.078
    _k_center = 0.061
    _f_min = 0.070
    _f_max = 0.086
    _k_min = 0.055
    _k_max = 0.067

    def _get_notes(self):
        mid = PALETTES[self.palette_idx][3]
        return [
            ("TURING WORMS", (255, 255, 255)),
            ("GRAY-SCOTT MODEL", mid),
            ("WORM-LIKE LABYRINTHINE PATTERN", mid),
            ("SIMILAR TO BRAIN CORAL SURFACE", mid),
            ("ALAN TURING 1952", (255, 255, 255)),
        ]
