"""
Remington Typewriter
====================
Side-view typewriter with type bars swinging in an arc to strike a platen.
Auto-types "THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG " on repeat.
Carriage slides left per character, sweeps back on return.

Controls:
  Left/Right - Adjust typing speed (6 levels)
"""

import math
from . import Visual, Display, Colors, GRID_SIZE


# --- Color Palette ---
BODY_COLOR = (30, 30, 35)
BODY_DARK = (18, 18, 22)
BODY_ACCENT = (50, 50, 55)

PLATEN_COLOR = (50, 50, 55)
PLATEN_HIGHLIGHT = (70, 70, 80)
PLATEN_KNOB = (120, 120, 130)

CARRIAGE_RAIL = (100, 100, 110)
CARRIAGE_COLOR = (80, 80, 90)

BAR_COLOR = (180, 180, 190)
BAR_BRIGHT = (220, 220, 230)

KEY_COLOR = (40, 40, 45)
KEY_TOP = (60, 60, 65)
KEY_BRIGHT = (90, 90, 95)

PAPER_COLOR = (220, 210, 190)
PAPER_EDGE = (200, 190, 170)
TEXT_COLOR = (40, 30, 20)

BELL_FLASH = (255, 220, 80)

RIBBON_COLOR = (30, 30, 30)
RIBBON_DARK = (15, 15, 15)

HUD_COLOR = (160, 160, 170)

STRIKE_FLASH = (255, 255, 220)

# --- Layout Constants ---
PLATEN_CX = 32
PLATEN_Y = 16
PLATEN_R = 5

PAPER_LEFT = 10
PAPER_RIGHT = 54
PAPER_TOP = 6
PAPER_WIDTH = PAPER_RIGHT - PAPER_LEFT

BASKET_CX = 32
BASKET_Y = 42
BAR_LENGTH = 22

CARRIAGE_Y = 12
CARRIAGE_WIDTH = 48
CARRIAGE_HOME_X = 8  # left edge when at home position

KEY_Y_START = 52
KEY_ROWS = 3
KEY_SPACING_X = 5
KEY_ROW_KEYS = [10, 9, 7]
KEY_ROW_OFFSETS = [7, 10, 14]

# Speed levels: characters per minute
SPEED_CPMS = [30, 60, 120, 200, 300, 450]

# Auto-type text
TYPE_TEXT = "THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG "

# State machine
STATE_IDLE = 0
STATE_BAR_SWING = 1
STATE_STRIKE = 2
STATE_BAR_RETURN = 3
STATE_CARRIAGE_ADVANCE = 4
STATE_BELL = 5
STATE_CARRIAGE_RETURN = 6
STATE_LINE_FEED = 7

# Timing (fractions of one character cycle)
SWING_FRAC = 0.25
STRIKE_FRAC = 0.05
RETURN_FRAC = 0.25
ADVANCE_FRAC = 0.10
BELL_FRAC = 0.15
CR_DURATION = 0.8  # seconds for carriage return sweep
LF_DURATION = 0.3  # seconds for line feed

# Characters per line before carriage return
CHARS_PER_LINE = 10
LINE_SPACING = 6  # pixels between text lines on paper


class Typewriter(Visual):
    name = "TYPEWRITER"
    description = "Remington typewriter"
    category = "mechanics"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed_level = 3  # 1-6
        self.state = STATE_IDLE
        self.state_timer = 0.0
        self.char_index = 0  # position in TYPE_TEXT
        self.col = 0  # current column on line
        self.line = 0  # current line number
        self.bar_progress = 0.0  # 0=rest, 1=at platen
        self.carriage_offset = 0.0  # 0=home (right), increases left
        self.target_carriage = 0.0
        self.typed_lines = []  # list of strings already printed
        self.current_line_text = ""
        self.flash_timer = 0.0
        self.bell_timer = 0.0
        self.strike_flash = 0.0
        self.idle_accumulator = 0.0

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

        cpm = SPEED_CPMS[self.speed_level - 1]
        char_period = 60.0 / cpm  # seconds per character

        # Decay timers
        if self.flash_timer > 0:
            self.flash_timer = max(0.0, self.flash_timer - dt)
        if self.bell_timer > 0:
            self.bell_timer = max(0.0, self.bell_timer - dt)
        if self.strike_flash > 0:
            self.strike_flash = max(0.0, self.strike_flash - dt)

        if self.state == STATE_IDLE:
            self.idle_accumulator += dt
            if self.idle_accumulator >= char_period * 0.35:
                self.idle_accumulator = 0.0
                self.state = STATE_BAR_SWING
                self.state_timer = 0.0
                self.bar_progress = 0.0

        elif self.state == STATE_BAR_SWING:
            duration = char_period * SWING_FRAC
            self.state_timer += dt
            t = min(1.0, self.state_timer / max(0.001, duration))
            self.bar_progress = 0.5 - 0.5 * math.cos(math.pi * t)
            if t >= 1.0:
                self.state = STATE_STRIKE
                self.state_timer = 0.0
                self.strike_flash = 0.1

        elif self.state == STATE_STRIKE:
            duration = char_period * STRIKE_FRAC
            self.state_timer += dt
            self.bar_progress = 1.0
            if self.state_timer >= duration:
                # Print character
                ch = TYPE_TEXT[self.char_index % len(TYPE_TEXT)]
                self.current_line_text += ch
                self.char_index += 1
                self.col += 1
                self.state = STATE_BAR_RETURN
                self.state_timer = 0.0

        elif self.state == STATE_BAR_RETURN:
            duration = char_period * RETURN_FRAC
            self.state_timer += dt
            t = min(1.0, self.state_timer / max(0.001, duration))
            self.bar_progress = 1.0 - (0.5 - 0.5 * math.cos(math.pi * t))
            if t >= 1.0:
                self.bar_progress = 0.0
                if self.col >= CHARS_PER_LINE:
                    self.state = STATE_BELL
                    self.state_timer = 0.0
                    self.bell_timer = 0.3
                else:
                    self.state = STATE_CARRIAGE_ADVANCE
                    self.state_timer = 0.0
                    self.target_carriage = self.col * (PAPER_WIDTH / CHARS_PER_LINE)

        elif self.state == STATE_CARRIAGE_ADVANCE:
            duration = char_period * ADVANCE_FRAC
            self.state_timer += dt
            t = min(1.0, self.state_timer / max(0.001, duration))
            self.carriage_offset += (self.target_carriage - self.carriage_offset) * min(1.0, dt * 15)
            if t >= 1.0:
                self.carriage_offset = self.target_carriage
                self.state = STATE_IDLE
                self.state_timer = 0.0

        elif self.state == STATE_BELL:
            duration = char_period * BELL_FRAC
            self.state_timer += dt
            if self.state_timer >= duration:
                self.state = STATE_CARRIAGE_RETURN
                self.state_timer = 0.0

        elif self.state == STATE_CARRIAGE_RETURN:
            self.state_timer += dt
            t = min(1.0, self.state_timer / max(0.001, CR_DURATION))
            eased = 0.5 - 0.5 * math.cos(math.pi * t)
            self.carriage_offset = self.target_carriage * (1.0 - eased)
            if t >= 1.0:
                self.carriage_offset = 0.0
                self.state = STATE_LINE_FEED
                self.state_timer = 0.0
                # Commit current line
                self.typed_lines.append(self.current_line_text)
                self.current_line_text = ""
                self.col = 0
                # Keep only last few lines visible
                if len(self.typed_lines) > 4:
                    self.typed_lines = self.typed_lines[-4:]

        elif self.state == STATE_LINE_FEED:
            self.state_timer += dt
            if self.state_timer >= LF_DURATION:
                self.line += 1
                self.state = STATE_IDLE
                self.state_timer = 0.0

    def draw(self):
        d = self.display
        d.clear(Colors.BLACK)

        self._draw_body(d)
        self._draw_paper(d)
        self._draw_platen(d)
        self._draw_carriage_rail(d)
        self._draw_type_bar(d)
        self._draw_keyboard(d)
        self._draw_ribbon(d)
        self._draw_bell(d)
        self._draw_hud(d)

    def _draw_body(self, d):
        """Draw the typewriter body/frame."""
        # Main body block
        d.draw_rect(4, 38, 56, 14, BODY_COLOR)
        # Top edge accent
        d.draw_line(4, 38, 59, 38, BODY_ACCENT)
        # Side panels
        d.draw_rect(4, 22, 3, 16, BODY_DARK)
        d.draw_rect(57, 22, 3, 16, BODY_DARK)

    def _draw_paper(self, d):
        """Draw paper curving over the platen with typed text."""
        # Paper behind platen (upper portion visible)
        paper_vis_left = PAPER_LEFT + int(self.carriage_offset * 0.3)
        paper_vis_right = min(63, PAPER_RIGHT + int(self.carriage_offset * 0.3))

        for y in range(PAPER_TOP, PLATEN_Y - PLATEN_R):
            for x in range(paper_vis_left, paper_vis_right + 1):
                if x == paper_vis_left or x == paper_vis_right:
                    d.set_pixel(x, y, PAPER_EDGE)
                else:
                    d.set_pixel(x, y, PAPER_COLOR)

        # Draw typed text on the paper
        text_base_x = paper_vis_left + 2
        for i, line_text in enumerate(self.typed_lines):
            ty = PAPER_TOP + 1 + i * LINE_SPACING
            if ty >= PLATEN_Y - PLATEN_R - 1:
                break
            for j, ch in enumerate(line_text):
                cx = text_base_x + j * 4
                if cx < paper_vis_right - 2 and ty < PLATEN_Y - PLATEN_R - 1:
                    d.draw_text_small(cx, ty, ch, TEXT_COLOR)

        # Current line being typed (at platen position)
        cur_ty = PAPER_TOP + 1 + len(self.typed_lines) * LINE_SPACING
        if cur_ty < PLATEN_Y - PLATEN_R - 1:
            for j, ch in enumerate(self.current_line_text):
                cx = text_base_x + j * 4
                if cx < paper_vis_right - 2:
                    d.draw_text_small(cx, cur_ty, ch, TEXT_COLOR)

    def _draw_platen(self, d):
        """Draw the cylindrical platen roller."""
        # Platen cylinder (horizontal bar with rounded appearance)
        platen_left = 8 + int(self.carriage_offset * 0.3)
        platen_right = min(63, 56 + int(self.carriage_offset * 0.3))

        for y in range(PLATEN_Y - PLATEN_R, PLATEN_Y + PLATEN_R + 1):
            dy = abs(y - PLATEN_Y)
            if dy <= PLATEN_R:
                for x in range(platen_left, platen_right + 1):
                    if dy == 0:
                        d.set_pixel(x, y, PLATEN_HIGHLIGHT)
                    elif dy < PLATEN_R:
                        d.set_pixel(x, y, PLATEN_COLOR)
                    else:
                        d.set_pixel(x, y, BODY_DARK)

        # Platen knobs at ends
        d.set_pixel(platen_left - 1, PLATEN_Y, PLATEN_KNOB)
        d.set_pixel(platen_right + 1, PLATEN_Y, PLATEN_KNOB)

    def _draw_carriage_rail(self, d):
        """Draw the carriage rail."""
        rail_y = PLATEN_Y + PLATEN_R + 2
        d.draw_line(6, rail_y, 58, rail_y, CARRIAGE_RAIL)

        # Carriage indicator (small moving block)
        carriage_x = int(48 - self.carriage_offset * 0.8)
        carriage_x = max(8, min(56, carriage_x))
        d.draw_rect(carriage_x - 2, rail_y - 1, 5, 3, CARRIAGE_COLOR)

    def _draw_type_bar(self, d):
        """Draw the active type bar swinging from basket to platen."""
        if self.bar_progress <= 0.001:
            return

        # Bar swings in an arc from basket to strike point
        # Rest angle: pointing down-ish (~70 deg from vertical)
        # Strike angle: pointing up to platen (~-10 deg from vertical)
        rest_angle = 1.2  # radians from vertical (basket position)
        strike_angle = -0.15  # radians (at platen)

        angle = rest_angle + (strike_angle - rest_angle) * self.bar_progress

        # Bar endpoint
        tip_x = BASKET_CX + BAR_LENGTH * math.sin(angle)
        tip_y = BASKET_Y - BAR_LENGTH * math.cos(angle)

        # Draw bar line
        color = BAR_BRIGHT if self.bar_progress > 0.8 else BAR_COLOR
        d.draw_line(BASKET_CX, BASKET_Y, int(tip_x), int(tip_y), color)

        # Type slug at tip (small block)
        itx, ity = int(tip_x), int(tip_y)
        d.set_pixel(itx, ity, BAR_BRIGHT)
        d.set_pixel(itx - 1, ity, BAR_COLOR)
        d.set_pixel(itx + 1, ity, BAR_COLOR)

        # Strike flash
        if self.strike_flash > 0 and self.bar_progress > 0.9:
            bright = self.strike_flash / 0.1
            fr = int(STRIKE_FLASH[0] * bright)
            fg = int(STRIKE_FLASH[1] * bright)
            fb = int(STRIKE_FLASH[2] * bright)
            flash = (min(255, fr), min(255, fg), min(255, fb))
            d.set_pixel(itx, ity, flash)
            d.set_pixel(itx, ity - 1, flash)
            d.set_pixel(itx, ity + 1, flash)

    def _draw_keyboard(self, d):
        """Draw stylized keyboard rows at the bottom."""
        for row in range(KEY_ROWS):
            num_keys = KEY_ROW_KEYS[row]
            row_x = KEY_ROW_OFFSETS[row]
            ky = KEY_Y_START + row * 4

            for k in range(num_keys):
                kx = row_x + k * KEY_SPACING_X
                # Key cap (3x3 with highlight)
                d.draw_rect(kx, ky, 3, 3, KEY_COLOR)
                d.set_pixel(kx + 1, ky, KEY_TOP)

                # Highlight active key during swing
                if (self.state == STATE_BAR_SWING or self.state == STATE_STRIKE):
                    active_key = self.char_index % num_keys
                    if k == active_key and row == 0:
                        d.draw_rect(kx, ky, 3, 3, KEY_BRIGHT)

    def _draw_ribbon(self, d):
        """Draw ink ribbon between type bars and platen."""
        ribbon_y = PLATEN_Y + PLATEN_R + 1
        d.draw_line(12, ribbon_y, 52, ribbon_y, RIBBON_COLOR)
        # Ribbon spools
        d.set_pixel(10, ribbon_y, RIBBON_DARK)
        d.set_pixel(11, ribbon_y, RIBBON_DARK)
        d.set_pixel(53, ribbon_y, RIBBON_DARK)
        d.set_pixel(54, ribbon_y, RIBBON_DARK)

    def _draw_bell(self, d):
        """Draw bell flash at end of line."""
        if self.bell_timer > 0:
            bright = self.bell_timer / 0.3
            r = int(BELL_FLASH[0] * bright)
            g = int(BELL_FLASH[1] * bright)
            b = int(BELL_FLASH[2] * bright)
            flash = (min(255, r), min(255, g), min(255, b))
            # Bell position near right end of carriage
            bx, by = 55, PLATEN_Y - PLATEN_R - 2
            d.set_pixel(bx, by, flash)
            d.set_pixel(bx - 1, by, flash)
            d.set_pixel(bx + 1, by, flash)
            d.set_pixel(bx, by - 1, flash)

    def _draw_hud(self, d):
        """Draw speed indicator."""
        cpm = SPEED_CPMS[self.speed_level - 1]
        d.draw_text_small(2, 2, f"{cpm} CPM", HUD_COLOR)
