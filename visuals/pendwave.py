"""
Pendulum Wave
=============
An array of simple pendulums with slightly different lengths, all released
from the same angle simultaneously.  Their different periods create
mesmerizing traveling-wave and beating patterns.  The pendulums periodically
realign, completing one visual cycle.

Scenarios:
  WAVE     - Classic pendulum wave with strings
  SNAKE    - Top-down view with motion trails
  CURTAIN  - 32 thin pendulums connected like fabric
  CHAOS    - Random phase offsets, periodic resync

Controls:
  Left/Right     - Cycle scenario
  Up/Down        - Cycle color palette
  Single button  - Reset / release all from same angle
  Both buttons   - Toggle scrolling notes
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE

# ── Physics constants ────────────────────────────────────────────

G = 9.81
T_CYCLE = 60.0          # seconds for one full realignment cycle
N_BASE = 20             # base oscillation count for longest pendulum
AMP_ANGLE = 0.4         # starting amplitude (radians)
AMP_DISPLAY = 8.0       # max lateral pixel displacement for bobs

# ── Scenarios ────────────────────────────────────────────────────

_SCENARIOS = ['WAVE', 'SNAKE', 'CURTAIN', 'CHAOS']

# ── Palettes ─────────────────────────────────────────────────────
# Each palette: list of (r, g, b) that bobs are mapped across,
# plus a bg color and string color.

PALETTES = [
    {   # Rainbow
        'bobs': [(255, 0, 0), (255, 128, 0), (255, 255, 0), (0, 255, 0),
                 (0, 200, 255), (80, 0, 255), (200, 0, 255)],
        'string': (60, 60, 80),
        'bar': (100, 100, 110),
        'bg': (4, 4, 12),
        'note': (200, 200, 255),
    },
    {   # Fire
        'bobs': [(255, 40, 0), (255, 100, 0), (255, 180, 0),
                 (255, 230, 60), (255, 255, 180)],
        'string': (80, 40, 20),
        'bar': (120, 60, 30),
        'bg': (10, 4, 2),
        'note': (255, 200, 120),
    },
    {   # Ocean
        'bobs': [(10, 30, 120), (20, 80, 180), (40, 160, 220),
                 (100, 220, 240), (200, 255, 255)],
        'string': (20, 40, 70),
        'bar': (40, 70, 100),
        'bg': (2, 4, 12),
        'note': (150, 220, 255),
    },
    {   # Neon
        'bobs': [(255, 0, 200), (200, 0, 255), (100, 0, 255),
                 (0, 100, 255), (0, 220, 255)],
        'string': (60, 20, 80),
        'bar': (100, 40, 120),
        'bg': (6, 2, 12),
        'note': (220, 150, 255),
    },
    {   # Mono
        'bobs': [(255, 255, 255), (240, 240, 240), (220, 220, 220),
                 (200, 200, 200), (180, 180, 180)],
        'string': (50, 50, 50),
        'bar': (80, 80, 80),
        'bg': (5, 5, 5),
        'note': (200, 200, 200),
    },
]


# ── Helper: interpolate a color ramp ─────────────────────────────

def _lerp_ramp(ramp, t):
    """Interpolate a color ramp at position t in [0, 1]."""
    t = max(0.0, min(1.0, t))
    idx = t * (len(ramp) - 1)
    lo = int(idx)
    hi = min(lo + 1, len(ramp) - 1)
    f = idx - lo
    c0, c1 = ramp[lo], ramp[hi]
    return (
        int(c0[0] + (c1[0] - c0[0]) * f),
        int(c0[1] + (c1[1] - c0[1]) * f),
        int(c0[2] + (c1[2] - c0[2]) * f),
    )


def _dim(color, factor):
    """Dim a color by a factor in [0, 1]."""
    return (
        int(color[0] * factor),
        int(color[1] * factor),
        int(color[2] * factor),
    )


# ── PendulumWave class ───────────────────────────────────────────

class PendulumWave(Visual):
    name = "PENDULUM WAVE"
    description = "Mesmerizing beating pendulums"
    category = "science"

    def __init__(self, display: Display):
        super().__init__(display)

    # ── notes ─────────────────────────────────────────────────

    def _get_notes(self):
        pal = PALETTES[self.palette_idx]
        mid = pal['note']
        return [
            ("PENDULUM WAVE", (255, 255, 255)),
            ("EACH PENDULUM HAS A DIFFERENT LENGTH", mid),
            ("SHORTER PENDULUMS SWING FASTER", mid),
            ("PERIOD = 2 PI SQRT(L/G)", mid),
            ("THEY REALIGN AFTER ONE FULL CYCLE", mid),
            ("GALILEO GALILEI 1602", (255, 255, 255)),
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

    # ── overlay ───────────────────────────────────────────────

    def _draw_overlay(self):
        if self.overlay_timer <= 0:
            return
        alpha = min(1.0, self.overlay_timer / 0.5)
        c = (int(255 * alpha), int(255 * alpha), int(255 * alpha))
        self.display.draw_text_small(2, 2, self.overlay_text, c)

    def _show_overlay(self, text):
        self.overlay_text = text
        self.overlay_timer = 2.0

    # ── reset / physics setup ─────────────────────────────────

    def reset(self):
        self.time = 0.0
        self.speed = 1.0
        self.palette_idx = random.randint(0, len(PALETTES) - 1)
        self.scenario_idx = 0

        # Overlay / notes state
        self.overlay_text = ''
        self.overlay_timer = 0.0
        self.show_notes = False
        self.notes_scroll_offset = 0.0
        self.notes_segments = []
        self.notes_scroll_len = 1
        self._both_pressed_prev = False
        self._build_notes_segments()

        # Build pendulum arrays
        self._setup_scenario()

    def _setup_scenario(self):
        """Initialize pendulum state for the current scenario."""
        scenario = _SCENARIOS[self.scenario_idx]

        if scenario == 'CURTAIN':
            self.num_pend = 32
        else:
            self.num_pend = 16

        # Compute angular frequencies: pendulum i completes (N_BASE + i)
        # oscillations in T_CYCLE seconds.
        self.omegas = []
        for i in range(self.num_pend):
            n_osc = N_BASE + i
            omega = 2.0 * math.pi * n_osc / T_CYCLE
            self.omegas.append(omega)

        # Phase offsets (all zero except CHAOS)
        if scenario == 'CHAOS':
            self.phases = [random.uniform(0, 2 * math.pi)
                           for _ in range(self.num_pend)]
            self._chaos_resync_timer = 15.0 + random.uniform(0, 5)
        else:
            self.phases = [0.0] * self.num_pend
            self._chaos_resync_timer = 0.0

        # X positions of pivots, evenly spaced
        if scenario == 'CURTAIN':
            margin = 2
            span = GRID_SIZE - 2 * margin - 1
            self.pivot_xs = [margin + int(i * span / (self.num_pend - 1))
                             for i in range(self.num_pend)]
        else:
            margin = 4
            span = GRID_SIZE - 2 * margin - 1
            self.pivot_xs = [margin + int(i * span / (self.num_pend - 1))
                             for i in range(self.num_pend)]

        self.pivot_y = 4  # horizontal bar y

        # Trails for SNAKE scenario
        self.trail_len = 20
        self.trails = [[] for _ in range(self.num_pend)]

        # Reset simulation time for clean start
        self.time = 0.0

    # ── input ─────────────────────────────────────────────────

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Left/Right: cycle scenario
        if input_state.left_pressed:
            self.scenario_idx = (self.scenario_idx - 1) % len(_SCENARIOS)
            self._setup_scenario()
            self._show_overlay(_SCENARIOS[self.scenario_idx])
            consumed = True
        if input_state.right_pressed:
            self.scenario_idx = (self.scenario_idx + 1) % len(_SCENARIOS)
            self._setup_scenario()
            self._show_overlay(_SCENARIOS[self.scenario_idx])
            consumed = True

        # Up/Down: cycle palette
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
                # Single button: reset / resync all pendulums
                self.phases = [0.0] * self.num_pend
                self.time = 0.0
                self.trails = [[] for _ in range(self.num_pend)]
                if _SCENARIOS[self.scenario_idx] == 'CHAOS':
                    self._chaos_resync_timer = 15.0 + random.uniform(0, 5)
                consumed = True
        self._both_pressed_prev = both

        return consumed

    # ── update ────────────────────────────────────────────────

    def update(self, dt: float):
        self.time += dt
        scenario = _SCENARIOS[self.scenario_idx]

        # CHAOS: periodically resync then re-scatter
        if scenario == 'CHAOS':
            self._chaos_resync_timer -= dt
            if self._chaos_resync_timer <= 0:
                # Toggle between synced and chaotic
                if self.phases[0] == 0.0:
                    # Currently synced -> go chaotic
                    self.phases = [random.uniform(0, 2 * math.pi)
                                   for _ in range(self.num_pend)]
                    self._chaos_resync_timer = 10.0 + random.uniform(0, 5)
                else:
                    # Currently chaotic -> resync
                    self.phases = [0.0] * self.num_pend
                    self.time = 0.0
                    self.trails = [[] for _ in range(self.num_pend)]
                    self._chaos_resync_timer = 5.0 + random.uniform(0, 3)

        # Compute bob positions for trail recording (SNAKE)
        if scenario == 'SNAKE':
            for i in range(self.num_pend):
                angle = AMP_ANGLE * math.cos(
                    self.omegas[i] * self.time * self.speed + self.phases[i])
                bx = self.pivot_xs[i] + AMP_DISPLAY * math.sin(angle)
                by = 40  # fixed y for SNAKE
                self.trails[i].append((int(round(bx)), by))
                if len(self.trails[i]) > self.trail_len:
                    self.trails[i].pop(0)

        # Overlay timer
        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

        # Notes scroll
        if self.show_notes:
            self.notes_scroll_offset += dt * 18

    # ── draw ──────────────────────────────────────────────────

    def _bob_color(self, idx):
        """Get color for bob at index idx."""
        pal = PALETTES[self.palette_idx]
        t = idx / max(1, self.num_pend - 1)
        return _lerp_ramp(pal['bobs'], t)

    def draw(self):
        pal = PALETTES[self.palette_idx]
        self.display.clear(pal['bg'])

        scenario = _SCENARIOS[self.scenario_idx]

        if scenario == 'WAVE':
            self._draw_wave(pal)
        elif scenario == 'SNAKE':
            self._draw_snake(pal)
        elif scenario == 'CURTAIN':
            self._draw_curtain(pal)
        elif scenario == 'CHAOS':
            self._draw_chaos(pal)

        if self.show_notes:
            self._draw_notes()
        self._draw_overlay()

    def _compute_bob_x(self, i):
        """Compute the horizontal position of bob i."""
        angle = AMP_ANGLE * math.cos(
            self.omegas[i] * self.time * self.speed + self.phases[i])
        return self.pivot_xs[i] + AMP_DISPLAY * math.sin(angle)

    # ── WAVE scenario ─────────────────────────────────────────

    def _draw_wave(self, pal):
        # Pivot bar
        self.display.draw_line(0, self.pivot_y, GRID_SIZE - 1, self.pivot_y,
                               pal['bar'])

        bob_y = 40  # all bobs at same y for clean wave visualization

        for i in range(self.num_pend):
            bx = self._compute_bob_x(i)
            ibx = int(round(bx))

            # String from pivot to bob
            self.display.draw_line(self.pivot_xs[i], self.pivot_y + 1,
                                   ibx, bob_y - 2, pal['string'])

            # Bob
            color = self._bob_color(i)
            self.display.draw_circle(ibx, bob_y, 2, color, filled=True)

    # ── SNAKE scenario ────────────────────────────────────────

    def _draw_snake(self, pal):
        bob_y = 40

        for i in range(self.num_pend):
            color = self._bob_color(i)

            # Draw trail
            trail = self.trails[i]
            n = len(trail)
            for j, (tx, ty) in enumerate(trail):
                fade = 0.1 + 0.5 * (j / max(1, n - 1))
                tc = _dim(color, fade)
                if 0 <= tx < GRID_SIZE and 0 <= ty < GRID_SIZE:
                    self.display.set_pixel(tx, ty, tc)

            # Draw current bob
            bx = self._compute_bob_x(i)
            ibx = int(round(bx))
            self.display.draw_circle(ibx, bob_y, 2, color, filled=True)

    # ── CURTAIN scenario ──────────────────────────────────────

    def _draw_curtain(self, pal):
        # Pivot bar
        self.display.draw_line(0, self.pivot_y, GRID_SIZE - 1, self.pivot_y,
                               pal['bar'])

        bob_y = 40
        bob_positions = []

        for i in range(self.num_pend):
            bx = self._compute_bob_x(i)
            ibx = int(round(bx))
            bob_positions.append((ibx, bob_y))

            # Thin string
            self.display.draw_line(self.pivot_xs[i], self.pivot_y + 1,
                                   ibx, bob_y, pal['string'])

        # Connect neighboring bobs with lines (curtain fabric)
        for i in range(self.num_pend - 1):
            x0, y0 = bob_positions[i]
            x1, y1 = bob_positions[i + 1]
            # Blend color between neighbors
            c0 = self._bob_color(i)
            c1 = self._bob_color(i + 1)
            avg_c = (
                (c0[0] + c1[0]) // 2,
                (c0[1] + c1[1]) // 2,
                (c0[2] + c1[2]) // 2,
            )
            self.display.draw_line(x0, y0, x1, y1, _dim(avg_c, 0.7))

        # Draw bobs on top (small, radius 1 for curtain density)
        for i, (bx, by) in enumerate(bob_positions):
            color = self._bob_color(i)
            if 0 <= bx < GRID_SIZE and 0 <= by < GRID_SIZE:
                self.display.set_pixel(bx, by, color)

    # ── CHAOS scenario ────────────────────────────────────────

    def _draw_chaos(self, pal):
        # Pivot bar
        self.display.draw_line(0, self.pivot_y, GRID_SIZE - 1, self.pivot_y,
                               pal['bar'])

        bob_y = 40

        for i in range(self.num_pend):
            bx = self._compute_bob_x(i)
            ibx = int(round(bx))

            # String
            self.display.draw_line(self.pivot_xs[i], self.pivot_y + 1,
                                   ibx, bob_y - 2, pal['string'])

            # Bob with slight glow when synced (phases all zero)
            color = self._bob_color(i)
            if self.phases[i] == 0.0:
                # Synced: brighter
                self.display.draw_circle(ibx, bob_y, 2, color, filled=True)
                # Highlight center pixel
                if 0 <= ibx < GRID_SIZE and 0 <= bob_y < GRID_SIZE:
                    self.display.set_pixel(ibx, bob_y, Colors.WHITE)
            else:
                self.display.draw_circle(ibx, bob_y, 2, color, filled=True)
