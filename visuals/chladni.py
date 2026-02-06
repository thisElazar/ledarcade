"""
Chladni Plates - Vibrating Plate Nodal Patterns
================================================
Sand particles drift toward nodal lines on a vibrating plate.
Frequency control sweeps smoothly between modes.

Controls:
  Left/Right (held) - Sweep frequency continuously
  Up/Down (pressed) - Cycle plate shape (square, circle, rectangle)
  Space             - Scatter sand (reset particles)
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE

# Plate shapes
SHAPES = [
    ('SQUARE', 'square'),
    ('CIRCLE', 'circle'),
    ('RECTANGLE', 'rect'),
]

# Sand colors (warm tan/gold palette)
SAND_COLORS = [
    (220, 190, 130),
    (240, 210, 150),
    (200, 170, 110),
    (230, 200, 140),
    (250, 220, 160),
]

# Plate background
PLATE_COLOR = (15, 12, 10)
NODAL_DIM = (30, 25, 18)

NUM_PARTICLES = 400

# Drawing area
DRAW_SIZE = 54  # Leave room for label
DRAW_OFFSET_X = (GRID_SIZE - DRAW_SIZE) // 2
DRAW_OFFSET_Y = 1


class Chladni(Visual):
    name = "CHLADNI"
    description = "Vibrating plate nodal patterns"
    category = "science"

    def reset(self):
        self.time = 0.0
        self.shape_idx = 0
        self.frequency = 2.5  # Continuous float mapping to mode blend
        self.label_timer = 0.0
        self.overlay_timer = 0.0

        # Initialize particles at random positions
        self.particles = []
        self._scatter_particles()

    def _scatter_particles(self):
        """Reset all particles to random positions."""
        self.particles = []
        for _ in range(NUM_PARTICLES):
            x = random.uniform(0, 1)
            y = random.uniform(0, 1)
            color = random.choice(SAND_COLORS)
            self.particles.append([x, y, color])

    def _chladni_amplitude(self, x, y, n, m, shape):
        """Compute Chladni pattern amplitude at normalized (x, y) in [0, 1].
        Returns a value where 0 = nodal line (sand settles here).
        """
        if shape == 'circle':
            # Map to polar, use circular approximation
            cx, cy = x - 0.5, y - 0.5
            r = math.sqrt(cx * cx + cy * cy) * 2  # r in [0, 1]
            if r > 1.0:
                return 1.0  # Outside plate
            theta = math.atan2(cy, cx)
            # Approximate circular Chladni with angular + radial modes
            radial = math.cos(n * math.pi * r)
            angular = math.cos(m * theta)
            return radial * angular

        elif shape == 'rect':
            # Rectangle: different aspect ratio
            val = (math.cos(n * math.pi * x) * math.cos(m * math.pi * y * 1.5)
                   - math.cos(m * math.pi * x) * math.cos(n * math.pi * y * 1.5))
            return val

        else:
            # Square plate: classic Chladni formula
            val = (math.cos(n * math.pi * x) * math.cos(m * math.pi * y)
                   - math.cos(m * math.pi * x) * math.cos(n * math.pi * y))
            return val

    def _get_blended_modes(self):
        """Get two mode pairs and a blend factor from the frequency float."""
        # Map frequency to pairs of (n, m) modes
        modes = [
            (1, 2), (2, 3), (1, 3), (3, 4), (2, 5),
            (3, 5), (1, 4), (4, 5), (2, 4), (5, 6),
            (3, 7), (4, 7), (1, 5), (5, 8), (6, 7),
        ]
        idx = self.frequency
        i = int(idx) % len(modes)
        j = (i + 1) % len(modes)
        blend = idx - int(idx)
        return modes[i], modes[j], blend

    def _blended_amplitude(self, x, y, shape):
        """Compute blended amplitude between two mode pairs."""
        (n1, m1), (n2, m2), blend = self._get_blended_modes()
        a1 = self._chladni_amplitude(x, y, n1, m1, shape)
        a2 = self._chladni_amplitude(x, y, n2, m2, shape)
        return a1 * (1.0 - blend) + a2 * blend

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Continuous frequency sweep
        if input_state.left:
            self.frequency -= 0.04
            if self.frequency < 0:
                self.frequency = 0.0
            consumed = True
        if input_state.right:
            self.frequency += 0.04
            consumed = True

        # Discrete shape cycling
        if input_state.up_pressed:
            self.shape_idx = (self.shape_idx - 1) % len(SHAPES)
            self.overlay_timer = 2.5
            consumed = True
        if input_state.down_pressed:
            self.shape_idx = (self.shape_idx + 1) % len(SHAPES)
            self.overlay_timer = 2.5
            consumed = True

        # Action: scatter sand
        if input_state.action_l or input_state.action_r:
            self._scatter_particles()
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt
        self.label_timer += dt

        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

        shape_name, shape_key = SHAPES[self.shape_idx]

        # Move particles toward nodal lines
        drift_speed = 0.8 * dt
        jitter = 0.002

        for p in self.particles:
            x, y = p[0], p[1]

            # Compute amplitude at current position
            amp = self._blended_amplitude(x, y, shape_key)

            # Compute gradient (which direction has lower amplitude)
            eps = 0.01
            ax_pos = abs(self._blended_amplitude(min(1, x + eps), y, shape_key))
            ax_neg = abs(self._blended_amplitude(max(0, x - eps), y, shape_key))
            ay_pos = abs(self._blended_amplitude(x, min(1, y + eps), shape_key))
            ay_neg = abs(self._blended_amplitude(x, max(0, y - eps), shape_key))

            # Gradient of |amplitude| — particles move toward lower |amplitude|
            grad_x = (ax_pos - ax_neg) / (2 * eps)
            grad_y = (ay_pos - ay_neg) / (2 * eps)

            # Normalize and scale by current amplitude (stronger push when farther from node)
            grad_mag = math.sqrt(grad_x * grad_x + grad_y * grad_y)
            if grad_mag > 0.01:
                grad_x /= grad_mag
                grad_y /= grad_mag

            force = min(1.0, abs(amp)) * drift_speed
            p[0] -= grad_x * force + random.uniform(-jitter, jitter)
            p[1] -= grad_y * force + random.uniform(-jitter, jitter)

            # Clamp to plate
            p[0] = max(0.0, min(1.0, p[0]))
            p[1] = max(0.0, min(1.0, p[1]))

            # For circle, keep within radius
            if shape_key == 'circle':
                cx, cy = p[0] - 0.5, p[1] - 0.5
                r = math.sqrt(cx * cx + cy * cy)
                if r > 0.48:
                    scale = 0.48 / r
                    p[0] = 0.5 + cx * scale
                    p[1] = 0.5 + cy * scale

    def draw(self):
        d = self.display
        d.clear(Colors.BLACK)

        shape_name, shape_key = SHAPES[self.shape_idx]

        # Draw plate background
        for py in range(DRAW_SIZE):
            for px in range(DRAW_SIZE):
                sx = DRAW_OFFSET_X + px
                sy = DRAW_OFFSET_Y + py

                nx = px / (DRAW_SIZE - 1)
                ny = py / (DRAW_SIZE - 1)

                # Check if within plate shape
                in_plate = True
                if shape_key == 'circle':
                    cx, cy = nx - 0.5, ny - 0.5
                    if cx * cx + cy * cy > 0.25:
                        in_plate = False

                if in_plate:
                    # Show nodal lines dimly
                    amp = abs(self._blended_amplitude(nx, ny, shape_key))
                    if amp < 0.08:
                        d.set_pixel(sx, sy, NODAL_DIM)
                    else:
                        d.set_pixel(sx, sy, PLATE_COLOR)

        # Draw sand particles
        for p in self.particles:
            px = int(p[0] * (DRAW_SIZE - 1)) + DRAW_OFFSET_X
            py = int(p[1] * (DRAW_SIZE - 1)) + DRAW_OFFSET_Y
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                d.set_pixel(px, py, p[2])

        # Bottom label
        (n1, m1), (n2, m2), blend = self._get_blended_modes()
        phase = int(self.label_timer / 4) % 3
        if phase == 0:
            label = f"MODE {n1}.{m1}"
        elif phase == 1:
            label = shape_name
        else:
            label = "CHLADNI PLATE"
        d.draw_text_small(2, 58, label, Colors.WHITE)

        # Shape overlay
        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            oc = (int(220 * alpha), int(190 * alpha), int(130 * alpha))
            d.draw_text_small(2, 2, shape_name, oc)
