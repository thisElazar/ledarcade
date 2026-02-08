"""
Darts - LED Arcade
==================
Arcade-style darts with raw point scoring (doubles, triples, bullseye).
Two-axis oscillating bar throw mechanic on a full 64x64 dartboard.
1P score attack (5 rounds x 3 darts) and 2P alternating (highest score wins).

Controls:
  Space      - Lock aim axis / confirm selection
  Joystick   - Cancel Y-aim back to X-aim / navigate mode select
"""

import math
import random
from arcade import Game, GameState, Display, Colors, InputState

# Phases (internal, all under GameState.PLAYING)
PHASE_MODE_SELECT = 0
PHASE_AIM_X = 1
PHASE_AIM_Y = 2
PHASE_DART_LAND = 3
PHASE_TURN_CHANGE = 4
PHASE_GAME_OVER_2P = 5

# Dartboard geometry
CX = 31.5
CY = 31.5
MAX_RADIUS = 31

# Ring boundaries (distance from center)
INNER_BULL_R = 2
OUTER_BULL_R = 5
INNER_SINGLE_R = 14
TRIPLE_R = 18
OUTER_SINGLE_R = 25
DOUBLE_R = 31

# Standard dartboard segment order (clockwise from top)
SEGMENT_ORDER = [20, 1, 18, 4, 13, 6, 10, 15, 2, 17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5]

# Segment width in radians (20 segments)
SEG_WIDTH = math.pi / 10  # 18 degrees

# Colors (traditional dartboard palette for LED)
COLOR_A_SINGLE = (20, 20, 20)      # dark
COLOR_A_MULTI = (180, 40, 40)      # red (double/triple)
COLOR_B_SINGLE = (90, 75, 50)      # sienna
COLOR_B_MULTI = (40, 140, 40)      # green (double/triple)
COLOR_OUTER_BULL = (40, 140, 40)   # green
COLOR_INNER_BULL = (180, 40, 40)   # red

# Throw speed
BASE_SPEED = 40.0   # px/s
SPEED_PER_ROUND = 8.0  # +8 px/s per round

# Timing
DART_LAND_TIME = 0.7
TURN_CHANGE_TIME = 0.5

# Rounds / darts
ROUNDS = 5
DARTS_PER_ROUND = 3

# Bonus tile
BONUS_POINTS = 75
COLOR_BONUS = (255, 255, 0)  # bright yellow


class Darts(Game):
    name = "DARTS"
    description = "Arcade darts with doubles, triples, bullseye"
    category = "bar"

    def __init__(self, display: Display):
        super().__init__(display)
        # Precomputed board: (color, face_value, multiplier) per pixel
        self.board_color = None  # 64x64 array of RGB tuples
        self.board_score = None  # 64x64 array of (face_value, multiplier)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.phase = PHASE_MODE_SELECT
        self.score = 0
        self.mode_select = 0  # 0 = 1P, 1 = 2P

        # Game state
        self.two_player = False
        self.current_player = 0
        self.scores = [0, 0]
        self.current_round = 0   # 0-indexed
        self.darts_left = DARTS_PER_ROUND

        # Throw state
        self.sweep_x = 0.0
        self.sweep_y = 0.0
        self.sweep_dir_x = 1   # 1 or -1
        self.sweep_dir_y = 1
        self.locked_x = 0

        # Dart landing
        self.phase_timer = 0.0
        self.last_points = 0
        self.last_label = ""

        # Landed darts for current round (list of (x, y, player))
        self.landed_darts = []

        # Bonus tile: pixels for each (seg_idx, multiplier) on double/triple rings
        self.multi_pixels = {}  # (seg_idx, mult) -> [(x, y), ...]
        self.bonus_key = None   # current (seg_idx, mult) or None
        self.bonus_pixels = set()  # set of (x, y) for fast lookup

        # Precompute board
        self._build_board()

    def _build_board(self):
        """Precompute 64x64 board: color and score for each pixel."""
        self.board_color = [[(0, 0, 0)] * 64 for _ in range(64)]
        self.board_score = [[(0, 0)] * 64 for _ in range(64)]
        self.multi_pixels = {}

        for y in range(64):
            for x in range(64):
                dx = x - CX
                dy = y - CY
                dist = math.sqrt(dx * dx + dy * dy)

                if dist > MAX_RADIUS:
                    self.board_color[y][x] = (0, 0, 0)
                    self.board_score[y][x] = (0, 0)
                    continue

                # Determine ring
                if dist <= INNER_BULL_R:
                    self.board_color[y][x] = COLOR_INNER_BULL
                    self.board_score[y][x] = (50, 1)
                    continue
                elif dist <= OUTER_BULL_R:
                    self.board_color[y][x] = COLOR_OUTER_BULL
                    self.board_score[y][x] = (25, 1)
                    continue

                # Determine segment
                # angle: 0 at top, clockwise positive
                angle = math.atan2(dx, -dy)  # 0=up, clockwise
                if angle < 0:
                    angle += 2 * math.pi

                seg_idx = int((angle + SEG_WIDTH / 2) / SEG_WIDTH) % 20
                face_value = SEGMENT_ORDER[seg_idx]
                is_a = (seg_idx % 2 == 0)  # alternating A/B

                # Determine ring and multiplier
                if dist <= INNER_SINGLE_R:
                    multiplier = 1
                    color = COLOR_A_SINGLE if is_a else COLOR_B_SINGLE
                elif dist <= TRIPLE_R:
                    multiplier = 3
                    color = COLOR_A_MULTI if is_a else COLOR_B_MULTI
                elif dist <= OUTER_SINGLE_R:
                    multiplier = 1
                    color = COLOR_A_SINGLE if is_a else COLOR_B_SINGLE
                elif dist <= DOUBLE_R:
                    multiplier = 2
                    color = COLOR_A_MULTI if is_a else COLOR_B_MULTI
                else:
                    multiplier = 0
                    color = (0, 0, 0)

                self.board_color[y][x] = color
                self.board_score[y][x] = (face_value, multiplier)

                # Collect double/triple ring pixels by segment
                if multiplier in (2, 3):
                    key = (seg_idx, multiplier)
                    if key not in self.multi_pixels:
                        self.multi_pixels[key] = []
                    self.multi_pixels[key].append((x, y))

    def _sweep_speed(self):
        """Current sweep speed in px/s based on round."""
        return BASE_SPEED + SPEED_PER_ROUND * self.current_round

    def _score_dart(self, x, y):
        """Look up score for a dart landing at (x, y). Returns (points, label)."""
        ix = int(round(x))
        iy = int(round(y))
        if ix < 0 or ix >= 64 or iy < 0 or iy >= 64:
            return 0, "MISS"

        # Check bonus tile first
        if (ix, iy) in self.bonus_pixels:
            return BONUS_POINTS, "BONUS!"

        face, mult = self.board_score[iy][ix]
        if face == 0 or mult == 0:
            return 0, "MISS"

        points = face * mult
        if face == 50:
            return points, "BULL!"
        elif face == 25:
            return points, "OUTER BULL"
        elif mult == 3:
            return points, f"TRIPLE {face}!"
        elif mult == 2:
            return points, f"DOUBLE {face}"
        else:
            return points, f"+{points}"

    def _next_dart_or_round(self):
        """Advance to next dart, round, or game over."""
        self.darts_left -= 1

        if self.darts_left > 0:
            # More darts this round
            self._start_aim_x()
            return

        # Round of 3 darts is done
        if self.two_player:
            if self.current_player == 0:
                # P1 done, P2's turn
                self.current_player = 1
                self.darts_left = DARTS_PER_ROUND
                self.landed_darts = []
                self.phase = PHASE_TURN_CHANGE
                self.phase_timer = TURN_CHANGE_TIME
            else:
                # P2 done, end of round
                self.current_round += 1
                if self.current_round >= ROUNDS:
                    self.phase = PHASE_GAME_OVER_2P
                else:
                    self.current_player = 0
                    self.darts_left = DARTS_PER_ROUND
                    self.landed_darts = []
                    self.phase = PHASE_TURN_CHANGE
                    self.phase_timer = TURN_CHANGE_TIME
        else:
            # 1P: advance round
            self.current_round += 1
            self.landed_darts = []
            if self.current_round >= ROUNDS:
                self.state = GameState.GAME_OVER
            else:
                self.darts_left = DARTS_PER_ROUND
                self._start_aim_x()

    def _pick_bonus(self):
        """Pick a random double/triple segment as the bonus tile."""
        keys = list(self.multi_pixels.keys())
        self.bonus_key = random.choice(keys)
        self.bonus_pixels = set(self.multi_pixels[self.bonus_key])

    def _start_aim_x(self):
        """Begin X-axis aiming phase."""
        self._pick_bonus()
        self.phase = PHASE_AIM_X
        self.sweep_x = 32.0
        self.sweep_dir_x = 1

    def _start_aim_y(self):
        """Begin Y-axis aiming phase."""
        self.phase = PHASE_AIM_Y
        self.sweep_y = 32.0
        self.sweep_dir_y = 1

    # ==== UPDATE ====

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        if self.phase == PHASE_MODE_SELECT:
            self._update_mode_select(input_state)
        elif self.phase == PHASE_AIM_X:
            self._update_aim_x(input_state, dt)
        elif self.phase == PHASE_AIM_Y:
            self._update_aim_y(input_state, dt)
        elif self.phase == PHASE_DART_LAND:
            self._update_dart_land(dt)
        elif self.phase == PHASE_TURN_CHANGE:
            self._update_turn_change(dt)
        elif self.phase == PHASE_GAME_OVER_2P:
            self._update_game_over_2p(input_state)

    def _update_mode_select(self, inp):
        if inp.up_pressed or inp.down_pressed:
            self.mode_select = 1 - self.mode_select
        if inp.action_l or inp.action_r:
            self.two_player = (self.mode_select == 1)
            if self.two_player:
                self.scores = [0, 0]
                self.current_player = 0
            else:
                self.score = 0
            self.current_round = 0
            self.darts_left = DARTS_PER_ROUND
            self.landed_darts = []
            self._start_aim_x()

    def _update_aim_x(self, inp, dt):
        speed = self._sweep_speed()
        self.sweep_x += self.sweep_dir_x * speed * dt

        # Bounce at edges
        if self.sweep_x >= 63:
            self.sweep_x = 63
            self.sweep_dir_x = -1
        elif self.sweep_x <= 0:
            self.sweep_x = 0
            self.sweep_dir_x = 1

        if inp.action_l or inp.action_r:
            self.locked_x = int(round(self.sweep_x))
            self._start_aim_y()

    def _update_aim_y(self, inp, dt):
        # Joystick cancels back to AIM_X
        if inp.any_direction:
            self._start_aim_x()
            return

        speed = self._sweep_speed()
        self.sweep_y += self.sweep_dir_y * speed * dt

        # Bounce at edges
        if self.sweep_y >= 63:
            self.sweep_y = 63
            self.sweep_dir_y = -1
        elif self.sweep_y <= 0:
            self.sweep_y = 0
            self.sweep_dir_y = 1

        if inp.action_l or inp.action_r:
            # Dart lands
            land_y = int(round(self.sweep_y))
            land_x = self.locked_x

            points, label = self._score_dart(land_x, land_y)
            self.last_points = points
            self.last_label = label

            # Apply score
            if self.two_player:
                self.scores[self.current_player] += points
                self.score = self.scores[self.current_player]
            else:
                self.score += points

            # Record dart position
            self.landed_darts.append((land_x, land_y, self.current_player))

            self.phase = PHASE_DART_LAND
            self.phase_timer = DART_LAND_TIME

    def _update_dart_land(self, dt):
        self.phase_timer -= dt
        if self.phase_timer <= 0:
            self._next_dart_or_round()

    def _update_turn_change(self, dt):
        self.phase_timer -= dt
        if self.phase_timer <= 0:
            self._start_aim_x()

    def _update_game_over_2p(self, inp):
        if inp.action_l or inp.action_r:
            self.reset()

    # ==== DRAW ====

    def draw(self):
        self.display.clear(Colors.BLACK)

        if self.phase == PHASE_MODE_SELECT:
            self._draw_mode_select()
            return

        if self.phase == PHASE_GAME_OVER_2P:
            self._draw_game_over_2p()
            return

        # Base: dartboard
        self._draw_board()

        # Landed darts
        self._draw_landed_darts()

        # HUD
        self._draw_hud()

        # Phase overlays
        if self.phase == PHASE_AIM_X:
            self._draw_aim_x()
        elif self.phase == PHASE_AIM_Y:
            self._draw_aim_y()
        elif self.phase == PHASE_DART_LAND:
            self._draw_dart_land()
        elif self.phase == PHASE_TURN_CHANGE:
            self._draw_turn_change()

    def _draw_mode_select(self):
        self.display.draw_text_small(14, 10, "DARTS", Colors.WHITE)

        # Simple dartboard icon (circle)
        self.display.draw_circle(31, 28, 7, COLOR_A_MULTI, filled=True)
        self.display.draw_circle(31, 28, 4, COLOR_B_MULTI, filled=True)
        self.display.draw_circle(31, 28, 2, COLOR_INNER_BULL, filled=True)

        y1 = 44
        if self.mode_select == 0:
            self.display.draw_text_small(2, y1, ">1 PLAYER", Colors.YELLOW)
            self.display.draw_text_small(2, y1 + 10, " 2 PLAYERS", Colors.GRAY)
        else:
            self.display.draw_text_small(2, y1, " 1 PLAYER", Colors.GRAY)
            self.display.draw_text_small(2, y1 + 10, ">2 PLAYERS", Colors.YELLOW)

    def _draw_board(self):
        """Blit the precomputed dartboard with bonus tile highlight."""
        for y in range(64):
            for x in range(64):
                if (x, y) in self.bonus_pixels:
                    self.display.set_pixel(x, y, COLOR_BONUS)
                else:
                    c = self.board_color[y][x]
                    if c != (0, 0, 0):
                        self.display.set_pixel(x, y, c)

    def _draw_landed_darts(self):
        """Draw markers for darts that have landed this round."""
        for dx, dy, player in self.landed_darts:
            if self.two_player:
                color = Colors.YELLOW if player == 0 else Colors.CYAN
            else:
                color = Colors.WHITE
            self.display.set_pixel(dx, dy, color)

    def _draw_hud(self):
        """Score and darts-remaining overlay."""
        if self.two_player:
            p1_c = Colors.YELLOW if self.current_player == 0 else Colors.GRAY
            p2_c = Colors.YELLOW if self.current_player == 1 else Colors.GRAY
            self.display.draw_text_small(2, 1, f"P1:{self.scores[0]}", p1_c)
            self.display.draw_text_small(34, 1, f"P2:{self.scores[1]}", p2_c)
        else:
            self.display.draw_text_small(2, 1, f"{self.score}", Colors.WHITE)

        # Darts remaining as dots (top-right)
        dot_x = 60
        dot_y = 2
        for i in range(self.darts_left):
            self.display.set_pixel(dot_x - i * 3, dot_y, Colors.WHITE)
            self.display.set_pixel(dot_x - i * 3, dot_y + 1, Colors.WHITE)

        # Round indicator (bottom-left)
        rnd = self.current_round + 1
        self.display.draw_text_small(2, 59, f"R{rnd}/{ROUNDS}", Colors.GRAY)

    def _draw_aim_x(self):
        """Draw sweeping vertical line."""
        sx = int(round(self.sweep_x))
        for y in range(64):
            self.display.set_pixel(sx, y, Colors.CYAN)

    def _draw_aim_y(self):
        """Draw locked vertical line (dim) and sweeping horizontal line."""
        # Dim locked X line
        dim_cyan = (0, 100, 100)
        for y in range(64):
            self.display.set_pixel(self.locked_x, y, dim_cyan)

        # Bright sweeping Y line
        sy = int(round(self.sweep_y))
        for x in range(64):
            self.display.set_pixel(x, sy, Colors.CYAN)

        # Crosshair highlight at intersection
        self.display.set_pixel(self.locked_x, sy, Colors.WHITE)

    def _draw_dart_land(self):
        """Flash score text for the last dart."""
        # Score text centered on board
        text = self.last_label
        # Estimate width: 4px per char
        tw = len(text) * 4
        tx = max(2, (64 - tw) // 2)

        # Dark backdrop for text
        self.display.draw_rect(tx - 1, 28, tw + 2, 7, (0, 0, 0))

        if self.last_points > 0:
            color = Colors.YELLOW
        else:
            color = Colors.RED
        self.display.draw_text_small(tx, 29, text, color)

    def _draw_turn_change(self):
        p = self.current_player + 1
        self.display.draw_rect(8, 27, 48, 9, (0, 0, 0))
        self.display.draw_text_small(14, 29, f"P{p} TURN", Colors.CYAN)

    def _draw_game_over_2p(self):
        self.display.clear(Colors.BLACK)
        if self.scores[0] > self.scores[1]:
            winner = "P1 WINS!"
            color = Colors.YELLOW
        elif self.scores[1] > self.scores[0]:
            winner = "P2 WINS!"
            color = Colors.YELLOW
        else:
            winner = "TIE GAME"
            color = Colors.CYAN

        self.display.draw_text_small(10, 12, winner, color)
        self.display.draw_text_small(2, 26, f"P1:{self.scores[0]}", Colors.WHITE)
        self.display.draw_text_small(2, 36, f"P2:{self.scores[1]}", Colors.WHITE)
        self.display.draw_text_small(2, 52, "BTN:AGAIN", Colors.GRAY)
