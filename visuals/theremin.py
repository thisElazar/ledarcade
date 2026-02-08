"""
Theremin - Electronic Musical Instrument Visualization
======================================================
Side view of a theremin with pitch antenna, volume loop,
moving hands, EM field arcs, and a scrolling waveform display.

Controls:
  Button     - Toggle user mode (manual hand control)

  Auto mode:
    Left/Right - Adjust hand oscillation speed
    Up/Down    - Cycle waveform type (Sine/Square/Triangle/Sawtooth)

  User mode:
    Left/Right - Control volume hand (left hand, affects volume)
    Up/Down    - Control pitch hand (right hand, affects frequency)
"""

import math
from . import Visual, Display, Colors, GRID_SIZE

# Waveform types
WAVE_TYPES = ['SINE', 'SQUARE', 'TRIANGLE', 'SAW']

# Colors
BODY_COLOR = (60, 40, 30)
BODY_HIGHLIGHT = (90, 65, 45)
ANTENNA_COLOR = (180, 180, 190)
ANTENNA_TIP = (220, 220, 240)
LOOP_COLOR = (160, 160, 170)
HAND_COLOR = (220, 180, 140)
HAND_OUTLINE = (160, 120, 90)
FIELD_BASE = (140, 50, 200)      # Purple EM field
LABEL_COLOR = (180, 180, 200)
WAVE_AREA_TOP = 43
WAVE_AREA_BOT = 62
BG_COLOR = (5, 5, 12)


class Theremin(Visual):
    name = "THEREMIN"
    description = "Electronic theremin instrument"
    category = "music"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.hand_speed = 1.0
        self.wave_idx = 0
        self.overlay_timer = 0.0
        self.overlay_text = ''
        # Waveform scroll buffer (stores columns of y-values)
        self.wave_buffer = []
        self.wave_width = GRID_SIZE  # 64 columns

        # User control mode
        self.user_mode = False
        self.pitch_hand_x = 50.0
        self.pitch_hand_y = 18.0
        self.volume_hand_x = 18.0
        self.volume_hand_y = 28.0

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Button press: toggle user mode
        if input_state.action_l or input_state.action_r:
            self.user_mode = not self.user_mode
            self.overlay_text = 'USER MODE' if self.user_mode else 'AUTO MODE'
            self.overlay_timer = 2.0
            # Sync user positions with current auto positions when entering user mode
            if self.user_mode:
                self.pitch_hand_x, self.pitch_hand_y = self._auto_pitch_hand_pos()
                self.volume_hand_x, self.volume_hand_y = self._auto_volume_hand_pos()
            consumed = True

        if self.user_mode:
            # User mode: joystick controls both hands
            # Left/Right: control volume hand (left hand) horizontally
            if input_state.left:
                self.volume_hand_x = max(4, self.volume_hand_x - 40.0 * 0.016)
                consumed = True
            if input_state.right:
                self.volume_hand_x = min(28, self.volume_hand_x + 40.0 * 0.016)
                consumed = True
            # Up/Down: control pitch hand (right hand) vertically
            if input_state.up:
                self.pitch_hand_y = max(4, self.pitch_hand_y - 40.0 * 0.016)
                consumed = True
            if input_state.down:
                self.pitch_hand_y = min(38, self.pitch_hand_y + 40.0 * 0.016)
                consumed = True
        else:
            # Auto mode: original controls
            if input_state.left_pressed:
                self.hand_speed = max(0.3, self.hand_speed - 0.2)
                consumed = True
            if input_state.right_pressed:
                self.hand_speed = min(3.0, self.hand_speed + 0.2)
                consumed = True
            if input_state.up_pressed:
                self.wave_idx = (self.wave_idx - 1) % len(WAVE_TYPES)
                self.overlay_text = WAVE_TYPES[self.wave_idx]
                self.overlay_timer = 2.0
                consumed = True
            if input_state.down_pressed:
                self.wave_idx = (self.wave_idx + 1) % len(WAVE_TYPES)
                self.overlay_text = WAVE_TYPES[self.wave_idx]
                self.overlay_timer = 2.0
                consumed = True

        return consumed

    # -- Hand position helpers --

    def _auto_pitch_hand_pos(self):
        """Right hand auto position - sinusoidal vertical motion."""
        t = self.time * self.hand_speed * 0.7
        # Oscillates vertically near antenna (right side)
        base_x = 50
        base_y = 18
        x = base_x + 2.0 * math.sin(t * 1.3)
        y = base_y + 10.0 * math.sin(t * 0.6)
        return x, y

    def _auto_volume_hand_pos(self):
        """Left hand auto position - sinusoidal horizontal motion."""
        t = self.time * self.hand_speed * 0.5
        base_x = 18
        base_y = 28
        x = base_x + 6.0 * math.sin(t * 0.8)
        y = base_y + 3.0 * math.sin(t * 1.1)
        return x, y

    def _pitch_hand_pos(self):
        """Right hand position - auto or user controlled."""
        if self.user_mode:
            return self.pitch_hand_x, self.pitch_hand_y
        return self._auto_pitch_hand_pos()

    def _volume_hand_pos(self):
        """Left hand position - auto or user controlled."""
        if self.user_mode:
            return self.volume_hand_x, self.volume_hand_y
        return self._auto_volume_hand_pos()

    def _get_frequency(self):
        """Derive frequency from pitch hand distance to antenna tip."""
        px, py = self._pitch_hand_pos()
        antenna_tip_x, antenna_tip_y = 56, 4
        dist = math.sqrt((px - antenna_tip_x) ** 2 + (py - antenna_tip_y) ** 2)
        # Closer = higher frequency (range 1-8 Hz visual)
        freq = max(1.0, min(8.0, 30.0 / (dist + 2.0)))
        return freq

    def _get_amplitude(self):
        """Derive amplitude from volume hand distance to loop."""
        vx, vy = self._volume_hand_pos()
        loop_cx, loop_cy = 10, 30
        dist = math.sqrt((vx - loop_cx) ** 2 + (vy - loop_cy) ** 2)
        # Closer = louder (range 0.1-1.0)
        amp = max(0.1, min(1.0, 1.0 - dist / 25.0))
        return amp

    # -- Waveform generation --

    def _wave_sample(self, phase, freq, amp):
        """Generate a single waveform sample based on current type."""
        wtype = WAVE_TYPES[self.wave_idx]
        if wtype == 'SINE':
            return amp * math.sin(phase)
        elif wtype == 'SQUARE':
            return amp * (1.0 if math.sin(phase) >= 0 else -1.0)
        elif wtype == 'TRIANGLE':
            p = (phase / (2 * math.pi)) % 1.0
            return amp * (4.0 * abs(p - 0.5) - 1.0)
        elif wtype == 'SAW':
            p = (phase / (2 * math.pi)) % 1.0
            return amp * (2.0 * p - 1.0)
        return 0.0

    def _freq_to_color(self, freq):
        """Map frequency to a color - low=blue, mid=green, high=red/yellow."""
        t = (freq - 1.0) / 7.0  # 0..1
        if t < 0.33:
            f = t / 0.33
            return (int(50 * (1 - f)), int(100 + 155 * f), 255)
        elif t < 0.66:
            f = (t - 0.33) / 0.33
            return (int(80 * f), 255, int(255 * (1 - f)))
        else:
            f = (t - 0.66) / 0.34
            return (255, int(255 * (1 - f * 0.5)), int(50 * (1 - f)))

    # -- Update --

    def update(self, dt: float):
        self.time += dt

        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

        freq = self._get_frequency()
        amp = self._get_amplitude()

        # Push a new waveform column
        phase = self.time * freq * 2.0 * math.pi * 0.3
        sample = self._wave_sample(phase, freq, amp)
        self.wave_buffer.append((sample, freq))

        # Keep buffer at display width
        if len(self.wave_buffer) > self.wave_width:
            self.wave_buffer.pop(0)

    # -- Drawing --

    def _draw_body(self):
        """Draw theremin body (wooden box on table)."""
        d = self.display
        # Main body - rectangular box
        d.draw_rect(22, 30, 36, 8, BODY_COLOR, filled=True)
        # Top surface highlight
        d.draw_line(22, 30, 57, 30, BODY_HIGHLIGHT)
        d.draw_line(22, 31, 57, 31, BODY_HIGHLIGHT)
        # Front panel detail
        d.draw_rect(28, 33, 6, 3, (40, 30, 22), filled=True)
        # Knobs
        d.set_pixel(30, 34, (100, 80, 60))
        d.set_pixel(32, 34, (100, 80, 60))

    def _draw_pitch_antenna(self):
        """Draw vertical pitch antenna on right side."""
        d = self.display
        # Vertical rod from body top upward
        ax = 56
        for y in range(4, 31):
            d.set_pixel(ax, y, ANTENNA_COLOR)
        # Antenna tip (bright)
        d.set_pixel(ax, 4, ANTENNA_TIP)
        d.set_pixel(ax, 5, ANTENNA_TIP)
        d.set_pixel(ax - 1, 4, ANTENNA_TIP)
        d.set_pixel(ax + 1, 4, ANTENNA_TIP)

    def _draw_volume_loop(self):
        """Draw horizontal volume loop arc on left side."""
        d = self.display
        # Horizontal rod from body
        for x in range(10, 23):
            d.set_pixel(x, 32, LOOP_COLOR)
        # Arc/loop at end
        d.draw_circle(10, 30, 3, LOOP_COLOR, filled=False)

    def _draw_hand(self, x, y):
        """Draw a small hand sprite (5x4 pixels)."""
        d = self.display
        ix, iy = int(round(x)), int(round(y))
        # Simple hand shape: palm + fingers
        # Palm (3x3)
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                px, py = ix + dx, iy + dy
                if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                    d.set_pixel(px, py, HAND_COLOR)
        # Fingers (extending upward/toward antenna)
        for dx in range(-1, 2):
            px, py = ix + dx, iy - 2
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                d.set_pixel(px, py, HAND_OUTLINE)
        # Thumb
        px, py = ix - 2, iy
        if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
            d.set_pixel(px, py, HAND_OUTLINE)

    def _draw_em_field(self):
        """Draw pulsing EM field arcs from the antenna tip."""
        d = self.display
        tip_x, tip_y = 56, 4
        # Draw concentric arcs expanding outward
        num_arcs = 4
        for i in range(num_arcs):
            # Phase offset so arcs pulse outward over time
            r = ((self.time * 8.0 + i * 4.0) % 16.0) + 2.0
            # Fade intensity with distance
            fade = max(0.0, 1.0 - r / 18.0)
            if fade <= 0:
                continue
            color = (
                int(FIELD_BASE[0] * fade),
                int(FIELD_BASE[1] * fade),
                int(FIELD_BASE[2] * fade),
            )
            # Draw arc (left half of circle from antenna tip)
            steps = 20
            for s in range(steps):
                # Arc from -PI to 0 (left/upper side of antenna)
                angle = math.pi + (math.pi * s / (steps - 1))
                ax = int(round(tip_x + r * math.cos(angle)))
                ay = int(round(tip_y + r * math.sin(angle)))
                if 0 <= ax < GRID_SIZE and 0 <= ay < GRID_SIZE:
                    d.set_pixel(ax, ay, color)

    def _draw_waveform(self):
        """Draw scrolling waveform in bottom display area."""
        d = self.display
        wave_h = WAVE_AREA_BOT - WAVE_AREA_TOP
        mid_y = WAVE_AREA_TOP + wave_h // 2

        # Dark background for wave area
        d.draw_rect(0, WAVE_AREA_TOP, GRID_SIZE, wave_h, (8, 8, 20), filled=True)
        # Separator line
        d.draw_line(0, WAVE_AREA_TOP, GRID_SIZE - 1, WAVE_AREA_TOP, (30, 30, 60))

        # Center line (zero crossing)
        for x in range(0, GRID_SIZE, 2):
            d.set_pixel(x, mid_y, (20, 20, 40))

        if len(self.wave_buffer) < 2:
            return

        # Draw waveform from buffer (right-aligned, newest on right)
        buf_len = len(self.wave_buffer)
        half_h = (wave_h // 2) - 1
        prev_y = None

        for x in range(GRID_SIZE):
            buf_idx = buf_len - GRID_SIZE + x
            if buf_idx < 0:
                continue
            sample, freq = self.wave_buffer[buf_idx]
            # Map sample (-1..1) to pixel y
            py = mid_y - int(sample * half_h)
            py = max(WAVE_AREA_TOP + 1, min(WAVE_AREA_BOT - 1, py))

            color = self._freq_to_color(freq)

            if prev_y is not None:
                # Draw vertical line between previous and current for continuity
                y0 = min(prev_y, py)
                y1 = max(prev_y, py)
                for yy in range(y0, y1 + 1):
                    if WAVE_AREA_TOP < yy < WAVE_AREA_BOT:
                        d.set_pixel(x, yy, color)
            else:
                if WAVE_AREA_TOP < py < WAVE_AREA_BOT:
                    d.set_pixel(x, py, color)

            prev_y = py

    def _draw_label(self):
        """Draw waveform type label or mode indicator at top."""
        d = self.display
        wtype = WAVE_TYPES[self.wave_idx]
        freq = self._get_frequency()

        if self.overlay_timer > 0:
            # Show overlay text (mode or waveform change)
            alpha = min(1.0, self.overlay_timer / 0.5)
            c = (int(255 * alpha), int(255 * alpha), int(255 * alpha))
            d.draw_text_small(2, 0, self.overlay_text, c)
        else:
            # Show mode indicator or alternate info
            if self.user_mode:
                d.draw_text_small(2, 0, "USER", (100, 255, 100))
            else:
                # Alternate between type and frequency display
                phase = int(self.time / 3) % 2
                if phase == 0:
                    d.draw_text_small(2, 0, wtype, (60, 60, 80))
                else:
                    d.draw_text_small(2, 0, f"F={freq:.1f}", (60, 60, 80))

    def draw(self):
        d = self.display
        d.clear(BG_COLOR)

        # Draw instrument components
        self._draw_em_field()
        self._draw_body()
        self._draw_pitch_antenna()
        self._draw_volume_loop()

        # Draw hands
        px, py = self._pitch_hand_pos()
        self._draw_hand(px, py)
        vx, vy = self._volume_hand_pos()
        self._draw_hand(vx, vy)

        # Draw waveform display
        self._draw_waveform()

        # Draw label
        self._draw_label()
