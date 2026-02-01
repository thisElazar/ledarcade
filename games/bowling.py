"""
Bowling - LED Arcade
====================
10-pin bowling with top-down lane view on a 64x64 LED matrix.
Three-step throw mechanic: position marker, aim direction, then power/spin.
Physics-based pin simulation with elastic collisions.
1P score attack (10 frames) and 2P alternating (highest score wins).

Controls:
  Space      - Lock position / confirm aim / confirm power / navigate
  Joystick   - Cancel aim→position / cancel power→aim / navigate
"""

import math
from arcade import Game, GameState, Display, Colors, InputState

# Phases
PHASE_MODE_SELECT = 0
PHASE_POSITION = 1
PHASE_AIM = 2
PHASE_POWER = 3
PHASE_ROLLING = 4
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
BALL_RADIUS = 1.5  # collision radius

# Pin layout: 10-pin triangle, back row at y=12, headpin at y=26
PIN_ROWS = [
    [(-7, 12), (-2, 12), (3, 12), (8, 12)],
    [(-5, 17), (0, 17), (5, 17)],
    [(-2, 22), (3, 22)],
    [(0, 27)],
]

PIN_NUMBERS = [7, 8, 9, 10, 4, 5, 6, 2, 3, 1]

PIN_COLOR = Colors.WHITE
PIN_DOWN_COLOR = (60, 40, 30)

# Sweep speeds
BASE_SWEEP_SPEED = 35.0
SWEEP_SPEED_PER_FRAME = 3.0

# Aim line
AIM_LINE_LENGTH = 25
MAX_AIM_ANGLE = math.pi / 3  # 60 degrees max deflection

# Power / Spin
BASE_POWER_SPEED = 1.5
POWER_SPEED_PER_FRAME = 0.08
MAX_BALL_SPEED = 80.0
MIN_BALL_SPEED = 48.0
SPIN_LATERAL_ACCEL = 30.0  # px/s^2 at max spin

# Pin physics
PIN_RADIUS = 1.5
PIN_COLLISION_DIST = 3.0
BALL_PIN_COLLISION_DIST = 3.0
PIN_FRICTION = 40.0         # px/s^2 deceleration
BALL_FRICTION = 5.0
PIN_RESTITUTION = 0.8
BALL_PIN_RESTITUTION = 0.85
PIN_KNOCKED_DIST = 2.5      # displacement threshold
MIN_SPEED = 2.0
SUBSTEPS = 3

# Mass ratio (ball is heavier)
BALL_MASS = 3.0
PIN_MASS = 1.0

# Lane boundaries for pin physics
LANE_WALL_LEFT = LANE_LEFT + 0.5
LANE_WALL_RIGHT = LANE_RIGHT - 0.5
PIN_AREA_TOP = PIN_DECK_TOP - 2.0
PIN_AREA_BOTTOM = FOUL_LINE_Y

# Timing
SCORE_SHOW_TIME = 1.2
TURN_CHANGE_TIME = 0.5

# Frames
TOTAL_FRAMES = 10


def _build_pin_positions():
    """Build flat list of (x, y) pin positions."""
    cx = (LANE_LEFT + LANE_RIGHT) // 2
    positions = []
    for row in PIN_ROWS:
        for ox, py in row:
            positions.append((cx + ox, py))
    return positions


PIN_POSITIONS = _build_pin_positions()


class Pin:
    __slots__ = ['x', 'y', 'vx', 'vy', 'home_x', 'home_y', 'knocked', 'active']

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.home_x = float(x)
        self.home_y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.knocked = False
        self.active = True

    def speed(self):
        return math.sqrt(self.vx * self.vx + self.vy * self.vy)

    def moving(self):
        return self.speed() > MIN_SPEED

    def displacement(self):
        dx = self.x - self.home_x
        dy = self.y - self.home_y
        return math.sqrt(dx * dx + dy * dy)


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
        self.current_frame = 0
        self.ball_in_frame = 0

        # Scoring arrays
        self.rolls = [[[] for _ in range(TOTAL_FRAMES)] for _ in range(2)]
        self.frame_scores = [[None] * TOTAL_FRAMES for _ in range(2)]
        self.total_scores = [0, 0]

        # Pins
        self.pins = self._create_pins()
        self.pins_before_roll = 10

        # Position sweep
        self.sweep_pos = float((LANE_LEFT + LANE_RIGHT) // 2)
        self.sweep_dir = 1

        # Aim sweep
        self.aim_angle = 0.0
        self.aim_dir = 1

        # Power/spin
        self.power_pos = 0.0
        self.power_dir = 1
        self.power_value = 1.0
        self.spin_value = 0.0

        # Ball state
        self.ball_x = 0.0
        self.ball_y = 0.0
        self.ball_vx = 0.0
        self.ball_vy = 0.0
        self.ball_active = False

        # Phase timer
        self.phase_timer = 0.0

        # Score display
        self.last_knock_count = 0
        self.last_was_strike = False
        self.last_was_spare = False

        self._pending_advance = False

    def _create_pins(self):
        pins = []
        for i in range(10):
            px, py = PIN_POSITIONS[i]
            pins.append(Pin(px, py))
        return pins

    def _sweep_speed(self):
        return BASE_SWEEP_SPEED + SWEEP_SPEED_PER_FRAME * self.current_frame

    def _power_speed(self):
        return BASE_POWER_SPEED + POWER_SPEED_PER_FRAME * self.current_frame

    def _reset_pins(self):
        self.pins = self._create_pins()
        self.pins_before_roll = 10

    def _standing_count(self):
        return sum(1 for p in self.pins if not p.knocked and p.active)

    def _all_down(self):
        return self._standing_count() == 0

    def _any_pin_moving(self):
        return any(p.moving() for p in self.pins if p.active)

    def _all_stopped(self):
        if self.ball_active:
            bspd = math.sqrt(self.ball_vx ** 2 + self.ball_vy ** 2)
            if bspd > MIN_SPEED:
                return False
        return not self._any_pin_moving()

    def _start_position(self):
        self.phase = PHASE_POSITION
        self.sweep_pos = float((LANE_LEFT + LANE_RIGHT) // 2)
        self.sweep_dir = 1

    def _start_aim(self):
        self.phase = PHASE_AIM
        self.aim_angle = 0.0
        self.aim_dir = 1

    def _start_power(self):
        self.phase = PHASE_POWER
        self.power_pos = 0.0
        self.power_dir = 1

    def _launch_ball(self):
        self.ball_x = self.sweep_pos
        self.ball_y = float(APPROACH_TOP)
        ball_speed = MIN_BALL_SPEED + (MAX_BALL_SPEED - MIN_BALL_SPEED) * self.power_value
        self.ball_vx = math.sin(self.aim_angle) * ball_speed
        self.ball_vy = -ball_speed  # upward
        self.ball_active = True
        self.pins_before_roll = self._standing_count()
        self.phase = PHASE_ROLLING

    def _evaluate_knocked_pins(self):
        """Mark pins as knocked based on displacement from home position."""
        for pin in self.pins:
            if not pin.active:
                pin.knocked = True
            elif pin.displacement() >= PIN_KNOCKED_DIST:
                pin.knocked = True

    # ==== PHYSICS ====

    def _physics_step(self, dt):
        """One substep of physics for ball and all pins."""

        # --- Move ball ---
        if self.ball_active:
            # Spin curves the ball laterally
            self.ball_vx += self.spin_value * SPIN_LATERAL_ACCEL * dt

            self.ball_x += self.ball_vx * dt
            self.ball_y += self.ball_vy * dt

            # Ball friction (gentle)
            bspd = math.sqrt(self.ball_vx ** 2 + self.ball_vy ** 2)
            if bspd > 0:
                decel = BALL_FRICTION * dt
                new_spd = max(0, bspd - decel)
                factor = new_spd / bspd
                self.ball_vx *= factor
                self.ball_vy *= factor

            # Ball in gutter
            if self.ball_x < LANE_LEFT or self.ball_x > LANE_RIGHT:
                self.ball_active = False
                self.ball_vx = 0.0
                self.ball_vy = 0.0

            # Ball past pin deck
            if self.ball_y < PIN_DECK_TOP - 4:
                self.ball_active = False
                self.ball_vx = 0.0
                self.ball_vy = 0.0

        # --- Move pins ---
        for pin in self.pins:
            if not pin.active or not pin.moving():
                continue

            pin.x += pin.vx * dt
            pin.y += pin.vy * dt

            # Pin friction
            spd = pin.speed()
            if spd > 0:
                decel = PIN_FRICTION * dt
                new_spd = max(0, spd - decel)
                factor = new_spd / spd
                pin.vx *= factor
                pin.vy *= factor
                if new_spd < MIN_SPEED:
                    pin.vx = 0.0
                    pin.vy = 0.0

            # Pin off lane -> deactivate
            if (pin.x < LANE_WALL_LEFT or pin.x > LANE_WALL_RIGHT or
                    pin.y < PIN_AREA_TOP or pin.y > PIN_AREA_BOTTOM):
                pin.active = False
                pin.knocked = True
                pin.vx = 0.0
                pin.vy = 0.0

        # --- Ball-to-pin collisions (unequal mass) ---
        if self.ball_active:
            for pin in self.pins:
                if not pin.active:
                    continue
                dx = pin.x - self.ball_x
                dy = pin.y - self.ball_y
                dist_sq = dx * dx + dy * dy
                min_dist = BALL_PIN_COLLISION_DIST
                if dist_sq < min_dist * min_dist and dist_sq > 0:
                    dist = math.sqrt(dist_sq)
                    nx = dx / dist
                    ny = dy / dist

                    # Separate overlap
                    overlap = min_dist - dist
                    total_mass = BALL_MASS + PIN_MASS
                    self.ball_x -= nx * overlap * (PIN_MASS / total_mass)
                    self.ball_y -= ny * overlap * (PIN_MASS / total_mass)
                    pin.x += nx * overlap * (BALL_MASS / total_mass)
                    pin.y += ny * overlap * (BALL_MASS / total_mass)

                    # Impulse
                    rel_vx = pin.vx - self.ball_vx
                    rel_vy = pin.vy - self.ball_vy
                    rel_vn = rel_vx * nx + rel_vy * ny

                    if rel_vn < 0:  # approaching
                        j = -(1 + BALL_PIN_RESTITUTION) * rel_vn / (1 / BALL_MASS + 1 / PIN_MASS)
                        self.ball_vx -= (j / BALL_MASS) * nx
                        self.ball_vy -= (j / BALL_MASS) * ny
                        pin.vx += (j / PIN_MASS) * nx
                        pin.vy += (j / PIN_MASS) * ny

        # --- Pin-to-pin collisions (equal mass) ---
        active_pins = [p for p in self.pins if p.active]
        for i in range(len(active_pins)):
            for j in range(i + 1, len(active_pins)):
                a = active_pins[i]
                b = active_pins[j]
                dx = b.x - a.x
                dy = b.y - a.y
                dist_sq = dx * dx + dy * dy
                min_dist = PIN_COLLISION_DIST
                if dist_sq < min_dist * min_dist and dist_sq > 0:
                    dist = math.sqrt(dist_sq)
                    nx = dx / dist
                    ny = dy / dist

                    # Separate overlap
                    overlap = min_dist - dist
                    a.x -= nx * overlap * 0.5
                    a.y -= ny * overlap * 0.5
                    b.x += nx * overlap * 0.5
                    b.y += ny * overlap * 0.5

                    # Elastic collision
                    rel_vn = (b.vx - a.vx) * nx + (b.vy - a.vy) * ny
                    if rel_vn < 0:
                        a.vx += rel_vn * nx * PIN_RESTITUTION
                        a.vy += rel_vn * ny * PIN_RESTITUTION
                        b.vx -= rel_vn * nx * PIN_RESTITUTION
                        b.vy -= rel_vn * ny * PIN_RESTITUTION

    # ==== SCORING ====

    def _record_roll(self, knocked):
        """Record a roll and handle frame advancement."""
        p = self.current_player
        f = self.current_frame
        self.rolls[p][f].append(knocked)

        self.last_knock_count = knocked
        self.last_was_strike = False
        self.last_was_spare = False

        if f < 9:
            if self.ball_in_frame == 0 and knocked == 10:
                self.last_was_strike = True
                self._advance_turn()
            elif self.ball_in_frame == 1:
                first = self.rolls[p][f][0]
                if first + knocked == 10:
                    self.last_was_spare = True
                self._advance_turn()
            else:
                self.ball_in_frame = 1
                self.phase = PHASE_SCORE_SHOW
                self.phase_timer = SCORE_SHOW_TIME
        else:
            # 10th frame special rules
            total_rolls = len(self.rolls[p][f])

            if self.ball_in_frame == 0 and knocked == 10:
                self.last_was_strike = True

            if total_rolls == 1:
                if knocked == 10:
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
                    self.last_was_spare = True
                    self._reset_pins()
                    self.ball_in_frame = 2
                    self.phase = PHASE_SCORE_SHOW
                    self.phase_timer = SCORE_SHOW_TIME
                else:
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
        self._pending_advance = True

    def _after_score_show(self):
        """Called after score display timer expires."""
        if self._pending_advance:
            self._pending_advance = False

            if self.two_player:
                if self.current_player == 0:
                    self.current_player = 1
                    self.ball_in_frame = 0
                    self._reset_pins()
                    self.phase = PHASE_TURN_CHANGE
                    self.phase_timer = TURN_CHANGE_TIME
                else:
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
        """Calculate cumulative scores using standard bowling rules."""
        for p in range(2 if self.two_player else 1):
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
                        roll_idx += 1
                else:
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
        elif self.phase == PHASE_POWER:
            self._update_power(input_state, dt)
        elif self.phase == PHASE_ROLLING:
            self._update_rolling(dt)
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
        if inp.any_direction:
            self._start_position()
            return

        speed = self._sweep_speed() * 0.04
        self.aim_angle += self.aim_dir * speed * dt

        if self.aim_angle >= MAX_AIM_ANGLE:
            self.aim_angle = MAX_AIM_ANGLE
            self.aim_dir = -1
        elif self.aim_angle <= -MAX_AIM_ANGLE:
            self.aim_angle = -MAX_AIM_ANGLE
            self.aim_dir = 1

        if inp.action_l or inp.action_r:
            self._start_power()

    def _update_power(self, inp, dt):
        if inp.any_direction:
            self._start_aim()
            return

        speed = self._power_speed()
        self.power_pos += self.power_dir * speed * dt
        if self.power_pos >= 1.0:
            self.power_pos = 1.0
            self.power_dir = -1
        elif self.power_pos <= 0.0:
            self.power_pos = 0.0
            self.power_dir = 1

        if inp.action_l or inp.action_r:
            center_dist = abs(self.power_pos - 0.5) * 2.0
            self.power_value = 0.6 + 0.4 * (1.0 - center_dist)
            self.spin_value = (self.power_pos - 0.5) * 2.0
            self._launch_ball()

    def _update_rolling(self, dt):
        sub_dt = dt / SUBSTEPS
        for _ in range(SUBSTEPS):
            self._physics_step(sub_dt)

        if self._all_stopped():
            self._evaluate_knocked_pins()
            knocked = self.pins_before_roll - self._standing_count()
            self._record_roll(knocked)
            if self.phase == PHASE_ROLLING:
                self._calculate_scores()
                self.phase = PHASE_SCORE_SHOW
                self.phase_timer = SCORE_SHOW_TIME

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
        elif self.phase == PHASE_POWER:
            self._draw_aim_line()
            self._draw_power_bar()
        elif self.phase == PHASE_SCORE_SHOW:
            self._draw_score_show()
        elif self.phase == PHASE_TURN_CHANGE:
            self._draw_turn_change()

    def _draw_mode_select(self):
        self.display.draw_text_small(6, 10, "BOWLING", Colors.WHITE)

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
        for pin in self.pins:
            if not pin.active:
                continue

            px = int(round(pin.x))
            py = int(round(pin.y))

            if pin.knocked:
                self.display.set_pixel(px, py, PIN_DOWN_COLOR)
            elif pin.moving():
                self.display.set_pixel(px, py, (220, 220, 220))
                self.display.set_pixel(px - 1, py, (140, 140, 140))
                self.display.set_pixel(px + 1, py, (140, 140, 140))
                self.display.set_pixel(px, py - 1, (140, 140, 140))
                self.display.set_pixel(px, py + 1, (140, 140, 140))
            else:
                self.display.set_pixel(px, py, PIN_COLOR)
                self.display.set_pixel(px - 1, py, (180, 180, 180))
                self.display.set_pixel(px + 1, py, (180, 180, 180))
                self.display.set_pixel(px, py - 1, (180, 180, 180))
                self.display.set_pixel(px, py + 1, (180, 180, 180))

    def _draw_ball(self):
        bx = int(round(self.ball_x))
        by = int(round(self.ball_y))
        self.display.set_pixel(bx, by, BALL_COLOR)
        self.display.set_pixel(bx - 1, by, (150, 150, 160))
        self.display.set_pixel(bx + 1, by, (150, 150, 160))
        self.display.set_pixel(bx, by - 1, (150, 150, 160))
        self.display.set_pixel(bx, by + 1, (150, 150, 160))

    def _draw_hud(self):
        self.display.draw_rect(0, HUD_TOP, 64, HUD_BOTTOM + 1, Colors.BLACK)

        if self.two_player:
            p1_c = Colors.YELLOW if self.current_player == 0 else Colors.GRAY
            p2_c = Colors.YELLOW if self.current_player == 1 else Colors.GRAY
            self.display.draw_text_small(2, 1, f"P1:{self.total_scores[0]}", p1_c)
            self.display.draw_text_small(34, 1, f"P2:{self.total_scores[1]}", p2_c)
        else:
            self.display.draw_text_small(2, 1, f"{self.total_scores[0]}", Colors.WHITE)

        frame_num = min(self.current_frame + 1, TOTAL_FRAMES)
        self.display.draw_text_small(42, 1, f"F{frame_num}", Colors.CYAN)

        # Pin indicator dots
        for i in range(10):
            hx = 2 + i * 3
            pin = self.pins[i]
            if not pin.knocked and pin.active:
                self.display.set_pixel(hx, 7, Colors.WHITE)
            else:
                self.display.set_pixel(hx, 7, (40, 40, 40))

    def _draw_position_marker(self):
        sx = int(round(self.sweep_pos))
        for y in range(APPROACH_TOP, APPROACH_BOTTOM + 1):
            self.display.set_pixel(sx, y, Colors.CYAN)
        self.display.set_pixel(sx - 1, APPROACH_TOP + 1, Colors.CYAN)
        self.display.set_pixel(sx + 1, APPROACH_TOP + 1, Colors.CYAN)

    def _draw_aim_line(self):
        sx = int(round(self.sweep_pos))
        start_y = APPROACH_TOP

        dx = math.sin(self.aim_angle)
        dy = -1.0
        length = math.sqrt(dx * dx + dy * dy)
        dx /= length
        dy /= length

        dim = self.phase == PHASE_POWER
        for i in range(1, AIM_LINE_LENGTH):
            lx = sx + dx * i
            ly = start_y + dy * i
            ix = int(round(lx))
            iy = int(round(ly))
            if iy < PIN_DECK_TOP:
                break
            if i % 3 != 0:
                color = (0, 100, 100) if dim else Colors.YELLOW
                self.display.set_pixel(ix, iy, color)

        for y in range(APPROACH_TOP, APPROACH_BOTTOM + 1):
            self.display.set_pixel(sx, y, (0, 100, 100))

    def _draw_power_bar(self):
        """Draw power/spin bar: green at center, red at edges."""
        bar_y = APPROACH_BOTTOM + 2
        bar_x = LANE_LEFT
        bar_w = LANE_RIGHT - LANE_LEFT + 1

        # Dim gradient background
        for x in range(bar_w):
            frac = x / max(bar_w - 1, 1)
            center_dist = abs(frac - 0.5) * 2.0
            r = int(80 * center_dist)
            g = int(80 * (1.0 - center_dist))
            self.display.set_pixel(bar_x + x, bar_y, (r, g, 0))
            self.display.set_pixel(bar_x + x, bar_y + 1, (r, g, 0))

        # Bright marker
        marker_x = bar_x + int(self.power_pos * (bar_w - 1))
        center_dist = abs(self.power_pos - 0.5) * 2.0
        r = int(255 * center_dist)
        g = int(255 * (1.0 - center_dist))
        marker_color = (r, g, 0)

        for dx in range(-1, 2):
            mx = marker_x + dx
            if bar_x <= mx < bar_x + bar_w:
                self.display.set_pixel(mx, bar_y, marker_color)
                self.display.set_pixel(mx, bar_y + 1, marker_color)

    def _draw_score_show(self):
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
