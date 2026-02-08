"""
Turntable
=========
Top-down view of a spinning vinyl record with tonearm.
Concentric grooves rotate with light reflections sweeping across
the surface. Center label rotates with the disc.

Controls:
  Left/Right - Cycle RPM (33, 45, 78)
  Up/Down    - Cycle label color
"""

import math
from . import Visual, Display, Colors, GRID_SIZE


# Record geometry
CENTER_X = 32
CENTER_Y = 34
RECORD_R = 26
PLATTER_R_INNER = 27
PLATTER_R_OUTER = 28
LABEL_R_INNER = 4
LABEL_R_OUTER = 10

# Tonearm
ARM_PIVOT_X = 58
ARM_PIVOT_Y = 4
ARM_LENGTH_1 = 30   # upper arm segment
ARM_LENGTH_2 = 16   # lower arm segment (to stylus)

# RPM options
RPM_OPTIONS = [33, 45, 78]

# Colors
VINYL_DARK = (8, 8, 12)
VINYL_GROOVE = (18, 18, 25)
VINYL_HIGHLIGHT = (55, 55, 70)
PLATTER_COLOR = (50, 50, 55)
PLATTER_EDGE = (70, 70, 78)
ARM_COLOR = (180, 180, 190)
ARM_HIGHLIGHT = (220, 220, 230)
ARM_SHADOW = (120, 120, 130)
HEADSHELL_COLOR = (200, 200, 210)
STYLUS_COLOR = (255, 60, 60)
PIVOT_COLOR = (160, 160, 170)
HUD_COLOR = (160, 160, 170)

# Label color palettes: (primary, secondary, text)
LABEL_PALETTES = [
    ((200, 50, 50), (160, 30, 30), (255, 220, 180)),    # Red (classic)
    ((50, 80, 200), (30, 55, 160), (220, 230, 255)),    # Blue
    ((200, 160, 30), (160, 120, 20), (80, 50, 20)),     # Gold
    ((50, 160, 60), (30, 120, 40), (200, 255, 200)),    # Green
    ((180, 80, 200), (140, 50, 160), (240, 220, 255)),  # Purple
    ((220, 120, 30), (180, 90, 20), (255, 240, 200)),   # Orange
]


class Turntable(Visual):
    name = "TURNTABLE"
    description = "Spinning vinyl"
    category = "music"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.angle = 0.0           # Current disc rotation angle (radians)
        self.rpm_idx = 0           # Index into RPM_OPTIONS
        self.label_idx = 0         # Index into LABEL_PALETTES
        self.arm_progress = 0.0    # 0.0 = outer edge, 1.0 = inner label

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.right_pressed:
            self.rpm_idx = (self.rpm_idx + 1) % len(RPM_OPTIONS)
            consumed = True
        if input_state.left_pressed:
            self.rpm_idx = (self.rpm_idx - 1) % len(RPM_OPTIONS)
            consumed = True
        if input_state.up_pressed:
            self.label_idx = (self.label_idx + 1) % len(LABEL_PALETTES)
            consumed = True
        if input_state.down_pressed:
            self.label_idx = (self.label_idx - 1) % len(LABEL_PALETTES)
            consumed = True
        return consumed

    def update(self, dt: float):
        self.time += dt

        # Rotate disc based on RPM
        rpm = RPM_OPTIONS[self.rpm_idx]
        rps = rpm / 60.0  # revolutions per second
        self.angle += rps * 2.0 * math.pi * dt

        # Keep angle in [0, 2*pi)
        self.angle = self.angle % (2.0 * math.pi)

        # Tonearm slowly sweeps inward then resets
        self.arm_progress += dt * 0.008  # Very slow sweep
        if self.arm_progress > 1.0:
            self.arm_progress = 0.0

    def draw(self):
        d = self.display
        d.clear(Colors.BLACK)

        # -- Draw platter ring --
        self._draw_platter(d)

        # -- Draw vinyl record with grooves --
        self._draw_record(d)

        # -- Draw label --
        self._draw_label(d)

        # -- Draw center spindle --
        d.set_pixel(CENTER_X, CENTER_Y, PLATTER_EDGE)

        # -- Draw tonearm --
        self._draw_tonearm(d)

        # -- HUD: RPM display --
        rpm = RPM_OPTIONS[self.rpm_idx]
        d.draw_text_small(2, 2, f"{rpm} RPM", HUD_COLOR)

    def _draw_platter(self, d):
        """Draw the metallic platter ring around the record."""
        for y in range(CENTER_Y - PLATTER_R_OUTER - 1, CENTER_Y + PLATTER_R_OUTER + 2):
            for x in range(CENTER_X - PLATTER_R_OUTER - 1, CENTER_X + PLATTER_R_OUTER + 2):
                if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                    dx = x - CENTER_X
                    dy = y - CENTER_Y
                    dist = math.sqrt(dx * dx + dy * dy)
                    if PLATTER_R_INNER <= dist <= PLATTER_R_OUTER:
                        # Metallic shading
                        edge_t = (dist - PLATTER_R_INNER) / max(1, PLATTER_R_OUTER - PLATTER_R_INNER)
                        if edge_t < 0.5:
                            d.set_pixel(x, y, PLATTER_EDGE)
                        else:
                            d.set_pixel(x, y, PLATTER_COLOR)

    def _draw_record(self, d):
        """Draw the vinyl disc with rotating concentric grooves and light reflection."""
        highlight_angle = self.time * 0.4  # Slowly sweeping highlight

        for y in range(CENTER_Y - RECORD_R - 1, CENTER_Y + RECORD_R + 2):
            for x in range(CENTER_X - RECORD_R - 1, CENTER_X + RECORD_R + 2):
                if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                    dx = x - CENTER_X
                    dy = y - CENTER_Y
                    dist = math.sqrt(dx * dx + dy * dy)

                    if dist <= RECORD_R and dist > LABEL_R_OUTER:
                        # Pixel angle relative to disc rotation
                        px_angle = math.atan2(dy, dx) + self.angle

                        # Concentric groove pattern: use distance + angle offset
                        # Creates spiral-like groove appearance
                        groove_val = (dist * 2.0 + px_angle * 0.8) % 3.0

                        if groove_val < 1.5:
                            base = VINYL_DARK
                        else:
                            base = VINYL_GROOVE

                        # Light reflection: bright band sweeping across disc
                        reflection_angle = math.atan2(dy, dx)
                        angle_diff = reflection_angle - highlight_angle
                        # Normalize to [-pi, pi]
                        angle_diff = (angle_diff + math.pi) % (2.0 * math.pi) - math.pi
                        reflection = max(0.0, math.cos(angle_diff * 2.0))
                        reflection = reflection ** 3  # Sharpen the highlight

                        # Apply reflection
                        r = min(255, int(base[0] + (VINYL_HIGHLIGHT[0] - base[0]) * reflection))
                        g = min(255, int(base[1] + (VINYL_HIGHLIGHT[1] - base[1]) * reflection))
                        b = min(255, int(base[2] + (VINYL_HIGHLIGHT[2] - base[2]) * reflection))

                        d.set_pixel(x, y, (r, g, b))

    def _draw_label(self, d):
        """Draw the rotating center label."""
        primary, secondary, text_color = LABEL_PALETTES[self.label_idx]

        for y in range(CENTER_Y - LABEL_R_OUTER - 1, CENTER_Y + LABEL_R_OUTER + 2):
            for x in range(CENTER_X - LABEL_R_OUTER - 1, CENTER_X + LABEL_R_OUTER + 2):
                if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                    dx = x - CENTER_X
                    dy = y - CENTER_Y
                    dist = math.sqrt(dx * dx + dy * dy)

                    if dist <= LABEL_R_OUTER and dist >= LABEL_R_INNER:
                        # Rotating pattern on label
                        px_angle = math.atan2(dy, dx) + self.angle

                        # Radiating segments (like a label design)
                        segment = (px_angle * 4.0 / math.pi) % 2.0
                        if segment < 1.0:
                            color = primary
                        else:
                            color = secondary

                        # Slight highlight near top of label
                        if dy < -dist * 0.3:
                            r = min(255, color[0] + 25)
                            g = min(255, color[1] + 25)
                            b = min(255, color[2] + 25)
                            color = (r, g, b)

                        d.set_pixel(x, y, color)

                    elif dist < LABEL_R_INNER:
                        # Inner spindle hole area
                        d.set_pixel(x, y, (30, 30, 35))

    def _draw_tonearm(self, d):
        """Draw the tonearm that pivots from top-right and sweeps inward."""
        # Calculate stylus position: moves radially inward along the record
        # from outer edge (RECORD_R) to inner label (LABEL_R_OUTER)
        target_r = RECORD_R - (RECORD_R - LABEL_R_OUTER - 1) * self.arm_progress
        stylus_x = CENTER_X - target_r  # Stylus approaches from left side
        stylus_y = CENTER_Y

        # Arm consists of two segments: pivot -> elbow -> stylus
        # Total arm length is ARM_LENGTH_1 + ARM_LENGTH_2
        # We need to solve for elbow position such that:
        # - Distance from pivot to elbow = ARM_LENGTH_1
        # - Distance from elbow to stylus = ARM_LENGTH_2

        dx_total = stylus_x - ARM_PIVOT_X
        dy_total = stylus_y - ARM_PIVOT_Y

        # Elbow position: use ratio to place between pivot and stylus
        # This creates smooth arm motion regardless of distance
        elbow_ratio = 0.6  # 60% along the way from pivot to stylus
        elbow_x = ARM_PIVOT_X + dx_total * elbow_ratio
        elbow_y = ARM_PIVOT_Y + dy_total * elbow_ratio - 2  # Slight upward curve

        # Draw upper arm segment (pivot to elbow)
        d.draw_line(ARM_PIVOT_X, ARM_PIVOT_Y, int(elbow_x), int(elbow_y), ARM_COLOR)

        # Draw lower arm segment (elbow to headshell)
        headshell_x = int(stylus_x)
        headshell_y = int(stylus_y) - 1
        d.draw_line(int(elbow_x), int(elbow_y), headshell_x, headshell_y, ARM_COLOR)

        # Headshell (small rectangle at end of arm)
        d.set_pixel(headshell_x, headshell_y, HEADSHELL_COLOR)
        d.set_pixel(headshell_x - 1, headshell_y, HEADSHELL_COLOR)
        d.set_pixel(headshell_x, headshell_y + 1, HEADSHELL_COLOR)
        d.set_pixel(headshell_x - 1, headshell_y + 1, HEADSHELL_COLOR)

        # Stylus point (red dot)
        d.set_pixel(headshell_x - 1, int(stylus_y) + 1, STYLUS_COLOR)

        # Pivot point (metallic circle)
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                px = ARM_PIVOT_X + dx
                py = ARM_PIVOT_Y + dy
                if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                    d.set_pixel(px, py, PIVOT_COLOR)
        d.set_pixel(ARM_PIVOT_X, ARM_PIVOT_Y, ARM_HIGHLIGHT)
