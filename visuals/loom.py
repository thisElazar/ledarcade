"""
Power Loom
==========
Side-view cutaway of an industrial power loom weaving fabric.
The shuttle flies back and forth through the shed (gap between raised and lowered
warp threads). Heddles alternate which threads are up/down after each pass.
The beater pushes the new weft thread tight. Rhythmic, industrial, mesmerizing.

Controls:
  Left/Right - Adjust weaving speed (6 levels)
"""

import math
from . import Visual, Display, Colors, GRID_SIZE


# --- Color Palette (industrial/metallic) ---

# Steel gray (machine frame)
STEEL_GRAY = (180, 180, 190)
STEEL_DARK = (120, 120, 130)
STEEL_LIGHT = (200, 200, 210)

# Dark iron (heavy machinery)
DARK_IRON = (80, 80, 90)
DARK_IRON_LIGHT = (100, 100, 110)
DARK_IRON_DARK = (50, 50, 60)

# Brass/gold (accents and mechanisms)
BRASS = (200, 170, 50)
BRASS_DIM = (150, 125, 35)
BRASS_BRIGHT = (230, 195, 70)

# Copper (shuttle and heddles)
COPPER = (200, 120, 60)
COPPER_DIM = (150, 90, 45)
COPPER_BRIGHT = (230, 145, 80)

# Warp threads (vertical)
WARP_LIGHT = (220, 200, 160)  # Natural cotton/linen
WARP_DARK = (180, 160, 120)
WARP_DIM = (120, 100, 80)  # Dimmer for background threads

# Weft thread (horizontal, carried by shuttle)
WEFT_COLOR = (180, 60, 60)  # Colored thread
WEFT_DIM = (140, 45, 45)

# Woven fabric
FABRIC_LIGHT = (200, 180, 140)
FABRIC_DARK = (160, 140, 100)
FABRIC_EDGE = (130, 115, 85)

# HUD
HUD_COLOR = (160, 160, 170)

# --- Layout Constants ---

# Main frame
FRAME_TOP = 8
FRAME_BOT = 56
FRAME_LEFT = 2
FRAME_RIGHT = 62

# Warp beam (back roller with threads wound on it)
WARP_BEAM_CX = 56
WARP_BEAM_CY = 14
WARP_BEAM_R = 4

# Cloth beam (front roller where fabric accumulates)
CLOTH_BEAM_CX = 8
CLOTH_BEAM_CY = 50
CLOTH_BEAM_R = 5

# Heddle frames (control warp thread up/down)
HEDDLE_LEFT = 28
HEDDLE_RIGHT = 40
HEDDLE_TOP_UP = 18
HEDDLE_TOP_DOWN = 26
HEDDLE_BOT_UP = 36
HEDDLE_BOT_DOWN = 44

# Shed (gap where shuttle passes)
SHED_Y = 31  # center of shed
SHED_HEIGHT = 8  # half-height of shed opening

# Beater (pushes weft tight)
BEATER_Y_BACK = 32
BEATER_Y_FRONT = 28
BEATER_LEFT = 18
BEATER_RIGHT = 48

# Shuttle path
SHUTTLE_Y = SHED_Y
SHUTTLE_LEFT = 4
SHUTTLE_RIGHT = 60
SHUTTLE_WIDTH = 6
SHUTTLE_HEIGHT = 3

# Warp thread positions (x coordinates of vertical threads)
NUM_WARP_THREADS = 12
WARP_THREAD_START = 16
WARP_THREAD_END = 50
WARP_THREAD_SPACING = (WARP_THREAD_END - WARP_THREAD_START) // (NUM_WARP_THREADS - 1)

# Speed levels (passes per minute)
SPEED_PPMS = [15, 30, 50, 80, 120, 160]


class Loom(Visual):
    name = "LOOM"
    description = "Power loom"
    category = "mechanics"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed_level = 3  # 1-6

        # Shuttle state
        self.shuttle_x = SHUTTLE_LEFT
        self.shuttle_direction = 1  # 1 = right, -1 = left
        self.shuttle_phase = 0.0  # 0 to 1 for one pass

        # Heddle state: which set is up (0 or 1)
        # Even threads up when heddle_state=0, odd when heddle_state=1
        self.heddle_state = 0
        self.heddle_transition = 0.0  # 0 to 1 for smooth transition
        self.heddle_transitioning = False

        # Beater state
        self.beater_phase = 0.0  # 0 to 1 for beat cycle
        self.beater_forward = False

        # Woven fabric tracking
        self.fabric_rows = []  # list of (weft_y, heddle_state) tuples
        self.pass_count = 0

        # Initialize some pre-woven fabric
        for i in range(8):
            self.fabric_rows.append((CLOTH_BEAM_CY - 15 + i, i % 2))

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

        # Get current speed
        ppm = SPEED_PPMS[self.speed_level - 1]
        pass_duration = 60.0 / ppm  # seconds per pass

        # Update shuttle position
        shuttle_speed = (SHUTTLE_RIGHT - SHUTTLE_LEFT) / pass_duration
        self.shuttle_x += self.shuttle_direction * shuttle_speed * dt

        # Update shuttle phase
        self.shuttle_phase += dt / pass_duration

        # Check for shuttle reaching edge
        if self.shuttle_direction == 1 and self.shuttle_x >= SHUTTLE_RIGHT - SHUTTLE_WIDTH:
            self.shuttle_x = SHUTTLE_RIGHT - SHUTTLE_WIDTH
            self._complete_pass()
        elif self.shuttle_direction == -1 and self.shuttle_x <= SHUTTLE_LEFT:
            self.shuttle_x = SHUTTLE_LEFT
            self._complete_pass()

        # Update heddle transition
        if self.heddle_transitioning:
            transition_speed = 4.0  # transitions per second
            self.heddle_transition += transition_speed * dt
            if self.heddle_transition >= 1.0:
                self.heddle_transition = 0.0
                self.heddle_transitioning = False

        # Update beater
        if self.beater_forward:
            beater_speed = 3.0  # beats per second
            self.beater_phase += beater_speed * dt
            if self.beater_phase >= 1.0:
                self.beater_phase = 0.0
                self.beater_forward = False

    def _complete_pass(self):
        """Called when shuttle completes a pass."""
        self.pass_count += 1

        # Reverse shuttle direction
        self.shuttle_direction *= -1
        self.shuttle_phase = 0.0

        # Record fabric row
        fabric_y = BEATER_Y_FRONT - 2  # where weft gets pushed
        self.fabric_rows.append((fabric_y, self.heddle_state))

        # Limit fabric rows to prevent memory growth
        if len(self.fabric_rows) > 30:
            self.fabric_rows = self.fabric_rows[-25:]

        # Start heddle transition and beater beat
        self.heddle_state = 1 - self.heddle_state
        self.heddle_transitioning = True
        self.beater_forward = True

    def draw(self):
        d = self.display
        d.clear(Colors.BLACK)

        # Draw order: back to front
        self._draw_warp_beam(d)
        self._draw_frame(d)
        self._draw_warp_threads(d)
        self._draw_heddles(d)
        self._draw_beater(d)
        self._draw_shuttle(d)
        self._draw_fabric(d)
        self._draw_cloth_beam(d)
        self._draw_hud(d)

    def _draw_frame(self, d):
        """Draw the loom's main frame structure."""
        # Top beam
        d.draw_rect(FRAME_LEFT, FRAME_TOP, FRAME_RIGHT - FRAME_LEFT, 3, DARK_IRON)
        d.draw_line(FRAME_LEFT, FRAME_TOP, FRAME_RIGHT - 1, FRAME_TOP, DARK_IRON_LIGHT)

        # Left upright
        d.draw_rect(FRAME_LEFT, FRAME_TOP, 3, FRAME_BOT - FRAME_TOP, DARK_IRON)
        d.draw_line(FRAME_LEFT, FRAME_TOP, FRAME_LEFT, FRAME_BOT - 1, DARK_IRON_LIGHT)

        # Right upright
        d.draw_rect(FRAME_RIGHT - 3, FRAME_TOP, 3, FRAME_BOT - FRAME_TOP, DARK_IRON)
        d.draw_line(FRAME_RIGHT - 1, FRAME_TOP, FRAME_RIGHT - 1, FRAME_BOT - 1, DARK_IRON_LIGHT)

        # Bottom beam
        d.draw_rect(FRAME_LEFT, FRAME_BOT - 3, FRAME_RIGHT - FRAME_LEFT, 3, DARK_IRON)
        d.draw_line(FRAME_LEFT, FRAME_BOT - 1, FRAME_RIGHT - 1, FRAME_BOT - 1, DARK_IRON_DARK)

        # Brass decorative rivets
        for x in [FRAME_LEFT + 1, FRAME_RIGHT - 2]:
            for y in [FRAME_TOP + 5, FRAME_TOP + 20, FRAME_TOP + 35]:
                d.set_pixel(x, y, BRASS)

    def _draw_warp_beam(self, d):
        """Draw the back roller with wound warp threads."""
        cx, cy, r = WARP_BEAM_CX, WARP_BEAM_CY, WARP_BEAM_R

        # Beam core
        self._draw_circle_filled(d, cx, cy, r, STEEL_DARK)
        self._draw_circle_outline(d, cx, cy, r, STEEL_GRAY)

        # Wound thread appearance (concentric rings)
        for ring in range(r - 2, 0, -1):
            color = WARP_LIGHT if ring % 2 == 0 else WARP_DARK
            self._draw_circle_outline(d, cx, cy, ring, color)

        # Axle
        d.set_pixel(cx, cy, BRASS)

        # Threads unwinding from beam toward heddles
        for i in range(NUM_WARP_THREADS):
            x = WARP_THREAD_START + i * WARP_THREAD_SPACING
            # Thread from beam edge to top of heddle area
            d.draw_line(cx - r, cy + 2, x, HEDDLE_TOP_UP - 2, WARP_DIM)

    def _draw_cloth_beam(self, d):
        """Draw the front roller where woven fabric accumulates."""
        cx, cy, r = CLOTH_BEAM_CX, CLOTH_BEAM_CY, CLOTH_BEAM_R

        # Beam core
        self._draw_circle_filled(d, cx, cy, r, STEEL_DARK)
        self._draw_circle_outline(d, cx, cy, r, STEEL_GRAY)

        # Wound fabric appearance
        for ring in range(r - 1, 0, -1):
            color = FABRIC_LIGHT if ring % 2 == 0 else FABRIC_DARK
            self._draw_circle_outline(d, cx, cy, ring, color)

        # Axle
        d.set_pixel(cx, cy, BRASS_BRIGHT)

    def _get_thread_y(self, thread_index, at_heddle=True):
        """Get the Y position of a warp thread based on current heddle state."""
        is_even = thread_index % 2 == 0

        if self.heddle_transitioning:
            # Smooth transition
            t = self.heddle_transition
            # Ease in-out
            t = t * t * (3.0 - 2.0 * t)

            if self.heddle_state == 0:
                # Transitioning TO state 0 (even up)
                if is_even:
                    y = HEDDLE_BOT_DOWN + t * (HEDDLE_TOP_UP - HEDDLE_BOT_DOWN)
                else:
                    y = HEDDLE_TOP_UP + t * (HEDDLE_BOT_DOWN - HEDDLE_TOP_UP)
            else:
                # Transitioning TO state 1 (odd up)
                if is_even:
                    y = HEDDLE_TOP_UP + t * (HEDDLE_BOT_DOWN - HEDDLE_TOP_UP)
                else:
                    y = HEDDLE_BOT_DOWN + t * (HEDDLE_TOP_UP - HEDDLE_BOT_DOWN)
        else:
            # Static position
            if self.heddle_state == 0:
                y = HEDDLE_TOP_UP if is_even else HEDDLE_BOT_DOWN
            else:
                y = HEDDLE_BOT_DOWN if is_even else HEDDLE_TOP_UP

        return int(y)

    def _draw_warp_threads(self, d):
        """Draw the vertical warp threads passing through the heddles."""
        for i in range(NUM_WARP_THREADS):
            x = WARP_THREAD_START + i * WARP_THREAD_SPACING
            thread_y = self._get_thread_y(i)

            # Thread color alternates
            color = WARP_LIGHT if i % 2 == 0 else WARP_DARK

            # Draw thread from heddle area down toward beater/fabric
            # Upper portion (above heddle eye to warp beam)
            d.draw_line(x, HEDDLE_TOP_UP - 4, x, thread_y, color)

            # Lower portion (below heddle eye to fabric)
            d.draw_line(x, thread_y, x, BEATER_Y_FRONT + 2, color)

    def _draw_heddles(self, d):
        """Draw the heddle frames that raise/lower warp threads."""
        # Two heddle frames: one for even threads, one for odd

        for frame in range(2):
            is_up = (self.heddle_state == frame) != self.heddle_transitioning

            if self.heddle_transitioning:
                t = self.heddle_transition
                t = t * t * (3.0 - 2.0 * t)  # ease
                if self.heddle_state == frame:
                    # This frame is moving up
                    frame_y = HEDDLE_BOT_DOWN + t * (HEDDLE_TOP_UP - HEDDLE_BOT_DOWN)
                else:
                    # This frame is moving down
                    frame_y = HEDDLE_TOP_UP + t * (HEDDLE_BOT_DOWN - HEDDLE_TOP_UP)
            else:
                frame_y = HEDDLE_TOP_UP if self.heddle_state == frame else HEDDLE_BOT_DOWN

            frame_y = int(frame_y)

            # Frame bar
            frame_color = COPPER if frame == 0 else COPPER_DIM
            bar_x_left = HEDDLE_LEFT - 2
            bar_x_right = HEDDLE_RIGHT + 2
            d.draw_line(bar_x_left, frame_y, bar_x_right, frame_y, frame_color)
            d.draw_line(bar_x_left, frame_y + 1, bar_x_right, frame_y + 1, frame_color)

            # Heddle eyes (small loops that hold threads)
            for i in range(NUM_WARP_THREADS):
                if i % 2 == frame:
                    x = WARP_THREAD_START + i * WARP_THREAD_SPACING
                    d.set_pixel(x, frame_y, BRASS)
                    d.set_pixel(x, frame_y + 1, BRASS_DIM)

            # Vertical connection rods to frame
            d.draw_line(bar_x_left, FRAME_TOP + 3, bar_x_left, frame_y, STEEL_DARK)
            d.draw_line(bar_x_right, FRAME_TOP + 3, bar_x_right, frame_y, STEEL_DARK)

    def _draw_beater(self, d):
        """Draw the beater that pushes weft thread tight."""
        # Beater swings forward to push weft
        if self.beater_forward:
            t = self.beater_phase
            # Quick forward, slow back
            if t < 0.3:
                swing = t / 0.3
            else:
                swing = 1.0 - (t - 0.3) / 0.7
            beater_y = BEATER_Y_BACK - int(swing * (BEATER_Y_BACK - BEATER_Y_FRONT))
        else:
            beater_y = BEATER_Y_BACK

        # Beater frame (reed)
        d.draw_rect(BEATER_LEFT, beater_y - 1, BEATER_RIGHT - BEATER_LEFT, 3, STEEL_GRAY)
        d.draw_line(BEATER_LEFT, beater_y - 1, BEATER_RIGHT - 1, beater_y - 1, STEEL_LIGHT)
        d.draw_line(BEATER_LEFT, beater_y + 1, BEATER_RIGHT - 1, beater_y + 1, STEEL_DARK)

        # Reed dents (vertical slits)
        for x in range(BEATER_LEFT + 2, BEATER_RIGHT - 2, 2):
            d.set_pixel(x, beater_y, DARK_IRON)

        # Pivot points at frame
        d.set_pixel(BEATER_LEFT - 1, beater_y, BRASS)
        d.set_pixel(BEATER_RIGHT, beater_y, BRASS)

    def _draw_shuttle(self, d):
        """Draw the shuttle carrying weft thread."""
        sx = int(self.shuttle_x)
        sy = SHUTTLE_Y

        # Shuttle body (boat-shaped)
        # Pointed ends, wider middle
        d.draw_rect(sx + 1, sy - 1, SHUTTLE_WIDTH - 2, SHUTTLE_HEIGHT, COPPER)

        # Pointed ends
        if self.shuttle_direction == 1:
            # Moving right - point on right
            d.set_pixel(sx + SHUTTLE_WIDTH - 1, sy, COPPER_BRIGHT)
            d.set_pixel(sx, sy - 1, COPPER_DIM)
            d.set_pixel(sx, sy, COPPER_DIM)
            d.set_pixel(sx, sy + 1, COPPER_DIM)
        else:
            # Moving left - point on left
            d.set_pixel(sx, sy, COPPER_BRIGHT)
            d.set_pixel(sx + SHUTTLE_WIDTH - 1, sy - 1, COPPER_DIM)
            d.set_pixel(sx + SHUTTLE_WIDTH - 1, sy, COPPER_DIM)
            d.set_pixel(sx + SHUTTLE_WIDTH - 1, sy + 1, COPPER_DIM)

        # Bobbin in shuttle (wound weft thread)
        bobbin_x = sx + SHUTTLE_WIDTH // 2
        d.set_pixel(bobbin_x, sy, WEFT_COLOR)
        d.set_pixel(bobbin_x - 1, sy, WEFT_DIM)
        d.set_pixel(bobbin_x + 1, sy, WEFT_DIM)

        # Weft thread trailing behind shuttle
        if self.shuttle_direction == 1:
            # Thread trails to left
            d.draw_line(BEATER_LEFT, sy, sx, sy, WEFT_COLOR)
        else:
            # Thread trails to right
            d.draw_line(sx + SHUTTLE_WIDTH, sy, BEATER_RIGHT - 1, sy, WEFT_COLOR)

    def _draw_fabric(self, d):
        """Draw the woven fabric accumulating at the cloth beam."""
        # Draw fabric area (between beater and cloth beam)
        fabric_left = CLOTH_BEAM_CX + CLOTH_BEAM_R + 2
        fabric_right = BEATER_LEFT - 2
        fabric_top = BEATER_Y_FRONT + 3
        fabric_bot = CLOTH_BEAM_CY - 2

        # Draw woven pattern
        for y in range(fabric_top, fabric_bot):
            for x in range(fabric_left, fabric_right):
                # Weave pattern based on position
                row_offset = (y - fabric_top) % 2
                col_offset = (x - fabric_left) % 2

                if (row_offset + col_offset) % 2 == 0:
                    color = FABRIC_LIGHT
                else:
                    color = FABRIC_DARK

                # Add weft color every few rows
                if (y - fabric_top) % 3 == 0:
                    if col_offset == 0:
                        color = WEFT_DIM

                d.set_pixel(x, y, color)

        # Fabric edge highlight
        d.draw_line(fabric_left, fabric_top, fabric_right - 1, fabric_top, FABRIC_EDGE)

    def _draw_circle_filled(self, d, cx, cy, r, color):
        """Draw a filled circle."""
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if dx * dx + dy * dy <= r * r:
                    d.set_pixel(cx + dx, cy + dy, color)

    def _draw_circle_outline(self, d, cx, cy, r, color):
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

    def _draw_hud(self, d):
        """Draw speed indicator."""
        ppm = SPEED_PPMS[self.speed_level - 1]
        d.draw_text_small(2, 2, f"{ppm} PPM", HUD_COLOR)

        # Pass counter
        d.draw_text_small(42, 2, f"{self.pass_count}", HUD_COLOR)
