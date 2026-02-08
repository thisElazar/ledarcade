"""
Jake Music - Adventure Time
============================
Jake listens to music with his headphones on.
Button press toggles between day and night scenes.

Pixel art by Nandoo.px

Controls:
  Button  - Toggle day/night
"""

import os
from . import Visual, Display, Colors, GRID_SIZE

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class JakeMusic(Visual):
    name = "JAKE MUSIC"
    description = "Jake with headphones"
    category = "superheroes"

    GIF_DAY = "jake_music_day.gif"
    GIF_NIGHT = "jake_music_night.gif"
    BASE_INTERVAL = 0.08  # Frame timing

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.frame_timer = 0.0
        self.frame_index = 0
        self.is_night = False  # Start with day

        self.day_frames = []
        self.night_frames = []
        self._load_gifs()

    def _load_gifs(self):
        """Load both day and night GIF frames."""
        if not HAS_PIL:
            return

        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = os.path.dirname(script_dir)

        # Load day frames
        day_path = os.path.join(project_dir, "assets", self.GIF_DAY)
        if os.path.exists(day_path):
            self.day_frames = self._load_gif_frames(day_path)

        # Load night frames
        night_path = os.path.join(project_dir, "assets", self.GIF_NIGHT)
        if os.path.exists(night_path):
            self.night_frames = self._load_gif_frames(night_path)

    def _load_gif_frames(self, path):
        """Load and process a single GIF file."""
        from .gifcache import cache_frames, extract_rgb

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

        return cache_frames(path, process)

    def handle_input(self, input_state) -> bool:
        # Toggle day/night on button press
        if input_state.action_l or input_state.action_r:
            self.is_night = not self.is_night
            self.frame_index = 0  # Reset to first frame when toggling
            return True
        return False

    def update(self, dt: float):
        self.time += dt

        # Advance animation frames
        frames = self.night_frames if self.is_night else self.day_frames
        if not frames:
            return

        self.frame_timer += dt
        if self.frame_timer >= self.BASE_INTERVAL:
            self.frame_timer -= self.BASE_INTERVAL
            self.frame_index = (self.frame_index + 1) % len(frames)

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Draw current frame (day or night)
        frames = self.night_frames if self.is_night else self.day_frames
        if not frames:
            # Fallback if GIFs didn't load
            self.display.draw_text_small(10, 28, "JAKE", Colors.YELLOW)
            return

        frame = frames[self.frame_index]
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                self.display.set_pixel(x, y, frame[y * GRID_SIZE + x])
