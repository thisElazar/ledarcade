"""
PERIODIC - Bohr Model Atomic Orbitals
======================================
Animated 2D Bohr model atoms for all 118 elements.
Electrons orbit on fixed rings around a pulsing nucleus.
"""

import math
import random
from . import Visual, Display, Colors

# ---------------------------------------------------------------------------
# Category colours (nucleus + dim ring tint)
# ---------------------------------------------------------------------------
CATEGORY_COLORS = {
    'alkali':     (255, 100, 80),
    'alkaline':   (255, 170, 50),
    'transition': (255, 210, 100),
    'post_trans': (100, 200, 180),
    'metalloid':  (80, 200, 80),
    'nonmetal':   (80, 160, 255),
    'halogen':    (80, 240, 200),
    'noble':      (180, 130, 255),
    'lanthanide': (255, 150, 200),
    'actinide':   (255, 120, 140),
}

CATEGORY_NAMES = {
    'alkali':     'ALKALI METAL',
    'alkaline':   'ALKALINE EARTH',
    'transition': 'TRANSITION METAL',
    'post_trans': 'POST-TRANSITION',
    'metalloid':  'METALLOID',
    'nonmetal':   'NONMETAL',
    'halogen':    'HALOGEN',
    'noble':      'NOBLE GAS',
    'lanthanide': 'LANTHANIDE',
    'actinide':   'ACTINIDE',
}

# ---------------------------------------------------------------------------
# All 118 elements: (symbol, name, atomic_number, [shell_electrons], category)
# ---------------------------------------------------------------------------
ELEMENTS = [
    ('H',  'HYDROGEN',      1,  [1],                          'nonmetal'),
    ('He', 'HELIUM',         2,  [2],                          'noble'),
    ('Li', 'LITHIUM',        3,  [2, 1],                       'alkali'),
    ('Be', 'BERYLLIUM',      4,  [2, 2],                       'alkaline'),
    ('B',  'BORON',          5,  [2, 3],                       'metalloid'),
    ('C',  'CARBON',         6,  [2, 4],                       'nonmetal'),
    ('N',  'NITROGEN',       7,  [2, 5],                       'nonmetal'),
    ('O',  'OXYGEN',         8,  [2, 6],                       'nonmetal'),
    ('F',  'FLUORINE',       9,  [2, 7],                       'halogen'),
    ('Ne', 'NEON',          10,  [2, 8],                       'noble'),
    ('Na', 'SODIUM',        11,  [2, 8, 1],                    'alkali'),
    ('Mg', 'MAGNESIUM',     12,  [2, 8, 2],                    'alkaline'),
    ('Al', 'ALUMINIUM',     13,  [2, 8, 3],                    'post_trans'),
    ('Si', 'SILICON',       14,  [2, 8, 4],                    'metalloid'),
    ('P',  'PHOSPHORUS',    15,  [2, 8, 5],                    'nonmetal'),
    ('S',  'SULFUR',        16,  [2, 8, 6],                    'nonmetal'),
    ('Cl', 'CHLORINE',      17,  [2, 8, 7],                    'halogen'),
    ('Ar', 'ARGON',         18,  [2, 8, 8],                    'noble'),
    ('K',  'POTASSIUM',     19,  [2, 8, 8, 1],                 'alkali'),
    ('Ca', 'CALCIUM',       20,  [2, 8, 8, 2],                 'alkaline'),
    ('Sc', 'SCANDIUM',      21,  [2, 8, 9, 2],                 'transition'),
    ('Ti', 'TITANIUM',      22,  [2, 8, 10, 2],                'transition'),
    ('V',  'VANADIUM',      23,  [2, 8, 11, 2],                'transition'),
    ('Cr', 'CHROMIUM',      24,  [2, 8, 13, 1],                'transition'),
    ('Mn', 'MANGANESE',     25,  [2, 8, 13, 2],                'transition'),
    ('Fe', 'IRON',          26,  [2, 8, 14, 2],                'transition'),
    ('Co', 'COBALT',        27,  [2, 8, 15, 2],                'transition'),
    ('Ni', 'NICKEL',        28,  [2, 8, 16, 2],                'transition'),
    ('Cu', 'COPPER',        29,  [2, 8, 18, 1],                'transition'),
    ('Zn', 'ZINC',          30,  [2, 8, 18, 2],                'transition'),
    ('Ga', 'GALLIUM',       31,  [2, 8, 18, 3],                'post_trans'),
    ('Ge', 'GERMANIUM',     32,  [2, 8, 18, 4],                'metalloid'),
    ('As', 'ARSENIC',       33,  [2, 8, 18, 5],                'metalloid'),
    ('Se', 'SELENIUM',      34,  [2, 8, 18, 6],                'nonmetal'),
    ('Br', 'BROMINE',       35,  [2, 8, 18, 7],                'halogen'),
    ('Kr', 'KRYPTON',       36,  [2, 8, 18, 8],                'noble'),
    ('Rb', 'RUBIDIUM',      37,  [2, 8, 18, 8, 1],             'alkali'),
    ('Sr', 'STRONTIUM',     38,  [2, 8, 18, 8, 2],             'alkaline'),
    ('Y',  'YTTRIUM',       39,  [2, 8, 18, 9, 2],             'transition'),
    ('Zr', 'ZIRCONIUM',     40,  [2, 8, 18, 10, 2],            'transition'),
    ('Nb', 'NIOBIUM',       41,  [2, 8, 18, 12, 1],            'transition'),
    ('Mo', 'MOLYBDENUM',    42,  [2, 8, 18, 13, 1],            'transition'),
    ('Tc', 'TECHNETIUM',    43,  [2, 8, 18, 13, 2],            'transition'),
    ('Ru', 'RUTHENIUM',     44,  [2, 8, 18, 15, 1],            'transition'),
    ('Rh', 'RHODIUM',       45,  [2, 8, 18, 16, 1],            'transition'),
    ('Pd', 'PALLADIUM',     46,  [2, 8, 18, 18],               'transition'),
    ('Ag', 'SILVER',        47,  [2, 8, 18, 18, 1],            'transition'),
    ('Cd', 'CADMIUM',       48,  [2, 8, 18, 18, 2],            'transition'),
    ('In', 'INDIUM',        49,  [2, 8, 18, 18, 3],            'post_trans'),
    ('Sn', 'TIN',           50,  [2, 8, 18, 18, 4],            'post_trans'),
    ('Sb', 'ANTIMONY',      51,  [2, 8, 18, 18, 5],            'metalloid'),
    ('Te', 'TELLURIUM',     52,  [2, 8, 18, 18, 6],            'metalloid'),
    ('I',  'IODINE',        53,  [2, 8, 18, 18, 7],            'halogen'),
    ('Xe', 'XENON',         54,  [2, 8, 18, 18, 8],            'noble'),
    ('Cs', 'CAESIUM',       55,  [2, 8, 18, 18, 8, 1],         'alkali'),
    ('Ba', 'BARIUM',        56,  [2, 8, 18, 18, 8, 2],         'alkaline'),
    ('La', 'LANTHANUM',     57,  [2, 8, 18, 18, 9, 2],         'lanthanide'),
    ('Ce', 'CERIUM',        58,  [2, 8, 18, 19, 9, 2],         'lanthanide'),
    ('Pr', 'PRASEODYMIUM',  59,  [2, 8, 18, 21, 8, 2],         'lanthanide'),
    ('Nd', 'NEODYMIUM',     60,  [2, 8, 18, 22, 8, 2],         'lanthanide'),
    ('Pm', 'PROMETHIUM',    61,  [2, 8, 18, 23, 8, 2],         'lanthanide'),
    ('Sm', 'SAMARIUM',      62,  [2, 8, 18, 24, 8, 2],         'lanthanide'),
    ('Eu', 'EUROPIUM',      63,  [2, 8, 18, 25, 8, 2],         'lanthanide'),
    ('Gd', 'GADOLINIUM',    64,  [2, 8, 18, 25, 9, 2],         'lanthanide'),
    ('Tb', 'TERBIUM',       65,  [2, 8, 18, 27, 8, 2],         'lanthanide'),
    ('Dy', 'DYSPROSIUM',    66,  [2, 8, 18, 28, 8, 2],         'lanthanide'),
    ('Ho', 'HOLMIUM',       67,  [2, 8, 18, 29, 8, 2],         'lanthanide'),
    ('Er', 'ERBIUM',        68,  [2, 8, 18, 30, 8, 2],         'lanthanide'),
    ('Tm', 'THULIUM',       69,  [2, 8, 18, 31, 8, 2],         'lanthanide'),
    ('Yb', 'YTTERBIUM',     70,  [2, 8, 18, 32, 8, 2],         'lanthanide'),
    ('Lu', 'LUTETIUM',      71,  [2, 8, 18, 32, 9, 2],         'lanthanide'),
    ('Hf', 'HAFNIUM',       72,  [2, 8, 18, 32, 10, 2],        'transition'),
    ('Ta', 'TANTALUM',      73,  [2, 8, 18, 32, 11, 2],        'transition'),
    ('W',  'TUNGSTEN',      74,  [2, 8, 18, 32, 12, 2],        'transition'),
    ('Re', 'RHENIUM',       75,  [2, 8, 18, 32, 13, 2],        'transition'),
    ('Os', 'OSMIUM',        76,  [2, 8, 18, 32, 14, 2],        'transition'),
    ('Ir', 'IRIDIUM',       77,  [2, 8, 18, 32, 15, 2],        'transition'),
    ('Pt', 'PLATINUM',      78,  [2, 8, 18, 32, 17, 1],        'transition'),
    ('Au', 'GOLD',          79,  [2, 8, 18, 32, 18, 1],        'transition'),
    ('Hg', 'MERCURY',       80,  [2, 8, 18, 32, 18, 2],        'transition'),
    ('Tl', 'THALLIUM',      81,  [2, 8, 18, 32, 18, 3],        'post_trans'),
    ('Pb', 'LEAD',          82,  [2, 8, 18, 32, 18, 4],        'post_trans'),
    ('Bi', 'BISMUTH',       83,  [2, 8, 18, 32, 18, 5],        'post_trans'),
    ('Po', 'POLONIUM',      84,  [2, 8, 18, 32, 18, 6],        'post_trans'),
    ('At', 'ASTATINE',      85,  [2, 8, 18, 32, 18, 7],        'halogen'),
    ('Rn', 'RADON',         86,  [2, 8, 18, 32, 18, 8],        'noble'),
    ('Fr', 'FRANCIUM',      87,  [2, 8, 18, 32, 18, 8, 1],     'alkali'),
    ('Ra', 'RADIUM',        88,  [2, 8, 18, 32, 18, 8, 2],     'alkaline'),
    ('Ac', 'ACTINIUM',      89,  [2, 8, 18, 32, 18, 9, 2],     'actinide'),
    ('Th', 'THORIUM',       90,  [2, 8, 18, 32, 18, 10, 2],    'actinide'),
    ('Pa', 'PROTACTINIUM',  91,  [2, 8, 18, 32, 20, 9, 2],     'actinide'),
    ('U',  'URANIUM',       92,  [2, 8, 18, 32, 21, 9, 2],     'actinide'),
    ('Np', 'NEPTUNIUM',     93,  [2, 8, 18, 32, 22, 9, 2],     'actinide'),
    ('Pu', 'PLUTONIUM',     94,  [2, 8, 18, 32, 24, 8, 2],     'actinide'),
    ('Am', 'AMERICIUM',     95,  [2, 8, 18, 32, 25, 8, 2],     'actinide'),
    ('Cm', 'CURIUM',        96,  [2, 8, 18, 32, 25, 9, 2],     'actinide'),
    ('Bk', 'BERKELIUM',     97,  [2, 8, 18, 32, 27, 8, 2],     'actinide'),
    ('Cf', 'CALIFORNIUM',   98,  [2, 8, 18, 32, 28, 8, 2],     'actinide'),
    ('Es', 'EINSTEINIUM',   99,  [2, 8, 18, 32, 29, 8, 2],     'actinide'),
    ('Fm', 'FERMIUM',      100,  [2, 8, 18, 32, 30, 8, 2],     'actinide'),
    ('Md', 'MENDELEVIUM',  101,  [2, 8, 18, 32, 31, 8, 2],     'actinide'),
    ('No', 'NOBELIUM',     102,  [2, 8, 18, 32, 32, 8, 2],     'actinide'),
    ('Lr', 'LAWRENCIUM',   103,  [2, 8, 18, 32, 32, 8, 3],     'actinide'),
    ('Rf', 'RUTHERFORDIUM',104,  [2, 8, 18, 32, 32, 10, 2],    'transition'),
    ('Db', 'DUBNIUM',      105,  [2, 8, 18, 32, 32, 11, 2],    'transition'),
    ('Sg', 'SEABORGIUM',   106,  [2, 8, 18, 32, 32, 12, 2],    'transition'),
    ('Bh', 'BOHRIUM',      107,  [2, 8, 18, 32, 32, 13, 2],    'transition'),
    ('Hs', 'HASSIUM',      108,  [2, 8, 18, 32, 32, 14, 2],    'transition'),
    ('Mt', 'MEITNERIUM',   109,  [2, 8, 18, 32, 32, 15, 2],    'transition'),
    ('Ds', 'DARMSTADTIUM', 110,  [2, 8, 18, 32, 32, 16, 2],    'transition'),
    ('Rg', 'ROENTGENIUM',  111,  [2, 8, 18, 32, 32, 17, 2],    'transition'),
    ('Cn', 'COPERNICIUM',  112,  [2, 8, 18, 32, 32, 18, 2],    'transition'),
    ('Nh', 'NIHONIUM',     113,  [2, 8, 18, 32, 32, 18, 3],    'post_trans'),
    ('Fl', 'FLEROVIUM',    114,  [2, 8, 18, 32, 32, 18, 4],    'post_trans'),
    ('Mc', 'MOSCOVIUM',    115,  [2, 8, 18, 32, 32, 18, 5],    'post_trans'),
    ('Lv', 'LIVERMORIUM',  116,  [2, 8, 18, 32, 32, 18, 6],    'post_trans'),
    ('Ts', 'TENNESSINE',   117,  [2, 8, 18, 32, 32, 18, 7],    'halogen'),
    ('Og', 'OGANESSON',    118,  [2, 8, 18, 32, 32, 18, 8],    'noble'),
]

# ---------------------------------------------------------------------------
# Groups for up/down cycling
# ---------------------------------------------------------------------------
GROUPS = [
    ('all',       'ALL',         (255, 255, 255)),
    ('simple',    'SIMPLE',      (80, 160, 255)),
    ('noble',     'NOBLE GASES', (180, 130, 255)),
    ('alkali',    'ALKALI',      (255, 100, 80)),
    ('halogens',  'HALOGENS',    (80, 240, 200)),
    ('life',      'LIFE',        (0, 255, 0)),
    ('precious',  'PRECIOUS',    (255, 215, 0)),
]

# Which element indices belong to each group
_LIFE_SYMBOLS = {
    'H', 'C', 'N', 'O', 'P', 'S', 'Na', 'Mg', 'Cl', 'K', 'Ca',
    'Fe', 'Zn', 'Se', 'I', 'Mn', 'Co', 'Cu', 'Mo',
}
_PRECIOUS_SYMBOLS = {'Cu', 'Ag', 'Au', 'Pt'}


def _build_group_indices():
    """Build mapping from group key to list of ELEMENTS indices."""
    indices = {'all': list(range(len(ELEMENTS)))}
    indices['simple'] = list(range(10))  # H through Ne
    indices['noble'] = []
    indices['alkali'] = []
    indices['halogens'] = []
    indices['life'] = []
    indices['precious'] = []

    for i, (sym, name, z, shells, cat) in enumerate(ELEMENTS):
        if cat == 'noble':
            indices['noble'].append(i)
        if cat == 'alkali':
            indices['alkali'].append(i)
        if cat == 'halogen':
            indices['halogens'].append(i)
        if sym in _LIFE_SYMBOLS:
            indices['life'].append(i)
        if sym in _PRECIOUS_SYMBOLS:
            indices['precious'].append(i)

    return indices


# Shell orbital radii in pixels (shells 1-7)
SHELL_RADII = [5, 9, 13, 16, 19, 22, 25]

# Angular speeds per shell (rad/s) — inner fastest
SHELL_SPEEDS = [2.0, 1.5, 1.1, 0.8, 0.55, 0.4, 0.3]

# Electron colour
ELECTRON_COLOR = (220, 240, 255)

# Center of atom
CX, CY = 32, 28


class Periodic(Visual):
    name = "PERIODIC"
    description = "Bohr model atomic orbitals"
    category = "science"

    def reset(self):
        self.time = 0.0
        self.group_indices = _build_group_indices()
        self.group_idx = 0
        self.elem_pos = 0
        self.auto_cycle = True
        self.cycle_timer = 0.0
        self.cycle_duration = 8.0
        self.overlay_timer = 0.0
        self.label_timer = 0.0
        self.scroll_offset = 0.0
        self.flash_timer = 0.0
        # Random phase jitter per electron (regenerated on element change)
        self.phase_jitter = []
        self._prepare_element()

    def _current_elem_list(self):
        """Get list of element indices for current group."""
        key = GROUPS[self.group_idx][0]
        return self.group_indices.get(key, [])

    def _current_elem_index(self):
        """Get the global ELEMENTS index for the current selection."""
        elem_list = self._current_elem_list()
        if not elem_list:
            return 0
        return elem_list[self.elem_pos % len(elem_list)]

    def _prepare_element(self):
        """Set up rendering data for the current element."""
        idx = self._current_elem_index()
        sym, name, z, shells, cat = ELEMENTS[idx]

        self.cur_symbol = sym
        self.cur_name = name
        self.cur_z = z
        self.cur_shells = shells
        self.cur_cat = cat
        self.cur_color = CATEGORY_COLORS.get(cat, (200, 200, 200))
        self.nucleus_r = 2 + min(2, z // 40)

        # Generate random phase jitter for each electron
        self.phase_jitter = []
        for n_electrons in shells:
            jitters = [random.uniform(0, 0.3) for _ in range(n_electrons)]
            self.phase_jitter.append(jitters)

        self.label_timer = 0.0
        self.scroll_offset = 0.0
        self.flash_timer = 0.3

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.up_pressed:
            self.group_idx = (self.group_idx - 1) % len(GROUPS)
            self.elem_pos = 0
            self.cycle_timer = 0.0
            self.overlay_timer = 2.5
            self._prepare_element()
            consumed = True
        if input_state.down_pressed:
            self.group_idx = (self.group_idx + 1) % len(GROUPS)
            self.elem_pos = 0
            self.cycle_timer = 0.0
            self.overlay_timer = 2.5
            self._prepare_element()
            consumed = True
        if input_state.left_pressed:
            elem_list = self._current_elem_list()
            if elem_list:
                self.elem_pos = (self.elem_pos - 1) % len(elem_list)
            self.cycle_timer = 0.0
            self._prepare_element()
            consumed = True
        if input_state.right_pressed:
            elem_list = self._current_elem_list()
            if elem_list:
                self.elem_pos = (self.elem_pos + 1) % len(elem_list)
            self.cycle_timer = 0.0
            self._prepare_element()
            consumed = True
        if input_state.action_l or input_state.action_r:
            self.auto_cycle = not self.auto_cycle
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt
        self.label_timer += dt
        self.scroll_offset += dt * 20

        if self.flash_timer > 0:
            self.flash_timer = max(0.0, self.flash_timer - dt)

        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

        if self.auto_cycle:
            self.cycle_timer += dt
            if self.cycle_timer >= self.cycle_duration:
                self.cycle_timer = 0.0
                elem_list = self._current_elem_list()
                if elem_list:
                    self.elem_pos = (self.elem_pos + 1) % len(elem_list)
                self._prepare_element()

    def draw(self):
        d = self.display
        d.clear()

        # --- Shell rings (dim outlines) ---
        dim = tuple(max(1, c // 8) for c in self.cur_color)
        for i, n_electrons in enumerate(self.cur_shells):
            if n_electrons > 0 and i < len(SHELL_RADII):
                d.draw_circle(CX, CY, SHELL_RADII[i], dim, filled=False)

        # --- Nucleus (filled circle with pulse) ---
        pulse = 1.0 + 0.15 * math.sin(self.time * math.pi)
        # Flash on transition
        if self.flash_timer > 0:
            flash_boost = self.flash_timer / 0.3
            pulse += flash_boost * 0.8
        nc = tuple(min(255, int(c * pulse)) for c in self.cur_color)
        d.draw_circle(CX, CY, self.nucleus_r, nc, filled=True)
        # Specular highlight at center
        highlight = tuple(min(255, c + 80) for c in nc)
        d.set_pixel(CX, CY, highlight)

        # --- Electrons ---
        t = self.time
        for shell_i, n_electrons in enumerate(self.cur_shells):
            if shell_i >= len(SHELL_RADII):
                break
            r = SHELL_RADII[shell_i]
            speed = SHELL_SPEEDS[shell_i]
            spacing = (2.0 * math.pi) / n_electrons if n_electrons > 0 else 0

            for e in range(n_electrons):
                jitter = self.phase_jitter[shell_i][e] if e < len(self.phase_jitter[shell_i]) else 0
                angle = spacing * e + jitter + t * speed
                ex = int(CX + r * math.cos(angle))
                ey = int(CY + r * math.sin(angle))
                d.set_pixel(ex, ey, ELECTRON_COLOR)

        # --- Bottom label (3 phases, 5s each) ---
        phase = int(self.label_timer / 5) % 3
        if phase == 0:
            label = self.cur_name
        elif phase == 1:
            label = f"{self.cur_symbol} - {self.cur_z}"
        else:
            label = CATEGORY_NAMES.get(self.cur_cat, self.cur_cat.upper())

        # Reset scroll when phase changes
        if not hasattr(self, '_last_label_phase') or self._last_label_phase != phase:
            self._last_label_phase = phase
            self.scroll_offset = 0

        max_chars = 14
        if len(label) > max_chars:
            padded = label + "    " + label
            char_width = 4
            total_width = len(label + "    ") * char_width
            offset = int(self.scroll_offset) % total_width
            d.draw_text_small(2 - offset, 58, padded, Colors.WHITE)
        else:
            d.draw_text_small(2, 58, label, Colors.WHITE)

        # --- Group overlay at top ---
        if self.overlay_timer > 0:
            _, gname, gcolor = GROUPS[self.group_idx]
            alpha = min(1.0, self.overlay_timer / 0.5)
            oc = (int(gcolor[0] * alpha), int(gcolor[1] * alpha),
                  int(gcolor[2] * alpha))
            d.draw_text_small(2, 2, gname, oc)
