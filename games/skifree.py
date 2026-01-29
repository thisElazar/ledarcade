"""
SkiFree - Endless Downhill Skiing
=================================
Ski down the mountain, dodge trees and rocks!
The Yeti appears at 2000m — use boost to outrun him!

Controls:
  Left/Right - Steer (diagonal skiing)
  Up         - Brake / slow down
  Button     - Speed boost (limited fuel)
"""

import random
import math
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


class SkiFree(Game):
    name = "SKIFREE"
    description = "Ski the slopes!"
    category = "retro"

    # Player constants
    PLAYER_SCREEN_Y = 48       # Fixed vertical position on screen
    BASE_SPEED = 45.0          # Pixels/sec straight downhill
    MAX_SPEED = 80.0           # Speed cap before boost
    BOOST_SPEED = 110.0        # Speed while boosting
    BRAKE_SPEED = 8.0          # Speed while braking
    LATERAL_SPEED = 50.0       # Horizontal movement speed

    # Speed multipliers by direction
    # direction: -2=hard-left, -1=diag-left, 0=down, 1=diag-right, 2=hard-right
    DIRECTION_SPEED = {
        -2: 0.15,   # Hard left — mostly lateral
        -1: 0.7,    # Diagonal left
         0: 1.0,    # Straight down — fastest
         1: 0.7,    # Diagonal right
         2: 0.15,   # Hard right — mostly lateral
    }
    DIRECTION_LATERAL = {
        -2: -1.0,
        -1: -0.5,
         0:  0.0,
         1:  0.5,
         2:  1.0,
    }

    # Boost
    BOOST_FUEL_MAX = 3.0       # Seconds of boost
    BOOST_RECHARGE = 0.3       # Fuel per second recharge

    # Crash
    CRASH_DURATION = 0.8       # Seconds frozen after crash

    # Jump
    JUMP_DURATION = 0.5        # Airborne time from ramp
    MOGUL_JUMP_DURATION = 0.2  # Small hop from mogul

    # Yeti
    YETI_SPAWN_DISTANCE = 2000  # Meters
    YETI_SPEED = 90.0           # Faster than normal max
    YETI_CATCH_DIST = 4.0       # Pixels to catch player

    # Obstacle generation
    OBSTACLE_INTERVAL_START = 30.0  # Pixels between obstacle rows (sparse)
    OBSTACLE_INTERVAL_MIN = 12.0    # Minimum spacing (dense)
    MIN_GAP = 10                    # Minimum clear gap in pixels

    # Colors
    SNOW_COLOR = (240, 240, 255)
    TREE_GREEN = (30, 160, 40)
    TREE_DARK = (20, 120, 30)
    TREE_TRUNK = (120, 70, 30)
    ROCK_COLOR = (130, 130, 140)
    ROCK_DARK = (90, 90, 100)
    MOGUL_COLOR = (210, 210, 225)
    RAMP_COLORS = [(255, 80, 80), (255, 200, 50), (50, 200, 50), (50, 150, 255)]
    SKIER_BODY = (220, 40, 40)
    SKIER_HEAD = (255, 200, 150)
    SKIER_SKI = (60, 60, 200)
    CRASH_COLOR = (255, 100, 100)
    YETI_BODY = (230, 230, 240)
    YETI_FACE = (60, 60, 80)
    BOOST_COLOR = (50, 200, 255)
    BOOST_EMPTY = (60, 60, 70)

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0

        # Player state
        self.player_x = 32.0
        self.direction = 0
        self.braking = False
        self.speed = self.BASE_SPEED

        # Crash state
        self.crashed = False
        self.crash_timer = 0.0

        # Jump state
        self.airborne = False
        self.air_timer = 0.0

        # Boost state
        self.boost_fuel = self.BOOST_FUEL_MAX
        self.boosting = False

        # Scrolling / distance
        self.scroll_speed = self.BASE_SPEED
        self.distance = 0.0         # Total pixels scrolled
        self.distance_meters = 0.0  # Displayed distance

        # Obstacles: {type, x, y, w, h}
        self.obstacles = []
        self.next_obstacle_y = GRID_SIZE + 10  # Start generating below screen

        # Pre-generate initial obstacles
        self._generate_obstacles_until(GRID_SIZE + 80)

        # Yeti
        self.yeti_active = False
        self.yeti_x = 0.0
        self.yeti_y = 0.0
        self.yeti_eating = False
        self.yeti_eat_timer = 0.0

    def _get_obstacle_interval(self):
        """Get spacing between obstacle rows based on distance."""
        # Gradually decrease interval (more dense) as distance increases
        progress = min(1.0, self.distance_meters / 3000.0)
        return self.OBSTACLE_INTERVAL_START - progress * (self.OBSTACLE_INTERVAL_START - self.OBSTACLE_INTERVAL_MIN)

    def _generate_obstacles_until(self, target_y: float):
        """Generate obstacles from current frontier down to target_y."""
        while self.next_obstacle_y < target_y:
            self._generate_obstacle_row(self.next_obstacle_y)
            self.next_obstacle_y += self._get_obstacle_interval()

    def _generate_obstacle_row(self, y: float):
        """Generate a row of obstacles at the given y position."""
        # Decide how many obstacles in this row (1-3)
        density = min(0.8, 0.3 + self.distance_meters / 4000.0)
        num_obstacles = 1
        if random.random() < density:
            num_obstacles = 2
        if random.random() < density * 0.4:
            num_obstacles = 3

        # Place obstacles with guaranteed gap
        placed = []
        attempts = 0

        for _ in range(num_obstacles):
            for _ in range(10):  # Max attempts per obstacle
                attempts += 1
                obs = self._random_obstacle(y)

                # Check gap with existing obstacles in this row
                overlaps = False
                for p in placed:
                    if abs(obs['x'] - p['x']) < self.MIN_GAP:
                        overlaps = True
                        break

                if not overlaps:
                    placed.append(obs)
                    self.obstacles.append(obs)
                    break

    def _random_obstacle(self, y: float) -> dict:
        """Create a random obstacle at given y."""
        x = random.randint(2, GRID_SIZE - 6)
        roll = random.random()

        # After Yeti spawns, more ramps to help escape
        ramp_chance = 0.08
        if self.yeti_active:
            ramp_chance = 0.15

        if roll < 0.45:
            # Small tree
            return {'type': 'small_tree', 'x': x, 'y': y, 'w': 3, 'h': 4}
        elif roll < 0.75:
            # Large tree
            return {'type': 'large_tree', 'x': x, 'y': y, 'w': 5, 'h': 6}
        elif roll < 0.88:
            # Rock
            return {'type': 'rock', 'x': x, 'y': y, 'w': 3, 'h': 2}
        elif roll < 1.0 - ramp_chance:
            # Mogul
            return {'type': 'mogul', 'x': x, 'y': y, 'w': 3, 'h': 2}
        else:
            # Jump ramp
            return {'type': 'ramp', 'x': x, 'y': y, 'w': 4, 'h': 2}

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        # Yeti eating animation
        if self.yeti_eating:
            self.yeti_eat_timer += dt
            if self.yeti_eat_timer >= 1.5:
                self.state = GameState.GAME_OVER
            return

        # Crash recovery
        if self.crashed:
            self.crash_timer -= dt
            if self.crash_timer <= 0:
                self.crashed = False
            # Yeti still moves during crash
            if self.yeti_active:
                self._update_yeti(dt)
                if self._check_yeti_catch():
                    return
            return

        # --- Input ---
        if input_state.up:
            self.braking = True
            self.direction = 0
        else:
            self.braking = False
            if input_state.left and input_state.right:
                self.direction = 0
            elif input_state.left:
                self.direction = -1
            elif input_state.right:
                self.direction = 1
            else:
                self.direction = 0

        # Boost
        if (input_state.action_l_held or input_state.action_r_held) and self.boost_fuel > 0 and not self.braking:
            self.boosting = True
            self.boost_fuel -= dt
            if self.boost_fuel < 0:
                self.boost_fuel = 0
                self.boosting = False
        else:
            self.boosting = False
            # Recharge boost fuel when not using it
            self.boost_fuel = min(self.BOOST_FUEL_MAX, self.boost_fuel + self.BOOST_RECHARGE * dt)

        # --- Speed calculation ---
        if self.braking:
            target_speed = self.BRAKE_SPEED
        elif self.boosting:
            target_speed = self.BOOST_SPEED
        else:
            # Base speed increases with distance
            progress_speed = min(self.MAX_SPEED, self.BASE_SPEED + self.distance_meters * 0.008)
            target_speed = progress_speed * self.DIRECTION_SPEED[self.direction]

        # Smooth speed transitions
        self.speed += (target_speed - self.speed) * min(1.0, dt * 5.0)

        # --- Horizontal movement ---
        lateral = self.DIRECTION_LATERAL[self.direction] * self.LATERAL_SPEED * dt
        if self.boosting:
            lateral *= 1.3  # Slightly faster lateral during boost
        self.player_x += lateral
        self.player_x = max(2, min(GRID_SIZE - 3, self.player_x))

        # --- Scroll obstacles ---
        scroll_amount = self.speed * dt
        for obs in self.obstacles:
            obs['y'] -= scroll_amount

        # --- Distance tracking ---
        self.distance += scroll_amount
        self.distance_meters = self.distance / 3.0  # Scale factor
        self.score = int(self.distance_meters)

        # --- Jump timer ---
        if self.airborne:
            self.air_timer -= dt
            if self.air_timer <= 0:
                self.airborne = False

        # --- Collision detection ---
        if not self.airborne:
            px = int(self.player_x)
            py = self.PLAYER_SCREEN_Y
            player_box = (px - 1, py - 1, 3, 4)

            for obs in self.obstacles:
                ox = int(obs['x'])
                oy = int(obs['y'])
                ow = obs['w']
                oh = obs['h']

                # Simple AABB overlap
                if (player_box[0] < ox + ow and player_box[0] + player_box[2] > ox and
                    player_box[1] < oy + oh and player_box[1] + player_box[3] > oy):

                    if obs['type'] in ('small_tree', 'large_tree', 'rock'):
                        self.crashed = True
                        self.crash_timer = self.CRASH_DURATION
                        self.speed *= 0.2
                        self.boosting = False
                        break
                    elif obs['type'] == 'mogul':
                        self.airborne = True
                        self.air_timer = self.MOGUL_JUMP_DURATION
                    elif obs['type'] == 'ramp':
                        self.airborne = True
                        self.air_timer = self.JUMP_DURATION
                        self.speed *= 1.2  # Speed boost from ramp

        # --- Generate new obstacles ---
        self._generate_obstacles_until(GRID_SIZE + 40)

        # --- Cull off-screen obstacles ---
        self.obstacles = [o for o in self.obstacles if o['y'] > -10]

        # --- Yeti ---
        if not self.yeti_active and self.distance_meters >= self.YETI_SPAWN_DISTANCE:
            self.yeti_active = True
            self.yeti_x = self.player_x
            self.yeti_y = -10  # Spawn above screen

        if self.yeti_active:
            self._update_yeti(dt)
            self._check_yeti_catch()

    def _update_yeti(self, dt: float):
        """Move Yeti toward player."""
        dx = self.player_x - self.yeti_x
        dy = self.PLAYER_SCREEN_Y - self.yeti_y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist > 0:
            # Yeti moves toward player at fixed speed
            # But also scrolls with the slope (moves up with obstacles)
            yeti_move = self.YETI_SPEED * dt
            self.yeti_x += (dx / dist) * yeti_move
            self.yeti_y += (dy / dist) * yeti_move

        # Yeti also gets pushed up by scrolling (same as obstacles)
        self.yeti_y -= self.speed * dt * 0.3  # Partial scroll — Yeti resists being scrolled away

    def _check_yeti_catch(self) -> bool:
        """Check if Yeti caught the player."""
        dx = self.player_x - self.yeti_x
        dy = self.PLAYER_SCREEN_Y - self.yeti_y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist < self.YETI_CATCH_DIST:
            self.yeti_eating = True
            self.yeti_eat_timer = 0.0
            self.yeti_x = self.player_x
            self.yeti_y = self.PLAYER_SCREEN_Y
            return True
        return False

    def draw(self):
        # Snow background
        self.display.clear(self.SNOW_COLOR)

        # Draw some snow texture (subtle dots)
        random.seed(int(self.distance / 20) * 7)
        for _ in range(20):
            sx = random.randint(0, 63)
            sy = random.randint(0, 63)
            self.display.set_pixel(sx, sy, (225, 225, 240))
        random.seed()

        # Draw obstacles (sorted by y so closer ones draw on top)
        sorted_obs = sorted(self.obstacles, key=lambda o: o['y'])
        for obs in sorted_obs:
            self._draw_obstacle(obs)

        # Draw player
        if not self.yeti_eating:
            self._draw_player()

        # Draw Yeti
        if self.yeti_active:
            self._draw_yeti()

        # Draw HUD
        self._draw_hud()

    def _draw_obstacle(self, obs: dict):
        x = int(obs['x'])
        y = int(obs['y'])

        # Skip if off screen
        if y < -8 or y > GRID_SIZE + 4:
            return

        if obs['type'] == 'small_tree':
            # Triangle tree: 3 wide, 3 tall canopy + 1 trunk
            #   X
            #  XXX
            #   X
            #   |
            if 0 <= y < GRID_SIZE:
                self.display.set_pixel(x + 1, y, self.TREE_GREEN)
            if 0 <= y + 1 < GRID_SIZE:
                for dx in range(3):
                    if 0 <= x + dx < GRID_SIZE:
                        self.display.set_pixel(x + dx, y + 1, self.TREE_GREEN)
            if 0 <= y + 2 < GRID_SIZE:
                self.display.set_pixel(x + 1, y + 2, self.TREE_DARK)
            if 0 <= y + 3 < GRID_SIZE:
                self.display.set_pixel(x + 1, y + 3, self.TREE_TRUNK)

        elif obs['type'] == 'large_tree':
            # Larger tree: 5 wide
            #    X
            #   XXX
            #  XXXXX
            #   XXX
            #    X
            #    |
            rows = [
                (2, 1),       # 1 pixel wide at top
                (1, 3),       # 3 wide
                (0, 5),       # 5 wide
                (1, 3),       # 3 wide
                (2, 1),       # 1 wide
            ]
            for i, (offset, width) in enumerate(rows):
                ry = y + i
                if 0 <= ry < GRID_SIZE:
                    color = self.TREE_GREEN if i < 3 else self.TREE_DARK
                    for dx in range(width):
                        px = x + offset + dx
                        if 0 <= px < GRID_SIZE:
                            self.display.set_pixel(px, ry, color)
            # Trunk
            if 0 <= y + 5 < GRID_SIZE and 0 <= x + 2 < GRID_SIZE:
                self.display.set_pixel(x + 2, y + 5, self.TREE_TRUNK)

        elif obs['type'] == 'rock':
            # Gray blob 3x2
            if 0 <= y < GRID_SIZE:
                for dx in range(3):
                    if 0 <= x + dx < GRID_SIZE:
                        self.display.set_pixel(x + dx, y, self.ROCK_COLOR)
            if 0 <= y + 1 < GRID_SIZE:
                if 0 <= x < GRID_SIZE:
                    self.display.set_pixel(x, y + 1, self.ROCK_DARK)
                if 0 <= x + 1 < GRID_SIZE:
                    self.display.set_pixel(x + 1, y + 1, self.ROCK_COLOR)
                if 0 <= x + 2 < GRID_SIZE:
                    self.display.set_pixel(x + 2, y + 1, self.ROCK_DARK)

        elif obs['type'] == 'mogul':
            # Small white-gray bump
            if 0 <= y < GRID_SIZE:
                for dx in range(3):
                    if 0 <= x + dx < GRID_SIZE:
                        self.display.set_pixel(x + dx, y, self.MOGUL_COLOR)
            if 0 <= y + 1 < GRID_SIZE:
                if 0 <= x + 1 < GRID_SIZE:
                    self.display.set_pixel(x + 1, y + 1, (200, 200, 215))

        elif obs['type'] == 'ramp':
            # Rainbow stripe ramp
            if 0 <= y < GRID_SIZE:
                for dx in range(4):
                    if 0 <= x + dx < GRID_SIZE:
                        self.display.set_pixel(x + dx, y, self.RAMP_COLORS[dx % len(self.RAMP_COLORS)])
            if 0 <= y + 1 < GRID_SIZE:
                for dx in range(4):
                    if 0 <= x + dx < GRID_SIZE:
                        c = self.RAMP_COLORS[(dx + 1) % len(self.RAMP_COLORS)]
                        self.display.set_pixel(x + dx, y + 1, c)

    def _draw_player(self):
        px = int(self.player_x)
        py = self.PLAYER_SCREEN_Y

        if self.crashed:
            # Tumble sprite — sprawled out
            if 0 <= py < GRID_SIZE:
                self.display.set_pixel(px, py, self.CRASH_COLOR)
            if 0 <= py + 1 < GRID_SIZE:
                for dx in [-1, 0, 1]:
                    if 0 <= px + dx < GRID_SIZE:
                        self.display.set_pixel(px + dx, py + 1, self.CRASH_COLOR)
            if 0 <= py + 2 < GRID_SIZE:
                self.display.set_pixel(px, py + 2, self.SKIER_SKI)
            return

        if self.airborne:
            # Airborne — spread eagle with shadow
            # Shadow on ground
            if 0 <= py + 3 < GRID_SIZE:
                self.display.set_pixel(px, py + 3, (180, 180, 195))
            # Skier raised up
            jump_py = py - 3
        else:
            jump_py = py

        if self.direction == 0:
            # Straight down
            #  O
            # /|\
            #  |
            # / \
            if 0 <= jump_py < GRID_SIZE:
                self.display.set_pixel(px, jump_py, self.SKIER_HEAD)
            if 0 <= jump_py + 1 < GRID_SIZE:
                self.display.set_pixel(px, jump_py + 1, self.SKIER_BODY)
                for dx in [-1, 1]:
                    if 0 <= px + dx < GRID_SIZE:
                        self.display.set_pixel(px + dx, jump_py + 1, self.SKIER_BODY)
            if 0 <= jump_py + 2 < GRID_SIZE:
                self.display.set_pixel(px, jump_py + 2, self.SKIER_BODY)
            if 0 <= jump_py + 3 < GRID_SIZE:
                for dx in [-1, 1]:
                    if 0 <= px + dx < GRID_SIZE:
                        self.display.set_pixel(px + dx, jump_py + 3, self.SKIER_SKI)

        elif self.direction in (-1, -2):
            # Leaning left
            #  O
            # /|
            # /
            # |
            if 0 <= jump_py < GRID_SIZE:
                self.display.set_pixel(px, jump_py, self.SKIER_HEAD)
            if 0 <= jump_py + 1 < GRID_SIZE:
                self.display.set_pixel(px, jump_py + 1, self.SKIER_BODY)
                if 0 <= px - 1 < GRID_SIZE:
                    self.display.set_pixel(px - 1, jump_py + 1, self.SKIER_BODY)
            if 0 <= jump_py + 2 < GRID_SIZE:
                if 0 <= px - 1 < GRID_SIZE:
                    self.display.set_pixel(px - 1, jump_py + 2, self.SKIER_SKI)
            if 0 <= jump_py + 3 < GRID_SIZE:
                self.display.set_pixel(px, jump_py + 3, self.SKIER_SKI)

        elif self.direction in (1, 2):
            # Leaning right
            # O
            # |\
            #   \
            #   |
            if 0 <= jump_py < GRID_SIZE:
                self.display.set_pixel(px, jump_py, self.SKIER_HEAD)
            if 0 <= jump_py + 1 < GRID_SIZE:
                self.display.set_pixel(px, jump_py + 1, self.SKIER_BODY)
                if 0 <= px + 1 < GRID_SIZE:
                    self.display.set_pixel(px + 1, jump_py + 1, self.SKIER_BODY)
            if 0 <= jump_py + 2 < GRID_SIZE:
                if 0 <= px + 1 < GRID_SIZE:
                    self.display.set_pixel(px + 1, jump_py + 2, self.SKIER_SKI)
            if 0 <= jump_py + 3 < GRID_SIZE:
                self.display.set_pixel(px, jump_py + 3, self.SKIER_SKI)

        # Boost trail
        if self.boosting and not self.airborne:
            trail_color = (180, 220, 255)
            for i in range(3):
                ty = py - 2 - i
                if 0 <= ty < GRID_SIZE:
                    self.display.set_pixel(px, ty, trail_color)

    def _draw_yeti(self):
        yx = int(self.yeti_x)
        yy = int(self.yeti_y)

        if self.yeti_eating:
            # Eating animation — big yeti over player
            px = int(self.player_x)
            py = self.PLAYER_SCREEN_Y

            # Yeti body (larger during eat)
            for dy in range(-2, 4):
                for dx in range(-2, 3):
                    ppx = px + dx
                    ppy = py + dy
                    if 0 <= ppx < GRID_SIZE and 0 <= ppy < GRID_SIZE:
                        self.display.set_pixel(ppx, ppy, self.YETI_BODY)
            # Face
            if 0 <= py - 1 < GRID_SIZE:
                if 0 <= px - 1 < GRID_SIZE:
                    self.display.set_pixel(px - 1, py - 1, self.YETI_FACE)
                if 0 <= px + 1 < GRID_SIZE:
                    self.display.set_pixel(px + 1, py - 1, self.YETI_FACE)
            # Mouth
            if 0 <= py < GRID_SIZE:
                self.display.set_pixel(px, py, (200, 50, 50))
            return

        # Normal Yeti — chasing
        # Head
        if 0 <= yy < GRID_SIZE:
            for dx in range(-1, 2):
                if 0 <= yx + dx < GRID_SIZE:
                    self.display.set_pixel(yx + dx, yy, self.YETI_BODY)
        # Eyes
        if 0 <= yy + 1 < GRID_SIZE:
            if 0 <= yx - 1 < GRID_SIZE:
                self.display.set_pixel(yx - 1, yy + 1, self.YETI_FACE)
            self.display.set_pixel(yx, yy + 1, self.YETI_BODY)
            if 0 <= yx + 1 < GRID_SIZE:
                self.display.set_pixel(yx + 1, yy + 1, self.YETI_FACE)
        # Body
        for dy in range(2, 4):
            if 0 <= yy + dy < GRID_SIZE:
                for dx in range(-1, 2):
                    if 0 <= yx + dx < GRID_SIZE:
                        self.display.set_pixel(yx + dx, yy + dy, self.YETI_BODY)
        # Legs
        if 0 <= yy + 4 < GRID_SIZE:
            if 0 <= yx - 1 < GRID_SIZE:
                self.display.set_pixel(yx - 1, yy + 4, self.YETI_BODY)
            if 0 <= yx + 1 < GRID_SIZE:
                self.display.set_pixel(yx + 1, yy + 4, self.YETI_BODY)

    def _draw_hud(self):
        """Draw distance and boost meter."""
        # Dark bar at top for readability
        self.display.draw_rect(0, 0, GRID_SIZE, 7, (0, 0, 0))

        # Distance
        dist_str = f"{int(self.distance_meters)}M"
        self.display.draw_text_small(1, 1, dist_str, Colors.WHITE)

        # Yeti warning
        if self.yeti_active:
            self.display.draw_text_small(28, 1, "YETI", Colors.RED)

        # Boost meter (right side, 10px wide bar)
        bar_x = 53
        bar_w = 10
        bar_h = 3
        bar_y = 2

        # Background
        self.display.draw_rect(bar_x, bar_y, bar_w, bar_h, self.BOOST_EMPTY)

        # Fuel level
        fuel_pct = self.boost_fuel / self.BOOST_FUEL_MAX
        fuel_w = int(bar_w * fuel_pct)
        if fuel_w > 0:
            self.display.draw_rect(bar_x, bar_y, fuel_w, bar_h, self.BOOST_COLOR)

    def draw_game_over(self):
        self.display.clear(Colors.BLACK)
        self.display.draw_text_small(8, 16, "GAME OVER", Colors.RED)

        if self.yeti_active:
            self.display.draw_text_small(4, 28, "YETI GOT YOU", Colors.WHITE)
        else:
            self.display.draw_text_small(8, 28, f"DIST:{self.score}M", Colors.WHITE)

        self.display.draw_text_small(4, 50, "BTN:RETRY", Colors.GRAY)
