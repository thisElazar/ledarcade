"""
Swiss Watch Movement
====================
Meshing gears with visible teeth, jewel bearings, and metallic colors.
Gears mesh properly — teeth interleave without overlapping.

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
JEWEL = (180, 20, 40)
JEWEL_HIGHLIGHT = (255, 80, 100)
HUB_COLOR = (90, 90, 100)
PLATE_COLOR = (25, 25, 30)


# Gear definitions
# Module m=2: pitch_radius = num_teeth (for rendering purposes)
# Center distance for meshing = r1 + r2

GEARS = [
    # Gear A: 12 teeth, r=12, large drive gear
    {"teeth": 12, "r": 12, "cx": 22, "cy": 32, "body": BRASS, "dark": BRASS_DARK, "tooth": BRASS_TOOTH},
    # Gear B: 8 teeth, r=8, meshes with A
    {"teeth": 8, "r": 8, "cx": 42, "cy": 32, "body": STEEL, "dark": STEEL_DARK, "tooth": STEEL_TOOTH},
    # Gear C: 6 teeth, r=6, meshes with B
    {"teeth": 6, "r": 6, "cx": 52, "cy": 20, "body": COPPER, "dark": COPPER_DARK, "tooth": COPPER_TOOTH},
    # Gear D: 5 teeth, r=5, meshes with A
    {"teeth": 5, "r": 5, "cx": 15, "cy": 49, "body": SILVER, "dark": SILVER_DARK, "tooth": SILVER_TOOTH},
]

# Mesh relationships: (driver_idx, driven_idx)
MESHES = [(0, 1), (1, 2), (0, 3)]


def _compute_center_distances():
    """Adjust gear positions so meshing gears have correct center distance."""
    # A-B: r_A + r_B = 12 + 8 = 20
    GEARS[1]["cx"] = GEARS[0]["cx"] + GEARS[0]["r"] + GEARS[1]["r"]
    GEARS[1]["cy"] = GEARS[0]["cy"]

    # B-C: r_B + r_C = 8 + 6 = 14
    angle_bc = -1.1
    dist_bc = GEARS[1]["r"] + GEARS[2]["r"]
    GEARS[2]["cx"] = int(round(GEARS[1]["cx"] + dist_bc * math.cos(angle_bc)))
    GEARS[2]["cy"] = int(round(GEARS[1]["cy"] + dist_bc * math.sin(angle_bc)))

    # A-D: r_A + r_D = 12 + 5 = 17
    angle_ad = 2.0
    dist_ad = GEARS[0]["r"] + GEARS[3]["r"]
    GEARS[3]["cx"] = int(round(GEARS[0]["cx"] + dist_ad * math.cos(angle_ad)))
    GEARS[3]["cy"] = int(round(GEARS[0]["cy"] + dist_ad * math.sin(angle_ad)))


_compute_center_distances()


class WatchGears(Visual):
    name = "WATCH"
    description = "Swiss watch movement"
    category = "mechanics"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed_level = 3   # 1-6
        self.base_speed = self.speed_level * 0.18

        # Rotation ratios (alternating direction through mesh chain)
        self.ratios = [0.0] * len(GEARS)
        self.ratios[0] = 1.0
        self.ratios[1] = -GEARS[0]["teeth"] / GEARS[1]["teeth"]   # -1.5
        self.ratios[2] = self.ratios[1] * (-GEARS[1]["teeth"] / GEARS[2]["teeth"])  # 2.0
        self.ratios[3] = -GEARS[0]["teeth"] / GEARS[3]["teeth"]   # -2.4

        # Phase offsets for teeth to mesh at contact points
        self.phase_offsets = [0.0] * len(GEARS)
        self._calibrate_phases()

        # Accumulated rotation angles — avoids jumps when speed changes
        self.rotations = list(self.phase_offsets)

    def _calibrate_phases(self):
        """Calculate phase offsets so gear teeth mesh at each contact point.

        The gear ratio makes tooth phases at the contact point change at
        equal and opposite rates, so phi_driver + phi_driven = const.
        For correct meshing that constant must be 0 (mod 1): when one
        gear reads 0.3 (tooth) the other reads 0.7 (gap).

        Process MESHES in order so each driver's offset is already set.
        """
        for driver_idx, driven_idx in MESHES:
            gd = GEARS[driver_idx]
            gv = GEARS[driven_idx]

            # Contact angle from driver center toward driven center
            alpha = math.atan2(gv["cy"] - gd["cy"], gv["cx"] - gd["cx"])
            beta = alpha + math.pi  # same point, from driven's perspective

            # Solve for offset_v such that phi_d + phi_v = 0 (mod 1):
            #   phi_d = ((alpha - off_d) * Nd / 2pi) % 1
            #   phi_v = ((beta  - off_v) * Nv / 2pi) % 1
            #   => off_v = beta + (alpha - off_d) * Nd / Nv
            self.phase_offsets[driven_idx] = (
                beta + (alpha - self.phase_offsets[driver_idx]) * gd["teeth"] / gv["teeth"]
            )

    def handle_input(self, input_state):
        consumed = False
        if input_state.right_pressed:
            self.speed_level = min(6, self.speed_level + 1)
            self.base_speed = self.speed_level * 0.18
            consumed = True
        elif input_state.left_pressed:
            self.speed_level = max(1, self.speed_level - 1)
            self.base_speed = self.speed_level * 0.18
            consumed = True
        return consumed

    def update(self, dt):
        self.time += dt
        # Accumulate rotation incrementally so speed changes are smooth
        for i in range(len(GEARS)):
            self.rotations[i] += self.base_speed * self.ratios[i] * dt

    def draw(self):
        d = self.display
        d.clear(PLATE_COLOR)

        # Pre-compute per-gear rendering constants
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

        # Bounding box union of all gears
        min_x = max(0, min(g[0] - int(g[5]) - 2 for g in gear_info))
        max_x = min(63, max(g[0] + int(g[5]) + 2 for g in gear_info))
        min_y = max(0, min(g[1] - int(g[5]) - 2 for g in gear_info))
        max_y = min(63, max(g[1] + int(g[5]) + 2 for g in gear_info))

        # Render: for each pixel, the closest gear that claims it wins.
        # This prevents teeth from two meshing gears from overlapping —
        # each gear's teeth only extend into the half of the mesh zone
        # closest to its own center, naturally interleaving with the other.
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
                        # Gear body — darken near edge
                        if dist_sq > (root_r - 1) * (root_r - 1):
                            color = dark
                        else:
                            color = body
                    else:
                        # Tooth region — check tooth/gap pattern
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

        # Jewel bearings on top
        for gear in GEARS:
            gcx, gcy = gear["cx"], gear["cy"]
            d.set_pixel(gcx, gcy, JEWEL)
            d.set_pixel(gcx - 1, gcy, JEWEL)
            d.set_pixel(gcx + 1, gcy, JEWEL)
            d.set_pixel(gcx, gcy - 1, JEWEL)
            d.set_pixel(gcx, gcy + 1, JEWEL)
            d.set_pixel(gcx - 1, gcy - 1, JEWEL_HIGHLIGHT)
