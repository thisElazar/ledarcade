"""
Antikythera Mechanism
=====================
Ancient Greek hand-powered orrery (c. 100 BC) - the first analog computer.
Cross-section view showing interlocking bronze gears that predict astronomical
positions and eclipses. Discovered in 1901 in an Aegean shipwreck.
Nothing comparable existed for 1500 years after its creation.

Controls:
  Left/Right - Adjust rotation speed
"""

import math
from . import Visual, Display, Colors, GRID_SIZE


# Ancient bronze/verdigris color palette
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

# Dial and pointer colors
DIAL_RING = (120, 100, 50)
DIAL_MARK = (160, 140, 70)
POINTER_COLOR = (200, 170, 80)
POINTER_TIP = (220, 190, 100)

# Background (aged bronze plate)
BACKGROUND = (30, 28, 20)
PLATE_EDGE = (60, 55, 40)

# Hub color
HUB_COLOR = (70, 65, 50)


# Gear definitions for the Antikythera mechanism
# The mechanism had multiple gear trains for sun, moon, and planet predictions
# Main train: input -> sun gear -> moon train -> eclipse predictor
GEARS = [
    # Main input gear (large, central-left)
    {"teeth": 12, "r": 11, "cx": 18, "cy": 32, "body": BRONZE, "dark": BRONZE_DARK, "tooth": BRONZE_TOOTH},
    # Sun gear (medium, center)
    {"teeth": 10, "r": 9,  "cx": 32, "cy": 20, "body": AGED_BRONZE, "dark": BRONZE_DARK, "tooth": BRONZE_LIGHT},
    # Moon gear (medium, right of sun)
    {"teeth": 8,  "r": 7,  "cx": 46, "cy": 14, "body": BRONZE, "dark": BRONZE_DARK, "tooth": BRONZE_TOOTH},
    # Eclipse gear (small, far right)
    {"teeth": 6,  "r": 5,  "cx": 56, "cy": 22, "body": VERDIGRIS, "dark": VERDIGRIS_DARK, "tooth": VERDIGRIS_LIGHT},
    # Calendar gear (large, bottom center)
    {"teeth": 14, "r": 12, "cx": 36, "cy": 46, "body": PATINA, "dark": VERDIGRIS_DARK, "tooth": VERDIGRIS_LIGHT},
    # Secondary moon train (small, bottom left)
    {"teeth": 7,  "r": 6,  "cx": 12, "cy": 50, "body": COPPER_OLD, "dark": BRONZE_DARK, "tooth": BRONZE_LIGHT},
    # Planetary gear (small, top center)
    {"teeth": 5,  "r": 4,  "cx": 32, "cy": 6,  "body": AGED_BRONZE, "dark": BRONZE_DARK, "tooth": BRONZE_TOOTH},
]

# Mesh relationships (gear trains)
# (driver, driven) - gears that interlock
MESHES = [
    (0, 1),  # Input -> Sun
    (1, 2),  # Sun -> Moon
    (2, 3),  # Moon -> Eclipse
    (0, 4),  # Input -> Calendar
    (4, 5),  # Calendar -> Secondary moon
    (1, 6),  # Sun -> Planetary
]

# Circular dials with pointers
DIALS = [
    # Sun position dial (top-left area)
    {"cx": 10, "cy": 12, "r": 8, "marks": 12, "pointer_len": 6, "name": "sun"},
    # Moon phase dial (top-right area)
    {"cx": 54, "cy": 8, "r": 6, "marks": 8, "pointer_len": 4, "name": "moon"},
    # Eclipse predictor dial (right side)
    {"cx": 58, "cy": 38, "r": 7, "marks": 6, "pointer_len": 5, "name": "eclipse"},
]

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
        self.speed_level = 2  # Start at medium speed
        self.base_speed = SPEED_LEVELS[self.speed_level] * 2.0 * math.pi / 60.0  # RPM to rad/s

        # Calculate rotation ratios based on mesh relationships
        # Gear ratio = -teeth_driver / teeth_driven (negative for direction reversal)
        self.ratios = [1.0] * len(GEARS)
        self._compute_ratios()

        # Phase offsets for proper tooth meshing
        self.phase_offsets = [0.0] * len(GEARS)
        self._calibrate_phases()

        # Accumulated rotation angles
        self.rotations = list(self.phase_offsets)

        # Dial pointer angles
        self.dial_angles = [0.0] * len(DIALS)

    def _compute_ratios(self):
        """Compute gear rotation ratios based on mesh relationships."""
        # Process meshes to propagate ratios
        processed = {0}  # Start with input gear (ratio = 1.0)

        # Iterate until all gears are processed
        for _ in range(len(GEARS)):
            for driver_idx, driven_idx in MESHES:
                if driver_idx in processed and driven_idx not in processed:
                    # Driven gear rotates opposite direction, scaled by tooth ratio
                    self.ratios[driven_idx] = self.ratios[driver_idx] * (
                        -GEARS[driver_idx]["teeth"] / GEARS[driven_idx]["teeth"]
                    )
                    processed.add(driven_idx)

    def _calibrate_phases(self):
        """Calculate phase offsets so gear teeth mesh properly at contact points."""
        for driver_idx, driven_idx in MESHES:
            gd = GEARS[driver_idx]
            gv = GEARS[driven_idx]

            # Angle from driver center to driven center
            alpha = math.atan2(gv["cy"] - gd["cy"], gv["cx"] - gd["cx"])
            beta = alpha + math.pi  # Opposite angle

            # Calculate phase offset for proper meshing
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

        # Update gear rotations
        for i in range(len(GEARS)):
            self.rotations[i] += self.base_speed * self.ratios[i] * dt

        # Update dial pointers (linked to specific gears)
        # Sun dial linked to sun gear (1)
        self.dial_angles[0] = self.rotations[1] * 0.5
        # Moon dial linked to moon gear (2)
        self.dial_angles[1] = self.rotations[2] * 0.7
        # Eclipse dial linked to eclipse gear (3)
        self.dial_angles[2] = self.rotations[3] * 0.3

    def draw(self):
        d = self.display
        d.clear(BACKGROUND)

        # Draw aged plate background with edge
        self._draw_plate_background(d)

        # Draw circular dials first (behind gears)
        self._draw_dials(d)

        # Draw all gears
        self._draw_gears(d)

        # Draw dial pointers (on top of gears)
        self._draw_pointers(d)

        # Draw some verdigris/corrosion patches for authenticity
        self._draw_patina(d)

    def _draw_plate_background(self, d):
        """Draw the aged bronze plate background."""
        # Subtle edge/frame
        for x in range(64):
            d.set_pixel(x, 0, PLATE_EDGE)
            d.set_pixel(x, 63, PLATE_EDGE)
        for y in range(64):
            d.set_pixel(0, y, PLATE_EDGE)
            d.set_pixel(63, y, PLATE_EDGE)

    def _draw_dials(self, d):
        """Draw circular dials with tick marks."""
        for dial in DIALS:
            cx, cy = dial["cx"], dial["cy"]
            r = dial["r"]
            n_marks = dial["marks"]

            # Draw dial ring (unfilled circle)
            for step in range(64):
                angle = step * 2.0 * math.pi / 64
                px = int(round(cx + r * math.cos(angle)))
                py = int(round(cy + r * math.sin(angle)))
                if 0 <= px < 64 and 0 <= py < 64:
                    d.set_pixel(px, py, DIAL_RING)

            # Draw tick marks around the dial
            for i in range(n_marks):
                angle = i * 2.0 * math.pi / n_marks
                # Outer tick position
                outer_x = int(round(cx + (r + 1) * math.cos(angle)))
                outer_y = int(round(cy + (r + 1) * math.sin(angle)))
                if 0 <= outer_x < 64 and 0 <= outer_y < 64:
                    d.set_pixel(outer_x, outer_y, DIAL_MARK)

    def _draw_gears(self, d):
        """Render all gear bodies and teeth."""
        TWO_PI = 2.0 * math.pi

        # Pre-compute gear rendering info
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

        # Determine bounding box for all gears
        min_x = max(0, min(g[0] - int(g[5]) - 2 for g in gear_info))
        max_x = min(63, max(g[0] + int(g[5]) + 2 for g in gear_info))
        min_y = max(0, min(g[1] - int(g[5]) - 2 for g in gear_info))
        max_y = min(63, max(g[1] + int(g[5]) + 2 for g in gear_info))

        # Render pixels
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
                        # Tooth region
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

    def _draw_pointers(self, d):
        """Draw rotating pointers on the dials."""
        for i, dial in enumerate(DIALS):
            cx, cy = dial["cx"], dial["cy"]
            pointer_len = dial["pointer_len"]
            angle = self.dial_angles[i]

            # Draw pointer as a line from center outward
            for t in range(pointer_len + 1):
                frac = t / float(pointer_len)
                px = int(round(cx + t * math.cos(angle)))
                py = int(round(cy + t * math.sin(angle)))
                if 0 <= px < 64 and 0 <= py < 64:
                    # Tip is brighter
                    if frac > 0.7:
                        d.set_pixel(px, py, POINTER_TIP)
                    else:
                        d.set_pixel(px, py, POINTER_COLOR)

            # Draw small hub at dial center
            d.set_pixel(cx, cy, BRONZE_LIGHT)

    def _draw_patina(self, d):
        """Draw subtle verdigris/corrosion patches for authenticity."""
        # Static patina spots (based on time for subtle shimmer)
        patina_spots = [
            (5, 28), (8, 45), (52, 52), (48, 4), (3, 58),
            (60, 48), (25, 58), (58, 28), (2, 2),
        ]

        pulse = 0.8 + 0.2 * math.sin(self.time * 0.5)

        for sx, sy in patina_spots:
            # Small cluster of patina pixels
            if 0 <= sx < 64 and 0 <= sy < 64:
                # Only draw if not already occupied by a bright gear pixel
                existing = d.get_pixel(sx, sy)
                if existing == BACKGROUND or sum(existing) < 150:
                    color = (
                        int(VERDIGRIS[0] * pulse),
                        int(VERDIGRIS[1] * pulse),
                        int(VERDIGRIS[2] * pulse),
                    )
                    d.set_pixel(sx, sy, color)
