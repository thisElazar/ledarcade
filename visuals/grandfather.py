"""
Grandfather Clock
=================
Tall pendulum swinging behind an exposed escapement wheel.
The anchor/pallet fork catches and releases escapement teeth,
creating the characteristic tick-tock. Gear train visible
connecting escapement to clock hands.

Controls:
  Left/Right - Adjust BPM (pendulum speed)
"""

import math
from . import Visual, Display, Colors, GRID_SIZE


# Color palette
BG_COLOR = (10, 8, 5)
CASE_DARK = (60, 35, 15)
CASE_MID = (80, 50, 20)
CASE_LIGHT = (100, 65, 30)
PENDULUM_ARM = (200, 170, 50)
PENDULUM_BOB = (180, 150, 40)
BOB_HIGHLIGHT = (220, 195, 70)
ESCAPE_WHEEL = (180, 180, 190)
ESCAPE_TOOTH = (200, 200, 215)
ESCAPE_HUB = (140, 140, 150)
ANCHOR_COLOR = (200, 120, 60)
ANCHOR_BRIGHT = (230, 150, 80)
TICK_FLASH = (255, 255, 200)
HUD_COLOR = (160, 160, 170)
HUD_DIM = (90, 90, 100)
HAND_COLOR = (200, 200, 210)
HAND_MIN = (170, 170, 180)
FACE_COLOR = (40, 35, 30)
FACE_MARK = (120, 110, 90)
GEAR_SMALL = (160, 140, 50)
GEAR_SMALL_TOOTH = (190, 170, 70)


class GrandfatherClock(Visual):
    name = "GRANDFATHER"
    description = "Escapement clock"
    category = "mechanics"

    # Layout
    PIVOT_X = 32
    PIVOT_Y = 22
    PEND_LENGTH_MIN = 22
    PEND_LENGTH_MAX = 40
    BOB_RADIUS = 3
    MAX_ANGLE = 0.38          # max pendulum swing in radians

    # Escapement wheel
    ESCAPE_CX = 32
    ESCAPE_CY = 22
    ESCAPE_TEETH = 12
    ESCAPE_OUTER_R = 9
    ESCAPE_INNER_R = 6

    # Anchor geometry
    ANCHOR_LEN = 11           # arm length from pivot to pallet tip
    ANCHOR_SPREAD = 0.55      # half-angle of anchor fork (radians)
    ANCHOR_ROCK = 0.15        # how far anchor rocks with pendulum

    # Clock face
    FACE_CX = 32
    FACE_CY = 8
    FACE_R = 6

    # Gear between escapement and face
    GEAR_CX = 32
    GEAR_CY = 15
    GEAR_R = 3
    GEAR_TEETH_N = 8

    # Case dimensions
    CASE_X = 14
    CASE_Y = 0
    CASE_W = 36
    CASE_H = 64

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.bpm = 30                  # ticks per minute (one tick = one pendulum extreme)
        self.phase = 0.0               # pendulum phase (continuous)
        self.last_tick_id = 0          # last detected tick (half-period crossing)
        self.flash_timer = 0.0         # tick flash duration remaining
        self.tick_side = 0             # 0 = left extreme, 1 = right extreme

        # Escapement state
        self.escape_angle = 0.0        # current wheel angle (radians)
        self.escape_target = 0.0       # target angle (advances in discrete steps)
        self.step_size = 2.0 * math.pi / self.ESCAPE_TEETH

        # Pendulum length (visual, controlled by BPM)
        self._update_pendulum_length()

        # Clock hands (driven by escapement advancement)
        self.total_ticks = 0
        self.hand_hour_angle = 0.0
        self.hand_min_angle = 0.0

        # Gear rotation (small connecting gear)
        self.gear_angle = 0.0

    def _update_pendulum_length(self):
        """Compute pendulum display length from BPM. Slower = longer."""
        t = (self.bpm - 10) / (60 - 10)  # 0 at 10 BPM, 1 at 60 BPM
        t = max(0.0, min(1.0, t))
        # Shorter pendulum = faster, longer = slower
        self.pend_length = self.PEND_LENGTH_MAX - t * (self.PEND_LENGTH_MAX - self.PEND_LENGTH_MIN)

    def handle_input(self, input_state):
        consumed = False
        if input_state.right_pressed:
            self.bpm = min(60, self.bpm + 5)
            self._update_pendulum_length()
            consumed = True
        elif input_state.left_pressed:
            self.bpm = max(10, self.bpm - 5)
            self._update_pendulum_length()
            consumed = True
        return consumed

    def update(self, dt):
        self.time += dt

        # Advance pendulum phase
        # One full phase unit = one complete period (two ticks: tick + tock)
        # Ticks per second = bpm / 60
        # Phase advances at bpm / 120 per second (two ticks per period)
        self.phase += (self.bpm / 120.0) * dt

        # Detect tick at pendulum extremes
        # Pendulum angle = MAX_ANGLE * sin(phase * 2 * pi)
        # Extremes occur at phase = 0.25, 0.75, 1.25, ... i.e. every 0.5 phase units
        # We track tick_id = floor(phase * 2) to detect each half-period crossing
        tick_id = int(self.phase * 2.0)
        if tick_id != self.last_tick_id:
            self.last_tick_id = tick_id
            self.flash_timer = 0.12
            self.tick_side = tick_id % 2  # 0 or 1

            # Advance escapement wheel one tooth
            self.escape_target += self.step_size
            self.total_ticks += 1

            # Update clock hands
            # Minute hand: full revolution per 60 ticks (arbitrary mapping for visual interest)
            self.hand_min_angle = (self.total_ticks / 60.0) * 2.0 * math.pi
            # Hour hand: full revolution per 720 ticks
            self.hand_hour_angle = (self.total_ticks / 720.0) * 2.0 * math.pi

        # Ease escapement wheel toward target (quick animated step)
        if self.escape_angle < self.escape_target:
            diff = self.escape_target - self.escape_angle
            step = self.step_size * 12.0 * dt  # fast ease-out
            self.escape_angle += min(diff, step)

        # Gear rotation tracks escapement (with ratio)
        self.gear_angle = self.escape_angle * (self.ESCAPE_TEETH / self.GEAR_TEETH_N)

        # Decay flash timer
        if self.flash_timer > 0:
            self.flash_timer = max(0.0, self.flash_timer - dt)

    def draw(self):
        d = self.display
        d.clear(BG_COLOR)

        self._draw_case(d)
        self._draw_clock_face(d)
        self._draw_gear(d)
        self._draw_escapement(d)
        self._draw_anchor(d)
        self._draw_pendulum(d)
        self._draw_tick_flash(d)
        self._draw_hud(d)

    def _draw_case(self, d):
        """Draw the grandfather clock case as a dark wooden frame."""
        x0 = self.CASE_X
        y0 = self.CASE_Y
        w = self.CASE_W
        h = self.CASE_H

        # Left edge
        for y in range(y0, y0 + h):
            d.set_pixel(x0, y, CASE_DARK)
            d.set_pixel(x0 + 1, y, CASE_MID)
        # Right edge
        for y in range(y0, y0 + h):
            d.set_pixel(x0 + w - 1, y, CASE_DARK)
            d.set_pixel(x0 + w - 2, y, CASE_MID)
        # Top edge
        for x in range(x0, x0 + w):
            d.set_pixel(x, y0, CASE_DARK)
        # Bottom edge
        for x in range(x0, x0 + w):
            d.set_pixel(x, y0 + h - 1, CASE_DARK)

        # Top decorative arch (subtle)
        d.set_pixel(x0 + 2, y0 + 1, CASE_LIGHT)
        d.set_pixel(x0 + w - 3, y0 + 1, CASE_LIGHT)

        # Vertical trim lines inside
        for y in range(y0 + 2, y0 + h - 2):
            if y % 8 < 6:
                d.set_pixel(x0 + 2, y, CASE_DARK)
                d.set_pixel(x0 + w - 3, y, CASE_DARK)

    def _draw_clock_face(self, d):
        """Draw a small clock face with hour and minute hands."""
        cx = self.FACE_CX
        cy = self.FACE_CY
        r = self.FACE_R

        # Face background
        d.draw_circle(cx, cy, r, FACE_COLOR, filled=True)
        d.draw_circle(cx, cy, r, FACE_MARK, filled=False)

        # Hour marks (12 positions)
        for i in range(12):
            a = i * math.pi / 6.0
            mx = cx + int(round((r - 1) * math.sin(a)))
            my = cy - int(round((r - 1) * math.cos(a)))
            d.set_pixel(mx, my, FACE_MARK)

        # Hour hand (short)
        hx = cx + int(round((r - 3) * math.sin(self.hand_hour_angle)))
        hy = cy - int(round((r - 3) * math.cos(self.hand_hour_angle)))
        d.draw_line(cx, cy, hx, hy, HAND_COLOR)

        # Minute hand (longer)
        mx = cx + int(round((r - 1) * math.sin(self.hand_min_angle)))
        my = cy - int(round((r - 1) * math.cos(self.hand_min_angle)))
        d.draw_line(cx, cy, mx, my, HAND_MIN)

        # Center dot
        d.set_pixel(cx, cy, HAND_COLOR)

    def _draw_gear(self, d):
        """Draw small connecting gear between escapement and clock face."""
        cx = self.GEAR_CX
        cy = self.GEAR_CY
        r = self.GEAR_R
        n = self.GEAR_TEETH_N
        angle = self.gear_angle
        step = 2.0 * math.pi / n

        # Gear body
        d.draw_circle(cx, cy, r - 1, GEAR_SMALL, filled=True)

        # Teeth
        for i in range(n):
            ta = angle + i * step
            # Tooth tip at outer radius
            tx = cx + int(round((r + 1) * math.cos(ta)))
            ty = cy + int(round((r + 1) * math.sin(ta)))
            # Tooth base
            bx = cx + int(round(r * math.cos(ta + step * 0.3)))
            by = cy + int(round(r * math.sin(ta + step * 0.3)))
            d.draw_line(tx, ty, bx, by, GEAR_SMALL_TOOTH)

        # Hub
        d.set_pixel(cx, cy, ESCAPE_HUB)

    def _draw_escapement(self, d):
        """Draw the escapement wheel with pointed teeth."""
        cx = self.ESCAPE_CX
        cy = self.ESCAPE_CY
        outer_r = self.ESCAPE_OUTER_R
        inner_r = self.ESCAPE_INNER_R
        n = self.ESCAPE_TEETH
        angle = self.escape_angle
        step = self.step_size
        half_tooth = step * 0.35

        # Inner circle (wheel body)
        d.draw_circle(cx, cy, inner_r - 1, ESCAPE_WHEEL, filled=True)

        # Draw teeth as lines from inner base to outer tip
        for i in range(n):
            tooth_angle = angle + i * step
            # Tooth tip
            tx = cx + outer_r * math.cos(tooth_angle)
            ty = cy + outer_r * math.sin(tooth_angle)
            # Tooth base (offset for pointed shape)
            bx = cx + inner_r * math.cos(tooth_angle + half_tooth)
            by = cy + inner_r * math.sin(tooth_angle + half_tooth)
            # Second base point for other side of tooth
            bx2 = cx + inner_r * math.cos(tooth_angle - half_tooth)
            by2 = cy + inner_r * math.sin(tooth_angle - half_tooth)

            d.draw_line(int(round(tx)), int(round(ty)),
                        int(round(bx)), int(round(by)), ESCAPE_TOOTH)
            d.draw_line(int(round(tx)), int(round(ty)),
                        int(round(bx2)), int(round(by2)), ESCAPE_TOOTH)

        # Hub dot
        d.set_pixel(cx, cy, ESCAPE_HUB)
        d.set_pixel(cx - 1, cy, ESCAPE_HUB)
        d.set_pixel(cx + 1, cy, ESCAPE_HUB)
        d.set_pixel(cx, cy - 1, ESCAPE_HUB)
        d.set_pixel(cx, cy + 1, ESCAPE_HUB)

        # Axle to connecting gear
        d.draw_line(cx, cy - inner_r, self.GEAR_CX, self.GEAR_CY + self.GEAR_R, ESCAPE_HUB)

    def _draw_anchor(self, d):
        """Draw the anchor/pallet fork that rocks with the pendulum."""
        cx = self.ESCAPE_CX
        cy = self.ESCAPE_CY

        # Anchor rocks based on pendulum position
        pend_angle = self.MAX_ANGLE * math.sin(self.phase * 2.0 * math.pi)
        rock = pend_angle * (self.ANCHOR_ROCK / self.MAX_ANGLE)

        # The anchor has two arms (pallets) extending from the pivot
        # downward-left and downward-right toward the escapement wheel
        arm_len = self.ANCHOR_LEN

        # Left pallet arm
        left_angle = math.pi / 2.0 + self.ANCHOR_SPREAD + rock
        lx = cx + int(round(arm_len * math.cos(left_angle)))
        ly = cy + int(round(arm_len * math.sin(left_angle)))

        # Right pallet arm
        right_angle = math.pi / 2.0 - self.ANCHOR_SPREAD + rock
        rx = cx + int(round(arm_len * math.cos(right_angle)))
        ry = cy + int(round(arm_len * math.sin(right_angle)))

        # Arbor (short arm upward connecting to pendulum)
        arbor_angle = -math.pi / 2.0 + rock
        arbor_len = 4
        ax = cx + int(round(arbor_len * math.cos(arbor_angle)))
        ay = cy + int(round(arbor_len * math.sin(arbor_angle)))

        # Draw anchor arms
        d.draw_line(cx, cy, lx, ly, ANCHOR_COLOR)
        d.draw_line(cx, cy, rx, ry, ANCHOR_COLOR)
        d.draw_line(cx, cy, ax, ay, ANCHOR_COLOR)

        # Pallet tips (bright dots showing engagement points)
        # Highlight the engaging pallet
        if pend_angle > 0:
            # Swung right: left pallet is engaging (blocking)
            d.set_pixel(lx, ly, ANCHOR_BRIGHT)
            d.set_pixel(lx - 1, ly, ANCHOR_BRIGHT)
        else:
            # Swung left: right pallet is engaging (blocking)
            d.set_pixel(rx, ry, ANCHOR_BRIGHT)
            d.set_pixel(rx + 1, ry, ANCHOR_BRIGHT)

        # Pivot dot
        d.set_pixel(cx, cy, ANCHOR_BRIGHT)

    def _draw_pendulum(self, d):
        """Draw the pendulum arm and bob."""
        px = self.PIVOT_X
        py = self.PIVOT_Y

        # Pendulum angle from sinusoidal phase
        pend_angle = self.MAX_ANGLE * math.sin(self.phase * 2.0 * math.pi)

        # Arm extends downward from pivot
        arm_len = self.pend_length
        bob_x = px + arm_len * math.sin(pend_angle)
        bob_y = py + arm_len * math.cos(pend_angle)

        ibx = int(round(bob_x))
        iby = int(round(bob_y))

        # Draw arm
        d.draw_line(px, py, ibx, iby, PENDULUM_ARM)

        # Draw bob (filled circle)
        d.draw_circle(ibx, iby, self.BOB_RADIUS, PENDULUM_BOB, filled=True)

        # Bob highlight (upper left of bob)
        hx = ibx - 1
        hy = iby - 1
        d.set_pixel(hx, hy, BOB_HIGHLIGHT)
        d.set_pixel(hx + 1, hy, BOB_HIGHLIGHT)

        # Pivot bearing
        d.set_pixel(px, py, PENDULUM_ARM)
        d.set_pixel(px - 1, py, PENDULUM_ARM)
        d.set_pixel(px + 1, py, PENDULUM_ARM)

    def _draw_tick_flash(self, d):
        """Draw brief flash at pendulum bob when tick occurs."""
        if self.flash_timer <= 0:
            return

        brightness = self.flash_timer / 0.12
        r = int(TICK_FLASH[0] * brightness)
        g = int(TICK_FLASH[1] * brightness)
        b = int(TICK_FLASH[2] * brightness)
        flash = (r, g, b)

        # Flash at the current bob position
        pend_angle = self.MAX_ANGLE * math.sin(self.phase * 2.0 * math.pi)
        arm_len = self.pend_length
        bob_x = self.PIVOT_X + arm_len * math.sin(pend_angle)
        bob_y = self.PIVOT_Y + arm_len * math.cos(pend_angle)
        ibx = int(round(bob_x))
        iby = int(round(bob_y))

        # Radial flash around bob
        flash_r = self.BOB_RADIUS + 2
        for a in range(8):
            angle = a * math.pi / 4.0
            fx = ibx + int(round(flash_r * math.cos(angle)))
            fy = iby + int(round(flash_r * math.sin(angle)))
            d.set_pixel(fx, fy, flash)

    def _draw_hud(self, d):
        """Draw BPM and tick indicator."""
        # BPM display at top-left
        bpm_str = f"{self.bpm} BPM"
        d.draw_text_small(2, 2, bpm_str, HUD_COLOR)

        # Tick/Tock indicator at top-right
        if self.flash_timer > 0:
            label = "TICK" if self.tick_side == 0 else "TOCK"
            bright = self.flash_timer / 0.12
            r = int(HUD_COLOR[0] * bright)
            g = int(HUD_COLOR[1] * bright)
            b = int(HUD_COLOR[2] * bright)
            d.draw_text_small(2, 9, label, (r, g, b))

        # Pendulum length indicator (small bar)
        bar_x = 52
        bar_y = 3
        bar_h = 8
        t = (self.pend_length - self.PEND_LENGTH_MIN) / (self.PEND_LENGTH_MAX - self.PEND_LENGTH_MIN)
        fill_h = max(1, int(round(t * bar_h)))
        # Outline
        d.draw_rect(bar_x, bar_y, 3, bar_h, (30, 30, 35))
        # Fill from bottom
        d.draw_rect(bar_x, bar_y + bar_h - fill_h, 3, fill_h, HUD_DIM)
