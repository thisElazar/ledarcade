"""
Clock - Animated time display
=============================
Shows current time with animated effects.

Controls:
  Space - Toggle between digital and analog mode
  Escape - Exit
"""

import math
import time as time_module
from . import Visual, Display, Colors, GRID_SIZE


class Clock(Visual):
    name = "CLOCK"
    description = "Animated clock"
    category = "utility"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.analog_mode = False
        self.color_cycle = 0.0

    def handle_input(self, input_state) -> bool:
        if (input_state.action_l or input_state.action_r):
            self.analog_mode = not self.analog_mode
            return True
        if (input_state.up_pressed or input_state.down_pressed or
                input_state.left_pressed or input_state.right_pressed):
            self.wants_exit = True
            return True
        return False

    def update(self, dt: float):
        self.time += dt
        self.color_cycle += dt * 0.1

    def _get_cycle_color(self):
        """Get a color that cycles over time."""
        h = (self.color_cycle % 1.0) * 6.0
        i = int(h)
        f = h - i

        if i == 0:
            return (255, int(255 * f), 0)
        elif i == 1:
            return (int(255 * (1 - f)), 255, 0)
        elif i == 2:
            return (0, 255, int(255 * f))
        elif i == 3:
            return (0, int(255 * (1 - f)), 255)
        elif i == 4:
            return (int(255 * f), 0, 255)
        else:
            return (255, 0, int(255 * (1 - f)))

    def _draw_digit_large(self, x, y, digit, color):
        """Draw a large 7-segment style digit (8x12 pixels)."""
        # Segment patterns for 0-9
        # Segments: top, top-left, top-right, middle, bot-left, bot-right, bottom
        segments = [
            [1,1,1,0,1,1,1],  # 0
            [0,0,1,0,0,1,0],  # 1
            [1,0,1,1,1,0,1],  # 2
            [1,0,1,1,0,1,1],  # 3
            [0,1,1,1,0,1,0],  # 4
            [1,1,0,1,0,1,1],  # 5
            [1,1,0,1,1,1,1],  # 6
            [1,0,1,0,0,1,0],  # 7
            [1,1,1,1,1,1,1],  # 8
            [1,1,1,1,0,1,1],  # 9
        ]

        seg = segments[digit]

        # Draw horizontal segments (6 wide, 2 tall)
        if seg[0]:  # top
            self.display.draw_rect(x + 1, y, 6, 2, color)
        if seg[3]:  # middle
            self.display.draw_rect(x + 1, y + 5, 6, 2, color)
        if seg[6]:  # bottom
            self.display.draw_rect(x + 1, y + 10, 6, 2, color)

        # Draw vertical segments (2 wide, 4 tall)
        if seg[1]:  # top-left
            self.display.draw_rect(x, y + 1, 2, 4, color)
        if seg[2]:  # top-right
            self.display.draw_rect(x + 6, y + 1, 2, 4, color)
        if seg[4]:  # bottom-left
            self.display.draw_rect(x, y + 6, 2, 4, color)
        if seg[5]:  # bottom-right
            self.display.draw_rect(x + 6, y + 6, 2, 4, color)

    def _draw_digital(self):
        """Draw digital clock display."""
        now = time_module.localtime()
        hour = now.tm_hour
        minute = now.tm_min
        second = now.tm_sec

        color = self._get_cycle_color()

        # Draw hours (2 digits)
        h1 = hour // 10
        h2 = hour % 10
        self._draw_digit_large(3, 20, h1, color)
        self._draw_digit_large(14, 20, h2, color)

        # Colon (blinking)
        if second % 2 == 0:
            self.display.draw_rect(25, 24, 2, 2, color)
            self.display.draw_rect(25, 29, 2, 2, color)

        # Draw minutes (2 digits)
        m1 = minute // 10
        m2 = minute % 10
        self._draw_digit_large(30, 20, m1, color)
        self._draw_digit_large(41, 20, m2, color)

        # Draw seconds smaller at bottom
        s1 = second // 10
        s2 = second % 10
        dim_color = tuple(c // 3 for c in color)
        self.display.draw_text_small(25, 40, f"{s1}{s2}", dim_color)

    def _draw_analog(self):
        """Draw analog clock display."""
        now = time_module.localtime()
        hour = now.tm_hour % 12
        minute = now.tm_min
        second = now.tm_sec

        cx, cy = GRID_SIZE // 2, GRID_SIZE // 2
        radius = 28

        # Draw clock face
        color = self._get_cycle_color()

        # Hour markers
        for i in range(12):
            angle = i * math.pi / 6 - math.pi / 2
            if i % 3 == 0:
                # Major markers (3, 6, 9, 12)
                inner_r = radius - 4
            else:
                inner_r = radius - 2

            x1 = int(cx + math.cos(angle) * inner_r)
            y1 = int(cy + math.sin(angle) * inner_r)
            x2 = int(cx + math.cos(angle) * radius)
            y2 = int(cy + math.sin(angle) * radius)
            self.display.draw_line(x1, y1, x2, y2, Colors.GRAY)

        # Hour hand
        hour_angle = (hour + minute / 60) * math.pi / 6 - math.pi / 2
        hour_len = 12
        hx = int(cx + math.cos(hour_angle) * hour_len)
        hy = int(cy + math.sin(hour_angle) * hour_len)
        self.display.draw_line(cx, cy, hx, hy, color)
        self.display.draw_line(cx + 1, cy, hx + 1, hy, color)

        # Minute hand
        min_angle = minute * math.pi / 30 - math.pi / 2
        min_len = 20
        mx = int(cx + math.cos(min_angle) * min_len)
        my = int(cy + math.sin(min_angle) * min_len)
        self.display.draw_line(cx, cy, mx, my, color)

        # Second hand
        sec_angle = second * math.pi / 30 - math.pi / 2
        sec_len = 24
        sx = int(cx + math.cos(sec_angle) * sec_len)
        sy = int(cy + math.sin(sec_angle) * sec_len)
        self.display.draw_line(cx, cy, sx, sy, Colors.RED)

        # Center dot
        self.display.set_pixel(cx, cy, Colors.WHITE)
        self.display.set_pixel(cx + 1, cy, Colors.WHITE)
        self.display.set_pixel(cx, cy + 1, Colors.WHITE)
        self.display.set_pixel(cx + 1, cy + 1, Colors.WHITE)

    def draw(self):
        self.display.clear(Colors.BLACK)

        if self.analog_mode:
            self._draw_analog()
        else:
            self._draw_digital()
