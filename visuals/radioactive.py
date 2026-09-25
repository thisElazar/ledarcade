"""
Radioactive - Decay Chains
===========================
One nucleus at a time, drawn as the protons and neutrons it actually
contains, walking down a real decay chain until it reaches a stable
isotope. Uranium-238 takes fourteen decays to become lead-206, and you
watch every one: an alpha decay throws off two protons and two neutrons
and the nucleus visibly shrinks, a beta decay turns one neutron into a
proton and spits out an electron.

Nuclear radius follows R = r0 * A^(1/3), so the nucleus is drawn at the
size its mass number earns. Short-lived isotopes visibly buzz — polonium-214
lasts 164 microseconds and cannot hold still; uranium-238 has sat for four
and a half billion years and barely moves.

Controls:
  Left/Right     - Step through the chain
  Up/Down        - Change decay chain
  Single button  - Force the next decay
  Both buttons   - Toggle the chain map
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE

# ── Decay data ──────────────────────────────────────────────────────
# (symbol, Z, A, half-life, mode, instability)
#   mode:        'A' alpha (A-4, Z-2), 'B' beta-minus (A, Z+1), None stable
#   instability: 0..1, drives how hard the nucleus shakes. Derived by eye
#                from the half-life so the display reads at a glance.

_CHAINS = [
    ("URANIUM-238", [
        ("U",  92, 238, "4.5E9 Y",  'A', 0.05),
        ("Th", 90, 234, "24.1 D",   'B', 0.55),
        ("Pa", 91, 234, "6.7 H",    'B', 0.65),
        ("U",  92, 234, "245 KY",   'A', 0.12),
        ("Th", 90, 230, "75.4 KY",  'A', 0.15),
        ("Ra", 88, 226, "1600 Y",   'A', 0.25),
        ("Rn", 86, 222, "3.8 D",    'A', 0.60),
        ("Po", 84, 218, "3.1 MIN",  'A', 0.80),
        ("Pb", 82, 214, "26.8 MIN", 'B', 0.72),
        ("Bi", 83, 214, "19.9 MIN", 'B', 0.74),
        ("Po", 84, 214, "164 US",   'A', 1.00),
        ("Pb", 82, 210, "22.2 Y",   'B', 0.35),
        ("Bi", 83, 210, "5.01 D",   'B', 0.58),
        ("Po", 84, 210, "138 D",    'A', 0.45),
        ("Pb", 82, 206, "STABLE",   None, 0.0),
    ]),
    ("THORIUM-232", [
        ("Th", 90, 232, "1.4E10 Y", 'A', 0.04),
        ("Ra", 88, 228, "5.75 Y",   'B', 0.40),
        ("Ac", 89, 228, "6.15 H",   'B', 0.66),
        ("Th", 90, 228, "1.9 Y",    'A', 0.45),
        ("Ra", 88, 224, "3.6 D",    'A', 0.60),
        ("Rn", 86, 220, "55.6 S",   'A', 0.85),
        ("Po", 84, 216, "145 MS",   'A', 0.95),
        ("Pb", 82, 212, "10.6 H",   'B', 0.62),
        ("Bi", 83, 212, "60.6 MIN", 'B', 0.70),
        ("Po", 84, 212, "299 NS",   'A', 1.00),
        ("Pb", 82, 208, "STABLE",   None, 0.0),
    ]),
    ("CARBON-14", [
        ("C",  6,  14, "5730 Y",    'B', 0.30),
        ("N",  7,  14, "STABLE",    None, 0.0),
    ]),
    ("COBALT-60", [
        ("Co", 27, 60, "5.27 Y",    'B', 0.38),
        ("Ni", 28, 60, "STABLE",    None, 0.0),
    ]),
    ("CESIUM-137", [
        ("Cs", 55, 137, "30.2 Y",   'B', 0.33),
        ("Ba", 56, 137, "STABLE",   None, 0.0),
    ]),
    ("IODINE-131", [
        ("I",  53, 131, "8.02 D",   'B', 0.57),
        ("Xe", 54, 131, "STABLE",   None, 0.0),
    ]),
    ("TRITIUM", [
        ("H",  1,   3, "12.3 Y",    'B', 0.36),
        ("He", 2,   3, "STABLE",    None, 0.0),
    ]),
]

# ── Layout ──────────────────────────────────────────────────────────
CX, CY = 32, 27        # nucleus centre, in pixels
CELL = 2               # a nucleon is a CELL x CELL block
MAX_CELLS = 10         # nucleon lattice radius, in cells

PROTON = (255, 95, 70)
PROTON_DIM = (150, 45, 30)
NEUTRON = (120, 150, 190)
NEUTRON_DIM = (60, 78, 105)
BG = (3, 3, 6)

ALPHA_COLOR = (255, 200, 60)
BETA_COLOR = (120, 230, 255)
GAMMA_COLOR = (200, 255, 200)

DWELL = 4.5            # seconds on each isotope
STABLE_DWELL = 7.0     # longer pause on the end of the chain
DECAY_ANIM = 1.1       # seconds of decay animation


def _lattice():
    """Nucleon slots in a disc, ordered centre-outward.

    Fixed and shared by every isotope, so a nucleus that loses four
    nucleons keeps the other 234 exactly where they were — the alpha
    particle leaves a nucleus, it doesn't rebuild one.
    """
    pts = []
    for dy in range(-MAX_CELLS, MAX_CELLS + 1):
        for dx in range(-MAX_CELLS, MAX_CELLS + 1):
            d2 = dx * dx + dy * dy
            if d2 <= MAX_CELLS * MAX_CELLS:
                pts.append((d2, dx, dy))
    pts.sort()
    return [(dx, dy) for _, dx, dy in pts]


_LATTICE = _lattice()


class Radioactive(Visual):
    name = "RADIOACTIVE"
    description = "Decay chains"
    category = "science_micro"
    GUIDE = {
        'desc': 'A single nucleus drawn as the protons and neutrons it contains, stepping down a real decay chain. Alpha decay throws off two protons and two neutrons; beta decay turns a neutron into a proton. Uranium-238 needs fourteen decays to reach stable lead-206.',
        'credit': 'Rutherford & Soddy, 1902',
        'legend': {
            '#P #N': 'Proton and neutron count in the nucleus.',
            'time value (4.5E9 Y)': "The isotope's half-life. Units: NS, US, MS, S, MIN, H, D, Y, KY (thousand years); E9 means times a billion (ten to the 9th).",
            'A/B/-': 'Decay mode in chain view: A=alpha, B=beta, -=stable.',
            'Element-#': 'Isotope notation: element symbol and mass number.',
        },
    }

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.chain_idx = 0
        self.step_idx = 0
        self.dwell_timer = 0.0
        self.decay_timer = 0.0      # >0 while the decay animation runs
        self.particles = []
        self.flash = 0.0
        self.show_map = False
        self._both_prev = False
        self.label_timer = 3.0
        self._load_isotope()

    # -- isotope state ------------------------------------------------

    @property
    def chain(self):
        return _CHAINS[self.chain_idx][1]

    @property
    def isotope(self):
        return self.chain[min(self.step_idx, len(self.chain) - 1)]

    def _load_isotope(self):
        """Lay out the nucleons for the current isotope."""
        sym, z, a, half, mode, inst = self.isotope
        self.n_protons = z
        self.n_nucleons = a
        self.instability = inst

        # Which lattice slots hold protons. Deterministic per isotope, so the
        # same nucleus always looks the same, but mixed rather than layered.
        rng = random.Random(z * 1000 + a)
        slots = list(range(min(a, len(_LATTICE))))
        rng.shuffle(slots)
        self.proton_slots = set(slots[:z])
        self.dwell_timer = 0.0
        self.decay_timer = 0.0

    def _advance(self, delta):
        self.step_idx = (self.step_idx + delta) % len(self.chain)
        self.particles = []
        self.flash = 0.0
        self._load_isotope()
        self.label_timer = 3.0

    def _set_chain(self, delta):
        self.chain_idx = (self.chain_idx + delta) % len(_CHAINS)
        self.step_idx = 0
        self.particles = []
        self.flash = 0.0
        self._load_isotope()
        self.label_timer = 3.0

    # -- decay --------------------------------------------------------

    def _nucleus_radius(self):
        """Nucleus radius in pixels. R = r0 * A^(1/3) is the real law, but the
        nucleons here are a flat disc of cells, so the drawn radius is what
        actually encloses them."""
        return math.sqrt(min(self.n_nucleons, len(_LATTICE)) / math.pi) * CELL

    def _begin_decay(self):
        sym, z, a, half, mode, inst = self.isotope
        if mode is None:
            return
        self.decay_timer = DECAY_ANIM
        self.flash = 0.18
        ang = random.uniform(0, math.tau)
        speed = 26.0
        # Emit from the surface, not the centre: a particle launched from the
        # middle spends its first third of a second buried in the nucleus.
        r = self._nucleus_radius() + 1
        ex, ey = CX + math.cos(ang) * r, CY + math.sin(ang) * r

        if mode == 'A':
            # Alpha: a bound two-proton, two-neutron cluster leaves together.
            for i, (ox, oy) in enumerate(((0, 0), (1, 0), (0, 1), (1, 1))):
                self.particles.append([
                    ex + ox, ey + oy,
                    math.cos(ang) * speed, math.sin(ang) * speed,
                    DECAY_ANIM, PROTON if i < 2 else NEUTRON,
                ])
        else:
            # Beta: an electron leaves fast; the nucleus keeps its mass.
            self.particles.append([
                ex, ey,
                math.cos(ang) * speed * 2.2, math.sin(ang) * speed * 2.2,
                DECAY_ANIM * 0.7, BETA_COLOR,
            ])
            # Antineutrino, drawn faint and going the other way.
            self.particles.append([
                CX - math.cos(ang) * r, CY - math.sin(ang) * r,
                -math.cos(ang) * speed * 2.6, -math.sin(ang) * speed * 2.6,
                DECAY_ANIM * 0.5, (70, 90, 110),
            ])

    def _finish_decay(self):
        """Land on the daughter isotope."""
        if self.step_idx < len(self.chain) - 1:
            self.step_idx += 1
        self._load_isotope()
        self.label_timer = 3.0

    # -- input --------------------------------------------------------

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.left_pressed:
            self._advance(-1)
            consumed = True
        if input_state.right_pressed:
            self._advance(1)
            consumed = True
        if input_state.up_pressed:
            self._set_chain(-1)
            consumed = True
        if input_state.down_pressed:
            self._set_chain(1)
            consumed = True

        both = input_state.action_l_held and input_state.action_r_held
        if self._both_prev and not both:
            self.show_map = not self.show_map
            consumed = True
        elif not both and (input_state.action_l or input_state.action_r):
            if self.decay_timer <= 0:
                self._begin_decay()
            consumed = True
        self._both_prev = both

        return consumed

    # -- update -------------------------------------------------------

    def update(self, dt: float):
        self.time += dt
        if self.label_timer > 0:
            self.label_timer = max(0.0, self.label_timer - dt)
        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)

        for p in self.particles:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[4] -= dt
        self.particles = [p for p in self.particles if p[4] > 0]

        if self.decay_timer > 0:
            self.decay_timer -= dt
            if self.decay_timer <= 0:
                self._finish_decay()
            return

        _, _, _, _, mode, _ = self.isotope
        self.dwell_timer += dt
        if mode is None:
            if self.dwell_timer >= STABLE_DWELL:
                self.step_idx = 0
                self._load_isotope()
                self.label_timer = 3.0
        elif self.dwell_timer >= DWELL:
            self._begin_decay()

    # -- draw ---------------------------------------------------------

    def draw(self):
        d = self.display
        d.clear(BG)

        self._draw_nucleus()

        for px, py, _, _, life, col in self.particles:
            ix, iy = int(px), int(py)
            if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                fade = min(1.0, life / 0.4)
                d.set_pixel(ix, iy, (int(col[0] * fade), int(col[1] * fade),
                                     int(col[2] * fade)))

        if self.show_map:
            self._draw_map()
        else:
            self._draw_readout()

    def _draw_nucleus(self):
        d = self.display
        sym, z, a, half, mode, inst = self.isotope

        # Shake amplitude tracks instability: a microsecond isotope cannot sit
        # still, a billion-year one barely moves.
        amp = 0.35 + inst * 1.5
        t = self.time
        jx = math.sin(t * (3.0 + inst * 16.0)) * amp
        jy = math.cos(t * (3.7 + inst * 14.0)) * amp
        ox = int(round(jx))
        oy = int(round(jy))

        flash = self.flash > 0
        decaying = self.decay_timer > 0

        count = min(a, len(_LATTICE))
        for i in range(count):
            dx, dy = _LATTICE[i]
            is_proton = i in self.proton_slots
            if flash:
                # Blend toward white rather than replacing: a full whiteout
                # loses the proton/neutron split at the one moment it matters.
                base = PROTON if is_proton else NEUTRON
                k = min(1.0, self.flash / 0.18) * 0.65
                col = (int(base[0] + (255 - base[0]) * k),
                       int(base[1] + (250 - base[1]) * k),
                       int(base[2] + (220 - base[2]) * k))
            elif decaying:
                col = PROTON_DIM if is_proton else NEUTRON_DIM
            else:
                col = PROTON if is_proton else NEUTRON
            px = CX + dx * CELL + ox
            py = CY + dy * CELL + oy
            for sy in range(CELL):
                for sx in range(CELL):
                    x, y = px + sx, py + sy
                    if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                        d.set_pixel(x, y, col)

    def _draw_readout(self):
        d = self.display
        sym, z, a, half, mode, inst = self.isotope
        chain_name = _CHAINS[self.chain_idx][0]

        # Isotope, top-left: the one label that always stays up.
        label = f"{sym}-{a}"
        d.draw_text_small(1, 1, label, (255, 255, 235))

        # Proton / neutron split, top-right.
        counts = f"{z}P {a - z}N"
        d.draw_text_small(GRID_SIZE - len(counts) * 4, 1, counts, (140, 150, 175))

        # Half-life and what happens next, along the bottom.
        d.draw_text_small(1, 52, half[:15], (150, 150, 130))
        if mode == 'A':
            d.draw_text_small(1, 58, "ALPHA", ALPHA_COLOR)
        elif mode == 'B':
            d.draw_text_small(1, 58, "BETA", BETA_COLOR)
        else:
            d.draw_text_small(1, 58, "STABLE", (110, 230, 130))

        # Chain progress: one tick per isotope, current one lit.
        n = len(self.chain)
        x0 = GRID_SIZE - n * 2 - 1
        for i in range(n):
            lit = i == self.step_idx
            done = i < self.step_idx
            if lit:
                col = (255, 230, 120)
            elif done:
                col = (90, 80, 50)
            else:
                col = (45, 45, 55)
            d.set_pixel(x0 + i * 2, 60, col)
            d.set_pixel(x0 + i * 2, 61, col)

        if self.label_timer > 0:
            a_ = min(1.0, self.label_timer / 0.5)
            c = int(190 * a_)
            d.draw_text_small(1, 7, chain_name[:15], (c, c, int(c * 1.1)))

    def _draw_map(self):
        """Full chain listing, so you can see where this nucleus is headed."""
        d = self.display
        d.clear((0, 0, 0))
        chain_name = _CHAINS[self.chain_idx][0]
        d.draw_text_small(1, 1, chain_name[:15], (255, 255, 200))

        # Only so many rows fit; window around the current step.
        rows = 8
        start = max(0, min(self.step_idx - rows // 2, len(self.chain) - rows))
        for r in range(min(rows, len(self.chain) - start)):
            i = start + r
            sym, z, a, half, mode, _ = self.chain[i]
            y = 9 + r * 6
            cur = i == self.step_idx
            col = (255, 235, 140) if cur else (120, 125, 145)
            # Columns: 6-char isotope (24px), 1-char mode, then 8 chars of
            # half-life — enough for "26.8 MIN" and "1.4E10 Y" uncut.
            d.draw_text_small(1, y, f"{sym}-{a}"[:6], col)
            tag = "A" if mode == 'A' else ("B" if mode == 'B' else "-")
            tcol = ALPHA_COLOR if mode == 'A' else (
                BETA_COLOR if mode == 'B' else (110, 230, 130))
            d.draw_text_small(26, y, tag, tcol if cur else
                              (tcol[0] // 3, tcol[1] // 3, tcol[2] // 3))
            d.draw_text_small(32, y, half[:8], col)
