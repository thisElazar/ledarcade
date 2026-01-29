"""
Boids - Flocking Swarm Simulation
=================================
Implementation of Craig Reynolds' Boids algorithm simulating flocking behavior
of birds, fish, or other swarming creatures using three simple rules:
1. Separation - Avoid crowding neighbors
2. Alignment - Steer toward average heading of neighbors
3. Cohesion - Steer toward average position of neighbors

Boids continuously spawn from the edges and flock inward.

Controls:
  Up/Down     - Adjust cohesion strength
  Left/Right  - Adjust overall speed
  Space       - Spawn new boids
"""

import random
import math
from . import Visual, Display, Colors, GRID_SIZE


class Boid:
    """A single boid agent with position and velocity."""

    def __init__(self, x: float, y: float, vx: float, vy: float):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy

    def heading(self) -> float:
        """Return heading angle in radians."""
        return math.atan2(self.vy, self.vx)

    def speed(self) -> float:
        """Return current speed."""
        return math.sqrt(self.vx * self.vx + self.vy * self.vy)


class Boids(Visual):
    name = "BOIDS"
    description = "Flocking swarm"
    category = "automata"

    # Flocking parameters
    NUM_BOIDS = 80
    PERCEPTION_RADIUS = 10.0
    SEPARATION_RADIUS = 2.5

    # Speed limits
    MIN_SPEED = 0.5
    MAX_SPEED = 3.0

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        """Reset the simulation with new random boids."""
        self.time = 0.0

        # Tunable weights for the three rules (stronger flocking)
        self.separation_weight = 1.8
        self.alignment_weight = 1.5
        self.cohesion_weight = 1.8

        # Overall speed multiplier
        self.speed_multiplier = 1.0

        # Spawn timing
        self.spawn_timer = 0.0
        self.spawn_interval = 0.15  # Spawn rate

        # Flock disruption - break up mega flocks
        self.disruption_timer = 0.0
        self.disruption_interval = 3.0  # Check for mega flocks every 3 seconds
        self.mega_flock_threshold = 12  # If this many boids cluster, disrupt some

        # Create initial boids spawned randomly
        self.boids = []
        for _ in range(self.NUM_BOIDS // 2):
            self._spawn_random()

    def _spawn_random(self):
        """Spawn a single boid at a random position with random velocity."""
        x = random.uniform(5, GRID_SIZE - 5)
        y = random.uniform(5, GRID_SIZE - 5)
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1.5, 2.5)
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed
        self.boids.append(Boid(x, y, vx, vy))

    def _disrupt_mega_flocks(self):
        """Find and break up large clusters of boids to keep population dynamic."""
        if len(self.boids) < self.mega_flock_threshold:
            return

        # Find boids with many neighbors (part of a mega flock)
        for boid in self.boids:
            neighbors = self._get_neighbors(boid, self.PERCEPTION_RADIUS * 0.8)
            if len(neighbors) >= self.mega_flock_threshold:
                # This boid is in a mega flock - give it a random velocity burst
                # to scatter some of the flock
                if random.random() < 0.3:  # Only disrupt 30% of mega-flock members
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(2.5, 3.5)
                    boid.vx = math.cos(angle) * speed
                    boid.vy = math.sin(angle) * speed

    def handle_input(self, input_state) -> bool:
        """Handle user input for adjusting parameters."""
        consumed = False

        # Space spawns new boids
        if (input_state.action_l or input_state.action_r):
            self._spawn_several()
            consumed = True

        # Up/Down to adjust cohesion
        if input_state.up:
            self.cohesion_weight = min(3.0, self.cohesion_weight + 0.2)
            consumed = True

        if input_state.down:
            self.cohesion_weight = max(0.0, self.cohesion_weight - 0.2)
            consumed = True

        # Left/Right to adjust speed
        if input_state.right:
            self.speed_multiplier = min(2.0, self.speed_multiplier + 0.1)
            consumed = True

        if input_state.left:
            self.speed_multiplier = max(0.3, self.speed_multiplier - 0.1)
            consumed = True

        return consumed

    def _spawn_several(self):
        """Spawn several new boids at random positions."""
        for _ in range(5):
            self._spawn_random()

    def _distance(self, b1: Boid, b2: Boid) -> float:
        """Calculate toroidal distance between two boids."""
        dx = abs(b1.x - b2.x)
        dy = abs(b1.y - b2.y)

        # Wrap around for toroidal distance
        if dx > GRID_SIZE / 2:
            dx = GRID_SIZE - dx
        if dy > GRID_SIZE / 2:
            dy = GRID_SIZE - dy

        return math.sqrt(dx * dx + dy * dy)

    def _toroidal_diff(self, from_val: float, to_val: float) -> float:
        """Calculate the shortest difference on a toroidal axis."""
        diff = to_val - from_val
        if diff > GRID_SIZE / 2:
            diff -= GRID_SIZE
        elif diff < -GRID_SIZE / 2:
            diff += GRID_SIZE
        return diff

    def _get_neighbors(self, boid: Boid, radius: float) -> list:
        """Get all boids within radius of the given boid."""
        neighbors = []
        for other in self.boids:
            if other is not boid:
                dist = self._distance(boid, other)
                if dist < radius:
                    neighbors.append((other, dist))
        return neighbors

    def _separation(self, boid: Boid, neighbors: list) -> tuple:
        """Rule 1: Steer to avoid crowding local flockmates."""
        steer_x, steer_y = 0.0, 0.0

        for other, dist in neighbors:
            if dist < self.SEPARATION_RADIUS and dist > 0:
                # Steer away from neighbor
                diff_x = self._toroidal_diff(other.x, boid.x)
                diff_y = self._toroidal_diff(other.y, boid.y)

                # Weight by inverse distance (closer = stronger repulsion)
                weight = 1.0 / dist
                steer_x += diff_x * weight
                steer_y += diff_y * weight

        return steer_x, steer_y

    def _alignment(self, boid: Boid, neighbors: list) -> tuple:
        """Rule 2: Steer toward average heading of local flockmates."""
        if not neighbors:
            return 0.0, 0.0

        avg_vx, avg_vy = 0.0, 0.0
        for other, _ in neighbors:
            avg_vx += other.vx
            avg_vy += other.vy

        avg_vx /= len(neighbors)
        avg_vy /= len(neighbors)

        # Steer toward average velocity
        steer_x = avg_vx - boid.vx
        steer_y = avg_vy - boid.vy

        return steer_x, steer_y

    def _cohesion(self, boid: Boid, neighbors: list) -> tuple:
        """Rule 3: Steer toward average position of local flockmates."""
        if not neighbors:
            return 0.0, 0.0

        # Calculate center of mass using toroidal coordinates
        avg_x, avg_y = 0.0, 0.0
        for other, _ in neighbors:
            avg_x += self._toroidal_diff(boid.x, other.x)
            avg_y += self._toroidal_diff(boid.y, other.y)

        avg_x /= len(neighbors)
        avg_y /= len(neighbors)

        # Steer toward center of mass
        return avg_x, avg_y

    def _limit_speed(self, boid: Boid):
        """Limit boid speed to min/max bounds."""
        speed = boid.speed()

        if speed > 0:
            if speed < self.MIN_SPEED:
                boid.vx = (boid.vx / speed) * self.MIN_SPEED
                boid.vy = (boid.vy / speed) * self.MIN_SPEED
            elif speed > self.MAX_SPEED:
                boid.vx = (boid.vx / speed) * self.MAX_SPEED
                boid.vy = (boid.vy / speed) * self.MAX_SPEED

    def update(self, dt: float):
        """Update all boids."""
        self.time += dt

        # Continuously spawn new boids randomly on screen
        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0
            # Always spawn - let natural attrition balance population
            self._spawn_random()

        # Periodically disrupt mega flocks to keep things dynamic
        self.disruption_timer += dt
        if self.disruption_timer >= self.disruption_interval:
            self.disruption_timer = 0
            self._disrupt_mega_flocks()

        # Scale dt by speed multiplier
        effective_dt = dt * self.speed_multiplier

        # Calculate new velocities for all boids
        new_velocities = []

        for boid in self.boids:
            # Get neighbors within perception radius
            neighbors = self._get_neighbors(boid, self.PERCEPTION_RADIUS)

            # Calculate steering forces from the three rules
            sep_x, sep_y = self._separation(boid, neighbors)
            ali_x, ali_y = self._alignment(boid, neighbors)
            coh_x, coh_y = self._cohesion(boid, neighbors)

            # Combine forces with weights
            accel_x = (sep_x * self.separation_weight +
                       ali_x * self.alignment_weight +
                       coh_x * self.cohesion_weight)
            accel_y = (sep_y * self.separation_weight +
                       ali_y * self.alignment_weight +
                       coh_y * self.cohesion_weight)

            # Apply acceleration to velocity
            new_vx = boid.vx + accel_x * effective_dt
            new_vy = boid.vy + accel_y * effective_dt

            new_velocities.append((new_vx, new_vy))

        # Update all boids
        for i, boid in enumerate(self.boids):
            boid.vx, boid.vy = new_velocities[i]

            # Limit speed
            self._limit_speed(boid)

            # Update position
            boid.x += boid.vx * effective_dt
            boid.y += boid.vy * effective_dt

            # Soft boundary steering - gentle nudge back toward center near edges
            # Weak enough that some boids still escape, keeping population dynamic
            margin = 6
            turn_factor = 0.15
            if boid.x < margin:
                boid.vx += turn_factor
            elif boid.x > GRID_SIZE - margin:
                boid.vx -= turn_factor
            if boid.y < margin:
                boid.vy += turn_factor
            elif boid.y > GRID_SIZE - margin:
                boid.vy -= turn_factor

        # Remove boids that go off screen - tight boundary so population stays fresh
        self.boids = [b for b in self.boids if -2 < b.x < GRID_SIZE + 2 and -2 < b.y < GRID_SIZE + 2]

        # Soft cap to prevent runaway growth
        if len(self.boids) > self.NUM_BOIDS * 1.5:
            # Remove oldest boids (first in list)
            self.boids = self.boids[-(self.NUM_BOIDS):]

    def _heading_to_color(self, heading: float) -> tuple:
        """Convert heading angle to rainbow color."""
        # Normalize heading to 0-1 range
        hue = (heading + math.pi) / (2 * math.pi)

        # HSV to RGB conversion (saturation=1, value=1)
        h = hue * 6.0
        i = int(h)
        f = h - i

        if i == 0:
            r, g, b = 1.0, f, 0.0
        elif i == 1:
            r, g, b = 1.0 - f, 1.0, 0.0
        elif i == 2:
            r, g, b = 0.0, 1.0, f
        elif i == 3:
            r, g, b = 0.0, 1.0 - f, 1.0
        elif i == 4:
            r, g, b = f, 0.0, 1.0
        else:
            r, g, b = 1.0, 0.0, 1.0 - f

        return (int(r * 255), int(g * 255), int(b * 255))

    def draw(self):
        """Draw all boids to the display."""
        self.display.clear(Colors.BLACK)

        for boid in self.boids:
            # Get pixel position
            px = int(boid.x)
            py = int(boid.y)

            # Color based on heading angle
            heading = boid.heading()
            color = self._heading_to_color(heading)
            dim_color = (color[0] // 2, color[1] // 2, color[2] // 2)

            # Draw boid as 2x2 block for visibility
            for dy in range(2):
                for dx in range(2):
                    bx, by = (px + dx) % GRID_SIZE, (py + dy) % GRID_SIZE
                    if 0 <= bx < GRID_SIZE and 0 <= by < GRID_SIZE:
                        self.display.set_pixel(bx, by, color)

            # Draw trail behind the boid (3-4 pixels showing direction)
            speed = boid.speed()
            if speed > 0.1:
                # Normalize velocity for trail direction
                trail_dx = -boid.vx / speed
                trail_dy = -boid.vy / speed

                for i in range(1, 4):
                    trail_x = int(px + trail_dx * i * 1.2) % GRID_SIZE
                    trail_y = int(py + trail_dy * i * 1.2) % GRID_SIZE
                    # Fade trail
                    fade = 1.0 - (i / 4.0)
                    trail_color = (int(color[0] * fade * 0.5),
                                   int(color[1] * fade * 0.5),
                                   int(color[2] * fade * 0.5))
                    if 0 <= trail_x < GRID_SIZE and 0 <= trail_y < GRID_SIZE:
                        self.display.set_pixel(trail_x, trail_y, trail_color)
