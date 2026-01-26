"""
Lava Lamp - Classic blob simulation
===================================
Blobs naturally rise and fall with convection currents.

Controls:
  Space   - Cycle color scheme
  Escape  - Exit
"""

import random
import math
from . import Visual, Display, Colors, GRID_SIZE


# Classic lava lamp color schemes: (blob_color, background_color)
COLOR_SCHEMES = [
    ((255, 100, 0), (20, 0, 60)),      # Orange on purple
    ((255, 50, 50), (20, 20, 80)),     # Red on blue
    ((50, 255, 50), (20, 20, 60)),     # Green on purple
    ((255, 255, 50), (80, 20, 20)),    # Yellow on dark red
    ((50, 200, 255), (60, 20, 60)),    # Cyan on purple
    ((255, 100, 200), (20, 40, 20)),   # Pink on dark green
]


class Blob:
    """A single lava blob."""
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.radius = 5.0
        self.phase = 0.0  # For wobble


class Lava(Visual):
    name = "LAVA"
    description = "Lava lamp blobs"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.scheme_idx = 0

        # Create blobs - bigger and more
        self.blobs = []
        for _ in range(13):
            blob = Blob()
            blob.x = random.uniform(12, GRID_SIZE - 12)
            blob.y = random.uniform(8, GRID_SIZE - 8)
            blob.radius = random.uniform(8, 20)
            blob.phase = random.uniform(0, math.pi * 2)
            blob.vy = random.uniform(-5, 5)
            self.blobs.append(blob)

    def handle_input(self, input_state) -> bool:
        if input_state.action:
            self.scheme_idx = (self.scheme_idx + 1) % len(COLOR_SCHEMES)
            return True
        return False

    def update(self, dt: float):
        self.time += dt

        center_x = GRID_SIZE / 2
        center_y = GRID_SIZE / 2

        for blob in self.blobs:
            # Update phase for wobble
            blob.phase += dt * 2

            # CONVECTION CURRENT: Circular motion like real lava lamp
            # - Up in the center (heated by bulb below)
            # - Down at the edges (cooled by glass walls)

            # How far from center horizontally (normalized -1 to 1)
            x_offset = (blob.x - center_x) / center_x

            # Vertical convection force (gentler)
            if abs(x_offset) < 0.4:
                # Near center - rise (stronger near bottom)
                rise_strength = 4 + (blob.y - center_y) * 0.1
                blob.vy -= rise_strength * dt
            else:
                # Near edges - sink (stronger near top)
                sink_strength = 2 + (center_y - blob.y) * 0.08
                blob.vy += sink_strength * dt

            # Horizontal convection force
            # At top, push outward from center
            # At bottom, push inward toward center
            if blob.y < center_y - 5:
                # Near top - push outward
                blob.vx += x_offset * 6 * dt
            elif blob.y > center_y + 5:
                # Near bottom - push inward
                blob.vx -= x_offset * 6 * dt

            # Add some organic randomness
            blob.vx += random.uniform(-4, 4) * dt
            blob.vy += random.uniform(-2, 2) * dt

            # More side-to-side wobble
            blob.vx += math.sin(self.time * 0.5 + blob.phase) * 5 * dt
            blob.vx += math.cos(self.time * 0.3 + blob.phase * 2) * 3 * dt

            # Slower damping for more fluid motion
            blob.vx *= 0.99
            blob.vy *= 0.99

            # Slower max velocity
            max_v = 6
            blob.vx = max(-max_v, min(max_v, blob.vx))
            blob.vy = max(-max_v, min(max_v, blob.vy))

            # Move
            blob.x += blob.vx * dt
            blob.y += blob.vy * dt

            # Bounce off edges softly (jelly effect)
            margin = blob.radius + 2
            if blob.x < margin:
                blob.x = margin
                blob.vx = abs(blob.vx) * 0.6
            elif blob.x > GRID_SIZE - margin:
                blob.x = GRID_SIZE - margin
                blob.vx = -abs(blob.vx) * 0.6

            if blob.y < margin:
                blob.y = margin
                blob.vy = abs(blob.vy) * 0.6
            elif blob.y > GRID_SIZE - margin:
                blob.y = GRID_SIZE - margin
                blob.vy = -abs(blob.vy) * 0.6

            # Radius wobble - bigger blobs
            blob.radius = 10 + math.sin(blob.phase) * 3

    def draw(self):
        blob_color, bg_color = COLOR_SCHEMES[self.scheme_idx]

        # Draw background gradient
        for y in range(GRID_SIZE):
            # Slightly lighter at top
            factor = 1.0 + (GRID_SIZE - y) / GRID_SIZE * 0.3
            r = min(255, int(bg_color[0] * factor))
            g = min(255, int(bg_color[1] * factor))
            b = min(255, int(bg_color[2] * factor))
            for x in range(GRID_SIZE):
                self.display.set_pixel(x, y, (r, g, b))

        # Create density field from blobs (for smooth merging)
        density = [[0.0] * GRID_SIZE for _ in range(GRID_SIZE)]

        for blob in self.blobs:
            # Add blob's contribution to density field
            r = int(blob.radius) + 4
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    px = int(blob.x) + dx
                    py = int(blob.y) + dy

                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        dist = math.sqrt(dx * dx + dy * dy)
                        if dist < blob.radius:
                            # Smooth falloff
                            strength = 1.0 - (dist / blob.radius)
                            strength = strength * strength  # Quadratic falloff
                            density[py][px] += strength

        # Draw based on density (threshold for blob edges)
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                d = density[y][x]
                if d > 0.3:
                    # Inside blob
                    # Brighter toward center
                    brightness = min(1.0, d)
                    r = int(blob_color[0] * (0.6 + 0.4 * brightness))
                    g = int(blob_color[1] * (0.6 + 0.4 * brightness))
                    b = int(blob_color[2] * (0.6 + 0.4 * brightness))
                    self.display.set_pixel(x, y, (r, g, b))
                elif d > 0.15:
                    # Edge glow
                    factor = (d - 0.15) / 0.15
                    r = int(blob_color[0] * 0.4 * factor)
                    g = int(blob_color[1] * 0.4 * factor)
                    b = int(blob_color[2] * 0.4 * factor)
                    # Blend with background
                    bg = self.display.pixels[y * GRID_SIZE + x] if hasattr(self.display, 'pixels') else bg_color
                    self.display.set_pixel(x, y, (r, g, b))
