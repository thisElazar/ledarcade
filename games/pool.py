"""
Pool - LED Arcade
=================
Hybrid of Video Hustler scoring + Side Pocket controls.
1P score attack or 2P alternating turns on a 64x64 LED table.

Controls:
  Left/Right - Aim cue ball direction
  Up/Down    - Fine/coarse aim adjustment
  Space      - Start power bar / fire shot
"""

import math
import random
from arcade import Game, GameState, Display, Colors, InputState

# Phases (internal, all under GameState.PLAYING)
PHASE_MODE_SELECT = 0
PHASE_AIMING = 1
PHASE_POWER = 2
PHASE_SHOOTING = 3
PHASE_SCORING = 4
PHASE_FOUL = 5
PHASE_TURN_CHANGE = 6
PHASE_GAME_OVER_2P = 7

# Table geometry
TABLE_LEFT = 2
TABLE_RIGHT = 61
TABLE_TOP = 10
TABLE_BOTTOM = 61
TABLE_BORDER = 2
FELT_COLOR = (0, 100, 0)
BORDER_COLOR = (120, 70, 20)
POCKET_COLOR = (30, 30, 30)

# Ball properties
BALL_RADIUS = 1  # center + cardinal pixels = 3px cross
CUE_BREAK_X = 16.0
CUE_BREAK_Y = 36.0
RACK_X = 46.0
RACK_Y = 36.0

# Physics
FRICTION = 30.0        # px/s^2 deceleration
CUSHION_RESTITUTION = 0.85
SUBSTEPS = 3
POCKET_RADIUS = 3.0
BALL_COLLISION_DIST = 3.0  # diameter for collision detection
MIN_SPEED = 3.0        # below this, ball stops
MAX_POWER = 120.0

# Scoring
BALL_VALUES = {1: 10, 2: 20, 3: 30, 4: 40, 5: 50, 6: 60}
CLEAR_BONUS = 200

# Ball colors
BALL_COLORS = {
    0: Colors.WHITE,           # cue ball
    1: Colors.YELLOW,
    2: (50, 80, 255),          # blue
    3: Colors.RED,
    4: (160, 50, 200),         # purple
    5: Colors.ORANGE,
    6: (0, 200, 50),           # green
}

# Pocket positions and multipliers
# (x, y, multiplier)
POCKETS = [
    (TABLE_LEFT, TABLE_TOP, 1),          # top-left corner
    (TABLE_RIGHT, TABLE_TOP, 1),         # top-right corner
    (TABLE_LEFT, TABLE_BOTTOM, 1),       # bottom-left corner
    (TABLE_RIGHT, TABLE_BOTTOM, 1),      # bottom-right corner
    ((TABLE_LEFT + TABLE_RIGHT) // 2, TABLE_TOP, 2),     # top side
    ((TABLE_LEFT + TABLE_RIGHT) // 2, TABLE_BOTTOM, 2),  # bottom side
]


class Ball:
    __slots__ = ['num', 'x', 'y', 'vx', 'vy', 'active']

    def __init__(self, num, x, y):
        self.num = num
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.active = True

    def speed(self):
        return math.sqrt(self.vx * self.vx + self.vy * self.vy)

    def moving(self):
        return self.speed() > MIN_SPEED


class Pool(Game):
    name = "POOL"
    description = "Billiards with Video Hustler scoring"
    category = "bar"

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.phase = PHASE_MODE_SELECT
        self.score = 0
        self.mode_select = 0  # 0 = 1P, 1 = 2P

        # 1P state
        self.shots_left = 10

        # 2P state
        self.current_player = 0  # 0 or 1
        self.scores = [0, 0]
        self.two_player = False

        # Aiming
        self.aim_angle = 0.0  # radians, 0 = right

        # Power
        self.power = 0.0
        self.power_dir = 1  # oscillation direction
        self.power_speed = 1.8  # oscillations per second

        # Scoring display
        self.phase_timer = 0.0
        self.points_earned = 0
        self.pocketed_this_shot = []

        # Create balls
        self.balls = []
        self._setup_balls()

    def _setup_balls(self):
        self.balls = []
        # Cue ball
        self.balls.append(Ball(0, CUE_BREAK_X, CUE_BREAK_Y))
        # Rack: triangle on right side (1 front, 2 mid, 3 back)
        spacing = 3.5
        rows = [
            [1],
            [2, 3],
            [4, 5, 6],
        ]
        for row_i, row in enumerate(rows):
            rx = RACK_X + row_i * spacing
            row_height = (len(row) - 1) * spacing
            for ball_i, ball_num in enumerate(row):
                ry = RACK_Y - row_height / 2 + ball_i * spacing
                self.balls.append(Ball(ball_num, rx, ry))

    def _cue_ball(self):
        for b in self.balls:
            if b.num == 0 and b.active:
                return b
        return None

    def _object_balls(self):
        return [b for b in self.balls if b.num > 0 and b.active]

    def _any_moving(self):
        return any(b.moving() for b in self.balls if b.active)

    def _near_pocket(self, x, y):
        """Check if position is near any pocket (for wall collision exemption)."""
        for px, py, _ in POCKETS:
            dx = x - px
            dy = y - py
            if dx * dx + dy * dy < (POCKET_RADIUS + 1) ** 2:
                return True
        return False

    def _check_pocket(self, ball):
        """Check if ball fell into a pocket. Returns (pocketed, multiplier)."""
        for px, py, mult in POCKETS:
            dx = ball.x - px
            dy = ball.y - py
            if dx * dx + dy * dy < POCKET_RADIUS * POCKET_RADIUS:
                return True, mult
        return False, 0

    def _physics_step(self, dt):
        """One substep of physics simulation."""
        for ball in self.balls:
            if not ball.active or not ball.moving():
                continue

            # Move
            ball.x += ball.vx * dt
            ball.y += ball.vy * dt

            # Friction
            spd = ball.speed()
            if spd > 0:
                decel = FRICTION * dt
                new_spd = max(0, spd - decel)
                factor = new_spd / spd
                ball.vx *= factor
                ball.vy *= factor
                if new_spd < MIN_SPEED:
                    ball.vx = 0.0
                    ball.vy = 0.0

            # Cushion bounces (skip near pockets)
            if not self._near_pocket(ball.x, ball.y):
                if ball.x <= TABLE_LEFT + 1:
                    ball.x = TABLE_LEFT + 1
                    ball.vx = abs(ball.vx) * CUSHION_RESTITUTION
                    ball.vy *= CUSHION_RESTITUTION
                elif ball.x >= TABLE_RIGHT - 1:
                    ball.x = TABLE_RIGHT - 1
                    ball.vx = -abs(ball.vx) * CUSHION_RESTITUTION
                    ball.vy *= CUSHION_RESTITUTION
                if ball.y <= TABLE_TOP + 1:
                    ball.y = TABLE_TOP + 1
                    ball.vy = abs(ball.vy) * CUSHION_RESTITUTION
                    ball.vx *= CUSHION_RESTITUTION
                elif ball.y >= TABLE_BOTTOM - 1:
                    ball.y = TABLE_BOTTOM - 1
                    ball.vy = -abs(ball.vy) * CUSHION_RESTITUTION
                    ball.vx *= CUSHION_RESTITUTION

            # Check pockets
            pocketed, mult = self._check_pocket(ball)
            if pocketed:
                ball.active = False
                ball.vx = 0.0
                ball.vy = 0.0
                if ball.num == 0:
                    # Cue ball scratch
                    self.scratch = True
                else:
                    # Object ball pocketed
                    points = BALL_VALUES.get(ball.num, 10) * mult
                    self.points_earned += points
                    self.pocketed_this_shot.append(ball.num)

        # Ball-to-ball collisions (elastic, equal mass)
        active = [b for b in self.balls if b.active]
        for i in range(len(active)):
            for j in range(i + 1, len(active)):
                a = active[i]
                b = active[j]
                dx = b.x - a.x
                dy = b.y - a.y
                dist_sq = dx * dx + dy * dy
                min_dist = BALL_COLLISION_DIST
                if dist_sq < min_dist * min_dist and dist_sq > 0:
                    dist = math.sqrt(dist_sq)
                    nx = dx / dist
                    ny = dy / dist

                    # Separate overlapping balls
                    overlap = min_dist - dist
                    a.x -= nx * overlap * 0.5
                    a.y -= ny * overlap * 0.5
                    b.x += nx * overlap * 0.5
                    b.y += ny * overlap * 0.5

                    # Elastic collision (equal mass: swap normal components)
                    rel_vn = (b.vx - a.vx) * nx + (b.vy - a.vy) * ny
                    if rel_vn < 0:  # approaching
                        a.vx += rel_vn * nx
                        a.vy += rel_vn * ny
                        b.vx -= rel_vn * nx
                        b.vy -= rel_vn * ny

    def _fire_shot(self):
        cue = self._cue_ball()
        if not cue:
            return
        power = (self.power / 1.0) * MAX_POWER
        cue.vx = math.cos(self.aim_angle) * power
        cue.vy = math.sin(self.aim_angle) * power
        self.phase = PHASE_SHOOTING
        self.scratch = False
        self.points_earned = 0
        self.pocketed_this_shot = []

    def _replace_cue_ball(self):
        """Put cue ball back at break position."""
        cue = None
        for b in self.balls:
            if b.num == 0:
                cue = b
                break
        if cue is None:
            cue = Ball(0, CUE_BREAK_X, CUE_BREAK_Y)
            self.balls.insert(0, cue)
        cue.x = CUE_BREAK_X
        cue.y = CUE_BREAK_Y
        cue.vx = 0.0
        cue.vy = 0.0
        cue.active = True

    def _check_table_clear(self):
        return len(self._object_balls()) == 0

    def _re_rack(self):
        """Re-rack object balls after a table clear."""
        # Remove old object balls
        self.balls = [b for b in self.balls if b.num == 0]
        # Add new racked balls
        spacing = 3.5
        rows = [[1], [2, 3], [4, 5, 6]]
        for row_i, row in enumerate(rows):
            rx = RACK_X + row_i * spacing
            row_height = (len(row) - 1) * spacing
            for ball_i, ball_num in enumerate(row):
                ry = RACK_Y - row_height / 2 + ball_i * spacing
                self.balls.append(Ball(ball_num, rx, ry))

    # ==== UPDATE ====

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        if self.phase == PHASE_MODE_SELECT:
            self._update_mode_select(input_state)
        elif self.phase == PHASE_AIMING:
            self._update_aiming(input_state, dt)
        elif self.phase == PHASE_POWER:
            self._update_power(input_state, dt)
        elif self.phase == PHASE_SHOOTING:
            self._update_shooting(dt)
        elif self.phase == PHASE_SCORING:
            self._update_scoring(dt)
        elif self.phase == PHASE_FOUL:
            self._update_foul(dt)
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
                self.shots_left = 10
            self.phase = PHASE_AIMING

    def _update_aiming(self, inp, dt):
        # Left/Right = smooth continuous rotation (held)
        smooth_speed = 1.6
        if inp.left:
            self.aim_angle -= smooth_speed * dt
        if inp.right:
            self.aim_angle += smooth_speed * dt

        # Up/Down = precision discrete steps (pressed)
        precision_step = math.pi / 64  # ~2.8 degrees per tap
        if inp.up_pressed:
            self.aim_angle -= precision_step
        if inp.down_pressed:
            self.aim_angle += precision_step

        # Wrap angle
        self.aim_angle = self.aim_angle % (2 * math.pi)

        if inp.action_l or inp.action_r:
            # Start power bar
            self.power = 0.0
            self.power_dir = 1
            self.phase = PHASE_POWER

    def _update_power(self, inp, dt):
        # Any joystick input cancels back to aiming (accidental press)
        if inp.any_direction:
            self.phase = PHASE_AIMING
            return

        # Oscillate power 0..1
        self.power += self.power_dir * self.power_speed * dt
        if self.power >= 1.0:
            self.power = 1.0
            self.power_dir = -1
        elif self.power <= 0.0:
            self.power = 0.0
            self.power_dir = 1

        if inp.action_l or inp.action_r:
            self._fire_shot()

    def _update_shooting(self, dt):
        # Run physics substeps
        sub_dt = dt / SUBSTEPS
        for _ in range(SUBSTEPS):
            self._physics_step(sub_dt)

        # Wait for all balls to stop
        if not self._any_moving():
            # Shot finished
            if self.scratch:
                self.phase = PHASE_FOUL
                self.phase_timer = 1.0
            elif self.points_earned > 0:
                self.phase = PHASE_SCORING
                self.phase_timer = 0.7
            else:
                # Miss - no balls pocketed
                self._handle_miss()

    def _handle_miss(self):
        if self.two_player:
            self.phase = PHASE_TURN_CHANGE
            self.phase_timer = 0.5
            self.current_player = 1 - self.current_player
        else:
            # 1P: just aim again (no penalty for miss)
            self.shots_left -= 1
            if self.shots_left <= 0:
                self.state = GameState.GAME_OVER
            else:
                self.phase = PHASE_AIMING

    def _update_scoring(self, dt):
        self.phase_timer -= dt
        if self.phase_timer <= 0:
            # Apply score
            if self.two_player:
                self.scores[self.current_player] += self.points_earned
                self.score = self.scores[self.current_player]
            else:
                self.score += self.points_earned
                # Potted a ball: +1 shot per ball
                self.shots_left += len(self.pocketed_this_shot)

            # Check table clear
            if self._check_table_clear():
                if self.two_player:
                    # Game over in 2P
                    self.phase = PHASE_GAME_OVER_2P
                    return
                else:
                    self.score += CLEAR_BONUS
                    self.shots_left += 5
                    self._re_rack()
                    self._replace_cue_ball()

            # Potted a ball = shoot again (both modes)
            if self.scratch:
                self._replace_cue_ball()
            self.phase = PHASE_AIMING

    def _update_foul(self, dt):
        self.phase_timer -= dt
        if self.phase_timer <= 0:
            self._replace_cue_ball()
            if self.two_player:
                # Scratch: turn passes
                self.phase = PHASE_TURN_CHANGE
                self.phase_timer = 0.5
                self.current_player = 1 - self.current_player
            else:
                # 1P scratch: costs a shot
                self.shots_left -= 2  # normal -1 plus penalty -1
                if self.shots_left <= 0:
                    self.shots_left = 0
                    self.state = GameState.GAME_OVER
                else:
                    self.phase = PHASE_AIMING

    def _update_turn_change(self, dt):
        self.phase_timer -= dt
        if self.phase_timer <= 0:
            self.phase = PHASE_AIMING

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

        # Draw table
        self._draw_table()

        # Draw balls
        self._draw_balls()

        # Draw HUD
        self._draw_hud()

        # Phase-specific overlays
        if self.phase == PHASE_AIMING:
            self._draw_aim_line()
        elif self.phase == PHASE_POWER:
            self._draw_aim_line()
            self._draw_power_bar()
        elif self.phase == PHASE_SCORING:
            self._draw_scoring_flash()
        elif self.phase == PHASE_FOUL:
            self._draw_foul_flash()
        elif self.phase == PHASE_TURN_CHANGE:
            self._draw_turn_change()

    def _draw_mode_select(self):
        self.display.draw_text_small(18, 10, "POOL", Colors.WHITE)
        # Simple table icon
        self.display.draw_rect(16, 20, 32, 18, BORDER_COLOR, filled=False)
        self.display.draw_rect(17, 21, 30, 16, FELT_COLOR, filled=True)

        y1 = 44
        if self.mode_select == 0:
            self.display.draw_text_small(2, y1, ">1 PLAYER", Colors.YELLOW)
            self.display.draw_text_small(2, y1 + 10, " 2 PLAYERS", Colors.GRAY)
        else:
            self.display.draw_text_small(2, y1, " 1 PLAYER", Colors.GRAY)
            self.display.draw_text_small(2, y1 + 10, ">2 PLAYERS", Colors.YELLOW)

    def _draw_table(self):
        # Border
        self.display.draw_rect(TABLE_LEFT - TABLE_BORDER, TABLE_TOP - TABLE_BORDER,
                               TABLE_RIGHT - TABLE_LEFT + 1 + TABLE_BORDER * 2,
                               TABLE_BOTTOM - TABLE_TOP + 1 + TABLE_BORDER * 2,
                               BORDER_COLOR, filled=True)
        # Felt
        self.display.draw_rect(TABLE_LEFT, TABLE_TOP,
                               TABLE_RIGHT - TABLE_LEFT + 1,
                               TABLE_BOTTOM - TABLE_TOP + 1,
                               FELT_COLOR, filled=True)
        # Pockets
        for px, py, _ in POCKETS:
            self.display.set_pixel(px, py, POCKET_COLOR)
            self.display.set_pixel(px - 1, py, POCKET_COLOR)
            self.display.set_pixel(px + 1, py, POCKET_COLOR)
            self.display.set_pixel(px, py - 1, POCKET_COLOR)
            self.display.set_pixel(px, py + 1, POCKET_COLOR)

    def _draw_balls(self):
        for ball in self.balls:
            if not ball.active:
                continue
            bx = int(ball.x)
            by = int(ball.y)
            color = BALL_COLORS.get(ball.num, Colors.WHITE)
            # 3x3 circle: full color center + cardinal, dimmed corners
            dim = (color[0] * 2 // 5, color[1] * 2 // 5, color[2] * 2 // 5)
            self.display.set_pixel(bx, by, color)
            self.display.set_pixel(bx - 1, by, color)
            self.display.set_pixel(bx + 1, by, color)
            self.display.set_pixel(bx, by - 1, color)
            self.display.set_pixel(bx, by + 1, color)
            self.display.set_pixel(bx - 1, by - 1, dim)
            self.display.set_pixel(bx + 1, by - 1, dim)
            self.display.set_pixel(bx - 1, by + 1, dim)
            self.display.set_pixel(bx + 1, by + 1, dim)

    def _draw_hud(self):
        if self.two_player:
            p1_color = Colors.YELLOW if self.current_player == 0 else Colors.GRAY
            p2_color = Colors.YELLOW if self.current_player == 1 else Colors.GRAY
            self.display.draw_text_small(2, 1, f"P1:{self.scores[0]}", p1_color)
            self.display.draw_text_small(34, 1, f"P2:{self.scores[1]}", p2_color)
        else:
            self.display.draw_text_small(2, 1, f"{self.score}", Colors.WHITE)
            self.display.draw_text_small(34, 1, f"SHOTS:{self.shots_left}", Colors.CYAN)

    def _draw_aim_line(self):
        """Draw dotted trajectory line from cue ball."""
        cue = self._cue_ball()
        if not cue:
            return

        dx = math.cos(self.aim_angle)
        dy = math.sin(self.aim_angle)

        # Trace until we hit a cushion
        x, y = cue.x, cue.y
        step = 1.0
        drawn = 0
        for i in range(1, 60):
            nx = x + dx * step * i
            ny = y + dy * step * i

            # Check if out of bounds (hit cushion)
            if nx <= TABLE_LEFT + 1 or nx >= TABLE_RIGHT - 1:
                # Draw bounce continuation
                bounce_dx = -dx
                bounce_dy = dy
                bx, by = nx, ny
                # Clamp to table edge
                if nx <= TABLE_LEFT + 1:
                    bx = TABLE_LEFT + 1
                elif nx >= TABLE_RIGHT - 1:
                    bx = TABLE_RIGHT - 1
                # Draw a few pixels of bounce
                for j in range(1, 15):
                    bnx = bx + bounce_dx * step * j
                    bny = by + bounce_dy * step * j
                    if (TABLE_LEFT + 1 <= bnx <= TABLE_RIGHT - 1 and
                            TABLE_TOP + 1 <= bny <= TABLE_BOTTOM - 1):
                        if j % 3 != 0:
                            self.display.set_pixel(int(bnx), int(bny), (100, 100, 100))
                break
            if ny <= TABLE_TOP + 1 or ny >= TABLE_BOTTOM - 1:
                bounce_dx = dx
                bounce_dy = -dy
                bx, by = nx, ny
                if ny <= TABLE_TOP + 1:
                    by = TABLE_TOP + 1
                elif ny >= TABLE_BOTTOM - 1:
                    by = TABLE_BOTTOM - 1
                for j in range(1, 15):
                    bnx = bx + bounce_dx * step * j
                    bny = by + bounce_dy * step * j
                    if (TABLE_LEFT + 1 <= bnx <= TABLE_RIGHT - 1 and
                            TABLE_TOP + 1 <= bny <= TABLE_BOTTOM - 1):
                        if j % 3 != 0:
                            self.display.set_pixel(int(bnx), int(bny), (100, 100, 100))
                break

            # Draw dotted line (every other 2 pixels)
            if i % 3 != 0:
                self.display.set_pixel(int(nx), int(ny), Colors.WHITE)
            drawn += 1

    def _draw_power_bar(self):
        """Draw oscillating power bar in HUD area."""
        bar_x = 2
        bar_y = 7
        bar_w = 60
        bar_h = 2

        # Background
        self.display.draw_rect(bar_x, bar_y, bar_w, bar_h, (40, 40, 40), filled=True)

        # Filled portion
        fill_w = int(self.power * bar_w)
        for px in range(fill_w):
            frac = px / max(bar_w - 1, 1)
            if frac < 0.5:
                # Green to yellow
                r = int(255 * frac * 2)
                g = 255
            else:
                # Yellow to red
                r = 255
                g = int(255 * (1.0 - frac) * 2)
            color = (r, g, 0)
            self.display.set_pixel(bar_x + px, bar_y, color)
            self.display.set_pixel(bar_x + px, bar_y + 1, color)

    def _draw_scoring_flash(self):
        """Flash points earned."""
        if self.points_earned > 0:
            txt = f"+{self.points_earned}"
            self.display.draw_text_small(24, 30, txt, Colors.YELLOW)

    def _draw_foul_flash(self):
        self.display.draw_text_small(10, 30, "SCRATCH!", Colors.RED)

    def _draw_turn_change(self):
        p = self.current_player + 1
        self.display.draw_text_small(10, 30, f"P{p} TURN", Colors.CYAN)

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
