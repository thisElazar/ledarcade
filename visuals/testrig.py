"""
Mechanical Test Rig
===================
A test visual exercising the core primitives needed for all mechanics visuals:
  P1  Crank-slider linkage (connecting rod + piston)
  P4  Triggered event (TDC flash)
  P5  Intermittent indicator (stroke phase)
  P6  Cam profile (valve lift)
  P7  State machine (4-stroke cycle)
  P11 Spring drawing (valve return spring)
  P12 Spoked wheel rendering (flywheel + secondary wheel)
  P13 Coupling rod (rigid link between wheels)

Layout: vertical engine cross-section.
  Left: cylinder + piston above a main flywheel
  Right: cam + valve + spring above a secondary wheel
  Bottom: coupling rod connecting both wheels

Controls:
  Left/Right - Adjust RPM
"""

import math
from . import Visual, Display, Colors, GRID_SIZE


# ── Colors ────────────────────────────────────────────────────────
STEEL = (180, 180, 190)
STEEL_DK = (110, 110, 120)
BRASS = (200, 170, 50)
BRASS_DK = (140, 120, 40)
COPPER = (200, 120, 60)
IRON = (80, 80, 90)
IRON_LT = (100, 100, 110)
HUB = (220, 220, 230)
PIN = (255, 220, 80)
ROD_COLOR = (190, 170, 70)
COUPLING_COLOR = (230, 200, 80)
PISTON_COLOR = (200, 200, 210)
PISTON_HI = (230, 230, 240)
CYLINDER_WALL = (100, 100, 110)
CYLINDER_HEAD = (120, 120, 130)
VALVE_COLOR = (180, 60, 60)
VALVE_SEAT = (120, 40, 40)
SPRING_COLOR = (140, 140, 150)
CAM_BODY = (170, 170, 180)
CAM_EDGE = (130, 130, 140)
CAM_LOBE = (200, 200, 210)
FLASH_COLOR = (255, 255, 200)
PHASE_COLORS = [
    (80, 180, 255),   # intake  - blue
    (255, 200, 80),   # compress - yellow
    (255, 80, 40),    # power   - red
    (160, 160, 170),  # exhaust - gray
]
PHASE_NAMES = ["IN", "CMP", "POW", "EXH"]
LABEL_COLOR = (160, 160, 170)
BASE_COLOR = (50, 50, 55)

# ── Geometry ──────────────────────────────────────────────────────
# Main flywheel
MAIN_CX, MAIN_CY = 18, 46
MAIN_R = 10
CRANK_R = 6
ROD_LEN = 16

# Secondary wheel
SEC_CX, SEC_CY = 46, 46
SEC_R = 7
SEC_CRANK_R = 6  # same as main for horizontal coupling rod

# Cylinder (vertical, above main wheel)
CYL_CX = MAIN_CX
CYL_HALF_W = 6
CYL_TOP = 14       # cylinder head y
CYL_BOT = 35       # cylinder bottom opening

# Cam (on secondary shaft, above second wheel)
CAM_CX, CAM_CY = SEC_CX, 18
CAM_BASE_R = 4
CAM_LOBE_R = 8
CAM_LOBE_WIDTH = 0.4  # fraction of rotation that is lobe

# Valve / follower (above cam)
FOLLOWER_X = CAM_CX
FOLLOWER_W = 4
GUIDE_TOP = 4       # top of spring / guide rail


# ── Primitives ────────────────────────────────────────────────────

def crank_slider(theta, r, L):
    """P1: Crank-slider — returns piston displacement from crank center.

    Given crank angle theta, crank radius r, connecting rod length L,
    returns how far the wrist pin is from the crank center along the
    slider axis.  Accounts for connecting-rod geometry (non-sinusoidal).
    """
    sin_t = math.sin(theta)
    cos_t = math.cos(theta)
    return r * cos_t + math.sqrt(L * L - r * r * sin_t * sin_t)


def cam_radius(angle, base_r, lobe_r, lobe_w):
    """P6: Cam profile — raised cosine lobe.

    Returns the cam surface radius at the given angle.
    Lobe is centered at angle=0.
    """
    a = angle % (2 * math.pi)
    if a > math.pi:
        a -= 2 * math.pi
    half_lobe = lobe_w * math.pi
    if abs(a) < half_lobe:
        t = 0.5 * (1 + math.cos(math.pi * a / half_lobe))
        return base_r + (lobe_r - base_r) * t
    return base_r


# Speed levels: RPM
SPEED_RPMS = [30, 60, 120, 200, 300, 400]


class TestRig(Visual):
    name = "TEST RIG"
    description = "Mechanical primitives"
    category = "mechanics"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.theta = 0.0           # master crank angle
        self.speed_level = 3       # 1-6
        self.rpm = SPEED_RPMS[self.speed_level - 1]

        # Triggered event: TDC flash
        self.flash_timer = 0.0

        # State machine: 4-stroke cycle (2 full rotations per cycle)
        # Phase 0: intake, 1: compression, 2: power, 3: exhaust
        self.stroke_phase = 0
        # Track which half-revolution we're in for phase detection
        self.last_half_id = 0

    def handle_input(self, input_state):
        consumed = False
        if input_state.right_pressed:
            self.speed_level = min(6, self.speed_level + 1)
            self.rpm = SPEED_RPMS[self.speed_level - 1]
            consumed = True
        elif input_state.left_pressed:
            self.speed_level = max(1, self.speed_level - 1)
            self.rpm = SPEED_RPMS[self.speed_level - 1]
            consumed = True
        return consumed

    def update(self, dt):
        self.time += dt
        omega = (self.rpm / 60.0) * 2 * math.pi
        self.theta += omega * dt

        # P7: 4-stroke state machine — advance phase at each TDC and BDC
        # Phase changes every half-revolution (pi radians)
        half_id = int(self.theta / math.pi)
        if half_id != self.last_half_id:
            self.stroke_phase = (self.stroke_phase + 1) % 4
            # P4: Flash at TDC only (even half_id = TDC)
            if half_id % 2 == 0:
                self.flash_timer = 0.12
            self.last_half_id = half_id

        if self.flash_timer > 0:
            self.flash_timer = max(0.0, self.flash_timer - dt)

    def draw(self):
        d = self.display
        d.clear(Colors.BLACK)

        # Ground / base
        for x in range(GRID_SIZE):
            d.set_pixel(x, 58, BASE_COLOR)
            d.set_pixel(x, 59, BASE_COLOR)

        # ── Draw wheels ──────────────────────────────────────
        self._draw_wheel(d, MAIN_CX, MAIN_CY, MAIN_R)
        self._draw_wheel(d, SEC_CX, SEC_CY, SEC_R)

        # ── Coupling rod (P13) ───────────────────────────────
        cp1x, cp1y = self._crank_pin(MAIN_CX, MAIN_CY, CRANK_R)
        cp2x, cp2y = self._crank_pin(SEC_CX, SEC_CY, SEC_CRANK_R)
        ic1x, ic1y = int(round(cp1x)), int(round(cp1y))
        ic2x, ic2y = int(round(cp2x)), int(round(cp2y))
        # Draw 3px thick coupling rod
        d.draw_line(ic1x, ic1y, ic2x, ic2y, COUPLING_COLOR)
        d.draw_line(ic1x, ic1y - 1, ic2x, ic2y - 1, COUPLING_COLOR)
        d.draw_line(ic1x, ic1y + 1, ic2x, ic2y + 1, COUPLING_COLOR)

        # ── Crank pins ───────────────────────────────────────
        for px, py in [(ic1x, ic1y), (ic2x, ic2y)]:
            d.set_pixel(px, py, PIN)
            for dx2, dy2 in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                d.set_pixel(px + dx2, py + dy2, PIN)

        # ── Cylinder walls ───────────────────────────────────
        for y in range(CYL_TOP, CYL_BOT + 1):
            d.set_pixel(CYL_CX - CYL_HALF_W, y, CYLINDER_WALL)
            d.set_pixel(CYL_CX + CYL_HALF_W, y, CYLINDER_WALL)
        # Cylinder head
        for x in range(CYL_CX - CYL_HALF_W, CYL_CX + CYL_HALF_W + 1):
            d.set_pixel(x, CYL_TOP, CYLINDER_HEAD)
            d.set_pixel(x, CYL_TOP - 1, CYLINDER_HEAD)

        # ── Piston + connecting rod (P1) ─────────────────────
        # Crank pin on main wheel
        cpx, cpy = cp1x, cp1y

        # Wrist pin / piston position (piston constrained to x=CYL_CX, vertical)
        # Piston is ABOVE the crank, so wrist_pin_y = cpy - sqrt(L^2 - dx^2)
        dx = cpx - CYL_CX
        disc = ROD_LEN * ROD_LEN - dx * dx
        if disc < 0:
            disc = 0
        wrist_y = cpy - math.sqrt(disc)
        iwrist_y = int(round(wrist_y))

        # Connecting rod: line from crank pin to wrist pin
        d.draw_line(int(round(cpx)), int(round(cpy)),
                    CYL_CX, iwrist_y, ROD_COLOR)

        # Piston body
        pw = CYL_HALF_W * 2 - 2
        ph = 5
        px0 = CYL_CX - pw // 2
        py0 = iwrist_y - ph // 2
        d.draw_rect(px0, py0, pw, ph, PISTON_COLOR)
        # Highlight top edge
        for x in range(px0, px0 + pw):
            d.set_pixel(x, py0, PISTON_HI)

        # Wrist pin dot
        d.set_pixel(CYL_CX, iwrist_y, HUB)

        # ── Cam + follower + spring (P6, P11) ────────────────
        # Cam rotates at crank speed (simplified; real = half speed)
        cam_angle = self.theta
        self._draw_cam(d, cam_angle)

        # Follower lift from cam
        # Follower rides on top of cam (cam lobe points UP, follower pushed up)
        lift_angle = -math.pi / 2 - cam_angle  # top of cam
        r_at_top = cam_radius(lift_angle, CAM_BASE_R, CAM_LOBE_R, CAM_LOBE_WIDTH)
        lift = (r_at_top - CAM_BASE_R) / (CAM_LOBE_R - CAM_BASE_R)

        # Follower position
        follower_travel = CAM_CY - CAM_LOBE_R - GUIDE_TOP - 4
        follower_y = int(CAM_CY - CAM_LOBE_R - lift * follower_travel)

        # Follower body
        fx = FOLLOWER_X - FOLLOWER_W // 2
        d.draw_rect(fx, follower_y, FOLLOWER_W, 3, VALVE_COLOR)
        d.draw_line(fx, follower_y, fx + FOLLOWER_W - 1, follower_y, (220, 80, 80))

        # Valve stem below cam
        valve_top = CAM_CY + CAM_LOBE_R + 1
        valve_bot = min(GRID_SIZE - 1, valve_top + 4 + int(lift * 3))
        d.draw_line(FOLLOWER_X, valve_top, FOLLOWER_X, valve_bot, VALVE_SEAT)
        d.draw_line(FOLLOWER_X - 1, valve_bot, FOLLOWER_X + 1, valve_bot, VALVE_SEAT)

        # P11: Spring between follower top and guide
        spring_bot = follower_y
        spring_top = GUIDE_TOP
        if spring_bot - spring_top > 3:
            teeth = 3
            seg_h = (spring_bot - spring_top) / (teeth * 2)
            for t in range(teeth * 2):
                y0 = int(spring_top + t * seg_h)
                y1 = int(spring_top + (t + 1) * seg_h)
                if t % 2 == 0:
                    d.draw_line(FOLLOWER_X - 2, y0, FOLLOWER_X + 2, y1, SPRING_COLOR)
                else:
                    d.draw_line(FOLLOWER_X + 2, y0, FOLLOWER_X - 2, y1, SPRING_COLOR)

        # ── TDC Flash (P4) ───────────────────────────────────
        if self.flash_timer > 0:
            brightness = self.flash_timer / 0.12
            r_c = int(FLASH_COLOR[0] * brightness)
            g_c = int(FLASH_COLOR[1] * brightness)
            b_c = int(FLASH_COLOR[2] * brightness)
            flash = (r_c, g_c, b_c)
            # Flash at piston top
            for dx2 in range(-2, 3):
                for dy2 in range(-1, 2):
                    px2 = CYL_CX + dx2
                    py2 = py0 - 2 + dy2
                    if 0 <= px2 < GRID_SIZE and 0 <= py2 < GRID_SIZE:
                        d.set_pixel(px2, py2, flash)

        # ── Shaft line connecting wheels ─────────────────────
        # Visual: horizontal shaft at wheel center y
        d.draw_line(MAIN_CX + MAIN_R + 1, MAIN_CY,
                    SEC_CX - SEC_R - 1, SEC_CY, IRON)

        # Vertical shaft from main wheel up to cylinder
        d.draw_line(MAIN_CX, CYL_BOT + 1, MAIN_CX, MAIN_CY - MAIN_R - 1, IRON_LT)

        # ── HUD ──────────────────────────────────────────────
        d.draw_text_small(2, 2, f"{self.rpm} RPM", LABEL_COLOR)

        # Stroke phase indicator (P7)
        phase = self.stroke_phase
        phase_color = PHASE_COLORS[phase]
        phase_name = PHASE_NAMES[phase]
        d.draw_text_small(2, 9, phase_name, phase_color)

        # Phase dots (4 dots, current one bright)
        for i in range(4):
            dot_x = 2 + i * 4
            dot_y = 60
            if i == phase:
                d.set_pixel(dot_x, dot_y, PHASE_COLORS[i])
                d.set_pixel(dot_x + 1, dot_y, PHASE_COLORS[i])
                d.set_pixel(dot_x, dot_y + 1, PHASE_COLORS[i])
                d.set_pixel(dot_x + 1, dot_y + 1, PHASE_COLORS[i])
            else:
                c = PHASE_COLORS[i]
                dim = (c[0] // 4, c[1] // 4, c[2] // 4)
                d.set_pixel(dot_x, dot_y, dim)

    # ── Helpers ───────────────────────────────────────────────

    def _crank_pin(self, cx, cy, r):
        """Position of a crank pin at angle theta on a wheel."""
        return (cx + r * math.sin(self.theta),
                cy - r * math.cos(self.theta))

    def _draw_wheel(self, d, cx, cy, r):
        """P12: Spoked wheel with rotating spokes."""
        # Rim (two concentric circles for thickness)
        self._circle_outline(d, cx, cy, r, STEEL_DK)
        self._circle_outline(d, cx, cy, r - 1, STEEL)

        # 4 spokes
        for s in range(4):
            spoke_a = self.theta + s * math.pi / 2
            for t in range(2, r - 1):
                sx = int(round(cx + t * math.sin(spoke_a)))
                sy = int(round(cy - t * math.cos(spoke_a)))
                if 0 <= sx < GRID_SIZE and 0 <= sy < GRID_SIZE:
                    d.set_pixel(sx, sy, IRON_LT)

        # Hub (5-pixel cross)
        d.set_pixel(cx, cy, HUB)
        for dx2, dy2 in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            d.set_pixel(cx + dx2, cy + dy2, IRON)

    def _draw_cam(self, d, angle):
        """P6: Rotating cam lobe with pixel-level rendering."""
        cx, cy = CAM_CX, CAM_CY
        margin = CAM_LOBE_R + 2
        for py in range(max(0, cy - margin), min(GRID_SIZE, cy + margin + 1)):
            for px in range(max(0, cx - margin), min(GRID_SIZE, cx + margin + 1)):
                dx = px - cx
                dy = py - cy
                dist_sq = dx * dx + dy * dy
                if dist_sq > (CAM_LOBE_R + 1) ** 2:
                    continue
                dist = math.sqrt(dist_sq)
                pixel_angle = math.atan2(dy, dx) - angle
                r_at = cam_radius(pixel_angle, CAM_BASE_R, CAM_LOBE_R, CAM_LOBE_WIDTH)
                if dist <= r_at:
                    if dist > r_at - 1.2:
                        d.set_pixel(px, py, CAM_EDGE)
                    else:
                        d.set_pixel(px, py, CAM_BODY)

        # Cam center dot
        d.set_pixel(cx, cy, HUB)

    def _circle_outline(self, d, cx, cy, r, color):
        """Midpoint circle algorithm for pixel-perfect outlines."""
        x, y, err = r, 0, 1 - r
        while x >= y:
            for dx2, dy2 in [(x, y), (y, x), (-y, x), (-x, y),
                             (-x, -y), (-y, -x), (y, -x), (x, -y)]:
                px, py = cx + dx2, cy + dy2
                if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                    d.set_pixel(px, py, color)
            y += 1
            if err < 0:
                err += 2 * y + 1
            else:
                x -= 1
                err += 2 * (y - x) + 1
