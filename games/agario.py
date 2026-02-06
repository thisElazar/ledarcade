"""
Agar.io - Eat or be eaten
=========================
Control a cell in a petri dish. Eat food pellets and smaller cells to grow.
Avoid bigger cells or get consumed!

Controls:
  Arrow Keys  - Move direction (held = continuous)
  Space       - Speed boost (costs 10% mass)
"""

import random
import math
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


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

    NUM_FOOD = 40
    NUM_AI = 7

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0

        # Player cell
        self.player = Cell(
            random.randint(16, 48), random.randint(16, 48),
            10, Colors.CYAN
        )
        self.boost_timer = 0.0

        # Food pellets
        self.food = []
        for _ in range(self.NUM_FOOD):
            self.food.append(self._spawn_food())

        # AI cells
        self.ai_cells = []
        for _ in range(self.NUM_AI):
            self.ai_cells.append(self._spawn_ai())

    def _spawn_food(self):
        return {
            'x': random.randint(1, GRID_SIZE - 2),
            'y': random.randint(1, GRID_SIZE - 2),
            'color': random.choice(FOOD_COLORS),
        }

    def _spawn_ai(self, edge=False):
        mass = random.uniform(5, 25)
        color = random.choice(CELL_COLORS)
        if edge:
            side = random.randint(0, 3)
            if side == 0:
                x, y = random.randint(2, GRID_SIZE - 3), 1
            elif side == 1:
                x, y = random.randint(2, GRID_SIZE - 3), GRID_SIZE - 2
            elif side == 2:
                x, y = 1, random.randint(2, GRID_SIZE - 3)
            else:
                x, y = GRID_SIZE - 2, random.randint(2, GRID_SIZE - 3)
        else:
            x = random.randint(4, GRID_SIZE - 5)
            y = random.randint(4, GRID_SIZE - 5)
        return Cell(x, y, mass, color)

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        # Player movement
        dx = input_state.dx
        dy = input_state.dy
        if dx != 0 or dy != 0:
            length = math.sqrt(dx * dx + dy * dy)
            dx /= length
            dy /= length
            speed = self.player.speed
            # Boost
            if self.boost_timer > 0:
                speed *= 2.0
                self.boost_timer -= dt
            self.player.x += dx * speed * dt
            self.player.y += dy * speed * dt
        else:
            if self.boost_timer > 0:
                self.boost_timer -= dt

        # Speed boost on action
        if input_state.action_l or input_state.action_r:
            if self.player.mass > 12:
                self.player.mass *= 0.9
                self.boost_timer = 0.3

        # Clamp player to arena
        r = self.player.radius
        self.player.x = max(r, min(GRID_SIZE - 1 - r, self.player.x))
        self.player.y = max(r, min(GRID_SIZE - 1 - r, self.player.y))

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
            dist = math.sqrt((cell.x - f['x']) ** 2 + (cell.y - f['y']) ** 2)
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
            dist = math.sqrt((self.player.x - ai.x) ** 2 + (self.player.y - ai.y) ** 2)
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
                dist = math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)
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
                d = math.sqrt((ai.x - f['x']) ** 2 + (ai.y - f['y']) ** 2)
                if d < best_food_dist:
                    best_food_dist = d
                    best_food = f

            # Find nearest threat and nearest prey among other cells
            nearest_threat = None
            threat_dist = float('inf')
            nearest_prey = None
            prey_dist = float('inf')

            # Check player
            d = math.sqrt((ai.x - self.player.x) ** 2 + (ai.y - self.player.y) ** 2)
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
                d = math.sqrt((ai.x - other.x) ** 2 + (ai.y - other.y) ** 2)
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
                # Flee: move away from threat
                dx = ai.x - nearest_threat.x
                dy = ai.y - nearest_threat.y
                if dx == 0 and dy == 0:
                    dx, dy = random.uniform(-1, 1), random.uniform(-1, 1)
                tx = ai.x + dx
                ty = ai.y + dy
            elif nearest_prey and prey_dist < 15:
                tx = nearest_prey.x
                ty = nearest_prey.y
            elif best_food:
                tx = best_food['x']
                ty = best_food['y']

            # Move toward target
            dx = tx - ai.x
            dy = ty - ai.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 0.5:
                dx /= dist
                dy /= dist
                speed = ai.speed
                ai.x += dx * speed * dt
                ai.y += dy * speed * dt

            # Clamp to arena
            ar = ai.radius
            ai.x = max(ar, min(GRID_SIZE - 1 - ar, ai.x))
            ai.y = max(ar, min(GRID_SIZE - 1 - ar, ai.y))

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Draw subtle grid
        for i in range(0, GRID_SIZE, 8):
            for j in range(GRID_SIZE):
                self.display.set_pixel(i, j, (10, 10, 10))
                self.display.set_pixel(j, i, (10, 10, 10))

        # Draw food
        for f in self.food:
            self.display.set_pixel(f['x'], f['y'], f['color'])

        # Draw AI cells (sorted by size so bigger ones render on top)
        all_cells = sorted(self.ai_cells, key=lambda c: c.radius)
        for cell in all_cells:
            self._draw_cell(cell)

        # Draw player on top
        self._draw_cell(self.player)

        # HUD: score
        self.display.draw_text_small(2, 1, f"{self.score}", Colors.WHITE)

    def _draw_cell(self, cell):
        r = cell.draw_radius()
        cx, cy = int(cell.x), int(cell.y)
        # Darker outline color
        dark = tuple(max(0, c // 3) for c in cell.color)
        if r >= 2:
            self.display.draw_circle(cx, cy, r, dark, filled=True)
            self.display.draw_circle(cx, cy, r - 1, cell.color, filled=True)
        else:
            self.display.draw_circle(cx, cy, r, cell.color, filled=True)
