"""
Pit Flying - Sprite Animation
===============================
Pit soars through Angel Land's Skyworld, banking left and right
across the cloud-filled sky. 2-frame wing-flap animation from
Kid Icarus NES sprites.

Controls:
  Left/Right  - Change direction
  Up/Down     - Adjust speed
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


class Pit(Visual):
    name = "PIT"
    description = "Angel Land flight"
    category = "sprites"

    PIT_R_GIF = "PitFlyingR.gif"
    PIT_L_GIF = "PitFlyingL.gif"

    WORLD_W = 80
    VIEW_OFFSET = 8
    BASE_SPEED = 25.0
    FLAP_INTERVAL = 0.12     # Wing flap speed
    DIR_CHANGE_TIME = 4.0    # Seconds between auto direction changes

    # Skyworld palette
    SKY_TOP = (100, 160, 255)
    SKY_BOT = (180, 220, 255)
    CLOUD_COLOR = (240, 240, 248)
    COLUMN_LIGHT = (200, 195, 210)
    COLUMN_DARK = (150, 145, 165)
    COLUMN_CAP = (220, 215, 230)

    def __init__(self, display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed_mult = 1.0

        self.pit_r = []
        self.pit_l = []
        self._load_all()

        self.pit_x = 40.0
        self.pit_y = 28.0
        self.pit_dir = 1
        self.pit_frame = 0
        self.pit_timer = 0.0
        self.dir_timer = 0.0

        self._build_background()

    def _load_gif_native(self, filename):
        if not HAS_PIL:
            return []
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = os.path.dirname(script_dir)
        path = os.path.join(project_dir, "assets", filename)
        if not os.path.exists(path):
            return []

        from .gifcache import cache_frames, extract_rgba

        def process():
            gif = Image.open(path)
            result = []
            for i in range(getattr(gif, 'n_frames', 1)):
                gif.seek(i)
                frame = gif.convert("RGBA")
                w, h = frame.size
                pixels, alphas = extract_rgba(frame)
                result.append((pixels, alphas, w, h))
            return result

        return cache_frames(path, process) or []

    def _load_all(self):
        self.pit_r = self._load_gif_native(self.PIT_R_GIF)
        self.pit_l = self._load_gif_native(self.PIT_L_GIF)

    def _build_background(self):
        """Pre-render Skyworld background with gradient sky, clouds, columns."""
        self.bg_buf = [[(0, 0, 0)] * GRID_SIZE for _ in range(GRID_SIZE)]

        # Sky gradient
        for y in range(GRID_SIZE):
            t = y / GRID_SIZE
            r = int(self.SKY_TOP[0] + (self.SKY_BOT[0] - self.SKY_TOP[0]) * t)
            g = int(self.SKY_TOP[1] + (self.SKY_BOT[1] - self.SKY_TOP[1]) * t)
            b = int(self.SKY_TOP[2] + (self.SKY_BOT[2] - self.SKY_TOP[2]) * t)
            for x in range(GRID_SIZE):
                self.bg_buf[y][x] = (r, g, b)

        # Cloud clusters
        clouds = [
            (5, 8, 10, 4), (30, 4, 12, 5), (52, 12, 8, 3),
            (15, 45, 9, 3), (40, 50, 11, 4), (58, 42, 6, 3),
            (2, 28, 7, 3), (35, 30, 8, 3), (55, 25, 6, 2),
        ]
        cc = self.CLOUD_COLOR
        for cx, cy, cw, ch in clouds:
            for dy in range(ch):
                for dx in range(cw):
                    # Round corners
                    if (dy == 0 or dy == ch - 1) and (dx == 0 or dx == cw - 1):
                        continue
                    px, py = cx + dx, cy + dy
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        self.bg_buf[py][px] = cc

        # Greek columns at edges (decorative)
        for col_x in [2, 60]:
            col_w = 3
            # Capital (top piece)
            for dx in range(-1, col_w + 1):
                px = col_x + dx
                if 0 <= px < GRID_SIZE:
                    self.bg_buf[52][px] = self.COLUMN_CAP
                    self.bg_buf[53][px] = self.COLUMN_CAP
            # Shaft
            for y in range(54, GRID_SIZE):
                for dx in range(col_w):
                    px = col_x + dx
                    if 0 <= px < GRID_SIZE:
                        c = self.COLUMN_LIGHT if dx == 1 else self.COLUMN_DARK
                        self.bg_buf[y][px] = c

    def handle_input(self, input_state):
        consumed = False
        if input_state.left:
            self.pit_dir = -1
            self.dir_timer = 0.0
            consumed = True
        if input_state.right:
            self.pit_dir = 1
            self.dir_timer = 0.0
            consumed = True
        if input_state.up:
            self.speed_mult = min(3.0, self.speed_mult + 0.15)
            consumed = True
        if input_state.down:
            self.speed_mult = max(0.3, self.speed_mult - 0.15)
            consumed = True
        if input_state.action_l or input_state.action_r:
            self.speed_mult = 1.0
            self.pit_dir = 1
            self.pit_x = 40.0
            self.pit_y = 28.0
            self.pit_frame = 0
            self.dir_timer = 0.0
            consumed = True
        return consumed

    def update(self, dt):
        self.time += dt
        ws = self.WORLD_W
        spd = self.BASE_SPEED * self.speed_mult

        # Auto direction change
        self.dir_timer += dt
        if self.dir_timer >= self.DIR_CHANGE_TIME:
            self.dir_timer = 0.0
            self.pit_dir = -self.pit_dir

        # Horizontal movement (wrapping)
        self.pit_x = (self.pit_x + self.pit_dir * spd * dt) % ws

        # Vertical: gentle sine wave flight path
        self.pit_y = 26.0 + math.sin(self.time * 1.2) * 10.0

        # Wing flap animation
        self.pit_timer += dt
        interval = self.FLAP_INTERVAL / self.speed_mult
        if self.pit_timer >= interval:
            self.pit_timer -= interval
            frames = self.pit_r if self.pit_dir == 1 else self.pit_l
            if frames:
                self.pit_frame = (self.pit_frame + 1) % len(frames)

    def _blit(self, set_pixel, sprite, sx, sy):
        pixels, alphas, w, h = sprite
        ix, iy = int(sx), int(sy)
        for fy in range(h):
            dy = iy + fy
            if 0 <= dy < GRID_SIZE:
                for fx in range(w):
                    if alphas[fy][fx] > 128:
                        dx = ix + fx
                        if 0 <= dx < GRID_SIZE:
                            set_pixel(dx, dy, pixels[fy][fx])

    def draw(self):
        display = self.display
        sp = display.set_pixel

        # 1. Background
        for y in range(GRID_SIZE):
            row = self.bg_buf[y]
            for x in range(GRID_SIZE):
                sp(x, y, row[x])

        # 2. Pit sprite
        frames = self.pit_r if self.pit_dir == 1 else self.pit_l
        if frames:
            sf = frames[self.pit_frame % len(frames)]
            _, _, sw, sh = sf
            sx = self.pit_x - self.VIEW_OFFSET - sw / 2
            sy = self.pit_y - sh / 2
            self._blit(sp, sf, sx, sy)
