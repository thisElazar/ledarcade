"""
JezzBall - Trap the bouncing atoms
==================================
Build walls to divide the play area. Trap atoms in smaller areas.
Complete the level when 75%+ of the area is filled.

Based on the original Microsoft Entertainment Pack game by Dima Pavlovsky (1992).

Mechanics:
  - Press Space to shoot two wall rays in opposite directions
  - Rays extend until they hit an existing wall
  - If an atom hits a ray, that ray is destroyed and you lose 1 life
  - If an atom hits the source point (center), BOTH rays die and you lose 2 lives
  - Rays are independent: one can complete while the other is destroyed
  - Areas without atoms are automatically filled when walls complete
  - You start each level with lives equal to the number of atoms

Difficulty:
  - You have a 5-second SHIELD at the start of each level (cyan forcefield)
  - After the shield expires, atoms hitting your cursor cost 1 life!
  - Taking damage gives you 1 second of invincibility to escape
  - Lives persist between levels - be careful!
  - Bonus life at level 3, then every 2 levels (3, 5, 7, 9...) max 10

Controls:
  Arrow Keys - Move cursor and set wall direction
  Space      - Build wall in current direction
  Escape     - Return to menu
"""

import random
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


class Wall:
    """A single wall ray that extends in one direction."""

    def __init__(self, start_x: int, start_y: int, dx: int, dy: int):
        self.start_x = start_x
        self.start_y = start_y
        self.dx = dx  # Direction: -1, 0, or 1
        self.dy = dy
        self.length = 0  # Current length (not counting start)
        self.finished = False
        self.dead = False
        self.speed = 80  # Pixels per second
        self.progress = 0.0  # Sub-pixel progress

    def get_tip_position(self) -> tuple:
        """Get the current tip position of the wall."""
        return (
            self.start_x + self.dx * self.length,
            self.start_y + self.dy * self.length
        )

    def get_all_positions(self) -> list:
        """Get all positions this wall occupies (excluding start if length > 0)."""
        positions = []
        for i in range(1, self.length + 1):
            positions.append((
                self.start_x + self.dx * i,
                self.start_y + self.dy * i
            ))
        return positions


class JezzBall(Game):
    name = "JEZZBALL"
    description = "Trap the bouncing atoms!"
    category = "retro"

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0
        self.level = 1
        self.lives = 2  # Start with lives = atoms (level 1 has 2 atoms)

        # Play area (leaving room for HUD at top)
        self.play_top = 10
        self.play_left = 2
        self.play_right = 61
        self.play_bottom = 61

        # Grid to track filled areas (True = wall/filled)
        self.width = self.play_right - self.play_left
        self.height = self.play_bottom - self.play_top
        self.grid = [[False for _ in range(self.width)] for _ in range(self.height)]

        # Draw border as filled
        for x in range(self.width):
            self.grid[0][x] = True
            self.grid[self.height - 1][x] = True
        for y in range(self.height):
            self.grid[y][0] = True
            self.grid[y][self.width - 1] = True

        # Atoms (bouncing balls)
        self.atoms = []
        self.spawn_atoms(self.level + 1)

        # Cursor position (in grid coordinates)
        self.cursor_x = self.width // 2
        self.cursor_y = self.height // 2
        self.cursor_blink = 0.0

        # Wall building direction (True = horizontal, False = vertical)
        self.horizontal = True

        # Active walls being built (two rays extending in opposite directions)
        self.walls = []  # List of Wall objects

        # Movement timing
        self.cursor_delay = 0.06
        self.cursor_timer = 0
        self.move_held_time = 0.0

        # Shield timer - invincible for first 5 seconds of each level
        self.level_time = 0.0
        self.shield_duration = 5.0
        self.shield_hit_flash = 0.0  # Flash when hit while shielded
        self.bonus_life_flash = 0.0  # Flash when gaining a bonus life

        # Fill percentage
        self.fill_percent = 0
        self.update_fill_percent()

    def spawn_atoms(self, count: int):
        """Spawn atoms in the play area."""
        self.atoms = []
        colors = [Colors.RED, Colors.CYAN, Colors.YELLOW, Colors.MAGENTA, Colors.ORANGE]

        for i in range(count):
            # Find a valid spawn position (away from edges)
            attempts = 0
            while attempts < 100:
                x = random.randint(8, self.width - 10)
                y = random.randint(8, self.height - 10)
                if not self.grid[y][x]:
                    break
                attempts += 1

            # Random direction with consistent speed
            speed = random.uniform(28, 38)
            angle = random.uniform(0.3, 1.2)  # Avoid pure horizontal/vertical
            if random.random() < 0.5:
                angle = -angle

            import math
            dx = speed * math.cos(angle) * random.choice([-1, 1])
            dy = speed * math.sin(angle) * random.choice([-1, 1])

            self.atoms.append({
                'x': float(x),
                'y': float(y),
                'dx': dx,
                'dy': dy,
                'color': colors[i % len(colors)]
            })

    def update_fill_percent(self):
        """Calculate the percentage of area filled."""
        total = 0
        filled = 0
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                total += 1
                if self.grid[y][x]:
                    filled += 1
        self.fill_percent = int((filled / total) * 100) if total > 0 else 0

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        # Update timers
        self.cursor_blink += dt
        self.level_time += dt

        # Decay flash effects
        if self.shield_hit_flash > 0:
            self.shield_hit_flash -= dt * 4
        if self.bonus_life_flash > 0:
            self.bonus_life_flash -= dt * 2

        # Direction switching (even while walls are building)
        if input_state.up or input_state.down:
            self.horizontal = False
        elif input_state.left or input_state.right:
            self.horizontal = True

        # Cursor movement with acceleration
        if input_state.any_direction:
            self.move_held_time += dt
        else:
            self.move_held_time = 0

        # Faster movement after holding
        current_delay = self.cursor_delay if self.move_held_time < 0.3 else 0.03

        self.cursor_timer += dt
        if self.cursor_timer >= current_delay:
            moved = False
            if input_state.up and self.cursor_y > 1:
                self.cursor_y -= 1
                moved = True
            elif input_state.down and self.cursor_y < self.height - 2:
                self.cursor_y += 1
                moved = True
            elif input_state.left and self.cursor_x > 1:
                self.cursor_x -= 1
                moved = True
            elif input_state.right and self.cursor_x < self.width - 2:
                self.cursor_x += 1
                moved = True

            if moved:
                self.cursor_timer = 0

        # Start building wall on action press (only if no walls active)
        if input_state.action and not self.walls:
            # Can only start wall from empty space
            if not self.grid[self.cursor_y][self.cursor_x]:
                if self.horizontal:
                    # Two walls: one going left, one going right
                    self.walls = [
                        Wall(self.cursor_x, self.cursor_y, -1, 0),
                        Wall(self.cursor_x, self.cursor_y, 1, 0),
                    ]
                else:
                    # Two walls: one going up, one going down
                    self.walls = [
                        Wall(self.cursor_x, self.cursor_y, 0, -1),
                        Wall(self.cursor_x, self.cursor_y, 0, 1),
                    ]

        # Update active walls
        if self.walls:
            self._update_walls(dt)

        # Move atoms
        self._update_atoms(dt)

    def _update_walls(self, dt: float):
        """Update all active wall rays."""
        for wall in self.walls:
            if wall.finished or wall.dead:
                continue

            # Advance wall
            wall.progress += wall.speed * dt

            while wall.progress >= 1.0 and not wall.finished and not wall.dead:
                wall.progress -= 1.0
                wall.length += 1

                tip_x, tip_y = wall.get_tip_position()

                # Check bounds
                if tip_x < 0 or tip_x >= self.width or tip_y < 0 or tip_y >= self.height:
                    wall.finished = True
                    break

                # Check if hit existing wall
                if self.grid[tip_y][tip_x]:
                    wall.finished = True
                    break

        # Check if both walls are done (finished or dead)
        all_done = all(w.finished or w.dead for w in self.walls)

        if all_done and self.walls:
            # Commit completed walls to grid
            for wall in self.walls:
                if wall.finished and not wall.dead:
                    for x, y in wall.get_all_positions():
                        if 0 <= x < self.width and 0 <= y < self.height:
                            self.grid[y][x] = True

            # Also mark the starting position if at least one wall finished
            any_finished = any(w.finished and not w.dead for w in self.walls)
            if any_finished:
                start_x = self.walls[0].start_x
                start_y = self.walls[0].start_y
                self.grid[start_y][start_x] = True

                # Fill regions without atoms
                self.fill_empty_regions()
                self.update_fill_percent()
                self.score += 10

            # Clear walls
            self.walls = []

            # Check win condition
            if self.fill_percent >= 75:
                self.score += (self.fill_percent - 75) * 5  # Bonus for extra fill
                self.level += 1
                self.start_next_level()

    def _check_atom_at_position(self, px: int, py: int) -> bool:
        """Check if any atom occupies the given position."""
        for atom in self.atoms:
            ax, ay = int(atom['x']), int(atom['y'])
            # Atoms are 2x2
            for adx in range(2):
                for ady in range(2):
                    if px == ax + adx and py == ay + ady:
                        return True
        return False

    def _check_wall_collisions(self):
        """
        Check for atom collisions with building walls.
        Handles the special case where hitting the source point costs 2 lives.
        """
        if not self.walls:
            return

        # Get source point (shared by both walls)
        source_x = self.walls[0].start_x
        source_y = self.walls[0].start_y

        # Check if atom hit the source point (where both rays originate)
        # This costs 2 lives and kills both walls
        source_hit = self._check_atom_at_position(source_x, source_y)

        if source_hit:
            # Kill both walls and lose 2 lives
            for wall in self.walls:
                wall.dead = True
            self.lives -= 2
            if self.lives <= 0:
                self.lives = 0
                self.state = GameState.GAME_OVER
            return

        # Check each wall independently for hits along their length
        for wall in self.walls:
            if wall.dead or wall.finished:
                continue

            wall_hit = False

            # Check all positions along the wall (excluding source, handled above)
            for wx, wy in wall.get_all_positions():
                if self._check_atom_at_position(wx, wy):
                    wall_hit = True
                    break

            if wall_hit:
                wall.dead = True
                self.lives -= 1
                if self.lives <= 0:
                    self.lives = 0
                    self.state = GameState.GAME_OVER

    def _update_atoms(self, dt: float):
        """Update atom positions and handle bouncing."""
        # Get all wall positions for bounce collision (not destruction)
        wall_positions = set()
        for wall in self.walls:
            if not wall.dead:
                wall_positions.add((wall.start_x, wall.start_y))
                for pos in wall.get_all_positions():
                    wall_positions.add(pos)

        for atom in self.atoms:
            # Calculate new position
            new_x = atom['x'] + atom['dx'] * dt
            new_y = atom['y'] + atom['dy'] * dt

            # Check collision with grid walls and active building walls
            bounce_x = False
            bounce_y = False

            # Check all 4 corners of 2x2 atom
            for dx in range(2):
                for dy in range(2):
                    check_x = int(new_x) + dx
                    check_y = int(new_y) + dy

                    if 0 <= check_x < self.width and 0 <= check_y < self.height:
                        hit_wall = self.grid[check_y][check_x] or (check_x, check_y) in wall_positions

                        if hit_wall:
                            old_check_x = int(atom['x']) + dx
                            old_check_y = int(atom['y']) + dy

                            # Determine bounce direction
                            if old_check_x != check_x:
                                bounce_x = True
                            if old_check_y != check_y:
                                bounce_y = True

            if bounce_x:
                atom['dx'] = -atom['dx']
                new_x = atom['x']
            if bounce_y:
                atom['dy'] = -atom['dy']
                new_y = atom['y']

            atom['x'] = new_x
            atom['y'] = new_y

        # Now check for wall destruction (separate from bouncing)
        self._check_wall_collisions()

        # Check cursor collision (only after shield expires)
        self._check_cursor_collision()

    def _check_cursor_collision(self):
        """Check if an atom hits the cursor. Damages player after shield expires."""
        # Shield active - no damage but show feedback
        shielded = self.level_time < self.shield_duration

        for atom in self.atoms:
            ax, ay = int(atom['x']), int(atom['y'])

            # Check if atom (2x2) overlaps cursor position
            cursor_hit = False
            for adx in range(2):
                for ady in range(2):
                    if ax + adx == self.cursor_x and ay + ady == self.cursor_y:
                        cursor_hit = True
                        break
                if cursor_hit:
                    break

            if cursor_hit:
                if shielded:
                    # Shield absorbs hit - just flash
                    self.shield_hit_flash = 1.0
                else:
                    # Take damage!
                    self.lives -= 1
                    # Brief invincibility after hit (reset shield for 1 second)
                    self.level_time = self.shield_duration - 1.0
                    if self.lives <= 0:
                        self.lives = 0
                        self.state = GameState.GAME_OVER
                    return  # Only take one hit per frame

    def start_next_level(self):
        """Start the next level."""
        # Reset grid but keep score
        self.grid = [[False for _ in range(self.width)] for _ in range(self.height)]

        # Draw border
        for x in range(self.width):
            self.grid[0][x] = True
            self.grid[self.height - 1][x] = True
        for y in range(self.height):
            self.grid[y][0] = True
            self.grid[y][self.width - 1] = True

        # Bonus life at level 3, then every 2 levels (3, 5, 7, 9...) - max 10 lives
        if self.level >= 3 and self.level % 2 == 1:
            self.lives = min(10, self.lives + 1)
            self.bonus_life_flash = 1.0  # Visual feedback

        # Spawn more atoms (lives persist - no reset!)
        atom_count = self.level + 1
        self.spawn_atoms(atom_count)
        self.update_fill_percent()
        self.walls = []

        # Reset shield timer for new level
        self.level_time = 0.0
        self.shield_hit_flash = 0.0

    def fill_empty_regions(self):
        """Fill regions that don't contain atoms using flood fill."""
        visited = [[False for _ in range(self.width)] for _ in range(self.height)]

        # Get atom positions (2x2 for each)
        atom_positions = set()
        for atom in self.atoms:
            for dx in range(2):
                for dy in range(2):
                    atom_positions.add((int(atom['x']) + dx, int(atom['y']) + dy))

        def flood_fill(start_x, start_y):
            """Return all pixels in this region and whether it contains an atom."""
            region = []
            has_atom = False
            stack = [(start_x, start_y)]

            while stack:
                x, y = stack.pop()
                if x < 0 or x >= self.width or y < 0 or y >= self.height:
                    continue
                if visited[y][x] or self.grid[y][x]:
                    continue

                visited[y][x] = True
                region.append((x, y))

                if (x, y) in atom_positions:
                    has_atom = True

                stack.extend([(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)])

            return region, has_atom

        # Find and fill all regions without atoms
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                if not visited[y][x] and not self.grid[y][x]:
                    region, has_atom = flood_fill(x, y)
                    if not has_atom:
                        # Fill this region
                        for rx, ry in region:
                            self.grid[ry][rx] = True
                        self.score += len(region)

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Draw HUD
        self.display.draw_text_small(1, 1, f"L{self.level}", Colors.CYAN)
        self.display.draw_text_small(18, 1, f"{self.fill_percent}%", Colors.GREEN)

        # Draw lives as small dots (flash green when bonus life gained)
        for i in range(self.lives):
            x = 50 + (i % 5) * 3
            y = 2 if i < 5 else 5

            # Flash all lives green/white when bonus gained
            if self.bonus_life_flash > 0:
                flash = int(self.bonus_life_flash * 4) % 2 == 0
                life_color = Colors.WHITE if flash else Colors.GREEN
            else:
                life_color = Colors.RED

            self.display.set_pixel(x, y, life_color)
            self.display.set_pixel(x + 1, y, life_color)

        # Show "+1" indicator when bonus life gained
        if self.bonus_life_flash > 0.3:
            self.display.draw_text_small(44, 1, "+1", Colors.GREEN)

        # Draw direction indicator
        dir_char = "H" if self.horizontal else "V"
        self.display.draw_text_small(42, 1, dir_char, Colors.YELLOW)

        # Draw separator
        self.display.draw_line(0, 8, 63, 8, Colors.DARK_GRAY)

        # Draw grid (walls and filled areas)
        for y in range(self.height):
            for x in range(self.width):
                screen_x = self.play_left + x
                screen_y = self.play_top + y
                if self.grid[y][x]:
                    # Border vs filled interior
                    if y == 0 or y == self.height - 1 or x == 0 or x == self.width - 1:
                        self.display.set_pixel(screen_x, screen_y, Colors.BLUE)
                    else:
                        self.display.set_pixel(screen_x, screen_y, (100, 100, 140))

        # Draw building walls
        for wall in self.walls:
            if wall.dead:
                continue

            # Draw start position
            sx = self.play_left + wall.start_x
            sy = self.play_top + wall.start_y
            self.display.set_pixel(sx, sy, Colors.YELLOW)

            # Draw wall body
            for wx, wy in wall.get_all_positions():
                screen_x = self.play_left + wx
                screen_y = self.play_top + wy
                if 0 <= screen_x < GRID_SIZE and 0 <= screen_y < GRID_SIZE:
                    # Brighter at tip
                    if (wx, wy) == wall.get_tip_position():
                        self.display.set_pixel(screen_x, screen_y, Colors.WHITE)
                    else:
                        self.display.set_pixel(screen_x, screen_y, Colors.YELLOW)

        # Draw atoms (2x2)
        for atom in self.atoms:
            ax, ay = int(atom['x']), int(atom['y'])
            for dx in range(2):
                for dy in range(2):
                    screen_x = self.play_left + ax + dx
                    screen_y = self.play_top + ay + dy
                    if 0 <= screen_x < GRID_SIZE and 0 <= screen_y < GRID_SIZE:
                        self.display.set_pixel(screen_x, screen_y, atom['color'])

        # Draw shield effect when active
        cx = self.play_left + self.cursor_x
        cy = self.play_top + self.cursor_y
        shielded = self.level_time < self.shield_duration

        if shielded:
            # Pulsing shield circle
            import math
            pulse = 0.5 + 0.5 * math.sin(self.level_time * 6)
            shield_time_left = self.shield_duration - self.level_time

            # Shield gets dimmer as it runs out
            intensity = min(1.0, shield_time_left / 2.0)

            # Flash brighter when hit
            if self.shield_hit_flash > 0:
                intensity = 1.0
                pulse = 1.0

            # Shield color (cyan with pulse)
            shield_brightness = int(80 + 120 * pulse * intensity)
            shield_color = (0, shield_brightness, shield_brightness)

            # Draw shield ring (radius 4)
            shield_points = [
                (0, -4), (0, 4), (-4, 0), (4, 0),  # Cardinals
                (-3, -3), (3, -3), (-3, 3), (3, 3),  # Diagonals
                (-2, -3), (2, -3), (-2, 3), (2, 3),  # Near diagonals
                (-3, -2), (3, -2), (-3, 2), (3, 2),
            ]
            for dx, dy in shield_points:
                px, py = cx + dx, cy + dy
                if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                    self.display.set_pixel(px, py, shield_color)

            # Show countdown in HUD area
            secs_left = int(shield_time_left) + 1
            self.display.draw_text_small(56, 1, str(secs_left), Colors.CYAN)

        # Draw cursor as directional arrows
        if int(self.cursor_blink * 4) % 2 == 0 or self.walls:
            # Color based on whether we can build here
            can_build = not self.grid[self.cursor_y][self.cursor_x] and not self.walls
            cursor_color = Colors.GREEN if can_build else Colors.RED

            # Flash white briefly after taking damage
            if not shielded and self.level_time < self.shield_duration + 1.0:
                if int(self.level_time * 8) % 2 == 0:
                    cursor_color = Colors.WHITE

            if self.horizontal:
                # Horizontal arrows pointing left and right (< >)
                # Left arrow
                self.display.set_pixel(cx - 2, cy, cursor_color)
                self.display.set_pixel(cx - 1, cy - 1, cursor_color)
                self.display.set_pixel(cx - 1, cy + 1, cursor_color)
                # Right arrow
                self.display.set_pixel(cx + 2, cy, cursor_color)
                self.display.set_pixel(cx + 1, cy - 1, cursor_color)
                self.display.set_pixel(cx + 1, cy + 1, cursor_color)
                # Center dot
                self.display.set_pixel(cx, cy, cursor_color)
            else:
                # Vertical arrows pointing up and down (^ v)
                # Up arrow
                self.display.set_pixel(cx, cy - 2, cursor_color)
                self.display.set_pixel(cx - 1, cy - 1, cursor_color)
                self.display.set_pixel(cx + 1, cy - 1, cursor_color)
                # Down arrow
                self.display.set_pixel(cx, cy + 2, cursor_color)
                self.display.set_pixel(cx - 1, cy + 1, cursor_color)
                self.display.set_pixel(cx + 1, cy + 1, cursor_color)
                # Center dot
                self.display.set_pixel(cx, cy, cursor_color)

    def draw_game_over(self):
        """Custom game over screen."""
        self.display.clear(Colors.BLACK)
        self.display.draw_text_small(8, 20, "GAME OVER", Colors.RED)
        self.display.draw_text_small(12, 32, f"LEVEL:{self.level}", Colors.CYAN)
        self.display.draw_text_small(12, 40, f"SCORE:{self.score}", Colors.WHITE)
        self.display.draw_text_small(4, 50, "SPACE:RETRY", Colors.GRAY)
