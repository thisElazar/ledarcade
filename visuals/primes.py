"""
PRIMES - Prime number pattern visualizer
=========================================
Three modes: Ulam spiral, Sacks spiral, and number grid.

Controls:
  Up/Down    - Cycle mode
  Left/Right - Adjust build speed
  Button     - Reset animation
"""

import math
from . import Visual, Display, Colors, GRID_SIZE


def _hsv(h, s, v):
    c = v * s
    x = c * (1 - abs((h * 6) % 2 - 1))
    m = v - c
    if h < 1/6:   r, g, b = c, x, 0
    elif h < 2/6: r, g, b = x, c, 0
    elif h < 3/6: r, g, b = 0, c, x
    elif h < 4/6: r, g, b = 0, x, c
    elif h < 5/6: r, g, b = x, 0, c
    else:          r, g, b = c, 0, x
    return (int((r + m) * 255), int((g + m) * 255), int((b + m) * 255))


# Sieve of Eratosthenes
_LIMIT = 4096
_is_prime = [False, False] + [True] * (_LIMIT - 2)
for _i in range(2, int(_LIMIT ** 0.5) + 1):
    if _is_prime[_i]:
        for _j in range(_i * _i, _LIMIT, _i):
            _is_prime[_j] = False

# Pre-build list of primes for digit display
_PRIMES = [n for n in range(_LIMIT) if _is_prime[n]]

MODE_NAMES = ['ULAM', 'SACKS', 'GRID']


def _ulam_coords(limit):
    """Pre-compute Ulam spiral coordinates for integers 1..limit."""
    coords = [(0, 0)] * (limit + 1)
    x, y = 0, 0
    dx, dy = 1, 0
    steps_in_leg = 1
    steps_taken = 0
    leg = 0
    coords[1] = (0, 0)
    for n in range(2, limit + 1):
        x += dx
        y += dy
        coords[n] = (x, y)
        steps_taken += 1
        if steps_taken == steps_in_leg:
            steps_taken = 0
            # Turn left: (dx,dy) -> (-dy,dx)
            dx, dy = -dy, dx
            leg += 1
            if leg % 2 == 0:
                steps_in_leg += 1
    return coords


_ULAM_COORDS = _ulam_coords(_LIMIT)


class Primes(Visual):
    name = "PRIMES"
    description = "Prime number patterns"
    category = "math"

    def reset(self):
        self.time = 0.0
        self.mode = 0
        self.build_progress = 0.0
        self.build_speed = 200.0  # integers per second
        self.overlay_timer = 0.0
        self._grid_scroll = 0.0

    def handle_input(self, input_state):
        consumed = False
        if input_state.up_pressed:
            self.mode = (self.mode - 1) % len(MODE_NAMES)
            self.build_progress = 0.0
            self._grid_scroll = 0.0
            self.overlay_timer = 2.0
            consumed = True
        if input_state.down_pressed:
            self.mode = (self.mode + 1) % len(MODE_NAMES)
            self.build_progress = 0.0
            self._grid_scroll = 0.0
            self.overlay_timer = 2.0
            consumed = True
        if input_state.left:
            self.build_speed = max(20, self.build_speed - 20)
            consumed = True
        if input_state.right:
            self.build_speed = min(1000, self.build_speed + 20)
            consumed = True
        if input_state.action_l or input_state.action_r:
            self.build_progress = 0.0
            self._grid_scroll = 0.0
            consumed = True
        return consumed

    def update(self, dt):
        self.time += dt
        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)
        if self.mode <= 1:
            self.build_progress = min(_LIMIT, self.build_progress + self.build_speed * dt)
        else:
            self._grid_scroll += dt * 3

    def draw(self):
        d = self.display
        d.clear()
        if self.mode == 0:
            self._draw_ulam(d)
        elif self.mode == 1:
            self._draw_sacks(d)
        else:
            self._draw_grid(d)

        # Label
        d.draw_text_small(2, 58, MODE_NAMES[self.mode], Colors.WHITE)

        # Overlay
        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            c = (int(200 * alpha), int(200 * alpha), int(200 * alpha))
            d.draw_text_small(2, 2, MODE_NAMES[self.mode], c)

    def _draw_ulam(self, d):
        cx, cy = 32, 32
        count = int(self.build_progress)
        for n in range(1, min(count + 1, _LIMIT)):
            ox, oy = _ULAM_COORDS[n]
            px = cx + ox
            py = cy - oy
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                if _is_prime[n]:
                    hue = (n / 500.0) % 1.0
                    d.set_pixel(px, py, _hsv(hue, 1.0, 1.0))
                else:
                    d.set_pixel(px, py, (15, 15, 20))

    def _draw_sacks(self, d):
        count = int(self.build_progress)
        cx, cy = 32, 32
        scale = 1.8
        for n in range(1, min(count + 1, _LIMIT)):
            angle = n * 2 * math.pi
            radius = math.sqrt(n) * scale
            px = int(cx + radius * math.cos(angle))
            py = int(cy - radius * math.sin(angle))
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                if _is_prime[n]:
                    hue = (n / 300.0) % 1.0
                    d.set_pixel(px, py, _hsv(hue, 1.0, 1.0))

    def _draw_grid(self, d):
        """Number grid: integers in rows, primes highlighted, composites dim."""
        # Each number takes 3 digits + 1 space = 16px wide (4 chars * 4px)
        # Fit ~4 numbers per row with some spacing
        # Use 3-digit numbers, 4px per char digit = 12px + 4px gap = 16px
        # 64px / 16px = 4 columns
        cols = 4
        char_w = 4
        num_w = char_w * 4  # 4 chars per cell (room for 3-digit + space)
        row_h = 7  # 5px font + 2px gap
        visible_rows = GRID_SIZE // row_h

        scroll_row = int(self._grid_scroll)

        for row in range(visible_rows):
            for col in range(cols):
                n = (scroll_row + row) * cols + col + 1
                if n >= _LIMIT:
                    continue
                x = col * num_w
                y = row * row_h
                if y + 5 > GRID_SIZE - 6:
                    break
                text = f"{n:>3}"
                if _is_prime[n]:
                    hue = (n / 200.0) % 1.0
                    color = _hsv(hue, 1.0, 1.0)
                else:
                    color = (35, 35, 45)
                d.draw_text_small(x + 1, y, text, color)
