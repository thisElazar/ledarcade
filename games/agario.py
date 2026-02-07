"""
Agar.io - Eat or be eaten
=========================
Control a cell in a petri dish. Eat food pellets and smaller cells to grow.
Avoid bigger cells or get consumed! 3-minute timed challenge.

Controls:
  Arrow Keys  - Move direction (held = continuous)
  Space       - Speed boost (3s, costs 10% mass)
  Z           - Eject mass forward
"""

import random
import math
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE

WORLD_SIZE = 192  # Toroidal open world (3x screen)


class Cell:
    """A cell (player or AI) in the arena."""

    def __init__(self, x, y, mass, color):
        self.x = float(x)
        self.y = float(y)
        self.mass = float(mass)
        self.color = color
        self.vx = 0.0
        self.vy = 0.0

    @property
    def radius(self):
        return math.sqrt(self.mass) * 0.9

    @property
    def speed(self):
        return 30.0 / math.sqrt(self.mass / 10.0)

    def draw_radius(self):
        return max(1, int(self.radius))


# Bright colors for food and AI cells
CELL_COLORS = [
    Colors.RED, Colors.GREEN, Colors.YELLOW, Colors.MAGENTA,
    Colors.ORANGE, Colors.PINK, Colors.LIME, Colors.PURPLE,
]

FOOD_COLORS = [
    Colors.RED, Colors.GREEN, Colors.YELLOW, Colors.CYAN,
    Colors.MAGENTA, Colors.ORANGE, Colors.PINK, Colors.LIME,
    Colors.PURPLE, Colors.WHITE,
]


class Agario(Game):
    name = "AGAR.IO"
    description = "Eat cells to grow, avoid bigger ones!"
    category = "modern"

    NUM_FOOD = 120
    NUM_AI = 12

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0

        # Player cell - start near center of world
        cx = WORLD_SIZE // 2
        self.player = Cell(
            cx + random.randint(-16, 16),
            cx + random.randint(-16, 16),
            10, Colors.CYAN
        )
        self.boost_timer = 0.0
        self.face_x = 1.0
        self.face_y = 0.0
        self.ejects = []  # flying ejected blobs
        self.time_left = 180.0  # 3-minute challenge

        # Camera follows player
        self.cam_x = self.player.x
        self.cam_y = self.player.y

        # Food pellets
        self.food = []
        for _ in range(self.NUM_FOOD):
            self.food.append(self._spawn_food())

        # AI cells
        self.ai_cells = []
        for _ in range(self.NUM_AI):
            self.ai_cells.append(self._spawn_ai())

    # --- World wrapping helpers ---

    def _wrap_delta(self, x1, y1, x2, y2):
        """Shortest delta from (x1,y1) to (x2,y2) on toroidal world."""
        dx = (x2 - x1 + WORLD_SIZE / 2) % WORLD_SIZE - WORLD_SIZE / 2
        dy = (y2 - y1 + WORLD_SIZE / 2) % WORLD_SIZE - WORLD_SIZE / 2
        return dx, dy

    def _wrap_dist(self, x1, y1, x2, y2):
        dx, dy = self._wrap_delta(x1, y1, x2, y2)
        return math.sqrt(dx * dx + dy * dy)

    def _world_to_screen(self, wx, wy):
        """Convert world coords to screen coords relative to camera."""
        half = GRID_SIZE // 2
        dx = (wx - self.cam_x + WORLD_SIZE / 2) % WORLD_SIZE - WORLD_SIZE / 2
        dy = (wy - self.cam_y + WORLD_SIZE / 2) % WORLD_SIZE - WORLD_SIZE / 2
        return int(half + dx), int(half + dy)

    # --- Spawning ---

    def _spawn_food(self):
        return {
            'x': random.randint(0, WORLD_SIZE - 1),
            'y': random.randint(0, WORLD_SIZE - 1),
            'color': random.choice(FOOD_COLORS),
        }

    def _spawn_ai(self, edge=False):
        mass = random.uniform(5, 25)
        color = random.choice(CELL_COLORS)
        if edge:
            # Spawn just outside visible area around player
            angle = random.uniform(0, 2 * math.pi)
            dist = GRID_SIZE // 2 + random.randint(5, 20)
            x = (self.player.x + math.cos(angle) * dist) % WORLD_SIZE
            y = (self.player.y + math.sin(angle) * dist) % WORLD_SIZE
        else:
            x = random.randint(0, WORLD_SIZE - 1)
            y = random.randint(0, WORLD_SIZE - 1)
        return Cell(x, y, mass, color)

    # --- Update ---

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        # Countdown timer
        self.time_left -= dt
        if self.time_left <= 0:
            self.time_left = 0
            self.state = GameState.GAME_OVER
            return

        # Player movement
        dx = input_state.dx
        dy = input_state.dy
        if dx != 0 or dy != 0:
            length = math.sqrt(dx * dx + dy * dy)
            dx /= length
            dy /= length
            self.face_x = dx
            self.face_y = dy
            speed = self.player.speed
            if self.boost_timer > 0:
                speed *= 2.0
                self.boost_timer -= dt
            self.player.x += dx * speed * dt
            self.player.y += dy * speed * dt
        else:
            if self.boost_timer > 0:
                self.boost_timer -= dt

        # Speed boost (Space)
        if input_state.action_l:
            if self.player.mass > 12 and self.boost_timer <= 0:
                self.player.mass *= 0.9
                self.boost_timer = 3.0

        # Eject mass forward (Z)
        if input_state.action_r:
            if self.player.mass > 15:
                eject_mass = max(3, self.player.mass * 0.1)
                self.player.mass -= eject_mass
                self.ejects.append({
                    'x': self.player.x,
                    'y': self.player.y,
                    'vx': self.face_x * 50.0,
                    'vy': self.face_y * 50.0,
                    'color': self.player.color,
                    'life': 0.4,
                })

        # Wrap player position (toroidal world - no edges!)
        self.player.x %= WORLD_SIZE
        self.player.y %= WORLD_SIZE

        # Camera follows player
        self.cam_x = self.player.x
        self.cam_y = self.player.y

        # Update ejected blobs
        for e in self.ejects:
            e['x'] = (e['x'] + e['vx'] * dt) % WORLD_SIZE
            e['y'] = (e['y'] + e['vy'] * dt) % WORLD_SIZE
            e['vx'] *= 0.92
            e['vy'] *= 0.92
            e['life'] -= dt
        expired = [i for i, e in enumerate(self.ejects) if e['life'] <= 0]
        for i in reversed(expired):
            e = self.ejects.pop(i)
            self.food.append({'x': e['x'], 'y': e['y'], 'color': e['color']})

        # AI movement
        self._update_ai(dt)

        # Check player eating food
        self._check_food_eating(self.player)

        # Check AI eating food
        for ai in self.ai_cells:
            self._check_food_eating(ai)

        # Check cell-vs-cell collisions (player vs AI)
        self._check_cell_collisions()

        # Check AI-vs-AI collisions
        self._check_ai_collisions()

        # Respawn food to maintain count
        while len(self.food) < self.NUM_FOOD:
            self.food.append(self._spawn_food())

    def _check_food_eating(self, cell):
        r = cell.radius
        eaten = []
        for i, f in enumerate(self.food):
            dist = self._wrap_dist(cell.x, cell.y, f['x'], f['y'])
            if dist < r + 0.5:
                eaten.append(i)
                cell.mass += 1
                if cell is self.player:
                    self.score += 1
        for i in reversed(eaten):
            self.food.pop(i)

    def _check_cell_collisions(self):
        pr = self.player.radius
        for i, ai in enumerate(self.ai_cells):
            ar = ai.radius
            dist = self._wrap_dist(self.player.x, self.player.y, ai.x, ai.y)
            if dist < max(pr, ar):
                if pr >= ar:
                    # Player eats AI
                    self.score += int(ai.mass)
                    self.player.mass += ai.mass
                    self.ai_cells[i] = self._spawn_ai(edge=True)
                else:
                    # AI eats player - game over
                    self.state = GameState.GAME_OVER

    def _check_ai_collisions(self):
        to_respawn = []
        for i in range(len(self.ai_cells)):
            for j in range(i + 1, len(self.ai_cells)):
                a = self.ai_cells[i]
                b = self.ai_cells[j]
                dist = self._wrap_dist(a.x, a.y, b.x, b.y)
                if dist < max(a.radius, b.radius):
                    if a.radius >= b.radius:
                        a.mass += b.mass
                        to_respawn.append(j)
                    else:
                        b.mass += a.mass
                        to_respawn.append(i)
        for idx in sorted(set(to_respawn), reverse=True):
            self.ai_cells[idx] = self._spawn_ai(edge=True)

    def _update_ai(self, dt):
        for ai in self.ai_cells:
            # Find nearest food
            best_food = None
            best_food_dist = float('inf')
            for f in self.food:
                d = self._wrap_dist(ai.x, ai.y, f['x'], f['y'])
                if d < best_food_dist:
                    best_food_dist = d
                    best_food = f

            # Find nearest threat and nearest prey
            nearest_threat = None
            threat_dist = float('inf')
            nearest_prey = None
            prey_dist = float('inf')

            # Check player
            d = self._wrap_dist(ai.x, ai.y, self.player.x, self.player.y)
            if self.player.radius > ai.radius:
                if d < threat_dist:
                    threat_dist = d
                    nearest_threat = self.player
            elif ai.radius > self.player.radius:
                if d < prey_dist:
                    prey_dist = d
                    nearest_prey = self.player

            # Check other AI
            for other in self.ai_cells:
                if other is ai:
                    continue
                d = self._wrap_dist(ai.x, ai.y, other.x, other.y)
                if other.radius > ai.radius:
                    if d < threat_dist:
                        threat_dist = d
                        nearest_threat = other
                elif ai.radius > other.radius:
                    if d < prey_dist:
                        prey_dist = d
                        nearest_prey = other

            # Decide target: flee threats within 12px, else chase prey or food
            tx, ty = ai.x, ai.y
            if nearest_threat and threat_dist < 12:
                # Flee: direction away from threat (wrapped)
                fdx, fdy = self._wrap_delta(nearest_threat.x, nearest_threat.y, ai.x, ai.y)
                if fdx == 0 and fdy == 0:
                    fdx, fdy = random.uniform(-1, 1), random.uniform(-1, 1)
                tx = ai.x + fdx
                ty = ai.y + fdy
            elif nearest_prey and prey_dist < 15:
                tx = nearest_prey.x
                ty = nearest_prey.y
            elif best_food:
                tx = best_food['x']
                ty = best_food['y']

            # Move toward target (using wrapped direction)
            dx, dy = self._wrap_delta(ai.x, ai.y, tx, ty)
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 0.5:
                dx /= dist
                dy /= dist
                speed = ai.speed
                ai.x += dx * speed * dt
                ai.y += dy * speed * dt

            # Wrap position
            ai.x %= WORLD_SIZE
            ai.y %= WORLD_SIZE

    # --- Drawing ---

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Draw scrolling grid
        half = GRID_SIZE // 2
        cam_ix = int(round(self.cam_x))
        cam_iy = int(round(self.cam_y))
        gx = (-(cam_ix - half)) % 8
        gy = (-(cam_iy - half)) % 8
        for sx in range(gx, GRID_SIZE, 8):
            for sy in range(GRID_SIZE):
                self.display.set_pixel(sx, sy, (10, 10, 10))
        for sy in range(gy, GRID_SIZE, 8):
            for sx in range(GRID_SIZE):
                self.display.set_pixel(sx, sy, (10, 10, 10))

        # Draw food (only visible)
        for f in self.food:
            sx, sy = self._world_to_screen(f['x'], f['y'])
            if 0 <= sx < GRID_SIZE and 0 <= sy < GRID_SIZE:
                self.display.set_pixel(sx, sy, f['color'])

        # Draw ejected blobs (only visible)
        for e in self.ejects:
            sx, sy = self._world_to_screen(e['x'], e['y'])
            if 0 <= sx < GRID_SIZE and 0 <= sy < GRID_SIZE:
                self.display.set_pixel(sx, sy, e['color'])

        # Draw AI cells (sorted by size so bigger ones render on top)
        all_cells = sorted(self.ai_cells, key=lambda c: c.radius)
        for cell in all_cells:
            self._draw_cell(cell)

        # Draw player on top
        self._draw_cell(self.player)

        # HUD: score (left) and timer (right)
        self.display.draw_text_small(2, 1, f"{self.score}", Colors.WHITE)
        mins = int(self.time_left) // 60
        secs = int(self.time_left) % 60
        timer_str = f"{mins}:{secs:02d}"
        timer_color = Colors.RED if self.time_left < 30 else Colors.WHITE
        self.display.draw_text_small(44, 1, timer_str, timer_color)

    def _draw_cell(self, cell):
        sx, sy = self._world_to_screen(cell.x, cell.y)
        r = cell.draw_radius()
        # Cull off-screen cells
        if sx + r < 0 or sx - r >= GRID_SIZE or sy + r < 0 or sy - r >= GRID_SIZE:
            return
        dark = tuple(max(0, c // 3) for c in cell.color)
        if r >= 2:
            self.display.draw_circle(sx, sy, r, dark, filled=True)
            self.display.draw_circle(sx, sy, r - 1, cell.color, filled=True)
        else:
            self.display.draw_circle(sx, sy, r, cell.color, filled=True)
