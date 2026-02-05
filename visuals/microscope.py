"""
MICROSCOPE - Biological Specimens
==================================
Animated biological specimens as seen through a microscope.
Each specimen has its own rendering and animation logic.
Up/Down cycles groups, Left/Right browses specimens, Space toggles auto-cycle.
"""

import math
import random
from . import Visual, Display, Colors

# ---------------------------------------------------------------------------
# Groups (cycled with up/down)
# ---------------------------------------------------------------------------
GROUPS = [
    ('all',     'ALL',     (255, 255, 255)),
    ('blood',   'BLOOD',   (255, 80, 80)),
    ('plant',   'PLANT',   (80, 255, 80)),
    ('microbe', 'MICROBE', (200, 120, 255)),
    ('water',   'WATER',   (80, 180, 255)),
]

# ---------------------------------------------------------------------------
# Specimens data
# ---------------------------------------------------------------------------
SPECIMENS = [
    # BLOOD group
    {'name': 'RED BLOOD CELLS', 'sci_name': 'ERYTHROCYTES',
     'group': 'blood', 'setup': '_setup_rbc', 'draw': '_draw_rbc',
     'bg': (15, 8, 0)},
    {'name': 'SICKLE CELLS', 'sci_name': 'SICKLE CELL ANEMIA',
     'group': 'blood', 'setup': '_setup_sickle', 'draw': '_draw_sickle',
     'bg': (15, 8, 0)},
    {'name': 'WHITE BLOOD CELL', 'sci_name': 'LEUKOCYTE',
     'group': 'blood', 'setup': '_setup_wbc', 'draw': '_draw_wbc',
     'bg': (12, 6, 0)},
    # PLANT group
    {'name': 'PLANT CELL', 'sci_name': 'CELL CROSS-SECTION',
     'group': 'plant', 'setup': '_setup_plant_cell', 'draw': '_draw_plant_cell',
     'bg': (5, 15, 5)},
    {'name': 'STOMATA', 'sci_name': 'GUARD CELLS',
     'group': 'plant', 'setup': '_setup_stomata', 'draw': '_draw_stomata',
     'bg': (10, 30, 10)},
    {'name': 'POLLEN', 'sci_name': 'POLLEN GRAINS',
     'group': 'plant', 'setup': '_setup_pollen', 'draw': '_draw_pollen',
     'bg': (8, 8, 2)},
    # MICROBE group
    {'name': 'BACTERIA', 'sci_name': 'BACILLUS',
     'group': 'microbe', 'setup': '_setup_bacteria', 'draw': '_draw_bacteria',
     'bg': (5, 5, 12)},
    {'name': 'AMOEBA', 'sci_name': 'AMOEBA PROTEUS',
     'group': 'microbe', 'setup': '_setup_amoeba', 'draw': '_draw_amoeba',
     'bg': (5, 8, 12)},
    {'name': 'PARAMECIUM', 'sci_name': 'PARAMECIUM CAUDATUM',
     'group': 'microbe', 'setup': '_setup_paramecium', 'draw': '_draw_paramecium',
     'bg': (5, 5, 10)},
    # WATER group
    {'name': 'SURFACE TENSION', 'sci_name': 'HYDROGEN BONDS',
     'group': 'water', 'setup': '_setup_surface', 'draw': '_draw_surface',
     'bg': (2, 2, 10)},
    {'name': 'DIATOMS', 'sci_name': 'BACILLARIOPHYCEAE',
     'group': 'water', 'setup': '_setup_diatoms', 'draw': '_draw_diatoms',
     'bg': (5, 8, 15)},
]


def _build_group_indices():
    """Build mapping from group key to list of SPECIMENS indices."""
    indices = {'all': list(range(len(SPECIMENS)))}
    for i, spec in enumerate(SPECIMENS):
        g = spec['group']
        if g not in indices:
            indices[g] = []
        indices[g].append(i)
    return indices


class Microscope(Visual):
    name = "MICROSCOPE"
    description = "Biological specimens"
    category = "science"

    def reset(self):
        self.time = 0.0
        self.group_indices = _build_group_indices()
        self.group_idx = 0
        self.spec_pos = 0
        self.auto_cycle = True
        self.cycle_timer = 0.0
        self.cycle_duration = 10.0
        self.overlay_timer = 0.0
        self.label_timer = 0.0
        self.scroll_offset = 0.0
        # Specimen-specific state
        self.particles = []
        self.state = {}
        self._prepare_specimen()

    # -------------------------------------------------------------------
    # Navigation helpers
    # -------------------------------------------------------------------
    def _current_spec_list(self):
        key = GROUPS[self.group_idx][0]
        return self.group_indices.get(key, [])

    def _current_spec_index(self):
        sl = self._current_spec_list()
        if not sl:
            return 0
        return sl[self.spec_pos % len(sl)]

    def _prepare_specimen(self):
        idx = self._current_spec_index()
        spec = SPECIMENS[idx]
        self.cur_spec = spec
        self.label_timer = 0.0
        self.scroll_offset = 0.0
        self.particles = []
        self.state = {}
        setup_fn = getattr(self, spec['setup'])
        setup_fn()

    # -------------------------------------------------------------------
    # Input
    # -------------------------------------------------------------------
    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.up_pressed:
            self.group_idx = (self.group_idx - 1) % len(GROUPS)
            self.spec_pos = 0
            self.cycle_timer = 0.0
            self.overlay_timer = 2.5
            self._prepare_specimen()
            consumed = True
        if input_state.down_pressed:
            self.group_idx = (self.group_idx + 1) % len(GROUPS)
            self.spec_pos = 0
            self.cycle_timer = 0.0
            self.overlay_timer = 2.5
            self._prepare_specimen()
            consumed = True
        if input_state.left_pressed:
            sl = self._current_spec_list()
            if sl:
                self.spec_pos = (self.spec_pos - 1) % len(sl)
            self.cycle_timer = 0.0
            self._prepare_specimen()
            consumed = True
        if input_state.right_pressed:
            sl = self._current_spec_list()
            if sl:
                self.spec_pos = (self.spec_pos + 1) % len(sl)
            self.cycle_timer = 0.0
            self._prepare_specimen()
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
                sl = self._current_spec_list()
                if sl:
                    self.spec_pos = (self.spec_pos + 1) % len(sl)
                self._prepare_specimen()

    # -------------------------------------------------------------------
    # Draw
    # -------------------------------------------------------------------
    def draw(self):
        d = self.display
        bg = self.cur_spec['bg']
        d.clear(bg)

        draw_fn = getattr(self, self.cur_spec['draw'])
        draw_fn()

        self._draw_label()
        self._draw_overlay()

    # -------------------------------------------------------------------
    # Label (bottom, y=58)
    # -------------------------------------------------------------------
    def _draw_label(self):
        d = self.display
        phase = int(self.label_timer / 4) % 2
        if phase == 0:
            label = self.cur_spec['name']
        else:
            label = self.cur_spec['sci_name']

        max_chars = 14
        if len(label) > max_chars:
            padded = label + "    " + label
            char_width = 4
            total_width = len(label + "    ") * char_width
            offset = int(self.scroll_offset) % total_width
            d.draw_text_small(2 - offset, 58, padded, Colors.WHITE)
        else:
            d.draw_text_small(2, 58, label, Colors.WHITE)

    # -------------------------------------------------------------------
    # Group overlay (top, y=2)
    # -------------------------------------------------------------------
    def _draw_overlay(self):
        if self.overlay_timer > 0:
            d = self.display
            _, gname, gcolor = GROUPS[self.group_idx]
            alpha = min(1.0, self.overlay_timer / 0.5)
            oc = (int(gcolor[0] * alpha), int(gcolor[1] * alpha),
                  int(gcolor[2] * alpha))
            d.draw_text_small(2, 2, gname, oc)

    # ===================================================================
    # Shared helpers
    # ===================================================================
    def _draw_cell_disc(self, cx, cy, r, color, highlight=True):
        """Draw a biconcave RBC disc with center dimming and specular highlight."""
        d = self.display
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                dist_sq = dx * dx + dy * dy
                if dist_sq <= r * r:
                    dist = math.sqrt(dist_sq)
                    frac = dist / max(r, 1)
                    # Biconcave: dimmer in center band
                    if frac < 0.4:
                        dim = 0.6
                    elif frac < 0.7:
                        dim = 0.8 + 0.2 * ((frac - 0.4) / 0.3)
                    else:
                        dim = 1.0 - 0.3 * ((frac - 0.7) / 0.3)
                    c = (max(0, min(255, int(color[0] * dim))),
                         max(0, min(255, int(color[1] * dim))),
                         max(0, min(255, int(color[2] * dim))))
                    d.set_pixel(cx + dx, cy + dy, c)
        if highlight and r >= 3:
            hx = cx - r // 3
            hy = cy - r // 3
            hc = (min(255, color[0] + 80), min(255, color[1] + 80),
                  min(255, color[2] + 80))
            d.set_pixel(hx, hy, hc)

    def _draw_crescent(self, cx, cy, r, color):
        """Draw a sickle/crescent shape via circle subtraction."""
        d = self.display
        offset_x = r * 0.6
        for dy in range(-r - 1, r + 2):
            for dx in range(-r - 1, r + 2):
                dist_main = dx * dx + dy * dy
                dist_sub = (dx - offset_x) ** 2 + dy * dy
                if dist_main <= r * r and dist_sub > r * r:
                    frac = math.sqrt(dist_main) / max(r, 1)
                    dim = 0.7 + 0.3 * frac
                    c = (max(0, min(255, int(color[0] * dim))),
                         max(0, min(255, int(color[1] * dim))),
                         max(0, min(255, int(color[2] * dim))))
                    d.set_pixel(cx + dx, cy + dy, c)

    def _draw_filled_ellipse(self, cx, cy, rx, ry, color):
        """Draw a filled ellipse."""
        d = self.display
        for dy in range(-ry, ry + 1):
            for dx in range(-rx, rx + 1):
                if rx > 0 and ry > 0:
                    if (dx * dx) / (rx * rx) + (dy * dy) / (ry * ry) <= 1.0:
                        d.set_pixel(cx + dx, cy + dy, color)

    def _drift_particles(self, dt, wrap=True):
        """Update particle positions with velocity, optional wrap-around."""
        for p in self.particles:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            if wrap:
                if p['x'] > 68:
                    p['x'] = -4
                elif p['x'] < -4:
                    p['x'] = 68
                if p['y'] > 68:
                    p['y'] = -4
                elif p['y'] < -4:
                    p['y'] = 68

    def _brownian_jitter(self, strength):
        """Apply random velocity perturbations."""
        for p in self.particles:
            p['vx'] += random.uniform(-strength, strength)
            p['vy'] += random.uniform(-strength, strength)

    # ===================================================================
    # 1. RED BLOOD CELLS
    # ===================================================================
    def _setup_rbc(self):
        self.particles = []
        for _ in range(6):
            self.particles.append({
                'x': random.uniform(5, 58),
                'y': random.uniform(8, 48),
                'vx': random.uniform(3, 7),
                'vy': random.uniform(-1, 1),
                'r': random.choice([5, 6, 7]),
                'phase': random.uniform(0, math.pi * 2),
            })

    def _draw_rbc(self):
        d = self.display
        t = self.time
        dt = 1.0 / 30.0
        # Drift
        for p in self.particles:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt + math.sin(t * 2 + p['phase']) * 0.3 * dt
            if p['x'] > 68:
                p['x'] = -8
            if p['y'] < 2:
                p['y'] = 2
            if p['y'] > 52:
                p['y'] = 52

        # Amber plasma shimmer
        for _ in range(20):
            px = random.randint(0, 63)
            py = random.randint(0, 55)
            if random.random() < 0.3:
                d.set_pixel(px, py, (20, 14, 4))

        # Draw cells
        base_color = (200, 50, 40)
        for p in self.particles:
            pulse = 1.0 + 0.05 * math.sin(t * 3 + p['phase'])
            c = (min(255, int(base_color[0] * pulse)),
                 min(255, int(base_color[1] * pulse)),
                 min(255, int(base_color[2] * pulse)))
            self._draw_cell_disc(int(p['x']), int(p['y']), p['r'], c)

    # ===================================================================
    # 2. SICKLE CELLS
    # ===================================================================
    def _setup_sickle(self):
        self.particles = []
        for i in range(8):
            is_sickle = i < 3  # ~40% sickle
            if is_sickle and i < 2:
                # Clustered near center
                x = random.uniform(24, 40)
                y = random.uniform(18, 36)
                vx = random.uniform(-0.5, 0.5)
                vy = random.uniform(-0.5, 0.5)
            else:
                x = random.uniform(5, 58)
                y = random.uniform(8, 48)
                vx = random.uniform(2, 5)
                vy = random.uniform(-1, 1)
            self.particles.append({
                'x': x, 'y': y, 'vx': vx, 'vy': vy,
                'r': random.choice([5, 6]),
                'phase': random.uniform(0, math.pi * 2),
                'sickle': is_sickle,
            })

    def _draw_sickle(self):
        d = self.display
        t = self.time
        dt = 1.0 / 30.0

        for p in self.particles:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            if p['x'] > 68:
                p['x'] = -6
            elif p['x'] < -6:
                p['x'] = 68
            if p['y'] > 52:
                p['y'] = 52
            elif p['y'] < 4:
                p['y'] = 4

        # Plasma shimmer
        for _ in range(15):
            px = random.randint(0, 63)
            py = random.randint(0, 55)
            if random.random() < 0.25:
                d.set_pixel(px, py, (20, 14, 4))

        normal_color = (200, 50, 40)
        sickle_color = (170, 40, 50)
        for p in self.particles:
            cx, cy = int(p['x']), int(p['y'])
            if p['sickle']:
                self._draw_crescent(cx, cy, p['r'], sickle_color)
            else:
                self._draw_cell_disc(cx, cy, p['r'], normal_color)

    # ===================================================================
    # 3. WHITE BLOOD CELL
    # ===================================================================
    def _setup_wbc(self):
        # Background RBCs
        self.particles = []
        for _ in range(5):
            self.particles.append({
                'x': random.uniform(5, 58),
                'y': random.uniform(8, 48),
                'vx': random.uniform(2, 5),
                'vy': random.uniform(-0.5, 0.5),
                'r': random.choice([4, 5]),
                'phase': random.uniform(0, math.pi * 2),
            })
        # WBC state
        self.state['wbc_x'] = 32.0
        self.state['wbc_y'] = 28.0
        self.state['wbc_r'] = 12
        self.state['lobe_angle'] = 0.0

    def _draw_wbc(self):
        d = self.display
        t = self.time
        dt = 1.0 / 30.0

        # Drift background RBCs
        for p in self.particles:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            if p['x'] > 68:
                p['x'] = -5

        # Draw background RBCs (dimmer, behind WBC)
        rbc_color = (140, 35, 25)
        for p in self.particles:
            self._draw_cell_disc(int(p['x']), int(p['y']), p['r'], rbc_color, highlight=False)

        # WBC body - large pale cell with pulsing
        wx = int(self.state['wbc_x'])
        wy = int(self.state['wbc_y'])
        wr = self.state['wbc_r']
        pulse = 1.0 + 0.08 * math.sin(t * 1.5)
        body_r = int(wr * pulse)
        body_color = (180, 190, 210)
        d.draw_circle(wx, wy, body_r, body_color, filled=True)

        # Membrane edge
        edge_color = (140, 150, 170)
        d.draw_circle(wx, wy, body_r, edge_color, filled=False)

        # Lobed nucleus - 3 overlapping purple circles
        self.state['lobe_angle'] += dt * 0.3
        lobe_r = 4
        nucleus_color = (100, 50, 140)
        for i in range(3):
            angle = self.state['lobe_angle'] + i * (2 * math.pi / 3)
            lx = wx + int(3 * math.cos(angle))
            ly = wy + int(3 * math.sin(angle))
            d.draw_circle(lx, ly, lobe_r, nucleus_color, filled=True)

        # Granules - scattered bright pixels
        random.seed(int(t * 2))
        for _ in range(12):
            gx = wx + random.randint(-body_r + 2, body_r - 2)
            gy = wy + random.randint(-body_r + 2, body_r - 2)
            if (gx - wx) ** 2 + (gy - wy) ** 2 < (body_r - 2) ** 2:
                d.set_pixel(gx, gy, (220, 200, 240))
        random.seed()  # Reset seed

    # ===================================================================
    # 4. PLANT CELL
    # ===================================================================
    def _setup_plant_cell(self):
        # Chloroplast positions (orbit around cytoplasm)
        self.state['chloroplasts'] = []
        for i in range(7):
            angle = i * (2 * math.pi / 7)
            self.state['chloroplasts'].append({
                'angle': angle,
                'r_orbit': random.uniform(14, 20),
                'speed': random.uniform(0.15, 0.25),
            })

    def _draw_plant_cell(self):
        d = self.display
        t = self.time
        cx, cy = 32, 28

        # Cell wall (outer rectangle)
        d.draw_rect(4, 4, 56, 48, (80, 140, 60), filled=False)
        d.draw_rect(5, 5, 54, 46, (70, 120, 50), filled=False)

        # Cell membrane (just inside wall)
        d.draw_rect(7, 7, 50, 42, (100, 160, 80), filled=False)

        # Cytoplasm fill (pale green)
        d.draw_rect(8, 8, 48, 40, (25, 50, 20), filled=True)

        # Central vacuole (large, pulsing)
        vac_r = int(10 + 1.5 * math.sin(t * 0.8))
        d.draw_circle(cx, cy, vac_r, (40, 60, 120), filled=True)
        d.draw_circle(cx, cy, vac_r, (60, 80, 140), filled=False)

        # Nucleus
        nuc_x, nuc_y = 18, 18
        d.draw_circle(nuc_x, nuc_y, 6, (80, 70, 50), filled=True)
        d.draw_circle(nuc_x, nuc_y, 6, (100, 90, 70), filled=False)
        # Nucleolus
        d.draw_circle(nuc_x, nuc_y, 2, (120, 100, 70), filled=True)

        # Chloroplasts - orbiting (cytoplasmic streaming)
        for cp in self.state['chloroplasts']:
            cp['angle'] += cp['speed'] * (1.0 / 30.0)
            cpx = cx + int(cp['r_orbit'] * math.cos(cp['angle']))
            cpy = cy + int(cp['r_orbit'] * 0.7 * math.sin(cp['angle']))
            # Stay inside cell
            cpx = max(9, min(55, cpx))
            cpy = max(9, min(46, cpy))
            # Small green ellipse
            self._draw_filled_ellipse(cpx, cpy, 3, 2, (30, 160, 30))
            d.set_pixel(cpx, cpy, (50, 200, 50))  # Bright center

    # ===================================================================
    # 5. STOMATA
    # ===================================================================
    def _setup_stomata(self):
        self.state['pore_phase'] = 0.0

    def _draw_stomata(self):
        d = self.display
        t = self.time
        cx, cy = 32, 28

        # Leaf surface background with subtle cell pattern
        for y in range(0, 56):
            for x in range(64):
                # Irregular cell pattern
                cell_val = ((x * 7 + y * 13) % 17)
                if cell_val == 0:
                    d.set_pixel(x, y, (15, 45, 15))
                elif cell_val < 3:
                    d.set_pixel(x, y, (12, 38, 12))

        # Leaf vein lines
        d.draw_line(0, 28, 63, 28, (8, 25, 8))
        d.draw_line(32, 0, 32, 55, (8, 25, 8))

        # Guard cells - two kidney-bean shapes
        self.state['pore_phase'] += (1.0 / 30.0)
        pore_width = 2 + int(3 * abs(math.sin(t * 0.5)))

        guard_color = (50, 150, 50)
        guard_dark = (30, 100, 30)

        # Upper guard cell (arc above pore)
        for angle_deg in range(-60, 241):
            angle = math.radians(angle_deg)
            r = 12
            gx = cx + int(r * math.cos(angle))
            gy = cy - pore_width + int(r * math.sin(angle)) - 2
            if 0 <= gx < 64 and 0 <= gy < 56:
                if angle_deg < 0 or angle_deg > 180:
                    continue
                # Only draw the upper arc
                if math.sin(angle) < -0.1:
                    d.set_pixel(gx, gy, guard_color)

        # Simplified: two filled ellipses as guard cells
        upper_y = cy - pore_width - 1
        lower_y = cy + pore_width + 1
        self._draw_filled_ellipse(cx, upper_y, 11, 4, guard_color)
        self._draw_filled_ellipse(cx, lower_y, 11, 4, guard_color)

        # Darker edges
        self._draw_filled_ellipse(cx, upper_y, 11, 4, guard_dark)
        # Lighter fill inside
        self._draw_filled_ellipse(cx, upper_y, 9, 3, guard_color)
        self._draw_filled_ellipse(cx, lower_y, 11, 4, guard_dark)
        self._draw_filled_ellipse(cx, lower_y, 9, 3, guard_color)

        # Pore opening (dark gap between guard cells)
        pore_color = (5, 15, 5)
        for px in range(-8, 9):
            width_at_x = pore_width * (1 - (px * px) / 81.0)
            if width_at_x > 0:
                for py in range(-int(width_at_x), int(width_at_x) + 1):
                    d.set_pixel(cx + px, cy + py, pore_color)

        # Chloroplast dots on guard cells
        random.seed(42)
        for _ in range(8):
            gx = cx + random.randint(-8, 8)
            gy_choices = [upper_y + random.randint(-2, 2),
                          lower_y + random.randint(-2, 2)]
            gy = random.choice(gy_choices)
            d.set_pixel(gx, gy, (60, 200, 60))
        random.seed()

    # ===================================================================
    # 6. POLLEN
    # ===================================================================
    def _setup_pollen(self):
        self.particles = []
        for _ in range(5):
            self.particles.append({
                'x': random.uniform(10, 54),
                'y': random.uniform(8, 44),
                'vx': random.uniform(-0.5, 0.5),
                'vy': random.uniform(-0.5, 0.5),
                'r': random.choice([5, 6, 7]),
                'phase': random.uniform(0, math.pi * 2),
                'n_spikes': random.randint(8, 12),
                'rot': random.uniform(0, math.pi * 2),
                'rot_speed': random.uniform(0.2, 0.5),
            })

    def _draw_pollen(self):
        d = self.display
        t = self.time
        dt = 1.0 / 30.0

        # Brownian motion
        self._brownian_jitter(0.3)
        # Damping
        for p in self.particles:
            p['vx'] *= 0.95
            p['vy'] *= 0.95
        self._drift_particles(dt, wrap=False)
        # Bounce off edges
        for p in self.particles:
            if p['x'] < 4 or p['x'] > 59:
                p['vx'] = -p['vx']
                p['x'] = max(4, min(59, p['x']))
            if p['y'] < 4 or p['y'] > 50:
                p['vy'] = -p['vy']
                p['y'] = max(4, min(50, p['y']))

        # Draw grains
        gold = (200, 170, 40)
        gold_bright = (255, 220, 80)
        for p in self.particles:
            cx, cy = int(p['x']), int(p['y'])
            r = p['r']
            # Body
            d.draw_circle(cx, cy, r, gold, filled=True)
            # Texture dots
            d.set_pixel(cx - 1, cy - 1, gold_bright)
            d.set_pixel(cx + 1, cy, (180, 150, 30))

            # Spikes
            p['rot'] += p['rot_speed'] * dt
            for i in range(p['n_spikes']):
                angle = p['rot'] + i * (2 * math.pi / p['n_spikes'])
                spike_len = r + 2
                sx = cx + int(spike_len * math.cos(angle))
                sy = cy + int(spike_len * math.sin(angle))
                d.set_pixel(sx, sy, gold_bright)
                # Mid-spike pixel
                mx = cx + int((r + 1) * math.cos(angle))
                my = cy + int((r + 1) * math.sin(angle))
                d.set_pixel(mx, my, gold)

    # ===================================================================
    # 7. BACTERIA
    # ===================================================================
    def _setup_bacteria(self):
        self.particles = []
        colors = [(140, 60, 180), (160, 70, 200), (180, 80, 140),
                  (200, 100, 160), (140, 50, 160), (170, 80, 190)]
        for i in range(6):
            angle = random.choice([0, 45, 90, 135]) * math.pi / 180
            self.particles.append({
                'x': random.uniform(10, 54),
                'y': random.uniform(8, 44),
                'vx': random.uniform(-2, 2),
                'vy': random.uniform(-2, 2),
                'angle': angle,
                'length': random.randint(8, 12),
                'color': colors[i % len(colors)],
                'phase': random.uniform(0, math.pi * 2),
                'flag_len': random.randint(4, 6),
            })

    def _draw_bacteria(self):
        d = self.display
        t = self.time
        dt = 1.0 / 30.0

        # Slow drift
        for p in self.particles:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            # Wrap
            if p['x'] > 68:
                p['x'] = -8
            elif p['x'] < -8:
                p['x'] = 68
            if p['y'] > 56:
                p['y'] = -4
            elif p['y'] < -4:
                p['y'] = 56

        for p in self.particles:
            cx, cy = int(p['x']), int(p['y'])
            angle = p['angle']
            half_len = p['length'] // 2
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)
            color = p['color']

            # Rod body: thick line
            x0 = cx - int(half_len * cos_a)
            y0 = cy - int(half_len * sin_a)
            x1 = cx + int(half_len * cos_a)
            y1 = cy + int(half_len * sin_a)
            d.draw_line(x0, y0, x1, y1, color)
            # Thicken by drawing adjacent lines
            perp_x = int(sin_a)
            perp_y = int(-cos_a)
            d.draw_line(x0 + perp_x, y0 + perp_y, x1 + perp_x, y1 + perp_y, color)
            d.draw_line(x0 - perp_x, y0 - perp_y, x1 - perp_x, y1 - perp_y, color)

            # End caps
            cap_color = (min(255, color[0] + 20), min(255, color[1] + 20),
                         min(255, color[2] + 20))
            d.draw_circle(x0, y0, 1, cap_color, filled=True)
            d.draw_circle(x1, y1, 1, cap_color, filled=True)

            # Flagella (wavy tail from one end)
            for fi in range(p['flag_len']):
                wave = math.sin(t * 5 + p['phase'] + fi * 1.2) * 2
                fx = x0 - int((fi + 1) * cos_a * 1.5) + int(wave * sin_a)
                fy = y0 - int((fi + 1) * sin_a * 1.5) - int(wave * cos_a)
                dim_color = (color[0] // 2, color[1] // 2, color[2] // 2)
                d.set_pixel(fx, fy, dim_color)

    # ===================================================================
    # 8. AMOEBA
    # ===================================================================
    def _setup_amoeba(self):
        n_lobes = 6
        self.state['cx'] = 32.0
        self.state['cy'] = 26.0
        self.state['lobes'] = []
        for i in range(n_lobes):
            angle = i * (2 * math.pi / n_lobes)
            self.state['lobes'].append({
                'angle': angle,
                'length': random.uniform(8, 14),
                'target': random.uniform(8, 16),
                'speed': random.uniform(1.5, 3.0),
            })
        self.state['vacuole_phase'] = 0.0

    def _draw_amoeba(self):
        d = self.display
        t = self.time
        dt = 1.0 / 30.0
        cx = self.state['cx']
        cy = self.state['cy']

        # Update lobe extensions
        for lobe in self.state['lobes']:
            diff = lobe['target'] - lobe['length']
            lobe['length'] += diff * lobe['speed'] * dt
            if abs(diff) < 0.5:
                lobe['target'] = random.uniform(7, 17)

        # Render body via radial distance check
        body_color = (80, 140, 100)
        membrane_color = (60, 110, 80)
        lobes = self.state['lobes']
        n_lobes = len(lobes)

        for py in range(max(0, int(cy) - 22), min(56, int(cy) + 22)):
            for px in range(max(0, int(cx) - 22), min(64, int(cx) + 22)):
                dx = px - cx
                dy = py - cy
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < 0.5:
                    d.set_pixel(px, py, body_color)
                    continue
                angle = math.atan2(dy, dx)

                # Interpolate lobe radii
                max_r = 0
                for i, lobe in enumerate(lobes):
                    a_diff = angle - lobe['angle']
                    # Normalize
                    while a_diff > math.pi:
                        a_diff -= 2 * math.pi
                    while a_diff < -math.pi:
                        a_diff += 2 * math.pi
                    influence = max(0, 1.0 - abs(a_diff) / (math.pi / (n_lobes * 0.6)))
                    r = lobe['length'] * influence
                    if r > max_r:
                        max_r = r

                # Minimum base radius
                boundary = max(max_r, 5)

                if dist < boundary - 1:
                    d.set_pixel(px, py, body_color)
                elif dist < boundary:
                    d.set_pixel(px, py, membrane_color)

        # Nucleus
        nuc_x = int(cx) + 3
        nuc_y = int(cy) - 1
        d.draw_circle(nuc_x, nuc_y, 4, (60, 80, 120), filled=True)
        d.draw_circle(nuc_x, nuc_y, 4, (80, 100, 140), filled=False)

        # Contractile vacuole (pulsing pixel)
        self.state['vacuole_phase'] += dt
        vac_pulse = abs(math.sin(self.state['vacuole_phase'] * 2))
        vac_color = (int(40 + 60 * vac_pulse), int(80 + 60 * vac_pulse),
                     int(120 + 60 * vac_pulse))
        d.set_pixel(int(cx) - 5, int(cy) + 2, vac_color)
        d.set_pixel(int(cx) - 4, int(cy) + 2, vac_color)

    # ===================================================================
    # 9. PARAMECIUM
    # ===================================================================
    def _setup_paramecium(self):
        self.state['body_cx'] = 32.0
        self.state['body_cy'] = 26.0
        self.state['body_rx'] = 7
        self.state['body_ry'] = 14
        self.state['cilia_phase'] = 0.0
        self.state['drift_vx'] = 1.5
        self.state['drift_vy'] = 0.3

    def _draw_paramecium(self):
        d = self.display
        t = self.time
        dt = 1.0 / 30.0

        # Slow drift
        self.state['body_cx'] += self.state['drift_vx'] * dt
        self.state['body_cy'] += self.state['drift_vy'] * dt
        # Wrap
        if self.state['body_cx'] > 72:
            self.state['body_cx'] = -8
        if self.state['body_cy'] > 56:
            self.state['body_cy'] = 2
        elif self.state['body_cy'] < 2:
            self.state['body_cy'] = 56

        cx = int(self.state['body_cx'])
        cy = int(self.state['body_cy'])
        rx = self.state['body_rx']
        ry = self.state['body_ry']

        # Body (slipper-shaped ellipse)
        body_color = (120, 140, 130)
        self._draw_filled_ellipse(cx, cy, rx, ry, body_color)

        # Membrane
        membrane = (90, 110, 100)
        for angle_i in range(60):
            a = angle_i * (2 * math.pi / 60)
            mx = cx + int(rx * math.cos(a))
            my = cy + int(ry * math.sin(a))
            d.set_pixel(mx, my, membrane)

        # Oral groove (darker indentation on one side)
        groove_color = (70, 85, 75)
        for gy in range(-4, 5):
            gx = cx - rx + 2
            d.set_pixel(gx, cy + gy, groove_color)
            d.set_pixel(gx + 1, cy + gy, groove_color)

        # Macronucleus (large, bean-shaped)
        mac_color = (90, 70, 110)
        self._draw_filled_ellipse(cx + 1, cy - 2, 4, 3, mac_color)

        # Micronucleus (small dot)
        d.set_pixel(cx + 3, cy - 4, (120, 90, 140))
        d.set_pixel(cx + 4, cy - 4, (120, 90, 140))

        # Contractile vacuoles at ends
        vac_pulse = abs(math.sin(t * 2))
        vac_c = (int(60 + 60 * vac_pulse), int(80 + 60 * vac_pulse),
                 int(140 + 60 * vac_pulse))
        d.set_pixel(cx, cy - ry + 2, vac_c)
        d.set_pixel(cx, cy + ry - 2, vac_c)

        # Cilia - perimeter pixels flashing in metachronal wave
        self.state['cilia_phase'] += dt * 8
        n_cilia = 24
        cilia_bright = (180, 210, 200)
        cilia_dim = (100, 120, 110)
        for i in range(n_cilia):
            a = i * (2 * math.pi / n_cilia)
            wave = math.sin(self.state['cilia_phase'] + i * 0.8)
            extend = 1 if wave > 0.3 else 0
            cilia_x = cx + int((rx + 1 + extend) * math.cos(a))
            cilia_y = cy + int((ry + 1 + extend) * math.sin(a))
            color = cilia_bright if wave > 0.3 else cilia_dim
            d.set_pixel(cilia_x, cilia_y, color)

    # ===================================================================
    # 10. SURFACE TENSION
    # ===================================================================
    def _setup_surface(self):
        # Water molecules
        self.state['molecules'] = []
        surface_y = 28
        # Surface molecules (packed tighter)
        for i in range(10):
            self.state['molecules'].append({
                'x': 4 + i * 6,
                'y': surface_y + random.uniform(-1, 1),
                'vx': random.uniform(-0.3, 0.3),
                'vy': random.uniform(-0.2, 0.2),
                'surface': True,
            })
        # Bulk molecules (more spread out)
        for _ in range(12):
            self.state['molecules'].append({
                'x': random.uniform(4, 60),
                'y': random.uniform(34, 52),
                'vx': random.uniform(-0.5, 0.5),
                'vy': random.uniform(-0.5, 0.5),
                'surface': False,
            })
        self.state['wave_phase'] = 0.0

    def _draw_surface(self):
        d = self.display
        t = self.time
        dt = 1.0 / 30.0
        surface_y = 28

        # Dark air region above
        for y in range(0, surface_y - 2):
            for x in range(64):
                d.set_pixel(x, y, (3, 3, 8))

        # Water region below with gradient
        for y in range(surface_y + 2, 56):
            depth = (y - surface_y) / 28.0
            blue = int(20 + 40 * depth)
            d.set_pixel(0, y, (2, 2, blue))  # Just set gradient base

        for y in range(surface_y + 2, 56):
            depth = (y - surface_y) / 28.0
            blue = int(20 + 40 * depth)
            for x in range(64):
                d.set_pixel(x, y, (2, 2, blue))

        # Wavy surface line
        self.state['wave_phase'] += dt
        for x in range(64):
            wave = math.sin(t * 1.5 + x * 0.15) * 1.5
            sy = surface_y + int(wave)
            d.set_pixel(x, sy, (40, 80, 180))
            d.set_pixel(x, sy + 1, (30, 60, 140))

        # Jitter molecules
        for mol in self.state['molecules']:
            mol['x'] += mol['vx'] * dt
            mol['y'] += mol['vy'] * dt
            mol['vx'] += random.uniform(-0.5, 0.5) * dt
            mol['vy'] += random.uniform(-0.5, 0.5) * dt
            mol['vx'] *= 0.98
            mol['vy'] *= 0.98
            # Keep surface molecules near surface
            if mol['surface']:
                mol['y'] = surface_y + (mol['y'] - surface_y) * 0.95
                mol['x'] = max(2, min(62, mol['x']))
            else:
                mol['y'] = max(34, min(52, mol['y']))
                mol['x'] = max(2, min(62, mol['x']))

        # Draw molecules as "Mickey Mouse" shapes (O=red, 2H=white)
        for mol in self.state['molecules']:
            mx, my = int(mol['x']), int(mol['y'])
            # Oxygen (red center)
            d.set_pixel(mx, my, (200, 50, 50))
            # Hydrogen atoms (white, offset at ~104.5 degree angle)
            h_angle = t * 0.5 + mol['x'] * 0.1  # Slight rotation
            d.set_pixel(mx - 1, my - 1, (220, 220, 220))
            d.set_pixel(mx + 1, my - 1, (220, 220, 220))

        # H-bonds between nearby surface molecules (dim dotted lines)
        surface_mols = [m for m in self.state['molecules'] if m['surface']]
        bond_color = (25, 50, 100)
        for i in range(len(surface_mols) - 1):
            m1 = surface_mols[i]
            m2 = surface_mols[i + 1]
            x1, y1 = int(m1['x']), int(m1['y'])
            x2, y2 = int(m2['x']), int(m2['y'])
            dist = abs(x2 - x1)
            if dist < 10:
                # Dotted line between
                for step in range(0, dist, 2):
                    bx = x1 + int(step * (x2 - x1) / max(dist, 1))
                    by = y1 + int(step * (y2 - y1) / max(dist, 1))
                    d.set_pixel(bx, by, bond_color)

    # ===================================================================
    # 11. DIATOMS
    # ===================================================================
    def _setup_diatoms(self):
        self.particles = []
        for _ in range(4):
            n_spokes = random.choice([6, 8, 10, 12])
            self.particles.append({
                'x': random.uniform(12, 52),
                'y': random.uniform(10, 42),
                'vx': random.uniform(-0.3, 0.3),
                'vy': random.uniform(-0.3, 0.3),
                'r': random.choice([7, 8, 9, 10]),
                'n_spokes': n_spokes,
                'rot': random.uniform(0, math.pi * 2),
                'rot_speed': random.uniform(0.1, 0.3),
                'phase': random.uniform(0, math.pi * 2),
            })

    def _draw_diatoms(self):
        d = self.display
        t = self.time
        dt = 1.0 / 30.0

        # Gentle Brownian drift
        self._brownian_jitter(0.15)
        for p in self.particles:
            p['vx'] *= 0.97
            p['vy'] *= 0.97
        self._drift_particles(dt, wrap=False)
        for p in self.particles:
            p['x'] = max(12, min(52, p['x']))
            p['y'] = max(10, min(44, p['y']))

        # Draw each diatom
        for p in self.particles:
            cx, cy = int(p['x']), int(p['y'])
            r = p['r']
            p['rot'] += p['rot_speed'] * dt

            # Pulsing brightness
            pulse = 0.7 + 0.3 * math.sin(t * 1.5 + p['phase'])
            base_r = int(160 * pulse)
            base_g = int(130 * pulse)
            base_b = int(40 * pulse)
            body_color = (base_r, base_g, base_b)
            spoke_color = (min(255, base_r + 40), min(255, base_g + 30),
                           min(255, base_b + 20))

            # Outer ring
            d.draw_circle(cx, cy, r, body_color, filled=False)

            # Inner filled circle (smaller)
            inner_r = max(2, r - 3)
            d.draw_circle(cx, cy, inner_r, (base_r // 2, base_g // 2, base_b // 2), filled=True)

            # Center dot
            d.set_pixel(cx, cy, spoke_color)

            # Radial spokes
            for i in range(p['n_spokes']):
                angle = p['rot'] + i * (2 * math.pi / p['n_spokes'])
                for ri in range(inner_r, r + 1):
                    sx = cx + int(ri * math.cos(angle))
                    sy = cy + int(ri * math.sin(angle))
                    d.set_pixel(sx, sy, spoke_color)

            # Concentric ring patterns between inner and outer
            mid_r = (inner_r + r) // 2
            if mid_r > inner_r:
                ring_c = (base_r * 3 // 4, base_g * 3 // 4, base_b * 3 // 4)
                d.draw_circle(cx, cy, mid_r, ring_c, filled=False)
