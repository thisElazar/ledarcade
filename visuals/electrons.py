"""
Electrons - Dynamic Electron Behavior
======================================
What electrons *do*: physics experiments, energy transitions, chemical
reactions, quantum phenomena, and semiconductor devices.  Each scene is
a self-contained looping animation with moving electron/photon particles
on simple geometric backdrops.

Controls:
  Up/Down    - Cycle through groups
  Left/Right - Browse scenes in current group
  Both btns  - Pause / resume animation
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE

DISP_W = 64
DISP_H = 64

# ── Palette ────────────────────────────────────────────────────────────

E_COL      = (180, 220, 255)    # electron: pale cyan
PHOTON     = (255, 220, 80)     # photon: warm gold
UV_PHOTON  = (160, 80, 255)     # UV photon: violet
RED_PHOTON = (255, 60, 40)      # sub-threshold photon: red
NUC        = (255, 120, 60)     # nucleus dot
METAL      = (100, 110, 130)    # metal surface
LEVEL      = (50, 55, 80)       # energy level line
BARRIER    = (100, 70, 40)      # tunnel barrier
VALENCE    = (30, 50, 130)      # valence band
CONDUCT    = (50, 180, 200)     # conduction band
HOLE       = (255, 90, 160)     # semiconductor hole
POS_ION    = (255, 160, 60)     # cation
NEG_ION    = (80, 160, 255)     # anion
PLATE_COL  = (140, 140, 100)    # electrode plate
WIRE_COL   = (70, 70, 55)       # wire/connection
FIELD_COL  = (60, 50, 80)       # field region
ATOM_RING  = (80, 100, 80)      # neutral atom ring
ANTINU     = (160, 120, 200)    # antineutrino
POSITRON   = (255, 140, 180)    # positron


def _wl_color(nm):
    """Wavelength (nm) -> approximate visible RGB."""
    if nm < 400:  return (140, 40, 200)
    if nm < 450:  return (80, 40, 255)
    if nm < 490:  return (0, 120, 255)
    if nm < 520:  return (0, 210, 120)
    if nm < 565:  return (120, 255, 0)
    if nm < 595:  return (255, 255, 0)
    if nm < 640:  return (255, 160, 0)
    if nm < 700:  return (255, 40, 0)
    return (160, 0, 0)


def _col_alpha(c, a):
    """Apply alpha (0-1) to color tuple."""
    a = max(0.0, min(1.0, a))
    return (int(c[0] * a), int(c[1] * a), int(c[2] * a))


def _lerp(a, b, t):
    return a + (b - a) * max(0.0, min(1.0, t))


def _draw_circle(disp, cx, cy, r, color, filled=False):
    """Draw small circle on 64x64 display."""
    ri = int(r)
    r2 = r * r
    for dy in range(-ri, ri + 1):
        for dx in range(-ri, ri + 1):
            d2 = dx * dx + dy * dy
            px, py = int(cx) + dx, int(cy) + dy
            if 0 <= px < DISP_W and 0 <= py < DISP_H:
                if filled and d2 <= r2:
                    disp.set_pixel(px, py, color)
                elif not filled and abs(d2 - r2) <= r + 0.5:
                    disp.set_pixel(px, py, color)


def _safe_pixel(disp, x, y, color):
    """Set pixel with bounds checking."""
    ix, iy = int(x), int(y)
    if 0 <= ix < DISP_W and 0 <= iy < DISP_H:
        disp.set_pixel(ix, iy, color)


# ── Groups ─────────────────────────────────────────────────────────────

GROUPS = [
    ('physics',     'PHYSICS',        (180, 220, 255)),
    ('transitions', 'TRANSITIONS',    (255, 200, 80)),
    ('chemistry',   'CHEMISTRY',      (100, 255, 160)),
    ('quantum',     'QUANTUM',        (200, 140, 255)),
    ('semicond',    'SEMICONDUCTOR',  (255, 140, 180)),
]

# ── Scenes ─────────────────────────────────────────────────────────────

SCENES = [
    # ── Physics ────────────────────────────────────────────────────
    {'name': 'PHOTOELECTRIC', 'desc': 'UV KNOCKS E FREE',
     'groups': ['physics'], 'type': 'photoelectric', 'detail': 'hf > WORK FN'},
    {'name': 'CATHODE RAY', 'desc': 'ELECTRON BEAM',
     'groups': ['physics'], 'type': 'cathode_ray', 'detail': 'J.J. THOMSON'},
    {'name': 'DOUBLE SLIT', 'desc': 'INTERFERENCE',
     'groups': ['physics'], 'type': 'double_slit', 'detail': 'WAVE-PARTICLE'},
    {'name': 'BETA DECAY', 'desc': 'N EMITS E + NU',
     'groups': ['physics'], 'type': 'beta_decay', 'detail': 'WEAK FORCE'},
    {'name': 'SEM DETECTOR', 'desc': 'SECONDARY E',
     'groups': ['physics'], 'type': 'sem_detector', 'detail': 'EVERHART-THORNLEY'},

    # ── Transitions ────────────────────────────────────────────────
    # Hydrogen: levels are true n, spacing derived from -13.6/n² eV
    {'name': 'H BALMER', 'desc': 'VISIBLE SERIES',
     'groups': ['transitions'], 'type': 'emission',
     'levels': [1, 2, 3, 4, 5],
     'transitions': [(3, 2, 656), (4, 2, 486), (5, 2, 434)],
     'detail': 'N>2 TO N=2'},
    {'name': 'H LYMAN', 'desc': 'UV SERIES',
     'groups': ['transitions'], 'type': 'emission',
     'levels': [1, 2, 3, 4],
     'transitions': [(2, 1, 122), (3, 1, 103), (4, 1, 97)],
     'detail': 'N>1 TO N=1'},
    {'name': 'H ABSORB', 'desc': 'PHOTON ABSORBED',
     'groups': ['transitions'], 'type': 'absorption',
     'levels': [1, 2, 3, 4],
     'transitions': [(1, 3, 103), (1, 2, 122), (2, 4, 486)],
     'detail': 'E JUMPS UP'},
    # Na: actual term levels (3S, 3P, 4S), custom energies (eV above ground)
    {'name': 'NA YELLOW', 'desc': 'SODIUM D LINE',
     'groups': ['transitions'], 'type': 'emission',
     'levels': [1, 2, 3],
     'level_labels': ['3S', '3P', '4S'],
     'level_energies': [0.0, 2.10, 3.19],
     'transitions': [(2, 1, 589)],
     'detail': '589 NM'},
    # Neon: excited config levels, big gap to ground
    {'name': 'NEON GLOW', 'desc': 'NOBLE GAS LINES',
     'groups': ['transitions'], 'type': 'emission',
     'levels': [1, 2, 3, 4, 5],
     'level_labels': ['GND', '3S', '3P', '4S', '4P'],
     'level_energies': [0.0, 16.6, 18.4, 19.7, 20.0],
     'transitions': [(3, 2, 640), (4, 3, 585), (5, 4, 540)],
     'detail': 'NEON SIGN'},

    # ── Chemistry ──────────────────────────────────────────────────
    {'name': 'NA + CL', 'desc': 'IONIC BOND',
     'groups': ['chemistry'], 'type': 'transfer',
     'donor': 'Na', 'acceptor': 'Cl', 'e_count': 1,
     'donor_inner': 2, 'acceptor_inner': 2,
     'detail': 'NACL'},
    {'name': 'MG + O', 'desc': '2E TRANSFER',
     'groups': ['chemistry'], 'type': 'transfer',
     'donor': 'Mg', 'acceptor': 'O', 'e_count': 2,
     'donor_inner': 2, 'acceptor_inner': 2,
     'detail': 'MGO'},

    # ── Quantum ────────────────────────────────────────────────────
    {'name': 'TUNNELING', 'desc': 'THROUGH BARRIER',
     'groups': ['quantum'], 'type': 'tunneling',
     'detail': 'PSI LEAKS'},

    # ── Semiconductor ──────────────────────────────────────────────
    {'name': 'BAND GAP', 'desc': 'SI 1.1 EV',
     'groups': ['semicond'], 'type': 'band',
     'gap_px': 10, 'material': 'SILICON',
     'detail': '1.1 EV'},
    {'name': 'N DOPING', 'desc': 'DONOR LEVEL',
     'groups': ['semicond'], 'type': 'doping_n',
     'detail': 'PHOSPHORUS'},
    {'name': 'P DOPING', 'desc': 'ACCEPTOR LEVEL',
     'groups': ['semicond'], 'type': 'doping_p',
     'detail': 'BORON'},
    {'name': 'P-N JUNCTION', 'desc': 'DIODE',
     'groups': ['semicond'], 'type': 'pn_junction',
     'detail': 'FORWARD BIAS'},
    {'name': 'LED', 'desc': 'LIGHT EMISSION',
     'groups': ['semicond'], 'type': 'led_emit',
     'detail': 'E TO PHOTON'},
    {'name': 'SOLAR CELL', 'desc': 'PHOTON TO E',
     'groups': ['semicond'], 'type': 'solar',
     'detail': 'PHOTOVOLTAIC'},
]


def _build_group_indices():
    groups = {}
    for i, sc in enumerate(SCENES):
        for g in sc['groups']:
            groups.setdefault(g, []).append(i)
    return groups


# ── Energy level helpers ───────────────────────────────────────────────

def _level_y(n, levels, level_energies=None):
    """Map level index to screen y position.

    If *level_energies* is provided (list matching *levels*), use those
    for spacing.  Otherwise use hydrogen -1/n² spacing.
    """
    if level_energies:
        e_map = {lv: e for lv, e in zip(levels, level_energies)}
    else:
        # Hydrogen-like: E ∝ -1/n²
        e_map = {lv: -1.0 / (lv * lv) for lv in levels}
    e_min = min(e_map.values())
    e_max = max(e_map.values())
    if abs(e_max - e_min) < 1e-12:
        return 30
    frac = (e_map[n] - e_min) / (e_max - e_min)
    return int(52 - frac * 44)


# ── Electrons visual class ─────────────────────────────────────────────

class Electrons(Visual):
    name = "ELECTRONS"
    description = "What electrons do: experiments, transitions, reactions"
    category = "science_micro"

    _saved_group_idx = None
    _saved_scene_pos = None

    def reset(self):
        self.time = 0.0
        self.scene_time = 0.0
        self.group_indices = _build_group_indices()

        if Electrons._saved_group_idx is not None:
            self.group_idx = Electrons._saved_group_idx
            self.scene_pos = Electrons._saved_scene_pos
        else:
            self.group_idx = 0
            self.scene_pos = 0

        self.paused = False
        self.overlay_timer = 2.5
        self.label_timer = 0.0
        self._pause_timer = 0.0
        self._prev_up = False
        self._prev_down = False
        self._prev_left = False
        self._prev_right = False

        # Particle pool: [x, y, vx, vy, (r,g,b), born, lifetime]
        self.particles = []
        self._hit_pattern = []       # double-slit accumulation
        self._ds_cdf = []            # double-slit interference CDF
        self._ds_total = 0.0
        self._sem_image = []         # SEM image buffer
        self._sem_scan_x = 0.0

        self._prepare_scene()

    def _current_scene_list(self):
        key = GROUPS[self.group_idx][0]
        return self.group_indices.get(key, [])

    def _current_scene(self):
        sl = self._current_scene_list()
        if not sl:
            return SCENES[0]
        return SCENES[sl[self.scene_pos % len(sl)]]

    def _prepare_scene(self):
        """Reset scene-specific state."""
        self.scene_time = 0.0
        self.particles = []
        self.label_timer = 0.0
        self._hit_pattern = []
        self._ds_cdf = []
        self._ds_total = 0.0
        self._sem_image = []
        self._sem_scan_x = 0.0
        sc = self._current_scene()

        if sc['type'] == 'double_slit':
            self._hit_pattern = [0] * DISP_H
            # Precompute two-slit interference pattern
            slit1_y, slit2_y = 26.0, 38.0
            L = 36.0          # wall-to-screen distance in pixels
            wl = 2.7           # effective wavelength for ~5 visible fringes
            slit_w = 3.0       # slit width
            intensities = []
            for y in range(DISP_H):
                dy = y - 32.0
                # Two-slit cos² envelope
                phase = math.pi * (slit2_y - slit1_y) * dy / (wl * L)
                I = math.cos(phase) ** 2
                # Single-slit sinc² diffraction envelope
                beta = math.pi * slit_w * dy / (wl * L)
                if abs(beta) > 0.001:
                    I *= (math.sin(beta) / beta) ** 2
                intensities.append(max(I, 0.002))
            # Build CDF for rejection-free sampling
            self._ds_cdf = []
            running = 0.0
            for I in intensities:
                running += I
                self._ds_cdf.append(running)
            self._ds_total = running

        elif sc['type'] == 'sem_detector':
            self._sem_image = [0] * DISP_W
            self._sem_scan_x = 4.0

        Electrons._saved_group_idx = self.group_idx
        Electrons._saved_scene_pos = self.scene_pos

    def handle_input(self, input_state) -> bool:
        consumed = False
        up_edge = input_state.up and not self._prev_up
        down_edge = input_state.down and not self._prev_down
        left_edge = input_state.left and not self._prev_left
        right_edge = input_state.right and not self._prev_right

        if up_edge:
            self.group_idx = (self.group_idx - 1) % len(GROUPS)
            self.scene_pos = 0
            self.overlay_timer = 2.5
            self._prepare_scene()
            consumed = True
        elif down_edge:
            self.group_idx = (self.group_idx + 1) % len(GROUPS)
            self.scene_pos = 0
            self.overlay_timer = 2.5
            self._prepare_scene()
            consumed = True

        if left_edge:
            sl = self._current_scene_list()
            if sl:
                self.scene_pos = (self.scene_pos - 1) % len(sl)
            self._prepare_scene()
            consumed = True
        elif right_edge:
            sl = self._current_scene_list()
            if sl:
                self.scene_pos = (self.scene_pos + 1) % len(sl)
            self._prepare_scene()
            consumed = True

        action = input_state.action_l or input_state.action_r
        if action:
            self.paused = not self.paused
            self._pause_timer = 1.5
            consumed = True

        self._prev_up = input_state.up
        self._prev_down = input_state.down
        self._prev_left = input_state.left
        self._prev_right = input_state.right
        return consumed

    def update(self, dt: float):
        self.time += dt
        self.label_timer += dt

        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)
        if self._pause_timer > 0:
            self._pause_timer = max(0.0, self._pause_timer - dt)

        if self.paused:
            return

        self.scene_time += dt

        # Update particles: basic physics
        alive = []
        for p in self.particles:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            age = self.scene_time - p[5]
            if age < p[6] and -20 < p[0] < DISP_W + 20 and -20 < p[1] < DISP_H + 20:
                alive.append(p)
        self.particles = alive

        # Scene-specific spawning / physics
        sc = self._current_scene()
        stype = sc['type']

        if stype == 'photoelectric':
            self._update_photoelectric(dt)
        elif stype == 'cathode_ray':
            self._update_cathode_ray(dt)
        elif stype == 'double_slit':
            self._update_double_slit(dt)
        elif stype == 'sem_detector':
            self._update_sem(dt)

    def draw(self):
        self.display.clear(Colors.BLACK)
        sc = self._current_scene()
        stype = sc['type']

        # Dispatch to scene-type renderer
        if stype == 'photoelectric':
            self._draw_photoelectric(sc)
        elif stype == 'cathode_ray':
            self._draw_cathode_ray(sc)
        elif stype == 'double_slit':
            self._draw_double_slit(sc)
        elif stype == 'beta_decay':
            self._draw_beta_decay(sc)
        elif stype == 'sem_detector':
            self._draw_sem(sc)
        elif stype == 'emission':
            self._draw_emission(sc)
        elif stype == 'absorption':
            self._draw_absorption(sc)
        elif stype == 'transfer':
            self._draw_transfer(sc)
        elif stype == 'tunneling':
            self._draw_tunneling(sc)
        elif stype == 'band':
            self._draw_band(sc)
        elif stype == 'doping_n':
            self._draw_doping_n(sc)
        elif stype == 'doping_p':
            self._draw_doping_p(sc)
        elif stype == 'pn_junction':
            self._draw_pn_junction(sc)
        elif stype == 'led_emit':
            self._draw_led_emit(sc)
        elif stype == 'solar':
            self._draw_solar(sc)

        # Draw particles on top
        self._draw_particles()

        # Labels
        self._draw_labels(sc)

        # Group overlay
        if self.overlay_timer > 0:
            _, gname, gcol = GROUPS[self.group_idx]
            alpha = min(1.0, self.overlay_timer / 0.5)
            self.display.draw_text_small(2, 2, gname, _col_alpha(gcol, alpha))

        # Pause indicator
        if self._pause_timer > 0:
            alpha = min(1.0, self._pause_timer / 0.4)
            lbl = 'PAUSED' if self.paused else 'PLAY'
            col = _col_alpha((200, 200, 200), alpha)
            self.display.draw_text_small(DISP_W - len(lbl) * 4 - 1, 2, lbl, col)

    def _draw_particles(self):
        """Draw all particles as single bright pixels."""
        for p in self.particles:
            x, y = int(p[0]), int(p[1])
            if 0 <= x < DISP_W and 0 <= y < DISP_H:
                age = self.scene_time - p[5]
                remaining = p[6] - age
                alpha = 1.0
                if age < 0.1:
                    alpha = age / 0.1
                if remaining < 0.3:
                    alpha = min(alpha, remaining / 0.3)
                self.display.set_pixel(x, y, _col_alpha(p[4], alpha))

    def _draw_labels(self, sc):
        """Cycling labels at bottom: name -> desc -> detail."""
        phase = int(self.label_timer / 5.0) % 3
        y = 58
        if phase == 0:
            self.display.draw_text_small(2, y, sc['name'], Colors.WHITE)
        elif phase == 1:
            self.display.draw_text_small(2, y, sc['desc'], (200, 200, 200))
        else:
            detail = sc.get('detail', '')
            if detail:
                self.display.draw_text_small(2, y, detail, (160, 160, 220))

    # ══════════════════════════════════════════════════════════════
    #  PHYSICS scenes
    # ══════════════════════════════════════════════════════════════

    # ── Photoelectric: threshold behaviour ─────────────────────────

    def _update_photoelectric(self, dt):
        """Alternate sub-threshold (red) and above-threshold (UV) photons.
        Only UV photons eject electrons — the key insight."""
        t = self.scene_time
        if int(t / 0.35) > int((t - dt) / 0.35):
            x = random.randint(8, 56)
            idx = int(t / 0.35)
            if idx % 3 == 0:
                # Red/IR photon — below work-function threshold
                self.particles.append(
                    [float(x), 0.0, 0.0, 30.0, RED_PHOTON, t, 2.5])
            else:
                # UV photon — above threshold
                self.particles.append(
                    [float(x), 0.0, 0.0, 30.0, UV_PHOTON, t, 2.5])

        for p in list(self.particles):
            if p[1] >= 46 and p[4] != E_COL:
                if p[4] == UV_PHOTON:
                    # UV ejects electron with KE = hf - work fn
                    ex = p[0] + random.uniform(-2, 2)
                    self.particles.append(
                        [ex, 46.0, random.uniform(-5, 5),
                         random.uniform(-35, -15), E_COL, self.scene_time, 2.0])
                    p[6] = 0  # photon absorbed
                elif p[4] == RED_PHOTON:
                    # Sub-threshold: photon reflects, no ejection
                    p[3] = -abs(p[3]) * 0.4
                    p[2] = random.uniform(-12, 12)
                    p[5] = self.scene_time
                    p[6] = 0.8
                    p[4] = _col_alpha(RED_PHOTON, 0.5)

    def _draw_photoelectric(self, sc):
        d = self.display
        # Metal surface
        for x in range(4, 60):
            for y in range(47, 52):
                d.set_pixel(x, y, METAL)
        d.draw_text_small(2, 52, 'METAL', (80, 80, 90))
        # Threshold annotation
        t = self.scene_time
        a = 0.4 + 0.2 * math.sin(t * 2)
        d.draw_text_small(2, 8, 'UV', _col_alpha(UV_PHOTON, a))
        d.draw_text_small(16, 8, 'YES', _col_alpha((100, 255, 100), a))
        d.draw_text_small(2, 14, 'RED', _col_alpha(RED_PHOTON, a))
        d.draw_text_small(16, 14, 'NO', _col_alpha((255, 80, 80), a))

    # ── Cathode ray: field-based deflection ────────────────────────

    def _update_cathode_ray(self, dt):
        """Electrons enter straight; E field between plates deflects them."""
        t = self.scene_time
        if int(t / 0.12) > int((t - dt) / 0.12):
            # Spawn electron going straight right, vy = 0
            self.particles.append(
                [6.0, 32.0, 40.0, 0.0, E_COL, t, 1.8])
        # Apply oscillating E field to electrons between the plates
        field = math.sin(t * 1.5) * 120.0
        for p in self.particles:
            if p[4] == E_COL and 18.0 <= p[0] <= 42.0:
                p[3] += field * dt  # accelerate vy while between plates

    def _draw_cathode_ray(self, sc):
        d = self.display
        # Gun
        d.draw_rect(1, 28, 5, 8, (60, 70, 80))
        d.draw_rect(2, 30, 3, 4, E_COL)
        # Deflection plates
        for x in range(18, 42):
            d.set_pixel(x, 16, PLATE_COL)
            d.set_pixel(x, 17, PLATE_COL)
            d.set_pixel(x, 46, PLATE_COL)
            d.set_pixel(x, 47, PLATE_COL)
        d.draw_text_small(18, 12, '+', (200, 100, 100))
        d.draw_text_small(18, 49, '-', (100, 100, 200))
        # Phosphor screen
        for y in range(8, 56):
            d.set_pixel(60, y, (20, 40, 20))
            d.set_pixel(61, y, (20, 40, 20))
        # Glow dot where beam currently hits
        t = self.scene_time
        gy = int(32 + math.sin(t * 1.5) * 12)
        _draw_circle(d, 61, gy, 2, (100, 255, 100), filled=True)

    # ── Double slit: proper interference fringes ───────────────────

    def _update_double_slit(self, dt):
        """Fire electrons one at a time; hits sampled from interference CDF."""
        t = self.scene_time
        if int(t / 0.15) > int((t - dt) / 0.15):
            self.particles.append(
                [2.0, 32.0, 50.0, 0.0, E_COL, t, 0.6])

        if not self._ds_cdf:
            return
        for p in list(self.particles):
            if p[4] == E_COL and p[0] >= 23:
                # Sample hit y from interference pattern
                r = random.random() * self._ds_total
                lo, hi = 0, len(self._ds_cdf) - 1
                while lo < hi:
                    mid = (lo + hi) >> 1
                    if self._ds_cdf[mid] < r:
                        lo = mid + 1
                    else:
                        hi = mid
                iy = lo
                if 0 <= iy < DISP_H:
                    self._hit_pattern[iy] = min(255,
                        self._hit_pattern[iy] + 2)
                p[6] = 0

    def _draw_double_slit(self, sc):
        d = self.display
        slit_y = [26, 38]
        for y in range(8, 56):
            is_slit = any(abs(y - sy) < 3 for sy in slit_y)
            if not is_slit:
                d.set_pixel(24, y, METAL)
                d.set_pixel(25, y, METAL)
        # Accumulated interference pattern on detection screen
        for y in range(DISP_H):
            v = self._hit_pattern[y] if y < len(self._hit_pattern) else 0
            if v > 0:
                bright = min(255, v)
                d.set_pixel(60, y, (bright, bright, bright))
                d.set_pixel(61, y, (bright // 2, bright // 2, bright))
        _draw_circle(d, 3, 32, 2, (60, 70, 80), filled=True)

    # ── Beta decay ─────────────────────────────────────────────────

    def _draw_beta_decay(self, sc):
        d = self.display
        t = self.scene_time
        cycle = t % 4.0

        if cycle < 1.5:
            wobble = math.sin(cycle * 6) * 0.5
            _draw_circle(d, int(24 + wobble), 32, 5,
                         (120, 120, 140), filled=True)
            d.draw_text_small(20, 30, 'N', (200, 200, 220))
        elif cycle < 1.8:
            _draw_circle(d, 24, 32, 6, (200, 200, 255), filled=True)
        else:
            frac = (cycle - 1.8) / 2.2
            _draw_circle(d, 22, 32, 4, NUC, filled=True)
            d.draw_text_small(18, 30, 'P', (255, 200, 180))
            # Electron
            ex = int(26 + frac * 30)
            ey = int(32 - frac * 15)
            _draw_circle(d, ex, ey, 1, E_COL, filled=True)
            # Antineutrino
            nx = int(26 + frac * 25)
            ny = int(32 + frac * 12)
            _safe_pixel(d, nx, ny, ANTINU)
            if frac > 0.15:
                a = min(1.0, frac * 2)
                d.draw_text_small(min(ex + 2, 50), ey - 4, 'E-',
                                  _col_alpha(E_COL, a))
                d.draw_text_small(min(nx + 2, 46), ny + 2, 'VE',
                                  _col_alpha(ANTINU, a))

    # ── SEM secondary electron detector ────────────────────────────

    def _update_sem(self, dt):
        """Primary beam scans sample; secondary electrons spray to detector."""
        t = self.scene_time
        # Scan beam across sample surface
        self._sem_scan_x = 4 + ((t * 6) % 52)
        scan_x = self._sem_scan_x

        # Sample topography: sine bumps
        sample_y = self._sem_surface_y(scan_x)

        # Spawn secondary electrons from impact point
        if int(t / 0.08) > int((t - dt) / 0.08):
            # SE yield depends on surface slope (more SE from edges)
            slope = abs(self._sem_surface_y(scan_x + 1) -
                        self._sem_surface_y(scan_x - 1))
            n_se = 1 + int(slope * 2)
            for _ in range(n_se):
                angle = random.uniform(-math.pi * 0.8, -0.2)
                speed = random.uniform(10, 25)
                self.particles.append([
                    scan_x, float(sample_y) - 1,
                    math.cos(angle) * speed + 8,   # bias toward detector
                    math.sin(angle) * speed,
                    E_COL, t, 1.2])

        # Attract SEs toward detector (+200V bias)
        det_x, det_y = 56.0, 16.0
        for p in self.particles:
            if p[4] == E_COL:
                dx = det_x - p[0]
                dy = det_y - p[1]
                dist = max(3.0, math.sqrt(dx * dx + dy * dy))
                force = 40.0 / dist
                p[2] += (dx / dist) * force * dt
                p[3] += (dy / dist) * force * dt

        # Record SEM signal: count SEs arriving at detector
        ix = int(scan_x)
        for p in list(self.particles):
            if p[4] == E_COL and abs(p[0] - det_x) < 4 and abs(p[1] - det_y) < 6:
                if 0 <= ix < DISP_W:
                    self._sem_image[ix] = min(255,
                        self._sem_image[ix] + 25)
                p[6] = 0

    def _sem_surface_y(self, x):
        """Sample topography: bumps and ridges."""
        return 42 + int(3.0 * math.sin(x * 0.25) +
                        1.5 * math.sin(x * 0.6 + 1.0))

    def _draw_sem(self, sc):
        d = self.display
        t = self.scene_time
        scan_x = self._sem_scan_x

        # Sample surface with topography
        for x in range(4, 58):
            sy = self._sem_surface_y(x)
            for y in range(sy, 54):
                d.set_pixel(x, y, (60, 60, 70))
            d.set_pixel(x, sy, (90, 90, 100))

        # Primary beam from top to sample
        sy = self._sem_surface_y(scan_x)
        ix = int(scan_x)
        for y in range(2, sy):
            _safe_pixel(d, ix, y, _col_alpha((100, 255, 100), 0.4))
        # Impact point glow
        _draw_circle(d, ix, sy, 1, (200, 255, 200), filled=True)

        # Interaction volume (teardrop faintly inside sample)
        for dy in range(1, 6):
            spread = max(1, dy - 1)
            for ddx in range(-spread, spread + 1):
                a = 0.15 * (1.0 - dy / 6.0)
                _safe_pixel(d, ix + ddx, sy + dy, _col_alpha((100, 200, 100), a))

        # ET detector (box with grid)
        d.draw_rect(52, 10, 8, 12, (80, 80, 40), filled=False)
        d.draw_text_small(53, 6, '+', (200, 160, 60))
        # Collection grid (dashed)
        for y in range(11, 21, 2):
            d.set_pixel(51, y, (120, 120, 60))
        # Scintillator glow when SEs arrive
        n_near = sum(1 for p in self.particles
                     if p[4] == E_COL and abs(p[0] - 56) < 6
                     and abs(p[1] - 16) < 8)
        if n_near > 0:
            glow = min(1.0, n_near * 0.3)
            d.draw_rect(53, 11, 6, 10,
                        _col_alpha((200, 255, 100), glow))

        # SEM image buildup at bottom
        for x in range(DISP_W):
            v = self._sem_image[x] if x < len(self._sem_image) else 0
            if v > 0:
                b = min(255, v)
                d.set_pixel(x, 56, (b, b, b))
                d.set_pixel(x, 57, (b // 2, b // 2, b // 2))

        # Electron gun label
        d.draw_text_small(2, 2, 'E-GUN', (100, 200, 100))

    # ══════════════════════════════════════════════════════════════
    #  TRANSITION scenes
    # ══════════════════════════════════════════════════════════════

    def _draw_energy_levels(self, levels, x0=4, x1=30,
                            level_energies=None, level_labels=None):
        """Draw horizontal energy level lines with labels."""
        d = self.display
        for i, n in enumerate(levels):
            y = _level_y(n, levels, level_energies)
            for x in range(x0, x1):
                d.set_pixel(x, y, LEVEL)
            if level_labels and i < len(level_labels):
                lbl = level_labels[i]
            else:
                lbl = 'N=%d' % n
            d.draw_text_small(x1 + 1, y - 2, lbl,
                              _col_alpha(LEVEL, 1.5))

    def _draw_emission(self, sc):
        d = self.display
        levels = sc.get('levels', [1, 2, 3])
        transitions = sc.get('transitions', [])
        energies = sc.get('level_energies')
        labels = sc.get('level_labels')
        if not transitions:
            return

        self._draw_energy_levels(levels, level_energies=energies,
                                 level_labels=labels)

        t = self.scene_time
        cycle_len = 3.0
        idx = int(t / cycle_len) % len(transitions)
        phase = (t % cycle_len) / cycle_len

        n_from, n_to, wl = transitions[idx]
        y_from = _level_y(n_from, levels, energies)
        y_to = _level_y(n_to, levels, energies)
        photon_col = _wl_color(wl)

        if phase < 0.3:
            ey = y_from
        elif phase < 0.5:
            drop_frac = (phase - 0.3) / 0.2
            ey = int(_lerp(y_from, y_to, drop_frac))
        else:
            ey = y_to

        _draw_circle(d, 17, ey, 2, E_COL, filled=True)

        if phase >= 0.5:
            photon_frac = (phase - 0.5) / 0.5
            px = int(_lerp(20, 58, photon_frac))
            py = int(_lerp(y_to, y_to - 5, photon_frac * 0.3))
            wave_y = py + int(math.sin(px * 0.8) * 2)
            _safe_pixel(d, px, wave_y, photon_col)
            _safe_pixel(d, px - 1, wave_y, _col_alpha(photon_col, 0.5))
            _safe_pixel(d, px - 2, wave_y, _col_alpha(photon_col, 0.2))
            d.draw_text_small(42, y_to - 8, '%dNM' % wl,
                              _col_alpha(photon_col, 0.7))

    def _draw_absorption(self, sc):
        d = self.display
        levels = sc.get('levels', [1, 2, 3])
        transitions = sc.get('transitions', [])
        energies = sc.get('level_energies')
        labels = sc.get('level_labels')
        if not transitions:
            return

        self._draw_energy_levels(levels, level_energies=energies,
                                 level_labels=labels)

        t = self.scene_time
        cycle_len = 3.0
        idx = int(t / cycle_len) % len(transitions)
        phase = (t % cycle_len) / cycle_len

        n_from, n_to, wl = transitions[idx]
        y_from = _level_y(n_from, levels, energies)
        y_to = _level_y(n_to, levels, energies)
        photon_col = _wl_color(wl)

        if phase < 0.4:
            pfrac = phase / 0.4
            px = int(_lerp(58, 20, pfrac))
            py = y_from + int(math.sin(px * 0.8) * 2)
            _safe_pixel(d, px, py, photon_col)
            _safe_pixel(d, px + 1, py, _col_alpha(photon_col, 0.5))
            _draw_circle(d, 17, y_from, 2, E_COL, filled=True)
        elif phase < 0.6:
            flash_a = 1.0 - (phase - 0.4) / 0.2
            _draw_circle(d, 17, y_from, 3,
                         _col_alpha(photon_col, flash_a), filled=True)
            jump_frac = (phase - 0.4) / 0.2
            ey = int(_lerp(y_from, y_to, jump_frac))
            _draw_circle(d, 17, ey, 2, E_COL, filled=True)
        else:
            pulse = 0.7 + 0.3 * math.sin(self.scene_time * 8)
            _draw_circle(d, 17, y_to, 2,
                         _col_alpha(E_COL, pulse), filled=True)

    # ══════════════════════════════════════════════════════════════
    #  CHEMISTRY scenes
    # ══════════════════════════════════════════════════════════════

    def _draw_atom(self, cx, cy, radius, nuc_color, ring_color, label,
                   inner_e=0):
        """Draw Bohr atom with optional inner-shell electrons."""
        d = self.display
        _draw_circle(d, cx, cy, radius, ring_color)
        _draw_circle(d, cx, cy, 1, nuc_color, filled=True)
        lx = cx - len(label) * 2
        d.draw_text_small(lx, cy - radius - 6, label,
                          _col_alpha(ring_color, 0.8))
        # Inner shell electrons (dim, tight orbit)
        if inner_e > 0:
            inner_r = max(3, radius // 2)
            _draw_circle(d, cx, cy, inner_r, _col_alpha(ring_color, 0.3))
            for i in range(inner_e):
                angle = self.time * 2.5 + i * (2 * math.pi / inner_e)
                ix = cx + int(inner_r * math.cos(angle))
                iy = cy + int(inner_r * math.sin(angle))
                _safe_pixel(d, ix, iy, _col_alpha(E_COL, 0.4))

    def _draw_transfer(self, sc):
        d = self.display
        t = self.scene_time
        cycle = t % 4.0
        e_count = sc.get('e_count', 1)
        donor = sc.get('donor', 'A')
        acceptor = sc.get('acceptor', 'B')
        d_inner = sc.get('donor_inner', 0)
        a_inner = sc.get('acceptor_inner', 0)

        dx_c, dy_c = 18, 30
        ax_c, ay_c = 46, 30
        r = 8

        if cycle < 1.5:
            self._draw_atom(dx_c, dy_c, r, NUC, ATOM_RING, donor,
                            inner_e=d_inner)
            self._draw_atom(ax_c, ay_c, r, NUC, ATOM_RING, acceptor,
                            inner_e=a_inner)
            for i in range(e_count):
                angle = t * 3.0 + i * math.pi
                ex = dx_c + int(r * math.cos(angle))
                ey = dy_c + int(r * math.sin(angle))
                _safe_pixel(d, ex, ey, E_COL)
        elif cycle < 2.5:
            frac = (cycle - 1.5) / 1.0
            self._draw_atom(dx_c, dy_c, r, NUC,
                            _col_alpha(ATOM_RING, 1.0 - 0.3 * frac), donor,
                            inner_e=d_inner)
            self._draw_atom(ax_c, ay_c, r, NUC,
                            _col_alpha(ATOM_RING, 1.0 - 0.3 * frac), acceptor,
                            inner_e=a_inner)
            for i in range(e_count):
                offset = i * 0.15
                f = max(0.0, min(1.0, (frac - offset) / (1.0 - offset)))
                ex = int(_lerp(dx_c + r, ax_c - r, f))
                ey = int(_lerp(dy_c, ay_c, f) - math.sin(f * math.pi) * 8)
                _draw_circle(d, ex, ey, 1, E_COL, filled=True)
        else:
            frac = (cycle - 2.5) / 1.5
            glow = 0.6 + 0.4 * math.sin(t * 4)
            self._draw_atom(dx_c, dy_c, r, NUC,
                            _col_alpha(POS_ION, glow), donor + '+',
                            inner_e=d_inner)
            self._draw_atom(ax_c, ay_c, r, NUC,
                            _col_alpha(NEG_ION, glow), acceptor + '-',
                            inner_e=a_inner)
            for i in range(e_count):
                angle = t * 3.0 + i * math.pi
                ex = ax_c + int(r * math.cos(angle))
                ey = ay_c + int(r * math.sin(angle))
                _safe_pixel(d, ex, ey, E_COL)
            if frac > 0.3:
                a = min(1.0, (frac - 0.3) * 2)
                for x in range(dx_c + r + 1, ax_c - r):
                    if x % 3 == 0:
                        _safe_pixel(d, x, 30, _col_alpha((200, 200, 100), a))

    # ══════════════════════════════════════════════════════════════
    #  QUANTUM scenes
    # ══════════════════════════════════════════════════════════════

    def _draw_tunneling(self, sc):
        """Wave packet hits barrier; conserves probability: |R|²+|T|²=1."""
        d = self.display
        t = self.scene_time
        cycle = t % 4.0

        bx, bw = 28, 8
        for x in range(bx, bx + bw):
            for y in range(12, 52):
                d.set_pixel(x, y, BARRIER)
        for x in range(4, 60):
            if x < bx or x >= bx + bw:
                d.set_pixel(x, 32, (30, 30, 50))

        # Probability-conserving amplitudes: R²+T²=1
        R_amp = 0.92    # |R|²≈0.85
        T_amp = 0.39    # |T|²≈0.15

        if cycle < 2.0:
            cx = int(_lerp(4, bx - 2, cycle / 2.0))
            for ddx in range(-4, 5):
                amp = math.exp(-ddx * ddx / 4.0)
                px = cx + ddx
                if 0 <= px < DISP_W:
                    wave_y = 32 + int(math.sin(ddx * 1.5 + t * 6) * 3 * amp)
                    _safe_pixel(d, px, wave_y, _col_alpha(E_COL, amp))
                    if amp > 0.5:
                        _safe_pixel(d, px, wave_y - 1,
                                    _col_alpha(E_COL, amp * 0.3))
        elif cycle < 2.5:
            frac = (cycle - 2.0) / 0.5
            _draw_circle(d, bx, 32, 3,
                         _col_alpha(E_COL, 1.0 - frac), filled=True)
        else:
            frac = (cycle - 2.5) / 1.5
            # Reflected
            rx = int(_lerp(bx - 2, 4, frac))
            for ddx in range(-3, 4):
                amp = math.exp(-ddx * ddx / 3.0) * R_amp
                px = rx + ddx
                if 0 <= px < bx:
                    wave_y = 32 + int(math.sin(ddx * 1.5 - t * 6) * 2 * amp)
                    _safe_pixel(d, px, wave_y, _col_alpha(E_COL, amp))
            # Transmitted (smaller)
            tx = int(_lerp(bx + bw + 1, 58, frac))
            for ddx in range(-2, 3):
                amp = math.exp(-ddx * ddx / 2.0) * T_amp
                px = tx + ddx
                if bx + bw <= px < DISP_W:
                    wave_y = 32 + int(math.sin(ddx * 1.5 + t * 6) * 2 * amp)
                    _safe_pixel(d, px, wave_y, _col_alpha(E_COL, amp))

        d.draw_text_small(bx, 8, 'BARRIER', _col_alpha(BARRIER, 0.6))

    # ══════════════════════════════════════════════════════════════
    #  SEMICONDUCTOR scenes
    # ══════════════════════════════════════════════════════════════

    def _draw_band_diagram(self, gap_px, valence_top=46, label=None):
        """Valence band (~full), gap, conduction band (~empty)."""
        d = self.display
        conduct_bottom = valence_top - gap_px
        conduct_top = max(8, conduct_bottom - 12)
        valence_bottom = min(54, valence_top + 12)

        # Valence band: nearly full (~95% fill)
        for y in range(valence_top, valence_bottom):
            for x in range(8, 56):
                noise = random.Random(x * 100 + y).random()
                if noise < 0.95:
                    bright = 0.5 + noise * 0.5
                    d.set_pixel(x, y, _col_alpha(VALENCE, bright))

        # Conduction band: nearly empty (~5% fill at equilibrium)
        for y in range(conduct_top, conduct_bottom):
            for x in range(8, 56):
                noise = random.Random(x * 100 + y + 5000).random()
                if noise < 0.05:
                    bright = 0.3 + noise * 4.0
                    d.set_pixel(x, y, _col_alpha(CONDUCT, bright))

        # Band edges
        for x in range(8, 56):
            d.set_pixel(x, valence_top, _col_alpha(VALENCE, 0.8))
            d.set_pixel(x, conduct_bottom, _col_alpha(CONDUCT, 0.8))

        if label and gap_px > 6:
            mid_y = (valence_top + conduct_bottom) // 2 - 2
            d.draw_text_small(20, mid_y, label, (80, 80, 80))

        return conduct_bottom, valence_top

    def _draw_band(self, sc):
        d = self.display
        gap_px = sc.get('gap_px', 10)
        material = sc.get('material', '')
        t = self.scene_time

        conduct_bot, valence_top = self._draw_band_diagram(
            gap_px, label=sc.get('detail', ''))

        if gap_px < 20:
            cycle = t % 3.0
            if 0.8 <= cycle < 1.2:
                frac = (cycle - 0.8) / 0.4
                ey = int(_lerp(valence_top, conduct_bot, frac))
                _draw_circle(d, 32, ey, 1, E_COL, filled=True)
                _safe_pixel(d, 32, valence_top, HOLE)
            elif 1.2 <= cycle < 2.5:
                ex = 32 + int(math.sin(t * 3) * 8)
                _draw_circle(d, ex, conduct_bot - 2, 1, E_COL, filled=True)
                hx = 32 - int(math.sin(t * 2.5) * 6)
                _draw_circle(d, hx, valence_top + 2, 1, HOLE, filled=True)

        d.draw_text_small(2, 4, material, (140, 140, 160))

    def _draw_doping_n(self, sc):
        d = self.display
        t = self.scene_time
        conduct_bot, valence_top = self._draw_band_diagram(10)
        donor_y = conduct_bot + 3
        for x in range(12, 52):
            if x % 3 != 0:
                d.set_pixel(x, donor_y, (100, 200, 100))
        for i in range(3):
            cycle = (t * 0.6 + i * 0.33) % 1.0
            x = 18 + i * 12
            if cycle < 0.4:
                _safe_pixel(d, x, donor_y, E_COL)
            else:
                frac = (cycle - 0.4) / 0.6
                ey = int(_lerp(donor_y, conduct_bot - 2, frac))
                _safe_pixel(d, x, ey, E_COL)
        d.draw_text_small(2, 4, 'N-TYPE', (100, 200, 100))
        d.draw_text_small(2, donor_y - 2, 'DONOR', (80, 150, 80))

    def _draw_doping_p(self, sc):
        d = self.display
        t = self.scene_time
        conduct_bot, valence_top = self._draw_band_diagram(10)
        acceptor_y = valence_top - 3
        for x in range(12, 52):
            if x % 3 != 0:
                d.set_pixel(x, acceptor_y, (200, 100, 160))
        for i in range(3):
            cycle = (t * 0.6 + i * 0.33) % 1.0
            x = 18 + i * 12
            if cycle < 0.4:
                _safe_pixel(d, x, valence_top + 2, E_COL)
            elif cycle < 0.7:
                frac = (cycle - 0.4) / 0.3
                ey = int(_lerp(valence_top + 2, acceptor_y, frac))
                _safe_pixel(d, x, ey, E_COL)
            else:
                _safe_pixel(d, x, acceptor_y, E_COL)
                pulse = 0.5 + 0.5 * math.sin(t * 5 + i)
                _safe_pixel(d, x, valence_top + 2,
                            _col_alpha(HOLE, pulse))
        d.draw_text_small(2, 4, 'P-TYPE', (200, 100, 160))
        d.draw_text_small(2, acceptor_y - 2, 'ACCEPT', (160, 80, 130))

    def _draw_pn_junction(self, sc):
        d = self.display
        t = self.scene_time
        for y in range(12, 52):
            for x in range(4, 28):
                d.set_pixel(x, y, (15, 20, 35))
        for y in range(12, 52):
            for x in range(36, 60):
                d.set_pixel(x, y, (25, 15, 25))
        for y in range(12, 52):
            for x in range(28, 36):
                d.set_pixel(x, y, (8, 8, 12))
        d.draw_text_small(2, 8, 'N', (100, 160, 220))
        d.draw_text_small(56, 8, 'P', (220, 100, 160))
        d.draw_text_small(24, 8, 'PN', (120, 120, 120))
        for i in range(8):
            phase = (t * 0.4 + i * 0.12) % 1.0
            ex = int(_lerp(6, 58, phase))
            ey = 24 + (i % 4) * 7
            if ex < 28 or ex > 36:
                _safe_pixel(d, ex, ey, E_COL)
            elif 0.4 < phase < 0.65:
                _safe_pixel(d, ex, ey, _col_alpha(E_COL, 0.6))
        for i in range(6):
            phase = (t * 0.35 + i * 0.16) % 1.0
            hx = int(_lerp(58, 6, phase))
            hy = 28 + (i % 3) * 8
            if hx > 36 or hx < 28:
                _safe_pixel(d, hx, hy, HOLE)

    def _draw_led_emit(self, sc):
        d = self.display
        t = self.scene_time
        cycle = t % 3.0
        for x in range(4, 30):
            d.set_pixel(x, 24, CONDUCT)
            d.set_pixel(x, 36, VALENCE)
        for x in range(34, 60):
            d.set_pixel(x, 30, CONDUCT)
            d.set_pixel(x, 42, VALENCE)
        d.draw_line(30, 24, 34, 30, (60, 60, 80))
        d.draw_line(30, 36, 34, 42, (60, 60, 80))

        if cycle < 1.0:
            ex = int(_lerp(8, 30, cycle))
            _draw_circle(d, ex, 22, 1, E_COL, filled=True)
            _draw_circle(d, 46, 44, 1, HOLE, filled=True)
        elif cycle < 1.5:
            frac = (cycle - 1.0) / 0.5
            ex = int(_lerp(30, 40, frac))
            ey = int(_lerp(22, 42, frac))
            _draw_circle(d, ex, ey, 1, E_COL, filled=True)
            _draw_circle(d, 46, 44, 1, HOLE, filled=True)
        elif cycle < 1.8:
            frac = (cycle - 1.5) / 0.3
            _draw_circle(d, 42, 42, int(3 + frac * 3),
                         _col_alpha((200, 255, 100), 1.0 - frac), filled=True)
        else:
            frac = (cycle - 1.8) / 1.2
            px_c = 42
            py_c = int(42 - frac * 36)
            col = (0, 255, 80)
            _safe_pixel(d, px_c, py_c, col)
            _safe_pixel(d, px_c, py_c + 1, _col_alpha(col, 0.4))
            _safe_pixel(d, px_c - 1, py_c, _col_alpha(col, 0.3))
            _safe_pixel(d, px_c + 1, py_c, _col_alpha(col, 0.3))

        d.draw_text_small(2, 4, 'LED', (0, 200, 80))

    def _draw_solar(self, sc):
        d = self.display
        t = self.scene_time
        cycle = t % 3.5
        for x in range(8, 56):
            d.set_pixel(x, 30, (60, 60, 80))
        for y in range(12, 30):
            for x in range(8, 56):
                if (x + y) % 6 == 0:
                    d.set_pixel(x, y, (20, 25, 40))
        for y in range(31, 50):
            for x in range(8, 56):
                if (x + y) % 6 == 0:
                    d.set_pixel(x, y, (25, 18, 30))
        d.draw_text_small(2, 14, 'N', (100, 160, 220))
        d.draw_text_small(2, 40, 'P', (220, 100, 160))

        if cycle < 1.0:
            frac = cycle
            py_c = int(_lerp(2, 28, frac))
            _safe_pixel(d, 32, py_c, PHOTON)
            _safe_pixel(d, 32, py_c - 1, _col_alpha(PHOTON, 0.5))
        elif cycle < 1.5:
            frac = (cycle - 1.0) / 0.5
            _draw_circle(d, 32, 30, int(2 + frac * 2),
                         _col_alpha(PHOTON, 1.0 - frac), filled=True)
        else:
            frac = (cycle - 1.5) / 2.0
            ey = int(_lerp(28, 12, frac))
            _draw_circle(d, 32, ey, 1, E_COL, filled=True)
            hy = int(_lerp(32, 48, frac))
            _draw_circle(d, 32, hy, 1, HOLE, filled=True)
            if frac > 0.3:
                a = min(1.0, (frac - 0.3) * 2)
                for i in range(3):
                    ay_e = 14 + i * 4
                    _safe_pixel(d, 6, ay_e, _col_alpha(E_COL, a * 0.5))

        d.draw_text_small(24, 4, 'SOLAR', _col_alpha(PHOTON, 0.6))
