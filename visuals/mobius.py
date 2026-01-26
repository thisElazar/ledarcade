"""
Mobius Strip - 3D rotating visual
=================================
A Möbius strip that rotates 360 degrees around the Y axis,
allowing you to view it from all angles.

Controls:
  Up/Down    - Tilt view angle
  Left/Right - Adjust rotation speed/direction
  Space      - Cycle color scheme
"""

import math
from . import Visual, Display, Colors, GRID_SIZE


class Mobius(Visual):
    name = "MOBIUS"
    description = "Rotating Mobius strip"
    category = "digital"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.rotation_y = 0.0  # Current Y rotation angle
        self.rotation_speed = 0.5  # Radians per second
        self.tilt = 0.3  # X-axis tilt for better viewing

        # Mobius strip parameters
        self.strip_radius = 20  # Main radius
        self.strip_width = 8    # Half-width of the strip

        # Resolution for rendering
        self.u_steps = 80   # Around the loop
        self.v_steps = 12   # Across the width

        # Color schemes: (edge_color, middle_color, bg_color)
        self.color_schemes = [
            ((255, 100, 180), (80, 160, 255), (10, 10, 20)),    # Pink edges, blue middle
            ((255, 200, 80), (255, 60, 60), (15, 10, 10)),      # Gold edges, red middle
            ((100, 255, 150), (50, 120, 255), (5, 15, 15)),     # Mint edges, blue middle
            ((255, 255, 255), (80, 80, 80), (0, 0, 0)),         # White edges, gray middle
            ((255, 150, 50), (150, 50, 255), (10, 5, 15)),      # Orange edges, purple middle
            ((50, 255, 255), (255, 50, 150), (10, 10, 15)),     # Cyan edges, magenta middle
        ]
        self.current_scheme = 0
        self.update_colors()

        # Pre-calculate strip points
        self.generate_strip()

    def update_colors(self):
        """Update colors from current scheme."""
        scheme = self.color_schemes[self.current_scheme]
        self.color_edge = scheme[0]    # Color at edges
        self.color_middle = scheme[1]  # Color at middle
        self.bg_color = scheme[2]      # Background

    def generate_strip(self):
        """Generate the Möbius strip surface points."""
        self.strip_points = []

        for i in range(self.u_steps):
            u = (i / self.u_steps) * 2 * math.pi  # 0 to 2π

            row = []
            for j in range(self.v_steps):
                v = (j / (self.v_steps - 1)) - 0.5  # -0.5 to 0.5
                v *= self.strip_width * 2

                # Möbius strip parametric equations
                # The half-twist comes from u/2 in the cos and sin
                x = (self.strip_radius + v * math.cos(u / 2)) * math.cos(u)
                y = (self.strip_radius + v * math.cos(u / 2)) * math.sin(u)
                z = v * math.sin(u / 2)

                # Color based on position along strip width
                t = j / (self.v_steps - 1)
                row.append({
                    'base_x': x,
                    'base_y': y,
                    'base_z': z,
                    'color_t': t,
                    'u': u,
                    'v': v,
                })

            self.strip_points.append(row)

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Up/Down adjusts tilt (visual angle)
        if input_state.up:
            self.tilt = min(1.0, self.tilt + 0.05)
            consumed = True
        if input_state.down:
            self.tilt = max(-1.0, self.tilt - 0.05)
            consumed = True

        # Left/Right adjusts rotation speed (time-based)
        if input_state.left:
            self.rotation_speed = max(-2.0, self.rotation_speed - 0.1)
            consumed = True
        if input_state.right:
            self.rotation_speed = min(2.0, self.rotation_speed + 0.1)
            consumed = True

        # Space cycles color scheme
        if input_state.action:
            self.current_scheme = (self.current_scheme + 1) % len(self.color_schemes)
            self.update_colors()
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt
        self.rotation_y += self.rotation_speed * dt

    def draw(self):
        # Clear to background
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                self.display.set_pixel(x, y, self.bg_color)

        # Transform and collect all quads with depth info
        quads = []

        cos_ry = math.cos(self.rotation_y)
        sin_ry = math.sin(self.rotation_y)
        cos_rx = math.cos(self.tilt)
        sin_rx = math.sin(self.tilt)

        num_u = len(self.strip_points)
        num_v = len(self.strip_points[0])

        # Generate all quads uniformly, including the closing seam via modulo
        for i in range(num_u):
            i_next = (i + 1) % num_u  # Wraps around for seamless closing

            for j in range(num_v - 1):
                # Get four corners of quad
                corners = [
                    self.strip_points[i][j],
                    self.strip_points[i][j + 1],
                    self.strip_points[i_next][j + 1],
                    self.strip_points[i_next][j],
                ]

                transformed = []
                total_z = 0

                for corner in corners:
                    x, y, z = corner['base_x'], corner['base_y'], corner['base_z']

                    # Rotate around Y axis
                    x2 = x * cos_ry + z * sin_ry
                    z2 = -x * sin_ry + z * cos_ry

                    # Rotate around X axis (tilt)
                    y2 = y * cos_rx - z2 * sin_rx
                    z3 = y * sin_rx + z2 * cos_rx

                    # Project to screen (orthographic with center offset)
                    screen_x = int(GRID_SIZE / 2 + x2)
                    screen_y = int(GRID_SIZE / 2 - y2)

                    transformed.append((screen_x, screen_y, z3))
                    total_z += z3

                avg_z = total_z / 4
                avg_color_t = sum(c['color_t'] for c in corners) / 4

                quads.append({
                    'corners': transformed,
                    'depth': avg_z,
                    'color_t': avg_color_t,
                })

        # Sort by depth (painter's algorithm - draw far things first)
        quads.sort(key=lambda q: q['depth'])

        # Draw quads
        for quad in quads:
            self.draw_quad(quad)

    def draw_quad(self, quad):
        """Draw a filled quadrilateral."""
        corners = quad['corners']
        color_t = quad['color_t']
        depth = quad['depth']

        # Calculate color based on position and depth for shading
        # Depth shading: further = darker
        # Strip radius is 20, so depth ranges roughly from -30 to +30
        depth_factor = (depth + 35) / 70  # Normalize depth to 0-1 range
        depth_factor = max(0.4, min(1.0, depth_factor))  # Keep minimum brightness

        # Map color_t so edges (0 and 1) are edge color, middle (0.5) is middle color
        # This makes the seam seamless since both edges are the same color
        middle_t = 1 - abs(2 * color_t - 1)  # 0 at edges, 1 at middle
        base_color = self.lerp_color(self.color_edge, self.color_middle, middle_t)

        # Apply depth shading
        color = (
            int(base_color[0] * depth_factor),
            int(base_color[1] * depth_factor),
            int(base_color[2] * depth_factor),
        )

        # Get bounding box
        xs = [c[0] for c in corners]
        ys = [c[1] for c in corners]
        min_x = max(0, min(xs))
        max_x = min(GRID_SIZE - 1, max(xs))
        min_y = max(0, min(ys))
        max_y = min(GRID_SIZE - 1, max(ys))

        # Fill the quad using scanline
        for py in range(min_y, max_y + 1):
            for px in range(min_x, max_x + 1):
                if self.point_in_quad(px, py, corners):
                    self.display.set_pixel(px, py, color)

    def point_in_quad(self, px, py, corners):
        """Check if point is inside quadrilateral - handles both winding orders."""
        n = len(corners)

        # Count cross product signs
        positive = 0
        negative = 0

        for i in range(n):
            x1, y1, _ = corners[i]
            x2, y2, _ = corners[(i + 1) % n]

            cross = (x2 - x1) * (py - y1) - (y2 - y1) * (px - x1)
            if cross > 0:
                positive += 1
            elif cross < 0:
                negative += 1

        # Point is inside if all crosses have same sign (either all positive or all negative)
        return positive == 0 or negative == 0

    def lerp_color(self, c1, c2, t):
        """Linearly interpolate between two colors."""
        t = max(0, min(1, t))
        return (
            int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t),
        )
