"""
WorldMap - Pixel World Map Display
==================================
A simplified pixel art world map on the 64x64 display.

Controls:
  Up/Down    - Cycle color scheme
  Left/Right - Scroll map horizontally
  Space      - Toggle day/night terminator animation
"""

from . import Visual, Display, Colors, GRID_SIZE
import math


class WorldMap(Visual):
    name = "WORLDMAP"
    description = "Pixel world map"
    category = "utility"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.scroll_offset = 0
        self.palette_index = 0
        self.show_terminator = False

        # Color palettes: (ocean, land, ice)
        self.palettes = [
            # Classic
            ((20, 50, 120), (30, 120, 50), (200, 200, 220)),
            # Satellite
            ((10, 30, 80), (50, 80, 40), (240, 240, 250)),
            # Vintage
            ((60, 80, 100), (120, 110, 80), (180, 170, 150)),
            # Neon
            ((20, 0, 60), (0, 200, 100), (255, 100, 200)),
            # Monochrome
            ((30, 30, 40), (120, 120, 130), (200, 200, 210)),
        ]

        # Simplified world map bitmap (64x32, will be centered vertically)
        # 1 = land, 0 = ocean, 2 = ice/arctic
        self.map_data = self._create_map()

    def _create_map(self):
        """Create a simplified 64x32 world map."""
        # Initialize with ocean
        world = [[0 for _ in range(64)] for _ in range(32)]

        # Helper to set land pixels
        def land(x, y):
            if 0 <= x < 64 and 0 <= y < 32:
                world[y][x] = 1

        def ice(x, y):
            if 0 <= x < 64 and 0 <= y < 32:
                world[y][x] = 2

        # Arctic ice (top)
        for x in range(64):
            if x < 10 or x > 54 or (20 < x < 44):
                ice(x, 0)
            if 25 < x < 40:
                ice(x, 1)

        # North America
        for x in range(8, 22):
            land(x, 4)
            land(x, 5)
        for x in range(6, 24):
            land(x, 6)
            land(x, 7)
        for x in range(5, 22):
            land(x, 8)
        for x in range(6, 20):
            land(x, 9)
            land(x, 10)
        for x in range(8, 18):
            land(x, 11)
        for x in range(9, 17):
            land(x, 12)
        for x in range(10, 16):
            land(x, 13)
        # Central America
        for x in range(11, 14):
            land(x, 14)
            land(x, 15)

        # South America
        for x in range(14, 19):
            land(x, 16)
        for x in range(15, 21):
            land(x, 17)
            land(x, 18)
        for x in range(16, 22):
            land(x, 19)
            land(x, 20)
        for x in range(17, 21):
            land(x, 21)
            land(x, 22)
        for x in range(18, 20):
            land(x, 23)
            land(x, 24)
        land(18, 25)

        # Greenland
        for x in range(22, 27):
            land(x, 3)
            land(x, 4)
        for x in range(23, 26):
            land(x, 5)
            land(x, 6)

        # Europe
        for x in range(32, 38):
            land(x, 5)
        for x in range(30, 40):
            land(x, 6)
            land(x, 7)
        for x in range(32, 42):
            land(x, 8)
        for x in range(33, 40):
            land(x, 9)
        for x in range(34, 38):
            land(x, 10)

        # British Isles
        land(29, 6)
        land(29, 7)
        land(30, 7)

        # Africa
        for x in range(34, 42):
            land(x, 11)
            land(x, 12)
        for x in range(33, 44):
            land(x, 13)
            land(x, 14)
        for x in range(34, 45):
            land(x, 15)
            land(x, 16)
        for x in range(35, 44):
            land(x, 17)
            land(x, 18)
        for x in range(36, 43):
            land(x, 19)
        for x in range(37, 42):
            land(x, 20)
        for x in range(38, 41):
            land(x, 21)

        # Middle East
        for x in range(42, 48):
            land(x, 10)
            land(x, 11)
        for x in range(44, 50):
            land(x, 12)

        # Russia/Asia
        for x in range(40, 62):
            land(x, 4)
            land(x, 5)
        for x in range(42, 63):
            land(x, 6)
        for x in range(44, 64):
            land(x, 7)
        for x in range(46, 63):
            land(x, 8)
        for x in range(48, 62):
            land(x, 9)

        # China/India/SE Asia
        for x in range(50, 60):
            land(x, 10)
            land(x, 11)
        for x in range(48, 58):
            land(x, 12)
            land(x, 13)
        for x in range(50, 56):
            land(x, 14)
        for x in range(52, 58):
            land(x, 15)
        for x in range(54, 60):
            land(x, 16)

        # Japan
        land(60, 9)
        land(61, 9)
        land(61, 10)
        land(62, 10)

        # Indonesia/Philippines
        for x in range(56, 62):
            land(x, 17)
        land(57, 18)
        land(59, 18)
        land(61, 18)
        land(58, 19)
        land(60, 19)

        # Australia
        for x in range(54, 62):
            land(x, 21)
            land(x, 22)
        for x in range(55, 63):
            land(x, 23)
        for x in range(56, 62):
            land(x, 24)
        for x in range(57, 61):
            land(x, 25)

        # New Zealand
        land(63, 26)
        land(63, 27)

        # Antarctica (bottom)
        for x in range(5, 60):
            ice(x, 30)
            ice(x, 31)
        for x in range(10, 55):
            ice(x, 29)

        return world

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Scroll map
        if input_state.right:
            self.scroll_offset = (self.scroll_offset + 1) % 64
            consumed = True
        if input_state.left:
            self.scroll_offset = (self.scroll_offset - 1) % 64
            consumed = True

        # Change palette
        if input_state.up:
            self.palette_index = (self.palette_index + 1) % len(self.palettes)
            consumed = True
        if input_state.down:
            self.palette_index = (self.palette_index - 1) % len(self.palettes)
            consumed = True

        # Toggle day/night terminator
        if input_state.action:
            self.show_terminator = not self.show_terminator
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        self.display.clear(Colors.BLACK)

        ocean_color, land_color, ice_color = self.palettes[self.palette_index]

        # Calculate terminator position (day/night line)
        terminator_x = int((self.time * 2) % 64) if self.show_terminator else -1

        # Draw the map (centered vertically: 32 rows of map in 64 row display)
        y_offset = 16  # Center the 32-row map in 64-row display

        for y in range(32):
            for x in range(64):
                # Apply horizontal scroll
                map_x = (x + self.scroll_offset) % 64
                pixel_type = self.map_data[y][map_x]

                # Get base color
                if pixel_type == 0:
                    color = ocean_color
                elif pixel_type == 1:
                    color = land_color
                else:
                    color = ice_color

                # Apply day/night shading if enabled
                if self.show_terminator:
                    # Calculate distance from terminator
                    dist = abs(x - terminator_x)
                    if dist > 32:
                        dist = 64 - dist

                    # Night side is darker
                    if (x - terminator_x) % 64 > 32:
                        # Night side
                        darkness = max(0.2, 1.0 - (32 - dist) / 32 * 0.8)
                        color = (
                            int(color[0] * darkness),
                            int(color[1] * darkness),
                            int(color[2] * darkness),
                        )

                self.display.set_pixel(x, y + y_offset, color)

        # Draw subtle border lines at top and bottom of map area
        for x in range(64):
            self.display.set_pixel(x, y_offset - 1, (40, 40, 50))
            self.display.set_pixel(x, y_offset + 32, (40, 40, 50))
