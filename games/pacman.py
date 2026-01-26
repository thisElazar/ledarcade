"""
Pac-Man - Classic maze chase
============================
Navigate the maze, eat all dots. Avoid ghosts unless you eat a power pellet!

Controls:
  Arrow Keys - Set direction (queued for next intersection)
  Escape     - Return to menu
"""

import random
import math
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


class PacMan(Game):
    name = "PAC-MAN"
    description = "Eat dots, avoid ghosts!"
    category = "arcade"

    # Simplified maze for 64x64 display (21x19 tiles at 3px each = 63x57)
    # 0=empty, 1=wall, 2=dot, 3=power pellet, 4=ghost house door
    # Fully connected - every dot reachable
    MAZE_TEMPLATE = [
        "111111111111111111111",
        "132222222222222222231",
        "121211121112112112121",
        "122212222222222212221",
        "112212111411121212211",
        "122212000000002122221",
        "121212011111102121121",
        "002222010000102222200",
        "121212010000102121121",
        "122212000000002122221",
        "112212011111101212211",
        "122222222222222222221",
        "121121121112112112121",
        "122222222222222222221",
        "121211211112112112121",
        "122222222222222222221",
        "121121121112112112121",
        "132222222222222222231",
        "111111111111111111111",
    ]

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0
        self.lives = 3
        self.level = 1

        # Maze dimensions
        self.maze_width = 21
        self.maze_height = 19
        self.tile_size = 3  # Each tile is 3x3 pixels

        # Offset to center maze
        self.offset_x = 0
        self.offset_y = 7  # Leave room for HUD at top

        # Initialize maze from template
        self.maze = []
        self.dots_remaining = 0
        for row in self.MAZE_TEMPLATE:
            maze_row = []
            for char in row:
                cell = int(char)
                maze_row.append(cell)
                if cell == 2 or cell == 3:
                    self.dots_remaining += 1
            self.maze.append(maze_row)

        # Pac-Man position (tile coordinates, float for smooth movement)
        self.pac_x = 11.0
        self.pac_y = 13.0
        self.pac_dir = (0, 0)  # Current direction
        self.pac_next_dir = (0, 0)  # Queued direction
        self.pac_speed = 6.0  # Tiles per second
        self.mouth_open = True
        self.mouth_timer = 0

        # Ghosts - positioned in/around ghost house (rows 5-9, cols 7-13)
        self.ghosts = [
            {'name': 'blinky', 'x': 10.0, 'y': 5.0, 'dir': (-1, 0), 'color': Colors.RED,
             'scatter_target': (19, 0), 'in_house': False, 'frightened': False, 'eaten': False},
            {'name': 'pinky', 'x': 10.0, 'y': 7.0, 'dir': (0, 1), 'color': Colors.PINK,
             'scatter_target': (1, 0), 'in_house': True, 'frightened': False, 'eaten': False},
            {'name': 'inky', 'x': 9.0, 'y': 8.0, 'dir': (0, -1), 'color': Colors.CYAN,
             'scatter_target': (19, 18), 'in_house': True, 'frightened': False, 'eaten': False},
            {'name': 'clyde', 'x': 11.0, 'y': 8.0, 'dir': (0, -1), 'color': Colors.ORANGE,
             'scatter_target': (0, 18), 'in_house': True, 'frightened': False, 'eaten': False},
        ]
        self.ghost_speed = 4.5
        self.frightened_speed = 3.0
        self.frightened_timer = 0
        self.ghost_release_timer = 0
        self.ghosts_released = 1  # Blinky starts outside

        # Mode switching (scatter/chase)
        self.chase_mode = True
        self.mode_timer = 0
        self.mode_duration = 20.0

        # Power pellet flashing
        self.pellet_flash = 0

        # Eaten ghost points
        self.ghost_points = 200

    def get_tile(self, x, y):
        """Get tile at position, handling wrapping."""
        tx, ty = int(x), int(y)
        if ty < 0 or ty >= self.maze_height:
            return 1  # Wall
        # Wrap horizontally for tunnel
        if tx < 0:
            tx = self.maze_width - 1
        elif tx >= self.maze_width:
            tx = 0
        return self.maze[ty][tx]

    def set_tile(self, x, y, value):
        """Set tile value."""
        tx, ty = int(x), int(y)
        if 0 <= ty < self.maze_height and 0 <= tx < self.maze_width:
            self.maze[ty][tx] = value

    def is_wall(self, x, y):
        """Check if position is a wall."""
        tile = self.get_tile(x, y)
        return tile == 1

    def is_passable(self, x, y, is_ghost=False):
        """Check if position is passable."""
        tile = self.get_tile(x, y)
        if tile == 1:
            return False
        if tile == 4 and not is_ghost:  # Ghost house door
            return False
        return True

    def can_move(self, x, y, dx, dy, is_ghost=False):
        """Check if entity can move in direction from position (x,y)."""
        # Round position to tile and check adjacent tile
        tile_x = int(round(x))
        tile_y = int(round(y))
        next_tile_x = tile_x + dx
        next_tile_y = tile_y + dy
        return self.tile_passable(next_tile_x, next_tile_y, is_ghost)

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        # Handle direction input (queue for next possible turn)
        if input_state.up:
            self.pac_next_dir = (0, -1)
        elif input_state.down:
            self.pac_next_dir = (0, 1)
        elif input_state.left:
            self.pac_next_dir = (-1, 0)
        elif input_state.right:
            self.pac_next_dir = (1, 0)

        # Update mode timer
        self.mode_timer += dt
        if self.mode_timer >= self.mode_duration:
            self.mode_timer = 0
            self.chase_mode = not self.chase_mode

        # Update frightened timer
        if self.frightened_timer > 0:
            self.frightened_timer -= dt
            if self.frightened_timer <= 0:
                for ghost in self.ghosts:
                    ghost['frightened'] = False
                self.ghost_points = 200

        # Release ghosts from house
        self.ghost_release_timer += dt
        if self.ghost_release_timer >= 4.0 and self.ghosts_released < 4:
            for ghost in self.ghosts:
                if ghost['in_house']:
                    ghost['in_house'] = False
                    ghost['x'] = 9.0  # Exit through door
                    ghost['y'] = 5.0
                    ghost['dir'] = (-1, 0)
                    self.ghosts_released += 1
                    self.ghost_release_timer = 0
                    break

        # Move Pac-Man
        self.move_pacman(dt)

        # Animate mouth
        self.mouth_timer += dt
        if self.mouth_timer >= 0.15:
            self.mouth_timer = 0
            self.mouth_open = not self.mouth_open

        # Check dot collision at current tile
        tx, ty = int(self.pac_x + 0.5), int(self.pac_y + 0.5)
        if 0 <= tx < self.maze_width and 0 <= ty < self.maze_height:
            tile = self.maze[ty][tx]
            if tile == 2:  # Dot
                self.maze[ty][tx] = 0
                self.score += 10
                self.dots_remaining -= 1
            elif tile == 3:  # Power pellet
                self.maze[ty][tx] = 0
                self.score += 50
                self.dots_remaining -= 1
                self.activate_power()

        # Check win condition
        if self.dots_remaining <= 0:
            self.level += 1
            self.next_level()
            return

        # Move ghosts
        for ghost in self.ghosts:
            self.move_ghost(ghost, dt)

        # Check ghost collisions
        for ghost in self.ghosts:
            dist = math.sqrt((self.pac_x - ghost['x'])**2 + (self.pac_y - ghost['y'])**2)
            if dist < 0.7:
                if ghost['frightened'] and not ghost['eaten']:
                    ghost['eaten'] = True
                    self.score += self.ghost_points
                    self.ghost_points *= 2
                elif not ghost['eaten']:
                    self.lives -= 1
                    if self.lives <= 0:
                        self.state = GameState.GAME_OVER
                    else:
                        self.respawn()
                    return

        # Pellet flash animation
        self.pellet_flash += dt

    def move_pacman(self, dt: float):
        """Move Pac-Man with queued direction handling and turn assist."""
        # Get current tile
        cur_tile_x = int(round(self.pac_x))
        cur_tile_y = int(round(self.pac_y))

        # Try to turn to queued direction (with generous turn assist)
        if self.pac_next_dir != (0, 0) and self.pac_next_dir != self.pac_dir:
            ndx, ndy = self.pac_next_dir

            # Check multiple nearby tiles for valid turn points
            turn_made = False

            # Tiles to check: current tile and one tile back in current direction
            tiles_to_check = [(cur_tile_x, cur_tile_y)]
            if self.pac_dir != (0, 0):
                back_x = cur_tile_x - self.pac_dir[0]
                back_y = cur_tile_y - self.pac_dir[1]
                tiles_to_check.append((back_x, back_y))

            for check_tx, check_ty in tiles_to_check:
                # Can we turn at this tile?
                next_x = check_tx + ndx
                next_y = check_ty + ndy

                if self.tile_passable(next_x, next_y, is_ghost=False):
                    # Check if we're close enough to this turn point
                    dist_x = abs(self.pac_x - check_tx)
                    dist_y = abs(self.pac_y - check_ty)

                    # Generous turn window
                    if self.pac_dir == (0, 0):
                        can_turn = dist_x < 0.5 and dist_y < 0.5
                    elif self.pac_dir[0] != 0:  # Moving horizontally
                        can_turn = dist_y < 0.3 and dist_x < 0.6
                    else:  # Moving vertically
                        can_turn = dist_x < 0.3 and dist_y < 0.6

                    if can_turn:
                        self.pac_dir = self.pac_next_dir
                        # Snap to the turn point's lane
                        if ndx != 0:  # Turning to horizontal
                            self.pac_y = float(check_ty)
                        if ndy != 0:  # Turning to vertical
                            self.pac_x = float(check_tx)
                        turn_made = True
                        break

            # If we couldn't turn, keep the queued direction for later

        # Move in current direction
        if self.pac_dir != (0, 0):
            dx, dy = self.pac_dir
            new_x = self.pac_x + dx * self.pac_speed * dt
            new_y = self.pac_y + dy * self.pac_speed * dt

            # Get the tile Pac-Man would be in after moving
            new_tile_x = int(round(new_x))
            new_tile_y = int(round(new_y))

            # Also check the tile ahead for early wall detection
            ahead_tile_x = int(new_x + dx * 0.5)
            ahead_tile_y = int(new_y + dy * 0.5)

            # Current tile must always be passable
            if not self.tile_passable(new_tile_x, new_tile_y, is_ghost=False):
                # Would enter a wall - stop at tile center
                self.pac_x = float(cur_tile_x)
                self.pac_y = float(cur_tile_y)
            elif not self.tile_passable(ahead_tile_x, ahead_tile_y, is_ghost=False):
                # Approaching a wall - stop at the edge of current tile
                if dx > 0:
                    max_x = float(new_tile_x) + 0.4
                    self.pac_x = min(new_x, max_x)
                elif dx < 0:
                    min_x = float(new_tile_x) - 0.4
                    self.pac_x = max(new_x, min_x)
                if dy > 0:
                    max_y = float(new_tile_y) + 0.4
                    self.pac_y = min(new_y, max_y)
                elif dy < 0:
                    min_y = float(new_tile_y) - 0.4
                    self.pac_y = max(new_y, min_y)
            else:
                # Safe to move
                self.pac_x = new_x
                self.pac_y = new_y

        # Tunnel wrap
        if self.pac_x < 0:
            self.pac_x = self.maze_width - 1.0
        elif self.pac_x >= self.maze_width:
            self.pac_x = 0.0

    def tile_passable(self, tx, ty, is_ghost=False):
        """Check if a specific tile is passable."""
        if tx < 0 or tx >= self.maze_width or ty < 0 or ty >= self.maze_height:
            # Allow tunnel wrap on row 7
            if ty == 7 and (tx < 0 or tx >= self.maze_width):
                return True
            return False
        tile = self.maze[ty][tx]
        if tile == 1:
            return False
        if tile == 4 and not is_ghost:
            return False
        return True

    def move_ghost(self, ghost, dt: float):
        """Move ghost with AI."""
        if ghost['in_house']:
            # Float up and down in house
            ghost['y'] += ghost['dir'][1] * 1.5 * dt
            if ghost['y'] < 7.0:
                ghost['dir'] = (0, 1)
            elif ghost['y'] > 8.5:
                ghost['dir'] = (0, -1)
            return

        # Determine speed
        if ghost['eaten']:
            speed = self.ghost_speed * 2
        elif ghost['frightened']:
            speed = self.frightened_speed
        else:
            speed = self.ghost_speed

        # Get current tile position
        gx, gy = ghost['x'], ghost['y']
        tile_x, tile_y = int(round(gx)), int(round(gy))

        # Check if at tile center (for direction decisions)
        at_center = abs(gx - tile_x) < 0.1 and abs(gy - tile_y) < 0.1

        if at_center:
            # Snap to center
            ghost['x'] = float(tile_x)
            ghost['y'] = float(tile_y)
            gx, gy = ghost['x'], ghost['y']

            # Check for eaten ghost reaching home
            if ghost['eaten']:
                if tile_x == 9 and tile_y == 5:
                    ghost['eaten'] = False
                    ghost['frightened'] = False
                    ghost['in_house'] = True
                    ghost['x'] = 10.0
                    ghost['y'] = 7.5
                    ghost['dir'] = (0, 1)
                    return

            # Find valid directions
            possible = []
            reverse = (-ghost['dir'][0], -ghost['dir'][1])

            for d in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                next_x = tile_x + d[0]
                next_y = tile_y + d[1]

                if self.tile_passable(next_x, next_y, is_ghost=True):
                    # Don't reverse unless necessary
                    if d != reverse or ghost['frightened'] or ghost['eaten']:
                        possible.append(d)

            # If no non-reverse options, allow reverse
            if not possible:
                for d in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                    next_x = tile_x + d[0]
                    next_y = tile_y + d[1]
                    if self.tile_passable(next_x, next_y, is_ghost=True):
                        possible.append(d)

            # Choose direction
            if possible:
                if ghost['frightened'] and not ghost['eaten']:
                    ghost['dir'] = random.choice(possible)
                else:
                    target = self.get_ghost_target(ghost)
                    best_dir = possible[0]
                    best_dist = float('inf')

                    for d in possible:
                        nx = tile_x + d[0]
                        ny = tile_y + d[1]
                        dist = (nx - target[0])**2 + (ny - target[1])**2
                        if dist < best_dist:
                            best_dist = dist
                            best_dir = d

                    ghost['dir'] = best_dir

        # Move in current direction
        dx, dy = ghost['dir']
        if dx != 0 or dy != 0:
            new_x = gx + dx * speed * dt
            new_y = gy + dy * speed * dt

            # Check if we're about to enter a wall
            check_x = int(round(new_x + dx * 0.4))
            check_y = int(round(new_y + dy * 0.4))

            if self.tile_passable(check_x, check_y, is_ghost=True):
                ghost['x'] = new_x
                ghost['y'] = new_y
            else:
                # Stop at tile center
                ghost['x'] = round(ghost['x'])
                ghost['y'] = round(ghost['y'])

        # Tunnel wrap
        if ghost['x'] < 0:
            ghost['x'] = self.maze_width - 1.0
        elif ghost['x'] >= self.maze_width:
            ghost['x'] = 0.0

    def get_ghost_target(self, ghost):
        """Get target tile for ghost AI."""
        if ghost['eaten']:
            return (9.0, 5.0)  # Ghost house door

        if not self.chase_mode:
            return ghost['scatter_target']

        name = ghost['name']
        if name == 'blinky':
            return (self.pac_x, self.pac_y)
        elif name == 'pinky':
            return (self.pac_x + self.pac_dir[0] * 4, self.pac_y + self.pac_dir[1] * 4)
        elif name == 'inky':
            px = self.pac_x + self.pac_dir[0] * 2
            py = self.pac_y + self.pac_dir[1] * 2
            blinky = self.ghosts[0]
            return (px + (px - blinky['x']), py + (py - blinky['y']))
        elif name == 'clyde':
            dist = math.sqrt((self.pac_x - ghost['x'])**2 + (self.pac_y - ghost['y'])**2)
            if dist > 8:
                return (self.pac_x, self.pac_y)
            else:
                return ghost['scatter_target']

        return (self.pac_x, self.pac_y)

    def activate_power(self):
        """Activate power pellet effect."""
        self.frightened_timer = 6.0
        self.ghost_points = 200
        for ghost in self.ghosts:
            if not ghost['eaten'] and not ghost['in_house']:
                ghost['frightened'] = True
                ghost['dir'] = (-ghost['dir'][0], -ghost['dir'][1])

    def respawn(self):
        """Respawn Pac-Man after death."""
        self.pac_x = 11.0
        self.pac_y = 13.0
        self.pac_dir = (0, 0)
        self.pac_next_dir = (0, 0)

        # Reset ghosts
        self.ghosts[0]['x'], self.ghosts[0]['y'] = 10.0, 5.0
        self.ghosts[0]['in_house'] = False
        self.ghosts[0]['dir'] = (-1, 0)
        self.ghosts[1]['x'], self.ghosts[1]['y'] = 10.0, 7.0
        self.ghosts[1]['in_house'] = True
        self.ghosts[2]['x'], self.ghosts[2]['y'] = 9.0, 8.0
        self.ghosts[2]['in_house'] = True
        self.ghosts[3]['x'], self.ghosts[3]['y'] = 11.0, 8.0
        self.ghosts[3]['in_house'] = True

        for ghost in self.ghosts:
            ghost['frightened'] = False
            ghost['eaten'] = False

        self.ghosts_released = 1
        self.ghost_release_timer = 0
        self.frightened_timer = 0

    def next_level(self):
        """Start next level."""
        self.maze = []
        self.dots_remaining = 0
        for row in self.MAZE_TEMPLATE:
            maze_row = []
            for char in row:
                cell = int(char)
                maze_row.append(cell)
                if cell == 2 or cell == 3:
                    self.dots_remaining += 1
            self.maze.append(maze_row)

        self.respawn()
        self.ghost_speed = min(6.0, self.ghost_speed + 0.3)

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Draw HUD
        self.display.draw_text_small(1, 1, f"{self.score}", Colors.WHITE)

        # Draw lives
        for i in range(self.lives - 1):
            lx = 50 + i * 5
            self.display.set_pixel(lx, 2, Colors.YELLOW)
            self.display.set_pixel(lx + 1, 2, Colors.YELLOW)
            self.display.set_pixel(lx, 3, Colors.YELLOW)
            self.display.set_pixel(lx + 1, 3, Colors.YELLOW)

        # Draw maze
        for ty in range(self.maze_height):
            for tx in range(self.maze_width):
                px = self.offset_x + tx * self.tile_size
                py = self.offset_y + ty * self.tile_size
                tile = self.maze[ty][tx]

                if tile == 1:  # Wall
                    for dx in range(self.tile_size):
                        for dy in range(self.tile_size):
                            self.display.set_pixel(px + dx, py + dy, Colors.BLUE)
                elif tile == 4:  # Ghost house door
                    self.display.set_pixel(px + 1, py + 1, Colors.PINK)
                elif tile == 2:  # Dot
                    self.display.set_pixel(px + 1, py + 1, (255, 255, 200))
                elif tile == 3:  # Power pellet (flashing)
                    if int(self.pellet_flash * 4) % 2 == 0:
                        for dx in range(2):
                            for dy in range(2):
                                self.display.set_pixel(px + dx, py + dy, (255, 255, 200))

        # Draw ghosts (2x2)
        for ghost in self.ghosts:
            gx = self.offset_x + int(ghost['x'] * self.tile_size) + 1
            gy = self.offset_y + int(ghost['y'] * self.tile_size) + 1

            if ghost['eaten']:
                # Just eyes
                self.display.set_pixel(gx, gy, Colors.WHITE)
                self.display.set_pixel(gx + 1, gy, Colors.WHITE)
            elif ghost['frightened']:
                if self.frightened_timer < 2.0 and int(self.frightened_timer * 4) % 2 == 0:
                    color = Colors.WHITE
                else:
                    color = (0, 0, 200)
                self.display.set_pixel(gx, gy, color)
                self.display.set_pixel(gx + 1, gy, color)
                self.display.set_pixel(gx, gy + 1, color)
                self.display.set_pixel(gx + 1, gy + 1, color)
            else:
                color = ghost['color']
                self.display.set_pixel(gx, gy, color)
                self.display.set_pixel(gx + 1, gy, color)
                self.display.set_pixel(gx, gy + 1, color)
                self.display.set_pixel(gx + 1, gy + 1, color)
                # Eyes
                self.display.set_pixel(gx, gy, Colors.WHITE)
                self.display.set_pixel(gx + 1, gy, Colors.WHITE)

        # Draw Pac-Man (2x2 yellow)
        px = self.offset_x + int(self.pac_x * self.tile_size) + 1
        py = self.offset_y + int(self.pac_y * self.tile_size) + 1

        self.display.set_pixel(px, py, Colors.YELLOW)
        self.display.set_pixel(px + 1, py, Colors.YELLOW)
        self.display.set_pixel(px, py + 1, Colors.YELLOW)
        self.display.set_pixel(px + 1, py + 1, Colors.YELLOW)

        # Mouth animation (cut out one pixel)
        if self.mouth_open:
            if self.pac_dir == (1, 0):  # Right
                self.display.set_pixel(px + 1, py + 1, Colors.BLACK)
            elif self.pac_dir == (-1, 0):  # Left
                self.display.set_pixel(px, py + 1, Colors.BLACK)
            elif self.pac_dir == (0, -1):  # Up
                self.display.set_pixel(px + 1, py, Colors.BLACK)
            elif self.pac_dir == (0, 1):  # Down
                self.display.set_pixel(px + 1, py + 1, Colors.BLACK)

    def draw_game_over(self):
        """Custom game over screen."""
        self.display.clear(Colors.BLACK)
        self.display.draw_text_small(8, 20, "GAME OVER", Colors.RED)
        self.display.draw_text_small(12, 32, f"SCORE:{self.score}", Colors.WHITE)
        self.display.draw_text_small(16, 40, f"LEVEL:{self.level}", Colors.YELLOW)
        self.display.draw_text_small(4, 50, "SPACE:RETRY", Colors.GRAY)
