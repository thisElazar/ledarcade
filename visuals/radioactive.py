"""
Radioactive - Nuclear Decay Simulation
=======================================
Simulate radioactive decay on a 16x16 grid of atoms. Unstable atoms
randomly decay, emitting alpha, beta, and gamma particles that fly
outward. Five scenarios demonstrate different decay modes.

Controls:
  Left/Right     - Cycle scenario
  Up/Down        - Cycle color palette
  Single button  - Reset current scenario
  Both buttons   - Toggle scrolling notes
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE

# Atom states
STABLE = 0
UNSTABLE = 1
DECAYED = 2

# Particle types
ALPHA = 'alpha'
BETA = 'beta'
GAMMA = 'gamma'

# Atom grid dimensions (4x4 pixel cells -> 16x16 atom grid)
ATOM_SIZE = 4
ATOM_COLS = GRID_SIZE // ATOM_SIZE  # 16
ATOM_ROWS = GRID_SIZE // ATOM_SIZE  # 16

# Max active particles (Pi 3 performance)
MAX_PARTICLES = 180

_SCENARIOS = ['ALPHA DECAY', 'BETA DECAY', 'CHAIN REACTION', 'HALF-LIFE', 'RANDOM MIX']

PALETTES = [
    # Nuclear: green unstable, yellow/orange particles, dark bg
    {
        'name': 'NUCLEAR',
        'unstable': (0, 200, 40),
        'stable': (80, 80, 80),
        'decayed': (10, 20, 5),
        'flash': (200, 255, 100),
        'alpha': (255, 200, 50),
        'beta': (50, 180, 255),
        'gamma': (150, 255, 150),
        'bg': (2, 5, 2),
        'text': (0, 200, 40),
    },
    # Uranium: yellow-green atoms, bright particles
    {
        'name': 'URANIUM',
        'unstable': (180, 220, 30),
        'stable': (90, 90, 70),
        'decayed': (15, 15, 5),
        'flash': (255, 255, 100),
        'alpha': (255, 180, 30),
        'beta': (80, 200, 255),
        'gamma': (255, 255, 200),
        'bg': (3, 4, 1),
        'text': (180, 220, 30),
    },
    # Hot: red/orange atoms, white/yellow particles
    {
        'name': 'HOT',
        'unstable': (255, 80, 20),
        'stable': (100, 60, 60),
        'decayed': (20, 5, 2),
        'flash': (255, 255, 200),
        'alpha': (255, 255, 80),
        'beta': (255, 200, 150),
        'gamma': (255, 255, 255),
        'bg': (5, 1, 1),
        'text': (255, 120, 40),
    },
    # Cool: blue atoms, cyan/white particles
    {
        'name': 'COOL',
        'unstable': (40, 100, 255),
        'stable': (60, 60, 100),
        'decayed': (2, 5, 20),
        'flash': (150, 200, 255),
        'alpha': (100, 200, 255),
        'beta': (50, 255, 255),
        'gamma': (220, 240, 255),
        'bg': (1, 1, 5),
        'text': (80, 150, 255),
    },
    # Mono: white atoms, gray particles
    {
        'name': 'MONO',
        'unstable': (220, 220, 220),
        'stable': (100, 100, 100),
        'decayed': (15, 15, 15),
        'flash': (255, 255, 255),
        'alpha': (200, 200, 200),
        'beta': (170, 170, 170),
        'gamma': (255, 255, 255),
        'bg': (3, 3, 3),
        'text': (200, 200, 200),
    },
]


class Radioactive(Visual):
    name = "RADIOACTIVE"
    description = "Nuclear decay simulation"
    category = "science"

    def __init__(self, display: Display):
        super().__init__(display)

    # -- notes --------------------------------------------------------

    def _get_notes(self):
        pal = PALETTES[self.palette_idx]
        mid = pal['text']
        return [
            ("RADIOACTIVE DECAY", (255, 255, 255)),
            ("ATOMS EMIT ALPHA BETA AND GAMMA", mid),
            ("HALF-LIFE: TIME FOR HALF TO DECAY", mid),
            ("CHAIN REACTIONS TRIGGER NEIGHBORS", mid),
            ("HENRI BECQUEREL 1896", (255, 255, 255)),
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

    # -- overlay ------------------------------------------------------

    def _draw_overlay(self):
        if self.overlay_timer <= 0:
            return
        alpha = min(1.0, self.overlay_timer / 0.5)
        c = (int(255 * alpha), int(255 * alpha), int(255 * alpha))
        self.display.draw_text_small(2, 2, self.overlay_text, c)

    def _show_overlay(self, text):
        self.overlay_text = text
        self.overlay_timer = 2.0

    # -- scenario setup -----------------------------------------------

    def reset(self):
        self.time = 0.0
        self.palette_idx = 0
        self.scenario_idx = 0
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
        """Initialize atoms and scenario-specific state."""
        self.atoms = [[DECAYED] * ATOM_COLS for _ in range(ATOM_ROWS)]
        self.particles = []
        self.flashes = []  # [(grid_x, grid_y, timer)]
        self.atom_flicker = [[random.random() for _ in range(ATOM_COLS)]
                             for _ in range(ATOM_ROWS)]
        self.auto_reset_timer = 0.0
        self.elapsed = 0.0
        # Chain reaction boost grid
        self.boost = [[0.0] * ATOM_COLS for _ in range(ATOM_ROWS)]

        scenario = _SCENARIOS[self.scenario_idx]

        if scenario == 'ALPHA DECAY':
            self.half_life = 8.0
            self.particle_types = [ALPHA]
            self._fill_all_unstable()

        elif scenario == 'BETA DECAY':
            self.half_life = 4.0
            self.particle_types = [BETA]
            self._fill_all_unstable()

        elif scenario == 'CHAIN REACTION':
            self.half_life = 999.0  # Natural decay very unlikely
            self.particle_types = [ALPHA, BETA, GAMMA]
            self._fill_all_unstable()
            # Trigger center atom
            cx, cy = ATOM_COLS // 2, ATOM_ROWS // 2
            self.atoms[cy][cx] = DECAYED
            self._spawn_decay_particles(cx, cy, count=3)
            self._add_flash(cx, cy)
            # Boost neighbors
            self._boost_neighbors(cx, cy)

        elif scenario == 'HALF-LIFE':
            self.half_life = 3.0
            self.particle_types = [ALPHA, BETA, GAMMA]
            self._fill_all_unstable()

        elif scenario == 'RANDOM MIX':
            self.half_life = 5.0
            self.particle_types = [ALPHA, BETA, GAMMA]
            # ~200 unstable, ~56 stable
            for r in range(ATOM_ROWS):
                for c in range(ATOM_COLS):
                    roll = random.random()
                    if roll < 0.22:
                        self.atoms[r][c] = STABLE
                    else:
                        self.atoms[r][c] = UNSTABLE

    def _fill_all_unstable(self):
        for r in range(ATOM_ROWS):
            for c in range(ATOM_COLS):
                self.atoms[r][c] = UNSTABLE

    def _count_unstable(self):
        count = 0
        for r in range(ATOM_ROWS):
            for c in range(ATOM_COLS):
                if self.atoms[r][c] == UNSTABLE:
                    count += 1
        return count

    # -- particle spawning --------------------------------------------

    def _spawn_decay_particles(self, gx, gy, count=0):
        """Spawn particles from a decaying atom at grid position (gx, gy)."""
        if count == 0:
            count = random.randint(1, 3)
        # Pixel center of atom cell
        px = gx * ATOM_SIZE + ATOM_SIZE // 2
        py = gy * ATOM_SIZE + ATOM_SIZE // 2

        for _ in range(count):
            if len(self.particles) >= MAX_PARTICLES:
                break
            ptype = random.choice(self.particle_types)
            angle = random.uniform(0, 2 * math.pi)

            if ptype == ALPHA:
                speed = random.uniform(15, 25)
                max_life = 0.5
            elif ptype == BETA:
                speed = random.uniform(40, 70)
                max_life = 0.6
            else:  # GAMMA
                speed = random.uniform(80, 120)
                max_life = 0.7

            self.particles.append({
                'x': float(px),
                'y': float(py),
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': max_life,
                'max_life': max_life,
                'type': ptype,
            })

    def _add_flash(self, gx, gy):
        self.flashes.append((gx, gy, 0.15))

    def _boost_neighbors(self, gx, gy):
        """Boost decay probability of neighboring atoms (chain reaction)."""
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = gx + dx, gy + dy
                if 0 <= nx < ATOM_COLS and 0 <= ny < ATOM_ROWS:
                    self.boost[ny][nx] = max(self.boost[ny][nx], 0.3)

    # -- input --------------------------------------------------------

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Left/Right: cycle scenario
        if input_state.left_pressed:
            self.scenario_idx = (self.scenario_idx - 1) % len(_SCENARIOS)
            self._setup_scenario()
            self._show_overlay(_SCENARIOS[self.scenario_idx])
            consumed = True
        if input_state.right_pressed:
            self.scenario_idx = (self.scenario_idx + 1) % len(_SCENARIOS)
            self._setup_scenario()
            self._show_overlay(_SCENARIOS[self.scenario_idx])
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
                # Single button: reset current scenario
                self._setup_scenario()
                self._show_overlay(_SCENARIOS[self.scenario_idx])
                consumed = True
        self._both_pressed_prev = both

        return consumed

    # -- update -------------------------------------------------------

    def update(self, dt: float):
        self.time += dt
        self.elapsed += dt

        scenario = _SCENARIOS[self.scenario_idx]
        is_chain = scenario == 'CHAIN REACTION'

        # -- Decay atoms --
        unstable_count = 0
        for r in range(ATOM_ROWS):
            for c in range(ATOM_COLS):
                if self.atoms[r][c] != UNSTABLE:
                    continue
                unstable_count += 1

                # Compute decay probability
                if is_chain:
                    # Chain reaction: mostly from boost, tiny natural rate
                    p = 1.0 - 2.0 ** (-dt / self.half_life)
                    p = max(p, self.boost[r][c] * dt * 8.0)
                else:
                    p = 1.0 - 2.0 ** (-dt / self.half_life)

                if random.random() < p:
                    self.atoms[r][c] = DECAYED
                    particle_count = 3 if is_chain else random.randint(1, 2)
                    self._spawn_decay_particles(c, r, count=particle_count)
                    self._add_flash(c, r)
                    if is_chain:
                        self._boost_neighbors(c, r)

                # Update flicker
                self.atom_flicker[r][c] += random.uniform(-0.3, 0.3)
                self.atom_flicker[r][c] = max(0.0, min(1.0, self.atom_flicker[r][c]))

        # -- Decay boost (chain reaction) --
        if is_chain:
            for r in range(ATOM_ROWS):
                for c in range(ATOM_COLS):
                    if self.boost[r][c] > 0:
                        self.boost[r][c] = max(0.0, self.boost[r][c] - dt * 0.5)

        # -- Update particles --
        is_random_mix = scenario == 'RANDOM MIX'
        alive = []
        for p in self.particles:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['life'] -= dt

            # Check bounds
            if p['x'] < -2 or p['x'] >= GRID_SIZE + 2 or \
               p['y'] < -2 or p['y'] >= GRID_SIZE + 2:
                p['life'] = 0

            # Stable atom absorption (RANDOM MIX only)
            if is_random_mix and p['life'] > 0:
                gx = int(p['x']) // ATOM_SIZE
                gy = int(p['y']) // ATOM_SIZE
                if 0 <= gx < ATOM_COLS and 0 <= gy < ATOM_ROWS:
                    if self.atoms[gy][gx] == STABLE:
                        p['life'] = 0  # Absorbed

            if p['life'] > 0:
                alive.append(p)
        self.particles = alive

        # -- Update flashes --
        new_flashes = []
        for gx, gy, t in self.flashes:
            t -= dt
            if t > 0:
                new_flashes.append((gx, gy, t))
        self.flashes = new_flashes

        # -- Auto-reset check --
        if unstable_count == 0 and len(self.particles) == 0 and len(self.flashes) == 0:
            self.auto_reset_timer += dt
            if self.auto_reset_timer >= 2.0:
                self._setup_scenario()
        else:
            self.auto_reset_timer = 0.0

        # -- Overlay & notes timers --
        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

        if self.show_notes:
            self.notes_scroll_offset += dt * 18

    # -- draw ---------------------------------------------------------

    def draw(self):
        pal = PALETTES[self.palette_idx]
        self.display.clear(pal['bg'])

        scenario = _SCENARIOS[self.scenario_idx]

        # -- Draw atoms --
        for r in range(ATOM_ROWS):
            for c in range(ATOM_COLS):
                state = self.atoms[r][c]
                px = c * ATOM_SIZE
                py = r * ATOM_SIZE

                if state == UNSTABLE:
                    base = pal['unstable']
                    # Subtle brightness flicker
                    flick = 0.8 + 0.2 * self.atom_flicker[r][c]
                    color = (
                        min(255, int(base[0] * flick)),
                        min(255, int(base[1] * flick)),
                        min(255, int(base[2] * flick)),
                    )
                    # Draw 3x3 filled square within 4x4 cell (offset by 0,0)
                    for dy in range(3):
                        for dx in range(3):
                            self.display.set_pixel(px + dx, py + dy, color)

                elif state == STABLE:
                    color = pal['stable']
                    for dy in range(3):
                        for dx in range(3):
                            self.display.set_pixel(px + dx, py + dy, color)

                elif state == DECAYED:
                    # Very dim single pixel
                    dim = pal['decayed']
                    self.display.set_pixel(px + 1, py + 1, dim)

        # -- Draw flashes --
        for gx, gy, t in self.flashes:
            px = gx * ATOM_SIZE
            py = gy * ATOM_SIZE
            brightness = t / 0.15  # 1.0 -> 0.0
            fc = pal['flash']
            color = (
                min(255, int(fc[0] * brightness)),
                min(255, int(fc[1] * brightness)),
                min(255, int(fc[2] * brightness)),
            )
            for dy in range(3):
                for dx in range(3):
                    self.display.set_pixel(px + dx, py + dy, color)

        # -- Draw particles --
        for p in self.particles:
            life_frac = max(0.0, p['life'] / p['max_life'])
            ptype = p['type']
            ix = int(p['x'])
            iy = int(p['y'])

            if ptype == ALPHA:
                base = pal['alpha']
                brightness = life_frac
                color = (
                    min(255, int(base[0] * brightness)),
                    min(255, int(base[1] * brightness)),
                    min(255, int(base[2] * brightness)),
                )
                # 2x2 bright dot
                for dy in range(2):
                    for dx in range(2):
                        nx, ny = ix + dx, iy + dy
                        if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                            self.display.set_pixel(nx, ny, color)
                # 1-frame afterglow trail
                trail_brightness = life_frac * 0.3
                trail_color = (
                    int(base[0] * trail_brightness),
                    int(base[1] * trail_brightness),
                    int(base[2] * trail_brightness),
                )
                tx = ix - int(p['vx'] * 0.03)
                ty = iy - int(p['vy'] * 0.03)
                if 0 <= tx < GRID_SIZE and 0 <= ty < GRID_SIZE:
                    self.display.set_pixel(tx, ty, trail_color)

            elif ptype == BETA:
                base = pal['beta']
                brightness = life_frac
                color = (
                    min(255, int(base[0] * brightness)),
                    min(255, int(base[1] * brightness)),
                    min(255, int(base[2] * brightness)),
                )
                # 1px dot
                if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                    self.display.set_pixel(ix, iy, color)
                # Thin trail (2-3 px behind)
                trail_brightness = life_frac * 0.25
                trail_color = (
                    int(base[0] * trail_brightness),
                    int(base[1] * trail_brightness),
                    int(base[2] * trail_brightness),
                )
                for step in range(1, 3):
                    tx = ix - int(p['vx'] * 0.015 * step)
                    ty = iy - int(p['vy'] * 0.015 * step)
                    if 0 <= tx < GRID_SIZE and 0 <= ty < GRID_SIZE:
                        self.display.set_pixel(tx, ty, trail_color)

            else:  # GAMMA
                base = pal['gamma']
                brightness = life_frac
                color = (
                    min(255, int(base[0] * brightness)),
                    min(255, int(base[1] * brightness)),
                    min(255, int(base[2] * brightness)),
                )
                # 1px very bright dot
                if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                    self.display.set_pixel(ix, iy, color)

        # -- HUD for HALF-LIFE scenario --
        if scenario == 'HALF-LIFE':
            count = self._count_unstable()
            half_lives = self.elapsed / self.half_life if self.half_life > 0 else 0
            self.display.draw_text_small(2, 2,
                                         "N:" + str(count),
                                         (255, 255, 255))
            # Format half-lives to 1 decimal
            hl_str = "{:.1f}".format(half_lives)
            self.display.draw_text_small(2, 8,
                                         "T:" + hl_str,
                                         (255, 255, 255))

        # -- Notes & overlay --
        if self.show_notes:
            self._draw_notes()
        self._draw_overlay()
