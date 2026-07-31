"""
Lunar Lander - Arcade Classic
==============================
Land safely on the moon! One shared fuel tank — make it last.

Controls:
  Left/Right - Rotate lander
  Space      - Low burn (gentle thrust)
  Z          - Full burn

Progression:
  - One shared fuel tank across all attempts (like the original)
  - Each successful landing advances the level and pays fuel into the
    tank (harder pads pay more); higher levels have more gravity,
    rougher terrain, and smaller pads
  - Crashing scores nothing and drains fuel - then a new terrain appears
  - Game ends when the fuel is gone and the lander is down
"""

from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE
import random
import math


class LunarLander(Game):
    name = "LUNAR LANDER"
    description = "Moon Landing"
    category = "arcade"
    GUIDE = {
        'desc': 'Fly attempt after attempt on one shared fuel tank. Left button is a gentle low burn, right button a full burn. Soft-land upright on a pad for full points and a fuel payout (harder pads pay more); land hard for half points. Crashes score nothing and drain 30 fuel from the tank — the game ends when the tank runs dry. The view zooms 2x for the final approach.',
        'controls': {
            'Left/Right': 'Rotate lander',
            'Left button': 'Low burn',
            'Right button': 'Full burn',
        },
    }

    # Base physics (modified by level)
    BASE_GRAVITY = 8.0           # Pixels per second squared
    BASE_THRUST = 28.0           # Main engine thrust
    ROTATION_SPEED = 3.0         # Radians per second
    MAX_LANDING_SPEED = 18.0     # Max vertical speed for safe landing
    MAX_LATERAL_SPEED = 12.0     # Max horizontal speed for safe landing
    MAX_LANDING_ANGLE = 0.21     # Max angle from vertical for safe landing (~12 degrees)

    # Fuel — one shared tank across all attempts
    BASE_FUEL = 250.0
    FUEL_MAX = 400.0             # Tank capacity (gauge maximum)
    THRUST_FUEL_RATE = 25.0      # Fuel per second of full thrust
    LOW_BURN = 0.4               # Low-burn throttle fraction (thrust and fuel)

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
        self.level = 1
        self.landings = 0
        # The shared fuel tank — filled once here, never reset per attempt
        self.fuel = self.BASE_FUEL
        self.start_new_descent()

    def start_new_descent(self):
        """Start a new descent attempt (after a landing or a crash).

        Deliberately does NOT touch self.fuel — the tank is shared across
        attempts; difficulty escalates through terrain, not fuel cuts.
        """
        # Calculate level-based difficulty
        level_factor = min(self.level, 10)  # Cap at level 10 difficulty

        # Physics get harder: more gravity
        self.gravity = self.BASE_GRAVITY + (level_factor - 1) * 1.5

        # Lander state
        self.x = 32.0
        self.y = 8.0
        # Higher levels start with more lateral velocity
        self.vx = random.uniform(-3 - level_factor * 0.5, 3 + level_factor * 0.5)
        self.vy = 0.0
        self.angle = random.uniform(-0.3, 0.3)

        # Thrust state (for visuals)
        self.thrusting = False
        self.thrust_level = 0.0

        # Generate terrain and landing pads
        self.generate_terrain()

        # Landing state
        self.landed = False
        self.crashed = False
        self.crash_timer = 0.0
        self.landing_pad = None
        self.landing_multiplier = 1
        self.landing_bonus = 0
        self.landing_quality = 'GOOD'
        self.landing_fuel_gain = 0

    def generate_terrain(self):
        """Generate random terrain with landing pads. Difficulty scales with level."""
        self.terrain = []
        self.pads = []  # List of (x_start, x_end, multiplier)

        level_factor = min(self.level, 10)

        # Generate terrain heights
        y = 55  # Start near bottom
        x = 0

        # Decide pad positions (fewer pads at higher levels)
        if self.level <= 3:
            num_pads = 3
        elif self.level <= 6:
            num_pads = 2
        else:
            num_pads = random.choice([1, 2])

        pad_positions = sorted(random.sample(range(1, 6), min(num_pads, 5)))

        # Pad widths shrink at higher levels
        base_width = max(12 - level_factor, 6)
        pad_widths = [random.randint(base_width, base_width + 4) for _ in pad_positions]

        # Point multipliers (smaller pads = more points)
        pad_multipliers = []
        for w in pad_widths:
            if w <= 7:
                pad_multipliers.append(5)
            elif w <= 9:
                pad_multipliers.append(2)
            else:
                pad_multipliers.append(1)

        segment_width = GRID_SIZE // 6
        current_pad_idx = 0

        # Terrain roughness increases with level (the difficulty lever,
        # now that the fuel tank is no longer cut per level)
        max_height_change = min(2 + level_factor // 2, 6)

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
                # Random terrain (rougher at higher levels)
                steps = random.randint(2, 6)
                for _ in range(steps):
                    if x < GRID_SIZE:
                        self.terrain.append(y)
                        x += 1
                        # Vary height (more at higher levels)
                        y += random.randint(-max_height_change, max_height_change)
                        y = max(42, min(60, y))

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
            if (input_state.action_l or input_state.action_r):
                self.reset()
            return

        # Landed - show success screen, wait for click to advance to next level
        if self.landed:
            if (input_state.action_l or input_state.action_r):
                self.level += 1
                self.start_new_descent()
            return

        if self.crashed:
            # Brief crash message, then a fresh terrain — the shared fuel
            # pool is untouched. Down with an empty tank ends the game.
            self.crash_timer -= dt
            if self.crash_timer <= 0:
                if self.fuel <= 0:
                    self.state = GameState.GAME_OVER
                else:
                    self.start_new_descent()
            return

        # Reset thrust visuals
        self.thrusting = False
        self.thrust_level = 0.0

        # Rotation (left/right rotates the lander)
        if input_state.left:
            self.angle -= self.ROTATION_SPEED * dt
        if input_state.right:
            self.angle += self.ROTATION_SPEED * dt

        # Two-level throttle: left button = low burn, right button = full
        # burn (both held = full). Thrust and fuel scale together.
        if self.fuel > 0:
            if input_state.action_r_held:
                self.thrust_level = 1.0
            elif input_state.action_l_held:
                self.thrust_level = self.LOW_BURN
        if self.thrust_level > 0:
            # Thrust direction: angle=0 means pointing up, so thrust is up
            # angle>0 means tilted right, thrust pushes up-right
            self.vx += math.sin(self.angle) * self.BASE_THRUST * self.thrust_level * dt
            self.vy -= math.cos(self.angle) * self.BASE_THRUST * self.thrust_level * dt
            self.fuel -= self.THRUST_FUEL_RATE * self.thrust_level * dt
            self.thrusting = True

        # Clamp fuel
        self.fuel = max(0, self.fuel)

        # Apply gravity (scales with level)
        self.vy += self.gravity * dt

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
            # Landing quality: soft touchdowns pay full, hard ones half
            if abs(self.vy) < 8.0:
                self.landing_quality = 'GOOD'
                self.landing_bonus = 50 * self.landing_multiplier
            else:
                self.landing_quality = 'HARD'
                self.landing_bonus = 25 * self.landing_multiplier
            self.score += self.landing_bonus
            # Landing pays fuel into the shared tank, not points
            gain = 50 * self.landing_multiplier
            self.landing_fuel_gain = int(min(self.FUEL_MAX - self.fuel, gain))
            self.fuel = min(self.FUEL_MAX, self.fuel + gain)
            self.landings += 1
            # Don't set GAME_OVER yet - show landed screen, then advance level
        elif crashed:
            self.crashed = True
            self.crash_timer = 2.0
            self.fuel = max(0, self.fuel - 30)  # Wrecked landers cost fuel

    def zoomed(self) -> bool:
        """2x view for the final approach — when close above the ground."""
        alt = self.get_terrain_height(int(self.x)) - (self.y + self.LANDER_HEIGHT)
        return alt < 14

    def draw(self):
        self.display.clear(Colors.BLACK)

        zoom = self.zoomed()

        # Draw terrain
        self.draw_terrain(zoom)

        # Draw lander
        if not self.crashed:
            self.draw_lander(zoom)
        else:
            self.draw_explosion(zoom)

        # Draw HUD
        self.draw_hud()

        # Draw landed success screen
        if self.landed:
            quality_color = Colors.GREEN if self.landing_quality == 'GOOD' else Colors.ORANGE
            self.display.draw_text_small(8, 14, f"{self.landing_quality} LANDING", quality_color)
            self.display.draw_text_small(10, 24, f"+{self.landing_bonus}", Colors.YELLOW)
            if self.landing_multiplier > 1:
                self.display.draw_text_small(35, 24, f"{self.landing_multiplier}X", Colors.CYAN)
            self.display.draw_text_small(4, 34, f"FUEL+{self.landing_fuel_gain}", self.FUEL_COLOR)
            self.display.draw_text_small(4, 44, f"NEXT:LV{self.level + 1}", Colors.GRAY)
            self.display.draw_text_small(8, 54, "PRESS BTN", Colors.GRAY)

        # Brief crash message (the fuel penalty, then a fresh terrain)
        elif self.crashed and self.state != GameState.GAME_OVER:
            self.display.draw_text_small(16, 16, "CRASHED", Colors.RED)
            self.display.draw_text_small(16, 26, "FUEL-30", self.FUEL_COLOR)

    def draw_terrain(self, zoom: bool = False):
        """Draw the terrain and landing pads (2x centered on lander if zoomed)."""
        if not zoom:
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
            return

        # Zoomed: each screen column samples half a world pixel; the lander
        # world center maps to screen (32, 28)
        cy = self.y + 3
        for px in range(GRID_SIZE):
            wx = self.x + (px - 32) / 2.0
            col = int(max(0, min(GRID_SIZE - 1, wx)))
            terrain_y = self.terrain[col]

            # Pad columns get their marker color on the top rows
            pad_color = None
            for pad_x_start, pad_x_end, pad_y, multiplier in self.pads:
                if pad_x_start <= col <= pad_x_end:
                    if multiplier == 1:
                        pad_color = self.PAD_COLOR
                    elif multiplier == 2:
                        pad_color = self.PAD_2X_COLOR
                    else:
                        pad_color = self.PAD_5X_COLOR
                    break

            sy_top = 28 + int((terrain_y - cy) * 2)
            for sy in range(max(0, sy_top), GRID_SIZE):
                if pad_color is not None and sy < sy_top + 4:
                    self.display.set_pixel(px, sy, pad_color)
                else:
                    self.display.set_pixel(px, sy, self.TERRAIN_COLOR)

    def draw_lander(self, zoom: bool = False):
        """Draw the lunar lander with rotation (2x at screen center if zoomed)."""
        if zoom:
            cx, cy, s = 32, 28, 2
        else:
            cx = int(self.x)
            cy = int(self.y + 3)  # Center point (adjusted for sprite)
            s = 1

        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)

        def rotate_point(px, py):
            """Rotate point around center (scaled)."""
            rx = cx + int((px * cos_a - py * sin_a) * s)
            ry = cy + int((px * sin_a + py * cos_a) * s)
            return rx, ry

        def plot(rx, ry, color):
            """Draw an s x s block (set_pixel clips off-screen)."""
            for oy in range(s):
                for ox in range(s):
                    self.display.set_pixel(rx + ox, ry + oy, color)

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
            plot(rx, ry, self.LANDER_COLOR)

        # Draw legs
        for px, py in leg_pixels:
            rx, ry = rotate_point(px, py)
            plot(rx, ry, self.LANDER_COLOR)

        # Thrust flame (extends from bottom, opposite to thrust direction)
        if self.thrusting:
            # Full burn throws a longer flame than a low burn
            if self.thrust_level >= 1.0:
                flame_len = random.randint(2, 4)
            else:
                flame_len = random.randint(1, 2)
            # Flame comes out bottom of lander (opposite to thrust direction)
            # Start from bottom of lander (y=+2 relative to center) then extend outward
            for i in range(flame_len):
                # Base position at bottom of lander, then extend in opposite direction of thrust
                dist = 2 + i
                fx = cx + int(-sin_a * dist * s)  # Opposite x direction from thrust
                fy = cy + int(cos_a * dist * s)   # Opposite y direction from thrust
                plot(fx, fy, self.THRUST_COLOR)

    def draw_explosion(self, zoom: bool = False):
        """Draw crash explosion."""
        if zoom:
            cx, cy = 32, 28
        else:
            cx = int(self.x)
            cy = int(self.y)

        for i in range(8):
            px = cx + random.randint(-4, 4)
            py = cy + random.randint(-2, 4)
            color = Colors.YELLOW if random.random() > 0.5 else Colors.RED
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                self.display.set_pixel(px, py, color)

    def draw_hud(self):
        """Draw fuel gauge, level, score, and velocity indicators."""
        # Level indicator
        self.display.draw_text_small(1, 1, f"L{self.level}", Colors.WHITE)

        # Fuel bar (fixed gauge maximum so the bar is honest)
        fuel_pct = min(1.0, self.fuel / self.FUEL_MAX)
        fuel_width = int(16 * fuel_pct)
        fuel_color = self.FUEL_COLOR if fuel_pct > 0.25 else self.DANGER_COLOR
        self.display.draw_rect(14, 1, fuel_width, 4, fuel_color)

        # Score (top right)
        score_str = str(self.score)
        self.display.draw_text_small(64 - len(score_str) * 4, 1, score_str, Colors.YELLOW)

        # Velocity indicator
        speed = math.sqrt(self.vx * self.vx + self.vy * self.vy)
        speed_color = Colors.GREEN if speed < self.MAX_LANDING_SPEED else self.DANGER_COLOR

        # Vertical speed indicator (arrow) - bottom left
        if self.vy > 2:
            self.display.draw_text_small(1, 58, "v", speed_color)
        elif self.vy < -2:
            self.display.draw_text_small(1, 58, "^", speed_color)

        # Angle indicator (shows if tilted too much)
        angle_ok = abs(self.angle) <= self.MAX_LANDING_ANGLE
        angle_color = Colors.GREEN if angle_ok else self.DANGER_COLOR
        if self.angle > 0.1:
            self.display.draw_text_small(8, 58, ">", angle_color)
        elif self.angle < -0.1:
            self.display.draw_text_small(8, 58, "<", angle_color)
