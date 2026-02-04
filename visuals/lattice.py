"""
Lattice - 3D Crystal Lattice Structures
========================================
Rotating 3D tiled unit cells of crystalline structures.
Shows 2x2x2 tiled lattices with edge fading to suggest infinite periodicity.

Controls:
  Up/Down  - Cycle through crystal structures
  Space    - Toggle auto-cycle on/off
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE
from .molecule import CPK_COLORS, CPK_RADIUS


# Extend CPK colors with additional metals for crystals
LATTICE_COLORS = dict(CPK_COLORS)
LATTICE_COLORS.update({
    'Cu': (200, 128, 51),      # Copper - copper/orange
    'Ca': (61, 255, 0),        # Calcium - lime green
    'Ti': (191, 194, 199),     # Titanium - silver-gray
})

LATTICE_RADIUS = dict(CPK_RADIUS)
LATTICE_RADIUS.update({
    'Cu': 3,
    'Ca': 3,
    'Ti': 3,
})

BOND_COLOR = (60, 60, 60)  # Dim gray for lattice bonds


# Crystal structure definitions
# Each has fractional coordinates (0-1) within the unit cell
CRYSTALS = [
    {
        'name': 'DIAMOND',
        'formula': 'C',
        'system': 'Cubic',
        'a': 3.57,  # Lattice constant (Angstroms)
        'basis': [
            # FCC positions
            ('C', 0.0, 0.0, 0.0),
            ('C', 0.5, 0.5, 0.0),
            ('C', 0.5, 0.0, 0.5),
            ('C', 0.0, 0.5, 0.5),
            # Additional tetrahedral positions
            ('C', 0.25, 0.25, 0.25),
            ('C', 0.75, 0.75, 0.25),
            ('C', 0.75, 0.25, 0.75),
            ('C', 0.25, 0.75, 0.75),
        ],
        'bond_cutoff': 0.45,  # Fraction of lattice constant
    },
    {
        'name': 'SALT',
        'formula': 'NaCl',
        'system': 'Cubic',
        'a': 5.64,
        'basis': [
            # Na atoms (FCC)
            ('Na', 0.0, 0.0, 0.0),
            ('Na', 0.5, 0.5, 0.0),
            ('Na', 0.5, 0.0, 0.5),
            ('Na', 0.0, 0.5, 0.5),
            # Cl atoms (offset FCC)
            ('Cl', 0.5, 0.0, 0.0),
            ('Cl', 0.0, 0.5, 0.0),
            ('Cl', 0.0, 0.0, 0.5),
            ('Cl', 0.5, 0.5, 0.5),
        ],
        'bond_cutoff': 0.52,
    },
    {
        'name': 'IRON BCC',
        'formula': 'Fe',
        'system': 'Cubic',
        'a': 2.87,
        'basis': [
            ('Fe', 0.0, 0.0, 0.0),
            ('Fe', 0.5, 0.5, 0.5),
        ],
        'bond_cutoff': 0.90,
    },
    {
        'name': 'COPPER',
        'formula': 'Cu',
        'system': 'Cubic',
        'a': 3.61,
        'basis': [
            # FCC
            ('Cu', 0.0, 0.0, 0.0),
            ('Cu', 0.5, 0.5, 0.0),
            ('Cu', 0.5, 0.0, 0.5),
            ('Cu', 0.0, 0.5, 0.5),
        ],
        'bond_cutoff': 0.75,
    },
    {
        'name': 'GRAPHITE',
        'formula': 'C',
        'system': 'Hexagonal',
        'a': 2.46,  # In-plane lattice constant
        'c': 6.71,  # Out-of-plane (layer spacing)
        'basis': [
            # Layer 1
            ('C', 0.0, 0.0, 0.0),
            ('C', 0.333, 0.667, 0.0),
            # Layer 2 (shifted)
            ('C', 0.0, 0.0, 0.5),
            ('C', 0.667, 0.333, 0.5),
        ],
        'bond_cutoff': 0.60,
    },
    {
        'name': 'ICE',
        'formula': 'H2O',
        'system': 'Hexagonal',
        'a': 4.52,
        'c': 7.36,
        'basis': [
            # Oxygen atoms in hexagonal ice Ih
            ('O', 0.0, 0.0, 0.0),
            ('O', 0.333, 0.667, 0.0625),
            ('O', 0.333, 0.667, 0.4375),
            ('O', 0.0, 0.0, 0.5),
        ],
        'bond_cutoff': 0.65,
    },
    {
        'name': 'PEROVSKITE',
        'formula': 'CaTiO3',
        'system': 'Cubic',
        'a': 3.90,  # CaTiO3
        'basis': [
            ('Ca', 0.0, 0.0, 0.0),
            ('Ti', 0.5, 0.5, 0.5),
            ('O', 0.5, 0.5, 0.0),
            ('O', 0.5, 0.0, 0.5),
            ('O', 0.0, 0.5, 0.5),
        ],
        'bond_cutoff': 0.55,
    },
    {
        'name': 'SiC',
        'formula': 'SiC',
        'system': 'Cubic',
        'a': 4.36,  # Silicon carbide (zincblende)
        'basis': [
            # Si FCC
            ('Si', 0.0, 0.0, 0.0),
            ('Si', 0.5, 0.5, 0.0),
            ('Si', 0.5, 0.0, 0.5),
            ('Si', 0.0, 0.5, 0.5),
            # C tetrahedral
            ('C', 0.25, 0.25, 0.25),
            ('C', 0.75, 0.75, 0.25),
            ('C', 0.75, 0.25, 0.75),
            ('C', 0.25, 0.75, 0.75),
        ],
        'bond_cutoff': 0.45,
    },
]


class Lattice(Visual):
    name = "LATTICE"
    description = "Crystal lattice structures"
    category = "science"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.crystal_idx = random.randint(0, len(CRYSTALS) - 1)
        self.rotation_y = 0.0
        self.rotation_speed = 0.3  # Slower than molecule.py
        self.tilt_phase = 0.0
        self.auto_cycle = True
        self.cycle_timer = 0.0
        self.cycle_duration = 10.0  # Longer than molecules
        self.tiles = 2  # 2x2x2 tiling
        self.label_timer = 0.0  # For cycling label display
        self._prepare_crystal()

    def _prepare_crystal(self):
        """Pre-compute tiled atoms, bonds, and scaling for current crystal."""
        crystal = CRYSTALS[self.crystal_idx]
        basis = crystal['basis']
        a = crystal['a']
        c = crystal.get('c', a)  # For hexagonal, otherwise same as a

        # Generate tiled atoms with fade values
        self.tiled_atoms = []
        tiles = self.tiles
        center = (tiles - 1) / 2.0  # 0.5 for 2x2x2
        max_dist = math.sqrt(3) * center  # Corner distance from center

        for ti in range(tiles):
            for tj in range(tiles):
                for tk in range(tiles):
                    # Compute fade based on distance from center tile
                    dist = math.sqrt(
                        (ti - center) ** 2 +
                        (tj - center) ** 2 +
                        (tk - center) ** 2
                    )
                    # Full brightness in center, fade to 40% at corners
                    fade = 1.0 - (dist / max_dist) * 0.6 if max_dist > 0 else 1.0

                    for elem, fx, fy, fz in basis:
                        # Convert fractional to Cartesian with tile offset
                        x = (fx + ti) * a
                        y = (fy + tj) * a
                        z = (fz + tk) * c
                        self.tiled_atoms.append((elem, x, y, z, fade))

        # Center the structure
        if self.tiled_atoms:
            cx = sum(a[1] for a in self.tiled_atoms) / len(self.tiled_atoms)
            cy = sum(a[2] for a in self.tiled_atoms) / len(self.tiled_atoms)
            cz = sum(a[3] for a in self.tiled_atoms) / len(self.tiled_atoms)
            self.offset = (cx, cy, cz)
        else:
            self.offset = (0, 0, 0)

        # Compute scale
        max_r = 0.0
        for elem, x, y, z, fade in self.tiled_atoms:
            dx, dy, dz = x - self.offset[0], y - self.offset[1], z - self.offset[2]
            r = math.sqrt(dx * dx + dy * dy + dz * dz)
            max_r = max(max_r, r)

        target_radius = 22.0
        self.scale = target_radius / max_r if max_r > 0 else 10.0

        # Generate bonds by distance cutoff
        self._generate_bonds(crystal)

        # Reset label timer when switching crystals
        self.label_timer = 0.0

    def _generate_bonds(self, crystal):
        """Generate bonds between atoms within cutoff distance."""
        self.bonds = []
        cutoff = crystal['bond_cutoff'] * crystal['a']

        n = len(self.tiled_atoms)
        for i in range(n):
            _, x1, y1, z1, f1 = self.tiled_atoms[i]
            for j in range(i + 1, n):
                _, x2, y2, z2, f2 = self.tiled_atoms[j]
                dist = math.sqrt(
                    (x2 - x1) ** 2 +
                    (y2 - y1) ** 2 +
                    (z2 - z1) ** 2
                )
                if dist < cutoff and dist > 0.01:
                    # Bond fade is minimum of both atom fades
                    bond_fade = min(f1, f2)
                    self.bonds.append((i, j, bond_fade))

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.up_pressed:
            self.crystal_idx = (self.crystal_idx - 1) % len(CRYSTALS)
            self.cycle_timer = 0.0
            self._prepare_crystal()
            consumed = True
        if input_state.down_pressed:
            self.crystal_idx = (self.crystal_idx + 1) % len(CRYSTALS)
            self.cycle_timer = 0.0
            self._prepare_crystal()
            consumed = True
        if input_state.action_l or input_state.action_r:
            self.auto_cycle = not self.auto_cycle
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt
        self.label_timer += dt
        self.rotation_y += self.rotation_speed * dt
        self.tilt_phase += dt * 0.3  # Slower tilt

        if self.auto_cycle:
            self.cycle_timer += dt
            if self.cycle_timer >= self.cycle_duration:
                self.cycle_timer = 0.0
                self.crystal_idx = (self.crystal_idx + 1) % len(CRYSTALS)
                self._prepare_crystal()

    def _transform_point(self, x, y, z):
        """Apply rotation and project to screen coords."""
        x -= self.offset[0]
        y -= self.offset[1]
        z -= self.offset[2]
        x *= self.scale
        y *= self.scale
        z *= self.scale

        # X-axis tilt (slower sinusoidal)
        tilt = 0.26 * math.sin(self.tilt_phase)
        cos_t, sin_t = math.cos(tilt), math.sin(tilt)
        y2 = y * cos_t - z * sin_t
        z2 = y * sin_t + z * cos_t

        # Y-axis rotation
        cos_r, sin_r = math.cos(self.rotation_y), math.sin(self.rotation_y)
        x2 = x * cos_r + z2 * sin_r
        z3 = -x * sin_r + z2 * cos_r

        screen_x = GRID_SIZE // 2 + x2
        screen_y = 28 - y2
        return screen_x, screen_y, z3

    def draw(self):
        self.display.clear(Colors.BLACK)

        crystal = CRYSTALS[self.crystal_idx]

        # Transform all atoms
        transformed = []
        for elem, ax, ay, az, fade in self.tiled_atoms:
            if fade < 0.15:
                continue  # Skip very faded atoms
            sx, sy, sz = self._transform_point(ax, ay, az)
            transformed.append((elem, sx, sy, sz, fade))

        # Build draw list with z-sorting
        draw_list = []

        # Add bonds
        for i, j, bond_fade in self.bonds:
            if bond_fade < 0.15:
                continue
            e1, x1, y1, z1, f1 = self.tiled_atoms[i]
            e2, x2, y2, z2, f2 = self.tiled_atoms[j]
            sx1, sy1, sz1 = self._transform_point(x1, y1, z1)
            sx2, sy2, sz2 = self._transform_point(x2, y2, z2)
            avg_z = (sz1 + sz2) / 2
            draw_list.append(('bond', avg_z, sx1, sy1, sx2, sy2, bond_fade))

        # Add atoms
        for elem, sx, sy, sz, fade in transformed:
            r = LATTICE_RADIUS.get(elem, 3)
            color = LATTICE_COLORS.get(elem, (200, 200, 200))
            draw_list.append(('atom', sz, sx, sy, r, color, fade))

        # Sort by z (painter's algorithm)
        draw_list.sort(key=lambda item: item[1])

        # Render
        for item in draw_list:
            if item[0] == 'bond':
                _, _, x1, y1, x2, y2, fade = item
                self._draw_bond(x1, y1, x2, y2, fade)
            else:
                _, _, sx, sy, r, color, fade = item
                self._draw_atom(sx, sy, r, color, fade)

        # Bottom label: cycle between name, system, formula (3s each)
        label_phase = int(self.label_timer / 3) % 3
        if label_phase == 0:
            label = crystal['name']
        elif label_phase == 1:
            label = crystal['system']
        else:
            label = crystal['formula']
        self.display.draw_text_small(2, 58, label, Colors.WHITE)

    def _draw_atom(self, cx, cy, r, color, fade):
        """Draw a filled circle with simple shading and fade."""
        icx = int(round(cx))
        icy = int(round(cy))

        # Apply fade to color
        color = (
            int(color[0] * fade),
            int(color[1] * fade),
            int(color[2] * fade),
        )

        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if dx * dx + dy * dy <= r * r:
                    # Simple highlight shading
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist < r * 0.4:
                        t = dist / (r * 0.4)
                        shade = 1.0 + (1.0 - t) * 0.4
                    else:
                        shade = 1.0 - (dist / r) * 0.3
                    c = (
                        min(255, int(color[0] * shade)),
                        min(255, int(color[1] * shade)),
                        min(255, int(color[2] * shade)),
                    )
                    self.display.set_pixel(icx + dx, icy + dy, c)

    def _draw_bond(self, x1, y1, x2, y2, fade):
        """Draw a bond line with fade applied."""
        ix1, iy1 = int(round(x1)), int(round(y1))
        ix2, iy2 = int(round(x2)), int(round(y2))
        color = (
            int(BOND_COLOR[0] * fade),
            int(BOND_COLOR[1] * fade),
            int(BOND_COLOR[2] * fade),
        )
        self.display.draw_line(ix1, iy1, ix2, iy2, color)
