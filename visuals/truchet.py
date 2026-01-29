"""
Truchet Tiles - Flowing Arc Patterns
=====================================
Quarter-circle Truchet tiles create flowing organic curves and
maze-like patterns from simple random tile orientations.
Invented by Sebastien Truchet in 1704.

Controls:
  Up/Down     - Cycle color palette
  Left/Right  - Adjust speed
  Space       - Regenerate pattern (cycles tile size)
  Escape      - Exit
"""

import random
import math
from . import Visual, Display, Colors, GRID_SIZE


class Truchet(Visual):
    name = "TRUCHET"
    description = "Flowing arc tiles"
    category = "digital"

    # Available tile sizes (in pixels)
    TILE_SIZES = [4, 8, 16]

    # Color palettes: each is (name, arc_color_func, background)
    PALETTE_NAMES = ["neon", "classic", "warm", "cool", "rainbow", "ocean"]

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed = 1.0
        self.tile_size_index = 1  # Start with 8x8 tiles
        self.tile_size = self.TILE_SIZES[self.tile_size_index]
        self.palette_index = 0

        # Timer for gentle tile evolution
        self.evolve_timer = 0.0
        self.base_evolve_interval = 0.15

        # Wave mode state
        self.wave_timer = 0.0
        self.base_wave_interval = 12.0
        self.wave_active = False
        self.wave_column = 0

        # Generate the tile grid
        self._generate_grid()

        # Precompute arc lookup tables for current tile size
        self._build_arc_tables()

    def _generate_grid(self):
        """Create a grid of random tile orientations (0 or 1)."""
        cols = GRID_SIZE // self.tile_size
        rows = GRID_SIZE // self.tile_size
        self.cols = cols
        self.rows = rows
        self.tiles = [[random.randint(0, 1) for _ in range(cols)] for _ in range(rows)]

    def _build_arc_tables(self):
        """Precompute which pixels belong to arcs for each orientation."""
        s = self.tile_size
        half = s / 2.0
        # Arc thickness: thinner for small tiles, thicker for large
        if s <= 4:
            thickness = 0.9
        elif s <= 8:
            thickness = 1.4
        else:
            thickness = 2.0

        self.arc_pixels = [{}, {}]

        for ly in range(s):
            for lx in range(s):
                px = lx + 0.5  # Pixel center
                py = ly + 0.5

                # Orientation 0: corners at (0, 0) and (s, s)
                d0a = math.sqrt(px * px + py * py)
                dist0a = abs(d0a - half)
                d0b = math.sqrt((px - s) ** 2 + (py - s) ** 2)
                dist0b = abs(d0b - half)

                # Orientation 1: corners at (s, 0) and (0, s)
                d1a = math.sqrt((px - s) ** 2 + py * py)
                dist1a = abs(d1a - half)
                d1b = math.sqrt(px * px + (py - s) ** 2)
                dist1b = abs(d1b - half)

                # Orientation 0
                min_dist_0 = min(dist0a, dist0b)
                if min_dist_0 < thickness:
                    intensity = 1.0 - (min_dist_0 / thickness)
                    intensity = max(0.0, min(1.0, intensity))
                    self.arc_pixels[0][(lx, ly)] = intensity

                # Orientation 1
                min_dist_1 = min(dist1a, dist1b)
                if min_dist_1 < thickness:
                    intensity = 1.0 - (min_dist_1 / thickness)
                    intensity = max(0.0, min(1.0, intensity))
                    self.arc_pixels[1][(lx, ly)] = intensity

    def _get_palette_colors(self):
        """Return (arc_primary, arc_secondary, background) for the current palette and time."""
        palette = self.PALETTE_NAMES[self.palette_index]
        t = self.time

        # Slow color cycling phase
        phase = t * 0.3

        if palette == "neon":
            cp = math.sin(phase) * 0.5 + 0.5
            arc1 = (
                int(40 + 60 * cp),
                int(200 + 55 * (1 - cp)),
                255
            )
            arc2 = (
                255,
                int(40 + 80 * cp),
                int(180 + 75 * (1 - cp))
            )
            bg = (5, 5, 15)

        elif palette == "classic":
            warm = math.sin(phase * 0.7) * 0.15 + 0.85
            v = int(255 * warm)
            arc1 = (v, v, int(v * 0.95))
            arc2 = (v, v, int(v * 0.95))
            bg = (0, 0, 0)

        elif palette == "warm":
            cp = math.sin(phase) * 0.5 + 0.5
            arc1 = (
                255,
                int(100 + 80 * cp),
                int(20 + 30 * cp)
            )
            arc2 = (
                255,
                int(50 + 60 * (1 - cp)),
                int(10 + 20 * (1 - cp))
            )
            bg = (15, 5, 2)

        elif palette == "cool":
            cp = math.sin(phase) * 0.5 + 0.5
            arc1 = (
                int(20 + 40 * cp),
                int(120 + 100 * cp),
                int(200 + 55 * (1 - cp))
            )
            arc2 = (
                int(20 + 60 * (1 - cp)),
                int(200 + 55 * cp),
                int(100 + 80 * (1 - cp))
            )
            bg = (2, 5, 15)

        elif palette == "rainbow":
            h1 = (phase * 0.5) % 1.0
            h2 = (h1 + 0.5) % 1.0
            arc1 = self._hsv_to_rgb(h1, 1.0, 1.0)
            arc2 = self._hsv_to_rgb(h2, 1.0, 1.0)
            bg = (5, 5, 5)

        else:  # ocean
            cp = math.sin(phase * 0.8) * 0.5 + 0.5
            arc1 = (
                int(20 + 40 * cp),
                int(150 + 80 * cp),
                int(200 + 55 * (1 - cp))
            )
            arc2 = (
                int(10 + 30 * (1 - cp)),
                int(180 + 75 * cp),
                int(180 + 75 * cp)
            )
            bg = (2, 8, 20)

        return arc1, arc2, bg

    @staticmethod
    def _hsv_to_rgb(h, s, v):
        """Convert HSV (0-1 range) to RGB tuple."""
        if s == 0.0:
            iv = int(v * 255)
            return (iv, iv, iv)
        h6 = h * 6.0
        i = int(h6)
        f = h6 - i
        p = v * (1.0 - s)
        q = v * (1.0 - s * f)
        t = v * (1.0 - s * (1.0 - f))
        if i == 0:
            r, g, b = v, t, p
        elif i == 1:
            r, g, b = q, v, p
        elif i == 2:
            r, g, b = p, v, t
        elif i == 3:
            r, g, b = p, q, v
        elif i == 4:
            r, g, b = t, p, v
        else:
            r, g, b = v, p, q
        return (int(r * 255), int(g * 255), int(b * 255))

    def _lerp_color(self, c1, c2, t):
        """Linearly interpolate between two RGB colors."""
        t = max(0.0, min(1.0, t))
        return (
            int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t),
        )

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Up/Down: cycle color palette
        if input_state.up_pressed:
            self.palette_index = (self.palette_index + 1) % len(self.PALETTE_NAMES)
            consumed = True
        if input_state.down_pressed:
            self.palette_index = (self.palette_index - 1) % len(self.PALETTE_NAMES)
            consumed = True

        # Left/Right: adjust speed
        if input_state.left:
            self.speed = max(0.2, self.speed - 0.2)
            consumed = True
        if input_state.right:
            self.speed = min(3.0, self.speed + 0.2)
            consumed = True

        # Space: regenerate pattern and cycle tile size
        if (input_state.action_l or input_state.action_r):
            self.tile_size_index = (self.tile_size_index + 1) % len(self.TILE_SIZES)
            self.tile_size = self.TILE_SIZES[self.tile_size_index]
            self._generate_grid()
            self._build_arc_tables()
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt

        # Speed-adjusted evolution interval
        effective_evolve = max(self.base_evolve_interval / self.speed, 0.05)

        # Gentle evolution: re-randomize one tile at a time
        self.evolve_timer += dt
        if self.evolve_timer >= effective_evolve:
            self.evolve_timer -= effective_evolve
            # Pick a random tile and flip it
            row = random.randint(0, self.rows - 1)
            col = random.randint(0, self.cols - 1)
            self.tiles[row][col] = 1 - self.tiles[row][col]

        # Speed-adjusted wave interval
        effective_wave = max(self.base_wave_interval / self.speed, 4.0)

        # Wave sweep: periodically re-randomize column by column
        self.wave_timer += dt
        if self.wave_timer >= effective_wave:
            self.wave_active = True
            self.wave_timer = 0.0
            self.wave_column = 0

        if self.wave_active:
            cols_per_second = self.cols * 1.5 * self.speed
            cols_to_process = max(1, int(cols_per_second * dt))
            for _ in range(cols_to_process):
                if self.wave_column < self.cols:
                    for row in range(self.rows):
                        self.tiles[row][self.wave_column] = random.randint(0, 1)
                    self.wave_column += 1
                else:
                    self.wave_active = False
                    break

    def draw(self):
        arc1, arc2, bg = self._get_palette_colors()

        # Fill background
        self.display.clear(bg)

        s = self.tile_size

        # Draw each tile's arcs
        for row in range(self.rows):
            for col in range(self.cols):
                orientation = self.tiles[row][col]
                ox = col * s  # Tile origin x
                oy = row * s  # Tile origin y

                arc_lookup = self.arc_pixels[orientation]

                for (lx, ly), intensity in arc_lookup.items():
                    px = ox + lx
                    py = oy + ly
                    if px < GRID_SIZE and py < GRID_SIZE:
                        # Use tile position to blend between the two arc colors
                        blend = ((col + row) % 2)
                        if blend == 0:
                            base_color = arc1
                        else:
                            base_color = arc2

                        # Apply arc intensity for smooth edges
                        if intensity >= 0.95:
                            color = base_color
                        else:
                            color = self._lerp_color(bg, base_color, intensity)

                        self.display.set_pixel(px, py, color)
