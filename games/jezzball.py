"""
JezzBall - Trap the bouncing atoms
==================================
Build walls to divide the play area. Trap atoms in smaller areas.
Complete the level when 75%+ of the area is filled with walls.

Controls:
  Arrow Keys - Move cursor
  Space + Up/Down - Build horizontal wall
  Space + Left/Right - Build vertical wall
  Space alone - Build in last direction used (default: horizontal)
  Escape - Return to menu
"""

import random
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


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
        self.lives = 3

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

        # Cursor
        self.cursor_x = self.width // 2
        self.cursor_y = self.height // 2
        self.cursor_blink = 0

        # Wall building direction (True = horizontal, False = vertical)
        self.horizontal = True

        # Active walls being built (list of wall segments)
        self.building_walls = []  # {'x': int, 'y': int, 'dx': int, 'dy': int, 'pixels': list}

        # Movement timing
        self.cursor_delay = 0.08
        self.cursor_timer = 0

        # Fill percentage
        self.fill_percent = 0
        self.update_fill_percent()

    def spawn_atoms(self, count: int):
        """Spawn atoms in the play area."""
        self.atoms = []
        colors = [Colors.RED, Colors.CYAN, Colors.YELLOW, Colors.MAGENTA, Colors.ORANGE]

        for i in range(count):
            # Find a valid spawn position
            attempts = 0
            while attempts < 100:
                x = random.randint(5, self.width - 6)
                y = random.randint(5, self.height - 6)
                if not self.grid[y][x]:
                    break
                attempts += 1

            # Random direction
            dx = random.choice([-1, 1]) * random.uniform(25, 40)
            dy = random.choice([-1, 1]) * random.uniform(25, 40)

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

        # Cursor movement with repeat
        self.cursor_timer += dt
        if self.cursor_timer >= self.cursor_delay:
            if input_state.up:
                self.cursor_y = max(1, self.cursor_y - 1)
                self.cursor_timer = 0
            elif input_state.down:
                self.cursor_y = min(self.height - 2, self.cursor_y + 1)
                self.cursor_timer = 0
            elif input_state.left:
                self.cursor_x = max(1, self.cursor_x - 1)
                self.cursor_timer = 0
            elif input_state.right:
                self.cursor_x = min(self.width - 2, self.cursor_x + 1)
                self.cursor_timer = 0

        # Cursor blink
        self.cursor_blink += dt

        # Start building wall on action
        if input_state.action and not self.building_walls:
            # Determine direction based on held arrow key
            # Up/Down arrow = build vertical wall (goes up and down)
            # Left/Right arrow = build horizontal wall (goes left and right)
            if input_state.up or input_state.down:
                self.horizontal = False  # Build vertical wall
            elif input_state.left or input_state.right:
                self.horizontal = True  # Build horizontal wall

            # Can only start wall from empty space
            if not self.grid[self.cursor_y][self.cursor_x]:
                if self.horizontal:
                    # Build wall going left and right
                    self.building_walls = [
                        {'x': self.cursor_x, 'y': self.cursor_y, 'dx': -1, 'dy': 0, 'pixels': []},
                        {'x': self.cursor_x, 'y': self.cursor_y, 'dx': 1, 'dy': 0, 'pixels': []},
                    ]
                else:
                    # Build wall going up and down
                    self.building_walls = [
                        {'x': self.cursor_x, 'y': self.cursor_y, 'dx': 0, 'dy': -1, 'pixels': []},
                        {'x': self.cursor_x, 'y': self.cursor_y, 'dx': 0, 'dy': 1, 'pixels': []},
                    ]

        # Grow building walls
        walls_to_remove = []
        for wall in self.building_walls:
            # Extend wall
            wall['x'] += wall['dx']
            wall['y'] += wall['dy']

            x, y = wall['x'], wall['y']

            # Check if hit existing wall
            if 0 <= x < self.width and 0 <= y < self.height:
                if self.grid[y][x]:
                    # Wall reached existing wall - complete this segment
                    walls_to_remove.append(wall)
                else:
                    # Check atom collision with building wall
                    hit_atom = False
                    for atom in self.atoms:
                        ax, ay = int(atom['x']), int(atom['y'])
                        # Check 2x2 area for atom
                        for adx in range(2):
                            for ady in range(2):
                                if x == ax + adx and y == ay + ady:
                                    hit_atom = True
                                    break

                    if hit_atom:
                        # Wall hit by atom - destroy wall and lose life
                        self.lose_life()
                        return
                    else:
                        # Add pixel to wall
                        wall['pixels'].append((x, y))
            else:
                walls_to_remove.append(wall)

        # Remove completed wall segments
        for wall in walls_to_remove:
            if wall in self.building_walls:
                self.building_walls.remove(wall)

        # If all walls complete, commit them to grid
        if not self.building_walls and walls_to_remove:
            for wall in walls_to_remove:
                for px, py in wall['pixels']:
                    if 0 <= px < self.width and 0 <= py < self.height:
                        self.grid[py][px] = True

            # Fill areas without atoms
            self.fill_empty_regions()
            self.update_fill_percent()
            self.score += 10

            # Check win condition
            if self.fill_percent >= 75:
                self.level += 1
                self.start_next_level()

        # Move atoms
        for atom in self.atoms:
            new_x = atom['x'] + atom['dx'] * dt
            new_y = atom['y'] + atom['dy'] * dt

            # Bounce off walls
            ix, iy = int(new_x), int(new_y)

            # Check all 4 corners of 2x2 atom
            bounce_x = False
            bounce_y = False

            for dx in range(2):
                for dy in range(2):
                    check_x = int(new_x) + dx
                    check_y = int(new_y) + dy
                    if 0 <= check_x < self.width and 0 <= check_y < self.height:
                        if self.grid[check_y][check_x]:
                            # Determine if horizontal or vertical bounce
                            old_check_x = int(atom['x']) + dx
                            old_check_y = int(atom['y']) + dy
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

            # Check collision with building walls
            for wall in self.building_walls:
                for px, py in wall['pixels']:
                    for adx in range(2):
                        for ady in range(2):
                            if px == int(atom['x']) + adx and py == int(atom['y']) + ady:
                                self.lose_life()
                                return

    def lose_life(self):
        """Handle losing a life."""
        self.lives -= 1
        self.building_walls = []
        if self.lives <= 0:
            self.state = GameState.GAME_OVER

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

        # Spawn more atoms
        self.spawn_atoms(self.level + 1)
        self.update_fill_percent()
        self.lives = min(self.lives + 1, 5)  # Gain a life, max 5

    def fill_empty_regions(self):
        """Fill regions that don't contain atoms using flood fill."""
        # Find all empty regions
        visited = [[False for _ in range(self.width)] for _ in range(self.height)]

        # Get atom positions
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

        # Draw lives
        for i in range(self.lives):
            self.display.set_pixel(50 + i * 3, 2, Colors.RED)
            self.display.set_pixel(51 + i * 3, 2, Colors.RED)

        # Draw direction indicator
        dir_text = "H" if self.horizontal else "V"
        self.display.draw_text_small(42, 1, dir_text, Colors.YELLOW)

        # Draw separator
        self.display.draw_line(0, 8, 63, 8, Colors.DARK_GRAY)

        # Draw grid
        for y in range(self.height):
            for x in range(self.width):
                screen_x = self.play_left + x
                screen_y = self.play_top + y
                if self.grid[y][x]:
                    # Border vs filled
                    if y == 0 or y == self.height - 1 or x == 0 or x == self.width - 1:
                        self.display.set_pixel(screen_x, screen_y, Colors.BLUE)
                    else:
                        self.display.set_pixel(screen_x, screen_y, Colors.WHITE)

        # Draw building walls
        for wall in self.building_walls:
            for px, py in wall['pixels']:
                screen_x = self.play_left + px
                screen_y = self.play_top + py
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

        # Draw cursor (blinking crosshair)
        if int(self.cursor_blink * 4) % 2 == 0:
            cx = self.play_left + self.cursor_x
            cy = self.play_top + self.cursor_y
            cursor_color = Colors.GREEN if not self.grid[self.cursor_y][self.cursor_x] else Colors.RED

            # Crosshair
            self.display.set_pixel(cx, cy, cursor_color)
            self.display.set_pixel(cx - 1, cy, cursor_color)
            self.display.set_pixel(cx + 1, cy, cursor_color)
            self.display.set_pixel(cx, cy - 1, cursor_color)
            self.display.set_pixel(cx, cy + 1, cursor_color)

    def draw_game_over(self):
        """Custom game over screen."""
        self.display.clear(Colors.BLACK)
        self.display.draw_text_small(8, 20, "GAME OVER", Colors.RED)
        self.display.draw_text_small(12, 32, f"LEVEL:{self.level}", Colors.CYAN)
        self.display.draw_text_small(12, 40, f"SCORE:{self.score}", Colors.WHITE)
        self.display.draw_text_small(4, 50, "SPACE:RETRY", Colors.GRAY)
