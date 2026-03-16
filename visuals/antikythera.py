"""
Antikythera Mechanism
=====================
Ancient Greek hand-powered orrery (c. 100 BC) — the first analog computer.
Dense bronze gear train in a rectangular case encoding astronomical cycles:
the Metonic cycle (19 years = 235 lunar months) and the Saros eclipse cycle
(~223 synodic months ≈ 18 years). Discovered in 1901 in an Aegean shipwreck.

The large central drive wheel dominates, with gear trains branching to
calendar, lunar, and eclipse sub-mechanisms — all tightly packed as in
the original device.

Controls:
  Left/Right - Adjust rotation speed
"""

import math
from . import Visual, Display, Colors, GRID_SIZE


# Ancient bronze / verdigris palette
BRONZE = (180, 140, 60)
BRONZE_DARK = (140, 110, 50)
BRONZE_LIGHT = (200, 160, 80)
BRONZE_TOOTH = (190, 150, 70)
AGED_BRONZE = (140, 110, 50)
VERDIGRIS = (80, 140, 120)
VERDIGRIS_DARK = (60, 110, 95)
VERDIGRIS_LIGHT = (100, 160, 140)
PATINA = (90, 130, 110)
COPPER_OLD = (160, 100, 60)

# Case and plate
CASE_EDGE = (70, 65, 50)
CASE_CORNER = (80, 75, 55)
PLATE_BG = (30, 28, 20)
RIVET = (110, 100, 70)

# Front dial
DIAL_RING = (120, 100, 50)
DIAL_MARK = (160, 140, 70)
POINTER_COLOR = (200, 170, 80)
POINTER_TIP = (220, 190, 100)
MOON_POINTER = VERDIGRIS_LIGHT
HUB_COLOR = (70, 65, 50)


# Gear definitions: tooth counts encode astronomical periods
# 19 = Metonic years, 12 ≈ months/year, 15 = lunar intermediate
GEARS = [
    # 0: Main drive (b1) — large central gear
    {"teeth": 19, "r": 11, "cx": 32, "cy": 30,
     "body": BRONZE, "dark": BRONZE_DARK, "tooth": BRONZE_TOOTH},
    # 1: Sun transfer — 12 teeth (months/year)
    {"teeth": 12, "r": 6, "cx": 0, "cy": 0,
     "body": AGED_BRONZE, "dark": BRONZE_DARK, "tooth": BRONZE_LIGHT},
    # 2: Moon intermediate — 15 teeth
    {"teeth": 15, "r": 5, "cx": 0, "cy": 0,
     "body": BRONZE, "dark": BRONZE_DARK, "tooth": BRONZE_TOOTH},
    # 3: Eclipse gear — 8 teeth
    {"teeth": 8, "r": 4, "cx": 0, "cy": 0,
     "body": VERDIGRIS, "dark": VERDIGRIS_DARK, "tooth": VERDIGRIS_LIGHT},
    # 4: Metonic calendar — 19 teeth
    {"teeth": 19, "r": 8, "cx": 0, "cy": 0,
     "body": PATINA, "dark": VERDIGRIS_DARK, "tooth": VERDIGRIS_LIGHT},
    # 5: Saros train — 10 teeth
    {"teeth": 10, "r": 4, "cx": 0, "cy": 0,
     "body": COPPER_OLD, "dark": BRONZE_DARK, "tooth": BRONZE_LIGHT},
    # 6: Planetary display — 7 teeth
    {"teeth": 7, "r": 3, "cx": 0, "cy": 0,
     "body": AGED_BRONZE, "dark": BRONZE_DARK, "tooth": BRONZE_TOOTH},
]

# Mesh relationships (gear trains — tree structure)
MESHES = [
    (0, 1),  # Main → Sun
    (1, 2),  # Sun → Moon
    (2, 3),  # Moon → Eclipse
    (0, 4),  # Main → Calendar
    (4, 5),  # Calendar → Saros
    (1, 6),  # Sun → Planetary
]

# Mesh angles: direction from driver center to driven center (radians)
MESH_ANGLES = [-1.1, 0.5, 1.3, 2.2, -2.5, -2.5]


def _compute_positions():
    """Position gears using mesh angles from the main drive gear."""
    positioned = {0}
    for _ in range(len(GEARS)):
        for i, (di, dv) in enumerate(MESHES):
            if di in positioned and dv not in positioned:
                gd = GEARS[di]
                gv = GEARS[dv]
                dist = gd["r"] + gv["r"]
                angle = MESH_ANGLES[i]
                gv["cx"] = int(round(gd["cx"] + dist * math.cos(angle)))
                gv["cy"] = int(round(gd["cy"] + dist * math.sin(angle)))
                positioned.add(dv)


_compute_positions()

# Case bounds (computed from gear extents + padding)
_PAD = 4
CASE_X0 = max(0, min(g["cx"] - g["r"] for g in GEARS) - _PAD)
CASE_X1 = min(63, max(g["cx"] + g["r"] for g in GEARS) + _PAD)
CASE_Y0 = max(0, min(g["cy"] - g["r"] for g in GEARS) - _PAD)
CASE_Y1 = min(63, max(g["cy"] + g["r"] for g in GEARS) + _PAD)

# Front zodiac dial: concentric with main gear, slightly larger
DIAL_CX = GEARS[0]["cx"]
DIAL_CY = GEARS[0]["cy"]
DIAL_R = 15

# Speed levels
SPEED_LEVELS = [0.5, 1.0, 2.0, 4.0, 6.0, 10.0]


class Antikythera(Visual):
    name = "ANTIKYTHERA"
    description = "Ancient Greek analog computer"
    category = "mechanics"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed_level = 2
        self.base_speed = SPEED_LEVELS[self.speed_level] * 2.0 * math.pi / 60.0

        self.ratios = [1.0] * len(GEARS)
        self._compute_ratios()

        self.phase_offsets = [0.0] * len(GEARS)
        self._calibrate_phases()

        self.rotations = list(self.phase_offsets)

        # Dial pointer angles
        self.zodiac_angle = 0.0
        self.moon_angle = 0.0

    def _compute_ratios(self):
        """Compute rotation ratios propagated through the mesh tree."""
        processed = {0}
        for _ in range(len(GEARS)):
            for driver_idx, driven_idx in MESHES:
                if driver_idx in processed and driven_idx not in processed:
                    self.ratios[driven_idx] = self.ratios[driver_idx] * (
                        -GEARS[driver_idx]["teeth"] / GEARS[driven_idx]["teeth"]
                    )
                    processed.add(driven_idx)

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

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.right_pressed:
            self.speed_level = min(len(SPEED_LEVELS) - 1, self.speed_level + 1)
            self.base_speed = SPEED_LEVELS[self.speed_level] * 2.0 * math.pi / 60.0
            consumed = True
        elif input_state.left_pressed:
            self.speed_level = max(0, self.speed_level - 1)
            self.base_speed = SPEED_LEVELS[self.speed_level] * 2.0 * math.pi / 60.0
            consumed = True
        return consumed

    def update(self, dt):
        self.time += dt
        for i in range(len(GEARS)):
            self.rotations[i] += self.base_speed * self.ratios[i] * dt

        # Zodiac pointer: tracks main gear (1 rev / year)
        self.zodiac_angle = self.rotations[0]
        # Moon pointer: 235/19 revolutions per year (Metonic cycle)
        self.moon_angle = self.rotations[0] * (235.0 / 19.0)

    def draw(self):
        d = self.display
        d.clear((0, 0, 0))

        self._draw_case(d)
        self._draw_gears(d)
        self._draw_front_dial(d)
        self._draw_patina(d)

    # ── Case ──────────────────────────────────────────────────────

    def _draw_case(self, d):
        """Draw rectangular bronze case with rivets."""
        x0, x1 = CASE_X0, CASE_X1
        y0, y1 = CASE_Y0, CASE_Y1

        # Fill case interior
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                d.set_pixel(x, y, PLATE_BG)

        # Case edge border
        for x in range(x0, x1 + 1):
            d.set_pixel(x, y0, CASE_EDGE)
            d.set_pixel(x, y1, CASE_EDGE)
        for y in range(y0, y1 + 1):
            d.set_pixel(x0, y, CASE_EDGE)
            d.set_pixel(x1, y, CASE_EDGE)

        # Brighter corners
        for rx, ry in [(x0, y0), (x1, y0), (x0, y1), (x1, y1)]:
            d.set_pixel(rx, ry, CASE_CORNER)

        # Corner rivets (inset 2px)
        for rx, ry in [(x0 + 2, y0 + 2), (x1 - 2, y0 + 2),
                       (x0 + 2, y1 - 2), (x1 - 2, y1 - 2)]:
            d.set_pixel(rx, ry, RIVET)

    # ── Gears ─────────────────────────────────────────────────────

    def _draw_gears(self, d):
        """Render all gear bodies and teeth."""
        TWO_PI = 2.0 * math.pi

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

    # ── Front dial ────────────────────────────────────────────────

    def _draw_front_dial(self, d):
        """Draw the zodiac/calendar dial ring with sun and moon pointers."""
        cx, cy = DIAL_CX, DIAL_CY
        r = DIAL_R

        # Dial ring (2px wide)
        for step in range(80):
            a = step * 2.0 * math.pi / 80
            for dr in range(2):
                px = int(round(cx + (r + dr) * math.cos(a)))
                py = int(round(cy + (r + dr) * math.sin(a)))
                if 0 <= px < 64 and 0 <= py < 64:
                    d.set_pixel(px, py, DIAL_RING)

        # 12 zodiac division marks (outside the ring)
        for i in range(12):
            a = i * math.pi / 6.0
            for dr in range(2, 4):
                px = int(round(cx + (r + dr) * math.cos(a)))
                py = int(round(cy + (r + dr) * math.sin(a)))
                if 0 <= px < 64 and 0 <= py < 64:
                    d.set_pixel(px, py, DIAL_MARK)

        pointer_len = r - 2

        # Sun / zodiac pointer (gold, 1 revolution per year)
        angle = self.zodiac_angle
        for t in range(pointer_len + 1):
            frac = t / float(pointer_len)
            px = int(round(cx + t * math.cos(angle)))
            py = int(round(cy + t * math.sin(angle)))
            if 0 <= px < 64 and 0 <= py < 64:
                d.set_pixel(px, py, POINTER_TIP if frac > 0.7 else POINTER_COLOR)

        # Moon pointer (verdigris, faster — Metonic ratio 235:19)
        moon_len = pointer_len - 3
        angle = self.moon_angle
        for t in range(moon_len + 1):
            px = int(round(cx + t * math.cos(angle)))
            py = int(round(cy + t * math.sin(angle)))
            if 0 <= px < 64 and 0 <= py < 64:
                d.set_pixel(px, py, MOON_POINTER)

        # Hub
        d.set_pixel(cx, cy, BRONZE_LIGHT)

    # ── Patina ────────────────────────────────────────────────────

    def _draw_patina(self, d):
        """Draw subtle verdigris corrosion on empty case areas."""
        pulse = 0.8 + 0.2 * math.sin(self.time * 0.5)

        # Patina spots on exposed plate
        patina_spots = [
            (CASE_X0 + 2, CASE_Y0 + 4),
            (CASE_X1 - 3, CASE_Y0 + 3),
            (CASE_X0 + 3, CASE_Y1 - 3),
            (CASE_X1 - 2, CASE_Y1 - 4),
            (CASE_X0 + 4, (CASE_Y0 + CASE_Y1) // 2),
            (CASE_X1 - 4, (CASE_Y0 + CASE_Y1) // 2),
        ]

        for sx, sy in patina_spots:
            if 0 <= sx < 64 and 0 <= sy < 64:
                existing = d.get_pixel(sx, sy)
                if existing == PLATE_BG or sum(existing) < 120:
                    color = (
                        int(VERDIGRIS[0] * pulse),
                        int(VERDIGRIS[1] * pulse),
                        int(VERDIGRIS[2] * pulse),
                    )
                    d.set_pixel(sx, sy, color)

        # Small label at bottom of case
        d.draw_text_small(CASE_X0 + 1, CASE_Y1 - 6, "100 BC", DIAL_MARK)
