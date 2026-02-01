"""
Link Spin - Sprite Animation
==============================
Classic Link spin attack loaded from animated GIF with
Zelda-style overworld grass background.

Controls:
  Left/Right  - Adjust speed (slow-mo to hyper spin)
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


class Link(Visual):
    name = "LINK"
    description = "Spin attack"
    category = "sprites"

    GIF_FILE = "ani_link_spin.gif"

    # Hyrule overworld grass colors
    GRASS_LIGHT = (56, 168, 56)
    GRASS_DARK = (40, 136, 40)
    GRASS_ACCENT = (72, 184, 72)

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed = 1.0
        self.frame_timer = 0.0
        self.frame_index = 0

        self.frames = []       # pixel arrays per frame
        self.alphas = []       # alpha arrays per frame
        self.durations = []    # per-frame duration in seconds

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

        from .gifcache import cache_frames, extract_rgba

        def process():
            gif = Image.open(path)
            n_frames = getattr(gif, 'n_frames', 1)
            data = []
            for i in range(n_frames):
                gif.seek(i)
                frame = gif.convert("RGBA")
                frame = frame.resize((GRID_SIZE, GRID_SIZE),
                                     Image.Resampling.NEAREST)
                pixels, alphas = extract_rgba(frame)
                duration_ms = gif.info.get('duration', 100)
                if duration_ms <= 0:
                    duration_ms = 100
                data.append((pixels, alphas, duration_ms / 1000.0))
            return data

        cached = cache_frames(path, process)
        for pixels, alphas, dur in (cached or []):
            self.frames.append(pixels)
            self.alphas.append(alphas)
            self.durations.append(dur)

    def _build_background(self):
        """Pre-render Zelda-style grass tile background."""
        self.bg_buf = [[(0, 0, 0)] * GRID_SIZE for _ in range(GRID_SIZE)]

        light = self.GRASS_LIGHT
        dark = self.GRASS_DARK
        accent = self.GRASS_ACCENT

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                # 8x8 checkerboard tiles
                tile_x = x // 8
                tile_y = y // 8
                local_x = x % 8
                local_y = y % 8

                if (tile_x + tile_y) % 2 == 0:
                    base = light
                else:
                    base = dark

                # Small grass accent tufts
                if local_x == 3 and local_y == 2:
                    self.bg_buf[y][x] = accent
                elif local_x == 6 and local_y == 5:
                    self.bg_buf[y][x] = accent
                else:
                    self.bg_buf[y][x] = base

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

        # Use per-frame GIF duration, adjusted by speed
        current_duration = self.durations[self.frame_index] / self.speed

        if self.frame_timer >= current_duration:
            self.frame_timer -= current_duration
            self.frame_index = (self.frame_index + 1) % len(self.frames)

    def draw(self):
        display = self.display
        set_pixel = display.set_pixel

        # 1. Grass background
        bg = self.bg_buf
        for y in range(GRID_SIZE):
            row = bg[y]
            for x in range(GRID_SIZE):
                set_pixel(x, y, row[x])

        # 2. Link sprite overlay (alpha-based transparency)
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
