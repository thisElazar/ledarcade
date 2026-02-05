"""
CELL - Cellular Pathways
=========================
Data-driven visualization of molecular machinery inside cells.
Protein complexes embedded in membranes with flowing molecules.
The classic biochemistry textbook cross-section, animated.

Each pathway is defined as data: membrane position, protein complexes,
and particle flows between them. One rendering engine draws any pathway.
"""

import math
import random
from . import Visual, Display, Colors

# ---------------------------------------------------------------------------
# Particle visual styles
# ---------------------------------------------------------------------------
PARTICLE_STYLES = {
    'photon':   {'color': (255, 255, 150), 'size': 1, 'wave': True},
    'electron': {'color': (255, 255, 50),  'size': 1},
    'h_plus':   {'color': (255, 110, 70),  'size': 1},
    'water':    {'color': (80, 140, 255),  'size': 1},
    'oxygen':   {'color': (100, 220, 140), 'size': 2},
    'nadph':    {'color': (100, 200, 255), 'size': 2},
    'atp':      {'color': (255, 200, 50),  'size': 2},
}

# ---------------------------------------------------------------------------
# Pathway definitions
# ---------------------------------------------------------------------------
# Each pathway: membrane, regions, protein complexes, particle flows.
# The rendering engine interprets this data to draw any pathway.

PATHWAYS = [
    {
        'name': 'LIGHT REACTIONS',
        'sci_name': 'PHOTOSYNTHESIS',
        'group': 'energy',
        'membrane': {
            'y': 30,
            'head_color': (120, 115, 65),
            'tail_color': (50, 45, 25),
        },
        'stroma_color': (6, 14, 8),
        'lumen_color': (8, 10, 20),
        'lumen_warm': True,  # H+ gradient tints lumen warm near membrane
        'complexes': [
            # Photosystem II — water splitting, light capture at 680nm
            # Green: chlorophyll-rich antenna complex
            {'id': 'psii', 'x': 10, 'w': 9, 'color': (45, 125, 65),
             'above': 5, 'below': 6, 'channel_w': 1},
            # Cytochrome b6f — electron relay, proton pump
            # Red-brown: heme prosthetic groups
            {'id': 'b6f', 'x': 27, 'w': 7, 'color': (145, 60, 50),
             'above': 4, 'below': 4, 'channel_w': 1},
            # Photosystem I — light capture at 700nm, reduces ferredoxin
            # Blue: distinct from PSII
            {'id': 'psi', 'x': 43, 'w': 9, 'color': (50, 60, 135),
             'above': 5, 'below': 5, 'channel_w': 1},
            # ATP synthase — rotary motor driven by proton motive force
            # Gold: energy/ATP association
            {'id': 'atps', 'x': 58, 'w': 5, 'color': (165, 130, 40),
             'above': 3, 'below': 3, 'channel_w': 1,
             'f1': {'stalk_h': 3, 'head_h': 4, 'head_w': 7,
                    'color': (185, 150, 50)}},
        ],
        'flows': [
            # Photons striking photosystems from above
            {'type': 'photon', 'path': [(10, 4), (10, 23)],
             'speed': 35, 'interval': 2.0, 'max': 2},
            {'type': 'photon', 'path': [(43, 4), (43, 23)],
             'speed': 35, 'interval': 2.5, 'max': 2},
            # Electron transport: PSII -> plastoquinone -> Cyt b6f
            # Moves through the membrane lipid bilayer
            {'type': 'electron', 'path': [(14, 30), (24, 30)],
             'speed': 10, 'interval': 2.5, 'max': 2},
            # Electron: Cyt b6f -> plastocyanin -> PSI
            # Plastocyanin shuttles through the lumen
            {'type': 'electron', 'path': [(30, 35), (35, 37), (39, 35)],
             'speed': 8, 'interval': 2.5, 'max': 2},
            # Electron: PSI -> ferredoxin -> NADP+ reductase
            # Rises into stroma where NADPH is produced
            {'type': 'electron', 'path': [(47, 26), (52, 20), (56, 16)],
             'speed': 10, 'interval': 2.5, 'max': 2},
            # H+ from water splitting at PSII released into lumen
            {'type': 'h_plus', 'path': [(9, 35), (9, 42)],
             'speed': 5, 'interval': 2.5, 'max': 2},
            # H+ pumped by Cyt b6f: stroma -> lumen (Q cycle)
            {'type': 'h_plus', 'path': [(27, 26), (27, 42)],
             'speed': 5, 'interval': 2.0, 'max': 3},
            # H+ return through ATP synthase: lumen -> stroma
            # This flow drives the rotary motor
            {'type': 'h_plus', 'path': [(58, 42), (58, 20)],
             'speed': 6, 'interval': 1.8, 'max': 3},
            # Water entering PSII from lumen side
            {'type': 'water', 'path': [(7, 44), (7, 36)],
             'speed': 3, 'interval': 3.5, 'max': 1},
            # O2 released from water splitting, diffuses into lumen
            {'type': 'oxygen', 'path': [(13, 36), (14, 46)],
             'speed': 2, 'interval': 4.5, 'max': 1},
        ],
    },
]

# ---------------------------------------------------------------------------
# Groups
# ---------------------------------------------------------------------------
GROUPS = [
    ('all', 'ALL', (255, 255, 255)),
]


def _build_group_indices():
    indices = {'all': list(range(len(PATHWAYS)))}
    for i, pw in enumerate(PATHWAYS):
        g = pw['group']
        if g not in indices:
            indices[g] = []
        indices[g].append(i)
    return indices


def _path_length(path):
    total = 0
    for i in range(len(path) - 1):
        dx = path[i + 1][0] - path[i][0]
        dy = path[i + 1][1] - path[i][1]
        total += math.sqrt(dx * dx + dy * dy)
    return total


def _interp_path(path, progress):
    """Interpolate position along path at progress 0-1 (arc-length)."""
    if len(path) < 2:
        return path[0]
    seg_lens = []
    total = 0
    for i in range(len(path) - 1):
        dx = path[i + 1][0] - path[i][0]
        dy = path[i + 1][1] - path[i][1]
        seg_lens.append(math.sqrt(dx * dx + dy * dy))
        total += seg_lens[-1]
    if total < 0.01:
        return path[0]
    target = max(0.0, min(progress, 1.0)) * total
    accum = 0
    for i, sl in enumerate(seg_lens):
        if accum + sl >= target or i == len(seg_lens) - 1:
            t = (target - accum) / sl if sl > 0.01 else 0
            x = path[i][0] + t * (path[i + 1][0] - path[i][0])
            y = path[i][1] + t * (path[i + 1][1] - path[i][1])
            return (x, y)
        accum += sl
    return path[-1]


# ===================================================================
# CELL visual
# ===================================================================
class Cell(Visual):
    name = "CELL"
    description = "Cellular pathways"
    category = "science"

    def reset(self):
        self.time = 0.0
        self.group_indices = _build_group_indices()
        self.group_idx = 0
        self.pw_pos = 0
        self.auto_cycle = True
        self.cycle_timer = 0.0
        self.cycle_duration = 10.0
        self.overlay_timer = 0.0
        self.label_timer = 0.0
        self.scroll_offset = 0.0
        self.active_particles = []
        self.spawn_timers = []
        self.flow_lengths = []
        self._prepare_pathway()

    # -------------------------------------------------------------------
    # Navigation
    # -------------------------------------------------------------------
    def _current_pw_list(self):
        key = GROUPS[self.group_idx][0]
        return self.group_indices.get(key, [])

    def _current_pw_index(self):
        pl = self._current_pw_list()
        if not pl:
            return 0
        return pl[self.pw_pos % len(pl)]

    def _prepare_pathway(self):
        idx = self._current_pw_index()
        self.cur_pw = PATHWAYS[idx]
        self.label_timer = 0.0
        self.scroll_offset = 0.0
        self.active_particles = []
        flows = self.cur_pw['flows']
        self.spawn_timers = [random.uniform(0, f['interval'] * 0.5)
                             for f in flows]
        self.flow_lengths = [_path_length(f['path']) for f in flows]

    # -------------------------------------------------------------------
    # Input
    # -------------------------------------------------------------------
    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.up_pressed:
            self.group_idx = (self.group_idx - 1) % len(GROUPS)
            self.pw_pos = 0
            self.cycle_timer = 0.0
            self.overlay_timer = 2.5
            self._prepare_pathway()
            consumed = True
        if input_state.down_pressed:
            self.group_idx = (self.group_idx + 1) % len(GROUPS)
            self.pw_pos = 0
            self.cycle_timer = 0.0
            self.overlay_timer = 2.5
            self._prepare_pathway()
            consumed = True
        if input_state.left_pressed:
            pl = self._current_pw_list()
            if pl:
                self.pw_pos = (self.pw_pos - 1) % len(pl)
            self.cycle_timer = 0.0
            self._prepare_pathway()
            consumed = True
        if input_state.right_pressed:
            pl = self._current_pw_list()
            if pl:
                self.pw_pos = (self.pw_pos + 1) % len(pl)
            self.cycle_timer = 0.0
            self._prepare_pathway()
            consumed = True
        if input_state.action_l or input_state.action_r:
            self.auto_cycle = not self.auto_cycle
            consumed = True
        return consumed

    # -------------------------------------------------------------------
    # Update
    # -------------------------------------------------------------------
    def update(self, dt: float):
        self.time += dt
        self.label_timer += dt
        self.scroll_offset += dt * 20
        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)
        if self.auto_cycle:
            self.cycle_timer += dt
            if self.cycle_timer >= self.cycle_duration:
                self.cycle_timer = 0.0
                pl = self._current_pw_list()
                if pl:
                    self.pw_pos = (self.pw_pos + 1) % len(pl)
                self._prepare_pathway()
        self._update_particles(dt)

    def _update_particles(self, dt):
        flows = self.cur_pw['flows']
        for i, flow in enumerate(flows):
            self.spawn_timers[i] += dt
            if self.spawn_timers[i] >= flow['interval']:
                self.spawn_timers[i] = 0.0
                count = sum(1 for p in self.active_particles if p['flow'] == i)
                if count < flow.get('max', 3):
                    self.active_particles.append({
                        'flow': i, 'progress': 0.0,
                    })
        for p in self.active_particles:
            fl = self.flow_lengths[p['flow']]
            if fl > 0:
                p['progress'] += (flows[p['flow']]['speed'] / fl) * dt
        self.active_particles = [p for p in self.active_particles
                                 if p['progress'] < 1.0]

    # -------------------------------------------------------------------
    # Draw
    # -------------------------------------------------------------------
    def draw(self):
        d = self.display
        pw = self.cur_pw
        mem_y = pw['membrane']['y']

        # Background: stroma color everywhere, then lumen below
        d.clear(pw['stroma_color'])
        lc = pw['lumen_color']
        warm = pw.get('lumen_warm', False)
        lumen_top = mem_y + 3
        for y in range(lumen_top, 56):
            if warm:
                frac = 1.0 - (y - lumen_top) / max(1, 55 - lumen_top)
                c = (min(255, lc[0] + int(10 * frac)), lc[1],
                     max(0, lc[2] - int(4 * frac)))
            else:
                c = lc
            for x in range(64):
                d.set_pixel(x, y, c)

        # Dim region labels
        d.draw_text_small(2, 8, 'STROMA', (18, 28, 18))
        d.draw_text_small(2, 48, 'LUMEN', (18, 18, 32))

        self._render_membrane(pw)
        self._render_complexes(pw)
        self._render_particles(pw)
        self._draw_label()
        self._draw_overlay()

    # -------------------------------------------------------------------
    # Membrane: lipid bilayer cross-section
    # -------------------------------------------------------------------
    def _render_membrane(self, pw):
        d = self.display
        mem = pw['membrane']
        cy = mem['y']
        head = mem['head_color']
        tail = mem['tail_color']

        # Upper leaflet heads (phospholipid head groups, spaced)
        for x in range(0, 64, 2):
            d.set_pixel(x, cy - 2, head)
        # Hydrophobic fatty acid tails
        for y in range(cy - 1, cy + 2):
            for x in range(64):
                d.set_pixel(x, y, tail)
        # Lower leaflet heads
        for x in range(0, 64, 2):
            d.set_pixel(x, cy + 2, head)

    # -------------------------------------------------------------------
    # Protein complexes embedded in membrane
    # -------------------------------------------------------------------
    def _render_complexes(self, pw):
        d = self.display
        mem_y = pw['membrane']['y']

        for cx in pw['complexes']:
            x = cx['x']
            hw = cx['w'] // 2
            color = cx['color']
            above = cx.get('above', 4)
            below = cx.get('below', 4)

            top = mem_y - 2 - above
            bot = mem_y + 2 + below
            left = x - hw
            right = x + hw

            # Main body with highlight and edge shading
            for py in range(top, bot + 1):
                for px in range(left, right + 1):
                    edge = (px == left or px == right or
                            py == top or py == bot)
                    if edge:
                        shade = 0.55
                    elif py == top + 1:
                        shade = 1.25
                    else:
                        shade = 1.0
                    c = (min(255, int(color[0] * shade)),
                         min(255, int(color[1] * shade)),
                         min(255, int(color[2] * shade)))
                    d.set_pixel(px, py, c)

            # Channel pore (dark stripe through center)
            cw = cx.get('channel_w', 0)
            if cw > 0:
                pore = (max(1, color[0] // 5),
                        max(1, color[1] // 5),
                        max(1, color[2] // 5))
                for py in range(top + 2, bot - 1):
                    for px in range(x - cw // 2, x + cw // 2 + 1):
                        d.set_pixel(px, py, pore)

            # ATP synthase F1 head (lollipop above membrane)
            f1 = cx.get('f1')
            if f1:
                f1c = f1['color']
                stalk_h = f1['stalk_h']
                head_h = f1['head_h']
                head_hw = f1['head_w'] // 2
                stalk_bot = top
                stalk_top = top - stalk_h
                head_top = stalk_top - head_h

                # Stalk (narrow connector)
                for py in range(stalk_top, stalk_bot):
                    d.set_pixel(x, py, color)

                # F1 catalytic head
                for py in range(head_top, stalk_top):
                    for px in range(x - head_hw, x + head_hw + 1):
                        edge = (px == x - head_hw or px == x + head_hw
                                or py == head_top or py == stalk_top - 1)
                        shade = 0.55 if edge else (1.25 if py == head_top + 1 else 1.0)
                        c = (min(255, int(f1c[0] * shade)),
                             min(255, int(f1c[1] * shade)),
                             min(255, int(f1c[2] * shade)))
                        d.set_pixel(px, py, c)

                # Rotation indicator: 3 subunit dots cycling brightness
                t = self.time
                for si in range(3):
                    angle = t * 1.5 + si * (2.0 * math.pi / 3.0)
                    bright = 0.6 + 0.4 * max(0, math.sin(angle))
                    mid_y = (head_top + stalk_top) // 2
                    sx = x + int(2 * math.cos(angle))
                    sy = mid_y + int(1.5 * math.sin(angle))
                    sc = (min(255, int(f1c[0] * bright * 1.2)),
                          min(255, int(f1c[1] * bright * 1.2)),
                          min(255, int(f1c[2] * bright * 0.8)))
                    d.set_pixel(sx, sy, sc)

    # -------------------------------------------------------------------
    # Flowing particles
    # -------------------------------------------------------------------
    def _render_particles(self, pw):
        d = self.display
        flows = pw['flows']
        for p in self.active_particles:
            flow = flows[p['flow']]
            style = PARTICLE_STYLES.get(flow['type'],
                                        PARTICLE_STYLES['electron'])
            pos = _interp_path(flow['path'], p['progress'])
            px, py = int(pos[0]), int(pos[1])
            color = style['color']

            # Photons: wavy path (electromagnetic wave)
            if style.get('wave'):
                wave = math.sin(p['progress'] * 30) * 1.5
                px = int(pos[0] + wave)

            size = style.get('size', 1)
            d.set_pixel(px, py, color)
            if size >= 2:
                d.set_pixel(px + 1, py, color)
                d.set_pixel(px, py + 1, color)

    # -------------------------------------------------------------------
    # Labels and overlay (same pattern as PERIODIC/MICROSCOPE)
    # -------------------------------------------------------------------
    def _draw_label(self):
        d = self.display
        pw = self.cur_pw
        phase = int(self.label_timer / 4) % 2
        label = pw['name'] if phase == 0 else pw['sci_name']
        max_chars = 14
        if len(label) > max_chars:
            padded = label + "    " + label
            total_w = len(label + "    ") * 4
            offset = int(self.scroll_offset) % total_w
            d.draw_text_small(2 - offset, 58, padded, Colors.WHITE)
        else:
            d.draw_text_small(2, 58, label, Colors.WHITE)

    def _draw_overlay(self):
        if self.overlay_timer > 0:
            d = self.display
            _, gname, gcolor = GROUPS[self.group_idx]
            alpha = min(1.0, self.overlay_timer / 0.5)
            oc = (int(gcolor[0] * alpha), int(gcolor[1] * alpha),
                  int(gcolor[2] * alpha))
            d.draw_text_small(2, 2, gname, oc)
