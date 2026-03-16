"""
Swiss Watch Movement
====================
Five-gear watch train (barrel → center → third → fourth → escape)
with balance wheel, hairspring, pallet fork, and clock hands.
Circular watch case with skeleton dial — gears visible through the face.

Controls:
  Left/Right - Adjust rotation speed
"""

import math
from . import Visual, Display, Colors, GRID_SIZE


# Metallic palette
BRASS = (200, 170, 60)
BRASS_DARK = (140, 120, 40)
BRASS_TOOTH = (220, 190, 80)
STEEL = (170, 175, 185)
STEEL_DARK = (120, 125, 135)
STEEL_TOOTH = (195, 200, 210)
COPPER = (190, 120, 70)
COPPER_DARK = (140, 85, 45)
COPPER_TOOTH = (215, 145, 95)
SILVER = (200, 200, 210)
SILVER_DARK = (150, 150, 160)
SILVER_TOOTH = (225, 225, 235)
GOLD = (218, 190, 80)
GOLD_DARK = (160, 135, 50)
GOLD_TOOTH = (240, 215, 110)
JEWEL = (180, 20, 40)
JEWEL_HIGHLIGHT = (255, 80, 100)
HUB_COLOR = (90, 90, 100)
PLATE_COLOR = (25, 25, 30)

# Watch case
BEZEL_COLOR = (150, 145, 130)
BEZEL_HIGHLIGHT = (180, 175, 160)
MARKER_COLOR = (200, 195, 180)
MARKER_BRIGHT = (240, 235, 210)

# Balance wheel and hairspring
BALANCE_RIM = (180, 180, 195)
BALANCE_BAR = (200, 200, 215)
HAIRSPRING_COLOR = (120, 140, 180)
HAND_MINUTE = (255, 255, 255)
HAND_HOUR = (200, 200, 210)
HAND_CENTER = (255, 255, 255)

# Pallet fork
FORK_COLOR = STEEL
FORK_DARK = STEEL_DARK
PALLET_COLOR = JEWEL

# Watch case geometry — nearly fills the 64x64 panel
CASE_CX = 32
CASE_CY = 32
CASE_R = 30       # outer bezel edge
FACE_R = 28       # inner face radius
MARKER_R = 25     # hour marker radius

# Gear definitions: 5-gear watch train
# Barrel positioned so center wheel lands at (32, 32) = watch center
GEARS = [
    # 0 Barrel: mainspring, largest, slowest
    {"teeth": 8, "r": 8, "cx": 27, "cy": 18,
     "body": BRASS, "dark": BRASS_DARK, "tooth": BRASS_TOOTH},
    # 1 Center: minute-hand shaft (lands at watch center)
    {"teeth": 7, "r": 7, "cx": 32, "cy": 32,
     "body": STEEL, "dark": STEEL_DARK, "tooth": STEEL_TOOTH},
    # 2 Third: intermediate
    {"teeth": 6, "r": 6, "cx": 0, "cy": 0,
     "body": COPPER, "dark": COPPER_DARK, "tooth": COPPER_TOOTH},
    # 3 Fourth: second-hand speed
    {"teeth": 5, "r": 5, "cx": 0, "cy": 0,
     "body": SILVER, "dark": SILVER_DARK, "tooth": SILVER_TOOTH},
    # 4 Escape: fastest, drives balance wheel
    {"teeth": 4, "r": 4, "cx": 0, "cy": 0,
     "body": GOLD, "dark": GOLD_DARK, "tooth": GOLD_TOOTH},
]

MESHES = [(0, 1), (1, 2), (2, 3), (3, 4)]
MESH_ANGLES = [1.2, 0.5, -0.8, -2.0]


def _compute_positions():
    """Position gears along the train using mesh angles."""
    for i, (driver_idx, driven_idx) in enumerate(MESHES):
        gd = GEARS[driver_idx]
        gv = GEARS[driven_idx]
        angle = MESH_ANGLES[i]
        dist = gd["r"] + gv["r"]
        gv["cx"] = int(round(gd["cx"] + dist * math.cos(angle)))
        gv["cy"] = int(round(gd["cy"] + dist * math.sin(angle)))


_compute_positions()

# Balance wheel: near escape wheel
_esc = GEARS[4]
BALANCE_CX = _esc["cx"] + 2
BALANCE_CY = _esc["cy"] - 6
BALANCE_R = 4

# Speed levels: barrel RPM
SPEED_RPMS = [1, 2, 4, 6, 8, 10]


class WatchGears(Visual):
    name = "WATCH"
    description = "Swiss watch movement"
    category = "mechanics"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed_level = 3
        self.base_speed = SPEED_RPMS[self.speed_level - 1] * 2.0 * math.pi / 60.0

        # Rotation ratios: linear chain, each mesh reverses direction
        self.ratios = [0.0] * len(GEARS)
        self.ratios[0] = 1.0
        for i, (driver_idx, driven_idx) in enumerate(MESHES):
            self.ratios[driven_idx] = self.ratios[driver_idx] * (
                -GEARS[driver_idx]["teeth"] / GEARS[driven_idx]["teeth"]
            )

        # Phase offsets for proper tooth meshing
        self.phase_offsets = [0.0] * len(GEARS)
        self._calibrate_phases()

        self.rotations = list(self.phase_offsets)

        # Balance wheel oscillation
        self.balance_phase = 0.0

        # Clock hands
        self.minute_angle = 0.0
        self.hour_angle = 0.0

    def _calibrate_phases(self):
        """Calculate phase offsets so gear teeth mesh at contact points."""
        for driver_idx, driven_idx in MESHES:
            gd = GEARS[driver_idx]
            gv = GEARS[driven_idx]
            alpha = math.atan2(gv["cy"] - gd["cy"], gv["cx"] - gd["cx"])
            beta = alpha + math.pi
            self.phase_offsets[driven_idx] = (
                beta + (alpha - self.phase_offsets[driver_idx]) * gd["teeth"] / gv["teeth"]
            )

    def handle_input(self, input_state):
        consumed = False
        if input_state.right_pressed:
            self.speed_level = min(6, self.speed_level + 1)
            self.base_speed = SPEED_RPMS[self.speed_level - 1] * 2.0 * math.pi / 60.0
            consumed = True
        elif input_state.left_pressed:
            self.speed_level = max(1, self.speed_level - 1)
            self.base_speed = SPEED_RPMS[self.speed_level - 1] * 2.0 * math.pi / 60.0
            consumed = True
        return consumed

    def update(self, dt):
        self.time += dt
        for i in range(len(GEARS)):
            self.rotations[i] += self.base_speed * self.ratios[i] * dt

        # Balance wheel: 2 oscillations per escape wheel revolution
        escape_speed = abs(self.base_speed * self.ratios[4])
        self.balance_phase += escape_speed * 2.0 * dt

        # Clock hands track center wheel (gear 1), negated for clockwise
        center_delta = self.base_speed * self.ratios[1] * dt
        self.minute_angle -= center_delta
        self.hour_angle -= center_delta / 12.0

    def draw(self):
        d = self.display
        d.clear((0, 0, 0))

        self._draw_case_plate(d)
        self._draw_gears(d)
        self._draw_jewels(d)
        self._draw_pallet_fork(d)
        self._draw_hairspring(d)
        self._draw_balance_wheel(d)
        self._draw_hour_markers(d)
        self._draw_clock_hands(d)
        self._draw_bezel(d)

    # ── Watch case ────────────────────────────────────────────────

    def _draw_case_plate(self, d):
        """Fill the watch case interior with movement plate color."""
        cx, cy = CASE_CX, CASE_CY
        r_sq = FACE_R * FACE_R
        for y in range(max(0, cy - FACE_R), min(64, cy + FACE_R + 1)):
            dy_sq = (y - cy) ** 2
            for x in range(max(0, cx - FACE_R), min(64, cx + FACE_R + 1)):
                if (x - cx) ** 2 + dy_sq <= r_sq:
                    d.set_pixel(x, y, PLATE_COLOR)

    def _draw_bezel(self, d):
        """Draw the circular watch case bezel ring."""
        cx, cy = CASE_CX, CASE_CY
        inner_sq = FACE_R * FACE_R
        outer_sq = CASE_R * CASE_R
        for y in range(max(0, cy - CASE_R), min(64, cy + CASE_R + 1)):
            dy = y - cy
            dy_sq = dy * dy
            for x in range(max(0, cx - CASE_R), min(64, cx + CASE_R + 1)):
                dist_sq = (x - cx) ** 2 + dy_sq
                if inner_sq < dist_sq <= outer_sq:
                    # Upper half slightly brighter for dimension
                    d.set_pixel(x, y, BEZEL_HIGHLIGHT if dy < 0 else BEZEL_COLOR)

    def _draw_hour_markers(self, d):
        """Draw 12 hour markers around the watch face."""
        cx, cy = CASE_CX, CASE_CY
        for h in range(12):
            angle = h * math.pi / 6.0 - math.pi / 2.0  # 12 o'clock at top
            # Major markers (12, 3, 6, 9) are longer
            if h % 3 == 0:
                r_start, r_end = MARKER_R - 2, MARKER_R + 1
                color = MARKER_BRIGHT
            else:
                r_start, r_end = MARKER_R - 1, MARKER_R + 1
                color = MARKER_COLOR
            for r in range(r_start, r_end + 1):
                px = int(round(cx + r * math.cos(angle)))
                py = int(round(cy + r * math.sin(angle)))
                if 0 <= px < 64 and 0 <= py < 64:
                    d.set_pixel(px, py, color)

    def _draw_clock_hands(self, d):
        """Draw properly-sized minute and hour hands from watch center."""
        cx, cy = CASE_CX, CASE_CY

        # Hour hand (14px, silver)
        h_angle = self.hour_angle - math.pi / 2.0
        for t in range(15):
            px = int(round(cx + t * math.cos(h_angle)))
            py = int(round(cy + t * math.sin(h_angle)))
            if 0 <= px < 64 and 0 <= py < 64:
                d.set_pixel(px, py, HAND_HOUR)

        # Minute hand (22px, bright white)
        m_angle = self.minute_angle - math.pi / 2.0
        for t in range(23):
            px = int(round(cx + t * math.cos(m_angle)))
            py = int(round(cy + t * math.sin(m_angle)))
            if 0 <= px < 64 and 0 <= py < 64:
                d.set_pixel(px, py, HAND_MINUTE)

        # Center pip
        d.set_pixel(cx, cy, HAND_CENTER)
        d.set_pixel(cx - 1, cy, HAND_CENTER)
        d.set_pixel(cx + 1, cy, HAND_CENTER)
        d.set_pixel(cx, cy - 1, HAND_CENTER)
        d.set_pixel(cx, cy + 1, HAND_CENTER)

    # ── Gear train ────────────────────────────────────────────────

    def _draw_gears(self, d):
        """Render all gear bodies and teeth."""
        gear_info = []
        for gi, gear in enumerate(GEARS):
            r = gear["r"]
            hub_r_sq = max(2.0, r * 0.25) ** 2
            root_r = r - 1.5
            tip_r = r + 1.5
            gear_info.append((
                gear["cx"], gear["cy"],
                hub_r_sq,
                root_r, root_r * root_r,
                tip_r, tip_r * tip_r,
                gear["teeth"],
                self.rotations[gi],
                gear["body"], gear["dark"], gear["tooth"],
            ))

        min_x = max(0, min(g[0] - int(g[5]) - 2 for g in gear_info))
        max_x = min(63, max(g[0] + int(g[5]) + 2 for g in gear_info))
        min_y = max(0, min(g[1] - int(g[5]) - 2 for g in gear_info))
        max_y = min(63, max(g[1] + int(g[5]) + 2 for g in gear_info))

        TWO_PI = 2.0 * math.pi
        for py in range(min_y, max_y + 1):
            for px in range(min_x, max_x + 1):
                best_color = None
                best_dist_sq = 1e9

                for gcx, gcy, hub_r_sq, root_r, root_r_sq, tip_r, tip_r_sq, n_teeth, rotation, body, dark, tooth in gear_info:
                    dx = px - gcx
                    dy = py - gcy
                    dist_sq = dx * dx + dy * dy

                    if dist_sq > tip_r_sq:
                        continue

                    color = None
                    if dist_sq <= hub_r_sq:
                        color = HUB_COLOR
                    elif dist_sq <= root_r_sq:
                        if dist_sq > (root_r - 1) * (root_r - 1):
                            color = dark
                        else:
                            color = body
                    else:
                        angle = math.atan2(dy, dx) - rotation
                        tooth_phase = (angle * n_teeth / TWO_PI) % 1.0
                        if tooth_phase < 0:
                            tooth_phase += 1.0
                        if tooth_phase < 0.5:
                            color = tooth

                    if color is not None and dist_sq < best_dist_sq:
                        best_color = color
                        best_dist_sq = dist_sq

                if best_color is not None:
                    d.set_pixel(px, py, best_color)

    def _draw_jewels(self, d):
        """Draw jewel bearings at each gear center."""
        for gear in GEARS:
            gcx, gcy = gear["cx"], gear["cy"]
            d.set_pixel(gcx, gcy, JEWEL)
            d.set_pixel(gcx - 1, gcy, JEWEL)
            d.set_pixel(gcx + 1, gcy, JEWEL)
            d.set_pixel(gcx, gcy - 1, JEWEL)
            d.set_pixel(gcx, gcy + 1, JEWEL)
            d.set_pixel(gcx - 1, gcy - 1, JEWEL_HIGHLIGHT)

    # ── Escapement ────────────────────────────────────────────────

    def _draw_pallet_fork(self, d):
        """Draw the pallet fork between escape and balance wheels."""
        esc = GEARS[4]
        esc_cx, esc_cy = esc["cx"], esc["cy"]

        fork_px = (esc_cx + BALANCE_CX) // 2 + 1
        fork_py = (esc_cy + BALANCE_CY) // 2

        swing = math.sin(self.balance_phase) * (15.0 * math.pi / 180.0)

        # Fork body toward escape wheel
        arm_len = 5
        arm_angle = math.atan2(esc_cy - fork_py, esc_cx - fork_px) + swing

        for t in range(arm_len + 1):
            px = int(round(fork_px + t * math.cos(arm_angle)))
            py = int(round(fork_py + t * math.sin(arm_angle)))
            if 0 <= px < 64 and 0 <= py < 64:
                d.set_pixel(px, py, FORK_COLOR)

        # Two ruby pallet stones at the tip
        tip_x = fork_px + arm_len * math.cos(arm_angle)
        tip_y = fork_py + arm_len * math.sin(arm_angle)
        perp_angle = arm_angle + math.pi / 2

        for sign in (-1, 1):
            for t in range(1, 3):
                px = int(round(tip_x + sign * t * math.cos(perp_angle)))
                py = int(round(tip_y + sign * t * math.sin(perp_angle)))
                if 0 <= px < 64 and 0 <= py < 64:
                    d.set_pixel(px, py, PALLET_COLOR)

        # Impulse pin toward balance wheel
        imp_angle = math.atan2(BALANCE_CY - fork_py, BALANCE_CX - fork_px) + swing * 0.5
        for t in range(1, 4):
            px = int(round(fork_px + t * math.cos(imp_angle)))
            py = int(round(fork_py + t * math.sin(imp_angle)))
            if 0 <= px < 64 and 0 <= py < 64:
                d.set_pixel(px, py, FORK_DARK)

        # Flash on tick
        tick = abs(math.sin(self.balance_phase)) < 0.15
        if tick:
            d.set_pixel(int(tip_x), int(tip_y), JEWEL_HIGHLIGHT)

        d.set_pixel(fork_px, fork_py, JEWEL)

    def _draw_balance_wheel(self, d):
        """Draw oscillating balance wheel with rim and crossbar."""
        cx, cy = BALANCE_CX, BALANCE_CY
        r = BALANCE_R
        swing = math.sin(self.balance_phase) * (75.0 * math.pi / 180.0)

        # Rim circle
        for a_step in range(32):
            a = a_step * 2.0 * math.pi / 32
            px = int(round(cx + r * math.cos(a)))
            py = int(round(cy + r * math.sin(a)))
            if 0 <= px < 64 and 0 <= py < 64:
                d.set_pixel(px, py, BALANCE_RIM)

        # Oscillating crossbar
        for t in range(-r, r + 1):
            px = int(round(cx + t * math.cos(swing)))
            py = int(round(cy + t * math.sin(swing)))
            if 0 <= px < 64 and 0 <= py < 64:
                d.set_pixel(px, py, BALANCE_BAR)

        d.set_pixel(cx, cy, JEWEL)

    def _draw_hairspring(self, d):
        """Draw ~2-turn spiral around balance wheel that coils/uncoils."""
        cx, cy = BALANCE_CX, BALANCE_CY
        swing = math.sin(self.balance_phase) * (75.0 * math.pi / 180.0)
        turns = 2.0
        steps = 48
        max_r = BALANCE_R - 0.5
        min_r = 0.8

        for i in range(steps):
            frac = i / float(steps)
            theta = frac * turns * 2.0 * math.pi + swing
            radius = min_r + (max_r - min_r) * frac
            px = int(round(cx + radius * math.cos(theta)))
            py = int(round(cy + radius * math.sin(theta)))
            if 0 <= px < 64 and 0 <= py < 64:
                d.set_pixel(px, py, HAIRSPRING_COLOR)
