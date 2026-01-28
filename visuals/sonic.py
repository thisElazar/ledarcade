"""
Sonic Run - Sprite Animation
==============================
Classic Sonic run cycle from 4 sprite frames with Green Hill Zone
scrolling ground and parallax clouds. Gotta go fast!

Controls:
  Left/Right  - Adjust speed (jog to sprint)
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


class Sonic(Visual):
    name = "SONIC"
    description = "Run cycle"
    category = "sprites"

    FRAME_FILES = [
        "sonic_run1.png",
        "sonic_run2.png",
        "sonic_run3.png",
        "sonic_run4.png",
    ]

    # Background threshold
    BG_THRESHOLD = 200

    # Ground level (right below Sonic's feet at y=52)
    GROUND_Y = 53

    # Green Hill Zone inspired colors
    SKY_COLOR = (112, 180, 252)
    GRASS_TOP = (0, 228, 0)
    GRASS_BASE = (0, 168, 0)
    # Checkered ground colors
    CHECK_LIGHT = (228, 164, 60)
    CHECK_DARK = (180, 108, 20)
    CLOUD_COLOR = (248, 248, 248)
    CLOUD_SHADOW = (212, 228, 248)

    # Cloud definitions: (shape, base_x, base_y, parallax)
    CLOUD_DEFS = [
        (1, 5, 4, 0.4),
        (0, 28, 8, 0.7),
        (1, 50, 2, 0.3),
        (0, 42, 11, 0.9),
    ]

    # Cloud pixel shapes
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
        self.speed = 1.5  # Sonic starts a bit faster than Mario
        self.base_interval = 0.10  # Faster base animation for a runner
        self.min_interval = 0.03
        self.frame_timer = 0.0
        self.frame_index = 0
        self.scroll_offset = 0.0

        self.frames = []
        self._load_frames()
        self._build_ground()

    def _load_frames(self):
        """Load Sonic run frames from assets."""
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
        """Pre-render Green Hill Zone checkered ground pattern."""
        gy = self.GROUND_Y
        height = GRID_SIZE - gy
        self.ground_buf = [[(0, 0, 0)] * GRID_SIZE for _ in range(height)]

        grass_top = self.GRASS_TOP
        grass_base = self.GRASS_BASE
        check_light = self.CHECK_LIGHT
        check_dark = self.CHECK_DARK

        for local_y in range(height):
            for x in range(GRID_SIZE):
                if local_y == 0:
                    self.ground_buf[local_y][x] = grass_top
                elif local_y == 1:
                    self.ground_buf[local_y][x] = grass_base
                else:
                    # Green Hill Zone checkered pattern
                    # 4x4 pixel checker squares
                    check_row = (local_y - 2) // 4
                    check_col = x // 4
                    if (check_row + check_col) % 2 == 0:
                        self.ground_buf[local_y][x] = check_light
                    else:
                        self.ground_buf[local_y][x] = check_dark

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.left:
            self.speed = max(0.3, self.speed - 0.2)
            consumed = True
        if input_state.right:
            self.speed = min(6.0, self.speed + 0.2)
            consumed = True

        if input_state.action:
            self.speed = 1.5
            self.frame_index = 0
            self.frame_timer = 0.0
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt

        # Scroll based on speed — Sonic scrolls faster than Mario
        self.scroll_offset += self.speed * 28.0 * dt

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

        # 3. Ground (scrolling checkers)
        self._draw_ground(set_pixel)

        # 4. Sonic sprite overlay
        if not self.frames:
            display.draw_text_small(4, 28, "NO FRAMES", Colors.RED)
            return

        frame = self.frames[self.frame_index]
        thresh = self.BG_THRESHOLD

        for y in range(GRID_SIZE):
            row = frame[y]
            for x in range(GRID_SIZE):
                r, g, b = row[x]
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
            cx = base_x - int(scroll * parallax)
            max_dy = max(d[1] for d in shape)

            for dx, dy in shape:
                px = (cx + dx) % GRID_SIZE
                py = base_y + dy
                if py < gy:
                    color = cloud_shadow if dy == max_dy else cloud_color
                    set_pixel(px, py, color)

    def _draw_ground(self, set_pixel):
        """Draw scrolling Green Hill Zone ground."""
        gy = self.GROUND_Y
        ground = self.ground_buf
        # Checker pattern repeats every 8px (two 4px squares)
        scroll_x = int(self.scroll_offset) % 8

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
                # Checkers scroll
                for x in range(GRID_SIZE):
                    src_x = (x + scroll_x) % GRID_SIZE
                    set_pixel(x, screen_y, row[src_x])
