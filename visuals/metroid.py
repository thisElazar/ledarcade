"""
Samus Chase - Sprite Animation
=================================
Samus runs along a wrapping platform through a Brinstar cavern
while a Metroid gives chase. Change her direction and watch
the Metroid scramble to keep up! It never quite catches her.

The world is 80px wide so sprites vanish off one edge before
reappearing on the other (no split-sprite wrapping).

Controls:
  Left/Right  - Change Samus direction
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


class MetroidChase(Visual):
    name = "SAMUS"
    description = "Metroid chase"
    category = "sprites"

    SAMUS_R_GIF = "SamusRunningR.gif"
    SAMUS_L_GIF = "SamusRunningL.gif"
    METROID_GIF = "Metroidgif.gif"

    WORLD_SIZE = 80        # Virtual floor width (> 64 so sprites exit cleanly)
    VIEW_OFFSET = 8        # Screen shows world [8..71], centered in 80px world
    GROUND_Y = 50          # Top of platform
    PLATFORM_H = 3         # Platform thickness
    CHASE_DIST = 22        # Pixels the Metroid trails behind Samus
    SAMUS_SPEED = 30.0     # Base pixels per second
    METROID_SMOOTH = 2.0   # Exponential follow factor (lower = more sluggish)

    # Brinstar cavern palette
    BG_COLOR = (8, 4, 20)
    PLAT_TOP = (90, 80, 110)
    PLAT_MID = (60, 55, 80)
    PLAT_BOT = (40, 36, 55)
    PLAT_LIGHT = (140, 130, 180)

    def __init__(self, display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed_mult = 1.0

        self.samus_r = []
        self.samus_l = []
        self.metroid_sprites = []
        self._load_all()

        self.samus_x = 40.0
        self.samus_dir = 1
        self.samus_frame = 0
        self.samus_timer = 0.0

        self.metroid_x = (40.0 - self.CHASE_DIST) % self.WORLD_SIZE
        self.metroid_frame = 0
        self.metroid_timer = 0.0

        self._build_background()

    def _load_gif_native(self, filename):
        """Load all GIF frames at native resolution with alpha."""
        if not HAS_PIL:
            return []
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = os.path.dirname(script_dir)
        path = os.path.join(project_dir, "assets", filename)
        if not os.path.exists(path):
            return []
        result = []
        try:
            gif = Image.open(path)
            for i in range(getattr(gif, 'n_frames', 1)):
                gif.seek(i)
                frame = gif.convert("RGBA")
                w, h = frame.size
                pixels, alphas = [], []
                for y in range(h):
                    prow, arow = [], []
                    for x in range(w):
                        r, g, b, a = frame.getpixel((x, y))
                        prow.append((r, g, b))
                        arow.append(a)
                    pixels.append(prow)
                    alphas.append(arow)
                result.append((pixels, alphas, w, h))
        except Exception:
            pass
        return result

    def _load_all(self):
        self.samus_r = self._load_gif_native(self.SAMUS_R_GIF)
        self.samus_l = self._load_gif_native(self.SAMUS_L_GIF)
        self.metroid_sprites = self._load_gif_native(self.METROID_GIF)

    def _build_background(self):
        """Pre-render Brinstar cavern background."""
        bg = self.BG_COLOR
        self.bg_buf = [[bg] * GRID_SIZE for _ in range(GRID_SIZE)]

        import random
        rng = random.Random(77)

        # Rock texture specks
        for _ in range(50):
            x = rng.randint(0, 63)
            y = rng.randint(0, self.GROUND_Y - 1)
            s = rng.randint(10, 22)
            self.bg_buf[y][x] = (s, s // 3, s + 8)

        # Ceiling stalactites
        for base_x in [8, 25, 44, 57]:
            h = rng.randint(3, 7)
            for dy in range(h):
                w = max(1, 3 - dy)
                for dx in range(-w // 2, w // 2 + 1):
                    px = base_x + dx
                    if 0 <= px < GRID_SIZE:
                        s = 30 - dy * 3
                        self.bg_buf[dy][px] = (s, s // 2, s + 10)

        # Bioluminescent dots
        for _ in range(8):
            x = rng.randint(0, 63)
            y = rng.randint(2, self.GROUND_Y - 3)
            self.bg_buf[y][x] = (20, 60, 40)

        # Platform
        gy = self.GROUND_Y
        for dy in range(self.PLATFORM_H):
            y = gy + dy
            if y >= GRID_SIZE:
                break
            for x in range(GRID_SIZE):
                if dy == 0:
                    c = self.PLAT_LIGHT if x % 16 < 2 else self.PLAT_TOP
                elif dy == 1:
                    c = self.PLAT_MID
                else:
                    c = self.PLAT_BOT
                self.bg_buf[y][x] = c

        # Below platform
        for y in range(gy + self.PLATFORM_H, GRID_SIZE):
            for x in range(GRID_SIZE):
                self.bg_buf[y][x] = (4, 2, 10)

    def handle_input(self, input_state):
        consumed = False
        if input_state.left:
            self.samus_dir = -1
            consumed = True
        if input_state.right:
            self.samus_dir = 1
            consumed = True
        if input_state.up:
            self.speed_mult = min(3.0, self.speed_mult + 0.15)
            consumed = True
        if input_state.down:
            self.speed_mult = max(0.3, self.speed_mult - 0.15)
            consumed = True
        if input_state.action_l or input_state.action_r:
            self.speed_mult = 1.0
            self.samus_dir = 1
            self.samus_x = 40.0
            self.metroid_x = (40.0 - self.CHASE_DIST) % self.WORLD_SIZE
            self.samus_frame = 0
            self.metroid_frame = 0
            consumed = True
        return consumed

    def update(self, dt):
        self.time += dt
        ws = self.WORLD_SIZE
        spd = self.SAMUS_SPEED * self.speed_mult

        # Move Samus (wraps around 80px world)
        self.samus_x = (self.samus_x + self.samus_dir * spd * dt) % ws

        # Metroid target: CHASE_DIST behind Samus
        target = (self.samus_x - self.samus_dir * self.CHASE_DIST) % ws

        # Exponential smooth follow on wrapping axis
        diff = (target - self.metroid_x) % ws
        if diff > ws / 2:
            diff -= ws
        smooth = self.METROID_SMOOTH * self.speed_mult
        factor = 1.0 - math.exp(-smooth * dt)
        self.metroid_x = (self.metroid_x + diff * factor) % ws

        # Animate Samus run cycle (faster at higher speed)
        self.samus_timer += dt
        samus_interval = 0.06 / self.speed_mult
        if self.samus_timer >= samus_interval:
            self.samus_timer -= samus_interval
            frames = self.samus_r if self.samus_dir == 1 else self.samus_l
            if frames:
                self.samus_frame = (self.samus_frame + 1) % len(frames)

        # Animate Metroid pulsing
        self.metroid_timer += dt
        if self.metroid_timer >= 0.25:
            self.metroid_timer -= 0.25
            if self.metroid_sprites:
                self.metroid_frame = (self.metroid_frame + 1) % len(self.metroid_sprites)

    def _blit(self, set_pixel, sprite, sx, sy):
        """Draw sprite at screen (sx, sy), clipping to display bounds."""
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

        # 2. Metroid (draw first so Samus overlaps if they're close)
        vo = self.VIEW_OFFSET
        if self.metroid_sprites:
            mf = self.metroid_sprites[self.metroid_frame]
            _, _, mw, mh = mf
            bob = math.sin(self.time * 5.0) * 3.0
            mx = self.metroid_x - vo - mw / 2
            my = self.GROUND_Y - mh - 14 + bob
            self._blit(sp, mf, mx, my)

        # 3. Samus
        frames = self.samus_r if self.samus_dir == 1 else self.samus_l
        if frames:
            sf = frames[self.samus_frame % len(frames)]
            _, _, sw, sh = sf
            sx = self.samus_x - vo - sw / 2
            sy = self.GROUND_Y - sh
            self._blit(sp, sf, sx, sy)
