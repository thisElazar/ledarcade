"""
Turing - Reaction-Diffusion Patterns
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

N = GRID_SIZE


# ── Shared Gray-Scott solver ───────────────────────────────────────

def _init_grid():
    """Initialize U=1, V=0 with random seed patches of V."""
    size = N * N
    u = [1.0] * size
    v = [0.0] * size

    n_seeds = random.randint(3, 6)
    for _ in range(n_seeds):
        cx = random.randint(5, N - 6)
        cy = random.randint(5, N - 6)
        r = random.randint(2, 4)
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if dx * dx + dy * dy <= r * r:
                    x = (cx + dx) % N
                    y = (cy + dy) % N
                    idx = y * N + x
                    v[idx] = 0.5 + random.uniform(-0.05, 0.05)
                    u[idx] = 0.5 + random.uniform(-0.05, 0.05)
    return u, v


def _step_gray_scott(u, v, f, k, steps):
    """Run *steps* iterations of the Gray-Scott reaction-diffusion."""
    n = N
    du = DU
    dv = DV

    for _ in range(steps):
        new_u = [0.0] * (n * n)
        new_v = [0.0] * (n * n)

        for y in range(n):
            ym = (y - 1) % n
            yp = (y + 1) % n
            yn = y * n
            ymn = ym * n
            ypn = yp * n

            for x in range(n):
                xm = (x - 1) % n
                xp = (x + 1) % n
                idx = yn + x

                u_val = u[idx]
                v_val = v[idx]

                # 5-point Laplacian with wrapping
                lap_u = (u[yn + xm] + u[yn + xp] + u[ymn + x] + u[ypn + x]) - 4.0 * u_val
                lap_v = (v[yn + xm] + v[yn + xp] + v[ymn + x] + v[ypn + x]) - 4.0 * v_val

                uvv = u_val * v_val * v_val

                new_u[idx] = u_val + du * lap_u - uvv + f * (1.0 - u_val)
                new_v[idx] = v_val + dv * lap_v + uvv - (f + k) * v_val

        u = new_u
        v = new_v

    return u, v


def _draw_turing(display, v, palette_idx):
    """Draw V concentration through a color palette."""
    palette = PALETTES[palette_idx]
    n_colors = len(palette)
    n = N
    set_pixel = display.set_pixel

    for y in range(n):
        yn = y * n
        for x in range(n):
            val = v[yn + x]
            if val < 0.0:
                val = 0.0
            elif val > 1.0:
                val = 1.0

            idx_f = val * (n_colors - 1)
            lo = int(idx_f)
            hi = min(lo + 1, n_colors - 1)
            frac = idx_f - lo
            c0 = palette[lo]
            c1 = palette[hi]
            r = int(c0[0] + (c1[0] - c0[0]) * frac)
            g = int(c0[1] + (c1[1] - c0[1]) * frac)
            b = int(c0[2] + (c1[2] - c0[2]) * frac)
            set_pixel(x, y, (r, g, b))


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

    def reset(self):
        self.time = 0.0
        self.palette_idx = 0
        self.steps_per_frame = 8
        self.f = self._f_center
        self.k = self._k_center
        self.u, self.v = _init_grid()

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.up_pressed:
            self.palette_idx = (self.palette_idx + 1) % len(PALETTES)
            consumed = True
        if input_state.down_pressed:
            self.palette_idx = (self.palette_idx - 1) % len(PALETTES)
            consumed = True
        if input_state.left_pressed:
            # Decrease F, adjust k proportionally
            self.f = max(self._f_min, self.f - 0.001)
            t = (self.f - self._f_min) / max(0.001, self._f_max - self._f_min)
            self.k = self._k_min + t * (self._k_max - self._k_min)
            consumed = True
        if input_state.right_pressed:
            # Increase F, adjust k proportionally
            self.f = min(self._f_max, self.f + 0.001)
            t = (self.f - self._f_min) / max(0.001, self._f_max - self._f_min)
            self.k = self._k_min + t * (self._k_max - self._k_min)
            consumed = True
        if input_state.action_l or input_state.action_r:
            self.u, self.v = _init_grid()
            consumed = True
        return consumed

    def update(self, dt: float):
        self.time += dt
        self.u, self.v = _step_gray_scott(self.u, self.v, self.f, self.k,
                                           self.steps_per_frame)

    def draw(self):
        _draw_turing(self.display, self.v, self.palette_idx)


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
