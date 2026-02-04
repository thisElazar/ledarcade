"""
Gyroscope
=========
A heavy disc spinning rapidly inside a gimbal frame. The disc stays
level (or precesses slowly) while the frame tilts. Shows the gimbal
rings as concentric circles at varying angles, disc as a bright
spinning element inside.

Controls:
  Left/Right - Adjust precession rate
  Up/Down    - Adjust spin speed
"""

import math
from . import Visual, Display, Colors, GRID_SIZE


# Color palette
BG_COLOR = (5, 5, 10)
STEEL_GRAY = (180, 180, 190)
STEEL_DARK = (100, 100, 110)
STEEL_LIGHT = (220, 220, 230)
BRASS = (200, 170, 50)
BRASS_DARK = (140, 115, 30)
BRASS_LIGHT = (240, 210, 90)
DISC_CORE = (255, 255, 255)
DISC_BRIGHT = (255, 240, 200)
DISC_SPOKE = (220, 200, 160)
HUD_COLOR = (160, 160, 170)
HUD_DIM = (90, 90, 100)


class Gyroscope(Visual):
    name = "GYROSCOPE"
    description = "Gimbal mechanism"
    category = "mechanics"

    # Layout
    CENTER_X = 32
    CENTER_Y = 34

    # Gimbal ring radii
    OUTER_RING_R = 26
    INNER_RING_R = 18
    DISC_R = 10

    # Disc spoke count
    SPOKE_COUNT = 6

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

        # Precession: slow rotation of gimbal orientation
        self.precession_rate = 0.3  # radians per second
        self.precession_angle = 0.0

        # Gimbal tilt angles (for 3D effect)
        self.outer_tilt = 0.0  # outer ring tilt phase
        self.inner_tilt = 0.0  # inner ring tilt phase

        # Disc spin
        self.spin_rate = 8.0  # radians per second (fast spin)
        self.spin_angle = 0.0

        # Control limits
        self.min_precession = 0.0
        self.max_precession = 1.0
        self.min_spin = 2.0
        self.max_spin = 20.0

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Left/Right: adjust precession rate
        if input_state.right_pressed:
            self.precession_rate = min(self.max_precession, self.precession_rate + 0.1)
            consumed = True
        elif input_state.left_pressed:
            self.precession_rate = max(self.min_precession, self.precession_rate - 0.1)
            consumed = True

        # Up/Down: adjust spin speed
        if input_state.up_pressed:
            self.spin_rate = min(self.max_spin, self.spin_rate + 2.0)
            consumed = True
        elif input_state.down_pressed:
            self.spin_rate = max(self.min_spin, self.spin_rate - 2.0)
            consumed = True

        return consumed

    def update(self, dt):
        self.time += dt

        # Update precession angle
        self.precession_angle += self.precession_rate * dt

        # Update gimbal tilt phases (different rates for visual interest)
        self.outer_tilt = self.precession_angle * 0.7
        self.inner_tilt = self.precession_angle * 1.3 + math.pi / 4

        # Update disc spin
        self.spin_angle += self.spin_rate * dt

    def draw(self):
        d = self.display
        d.clear(BG_COLOR)

        # Draw gimbal mount (top support)
        self._draw_mount(d)

        # Draw outer gimbal ring
        self._draw_gimbal_ring(d, self.OUTER_RING_R, self.outer_tilt,
                               STEEL_DARK, STEEL_GRAY, STEEL_LIGHT)

        # Draw inner gimbal ring
        self._draw_gimbal_ring(d, self.INNER_RING_R, self.inner_tilt,
                               BRASS_DARK, BRASS, BRASS_LIGHT)

        # Draw spinning disc
        self._draw_disc(d)

        # Draw HUD
        self._draw_hud(d)

    def _draw_mount(self, d):
        """Draw the top mounting bracket for the gyroscope."""
        cx = self.CENTER_X
        top_y = self.CENTER_Y - self.OUTER_RING_R - 4

        # Vertical support
        d.draw_line(cx, 0, cx, top_y + 2, STEEL_DARK)
        d.draw_line(cx - 1, 0, cx - 1, top_y, STEEL_GRAY)
        d.draw_line(cx + 1, 0, cx + 1, top_y, STEEL_GRAY)

        # Mounting bracket at top of outer ring
        d.draw_line(cx - 3, top_y, cx + 3, top_y, STEEL_LIGHT)
        d.draw_line(cx - 2, top_y + 1, cx + 2, top_y + 1, STEEL_GRAY)

    def _draw_gimbal_ring(self, d, radius, tilt_phase, dark, mid, light):
        """
        Draw a tilted gimbal ring as an ellipse.
        The tilt_phase affects the apparent orientation of the ring.
        """
        cx = self.CENTER_X
        cy = self.CENTER_Y

        # Calculate apparent tilt (makes ring look 3D)
        tilt_x = math.sin(tilt_phase) * 0.4  # horizontal tilt factor
        tilt_y = math.cos(tilt_phase * 0.7) * 0.3  # vertical tilt factor

        # Draw ellipse by plotting points
        segments = 64
        prev_x, prev_y = None, None

        for i in range(segments + 1):
            angle = (i / segments) * 2.0 * math.pi

            # Base circle position
            base_x = math.cos(angle)
            base_y = math.sin(angle)

            # Apply 3D tilt transformation
            # Simulate perspective by scaling based on depth
            depth = base_x * tilt_x + base_y * tilt_y
            scale = 1.0 + depth * 0.3

            # Project to screen coordinates
            px = cx + int(round(radius * base_x * (1.0 - abs(tilt_y) * 0.2)))
            py = cy + int(round(radius * base_y * (1.0 - abs(tilt_x) * 0.2) * scale))

            # Color based on "facing" direction (simulate lighting)
            brightness = 0.5 + 0.5 * math.sin(angle + tilt_phase)

            if brightness > 0.7:
                color = light
            elif brightness > 0.3:
                color = mid
            else:
                color = dark

            # Draw point
            d.set_pixel(px, py, color)

            # Connect with line for smoother appearance
            if prev_x is not None:
                # Only draw connection if points are close
                if abs(px - prev_x) <= 2 and abs(py - prev_y) <= 2:
                    d.draw_line(prev_x, prev_y, px, py, mid)

            prev_x, prev_y = px, py

        # Draw ring thickness by adding inner edge
        inner_offset = 2
        for i in range(segments + 1):
            angle = (i / segments) * 2.0 * math.pi
            base_x = math.cos(angle)
            base_y = math.sin(angle)
            depth = base_x * tilt_x + base_y * tilt_y
            scale = 1.0 + depth * 0.3

            inner_r = radius - inner_offset
            px = cx + int(round(inner_r * base_x * (1.0 - abs(tilt_y) * 0.2)))
            py = cy + int(round(inner_r * base_y * (1.0 - abs(tilt_x) * 0.2) * scale))
            d.set_pixel(px, py, dark)

    def _draw_disc(self, d):
        """
        Draw the spinning disc in the center.
        Fast spin creates a blur effect via spoke animation.
        """
        cx = self.CENTER_X
        cy = self.CENTER_Y
        r = self.DISC_R

        # Draw disc body (filled circle with gradient)
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                dist_sq = dx * dx + dy * dy
                if dist_sq <= r * r:
                    # Radial gradient
                    dist = math.sqrt(dist_sq)
                    t = dist / r

                    # Blend from center to edge
                    if t < 0.3:
                        color = DISC_CORE
                    elif t < 0.6:
                        # Interpolate
                        blend = (t - 0.3) / 0.3
                        color = (
                            int(DISC_CORE[0] * (1 - blend) + DISC_BRIGHT[0] * blend),
                            int(DISC_CORE[1] * (1 - blend) + DISC_BRIGHT[1] * blend),
                            int(DISC_CORE[2] * (1 - blend) + DISC_BRIGHT[2] * blend),
                        )
                    else:
                        color = DISC_BRIGHT

                    d.set_pixel(cx + dx, cy + dy, color)

        # Draw spinning spokes (blur effect when fast)
        # More spokes visible at higher speeds to simulate blur
        effective_spokes = self.SPOKE_COUNT
        if self.spin_rate > 10:
            effective_spokes = self.SPOKE_COUNT * 2

        for i in range(effective_spokes):
            spoke_angle = self.spin_angle + (i / effective_spokes) * 2.0 * math.pi

            # Spoke fades based on spin speed (faster = more transparent blur)
            alpha = max(0.3, 1.0 - (self.spin_rate - self.min_spin) / (self.max_spin - self.min_spin) * 0.7)

            # Draw spoke from center outward
            for dist in range(2, r + 2):
                sx = cx + int(round(dist * math.cos(spoke_angle)))
                sy = cy + int(round(dist * math.sin(spoke_angle)))

                if 0 <= sx < GRID_SIZE and 0 <= sy < GRID_SIZE:
                    # Get existing color and blend
                    existing = d.get_pixel(sx, sy)
                    spoke_c = DISC_SPOKE

                    # Blend spoke color with existing
                    color = (
                        int(existing[0] * (1 - alpha) + spoke_c[0] * alpha),
                        int(existing[1] * (1 - alpha) + spoke_c[1] * alpha),
                        int(existing[2] * (1 - alpha) + spoke_c[2] * alpha),
                    )
                    d.set_pixel(sx, sy, color)

        # Draw center hub
        d.draw_circle(cx, cy, 2, BRASS_LIGHT, filled=True)
        d.set_pixel(cx, cy, DISC_CORE)

        # Draw axle extending through disc
        axle_ext = 3
        for i in range(-axle_ext, axle_ext + 1):
            # Axle goes through based on inner gimbal tilt
            ax = cx + int(round(i * math.cos(self.inner_tilt + math.pi / 2)))
            ay = cy + int(round(i * math.sin(self.inner_tilt + math.pi / 2) * 0.5))
            d.set_pixel(ax, ay, STEEL_LIGHT)

    def _draw_hud(self, d):
        """Draw control information."""
        # Precession rate
        prec_pct = int((self.precession_rate - self.min_precession) /
                       (self.max_precession - self.min_precession) * 100)
        d.draw_text_small(2, 2, f"PREC {prec_pct}", HUD_COLOR)

        # Spin rate
        spin_pct = int((self.spin_rate - self.min_spin) /
                       (self.max_spin - self.min_spin) * 100)
        d.draw_text_small(2, 9, f"SPIN {spin_pct}", HUD_DIM)

        # Visual indicator bars
        bar_x = 56
        bar_h = 8

        # Precession bar
        prec_fill = max(1, int(prec_pct / 100.0 * bar_h))
        d.draw_rect(bar_x, 2, 3, bar_h, (30, 30, 35))
        d.draw_rect(bar_x, 2 + bar_h - prec_fill, 3, prec_fill, STEEL_GRAY)

        # Spin bar
        spin_fill = max(1, int(spin_pct / 100.0 * bar_h))
        d.draw_rect(bar_x + 4, 2, 3, bar_h, (30, 30, 35))
        d.draw_rect(bar_x + 4, 2 + bar_h - spin_fill, 3, spin_fill, BRASS)
