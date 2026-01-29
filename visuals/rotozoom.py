"""
Rotozoom - Classic demoscene effect
===================================
A texture that rotates and zooms simultaneously. For each screen pixel, we
compute rotated/scaled UV coordinates back into a procedural texture space.

The rotation matrix is:
    u = x * cos(angle) - y * sin(angle)
    v = x * sin(angle) + y * cos(angle)

Then we scale by a time-varying zoom factor and sample from one of several
procedural texture patterns (checkerboard, XOR pattern, concentric circles, etc.)

Controls:
  Left/Right - Adjust rotation speed
  Up/Down    - Cycle color palette
  Space      - Cycle texture pattern
  Escape     - Exit
"""

import math
from typing import Tuple
from . import Visual, Display, Colors, GRID_SIZE


class Rotozoom(Visual):
    name = "ROTOZOOM"
    description = "Rotating zoom"
    category = "digital"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.rotation_speed = 0.5  # Radians per second
        self.zoom_speed = 0.8
        self.zoom_direction = 1  # 1 = zoom in/out oscillating, -1 = reversed
        self.texture_index = 0
        self.palette_index = 0

        # Texture patterns
        self.textures = [
            self._texture_checkerboard,
            self._texture_xor,
            self._texture_circles,
            self._texture_plasma,
            self._texture_spiral,
        ]

        # Color palettes
        self.palettes = [
            self._palette_classic,
            self._palette_fire,
            self._palette_cyber,
            self._palette_rainbow,
            self._palette_matrix,
        ]

        # Precompute centered coordinates for efficiency
        self.center = GRID_SIZE / 2.0
        self._precompute_coords()

    def _precompute_coords(self):
        """Precompute pixel coordinates centered at origin."""
        self.coords_x = [[0.0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.coords_y = [[0.0] * GRID_SIZE for _ in range(GRID_SIZE)]

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                # Center coordinates at (0, 0)
                self.coords_x[y][x] = (x - self.center + 0.5)
                self.coords_y[y][x] = (y - self.center + 0.5)

    # -------------------------------------------------------------------------
    # Texture patterns - return value 0.0 to 1.0 based on (u, v) coordinates
    # -------------------------------------------------------------------------

    def _texture_checkerboard(self, u: float, v: float) -> float:
        """Classic checkerboard pattern."""
        # Scale for tile size
        tile_u = int(u) & 1
        tile_v = int(v) & 1
        return 1.0 if (tile_u ^ tile_v) else 0.0

    def _texture_xor(self, u: float, v: float) -> float:
        """XOR texture - creates fractal-like interference pattern."""
        # Classic demoscene XOR pattern
        iu = int(u * 4) & 255
        iv = int(v * 4) & 255
        xor_val = (iu ^ iv) & 255
        return xor_val / 255.0

    def _texture_circles(self, u: float, v: float) -> float:
        """Concentric circles from origin."""
        dist = math.sqrt(u * u + v * v)
        # Create rings
        return (math.sin(dist * 2.0) + 1.0) / 2.0

    def _texture_plasma(self, u: float, v: float) -> float:
        """Plasma-like pattern using sine waves."""
        v1 = math.sin(u * 0.5)
        v2 = math.sin(v * 0.5)
        v3 = math.sin((u + v) * 0.35)
        v4 = math.sin(math.sqrt(u * u + v * v) * 0.5)
        return ((v1 + v2 + v3 + v4) / 4.0 + 1.0) / 2.0

    def _texture_spiral(self, u: float, v: float) -> float:
        """Spiral arms pattern."""
        angle = math.atan2(v, u)
        dist = math.sqrt(u * u + v * v)
        # Spiral: angle offset by distance
        spiral = math.sin(angle * 4 + dist * 0.5)
        return (spiral + 1.0) / 2.0

    # -------------------------------------------------------------------------
    # Color palettes - map texture value (0-1) to RGB color
    # -------------------------------------------------------------------------

    def _palette_classic(self, v: float) -> Tuple[int, int, int]:
        """Classic blue/white demoscene look."""
        if v < 0.5:
            t = v / 0.5
            return (0, 0, int(200 * t))
        else:
            t = (v - 0.5) / 0.5
            return (int(255 * t), int(255 * t), 200 + int(55 * t))

    def _palette_fire(self, v: float) -> Tuple[int, int, int]:
        """Fire palette: black -> red -> orange -> yellow."""
        if v < 0.33:
            t = v / 0.33
            return (int(255 * t), 0, 0)
        elif v < 0.66:
            t = (v - 0.33) / 0.33
            return (255, int(128 * t), 0)
        else:
            t = (v - 0.66) / 0.34
            return (255, 128 + int(127 * t), int(200 * t))

    def _palette_cyber(self, v: float) -> Tuple[int, int, int]:
        """Cyberpunk neon: magenta and cyan."""
        if v < 0.5:
            t = v / 0.5
            return (int(255 * t), 0, int(200 * t))
        else:
            t = (v - 0.5) / 0.5
            return (int(255 * (1.0 - t)), int(255 * t), 200 + int(55 * t))

    def _palette_rainbow(self, v: float) -> Tuple[int, int, int]:
        """Rainbow palette using HSV-like mapping."""
        h = v * 6.0
        i = int(h) % 6
        f = h - int(h)
        if i == 0:
            return (255, int(255 * f), 0)
        elif i == 1:
            return (int(255 * (1 - f)), 255, 0)
        elif i == 2:
            return (0, 255, int(255 * f))
        elif i == 3:
            return (0, int(255 * (1 - f)), 255)
        elif i == 4:
            return (int(255 * f), 0, 255)
        else:
            return (255, 0, int(255 * (1 - f)))

    def _palette_matrix(self, v: float) -> Tuple[int, int, int]:
        """Matrix green: black -> dark green -> bright green."""
        intensity = v * v  # Quadratic for more contrast
        return (0, int(255 * intensity), int(80 * intensity))

    def handle_input(self, input_state) -> bool:
        """Handle user input for speed and texture control."""
        consumed = False

        # Left/Right adjust rotation speed
        if input_state.right:
            self.rotation_speed = min(2.0, self.rotation_speed + 0.1)
            consumed = True
        if input_state.left:
            self.rotation_speed = max(-2.0, self.rotation_speed - 0.1)
            consumed = True

        # Up/Down cycle color palette
        if input_state.up:
            self.palette_index = (self.palette_index + 1) % len(self.palettes)
            consumed = True
        if input_state.down:
            self.palette_index = (self.palette_index - 1) % len(self.palettes)
            consumed = True

        # Space cycles texture pattern
        if (input_state.action_l or input_state.action_r):
            self.texture_index = (self.texture_index + 1) % len(self.textures)
            consumed = True

        return consumed

    def update(self, dt: float):
        """Update animation time."""
        self.time += dt

    def draw(self):
        """Render the rotozoom effect."""
        self.display.clear(Colors.BLACK)

        texture_func = self.textures[self.texture_index]
        palette_func = self.palettes[self.palette_index]

        # Calculate current rotation angle and zoom scale
        angle = self.time * self.rotation_speed
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        # Oscillating zoom between 0.5 and 3.0
        zoom_phase = self.time * self.zoom_speed * self.zoom_direction
        scale = 1.5 + math.sin(zoom_phase) * 1.2  # Zoom between 0.3 and 2.7

        # Inverse scale for texture lookup (larger scale = more zoomed in = smaller UV)
        inv_scale = 1.0 / scale

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                # Get pre-centered coordinates
                px = self.coords_x[y][x]
                py = self.coords_y[y][x]

                # Apply rotation and scale to get texture UV coordinates
                u = (px * cos_a - py * sin_a) * inv_scale
                v = (px * sin_a + py * cos_a) * inv_scale

                # Get texture value and convert to color
                tex_value = texture_func(u, v)
                color = palette_func(tex_value)

                self.display.set_pixel(x, y, color)
