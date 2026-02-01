"""
Mega Man X - Sprite Animation
==============================
Mega Man X buster shot animation loaded from animated GIF with
a sci-fi tech corridor background inspired by Maverick Hunter HQ.

Sprite art by Sanicking2.

Controls:
  Left/Right  - Adjust speed
  Space       - Reset
  Escape      - Exit
"""

import os
from . import Visual, Display, Colors, GRID_SIZE

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class MegaMan(Visual):
    name = "MEGA MAN"
    description = "Buster shot"
    category = "sprites"

    GIF_FILE = "megamanxpack2.gif"

    # Crop box: (left, upper, right, lower) to isolate the sprite
    # from the oversized 1280x720 canvas. Square crop starting at
    # the sprite's left edge, using full height for 1:1 aspect.
    CROP_BOX = (30, 0, 750, 720)

    # Background color in the source GIF (light blue)
    BG_COLOR = (153, 210, 255)
    BG_TOLERANCE = 25

    # Tech corridor palette
    WALL_DARK = (20, 24, 40)
    WALL_MID = (32, 40, 64)
    WALL_LIGHT = (44, 56, 80)
    PANEL_LINE = (56, 72, 104)
    FLOOR_DARK = (28, 32, 48)
    FLOOR_LIGHT = (40, 48, 72)
    FLOOR_STRIPE = (60, 80, 120)

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed = 1.0
        self.frame_timer = 0.0
        self.frame_index = 0

        self.frames = []
        self.alphas = []
        self.durations = []

        self._load_gif()
        self._build_background()

    def _load_gif(self):
        """Load all frames from the animated GIF."""
        if not HAS_PIL:
            return

        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = os.path.dirname(script_dir)
        assets_dir = os.path.join(project_dir, "assets")

        path = os.path.join(assets_dir, self.GIF_FILE)
        if not os.path.exists(path):
            return

        from .gifcache import cache_frames

        bg_r, bg_g, bg_b = self.BG_COLOR
        tol = self.BG_TOLERANCE

        def process():
            gif = Image.open(path)
            n_frames = getattr(gif, 'n_frames', 1)
            data = []
            for i in range(n_frames):
                gif.seek(i)
                frame = gif.convert("RGB")
                frame = frame.crop(self.CROP_BOX)
                frame = frame.resize((GRID_SIZE, GRID_SIZE),
                                     Image.Resampling.NEAREST)

                w, h = frame.size
                raw = frame.tobytes()
                pixels = []
                alphas = []
                stride = w * 3
                for y in range(h):
                    prow = []
                    arow = []
                    offset = y * stride
                    for x in range(w):
                        idx = offset + x * 3
                        r, g, b = raw[idx], raw[idx + 1], raw[idx + 2]
                        # Color-key: treat source background as transparent
                        is_bg = (abs(r - bg_r) < tol and
                                 abs(g - bg_g) < tol and
                                 abs(b - bg_b) < tol)
                        prow.append((r, g, b))
                        arow.append(0 if is_bg else 255)
                    pixels.append(prow)
                    alphas.append(arow)

                duration_ms = gif.info.get('duration', 140)
                if duration_ms <= 0:
                    duration_ms = 140
                data.append((pixels, alphas, duration_ms / 1000.0))
            return data

        cached = cache_frames(path, process)
        for pixels, alphas, dur in (cached or []):
            self.frames.append(pixels)
            self.alphas.append(alphas)
            self.durations.append(dur)

    def _build_background(self):
        """Pre-render Maverick Hunter HQ style tech corridor."""
        self.bg_buf = [[(0, 0, 0)] * GRID_SIZE for _ in range(GRID_SIZE)]

        wall_dark = self.WALL_DARK
        wall_mid = self.WALL_MID
        wall_light = self.WALL_LIGHT
        panel_line = self.PANEL_LINE
        floor_dark = self.FLOOR_DARK
        floor_light = self.FLOOR_LIGHT
        floor_stripe = self.FLOOR_STRIPE

        floor_y = 54  # floor starts here

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if y < floor_y:
                    # Wall section - vertical panels
                    panel = x // 8
                    local_x = x % 8

                    if local_x == 0 or local_x == 7:
                        # Panel seam lines
                        self.bg_buf[y][x] = panel_line
                    elif y % 16 == 0:
                        # Horizontal accent lines
                        self.bg_buf[y][x] = panel_line
                    elif panel % 2 == 0:
                        self.bg_buf[y][x] = wall_dark
                    else:
                        self.bg_buf[y][x] = wall_mid

                    # Light strip near top of each panel section
                    if 2 <= local_x <= 5 and y % 16 == 4:
                        self.bg_buf[y][x] = wall_light
                else:
                    # Floor section - metallic grating
                    floor_local = y - floor_y

                    if floor_local == 0:
                        # Floor edge highlight
                        self.bg_buf[y][x] = floor_stripe
                    elif x % 8 == 0:
                        # Floor grating lines
                        self.bg_buf[y][x] = floor_stripe
                    elif floor_local % 4 == 0:
                        self.bg_buf[y][x] = floor_stripe
                    elif (x // 4 + floor_local // 4) % 2 == 0:
                        self.bg_buf[y][x] = floor_dark
                    else:
                        self.bg_buf[y][x] = floor_light

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
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt

        if not self.frames:
            return

        self.frame_timer += dt

        current_duration = self.durations[self.frame_index] / self.speed

        if self.frame_timer >= current_duration:
            self.frame_timer -= current_duration
            self.frame_index = (self.frame_index + 1) % len(self.frames)

    def draw(self):
        display = self.display
        set_pixel = display.set_pixel

        # 1. Tech corridor background
        bg = self.bg_buf
        for y in range(GRID_SIZE):
            row = bg[y]
            for x in range(GRID_SIZE):
                set_pixel(x, y, row[x])

        # 2. Mega Man sprite overlay (color-key transparency)
        if not self.frames:
            display.draw_text_small(4, 28, "NO FRAMES", Colors.RED)
            return

        frame = self.frames[self.frame_index]
        alpha = self.alphas[self.frame_index]

        for y in range(GRID_SIZE):
            prow = frame[y]
            arow = alpha[y]
            for x in range(GRID_SIZE):
                if arow[x] > 128:
                    set_pixel(x, y, prow[x])
