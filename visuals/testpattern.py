"""
TestPattern - Pixel Test Utility
================================
Tests every single pixel in the 64x64 matrix with all primary colors.

MODE 1 - Pixel March (default):
  A cursor marches through every pixel sequentially with a colored tail.
  Current pixel: WHITE, 1 behind: RED, 2 behind: GREEN, 3 behind: BLUE

MODE 2 - Quadrant Test:
  Each quadrant shows a different color, rotating every second.
  Quick way to verify all quadrants work with all colors.

Controls:
  Space      - Toggle between Pixel March and Quadrant mode
  Left/Right - Adjust speed
  Escape     - Exit
"""

from . import Visual, Display, Colors, GRID_SIZE


class TestPattern(Visual):
    name = "PIXELTEST"
    description = "Test all pixels"
    category = "utility"

    # Total pixels in the grid
    TOTAL_PIXELS = GRID_SIZE * GRID_SIZE  # 4096

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

        # Mode: 0 = pixel march, 1 = quadrant test
        self.mode = 0

        # Current pixel index (0 to 4095) for pixel march mode
        self.pixel_index = 0.0

        # Speed: pixels per second
        self.speed = 150.0  # ~27 seconds for full cycle
        self.min_speed = 20.0
        self.max_speed = 500.0

        # Quadrant mode: color rotation index (0-3)
        self.quadrant_index = 0
        self.quadrant_timer = 0.0
        self.quadrant_cycle_time = 1.0  # 1 second per rotation

        # Colors for quadrant mode: White, Red, Green, Blue
        self.quad_colors = [Colors.WHITE, Colors.RED, Colors.GREEN, Colors.BLUE]

        # Show pixel counter
        self.show_info = True

    def _index_to_xy(self, index: int) -> tuple:
        """Convert linear pixel index to (x, y) coordinates."""
        index = index % self.TOTAL_PIXELS
        x = index % GRID_SIZE
        y = index // GRID_SIZE
        return (x, y)

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Left/Right - adjust speed
        if input_state.right:
            self.speed = min(self.max_speed, self.speed + 20.0)
            consumed = True
        if input_state.left:
            self.speed = max(self.min_speed, self.speed - 20.0)
            consumed = True

        # Toggle between pixel march and quadrant mode
        if input_state.action:
            self.mode = 1 - self.mode  # Toggle between 0 and 1
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt

        if self.mode == 0:
            # Pixel march mode: advance pixel position
            self.pixel_index += self.speed * dt

            # Wrap around when we complete the cycle
            if self.pixel_index >= self.TOTAL_PIXELS:
                self.pixel_index -= self.TOTAL_PIXELS
        else:
            # Quadrant mode: cycle colors every second
            self.quadrant_timer += dt
            if self.quadrant_timer >= self.quadrant_cycle_time:
                self.quadrant_timer -= self.quadrant_cycle_time
                self.quadrant_index = (self.quadrant_index + 1) % 4

    def draw(self):
        self.display.clear(Colors.BLACK)

        if self.mode == 0:
            # Pixel march mode
            self._draw_pixel_march()
        else:
            # Quadrant mode
            self._draw_quadrants()

    def _draw_pixel_march(self):
        """Draw the pixel march test pattern."""
        # Get current pixel position (integer)
        current = int(self.pixel_index)

        # Draw the tail: 4 pixels total (current + 3 behind)
        # Current pixel (white) - being tested now
        x, y = self._index_to_xy(current)
        self.display.set_pixel(x, y, Colors.WHITE)

        # 1 pixel behind (red)
        x, y = self._index_to_xy(current - 1)
        self.display.set_pixel(x, y, Colors.RED)

        # 2 pixels behind (green)
        x, y = self._index_to_xy(current - 2)
        self.display.set_pixel(x, y, Colors.GREEN)

        # 3 pixels behind (blue)
        x, y = self._index_to_xy(current - 3)
        self.display.set_pixel(x, y, Colors.BLUE)

        # Show pixel counter in top-left corner
        if self.show_info:
            info = f"P:{current}"
            self.display.draw_text_small(2, 2, info, Colors.DARK_GRAY)

    def _draw_quadrants(self):
        """Draw quadrant color test - each quadrant a different color, rotating."""
        half = GRID_SIZE // 2  # 32

        # Get colors for each quadrant (rotated by quadrant_index)
        # Top-left, Top-right, Bottom-left, Bottom-right
        c0 = self.quad_colors[(0 + self.quadrant_index) % 4]  # Top-left
        c1 = self.quad_colors[(1 + self.quadrant_index) % 4]  # Top-right
        c2 = self.quad_colors[(2 + self.quadrant_index) % 4]  # Bottom-left
        c3 = self.quad_colors[(3 + self.quadrant_index) % 4]  # Bottom-right

        # Draw each quadrant
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if x < half and y < half:
                    color = c0  # Top-left
                elif x >= half and y < half:
                    color = c1  # Top-right
                elif x < half and y >= half:
                    color = c2  # Bottom-left
                else:
                    color = c3  # Bottom-right
                self.display.set_pixel(x, y, color)
