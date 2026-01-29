"""
Attractors - Strange attractor visualization
=============================================
Simulates chaotic dynamical systems that create beautiful, never-repeating
trajectories. Points trace the attractor with fading trails while the
view slowly rotates for a 3D effect.

Included attractors:
  - Lorenz attractor: The classic "butterfly" shape
  - Rossler attractor: A folded band structure
  - Thomas attractor: Cyclically symmetric chaos

Controls:
  Up/Down    - Cycle color palette
  Left/Right - Adjust simulation speed
  Space      - Change attractor type (auto-resets particles)
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE


class Attractors(Visual):
    name = "ATTRACTORS"
    description = "Chaotic beauty"
    category = "digital"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

        # Attractor definitions with parameters and scaling
        self.attractors = [
            {
                'name': 'Lorenz',
                'params': {'sigma': 10.0, 'rho': 28.0, 'beta': 8.0 / 3.0},
                'scale': 0.8,
                'offset': (0, 0, -25),  # Center the attractor
            },
            {
                'name': 'Rossler',
                'params': {'a': 0.2, 'b': 0.2, 'c': 5.7},
                'scale': 1.5,
                'offset': (0, 0, 0),
            },
            {
                'name': 'Thomas',
                'params': {'b': 0.208186},
                'scale': 8.0,
                'offset': (0, 0, 0),
            },
        ]
        self.current_attractor = 0

        # View rotation
        self.rotation_y = 0.0
        self.rotation_x = 0.3  # Slight tilt
        self.rotation_speed = 0.2  # Radians per second

        # Integration parameters
        self.dt_sim = 0.005  # Simulation timestep
        self.steps_per_frame = 3  # Integration steps per frame
        self.speed_multiplier = 1.0  # Time control

        # Number of particles tracing the attractor
        self.num_particles = 75

        # Trail length (number of positions to remember)
        self.trail_length = 40

        # Initialize particles
        self.init_particles()

        # Trail buffer for each particle: list of (x, y, z) positions
        self.trails = [[] for _ in range(self.num_particles)]

        # Color palettes for particles (by velocity)
        self.palettes = [
            # Ocean to fire
            [(50, 100, 255), (100, 200, 255), (150, 255, 200), (255, 255, 100), (255, 150, 50), (255, 80, 80)],
            # Neon rainbow
            [(255, 0, 100), (255, 0, 255), (100, 0, 255), (0, 100, 255), (0, 255, 200), (100, 255, 0)],
            # Fire
            [(60, 0, 0), (150, 30, 0), (255, 80, 0), (255, 150, 0), (255, 220, 50), (255, 255, 200)],
            # Ice
            [(30, 30, 80), (50, 80, 150), (80, 150, 200), (150, 220, 255), (220, 255, 255), (255, 255, 255)],
            # Matrix green
            [(0, 30, 0), (0, 80, 20), (0, 150, 50), (50, 200, 80), (100, 255, 120), (200, 255, 200)],
            # Purple plasma
            [(30, 0, 60), (80, 0, 120), (150, 50, 180), (200, 100, 220), (255, 150, 255), (255, 220, 255)],
            # Sunset
            [(50, 0, 80), (100, 20, 100), (180, 50, 80), (255, 100, 50), (255, 180, 80), (255, 240, 150)],
            # Grayscale
            [(30, 30, 30), (60, 60, 60), (100, 100, 100), (150, 150, 150), (200, 200, 200), (255, 255, 255)],
        ]
        self.current_palette = 0
        self.colors = self.palettes[self.current_palette]

        # Fade buffer for trail effect
        self.fade_buffer = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

    def init_particles(self):
        """Initialize particles with random positions near the attractor."""
        attractor = self.attractors[self.current_attractor]

        self.particles = []
        for _ in range(self.num_particles):
            # Start with small random perturbations
            if attractor['name'] == 'Lorenz':
                x = random.uniform(-1, 1)
                y = random.uniform(-1, 1)
                z = random.uniform(20, 30)
            elif attractor['name'] == 'Rossler':
                x = random.uniform(-1, 1)
                y = random.uniform(-1, 1)
                z = random.uniform(0, 1)
            else:  # Thomas
                x = random.uniform(-1, 1)
                y = random.uniform(-1, 1)
                z = random.uniform(-1, 1)

            self.particles.append([x, y, z])

        # Clear trails
        self.trails = [[] for _ in range(self.num_particles)]

    def lorenz_derivative(self, x, y, z, params):
        """Lorenz attractor: dx/dt = sigma(y-x), dy/dt = x(rho-z)-y, dz/dt = xy-beta*z"""
        sigma = params['sigma']
        rho = params['rho']
        beta = params['beta']

        dx = sigma * (y - x)
        dy = x * (rho - z) - y
        dz = x * y - beta * z

        return dx, dy, dz

    def rossler_derivative(self, x, y, z, params):
        """Rossler attractor: dx/dt = -y-z, dy/dt = x+ay, dz/dt = b+z(x-c)"""
        a = params['a']
        b = params['b']
        c = params['c']

        dx = -y - z
        dy = x + a * y
        dz = b + z * (x - c)

        return dx, dy, dz

    def thomas_derivative(self, x, y, z, params):
        """Thomas attractor: dx/dt = sin(y)-bx, dy/dt = sin(z)-by, dz/dt = sin(x)-bz"""
        b = params['b']

        dx = math.sin(y) - b * x
        dy = math.sin(z) - b * y
        dz = math.sin(x) - b * z

        return dx, dy, dz

    def get_derivative(self, x, y, z):
        """Get derivative based on current attractor."""
        attractor = self.attractors[self.current_attractor]
        params = attractor['params']

        if attractor['name'] == 'Lorenz':
            return self.lorenz_derivative(x, y, z, params)
        elif attractor['name'] == 'Rossler':
            return self.rossler_derivative(x, y, z, params)
        else:  # Thomas
            return self.thomas_derivative(x, y, z, params)

    def rk4_step(self, x, y, z, dt):
        """4th order Runge-Kutta integration step."""
        # k1
        dx1, dy1, dz1 = self.get_derivative(x, y, z)

        # k2
        dx2, dy2, dz2 = self.get_derivative(
            x + 0.5 * dt * dx1,
            y + 0.5 * dt * dy1,
            z + 0.5 * dt * dz1
        )

        # k3
        dx3, dy3, dz3 = self.get_derivative(
            x + 0.5 * dt * dx2,
            y + 0.5 * dt * dy2,
            z + 0.5 * dt * dz2
        )

        # k4
        dx4, dy4, dz4 = self.get_derivative(
            x + dt * dx3,
            y + dt * dy3,
            z + dt * dz3
        )

        # Combine
        new_x = x + (dt / 6.0) * (dx1 + 2*dx2 + 2*dx3 + dx4)
        new_y = y + (dt / 6.0) * (dy1 + 2*dy2 + 2*dy3 + dy4)
        new_z = z + (dt / 6.0) * (dz1 + 2*dz2 + 2*dz3 + dz4)

        # Calculate velocity magnitude for coloring
        velocity = math.sqrt(dx1*dx1 + dy1*dy1 + dz1*dz1)

        return new_x, new_y, new_z, velocity

    def project_3d_to_2d(self, x, y, z):
        """Project 3D point to 2D screen coordinates with rotation."""
        attractor = self.attractors[self.current_attractor]
        scale = attractor['scale']
        offset = attractor['offset']

        # Apply offset to center the attractor
        x = x + offset[0]
        y = y + offset[1]
        z = z + offset[2]

        # Rotate around Y axis
        cos_ry = math.cos(self.rotation_y)
        sin_ry = math.sin(self.rotation_y)
        x2 = x * cos_ry + z * sin_ry
        z2 = -x * sin_ry + z * cos_ry

        # Rotate around X axis (tilt)
        cos_rx = math.cos(self.rotation_x)
        sin_rx = math.sin(self.rotation_x)
        y2 = y * cos_rx - z2 * sin_rx
        z3 = y * sin_rx + z2 * cos_rx

        # Simple perspective projection
        perspective_dist = 100.0
        factor = perspective_dist / (perspective_dist + z3 * 0.5)

        # Scale and center on screen
        screen_x = int(GRID_SIZE / 2 + x2 * scale * factor)
        screen_y = int(GRID_SIZE / 2 - y2 * scale * factor)

        return screen_x, screen_y, z3

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Up/Down change color palette
        if input_state.up_pressed:
            self.current_palette = (self.current_palette + 1) % len(self.palettes)
            self.colors = self.palettes[self.current_palette]
            consumed = True
        if input_state.down_pressed:
            self.current_palette = (self.current_palette - 1) % len(self.palettes)
            self.colors = self.palettes[self.current_palette]
            consumed = True

        # Left/Right adjust simulation speed
        if input_state.left:
            self.speed_multiplier = max(0.2, self.speed_multiplier - 0.1)
            consumed = True
        if input_state.right:
            self.speed_multiplier = min(3.0, self.speed_multiplier + 0.1)
            consumed = True

        # Space changes attractor type (auto-resets particles)
        if (input_state.action_l or input_state.action_r):
            self.current_attractor = (self.current_attractor + 1) % len(self.attractors)
            self.init_particles()
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt

        # Update view rotation
        self.rotation_y += self.rotation_speed * dt

        # Integrate each particle
        for i, particle in enumerate(self.particles):
            x, y, z = particle

            # Multiple integration steps per frame for stability
            for _ in range(self.steps_per_frame):
                x, y, z, velocity = self.rk4_step(x, y, z, self.dt_sim * self.speed_multiplier)

            # Update particle position
            self.particles[i] = [x, y, z]

            # Add to trail
            self.trails[i].append((x, y, z, velocity))

            # Limit trail length
            if len(self.trails[i]) > self.trail_length:
                self.trails[i].pop(0)

    def velocity_to_color(self, velocity):
        """Map velocity to color from palette."""
        # Normalize velocity (different ranges for different attractors)
        attractor = self.attractors[self.current_attractor]

        if attractor['name'] == 'Lorenz':
            max_vel = 50.0
        elif attractor['name'] == 'Rossler':
            max_vel = 15.0
        else:  # Thomas
            max_vel = 2.0

        t = min(1.0, velocity / max_vel)

        # Interpolate between colors
        idx = t * (len(self.colors) - 1)
        idx_low = int(idx)
        idx_high = min(idx_low + 1, len(self.colors) - 1)
        frac = idx - idx_low

        c1 = self.colors[idx_low]
        c2 = self.colors[idx_high]

        return (
            int(c1[0] + (c2[0] - c1[0]) * frac),
            int(c1[1] + (c2[1] - c1[1]) * frac),
            int(c1[2] + (c2[2] - c1[2]) * frac),
        )

    def draw(self):
        # Clear with dark background
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                self.display.set_pixel(x, y, (5, 5, 15))

        # Collect all trail points with depth for sorting
        all_points = []

        for i, trail in enumerate(self.trails):
            trail_len = len(trail)
            for j, (x, y, z, velocity) in enumerate(trail):
                # Project to screen
                screen_x, screen_y, depth = self.project_3d_to_2d(x, y, z)

                # Calculate fade based on position in trail (newer = brighter)
                age_factor = (j + 1) / trail_len

                # Get base color from velocity
                base_color = self.velocity_to_color(velocity)

                # Apply age fade
                color = (
                    int(base_color[0] * age_factor),
                    int(base_color[1] * age_factor),
                    int(base_color[2] * age_factor),
                )

                all_points.append({
                    'x': screen_x,
                    'y': screen_y,
                    'depth': depth,
                    'color': color,
                    'is_head': j == trail_len - 1,  # Is this the current position?
                })

        # Sort by depth (draw far points first)
        all_points.sort(key=lambda p: p['depth'])

        # Draw all points
        for point in all_points:
            x, y = point['x'], point['y']

            if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                # Additive blending for trails
                current = self.display.get_pixel(x, y)
                new_color = (
                    min(255, current[0] + point['color'][0]),
                    min(255, current[1] + point['color'][1]),
                    min(255, current[2] + point['color'][2]),
                )
                self.display.set_pixel(x, y, new_color)

                # Make head particles brighter/larger
                if point['is_head']:
                    # Draw a small glow around head
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                                glow_intensity = 0.3 if (dx != 0 or dy != 0) else 0.5
                                current = self.display.get_pixel(nx, ny)
                                glow = (
                                    min(255, int(current[0] + point['color'][0] * glow_intensity)),
                                    min(255, int(current[1] + point['color'][1] * glow_intensity)),
                                    min(255, int(current[2] + point['color'][2] * glow_intensity)),
                                )
                                self.display.set_pixel(nx, ny, glow)
