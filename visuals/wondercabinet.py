"""
Wonder Cabinet - Branded idle visuals
======================================
Branded visuals for the Wonder Cabinet arcade.
Motion, game-inspired, film-inspired, and ad-inspired title screens.
"""

import math
import os
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
    """Calculate x position to center text (3px char + 1px space = 4px stride)."""
    width = len(text) * 4 - 1  # 3px per char + 1px gap, minus trailing gap
    return max(0, (GRID_SIZE - width) // 2)


# Precomputed centered x positions
WONDER_X = _center_x("WONDER")   # 20
CABINET_X = _center_x("CABINET")  # 18
WONDER_W = len("WONDER") * 4 - 1   # 23
CABINET_W = len("CABINET") * 4 - 1 # 27
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
    category = "titles"

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
    category = "titles"

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
    category = "titles"

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
    category = "titles"

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
    category = "titles"

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
    category = "titles"

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


# =========================================================================
# WonderPacMan - Pac-Man eats dots, reveals title
# =========================================================================

class WonderPacMan(Visual):
    name = "WONDER PAC"
    description = "Pac-Man reveals title"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        self.display.clear(Colors.BLACK)
        # 8s cycle: pac eats across top half, then bottom half, text stays
        cycle = 8.0
        t = self.time % cycle

        # Pac-Man: 5px yellow circle with mouth
        def draw_pac(px, py, mouth_open, facing_right):
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    if dx * dx + dy * dy <= 5:
                        # Mouth cutout
                        if mouth_open and facing_right and dx > 0 and abs(dy) <= (1 if dx > 1 else 0):
                            continue
                        if mouth_open and not facing_right and dx < 0 and abs(dy) <= (1 if dx < -1 else 0):
                            continue
                        sx, sy = px + dx, py + dy
                        if 0 <= sx < GRID_SIZE and 0 <= sy < GRID_SIZE:
                            self.display.set_pixel(sx, sy, (255, 255, 0))

        # Dot row positions
        dot_y1 = WONDER_Y + 3  # dots at text baseline
        dot_y2 = CABINET_Y + 3

        # Phase 1 (0-3s): Pac moves right eating dots, WONDER appears behind
        if t < 3.0:
            pac_x = int(-3 + (t / 3.0) * (GRID_SIZE + 6))
            mouth = int(t * 8) % 2 == 0
            draw_pac(pac_x, dot_y1, mouth, True)
            # Dots ahead of pac
            for dx in range(pac_x + 5, GRID_SIZE, 8):
                if 0 <= dx < GRID_SIZE:
                    self.display.set_pixel(dx, dot_y1, (255, 184, 151))
            # WONDER revealed behind pac
            chars_revealed = max(0, min(6, int((pac_x - WONDER_X) / 5) + 1))
            if chars_revealed > 0:
                revealed = "WONDER"[:chars_revealed]
                self.display.draw_text_small(WONDER_X, WONDER_Y, revealed, Colors.WHITE)

        # Phase 2 (3-6s): Pac returns left eating dots, CABINET appears behind
        elif t < 6.0:
            pt = t - 3.0
            pac_x = int(GRID_SIZE + 3 - (pt / 3.0) * (GRID_SIZE + 6))
            mouth = int(t * 8) % 2 == 0
            draw_pac(pac_x, dot_y2, mouth, False)
            # Dots ahead of pac (to the left)
            for dx in range(pac_x - 5, -1, -8):
                if 0 <= dx < GRID_SIZE:
                    self.display.set_pixel(dx, dot_y2, (255, 184, 151))
            # Full WONDER
            self.display.draw_text_small(WONDER_X, WONDER_Y, "WONDER", Colors.WHITE)
            # CABINET revealed behind pac (right to left)
            right_edge = CABINET_X + CABINET_W
            chars_revealed = max(0, min(7, int((right_edge - pac_x) / 5) + 1))
            if chars_revealed > 0:
                # Reveal from right side
                start = 7 - chars_revealed
                revealed = "CABINET"[start:]
                rx = CABINET_X + start * 5
                self.display.draw_text_small(rx, CABINET_Y, revealed, Colors.WHITE)

        # Phase 3 (6-8s): Both words shown, gentle color cycle
        else:
            pt = t - 6.0
            hue = (pt * 0.3) % 1.0
            c = _hue_to_rgb(hue)
            self.display.draw_text_small(WONDER_X, WONDER_Y, "WONDER", c)
            c2 = _hue_to_rgb((hue + 0.15) % 1.0)
            self.display.draw_text_small(CABINET_X, CABINET_Y, "CABINET", c2)


# =========================================================================
# WonderInvaders - Space Invader formation reveals title
# =========================================================================

class WonderInvaders(Visual):
    name = "WONDER INVADE"
    description = "Space Invaders title"
    category = "titles"

    # 5x3 invader sprite
    INVADER = [
        [0, 1, 0, 1, 0],
        [1, 1, 1, 1, 1],
        [1, 0, 1, 0, 1],
    ]

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        self.display.clear(Colors.BLACK)
        cycle = 8.0
        t = self.time % cycle

        # Invaders march down from top, text appears after they pass
        march_speed = 8.0  # pixels per second
        sway = int(4 * math.sin(t * 2.0))  # horizontal sway

        # 3 rows of 5 invaders each
        for row in range(3):
            base_y = int(-12 + t * march_speed) + row * 8
            for col in range(5):
                ix = 6 + col * 11 + sway
                iy = base_y
                # Color varies by row
                colors = [(0, 255, 0), (0, 200, 255), (255, 100, 255)]
                c = colors[row % 3]
                # Animate legs
                frame = int(t * 4) % 2
                for dy, srow in enumerate(self.INVADER):
                    for dx, pixel in enumerate(srow):
                        if pixel:
                            px = ix + dx
                            py = iy + dy
                            if frame == 1 and dy == 2:
                                # Alternate leg positions
                                px += (1 if dx < 2 else -1)
                            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                                self.display.set_pixel(px, py, c)

        # Text appears as invaders march past
        inv_front = int(-12 + t * march_speed) + 2 * 8 + 3  # bottom of formation
        if inv_front > WONDER_Y:
            self.display.draw_text_small(WONDER_X, WONDER_Y, "WONDER", Colors.WHITE)
        if inv_front > CABINET_Y:
            self.display.draw_text_small(CABINET_X, CABINET_Y, "CABINET", Colors.WHITE)


# =========================================================================
# WonderTetris - Tetris blocks frame the title
# =========================================================================

class WonderTetris(Visual):
    name = "WONDER TETRIS"
    description = "Tetris blocks title"
    category = "titles"

    PIECE_COLORS = [
        (0, 255, 255),   # I - cyan
        (255, 255, 0),   # O - yellow
        (128, 0, 255),   # T - purple
        (0, 255, 0),     # S - green
        (255, 0, 0),     # Z - red
        (0, 0, 255),     # J - blue
        (255, 165, 0),   # L - orange
    ]

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        # Generate fixed block pattern for sides
        random.seed(99)
        self.blocks = []
        # Left column blocks (x 0-12)
        for y in range(0, GRID_SIZE, 4):
            for x in range(0, 13, 4):
                if random.random() < 0.7:
                    c = random.choice(self.PIECE_COLORS)
                    self.blocks.append((x, y, c))
        # Right column blocks (x 52-63)
        for y in range(0, GRID_SIZE, 4):
            for x in range(52, GRID_SIZE, 4):
                if random.random() < 0.7:
                    c = random.choice(self.PIECE_COLORS)
                    self.blocks.append((x, y, c))
        random.seed()

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        self.display.clear(Colors.BLACK)
        t = self.time

        # Blocks fall into place over first 3 seconds
        for i, (bx, by, color) in enumerate(self.blocks):
            # Stagger: each block has its own drop delay
            delay = (i * 0.03) % 3.0
            if t < delay:
                continue
            drop_t = min(1.0, (t - delay) / 0.5)
            actual_y = int(-4 + drop_t * (by + 4))
            # Draw 4x4 block
            dim = 0.6 + 0.4 * math.sin(t * 2.0 + i * 0.5)
            c = (int(color[0] * dim), int(color[1] * dim), int(color[2] * dim))
            for dy in range(3):
                for dx in range(3):
                    px, py = bx + dx, actual_y + dy
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        self.display.set_pixel(px, py, c)
            # Block border
            for dx in range(4):
                for py_b in [actual_y, actual_y + 3]:
                    px = bx + dx
                    if 0 <= px < GRID_SIZE and 0 <= py_b < GRID_SIZE:
                        self.display.set_pixel(px, py_b, (40, 40, 40))
            for dy in range(4):
                for px_b in [bx, bx + 3]:
                    py_p = actual_y + dy
                    if 0 <= px_b < GRID_SIZE and 0 <= py_p < GRID_SIZE:
                        self.display.set_pixel(px_b, py_p, (40, 40, 40))

        # Text appears after blocks settle
        if t > 2.0:
            fade = min(1.0, (t - 2.0) / 0.5)
            c = (int(255 * fade), int(255 * fade), int(255 * fade))
            self.display.draw_text_small(WONDER_X, WONDER_Y, "WONDER", c)
            self.display.draw_text_small(CABINET_X, CABINET_Y, "CABINET", c)


# =========================================================================
# WonderMatrix - Matrix digital rain reveals title
# =========================================================================

class WonderMatrix(Visual):
    name = "WONDER MATRIX"
    description = "Matrix rain title"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        # Rain columns
        self.columns = []
        for x in range(0, GRID_SIZE, 3):
            self.columns.append({
                'x': x,
                'y': random.uniform(-GRID_SIZE, 0),
                'speed': random.uniform(15, 35),
                'length': random.randint(6, 16),
            })

    def update(self, dt: float):
        self.time += dt
        for col in self.columns:
            col['y'] += col['speed'] * dt
            if col['y'] - col['length'] > GRID_SIZE:
                col['y'] = random.uniform(-10, -2)
                col['speed'] = random.uniform(15, 35)
                col['length'] = random.randint(6, 16)

    def draw(self):
        self.display.clear(Colors.BLACK)
        t = self.time

        # Draw rain
        for col in self.columns:
            head = int(col['y'])
            for i in range(col['length']):
                py = head - i
                if 0 <= py < GRID_SIZE:
                    fade = 1.0 - (i / col['length'])
                    if i == 0:
                        c = (180, 255, 180)  # bright head
                    else:
                        g = int(180 * fade)
                        c = (0, g, 0)
                    self.display.set_pixel(col['x'], py, c)
                    if col['x'] + 1 < GRID_SIZE:
                        self.display.set_pixel(col['x'] + 1, py, (0, int(80 * fade), 0))

        # Text burns through in white after 1.5s
        if t > 1.5:
            fade = min(1.0, (t - 1.5) / 1.0)
            glow_g = int(200 * fade)
            # Glow behind text
            for ox in [-1, 0, 1]:
                for oy in [-1, 0, 1]:
                    if ox == 0 and oy == 0:
                        continue
                    self.display.draw_text_small(WONDER_X + ox, WONDER_Y + oy,
                                                 "WONDER", (0, glow_g // 3, 0))
                    self.display.draw_text_small(CABINET_X + ox, CABINET_Y + oy,
                                                 "CABINET", (0, glow_g // 3, 0))
            bright = int(255 * fade)
            self.display.draw_text_small(WONDER_X, WONDER_Y,
                                         "WONDER", (bright, 255, bright))
            self.display.draw_text_small(CABINET_X, CABINET_Y,
                                         "CABINET", (bright, 255, bright))


# =========================================================================
# WonderNeon - Neon sign flickers on letter by letter
# =========================================================================

class WonderNeon(Visual):
    name = "WONDER NEON"
    description = "Neon sign title"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        # Random flicker seeds for each letter
        self.flicker_seeds = [random.random() * 100 for _ in range(13)]

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        self.display.clear(Colors.BLACK)
        t = self.time
        cycle = 10.0
        ct = t % cycle

        text = "WONDER CABINET"
        # Letters turn on one by one over 4 seconds
        letters_on = min(13, int(ct / 0.3))

        # Neon pink/blue colors
        neon_w = (255, 50, 150)  # hot pink for WONDER
        neon_c = (50, 150, 255)  # electric blue for CABINET

        for i, ch in enumerate("WONDER"):
            if i >= letters_on:
                break
            x = WONDER_X + i * 5
            # Flicker effect: newly lit letters flicker more
            age = ct - i * 0.3
            if age < 0.6:
                # Flickering on
                flick = math.sin(age * 30 + self.flicker_seeds[i]) > -0.3
                if not flick:
                    continue
            # Steady glow with subtle pulse
            pulse = 0.85 + 0.15 * math.sin(t * 3 + i)
            c = (int(neon_w[0] * pulse), int(neon_w[1] * pulse), int(neon_w[2] * pulse))
            # Glow
            glow = (c[0] // 5, c[1] // 5, c[2] // 5)
            for ox in [-1, 0, 1]:
                for oy in [-1, 0, 1]:
                    if ox == 0 and oy == 0:
                        continue
                    self.display.draw_text_small(x + ox, WONDER_Y + oy, ch, glow)
            self.display.draw_text_small(x, WONDER_Y, ch, c)

        for i, ch in enumerate("CABINET"):
            li = i + 6  # letter index in full sequence
            if li >= letters_on:
                break
            x = CABINET_X + i * 5
            age = ct - li * 0.3
            if age < 0.6:
                flick = math.sin(age * 30 + self.flicker_seeds[li]) > -0.3
                if not flick:
                    continue
            pulse = 0.85 + 0.15 * math.sin(t * 3 + li)
            c = (int(neon_c[0] * pulse), int(neon_c[1] * pulse), int(neon_c[2] * pulse))
            glow = (c[0] // 5, c[1] // 5, c[2] // 5)
            for ox in [-1, 0, 1]:
                for oy in [-1, 0, 1]:
                    if ox == 0 and oy == 0:
                        continue
                    self.display.draw_text_small(x + ox, CABINET_Y + oy, ch, glow)
            self.display.draw_text_small(x, CABINET_Y, ch, c)


# =========================================================================
# WonderFilm - Old film countdown leader then title card
# =========================================================================

class WonderFilm(Visual):
    name = "WONDER FILM"
    description = "Film countdown title"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        self.display.clear(Colors.BLACK)
        cycle = 8.0
        t = self.time % cycle
        cx, cy = GRID_SIZE // 2, GRID_SIZE // 2

        if t < 4.5:
            # Countdown: 3, 2, 1
            num_idx = int(t / 1.5)
            num = str(3 - num_idx)
            phase = (t % 1.5) / 1.5  # 0-1 within each number

            # Sepia/amber film tones
            film_color = (200, 170, 100)
            dim_color = (80, 68, 40)

            # Countdown circle
            radius = 20
            segments = 32
            sweep = phase  # pie sweep from 0 to 1
            for i in range(segments):
                frac = i / segments
                if frac > sweep:
                    break
                angle = -math.pi / 2 + frac * 2 * math.pi
                px = int(cx + radius * math.cos(angle))
                py = int(cy + radius * math.sin(angle))
                if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                    self.display.set_pixel(px, py, film_color)

            # Cross hairs
            for i in range(-2, 3):
                if 0 <= cx + i < GRID_SIZE:
                    self.display.set_pixel(cx + i, cy, dim_color)
                if 0 <= cy + i < GRID_SIZE:
                    self.display.set_pixel(cx, cy + i, dim_color)

            # Number in center
            nx = _center_x(num)
            self.display.draw_text_small(nx, cy - 3, num, film_color)

            # Film grain
            random.seed(int(t * 10))
            for _ in range(15):
                gx = random.randint(0, GRID_SIZE - 1)
                gy = random.randint(0, GRID_SIZE - 1)
                self.display.set_pixel(gx, gy, (40, 35, 20))
            random.seed()

        elif t < 4.8:
            # Brief white flash
            bright = int(255 * (1.0 - (t - 4.5) / 0.3))
            for y in range(GRID_SIZE):
                for x in range(0, GRID_SIZE, 4):
                    self.display.set_pixel(x, y, (bright, bright, bright))

        else:
            # Title card - elegant with border
            # Double-line border
            for i in range(GRID_SIZE):
                self.display.set_pixel(i, 3, (180, 150, 80))
                self.display.set_pixel(i, GRID_SIZE - 4, (180, 150, 80))
                self.display.set_pixel(i, 5, (100, 85, 45))
                self.display.set_pixel(i, GRID_SIZE - 6, (100, 85, 45))
            for i in range(3, GRID_SIZE - 3):
                self.display.set_pixel(3, i, (180, 150, 80))
                self.display.set_pixel(GRID_SIZE - 4, i, (180, 150, 80))
                self.display.set_pixel(5, i, (100, 85, 45))
                self.display.set_pixel(GRID_SIZE - 4 - 2, i, (100, 85, 45))

            # Text in warm white
            self.display.draw_text_small(WONDER_X, WONDER_Y, "WONDER", (255, 240, 200))
            self.display.draw_text_small(CABINET_X, CABINET_Y, "CABINET", (255, 240, 200))

            # Subtle grain
            random.seed(int(t * 5))
            for _ in range(8):
                gx = random.randint(6, GRID_SIZE - 7)
                gy = random.randint(6, GRID_SIZE - 7)
                self.display.set_pixel(gx, gy, (35, 30, 18))
            random.seed()


# =========================================================================
# WonderRetroTV - CRT static tunes into title
# =========================================================================

class WonderRetroTV(Visual):
    name = "WONDER TV"
    description = "Retro TV static title"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        self.display.clear(Colors.BLACK)
        cycle = 7.0
        t = self.time % cycle

        if t < 2.5:
            # Static noise gradually clearing
            clarity = t / 2.5  # 0 = pure static, 1 = clear
            # Static
            noise_amount = 1.0 - clarity
            for y in range(GRID_SIZE):
                for x in range(0, GRID_SIZE, 2):
                    if random.random() < noise_amount:
                        gray = random.randint(0, 120)
                        self.display.set_pixel(x, y, (gray, gray, gray))
            # Scan line
            scan_y = int((t * 20) % GRID_SIZE)
            for x in range(GRID_SIZE):
                if 0 <= scan_y < GRID_SIZE:
                    self.display.set_pixel(x, scan_y, (60, 60, 60))

            # Text fading in through static
            if clarity > 0.3:
                text_alpha = (clarity - 0.3) / 0.7
                # Horizontal distortion
                distort = int((1.0 - clarity) * 8 * math.sin(t * 15))
                c = int(255 * text_alpha)
                # CRT phosphor green-ish tint
                color = (int(c * 0.8), c, int(c * 0.8))
                self.display.draw_text_small(WONDER_X + distort, WONDER_Y, "WONDER", color)
                self.display.draw_text_small(CABINET_X - distort, CABINET_Y, "CABINET", color)

        else:
            # Clear display with scan lines and text
            # CRT scan line effect (every other row dimmed)
            for y in range(0, GRID_SIZE, 2):
                for x in range(GRID_SIZE):
                    self.display.set_pixel(x, y, (4, 4, 4))

            # Subtle CRT curve vignette (dim corners)
            for y in range(GRID_SIZE):
                for x in [0, 1, GRID_SIZE - 2, GRID_SIZE - 1]:
                    self.display.set_pixel(x, y, (2, 2, 2))

            # Phosphor glow text
            pulse = 0.85 + 0.15 * math.sin(t * 2.0)
            c = (int(200 * pulse), int(255 * pulse), int(200 * pulse))
            self.display.draw_text_small(WONDER_X, WONDER_Y, "WONDER", c)
            self.display.draw_text_small(CABINET_X, CABINET_Y, "CABINET", c)


# =========================================================================
# WonderDK - Donkey Kong girder-style with climbing
# =========================================================================

class WonderDK(Visual):
    name = "WONDER DK"
    description = "Donkey Kong girder title"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        self.display.clear(Colors.BLACK)
        t = self.time

        # Red girders (slanted platforms like DK)
        girder_color = (200, 50, 50)
        rivet_color = (255, 150, 50)
        for row in range(5):
            gy = 8 + row * 12
            slant = (row % 2) * 2 - 1  # alternating slant
            for x in range(GRID_SIZE):
                py = gy + int(slant * x * 0.05)
                if 0 <= py < GRID_SIZE:
                    self.display.set_pixel(x, py, girder_color)
                    if 0 <= py + 1 < GRID_SIZE:
                        self.display.set_pixel(x, py + 1, (140, 30, 30))
            # Rivets
            for rx in range(4, GRID_SIZE, 12):
                py = gy + int(slant * rx * 0.05)
                if 0 <= py < GRID_SIZE:
                    self.display.set_pixel(rx, py, rivet_color)

        # Ladders
        ladder_color = (100, 200, 255)
        for lx in [15, 48]:
            for ly in range(8, 56):
                self.display.set_pixel(lx, ly, ladder_color)
                self.display.set_pixel(lx + 4, ly, ladder_color)
                if ly % 4 == 0:
                    for rx in range(lx, lx + 5):
                        self.display.set_pixel(rx, ly, ladder_color)

        # Text on top of girders
        pulse = 0.8 + 0.2 * math.sin(t * 3.0)
        c = (int(255 * pulse), int(255 * pulse), int(50 * pulse))
        self.display.draw_text_small(WONDER_X, 18, "WONDER", c)
        self.display.draw_text_small(CABINET_X, 40, "CABINET", c)


# =========================================================================
# WonderFrogger - Cars/logs crossing, text on safe zones
# =========================================================================

class WonderFrogger(Visual):
    name = "WONDER FROG"
    description = "Frogger lane title"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        self.display.clear(Colors.BLACK)
        t = self.time

        # Road lanes (dark gray)
        for lane in range(4):
            ly = 10 + lane * 8
            for x in range(GRID_SIZE):
                self.display.set_pixel(x, ly + 3, (30, 30, 30))  # lane divider

            # Cars/trucks moving
            speed = (12 + lane * 5) * (1 if lane % 2 == 0 else -1)
            car_colors = [(255, 0, 0), (0, 0, 255), (255, 255, 0), (255, 100, 0)]
            for car_i in range(3):
                cx = int((car_i * 22 + t * speed) % (GRID_SIZE + 10) - 5)
                c = car_colors[lane]
                for dx in range(6):
                    for dy in range(3):
                        px = cx + dx
                        py = ly + dy
                        if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                            self.display.set_pixel(px, py, c)

        # Water lanes with logs (top area)
        water_color = (0, 0, 80)
        for y in range(0, 8):
            for x in range(GRID_SIZE):
                self.display.set_pixel(x, y, water_color)

        # Safe zones (green strips) where text sits
        for x in range(GRID_SIZE):
            for dy in range(6):
                self.display.set_pixel(x, WONDER_Y - 1 + dy, (0, 40, 0))
                self.display.set_pixel(x, CABINET_Y - 1 + dy, (0, 40, 0))

        # Text on safe zones
        self.display.draw_text_small(WONDER_X, WONDER_Y, "WONDER", (255, 255, 255))
        self.display.draw_text_small(CABINET_X, CABINET_Y, "CABINET", (255, 255, 255))


# =========================================================================
# Text mask helper for automata seeding
# =========================================================================

# 3x5 font data (same as arcade.py)
_FONT = {
    'W': ['101', '101', '111', '111', '101'],
    'O': ['010', '101', '101', '101', '010'],
    'N': ['101', '111', '111', '111', '101'],
    'D': ['110', '101', '101', '101', '110'],
    'E': ['111', '100', '110', '100', '111'],
    'R': ['110', '101', '110', '101', '101'],
    'C': ['011', '100', '100', '100', '011'],
    'A': ['010', '101', '111', '101', '101'],
    'B': ['110', '101', '110', '101', '110'],
    'I': ['111', '010', '010', '010', '111'],
    'T': ['111', '010', '010', '010', '010'],
}


def _text_mask():
    """Return a 64x64 boolean grid with WONDER CABINET text pixels set True."""
    mask = [[False] * GRID_SIZE for _ in range(GRID_SIZE)]
    for text, tx, ty in [("WONDER", WONDER_X, WONDER_Y),
                          ("CABINET", CABINET_X, CABINET_Y)]:
        cx = tx
        for ch in text:
            glyph = _FONT.get(ch)
            if glyph:
                for row_i, row in enumerate(glyph):
                    for col_i, pixel in enumerate(row):
                        if pixel == '1':
                            px, py = cx + col_i, ty + row_i
                            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                                mask[py][px] = True
            cx += 4  # 3px char + 1px gap
    return mask


# --- Snapshot helpers (memory-efficient bytes storage) ---

_SZ = GRID_SIZE * GRID_SIZE  # 4096

def _snap(grid):
    """Save a 2D grid to a compact bytes snapshot."""
    flat = bytearray(_SZ)
    i = 0
    for row in grid:
        for val in row:
            flat[i] = int(val) & 0xFF
            i += 1
    return bytes(flat)


def _restore(snapshot, as_bool=False):
    """Restore a 2D grid from a bytes snapshot."""
    grid = []
    i = 0
    for y in range(GRID_SIZE):
        row = []
        for x in range(GRID_SIZE):
            v = snapshot[i]
            row.append(bool(v) if as_bool else v)
            i += 1
        grid.append(row)
    return grid


# Phase constants
_TEXT_HOLD = 2.0    # seconds to show static text
_FORWARD = 10.0     # seconds of forward CA evolution
_MAX_SNAPS = 120    # cap on stored snapshots


# =========================================================================
# WonderLife - Game of Life seeded with title text
# =========================================================================

class WonderLife(Visual):
    name = "WONDER LIFE"
    description = "Game of Life title seed"
    category = "titles"
    _INTERVAL = 0.12

    def __init__(self, display: Display):
        super().__init__(display)

    def _init_grid(self):
        mask = _text_mask()
        self.grid = [[False] * GRID_SIZE for _ in range(GRID_SIZE)]
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if mask[y][x]:
                    self.grid[y][x] = True

    def reset(self):
        self.time = 0.0
        self.phase = 'text'
        self.phase_timer = 0.0
        self.step_accum = 0.0
        self.history = []
        self.rev_idx = 0
        self._init_grid()

    def _count(self, x, y):
        n = 0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                if self.grid[(y + dy) % GRID_SIZE][(x + dx) % GRID_SIZE]:
                    n += 1
        return n

    def _step(self):
        new = [[False] * GRID_SIZE for _ in range(GRID_SIZE)]
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                n = self._count(x, y)
                if self.grid[y][x]:
                    new[y][x] = n in (2, 3)
                else:
                    new[y][x] = n == 3
        self.grid = new

    def update(self, dt: float):
        self.time += dt
        self.phase_timer += dt
        if self.phase == 'text':
            if self.phase_timer >= _TEXT_HOLD:
                self.phase = 'forward'
                self.phase_timer = 0.0
                self.step_accum = 0.0
                self.history = [_snap(self.grid)]
        elif self.phase == 'forward':
            self.step_accum += dt
            while self.step_accum >= self._INTERVAL:
                self.step_accum -= self._INTERVAL
                self._step()
                if len(self.history) < _MAX_SNAPS:
                    self.history.append(_snap(self.grid))
            if self.phase_timer >= _FORWARD:
                self.phase = 'reverse'
                self.phase_timer = 0.0
                self.step_accum = 0.0
                self.rev_idx = len(self.history) - 1
        elif self.phase == 'reverse':
            self.step_accum += dt
            while self.step_accum >= self._INTERVAL and self.rev_idx > 0:
                self.step_accum -= self._INTERVAL
                self.rev_idx -= 1
                self.grid = _restore(self.history[self.rev_idx], as_bool=True)
            if self.rev_idx <= 0:
                self.phase = 'text'
                self.phase_timer = 0.0
                self.grid = _restore(self.history[0], as_bool=True)
                self.history = []

    def draw(self):
        self.display.clear(Colors.BLACK)
        hue = (self.time * 0.05) % 1.0
        color = _hue_to_rgb(hue)
        if self.phase == 'text':
            self.display.draw_text_small(WONDER_X, WONDER_Y, "WONDER", color)
            self.display.draw_text_small(CABINET_X, CABINET_Y, "CABINET", color)
        else:
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    if self.grid[y][x]:
                        self.display.set_pixel(x, y, color)


# =========================================================================
# WonderHodge - Hodgepodge machine seeded with title text
# =========================================================================

class WonderHodge(Visual):
    name = "WONDER HODGE"
    description = "BZ reaction title seed"
    category = "titles"
    _INTERVAL = 0.08

    def __init__(self, display: Display):
        super().__init__(display)

    def _init_grid(self):
        mask = _text_mask()
        self.grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.next_grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if mask[y][x]:
                    self.grid[y][x] = (x * 7 + y * 3) % (self.n + 1)

    def reset(self):
        self.time = 0.0
        self.phase = 'text'
        self.phase_timer = 0.0
        self.step_accum = 0.0
        self.history = []
        self.rev_idx = 0
        self.n = 63
        self.k1 = 2
        self.k2 = 3
        self.g = 5
        self.colors = [(0, 0, 0)] + [_hue_to_rgb(i / 63) for i in range(1, 64)]
        self._init_grid()

    def _step(self):
        n = self.n
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                state = self.grid[y][x]
                if state == n:
                    self.next_grid[y][x] = 0
                elif state == 0:
                    infected = ill = 0
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            if dx == 0 and dy == 0:
                                continue
                            ns = self.grid[(y + dy) % GRID_SIZE][(x + dx) % GRID_SIZE]
                            if ns == n:
                                ill += 1
                            elif ns > 0:
                                infected += 1
                    self.next_grid[y][x] = min(n, infected // self.k1 + ill // self.k2)
                else:
                    total = count = 0
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            total += self.grid[(y + dy) % GRID_SIZE][(x + dx) % GRID_SIZE]
                            count += 1
                    self.next_grid[y][x] = min(n, total // count + self.g)
        self.grid, self.next_grid = self.next_grid, self.grid

    def update(self, dt: float):
        self.time += dt
        self.phase_timer += dt
        if self.phase == 'text':
            if self.phase_timer >= _TEXT_HOLD:
                self.phase = 'forward'
                self.phase_timer = 0.0
                self.step_accum = 0.0
                self.history = [_snap(self.grid)]
        elif self.phase == 'forward':
            self.step_accum += dt
            while self.step_accum >= self._INTERVAL:
                self.step_accum -= self._INTERVAL
                self._step()
                if len(self.history) < _MAX_SNAPS:
                    self.history.append(_snap(self.grid))
            if self.phase_timer >= _FORWARD:
                self.phase = 'reverse'
                self.phase_timer = 0.0
                self.step_accum = 0.0
                self.rev_idx = len(self.history) - 1
        elif self.phase == 'reverse':
            self.step_accum += dt
            while self.step_accum >= self._INTERVAL and self.rev_idx > 0:
                self.step_accum -= self._INTERVAL
                self.rev_idx -= 1
                self.grid = _restore(self.history[self.rev_idx])
            if self.rev_idx <= 0:
                self.phase = 'text'
                self.phase_timer = 0.0
                self.grid = _restore(self.history[0])
                self.history = []

    def draw(self):
        if self.phase == 'text':
            self.display.clear(Colors.BLACK)
            c = self.colors[self.n]
            self.display.draw_text_small(WONDER_X, WONDER_Y, "WONDER", c)
            self.display.draw_text_small(CABINET_X, CABINET_Y, "CABINET", c)
        else:
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    self.display.set_pixel(x, y, self.colors[self.grid[y][x]])


# =========================================================================
# WonderStarWars - Generations CA (345/2/4) seeded with title text
# =========================================================================

class WonderStarWars(Visual):
    name = "WONDER WARS"
    description = "Star Wars CA title seed"
    category = "titles"
    _INTERVAL = 0.1

    PALETTES = [
        ((0, 0, 0), (220, 255, 255), (40, 80, 200), (25, 10, 80)),
        ((0, 0, 0), (255, 240, 80), (255, 120, 20), (100, 20, 0)),
        ((0, 0, 0), (100, 255, 100), (0, 150, 50), (0, 50, 20)),
        ((0, 0, 0), (255, 255, 255), (220, 50, 220), (60, 0, 80)),
    ]

    def __init__(self, display: Display):
        super().__init__(display)

    def _init_grid(self):
        mask = _text_mask()
        self.grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.next_grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if mask[y][x]:
                    self.grid[y][x] = 1

    def reset(self):
        self.time = 0.0
        self.phase = 'text'
        self.phase_timer = 0.0
        self.step_accum = 0.0
        self.history = []
        self.rev_idx = 0
        self.palette = random.choice(self.PALETTES)
        self._init_grid()

    def _step(self):
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                state = self.grid[y][x]
                if state == 0:
                    alive_n = 0
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            if dx == 0 and dy == 0:
                                continue
                            if self.grid[(y + dy) % GRID_SIZE][(x + dx) % GRID_SIZE] == 1:
                                alive_n += 1
                    self.next_grid[y][x] = 1 if alive_n == 2 else 0
                elif state == 1:
                    alive_n = 0
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            if dx == 0 and dy == 0:
                                continue
                            if self.grid[(y + dy) % GRID_SIZE][(x + dx) % GRID_SIZE] == 1:
                                alive_n += 1
                    self.next_grid[y][x] = 1 if alive_n in (3, 4, 5) else 2
                else:
                    self.next_grid[y][x] = (state + 1) if state + 1 < 4 else 0
        self.grid, self.next_grid = self.next_grid, self.grid

    def update(self, dt: float):
        self.time += dt
        self.phase_timer += dt
        if self.phase == 'text':
            if self.phase_timer >= _TEXT_HOLD:
                self.phase = 'forward'
                self.phase_timer = 0.0
                self.step_accum = 0.0
                self.history = [_snap(self.grid)]
        elif self.phase == 'forward':
            self.step_accum += dt
            while self.step_accum >= self._INTERVAL:
                self.step_accum -= self._INTERVAL
                self._step()
                if len(self.history) < _MAX_SNAPS:
                    self.history.append(_snap(self.grid))
            if self.phase_timer >= _FORWARD:
                self.phase = 'reverse'
                self.phase_timer = 0.0
                self.step_accum = 0.0
                self.rev_idx = len(self.history) - 1
        elif self.phase == 'reverse':
            self.step_accum += dt
            while self.step_accum >= self._INTERVAL and self.rev_idx > 0:
                self.step_accum -= self._INTERVAL
                self.rev_idx -= 1
                self.grid = _restore(self.history[self.rev_idx])
            if self.rev_idx <= 0:
                self.phase = 'text'
                self.phase_timer = 0.0
                self.grid = _restore(self.history[0])
                self.history = []

    def draw(self):
        p = self.palette
        if self.phase == 'text':
            self.display.clear(Colors.BLACK)
            self.display.draw_text_small(WONDER_X, WONDER_Y, "WONDER", p[1])
            self.display.draw_text_small(CABINET_X, CABINET_Y, "CABINET", p[1])
        else:
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    self.display.set_pixel(x, y, p[self.grid[y][x]])


# =========================================================================
# WonderSpirals - Cyclic CA seeded with title text
# =========================================================================

# =========================================================================
# WonderBoids - Boid flocking seeded from title text pixels
# =========================================================================

class WonderBoids(Visual):
    name = "WONDER FLOCK"
    description = "Boid flocking from title seed"
    category = "titles"
    _INTERVAL = 1.0 / 10

    def __init__(self, display: Display):
        super().__init__(display)

    def _init_grid(self):
        mask = _text_mask()
        self.grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.boids = []
        count = 0
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if mask[y][x]:
                    self.grid[y][x] = 255
                    count += 1
                    if count % 2 == 0:
                        continue
                    angle = (x * 0.7 + y * 1.3) % (2 * math.pi)
                    self.boids.append([float(x), float(y),
                                       math.cos(angle) * 0.8,
                                       math.sin(angle) * 0.8])

    def reset(self):
        self.time = 0.0
        self.phase = 'text'
        self.phase_timer = 0.0
        self.step_accum = 0.0
        self.history = []
        self.rev_idx = 0
        self._init_grid()

    def _step(self):
        # Decay trail
        for y in range(GRID_SIZE):
            row = self.grid[y]
            for x in range(GRID_SIZE):
                if row[x] > 0:
                    row[x] = max(0, row[x] - 6)
        N = len(self.boids)
        if N == 0:
            return
        for i in range(N):
            bx, by, bvx, bvy = self.boids[i]
            sx, sy, ax, ay, cx, cy = 0., 0., 0., 0., 0., 0.
            sc, ac, cc = 0, 0, 0
            for j in range(N):
                if i == j:
                    continue
                ox, oy = self.boids[j][0], self.boids[j][1]
                dx = ox - bx
                dy = oy - by
                # Wrap distance
                if dx > 32: dx -= 64
                elif dx < -32: dx += 64
                if dy > 32: dy -= 64
                elif dy < -32: dy += 64
                d = math.sqrt(dx * dx + dy * dy)
                if d < 0.5:
                    continue
                if d < 3.0:
                    sx -= dx / d
                    sy -= dy / d
                    sc += 1
                if d < 8.0:
                    ax += self.boids[j][2]
                    ay += self.boids[j][3]
                    ac += 1
                if d < 12.0:
                    cx += dx
                    cy += dy
                    cc += 1
            if sc > 0:
                bvx += sx * 0.15
                bvy += sy * 0.15
            if ac > 0:
                bvx += (ax / ac - bvx) * 0.05
                bvy += (ay / ac - bvy) * 0.05
            if cc > 0:
                bvx += (cx / cc) * 0.01
                bvy += (cy / cc) * 0.01
            speed = math.sqrt(bvx * bvx + bvy * bvy)
            if speed > 1.5:
                bvx = bvx / speed * 1.5
                bvy = bvy / speed * 1.5
            elif speed < 0.3:
                bvx = bvx / max(speed, 0.01) * 0.3
                bvy = bvy / max(speed, 0.01) * 0.3
            bx = (bx + bvx) % GRID_SIZE
            by = (by + bvy) % GRID_SIZE
            self.boids[i] = [bx, by, bvx, bvy]
            ix = int(bx) % GRID_SIZE
            iy = int(by) % GRID_SIZE
            self.grid[iy][ix] = 255

    def update(self, dt: float):
        self.time += dt
        self.phase_timer += dt
        if self.phase == 'text':
            if self.phase_timer >= _TEXT_HOLD:
                self.phase = 'forward'
                self.phase_timer = 0.0
                self.step_accum = 0.0
                self.history = [_snap(self.grid)]
        elif self.phase == 'forward':
            self.step_accum += dt
            while self.step_accum >= self._INTERVAL:
                self.step_accum -= self._INTERVAL
                self._step()
                if len(self.history) < _MAX_SNAPS:
                    self.history.append(_snap(self.grid))
            if self.phase_timer >= _FORWARD:
                self.phase = 'reverse'
                self.phase_timer = 0.0
                self.step_accum = 0.0
                self.rev_idx = len(self.history) - 1
        elif self.phase == 'reverse':
            self.step_accum += dt
            while self.step_accum >= self._INTERVAL and self.rev_idx > 0:
                self.step_accum -= self._INTERVAL
                self.rev_idx -= 1
                self.grid = _restore(self.history[self.rev_idx])
            if self.rev_idx <= 0:
                self.phase = 'text'
                self.phase_timer = 0.0
                self.grid = _restore(self.history[0])
                self.history = []
                self._init_grid()

    def draw(self):
        if self.phase == 'text':
            self.display.clear(Colors.BLACK)
            self.display.draw_text_small(WONDER_X, WONDER_Y, "WONDER", (255, 180, 60))
            self.display.draw_text_small(CABINET_X, CABINET_Y, "CABINET", (255, 180, 60))
        else:
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    v = self.grid[y][x]
                    if v > 0:
                        t = v / 255.0
                        r = int(255 * t)
                        g = int(140 * t)
                        b = int(30 * t * t)
                        self.display.set_pixel(x, y, (r, g, b))
                    else:
                        self.display.set_pixel(x, y, (0, 0, 0))


# =========================================================================
# WonderSlime - Slime mold agents seeded from title text pixels
# =========================================================================

class WonderSlime(Visual):
    name = "WONDER SLIME"
    description = "Slime mold from title seed"
    category = "titles"
    _INTERVAL = 1.0 / 20

    def __init__(self, display: Display):
        super().__init__(display)

    def _init_grid(self):
        mask = _text_mask()
        self.grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.agents = []
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if mask[y][x]:
                    self.grid[y][x] = 255
                    angle = (x * 2.1 + y * 0.7) % (2 * math.pi)
                    self.agents.append([float(x), float(y), angle])

    def reset(self):
        self.time = 0.0
        self.phase = 'text'
        self.phase_timer = 0.0
        self.step_accum = 0.0
        self.history = []
        self.rev_idx = 0
        self._init_grid()

    def _step(self):
        SZ = GRID_SIZE
        trail = self.grid
        sensor_dist = 4.0
        sensor_angle = 0.6
        turn_speed = 0.4
        deposit = 80
        # Move agents
        for a in self.agents:
            x, y, angle = a[0], a[1], a[2]
            # Sense left, center, right
            sl = sr = sc_val = 0
            for da, accum in ((-sensor_angle, 'l'), (0, 'c'), (sensor_angle, 'r')):
                sa = angle + da
                sx = int(x + math.cos(sa) * sensor_dist) % SZ
                sy = int(y + math.sin(sa) * sensor_dist) % SZ
                val = trail[sy][sx]
                if da < 0:
                    sl = val
                elif da > 0:
                    sr = val
                else:
                    sc_val = val
            # Steer toward strongest trail
            if sc_val >= sl and sc_val >= sr:
                pass  # go straight
            elif sl > sr:
                angle -= turn_speed
            elif sr > sl:
                angle += turn_speed
            # Move
            nx = (x + math.cos(angle) * 1.0) % SZ
            ny = (y + math.sin(angle) * 1.0) % SZ
            a[0], a[1], a[2] = nx, ny, angle
            # Deposit
            ix, iy = int(nx) % SZ, int(ny) % SZ
            trail[iy][ix] = min(255, trail[iy][ix] + deposit)
        # Diffuse and decay
        new = [row[:] for row in trail]
        for y in range(SZ):
            for x in range(SZ):
                total = 0
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        total += trail[(y + dy) % SZ][(x + dx) % SZ]
                new[y][x] = max(0, total // 9 - 2)
        self.grid = new

    def update(self, dt: float):
        self.time += dt
        self.phase_timer += dt
        if self.phase == 'text':
            if self.phase_timer >= _TEXT_HOLD:
                self.phase = 'forward'
                self.phase_timer = 0.0
                self.step_accum = 0.0
                self.history = [_snap(self.grid)]
        elif self.phase == 'forward':
            self.step_accum += dt
            while self.step_accum >= self._INTERVAL:
                self.step_accum -= self._INTERVAL
                self._step()
                if len(self.history) < _MAX_SNAPS:
                    self.history.append(_snap(self.grid))
            if self.phase_timer >= _FORWARD:
                self.phase = 'reverse'
                self.phase_timer = 0.0
                self.step_accum = 0.0
                self.rev_idx = len(self.history) - 1
        elif self.phase == 'reverse':
            self.step_accum += dt
            while self.step_accum >= self._INTERVAL and self.rev_idx > 0:
                self.step_accum -= self._INTERVAL
                self.rev_idx -= 1
                self.grid = _restore(self.history[self.rev_idx])
            if self.rev_idx <= 0:
                self.phase = 'text'
                self.phase_timer = 0.0
                self.grid = _restore(self.history[0])
                self.history = []
                self._init_grid()

    def draw(self):
        if self.phase == 'text':
            self.display.clear(Colors.BLACK)
            self.display.draw_text_small(WONDER_X, WONDER_Y, "WONDER", (80, 255, 80))
            self.display.draw_text_small(CABINET_X, CABINET_Y, "CABINET", (80, 255, 80))
        else:
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    v = self.grid[y][x]
                    if v > 0:
                        t = v / 255.0
                        g = int(255 * t)
                        r = int(80 * t * t)
                        b = int(40 * t * t)
                        self.display.set_pixel(x, y, (r, g, b))
                    else:
                        self.display.set_pixel(x, y, (0, 0, 0))


# =========================================================================
# WonderDiffusion - Heat diffusion from title text pixels
# =========================================================================

class WonderDiffusion(Visual):
    name = "WONDER HEAT"
    description = "Heat diffusion from title seed"
    category = "titles"
    _INTERVAL = 1.0 / 20

    def __init__(self, display: Display):
        super().__init__(display)

    def _init_grid(self):
        mask = _text_mask()
        self.grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if mask[y][x]:
                    self.grid[y][x] = 255

    def reset(self):
        self.time = 0.0
        self.phase = 'text'
        self.phase_timer = 0.0
        self.step_accum = 0.0
        self.history = []
        self.rev_idx = 0
        self._init_grid()

    def _step(self):
        SZ = GRID_SIZE
        old = self.grid
        new = [[0] * SZ for _ in range(SZ)]
        for y in range(SZ):
            for x in range(SZ):
                # 5-point laplacian diffusion
                c = old[y][x]
                n = old[(y - 1) % SZ][x]
                s = old[(y + 1) % SZ][x]
                w = old[y][(x - 1) % SZ]
                e = old[y][(x + 1) % SZ]
                # Diffuse: blend with neighbors, slight decay
                val = c + 0.2 * (n + s + w + e - 4 * c) - 0.3
                new[y][x] = max(0, min(255, int(val)))
        self.grid = new

    def update(self, dt: float):
        self.time += dt
        self.phase_timer += dt
        if self.phase == 'text':
            if self.phase_timer >= _TEXT_HOLD:
                self.phase = 'forward'
                self.phase_timer = 0.0
                self.step_accum = 0.0
                self.history = [_snap(self.grid)]
        elif self.phase == 'forward':
            self.step_accum += dt
            while self.step_accum >= self._INTERVAL:
                self.step_accum -= self._INTERVAL
                self._step()
                if len(self.history) < _MAX_SNAPS:
                    self.history.append(_snap(self.grid))
            if self.phase_timer >= _FORWARD:
                self.phase = 'reverse'
                self.phase_timer = 0.0
                self.step_accum = 0.0
                self.rev_idx = len(self.history) - 1
        elif self.phase == 'reverse':
            self.step_accum += dt
            while self.step_accum >= self._INTERVAL and self.rev_idx > 0:
                self.step_accum -= self._INTERVAL
                self.rev_idx -= 1
                self.grid = _restore(self.history[self.rev_idx])
            if self.rev_idx <= 0:
                self.phase = 'text'
                self.phase_timer = 0.0
                self.grid = _restore(self.history[0])
                self.history = []

    def draw(self):
        if self.phase == 'text':
            self.display.clear(Colors.BLACK)
            self.display.draw_text_small(WONDER_X, WONDER_Y, "WONDER", (255, 200, 100))
            self.display.draw_text_small(CABINET_X, CABINET_Y, "CABINET", (255, 200, 100))
        else:
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    v = self.grid[y][x]
                    if v > 0:
                        t = v / 255.0
                        r = int(255 * min(1.0, t * 1.5))
                        g = int(200 * t * t)
                        b = int(80 * t * t * t)
                        self.display.set_pixel(x, y, (r, g, b))
                    else:
                        self.display.set_pixel(x, y, (0, 0, 0))


# =========================================================================
# WonderBrain - Brian's Brain CA seeded from title text pixels
# =========================================================================

class WonderBrain(Visual):
    name = "WONDER BRAIN"
    description = "Brian's Brain from title seed"
    category = "titles"
    _INTERVAL = 0.1

    def __init__(self, display: Display):
        super().__init__(display)

    def _init_grid(self):
        mask = _text_mask()
        # States: 0=off, 1=on, 2=dying
        self.grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.next_grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if mask[y][x]:
                    self.grid[y][x] = 1

    def reset(self):
        self.time = 0.0
        self.phase = 'text'
        self.phase_timer = 0.0
        self.step_accum = 0.0
        self.history = []
        self.rev_idx = 0
        self._init_grid()

    def _step(self):
        SZ = GRID_SIZE
        for y in range(SZ):
            for x in range(SZ):
                state = self.grid[y][x]
                if state == 1:
                    self.next_grid[y][x] = 2  # on -> dying
                elif state == 2:
                    self.next_grid[y][x] = 0  # dying -> off
                else:
                    # Count ON neighbors
                    count = 0
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            if dx == 0 and dy == 0:
                                continue
                            if self.grid[(y + dy) % SZ][(x + dx) % SZ] == 1:
                                count += 1
                    self.next_grid[y][x] = 1 if count == 2 else 0
        self.grid, self.next_grid = self.next_grid, self.grid

    def update(self, dt: float):
        self.time += dt
        self.phase_timer += dt
        if self.phase == 'text':
            if self.phase_timer >= _TEXT_HOLD:
                self.phase = 'forward'
                self.phase_timer = 0.0
                self.step_accum = 0.0
                self.history = [_snap(self.grid)]
        elif self.phase == 'forward':
            self.step_accum += dt
            while self.step_accum >= self._INTERVAL:
                self.step_accum -= self._INTERVAL
                self._step()
                if len(self.history) < _MAX_SNAPS:
                    self.history.append(_snap(self.grid))
            if self.phase_timer >= _FORWARD:
                self.phase = 'reverse'
                self.phase_timer = 0.0
                self.step_accum = 0.0
                self.rev_idx = len(self.history) - 1
        elif self.phase == 'reverse':
            self.step_accum += dt
            while self.step_accum >= self._INTERVAL and self.rev_idx > 0:
                self.step_accum -= self._INTERVAL
                self.rev_idx -= 1
                self.grid = _restore(self.history[self.rev_idx])
            if self.rev_idx <= 0:
                self.phase = 'text'
                self.phase_timer = 0.0
                self.grid = _restore(self.history[0])
                self.history = []

    def draw(self):
        if self.phase == 'text':
            self.display.clear(Colors.BLACK)
            self.display.draw_text_small(WONDER_X, WONDER_Y, "WONDER", (200, 200, 255))
            self.display.draw_text_small(CABINET_X, CABINET_Y, "CABINET", (200, 200, 255))
        else:
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    s = self.grid[y][x]
                    if s == 1:
                        self.display.set_pixel(x, y, (255, 255, 255))
                    elif s == 2:
                        self.display.set_pixel(x, y, (40, 60, 200))
                    else:
                        self.display.set_pixel(x, y, (0, 0, 0))


# =========================================================================
# WonderFlow - Flow field particles seeded from title text pixels
# =========================================================================

class WonderFlow(Visual):
    name = "WONDER FLOW"
    description = "Flow field from title seed"
    category = "titles"
    _INTERVAL = 1.0 / 20

    def __init__(self, display: Display):
        super().__init__(display)

    def _init_grid(self):
        mask = _text_mask()
        self.grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.particles = []
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if mask[y][x]:
                    self.grid[y][x] = 255
                    self.particles.append([float(x), float(y)])

    def reset(self):
        self.time = 0.0
        self.phase = 'text'
        self.phase_timer = 0.0
        self.step_accum = 0.0
        self.history = []
        self.rev_idx = 0
        self.flow_time = 0.0
        self._init_grid()

    def _flow_angle(self, x, y, t):
        """Smooth time-varying flow field from layered sinusoids."""
        return (math.sin(x * 0.12 + t * 0.4) * math.cos(y * 0.1)
                + math.sin(y * 0.15 - t * 0.3) * math.cos(x * 0.08 + t * 0.2)
                ) * math.pi

    def _step(self):
        SZ = GRID_SIZE
        trail = self.grid
        self.flow_time += self._INTERVAL
        t = self.flow_time
        # Decay trail
        for y in range(SZ):
            row = trail[y]
            for x in range(SZ):
                if row[x] > 0:
                    row[x] = max(0, row[x] - 5)
        # Move particles along flow field
        for p in self.particles:
            angle = self._flow_angle(p[0], p[1], t)
            p[0] = (p[0] + math.cos(angle) * 0.8) % SZ
            p[1] = (p[1] + math.sin(angle) * 0.8) % SZ
            ix = int(p[0]) % SZ
            iy = int(p[1]) % SZ
            trail[iy][ix] = 255

    def update(self, dt: float):
        self.time += dt
        self.phase_timer += dt
        if self.phase == 'text':
            if self.phase_timer >= _TEXT_HOLD:
                self.phase = 'forward'
                self.phase_timer = 0.0
                self.step_accum = 0.0
                self.flow_time = 0.0
                self.history = [_snap(self.grid)]
        elif self.phase == 'forward':
            self.step_accum += dt
            while self.step_accum >= self._INTERVAL:
                self.step_accum -= self._INTERVAL
                self._step()
                if len(self.history) < _MAX_SNAPS:
                    self.history.append(_snap(self.grid))
            if self.phase_timer >= _FORWARD:
                self.phase = 'reverse'
                self.phase_timer = 0.0
                self.step_accum = 0.0
                self.rev_idx = len(self.history) - 1
        elif self.phase == 'reverse':
            self.step_accum += dt
            while self.step_accum >= self._INTERVAL and self.rev_idx > 0:
                self.step_accum -= self._INTERVAL
                self.rev_idx -= 1
                self.grid = _restore(self.history[self.rev_idx])
            if self.rev_idx <= 0:
                self.phase = 'text'
                self.phase_timer = 0.0
                self.grid = _restore(self.history[0])
                self.history = []
                self._init_grid()

    def draw(self):
        if self.phase == 'text':
            self.display.clear(Colors.BLACK)
            self.display.draw_text_small(WONDER_X, WONDER_Y, "WONDER", (100, 180, 255))
            self.display.draw_text_small(CABINET_X, CABINET_Y, "CABINET", (100, 180, 255))
        else:
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    v = self.grid[y][x]
                    if v > 0:
                        t = v / 255.0
                        h = (x * 0.02 + y * 0.01 + self.time * 0.1) % 1.0
                        r, g, b = _hue_to_rgb(h)
                        self.display.set_pixel(x, y, (int(r * t), int(g * t), int(b * t)))
                    else:
                        self.display.set_pixel(x, y, (0, 0, 0))


# =========================================================================
# WonderSand - Sandpile seeded with grains at title text pixels
# =========================================================================

class WonderSand(Visual):
    name = "WONDER SAND"
    description = "Sandpile title seed"
    category = "titles"
    _INTERVAL = 0.03

    COLORS = [
        (5, 5, 30),      # 0 grains
        (0, 200, 200),   # 1 grain
        (200, 220, 0),   # 2 grains
        (180, 0, 220),   # 3 grains
        (255, 255, 255), # 4+ (avalanche)
    ]

    def __init__(self, display: Display):
        super().__init__(display)

    def _init_grid(self):
        self.grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        mask = _text_mask()
        # Drop a big pile of grains on each text pixel
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if mask[y][x]:
                    self.grid[y][x] = 16

    def reset(self):
        self.time = 0.0
        self.phase = 'text'
        self.phase_timer = 0.0
        self.step_accum = 0.0
        self.history = []
        self.rev_idx = 0
        self._init_grid()

    def _topple(self):
        changed = False
        new = [row[:] for row in self.grid]
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if self.grid[y][x] >= 4:
                    changed = True
                    new[y][x] -= 4
                    if y > 0: new[y - 1][x] += 1
                    if y < GRID_SIZE - 1: new[y + 1][x] += 1
                    if x > 0: new[y][x - 1] += 1
                    if x < GRID_SIZE - 1: new[y][x + 1] += 1
        self.grid = new
        return changed

    def update(self, dt: float):
        self.time += dt
        self.phase_timer += dt
        if self.phase == 'text':
            if self.phase_timer >= _TEXT_HOLD:
                self.phase = 'forward'
                self.phase_timer = 0.0
                self.step_accum = 0.0
                self.history = [_snap(self.grid)]
        elif self.phase == 'forward':
            self.step_accum += dt
            # Record every 4th step to stay under snapshot cap
            step_count = 0
            while self.step_accum >= self._INTERVAL:
                self.step_accum -= self._INTERVAL
                self._topple()
                step_count += 1
                if step_count % 4 == 0 and len(self.history) < _MAX_SNAPS:
                    self.history.append(_snap(self.grid))
            if self.phase_timer >= _FORWARD:
                self.phase = 'reverse'
                self.phase_timer = 0.0
                self.step_accum = 0.0
                self.rev_idx = len(self.history) - 1
        elif self.phase == 'reverse':
            self.step_accum += dt
            # Play back at ~4x the step interval to match forward pacing
            rev_interval = self._INTERVAL * 4
            while self.step_accum >= rev_interval and self.rev_idx > 0:
                self.step_accum -= rev_interval
                self.rev_idx -= 1
                self.grid = _restore(self.history[self.rev_idx])
            if self.rev_idx <= 0:
                self.phase = 'text'
                self.phase_timer = 0.0
                self.grid = _restore(self.history[0])
                self.history = []

    def draw(self):
        if self.phase == 'text':
            self.display.clear(Colors.BLACK)
            self.display.draw_text_small(WONDER_X, WONDER_Y, "WONDER", (0, 200, 200))
            self.display.draw_text_small(CABINET_X, CABINET_Y, "CABINET", (0, 200, 200))
        else:
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    v = min(self.grid[y][x], 4)
                    self.display.set_pixel(x, y, self.COLORS[v])


# =========================================================================
# WonderPong - Classic Pong rally with score as title text
# =========================================================================

class WonderPong(Visual):
    name = "WONDER PONG"
    description = "Pong rally title"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.ball_x = 32.0
        self.ball_y = 32.0
        self.ball_vx = 25.0
        self.ball_vy = 18.0
        self.paddle_l = 28.0
        self.paddle_r = 28.0
        self.score_l = 0
        self.score_r = 0

    def update(self, dt: float):
        self.time += dt
        # Move ball
        self.ball_x += self.ball_vx * dt
        self.ball_y += self.ball_vy * dt
        # Top/bottom bounce
        if self.ball_y < 6 or self.ball_y > 57:
            self.ball_vy = -self.ball_vy
            self.ball_y = max(6, min(57, self.ball_y))
        # AI paddles track ball
        for attr, bx_check in [('paddle_l', 32), ('paddle_r', 32)]:
            target = self.ball_y
            current = getattr(self, attr)
            speed = 30.0
            diff = target - current
            move = min(abs(diff), speed * dt) * (1 if diff > 0 else -1)
            setattr(self, attr, max(10, min(54, current + move)))
        # Left paddle bounce
        if self.ball_x <= 5:
            if abs(self.ball_y - self.paddle_l) < 7:
                self.ball_vx = abs(self.ball_vx)
                self.ball_vy += (self.ball_y - self.paddle_l) * 2.0
            else:
                self.score_r += 1
                self.ball_x = 32.0
                self.ball_y = 32.0
                self.ball_vx = 25.0
                self.ball_vy = 18.0 * (1 if random.random() > 0.5 else -1)
        # Right paddle bounce
        if self.ball_x >= 59:
            if abs(self.ball_y - self.paddle_r) < 7:
                self.ball_vx = -abs(self.ball_vx)
                self.ball_vy += (self.ball_y - self.paddle_r) * 2.0
            else:
                self.score_l += 1
                self.ball_x = 32.0
                self.ball_y = 32.0
                self.ball_vx = -25.0
                self.ball_vy = 18.0 * (1 if random.random() > 0.5 else -1)
        # Cap velocity
        speed = math.sqrt(self.ball_vx ** 2 + self.ball_vy ** 2)
        if speed > 40:
            self.ball_vx = self.ball_vx / speed * 40
            self.ball_vy = self.ball_vy / speed * 40
        # Reset scores to cycle
        if self.score_l > 9 or self.score_r > 9:
            self.score_l = 0
            self.score_r = 0

    def draw(self):
        self.display.clear(Colors.BLACK)
        # Dashed center line
        for y in range(0, GRID_SIZE, 4):
            self.display.set_pixel(32, y, (60, 60, 60))
            self.display.set_pixel(32, y + 1, (60, 60, 60))
        # Paddles
        pl = int(self.paddle_l)
        pr = int(self.paddle_r)
        for dy in range(-5, 6):
            py = pl + dy
            if 0 <= py < GRID_SIZE:
                self.display.set_pixel(2, py, (255, 255, 255))
                self.display.set_pixel(3, py, (255, 255, 255))
            py = pr + dy
            if 0 <= py < GRID_SIZE:
                self.display.set_pixel(60, py, (255, 255, 255))
                self.display.set_pixel(61, py, (255, 255, 255))
        # Ball
        bx, by = int(self.ball_x), int(self.ball_y)
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                px, py = bx + dx, by + dy
                if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                    self.display.set_pixel(px, py, (255, 255, 255))
        # Score as WONDER / CABINET text at top
        hue = (self.time * 0.15) % 1.0
        color = _hue_to_rgb(hue)
        self.display.draw_text_small(_center_x("WONDER"), 1, "WONDER", color)
        color2 = _hue_to_rgb((hue + 0.15) % 1.0)
        self.display.draw_text_small(_center_x("CABINET"), 57, "CABINET", color2)


# =========================================================================
# WonderSega - Sega-style zoom splash screen
# =========================================================================

class WonderSega(Visual):
    name = "WONDER SEGA"
    description = "Sega zoom splash"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        self.display.clear((0, 0, 120))  # blue background
        cycle = 6.0
        t = self.time % cycle

        cx = GRID_SIZE // 2

        if t < 2.5:
            # WONDER zooms in from tiny
            progress = t / 2.5
            scale = _ease_out_bounce(progress)
            # Simulate zoom by varying brightness/position
            alpha = min(1.0, scale)
            if scale > 0.1:
                c = (int(255 * alpha), int(255 * alpha), int(255 * alpha))
                # Offset shrinks to center as scale increases
                offset_y = int(WONDER_Y + (1.0 - scale) * 10)
                self.display.draw_text_small(WONDER_X, offset_y, "WONDER", c)
            # Starburst rays
            if progress > 0.3:
                ray_alpha = min(1.0, (progress - 0.3) / 0.5)
                ray_len = int(30 * ray_alpha)
                for angle_i in range(12):
                    a = angle_i * math.pi / 6
                    for r in range(ray_len):
                        px = int(cx + r * math.cos(a))
                        py = int(WONDER_Y + 2 + r * math.sin(a))
                        if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                            fade = max(0, 1.0 - r / max(1, ray_len))
                            bright = int(80 * fade * ray_alpha)
                            # Blend with blue background
                            self.display.set_pixel(px, py,
                                (bright, bright, 120 + bright // 2))

        elif t < 3.5:
            # Hold WONDER, CABINET slams in from below
            self.display.draw_text_small(WONDER_X, WONDER_Y, "WONDER",
                                         (255, 255, 255))
            slam_t = (t - 2.5) / 1.0
            slam_p = _ease_out_bounce(min(1.0, slam_t))
            cy_pos = int(GRID_SIZE + 8 - slam_p * (GRID_SIZE + 8 - CABINET_Y))
            self.display.draw_text_small(CABINET_X, cy_pos, "CABINET",
                                         (255, 255, 255))
        else:
            # Hold both with pulse
            pulse = 0.8 + 0.2 * math.sin(self.time * 4.0)
            c = (int(255 * pulse), int(255 * pulse), int(255 * pulse))
            self.display.draw_text_small(WONDER_X, WONDER_Y, "WONDER", c)
            self.display.draw_text_small(CABINET_X, CABINET_Y, "CABINET", c)
            # Subtle starburst
            for angle_i in range(12):
                a = angle_i * math.pi / 6 + self.time * 0.5
                for r in range(8, 25):
                    px = int(cx + r * math.cos(a))
                    py = int(32 + r * math.sin(a))
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        fade = max(0, 1.0 - (r - 8) / 17)
                        bright = int(40 * fade * pulse)
                        self.display.set_pixel(px, py,
                            (bright, bright, 120 + bright // 2))


# =========================================================================
# WonderPS1 - PS1-style particle cascade coalescing into title
# =========================================================================

class WonderPS1(Visual):
    name = "WONDER PS1"
    description = "PS1 startup particles"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        # Generate particles with targets on the text
        self.particles = []
        mask = _text_mask()
        targets = []
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if mask[y][x]:
                    targets.append((x, y))
        random.shuffle(targets)
        for tx, ty in targets:
            # Start from random edge
            edge = random.randint(0, 3)
            if edge == 0:
                sx, sy = random.randint(0, 63), 0
            elif edge == 1:
                sx, sy = 63, random.randint(0, 63)
            elif edge == 2:
                sx, sy = random.randint(0, 63), 63
            else:
                sx, sy = 0, random.randint(0, 63)
            delay = random.uniform(0, 2.5)
            hue = random.random()
            self.particles.append({
                'sx': float(sx), 'sy': float(sy),
                'tx': float(tx), 'ty': float(ty),
                'delay': delay, 'hue': hue,
            })

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        self.display.clear(Colors.BLACK)
        t = self.time
        cycle = 8.0
        ct = t % cycle

        for p in self.particles:
            if ct < p['delay']:
                continue
            travel_t = ct - p['delay']
            travel_dur = 2.5
            if travel_t < travel_dur:
                # Swirl towards target
                progress = travel_t / travel_dur
                ease = progress * progress * (3 - 2 * progress)
                # Add spiral motion
                spiral = (1.0 - ease) * 6
                angle = progress * math.pi * 3 + p['hue'] * math.pi * 2
                ox = math.cos(angle) * spiral
                oy = math.sin(angle) * spiral
                px = p['sx'] + (p['tx'] - p['sx']) * ease + ox
                py = p['sy'] + (p['ty'] - p['sy']) * ease + oy
            else:
                px, py = p['tx'], p['ty']

            ix, iy = int(px), int(py)
            if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                color = _hue_to_rgb(p['hue'])
                # Fade to white as it settles
                if travel_t >= travel_dur:
                    white_t = min(1.0, (travel_t - travel_dur) / 1.0)
                    color = (
                        int(color[0] + (255 - color[0]) * white_t),
                        int(color[1] + (255 - color[1]) * white_t),
                        int(color[2] + (255 - color[2]) * white_t),
                    )
                self.display.set_pixel(ix, iy, color)

        # Diamond sparkles
        if ct > 3.0:
            spark_count = min(8, int((ct - 3.0) * 3))
            random.seed(int(ct * 5))
            for _ in range(spark_count):
                sx = random.randint(0, 63)
                sy = random.randint(0, 63)
                bright = random.randint(150, 255)
                self.display.set_pixel(sx, sy, (bright, bright, bright))
            random.seed()


# =========================================================================
# WonderInsertCoin - GAME OVER / INSERT COIN / countdown cycle
# =========================================================================

class WonderInsertCoin(Visual):
    name = "WONDER COIN"
    description = "Insert coin title"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        self.display.clear(Colors.BLACK)
        cycle = 16.0
        t = self.time % cycle

        if t < 4.0:
            # GAME OVER drops in letter by letter
            text = "GAME"
            chars = min(4, int(t / 0.3) + 1)
            gx = _center_x("GAME")
            for i in range(chars):
                drop_t = t - i * 0.3
                if drop_t < 0:
                    continue
                bounce = _ease_out_bounce(min(1.0, drop_t / 0.5))
                y = int(-8 + bounce * (14 + 8))
                ch = text[i]
                self.display.draw_text_small(gx + i * 5, y, ch, (255, 40, 40))

            text2 = "OVER"
            chars2 = max(0, min(4, int((t - 1.5) / 0.3) + 1))
            ox = _center_x("OVER")
            for i in range(chars2):
                drop_t = t - 1.5 - i * 0.3
                if drop_t < 0:
                    continue
                bounce = _ease_out_bounce(min(1.0, drop_t / 0.5))
                y = int(-8 + bounce * (24 + 8))
                ch = text2[i]
                self.display.draw_text_small(ox + i * 5, y, ch, (255, 40, 40))

        elif t < 14.0:
            # Show GAME OVER steady + blinking INSERT COIN + countdown
            self.display.draw_text_small(_center_x("GAME"), 14, "GAME",
                                         (255, 40, 40))
            self.display.draw_text_small(_center_x("OVER"), 24, "OVER",
                                         (255, 40, 40))

            # INSERT COIN blinks
            blink = int(t * 2.5) % 2 == 0
            if blink:
                self.display.draw_text_small(_center_x("INSERT"), 38,
                                             "INSERT", (255, 255, 100))
                self.display.draw_text_small(_center_x("COIN"), 48,
                                             "COIN", (255, 255, 100))

            # Countdown 9->0
            countdown_t = t - 4.0
            num = max(0, 9 - int(countdown_t))
            nx = _center_x(str(num))
            self.display.draw_text_small(nx, 56, str(num), (255, 255, 255))

        else:
            # Title appears
            fade = min(1.0, (t - 14.0) / 0.5)
            c = int(255 * fade)
            hue = (self.time * 0.2) % 1.0
            color = _hue_to_rgb(hue)
            color = (int(color[0] * fade), int(color[1] * fade),
                     int(color[2] * fade))
            self.display.draw_text_small(WONDER_X, WONDER_Y, "WONDER", color)
            color2 = _hue_to_rgb((hue + 0.15) % 1.0)
            color2 = (int(color2[0] * fade), int(color2[1] * fade),
                      int(color2[2] * fade))
            self.display.draw_text_small(CABINET_X, CABINET_Y, "CABINET",
                                         color2)


# =========================================================================
# WonderCreeper - Minecraft Creeper face fades in, explodes, reforms
# =========================================================================

class WonderCreeper(Visual):
    name = "WONDER CREEP"
    description = "Creeper explosion title"
    category = "titles"

    # 8x8 creeper face pattern (1 = dark green feature)
    FACE = [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 0, 0, 1, 1, 0],
        [0, 1, 1, 0, 0, 1, 1, 0],
        [0, 0, 0, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 1, 1, 0, 0],
        [0, 0, 1, 1, 1, 1, 0, 0],
        [0, 0, 1, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
    ]

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.explosion_particles = []
        self._gen_particles()

    def _gen_particles(self):
        self.explosion_particles = []
        # One particle per face pixel
        scale = 5  # each creeper pixel = 5x5 LED pixels
        ox = (GRID_SIZE - 8 * scale) // 2
        oy = (GRID_SIZE - 8 * scale) // 2 - 6
        for fy in range(8):
            for fx in range(8):
                cx = ox + fx * scale + scale // 2
                cy = oy + fy * scale + scale // 2
                is_feature = self.FACE[fy][fx] == 1
                angle = random.uniform(0, math.pi * 2)
                speed = random.uniform(20, 60)
                self.explosion_particles.append({
                    'fx': fx, 'fy': fy,
                    'home_x': cx, 'home_y': cy,
                    'vx': math.cos(angle) * speed,
                    'vy': math.sin(angle) * speed,
                    'is_feature': is_feature,
                })

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        self.display.clear(Colors.BLACK)
        cycle = 8.0
        t = self.time % cycle
        scale = 5
        ox = (GRID_SIZE - 8 * scale) // 2
        oy = (GRID_SIZE - 8 * scale) // 2 - 6

        green_bg = (80, 200, 50)
        green_dark = (30, 80, 15)

        if t < 2.5:
            # Fade in creeper face
            fade = min(1.0, t / 1.5)
            bg = (int(green_bg[0] * fade), int(green_bg[1] * fade),
                  int(green_bg[2] * fade))
            dk = (int(green_dark[0] * fade), int(green_dark[1] * fade),
                  int(green_dark[2] * fade))
            for fy in range(8):
                for fx in range(8):
                    c = dk if self.FACE[fy][fx] else bg
                    for dy in range(scale):
                        for dx in range(scale):
                            px = ox + fx * scale + dx
                            py = oy + fy * scale + dy
                            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                                self.display.set_pixel(px, py, c)

        elif t < 2.8:
            # White flash (hiss)
            bright = int(255 * (1.0 - (t - 2.5) / 0.3))
            for y in range(GRID_SIZE):
                for x in range(0, GRID_SIZE, 2):
                    self.display.set_pixel(x, y, (bright, bright, bright))

        elif t < 5.0:
            # Explosion - particles fly outward
            et = t - 2.8
            for p in self.explosion_particles:
                px = p['home_x'] + p['vx'] * et
                py = p['home_y'] + p['vy'] * et + 20 * et * et  # gravity
                ix, iy = int(px), int(py)
                if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                    fade = max(0, 1.0 - et / 2.2)
                    c = green_dark if p['is_feature'] else green_bg
                    c = (int(c[0] * fade), int(c[1] * fade), int(c[2] * fade))
                    self.display.set_pixel(ix, iy, c)

        else:
            # Reform into title text
            reform_t = min(1.0, (t - 5.0) / 1.5)
            ease = reform_t * reform_t * (3 - 2 * reform_t)
            hue = (self.time * 0.15) % 1.0
            color = _hue_to_rgb(hue)
            c = (int(color[0] * ease), int(color[1] * ease),
                 int(color[2] * ease))
            color2 = _hue_to_rgb((hue + 0.15) % 1.0)
            c2 = (int(color2[0] * ease), int(color2[1] * ease),
                  int(color2[2] * ease))
            self.display.draw_text_small(WONDER_X, WONDER_Y, "WONDER", c)
            self.display.draw_text_small(CABINET_X, CABINET_Y, "CABINET", c2)


# =========================================================================
# WonderNyanCat - Nyan Cat with rainbow trail and scrolling banner
# =========================================================================

class WonderNyanCat(Visual):
    name = "WONDER NYAN"
    description = "Nyan Cat rainbow title"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.stars = []
        for _ in range(20):
            self.stars.append({
                'x': random.randint(0, 63),
                'y': random.randint(0, 63),
                'phase': random.random() * math.pi * 2,
            })

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        self.display.clear((10, 10, 40))  # dark blue sky
        t = self.time

        # Twinkling stars
        for star in self.stars:
            bright = int(80 + 80 * math.sin(t * 3 + star['phase']))
            self.display.set_pixel(star['x'], star['y'],
                                   (bright, bright, bright))

        # Nyan cat position - bounces vertically while moving right
        cat_x = int((t * 20) % (GRID_SIZE + 40)) - 20
        cat_y = 20 + int(4 * math.sin(t * 5))

        # Rainbow trail (6 colors, extends left from cat)
        rainbow = [
            (255, 0, 0), (255, 165, 0), (255, 255, 0),
            (0, 255, 0), (0, 100, 255), (128, 0, 255),
        ]
        trail_len = 30
        for i, color in enumerate(rainbow):
            ry = cat_y - 1 + i
            if 0 <= ry < GRID_SIZE:
                for dx in range(trail_len):
                    tx = cat_x - 4 - dx
                    if 0 <= tx < GRID_SIZE:
                        fade = max(0.2, 1.0 - dx / trail_len)
                        c = (int(color[0] * fade), int(color[1] * fade),
                             int(color[2] * fade))
                        self.display.set_pixel(tx, ry, c)

        # Cat body (poptart - tan rectangle with pink face)
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                px, py = cat_x + dx, cat_y + dy
                if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                    if abs(dx) <= 2 and abs(dy) <= 2:
                        self.display.set_pixel(px, py, (255, 180, 120))  # poptart
                    else:
                        self.display.set_pixel(px, py, (120, 120, 120))  # edges
        # Cat face (gray with eyes)
        for dx, dy in [(1, -1), (3, -1)]:  # eyes
            px, py = cat_x + dx - 1, cat_y + dy
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                self.display.set_pixel(px, py, (40, 40, 40))

        # Scrolling WONDER CABINET banner at bottom
        scroll = int(t * 15) % (GRID_SIZE + 80)
        banner_x = GRID_SIZE - scroll
        self.display.draw_text_small(banner_x, 56, "WONDER CABINET",
                                     (255, 255, 255))


# =========================================================================
# WonderC64 - Commodore 64 boot screen with typed text
# =========================================================================

class WonderC64(Visual):
    name = "WONDER C64"
    description = "C64 boot screen"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        # C64 colors: light blue bg, dark blue border
        border = (50, 50, 180)
        bg = (100, 100, 255)
        text_color = (100, 100, 255)
        cursor_color = (100, 100, 255)

        # Fill border
        self.display.clear(border)
        # Fill inner area
        for y in range(4, 60):
            for x in range(4, 60):
                self.display.set_pixel(x, y, bg)

        cycle = 12.0
        t = self.time % cycle

        # Text lines typed character by character
        lines = [
            (0.0, "****", 5, 6),
            (0.8, "WONDER", 5, 14),
            (1.6, "64", 5, 22),
            (2.2, "****", 5, 30),
            (3.5, "READY.", 5, 42),
        ]

        white = (255, 255, 255)

        for start_t, text, tx, ty in lines:
            if t < start_t:
                continue
            chars = min(len(text), int((t - start_t) * 12) + 1)
            self.display.draw_text_small(tx, ty, text[:chars], white)

        # After READY, show cursor blinking
        if t > 4.0:
            blink = int(t * 2) % 2 == 0
            cursor_x = 5
            cursor_y = 50
            if t > 5.5:
                # Type "RUN" then show title
                run_chars = min(3, int((t - 5.5) * 8) + 1)
                self.display.draw_text_small(5, 50, "RUN"[:run_chars], white)
                cursor_x = 5 + run_chars * 5
            if blink and t < 7.0:
                for dy in range(5):
                    for dx in range(4):
                        px, py = cursor_x + dx, cursor_y + dy
                        if 0 <= px < 60 and 0 <= py < 60:
                            self.display.set_pixel(px, py, white)

        # After typing RUN, show title
        if t > 7.0:
            fade = min(1.0, (t - 7.0) / 0.5)
            c = (int(255 * fade), int(255 * fade), int(255 * fade))
            # Clear inner area and show title
            for y in range(4, 60):
                for x in range(4, 60):
                    self.display.set_pixel(x, y, bg)
            self.display.draw_text_small(WONDER_X, WONDER_Y, "WONDER", c)
            self.display.draw_text_small(CABINET_X, CABINET_Y, "CABINET", c)


# =========================================================================
# WonderGameBoy - Game Boy startup with scrolling bar
# =========================================================================

class WonderGameBoy(Visual):
    name = "WONDER GBOY"
    description = "Game Boy startup"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        # Game Boy olive-green palette
        lightest = (155, 188, 15)
        light = (139, 172, 15)
        dark = (48, 98, 48)
        darkest = (15, 56, 15)

        self.display.clear(lightest)
        cycle = 6.0
        t = self.time % cycle

        if t < 2.0:
            # Bar scrolls down from top to center
            bar_y = int(-8 + (t / 2.0) * (32 + 8))
            bar_h = 8

            # Draw the bar (dark rectangle)
            for y in range(bar_y, bar_y + bar_h):
                if 0 <= y < GRID_SIZE:
                    for x in range(GRID_SIZE):
                        self.display.set_pixel(x, y, darkest)

            # "WONDER" text inside bar
            text_y = bar_y + 1
            if 0 <= text_y < GRID_SIZE - 4:
                self.display.draw_text_small(WONDER_X, text_y, "WONDER",
                                             lightest)

            # Ding sound visual - small ring at center after bar arrives
            if t > 1.5:
                ring_r = int((t - 1.5) * 30)
                for a in range(0, 360, 10):
                    rad = math.radians(a)
                    px = int(32 + ring_r * math.cos(rad))
                    py = int(32 + ring_r * math.sin(rad))
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        self.display.set_pixel(px, py, dark)

        elif t < 3.5:
            # Bar settled at center, dissolve effect
            dissolve = (t - 2.0) / 1.5
            # Bar fading
            bar_y = 24
            bar_h = 8
            for y in range(bar_y, bar_y + bar_h):
                for x in range(GRID_SIZE):
                    if random.random() > dissolve:
                        self.display.set_pixel(x, y, darkest)
            # Text emerging
            if dissolve > 0.3:
                alpha = min(1.0, (dissolve - 0.3) / 0.5)
                c = (int(darkest[0] + (dark[0] - darkest[0]) * alpha),
                     int(darkest[1] + (dark[1] - darkest[1]) * alpha),
                     int(darkest[2] + (dark[2] - darkest[2]) * alpha))
                self.display.draw_text_small(WONDER_X, WONDER_Y, "WONDER", c)
                self.display.draw_text_small(CABINET_X, CABINET_Y, "CABINET", c)
        else:
            # Title shown in GB palette
            self.display.draw_text_small(WONDER_X, WONDER_Y, "WONDER", darkest)
            self.display.draw_text_small(CABINET_X, CABINET_Y, "CABINET", dark)


# =========================================================================
# WonderDOS - MS-DOS boot sequence
# =========================================================================

class WonderDOS(Visual):
    name = "WONDER DOS"
    description = "DOS boot sequence"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        self.display.clear(Colors.BLACK)
        cycle = 12.0
        t = self.time % cycle

        gray = (170, 170, 170)
        white = (255, 255, 255)

        if t < 1.5:
            # POST text scrolling
            lines = ["BIOS 1.0", "RAM  640K", "OK"]
            for i, line in enumerate(lines):
                show_t = t - i * 0.4
                if show_t > 0:
                    chars = min(len(line), int(show_t * 20) + 1)
                    self.display.draw_text_small(2, 2 + i * 8, line[:chars],
                                                 gray)

        elif t < 3.0:
            # Memory counter
            self.display.draw_text_small(2, 2, "BIOS 1.0", gray)
            self.display.draw_text_small(2, 10, "RAM  640K", gray)
            self.display.draw_text_small(2, 18, "OK", gray)
            mem_val = min(640, int((t - 1.5) * 450))
            self.display.draw_text_small(2, 30, str(mem_val) + "K", white)

        elif t < 5.0:
            # C:\> prompt
            self.display.draw_text_small(2, 2, "C:\\>", gray)
            # Type WONDER.EXE
            type_t = t - 3.5
            if type_t > 0:
                text = "WONDER"
                chars = min(len(text), int(type_t * 8) + 1)
                self.display.draw_text_small(2, 10, text[:chars], white)
            # Blinking cursor
            cursor_t = t - 3.0
            if cursor_t > 0:
                blink = int(t * 2) % 2 == 0
                if blink:
                    if type_t > 0:
                        cx = 2 + min(len("WONDER"), int(type_t * 8) + 1) * 5
                    else:
                        cx = 22
                    for dy in range(5):
                        if 0 <= cx < GRID_SIZE:
                            self.display.set_pixel(cx, 10 + dy, white)

        else:
            # Title appears
            fade = min(1.0, (t - 5.0) / 0.5)
            hue = (self.time * 0.15) % 1.0
            color = _hue_to_rgb(hue)
            c = (int(color[0] * fade), int(color[1] * fade),
                 int(color[2] * fade))
            self.display.draw_text_small(WONDER_X, WONDER_Y, "WONDER", c)
            color2 = _hue_to_rgb((hue + 0.15) % 1.0)
            c2 = (int(color2[0] * fade), int(color2[1] * fade),
                  int(color2[2] * fade))
            self.display.draw_text_small(CABINET_X, CABINET_Y, "CABINET", c2)


# =========================================================================
# WonderBSOD - Blue Screen of Death with restart
# =========================================================================

class WonderBSOD(Visual):
    name = "WONDER BSOD"
    description = "Blue screen of death"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        cycle = 12.0
        t = self.time % cycle

        if t < 8.0:
            # Blue screen
            self.display.clear((0, 0, 170))
            white = (255, 255, 255)

            # Sad face :(
            if t > 0.3:
                self.display.draw_text_small(_center_x(":("), 4, ":(", white)

            # Error text typed character by character
            if t > 1.0:
                line1 = "WONDER"
                chars1 = min(len(line1), int((t - 1.0) * 10) + 1)
                self.display.draw_text_small(2, 16, line1[:chars1], white)

            if t > 2.0:
                line2 = "RAN"
                chars2 = min(len(line2), int((t - 2.0) * 10) + 1)
                self.display.draw_text_small(2, 24, line2[:chars2], white)

            if t > 2.5:
                line3 = "INTO A"
                chars3 = min(len(line3), int((t - 2.5) * 10) + 1)
                self.display.draw_text_small(2, 32, line3[:chars3], white)

            if t > 3.2:
                line4 = "PROBLEM"
                chars4 = min(len(line4), int((t - 3.2) * 10) + 1)
                self.display.draw_text_small(2, 40, line4[:chars4], white)

            # Percentage counter
            if t > 4.0:
                pct = min(100, int((t - 4.0) * 30))
                pct_str = str(pct) + "%"
                self.display.draw_text_small(_center_x(pct_str), 52,
                                             pct_str, white)

        elif t < 8.5:
            # Black (restarting)
            self.display.clear(Colors.BLACK)

        elif t < 9.5:
            # Brief spinning dots (restart)
            self.display.clear(Colors.BLACK)
            dots = 4
            spin_t = t - 8.5
            for i in range(dots):
                angle = spin_t * 6 + i * math.pi * 2 / dots
                dx = int(32 + 6 * math.cos(angle))
                dy = int(32 + 6 * math.sin(angle))
                if 0 <= dx < GRID_SIZE and 0 <= dy < GRID_SIZE:
                    bright = 150 + int(105 * (i / dots))
                    self.display.set_pixel(dx, dy,
                                           (bright, bright, bright))

        else:
            # Title appears (system recovered)
            self.display.clear(Colors.BLACK)
            fade = min(1.0, (t - 9.5) / 0.5)
            hue = (self.time * 0.15) % 1.0
            color = _hue_to_rgb(hue)
            c = (int(color[0] * fade), int(color[1] * fade),
                 int(color[2] * fade))
            self.display.draw_text_small(WONDER_X, WONDER_Y, "WONDER", c)
            color2 = _hue_to_rgb((hue + 0.15) % 1.0)
            c2 = (int(color2[0] * fade), int(color2[1] * fade),
                  int(color2[2] * fade))
            self.display.draw_text_small(CABINET_X, CABINET_Y, "CABINET", c2)


# =========================================================================
# WonderLoading - Comedic loading bar that hangs at 99%
# =========================================================================

class WonderLoading(Visual):
    name = "WONDER LOAD"
    description = "Loading bar comedy"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        self.display.clear(Colors.BLACK)
        cycle = 12.0
        t = self.time % cycle

        white = (255, 255, 255)
        gray = (100, 100, 100)
        green = (0, 200, 0)
        bar_x = 6
        bar_w = 52
        bar_y = 30
        bar_h = 6

        if t < 10.0:
            # LOADING... text with animated dots
            dots = "." * (int(t * 2) % 4)
            self.display.draw_text_small(_center_x("LOADING"), 18,
                                         "LOADING", white)
            if dots:
                self.display.draw_text_small(
                    _center_x("LOADING") + 7 * 5, 18, dots, white)

            # Progress bar outline
            for x in range(bar_x - 1, bar_x + bar_w + 1):
                self.display.set_pixel(x, bar_y - 1, gray)
                self.display.set_pixel(x, bar_y + bar_h, gray)
            for y in range(bar_y - 1, bar_y + bar_h + 1):
                self.display.set_pixel(bar_x - 1, y, gray)
                self.display.set_pixel(bar_x + bar_w, y, gray)

            # Progress fills with stutters
            if t < 3.0:
                # Quick progress to ~60%
                pct = t / 3.0 * 0.6
            elif t < 4.0:
                # Stutter
                pct = 0.6 + (t - 3.0) * 0.05
            elif t < 5.5:
                # Resume to ~90%
                pct = 0.65 + (t - 4.0) / 1.5 * 0.25
            elif t < 6.0:
                # Quick to 95%
                pct = 0.90 + (t - 5.5) * 0.1
            elif t < 8.5:
                # Hang at 99% - comedically slow
                pct = 0.95 + (t - 6.0) / 2.5 * 0.04
            else:
                # Snap to 100%
                pct = 1.0

            fill_w = int(bar_w * min(1.0, pct))
            for y in range(bar_y, bar_y + bar_h):
                for x in range(bar_x, bar_x + fill_w):
                    self.display.set_pixel(x, y, green)

            # Percentage text
            pct_val = int(pct * 100)
            pct_str = str(min(100, pct_val)) + "%"
            self.display.draw_text_small(_center_x(pct_str), 40,
                                         pct_str, white)

        else:
            # Fanfare - title appears with flash
            flash_t = t - 10.0
            if flash_t < 0.3:
                bright = int(255 * (1.0 - flash_t / 0.3))
                for y in range(GRID_SIZE):
                    for x in range(0, GRID_SIZE, 3):
                        self.display.set_pixel(x, y,
                                               (bright, bright, bright))
            hue = (self.time * 0.2) % 1.0
            color = _hue_to_rgb(hue)
            self.display.draw_text_small(WONDER_X, WONDER_Y, "WONDER", color)
            color2 = _hue_to_rgb((hue + 0.15) % 1.0)
            self.display.draw_text_small(CABINET_X, CABINET_Y, "CABINET",
                                         color2)


# =========================================================================
# WonderColorBars - SMPTE color bars with "PLEASE STAND BY"
# =========================================================================

class WonderColorBars(Visual):
    name = "WONDER BARS"
    description = "SMPTE color bars title"
    category = "titles"

    BARS = [
        (191, 191, 191),  # gray
        (191, 191, 0),    # yellow
        (0, 191, 191),    # cyan
        (0, 191, 0),      # green
        (191, 0, 191),    # magenta
        (191, 0, 0),      # red
        (0, 0, 191),      # blue
    ]

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        self.display.clear(Colors.BLACK)
        cycle = 10.0
        t = self.time % cycle

        bar_w = GRID_SIZE // 7
        remainder = GRID_SIZE - bar_w * 7

        if t < 3.5:
            # Bars appear one stripe at a time
            bars_shown = min(7, int(t / 0.5) + 1)
            x = 0
            for i in range(bars_shown):
                w = bar_w + (1 if i < remainder else 0)
                for dy in range(GRID_SIZE):
                    for dx in range(w):
                        if x + dx < GRID_SIZE:
                            self.display.set_pixel(x + dx, dy, self.BARS[i])
                x += w

        elif t < 7.5:
            # All bars shown + "PLEASE STAND BY" overlay
            x = 0
            for i in range(7):
                w = bar_w + (1 if i < remainder else 0)
                for dy in range(GRID_SIZE):
                    for dx in range(w):
                        if x + dx < GRID_SIZE:
                            self.display.set_pixel(x + dx, dy, self.BARS[i])
                x += w

            # "PLEASE STAND BY" text
            blink = int(t * 1.5) % 2 == 0
            if blink:
                # Dark background for text
                for y in range(WONDER_Y - 2, CABINET_Y + 7):
                    for bx in range(GRID_SIZE):
                        if 0 <= y < GRID_SIZE:
                            # Darken existing pixel
                            self.display.set_pixel(bx, y, (20, 20, 20))
                self.display.draw_text_small(_center_x("PLEASE"), WONDER_Y,
                                             "PLEASE", (255, 255, 255))
                self.display.draw_text_small(_center_x("STANDBY"), CABINET_Y,
                                             "STANDBY", (255, 255, 255))

            # Occasional static bursts
            if int(t * 3) % 5 == 0:
                for _ in range(30):
                    sx = random.randint(0, 63)
                    sy = random.randint(0, 63)
                    gray = random.randint(100, 255)
                    self.display.set_pixel(sx, sy, (gray, gray, gray))

        else:
            # Dissolve to title
            dissolve = (t - 7.5) / 2.0
            # Bars fading
            x = 0
            for i in range(7):
                w = bar_w + (1 if i < remainder else 0)
                for dy in range(GRID_SIZE):
                    for dx in range(w):
                        if x + dx < GRID_SIZE and random.random() > dissolve:
                            c = self.BARS[i]
                            fade = 1.0 - dissolve
                            c = (int(c[0] * fade), int(c[1] * fade),
                                 int(c[2] * fade))
                            self.display.set_pixel(x + dx, dy, c)
                x += w

            # Title fading in
            if dissolve > 0.3:
                alpha = min(1.0, (dissolve - 0.3) / 0.5)
                c = (int(255 * alpha), int(255 * alpha), int(255 * alpha))
                self.display.draw_text_small(WONDER_X, WONDER_Y, "WONDER", c)
                self.display.draw_text_small(CABINET_X, CABINET_Y,
                                             "CABINET", c)


# =========================================================================
# WonderVHS - VHS tracking effect revealing title
# =========================================================================

class WonderVHS(Visual):
    name = "WONDER VHS"
    description = "VHS tracking title"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        self.display.clear(Colors.BLACK)
        cycle = 10.0
        t = self.time % cycle

        white = (255, 255, 255)
        blue = (50, 50, 220)

        if t < 5.0:
            # Rolling horizontal static bands gradually clearing
            clarity = t / 5.0  # 0 to 1
            noise = 1.0 - clarity

            # Static bands that scroll
            for y in range(GRID_SIZE):
                # Rolling band offset
                band_phase = (y * 0.3 + t * 15) % 20
                in_band = band_phase < (8 * noise)

                for x in range(0, GRID_SIZE, 1 + int(clarity * 2)):
                    if in_band:
                        # Static noise in band
                        gray = random.randint(20, 180)
                        self.display.set_pixel(x, y, (gray, gray, gray))
                    elif random.random() < noise * 0.3:
                        # Sparse noise outside bands
                        gray = random.randint(0, 60)
                        self.display.set_pixel(x, y, (gray, gray, gray))

            # Title showing through where static has cleared
            if clarity > 0.3:
                alpha = (clarity - 0.3) / 0.7
                # Horizontal jitter decreasing
                jitter = int((1.0 - clarity) * 6 * math.sin(t * 20))
                c = (int(255 * alpha), int(255 * alpha), int(255 * alpha))
                self.display.draw_text_small(WONDER_X + jitter, WONDER_Y,
                                             "WONDER", c)
                self.display.draw_text_small(CABINET_X - jitter, CABINET_Y,
                                             "CABINET", c)

        elif t < 7.0:
            # Clear title with VHS artifacts
            self.display.draw_text_small(WONDER_X, WONDER_Y, "WONDER", white)
            self.display.draw_text_small(CABINET_X, CABINET_Y, "CABINET",
                                         white)
            # VHS timestamp in corner
            secs = int(self.time) % 60
            mins = int(self.time) // 60
            ts = "{:01d}:{:02d}".format(mins % 10, secs)
            self.display.draw_text_small(38, 2, ts, (200, 200, 200))

        elif t < 8.0:
            # "BE KIND REWIND" flash
            self.display.clear(blue)
            blink = int(t * 4) % 2 == 0
            if blink:
                self.display.draw_text_small(_center_x("REWIND"), 28,
                                             "REWIND", white)
        else:
            # Back to title
            self.display.draw_text_small(WONDER_X, WONDER_Y, "WONDER", white)
            self.display.draw_text_small(CABINET_X, CABINET_Y, "CABINET",
                                         white)
            # Timestamp
            secs = int(self.time) % 60
            mins = int(self.time) // 60
            ts = "{:01d}:{:02d}".format(mins % 10, secs)
            self.display.draw_text_small(38, 2, ts, (200, 200, 200))


# =========================================================================
# WonderBoing - Amiga Boing Ball bouncing with title
# =========================================================================

class WonderBoing(Visual):
    name = "WONDER BOING"
    description = "Amiga Boing Ball"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.ball_x = 32.0
        self.ball_y = 15.0
        self.ball_vx = 18.0
        self.ball_vy = 0.0

    def update(self, dt: float):
        self.time += dt
        # Gravity
        self.ball_vy += 60.0 * dt
        self.ball_x += self.ball_vx * dt
        self.ball_y += self.ball_vy * dt
        # Floor bounce (floor at y=42)
        if self.ball_y > 42:
            self.ball_y = 42
            self.ball_vy = -abs(self.ball_vy) * 0.9
        # Wall bounce
        if self.ball_x < 8 or self.ball_x > 56:
            self.ball_vx = -self.ball_vx
            self.ball_x = max(8, min(56, self.ball_x))

    def draw(self):
        self.display.clear((170, 170, 200))  # light gray-blue bg

        # Grid floor
        for y in range(46, GRID_SIZE):
            for x in range(0, GRID_SIZE, 4):
                if (x // 4 + y // 4) % 2 == 0:
                    self.display.set_pixel(x, y, (140, 140, 170))
                    if x + 1 < GRID_SIZE:
                        self.display.set_pixel(x + 1, y, (140, 140, 170))

        # Shadow on floor
        shadow_x = int(self.ball_x)
        shadow_scale = max(0.3, 1.0 - (42 - self.ball_y) / 40.0)
        shadow_w = int(8 * shadow_scale)
        for dx in range(-shadow_w, shadow_w + 1):
            px = shadow_x + dx
            if 0 <= px < GRID_SIZE:
                alpha = max(0, 1.0 - abs(dx) / max(1, shadow_w))
                gray = int(120 * alpha)
                self.display.set_pixel(px, 45, (gray, gray, gray + 20))

        # Boing ball - checkered red/white sphere
        bx, by = int(self.ball_x), int(self.ball_y)
        radius = 7
        rot = self.time * 3.0  # rotation angle
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                dist = math.sqrt(dx * dx + dy * dy)
                if dist <= radius:
                    px, py = bx + dx, by + dy
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        # Checker pattern with rotation
                        u = math.atan2(dy, dx) + rot
                        v = dist / radius
                        check = (int(u * 3 / math.pi) + int(v * 4)) % 2
                        if check:
                            # Shade by distance from center for 3D look
                            shade = max(0.5, 1.0 - dist / radius * 0.5)
                            c = (int(255 * shade), int(40 * shade),
                                 int(40 * shade))
                        else:
                            shade = max(0.6, 1.0 - dist / radius * 0.4)
                            c = (int(255 * shade), int(255 * shade),
                                 int(255 * shade))
                        self.display.set_pixel(px, py, c)

        # Title text below
        self.display.draw_text_small(WONDER_X, 50, "WONDER", (40, 40, 80))
        self.display.draw_text_small(CABINET_X, 57, "CABINET", (40, 40, 80))


# =========================================================================
# WonderNES - Nintendo-style red curtain reveal
# =========================================================================

class WonderNES(Visual):
    name = "WONDER NES"
    description = "NES startup curtain"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        self.display.clear(Colors.BLACK)
        cycle = 8.0
        t = self.time % cycle

        if t < 3.0:
            # Red curtain covers screen, then splits open
            open_frac = max(0.0, (t - 1.0) / 2.0)
            open_px = int(open_frac * 33)
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    # Left curtain
                    if x < 32 - open_px:
                        wave = int(2 * math.sin(y * 0.3 + self.time * 2))
                        shade = max(0.4, 1.0 - abs(x - 16 + wave) / 32)
                        self.display.set_pixel(x, y,
                            (int(200 * shade), int(20 * shade), int(20 * shade)))
                    # Right curtain
                    elif x >= 32 + open_px:
                        wave = int(2 * math.sin(y * 0.3 + self.time * 2 + 1))
                        shade = max(0.4, 1.0 - abs(x - 48 + wave) / 32)
                        self.display.set_pixel(x, y,
                            (int(200 * shade), int(20 * shade), int(20 * shade)))
        elif t < 4.5:
            # Blank pause
            pass
        elif t < 6.0:
            # NES-style blink: red rectangle with white text
            blink = int(t * 6) % 2
            if blink:
                self.display.draw_rect(8, 20, 48, 24, (180, 0, 0), filled=True)
                self.display.draw_rect(8, 20, 48, 24, (255, 60, 60), filled=False)
                self.display.draw_text_small(WONDER_X, WONDER_Y, "WONDER", Colors.WHITE)
                self.display.draw_text_small(CABINET_X, CABINET_Y, "CABINET", Colors.WHITE)
        else:
            # Steady title with NES palette
            self.display.draw_rect(8, 20, 48, 24, (180, 0, 0), filled=True)
            self.display.draw_rect(8, 20, 48, 24, (255, 60, 60), filled=False)
            pulse = 0.85 + 0.15 * math.sin(t * 4)
            c = (int(255 * pulse), int(255 * pulse), int(255 * pulse))
            self.display.draw_text_small(WONDER_X, WONDER_Y, "WONDER", c)
            self.display.draw_text_small(CABINET_X, CABINET_Y, "CABINET", c)


# =========================================================================
# WonderN64 - Spinning N logo
# =========================================================================

class WonderN64(Visual):
    name = "WONDER N64"
    description = "N64 spinning logo"
    category = "titles"

    # 11x13 "W" bitmap (wide enough to read at low res)
    W_SHAPE = [
        "11000000011",
        "11000000011",
        "11000000011",
        "11000000011",
        "01100000110",
        "01100000110",
        "01100110110",
        "01100110110",
        "00101101100",
        "00101101100",
        "00101101100",
        "00011011000",
        "00011011000",
    ]
    # 11x13 "C" bitmap (same dimensions as W)
    C_SHAPE = [
        "00011111100",
        "00111111110",
        "01100000011",
        "11000000000",
        "11000000000",
        "11000000000",
        "11000000000",
        "11000000000",
        "11000000000",
        "11000000000",
        "01100000011",
        "00111111110",
        "00011111100",
    ]

    N64_COLORS = [(0, 180, 0), (220, 30, 30), (30, 30, 220), (230, 190, 0)]

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

    def update(self, dt: float):
        self.time += dt

    def _draw_letter(self, shape, cx, cy, angle, color_idx):
        """Draw a bitmap letter with fake 3D Y-axis rotation."""
        h = len(shape)
        w = len(shape[0])
        cos_a = math.cos(angle)
        squeeze = abs(cos_a)
        # Skip when edge-on (too thin to see)
        if squeeze < 0.08:
            return
        # Pick color based on which face is showing
        face = int(((angle % (math.pi * 2)) / (math.pi * 2)) * 4) % 4
        c = self.N64_COLORS[(color_idx + face) % 4]
        # Slightly darken when angled away
        shade = 0.5 + 0.5 * squeeze
        c = (int(c[0] * shade), int(c[1] * shade), int(c[2] * shade))

        for row in range(h):
            for col in range(w):
                if shape[row][col] == '1':
                    dx = (col - w / 2.0) * squeeze
                    px = cx + int(round(dx))
                    py = cy + row - h // 2
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        self.display.set_pixel(px, py, c)

    def draw(self):
        self.display.clear(Colors.BLACK)
        cycle = 8.0
        t = self.time % cycle
        # Shared center point, like the real N64 logo
        cx, cy = 32, 22
        angle = t * 2.0

        # W and C share the same center, offset by 90 degrees
        # So when W is face-on, C is edge-on (invisible), and vice versa
        self._draw_letter(self.W_SHAPE, cx, cy, angle, 0)
        self._draw_letter(self.C_SHAPE, cx, cy, angle + math.pi / 2, 2)

        # Title text fades in
        if t > 3.0:
            fade = min(1.0, (t - 3.0) / 1.5)
            c1 = (int(100 * fade), int(200 * fade), int(100 * fade))
            c2 = (int(200 * fade), int(100 * fade), int(100 * fade))
            self.display.draw_text_small(WONDER_X, 42, "WONDER", c1)
            self.display.draw_text_small(CABINET_X, 50, "CABINET", c2)


# =========================================================================
# WonderAtari - Rainbow-stripe Fuji logo
# =========================================================================

class WonderAtari(Visual):
    name = "WONDER ATARI"
    description = "Atari rainbow logo"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        self.display.clear(Colors.BLACK)
        t = self.time

        # Atari Fuji: three vertical prongs with a peak
        cx = 32
        peak_y = 8
        base_y = 38
        prong_w = 3
        gap = 5

        # Rainbow stripe colors cycling
        stripes = [
            (255, 50, 50), (255, 140, 0), (255, 255, 50),
            (50, 255, 50), (50, 150, 255), (150, 50, 255),
        ]

        # Fade in
        fade = min(1.0, t / 2.0)

        # Draw the three prongs
        for prong in range(-1, 2):
            px = cx + prong * gap
            for y in range(peak_y, base_y):
                # Taper at top
                frac = (y - peak_y) / max(1, base_y - peak_y)
                w = max(1, int(prong_w * min(1.0, frac * 3)))
                if prong == 0 and y < peak_y + 6:
                    w = max(1, int(prong_w * frac * 2))
                for dx in range(-w, w + 1):
                    stripe_idx = int((y + t * 8) / 5) % len(stripes)
                    c = stripes[stripe_idx]
                    c = (int(c[0] * fade), int(c[1] * fade), int(c[2] * fade))
                    sx = px + dx
                    if 0 <= sx < GRID_SIZE and 0 <= y < GRID_SIZE:
                        self.display.set_pixel(sx, y, c)

        # Title text
        if t > 1.5:
            text_fade = min(1.0, (t - 1.5) / 1.0)
            c = (int(255 * text_fade), int(255 * text_fade), int(255 * text_fade))
            self.display.draw_text_small(WONDER_X, 44, "WONDER", c)
            self.display.draw_text_small(CABINET_X, 52, "CABINET", c)


# =========================================================================
# WonderBreakout - Bricks crumble to reveal title
# =========================================================================

class WonderBreakout(Visual):
    name = "WONDER BREAK"
    description = "Breakout bricks title"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.title_time = 0.0
        # Build brick grid — 3 rows for faster clearing
        self.bricks = []
        colors = [(255, 50, 50), (255, 200, 50), (50, 200, 255)]
        for row in range(3):
            for col in range(8):
                self.bricks.append({
                    'x': col * 8, 'y': 4 + row * 6,
                    'w': 7, 'h': 5,
                    'color': colors[row],
                    'alive': True,
                    'break_time': None,
                })
        # Ball
        self.ball_x = 32.0
        self.ball_y = 40.0
        self.ball_vx = 45.0
        self.ball_vy = -55.0
        # Paddle
        self.paddle_x = 28.0

    def _aim_at_bricks(self):
        """Aim ball towards a column that still has bricks."""
        alive_bricks = [b for b in self.bricks if b['alive']]
        if alive_bricks:
            target = random.choice(alive_bricks)
            target_x = target['x'] + target['w'] // 2
            self.ball_vx = (target_x - self.ball_x) * 4
            self.ball_vx = max(-60, min(60, self.ball_vx))

    def update(self, dt: float):
        self.time += dt
        alive = sum(1 for b in self.bricks if b['alive'])
        if alive == 0:
            self.title_time += dt
            if self.title_time > 3.0:
                self.reset()
            return
        # After 10s, clear all remaining stragglers
        if self.time > 10.0:
            for b in self.bricks:
                if b['alive']:
                    b['alive'] = False
                    b['break_time'] = self.time
            return
        # Sub-step for collision reliability
        steps = 4
        sub_dt = dt / steps
        for _ in range(steps):
            self.ball_x += self.ball_vx * sub_dt
            self.ball_y += self.ball_vy * sub_dt
            # Wall bounces
            if self.ball_x < 1:
                self.ball_x = 1
                self.ball_vx = abs(self.ball_vx)
            elif self.ball_x > 62:
                self.ball_x = 62
                self.ball_vx = -abs(self.ball_vx)
            if self.ball_y < 1:
                self.ball_y = 1
                self.ball_vy = abs(self.ball_vy)
            # Paddle bounce — aim towards remaining bricks
            if self.ball_y > 48 and self.ball_vy > 0:
                self.ball_y = 48
                self.ball_vy = -abs(self.ball_vy)
                self._aim_at_bricks()
            # Brick collisions — ball plows through, no bounce
            bx, by = int(self.ball_x), int(self.ball_y)
            for brick in self.bricks:
                if not brick['alive']:
                    continue
                cx = brick['x'] + brick['w'] // 2
                cy = brick['y'] + brick['h'] // 2
                if abs(bx - cx) < 7 and abs(by - cy) < 5:
                    brick['alive'] = False
                    brick['break_time'] = self.time
        # Auto-aim paddle
        self.paddle_x += (self.ball_x - self.paddle_x - 6) * 5 * dt

    def draw(self):
        self.display.clear(Colors.BLACK)
        for brick in self.bricks:
            if brick['alive']:
                self.display.draw_rect(brick['x'], brick['y'],
                                       brick['w'], brick['h'], brick['color'])
            elif brick['break_time']:
                elapsed = self.time - brick['break_time']
                if elapsed < 0.8:
                    for i in range(4):
                        px = brick['x'] + brick['w'] // 2 + int(
                            math.cos(i * 1.5) * elapsed * 15)
                        py = brick['y'] + int(elapsed * 20 + math.sin(i * 2) * 5)
                        if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                            fade = max(0, 1.0 - elapsed / 0.8)
                            c = brick['color']
                            c = (int(c[0] * fade), int(c[1] * fade),
                                 int(c[2] * fade))
                            self.display.set_pixel(px, py, c)
        # Ball (3px)
        bx, by = int(self.ball_x), int(self.ball_y)
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if dx * dx + dy * dy <= 1:
                    px, py = bx + dx, by + dy
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        self.display.set_pixel(px, py, Colors.WHITE)
        # Paddle
        px = int(self.paddle_x)
        self.display.draw_rect(max(0, px), 50, 12, 2, (180, 180, 255))
        # Title fades in as bricks clear
        alive = sum(1 for b in self.bricks if b['alive'])
        total = len(self.bricks)
        if alive < total:
            fade = 1.0 - alive / total
            hue = (self.time * 0.2) % 1.0
            c = _hue_to_rgb(hue)
            c = (int(c[0] * fade), int(c[1] * fade), int(c[2] * fade))
            self.display.draw_text_small(WONDER_X, WONDER_Y, "WONDER", c)
            c2 = _hue_to_rgb((hue + 0.15) % 1.0)
            c2 = (int(c2[0] * fade), int(c2[1] * fade), int(c2[2] * fade))
            self.display.draw_text_small(CABINET_X, CABINET_Y, "CABINET", c2)


# =========================================================================
# WonderSnake - Snake traces out the title letters
# =========================================================================

class WonderSnake(Visual):
    name = "WONDER SNAKE"
    description = "Snake traces title"
    category = "titles"

    # Pixel positions for WONDER CABINET text (simplified path)
    def _build_path(self):
        """Build a list of pixel coords that trace 'WONDER CABINET'."""
        path = []
        # Trace WONDER at y=WONDER_Y, then CABINET at y=CABINET_Y
        for text, bx, by in [("WONDER", WONDER_X, WONDER_Y),
                               ("CABINET", CABINET_X, CABINET_Y)]:
            for ci, ch in enumerate(text):
                cx = bx + ci * 4
                # Simple raster: go through each column of 3x5 glyph
                for col in range(3):
                    for row in range(5):
                        path.append((cx + col, by + row))
        return path

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.path = self._build_path()
        self.trail = []
        self.head_idx = 0
        self.step_timer = 0.0

    def update(self, dt: float):
        self.time += dt
        self.step_timer += dt
        speed = 0.01  # seconds per step
        while self.step_timer >= speed and self.head_idx < len(self.path):
            self.trail.append(self.path[self.head_idx])
            self.head_idx += 1
            self.step_timer -= speed
            # Keep trail finite for snake body look
            if len(self.trail) > 30:
                self.trail.pop(0)

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Draw completed letters (already traced)
        completed = self.head_idx
        for i in range(completed - len(self.trail)):
            if 0 <= i < len(self.path):
                px, py = self.path[i]
                if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                    self.display.set_pixel(px, py, (0, 100, 0))

        # Draw snake body (fading green)
        for i, (px, py) in enumerate(self.trail):
            frac = i / max(1, len(self.trail) - 1)
            bright = int(80 + 175 * frac)
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                self.display.set_pixel(px, py, (0, bright, 0))

        # Snake head
        if self.trail:
            hx, hy = self.trail[-1]
            if 0 <= hx < GRID_SIZE and 0 <= hy < GRID_SIZE:
                self.display.set_pixel(hx, hy, (0, 255, 0))
                # Eyes
                if hx + 1 < GRID_SIZE:
                    self.display.set_pixel(hx + 1, hy, (255, 50, 50))

        # After path complete, show full title cycling
        if self.head_idx >= len(self.path):
            hold = self.time - (len(self.path) * 0.01)
            if hold > 0.5:
                hue = (self.time * 0.2) % 1.0
                c = _hue_to_rgb(hue)
                self.display.draw_text_small(WONDER_X, WONDER_Y, "WONDER", c)
                c2 = _hue_to_rgb((hue + 0.15) % 1.0)
                self.display.draw_text_small(CABINET_X, CABINET_Y, "CABINET", c2)
            if hold > 4.0:
                self.reset()


# =========================================================================
# WonderAsteroids - Vector-style floating letters
# =========================================================================

class WonderAsteroids(Visual):
    name = "WONDER ASTRDS"
    description = "Asteroids vector title"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        # Floating letter chunks
        self.chunks = []
        for text, bx, by in [("WONDER", WONDER_X, WONDER_Y),
                               ("CABINET", CABINET_X, CABINET_Y)]:
            for i, ch in enumerate(text):
                self.chunks.append({
                    'char': ch,
                    'home_x': bx + i * 4,
                    'home_y': by,
                    'x': random.uniform(0, 60),
                    'y': random.uniform(0, 60),
                    'vx': random.uniform(-10, 10),
                    'vy': random.uniform(-10, 10),
                    'angle': random.uniform(0, math.pi * 2),
                    'spin': random.uniform(-2, 2),
                })

    def update(self, dt: float):
        self.time += dt
        for chunk in self.chunks:
            if self.time < 4.0:
                # Drift phase
                chunk['x'] += chunk['vx'] * dt
                chunk['y'] += chunk['vy'] * dt
                chunk['angle'] += chunk['spin'] * dt
                # Wrap around
                chunk['x'] = chunk['x'] % GRID_SIZE
                chunk['y'] = chunk['y'] % GRID_SIZE
            else:
                # Converge to home positions
                frac = min(1.0, (self.time - 4.0) / 2.0)
                ease = frac * frac * (3 - 2 * frac)
                chunk['x'] += (chunk['home_x'] - chunk['x']) * ease * dt * 3
                chunk['y'] += (chunk['home_y'] - chunk['y']) * ease * dt * 3
                chunk['angle'] *= (1.0 - ease * dt * 3)

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Vector-style: draw letters at their positions
        for chunk in self.chunks:
            x, y = int(chunk['x']), int(chunk['y'])
            # Green vector glow
            self.display.draw_text_small(x, y, chunk['char'], (0, 255, 100))

        # Ship in center during drift phase
        if self.time < 4.0:
            sx, sy = 32, 32
            a = self.time * 0.5
            # Simple triangle ship
            pts = [
                (sx + int(3 * math.cos(a)), sy + int(3 * math.sin(a))),
                (sx + int(3 * math.cos(a + 2.3)), sy + int(3 * math.sin(a + 2.3))),
                (sx + int(3 * math.cos(a - 2.3)), sy + int(3 * math.sin(a - 2.3))),
            ]
            for i in range(3):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % 3]
                self.display.draw_line(x0, y0, x1, y1, (0, 255, 100))

        # Reset after converged + hold
        if self.time > 8.0:
            self.reset()


# =========================================================================
# WonderDoom - Fire-engulfed title
# =========================================================================

class WonderDoom(Visual):
    name = "WONDER DOOM"
    description = "Fire engulfed title"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        # Fire buffer (bottom-up heat simulation)
        self.fire = [[0.0] * GRID_SIZE for _ in range(GRID_SIZE)]

    def update(self, dt: float):
        self.time += dt
        # Seed bottom row with random heat
        for x in range(GRID_SIZE):
            self.fire[GRID_SIZE - 1][x] = random.uniform(0.3, 1.0)
        # Propagate upward
        for y in range(0, GRID_SIZE - 1):
            for x in range(GRID_SIZE):
                below = self.fire[min(GRID_SIZE - 1, y + 1)][x]
                left = self.fire[min(GRID_SIZE - 1, y + 1)][max(0, x - 1)]
                right = self.fire[min(GRID_SIZE - 1, y + 1)][min(63, x + 1)]
                below2 = self.fire[min(GRID_SIZE - 1, y + 2)][x] if y + 2 < GRID_SIZE else 0
                self.fire[y][x] = (below + left + right + below2) / 4.08

    def draw(self):
        self.display.clear(Colors.BLACK)
        # Draw fire
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                heat = self.fire[y][x]
                if heat > 0.01:
                    r = min(255, int(heat * 380))
                    g = min(255, max(0, int((heat - 0.3) * 400)))
                    b = min(255, max(0, int((heat - 0.7) * 500)))
                    self.display.set_pixel(x, y, (r, g, b))

        # Title text with ember glow
        t = self.time
        pulse = 0.7 + 0.3 * math.sin(t * 3)
        r = int(255 * pulse)
        g = int(120 * pulse)
        # Glow behind text
        for ox in [-1, 0, 1]:
            for oy in [-1, 0, 1]:
                if ox == 0 and oy == 0:
                    continue
                self.display.draw_text_small(WONDER_X + ox, WONDER_Y + oy,
                                             "WONDER", (r // 3, g // 4, 0))
                self.display.draw_text_small(CABINET_X + ox, CABINET_Y + oy,
                                             "CABINET", (r // 3, g // 4, 0))
        self.display.draw_text_small(WONDER_X, WONDER_Y, "WONDER",
                                     (r, g, 0))
        self.display.draw_text_small(CABINET_X, CABINET_Y, "CABINET",
                                     (r, int(g * 0.8), 0))


# =========================================================================
# WonderPipe - Screensaver pipes reveal title
# =========================================================================

class WonderPipe(Visual):
    name = "WONDER PIPE"
    description = "Pipes screensaver title"
    category = "titles"

    DIRS = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # up, right, down, left

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.pipes = []
        self.grid = [[False] * GRID_SIZE for _ in range(GRID_SIZE)]
        self._start_pipe()
        self.step_timer = 0.0

    def _start_pipe(self):
        self.pipe_x = random.randint(4, 59)
        self.pipe_y = random.randint(4, 59)
        self.pipe_dir = random.randint(0, 3)
        self.pipe_color = _hue_to_rgb(random.random())
        self.pipe_steps = 0

    def update(self, dt: float):
        self.time += dt
        self.step_timer += dt
        while self.step_timer >= 0.03:
            self.step_timer -= 0.03
            # Advance pipe
            dx, dy = self.DIRS[self.pipe_dir]
            nx = self.pipe_x + dx
            ny = self.pipe_y + dy
            # Turn randomly or if hitting edge/existing pipe
            if (not (1 <= nx < GRID_SIZE - 1 and 1 <= ny < GRID_SIZE - 1) or
                    self.grid[ny][nx] or random.random() < 0.15):
                self.pipe_dir = (self.pipe_dir + random.choice([-1, 1])) % 4
                # Joint
                if 0 <= self.pipe_x < GRID_SIZE and 0 <= self.pipe_y < GRID_SIZE:
                    self.display.set_pixel(self.pipe_x, self.pipe_y,
                                           (min(255, self.pipe_color[0] + 60),
                                            min(255, self.pipe_color[1] + 60),
                                            min(255, self.pipe_color[2] + 60)))
                self.pipe_steps += 1
            else:
                self.pipe_x = nx
                self.pipe_y = ny
                if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                    self.grid[ny][nx] = True
                    self.pipes.append((nx, ny, self.pipe_color))
                self.pipe_steps += 1

            # New pipe after enough steps
            if self.pipe_steps > 80:
                self._start_pipe()

    def draw(self):
        self.display.clear(Colors.BLACK)
        # Draw pipes
        for px, py, color in self.pipes:
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                self.display.set_pixel(px, py, color)

        # Title over pipes
        if self.time > 2.0:
            fade = min(1.0, (self.time - 2.0) / 1.0)
            c = (int(255 * fade), int(255 * fade), int(255 * fade))
            # Dark backing for readability
            self.display.draw_rect(WONDER_X - 1, WONDER_Y - 1,
                                   WONDER_W + 2, 7, Colors.BLACK)
            self.display.draw_rect(CABINET_X - 1, CABINET_Y - 1,
                                   CABINET_W + 2, 7, Colors.BLACK)
            self.display.draw_text_small(WONDER_X, WONDER_Y, "WONDER", c)
            self.display.draw_text_small(CABINET_X, CABINET_Y, "CABINET", c)

        # Reset periodically
        if self.time > 12.0:
            self.reset()


# =========================================================================
# WonderWinXP - Bliss hillside with title
# =========================================================================

class WonderWinXP(Visual):
    name = "WONDER XP"
    description = "Windows XP Bliss hill"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        # Precompute hill profile
        self.hill = []
        for x in range(GRID_SIZE):
            # Rolling hill shape
            h = 38 + int(6 * math.sin(x * 0.08) + 3 * math.sin(x * 0.15 + 1))
            self.hill.append(h)

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        self.display.clear((100, 160, 255))  # sky blue
        t = self.time

        # Clouds
        for ci in range(3):
            cx = int((ci * 25 + t * 3) % 80) - 8
            cy = 6 + ci * 7
            for dx in range(-5, 6):
                for dy in range(-2, 3):
                    if dx * dx + dy * dy * 4 < 20:
                        px = cx + dx
                        if 0 <= px < GRID_SIZE and 0 <= cy + dy < GRID_SIZE:
                            self.display.set_pixel(px, cy + dy, (240, 245, 255))

        # Green hill
        for x in range(GRID_SIZE):
            hill_y = self.hill[x]
            for y in range(hill_y, GRID_SIZE):
                # Gradient green
                frac = (y - hill_y) / max(1, GRID_SIZE - hill_y)
                g = int(180 - 80 * frac)
                r = int(60 - 30 * frac)
                b = int(30 - 15 * frac)
                self.display.set_pixel(x, y, (r, g, b))

        # XP-style window with title
        if t > 1.0:
            fade = min(1.0, (t - 1.0) / 1.0)
            # Window border
            wx, wy, ww, wh = 6, 14, 52, 28
            # Blue title bar
            self.display.draw_rect(wx, wy, ww, 7,
                (int(0 * fade), int(80 * fade), int(215 * fade)))
            # White window body
            self.display.draw_rect(wx, wy + 7, ww, wh - 7,
                (int(240 * fade), int(240 * fade), int(240 * fade)))
            # Border
            self.display.draw_rect(wx, wy, ww, wh,
                (int(100 * fade), int(100 * fade), int(200 * fade)), filled=False)
            # Title text in window
            c = (int(40 * fade), int(40 * fade), int(120 * fade))
            self.display.draw_text_small(WONDER_X, wy + 10, "WONDER", c)
            self.display.draw_text_small(CABINET_X, wy + 18, "CABINET", c)


# =========================================================================
# WonderGlitch - Datamosh corruption reveal
# =========================================================================

class WonderGlitch(Visual):
    name = "WONDER GLITCH"
    description = "Glitch art title"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.glitch_rows = {}  # y -> (offset, color_shift, duration)
        self.next_glitch = 0.0

    def update(self, dt: float):
        self.time += dt
        # Trigger glitch bursts
        if self.time > self.next_glitch:
            intensity = min(1.0, self.time / 4.0)
            count = random.randint(2, int(8 * intensity) + 2)
            for _ in range(count):
                y = random.randint(0, GRID_SIZE - 1)
                self.glitch_rows[y] = (
                    random.randint(-20, 20),        # x offset
                    random.choice([(1,0,0), (0,1,0), (0,0,1), (1,1,0)]),  # channel
                    self.time + random.uniform(0.05, 0.3),  # expiry
                )
            self.next_glitch = self.time + random.uniform(0.1, 0.5)

        # Expire old glitches
        expired = [y for y, (_, _, exp) in self.glitch_rows.items()
                   if self.time > exp]
        for y in expired:
            del self.glitch_rows[y]

    def draw(self):
        self.display.clear(Colors.BLACK)
        t = self.time

        # Base: title text that gradually assembles
        reveal = min(1.0, t / 5.0)

        # Draw text
        hue = (t * 0.15) % 1.0
        c1 = _hue_to_rgb(hue)
        c2 = _hue_to_rgb((hue + 0.15) % 1.0)

        # Scanlines / static background
        for y in range(GRID_SIZE):
            if y in self.glitch_rows:
                offset, channel, _ = self.glitch_rows[y]
                for x in range(GRID_SIZE):
                    sx = (x + offset) % GRID_SIZE
                    bright = random.randint(30, 100)
                    c = (bright * channel[0], bright * channel[1],
                         bright * channel[2])
                    self.display.set_pixel(x, y, c)
            else:
                # Subtle scanlines
                if random.random() < 0.02:
                    gray = random.randint(10, 30)
                    for x in range(GRID_SIZE):
                        self.display.set_pixel(x, y, (gray, gray, gray))

        # Title with glitch displacement
        if reveal > 0.3:
            alpha = min(1.0, (reveal - 0.3) / 0.7)
            tc1 = (int(c1[0] * alpha), int(c1[1] * alpha), int(c1[2] * alpha))
            tc2 = (int(c2[0] * alpha), int(c2[1] * alpha), int(c2[2] * alpha))
            # Occasional RGB split
            if random.random() < 0.3 and self.glitch_rows:
                self.display.draw_text_small(WONDER_X - 1, WONDER_Y,
                    "WONDER", (tc1[0], 0, 0))
                self.display.draw_text_small(WONDER_X + 1, WONDER_Y,
                    "WONDER", (0, 0, tc1[2]))
                self.display.draw_text_small(CABINET_X - 1, CABINET_Y,
                    "CABINET", (tc2[0], 0, 0))
                self.display.draw_text_small(CABINET_X + 1, CABINET_Y,
                    "CABINET", (0, 0, tc2[2]))
            self.display.draw_text_small(WONDER_X, WONDER_Y, "WONDER", tc1)
            self.display.draw_text_small(CABINET_X, CABINET_Y, "CABINET", tc2)


# =========================================================================
# WonderTypewriter - Letter-by-letter with carriage return
# =========================================================================

class WonderTypewriter(Visual):
    name = "WONDER TYPE"
    description = "Typewriter title"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.text = "WONDER  CABINET"
        self.typed = 0
        self.type_timer = 0.0
        self.carriage_x = 0.0

    def update(self, dt: float):
        self.time += dt
        if self.typed < len(self.text):
            self.type_timer += dt
            if self.type_timer > 0.2:
                self.type_timer = 0.0
                self.typed += 1
                # Carriage return between words
                if self.typed == 7:  # After "WONDER "
                    self.carriage_x = 60.0

    def draw(self):
        self.display.clear((30, 25, 20))  # Warm paper color
        t = self.time

        # Paper texture - subtle horizontal lines
        for y in range(0, GRID_SIZE, 3):
            for x in range(GRID_SIZE):
                self.display.set_pixel(x, y, (35, 30, 25))

        # Ink ribbon line at top
        self.display.draw_rect(0, 8, GRID_SIZE, 1, (20, 15, 10))

        # Typed text - WONDER
        wonder_chars = min(6, self.typed)
        if wonder_chars > 0:
            text = "WONDER"[:wonder_chars]
            self.display.draw_text_small(WONDER_X, WONDER_Y, text, (15, 10, 5))

        # Typed text - CABINET
        if self.typed > 8:
            cab_chars = min(7, self.typed - 8)
            text = "CABINET"[:cab_chars]
            self.display.draw_text_small(CABINET_X, CABINET_Y, text, (15, 10, 5))

        # Carriage / cursor
        if self.typed < len(self.text):
            blink = int(t * 4) % 2
            if self.typed <= 6:
                cx = WONDER_X + self.typed * 4
                cy = WONDER_Y
            else:
                cab_idx = max(0, self.typed - 8)
                cx = CABINET_X + cab_idx * 4
                cy = CABINET_Y
            if blink:
                self.display.draw_rect(cx, cy, 1, 5, (60, 40, 20))
        else:
            # After typing complete, warm color cycle
            hold = t - self.typed * 0.2
            if hold > 1.0:
                pulse = 0.7 + 0.3 * math.sin(hold * 2)
                c = (int(120 * pulse), int(80 * pulse), int(40 * pulse))
                self.display.draw_text_small(WONDER_X, WONDER_Y, "WONDER", c)
                self.display.draw_text_small(CABINET_X, CABINET_Y, "CABINET", c)

            # Reset after hold
            if hold > 5.0:
                self.reset()


# =========================================================================
# WonderZoom - Starfield rush into title
# =========================================================================

class WonderZoom(Visual):
    name = "WONDER ZOOM"
    description = "Starfield zoom title"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.stars = []
        for _ in range(80):
            self.stars.append({
                'x': random.uniform(-1, 1),
                'y': random.uniform(-1, 1),
                'z': random.uniform(0.1, 1.0),
                'speed': random.uniform(0.3, 1.0),
            })

    def update(self, dt: float):
        self.time += dt
        for star in self.stars:
            star['z'] -= star['speed'] * dt * 0.8
            if star['z'] <= 0.01:
                star['x'] = random.uniform(-1, 1)
                star['y'] = random.uniform(-1, 1)
                star['z'] = 1.0

    def draw(self):
        self.display.clear(Colors.BLACK)
        t = self.time
        cx, cy = 32, 32

        # Draw stars with perspective projection
        for star in self.stars:
            # Project to screen
            sx = cx + int(star['x'] / star['z'] * 30)
            sy = cy + int(star['y'] / star['z'] * 30)
            # Brightness based on closeness
            bright = int(min(255, 50 + 200 * (1.0 - star['z'])))
            if 0 <= sx < GRID_SIZE and 0 <= sy < GRID_SIZE:
                self.display.set_pixel(sx, sy, (bright, bright, bright))
                # Streak for close stars
                if star['z'] < 0.3:
                    streak = int(3 * (1.0 - star['z']) / 0.3)
                    dx = star['x'] / max(0.01, star['z'])
                    dy = star['y'] / max(0.01, star['z'])
                    mag = max(0.01, math.sqrt(dx * dx + dy * dy))
                    dx, dy = dx / mag, dy / mag
                    for s in range(1, streak + 1):
                        tx = sx - int(dx * s)
                        ty = sy - int(dy * s)
                        if 0 <= tx < GRID_SIZE and 0 <= ty < GRID_SIZE:
                            trail_b = bright // (s + 1)
                            self.display.set_pixel(tx, ty,
                                (trail_b, trail_b, trail_b))

        # Title appears from center, growing
        if t > 2.0:
            scale = min(1.0, (t - 2.0) / 2.0)
            ease = scale * scale * (3 - 2 * scale)
            alpha = ease
            c = (int(200 * alpha), int(220 * alpha), int(255 * alpha))
            c2 = (int(180 * alpha), int(200 * alpha), int(255 * alpha))
            self.display.draw_text_small(WONDER_X, WONDER_Y, "WONDER", c)
            self.display.draw_text_small(CABINET_X, CABINET_Y, "CABINET", c2)


# =========================================================================
# WonderVinyl - Spinning record with title on label
# =========================================================================

class WonderVinyl(Visual):
    name = "WONDER VINYL"
    description = "Spinning record title"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        self.display.clear(Colors.BLACK)
        t = self.time
        cx, cy = 32, 30
        radius = 28

        # Record disc (dark with grooves)
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                dist = math.sqrt(dx * dx + dy * dy)
                if dist <= radius:
                    # Groove pattern
                    groove = int(dist * 2 + t * 8) % 3
                    if dist < 8:
                        # Label area - colored
                        angle = math.atan2(dy, dx) + t * 2
                        hue = (angle / (math.pi * 2) + 0.5) % 1.0
                        c = _hue_to_rgb(hue)
                        c = (c[0] // 2 + 40, c[1] // 2 + 40, c[2] // 2 + 40)
                    elif dist < 3:
                        # Center hole
                        c = (20, 20, 20)
                    else:
                        # Vinyl grooves
                        base = 15 + groove * 8
                        # Light reflection sweeping across
                        angle = math.atan2(dy, dx)
                        ref = math.cos(angle - t * 1.5)
                        highlight = max(0, int(ref * 25))
                        c = (base + highlight, base + highlight, base + highlight + 5)
                    px, py = cx + dx, cy + dy
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        self.display.set_pixel(px, py, c)

        # Label text (rotates with record)
        # Just draw static centered text on the label
        self.display.draw_text_small(cx - 11, cy - 3, "WONDER", (220, 220, 240))
        self.display.draw_text_small(cx - 13, cy + 3, "CABINET", (220, 220, 240))

        # Tonearm
        arm_angle = 0.3 + 0.1 * math.sin(t * 0.2)
        ax = cx + int(radius * math.cos(arm_angle)) + 5
        ay = 2
        tip_x = cx + int(12 * math.cos(arm_angle + 0.5))
        tip_y = cy + int(12 * math.sin(arm_angle + 0.5)) - 8
        self.display.draw_line(ax, ay, tip_x, tip_y, (160, 160, 170))


# =========================================================================
# WonderCassette - Tape deck rewind and play
# =========================================================================

class WonderCassette(Visual):
    name = "WONDER TAPE"
    description = "Cassette tape title"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        self.display.clear((40, 35, 30))  # Brown tape player bg
        t = self.time

        # Cassette body
        body_x, body_y = 8, 10
        body_w, body_h = 48, 30
        self.display.draw_rect(body_x, body_y, body_w, body_h,
                               (80, 75, 65))  # Cassette shell
        self.display.draw_rect(body_x, body_y, body_w, body_h,
                               (60, 55, 45), filled=False)  # Border

        # Tape window
        win_x, win_y = 16, 15
        win_w, win_h = 32, 12
        self.display.draw_rect(win_x, win_y, win_w, win_h, (20, 18, 15))

        # Tape reels (two circles spinning)
        reel_speed = 4.0 if t < 3.0 else 1.0  # Fast rewind, then play
        reel_r = 4

        # Left reel (feeds out)
        lr_x, lr_y = win_x + 8, win_y + win_h // 2
        lr_size = reel_r - int(min(2, t * 0.3))  # Shrinks during rewind
        for dy in range(-reel_r, reel_r + 1):
            for dx in range(-reel_r, reel_r + 1):
                dist = math.sqrt(dx * dx + dy * dy)
                if dist <= reel_r:
                    angle = math.atan2(dy, dx) + t * reel_speed
                    spoke = int(angle * 3 / math.pi) % 2
                    c = (60, 50, 40) if spoke else (35, 30, 25)
                    if dist <= lr_size:
                        c = (70, 55, 35)  # Tape on reel
                    px, py = lr_x + dx, lr_y + dy
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        self.display.set_pixel(px, py, c)

        # Right reel (takes up)
        rr_x, rr_y = win_x + win_w - 8, win_y + win_h // 2
        rr_size = 1 + int(min(3, t * 0.3))  # Grows during play
        for dy in range(-reel_r, reel_r + 1):
            for dx in range(-reel_r, reel_r + 1):
                dist = math.sqrt(dx * dx + dy * dy)
                if dist <= reel_r:
                    angle = math.atan2(dy, dx) - t * reel_speed
                    spoke = int(angle * 3 / math.pi) % 2
                    c = (60, 50, 40) if spoke else (35, 30, 25)
                    if dist <= rr_size:
                        c = (70, 55, 35)
                    px, py = rr_x + dx, rr_y + dy
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        self.display.set_pixel(px, py, c)

        # Tape running between reels
        self.display.draw_line(lr_x + reel_r, lr_y, rr_x - reel_r, rr_y,
                               (45, 35, 25))

        # Label on cassette
        self.display.draw_rect(body_x + 4, body_y + 2, body_w - 8, 8,
                               (200, 195, 180))  # White label
        # Title on label
        label_c = (40, 30, 20) if t > 1.0 else (
            int(40 * t), int(30 * t), int(20 * t))
        self.display.draw_text_small(body_x + 8, body_y + 3, "WONDER", label_c)

        # CABINET below cassette
        if t > 2.0:
            fade = min(1.0, (t - 2.0) / 1.0)
            hue = (t * 0.1) % 1.0
            c = _hue_to_rgb(hue)
            c = (int(c[0] * fade), int(c[1] * fade), int(c[2] * fade))
            self.display.draw_text_small(CABINET_X, 46, "CABINET", c)


# =========================================================================
# WonderJake - Dancing Jake with popping text
# =========================================================================

class WonderJake(Visual):
    name = "WONDER JAKE"
    description = "Jake dance title"
    category = "titles"

    GIF_FILE = "jake_dance.gif"
    
    def __init__(self, display: Display):
        super().__init__(display)
        
    def reset(self):
        self.time = 0.0
        self.frame_timer = 0.0
        self.frame_index = 0
        self.frames = []
        self._load_gif()
        
    def _load_gif(self):
        """Load Jake dance GIF frames."""
        try:
            from PIL import Image
            from .gifcache import cache_frames, extract_rgb

            project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            path = os.path.join(project_dir, "assets", self.GIF_FILE)
            if not os.path.exists(path):
                return

            def process():
                gif = Image.open(path)
                orig_w, orig_h = gif.size
                # Center crop to square
                sq = min(orig_w, orig_h)
                x_off = (orig_w - sq) // 2
                y_off = (orig_h - sq) // 2
                canvas = None
                frames = []
                for i in range(getattr(gif, 'n_frames', 1)):
                    gif.seek(i)
                    frame = gif.convert("RGBA")
                    if canvas is None:
                        canvas = frame.copy()
                    else:
                        canvas.paste(frame, (0, 0), frame)
                    cropped = canvas.copy().crop((x_off, y_off, x_off + sq, y_off + sq))
                    scaled = cropped.resize((GRID_SIZE, GRID_SIZE),
                                            Image.Resampling.NEAREST)
                    frames.append(extract_rgb(scaled))
                return frames

            self.frames = cache_frames(path, process)
        except:
            pass
    
    def update(self, dt: float):
        self.time += dt
        
        # Animate Jake
        if self.frames:
            self.frame_timer += dt
            if self.frame_timer >= 0.08:  # ~12 fps
                self.frame_timer = 0.0
                self.frame_index = (self.frame_index + 1) % len(self.frames)
        
    def draw(self):
        d = self.display
        d.clear(Colors.BLACK)
        t = self.time
        
        # Draw Jake dancing GIF
        if self.frames and len(self.frames) > 0:
            frame = self.frames[self.frame_index]
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    d.set_pixel(x, y, frame[y][x])
        
        # Pop-up text effect for WONDER and CABINET
        # WONDER pops up first, then CABINET
        if t > 1.0:
            # WONDER pop
            wonder_t = min(1.0, (t - 1.0) / 0.5)
            # Bounce effect
            if wonder_t < 1.0:
                bounce = abs(math.sin(wonder_t * math.pi * 2)) * 3
                y_off = int((1.0 - wonder_t) * 10 - bounce)
            else:
                y_off = 0
            
            # Scale and fade in
            alpha = wonder_t
            c = (int(255 * alpha), int(220 * alpha), int(100 * alpha))
            d.draw_text_small(WONDER_X, max(2, 8 - y_off), "WONDER", c)
        
        if t > 1.8:
            # CABINET pop
            cabinet_t = min(1.0, (t - 1.8) / 0.5)
            # Bounce effect
            if cabinet_t < 1.0:
                bounce = abs(math.sin(cabinet_t * math.pi * 2)) * 3
                y_off = int((1.0 - cabinet_t) * 10 - bounce)
            else:
                y_off = 0
            
            # Scale and fade in
            alpha = cabinet_t
            c = (int(40 * alpha), int(140 * alpha), int(200 * alpha))
            d.draw_text_small(CABINET_X, max(2, 16 - y_off), "CABINET", c)


# =========================================================================
# WonderSauron - Eye of Sauron title
# =========================================================================

class WonderSauron(Visual):
    name = "WONDER SAURON"
    description = "The Eye of Sauron"
    category = "titles"

    _CX = 32
    _CY = 22
    _EW = 24   # eye half-width
    _EH = 10   # eye half-height

    def __init__(self, display: Display):
        super().__init__(display)
        # Precompute parabolic eye half-heights per column
        self._col_hh = {}
        for px in range(self._CX - self._EW, self._CX + self._EW + 1):
            nx = abs(px - self._CX) / self._EW
            self._col_hh[px] = self._EH * (1.0 - nx * nx)

    def reset(self):
        self.time = 0.0
        self.sparks = [self._spark() for _ in range(30)]

    def _spark(self):
        a = random.uniform(0, math.pi * 2)
        life = random.uniform(0.3, 1.2)
        return {
            'x': self._CX + self._EW * math.cos(a) * random.uniform(0.6, 1.0),
            'y': self._CY + self._EH * math.sin(a) * random.uniform(0.6, 1.0),
            'vx': random.uniform(-1.5, 1.5),
            'vy': random.uniform(-18, -6),
            'life': life, 'ml': life,
        }

    def update(self, dt: float):
        self.time += dt
        for s in self.sparks:
            s['x'] += s['vx'] * dt
            s['y'] += s['vy'] * dt
            s['life'] -= dt
            if s['life'] <= 0:
                s.update(self._spark())

    def draw(self):
        d = self.display
        d.clear()
        t = self.time
        cx, cy = self._CX, self._CY
        ew, eh = self._EW, self._EH
        pulse = 0.8 + 0.2 * math.sin(t * 2.3)

        # Pupil drift (slowly looks left/right)
        pcx = cx + 2.5 * math.sin(t * 0.6)
        slit_hw = 1.0 + 0.5 * math.sin(t * 1.5)

        # Ambient glow behind eye
        glow_w, glow_h = ew + 3, eh + 5
        for py in range(max(0, cy - glow_h), min(GRID_SIZE, cy + glow_h + 1)):
            for px in range(max(0, cx - glow_w), min(GRID_SIZE, cx + glow_w + 1)):
                dx = (px - cx) / glow_w
                dy = (py - cy) / glow_h
                d2 = dx * dx + dy * dy
                if d2 < 1.0:
                    g = (1.0 - d2) * 0.2 * pulse
                    r = int(100 * g)
                    if r > 1:
                        d.set_pixel(px, py, (r, int(15 * g), 0))

        # Eye body
        for px, hh in self._col_hh.items():
            y_lo = max(0, int(cy - hh))
            y_hi = min(GRID_SIZE - 1, int(cy + hh))
            nx = abs(px - cx) / ew
            for py in range(y_lo, y_hi + 1):
                dy = py - cy
                if abs(dy) > hh:
                    continue
                rim = abs(dy) / hh if hh > 0 else 1.0

                # Slit pupil
                pdist = abs(px - pcx)
                if pdist <= slit_hw and rim < 0.8:
                    d.set_pixel(px, py, (int(20 * pulse), int(5 * pulse), 0))
                    continue

                # Fire intensity
                intensity = (1.0 - rim * 0.6) * (1.0 - nx * 0.3) * pulse
                # Bright iris glow near slit edge
                nd = pdist / ew
                if nd < 0.25:
                    intensity *= 1.0 + 0.5 * (1.0 - nd / 0.25)
                if intensity > 1.0:
                    intensity = 1.0
                # Flicker
                intensity *= 0.88 + 0.12 * math.sin(px * 3.7 + py * 2.3 + t * 8.5)

                # Fire color ramp
                if intensity > 0.7:
                    r = int(255 * intensity)
                    g = int(200 * (intensity - 0.2))
                    b = int(30 * max(0, intensity - 0.6))
                elif intensity > 0.4:
                    r = int(255 * intensity)
                    g = int(90 * intensity)
                    b = 0
                else:
                    v = max(0.0, intensity * 1.8)
                    r = int(160 * v)
                    g = int(25 * v)
                    b = 0
                if r > 1:
                    d.set_pixel(px, py, (min(255, r), min(255, g), min(255, b)))

        # Rising embers
        for s in self.sparks:
            frac = max(0.0, s['life'] / s['ml'])
            sx, sy = int(s['x']), int(s['y'])
            if 0 <= sx < GRID_SIZE and 0 <= sy < GRID_SIZE and frac > 0:
                d.set_pixel(sx, sy, (int(255 * frac), int(90 * frac * frac), 0))

        # Title text in fire colors
        tp = 0.6 + 0.4 * math.sin(t * 1.2)
        d.draw_text_small(WONDER_X, 44, "WONDER",
                          (int(210 * tp), int(100 * tp), 0))
        tp2 = 0.6 + 0.4 * math.sin(t * 1.2 + 0.5)
        d.draw_text_small(CABINET_X, 52, "CABINET",
                          (int(180 * tp2), int(80 * tp2), 0))


# =========================================================================
# WonderVertigo - Hitchcock / Saul Bass spiral
# =========================================================================

class WonderVertigo(Visual):
    name = "WONDER VERTIGO"
    description = "Saul Bass spiral"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)
        # Pre-compute polar coords
        cx, cy = GRID_SIZE / 2, GRID_SIZE / 2
        self._angle = [[0.0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self._radius = [[0.0] * GRID_SIZE for _ in range(GRID_SIZE)]
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                dx = x - cx + 0.5
                dy = y - cy + 0.5
                self._angle[y][x] = math.atan2(dy, dx)
                self._radius[y][x] = math.sqrt(dx * dx + dy * dy)

    def reset(self):
        self.time = 0.0

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        d = self.display
        d.clear()
        t = self.time

        # Green Saul Bass palette
        pal = [(0, 0, 0), (0, 60, 25), (0, 140, 55), (0, 200, 80)]

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                angle = self._angle[y][x]
                radius = self._radius[y][x]

                # Dual spirals rotating opposite directions
                spiral = angle * 3.0 + radius * 0.35 - t * 2.0
                spiral2 = angle * 5.0 - radius * 0.25 + t * 1.3
                pulse = math.sin(t * 0.7) * 0.15
                v1 = math.sin(spiral + pulse) * 0.5 + 0.5
                v2 = math.sin(spiral2) * 0.5 + 0.5
                v = v1 * 0.65 + v2 * 0.35

                # Sharp threshold bands for woodcut look
                if v < 0.25:
                    color = pal[0]
                elif v < 0.45:
                    color = pal[1]
                elif v < 0.7:
                    color = pal[2]
                else:
                    color = pal[3]

                # Fade edges to black
                edge = max(0.0, 1.0 - radius / 38.0)
                if edge < 1.0:
                    color = (int(color[0] * edge), int(color[1] * edge),
                             int(color[2] * edge))

                d.set_pixel(x, y, color)

        # Title text - green on black, pulsing
        tp = 0.6 + 0.4 * math.sin(t * 1.5)
        d.draw_text_small(WONDER_X, WONDER_Y, "WONDER",
                          (int(80 * tp), int(220 * tp), int(90 * tp)))
        tp2 = 0.6 + 0.4 * math.sin(t * 1.5 + 0.4)
        d.draw_text_small(CABINET_X, CABINET_Y, "CABINET",
                          (int(60 * tp2), int(180 * tp2), int(70 * tp2)))


# =========================================================================
# WonderStargate - 2001: A Space Odyssey slit-scan tunnel
# =========================================================================

class WonderStargate(Visual):
    name = "WONDER STARGATE"
    description = "2001 slit-scan tunnel"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)
        cx, cy = GRID_SIZE / 2, GRID_SIZE / 2
        self._dist = [[0.0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self._angle = [[0.0] * GRID_SIZE for _ in range(GRID_SIZE)]
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                dx = abs(x - cx + 0.5)
                dy = abs(y - cy + 0.5)
                self._dist[y][x] = max(dx, dy)  # Chebyshev = rectangular tunnel
                self._angle[y][x] = math.atan2(y - cy + 0.5, x - cx + 0.5)

    def reset(self):
        self.time = 0.0

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        d = self.display
        d.clear()
        t = self.time

        # Kubrick blue/orange palette
        pal = [
            (0, 0, 40), (0, 60, 180), (200, 100, 0), (255, 180, 50),
            (0, 30, 120), (255, 130, 20),
        ]
        n_colors = len(pal)

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                dist = self._dist[y][x]
                angle = self._angle[y][x]

                if dist < 0.5:
                    continue

                # Tunnel depth via inverse distance
                depth = 30.0 / dist
                band = depth * 3.0 - t * 4.0 + (angle / math.pi) * 0.5

                band_val = band % n_colors
                idx = int(band_val) % n_colors
                frac = band_val - int(band_val)
                c1 = pal[idx]
                c2 = pal[(idx + 1) % n_colors]
                r = int(c1[0] + (c2[0] - c1[0]) * frac)
                g = int(c1[1] + (c2[1] - c1[1]) * frac)
                b = int(c1[2] + (c2[2] - c1[2]) * frac)

                # Brightness falloff + shimmer
                brightness = min(1.0, dist / 8.0)
                brightness *= 0.85 + 0.15 * math.sin(depth * 6.0 + t * 3.0)
                d.set_pixel(x, y, (int(r * brightness), int(g * brightness),
                                   int(b * brightness)))

        # Title text - electric blue/white
        tp = 0.7 + 0.3 * math.sin(t * 2.0)
        d.draw_text_small(WONDER_X, WONDER_Y, "WONDER",
                          (int(150 * tp), int(200 * tp), int(255 * tp)))
        tp2 = 0.7 + 0.3 * math.sin(t * 2.0 + 0.5)
        d.draw_text_small(CABINET_X, CABINET_Y, "CABINET",
                          (int(120 * tp2), int(170 * tp2), int(255 * tp2)))


# =========================================================================
# WonderPsycho - Hitchcock's shower drain spiral
# =========================================================================

class WonderPsycho(Visual):
    name = "WONDER PSYCHO"
    description = "Shower drain spiral"
    category = "titles"

    _DRAIN_CX = GRID_SIZE // 2
    _DRAIN_CY = GRID_SIZE // 2 + 2

    def __init__(self, display: Display):
        super().__init__(display)
        cx, cy = self._DRAIN_CX, self._DRAIN_CY
        self._angle = [[0.0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self._radius = [[0.0] * GRID_SIZE for _ in range(GRID_SIZE)]
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                dx = x - cx + 0.5
                dy = y - cy + 0.5
                self._angle[y][x] = math.atan2(dy, dx)
                self._radius[y][x] = math.sqrt(dx * dx + dy * dy)

    def reset(self):
        self.time = 0.0

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        d = self.display
        d.clear()
        t = self.time
        cx, cy = self._DRAIN_CX, self._DRAIN_CY

        # Slowly oscillating convergence
        progress = math.sin(t * 0.25) * 0.5 + 0.5  # 0→1→0

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                angle = self._angle[y][x]
                radius = self._radius[y][x]

                # Spiral arms converging on drain
                spiral = angle * 2.0 + radius * 0.4 - t * 3.0

                converge = max(0.0, radius - (1.0 - progress) * 35)
                in_flow = converge < 15.0
                v = math.sin(spiral) * 0.5 + 0.5

                if in_flow and radius < 35:
                    # BW noir: mix gray water and dark streaks
                    blood_mix = progress * 0.5 + v * 0.3
                    # Grayscale noir palette
                    water_l = int(130 - blood_mix * 80)
                    streak = abs(math.sin(spiral * 2.0))
                    water_l = max(10, int(water_l + streak * 30))

                    # Subtle warm tint at high convergence
                    warm = progress * 0.4
                    color = (min(255, int(water_l * (1.0 + warm * 0.4))),
                             int(water_l * (1.0 - warm * 0.1)),
                             int(water_l * (1.0 - warm * 0.3)))

                    # Darken toward center (drain hole)
                    center_dark = max(0.0, 1.0 - radius / 6.0)
                    if center_dark > 0:
                        color = (int(color[0] * (1 - center_dark)),
                                 int(color[1] * (1 - center_dark)),
                                 int(color[2] * (1 - center_dark)))
                else:
                    # White porcelain
                    base = max(60, 200 - int(radius * 1.5))
                    color = (base, base - 3, base - 6)

                d.set_pixel(x, y, color)

        # Drain hole
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                if dx * dx + dy * dy <= 4:
                    px, py = cx + dx, cy + dy
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        d.set_pixel(px, py, (8, 8, 10))

        # Title text - cold white, slightly flickering
        flick = 0.8 + 0.2 * math.sin(t * 6.0 + math.sin(t * 2.3) * 3)
        d.draw_text_small(WONDER_X, WONDER_Y, "WONDER",
                          (int(220 * flick), int(220 * flick), int(230 * flick)))
        flick2 = 0.8 + 0.2 * math.sin(t * 6.0 + 1.0 + math.sin(t * 2.3) * 3)
        d.draw_text_small(CABINET_X, CABINET_Y, "CABINET",
                          (int(200 * flick2), int(200 * flick2), int(210 * flick2)))


# =========================================================================
# WonderNosferatu - Murnau's shadow on stairs
# =========================================================================

class WonderNosferatu(Visual):
    name = "WONDER NOSFERATU"
    description = "Shadow on the stairs"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        d = self.display
        d.clear()
        t = self.time

        # Candlelight flicker
        flicker = (0.82 + 0.18 * math.sin(t * 11.0)
                   * (0.9 + 0.1 * math.sin(t * 7.3)))

        # Staircase wall background
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                stair_y = (y + x // 2) % 12
                if stair_y < 1:
                    base = (120, 90, 40)
                elif stair_y < 6:
                    base = (90, 65, 30)
                else:
                    base = (150, 115, 55)
                # Darker at top (light from below)
                vert = 0.55 + 0.45 * (y / GRID_SIZE)
                c = (int(base[0] * vert * flicker),
                     int(base[1] * vert * flicker),
                     int(base[2] * vert * flicker))
                d.set_pixel(x, y, c)

        # Shadow silhouette - cycles through phases
        cycle = 12.0
        phase_t = t % cycle
        if phase_t < 5.0:
            # Climb: shadow rises from bottom
            progress = phase_t / 5.0
            y_off = int(55 - progress * 40)
            hand_ext = 0.0
            scale = 0.6 + progress * 0.4
        elif phase_t < 9.0:
            # Loom: hand extends
            progress = (phase_t - 5.0) / 4.0
            y_off = 15
            hand_ext = progress
            scale = 1.0 + progress * 0.3
        else:
            # Retreat
            progress = (phase_t - 9.0) / 3.0
            y_off = int(15 + progress * 45)
            hand_ext = max(0.0, 1.0 - progress * 2)
            scale = 1.3 - progress * 0.7

        shadow = (12, 8, 4)
        sx = 38

        # Head (bald oval)
        head_cy = y_off + int(8 * scale)
        head_rx = int(5 * scale)
        head_ry = int(7 * scale)
        for dy in range(-head_ry, head_ry + 1):
            row = head_cy + dy
            if 0 <= row < GRID_SIZE:
                tv = dy / head_ry if head_ry > 0 else 0
                w = int(head_rx * math.sqrt(max(0, 1 - tv * tv)))
                for dx in range(-w, w + 1):
                    col = sx + dx
                    if 0 <= col < GRID_SIZE:
                        d.set_pixel(col, row, shadow)

        # Pointed ears
        for i in range(int(3 * scale)):
            ear_y = head_cy - head_ry + i
            for side in [-1, 1]:
                ear_x = sx + side * (head_rx + i)
                if 0 <= ear_x < GRID_SIZE and 0 <= ear_y < GRID_SIZE:
                    d.set_pixel(ear_x, ear_y, shadow)

        # Body
        body_top = head_cy + head_ry
        for i in range(int(20 * scale)):
            row = body_top + i
            if row >= GRID_SIZE:
                break
            w = max(2, int((6 - i * 0.1) * scale))
            for dx in range(-w, w + 1):
                col = sx + dx
                if 0 <= col < GRID_SIZE:
                    d.set_pixel(col, row, shadow)

        # Claw hand
        arm_y = body_top + int(5 * scale)
        arm_x = sx - int(6 * scale)
        finger_len = int(6 * scale * (0.3 + hand_ext * 0.7))
        for f in range(5):
            angle = -0.8 + f * 0.3
            for seg in range(finger_len):
                fx = arm_x - seg
                fy = arm_y + int(seg * math.tan(angle))
                if 0 <= fx < GRID_SIZE and 0 <= fy < GRID_SIZE:
                    d.set_pixel(fx, fy, shadow)
                    if fy + 1 < GRID_SIZE and seg < finger_len - 2:
                        d.set_pixel(fx, fy + 1, shadow)
        # Arm to body
        for seg in range(int(6 * scale)):
            ax = sx - seg
            ay = arm_y + seg // 3
            if 0 <= ax < GRID_SIZE and 0 <= ay < GRID_SIZE:
                d.set_pixel(ax, ay, shadow)
                if ay + 1 < GRID_SIZE:
                    d.set_pixel(ax, ay + 1, shadow)

        # Title text - warm amber, candle-tinted
        tp = 0.6 + 0.4 * math.sin(t * 1.0) * flicker
        d.draw_text_small(WONDER_X, WONDER_Y, "WONDER",
                          (int(220 * tp), int(160 * tp), int(50 * tp)))
        tp2 = 0.6 + 0.4 * math.sin(t * 1.0 + 0.6) * flicker
        d.draw_text_small(CABINET_X, CABINET_Y, "CABINET",
                          (int(200 * tp2), int(140 * tp2), int(40 * tp2)))


# =========================================================================
# WonderJaws - Spielberg's iconic poster
# =========================================================================

class WonderJaws(Visual):
    name = "WONDER JAWS"
    description = "Shark from below"
    category = "titles"

    _SURFACE_Y = 14

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self._bubbles = [self._new_bubble() for _ in range(12)]

    def _new_bubble(self):
        return {
            'x': random.uniform(4, GRID_SIZE - 4),
            'y': random.uniform(self._SURFACE_Y + 5, GRID_SIZE),
            'speed': random.uniform(6, 14),
        }

    def update(self, dt: float):
        self.time += dt
        for b in self._bubbles:
            b['y'] -= b['speed'] * dt
            if b['y'] < self._SURFACE_Y:
                b.update(self._new_bubble())
                b['y'] = GRID_SIZE

    def draw(self):
        d = self.display
        d.clear()
        t = self.time
        cx = GRID_SIZE // 2
        sy = self._SURFACE_Y

        # Night sky
        for y in range(sy):
            grad = y / sy
            c = (int(8 + 10 * grad), int(8 + 12 * grad), int(25 + 20 * grad))
            for x in range(GRID_SIZE):
                d.set_pixel(x, y, c)

        # Moon
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                if dx * dx + dy * dy <= 9:
                    px, py = 50 + dx, 4 + dy
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        d.set_pixel(px, py, (190, 190, 170))

        # Underwater
        for y in range(sy, GRID_SIZE):
            depth = (y - sy) / (GRID_SIZE - sy)
            base_r = int(15 * (1 - depth))
            base_g = int(50 + 10 * (1 - depth))
            base_b = int(100 + 30 * (1 - depth))
            for x in range(GRID_SIZE):
                # Caustic rays
                ray = math.sin((x - cx) * 0.3 + t * 0.5 + y * 0.1)
                ray += math.sin((x - cx) * 0.15 - t * 0.3 + y * 0.15)
                ri = max(0.0, ray * 0.5) * (1.0 - depth) * 0.25
                d.set_pixel(x, y, (min(255, int(base_r + ri * 60)),
                                   min(255, int(base_g + ri * 100)),
                                   min(255, int(base_b + ri * 50))))

        # Surface wave
        for x in range(GRID_SIZE):
            wy = sy + int(math.sin(x * 0.3 + t * 2.0) * 1.2)
            if 0 <= wy < GRID_SIZE:
                d.set_pixel(x, wy, (50, 90, 150))

        # Swimmer silhouette
        swim_x = cx + int(math.sin(t * 0.5) * 3)
        for dx in range(-4, 5):
            px = swim_x + dx
            if 0 <= px < GRID_SIZE and 0 <= sy - 1 < GRID_SIZE:
                d.set_pixel(px, sy - 1, (160, 130, 100))
        # Kicking legs
        kick = int(math.sin(t * 4.0) * 2)
        for i in range(2):
            lx = swim_x - 4 - i
            ly = sy + abs(kick)
            if 0 <= lx < GRID_SIZE and 0 <= ly < GRID_SIZE:
                d.set_pixel(lx, ly, (140, 110, 80))

        # Shark - oscillates up/down, viewed from below (poster angle)
        # Pixel-art silhouette: each row is (y_offset, x_min, x_max) from snout
        # Nose-up, open jaws, pectoral fins out, forked tail
        SHARK_DARK = (15, 18, 28)      # body silhouette
        SHARK_BELLY = (45, 50, 60)     # lighter underbelly
        SHARK_MOUTH = (90, 20, 15)     # red mouth interior
        SHARK_TEETH = (220, 225, 230)  # teeth
        SHARK_EYE = (10, 10, 10)       # beady black eye

        # Silhouette rows: list of (half-width,) from snout tip downward
        # Row 0 = snout tip, progressing to tail
        #   snout → jaw → head → pectoral fins → body → caudal peduncle → tail
        body_profile = [
            1,           # 0  snout tip
            2,           # 1  snout
            3,           # 2  upper jaw
            4,           # 3  jaw hinge
            5,           # 4  head widens
            6,           # 5  head
            7,           # 6  gills / widest head
            7,           # 7  pectoral fin root
            6,           # 8  behind pectorals
            5,           # 9  torso
            5,           # 10 torso
            4,           # 11 abdomen
            4,           # 12 abdomen
            3,           # 13 taper
            3,           # 14 taper
            2,           # 15 caudal peduncle
            2,           # 16 peduncle
            1,           # 17 peduncle narrow
        ]
        body_len = len(body_profile)

        shark_cycle = 10.0
        st = t % shark_cycle
        if st < 6.0:
            progress = st / 6.0
            shark_y = int(GRID_SIZE - 2 - progress * 30)
        else:
            progress = (st - 6.0) / 4.0
            shark_y = int(GRID_SIZE - 32 + progress * 30)

        # Draw body silhouette
        for i, hw in enumerate(body_profile):
            row = shark_y + i
            if row < sy or row >= GRID_SIZE:
                continue
            # Belly is lighter in the center, darker at edges
            for dx in range(-hw, hw + 1):
                col = cx + dx
                if 0 <= col < GRID_SIZE:
                    edge = abs(dx) / max(1, hw)
                    if edge > 0.7:
                        d.set_pixel(col, row, SHARK_DARK)
                    else:
                        d.set_pixel(col, row, SHARK_BELLY)

        # Open mouth (V-shaped gape, rows 0-3)
        for i in range(4):
            row = shark_y + i
            if row < sy or row >= GRID_SIZE:
                continue
            # Mouth interior is narrower than head, creating jaw edges
            mouth_hw = max(0, i)  # widens downward
            for dx in range(-mouth_hw, mouth_hw + 1):
                col = cx + dx
                if 0 <= col < GRID_SIZE:
                    d.set_pixel(col, row, SHARK_MOUTH)

        # Teeth along upper jaw edge (row 0-1) and lower jaw (row 3)
        for row_off in [0, 1]:
            row = shark_y + row_off
            if row < sy or row >= GRID_SIZE:
                continue
            jaw_hw = body_profile[row_off]
            # Teeth at the outer edges of the jaw
            for dx in range(-jaw_hw, jaw_hw + 1):
                col = cx + dx
                if 0 <= col < GRID_SIZE:
                    # Alternating teeth pattern
                    if (dx + row_off) % 2 == 0:
                        d.set_pixel(col, row, SHARK_TEETH)
        # Lower teeth row
        row = shark_y + 3
        if sy <= row < GRID_SIZE:
            for dx in range(-3, 4):
                col = cx + dx
                if 0 <= col < GRID_SIZE and dx % 2 == 0:
                    d.set_pixel(col, row, SHARK_TEETH)

        # Eyes (row 5, set into the head sides)
        eye_row = shark_y + 5
        if sy <= eye_row < GRID_SIZE:
            for side in [-1, 1]:
                ex = cx + side * 5
                if 0 <= ex < GRID_SIZE:
                    d.set_pixel(ex, eye_row, SHARK_EYE)

        # Pectoral fins (extend out from rows 7-10)
        for i in range(4):
            row = shark_y + 7 + i
            if row < sy or row >= GRID_SIZE:
                continue
            # Fins extend outward, wider near root, tapering
            fin_start = body_profile[7 + i] + 1
            fin_len = max(0, 5 - i)
            for side in [-1, 1]:
                for f in range(fin_len):
                    col = cx + side * (fin_start + f)
                    if 0 <= col < GRID_SIZE:
                        d.set_pixel(col, row, SHARK_DARK)

        # Tail fin (forked caudal fin, two lobes angling outward)
        tail_start = shark_y + body_len
        for i in range(5):
            row = tail_start + i
            if row < sy or row >= GRID_SIZE:
                continue
            # Two lobes spread outward
            spread = 2 + i
            for side in [-1, 1]:
                for w in range(2):
                    col = cx + side * (spread - w)
                    if 0 <= col < GRID_SIZE:
                        d.set_pixel(col, row, SHARK_DARK)
            # Thin connector in middle for first couple rows
            if i < 2:
                d.set_pixel(cx, row, SHARK_DARK)

        # Bubbles
        for b in self._bubbles:
            bx, by = int(b['x']), int(b['y'])
            if 0 <= bx < GRID_SIZE and sy <= by < GRID_SIZE:
                d.set_pixel(bx, by, (90, 150, 210))

        # Title text - ocean blue/white
        tp = 0.65 + 0.35 * math.sin(t * 1.3)
        d.draw_text_small(WONDER_X, WONDER_Y, "WONDER",
                          (int(180 * tp), int(210 * tp), int(255 * tp)))
        tp2 = 0.65 + 0.35 * math.sin(t * 1.3 + 0.5)
        d.draw_text_small(CABINET_X, CABINET_Y, "CABINET",
                          (int(150 * tp2), int(190 * tp2), int(255 * tp2)))


# =========================================================================
# WonderShining - Kubrick's Overlook corridor
# =========================================================================

class WonderShining(Visual):
    name = "WONDER SHINING"
    description = "The Overlook corridor"
    category = "titles"

    _VP_Y = 20  # Vanishing point Y

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self._flash_timer = 0.0

    def handle_input(self, input_state) -> bool:
        if input_state.up:
            self._flash_timer = 0.5
            return True
        return False

    def update(self, dt: float):
        self.time += dt
        if self._flash_timer > 0:
            self._flash_timer -= dt

    def draw(self):
        d = self.display
        d.clear()
        t = self.time
        cx = GRID_SIZE // 2
        vpy = self._VP_Y

        # Light flicker
        flicker = 0.86 + 0.14 * math.sin(t * 8.0 + math.sin(t * 3.0) * 2.0)

        # Easter egg: REDRUM flash (joystick up)
        if self._flash_timer > 0:
            alpha = min(1.0, self._flash_timer / 0.15)
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    d.set_pixel(x, y, (int(15 * alpha), int(20 * alpha),
                                       int(45 * alpha)))
            rc = (int(220 * alpha), int(20 * alpha), int(20 * alpha))
            d.draw_text_small(_center_x("REDRUM"), 18, "REDRUM", rc)
            mc = (int(140 * alpha), int(10 * alpha), int(10 * alpha))
            d.draw_text_small(_center_x("MURDER"), 28, "MURDER", mc)
            d.draw_text_small(WONDER_X, 44, "WONDER",
                              (int(180 * alpha), int(60 * alpha), int(60 * alpha)))
            d.draw_text_small(CABINET_X, 52, "CABINET",
                              (int(150 * alpha), int(50 * alpha), int(50 * alpha)))
            return

        # One-point perspective corridor
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                dx = abs(x - cx)
                wall_hw = 8 + abs(y - vpy) * 0.8

                if y < vpy:
                    # Ceiling
                    if dx < wall_hw:
                        depth = max(1, vpy - y)
                        df = min(1.0, depth / 30.0)
                        base = (int((160 + 20 * df) * flicker),
                                int((150 + 20 * df) * flicker),
                                int((130 + 20 * df) * flicker))
                        # Panel pattern
                        panel = ((x + int(t * 2)) // 8) % 2
                        if panel:
                            base = (max(0, base[0] - 12), max(0, base[1] - 12),
                                    max(0, base[2] - 12))
                        d.set_pixel(x, y, base)
                    else:
                        # Upper wall
                        df = min(1.0, (vpy - y) / 30.0)
                        c = (int((100 + 50 * df) * flicker),
                             int((60 + 40 * df) * flicker),
                             int((30 + 20 * df) * flicker))
                        d.set_pixel(x, y, c)

                elif y == vpy:
                    # Back wall / door
                    if dx < 5:
                        d.set_pixel(x, y, (int(55 * flicker), int(90 * flicker),
                                           int(130 * flicker)))
                    else:
                        d.set_pixel(x, y, (int(90 * flicker), int(55 * flicker),
                                           int(28 * flicker)))
                else:
                    # Floor
                    if dx < wall_hw:
                        df = min(1.0, (y - vpy) / 30.0)
                        # Hicks hexagonal carpet
                        fx = x + t * 3
                        fy = (y - vpy) * 2.0 / max(1, df * 4 + 1)
                        hx = int(fx * 0.4) % 3
                        hy = int(fy * 0.4 + (int(fx * 0.4) % 2) * 0.5) % 3
                        if (hx + hy) % 2 == 0:
                            c = (160, 50, 20)  # Red
                        else:
                            c = (200, 120, 40)  # Orange
                        dark = 1.0 - df * 0.6
                        c = (int(c[0] * dark * flicker), int(c[1] * dark * flicker),
                             int(c[2] * dark * flicker))
                        d.set_pixel(x, y, c)
                    else:
                        # Lower wall
                        df = min(1.0, (y - vpy) / 30.0)
                        c = (int((100 + 50 * df) * flicker),
                             int((60 + 40 * df) * flicker),
                             int((30 + 20 * df) * flicker))
                        d.set_pixel(x, y, c)

        # Twin silhouettes at vanishing point
        for twin_off in [-4, 4]:
            tx = cx + twin_off
            for dy in range(10):
                row = vpy - 5 + dy
                if 0 <= row < GRID_SIZE:
                    rel = dy / 10.0
                    w = 1 if rel < 0.25 else (0 if rel < 0.3 else 1 + int(rel * 2))
                    for ddx in range(-w, w + 1):
                        col = tx + ddx
                        if 0 <= col < GRID_SIZE:
                            c = (35, 50, 110) if rel > 0.3 else (28, 22, 18)
                            d.set_pixel(col, row, c)

        # Ceiling lights with glow
        for lx in [cx - 10, cx, cx + 10]:
            ly = vpy - 14
            if 0 <= ly < GRID_SIZE and 0 <= lx < GRID_SIZE:
                bv = int(210 * flicker)
                d.set_pixel(lx, ly, (bv, bv, min(255, bv + 20)))
                for cdy in range(1, 3):
                    for cdx in range(-cdy, cdy + 1):
                        px, py = lx + cdx, ly + cdy
                        if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                            iv = max(0, bv - cdy * 60 - abs(cdx) * 40)
                            if iv > 0:
                                ex = d.get_pixel(px, py)
                                d.set_pixel(px, py, (min(255, ex[0] + iv // 3),
                                                     min(255, ex[1] + iv // 3),
                                                     min(255, ex[2] + iv // 4)))

        # Title text - eerie warm white
        tp = 0.65 + 0.35 * math.sin(t * 1.0) * flicker
        d.draw_text_small(WONDER_X, WONDER_Y + 20, "WONDER",
                          (int(240 * tp), int(200 * tp), int(140 * tp)))
        tp2 = 0.65 + 0.35 * math.sin(t * 1.0 + 0.5) * flicker
        d.draw_text_small(CABINET_X, CABINET_Y + 20, "CABINET",
                          (int(220 * tp2), int(180 * tp2), int(120 * tp2)))


# =========================================================================
# WonderET - E.T. moon bicycle silhouette
# =========================================================================

class WonderET(Visual):
    name = "WONDER ET"
    description = "Moon bicycle flight"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        # A few twinkling stars
        self._stars = [(random.randint(0, GRID_SIZE - 1),
                        random.randint(0, GRID_SIZE - 1),
                        random.uniform(0, math.pi * 2),
                        random.uniform(0.8, 2.0))
                       for _ in range(25)]

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        d = self.display
        d.clear()
        t = self.time

        # Dark blue night sky
        for y in range(GRID_SIZE):
            grad = y / GRID_SIZE
            for x in range(GRID_SIZE):
                d.set_pixel(x, y, (int(5 + 8 * grad), int(5 + 10 * grad),
                                   int(20 + 25 * grad)))

        # Stars
        for sx, sy, phase, spd in self._stars:
            bri = int(80 + 60 * math.sin(t * spd + phase))
            d.set_pixel(sx, sy, (bri, bri, bri + 20))

        # Large moon
        moon_cx, moon_cy, moon_r = 40, 18, 14
        for dy in range(-moon_r, moon_r + 1):
            for dx in range(-moon_r, moon_r + 1):
                dist = math.sqrt(dx * dx + dy * dy)
                if dist <= moon_r:
                    # Moon surface with craters
                    edge = dist / moon_r
                    base = int(220 - edge * 40)
                    # Crater shadows
                    crater1 = math.sqrt((dx + 3) ** 2 + (dy - 2) ** 2)
                    crater2 = math.sqrt((dx - 5) ** 2 + (dy + 4) ** 2)
                    crater3 = math.sqrt((dx + 1) ** 2 + (dy + 6) ** 2)
                    if crater1 < 3:
                        base -= 25
                    if crater2 < 4:
                        base -= 20
                    if crater3 < 2.5:
                        base -= 30
                    base = max(100, base)
                    px, py = moon_cx + dx, moon_cy + dy
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        d.set_pixel(px, py, (base, base - 10, base - 30))

        # Bicycle + E.T. silhouette flying across the moon
        cycle = 14.0
        ct = t % cycle
        # Arc path across the moon
        bike_x = int(-10 + ct / cycle * 80)
        bike_y = int(moon_cy - 4 + 12 * math.sin(ct / cycle * math.pi))
        bike_y = min(bike_y, moon_cy + 2)

        # Bicycle frame (tiny pixel art)
        sil = (5, 5, 12)
        # Wheels (2px circles)
        for wx_off in [-3, 3]:
            wx = bike_x + wx_off
            wy = bike_y + 3
            for ddy in [-1, 0, 1]:
                for ddx in [-1, 0, 1]:
                    if abs(ddx) + abs(ddy) <= 1:
                        px, py = wx + ddx, wy + ddy
                        if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                            d.set_pixel(px, py, sil)
        # Frame connecting wheels
        for fx in range(bike_x - 2, bike_x + 3):
            if 0 <= fx < GRID_SIZE and 0 <= bike_y + 2 < GRID_SIZE:
                d.set_pixel(fx, bike_y + 2, sil)
        # Rider body
        for ry in range(bike_y - 1, bike_y + 2):
            if 0 <= bike_x < GRID_SIZE and 0 <= ry < GRID_SIZE:
                d.set_pixel(bike_x, ry, sil)
        # E.T. in basket (front, bigger head)
        et_x = bike_x + 3
        for ey in range(bike_y - 2, bike_y + 1):
            if 0 <= et_x < GRID_SIZE and 0 <= ey < GRID_SIZE:
                d.set_pixel(et_x, ey, sil)
        # E.T. head (larger)
        for ddx in [-1, 0, 1]:
            px = et_x + ddx
            if 0 <= px < GRID_SIZE and 0 <= bike_y - 3 < GRID_SIZE:
                d.set_pixel(px, bike_y - 3, sil)
        # E.T. finger pointing (glowing!)
        finger_x = et_x + 2
        finger_y = bike_y - 1
        if 0 <= finger_x < GRID_SIZE and 0 <= finger_y < GRID_SIZE:
            glow = 0.6 + 0.4 * math.sin(t * 3.0)
            d.set_pixel(finger_x, finger_y,
                        (int(200 * glow), int(180 * glow), int(255 * glow)))

        # Title text - warm moonlit
        tp = 0.6 + 0.4 * math.sin(t * 1.2)
        d.draw_text_small(WONDER_X, WONDER_Y + 20, "WONDER",
                          (int(200 * tp), int(190 * tp), int(255 * tp)))
        tp2 = 0.6 + 0.4 * math.sin(t * 1.2 + 0.5)
        d.draw_text_small(CABINET_X, CABINET_Y + 20, "CABINET",
                          (int(170 * tp2), int(160 * tp2), int(230 * tp2)))


# =========================================================================
# WonderAlien - Alien egg with green glow
# =========================================================================

class WonderAlien(Visual):
    name = "WONDER ALIEN"
    description = "In space no one can hear"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self._mist = [(random.uniform(0, GRID_SIZE), random.uniform(50, 63),
                        random.uniform(0.5, 2.0), random.uniform(0.3, 1.0))
                       for _ in range(20)]

    def update(self, dt: float):
        self.time += dt
        for i, (mx, my, ms, ml) in enumerate(self._mist):
            my -= ms * dt * 0.3
            mx += math.sin(self.time + i) * dt * 0.5
            if my < 40:
                my = random.uniform(55, 63)
                mx = random.uniform(0, GRID_SIZE)
            self._mist[i] = (mx, my, ms, ml)

    def draw(self):
        d = self.display
        d.clear()
        t = self.time

        # Pure black space
        cx = GRID_SIZE // 2
        egg_cx, egg_cy = cx, 34
        egg_w, egg_h = 8, 14

        # Green underglow (from the crack)
        crack_open = (math.sin(t * 0.3) * 0.5 + 0.5)  # 0-1 pulse
        glow_intensity = 0.3 + crack_open * 0.7

        # Floor glow
        for y in range(45, GRID_SIZE):
            for x in range(GRID_SIZE):
                dx = abs(x - egg_cx)
                dist = dx + (y - 45) * 0.5
                g = max(0, int(40 * glow_intensity * max(0, 1.0 - dist / 25.0)))
                if g > 0:
                    d.set_pixel(x, y, (0, g, g // 4))

        # Egg shape (ovoid)
        for y in range(egg_cy - egg_h, egg_cy + egg_h + 1):
            ny = (y - egg_cy) / egg_h
            # Egg is wider at bottom, narrower at top
            width_factor = 1.0 - ny * 0.3  # narrower at top
            w = egg_w * math.sqrt(max(0, 1.0 - ny * ny)) * width_factor
            w = int(w)
            for dx in range(-w, w + 1):
                px = egg_cx + dx
                if 0 <= px < GRID_SIZE and 0 <= y < GRID_SIZE:
                    edge = abs(dx) / max(1, w)
                    # Leathery texture
                    tex = math.sin(y * 1.5 + dx * 0.8) * 0.1
                    base = 0.35 + tex - edge * 0.15
                    r = int(90 * base)
                    g = int(80 * base)
                    b = int(60 * base)
                    d.set_pixel(px, y, (r, g, b))

        # Crack at top of egg (opening petals)
        petal_open = crack_open * 6
        for i in range(4):
            angle = i * math.pi / 2 + t * 0.1
            for seg in range(int(petal_open)):
                px = int(egg_cx + math.cos(angle) * (seg + 1) * 0.8)
                py = int(egg_cy - egg_h + seg)
                if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                    d.set_pixel(px, py, (70, 65, 45))

        # Green glow from crack
        for dy in range(-3, 1):
            for dx in range(-3, 4):
                px = egg_cx + dx
                py = egg_cy - egg_h + dy
                dist = math.sqrt(dx * dx + dy * dy)
                if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE and dist < 4:
                    gi = max(0, int(120 * glow_intensity * (1.0 - dist / 4.0)))
                    ex = d.get_pixel(px, py)
                    d.set_pixel(px, py, (ex[0], min(255, ex[1] + gi),
                                         ex[2] + gi // 3))

        # Mist particles
        for mx, my, ms, ml in self._mist:
            ix, iy = int(mx), int(my)
            if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                g = int(25 * glow_intensity * ml)
                d.set_pixel(ix, iy, (0, g, g // 3))

        # Horizontal line (the iconic crack of light)
        line_y = egg_cy - egg_h - 2
        if 0 <= line_y < GRID_SIZE:
            hw = int(12 * glow_intensity)
            for dx in range(-hw, hw + 1):
                px = egg_cx + dx
                if 0 <= px < GRID_SIZE:
                    fall = abs(dx) / max(1, hw)
                    gi = int(100 * glow_intensity * (1.0 - fall))
                    d.set_pixel(px, line_y, (0, gi, gi // 3))

        # Title text - acid green
        tp = 0.5 + 0.5 * glow_intensity
        d.draw_text_small(WONDER_X, WONDER_Y, "WONDER",
                          (0, int(200 * tp), int(60 * tp)))
        d.draw_text_small(CABINET_X, CABINET_Y, "CABINET",
                          (0, int(170 * tp), int(50 * tp)))


# =========================================================================
# WonderExorcist - The iconic window silhouette
# =========================================================================

class WonderExorcist(Visual):
    name = "WONDER EXORCIST"
    description = "The power of light"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        d = self.display
        d.clear()
        t = self.time

        # Dark foggy night
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                fog = int(8 + 4 * math.sin(x * 0.1 + y * 0.15 + t * 0.3))
                d.set_pixel(x, y, (fog, fog, fog + 3))

        # House silhouette (dark block)
        house_x, house_y = 18, 12
        house_w, house_h = 28, 40
        for y in range(house_y, min(GRID_SIZE, house_y + house_h)):
            for x in range(house_x, house_x + house_w):
                if 0 <= x < GRID_SIZE:
                    d.set_pixel(x, y, (3, 3, 5))

        # Roof peak
        peak_cx = house_x + house_w // 2
        for row in range(8):
            y = house_y - row
            hw = house_w // 2 - row * 2
            if hw < 1:
                break
            for dx in range(-hw, hw + 1):
                px = peak_cx + dx
                if 0 <= px < GRID_SIZE and 0 <= y < GRID_SIZE:
                    d.set_pixel(px, y, (3, 3, 5))

        # Window (the iconic glowing rectangle, upper right of house)
        win_x, win_y = 34, 16
        win_w, win_h = 8, 12

        # Light beam from window (cone of light into fog)
        beam_intensity = 0.7 + 0.3 * math.sin(t * 0.5)
        for y in range(0, win_y + win_h):
            for x in range(win_x - 2, win_x + win_w + 2):
                # Distance from window
                dy = win_y - y
                if dy < 0:
                    continue
                dx = x - (win_x + win_w // 2)
                # Beam spreads upward
                spread = max(1, dy * 0.4)
                if abs(dx) < spread + win_w // 2:
                    fall = abs(dx) / (spread + win_w // 2)
                    fog_light = int(60 * beam_intensity * (1.0 - fall)
                                    * min(1.0, dy / 3.0))
                    if fog_light > 0 and 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                        ex = d.get_pixel(x, y)
                        d.set_pixel(x, y, (min(255, ex[0] + fog_light),
                                           min(255, ex[1] + fog_light),
                                           min(255, ex[2] + fog_light // 2)))

        # Window glow
        for y in range(win_y, win_y + win_h):
            for x in range(win_x, win_x + win_w):
                if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                    # Warm yellow light
                    d.set_pixel(x, y, (int(220 * beam_intensity),
                                       int(190 * beam_intensity),
                                       int(80 * beam_intensity)))

        # Window frame (cross)
        mid_x = win_x + win_w // 2
        mid_y = win_y + win_h // 2
        for y in range(win_y, win_y + win_h):
            if 0 <= mid_x < GRID_SIZE and 0 <= y < GRID_SIZE:
                d.set_pixel(mid_x, y, (3, 3, 5))
        for x in range(win_x, win_x + win_w):
            if 0 <= x < GRID_SIZE and 0 <= mid_y < GRID_SIZE:
                d.set_pixel(x, mid_y, (3, 3, 5))

        # Figure silhouette in front of house (hat, briefcase)
        fig_x = house_x + 4
        fig_top = 30
        # Hat brim
        for dx in range(-3, 4):
            px = fig_x + dx
            if 0 <= px < GRID_SIZE and 0 <= fig_top < GRID_SIZE:
                d.set_pixel(px, fig_top, (2, 2, 3))
        # Hat crown
        for dy in range(-3, 0):
            for dx in range(-2, 3):
                px, py = fig_x + dx, fig_top + dy
                if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                    d.set_pixel(px, py, (2, 2, 3))
        # Body
        for dy in range(1, 16):
            row = fig_top + dy
            if row >= GRID_SIZE:
                break
            w = 2 if dy < 8 else 3
            for dx in range(-w, w + 1):
                px = fig_x + dx
                if 0 <= px < GRID_SIZE:
                    d.set_pixel(px, row, (2, 2, 3))
        # Briefcase
        for dy in range(8, 12):
            for dx in range(3, 6):
                px, py = fig_x + dx, fig_top + dy
                if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                    d.set_pixel(px, py, (2, 2, 3))

        # Lamppost
        lamp_x = house_x - 3
        for y in range(8, 48):
            if 0 <= lamp_x < GRID_SIZE and 0 <= y < GRID_SIZE:
                d.set_pixel(lamp_x, y, (3, 3, 5))
        # Lamp head
        for dx in range(-1, 2):
            px = lamp_x + dx
            if 0 <= px < GRID_SIZE:
                d.set_pixel(px, 8, (3, 3, 5))
        # Lamp glow
        glow = int(120 * beam_intensity)
        if 0 <= lamp_x < GRID_SIZE:
            d.set_pixel(lamp_x, 9, (glow, glow, glow // 2))
            for ddx in [-1, 0, 1]:
                for ddy in [9, 10]:
                    px = lamp_x + ddx
                    if 0 <= px < GRID_SIZE and 0 <= ddy < GRID_SIZE:
                        g = glow // 3
                        ex = d.get_pixel(px, ddy)
                        d.set_pixel(px, ddy, (min(255, ex[0] + g),
                                              min(255, ex[1] + g),
                                              min(255, ex[2] + g // 2)))

        # Title text
        tp = 0.5 + 0.5 * beam_intensity
        d.draw_text_small(WONDER_X, WONDER_Y, "WONDER",
                          (int(220 * tp), int(190 * tp), int(80 * tp)))
        d.draw_text_small(CABINET_X, CABINET_Y, "CABINET",
                          (int(200 * tp), int(170 * tp), int(60 * tp)))


# =========================================================================
# WonderTerminator - Chrome skull with scanning red eye
# =========================================================================

class WonderTerminator(Visual):
    name = "WONDER TERMINATOR"
    description = "I'll be back"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        d = self.display
        d.clear()
        t = self.time
        cx, cy = GRID_SIZE // 2, 24

        # Dark background with subtle red ambient
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                d.set_pixel(x, y, (3, 0, 0))

        # Chrome skull (metallic grays)
        # Cranium (top dome)
        for dy in range(-12, 13):
            for dx in range(-10, 11):
                # Skull shape: wider at temples, narrow at chin
                ny = dy / 12.0
                if ny < 0:
                    # Upper cranium - dome
                    max_w = 10 * math.sqrt(max(0, 1 - ny * ny))
                elif ny < 0.5:
                    # Cheekbones - widest
                    max_w = 10 - ny * 4
                else:
                    # Jaw narrows
                    max_w = 10 - ny * 12
                    max_w = max(2, max_w)

                if abs(dx) > max_w:
                    continue

                px, py = cx + dx, cy + dy
                if not (0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE):
                    continue

                edge = abs(dx) / max(1, max_w)
                # Chrome: bright highlights, dark edges
                highlight = math.sin(dx * 0.5 + dy * 0.3 + t * 0.5) * 0.15
                base = 0.5 + highlight - edge * 0.3
                # Specular highlight on forehead
                spec_dist = math.sqrt((dx - 2) ** 2 + (dy + 6) ** 2)
                spec = max(0, 1.0 - spec_dist / 5.0) * 0.4
                base += spec
                base = max(0.15, min(1.0, base))

                r = int(160 * base)
                g = int(165 * base)
                b = int(175 * base)
                d.set_pixel(px, py, (r, g, b))

        # Eye sockets (dark recesses)
        for side in [-1, 1]:
            eye_cx = cx + side * 4
            eye_cy = cy - 2
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist <= 2.5:
                        px, py = eye_cx + dx, eye_cy + dy
                        if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                            d.set_pixel(px, py, (10, 0, 0))

        # Red eye (left socket has the iconic red glow)
        eye_x = cx - 4
        eye_y = cy - 2
        # Scanning: eye pulses and occasionally sweeps
        pulse = 0.6 + 0.4 * math.sin(t * 2.0)
        scan_x = int(math.sin(t * 0.7) * 1.5)
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                dist = math.sqrt(dx * dx + dy * dy)
                if dist <= 1.5:
                    px, py = eye_x + scan_x + dx, eye_y + dy
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        intensity = (1.0 - dist / 1.5) * pulse
                        d.set_pixel(px, py, (int(255 * intensity),
                                             int(20 * intensity), 0))

        # Eye glow bleed
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                dist = math.sqrt(dx * dx + dy * dy)
                if 1.5 < dist < 4:
                    px, py = eye_x + scan_x + dx, eye_y + dy
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        gi = int(30 * pulse * (1.0 - dist / 4.0))
                        if gi > 0:
                            ex = d.get_pixel(px, py)
                            d.set_pixel(px, py, (min(255, ex[0] + gi),
                                                 ex[1], ex[2]))

        # Nose cavity
        for dy in range(0, 4):
            for dx in range(-1, 2):
                px, py = cx + dx, cy + 2 + dy
                if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                    if abs(dx) <= 1 - dy // 3:
                        d.set_pixel(px, py, (15, 5, 5))

        # Teeth
        teeth_y = cy + 7
        for row in range(3):
            ry = teeth_y + row
            if ry >= GRID_SIZE:
                break
            jaw_w = 6 - row
            for dx in range(-jaw_w, jaw_w + 1):
                px = cx + dx
                if 0 <= px < GRID_SIZE and 0 <= ry < GRID_SIZE:
                    if dx % 2 == 0:
                        d.set_pixel(px, ry, (180, 185, 190))
                    else:
                        d.set_pixel(px, ry, (20, 10, 10))

        # Horizontal scan line sweeping across
        scan_y = int(cy - 12 + ((t * 8) % 28))
        if 0 <= scan_y < GRID_SIZE:
            for x in range(GRID_SIZE):
                ex = d.get_pixel(x, scan_y)
                d.set_pixel(x, scan_y, (min(255, ex[0] + 15),
                                         min(255, ex[1] + 5), ex[2]))

        # Title text - chrome/red
        tp = 0.6 + 0.4 * pulse
        d.draw_text_small(WONDER_X, WONDER_Y + 20, "WONDER",
                          (int(220 * tp), int(50 * tp), int(30 * tp)))
        tp2 = 0.6 + 0.4 * math.sin(t * 2.0 + 0.5)
        d.draw_text_small(CABINET_X, CABINET_Y + 20, "CABINET",
                          (int(200 * tp2), int(40 * tp2), int(20 * tp2)))


# =========================================================================
# WonderGodzilla - City skyline with atomic breath
# =========================================================================

class WonderGodzilla(Visual):
    name = "WONDER GODZILLA"
    description = "King of the monsters"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)
        # Random city skyline heights
        rng = random.Random(99)
        self._buildings = []
        x = 0
        while x < GRID_SIZE:
            w = rng.randint(3, 7)
            h = rng.randint(12, 30)
            self._buildings.append((x, w, h))
            x += w + rng.randint(0, 1)

    def reset(self):
        self.time = 0.0
        self._breath_particles = []

    def update(self, dt: float):
        self.time += dt
        # Update breath particles
        for p in self._breath_particles:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['life'] -= dt
        self._breath_particles = [p for p in self._breath_particles if p['life'] > 0]

        # Spawn breath particles during breath phase
        # Jaw tip is at gz_x(44) - 6 = 38, jaw_y = head_top(14) + 5 = 19
        cycle = 8.0
        ct = self.time % cycle
        if 3.0 < ct < 6.0:
            mouth_x, mouth_y = 38, 19
            for _ in range(3):
                angle = math.pi + random.uniform(-0.4, 0.4)  # shoot left
                speed = random.uniform(15, 30)
                self._breath_particles.append({
                    'x': float(mouth_x),
                    'y': float(mouth_y),
                    'vx': math.cos(angle) * speed,
                    'vy': math.sin(angle) * speed,
                    'life': random.uniform(0.3, 0.8),
                })

    def draw(self):
        d = self.display
        d.clear()
        t = self.time

        # Dark stormy sky
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                cloud = math.sin(x * 0.15 + t * 0.3) * math.sin(y * 0.2 + t * 0.2)
                base = int(12 + cloud * 6)
                d.set_pixel(x, y, (base, base, base + 5))

        # City skyline
        for bx, bw, bh in self._buildings:
            top = GRID_SIZE - bh
            for y in range(top, GRID_SIZE):
                for x in range(bx, min(GRID_SIZE, bx + bw)):
                    # Windows
                    is_window = (x - bx) % 2 == 1 and (y - top) % 3 == 1
                    if is_window and y < GRID_SIZE - 2:
                        win_on = ((x * 7 + y * 13) % 5) > 1
                        if win_on:
                            d.set_pixel(x, y, (180, 160, 60))
                        else:
                            d.set_pixel(x, y, (25, 25, 35))
                    else:
                        d.set_pixel(x, y, (20, 20, 30))

        # Godzilla silhouette (right side, towering over buildings)
        gz_x = 44  # Center x
        gz_base = GRID_SIZE  # Feet at bottom

        # Body profile (from top of head down)
        sil = (8, 8, 12)
        # Head (dorsal ridge)
        head_top = gz_base - 50
        for dy in range(6):
            row = head_top + dy
            if 0 <= row < GRID_SIZE:
                hw = 2 + dy // 2
                for dx in range(-hw, hw + 1):
                    px = gz_x + dx
                    if 0 <= px < GRID_SIZE:
                        d.set_pixel(px, row, sil)
        # Jaw / snout extends forward
        jaw_y = head_top + 4
        for dx in range(-5, -1):
            px = gz_x + dx
            if 0 <= px < GRID_SIZE and 0 <= jaw_y < GRID_SIZE:
                d.set_pixel(px, jaw_y, sil)
            if 0 <= px < GRID_SIZE and 0 <= jaw_y + 1 < GRID_SIZE:
                d.set_pixel(px, jaw_y + 1, sil)

        # Neck and body
        for dy in range(6, 35):
            row = head_top + dy
            if row >= GRID_SIZE:
                break
            # Body widens from neck to torso
            if dy < 12:
                hw = 3 + dy // 2
            elif dy < 25:
                hw = 9
            else:
                hw = 9 - (dy - 25) // 3
            hw = max(2, hw)
            for dx in range(-hw, hw + 1):
                px = gz_x + dx
                if 0 <= px < GRID_SIZE:
                    d.set_pixel(px, row, sil)

        # Dorsal spines along back
        for i in range(5):
            spine_y = head_top + 2 + i * 5
            spine_x = gz_x + 4 + (2 - abs(i - 2))
            for sy in range(-2, 1):
                px, py = spine_x, spine_y + sy
                if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                    d.set_pixel(px, py, sil)

        # Arms (small T-Rex-like)
        arm_y = head_top + 14
        for i in range(3):
            px = gz_x - 7 - i
            py = arm_y + i
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                d.set_pixel(px, py, sil)

        # Tail (extending right and down)
        for i in range(12):
            tx = gz_x + 8 + i
            ty = head_top + 28 + i // 2
            if 0 <= tx < GRID_SIZE and 0 <= ty < GRID_SIZE:
                d.set_pixel(tx, ty, sil)
                if ty + 1 < GRID_SIZE:
                    d.set_pixel(tx, ty + 1, sil)

        # Eye
        eye_x, eye_y = gz_x - 2, head_top + 3
        if 0 <= eye_x < GRID_SIZE and 0 <= eye_y < GRID_SIZE:
            glow = 0.5 + 0.5 * math.sin(t * 2.0)
            d.set_pixel(eye_x, eye_y, (int(255 * glow), int(100 * glow), 0))

        # Atomic breath particles
        for p in self._breath_particles:
            px, py = int(p['x']), int(p['y'])
            frac = max(0, p['life'] / 0.8)
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                # Blue-white beam
                r = int(100 * frac)
                g = int(150 * frac)
                b = int(255 * frac)
                d.set_pixel(px, py, (r, g, b))
                # Glow neighbors
                for ddx, ddy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = px + ddx, py + ddy
                    if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                        ex = d.get_pixel(nx, ny)
                        d.set_pixel(nx, ny, (min(255, ex[0] + r // 4),
                                             min(255, ex[1] + g // 4),
                                             min(255, ex[2] + b // 4)))

        # Title text - radioactive blue
        tp = 0.6 + 0.4 * math.sin(t * 1.5)
        d.draw_text_small(WONDER_X, WONDER_Y, "WONDER",
                          (int(100 * tp), int(160 * tp), int(255 * tp)))
        tp2 = 0.6 + 0.4 * math.sin(t * 1.5 + 0.5)
        d.draw_text_small(CABINET_X, CABINET_Y, "CABINET",
                          (int(80 * tp2), int(140 * tp2), int(230 * tp2)))


# =========================================================================
# WonderBladeRunner - Neon rain cityscape
# =========================================================================

class WonderBladeRunner(Visual):
    name = "WONDER BLADE RUNNER"
    description = "Tears in rain"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)
        # Skyline
        rng = random.Random(2019)
        self._buildings = []
        x = 0
        while x < GRID_SIZE:
            w = rng.randint(2, 5)
            h = rng.randint(15, 45)
            self._buildings.append((x, w, h))
            x += w + rng.randint(0, 1)

    def reset(self):
        self.time = 0.0
        self._rain = [{'x': random.randint(0, GRID_SIZE - 1),
                        'y': random.uniform(-GRID_SIZE, GRID_SIZE),
                        'speed': random.uniform(40, 70),
                        'len': random.randint(2, 4)}
                       for _ in range(50)]
        self._neon_signs = [
            (random.randint(3, 58), random.randint(20, 50),
             random.choice([(255, 0, 80), (0, 200, 255), (255, 100, 0),
                            (200, 0, 255), (0, 255, 150)]),
             random.uniform(0, math.pi * 2))
            for _ in range(8)]

    def update(self, dt: float):
        self.time += dt
        for r in self._rain:
            r['y'] += r['speed'] * dt
            if r['y'] > GRID_SIZE + 5:
                r['y'] = random.uniform(-10, -1)
                r['x'] = random.randint(0, GRID_SIZE - 1)

    def draw(self):
        d = self.display
        d.clear()
        t = self.time

        # Dark sky with smog
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                smog = math.sin(x * 0.08 + t * 0.2) * math.sin(y * 0.1 - t * 0.1)
                base = int(8 + smog * 4)
                d.set_pixel(x, y, (base + 2, base, base + 5))

        # Buildings
        for bx, bw, bh in self._buildings:
            top = GRID_SIZE - bh
            for y in range(max(0, top), GRID_SIZE):
                for x in range(bx, min(GRID_SIZE, bx + bw)):
                    d.set_pixel(x, y, (12, 12, 18))

        # Neon signs on buildings
        for sx, sy, color, phase in self._neon_signs:
            flick = math.sin(t * 4 + phase)
            if flick > -0.3:  # Occasionally off
                brightness = 0.5 + 0.5 * flick
                c = (int(color[0] * brightness),
                     int(color[1] * brightness),
                     int(color[2] * brightness))
                if 0 <= sx < GRID_SIZE and 0 <= sy < GRID_SIZE:
                    d.set_pixel(sx, sy, c)
                    if sx + 1 < GRID_SIZE:
                        d.set_pixel(sx + 1, sy, c)
                # Glow on nearby building wall
                for ddy in [-1, 0, 1]:
                    for ddx in [-1, 0, 1]:
                        px, py = sx + ddx, sy + ddy
                        if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                            ex = d.get_pixel(px, py)
                            g = brightness * 0.2
                            d.set_pixel(px, py, (min(255, int(ex[0] + color[0] * g)),
                                                 min(255, int(ex[1] + color[1] * g)),
                                                 min(255, int(ex[2] + color[2] * g))))

        # Rain
        for r in self._rain:
            rx = r['x']
            for i in range(r['len']):
                ry = int(r['y']) - i
                if 0 <= rx < GRID_SIZE and 0 <= ry < GRID_SIZE:
                    bri = 60 - i * 15
                    ex = d.get_pixel(rx, ry)
                    d.set_pixel(rx, ry, (min(255, ex[0] + bri // 2),
                                         min(255, ex[1] + bri // 2),
                                         min(255, ex[2] + bri)))

        # Spinner lights (flying car) crossing occasionally
        spinner_cycle = 12.0
        sp_t = t % spinner_cycle
        if sp_t < 4.0:
            sp_x = int(sp_t / 4.0 * (GRID_SIZE + 20)) - 10
            sp_y = 8 + int(math.sin(sp_t * 2.0) * 3)
            for dx in range(-1, 2):
                px = sp_x + dx
                if 0 <= px < GRID_SIZE and 0 <= sp_y < GRID_SIZE:
                    d.set_pixel(px, sp_y, (200, 100, 30))
            # Tail lights
            if 0 <= sp_x - 2 < GRID_SIZE and 0 <= sp_y < GRID_SIZE:
                d.set_pixel(sp_x - 2, sp_y, (200, 30, 10))

        # Title text - neon pink/cyan
        tp = 0.6 + 0.4 * math.sin(t * 1.5)
        d.draw_text_small(WONDER_X, WONDER_Y, "WONDER",
                          (int(255 * tp), int(50 * tp), int(120 * tp)))
        tp2 = 0.6 + 0.4 * math.sin(t * 1.5 + 0.5)
        d.draw_text_small(CABINET_X, CABINET_Y, "CABINET",
                          (int(50 * tp2), int(200 * tp2), int(255 * tp2)))


# =========================================================================
# WonderCloseEncounters - Devil's Tower with UFO lights
# =========================================================================

class WonderCloseEncounters(Visual):
    name = "WONDER CLOSE ENCOUNTERS"
    description = "Devil's Tower lights"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)
        # Devil's Tower profile (flat-topped butte)
        rng = random.Random(1977)
        self._tower_profile = []
        for x in range(GRID_SIZE):
            dx = abs(x - GRID_SIZE // 2)
            if dx < 12:
                # Flat top
                h = 30 + rng.randint(-1, 1)
            elif dx < 18:
                # Steep sides with columnar texture
                h = 30 - (dx - 12) * 3 + rng.randint(-1, 1)
            else:
                # Ground level
                h = max(5, 8 - (dx - 18) + rng.randint(-1, 1))
            self._tower_profile.append(max(3, h))

    def reset(self):
        self.time = 0.0
        self._ufo_lights = [random.uniform(0, math.pi * 2) for _ in range(12)]

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        d = self.display
        d.clear()
        t = self.time
        cx = GRID_SIZE // 2

        # Night sky with stars
        rng = random.Random(42)
        for _ in range(30):
            sx = rng.randint(0, GRID_SIZE - 1)
            sy = rng.randint(0, 25)
            bri = int(50 + 40 * math.sin(t * rng.uniform(0.5, 2.0) + rng.random() * 6))
            d.set_pixel(sx, sy, (bri, bri, bri + 10))

        # Devil's Tower
        for x in range(GRID_SIZE):
            h = self._tower_profile[x]
            top = GRID_SIZE - h
            for y in range(max(0, top), GRID_SIZE):
                # Columnar basalt texture
                col_stripe = (x + (y // 4) % 2) % 3
                if y < top + 2:
                    # Top edge highlight
                    c = (70, 60, 45)
                elif col_stripe == 0:
                    c = (40, 35, 25)
                else:
                    c = (50, 45, 32)
                # Moonlight from right
                if x > cx:
                    c = (int(c[0] * 1.2), int(c[1] * 1.2), int(c[2] * 1.2))
                d.set_pixel(x, y, (min(255, c[0]), min(255, c[1]), min(255, c[2])))

        # UFO mothership (hovering above tower)
        ufo_y = 12 + int(math.sin(t * 0.5) * 2)
        # Ship body (elliptical)
        for dx in range(-14, 15):
            for dy in range(-2, 3):
                dist = math.sqrt((dx / 14.0) ** 2 + (dy / 2.0) ** 2)
                if dist <= 1.0:
                    px, py = cx + dx, ufo_y + dy
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        edge = dist
                        bri = int(80 * (1.0 - edge * 0.5))
                        d.set_pixel(px, py, (bri, bri, bri + 10))

        # Ring of colored lights around UFO
        for i, phase in enumerate(self._ufo_lights):
            angle = i / len(self._ufo_lights) * math.pi * 2 + t * 0.8
            lx = int(cx + 13 * math.cos(angle))
            ly = int(ufo_y + 2 * math.sin(angle))
            if 0 <= lx < GRID_SIZE and 0 <= ly < GRID_SIZE:
                pulse = 0.5 + 0.5 * math.sin(t * 3 + phase)
                hue = (i / len(self._ufo_lights) + t * 0.1) % 1.0
                color = _hue_to_rgb(hue)
                d.set_pixel(lx, ly, (int(color[0] * pulse),
                                     int(color[1] * pulse),
                                     int(color[2] * pulse)))

        # Light beams descending from UFO to tower
        beam_phase = math.sin(t * 0.4) * 0.5 + 0.5
        beam_count = int(3 + beam_phase * 4)
        for i in range(beam_count):
            bx = cx + int((i - beam_count / 2) * 3)
            for by in range(ufo_y + 3, GRID_SIZE - self._tower_profile[max(0, min(63, bx))]):
                if 0 <= bx < GRID_SIZE and 0 <= by < GRID_SIZE:
                    depth = (by - ufo_y) / 40.0
                    intensity = int(40 * beam_phase * (1.0 - depth * 0.5))
                    shimmer = math.sin(by * 0.5 + t * 5 + i) * 0.3 + 0.7
                    intensity = int(intensity * shimmer)
                    if intensity > 0:
                        ex = d.get_pixel(bx, by)
                        d.set_pixel(bx, by, (min(255, ex[0] + intensity),
                                             min(255, ex[1] + intensity),
                                             min(255, ex[2] + intensity // 2)))

        # Musical tone lights (the five-note sequence)
        note_cycle = 6.0
        nt = t % note_cycle
        notes = [(255, 50, 50), (255, 200, 50), (50, 255, 50),
                 (50, 150, 255), (255, 100, 255)]
        note_idx = min(4, int(nt / 1.2))
        if nt < 5.0:
            nc = notes[note_idx]
            tp = 0.3 + 0.7 * math.sin((nt - note_idx * 1.2) / 1.2 * math.pi)
            # Flash the bottom edge
            for x in range(GRID_SIZE):
                ex = d.get_pixel(x, GRID_SIZE - 1)
                d.set_pixel(x, GRID_SIZE - 1,
                            (min(255, int(ex[0] + nc[0] * tp * 0.15)),
                             min(255, int(ex[1] + nc[1] * tp * 0.15)),
                             min(255, int(ex[2] + nc[2] * tp * 0.15))))

        # Title text - warm white
        tp = 0.6 + 0.4 * math.sin(t * 1.0)
        d.draw_text_small(WONDER_X, WONDER_Y, "WONDER",
                          (int(240 * tp), int(220 * tp), int(180 * tp)))
        tp2 = 0.6 + 0.4 * math.sin(t * 1.0 + 0.5)
        d.draw_text_small(CABINET_X, CABINET_Y, "CABINET",
                          (int(220 * tp2), int(200 * tp2), int(160 * tp2)))


# =========================================================================
# WonderTron - Light cycle trails on perspective grid
# =========================================================================

class WonderTron(Visual):
    name = "WONDER TRON"
    description = "Light cycle grid"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        # Light cycles: each has position, direction, color, trail
        self._cycles = [
            {'x': 10.0, 'y': 40.0, 'dx': 1, 'dy': 0,
             'color': (0, 200, 255), 'trail': [], 'turn_timer': 0},
            {'x': 54.0, 'y': 50.0, 'dx': -1, 'dy': 0,
             'color': (255, 100, 0), 'trail': [], 'turn_timer': 0},
        ]

    def update(self, dt: float):
        self.time += dt
        speed = 20.0
        for c in self._cycles:
            c['trail'].append((int(c['x']), int(c['y'])))
            if len(c['trail']) > 80:
                c['trail'].pop(0)
            c['x'] += c['dx'] * speed * dt
            c['y'] += c['dy'] * speed * dt
            c['turn_timer'] -= dt
            # Random turns or boundary avoidance
            if (c['turn_timer'] <= 0 or
                    c['x'] < 2 or c['x'] > 61 or c['y'] < 20 or c['y'] > 61):
                c['turn_timer'] = random.uniform(0.5, 2.0)
                if c['dx'] != 0:
                    c['dx'] = 0
                    c['dy'] = random.choice([-1, 1])
                    if c['y'] < 25:
                        c['dy'] = 1
                    elif c['y'] > 58:
                        c['dy'] = -1
                else:
                    c['dy'] = 0
                    c['dx'] = random.choice([-1, 1])
                    if c['x'] < 5:
                        c['dx'] = 1
                    elif c['x'] > 58:
                        c['dx'] = -1
            # Wrap
            c['x'] = max(1, min(62, c['x']))
            c['y'] = max(18, min(62, c['y']))

    def draw(self):
        d = self.display
        d.clear()
        t = self.time

        # Dark background
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                d.set_pixel(x, y, (0, 2, 8))

        # Grid lines (scrolling for motion feel)
        grid_off = (t * 5) % 8
        # Horizontal grid
        for gy in range(GRID_SIZE):
            if (gy + int(grid_off)) % 8 == 0 and gy > 16:
                for x in range(GRID_SIZE):
                    d.set_pixel(x, gy, (0, 20, 40))
        # Vertical grid
        for gx in range(GRID_SIZE):
            if gx % 8 == 0:
                for y in range(17, GRID_SIZE):
                    ex = d.get_pixel(gx, y)
                    d.set_pixel(gx, y, (max(ex[0], 0), max(ex[1], 20),
                                        max(ex[2], 40)))

        # Light cycle trails
        for c in self._cycles:
            color = c['color']
            trail = c['trail']
            for i, (tx, ty) in enumerate(trail):
                frac = i / max(1, len(trail))
                fade = frac * 0.8
                tc = (int(color[0] * fade), int(color[1] * fade),
                      int(color[2] * fade))
                if 0 <= tx < GRID_SIZE and 0 <= ty < GRID_SIZE:
                    d.set_pixel(tx, ty, tc)

            # Cycle head (bright)
            hx, hy = int(c['x']), int(c['y'])
            if 0 <= hx < GRID_SIZE and 0 <= hy < GRID_SIZE:
                d.set_pixel(hx, hy, (min(255, color[0] + 55),
                                     min(255, color[1] + 55),
                                     min(255, color[2] + 55)))
                # Glow
                for ddx, ddy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    px, py = hx + ddx, hy + ddy
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        d.set_pixel(px, py, (color[0] // 2, color[1] // 2,
                                             color[2] // 2))

        # Title text - cyan neon
        tp = 0.6 + 0.4 * math.sin(t * 2.0)
        d.draw_text_small(WONDER_X, WONDER_Y - 2, "WONDER",
                          (int(100 * tp), int(220 * tp), int(255 * tp)))
        tp2 = 0.6 + 0.4 * math.sin(t * 2.0 + 0.5)
        d.draw_text_small(CABINET_X, CABINET_Y - 2, "CABINET",
                          (int(80 * tp2), int(200 * tp2), int(255 * tp2)))


# =========================================================================
# WonderJurassicPark - Water ripple in the cup
# =========================================================================

class WonderJurassicPark(Visual):
    name = "WONDER JURASSIC PARK"
    description = "Water ripple impact"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        d = self.display
        d.clear()
        t = self.time
        cx, cy = GRID_SIZE // 2, GRID_SIZE // 2

        # Dark interior (dashboard of the car)
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                d.set_pixel(x, y, (12, 10, 8))

        # Cup of water (viewed from above - circular)
        cup_cx, cup_cy = cx, cy - 2
        cup_r = 16

        for dy in range(-cup_r - 1, cup_r + 2):
            for dx in range(-cup_r - 1, cup_r + 2):
                dist = math.sqrt(dx * dx + dy * dy)
                px, py = cup_cx + dx, cup_cy + dy

                if not (0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE):
                    continue

                if cup_r - 1 < dist <= cup_r + 1:
                    # Cup rim (glass edge)
                    rim_highlight = 0.6 + 0.4 * math.cos(math.atan2(dy, dx) - 0.5)
                    d.set_pixel(px, py, (int(180 * rim_highlight),
                                         int(190 * rim_highlight),
                                         int(200 * rim_highlight)))
                elif dist < cup_r - 1:
                    # Water surface
                    # Concentric ripples from T-Rex footsteps
                    # Footstep rhythm: thud every ~2.5 seconds
                    thud_period = 2.5
                    time_since_thud = t % thud_period
                    ripple_speed = 12.0

                    # Multiple ripple rings expanding from center
                    ripple_dist = time_since_thud * ripple_speed
                    ripple1 = math.sin((dist - ripple_dist) * 1.5) * \
                              max(0, 1.0 - time_since_thud / thud_period)
                    # Previous thud's ripple (still fading)
                    prev_dist = (time_since_thud + thud_period) * ripple_speed
                    ripple2 = math.sin((dist - prev_dist) * 1.5) * \
                              max(0, -time_since_thud / thud_period + 0.3)

                    ripple = (ripple1 + ripple2) * 0.5

                    # Water color
                    base_r = 60
                    base_g = 80
                    base_b = 120
                    # Ripple creates light/dark bands
                    shift = int(ripple * 35)
                    # Highlight on crests
                    highlight = max(0, ripple) * 25
                    d.set_pixel(px, py, (min(255, base_r + shift + int(highlight)),
                                         min(255, base_g + shift + int(highlight)),
                                         min(255, base_b + shift)))

        # Dashboard elements around the cup
        # Rearview mirror at top
        for x in range(cx - 8, cx + 9):
            for y in range(3, 7):
                if 0 <= x < GRID_SIZE:
                    d.set_pixel(x, y, (25, 22, 18))
        # Mirror reflection (green jungle)
        for x in range(cx - 6, cx + 7):
            for y in range(4, 6):
                if 0 <= x < GRID_SIZE:
                    jitter = int(math.sin(x * 0.5 + t) * 10)
                    d.set_pixel(x, y, (15 + jitter, 40 + jitter, 10))

        # Title text - amber/jungle
        tp = 0.6 + 0.4 * math.sin(t * 1.0)
        d.draw_text_small(WONDER_X, WONDER_Y + 22, "WONDER",
                          (int(220 * tp), int(180 * tp), int(50 * tp)))
        tp2 = 0.6 + 0.4 * math.sin(t * 1.0 + 0.5)
        d.draw_text_small(CABINET_X, CABINET_Y + 22, "CABINET",
                          (int(200 * tp2), int(160 * tp2), int(40 * tp2)))


# =========================================================================
# WonderIndiana - Rolling boulder in tunnel
# =========================================================================

class WonderIndiana(Visual):
    name = "WONDER INDIANA"
    description = "Rolling boulder chase"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self._dust = []

    def update(self, dt: float):
        self.time += dt
        # Update dust
        for p in self._dust:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['life'] -= dt
        self._dust = [p for p in self._dust if p['life'] > 0]
        # Spawn dust from boulder
        if random.random() < 0.4:
            boulder_x = 45 + int(math.sin(self.time * 0.3) * 3)
            self._dust.append({
                'x': float(boulder_x + random.randint(-8, 8)),
                'y': float(random.randint(25, 55)),
                'vx': random.uniform(-10, -3),
                'vy': random.uniform(-5, 5),
                'life': random.uniform(0.3, 0.8),
            })

    def draw(self):
        d = self.display
        d.clear()
        t = self.time
        cx = GRID_SIZE // 2

        # Tunnel walls (one-point perspective, like the corridor)
        vp_y = 35  # Vanishing point
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                dx = abs(x - cx)
                wall_hw = 6 + abs(y - vp_y) * 0.7

                if dx < wall_hw:
                    # Floor/ceiling - stone texture
                    stone = ((x * 3 + y * 7) % 11) / 11.0
                    if y < vp_y:
                        # Ceiling
                        base = int(50 + stone * 20)
                        d.set_pixel(x, y, (base, max(0, base - 5), max(0, base - 10)))
                    else:
                        # Floor
                        base = int(60 + stone * 15)
                        d.set_pixel(x, y, (base, max(0, base - 5), max(0, base - 15)))
                else:
                    # Walls
                    depth = abs(y - vp_y) / 32.0
                    stone = ((x * 5 + y * 3) % 7) / 7.0
                    base = int(40 + stone * 15 + depth * 20)
                    d.set_pixel(x, y, (base, max(0, base - 8), max(0, base - 15)))

        # Running figure silhouette (Indy)
        fig_x = 20 + int(math.sin(t * 3.0) * 2)  # Bob while running
        fig_y_base = 50
        sil = (5, 5, 3)

        # Hat
        hat_y = fig_y_base - 14
        for dx in range(-3, 4):
            if 0 <= fig_x + dx < GRID_SIZE and 0 <= hat_y < GRID_SIZE:
                d.set_pixel(fig_x + dx, hat_y, sil)
        for dx in range(-2, 3):
            if 0 <= fig_x + dx < GRID_SIZE and 0 <= hat_y - 1 < GRID_SIZE:
                d.set_pixel(fig_x + dx, hat_y - 1, sil)
            if 0 <= fig_x + dx < GRID_SIZE and 0 <= hat_y - 2 < GRID_SIZE:
                d.set_pixel(fig_x + dx, hat_y - 2, sil)

        # Head
        for dy in range(1, 4):
            for dx in range(-1, 2):
                px, py = fig_x + dx, hat_y + dy
                if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                    d.set_pixel(px, py, sil)

        # Body
        for dy in range(4, 12):
            row = hat_y + dy
            if row >= GRID_SIZE:
                break
            w = 2 if dy < 8 else 1
            for dx in range(-w, w + 1):
                px = fig_x + dx
                if 0 <= px < GRID_SIZE and 0 <= row < GRID_SIZE:
                    d.set_pixel(px, row, sil)

        # Running legs (animated)
        leg_phase = math.sin(t * 8.0)
        for leg_side in [-1, 1]:
            leg_dx = int(leg_phase * leg_side * 2)
            for i in range(3):
                px = fig_x + leg_dx + (i if leg_side > 0 else -i)
                py = fig_y_base - 2 + i
                if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                    d.set_pixel(px, py, sil)

        # Boulder (large circle, right side, rolling)
        boulder_cx = 48 + int(math.sin(t * 0.3) * 3)
        boulder_cy = 38
        boulder_r = 10
        roll_angle = t * 3.0

        for dy in range(-boulder_r, boulder_r + 1):
            for dx in range(-boulder_r, boulder_r + 1):
                dist = math.sqrt(dx * dx + dy * dy)
                if dist <= boulder_r:
                    px, py = boulder_cx + dx, boulder_cy + dy
                    if not (0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE):
                        continue
                    # Rocky texture that rotates
                    angle = math.atan2(dy, dx) + roll_angle
                    tex = math.sin(angle * 3) * math.sin(dist * 0.8) * 0.3
                    edge = dist / boulder_r
                    base = 0.6 + tex - edge * 0.3
                    base = max(0.2, min(1.0, base))
                    r = int(140 * base)
                    g = int(120 * base)
                    b = int(80 * base)
                    d.set_pixel(px, py, (r, g, b))

        # Dust particles
        for p in self._dust:
            px, py = int(p['x']), int(p['y'])
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                frac = max(0, p['life'] / 0.8)
                bri = int(80 * frac)
                d.set_pixel(px, py, (bri, max(0, bri - 10), max(0, bri - 20)))

        # Title text - adventure gold
        tp = 0.6 + 0.4 * math.sin(t * 1.2)
        d.draw_text_small(WONDER_X, WONDER_Y, "WONDER",
                          (int(240 * tp), int(190 * tp), int(60 * tp)))
        tp2 = 0.6 + 0.4 * math.sin(t * 1.2 + 0.5)
        d.draw_text_small(CABINET_X, CABINET_Y, "CABINET",
                          (int(220 * tp2), int(170 * tp2), int(50 * tp2)))


# =========================================================================
# WonderMetropolis - Maria the robot with electric arcs
# =========================================================================

class WonderMetropolis(Visual):
    name = "WONDER METROPOLIS"
    description = "Maria the machine"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self._arcs = []

    def update(self, dt: float):
        self.time += dt
        # Update arcs
        for a in self._arcs:
            a['life'] -= dt
        self._arcs = [a for a in self._arcs if a['life'] > 0]
        # Spawn new arcs
        if random.random() < 0.3:
            cx = GRID_SIZE // 2
            side = random.choice([-1, 1])
            self._arcs.append({
                'x': cx + side * random.randint(8, 20),
                'y': random.randint(10, 45),
                'segments': [(random.uniform(-3, 3), random.uniform(-3, 3))
                             for _ in range(random.randint(3, 6))],
                'life': random.uniform(0.05, 0.15),
            })

    def draw(self):
        d = self.display
        d.clear()
        t = self.time
        cx = GRID_SIZE // 2

        # Dark art deco background
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                # Radiating lines from center (deco pattern)
                angle = math.atan2(y - 25, x - cx)
                ray = int(abs(math.sin(angle * 8)) * 6)
                d.set_pixel(x, y, (ray + 3, ray + 2, ray + 5))

        # Maria robot silhouette (chrome art deco humanoid)
        # Head (circular with art deco crown)
        head_cy = 14
        for dy in range(-4, 5):
            for dx in range(-3, 4):
                dist = math.sqrt(dx * dx + dy * dy)
                if dist <= 4:
                    px, py = cx + dx, head_cy + dy
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        edge = dist / 4.0
                        # Chrome metallic
                        bri = 0.6 + 0.3 * math.cos(dx * 0.8 + t * 0.5) - edge * 0.2
                        bri = max(0.2, min(1.0, bri))
                        d.set_pixel(px, py, (int(160 * bri), int(170 * bri),
                                             int(180 * bri)))
        # Crown spikes
        for i in range(5):
            spike_x = cx - 4 + i * 2
            for sy in range(head_cy - 6, head_cy - 3):
                if 0 <= spike_x < GRID_SIZE and 0 <= sy < GRID_SIZE:
                    d.set_pixel(spike_x, sy, (140, 150, 160))

        # Eyes (glowing)
        eye_glow = 0.5 + 0.5 * math.sin(t * 2.0)
        for side in [-1, 1]:
            ex = cx + side * 2
            ey = head_cy - 1
            if 0 <= ex < GRID_SIZE and 0 <= ey < GRID_SIZE:
                d.set_pixel(ex, ey, (int(200 * eye_glow), int(200 * eye_glow),
                                     int(100 * eye_glow)))

        # Neck
        for dy in range(5, 8):
            for dx in range(-1, 2):
                px, py = cx + dx, head_cy + dy
                if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                    d.set_pixel(px, py, (100, 110, 120))

        # Torso (art deco angular)
        torso_top = head_cy + 8
        for dy in range(14):
            row = torso_top + dy
            if row >= GRID_SIZE:
                break
            # Shoulders wide, waist narrow, hips moderate
            if dy < 3:
                hw = 6 + dy
            elif dy < 8:
                hw = 9 - dy // 2
            else:
                hw = 5 + (dy - 8) // 2
            hw = min(hw, 10)
            for dx in range(-hw, hw + 1):
                px = cx + dx
                if 0 <= px < GRID_SIZE:
                    edge = abs(dx) / max(1, hw)
                    bri = 0.4 + 0.2 * (1 - edge)
                    # Segmented armor plates
                    if dy % 4 == 0:
                        bri += 0.15
                    d.set_pixel(px, row, (int(130 * bri), int(140 * bri),
                                          int(155 * bri)))

        # Art deco rings around the figure
        ring_r = 18 + int(math.sin(t * 0.8) * 2)
        ring_cy = 28
        for i in range(64):
            angle = i / 64.0 * math.pi * 2
            rx = int(cx + ring_r * math.cos(angle))
            ry = int(ring_cy + ring_r * 0.5 * math.sin(angle))
            if 0 <= rx < GRID_SIZE and 0 <= ry < GRID_SIZE:
                pulse = 0.3 + 0.7 * abs(math.sin(angle * 3 + t * 2))
                d.set_pixel(rx, ry, (int(100 * pulse), int(110 * pulse),
                                     int(130 * pulse)))

        # Electric arcs
        for a in self._arcs:
            frac = a['life'] / 0.15
            ax, ay = a['x'], a['y']
            for sdx, sdy in a['segments']:
                ax += sdx
                ay += sdy
                px, py = int(ax), int(ay)
                if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                    d.set_pixel(px, py, (int(200 * frac), int(220 * frac),
                                         int(255 * frac)))

        # Title text - silver art deco
        tp = 0.6 + 0.4 * math.sin(t * 1.0)
        d.draw_text_small(WONDER_X, WONDER_Y + 20, "WONDER",
                          (int(180 * tp), int(190 * tp), int(210 * tp)))
        tp2 = 0.6 + 0.4 * math.sin(t * 1.0 + 0.5)
        d.draw_text_small(CABINET_X, CABINET_Y + 20, "CABINET",
                          (int(160 * tp2), int(170 * tp2), int(190 * tp2)))


# =========================================================================
# WonderKingKong - Atop the Empire State, biplanes circling
# =========================================================================

class WonderKingKong(Visual):
    name = "WONDER KING KONG"
    description = "Top of the world"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        d = self.display
        d.clear()
        t = self.time
        cx = GRID_SIZE // 2

        # Dusk sky gradient
        for y in range(GRID_SIZE):
            grad = y / GRID_SIZE
            r = int(40 + 60 * (1 - grad))
            g = int(25 + 40 * (1 - grad))
            b = int(50 + 30 * (1 - grad))
            for x in range(GRID_SIZE):
                d.set_pixel(x, y, (r, g, b))

        # Empire State Building spire
        spire_x = cx
        spire_base = GRID_SIZE  # Goes off screen at bottom

        # Main spire (narrow tower top)
        for y in range(20, GRID_SIZE):
            # Tower narrows toward top
            if y < 30:
                hw = 1
            elif y < 40:
                hw = 2
            elif y < 50:
                hw = 4 + (y - 40) // 3
            else:
                hw = 7 + (y - 50) // 2
            hw = min(hw, 14)
            for dx in range(-hw, hw + 1):
                px = spire_x + dx
                if 0 <= px < GRID_SIZE:
                    edge = abs(dx) / max(1, hw)
                    # Art deco limestone
                    bri = 0.5 + 0.3 * (1 - edge)
                    # Window pattern
                    if y > 35 and abs(dx) < hw - 1 and (y % 3 == 0) and (dx % 2 == 0):
                        d.set_pixel(px, y, (int(160 * bri), int(140 * bri),
                                            int(60 * bri)))
                    else:
                        d.set_pixel(px, y, (int(120 * bri), int(115 * bri),
                                            int(100 * bri)))

        # Antenna
        for y in range(14, 21):
            if 0 <= spire_x < GRID_SIZE:
                d.set_pixel(spire_x, y, (100, 95, 85))

        # Kong silhouette on the spire
        kong_x = spire_x - 1
        kong_top = 25
        sil = (8, 6, 5)

        # Head
        for dy in range(5):
            for dx in range(-2, 3):
                dist = math.sqrt(dx * dx + (dy - 2) ** 2)
                if dist <= 2.5:
                    px, py = kong_x + dx, kong_top + dy
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        d.set_pixel(px, py, sil)

        # Body (hunched, holding onto spire)
        for dy in range(5, 14):
            row = kong_top + dy
            if row >= GRID_SIZE:
                break
            hw = 3 if dy < 10 else 2
            for dx in range(-hw, hw + 1):
                px = kong_x + dx
                if 0 <= px < GRID_SIZE and 0 <= row < GRID_SIZE:
                    d.set_pixel(px, row, sil)

        # Arm reaching out (holding something)
        arm_y = kong_top + 7
        for i in range(5):
            ax = kong_x - 3 - i
            ay = arm_y - i // 2
            if 0 <= ax < GRID_SIZE and 0 <= ay < GRID_SIZE:
                d.set_pixel(ax, ay, sil)
                if ay + 1 < GRID_SIZE:
                    d.set_pixel(ax, ay + 1, sil)

        # Biplanes circling
        for plane_i in range(3):
            angle = t * 0.8 + plane_i * math.pi * 2 / 3
            orbit_r = 22
            px = int(cx + orbit_r * math.cos(angle))
            py = int(30 + orbit_r * 0.3 * math.sin(angle))

            # Plane silhouette (tiny)
            facing_right = math.cos(angle - math.pi / 2) > 0
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                d.set_pixel(px, py, (60, 60, 50))
                # Wings
                wing_dir = 1 if facing_right else -1
                for w in range(-2, 3):
                    wx = px + w
                    if 0 <= wx < GRID_SIZE:
                        d.set_pixel(wx, py, (60, 60, 50))
                # Tail
                tx = px - wing_dir * 2
                if 0 <= tx < GRID_SIZE and 0 <= py - 1 < GRID_SIZE:
                    d.set_pixel(tx, py - 1, (60, 60, 50))

        # Searchlight beams from below
        for beam_i in range(2):
            beam_angle = math.sin(t * 0.5 + beam_i * 2) * 0.4
            for by in range(GRID_SIZE - 1, 20, -1):
                bx = int(cx + (GRID_SIZE - by) * math.tan(beam_angle) +
                         beam_i * 10 - 5)
                if 0 <= bx < GRID_SIZE:
                    fall = (GRID_SIZE - by) / 40.0
                    intensity = int(20 * max(0, 1.0 - fall))
                    if intensity > 0:
                        ex = d.get_pixel(bx, by)
                        d.set_pixel(bx, by, (min(255, ex[0] + intensity),
                                             min(255, ex[1] + intensity),
                                             min(255, ex[2] + intensity)))

        # Title text
        tp = 0.6 + 0.4 * math.sin(t * 1.0)
        d.draw_text_small(WONDER_X, WONDER_Y, "WONDER",
                          (int(220 * tp), int(190 * tp), int(120 * tp)))
        tp2 = 0.6 + 0.4 * math.sin(t * 1.0 + 0.5)
        d.draw_text_small(CABINET_X, CABINET_Y, "CABINET",
                          (int(200 * tp2), int(170 * tp2), int(100 * tp2)))


# =========================================================================
# WonderWizardOz - Sepia to color with tornado
# =========================================================================

class WonderWizardOz(Visual):
    name = "WONDER WIZARD OF OZ"
    description = "Somewhere over rainbow"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self._debris = []

    def update(self, dt: float):
        self.time += dt
        for p in self._debris:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['angle'] += p['spin'] * dt
            p['life'] -= dt
        self._debris = [p for p in self._debris if p['life'] > 0]
        # Spawn debris near tornado
        if random.random() < 0.2:
            self._debris.append({
                'x': float(GRID_SIZE // 2 + random.randint(-5, 5)),
                'y': float(random.randint(15, 50)),
                'vx': random.uniform(-8, 8),
                'vy': random.uniform(-10, -2),
                'angle': random.uniform(0, math.pi * 2),
                'spin': random.uniform(-5, 5),
                'life': random.uniform(0.5, 1.5),
            })

    def draw(self):
        d = self.display
        d.clear()
        t = self.time
        cx = GRID_SIZE // 2

        # The visual cycles between sepia (Kansas) and color (Oz)
        cycle = 10.0
        ct = t % cycle
        color_blend = 0.0
        if ct > 5.0:
            color_blend = min(1.0, (ct - 5.0) / 2.0)

        # Background
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if color_blend < 0.5:
                    # Sepia Kansas sky
                    grad = y / GRID_SIZE
                    base = int(120 - grad * 50)
                    sepia = (base, int(base * 0.85), int(base * 0.65))
                    d.set_pixel(x, y, sepia)
                else:
                    # Technicolor Oz - rainbow sky
                    grad = y / GRID_SIZE
                    hue = (x / GRID_SIZE * 0.3 + grad * 0.1 + t * 0.05) % 1.0
                    rgb = _hue_to_rgb(hue)
                    blend = (color_blend - 0.5) * 2  # 0-1 for Oz portion
                    # Blend from sepia to color
                    base = int(120 - grad * 50)
                    sepia = (base, int(base * 0.85), int(base * 0.65))
                    r = int(sepia[0] + (rgb[0] // 3 - sepia[0]) * blend)
                    g = int(sepia[1] + (rgb[1] // 3 - sepia[1]) * blend)
                    b = int(sepia[2] + (rgb[2] // 3 - sepia[2]) * blend)
                    d.set_pixel(x, y, (max(0, r), max(0, g), max(0, b)))

        # Tornado (in Kansas phase)
        if color_blend < 0.8:
            tornado_opacity = 1.0 - color_blend
            # Funnel shape: narrow at top, wide at bottom
            for y in range(5, 58):
                progress = (y - 5) / 53.0
                width = 2 + int(progress * 12)
                # Swirl offset
                swirl = math.sin(y * 0.3 + t * 4.0) * (width * 0.3)
                for dx in range(-width, width + 1):
                    px = int(cx + dx + swirl)
                    if 0 <= px < GRID_SIZE and 0 <= y < GRID_SIZE:
                        edge = abs(dx) / max(1, width)
                        bri = (0.4 - edge * 0.2) * tornado_opacity
                        if bri > 0.05:
                            # Dark funnel cloud
                            ex = d.get_pixel(px, y)
                            dark = int(bri * 80)
                            d.set_pixel(px, y, (max(0, ex[0] - dark),
                                                max(0, ex[1] - dark),
                                                max(0, ex[2] - dark)))

        # Flying debris
        for p in self._debris:
            px, py = int(p['x']), int(p['y'])
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                frac = max(0, p['life'] / 1.5)
                d.set_pixel(px, py, (int(80 * frac), int(70 * frac),
                                     int(50 * frac)))

        # Rainbow (in Oz phase)
        if color_blend > 0.3:
            rb_opacity = min(1.0, (color_blend - 0.3) * 2)
            rb_cx, rb_cy = cx, GRID_SIZE + 10
            for angle_i in range(40):
                angle = math.pi * 0.15 + angle_i / 40.0 * math.pi * 0.7
                for band in range(6):
                    r = 30 + band * 2
                    px = int(rb_cx + r * math.cos(angle))
                    py = int(rb_cy - r * math.sin(angle))
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        hue = band / 6.0
                        color = _hue_to_rgb(hue)
                        c = (int(color[0] * rb_opacity * 0.6),
                             int(color[1] * rb_opacity * 0.6),
                             int(color[2] * rb_opacity * 0.6))
                        d.set_pixel(px, py, c)

        # Title text - transitions from sepia to technicolor
        if color_blend < 0.5:
            tc = (int(200 * (0.6 + 0.4 * math.sin(t))),
                  int(170 * (0.6 + 0.4 * math.sin(t))),
                  int(100 * (0.6 + 0.4 * math.sin(t))))
            tc2 = (int(180 * (0.6 + 0.4 * math.sin(t + 0.5))),
                   int(150 * (0.6 + 0.4 * math.sin(t + 0.5))),
                   int(80 * (0.6 + 0.4 * math.sin(t + 0.5))))
        else:
            tp = 0.6 + 0.4 * math.sin(t * 1.5)
            tc = (int(100 * tp), int(220 * tp), int(100 * tp))
            tc2 = (int(80 * tp), int(200 * tp), int(80 * tp))
        d.draw_text_small(WONDER_X, WONDER_Y, "WONDER", tc)
        d.draw_text_small(CABINET_X, CABINET_Y, "CABINET", tc2)


# =========================================================================
# WonderGhostbusters - Proton pack streams
# =========================================================================

class WonderGhostbusters(Visual):
    name = "WONDER GHOSTBUSTERS"
    description = "Don't cross the streams"
    category = "titles"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        d = self.display
        d.clear()
        t = self.time
        cx, cy = GRID_SIZE // 2, GRID_SIZE // 2

        # Dark background
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                d.set_pixel(x, y, (3, 3, 8))

        # No-ghost sign (red circle with slash)
        sign_cx, sign_cy = cx, 22
        sign_r = 14

        # White circle fill
        for dy in range(-sign_r, sign_r + 1):
            for dx in range(-sign_r, sign_r + 1):
                dist = math.sqrt(dx * dx + dy * dy)
                if dist <= sign_r - 2:
                    px, py = sign_cx + dx, sign_cy + dy
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        d.set_pixel(px, py, (240, 240, 240))

        # Ghost silhouette (inside circle)
        ghost_cx = sign_cx
        ghost_top = sign_cy - 7
        for dy in range(12):
            row = ghost_top + dy
            if dy < 5:
                hw = 2 + dy
            elif dy < 9:
                hw = 7
            else:
                hw = 7
            # Ghost wavy bottom
            if dy >= 9:
                wavy = (dy - 9)
                for dx in range(-hw, hw + 1):
                    # Wavy bottom edge
                    if (dx + wavy) % 3 == 0:
                        continue
                    px, py = ghost_cx + dx, row
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        d.set_pixel(px, py, (180, 230, 180))
            else:
                for dx in range(-hw, hw + 1):
                    px, py = ghost_cx + dx, row
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        d.set_pixel(px, py, (180, 230, 180))

        # Ghost eyes
        for side in [-1, 1]:
            ex = ghost_cx + side * 3
            ey = ghost_top + 3
            if 0 <= ex < GRID_SIZE and 0 <= ey < GRID_SIZE:
                d.set_pixel(ex, ey, (10, 10, 10))
                if 0 <= ey + 1 < GRID_SIZE:
                    d.set_pixel(ex, ey + 1, (10, 10, 10))
        # Ghost mouth
        for dx in range(-2, 3):
            mx = ghost_cx + dx
            my = ghost_top + 6
            if 0 <= mx < GRID_SIZE and 0 <= my < GRID_SIZE:
                d.set_pixel(mx, my, (10, 10, 10))

        # Red circle border
        for i in range(80):
            angle = i / 80.0 * math.pi * 2
            for r_off in range(-1, 2):
                rx = int(sign_cx + (sign_r + r_off) * math.cos(angle))
                ry = int(sign_cy + (sign_r + r_off) * math.sin(angle))
                if 0 <= rx < GRID_SIZE and 0 <= ry < GRID_SIZE:
                    d.set_pixel(rx, ry, (220, 30, 20))

        # Red slash (diagonal line through ghost)
        for i in range(sign_r * 2 + 2):
            frac = i / (sign_r * 2 + 1)
            sx = int(sign_cx - sign_r + i)
            sy = int(sign_cy - sign_r + i)
            for w in range(-1, 2):
                px = sx
                py = sy + w
                if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                    d.set_pixel(px, py, (220, 30, 20))

        # Proton streams (two beams converging)
        for beam_i in range(2):
            start_x = 5 if beam_i == 0 else 58
            start_y = 55
            target_x = cx + int(math.sin(t * 2.0 + beam_i * 3) * 5)
            target_y = 38 + int(math.cos(t * 1.5) * 3)

            segments = 20
            for s in range(segments):
                frac = s / segments
                bx = int(start_x + (target_x - start_x) * frac)
                by = int(start_y + (target_y - start_y) * frac)
                # Wavy beam
                wobble_x = int(math.sin(s * 1.5 + t * 8 + beam_i * 5) * 2)
                wobble_y = int(math.cos(s * 1.2 + t * 6 + beam_i * 3) * 1.5)
                px = bx + wobble_x
                py = by + wobble_y
                if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                    # Orange-red proton stream
                    intensity = 0.5 + 0.5 * math.sin(s * 0.8 + t * 10)
                    d.set_pixel(px, py, (int(255 * intensity),
                                         int(120 * intensity),
                                         int(30 * intensity)))

        # Crossing point sparks
        spark_x = target_x
        spark_y = target_y
        if random.random() < 0.5:
            for _ in range(3):
                sx = spark_x + random.randint(-3, 3)
                sy = spark_y + random.randint(-3, 3)
                if 0 <= sx < GRID_SIZE and 0 <= sy < GRID_SIZE:
                    d.set_pixel(sx, sy, (255, 255, 200))

        # Title text
        tp = 0.6 + 0.4 * math.sin(t * 1.5)
        d.draw_text_small(WONDER_X, WONDER_Y + 20, "WONDER",
                          (int(255 * tp), int(50 * tp), int(30 * tp)))
        tp2 = 0.6 + 0.4 * math.sin(t * 1.5 + 0.5)
        d.draw_text_small(CABINET_X, CABINET_Y + 20, "CABINET",
                          (int(230 * tp2), int(40 * tp2), int(20 * tp2)))
