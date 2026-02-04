"""
Curta Calculator
================
The legendary handheld mechanical calculator invented by Curt Herzstark.
A cylindrical core of stepped drums (Leibniz wheels) rotates inside a housing.
Number wheels on top advance as the crank turns. Shows a cross-section with
the drums meshing with result counters.

Controls:
  Left/Right - Adjust crank speed (5 levels)
"""

import math
from . import Visual, Display, Colors, GRID_SIZE


# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------
STEEL = (180, 180, 190)        # Main steel/chrome
STEEL_DARK = (110, 110, 120)   # Darker steel accents
IRON = (80, 80, 90)            # Dark iron/shadow
BRASS = (200, 170, 50)         # Brass highlights (crank, pins)
HOUSING = (50, 50, 55)         # Dark housing/body
HOUSING_LIGHT = (70, 70, 75)   # Housing highlight
DRUM_COLOR = (160, 160, 170)   # Stepped drum color
DRUM_DARK = (100, 100, 110)    # Drum shadow
TOOTH_COLOR = (220, 220, 230)  # Tooth tips (bright)
COUNTER_BG = (30, 30, 35)      # Counter wheel background
COUNTER_FG = (255, 255, 255)   # Counter digits
CRANK_COLOR = (200, 170, 50)   # Crank handle (brass)
HUD_COLOR = (160, 160, 170)    # HUD text

# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------
# Number of stepped drums visible in cross-section
NUM_DRUMS = 5
DRUM_RADIUS = 6
DRUM_SPACING = 11
DRUM_Y = 38           # Y position of drum centers
DRUM_START_X = 9      # X position of leftmost drum

# Counter display at top
COUNTER_Y = 4
COUNTER_HEIGHT = 10
NUM_DIGITS = 8

# Crank position
CRANK_CX = 56
CRANK_CY = 38
CRANK_R = 8

# Teeth per drum (Curta has 9 teeth of varying heights)
NUM_TEETH = 9

# Speed levels (cranks per minute)
SPEED_LEVELS = [15, 30, 60, 90, 120]


class Curta(Visual):
    name = "CURTA"
    description = "Mechanical calculator"
    category = "mechanics"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.crank_angle = 0.0        # Crank rotation in radians
        self.speed_level = 2          # 1-5 (index into SPEED_LEVELS)
        self.cpm = SPEED_LEVELS[self.speed_level]  # Cranks per minute
        self.counter_value = 0        # The accumulator value
        self.last_revolution = 0      # Track completed revolutions
        self.drum_phases = [0.0] * NUM_DRUMS  # Individual drum rotation phases

    def handle_input(self, input_state):
        consumed = False
        if input_state.right_pressed:
            self.speed_level = min(len(SPEED_LEVELS) - 1, self.speed_level + 1)
            self.cpm = SPEED_LEVELS[self.speed_level]
            consumed = True
        elif input_state.left_pressed:
            self.speed_level = max(0, self.speed_level - 1)
            self.cpm = SPEED_LEVELS[self.speed_level]
            consumed = True
        return consumed

    def update(self, dt):
        self.time += dt

        # Rotate crank
        omega = (self.cpm / 60.0) * 2.0 * math.pi
        self.crank_angle += omega * dt

        # Update drum rotations (drums rotate with crank)
        for i in range(NUM_DRUMS):
            # Each drum has a slight phase offset for visual interest
            self.drum_phases[i] = self.crank_angle + (i * 0.3)

        # Count revolutions for counter increment
        current_revolution = int(self.crank_angle / (2.0 * math.pi))
        if current_revolution > self.last_revolution:
            # Each full crank rotation adds to the counter
            # Simulate adding a number (e.g., 137 per turn)
            self.counter_value += 137
            # Wrap at 8 digits
            self.counter_value = self.counter_value % 100000000
            self.last_revolution = current_revolution

    def draw(self):
        d = self.display
        d.clear(Colors.BLACK)

        # Draw order: back to front

        # 1. Housing/body (cylindrical body of calculator)
        self._draw_housing(d)

        # 2. Counter display at top
        self._draw_counter(d)

        # 3. Stepped drums (the heart of the mechanism)
        self._draw_drums(d)

        # 4. Crank mechanism
        self._draw_crank(d)

        # 5. HUD
        self._draw_hud(d)

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------

    def _draw_housing(self, d):
        """Draw the cylindrical housing cross-section."""
        # Main body outline (rectangular cross-section of cylinder)
        body_left = 2
        body_right = 52
        body_top = COUNTER_Y + COUNTER_HEIGHT + 2
        body_bottom = 58

        # Housing background
        d.draw_rect(body_left, body_top, body_right - body_left,
                    body_bottom - body_top, HOUSING)

        # Inner chamber (where drums sit)
        chamber_left = body_left + 3
        chamber_right = body_right - 3
        chamber_top = body_top + 3
        chamber_bottom = body_bottom - 3
        d.draw_rect(chamber_left, chamber_top,
                    chamber_right - chamber_left, chamber_bottom - chamber_top,
                    IRON)

        # Housing edge highlights
        d.draw_line(body_left, body_top, body_right - 1, body_top, HOUSING_LIGHT)
        d.draw_line(body_left, body_top, body_left, body_bottom - 1, HOUSING_LIGHT)

    def _draw_counter(self, d):
        """Draw the result counter wheels at the top."""
        # Counter background
        counter_left = 4
        counter_width = 48
        d.draw_rect(counter_left, COUNTER_Y, counter_width, COUNTER_HEIGHT, COUNTER_BG)

        # Border
        d.draw_rect(counter_left, COUNTER_Y, counter_width, COUNTER_HEIGHT, STEEL_DARK, filled=False)

        # Format counter value as 8 digits
        value_str = f"{self.counter_value:08d}"

        # Draw each digit with a wheel appearance
        digit_width = 5
        digit_start_x = counter_left + 4

        for i, digit in enumerate(value_str):
            dx = digit_start_x + i * digit_width

            # Digit wheel separator line
            if i > 0:
                d.draw_line(dx - 1, COUNTER_Y + 1, dx - 1, COUNTER_Y + COUNTER_HEIGHT - 2, IRON)

            # Draw the digit
            d.draw_text_small(dx, COUNTER_Y + 3, digit, COUNTER_FG)

        # Wheel rotation indicator (subtle animation)
        # Show tick marks that rotate with crank
        tick_y = COUNTER_Y + COUNTER_HEIGHT - 2
        tick_offset = int((self.crank_angle * 2) % 5)
        for i in range(NUM_DIGITS):
            tx = digit_start_x + i * digit_width + tick_offset % 3
            if 0 <= tx < GRID_SIZE:
                d.set_pixel(tx, tick_y, STEEL_DARK)

    def _draw_drums(self, d):
        """Draw the stepped drums (Leibniz wheels)."""
        for drum_idx in range(NUM_DRUMS):
            cx = DRUM_START_X + drum_idx * DRUM_SPACING
            cy = DRUM_Y
            phase = self.drum_phases[drum_idx]

            self._draw_single_drum(d, cx, cy, phase, drum_idx)

    def _draw_single_drum(self, d, cx, cy, phase, drum_idx):
        """Draw a single stepped drum with teeth of varying heights."""
        # Drum body (circle)
        d.draw_circle(cx, cy, DRUM_RADIUS - 1, DRUM_DARK, filled=True)
        d.draw_circle(cx, cy, DRUM_RADIUS, DRUM_COLOR, filled=False)

        # Central axle
        d.set_pixel(cx, cy, BRASS)

        # Draw teeth around the drum
        # In a Curta, each drum has teeth of 9 different heights (0-9)
        # representing the stepped drum mechanism
        for tooth_idx in range(NUM_TEETH):
            tooth_angle = phase + (tooth_idx * 2.0 * math.pi / NUM_TEETH)

            # Tooth height varies (simulating stepped drum)
            # Height represents digit value (0-9)
            tooth_height = (tooth_idx + 1) % 10

            # Scale height for visibility
            base_r = DRUM_RADIUS - 2
            tip_r = base_r + 1 + int(tooth_height / 4)  # Height 0-9 -> extension 1-3 pixels

            # Calculate tooth tip position
            cos_a = math.cos(tooth_angle)
            sin_a = math.sin(tooth_angle)

            tx = int(round(cx + tip_r * sin_a))
            ty = int(round(cy - tip_r * cos_a))

            # Draw tooth as a bright pixel at tip
            if 0 <= tx < GRID_SIZE and 0 <= ty < GRID_SIZE:
                # Brighter for taller teeth
                if tooth_height > 5:
                    d.set_pixel(tx, ty, TOOTH_COLOR)
                else:
                    d.set_pixel(tx, ty, STEEL)

            # Draw tooth stem (line from drum edge to tip)
            bx = int(round(cx + base_r * sin_a))
            by = int(round(cy - base_r * cos_a))
            if tip_r > base_r:
                d.draw_line(bx, by, tx, ty, DRUM_COLOR)

        # Engagement indicator: show which tooth is engaging with counter
        # The topmost tooth (around 270 degrees / -90 degrees) engages
        engage_angle = phase
        engage_tooth = int((engage_angle / (2.0 * math.pi)) * NUM_TEETH) % NUM_TEETH
        engage_height = (engage_tooth + 1) % 10

        # Draw engagement zone (small bright area at top)
        engage_y = cy - DRUM_RADIUS - 2
        if engage_height > 3:
            d.set_pixel(cx, engage_y, BRASS)
            d.set_pixel(cx, engage_y - 1, BRASS)

    def _draw_crank(self, d):
        """Draw the crank mechanism on the right side."""
        sin_a = math.sin(self.crank_angle)
        cos_a = math.cos(self.crank_angle)

        # Crank hub (central pivot)
        d.draw_circle(CRANK_CX, CRANK_CY, 2, STEEL, filled=True)
        d.set_pixel(CRANK_CX, CRANK_CY, BRASS)

        # Crank arm
        arm_x = int(round(CRANK_CX + CRANK_R * sin_a))
        arm_y = int(round(CRANK_CY - CRANK_R * cos_a))
        d.draw_line(CRANK_CX, CRANK_CY, arm_x, arm_y, STEEL)

        # Crank handle (bright knob at end)
        d.set_pixel(arm_x, arm_y, CRANK_COLOR)
        # Add handle detail
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            px, py = arm_x + dx, arm_y + dy
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                d.set_pixel(px, py, BRASS)

        # Draw connecting shaft to drums (horizontal line)
        shaft_y = CRANK_CY
        shaft_start = DRUM_START_X + (NUM_DRUMS - 1) * DRUM_SPACING + DRUM_RADIUS + 2
        d.draw_line(shaft_start, shaft_y, CRANK_CX - 3, shaft_y, STEEL_DARK)

        # Shaft rotation indicator (alternating marks)
        mark_offset = int((self.crank_angle * 4) % 4)
        for i in range(shaft_start + mark_offset, CRANK_CX - 3, 4):
            d.set_pixel(i, shaft_y, STEEL)

    def _draw_hud(self, d):
        """Draw speed indicator."""
        # OPM (operations per minute) at bottom
        d.draw_text_small(2, 59, f"{self.cpm}OPM", HUD_COLOR)

        # Speed level indicator (dots)
        dot_start_x = 44
        dot_y = 60
        for i in range(len(SPEED_LEVELS)):
            if i <= self.speed_level:
                d.set_pixel(dot_start_x + i * 3, dot_y, BRASS)
            else:
                d.set_pixel(dot_start_x + i * 3, dot_y, IRON)
