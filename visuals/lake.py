"""
Lake - Vector flow field visual
===============================
A grid of flow lines simulating water on a lake surface.
Wind creates vortices across the field. Ships pass through
on random courses, creating wakes that disturb the flow field.

Controls:
  Up/Down    - Adjust wind strength
  Left/Right - Adjust animation speed
  Space      - Spawn a new ship
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE


class Lake(Visual):
    name = "LAKE"
    description = "Flow field lake"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.time_scale = 1.0  # Animation speed

        # Flow field grid (spacing between flow indicators)
        self.grid_spacing = 4
        self.grid_cols = GRID_SIZE // self.grid_spacing
        self.grid_rows = GRID_SIZE // self.grid_spacing

        # Wind strength (affects vortex intensity)
        self.wind_strength = 0.5

        # Generate vortex/eddy centers for natural wind patterns
        self.eddies = []
        self.generate_eddies()

        # Flow field - each cell has angle and strength
        # Add organic jitter to positions
        self.flow = []
        for row in range(self.grid_rows):
            flow_row = []
            for col in range(self.grid_cols):
                # Random offset from grid position for organic feel
                jitter_x = random.uniform(-1.5, 1.5)
                jitter_y = random.uniform(-1.5, 1.5)
                # Random phase for wobble animation
                wobble_phase = random.uniform(0, math.pi * 2)
                wobble_speed = random.uniform(0.8, 1.5)
                # Vary base line length
                length_mult = random.uniform(0.7, 1.3)

                flow_row.append({
                    'angle': 0,
                    'strength': 0.3,
                    'disturbance': 0.0,  # Wake effect
                    'wake_angle': 0,  # Angle from wake
                    'jitter_x': jitter_x,
                    'jitter_y': jitter_y,
                    'wobble_phase': wobble_phase,
                    'wobble_speed': wobble_speed,
                    'length_mult': length_mult,
                    'wave_phase': random.uniform(0, math.pi * 2),  # For wave color cycling
                })
            self.flow.append(flow_row)

        # Ships
        self.ships = []
        self.ship_timer = 0.0
        self.spawn_ship()

        # Colors - wave layers from trough to crest
        self.water_color = (15, 30, 60)
        self.flow_trough = (30, 55, 100)      # Darkest - wave trough
        self.flow_color = (60, 100, 160)       # Mid - normal
        self.flow_crest = (110, 160, 210)      # Brightest - wave crest
        self.flow_highlight = (140, 190, 230)  # Wake disturbance
        self.ship_color = (180, 140, 100)

    def generate_eddies(self):
        """Generate vortex centers for wind patterns."""
        self.eddies = []

        # Several eddies spread across the lake
        num_eddies = random.randint(4, 6)
        for _ in range(num_eddies):
            self.eddies.append({
                'x': random.uniform(10, GRID_SIZE - 10),
                'y': random.uniform(10, GRID_SIZE - 10),
                'radius': random.uniform(15, 30),
                'strength': random.uniform(0.5, 1.0),
                'direction': random.choice([-1, 1]),
                'drift_x': random.uniform(-3, 3),  # Slow drift
                'drift_y': random.uniform(-3, 3),
            })

    def spawn_ship(self):
        """Spawn a ship at a random edge heading across the lake."""
        # Pick a random edge to start from
        edge = random.randint(0, 3)

        if edge == 0:  # Top
            x = random.uniform(10, GRID_SIZE - 10)
            y = -5
            angle = random.uniform(math.pi * 0.25, math.pi * 0.75)
        elif edge == 1:  # Right
            x = GRID_SIZE + 5
            y = random.uniform(10, GRID_SIZE - 10)
            angle = random.uniform(math.pi * 0.75, math.pi * 1.25)
        elif edge == 2:  # Bottom
            x = random.uniform(10, GRID_SIZE - 10)
            y = GRID_SIZE + 5
            angle = random.uniform(-math.pi * 0.75, -math.pi * 0.25)
        else:  # Left
            x = -5
            y = random.uniform(10, GRID_SIZE - 10)
            angle = random.uniform(-math.pi * 0.25, math.pi * 0.25)

        self.ships.append({
            'x': x,
            'y': y,
            'angle': angle,
            'speed': random.uniform(15, 25),
            'size': random.uniform(2, 4),
            'wake_strength': random.uniform(0.8, 1.2),
        })

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.up:
            self.wind_strength = min(1.5, self.wind_strength + 0.05)
            consumed = True
        if input_state.down:
            self.wind_strength = max(0.0, self.wind_strength - 0.05)
            consumed = True

        if input_state.left:
            self.time_scale = max(0.0, self.time_scale - 0.1)
            consumed = True
        if input_state.right:
            self.time_scale = min(3.0, self.time_scale + 0.1)
            consumed = True

        if input_state.action:
            self.spawn_ship()
            consumed = True

        return consumed

    def update(self, dt: float):
        scaled_dt = dt * self.time_scale
        self.time += scaled_dt
        self.ship_timer += dt  # Ship spawning uses real time

        # Auto-spawn ships occasionally
        if self.ship_timer > random.uniform(5, 10):
            self.ship_timer = 0
            if len(self.ships) < 3:
                self.spawn_ship()

        # Update eddy positions (slow drift)
        for eddy in self.eddies:
            eddy['x'] += eddy['drift_x'] * scaled_dt
            eddy['y'] += eddy['drift_y'] * scaled_dt

            # Wrap around or bounce
            if eddy['x'] < 0 or eddy['x'] > GRID_SIZE:
                eddy['drift_x'] *= -1
            if eddy['y'] < 0 or eddy['y'] > GRID_SIZE:
                eddy['drift_y'] *= -1

        # Update ships and create wake
        for ship in self.ships:
            # Move ship
            ship['x'] += math.cos(ship['angle']) * ship['speed'] * scaled_dt
            ship['y'] += math.sin(ship['angle']) * ship['speed'] * scaled_dt

            # Create wake disturbance in flow field
            self.create_wake(ship, scaled_dt)

        # Remove ships that left the screen
        margin = 15
        self.ships = [s for s in self.ships if
                      -margin < s['x'] < GRID_SIZE + margin and
                      -margin < s['y'] < GRID_SIZE + margin]

        # Update flow field
        for row in range(self.grid_rows):
            for col in range(self.grid_cols):
                cell = self.flow[row][col]

                # Grid cell world position
                gx = col * self.grid_spacing + self.grid_spacing / 2
                gy = row * self.grid_spacing + self.grid_spacing / 2

                # Calculate wind angle from eddies (like Starry Night)
                flow_x = 0
                flow_y = 0

                for eddy in self.eddies:
                    dx = gx - eddy['x']
                    dy = gy - eddy['y']
                    dist = math.sqrt(dx * dx + dy * dy)

                    if dist < eddy['radius'] * 2 and dist > 0.1:
                        # Influence falls off with distance
                        influence = max(0, 1 - dist / (eddy['radius'] * 2))
                        influence = influence ** 0.6

                        # Tangent direction (perpendicular to radius) creates circular flow
                        tangent_x = -dy / dist * eddy['direction']
                        tangent_y = dx / dist * eddy['direction']

                        flow_x += tangent_x * influence * eddy['strength']
                        flow_y += tangent_y * influence * eddy['strength']

                # Add slight global drift
                flow_x += math.sin(self.time * 0.2) * 0.2
                flow_y += math.cos(self.time * 0.15) * 0.1

                # Calculate target wind angle
                wind_angle = math.atan2(flow_y, flow_x)
                wind_mag = math.sqrt(flow_x * flow_x + flow_y * flow_y) * self.wind_strength

                # Decay disturbance slowly
                cell['disturbance'] *= 0.985

                # Blend between wake angle and wind angle based on disturbance
                if cell['disturbance'] > 0.05:
                    # Wake is active - blend toward wake angle
                    cell['angle'] = self.blend_angles(cell['angle'], cell['wake_angle'],
                                                       cell['disturbance'] * scaled_dt * 3)
                else:
                    # No wake - follow wind pattern
                    cell['angle'] = self.blend_angles(cell['angle'], wind_angle, scaled_dt * 2)

                # Update strength
                target_strength = 0.2 + wind_mag * 0.4 + cell['disturbance'] * 0.6
                cell['strength'] += (target_strength - cell['strength']) * scaled_dt * 3

    def create_wake(self, ship, dt):
        """Create wake disturbance behind the ship."""
        # Wake extends behind the ship in a V pattern - larger for more persistence
        wake_length = 50
        wake_width = 35

        for row in range(self.grid_rows):
            for col in range(self.grid_cols):
                # Grid cell world position
                gx = col * self.grid_spacing + self.grid_spacing / 2
                gy = row * self.grid_spacing + self.grid_spacing / 2

                # Vector from ship to grid point
                dx = gx - ship['x']
                dy = gy - ship['y']
                dist = math.sqrt(dx * dx + dy * dy)

                if dist < 1:
                    continue

                # Check if point is in wake zone (behind ship)
                # Project onto ship's direction
                ship_dx = math.cos(ship['angle'])
                ship_dy = math.sin(ship['angle'])

                # How far behind the ship (negative = behind)
                along = dx * ship_dx + dy * ship_dy

                # How far to the side (signed)
                across_signed = dx * (-ship_dy) + dy * ship_dx
                across = abs(across_signed)

                # Wake is behind the ship and spreads out
                if along < 0 and along > -wake_length:
                    # Wake width increases with distance behind
                    wake_spread = wake_width * (-along / wake_length) ** 0.7

                    if across < wake_spread:
                        # Calculate wake influence - stronger near the ship
                        dist_factor = (1 - (-along / wake_length)) ** 0.5
                        side_factor = 1 - (across / max(1, wake_spread))
                        influence = dist_factor * side_factor * ship['wake_strength'] * dt * 4

                        cell = self.flow[row][col]

                        # Wake pushes outward from ship's path in a V shape
                        # Angle depends on which side of the wake
                        if across_signed > 0:
                            wake_angle = ship['angle'] + math.pi * 0.65
                        else:
                            wake_angle = ship['angle'] - math.pi * 0.65

                        # Store wake angle and add disturbance
                        if influence > 0.01:
                            cell['wake_angle'] = self.blend_angles(cell['wake_angle'], wake_angle, 0.5)
                            cell['disturbance'] = min(1.0, cell['disturbance'] + influence)

                # Bow wave (in front of ship)
                if along > 0 and along < 12 and dist < 15:
                    influence = (1 - along / 12) * (1 - dist / 15) * ship['wake_strength'] * dt * 3
                    cell = self.flow[row][col]

                    # Bow wave pushes outward
                    push_angle = math.atan2(dy, dx)
                    if influence > 0.01:
                        cell['wake_angle'] = push_angle
                        cell['disturbance'] = min(1.0, cell['disturbance'] + influence * 0.7)

    def blend_angles(self, a1, a2, t):
        """Blend between two angles, handling wraparound."""
        diff = a2 - a1
        while diff > math.pi:
            diff -= 2 * math.pi
        while diff < -math.pi:
            diff += 2 * math.pi
        return a1 + diff * t

    def draw(self):
        # Draw water background
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                # Subtle water variation
                noise = math.sin(x * 0.2 + self.time) * math.cos(y * 0.15 + self.time * 0.7)
                variation = int(noise * 8)
                color = (
                    max(0, min(255, self.water_color[0] + variation)),
                    max(0, min(255, self.water_color[1] + variation)),
                    max(0, min(255, self.water_color[2] + variation)),
                )
                self.display.set_pixel(x, y, color)

        # Draw flow lines
        for row in range(self.grid_rows):
            for col in range(self.grid_cols):
                self.draw_flow_line(row, col)

        # Draw ships
        for ship in self.ships:
            self.draw_ship(ship)

    def draw_flow_line(self, row, col):
        """Draw a single flow indicator."""
        cell = self.flow[row][col]

        # Center of this grid cell with jitter and wobble
        base_x = col * self.grid_spacing + self.grid_spacing // 2
        base_y = row * self.grid_spacing + self.grid_spacing // 2

        # Add jitter offset
        cx = base_x + cell['jitter_x']
        cy = base_y + cell['jitter_y']

        # Add subtle wobble animation
        wobble = math.sin(self.time * cell['wobble_speed'] + cell['wobble_phase'])
        cx += wobble * 0.5
        cy += math.cos(self.time * cell['wobble_speed'] * 0.7 + cell['wobble_phase']) * 0.5

        # Line length based on strength, with individual variation
        length = (1 + cell['strength'] * 2 + cell['disturbance'] * 1.5) * cell['length_mult']

        # Calculate line endpoints
        dx = math.cos(cell['angle']) * length
        dy = math.sin(cell['angle']) * length

        x1 = int(cx - dx)
        y1 = int(cy - dy)
        x2 = int(cx + dx)
        y2 = int(cy + dy)

        # Wave color - propagating wave pattern across the field
        # Wave moves in direction of flow angle with spatial variation
        wave_spatial = (base_x * 0.08 + base_y * 0.06)  # Spatial component
        wave_temporal = self.time * 1.5  # Time component
        wave_flow = cell['angle'] * 0.5  # Flow-influenced component
        wave_val = math.sin(wave_spatial + wave_temporal + cell['wave_phase'] + wave_flow)

        # Map wave value to color: -1 = trough, 0 = mid, 1 = crest
        if cell['disturbance'] > 0.15:
            # Wake disturbance overrides wave color
            t = min(1.0, cell['disturbance'])
            color = self.lerp_color(self.flow_crest, self.flow_highlight, t)
        elif wave_val < -0.3:
            # Trough - darkest
            t = (-wave_val - 0.3) / 0.7  # 0 to 1
            color = self.lerp_color(self.flow_color, self.flow_trough, t)
        elif wave_val > 0.3:
            # Crest - brightest
            t = (wave_val - 0.3) / 0.7  # 0 to 1
            color = self.lerp_color(self.flow_color, self.flow_crest, t)
        else:
            # Mid range
            color = self.flow_color

        # Draw the line
        self.draw_line(x1, y1, x2, y2, color)

    def draw_line(self, x1, y1, x2, y2, color):
        """Draw a line using Bresenham's algorithm."""
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        while True:
            if 0 <= x1 < GRID_SIZE and 0 <= y1 < GRID_SIZE:
                self.display.set_pixel(x1, y1, color)

            if x1 == x2 and y1 == y2:
                break

            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy

    def draw_ship(self, ship):
        """Draw a simple ship shape."""
        x, y = int(ship['x']), int(ship['y'])
        angle = ship['angle']
        size = ship['size']

        # Ship is a simple triangle/wedge shape
        # Front point
        fx = x + math.cos(angle) * size * 2
        fy = y + math.sin(angle) * size * 2

        # Back corners
        back_angle1 = angle + math.pi * 0.8
        back_angle2 = angle - math.pi * 0.8
        b1x = x + math.cos(back_angle1) * size
        b1y = y + math.sin(back_angle1) * size
        b2x = x + math.cos(back_angle2) * size
        b2y = y + math.sin(back_angle2) * size

        # Draw ship body
        self.draw_line(int(fx), int(fy), int(b1x), int(b1y), self.ship_color)
        self.draw_line(int(fx), int(fy), int(b2x), int(b2y), self.ship_color)
        self.draw_line(int(b1x), int(b1y), int(b2x), int(b2y), self.ship_color)

        # Fill center
        if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
            self.display.set_pixel(x, y, self.ship_color)

    def lerp_color(self, c1, c2, t):
        t = max(0, min(1, t))
        return (
            int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t),
        )
