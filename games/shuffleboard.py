"""
Shuffleboard - LED Arcade
==========================
Bar-style table shuffleboard on a 64x64 LED matrix.
Slide pucks toward scoring zones. Physics with friction and collisions.
1P score attack (4 pucks x 4 rounds) and 2P alternating shots (4 each).

Controls:
  Space      - Lock aim / confirm power / navigate mode select
  Joystick   - Cancel power back to aim / navigate mode select
"""

import math
import random
from arcade import Game, GameState, Display, Colors, InputState

# Phases
PHASE_MODE_SELECT = 0
PHASE_AIM = 1
PHASE_POWER = 2
PHASE_SLIDING = 3
PHASE_SCORE_SHOW = 4
PHASE_TURN_CHANGE = 5
PHASE_GAME_OVER_2P = 6

# Table geometry
TABLE_LEFT = 8
TABLE_RIGHT = 55
TABLE_WIDTH = TABLE_RIGHT - TABLE_LEFT  # 48px

# Zones (y coordinates, top to bottom)
TOP_RAIL = 0       # y=0-1, fall-off edge
ZONE4_TOP = 2      # y=2-10, 4 pts
ZONE4_BOTTOM = 10
ZONE3_TOP = 11     # y=11-19, 3 pts
ZONE3_BOTTOM = 19
ZONE2_TOP = 20     # y=20-28, 2 pts
ZONE2_BOTTOM = 28
ZONE1_TOP = 29     # y=29-37, 1 pt
ZONE1_BOTTOM = 37
NO_SCORE_TOP = 38  # y=38-44, 0 pts
NO_SCORE_BOTTOM = 44
FOUL_LINE_Y = 45
LAUNCH_TOP = 46
LAUNCH_BOTTOM = 54
BOTTOM_RAIL = 55   # y=55-56

# HUD area
HUD_TOP = 57
HUD_BOTTOM = 63

# Zone colors (lightest at top = highest score)
ZONE4_COLOR = (160, 120, 60)   # light wood
ZONE3_COLOR = (130, 95, 45)
ZONE2_COLOR = (110, 80, 35)
ZONE1_COLOR = (90, 65, 30)
NO_SCORE_COLOR = (70, 50, 25)  # dark wood
LAUNCH_COLOR = (80, 60, 30)
RAIL_COLOR = (50, 35, 15)
FOUL_LINE_COLOR = Colors.RED

# Puck properties
PUCK_RADIUS = 2.0      # visual and collision radius
PUCK_COLLISION_DIST = 4.0  # diameter for collision
P1_PUCK_COLOR = Colors.YELLOW
P2_PUCK_COLOR = Colors.CYAN
SOLO_PUCK_COLOR = Colors.YELLOW

# Physics
FRICTION = 18.0          # px/s^2 deceleration
SIDE_RESTITUTION = 0.4   # low bounce off side rails
PUCK_RESTITUTION = 0.85  # puck-to-puck
MIN_SPEED = 2.0          # below this, puck stops
MAX_POWER = 90.0
SUBSTEPS = 3

# Aim
MAX_AIM_ANGLE = math.pi / 5  # ~36 degrees
BASE_AIM_SPEED = 1.8   # radians/s
AIM_SPEED_PER_ROUND = 0.15

# Power bar
BASE_POWER_SPEED = 1.5  # oscillations/s
POWER_SPEED_PER_ROUND = 0.1

# Game config
PUCKS_PER_PLAYER = 4
TOTAL_ROUNDS = 4

# Timing
SCORE_SHOW_TIME = 1.5
TURN_CHANGE_TIME = 0.5


class Puck:
    __slots__ = ['x', 'y', 'vx', 'vy', 'player', 'active', 'scored']

    def __init__(self, x, y, player):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.player = player  # 0 or 1
        self.active = True    # on table
        self.scored = False    # has been scored

    def speed(self):
        return math.sqrt(self.vx * self.vx + self.vy * self.vy)

    def moving(self):
        return self.speed() > MIN_SPEED


class Shuffleboard(Game):
    name = "SHUFFLEBOARD"
    description = "Slide pucks into scoring zones"
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
        self.current_round = 0
        self.pucks_remaining = [PUCKS_PER_PLAYER, PUCKS_PER_PLAYER]
        self.scores = [0, 0]

        # Pucks on table
        self.pucks = []

        # Aim
        self.aim_angle = 0.0  # radians from vertical (neg=left, pos=right)
        self.aim_dir = 1
        self.launch_x = float((TABLE_LEFT + TABLE_RIGHT) // 2)

        # Power
        self.power = 0.0
        self.power_dir = 1

        # Phase timer
        self.phase_timer = 0.0
        self.round_scores = [0, 0]  # scores for current round display

    def _aim_speed(self):
        return BASE_AIM_SPEED + AIM_SPEED_PER_ROUND * self.current_round

    def _power_speed(self):
        return BASE_POWER_SPEED + POWER_SPEED_PER_ROUND * self.current_round

    def _any_moving(self):
        return any(p.moving() for p in self.pucks if p.active)

    def _start_aim(self):
        self.phase = PHASE_AIM
        self.aim_angle = 0.0
        self.aim_dir = 1
        self.launch_x = float((TABLE_LEFT + TABLE_RIGHT) // 2)

    def _start_power(self):
        self.phase = PHASE_POWER
        self.power = 0.0
        self.power_dir = 1

    def _launch_puck(self):
        puck = Puck(self.launch_x, float(LAUNCH_BOTTOM - 2), self.current_player)
        vx = math.sin(self.aim_angle) * self.power * MAX_POWER
        vy = -math.cos(self.aim_angle) * self.power * MAX_POWER  # upward
        puck.vx = vx
        puck.vy = vy
        self.pucks.append(puck)
        self.pucks_remaining[self.current_player] -= 1
        self.phase = PHASE_SLIDING

    def _zone_score(self, y):
        """Return point value for a puck resting at y position."""
        if y < ZONE4_TOP or y > NO_SCORE_BOTTOM:
            return 0
        if y <= ZONE4_BOTTOM:
            return 4
        if y <= ZONE3_BOTTOM:
            return 3
        if y <= ZONE2_BOTTOM:
            return 2
        if y <= ZONE1_BOTTOM:
            return 1
        return 0  # no-score area

    def _physics_step(self, dt):
        """One substep of physics."""
        for puck in self.pucks:
            if not puck.active or not puck.moving():
                continue

            puck.x += puck.vx * dt
            puck.y += puck.vy * dt

            # Friction
            spd = puck.speed()
            if spd > 0:
                decel = FRICTION * dt
                new_spd = max(0, spd - decel)
                factor = new_spd / spd
                puck.vx *= factor
                puck.vy *= factor
                if new_spd < MIN_SPEED:
                    puck.vx = 0.0
                    puck.vy = 0.0

            # Side rails — puck stops horizontally (no bounce)
            if puck.x <= TABLE_LEFT + 1:
                puck.x = TABLE_LEFT + 1
                puck.vx = 0.0
            elif puck.x >= TABLE_RIGHT - 1:
                puck.x = TABLE_RIGHT - 1
                puck.vx = 0.0

            # Top edge: puck falls off
            if puck.y < TOP_RAIL:
                puck.active = False
                puck.vx = 0.0
                puck.vy = 0.0
                continue

            # Bottom rail: bounce back (shouldn't happen much)
            if puck.y > BOTTOM_RAIL:
                puck.y = BOTTOM_RAIL
                puck.vy = -abs(puck.vy) * SIDE_RESTITUTION

            # Below foul line = stays but scores 0 (handled in scoring)

        # Puck-to-puck collisions
        active = [p for p in self.pucks if p.active]
        for i in range(len(active)):
            for j in range(i + 1, len(active)):
                a = active[i]
                b = active[j]
                dx = b.x - a.x
                dy = b.y - a.y
                dist_sq = dx * dx + dy * dy
                min_dist = PUCK_COLLISION_DIST
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
                        a.vx += rel_vn * nx * PUCK_RESTITUTION
                        a.vy += rel_vn * ny * PUCK_RESTITUTION
                        b.vx -= rel_vn * nx * PUCK_RESTITUTION
                        b.vy -= rel_vn * ny * PUCK_RESTITUTION

    def _calculate_round_scores(self):
        """Tally scores for all pucks currently on the table."""
        self.round_scores = [0, 0]
        for puck in self.pucks:
            if not puck.active:
                continue
            py = int(round(puck.y))
            # Below foul line = 0
            if py >= FOUL_LINE_Y:
                pts = 0
            else:
                pts = self._zone_score(py)
            self.round_scores[puck.player] += pts

    def _end_round(self):
        """Finalize round scores and advance."""
        self._calculate_round_scores()
        self.scores[0] += self.round_scores[0]
        self.scores[1] += self.round_scores[1]
        self.score = self.scores[0] if not self.two_player else self.scores[self.current_player]

    def _next_shot_or_round(self):
        """Determine what happens after pucks stop."""
        if self.two_player:
            # Check if both players have pucks remaining
            p1_left = self.pucks_remaining[0]
            p2_left = self.pucks_remaining[1]

            if p1_left == 0 and p2_left == 0:
                # Round over
                self._end_round()
                self.current_round += 1
                if self.current_round >= TOTAL_ROUNDS:
                    self.phase = PHASE_SCORE_SHOW
                    self.phase_timer = SCORE_SHOW_TIME
                    self._pending_game_over = True
                else:
                    self.phase = PHASE_SCORE_SHOW
                    self.phase_timer = SCORE_SHOW_TIME
                    self._pending_new_round = True
            else:
                # Switch to other player if they have pucks
                other = 1 - self.current_player
                if self.pucks_remaining[other] > 0:
                    self.current_player = other
                    self.phase = PHASE_TURN_CHANGE
                    self.phase_timer = TURN_CHANGE_TIME
                elif self.pucks_remaining[self.current_player] > 0:
                    # Other player is out, current keeps shooting
                    self._start_aim()
                else:
                    # Both done (shouldn't reach here)
                    self._end_round()
                    self.current_round += 1
                    self.phase = PHASE_SCORE_SHOW
                    self.phase_timer = SCORE_SHOW_TIME
                    self._pending_new_round = True
        else:
            # 1P mode
            if self.pucks_remaining[0] == 0:
                # Round over
                self._end_round()
                self.current_round += 1
                if self.current_round >= TOTAL_ROUNDS:
                    self.score = self.scores[0]
                    self.state = GameState.GAME_OVER
                else:
                    self.phase = PHASE_SCORE_SHOW
                    self.phase_timer = SCORE_SHOW_TIME
                    self._pending_new_round = True
            else:
                self._start_aim()

    def _start_new_round(self):
        """Reset for a new round."""
        self.pucks = []
        self.pucks_remaining = [PUCKS_PER_PLAYER, PUCKS_PER_PLAYER]
        self.current_player = 0
        self._start_aim()

    # ==== UPDATE ====

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        if self.phase == PHASE_MODE_SELECT:
            self._update_mode_select(input_state)
        elif self.phase == PHASE_AIM:
            self._update_aim(input_state, dt)
        elif self.phase == PHASE_POWER:
            self._update_power(input_state, dt)
        elif self.phase == PHASE_SLIDING:
            self._update_sliding(dt)
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
            self.scores = [0, 0]
            self.current_player = 0
            self.current_round = 0
            self.pucks = []
            self.pucks_remaining = [PUCKS_PER_PLAYER, PUCKS_PER_PLAYER]
            self._pending_game_over = False
            self._pending_new_round = False
            self._start_aim()

    def _update_aim(self, inp, dt):
        speed = self._aim_speed()
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
        # Joystick cancels back to aim
        if inp.any_direction:
            self.phase = PHASE_AIM
            return

        speed = self._power_speed()
        self.power += self.power_dir * speed * dt
        if self.power >= 1.0:
            self.power = 1.0
            self.power_dir = -1
        elif self.power <= 0.0:
            self.power = 0.0
            self.power_dir = 1

        if inp.action_l or inp.action_r:
            self._launch_puck()

    def _update_sliding(self, dt):
        sub_dt = dt / SUBSTEPS
        for _ in range(SUBSTEPS):
            self._physics_step(sub_dt)

        if not self._any_moving():
            self._next_shot_or_round()

    def _update_score_show(self, dt):
        self.phase_timer -= dt
        if self.phase_timer <= 0:
            if hasattr(self, '_pending_game_over') and self._pending_game_over:
                self._pending_game_over = False
                if self.two_player:
                    self.phase = PHASE_GAME_OVER_2P
                else:
                    self.score = self.scores[0]
                    self.state = GameState.GAME_OVER
            elif hasattr(self, '_pending_new_round') and self._pending_new_round:
                self._pending_new_round = False
                self._start_new_round()
            else:
                self._start_aim()

    def _update_turn_change(self, dt):
        self.phase_timer -= dt
        if self.phase_timer <= 0:
            self._start_aim()

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

        # Draw pucks
        self._draw_pucks()

        # Draw HUD
        self._draw_hud()

        # Phase overlays
        if self.phase == PHASE_AIM:
            self._draw_aim()
        elif self.phase == PHASE_POWER:
            self._draw_aim()
            self._draw_power_bar()
        elif self.phase == PHASE_SCORE_SHOW:
            self._draw_score_show()
        elif self.phase == PHASE_TURN_CHANGE:
            self._draw_turn_change()

    def _draw_mode_select(self):
        self.display.draw_text_small(2, 6, "SHUFFLE", Colors.WHITE)
        self.display.draw_text_small(2, 13, "BOARD", Colors.WHITE)

        # Simple table icon
        self.display.draw_rect(18, 22, 28, 14, ZONE2_COLOR, filled=True)
        self.display.draw_rect(18, 22, 28, 4, ZONE4_COLOR, filled=True)
        self.display.draw_rect(18, 26, 28, 4, ZONE3_COLOR, filled=True)
        # Zone lines
        for x in range(18, 46):
            self.display.set_pixel(x, 26, (60, 40, 20))
            self.display.set_pixel(x, 30, (60, 40, 20))

        y1 = 44
        if self.mode_select == 0:
            self.display.draw_text_small(2, y1, ">1 PLAYER", Colors.YELLOW)
            self.display.draw_text_small(2, y1 + 10, " 2 PLAYERS", Colors.GRAY)
        else:
            self.display.draw_text_small(2, y1, " 1 PLAYER", Colors.GRAY)
            self.display.draw_text_small(2, y1 + 10, ">2 PLAYERS", Colors.YELLOW)

    def _draw_table(self):
        # Side rails
        for y in range(TOP_RAIL, BOTTOM_RAIL + 2):
            self.display.set_pixel(TABLE_LEFT - 1, y, RAIL_COLOR)
            self.display.set_pixel(TABLE_LEFT - 2, y, RAIL_COLOR)
            self.display.set_pixel(TABLE_RIGHT + 1, y, RAIL_COLOR)
            self.display.set_pixel(TABLE_RIGHT + 2, y, RAIL_COLOR)

        # Top rail
        for x in range(TABLE_LEFT - 2, TABLE_RIGHT + 3):
            self.display.set_pixel(x, TOP_RAIL, RAIL_COLOR)
            self.display.set_pixel(x, TOP_RAIL + 1, RAIL_COLOR)

        # Bottom rail
        for x in range(TABLE_LEFT - 2, TABLE_RIGHT + 3):
            self.display.set_pixel(x, BOTTOM_RAIL, RAIL_COLOR)
            self.display.set_pixel(x, BOTTOM_RAIL + 1, RAIL_COLOR)

        # Zone 4 (4 pts)
        for y in range(ZONE4_TOP, ZONE4_BOTTOM + 1):
            for x in range(TABLE_LEFT, TABLE_RIGHT + 1):
                self.display.set_pixel(x, y, ZONE4_COLOR)

        # Zone 3 (3 pts)
        for y in range(ZONE3_TOP, ZONE3_BOTTOM + 1):
            for x in range(TABLE_LEFT, TABLE_RIGHT + 1):
                self.display.set_pixel(x, y, ZONE3_COLOR)

        # Zone 2 (2 pts)
        for y in range(ZONE2_TOP, ZONE2_BOTTOM + 1):
            for x in range(TABLE_LEFT, TABLE_RIGHT + 1):
                self.display.set_pixel(x, y, ZONE2_COLOR)

        # Zone 1 (1 pt)
        for y in range(ZONE1_TOP, ZONE1_BOTTOM + 1):
            for x in range(TABLE_LEFT, TABLE_RIGHT + 1):
                self.display.set_pixel(x, y, ZONE1_COLOR)

        # No-score area
        for y in range(NO_SCORE_TOP, NO_SCORE_BOTTOM + 1):
            for x in range(TABLE_LEFT, TABLE_RIGHT + 1):
                self.display.set_pixel(x, y, NO_SCORE_COLOR)

        # Launch area
        for y in range(LAUNCH_TOP, LAUNCH_BOTTOM + 1):
            for x in range(TABLE_LEFT, TABLE_RIGHT + 1):
                self.display.set_pixel(x, y, LAUNCH_COLOR)

        # Zone divider lines
        for x in range(TABLE_LEFT, TABLE_RIGHT + 1):
            self.display.set_pixel(x, ZONE4_BOTTOM, (100, 75, 35))
            self.display.set_pixel(x, ZONE3_BOTTOM, (100, 75, 35))
            self.display.set_pixel(x, ZONE2_BOTTOM, (100, 75, 35))
            self.display.set_pixel(x, ZONE1_BOTTOM, (100, 75, 35))

        # Foul line
        for x in range(TABLE_LEFT, TABLE_RIGHT + 1):
            self.display.set_pixel(x, FOUL_LINE_Y, FOUL_LINE_COLOR)

        # Zone labels (right edge)
        self.display.draw_text_small(TABLE_RIGHT - 3, (ZONE4_TOP + ZONE4_BOTTOM) // 2 - 2, "4", (200, 160, 80))
        self.display.draw_text_small(TABLE_RIGHT - 3, (ZONE3_TOP + ZONE3_BOTTOM) // 2 - 2, "3", (180, 140, 70))
        self.display.draw_text_small(TABLE_RIGHT - 3, (ZONE2_TOP + ZONE2_BOTTOM) // 2 - 2, "2", (160, 120, 60))
        self.display.draw_text_small(TABLE_RIGHT - 3, (ZONE1_TOP + ZONE1_BOTTOM) // 2 - 2, "1", (140, 100, 50))

    def _draw_pucks(self):
        for puck in self.pucks:
            if not puck.active:
                continue
            px = int(round(puck.x))
            py = int(round(puck.y))

            if self.two_player:
                color = P1_PUCK_COLOR if puck.player == 0 else P2_PUCK_COLOR
            else:
                color = SOLO_PUCK_COLOR

            dim = (color[0] * 2 // 5, color[1] * 2 // 5, color[2] * 2 // 5)

            # 3x3 puck with dimmed corners
            self.display.set_pixel(px, py, color)
            self.display.set_pixel(px - 1, py, color)
            self.display.set_pixel(px + 1, py, color)
            self.display.set_pixel(px, py - 1, color)
            self.display.set_pixel(px, py + 1, color)
            self.display.set_pixel(px - 1, py - 1, dim)
            self.display.set_pixel(px + 1, py - 1, dim)
            self.display.set_pixel(px - 1, py + 1, dim)
            self.display.set_pixel(px + 1, py + 1, dim)

    def _draw_hud(self):
        # Dark background
        self.display.draw_rect(0, HUD_TOP, 64, HUD_BOTTOM - HUD_TOP + 1, Colors.BLACK)

        if self.two_player:
            p1_c = Colors.YELLOW if self.current_player == 0 else Colors.GRAY
            p2_c = Colors.CYAN if self.current_player == 1 else Colors.GRAY
            self.display.draw_text_small(2, HUD_TOP + 1, f"P1:{self.scores[0]}", p1_c)
            self.display.draw_text_small(34, HUD_TOP + 1, f"P2:{self.scores[1]}", p2_c)
        else:
            self.display.draw_text_small(2, HUD_TOP + 1, f"{self.scores[0]}", Colors.WHITE)

        # Round indicator
        rnd = min(self.current_round + 1, TOTAL_ROUNDS)
        self.display.draw_text_small(42, HUD_TOP + 1, f"R{rnd}", Colors.CYAN)

        # Puck indicators (dots showing remaining pucks for current player)
        p = self.current_player
        remaining = self.pucks_remaining[p]
        dot_x = 2
        dot_y = HUD_TOP + 6
        puck_c = P1_PUCK_COLOR if p == 0 else P2_PUCK_COLOR
        if not self.two_player:
            puck_c = SOLO_PUCK_COLOR
        for i in range(remaining):
            self.display.set_pixel(dot_x + i * 3, dot_y, puck_c)

    def _draw_aim(self):
        """Draw oscillating aim line from launch position."""
        cx = (TABLE_LEFT + TABLE_RIGHT) // 2
        start_y = LAUNCH_TOP

        dx = math.sin(self.aim_angle)
        dy = -math.cos(self.aim_angle)

        for i in range(1, 30):
            lx = cx + dx * i
            ly = start_y + dy * i
            ix = int(round(lx))
            iy = int(round(ly))
            if iy < ZONE4_TOP:
                break
            if ix < TABLE_LEFT or ix > TABLE_RIGHT:
                break
            if i % 3 != 0:
                color = P1_PUCK_COLOR if self.current_player == 0 else P2_PUCK_COLOR
                if not self.two_player:
                    color = Colors.WHITE
                self.display.set_pixel(ix, iy, color)

    def _draw_power_bar(self):
        """Draw power bar at bottom of table area."""
        bar_x = TABLE_LEFT
        bar_y = LAUNCH_BOTTOM + 1
        bar_w = TABLE_RIGHT - TABLE_LEFT + 1
        bar_h = 1

        # Background
        self.display.draw_rect(bar_x, bar_y, bar_w, bar_h, (40, 40, 40))

        # Fill
        fill_w = int(self.power * bar_w)
        for px in range(fill_w):
            frac = px / max(bar_w - 1, 1)
            if frac < 0.5:
                r = int(255 * frac * 2)
                g = 255
            else:
                r = 255
                g = int(255 * (1.0 - frac) * 2)
            self.display.set_pixel(bar_x + px, bar_y, (r, g, 0))

    def _draw_score_show(self):
        """Show round scores."""
        self._calculate_round_scores()
        if self.two_player:
            text = f"P1:{self.round_scores[0]} P2:{self.round_scores[1]}"
        else:
            text = f"+{self.round_scores[0]} PTS"

        tw = len(text) * 4
        tx = max(2, (64 - tw) // 2)
        ty = 26
        self.display.draw_rect(tx - 1, ty - 1, tw + 2, 7, Colors.BLACK)
        self.display.draw_text_small(tx, ty, text, Colors.YELLOW)

    def _draw_turn_change(self):
        p = self.current_player + 1
        self.display.draw_rect(8, 26, 48, 9, Colors.BLACK)
        self.display.draw_text_small(14, 28, f"P{p} TURN", Colors.CYAN)

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
