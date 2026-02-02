"""
Film Projector
==============
Geneva drive mechanism advancing film frames in discrete steps while the
shutter rotates. A continuously spinning driver disc has a pin that engages
slots in a Maltese cross, advancing it exactly 90 degrees per revolution.

The film physically travels from supply reel (top) through sprocket rollers
and a film gate down to the takeup reel (bottom). The Geneva cross connects
via a horizontal axle to the lower sprocket, which drives the film.

Key elements: Geneva drive (driver + cross), film strip with sprocket holes,
rotating shutter disc, projected light beam, and supply/take-up reels.

Controls:
  Left/Right - Adjust projection speed (1-6)
"""

import math
from . import Visual, Display, Colors, GRID_SIZE


# --- Color Palette ---
BODY_COLOR = (40, 40, 45)
DRIVER_COLOR = (180, 180, 190)
DRIVER_DARK = (130, 130, 140)
PIN_COLOR = (255, 220, 80)
CROSS_COLOR = (200, 170, 50)
CROSS_DARK = (140, 120, 40)
CROSS_SLOT = (100, 85, 30)
FILM_COLOR = (60, 40, 20)
FILM_EDGE = (45, 30, 15)
FRAME_COLOR = (80, 60, 30)
FRAME_BRIGHT = (110, 85, 45)
SPROCKET_COLOR = (30, 20, 10)
SHUTTER_COLOR = (60, 60, 70)
SHUTTER_EDGE = (80, 80, 90)
BEAM_BRIGHT = (255, 240, 180)
BEAM_MID = (200, 185, 120)
BEAM_DIM = (120, 110, 70)
BEAM_FAINT = (60, 55, 35)
REEL_COLOR = (80, 80, 90)
REEL_HUB = (120, 120, 130)
REEL_SPOKE = (100, 100, 110)
LOCK_COLOR = (150, 150, 160)
HUD_COLOR = (160, 160, 170)
GATE_COLOR = (180, 170, 100)
AXLE_COLOR = (140, 140, 150)
SPROCKET_ROLLER = (100, 100, 110)
FILM_WRAP = (80, 55, 30)

# Frame content colors (variety for visual interest)
FRAME_COLORS = [
    (120, 90, 50),
    (100, 80, 60),
    (110, 95, 55),
    (95, 75, 45),
    (115, 85, 40),
]

# --- Layout Constants ---

# Film axis (everything vertically aligned at x=38)
FILM_CX = 38

# Supply reel (top)
SUPPLY_CX = FILM_CX
SUPPLY_CY = 6
SUPPLY_R = 5

# Upper sprocket roller
UPPER_SPROCKET_CY = 13
UPPER_SPROCKET_R = 2

# Film strip
FILM_LEFT = 35
FILM_RIGHT = 41
FILM_W = FILM_RIGHT - FILM_LEFT + 1  # 7 pixels wide
FRAME_H = 5
FRAME_GAP = 2
FRAME_STEP = FRAME_H + FRAME_GAP
FILM_TOP = 15
FILM_BOT = 45

# Film gate (highlighted window)
GATE_TOP = 27
GATE_BOT = 33
GATE_CY = 30

# Lower sprocket roller
LOWER_SPROCKET_CY = 48
LOWER_SPROCKET_R = 2

# Takeup reel (bottom)
TAKEUP_CX = FILM_CX
TAKEUP_CY = 56
TAKEUP_R = 4

# Geneva driver
DRIVER_CX = 10
DRIVER_CY = 48
DRIVER_R = 6
PIN_DIST = 5

# Geneva cross
CROSS_CX = 17
CROSS_CY = 48
CROSS_R = 5
CROSS_ARM_LEN = 4
CROSS_ARM_W = 1

# Axle from cross hub to lower sprocket
AXLE_Y = 48

# Shutter (between Geneva area and film)
SHUTTER_CX = 28
SHUTTER_CY = 30
SHUTTER_R = 4

# Light beam
BEAM_START_X = FILM_RIGHT + 2
BEAM_Y = GATE_CY

# Speed settings: film frames per second
SPEED_FPS = [1, 4, 8, 12, 18, 24]
ENGAGE_FRAC = 0.25


class Projector(Visual):
    name = "PROJECTOR"
    description = "Film projector"
    category = "mechanics"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed_level = 3
        self.driver_angle = 0.0
        self.cross_angle = 0.0
        self.shutter_angle = math.pi  # phase offset so beam fires during stationary period
        self.supply_angle = 0.0
        self.takeup_angle = 0.0
        self.beam_on = False
        self.flicker_timer = 0.0

    def handle_input(self, input_state):
        consumed = False
        if input_state.right_pressed:
            self.speed_level = min(6, self.speed_level + 1)
            consumed = True
        elif input_state.left_pressed:
            self.speed_level = max(1, self.speed_level - 1)
            consumed = True
        return consumed

    def update(self, dt):
        self.time += dt

        # Driver omega derived from film FPS:
        # one driver revolution = one Geneva step = one film frame
        fps = SPEED_FPS[self.speed_level - 1]
        omega = fps * 2.0 * math.pi

        # Driver rotates continuously
        self.driver_angle += omega * dt

        # Geneva cross: intermittent motion from driver
        full_revs = self.driver_angle / (2.0 * math.pi)
        step_num = int(full_revs)
        frac = full_revs - step_num

        if frac < ENGAGE_FRAC:
            t = frac / ENGAGE_FRAC
            smooth = 0.5 - 0.5 * math.cos(math.pi * t)
            self.cross_angle = (step_num * math.pi / 2.0) + smooth * (math.pi / 2.0)
        else:
            self.cross_angle = (step_num + 1) * math.pi / 2.0

        # Film offset derived continuously from cross angle:
        # each pi/2 of cross rotation = one FRAME_STEP of film travel
        self.film_offset = self.cross_angle / (math.pi / 2.0) * FRAME_STEP

        # Shutter rotates at 2x driver speed
        self.shutter_angle += omega * 2.0 * dt

        shutter_norm = (self.shutter_angle % (2.0 * math.pi)) / (2.0 * math.pi)
        self.beam_on = shutter_norm < 0.45

        # Reels rotate continuously
        self.supply_angle += omega * 0.4 * dt
        self.takeup_angle += omega * 0.55 * dt

        self.flicker_timer += dt

    def draw(self):
        d = self.display
        d.clear(BODY_COLOR)

        self._draw_reels(d)
        self._draw_film_strip(d)
        self._draw_sprocket_rollers(d)
        self._draw_axle(d)
        self._draw_geneva_drive(d)
        self._draw_shutter(d)
        self._draw_light_beam(d)
        self._draw_hud(d)

    def _draw_reels(self, d):
        """Draw supply (top) and take-up (bottom) reels with rotating spokes."""
        for cx, cy, r, angle in [
            (SUPPLY_CX, SUPPLY_CY, SUPPLY_R, self.supply_angle),
            (TAKEUP_CX, TAKEUP_CY, TAKEUP_R, self.takeup_angle),
        ]:
            # Reel rim
            d.draw_circle(cx, cy, r, REEL_COLOR)
            d.draw_circle(cx, cy, r - 1, REEL_COLOR)

            # Spokes (5 spokes)
            for i in range(5):
                spoke_a = angle + i * 2.0 * math.pi / 5.0
                ex = int(round(cx + (r - 1) * math.cos(spoke_a)))
                ey = int(round(cy + (r - 1) * math.sin(spoke_a)))
                d.draw_line(cx, cy, ex, ey, REEL_SPOKE)

            # Hub
            d.set_pixel(cx, cy, REEL_HUB)
            d.set_pixel(cx - 1, cy, REEL_HUB)
            d.set_pixel(cx + 1, cy, REEL_HUB)
            d.set_pixel(cx, cy - 1, REEL_HUB)
            d.set_pixel(cx, cy + 1, REEL_HUB)

            # Film wrap: small arc of film color at reel edge facing the strip
            # Supply reel: film exits from bottom
            # Takeup reel: film enters from top
            if cy < 30:
                # Supply reel — film exits downward
                for dx in range(-1, 2):
                    d.set_pixel(cx + dx, cy + r, FILM_WRAP)
                    d.set_pixel(cx + dx, cy + r + 1, FILM_WRAP)
            else:
                # Takeup reel — film enters from above
                for dx in range(-1, 2):
                    d.set_pixel(cx + dx, cy - r, FILM_WRAP)
                    d.set_pixel(cx + dx, cy - r - 1, FILM_WRAP)

    def _draw_film_strip(self, d):
        """Draw the vertical film strip from upper sprocket to lower sprocket,
        plus short extensions to each reel."""
        # --- Short film segment: supply reel to upper sprocket ---
        for y in range(SUPPLY_CY + SUPPLY_R + 2, FILM_TOP):
            for x in range(FILM_LEFT, FILM_RIGHT + 1):
                if x == FILM_LEFT or x == FILM_RIGHT:
                    d.set_pixel(x, y, FILM_EDGE)
                else:
                    d.set_pixel(x, y, FILM_COLOR)

        # --- Main film strip: FILM_TOP to FILM_BOT ---
        # Film background
        for y in range(FILM_TOP, FILM_BOT + 1):
            for x in range(FILM_LEFT, FILM_RIGHT + 1):
                if x == FILM_LEFT or x == FILM_RIGHT:
                    d.set_pixel(x, y, FILM_EDGE)
                else:
                    d.set_pixel(x, y, FILM_COLOR)

        # Frame positions based on film_offset
        # Phase of 1 pixel centers the frame image in the gate when stationary
        offset = (self.film_offset + 1) % FRAME_STEP
        y = FILM_TOP - offset - FRAME_STEP

        frame_idx = 0
        while y < FILM_BOT + FRAME_STEP:
            fy = int(round(y))
            frame_top = fy + 1
            frame_bot = fy + FRAME_H - 1
            frame_left = FILM_LEFT + 1
            frame_right = FILM_RIGHT - 1

            if frame_bot >= FILM_TOP and frame_top <= FILM_BOT:
                # Clip to film strip bounds
                draw_top = max(frame_top, FILM_TOP)
                draw_bot = min(frame_bot, FILM_BOT)

                # Frame border
                for px in range(frame_left, frame_right + 1):
                    if FILM_TOP <= frame_top <= FILM_BOT:
                        d.set_pixel(px, frame_top, FRAME_COLOR)
                    if FILM_TOP <= frame_bot <= FILM_BOT:
                        d.set_pixel(px, frame_bot, FRAME_COLOR)
                for py in range(draw_top, draw_bot + 1):
                    d.set_pixel(frame_left, py, FRAME_COLOR)
                    d.set_pixel(frame_right, py, FRAME_COLOR)

                # Frame interior (colored to suggest an image)
                color = FRAME_COLORS[frame_idx % len(FRAME_COLORS)]
                for py in range(max(draw_top, frame_top + 1), min(draw_bot + 1, frame_bot)):
                    for px in range(frame_left + 1, frame_right):
                        d.set_pixel(px, py, color)

            # Sprocket hole on left edge between frames
            hole_y = fy + FRAME_H + FRAME_GAP // 2
            if FILM_TOP <= hole_y <= FILM_BOT:
                d.set_pixel(FILM_LEFT, hole_y, SPROCKET_COLOR)

            y += FRAME_STEP
            frame_idx += 1

        # Film gate highlight
        for px in range(FILM_LEFT - 1, FILM_RIGHT + 2):
            d.set_pixel(px, GATE_TOP - 1, GATE_COLOR)
            d.set_pixel(px, GATE_BOT + 1, GATE_COLOR)
        for py in range(GATE_TOP - 1, GATE_BOT + 2):
            d.set_pixel(FILM_LEFT - 1, py, GATE_COLOR)
            d.set_pixel(FILM_RIGHT + 1, py, GATE_COLOR)

        # --- Short film segment: lower sprocket to takeup reel ---
        for y in range(FILM_BOT + 1, TAKEUP_CY - TAKEUP_R - 1):
            for x in range(FILM_LEFT, FILM_RIGHT + 1):
                if x == FILM_LEFT or x == FILM_RIGHT:
                    d.set_pixel(x, y, FILM_EDGE)
                else:
                    d.set_pixel(x, y, FILM_COLOR)

    def _draw_sprocket_rollers(self, d):
        """Draw upper and lower sprocket rollers that guide the film."""
        for cy, r in [
            (UPPER_SPROCKET_CY, UPPER_SPROCKET_R),
            (LOWER_SPROCKET_CY, LOWER_SPROCKET_R),
        ]:
            # Roller body (extends across film width)
            for px in range(FILM_LEFT - 1, FILM_RIGHT + 2):
                d.set_pixel(px, cy, SPROCKET_ROLLER)
                if r >= 2:
                    d.set_pixel(px, cy - 1, SPROCKET_ROLLER)
                    d.set_pixel(px, cy + 1, SPROCKET_ROLLER)

            # Sprocket teeth (bright dots that engage the holes)
            # Rotate with the film motion
            tooth_offset = int(self.film_offset) % FRAME_STEP
            for ty in range(-1, 2):
                tooth_y = cy + ty
                if 0 <= tooth_y < GRID_SIZE:
                    d.set_pixel(FILM_LEFT, tooth_y, REEL_HUB)

            # Center hub
            d.set_pixel(FILM_CX, cy, REEL_HUB)

    def _draw_axle(self, d):
        """Draw horizontal axle from Geneva cross hub to lower sprocket."""
        axle_left = CROSS_CX + 2
        axle_right = FILM_LEFT - 2

        # Axle line (2px thick for visibility)
        d.draw_line(axle_left, AXLE_Y, axle_right, AXLE_Y, AXLE_COLOR)
        d.draw_line(axle_left, AXLE_Y - 1, axle_right, AXLE_Y - 1, AXLE_COLOR)

        # Small joint circles at each end
        d.set_pixel(axle_left, AXLE_Y, REEL_HUB)
        d.set_pixel(axle_right, AXLE_Y, REEL_HUB)

    def _draw_geneva_drive(self, d):
        """Draw the Geneva drive: driver disc with pin and Maltese cross."""
        # --- Driver disc ---
        for py in range(DRIVER_CY - DRIVER_R - 1, DRIVER_CY + DRIVER_R + 2):
            for px in range(DRIVER_CX - DRIVER_R - 1, DRIVER_CX + DRIVER_R + 2):
                dx = px - DRIVER_CX
                dy = py - DRIVER_CY
                dist_sq = dx * dx + dy * dy
                if dist_sq <= DRIVER_R * DRIVER_R:
                    if dist_sq > (DRIVER_R - 1.5) * (DRIVER_R - 1.5):
                        d.set_pixel(px, py, DRIVER_DARK)
                    else:
                        d.set_pixel(px, py, DRIVER_COLOR)

        # Driver center hub
        d.set_pixel(DRIVER_CX, DRIVER_CY, REEL_HUB)

        # Locking disc segment
        lock_angle = self.driver_angle + math.pi
        for i in range(-2, 3):
            a = lock_angle + i * 0.15
            lx = int(round(DRIVER_CX + (DRIVER_R - 1) * math.cos(a)))
            ly = int(round(DRIVER_CY + (DRIVER_R - 1) * math.sin(a)))
            d.set_pixel(lx, ly, LOCK_COLOR)

        # Pin on driver disc
        pin_x = DRIVER_CX + PIN_DIST * math.cos(self.driver_angle)
        pin_y = DRIVER_CY + PIN_DIST * math.sin(self.driver_angle)
        ipx = int(round(pin_x))
        ipy = int(round(pin_y))
        d.set_pixel(ipx, ipy, PIN_COLOR)
        d.set_pixel(ipx + 1, ipy, PIN_COLOR)
        d.set_pixel(ipx, ipy + 1, PIN_COLOR)
        d.set_pixel(ipx + 1, ipy + 1, PIN_COLOR)

        # --- Geneva cross (Maltese cross) ---
        for i in range(4):
            arm_angle = self.cross_angle + i * math.pi / 2.0
            cos_a = math.cos(arm_angle)
            sin_a = math.sin(arm_angle)
            perp_x = -sin_a
            perp_y = cos_a

            for t_int in range(2, CROSS_ARM_LEN + 1):
                t = float(t_int)
                ax = CROSS_CX + t * cos_a
                ay = CROSS_CY + t * sin_a

                for w in range(-CROSS_ARM_W, CROSS_ARM_W + 1):
                    px = int(round(ax + w * perp_x))
                    py = int(round(ay + w * perp_y))
                    if t_int == CROSS_ARM_LEN:
                        d.set_pixel(px, py, CROSS_DARK)
                    else:
                        d.set_pixel(px, py, CROSS_COLOR)

                if t_int >= CROSS_ARM_LEN - 1:
                    sx = int(round(ax))
                    sy = int(round(ay))
                    d.set_pixel(sx, sy, CROSS_SLOT)

        # Cross center disc
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if abs(dx) + abs(dy) <= 1:
                    d.set_pixel(CROSS_CX + dx, CROSS_CY + dy, CROSS_DARK)
        d.set_pixel(CROSS_CX, CROSS_CY, CROSS_COLOR)

    def _draw_shutter(self, d):
        """Draw the rotating shutter disc between Geneva area and film gate."""
        shutter_norm = self.shutter_angle % (2.0 * math.pi)

        for py in range(SHUTTER_CY - SHUTTER_R - 1, SHUTTER_CY + SHUTTER_R + 2):
            for px in range(SHUTTER_CX - SHUTTER_R - 1, SHUTTER_CX + SHUTTER_R + 2):
                dx = px - SHUTTER_CX
                dy = py - SHUTTER_CY
                dist_sq = dx * dx + dy * dy
                if dist_sq > SHUTTER_R * SHUTTER_R:
                    continue
                if dist_sq <= 1:
                    d.set_pixel(px, py, REEL_HUB)
                    continue

                pixel_angle = math.atan2(dy, dx) - shutter_norm
                pixel_angle = pixel_angle % (2.0 * math.pi)

                in_blade = (pixel_angle < math.pi * 0.45 or
                            (pixel_angle > math.pi * 0.55 and pixel_angle < math.pi * 1.45) or
                            pixel_angle > math.pi * 1.55)

                if in_blade:
                    if dist_sq > (SHUTTER_R - 1) * (SHUTTER_R - 1):
                        d.set_pixel(px, py, SHUTTER_EDGE)
                    else:
                        d.set_pixel(px, py, SHUTTER_COLOR)

    def _draw_light_beam(self, d):
        """Draw the projected light beam when shutter is open."""
        if not self.beam_on:
            return

        flicker = 0.85 + 0.15 * math.sin(self.flicker_timer * 37.0)

        beam_start = BEAM_START_X
        beam_end = GRID_SIZE - 1
        beam_width_start = 2
        beam_width_end = 10

        for bx in range(beam_start, beam_end + 1):
            t = (bx - beam_start) / max(1, beam_end - beam_start)
            half_w = beam_width_start + t * (beam_width_end - beam_width_start)
            half_w = half_w * 0.5

            if t < 0.2:
                base = BEAM_BRIGHT
            elif t < 0.45:
                base = BEAM_MID
            elif t < 0.7:
                base = BEAM_DIM
            else:
                base = BEAM_FAINT

            for dy_i in range(int(-half_w) - 1, int(half_w) + 2):
                py = BEAM_Y + dy_i
                if py < 0 or py >= GRID_SIZE:
                    continue

                dist_from_center = abs(dy_i) / max(0.5, half_w)
                if dist_from_center > 1.0:
                    continue

                edge_fade = max(0.0, 1.0 - dist_from_center * dist_from_center)
                r = int(base[0] * edge_fade * flicker)
                g = int(base[1] * edge_fade * flicker)
                b = int(base[2] * edge_fade * flicker)
                r = min(255, max(0, r))
                g = min(255, max(0, g))
                b = min(255, max(0, b))

                if r > 5 or g > 5 or b > 5:
                    d.set_pixel(bx, py, (r, g, b))

    def _draw_hud(self, d):
        """Draw speed indicator text."""
        fps = SPEED_FPS[self.speed_level - 1]
        d.draw_text_small(2, 2, f"{fps} FPS", HUD_COLOR)
        d.draw_text_small(2, 58, "PROJECTOR", HUD_COLOR)
