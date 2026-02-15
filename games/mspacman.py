"""
Ms. Pac-Man - Maze chase with cycling mazes
=============================================
Navigate 4 distinct mazes, eat all dots. Ghosts are less predictable!
Bouncing fruit enters from the tunnels for bonus points.

Controls:
  Arrow Keys - Set direction (queued for next intersection)
  Escape     - Return to menu
"""

import random
import math
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


class MsPacMan(Game):
    name = "MS. PAK-MAN"
    description = "Eat dots, avoid ghosts!"
    category = "arcade"

    # 4 cycling maze layouts (21x19 tiles at 3px each = 63x57)
    # 0=empty, 1=wall, 2=dot, 3=power pellet, 4=ghost house door
    # Rows 7-12 are identical across all mazes (ghost house region)
    # All corridors are paths (no open areas). Two tunnels per maze.
    # Every row is a palindrome. No dead ends.
    MAZES = [
        {
            # Maze 1 (Hot Pink): Tunnels at R3, R9
            'template': [
                "111111111111111111111",  # R0
                "122212221222122212221",  # R1
                "121212121212121212121",  # R2  - narrowed to 1-wide vertical
                "032212221222122212230",  # R3  tunnel + pellets
                "121222122212221222121",  # R4
                "122212221222122212221",  # R5
                "121222122212221222121",  # R6
                "122212221222122212221",  # R7  - full corridor for T-junctions
                "121212121141121212121",  # R8  - alternating 1-wide corridors
                "021212121000121212120",  # R9  tunnel + ghost interior
                "121212121000121212121",  # R10
                "121212121111121212121",  # R11
                "122212221222122212221",  # R12 - full corridor for T-junctions
                "121222122212221222121",  # R13
                "122212221222122212221",  # R14
                "131222122212221222131",  # R15  pellets
                "121212121212121212121",  # R16 - narrowed to 1-wide vertical
                "122212221222122212221",  # R17
                "111111111111111111111",  # R18
            ],
            'wall_color': (255, 105, 180),  # Hot pink
            'tunnel_rows': [3, 9],
        },
        {
            # Maze 2 (Cyan): Tunnels at R9, R15
            'template': [
                "111111111111111111111",  # R0
                "132112221222122211231",  # R1  pellets (F-type)
                "122212221222122212221",  # R2
                "121222122212221222121",  # R3
                "122212221222122212221",  # R4
                "121212121212121212121",  # R5  - narrowed
                "122212221222122212221",  # R6  - full for T-junctions
                "122212221222122212221",  # R7  - full corridor for T-junctions
                "121212121141121212121",  # R8  - alternating 1-wide corridors
                "021212121000121212120",  # R9  tunnel + ghost interior
                "121212121000121212121",  # R10
                "121212121111121212121",  # R11
                "122212221222122212221",  # R12 - full corridor for T-junctions
                "121222122212221222121",  # R13
                "122212221222122212221",  # R14
                "031222122212221222130",  # R15  tunnel + pellets
                "122212221222122212221",  # R16
                "122112221222122211221",  # R17  (F-type)
                "111111111111111111111",  # R18
            ],
            'wall_color': (0, 255, 255),  # Cyan
            'tunnel_rows': [9, 15],
        },
        {
            # Maze 3 (Brown/Orange): Tunnels at R3, R9
            'template': [
                "111111111111111111111",  # R0
                "132212221222122212231",  # R1  pellets
                "121222122212221222121",  # R2
                "022212221222122212220",  # R3  tunnel
                "121222122212221222121",  # R4
                "122212221222122212221",  # R5
                "121212121212121212121",  # R6  - narrowed
                "122212221222122212221",  # R7  - full corridor for T-junctions
                "121212121141121212121",  # R8  - alternating 1-wide corridors
                "021212121000121212120",  # R9  tunnel + ghost interior
                "121212121000121212121",  # R10
                "121212121111121212121",  # R11
                "122212221222122212221",  # R12 - full corridor for T-junctions
                "121212121212121212121",  # R13 - narrowed
                "122212221222122212221",  # R14
                "131222122212221222131",  # R15  pellets
                "122212221222122212221",  # R16
                "122212221222122212221",  # R17
                "111111111111111111111",  # R18
            ],
            'wall_color': (180, 100, 50),  # Brown/orange
            'tunnel_rows': [3, 9],
        },
        {
            # Maze 4 (Blue): Tunnels at R9, R15
            'template': [
                "111111111111111111111",  # R0
                "122212221222122212221",  # R1
                "121212121212121212121",  # R2  - narrowed
                "132212221222122212231",  # R3  pellets
                "121222122212221222121",  # R4
                "122212221222122212221",  # R5
                "121212121212121212121",  # R6  - narrowed
                "122212221222122212221",  # R7  - full corridor for T-junctions
                "121212121141121212121",  # R8  - alternating 1-wide corridors
                "021212121000121212120",  # R9  tunnel + ghost interior
                "121212121000121212121",  # R10
                "121212121111121212121",  # R11
                "122212221222122212221",  # R12 - full corridor for T-junctions
                "121222122212221222121",  # R13
                "122212221222122212221",  # R14
                "031222122212221222130",  # R15  tunnel + pellets
                "122212221222122212221",  # R16
                "122112221222122211221",  # R17  (F-type)
                "111111111111111111111",  # R18
            ],
            'wall_color': (80, 80, 255),  # Blue
            'tunnel_rows': [9, 15],
        },
    ]

    # Fruit types: (name, color, points)
    FRUIT_TYPES = [
        ('cherry',     (255, 0, 0),     100),
        ('strawberry', (255, 50, 50),   200),
        ('orange',     (255, 165, 0),   500),
        ('pretzel',    (180, 120, 60),  700),
        ('apple',      (0, 200, 0),     1000),
        ('pear',       (180, 255, 0),   2000),
        ('banana',     (255, 255, 0),   5000),
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

        # Load initial maze
        self._load_maze(self._get_maze_index())

        # Pac-Man position (tile coordinates, float for smooth movement)
        self.pac_x = 10.0
        self.pac_y = 14.0
        self.pac_dir = (0, 0)  # Current direction
        self.pac_next_dir = (0, 0)  # Queued direction
        self.pac_speed = 6.0  # Tiles per second
        self.mouth_open = True
        self.mouth_timer = 0

        # Ghosts - positioned in/around ghost house (rows 8-11)
        self.ghosts = [
            {'name': 'blinky', 'x': 10.0, 'y': 7.0, 'dir': (-1, 0), 'color': Colors.RED,
             'scatter_target': (19, 0), 'in_house': False, 'frightened': False, 'eaten': False},
            {'name': 'pinky', 'x': 10.0, 'y': 9.0, 'dir': (0, 1), 'color': Colors.PINK,
             'scatter_target': (1, 0), 'in_house': True, 'frightened': False, 'eaten': False},
            {'name': 'inky', 'x': 9.0, 'y': 10.0, 'dir': (0, -1), 'color': Colors.CYAN,
             'scatter_target': (19, 18), 'in_house': True, 'frightened': False, 'eaten': False},
            {'name': 'clyde', 'x': 11.0, 'y': 10.0, 'dir': (0, -1), 'color': Colors.ORANGE,
             'scatter_target': (0, 18), 'in_house': True, 'frightened': False, 'eaten': False},
        ]
        # Base speeds (will be modified by level)
        self.base_ghost_speed = 4.5
        self.base_frightened_speed = 3.0
        self.ghost_speed = self.base_ghost_speed
        self.frightened_speed = self.base_frightened_speed
        self.frightened_timer = 0
        self.ghost_release_timer = 0
        self.ghosts_released = 1  # Blinky starts outside

        # Level-based difficulty settings
        self._apply_level_difficulty()

        # Mode switching (scatter/chase)
        self.chase_mode = True
        self.mode_timer = 0
        self.mode_duration = 20.0

        # Power pellet flashing
        self.pellet_flash = 0

        # Eaten ghost points
        self.ghost_points = 200

        # Fruit state
        self.fruit = {'active': False, 'x': 0.0, 'y': 0.0,
                      'dir': (1, 0), 'type': 0, 'timer': 0.0}
        self.fruit_score_display = 0
        self.fruit_score_timer = 0.0

    def _get_maze_index(self):
        """Get maze index based on current level."""
        level = self.level
        if level <= 2:
            return 0
        elif level <= 5:
            return 1
        elif level <= 9:
            return 2
        elif level <= 14:
            return 3
        else:
            return 2 + ((level - 15) % 2)  # Alternate mazes 3 & 4

    def _load_maze(self, maze_index):
        """Load a maze layout by index."""
        maze_data = self.MAZES[maze_index]
        self.wall_color = maze_data['wall_color']
        self.tunnel_rows = maze_data['tunnel_rows']
        self.maze = []
        self.dots_remaining = 0
        for row in maze_data['template']:
            maze_row = [int(ch) for ch in row]
            for cell in maze_row:
                if cell in (2, 3):
                    self.dots_remaining += 1
            self.maze.append(maze_row)
        self.dots_total = self.dots_remaining
        self.dots_eaten = 0
        self.fruit_spawned_count = 0
        self.fruit = {'active': False, 'x': 0.0, 'y': 0.0,
                      'dir': (1, 0), 'type': 0, 'timer': 0.0}

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
        tile_x = int(round(x))
        tile_y = int(round(y))
        next_tile_x = tile_x + dx
        next_tile_y = tile_y + dy
        return self.tile_passable(next_tile_x, next_tile_y, is_ghost)

    def tile_passable(self, tx, ty, is_ghost=False):
        """Check if a specific tile is passable."""
        if tx < 0 or tx >= self.maze_width or ty < 0 or ty >= self.maze_height:
            # Allow tunnel wrap on tunnel rows
            if ty in self.tunnel_rows and (tx < 0 or tx >= self.maze_width):
                return True
            return False
        tile = self.maze[ty][tx]
        if tile == 1:
            return False
        if tile == 4 and not is_ghost:
            return False
        return True

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
        ghost_release_interval = self._get_ghost_release_interval()
        if self.ghost_release_timer >= ghost_release_interval and self.ghosts_released < 4:
            for ghost in self.ghosts:
                if ghost['in_house']:
                    ghost['in_house'] = False
                    ghost['x'] = 10.0
                    ghost['y'] = 7.0
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
                self.dots_eaten += 1
                self._check_fruit_spawn()
            elif tile == 3:  # Power pellet
                self.maze[ty][tx] = 0
                self.score += 50
                self.dots_remaining -= 1
                self.dots_eaten += 1
                self.activate_power()
                self._check_fruit_spawn()

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
                    ghost['eaten_timer'] = 0
                    self.score += self.ghost_points
                    self.ghost_points *= 2
                elif not ghost['eaten']:
                    self.lives -= 1
                    if self.lives <= 0:
                        self.state = GameState.GAME_OVER
                    else:
                        self.respawn()
                    return

        # Update fruit
        self._move_fruit(dt)
        self._check_fruit_collection()

        # Update fruit score display timer
        if self.fruit_score_timer > 0:
            self.fruit_score_timer -= dt

        # Pellet flash animation
        self.pellet_flash += dt

    def _check_fruit_spawn(self):
        """Spawn fruit at ~35% and ~85% dots eaten."""
        if self.fruit_spawned_count >= 2 or self.fruit['active']:
            return
        ratio = self.dots_eaten / max(self.dots_total, 1)
        if self.fruit_spawned_count == 0 and ratio >= 0.35:
            self._spawn_fruit()
        elif self.fruit_spawned_count == 1 and ratio >= 0.85:
            self._spawn_fruit()

    def _spawn_fruit(self):
        """Spawn fruit from a random tunnel opening."""
        self.fruit_spawned_count += 1
        # Pick a random tunnel row
        row = random.choice(self.tunnel_rows)
        # Enter from left or right
        if random.random() < 0.5:
            x = 0.0
            d = (1, 0)
        else:
            x = float(self.maze_width - 1)
            d = (-1, 0)
        # Fruit type based on level
        fruit_idx = min(self.level - 1, len(self.FRUIT_TYPES) - 1)
        self.fruit = {
            'active': True,
            'x': x,
            'y': float(row),
            'dir': d,
            'type': fruit_idx,
            'timer': 10.0,  # 10 second lifetime
        }

    def _move_fruit(self, dt):
        """Move the bouncing fruit through the maze."""
        if not self.fruit['active']:
            return

        self.fruit['timer'] -= dt
        if self.fruit['timer'] <= 0:
            self.fruit['active'] = False
            return

        # Move at 75% of Pac-Man speed
        speed = self.pac_speed * 0.75
        fx, fy = self.fruit['x'], self.fruit['y']
        tile_x, tile_y = int(round(fx)), int(round(fy))

        # At tile center, pick a new direction
        at_center = abs(fx - tile_x) < 0.1 and abs(fy - tile_y) < 0.1
        if at_center:
            self.fruit['x'] = float(tile_x)
            self.fruit['y'] = float(tile_y)
            fx, fy = self.fruit['x'], self.fruit['y']

            # Find valid directions (no reverse unless stuck)
            possible = []
            reverse = (-self.fruit['dir'][0], -self.fruit['dir'][1])
            for d in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                nx = tile_x + d[0]
                ny = tile_y + d[1]
                if self.tile_passable(nx, ny, is_ghost=False):
                    if d != reverse:
                        possible.append(d)
            if not possible:
                # Allow reverse
                for d in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                    nx = tile_x + d[0]
                    ny = tile_y + d[1]
                    if self.tile_passable(nx, ny, is_ghost=False):
                        possible.append(d)
            if possible:
                self.fruit['dir'] = random.choice(possible)

        # Move
        dx, dy = self.fruit['dir']
        new_x = fx + dx * speed * dt
        new_y = fy + dy * speed * dt

        check_x = int(round(new_x + dx * 0.4))
        check_y = int(round(new_y + dy * 0.4))
        if self.tile_passable(check_x, check_y, is_ghost=False):
            self.fruit['x'] = new_x
            self.fruit['y'] = new_y
        else:
            self.fruit['x'] = round(self.fruit['x'])
            self.fruit['y'] = round(self.fruit['y'])

        # Tunnel wrap
        if self.fruit['x'] < 0:
            self.fruit['x'] = self.maze_width - 1.0
        elif self.fruit['x'] >= self.maze_width:
            self.fruit['x'] = 0.0

    def _check_fruit_collection(self):
        """Check if Pac-Man collected the fruit."""
        if not self.fruit['active']:
            return
        dist = math.sqrt((self.pac_x - self.fruit['x'])**2 +
                         (self.pac_y - self.fruit['y'])**2)
        if dist < 0.8:
            _, _, points = self.FRUIT_TYPES[self.fruit['type']]
            self.score += points
            self.fruit_score_display = points
            self.fruit_score_timer = 1.5
            self.fruit['active'] = False

    def move_pacman(self, dt: float):
        """Move Pac-Man with queued direction handling and turn assist."""
        cur_tile_x = int(round(self.pac_x))
        cur_tile_y = int(round(self.pac_y))

        # Try to turn to queued direction (with generous turn assist)
        if self.pac_next_dir != (0, 0) and self.pac_next_dir != self.pac_dir:
            ndx, ndy = self.pac_next_dir

            tiles_to_check = [(cur_tile_x, cur_tile_y)]
            if self.pac_dir != (0, 0):
                back_x = cur_tile_x - self.pac_dir[0]
                back_y = cur_tile_y - self.pac_dir[1]
                tiles_to_check.append((back_x, back_y))

            for check_tx, check_ty in tiles_to_check:
                next_x = check_tx + ndx
                next_y = check_ty + ndy

                if self.tile_passable(next_x, next_y, is_ghost=False):
                    dist_x = abs(self.pac_x - check_tx)
                    dist_y = abs(self.pac_y - check_ty)

                    if self.pac_dir == (0, 0):
                        can_turn = dist_x < 0.5 and dist_y < 0.5
                    elif self.pac_dir[0] != 0:
                        can_turn = dist_y < 0.3 and dist_x < 0.6
                    else:
                        can_turn = dist_x < 0.3 and dist_y < 0.6

                    if can_turn:
                        self.pac_dir = self.pac_next_dir
                        if ndx != 0:
                            self.pac_y = float(check_ty)
                        if ndy != 0:
                            self.pac_x = float(check_tx)
                        break

        # Move in current direction
        if self.pac_dir != (0, 0):
            dx, dy = self.pac_dir
            new_x = self.pac_x + dx * self.pac_speed * dt
            new_y = self.pac_y + dy * self.pac_speed * dt

            new_tile_x = int(round(new_x))
            new_tile_y = int(round(new_y))

            ahead_tile_x = int(new_x + dx * 0.5)
            ahead_tile_y = int(new_y + dy * 0.5)

            if not self.tile_passable(new_tile_x, new_tile_y, is_ghost=False):
                self.pac_x = float(cur_tile_x)
                self.pac_y = float(cur_tile_y)
            elif not self.tile_passable(ahead_tile_x, ahead_tile_y, is_ghost=False):
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
                self.pac_x = new_x
                self.pac_y = new_y

        # Tunnel wrap
        if self.pac_x < 0:
            self.pac_x = self.maze_width - 1.0
        elif self.pac_x >= self.maze_width:
            self.pac_x = 0.0

    def move_ghost(self, ghost, dt: float):
        """Move ghost with AI - semi-random at intersections."""
        if ghost['in_house']:
            ghost['y'] += ghost['dir'][1] * 1.5 * dt
            if ghost['y'] < 9.0:
                ghost['dir'] = (0, 1)
            elif ghost['y'] > 10.5:
                ghost['dir'] = (0, -1)
            return

        # Safety: teleport home if eaten ghost is stuck too long
        if ghost['eaten']:
            ghost['eaten_timer'] = ghost.get('eaten_timer', 0) + dt
            if ghost['eaten_timer'] > 15.0:
                self._return_ghost_home(ghost)
                return

        # Determine speed
        if ghost['eaten']:
            speed = self.ghost_speed * 2
        elif ghost['frightened']:
            speed = self.frightened_speed
        else:
            speed = self.ghost_speed

        gx, gy = ghost['x'], ghost['y']
        tile_x, tile_y = int(round(gx)), int(round(gy))

        at_center = abs(gx - tile_x) < 0.1 and abs(gy - tile_y) < 0.1

        if at_center:
            ghost['x'] = float(tile_x)
            ghost['y'] = float(tile_y)
            gx, gy = ghost['x'], ghost['y']

            # Check for eaten ghost reaching home
            if ghost['eaten']:
                if tile_x == 10 and tile_y == 8:
                    self._return_ghost_home(ghost)
                    return

            # Find valid directions
            possible = []
            reverse = (-ghost['dir'][0], -ghost['dir'][1])

            for d in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                next_x = tile_x + d[0]
                next_y = tile_y + d[1]
                if self.tile_passable(next_x, next_y, is_ghost=True):
                    if d != reverse or ghost['frightened'] or ghost['eaten']:
                        possible.append(d)

            if not possible:
                for d in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                    next_x = tile_x + d[0]
                    next_y = tile_y + d[1]
                    if self.tile_passable(next_x, next_y, is_ghost=True):
                        possible.append(d)

            # Choose direction - semi-random AI
            if possible:
                if ghost['frightened'] and not ghost['eaten']:
                    ghost['dir'] = random.choice(possible)
                elif not ghost['eaten'] and len(possible) >= 3 and random.random() < 0.25:
                    # Ms. Pac-Man: 25% chance of random turn at intersections
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

            check_x = int(round(new_x + dx * 0.4))
            check_y = int(round(new_y + dy * 0.4))

            if self.tile_passable(check_x, check_y, is_ghost=True):
                ghost['x'] = new_x
                ghost['y'] = new_y
            else:
                ghost['x'] = round(ghost['x'])
                ghost['y'] = round(ghost['y'])

        # Tunnel wrap
        if ghost['x'] < 0:
            ghost['x'] = self.maze_width - 1.0
        elif ghost['x'] >= self.maze_width:
            ghost['x'] = 0.0

        # Eaten ghost: proximity catch for door
        if ghost['eaten']:
            if abs(ghost['x'] - 10.0) < 0.5 and abs(ghost['y'] - 8.0) < 0.5:
                self._return_ghost_home(ghost)
                return

    def _return_ghost_home(self, ghost):
        """Return an eaten ghost to the house."""
        ghost['eaten'] = False
        ghost['frightened'] = False
        ghost['in_house'] = True
        ghost['x'] = 10.0
        ghost['y'] = 9.5
        ghost['dir'] = (0, 1)
        self.ghosts_released -= 1

    def get_ghost_target(self, ghost):
        """Get target tile for ghost AI."""
        if ghost['eaten']:
            return (10.0, 8.0)

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

    def _get_frightened_duration(self):
        """Get frightened duration based on level."""
        frightened_table = {
            1: 6.0, 2: 5.0, 3: 4.0, 4: 3.0, 5: 2.0,
            6: 5.0, 7: 4.0, 8: 3.0, 9: 1.0, 10: 5.0,
            11: 2.0, 12: 1.0, 13: 1.0, 14: 3.0, 15: 1.0,
            16: 1.0, 17: 0.0, 18: 1.0,
        }
        if self.level >= 19:
            return 0.0
        return frightened_table.get(self.level, 6.0)

    def _get_ghost_speed_multiplier(self):
        """Get ghost speed multiplier based on level."""
        multiplier = 1.0 + (self.level - 1) * 0.05
        return min(multiplier, 1.4)

    def _get_ghost_release_interval(self):
        """Get interval between ghost releases from the pen."""
        interval = 4.0 - (self.level - 1) * 0.3
        return max(interval, 1.0)

    def _apply_level_difficulty(self):
        """Apply difficulty settings based on current level."""
        speed_mult = self._get_ghost_speed_multiplier()
        self.ghost_speed = self.base_ghost_speed * speed_mult
        self.frightened_speed = self.base_frightened_speed * speed_mult

    def activate_power(self):
        """Activate power pellet effect."""
        frightened_duration = self._get_frightened_duration()
        self.frightened_timer = frightened_duration
        self.ghost_points = 200

        if frightened_duration > 0:
            for ghost in self.ghosts:
                if not ghost['eaten'] and not ghost['in_house']:
                    ghost['frightened'] = True
                    ghost['dir'] = (-ghost['dir'][0], -ghost['dir'][1])

    def respawn(self):
        """Respawn Pac-Man after death."""
        self.pac_x = 10.0
        self.pac_y = 14.0
        self.pac_dir = (0, 0)
        self.pac_next_dir = (0, 0)

        # Reset ghosts
        self.ghosts[0]['x'], self.ghosts[0]['y'] = 10.0, 7.0
        self.ghosts[0]['in_house'] = False
        self.ghosts[0]['dir'] = (-1, 0)
        self.ghosts[1]['x'], self.ghosts[1]['y'] = 10.0, 9.0
        self.ghosts[1]['in_house'] = True
        self.ghosts[2]['x'], self.ghosts[2]['y'] = 9.0, 10.0
        self.ghosts[2]['in_house'] = True
        self.ghosts[3]['x'], self.ghosts[3]['y'] = 11.0, 10.0
        self.ghosts[3]['in_house'] = True

        for ghost in self.ghosts:
            ghost['frightened'] = False
            ghost['eaten'] = False

        self.ghosts_released = 1
        self.ghost_release_timer = 0
        self.frightened_timer = 0

        # Deactivate fruit on death
        self.fruit['active'] = False

    def next_level(self):
        """Start next level with new maze."""
        self._load_maze(self._get_maze_index())
        self.respawn()
        self._apply_level_difficulty()

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Draw HUD
        self.display.draw_text_small(1, 1, f"{self.score}", Colors.WHITE)

        # Draw lives (with bow on each life icon)
        for i in range(self.lives - 1):
            lx = 50 + i * 5
            # Yellow body
            self.display.set_pixel(lx, 2, Colors.YELLOW)
            self.display.set_pixel(lx + 1, 2, Colors.YELLOW)
            self.display.set_pixel(lx, 3, Colors.YELLOW)
            self.display.set_pixel(lx + 1, 3, Colors.YELLOW)
            # Pink bow on top
            self.display.set_pixel(lx, 1, (255, 50, 100))

        # Draw maze
        for ty in range(self.maze_height):
            for tx in range(self.maze_width):
                px = self.offset_x + tx * self.tile_size
                py = self.offset_y + ty * self.tile_size
                tile = self.maze[ty][tx]

                if tile == 1:  # Wall - use per-maze color
                    for dx in range(self.tile_size):
                        for dy in range(self.tile_size):
                            self.display.set_pixel(px + dx, py + dy, self.wall_color)
                elif tile == 4:  # Ghost house door
                    self.display.set_pixel(px + 1, py + 1, Colors.PINK)
                elif tile == 2:  # Dot
                    self.display.set_pixel(px + 1, py + 1, (255, 255, 200))
                elif tile == 3:  # Power pellet (flashing)
                    if int(self.pellet_flash * 4) % 2 == 0:
                        for dx in range(2):
                            for dy in range(2):
                                self.display.set_pixel(px + dx, py + dy, (255, 255, 200))

        # Draw fruit
        if self.fruit['active']:
            _, color, _ = self.FRUIT_TYPES[self.fruit['type']]
            fx = self.offset_x + int(self.fruit['x'] * self.tile_size) + 1
            fy = self.offset_y + int(self.fruit['y'] * self.tile_size) + 1
            self.display.set_pixel(fx, fy, color)
            self.display.set_pixel(fx + 1, fy, color)
            self.display.set_pixel(fx, fy + 1, color)
            self.display.set_pixel(fx + 1, fy + 1, color)

        # Draw fruit score popup
        if self.fruit_score_timer > 0:
            self.display.draw_text_small(1, 1, f"{self.score}", Colors.WHITE)

        # Draw ghosts (2x2)
        for ghost in self.ghosts:
            gx = self.offset_x + int(ghost['x'] * self.tile_size) + 1
            gy = self.offset_y + int(ghost['y'] * self.tile_size) + 1

            if ghost['eaten']:
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

        # Draw Ms. Pac-Man (2x2 yellow with bow)
        px = self.offset_x + int(self.pac_x * self.tile_size) + 1
        py = self.offset_y + int(self.pac_y * self.tile_size) + 1

        self.display.set_pixel(px, py, Colors.YELLOW)
        self.display.set_pixel(px + 1, py, Colors.YELLOW)
        self.display.set_pixel(px, py + 1, Colors.YELLOW)
        self.display.set_pixel(px + 1, py + 1, Colors.YELLOW)

        # Bow - pink pixel positioned based on facing direction
        bow_color = (255, 50, 100)
        if self.pac_dir == (1, 0):  # Facing right - bow on top-left
            self.display.set_pixel(px, py - 1, bow_color)
        elif self.pac_dir == (-1, 0):  # Facing left - bow on top-right
            self.display.set_pixel(px + 1, py - 1, bow_color)
        elif self.pac_dir == (0, -1):  # Facing up - bow on right
            self.display.set_pixel(px + 2, py, bow_color)
        elif self.pac_dir == (0, 1):  # Facing down - bow on right
            self.display.set_pixel(px + 2, py, bow_color)
        else:  # Stationary - bow on top
            self.display.set_pixel(px, py - 1, bow_color)

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
        self.display.draw_text_small(4, 50, "BTN:RETRY", Colors.GRAY)
