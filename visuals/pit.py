"""
Pit Flying - Sprite Animation
===============================
Pit soars through Angel Land's Skyworld, banking left and right
across the cloud-filled sky. 2-frame wing-flap animation from
Kid Icarus NES sprites.

Controls:
  Left/Right  - Adjust speed
  Up/Down     - Cycle sky (day / sunset / night / sunrise)
  Space       - Reset
  Escape      - Exit
"""

import os
import math
import random
from . import Visual, Display, Colors, GRID_SIZE

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


# Sky palettes: (sky_top, sky_bot, cloud, column_light, column_dark, column_cap, star_chance)
_SKIES = {
    'day': (
        (100, 160, 255), (180, 220, 255), (240, 240, 248),
        (200, 195, 210), (150, 145, 165), (220, 215, 230), 0.0,
    ),
    'sunset': (
        (180, 80, 40), (255, 160, 60), (255, 200, 140),
        (180, 140, 110), (130, 95, 75), (200, 165, 130), 0.0,
    ),
    'night': (
        (10, 10, 40), (25, 20, 60), (60, 55, 80),
        (70, 65, 90), (45, 40, 60), (90, 85, 110), 0.08,
    ),
    'sunrise': (
        (60, 40, 120), (200, 140, 100), (220, 180, 160),
        (170, 145, 155), (120, 100, 115), (195, 175, 180), 0.0,
    ),
}
_SKY_ORDER = ['day', 'sunset', 'night', 'sunrise']

# Cloud layout shared across all sky states
_CLOUDS = [
    (5, 8, 10, 4), (30, 4, 12, 5), (52, 12, 8, 3),
    (15, 45, 9, 3), (40, 50, 11, 4), (58, 42, 6, 3),
    (2, 28, 7, 3), (35, 30, 8, 3), (55, 25, 6, 2),
]


class Pit(Visual):
    name = "PIT"
    description = "Angel Land flight"
    category = "sprites"

    PIT_R_GIF = "PitFlyingR.gif"
    PIT_L_GIF = "PitFlyingL.gif"

    WORLD_W = 80
    VIEW_OFFSET = 8
    BASE_SPEED = 25.0
    FLAP_INTERVAL = 0.12
    DIR_CHANGE_MIN = 1.0
    DIR_CHANGE_MAX = 6.0

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
        self._next_dir_change = random.uniform(self.DIR_CHANGE_MIN, self.DIR_CHANGE_MAX)

        self.sky_idx = 0
        self._prev_up = False
        self._prev_down = False
        self._build_all_backgrounds()

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

    def _build_all_backgrounds(self):
        """Pre-render a background buffer for each sky state."""
        self._backgrounds = {}
        rng = random.Random(42)
        for key in _SKY_ORDER:
            sky_top, sky_bot, cloud_c, col_lt, col_dk, col_cap, star_chance = _SKIES[key]
            buf = [[(0, 0, 0)] * GRID_SIZE for _ in range(GRID_SIZE)]

            # Sky gradient
            for y in range(GRID_SIZE):
                t = y / GRID_SIZE
                r = int(sky_top[0] + (sky_bot[0] - sky_top[0]) * t)
                g = int(sky_top[1] + (sky_bot[1] - sky_top[1]) * t)
                b = int(sky_top[2] + (sky_bot[2] - sky_top[2]) * t)
                for x in range(GRID_SIZE):
                    buf[y][x] = (r, g, b)

            # Stars (night sky)
            if star_chance > 0:
                star_rng = random.Random(99)
                for y in range(GRID_SIZE):
                    for x in range(GRID_SIZE):
                        if star_rng.random() < star_chance:
                            v = star_rng.randint(140, 255)
                            buf[y][x] = (v, v, int(v * 0.85))

            # Clouds
            for cx, cy, cw, ch in _CLOUDS:
                for dy in range(ch):
                    for dx in range(cw):
                        if (dy == 0 or dy == ch - 1) and (dx == 0 or dx == cw - 1):
                            continue
                        px, py = cx + dx, cy + dy
                        if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                            buf[py][px] = cloud_c

            # Greek columns at edges
            for col_x in [2, 60]:
                col_w = 3
                for dx in range(-1, col_w + 1):
                    px = col_x + dx
                    if 0 <= px < GRID_SIZE:
                        buf[52][px] = col_cap
                        buf[53][px] = col_cap
                for y in range(54, GRID_SIZE):
                    for dx in range(col_w):
                        px = col_x + dx
                        if 0 <= px < GRID_SIZE:
                            buf[y][px] = col_lt if dx == 1 else col_dk

            self._backgrounds[key] = buf

    def handle_input(self, input_state):
        consumed = False
        if input_state.left:
            self.speed_mult = max(0.3, self.speed_mult - 0.15)
            consumed = True
        if input_state.right:
            self.speed_mult = min(3.0, self.speed_mult + 0.15)
            consumed = True
        if input_state.up and not self._prev_up:
            self.sky_idx = (self.sky_idx - 1) % len(_SKY_ORDER)
            consumed = True
        if input_state.down and not self._prev_down:
            self.sky_idx = (self.sky_idx + 1) % len(_SKY_ORDER)
            consumed = True
        self._prev_up = input_state.up
        self._prev_down = input_state.down
        if input_state.action_l or input_state.action_r:
            self.speed_mult = 1.0
            self.pit_dir = 1
            self.pit_x = 40.0
            self.pit_y = 28.0
            self.pit_frame = 0
            self.dir_timer = 0.0
            self.sky_idx = 0
            consumed = True
        return consumed

    def update(self, dt):
        self.time += dt
        ws = self.WORLD_W
        spd = self.BASE_SPEED * self.speed_mult

        # Random direction change
        self.dir_timer += dt
        if self.dir_timer >= self._next_dir_change:
            self.dir_timer = 0.0
            self.pit_dir = -self.pit_dir
            self._next_dir_change = random.uniform(self.DIR_CHANGE_MIN, self.DIR_CHANGE_MAX)

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

        # 1. Background for current sky state
        sky_key = _SKY_ORDER[self.sky_idx]
        bg = self._backgrounds[sky_key]
        for y in range(GRID_SIZE):
            row = bg[y]
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
