"""
Mario Walk - Sprite Animation
==============================
Classic Mario walk cycle from 3 sprite frames with scrolling
ground and parallax clouds. Speed him up and he runs!

Controls:
  Left/Right  - Adjust speed (walk to run)
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


class Mario(Visual):
    name = "MARIO"
    description = "Walk cycle"
    category = "sprites"

    FRAME_FILES = [
        "mario_walk1.png",
        "mario_walk2.png",
        "mario_walk3.png",
    ]

    # Background threshold: pixels with R, G, B all above this are transparent
    BG_THRESHOLD = 200

    # Ground level (right below Mario's feet at y=47)
    GROUND_Y = 48

    # NES-inspired colors
    SKY_COLOR = (92, 148, 252)
    GRASS_TOP = (0, 200, 0)
    GRASS_BASE = (0, 148, 0)
    BRICK_FACE = (200, 100, 30)
    BRICK_MORTAR = (100, 50, 10)
    CLOUD_COLOR = (252, 252, 252)
    CLOUD_SHADOW = (220, 228, 252)

    # Cloud definitions: (shape, base_x, base_y, parallax)
    # Shape 0 = small, shape 1 = medium
    CLOUD_DEFS = [
        (0, 8, 6, 0.6),
        (1, 32, 10, 1.0),
        (0, 56, 4, 0.5),
    ]

    # Cloud pixel shapes (relative offsets)
    CLOUD_SHAPES = [
        # Small cloud (6w x 3h)
        [
            (1, 0), (2, 0), (3, 0), (4, 0),
            (0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1),
            (1, 2), (2, 2), (3, 2), (4, 2),
        ],
        # Medium cloud (10w x 4h)
        [
            (3, 0), (4, 0), (5, 0), (6, 0),
            (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1), (7, 1), (8, 1),
            (0, 2), (1, 2), (2, 2), (3, 2), (4, 2), (5, 2), (6, 2), (7, 2), (8, 2), (9, 2),
            (1, 3), (2, 3), (3, 3), (4, 3), (5, 3), (6, 3), (7, 3), (8, 3),
        ],
    ]

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed = 1.0
        self.base_interval = 0.18  # seconds per frame at 1x speed
        self.min_interval = 0.04
        self.frame_timer = 0.0
        self.frame_index = 0
        self.scroll_offset = 0.0  # accumulated scroll distance in pixels

        # Load frames
        self.frames = []
        self._load_frames()

        # Pre-render ground into a buffer
        self._build_ground()

    def _load_frames(self):
        """Load Mario walk frames from assets."""
        if not HAS_PIL:
            return

        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = os.path.dirname(script_dir)
        assets_dir = os.path.join(project_dir, "assets")

        for filename in self.FRAME_FILES:
            path = os.path.join(assets_dir, filename)
            if not os.path.exists(path):
                continue
            try:
                img = Image.open(path).convert("RGB")
                img = img.resize((GRID_SIZE, GRID_SIZE), Image.Resampling.NEAREST)

                pixels = []
                for y in range(GRID_SIZE):
                    row = []
                    for x in range(GRID_SIZE):
                        r, g, b = img.getpixel((x, y))
                        row.append((r, g, b))
                    pixels.append(row)
                self.frames.append(pixels)
            except Exception:
                continue

    def _build_ground(self):
        """Pre-render the ground block pattern."""
        gy = self.GROUND_Y
        height = GRID_SIZE - gy
        self.ground_buf = [[(0, 0, 0)] * GRID_SIZE for _ in range(height)]

        grass_top = self.GRASS_TOP
        grass_base = self.GRASS_BASE
        brick = self.BRICK_FACE
        mortar = self.BRICK_MORTAR

        for local_y in range(height):
            for x in range(GRID_SIZE):
                if local_y == 0:
                    self.ground_buf[local_y][x] = grass_top
                elif local_y == 1:
                    self.ground_buf[local_y][x] = grass_base
                else:
                    # Brick pattern
                    brick_row = local_y - 2
                    row_group = brick_row // 4
                    row_in_brick = brick_row % 4
                    offset = 4 if row_group % 2 else 0
                    col_in_brick = (x + offset) % 8

                    if row_in_brick == 0 or col_in_brick == 0:
                        self.ground_buf[local_y][x] = mortar
                    else:
                        self.ground_buf[local_y][x] = brick

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.left:
            self.speed = max(0.2, self.speed - 0.2)
            consumed = True
        if input_state.right:
            self.speed = min(5.0, self.speed + 0.2)
            consumed = True

        if input_state.action:
            self.speed = 1.0
            self.frame_index = 0
            self.frame_timer = 0.0
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt

        # Scroll clouds/ground based on speed
        self.scroll_offset += self.speed * 20.0 * dt

        if not self.frames:
            return

        self.frame_timer += dt

        effective_interval = max(self.base_interval / self.speed, self.min_interval)

        if self.frame_timer >= effective_interval:
            self.frame_timer -= effective_interval
            self.frame_index = (self.frame_index + 1) % len(self.frames)

    def draw(self):
        display = self.display
        set_pixel = display.set_pixel

        # 1. Sky background
        display.clear(self.SKY_COLOR)

        # 2. Clouds (parallax scrolling)
        self._draw_clouds(set_pixel)

        # 3. Ground (scrolling bricks)
        self._draw_ground(set_pixel)

        # 4. Mario sprite overlay
        if not self.frames:
            display.draw_text_small(4, 28, "NO FRAMES", Colors.RED)
            return

        frame = self.frames[self.frame_index]
        thresh = self.BG_THRESHOLD

        for y in range(GRID_SIZE):
            row = frame[y]
            for x in range(GRID_SIZE):
                r, g, b = row[x]
                # Only draw non-background sprite pixels
                if not (r > thresh and g > thresh and b > thresh):
                    set_pixel(x, y, (r, g, b))

    def _draw_clouds(self, set_pixel):
        """Draw parallax-scrolling clouds."""
        cloud_color = self.CLOUD_COLOR
        cloud_shadow = self.CLOUD_SHADOW
        scroll = self.scroll_offset
        gy = self.GROUND_Y

        for shape_idx, base_x, base_y, parallax in self.CLOUD_DEFS:
            shape = self.CLOUD_SHAPES[shape_idx]
            # Cloud x offset scrolls with parallax factor
            cx = base_x - int(scroll * parallax)

            for dx, dy in shape:
                px = (cx + dx) % GRID_SIZE
                py = base_y + dy
                if py < gy:
                    # Bottom row of cloud gets a shadow tint
                    color = cloud_shadow if dy == max(d[1] for d in shape) else cloud_color
                    set_pixel(px, py, color)

    def _draw_ground(self, set_pixel):
        """Draw scrolling ground blocks."""
        gy = self.GROUND_Y
        ground = self.ground_buf
        # Ground scrolls with the walk
        scroll_x = int(self.scroll_offset) % 8  # brick pattern repeats every 8px

        for local_y in range(len(ground)):
            screen_y = gy + local_y
            if screen_y >= GRID_SIZE:
                break
            row = ground[local_y]
            if local_y < 2:
                # Grass doesn't scroll (uniform color)
                for x in range(GRID_SIZE):
                    set_pixel(x, screen_y, row[x])
            else:
                # Bricks scroll
                for x in range(GRID_SIZE):
                    src_x = (x + scroll_x) % GRID_SIZE
                    set_pixel(x, screen_y, row[src_x])
