"""
Lattice - 3D Crystal Lattice Structures
========================================
Rotating 3D tiled unit cells of crystalline structures.
Shows 2x2x2 tiled lattices with edge fading to suggest infinite periodicity.

Controls:
  Up/Down    - Cycle through categories
  Left/Right - Browse structures in current category
  Space      - Toggle auto-cycle on/off
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE
from .molecule import CPK_COLORS, CPK_RADIUS


# Extend CPK colors with additional elements for crystals
LATTICE_COLORS = dict(CPK_COLORS)
LATTICE_COLORS.update({
    'Cu': (200, 128, 51),      # Copper - copper/orange
    'Ca': (61, 255, 0),        # Calcium - lime green
    'Ti': (191, 194, 199),     # Titanium - silver-gray
    'Au': (255, 209, 35),      # Gold - gold
    'Ag': (192, 192, 192),     # Silver - silver
    'Zn': (125, 128, 176),     # Zinc - slate blue
    'Al': (191, 166, 166),     # Aluminum - pink-gray
    'Cr': (138, 153, 199),     # Chromium - steel blue
    'Mg': (138, 255, 0),       # Magnesium - bright green
    'F': (144, 224, 80),       # Fluorine - yellow-green
    'Be': (194, 255, 0),       # Beryllium - lime
    'B': (255, 181, 181),      # Boron - salmon
    'Zr': (148, 224, 224),     # Zirconium - cyan
    'Ni': (80, 208, 80),       # Nickel - green-gray
    'Sn': (102, 128, 128),     # Tin - gray
    'K': (143, 64, 212),       # Potassium - purple
})

LATTICE_RADIUS = dict(CPK_RADIUS)
LATTICE_RADIUS.update({
    'Cu': 3,
    'Ca': 3,
    'Ti': 3,
    'Au': 3,
    'Ag': 3,
    'Zn': 3,
    'Al': 3,
    'Cr': 3,
    'Mg': 3,
    'F': 2,
    'Be': 2,
    'B': 2,
    'Zr': 3,
    'Ni': 3,
    'Sn': 3,
    'K': 3,
})

BOND_COLOR = (60, 60, 60)  # Dim gray for lattice bonds


# Categories: (key, display_name, color)
CATEGORIES = [
    ('all', 'ALL', (255, 255, 255)),
    ('gems', 'GEMS', (255, 50, 200)),
    ('minerals', 'MINERALS', (100, 200, 255)),
    ('carbon', 'CARBON', (160, 160, 160)),
    ('metals', 'METALS', (255, 200, 100)),
    ('steel', 'STEEL', (180, 180, 200)),
    ('ceramics', 'CERAMICS', (255, 150, 100)),
    ('glass', 'GLASS', (150, 220, 255)),
]


# Crystal structure definitions with accurate crystallographic data
# Each has fractional coordinates (0-1) within the unit cell
CRYSTALS = [
    # ══════════════════════════════════════════════════════════════════
    # GEMS - Precious and semi-precious stones
    # ══════════════════════════════════════════════════════════════════
    {
        'name': 'DIAMOND',
        'formula': 'C',
        'system': 'Cubic',
        'categories': ['gems', 'carbon'],
        'a': 3.57,
        'basis': [
            # FCC positions
            ('C', 0.0, 0.0, 0.0),
            ('C', 0.5, 0.5, 0.0),
            ('C', 0.5, 0.0, 0.5),
            ('C', 0.0, 0.5, 0.5),
            # Tetrahedral interstitial positions
            ('C', 0.25, 0.25, 0.25),
            ('C', 0.75, 0.75, 0.25),
            ('C', 0.75, 0.25, 0.75),
            ('C', 0.25, 0.75, 0.75),
        ],
        'bond_cutoff': 0.45,
    },
    {
        'name': 'RUBY',
        'formula': 'Al2O3',
        'system': 'Trigonal',
        'categories': ['gems', 'ceramics'],
        'a': 4.76,
        'c': 4.04,  # Simplified hexagonal approximation
        'basis': [
            # Corundum structure (simplified)
            # Al in octahedral coordination
            ('Al', 0.0, 0.0, 0.35),
            ('Al', 0.0, 0.0, 0.65),
            ('Al', 0.333, 0.667, 0.02),
            ('Al', 0.667, 0.333, 0.68),
            # O in hexagonal close-packed layers
            ('O', 0.306, 0.0, 0.25),
            ('O', 0.0, 0.306, 0.25),
            ('O', 0.694, 0.694, 0.25),
            ('O', 0.639, 0.0, 0.75),
            ('O', 0.0, 0.639, 0.75),
            ('O', 0.361, 0.361, 0.75),
            # Trace Cr gives red color (shown as Al here)
        ],
        'bond_cutoff': 0.50,
    },
    {
        'name': 'SAPPHIRE',
        'formula': 'Al2O3',
        'system': 'Trigonal',
        'categories': ['gems', 'ceramics'],
        'a': 4.76,
        'c': 4.04,
        'basis': [
            # Same as ruby (corundum), different trace impurities
            ('Al', 0.0, 0.0, 0.35),
            ('Al', 0.0, 0.0, 0.65),
            ('Al', 0.333, 0.667, 0.02),
            ('Al', 0.667, 0.333, 0.68),
            ('O', 0.306, 0.0, 0.25),
            ('O', 0.0, 0.306, 0.25),
            ('O', 0.694, 0.694, 0.25),
            ('O', 0.639, 0.0, 0.75),
            ('O', 0.0, 0.639, 0.75),
            ('O', 0.361, 0.361, 0.75),
        ],
        'bond_cutoff': 0.50,
    },
    {
        'name': 'EMERALD',
        'formula': 'Be3Al2Si6O18',
        'system': 'Hexagonal',
        'categories': ['gems'],
        'a': 9.21,
        'c': 9.19,
        'basis': [
            # Beryl structure (simplified - showing key ring structure)
            # Si6O18 rings with Be and Al
            ('Si', 0.39, 0.12, 0.0),
            ('Si', 0.88, 0.27, 0.0),
            ('Si', 0.61, 0.73, 0.0),
            ('Si', 0.12, 0.51, 0.0),
            ('Si', 0.27, 0.39, 0.5),
            ('Si', 0.73, 0.61, 0.5),
            ('Be', 0.333, 0.667, 0.25),
            ('Be', 0.667, 0.333, 0.75),
            ('Al', 0.0, 0.0, 0.25),
            ('Al', 0.0, 0.0, 0.75),
            ('O', 0.31, 0.24, 0.0),
            ('O', 0.49, 0.0, 0.0),
            ('O', 0.76, 0.07, 0.0),
        ],
        'bond_cutoff': 0.30,
    },
    {
        'name': 'GARNET',
        'formula': 'Fe3Al2Si3O12',
        'system': 'Cubic',
        'categories': ['gems', 'minerals'],
        'a': 11.53,
        'basis': [
            # Almandine garnet (simplified)
            # Showing key structural units
            ('Fe', 0.125, 0.0, 0.25),
            ('Fe', 0.375, 0.0, 0.75),
            ('Fe', 0.875, 0.0, 0.25),
            ('Al', 0.0, 0.0, 0.0),
            ('Al', 0.5, 0.5, 0.5),
            ('Si', 0.375, 0.0, 0.25),
            ('Si', 0.125, 0.0, 0.75),
            ('O', 0.03, 0.05, 0.65),
            ('O', 0.47, 0.55, 0.15),
            ('O', 0.97, 0.45, 0.35),
            ('O', 0.53, 0.95, 0.85),
        ],
        'bond_cutoff': 0.25,
    },

    # ══════════════════════════════════════════════════════════════════
    # MINERALS - Common crystalline minerals
    # ══════════════════════════════════════════════════════════════════
    {
        'name': 'QUARTZ',
        'formula': 'SiO2',
        'system': 'Trigonal',
        'categories': ['minerals', 'ceramics'],
        'a': 4.91,
        'c': 5.41,
        'basis': [
            # Alpha-quartz structure
            ('Si', 0.470, 0.0, 0.0),
            ('Si', 0.0, 0.470, 0.333),
            ('Si', 0.530, 0.530, 0.667),
            ('O', 0.413, 0.267, 0.119),
            ('O', 0.267, 0.413, 0.548),
            ('O', 0.733, 0.146, 0.214),
            ('O', 0.146, 0.733, 0.452),
            ('O', 0.587, 0.854, 0.881),
            ('O', 0.854, 0.587, 0.786),
        ],
        'bond_cutoff': 0.42,
    },
    {
        'name': 'FLUORITE',
        'formula': 'CaF2',
        'system': 'Cubic',
        'categories': ['minerals'],
        'a': 5.46,
        'basis': [
            # Ca in FCC positions
            ('Ca', 0.0, 0.0, 0.0),
            ('Ca', 0.5, 0.5, 0.0),
            ('Ca', 0.5, 0.0, 0.5),
            ('Ca', 0.0, 0.5, 0.5),
            # F in all 8 tetrahedral holes
            ('F', 0.25, 0.25, 0.25),
            ('F', 0.75, 0.25, 0.25),
            ('F', 0.25, 0.75, 0.25),
            ('F', 0.75, 0.75, 0.25),
            ('F', 0.25, 0.25, 0.75),
            ('F', 0.75, 0.25, 0.75),
            ('F', 0.25, 0.75, 0.75),
            ('F', 0.75, 0.75, 0.75),
        ],
        'bond_cutoff': 0.50,
    },
    {
        'name': 'PYRITE',
        'formula': 'FeS2',
        'system': 'Cubic',
        'categories': ['minerals'],
        'a': 5.42,
        'basis': [
            # Fe in NaCl-type positions
            ('Fe', 0.0, 0.0, 0.0),
            ('Fe', 0.5, 0.5, 0.0),
            ('Fe', 0.5, 0.0, 0.5),
            ('Fe', 0.0, 0.5, 0.5),
            # S2 dumbbells
            ('S', 0.385, 0.385, 0.385),
            ('S', 0.615, 0.615, 0.615),
            ('S', 0.115, 0.885, 0.385),
            ('S', 0.885, 0.115, 0.615),
            ('S', 0.385, 0.115, 0.885),
            ('S', 0.615, 0.885, 0.115),
            ('S', 0.885, 0.385, 0.115),
            ('S', 0.115, 0.615, 0.885),
        ],
        'bond_cutoff': 0.45,
    },
    {
        'name': 'CALCITE',
        'formula': 'CaCO3',
        'system': 'Trigonal',
        'categories': ['minerals'],
        'a': 4.99,
        'c': 5.68,  # Simplified
        'basis': [
            # Calcite structure (simplified)
            ('Ca', 0.0, 0.0, 0.0),
            ('Ca', 0.0, 0.0, 0.5),
            ('C', 0.0, 0.0, 0.25),
            ('C', 0.0, 0.0, 0.75),
            ('O', 0.257, 0.0, 0.25),
            ('O', 0.0, 0.257, 0.25),
            ('O', 0.743, 0.743, 0.25),
            ('O', 0.257, 0.0, 0.75),
            ('O', 0.0, 0.257, 0.75),
            ('O', 0.743, 0.743, 0.75),
        ],
        'bond_cutoff': 0.40,
    },
    {
        'name': 'SALT',
        'formula': 'NaCl',
        'system': 'Cubic',
        'categories': ['minerals'],
        'a': 5.64,
        'basis': [
            # Na in FCC positions
            ('Na', 0.0, 0.0, 0.0),
            ('Na', 0.5, 0.5, 0.0),
            ('Na', 0.5, 0.0, 0.5),
            ('Na', 0.0, 0.5, 0.5),
            # Cl in offset FCC
            ('Cl', 0.5, 0.0, 0.0),
            ('Cl', 0.0, 0.5, 0.0),
            ('Cl', 0.0, 0.0, 0.5),
            ('Cl', 0.5, 0.5, 0.5),
        ],
        'bond_cutoff': 0.52,
    },

    # ══════════════════════════════════════════════════════════════════
    # CARBON - Carbon allotropes
    # ══════════════════════════════════════════════════════════════════
    {
        'name': 'GRAPHITE',
        'formula': 'C',
        'system': 'Hexagonal',
        'categories': ['carbon'],
        'a': 2.46,
        'c': 6.71,
        'basis': [
            # Layer 1 (A)
            ('C', 0.0, 0.0, 0.0),
            ('C', 0.333, 0.667, 0.0),
            # Layer 2 (B) - shifted
            ('C', 0.0, 0.0, 0.5),
            ('C', 0.667, 0.333, 0.5),
        ],
        'bond_cutoff': 0.60,
    },
    {
        'name': 'LONSDALEITE',
        'formula': 'C',
        'system': 'Hexagonal',
        'categories': ['carbon', 'gems'],
        'a': 2.52,
        'c': 4.12,
        'basis': [
            # Hexagonal diamond
            ('C', 0.333, 0.667, 0.063),
            ('C', 0.667, 0.333, 0.563),
            ('C', 0.333, 0.667, 0.437),
            ('C', 0.667, 0.333, 0.937),
        ],
        'bond_cutoff': 0.65,
    },
    {
        'name': 'FULLERENE',
        'formula': 'C60',
        'system': 'FCC',
        'categories': ['carbon'],
        'a': 14.17,  # FCC packing of C60 molecules
        'basis': [
            # Simplified C60 as a shell of carbons
            # Showing vertices of truncated icosahedron (subset)
            ('C', 0.5, 0.44, 0.5),
            ('C', 0.5, 0.56, 0.5),
            ('C', 0.44, 0.5, 0.5),
            ('C', 0.56, 0.5, 0.5),
            ('C', 0.5, 0.5, 0.44),
            ('C', 0.5, 0.5, 0.56),
            ('C', 0.47, 0.47, 0.47),
            ('C', 0.53, 0.53, 0.47),
            ('C', 0.47, 0.53, 0.53),
            ('C', 0.53, 0.47, 0.53),
            ('C', 0.53, 0.53, 0.53),
            ('C', 0.47, 0.47, 0.53),
            ('C', 0.53, 0.47, 0.47),
            ('C', 0.47, 0.53, 0.47),
        ],
        'bond_cutoff': 0.12,
    },
    {
        'name': 'GRAPHENE',
        'formula': 'C',
        'system': 'Hexagonal',
        'categories': ['carbon'],
        'a': 2.46,
        'c': 3.35,  # Single layer spacing
        'basis': [
            # Single layer honeycomb
            ('C', 0.0, 0.0, 0.5),
            ('C', 0.333, 0.667, 0.5),
        ],
        'bond_cutoff': 0.65,
    },

    # ══════════════════════════════════════════════════════════════════
    # METALS - Pure metallic elements
    # ══════════════════════════════════════════════════════════════════
    {
        'name': 'GOLD',
        'formula': 'Au',
        'system': 'Cubic',
        'categories': ['metals'],
        'a': 4.08,
        'basis': [
            # FCC
            ('Au', 0.0, 0.0, 0.0),
            ('Au', 0.5, 0.5, 0.0),
            ('Au', 0.5, 0.0, 0.5),
            ('Au', 0.0, 0.5, 0.5),
        ],
        'bond_cutoff': 0.75,
    },
    {
        'name': 'SILVER',
        'formula': 'Ag',
        'system': 'Cubic',
        'categories': ['metals'],
        'a': 4.09,
        'basis': [
            # FCC
            ('Ag', 0.0, 0.0, 0.0),
            ('Ag', 0.5, 0.5, 0.0),
            ('Ag', 0.5, 0.0, 0.5),
            ('Ag', 0.0, 0.5, 0.5),
        ],
        'bond_cutoff': 0.75,
    },
    {
        'name': 'COPPER',
        'formula': 'Cu',
        'system': 'Cubic',
        'categories': ['metals'],
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
        'name': 'BRONZE',
        'formula': 'Cu3Sn',
        'system': 'FCC',
        'categories': ['metals'],
        'a': 3.68,  # Alpha bronze (Cu-Sn alloy)
        'basis': [
            # FCC copper with tin substitution
            ('Cu', 0.0, 0.0, 0.0),
            ('Cu', 0.5, 0.5, 0.0),
            ('Cu', 0.5, 0.0, 0.5),
            ('Sn', 0.0, 0.5, 0.5),  # Sn substitutes ~10% in real bronze
        ],
        'bond_cutoff': 0.75,
    },
    {
        'name': 'TITANIUM',
        'formula': 'Ti',
        'system': 'Hexagonal',
        'categories': ['metals'],
        'a': 2.95,
        'c': 4.68,
        'basis': [
            # HCP
            ('Ti', 0.0, 0.0, 0.0),
            ('Ti', 0.333, 0.667, 0.5),
        ],
        'bond_cutoff': 1.05,
    },
    {
        'name': 'ZINC',
        'formula': 'Zn',
        'system': 'Hexagonal',
        'categories': ['metals'],
        'a': 2.66,
        'c': 4.95,
        'basis': [
            # HCP
            ('Zn', 0.0, 0.0, 0.0),
            ('Zn', 0.333, 0.667, 0.5),
        ],
        'bond_cutoff': 1.10,
    },
    {
        'name': 'ALUMINUM',
        'formula': 'Al',
        'system': 'Cubic',
        'categories': ['metals'],
        'a': 4.05,
        'basis': [
            # FCC
            ('Al', 0.0, 0.0, 0.0),
            ('Al', 0.5, 0.5, 0.0),
            ('Al', 0.5, 0.0, 0.5),
            ('Al', 0.0, 0.5, 0.5),
        ],
        'bond_cutoff': 0.75,
    },

    # ══════════════════════════════════════════════════════════════════
    # STEEL - Iron phases and steel components
    # ══════════════════════════════════════════════════════════════════
    {
        'name': 'FERRITE',
        'formula': 'Fe',
        'system': 'BCC',
        'categories': ['steel', 'metals'],
        'a': 2.87,
        'basis': [
            # BCC - alpha iron (room temperature)
            ('Fe', 0.0, 0.0, 0.0),
            ('Fe', 0.5, 0.5, 0.5),
        ],
        'bond_cutoff': 0.90,
    },
    {
        'name': 'AUSTENITE',
        'formula': 'Fe',
        'system': 'FCC',
        'categories': ['steel', 'metals'],
        'a': 3.65,
        'basis': [
            # FCC - gamma iron (high temperature)
            ('Fe', 0.0, 0.0, 0.0),
            ('Fe', 0.5, 0.5, 0.0),
            ('Fe', 0.5, 0.0, 0.5),
            ('Fe', 0.0, 0.5, 0.5),
        ],
        'bond_cutoff': 0.75,
    },
    {
        'name': 'CEMENTITE',
        'formula': 'Fe3C',
        'system': 'Orthorhombic',
        'categories': ['steel'],
        'a': 5.09,
        'b': 6.74,
        'c': 4.52,
        'basis': [
            # Iron carbide (simplified)
            ('Fe', 0.18, 0.06, 0.25),
            ('Fe', 0.82, 0.94, 0.75),
            ('Fe', 0.04, 0.25, 0.75),
            ('Fe', 0.96, 0.75, 0.25),
            ('Fe', 0.33, 0.18, 0.75),
            ('Fe', 0.67, 0.82, 0.25),
            ('C', 0.43, 0.88, 0.25),
            ('C', 0.57, 0.12, 0.75),
        ],
        'bond_cutoff': 0.45,
    },
    {
        'name': 'MARTENSITE',
        'formula': 'Fe',
        'system': 'BCT',
        'categories': ['steel'],
        'a': 2.87,
        'c': 2.93,  # Slightly elongated BCC
        'basis': [
            # Body-centered tetragonal (quenched steel)
            ('Fe', 0.0, 0.0, 0.0),
            ('Fe', 0.5, 0.5, 0.5),
        ],
        'bond_cutoff': 0.90,
    },
    {
        'name': 'STAINLESS',
        'formula': 'FeCrNi',
        'system': 'FCC',
        'categories': ['steel', 'metals'],
        'a': 3.59,  # 304 stainless, austenitic
        'basis': [
            # FCC with Cr and Ni substitution (simplified)
            ('Fe', 0.0, 0.0, 0.0),
            ('Cr', 0.5, 0.5, 0.0),
            ('Fe', 0.5, 0.0, 0.5),
            ('Ni', 0.0, 0.5, 0.5),
        ],
        'bond_cutoff': 0.75,
    },

    # ══════════════════════════════════════════════════════════════════
    # CERAMICS - Technical ceramics and oxides
    # ══════════════════════════════════════════════════════════════════
    {
        'name': 'ALUMINA',
        'formula': 'Al2O3',
        'system': 'Trigonal',
        'categories': ['ceramics'],
        'a': 4.76,
        'c': 4.04,
        'basis': [
            # Same as corundum/ruby/sapphire
            ('Al', 0.0, 0.0, 0.35),
            ('Al', 0.0, 0.0, 0.65),
            ('Al', 0.333, 0.667, 0.02),
            ('Al', 0.667, 0.333, 0.68),
            ('O', 0.306, 0.0, 0.25),
            ('O', 0.0, 0.306, 0.25),
            ('O', 0.694, 0.694, 0.25),
            ('O', 0.639, 0.0, 0.75),
            ('O', 0.0, 0.639, 0.75),
            ('O', 0.361, 0.361, 0.75),
        ],
        'bond_cutoff': 0.50,
    },
    {
        'name': 'ZIRCONIA',
        'formula': 'ZrO2',
        'system': 'Cubic',
        'categories': ['ceramics', 'gems'],
        'a': 5.07,
        'basis': [
            # Cubic stabilized zirconia (fluorite-type)
            ('Zr', 0.0, 0.0, 0.0),
            ('Zr', 0.5, 0.5, 0.0),
            ('Zr', 0.5, 0.0, 0.5),
            ('Zr', 0.0, 0.5, 0.5),
            ('O', 0.25, 0.25, 0.25),
            ('O', 0.75, 0.25, 0.25),
            ('O', 0.25, 0.75, 0.25),
            ('O', 0.75, 0.75, 0.25),
            ('O', 0.25, 0.25, 0.75),
            ('O', 0.75, 0.25, 0.75),
            ('O', 0.25, 0.75, 0.75),
            ('O', 0.75, 0.75, 0.75),
        ],
        'bond_cutoff': 0.50,
    },
    {
        'name': 'BORON NITRIDE',
        'formula': 'BN',
        'system': 'Hexagonal',
        'categories': ['ceramics'],
        'a': 2.50,
        'c': 6.66,
        'basis': [
            # Hexagonal BN (like graphite)
            ('B', 0.0, 0.0, 0.0),
            ('N', 0.333, 0.667, 0.0),
            ('B', 0.0, 0.0, 0.5),
            ('N', 0.667, 0.333, 0.5),
        ],
        'bond_cutoff': 0.60,
    },
    {
        'name': 'SPINEL',
        'formula': 'MgAl2O4',
        'system': 'Cubic',
        'categories': ['ceramics', 'gems'],
        'a': 8.08,
        'basis': [
            # Spinel structure (simplified)
            ('Mg', 0.125, 0.125, 0.125),
            ('Mg', 0.625, 0.625, 0.125),
            ('Al', 0.5, 0.5, 0.5),
            ('Al', 0.5, 0.0, 0.0),
            ('Al', 0.0, 0.5, 0.0),
            ('Al', 0.0, 0.0, 0.5),
            ('O', 0.26, 0.26, 0.26),
            ('O', 0.74, 0.74, 0.26),
            ('O', 0.26, 0.74, 0.74),
            ('O', 0.74, 0.26, 0.74),
        ],
        'bond_cutoff': 0.30,
    },
    {
        'name': 'PEROVSKITE',
        'formula': 'CaTiO3',
        'system': 'Cubic',
        'categories': ['ceramics'],
        'a': 3.90,
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
        'categories': ['ceramics'],
        'a': 4.36,
        'basis': [
            # Zincblende structure
            ('Si', 0.0, 0.0, 0.0),
            ('Si', 0.5, 0.5, 0.0),
            ('Si', 0.5, 0.0, 0.5),
            ('Si', 0.0, 0.5, 0.5),
            ('C', 0.25, 0.25, 0.25),
            ('C', 0.75, 0.75, 0.25),
            ('C', 0.75, 0.25, 0.75),
            ('C', 0.25, 0.75, 0.75),
        ],
        'bond_cutoff': 0.45,
    },
    {
        'name': 'PORCELAIN',
        'formula': 'Al6Si2O13',
        'system': 'Orthorhombic',
        'categories': ['ceramics'],
        'a': 7.54,  # Mullite - key crystal phase in porcelain
        'b': 7.69,
        'c': 2.88,
        'basis': [
            # Mullite structure (simplified)
            # Al in octahedral and tetrahedral sites
            ('Al', 0.0, 0.0, 0.0),
            ('Al', 0.5, 0.5, 0.0),
            ('Al', 0.15, 0.34, 0.5),
            ('Al', 0.85, 0.66, 0.5),
            ('Al', 0.34, 0.85, 0.5),
            ('Al', 0.66, 0.15, 0.5),
            # Si in tetrahedral sites
            ('Si', 0.25, 0.21, 0.0),
            ('Si', 0.75, 0.79, 0.0),
            # Oxygen framework
            ('O', 0.0, 0.0, 0.5),
            ('O', 0.5, 0.5, 0.5),
            ('O', 0.14, 0.44, 0.0),
            ('O', 0.86, 0.56, 0.0),
            ('O', 0.35, 0.07, 0.5),
            ('O', 0.65, 0.93, 0.5),
        ],
        'bond_cutoff': 0.35,
    },

    # ══════════════════════════════════════════════════════════════════
    # GLASS - Amorphous structures
    # ══════════════════════════════════════════════════════════════════
    {
        'name': 'GLASS',
        'formula': 'SiO2',
        'system': 'Amorphous',
        'categories': ['glass'],
        'a': 5.0,
        'amorphous': True,
        'basis': [],  # Generated procedurally
        'bond_cutoff': 0.42,
    },
    {
        'name': 'OBSIDIAN',
        'formula': 'SiO2',
        'system': 'Amorphous',
        'categories': ['glass', 'minerals'],
        'a': 5.0,
        'amorphous': True,
        'basis': [],  # Generated procedurally
        'bond_cutoff': 0.42,
    },

    # ══════════════════════════════════════════════════════════════════
    # ICE - Water ice with full H2O structure
    # ══════════════════════════════════════════════════════════════════
    {
        'name': 'ICE',
        'formula': 'H2O',
        'system': 'Hexagonal',
        'categories': ['minerals'],
        'a': 4.52,
        'c': 7.36,
        'basis': [
            # Ice Ih - oxygen positions with hydrogens
            # Oxygen framework
            ('O', 0.0, 0.0, 0.0625),
            ('O', 0.333, 0.667, 0.5625),
            ('O', 0.667, 0.333, 0.9375),
            ('O', 0.0, 0.0, 0.4375),
            # Hydrogen positions (approximate, ordered)
            ('H', 0.12, 0.0, 0.0),
            ('H', 0.0, 0.12, 0.125),
            ('H', 0.45, 0.55, 0.5),
            ('H', 0.21, 0.79, 0.625),
            ('H', 0.79, 0.45, 0.875),
            ('H', 0.55, 0.21, 1.0),
            ('H', 0.12, 0.12, 0.375),
            ('H', 0.88, 0.0, 0.5),
        ],
        'bond_cutoff': 0.35,
    },
]


def _build_category_indices():
    """Build mapping from category key to list of crystal indices."""
    indices = {'all': list(range(len(CRYSTALS)))}
    for key, _, _ in CATEGORIES:
        if key != 'all':
            indices[key] = []
    for i, crystal in enumerate(CRYSTALS):
        for cat in crystal.get('categories', []):
            if cat in indices:
                indices[cat].append(i)
    return indices


def _generate_amorphous_structure(crystal, seed=None):
    """Generate amorphous (glass-like) structure with local tetrahedral order."""
    if seed is not None:
        random.seed(seed)

    a = crystal['a']
    atoms = []

    # Generate Si atoms in roughly random positions
    n_si = 8
    si_positions = []
    for _ in range(n_si):
        # Random position with some minimum spacing
        for _ in range(100):  # Max attempts
            x = random.random()
            y = random.random()
            z = random.random()
            # Check distance to existing Si
            too_close = False
            for sx, sy, sz in si_positions:
                dx = min(abs(x - sx), 1 - abs(x - sx))
                dy = min(abs(y - sy), 1 - abs(y - sy))
                dz = min(abs(z - sz), 1 - abs(z - sz))
                if math.sqrt(dx*dx + dy*dy + dz*dz) < 0.25:
                    too_close = True
                    break
            if not too_close:
                si_positions.append((x, y, z))
                atoms.append(('Si', x, y, z))
                break

    # Add O atoms between Si pairs (bridging oxygens)
    for i, (x1, y1, z1) in enumerate(si_positions):
        for j, (x2, y2, z2) in enumerate(si_positions):
            if i >= j:
                continue
            # Calculate distance (with periodic boundaries)
            dx = x2 - x1
            dy = y2 - y1
            dz = z2 - z1
            # Minimum image
            if dx > 0.5: dx -= 1
            if dx < -0.5: dx += 1
            if dy > 0.5: dy -= 1
            if dy < -0.5: dy += 1
            if dz > 0.5: dz -= 1
            if dz < -0.5: dz += 1
            dist = math.sqrt(dx*dx + dy*dy + dz*dz)
            # Add bridging O if Si atoms are close enough
            if 0.28 < dist < 0.45:
                # O at midpoint with small random offset
                ox = (x1 + x2) / 2 + random.uniform(-0.03, 0.03)
                oy = (y1 + y2) / 2 + random.uniform(-0.03, 0.03)
                oz = (z1 + z2) / 2 + random.uniform(-0.03, 0.03)
                atoms.append(('O', ox % 1, oy % 1, oz % 1))

    return atoms


class Lattice(Visual):
    name = "LATTICE"
    description = "Crystal lattice structures"
    category = "science"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.category_indices = _build_category_indices()
        self.category_idx = 0  # Index into CATEGORIES
        self.crystal_pos = random.randint(0, len(CRYSTALS) - 1)
        self.rotation_y = 0.0
        self.rotation_speed = 0.3  # Slower than molecule.py
        self.tilt_phase = 0.0
        self.auto_cycle = True
        self.cycle_timer = 0.0
        self.cycle_duration = 10.0
        self.tiles = 2  # 2x2x2 tiling
        self.label_timer = 0.0
        self.overlay_timer = 0.0  # Category name overlay
        self._prepare_crystal()

    def _current_crystal_list(self):
        """Get list of crystal indices for current category."""
        key = CATEGORIES[self.category_idx][0]
        return self.category_indices.get(key, [])

    def _current_crystal_index(self):
        """Get the global CRYSTALS index for the current selection."""
        crystal_list = self._current_crystal_list()
        if not crystal_list:
            return 0
        return crystal_list[self.crystal_pos % len(crystal_list)]

    def _prepare_crystal(self):
        """Pre-compute tiled atoms, bonds, and scaling for current crystal."""
        crystal = CRYSTALS[self._current_crystal_index()]

        # Handle amorphous structures specially
        if crystal.get('amorphous', False):
            basis = _generate_amorphous_structure(
                crystal, seed=self._current_crystal_index()
            )
        else:
            basis = crystal['basis']

        a = crystal['a']
        b = crystal.get('b', a)
        c = crystal.get('c', a)

        # Generate tiled atoms with fade values
        self.tiled_atoms = []
        tiles = self.tiles
        center = (tiles - 1) / 2.0
        max_dist = math.sqrt(3) * center if center > 0 else 1

        for ti in range(tiles):
            for tj in range(tiles):
                for tk in range(tiles):
                    # Compute fade based on distance from center
                    dist = math.sqrt(
                        (ti - center) ** 2 +
                        (tj - center) ** 2 +
                        (tk - center) ** 2
                    )
                    fade = 1.0 - (dist / max_dist) * 0.6 if max_dist > 0 else 1.0

                    for atom in basis:
                        elem, fx, fy, fz = atom[0], atom[1], atom[2], atom[3]
                        # Convert fractional to Cartesian with tile offset
                        x = (fx + ti) * a
                        y = (fy + tj) * b
                        z = (fz + tk) * c
                        self.tiled_atoms.append((elem, x, y, z, fade))

        # Center the structure
        if self.tiled_atoms:
            cx = sum(atom[1] for atom in self.tiled_atoms) / len(self.tiled_atoms)
            cy = sum(atom[2] for atom in self.tiled_atoms) / len(self.tiled_atoms)
            cz = sum(atom[3] for atom in self.tiled_atoms) / len(self.tiled_atoms)
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

        # Reset label timer
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
                    bond_fade = min(f1, f2)
                    self.bonds.append((i, j, bond_fade))

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Up/Down: cycle categories
        if input_state.up_pressed:
            self.category_idx = (self.category_idx - 1) % len(CATEGORIES)
            self.crystal_pos = 0
            self.cycle_timer = 0.0
            self.overlay_timer = 2.5
            self._prepare_crystal()
            consumed = True
        if input_state.down_pressed:
            self.category_idx = (self.category_idx + 1) % len(CATEGORIES)
            self.crystal_pos = 0
            self.cycle_timer = 0.0
            self.overlay_timer = 2.5
            self._prepare_crystal()
            consumed = True

        # Left/Right: cycle within category
        if input_state.left_pressed:
            crystal_list = self._current_crystal_list()
            if crystal_list:
                self.crystal_pos = (self.crystal_pos - 1) % len(crystal_list)
            self.cycle_timer = 0.0
            self._prepare_crystal()
            consumed = True
        if input_state.right_pressed:
            crystal_list = self._current_crystal_list()
            if crystal_list:
                self.crystal_pos = (self.crystal_pos + 1) % len(crystal_list)
            self.cycle_timer = 0.0
            self._prepare_crystal()
            consumed = True

        # Space: toggle auto-cycle
        if input_state.action_l or input_state.action_r:
            self.auto_cycle = not self.auto_cycle
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt
        self.label_timer += dt
        self.rotation_y += self.rotation_speed * dt
        self.tilt_phase += dt * 0.3

        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

        if self.auto_cycle:
            self.cycle_timer += dt
            if self.cycle_timer >= self.cycle_duration:
                self.cycle_timer = 0.0
                crystal_list = self._current_crystal_list()
                if crystal_list:
                    self.crystal_pos = (self.crystal_pos + 1) % len(crystal_list)
                self._prepare_crystal()

    def _transform_point(self, x, y, z):
        """Apply rotation and project to screen coords."""
        x -= self.offset[0]
        y -= self.offset[1]
        z -= self.offset[2]
        x *= self.scale
        y *= self.scale
        z *= self.scale

        # X-axis tilt
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

        crystal = CRYSTALS[self._current_crystal_index()]

        # Transform all atoms
        transformed = []
        for elem, ax, ay, az, fade in self.tiled_atoms:
            if fade < 0.15:
                continue
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

        # Bottom label: cycle between name, system, formula
        label_phase = int(self.label_timer / 3) % 3
        if label_phase == 0:
            label = crystal['name']
        elif label_phase == 1:
            label = crystal['system']
        else:
            label = crystal['formula']
        self.display.draw_text_small(2, 58, label, Colors.WHITE)

        # Category overlay at top (fades after switching)
        if self.overlay_timer > 0:
            _, cat_name, cat_color = CATEGORIES[self.category_idx]
            alpha = min(1.0, self.overlay_timer / 0.5)
            oc = (int(cat_color[0] * alpha),
                  int(cat_color[1] * alpha),
                  int(cat_color[2] * alpha))
            self.display.draw_text_small(2, 2, cat_name, oc)

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
