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
    name = "GOLD RUNNER"
    description = "Dig & Escape!"
    category = "arcade"
    GUIDE = {
        'desc': 'Collect all gold on each level, then escape to the top. Dig holes to trap guards — they can pick up gold and carry it. Endless procedurally generated levels that get harder as you go.',
    }

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
        self.move_delay = 0.13
        self.fall_timer = 0.0
        self.fall_delay = 0.08  # Seconds per tile of falling (faster than walking)
        self.dig_cooldown = 0
        self.enemy_start_delay = 1.5  # Guards pause before chasing

        self.generate_level()

    def generate_level(self):
        """Generate a structured level with connected floors."""
        # Clear
        self.tiles = [[self.EMPTY] * self.LEVEL_WIDTH for _ in range(self.LEVEL_HEIGHT)]
        self.enemies = []
        self.holes = {}

        # --- Define floor rows ---
        # Bottom floor is SOLID, upper floors are BRICK
        floor_spacing = 5
        floor_rows = []
        y = self.LEVEL_HEIGHT - 1
        while y >= 3:
            floor_rows.append(y)
            y -= floor_spacing
        # floor_rows[0] = ground, rest going upward

        # --- Place platforms on each floor ---
        gap_chance = min(0.12 + self.level * 0.02, 0.25)
        for fi, fy in enumerate(floor_rows):
            tile = self.SOLID if fi == 0 else self.BRICK
            for x in range(self.LEVEL_WIDTH):
                # Leave gaps on non-ground floors for falling through
                if fi > 0 and random.random() < gap_chance:
                    continue
                self.tiles[fy][x] = tile

        # --- Connect adjacent floors with ladders ---
        # Ensure at least 2 ladders between each pair; more at lower levels
        min_ladders = max(2, 4 - self.level // 3)
        max_ladders = min_ladders + 2
        for fi in range(len(floor_rows) - 1):
            lower_y = floor_rows[fi]
            upper_y = floor_rows[fi + 1]
            num_ladders = random.randint(min_ladders, max_ladders)

            # Spread ladders across the width
            segment_w = self.LEVEL_WIDTH // num_ladders
            for li in range(num_ladders):
                seg_start = li * segment_w + 1
                seg_end = min((li + 1) * segment_w - 1, self.LEVEL_WIDTH - 2)
                lx = random.randint(seg_start, max(seg_start, seg_end))

                # Ladder spans from just above the lower floor to the upper floor
                for ly in range(upper_y, lower_y):
                    self.tiles[ly][lx] = self.LADDER
                # Ensure the floor tile under the ladder is solid (not a gap)
                if self.tiles[lower_y][lx] == self.EMPTY:
                    self.tiles[lower_y][lx] = self.BRICK if fi > 0 else self.SOLID

        # --- Place ropes between floors for horizontal traversal ---
        num_ropes = 2 + self.level // 2
        for _ in range(num_ropes):
            # Pick a gap between two floors
            fi = random.randint(0, len(floor_rows) - 2)
            lower_y = floor_rows[fi]
            upper_y = floor_rows[fi + 1]
            # Rope sits 2 rows above the upper floor (midway in the gap)
            ry = upper_y + (lower_y - upper_y) // 2
            rx = random.randint(2, self.LEVEL_WIDTH - 8)
            rw = random.randint(5, 10)
            for x in range(rx, min(rx + rw, self.LEVEL_WIDTH - 1)):
                if self.tiles[ry][x] == self.EMPTY:
                    self.tiles[ry][x] = self.ROPE

        # --- Place gold on reachable surfaces ---
        self.gold_remaining = 4 + self.level
        # Collect valid spots: empty tile with solid/brick/ladder below
        valid_spots = []
        for fy in floor_rows:
            surface_y = fy - 1  # one tile above the floor
            if surface_y < 1:
                continue
            for x in range(1, self.LEVEL_WIDTH - 1):
                if self.tiles[surface_y][x] == self.EMPTY:
                    below = self.tiles[surface_y + 1][x]
                    if below in (self.BRICK, self.SOLID, self.LADDER):
                        valid_spots.append((x, surface_y))

        random.shuffle(valid_spots)
        placed = 0
        for gx, gy in valid_spots:
            if placed >= self.gold_remaining:
                break
            self.tiles[gy][gx] = self.GOLD
            placed += 1
        self.gold_remaining = placed

        # --- Place player on ground floor ---
        self.player_x = 2
        self.player_y = self.LEVEL_HEIGHT - 2
        # Ensure player start area is clear
        self.tiles[self.player_y][self.player_x] = self.EMPTY
        # Ensure ground under player
        self.tiles[self.LEVEL_HEIGHT - 1][self.player_x] = self.SOLID

        # --- Place enemies on reachable surfaces, far from player ---
        # Original: 1 guard on level 1, slow ramp to ~5
        num_enemies = min(1 + (self.level - 1) // 2, 5)
        enemy_spots = []
        for fy in floor_rows:
            surface_y = fy - 1
            if surface_y < 1:
                continue
            for x in range(1, self.LEVEL_WIDTH - 1):
                if self.tiles[surface_y][x] in (self.EMPTY, self.LADDER):
                    below = self.tiles[surface_y + 1][x]
                    if below in (self.BRICK, self.SOLID, self.LADDER):
                        dist = abs(x - self.player_x) + abs(surface_y - self.player_y)
                        if dist > 10:
                            enemy_spots.append((x, surface_y))

        random.shuffle(enemy_spots)
        for i in range(min(num_enemies, len(enemy_spots))):
            ex, ey = enemy_spots[i]
            # Don't place on gold
            if self.tiles[ey][ex] == self.GOLD:
                continue
            self.enemies.append({
                'x': ex, 'y': ey,
                'falling': False, 'trapped': False,
                'trap_timer': 0, 'move_timer': 0,
                'fall_timer': 0.0, 'gold': False,
            })

        # --- Exit ladder at top ---
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
        # Standing on a trapped guard's head
        for enemy in self.enemies:
            if enemy['trapped'] and enemy['x'] == x and enemy['y'] == y + 1:
                return True
        # A dug hole below is no support (checked before the tile, which
        # remains BRICK while the hole is open)
        if (x, y + 1) in self.holes:
            return False
        below = self.tiles[y + 1][x]
        if below in [self.BRICK, self.SOLID, self.LADDER]:
            return True
        return False

    def dig_hole(self, x: int, y: int) -> bool:
        """Dig a hole in a brick. Returns True if successful."""
        if not (0 <= x < self.LEVEL_WIDTH and 0 <= y < self.LEVEL_HEIGHT):
            return False
        if self.tiles[y][x] != self.BRICK or (x, y) in self.holes:
            return False
        # Can't dig under a covered tile (brick/ladder directly above)
        if y > 0 and self.tiles[y - 1][x] in (self.BRICK, self.SOLID, self.LADDER):
            return False
        # Can't dig a tile a guard occupies
        for enemy in self.enemies:
            if enemy['x'] == x and enemy['y'] == y:
                return False
        self.holes[(x, y)] = 10.0  # ~10s like original
        return True

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        self.move_timer += dt

        # Update holes
        for pos in list(self.holes.keys()):
            self.holes[pos] -= dt
            if self.holes[pos] <= 0:
                del self.holes[pos]
                # Crush any enemy still in the hole — respawn at top
                # (before the player check, so a shared hole can't entomb a guard)
                for enemy in self.enemies:
                    if (enemy['x'], enemy['y']) == pos:
                        enemy['trapped'] = False
                        enemy['fall_timer'] = 0.0
                        enemy['y'] = 0
                        enemy['x'] = random.randint(1, self.LEVEL_WIDTH - 2)
                # A refilling hole kills the player caught inside it
                if (self.player_x, self.player_y) == pos:
                    self.player_hit()
                    return

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

        if (input_state.action_l or input_state.action_r) and self.dig_cooldown <= 0:
            # Dig in the direction player is facing
            dig_x = self.player_x + self.player_facing
            if self.dig_hole(dig_x, self.player_y + 1):
                self.dig_cooldown = 0.3  # Cooldown after successful dig

        # Apply gravity to player (timed — one tile per fall_delay seconds)
        if (not self.is_supported(self.player_x, self.player_y) and
                self.tiles[self.player_y][self.player_x] != self.ROPE):
            self.fall_timer += dt
            if self.fall_timer >= self.fall_delay:
                self.fall_timer = 0.0
                self.player_y += 1
        else:
            self.fall_timer = 0.0

        # Collect gold
        if self.tiles[self.player_y][self.player_x] == self.GOLD:
            self.tiles[self.player_y][self.player_x] = self.EMPTY
            self.gold_remaining -= 1
            self.score += 250

            # Open exit when all gold collected
            if self.gold_remaining <= 0:
                self.exit_open = True
                # Add exit ladder
                for y in range(self.LEVEL_HEIGHT):
                    self.tiles[y][self.exit_x] = self.LADDER

        # Check win condition
        if self.exit_open and self.player_y <= 1:
            self.next_level()

        # Guards pause briefly at level start before chasing
        if self.enemy_start_delay > 0:
            self.enemy_start_delay -= dt
        else:
            self.update_enemies(dt)

        # Check enemy collision
        for enemy in self.enemies:
            if not enemy['trapped']:
                if enemy['x'] == self.player_x and enemy['y'] == self.player_y:
                    self.player_hit()
                    break

    def update_enemies(self, dt: float):
        """Update guard AI."""
        for enemy in self.enemies:
            enemy['move_timer'] += dt

            # Check if in hole
            if not enemy['trapped'] and (enemy['x'], enemy['y']) in self.holes:
                enemy['trapped'] = True
                enemy['trap_timer'] = 5.0  # ~5s like original
                # A trapped guard always drops its gold above the hole
                if enemy['gold']:
                    gy = enemy['y'] - 1
                    if gy >= 0 and self.tiles[gy][enemy['x']] == self.EMPTY:
                        enemy['gold'] = False
                        self.tiles[gy][enemy['x']] = self.GOLD

            if enemy['trapped']:
                enemy['trap_timer'] -= dt
                if enemy['trap_timer'] <= 0:
                    # Climb out only if the space above is clear
                    ax, ay = enemy['x'], enemy['y'] - 1
                    blocked = (ay < 0 or self.is_solid(ax, ay) or
                               (self.player_x, self.player_y) == (ax, ay) or
                               any(o is not enemy and (o['x'], o['y']) == (ax, ay)
                                   for o in self.enemies))
                    if blocked:
                        enemy['trap_timer'] = 0.5  # retry shortly
                    else:
                        enemy['trapped'] = False
                        enemy['y'] -= 1
                continue

            # Apply gravity (timed — one tile per fall_delay seconds)
            if (not self.is_supported(enemy['x'], enemy['y']) and
                    self.tiles[enemy['y']][enemy['x']] != self.ROPE):
                enemy['fall_timer'] += dt
                if enemy['fall_timer'] >= self.fall_delay:
                    enemy['fall_timer'] = 0.0
                    enemy['y'] += 1
                continue
            enemy['fall_timer'] = 0.0

            # Guards move on a slower schedule than the player
            enemy_speed = max(0.18, 0.28 - self.level * 0.01)
            if enemy['move_timer'] >= enemy_speed:
                enemy['move_timer'] = 0

                dx, dy = self.guard_pick_move(enemy)
                nx, ny = enemy['x'] + dx, enemy['y'] + dy

                # Two guards never occupy the same cell
                if (dx or dy) and not any(
                        o is not enemy and (o['x'], o['y']) == (nx, ny)
                        for o in self.enemies):
                    old_x, old_y = enemy['x'], enemy['y']
                    enemy['x'], enemy['y'] = nx, ny

                    # Gold: pick up when walking onto it (carry at most one)
                    if self.tiles[ny][nx] == self.GOLD and not enemy['gold']:
                        enemy['gold'] = True
                        self.tiles[ny][nx] = self.EMPTY
                    # Small chance to drop carried gold on the cell just left
                    elif (enemy['gold'] and
                          self.tiles[old_y][old_x] == self.EMPTY and
                          random.random() < 0.05):
                        enemy['gold'] = False
                        self.tiles[old_y][old_x] = self.GOLD

    def guard_pick_move(self, enemy):
        """Original-style guard AI (reimplemented scan).

        Same row as the runner: run straight at him. Otherwise scan the
        columns reachable by walking along the current row and score every
        ladder-up / ladder-down / fall-through exit by how close its
        destination row gets to the runner's row; commit to the best.
        Returns a (dx, dy) step.
        """
        ex, ey = enemy['x'], enemy['y']
        px, py = self.player_x, self.player_y

        # Same row: run straight at the runner
        if ey == py and ex != px:
            step = 1 if px > ex else -1
            if not self.is_solid(ex + step, ey):
                return step, 0

        # Scan reachable columns along this row (stop at walls; a gap is
        # walkable into but not past — it's a fall-through exit)
        best = None  # (row_dist, col_dist, dx, dy)

        def consider(row_dist, col_dist, dx, dy):
            nonlocal best
            cand = (row_dist, col_dist, dx, dy)
            if best is None or cand[:2] < best[:2]:
                best = cand

        for direction in (0, -1, 1):
            cx = ex
            while True:
                if direction == 0:
                    pass  # evaluate the current column once
                else:
                    cx += direction
                    if self.is_solid(cx, ey):
                        break
                first_dx = 0 if cx == ex else (1 if cx > ex else -1)
                col_dist = abs(cx - ex)

                # Ladder-up exit
                if py < ey and self.tiles[ey][cx] == self.LADDER:
                    dest = self.climb_dest_row(cx, ey)
                    if dest < ey:
                        consider(abs(dest - py), col_dist,
                                 first_dx if first_dx else 0,
                                 -1 if cx == ex else 0)

                # Ladder-down / fall-through exit
                if py > ey:
                    dest = self.descend_dest_row(cx, ey)
                    if dest > ey:
                        consider(abs(dest - py), col_dist,
                                 first_dx if first_dx else 0,
                                 1 if cx == ex else 0)

                if direction == 0:
                    break
                # Can't walk past an unsupported column — the guard drops there
                if not self.is_supported(cx, ey):
                    break

        if best is not None:
            _, _, dx, dy = best
            # Vertical steps must be into open space
            if dy == -1 and self.is_solid(ex, ey - 1):
                return 0, 0
            if dy == 1 and self.is_solid(ex, ey + 1):
                return 0, 0
            return dx, dy

        # No useful exit: shuffle toward the runner if the way is open
        if px != ex:
            step = 1 if px > ex else -1
            if not self.is_solid(ex + step, ey):
                return step, 0
        return 0, 0

    def climb_dest_row(self, x, y):
        """Row reached by climbing the ladder at (x, y) upward."""
        ty = y
        while (ty > 0 and self.tiles[ty][x] == self.LADDER and
                not self.is_solid(x, ty - 1)):
            ty -= 1
            if ty <= self.player_y:
                break
        return ty

    def descend_dest_row(self, x, y):
        """Row reached by climbing down / falling / dropping from (x, y)."""
        ty = y
        while (ty < self.LEVEL_HEIGHT - 1 and ty < self.player_y and
                not self.is_solid(x, ty + 1)):
            ty += 1
            if self.tiles[ty][x] == self.ROPE:
                break  # falling guards grab ropes
        return ty

    def player_hit(self):
        """Handle player death."""
        self.lives -= 1
        if self.lives <= 0:
            self.state = GameState.GAME_OVER
        else:
            self.player_x = 2
            self.player_y = self.LEVEL_HEIGHT - 2
            self.fall_timer = 0.0
            self.enemy_start_delay = 1.5  # Brief reprieve on respawn
            # Reset enemies
            for enemy in self.enemies:
                enemy['trapped'] = False

    def next_level(self):
        """Advance to next level."""
        self.level += 1
        self.score += 500
        self.enemy_start_delay = 1.5
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

        # Show carried gold as a glint on the guard
        if enemy['gold']:
            self.display.set_pixel(px + 1, py, self.GOLD_COLOR)

    def draw_game_over(self):
        self.display.clear(Colors.BLACK)
        self.display.draw_text_small(8, 20, "GAME OVER", Colors.RED)
        self.display.draw_text_small(10, 32, f"SCORE:{self.score}", Colors.WHITE)
        self.display.draw_text_small(4, 50, "BTN:RETRY", Colors.GRAY)
