"""
Synthesizer - Modular Synth Panel
=================================
A modular synthesizer front panel with animated oscillators, rotating knobs,
blinking LED indicators, a patch bay with colorful cables, and a VU meter.

Controls:
  Left/Right - Adjust master frequency
  Up/Down    - Cycle patch cable preset
"""

import math
from . import Visual, Display, Colors, GRID_SIZE


# --- Color Palette ---
PANEL_BG = (25, 25, 30)
PANEL_DARK = (15, 15, 18)
PANEL_LINE = (45, 45, 55)
PANEL_LABEL = (120, 120, 140)

# Oscillator waveform colors
OSC_SINE_COLOR = (0, 220, 120)
OSC_SAW_COLOR = (255, 160, 0)
OSC_SQUARE_COLOR = (80, 160, 255)
OSC_BG = (10, 10, 14)
OSC_BORDER = (60, 60, 70)

# Knob colors
KNOB_BODY = (50, 50, 60)
KNOB_RING = (70, 70, 85)
KNOB_POINTER = (255, 255, 255)
KNOB_DOT = (200, 200, 220)

# LED colors
LED_RED = (255, 30, 20)
LED_RED_DIM = (80, 10, 8)
LED_GREEN = (30, 255, 50)
LED_GREEN_DIM = (10, 80, 16)
LED_YELLOW = (255, 220, 30)
LED_YELLOW_DIM = (80, 70, 10)
LED_BLUE = (40, 100, 255)
LED_BLUE_DIM = (12, 30, 80)

# Patch bay colors
JACK_COLOR = (90, 90, 100)
JACK_HOLE = (20, 20, 25)

# Patch cable colors (per preset)
CABLE_COLORS = [
    [(255, 50, 50), (50, 255, 100), (80, 150, 255), (255, 200, 50)],
    [(255, 100, 200), (100, 255, 255), (255, 150, 50), (180, 100, 255)],
    [(50, 255, 50), (255, 80, 80), (255, 255, 100), (150, 200, 255)],
    [(200, 50, 255), (255, 200, 100), (50, 200, 200), (255, 100, 100)],
]

# Cable routing presets: each is a list of (src_jack, dst_jack) index pairs
CABLE_PRESETS = [
    [(0, 8), (2, 10), (4, 9), (6, 11)],
    [(1, 9), (3, 11), (5, 8), (7, 10)],
    [(0, 11), (1, 10), (3, 9), (5, 8)],
    [(2, 8), (4, 11), (6, 9), (7, 10)],
]

# VU meter colors
VU_GREEN = (0, 200, 60)
VU_YELLOW = (220, 200, 0)
VU_RED = (255, 30, 20)
VU_BG = (20, 20, 24)

# Layout constants
OSC_Y = 2
OSC_H = 12
OSC_W = 18

KNOB_ROW_Y = 18
KNOB_SPACING = 9
KNOB_R = 3

LED_ROW_Y = 30
LED_SPACING = 4

PATCH_Y = 36
PATCH_ROWS = 2
PATCH_COLS = 4
JACK_SPACING_X = 14
JACK_SPACING_Y = 8
PATCH_X_START = 5

VU_Y = 54
VU_X = 2
VU_W = 44
VU_H = 4

FREQ_X = 49
FREQ_Y = 55


class Synthesizer(Visual):
    name = "SYNTHESIZER"
    description = "Modular synth panel"
    category = "music"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.master_freq = 440.0
        self.min_freq = 100.0
        self.max_freq = 2000.0
        self.patch_preset = 0
        self.clock_phase = 0.0
        self.clock_bpm = 120.0

        # Knob angles (radians) - 7 knobs across the panel
        self.num_knobs = 7
        self.knob_angles = [0.0] * self.num_knobs
        self.knob_speeds = [0.3, -0.5, 0.7, -0.4, 0.6, -0.35, 0.55]

        # LED states (16 LEDs in a row)
        self.num_leds = 16
        self.led_brightness = [0.0] * self.num_leds

        # VU meter level (0 to 1)
        self.vu_level = 0.0
        self.vu_target = 0.5

        # Patch jack positions (row-major, 2 rows x 4 cols = 8 top + 4 bottom)
        self.jack_positions = []
        for row in range(PATCH_ROWS + 1):
            for col in range(PATCH_COLS):
                jx = PATCH_X_START + col * JACK_SPACING_X + 3
                jy = PATCH_Y + row * JACK_SPACING_Y + 2
                self.jack_positions.append((jx, jy))

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Left/Right - adjust master frequency
        if input_state.left:
            self.master_freq = max(self.min_freq, self.master_freq - 5.0)
            consumed = True
        if input_state.right:
            self.master_freq = min(self.max_freq, self.master_freq + 5.0)
            consumed = True

        # Up/Down - cycle patch preset
        if input_state.up_pressed:
            self.patch_preset = (self.patch_preset + 1) % len(CABLE_PRESETS)
            consumed = True
        if input_state.down_pressed:
            self.patch_preset = (self.patch_preset - 1) % len(CABLE_PRESETS)
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt

        # Advance clock
        self.clock_phase += dt * (self.clock_bpm / 60.0) * 2.0 * math.pi

        # Rotate knobs
        freq_factor = self.master_freq / 440.0
        for i in range(self.num_knobs):
            self.knob_angles[i] += self.knob_speeds[i] * freq_factor * dt

        # Update LED pattern (sequencer-style chase synced to clock)
        step = int((self.clock_phase / (2.0 * math.pi)) * self.num_leds) % self.num_leds
        for i in range(self.num_leds):
            if i == step:
                self.led_brightness[i] = 1.0
            elif i == (step - 1) % self.num_leds:
                self.led_brightness[i] = max(self.led_brightness[i] - dt * 6.0, 0.0)
            elif i == (step - 2) % self.num_leds:
                self.led_brightness[i] = max(self.led_brightness[i] - dt * 4.0, 0.0)
            else:
                self.led_brightness[i] = max(self.led_brightness[i] - dt * 8.0, 0.0)

        # VU meter bouncing
        self.vu_target = 0.4 + 0.35 * math.sin(self.time * 1.7) + 0.15 * math.sin(self.time * 3.1)
        self.vu_target = max(0.0, min(1.0, self.vu_target))
        # Smooth follow with faster attack, slower decay
        if self.vu_target > self.vu_level:
            self.vu_level += (self.vu_target - self.vu_level) * min(1.0, dt * 12.0)
        else:
            self.vu_level += (self.vu_target - self.vu_level) * min(1.0, dt * 4.0)

    def draw(self):
        d = self.display
        d.clear(PANEL_BG)

        self._draw_oscillators(d)
        self._draw_knobs(d)
        self._draw_leds(d)
        self._draw_patch_bay(d)
        self._draw_vu_meter(d)
        self._draw_freq_display(d)

    # ----- Oscillator Section -----

    def _draw_oscillators(self, d):
        """Draw 3 mini oscillator waveform displays side by side."""
        osc_configs = [
            ("SIN", OSC_SINE_COLOR, self._wave_sine),
            ("SAW", OSC_SAW_COLOR, self._wave_saw),
            ("SQR", OSC_SQUARE_COLOR, self._wave_square),
        ]
        for i, (label, color, wave_fn) in enumerate(osc_configs):
            ox = 2 + i * 21
            oy = OSC_Y

            # Background box
            d.draw_rect(ox, oy, OSC_W, OSC_H, OSC_BG)
            # Border
            d.draw_rect(ox, oy, OSC_W, OSC_H, OSC_BORDER, filled=False)

            # Center line
            cy = oy + OSC_H // 2
            for x in range(ox + 1, ox + OSC_W - 1, 2):
                d.set_pixel(x, cy, (30, 30, 35))

            # Draw waveform
            freq_factor = self.master_freq / 440.0
            for px in range(OSC_W - 2):
                t = px / (OSC_W - 3)
                val = wave_fn(t * 2.0 * math.pi * freq_factor + self.time * 4.0)
                amplitude = (OSC_H // 2) - 2
                sy = cy - int(val * amplitude)
                sy = max(oy + 1, min(oy + OSC_H - 2, sy))
                d.set_pixel(ox + 1 + px, sy, color)
                # Vertical connection to next point for cleaner look
                if px > 0:
                    prev_val = wave_fn((px - 1) / (OSC_W - 3) * 2.0 * math.pi * freq_factor + self.time * 4.0)
                    prev_sy = cy - int(prev_val * amplitude)
                    prev_sy = max(oy + 1, min(oy + OSC_H - 2, prev_sy))
                    if abs(sy - prev_sy) > 1:
                        step = 1 if sy > prev_sy else -1
                        for fill_y in range(prev_sy, sy, step):
                            fill_y_c = max(oy + 1, min(oy + OSC_H - 2, fill_y))
                            d.set_pixel(ox + 1 + px, fill_y_c, color)

            # Label below waveform
            d.draw_text_small(ox + 2, oy + OSC_H + 1, label, PANEL_LABEL)

    def _wave_sine(self, t):
        return math.sin(t)

    def _wave_saw(self, t):
        return 2.0 * ((t / (2.0 * math.pi)) % 1.0) - 1.0

    def _wave_square(self, t):
        return 1.0 if math.sin(t) >= 0 else -1.0

    # ----- Knob Grid -----

    def _draw_knobs(self, d):
        """Draw a row of circular knobs with rotating pointer dots."""
        for i in range(self.num_knobs):
            cx = 5 + i * KNOB_SPACING
            cy = KNOB_ROW_Y + KNOB_R + 1

            # Knob body (filled circle)
            d.draw_circle(cx, cy, KNOB_R, KNOB_BODY, filled=True)
            # Knob ring (circle outline)
            d.draw_circle(cx, cy, KNOB_R, KNOB_RING, filled=False)

            # Pointer dot (rotating around knob)
            angle = self.knob_angles[i]
            px = cx + int(round((KNOB_R - 1) * math.cos(angle)))
            py = cy + int(round((KNOB_R - 1) * math.sin(angle)))
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                d.set_pixel(px, py, KNOB_POINTER)

    # ----- LED Indicators -----

    def _draw_leds(self, d):
        """Draw a row of blinking LED indicators."""
        led_colors_on = [LED_RED, LED_GREEN, LED_YELLOW, LED_BLUE]
        led_colors_dim = [LED_RED_DIM, LED_GREEN_DIM, LED_YELLOW_DIM, LED_BLUE_DIM]

        for i in range(self.num_leds):
            lx = 2 + i * LED_SPACING
            ly = LED_ROW_Y

            if lx >= GRID_SIZE - 1:
                break

            ci = i % len(led_colors_on)
            brightness = self.led_brightness[i]

            if brightness > 0.5:
                color = led_colors_on[ci]
            elif brightness > 0.1:
                # Blend between dim and on
                t = (brightness - 0.1) / 0.4
                on = led_colors_on[ci]
                dim = led_colors_dim[ci]
                color = (
                    int(dim[0] + (on[0] - dim[0]) * t),
                    int(dim[1] + (on[1] - dim[1]) * t),
                    int(dim[2] + (on[2] - dim[2]) * t),
                )
            else:
                color = led_colors_dim[ci]

            d.set_pixel(lx, ly, color)
            d.set_pixel(lx + 1, ly, color)
            d.set_pixel(lx, ly + 1, color)
            d.set_pixel(lx + 1, ly + 1, color)

    # ----- Patch Bay -----

    def _draw_patch_bay(self, d):
        """Draw patch bay jacks and cables."""
        # Draw separator line
        d.draw_line(0, PATCH_Y - 1, 63, PATCH_Y - 1, PANEL_LINE)

        # Draw label
        d.draw_text_small(2, PATCH_Y, "PATCH", PANEL_LABEL)

        # Draw jack sockets
        for idx, (jx, jy) in enumerate(self.jack_positions):
            if jx >= GRID_SIZE - 1 or jy >= GRID_SIZE - 1:
                continue
            # Outer ring
            d.set_pixel(jx - 1, jy, JACK_COLOR)
            d.set_pixel(jx + 1, jy, JACK_COLOR)
            d.set_pixel(jx, jy - 1, JACK_COLOR)
            d.set_pixel(jx, jy + 1, JACK_COLOR)
            # Center hole
            d.set_pixel(jx, jy, JACK_HOLE)

        # Draw patch cables
        preset = CABLE_PRESETS[self.patch_preset]
        colors = CABLE_COLORS[self.patch_preset]

        for cable_idx, (src, dst) in enumerate(preset):
            if src >= len(self.jack_positions) or dst >= len(self.jack_positions):
                continue
            sx, sy = self.jack_positions[src]
            dx, dy = self.jack_positions[dst]
            cable_color = colors[cable_idx % len(colors)]

            # Draw curved cable using quadratic Bezier
            # Control point: midpoint shifted down for sag
            mx = (sx + dx) // 2
            sag = 4 + (cable_idx % 3) * 2
            my = max(sy, dy) + sag

            # Sample the Bezier curve
            prev_px, prev_py = sx, sy
            num_steps = 20
            for step in range(1, num_steps + 1):
                t = step / num_steps
                inv_t = 1.0 - t
                # Quadratic Bezier: B(t) = (1-t)^2*P0 + 2*(1-t)*t*P1 + t^2*P2
                bx = inv_t * inv_t * sx + 2 * inv_t * t * mx + t * t * dx
                by = inv_t * inv_t * sy + 2 * inv_t * t * my + t * t * dy
                px = int(round(bx))
                py = int(round(by))
                px = max(0, min(GRID_SIZE - 1, px))
                py = max(0, min(GRID_SIZE - 1, py))
                d.draw_line(prev_px, prev_py, px, py, cable_color)
                prev_px, prev_py = px, py

            # Bright dots at cable endpoints
            d.set_pixel(sx, sy, cable_color)
            d.set_pixel(dx, dy, cable_color)

    # ----- VU Meter -----

    def _draw_vu_meter(self, d):
        """Draw a horizontal VU meter bar."""
        # Background
        d.draw_rect(VU_X, VU_Y, VU_W, VU_H, VU_BG)

        # Filled bar based on level
        fill_w = int(self.vu_level * VU_W)
        for px in range(fill_w):
            frac = px / VU_W
            if frac < 0.6:
                color = VU_GREEN
            elif frac < 0.8:
                color = VU_YELLOW
            else:
                color = VU_RED
            for py in range(VU_H):
                d.set_pixel(VU_X + px, VU_Y + py, color)

        # Border
        d.draw_rect(VU_X, VU_Y, VU_W, VU_H, PANEL_LINE, filled=False)

        # VU label
        d.draw_text_small(VU_X, VU_Y - 5, "VU", PANEL_LABEL)

    # ----- Frequency Display -----

    def _draw_freq_display(self, d):
        """Draw the master frequency readout."""
        freq_int = int(self.master_freq)
        d.draw_text_small(FREQ_X, FREQ_Y, str(freq_int), (0, 255, 120))
        d.draw_text_small(FREQ_X, FREQ_Y + 5, "Hz", PANEL_LABEL)
