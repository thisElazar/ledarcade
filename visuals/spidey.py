"""
Spider-Man Swing - Sprite Animation
=====================================
Spider-Man swings through the city on his web.
Full scene animation from an animated GIF.

Sprite art by Huard Olivier.

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


class Spidey(Visual):
    name = "SPIDEY"
    description = "Web swing"
    category = "sprites"

    GIF_FILE = "spidey_swing.gif"
    BASE_INTERVAL = 0.03  # Match original 30ms frame timing

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed = 1.0
        self.frame_timer = 0.0
        self.frame_index = 0

        self.frames = []
        self._load_gif()

    def _load_gif(self):
        """Load GIF frames, composite, crop to square, and scale to 64x64."""
        if not HAS_PIL:
            return

        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = os.path.dirname(script_dir)
        path = os.path.join(project_dir, "assets", self.GIF_FILE)
        if not os.path.exists(path):
            return

        from .gifcache import cache_frames, extract_rgb

        def process():
            gif = Image.open(path)
            orig_w, orig_h = gif.size
            sq = min(orig_w, orig_h)
            x_off = (orig_w - sq) // 2
            canvas = None
            frames = []
            for i in range(getattr(gif, 'n_frames', 1)):
                gif.seek(i)
                frame = gif.convert("RGBA")
                if canvas is None:
                    canvas = frame.copy()
                else:
                    canvas.paste(frame, (0, 0), frame)
                cropped = canvas.copy().crop((x_off, 0, x_off + sq, sq))
                scaled = cropped.resize((GRID_SIZE, GRID_SIZE),
                                        Image.Resampling.NEAREST)
                frames.append(extract_rgb(scaled))
            return frames

        self.frames = cache_frames(path, process)

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
        effective_interval = max(self.BASE_INTERVAL / self.speed, 0.02)

        if self.frame_timer >= effective_interval:
            self.frame_timer -= effective_interval
            self.frame_index = (self.frame_index + 1) % len(self.frames)

    def draw(self):
        display = self.display
        set_pixel = display.set_pixel

        if not self.frames:
            display.draw_text_small(4, 28, "NO FRAMES", Colors.RED)
            return

        frame = self.frames[self.frame_index]
        for y in range(GRID_SIZE):
            row = frame[y]
            for x in range(GRID_SIZE):
                set_pixel(x, y, row[x])
