"""
Yoshi Tongue - GIF Sprite Animation
=====================================
Yoshi (with Mario riding) flicks his tongue out and retracts it,
loaded from an animated GIF with alpha transparency.

Controls:
  Left/Right  - Adjust speed
  Space       - Reset
  Escape      - Exit
"""

import os
import math
from . import Visual, Display, Colors, GRID_SIZE

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class Yoshi(Visual):
    name = "YOSHI"
    description = "Tongue flick"
    category = "sprites"

    GIF_FILE = "yoshi_tongue.gif"
    BASE_INTERVAL = 0.08

    # Per-frame scroll delta: +1 on the step-out frame only
    FRAME_SCROLL_DELTA = [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    # Yoshi's Island palette
    SKY_TOP = (80, 160, 252)
    SKY_BOT = (140, 200, 252)
    HILL_FAR = (80, 180, 80)
    HILL_NEAR = (50, 160, 50)
    GRASS_TOP = (30, 200, 30)
    GRASS_BASE = (20, 160, 20)
    GROUND = (120, 90, 50)
    GROUND_DARK = (90, 65, 35)
    FLOWER_CENTER = (252, 220, 40)
    FLOWER_PETAL = (252, 100, 100)
    BUSH_COLOR = (40, 140, 40)
    BUSH_LIGHT = (60, 170, 60)
    CLOUD_COLOR = (252, 252, 252)
    CLOUD_SHADOW = (220, 230, 252)

    GROUND_Y = 56  # Feet land at scaled y=55

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed = 1.0
        self.frame_timer = 0.0
        self.frame_index = 0
        self.scroll_offset = 0

        self.sprites = []  # list of (pixels, alphas, w, h)
        self._load_gif()
        self._build_background()

    def _load_gif(self):
        """Load all GIF frames scaled to 64px height with alpha."""
        if not HAS_PIL:
            return

        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = os.path.dirname(script_dir)
        path = os.path.join(project_dir, "assets", self.GIF_FILE)
        if not os.path.exists(path):
            return

        try:
            gif = Image.open(path)
            orig_w, orig_h = gif.size
            scale = GRID_SIZE / orig_h
            new_w = int(orig_w * scale)
            new_h = GRID_SIZE

            for i in range(getattr(gif, 'n_frames', 1)):
                gif.seek(i)
                frame = gif.convert("RGBA")
                frame = frame.resize((new_w, new_h), Image.Resampling.NEAREST)

                pixels = []
                alphas = []
                for y in range(new_h):
                    prow = []
                    arow = []
                    for x in range(new_w):
                        r, g, b, a = frame.getpixel((x, y))
                        prow.append((r, g, b))
                        arow.append(a)
                    pixels.append(prow)
                    alphas.append(arow)
                self.sprites.append((pixels, alphas, new_w, new_h))
        except Exception:
            pass

    def _build_background(self):
        """Pre-render Yoshi's Island hillside background."""
        self.bg_buf = [[(0, 0, 0)] * GRID_SIZE for _ in range(GRID_SIZE)]
        gy = self.GROUND_Y

        # Gradient sky
        for y in range(gy):
            t = y / max(1, gy - 1)
            r = int(self.SKY_TOP[0] + (self.SKY_BOT[0] - self.SKY_TOP[0]) * t)
            g = int(self.SKY_TOP[1] + (self.SKY_BOT[1] - self.SKY_TOP[1]) * t)
            b = int(self.SKY_TOP[2] + (self.SKY_BOT[2] - self.SKY_TOP[2]) * t)
            for x in range(GRID_SIZE):
                self.bg_buf[y][x] = (r, g, b)

        # Far rolling hills
        for x in range(GRID_SIZE):
            hill_h = int(6 + 4 * math.sin(x * 0.12) + 2 * math.sin(x * 0.25 + 1.5))
            for dy in range(hill_h):
                y = gy - 1 - dy
                if 0 <= y < gy:
                    self.bg_buf[y][x] = self.HILL_FAR

        # Near hills
        for x in range(GRID_SIZE):
            hill_h = int(3 + 3 * math.sin(x * 0.18 + 2.0) + 1.5 * math.sin(x * 0.35))
            for dy in range(hill_h):
                y = gy - 1 - dy
                if 0 <= y < gy:
                    self.bg_buf[y][x] = self.HILL_NEAR

        # Clouds
        for cx, cy in [(10, 8), (38, 5), (55, 10)]:
            for dx, dy in [(-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0),
                           (-3, 1), (-2, 1), (-1, 1), (0, 1), (1, 1), (2, 1), (3, 1),
                           (-2, 2), (-1, 2), (0, 2), (1, 2), (2, 2)]:
                px, py = cx + dx, cy + dy
                if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                    self.bg_buf[py][px] = self.CLOUD_SHADOW if dy == 2 else self.CLOUD_COLOR

        # Ground
        for y in range(gy, GRID_SIZE):
            for x in range(GRID_SIZE):
                if y == gy:
                    self.bg_buf[y][x] = self.GRASS_TOP
                elif y == gy + 1:
                    self.bg_buf[y][x] = self.GRASS_BASE
                else:
                    self.bg_buf[y][x] = self.GROUND_DARK if (x + y) % 7 == 0 else self.GROUND

        # Bushes
        for bx in [48, 58]:
            for dx, dy in [(-1, -1), (0, -1), (1, -1),
                           (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0),
                           (-1, 1), (0, 1), (1, 1)]:
                px, py = bx + dx, gy + dy
                if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                    self.bg_buf[py][px] = self.BUSH_LIGHT if dy == -1 else self.BUSH_COLOR

        # Flowers
        for fx in [45, 53, 61]:
            fy = gy - 1
            if 0 <= fx < GRID_SIZE and 0 <= fy < GRID_SIZE:
                self.bg_buf[fy][fx] = self.FLOWER_CENTER
                for ddx, ddy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    px, py = fx + ddx, fy + ddy
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        self.bg_buf[py][px] = self.FLOWER_PETAL

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.left:
            self.speed = max(0.2, self.speed - 0.2)
            consumed = True
        if input_state.right:
            self.speed = min(5.0, self.speed + 0.2)
            consumed = True

        if input_state.action_l or input_state.action_r:
            self.speed = 1.0
            self.frame_index = 0
            self.frame_timer = 0.0
            self.scroll_offset = 0
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt

        if not self.sprites:
            return

        self.frame_timer += dt
        effective_interval = max(self.BASE_INTERVAL / self.speed, 0.02)

        if self.frame_timer >= effective_interval:
            self.frame_timer -= effective_interval
            self.frame_index = (self.frame_index + 1) % len(self.sprites)
            delta = self.FRAME_SCROLL_DELTA[self.frame_index % len(self.FRAME_SCROLL_DELTA)]
            self.scroll_offset = (self.scroll_offset + delta) % GRID_SIZE

    def _blit(self, set_pixel, sprite):
        """Draw sprite at (0,0) clipping to 64x64 display."""
        pixels, alphas, w, h = sprite
        for y in range(min(h, GRID_SIZE)):
            arow = alphas[y]
            prow = pixels[y]
            for x in range(min(w, GRID_SIZE)):
                if arow[x] > 128:
                    set_pixel(x, y, prow[x])

    def draw(self):
        display = self.display
        set_pixel = display.set_pixel

        # 1. Background (scrolls forward as Yoshi walks)
        bg = self.bg_buf
        scroll = self.scroll_offset
        for y in range(GRID_SIZE):
            row = bg[y]
            for x in range(GRID_SIZE):
                set_pixel(x, y, row[(x + scroll) % GRID_SIZE])

        # 2. Yoshi sprite overlay (alpha transparency)
        if not self.sprites:
            display.draw_text_small(4, 28, "NO FRAMES", Colors.RED)
            return

        self._blit(set_pixel, self.sprites[self.frame_index])
