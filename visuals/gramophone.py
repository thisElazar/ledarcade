"""
Gramophone
==========
Vintage horn speaker with spinning disc. A large flared horn extends from
a throat to a wide bell mouth, with concentric sound wave arcs expanding
outward. Below, a turntable spins with visible groove lines in a
foreshortened elliptical view. A tonearm connects the disc to the horn,
and a crank handle rotates slowly at the side.

Controls:
  Left/Right - RPM (33 / 45 / 78)
  Up/Down    - Horn finish (Brass / Copper / Silver / Painted)
"""

import math
from . import Visual, Display, Colors, GRID_SIZE


# --- RPM Settings ---
RPM_OPTIONS = [33, 45, 78]

# --- Horn Finish Palettes ---
# Each finish: (name, horn_bright, horn_mid, horn_dark, horn_interior, wave_color)
FINISHES = [
    ("BRASS",   (220, 190, 80),  (180, 150, 50),  (120, 100, 30),  (90, 70, 20),   (255, 230, 100)),
    ("COPPER",  (210, 130, 70),  (170, 100, 50),  (120, 65, 30),   (80, 45, 20),   (240, 160, 90)),
    ("SILVER",  (210, 210, 220), (170, 170, 180), (120, 120, 130), (80, 80, 90),   (230, 230, 255)),
    ("PAINTED", (180, 50, 50),   (140, 35, 35),   (100, 25, 25),   (60, 15, 15),   (255, 120, 100)),
]

# --- Static Colors ---
BG_COLOR = (12, 10, 8)
TURNTABLE_BASE = (40, 35, 30)
TURNTABLE_RIM = (70, 60, 50)
DISC_COLOR = (20, 20, 22)
DISC_GROOVE = (30, 30, 35)
DISC_LABEL = (160, 50, 45)
DISC_LABEL_DARK = (120, 35, 30)
TONEARM_COLOR = (180, 180, 190)
TONEARM_PIVOT = (140, 140, 150)
TONEARM_HEAD = (200, 200, 210)
NEEDLE_COLOR = (255, 255, 255)
CRANK_ARM = (150, 150, 160)
CRANK_HANDLE = (100, 70, 35)
CRANK_HUB = (180, 180, 190)
THROAT_CONNECTOR = (100, 90, 60)
HUD_COLOR = (160, 160, 170)

# --- Layout Constants ---

# Horn geometry: flared trapezoid from throat to bell
THROAT_X = 14
THROAT_Y = 28
THROAT_HALF_H = 3       # half-height of throat opening
BELL_X = 58
BELL_Y = 28
BELL_HALF_H = 14        # half-height of bell opening

# Turntable (foreshortened ellipse)
TABLE_CX = 20
TABLE_CY = 50
TABLE_RX = 14           # horizontal radius
TABLE_RY = 7            # vertical radius (foreshortened)
DISC_RX = 12
DISC_RY = 6
LABEL_RX = 4
LABEL_RY = 2

# Tonearm
ARM_PIVOT_X = 6
ARM_PIVOT_Y = 42
ARM_ELBOW_X = 10
ARM_ELBOW_Y = 46
ARM_TIP_X = 18          # near edge of disc (adjusted by rotation)
ARM_TIP_Y = 48

# Crank handle
CRANK_CX = 6
CRANK_CY = 54
CRANK_R = 4

# Sound wave arcs origin (at bell mouth)
WAVE_ORIGIN_X = BELL_X
WAVE_ORIGIN_Y = BELL_Y


class Gramophone(Visual):
    name = "GRAMOPHONE"
    description = "Vintage gramophone"
    category = "music"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.rpm_index = 1          # default 45 RPM
        self.finish_index = 0       # default Brass
        self.disc_angle = 0.0       # turntable rotation in radians
        self.crank_angle = 0.0      # crank handle angle
        self.wave_timer = 0.0       # for cycling sound wave arcs

    def handle_input(self, input_state):
        consumed = False
        if input_state.right_pressed:
            self.rpm_index = min(len(RPM_OPTIONS) - 1, self.rpm_index + 1)
            consumed = True
        elif input_state.left_pressed:
            self.rpm_index = max(0, self.rpm_index - 1)
            consumed = True
        if input_state.up_pressed:
            self.finish_index = (self.finish_index - 1) % len(FINISHES)
            consumed = True
        elif input_state.down_pressed:
            self.finish_index = (self.finish_index + 1) % len(FINISHES)
            consumed = True
        return consumed

    def update(self, dt):
        self.time += dt

        rpm = RPM_OPTIONS[self.rpm_index]
        # Disc rotation: convert RPM to radians/sec
        rps = rpm / 60.0
        self.disc_angle += rps * 2.0 * math.pi * dt

        # Crank rotates slowly (linked to disc but slower)
        self.crank_angle += rps * 0.5 * 2.0 * math.pi * dt

        # Sound wave timer
        self.wave_timer += dt

    def draw(self):
        d = self.display
        d.clear(BG_COLOR)

        finish = FINISHES[self.finish_index]
        horn_bright = finish[1]
        horn_mid = finish[2]
        horn_dark = finish[3]
        horn_interior = finish[4]
        wave_color = finish[5]

        self._draw_turntable(d)
        self._draw_disc(d)
        self._draw_tonearm(d)
        self._draw_horn(d, horn_bright, horn_mid, horn_dark, horn_interior)
        self._draw_sound_waves(d, wave_color)
        self._draw_crank(d)
        self._draw_hud(d, finish[0])

    def _draw_turntable(self, d):
        """Draw the turntable base as a foreshortened ellipse."""
        cx, cy = TABLE_CX, TABLE_CY
        rx, ry = TABLE_RX, TABLE_RY

        # Base platform (slightly larger than disc)
        for py in range(cy - ry - 1, cy + ry + 2):
            for px in range(cx - rx - 1, cx + rx + 2):
                dx = (px - cx) / (rx + 1.0)
                dy = (py - cy) / (ry + 1.0)
                if dx * dx + dy * dy <= 1.0:
                    d.set_pixel(px, py, TURNTABLE_BASE)

        # Rim highlight
        for angle_i in range(72):
            a = angle_i * math.pi * 2.0 / 72.0
            ex = int(round(cx + (rx + 0.5) * math.cos(a)))
            ey = int(round(cy + (ry + 0.5) * math.sin(a)))
            if 0 <= ex < GRID_SIZE and 0 <= ey < GRID_SIZE:
                d.set_pixel(ex, ey, TURNTABLE_RIM)

    def _draw_disc(self, d):
        """Draw spinning vinyl disc with groove lines and label."""
        cx, cy = TABLE_CX, TABLE_CY
        rx, ry = DISC_RX, DISC_RY
        lrx, lry = LABEL_RX, LABEL_RY

        for py in range(cy - ry, cy + ry + 1):
            for px in range(cx - rx, cx + rx + 1):
                dx = (px - cx)
                dy = (py - cy)
                # Ellipse distance (normalized)
                ex = dx / float(rx)
                ey = dy / float(ry)
                dist_sq = ex * ex + ey * ey
                if dist_sq > 1.0:
                    continue

                # Check if in label area
                lx = dx / float(lrx)
                ly = dy / float(lry)
                label_dist = lx * lx + ly * ly
                if label_dist <= 1.0:
                    # Label area
                    if label_dist > 0.7:
                        d.set_pixel(px, py, DISC_LABEL_DARK)
                    else:
                        d.set_pixel(px, py, DISC_LABEL)
                    continue

                # Groove lines: concentric rings that rotate
                # Map pixel to angle relative to disc center
                angle = math.atan2(dy, dx) + self.disc_angle
                # Radial distance in disc space
                r_norm = math.sqrt(dist_sq)
                # Create groove pattern: modulate by radius + subtle angle shift
                groove_val = (r_norm * 12.0 + angle * 0.3) % 1.0
                if groove_val < 0.35:
                    d.set_pixel(px, py, DISC_GROOVE)
                else:
                    d.set_pixel(px, py, DISC_COLOR)

        # Spindle dot at center
        d.set_pixel(cx, cy, TONEARM_PIVOT)

    def _draw_tonearm(self, d):
        """Draw tonearm from pivot to needle position on disc."""
        # Tonearm sways very slightly with rotation
        sway = math.sin(self.disc_angle * 0.1) * 0.5

        pivot_x = ARM_PIVOT_X
        pivot_y = ARM_PIVOT_Y

        # Elbow point
        elbow_x = ARM_ELBOW_X + int(sway * 0.3)
        elbow_y = ARM_ELBOW_Y

        # Tip (needle) near disc edge
        tip_x = ARM_TIP_X + int(sway)
        tip_y = ARM_TIP_Y

        # Draw arm segments
        d.draw_line(pivot_x, pivot_y, elbow_x, elbow_y, TONEARM_COLOR)
        d.draw_line(elbow_x, elbow_y, tip_x, tip_y, TONEARM_COLOR)

        # Pivot base
        d.set_pixel(pivot_x, pivot_y, TONEARM_PIVOT)
        d.set_pixel(pivot_x + 1, pivot_y, TONEARM_PIVOT)
        d.set_pixel(pivot_x, pivot_y + 1, TONEARM_PIVOT)

        # Headshell at tip
        d.set_pixel(tip_x, tip_y, TONEARM_HEAD)
        d.set_pixel(tip_x + 1, tip_y, TONEARM_HEAD)

        # Needle (bright dot)
        d.set_pixel(tip_x + 1, tip_y + 1, NEEDLE_COLOR)

    def _draw_horn(self, d, horn_bright, horn_mid, horn_dark, horn_interior):
        """Draw the flared horn as a trapezoid from throat to bell."""
        tx, ty = THROAT_X, THROAT_Y
        bx, by = BELL_X, BELL_Y

        # Connect throat to turntable area
        d.draw_line(tx - 2, ty, tx, ty, THROAT_CONNECTOR)
        d.draw_line(tx - 2, ty - 1, tx, ty - 1, THROAT_CONNECTOR)
        d.draw_line(tx - 2, ty + 1, tx, ty + 1, THROAT_CONNECTOR)

        # Draw horn body column by column
        horn_len = bx - tx
        for col in range(horn_len + 1):
            x = tx + col
            t = col / float(max(1, horn_len))

            # Flare: half-height expands from throat to bell (exponential-ish)
            flare = t * t  # quadratic flare
            half_h = THROAT_HALF_H + flare * (BELL_HALF_H - THROAT_HALF_H)

            top = int(round(by - half_h))
            bot = int(round(by + half_h))

            for y in range(top, bot + 1):
                if y < 0 or y >= GRID_SIZE:
                    continue

                # Distance from center line (0 to 1)
                dist = abs(y - by) / max(1.0, half_h)

                if dist > 0.9:
                    # Rim / edge
                    d.set_pixel(x, y, horn_bright)
                elif dist > 0.6:
                    # Outer surface
                    d.set_pixel(x, y, horn_mid)
                elif dist > 0.3:
                    # Inner surface shading
                    # Only show interior for the wider part of the horn
                    if t > 0.3:
                        d.set_pixel(x, y, horn_dark)
                    else:
                        d.set_pixel(x, y, horn_mid)
                else:
                    # Deep interior (dark)
                    if t > 0.25:
                        d.set_pixel(x, y, horn_interior)
                    else:
                        d.set_pixel(x, y, horn_dark)

        # Bell rim highlight at the mouth
        for y in range(by - BELL_HALF_H, by + BELL_HALF_H + 1):
            if 0 <= y < GRID_SIZE:
                d.set_pixel(bx, y, horn_bright)

    def _draw_sound_waves(self, d, wave_color):
        """Draw concentric arc waves expanding from the bell mouth."""
        ox, oy = WAVE_ORIGIN_X, WAVE_ORIGIN_Y

        # Generate 3 waves at different radii, cycling outward
        num_waves = 3
        wave_speed = 8.0  # pixels per second
        max_radius = 20
        cycle_period = max_radius / wave_speed

        for i in range(num_waves):
            # Stagger the waves
            phase = (self.wave_timer + i * cycle_period / num_waves) % cycle_period
            radius = int(phase * wave_speed)

            if radius < 2 or radius > max_radius:
                continue

            # Fade with distance
            fade = 1.0 - (radius / float(max_radius))
            fade = max(0.0, fade)
            r = int(wave_color[0] * fade * 0.6)
            g = int(wave_color[1] * fade * 0.6)
            b = int(wave_color[2] * fade * 0.6)
            if r < 5 and g < 5 and b < 5:
                continue
            color = (r, g, b)

            # Draw arc: only the rightward-facing portion (spread angle)
            arc_spread = 0.7  # radians above and below horizontal
            steps = max(12, radius * 4)
            for s in range(steps + 1):
                t = s / float(steps)
                angle = -arc_spread + t * 2.0 * arc_spread
                px = int(round(ox + radius * math.cos(angle)))
                py = int(round(oy + radius * math.sin(angle)))
                if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                    d.set_pixel(px, py, color)

    def _draw_crank(self, d):
        """Draw the rotating crank handle at the side of the cabinet."""
        cx, cy = CRANK_CX, CRANK_CY

        # Hub
        d.set_pixel(cx, cy, CRANK_HUB)
        d.set_pixel(cx + 1, cy, CRANK_HUB)
        d.set_pixel(cx, cy + 1, CRANK_HUB)

        # Crank arm rotates
        arm_x = int(round(cx + CRANK_R * math.cos(self.crank_angle)))
        arm_y = int(round(cy + CRANK_R * math.sin(self.crank_angle)))

        d.draw_line(cx, cy, arm_x, arm_y, CRANK_ARM)

        # Handle knob at end of arm
        if 0 <= arm_x < GRID_SIZE and 0 <= arm_y < GRID_SIZE:
            d.set_pixel(arm_x, arm_y, CRANK_HANDLE)
            if arm_x + 1 < GRID_SIZE:
                d.set_pixel(arm_x + 1, arm_y, CRANK_HANDLE)
            if arm_y + 1 < GRID_SIZE:
                d.set_pixel(arm_x, arm_y + 1, CRANK_HANDLE)

    def _draw_hud(self, d, finish_name):
        """Draw RPM and finish labels."""
        rpm = RPM_OPTIONS[self.rpm_index]
        d.draw_text_small(2, 2, f"{rpm} RPM", HUD_COLOR)
        d.draw_text_small(2, 58, finish_name, HUD_COLOR)
