"""
Convection - Rayleigh-Benard Convection Cells
==============================================
Heat at bottom, cool at top. Below a critical temperature difference:
pure conduction (linear gradient, no motion). Above it: spontaneous
symmetry breaking as convection rolls self-organise into beautiful
rolling cells.

Controls:
  Left/Right  - Temperature gradient (Rayleigh number)
  Up/Down     - Cycle viz mode (TEMP / FLOW / BOTH)
  Space       - Perturb (inject random temperature blobs)
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE

N_SIM = 32          # internal simulation grid
N_DISP = GRID_SIZE  # 64 - display grid
SCALE = N_DISP // N_SIM  # 2x upscale


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
    category = "science"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        S = N_SIM

        # Temperature gradient control  (maps to Rayleigh number)
        self.temp_gradient = 0.8
        self.viz_mode = 0  # 0=TEMP, 1=FLOW, 2=BOTH

        # Overlay
        self.overlay_timer = 0.0
        self.overlay_lines = []

        # Physics fields on the smaller sim grid
        # T[y][x], vx[y][x], vy[y][x]
        self.T = [[0.0] * S for _ in range(S)]
        self.vx = [[0.0] * S for _ in range(S)]
        self.vy = [[0.0] * S for _ in range(S)]

        # Initialize temperature: linear gradient + tiny perturbation
        for y in range(S):
            base = 1.0 - y / (S - 1)  # 1.0 at bottom, 0.0 at top
            for x in range(S):
                self.T[y][x] = base + random.uniform(-0.002, 0.002)

        # Step timing - 10Hz for Pi performance
        self.step_timer = 0.0
        self.step_interval = 0.1

        # Scratch buffers
        self._Tnew = [[0.0] * S for _ in range(S)]

    # ── Input ────────────────────────────────────────────────────
    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.right:
            self.temp_gradient = min(2.0, self.temp_gradient + 0.02)
            self.overlay_timer = 2.0
            ra = self._rayleigh()
            self.overlay_lines = [f"Ra {ra:.1f}"]
            consumed = True
        if input_state.left:
            self.temp_gradient = max(0.2, self.temp_gradient - 0.02)
            self.overlay_timer = 2.0
            ra = self._rayleigh()
            self.overlay_lines = [f"Ra {ra:.1f}"]
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
        S = N_SIM
        for _ in range(8):
            cx = random.randint(4, S - 5)
            cy = random.randint(4, S - 5)
            r = random.randint(2, 4)
            hot = random.random() > 0.5
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    dist2 = dx * dx + dy * dy
                    if dist2 <= r * r:
                        px = cx + dx
                        py = cy + dy
                        if 0 <= px < S and 0 <= py < S:
                            strength = 1.0 - math.sqrt(dist2) / r
                            if hot:
                                self.T[py][px] = min(1.0, self.T[py][px] + 0.4 * strength)
                            else:
                                self.T[py][px] = max(0.0, self.T[py][px] - 0.4 * strength)

    # ── Physics step ─────────────────────────────────────────────
    def _step(self):
        T = self.T
        vx = self.vx
        vy = self.vy
        Tn = self._Tnew
        grad = self.temp_gradient
        S = N_SIM
        S1 = S - 1

        # Effective Rayleigh number determines buoyancy strength
        Ra = grad * 10.0
        # Critical Ra ~ 5.0 (gradient ~ 0.5)
        buoyancy = max(0.0, (Ra - 5.0) * 0.06) if Ra > 5.0 else 0.0

        # Thermal diffusivity
        kappa = 0.15
        # Viscosity (velocity damping)
        visc_damp = 0.92
        # Velocity diffusion
        vel_diff = 0.08

        dt_phys = 0.5  # sub-timestep scaling

        # --- Update velocity from buoyancy ---
        # Compute row means for anomaly
        row_mean = [0.0] * S
        for y in range(S):
            s = 0.0
            row = T[y]
            for x in range(S):
                s += row[x]
            row_mean[y] = s / S

        for y in range(1, S1):
            Ty = T[y]
            vxy = vx[y]
            vyy = vy[y]
            rm = row_mean[y]
            for x in range(S):
                anomaly = Ty[x] - rm
                vyy[x] += -buoyancy * anomaly * dt_phys
                xl = Ty[(x - 1) % S]
                xr = Ty[(x + 1) % S]
                vxy[x] += buoyancy * 0.3 * (xr - xl) * dt_phys

        # --- Velocity diffusion + damping ---
        for y in range(1, S1):
            vxy = vx[y]
            vyy = vy[y]
            vx_ym1 = vx[y - 1]
            vx_yp1 = vx[y + 1]
            vy_ym1 = vy[y - 1]
            vy_yp1 = vy[y + 1]
            for x in range(S):
                xl = (x - 1) % S
                xr = (x + 1) % S
                vxy[x] += vel_diff * (
                    vx_ym1[x] + vx_yp1[x] +
                    vxy[xl] + vxy[xr] - 4 * vxy[x]
                )
                vyy[x] += vel_diff * (
                    vy_ym1[x] + vy_yp1[x] +
                    vyy[xl] + vyy[xr] - 4 * vyy[x]
                )
                vxy[x] *= visc_damp
                vyy[x] *= visc_damp

        # Top/bottom boundaries: no vertical velocity
        for x in range(S):
            vy[0][x] = 0.0
            vy[S1][x] = 0.0
            vx[0][x] *= 0.5
            vx[S1][x] *= 0.5

        # --- Enforce incompressibility (single relaxation iteration) ---
        for y in range(1, S1):
            vxy = vx[y]
            vyy_p1 = vy[y + 1]
            vyy_m1 = vy[y - 1]
            for x in range(S):
                xl = (x - 1) % S
                xr = (x + 1) % S
                div = (vxy[xr] - vxy[xl] + vyy_p1[x] - vyy_m1[x]) * 0.5
                vxy[xr] -= div * 0.25
                vxy[xl] += div * 0.25
                vyy_p1[x] -= div * 0.25
                vyy_m1[x] += div * 0.25

        # --- Advect temperature (semi-Lagrangian, with diffusion) ---
        for y in range(S):
            vxy = vx[y]
            vyy = vy[y]
            Tny = Tn[y]
            for x in range(S):
                # Backtrace
                sx = x - vxy[x] * dt_phys
                sy = y - vyy[x] * dt_phys
                # Wrap horizontally, clamp vertically
                sx = sx % S
                sy = max(0.0, min(S - 1.001, sy))
                # Bilinear interpolation
                ix = int(sx)
                iy = int(sy)
                fx = sx - ix
                fy = sy - iy
                ix2 = (ix + 1) % S
                iy2 = min(iy + 1, S1)
                Tny[x] = (
                    T[iy][ix] * (1 - fx) * (1 - fy) +
                    T[iy][ix2] * fx * (1 - fy) +
                    T[iy2][ix] * (1 - fx) * fy +
                    T[iy2][ix2] * fx * fy
                )

        # --- Thermal diffusion ---
        for y in range(1, S1):
            Tny = Tn[y]
            Tn_ym1 = Tn[y - 1]
            Tn_yp1 = Tn[y + 1]
            for x in range(S):
                xl = (x - 1) % S
                xr = (x + 1) % S
                lap = (
                    Tn_ym1[x] + Tn_yp1[x] +
                    Tny[xl] + Tny[xr] - 4 * Tny[x]
                )
                Tny[x] += kappa * lap

        # --- Boundary conditions ---
        # Bottom heated, top cooled, scaled by gradient
        bot_T = min(1.0, 0.5 + grad * 0.25)
        top_T = max(0.0, 0.5 - grad * 0.25)
        for x in range(S):
            Tn[S1][x] = bot_T
            Tn[0][x] = top_T

        # Clamp
        for y in range(S):
            Tny = Tn[y]
            for x in range(S):
                v = Tny[x]
                if v < 0.0:
                    Tny[x] = 0.0
                elif v > 1.0:
                    Tny[x] = 1.0

        # Swap
        self.T, self._Tnew = Tn, self.T

    # ── Update ───────────────────────────────────────────────────
    def update(self, dt: float):
        self.time += dt

        if self.overlay_timer > 0:
            self.overlay_timer -= dt

        self.step_timer += dt
        while self.step_timer >= self.step_interval:
            self.step_timer -= self.step_interval
            self._step()

    # ── Draw (upscale 2x from 32x32 sim to 64x64 display) ───────
    def draw(self):
        # No clear() needed — we fill every pixel via 2x upscale
        set_pixel = self.display.set_pixel
        T = self.T
        vx = self.vx
        vy = self.vy
        mode = self.viz_mode
        lut = _COLOR_LUT
        S = N_SIM
        _sqrt = math.sqrt

        if mode == 0:
            # TEMP mode: pure temperature field
            for sy in range(S):
                row = T[sy]
                dy = sy * 2
                dy1 = dy + 1
                for sx in range(S):
                    idx = int(row[sx] * 255)
                    if idx < 0:
                        idx = 0
                    elif idx > 255:
                        idx = 255
                    c = lut[idx]
                    dx = sx * 2
                    set_pixel(dx, dy, c)
                    set_pixel(dx + 1, dy, c)
                    set_pixel(dx, dy1, c)
                    set_pixel(dx + 1, dy1, c)

        elif mode == 1:
            # FLOW mode: velocity direction + magnitude (trig-free)
            _fc = _flow_color
            for sy in range(S):
                vx_row = vx[sy]
                vy_row = vy[sy]
                dy = sy * 2
                dy1 = dy + 1
                for sx in range(S):
                    uvx = vx_row[sx]
                    uvy = vy_row[sx]
                    mag = _sqrt(uvx * uvx + uvy * uvy)
                    c = _fc(uvx, uvy, mag)
                    dx = sx * 2
                    set_pixel(dx, dy, c)
                    set_pixel(dx + 1, dy, c)
                    set_pixel(dx, dy1, c)
                    set_pixel(dx + 1, dy1, c)

        else:
            # BOTH mode: temperature with velocity streamline dots
            for sy in range(S):
                row = T[sy]
                dy = sy * 2
                dy1 = dy + 1
                for sx in range(S):
                    idx = int(row[sx] * 255)
                    if idx < 0:
                        idx = 0
                    elif idx > 255:
                        idx = 255
                    c = lut[idx]
                    dx = sx * 2
                    set_pixel(dx, dy, c)
                    set_pixel(dx + 1, dy, c)
                    set_pixel(dx, dy1, c)
                    set_pixel(dx + 1, dy1, c)

            # Overlay velocity as bright dots on a sparse grid
            for sy in range(1, S, 3):
                for sx in range(1, S, 3):
                    uvx = vx[sy][sx]
                    uvy = vy[sy][sx]
                    mag = _sqrt(uvx * uvx + uvy * uvy)
                    if mag > 0.05:
                        norm = min(2.5, mag * 4.0) / mag
                        ex = int(sx * 2 + uvx * norm * 2 + 0.5)
                        ey = int(sy * 2 + uvy * norm * 2 + 0.5)
                        if 0 <= ex < N_DISP and 0 <= ey < N_DISP:
                            set_pixel(ex, ey, (255, 255, 255))

        # HUD overlay
        if self.overlay_timer > 0 and self.overlay_lines:
            alpha = min(1.0, self.overlay_timer / 0.5)
            for i, line in enumerate(self.overlay_lines):
                cr = int(255 * alpha)
                cg = int(255 * alpha)
                cb = int(200 * alpha)
                self.display.draw_text_small(2, 2 + i * 8, line, (cr, cg, cb))
