"""
SkiFree - Endless Downhill Skiing
=================================
Ski down the mountain, dodge trees and rocks!
The Yeti appears at 750m — use boost to outrun him!

Controls:
  Left/Right - Steer (hold ~0.4s to carve into a hard turn)
  Up         - Brake / slow down
  Button     - Speed boost (limited fuel)
  Button (in air) - Flip trick (land it for style!)
"""

import random
import math
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


class SkiFree(Game):
    name = "SKI RUN"
    description = "Ski the slopes!"
    category = "retro"
    GUIDE = {
        'desc': 'Ski downhill, dodging trees, rocks, wandering dogs, and rival skiers. Hold a turn to carve hard. Slalom gates and ramp flips (press the button mid-air, land it clean) build STYLE points. The Abominable Snowman appears at 750m and sprints faster than plain skiing - boost is your only escape.',
    }

    # Player constants
    PLAYER_Y_MIN = 20          # Highest screen position (skiing fast)
    PLAYER_Y_MAX = 50          # Lowest screen position (skiing slow)
    PLAYER_Y_DEFAULT = 35      # Default screen position
    BASE_SPEED = 45.0          # Pixels/sec straight downhill
    MAX_SPEED = 80.0           # Speed cap before boost
    BOOST_SPEED = 110.0        # Speed while boosting
    PLAYER_Y_SPEED = 40.0      # How fast player moves up/down on screen
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
    CRASH_DURATION = 0.8       # Seconds tumbling after crash
    INVULN_DURATION = 0.5      # Brief invulnerability after crash recovery

    # Jump
    JUMP_DURATION = 0.5        # Airborne time from ramp
    MOGUL_JUMP_DURATION = 0.2  # Small hop from mogul

    # Hard turn: hold a direction this long to carve into the ±2 stance
    HARD_TURN_HOLD = 0.4

    # Style: slalom gates and flips
    GATE_SPACING = 120         # World px between gate rows (~40 m)
    GATE_WIDTH = 8             # Px between the two flags
    GATE_STYLE = 10            # Style for passing between the flags
    GATE_PENALTY = 5           # Style lost for missing a nearby gate
    FLIP_DURATION = 0.4        # Seconds a flip takes
    FLIP_STYLE = 25            # Style for a landed flip

    # Yeti — faster than plain skiing (MAX_SPEED); only boost outruns him.
    # _update_yeti adds a downhill drift of 0.7 * player speed ON TOP of
    # yeti_speed, so effective closure = yeti_speed - 0.3 * player_speed.
    # Plain skiing tops out at MAX_SPEED 80 -> 0.3*80 = 24 < 27 (caught);
    # BOOST is 110 -> 0.3*110 = 33 > 30 (escapes).
    YETI_SPAWN_DISTANCE = 750   # Meters
    YETI_SPEED_MIN = 27.0       # Slowest lope (still catches plain skiing)
    YETI_SPEED_MAX = 30.0       # Fastest burst (only BOOST pulls away)
    YETI_SPEED_CHANGE = 1.5     # Seconds between speed shifts
    YETI_CATCH_DIST = 4.0       # Pixels to catch player

    # Obstacle generation
    OBSTACLE_INTERVAL_START = 30.0  # Pixels between obstacle rows (sparse)
    OBSTACLE_INTERVAL_MIN = 12.0    # Minimum spacing (dense)
    MIN_GAP = 10                    # Minimum clear gap in pixels

    # Chunk-based generation
    CHUNK_SIZE = 64

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
    YETI_BODY = (150, 150, 165)
    YETI_FACE = (50, 50, 70)
    YETI_ARMS = (0, 0, 0)
    BOOST_COLOR = (50, 200, 255)
    BOOST_EMPTY = (60, 60, 70)
    GATE_BLUE = (60, 120, 255)
    GATE_RED = (255, 60, 60)
    GATE_POLE = (120, 90, 60)
    DOG_COLOR = (150, 100, 50)
    DOG_DARK = (110, 70, 35)
    RIVAL_BODY = (40, 160, 80)
    STYLE_COLOR = (80, 200, 255)

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0

        # Player state — world-space X, screen-space Y
        self.player_x = 32.0        # World X (unbounded)
        self.player_y = float(self.PLAYER_Y_DEFAULT)  # Screen Y
        self.direction = 0
        self.turn_hold = 0.0        # How long the current direction is held
        self.braking = False
        self.speed = self.BASE_SPEED

        # Style points (gates + tricks)
        self.style = 0

        # Crash state
        self.crashed = False
        self.crash_timer = 0.0
        self.invuln_timer = 0.0

        # Jump / trick state
        self.airborne = False
        self.air_timer = 0.0
        self.air_from_ramp = False
        self.flipping = False
        self.flip_timer = 0.0
        self.flip_done = False

        # Boost state
        self.boost_fuel = self.BOOST_FUEL_MAX
        self.boosting = False

        # Scrolling / distance
        self.scroll_speed = self.BASE_SPEED
        self.distance = 0.0         # Total vertical world distance
        self.distance_meters = 0.0  # Displayed distance

        # Yeti — world-space coordinates
        self.yeti_active = False
        self.yeti_x = 0.0          # World X
        self.yeti_y = 0.0          # World Y
        self.yeti_eating = False
        self.yeti_eat_timer = 0.0
        self.yeti_speed = self.YETI_SPEED_MAX
        self.yeti_speed_timer = 0.0

        # Obstacles: {type, x, y, w, h} — world-space coords (fixed after creation)
        self.obstacles = []
        # Moving entities (dogs, rival skiers) — world-space, updated per frame
        self.entities = []
        # Chunk-based generation
        self.generated_chunks = set()

        # Generate initial chunks
        self._generate_chunks()

    def _get_obstacle_interval(self, distance_meters):
        """Get spacing between obstacle rows based on distance."""
        progress = min(1.0, distance_meters / 3000.0)
        return self.OBSTACLE_INTERVAL_START - progress * (self.OBSTACLE_INTERVAL_START - self.OBSTACLE_INTERVAL_MIN)

    def _generate_chunks(self):
        """Generate chunks visible to camera plus a buffer."""
        cam_x = self.player_x - 32
        cam_y = self.distance

        # Visible chunk range with 1-chunk buffer on each side
        cx_min = int(math.floor(cam_x / self.CHUNK_SIZE)) - 1
        cx_max = int(math.floor((cam_x + GRID_SIZE) / self.CHUNK_SIZE)) + 1
        cy_min = int(math.floor(cam_y / self.CHUNK_SIZE)) - 1
        cy_max = int(math.floor((cam_y + GRID_SIZE) / self.CHUNK_SIZE)) + 1

        for cx in range(cx_min, cx_max + 1):
            for cy in range(cy_min, cy_max + 1):
                if (cx, cy) not in self.generated_chunks:
                    self._generate_chunk(cx, cy)
                    self.generated_chunks.add((cx, cy))

    def _generate_chunk(self, cx, cy):
        """Generate obstacles for a single chunk using deterministic seeding."""
        # Skip chunks above world start
        if cy < 0:
            return

        # Deterministic RNG per chunk
        seed = (cx * 73856093) ^ (cy * 19349663)
        rng = random.Random(seed)

        x_min = cx * self.CHUNK_SIZE
        y_min = cy * self.CHUNK_SIZE

        # Distance (meters) at chunk center for difficulty scaling
        chunk_center_y = y_min + self.CHUNK_SIZE / 2
        distance_meters = chunk_center_y / 3.0

        interval = self._get_obstacle_interval(distance_meters)

        # Generate obstacle rows within chunk
        y = y_min + rng.uniform(0, interval)
        while y < y_min + self.CHUNK_SIZE:
            self._generate_obstacle_row(rng, x_min, y, distance_meters)
            y += interval

        # Slalom gates every GATE_SPACING of world y (~40 m), blue/red
        # alternating by row
        gy = -(-y_min // self.GATE_SPACING) * self.GATE_SPACING
        while gy < y_min + self.CHUNK_SIZE:
            gx = x_min + rng.randint(4, self.CHUNK_SIZE - 12)
            self.obstacles.append({
                'type': 'gate', 'x': gx, 'y': gy,
                'w': self.GATE_WIDTH, 'h': 2,
                'ci': (gy // self.GATE_SPACING) % 2, 'scored': False,
            })
            gy += self.GATE_SPACING

        # Moving hazards: an occasional dog or rival skier per chunk
        # (skip the first couple rows so the start stays clear)
        if cy >= 2:
            if rng.random() < 0.2:
                self.entities.append({
                    'kind': 'dog',
                    'x': float(x_min + rng.randint(8, self.CHUNK_SIZE - 8)),
                    'y': float(y_min + rng.randint(0, self.CHUNK_SIZE - 1)),
                    'vx': rng.choice([-1.0, 1.0]) * rng.uniform(6.0, 12.0),
                    'turn_timer': rng.uniform(1.0, 3.0),
                    'tangle': 0.0,
                })
            if rng.random() < 0.15:
                self.entities.append({
                    'kind': 'rival',
                    'x': float(x_min + rng.randint(8, self.CHUNK_SIZE - 8)),
                    'y': float(y_min + rng.randint(0, self.CHUNK_SIZE - 1)),
                    'vy': rng.uniform(20.0, 32.0),
                    'sway': rng.uniform(0.0, 6.28),
                    'tangle': 0.0,
                })

    def _generate_obstacle_row(self, rng, x_min, y, distance_meters):
        """Generate a row of obstacles at the given world y position."""
        density = min(0.8, 0.3 + distance_meters / 4000.0)
        num_obstacles = 1
        if rng.random() < density:
            num_obstacles = 2
        if rng.random() < density * 0.4:
            num_obstacles = 3

        placed = []
        for _ in range(num_obstacles):
            for _ in range(10):
                obs = self._random_obstacle(rng, x_min, y, distance_meters)
                overlaps = False
                for p in placed:
                    if abs(obs['x'] - p['x']) < self.MIN_GAP:
                        overlaps = True
                        break
                if not overlaps:
                    placed.append(obs)
                    self.obstacles.append(obs)
                    break

    def _random_obstacle(self, rng, x_min, y, distance_meters):
        """Create a random obstacle at given world y within the chunk's x range."""
        x = x_min + rng.randint(2, self.CHUNK_SIZE - 6)
        roll = rng.random()

        # More ramps after yeti distance for escape opportunities (deterministic)
        ramp_chance = 0.08
        if distance_meters >= self.YETI_SPAWN_DISTANCE:
            ramp_chance = 0.15

        if roll < 0.45:
            return {'type': 'small_tree', 'x': x, 'y': y, 'w': 3, 'h': 4}
        elif roll < 0.75:
            return {'type': 'large_tree', 'x': x, 'y': y, 'w': 5, 'h': 6}
        elif roll < 0.88:
            return {'type': 'rock', 'x': x, 'y': y, 'w': 3, 'h': 2}
        elif roll < 1.0 - ramp_chance:
            return {'type': 'mogul', 'x': x, 'y': y, 'w': 3, 'h': 2}
        else:
            return {'type': 'ramp', 'x': x, 'y': y, 'w': 4, 'h': 2}

    def _cull_far(self):
        """Remove obstacles and entities far from the camera."""
        cam_x = self.player_x - 32
        cam_y = self.distance
        cull_dist = self.CHUNK_SIZE * 2.5

        self.obstacles = [o for o in self.obstacles
                          if abs(o['y'] - cam_y) < cull_dist
                          and abs(o['x'] - cam_x) < cull_dist]
        self.entities = [e for e in self.entities
                         if abs(e['y'] - cam_y) < cull_dist
                         and abs(e['x'] - cam_x) < cull_dist]

        # Prune old vertical chunk records (but keep horizontal for determinism)
        current_cy = int(math.floor(cam_y / self.CHUNK_SIZE))
        self.generated_chunks = {
            (cx, cy) for (cx, cy) in self.generated_chunks
            if cy >= current_cy - 2
        }

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        # Yeti eating animation
        if self.yeti_eating:
            self.yeti_eat_timer += dt
            if self.yeti_eat_timer >= 1.5:
                self.state = GameState.GAME_OVER
            return

        # Crash recovery — slope keeps scrolling
        if self.crashed:
            self.crash_timer -= dt
            if self.crash_timer <= 0:
                self.crashed = False
                self.invuln_timer = self.INVULN_DURATION

            scroll_amount = self.speed * dt
            self.distance += scroll_amount
            self.distance_meters = self.distance / 3.0
            self.score = int(self.distance_meters)
            self._generate_chunks()
            self._cull_far()
            self._update_entities(dt)

            # Yeti still moves during crash
            if self.yeti_active:
                self._update_yeti(dt)
                if self._check_yeti_catch():
                    return
            return

        # Tick down invulnerability
        if self.invuln_timer > 0:
            self.invuln_timer -= dt

        # --- Input ---
        if input_state.up:
            self.player_y -= 40.0 * dt
        elif input_state.down:
            self.player_y += 40.0 * dt
        self.player_y = max(self.PLAYER_Y_MIN, min(self.PLAYER_Y_MAX, self.player_y))

        # Left/Right steer — holding a direction carves into the hard stance
        if input_state.left and input_state.right:
            self.direction = 0
            self.turn_hold = 0.0
        elif input_state.left:
            if self.direction in (-1, -2):
                self.turn_hold += dt
                if self.turn_hold >= self.HARD_TURN_HOLD:
                    self.direction = -2
            else:
                self.direction = -1
                self.turn_hold = 0.0
        elif input_state.right:
            if self.direction in (1, 2):
                self.turn_hold += dt
                if self.turn_hold >= self.HARD_TURN_HOLD:
                    self.direction = 2
            else:
                self.direction = 1
                self.turn_hold = 0.0
        else:
            self.direction = 0
            self.turn_hold = 0.0

        self.braking = False

        # Trick: press the button while airborne off a ramp to start a flip
        if (self.airborne and self.air_from_ramp and not self.flipping
                and not self.flip_done
                and (input_state.action_l or input_state.action_r)):
            self.flipping = True
            self.flip_timer = self.FLIP_DURATION

        # Boost
        if (input_state.action_l_held or input_state.action_r_held) and self.boost_fuel > 0:
            self.boosting = True
            self.boost_fuel -= dt
            if self.boost_fuel < 0:
                self.boost_fuel = 0
                self.boosting = False
        else:
            self.boosting = False
            self.boost_fuel = min(self.BOOST_FUEL_MAX, self.boost_fuel + self.BOOST_RECHARGE * dt)

        # --- Speed calculation ---
        if self.boosting:
            target_speed = self.BOOST_SPEED
        else:
            progress_speed = min(self.MAX_SPEED, self.BASE_SPEED + self.distance_meters * 0.008)
            target_speed = progress_speed * self.DIRECTION_SPEED[self.direction]

        self.speed += (target_speed - self.speed) * min(1.0, dt * 5.0)

        # --- Horizontal movement (world-space, unbounded) ---
        lateral = self.DIRECTION_LATERAL[self.direction] * self.LATERAL_SPEED * dt
        if self.boosting:
            lateral *= 1.3
        self.player_x += lateral

        # --- Vertical scrolling (distance) ---
        scroll_amount = self.speed * dt
        self.distance += scroll_amount
        self.distance_meters = self.distance / 3.0
        self.score = int(self.distance_meters)

        # --- Jump timer / flip trick ---
        if self.airborne:
            self.air_timer -= dt
            if self.flipping:
                self.flip_timer -= dt
                if self.flip_timer <= 0:
                    self.flipping = False
                    self.flip_done = True
            if self.air_timer <= 0:
                self.airborne = False
                if self.flipping:
                    # Landed mid-flip — faceplant
                    self.flipping = False
                    self.crashed = True
                    self.crash_timer = self.CRASH_DURATION
                    self.speed *= 0.2
                    self.boosting = False
                elif self.flip_done:
                    # Stomped it
                    self.style += self.FLIP_STYLE
                self.flip_done = False
                self.air_from_ramp = False

        # --- Collision detection ---
        if not self.airborne and self.invuln_timer <= 0:
            cam_x = self.player_x - 32
            # Player hitbox at screen center
            player_box = (31, int(self.player_y) - 1, 3, 4)

            for obs in self.obstacles:
                ox = int(obs['x'] - cam_x)
                oy = int(obs['y'] - self.distance)

                # Quick screen reject
                if ox < -8 or ox > 72 or oy < -8 or oy > 72:
                    continue

                ow = obs['w']
                oh = obs['h']

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
                        self.air_from_ramp = False
                    elif obs['type'] == 'ramp':
                        self.airborne = True
                        self.air_timer = self.JUMP_DURATION
                        self.air_from_ramp = True
                        self.speed *= 1.2

            # Tangle with a dog or rival skier — comedic wipeout
            if not self.crashed:
                for ent in self.entities:
                    ex = int(ent['x'] - cam_x)
                    ey = int(ent['y'] - self.distance)
                    if (player_box[0] < ex + 3
                            and player_box[0] + player_box[2] > ex
                            and player_box[1] < ey + 3
                            and player_box[1] + player_box[3] > ey):
                        self.crashed = True
                        self.crash_timer = self.CRASH_DURATION
                        self.speed *= 0.2
                        self.boosting = False
                        ent['tangle'] = 0.8
                        break

        # --- Slalom gates: pass between the flags for style ---
        player_world_y = self.distance + self.player_y
        for obs in self.obstacles:
            if obs['type'] != 'gate' or obs['scored']:
                continue
            if obs['y'] <= player_world_y:
                obs['scored'] = True
                # Only judge gates crossed this instant (not ones that
                # scrolled past during a crash)
                if player_world_y - obs['y'] > 6:
                    continue
                dx = abs(self.player_x - (obs['x'] + obs['w'] / 2.0))
                if dx <= obs['w'] / 2.0:
                    self.style += self.GATE_STYLE
                elif dx <= 16:
                    self.style = max(0, self.style - self.GATE_PENALTY)

        # --- Generate new chunks & cull ---
        self._generate_chunks()
        self._cull_far()
        self._update_entities(dt)

        # --- Yeti ---
        if not self.yeti_active and self.distance_meters >= self.YETI_SPAWN_DISTANCE:
            self.yeti_active = True
            self.yeti_x = self.player_x
            self.yeti_y = self.distance - 10  # Above screen in world Y

        if self.yeti_active:
            self._update_yeti(dt)
            self._check_yeti_catch()

    def _update_yeti(self, dt: float):
        """Move Yeti toward player with variable speed."""
        self.yeti_speed_timer += dt
        if self.yeti_speed_timer >= self.YETI_SPEED_CHANGE:
            self.yeti_speed_timer = 0.0
            self.yeti_speed = random.uniform(self.YETI_SPEED_MIN, self.YETI_SPEED_MAX)

        # Player world position
        player_world_y = self.distance + self.player_y

        dx = self.player_x - self.yeti_x
        dy = player_world_y - self.yeti_y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist > 0:
            yeti_move = self.yeti_speed * dt
            self.yeti_x += (dx / dist) * yeti_move
            self.yeti_y += (dy / dist) * yeti_move

        # Downhill drift (replaces old scroll resistance)
        self.yeti_y += self.speed * dt * 0.7

    def _check_yeti_catch(self) -> bool:
        """Check if Yeti caught the player (world-space)."""
        player_world_y = self.distance + self.player_y

        dx = self.player_x - self.yeti_x
        dy = player_world_y - self.yeti_y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist < self.YETI_CATCH_DIST:
            self.yeti_eating = True
            self.yeti_eat_timer = 0.0
            self.yeti_x = self.player_x
            self.yeti_y = player_world_y
            return True
        return False

    def _update_entities(self, dt: float):
        """Move the wandering dogs and descending rival skiers."""
        for ent in self.entities:
            if ent['tangle'] > 0:
                ent['tangle'] -= dt
                continue  # Tangled entities sit and tumble for a moment
            if ent['kind'] == 'dog':
                ent['x'] += ent['vx'] * dt
                ent['turn_timer'] -= dt
                if ent['turn_timer'] <= 0:
                    if random.random() < 0.6:
                        ent['vx'] = -ent['vx']
                    ent['turn_timer'] = random.uniform(1.0, 3.0)
            else:  # rival skier — slowly descends, swaying side to side
                ent['y'] += ent['vy'] * dt
                ent['sway'] += dt * 1.5
                ent['x'] += math.sin(ent['sway']) * 6.0 * dt

    def draw(self):
        cam_x = self.player_x - 32
        cam_y = self.distance

        # Snow background
        self.display.clear(self.SNOW_COLOR)

        # Draw some snow texture (subtle dots) — seeded from camera position
        random.seed(int(cam_x / 20) * 7 + int(cam_y / 20) * 13)
        for _ in range(20):
            sx = random.randint(0, 63)
            sy = random.randint(0, 63)
            self.display.set_pixel(sx, sy, (225, 225, 240))
        random.seed()

        # Draw obstacles (sorted by y so closer ones draw on top)
        sorted_obs = sorted(self.obstacles, key=lambda o: o['y'])
        for obs in sorted_obs:
            self._draw_obstacle(obs, cam_x, cam_y)

        # Draw moving entities (dogs, rival skiers)
        for ent in self.entities:
            self._draw_entity(ent, cam_x, cam_y)

        # Draw player
        if not self.yeti_eating:
            self._draw_player()

        # Draw Yeti
        if self.yeti_active:
            self._draw_yeti(cam_x, cam_y)

        # Draw HUD
        self._draw_hud()

    def _draw_obstacle(self, obs: dict, cam_x: float, cam_y: float):
        x = int(obs['x'] - cam_x)
        y = int(obs['y'] - cam_y)

        # Skip if off screen
        if x < -8 or x > GRID_SIZE + 4 or y < -8 or y > GRID_SIZE + 4:
            return

        if obs['type'] == 'small_tree':
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
            rows = [
                (2, 1),
                (1, 3),
                (0, 5),
                (1, 3),
                (2, 1),
            ]
            for i, (offset, width) in enumerate(rows):
                ry = y + i
                if 0 <= ry < GRID_SIZE:
                    color = self.TREE_GREEN if i < 3 else self.TREE_DARK
                    for dx in range(width):
                        px = x + offset + dx
                        if 0 <= px < GRID_SIZE:
                            self.display.set_pixel(px, ry, color)
            if 0 <= y + 5 < GRID_SIZE and 0 <= x + 2 < GRID_SIZE:
                self.display.set_pixel(x + 2, y + 5, self.TREE_TRUNK)

        elif obs['type'] == 'rock':
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
            if 0 <= y < GRID_SIZE:
                for dx in range(3):
                    if 0 <= x + dx < GRID_SIZE:
                        self.display.set_pixel(x + dx, y, self.MOGUL_COLOR)
            if 0 <= y + 1 < GRID_SIZE:
                if 0 <= x + 1 < GRID_SIZE:
                    self.display.set_pixel(x + 1, y + 1, (200, 200, 215))

        elif obs['type'] == 'ramp':
            if 0 <= y < GRID_SIZE:
                for dx in range(4):
                    if 0 <= x + dx < GRID_SIZE:
                        self.display.set_pixel(x + dx, y, self.RAMP_COLORS[dx % len(self.RAMP_COLORS)])
            if 0 <= y + 1 < GRID_SIZE:
                for dx in range(4):
                    if 0 <= x + dx < GRID_SIZE:
                        c = self.RAMP_COLORS[(dx + 1) % len(self.RAMP_COLORS)]
                        self.display.set_pixel(x + dx, y + 1, c)

        elif obs['type'] == 'gate':
            # Slalom gate: two flags on short poles, blue/red alternating
            color = self.GATE_BLUE if obs['ci'] == 0 else self.GATE_RED
            for gx in (x, x + obs['w']):
                if 0 <= gx < GRID_SIZE:
                    if 0 <= y < GRID_SIZE:
                        self.display.set_pixel(gx, y, color)
                    if 0 <= y + 1 < GRID_SIZE:
                        self.display.set_pixel(gx, y + 1, self.GATE_POLE)

    def _draw_entity(self, ent: dict, cam_x: float, cam_y: float):
        x = int(ent['x'] - cam_x)
        y = int(ent['y'] - cam_y)

        if x < -4 or x > GRID_SIZE + 4 or y < -4 or y > GRID_SIZE + 4:
            return

        tangled = ent['tangle'] > 0
        if ent['kind'] == 'dog':
            body = self.DOG_COLOR
            if tangled and int(ent['tangle'] * 10) % 2 == 0:
                body = (255, 140, 100)
            # Small sideways dog: head leads in the direction of travel
            head_dx = 2 if ent['vx'] > 0 else 0
            if 0 <= y < GRID_SIZE and 0 <= x + head_dx < GRID_SIZE:
                self.display.set_pixel(x + head_dx, y, body)
            if 0 <= y + 1 < GRID_SIZE:
                for dx in range(3):
                    if 0 <= x + dx < GRID_SIZE:
                        self.display.set_pixel(x + dx, y + 1, body)
            if 0 <= y + 2 < GRID_SIZE:
                for dx in (0, 2):
                    if 0 <= x + dx < GRID_SIZE:
                        self.display.set_pixel(x + dx, y + 2, self.DOG_DARK)
        else:
            # Rival skier — same silhouette as the player, green jacket
            body = self.RIVAL_BODY
            if tangled and int(ent['tangle'] * 10) % 2 == 0:
                body = (255, 140, 100)
            if 0 <= y < GRID_SIZE and 0 <= x < GRID_SIZE:
                self.display.set_pixel(x, y, self.SKIER_HEAD)
            if 0 <= y + 1 < GRID_SIZE:
                for dx in (-1, 0, 1):
                    if 0 <= x + dx < GRID_SIZE:
                        self.display.set_pixel(x + dx, y + 1, body)
            if 0 <= y + 2 < GRID_SIZE and 0 <= x < GRID_SIZE:
                self.display.set_pixel(x, y + 2, body)
            if 0 <= y + 3 < GRID_SIZE:
                for dx in (-1, 1):
                    if 0 <= x + dx < GRID_SIZE:
                        self.display.set_pixel(x + dx, y + 3, self.SKIER_SKI)

    def _draw_player(self):
        px = 32  # Always screen center
        py = int(self.player_y)

        if self.crashed:
            if 0 <= py < GRID_SIZE:
                self.display.set_pixel(px, py, self.CRASH_COLOR)
            if 0 <= py + 1 < GRID_SIZE:
                for dx in [-1, 0, 1]:
                    if 0 <= px + dx < GRID_SIZE:
                        self.display.set_pixel(px + dx, py + 1, self.CRASH_COLOR)
            if 0 <= py + 2 < GRID_SIZE:
                self.display.set_pixel(px, py + 2, self.SKIER_SKI)
            return

        # Flicker during invulnerability
        if self.invuln_timer > 0 and int(self.invuln_timer * 10) % 2 == 0:
            return

        if self.airborne:
            if 0 <= py + 3 < GRID_SIZE:
                self.display.set_pixel(px, py + 3, (180, 180, 195))
            jump_py = py - 3
        else:
            jump_py = py

        # Mid-flip — 2-frame rotation
        if self.airborne and self.flipping:
            frame = int((self.FLIP_DURATION - self.flip_timer)
                        / self.FLIP_DURATION * 2) % 2
            if frame == 0:
                # Sideways: body horizontal, skis trailing
                if 0 <= jump_py + 1 < GRID_SIZE:
                    for dx in (-1, 0, 1):
                        if 0 <= px + dx < GRID_SIZE:
                            self.display.set_pixel(px + dx, jump_py + 1,
                                                   self.SKIER_BODY)
                    if 0 <= px - 2 < GRID_SIZE:
                        self.display.set_pixel(px - 2, jump_py + 1,
                                               self.SKIER_HEAD)
                if 0 <= jump_py < GRID_SIZE and 0 <= px + 2 < GRID_SIZE:
                    self.display.set_pixel(px + 2, jump_py, self.SKIER_SKI)
            else:
                # Upside down: skis above, head below
                if 0 <= jump_py < GRID_SIZE:
                    for dx in (-1, 1):
                        if 0 <= px + dx < GRID_SIZE:
                            self.display.set_pixel(px + dx, jump_py,
                                                   self.SKIER_SKI)
                if 0 <= jump_py + 1 < GRID_SIZE:
                    self.display.set_pixel(px, jump_py + 1, self.SKIER_BODY)
                if 0 <= jump_py + 2 < GRID_SIZE:
                    self.display.set_pixel(px, jump_py + 2, self.SKIER_HEAD)
            return

        if self.direction == 0:
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

    def _draw_yeti(self, cam_x: float, cam_y: float):
        if self.yeti_eating:
            # Eating animation — big yeti over player (screen center)
            px = 32
            py = int(self.player_y)

            for dy in range(-2, 4):
                for dx in range(-2, 3):
                    ppx = px + dx
                    ppy = py + dy
                    if 0 <= ppx < GRID_SIZE and 0 <= ppy < GRID_SIZE:
                        self.display.set_pixel(ppx, ppy, self.YETI_BODY)
            if 0 <= py - 1 < GRID_SIZE:
                if 0 <= px - 1 < GRID_SIZE:
                    self.display.set_pixel(px - 1, py - 1, self.YETI_FACE)
                if 0 <= px + 1 < GRID_SIZE:
                    self.display.set_pixel(px + 1, py - 1, self.YETI_FACE)
            if 0 <= py < GRID_SIZE:
                self.display.set_pixel(px, py, (200, 50, 50))
            return

        # Normal Yeti — chasing (world to screen transform)
        yx = int(self.yeti_x - cam_x)
        yy = int(self.yeti_y - cam_y)

        # Skip if off screen
        if yx < -8 or yx > GRID_SIZE + 8 or yy < -8 or yy > GRID_SIZE + 8:
            return

        # Head (3 wide)
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
        # Body (3 wide) + stick arms
        for dy in range(2, 4):
            if 0 <= yy + dy < GRID_SIZE:
                for dx in range(-1, 2):
                    if 0 <= yx + dx < GRID_SIZE:
                        self.display.set_pixel(yx + dx, yy + dy, self.YETI_BODY)
        # Arms
        if 0 <= yy + 2 < GRID_SIZE:
            if 0 <= yx - 2 < GRID_SIZE:
                self.display.set_pixel(yx - 2, yy + 2, self.YETI_ARMS)
            if 0 <= yx + 2 < GRID_SIZE:
                self.display.set_pixel(yx + 2, yy + 2, self.YETI_ARMS)
            if 0 <= yy + 3 < GRID_SIZE:
                if 0 <= yx - 3 < GRID_SIZE:
                    self.display.set_pixel(yx - 3, yy + 3, self.YETI_ARMS)
                if 0 <= yx + 3 < GRID_SIZE:
                    self.display.set_pixel(yx + 3, yy + 3, self.YETI_ARMS)
        # Legs
        if 0 <= yy + 4 < GRID_SIZE:
            if 0 <= yx - 1 < GRID_SIZE:
                self.display.set_pixel(yx - 1, yy + 4, self.YETI_BODY)
            if 0 <= yx + 1 < GRID_SIZE:
                self.display.set_pixel(yx + 1, yy + 4, self.YETI_BODY)

    def _draw_hud(self):
        """Draw distance, style points, yeti warning, and boost meter."""
        self.display.draw_rect(0, 0, GRID_SIZE, 7, (0, 0, 0))

        dist_str = f"{int(self.distance_meters)}M"
        self.display.draw_text_small(1, 1, dist_str, Colors.WHITE)

        self.display.draw_text_small(24, 1, f"S{self.style}", self.STYLE_COLOR)

        if self.yeti_active and int(self.distance * 0.1) % 2 == 0:
            self.display.draw_text_small(42, 1, "Y!", Colors.RED)

        bar_x = 53
        bar_w = 10
        bar_h = 3
        bar_y = 2

        self.display.draw_rect(bar_x, bar_y, bar_w, bar_h, self.BOOST_EMPTY)

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

        self.display.draw_text_small(8, 38, f"STYLE:{self.style}",
                                     self.STYLE_COLOR)

        self.display.draw_text_small(4, 50, "BTN:RETRY", Colors.GRAY)
