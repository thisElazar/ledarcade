"""
Oscilloscope - Lissajous Figures & Waveforms
=============================================
Phosphor-green waveforms on black with grid lines and
phosphor trail fade effect.

Controls:
  Up/Down    - Cycle modes (sine, Lissajous, superposition, sweep)
  Left/Right - Adjust frequency ratio / frequency (held = continuous)
  Space      - Toggle auto-cycle
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE

# Oscilloscope color palette (phosphor green)
PHOSPHOR_BRIGHT = (0, 255, 80)
PHOSPHOR_MED = (0, 160, 50)
PHOSPHOR_DIM = (0, 80, 25)
PHOSPHOR_FAINT = (0, 40, 12)
GRID_COLOR = (0, 30, 10)
GRID_AXIS = (0, 50, 15)

# Display modes
MODES = [
    'SINE WAVE',
    'SQUARE WAVE',
    'TRIANGLE',
    'SAWTOOTH',
    'LISSAJOUS',
    'SUPERPOSITION',
    'FREQ SWEEP',
    'NOISE',
]

# Lissajous frequency ratios (a:b)
RATIOS = [
    (1, 1), (1, 2), (1, 3), (2, 3), (3, 2),
    (3, 4), (4, 3), (3, 5), (5, 4), (4, 5),
    (5, 6), (7, 6), (5, 8),
]

# Drawing area (leave room for label at bottom)
DRAW_Y_MIN = 2
DRAW_Y_MAX = 53
DRAW_X_MIN = 0
DRAW_X_MAX = 63
CX = (DRAW_X_MIN + DRAW_X_MAX) // 2
CY = (DRAW_Y_MIN + DRAW_Y_MAX) // 2
HALF_W = (DRAW_X_MAX - DRAW_X_MIN) // 2
HALF_H = (DRAW_Y_MAX - DRAW_Y_MIN) // 2


class Oscilloscope(Visual):
    name = "OSCILLOSCOPE"
    description = "Phosphor-green waveforms and Lissajous figures"
    category = "science"

    def reset(self):
        self.time = 0.0
        self.mode_idx = 0
        self.freq = 2.0            # Base frequency for sine mode
        self.ratio_idx = 0         # Index into RATIOS for Lissajous
        self.phase = 0.0           # Phase offset for Lissajous
        self.sweep_freq = 1.0      # Current sweep frequency
        self.auto_cycle = True
        self.cycle_timer = 0.0
        self.cycle_duration = 10.0
        self.overlay_timer = 0.0
        self.label_timer = 0.0

        # Trail buffer: list of previous frame point sets for fade
        self.trail = []
        self.max_trail = 6

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.up_pressed:
            self.mode_idx = (self.mode_idx - 1) % len(MODES)
            self.overlay_timer = 2.5
            self.trail.clear()
            consumed = True
        if input_state.down_pressed:
            self.mode_idx = (self.mode_idx + 1) % len(MODES)
            self.overlay_timer = 2.5
            self.trail.clear()
            consumed = True

        # Continuous held input for frequency adjustment
        if input_state.left:
            mode = MODES[self.mode_idx]
            if mode == 'LISSAJOUS':
                if input_state.left_pressed:
                    self.ratio_idx = (self.ratio_idx - 1) % len(RATIOS)
                    self.trail.clear()
            elif mode == 'FREQ SWEEP':
                pass  # Sweep is automatic
            else:
                self.freq = max(0.5, self.freq - 0.03)
            consumed = True
        if input_state.right:
            mode = MODES[self.mode_idx]
            if mode == 'LISSAJOUS':
                if input_state.right_pressed:
                    self.ratio_idx = (self.ratio_idx + 1) % len(RATIOS)
                    self.trail.clear()
            elif mode == 'FREQ SWEEP':
                pass
            else:
                self.freq = min(8.0, self.freq + 0.03)
            consumed = True

        if input_state.action_l or input_state.action_r:
            self.auto_cycle = not self.auto_cycle
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt
        self.label_timer += dt
        self.phase += dt * 1.5

        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

        # Sweep mode: auto-vary frequency
        if MODES[self.mode_idx] == 'FREQ SWEEP':
            self.sweep_freq = 1.0 + 3.0 * (0.5 + 0.5 * math.sin(self.time * 0.3))

        if self.auto_cycle:
            self.cycle_timer += dt
            if self.cycle_timer >= self.cycle_duration:
                self.cycle_timer = 0.0
                self.mode_idx = (self.mode_idx + 1) % len(MODES)
                self.overlay_timer = 2.0
                self.trail.clear()

    def _generate_points(self):
        """Generate the current waveform as a list of (x, y) screen points."""
        mode = MODES[self.mode_idx]
        points = []
        n_samples = 128

        if mode == 'SINE WAVE':
            for i in range(n_samples):
                t = i / n_samples
                x = DRAW_X_MIN + t * (DRAW_X_MAX - DRAW_X_MIN)
                y_val = math.sin(2 * math.pi * self.freq * t + self.phase)
                y = CY - y_val * (HALF_H - 2)
                points.append((x, y))

        elif mode == 'SQUARE WAVE':
            for i in range(n_samples):
                t = i / n_samples
                x = DRAW_X_MIN + t * (DRAW_X_MAX - DRAW_X_MIN)
                s = math.sin(2 * math.pi * self.freq * t + self.phase)
                y_val = 1.0 if s >= 0 else -1.0
                y = CY - y_val * (HALF_H - 4)
                points.append((x, y))

        elif mode == 'TRIANGLE':
            for i in range(n_samples):
                t = i / n_samples
                x = DRAW_X_MIN + t * (DRAW_X_MAX - DRAW_X_MIN)
                p = (self.freq * t + self.phase / (2 * math.pi)) % 1.0
                y_val = 4 * abs(p - 0.5) - 1.0
                y = CY - y_val * (HALF_H - 2)
                points.append((x, y))

        elif mode == 'SAWTOOTH':
            for i in range(n_samples):
                t = i / n_samples
                x = DRAW_X_MIN + t * (DRAW_X_MAX - DRAW_X_MIN)
                p = (self.freq * t + self.phase / (2 * math.pi)) % 1.0
                y_val = 2 * p - 1.0
                y = CY - y_val * (HALF_H - 2)
                points.append((x, y))

        elif mode == 'LISSAJOUS':
            a, b = RATIOS[self.ratio_idx]
            delta = self.phase * 0.5
            for i in range(n_samples):
                t = i / n_samples * 2 * math.pi
                x_val = math.sin(a * t + delta)
                y_val = math.sin(b * t)
                x = CX + x_val * (HALF_W - 2)
                y = CY - y_val * (HALF_H - 2)
                points.append((x, y))

        elif mode == 'SUPERPOSITION':
            f1 = self.freq
            f2 = self.freq * 1.5
            for i in range(n_samples):
                t = i / n_samples
                x = DRAW_X_MIN + t * (DRAW_X_MAX - DRAW_X_MIN)
                y_val = 0.5 * math.sin(2 * math.pi * f1 * t + self.phase)
                y_val += 0.5 * math.sin(2 * math.pi * f2 * t + self.phase * 0.7)
                y = CY - y_val * (HALF_H - 2)
                points.append((x, y))

        elif mode == 'FREQ SWEEP':
            for i in range(n_samples):
                t = i / n_samples
                x = DRAW_X_MIN + t * (DRAW_X_MAX - DRAW_X_MIN)
                y_val = math.sin(2 * math.pi * self.sweep_freq * t + self.phase)
                y = CY - y_val * (HALF_H - 2)
                points.append((x, y))

        elif mode == 'NOISE':
            prev_y = 0.0
            for i in range(n_samples):
                t = i / n_samples
                x = DRAW_X_MIN + t * (DRAW_X_MAX - DRAW_X_MIN)
                # Filtered noise: random walk smoothed by frequency
                prev_y += random.uniform(-0.3, 0.3)
                prev_y *= 0.95  # Decay toward center
                y_val = max(-1.0, min(1.0, prev_y))
                y = CY - y_val * (HALF_H - 2)
                points.append((x, y))

        return points

    def _draw_grid(self):
        """Draw oscilloscope grid."""
        d = self.display

        # Horizontal and vertical center axes
        for x in range(DRAW_X_MIN, DRAW_X_MAX + 1):
            d.set_pixel(x, CY, GRID_AXIS)
        for y in range(DRAW_Y_MIN, DRAW_Y_MAX + 1):
            d.set_pixel(CX, y, GRID_AXIS)

        # Grid divisions (every 8 pixels)
        for gx in range(DRAW_X_MIN, DRAW_X_MAX + 1, 8):
            for y in range(DRAW_Y_MIN, DRAW_Y_MAX + 1):
                d.set_pixel(gx, y, GRID_COLOR)
        for gy in range(DRAW_Y_MIN, DRAW_Y_MAX + 1, 8):
            for x in range(DRAW_X_MIN, DRAW_X_MAX + 1):
                d.set_pixel(x, gy, GRID_COLOR)

        # Tick marks on axes (every 8 pixels)
        for gx in range(DRAW_X_MIN, DRAW_X_MAX + 1, 8):
            for dy in range(-1, 2):
                d.set_pixel(gx, CY + dy, GRID_AXIS)
        for gy in range(DRAW_Y_MIN, DRAW_Y_MAX + 1, 8):
            for dx in range(-1, 2):
                d.set_pixel(CX + dx, gy, GRID_AXIS)

    def _draw_waveform(self, points, color):
        """Draw connected waveform points."""
        d = self.display
        for i in range(len(points) - 1):
            x0, y0 = int(round(points[i][0])), int(round(points[i][1]))
            x1, y1 = int(round(points[i + 1][0])), int(round(points[i + 1][1]))
            d.draw_line(x0, y0, x1, y1, color)

    def draw(self):
        d = self.display
        d.clear(Colors.BLACK)

        self._draw_grid()

        # Draw phosphor trails (oldest = dimmest)
        trail_colors = [PHOSPHOR_FAINT, PHOSPHOR_FAINT, PHOSPHOR_DIM,
                        PHOSPHOR_DIM, PHOSPHOR_MED, PHOSPHOR_MED]
        for i, old_points in enumerate(self.trail):
            ci = min(i, len(trail_colors) - 1)
            self._draw_waveform(old_points, trail_colors[ci])

        # Generate and draw current waveform
        current = self._generate_points()
        self._draw_waveform(current, PHOSPHOR_BRIGHT)

        # Update trail
        self.trail.append(current)
        if len(self.trail) > self.max_trail:
            self.trail.pop(0)

        # Bottom label
        mode = MODES[self.mode_idx]
        phase = int(self.label_timer / 4) % 2
        if phase == 0:
            label = mode
        else:
            if mode == 'LISSAJOUS':
                a, b = RATIOS[self.ratio_idx]
                label = f"RATIO {a}:{b}"
            elif mode == 'FREQ SWEEP':
                label = f"F={self.sweep_freq:.1f}"
            else:
                label = f"F={self.freq:.1f}"
        d.draw_text_small(2, 58, label, PHOSPHOR_BRIGHT)

        # Mode overlay
        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            oc = (0, int(255 * alpha), int(80 * alpha))
            d.draw_text_small(2, 2, mode, oc)
