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

MODE 3 - Full White:
  All 4096 pixels at full brightness white. Power supply stress test.

Controls:
  Button     - Cycle mode (March -> Quadrant -> Full White)
  Left/Right - Adjust speed (March/Quadrant modes)
  Hold both  - Exit (2s)
"""

from . import Visual, Display, Colors, GRID_SIZE


MODE_MARCH = 0
MODE_QUADRANT = 1
MODE_FULL_WHITE = 2
NUM_MODES = 3

MODE_NAMES = ["MARCH", "QUADRANT", "FULL WHITE"]

SPEED_LEVELS = [20, 50, 100, 150, 250, 500]


class TestPattern(Visual):
    name = "PIXEL TEST"
    description = "Test all pixels"
    category = "utility"
    custom_exit = True  # handle own exit via hold-both-buttons

    # Total pixels in the grid
    TOTAL_PIXELS = GRID_SIZE * GRID_SIZE  # 4096

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.exit_hold = 0.0

        # Mode: 0 = pixel march, 1 = quadrant test, 2 = full white
        self.mode = MODE_MARCH

        # Current pixel index (0 to 4095) for pixel march mode
        self.pixel_index = 0.0

        # Speed level (1-6)
        self.speed_level = 4  # 150 px/s default

        # Quadrant mode: color rotation index (0-3)
        self.quadrant_index = 0
        self.quadrant_timer = 0.0
        self.quadrant_cycle_time = 1.0  # 1 second per rotation

        # Colors for quadrant mode: White, Red, Green, Blue
        self.quad_colors = [Colors.WHITE, Colors.RED, Colors.GREEN, Colors.BLUE]

    def _index_to_xy(self, index: int) -> tuple:
        """Convert linear pixel index to (x, y) coordinates."""
        index = index % self.TOTAL_PIXELS
        x = index % GRID_SIZE
        y = index // GRID_SIZE
        return (x, y)

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Button cycles mode
        if input_state.action_l or input_state.action_r:
            self.mode = (self.mode + 1) % NUM_MODES
            consumed = True

        # Left/Right adjusts speed
        if input_state.right_pressed:
            self.speed_level = min(6, self.speed_level + 1)
            consumed = True
        elif input_state.left_pressed:
            self.speed_level = max(1, self.speed_level - 1)
            consumed = True

        # Store held state for exit hold tracking in update()
        self._input = input_state
        return consumed

    def update(self, dt: float):
        self.time += dt

        # Hold both buttons 2s to exit
        inp = getattr(self, '_input', None)
        if inp and inp.action_l_held and inp.action_r_held:
            self.exit_hold += dt
            if self.exit_hold >= 2.0:
                self.wants_exit = True
        else:
            self.exit_hold = 0.0

        speed = SPEED_LEVELS[self.speed_level - 1]

        if self.mode == MODE_MARCH:
            # Pixel march mode: advance pixel position
            self.pixel_index += speed * dt
            if self.pixel_index >= self.TOTAL_PIXELS:
                self.pixel_index -= self.TOTAL_PIXELS

        elif self.mode == MODE_QUADRANT:
            # Quadrant mode: cycle colors
            # Speed level affects cycle time (faster speed = faster rotation)
            self.quadrant_cycle_time = 2.0 / (self.speed_level)
            self.quadrant_timer += dt
            if self.quadrant_timer >= self.quadrant_cycle_time:
                self.quadrant_timer -= self.quadrant_cycle_time
                self.quadrant_index = (self.quadrant_index + 1) % 4

    def draw(self):
        self.display.clear(Colors.BLACK)

        if self.mode == MODE_MARCH:
            self._draw_pixel_march()
        elif self.mode == MODE_QUADRANT:
            self._draw_quadrants()
        elif self.mode == MODE_FULL_WHITE:
            self._draw_full_white()

        # Exit hold progress bar
        if self.exit_hold > 0:
            bar_w = int((self.exit_hold / 2.0) * 60)
            bar_w = min(60, bar_w)
            if bar_w > 0:
                self.display.draw_rect(2, 60, bar_w, 2, Colors.RED)

    def _draw_pixel_march(self):
        """Draw the pixel march test pattern."""
        current = int(self.pixel_index)

        # Draw the tail: 4 pixels total (current + 3 behind)
        x, y = self._index_to_xy(current)
        self.display.set_pixel(x, y, Colors.WHITE)

        x, y = self._index_to_xy(current - 1)
        self.display.set_pixel(x, y, Colors.RED)

        x, y = self._index_to_xy(current - 2)
        self.display.set_pixel(x, y, Colors.GREEN)

        x, y = self._index_to_xy(current - 3)
        self.display.set_pixel(x, y, Colors.BLUE)

        # HUD
        speed = SPEED_LEVELS[self.speed_level - 1]
        self.display.draw_text_small(2, 2, f"P:{current}", Colors.DARK_GRAY)
        self.display.draw_text_small(2, 9, f"{speed} PX/S", Colors.DARK_GRAY)

    def _draw_quadrants(self):
        """Draw quadrant color test - each quadrant a different color, rotating."""
        half = GRID_SIZE // 2

        c0 = self.quad_colors[(0 + self.quadrant_index) % 4]
        c1 = self.quad_colors[(1 + self.quadrant_index) % 4]
        c2 = self.quad_colors[(2 + self.quadrant_index) % 4]
        c3 = self.quad_colors[(3 + self.quadrant_index) % 4]

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if x < half and y < half:
                    color = c0
                elif x >= half and y < half:
                    color = c1
                elif x < half and y >= half:
                    color = c2
                else:
                    color = c3
                self.display.set_pixel(x, y, color)

        # Mode label
        self.display.draw_text_small(2, 2, "QUADRANT", (40, 40, 40))

    def _draw_full_white(self):
        """All pixels full brightness white — power supply stress test."""
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                self.display.set_pixel(x, y, Colors.WHITE)

        self.display.draw_text_small(2, 2, "FULL WHITE", (200, 200, 200))
        self.display.draw_text_small(2, 9, "STRESS TEST", (200, 200, 200))
