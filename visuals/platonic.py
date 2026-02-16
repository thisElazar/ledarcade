"""
PLATONIC - Rotating Platonic solids
=====================================
All five Platonic solids with wireframe 3D rendering,
depth-shaded edges, and painter's algorithm.

Controls:
  Up/Down    - Cycle solid
  Left/Right - Adjust rotation speed
  Button     - Cycle color palette
"""

import math
from . import Visual, Display, Colors, GRID_SIZE


def _hsv(h, s, v):
    c = v * s
    x = c * (1 - abs((h * 6) % 2 - 1))
    m = v - c
    if h < 1/6:   r, g, b = c, x, 0
    elif h < 2/6: r, g, b = x, c, 0
    elif h < 3/6: r, g, b = 0, c, x
    elif h < 4/6: r, g, b = 0, x, c
    elif h < 5/6: r, g, b = x, 0, c
    else:          r, g, b = c, 0, x
    return (int((r + m) * 255), int((g + m) * 255), int((b + m) * 255))


PHI = (1 + math.sqrt(5)) / 2

# Vertex data for each solid (normalized to unit sphere, then scaled)
def _normalize(verts):
    """Normalize vertices to lie on unit sphere."""
    result = []
    for v in verts:
        length = math.sqrt(sum(c * c for c in v))
        result.append(tuple(c / length for c in v))
    return result


def _tetrahedron():
    verts = [(1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)]
    verts = _normalize(verts)
    edges = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
    return verts, edges, 4, 6, 4

def _cube():
    verts = []
    for x in (-1, 1):
        for y in (-1, 1):
            for z in (-1, 1):
                verts.append((x, y, z))
    verts = _normalize(verts)
    edges = [
        (0, 1), (0, 2), (0, 4), (1, 3), (1, 5), (2, 3),
        (2, 6), (3, 7), (4, 5), (4, 6), (5, 7), (6, 7),
    ]
    return verts, edges, 8, 12, 6

def _octahedron():
    verts = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
    edges = [
        (0, 2), (0, 3), (0, 4), (0, 5),
        (1, 2), (1, 3), (1, 4), (1, 5),
        (2, 4), (2, 5), (3, 4), (3, 5),
    ]
    return verts, edges, 6, 12, 8

def _dodecahedron():
    p = PHI
    ip = 1 / PHI
    verts = []
    # Cube vertices
    for x in (-1, 1):
        for y in (-1, 1):
            for z in (-1, 1):
                verts.append((x, y, z))
    # Rectangle vertices in 3 planes
    for x in (-ip, ip):
        for z in (-p, p):
            verts.append((x, 0, z))  # xz plane (y=0 missing, use 0)
    for y in (-ip, ip):
        for x in (-p, p):
            verts.append((x, y, 0))  # Correct: these sit in xy plane
    for z in (-ip, ip):
        for y in (-p, p):
            verts.append((0, y, z))
    verts = _normalize(verts)
    # Build edges by connecting vertices within threshold distance
    edges = []
    threshold = 0.8  # Normalized edge length for dodecahedron
    for i in range(len(verts)):
        for j in range(i + 1, len(verts)):
            dx = verts[i][0] - verts[j][0]
            dy = verts[i][1] - verts[j][1]
            dz = verts[i][2] - verts[j][2]
            dist = math.sqrt(dx*dx + dy*dy + dz*dz)
            if dist < threshold:
                edges.append((i, j))
    return verts, edges, 20, 30, 12

def _icosahedron():
    p = PHI
    verts = []
    for s1 in (-1, 1):
        for s2 in (-p, p):
            verts.append((0, s1, s2))
            verts.append((s1, s2, 0))
            verts.append((s2, 0, s1))
    verts = _normalize(verts)
    # Build edges by distance
    edges = []
    threshold = 1.2
    for i in range(len(verts)):
        for j in range(i + 1, len(verts)):
            dx = verts[i][0] - verts[j][0]
            dy = verts[i][1] - verts[j][1]
            dz = verts[i][2] - verts[j][2]
            dist = math.sqrt(dx*dx + dy*dy + dz*dz)
            if dist < threshold:
                edges.append((i, j))
    return verts, edges, 12, 30, 20


SOLIDS = [
    ('TETRA', _tetrahedron),
    ('CUBE', _cube),
    ('OCTA', _octahedron),
    ('DODECA', _dodecahedron),
    ('ICOSA', _icosahedron),
]

PALETTES = [
    ((100, 200, 255), (255, 255, 255)),    # Ice blue
    ((255, 180, 50), (255, 255, 200)),      # Gold
    ((100, 255, 150), (200, 255, 220)),     # Mint
    ((255, 100, 180), (255, 200, 230)),     # Pink
    ((180, 120, 255), (230, 200, 255)),     # Lavender
    ((255, 100, 60), (255, 200, 150)),      # Coral
]


class Platonic(Visual):
    name = "PLATONIC"
    description = "Rotating Platonic solids"
    category = "math"

    def reset(self):
        self.time = 0.0
        self.solid_idx = 0
        self.palette_idx = 0
        self.rotation_y = 0.0
        self.tilt = 0.4
        self.rotation_speed = 0.6
        self.overlay_timer = 0.0
        self.scale = 22.0
        self._build_solid()

    def _build_solid(self):
        name, builder = SOLIDS[self.solid_idx]
        self._verts, self._edges, self._nv, self._ne, self._nf = builder()
        self.overlay_timer = 2.0

    def handle_input(self, input_state):
        consumed = False
        if input_state.up_pressed:
            self.solid_idx = (self.solid_idx - 1) % len(SOLIDS)
            self._build_solid()
            consumed = True
        if input_state.down_pressed:
            self.solid_idx = (self.solid_idx + 1) % len(SOLIDS)
            self._build_solid()
            consumed = True
        if input_state.left:
            self.rotation_speed = max(-2.0, self.rotation_speed - 0.1)
            consumed = True
        if input_state.right:
            self.rotation_speed = min(2.0, self.rotation_speed + 0.1)
            consumed = True
        if input_state.action_l or input_state.action_r:
            self.palette_idx = (self.palette_idx + 1) % len(PALETTES)
            self.overlay_timer = 2.0
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
            # Depth shading
            depth_factor = max(0.3, min(1.0, (avg_z + self.scale) / (2 * self.scale)))
            c = (
                int(edge_color[0] * depth_factor),
                int(edge_color[1] * depth_factor),
                int(edge_color[2] * depth_factor),
            )
            x1, y1 = projected[a]
            x2, y2 = projected[b]
            d.draw_line(x1, y1, x2, y2, c)

        # Draw vertices as bright dots
        for i, (sx, sy) in enumerate(projected):
            depth_factor = max(0.5, min(1.0, (depths[i] + self.scale) / (2 * self.scale)))
            c = (
                int(vert_color[0] * depth_factor),
                int(vert_color[1] * depth_factor),
                int(vert_color[2] * depth_factor),
            )
            if 0 <= sx < GRID_SIZE and 0 <= sy < GRID_SIZE:
                d.set_pixel(sx, sy, c)
                # Small cross for visibility
                for dx2, dy2 in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = sx + dx2, sy + dy2
                    if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                        dim = (c[0] // 2, c[1] // 2, c[2] // 2)
                        d.set_pixel(nx, ny, dim)

        # Solid name
        solid_name = SOLIDS[self.solid_idx][0]
        d.draw_text_small(2, 58, solid_name, Colors.WHITE)

        # Overlay: V E F counts
        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            c = (int(200 * alpha), int(200 * alpha), int(200 * alpha))
            info = f"V{self._nv} E{self._ne} F{self._nf}"
            d.draw_text_small(2, 2, info, c)
