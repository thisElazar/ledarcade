"""
Lode Runner - Platform Puzzle Game
==================================
Collect all gold and escape! Dig holes to trap enemies.

Controls:
  Arrow Keys - Move (Left/Right/Climb)
  Space      - Dig (in direction you're facing)
"""

import random
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


class LodeRunner(Game):
    name = "LODERUN"
    description = "Dig & Escape!"
    category = "arcade"

    # Tile types
    EMPTY = 0
    BRICK = 1
    LADDER = 2
    ROPE = 3
    GOLD = 4
    SOLID = 5  # Can't be dug

    # Colors
    BRICK_COLOR = (180, 100, 60)
    LADDER_COLOR = (200, 180, 100)
    ROPE_COLOR = (139, 90, 43)
    GOLD_COLOR = Colors.YELLOW
    SOLID_COLOR = (100, 100, 110)
    PLAYER_COLOR = Colors.CYAN
    ENEMY_COLOR = Colors.RED

    # Level dimensions
    LEVEL_WIDTH = 32
    LEVEL_HEIGHT = 28
    TILE_SIZE = 2
    OFFSET_Y = 8

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0
        self.lives = 3
        self.level = 1

        # Level data
        self.tiles = [[self.EMPTY] * self.LEVEL_WIDTH for _ in range(self.LEVEL_HEIGHT)]

        # Player state
        self.player_x = 2
        self.player_y = self.LEVEL_HEIGHT - 2
        self.player_falling = False
        self.player_facing = 1  # 1 = right, -1 = left

        # Enemies
        self.enemies = []

        # Gold remaining
        self.gold_remaining = 0

        # Dug holes: {(x, y): timer}
        self.holes = {}

        # Exit ladder (appears when all gold collected)
        self.exit_open = False

        self.move_timer = 0
        self.move_delay = 0.08
        self.dig_cooldown = 0

        self.generate_level()

    def generate_level(self):
        """Generate a random level."""
        # Clear
        self.tiles = [[self.EMPTY] * self.LEVEL_WIDTH for _ in range(self.LEVEL_HEIGHT)]
        self.enemies = []
        self.holes = {}

        # Floor
        for x in range(self.LEVEL_WIDTH):
            self.tiles[self.LEVEL_HEIGHT - 1][x] = self.SOLID

        # Generate platforms
        num_platforms = 6 + self.level
        for _ in range(num_platforms):
            px = random.randint(0, self.LEVEL_WIDTH - 8)
            py = random.randint(4, self.LEVEL_HEIGHT - 4)
            pw = random.randint(4, 10)

            for x in range(px, min(px + pw, self.LEVEL_WIDTH)):
                if self.tiles[py][x] == self.EMPTY:
                    self.tiles[py][x] = self.BRICK

        # Generate ladders connecting platforms
        num_ladders = 4 + self.level // 2
        for _ in range(num_ladders):
            lx = random.randint(1, self.LEVEL_WIDTH - 2)
            ly1 = random.randint(4, self.LEVEL_HEIGHT - 6)
            ly2 = ly1 + random.randint(3, 8)

            for y in range(ly1, min(ly2, self.LEVEL_HEIGHT)):
                if self.tiles[y][lx] == self.EMPTY or self.tiles[y][lx] == self.BRICK:
                    self.tiles[y][lx] = self.LADDER

        # Generate ropes
        num_ropes = 2 + self.level // 3
        for _ in range(num_ropes):
            rx = random.randint(2, self.LEVEL_WIDTH - 6)
            ry = random.randint(4, self.LEVEL_HEIGHT - 8)
            rw = random.randint(4, 8)

            for x in range(rx, min(rx + rw, self.LEVEL_WIDTH)):
                if self.tiles[ry][x] == self.EMPTY:
                    self.tiles[ry][x] = self.ROPE

        # Place gold
        self.gold_remaining = 5 + self.level * 2
        placed = 0
        attempts = 0
        while placed < self.gold_remaining and attempts < 200:
            gx = random.randint(1, self.LEVEL_WIDTH - 2)
            gy = random.randint(2, self.LEVEL_HEIGHT - 3)

            # Gold should be on a surface
            if self.tiles[gy][gx] == self.EMPTY and self.tiles[gy + 1][gx] in [self.BRICK, self.SOLID, self.LADDER]:
                self.tiles[gy][gx] = self.GOLD
                placed += 1
            attempts += 1

        self.gold_remaining = placed

        # Place player
        self.player_x = 2
        self.player_y = self.LEVEL_HEIGHT - 2
        # Ensure player start is clear
        self.tiles[self.player_y][self.player_x] = self.EMPTY

        # Add starting ladder near player so they can climb up
        start_ladder_x = 4
        for y in range(self.LEVEL_HEIGHT - 8, self.LEVEL_HEIGHT - 1):
            self.tiles[y][start_ladder_x] = self.LADDER
        # Add a platform at the top of starting ladder
        for x in range(start_ladder_x - 2, start_ladder_x + 4):
            if 0 <= x < self.LEVEL_WIDTH and self.tiles[self.LEVEL_HEIGHT - 8][x] == self.EMPTY:
                self.tiles[self.LEVEL_HEIGHT - 8][x] = self.BRICK

        # Place enemies
        num_enemies = 2 + self.level
        for _ in range(num_enemies):
            attempts = 0
            while attempts < 50:
                ex = random.randint(5, self.LEVEL_WIDTH - 2)
                ey = random.randint(2, self.LEVEL_HEIGHT - 3)

                # Enemy should be on surface and away from player
                if self.tiles[ey][ex] == self.EMPTY:
                    if self.tiles[ey + 1][ex] in [self.BRICK, self.SOLID, self.LADDER]:
                        dist = abs(ex - self.player_x) + abs(ey - self.player_y)
                        if dist > 10:
                            self.enemies.append({
                                'x': ex,
                                'y': ey,
                                'falling': False,
                                'trapped': False,
                                'trap_timer': 0,
                                'move_timer': 0,
                            })
                            break
                attempts += 1

        # Exit ladder at top
        self.exit_x = self.LEVEL_WIDTH // 2
        self.exit_open = False

    def is_solid(self, x: int, y: int) -> bool:
        """Check if a tile blocks movement."""
        if x < 0 or x >= self.LEVEL_WIDTH or y < 0 or y >= self.LEVEL_HEIGHT:
            return True
        tile = self.tiles[y][x]
        if (x, y) in self.holes:
            return False  # Holes are passable
        return tile in [self.BRICK, self.SOLID]

    def is_supported(self, x: int, y: int) -> bool:
        """Check if position has support (not falling)."""
        # On ladder
        if 0 <= y < self.LEVEL_HEIGHT and self.tiles[y][x] == self.LADDER:
            return True
        # On rope
        if 0 <= y < self.LEVEL_HEIGHT and self.tiles[y][x] == self.ROPE:
            return True
        # On solid ground
        if y + 1 >= self.LEVEL_HEIGHT:
            return True
        below = self.tiles[y + 1][x]
        if below in [self.BRICK, self.SOLID, self.LADDER]:
            return True
        if (x, y + 1) in self.holes:
            return False
        return False

    def dig_hole(self, x: int, y: int) -> bool:
        """Dig a hole in a brick. Returns True if successful."""
        if 0 <= x < self.LEVEL_WIDTH and 0 <= y < self.LEVEL_HEIGHT:
            if self.tiles[y][x] == self.BRICK:
                self.holes[(x, y)] = 3.0  # Hole lasts 3 seconds
                return True
        return False

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        self.move_timer += dt

        # Update holes
        for pos in list(self.holes.keys()):
            self.holes[pos] -= dt
            if self.holes[pos] <= 0:
                del self.holes[pos]
                # Check if enemy was in hole
                for enemy in self.enemies:
                    if (enemy['x'], enemy['y']) == pos:
                        enemy['trapped'] = False

        # Player movement
        if self.move_timer >= self.move_delay:
            moved = False
            new_x, new_y = self.player_x, self.player_y

            # Horizontal movement
            if input_state.left and not self.is_solid(self.player_x - 1, self.player_y):
                new_x = self.player_x - 1
                self.player_facing = -1
                moved = True
            elif input_state.right and not self.is_solid(self.player_x + 1, self.player_y):
                new_x = self.player_x + 1
                self.player_facing = 1
                moved = True

            # Vertical movement (ladders)
            current_tile = self.tiles[self.player_y][self.player_x]
            if input_state.up:
                if current_tile == self.LADDER or (self.player_y > 0 and self.tiles[self.player_y - 1][self.player_x] == self.LADDER):
                    if not self.is_solid(self.player_x, self.player_y - 1):
                        new_y = self.player_y - 1
                        moved = True
            elif input_state.down:
                if current_tile == self.LADDER or (self.player_y + 1 < self.LEVEL_HEIGHT and self.tiles[self.player_y + 1][self.player_x] == self.LADDER):
                    if not self.is_solid(self.player_x, self.player_y + 1):
                        new_y = self.player_y + 1
                        moved = True
                elif (self.player_x, self.player_y + 1) in self.holes:
                    new_y = self.player_y + 1
                    moved = True

            if moved:
                self.move_timer = 0
                self.player_x = new_x
                self.player_y = new_y

        # Digging - separate from move timer for responsiveness
        if self.dig_cooldown > 0:
            self.dig_cooldown -= dt

        if input_state.action and self.dig_cooldown <= 0:
            # Dig in the direction player is facing
            dig_x = self.player_x + self.player_facing
            if self.dig_hole(dig_x, self.player_y + 1):
                self.dig_cooldown = 0.3  # Cooldown after successful dig

        # Apply gravity to player
        if not self.is_supported(self.player_x, self.player_y):
            if self.tiles[self.player_y][self.player_x] != self.ROPE:
                self.player_y += 1

        # Collect gold
        if self.tiles[self.player_y][self.player_x] == self.GOLD:
            self.tiles[self.player_y][self.player_x] = self.EMPTY
            self.gold_remaining -= 1
            self.score += 100

            # Open exit when all gold collected
            if self.gold_remaining <= 0:
                self.exit_open = True
                # Add exit ladder
                for y in range(self.LEVEL_HEIGHT):
                    self.tiles[y][self.exit_x] = self.LADDER

        # Check win condition
        if self.exit_open and self.player_y <= 1:
            self.next_level()

        # Update enemies
        self.update_enemies(dt)

        # Check enemy collision
        for enemy in self.enemies:
            if not enemy['trapped']:
                if enemy['x'] == self.player_x and enemy['y'] == self.player_y:
                    self.player_hit()
                    break

    def update_enemies(self, dt: float):
        """Update enemy AI."""
        for enemy in self.enemies:
            enemy['move_timer'] += dt

            # Check if in hole
            if (enemy['x'], enemy['y']) in self.holes:
                enemy['trapped'] = True
                enemy['trap_timer'] = 2.5

            if enemy['trapped']:
                enemy['trap_timer'] -= dt
                if enemy['trap_timer'] <= 0:
                    # Escape from hole
                    enemy['trapped'] = False
                    enemy['y'] -= 1
                continue

            # Apply gravity
            if not self.is_supported(enemy['x'], enemy['y']):
                if self.tiles[enemy['y']][enemy['x']] != self.ROPE:
                    enemy['y'] += 1
                    continue

            # Chase player
            if enemy['move_timer'] >= 0.15:
                enemy['move_timer'] = 0

                dx = 0
                dy = 0

                # Horizontal chase
                if self.player_x < enemy['x'] and not self.is_solid(enemy['x'] - 1, enemy['y']):
                    dx = -1
                elif self.player_x > enemy['x'] and not self.is_solid(enemy['x'] + 1, enemy['y']):
                    dx = 1

                # Vertical chase (ladders)
                current_tile = self.tiles[enemy['y']][enemy['x']]
                if dx == 0 or random.random() < 0.3:
                    if self.player_y < enemy['y'] and current_tile == self.LADDER:
                        if not self.is_solid(enemy['x'], enemy['y'] - 1):
                            dy = -1
                            dx = 0
                    elif self.player_y > enemy['y']:
                        if enemy['y'] + 1 < self.LEVEL_HEIGHT and self.tiles[enemy['y'] + 1][enemy['x']] == self.LADDER:
                            dy = 1
                            dx = 0

                enemy['x'] += dx
                enemy['y'] += dy

    def player_hit(self):
        """Handle player death."""
        self.lives -= 1
        if self.lives <= 0:
            self.state = GameState.GAME_OVER
        else:
            self.player_x = 2
            self.player_y = self.LEVEL_HEIGHT - 2
            # Reset enemies
            for enemy in self.enemies:
                enemy['trapped'] = False

    def next_level(self):
        """Advance to next level."""
        self.level += 1
        self.score += 500
        self.generate_level()

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Draw tiles
        for y in range(self.LEVEL_HEIGHT):
            for x in range(self.LEVEL_WIDTH):
                self.draw_tile(x, y)

        # Draw holes
        for (hx, hy), timer in self.holes.items():
            px = hx * self.TILE_SIZE
            py = self.OFFSET_Y + hy * self.TILE_SIZE
            self.display.set_pixel(px, py, Colors.BLACK)
            self.display.set_pixel(px + 1, py, Colors.BLACK)

        # Draw enemies
        for enemy in self.enemies:
            self.draw_enemy(enemy)

        # Draw player
        self.draw_player()

        # Draw exit indicator
        if self.exit_open:
            self.display.set_pixel(self.exit_x * self.TILE_SIZE, self.OFFSET_Y - 1, Colors.GREEN)
            self.display.set_pixel(self.exit_x * self.TILE_SIZE + 1, self.OFFSET_Y - 1, Colors.GREEN)

        # HUD
        self.display.draw_text_small(1, 1, f"{self.score}", Colors.WHITE)
        self.display.draw_text_small(25, 1, f"G:{self.gold_remaining}", Colors.YELLOW)
        for i in range(self.lives - 1):
            self.display.set_pixel(58 - i * 3, 2, Colors.CYAN)

    def draw_tile(self, x: int, y: int):
        """Draw a single tile."""
        tile = self.tiles[y][x]
        px = x * self.TILE_SIZE
        py = self.OFFSET_Y + y * self.TILE_SIZE

        if tile == self.BRICK:
            self.display.set_pixel(px, py, self.BRICK_COLOR)
            self.display.set_pixel(px + 1, py, self.BRICK_COLOR)
            self.display.set_pixel(px, py + 1, (140, 80, 50))
            self.display.set_pixel(px + 1, py + 1, (140, 80, 50))
        elif tile == self.LADDER:
            self.display.set_pixel(px, py, self.LADDER_COLOR)
            self.display.set_pixel(px + 1, py, self.LADDER_COLOR)
        elif tile == self.ROPE:
            self.display.set_pixel(px, py, self.ROPE_COLOR)
            self.display.set_pixel(px + 1, py, self.ROPE_COLOR)
        elif tile == self.GOLD:
            self.display.set_pixel(px, py, self.GOLD_COLOR)
            self.display.set_pixel(px + 1, py + 1, self.GOLD_COLOR)
        elif tile == self.SOLID:
            self.display.set_pixel(px, py, self.SOLID_COLOR)
            self.display.set_pixel(px + 1, py, self.SOLID_COLOR)
            self.display.set_pixel(px, py + 1, self.SOLID_COLOR)
            self.display.set_pixel(px + 1, py + 1, self.SOLID_COLOR)

    def draw_player(self):
        """Draw the player."""
        px = self.player_x * self.TILE_SIZE
        py = self.OFFSET_Y + self.player_y * self.TILE_SIZE

        self.display.set_pixel(px, py, self.PLAYER_COLOR)
        self.display.set_pixel(px + 1, py, self.PLAYER_COLOR)
        self.display.set_pixel(px, py + 1, self.PLAYER_COLOR)
        self.display.set_pixel(px + 1, py + 1, Colors.BLUE)

    def draw_enemy(self, enemy: dict):
        """Draw an enemy."""
        px = enemy['x'] * self.TILE_SIZE
        py = self.OFFSET_Y + enemy['y'] * self.TILE_SIZE

        color = Colors.ORANGE if enemy['trapped'] else self.ENEMY_COLOR

        self.display.set_pixel(px, py, color)
        self.display.set_pixel(px + 1, py, color)
        self.display.set_pixel(px, py + 1, color)
        self.display.set_pixel(px + 1, py + 1, color)

    def draw_game_over(self):
        self.display.clear(Colors.BLACK)
        self.display.draw_text_small(8, 20, "GAME OVER", Colors.RED)
        self.display.draw_text_small(10, 32, f"SCORE:{self.score}", Colors.WHITE)
        self.display.draw_text_small(4, 50, "SPACE:RETRY", Colors.GRAY)
