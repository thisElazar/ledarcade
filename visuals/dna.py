"""
DNA - 3D Rotating Double Helix
===============================
Two sugar-phosphate backbone strands spiraling around a central axis,
connected by base pair rungs with real base coloring.

Controls:
  Up/Down    - Cycle display modes (helix, ladder, single strand)
  Left/Right - Manual rotation (pauses auto-rotate)
  Space      - Toggle auto-cycle modes
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE

# Base pair colors
BASE_COLORS = {
    'A': (255, 50, 50),    # Adenine  - red
    'T': (50, 100, 255),   # Thymine  - blue
    'G': (50, 220, 50),    # Guanine  - green
    'C': (255, 230, 50),   # Cytosine - yellow
}

BASE_PAIRS = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G'}

BACKBONE_COLOR = (200, 200, 220)
BACKBONE_DIM = (100, 100, 120)

# Display modes
MODES = [
    ('DOUBLE HELIX', 'helix'),
    ('UNWOUND LADDER', 'ladder'),
    ('SINGLE STRAND', 'single'),
]

# Number of base pairs in the helix
NUM_BASES = 20

# Helix geometry
HELIX_RADIUS = 12.0    # Radius of each backbone strand
HELIX_PITCH = 3.4      # Rise per base pair (Angstroms-like units)
HELIX_TWIST = 2 * math.pi / 10  # ~36 degrees per base pair


class DNA(Visual):
    name = "DNA"
    description = "3D rotating double helix"
    category = "science"

    def reset(self):
        self.time = 0.0
        self.rotation_y = 0.0
        self.rotation_speed = 0.5
        self.auto_rotate = True
        self.tilt_phase = 0.0
        self.mode_idx = 0
        self.label_timer = 0.0
        self.overlay_timer = 0.0
        self.auto_cycle = True
        self.cycle_timer = 0.0
        self.cycle_duration = 12.0

        # Generate random base sequence
        self.sequence = []
        for _ in range(NUM_BASES):
            base = random.choice(['A', 'T', 'G', 'C'])
            self.sequence.append(base)

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.up_pressed:
            self.mode_idx = (self.mode_idx - 1) % len(MODES)
            self.overlay_timer = 2.5
            consumed = True
        if input_state.down_pressed:
            self.mode_idx = (self.mode_idx + 1) % len(MODES)
            self.overlay_timer = 2.5
            consumed = True
        if input_state.left or input_state.right:
            # Manual rotation
            self.auto_rotate = False
            speed = 1.5
            if input_state.left:
                self.rotation_y -= speed * 0.033
            if input_state.right:
                self.rotation_y += speed * 0.033
            consumed = True
        if input_state.action_l or input_state.action_r:
            self.auto_rotate = not self.auto_rotate
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt
        self.label_timer += dt
        self.tilt_phase += dt * 0.3

        if self.auto_rotate:
            self.rotation_y += self.rotation_speed * dt

        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

        if self.auto_cycle:
            self.cycle_timer += dt
            if self.cycle_timer >= self.cycle_duration:
                self.cycle_timer = 0.0
                self.mode_idx = (self.mode_idx + 1) % len(MODES)
                self.overlay_timer = 2.0

    def _transform_point(self, x, y, z):
        """Rotate around Y axis with gentle X tilt, project to screen."""
        tilt = 0.3 * math.sin(self.tilt_phase)
        cos_t, sin_t = math.cos(tilt), math.sin(tilt)
        y2 = y * cos_t - z * sin_t
        z2 = y * sin_t + z * cos_t

        cos_r, sin_r = math.cos(self.rotation_y), math.sin(self.rotation_y)
        x2 = x * cos_r + z2 * sin_r
        z3 = -x * sin_r + z2 * cos_r

        screen_x = GRID_SIZE // 2 + x2
        screen_y = 28 - y2
        return screen_x, screen_y, z3

    def _depth_shade(self, color, z, z_range=30.0):
        """Shade color based on depth (farther = dimmer)."""
        factor = 0.4 + 0.6 * ((z + z_range) / (2 * z_range))
        factor = max(0.2, min(1.0, factor))
        return (int(color[0] * factor), int(color[1] * factor), int(color[2] * factor))

    def draw(self):
        d = self.display
        d.clear(Colors.BLACK)

        mode_name, mode_key = MODES[self.mode_idx]
        draw_list = []

        # Build helix geometry
        center_y_offset = (NUM_BASES * HELIX_PITCH) / 2

        for i in range(NUM_BASES):
            base = self.sequence[i]
            comp = BASE_PAIRS[base]
            y_pos = i * HELIX_PITCH - center_y_offset

            angle = i * HELIX_TWIST

            if mode_key == 'ladder':
                # Unwound: flat ladder, strands at fixed x offset
                x1 = -HELIX_RADIUS
                z1 = 0
                x2 = HELIX_RADIUS
                z2 = 0
            elif mode_key == 'single':
                # Single strand: only backbone 1
                x1 = HELIX_RADIUS * math.cos(angle)
                z1 = HELIX_RADIUS * math.sin(angle)
                x2 = None
                z2 = None
            else:
                # Double helix
                x1 = HELIX_RADIUS * math.cos(angle)
                z1 = HELIX_RADIUS * math.sin(angle)
                x2 = HELIX_RADIUS * math.cos(angle + math.pi)
                z2 = HELIX_RADIUS * math.sin(angle + math.pi)

            # Scale y to fit on screen
            y_scaled = y_pos * 0.8

            # Transform backbone point 1
            sx1, sy1, sz1 = self._transform_point(x1, y_scaled, z1)
            draw_list.append(('base', sz1, sx1, sy1, BASE_COLORS[base], sz1))

            if x2 is not None:
                # Transform backbone point 2
                sx2, sy2, sz2 = self._transform_point(x2, y_scaled, z2)
                draw_list.append(('base', sz2, sx2, sy2, BASE_COLORS[comp], sz2))

                # Base pair rung connecting the two strands
                avg_z = (sz1 + sz2) / 2
                draw_list.append(('rung', avg_z, sx1, sy1, sx2, sy2, sz1))

            # Backbone connections to next base
            if i < NUM_BASES - 1:
                next_angle = (i + 1) * HELIX_TWIST
                next_y = ((i + 1) * HELIX_PITCH - center_y_offset) * 0.8

                if mode_key == 'ladder':
                    nx1 = -HELIX_RADIUS
                    nz1 = 0
                    nx2 = HELIX_RADIUS
                    nz2 = 0
                elif mode_key == 'single':
                    nx1 = HELIX_RADIUS * math.cos(next_angle)
                    nz1 = HELIX_RADIUS * math.sin(next_angle)
                    nx2 = None
                    nz2 = None
                else:
                    nx1 = HELIX_RADIUS * math.cos(next_angle)
                    nz1 = HELIX_RADIUS * math.sin(next_angle)
                    nx2 = HELIX_RADIUS * math.cos(next_angle + math.pi)
                    nz2 = HELIX_RADIUS * math.sin(next_angle + math.pi)

                snx1, sny1, snz1 = self._transform_point(nx1, next_y, nz1)
                bb_z = (sz1 + snz1) / 2
                draw_list.append(('backbone', bb_z, sx1, sy1, snx1, sny1, sz1))

                if nx2 is not None:
                    snx2, sny2, snz2 = self._transform_point(nx2, next_y, nz2)
                    bb_z2 = (sz2 + snz2) / 2
                    draw_list.append(('backbone', bb_z2, sx2, sy2, snx2, sny2, sz2))

        # Painter's algorithm: sort by depth (farthest first)
        draw_list.sort(key=lambda item: item[1])

        for item in draw_list:
            kind = item[0]
            if kind == 'backbone':
                _, _, x1, y1, x2, y2, z = item
                color = self._depth_shade(BACKBONE_COLOR, z)
                d.draw_line(int(x1), int(y1), int(x2), int(y2), color)
            elif kind == 'rung':
                _, _, x1, y1, x2, y2, z = item
                color = self._depth_shade(BACKBONE_DIM, z)
                d.draw_line(int(x1), int(y1), int(x2), int(y2), color)
            elif kind == 'base':
                _, _, sx, sy, base_color, z = item
                color = self._depth_shade(base_color, z)
                ix, iy = int(round(sx)), int(round(sy))
                # Draw 2px dot for each base
                d.set_pixel(ix, iy, color)
                d.set_pixel(ix + 1, iy, color)
                d.set_pixel(ix, iy + 1, color)
                d.set_pixel(ix + 1, iy + 1, color)

        # Bottom label: 3 phases
        phase = int(self.label_timer / 4) % 3
        if phase == 0:
            label = mode_name
        elif phase == 1:
            # Show base sequence snippet
            start = int(self.time * 2) % len(self.sequence)
            snippet = ''.join(self.sequence[start:start + 10])
            label = snippet
        else:
            label = "DNA DOUBLE HELIX"
        d.draw_text_small(2, 58, label, Colors.WHITE)

        # Mode overlay at top
        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            oc = (int(100 * alpha), int(200 * alpha), int(255 * alpha))
            d.draw_text_small(2, 2, mode_name, oc)
