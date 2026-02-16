"""
SOLIDS - Rotating polyhedra from 4 families
=============================================
35 solids: Platonic, Archimedean, Kepler-Poinsot, and Catalan.
Wireframe 3D rendering with depth-shaded edges and painter's algorithm.

Controls:
  Up/Down    - Cycle solid within current family
  Left/Right - Adjust rotation speed
  Button     - Cycle family
"""

import math
from . import Visual, Display, Colors, GRID_SIZE
from .solids_data import FAMILIES


PALETTES = [
    ((100, 200, 255), (255, 255, 255)),    # Ice blue
    ((255, 180, 50), (255, 255, 200)),      # Gold
    ((100, 255, 150), (200, 255, 220)),     # Mint
    ((255, 100, 180), (255, 200, 230)),     # Pink
    ((180, 120, 255), (230, 200, 255)),     # Lavender
    ((255, 100, 60), (255, 200, 150)),      # Coral
]


class Solids(Visual):
    name = "SOLIDS"
    description = "Rotating polyhedra"
    category = "math"

    def reset(self):
        self.time = 0.0
        self.family_idx = 0
        self.solid_idx = 0
        self.palette_idx = 0
        self.rotation_y = 0.0
        self.tilt = 0.4
        self.rotation_speed = 0.6
        self.overlay_timer = 0.0
        self.scale = 22.0
        self._build_solid()

    def _build_solid(self):
        family_name, solids = FAMILIES[self.family_idx]
        name, builder = solids[self.solid_idx]
        self._verts, self._edges, self._nv, self._ne, self._nf = builder()
        # Auto-scale: normalize so max vertex radius maps to 22px
        max_r = max(math.sqrt(sum(c * c for c in v)) for v in self._verts)
        self.scale = 22.0 / max_r if max_r > 0 else 22.0
        self.overlay_timer = 2.0

    def handle_input(self, input_state):
        consumed = False
        family_name, solids = FAMILIES[self.family_idx]
        if input_state.up_pressed:
            self.solid_idx = (self.solid_idx - 1) % len(solids)
            self._build_solid()
            consumed = True
        if input_state.down_pressed:
            self.solid_idx = (self.solid_idx + 1) % len(solids)
            self._build_solid()
            consumed = True
        if input_state.left:
            self.rotation_speed = max(-2.0, self.rotation_speed - 0.1)
            consumed = True
        if input_state.right:
            self.rotation_speed = min(2.0, self.rotation_speed + 0.1)
            consumed = True
        if input_state.action_l or input_state.action_r:
            self.family_idx = (self.family_idx + 1) % len(FAMILIES)
            self.solid_idx = 0
            self._build_solid()
            consumed = True
        return consumed

    def update(self, dt):
        self.time += dt
        self.rotation_y += self.rotation_speed * dt
        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

    def draw(self):
        d = self.display
        d.clear()

        edge_color, vert_color = PALETTES[self.palette_idx]
        cos_ry = math.cos(self.rotation_y)
        sin_ry = math.sin(self.rotation_y)
        cos_rx = math.cos(self.tilt)
        sin_rx = math.sin(self.tilt)
        cx, cy = GRID_SIZE // 2, GRID_SIZE // 2

        # Project all vertices
        projected = []
        depths = []
        for vx, vy, vz in self._verts:
            x, y, z = vx * self.scale, vy * self.scale, vz * self.scale
            # Rotate Y
            x2 = x * cos_ry + z * sin_ry
            z2 = -x * sin_ry + z * cos_ry
            # Rotate X (tilt)
            y2 = y * cos_rx - z2 * sin_rx
            z3 = y * sin_rx + z2 * cos_rx
            # Perspective
            persp = 80.0 / (80.0 + z3 * 0.3)
            sx = int(cx + x2 * persp)
            sy = int(cy - y2 * persp)
            projected.append((sx, sy))
            depths.append(z3)

        # Sort edges by average depth (painter's algorithm)
        edge_depths = []
        for i, (a, b) in enumerate(self._edges):
            avg_z = (depths[a] + depths[b]) / 2
            edge_depths.append((avg_z, a, b))
        edge_depths.sort(key=lambda e: e[0])

        # Draw edges
        for avg_z, a, b in edge_depths:
            depth_factor = max(0.3, min(1.0, (avg_z + self.scale) / (2 * self.scale)))
            c = (
                int(edge_color[0] * depth_factor),
                int(edge_color[1] * depth_factor),
                int(edge_color[2] * depth_factor),
            )
            x1, y1 = projected[a]
            x2, y2 = projected[b]
            d.draw_line(x1, y1, x2, y2, c)

        # Draw vertices as bright dots (skip for high-vertex solids to avoid clutter)
        if self._nv <= 60:
            for i, (sx, sy) in enumerate(projected):
                depth_factor = max(0.5, min(1.0, (depths[i] + self.scale) / (2 * self.scale)))
                c = (
                    int(vert_color[0] * depth_factor),
                    int(vert_color[1] * depth_factor),
                    int(vert_color[2] * depth_factor),
                )
                if 0 <= sx < GRID_SIZE and 0 <= sy < GRID_SIZE:
                    d.set_pixel(sx, sy, c)
                    if self._nv <= 30:
                        for dx2, dy2 in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            nx, ny = sx + dx2, sy + dy2
                            if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                                dim = (c[0] // 2, c[1] // 2, c[2] // 2)
                                d.set_pixel(nx, ny, dim)

        # Solid name at bottom
        family_name, solids = FAMILIES[self.family_idx]
        solid_name = solids[self.solid_idx][0]
        d.draw_text_small(2, 58, solid_name, Colors.WHITE)

        # Overlay
        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            c = (int(200 * alpha), int(200 * alpha), int(200 * alpha))
            d.draw_text_small(2, 2, family_name, c)
            info = f"V{self._nv} E{self._ne} F{self._nf}"
            d.draw_text_small(2, 8, info, c)
