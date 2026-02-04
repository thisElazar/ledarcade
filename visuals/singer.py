"""
Singer Sewing Machine
=====================
Side-view cutaway of a classic black-and-gold Singer treadle sewing machine.
The hand wheel drives a needle bar via crank-slider linkage. Thread loops
through a bobbin mechanism beneath the fabric. Fabric feeds in discrete
steps, accumulating visible stitch marks.

Controls:
  Left/Right - Adjust stitch speed (6 levels)
"""

import math
from . import Visual, Display, Colors, GRID_SIZE


# --- Color Palette ---

# Machine body
BODY_COLOR = (20, 20, 25)
BODY_DARK = (12, 12, 16)
GOLD_TRIM = (200, 170, 50)
GOLD_DIM = (140, 120, 35)
GOLD_BRIGHT = (230, 200, 70)

# Hand wheel
WHEEL_RIM = (180, 180, 190)
WHEEL_DARK = (110, 110, 120)
WHEEL_SPOKE = (100, 100, 110)
WHEEL_HUB = (200, 200, 210)

# Needle and bar
NEEDLE_BAR = (190, 190, 200)
NEEDLE_COLOR = (220, 220, 230)

# Connecting rod and crank
ROD_COLOR = (170, 170, 180)
CRANK_PIN = (255, 220, 80)

# Fabric
FABRIC_COLOR = (180, 150, 100)
FABRIC_DARK = (150, 125, 80)
FABRIC_EDGE = (130, 105, 65)

# Thread
THREAD_COLOR = (220, 40, 40)
THREAD_DIM = (160, 30, 30)

# Bobbin
BOBBIN_COLOR = (200, 120, 60)
BOBBIN_DARK = (150, 85, 40)
BOBBIN_HUB = (220, 140, 80)

# Hook / shuttle
HOOK_COLOR = (220, 200, 160)
HOOK_BRIGHT = (255, 240, 200)
SHUTTLE_RACE = (90, 90, 100)
CATCH_FLASH = (255, 255, 200)
BOBBIN_THREAD = (140, 25, 25)

# Stitch marks
STITCH_COLOR = (180, 35, 35)

# Table / base
TABLE_COLOR = (60, 40, 20)
TABLE_HIGHLIGHT = (80, 55, 30)

# HUD
HUD_COLOR = (160, 160, 170)

# --- Layout Constants ---

# Hand wheel (right side)
WHEEL_CX = 52
WHEEL_CY = 38
WHEEL_R = 8
CRANK_R = 5  # crank pin orbit radius on the hand wheel

# Needle position (horizontal constraint for crank-slider)
NEEDLE_X = 18

# Connecting rod length (crank pin to needle bar pivot)
ROD_LEN = 38

# Fabric band
FABRIC_Y_TOP = 34
FABRIC_Y_BOT = 36
FABRIC_LEFT = 2
FABRIC_RIGHT = 62

# Bobbin (below fabric)
BOBBIN_CX = 18
BOBBIN_CY = 42
BOBBIN_R = 4

# Machine arm (connects wheel area to needle head area)
ARM_Y_TOP = 20
ARM_Y_BOT = 24

# Needle head housing
HEAD_LEFT = 14
HEAD_RIGHT = 23
HEAD_TOP = 16
HEAD_BOT = 28

# Table surface
TABLE_Y = 56

# Thread spool position (top of machine)
SPOOL_X = 30
SPOOL_Y = 14

# Speed levels
SPEED_RPMS = [20, 60, 120, 200, 300, 400]


class Singer(Visual):
    name = "SINGER"
    description = "Sewing machine"
    category = "mechanics"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.theta = 0.0  # hand wheel angle (radians)
        self.speed_level = 3  # 1-6
        self.fabric_offset = 0  # pixel offset for fabric scroll
        self.last_half_id = 0  # for detecting stitch cycle completion
        self.stitches = []  # list of x positions (in fabric-local coords)
        self.stitch_count = 0
        self.hook_angle = 0.0  # rotating hook angle (1:1 with main shaft)
        self.catch_flash_timer = 0.0  # countdown for catch flash effect

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

        # Rotation speed from RPM
        rpm = SPEED_RPMS[self.speed_level - 1]
        omega = rpm * 2.0 * math.pi / 60.0
        self.theta += omega * dt

        # Hook rotates 1:1 with main shaft
        self.hook_angle = self.theta % (2.0 * math.pi)

        # Catch flash: trigger when hook is near 90 degrees (catch point)
        # and needle is below fabric
        hook_deg = math.degrees(self.hook_angle)
        if 85 < hook_deg < 95:
            self.catch_flash_timer = 0.15  # flash duration in seconds
        if self.catch_flash_timer > 0:
            self.catch_flash_timer -= dt

        # Detect stitch cycle completion (needle reaches top dead center)
        half_id = int(self.theta / math.pi)
        if half_id != self.last_half_id:
            if half_id % 2 == 0:
                # Needle at top = one stitch completed, advance fabric
                self.fabric_offset += 1
                self.stitch_count += 1
                # Record stitch position in fabric-local coordinates
                # The stitch appears at the needle X relative to fabric offset
                stitch_local_x = NEEDLE_X + self.fabric_offset
                self.stitches.append(stitch_local_x)
                # Prune old stitches that have scrolled off screen
                min_visible = self.fabric_offset - GRID_SIZE
                self.stitches = [s for s in self.stitches if s > min_visible]
            self.last_half_id = half_id

    def _get_needle_tip_y(self):
        """Compute needle tip Y using crank-slider kinematics.

        The crank pin orbits on the hand wheel. A connecting rod links
        the crank pin to the needle bar, which is constrained to move
        vertically at x = NEEDLE_X.

        Returns the needle bar y position (top of needle).
        """
        # Crank pin position on hand wheel
        cpx = WHEEL_CX + CRANK_R * math.sin(self.theta)
        cpy = WHEEL_CY - CRANK_R * math.cos(self.theta)

        # Crank-slider: needle bar constrained at x = NEEDLE_X
        dx = cpx - NEEDLE_X
        disc = ROD_LEN ** 2 - dx ** 2
        needle_bar_y = cpy - math.sqrt(max(0.0, disc))

        return needle_bar_y, cpx, cpy

    def draw(self):
        d = self.display
        d.clear(Colors.BLACK)

        # Compute needle position for this frame
        needle_bar_y, cpx, cpy = self._get_needle_tip_y()

        # Draw order: back to front
        self._draw_table(d)
        self._draw_bobbin_area(d)
        self._draw_fabric(d)
        self._draw_machine_body(d)
        self._draw_hand_wheel(d)
        self._draw_connecting_rod(d, cpx, cpy, needle_bar_y)
        self._draw_needle(d, needle_bar_y)
        self._draw_thread(d, needle_bar_y)
        self._draw_spool(d)
        self._draw_hud(d)

    def _draw_table(self, d):
        """Draw the table/base the machine sits on."""
        d.draw_rect(0, TABLE_Y, GRID_SIZE, GRID_SIZE - TABLE_Y, TABLE_COLOR)
        d.draw_line(0, TABLE_Y, 63, TABLE_Y, TABLE_HIGHLIGHT)

    def _draw_machine_body(self, d):
        """Draw the iconic Singer silhouette: curved arm from wheel to needle head."""
        # Needle head housing (vertical block on left)
        d.draw_rect(HEAD_LEFT, HEAD_TOP, HEAD_RIGHT - HEAD_LEFT, HEAD_BOT - HEAD_TOP, BODY_COLOR)
        # Gold filigree on head
        d.draw_line(HEAD_LEFT, HEAD_TOP, HEAD_RIGHT - 1, HEAD_TOP, GOLD_TRIM)
        d.draw_line(HEAD_LEFT, HEAD_BOT - 1, HEAD_RIGHT - 1, HEAD_BOT - 1, GOLD_DIM)

        # Horizontal arm connecting head to wheel area
        arm_left = HEAD_RIGHT
        arm_right = WHEEL_CX + 2
        d.draw_rect(arm_left, ARM_Y_TOP, arm_right - arm_left, ARM_Y_BOT - ARM_Y_TOP, BODY_COLOR)
        # Gold trim along top edge of arm
        d.draw_line(arm_left, ARM_Y_TOP, arm_right - 1, ARM_Y_TOP, GOLD_TRIM)
        # Gold trim along bottom edge of arm
        d.draw_line(arm_left, ARM_Y_BOT - 1, arm_right - 1, ARM_Y_BOT - 1, GOLD_DIM)
        # Gold decorative dot pattern on the arm
        for gx in range(arm_left + 3, arm_right - 2, 4):
            d.set_pixel(gx, ARM_Y_TOP + 2, GOLD_BRIGHT)

        # Vertical pillar on right side (wheel housing)
        pillar_left = WHEEL_CX - 4
        pillar_right = WHEEL_CX + 5
        d.draw_rect(pillar_left, ARM_Y_BOT, pillar_right - pillar_left,
                     WHEEL_CY - WHEEL_R - ARM_Y_BOT, BODY_COLOR)

        # Curved transition from arm down to needle head
        # Simple diagonal fill to suggest the Singer curve
        for dy in range(HEAD_BOT, FABRIC_Y_TOP):
            curve_x = HEAD_LEFT + 1
            d.set_pixel(curve_x, dy, BODY_COLOR)
            d.set_pixel(curve_x + 1, dy, BODY_COLOR)
            d.set_pixel(curve_x - 1, dy, BODY_DARK)

        # Bed plate (flat surface under fabric, machine base)
        bed_left = HEAD_LEFT - 4
        bed_right = WHEEL_CX + 6
        bed_top = FABRIC_Y_BOT + 1
        bed_bot = TABLE_Y
        d.draw_rect(bed_left, bed_top, bed_right - bed_left, bed_bot - bed_top, BODY_COLOR)
        # Gold trim on bed plate top
        d.draw_line(bed_left, bed_top, bed_right - 1, bed_top, GOLD_DIM)

        # Throat plate opening (where needle goes through)
        d.set_pixel(NEEDLE_X - 1, bed_top, BODY_DARK)
        d.set_pixel(NEEDLE_X, bed_top, BODY_DARK)
        d.set_pixel(NEEDLE_X + 1, bed_top, BODY_DARK)

        # Gold "SINGER" text suggestion on the arm (just a couple bright pixels)
        text_y = ARM_Y_TOP + 1
        for tx in range(arm_left + 2, arm_left + 10):
            if tx < arm_right - 1:
                d.set_pixel(tx, text_y, GOLD_DIM)

    def _draw_hand_wheel(self, d):
        """Draw the large hand wheel with rotating spokes."""
        cx, cy, r = WHEEL_CX, WHEEL_CY, WHEEL_R

        # Outer rim (circle outline)
        self._draw_circle_pixels(d, cx, cy, r, WHEEL_RIM)
        self._draw_circle_pixels(d, cx, cy, r - 1, WHEEL_DARK)

        # Inner rim
        self._draw_circle_pixels(d, cx, cy, r - 3, WHEEL_DARK)

        # Rotating spokes (6 spokes)
        num_spokes = 6
        spoke_inner = 2
        spoke_outer = r - 3
        for s in range(num_spokes):
            angle = self.theta + s * 2.0 * math.pi / num_spokes
            x0 = cx + int(round(spoke_inner * math.cos(angle)))
            y0 = cy + int(round(spoke_inner * math.sin(angle)))
            x1 = cx + int(round(spoke_outer * math.cos(angle)))
            y1 = cy + int(round(spoke_outer * math.sin(angle)))
            d.draw_line(x0, y0, x1, y1, WHEEL_SPOKE)

        # Hub center
        d.set_pixel(cx, cy, WHEEL_HUB)
        d.set_pixel(cx - 1, cy, WHEEL_HUB)
        d.set_pixel(cx + 1, cy, WHEEL_HUB)
        d.set_pixel(cx, cy - 1, WHEEL_HUB)
        d.set_pixel(cx, cy + 1, WHEEL_HUB)

        # Crank pin (rotating bright dot)
        pin_x = cx + int(round(CRANK_R * math.sin(self.theta)))
        pin_y = cy - int(round(CRANK_R * math.cos(self.theta)))
        d.set_pixel(pin_x, pin_y, CRANK_PIN)
        d.set_pixel(pin_x + 1, pin_y, CRANK_PIN)
        d.set_pixel(pin_x, pin_y + 1, CRANK_PIN)

    def _draw_circle_pixels(self, d, cx, cy, r, color):
        """Midpoint circle algorithm for pixel-perfect circle outline."""
        if r < 0:
            return
        x = r
        y = 0
        err = 1 - r
        while x >= y:
            d.set_pixel(cx + x, cy + y, color)
            d.set_pixel(cx - x, cy + y, color)
            d.set_pixel(cx + x, cy - y, color)
            d.set_pixel(cx - x, cy - y, color)
            d.set_pixel(cx + y, cy + x, color)
            d.set_pixel(cx - y, cy + x, color)
            d.set_pixel(cx + y, cy - x, color)
            d.set_pixel(cx - y, cy - x, color)
            y += 1
            if err < 0:
                err += 2 * y + 1
            else:
                x -= 1
                err += 2 * (y - x) + 1

    def _draw_connecting_rod(self, d, cpx, cpy, needle_bar_y):
        """Draw the connecting rod from crank pin to needle bar."""
        pin_ix = int(round(cpx))
        pin_iy = int(round(cpy))
        bar_ix = NEEDLE_X
        bar_iy = int(round(needle_bar_y))

        # Rod line (with thickness)
        d.draw_line(pin_ix, pin_iy, bar_ix, bar_iy, ROD_COLOR)
        d.draw_line(pin_ix + 1, pin_iy, bar_ix + 1, bar_iy, ROD_COLOR)

        # Crank pin highlight on top of rod
        d.set_pixel(pin_ix, pin_iy, CRANK_PIN)

    def _draw_needle(self, d, needle_bar_y):
        """Draw the needle bar and needle. The needle pierces through the fabric."""
        bar_iy = int(round(needle_bar_y))

        # Needle bar (vertical steel bar from head down to needle tip area)
        bar_top = bar_iy
        bar_bottom = bar_iy + 10  # needle bar extends below pivot point

        # Clamp bar_top into the head area
        bar_top = max(HEAD_TOP + 2, bar_top)

        # Draw needle bar
        d.draw_line(NEEDLE_X, bar_top, NEEDLE_X, bar_bottom, NEEDLE_BAR)

        # Presser foot (small horizontal piece at fabric level)
        foot_y = FABRIC_Y_TOP - 1
        d.set_pixel(NEEDLE_X - 1, foot_y, WHEEL_DARK)
        d.set_pixel(NEEDLE_X, foot_y, WHEEL_RIM)
        d.set_pixel(NEEDLE_X + 1, foot_y, WHEEL_DARK)

        # Needle itself (bright, thin, extends below bar)
        needle_top = bar_bottom
        needle_tip_y = bar_bottom + 6  # needle length
        d.draw_line(NEEDLE_X, needle_top, NEEDLE_X, needle_tip_y, NEEDLE_COLOR)

        # Needle eye (tiny dot near tip)
        eye_y = needle_tip_y - 2
        d.set_pixel(NEEDLE_X, eye_y, THREAD_COLOR)

    def _draw_thread(self, d, needle_bar_y):
        """Draw thread from spool to needle eye, with phase-based loop below fabric.

        The hook catches the upper thread loop, carries it around the bobbin,
        and releases it to form a lockstitch interlock with the bobbin thread.
        """
        bar_iy = int(round(needle_bar_y))
        needle_tip_y = bar_iy + 10 + 6  # matches needle drawing
        needle_eye_y = needle_tip_y - 2

        # Upper thread: spool -> thread guide on arm -> needle eye
        guide_x = NEEDLE_X
        guide_y = HEAD_TOP + 1

        # Spool to guide
        d.draw_line(SPOOL_X, SPOOL_Y, guide_x, guide_y, THREAD_COLOR)

        # Guide down to needle eye
        d.draw_line(guide_x, guide_y, NEEDLE_X, needle_eye_y, THREAD_COLOR)

        # Bobbin thread: persistent path from bobbin up through throat plate
        # to fabric underside — this thread is always present
        cx, cy, r = BOBBIN_CX, BOBBIN_CY, BOBBIN_R
        hook_r = r + 2
        throat_y = FABRIC_Y_BOT + 1  # throat plate surface
        d.draw_line(cx, cy, cx, throat_y, BOBBIN_THREAD)

        # Lower thread: phase-dependent upper-thread loop below fabric
        # Only visible when needle is below the fabric
        if needle_tip_y <= FABRIC_Y_TOP:
            return

        hook_deg = math.degrees(self.hook_angle)

        if hook_deg < 90:
            # Phase 1: Approaching — thread goes straight from needle to bobbin area
            target_y = min(needle_tip_y + 2, cy - r)
            if target_y > FABRIC_Y_BOT:
                d.draw_line(NEEDLE_X, needle_tip_y, cx, target_y, THREAD_DIM)

        elif hook_deg < 180:
            # Phase 2: Catching + carrying — thread loops from needle to hook tip
            # then around toward the bobbin
            phase_t = (hook_deg - 90) / 90.0  # 0 to 1

            # Hook tip position
            tip_a = self.hook_angle
            tip_x = int(round(cx + hook_r * math.cos(tip_a)))
            tip_y = int(round(cy + hook_r * math.sin(tip_a)))

            # Thread from needle tip to hook tip
            d.draw_line(NEEDLE_X, needle_tip_y, tip_x, tip_y, THREAD_COLOR)

            # Thread from hook tip curving around bobbin (partial arc)
            arc_end_angle = self.hook_angle + math.pi * phase_t
            steps = max(4, int(8 * phase_t))
            prev_x, prev_y = tip_x, tip_y
            for i in range(1, steps + 1):
                t = i / steps
                a = self.hook_angle + t * math.pi * phase_t
                ax = int(round(cx + hook_r * math.cos(a)))
                ay = int(round(cy + hook_r * math.sin(a)))
                d.draw_line(prev_x, prev_y, ax, ay, THREAD_DIM)
                prev_x, prev_y = ax, ay

        elif hook_deg < 270:
            # Phase 3: Carrying around — loop at maximum, wrapping the bobbin
            phase_t = (hook_deg - 180) / 90.0  # 0 to 1

            # Hook tip
            tip_a = self.hook_angle
            tip_x = int(round(cx + hook_r * math.cos(tip_a)))
            tip_y = int(round(cy + hook_r * math.sin(tip_a)))

            # Thread from needle down to one side of bobbin
            d.draw_line(NEEDLE_X, needle_tip_y, cx - hook_r, cy, THREAD_COLOR)

            # Large loop around bobbin: arc from one side through hook tip
            arc_start = math.pi  # left side
            arc_end = self.hook_angle
            arc_span = (arc_end - arc_start) % (2.0 * math.pi)
            steps = max(6, int(12 * (arc_span / (2.0 * math.pi))))
            prev_x = int(round(cx + hook_r * math.cos(arc_start)))
            prev_y = int(round(cy + hook_r * math.sin(arc_start)))
            for i in range(1, steps + 1):
                t = i / steps
                a = arc_start + t * arc_span
                ax = int(round(cx + hook_r * math.cos(a)))
                ay = int(round(cy + hook_r * math.sin(a)))
                d.draw_line(prev_x, prev_y, ax, ay, THREAD_DIM)
                prev_x, prev_y = ax, ay

            # Thread from hook tip back up to needle area
            d.draw_line(tip_x, tip_y, NEEDLE_X + 1, needle_tip_y + 1, THREAD_DIM)

        else:
            # Phase 4: Releasing — loop slips off, thread pulls tight
            phase_t = (hook_deg - 270) / 90.0  # 0 to 1

            # Thread tightens: goes from needle straight down past bobbin
            # and the loop shrinks as it slides off
            tighten = 1.0 - phase_t  # decreasing loop size

            if tighten > 0.1:
                # Shrinking loop
                loop_r = hook_r * tighten
                d.draw_line(NEEDLE_X, needle_tip_y, cx, cy - int(round(loop_r)),
                            THREAD_COLOR)
                # Small remnant arc
                arc_steps = max(3, int(6 * tighten))
                start_a = -math.pi / 2.0
                span = math.pi * tighten
                prev_x = int(round(cx + loop_r * math.cos(start_a)))
                prev_y = int(round(cy + loop_r * math.sin(start_a)))
                for i in range(1, arc_steps + 1):
                    t = i / arc_steps
                    a = start_a + t * span
                    ax = int(round(cx + loop_r * math.cos(a)))
                    ay = int(round(cy + loop_r * math.sin(a)))
                    d.draw_line(prev_x, prev_y, ax, ay, THREAD_DIM)
                    prev_x, prev_y = ax, ay
            else:
                # Thread fully tight — simple straight line
                target_y = min(needle_tip_y + 2, cy - r)
                if target_y > FABRIC_Y_BOT:
                    d.draw_line(NEEDLE_X, needle_tip_y, cx, target_y, THREAD_DIM)

    def _draw_spool(self, d):
        """Draw thread spool at top of machine."""
        # Spool is a small cylinder shape at the spool position
        d.draw_rect(SPOOL_X - 2, SPOOL_Y - 2, 5, 4, THREAD_COLOR)
        d.draw_rect(SPOOL_X - 3, SPOOL_Y - 2, 1, 4, THREAD_DIM)
        d.draw_rect(SPOOL_X + 3, SPOOL_Y - 2, 1, 4, THREAD_DIM)
        # Spool holder
        d.set_pixel(SPOOL_X, SPOOL_Y + 2, BODY_COLOR)

    def _draw_fabric(self, d):
        """Draw the fabric band with scrolling texture and stitch marks."""
        # Fabric band across the machine bed
        for y in range(FABRIC_Y_TOP, FABRIC_Y_BOT + 1):
            for x in range(FABRIC_LEFT, FABRIC_RIGHT + 1):
                # Scrolling texture pattern (weave effect)
                tx = (x + self.fabric_offset) % 4
                if y == FABRIC_Y_TOP:
                    color = FABRIC_EDGE
                elif y == FABRIC_Y_BOT:
                    color = FABRIC_EDGE
                elif tx < 2:
                    color = FABRIC_COLOR
                else:
                    color = FABRIC_DARK
                d.set_pixel(x, y, color)

        # Draw stitch marks on the fabric surface
        stitch_y = FABRIC_Y_TOP  # stitches appear on top of fabric
        for stitch_x_local in self.stitches:
            # Convert from fabric-local to screen coordinates
            screen_x = stitch_x_local - self.fabric_offset
            if FABRIC_LEFT <= screen_x <= FABRIC_RIGHT:
                d.set_pixel(screen_x, stitch_y, STITCH_COLOR)
                # Small cross-stitch effect
                if FABRIC_LEFT <= screen_x <= FABRIC_RIGHT:
                    d.set_pixel(screen_x, stitch_y + 1, STITCH_COLOR)

    def _draw_bobbin_area(self, d):
        """Draw the bobbin mechanism below the fabric with shuttle race and hook."""
        cx, cy, r = BOBBIN_CX, BOBBIN_CY, BOBBIN_R
        hook_r = r + 2  # hook orbits at this radius

        # Shuttle race housing (outer circle)
        race_r = r + 3
        self._draw_circle_pixels(d, cx, cy, race_r, SHUTTLE_RACE)

        # Bobbin case (background fill)
        d.draw_circle(cx, cy, r + 1, BODY_DARK, filled=True)

        # Bobbin disc (rotates with main shaft)
        bobbin_theta = self.theta * 1.5
        self._draw_circle_pixels(d, cx, cy, r, BOBBIN_COLOR)
        self._draw_circle_pixels(d, cx, cy, r - 1, BOBBIN_DARK)

        # Rotating marks on bobbin to show rotation
        num_marks = 4
        for m in range(num_marks):
            angle = bobbin_theta + m * 2.0 * math.pi / num_marks
            mx = cx + int(round((r - 1) * math.cos(angle)))
            my = cy + int(round((r - 1) * math.sin(angle)))
            d.set_pixel(mx, my, BOBBIN_HUB)

        # Bobbin hub center
        d.set_pixel(cx, cy, BOBBIN_HUB)

        # Thread wound on bobbin (colored ring)
        for m in range(6):
            angle = bobbin_theta * 0.8 + m * 2.0 * math.pi / 6
            tx = cx + int(round(2 * math.cos(angle)))
            ty = cy + int(round(2 * math.sin(angle)))
            d.set_pixel(tx, ty, BOBBIN_THREAD)

        # Rotating hook arm (~90 degree arc at hook_r)
        self._draw_hook(d, cx, cy, hook_r)

    def _draw_hook(self, d, cx, cy, hook_r):
        """Draw the rotating hook arm that catches and carries the upper thread."""
        # Hook is a ~90 degree bright arc rotating around the bobbin
        hook_start = self.hook_angle
        hook_span = math.pi / 2.0  # 90 degrees

        # Draw arc pixels
        num_steps = 16
        for i in range(num_steps + 1):
            t = i / num_steps
            a = hook_start + t * hook_span

            hx = cx + hook_r * math.cos(a)
            hy = cy + hook_r * math.sin(a)
            ipx = int(round(hx))
            ipy = int(round(hy))

            # Hook tip is brighter (leading edge)
            if i < 3:
                color = HOOK_BRIGHT
            else:
                color = HOOK_COLOR
            d.set_pixel(ipx, ipy, color)

        # Hook tip: extra bright pixel at the leading edge
        tip_a = hook_start
        tip_x = int(round(cx + hook_r * math.cos(tip_a)))
        tip_y = int(round(cy + hook_r * math.sin(tip_a)))
        d.set_pixel(tip_x, tip_y, HOOK_BRIGHT)

        # Catch flash: brief bright pulse when hook catches thread
        if self.catch_flash_timer > 0:
            flash_intensity = min(1.0, self.catch_flash_timer / 0.1)
            fr = int(CATCH_FLASH[0] * flash_intensity)
            fg = int(CATCH_FLASH[1] * flash_intensity)
            fb = int(CATCH_FLASH[2] * flash_intensity)
            d.set_pixel(tip_x, tip_y, (fr, fg, fb))
            # Flash neighbors
            for ddx, ddy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = tip_x + ddx, tip_y + ddy
                fr2 = int(fr * 0.5)
                fg2 = int(fg * 0.5)
                fb2 = int(fb * 0.5)
                d.set_pixel(nx, ny, (fr2, fg2, fb2))

    def _draw_hud(self, d):
        """Draw speed indicator."""
        spm = SPEED_RPMS[self.speed_level - 1]
        d.draw_text_small(2, 2, f"{spm} SPM", HUD_COLOR)

        # Stitch counter
        d.draw_text_small(2, 8, f"{self.stitch_count} ST", HUD_COLOR)
