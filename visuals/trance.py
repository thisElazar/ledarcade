"""
Trance - Classic demoscene tunnel effect
========================================
Flying through an infinite textured tunnel using polar coordinate mapping.

The technique precomputes angle (atan2) and distance (sqrt) from center for each
pixel. Each frame, the texture lookup is offset by time to create the illusion
of forward motion through a rotating tunnel.

Controls:
  Up/Down     - Adjust forward speed
  Left/Right  - Adjust rotation speed
  Space       - Cycle texture pattern
"""

import math
from typing import Tuple, List
from . import Visual, Display, Colors, GRID_SIZE


class Trance(Visual):
    name = "TRANCE"
    description = "Flying through"
    category = "digital"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.forward_speed = 2.0  # Faster default for more obvious motion
        self.rotation_speed = 0.15  # Slower rotation
        self.texture_index = 0
        self.palette_index = 0

        # Texture generators - focused on tunnel-like patterns
        self.textures = [
            self._texture_bricks,
            self._texture_rings,
            self._texture_grid,
            self._texture_stripes,
            self._texture_hexagons,
        ]

        # Color palettes
        self.palettes = [
            self._palette_stone,
            self._palette_cyber,
            self._palette_fire,
            self._palette_matrix,
            self._palette_purple,
        ]

        # Precompute lookup tables for angle and distance from center
        self._precompute_lookup_tables()

    def _precompute_lookup_tables(self):
        """Precompute angle and distance from center for each pixel."""
        self.angle_table = [[0.0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.distance_table = [[0.0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.raw_distance = [[0.0] * GRID_SIZE for _ in range(GRID_SIZE)]

        center_x = GRID_SIZE / 2.0
        center_y = GRID_SIZE / 2.0
        max_dist = math.sqrt(center_x * center_x + center_y * center_y)

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                dx = x - center_x + 0.5
                dy = y - center_y + 0.5

                # Angle from center (0 to 2*pi)
                angle = math.atan2(dy, dx)
                self.angle_table[y][x] = angle

                # Distance from center
                distance = math.sqrt(dx * dx + dy * dy)
                self.raw_distance[y][x] = distance / max_dist  # Normalized 0-1

                if distance < 0.5:
                    distance = 0.5
                # Use inverse distance for tunnel depth effect (stronger effect)
                self.distance_table[y][x] = 48.0 / distance

    # -------------------------------------------------------------------------
    # Texture patterns - return value 0.0 to 1.0 based on (u, v) coordinates
    # u = angle around tunnel (0-1), v = depth into tunnel (0-1)
    # -------------------------------------------------------------------------

    def _texture_bricks(self, u: float, v: float) -> float:
        """Brick pattern - classic tunnel wall texture."""
        # Scale for brick size
        brick_u = u * 8
        brick_v = v * 16

        # Offset every other row
        row = int(brick_v)
        if row % 2 == 1:
            brick_u += 0.5

        # Brick edges (mortar lines)
        u_frac = brick_u % 1.0
        v_frac = brick_v % 1.0

        # Mortar is darker
        mortar_width = 0.12
        if u_frac < mortar_width or v_frac < mortar_width:
            return 0.2
        return 0.7 + 0.3 * math.sin(brick_u * 3.14)

    def _texture_rings(self, u: float, v: float) -> float:
        """Concentric rings - like looking down a pipe."""
        # Strong depth rings with slight variation
        ring_value = math.sin(v * 24) * 0.5 + 0.5
        # Add subtle vertical lines
        vert_lines = math.sin(u * 32) * 0.1 + 0.9
        return ring_value * vert_lines

    def _texture_grid(self, u: float, v: float) -> float:
        """Grid pattern - like a sci-fi corridor."""
        # Grid lines around the tunnel
        u_line = abs(math.sin(u * 16 * math.pi))
        v_line = abs(math.sin(v * 32 * math.pi))

        # Combine for grid effect
        grid = max(u_line, v_line)
        # Threshold for sharp lines
        if grid > 0.9:
            return 1.0
        return 0.15

    def _texture_stripes(self, u: float, v: float) -> float:
        """Vertical stripes running along tunnel length."""
        # Strong vertical stripes
        stripe = (math.sin(u * 24 * math.pi) + 1.0) / 2.0
        # Add horizontal segments
        segments = 1.0 if int(v * 20) % 2 == 0 else 0.7
        return stripe * segments

    def _texture_hexagons(self, u: float, v: float) -> float:
        """Hexagonal tile pattern."""
        # Approximate hexagonal tiling
        scale_u = u * 12
        scale_v = v * 20

        # Offset pattern
        row = int(scale_v)
        if row % 2 == 1:
            scale_u += 0.5

        # Hexagon approximation using distance from centers
        cell_u = scale_u % 1.0 - 0.5
        cell_v = scale_v % 1.0 - 0.5

        dist = math.sqrt(cell_u * cell_u + cell_v * cell_v)
        if dist > 0.4:
            return 0.2  # Edge/mortar
        return 0.6 + 0.4 * (1.0 - dist / 0.4)

    # -------------------------------------------------------------------------
    # Color palettes - map texture value (0-1) to RGB color
    # -------------------------------------------------------------------------

    def _palette_stone(self, v: float) -> Tuple[int, int, int]:
        """Stone/brick tunnel: grays and browns."""
        base = int(v * 180)
        # Warm stone tint
        return (base + 20, base + 10, base)

    def _palette_cyber(self, v: float) -> Tuple[int, int, int]:
        """Cyberpunk neon: black -> blue -> cyan -> white."""
        if v < 0.33:
            t = v / 0.33
            return (0, 0, int(180 * t))
        elif v < 0.66:
            t = (v - 0.33) / 0.33
            return (0, int(255 * t), 180 + int(75 * t))
        else:
            t = (v - 0.66) / 0.34
            return (int(255 * t), 255, 255)

    def _palette_fire(self, v: float) -> Tuple[int, int, int]:
        """Fire palette: black -> red -> orange -> yellow."""
        if v < 0.33:
            t = v / 0.33
            return (int(200 * t), 0, 0)
        elif v < 0.66:
            t = (v - 0.33) / 0.33
            return (200 + int(55 * t), int(128 * t), 0)
        else:
            t = (v - 0.66) / 0.34
            return (255, 128 + int(127 * t), int(100 * t))

    def _palette_matrix(self, v: float) -> Tuple[int, int, int]:
        """Matrix green: black -> dark green -> bright green."""
        intensity = v * v  # Quadratic for more contrast
        return (0, int(255 * intensity), int(80 * intensity))

    def _palette_purple(self, v: float) -> Tuple[int, int, int]:
        """Purple haze: black -> purple -> magenta -> pink."""
        if v < 0.33:
            t = v / 0.33
            return (int(100 * t), 0, int(150 * t))
        elif v < 0.66:
            t = (v - 0.33) / 0.33
            return (100 + int(155 * t), int(50 * t), 150 + int(105 * t))
        else:
            t = (v - 0.66) / 0.34
            return (255, 50 + int(150 * t), 255)

    def handle_input(self, input_state) -> bool:
        """Handle user input for speed and texture control."""
        consumed = False

        # Space cycles texture pattern
        if (input_state.action_l or input_state.action_r):
            self.texture_index = (self.texture_index + 1) % len(self.textures)
            # Also cycle palette with texture for variety
            self.palette_index = (self.palette_index + 1) % len(self.palettes)
            consumed = True

        # Up/Down adjust forward speed
        if input_state.up:
            self.forward_speed = min(3.0, self.forward_speed + 0.1)
            consumed = True
        if input_state.down:
            self.forward_speed = max(0.1, self.forward_speed - 0.1)
            consumed = True

        # Left/Right adjust rotation speed
        if input_state.right:
            self.rotation_speed = min(2.0, self.rotation_speed + 0.1)
            consumed = True
        if input_state.left:
            self.rotation_speed = max(-2.0, self.rotation_speed - 0.1)
            consumed = True

        return consumed

    def update(self, dt: float):
        """Update animation time."""
        self.time += dt

    def draw(self):
        """Render the tunnel effect."""
        self.display.clear(Colors.BLACK)

        texture_func = self.textures[self.texture_index]
        palette_func = self.palettes[self.palette_index]

        # Animation offsets
        rotation_offset = self.time * self.rotation_speed
        depth_offset = self.time * self.forward_speed

        center_x = GRID_SIZE // 2
        center_y = GRID_SIZE // 2

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                # Get precomputed angle and distance
                angle = self.angle_table[y][x]
                distance = self.distance_table[y][x]
                raw_dist = self.raw_distance[y][x]

                # Apply animation offsets
                # u: angle (rotation around tunnel axis)
                # v: depth (distance into tunnel)
                u = (angle / (2.0 * math.pi)) + rotation_offset
                v = distance + depth_offset

                # Wrap coordinates
                u = u % 1.0
                v = v % 1.0

                # Get texture value and convert to color
                tex_value = texture_func(u, v)

                # Distance-based shading: center is dark (far away), edges are bright (close)
                # Use raw_distance which is 0 at center, 1 at corners
                # More aggressive falloff for tunnel depth effect
                shade = raw_dist ** 0.6  # Power < 1 makes walls brighter
                shade = max(0.05, min(1.0, shade))  # Clamp, keep center very dark

                tex_value *= shade

                # Very dark center circle (vanishing point)
                if raw_dist < 0.08:
                    color = (0, 0, 0)
                else:
                    color = palette_func(tex_value)

                self.display.set_pixel(x, y, color)
