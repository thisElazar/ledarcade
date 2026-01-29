"""
Flux - Flow field visualization
================================
Three species of curves trace through a curl noise field, creating
elegant, ever-evolving patterns like gases or fluids mixing.

Uses curl noise (divergence-free) so flow lines never converge into
sinks or diverge from sources - they flow smoothly around each other
like streamlines in an ideal fluid.

A boundary potential creates natural circulation away from edges.

Controls:
  Up/Down    - Adjust trail length
  Left/Right - Adjust flow speed
  Space      - Cycle color palette
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE


class Flux(Visual):
    name = "FLUX"
    description = "Curl noise flow"
    category = "digital"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.time_scale = 1.0

        # Curl noise parameters
        self.noise_scale = 0.06  # Spatial frequency
        self.time_speed = 0.12   # How fast the field evolves

        # Trail fade buffer
        self.trail_buffer = [[(0, 0, 0) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

        # Trail length controls
        self.base_trail_length = 30
        self.min_trail = 5
        self.max_trail = 70

        # Color palettes - (bg_color, [species...])
        # Each species: (dark, mid, bright, speed_mult, trail_mult)
        self.palettes = [
            # Cosmic - cyan, orange, violet
            ((3, 3, 8), [
                ((15, 50, 60), (40, 120, 140), (100, 200, 220), 1.0, 1.0),
                ((60, 25, 10), (140, 55, 20), (255, 120, 50), 1.1, 0.9),
                ((40, 15, 60), (90, 40, 130), (160, 90, 210), 0.9, 1.15),
            ]),
            # Ocean - teal, blue, seafoam
            ((2, 5, 12), [
                ((10, 40, 50), (30, 100, 120), (70, 180, 200), 0.95, 1.1),
                ((15, 25, 70), (40, 60, 150), (80, 120, 220), 1.0, 1.0),
                ((20, 55, 45), (50, 130, 100), (100, 200, 160), 1.1, 0.9),
            ]),
            # Fire - ember, gold, smoke
            ((8, 3, 2), [
                ((70, 25, 5), (160, 60, 15), (255, 110, 30), 1.1, 0.9),
                ((60, 45, 10), (140, 100, 25), (230, 180, 50), 1.0, 1.0),
                ((30, 25, 25), (70, 65, 60), (130, 120, 110), 0.85, 1.2),
            ]),
            # Aurora - green, pink, blue
            ((2, 4, 8), [
                ((15, 55, 25), (40, 140, 60), (90, 220, 110), 1.0, 1.0),
                ((55, 20, 45), (130, 50, 100), (210, 100, 170), 1.05, 0.95),
                ((15, 35, 60), (40, 80, 140), (80, 150, 220), 0.95, 1.1),
            ]),
            # Neon - magenta, cyan, yellow
            ((5, 2, 8), [
                ((55, 10, 50), (130, 30, 120), (220, 60, 200), 1.05, 0.95),
                ((10, 50, 55), (30, 120, 130), (60, 210, 220), 1.0, 1.0),
                ((55, 50, 10), (130, 120, 30), (220, 200, 60), 0.95, 1.1),
            ]),
            # Forest - emerald, amber, moss
            ((3, 6, 3), [
                ((15, 50, 30), (40, 130, 70), (80, 210, 120), 1.0, 1.0),
                ((50, 35, 10), (120, 80, 25), (200, 150, 50), 1.1, 0.85),
                ((25, 40, 20), (60, 100, 50), (110, 170, 90), 0.9, 1.15),
            ]),
        ]
        self.current_palette = 0
        self.num_species = 3

        # Occupancy grid - limit curves per cell
        self.cell_size = 3  # 3x3 pixel cells
        self.grid_dim = (GRID_SIZE + self.cell_size - 1) // self.cell_size
        self.max_occupancy = 2  # Max curves per cell

        # Generate curve origins and initialize curves
        self.curve_origins = []
        self.generate_curve_origins()
        self.curves = []
        self.init_curves()

    def get_bg_color(self):
        return self.palettes[self.current_palette][0]

    def get_species_def(self, species_id):
        return self.palettes[self.current_palette][1][species_id]

    def generate_curve_origins(self):
        """Generate evenly distributed curve origins."""
        self.curve_origins = []
        min_dist = 4.5
        max_attempts = 3000
        target_count = 150
        center = GRID_SIZE / 2
        margin = 6

        for _ in range(max_attempts):
            if len(self.curve_origins) >= target_count:
                break

            # Uniform distribution within margins
            x = random.uniform(margin, GRID_SIZE - margin)
            y = random.uniform(margin, GRID_SIZE - margin)

            # Check spacing
            valid = True
            for ox, oy, _ in self.curve_origins:
                if (x - ox) ** 2 + (y - oy) ** 2 < min_dist * min_dist:
                    valid = False
                    break

            if valid:
                species = len(self.curve_origins) % self.num_species
                self.curve_origins.append((x, y, species))

    def init_curves(self):
        """Initialize curves at origins."""
        self.curves = []
        for ox, oy, species in self.curve_origins:
            # Random initial velocity direction for separation cache
            angle = random.uniform(0, math.pi * 2)
            self.curves.append({
                'x': ox,
                'y': oy,
                'origin_x': ox,
                'origin_y': oy,
                'species': species,
                'trail': [(ox, oy)],
                'trail_mult': random.uniform(0.6, 1.5),
                'speed': random.uniform(14, 22),
                'age': random.uniform(0, 8),
                'phase': random.uniform(0, math.pi * 2),
                'lifetime': random.uniform(6, 12),
                'vx': math.cos(angle),
                'vy': math.sin(angle),
            })

    # -------------------------------------------------------------------------
    # Curl Noise Flow Field
    # -------------------------------------------------------------------------

    def noise_potential(self, x, y, t):
        """
        Scalar potential field P(x,y,t).
        The curl of this gives our velocity field.
        """
        # Multi-octave noise for organic variation
        p = 0.0
        # Octave 1 - large swirls
        p += math.sin(x * 0.8 + t * 0.7) * math.cos(y * 0.9 + t * 0.5) * 1.0
        # Octave 2 - medium features
        p += math.sin(x * 1.5 - y * 0.4 + t * 0.9) * 0.5
        p += math.cos(y * 1.6 + x * 0.3 + t * 0.6) * 0.5
        # Octave 3 - fine detail
        p += math.sin(x * 2.5 + y * 2.2 + t * 1.1) * 0.25
        # Octave 4 - subtle texture
        p += math.cos(x * 3.5 - y * 1.8 + t * 0.8) * 0.15

        return p

    def boundary_potential(self, x, y):
        """
        Potential that rises near edges, creating natural circulation inward.
        Curl of a radial potential creates circular flow.
        """
        center = GRID_SIZE / 2
        # Distance from center, normalized
        dx = (x - center) / center
        dy = (y - center) / center
        r_sq = dx * dx + dy * dy

        # Potential increases toward edges (quartic for soft center, strong edges)
        return r_sq * r_sq * 2.0

    def get_curl_velocity(self, x, y):
        """
        Compute velocity as curl of potential: (dP/dy, -dP/dx)
        This is divergence-free - no sinks or sources!
        """
        # Scale position for noise lookup
        nx = x * self.noise_scale
        ny = y * self.noise_scale
        t = self.time * self.time_speed

        # Numerical derivatives with small epsilon
        eps = 0.5

        # Noise potential derivatives
        p_xp = self.noise_potential(nx + eps, ny, t)
        p_xm = self.noise_potential(nx - eps, ny, t)
        p_yp = self.noise_potential(nx, ny + eps, t)
        p_ym = self.noise_potential(nx, ny - eps, t)

        dp_dx = (p_xp - p_xm) / (2 * eps)
        dp_dy = (p_yp - p_ym) / (2 * eps)

        # Boundary potential derivatives (analytical)
        center = GRID_SIZE / 2
        bx = (x - center) / center
        by = (y - center) / center
        r_sq = bx * bx + by * by

        # d/dx of r^4 = 4*r^2 * 2*bx/center = 8*r^2*bx/center
        db_dx = 8 * r_sq * bx / center * 2.0
        db_dy = 8 * r_sq * by / center * 2.0

        # Combine potentials
        total_dp_dx = dp_dx + db_dx * 0.15  # Boundary influence
        total_dp_dy = dp_dy + db_dy * 0.15

        # Curl: vx = dP/dy, vy = -dP/dx
        vx = total_dp_dy
        vy = -total_dp_dx

        return vx, vy

    def get_separation(self, curve, vx, vy):
        """
        Detect 1D singularities and return perpendicular separation force.
        Only activates when neighbors are close AND aligned (same direction).
        Uses cached velocity from previous frame for performance.
        """
        cx, cy = curve['x'], curve['y']
        sep_x, sep_y = 0.0, 0.0

        close_dist_sq = 16.0  # 4.0 squared
        align_threshold = 0.7

        # Perpendicular to our velocity (computed once)
        perp_x, perp_y = -vy, vx

        count = 0
        max_checks = 20  # Limit iterations for performance

        for other in self.curves:
            if other is curve:
                continue

            # Quick bounding box rejection
            dx = other['x'] - cx
            if dx > 4.0 or dx < -4.0:
                continue
            dy = other['y'] - cy
            if dy > 4.0 or dy < -4.0:
                continue

            dist_sq = dx * dx + dy * dy
            if dist_sq >= close_dist_sq or dist_sq < 0.01:
                continue

            count += 1
            if count > max_checks:
                break

            # Use cached velocity direction from other curve
            ovx = other.get('vx', 0)
            ovy = other.get('vy', 0)

            # Check alignment
            alignment = abs(vx * ovx + vy * ovy)
            if alignment < align_threshold:
                continue

            # Aligned and close - compute separation
            dist = math.sqrt(dist_sq)
            nx, ny = -dx / dist, -dy / dist
            perp_dot = nx * perp_x + ny * perp_y

            strength = (1.0 - dist / 4.0) * (alignment - align_threshold) * 1.3
            sep_x += perp_x * perp_dot * strength
            sep_y += perp_y * perp_dot * strength

        return sep_x, sep_y

    # -------------------------------------------------------------------------
    # Input / Update / Draw
    # -------------------------------------------------------------------------

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.up:
            self.base_trail_length = min(self.max_trail, self.base_trail_length + 6)
            consumed = True
        if input_state.down:
            self.base_trail_length = max(self.min_trail, self.base_trail_length - 6)
            consumed = True
        if input_state.left:
            self.time_scale = max(0.3, self.time_scale - 0.15)
            consumed = True
        if input_state.right:
            self.time_scale = min(2.5, self.time_scale + 0.15)
            consumed = True
        if (input_state.action_l or input_state.action_r):
            self.current_palette = (self.current_palette + 1) % len(self.palettes)
            consumed = True
        return consumed

    def get_cell(self, x, y):
        """Get occupancy grid cell for a position."""
        cx = max(0, min(self.grid_dim - 1, int(x / self.cell_size)))
        cy = max(0, min(self.grid_dim - 1, int(y / self.cell_size)))
        return cx, cy

    def build_occupancy_grid(self):
        """Build grid counting curves per cell."""
        grid = [[0] * self.grid_dim for _ in range(self.grid_dim)]
        for curve in self.curves:
            cx, cy = self.get_cell(curve['x'], curve['y'])
            grid[cy][cx] += 1
        return grid

    def update(self, dt: float):
        scaled_dt = dt * self.time_scale
        self.time += scaled_dt

        # Fade trail buffer
        bg = self.get_bg_color()
        fade = 0.96
        inv_fade = 1.0 - fade
        for row in self.trail_buffer:
            for i in range(GRID_SIZE):
                c = row[i]
                row[i] = (
                    int(c[0] * fade + bg[0] * inv_fade),
                    int(c[1] * fade + bg[1] * inv_fade),
                    int(c[2] * fade + bg[2] * inv_fade),
                )

        # Build occupancy grid for dispersal
        occupancy = self.build_occupancy_grid()

        # Update curves
        for curve in self.curves:
            curve['age'] += scaled_dt

            # Get species traits
            species_def = self.get_species_def(curve['species'])
            speed_mult = species_def[3]
            trail_mult = species_def[4]

            # Reset if lifetime exceeded
            if curve['age'] > curve['lifetime']:
                curve['x'] = curve['origin_x']
                curve['y'] = curve['origin_y']
                curve['trail'] = [(curve['x'], curve['y'])]
                curve['age'] = 0
                curve['lifetime'] = random.uniform(6, 12)
                continue

            # Get curl noise velocity
            vx, vy = self.get_curl_velocity(curve['x'], curve['y'])

            # Add subtle individual variation
            phase = curve['phase']
            vx += math.sin(curve['age'] * 2.0 + phase) * 0.15
            vy += math.cos(curve['age'] * 2.0 + phase) * 0.15

            # Normalize velocity
            mag = math.sqrt(vx * vx + vy * vy)
            if mag > 0.001:
                vx /= mag
                vy /= mag

            # 1D singularity breaker: separate from aligned neighbors
            sep_x, sep_y = self.get_separation(curve, vx, vy)
            vx += sep_x
            vy += sep_y

            # Re-normalize after separation
            mag = math.sqrt(vx * vx + vy * vy)
            if mag > 0.001:
                vx /= mag
                vy /= mag

            # Cache velocity for next frame's separation checks
            curve['vx'] = vx
            curve['vy'] = vy

            step = curve['speed'] * speed_mult * scaled_dt
            new_x = curve['x'] + vx * step
            new_y = curve['y'] + vy * step

            # Check occupancy at destination - disperse if crowded
            dest_cx, dest_cy = self.get_cell(new_x, new_y)
            if occupancy[dest_cy][dest_cx] > self.max_occupancy:
                # Cell is crowded - add random dispersal
                disperse_angle = random.uniform(0, math.pi * 2)
                disperse_strength = 2.0 + random.uniform(0, 2.0)
                new_x += math.cos(disperse_angle) * disperse_strength
                new_y += math.sin(disperse_angle) * disperse_strength

            # Soft boundary
            margin = 3
            if new_x < margin:
                new_x = margin + (margin - new_x) * 0.5
            elif new_x > GRID_SIZE - margin:
                new_x = GRID_SIZE - margin - (new_x - (GRID_SIZE - margin)) * 0.5
            if new_y < margin:
                new_y = margin + (margin - new_y) * 0.5
            elif new_y > GRID_SIZE - margin:
                new_y = GRID_SIZE - margin - (new_y - (GRID_SIZE - margin)) * 0.5

            # Update occupancy grid for subsequent curves this frame
            old_cx, old_cy = self.get_cell(curve['x'], curve['y'])
            new_cx, new_cy = self.get_cell(new_x, new_y)
            if (old_cx, old_cy) != (new_cx, new_cy):
                occupancy[old_cy][old_cx] = max(0, occupancy[old_cy][old_cx] - 1)
                occupancy[new_cy][new_cx] += 1

            # Draw trail segment
            self.draw_trail_line(curve['x'], curve['y'], new_x, new_y, curve)

            curve['x'] = new_x
            curve['y'] = new_y

            # Update trail history
            curve['trail'].append((new_x, new_y))
            max_trail = int(self.base_trail_length * curve['trail_mult'] * trail_mult)
            while len(curve['trail']) > max_trail:
                curve['trail'].pop(0)

    def draw_trail_line(self, x1, y1, x2, y2, curve):
        """Draw trail segment with species color."""
        species_def = self.get_species_def(curve['species'])
        trail_dark, trail_mid, trail_bright = species_def[0], species_def[1], species_def[2]

        # Brightness based on age
        age_factor = 1.0 - min(1.0, curve['age'] / curve['lifetime']) * 0.4

        if age_factor > 0.7:
            color = trail_bright
        elif age_factor > 0.4:
            t = (age_factor - 0.4) / 0.3
            color = self.lerp_color(trail_mid, trail_bright, t)
        else:
            t = age_factor / 0.4
            color = self.lerp_color(trail_dark, trail_mid, t)

        # Bresenham's line
        ix1, iy1 = int(x1), int(y1)
        ix2, iy2 = int(x2), int(y2)
        dx = abs(ix2 - ix1)
        dy = abs(iy2 - iy1)
        sx = 1 if ix1 < ix2 else -1
        sy = 1 if iy1 < iy2 else -1
        err = dx - dy

        while True:
            if 0 <= ix1 < GRID_SIZE and 0 <= iy1 < GRID_SIZE:
                current = self.trail_buffer[iy1][ix1]
                self.trail_buffer[iy1][ix1] = (
                    min(255, current[0] + color[0] // 4),
                    min(255, current[1] + color[1] // 4),
                    min(255, current[2] + color[2] // 4),
                )
            if ix1 == ix2 and iy1 == iy2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                ix1 += sx
            if e2 < dx:
                err += dx
                iy1 += sy

    def draw(self):
        # Copy trail buffer to display
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                self.display.set_pixel(x, y, self.trail_buffer[y][x])

        # Draw curve heads
        for curve in self.curves:
            cx, cy = int(curve['x']), int(curve['y'])
            if 0 <= cx < GRID_SIZE and 0 <= cy < GRID_SIZE:
                species_def = self.get_species_def(curve['species'])
                self.display.set_pixel(cx, cy, species_def[2])

    def lerp_color(self, c1, c2, t):
        t = max(0, min(1, t))
        return (
            int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t),
        )
