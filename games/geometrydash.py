"""
Geometry Dash - Rhythm runner with obstacles
=============================================
Jump over spikes and obstacles! Precise timing required.

Controls:
  Space      - Jump (tap or hold for repeated jumps)
  Escape     - Return to menu
"""

import random
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


class GeometryDash(Game):
    name = "GEODASH"
    description = "Jump the spikes!"
    category = "modern"

    # Physics
    GRAVITY = 250.0
    JUMP_VELOCITY = -85.0
    MAX_FALL_SPEED = 150.0

    # Game constants
    GROUND_Y = 52
    PLAYER_X = 12
    PLAYER_SIZE = 5
    SCROLL_SPEED = 55.0

    def __init__(self, display: Display):
        super().__init__(display)
        air_time = 2 * abs(self.JUMP_VELOCITY) / self.GRAVITY
        self.jump_distance = self.SCROLL_SPEED * air_time
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0

        self.player_y = self.GROUND_Y - self.PLAYER_SIZE
        self.velocity_y = 0.0
        self.on_ground = True
        self.rotation = 0.0

        self.scroll_x = 0.0
        self.obstacles = []
        self.ground_segments = []
        self._init_ground()

        self.beat_count = 0
        self._generate_rhythm_obstacles(GRID_SIZE + 80)

        self.particles = []
        self.bg_squares = []
        for i in range(5):
            self.bg_squares.append({
                'x': random.randint(0, GRID_SIZE),
                'y': random.randint(10, 45),
                'size': random.randint(3, 6),
                'speed': random.uniform(0.2, 0.5)
            })

        self.player_color = Colors.CYAN
        self.ground_color = (40, 40, 60)
        self.can_jump_again = True

    def _init_ground(self):
        self.ground_segments.append({
            'x': -10.0,
            'width': GRID_SIZE + 100,
            'has_ground': True
        })

    def _generate_rhythm_obstacles(self, target_x: float):
        """Generate varied obstacles on a rhythm grid."""
        if self.obstacles:
            rightmost = max(o['x'] + o.get('width', 0) for o in self.obstacles)
            start_x = rightmost + self.jump_distance * random.uniform(0.6, 0.9)
        else:
            start_x = 50.0

        # Rich pattern library with variations
        patterns = [
            # === SINGLE OBSTACLES ===
            # Single spike
            [{'type': 'spike', 'beat': 0}],
            # Single tall spike
            [{'type': 'spike_tall', 'beat': 0}],
            # Single block
            [{'type': 'block', 'beat': 0}],
            # Single small block (can jump on or over)
            [{'type': 'block_small', 'beat': 0}],

            # === DOUBLE OBSTACLES ===
            # Two spikes, one jump clears both
            [{'type': 'spike', 'beat': 0}, {'type': 'spike', 'beat': 0.4}],
            # Spike then block
            [{'type': 'spike', 'beat': 0}, {'type': 'block_small', 'beat': 1.0}],
            # Two blocks to hop across
            [{'type': 'block_small', 'beat': 0}, {'type': 'block_small', 'beat': 0.8}],

            # === TRIPLE OBSTACLES ===
            # Three spikes in a row
            [{'type': 'spike', 'beat': 0}, {'type': 'spike', 'beat': 0.35}, {'type': 'spike', 'beat': 0.7}],
            # Spike sandwich
            [{'type': 'spike', 'beat': 0}, {'type': 'block_small', 'beat': 0.6}, {'type': 'spike', 'beat': 1.2}],

            # === PLATFORM PATTERNS ===
            # High platform to jump to
            [{'type': 'platform_high', 'beat': 0}],
            # Low platform with spike
            [{'type': 'platform_low', 'beat': 0}, {'type': 'spike', 'beat': 0.5}],
            # Stair step up
            [{'type': 'block_small', 'beat': 0}, {'type': 'platform_mid', 'beat': 0.7}],

            # === COMPLEX PATTERNS ===
            # Block with spike on top (must jump over entirely)
            [{'type': 'block_spike', 'beat': 0}],
            # Gap jump with spike
            [{'type': 'spike', 'beat': 0}, {'type': 'spike', 'beat': 1.3}],
            # Platform gauntlet
            [{'type': 'platform_low', 'beat': 0}, {'type': 'spike', 'beat': 0.4}, {'type': 'platform_low', 'beat': 1.0}],

            # === REST BEATS ===
            [],  # Empty - breathing room (index 15)
            [],  # More rest options (index 16)
        ]

        while start_x < target_x:
            self.beat_count += 1

            # Difficulty progression (patterns has indices 0-16)
            if self.beat_count < 6:
                # Very easy - singles and rests
                available = [0, 3, 15, 16]
            elif self.beat_count < 15:
                # Easy - add doubles
                available = [0, 1, 2, 3, 4, 5, 9, 15, 16]
            elif self.beat_count < 30:
                # Medium - add triples and platforms
                available = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 15, 16]
            else:
                # Full variety
                available = list(range(len(patterns)))

            pattern = patterns[random.choice(available)]

            # Place obstacles from pattern
            for item in pattern:
                obs_x = start_x + item['beat'] * self.jump_distance
                obs_type = item['type']

                if obs_type == 'spike':
                    self.obstacles.append({
                        'type': 'spike',
                        'x': obs_x,
                        'y': self.GROUND_Y - 6,
                        'width': 6,
                        'height': 6
                    })
                elif obs_type == 'spike_tall':
                    self.obstacles.append({
                        'type': 'spike',
                        'x': obs_x,
                        'y': self.GROUND_Y - 8,
                        'width': 6,
                        'height': 8
                    })
                elif obs_type == 'block':
                    self.obstacles.append({
                        'type': 'block',
                        'x': obs_x,
                        'y': self.GROUND_Y - 8,
                        'width': 8,
                        'height': 8
                    })
                elif obs_type == 'block_small':
                    self.obstacles.append({
                        'type': 'block',
                        'x': obs_x,
                        'y': self.GROUND_Y - 5,
                        'width': 6,
                        'height': 5
                    })
                elif obs_type == 'block_spike':
                    self.obstacles.append({
                        'type': 'block',
                        'x': obs_x,
                        'y': self.GROUND_Y - 6,
                        'width': 7,
                        'height': 6
                    })
                    self.obstacles.append({
                        'type': 'spike',
                        'x': obs_x + 1,
                        'y': self.GROUND_Y - 10,
                        'width': 5,
                        'height': 4
                    })
                elif obs_type == 'platform_high':
                    self.obstacles.append({
                        'type': 'platform',
                        'x': obs_x,
                        'y': self.GROUND_Y - 18,
                        'width': 14,
                        'height': 3
                    })
                elif obs_type == 'platform_mid':
                    self.obstacles.append({
                        'type': 'platform',
                        'x': obs_x,
                        'y': self.GROUND_Y - 12,
                        'width': 12,
                        'height': 3
                    })
                elif obs_type == 'platform_low':
                    self.obstacles.append({
                        'type': 'platform',
                        'x': obs_x,
                        'y': self.GROUND_Y - 8,
                        'width': 10,
                        'height': 3
                    })

            # Variable spacing between pattern groups
            pattern_end = max([item['beat'] for item in pattern], default=0) + 1 if pattern else 0.3
            spacing = random.uniform(0.4, 0.7)
            start_x += self.jump_distance * (pattern_end + spacing)

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        if input_state.action_held:
            if self.on_ground and self.can_jump_again:
                self.velocity_y = self.JUMP_VELOCITY
                self.on_ground = False
                self.can_jump_again = False
                self._spawn_jump_particles()
        else:
            self.can_jump_again = True

        if not self.on_ground:
            self.velocity_y += self.GRAVITY * dt
            self.velocity_y = min(self.velocity_y, self.MAX_FALL_SPEED)

        self.player_y += self.velocity_y * dt

        if not self.on_ground:
            self.rotation += 360 * dt * 2
        else:
            self.rotation = round(self.rotation / 90) * 90

        scroll_amount = self.SCROLL_SPEED * dt
        self.scroll_x += scroll_amount

        for obs in self.obstacles:
            obs['x'] -= scroll_amount

        for seg in self.ground_segments:
            seg['x'] -= scroll_amount

        for sq in self.bg_squares:
            sq['x'] -= scroll_amount * sq['speed']
            if sq['x'] < -sq['size']:
                sq['x'] = GRID_SIZE + random.randint(0, 20)
                sq['y'] = random.randint(10, 45)

        for p in self.particles:
            p['x'] -= scroll_amount
            p['y'] += p['vy'] * dt
            p['vy'] += 50 * dt
            p['life'] -= dt
        self.particles = [p for p in self.particles if p['life'] > 0]

        # Ground collision
        self.on_ground = False
        if self.player_y >= self.GROUND_Y - self.PLAYER_SIZE:
            self.player_y = self.GROUND_Y - self.PLAYER_SIZE
            self.velocity_y = 0
            self.on_ground = True

        # Platform/block landing
        for obs in self.obstacles:
            if obs['type'] in ['platform', 'block']:
                if self.velocity_y >= 0 and self._player_over_platform(obs):
                    platform_top = obs['y']
                    if (self.player_y + self.PLAYER_SIZE >= platform_top and
                        self.player_y + self.PLAYER_SIZE <= platform_top + 6):
                        self.player_y = platform_top - self.PLAYER_SIZE
                        self.velocity_y = 0
                        self.on_ground = True
                        break

        # Collision detection
        player_box = (self.PLAYER_X + 1, int(self.player_y) + 1,
                     self.PLAYER_SIZE - 2, self.PLAYER_SIZE - 2)

        for obs in self.obstacles:
            if obs['type'] == 'spike':
                spike_box = (int(obs['x']) + 2, int(obs['y']) + 2,
                           obs['width'] - 4, obs['height'] - 2)
                if self._rect_collision(player_box, spike_box):
                    self.state = GameState.GAME_OVER
                    return

            elif obs['type'] == 'block':
                block_box = (int(obs['x']), int(obs['y']),
                           obs['width'], obs['height'])
                if self._rect_collision(player_box, block_box):
                    if self.player_y + self.PLAYER_SIZE > obs['y'] + 3:
                        self.state = GameState.GAME_OVER
                        return

        if self.player_y > GRID_SIZE:
            self.state = GameState.GAME_OVER
            return

        self.obstacles = [o for o in self.obstacles if o['x'] + o.get('width', 10) > -20]
        self._generate_rhythm_obstacles(GRID_SIZE + 80)

        self.score = int(self.scroll_x / 5)

    def _player_over_platform(self, platform: dict) -> bool:
        player_left = self.PLAYER_X
        player_right = self.PLAYER_X + self.PLAYER_SIZE
        plat_left = platform['x']
        plat_right = platform['x'] + platform['width']
        return player_right > plat_left and player_left < plat_right

    def _rect_collision(self, r1, r2) -> bool:
        x1, y1, w1, h1 = r1
        x2, y2, w2, h2 = r2
        return (x1 < x2 + w2 and x1 + w1 > x2 and
                y1 < y2 + h2 and y1 + h1 > y2)

    def _spawn_jump_particles(self):
        for _ in range(3):
            self.particles.append({
                'x': self.PLAYER_X + random.randint(0, self.PLAYER_SIZE),
                'y': self.player_y + self.PLAYER_SIZE,
                'vy': random.uniform(-20, 0),
                'life': 0.3,
                'color': Colors.CYAN
            })

    def draw(self):
        self.display.clear((10, 10, 20))

        for sq in self.bg_squares:
            x, y = int(sq['x']), int(sq['y'])
            size = sq['size']
            for dy in range(size):
                for dx in range(size):
                    px, py = x + dx, y + dy
                    if 0 <= px < GRID_SIZE and 8 <= py < GRID_SIZE:
                        self.display.set_pixel(px, py, (20, 20, 35))

        for x in range(GRID_SIZE):
            for y in range(self.GROUND_Y, GRID_SIZE):
                self.display.set_pixel(x, y, self.ground_color)

        for x in range(GRID_SIZE):
            self.display.set_pixel(x, self.GROUND_Y, Colors.MAGENTA)

        for obs in self.obstacles:
            ox = int(obs['x'])
            oy = int(obs['y'])

            if obs['type'] == 'spike':
                self._draw_spike(ox, oy, obs['width'], obs['height'])

            elif obs['type'] == 'block':
                for y in range(oy, oy + obs['height']):
                    for x in range(ox, ox + obs['width']):
                        if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                            if y == oy:
                                self.display.set_pixel(x, y, (80, 80, 100))
                            else:
                                self.display.set_pixel(x, y, (50, 50, 70))

            elif obs['type'] == 'platform':
                for y in range(oy, oy + obs['height']):
                    for x in range(ox, ox + obs['width']):
                        if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                            self.display.set_pixel(x, y, Colors.PURPLE)
                for x in range(ox, ox + obs['width']):
                    if 0 <= x < GRID_SIZE:
                        self.display.set_pixel(x, oy, Colors.MAGENTA)

        for p in self.particles:
            px, py = int(p['x']), int(p['y'])
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                alpha = p['life'] / 0.3
                color = tuple(int(c * alpha) for c in p['color'])
                self.display.set_pixel(px, py, color)

        px = self.PLAYER_X
        py = int(self.player_y)

        for dy in range(self.PLAYER_SIZE):
            for dx in range(self.PLAYER_SIZE):
                if 0 <= px + dx < GRID_SIZE and 0 <= py + dy < GRID_SIZE:
                    self.display.set_pixel(px + dx, py + dy, self.player_color)

        inner_color = (0, 150, 150)
        for dx in range(1, self.PLAYER_SIZE - 1):
            for dy in range(1, self.PLAYER_SIZE - 1):
                if 0 <= px + dx < GRID_SIZE and 0 <= py + dy < GRID_SIZE:
                    self.display.set_pixel(px + dx, py + dy, inner_color)

        for dx in range(self.PLAYER_SIZE):
            if 0 <= px + dx < GRID_SIZE and 0 <= py < GRID_SIZE:
                self.display.set_pixel(px + dx, py, Colors.WHITE)

        self.display.draw_line(0, 6, 63, 6, Colors.DARK_GRAY)
        self.display.draw_text_small(1, 1, f"{self.score}", Colors.WHITE)

        progress = (self.scroll_x % 1000) / 1000
        bar_width = int(30 * progress)
        for x in range(30, 30 + bar_width):
            self.display.set_pixel(x, 3, Colors.GREEN)
        for x in range(30 + bar_width, 60):
            self.display.set_pixel(x, 3, Colors.DARK_GRAY)

    def _draw_spike(self, x: int, y: int, width: int, height: int):
        center_x = x + width // 2

        for row in range(height):
            row_from_bottom = height - 1 - row
            half_width = (row_from_bottom * width) // (height * 2)

            for dx in range(-half_width, half_width + 1):
                px = center_x + dx
                py = y + row
                if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                    if row < 2:
                        self.display.set_pixel(px, py, Colors.WHITE)
                    else:
                        self.display.set_pixel(px, py, (200, 200, 200))

    def draw_game_over(self):
        self.display.clear(Colors.BLACK)
        self.display.draw_text_small(8, 20, "GAME OVER", Colors.RED)
        self.display.draw_text_small(12, 32, f"SCORE:{self.score}", Colors.WHITE)
        self.display.draw_text_small(4, 50, "SPACE:RETRY", Colors.GRAY)
