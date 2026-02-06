"""
Equalizer - Stereo Spectrum Analyzer
=====================================
Bouncing stereo spectrum analyzer bars with peak-hold dots.
16 vertical bars (8 per channel, mirrored L/R) driven by layered
sine waves simulating kick/snare/hat patterns.

Controls:
  Left/Right - Adjust BPM (60-200)
  Up/Down    - Cycle style (Classic VU / Neon / Mono)
"""

import math
from . import Visual, Display, Colors, GRID_SIZE


class Equalizer(Visual):
    name = "EQUALIZER"
    description = "Spectrum analyzer"
    category = "music"

    NUM_BARS = 16
    BAR_WIDTH = 3       # pixels wide per bar
    BAR_GAP = 1         # gap between bars
    MAX_HEIGHT = 56      # max bar height in pixels
    TOP_MARGIN = 6       # leave room for label at top
    PEAK_GRAVITY = 40.0  # pixels/s^2 peak dot falls
    PEAK_HOLD = 0.4      # seconds before peak starts falling

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.bpm = 120
        self.style_index = 0
        self.style_names = ["VU", "NEON", "MONO"]

        # Current smoothed heights for each bar
        self.heights = [0.0] * self.NUM_BARS
        # Peak dot positions and velocities
        self.peaks = [0.0] * self.NUM_BARS
        self.peak_vel = [0.0] * self.NUM_BARS
        self.peak_hold = [0.0] * self.NUM_BARS

    def _beat_phase(self) -> float:
        """Return the current beat phase based on BPM."""
        beats_per_sec = self.bpm / 60.0
        return self.time * beats_per_sec * math.pi * 2

    def _target_height(self, bar_index: int) -> float:
        """
        Compute the target height for a bar using layered sine waves
        that simulate kick, snare, and hi-hat frequency bands.
        Bars 0-7 are left channel, 8-15 are right channel (mirrored).
        """
        # Mirror: bar 0 matches 15, bar 1 matches 14, etc.
        if bar_index < 8:
            freq_band = bar_index
        else:
            freq_band = 15 - bar_index

        bp = self._beat_phase()

        # Kick pattern: heavy on low bars (0-2), pulses on beats
        kick = math.sin(bp) * 0.5 + 0.5
        kick *= max(0.0, 1.0 - freq_band * 0.3)

        # Snare pattern: mid-range bars (2-5), off-beat emphasis
        snare = math.sin(bp * 2.0 + math.pi * 0.5) * 0.5 + 0.5
        snare *= max(0.0, 1.0 - abs(freq_band - 3.5) * 0.3)

        # Hi-hat pattern: high bars (5-7), fast 16th-note shimmer
        hat = (math.sin(bp * 4.0) * 0.3 + 0.3)
        hat += (math.sin(bp * 8.0 + 1.0) * 0.2)
        hat = max(0.0, hat)
        hat *= max(0.0, (freq_band - 4.0) * 0.25)

        # Add some variation per bar with slower modulation
        variation = math.sin(self.time * 1.3 + bar_index * 0.7) * 0.15 + 0.1
        variation += math.sin(self.time * 0.7 + bar_index * 1.1) * 0.1

        # Stereo offset: slight phase difference between L and R
        if bar_index >= 8:
            stereo = math.sin(self.time * 0.5) * 0.08
        else:
            stereo = -math.sin(self.time * 0.5) * 0.08

        raw = kick + snare + hat + variation + stereo
        raw = max(0.0, min(1.0, raw))

        return raw * self.MAX_HEIGHT

    def _vu_color(self, y_from_bottom: int, bar_height: int) -> tuple:
        """Classic VU meter: green at bottom, yellow in middle, red at top."""
        if bar_height < 1:
            return (0, 40, 0)
        frac = y_from_bottom / self.MAX_HEIGHT
        if frac < 0.5:
            # Green zone
            g = 180 + int(frac * 2 * 75)
            return (0, g, 0)
        elif frac < 0.75:
            # Yellow zone
            t = (frac - 0.5) / 0.25
            return (200 + int(t * 55), 255 - int(t * 60), 0)
        else:
            # Red zone
            t = (frac - 0.75) / 0.25
            return (255, max(0, 195 - int(t * 195)), 0)

    def _neon_color(self, y_from_bottom: int, bar_height: int) -> tuple:
        """Neon style: cyan to magenta gradient."""
        if bar_height < 1:
            return (0, 10, 20)
        frac = y_from_bottom / self.MAX_HEIGHT
        if frac < 0.5:
            t = frac * 2
            r = int(t * 180)
            g = 50 + int((1 - t) * 200)
            b = 255
            return (r, g, b)
        else:
            t = (frac - 0.5) * 2
            r = 180 + int(t * 75)
            g = int((1 - t) * 50)
            b = 255 - int(t * 80)
            return (r, g, b)

    def _mono_color(self, y_from_bottom: int, bar_height: int) -> tuple:
        """Mono green style: single color with brightness gradient."""
        if bar_height < 1:
            return (0, 20, 0)
        frac = y_from_bottom / self.MAX_HEIGHT
        brightness = 0.4 + frac * 0.6
        return (0, int(255 * brightness), int(40 * brightness))

    def _bar_color(self, y_from_bottom: int, bar_height: int) -> tuple:
        """Get bar color based on current style."""
        if self.style_index == 0:
            return self._vu_color(y_from_bottom, bar_height)
        elif self.style_index == 1:
            return self._neon_color(y_from_bottom, bar_height)
        else:
            return self._mono_color(y_from_bottom, bar_height)

    def _peak_color(self) -> tuple:
        """Get peak dot color based on current style."""
        if self.style_index == 0:
            return (255, 255, 255)  # White
        elif self.style_index == 1:
            return (255, 255, 0)    # Yellow
        else:
            return (200, 255, 200)  # Pale green

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Adjust BPM
        if input_state.right_pressed:
            self.bpm = min(200, self.bpm + 10)
            consumed = True
        if input_state.left_pressed:
            self.bpm = max(60, self.bpm - 10)
            consumed = True

        # Cycle style
        if input_state.up_pressed:
            self.style_index = (self.style_index + 1) % len(self.style_names)
            consumed = True
        if input_state.down_pressed:
            self.style_index = (self.style_index - 1) % len(self.style_names)
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt

        for i in range(self.NUM_BARS):
            target = self._target_height(i)

            # Smooth interpolation toward target
            self.heights[i] += (target - self.heights[i]) * dt * 12

            # Peak dot logic
            h = self.heights[i]
            if h >= self.peaks[i]:
                # New peak reached
                self.peaks[i] = h
                self.peak_vel[i] = 0.0
                self.peak_hold[i] = self.PEAK_HOLD
            else:
                # Hold, then fall with gravity
                if self.peak_hold[i] > 0:
                    self.peak_hold[i] -= dt
                else:
                    self.peak_vel[i] += self.PEAK_GRAVITY * dt
                    self.peaks[i] -= self.peak_vel[i] * dt
                    if self.peaks[i] < 0:
                        self.peaks[i] = 0.0
                        self.peak_vel[i] = 0.0

    def draw(self):
        self.display.clear(Colors.BLACK)

        base_y = GRID_SIZE - 1  # Bottom of screen

        # Draw each bar
        for i in range(self.NUM_BARS):
            x_start = i * (self.BAR_WIDTH + self.BAR_GAP)
            bar_h = int(self.heights[i])

            # Draw filled bar from bottom up
            for y_off in range(bar_h):
                y = base_y - y_off
                if y < self.TOP_MARGIN:
                    break
                color = self._bar_color(y_off, bar_h)
                for bx in range(self.BAR_WIDTH):
                    x = x_start + bx
                    if 0 <= x < GRID_SIZE:
                        self.display.set_pixel(x, y, color)

            # Draw peak dot
            peak_y = base_y - int(self.peaks[i])
            if self.TOP_MARGIN <= peak_y < GRID_SIZE:
                pc = self._peak_color()
                for bx in range(self.BAR_WIDTH):
                    x = x_start + bx
                    if 0 <= x < GRID_SIZE:
                        self.display.set_pixel(x, peak_y, pc)

        # Draw label at top
        label = "%d BPM  %s" % (self.bpm, self.style_names[self.style_index])
        self.display.draw_text_small(2, 0, label, (100, 100, 100))
