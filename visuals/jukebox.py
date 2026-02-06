"""
Jukebox - Wurlitzer front view with bubble tubes
=================================================
A classic Wurlitzer jukebox with pulsing glow bands, spinning vinyl record,
rising bubble tubes, and a cycling selection display.

Controls:
  Left/Right - Adjust animation speed
  Up/Down    - Cycle glow theme (Warm/Neon/Pastel/Psychedelic)
  Escape     - Exit
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE


# Glow themes: each is a list of (color_a, color_b) pairs for sine-lerp bands
THEMES = {
    "Warm": [
        ((255, 180, 60), (255, 100, 150)),    # amber <-> pink
        ((255, 140, 40), (255, 80, 120)),
        ((220, 120, 30), (220, 70, 100)),
    ],
    "Neon": [
        ((0, 255, 255), (255, 0, 255)),       # cyan <-> magenta
        ((0, 200, 255), (255, 50, 200)),
        ((0, 150, 200), (200, 30, 150)),
    ],
    "Pastel": [
        ((255, 200, 220), (200, 220, 255)),   # blush <-> periwinkle
        ((255, 180, 200), (180, 200, 255)),
        ((230, 160, 180), (160, 180, 230)),
    ],
    "Psychedelic": [
        ((255, 50, 0), (0, 255, 50)),         # red <-> green
        ((255, 255, 0), (100, 0, 255)),        # yellow <-> violet
        ((0, 200, 255), (255, 100, 0)),        # sky <-> orange
    ],
}
THEME_NAMES = list(THEMES.keys())


class Bubble:
    """A single bubble particle in a tube."""
    def __init__(self, x_center, bottom, top):
        self.x_center = x_center
        self.bottom = bottom
        self.top = top
        self.x = float(x_center)
        self.y = float(bottom)
        self.speed = random.uniform(8, 16)
        self.wobble_phase = random.uniform(0, math.pi * 2)
        self.wobble_amp = random.uniform(0.5, 1.5)
        self.size = random.choice([1, 1, 2])
        self.brightness = random.uniform(0.6, 1.0)

    def reset(self):
        self.y = float(self.bottom)
        self.speed = random.uniform(8, 16)
        self.wobble_phase = random.uniform(0, math.pi * 2)
        self.brightness = random.uniform(0.6, 1.0)


class Jukebox(Visual):
    name = "JUKEBOX"
    description = "Wurlitzer jukebox"
    category = "music"

    # Jukebox body dimensions
    BODY_LEFT = 8
    BODY_RIGHT = 55
    BODY_TOP = 4
    BODY_BOTTOM = 62

    # Record window
    RECORD_CX = 32
    RECORD_CY = 26
    RECORD_R = 8

    # Bubble tube regions
    TUBE_L_X = 12
    TUBE_R_X = 51
    TUBE_TOP = 12
    TUBE_BOTTOM = 52

    # Selection panel
    PANEL_TOP = 42
    PANEL_BOTTOM = 54

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed = 1.0
        self.theme_idx = 0

        # Spinning record angle
        self.record_angle = 0.0

        # Selection display cycling
        self.sel_timer = 0.0
        self.sel_letters = "ABCDEFGH"
        self.sel_numbers = "1234567890"
        self.sel_letter_idx = 0
        self.sel_number_idx = 6  # Start at "A7"

        # Create bubble particles for left and right tubes
        self.bubbles_left = []
        self.bubbles_right = []
        for _ in range(8):
            self.bubbles_left.append(Bubble(self.TUBE_L_X, self.TUBE_BOTTOM, self.TUBE_TOP))
            self.bubbles_right.append(Bubble(self.TUBE_R_X, self.TUBE_BOTTOM, self.TUBE_TOP))
        # Stagger initial positions
        for i, b in enumerate(self.bubbles_left):
            b.y = self.TUBE_BOTTOM - i * 5 + random.uniform(-2, 2)
        for i, b in enumerate(self.bubbles_right):
            b.y = self.TUBE_BOTTOM - i * 5 + random.uniform(-2, 2)

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.right:
            self.speed = min(3.0, self.speed + 0.1)
            consumed = True
        if input_state.left:
            self.speed = max(0.2, self.speed - 0.1)
            consumed = True
        if input_state.up_pressed:
            self.theme_idx = (self.theme_idx + 1) % len(THEME_NAMES)
            consumed = True
        if input_state.down_pressed:
            self.theme_idx = (self.theme_idx - 1) % len(THEME_NAMES)
            consumed = True
        return consumed

    def update(self, dt: float):
        self.time += dt * self.speed

        # Spin the record
        self.record_angle += dt * self.speed * 2.0

        # Cycle selection display
        self.sel_timer += dt * self.speed
        if self.sel_timer > 2.0:
            self.sel_timer = 0.0
            self.sel_number_idx = (self.sel_number_idx + 1) % len(self.sel_numbers)
            if self.sel_number_idx == 0:
                self.sel_letter_idx = (self.sel_letter_idx + 1) % len(self.sel_letters)

        # Update bubbles
        for bubble_list in [self.bubbles_left, self.bubbles_right]:
            for b in bubble_list:
                b.y -= b.speed * dt * self.speed
                b.wobble_phase += dt * 3.0
                b.x = b.x_center + math.sin(b.wobble_phase) * b.wobble_amp
                # Reset bubble when it reaches the top
                if b.y < b.top:
                    b.reset()

    def _lerp_color(self, c1, c2, t):
        """Linear interpolate between two colors."""
        return (
            int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t),
        )

    def _dim(self, color, factor):
        """Dim a color by a factor (0-1)."""
        return (
            int(color[0] * factor),
            int(color[1] * factor),
            int(color[2] * factor),
        )

    def _draw_arch_top(self):
        """Draw the rounded arch top with pulsing glow bands."""
        theme_colors = THEMES[THEME_NAMES[self.theme_idx]]

        # Draw arch bands from outside in (rows 4-14)
        for band_idx, (ca, cb) in enumerate(theme_colors):
            t = (math.sin(self.time * 2.0 + band_idx * 0.8) + 1.0) / 2.0
            color = self._lerp_color(ca, cb, t)

            # Each band is a partial arc at the top
            inset = band_idx * 3
            band_left = self.BODY_LEFT + inset
            band_right = self.BODY_RIGHT - inset
            band_top = self.BODY_TOP + inset
            band_width = band_right - band_left
            cx = (band_left + band_right) / 2.0
            cy = band_top + 8.0
            rx = band_width / 2.0
            ry = 8.0 - inset * 0.5
            if ry < 2:
                ry = 2

            for y in range(band_top, band_top + 10):
                for x in range(band_left, band_right + 1):
                    # Elliptical arch shape
                    dx = (x - cx) / max(rx, 1)
                    dy = (y - cy) / max(ry, 1)
                    dist = dx * dx + dy * dy
                    if dist < 1.0 and y < cy:
                        if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                            self.display.set_pixel(x, y, color)

    def _draw_body(self):
        """Draw the main jukebox body (dark wood/chrome frame)."""
        body_color = (60, 30, 15)  # Dark wood
        chrome = (180, 180, 200)
        chrome_highlight = (220, 220, 240)

        # Main body fill
        for y in range(self.BODY_TOP + 8, self.BODY_BOTTOM + 1):
            for x in range(self.BODY_LEFT, self.BODY_RIGHT + 1):
                if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                    self.display.set_pixel(x, y, body_color)

        # Chrome trim - left edge
        for y in range(self.BODY_TOP + 5, self.BODY_BOTTOM + 1):
            if 0 <= self.BODY_LEFT < GRID_SIZE and 0 <= y < GRID_SIZE:
                self.display.set_pixel(self.BODY_LEFT, y, chrome)
            if 0 <= self.BODY_LEFT + 1 < GRID_SIZE and 0 <= y < GRID_SIZE:
                # Highlight shimmer
                shimmer = (math.sin(self.time * 3.0 + y * 0.3) + 1.0) / 2.0
                c = self._lerp_color(chrome, chrome_highlight, shimmer * 0.5)
                self.display.set_pixel(self.BODY_LEFT + 1, y, c)

        # Chrome trim - right edge
        for y in range(self.BODY_TOP + 5, self.BODY_BOTTOM + 1):
            if 0 <= self.BODY_RIGHT < GRID_SIZE and 0 <= y < GRID_SIZE:
                self.display.set_pixel(self.BODY_RIGHT, y, chrome)
            if 0 <= self.BODY_RIGHT - 1 < GRID_SIZE and 0 <= y < GRID_SIZE:
                shimmer = (math.sin(self.time * 3.0 + y * 0.3 + 1.0) + 1.0) / 2.0
                c = self._lerp_color(chrome, chrome_highlight, shimmer * 0.5)
                self.display.set_pixel(self.BODY_RIGHT - 1, y, c)

        # Chrome trim - bottom edge
        for x in range(self.BODY_LEFT, self.BODY_RIGHT + 1):
            if 0 <= x < GRID_SIZE and 0 <= self.BODY_BOTTOM < GRID_SIZE:
                self.display.set_pixel(x, self.BODY_BOTTOM, chrome)
            if 0 <= x < GRID_SIZE and 0 <= self.BODY_BOTTOM - 1 < GRID_SIZE:
                self.display.set_pixel(x, self.BODY_BOTTOM - 1, chrome_highlight)

    def _draw_record_window(self):
        """Draw the record viewing window with spinning vinyl."""
        cx = self.RECORD_CX
        cy = self.RECORD_CY
        r = self.RECORD_R

        # Window background (dark)
        window_bg = (15, 15, 25)
        for dy in range(-r - 2, r + 3):
            for dx in range(-r - 2, r + 3):
                dist = math.sqrt(dx * dx + dy * dy)
                if dist <= r + 2:
                    px, py = cx + dx, cy + dy
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        self.display.set_pixel(px, py, window_bg)

        # Vinyl record
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                dist = math.sqrt(dx * dx + dy * dy)
                if dist <= r:
                    px, py = cx + dx, cy + dy
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        # Angle from center
                        angle = math.atan2(dy, dx) + self.record_angle
                        # Grooves: alternating dark rings
                        groove = math.sin(dist * 2.5 + angle * 2) * 0.3
                        base = 20 + groove * 20

                        if dist < 2:
                            # Label center (red)
                            self.display.set_pixel(px, py, (180, 40, 40))
                        elif dist < 3:
                            # Label ring
                            label_t = (math.sin(angle * 3) + 1) / 2
                            self.display.set_pixel(px, py, (
                                int(180 - 40 * label_t),
                                int(40 + 20 * label_t),
                                int(40 + 20 * label_t),
                            ))
                        else:
                            # Vinyl surface with grooves
                            v = int(max(5, min(50, base)))
                            self.display.set_pixel(px, py, (v, v, v + 5))

        # Tonearm (small line from upper-right)
        arm_angle = 0.3 + math.sin(self.time * 0.2) * 0.05
        for i in range(5):
            ax = int(cx + r + 1 - i * math.cos(arm_angle))
            ay = int(cy - r + i * math.sin(arm_angle) + 1)
            if 0 <= ax < GRID_SIZE and 0 <= ay < GRID_SIZE:
                self.display.set_pixel(ax, ay, (160, 160, 180))

    def _draw_bubble_tube(self, bubbles, tube_x):
        """Draw a bubble tube with floating particles."""
        theme_colors = THEMES[THEME_NAMES[self.theme_idx]]
        base_color = theme_colors[0][0]  # Use first theme color for bubbles

        # Tube glass outline
        tube_color = (60, 60, 80)
        for y in range(self.TUBE_TOP, self.TUBE_BOTTOM + 1):
            if 0 <= tube_x - 2 < GRID_SIZE and 0 <= y < GRID_SIZE:
                self.display.set_pixel(tube_x - 2, y, tube_color)
            if 0 <= tube_x + 2 < GRID_SIZE and 0 <= y < GRID_SIZE:
                self.display.set_pixel(tube_x + 2, y, tube_color)

        # Tube interior (slightly lit)
        tube_inner = (20, 15, 30)
        for y in range(self.TUBE_TOP, self.TUBE_BOTTOM + 1):
            for dx in [-1, 0, 1]:
                px = tube_x + dx
                if 0 <= px < GRID_SIZE and 0 <= y < GRID_SIZE:
                    self.display.set_pixel(px, y, tube_inner)

        # Draw bubbles
        for b in bubbles:
            bx, by = int(b.x), int(b.y)
            if self.TUBE_TOP <= by <= self.TUBE_BOTTOM:
                bright = b.brightness
                color = self._dim(base_color, bright)
                if b.size == 1:
                    if 0 <= bx < GRID_SIZE and 0 <= by < GRID_SIZE:
                        self.display.set_pixel(bx, by, color)
                else:
                    for ddx in range(-1, 2):
                        for ddy in range(-1, 2):
                            if abs(ddx) + abs(ddy) <= 1:
                                px, py = bx + ddx, by + ddy
                                if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                                    if self.TUBE_TOP <= py <= self.TUBE_BOTTOM:
                                        self.display.set_pixel(px, py, color)

    def _draw_selection_panel(self):
        """Draw the selection panel with cycling track display."""
        panel_bg = (40, 25, 15)
        panel_border = (120, 100, 60)

        # Panel background
        for y in range(self.PANEL_TOP, self.PANEL_BOTTOM + 1):
            for x in range(self.BODY_LEFT + 4, self.BODY_RIGHT - 3):
                if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                    self.display.set_pixel(x, y, panel_bg)

        # Panel border top/bottom
        for x in range(self.BODY_LEFT + 4, self.BODY_RIGHT - 3):
            if 0 <= x < GRID_SIZE:
                if 0 <= self.PANEL_TOP < GRID_SIZE:
                    self.display.set_pixel(x, self.PANEL_TOP, panel_border)
                if 0 <= self.PANEL_BOTTOM < GRID_SIZE:
                    self.display.set_pixel(x, self.PANEL_BOTTOM, panel_border)

        # Selection code display (e.g. "A7")
        sel_text = self.sel_letters[self.sel_letter_idx] + self.sel_numbers[self.sel_number_idx]
        # Pulsing selection color
        pulse = (math.sin(self.time * 4.0) + 1.0) / 2.0
        text_color = self._lerp_color((255, 200, 50), (255, 255, 200), pulse)
        self.display.draw_text_small(2, self.PANEL_TOP + 3, sel_text, text_color)

        # Decorative row indicators on the panel
        row_y = self.PANEL_TOP + 3
        for i in range(5):
            dot_x = self.BODY_LEFT + 18 + i * 6
            dot_color = (100, 80, 40) if i != (int(self.time) % 5) else (255, 200, 80)
            if 0 <= dot_x < GRID_SIZE and 0 <= row_y < GRID_SIZE:
                self.display.set_pixel(dot_x, row_y, dot_color)
            if 0 <= dot_x + 1 < GRID_SIZE and 0 <= row_y < GRID_SIZE:
                self.display.set_pixel(dot_x + 1, row_y, dot_color)

    def _draw_glow_bands(self):
        """Draw pulsing glow bands around the record window area."""
        theme_colors = THEMES[THEME_NAMES[self.theme_idx]]

        # Horizontal glow bands between arch and record
        for band_idx in range(3):
            ca, cb = theme_colors[band_idx % len(theme_colors)]
            t = (math.sin(self.time * 2.5 + band_idx * 1.2) + 1.0) / 2.0
            color = self._lerp_color(ca, cb, t)
            dimmed = self._dim(color, 0.6)

            y = 15 + band_idx * 2
            for x in range(self.BODY_LEFT + 3, self.BODY_RIGHT - 2):
                # Skip over tube areas
                if abs(x - self.TUBE_L_X) <= 2 or abs(x - self.TUBE_R_X) <= 2:
                    continue
                if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                    self.display.set_pixel(x, y, dimmed)

        # Glow bands below record window
        for band_idx in range(2):
            ca, cb = theme_colors[(band_idx + 1) % len(theme_colors)]
            t = (math.sin(self.time * 2.5 + band_idx * 1.5 + 2.0) + 1.0) / 2.0
            color = self._lerp_color(ca, cb, t)
            dimmed = self._dim(color, 0.5)

            y = self.RECORD_CY + self.RECORD_R + 3 + band_idx * 2
            for x in range(self.BODY_LEFT + 3, self.BODY_RIGHT - 2):
                if abs(x - self.TUBE_L_X) <= 2 or abs(x - self.TUBE_R_X) <= 2:
                    continue
                if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                    self.display.set_pixel(x, y, dimmed)

    def _draw_base(self):
        """Draw the jukebox base/foot."""
        base_color = (80, 40, 20)
        chrome = (160, 160, 180)
        # Wider base
        for y in range(self.BODY_BOTTOM + 1, min(GRID_SIZE, self.BODY_BOTTOM + 3)):
            for x in range(self.BODY_LEFT - 2, self.BODY_RIGHT + 3):
                if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                    self.display.set_pixel(x, y, base_color)
        # Chrome strip on base
        if self.BODY_BOTTOM + 1 < GRID_SIZE:
            for x in range(self.BODY_LEFT - 2, self.BODY_RIGHT + 3):
                if 0 <= x < GRID_SIZE:
                    self.display.set_pixel(x, self.BODY_BOTTOM + 1, chrome)

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Draw layers back to front
        self._draw_body()
        self._draw_arch_top()
        self._draw_glow_bands()
        self._draw_bubble_tube(self.bubbles_left, self.TUBE_L_X)
        self._draw_bubble_tube(self.bubbles_right, self.TUBE_R_X)
        self._draw_record_window()
        self._draw_selection_panel()
        self._draw_base()

        # Theme name at very bottom
        theme_name = THEME_NAMES[self.theme_idx]
        self.display.draw_text_small(2, 58, theme_name, (120, 100, 80))
