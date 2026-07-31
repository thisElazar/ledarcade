"""
Q*bert - Isometric Cube Hopping
===============================
Hop on cubes to change their colors. Avoid enemies!

Controls:
  Arrow Keys - Hop diagonally (Up=up-right, Right=down-right, Down=down-left, Left=up-left)
  Space      - Not used (movement only)
"""

import random
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


class QBert(Game):
    name = "Q*BIT"
    description = "Hop & Color!"
    category = "arcade"
    GUIDE = {
        'desc': 'Hop on cubes in an isometric pyramid to change their colors — later levels need two hops per cube or revert when you re-hop. Avoid Coily the snake and the red balls; catch the green ball to freeze everyone. Hop onto a spinning disc to lure a close Coily off the edge.',
    }

    # Pyramid dimensions
    PYRAMID_ROWS = 7  # 7 rows = 28 cubes total

    # Isometric cube dimensions
    CUBE_WIDTH = 8
    CUBE_HEIGHT = 6
    CUBE_TOP_HEIGHT = 3

    # Colors
    CUBE_START_COLOR = (50, 50, 200)      # Blue - starting color
    CUBE_TARGET_COLOR = (255, 200, 0)     # Yellow/gold - target color
    CUBE_SIDE_LEFT = (30, 30, 150)        # Darker blue for left side
    CUBE_SIDE_RIGHT = (40, 40, 180)       # Medium blue for right side
    CUBE_TARGET_LEFT = (200, 150, 0)      # Darker gold
    CUBE_TARGET_RIGHT = (230, 180, 0)     # Medium gold
    CUBE_MID_COLOR = (255, 120, 180)      # Pink - intermediate (2-hop levels)
    CUBE_MID_LEFT = (190, 80, 130)
    CUBE_MID_RIGHT = (220, 100, 155)

    QBERT_COLOR = (255, 128, 0)           # Orange
    QBERT_NOSE = (255, 80, 80)            # Red-pink nose
    COILY_COLOR = (128, 0, 128)           # Purple snake
    SLICK_COLOR = (0, 200, 0)             # Green
    SAM_COLOR = (0, 200, 200)             # Cyan

    DISC_COLOR = (255, 0, 255)            # Magenta spinning discs

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0
        self.lives = 3
        self.level = 1

        # Pyramid origin (top-left of the top cube)
        self.pyramid_x = 28
        self.pyramid_y = 8

        # Cube states: 0 = start color, 1 = target color
        # Indexed as cubes[row][col] where row 0 is top
        self.cubes = [[0] * (row + 1) for row in range(self.PYRAMID_ROWS)]

        # Q*bert position (row, col)
        self.qbert_row = 0
        self.qbert_col = 0

        # Movement
        self.hop_timer = 0.0
        self.hop_cooldown = 0.25
        self.is_hopping = False
        self.hop_progress = 0.0
        self.hop_from = (0, 0)
        self.hop_to = (0, 0)

        # Enemies
        self.enemies = []
        self.enemy_spawn_timer = 0.0
        self.enemy_spawn_rate = 3.0

        # Spinning discs (escape platforms)
        self.discs = [
            {'row': 2, 'side': 'left', 'active': True},
            {'row': 4, 'side': 'right', 'active': True},
        ]
        self.on_disc = False
        self.disc_ride_timer = 0.0

        # Animation
        self.qbert_frame = 0
        self.anim_timer = 0.0

        # Green-ball freeze and death (swear-bubble) pause
        self.freeze_timer = 0.0
        self.swear_timer = 0.0

        # Check if level complete
        self.level_complete = False
        self.level_transition_timer = 0.0

    def get_cube_screen_pos(self, row, col):
        """Get the screen position for a cube at (row, col)."""
        # Isometric positioning
        x = self.pyramid_x + (col - row / 2) * self.CUBE_WIDTH
        y = self.pyramid_y + row * (self.CUBE_HEIGHT - 1)
        return int(x), int(y)

    def get_qbert_screen_pos(self):
        """Get Q*bert's screen position, accounting for hopping animation."""
        if self.is_hopping:
            # Interpolate between positions
            x1, y1 = self.get_cube_screen_pos(*self.hop_from)
            x2, y2 = self.get_cube_screen_pos(*self.hop_to)

            # Add arc for jump
            t = self.hop_progress
            x = x1 + (x2 - x1) * t
            y = y1 + (y2 - y1) * t

            # Parabolic arc (highest at t=0.5)
            arc_height = 8
            y -= arc_height * 4 * t * (1 - t)

            return int(x), int(y)
        else:
            return self.get_cube_screen_pos(self.qbert_row, self.qbert_col)

    def is_valid_cube(self, row, col):
        """Check if (row, col) is a valid cube position."""
        if row < 0 or row >= self.PYRAMID_ROWS:
            return False
        if col < 0 or col > row:
            return False
        return True

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        # Level transition
        if self.level_complete:
            self.level_transition_timer -= dt
            if self.level_transition_timer <= 0:
                self.next_level()
            return

        # Death pause: swear bubble, then resolve
        if self.swear_timer > 0:
            self.swear_timer -= dt
            if self.swear_timer <= 0:
                self.resolve_death()
            return

        # Disc ride animation
        if self.on_disc:
            self.disc_ride_timer -= dt
            if self.disc_ride_timer <= 0:
                self.on_disc = False
                self.qbert_row = 0
                self.qbert_col = 0
                # Enemies persist — only a lured Coily is gone
            return

        # Animation timer
        self.anim_timer += dt
        if self.anim_timer > 0.2:
            self.anim_timer = 0
            self.qbert_frame = (self.qbert_frame + 1) % 2

        # Hop cooldown
        if self.hop_timer > 0:
            self.hop_timer -= dt

        # Handle hopping animation
        if self.is_hopping:
            self.hop_progress += dt / 0.15  # 0.15 seconds per hop
            if self.hop_progress >= 1.0:
                self.is_hopping = False
                self.qbert_row, self.qbert_col = self.hop_to

                # Check if landed on valid cube
                if self.is_valid_cube(self.qbert_row, self.qbert_col):
                    # Advance cube color per this level's rules
                    mode = self.cube_mode()
                    cube = self.cubes[self.qbert_row][self.qbert_col]
                    if mode == 2:
                        # Re-hopping a finished cube reverts it
                        self.cubes[self.qbert_row][self.qbert_col] = 1 - cube
                        if cube == 0:
                            self.score += 25
                    elif cube < self.cube_target():
                        self.cubes[self.qbert_row][self.qbert_col] = cube + 1
                        self.score += 25

                    # Check level complete
                    if self.check_level_complete():
                        self.level_complete = True
                        self.level_transition_timer = 1.5
                        self.score += 1000 + 250 * (self.level - 1)
                else:
                    # Fell off pyramid - check for disc
                    disc = self.check_disc_collision()
                    if disc:
                        self.on_disc = True
                        self.disc_ride_timer = 1.0
                        disc['active'] = False
                        self.score += 50
                        self.lure_coily()
                    else:
                        self.player_die()
                        return
        else:
            # Handle input for hopping
            if self.hop_timer <= 0:
                new_row, new_col = self.qbert_row, self.qbert_col
                moved = False

                # Diagonal movement based on arrow combinations
                if input_state.up and input_state.left:
                    # Hop up-left (go to previous row, same relative col)
                    new_row = self.qbert_row - 1
                    new_col = self.qbert_col - 1
                    moved = True
                elif input_state.up and input_state.right:
                    # Hop up-right
                    new_row = self.qbert_row - 1
                    new_col = self.qbert_col
                    moved = True
                elif input_state.down and input_state.left:
                    # Hop down-left
                    new_row = self.qbert_row + 1
                    new_col = self.qbert_col
                    moved = True
                elif input_state.down and input_state.right:
                    # Hop down-right
                    new_row = self.qbert_row + 1
                    new_col = self.qbert_col + 1
                    moved = True
                # Single directions map to a consistent 45-degree rotation:
                # up=up-right, right=down-right, down=down-left, left=up-left
                elif input_state.up:
                    new_row = self.qbert_row - 1
                    new_col = self.qbert_col
                    moved = True
                elif input_state.right:
                    new_row = self.qbert_row + 1
                    new_col = self.qbert_col + 1
                    moved = True
                elif input_state.down:
                    new_row = self.qbert_row + 1
                    new_col = self.qbert_col
                    moved = True
                elif input_state.left:
                    new_row = self.qbert_row - 1
                    new_col = self.qbert_col - 1
                    moved = True

                if moved:
                    self.is_hopping = True
                    self.hop_progress = 0.0
                    self.hop_from = (self.qbert_row, self.qbert_col)
                    self.hop_to = (new_row, new_col)
                    self.hop_timer = self.hop_cooldown

        # Update enemies
        self.update_enemies(dt)

        # Check enemy collisions
        self.check_enemy_collisions()

        # Spawn enemies
        self.enemy_spawn_timer += dt
        if self.enemy_spawn_timer >= self.enemy_spawn_rate:
            self.enemy_spawn_timer = 0
            self.spawn_enemy()

    def cube_mode(self):
        """Per-level cube rules, cycling with level:
        0 = one hop, permanent; 1 = two hops via intermediate color;
        2 = one hop, but re-hopping reverts."""
        return (self.level - 1) % 3

    def cube_target(self):
        """Cube state that counts as finished for the current mode."""
        return 2 if self.cube_mode() == 1 else 1

    def check_level_complete(self):
        """Check if all cubes are the target color."""
        target = self.cube_target()
        for row in self.cubes:
            for cube in row:
                if cube != target:
                    return False
        return True

    def lure_coily(self):
        """A hatched Coily close to the edge follows Q*bert off it."""
        for enemy in self.enemies:
            if (enemy['type'] == 'coily' and not enemy.get('is_egg')
                    and not enemy.get('falling_off')):
                dist = (abs(enemy['row'] - self.qbert_row) +
                        abs(enemy['col'] - self.qbert_col))
                if dist <= 2:
                    x, y = self.get_cube_screen_pos(enemy['row'], enemy['col'])
                    enemy['falling_off'] = True
                    enemy['fall_x'] = x
                    enemy['fall_y'] = float(y)
                    self.score += 500
                    return

    def check_disc_collision(self):
        """Check if Q*bert landed on a spinning disc."""
        for disc in self.discs:
            if not disc['active']:
                continue

            disc_row = disc['row']
            if disc['side'] == 'left':
                # Left disc is at col -1
                if self.qbert_row == disc_row and self.qbert_col == -1:
                    return disc
            else:
                # Right disc is at col = row + 1
                if self.qbert_row == disc_row and self.qbert_col == disc_row + 1:
                    return disc
        return None

    def spawn_enemy(self):
        """Spawn a new enemy at the top of the pyramid (one Coily max)."""
        choices = ['slick', 'sam', 'red_ball', 'red_ball']
        if not any(e['type'] == 'coily' for e in self.enemies):
            choices += ['coily', 'coily', 'coily']

        if random.random() < 0.08:
            enemy_type = 'green_ball'  # Rare: freezes enemies on touch
        else:
            enemy_type = random.choice(choices)

        if enemy_type == 'coily':
            # Coily starts as an egg at top
            self.enemies.append({
                'type': 'coily',
                'row': 0,
                'col': 0,
                'is_egg': True,
                'move_timer': 0.0,
            })
        else:
            # Balls/slick/sam drop in on row 1, never on Q*bert's respawn
            # cube at the apex (like the real game)
            self.enemies.append({
                'type': enemy_type,
                'row': 1,
                'col': random.randint(0, 1),
                'move_timer': 0.0,
            })

    def update_enemies(self, dt: float):
        """Update enemy movement."""
        enemies_to_remove = []

        frozen = self.freeze_timer > 0
        if frozen:
            self.freeze_timer -= dt

        for enemy in self.enemies:
            # A lured Coily falls off the pyramid
            if enemy.get('falling_off'):
                enemy['fall_y'] += 50 * dt
                if enemy['fall_y'] > GRID_SIZE:
                    enemies_to_remove.append(enemy)
                continue

            if frozen:
                continue

            enemy['move_timer'] += dt

            move_rate = 0.6 if enemy['type'] == 'coily' and not enemy.get('is_egg') else 0.8

            if enemy['move_timer'] >= move_rate:
                enemy['move_timer'] = 0

                if enemy['type'] == 'coily':
                    if enemy.get('is_egg'):
                        # Egg falls down randomly
                        if enemy['row'] < self.PYRAMID_ROWS - 1:
                            enemy['row'] += 1
                            if random.random() < 0.5:
                                enemy['col'] += 1
                        else:
                            # Hatch into snake
                            enemy['is_egg'] = False
                    else:
                        # Snake chases Q*bert
                        dr = 1 if self.qbert_row > enemy['row'] else -1
                        dc = 1 if self.qbert_col > enemy['col'] else 0

                        new_row = enemy['row'] + dr
                        new_col = enemy['col'] + (1 if dr > 0 and dc > 0 else 0)

                        if dr < 0:
                            # Going up
                            new_col = enemy['col'] + (-1 if self.qbert_col < enemy['col'] else 0)

                        if self.is_valid_cube(new_row, new_col):
                            enemy['row'] = new_row
                            enemy['col'] = new_col
                        elif enemy['row'] >= self.PYRAMID_ROWS - 1:
                            # Coily falls off if at bottom
                            enemies_to_remove.append(enemy)
                elif enemy['type'] in ('red_ball', 'green_ball'):
                    # Balls bounce down the pyramid and roll off the bottom
                    if enemy['row'] < self.PYRAMID_ROWS - 1:
                        enemy['row'] += 1
                        if random.random() < 0.5:
                            enemy['col'] += 1
                    else:
                        enemies_to_remove.append(enemy)
                else:
                    # Slick and Sam move down and undo cube colors
                    if enemy['row'] < self.PYRAMID_ROWS - 1:
                        enemy['row'] += 1
                        if random.random() < 0.5:
                            enemy['col'] += 1

                        # Undo cube color one step
                        if self.is_valid_cube(enemy['row'], enemy['col']):
                            if self.cubes[enemy['row']][enemy['col']] > 0:
                                self.cubes[enemy['row']][enemy['col']] -= 1
                    else:
                        enemies_to_remove.append(enemy)

        for enemy in enemies_to_remove:
            self.enemies.remove(enemy)

    def check_enemy_collisions(self):
        """Check if Q*bert collides with any enemy."""
        if self.is_hopping or self.on_disc:
            return

        for enemy in self.enemies:
            if enemy.get('falling_off'):
                continue
            if enemy['row'] == self.qbert_row and enemy['col'] == self.qbert_col:
                if enemy['type'] in ['slick', 'sam']:
                    # Catching Slick/Sam gives points
                    self.enemies.remove(enemy)
                    self.score += 300
                elif enemy['type'] == 'green_ball':
                    # Green ball: points + freeze all enemies
                    self.enemies.remove(enemy)
                    self.score += 100
                    self.freeze_timer = 3.5
                elif self.freeze_timer <= 0:
                    # Coily or red ball kills Q*bert (unless frozen)
                    self.player_die()
                    return

    def player_die(self):
        """Q*bert swears; the death resolves after a short pause."""
        self.swear_timer = 0.8

    def resolve_death(self):
        """Apply the death after the swear-bubble pause."""
        self.lives -= 1
        if self.lives <= 0:
            self.state = GameState.GAME_OVER
        else:
            # Reset position but keep cube states
            self.qbert_row = 0
            self.qbert_col = 0
            self.is_hopping = False
            self.enemies.clear()
            self.enemy_spawn_timer = 0
            # Used discs do NOT come back — they respawn only on a new level

    def next_level(self):
        """Advance to next level."""
        self.level += 1
        self.level_complete = False

        # Reset cubes
        self.cubes = [[0] * (row + 1) for row in range(self.PYRAMID_ROWS)]

        # Reset Q*bert position
        self.qbert_row = 0
        self.qbert_col = 0
        self.is_hopping = False

        # Clear enemies
        self.enemies.clear()
        self.enemy_spawn_timer = 0
        self.freeze_timer = 0.0

        # Restore discs (new level only)
        for disc in self.discs:
            disc['active'] = True

        # Increase difficulty
        self.enemy_spawn_rate = max(1.5, 3.0 - self.level * 0.3)

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Draw spinning discs
        for disc in self.discs:
            if disc['active']:
                self.draw_disc(disc)

        # Draw pyramid (back to front for proper overlap)
        for row in range(self.PYRAMID_ROWS):
            for col in range(row + 1):
                self.draw_cube(row, col)

        # Draw enemies
        for enemy in self.enemies:
            self.draw_enemy(enemy)

        # Draw Q*bert
        if not self.on_disc:
            self.draw_qbert()
        else:
            # Draw Q*bert riding disc to top
            self.draw_qbert_on_disc()

        # Swear bubble beside Q*bert during the death pause
        if self.swear_timer > 0:
            qx, qy = self.get_qbert_screen_pos()
            bx = min(max(qx + 6, 2), 44)
            by = max(qy - 8, 8)
            self.display.draw_text_small(bx, by, "@!#?", Colors.WHITE)

        # Draw HUD
        self.draw_hud()

    def draw_cube(self, row, col):
        """Draw an isometric cube."""
        x, y = self.get_cube_screen_pos(row, col)

        # Determine colors based on cube state
        state = self.cubes[row][col]
        if state == 0:
            top_color = self.CUBE_START_COLOR
            left_color = self.CUBE_SIDE_LEFT
            right_color = self.CUBE_SIDE_RIGHT
        elif state < self.cube_target():
            # Intermediate color on 2-hop levels
            top_color = self.CUBE_MID_COLOR
            left_color = self.CUBE_MID_LEFT
            right_color = self.CUBE_MID_RIGHT
        else:
            top_color = self.CUBE_TARGET_COLOR
            left_color = self.CUBE_TARGET_LEFT
            right_color = self.CUBE_TARGET_RIGHT

        # Draw cube top (diamond shape)
        cx = x + self.CUBE_WIDTH // 2
        for dy in range(self.CUBE_TOP_HEIGHT):
            width = dy + 1 if dy < self.CUBE_TOP_HEIGHT // 2 + 1 else self.CUBE_TOP_HEIGHT - dy
            width = min(self.CUBE_WIDTH // 2, dy + 1)
            for dx in range(-width, width + 1):
                self.display.set_pixel(cx + dx, y + dy, top_color)

        # Draw left face
        for dy in range(self.CUBE_HEIGHT - self.CUBE_TOP_HEIGHT):
            py = y + self.CUBE_TOP_HEIGHT + dy
            for dx in range(self.CUBE_WIDTH // 2):
                px = x + dx
                self.display.set_pixel(px, py, left_color)

        # Draw right face
        for dy in range(self.CUBE_HEIGHT - self.CUBE_TOP_HEIGHT):
            py = y + self.CUBE_TOP_HEIGHT + dy
            for dx in range(self.CUBE_WIDTH // 2):
                px = x + self.CUBE_WIDTH // 2 + dx
                self.display.set_pixel(px, py, right_color)

    def draw_disc(self, disc):
        """Draw a spinning disc."""
        row = disc['row']
        if disc['side'] == 'left':
            x, y = self.get_cube_screen_pos(row, -1)
            x -= 2
        else:
            x, y = self.get_cube_screen_pos(row, row + 1)
            x += 4

        # Spinning animation
        frame = int(self.anim_timer * 10) % 4

        # Draw small disc
        for dx in range(-2, 3):
            for dy in range(-1, 2):
                if abs(dx) + abs(dy) <= 2:
                    self.display.set_pixel(x + dx, y + dy, self.DISC_COLOR)

    def draw_qbert(self):
        """Draw Q*bert."""
        x, y = self.get_qbert_screen_pos()

        # Offset to center on cube top
        x += self.CUBE_WIDTH // 2 - 2
        y -= 2

        # Body (4x4 orange blob)
        for dy in range(4):
            for dx in range(4):
                if dy == 0 and (dx == 0 or dx == 3):
                    continue  # Round corners
                if dy == 3 and (dx == 0 or dx == 3):
                    continue
                self.display.set_pixel(x + dx, y + dy, self.QBERT_COLOR)

        # Eyes
        self.display.set_pixel(x + 1, y + 1, Colors.WHITE)
        self.display.set_pixel(x + 2, y + 1, Colors.WHITE)

        # Nose (sticks out)
        nose_x = x + 4 if self.qbert_frame == 0 else x - 1
        self.display.set_pixel(nose_x, y + 2, self.QBERT_NOSE)

    def draw_qbert_on_disc(self):
        """Draw Q*bert riding disc back to top."""
        # Animate from disc position to top
        progress = 1.0 - (self.disc_ride_timer / 1.0)
        y = int(40 - progress * 35)
        x = 30

        # Simple Q*bert
        for dy in range(3):
            for dx in range(3):
                self.display.set_pixel(x + dx, y + dy, self.QBERT_COLOR)

    def draw_enemy(self, enemy):
        """Draw an enemy."""
        if enemy.get('falling_off'):
            # Lured Coily plummeting off the pyramid
            x = int(enemy['fall_x']) + self.CUBE_WIDTH // 2 - 1
            y = int(enemy['fall_y'])
        else:
            x, y = self.get_cube_screen_pos(enemy['row'], enemy['col'])
            x += self.CUBE_WIDTH // 2 - 1
            y -= 1

        if enemy['type'] == 'red_ball':
            self.display.set_pixel(x, y, Colors.RED)
            self.display.set_pixel(x + 1, y, Colors.RED)
            self.display.set_pixel(x, y + 1, (180, 0, 0))
            self.display.set_pixel(x + 1, y + 1, (180, 0, 0))
            return
        if enemy['type'] == 'green_ball':
            self.display.set_pixel(x, y, Colors.GREEN)
            self.display.set_pixel(x + 1, y, Colors.GREEN)
            self.display.set_pixel(x, y + 1, (0, 140, 0))
            self.display.set_pixel(x + 1, y + 1, (0, 140, 0))
            return

        if enemy['type'] == 'coily':
            if enemy.get('is_egg'):
                # Draw egg (purple ball)
                self.display.set_pixel(x, y, self.COILY_COLOR)
                self.display.set_pixel(x + 1, y, self.COILY_COLOR)
                self.display.set_pixel(x, y + 1, self.COILY_COLOR)
                self.display.set_pixel(x + 1, y + 1, self.COILY_COLOR)
            else:
                # Draw snake
                for dy in range(4):
                    self.display.set_pixel(x, y + dy, self.COILY_COLOR)
                    if dy < 2:
                        self.display.set_pixel(x + 1, y + dy, self.COILY_COLOR)
                # Eyes
                self.display.set_pixel(x, y, Colors.WHITE)
        elif enemy['type'] == 'slick':
            # Green creature
            for dy in range(3):
                for dx in range(2):
                    self.display.set_pixel(x + dx, y + dy, self.SLICK_COLOR)
        else:  # sam
            # Cyan creature
            for dy in range(3):
                for dx in range(2):
                    self.display.set_pixel(x + dx, y + dy, self.SAM_COLOR)

    def draw_hud(self):
        """Draw the heads-up display."""
        # Score
        self.display.draw_text_small(1, 1, f"{self.score}", Colors.WHITE)

        # Level
        self.display.draw_text_small(45, 1, f"L{self.level}", Colors.YELLOW)

        # Lives
        for i in range(self.lives - 1):
            lx = 56 - i * 4
            self.display.set_pixel(lx, 2, self.QBERT_COLOR)
            self.display.set_pixel(lx + 1, 2, self.QBERT_COLOR)

    def draw_game_over(self):
        """Draw game over screen."""
        self.display.clear(Colors.BLACK)
        self.display.draw_text_small(8, 20, "GAME OVER", Colors.RED)
        self.display.draw_text_small(8, 32, f"SCORE:{self.score}", Colors.WHITE)
        self.display.draw_text_small(12, 42, f"LEVEL:{self.level}", Colors.YELLOW)
        self.display.draw_text_small(4, 54, "BTN:RETRY", Colors.GRAY)
