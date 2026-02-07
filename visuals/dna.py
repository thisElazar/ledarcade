"""
DNA - Molecular Biology Visualization
======================================
Interactive exploration of DNA structure and the central dogma of
molecular biology on a 64x64 LED matrix.

Scenarios: DOUBLE HELIX, REPLICATION, TRANSCRIPTION, CODONS, MUTATION, CHROMATIN

Controls:
  Left/Right     - Adjust animation speed
  Up/Down        - Cycle color palette
  Single button  - Cycle scenario
  Both buttons   - Toggle scrolling notes
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE

# ── Base chemistry ─────────────────────────────────────────────

BASE_COLORS = {
    'A': (255, 50, 50),    # Adenine  - red
    'T': (50, 100, 255),   # Thymine  - blue
    'G': (50, 220, 50),    # Guanine  - green
    'C': (255, 230, 50),   # Cytosine - yellow
}

RNA_BASE_COLORS = {
    'A': (255, 80, 80),
    'U': (255, 140, 50),   # Uracil - orange (distinct from Thymine blue)
    'G': (80, 220, 80),
    'C': (255, 230, 80),
}

COMPLEMENT = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G'}
DNA_TO_RNA = {'T': 'A', 'A': 'U', 'C': 'G', 'G': 'C'}

# ── Codon table (mRNA codon -> single-letter amino acid) ──────

CODON_TABLE = {
    'UUU': 'F', 'UUC': 'F', 'UUA': 'L', 'UUG': 'L',
    'CUU': 'L', 'CUC': 'L', 'CUA': 'L', 'CUG': 'L',
    'AUU': 'I', 'AUC': 'I', 'AUA': 'I', 'AUG': 'M',
    'GUU': 'V', 'GUC': 'V', 'GUA': 'V', 'GUG': 'V',
    'UCU': 'S', 'UCC': 'S', 'UCA': 'S', 'UCG': 'S',
    'CCU': 'P', 'CCC': 'P', 'CCA': 'P', 'CCG': 'P',
    'ACU': 'T', 'ACC': 'T', 'ACA': 'T', 'ACG': 'T',
    'GCU': 'A', 'GCC': 'A', 'GCA': 'A', 'GCG': 'A',
    'UAU': 'Y', 'UAC': 'Y', 'UAA': '*', 'UAG': '*',
    'CAU': 'H', 'CAC': 'H', 'CAA': 'Q', 'CAG': 'Q',
    'AAU': 'N', 'AAC': 'N', 'AAA': 'K', 'AAG': 'K',
    'GAU': 'D', 'GAC': 'D', 'GAA': 'E', 'GAG': 'E',
    'UGU': 'C', 'UGC': 'C', 'UGA': '*', 'UGG': 'W',
    'CGU': 'R', 'CGC': 'R', 'CGA': 'R', 'CGG': 'R',
    'AGU': 'S', 'AGC': 'S', 'AGA': 'R', 'AGG': 'R',
    'GGU': 'G', 'GGC': 'G', 'GGA': 'G', 'GGG': 'G',
}

AMINO_NAMES = {
    'F': 'PHE', 'L': 'LEU', 'I': 'ILE', 'M': 'MET', 'V': 'VAL',
    'S': 'SER', 'P': 'PRO', 'T': 'THR', 'A': 'ALA', 'Y': 'TYR',
    'H': 'HIS', 'Q': 'GLN', 'N': 'ASN', 'K': 'LYS', 'D': 'ASP',
    'E': 'GLU', 'C': 'CYS', 'W': 'TRP', 'R': 'ARG', 'G': 'GLY',
    '*': 'STOP',
}

AMINO_COLORS = {
    # Hydrophobic (warm orange)
    'F': (255, 160, 60), 'L': (255, 140, 40), 'I': (255, 130, 30),
    'V': (255, 150, 50), 'A': (240, 140, 50), 'W': (255, 170, 80),
    'M': (255, 180, 80),
    # Polar (green)
    'S': (80, 220, 80), 'T': (80, 200, 80), 'Y': (80, 200, 120),
    'Q': (80, 220, 120), 'N': (80, 200, 100),
    # Positive charge (blue)
    'K': (80, 100, 255), 'R': (80, 120, 255), 'H': (100, 120, 255),
    # Negative charge (red)
    'D': (255, 80, 80), 'E': (255, 60, 60),
    # Special (yellow)
    'P': (220, 220, 60), 'G': (200, 200, 80), 'C': (220, 220, 80),
    # Stop
    '*': (255, 0, 0),
}

# ── Scenarios ──────────────────────────────────────────────────

_SCENARIOS = ['DOUBLE HELIX', 'REPLICATION', 'TRANSCRIPTION',
              'CODONS', 'MUTATION', 'CHROMATIN']

# ── Helix geometry ─────────────────────────────────────────────

HELIX_RADIUS = 12.0
HELIX_PITCH = 3.4
HELIX_TWIST = 2 * math.pi / 10
NUM_BASES = 20

# ── Palettes ───────────────────────────────────────────────────

PALETTES = [
    {'name': 'CLASSIC', 'bg': (0, 0, 0),
     'backbone': (200, 200, 220), 'dim': (100, 100, 120),
     'note': (200, 200, 255), 'highlight': (255, 255, 100),
     'tint': None},
    {'name': 'NEON', 'bg': (5, 0, 15),
     'backbone': (180, 100, 255), 'dim': (100, 50, 160),
     'note': (220, 150, 255), 'highlight': (255, 100, 255),
     'tint': (1.0, 0.7, 1.2)},
    {'name': 'BLUEPRINT', 'bg': (5, 5, 25),
     'backbone': (100, 150, 255), 'dim': (50, 80, 160),
     'note': (150, 200, 255), 'highlight': (100, 200, 255),
     'tint': (0.6, 0.8, 1.3)},
    {'name': 'WARM', 'bg': (15, 8, 5),
     'backbone': (220, 180, 140), 'dim': (140, 110, 80),
     'note': (255, 220, 180), 'highlight': (255, 220, 100),
     'tint': (1.2, 0.9, 0.6)},
    {'name': 'MONO', 'bg': (0, 0, 0),
     'backbone': (180, 180, 180), 'dim': (100, 100, 100),
     'note': (200, 200, 200), 'highlight': (255, 255, 255),
     'tint': 'mono'},
]


# ── DNA Visual ─────────────────────────────────────────────────

class DNA(Visual):
    name = "DNA"
    description = "Molecular biology explorer"
    category = "science"

    def __init__(self, display: Display):
        super().__init__(display)

    # ── notes ──────────────────────────────────────────────────

    def _get_notes(self):
        mid = PALETTES[self.palette_idx]['note']
        return [
            ("DEOXYRIBONUCLEIC ACID", (255, 255, 255)),
            ("A=T  G=C  BASE PAIRING", mid),
            ("3 BILLION BASE PAIRS PER CELL", mid),
            ("DNA TO RNA TO PROTEIN", mid),
            ("WATSON AND CRICK 1953", (255, 255, 255)),
            ("ROSALIND FRANKLIN X-RAY DIFFRACTION", mid),
        ]

    def _build_notes_segments(self):
        sep = '  --  '
        sep_color = (60, 55, 50)
        segments = []
        px_off = 0
        for i, (text, color) in enumerate(self._get_notes()):
            if i > 0:
                segments.append((px_off, sep, sep_color))
                px_off += len(sep) * 4
            segments.append((px_off, text, color))
            px_off += len(text) * 4
        segments.append((px_off, sep, sep_color))
        px_off += len(sep) * 4
        self.notes_segments = segments
        self.notes_scroll_len = px_off

    def _draw_notes(self):
        d = self.display
        scroll_x = int(self.notes_scroll_offset) % self.notes_scroll_len
        for copy in (0, self.notes_scroll_len):
            for seg_off, text, color in self.notes_segments:
                px = 2 + seg_off + copy - scroll_x
                text_w = len(text) * 4
                if px + text_w < 0 or px > 64:
                    continue
                d.draw_text_small(px, 58, text, color)

    # ── overlay ────────────────────────────────────────────────

    def _draw_overlay(self):
        if self.overlay_timer <= 0:
            return
        alpha = min(1.0, self.overlay_timer / 0.5)
        c = (int(255 * alpha), int(255 * alpha), int(255 * alpha))
        self.display.draw_text_small(2, 2, self.overlay_text, c)

    def _show_overlay(self, text):
        self.overlay_text = text
        self.overlay_timer = 2.0

    # ── helpers ────────────────────────────────────────────────

    def _tint(self, color, pal):
        tint = pal.get('tint')
        if tint is None:
            return color
        if tint == 'mono':
            gray = int(0.3 * color[0] + 0.59 * color[1] + 0.11 * color[2])
            return (gray, gray, gray)
        return (
            min(255, int(color[0] * tint[0])),
            min(255, int(color[1] * tint[1])),
            min(255, int(color[2] * tint[2])),
        )

    def _transform_point(self, x, y, z):
        """Rotate around Y axis with gentle X tilt, project to screen."""
        tilt = 0.3 * math.sin(self.time * 0.3)
        cos_t, sin_t = math.cos(tilt), math.sin(tilt)
        y2 = y * cos_t - z * sin_t
        z2 = y * sin_t + z * cos_t
        cos_r, sin_r = math.cos(self.rotation_y), math.sin(self.rotation_y)
        x2 = x * cos_r + z2 * sin_r
        z3 = -x * sin_r + z2 * cos_r
        return GRID_SIZE // 2 + x2, 28 - y2, z3

    def _depth_shade(self, color, z, z_range=30.0):
        factor = 0.4 + 0.6 * ((z + z_range) / (2 * z_range))
        factor = max(0.2, min(1.0, factor))
        return (int(color[0] * factor), int(color[1] * factor),
                int(color[2] * factor))

    def _set2x2(self, x, y, color):
        """Draw a 2x2 pixel block (used for bases)."""
        d = self.display
        for dx in range(2):
            for dy in range(2):
                px, py = x + dx, y + dy
                if 0 <= px < 64 and 0 <= py < 64:
                    d.set_pixel(px, py, color)

    # ── reset / setup ─────────────────────────────────────────

    def reset(self):
        self.time = 0.0
        self.speed = 1.0
        self.scenario_idx = 0
        self.palette_idx = 0
        self.rotation_y = 0.0

        # DNA template strand (36 bases = 12 codons)
        # TAC -> AUG (start), random middle, ATT -> UAA (stop)
        self.sequence = (list('TAC')
                         + [random.choice('ATGC') for _ in range(30)]
                         + list('ATT'))
        self.mrna = ''.join(DNA_TO_RNA[b] for b in self.sequence)

        # Mutation state
        self.mutations = {}
        self.mutation_timer = 0.0

        # Overlay / notes
        self.overlay_text = ''
        self.overlay_timer = 0.0
        self.show_notes = False
        self.notes_scroll_offset = 0.0
        self.notes_segments = []
        self.notes_scroll_len = 1
        self._both_pressed_prev = False
        self._build_notes_segments()

        self._setup_scenario()

    def _setup_scenario(self):
        self.rotation_y = 0.0
        self.mutations = {}
        self.mutation_timer = 0.0

    # ── input ─────────────────────────────────────────────────

    def handle_input(self, input_state):
        consumed = False

        # Left/Right: adjust speed
        if input_state.left_pressed or input_state.left:
            self.speed = max(0.1, self.speed - 0.05)
            consumed = True
        if input_state.right_pressed or input_state.right:
            self.speed = min(3.0, self.speed + 0.05)
            consumed = True

        # Up/Down: cycle palette
        if input_state.up_pressed:
            self.palette_idx = (self.palette_idx + 1) % len(PALETTES)
            if self.show_notes:
                self._build_notes_segments()
            consumed = True
        if input_state.down_pressed:
            self.palette_idx = (self.palette_idx - 1) % len(PALETTES)
            if self.show_notes:
                self._build_notes_segments()
            consumed = True

        # Both buttons: toggle notes
        both = input_state.action_l and input_state.action_r
        if both and not self._both_pressed_prev:
            self.show_notes = not self.show_notes
            self.notes_scroll_offset = 0.0
            if self.show_notes:
                self._build_notes_segments()
            consumed = True
        elif input_state.action_l or input_state.action_r:
            if not both:
                self.scenario_idx = (self.scenario_idx + 1) % len(_SCENARIOS)
                self._setup_scenario()
                self._show_overlay(_SCENARIOS[self.scenario_idx])
                consumed = True
        self._both_pressed_prev = both

        return consumed

    # ── update ────────────────────────────────────────────────

    def update(self, dt):
        self.time += dt
        scenario = _SCENARIOS[self.scenario_idx]

        if scenario in ('DOUBLE HELIX', 'MUTATION'):
            self.rotation_y += 0.5 * self.speed * dt

        if scenario == 'MUTATION':
            self._update_mutations(dt)

        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)
        if self.show_notes:
            self.notes_scroll_offset += dt * 18

    def _update_mutations(self, dt):
        self.mutation_timer += dt * self.speed
        if self.mutation_timer > 3.0:
            self.mutation_timer = 0.0
            idx = random.randint(0, len(self.sequence) - 1)
            original = self.sequence[idx]
            mutated = random.choice([b for b in 'ATGC' if b != original])
            self.mutations[idx] = {
                'original': original,
                'mutated': mutated,
                'timer': 0.0,
                'repaired': random.random() < 0.5,
            }
            self.sequence[idx] = mutated

        to_remove = []
        for idx, m in self.mutations.items():
            m['timer'] += dt * self.speed
            if m['repaired'] and m['timer'] > 2.0:
                self.sequence[idx] = m['original']
                to_remove.append(idx)
            elif m['timer'] > 5.0:
                to_remove.append(idx)
        for idx in to_remove:
            del self.mutations[idx]

    # ── draw ──────────────────────────────────────────────────

    def draw(self):
        pal = PALETTES[self.palette_idx]
        self.display.clear(pal['bg'])

        scenario = _SCENARIOS[self.scenario_idx]
        if scenario == 'DOUBLE HELIX':
            self._draw_helix(pal)
        elif scenario == 'REPLICATION':
            self._draw_replication(pal)
        elif scenario == 'TRANSCRIPTION':
            self._draw_transcription(pal)
        elif scenario == 'CODONS':
            self._draw_codons(pal)
        elif scenario == 'MUTATION':
            self._draw_mutation(pal)
        elif scenario == 'CHROMATIN':
            self._draw_chromatin(pal)

        if self.show_notes:
            self._draw_notes()
        self._draw_overlay()

    # ── DOUBLE HELIX ──────────────────────────────────────────

    def _draw_helix(self, pal):
        d = self.display
        draw_list = []
        center_y = (NUM_BASES * HELIX_PITCH) / 2

        for i in range(NUM_BASES):
            base = self.sequence[i % len(self.sequence)]
            comp = COMPLEMENT[base]
            y_pos = (i * HELIX_PITCH - center_y) * 0.8
            angle = i * HELIX_TWIST

            x1 = HELIX_RADIUS * math.cos(angle)
            z1 = HELIX_RADIUS * math.sin(angle)
            x2 = HELIX_RADIUS * math.cos(angle + math.pi)
            z2 = HELIX_RADIUS * math.sin(angle + math.pi)

            sx1, sy1, sz1 = self._transform_point(x1, y_pos, z1)
            sx2, sy2, sz2 = self._transform_point(x2, y_pos, z2)

            bc1 = self._tint(BASE_COLORS[base], pal)
            bc2 = self._tint(BASE_COLORS[comp], pal)
            draw_list.append(('base', sz1, sx1, sy1, bc1))
            draw_list.append(('base', sz2, sx2, sy2, bc2))
            draw_list.append(('rung', (sz1 + sz2) / 2, sx1, sy1, sx2, sy2,
                              pal['dim']))

            if i < NUM_BASES - 1:
                na = (i + 1) * HELIX_TWIST
                ny = ((i + 1) * HELIX_PITCH - center_y) * 0.8
                for xr, zr, sz in [(x1, z1, sz1), (x2, z2, sz2)]:
                    nxr = HELIX_RADIUS * math.cos(na + (math.pi if xr == x2 else 0))
                    nzr = HELIX_RADIUS * math.sin(na + (math.pi if xr == x2 else 0))
                    snx, sny, snz = self._transform_point(nxr, ny, nzr)
                    sx_c = sx1 if xr == x1 else sx2
                    sy_c = sy1 if xr == x1 else sy2
                    draw_list.append(('bb', (sz + snz) / 2, sx_c, sy_c,
                                      snx, sny, sz))

        self._render_helix_list(draw_list, pal)

    def _render_helix_list(self, draw_list, pal):
        """Painter's algorithm render for 3D helix draw lists."""
        d = self.display
        draw_list.sort(key=lambda it: it[1])
        for item in draw_list:
            kind = item[0]
            if kind == 'bb':
                _, _, x1, y1, x2, y2, z = item
                c = self._depth_shade(pal['backbone'], z)
                d.draw_line(int(x1), int(y1), int(x2), int(y2), c)
            elif kind == 'rung':
                _, _, x1, y1, x2, y2, rc = item
                z = item[1]
                c = self._depth_shade(rc, z)
                d.draw_line(int(x1), int(y1), int(x2), int(y2), c)
            elif kind == 'base':
                _, z, sx, sy, bc = item
                c = self._depth_shade(bc, z)
                ix, iy = int(round(sx)), int(round(sy))
                self._set2x2(ix, iy, c)

    # ── REPLICATION ───────────────────────────────────────────

    def _draw_replication(self, pal):
        """Replication fork: DNA unzips and two daughter strands form."""
        d = self.display
        num_bases = 30
        col_w = 2
        start_x = 2

        # Fork position cycles left to right
        fork_frac = (self.time * self.speed * 0.04) % 1.0
        fork_col = int(fork_frac * num_bases)

        # Y positions: unreplicated (paired) DNA centered at y=32
        pair_y1 = 29   # top strand
        pair_y2 = 34   # bottom strand
        # Replicated daughters (spread apart)
        d1_y = 14      # daughter 1 template (top strand moved up)
        d1_new_y = 19  # daughter 1 new complement
        d2_new_y = 44  # daughter 2 new complement
        d2_y = 49      # daughter 2 template (bottom strand moved down)

        for i in range(num_bases):
            x = start_x + i * col_w
            base = self.sequence[i % len(self.sequence)]
            comp = COMPLEMENT[base]
            bc1 = self._tint(BASE_COLORS[base], pal)
            bc2 = self._tint(BASE_COLORS[comp], pal)

            if i >= fork_col:
                # Unreplicated: paired double strand
                d.set_pixel(x, pair_y1, bc1)
                d.set_pixel(x + 1, pair_y1, bc1)
                d.set_pixel(x, pair_y2, bc2)
                d.set_pixel(x + 1, pair_y2, bc2)
                for by in range(pair_y1 + 1, pair_y2):
                    d.set_pixel(x, by, pal['dim'])
            else:
                # Replicated: strands diverge from fork
                cols_from_fork = fork_col - i
                t = min(1.0, cols_from_fork / 4.0)

                # Daughter 1 (top): template moves up
                y1 = int(pair_y1 + (d1_y - pair_y1) * t)
                d.set_pixel(x, y1, bc1)
                d.set_pixel(x + 1, y1, bc1)
                if t >= 1.0:
                    # New complementary strand appears below template
                    d.set_pixel(x, d1_new_y, bc2)
                    d.set_pixel(x + 1, d1_new_y, bc2)
                    for by in range(y1 + 1, d1_new_y):
                        d.set_pixel(x, by, pal['dim'])

                # Daughter 2 (bottom): template moves down
                y2 = int(pair_y2 + (d2_y - pair_y2) * t)
                d.set_pixel(x, y2, bc2)
                d.set_pixel(x + 1, y2, bc2)
                if t >= 1.0:
                    d.set_pixel(x, d2_new_y, bc1)
                    d.set_pixel(x + 1, d2_new_y, bc1)
                    for by in range(d2_new_y + 1, y2):
                        d.set_pixel(x, by, pal['dim'])

        # Helicase marker at fork
        fx = start_x + fork_col * col_w
        if 0 <= fx < 64:
            hc = pal['highlight']
            for fy in range(pair_y1 - 1, pair_y2 + 2):
                if 0 <= fy < 64:
                    d.set_pixel(fx, fy, hc)

        # Labels
        d.draw_text_small(2, 7, '5\'', pal['dim'])
        d.draw_text_small(2, 53, '3\'', pal['dim'])

    # ── TRANSCRIPTION ─────────────────────────────────────────

    def _draw_transcription(self, pal):
        """RNA polymerase reads template strand, builds mRNA."""
        d = self.display
        num_bases = 30
        col_w = 2
        start_x = 2

        # Polymerase position cycles across (with brief pause at end)
        poly_frac = (self.time * self.speed * 0.03) % 1.2
        poly_col = min(int(poly_frac * num_bases), num_bases)

        # DNA strand Y positions
        coding_y = 14     # coding (non-template) strand
        template_y = 22   # template strand
        # Transcription bubble half-width
        bubble_half = 3
        # mRNA Y position
        mrna_y = 34

        for i in range(num_bases):
            x = start_x + i * col_w
            base = self.sequence[i % len(self.sequence)]
            comp = COMPLEMENT[base]
            bc_coding = self._tint(BASE_COLORS[comp], pal)
            bc_template = self._tint(BASE_COLORS[base], pal)

            in_bubble = (0 <= poly_col - i <= bubble_half * 2
                         and i <= poly_col)

            if in_bubble:
                # Strands separate vertically
                d.set_pixel(x, coding_y - 4, bc_coding)
                d.set_pixel(x + 1, coding_y - 4, bc_coding)
                d.set_pixel(x, template_y + 4, bc_template)
                d.set_pixel(x + 1, template_y + 4, bc_template)
            else:
                # Paired DNA
                d.set_pixel(x, coding_y, bc_coding)
                d.set_pixel(x + 1, coding_y, bc_coding)
                d.set_pixel(x, template_y, bc_template)
                d.set_pixel(x + 1, template_y, bc_template)
                for by in range(coding_y + 1, template_y):
                    d.set_pixel(x, by, pal['dim'])

        # mRNA strand: transcribed bases (up to polymerase position)
        mrna_len = min(poly_col, num_bases)
        for i in range(mrna_len):
            x = start_x + i * col_w
            rna_base = DNA_TO_RNA[self.sequence[i % len(self.sequence)]]
            rc = self._tint(RNA_BASE_COLORS[rna_base], pal)
            d.set_pixel(x, mrna_y, rc)
            d.set_pixel(x + 1, mrna_y, rc)

        # Polymerase marker (connects template to mRNA)
        px = start_x + poly_col * col_w
        if 0 <= px < 64:
            hc = pal['highlight']
            for py in range(template_y + 2, mrna_y + 1):
                if 0 <= py < 64:
                    d.set_pixel(px, py, hc)

        # Labels
        d.draw_text_small(2, 7, 'DNA', pal['dim'])
        d.draw_text_small(2, mrna_y + 3, 'MRNA',
                          self._tint((255, 140, 50), pal))

    # ── CODONS ────────────────────────────────────────────────

    def _draw_codons(self, pal):
        """Ribosome reads mRNA in triplets, builds a protein chain."""
        d = self.display
        mrna = self.mrna
        num_codons = len(mrna) // 3

        # Current codon (ribosome position)
        codon_period = 2.0 / max(0.1, self.speed)
        current_codon = int(self.time / codon_period) % num_codons

        # Draw mRNA at top
        mrna_y = 8
        bases_shown = min(len(mrna), 30)
        for i in range(bases_shown):
            x = 2 + i * 2
            base = mrna[i]
            rc = self._tint(RNA_BASE_COLORS[base], pal)
            d.set_pixel(x, mrna_y, rc)
            d.set_pixel(x + 1, mrna_y, rc)

        # Highlight current codon with bracket
        cs = current_codon * 3
        if cs + 2 < bases_shown:
            hx = 2 + cs * 2
            hc = pal['highlight']
            # Top and bottom lines
            for dx in range(6):
                px = hx + dx
                if 0 <= px < 64:
                    d.set_pixel(px, mrna_y - 1, hc)
                    d.set_pixel(px, mrna_y + 1, hc)

        # Codon info in the middle
        if cs + 3 <= len(mrna):
            codon_str = mrna[cs:cs + 3]
            amino = CODON_TABLE.get(codon_str, '?')
            amino_name = AMINO_NAMES.get(amino, '???')
            amino_color = AMINO_COLORS.get(amino, (200, 200, 200))

            d.draw_text_small(2, 18, codon_str,
                              self._tint((255, 200, 100), pal))
            d.draw_text_small(20, 18, amino_name,
                              self._tint(amino_color, pal))

            # Amino acid property
            if amino == '*':
                atype = 'STOP CODON'
            elif amino == 'M' and current_codon == 0:
                atype = 'START'
            elif amino in 'FLIVAWM':
                atype = 'HYDROPHOBIC'
            elif amino in 'STYNQ':
                atype = 'POLAR'
            elif amino in 'KRH':
                atype = 'POSITIVE'
            elif amino in 'DE':
                atype = 'NEGATIVE'
            else:
                atype = 'SPECIAL'
            d.draw_text_small(2, 26, atype, pal['dim'])

        # Growing polypeptide chain
        chain_y = 40
        d.draw_text_small(2, chain_y - 5, 'PROTEIN', pal['dim'])
        for ci in range(min(current_codon + 1, num_codons)):
            c_start = ci * 3
            if c_start + 3 > len(mrna):
                break
            codon_str = mrna[c_start:c_start + 3]
            amino = CODON_TABLE.get(codon_str, '?')
            if amino == '*':
                # Stop codon: red X
                ax = 2 + ci * 4
                if ax + 2 < 64:
                    d.set_pixel(ax, chain_y, (255, 0, 0))
                    d.set_pixel(ax + 2, chain_y, (255, 0, 0))
                    d.set_pixel(ax + 1, chain_y + 1, (255, 0, 0))
                    d.set_pixel(ax, chain_y + 2, (255, 0, 0))
                    d.set_pixel(ax + 2, chain_y + 2, (255, 0, 0))
                break
            ac = self._tint(AMINO_COLORS.get(amino, (200, 200, 200)), pal)
            ax = 2 + ci * 4
            if ax + 2 < 64:
                for dx in range(3):
                    for dy in range(3):
                        d.set_pixel(ax + dx, chain_y + dy, ac)

    # ── MUTATION ──────────────────────────────────────────────

    def _draw_mutation(self, pal):
        """3D helix with flashing mutations and mismatched bases."""
        d = self.display
        draw_list = []
        center_y = (NUM_BASES * HELIX_PITCH) / 2

        for i in range(NUM_BASES):
            seq_i = i % len(self.sequence)
            base = self.sequence[seq_i]
            comp = COMPLEMENT[base]
            y_pos = (i * HELIX_PITCH - center_y) * 0.8
            angle = i * HELIX_TWIST

            x1 = HELIX_RADIUS * math.cos(angle)
            z1 = HELIX_RADIUS * math.sin(angle)
            x2 = HELIX_RADIUS * math.cos(angle + math.pi)
            z2 = HELIX_RADIUS * math.sin(angle + math.pi)

            sx1, sy1, sz1 = self._transform_point(x1, y_pos, z1)
            sx2, sy2, sz2 = self._transform_point(x2, y_pos, z2)

            # Check for active mutation
            is_mutated = seq_i in self.mutations
            flash = False
            if is_mutated:
                flash = int(self.mutations[seq_i]['timer'] * 6) % 2 == 0

            bc1 = self._tint(BASE_COLORS[base], pal)
            if is_mutated and flash:
                bc1 = (255, 255, 255)

            # Complement: if mutated, show OLD complement (mismatch)
            if is_mutated:
                orig_comp = COMPLEMENT[self.mutations[seq_i]['original']]
                bc2 = self._tint(BASE_COLORS[orig_comp], pal)
                if flash:
                    bc2 = (255, 0, 0)
            else:
                bc2 = self._tint(BASE_COLORS[comp], pal)

            draw_list.append(('base', sz1, sx1, sy1, bc1))
            draw_list.append(('base', sz2, sx2, sy2, bc2))

            # Rung color: red if mutated
            rc = pal['dim']
            if is_mutated:
                rc = (200, 50, 50) if not flash else (255, 100, 100)
            draw_list.append(('rung', (sz1 + sz2) / 2, sx1, sy1, sx2, sy2,
                              rc))

            if i < NUM_BASES - 1:
                na = (i + 1) * HELIX_TWIST
                ny = ((i + 1) * HELIX_PITCH - center_y) * 0.8
                for xr, zr, sz in [(x1, z1, sz1), (x2, z2, sz2)]:
                    offset = math.pi if xr == x2 else 0
                    nxr = HELIX_RADIUS * math.cos(na + offset)
                    nzr = HELIX_RADIUS * math.sin(na + offset)
                    snx, sny, snz = self._transform_point(nxr, ny, nzr)
                    sx_c = sx1 if xr == x1 else sx2
                    sy_c = sy1 if xr == x1 else sy2
                    draw_list.append(('bb', (sz + snz) / 2, sx_c, sy_c,
                                      snx, sny, sz))

        self._render_helix_list(draw_list, pal)

        # Mutation count label
        n_mut = len(self.mutations)
        if n_mut > 0:
            label = f'{n_mut} MUTATION' + ('S' if n_mut > 1 else '')
            d.draw_text_small(2, 2, label, (255, 100, 100))

    # ── CHROMATIN ─────────────────────────────────────────────

    def _draw_chromatin(self, pal):
        """Animated zoom through DNA packaging levels."""
        d = self.display
        phase_dur = 5.0 / max(0.1, self.speed)
        total = phase_dur * 4
        t = self.time % total
        phase = int(t / phase_dur)

        labels = ['2 NM: DNA', '11 NM: NUCLEOSOME',
                  '30 NM: FIBER', 'CHROMOSOME']

        if phase == 0:
            self._draw_bare_dna(pal)
        elif phase == 1:
            self._draw_nucleosomes(pal)
        elif phase == 2:
            self._draw_fiber(pal)
        else:
            self._draw_chromosome(pal)

        d.draw_text_small(2, 2, labels[phase], pal['note'])

    def _draw_bare_dna(self, pal):
        """Bare DNA double helix seen from the side (two wavy lines)."""
        d = self.display
        bc1 = self._tint((200, 100, 100), pal)
        bc2 = self._tint((100, 100, 200), pal)
        for x in range(64):
            wave = math.sin(x * 0.3 + self.time * 2 * self.speed) * 3
            y1 = int(32 + wave - 2)
            y2 = int(32 + wave + 2)
            if 0 <= y1 < 64:
                d.set_pixel(x, y1, bc1)
            if 0 <= y2 < 64:
                d.set_pixel(x, y2, bc2)
            mid = int(32 + wave)
            if 0 <= mid < 64:
                d.set_pixel(x, mid, pal['dim'])

    def _draw_nucleosomes(self, pal):
        """DNA wrapped around histone octamers (beads on a string)."""
        d = self.display
        histone = self._tint((120, 100, 200), pal)
        linker = pal['backbone']
        num = 5
        spacing = 12
        sx = 8
        centers = []
        for i in range(num):
            cx = sx + i * spacing
            cy = 32 + int(math.sin(i * 1.2 + self.time * 0.5 * self.speed) * 5)
            centers.append((cx, cy))
            r = 4
            # Histone core
            d.draw_circle(cx, cy, r, histone, filled=True)
            # DNA wrapping around the histone
            for step in range(16):
                a = step * math.pi * 2 / 16 + self.time * self.speed
                px = cx + int((r + 2) * math.cos(a))
                py = cy + int((r + 2) * math.sin(a))
                if 0 <= px < 64 and 0 <= py < 64:
                    d.set_pixel(px, py, linker)

        # Linker DNA between histones
        for i in range(num - 1):
            x1, y1 = centers[i]
            x2, y2 = centers[i + 1]
            d.draw_line(x1 + 5, y1, x2 - 5, y2, pal['dim'])

    def _draw_fiber(self, pal):
        """30nm chromatin fiber: zigzag of packed nucleosomes."""
        d = self.display
        fiber = self._tint((150, 120, 220), pal)
        num = 10
        prev = None
        for i in range(num):
            y_off = -8 if i % 2 == 0 else 8
            cx = 6 + i * 5 + int(math.cos(self.time * 0.2 * self.speed
                                           + i * 0.3) * 1)
            cy = 32 + y_off + int(math.sin(self.time * 0.3 * self.speed
                                           + i * 0.5) * 2)
            d.draw_circle(cx, cy, 3, fiber, filled=True)
            if prev:
                d.draw_line(prev[0], prev[1], cx, cy, pal['dim'])
            prev = (cx, cy)

    def _draw_chromosome(self, pal):
        """Condensed metaphase chromosome (X shape)."""
        d = self.display
        chrom = self._tint((180, 100, 255), pal)
        bright = self._tint((220, 160, 255), pal)
        cx, cy = 32, 32
        scale = 1.0 + 0.05 * math.sin(self.time * 1.5 * self.speed)
        arm_len = int(18 * scale)
        width = 3

        # Four arms radiating from centromere
        arms = [(-0.7, -0.9), (0.7, -0.9), (-0.7, 0.9), (0.7, 0.9)]
        for dx_d, dy_d in arms:
            for t in range(arm_len):
                frac = t / arm_len
                # Slight curve outward
                curve = 0.15 * t * math.sin(frac * 2)
                ax = cx + int(dx_d * t + curve * (1 if dx_d > 0 else -1))
                ay = cy + int(dy_d * t)
                for w in range(-width // 2, width // 2 + 1):
                    px = ax + w
                    if 0 <= px < 64 and 0 <= ay < 64:
                        c = bright if abs(w) == 0 else chrom
                        d.set_pixel(px, ay, c)

        # Centromere
        d.draw_circle(cx, cy, 2, pal['highlight'], filled=True)
