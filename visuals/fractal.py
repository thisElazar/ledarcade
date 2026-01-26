"""
Fractal - Sierpinski Carpet Infinite Zoom
=========================================
Infinite zoom centered on self-similar point with color cycling per generation.

Controls:
  Space   - Toggle zoom direction (in/out)
  Up/Down - Adjust speed
  Escape  - Exit
"""

from . import Visual, Display, Colors, GRID_SIZE


# Rainbow colors for each generation
RAINBOW = [
    (255, 0, 0),      # Red
    (255, 127, 0),    # Orange
    (255, 255, 0),    # Yellow
    (0, 255, 0),      # Green
    (0, 0, 255),      # Blue
    (75, 0, 130),     # Indigo
    (148, 0, 211),    # Violet
]


class Fractal(Visual):
    name = "FRACTAL"
    description = "Infinite zoom"
    category = "digital"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.frame_idx = 0
        self.frame_accum = 0.0
        self.speed = 5.0  # Frames per second
        self.zoom_in = True
        self.generation = 0  # Which color generation we're on

        # Pre-compute zoom frames
        self.num_frames = 45  # Frames per zoom cycle (1x to 3x)
        self.frames = []
        self._compute_frames()

    def _is_in_carpet(self, x, y):
        """Check if coord is in carpet (with tiling)."""
        for _ in range(7):
            # Tile the pattern
            x = x % 1.0
            y = y % 1.0

            xi = int(x * 3)
            yi = int(y * 3)
            xi = min(2, max(0, xi))
            yi = min(2, max(0, yi))

            if xi == 1 and yi == 1:
                return False

            x = x * 3 - xi
            y = y * 3 - yi
        return True

    def _compute_frames(self):
        """Pre-compute all zoom frames centered on (0,0)."""
        self.frames = []

        for f in range(self.num_frames):
            # Zoom goes from 1 to 3 exponentially
            t = f / self.num_frames
            zoom = 3.0 ** t

            # View size
            view_size = 1.0 / zoom

            # Center on (0,0) which means screen spans from -0.5/zoom to +0.5/zoom
            half = view_size / 2.0

            # Compute frame
            frame = [[False] * GRID_SIZE for _ in range(GRID_SIZE)]

            for py in range(GRID_SIZE):
                for px in range(GRID_SIZE):
                    # Map pixel to fractal coords, centered on (0,0)
                    fx = -half + (px / GRID_SIZE) * view_size
                    fy = -half + (py / GRID_SIZE) * view_size

                    frame[py][px] = self._is_in_carpet(fx, fy)

            self.frames.append(frame)

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.action:
            self.zoom_in = not self.zoom_in
            consumed = True

        if input_state.up:
            self.speed = min(20.0, self.speed + 1.0)
            consumed = True

        if input_state.down:
            self.speed = max(1.0, self.speed - 1.0)
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt

        # Advance frame
        self.frame_accum += self.speed * dt

        while self.frame_accum >= 1.0:
            self.frame_accum -= 1.0
            if self.zoom_in:
                self.frame_idx += 1
                if self.frame_idx >= self.num_frames:
                    self.frame_idx = 0
                    self.generation = (self.generation + 1) % len(RAINBOW)
            else:
                self.frame_idx -= 1
                if self.frame_idx < 0:
                    self.frame_idx = self.num_frames - 1
                    self.generation = (self.generation - 1) % len(RAINBOW)

    def _has_neighbor(self, frame, px, py):
        """Check if pixel has at least one filled neighbor."""
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = px + dx, py + dy
                if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                    if frame[ny][nx]:
                        return True
        return False

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Get current frame
        current_frame = self.frames[self.frame_idx]

        # Color is based on generation
        color = RAINBOW[self.generation]

        for py in range(GRID_SIZE):
            for px in range(GRID_SIZE):
                if current_frame[py][px]:
                    # Only draw if pixel has at least one neighbor
                    if self._has_neighbor(current_frame, px, py):
                        self.display.set_pixel(px, py, color)
