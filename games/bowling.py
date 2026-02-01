"""
Bowling - LED Arcade
====================
10-pin bowling with top-down lane view on a 64x64 LED matrix.
Two-step throw mechanic: position marker then aim direction.
1P score attack (10 frames) and 2P alternating (highest score wins).

Controls:
  Space      - Lock position / confirm aim / navigate mode select
  Joystick   - Cancel aim back to position / navigate mode select
"""

import math
import random
from arcade import Game, GameState, Display, Colors, InputState

# Phases
PHASE_MODE_SELECT = 0
PHASE_POSITION = 1
PHASE_AIM = 2
PHASE_ROLLING = 3
PHASE_PIN_FALL = 4
PHASE_SCORE_SHOW = 5
PHASE_TURN_CHANGE = 6
PHASE_GAME_OVER_2P = 7

# Lane geometry
LANE_LEFT = 14
LANE_RIGHT = 49
LANE_WIDTH = LANE_RIGHT - LANE_LEFT  # 36px
LANE_COLOR = (140, 100, 50)        # wood
GUTTER_COLOR = (60, 50, 30)        # dark wood
FOUL_LINE_Y = 50
APPROACH_TOP = 51
APPROACH_BOTTOM = 56

# Pin deck area
PIN_DECK_TOP = 9
PIN_DECK_BOTTOM = 28

# HUD
HUD_TOP = 0
HUD_BOTTOM = 8

# Ball
BALL_COLOR = (200, 200, 220)
BALL_SPEED = 60.0  # px/s upward
BALL_RADIUS = 1.5  # collision radius

# Pin layout: 10-pin triangle, back row at y=12, headpin at y=26
# Row 0 (back, 4 pins), Row 1 (3 pins), Row 2 (2 pins), Row 3 (headpin)
PIN_ROWS = [
    # (x_offset_from_center, y) for each row
    # Back row: 4 pins, spaced 5px apart, centered on lane
    [(-7, 12), (-2, 12), (3, 12), (8, 12)],
    # Row 2: 3 pins
    [(-5, 17), (0, 17), (5, 17)],
    # Row 3: 2 pins
    [(-2, 22), (3, 22)],
    # Headpin
    [(0, 27)],
]

# Standard pin numbering (7-10 back, 4-6, 2-3, 1 headpin)
PIN_NUMBERS = [7, 8, 9, 10, 4, 5, 6, 2, 3, 1]

# Adjacency map for chain reactions (pin index -> list of adjacent pin indices)
PIN_ADJACENCY = {
    0: [1, 4],        # pin 7 -> 8, 4
    1: [0, 2, 4, 5],  # pin 8 -> 7, 9, 4, 5
    2: [1, 3, 5, 6],  # pin 9 -> 8, 10, 5, 6
    3: [2, 6],         # pin 10 -> 9, 6
    4: [0, 1, 7],      # pin 4 -> 7, 8, 2
    5: [1, 2, 7, 8],   # pin 5 -> 8, 9, 2, 3
    6: [2, 3, 8],      # pin 6 -> 9, 10, 3
    7: [4, 5, 9],      # pin 2 -> 4, 5, 1
    8: [5, 6, 9],      # pin 3 -> 5, 6, 1
    9: [7, 8],         # pin 1 -> 2, 3
}

PIN_COLOR = Colors.WHITE
PIN_DOWN_COLOR = (60, 40, 30)

# Sweep speeds
BASE_SWEEP_SPEED = 35.0
SWEEP_SPEED_PER_FRAME = 3.0

# Aim line
AIM_LINE_LENGTH = 25
MAX_AIM_ANGLE = math.pi / 3  # 60 degrees max deflection

# Timing
PIN_FALL_TIME = 0.6
SCORE_SHOW_TIME = 1.2
TURN_CHANGE_TIME = 0.5

# Frames
TOTAL_FRAMES = 10


def _build_pin_positions():
    """Build flat list of (x, y) pin positions."""
    cx = (LANE_LEFT + LANE_RIGHT) // 2  # lane center x
    positions = []
    for row in PIN_ROWS:
        for ox, py in row:
            positions.append((cx + ox, py))
    return positions


PIN_POSITIONS = _build_pin_positions()


class Bowling(Game):
    name = "BOWLING"
    description = "10-pin bowling with position and aim"
    category = "bar"

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.phase = PHASE_MODE_SELECT
        self.score = 0
        self.mode_select = 0  # 0 = 1P, 1 = 2P

        # Game state
        self.two_player = False
        self.current_player = 0
        self.current_frame = 0   # 0-indexed
        self.ball_in_frame = 0   # 0 = first ball, 1 = second, 2 = bonus (10th)

        # Scoring arrays: rolls[player][frame] = list of roll values
        self.rolls = [[[] for _ in range(TOTAL_FRAMES)] for _ in range(2)]
        self.frame_scores = [[None] * TOTAL_FRAMES for _ in range(2)]
        self.total_scores = [0, 0]

        # Pins: True = standing
        self.pins = [True] * 10

        # Position sweep
        self.sweep_pos = float((LANE_LEFT + LANE_RIGHT) // 2)
        self.sweep_dir = 1

        # Aim sweep
        self.aim_angle = 0.0  # radians from vertical (negative = left, positive = right)
        self.aim_dir = 1

        # Ball state
        self.ball_x = 0.0
        self.ball_y = 0.0
        self.ball_vx = 0.0
        self.ball_vy = 0.0
        self.ball_active = False

        # Pin fall animation
        self.pins_just_knocked = []
        self.phase_timer = 0.0

        # Score display
        self.last_knock_count = 0
        self.last_was_strike = False
        self.last_was_spare = False

    def _sweep_speed(self):
        return BASE_SWEEP_SPEED + SWEEP_SPEED_PER_FRAME * self.current_frame

    def _reset_pins(self):
        self.pins = [True] * 10

    def _standing_count(self):
        return sum(1 for p in self.pins if p)

    def _all_down(self):
        return self._standing_count() == 0

    def _start_position(self):
        self.phase = PHASE_POSITION
        self.sweep_pos = float((LANE_LEFT + LANE_RIGHT) // 2)
        self.sweep_dir = 1

    def _start_aim(self):
        self.phase = PHASE_AIM
        self.aim_angle = 0.0
        self.aim_dir = 1

    def _launch_ball(self):
        self.ball_x = self.sweep_pos
        self.ball_y = float(APPROACH_TOP)
        # Aim: angle from straight up
        self.ball_vx = math.sin(self.aim_angle) * BALL_SPEED
        self.ball_vy = -BALL_SPEED  # upward
        self.ball_active = True
        self.pins_just_knocked = []
        self.phase = PHASE_ROLLING

    def _check_pin_collisions(self):
        """Check ball against standing pins. Direct hits + chain reactions."""
        hit_pins = []
        for i, standing in enumerate(self.pins):
            if not standing:
                continue
            px, py = PIN_POSITIONS[i]
            dx = self.ball_x - px
            dy = self.ball_y - py
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < BALL_RADIUS + 1.5:  # pin radius ~1.5
                hit_pins.append(i)

        # Knock down direct hits
        for i in hit_pins:
            if self.pins[i]:
                self.pins[i] = False
                self.pins_just_knocked.append(i)

        # Chain reactions with diminishing probability per step
        chain_queue = [(pin_idx, 0) for pin_idx in hit_pins]
        while chain_queue:
            pin_idx, depth = chain_queue.pop(0)
            prob = 0.3 * (0.5 ** depth)
            for adj in PIN_ADJACENCY.get(pin_idx, []):
                if self.pins[adj] and random.random() < prob:
                    self.pins[adj] = False
                    self.pins_just_knocked.append(adj)
                    chain_queue.append((adj, depth + 1))

    def _ball_in_gutter(self):
        return self.ball_x < LANE_LEFT or self.ball_x > LANE_RIGHT

    def _ball_past_pins(self):
        return self.ball_y < PIN_DECK_TOP - 2

    def _record_roll(self, knocked):
        """Record a roll and handle frame advancement."""
        p = self.current_player
        f = self.current_frame
        self.rolls[p][f].append(knocked)

        self.last_knock_count = knocked
        self.last_was_strike = False
        self.last_was_spare = False

        if f < 9:
            # Frames 1-9
            if self.ball_in_frame == 0 and knocked == 10:
                # Strike
                self.last_was_strike = True
                self._advance_turn()
            elif self.ball_in_frame == 1:
                # Second ball
                first = self.rolls[p][f][0]
                if first + knocked == 10:
                    self.last_was_spare = True
                self._advance_turn()
            else:
                # First ball, not a strike
                self.ball_in_frame = 1
                self.phase = PHASE_SCORE_SHOW
                self.phase_timer = SCORE_SHOW_TIME
        else:
            # 10th frame special rules
            total_rolls = len(self.rolls[p][f])
            roll_sum = sum(self.rolls[p][f])

            if self.ball_in_frame == 0 and knocked == 10:
                self.last_was_strike = True

            if total_rolls == 1:
                if knocked == 10:
                    # Strike in 10th: reset pins, 2 more balls
                    self._reset_pins()
                    self.ball_in_frame = 1
                    self.phase = PHASE_SCORE_SHOW
                    self.phase_timer = SCORE_SHOW_TIME
                else:
                    self.ball_in_frame = 1
                    self.phase = PHASE_SCORE_SHOW
                    self.phase_timer = SCORE_SHOW_TIME
            elif total_rolls == 2:
                first = self.rolls[p][f][0]
                second = self.rolls[p][f][1]
                if first == 10:
                    # First was strike
                    if second == 10:
                        self.last_was_strike = True
                        self._reset_pins()
                    elif first + second >= 10:
                        self.last_was_spare = True
                        self._reset_pins()
                    self.ball_in_frame = 2
                    self.phase = PHASE_SCORE_SHOW
                    self.phase_timer = SCORE_SHOW_TIME
                elif first + second == 10:
                    # Spare
                    self.last_was_spare = True
                    self._reset_pins()
                    self.ball_in_frame = 2
                    self.phase = PHASE_SCORE_SHOW
                    self.phase_timer = SCORE_SHOW_TIME
                else:
                    # No mark, frame done
                    self._advance_turn()
            elif total_rolls >= 3:
                if knocked == 10:
                    self.last_was_strike = True
                self._advance_turn()

    def _advance_turn(self):
        """Move to next frame/player or game over."""
        self._calculate_scores()
        self.phase = PHASE_SCORE_SHOW
        self.phase_timer = SCORE_SHOW_TIME

        # After score show, we'll decide what to do in _after_score_show
        self._pending_advance = True

    def _after_score_show(self):
        """Called after score display timer expires."""
        if hasattr(self, '_pending_advance') and self._pending_advance:
            self._pending_advance = False

            if self.two_player:
                if self.current_player == 0:
                    self.current_player = 1
                    self.ball_in_frame = 0
                    self._reset_pins()
                    self.phase = PHASE_TURN_CHANGE
                    self.phase_timer = TURN_CHANGE_TIME
                else:
                    # Both players done this frame
                    self.current_frame += 1
                    self.current_player = 0
                    self.ball_in_frame = 0
                    self._reset_pins()
                    if self.current_frame >= TOTAL_FRAMES:
                        self.phase = PHASE_GAME_OVER_2P
                    else:
                        self.phase = PHASE_TURN_CHANGE
                        self.phase_timer = TURN_CHANGE_TIME
            else:
                self.current_frame += 1
                self.ball_in_frame = 0
                self._reset_pins()
                if self.current_frame >= TOTAL_FRAMES:
                    self.score = self.total_scores[0]
                    self.state = GameState.GAME_OVER
                else:
                    self._start_position()
        else:
            # Not advancing turn, just showing score between balls
            self._start_position()

    def _calculate_scores(self):
        """Calculate cumulative scores for all frames using standard bowling rules."""
        for p in range(2 if self.two_player else 1):
            # Flatten all rolls for this player
            all_rolls = []
            for f in range(TOTAL_FRAMES):
                all_rolls.extend(self.rolls[p][f])

            total = 0
            roll_idx = 0
            for f in range(TOTAL_FRAMES):
                if roll_idx >= len(all_rolls):
                    break

                if f < 9:
                    if all_rolls[roll_idx] == 10:
                        # Strike
                        bonus = 0
                        if roll_idx + 1 < len(all_rolls):
                            bonus += all_rolls[roll_idx + 1]
                        if roll_idx + 2 < len(all_rolls):
                            bonus += all_rolls[roll_idx + 2]
                        total += 10 + bonus
                        self.frame_scores[p][f] = total
                        roll_idx += 1
                    elif roll_idx + 1 < len(all_rolls):
                        first = all_rolls[roll_idx]
                        second = all_rolls[roll_idx + 1]
                        if first + second == 10:
                            # Spare
                            bonus = 0
                            if roll_idx + 2 < len(all_rolls):
                                bonus = all_rolls[roll_idx + 2]
                            total += 10 + bonus
                            self.frame_scores[p][f] = total
                        else:
                            total += first + second
                            self.frame_scores[p][f] = total
                        roll_idx += 2
                    else:
                        # Only first ball rolled so far
                        roll_idx += 1
                else:
                    # 10th frame: just sum all rolls (up to 3)
                    frame_rolls = self.rolls[p][f]
                    total += sum(frame_rolls)
                    self.frame_scores[p][f] = total
                    roll_idx += len(frame_rolls)

            self.total_scores[p] = total
            if p == 0 and not self.two_player:
                self.score = total

    # ==== UPDATE ====

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        if self.phase == PHASE_MODE_SELECT:
            self._update_mode_select(input_state)
        elif self.phase == PHASE_POSITION:
            self._update_position(input_state, dt)
        elif self.phase == PHASE_AIM:
            self._update_aim(input_state, dt)
        elif self.phase == PHASE_ROLLING:
            self._update_rolling(dt)
        elif self.phase == PHASE_PIN_FALL:
            self._update_pin_fall(dt)
        elif self.phase == PHASE_SCORE_SHOW:
            self._update_score_show(dt)
        elif self.phase == PHASE_TURN_CHANGE:
            self._update_turn_change(dt)
        elif self.phase == PHASE_GAME_OVER_2P:
            self._update_game_over_2p(input_state)

    def _update_mode_select(self, inp):
        if inp.up_pressed or inp.down_pressed:
            self.mode_select = 1 - self.mode_select
        if inp.action_l or inp.action_r:
            self.two_player = (self.mode_select == 1)
            self.rolls = [[[] for _ in range(TOTAL_FRAMES)] for _ in range(2)]
            self.frame_scores = [[None] * TOTAL_FRAMES for _ in range(2)]
            self.total_scores = [0, 0]
            self.current_player = 0
            self.current_frame = 0
            self.ball_in_frame = 0
            self.score = 0
            self._reset_pins()
            self._start_position()

    def _update_position(self, inp, dt):
        speed = self._sweep_speed()
        self.sweep_pos += self.sweep_dir * speed * dt

        if self.sweep_pos >= LANE_RIGHT:
            self.sweep_pos = LANE_RIGHT
            self.sweep_dir = -1
        elif self.sweep_pos <= LANE_LEFT:
            self.sweep_pos = LANE_LEFT
            self.sweep_dir = 1

        if inp.action_l or inp.action_r:
            self._start_aim()

    def _update_aim(self, inp, dt):
        # Joystick cancels back to position
        if inp.any_direction:
            self._start_position()
            return

        speed = self._sweep_speed() * 0.04  # radians/s
        self.aim_angle += self.aim_dir * speed * dt

        if self.aim_angle >= MAX_AIM_ANGLE:
            self.aim_angle = MAX_AIM_ANGLE
            self.aim_dir = -1
        elif self.aim_angle <= -MAX_AIM_ANGLE:
            self.aim_angle = -MAX_AIM_ANGLE
            self.aim_dir = 1

        if inp.action_l or inp.action_r:
            self._launch_ball()

    def _update_rolling(self, dt):
        # Move ball
        self.ball_x += self.ball_vx * dt
        self.ball_y += self.ball_vy * dt

        # Check gutter
        if self._ball_in_gutter():
            self.ball_active = False
            knocked = len(self.pins_just_knocked)
            self._record_roll(knocked)
            if self.phase == PHASE_ROLLING:
                self.phase = PHASE_PIN_FALL
                self.phase_timer = PIN_FALL_TIME
            return

        # Check pin collisions
        self._check_pin_collisions()

        # Ball past pin area
        if self._ball_past_pins():
            self.ball_active = False
            knocked = len(self.pins_just_knocked)
            self._record_roll(knocked)
            if self.phase == PHASE_ROLLING:
                self.phase = PHASE_PIN_FALL
                self.phase_timer = PIN_FALL_TIME

    def _update_pin_fall(self, dt):
        self.phase_timer -= dt
        if self.phase_timer <= 0:
            self._calculate_scores()
            knocked = len(self.pins_just_knocked)

            # Determine if we need another ball or advance
            p = self.current_player
            f = self.current_frame

            if f < 9:
                if self.ball_in_frame == 0 and self._all_down():
                    # Strike
                    self.last_was_strike = True
                    self.last_knock_count = knocked
                    self.phase = PHASE_SCORE_SHOW
                    self.phase_timer = SCORE_SHOW_TIME
                    self._pending_advance = True
                elif self.ball_in_frame == 1:
                    if self._all_down():
                        self.last_was_spare = True
                    self.last_knock_count = knocked
                    self.phase = PHASE_SCORE_SHOW
                    self.phase_timer = SCORE_SHOW_TIME
                    self._pending_advance = True
                else:
                    # First ball, pins remaining
                    self.last_knock_count = knocked
                    self.last_was_strike = False
                    self.last_was_spare = False
                    self.ball_in_frame = 1
                    self.phase = PHASE_SCORE_SHOW
                    self.phase_timer = SCORE_SHOW_TIME
                    self._pending_advance = False
            else:
                # 10th frame
                total_rolls = len(self.rolls[p][f])
                self.last_knock_count = knocked

                if total_rolls == 1:
                    if self._all_down():
                        self.last_was_strike = True
                        self._reset_pins()
                    self.ball_in_frame = 1
                    self.phase = PHASE_SCORE_SHOW
                    self.phase_timer = SCORE_SHOW_TIME
                    self._pending_advance = False
                elif total_rolls == 2:
                    first = self.rolls[p][f][0]
                    second = self.rolls[p][f][1]
                    if first == 10:
                        if second == 10:
                            self.last_was_strike = True
                            self._reset_pins()
                        elif self._all_down():
                            self.last_was_spare = True
                            self._reset_pins()
                        self.ball_in_frame = 2
                        self.phase = PHASE_SCORE_SHOW
                        self.phase_timer = SCORE_SHOW_TIME
                        self._pending_advance = False
                    elif first + second == 10:
                        self.last_was_spare = True
                        self._reset_pins()
                        self.ball_in_frame = 2
                        self.phase = PHASE_SCORE_SHOW
                        self.phase_timer = SCORE_SHOW_TIME
                        self._pending_advance = False
                    else:
                        # No mark, done
                        self.phase = PHASE_SCORE_SHOW
                        self.phase_timer = SCORE_SHOW_TIME
                        self._pending_advance = True
                elif total_rolls >= 3:
                    if self._all_down():
                        self.last_was_strike = True
                    self.phase = PHASE_SCORE_SHOW
                    self.phase_timer = SCORE_SHOW_TIME
                    self._pending_advance = True

    def _update_score_show(self, dt):
        self.phase_timer -= dt
        if self.phase_timer <= 0:
            self._after_score_show()

    def _update_turn_change(self, dt):
        self.phase_timer -= dt
        if self.phase_timer <= 0:
            self._start_position()

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

        # Draw lane
        self._draw_lane()

        # Draw pins
        self._draw_pins()

        # Draw ball if active
        if self.ball_active:
            self._draw_ball()

        # Draw HUD
        self._draw_hud()

        # Phase overlays
        if self.phase == PHASE_POSITION:
            self._draw_position_marker()
        elif self.phase == PHASE_AIM:
            self._draw_aim_line()
        elif self.phase == PHASE_SCORE_SHOW:
            self._draw_score_show()
        elif self.phase == PHASE_TURN_CHANGE:
            self._draw_turn_change()

    def _draw_mode_select(self):
        self.display.draw_text_small(6, 10, "BOWLING", Colors.WHITE)

        # Simple pin triangle icon
        cx = 31
        self.display.set_pixel(cx, 24, Colors.WHITE)
        self.display.set_pixel(cx - 2, 27, Colors.WHITE)
        self.display.set_pixel(cx + 2, 27, Colors.WHITE)
        self.display.set_pixel(cx - 4, 30, Colors.WHITE)
        self.display.set_pixel(cx, 30, Colors.WHITE)
        self.display.set_pixel(cx + 4, 30, Colors.WHITE)

        y1 = 44
        if self.mode_select == 0:
            self.display.draw_text_small(2, y1, ">1 PLAYER", Colors.YELLOW)
            self.display.draw_text_small(2, y1 + 10, " 2 PLAYERS", Colors.GRAY)
        else:
            self.display.draw_text_small(2, y1, " 1 PLAYER", Colors.GRAY)
            self.display.draw_text_small(2, y1 + 10, ">2 PLAYERS", Colors.YELLOW)

    def _draw_lane(self):
        # Gutters
        for y in range(PIN_DECK_TOP, APPROACH_BOTTOM + 1):
            self.display.set_pixel(LANE_LEFT - 1, y, GUTTER_COLOR)
            self.display.set_pixel(LANE_LEFT - 2, y, GUTTER_COLOR)
            self.display.set_pixel(LANE_RIGHT + 1, y, GUTTER_COLOR)
            self.display.set_pixel(LANE_RIGHT + 2, y, GUTTER_COLOR)

        # Lane surface
        for y in range(PIN_DECK_TOP, APPROACH_BOTTOM + 1):
            for x in range(LANE_LEFT, LANE_RIGHT + 1):
                self.display.set_pixel(x, y, LANE_COLOR)

        # Foul line
        for x in range(LANE_LEFT, LANE_RIGHT + 1):
            self.display.set_pixel(x, FOUL_LINE_Y, Colors.RED)

        # Approach arrows (guide dots)
        cx = (LANE_LEFT + LANE_RIGHT) // 2
        for offset in [-6, -3, 0, 3, 6]:
            self.display.set_pixel(cx + offset, 44, (100, 80, 40))

    def _draw_pins(self):
        for i, standing in enumerate(self.pins):
            px, py = PIN_POSITIONS[i]
            if standing:
                # Standing pin: bright white dot
                self.display.set_pixel(px, py, PIN_COLOR)
                self.display.set_pixel(px - 1, py, (180, 180, 180))
                self.display.set_pixel(px + 1, py, (180, 180, 180))
                self.display.set_pixel(px, py - 1, (180, 180, 180))
                self.display.set_pixel(px, py + 1, (180, 180, 180))
            else:
                # Down pin: dim dot
                self.display.set_pixel(px, py, PIN_DOWN_COLOR)

    def _draw_ball(self):
        bx = int(round(self.ball_x))
        by = int(round(self.ball_y))
        self.display.set_pixel(bx, by, BALL_COLOR)
        self.display.set_pixel(bx - 1, by, (150, 150, 160))
        self.display.set_pixel(bx + 1, by, (150, 150, 160))
        self.display.set_pixel(bx, by - 1, (150, 150, 160))
        self.display.set_pixel(bx, by + 1, (150, 150, 160))

    def _draw_hud(self):
        # Dark background for HUD
        self.display.draw_rect(0, HUD_TOP, 64, HUD_BOTTOM + 1, Colors.BLACK)

        if self.two_player:
            p1_c = Colors.YELLOW if self.current_player == 0 else Colors.GRAY
            p2_c = Colors.YELLOW if self.current_player == 1 else Colors.GRAY
            self.display.draw_text_small(2, 1, f"P1:{self.total_scores[0]}", p1_c)
            self.display.draw_text_small(34, 1, f"P2:{self.total_scores[1]}", p2_c)
        else:
            self.display.draw_text_small(2, 1, f"{self.total_scores[0]}", Colors.WHITE)

        # Frame number
        frame_num = min(self.current_frame + 1, TOTAL_FRAMES)
        self.display.draw_text_small(42, 1, f"F{frame_num}", Colors.CYAN)

        # Pin indicator (small dots showing standing pins)
        # Show 10 dots in a row for standing pins
        for i in range(10):
            px = 2 + i * 3
            if self.pins[i]:
                self.display.set_pixel(px, 7, Colors.WHITE)
            else:
                self.display.set_pixel(px, 7, (40, 40, 40))

    def _draw_position_marker(self):
        """Draw sweeping position marker in approach area."""
        sx = int(round(self.sweep_pos))
        # Vertical marker in approach zone
        for y in range(APPROACH_TOP, APPROACH_BOTTOM + 1):
            self.display.set_pixel(sx, y, Colors.CYAN)
        # Arrow pointing up
        self.display.set_pixel(sx - 1, APPROACH_TOP + 1, Colors.CYAN)
        self.display.set_pixel(sx + 1, APPROACH_TOP + 1, Colors.CYAN)

    def _draw_aim_line(self):
        """Draw aim direction line from position."""
        sx = int(round(self.sweep_pos))
        start_y = APPROACH_TOP

        # Draw dotted line in aim direction
        dx = math.sin(self.aim_angle)
        dy = -1.0  # upward
        length = math.sqrt(dx * dx + dy * dy)
        dx /= length
        dy /= length

        for i in range(1, AIM_LINE_LENGTH):
            lx = sx + dx * i
            ly = start_y + dy * i
            ix = int(round(lx))
            iy = int(round(ly))
            if iy < PIN_DECK_TOP:
                break
            if i % 3 != 0:
                self.display.set_pixel(ix, iy, Colors.YELLOW)

        # Still show position marker dimly
        for y in range(APPROACH_TOP, APPROACH_BOTTOM + 1):
            self.display.set_pixel(sx, y, (0, 100, 100))

    def _draw_score_show(self):
        """Show result of last roll."""
        if self.last_was_strike:
            text = "STRIKE!"
            color = Colors.YELLOW
        elif self.last_was_spare:
            text = "SPARE!"
            color = Colors.GREEN
        elif self.last_knock_count > 0:
            text = f"-{self.last_knock_count} PINS"
            color = Colors.WHITE
        else:
            text = "GUTTER"
            color = Colors.RED

        tw = len(text) * 4
        tx = max(2, (64 - tw) // 2)
        self.display.draw_rect(tx - 1, 32, tw + 2, 7, Colors.BLACK)
        self.display.draw_text_small(tx, 33, text, color)

    def _draw_turn_change(self):
        p = self.current_player + 1
        self.display.draw_rect(8, 32, 48, 9, Colors.BLACK)
        self.display.draw_text_small(14, 34, f"P{p} TURN", Colors.CYAN)

    def _draw_game_over_2p(self):
        self.display.clear(Colors.BLACK)
        if self.total_scores[0] > self.total_scores[1]:
            winner = "P1 WINS!"
            color = Colors.YELLOW
        elif self.total_scores[1] > self.total_scores[0]:
            winner = "P2 WINS!"
            color = Colors.YELLOW
        else:
            winner = "TIE GAME"
            color = Colors.CYAN

        self.display.draw_text_small(10, 12, winner, color)
        self.display.draw_text_small(2, 26, f"P1:{self.total_scores[0]}", Colors.WHITE)
        self.display.draw_text_small(2, 36, f"P2:{self.total_scores[1]}", Colors.WHITE)
        self.display.draw_text_small(2, 52, "BTN:AGAIN", Colors.GRAY)
