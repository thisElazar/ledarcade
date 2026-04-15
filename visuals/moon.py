"""
MOON PHASES - Lunar Phase Visualization
========================================
Displays the Moon with realistic shadow rendering, twinkling background
stars, procedural crater texture, earthshine, a horizon silhouette,
and occasional shooting stars.

Default mode is LIVE — the moon tracks the real current lunar phase.
Press either action button to toggle to manual mode (left/right cycles
discrete phases) and back.
"""

import math
import random
import datetime
from . import Visual, Display, Colors

# ---------------------------------------------------------------------------
# Phase data (for manual mode discrete steps)
# ---------------------------------------------------------------------------
PHASES = [
    ('NEW MOON',         0.0),
    ('WAXING CRESCENT',  math.pi * 0.25),
    ('FIRST QUARTER',    math.pi * 0.5),
    ('WAXING GIBBOUS',   math.pi * 0.75),
    ('FULL MOON',        math.pi),
    ('WANING GIBBOUS',   math.pi * 1.25),
    ('LAST QUARTER',     math.pi * 1.5),
    ('WANING CRESCENT',  math.pi * 1.75),
]

PHASE_DAYS = [0, 3.7, 7.4, 11.1, 14.8, 18.5, 22.1, 25.8]

# ---------------------------------------------------------------------------
# Palettes: (name, lit_base, dark_surface)
# ---------------------------------------------------------------------------
PALETTES = [
    ('SILVER',     (200, 200, 210), (15, 15, 25)),
    ('GOLD',       (220, 200, 130), (20, 18, 10)),
    ('BLOOD MOON', (200, 60, 40),   (30, 8, 5)),
    ('BLUE MOON',  (140, 170, 220), (10, 12, 30)),
]

# Moon parameters
MOON_R = 22
CX, CY = 32, 28

# Synodic month for live-mode calculation
_SYNODIC_PERIOD = 29.53059  # days
# Known new moon: Jan 6 2000 18:14 UTC
_NEW_MOON_EPOCH = datetime.datetime(2000, 1, 6, 18, 14, 0,
                                    tzinfo=datetime.timezone.utc)

# ---------------------------------------------------------------------------
# Procedural craters (deterministic seed)
# ---------------------------------------------------------------------------
def _generate_craters():
    """Build a dict {(dx, dy): brightness_multiplier} for the moon surface."""
    rng = random.Random(42)
    surface = {}
    r2 = MOON_R * MOON_R

    # 5-6 large mare (dark basalt plains) — circles of radius 3-5
    n_mare = rng.randint(5, 6)
    for _ in range(n_mare):
        for _attempt in range(30):
            mx = rng.randint(-MOON_R + 5, MOON_R - 5)
            my = rng.randint(-MOON_R + 5, MOON_R - 5)
            if mx * mx + my * my < (MOON_R - 4) ** 2:
                break
        mare_r = rng.randint(3, 5)
        dim = rng.uniform(0.55, 0.65)
        for dy in range(-mare_r, mare_r + 1):
            for dx in range(-mare_r, mare_r + 1):
                if dx * dx + dy * dy <= mare_r * mare_r:
                    px, py = mx + dx, my + dy
                    if px * px + py * py < r2:
                        # Don't overwrite existing darker features
                        if (px, py) not in surface or surface[(px, py)] > dim:
                            surface[(px, py)] = dim

    # 15-18 small craters — single point
    n_small = rng.randint(15, 18)
    for _ in range(n_small):
        for _attempt in range(30):
            sx = rng.randint(-MOON_R + 2, MOON_R - 2)
            sy = rng.randint(-MOON_R + 2, MOON_R - 2)
            if sx * sx + sy * sy < (MOON_R - 1) ** 2:
                break
        dim = rng.uniform(0.70, 0.80)
        if (sx, sy) not in surface or surface[(sx, sy)] > dim:
            surface[(sx, sy)] = dim

    # 3 bright ray craters — multiplier > 1
    for _ in range(3):
        for _attempt in range(30):
            bx = rng.randint(-MOON_R + 3, MOON_R - 3)
            by = rng.randint(-MOON_R + 3, MOON_R - 3)
            if bx * bx + by * by < (MOON_R - 2) ** 2:
                break
        mult = rng.uniform(1.10, 1.20)
        surface[(bx, by)] = mult

    return surface

CRATER_MAP = _generate_craters()

# ---------------------------------------------------------------------------
# Horizon silhouette (static terrain profile)
# ---------------------------------------------------------------------------
def _generate_horizon():
    """Return a list of 64 heights (0-6 pixels up from row 63)."""
    rng = random.Random(7)
    heights = []
    h = 3.0
    for x in range(64):
        h += rng.uniform(-0.7, 0.7)
        h = max(0.5, min(6.0, h))
        # Occasional tree spikes
        if rng.random() < 0.08:
            heights.append(min(6, int(h) + rng.randint(1, 2)))
        else:
            heights.append(max(0, int(h)))
    return heights

HORIZON = _generate_horizon()


def _get_live_phase_angle():
    """Compute the current lunar phase angle from system UTC time."""
    now = datetime.datetime.now(datetime.timezone.utc)
    delta = (now - _NEW_MOON_EPOCH).total_seconds() / 86400.0
    phase_frac = (delta % _SYNODIC_PERIOD) / _SYNODIC_PERIOD
    return phase_frac * 2 * math.pi


def _phase_name_from_angle(angle):
    """Return a human-readable phase name for a continuous angle."""
    frac = (angle % (2 * math.pi)) / (2 * math.pi)
    if frac < 0.0625:
        return 'NEW MOON'
    elif frac < 0.1875:
        return 'WAXING CRESCENT'
    elif frac < 0.3125:
        return 'FIRST QUARTER'
    elif frac < 0.4375:
        return 'WAXING GIBBOUS'
    elif frac < 0.5625:
        return 'FULL MOON'
    elif frac < 0.6875:
        return 'WANING GIBBOUS'
    elif frac < 0.8125:
        return 'LAST QUARTER'
    elif frac < 0.9375:
        return 'WANING CRESCENT'
    else:
        return 'NEW MOON'


def _day_from_angle(angle):
    """Return synodic day (0-29.5) from phase angle."""
    frac = (angle % (2 * math.pi)) / (2 * math.pi)
    return frac * _SYNODIC_PERIOD


class MoonPhases(Visual):
    name = "MOON PHASES"
    description = "Lunar phase cycle with realistic shadows"
    category = "science_macro"

    def reset(self):
        self.time = 0.0
        self.phase_idx = 0
        self.palette_idx = 0
        self.overlay_timer = 0.0
        self.label_timer = 0.0
        self.scroll_offset = 0.0

        # Mode: True = live (real lunar phase), False = manual
        self.live_mode = True
        self.live_overlay_timer = 2.0  # Show "LIVE" label on start

        # Smooth transition (for manual mode)
        self.phase_angle = _get_live_phase_angle()
        self.target_angle = self.phase_angle

        # Auto-cycle for manual mode
        self.auto_cycle = True
        self.cycle_timer = 0.0
        self.cycle_duration = 4.0

        # Background stars — avoid horizon zone
        self.stars = []
        for _ in range(40):
            sx = random.randint(0, 63)
            sy = random.randint(0, 63)
            self.stars.append((sx, sy,
                               random.uniform(0, math.pi * 2),
                               random.uniform(0.3, 1.0)))

        # Shooting star state
        self._shoot_timer = random.uniform(8.0, 15.0)
        self._shoot_active = False
        self._shoot_x = 0.0
        self._shoot_y = 0.0
        self._shoot_dx = 0.0
        self._shoot_dy = 0.0
        self._shoot_age = 0.0
        self._shoot_dur = 0.4
        self._shoot_trail = []  # list of (x, y, age) for fading trail

    def handle_input(self, input_state):
        consumed = False

        # Action buttons: toggle live / manual mode
        if input_state.action_l or input_state.action_r:
            self.live_mode = not self.live_mode
            self.live_overlay_timer = 2.0
            if self.live_mode:
                # Snap to current real phase
                self.phase_angle = _get_live_phase_angle()
                self.target_angle = self.phase_angle
            else:
                # Enter manual: find nearest discrete phase
                best_idx = 0
                best_diff = 999.0
                for i, (_, ang) in enumerate(PHASES):
                    d = abs(self.phase_angle - ang)
                    d = min(d, 2 * math.pi - d)
                    if d < best_diff:
                        best_diff = d
                        best_idx = i
                self.phase_idx = best_idx
                self.target_angle = PHASES[self.phase_idx][1]
                self.cycle_timer = 0.0
                self.label_timer = 0.0
                self.scroll_offset = 0.0
            consumed = True

        # Left/right: manual phase cycling (only in manual mode)
        if not self.live_mode:
            if input_state.left_pressed:
                self.phase_idx = (self.phase_idx - 1) % len(PHASES)
                self.target_angle = PHASES[self.phase_idx][1]
                self.auto_cycle = False
                self.cycle_timer = 0.0
                self.label_timer = 0.0
                self.scroll_offset = 0.0
                consumed = True
            if input_state.right_pressed:
                self.phase_idx = (self.phase_idx + 1) % len(PHASES)
                self.target_angle = PHASES[self.phase_idx][1]
                self.auto_cycle = False
                self.cycle_timer = 0.0
                self.label_timer = 0.0
                self.scroll_offset = 0.0
                consumed = True

        # Up/down: palette cycling (both modes)
        if input_state.up_pressed:
            self.palette_idx = (self.palette_idx - 1) % len(PALETTES)
            self.overlay_timer = 2.0
            consumed = True
        if input_state.down_pressed:
            self.palette_idx = (self.palette_idx + 1) % len(PALETTES)
            self.overlay_timer = 2.0
            consumed = True

        return consumed

    def update(self, dt):
        self.time += dt
        self.label_timer += dt
        self.scroll_offset += dt * 20

        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)
        if self.live_overlay_timer > 0:
            self.live_overlay_timer = max(0.0, self.live_overlay_timer - dt)

        if self.live_mode:
            # Continuously track real lunar phase
            self.phase_angle = _get_live_phase_angle()
        else:
            # Manual mode: auto-cycle or smooth transition
            if self.auto_cycle:
                self.cycle_timer += dt
                if self.cycle_timer >= self.cycle_duration:
                    self.cycle_timer = 0.0
                    self.phase_idx = (self.phase_idx + 1) % len(PHASES)
                    self.target_angle = PHASES[self.phase_idx][1]
                    self.label_timer = 0.0
                    self.scroll_offset = 0.0

            # Smooth angle transition
            diff = self.target_angle - self.phase_angle
            if diff > math.pi:
                diff -= 2 * math.pi
            elif diff < -math.pi:
                diff += 2 * math.pi
            self.phase_angle += diff * min(1.0, dt * 4.0)

        # --- Shooting star logic ---
        if not self._shoot_active:
            self._shoot_timer -= dt
            if self._shoot_timer <= 0:
                self._launch_shooting_star()
        else:
            self._shoot_age += dt
            self._shoot_x += self._shoot_dx * dt
            self._shoot_y += self._shoot_dy * dt
            # Record trail point
            self._shoot_trail.append((self._shoot_x, self._shoot_y,
                                      self._shoot_age))
            # Keep only recent trail
            self._shoot_trail = [
                (tx, ty, ta) for tx, ty, ta in self._shoot_trail
                if self._shoot_age - ta < 0.15
            ]
            if self._shoot_age >= self._shoot_dur:
                self._shoot_active = False
                self._shoot_trail = []
                self._shoot_timer = random.uniform(8.0, 15.0)

    def _launch_shooting_star(self):
        """Pick a start position in the sky (above horizon, outside moon)."""
        for _ in range(20):
            sx = random.randint(2, 61)
            sy = random.randint(2, 50)
            # Check not behind moon
            mdx = sx - CX
            mdy = sy - CY
            if mdx * mdx + mdy * mdy < (MOON_R + 4) ** 2:
                continue
            # Check above horizon
            if sy >= 63 - HORIZON[sx]:
                continue
            # Good position — launch
            self._shoot_active = True
            self._shoot_x = float(sx)
            self._shoot_y = float(sy)
            # Diagonal direction (roughly down-right or down-left)
            angle = random.uniform(0.3, 1.0)  # radians from horizontal
            speed = random.uniform(80, 120)  # pixels/sec
            sign = random.choice([-1, 1])
            self._shoot_dx = sign * math.cos(angle) * speed
            self._shoot_dy = math.sin(angle) * speed
            self._shoot_age = 0.0
            self._shoot_trail = []
            self._shoot_dur = random.uniform(0.3, 0.5)
            return
        # Failed to find a spot — wait and try again
        self._shoot_timer = random.uniform(2.0, 4.0)

    def draw(self):
        d = self.display
        d.clear((3, 3, 12))

        angle = self.phase_angle

        # --- Horizon line (y value at or above which we draw terrain) ---
        # horizon_top[x] = first row of terrain (inclusive, counting from top)
        horizon_top = [63 - HORIZON[x] + 1 for x in range(64)]

        # --- Background stars ---
        for sx, sy, phase, brightness in self.stars:
            # Skip stars behind the moon
            mdx = sx - CX
            mdy = sy - CY
            if mdx * mdx + mdy * mdy < (MOON_R + 2) ** 2:
                continue
            # Skip stars below horizon
            if sy >= horizon_top[min(63, max(0, sx))]:
                continue
            twinkle = 0.5 + 0.5 * math.sin(self.time * 1.5 + phase)
            v = int(40 + 160 * brightness * twinkle)
            d.set_pixel(sx, sy, (v, v, v))

        # --- Shooting star ---
        if self._shoot_active:
            # Draw trail
            for tx, ty, ta in self._shoot_trail:
                ix, iy = int(tx), int(ty)
                if 0 <= ix < 64 and 0 <= iy < 64:
                    fade = max(0.0, 1.0 - (self._shoot_age - ta) / 0.15)
                    v = int(200 * fade)
                    d.set_pixel(ix, iy, (v, v, int(v * 0.8)))
            # Draw head
            ix, iy = int(self._shoot_x), int(self._shoot_y)
            if 0 <= ix < 64 and 0 <= iy < 64:
                d.set_pixel(ix, iy, (255, 255, 220))

        # --- Moon rendering ---
        pal_name, lit_base, dark_base = PALETTES[self.palette_idx]

        # Compute lit fraction for earthshine calculation
        # lit_fraction: 0 = new moon, 1 = full moon
        lit_fraction = (1.0 - math.cos(angle)) / 2.0

        r2 = MOON_R * MOON_R
        cos_a = math.cos(angle)

        for dy in range(-MOON_R, MOON_R + 1):
            half_w_sq = r2 - dy * dy
            if half_w_sq < 0:
                continue
            half_w = math.sqrt(half_w_sq)
            term_x = cos_a * half_w

            for dx in range(int(-half_w), int(half_w) + 1):
                # Determine lit or dark
                if angle <= math.pi:
                    lit = dx >= term_x
                else:
                    lit = dx <= -cos_a * half_w

                if lit:
                    base = lit_base
                    # Surface shading: slight falloff at edges
                    dist_frac = math.sqrt(dx * dx + dy * dy) / MOON_R
                    shade = 1.0 - 0.2 * dist_frac
                    # Crater/mare dimming
                    crater_mult = CRATER_MAP.get((dx, dy), 1.0)
                    shade *= crater_mult
                    c = (min(255, int(base[0] * shade)),
                         min(255, int(base[1] * shade)),
                         min(255, int(base[2] * shade)))
                else:
                    # Earthshine: when crescent (lit_fraction < 0.35),
                    # add a subtle glow to the dark side
                    if lit_fraction < 0.35:
                        # Stronger earthshine when less is lit
                        es_strength = 0.12 * (1.0 - lit_fraction / 0.35)
                        c = (min(255, int(lit_base[0] * es_strength)),
                             min(255, int(lit_base[1] * es_strength)),
                             min(255, int(lit_base[2] * es_strength)))
                    else:
                        c = dark_base

                d.set_pixel(CX + dx, CY + dy, c)

        # --- Horizon silhouette ---
        for x in range(64):
            h = HORIZON[x]
            for row_off in range(h + 1):
                y = 63 - row_off
                d.set_pixel(x, y, (2, 2, 4))

        # --- Label ---
        if self.live_mode:
            phase_name = _phase_name_from_angle(angle)
            day = _day_from_angle(angle)
        else:
            phase_name = PHASES[self.phase_idx][0]
            day = PHASE_DAYS[self.phase_idx]

        phase_cycle = int(self.label_timer / 4) % 2
        if phase_cycle == 0:
            label = phase_name
        else:
            label = f"DAY {day:.0f} OF 29"

        if not hasattr(self, '_last_label_phase') or self._last_label_phase != phase_cycle:
            self._last_label_phase = phase_cycle
            self.scroll_offset = 0

        # Position label above the horizon (row 56 instead of 58)
        label_y = 55
        max_chars = 14
        if len(label) > max_chars:
            padded = label + "    " + label
            total_w = len(label + "    ") * 4
            offset = int(self.scroll_offset) % total_w
            d.draw_text_small(2 - offset, label_y, padded, Colors.WHITE)
        else:
            d.draw_text_small(2, label_y, label, Colors.WHITE)

        # --- "LIVE" overlay ---
        if self.live_mode and self.live_overlay_timer > 0:
            alpha = min(1.0, self.live_overlay_timer / 0.5)
            c = (int(80 * alpha), int(200 * alpha), int(80 * alpha))
            d.draw_text_small(2, 2, "LIVE", c)

        # --- Palette overlay ---
        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            c = (int(200 * alpha), int(200 * alpha), int(200 * alpha))
            pal_y = 2 if not (self.live_mode and self.live_overlay_timer > 0) else 8
            d.draw_text_small(2, pal_y, pal_name, c)
