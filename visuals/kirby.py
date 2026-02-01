"""
Kirby Eats - Sprite Animation
===============================
Kirby waits by a Dreamland tree, then inhales a passing Waddle Dee.
Full scene animation from an animated GIF.

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


class Kirby(Visual):
    name = "KIRBY"
    description = "Inhale!"
    category = "sprites"

    GIF_FILE = "kirby_eats.gif"
    BASE_INTERVAL = 0.10
    CROP_SIZE = 332  # Square crop from the left of the 500x332 GIF

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
        """Load GIF frames, compositing with disposal=1, crop and scale."""
        if not HAS_PIL:
            return

        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = os.path.dirname(script_dir)
        path = os.path.join(project_dir, "assets", self.GIF_FILE)
        if not os.path.exists(path):
            return

        try:
            gif = Image.open(path)
            canvas = None

            for i in range(getattr(gif, 'n_frames', 1)):
                gif.seek(i)
                frame = gif.convert("RGBA")

                if canvas is None:
                    canvas = frame.copy()
                else:
                    canvas.paste(frame, (0, 0), frame)

                cropped = canvas.copy().crop((0, 0, self.CROP_SIZE, self.CROP_SIZE))
                scaled = cropped.resize((GRID_SIZE, GRID_SIZE),
                                        Image.Resampling.NEAREST)

                pixels = []
                for y in range(GRID_SIZE):
                    row = []
                    for x in range(GRID_SIZE):
                        r, g, b, a = scaled.getpixel((x, y))
                        row.append((r, g, b))
                    pixels.append(row)
                self.frames.append(pixels)
        except Exception:
            pass

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
