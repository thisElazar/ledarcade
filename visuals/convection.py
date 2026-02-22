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

N = GRID_SIZE  # 64


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
    """Map velocity direction + magnitude to color."""
    if mag < 0.001:
        return (5, 5, 10)
    angle = math.atan2(vy, vx)
    # Hue from angle, brightness from magnitude
    h = (angle / (2 * math.pi)) % 1.0
    b = min(1.0, mag * 3.0)
    # Simple HSV->RGB with S=1
    i = int(h * 6) % 6
    f = h * 6 - int(h * 6)
    vals = [
        (1, f, 0), (1 - f, 1, 0), (0, 1, f),
        (0, 1 - f, 1), (f, 0, 1), (1, 0, 1 - f),
    ]
    r, g, bl = vals[i]
    return (int(r * b * 255), int(g * b * 255), int(bl * b * 255))


VIZ_MODES = ["TEMP", "FLOW", "BOTH"]


class Convection(Visual):
    name = "CONVECTION"
    description = "Rayleigh-Benard cells"
    category = "simulation"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

        # Temperature gradient control  (maps to Rayleigh number)
        self.temp_gradient = 0.8
        self.viz_mode = 0  # 0=TEMP, 1=FLOW, 2=BOTH

        # Overlay
        self.overlay_timer = 0.0
        self.overlay_lines = []

        # Physics fields
        # T[y][x], vx[y][x], vy[y][x]
        self.T = [[0.0] * N for _ in range(N)]
        self.vx = [[0.0] * N for _ in range(N)]
        self.vy = [[0.0] * N for _ in range(N)]

        # Initialize temperature: linear gradient + tiny perturbation
        for y in range(N):
            base = 1.0 - y / (N - 1)  # 1.0 at bottom (y=63), 0.0 at top
            for x in range(N):
                self.T[y][x] = base + random.uniform(-0.002, 0.002)

        # Step timing
        self.step_timer = 0.0
        self.step_interval = 0.02

        # Scratch buffers
        self._Tnew = [[0.0] * N for _ in range(N)]

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
        for _ in range(8):
            cx = random.randint(8, N - 9)
            cy = random.randint(8, N - 9)
            r = random.randint(3, 7)
            hot = random.random() > 0.5
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    dist2 = dx * dx + dy * dy
                    if dist2 <= r * r:
                        px = cx + dx
                        py = cy + dy
                        if 0 <= px < N and 0 <= py < N:
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
        # Temperature anomaly relative to horizontal mean drives circulation
        # Compute row means for anomaly
        row_mean = [0.0] * N
        for y in range(N):
            s = 0.0
            for x in range(N):
                s += T[y][x]
            row_mean[y] = s / N

        for y in range(1, N - 1):
            for x in range(N):
                # Temperature anomaly (deviation from horizontal mean)
                anomaly = T[y][x] - row_mean[y]
                # Buoyancy: hot anomaly -> upward (negative vy in screen coords)
                vy[y][x] += -buoyancy * anomaly * dt_phys
                # Horizontal pressure-like term: fluid pushed sideways
                # by convergence/divergence
                xl = T[y][(x - 1) % N]
                xr = T[y][(x + 1) % N]
                vx[y][x] += buoyancy * 0.3 * (xr - xl) * dt_phys

        # --- Velocity diffusion + damping ---
        for y in range(1, N - 1):
            for x in range(N):
                xl = (x - 1) % N
                xr = (x + 1) % N
                # Diffuse velocity
                vx[y][x] += vel_diff * (
                    vx[y - 1][x] + vx[y + 1][x] +
                    vx[y][xl] + vx[y][xr] - 4 * vx[y][x]
                )
                vy[y][x] += vel_diff * (
                    vy[y - 1][x] + vy[y + 1][x] +
                    vy[y][xl] + vy[y][xr] - 4 * vy[y][x]
                )
                # Damp
                vx[y][x] *= visc_damp
                vy[y][x] *= visc_damp

        # Top/bottom boundaries: no vertical velocity
        for x in range(N):
            vy[0][x] = 0.0
            vy[N - 1][x] = 0.0
            vx[0][x] *= 0.5
            vx[N - 1][x] *= 0.5

        # --- Enforce incompressibility (simple pressure projection) ---
        # A few relaxation iterations to reduce divergence
        for _ in range(3):
            for y in range(1, N - 1):
                for x in range(N):
                    xl = (x - 1) % N
                    xr = (x + 1) % N
                    div = (vx[y][xr] - vx[y][xl] + vy[y + 1][x] - vy[y - 1][x]) * 0.5
                    # Push back
                    vx[y][xr] -= div * 0.25
                    vx[y][xl] += div * 0.25
                    vy[y + 1][x] -= div * 0.25
                    vy[y - 1][x] += div * 0.25

        # --- Advect temperature (semi-Lagrangian, with diffusion) ---
        for y in range(N):
            for x in range(N):
                # Backtrace
                sx = x - vx[y][x] * dt_phys
                sy = y - vy[y][x] * dt_phys
                # Wrap horizontally, clamp vertically
                sx = sx % N
                sy = max(0.0, min(N - 1.001, sy))
                # Bilinear interpolation
                ix = int(sx)
                iy = int(sy)
                fx = sx - ix
                fy = sy - iy
                ix2 = (ix + 1) % N
                iy2 = min(iy + 1, N - 1)
                Tn[y][x] = (
                    T[iy][ix] * (1 - fx) * (1 - fy) +
                    T[iy][ix2] * fx * (1 - fy) +
                    T[iy2][ix] * (1 - fx) * fy +
                    T[iy2][ix2] * fx * fy
                )

        # --- Thermal diffusion ---
        for y in range(1, N - 1):
            for x in range(N):
                xl = (x - 1) % N
                xr = (x + 1) % N
                lap = (
                    Tn[y - 1][x] + Tn[y + 1][x] +
                    Tn[y][xl] + Tn[y][xr] - 4 * Tn[y][x]
                )
                Tn[y][x] += kappa * lap

        # --- Boundary conditions ---
        # Bottom heated, top cooled, scaled by gradient
        bot_T = min(1.0, 0.5 + grad * 0.25)
        top_T = max(0.0, 0.5 - grad * 0.25)
        for x in range(N):
            Tn[N - 1][x] = bot_T
            Tn[0][x] = top_T

        # Clamp
        for y in range(N):
            for x in range(N):
                Tn[y][x] = max(0.0, min(1.0, Tn[y][x]))

        # Swap
        self.T, self._Tnew = Tn, self.T

    # ── Update ───────────────────────────────────────────────────
    def update(self, dt: float):
        self.time += dt

        if self.overlay_timer > 0:
            self.overlay_timer -= dt

        self.step_timer += dt
        # Run multiple sub-steps per frame for responsiveness
        while self.step_timer >= self.step_interval:
            self.step_timer -= self.step_interval
            self._step()

    # ── Draw ─────────────────────────────────────────────────────
    def draw(self):
        self.display.clear()
        set_pixel = self.display.set_pixel
        T = self.T
        vx = self.vx
        vy = self.vy
        mode = self.viz_mode
        lut = _COLOR_LUT

        if mode == 0:
            # TEMP mode: pure temperature field
            for y in range(N):
                row = T[y]
                for x in range(N):
                    idx = int(row[x] * 255)
                    if idx < 0:
                        idx = 0
                    elif idx > 255:
                        idx = 255
                    set_pixel(x, y, lut[idx])

        elif mode == 1:
            # FLOW mode: velocity direction + magnitude
            for y in range(N):
                for x in range(N):
                    uvx = vx[y][x]
                    uvy = vy[y][x]
                    mag = math.sqrt(uvx * uvx + uvy * uvy)
                    set_pixel(x, y, _flow_color(uvx, uvy, mag))

        else:
            # BOTH mode: temperature with velocity streamline dots
            for y in range(N):
                row = T[y]
                for x in range(N):
                    idx = int(row[x] * 255)
                    if idx < 0:
                        idx = 0
                    elif idx > 255:
                        idx = 255
                    set_pixel(x, y, lut[idx])

            # Overlay velocity as bright dots on a sparse grid
            for y in range(2, N, 4):
                for x in range(2, N, 4):
                    uvx = vx[y][x]
                    uvy = vy[y][x]
                    mag = math.sqrt(uvx * uvx + uvy * uvy)
                    if mag > 0.05:
                        # Draw a small line segment in velocity direction
                        norm = min(2.5, mag * 4.0) / mag
                        ex = int(round(x + uvx * norm))
                        ey = int(round(y + uvy * norm))
                        if 0 <= ex < N and 0 <= ey < N:
                            set_pixel(ex, ey, (255, 255, 255))

        # HUD overlay
        if self.overlay_timer > 0 and self.overlay_lines:
            alpha = min(1.0, self.overlay_timer / 0.5)
            for i, line in enumerate(self.overlay_lines):
                cr = int(255 * alpha)
                cg = int(255 * alpha)
                cb = int(200 * alpha)
                self.display.draw_text_small(2, 2 + i * 8, line, (cr, cg, cb))
