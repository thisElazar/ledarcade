"""
Particle Life - Emergent Multi-Species Particles
=================================================
Multiple colored particle species interact with asymmetric
attraction/repulsion forces, creating self-organizing clusters,
orbits, and molecular structures from simple rules.

Based on Jeffrey Ventrella's "Clusters" (2007), popularized by
Tom Mohr and Hunar Ahmad. Each species pair has a unique force
value, producing emergent behaviors like chasing, orbiting,
molecular bonding, and mitosis-like splitting.

Controls:
  Up/Down     - Adjust species count (changes colors)
  Left/Right  - Adjust speed
  Space       - New random rules
  Escape      - Exit
"""

import random
import math
from . import Visual, Display, Colors, GRID_SIZE


class Particle:
    """A single particle with position, velocity, and species."""

    __slots__ = ('x', 'y', 'vx', 'vy', 'species')

    def __init__(self, x: float, y: float, species: int):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.species = species


class ParticleLife(Visual):
    name = "P LIFE"
    description = "Emergent particles"
    category = "automata"

    # Bright, saturated species colors
    SPECIES_COLORS = [
        (255, 50, 50),     # Red
        (50, 255, 80),     # Green
        (60, 120, 255),    # Blue
        (255, 240, 40),    # Yellow
        (40, 240, 240),    # Cyan
        (240, 80, 240),    # Magenta
    ]

    # Default parameters
    DEFAULT_NUM_SPECIES = 4
    DEFAULT_NUM_PARTICLES = 180
    DEFAULT_INTERACTION_RADIUS = 18.0

    # Physics constants
    FRICTION = 0.95           # Velocity damping per frame
    MIN_DISTANCE = 2.0        # Prevent division-by-zero explosions
    FORCE_SCALE = 5.0         # Overall force multiplier
    MAX_SPEED = 3.0           # Velocity cap to prevent runaway

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        """Reset the simulation with new particles and rules."""
        self.time = 0.0
        self.speed = 1.0
        self.num_species = self.DEFAULT_NUM_SPECIES
        self.num_particles = self.DEFAULT_NUM_PARTICLES
        self.interaction_radius = self.DEFAULT_INTERACTION_RADIUS

        self._generate_rules()
        self._spawn_particles()

    def _generate_rules(self):
        """Generate a random NxN attraction matrix for all species pairs."""
        n = self.num_species
        self.attraction = []
        for i in range(n):
            row = []
            for j in range(n):
                row.append(random.uniform(-1.0, 1.0))
            self.attraction.append(row)

    def _spawn_particles(self):
        """Create particles distributed randomly across the grid."""
        self.particles = []
        for i in range(self.num_particles):
            species = i % self.num_species
            x = random.uniform(0, GRID_SIZE)
            y = random.uniform(0, GRID_SIZE)
            self.particles.append(Particle(x, y, species))

    def handle_input(self, input_state) -> bool:
        """Handle user input for adjusting parameters."""
        consumed = False

        # Space: regenerate rules and respawn
        if (input_state.action_l or input_state.action_r):
            self._generate_rules()
            self._spawn_particles()
            consumed = True

        # Up/Down: adjust species count (3-6)
        if input_state.up:
            if self.num_species < 6:
                self.num_species += 1
                self._generate_rules()
                self._spawn_particles()
            consumed = True

        if input_state.down:
            if self.num_species > 3:
                self.num_species -= 1
                self._generate_rules()
                self._spawn_particles()
            consumed = True

        # Left/Right: adjust speed
        if input_state.left:
            self.speed = max(0.2, self.speed - 0.2)
            consumed = True
        if input_state.right:
            self.speed = min(3.0, self.speed + 0.2)
            consumed = True

        return consumed

    def update(self, dt: float):
        """Update all particle positions and velocities."""
        self.time += dt
        scaled_dt = dt * self.speed

        particles = self.particles
        attraction = self.attraction
        radius = self.interaction_radius
        radius_sq = radius * radius
        min_dist = self.MIN_DISTANCE
        force_scale = self.FORCE_SCALE
        grid = GRID_SIZE
        half_grid = grid * 0.5

        # For each particle, accumulate forces from all others
        for p in particles:
            fx = 0.0
            fy = 0.0

            for q in particles:
                if p is q:
                    continue

                # Toroidal delta
                dx = q.x - p.x
                if dx > half_grid:
                    dx -= grid
                elif dx < -half_grid:
                    dx += grid

                dy = q.y - p.y
                if dy > half_grid:
                    dy -= grid
                elif dy < -half_grid:
                    dy += grid

                dist_sq = dx * dx + dy * dy

                # Skip if beyond interaction radius
                if dist_sq > radius_sq or dist_sq < 0.01:
                    continue

                dist = math.sqrt(dist_sq)

                if dist < min_dist:
                    # Universal short-range repulsion
                    repel = (min_dist - dist) / min_dist
                    inv_dist = 1.0 / dist
                    fx -= dx * inv_dist * repel * force_scale
                    fy -= dy * inv_dist * repel * force_scale
                else:
                    # Attraction/repulsion zone
                    g = attraction[p.species][q.species]

                    # Normalized distance within the interaction zone [0, 1]
                    norm_dist = (dist - min_dist) / (radius - min_dist)

                    # Bell-shaped force envelope
                    if norm_dist < 0.3:
                        envelope = norm_dist / 0.3
                    else:
                        envelope = (1.0 - norm_dist) / 0.7

                    force_magnitude = g * envelope * force_scale
                    inv_dist = 1.0 / dist
                    fx += dx * inv_dist * force_magnitude
                    fy += dy * inv_dist * force_magnitude

            # Apply accumulated force to velocity
            p.vx += fx * scaled_dt
            p.vy += fy * scaled_dt

            # Clamp velocity to prevent runaway
            speed_sq = p.vx * p.vx + p.vy * p.vy
            max_spd = self.MAX_SPEED
            if speed_sq > max_spd * max_spd:
                speed = math.sqrt(speed_sq)
                p.vx = (p.vx / speed) * max_spd
                p.vy = (p.vy / speed) * max_spd

        # Update positions and apply friction
        friction = self.FRICTION
        for p in particles:
            # Apply friction (damping)
            p.vx *= friction
            p.vy *= friction

            # Update position
            p.x += p.vx
            p.y += p.vy

            # Toroidal wrapping
            p.x %= grid
            p.y %= grid

    def draw(self):
        """Draw all particles to the display."""
        self.display.clear(Colors.BLACK)

        colors = self.SPECIES_COLORS

        for p in self.particles:
            px = int(p.x) % GRID_SIZE
            py = int(p.y) % GRID_SIZE
            color = colors[p.species]

            self.display.set_pixel(px, py, color)

            # Draw a faint glow around faster-moving particles for visual richness
            speed_sq = p.vx * p.vx + p.vy * p.vy
            if speed_sq > 0.5:
                # Dim secondary pixel in direction of movement
                glow_r = color[0] // 3
                glow_g = color[1] // 3
                glow_b = color[2] // 3
                glow = (glow_r, glow_g, glow_b)

                # Trail pixel behind the particle
                trail_x = int(p.x - p.vx * 0.8) % GRID_SIZE
                trail_y = int(p.y - p.vy * 0.8) % GRID_SIZE
                self.display.set_pixel(trail_x, trail_y, glow)
