"""
Wonder Cabinet - Branded idle visuals
======================================
Branded visuals for the Wonder Cabinet arcade:
  WonderGlow     - Ambient starfield with color-cycling text and glow
  WonderMarquee  - Classic arcade marquee border with chasing lights
  WonderCrawl    - Star Wars opening crawl
  WonderSlide    - Words slide in from opposite sides
  WonderDrop     - Words drop from above and bounce into place
  WonderSpin     - Words orbit around the center
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
    """Calculate x position to center text (4px per char + 1px spacing).
    Uses +1 rounding to avoid 1px left bias on odd remainders."""
    width = len(text) * 5 - 1
    return max(0, (GRID_SIZE - width + 1) // 2)


# Precomputed centered x positions
WONDER_X = _center_x("WONDER")   # 18
CABINET_X = _center_x("CABINET") # 15
WONDER_W = len("WONDER") * 5 - 1   # 29
CABINET_W = len("CABINET") * 5 - 1 # 34
# Vertical center positions for the two-line layout
WONDER_Y = 24
CABINET_Y = 34


def _ease_out_bounce(t):
    """Bounce easing function (0-1 input, 0-1 output)."""
    if t < 1 / 2.75:
        return 7.5625 * t * t
    elif t < 2 / 2.75:
        t -= 1.5 / 2.75
        return 7.5625 * t * t + 0.75
    elif t < 2.5 / 2.75:
        t -= 2.25 / 2.75
        return 7.5625 * t * t + 0.9375
    else:
        t -= 2.625 / 2.75
        return 7.5625 * t * t + 0.984375


def _ease_in_out(t):
    """Smooth ease in-out (0-1 input, 0-1 output)."""
    return t * t * (3.0 - 2.0 * t)


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

        for star in self.stars:
            brightness = 0.3 + 0.7 * max(0, math.sin(t * star['speed'] + star['phase']))
            gray = int(60 * brightness)
            self.display.set_pixel(star['x'], star['y'], (gray, gray, gray))

        pulse = 0.7 + 0.3 * math.sin(t * 1.5)
        hue = (t * 0.15) % 1.0
        color = _hue_to_rgb(hue)
        color = (int(color[0] * pulse), int(color[1] * pulse), int(color[2] * pulse))

        # "WONDER" with glow
        for ox in [-1, 0, 1]:
            for oy in [-1, 0, 1]:
                if ox == 0 and oy == 0:
                    continue
                glow = (color[0] // 4, color[1] // 4, color[2] // 4)
                self.display.draw_text_small(WONDER_X + ox, WONDER_Y + oy, "WONDER", glow)
        self.display.draw_text_small(WONDER_X, WONDER_Y, "WONDER", color)

        # "CABINET" with glow
        hue2 = (hue + 0.15) % 1.0
        color2 = _hue_to_rgb(hue2)
        color2 = (int(color2[0] * pulse), int(color2[1] * pulse), int(color2[2] * pulse))
        for ox in [-1, 0, 1]:
            for oy in [-1, 0, 1]:
                if ox == 0 and oy == 0:
                    continue
                glow2 = (color2[0] // 4, color2[1] // 4, color2[2] // 4)
                self.display.draw_text_small(CABINET_X + ox, CABINET_Y + oy, "CABINET", glow2)
        self.display.draw_text_small(CABINET_X, CABINET_Y, "CABINET", color2)


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
        self.border = []
        for x in range(0, GRID_SIZE, 2):
            self.border.append((x, 0))
        for y in range(2, GRID_SIZE, 2):
            self.border.append((GRID_SIZE - 1, y))
        for x in range(GRID_SIZE - 2, -1, -2):
            self.border.append((x, GRID_SIZE - 1))
        for y in range(GRID_SIZE - 3, 0, -2):
            self.border.append((0, y))

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        self.display.clear(Colors.BLACK)
        t = self.time
        n = len(self.border)

        chase_speed = 8.0
        lit_count = 6
        gap = 4
        period = lit_count + gap

        for i, (bx, by) in enumerate(self.border):
            pos = (i - int(t * chase_speed)) % period
            if pos < lit_count:
                hue = (i / n + t * 0.2) % 1.0
                self.display.set_pixel(bx, by, _hue_to_rgb(hue))
            else:
                self.display.set_pixel(bx, by, (20, 20, 20))

        pulse = 0.8 + 0.2 * math.sin(t * 3.0)
        text_color = (int(255 * pulse), int(255 * pulse), int(50 * pulse))
        self.display.draw_text_small(WONDER_X, WONDER_Y + 1, "WONDER", text_color)
        self.display.draw_text_small(CABINET_X, CABINET_Y + 1, "CABINET", text_color)


# =========================================================================
# WonderCrawl - Star Wars opening crawl
# =========================================================================

class WonderCrawl(Visual):
    name = "WONDER CRAWL"
    description = "Star Wars title crawl"
    category = "digital"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        self.display.clear(Colors.BLACK)
        t = self.time

        # Starfield background
        random.seed(42)
        for _ in range(40):
            sx = random.randint(0, GRID_SIZE - 1)
            sy = random.randint(0, GRID_SIZE - 1)
            bright = random.randint(20, 80)
            self.display.set_pixel(sx, sy, (bright, bright, bright))
        random.seed()

        # Scroll speed: full cycle every ~8 seconds
        scroll_speed = 12.0
        # Text starts at bottom (y=64), scrolls up past top (y=-10)
        cycle = GRID_SIZE + 20  # total travel distance
        y_offset = GRID_SIZE - (t * scroll_speed) % cycle

        # Yellow Star Wars color
        color = (255, 232, 58)
        dim = (140, 128, 30)

        wy = int(y_offset)
        cy = int(y_offset) + 10

        # Draw with slight dim trailing effect
        if 0 <= wy < GRID_SIZE - 2:
            self.display.draw_text_small(WONDER_X, wy, "WONDER", color)
        elif -6 < wy < 0:
            # Partially off top - draw dimmer
            self.display.draw_text_small(WONDER_X, wy, "WONDER", dim)

        if 0 <= cy < GRID_SIZE - 2:
            self.display.draw_text_small(CABINET_X, cy, "CABINET", color)
        elif -6 < cy < 0:
            self.display.draw_text_small(CABINET_X, cy, "CABINET", dim)


# =========================================================================
# WonderSlide - Words slide in from opposite sides
# =========================================================================

class WonderSlide(Visual):
    name = "WONDER SLIDE"
    description = "Sliding text from sides"
    category = "digital"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Cycle: 6 seconds total
        # 0-1.5s:  slide in from sides
        # 1.5-4s:  hold at center with glow
        # 4-5.5s:  slide out opposite sides
        # 5.5-6s:  brief pause
        cycle = 6.0
        t = self.time % cycle

        hue = (self.time * 0.2) % 1.0
        color = _hue_to_rgb(hue)
        color2 = _hue_to_rgb((hue + 0.15) % 1.0)

        if t < 1.5:
            # Slide in: WONDER from left, CABINET from right
            p = _ease_in_out(t / 1.5)
            wx = int(-WONDER_W + p * (WONDER_X + WONDER_W))
            cx = int(GRID_SIZE - p * (GRID_SIZE - CABINET_X))
        elif t < 4.0:
            # Hold at center
            wx = WONDER_X
            cx = CABINET_X
        elif t < 5.5:
            # Slide out: WONDER to right, CABINET to left
            p = _ease_in_out((t - 4.0) / 1.5)
            wx = int(WONDER_X + p * (GRID_SIZE - WONDER_X))
            cx = int(CABINET_X - p * (CABINET_X + CABINET_W))
        else:
            # Brief black pause
            return

        self.display.draw_text_small(wx, WONDER_Y, "WONDER", color)
        self.display.draw_text_small(cx, CABINET_Y, "CABINET", color2)


# =========================================================================
# WonderDrop - Words drop from above and bounce into place
# =========================================================================

class WonderDrop(Visual):
    name = "WONDER DROP"
    description = "Bouncing text from above"
    category = "digital"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Cycle: 6 seconds
        # 0-1.2s:  WONDER drops and bounces
        # 0.4-1.6s: CABINET drops and bounces (staggered)
        # 1.6-4.5s: hold with pulse
        # 4.5-5.5s: both fall off bottom
        # 5.5-6.0s: pause
        cycle = 6.0
        t = self.time % cycle

        hue = (self.time * 0.15) % 1.0

        # WONDER position
        if t < 1.2:
            p = min(1.0, t / 1.2)
            bounce = _ease_out_bounce(p)
            wy = int(-8 + bounce * (WONDER_Y + 8))
        elif t < 4.5:
            wy = WONDER_Y
        elif t < 5.5:
            p = (t - 4.5) / 1.0
            wy = int(WONDER_Y + p * p * (GRID_SIZE - WONDER_Y + 8))
        else:
            wy = GRID_SIZE + 8

        # CABINET position (staggered 0.4s later)
        ct = t - 0.4
        if ct < 0:
            cy = -8
        elif ct < 1.2:
            p = min(1.0, ct / 1.2)
            bounce = _ease_out_bounce(p)
            cy = int(-8 + bounce * (CABINET_Y + 8))
        elif ct < 4.1:
            cy = CABINET_Y
        elif ct < 5.1:
            p = (ct - 4.1) / 1.0
            cy = int(CABINET_Y + p * p * (GRID_SIZE - CABINET_Y + 8))
        else:
            cy = GRID_SIZE + 8

        color = _hue_to_rgb(hue)
        color2 = _hue_to_rgb((hue + 0.15) % 1.0)

        # Pulse while holding
        if 1.6 < t < 4.5:
            pulse = 0.7 + 0.3 * math.sin(t * 3.0)
            color = (int(color[0] * pulse), int(color[1] * pulse), int(color[2] * pulse))
            color2 = (int(color2[0] * pulse), int(color2[1] * pulse), int(color2[2] * pulse))

        if -6 <= wy < GRID_SIZE:
            self.display.draw_text_small(WONDER_X, wy, "WONDER", color)
        if -6 <= cy < GRID_SIZE:
            self.display.draw_text_small(CABINET_X, cy, "CABINET", color2)


# =========================================================================
# WonderSpin - Words orbit around the center
# =========================================================================

class WonderSpin(Visual):
    name = "WONDER SPIN"
    description = "Orbiting title text"
    category = "digital"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        self.display.clear(Colors.BLACK)
        t = self.time

        # Both words orbit center, 180 degrees apart
        orbit_speed = 0.6
        angle = t * orbit_speed * math.pi * 2

        cx_screen = GRID_SIZE // 2
        cy_screen = GRID_SIZE // 2
        radius_x = 20
        radius_y = 16

        # WONDER position (orbits)
        wx = int(cx_screen + radius_x * math.cos(angle) - WONDER_W // 2)
        wy = int(cy_screen + radius_y * math.sin(angle) - 3)

        # CABINET position (opposite side)
        cax = int(cx_screen + radius_x * math.cos(angle + math.pi) - CABINET_W // 2)
        cay = int(cy_screen + radius_y * math.sin(angle + math.pi) - 3)

        hue = (t * 0.2) % 1.0

        # Draw back word first (further from viewer based on y)
        pairs = [(wx, wy, "WONDER", hue), (cax, cay, "CABINET", (hue + 0.15) % 1.0)]
        # Sort by y so the "closer" (lower y = further back) draws first
        pairs.sort(key=lambda p: p[1])

        for px, py, text, h in pairs:
            color = _hue_to_rgb(h)
            # Dim text that's in the "back" of the orbit
            depth = (py - cy_screen) / radius_y  # -1 to 1
            bright = 0.5 + 0.5 * ((depth + 1) / 2)
            color = (int(color[0] * bright), int(color[1] * bright), int(color[2] * bright))
            self.display.draw_text_small(px, py, text, color)
