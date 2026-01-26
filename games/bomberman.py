"""
Bomberman - Grid-Based Bomb Action
==================================
Place bombs to destroy walls and enemies. Find the exit!

Controls:
  Arrow Keys - Move
  Space      - Place bomb
"""

import random
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


class Bomberman(Game):
    name = "BOMBERMAN"
    description = "Bomb & Blast!"
    category = "arcade"

    # Grid dimensions
    GRID_WIDTH = 15   # Odd number for proper wall pattern
    GRID_HEIGHT = 13
    TILE_SIZE = 4

    # Offset to center the grid
    OFFSET_X = (GRID_SIZE - GRID_WIDTH * TILE_SIZE) // 2
    OFFSET_Y = 6

    # Tile types
    EMPTY = 0
    WALL = 1          # Indestructible
    BRICK = 2         # Destructible
    BOMB = 3
    EXPLOSION = 4
    EXIT = 5
    POWERUP_BOMB = 6  # Extra bomb
    POWERUP_FIRE = 7  # Bigger explosion
    POWERUP_SPEED = 8 # Faster movement

    # Colors
    WALL_COLOR = (80, 80, 100)
    BRICK_COLOR = (180, 100, 60)
    BRICK_DARK = (140, 80, 50)
    FLOOR_COLOR = (40, 60, 40)
    BOMB_COLOR = (20, 20, 20)
    BOMB_FUSE = Colors.RED
    EXPLOSION_COLOR = Colors.ORANGE
    EXPLOSION_CENTER = Colors.YELLOW
    EXIT_COLOR = (100, 200, 100)
    PLAYER_COLOR = Colors.WHITE
    PLAYER_FACE = (255, 200, 150)
    ENEMY_COLOR = (200, 50, 200)  # Purple balloon enemy

    POWERUP_BOMB_COLOR = Colors.BLUE
    POWERUP_FIRE_COLOR = Colors.RED
    POWERUP_SPEED_COLOR = Colors.YELLOW

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0
        self.lives = 3
        self.level = 1

        # Player state
        self.player_x = 1
        self.player_y = 1
        self.player_speed = 1  # Tiles per move
        self.move_timer = 0.0
        self.move_delay = 0.12

        # Bomb stats
        self.max_bombs = 1
        self.fire_power = 1  # Explosion radius
        self.active_bombs = []  # List of bomb dicts

        # Explosions: list of {'x', 'y', 'timer'}
        self.explosions = []

        # Enemies
        self.enemies = []

        # Grid
        self.grid = [[self.EMPTY] * self.GRID_WIDTH for _ in range(self.GRID_HEIGHT)]

        # Animation
        self.anim_timer = 0.0
        self.player_frame = 0
        self.player_facing = 1  # 1=right, -1=left

        # Win condition
        self.exit_x = 0
        self.exit_y = 0
        self.exit_revealed = False

        self.generate_level()

    def generate_level(self):
        """Generate a new level layout."""
        # Clear grid
        self.grid = [[self.EMPTY] * self.GRID_WIDTH for _ in range(self.GRID_HEIGHT)]

        # Place indestructible walls in grid pattern
        for y in range(self.GRID_HEIGHT):
            for x in range(self.GRID_WIDTH):
                # Border walls
                if x == 0 or x == self.GRID_WIDTH - 1 or y == 0 or y == self.GRID_HEIGHT - 1:
                    self.grid[y][x] = self.WALL
                # Interior grid pattern (every other tile)
                elif x % 2 == 0 and y % 2 == 0:
                    self.grid[y][x] = self.WALL

        # Place destructible bricks randomly
        brick_chance = 0.4 + self.level * 0.05
        for y in range(1, self.GRID_HEIGHT - 1):
            for x in range(1, self.GRID_WIDTH - 1):
                if self.grid[y][x] == self.EMPTY:
                    # Keep starting area clear
                    if (x <= 2 and y <= 2):
                        continue
                    if random.random() < brick_chance:
                        self.grid[y][x] = self.BRICK

        # Place exit under a random brick (far from start)
        exit_candidates = []
        for y in range(self.GRID_HEIGHT // 2, self.GRID_HEIGHT - 1):
            for x in range(self.GRID_WIDTH // 2, self.GRID_WIDTH - 1):
                if self.grid[y][x] == self.BRICK:
                    exit_candidates.append((x, y))

        if exit_candidates:
            self.exit_x, self.exit_y = random.choice(exit_candidates)
        else:
            # Fallback
            self.exit_x, self.exit_y = self.GRID_WIDTH - 2, self.GRID_HEIGHT - 2

        self.exit_revealed = False

        # Place powerups under random bricks
        powerup_types = [self.POWERUP_BOMB, self.POWERUP_FIRE, self.POWERUP_SPEED]
        num_powerups = 2 + self.level // 2

        brick_positions = []
        for y in range(1, self.GRID_HEIGHT - 1):
            for x in range(1, self.GRID_WIDTH - 1):
                if self.grid[y][x] == self.BRICK and (x, y) != (self.exit_x, self.exit_y):
                    brick_positions.append((x, y))

        random.shuffle(brick_positions)
        self.hidden_powerups = {}  # {(x,y): powerup_type}
        for i in range(min(num_powerups, len(brick_positions))):
            pos = brick_positions[i]
            self.hidden_powerups[pos] = random.choice(powerup_types)

        # Place enemies
        self.enemies = []
        num_enemies = 3 + self.level

        enemy_positions = []
        for y in range(3, self.GRID_HEIGHT - 1):
            for x in range(3, self.GRID_WIDTH - 1):
                if self.grid[y][x] == self.EMPTY:
                    enemy_positions.append((x, y))

        random.shuffle(enemy_positions)
        for i in range(min(num_enemies, len(enemy_positions))):
            ex, ey = enemy_positions[i]
            self.enemies.append({
                'x': ex,
                'y': ey,
                'move_timer': random.random(),
                'direction': random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)]),
            })

        # Reset player
        self.player_x = 1
        self.player_y = 1
        self.active_bombs = []
        self.explosions = []

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        self.anim_timer += dt

        # Animation
        if self.anim_timer > 0.15:
            self.anim_timer = 0
            self.player_frame = (self.player_frame + 1) % 2

        # Update move timer
        self.move_timer += dt

        # Player movement
        if self.move_timer >= self.move_delay:
            dx, dy = 0, 0
            if input_state.up:
                dy = -1
            elif input_state.down:
                dy = 1
            elif input_state.left:
                dx = -1
                self.player_facing = -1
            elif input_state.right:
                dx = 1
                self.player_facing = 1

            if dx != 0 or dy != 0:
                new_x = self.player_x + dx
                new_y = self.player_y + dy

                if self.can_move_to(new_x, new_y):
                    self.player_x = new_x
                    self.player_y = new_y
                    self.move_timer = 0

                    # Check powerup pickup
                    self.check_powerup_pickup()

                    # Check exit
                    if self.exit_revealed and new_x == self.exit_x and new_y == self.exit_y:
                        self.next_level()
                        return

        # Place bomb
        if input_state.action:
            self.place_bomb()

        # Update bombs
        self.update_bombs(dt)

        # Update explosions
        self.update_explosions(dt)

        # Update enemies
        self.update_enemies(dt)

        # Check player collision with enemies
        self.check_enemy_collision()

        # Check player collision with explosions
        if self.grid[self.player_y][self.player_x] == self.EXPLOSION:
            self.player_die()

    def can_move_to(self, x, y):
        """Check if player can move to position."""
        if x < 0 or x >= self.GRID_WIDTH or y < 0 or y >= self.GRID_HEIGHT:
            return False
        tile = self.grid[y][x]
        # Can walk on empty, exit, powerups
        if tile in [self.EMPTY, self.EXIT, self.POWERUP_BOMB, self.POWERUP_FIRE, self.POWERUP_SPEED]:
            return True
        # Can walk through own explosions (briefly invincible)
        return False

    def place_bomb(self):
        """Place a bomb at player's position."""
        # Check if we can place more bombs
        if len(self.active_bombs) >= self.max_bombs:
            return

        # Check if there's already a bomb here
        for bomb in self.active_bombs:
            if bomb['x'] == self.player_x and bomb['y'] == self.player_y:
                return

        self.active_bombs.append({
            'x': self.player_x,
            'y': self.player_y,
            'timer': 3.0,  # 3 seconds until explosion
        })

    def update_bombs(self, dt: float):
        """Update bomb timers and trigger explosions."""
        bombs_to_explode = []

        for bomb in self.active_bombs:
            bomb['timer'] -= dt
            if bomb['timer'] <= 0:
                bombs_to_explode.append(bomb)

        for bomb in bombs_to_explode:
            self.active_bombs.remove(bomb)
            self.trigger_explosion(bomb['x'], bomb['y'])

    def trigger_explosion(self, x, y):
        """Create explosion at position."""
        # Center explosion
        self.create_explosion_at(x, y)

        # Spread in 4 directions
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        for dx, dy in directions:
            for dist in range(1, self.fire_power + 1):
                ex, ey = x + dx * dist, y + dy * dist

                if ex < 0 or ex >= self.GRID_WIDTH or ey < 0 or ey >= self.GRID_HEIGHT:
                    break

                tile = self.grid[ey][ex]

                if tile == self.WALL:
                    break  # Stop at walls

                if tile == self.BRICK:
                    # Destroy brick
                    self.grid[ey][ex] = self.EMPTY
                    self.create_explosion_at(ex, ey)
                    self.score += 10

                    # Check for hidden items
                    if (ex, ey) == (self.exit_x, self.exit_y):
                        self.grid[ey][ex] = self.EXIT
                        self.exit_revealed = True
                    elif (ex, ey) in self.hidden_powerups:
                        self.grid[ey][ex] = self.hidden_powerups[(ex, ey)]
                        del self.hidden_powerups[(ex, ey)]

                    break  # Stop after destroying brick

                # Create explosion in empty space
                self.create_explosion_at(ex, ey)

                # Chain reaction - explode other bombs
                for bomb in self.active_bombs[:]:
                    if bomb['x'] == ex and bomb['y'] == ey:
                        self.active_bombs.remove(bomb)
                        self.trigger_explosion(ex, ey)

        # Kill enemies in explosions
        for enemy in self.enemies[:]:
            if self.grid[enemy['y']][enemy['x']] == self.EXPLOSION:
                self.enemies.remove(enemy)
                self.score += 100

    def create_explosion_at(self, x, y):
        """Create explosion effect at position."""
        # Don't overwrite walls or already existing tiles
        if self.grid[y][x] in [self.WALL, self.BRICK]:
            return

        # Temporarily mark as explosion
        old_tile = self.grid[y][x]
        self.grid[y][x] = self.EXPLOSION

        self.explosions.append({
            'x': x,
            'y': y,
            'timer': 0.5,
            'old_tile': old_tile if old_tile not in [self.EXPLOSION, self.BOMB] else self.EMPTY,
        })

    def update_explosions(self, dt: float):
        """Update explosion timers."""
        explosions_to_remove = []

        for exp in self.explosions:
            exp['timer'] -= dt
            if exp['timer'] <= 0:
                explosions_to_remove.append(exp)

        for exp in explosions_to_remove:
            self.explosions.remove(exp)
            # Restore tile (might be exit or powerup)
            if self.grid[exp['y']][exp['x']] == self.EXPLOSION:
                self.grid[exp['y']][exp['x']] = exp['old_tile']

    def check_powerup_pickup(self):
        """Check if player picks up a powerup."""
        tile = self.grid[self.player_y][self.player_x]

        if tile == self.POWERUP_BOMB:
            self.max_bombs += 1
            self.grid[self.player_y][self.player_x] = self.EMPTY
            self.score += 50
        elif tile == self.POWERUP_FIRE:
            self.fire_power += 1
            self.grid[self.player_y][self.player_x] = self.EMPTY
            self.score += 50
        elif tile == self.POWERUP_SPEED:
            self.move_delay = max(0.06, self.move_delay - 0.02)
            self.grid[self.player_y][self.player_x] = self.EMPTY
            self.score += 50

    def update_enemies(self, dt: float):
        """Update enemy movement."""
        for enemy in self.enemies:
            enemy['move_timer'] += dt

            if enemy['move_timer'] >= 0.4:
                enemy['move_timer'] = 0

                dx, dy = enemy['direction']
                new_x = enemy['x'] + dx
                new_y = enemy['y'] + dy

                # Check if can move
                can_move = True
                if new_x < 1 or new_x >= self.GRID_WIDTH - 1:
                    can_move = False
                elif new_y < 1 or new_y >= self.GRID_HEIGHT - 1:
                    can_move = False
                elif self.grid[new_y][new_x] not in [self.EMPTY, self.EXIT]:
                    can_move = False

                # Also avoid bombs
                for bomb in self.active_bombs:
                    if bomb['x'] == new_x and bomb['y'] == new_y:
                        can_move = False

                if can_move:
                    enemy['x'] = new_x
                    enemy['y'] = new_y
                else:
                    # Change direction
                    enemy['direction'] = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])

    def check_enemy_collision(self):
        """Check if player collides with enemy."""
        for enemy in self.enemies:
            if enemy['x'] == self.player_x and enemy['y'] == self.player_y:
                self.player_die()
                return

    def player_die(self):
        """Handle player death."""
        self.lives -= 1
        if self.lives <= 0:
            self.state = GameState.GAME_OVER
        else:
            # Reset position
            self.player_x = 1
            self.player_y = 1
            self.active_bombs.clear()
            self.explosions.clear()

            # Clear explosion tiles
            for y in range(self.GRID_HEIGHT):
                for x in range(self.GRID_WIDTH):
                    if self.grid[y][x] == self.EXPLOSION:
                        self.grid[y][x] = self.EMPTY

    def next_level(self):
        """Advance to next level."""
        self.level += 1
        self.score += 500 * self.level
        self.generate_level()

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Draw grid
        for y in range(self.GRID_HEIGHT):
            for x in range(self.GRID_WIDTH):
                self.draw_tile(x, y)

        # Draw bombs
        for bomb in self.active_bombs:
            self.draw_bomb(bomb)

        # Draw enemies
        for enemy in self.enemies:
            self.draw_enemy(enemy)

        # Draw player
        self.draw_player()

        # Draw HUD
        self.draw_hud()

    def draw_tile(self, x, y):
        """Draw a single tile."""
        px = self.OFFSET_X + x * self.TILE_SIZE
        py = self.OFFSET_Y + y * self.TILE_SIZE
        tile = self.grid[y][x]

        if tile == self.WALL:
            # Indestructible wall
            for dy in range(self.TILE_SIZE):
                for dx in range(self.TILE_SIZE):
                    self.display.set_pixel(px + dx, py + dy, self.WALL_COLOR)
        elif tile == self.BRICK:
            # Destructible brick with pattern
            for dy in range(self.TILE_SIZE):
                for dx in range(self.TILE_SIZE):
                    color = self.BRICK_COLOR if (dx + dy) % 2 == 0 else self.BRICK_DARK
                    self.display.set_pixel(px + dx, py + dy, color)
        elif tile == self.EXPLOSION:
            # Explosion effect
            for dy in range(self.TILE_SIZE):
                for dx in range(self.TILE_SIZE):
                    if (dx == 1 or dx == 2) and (dy == 1 or dy == 2):
                        self.display.set_pixel(px + dx, py + dy, self.EXPLOSION_CENTER)
                    else:
                        self.display.set_pixel(px + dx, py + dy, self.EXPLOSION_COLOR)
        elif tile == self.EXIT:
            # Exit door
            for dy in range(self.TILE_SIZE):
                for dx in range(self.TILE_SIZE):
                    if dx == 0 or dx == self.TILE_SIZE - 1 or dy == 0:
                        self.display.set_pixel(px + dx, py + dy, self.EXIT_COLOR)
                    else:
                        self.display.set_pixel(px + dx, py + dy, (60, 120, 60))
        elif tile == self.POWERUP_BOMB:
            self.draw_powerup(px, py, self.POWERUP_BOMB_COLOR)
        elif tile == self.POWERUP_FIRE:
            self.draw_powerup(px, py, self.POWERUP_FIRE_COLOR)
        elif tile == self.POWERUP_SPEED:
            self.draw_powerup(px, py, self.POWERUP_SPEED_COLOR)
        else:
            # Empty floor
            for dy in range(self.TILE_SIZE):
                for dx in range(self.TILE_SIZE):
                    self.display.set_pixel(px + dx, py + dy, self.FLOOR_COLOR)

    def draw_powerup(self, px, py, color):
        """Draw a powerup icon."""
        # Floor background
        for dy in range(self.TILE_SIZE):
            for dx in range(self.TILE_SIZE):
                self.display.set_pixel(px + dx, py + dy, self.FLOOR_COLOR)
        # Powerup icon
        self.display.set_pixel(px + 1, py + 1, color)
        self.display.set_pixel(px + 2, py + 1, color)
        self.display.set_pixel(px + 1, py + 2, color)
        self.display.set_pixel(px + 2, py + 2, color)

    def draw_bomb(self, bomb):
        """Draw a bomb."""
        px = self.OFFSET_X + bomb['x'] * self.TILE_SIZE
        py = self.OFFSET_Y + bomb['y'] * self.TILE_SIZE

        # Bomb body
        self.display.set_pixel(px + 1, py + 1, self.BOMB_COLOR)
        self.display.set_pixel(px + 2, py + 1, self.BOMB_COLOR)
        self.display.set_pixel(px + 1, py + 2, self.BOMB_COLOR)
        self.display.set_pixel(px + 2, py + 2, self.BOMB_COLOR)

        # Flashing fuse
        if int(bomb['timer'] * 4) % 2 == 0:
            self.display.set_pixel(px + 2, py, self.BOMB_FUSE)

    def draw_enemy(self, enemy):
        """Draw an enemy."""
        px = self.OFFSET_X + enemy['x'] * self.TILE_SIZE
        py = self.OFFSET_Y + enemy['y'] * self.TILE_SIZE

        # Balloon-like enemy
        self.display.set_pixel(px + 1, py, self.ENEMY_COLOR)
        self.display.set_pixel(px + 2, py, self.ENEMY_COLOR)
        self.display.set_pixel(px, py + 1, self.ENEMY_COLOR)
        self.display.set_pixel(px + 1, py + 1, self.ENEMY_COLOR)
        self.display.set_pixel(px + 2, py + 1, self.ENEMY_COLOR)
        self.display.set_pixel(px + 3, py + 1, self.ENEMY_COLOR)
        self.display.set_pixel(px + 1, py + 2, self.ENEMY_COLOR)
        self.display.set_pixel(px + 2, py + 2, self.ENEMY_COLOR)

        # Eyes
        self.display.set_pixel(px + 1, py + 1, Colors.WHITE)
        self.display.set_pixel(px + 2, py + 1, Colors.WHITE)

    def draw_player(self):
        """Draw the player."""
        px = self.OFFSET_X + self.player_x * self.TILE_SIZE
        py = self.OFFSET_Y + self.player_y * self.TILE_SIZE

        # Body (white suit)
        self.display.set_pixel(px + 1, py, self.PLAYER_COLOR)
        self.display.set_pixel(px + 2, py, self.PLAYER_COLOR)
        self.display.set_pixel(px, py + 1, self.PLAYER_COLOR)
        self.display.set_pixel(px + 1, py + 1, self.PLAYER_FACE)
        self.display.set_pixel(px + 2, py + 1, self.PLAYER_FACE)
        self.display.set_pixel(px + 3, py + 1, self.PLAYER_COLOR)
        self.display.set_pixel(px + 1, py + 2, self.PLAYER_COLOR)
        self.display.set_pixel(px + 2, py + 2, self.PLAYER_COLOR)

        # Feet animation
        if self.player_frame == 0:
            self.display.set_pixel(px, py + 3, Colors.BLUE)
            self.display.set_pixel(px + 3, py + 3, Colors.BLUE)
        else:
            self.display.set_pixel(px + 1, py + 3, Colors.BLUE)
            self.display.set_pixel(px + 2, py + 3, Colors.BLUE)

    def draw_hud(self):
        """Draw the heads-up display."""
        # Score
        self.display.draw_text_small(1, 1, f"{self.score}", Colors.WHITE)

        # Level
        self.display.draw_text_small(35, 1, f"L{self.level}", Colors.YELLOW)

        # Bombs available
        bombs_left = self.max_bombs - len(self.active_bombs)
        self.display.draw_text_small(50, 1, f"B{bombs_left}", Colors.CYAN)

        # Lives
        for i in range(self.lives - 1):
            lx = 58 - i * 4
            self.display.set_pixel(lx, 2, self.PLAYER_COLOR)

    def draw_game_over(self):
        """Draw game over screen."""
        self.display.clear(Colors.BLACK)
        self.display.draw_text_small(8, 20, "GAME OVER", Colors.RED)
        self.display.draw_text_small(8, 32, f"SCORE:{self.score}", Colors.WHITE)
        self.display.draw_text_small(12, 42, f"LEVEL:{self.level}", Colors.YELLOW)
        self.display.draw_text_small(4, 54, "SPACE:RETRY", Colors.GRAY)
