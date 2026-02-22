"""
Maxwell's Demon — the iconic thermodynamic thought experiment.

A box divided in two by a wall with a gate.  ~120 gas particles bounce
around.  A tiny demon at the gate selectively opens it: fast (hot)
particles go right, slow (cold) particles go left.  One side heats up,
the other cools.  Toggle the demon off and entropy wins — sides
equalise in a beautiful cascade of mixing.
"""

from __future__ import annotations
import math
import random
from . import Visual, Display, Colors, GRID_SIZE

# ── Layout constants ────────────────────────────────────────────────
WALL_TOP = 2
WALL_BOT = 59
WALL_LEFT = 0
WALL_RIGHT = 63
DIVIDER_X = 31
GATE_TOP = 25
GATE_BOT = 36          # 12 px opening
TEMP_BAR_Y = 60

LEFT_X0, LEFT_X1 = 1, 30
RIGHT_X0, RIGHT_X1 = 32, 62
CHAMBER_Y0, CHAMBER_Y1 = 3, 58

NUM_PARTICLES = 120
MIN_SPEED = 0.3
MAX_SPEED = 5.0

# ── 7-stop speed→colour LUT (256 entries) ──────────────────────────
def _build_colour_lut():
    stops = [
        (0.00, (10, 10, 80)),    # deep blue  – still
        (0.15, (20, 40, 180)),   # blue
        (0.30, (0, 160, 200)),   # cyan
        (0.45, (20, 180, 40)),   # green
        (0.60, (220, 200, 0)),   # yellow
        (0.80, (240, 120, 0)),   # orange
        (1.00, (255, 30, 10)),   # red        – fast
    ]
    lut = []
    for i in range(256):
        t = i / 255.0
        # find surrounding stops
        for k in range(len(stops) - 1):
            t0, c0 = stops[k]
            t1, c1 = stops[k + 1]
            if t <= t1 or k == len(stops) - 2:
                f = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
                f = max(0.0, min(1.0, f))
                r = int(c0[0] + (c1[0] - c0[0]) * f)
                g = int(c0[1] + (c1[1] - c0[1]) * f)
                b = int(c0[2] + (c1[2] - c0[2]) * f)
                lut.append((r, g, b))
                break
    return lut

_COLOUR_LUT = _build_colour_lut()

def _speed_colour(speed):
    """Map speed (0..MAX_SPEED) → RGB via precomputed LUT."""
    idx = int(speed / MAX_SPEED * 255)
    return _COLOUR_LUT[min(idx, 255)]

def _dim(colour, factor):
    return (int(colour[0] * factor), int(colour[1] * factor), int(colour[2] * factor))

# ── Demon sprite (5×5) ─────────────────────────────────────────────
#  Row offsets relative to top-left of sprite
_DEMON_ROWS = [
    # row 0: horns
    [(-2, (200, 30, 30)), (2, (200, 30, 30))],
    # row 1: head
    [(-1, (140, 40, 160)), (0, (140, 40, 160)), (1, (140, 40, 160))],
    # row 2: eyes  (colour set dynamically for glow)
    [(-1, None), (1, None)],
    # row 3: body
    [(-1, (120, 30, 140)), (0, (120, 30, 140)), (1, (120, 30, 140))],
    # row 4: feet
    [(-1, (100, 25, 120)), (1, (100, 25, 120))],
]

# ── Auto-cycle phase timing ────────────────────────────────────────
PHASE_EQUILIBRIUM = 0
PHASE_DEMON_ARRIVE = 1
PHASE_SORTING = 2
PHASE_DEMON_DEPART = 3
PHASE_EQUALIZATION = 4
PHASE_HOLD = 5

_PHASE_DURATIONS = [5.0, 0.5, 20.0, 0.5, 10.0, 5.0]
IDLE_TIMEOUT = 8.0


class MaxwellDemon(Visual):
    name = "Maxwell's Demon"
    description = "Thermodynamic thought experiment — a demon sorts hot and cold gas"
    category = "science"

    def __init__(self, display: Display):
        super().__init__(display)

    # ── reset ───────────────────────────────────────────────────────
    def reset(self):
        self.time = 0.0
        # Particles: lists-of-floats for cache friendliness
        self.px = [0.0] * NUM_PARTICLES
        self.py = [0.0] * NUM_PARTICLES
        self.pvx = [0.0] * NUM_PARTICLES
        self.pvy = [0.0] * NUM_PARTICLES
        self._init_particles()

        # Demon state
        self.demon_active = False
        self.demon_alpha = 0.0       # 0..1 for fade in/out
        self.selectivity = 1.0       # multiplier on median threshold
        self.gate_open = 1.0         # 1=fully open, 0=fully closed
        self.gate_cooldown = 0.0
        self.gate_hold = 0.0         # time gate stays open after demon opens it

        # Speed control
        self.speed_mult = 1.0

        # Auto-cycle
        self.auto_phase = PHASE_EQUILIBRIUM
        self.phase_timer = 0.0
        self.idle_timer = 0.0
        self.auto_cycling = False

        # Cached chamber stats (updated every few frames)
        self._stats_cooldown = 0.0
        self.left_avg_speed = 0.0
        self.right_avg_speed = 0.0
        self.median_speed = 2.5

        # HUD overlay
        self.overlay_timer = 0.0
        self.overlay_lines = []

        # Frame counter for periodic work
        self._frame = 0

    def _init_particles(self):
        for i in range(NUM_PARTICLES):
            # Distribute evenly across both chambers
            if i < NUM_PARTICLES // 2:
                self.px[i] = random.uniform(LEFT_X0 + 0.5, LEFT_X1 - 0.5)
            else:
                self.px[i] = random.uniform(RIGHT_X0 + 0.5, RIGHT_X1 - 0.5)
            self.py[i] = random.uniform(CHAMBER_Y0 + 0.5, CHAMBER_Y1 - 0.5)
            speed = random.uniform(MIN_SPEED, MAX_SPEED)
            angle = random.uniform(0, 2 * math.pi)
            self.pvx[i] = math.cos(angle) * speed
            self.pvy[i] = math.sin(angle) * speed

    # ── input ───────────────────────────────────────────────────────
    def handle_input(self, inp) -> bool:
        consumed = False

        # Either button toggles demon
        if inp.action_l or inp.action_r:
            self.demon_active = not self.demon_active
            if not self.demon_active:
                self.gate_open = 1.0
            self.overlay_timer = 2.0
            self.overlay_lines = ["DEMON ON" if self.demon_active else "DEMON OFF"]
            consumed = True

        # Left / right: sim speed
        if inp.left:
            self.speed_mult = max(0.3, self.speed_mult - 0.04)
            self.overlay_timer = 1.5
            self.overlay_lines = [f"SPEED {self.speed_mult:.1f}X"]
            consumed = True
        if inp.right:
            self.speed_mult = min(2.5, self.speed_mult + 0.04)
            self.overlay_timer = 1.5
            self.overlay_lines = [f"SPEED {self.speed_mult:.1f}X"]
            consumed = True

        # Up / down: selectivity
        if inp.up_pressed:
            self.selectivity = min(2.0, self.selectivity + 0.2)
            self.overlay_timer = 1.5
            self.overlay_lines = [f"SELECT {self.selectivity:.1f}"]
            consumed = True
        if inp.down_pressed:
            self.selectivity = max(0.2, self.selectivity - 0.2)
            self.overlay_timer = 1.5
            self.overlay_lines = [f"SELECT {self.selectivity:.1f}"]
            consumed = True

        if consumed:
            self.auto_cycling = False
            self.idle_timer = 0.0
        return consumed

    # ── update ──────────────────────────────────────────────────────
    def update(self, dt: float):
        self.time += dt
        self._frame += 1
        eff_dt = dt * self.speed_mult

        # Overlay fade
        if self.overlay_timer > 0:
            self.overlay_timer -= dt

        # Idle / auto-cycle
        self.idle_timer += dt
        if not self.auto_cycling and self.idle_timer >= IDLE_TIMEOUT:
            self.auto_cycling = True
            self.auto_phase = PHASE_EQUILIBRIUM
            self.phase_timer = 0.0
        if self.auto_cycling:
            self._update_auto_cycle(dt)

        # Demon alpha fade
        target_alpha = 1.0 if self.demon_active else 0.0
        if self.demon_alpha < target_alpha:
            self.demon_alpha = min(target_alpha, self.demon_alpha + dt * 2.0)
        elif self.demon_alpha > target_alpha:
            self.demon_alpha = max(target_alpha, self.demon_alpha - dt * 2.0)

        # Gate animation: when demon active, close from edges inward
        if self.demon_active:
            if self.gate_hold > 0:
                self.gate_hold -= eff_dt
                self.gate_open = 1.0
            else:
                self.gate_open = max(0.0, self.gate_open - eff_dt * 4.0)
        else:
            self.gate_open = min(1.0, self.gate_open + eff_dt * 4.0)

        # Demon AI — scan & decide
        if self.demon_active and self.gate_hold <= 0 and self.gate_cooldown <= 0:
            self._demon_decide()
        if self.gate_cooldown > 0:
            self.gate_cooldown -= eff_dt

        # Move particles
        self._move_particles(eff_dt)

        # Update stats periodically
        self._stats_cooldown -= eff_dt
        if self._stats_cooldown <= 0:
            self._stats_cooldown = 0.15
            self._compute_stats()

    def _update_auto_cycle(self, dt):
        self.phase_timer += dt
        dur = _PHASE_DURATIONS[self.auto_phase]
        if self.phase_timer >= dur:
            self.phase_timer -= dur
            self.auto_phase = (self.auto_phase + 1) % len(_PHASE_DURATIONS)
            # Apply phase transitions
            if self.auto_phase == PHASE_EQUILIBRIUM:
                self.demon_active = False
            elif self.auto_phase == PHASE_DEMON_ARRIVE:
                self.demon_active = True
            elif self.auto_phase == PHASE_SORTING:
                pass  # demon already active
            elif self.auto_phase == PHASE_DEMON_DEPART:
                self.demon_active = False
            elif self.auto_phase == PHASE_EQUALIZATION:
                pass  # demon already off, gate opening
            elif self.auto_phase == PHASE_HOLD:
                pass

    def _demon_decide(self):
        """Scan particles near gate and decide whether to open."""
        threshold = self.median_speed * self.selectivity
        gate_y0 = GATE_TOP
        gate_y1 = GATE_BOT
        detect_x0, detect_x1 = 27, 35

        for i in range(NUM_PARTICLES):
            x, y = self.px[i], self.py[i]
            if x < detect_x0 or x > detect_x1:
                continue
            if y < gate_y0 or y > gate_y1:
                continue
            spd = math.sqrt(self.pvx[i] ** 2 + self.pvy[i] ** 2)
            vx = self.pvx[i]
            # Fast particle in left chamber moving right → let through
            if x < DIVIDER_X and vx > 0 and spd > threshold:
                self.gate_hold = 0.15
                self.gate_cooldown = 0.08
                return
            # Slow particle in right chamber moving left → let through
            if x > DIVIDER_X and vx < 0 and spd < threshold:
                self.gate_hold = 0.15
                self.gate_cooldown = 0.08
                return

    def _move_particles(self, dt):
        px, py, pvx, pvy = self.px, self.py, self.pvx, self.pvy
        # Precompute gate open range
        gate_open_frac = self.gate_open
        if gate_open_frac > 0.5:
            # Gate is open: full opening
            gy0 = GATE_TOP
            gy1 = GATE_BOT
        elif gate_open_frac > 0.01:
            # Partially open: shrink from edges toward centre
            mid = (GATE_TOP + GATE_BOT) / 2.0
            half = (GATE_BOT - GATE_TOP) / 2.0 * gate_open_frac * 2.0
            gy0 = mid - half
            gy1 = mid + half
        else:
            gy0 = gy1 = -1  # fully closed

        for i in range(NUM_PARTICLES):
            nx = px[i] + pvx[i] * dt
            ny = py[i] + pvy[i] * dt

            # Bounce off outer walls
            if nx <= LEFT_X0:
                nx = LEFT_X0 + (LEFT_X0 - nx)
                pvx[i] = abs(pvx[i])
            elif nx >= RIGHT_X1:
                nx = RIGHT_X1 - (nx - RIGHT_X1)
                pvx[i] = -abs(pvx[i])

            if ny <= CHAMBER_Y0:
                ny = CHAMBER_Y0 + (CHAMBER_Y0 - ny)
                pvy[i] = abs(pvy[i])
            elif ny >= CHAMBER_Y1:
                ny = CHAMBER_Y1 - (ny - CHAMBER_Y1)
                pvy[i] = -abs(pvy[i])

            # Divider wall collision
            old_x = px[i]
            if (old_x <= DIVIDER_X and nx > DIVIDER_X) or \
               (old_x >= DIVIDER_X + 1 and nx < DIVIDER_X):
                # Check if in gate opening
                in_gate = gy0 <= ny <= gy1
                if not in_gate:
                    pvx[i] = -pvx[i]
                    if old_x <= DIVIDER_X:
                        nx = DIVIDER_X - 0.1
                    else:
                        nx = DIVIDER_X + 1.1

            px[i] = nx
            py[i] = ny

    def _compute_stats(self):
        left_total = 0.0
        left_count = 0
        right_total = 0.0
        right_count = 0
        all_speeds = []
        for i in range(NUM_PARTICLES):
            spd = math.sqrt(self.pvx[i] ** 2 + self.pvy[i] ** 2)
            all_speeds.append(spd)
            if self.px[i] <= DIVIDER_X:
                left_total += spd
                left_count += 1
            else:
                right_total += spd
                right_count += 1
        self.left_avg_speed = left_total / max(left_count, 1)
        self.right_avg_speed = right_total / max(right_count, 1)
        all_speeds.sort()
        self.median_speed = all_speeds[len(all_speeds) // 2] if all_speeds else 2.5

    # ── draw ────────────────────────────────────────────────────────
    def draw(self):
        d = self.display
        d.clear()
        set_pixel = d.set_pixel

        # Chamber background tints (subtle)
        left_energy = min(1.0, self.left_avg_speed / MAX_SPEED)
        right_energy = min(1.0, self.right_avg_speed / MAX_SPEED)
        left_bg = (int(2 + 8 * left_energy), 2, int(14 - 10 * left_energy))
        right_bg = (int(2 + 8 * right_energy), 2, int(14 - 10 * right_energy))
        d.draw_rect(LEFT_X0, CHAMBER_Y0, LEFT_X1 - LEFT_X0 + 1,
                     CHAMBER_Y1 - CHAMBER_Y0 + 1, left_bg)
        d.draw_rect(RIGHT_X0, CHAMBER_Y0, RIGHT_X1 - RIGHT_X0 + 1,
                     CHAMBER_Y1 - CHAMBER_Y0 + 1, right_bg)

        # Box walls
        wall_col = (60, 60, 80)
        d.draw_line(WALL_LEFT, WALL_TOP, WALL_RIGHT, WALL_TOP, wall_col)   # top
        d.draw_line(WALL_LEFT, WALL_BOT, WALL_RIGHT, WALL_BOT, wall_col)   # bottom
        d.draw_line(WALL_LEFT, WALL_TOP, WALL_LEFT, WALL_BOT, wall_col)    # left
        d.draw_line(WALL_RIGHT, WALL_TOP, WALL_RIGHT, WALL_BOT, wall_col)  # right

        # Divider wall (with gate gap)
        gate_frac = self.gate_open
        if gate_frac > 0.5:
            gy0 = GATE_TOP
            gy1 = GATE_BOT
        elif gate_frac > 0.01:
            mid = (GATE_TOP + GATE_BOT) / 2.0
            half = (GATE_BOT - GATE_TOP) / 2.0 * gate_frac * 2.0
            gy0 = int(mid - half)
            gy1 = int(mid + half)
        else:
            gy0 = gy1 = -1
        for y in range(WALL_TOP + 1, WALL_BOT):
            if gy0 <= y <= gy1:
                continue  # gate opening
            set_pixel(DIVIDER_X, y, wall_col)

        # Particle trails then particles
        px, py, pvx, pvy = self.px, self.py, self.pvx, self.pvy
        for i in range(NUM_PARTICLES):
            spd = math.sqrt(pvx[i] ** 2 + pvy[i] ** 2)
            col = _speed_colour(spd)
            # Trail
            tx = int(px[i] - pvx[i] * 0.7)
            ty = int(py[i] - pvy[i] * 0.7)
            if LEFT_X0 <= tx <= RIGHT_X1 and CHAMBER_Y0 <= ty <= CHAMBER_Y1:
                set_pixel(tx, ty, _dim(col, 0.25))
            # Particle
            ix = int(px[i])
            iy = int(py[i])
            if LEFT_X0 <= ix <= RIGHT_X1 and CHAMBER_Y0 <= iy <= CHAMBER_Y1:
                set_pixel(ix, iy, col)

        # Demon sprite
        if self.demon_alpha > 0.01:
            self._draw_demon(set_pixel)

        # Temperature bars at y=60..61
        self._draw_temp_bars(set_pixel)

        # HUD overlay
        if self.overlay_timer > 0 and self.overlay_lines:
            alpha = min(1.0, self.overlay_timer / 0.5)
            c = int(255 * alpha)
            for idx, line in enumerate(self.overlay_lines):
                d.draw_text_small(2, 2 + idx * 8, line, (c, c, int(200 * alpha)))

    def _draw_demon(self, set_pixel):
        """Draw the 5×5 demon sprite at the gate centre."""
        cx = DIVIDER_X
        cy = (GATE_TOP + GATE_BOT) // 2
        alpha = self.demon_alpha
        # Eye glow pulse
        glow = 0.6 + 0.4 * math.sin(self.time * 4.0)
        eye_col = (int(40 * alpha), int((180 + 75 * glow) * alpha), int((220 + 35 * glow) * alpha))

        for row_idx, row in enumerate(_DEMON_ROWS):
            dy = row_idx - 2  # centre vertically
            for dx, base_col in row:
                if base_col is None:
                    col = eye_col
                else:
                    col = (int(base_col[0] * alpha),
                           int(base_col[1] * alpha),
                           int(base_col[2] * alpha))
                px = cx + dx
                py_pos = cy + dy
                if 0 <= px < GRID_SIZE and 0 <= py_pos < GRID_SIZE:
                    set_pixel(px, py_pos, col)

    def _draw_temp_bars(self, set_pixel):
        """Draw temperature indicator bars at bottom."""
        # Left chamber bar: y=61, x=1..30
        left_col = _speed_colour(self.left_avg_speed)
        for x in range(LEFT_X0, LEFT_X1 + 1):
            set_pixel(x, TEMP_BAR_Y + 1, left_col)
        # Right chamber bar: y=61, x=32..62
        right_col = _speed_colour(self.right_avg_speed)
        for x in range(RIGHT_X0, RIGHT_X1 + 1):
            set_pixel(x, TEMP_BAR_Y + 1, right_col)
        # Thin separator line at y=60
        sep_col = (40, 40, 50)
        for x in range(WALL_LEFT, WALL_RIGHT + 1):
            set_pixel(x, TEMP_BAR_Y, sep_col)
