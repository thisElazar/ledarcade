"""
Steam Locomotive
================
Side view of a steam locomotive with driving wheels connected by coupling
rods, a crank-slider piston mechanism, boiler, smokestack, and cab.
The wheels rotate with proper mechanical linkage math.

Controls:
  Left/Right - Adjust speed (6 levels)
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE


# --- Color Palette (metallic / industrial) ---
WHEEL_RIM = (180, 180, 190)
WHEEL_DARK = (110, 110, 120)
WHEEL_SPOKE = (140, 140, 150)
WHEEL_HUB = (200, 200, 210)

COUPLING_ROD = (200, 170, 50)
CRANK_PIN = (255, 220, 80)

BOILER_BODY = (80, 80, 90)
BOILER_HIGHLIGHT = (110, 110, 120)
BOILER_BAND = (130, 100, 50)

CYLINDER_BODY = (90, 90, 100)
CYLINDER_HIGHLIGHT = (130, 130, 140)
PISTON_ROD = (180, 180, 190)
CROSSHEAD = (200, 200, 210)
CONNECTING_ROD = (170, 140, 50)

SMOKESTACK_COLOR = (50, 50, 55)
SMOKESTACK_TOP = (70, 70, 75)

CAB_BODY = (200, 120, 60)
CAB_DARK = (150, 85, 40)
CAB_WINDOW = (40, 50, 70)
CAB_ROOF = (60, 60, 65)

GROUND_COLOR = (60, 40, 20)
RAIL_COLOR = (150, 150, 160)
TIE_COLOR = (80, 55, 30)

STEAM_BRIGHT = (220, 220, 230)
STEAM_MED = (160, 160, 170)
STEAM_DIM = (100, 100, 110)

HUD_COLOR = (160, 160, 170)

# --- Layout Constants ---
GROUND_Y = 58
RAIL_Y = 57

WHEEL_RADIUS = 8
WHEEL_CY = 50

# Three driving wheels, evenly spaced
WHEEL_1_CX = 18
WHEEL_2_CX = 36
WHEEL_3_CX = 54
WHEEL_CXS = [WHEEL_1_CX, WHEEL_2_CX, WHEEL_3_CX]

CRANK_RADIUS = 5

# Connecting rod length from front wheel crank pin to crosshead
CONROD_LENGTH = 20

# Cylinder position (horizontal, on left side)
CYLINDER_LEFT = 1
CYLINDER_RIGHT = 14
CYLINDER_TOP = 41
CYLINDER_BOT = 47
CYLINDER_CY = (CYLINDER_TOP + CYLINDER_BOT) // 2

# Boiler geometry
BOILER_TOP = 22
BOILER_BOT = 42
BOILER_LEFT = 4
BOILER_RIGHT = 46

# Smokestack
STACK_LEFT = 6
STACK_RIGHT = 11
STACK_BOT = BOILER_TOP
STACK_TOP = 10
STACK_CAP_LEFT = 4
STACK_CAP_RIGHT = 13

# Cab (right end)
CAB_LEFT = 46
CAB_RIGHT = 62
CAB_TOP = 16
CAB_BOT = BOILER_BOT
CAB_WINDOW_LEFT = 49
CAB_WINDOW_RIGHT = 58
CAB_WINDOW_TOP = 19
CAB_WINDOW_BOT = 27
CAB_ROOF_Y = 14


class SteamPuff:
    """A single particle of steam rising from the smokestack."""

    def __init__(self, x, y):
        self.x = x + random.uniform(-1.5, 1.5)
        self.y = float(y)
        self.vx = random.uniform(-0.3, 0.8)
        self.vy = random.uniform(-8.0, -4.0)
        self.life = 1.0
        self.decay = random.uniform(0.6, 1.2)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy *= 0.97
        self.life -= self.decay * dt

    def alive(self):
        return self.life > 0.0

    def draw(self, d):
        px = int(round(self.x))
        py = int(round(self.y))
        if self.life > 0.66:
            color = STEAM_BRIGHT
        elif self.life > 0.33:
            color = STEAM_MED
        else:
            color = STEAM_DIM
        d.set_pixel(px, py, color)


# Speed levels: driving wheel RPM (yard ~30, express ~200)
SPEED_RPMS = [15, 40, 80, 120, 160, 200]


class Locomotive(Visual):
    name = "LOCOMOTIVE"
    description = "Steam locomotive"
    category = "mechanics"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.theta = 0.0
        self.speed_level = 3
        self.tie_offset = 0.0
        self.steam_puffs = []
        self.steam_timer = 0.0

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

        rpm = SPEED_RPMS[self.speed_level - 1]
        omega = rpm * 2.0 * math.pi / 60.0
        self.theta += omega * dt

        # Scrolling ties
        wheel_circumference = 2.0 * math.pi * WHEEL_RADIUS
        linear_speed = omega * WHEEL_RADIUS
        self.tie_offset += linear_speed * dt

        # Steam puffs
        puff_interval = max(0.02, 0.25 - self.speed_level * 0.035)
        self.steam_timer += dt
        if self.steam_timer >= puff_interval:
            self.steam_timer -= puff_interval
            sx = (STACK_LEFT + STACK_RIGHT) / 2.0
            sy = float(STACK_TOP - 1)
            self.steam_puffs.append(SteamPuff(sx, sy))

        for puff in self.steam_puffs:
            puff.update(dt)
        self.steam_puffs = [p for p in self.steam_puffs if p.alive()]
        # Cap puff count for performance
        if len(self.steam_puffs) > 30:
            self.steam_puffs = self.steam_puffs[-30:]

    def draw(self):
        d = self.display
        d.clear(Colors.BLACK)

        self._draw_steam(d)
        self._draw_ground(d)
        self._draw_boiler(d)
        self._draw_smokestack(d)
        self._draw_cab(d)
        self._draw_cylinder(d)
        self._draw_wheels(d)
        self._draw_coupling_rod(d)
        self._draw_piston_linkage(d)
        self._draw_hud(d)

    # --- Ground and Rails ---

    def _draw_ground(self, d):
        # Ground fill
        d.draw_rect(0, GROUND_Y, GRID_SIZE, GRID_SIZE - GROUND_Y, GROUND_COLOR)

        # Rails (two bright lines)
        d.draw_line(0, RAIL_Y, 63, RAIL_Y, RAIL_COLOR)
        d.draw_line(0, RAIL_Y + 1, 63, RAIL_Y + 1, RAIL_COLOR)

        # Scrolling railroad ties
        tie_spacing = 8
        offset = self.tie_offset % tie_spacing
        x = -offset
        while x < GRID_SIZE + tie_spacing:
            tx = int(round(x))
            if 0 <= tx < GRID_SIZE:
                d.set_pixel(tx, GROUND_Y, TIE_COLOR)
                d.set_pixel(tx, GROUND_Y + 1, TIE_COLOR)
                if tx + 1 < GRID_SIZE:
                    d.set_pixel(tx + 1, GROUND_Y, TIE_COLOR)
                    d.set_pixel(tx + 1, GROUND_Y + 1, TIE_COLOR)
            x += tie_spacing

    # --- Boiler ---

    def _draw_boiler(self, d):
        # Main boiler body
        d.draw_rect(BOILER_LEFT, BOILER_TOP, BOILER_RIGHT - BOILER_LEFT,
                     BOILER_BOT - BOILER_TOP, BOILER_BODY)

        # Highlight band along top
        d.draw_line(BOILER_LEFT, BOILER_TOP, BOILER_RIGHT - 1, BOILER_TOP, BOILER_HIGHLIGHT)
        d.draw_line(BOILER_LEFT, BOILER_TOP + 1, BOILER_RIGHT - 1, BOILER_TOP + 1, BOILER_HIGHLIGHT)

        # Decorative boiler bands (brass rings)
        band_positions = [BOILER_LEFT + 6, BOILER_LEFT + 18, BOILER_LEFT + 30]
        for bx in band_positions:
            if bx < BOILER_RIGHT:
                d.draw_line(bx, BOILER_TOP + 2, bx, BOILER_BOT - 1, BOILER_BAND)

        # Rounded front of boiler (semicircle approximation)
        front_cx = BOILER_LEFT
        for dy in range(-9, 10):
            y = (BOILER_TOP + BOILER_BOT) // 2 + dy
            half_h = (BOILER_BOT - BOILER_TOP) // 2
            if abs(dy) <= half_h:
                frac = 1.0 - (dy * dy) / (half_h * half_h + 0.01)
                indent = int(round(2 * (1.0 - math.sqrt(max(0, frac)))))
                x = BOILER_LEFT - 2 + indent
                if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                    d.set_pixel(x, y, BOILER_HIGHLIGHT)

    # --- Smokestack ---

    def _draw_smokestack(self, d):
        # Main shaft
        d.draw_rect(STACK_LEFT, STACK_TOP, STACK_RIGHT - STACK_LEFT,
                     STACK_BOT - STACK_TOP, SMOKESTACK_COLOR)

        # Flared cap at top
        d.draw_line(STACK_CAP_LEFT, STACK_TOP, STACK_CAP_RIGHT, STACK_TOP, SMOKESTACK_TOP)
        d.draw_line(STACK_CAP_LEFT, STACK_TOP - 1, STACK_CAP_RIGHT, STACK_TOP - 1, SMOKESTACK_TOP)
        d.draw_line(STACK_CAP_LEFT + 1, STACK_TOP - 2, STACK_CAP_RIGHT - 1, STACK_TOP - 2, SMOKESTACK_COLOR)

    # --- Cab ---

    def _draw_cab(self, d):
        # Cab body
        d.draw_rect(CAB_LEFT, CAB_TOP, CAB_RIGHT - CAB_LEFT,
                     CAB_BOT - CAB_TOP, CAB_BODY)

        # Darker edge on left
        d.draw_line(CAB_LEFT, CAB_TOP, CAB_LEFT, CAB_BOT - 1, CAB_DARK)

        # Roof overhang
        d.draw_rect(CAB_LEFT - 1, CAB_ROOF_Y, CAB_RIGHT - CAB_LEFT + 2, 2, CAB_ROOF)

        # Window
        d.draw_rect(CAB_WINDOW_LEFT, CAB_WINDOW_TOP,
                     CAB_WINDOW_RIGHT - CAB_WINDOW_LEFT,
                     CAB_WINDOW_BOT - CAB_WINDOW_TOP, CAB_WINDOW)

        # Window frame highlight
        d.draw_line(CAB_WINDOW_LEFT, CAB_WINDOW_TOP,
                     CAB_WINDOW_RIGHT - 1, CAB_WINDOW_TOP, CAB_DARK)
        d.draw_line(CAB_WINDOW_LEFT, CAB_WINDOW_TOP,
                     CAB_WINDOW_LEFT, CAB_WINDOW_BOT - 1, CAB_DARK)

    # --- Cylinder and Piston ---

    def _draw_cylinder(self, d):
        # Cylinder housing
        d.draw_rect(CYLINDER_LEFT, CYLINDER_TOP, CYLINDER_RIGHT - CYLINDER_LEFT,
                     CYLINDER_BOT - CYLINDER_TOP, CYLINDER_BODY)

        # Highlight on top edge
        d.draw_line(CYLINDER_LEFT, CYLINDER_TOP,
                     CYLINDER_RIGHT - 1, CYLINDER_TOP, CYLINDER_HIGHLIGHT)

    def _get_crank_pin_pos(self, wheel_cx):
        """Get the position of the crank pin on a wheel at current theta."""
        px = wheel_cx + CRANK_RADIUS * math.cos(self.theta)
        py = WHEEL_CY + CRANK_RADIUS * math.sin(self.theta)
        return px, py

    def _get_crosshead_x(self):
        """Compute crosshead x position using crank-slider kinematics.

        displacement = r*cos(theta) + sqrt(L^2 - r^2*sin^2(theta))
        The crosshead slides horizontally at the cylinder centerline.
        """
        r = CRANK_RADIUS
        L = CONROD_LENGTH
        sin_t = math.sin(self.theta)
        cos_t = math.cos(self.theta)
        under_sqrt = L * L - r * r * sin_t * sin_t
        if under_sqrt < 0:
            under_sqrt = 0.0
        displacement = r * cos_t + math.sqrt(under_sqrt)
        # Crosshead x relative to front wheel center
        crosshead_x = WHEEL_1_CX - displacement
        return crosshead_x

    def _draw_piston_linkage(self, d):
        """Draw connecting rod from front wheel crank pin to crosshead,
        and piston rod extending into cylinder."""
        # Front wheel crank pin
        pin_x, pin_y = self._get_crank_pin_pos(WHEEL_1_CX)
        ipx = int(round(pin_x))
        ipy = int(round(pin_y))

        # Crosshead position
        crosshead_x = self._get_crosshead_x()
        cx_x = int(round(crosshead_x))
        cx_y = CYLINDER_CY

        # Connecting rod (crank pin to crosshead)
        d.draw_line(ipx, ipy, cx_x, cx_y, CONNECTING_ROD)
        # Thicken: draw offset lines
        d.draw_line(ipx, ipy - 1, cx_x, cx_y - 1, CONNECTING_ROD)

        # Crosshead block
        d.draw_rect(cx_x - 1, cx_y - 2, 3, 4, CROSSHEAD)

        # Piston rod: from crosshead leftward into cylinder
        rod_end_x = CYLINDER_LEFT + 2
        d.draw_line(rod_end_x, cx_y, cx_x - 1, cx_y, PISTON_ROD)
        d.draw_line(rod_end_x, cx_y - 1, cx_x - 1, cx_y - 1, PISTON_ROD)

        # Piston head inside cylinder
        d.draw_line(rod_end_x, CYLINDER_TOP + 1, rod_end_x, CYLINDER_BOT - 1, WHEEL_RIM)
        d.draw_line(rod_end_x - 1, CYLINDER_TOP + 1, rod_end_x - 1, CYLINDER_BOT - 1, WHEEL_DARK)

    # --- Wheels ---

    def _draw_wheels(self, d):
        for cx in WHEEL_CXS:
            self._draw_single_wheel(d, cx, WHEEL_CY, WHEEL_RADIUS)

    def _draw_single_wheel(self, d, cx, cy, r):
        """Draw a spoked wheel with rim and rotating spokes using pixel-level rendering."""
        # Outer rim using midpoint circle pixels
        self._draw_circle_pixels(d, cx, cy, r, WHEEL_RIM)
        self._draw_circle_pixels(d, cx, cy, r - 1, WHEEL_DARK)

        # Inner rim
        if r >= 4:
            self._draw_circle_pixels(d, cx, cy, r - 2, WHEEL_DARK)

        # Rotating spokes (4 spokes = cross pattern)
        num_spokes = 4
        spoke_inner = 2
        spoke_outer = r - 2
        for s in range(num_spokes):
            angle = self.theta + s * math.pi / num_spokes
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

        # Crank pin dot on this wheel
        pin_x, pin_y = self._get_crank_pin_pos(cx)
        ipx = int(round(pin_x))
        ipy = int(round(pin_y))
        d.set_pixel(ipx, ipy, CRANK_PIN)
        d.set_pixel(ipx + 1, ipy, CRANK_PIN)
        d.set_pixel(ipx, ipy + 1, CRANK_PIN)
        d.set_pixel(ipx + 1, ipy + 1, CRANK_PIN)

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

    # --- Coupling Rod ---

    def _draw_coupling_rod(self, d):
        """Draw the coupling rod connecting all crank pins.
        Since all wheels are keyed at the same phase, their crank pins
        all sit at the same angular position (self.theta). The coupling
        rod is a rigid bar linking them.
        """
        pin_positions = []
        for cx in WHEEL_CXS:
            px, py = self._get_crank_pin_pos(cx)
            pin_positions.append((int(round(px)), int(round(py))))

        # Draw thick line segments between consecutive pins
        for i in range(len(pin_positions) - 1):
            x0, y0 = pin_positions[i]
            x1, y1 = pin_positions[i + 1]
            d.draw_line(x0, y0, x1, y1, COUPLING_ROD)
            d.draw_line(x0, y0 - 1, x1, y1 - 1, COUPLING_ROD)
            d.draw_line(x0, y0 + 1, x1, y1 + 1, COUPLING_ROD)

        # Redraw crank pin highlights on top of rod
        for px, py in pin_positions:
            d.set_pixel(px, py, CRANK_PIN)
            d.set_pixel(px + 1, py, CRANK_PIN)
            d.set_pixel(px, py + 1, CRANK_PIN)
            d.set_pixel(px + 1, py + 1, CRANK_PIN)

    # --- Steam Puffs ---

    def _draw_steam(self, d):
        for puff in self.steam_puffs:
            puff.draw(d)

    # --- HUD ---

    def _draw_hud(self, d):
        rpm = SPEED_RPMS[self.speed_level - 1]
        d.draw_text_small(2, 2, f"{rpm} RPM", HUD_COLOR)
