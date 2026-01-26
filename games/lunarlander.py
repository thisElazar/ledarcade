"""
Lunar Lander - Arcade Classic
==============================
Land safely on the moon!

Controls:
  Left/Right - Rotate lander
  Space      - Main thrust (direction lander is pointing)
"""

from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE
import random
import math


class LunarLander(Game):
    name = "LUNAR LANDER"
    description = "Moon Landing"
    category = "arcade"

    # Physics
    GRAVITY = 10.0           # Pixels per second squared (floatier)
    THRUST = 28.0            # Main engine thrust
    ROTATION_SPEED = 3.0     # Radians per second
    MAX_LANDING_SPEED = 20.0   # Max vertical speed for safe landing
    MAX_LATERAL_SPEED = 15.0   # Max horizontal speed for safe landing
    MAX_LANDING_ANGLE = 0.21   # Max angle from vertical for safe landing (~12 degrees)

    # Fuel
    STARTING_FUEL = 200.0
    THRUST_FUEL_RATE = 25.0    # Fuel per second of thrust

    # Lander
    LANDER_WIDTH = 6
    LANDER_HEIGHT = 5

    # Colors
    TERRAIN_COLOR = (100, 80, 60)
    LANDER_COLOR = (200, 200, 220)
    THRUST_COLOR = (255, 150, 50)
    PAD_COLOR = (50, 200, 50)
    PAD_2X_COLOR = (200, 200, 50)
    PAD_5X_COLOR = (200, 50, 200)
    FUEL_COLOR = (50, 150, 255)
    DANGER_COLOR = Colors.RED

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0

        # Lander state
        self.x = 32.0
        self.y = 8.0
        self.vx = random.uniform(-3, 3)  # Initial horizontal velocity
        self.vy = 0.0
        self.angle = random.uniform(-0.3, 0.3)  # Initial angle (radians, 0 = pointing up)
        self.fuel = self.STARTING_FUEL

        # Thrust state (for visuals)
        self.thrusting = False

        # Generate terrain and landing pads
        self.generate_terrain()

        # Landing state
        self.landed = False
        self.crashed = False
        self.landing_pad = None
        self.landing_multiplier = 1

    def generate_terrain(self):
        """Generate random terrain with landing pads."""
        self.terrain = []
        self.pads = []  # List of (x_start, x_end, multiplier)

        # Generate terrain heights
        y = 55  # Start near bottom
        x = 0

        # Decide pad positions (2-3 pads)
        num_pads = random.randint(2, 3)
        pad_positions = sorted(random.sample(range(1, 6), num_pads))
        pad_widths = [random.randint(8, 12) for _ in pad_positions]
        pad_multipliers = [1, 2, 5][:num_pads]
        random.shuffle(pad_multipliers)

        segment_width = GRID_SIZE // 6
        current_pad_idx = 0

        while x < GRID_SIZE:
            segment = x // segment_width

            if current_pad_idx < num_pads and segment == pad_positions[current_pad_idx]:
                # Landing pad - flat area
                pad_width = pad_widths[current_pad_idx]
                pad_x_start = x
                pad_y = y

                for _ in range(pad_width):
                    if x < GRID_SIZE:
                        self.terrain.append(pad_y)
                        x += 1

                self.pads.append((pad_x_start, x - 1, pad_y, pad_multipliers[current_pad_idx]))
                current_pad_idx += 1
            else:
                # Random terrain
                steps = random.randint(3, 8)
                for _ in range(steps):
                    if x < GRID_SIZE:
                        self.terrain.append(y)
                        x += 1
                        # Vary height
                        y += random.randint(-2, 2)
                        y = max(45, min(60, y))

        # Ensure terrain covers full width
        while len(self.terrain) < GRID_SIZE:
            self.terrain.append(self.terrain[-1])

    def get_terrain_height(self, x: int) -> int:
        """Get terrain height at x position."""
        x = int(max(0, min(GRID_SIZE - 1, x)))
        return self.terrain[x]

    def check_landing(self) -> tuple:
        """Check if lander has landed or crashed. Returns (landed, crashed, pad)."""
        lander_bottom = self.y + self.LANDER_HEIGHT
        lander_left = int(self.x - self.LANDER_WIDTH // 2)
        lander_right = int(self.x + self.LANDER_WIDTH // 2)

        # Check terrain collision
        for x in range(lander_left, lander_right + 1):
            if 0 <= x < GRID_SIZE:
                terrain_y = self.get_terrain_height(x)
                if lander_bottom >= terrain_y:
                    # Collision! Check if it's a safe landing
                    on_pad = None
                    lander_center = int(self.x)
                    for pad_x_start, pad_x_end, pad_y, multiplier in self.pads:
                        # Check if lander center is on pad (more forgiving)
                        if pad_x_start <= lander_center <= pad_x_end:
                            on_pad = (pad_x_start, pad_x_end, pad_y, multiplier)
                            break

                    if on_pad is None:
                        return False, True, None  # Crashed on terrain

                    # Check landing speed
                    if abs(self.vy) > self.MAX_LANDING_SPEED:
                        return False, True, on_pad  # Too fast vertically
                    if abs(self.vx) > self.MAX_LATERAL_SPEED:
                        return False, True, on_pad  # Too fast horizontally
                    # Check landing angle (must be roughly upright)
                    if abs(self.angle) > self.MAX_LANDING_ANGLE:
                        return False, True, on_pad  # Too tilted

                    # Safe landing!
                    return True, False, on_pad

        return False, False, None

    def update(self, input_state: InputState, dt: float):
        if self.state == GameState.GAME_OVER:
            if input_state.action:
                self.reset()
            return

        # Landed - show success screen, wait for click to play again
        if self.landed:
            if input_state.action:
                self.reset()
            return

        if self.crashed:
            return

        # Reset thrust visuals
        self.thrusting = False

        # Rotation (left/right rotates the lander)
        if input_state.left:
            self.angle -= self.ROTATION_SPEED * dt
        if input_state.right:
            self.angle += self.ROTATION_SPEED * dt

        # Main thrust (pushes in direction lander is pointing)
        if input_state.action_held and self.fuel > 0:
            # Thrust direction: angle=0 means pointing up, so thrust is up
            # angle>0 means tilted right, thrust pushes up-right
            self.vx += math.sin(self.angle) * self.THRUST * dt
            self.vy -= math.cos(self.angle) * self.THRUST * dt
            self.fuel -= self.THRUST_FUEL_RATE * dt
            self.thrusting = True

        # Clamp fuel
        self.fuel = max(0, self.fuel)

        # Apply gravity
        self.vy += self.GRAVITY * dt

        # Update position
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Screen wrapping (horizontal)
        if self.x < 0:
            self.x = GRID_SIZE - 1
        elif self.x >= GRID_SIZE:
            self.x = 0

        # Check landing/crash
        landed, crashed, pad = self.check_landing()

        if landed:
            self.landed = True
            self.landing_pad = pad
            self.landing_multiplier = pad[3]
            self.score = int(100 * self.landing_multiplier + self.fuel)
            # Don't set GAME_OVER yet - show landed screen first
        elif crashed:
            self.crashed = True
            self.state = GameState.GAME_OVER

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Draw terrain
        self.draw_terrain()

        # Draw lander
        if not self.crashed:
            self.draw_lander()
        else:
            self.draw_explosion()

        # Draw HUD
        self.draw_hud()

        # Draw landed success screen
        if self.landed:
            self.display.draw_text_small(16, 16, "LANDED!", Colors.GREEN)
            mult_text = f"{self.landing_multiplier}X BONUS"
            self.display.draw_text_small(8, 26, mult_text, Colors.YELLOW)
            self.display.draw_text_small(8, 36, f"SCORE: {self.score}", Colors.WHITE)
            self.display.draw_text_small(4, 50, "PRESS SPACE", Colors.GRAY)

        # Draw crash message
        elif self.state == GameState.GAME_OVER:
            self.display.draw_text_small(16, 20, "CRASHED!", Colors.RED)

    def draw_terrain(self):
        """Draw the terrain and landing pads."""
        # Draw terrain
        for x in range(GRID_SIZE):
            terrain_y = self.terrain[x]
            # Fill from terrain to bottom
            for y in range(terrain_y, GRID_SIZE):
                self.display.set_pixel(x, y, self.TERRAIN_COLOR)

        # Draw landing pads
        for pad_x_start, pad_x_end, pad_y, multiplier in self.pads:
            if multiplier == 1:
                color = self.PAD_COLOR
            elif multiplier == 2:
                color = self.PAD_2X_COLOR
            else:
                color = self.PAD_5X_COLOR

            # Draw pad surface
            for x in range(pad_x_start, pad_x_end + 1):
                self.display.set_pixel(x, pad_y - 1, color)
                self.display.set_pixel(x, pad_y, color)

            # Draw multiplier indicator
            mid_x = (pad_x_start + pad_x_end) // 2
            self.display.draw_text_small(mid_x - 2, pad_y - 7, f"{multiplier}X", color)

    def draw_lander(self):
        """Draw the lunar lander with rotation."""
        cx = int(self.x)
        cy = int(self.y + 3)  # Center point (adjusted for sprite)

        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)

        def rotate_point(px, py):
            """Rotate point around center."""
            rx = cx + int(px * cos_a - py * sin_a)
            ry = cy + int(px * sin_a + py * cos_a)
            return rx, ry

        # Lander body pixels (relative to center)
        # Negative y = toward top of lander, positive y = toward engine
        body_pixels = [
            (0, -3),   # Top of cabin
            (-1, -2), (0, -2), (1, -2),  # Upper cabin
            (-1, -1), (0, -1), (1, -1),  # Lower cabin
        ]

        # Legs (extend down and out)
        leg_pixels = [
            (-1, 0), (1, 0),      # Leg attachment
            (-2, 1), (2, 1),      # Leg feet
        ]

        # Draw body
        for px, py in body_pixels:
            rx, ry = rotate_point(px, py)
            if 0 <= rx < GRID_SIZE and 0 <= ry < GRID_SIZE:
                self.display.set_pixel(rx, ry, self.LANDER_COLOR)

        # Draw legs
        for px, py in leg_pixels:
            rx, ry = rotate_point(px, py)
            if 0 <= rx < GRID_SIZE and 0 <= ry < GRID_SIZE:
                self.display.set_pixel(rx, ry, self.LANDER_COLOR)

        # Thrust flame (extends from bottom, opposite to thrust direction)
        if self.thrusting:
            flame_len = random.randint(2, 4)
            # Flame comes out bottom of lander (opposite to thrust direction)
            # Start from bottom of lander (y=+2 relative to center) then extend outward
            for i in range(flame_len):
                # Base position at bottom of lander, then extend in opposite direction of thrust
                dist = 2 + i
                fx = cx + int(-sin_a * dist)  # Opposite x direction from thrust
                fy = cy + int(cos_a * dist)   # Opposite y direction from thrust
                if 0 <= fx < GRID_SIZE and 0 <= fy < GRID_SIZE:
                    self.display.set_pixel(fx, fy, self.THRUST_COLOR)

    def draw_explosion(self):
        """Draw crash explosion."""
        cx = int(self.x)
        cy = int(self.y)

        for i in range(8):
            px = cx + random.randint(-4, 4)
            py = cy + random.randint(-2, 4)
            color = Colors.YELLOW if random.random() > 0.5 else Colors.RED
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                self.display.set_pixel(px, py, color)

    def draw_hud(self):
        """Draw fuel gauge and velocity indicators."""
        # Fuel bar
        fuel_pct = self.fuel / self.STARTING_FUEL
        fuel_width = int(20 * fuel_pct)
        fuel_color = self.FUEL_COLOR if fuel_pct > 0.25 else self.DANGER_COLOR

        self.display.draw_text_small(1, 1, "F", fuel_color)
        self.display.draw_rect(6, 1, fuel_width, 4, fuel_color)

        # Velocity indicator
        speed = math.sqrt(self.vx * self.vx + self.vy * self.vy)
        speed_color = Colors.GREEN if speed < self.MAX_LANDING_SPEED else self.DANGER_COLOR

        # Vertical speed indicator (arrow)
        if self.vy > 2:
            self.display.draw_text_small(56, 1, "v", speed_color)
        elif self.vy < -2:
            self.display.draw_text_small(56, 1, "^", speed_color)

        # Angle indicator (shows if tilted too much)
        angle_ok = abs(self.angle) <= self.MAX_LANDING_ANGLE
        angle_color = Colors.GREEN if angle_ok else self.DANGER_COLOR
        if self.angle > 0.1:
            self.display.draw_text_small(30, 1, ">", angle_color)
        elif self.angle < -0.1:
            self.display.draw_text_small(30, 1, "<", angle_color)
