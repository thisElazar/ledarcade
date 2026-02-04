"""
Proteins - 3D Protein Backbone Visualization
=============================================
Rotating 3D ribbon-style backbone traces of protein structures.
Color-coded by secondary structure: helix (red), sheet (yellow), coil (gray).

Controls:
  Joystick   - Rotate protein in 3D (left/right spins, up/down tilts)
  Z/X        - Cycle through proteins

Auto-rotates when joystick is idle for 2 seconds.
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE


# Secondary structure colors (classic ribbon diagram scheme)
SS_COLORS = {
    'H': (255, 80, 80),    # Alpha helix - red/salmon
    'G': (255, 120, 100),  # 3-10 helix - lighter red
    'I': (255, 60, 120),   # Pi helix - pink-red
    'E': (255, 255, 80),   # Beta sheet - yellow
    'B': (220, 200, 80),   # Beta bridge - darker yellow
    'T': (100, 200, 180),  # Turn - cyan
    'S': (140, 140, 140),  # Bend - gray
    'C': (180, 180, 180),  # Coil/loop - light gray
}

# Ubiquitin (PDB: 1UBQ) - 76 residues
# Cα coordinates extracted and secondary structure from DSSP
# This is the "kiss of death" protein - tags proteins for destruction
UBIQUITIN = {
    'name': 'UBIQUITIN',
    'pdb': '1UBQ',
    'description': 'Protein degradation tag',
    'residues': 76,
    # Format: (x, y, z, secondary_structure)
    # Coordinates in Angstroms, centered approximately at origin
    # Secondary structure: H=helix, E=sheet, C=coil, T=turn
    'backbone': [
        # Residues 1-7: N-terminal flexible region and first beta strand
        (27.340, 24.430, 2.614, 'C'),   # MET 1
        (26.266, 25.413, 5.958, 'C'),   # GLN 2
        (23.204, 23.652, 6.859, 'E'),   # ILE 3
        (22.128, 23.654, 10.437, 'E'),  # PHE 4
        (18.563, 24.891, 9.878, 'E'),   # VAL 5
        (17.635, 22.829, 12.871, 'E'),  # LYS 6
        (14.068, 23.641, 13.813, 'E'),  # THR 7
        # Residues 8-11: turn/loop
        (12.806, 20.122, 13.689, 'T'),  # LEU 8
        (9.453, 20.680, 15.365, 'T'),   # THR 9
        (7.817, 17.336, 15.904, 'T'),   # GLY 10
        (8.902, 15.078, 13.147, 'C'),   # LYS 11
        # Residues 12-17: second beta strand
        (12.089, 16.442, 11.628, 'E'),  # THR 12
        (14.389, 13.520, 11.654, 'E'),  # ILE 13
        (17.770, 14.980, 10.490, 'E'),  # THR 14
        (19.886, 12.201, 9.054, 'E'),   # LEU 15
        (23.240, 13.656, 8.207, 'E'),   # GLU 16
        (25.440, 11.236, 6.377, 'E'),   # VAL 17
        # Residues 18-21: loop before helix
        (28.866, 12.778, 5.704, 'C'),   # GLU 18
        (30.498, 10.239, 3.527, 'C'),   # PRO 19
        (29.755, 10.797, -0.149, 'C'),  # SER 20
        (26.171, 11.940, -0.924, 'C'),  # ASP 21
        (24.963, 9.227, -3.205, 'C'),   # THR 22
        # Residues 23-34: main alpha helix
        (21.336, 9.943, -4.026, 'H'),   # ILE 23
        (20.486, 6.558, -5.615, 'H'),   # GLU 24
        (16.956, 6.447, -4.245, 'H'),   # ASN 25
        (15.389, 3.015, -4.539, 'H'),   # VAL 26
        (12.022, 4.195, -3.184, 'H'),   # LYS 27
        (10.698, 0.693, -3.453, 'H'),   # ALA 28
        (7.266, 1.645, -2.109, 'H'),    # LYS 29
        (6.048, -1.846, -2.555, 'H'),   # ILE 30
        (2.676, -0.615, -1.574, 'H'),   # GLN 31
        (1.252, -3.974, -2.587, 'H'),   # ASP 32
        (-1.880, -2.373, -1.376, 'H'),  # LYS 33
        (-2.691, -5.766, -2.701, 'H'),  # GLU 34
        # Residues 35-40: loop region
        (-4.247, -4.803, -5.954, 'C'),  # GLY 35
        (-1.655, -3.212, -8.135, 'C'),  # ILE 36
        (1.495, -5.263, -7.819, 'C'),   # PRO 37
        (2.143, -6.143, -4.204, 'C'),   # PRO 38
        (4.995, -4.215, -2.651, 'C'),   # ASP 39
        (4.746, -5.200, 0.956, 'C'),    # GLN 40
        # Residues 41-45: third beta strand
        (7.853, -3.340, 2.154, 'E'),    # GLN 41
        (8.214, -4.685, 5.648, 'E'),    # ARG 42
        (11.733, -3.426, 6.680, 'E'),   # LEU 43
        (12.361, -5.321, 9.880, 'E'),   # ILE 44
        (15.986, -4.334, 10.531, 'E'),  # PHE 45
        # Residues 46-48: turn
        (17.133, -7.101, 12.784, 'T'),  # ALA 46
        (15.756, -10.411, 11.556, 'T'), # GLY 47
        (17.908, -11.657, 8.796, 'T'),  # LYS 48
        # Residues 49-59: fourth beta strand and loop
        (18.596, -8.690, 6.517, 'E'),   # GLN 49
        (21.866, -9.660, 4.819, 'E'),   # LEU 50
        (22.242, -6.640, 2.643, 'E'),   # GLU 51
        (25.734, -6.844, 1.084, 'E'),   # ASP 52
        (25.949, -3.660, -1.088, 'T'),  # GLY 53
        (26.657, -4.817, -4.592, 'T'),  # ARG 54
        (24.251, -2.331, -6.266, 'C'),  # THR 55
        (26.104, 0.831, -5.263, 'C'),   # LEU 56
        (23.825, 3.558, -5.886, 'C'),   # SER 57
        (25.279, 6.992, -5.057, 'C'),   # ASP 58
        (23.049, 9.684, -6.245, 'C'),   # TYR 59
        (24.714, 12.930, -5.183, 'C'),  # ASN 60
        # Residues 61-65: short strand/turn
        (22.636, 15.508, -3.385, 'C'),  # ILE 61
        (25.181, 17.888, -1.942, 'T'),  # GLN 62
        (24.038, 21.462, -1.534, 'T'),  # LYS 63
        (26.790, 23.833, -0.362, 'E'),  # GLU 64
        (25.494, 26.969, 1.248, 'E'),   # SER 65
        # Residues 66-72: fifth beta strand
        (27.655, 27.310, 4.364, 'E'),   # THR 66
        (25.823, 29.787, 6.597, 'E'),   # LEU 67
        (27.890, 29.223, 9.710, 'E'),   # HIS 68
        (26.056, 31.261, 12.354, 'E'),  # LEU 69
        (28.166, 29.933, 15.195, 'E'),  # VAL 70
        (26.431, 31.436, 18.163, 'E'),  # LEU 71
        (28.489, 29.550, 20.566, 'E'),  # ARG 72
        # Residues 73-76: C-terminal flexible tail
        (26.552, 30.557, 23.692, 'C'),  # LEU 73
        (27.817, 27.418, 25.353, 'C'),  # ARG 74
        (25.005, 26.139, 27.561, 'C'),  # GLY 75
        (25.934, 22.629, 28.687, 'C'),  # GLY 76
    ],
}

# List of all proteins (start with just ubiquitin for proof of concept)
PROTEINS = [
    UBIQUITIN,
]


class Proteins(Visual):
    name = "PROTEINS"
    description = "3D protein backbone structures"
    category = "science"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.protein_idx = 0
        self.rotation_y = 0.0  # Manual: left/right
        self.tilt_x = 0.0      # Manual: up/down
        self.rotation_z = 0.0  # Auto-rotate around Z (the uncontrolled axis)
        self.auto_rotate_speed = 0.3
        self.manual_timeout = 0.0  # Time since last manual input
        self.auto_cycle = True
        self.cycle_timer = 0.0
        self.cycle_duration = 15.0  # Longer view time for proteins
        self.label_timer = 0.0
        self.scroll_offset = 0.0  # For scrolling long text
        self._prepare_protein()

    def _prepare_protein(self):
        """Pre-compute scale and centering for current protein."""
        protein = PROTEINS[self.protein_idx]
        backbone = protein['backbone']

        if len(backbone) == 0:
            self.scale = 1.0
            self.offset = (0, 0, 0)
            return

        # Center of mass
        cx = sum(r[0] for r in backbone) / len(backbone)
        cy = sum(r[1] for r in backbone) / len(backbone)
        cz = sum(r[2] for r in backbone) / len(backbone)
        self.offset = (cx, cy, cz)

        # Find maximum extent
        max_r = 0.0
        for r in backbone:
            dx, dy, dz = r[0] - cx, r[1] - cy, r[2] - cz
            dist = math.sqrt(dx * dx + dy * dy + dz * dz)
            max_r = max(max_r, dist)

        # Scale to fit display (leave room for labels)
        target_radius = 24.0
        self.scale = target_radius / max_r if max_r > 0 else 1.0
        self.label_timer = 0.0

    def handle_input(self, input_state) -> bool:
        consumed = False
        rotation_speed = 2.0  # Radians per second for manual control
        tilt_speed = 1.5

        # Joystick controls rotation
        if input_state.left:
            self.rotation_y -= rotation_speed * 0.016  # Assume ~60fps
            self.manual_timeout = 2.0  # Pause auto-rotate for 2 seconds
            consumed = True
        if input_state.right:
            self.rotation_y += rotation_speed * 0.016
            self.manual_timeout = 2.0
            consumed = True
        if input_state.up:
            self.tilt_x -= tilt_speed * 0.016
            self.manual_timeout = 2.0
            consumed = True
        if input_state.down:
            self.tilt_x += tilt_speed * 0.016
            self.manual_timeout = 2.0
            consumed = True

        # Action buttons cycle through proteins
        if input_state.action_l:
            self.protein_idx = (self.protein_idx - 1) % len(PROTEINS)
            self.cycle_timer = 0.0
            self._prepare_protein()
            consumed = True
        if input_state.action_r:
            self.protein_idx = (self.protein_idx + 1) % len(PROTEINS)
            self.cycle_timer = 0.0
            self._prepare_protein()
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt
        self.label_timer += dt
        self.scroll_offset += dt * 20  # Scroll speed in pixels/sec

        # Countdown manual input timeout
        if self.manual_timeout > 0:
            self.manual_timeout -= dt

        # Auto-rotate around Z axis (the axis user can't control)
        self.rotation_z += self.auto_rotate_speed * dt

        # When idle, gently return manual rotations toward neutral
        if self.manual_timeout <= 0:
            if abs(self.tilt_x) > 0.01:
                self.tilt_x *= 0.98
            if abs(self.rotation_y) > 0.01:
                self.rotation_y *= 0.98

        if self.auto_cycle:
            self.cycle_timer += dt
            if self.cycle_timer >= self.cycle_duration:
                self.cycle_timer = 0.0
                self.protein_idx = (self.protein_idx + 1) % len(PROTEINS)
                self._prepare_protein()

    def _transform_point(self, x, y, z):
        """Apply rotation and project to screen coords."""
        # Center
        x -= self.offset[0]
        y -= self.offset[1]
        z -= self.offset[2]

        # Scale
        x *= self.scale
        y *= self.scale
        z *= self.scale

        # Auto-rotation around Z axis (constant tumble)
        cos_z, sin_z = math.cos(self.rotation_z), math.sin(self.rotation_z)
        x1 = x * cos_z - y * sin_z
        y1 = x * sin_z + y * cos_z

        # Manual tilt (rotation around X axis) - controlled by up/down
        cos_t, sin_t = math.cos(self.tilt_x), math.sin(self.tilt_x)
        y2 = y1 * cos_t - z * sin_t
        z2 = y1 * sin_t + z * cos_t

        # Manual rotation around Y axis - controlled by left/right
        cos_r, sin_r = math.cos(self.rotation_y), math.sin(self.rotation_y)
        x2 = x1 * cos_r + z2 * sin_r
        z3 = -x1 * sin_r + z2 * cos_r

        # Orthographic projection
        screen_x = GRID_SIZE // 2 + x2
        screen_y = 28 - y2  # Slight offset from center for label room

        return screen_x, screen_y, z3

    def draw(self):
        self.display.clear(Colors.BLACK)

        protein = PROTEINS[self.protein_idx]
        backbone = protein['backbone']

        if len(backbone) < 2:
            return

        # Transform all backbone points
        transformed = []
        for x, y, z, ss in backbone:
            sx, sy, sz = self._transform_point(x, y, z)
            transformed.append((sx, sy, sz, ss))

        # Build draw list: segments between consecutive residues
        # We'll draw back-to-front for proper occlusion
        segments = []
        for i in range(len(transformed) - 1):
            x1, y1, z1, ss1 = transformed[i]
            x2, y2, z2, ss2 = transformed[i + 1]
            avg_z = (z1 + z2) / 2
            # Use the secondary structure of the first residue for color
            segments.append((avg_z, x1, y1, x2, y2, ss1, i))

        # Sort by z (back to front)
        segments.sort(key=lambda s: s[0])

        # Draw backbone segments
        for seg in segments:
            _, x1, y1, x2, y2, ss, idx = seg
            color = SS_COLORS.get(ss, SS_COLORS['C'])

            # Apply depth shading
            avg_z = seg[0]
            depth_factor = 0.5 + 0.5 * (avg_z / 30.0 + 0.5)
            depth_factor = max(0.3, min(1.0, depth_factor))

            shaded = (
                int(color[0] * depth_factor),
                int(color[1] * depth_factor),
                int(color[2] * depth_factor),
            )

            # Draw thicker line for helices and sheets
            self._draw_backbone_segment(x1, y1, x2, y2, shaded, ss)

        # Draw small dots at Cα positions for structure
        for i, (sx, sy, sz, ss) in enumerate(transformed):
            color = SS_COLORS.get(ss, SS_COLORS['C'])
            depth_factor = 0.5 + 0.5 * (sz / 30.0 + 0.5)
            depth_factor = max(0.3, min(1.0, depth_factor))
            dot_color = (
                int(color[0] * depth_factor),
                int(color[1] * depth_factor),
                int(color[2] * depth_factor),
            )
            # Just the center pixel for Cα
            ix, iy = int(round(sx)), int(round(sy))
            if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                self.display.set_pixel(ix, iy, dot_color)

        # Draw label at bottom - cycle through name, description, PDB ID
        cycle = int(self.label_timer / 6) % 3
        if cycle == 0:
            label = protein['name']
        elif cycle == 1:
            label = protein['description']
        else:
            label = f"PDB: {protein['pdb']}"

        # Reset scroll when label changes
        if not hasattr(self, '_last_cycle') or self._last_cycle != cycle:
            self._last_cycle = cycle
            self.scroll_offset = 0

        # Scroll long text (4px per char, ~14 chars fit on screen)
        max_chars = 14
        if len(label) > max_chars:
            # Add padding for smooth loop
            padded = label + "    " + label
            char_width = 4
            total_width = len(label + "    ") * char_width
            offset = int(self.scroll_offset) % total_width
            self.display.draw_text_small(2 - offset, 58, padded, Colors.WHITE)
        else:
            self.display.draw_text_small(2, 58, label, Colors.WHITE)

    def _draw_backbone_segment(self, x1, y1, x2, y2, color, ss):
        """Draw a backbone segment with thickness based on secondary structure."""
        ix1, iy1 = int(round(x1)), int(round(y1))
        ix2, iy2 = int(round(x2)), int(round(y2))

        # Draw main line
        self.display.draw_line(ix1, iy1, ix2, iy2, color)

        # For helices and sheets, draw thicker (offset lines)
        if ss in ('H', 'G', 'I', 'E', 'B'):
            # Calculate perpendicular offset for thickness
            dx = x2 - x1
            dy = y2 - y1
            length = math.sqrt(dx * dx + dy * dy)
            if length > 0:
                # Perpendicular unit vector
                px = -dy / length
                py = dx / length

                # Draw parallel lines for thickness
                dimmed = (color[0] // 2, color[1] // 2, color[2] // 2)
                self.display.draw_line(
                    int(round(x1 + px)), int(round(y1 + py)),
                    int(round(x2 + px)), int(round(y2 + py)),
                    dimmed
                )
                self.display.draw_line(
                    int(round(x1 - px)), int(round(y1 - py)),
                    int(round(x2 - px)), int(round(y2 - py)),
                    dimmed
                )
