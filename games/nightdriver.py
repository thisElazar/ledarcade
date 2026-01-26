"""
Night Driver - Arcade Racing
=============================
Race through the night on winding roads!

Controls:
  Left/Right - Steer
  Space      - Restart (when crashed)
"""

from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE
import math
import random


class NightDriver(Game):
    name = "NIGHT DRIVER"
    description = "Night Racing"
    category = "arcade"

    # Road parameters
    HORIZON_Y = 20          # Y position of vanishing point
    ROAD_BOTTOM_Y = 62      # Bottom of visible road
    VANISHING_X = 32        # X position of vanishing point (center)

    # Road width at bottom and top (perspective)
    ROAD_WIDTH_BOTTOM = 50
    ROAD_WIDTH_TOP = 8

    # Post spacing
    NUM_POSTS = 8           # Number of post pairs visible
    POST_SPACING = 1.0      # Distance between posts (in world units)

    # Player car
    CAR_Y = 56
    CAR_WIDTH = 8
    CAR_HEIGHT = 6

    # Colors
    POST_COLOR = (255, 255, 255)
    ROAD_EDGE_COLOR = (100, 100, 100)
    CAR_COLOR = (200, 50, 50)
    CAR_WINDOW = (100, 150, 200)

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0

        # Player position (-1.0 to 1.0, 0 = center of road)
        self.player_x = 0.0

        # Speed and distance
        self.speed = 30.0       # Units per second
        self.max_speed = 80.0
        self.distance = 0.0     # Total distance traveled

        # Post positions (0.0 to POST_SPACING, cycles)
        self.post_offset = 0.0

        # Road curve system - sustained turns
        self.curve = 0.0           # Current curve amount
        self.target_curve = 0.0    # Where we're curving toward
        self.turn_duration = 0.0   # How long current turn lasts
        self.turn_timer = 0.0      # Time in current turn
        self.straight_timer = 0.0  # Time until next turn

        # Start with a short straight
        self.straight_timer = 2.0

        # Crash state
        self.crashed = False
        self.crash_timer = 0.0

    def update(self, input_state: InputState, dt: float):
        if self.state == GameState.GAME_OVER:
            if input_state.action:
                self.reset()
            return

        if self.crashed:
            self.crash_timer -= dt
            if self.crash_timer <= 0:
                self.state = GameState.GAME_OVER
            return

        # Steering
        steer_speed = 2.0
        if input_state.left:
            self.player_x -= steer_speed * dt
        if input_state.right:
            self.player_x += steer_speed * dt

        # Clamp player position
        self.player_x = max(-1.0, min(1.0, self.player_x))

        # Apply curve effect (pushes player toward outside of curve)
        self.player_x -= self.curve * dt * 0.6

        # Update turn/straight timing
        if self.straight_timer > 0:
            # In a straight section
            self.straight_timer -= dt
            # Ease curve back to zero
            self.curve *= 0.95

            if self.straight_timer <= 0:
                # Start a new turn
                self.target_curve = random.choice([-1.5, -1.0, 1.0, 1.5])
                self.turn_duration = random.uniform(2.0, 4.0)
                self.turn_timer = 0.0
        else:
            # In a turn
            self.turn_timer += dt

            # Smoothly approach target curve
            diff = self.target_curve - self.curve
            self.curve += diff * dt * 2.0

            if self.turn_timer >= self.turn_duration:
                # End turn, start straight section
                self.straight_timer = random.uniform(1.0, 3.0)

        # Update speed (gradually increases)
        self.speed = min(self.speed + 2.0 * dt, self.max_speed)

        # Update distance and post offset
        self.distance += self.speed * dt
        self.post_offset += self.speed * dt * 0.05
        if self.post_offset >= self.POST_SPACING:
            self.post_offset -= self.POST_SPACING

        # Score based on distance
        self.score = int(self.distance)

        # Check collision with posts
        if self.check_collision():
            self.crashed = True
            self.crash_timer = 1.5

    def check_collision(self) -> bool:
        """Check if player car hits a road post."""
        return abs(self.player_x) > 0.85

    def world_to_screen(self, world_z: float, world_x: float) -> tuple:
        """Convert world coordinates to screen coordinates with perspective."""
        # world_z: 0 = at car, 1 = at horizon
        # world_x: -1 = left edge, 0 = center, 1 = right edge

        # Perspective factor
        z = max(0.01, world_z)
        perspective = 1.0 - (z * 0.9)

        # Y position (interpolate from bottom to horizon)
        screen_y = self.ROAD_BOTTOM_Y - (self.ROAD_BOTTOM_Y - self.HORIZON_Y) * (1 - perspective)

        # X position (road narrows toward horizon)
        road_half_width = (self.ROAD_WIDTH_BOTTOM / 2) * perspective + (self.ROAD_WIDTH_TOP / 2) * (1 - perspective)

        # Apply curve offset - stronger effect in distance, creates bend appearance
        # The curve shifts the vanishing point, making the road appear to bend
        curve_offset = self.curve * (1 - perspective) * (1 - perspective) * 25

        screen_x = self.VANISHING_X + world_x * road_half_width + curve_offset

        return int(screen_x), int(screen_y)

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Draw score
        self.display.draw_text_small(1, 1, f"{self.score}", Colors.WHITE)

        # Draw speed indicator
        speed_pct = int((self.speed / self.max_speed) * 99)
        self.display.draw_text_small(45, 1, f"{speed_pct}", Colors.YELLOW)

        # Draw turn indicator
        if abs(self.curve) > 0.3:
            if self.curve > 0:
                self.display.draw_text_small(30, 1, ">", Colors.CYAN)
            else:
                self.display.draw_text_small(26, 1, "<", Colors.CYAN)

        # Draw road edges (perspective lines)
        self.draw_road_edges()

        # Draw posts
        self.draw_posts()

        # Draw car
        if not self.crashed:
            self.draw_car()
        else:
            self.draw_crash()

        # Draw game over
        if self.state == GameState.GAME_OVER:
            self.display.draw_text_small(8, 25, "GAME OVER", Colors.RED)
            self.display.draw_text_small(8, 35, f"DIST:{self.score}", Colors.WHITE)

    def draw_road_edges(self):
        """Draw the road edge lines converging to vanishing point."""
        # Draw multiple segments to show the curve
        prev_lx, prev_ly = self.world_to_screen(0, -1.0)
        prev_rx, prev_ry = self.world_to_screen(0, 1.0)

        for i in range(1, 11):
            z = i / 10.0
            lx, ly = self.world_to_screen(z, -1.0)
            rx, ry = self.world_to_screen(z, 1.0)

            self.display.draw_line(prev_lx, prev_ly, lx, ly, self.ROAD_EDGE_COLOR)
            self.display.draw_line(prev_rx, prev_ry, rx, ry, self.ROAD_EDGE_COLOR)

            prev_lx, prev_ly = lx, ly
            prev_rx, prev_ry = rx, ry

    def draw_posts(self):
        """Draw the road posts with perspective, scrolling toward player."""
        for i in range(self.NUM_POSTS):
            # Calculate z position (0 = near, 1 = far)
            # Posts scroll from far to near
            z = (i * self.POST_SPACING + self.post_offset) / (self.NUM_POSTS * self.POST_SPACING)

            if z > 1.0 or z < 0.05:
                continue

            # Post size decreases with distance
            post_height = int(6 * (1 - z * 0.8))
            post_width = max(1, int(2 * (1 - z * 0.7)))

            if post_height < 1:
                continue

            # Left post
            lx, ly = self.world_to_screen(z, -1.0)
            if 0 <= lx < GRID_SIZE and 0 <= ly < GRID_SIZE:
                self.display.draw_rect(lx - post_width // 2, ly - post_height,
                                       post_width, post_height, self.POST_COLOR)

            # Right post
            rx, ry = self.world_to_screen(z, 1.0)
            if 0 <= rx < GRID_SIZE and 0 <= ry < GRID_SIZE:
                self.display.draw_rect(rx - post_width // 2, ry - post_height,
                                       post_width, post_height, self.POST_COLOR)

    def draw_car(self):
        """Draw the player's car at bottom of screen."""
        car_center_x = self.VANISHING_X + int(self.player_x * 20)
        car_x = car_center_x - self.CAR_WIDTH // 2
        car_y = self.CAR_Y

        # Car body
        self.display.draw_rect(car_x, car_y, self.CAR_WIDTH, self.CAR_HEIGHT, self.CAR_COLOR)

        # Windshield
        self.display.draw_rect(car_x + 2, car_y, 4, 2, self.CAR_WINDOW)

        # Hood details
        self.display.set_pixel(car_x + 1, car_y + 3, (150, 30, 30))
        self.display.set_pixel(car_x + 6, car_y + 3, (150, 30, 30))

    def draw_crash(self):
        """Draw crash effect."""
        car_center_x = self.VANISHING_X + int(self.player_x * 20)

        flash = int(self.crash_timer * 10) % 2
        color = Colors.YELLOW if flash else Colors.RED

        for i in range(5):
            px = car_center_x + (hash(i + int(self.crash_timer * 20)) % 12) - 6
            py = self.CAR_Y + (hash(i * 3 + int(self.crash_timer * 15)) % 8) - 4
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                self.display.set_pixel(px, py, color)
