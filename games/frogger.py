"""
Frogger - Cross the road and river
==================================
Cross 5 lanes of traffic, then hop across logs and turtles to reach home.
Fill all 5 home slots to complete the level.

Controls:
  Arrow Keys - Hop one cell in direction
  Escape     - Return to menu
"""

import random
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


class Frogger(Game):
    name = "FROGGER"
    description = "Cross the road and river!"
    category = "arcade"

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0
        self.lives = 3
        self.level = 1

        # Grid dimensions (4x4 pixel cells)
        self.cell_size = 4
        self.cols = 16  # 64 / 4
        self.rows = 14  # Usable rows (leaving HUD at top)

        # Row types from bottom to top:
        # Row 0: Start (grass)
        # Rows 1-5: Road (traffic)
        # Row 6: Safe zone (grass)
        # Rows 7-11: River (logs/turtles)
        # Row 12: Home slots
        # Row 13: Top edge (HUD takes row 13+)

        # Frog position (grid coordinates)
        self.frog_col = 7
        self.frog_row = 0
        self.frog_riding = None  # Reference to log/turtle if riding

        # Movement input cooldown
        self.move_cooldown = 0
        self.move_delay = 0.12

        # Home slots (5 slots to fill)
        self.homes = [False, False, False, False, False]
        self.home_positions = [1, 4, 7, 10, 13]  # Column positions

        # Traffic lanes (row 1-5)
        self.cars = []
        self.setup_traffic()

        # Water objects (row 7-11)
        self.logs = []
        self.turtles = []
        self.setup_water()

        # Timer
        self.time_left = 30.0
        self.timer_warning = False

        # Death animation
        self.dying = False
        self.death_timer = 0

    def setup_traffic(self):
        """Initialize car lanes."""
        self.cars = []

        # Each lane has cars moving in one direction at a speed
        lane_configs = [
            # (row, direction, speed, car_length, gap)
            (1, 1, 15, 2, 8),    # Slow cars right
            (2, -1, 20, 2, 6),   # Medium cars left
            (3, 1, 25, 3, 7),    # Trucks right
            (4, -1, 18, 2, 5),   # Cars left
            (5, 1, 30, 2, 6),    # Fast cars right
        ]

        for row, direction, speed, length, gap in lane_configs:
            # Spawn cars evenly spaced
            num_cars = self.cols // (length + gap) + 2
            for i in range(num_cars):
                x = (i * (length + gap)) % (self.cols + length * 2) - length
                self.cars.append({
                    'row': row,
                    'x': float(x * self.cell_size),
                    'length': length,
                    'speed': speed * direction * (1 + self.level * 0.1),
                    'color': random.choice([Colors.RED, Colors.YELLOW, Colors.MAGENTA, Colors.CYAN])
                })

    def setup_water(self):
        """Initialize logs and turtles."""
        self.logs = []
        self.turtles = []

        # Water lane configs
        water_configs = [
            # (row, type, direction, speed, length, gap)
            (7, 'turtle', -1, 12, 3, 4),   # Turtles left
            (8, 'log', 1, 18, 4, 5),       # Short logs right
            (9, 'log', -1, 15, 5, 4),      # Medium logs left
            (10, 'turtle', 1, 14, 3, 5),   # Turtles right
            (11, 'log', -1, 20, 6, 6),     # Long logs left
        ]

        for row, obj_type, direction, speed, length, gap in water_configs:
            num_objs = self.cols // (length + gap) + 2

            for i in range(num_objs):
                x = (i * (length + gap)) % (self.cols + length * 2) - length

                obj = {
                    'row': row,
                    'x': float(x * self.cell_size),
                    'length': length,
                    'speed': speed * direction * (1 + self.level * 0.1),
                }

                if obj_type == 'turtle':
                    obj['diving'] = False
                    obj['dive_timer'] = random.uniform(3, 8)
                    self.turtles.append(obj)
                else:
                    self.logs.append(obj)

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        # Death animation
        if self.dying:
            self.death_timer -= dt
            if self.death_timer <= 0:
                self.dying = False
                self.respawn()
            return

        # Movement cooldown
        self.move_cooldown -= dt

        # Handle movement
        if self.move_cooldown <= 0:
            moved = False
            new_col, new_row = self.frog_col, self.frog_row

            if input_state.up:
                new_row = min(self.rows - 2, self.frog_row + 1)
                moved = True
            elif input_state.down:
                new_row = max(0, self.frog_row - 1)
                moved = True
            elif input_state.left:
                new_col = max(0, self.frog_col - 1)
                moved = True
            elif input_state.right:
                new_col = min(self.cols - 1, self.frog_col + 1)
                moved = True

            if moved:
                self.frog_col = new_col
                self.frog_row = new_row
                self.move_cooldown = self.move_delay
                self.frog_riding = None

                # Score for moving forward
                if new_row > self.frog_row:
                    self.score += 10

        # Update timer
        self.time_left -= dt
        self.timer_warning = self.time_left < 10
        if self.time_left <= 0:
            self.die()
            return

        # Move cars
        for car in self.cars:
            car['x'] += car['speed'] * dt
            # Wrap around
            if car['speed'] > 0 and car['x'] > GRID_SIZE:
                car['x'] = -car['length'] * self.cell_size
            elif car['speed'] < 0 and car['x'] < -car['length'] * self.cell_size:
                car['x'] = GRID_SIZE

        # Move logs
        for log in self.logs:
            log['x'] += log['speed'] * dt
            if log['speed'] > 0 and log['x'] > GRID_SIZE:
                log['x'] = -log['length'] * self.cell_size
            elif log['speed'] < 0 and log['x'] < -log['length'] * self.cell_size:
                log['x'] = GRID_SIZE

        # Move and update turtles
        for turtle in self.turtles:
            turtle['x'] += turtle['speed'] * dt
            if turtle['speed'] > 0 and turtle['x'] > GRID_SIZE:
                turtle['x'] = -turtle['length'] * self.cell_size
            elif turtle['speed'] < 0 and turtle['x'] < -turtle['length'] * self.cell_size:
                turtle['x'] = GRID_SIZE

            # Diving behavior
            turtle['dive_timer'] -= dt
            if turtle['dive_timer'] <= 0:
                turtle['diving'] = not turtle['diving']
                turtle['dive_timer'] = random.uniform(2, 5) if turtle['diving'] else random.uniform(3, 8)

        # Check collisions based on row
        frog_x = self.frog_col * self.cell_size
        frog_y = self.frog_row

        # Road collision (rows 1-5)
        if 1 <= frog_y <= 5:
            for car in self.cars:
                if car['row'] == frog_y:
                    car_left = car['x']
                    car_right = car['x'] + car['length'] * self.cell_size
                    frog_right = frog_x + self.cell_size

                    if frog_x < car_right and frog_right > car_left:
                        self.die()
                        return

        # Water collision (rows 7-11)
        elif 7 <= frog_y <= 11:
            on_platform = False

            # Check logs
            for log in self.logs:
                if log['row'] == frog_y:
                    log_left = log['x']
                    log_right = log['x'] + log['length'] * self.cell_size

                    if frog_x >= log_left - 2 and frog_x + self.cell_size <= log_right + 2:
                        on_platform = True
                        # Move with log
                        self.frog_col += log['speed'] * dt / self.cell_size
                        self.frog_riding = log
                        break

            # Check turtles
            if not on_platform:
                for turtle in self.turtles:
                    if turtle['row'] == frog_y and not turtle['diving']:
                        turtle_left = turtle['x']
                        turtle_right = turtle['x'] + turtle['length'] * self.cell_size

                        if frog_x >= turtle_left - 2 and frog_x + self.cell_size <= turtle_right + 2:
                            on_platform = True
                            self.frog_col += turtle['speed'] * dt / self.cell_size
                            self.frog_riding = turtle
                            break

            if not on_platform:
                self.die()
                return

            # Check if frog went off screen
            if self.frog_col < 0 or self.frog_col >= self.cols:
                self.die()
                return

        # Home slots (row 12)
        elif frog_y == 12:
            # Check if in a home slot
            reached_home = False
            for i, home_col in enumerate(self.home_positions):
                if abs(self.frog_col - home_col) <= 1 and not self.homes[i]:
                    self.homes[i] = True
                    self.score += 200 + int(self.time_left * 10)
                    reached_home = True

                    # Check if all homes filled
                    if all(self.homes):
                        self.level += 1
                        self.next_level()
                    else:
                        self.respawn()
                    break

            if not reached_home:
                # Hit edge between slots
                self.die()
                return

    def die(self):
        """Handle frog death."""
        self.lives -= 1
        if self.lives <= 0:
            self.state = GameState.GAME_OVER
        else:
            self.dying = True
            self.death_timer = 0.5

    def respawn(self):
        """Respawn frog at start."""
        self.frog_col = 7
        self.frog_row = 0
        self.frog_riding = None
        self.time_left = 30.0

    def next_level(self):
        """Start next level."""
        self.homes = [False, False, False, False, False]
        self.setup_traffic()
        self.setup_water()
        self.respawn()

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Calculate screen y for a row (bottom-up)
        def row_to_y(row):
            return GRID_SIZE - 8 - (row + 1) * self.cell_size

        # Draw safe zones (grass) - rows 0 and 6
        for row in [0, 6]:
            y = row_to_y(row)
            for x in range(GRID_SIZE):
                self.display.set_pixel(x, y, (0, 80, 0))
                self.display.set_pixel(x, y + 1, (0, 100, 0))
                self.display.set_pixel(x, y + 2, (0, 80, 0))
                self.display.set_pixel(x, y + 3, (0, 60, 0))

        # Draw road (dark gray) - rows 1-5
        for row in range(1, 6):
            y = row_to_y(row)
            for x in range(GRID_SIZE):
                self.display.set_pixel(x, y, (40, 40, 40))
                self.display.set_pixel(x, y + 1, (50, 50, 50))
                self.display.set_pixel(x, y + 2, (50, 50, 50))
                self.display.set_pixel(x, y + 3, (40, 40, 40))

        # Draw water (dark blue) - rows 7-11
        for row in range(7, 12):
            y = row_to_y(row)
            for x in range(GRID_SIZE):
                self.display.set_pixel(x, y, (0, 0, 60))
                self.display.set_pixel(x, y + 1, (0, 0, 80))
                self.display.set_pixel(x, y + 2, (0, 0, 80))
                self.display.set_pixel(x, y + 3, (0, 0, 60))

        # Draw home area - row 12
        y = row_to_y(12)
        for x in range(GRID_SIZE):
            self.display.set_pixel(x, y, (0, 60, 0))
            self.display.set_pixel(x, y + 1, (0, 60, 0))
            self.display.set_pixel(x, y + 2, (0, 60, 0))
            self.display.set_pixel(x, y + 3, (0, 60, 0))

        # Draw home slots
        for i, home_col in enumerate(self.home_positions):
            hx = home_col * self.cell_size
            hy = row_to_y(12)
            if self.homes[i]:
                # Filled home - draw frog
                self.display.draw_rect(hx, hy, 3, 3, Colors.GREEN)
            else:
                # Empty home slot
                self.display.draw_rect(hx, hy, 4, 4, (0, 100, 100), filled=False)

        # Draw cars
        for car in self.cars:
            cx = int(car['x'])
            cy = row_to_y(car['row'])
            for i in range(car['length'] * self.cell_size):
                if 0 <= cx + i < GRID_SIZE:
                    self.display.set_pixel(cx + i, cy, car['color'])
                    self.display.set_pixel(cx + i, cy + 1, car['color'])
                    self.display.set_pixel(cx + i, cy + 2, car['color'])

        # Draw logs
        for log in self.logs:
            lx = int(log['x'])
            ly = row_to_y(log['row'])
            for i in range(log['length'] * self.cell_size):
                if 0 <= lx + i < GRID_SIZE:
                    self.display.set_pixel(lx + i, ly, (139, 90, 43))
                    self.display.set_pixel(lx + i, ly + 1, (160, 100, 50))
                    self.display.set_pixel(lx + i, ly + 2, (160, 100, 50))
                    self.display.set_pixel(lx + i, ly + 3, (139, 90, 43))

        # Draw turtles
        for turtle in self.turtles:
            if not turtle['diving']:
                tx = int(turtle['x'])
                ty = row_to_y(turtle['row'])
                color = Colors.GREEN if not turtle['diving'] else (0, 100, 0)

                # Draw each turtle in the group
                for t in range(turtle['length']):
                    tsx = tx + t * self.cell_size
                    if 0 <= tsx < GRID_SIZE and tsx + 3 < GRID_SIZE:
                        # Turtle shell
                        self.display.set_pixel(tsx + 1, ty, color)
                        self.display.set_pixel(tsx, ty + 1, color)
                        self.display.set_pixel(tsx + 1, ty + 1, color)
                        self.display.set_pixel(tsx + 2, ty + 1, color)
                        self.display.set_pixel(tsx + 1, ty + 2, color)

        # Draw frog (3x3 green)
        if not self.dying:
            fx = int(self.frog_col) * self.cell_size
            fy = row_to_y(self.frog_row)
            # Body
            self.display.set_pixel(fx + 1, fy, Colors.LIME)
            self.display.set_pixel(fx, fy + 1, Colors.LIME)
            self.display.set_pixel(fx + 1, fy + 1, Colors.GREEN)
            self.display.set_pixel(fx + 2, fy + 1, Colors.LIME)
            self.display.set_pixel(fx, fy + 2, Colors.LIME)
            self.display.set_pixel(fx + 2, fy + 2, Colors.LIME)
            # Eyes
            self.display.set_pixel(fx, fy, Colors.WHITE)
            self.display.set_pixel(fx + 2, fy, Colors.WHITE)
        else:
            # Death animation - red X
            fx = int(self.frog_col) * self.cell_size
            fy = row_to_y(self.frog_row)
            self.display.set_pixel(fx, fy, Colors.RED)
            self.display.set_pixel(fx + 2, fy, Colors.RED)
            self.display.set_pixel(fx + 1, fy + 1, Colors.RED)
            self.display.set_pixel(fx, fy + 2, Colors.RED)
            self.display.set_pixel(fx + 2, fy + 2, Colors.RED)

        # HUD
        self.display.draw_line(0, 6, 63, 6, Colors.DARK_GRAY)
        self.display.draw_text_small(1, 1, f"{self.score}", Colors.WHITE)

        # Lives
        for i in range(self.lives):
            self.display.set_pixel(40 + i * 4, 2, Colors.GREEN)
            self.display.set_pixel(41 + i * 4, 2, Colors.GREEN)
            self.display.set_pixel(40 + i * 4, 3, Colors.GREEN)

        # Timer bar
        timer_width = int((self.time_left / 30.0) * 20)
        timer_color = Colors.RED if self.timer_warning else Colors.GREEN
        for x in range(timer_width):
            self.display.set_pixel(54 + x - 20, 4, timer_color)

    def draw_game_over(self):
        """Custom game over screen."""
        self.display.clear(Colors.BLACK)
        self.display.draw_text_small(8, 20, "GAME OVER", Colors.RED)
        self.display.draw_text_small(12, 32, f"SCORE:{self.score}", Colors.WHITE)
        self.display.draw_text_small(16, 40, f"LEVEL:{self.level}", Colors.GREEN)
        self.display.draw_text_small(4, 50, "SPACE:RETRY", Colors.GRAY)
