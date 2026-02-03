"""
Remington Typewriter
====================
Side-view typewriter with type bars swinging from a basket semicircle to
strike the platen. Each character swings from a different pivot position
and lights up the matching key. Types Shakespeare soliloquies on repeat.

Controls:
  Left/Right - Adjust typing speed (6 levels)
  Up         - Monkey mode (infinite monkeys easter egg)
"""

import math
import random
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
KEY_ACTIVE = (120, 120, 70)
KEY_FLASH = (160, 160, 90)

PAPER_COLOR = (220, 210, 190)
PAPER_EDGE = (200, 190, 170)
INK_COLOR = (40, 30, 20)
CHAR_FLASH = (255, 255, 0)  # bright yellow for legibility

BELL_FLASH = (255, 220, 80)
RIBBON_COLOR = (30, 30, 30)
RIBBON_DARK = (15, 15, 15)
HUD_COLOR = (160, 160, 170)

# --- Layout ---
PLATEN_Y = 16
PLATEN_R = 4
STRIKE_X = 32
STRIKE_Y = PLATEN_Y + PLATEN_R + 1

PAPER_LEFT = 10
PAPER_RIGHT = 54
PAPER_TOP = 4
PAPER_WIDTH = PAPER_RIGHT - PAPER_LEFT

BASKET_Y = 44

KEY_Y_START = 52
KEY_SPACING_X = 5
KEY_ROW_KEYS = [10, 9, 7]
KEY_ROW_OFFSETS = [7, 10, 14]
KEY_LABELS = [
    list("QWERTYUIOP"),
    list("ASDFGHJKL"),
    list("ZXCVBNM"),
]

# Char -> keyboard (row, col)
CHAR_TO_KEY = {}
for _r, _row in enumerate(KEY_LABELS):
    for _c, _ch in enumerate(_row):
        CHAR_TO_KEY[_ch] = (_r, _c)

# Char -> basket pivot X (bars spread across basket width)
# Keyboard order left-to-right maps to physical bar position
_ALL_KEYS = "QWERTYUIOPASDFGHJKLZXCVBNM"
CHAR_TO_PIVOT_X = {}
for _i, _ch in enumerate(_ALL_KEYS):
    _t = _i / max(1, len(_ALL_KEYS) - 1)
    CHAR_TO_PIVOT_X[_ch] = 10 + _t * 44  # spread x=10 to x=54

SPEED_CPMS = [30, 60, 120, 200, 300, 450]

# Shakespeare soliloquies (most famous passages, letters only)
SOLILOQUIES = [
    "TO BE OR NOT TO BE THAT IS THE QUESTION WHETHER TIS NOBLER "
    "IN THE MIND TO SUFFER THE SLINGS AND ARROWS OF OUTRAGEOUS "
    "FORTUNE OR TO TAKE ARMS AGAINST A SEA OF TROUBLES ",
    "ALL THE WORLDS A STAGE AND ALL THE MEN AND WOMEN MERELY "
    "PLAYERS THEY HAVE THEIR EXITS AND THEIR ENTRANCES AND ONE "
    "MAN IN HIS TIME PLAYS MANY PARTS ",
    "TOMORROW AND TOMORROW AND TOMORROW CREEPS IN THIS PETTY "
    "PACE FROM DAY TO DAY TO THE LAST SYLLABLE OF RECORDED TIME "
    "AND ALL OUR YESTERDAYS HAVE LIGHTED FOOLS THE WAY TO DUSTY "
    "DEATH OUT OUT BRIEF CANDLE ",
    "BUT SOFT WHAT LIGHT THROUGH YONDER WINDOW BREAKS IT IS THE "
    "EAST AND JULIET IS THE SUN ARISE FAIR SUN AND KILL THE "
    "ENVIOUS MOON ",
    "NOW IS THE WINTER OF OUR DISCONTENT MADE GLORIOUS SUMMER BY "
    "THIS SUN OF YORK AND ALL THE CLOUDS THAT LOURED UPON OUR "
    "HOUSE IN THE DEEP BOSOM OF THE OCEAN BURIED ",
    "FRIENDS ROMANS COUNTRYMEN LEND ME YOUR EARS I COME TO BURY "
    "CAESAR NOT TO PRAISE HIM THE EVIL THAT MEN DO LIVES AFTER "
    "THEM THE GOOD IS OFT INTERRED WITH THEIR BONES ",
    "IF MUSIC BE THE FOOD OF LOVE PLAY ON GIVE ME EXCESS OF IT "
    "THAT SURFEITING THE APPETITE MAY SICKEN AND SO DIE ",
    "IS THIS A DAGGER WHICH I SEE BEFORE ME THE HANDLE TOWARD "
    "MY HAND COME LET ME CLUTCH THEE I HAVE THEE NOT AND YET I "
    "SEE THEE STILL ",
    "ONCE MORE UNTO THE BREACH DEAR FRIENDS ONCE MORE OR CLOSE "
    "THE WALL UP WITH OUR DEAD IN PEACE THERE IS NOTHING SO "
    "BECOMES A MAN AS MODEST STILLNESS AND HUMILITY ",
    "WE FEW WE HAPPY FEW WE BAND OF BROTHERS FOR HE TODAY THAT "
    "SHEDS HIS BLOOD WITH ME SHALL BE MY BROTHER ",
    "THE QUALITY OF MERCY IS NOT STRAINED IT DROPPETH AS THE "
    "GENTLE RAIN FROM HEAVEN UPON THE PLACE BENEATH IT IS TWICE "
    "BLESSED IT BLESSETH HIM THAT GIVES AND HIM THAT TAKES ",
    "WHAT A PIECE OF WORK IS MAN HOW NOBLE IN REASON HOW "
    "INFINITE IN FACULTY IN FORM AND MOVING HOW EXPRESS AND "
    "ADMIRABLE IN ACTION HOW LIKE AN ANGEL ",
    "SHALL I COMPARE THEE TO A SUMMERS DAY THOU ART MORE LOVELY "
    "AND MORE TEMPERATE ROUGH WINDS DO SHAKE THE DARLING BUDS "
    "OF MAY ",
    "DOUBLE DOUBLE TOIL AND TROUBLE FIRE BURN AND CAULDRON "
    "BUBBLE ",
    "O ROMEO ROMEO WHEREFORE ART THOU ROMEO DENY THY FATHER AND "
    "REFUSE THY NAME OR IF THOU WILT NOT BE BUT SWORN MY LOVE "
    "AND I SHALL NO LONGER BE A CAPULET ",
]
TYPE_TEXT = "".join(SOLILOQUIES)  # each soliloquy has trailing space

# Monkey mode (hold UP to activate)
MONKEY_FUR = (140, 90, 40)
MONKEY_FACE = (200, 160, 100)
MONKEY_EAR = (170, 120, 65)
MONKEY_EYES = (20, 15, 10)
MONKEY_MOUTH = (120, 80, 40)
MONKEY_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ   "

STATE_IDLE = 0
STATE_BAR_SWING = 1
STATE_STRIKE = 2
STATE_BAR_RETURN = 3
STATE_ADVANCE = 4
STATE_BELL = 5
STATE_CR = 6
STATE_LF = 7

SWING_FRAC = 0.25
STRIKE_FRAC = 0.08
RETURN_FRAC = 0.25
ADVANCE_FRAC = 0.10
BELL_FRAC = 0.15
CR_DURATION = 0.8
LF_DURATION = 0.3
CHARS_PER_LINE = 10
CHAR_SPACING = 3  # px per character on paper
LINE_SPACING = 3


class Typewriter(Visual):
    name = "TYPEWRITER"
    description = "Remington typewriter"
    category = "mechanics"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed_level = 3
        self.state = STATE_IDLE
        self.state_timer = 0.0
        self.char_index = 0
        self.col = 0
        self.line = 0
        self.bar_progress = 0.0
        self.carriage_offset = 0.0
        self.target_carriage = 0.0
        self.typed_lines = []
        self.current_line_text = ""
        self.current_char = ' '
        self.pivot_x = 32.0
        self.bell_timer = 0.0
        self.strike_flash = 0.0
        self.idle_accumulator = 0.0
        self.monkey_mode = False
        self.saved_char_index = 0
        self._input = None

    def handle_input(self, input_state):
        self._input = input_state
        consumed = False
        if input_state.right_pressed:
            self.speed_level = min(6, self.speed_level + 1)
            consumed = True
        elif input_state.left_pressed:
            self.speed_level = max(1, self.speed_level - 1)
            consumed = True
        return consumed

    def _next_word_len(self):
        """Length of the next word starting at current char_index."""
        idx = self.char_index
        text_len = len(TYPE_TEXT)
        length = 0
        while length <= CHARS_PER_LINE:
            ch = TYPE_TEXT[idx % text_len]
            if ch == ' ':
                break
            length += 1
            idx += 1
        return length

    def _next_char(self):
        if self.monkey_mode:
            return random.choice(MONKEY_LETTERS)
        return TYPE_TEXT[self.char_index % len(TYPE_TEXT)]

    def _begin_swing(self, ch):
        self.current_char = ch
        self.pivot_x = CHAR_TO_PIVOT_X.get(ch, 32.0)
        self.state = STATE_BAR_SWING
        self.state_timer = 0.0
        self.bar_progress = 0.0

    def _advance_or_bell(self):
        if self.col >= CHARS_PER_LINE:
            self.state = STATE_BELL
            self.state_timer = 0.0
            self.bell_timer = 0.3
        else:
            self.state = STATE_ADVANCE
            self.state_timer = 0.0
            self.target_carriage = self.col * CHAR_SPACING

    def update(self, dt):
        self.time += dt

        # Monkey mode: active while UP is held
        inp = getattr(self, '_input', None)
        up_held = inp and inp.up if inp else False
        if up_held and not self.monkey_mode:
            self.monkey_mode = True
            self.saved_char_index = self.char_index
        elif not up_held and self.monkey_mode:
            self.monkey_mode = False
            self.char_index = self.saved_char_index

        cpm = SPEED_CPMS[self.speed_level - 1]
        char_period = 60.0 / cpm

        if self.bell_timer > 0:
            self.bell_timer = max(0.0, self.bell_timer - dt)
        if self.strike_flash > 0:
            self.strike_flash = max(0.0, self.strike_flash - dt)

        if self.state == STATE_IDLE:
            self.idle_accumulator += dt
            if self.idle_accumulator >= char_period * 0.35:
                self.idle_accumulator = 0.0
                ch = self._next_char()
                if ch == ' ':
                    self.char_index += 1
                    if self.col == 0:
                        pass  # skip leading spaces on new line
                    else:
                        # Word wrap: if next word won't fit, break line
                        wrap = False
                        if not self.monkey_mode:
                            nw = self._next_word_len()
                            remaining = CHARS_PER_LINE - self.col - 1
                            if nw > remaining and nw <= CHARS_PER_LINE:
                                wrap = True
                        if wrap:
                            self.state = STATE_BELL
                            self.state_timer = 0.0
                            self.bell_timer = 0.3
                        else:
                            self.current_line_text += ' '
                            self.col += 1
                            self._advance_or_bell()
                else:
                    self._begin_swing(ch)

        elif self.state == STATE_BAR_SWING:
            duration = char_period * SWING_FRAC
            self.state_timer += dt
            t = min(1.0, self.state_timer / max(0.001, duration))
            self.bar_progress = 0.5 - 0.5 * math.cos(math.pi * t)
            if t >= 1.0:
                self.state = STATE_STRIKE
                self.state_timer = 0.0
                self.strike_flash = 0.4  # longer display for readability
                self.current_line_text += self.current_char

        elif self.state == STATE_STRIKE:
            duration = char_period * STRIKE_FRAC
            self.state_timer += dt
            self.bar_progress = 1.0
            if self.state_timer >= duration:
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
                self._advance_or_bell()

        elif self.state == STATE_ADVANCE:
            duration = char_period * ADVANCE_FRAC
            self.state_timer += dt
            t = min(1.0, self.state_timer / max(0.001, duration))
            self.carriage_offset += (self.target_carriage - self.carriage_offset) * min(1.0, dt * 15)
            if t >= 1.0:
                self.carriage_offset = self.target_carriage
                self.state = STATE_IDLE
                self.state_timer = 0.0

        elif self.state == STATE_BELL:
            self.state_timer += dt
            if self.state_timer >= char_period * BELL_FRAC:
                self.state = STATE_CR
                self.state_timer = 0.0

        elif self.state == STATE_CR:
            self.state_timer += dt
            t = min(1.0, self.state_timer / max(0.001, CR_DURATION))
            eased = 0.5 - 0.5 * math.cos(math.pi * t)
            self.carriage_offset = self.target_carriage * (1.0 - eased)
            if t >= 1.0:
                self.carriage_offset = 0.0
                self.state = STATE_LF
                self.state_timer = 0.0
                self.typed_lines.append(self.current_line_text)
                self.current_line_text = ""
                self.col = 0
                if len(self.typed_lines) > 5:
                    self.typed_lines = self.typed_lines[-5:]

        elif self.state == STATE_LF:
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
        self._draw_strike_zone(d)
        self._draw_carriage_rail(d)
        self._draw_ribbon(d)
        self._draw_type_bar(d)
        if self.monkey_mode:
            self._draw_monkey(d)
        else:
            self._draw_keyboard(d)
        self._draw_bell(d)
        self._draw_hud(d)

    def _draw_body(self, d):
        d.draw_rect(4, 38, 56, 14, BODY_COLOR)
        d.draw_line(4, 38, 59, 38, BODY_ACCENT)
        d.draw_rect(4, 22, 3, 16, BODY_DARK)
        d.draw_rect(57, 22, 3, 16, BODY_DARK)

    def _draw_paper(self, d):
        # Paper background above platen — all text rendered in _draw_strike_zone
        offset = int(self.carriage_offset)
        pL = max(0, STRIKE_X - 6 - offset)
        pR = min(63, STRIKE_X + CHARS_PER_LINE * CHAR_SPACING + 6 - offset)

        for y in range(PAPER_TOP, PLATEN_Y - PLATEN_R):
            for x in range(pL, pR + 1):
                if x == pL or x == pR:
                    d.set_pixel(x, y, PAPER_EDGE)
                else:
                    d.set_pixel(x, y, PAPER_COLOR)

    def _draw_platen(self, d):
        # Platen slides with the carriage (wider than paper)
        offset = int(self.carriage_offset)
        pL = max(0, STRIKE_X - 10 - offset)
        pR = min(63, STRIKE_X + CHARS_PER_LINE * CHAR_SPACING + 10 - offset)
        for y in range(PLATEN_Y - PLATEN_R, PLATEN_Y + PLATEN_R + 1):
            dy = abs(y - PLATEN_Y)
            for x in range(pL, pR + 1):
                if dy == 0:
                    d.set_pixel(x, y, PLATEN_HIGHLIGHT)
                elif dy < PLATEN_R:
                    d.set_pixel(x, y, PLATEN_COLOR)
                elif dy == PLATEN_R:
                    d.set_pixel(x, y, BODY_DARK)
        if pL > 0:
            d.set_pixel(pL - 1, PLATEN_Y, PLATEN_KNOB)
        if pR < 63:
            d.set_pixel(pR + 1, PLATEN_Y, PLATEN_KNOB)

    def _draw_strike_zone(self, d):
        """Paper wrapping over platen and all text (current + completed)."""
        offset = int(self.carriage_offset)
        pL = max(0, STRIKE_X - 6 - offset)
        pR = min(63, STRIKE_X + CHARS_PER_LINE * CHAR_SPACING + 6 - offset)
        base_x = STRIKE_X - offset

        # Paper wrapping over platen surface (slightly darker to show curve)
        for y in range(PLATEN_Y - PLATEN_R, PLATEN_Y + PLATEN_R - 1):
            for x in range(max(0, pL), min(GRID_SIZE, pR + 1)):
                d.set_pixel(x, y, PAPER_EDGE)

        # Strike zone paper strip (2px tall, front of platen)
        strip_y = PLATEN_Y + PLATEN_R - 1  # y=19
        for x in range(max(0, pL), min(GRID_SIZE, pR + 1)):
            d.set_pixel(x, strip_y, PAPER_COLOR)
            d.set_pixel(x, strip_y + 1, PAPER_EDGE)

        # Current line text at strike zone
        for j, ch in enumerate(self.current_line_text):
            cx = base_x + j * CHAR_SPACING
            if ch != ' ' and 0 <= cx < GRID_SIZE - 1:
                d.set_pixel(cx, strip_y, INK_COLOR)
                d.set_pixel(cx + 1, strip_y, INK_COLOR)

        # Completed lines stack upward continuously from strike zone
        for i, line_text in enumerate(reversed(self.typed_lines)):
            ty = strip_y - (i + 1) * LINE_SPACING
            if ty < PAPER_TOP:
                break
            for j, ch in enumerate(line_text):
                cx = base_x + j * CHAR_SPACING
                if ch != ' ' and 0 <= cx < GRID_SIZE - 1:
                    d.set_pixel(cx, ty, INK_COLOR)
                    d.set_pixel(cx + 1, ty, INK_COLOR)

    def _draw_carriage_rail(self, d):
        rail_y = PLATEN_Y + PLATEN_R + 2
        d.draw_line(6, rail_y, 58, rail_y, CARRIAGE_RAIL)
        cx = int(48 - self.carriage_offset)
        cx = max(8, min(56, cx))
        d.draw_rect(cx - 2, rail_y - 1, 5, 3, CARRIAGE_COLOR)

    def _draw_type_bar(self, d):
        if self.bar_progress <= 0.001:
            return

        px = self.pivot_x
        py = float(BASKET_Y)

        # Compute swing arc from rest (below pivot) to strike point
        dx = STRIKE_X - px
        dy = STRIKE_Y - py  # negative (strike is above)
        bar_len = math.sqrt(dx * dx + dy * dy)
        strike_angle = math.atan2(dy, dx)

        # Rest: bar hangs downward from its pivot
        rest_angle = math.pi * 0.55

        # Eased interpolation
        angle = rest_angle + (strike_angle - rest_angle) * self.bar_progress
        tip_x = px + bar_len * math.cos(angle)
        tip_y = py + bar_len * math.sin(angle)

        color = BAR_BRIGHT if self.bar_progress > 0.8 else BAR_COLOR
        d.draw_line(int(px), int(py), int(tip_x), int(tip_y), color)

        # Type slug at tip
        itx, ity = int(tip_x), int(tip_y)
        d.set_pixel(itx, ity, BAR_BRIGHT)

        # Strike flash — show the actual character in yellow, fading smoothly
        if self.strike_flash > 0 and self.current_char != ' ':
            # Smooth fade: full brightness for first half, then fade out
            t = self.strike_flash / 0.4
            if t > 0.5:
                bright = 1.0
            else:
                bright = t / 0.5  # fade from 1.0 to 0 over second half
            # Ease the fade for smoothness
            bright = bright * bright * (3 - 2 * bright)  # smoothstep
            r = int(CHAR_FLASH[0] * bright)
            g = int(CHAR_FLASH[1] * bright)
            b = int(CHAR_FLASH[2] * bright)
            if r > 10 or g > 10:  # only draw if visible
                d.draw_text_small(STRIKE_X - 2, STRIKE_Y - 2, self.current_char, (r, g, b))

    def _draw_keyboard(self, d):
        for row in range(3):
            num_keys = KEY_ROW_KEYS[row]
            row_x = KEY_ROW_OFFSETS[row]
            ky = KEY_Y_START + row * 4
            for k in range(num_keys):
                kx = row_x + k * KEY_SPACING_X
                d.draw_rect(kx, ky, 3, 3, KEY_COLOR)
                d.set_pixel(kx + 1, ky, KEY_TOP)

        # Highlight the correct key
        if self.state in (STATE_BAR_SWING, STATE_STRIKE, STATE_BAR_RETURN):
            if self.current_char in CHAR_TO_KEY:
                row, idx = CHAR_TO_KEY[self.current_char]
                kx = KEY_ROW_OFFSETS[row] + idx * KEY_SPACING_X
                ky = KEY_Y_START + row * 4
                c = KEY_FLASH if self.state == STATE_STRIKE else KEY_ACTIVE
                d.draw_rect(kx, ky, 3, 3, c)

    def _draw_monkey(self, d):
        """Easter egg: a monkey typing at the keyboard."""
        cx, cy = 32, 50

        # Body
        d.draw_circle(cx, cy + 4, 4, MONKEY_FUR, filled=True)

        # Head
        d.draw_circle(cx, cy, 5, MONKEY_FUR, filled=True)
        d.draw_circle(cx, cy + 1, 3, MONKEY_FACE, filled=True)

        # Ears
        d.draw_circle(cx - 5, cy - 1, 2, MONKEY_FUR, filled=True)
        d.draw_circle(cx + 5, cy - 1, 2, MONKEY_FUR, filled=True)
        d.set_pixel(cx - 5, cy - 1, MONKEY_EAR)
        d.set_pixel(cx + 5, cy - 1, MONKEY_EAR)

        # Eyes (blink occasionally)
        blink = (int(self.time * 3) % 7) == 0
        if not blink:
            d.set_pixel(cx - 2, cy - 1, MONKEY_EYES)
            d.set_pixel(cx + 2, cy - 1, MONKEY_EYES)

        # Nose and mouth
        d.set_pixel(cx, cy + 1, MONKEY_MOUTH)
        d.set_pixel(cx - 1, cy + 2, MONKEY_MOUTH)
        d.set_pixel(cx + 1, cy + 2, MONKEY_MOUTH)

        # Arms reaching to keyboard area (animated)
        arm_phase = math.sin(self.time * 8) * 2
        lx = cx - 8 + int(arm_phase)
        rx = cx + 8 - int(arm_phase)
        d.draw_line(cx - 4, cy + 5, lx, cy + 10, MONKEY_FUR)
        d.draw_line(cx + 4, cy + 5, rx, cy + 10, MONKEY_FUR)

        # Hands (little dots at arm ends)
        d.set_pixel(lx, cy + 10, MONKEY_FACE)
        d.set_pixel(rx, cy + 10, MONKEY_FACE)

    def _draw_ribbon(self, d):
        ry = PLATEN_Y + PLATEN_R + 1
        d.draw_line(12, ry, 52, ry, RIBBON_COLOR)
        d.set_pixel(10, ry, RIBBON_DARK)
        d.set_pixel(11, ry, RIBBON_DARK)
        d.set_pixel(53, ry, RIBBON_DARK)
        d.set_pixel(54, ry, RIBBON_DARK)

    def _draw_bell(self, d):
        if self.bell_timer > 0:
            b = self.bell_timer / 0.3
            flash = (int(BELL_FLASH[0] * b), int(BELL_FLASH[1] * b), int(BELL_FLASH[2] * b))
            bx, by = 55, PLATEN_Y - PLATEN_R - 2
            d.set_pixel(bx, by, flash)
            d.set_pixel(bx - 1, by, flash)
            d.set_pixel(bx + 1, by, flash)
            d.set_pixel(bx, by - 1, flash)

    def _draw_hud(self, d):
        cpm = SPEED_CPMS[self.speed_level - 1]
        d.draw_text_small(2, 2, f"{cpm} CPM", HUD_COLOR)
