"""
Stick Runner - Endless rooftop runner
=====================================
Run across rooftops, jump between buildings of all shapes and sizes!

Controls:
  Space      - Jump
  Escape     - Return to menu
"""

import random
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


class StickRunner(Game):
    name = "STICKRUN"
    description = "Jump the rooftops!"
    category = "modern"

    # Physics constants
    GRAVITY = 180.0
    JUMP_VELOCITY = -70.0
    MAX_FALL_SPEED = 120.0

    # Game constants
    PLAYER_X = 15
    BASE_PLATFORM_Y = 44

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0

        self.player_y = float(self.BASE_PLATFORM_Y - 5)
        self.velocity_y = 0.0
        self.on_ground = False
        self.can_jump = True

        self.scroll_speed = 40.0
        self.scroll_x = 0.0

        # Buildings with varied roof types
        # {x, y, width, roof_type, color_shade}
        self.buildings = []

        self.beat_count = 0
        self.current_height = self.BASE_PLATFORM_Y

        # Starting building - wide and flat
        self.buildings.append({
            'x': 0.0,
            'y': self.BASE_PLATFORM_Y,
            'width': 50,
            'roof_type': 'flat',
            'shade': 0
        })

        self._generate_buildings_until(GRID_SIZE + 50)

        # Background buildings (parallax layer)
        self.bg_buildings = []
        for i in range(10):
            self.bg_buildings.append({
                'x': i * 8 - 10,
                'height': random.randint(15, 35),
                'width': random.randint(5, 9)
            })

        self.run_frame = 0
        self.run_timer = 0.0

    def _get_jump_distance(self) -> float:
        air_time = 2 * abs(self.JUMP_VELOCITY) / self.GRAVITY
        return self.scroll_speed * air_time

    def _generate_buildings_until(self, target_x: float):
        """Generate buildings with rhythm-based spacing and varied rooftops."""
        if not self.buildings:
            return

        roof_types = ['flat', 'flat', 'angled_left', 'angled_right', 'peaked', 'steeple', 'stepped']

        while True:
            last = self.buildings[-1]
            last_end = last['x'] + last['width']

            if last_end > target_x:
                break

            self.beat_count += 1
            jump_dist = self._get_jump_distance()

            # Gap varies within jumpable range
            base_gap = random.uniform(0.60, 0.85)

            # Height changes
            height_change = 0
            if self.beat_count > 3:
                roll = random.random()
                if roll < 0.30:  # Up
                    height_change = random.randint(-8, -3)
                elif roll < 0.55:  # Down
                    height_change = random.randint(3, 8)

            new_height = max(28, min(52, self.current_height + height_change))
            height_change = new_height - self.current_height

            # Adjust gap for height
            if height_change < 0:
                gap = jump_dist * (base_gap - 0.08)
            elif height_change > 0:
                gap = jump_dist * (base_gap + 0.05)
            else:
                gap = jump_dist * base_gap

            # Building width varies
            width_roll = random.random()
            if width_roll < 0.15:
                width = random.randint(8, 12)  # Narrow
            elif width_roll < 0.5:
                width = random.randint(14, 20)  # Medium
            else:
                width = random.randint(22, 35)  # Wide

            # Roof type - some types need minimum width
            if width < 12:
                roof = random.choice(['flat', 'peaked', 'steeple'])
            elif width < 18:
                roof = random.choice(['flat', 'flat', 'angled_left', 'angled_right', 'peaked'])
            else:
                roof = random.choice(roof_types)

            # Color variation
            shade = random.randint(0, 3)

            self.current_height = new_height

            self.buildings.append({
                'x': last_end + gap,
                'y': new_height,
                'width': width,
                'roof_type': roof,
                'shade': shade
            })

    def _get_landing_y(self, building: dict, x_pos: float) -> int:
        """Get the Y position for landing on a building at given X."""
        bx = building['x']
        by = building['y']
        bw = building['width']
        roof = building['roof_type']

        rel_x = x_pos - bx  # Position relative to building left edge

        if roof == 'flat':
            return by
        elif roof == 'angled_left':
            # Slopes down from left to right
            slope = 4 / bw
            return int(by + rel_x * slope)
        elif roof == 'angled_right':
            # Slopes up from left to right
            slope = 4 / bw
            return int(by + 4 - rel_x * slope)
        elif roof == 'peaked':
            # Peak in middle
            mid = bw / 2
            if rel_x < mid:
                return int(by - (rel_x / mid) * 4)
            else:
                return int(by - ((bw - rel_x) / mid) * 4)
        elif roof == 'steeple':
            # Tall narrow peak
            mid = bw / 2
            if rel_x < mid:
                return int(by - (rel_x / mid) * 8)
            else:
                return int(by - ((bw - rel_x) / mid) * 8)
        elif roof == 'stepped':
            # Two levels
            if rel_x < bw / 2:
                return by - 3
            else:
                return by

        return by

    def _near_ground(self) -> bool:
        """Check if player is close enough to a surface to jump (even if technically airborne)."""
        player_feet_y = self.player_y + 4
        tolerance = 6  # Pixels of grace for jump detection

        for b in self.buildings:
            if b['x'] <= self.PLAYER_X <= b['x'] + b['width']:
                landing_y = self._get_landing_y(b, self.PLAYER_X)
                # Can jump if feet are within tolerance of the surface
                if player_feet_y >= landing_y - tolerance and player_feet_y <= landing_y + tolerance:
                    return True
        return False

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        # Jump if on ground OR near a surface (allows slope jumping)
        can_jump_now = self.on_ground or self._near_ground()
        if (input_state.action_l or input_state.action_r) and can_jump_now and self.can_jump:
            self.velocity_y = self.JUMP_VELOCITY
            self.on_ground = False
            self.can_jump = False

        if not (input_state.action_l_held or input_state.action_r_held) or input_state.action_r_held:
            self.can_jump = True

        self.velocity_y += self.GRAVITY * dt
        self.velocity_y = min(self.velocity_y, self.MAX_FALL_SPEED)
        self.player_y += self.velocity_y * dt

        scroll_amount = self.scroll_speed * dt
        self.scroll_x += scroll_amount

        for b in self.buildings:
            b['x'] -= scroll_amount

        for b in self.bg_buildings:
            b['x'] -= scroll_amount * 0.3
            if b['x'] < -b['width']:
                b['x'] = GRID_SIZE + random.randint(0, 15)
                b['height'] = random.randint(15, 35)
                b['width'] = random.randint(5, 9)

        # Landing collision
        self.on_ground = False
        player_feet_y = self.player_y + 4

        for b in self.buildings:
            if b['x'] <= self.PLAYER_X <= b['x'] + b['width']:
                landing_y = self._get_landing_y(b, self.PLAYER_X)
                if self.velocity_y >= 0 and player_feet_y >= landing_y and player_feet_y <= landing_y + 10:
                    self.player_y = landing_y - 4
                    self.velocity_y = 0
                    self.on_ground = True
                    break

        if self.player_y > GRID_SIZE + 10:
            self.state = GameState.GAME_OVER
            return

        self.buildings = [b for b in self.buildings if b['x'] + b['width'] > -10]
        self._generate_buildings_until(GRID_SIZE + 60)

        self.score = int(self.scroll_x / 10)
        self.scroll_speed = min(70.0, 40.0 + self.score * 0.25)

        self.run_timer += dt
        if self.run_timer >= 0.1:
            self.run_timer = 0
            self.run_frame = (self.run_frame + 1) % 4

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Night sky
        for y in range(8, 58):
            shade = int((y - 8) * 0.3)
            self.display.draw_line(0, y, 63, y, (5, 5, min(35, 12 + shade)))

        # Stars
        random.seed(42)
        for _ in range(15):
            sx = random.randint(0, 63)
            sy = random.randint(8, 35)
            self.display.set_pixel(sx, sy, (100, 100, 120))
        random.seed()

        # Background buildings (silhouettes)
        for b in self.bg_buildings:
            bx = int(b['x'])
            by = 58 - b['height']
            for y in range(by, 58):
                for x in range(bx, bx + b['width']):
                    if 0 <= x < GRID_SIZE:
                        self.display.set_pixel(x, y, (15, 15, 25))
                        # Dim windows
                        if (x - bx) % 2 == 0 and (y - by) % 3 == 1:
                            self.display.set_pixel(x, y, (35, 35, 20))

        # Main buildings
        for b in self.buildings:
            self._draw_building(b)

        # Player
        self._draw_player()

        # HUD
        self.display.draw_line(0, 6, 63, 6, Colors.DARK_GRAY)
        self.display.draw_text_small(1, 1, f"{self.score}M", Colors.WHITE)
        speed_pct = int((self.scroll_speed - 40) / 30 * 100)
        self.display.draw_text_small(40, 1, f"{speed_pct}%", Colors.CYAN)

    def _draw_building(self, b: dict):
        bx = int(b['x'])
        by = b['y']
        bw = int(b['width'])
        roof = b['roof_type']
        shade = b['shade']

        # Building colors based on shade
        wall_colors = [
            (50, 45, 45), (45, 45, 55), (55, 50, 45), (40, 45, 50)
        ]
        roof_colors = [
            (90, 75, 65), (80, 80, 90), (95, 85, 70), (75, 80, 85)
        ]
        wall_color = wall_colors[shade]
        roof_color = roof_colors[shade]
        dark_roof = tuple(max(0, c - 25) for c in roof_color)

        # First draw the full building walls (bottom layer)
        for y in range(by, GRID_SIZE):
            for x in range(bx, bx + bw):
                if 0 <= x < GRID_SIZE:
                    self.display.set_pixel(x, y, wall_color)
                    # Windows
                    rel_x = x - bx
                    rel_y = y - by
                    if rel_x % 4 == 1 and rel_y % 5 in [2, 3]:
                        if random.random() < 0.85:
                            self.display.set_pixel(x, y, (70, 65, 40))

        # Then draw roof on top (with fills connecting to walls)
        if roof == 'flat':
            for x in range(bx, bx + bw):
                if 0 <= x < GRID_SIZE:
                    self.display.set_pixel(x, by, roof_color)
                    self.display.set_pixel(x, by + 1, dark_roof)

        elif roof == 'angled_left':
            # Slopes down from left to right
            for rx in range(bw):
                x = bx + rx
                roof_y = by + (rx * 4) // max(1, bw)
                if 0 <= x < GRID_SIZE:
                    self.display.set_pixel(x, roof_y, roof_color)
                    # Fill from roof line down to base level
                    for fy in range(roof_y + 1, by + 5):
                        if fy < GRID_SIZE:
                            self.display.set_pixel(x, fy, dark_roof)

        elif roof == 'angled_right':
            # Slopes down from right to left
            for rx in range(bw):
                x = bx + rx
                roof_y = by + 4 - (rx * 4) // max(1, bw)
                if 0 <= x < GRID_SIZE:
                    self.display.set_pixel(x, roof_y, roof_color)
                    for fy in range(roof_y + 1, by + 5):
                        if fy < GRID_SIZE:
                            self.display.set_pixel(x, fy, dark_roof)

        elif roof == 'peaked':
            mid = bw // 2
            for rx in range(bw):
                x = bx + rx
                if rx <= mid:
                    roof_y = by - (rx * 4) // max(1, mid)
                else:
                    roof_y = by - ((bw - rx) * 4) // max(1, mid)
                if 0 <= x < GRID_SIZE:
                    self.display.set_pixel(x, roof_y, roof_color)
                    # Fill under peak to wall level
                    for fy in range(roof_y + 1, by + 2):
                        self.display.set_pixel(x, fy, dark_roof)

        elif roof == 'steeple':
            mid = bw // 2
            for rx in range(bw):
                x = bx + rx
                if rx <= mid:
                    roof_y = by - (rx * 8) // max(1, mid)
                else:
                    roof_y = by - ((bw - rx) * 8) // max(1, mid)
                if 0 <= x < GRID_SIZE:
                    self.display.set_pixel(x, roof_y, roof_color)
                    for fy in range(roof_y + 1, by + 2):
                        self.display.set_pixel(x, fy, dark_roof)

        elif roof == 'stepped':
            # Left half is raised
            for x in range(bx, bx + bw // 2):
                if 0 <= x < GRID_SIZE:
                    self.display.set_pixel(x, by - 3, roof_color)
                    for fy in range(by - 2, by + 1):
                        self.display.set_pixel(x, fy, dark_roof)
            # Right half at base level
            for x in range(bx + bw // 2, bx + bw):
                if 0 <= x < GRID_SIZE:
                    self.display.set_pixel(x, by, roof_color)
                    self.display.set_pixel(x, by + 1, dark_roof)

    def _draw_player(self):
        px = self.PLAYER_X
        py = int(self.player_y)

        # Head
        self.display.set_pixel(px, py, Colors.WHITE)
        # Body
        self.display.set_pixel(px, py + 1, Colors.WHITE)
        self.display.set_pixel(px, py + 2, Colors.WHITE)

        if self.on_ground:
            if self.run_frame in [0, 2]:
                self.display.set_pixel(px - 1, py + 1, Colors.WHITE)
                self.display.set_pixel(px + 1, py + 2, Colors.WHITE)
                self.display.set_pixel(px - 1, py + 3, Colors.WHITE)
                self.display.set_pixel(px + 1, py + 4, Colors.WHITE)
            else:
                self.display.set_pixel(px + 1, py + 1, Colors.WHITE)
                self.display.set_pixel(px - 1, py + 2, Colors.WHITE)
                self.display.set_pixel(px + 1, py + 3, Colors.WHITE)
                self.display.set_pixel(px - 1, py + 4, Colors.WHITE)
        else:
            self.display.set_pixel(px - 1, py, Colors.WHITE)
            self.display.set_pixel(px + 1, py, Colors.WHITE)
            self.display.set_pixel(px - 1, py + 3, Colors.WHITE)
            self.display.set_pixel(px + 1, py + 3, Colors.WHITE)

    def draw_game_over(self):
        self.display.clear(Colors.BLACK)
        self.display.draw_text_small(8, 20, "GAME OVER", Colors.RED)
        self.display.draw_text_small(8, 32, f"DIST:{self.score}M", Colors.WHITE)
        self.display.draw_text_small(4, 50, "SPACE:RETRY", Colors.GRAY)
