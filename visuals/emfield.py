"""
EMField - Electric & Magnetic Field Visualization
===================================================
Coulomb: unified electrostatics sandbox with 5 scenarios (DIPOLE,
QUADRUPOLE, MOTOR, CIRCUIT, RANDOM) sharing one Coulomb physics engine,
field-line tracer, equipotential renderer, and palette system.

Controls:
  Left/Right     - Cycle scenario
  Up/Down        - Cycle color palette
  Single button  - Toggle view mode (field lines / equipotential / circuit wire)
  Both buttons   - Toggle scrolling notes
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE

# Coulomb constant (tuned for display scale)
K_COULOMB = 200.0

# Field line tracing parameters
LINE_STEP = 0.6
MAX_LINE_STEPS = 200
LINES_PER_CHARGE = 10


# ── Shared palettes ──────────────────────────────────────────────

PALETTES = [
    # Classic: red(+) blue(-) yellow lines
    {'pos': (255, 60, 60), 'neg': (60, 100, 255), 'line': (255, 220, 50), 'bg': (5, 5, 15)},
    # Neon
    {'pos': (255, 50, 200), 'neg': (50, 255, 150), 'line': (255, 255, 100), 'bg': (5, 5, 10)},
    # Warm
    {'pos': (255, 150, 50), 'neg': (100, 50, 200), 'line': (255, 200, 150), 'bg': (10, 5, 5)},
    # Cool
    {'pos': (50, 200, 255), 'neg': (200, 50, 100), 'line': (150, 220, 255), 'bg': (5, 5, 15)},
    # Monochrome
    {'pos': (255, 255, 255), 'neg': (120, 120, 120), 'line': (200, 200, 200), 'bg': (5, 5, 5)},
]

# Equipotential color ramp
EQUIP_RAMPS = [
    [(30, 0, 80), (0, 0, 200), (0, 180, 200), (80, 255, 80), (255, 255, 0), (255, 80, 0), (200, 0, 0)],
    [(0, 10, 30), (0, 80, 150), (0, 200, 200), (200, 255, 100), (255, 200, 50), (255, 80, 80), (200, 0, 50)],
    [(10, 0, 20), (80, 0, 120), (180, 50, 150), (255, 100, 100), (255, 200, 80), (255, 255, 150), (255, 255, 255)],
    [(0, 10, 20), (0, 60, 100), (50, 150, 150), (150, 200, 150), (200, 200, 100), (200, 150, 50), (150, 50, 0)],
    [(10, 10, 10), (50, 50, 50), (100, 100, 100), (150, 150, 150), (200, 200, 200), (230, 230, 230), (255, 255, 255)],
]


# ── Shared field computation ─────────────────────────────────────

class Charge:
    __slots__ = ('q', 'x', 'y', 'freq_x', 'freq_y', 'phase_x', 'phase_y',
                 'amp_x', 'amp_y', 'cx', 'cy')

    def __init__(self, q, cx, cy, freq_x=0, freq_y=0, phase_x=0, phase_y=0,
                 amp_x=0, amp_y=0):
        self.q = q
        self.cx = cx
        self.cy = cy
        self.freq_x = freq_x
        self.freq_y = freq_y
        self.phase_x = phase_x
        self.phase_y = phase_y
        self.amp_x = amp_x
        self.amp_y = amp_y
        self.x = cx
        self.y = cy


def _efield_at(charges, px, py):
    """Compute electric field (Ex, Ey) at point (px, py)."""
    ex, ey = 0.0, 0.0
    for c in charges:
        dx = px - c.x
        dy = py - c.y
        dist2 = dx * dx + dy * dy + 1.0
        dist = math.sqrt(dist2)
        inv_dist3 = 1.0 / (dist2 * dist)
        e_mag = K_COULOMB * c.q * inv_dist3
        ex += e_mag * dx
        ey += e_mag * dy
    return ex, ey


def _potential_at(charges, px, py):
    """Compute electric potential at point (px, py)."""
    v = 0.0
    for c in charges:
        dx = px - c.x
        dy = py - c.y
        dist = math.sqrt(dx * dx + dy * dy + 1.0)
        v += K_COULOMB * c.q / dist
    return v


def _trace_field_line(charges, start_x, start_y):
    """Trace a field line from a starting point."""
    points = []
    x, y = float(start_x), float(start_y)

    for _ in range(MAX_LINE_STEPS):
        ix, iy = int(x), int(y)
        if ix < 0 or ix >= GRID_SIZE or iy < 0 or iy >= GRID_SIZE:
            break
        points.append((ix, iy))

        ex, ey = _efield_at(charges, x, y)
        mag = math.sqrt(ex * ex + ey * ey)
        if mag < 0.01:
            break

        x += LINE_STEP * ex / mag
        y += LINE_STEP * ey / mag

        for c in charges:
            if c.q < 0:
                dx = x - c.x
                dy = y - c.y
                if dx * dx + dy * dy < 4.0:
                    points.append((int(x), int(y)))
                    return points

    return points


def _compute_field_lines(charges):
    """Compute all field lines from positive charges."""
    lines = []
    for c in charges:
        if c.q <= 0:
            continue
        for i in range(LINES_PER_CHARGE):
            angle = 2 * math.pi * i / LINES_PER_CHARGE
            sx = c.x + 2.0 * math.cos(angle)
            sy = c.y + 2.0 * math.sin(angle)
            line = _trace_field_line(charges, sx, sy)
            if len(line) > 2:
                lines.append(line)
    return lines


def _draw_charges(display, charges, pal):
    """Draw charge symbols (+/-)."""
    for c in charges:
        ix, iy = int(c.x), int(c.y)
        if c.q > 0:
            color = pal['pos']
            display.draw_circle(ix, iy, 2, color, filled=True)
            if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                display.set_pixel(ix, iy, Colors.WHITE)
        else:
            color = pal['neg']
            display.draw_circle(ix, iy, 2, color, filled=True)
            for dx in [-1, 0, 1]:
                px = ix + dx
                if 0 <= px < GRID_SIZE and 0 <= iy < GRID_SIZE:
                    display.set_pixel(px, iy, Colors.WHITE)


def _draw_field_lines(display, lines, pal):
    """Draw cached field lines."""
    line_color = pal['line']
    for line in lines:
        n = len(line)
        for i, (x, y) in enumerate(line):
            if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                t = 1.0 - (i / n) * 0.6
                color = (
                    int(line_color[0] * t),
                    int(line_color[1] * t),
                    int(line_color[2] * t),
                )
                display.set_pixel(x, y, color)


def _draw_equipotential(display, charges, palette_idx):
    """Draw equipotential contour map."""
    ramp = EQUIP_RAMPS[palette_idx % len(EQUIP_RAMPS)]
    n_colors = len(ramp)

    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            v = _potential_at(charges, x + 0.5, y + 0.5)
            t = (math.atan(v * 0.02) / math.pi + 0.5)

            band = (t * 20) % 1.0
            if band < 0.1:
                brightness = 0.3
            else:
                brightness = 0.6 + 0.4 * band

            idx = t * (n_colors - 1)
            lo = int(idx)
            hi = min(lo + 1, n_colors - 1)
            f = idx - lo
            c0 = ramp[lo]
            c1 = ramp[hi]
            r = int((c0[0] + (c1[0] - c0[0]) * f) * brightness)
            g = int((c0[1] + (c1[1] - c0[1]) * f) * brightness)
            b = int((c0[2] + (c1[2] - c0[2]) * f) * brightness)
            display.set_pixel(x, y, (r, g, b))


# ── EMMotor ──────────────────────────────────────────────────────

class EMMotor(Visual):
    name = "EM MOTOR"
    description = "Electromagnetic motor"
    category = "science"

    NUM_STATOR = 8
    NUM_ROTOR = 4

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed = 1.0
        self.palette_idx = 0
        self.rotor_angle = 0.0
        self.field_line_mode = True
        self._cached_lines = []
        self._cache_time = -1.0
        self._init_charges()

    def _init_charges(self):
        """Stator: ring of alternating charges. Rotor: inner ring that spins."""
        self.charges = []
        cx, cy = GRID_SIZE / 2, GRID_SIZE / 2

        # Stator charges (fixed ring)
        self.stator_charges = []
        r_stator = 22
        for i in range(self.NUM_STATOR):
            angle = 2 * math.pi * i / self.NUM_STATOR
            q = 1.0 if i % 2 == 0 else -1.0
            x = cx + r_stator * math.cos(angle)
            y = cy + r_stator * math.sin(angle)
            c = Charge(q, x, y)
            self.stator_charges.append(c)
            self.charges.append(c)

        # Rotor charges (spin around center)
        self.rotor_charges = []
        self.r_rotor = 10
        for i in range(self.NUM_ROTOR):
            q = 1.0 if i % 2 == 0 else -1.0
            c = Charge(q, cx, cy)  # Position updated in update()
            self.rotor_charges.append(c)
            self.charges.append(c)

        self.cx = cx
        self.cy = cy

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.up_pressed:
            self.palette_idx = (self.palette_idx + 1) % len(PALETTES)
            consumed = True
        if input_state.down_pressed:
            self.palette_idx = (self.palette_idx - 1) % len(PALETTES)
            consumed = True
        if input_state.left:
            self.speed = max(0.1, self.speed - 0.1)
            consumed = True
        if input_state.right:
            self.speed = min(3.0, self.speed + 0.1)
            consumed = True
        if input_state.action_l or input_state.action_r:
            self.field_line_mode = not self.field_line_mode
            self._cache_time = -1.0
            consumed = True
        return consumed

    def update(self, dt: float):
        self.time += dt

        # Auto-rotate rotor
        self.rotor_angle += dt * self.speed * 0.8
        for i, c in enumerate(self.rotor_charges):
            angle = self.rotor_angle + 2 * math.pi * i / self.NUM_ROTOR
            c.x = self.cx + self.r_rotor * math.cos(angle)
            c.y = self.cy + self.r_rotor * math.sin(angle)
            c.x = max(3, min(GRID_SIZE - 4, c.x))
            c.y = max(3, min(GRID_SIZE - 4, c.y))

        # Recompute field lines periodically
        if self.field_line_mode:
            if self.time - self._cache_time > 0.15:
                self._cached_lines = _compute_field_lines(self.charges)
                self._cache_time = self.time

    def draw(self):
        pal = PALETTES[self.palette_idx]
        self.display.clear(pal['bg'])

        if self.field_line_mode:
            _draw_field_lines(self.display, self._cached_lines, pal)
        else:
            _draw_equipotential(self.display, self.charges, self.palette_idx)

        _draw_charges(self.display, self.charges, pal)


# ── EMCircuit ────────────────────────────────────────────────────

class EMCircuit(Visual):
    name = "EM CIRCUIT"
    description = "Current in a circuit"
    category = "science"

    NUM_DOTS = 24

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed = 1.0
        self.palette_idx = 0
        self.field_line_mode = False  # Start with circuit view
        self._init_circuit()

    def _init_circuit(self):
        """Rectangular circuit path with charge dots flowing along it."""
        # Circuit rectangle corners (padded from edges)
        margin = 10
        self.x0 = margin
        self.y0 = margin
        self.x1 = GRID_SIZE - margin
        self.y1 = GRID_SIZE - margin

        # Perimeter segments: top, right, bottom, left
        w = self.x1 - self.x0
        h = self.y1 - self.y0
        self.perimeter = 2 * w + 2 * h

        # Resistor zone: bottom segment, middle third
        self.resistor_start = w + h + w // 3
        self.resistor_end = w + h + 2 * w // 3

        # Dot positions as fraction of perimeter [0, 1)
        self.dot_phases = [i / self.NUM_DOTS for i in range(self.NUM_DOTS)]

        # Charges for field line / equipotential rendering
        # Place alternating charges at corners and midpoints of circuit
        self._charges = []
        corners = [
            (self.x0, self.y0), (self.x1, self.y0),
            (self.x1, self.y1), (self.x0, self.y1),
        ]
        mids = [
            ((self.x0 + self.x1) / 2, self.y0),
            (self.x1, (self.y0 + self.y1) / 2),
            ((self.x0 + self.x1) / 2, self.y1),
            (self.x0, (self.y0 + self.y1) / 2),
        ]
        for i, (cx, cy) in enumerate(corners + mids):
            q = 1.0 if i % 2 == 0 else -1.0
            self._charges.append(Charge(q, cx, cy))

        # Cache for field lines
        self._cached_lines = []
        self._cache_time = -1.0

    def _perimeter_to_xy(self, frac):
        """Convert fractional perimeter position to (x, y) coordinates."""
        w = self.x1 - self.x0
        h = self.y1 - self.y0
        perim = self.perimeter
        d = (frac % 1.0) * perim

        if d < w:
            # Top edge: left to right
            return self.x0 + d, self.y0
        d -= w
        if d < h:
            # Right edge: top to bottom
            return self.x1, self.y0 + d
        d -= h
        if d < w:
            # Bottom edge: right to left
            return self.x1 - d, self.y1
        d -= w
        # Left edge: bottom to top
        return self.x0, self.y1 - d

    def _in_resistor(self, frac):
        """Check if a dot is in the resistor zone."""
        d = (frac % 1.0) * self.perimeter
        return self.resistor_start <= d <= self.resistor_end

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.up_pressed:
            self.palette_idx = (self.palette_idx + 1) % len(PALETTES)
            consumed = True
        if input_state.down_pressed:
            self.palette_idx = (self.palette_idx - 1) % len(PALETTES)
            consumed = True
        if input_state.left:
            self.speed = max(0.1, self.speed - 0.1)
            consumed = True
        if input_state.right:
            self.speed = min(3.0, self.speed + 0.1)
            consumed = True
        if input_state.action_l or input_state.action_r:
            self.field_line_mode = not self.field_line_mode
            self._cache_time = -1.0
            consumed = True
        return consumed

    def update(self, dt: float):
        self.time += dt

        # Move dots along perimeter
        base_speed = 0.15 * self.speed * dt
        for i in range(len(self.dot_phases)):
            # Slow down in resistor zone
            if self._in_resistor(self.dot_phases[i]):
                self.dot_phases[i] += base_speed * 0.3
            else:
                self.dot_phases[i] += base_speed
            self.dot_phases[i] %= 1.0

        # Update charge positions to follow dots (keeps field rendering alive)
        for k, c in enumerate(self._charges):
            frac = (k / len(self._charges) + self.time * 0.02 * self.speed) % 1.0
            x, y = self._perimeter_to_xy(frac)
            c.x = x
            c.y = y

        # Recompute field lines periodically
        if self.field_line_mode:
            if self.time - self._cache_time > 0.15:
                self._cached_lines = _compute_field_lines(self._charges)
                self._cache_time = self.time

    def _draw_circuit_view(self, pal):
        """Draw wire, glow, and charge dots."""
        # Draw wire path
        wire_color = (40, 40, 50)
        self.display.draw_line(self.x0, self.y0, self.x1, self.y0, wire_color)
        self.display.draw_line(self.x1, self.y0, self.x1, self.y1, wire_color)
        self.display.draw_line(self.x1, self.y1, self.x0, self.y1, wire_color)
        self.display.draw_line(self.x0, self.y1, self.x0, self.y0, wire_color)

        # Draw resistor zone highlight
        w = self.x1 - self.x0
        rx0 = self.x1 - w // 3
        rx1 = self.x1 - 2 * w // 3
        resistor_color = (60, 30, 15)
        self.display.draw_line(rx0, self.y1, rx1, self.y1, resistor_color)

        # Draw magnetic field glow around wire segments
        glow_color = pal['line']
        for frac_i in range(80):
            frac = frac_i / 80.0
            x, y = self._perimeter_to_xy(frac)
            ix, iy = int(x), int(y)
            intensity = 0.15 + 0.1 * math.sin(self.time * 4 + frac * 12)
            gc = (
                int(glow_color[0] * intensity),
                int(glow_color[1] * intensity),
                int(glow_color[2] * intensity),
            )
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = ix + dx, iy + dy
                if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                    cur = self.display.get_pixel(nx, ny)
                    blended = (
                        min(255, cur[0] + gc[0]),
                        min(255, cur[1] + gc[1]),
                        min(255, cur[2] + gc[2]),
                    )
                    self.display.set_pixel(nx, ny, blended)

        # Draw charge dots
        for phase in self.dot_phases:
            x, y = self._perimeter_to_xy(phase)
            ix, iy = int(x), int(y)
            if self._in_resistor(phase):
                color = (
                    int(pal['pos'][0] * 0.5),
                    int(pal['pos'][1] * 0.5),
                    int(pal['pos'][2] * 0.5),
                )
            else:
                color = pal['pos']
            if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                self.display.set_pixel(ix, iy, color)

    def draw(self):
        pal = PALETTES[self.palette_idx]
        self.display.clear(pal['bg'])

        if self.field_line_mode:
            _draw_field_lines(self.display, self._cached_lines, pal)
            _draw_charges(self.display, self._charges, pal)
        else:
            self._draw_circuit_view(pal)


# ── EMFreeAir ────────────────────────────────────────────────────

CONFIGS = [
    # Dipole
    [{'q': 1.0}, {'q': -1.0}],
    # Quadrupole
    [{'q': 1.0}, {'q': -1.0}, {'q': 1.0}, {'q': -1.0}],
    # Random 4-6
    None,
]


class EMFreeAir(Visual):
    name = "EM FIELD"
    description = "Electric field lines"
    category = "science"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed = 1.0
        self.palette_idx = 0
        self.config_idx = 0
        self.field_line_mode = True
        self._init_charges()
        self._cached_lines = []
        self._cache_time = -1.0

    def _init_charges(self):
        self.charges = []
        cx, cy = GRID_SIZE / 2, GRID_SIZE / 2
        config = CONFIGS[self.config_idx]

        if config is None:
            n = random.randint(4, 6)
            config = []
            for i in range(n):
                config.append({'q': 1.0 if i % 2 == 0 else -1.0})

        n = len(config)
        for i, cfg in enumerate(config):
            angle = 2 * math.pi * i / n
            r = 12 + random.uniform(-2, 2)
            ch_cx = cx + r * math.cos(angle)
            ch_cy = cy + r * math.sin(angle)
            freq_x = random.uniform(0.15, 0.4)
            freq_y = random.uniform(0.15, 0.4)
            phase_x = random.uniform(0, 2 * math.pi)
            phase_y = random.uniform(0, 2 * math.pi)
            amp_x = random.uniform(4, 10)
            amp_y = random.uniform(4, 10)
            self.charges.append(Charge(cfg['q'], ch_cx, ch_cy,
                                       freq_x, freq_y, phase_x, phase_y,
                                       amp_x, amp_y))

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.up_pressed:
            self.palette_idx = (self.palette_idx + 1) % len(PALETTES)
            consumed = True
        if input_state.down_pressed:
            self.palette_idx = (self.palette_idx - 1) % len(PALETTES)
            consumed = True
        if input_state.left:
            self.speed = max(0.1, self.speed - 0.1)
            consumed = True
        if input_state.right:
            self.speed = min(3.0, self.speed + 0.1)
            consumed = True
        if input_state.action_l or input_state.action_r:
            self.field_line_mode = not self.field_line_mode
            self._cache_time = -1.0
            consumed = True
        return consumed

    def update(self, dt: float):
        self.time += dt

        # Move charges along Lissajous paths
        t = self.time * self.speed
        for c in self.charges:
            c.x = c.cx + c.amp_x * math.sin(c.freq_x * t + c.phase_x)
            c.y = c.cy + c.amp_y * math.sin(c.freq_y * t + c.phase_y)
            c.x = max(3, min(GRID_SIZE - 4, c.x))
            c.y = max(3, min(GRID_SIZE - 4, c.y))

        # Cycle config on reseed timer
        # (configs cycle when user restarts via space on a different visual,
        #  or we could auto-cycle — keeping manual for now)

        if self.field_line_mode:
            if self.time - self._cache_time > 0.15:
                self._cached_lines = _compute_field_lines(self.charges)
                self._cache_time = self.time

    def draw(self):
        pal = PALETTES[self.palette_idx]
        self.display.clear(pal['bg'])

        if self.field_line_mode:
            _draw_field_lines(self.display, self._cached_lines, pal)
        else:
            _draw_equipotential(self.display, self.charges, self.palette_idx)

        _draw_charges(self.display, self.charges, pal)


# ── Coulomb (unified EM visual) ──────────────────────────────────

_SCENARIOS = ['DIPOLE', 'QUADRUPOLE', 'MOTOR', 'CIRCUIT', 'RANDOM']
_VIEW_MODES = ['FIELD LINES', 'POTENTIAL', 'CIRCUIT']


class Coulomb(Visual):
    name = "COULOMB"
    description = "Electrostatics sandbox"
    category = "science"

    NUM_STATOR = 8
    NUM_ROTOR = 4
    NUM_DOTS = 24

    def __init__(self, display: Display):
        super().__init__(display)

    # ── notes ────────────────────────────────────────────────────

    def _get_notes(self):
        pal = PALETTES[self.palette_idx]
        mid = pal['line']
        return [
            ("COULOMB'S LAW", (255, 255, 255)),
            ("F = K * Q1 * Q2 / R^2", mid),
            ("FIELD LINES FLOW + TO -", mid),
            ("EQUIPOTENTIALS ARE PERPENDICULAR TO FIELD LINES", mid),
            ("CHARLES-AUGUSTIN DE COULOMB 1785", (255, 255, 255)),
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
        self.speed = 1.0
        self.palette_idx = 0
        self.scenario_idx = 0
        self.view_mode = 0  # 0=field lines, 1=potential, 2=circuit wire
        self.charges = []
        self._cached_lines = []
        self._cache_time = -1.0
        self.overlay_text = ''
        self.overlay_timer = 0.0
        self.show_notes = False
        self.notes_scroll_offset = 0.0
        self.notes_segments = []
        self.notes_scroll_len = 1
        self._both_pressed_prev = False
        self._build_notes_segments()
        self._setup_scenario()

    def _setup_scenario(self):
        """Build charges + scenario-specific state for current scenario_idx."""
        self.charges = []
        self._cached_lines = []
        self._cache_time = -1.0
        scenario = _SCENARIOS[self.scenario_idx]

        if scenario == 'DIPOLE':
            self._setup_lissajous([{'q': 1.0}, {'q': -1.0}])
        elif scenario == 'QUADRUPOLE':
            self._setup_lissajous([{'q': 1.0}, {'q': -1.0},
                                    {'q': 1.0}, {'q': -1.0}])
        elif scenario == 'MOTOR':
            self._setup_motor()
        elif scenario == 'CIRCUIT':
            self._setup_circuit()
        elif scenario == 'RANDOM':
            n = random.randint(4, 6)
            config = [{'q': 1.0 if i % 2 == 0 else -1.0} for i in range(n)]
            self._setup_lissajous(config)

    def _setup_lissajous(self, config):
        """Create charges on Lissajous orbits."""
        cx, cy = GRID_SIZE / 2, GRID_SIZE / 2
        n = len(config)
        for i, cfg in enumerate(config):
            angle = 2 * math.pi * i / n
            r = 12 + random.uniform(-2, 2)
            ch_cx = cx + r * math.cos(angle)
            ch_cy = cy + r * math.sin(angle)
            freq_x = random.uniform(0.15, 0.4)
            freq_y = random.uniform(0.15, 0.4)
            phase_x = random.uniform(0, 2 * math.pi)
            phase_y = random.uniform(0, 2 * math.pi)
            amp_x = random.uniform(4, 10)
            amp_y = random.uniform(4, 10)
            self.charges.append(Charge(cfg['q'], ch_cx, ch_cy,
                                       freq_x, freq_y, phase_x, phase_y,
                                       amp_x, amp_y))

    def _setup_motor(self):
        """Stator ring + spinning rotor."""
        cx, cy = GRID_SIZE / 2, GRID_SIZE / 2
        self.cx = cx
        self.cy = cy
        self.r_rotor = 10
        self.rotor_angle = 0.0

        self.stator_charges = []
        r_stator = 22
        for i in range(self.NUM_STATOR):
            angle = 2 * math.pi * i / self.NUM_STATOR
            q = 1.0 if i % 2 == 0 else -1.0
            x = cx + r_stator * math.cos(angle)
            y = cy + r_stator * math.sin(angle)
            c = Charge(q, x, y)
            self.stator_charges.append(c)
            self.charges.append(c)

        self.rotor_charges = []
        for i in range(self.NUM_ROTOR):
            q = 1.0 if i % 2 == 0 else -1.0
            c = Charge(q, cx, cy)
            self.rotor_charges.append(c)
            self.charges.append(c)

    def _setup_circuit(self):
        """Rectangular circuit with flowing dot charges."""
        margin = 10
        self.x0 = margin
        self.y0 = margin
        self.x1 = GRID_SIZE - margin
        self.y1 = GRID_SIZE - margin
        w = self.x1 - self.x0
        h = self.y1 - self.y0
        self.perimeter = 2 * w + 2 * h
        self.resistor_start = w + h + w // 3
        self.resistor_end = w + h + 2 * w // 3
        self.dot_phases = [i / self.NUM_DOTS for i in range(self.NUM_DOTS)]

        corners = [
            (self.x0, self.y0), (self.x1, self.y0),
            (self.x1, self.y1), (self.x0, self.y1),
        ]
        mids = [
            ((self.x0 + self.x1) / 2, self.y0),
            (self.x1, (self.y0 + self.y1) / 2),
            ((self.x0 + self.x1) / 2, self.y1),
            (self.x0, (self.y0 + self.y1) / 2),
        ]
        for i, (cx, cy) in enumerate(corners + mids):
            q = 1.0 if i % 2 == 0 else -1.0
            self.charges.append(Charge(q, cx, cy))

    # ── circuit helpers ──────────────────────────────────────────

    def _perimeter_to_xy(self, frac):
        w = self.x1 - self.x0
        h = self.y1 - self.y0
        d = (frac % 1.0) * self.perimeter
        if d < w:
            return self.x0 + d, self.y0
        d -= w
        if d < h:
            return self.x1, self.y0 + d
        d -= h
        if d < w:
            return self.x1 - d, self.y1
        d -= w
        return self.x0, self.y1 - d

    def _in_resistor(self, frac):
        d = (frac % 1.0) * self.perimeter
        return self.resistor_start <= d <= self.resistor_end

    # ── input ────────────────────────────────────────────────────

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Left/Right: cycle scenario
        if input_state.left_pressed:
            self.scenario_idx = (self.scenario_idx - 1) % len(_SCENARIOS)
            self._setup_scenario()
            self._show_overlay(_SCENARIOS[self.scenario_idx])
            if self.view_mode == 2 and _SCENARIOS[self.scenario_idx] != 'CIRCUIT':
                self.view_mode = 0
            consumed = True
        if input_state.right_pressed:
            self.scenario_idx = (self.scenario_idx + 1) % len(_SCENARIOS)
            self._setup_scenario()
            self._show_overlay(_SCENARIOS[self.scenario_idx])
            if self.view_mode == 2 and _SCENARIOS[self.scenario_idx] != 'CIRCUIT':
                self.view_mode = 0
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
                # Single button: cycle view mode
                is_circuit = _SCENARIOS[self.scenario_idx] == 'CIRCUIT'
                max_mode = 3 if is_circuit else 2
                self.view_mode = (self.view_mode + 1) % max_mode
                self._cache_time = -1.0
                self._show_overlay(_VIEW_MODES[self.view_mode])
                consumed = True
        self._both_pressed_prev = both

        return consumed

    # ── update ───────────────────────────────────────────────────

    def update(self, dt: float):
        self.time += dt
        scenario = _SCENARIOS[self.scenario_idx]

        if scenario in ('DIPOLE', 'QUADRUPOLE', 'RANDOM'):
            t = self.time * self.speed
            for c in self.charges:
                c.x = c.cx + c.amp_x * math.sin(c.freq_x * t + c.phase_x)
                c.y = c.cy + c.amp_y * math.sin(c.freq_y * t + c.phase_y)
                c.x = max(3, min(GRID_SIZE - 4, c.x))
                c.y = max(3, min(GRID_SIZE - 4, c.y))

        elif scenario == 'MOTOR':
            self.rotor_angle += dt * self.speed * 0.8
            for i, c in enumerate(self.rotor_charges):
                angle = self.rotor_angle + 2 * math.pi * i / self.NUM_ROTOR
                c.x = self.cx + self.r_rotor * math.cos(angle)
                c.y = self.cy + self.r_rotor * math.sin(angle)
                c.x = max(3, min(GRID_SIZE - 4, c.x))
                c.y = max(3, min(GRID_SIZE - 4, c.y))

        elif scenario == 'CIRCUIT':
            base_speed = 0.15 * self.speed * dt
            for i in range(len(self.dot_phases)):
                if self._in_resistor(self.dot_phases[i]):
                    self.dot_phases[i] += base_speed * 0.3
                else:
                    self.dot_phases[i] += base_speed
                self.dot_phases[i] %= 1.0
            for k, c in enumerate(self.charges):
                frac = (k / len(self.charges) + self.time * 0.02 * self.speed) % 1.0
                x, y = self._perimeter_to_xy(frac)
                c.x = x
                c.y = y

        # Recompute field lines when in field line view
        if self.view_mode == 0:
            if self.time - self._cache_time > 0.15:
                self._cached_lines = _compute_field_lines(self.charges)
                self._cache_time = self.time

        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

        if self.show_notes:
            self.notes_scroll_offset += dt * 18

    # ── draw ─────────────────────────────────────────────────────

    def draw(self):
        pal = PALETTES[self.palette_idx]
        self.display.clear(pal['bg'])

        if self.view_mode == 0:
            _draw_field_lines(self.display, self._cached_lines, pal)
            _draw_charges(self.display, self.charges, pal)
        elif self.view_mode == 1:
            _draw_equipotential(self.display, self.charges, self.palette_idx)
        elif self.view_mode == 2:
            self._draw_circuit_view(pal)

        if self.show_notes:
            self._draw_notes()
        self._draw_overlay()

    def _draw_circuit_view(self, pal):
        """Draw wire path + magnetic glow + flowing charge dots."""
        wire_color = (40, 40, 50)
        self.display.draw_line(self.x0, self.y0, self.x1, self.y0, wire_color)
        self.display.draw_line(self.x1, self.y0, self.x1, self.y1, wire_color)
        self.display.draw_line(self.x1, self.y1, self.x0, self.y1, wire_color)
        self.display.draw_line(self.x0, self.y1, self.x0, self.y0, wire_color)

        w = self.x1 - self.x0
        rx0 = self.x1 - w // 3
        rx1 = self.x1 - 2 * w // 3
        resistor_color = (60, 30, 15)
        self.display.draw_line(rx0, self.y1, rx1, self.y1, resistor_color)

        glow_color = pal['line']
        for frac_i in range(80):
            frac = frac_i / 80.0
            x, y = self._perimeter_to_xy(frac)
            ix, iy = int(x), int(y)
            intensity = 0.15 + 0.1 * math.sin(self.time * 4 + frac * 12)
            gc = (
                int(glow_color[0] * intensity),
                int(glow_color[1] * intensity),
                int(glow_color[2] * intensity),
            )
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = ix + dx, iy + dy
                if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                    cur = self.display.get_pixel(nx, ny)
                    blended = (
                        min(255, cur[0] + gc[0]),
                        min(255, cur[1] + gc[1]),
                        min(255, cur[2] + gc[2]),
                    )
                    self.display.set_pixel(nx, ny, blended)

        for phase in self.dot_phases:
            x, y = self._perimeter_to_xy(phase)
            ix, iy = int(x), int(y)
            if self._in_resistor(phase):
                color = (
                    int(pal['pos'][0] * 0.5),
                    int(pal['pos'][1] * 0.5),
                    int(pal['pos'][2] * 0.5),
                )
            else:
                color = pal['pos']
            if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                self.display.set_pixel(ix, iy, color)
