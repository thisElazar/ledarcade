"""
Watt Beam Engine
================
James Watt's beam engine (1769+) - the stationary steam engine that powered
the Industrial Revolution. Features the iconic rocking beam pivoting at center,
with piston/cylinder on one side and flywheel/crank on the other.

The beam rocks up and down in a slow, powerful rhythm as steam drives the
piston, which rotates the flywheel through a connecting rod and crank.

Controls:
  Left/Right - Adjust engine speed (slower/faster)
"""

import math
from . import Visual, Display, Colors, GRID_SIZE


# ---------------------------------------------------------------------------
# Color palette - Industrial iron and brass
# ---------------------------------------------------------------------------
IRON_DARK = (60, 60, 70)       # Dark iron for structure
IRON = (80, 80, 90)            # Standard iron
STEEL = (150, 150, 160)        # Polished steel surfaces
BRASS = (180, 150, 50)         # Brass fittings and highlights
BRASS_BRIGHT = (220, 190, 80)  # Bright brass pins
PISTON_COLOR = (170, 170, 180)
CYLINDER_WALL = (90, 90, 100)
CYLINDER_INNER = (50, 50, 55)
FLYWHEEL_RIM = (130, 130, 140)
FLYWHEEL_SPOKE = (100, 100, 110)
HUB_COLOR = (200, 200, 210)
BEAM_COLOR = (120, 110, 100)   # Wooden beam core
BEAM_EDGE = (90, 85, 80)       # Beam edge
STEAM_COLOR = (180, 180, 190)
PIVOT_COLOR = (200, 180, 60)
BRICK = (120, 60, 50)          # Brick base/foundation
BRICK_DARK = (90, 45, 35)
HUD_COLOR = (140, 140, 150)

# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------
# Central pivot (the great beam rocks around this point)
PIVOT_X = 32
PIVOT_Y = 22

# Beam dimensions
BEAM_HALF_LEN = 26      # Half-length of the beam
BEAM_THICKNESS = 3      # Beam thickness in pixels

# Cylinder (left side)
CYL_X = 10              # Cylinder center x
CYL_TOP = 28            # Top of cylinder
CYL_BOT = 52            # Bottom of cylinder
CYL_HALF_W = 4          # Half-width of cylinder bore
PISTON_H = 4            # Piston height
PISTON_W = 6            # Piston width

# Piston rod connection to beam
PISTON_ROD_TOP_Y = 24   # Where rod connects to beam end

# Flywheel (right side)
FLY_CX = 54             # Flywheel center x
FLY_CY = 48             # Flywheel center y
FLY_R = 10              # Flywheel radius
CRANK_R = 6             # Crank radius
NUM_SPOKES = 6          # Number of flywheel spokes

# Connecting rod from beam to flywheel crank
CON_ROD_LEN = 22        # Length of connecting rod

# Speed levels (cycles per minute - real beam engines were slow)
SPEED_LEVELS = [4, 8, 12, 16, 20, 24]


class BeamEngine(Visual):
    name = "BEAM ENGINE"
    description = "Watt steam engine"
    category = "mechanics"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.theta = 0.0           # Flywheel angle in radians
        self.speed_level = 2       # 1-6
        self.cpm = SPEED_LEVELS[self.speed_level - 1]  # Cycles per minute
        self.steam_puffs = []      # List of (x, y, age) for steam particles

    def handle_input(self, input_state):
        consumed = False
        if input_state.right_pressed:
            self.speed_level = min(6, self.speed_level + 1)
            self.cpm = SPEED_LEVELS[self.speed_level - 1]
            consumed = True
        elif input_state.left_pressed:
            self.speed_level = max(1, self.speed_level - 1)
            self.cpm = SPEED_LEVELS[self.speed_level - 1]
            consumed = True
        return consumed

    def update(self, dt):
        self.time += dt
        # Convert cycles per minute to radians per second
        omega = (self.cpm / 60.0) * 2.0 * math.pi
        self.theta += omega * dt

        # Update steam puffs
        new_puffs = []
        for px, py, age in self.steam_puffs:
            new_age = age + dt
            if new_age < 1.5:  # Steam lasts 1.5 seconds
                # Drift upward and left
                new_puffs.append((px - dt * 3, py - dt * 8, new_age))
        self.steam_puffs = new_puffs

        # Occasionally emit steam near cylinder top
        if len(self.steam_puffs) < 8 and self.time % 0.3 < dt:
            import random
            px = CYL_X + random.randint(-2, 2)
            py = CYL_TOP - 2 + random.randint(-1, 1)
            self.steam_puffs.append((px, py, 0.0))

    def draw(self):
        d = self.display
        d.clear(Colors.BLACK)

        # --- Compute mechanism positions ---
        sin_t = math.sin(self.theta)
        cos_t = math.cos(self.theta)

        # Flywheel crank pin position
        crank_x = FLY_CX + CRANK_R * sin_t
        crank_y = FLY_CY - CRANK_R * cos_t

        # The beam end on the flywheel side connects to the crank via con rod
        # The beam rocks, so we need to find beam angle from crank position
        # Beam right end (above flywheel) connects to crank via connecting rod

        # For a beam engine, the beam rocks about the pivot.
        # Right end of beam connects via connecting rod to crank.
        # We compute the beam angle from the crank position.

        # Right beam end horizontal position (above the crank)
        beam_right_x = PIVOT_X + BEAM_HALF_LEN - 5  # Slightly inward

        # Find beam angle such that the connecting rod reaches the crank
        # Using geometry: right beam end position determines beam tilt
        # Beam tilts as crank rotates. The vertical motion at beam end
        # follows a sinusoidal pattern linked to flywheel rotation.

        # Simplified: beam end vertical position oscillates with crank
        # The beam angle is determined by the crank's vertical position
        max_beam_tilt = 0.12  # Max tilt in radians (~7 degrees)
        beam_angle = max_beam_tilt * sin_t

        # Beam endpoints
        beam_left_x = PIVOT_X - BEAM_HALF_LEN * math.cos(beam_angle)
        beam_left_y = PIVOT_Y + BEAM_HALF_LEN * math.sin(beam_angle)
        beam_right_x = PIVOT_X + BEAM_HALF_LEN * math.cos(beam_angle)
        beam_right_y = PIVOT_Y - BEAM_HALF_LEN * math.sin(beam_angle)

        # Piston position (connected to left beam end)
        # The piston moves vertically as the beam rocks
        piston_y = beam_left_y + 4  # Offset below beam end

        # Integer positions
        beam_left_xi = int(round(beam_left_x))
        beam_left_yi = int(round(beam_left_y))
        beam_right_xi = int(round(beam_right_x))
        beam_right_yi = int(round(beam_right_y))
        piston_yi = int(round(piston_y))
        crank_xi = int(round(crank_x))
        crank_yi = int(round(crank_y))

        # --- Draw order: back to front ---

        # 1. Background: brick foundation
        self._draw_foundation(d)

        # 2. Steam puffs (behind everything mechanical)
        self._draw_steam(d)

        # 3. Cylinder and piston
        self._draw_cylinder(d, piston_yi)

        # 4. Central pivot column/support
        self._draw_pivot_support(d)

        # 5. Flywheel
        self._draw_flywheel(d)

        # 6. Connecting rod from beam to crank
        d.draw_line(beam_right_xi, beam_right_yi + 1, crank_xi, crank_yi, BRASS)

        # 7. The great beam
        self._draw_beam(d, beam_left_xi, beam_left_yi,
                        beam_right_xi, beam_right_yi)

        # 8. Piston rod (from beam left end down to piston)
        d.draw_line(beam_left_xi, beam_left_yi + 1,
                    CYL_X, piston_yi - PISTON_H // 2, STEEL)

        # 9. Pivot pin (bright brass, on top of beam)
        d.set_pixel(PIVOT_X, PIVOT_Y, PIVOT_COLOR)
        d.set_pixel(PIVOT_X - 1, PIVOT_Y, BRASS)
        d.set_pixel(PIVOT_X + 1, PIVOT_Y, BRASS)

        # 10. Crank pin
        d.set_pixel(crank_xi, crank_yi, BRASS_BRIGHT)

        # 11. HUD
        self._draw_hud(d)

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------

    def _draw_foundation(self, d):
        """Draw brick foundation/base."""
        # Left foundation (under cylinder)
        for y in range(54, 64):
            for x in range(2, 20):
                # Brick pattern
                row = (y - 54) // 3
                offset = 2 if row % 2 else 0
                col = (x + offset) // 4
                if (x + offset) % 4 == 0 or (y - 54) % 3 == 0:
                    d.set_pixel(x, y, BRICK_DARK)
                else:
                    d.set_pixel(x, y, BRICK)

        # Center foundation (under pivot)
        for y in range(50, 64):
            for x in range(26, 38):
                row = (y - 50) // 3
                offset = 2 if row % 2 else 0
                col = (x + offset) // 4
                if (x + offset) % 4 == 0 or (y - 50) % 3 == 0:
                    d.set_pixel(x, y, BRICK_DARK)
                else:
                    d.set_pixel(x, y, BRICK)

        # Right foundation (under flywheel support)
        for y in range(58, 64):
            for x in range(46, 62):
                row = (y - 58) // 3
                offset = 2 if row % 2 else 0
                if (x + offset) % 4 == 0 or (y - 58) % 3 == 0:
                    d.set_pixel(x, y, BRICK_DARK)
                else:
                    d.set_pixel(x, y, BRICK)

    def _draw_steam(self, d):
        """Draw steam puffs."""
        for px, py, age in self.steam_puffs:
            alpha = 1.0 - age / 1.5
            if alpha > 0:
                intensity = int(180 * alpha)
                color = (intensity, intensity, intensity + 10)
                xi, yi = int(px), int(py)
                d.set_pixel(xi, yi, color)
                if age < 0.8:
                    d.set_pixel(xi + 1, yi, color)
                    d.set_pixel(xi, yi - 1, color)

    def _draw_cylinder(self, d, piston_y):
        """Draw the steam cylinder with piston."""
        # Cylinder body (outer walls)
        left_x = CYL_X - CYL_HALF_W - 1
        right_x = CYL_X + CYL_HALF_W + 1

        # Left wall
        d.draw_line(left_x, CYL_TOP, left_x, CYL_BOT, CYLINDER_WALL)
        d.draw_line(left_x - 1, CYL_TOP, left_x - 1, CYL_BOT, IRON_DARK)

        # Right wall
        d.draw_line(right_x, CYL_TOP, right_x, CYL_BOT, CYLINDER_WALL)
        d.draw_line(right_x + 1, CYL_TOP, right_x + 1, CYL_BOT, IRON_DARK)

        # Cylinder cap (top)
        d.draw_line(left_x - 1, CYL_TOP - 1, right_x + 1, CYL_TOP - 1, IRON)
        d.draw_line(left_x, CYL_TOP - 2, right_x, CYL_TOP - 2, IRON_DARK)

        # Cylinder bottom
        d.draw_line(left_x - 1, CYL_BOT + 1, right_x + 1, CYL_BOT + 1, IRON)

        # Cylinder bore interior (dark)
        for y in range(CYL_TOP, CYL_BOT + 1):
            for x in range(CYL_X - CYL_HALF_W, CYL_X + CYL_HALF_W + 1):
                d.set_pixel(x, y, CYLINDER_INNER)

        # Piston
        piston_top = piston_y - PISTON_H // 2
        piston_left = CYL_X - PISTON_W // 2
        d.draw_rect(piston_left, piston_top, PISTON_W, PISTON_H, PISTON_COLOR)
        # Piston ring (bright line at top)
        d.draw_line(piston_left, piston_top,
                    piston_left + PISTON_W - 1, piston_top, STEEL)

        # Steam pipe inlet (left side of cylinder)
        d.draw_line(left_x - 3, CYL_TOP + 4, left_x - 1, CYL_TOP + 4, BRASS)
        d.draw_line(left_x - 3, CYL_TOP + 5, left_x - 1, CYL_TOP + 5, BRASS)

    def _draw_pivot_support(self, d):
        """Draw the central pivot column that supports the beam."""
        # Main column (A-frame style)
        col_left = PIVOT_X - 3
        col_right = PIVOT_X + 3

        # Tapered column
        for y in range(PIVOT_Y + 2, 50):
            # Taper outward as we go down
            taper = (y - PIVOT_Y) // 8
            d.draw_line(col_left - taper, y, col_left - taper + 1, y, IRON)
            d.draw_line(col_right + taper - 1, y, col_right + taper, y, IRON)

        # Cross brace
        d.draw_line(PIVOT_X - 4, 36, PIVOT_X + 4, 36, IRON_DARK)

        # Top plate (pivot bearing housing)
        d.draw_rect(PIVOT_X - 4, PIVOT_Y - 2, 9, 3, IRON)
        d.draw_line(PIVOT_X - 3, PIVOT_Y - 3, PIVOT_X + 3, PIVOT_Y - 3, STEEL)

    def _draw_flywheel(self, d):
        """Draw the flywheel with spokes."""
        # Outer rim
        d.draw_circle(FLY_CX, FLY_CY, FLY_R, FLYWHEEL_RIM, filled=False)
        d.draw_circle(FLY_CX, FLY_CY, FLY_R - 1, IRON_DARK, filled=False)

        # Spokes (rotate with flywheel)
        for i in range(NUM_SPOKES):
            spoke_angle = self.theta + i * 2.0 * math.pi / NUM_SPOKES
            sx = int(round(FLY_CX + (FLY_R - 2) * math.sin(spoke_angle)))
            sy = int(round(FLY_CY - (FLY_R - 2) * math.cos(spoke_angle)))
            d.draw_line(FLY_CX, FLY_CY, sx, sy, FLYWHEEL_SPOKE)

        # Hub
        d.set_pixel(FLY_CX, FLY_CY, HUB_COLOR)
        d.set_pixel(FLY_CX - 1, FLY_CY, STEEL)
        d.set_pixel(FLY_CX + 1, FLY_CY, STEEL)
        d.set_pixel(FLY_CX, FLY_CY - 1, STEEL)
        d.set_pixel(FLY_CX, FLY_CY + 1, STEEL)

        # Flywheel support stand
        d.draw_line(FLY_CX - 2, FLY_CY + FLY_R + 1, FLY_CX - 2, 58, IRON)
        d.draw_line(FLY_CX + 2, FLY_CY + FLY_R + 1, FLY_CX + 2, 58, IRON)
        d.draw_line(FLY_CX - 3, 57, FLY_CX + 3, 57, IRON_DARK)

    def _draw_beam(self, d, left_x, left_y, right_x, right_y):
        """Draw the great rocking beam."""
        # Main beam body (thick line)
        # Draw multiple parallel lines for thickness
        dx = right_x - left_x
        dy = right_y - left_y
        length = math.sqrt(dx * dx + dy * dy)
        if length > 0:
            # Normal vector (perpendicular to beam)
            nx = -dy / length
            ny = dx / length

            # Draw beam as thick line
            for offset in range(-1, 2):
                ox = int(round(offset * nx))
                oy = int(round(offset * ny))
                if offset == 0:
                    color = BEAM_COLOR
                else:
                    color = BEAM_EDGE
                d.draw_line(left_x + ox, left_y + oy,
                            right_x + ox, right_y + oy, color)

        # End caps (arched beam ends, typical of Watt engines)
        # Left end cap
        d.set_pixel(left_x - 1, left_y, IRON)
        d.set_pixel(left_x - 1, left_y - 1, IRON)
        d.set_pixel(left_x - 1, left_y + 1, IRON)

        # Right end cap
        d.set_pixel(right_x + 1, right_y, IRON)
        d.set_pixel(right_x + 1, right_y - 1, IRON)
        d.set_pixel(right_x + 1, right_y + 1, IRON)

        # Chain/rod attachment points (small circles at beam ends)
        d.set_pixel(left_x, left_y, BRASS_BRIGHT)
        d.set_pixel(right_x, right_y, BRASS_BRIGHT)

    def _draw_hud(self, d):
        """Draw speed indicator."""
        # Show strokes per minute (steam engine standard)
        d.draw_text_small(2, 1, f"{self.cpm}SPM", HUD_COLOR)

        # Speed bar indicator
        bar_x = 48
        bar_y = 2
        for i in range(6):
            if i < self.speed_level:
                d.set_pixel(bar_x + i * 2, bar_y, BRASS)
                d.set_pixel(bar_x + i * 2, bar_y + 1, BRASS)
            else:
                d.set_pixel(bar_x + i * 2, bar_y, IRON_DARK)
                d.set_pixel(bar_x + i * 2, bar_y + 1, IRON_DARK)
