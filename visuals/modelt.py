"""
Ford Model T Engine
===================
Single-cylinder side-view cutaway of the engine that put the world on wheels.
Crankshaft rotates continuously, connecting rod drives piston up and down
inside the cylinder. Flywheel visible with spoked rendering. Full 4-stroke
cycle with intake/exhaust valves and combustion flash.

Controls:
  Left/Right - Adjust RPM (6 speed levels)
"""

import math
from . import Visual, Display, Colors, GRID_SIZE


# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------
STEEL = (180, 180, 190)
STEEL_DARK = (110, 110, 120)
IRON = (80, 80, 90)
BRASS = (200, 170, 50)
PISTON_COLOR = (200, 200, 210)
PISTON_HIGHLIGHT = (230, 230, 240)
CYLINDER_WALL = (100, 100, 110)
CYLINDER_HEAD = (120, 120, 130)
CRANK_PIN = (255, 220, 80)
HUB_COLOR = (220, 220, 230)
HOUSING_COLOR = (50, 50, 55)
FLASH_COLOR = (255, 255, 200)
HUD_COLOR = (160, 160, 170)

# Phase colors
INTAKE_COLOR = (80, 180, 255)
COMPRESS_COLOR = (255, 200, 80)
POWER_COLOR = (255, 80, 40)
EXHAUST_COLOR = (160, 160, 170)

PHASE_NAMES = ["INTK", "COMP", "POWR", "EXHT"]
PHASE_COLORS = [INTAKE_COLOR, COMPRESS_COLOR, POWER_COLOR, EXHAUST_COLOR]

# Valve colors
VALVE_OPEN = [(80, 180, 255), (160, 160, 170)]   # intake open, exhaust open
VALVE_CLOSED = (50, 50, 60)

# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------
FLY_CX = 32          # Flywheel center x
FLY_CY = 48          # Flywheel center y
FLY_R = 10           # Flywheel outer radius
CRANK_R = 7          # Crank radius (distance from shaft center to crank pin)
CON_ROD_L = 17       # Connecting rod length
CYL_CX = 32          # Cylinder centerline x
CYL_HALF_W = 7       # Half-width of cylinder bore
CYL_TOP = 8          # Top of cylinder (head)
CYL_BOT = 34         # Bottom of cylinder bore
PISTON_W = 12        # Piston width
PISTON_H = 5         # Piston height
NUM_SPOKES = 5       # Flywheel spokes

# Speed levels: RPM (idle ~200, cruise ~800-1000)
SPEED_RPMS = [60, 200, 400, 600, 800, 1000]


class ModelT(Visual):
    name = "MODEL T"
    description = "Ford engine cutaway"
    category = "mechanics"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.theta = 0.0           # Crank angle in radians
        self.speed_level = 3       # 1-6
        self.rpm = SPEED_RPMS[self.speed_level - 1]
        self.stroke_phase = 0      # 0=intake 1=compress 2=power 3=exhaust
        self.last_half_id = 0
        self.flash_timer = 0.0     # Combustion flash decay timer

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
        omega = (self.rpm / 60.0) * 2.0 * math.pi
        self.theta += omega * dt

        # 4-stroke state machine: advance phase every half revolution
        half_id = int(self.theta / math.pi)
        if half_id != self.last_half_id:
            self.stroke_phase = (self.stroke_phase + 1) % 4
            # Fire spark at TDC during power stroke
            if half_id % 2 == 0 and self.stroke_phase == 2:
                self.flash_timer = 0.12
            self.last_half_id = half_id

        # Decay flash timer
        if self.flash_timer > 0.0:
            self.flash_timer = max(0.0, self.flash_timer - dt)

    def draw(self):
        d = self.display
        d.clear(Colors.BLACK)

        # --- Compute crank-slider positions ---
        sin_t = math.sin(self.theta)
        cos_t = math.cos(self.theta)

        # Crank pin position (flywheel rotates, pin offset from center)
        cpx = FLY_CX + CRANK_R * sin_t
        cpy = FLY_CY - CRANK_R * cos_t

        # Wrist pin position (constrained to cylinder centerline)
        dx = cpx - CYL_CX
        disc = CON_ROD_L * CON_ROD_L - dx * dx
        wrist_y = cpy - math.sqrt(max(0.0, disc))

        # Piston top-left corner
        piston_x = int(round(CYL_CX - PISTON_W / 2))
        piston_y = int(round(wrist_y - PISTON_H / 2))

        # Integer positions for drawing
        cpx_i = int(round(cpx))
        cpy_i = int(round(cpy))
        wrist_x_i = CYL_CX
        wrist_y_i = int(round(wrist_y))

        # --- Draw order: back to front ---

        # 1. Engine block / housing around cylinder
        self._draw_housing(d)

        # 2. Cylinder walls
        self._draw_cylinder(d)

        # 3. Combustion flash (behind piston, in combustion chamber)
        if self.flash_timer > 0.0:
            self._draw_flash(d, piston_y)

        # 4. Flywheel
        self._draw_flywheel(d)

        # 5. Connecting rod
        d.draw_line(cpx_i, cpy_i, wrist_x_i, wrist_y_i, BRASS)

        # 6. Crank pin (bright dot)
        d.set_pixel(cpx_i, cpy_i, CRANK_PIN)

        # 7. Piston
        self._draw_piston(d, piston_x, piston_y)

        # 8. Wrist pin
        d.set_pixel(wrist_x_i, wrist_y_i, CRANK_PIN)

        # 9. Cylinder head and valves
        self._draw_cylinder_head(d)
        self._draw_valves(d)

        # 10. HUD: RPM and phase
        self._draw_hud(d)

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------

    def _draw_housing(self, d):
        """Draw engine block housing around the cylinder for context."""
        # Left housing block
        d.draw_rect(CYL_CX - CYL_HALF_W - 4, CYL_TOP - 2,
                     4, CYL_BOT - CYL_TOP + 4, HOUSING_COLOR)
        # Right housing block
        d.draw_rect(CYL_CX + CYL_HALF_W + 1, CYL_TOP - 2,
                     4, CYL_BOT - CYL_TOP + 4, HOUSING_COLOR)
        # Bottom housing connecting to crankcase
        d.draw_rect(CYL_CX - CYL_HALF_W - 4, CYL_BOT,
                     CYL_HALF_W * 2 + 9, 4, HOUSING_COLOR)

    def _draw_cylinder(self, d):
        """Draw the cylinder bore walls."""
        left_wall_x = CYL_CX - CYL_HALF_W
        right_wall_x = CYL_CX + CYL_HALF_W
        # Left wall
        d.draw_line(left_wall_x, CYL_TOP, left_wall_x, CYL_BOT, CYLINDER_WALL)
        d.draw_line(left_wall_x - 1, CYL_TOP, left_wall_x - 1, CYL_BOT, IRON)
        # Right wall
        d.draw_line(right_wall_x, CYL_TOP, right_wall_x, CYL_BOT, CYLINDER_WALL)
        d.draw_line(right_wall_x + 1, CYL_TOP, right_wall_x + 1, CYL_BOT, IRON)

    def _draw_flash(self, d, piston_top_y):
        """Draw combustion flash in the combustion chamber above piston."""
        intensity = self.flash_timer / 0.12  # 1.0 -> 0.0
        r = int(255 * intensity)
        g = int(255 * intensity)
        b = int(200 * intensity)
        flash = (r, g, b)
        # Fill combustion chamber area
        left = CYL_CX - CYL_HALF_W + 1
        right = CYL_CX + CYL_HALF_W - 1
        top = CYL_TOP + 1
        bot = min(piston_top_y - 1, CYL_TOP + 8)
        if bot > top:
            w = right - left + 1
            h = bot - top + 1
            d.draw_rect(left, top, w, h, flash)

    def _draw_flywheel(self, d):
        """Draw spoked flywheel with rim."""
        # Outer rim circle
        d.draw_circle(FLY_CX, FLY_CY, FLY_R, STEEL, filled=False)
        # Inner darker rim (one pixel inside)
        d.draw_circle(FLY_CX, FLY_CY, FLY_R - 1, STEEL_DARK, filled=False)

        # Spokes
        for i in range(NUM_SPOKES):
            spoke_angle = self.theta + i * 2.0 * math.pi / NUM_SPOKES
            sx = int(round(FLY_CX + (FLY_R - 2) * math.sin(spoke_angle)))
            sy = int(round(FLY_CY - (FLY_R - 2) * math.cos(spoke_angle)))
            d.draw_line(FLY_CX, FLY_CY, sx, sy, STEEL_DARK)

        # Hub (center dot cluster)
        d.set_pixel(FLY_CX, FLY_CY, HUB_COLOR)
        d.set_pixel(FLY_CX - 1, FLY_CY, STEEL)
        d.set_pixel(FLY_CX + 1, FLY_CY, STEEL)
        d.set_pixel(FLY_CX, FLY_CY - 1, STEEL)
        d.set_pixel(FLY_CX, FLY_CY + 1, STEEL)

    def _draw_piston(self, d, px, py):
        """Draw the piston body with highlighted top edge."""
        d.draw_rect(px, py, PISTON_W, PISTON_H, PISTON_COLOR)
        # Highlighted top edge
        d.draw_line(px, py, px + PISTON_W - 1, py, PISTON_HIGHLIGHT)
        # Ring grooves (two thin dark lines near top)
        d.draw_line(px + 1, py + 1, px + PISTON_W - 2, py + 1, STEEL_DARK)

    def _draw_cylinder_head(self, d):
        """Draw the cylinder head cap at the top of the bore."""
        left = CYL_CX - CYL_HALF_W - 1
        right = CYL_CX + CYL_HALF_W + 1
        # Head plate (2 pixels thick)
        d.draw_line(left, CYL_TOP, right, CYL_TOP, CYLINDER_HEAD)
        d.draw_line(left, CYL_TOP - 1, right, CYL_TOP - 1, IRON)

    def _draw_valves(self, d):
        """Draw intake and exhaust valve indicators at the cylinder head."""
        # Valve positions: left = intake, right = exhaust
        intake_x = CYL_CX - CYL_HALF_W + 2
        exhaust_x = CYL_CX + CYL_HALF_W - 3
        valve_y = CYL_TOP - 3  # Above cylinder head

        # Determine open/closed state from stroke phase
        # Phase 0=INTAKE (intake open), 1=COMPRESS (both closed),
        # 2=POWER (both closed), 3=EXHAUST (exhaust open)
        intake_open = (self.stroke_phase == 0)
        exhaust_open = (self.stroke_phase == 3)

        # Intake valve (left side)
        if intake_open:
            color_i = INTAKE_COLOR
            # Draw valve stem open (lowered into chamber)
            d.draw_rect(intake_x, valve_y, 3, 2, color_i)
            d.set_pixel(intake_x + 1, valve_y + 2, color_i)
        else:
            d.draw_rect(intake_x, valve_y, 3, 2, VALVE_CLOSED)

        # Exhaust valve (right side)
        if exhaust_open:
            color_e = EXHAUST_COLOR
            d.draw_rect(exhaust_x, valve_y, 3, 2, color_e)
            d.set_pixel(exhaust_x + 1, valve_y + 2, color_e)
        else:
            d.draw_rect(exhaust_x, valve_y, 3, 2, VALVE_CLOSED)

        # Labels above valves (single character)
        d.draw_text_small(intake_x, valve_y - 5, "I", INTAKE_COLOR)
        d.draw_text_small(exhaust_x, valve_y - 5, "E", EXHAUST_COLOR)

    def _draw_hud(self, d):
        """Draw RPM display and phase indicator."""
        # RPM at top-left
        d.draw_text_small(2, 1, f"{self.rpm}RPM", HUD_COLOR)

        # Phase indicator at top-right area
        phase_name = PHASE_NAMES[self.stroke_phase]
        phase_color = PHASE_COLORS[self.stroke_phase]
        d.draw_text_small(44, 1, phase_name, phase_color)

        # Phase dots at bottom: 4 dots showing which stroke is active
        dot_y = 62
        dot_start_x = 24
        dot_spacing = 5
        for i in range(4):
            dx = dot_start_x + i * dot_spacing
            if i == self.stroke_phase:
                # Active phase: bright filled dot
                d.set_pixel(dx, dot_y, PHASE_COLORS[i])
                d.set_pixel(dx + 1, dot_y, PHASE_COLORS[i])
                d.set_pixel(dx, dot_y - 1, PHASE_COLORS[i])
                d.set_pixel(dx + 1, dot_y - 1, PHASE_COLORS[i])
            else:
                # Inactive: dim single pixel
                dim = (60, 60, 65)
                d.set_pixel(dx, dot_y, dim)
