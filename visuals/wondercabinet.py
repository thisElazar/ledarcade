"""
Wonder Cabinet - Branded idle visuals
======================================
Branded visuals for the Wonder Cabinet arcade.
Motion, game-inspired, film-inspired, and ad-inspired title screens.
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
CABINET_X = _center_x("CABINET") + 1  # 16 (visual nudge)
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


# =========================================================================
# WonderPacMan - Pac-Man eats dots, reveals title
# =========================================================================

class WonderPacMan(Visual):
    name = "WONDER PAC"
    description = "Pac-Man reveals title"
    category = "digital"

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
    category = "digital"

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
    category = "digital"

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
    category = "digital"

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
    category = "digital"

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
    category = "digital"

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
    category = "digital"

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
    category = "digital"
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
    category = "digital"
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
    category = "digital"
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
    category = "digital"
    _INTERVAL = 1.0 / 20

    def __init__(self, display: Display):
        super().__init__(display)

    def _init_grid(self):
        mask = _text_mask()
        self.grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.boids = []
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if mask[y][x]:
                    self.grid[y][x] = 255
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
    category = "digital"
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
    category = "digital"
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
    category = "digital"
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
    category = "digital"
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
    category = "digital"
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
