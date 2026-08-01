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
    GUIDE = {
        'desc': 'Eat all dots while avoiding ghosts. Faster than PAK-MAN with multiple mazes; Blinky and Pinky roam unpredictably early in each level. Grab the bouncing fruit before it escapes out a tunnel. Extra life at 10,000 points.',
    }

    # 4 cycling maze layouts (21x19 tiles at 3px each = 63x57)
    # 0=empty, 1=wall, 2=dot, 3=power pellet, 4=ghost house door
    # Inspired by original Ms. Pac-Man arcade mazes with wide corridors.
    # Every row is a palindrome. No dead ends. Two tunnels per maze.
    MAZES = [
        {
            # Maze 1 (Hot Pink): Tunnels at R3, R9
            # Edge blocks + big center block. 1-wide corridors throughout.
            'template': [
                "111111111111111111111",  # R0
                "122222222222222222221",  # R1  highway
                "121112121212121211121",  # R2  edge blocks + alternating
                "031112121212121211130",  # R3  tunnel + pellets
                "122222222222222222221",  # R4  highway
                "121212111111111212121",  # R5  big 9-wide center block
                "121212111111111212121",  # R6  2-tall
                "122222222222222222221",  # R7  highway
                "121212121141121212121",  # R8  ghost house
                "021212121000121212120",  # R9  tunnel + ghost house
                "121212121000121212121",  # R10 ghost house
                "121212121111121212121",  # R11 ghost house bottom
                "122222222222222222221",  # R12 highway
                "121111121212121111121",  # R13 big edge blocks
                "122222222222222222221",  # R14 highway
                "131212111212111212131",  # R15 center blocks + pellets
                "121212111212111212121",  # R16 center blocks
                "122222222222222222221",  # R17 highway
                "111111111111111111111",  # R18
            ],
            'wall_color': (255, 105, 180),  # Hot pink
            'tunnel_rows': [3, 9],
        },
        {
            # Maze 2 (Cyan): Tunnels at R9, R15
            # Mixed blocks + twin blocks + large center. 1-wide corridors.
            'template': [
                "111111111111111111111",  # R0
                "132222222222222222231",  # R1  highway + pellets
                "121112112121211211121",  # R2  mixed blocks
                "121112112121211211121",  # R3  2-tall
                "122222222222222222221",  # R4  highway
                "121121111121111121121",  # R5  twin 5-wide blocks
                "121121111121111121121",  # R6  2-tall
                "122222222222222222221",  # R7  highway
                "121212121141121212121",  # R8  ghost house
                "021212121000121212120",  # R9  tunnel + ghost house
                "121212121000121212121",  # R10 ghost house
                "121212121111121212121",  # R11 ghost house bottom
                "122222222222222222221",  # R12 highway
                "121112111111111211121",  # R13 big 9-wide center block
                "122222222222222222221",  # R14 highway
                "031121111121111121130",  # R15 tunnel + twin blocks + pellets
                "121121111121111121121",  # R16 twin blocks
                "122222222222222222221",  # R17 highway
                "111111111111111111111",  # R18
            ],
            'wall_color': (0, 255, 255),  # Cyan
            'tunnel_rows': [9, 15],
        },
        {
            # Maze 3 (Brown/Orange): Tunnels at R3, R9
            # Center 3-wide blocks + edge blocks. 1-wide corridors.
            'template': [
                "111111111111111111111",  # R0
                "132222222222222222231",  # R1  highway + pellets
                "121212111212111212121",  # R2  center 3-wide blocks
                "021212111212111212120",  # R3  tunnel
                "122222222222222222221",  # R4  highway
                "121111211212112111121",  # R5  big edge blocks
                "121111211212112111121",  # R6  2-tall
                "122222222222222222221",  # R7  highway
                "121212121141121212121",  # R8  ghost house
                "021212121000121212120",  # R9  tunnel + ghost house
                "121212121000121212121",  # R10 ghost house
                "121212121111121212121",  # R11 ghost house bottom
                "122222222222222222221",  # R12 highway
                "121211121212121112121",  # R13 twin 3-wide blocks
                "122222222222222222221",  # R14 highway
                "131212111212111212131",  # R15 center blocks + pellets
                "121212111212111212121",  # R16 center blocks
                "122222222222222222221",  # R17 highway
                "111111111111111111111",  # R18
            ],
            'wall_color': (180, 100, 50),  # Brown/orange
            'tunnel_rows': [3, 9],
        },
        {
            # Maze 4 (Blue): Tunnels at R9, R15
            # Pac-Man-familiar blocks rearranged. 1-wide corridors.
            'template': [
                "111111111111111111111",  # R0
                "122222222222222222221",  # R1  highway
                "121211212111212112121",  # R2  scattered blocks
                "131211212111212112131",  # R3  pellets
                "122222222222222222221",  # R4  highway
                "121112121212121211121",  # R5  edge + alternating
                "121112121212121211121",  # R6  2-tall
                "122222222222222222221",  # R7  highway
                "121212121141121212121",  # R8  ghost house
                "021212121000121212120",  # R9  tunnel + ghost house
                "121212121000121212121",  # R10 ghost house
                "121212121111121212121",  # R11 ghost house bottom
                "122222222222222222221",  # R12 highway
                "121112111212111211121",  # R13 classic blocks
                "122222222222222222221",  # R14 highway
                "031211212111212112130",  # R15 tunnel + pellets
                "121211212111212112121",  # R16 scattered blocks
                "122222222222222222221",  # R17 highway
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

    # Scatter/chase phase durations in seconds (as in Pac-Man).
    # Even indices are scatter, odd are chase; the final chase never ends.
    # Levels 5+ shorten scatter phases to 5 seconds.
    MODE_SCHEDULE = [7.0, 20.0, 7.0, 20.0, 5.0, 20.0, 5.0, float('inf')]

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
        self.pac_speed = 6.6  # Tiles per second - faster than Pac-Man's 6.0
        self.pac_slow_timer = 0  # Brief slowdown after eating a dot
        self.mouth_open = True
        self.mouth_timer = 0

        # Ghosts - positioned in/around ghost house (rows 8-11)
        # The orange ghost is Sue in Ms. Pac-Man (Clyde's AI, new name)
        self.ghosts = [
            {'name': 'blinky', 'x': 10.0, 'y': 7.0, 'dir': (-1, 0), 'color': Colors.RED,
             'scatter_target': (19, 1), 'in_house': False, 'frightened': False, 'eaten': False,
             'dot_counter': 0},
            {'name': 'pinky', 'x': 10.0, 'y': 9.0, 'dir': (0, 1), 'color': Colors.PINK,
             'scatter_target': (1, 1), 'in_house': True, 'frightened': False, 'eaten': False,
             'dot_counter': 0},
            {'name': 'inky', 'x': 9.0, 'y': 10.0, 'dir': (0, -1), 'color': Colors.CYAN,
             'scatter_target': (19, 17), 'in_house': True, 'frightened': False, 'eaten': False,
             'dot_counter': 0},
            {'name': 'sue', 'x': 11.0, 'y': 10.0, 'dir': (0, -1), 'color': Colors.ORANGE,
             'scatter_target': (1, 17), 'in_house': True, 'frightened': False, 'eaten': False,
             'dot_counter': 0},
        ]
        # Base speeds (will be modified by level)
        self.base_ghost_speed = 4.5
        self.base_frightened_speed = 3.0
        self.ghost_speed = self.base_ghost_speed
        self.frightened_speed = self.base_frightened_speed
        self.frightened_timer = 0
        self.ghost_release_timer = 0  # Time since last dot eaten (no-dot fallback release)
        self.ghosts_released = 1  # Blinky starts outside

        # Level-based difficulty settings
        self._apply_level_difficulty()

        # Mode switching (scatter/chase) - arcade phase schedule, starts in scatter
        self.mode_phase = 0
        self.mode_timer = 0
        self.chase_mode = False

        # Power pellet flashing
        self.pellet_flash = 0

        # Eaten ghost points
        self.ghost_points = 200

        # One extra life awarded at 10,000 points
        self.extra_life_awarded = False

        # Fruit state
        self.fruit = {'active': False, 'x': 0.0, 'y': 0.0,
                      'dir': (1, 0), 'type': 0, 'timer': 0.0, 'leaving': False}
        self.fruit_score_display = 0
        self.fruit_score_timer = 0.0
        self.fruit_score_pos = (0.0, 0.0)

    def _get_maze_index(self):
        """Get maze index based on current level (arcade banding)."""
        level = self.level
        if level <= 2:
            return 0
        elif level <= 5:
            return 1
        elif level <= 9:
            return 2
        elif level <= 13:
            return 3
        else:
            return 2 + (((level - 14) // 4) % 2)  # Alternate mazes 3 & 4 every 4 levels

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
                      'dir': (1, 0), 'type': 0, 'timer': 0.0, 'leaving': False}

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

        # Advance scatter/chase phase (timer pauses while ghosts are frightened)
        if self.frightened_timer <= 0 and self.mode_phase < len(self.MODE_SCHEDULE) - 1:
            self.mode_timer += dt
            if self.mode_timer >= self._mode_phase_duration(self.mode_phase):
                self.mode_timer = 0
                self.mode_phase += 1
                self.chase_mode = (self.mode_phase % 2 == 1)
                # Mode flips force ghosts to reverse direction
                for ghost in self.ghosts:
                    if not ghost['eaten'] and not ghost['in_house']:
                        ghost['dir'] = (-ghost['dir'][0], -ghost['dir'][1])

        # Update frightened timer
        if self.frightened_timer > 0:
            self.frightened_timer -= dt
            if self.frightened_timer <= 0:
                for ghost in self.ghosts:
                    ghost['frightened'] = False
                self.ghost_points = 200

        # Dot slowdown wears off
        if self.pac_slow_timer > 0:
            self.pac_slow_timer -= dt

        # Dot-counter house exits (house order: Pinky, Inky, Sue)
        if self.ghosts_released < 4:
            for ghost in self.ghosts:
                if ghost['in_house']:
                    if ghost['dot_counter'] >= self._ghost_dot_limit(ghost['name']):
                        self._release_next_ghost()
                    break
            # Fallback: if no dot eaten for 4 seconds, release the next ghost anyway
            self.ghost_release_timer += dt
            if self.ghost_release_timer >= 4.0:
                self._release_next_ghost()

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
                self.pac_slow_timer = 0.05  # Chewing slows her briefly
                self._count_dot_for_house()
                self._check_fruit_spawn()
            elif tile == 3:  # Power pellet
                self.maze[ty][tx] = 0
                self.score += 50
                self.dots_remaining -= 1
                self.dots_eaten += 1
                self.pac_slow_timer = 0.15
                self._count_dot_for_house()
                self.activate_power()
                self._check_fruit_spawn()

        # Extra life at 10,000 points (awarded once)
        if not self.extra_life_awarded and self.score >= 10000:
            self.extra_life_awarded = True
            self.lives += 1

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
        """Spawn fruit at the arcade dot counts (70 and 170 of 244, scaled to our maze)."""
        if self.fruit_spawned_count >= 2 or self.fruit['active']:
            return
        if self.fruit_spawned_count == 0 and self.dots_eaten >= self.dots_total * 70 // 244:
            self._spawn_fruit()
        elif self.fruit_spawned_count == 1 and self.dots_eaten >= self.dots_total * 170 // 244:
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
        # Fruit type based on level; levels 8+ draw randomly from the full table
        if self.level >= 8:
            fruit_idx = random.randint(0, len(self.FRUIT_TYPES) - 1)
        else:
            fruit_idx = min(self.level - 1, len(self.FRUIT_TYPES) - 1)
        self.fruit = {
            'active': True,
            'x': x,
            'y': float(row),
            'dir': d,
            'type': fruit_idx,
            'timer': 10.0,  # 10 seconds before it heads for an exit
            'leaving': False,
        }

    def _move_fruit(self, dt):
        """Move the bouncing fruit through the maze."""
        if not self.fruit['active']:
            return

        self.fruit['timer'] -= dt
        if self.fruit['timer'] <= 0:
            # Time's up: head for the nearest tunnel and leave (still edible en route)
            self.fruit['leaving'] = True

        # Move at 75% of Pac-Man speed
        speed = self.pac_speed * 0.75
        fx, fy = self.fruit['x'], self.fruit['y']
        tile_x, tile_y = int(round(fx)), int(round(fy))

        # At tile center, pick a new direction (once per tile — re-snapping
        # every frame stalls the fruit when the per-frame step is < 0.1)
        at_center = abs(fx - tile_x) < 0.1 and abs(fy - tile_y) < 0.1
        if at_center and self.fruit.get('decided_tile') != (tile_x, tile_y):
            self.fruit['decided_tile'] = (tile_x, tile_y)
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
                if self.fruit['leaving']:
                    # Steer toward the nearest tunnel mouth
                    target = self._fruit_exit_target()
                    best_dir = possible[0]
                    best_dist = float('inf')
                    for d in possible:
                        nx = tile_x + d[0]
                        ny = tile_y + d[1]
                        dist = (nx - target[0])**2 + (ny - target[1])**2
                        if dist < best_dist:
                            best_dist = dist
                            best_dir = d
                    self.fruit['dir'] = best_dir
                else:
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

        # Tunnel wrap - a leaving fruit exits the maze instead
        if self.fruit['x'] < 0 or self.fruit['x'] >= self.maze_width:
            if self.fruit['leaving']:
                self.fruit['active'] = False
            elif self.fruit['x'] < 0:
                self.fruit['x'] = self.maze_width - 1.0
            else:
                self.fruit['x'] = 0.0

    def _fruit_exit_target(self):
        """Nearest tunnel mouth for a departing fruit (just outside the maze)."""
        fy = self.fruit['y']
        row = min(self.tunnel_rows, key=lambda r: abs(r - fy))
        x = -1 if self.fruit['x'] < self.maze_width / 2 else self.maze_width
        return (x, row)

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
            self.fruit_score_pos = (self.fruit['x'], self.fruit['y'])
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

        # Move in current direction (slower for a moment after eating a dot)
        if self.pac_dir != (0, 0):
            dx, dy = self.pac_dir
            speed = self.pac_speed * (0.8 if self.pac_slow_timer > 0 else 1.0)
            new_x = self.pac_x + dx * speed * dt
            new_y = self.pac_y + dy * speed * dt

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
        """Move ghost with AI."""
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
            # Cruise Elroy: Blinky speeds up as the dots run out
            if ghost['name'] == 'blinky':
                if self.dots_remaining <= self._elroy_threshold() // 2:
                    speed *= 1.10
                elif self.dots_remaining <= self._elroy_threshold():
                    speed *= 1.05

        gx, gy = ghost['x'], ghost['y']
        tile_x, tile_y = int(round(gx)), int(round(gy))

        # Ghosts slow down in the tunnel mouths
        if not ghost['eaten'] and tile_y in self.tunnel_rows and (tile_x <= 2 or tile_x >= 18):
            speed *= 0.55

        # Decide only once per tile: at slow speeds (tunnel/frightened) the
        # per-frame step is smaller than the snap window, and re-snapping
        # every frame stalls the ghost on the tile center forever.
        at_center = abs(gx - tile_x) < 0.1 and abs(gy - tile_y) < 0.1

        if at_center and ghost.get('decided_tile') != (tile_x, tile_y):
            ghost['decided_tile'] = (tile_x, tile_y)
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
                    if d != reverse or ghost['eaten']:
                        possible.append(d)

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

            check_x = int(round(new_x + dx * 0.4))
            check_y = int(round(new_y + dy * 0.4))

            if self.tile_passable(check_x, check_y, is_ghost=True):
                ghost['x'] = new_x
                ghost['y'] = new_y
            else:
                # Stop at tile center; re-decide next frame
                ghost['x'] = round(ghost['x'])
                ghost['y'] = round(ghost['y'])
                ghost['decided_tile'] = None

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

        name = ghost['name']
        if not self.chase_mode:
            # Cruise Elroy Blinky ignores scatter and keeps chasing
            if name == 'blinky' and self.dots_remaining <= self._elroy_threshold():
                return (self.pac_x, self.pac_y)
            # Ms. Pac-Man: during the first two scatters of a level, Blinky and
            # Pinky roam to pseudo-random tiles instead of their corners
            if self.mode_phase <= 2 and name in ('blinky', 'pinky'):
                tgt = ghost.get('random_target')
                if tgt is None or (abs(ghost['x'] - tgt[0]) < 1.5 and
                                   abs(ghost['y'] - tgt[1]) < 1.5):
                    tgt = self._random_roam_target()
                    ghost['random_target'] = tgt
                return tgt
            return ghost['scatter_target']

        if name == 'blinky':
            return (self.pac_x, self.pac_y)
        elif name == 'pinky':
            # Pac-Man's overflow bug survives here: facing up also shifts 4 left
            if self.pac_dir == (0, -1):
                return (self.pac_x - 4, self.pac_y - 4)
            return (self.pac_x + self.pac_dir[0] * 4, self.pac_y + self.pac_dir[1] * 4)
        elif name == 'inky':
            # Inky's overflow bug was fixed in Ms. Pac-Man - pivot is straight up
            px = self.pac_x + self.pac_dir[0] * 2
            py = self.pac_y + self.pac_dir[1] * 2
            blinky = self.ghosts[0]
            return (px + (px - blinky['x']), py + (py - blinky['y']))
        elif name == 'sue':
            dist = math.sqrt((self.pac_x - ghost['x'])**2 + (self.pac_y - ghost['y'])**2)
            if dist > 8:
                return (self.pac_x, self.pac_y)
            else:
                return ghost['scatter_target']

        return (self.pac_x, self.pac_y)

    def _random_roam_target(self):
        """Pick a random passable tile for a roaming scatter ghost."""
        while True:
            tx = random.randint(1, self.maze_width - 2)
            ty = random.randint(1, self.maze_height - 2)
            if self.maze[ty][tx] != 1 and self.maze[ty][tx] != 4:
                return (tx, ty)

    def _get_frightened_duration(self):
        """Get frightened duration based on level (~20% shorter than PAK-MAN's)."""
        frightened_table = {
            1: 4.8, 2: 4.0, 3: 3.2, 4: 2.4, 5: 1.6,
            6: 4.0, 7: 3.2, 8: 2.4, 9: 0.8, 10: 4.0,
            11: 1.6, 12: 0.8, 13: 0.8, 14: 2.4, 15: 0.8,
            16: 0.8, 17: 0.0, 18: 0.8,
        }
        if self.level >= 19:
            return 0.0
        return frightened_table.get(self.level, 4.8)

    def _get_ghost_speed_multiplier(self):
        """Get ghost speed multiplier based on level."""
        multiplier = 1.0 + (self.level - 1) * 0.05
        return min(multiplier, 1.4)

    def _mode_phase_duration(self, phase):
        """Duration of a scatter/chase phase; levels 5+ shorten scatters to 5s."""
        duration = self.MODE_SCHEDULE[phase]
        if self.level >= 5 and phase % 2 == 0:
            return min(duration, 5.0)
        return duration

    def _elroy_threshold(self):
        """Dots-remaining count at which Blinky becomes 'Cruise Elroy'."""
        return min(20 + (self.level - 1) * 10, self.dots_total // 3)

    def _ghost_dot_limit(self, name):
        """Personal dot-counter limit before a ghost leaves the house."""
        if name == 'inky':
            return 30 if self.level == 1 else 0
        if name == 'sue':
            if self.level == 1:
                return 60
            if self.level == 2:
                return 50
            return 0
        return 0  # Pinky (and returned Blinky) leave immediately

    def _count_dot_for_house(self):
        """Credit an eaten dot to the preferred waiting ghost's counter."""
        self.ghost_release_timer = 0
        for ghost in self.ghosts:
            if ghost['in_house']:
                ghost['dot_counter'] += 1
                break

    def _release_next_ghost(self):
        """Release the next waiting ghost (house order: Pinky, Inky, Sue)."""
        for ghost in self.ghosts:
            if ghost['in_house']:
                ghost['in_house'] = False
                ghost['x'] = 10.0  # Exit through door
                ghost['y'] = 7.0
                ghost['dir'] = (-1, 0)
                self.ghosts_released += 1
                self.ghost_release_timer = 0
                return

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
            ghost['dot_counter'] = 0
            ghost['random_target'] = None

        self.ghosts_released = 1
        self.ghost_release_timer = 0
        self.frightened_timer = 0

        # Scatter/chase schedule restarts on death and new level
        self.mode_phase = 0
        self.mode_timer = 0
        self.chase_mode = False

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

        # Draw fruit score popup - point value near where the fruit was eaten
        if self.fruit_score_timer > 0:
            text = f"{self.fruit_score_display}"
            sx = self.offset_x + int(self.fruit_score_pos[0] * self.tile_size) - 2
            sy = self.offset_y + int(self.fruit_score_pos[1] * self.tile_size) - 4
            sx = max(1, min(sx, 63 - len(text) * 4))
            sy = max(self.offset_y, min(sy, 58))
            self.display.draw_text_small(sx, sy, text, Colors.WHITE)

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
