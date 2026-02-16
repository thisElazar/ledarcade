"""
PI - Pi estimation and digit visualization
============================================
Four modes: Monte Carlo estimation, digit color grid,
digit spiral, and Buffon's needle experiment.

Controls:
  Up/Down    - Cycle mode
  Left/Right - Adjust rate
  Button     - Reset
"""

import math
import random
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


# First 1000+ digits of pi for display
PI_DIGITS = (
    "3."
    "14159265358979323846264338327950288419716939937510"
    "58209749445923078164062862089986280348253421170679"
    "82148086513282306647093844609550582231725359408128"
    "48111745028410270193852110555964462294895493038196"
    "44288109756659334461284756482337867831652712019091"
    "45648566923460348610454326648213393607260249141273"
    "72458700660631558817488152092096282925409171536436"
    "78925903600113305305488204665213841469519415116094"
    "33057270365759591953092186117381932611793105118548"
    "07446237996274956735188575272489122793818301194912"
    "98336733624406566430860213949463952247371907021798"
    "60943702770539217176293176752384674818467669405132"
    "00056812714526356082778577134275778960917363717872"
    "14684409012249534301465495853710507922796892589235"
    "42019956112129021960864034418159813629774771309960"
    "51870721134999999837297804995105973173281609631859"
    "50244594553469083026425223082533446850352619311881"
    "71010003137838752886587533208381420617177669147303"
    "59825349042875546873115956286388235378759375195778"
    "18577805321712268066130019278766111959092164201989"
)

# Strip the period for digit-only operations
PI_DIGIT_CHARS = PI_DIGITS.replace(".", "")

# Colors for digits 0-9
DIGIT_COLORS = [
    (40, 40, 40),       # 0 - dark gray
    (255, 60, 60),      # 1 - red
    (255, 160, 40),     # 2 - orange
    (255, 255, 60),     # 3 - yellow
    (60, 255, 60),      # 4 - green
    (60, 200, 255),     # 5 - cyan
    (80, 80, 255),      # 6 - blue
    (180, 60, 255),     # 7 - purple
    (255, 100, 200),    # 8 - pink
    (255, 255, 255),    # 9 - white
]

MODE_NAMES = ['MONTE CARLO', 'DIGITS', 'DIGIT SPIRAL', 'BUFFON']


class Pi(Visual):
    name = "PI"
    description = "Pi estimation and digits"
    category = "math"

    def reset(self):
        self.time = 0.0
        self.mode = 0
        self.overlay_timer = 0.0
        self.rate = 1.0
        self._reset_monte_carlo()
        self._reset_buffon()
        self._digit_scroll = 0.0
        self._spiral_progress = 0.0

    def _reset_monte_carlo(self):
        self.mc_points = []
        self.mc_inside = 0
        self.mc_total = 0

    def _reset_buffon(self):
        self.bf_needles = []
        self.bf_cross = 0
        self.bf_total = 0

    def handle_input(self, input_state):
        consumed = False
        if input_state.up_pressed:
            self.mode = (self.mode - 1) % len(MODE_NAMES)
            self.overlay_timer = 2.0
            consumed = True
        if input_state.down_pressed:
            self.mode = (self.mode + 1) % len(MODE_NAMES)
            self.overlay_timer = 2.0
            consumed = True
        if input_state.left:
            self.rate = max(0.2, self.rate - 0.1)
            consumed = True
        if input_state.right:
            self.rate = min(5.0, self.rate + 0.1)
            consumed = True
        if input_state.action_l or input_state.action_r:
            self._reset_monte_carlo()
            self._reset_buffon()
            self._digit_scroll = 0.0
            self._spiral_progress = 0.0
            consumed = True
        return consumed

    def update(self, dt):
        self.time += dt
        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

        if self.mode == 0:
            # Add Monte Carlo points
            pts_per_sec = int(50 * self.rate)
            for _ in range(max(1, int(pts_per_sec * dt))):
                if self.mc_total >= 3000:
                    break
                x = random.random()
                y = random.random()
                inside = (x * x + y * y) <= 1.0
                self.mc_points.append((x, y, inside))
                self.mc_total += 1
                if inside:
                    self.mc_inside += 1
        elif self.mode == 1:
            self._digit_scroll += self.rate * 2 * dt
        elif self.mode == 2:
            self._spiral_progress = min(len(PI_DIGIT_CHARS),
                                        self._spiral_progress + self.rate * 40 * dt)
        elif self.mode == 3:
            # Add Buffon needles
            needles_per_sec = int(20 * self.rate)
            for _ in range(max(1, int(needles_per_sec * dt))):
                if self.bf_total >= 2000:
                    break
                self._drop_needle()

    def _drop_needle(self):
        """Drop a Buffon's needle."""
        spacing = 10.0
        needle_len = spacing
        cx = random.uniform(4, GRID_SIZE - 4)
        cy = random.uniform(4, GRID_SIZE - 10)
        angle = random.uniform(0, math.pi)
        dx = needle_len / 2 * math.cos(angle)
        dy = needle_len / 2 * math.sin(angle)
        y1 = cy - dy
        y2 = cy + dy
        crosses = False
        for line_y in range(0, GRID_SIZE, int(spacing)):
            if (y1 <= line_y <= y2) or (y2 <= line_y <= y1):
                crosses = True
                break
        self.bf_needles.append((cx, cy, dx, dy, crosses))
        self.bf_total += 1
        if crosses:
            self.bf_cross += 1

    def draw(self):
        d = self.display
        d.clear()
        if self.mode == 0:
            self._draw_monte_carlo(d)
        elif self.mode == 1:
            self._draw_digits(d)
        elif self.mode == 2:
            self._draw_digit_spiral(d)
        else:
            self._draw_buffon(d)

        # Label
        label = MODE_NAMES[self.mode]
        d.draw_text_small(2, 58, label, Colors.WHITE)

        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            c = (int(200 * alpha), int(200 * alpha), int(200 * alpha))
            d.draw_text_small(2, 2, label, c)

    def _draw_monte_carlo(self, d):
        # Draw quarter circle boundary
        r = 54
        ox, oy = 4, 4
        for a in range(91):
            angle = math.radians(a)
            px = int(ox + r * math.cos(angle))
            py = int(oy + r * math.sin(angle))
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                d.set_pixel(px, py, (60, 60, 60))

        # Draw points
        for x, y, inside in self.mc_points:
            px = int(ox + x * r)
            py = int(oy + y * r)
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                if inside:
                    d.set_pixel(px, py, (60, 120, 255))
                else:
                    d.set_pixel(px, py, (255, 60, 60))

        # Show estimate
        if self.mc_total > 0:
            estimate = 4.0 * self.mc_inside / self.mc_total
            text = f"{estimate:.4f}"
            d.draw_text_small(2, 2, "PI=" + text, (255, 255, 100))

    def _draw_digits(self, d):
        """Show pi digits as actual text characters, scrolling vertically.

        Each char is 4px wide (3px glyph + 1px gap). At 64px we fit 16 chars
        per row. Row height = 7px (5px glyph + 2px gap). We show the digits
        as a continuous stream wrapping at 16 chars, colored by digit value.
        """
        chars_per_row = 16
        row_h = 7
        visible_rows = (GRID_SIZE - 6) // row_h  # leave room for label
        scroll_row = int(self._digit_scroll)

        # Header: "3." on first visible row before scrolling starts
        for row in range(visible_rows):
            src_row = scroll_row + row
            start_idx = src_row * chars_per_row
            y = row * row_h
            if y + 5 > GRID_SIZE - 6:
                break
            for col in range(chars_per_row):
                idx = start_idx + col
                if idx < 0 or idx >= len(PI_DIGITS):
                    continue
                ch = PI_DIGITS[idx]
                x = col * 4
                if ch == '.':
                    d.draw_text_small(x, y, '.', (200, 200, 200))
                else:
                    digit = int(ch)
                    d.draw_text_small(x, y, ch, DIGIT_COLORS[digit])

    def _draw_digit_spiral(self, d):
        """Pi digits placed in an Ulam-style spiral from center, each digit colored."""
        cx, cy = 32, 30
        count = int(self._spiral_progress)
        # Use Ulam spiral coordinates
        x, y = 0, 0
        sx, sy = 1, 0
        steps_in_leg = 1
        steps_taken = 0
        leg = 0
        for n in range(count):
            if n >= len(PI_DIGIT_CHARS):
                break
            px = cx + x
            py = cy - y
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                digit = int(PI_DIGIT_CHARS[n])
                d.set_pixel(px, py, DIGIT_COLORS[digit])
            # Advance spiral
            if n > 0:
                x += sx
                y += sy
                steps_taken += 1
                if steps_taken == steps_in_leg:
                    steps_taken = 0
                    sx, sy = -sy, sx  # turn left
                    leg += 1
                    if leg % 2 == 0:
                        steps_in_leg += 1

        # Legend at bottom
        d.draw_text_small(2, 2, f"{count} DIGITS", (200, 200, 100))

    def _draw_buffon(self, d):
        # Draw parallel horizontal lines
        spacing = 10
        for line_y in range(0, GRID_SIZE, spacing):
            d.draw_line(0, line_y, GRID_SIZE - 1, line_y, (40, 40, 50))

        # Draw needles
        for cx, cy, dx, dy, crosses in self.bf_needles:
            if crosses:
                color = (255, 100, 80)
            else:
                color = (80, 180, 255)
            x1, y1 = int(cx - dx), int(cy - dy)
            x2, y2 = int(cx + dx), int(cy + dy)
            d.draw_line(x1, y1, x2, y2, color)

        # Show estimate
        if self.bf_cross > 0:
            estimate = 2.0 * self.bf_total / self.bf_cross
            text = f"{estimate:.4f}"
            d.draw_text_small(2, 2, "PI=" + text, (255, 255, 100))
        elif self.bf_total > 0:
            d.draw_text_small(2, 2, "PI=...", (255, 255, 100))
