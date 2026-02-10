"""
Wave Tank - 2D Wave Equation Simulation
========================================
Simulates the 2D wave equation on a 64x64 grid using leapfrog integration.
Five scenarios demonstrate fundamental wave phenomena: point sources,
double-slit diffraction, two-source interference, rain ripples, and
reflection off angled barriers.

Controls:
  Left/Right     - Adjust simulation speed
  Up/Down        - Cycle visual style (view mode + palette)
  Single button  - Cycle scenario
  Both buttons   - Toggle scrolling notes
"""

import math
import random
import numpy as np
from . import Visual, Display, Colors, GRID_SIZE

# ── Grid size ────────────────────────────────────────────────────
N = GRID_SIZE  # 64

# ── Wave equation parameters ─────────────────────────────────────
C = 0.25           # Wave speed (must keep c*dt/dx < 1 for stability)
DAMPING = 0.9995   # Per-substep damping to prevent blowup
SUB_STEPS = 16     # Physics substeps per frame
DT_SUB = 0.25      # Substep dt (unitless, tuned with C)

# ── Scenarios ────────────────────────────────────────────────────
_SCENARIOS = ['SINGLE SOURCE', 'DOUBLE SLIT', 'INTERFERENCE', 'RIPPLE', 'REFLECTION']

# ── View modes ───────────────────────────────────────────────────
_VIEW_MODES = ['WAVES', 'ENERGY']

# ── Palettes ─────────────────────────────────────────────────────
# Each palette: (neg_color, zero_color, pos_color) for bipolar,
# and a single ramp for energy mode.
PALETTES = [
    {
        'name': 'OCEAN',
        'neg': (0, 80, 255),    'zero': (0, 0, 0),    'pos': (255, 255, 255),
        'energy': (0, 100, 255),
    },
    {
        'name': 'THERMAL',
        'neg': (0, 50, 255),    'zero': (0, 0, 0),    'pos': (255, 30, 0),
        'energy': (255, 60, 0),
    },
    {
        'name': 'NEON',
        'neg': (0, 255, 255),   'zero': (0, 0, 0),    'pos': (255, 0, 255),
        'energy': (255, 0, 255),
    },
    {
        'name': 'FIRE',
        'neg': (0, 10, 80),     'zero': (0, 0, 0),    'pos': (255, 160, 0),
        'energy': (255, 180, 0),
    },
    {
        'name': 'MONO',
        'neg': (60, 60, 60),    'zero': (0, 0, 0),    'pos': (255, 255, 255),
        'energy': (255, 255, 255),
    },
]

# Wall color
WALL_COLOR = (40, 40, 45)


# ── Color mapping helpers ────────────────────────────────────────

def _bipolar_color(val, pal):
    """Map a value in [-1, 1] to a color using the palette's neg/zero/pos."""
    val = max(-1.0, min(1.0, val))
    if val >= 0:
        t = val
        r = int(pal['zero'][0] + (pal['pos'][0] - pal['zero'][0]) * t)
        g = int(pal['zero'][1] + (pal['pos'][1] - pal['zero'][1]) * t)
        b = int(pal['zero'][2] + (pal['pos'][2] - pal['zero'][2]) * t)
    else:
        t = -val
        r = int(pal['zero'][0] + (pal['neg'][0] - pal['zero'][0]) * t)
        g = int(pal['zero'][1] + (pal['neg'][1] - pal['zero'][1]) * t)
        b = int(pal['zero'][2] + (pal['neg'][2] - pal['zero'][2]) * t)
    return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))


def _energy_color(val, pal):
    """Map energy value in [0, 1] to a single-ramp color."""
    t = max(0.0, min(1.0, val))
    ec = pal['energy']
    r = int(ec[0] * t)
    g = int(ec[1] * t)
    b = int(ec[2] * t)
    return (r, g, b)


# ── WaveTank visual ─────────────────────────────────────────────

class WaveTank(Visual):
    name = "WAVE TANK"
    description = "2D wave equation simulation"
    category = "science"

    def __init__(self, display: Display):
        super().__init__(display)

    # ── notes ────────────────────────────────────────────────────

    def _get_notes(self):
        return [
            ("WAVE EQUATION", (255, 255, 255)),
            ("AMPLITUDE TRAVELS AS RIPPLES", (150, 200, 255)),
            ("TWO SLITS CREATE INTERFERENCE", (150, 200, 255)),
            ("WAVES REFLECT OFF BARRIERS", (150, 200, 255)),
            ("CHRISTIAAN HUYGENS 1678", (255, 255, 255)),
        ]

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

    # ── overlay ──────────────────────────────────────────────────

    def _draw_overlay(self):
        if self.overlay_timer <= 0:
            return
        alpha = min(1.0, self.overlay_timer / 0.5)
        c = (int(255 * alpha), int(255 * alpha), int(255 * alpha))
        self.display.draw_text_small(2, 2, self.overlay_text, c)

    def _show_overlay(self, text):
        self.overlay_text = text
        self.overlay_timer = 2.0

    # ── scenario setup ───────────────────────────────────────────

    def reset(self):
        self.time = 0.0
        self.scenario_idx = 0
        self.palette_idx = 0
        self.view_mode = 0  # 0=waves, 1=energy
        self.style_idx = 0  # combined view_mode * num_palettes + palette_idx
        self.speed = 1.0    # simulation speed multiplier

        # Wave arrays
        self.u = np.zeros((N, N), dtype=np.float64)
        self.u_prev = np.zeros((N, N), dtype=np.float64)
        self.u_next = np.zeros((N, N), dtype=np.float64)

        # Wall mask
        self.walls = np.zeros((N, N), dtype=bool)

        # Sources
        self.sources = []

        # Ripple scenario state
        self.ripple_timer = 0.0

        # Overlay
        self.overlay_text = ''
        self.overlay_timer = 0.0

        # Notes
        self.show_notes = False
        self.notes_scroll_offset = 0.0
        self.notes_segments = []
        self.notes_scroll_len = 1
        self._both_pressed_prev = False
        self._build_notes_segments()

        # Physics time accumulator
        self.phys_time = 0.0

        self._setup_scenario()

    def _setup_scenario(self):
        """Configure walls and sources for the current scenario."""
        self.u[:] = 0.0
        self.u_prev[:] = 0.0
        self.u_next[:] = 0.0
        self.walls[:] = False
        self.sources = []
        self.phys_time = 0.0
        self.ripple_timer = 0.0

        scenario = _SCENARIOS[self.scenario_idx]

        if scenario == 'SINGLE SOURCE':
            self._setup_single_source()
        elif scenario == 'DOUBLE SLIT':
            self._setup_double_slit()
        elif scenario == 'INTERFERENCE':
            self._setup_interference()
        elif scenario == 'RIPPLE':
            self._setup_ripple()
        elif scenario == 'REFLECTION':
            self._setup_reflection()

    def _setup_single_source(self):
        """One oscillating point source at center-left."""
        self.sources.append({
            'x': 16, 'y': 32, 'freq': 0.025, 'phase': 0.0,
            'type': 'point', 'amp': 1.0,
        })

    def _setup_double_slit(self):
        """Plane wave from left hits a vertical barrier with two slits."""
        # Plane wave source along left edge
        self.sources.append({
            'x': 3, 'y': 32, 'freq': 0.03, 'phase': 0.0,
            'type': 'plane_left', 'amp': 0.8,
        })
        # Vertical barrier at x=24 with two slits
        slit_y1 = 24  # center of first slit
        slit_y2 = 40  # center of second slit
        slit_width = 3  # half-width of each slit opening
        barrier_x = 24
        for y in range(N):
            # Wall everywhere except at the two slit openings
            if abs(y - slit_y1) > slit_width and abs(y - slit_y2) > slit_width:
                self.walls[y, barrier_x] = True
                self.walls[y, barrier_x + 1] = True

    def _setup_interference(self):
        """Two point sources oscillating in phase."""
        self.sources.append({
            'x': 32, 'y': 20, 'freq': 0.028, 'phase': 0.0,
            'type': 'point', 'amp': 1.0,
        })
        self.sources.append({
            'x': 32, 'y': 44, 'freq': 0.028, 'phase': 0.0,
            'type': 'point', 'amp': 1.0,
        })

    def _setup_ripple(self):
        """Random drops falling periodically (rain on water)."""
        # No fixed sources; drops are spawned in update()
        pass

    def _setup_reflection(self):
        """Point source with angled barrier walls."""
        self.sources.append({
            'x': 16, 'y': 16, 'freq': 0.025, 'phase': 0.0,
            'type': 'point', 'amp': 1.0,
        })
        # Angled barrier: diagonal from (40, 10) to (55, 50)
        x0, y0 = 40, 10
        x1, y1 = 55, 50
        steps = max(abs(x1 - x0), abs(y1 - y0))
        for i in range(steps + 1):
            t = i / max(1, steps)
            bx = int(x0 + (x1 - x0) * t)
            by = int(y0 + (y1 - y0) * t)
            for d in range(-1, 2):
                wx = bx + d
                if 0 <= wx < N and 0 <= by < N:
                    self.walls[by, wx] = True
        # Short horizontal barrier at bottom
        for x in range(20, 50):
            if 0 <= x < N:
                self.walls[55, x] = True
                self.walls[56, x] = True

    # ── input ────────────────────────────────────────────────────

    def handle_input(self, input_state) -> bool:
        consumed = False
        num_styles = len(_VIEW_MODES) * len(PALETTES)

        # Left/Right: adjust simulation speed
        if input_state.left_pressed:
            self.speed = max(0.1, round(self.speed - 0.2, 1))
            self._show_overlay(f'{self.speed:.1f}X')
            consumed = True
        if input_state.right_pressed:
            self.speed = min(3.0, round(self.speed + 0.2, 1))
            self._show_overlay(f'{self.speed:.1f}X')
            consumed = True

        # Up/Down: cycle visual style (view mode + palette)
        if input_state.up_pressed:
            self.style_idx = (self.style_idx + 1) % num_styles
            self._apply_style()
            consumed = True
        if input_state.down_pressed:
            self.style_idx = (self.style_idx - 1) % num_styles
            self._apply_style()
            consumed = True

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
                # Single button: cycle scenario
                self.scenario_idx = (self.scenario_idx + 1) % len(_SCENARIOS)
                self._setup_scenario()
                self._show_overlay(_SCENARIOS[self.scenario_idx])
                consumed = True
        self._both_pressed_prev = both

        return consumed

    def _apply_style(self):
        """Update view_mode and palette_idx from combined style_idx."""
        self.view_mode = self.style_idx // len(PALETTES)
        self.palette_idx = self.style_idx % len(PALETTES)
        mode_name = _VIEW_MODES[self.view_mode]
        pal_name = PALETTES[self.palette_idx]['name']
        self._show_overlay(f'{pal_name} {mode_name}')

    # ── physics ──────────────────────────────────────────────────

    def _apply_sources(self):
        """Drive source points into the wave field."""
        t = self.phys_time
        for src in self.sources:
            val = src['amp'] * math.sin(2.0 * math.pi * src['freq'] * t + src['phase'])
            if src['type'] == 'point':
                x, y = src['x'], src['y']
                if 0 <= x < N and 0 <= y < N:
                    self.u[y, x] = val
            elif src['type'] == 'plane_left':
                # Drive entire left column
                x = src['x']
                for y in range(N):
                    if not self.walls[y, x]:
                        self.u[y, x] = val

    def _step_wave(self):
        """One leapfrog substep of the 2D wave equation."""
        c2 = C * C * DT_SUB * DT_SUB

        # Compute Laplacian using numpy roll (fast, wraps at edges)
        lap = (
            np.roll(self.u, 1, axis=0) +
            np.roll(self.u, -1, axis=0) +
            np.roll(self.u, 1, axis=1) +
            np.roll(self.u, -1, axis=1) -
            4.0 * self.u
        )

        # Leapfrog: u_next = 2*u - u_prev + c^2 * laplacian
        self.u_next[:] = 2.0 * self.u - self.u_prev + c2 * lap

        # Damping
        self.u_next *= DAMPING

        # Absorbing boundary: force edges to zero
        self.u_next[0, :] = 0.0
        self.u_next[-1, :] = 0.0
        self.u_next[:, 0] = 0.0
        self.u_next[:, -1] = 0.0

        # Enforce walls
        self.u_next[self.walls] = 0.0

        # Rotate buffers
        self.u_prev, self.u, self.u_next = self.u, self.u_next, self.u_prev

    # ── update ───────────────────────────────────────────────────

    def update(self, dt: float):
        self.time += dt

        # Ripple scenario: spawn random drops as wide gaussian blobs
        if _SCENARIOS[self.scenario_idx] == 'RIPPLE':
            self.ripple_timer += dt * self.speed
            if self.ripple_timer > 1.0:
                self.ripple_timer = 0.0
                rx = random.randint(8, N - 9)
                ry = random.randint(8, N - 9)
                amp = random.uniform(0.15, 0.35)
                r = 5  # blob radius — wide to suppress high frequencies
                for dy in range(-r, r + 1):
                    for dx in range(-r, r + 1):
                        d2 = dx * dx + dy * dy
                        if d2 <= r * r:
                            self.u[ry + dy, rx + dx] += amp * math.exp(-d2 / 3.0)

        # Run substeps (scaled by speed)
        steps = max(1, int(SUB_STEPS * self.speed))
        for _ in range(steps):
            self._apply_sources()
            self._step_wave()
            self.phys_time += DT_SUB
            # Clamp per-substep to prevent overflow
            np.clip(self.u, -2.0, 2.0, out=self.u)
            np.clip(self.u_prev, -2.0, 2.0, out=self.u_prev)

        # Overlay timer
        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

        # Notes scroll
        if self.show_notes:
            self.notes_scroll_offset += dt * 18

    # ── draw ─────────────────────────────────────────────────────

    def draw(self):
        d = self.display
        d.clear(Colors.BLACK)
        pal = PALETTES[self.palette_idx]

        if self.view_mode == 0:
            self._draw_waves(d, pal)
        else:
            self._draw_energy(d, pal)

        # Draw walls on top
        for y in range(N):
            for x in range(N):
                if self.walls[y, x]:
                    d.set_pixel(x, y, WALL_COLOR)

        if self.show_notes:
            self._draw_notes()
        self._draw_overlay()

    def _draw_waves(self, d, pal):
        """Render bipolar wave amplitude."""
        for y in range(N):
            for x in range(N):
                if self.walls[y, x]:
                    continue
                val = float(self.u[y, x])
                color = _bipolar_color(val, pal)
                d.set_pixel(x, y, color)

    def _draw_energy(self, d, pal):
        """Render energy density (u^2), single-sided color ramp."""
        energy = self.u * self.u

        for y in range(N):
            for x in range(N):
                if self.walls[y, x]:
                    continue
                val = float(energy[y, x])
                color = _energy_color(val, pal)
                d.set_pixel(x, y, color)
