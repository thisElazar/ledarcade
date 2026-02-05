"""
Wonder Cabinet - Branded idle visuals
======================================
Two branded visuals for the Wonder Cabinet arcade:
  WonderGlow  - Ambient starfield with color-cycling text and glow
  WonderMarquee - Classic arcade marquee border with chasing lights
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE


def _hue_to_rgb(h):
    """Convert hue (0.0-1.0) to RGB tuple."""
    h = h % 1.0
    r = max(0.0, min(1.0, abs(h * 6.0 - 3.0) - 1.0))
    g = max(0.0, min(1.0, 2.0 - abs(h * 6.0 - 2.0)))
    b = max(0.0, min(1.0, 2.0 - abs(h * 6.0 - 4.0)))
    return (int(r * 255), int(g * 255), int(b * 255))


def _center_x(text):
    """Calculate x position to center text (4px per char + 1px spacing)."""
    width = len(text) * 5 - 1
    return max(0, (GRID_SIZE - width) // 2)


# =========================================================================
# WonderGlow - Ambient starfield with color-cycling text
# =========================================================================

class WonderGlow(Visual):
    name = "WONDER GLOW"
    description = "Wonder Cabinet ambient glow"
    category = "digital"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        # Create persistent star positions
        self.stars = []
        for _ in range(30):
            self.stars.append({
                'x': random.randint(0, GRID_SIZE - 1),
                'y': random.randint(0, GRID_SIZE - 1),
                'phase': random.random() * math.pi * 2,
                'speed': 0.5 + random.random() * 1.5,
            })

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        self.display.clear(Colors.BLACK)
        t = self.time

        # Subtle twinkling stars
        for star in self.stars:
            brightness = 0.3 + 0.7 * max(0, math.sin(t * star['speed'] + star['phase']))
            gray = int(60 * brightness)
            self.display.set_pixel(star['x'], star['y'], (gray, gray, gray))

        # Pulsing brightness
        pulse = 0.7 + 0.3 * math.sin(t * 1.5)

        # Color-cycling hue
        hue = (t * 0.15) % 1.0
        color = _hue_to_rgb(hue)
        color = (int(color[0] * pulse), int(color[1] * pulse), int(color[2] * pulse))

        # "WONDER" with glow
        wx = _center_x("WONDER")
        wy = 24
        for ox in [-1, 0, 1]:
            for oy in [-1, 0, 1]:
                if ox == 0 and oy == 0:
                    continue
                glow = (color[0] // 4, color[1] // 4, color[2] // 4)
                self.display.draw_text_small(wx + ox, wy + oy, "WONDER", glow)
        self.display.draw_text_small(wx, wy, "WONDER", color)

        # "CABINET" with glow
        cx = _center_x("CABINET")
        cy = 34
        hue2 = (hue + 0.15) % 1.0
        color2 = _hue_to_rgb(hue2)
        color2 = (int(color2[0] * pulse), int(color2[1] * pulse), int(color2[2] * pulse))
        for ox in [-1, 0, 1]:
            for oy in [-1, 0, 1]:
                if ox == 0 and oy == 0:
                    continue
                glow2 = (color2[0] // 4, color2[1] // 4, color2[2] // 4)
                self.display.draw_text_small(cx + ox, cy + oy, "CABINET", glow2)
        self.display.draw_text_small(cx, cy, "CABINET", color2)


# =========================================================================
# WonderMarquee - Classic arcade marquee border with chasing lights
# =========================================================================

class WonderMarquee(Visual):
    name = "WONDER MARQUEE"
    description = "Arcade marquee border"
    category = "digital"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        # Build border pixel positions (clockwise)
        self.border = []
        # Top edge
        for x in range(0, GRID_SIZE, 2):
            self.border.append((x, 0))
        # Right edge
        for y in range(2, GRID_SIZE, 2):
            self.border.append((GRID_SIZE - 1, y))
        # Bottom edge (reversed)
        for x in range(GRID_SIZE - 2, -1, -2):
            self.border.append((x, GRID_SIZE - 1))
        # Left edge (reversed)
        for y in range(GRID_SIZE - 3, 0, -2):
            self.border.append((0, y))

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        self.display.clear(Colors.BLACK)
        t = self.time
        n = len(self.border)

        # Chasing lights around border
        chase_speed = 8.0
        lit_count = 6  # number of lit bulbs in each chase group
        gap = 4        # gap between groups
        period = lit_count + gap

        for i, (bx, by) in enumerate(self.border):
            pos = (i - int(t * chase_speed)) % period
            if pos < lit_count:
                # Lit bulb - cycle hue along the border
                hue = (i / n + t * 0.2) % 1.0
                self.display.set_pixel(bx, by, _hue_to_rgb(hue))
            else:
                # Dim bulb
                self.display.set_pixel(bx, by, (20, 20, 20))

        # Text: bright contrasting color with slight pulse
        pulse = 0.8 + 0.2 * math.sin(t * 3.0)
        text_color = (int(255 * pulse), int(255 * pulse), int(50 * pulse))

        wx = _center_x("WONDER")
        self.display.draw_text_small(wx, 25, "WONDER", text_color)

        cx = _center_x("CABINET")
        self.display.draw_text_small(cx, 35, "CABINET", text_color)
