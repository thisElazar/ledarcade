"""
Cat Stretch - Cozy feline relaxation
====================================
A cat stretching and relaxing on a pillow.
Watch it cycle through stretching, curling up, and peaceful breathing.

Controls:
  Space      - Pet the cat (makes it purr)
  Left/Right - Change cat color
  Up/Down    - Change pillow color
  Escape     - Exit
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE


# Cat color palettes (body, darker shade, ear interior)
CAT_COLORS = [
    ((255, 140, 50), (200, 100, 30), (255, 180, 150)),   # Orange tabby
    ((120, 120, 120), (80, 80, 80), (180, 150, 150)),    # Gray
    ((40, 40, 40), (20, 20, 20), (100, 80, 80)),         # Black
    ((240, 230, 210), (200, 180, 160), (255, 200, 180)), # Cream
    ((180, 140, 100), (130, 90, 60), (200, 160, 140)),   # Brown tabby
]

# Pillow colors
PILLOW_COLORS = [
    ((100, 80, 140), (70, 50, 100)),    # Purple
    ((80, 120, 140), (50, 80, 100)),    # Blue
    ((140, 100, 100), (100, 70, 70)),   # Rose
    ((100, 130, 100), (70, 90, 70)),    # Sage
    ((140, 120, 90), (100, 80, 60)),    # Tan
]


class Cat(Visual):
    name = "CAT"
    description = "Stretching on pillow"
    category = "household"

    # Animation states
    STATE_SLEEPING = 0
    STATE_WAKING = 1
    STATE_STRETCHING = 2
    STATE_RELAXING = 3
    STATE_CURLING = 4

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.state = self.STATE_SLEEPING
        self.state_time = 0.0

        # Color indices
        self.cat_color_idx = 0
        self.pillow_color_idx = 0

        # Animation parameters
        self.stretch_amount = 0.0  # 0 = curled, 1 = fully stretched
        self.breath_phase = 0.0
        self.tail_phase = random.uniform(0, math.pi * 2)
        self.blink_timer = random.uniform(2.0, 5.0)
        self.eyes_closed = False
        self.eye_close_timer = 0.0

        # Purr effect (when petted)
        self.purr_intensity = 0.0

        # Cat position (center of body)
        self.cat_x = 32
        self.cat_y = 38

    def handle_input(self, input_state) -> bool:
        consumed = False

        if (input_state.action_l or input_state.action_r):
            # Pet the cat!
            self.purr_intensity = 1.0
            consumed = True

        if input_state.right:
            self.cat_color_idx = (self.cat_color_idx + 1) % len(CAT_COLORS)
            consumed = True

        if input_state.left:
            self.cat_color_idx = (self.cat_color_idx - 1) % len(CAT_COLORS)
            consumed = True

        if input_state.up:
            self.pillow_color_idx = (self.pillow_color_idx + 1) % len(PILLOW_COLORS)
            consumed = True

        if input_state.down:
            self.pillow_color_idx = (self.pillow_color_idx - 1) % len(PILLOW_COLORS)
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt
        self.state_time += dt

        # Update breath and tail
        self.breath_phase += dt * 1.5
        self.tail_phase += dt * 2.0

        # Decay purr
        if self.purr_intensity > 0:
            self.purr_intensity = max(0, self.purr_intensity - dt * 0.5)

        # Blinking
        self.blink_timer -= dt
        if self.blink_timer <= 0:
            if self.eyes_closed:
                self.eyes_closed = False
                self.blink_timer = random.uniform(2.0, 6.0)
            else:
                self.eyes_closed = True
                self.blink_timer = 0.15

        # State machine for animation cycle
        if self.state == self.STATE_SLEEPING:
            self.stretch_amount = 0.0
            if self.state_time > 4.0:
                self._change_state(self.STATE_WAKING)

        elif self.state == self.STATE_WAKING:
            # Slowly wake up
            self.stretch_amount = min(0.3, self.state_time * 0.15)
            if self.state_time > 2.0:
                self._change_state(self.STATE_STRETCHING)

        elif self.state == self.STATE_STRETCHING:
            # Big stretch!
            target = 1.0
            self.stretch_amount += (target - self.stretch_amount) * dt * 2.0
            if self.state_time > 3.0:
                self._change_state(self.STATE_RELAXING)

        elif self.state == self.STATE_RELAXING:
            # Hold the stretch, then start to relax
            if self.state_time < 1.5:
                self.stretch_amount = 1.0
            else:
                self.stretch_amount = max(0.5, self.stretch_amount - dt * 0.3)
            if self.state_time > 4.0:
                self._change_state(self.STATE_CURLING)

        elif self.state == self.STATE_CURLING:
            # Curl back up
            self.stretch_amount = max(0, self.stretch_amount - dt * 0.4)
            if self.state_time > 3.0:
                self._change_state(self.STATE_SLEEPING)

    def _change_state(self, new_state):
        self.state = new_state
        self.state_time = 0.0

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Get colors
        body_color, dark_color, ear_inner = CAT_COLORS[self.cat_color_idx]
        pillow_main, pillow_dark = PILLOW_COLORS[self.pillow_color_idx]

        # Draw pillow
        self._draw_pillow(pillow_main, pillow_dark)

        # Draw cat
        self._draw_cat(body_color, dark_color, ear_inner)

        # Draw purr hearts if purring
        if self.purr_intensity > 0:
            self._draw_purr_effects()

    def _draw_pillow(self, main_color, dark_color):
        """Draw a cozy pillow."""
        # Pillow is a rounded rectangle
        px, py = 10, 42
        pw, ph = 44, 18

        # Main pillow body
        for y in range(py, py + ph):
            for x in range(px, px + pw):
                # Round the corners
                dx = min(x - px, px + pw - 1 - x)
                dy = min(y - py, py + ph - 1 - y)
                corner_dist = min(dx, dy)

                if corner_dist < 3:
                    # Corner rounding
                    if dx + dy < 4:
                        continue

                # Slight shading - darker at bottom
                if y > py + ph - 4:
                    color = dark_color
                elif y < py + 3:
                    # Lighter at top
                    color = tuple(min(255, c + 20) for c in main_color)
                else:
                    color = main_color

                self.display.set_pixel(x, y, color)

        # Pillow indent where cat sits
        indent_y = py + 2
        for x in range(px + 8, px + pw - 8):
            breathing = math.sin(self.breath_phase) * 0.5
            indent_depth = int(2 + breathing)
            for dy in range(indent_depth):
                self.display.set_pixel(x, indent_y + dy, dark_color)

    def _draw_cat(self, body_color, dark_color, ear_inner):
        """Draw the cat with current animation state."""
        cx, cy = self.cat_x, self.cat_y
        stretch = self.stretch_amount
        breath = math.sin(self.breath_phase)

        # Body dimensions - bigger base size, stretches horizontally
        body_w = int(18 + stretch * 10)
        body_h = int(12 - stretch * 3)

        # Breathing makes body slightly larger/smaller
        body_h = max(9, body_h + int(breath * 0.8))

        # Body center shifts left during stretch
        body_cx = cx - int(stretch * 5)

        # Track body bounds for tail connection
        body_left = body_cx - body_w // 2
        body_right = body_cx + body_w // 2

        # Draw body (filled ellipse)
        for dy in range(-body_h // 2, body_h // 2 + 1):
            # Calculate width at this row for ellipse shape
            if body_h > 0:
                row_factor = 1.0 - (dy * dy) / ((body_h / 2 + 1) ** 2)
                row_factor = max(0, row_factor) ** 0.5
            else:
                row_factor = 1.0
            row_half_width = int(body_w / 2 * row_factor)

            for dx in range(-row_half_width, row_half_width + 1):
                px = body_cx + dx
                py = cy + dy
                if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                    # Shading: darker on bottom and edges
                    if dy > body_h // 2 - 2 or abs(dx) > row_half_width - 2:
                        self.display.set_pixel(px, py, dark_color)
                    else:
                        self.display.set_pixel(px, py, body_color)

        # Head position - moves right and up during stretch
        head_x = body_right - 2 + int(stretch * 4)
        head_y = cy - 4 - int(stretch * 3)
        head_r = 7

        # Draw head (filled circle with slight bottom bulge for cheeks)
        for dy in range(-head_r, head_r + 2):
            for dx in range(-head_r - 1, head_r + 2):
                # Cheek bulge at bottom sides
                cheek_bonus = 0
                if dy > 2:
                    cheek_bonus = 1

                dist_sq = dx * dx + dy * dy
                threshold = (head_r + cheek_bonus) ** 2

                if dist_sq <= threshold:
                    px, py = head_x + dx, head_y + dy
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        self.display.set_pixel(px, py, body_color)

        # Ears - pointy triangles
        ear_positions = [
            (head_x - 5, head_y - 6),  # Left ear
            (head_x + 5, head_y - 6),  # Right ear
        ]
        for ex, ey in ear_positions:
            # Draw ear triangle (taller)
            for row in range(5):
                width = 4 - row
                for dx in range(-width, width + 1):
                    px, py = ex + dx, ey + row
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        # Inner ear is pink, outer is body color
                        if abs(dx) < width - 1 and row > 0:
                            self.display.set_pixel(px, py, ear_inner)
                        else:
                            self.display.set_pixel(px, py, body_color)

        # Eyes - bigger and cuter with highlights
        eye_y = head_y
        left_eye_x = head_x - 3
        right_eye_x = head_x + 3

        if self.state == self.STATE_SLEEPING or self.eyes_closed:
            # Closed eyes - curved lines (happy/sleepy look)
            for ex in [left_eye_x, right_eye_x]:
                self.display.set_pixel(ex - 1, eye_y, dark_color)
                self.display.set_pixel(ex, eye_y, dark_color)
                self.display.set_pixel(ex + 1, eye_y, dark_color)
                # Slight curve up at ends
                self.display.set_pixel(ex - 1, eye_y - 1, dark_color)
                self.display.set_pixel(ex + 1, eye_y - 1, dark_color)
        else:
            # Open eyes - 3x3 with white highlight
            for ex in [left_eye_x, right_eye_x]:
                # Eye white/base
                for edy in range(-1, 2):
                    for edx in range(-1, 2):
                        epx, epy = ex + edx, eye_y + edy
                        if 0 <= epx < GRID_SIZE and 0 <= epy < GRID_SIZE:
                            self.display.set_pixel(epx, epy, (40, 160, 80))  # Green

                # Pupil (center)
                self.display.set_pixel(ex, eye_y, (20, 20, 20))

                # Cute highlight (top-left)
                self.display.set_pixel(ex - 1, eye_y - 1, (255, 255, 255))

        # Nose - small pink triangle
        nose_x, nose_y = head_x, head_y + 4
        self.display.set_pixel(nose_x, nose_y, (255, 140, 150))
        self.display.set_pixel(nose_x - 1, nose_y - 1, (255, 140, 150))
        self.display.set_pixel(nose_x + 1, nose_y - 1, (255, 140, 150))

        # Mouth - little "w" shape or yawn
        if self.state == self.STATE_STRETCHING and self.stretch_amount > 0.7:
            # Yawning - open mouth
            for ydy in range(1, 4):
                for ydx in range(-2, 3):
                    mpx, mpy = nose_x + ydx, nose_y + ydy
                    if 0 <= mpx < GRID_SIZE and 0 <= mpy < GRID_SIZE:
                        if ydy == 1 or abs(ydx) < 2:
                            self.display.set_pixel(mpx, mpy, (180, 90, 100))
        else:
            # Cute little mouth
            self.display.set_pixel(nose_x - 1, nose_y + 1, dark_color)
            self.display.set_pixel(nose_x + 1, nose_y + 1, dark_color)

        # Whiskers (subtle)
        whisker_color = tuple(min(255, c + 60) for c in body_color)
        # Left whiskers
        self.display.set_pixel(head_x - 6, head_y + 2, whisker_color)
        self.display.set_pixel(head_x - 7, head_y + 3, whisker_color)
        # Right whiskers
        self.display.set_pixel(head_x + 6, head_y + 2, whisker_color)
        self.display.set_pixel(head_x + 7, head_y + 3, whisker_color)

        # Front legs/paws when stretching
        if stretch > 0.3:
            leg_extend = int(stretch * 14)
            leg_y = cy + body_h // 2 - 2

            # Leg starts from right side of body and extends outward
            leg_start_x = body_right - 2
            leg_end_x = leg_start_x + leg_extend

            # Draw the leg connecting body to paw
            for px in range(leg_start_x, leg_end_x + 1):
                if 0 <= px < GRID_SIZE:
                    self.display.set_pixel(px, leg_y, body_color)
                    self.display.set_pixel(px, leg_y + 1, body_color)

            # Paw beans at end
            if leg_extend > 3:
                paw_x = leg_end_x
                if 0 <= paw_x < GRID_SIZE and paw_x + 1 < GRID_SIZE:
                    self.display.set_pixel(paw_x, leg_y, (255, 180, 180))
                    self.display.set_pixel(paw_x + 1, leg_y, (255, 180, 180))
                    self.display.set_pixel(paw_x, leg_y + 1, (255, 180, 180))
                    self.display.set_pixel(paw_x + 1, leg_y + 1, (255, 180, 180))

        # Tail - connected to left side of body
        tail_base_x = body_left + 1
        tail_base_y = cy
        tail_length = 12
        tail_curl = 0.4 + (1 - stretch) * 0.4

        prev_tx, prev_ty = tail_base_x, tail_base_y

        for i in range(tail_length):
            t = i / tail_length
            # Tail curves up and back, with gentle wave
            wave = math.sin(self.tail_phase + t * 2.5) * (1.5 + self.purr_intensity * 2) * t
            tx = int(tail_base_x - i * 1.0 - t * t * tail_curl * 6)
            ty = int(tail_base_y - t * 5 + wave)

            # Draw line from previous point to current to ensure connection
            if i > 0:
                self._draw_thick_line(prev_tx, prev_ty, tx, ty, body_color, dark_color, i, tail_length)

            prev_tx, prev_ty = tx, ty

    def _draw_thick_line(self, x0, y0, x1, y1, color, dark_color, segment, total):
        """Draw a thick line segment for the tail."""
        # Bresenham-ish but just draw both points and neighbors
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        steps = max(dx, dy, 1)

        for step in range(steps + 1):
            t = step / steps if steps > 0 else 0
            x = int(x0 + (x1 - x0) * t)
            y = int(y0 + (y1 - y0) * t)

            # Tail gets thinner toward tip
            thickness = 2 if segment < total - 3 else 1

            for ty_off in range(thickness):
                px, py = x, y + ty_off
                if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                    self.display.set_pixel(px, py, color)

    def _draw_purr_effects(self):
        """Draw little hearts when cat is purring."""
        intensity = self.purr_intensity

        # Floating hearts
        num_hearts = int(intensity * 3) + 1
        for i in range(num_hearts):
            phase = self.time * 2 + i * 2.1
            hx = int(self.cat_x + 15 + math.sin(phase) * 5)
            hy = int(25 - (phase % 3) * 5)

            if 0 <= hx < GRID_SIZE - 3 and 0 <= hy < GRID_SIZE - 3:
                # Tiny heart shape
                heart_color = (255, int(100 + 100 * intensity), int(150 * intensity))
                self.display.set_pixel(hx, hy, heart_color)
                self.display.set_pixel(hx + 2, hy, heart_color)
                self.display.set_pixel(hx + 1, hy + 1, heart_color)
