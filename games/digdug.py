"""
Dig Dug - Underground Arcade Classic
====================================
Dig tunnels and pump enemies until they pop!

Controls:
  Arrow Keys - Move/Dig
  Space      - Pump (hold to inflate enemies)
"""

import random
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


class DigDug(Game):
    name = "DIGDUG"
    description = "Pump 'em up!"
    category = "arcade"

    # Colors
    DIRT_COLOR = (139, 90, 43)
    DIRT_DARK = (100, 65, 30)
    TUNNEL_COLOR = (50, 30, 15)
    PLAYER_COLOR = Colors.WHITE
    POOKA_COLOR = (255, 100, 100)  # Red round enemy
    FYGAR_COLOR = (100, 255, 100)  # Green dragon enemy
    ROCK_COLOR = (120, 120, 120)

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0
        self.lives = 3
        self.level = 1

        # Player state
        self.player_x = 32
        self.player_y = 8
        self.player_dir = (0, 1)  # Facing direction
        self.pump_active = False
        self.pump_length = 0
        self.pump_timer = 0

        # Tunnel map (True = dug out)
        self.tunnels = [[False] * GRID_SIZE for _ in range(GRID_SIZE)]

        # Create starting tunnel at surface
        for x in range(GRID_SIZE):
            for y in range(8):
                self.tunnels[y][x] = True

        # Create initial player tunnel
        for y in range(8, 16):
            self.tunnels[y][self.player_x] = True

        # Enemies
        self.enemies = []
        self.spawn_enemies()

        # Rocks
        self.rocks = []
        self.spawn_rocks()

        # Invincibility
        self.invincible = 0

        self.move_timer = 0
        self.move_delay = 0.08

    def spawn_enemies(self):
        """Spawn enemies for current level."""
        self.enemies = []
        num_enemies = 3 + self.level

        for i in range(num_enemies):
            # Place in lower portion of screen
            while True:
                ex = random.randint(5, 58)
                ey = random.randint(25, 55)
                # Don't spawn in tunnels or too close to player
                if not self.tunnels[ey][ex]:
                    dist = abs(ex - self.player_x) + abs(ey - self.player_y)
                    if dist > 20:
                        break

            enemy_type = 'pooka' if random.random() < 0.7 else 'fygar'
            self.enemies.append({
                'x': ex,
                'y': ey,
                'type': enemy_type,
                'dir': random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)]),
                'inflate': 0,  # 0-4, pops at 4
                'move_timer': 0,
                'ghost_mode': False,
                'ghost_timer': 0,
            })

            # Create small chamber around enemy
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    nx, ny = ex + dx, ey + dy
                    if 0 <= nx < GRID_SIZE and 8 <= ny < GRID_SIZE:
                        self.tunnels[ny][nx] = True

    def spawn_rocks(self):
        """Spawn rocks in the level."""
        self.rocks = []
        num_rocks = 2 + self.level // 2

        for _ in range(num_rocks):
            while True:
                rx = random.randint(10, 53)
                ry = random.randint(15, 45)
                if not self.tunnels[ry][rx]:
                    break

            self.rocks.append({
                'x': rx,
                'y': ry,
                'falling': False,
                'fall_timer': 0,
            })

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        self.move_timer += dt
        if self.invincible > 0:
            self.invincible -= dt

        # Player movement
        dx, dy = 0, 0
        if input_state.left:
            dx = -1
        elif input_state.right:
            dx = 1
        elif input_state.up:
            dy = -1
        elif input_state.down:
            dy = 1

        if (dx != 0 or dy != 0) and self.move_timer >= self.move_delay:
            self.move_timer = 0
            self.player_dir = (dx, dy)

            new_x = self.player_x + dx
            new_y = self.player_y + dy

            if 0 <= new_x < GRID_SIZE and 8 <= new_y < GRID_SIZE:
                # Dig tunnel
                self.tunnels[new_y][new_x] = True
                self.player_x = new_x
                self.player_y = new_y

        # Pump action
        if input_state.action_held:
            if not self.pump_active:
                self.pump_active = True
                self.pump_length = 0
                self.pump_timer = 0

            self.pump_timer += dt
            if self.pump_timer >= 0.1:
                self.pump_timer = 0
                self.pump_length = min(self.pump_length + 1, 8)

                # Check if pump hits enemy
                pump_x = self.player_x + self.player_dir[0] * self.pump_length
                pump_y = self.player_y + self.player_dir[1] * self.pump_length

                for enemy in self.enemies:
                    if abs(enemy['x'] - pump_x) <= 2 and abs(enemy['y'] - pump_y) <= 2:
                        enemy['inflate'] += 1
                        if enemy['inflate'] >= 4:
                            self.enemies.remove(enemy)
                            self.score += 200 if enemy['type'] == 'pooka' else 400
                        break
        else:
            self.pump_active = False
            self.pump_length = 0
            # Enemies deflate when not being pumped
            for enemy in self.enemies:
                if enemy['inflate'] > 0:
                    enemy['inflate'] = max(0, enemy['inflate'] - 1)

        # Update enemies
        self.update_enemies(dt)

        # Update rocks
        self.update_rocks(dt)

        # Check player-enemy collision
        if self.invincible <= 0:
            for enemy in self.enemies:
                if abs(enemy['x'] - self.player_x) <= 2 and abs(enemy['y'] - self.player_y) <= 2:
                    if enemy['inflate'] == 0:  # Can't hurt player while inflated
                        self.player_hit()
                        break

        # Check level complete
        if len(self.enemies) == 0:
            self.next_level()

    def update_enemies(self, dt: float):
        """Update enemy movement and behavior."""
        for enemy in self.enemies:
            if enemy['inflate'] > 0:
                continue  # Inflated enemies don't move

            enemy['move_timer'] += dt

            # Ghost mode - move through dirt toward player
            enemy['ghost_timer'] += dt
            if enemy['ghost_timer'] > 5.0 and not enemy['ghost_mode']:
                if random.random() < 0.3:
                    enemy['ghost_mode'] = True
                    enemy['ghost_timer'] = 0

            if enemy['ghost_mode']:
                if enemy['ghost_timer'] > 3.0:
                    enemy['ghost_mode'] = False
                    enemy['ghost_timer'] = 0

            move_speed = 0.15 if not enemy['ghost_mode'] else 0.2

            if enemy['move_timer'] >= move_speed:
                enemy['move_timer'] = 0

                if enemy['ghost_mode']:
                    # Move toward player through dirt
                    dx = 1 if self.player_x > enemy['x'] else -1 if self.player_x < enemy['x'] else 0
                    dy = 1 if self.player_y > enemy['y'] else -1 if self.player_y < enemy['y'] else 0

                    if random.random() < 0.5:
                        dx = 0
                    else:
                        dy = 0

                    new_x = enemy['x'] + dx
                    new_y = enemy['y'] + dy
                else:
                    # Normal movement - follow tunnels
                    dx, dy = enemy['dir']
                    new_x = enemy['x'] + dx
                    new_y = enemy['y'] + dy

                    # Check if can move in current direction
                    can_move = False
                    if 0 <= new_x < GRID_SIZE and 8 <= new_y < GRID_SIZE:
                        if self.tunnels[new_y][new_x]:
                            can_move = True

                    if not can_move:
                        # Try to turn
                        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
                        random.shuffle(directions)
                        for d in directions:
                            tx = enemy['x'] + d[0]
                            ty = enemy['y'] + d[1]
                            if 0 <= tx < GRID_SIZE and 8 <= ty < GRID_SIZE:
                                if self.tunnels[ty][tx]:
                                    enemy['dir'] = d
                                    new_x = tx
                                    new_y = ty
                                    can_move = True
                                    break

                    if not can_move:
                        continue

                # Actually move
                if 0 <= new_x < GRID_SIZE and 8 <= new_y < GRID_SIZE:
                    enemy['x'] = new_x
                    enemy['y'] = new_y

    def update_rocks(self, dt: float):
        """Update falling rocks."""
        for rock in self.rocks[:]:
            # Check if rock should start falling
            if not rock['falling']:
                # Check if tunnel below
                if rock['y'] + 3 < GRID_SIZE and self.tunnels[rock['y'] + 3][rock['x']]:
                    rock['fall_timer'] += dt
                    if rock['fall_timer'] > 0.5:
                        rock['falling'] = True
                        rock['fall_timer'] = 0
                else:
                    rock['fall_timer'] = 0
            else:
                # Falling
                rock['fall_timer'] += dt
                if rock['fall_timer'] >= 0.05:
                    rock['fall_timer'] = 0
                    rock['y'] += 1

                    # Dig tunnel as rock falls
                    for dx in range(-1, 2):
                        if 0 <= rock['x'] + dx < GRID_SIZE and rock['y'] < GRID_SIZE:
                            self.tunnels[rock['y']][rock['x'] + dx] = True

                    # Check if hit enemy
                    for enemy in self.enemies[:]:
                        if abs(enemy['x'] - rock['x']) <= 2 and abs(enemy['y'] - rock['y']) <= 2:
                            self.enemies.remove(enemy)
                            self.score += 500

                    # Check if hit player
                    if abs(self.player_x - rock['x']) <= 2 and abs(self.player_y - rock['y']) <= 2:
                        if self.invincible <= 0:
                            self.player_hit()

                    # Check if hit ground
                    if rock['y'] >= GRID_SIZE - 2 or (
                        rock['y'] + 1 < GRID_SIZE and not self.tunnels[rock['y'] + 1][rock['x']]
                    ):
                        self.rocks.remove(rock)

    def player_hit(self):
        """Handle player death."""
        self.lives -= 1
        if self.lives <= 0:
            self.state = GameState.GAME_OVER
        else:
            self.invincible = 2.0
            self.player_x = 32
            self.player_y = 12

    def next_level(self):
        """Advance to next level."""
        self.level += 1
        self.player_x = 32
        self.player_y = 8

        # Reset tunnels
        self.tunnels = [[False] * GRID_SIZE for _ in range(GRID_SIZE)]
        for x in range(GRID_SIZE):
            for y in range(8):
                self.tunnels[y][x] = True
        for y in range(8, 16):
            self.tunnels[y][self.player_x] = True

        self.spawn_enemies()
        self.spawn_rocks()

    def draw(self):
        self.display.clear(self.DIRT_COLOR)

        # Draw sky
        for y in range(8):
            self.display.draw_line(0, y, 63, y, Colors.BLUE)

        # Draw tunnels (darker where dug)
        for y in range(8, GRID_SIZE):
            for x in range(GRID_SIZE):
                if self.tunnels[y][x]:
                    self.display.set_pixel(x, y, self.TUNNEL_COLOR)

        # Draw depth layers (stripes)
        for y in range(8, GRID_SIZE, 12):
            for x in range(GRID_SIZE):
                if not self.tunnels[y][x]:
                    self.display.set_pixel(x, y, self.DIRT_DARK)

        # Draw rocks
        for rock in self.rocks:
            self.draw_rock(rock['x'], rock['y'])

        # Draw enemies
        for enemy in self.enemies:
            self.draw_enemy(enemy)

        # Draw pump
        if self.pump_active and self.pump_length > 0:
            self.draw_pump()

        # Draw player
        if self.invincible <= 0 or int(self.invincible * 10) % 2 == 0:
            self.draw_player()

        # HUD
        self.display.draw_text_small(1, 1, f"{self.score}", Colors.WHITE)
        for i in range(self.lives - 1):
            self.display.set_pixel(58 - i * 4, 2, Colors.WHITE)

    def draw_player(self):
        """Draw the player."""
        x, y = self.player_x, self.player_y

        # Body
        self.display.set_pixel(x, y, self.PLAYER_COLOR)
        self.display.set_pixel(x - 1, y, self.PLAYER_COLOR)
        self.display.set_pixel(x + 1, y, self.PLAYER_COLOR)
        self.display.set_pixel(x, y - 1, self.PLAYER_COLOR)
        self.display.set_pixel(x, y + 1, Colors.BLUE)  # Legs

        # Direction indicator
        dx, dy = self.player_dir
        self.display.set_pixel(x + dx * 2, y + dy * 2, Colors.RED)

    def draw_enemy(self, enemy: dict):
        """Draw an enemy."""
        x, y = enemy['x'], enemy['y']
        color = self.POOKA_COLOR if enemy['type'] == 'pooka' else self.FYGAR_COLOR

        # Inflate makes them bigger
        size = 1 + enemy['inflate']

        for dy in range(-size, size + 1):
            for dx in range(-size, size + 1):
                if abs(dx) + abs(dy) <= size:
                    px, py = x + dx, y + dy
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        self.display.set_pixel(px, py, color)

        # Eyes
        if enemy['inflate'] < 3:
            self.display.set_pixel(x - 1, y - 1, Colors.WHITE)
            self.display.set_pixel(x + 1, y - 1, Colors.WHITE)

        # Ghost mode indicator
        if enemy['ghost_mode']:
            self.display.set_pixel(x, y - size - 1, Colors.CYAN)

    def draw_rock(self, x: int, y: int):
        """Draw a rock."""
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                if abs(dx) + abs(dy) <= 2:
                    px, py = x + dx, y + dy
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        self.display.set_pixel(px, py, self.ROCK_COLOR)

    def draw_pump(self):
        """Draw the pump hose."""
        x, y = self.player_x, self.player_y
        dx, dy = self.player_dir

        for i in range(1, self.pump_length + 1):
            px = x + dx * i
            py = y + dy * i
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                self.display.set_pixel(px, py, Colors.YELLOW)

    def draw_game_over(self):
        self.display.clear(Colors.BLACK)
        self.display.draw_text_small(8, 20, "GAME OVER", Colors.RED)
        self.display.draw_text_small(10, 32, f"SCORE:{self.score}", Colors.WHITE)
        self.display.draw_text_small(4, 50, "SPACE:RETRY", Colors.GRAY)
