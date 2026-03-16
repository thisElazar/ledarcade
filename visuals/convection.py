"""
Convection - Rayleigh-Benard Convection Cells
==============================================
Heat at bottom, cool at top. Below a critical temperature difference:
pure conduction (linear gradient, no motion). Above it: spontaneous
symmetry breaking as convection rolls self-organise into beautiful
rolling cells.

Built on the Stam stable-fluids solver from fluid.py.

Controls:
  Left/Right  - Temperature gradient (Rayleigh number)
  Up/Down     - Cycle viz mode (TEMP / FLOW / BOTH)
  Space       - Perturb (inject random temperature blobs)
"""

import math
import numpy as np
from . import Visual, Display, Colors, GRID_SIZE
from .fluid import (
    _new_field, _set_bnd, _diffuse, _advect, _project,
    _velocity_step, _density_step, N as FLUID_N, S as FLUID_S,
)


# ── Color mapping: temperature -> RGB ────────────────────────────
# Piecewise-linear ramp through 5 stops
_COLOR_STOPS = [
    (0.00, (10, 20, 60)),       # cold: dark blue
    (0.25, (30, 60, 180)),      # cool: blue
    (0.50, (180, 40, 120)),     # warm: magenta
    (0.75, (255, 140, 30)),     # hot: orange
    (1.00, (255, 240, 100)),    # very hot: bright yellow
]

def _temp_color(t):
    """Map temperature 0..1 to (r, g, b)."""
    t = max(0.0, min(1.0, t))
    for i in range(len(_COLOR_STOPS) - 1):
        t0, c0 = _COLOR_STOPS[i]
        t1, c1 = _COLOR_STOPS[i + 1]
        if t <= t1:
            f = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
            return (
                int(c0[0] + (c1[0] - c0[0]) * f),
                int(c0[1] + (c1[1] - c0[1]) * f),
                int(c0[2] + (c1[2] - c0[2]) * f),
            )
    return _COLOR_STOPS[-1][1]


# Precompute a 256-entry LUT for fast drawing
_COLOR_LUT = [_temp_color(i / 255.0) for i in range(256)]


def _flow_color(vx, vy, mag):
    """Map velocity direction + magnitude to color — fast, no trig."""
    if mag < 0.001:
        return (5, 5, 10)
    b = min(1.0, mag * 3.0)
    # Direction via normalized components (avoids atan2)
    inv = b / mag
    nx = vx * inv   # -b..+b
    ny = vy * inv
    # R: rightward, B: leftward, G: upward/downward
    r = max(0.0, nx)
    bl = max(0.0, -nx)
    g = abs(ny) * 0.7
    return (int(r * 255), int(g * 255), int(bl * 255))


VIZ_MODES = ["TEMP", "FLOW", "BOTH"]


class Convection(Visual):
    name = "CONVECTION"
    description = "Rayleigh-Benard cells"
    category = "science_bench"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.temp_gradient = 0.8
        self.viz_mode = 0  # 0=TEMP, 1=FLOW, 2=BOTH

        # Overlay
        self.overlay_timer = 0.0
        self.overlay_lines = []

        # Use fluid solver's padded grid (S x S where S = N + 2 = 66)
        self.u = _new_field()      # x-velocity
        self.v = _new_field()      # y-velocity
        self.u0 = _new_field()     # scratch x-velocity
        self.v0 = _new_field()     # scratch y-velocity
        self.T = _new_field()      # temperature
        self.T0 = _new_field()     # scratch temperature

        # Scratch buffers for pressure projection
        self.p = _new_field()
        self.div = _new_field()

        # Initialize temperature: linear gradient + tiny perturbation
        N = FLUID_N
        for i in range(1, N + 1):
            for j in range(1, N + 1):
                # j=1 is top (cold), j=N is bottom (hot)
                base = j / float(N)
                self.T[i, j] = base + np.random.uniform(-0.002, 0.002)

        # Step timing - 10Hz physics
        self.step_timer = 0.0
        self.step_interval = 0.1

    # ── Input ────────────────────────────────────────────────────
    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.right:
            self.temp_gradient = min(2.0, self.temp_gradient + 0.02)
            self.overlay_timer = 2.0
            ra = self._rayleigh()
            self.overlay_lines = [f"dT {ra:.1f}"]
            consumed = True
        if input_state.left:
            self.temp_gradient = max(0.2, self.temp_gradient - 0.02)
            self.overlay_timer = 2.0
            ra = self._rayleigh()
            self.overlay_lines = [f"dT {ra:.1f}"]
            consumed = True

        if input_state.up_pressed:
            self.viz_mode = (self.viz_mode + 1) % len(VIZ_MODES)
            self.overlay_timer = 2.0
            self.overlay_lines = [VIZ_MODES[self.viz_mode]]
            consumed = True
        if input_state.down_pressed:
            self.viz_mode = (self.viz_mode - 1) % len(VIZ_MODES)
            self.overlay_timer = 2.0
            self.overlay_lines = [VIZ_MODES[self.viz_mode]]
            consumed = True

        if input_state.action_l or input_state.action_r:
            self._perturb()
            self.overlay_timer = 2.0
            self.overlay_lines = ["PERTURB"]
            consumed = True

        return consumed

    # ── Helpers ───────────────────────────────────────────────────
    def _rayleigh(self):
        """Effective Rayleigh number (simplified, for display)."""
        return self.temp_gradient * 10.0

    def _perturb(self):
        """Inject random temperature blobs to disrupt the flow."""
        N = FLUID_N
        for _ in range(8):
            ci = np.random.randint(5, N - 4)
            cj = np.random.randint(5, N - 4)
            r = np.random.randint(2, 4)
            hot = np.random.random() > 0.5
            for di in range(-r, r + 1):
                for dj in range(-r, r + 1):
                    d2 = di * di + dj * dj
                    if d2 <= r * r:
                        pi, pj = ci + di, cj + dj
                        if 1 <= pi <= N and 1 <= pj <= N:
                            strength = 1.0 - math.sqrt(d2) / r
                            if hot:
                                self.T[pi, pj] = min(1.0, self.T[pi, pj] + 0.4 * strength)
                            else:
                                self.T[pi, pj] = max(0.0, self.T[pi, pj] - 0.4 * strength)

    # ── Physics step ─────────────────────────────────────────────
    def _step(self):
        N = FLUID_N
        T = self.T
        u = self.u
        v = self.v
        u0 = self.u0
        v0 = self.v0
        T0 = self.T0
        grad = self.temp_gradient

        dt = 0.1  # physics timestep
        viscosity = 0.0001
        temp_diffusion = 0.0002

        # Effective Rayleigh number and buoyancy
        Ra = grad * 10.0
        # Critical Ra ~ 5.0 (gradient ~ 0.5)
        buoyancy = max(0.0, (Ra - 5.0) * 0.08) if Ra > 5.0 else 0.0

        # --- Apply buoyancy force (VERTICAL ONLY) ---
        # Hot fluid rises: negative v because j increases downward in display
        T_mean = np.mean(T[1:N+1, 1:N+1])
        v[1:N+1, 1:N+1] += -buoyancy * (T[1:N+1, 1:N+1] - T_mean) * dt

        # --- Velocity step (Stam solver: diffuse, project, advect, project) ---
        _velocity_step(u, v, u0, v0, viscosity, dt)

        # --- Temperature advection and diffusion ---
        T0[:] = T
        _advect(0, T, T0, u, v, dt)
        T0[:] = T
        _diffuse(0, T, T0, temp_diffusion, dt)

        # --- Boundary conditions for temperature ---
        # Bottom hot, top cold (scaled by gradient)
        bot_T = min(1.0, 0.5 + grad * 0.25)
        top_T = max(0.0, 0.5 - grad * 0.25)
        T[1:N+1, N] = bot_T      # Bottom row
        T[1:N+1, 1] = top_T      # Top row

        # Clamp temperature
        np.clip(T, 0.0, 1.0, out=T)

    # ── Update ───────────────────────────────────────────────────
    def update(self, dt: float):
        self.time += dt

        if self.overlay_timer > 0:
            self.overlay_timer -= dt

        self.step_timer += dt
        while self.step_timer >= self.step_interval:
            self.step_timer -= self.step_interval
            self._step()

    # ── Draw (1:1 from 64x64 solver to 64x64 display) ───────────
    def draw(self):
        d = self.display
        set_pixel = d.set_pixel
        T = self.T
        u = self.u
        v = self.v
        mode = self.viz_mode
        lut = _COLOR_LUT
        N = FLUID_N
        _sqrt = math.sqrt

        if mode == 0:
            # TEMP mode: pure temperature field
            for px in range(N):
                for py in range(N):
                    val = T[px + 1, py + 1]
                    idx = int(val * 255)
                    idx = max(0, min(255, idx))
                    set_pixel(px, py, lut[idx])

        elif mode == 1:
            # FLOW mode: velocity direction + magnitude
            _fc = _flow_color
            for px in range(N):
                for py in range(N):
                    uvx = u[px + 1, py + 1]
                    uvy = v[px + 1, py + 1]
                    mag = _sqrt(uvx * uvx + uvy * uvy)
                    set_pixel(px, py, _fc(uvx, uvy, mag))

        else:
            # BOTH mode: temperature + velocity dots
            for px in range(N):
                for py in range(N):
                    val = T[px + 1, py + 1]
                    idx = int(val * 255)
                    idx = max(0, min(255, idx))
                    set_pixel(px, py, lut[idx])

            # Velocity dots on sparse grid
            for si in range(2, N, 4):
                for sj in range(2, N, 4):
                    uvx = u[si + 1, sj + 1]
                    uvy = v[si + 1, sj + 1]
                    mag = _sqrt(uvx * uvx + uvy * uvy)
                    if mag > 0.05:
                        norm = min(2.5, mag * 4.0) / mag
                        ex = int(si + uvx * norm * 2 + 0.5)
                        ey = int(sj + uvy * norm * 2 + 0.5)
                        if 0 <= ex < N and 0 <= ey < N:
                            set_pixel(ex, ey, (255, 255, 255))

        # HUD overlay
        if self.overlay_timer > 0 and self.overlay_lines:
            alpha = min(1.0, self.overlay_timer / 0.5)
            for i, line in enumerate(self.overlay_lines):
                cr = int(255 * alpha)
                cg = int(255 * alpha)
                cb = int(200 * alpha)
                d.draw_text_small(2, 2 + i * 8, line, (cr, cg, cb))
