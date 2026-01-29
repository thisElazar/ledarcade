"""
Indy 500 - Top-Down Racing
===========================
Race around the track and beat your best time!

Controls:
  Left/Right - Steer
  Space      - Gas
"""

from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE
import math


class Indy500(Game):
    name = "INDY 500"
    description = "Top-Down Racing"
    category = "retro"

    # Track parameters (oval)
    TRACK_CENTER_X = 32
    TRACK_CENTER_Y = 34
    TRACK_RADIUS_X = 26  # Horizontal radius
    TRACK_RADIUS_Y = 22  # Vertical radius
    TRACK_WIDTH = 12     # Width of the track

    # Car parameters
    CAR_SIZE = 3
    MAX_SPEED = 60.0
    ACCELERATION = 40.0
    FRICTION = 25.0
    TURN_SPEED = 4.0     # Radians per second

    # Colors
    TRACK_COLOR = (60, 60, 70)
    GRASS_COLOR = (30, 80, 30)
    CURB_COLOR = (200, 50, 50)
    CAR_COLOR = (255, 200, 50)
    CAR_ACCENT = (200, 100, 30)
    FINISH_COLOR = Colors.WHITE

    def __init__(self, display: Display):
        super().__init__(display)
        self.best_time = None
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0

        # Car state - start at bottom of track
        self.x = self.TRACK_CENTER_X
        self.y = self.TRACK_CENTER_Y + self.TRACK_RADIUS_Y - self.TRACK_WIDTH // 2
        self.angle = -math.pi / 2  # Facing left (will go counter-clockwise)
        self.speed = 0.0

        # Lap tracking
        self.lap = 0
        self.lap_time = 0.0
        self.total_time = 0.0
        self.last_lap_time = 0.0
        self.crossed_finish = False
        self.checkpoint_passed = False  # Must pass opposite side before lap counts

        # Track state
        self.off_track = False
        self.off_track_timer = 0.0

        # Race state
        self.race_complete = False
        self.target_laps = 3

    def point_on_track(self, x: float, y: float) -> bool:
        """Check if a point is on the track."""
        # Distance from center (normalized for ellipse)
        dx = (x - self.TRACK_CENTER_X) / self.TRACK_RADIUS_X
        dy = (y - self.TRACK_CENTER_Y) / self.TRACK_RADIUS_Y
        dist = math.sqrt(dx * dx + dy * dy)

        # Calculate track boundaries
        inner_radius = 1 - (self.TRACK_WIDTH / 2) / min(self.TRACK_RADIUS_X, self.TRACK_RADIUS_Y)
        outer_radius = 1 + (self.TRACK_WIDTH / 2) / min(self.TRACK_RADIUS_X, self.TRACK_RADIUS_Y)

        return inner_radius <= dist <= outer_radius

    def update(self, input_state: InputState, dt: float):
        if self.state == GameState.GAME_OVER:
            if (input_state.action_l or input_state.action_r):
                self.reset()
            return

        if self.race_complete:
            return

        # Update time
        self.lap_time += dt
        self.total_time += dt

        # Steering
        if input_state.left:
            self.angle -= self.TURN_SPEED * dt
        if input_state.right:
            self.angle += self.TURN_SPEED * dt

        # Acceleration / braking
        if (input_state.action_l_held or input_state.action_r_held) or input_state.action_r_held:
            self.speed += self.ACCELERATION * dt
        else:
            # Friction when not accelerating
            self.speed -= self.FRICTION * dt

        # Speed limits
        self.speed = max(0, min(self.MAX_SPEED, self.speed))

        # Off-track penalty
        if self.off_track:
            self.speed = min(self.speed, self.MAX_SPEED * 0.4)
            self.off_track_timer += dt

        # Update position
        self.x += math.cos(self.angle) * self.speed * dt
        self.y += math.sin(self.angle) * self.speed * dt

        # Check if on track
        self.off_track = not self.point_on_track(self.x, self.y)

        # Keep on screen (wrap or clamp)
        self.x = max(2, min(GRID_SIZE - 3, self.x))
        self.y = max(10, min(GRID_SIZE - 3, self.y))

        # Check checkpoint (top of track)
        if self.y < self.TRACK_CENTER_Y - self.TRACK_RADIUS_Y + self.TRACK_WIDTH:
            self.checkpoint_passed = True

        # Check finish line crossing (outer half of track at bottom, going left)
        # Match the shifted finish line position
        track_midline_y = self.TRACK_CENTER_Y + self.TRACK_RADIUS_Y - self.TRACK_WIDTH // 2
        finish_y = track_midline_y + self.TRACK_WIDTH // 4  # Shifted toward outside
        if (abs(self.y - finish_y) < 4 and
            abs(self.x - self.TRACK_CENTER_X) < 4 and
            math.cos(self.angle) < 0):  # Moving left

            if not self.crossed_finish and self.checkpoint_passed:
                self.crossed_finish = True
                self.checkpoint_passed = False
                self.lap += 1
                self.last_lap_time = self.lap_time
                self.lap_time = 0.0

                if self.lap >= self.target_laps:
                    self.race_complete = True
                    self.score = int(self.total_time * 10)
                    if self.best_time is None or self.total_time < self.best_time:
                        self.best_time = self.total_time
                    self.state = GameState.GAME_OVER
        else:
            self.crossed_finish = False

    def draw(self):
        self.display.clear(self.GRASS_COLOR)

        # Draw track
        self.draw_track()

        # Draw finish line
        self.draw_finish_line()

        # Draw car
        self.draw_car()

        # Draw HUD
        self.draw_hud()

        # Draw race complete message
        if self.race_complete:
            self.draw_race_complete()

    def draw_track(self):
        """Draw the oval track."""
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if self.point_on_track(x, y):
                    self.display.set_pixel(x, y, self.TRACK_COLOR)

        # Draw curbs (inner and outer edges)
        for angle_deg in range(0, 360, 3):
            angle = math.radians(angle_deg)

            # Outer curb
            ox = self.TRACK_CENTER_X + math.cos(angle) * (self.TRACK_RADIUS_X + self.TRACK_WIDTH // 2 - 1)
            oy = self.TRACK_CENTER_Y + math.sin(angle) * (self.TRACK_RADIUS_Y + self.TRACK_WIDTH // 2 - 1)
            if 0 <= int(ox) < GRID_SIZE and 0 <= int(oy) < GRID_SIZE:
                color = self.CURB_COLOR if (angle_deg // 10) % 2 == 0 else Colors.WHITE
                self.display.set_pixel(int(ox), int(oy), color)

            # Inner curb
            ix = self.TRACK_CENTER_X + math.cos(angle) * (self.TRACK_RADIUS_X - self.TRACK_WIDTH // 2 + 1)
            iy = self.TRACK_CENTER_Y + math.sin(angle) * (self.TRACK_RADIUS_Y - self.TRACK_WIDTH // 2 + 1)
            if 0 <= int(ix) < GRID_SIZE and 0 <= int(iy) < GRID_SIZE:
                color = self.CURB_COLOR if (angle_deg // 10) % 2 == 0 else Colors.WHITE
                self.display.set_pixel(int(ix), int(iy), color)

    def draw_finish_line(self):
        """Draw the start/finish line across the track width."""
        finish_x = self.TRACK_CENTER_X

        # Track midline at bottom of oval
        track_midline_y = int(self.TRACK_CENTER_Y + self.TRACK_RADIUS_Y - self.TRACK_WIDTH // 2)
        track_inner_y = track_midline_y - self.TRACK_WIDTH // 2 + 2
        track_outer_y = track_midline_y + self.TRACK_WIDTH // 2 - 2

        # Shift down toward outside by half the line height
        line_height = track_outer_y - track_inner_y
        shift = line_height // 2
        track_inner_y += shift
        track_outer_y += shift

        for dy in range(track_inner_y, track_outer_y + 1):
            for dx in range(-1, 2):
                if (dx + dy) % 2 == 0:
                    px = finish_x + dx
                    if 0 <= px < GRID_SIZE and 0 <= dy < GRID_SIZE:
                        self.display.set_pixel(px, dy, self.FINISH_COLOR)

    def draw_car(self):
        """Draw the player's car."""
        cx, cy = int(self.x), int(self.y)

        # Car body (rotated rectangle approximation)
        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)

        # Draw car as a small rotated shape
        # Front
        fx = int(cx + cos_a * 2)
        fy = int(cy + sin_a * 2)
        if 0 <= fx < GRID_SIZE and 0 <= fy < GRID_SIZE:
            self.display.set_pixel(fx, fy, self.CAR_COLOR)

        # Body
        self.display.set_pixel(cx, cy, self.CAR_COLOR)

        # Back
        bx = int(cx - cos_a * 1)
        by = int(cy - sin_a * 1)
        if 0 <= bx < GRID_SIZE and 0 <= by < GRID_SIZE:
            self.display.set_pixel(bx, by, self.CAR_ACCENT)

        # Side pixels
        sx1 = int(cx - sin_a)
        sy1 = int(cy + cos_a)
        sx2 = int(cx + sin_a)
        sy2 = int(cy - cos_a)
        if 0 <= sx1 < GRID_SIZE and 0 <= sy1 < GRID_SIZE:
            self.display.set_pixel(sx1, sy1, self.CAR_ACCENT)
        if 0 <= sx2 < GRID_SIZE and 0 <= sy2 < GRID_SIZE:
            self.display.set_pixel(sx2, sy2, self.CAR_ACCENT)

    def draw_hud(self):
        """Draw lap counter and time."""
        # Lap counter
        lap_text = f"L{self.lap + 1}/{self.target_laps}"
        self.display.draw_text_small(1, 1, lap_text, Colors.WHITE)

        # Current lap time
        time_sec = int(self.lap_time)
        time_dec = int((self.lap_time - time_sec) * 10)
        time_text = f"{time_sec}.{time_dec}"
        self.display.draw_text_small(40, 1, time_text, Colors.YELLOW)

        # Speed indicator (small bar)
        speed_pct = self.speed / self.MAX_SPEED
        bar_width = int(10 * speed_pct)
        bar_color = Colors.GREEN if not self.off_track else Colors.RED
        self.display.draw_rect(54, 2, bar_width, 3, bar_color)

    def draw_race_complete(self):
        """Draw race complete message."""
        self.display.draw_text_small(12, 14, "FINISHED!", Colors.GREEN)

        # Total time
        total_sec = int(self.total_time)
        total_dec = int((self.total_time - total_sec) * 10)
        self.display.draw_text_small(8, 24, f"TIME:{total_sec}.{total_dec}s", Colors.WHITE)

        # Best time
        if self.best_time:
            best_sec = int(self.best_time)
            best_dec = int((self.best_time - best_sec) * 10)
            self.display.draw_text_small(8, 32, f"BEST:{best_sec}.{best_dec}s", Colors.YELLOW)
