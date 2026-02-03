"""
Bomberman Demo - AI Attract Mode
================================
Bomberman plays itself using pathfinding AI for idle screen demos.
The AI navigates around bombs, destroys bricks, kills enemies, and finds the exit.

AI Strategy:
- Calculate danger zones from active bombs (bomb positions + fire_power range in 4 directions)
- If in danger zone, pathfind to nearest safe tile
- If safe and near a brick wall, place bomb then move away
- If exit is revealed and all enemies dead, pathfind to exit
- Target bricks near enemies to kill them
- Collect powerups when safe
"""

from collections import deque
from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

# Import the actual game
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.bomberman import Bomberman


class BombermanDemo(Visual):
    name = "BOMBERMAN"
    description = "AI plays Bomberman"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = Bomberman(self.display)
        self.game.reset()
        self.decision_timer = 0.0
        self.decision_interval = 0.08  # Decide frequently for responsive play
        self.current_action = None  # 'up', 'down', 'left', 'right', 'bomb', None
        self.game_over_timer = 0.0
        self.escape_target = None  # Target tile when escaping danger
        self.last_bomb_time = 0.0  # Track when we last placed a bomb

    def handle_input(self, input_state):
        # Demo doesn't respond to input (auto-plays)
        return False

    def update(self, dt):
        self.time += dt

        # If game over, restart after a pause
        if self.game.state == GameState.GAME_OVER:
            self.game_over_timer += dt
            if self.game_over_timer > 3.0:
                self.game.reset()
                self.game_over_timer = 0.0
                self.escape_target = None
            return

        # Make AI decisions periodically
        self.decision_timer += dt
        if self.decision_timer >= self.decision_interval:
            self.decision_timer = 0.0
            self.current_action = self._decide_action()

        # Create input state with AI's chosen action
        ai_input = InputState()
        if self.current_action == 'up':
            ai_input.up = True
        elif self.current_action == 'down':
            ai_input.down = True
        elif self.current_action == 'left':
            ai_input.left = True
        elif self.current_action == 'right':
            ai_input.right = True
        elif self.current_action == 'bomb':
            ai_input.action_l = True

        self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()

        # Overlay "DEMO" text (blinking)
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)

    def _decide_action(self):
        """AI decision-making for Bomberman movement and bomb placement."""
        game = self.game
        px, py = game.player_x, game.player_y

        # Calculate danger zones from active bombs
        danger_zones = self._get_danger_zones()

        # Check if currently in danger
        in_danger = (px, py) in danger_zones

        if in_danger:
            # Priority 1: Escape danger!
            return self._escape_danger(px, py, danger_zones)

        # Clear escape target when safe
        self.escape_target = None

        # Priority 2: If exit revealed and all enemies dead, go to exit
        if game.exit_revealed and len(game.enemies) == 0:
            direction = self._pathfind_to(px, py, game.exit_x, game.exit_y, danger_zones)
            if direction:
                return direction

        # Priority 3: Collect nearby powerups if safe
        powerup_action = self._collect_powerup(px, py, danger_zones)
        if powerup_action:
            return powerup_action

        # Priority 4: Hunt enemies by bombing bricks near them
        bomb_action = self._offensive_strategy(px, py, danger_zones)
        if bomb_action:
            return bomb_action

        # Priority 5: Destroy bricks to explore
        explore_action = self._explore_strategy(px, py, danger_zones)
        if explore_action:
            return explore_action

        # Default: wander safely
        return self._wander_safely(px, py, danger_zones)

    def _get_danger_zones(self):
        """Calculate all tiles that will be hit by explosions."""
        game = self.game
        danger = set()

        for bomb in game.active_bombs:
            bx, by = bomb['x'], bomb['y']
            # Bomb center is dangerous
            danger.add((bx, by))

            # Explosion spreads in 4 directions up to fire_power
            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                for dist in range(1, game.fire_power + 1):
                    ex, ey = bx + dx * dist, by + dy * dist

                    # Check bounds
                    if ex < 0 or ex >= game.GRID_WIDTH or ey < 0 or ey >= game.GRID_HEIGHT:
                        break

                    tile = game.grid[ey][ex]

                    # Stop at walls
                    if tile == game.WALL:
                        break

                    # Add to danger (even if brick - it will be destroyed)
                    danger.add((ex, ey))

                    # Stop at bricks (explosion stops after destroying)
                    if tile == game.BRICK:
                        break

        # Also mark tiles near active explosions
        for y in range(game.GRID_HEIGHT):
            for x in range(game.GRID_WIDTH):
                if game.grid[y][x] == game.EXPLOSION:
                    danger.add((x, y))

        return danger

    def _escape_danger(self, px, py, danger_zones):
        """Find path to nearest safe tile."""
        game = self.game

        # If we have an escape target and it's still safe, continue toward it
        if self.escape_target and self.escape_target not in danger_zones:
            tx, ty = self.escape_target
            if (px, py) == self.escape_target:
                self.escape_target = None
                return None
            direction = self._pathfind_to(px, py, tx, ty, set())  # Ignore danger for pathing when escaping
            if direction:
                return direction

        # BFS to find nearest safe tile
        queue = deque([(px, py, None, 0)])  # x, y, first_direction, distance
        visited = {(px, py)}

        while queue:
            x, y, first_dir, dist = queue.popleft()

            # Check if this tile is safe
            if (x, y) not in danger_zones and dist > 0:
                self.escape_target = (x, y)
                return first_dir

            # Explore neighbors
            for direction, (dx, dy) in [('up', (0, -1)), ('down', (0, 1)),
                                         ('left', (-1, 0)), ('right', (1, 0))]:
                nx, ny = x + dx, y + dy

                if (nx, ny) not in visited and self._can_walk(nx, ny):
                    visited.add((nx, ny))
                    dir_to_use = first_dir if first_dir else direction
                    queue.append((nx, ny, dir_to_use, dist + 1))

        # No safe path found, try any direction
        for direction, (dx, dy) in [('up', (0, -1)), ('down', (0, 1)),
                                     ('left', (-1, 0)), ('right', (1, 0))]:
            nx, ny = px + dx, py + dy
            if self._can_walk(nx, ny):
                return direction

        return None

    def _can_walk(self, x, y):
        """Check if AI can walk to a tile."""
        game = self.game
        if x < 0 or x >= game.GRID_WIDTH or y < 0 or y >= game.GRID_HEIGHT:
            return False

        tile = game.grid[y][x]
        if tile in [game.EMPTY, game.EXIT, game.POWERUP_BOMB, game.POWERUP_FIRE, game.POWERUP_SPEED]:
            # Also check for bombs
            for bomb in game.active_bombs:
                if bomb['x'] == x and bomb['y'] == y:
                    return False
            return True
        return False

    def _pathfind_to(self, start_x, start_y, target_x, target_y, danger_zones):
        """BFS pathfinding to target, avoiding danger zones."""
        if start_x == target_x and start_y == target_y:
            return None

        queue = deque([(start_x, start_y, None)])
        visited = {(start_x, start_y)}

        while queue:
            x, y, first_dir = queue.popleft()

            if x == target_x and y == target_y:
                return first_dir

            for direction, (dx, dy) in [('up', (0, -1)), ('down', (0, 1)),
                                         ('left', (-1, 0)), ('right', (1, 0))]:
                nx, ny = x + dx, y + dy

                if (nx, ny) not in visited and self._can_walk(nx, ny):
                    if (nx, ny) not in danger_zones:
                        visited.add((nx, ny))
                        dir_to_use = first_dir if first_dir else direction
                        queue.append((nx, ny, dir_to_use))

        return None

    def _collect_powerup(self, px, py, danger_zones):
        """Move toward nearby powerups if safe."""
        game = self.game

        # Find nearest powerup
        nearest_powerup = None
        nearest_dist = float('inf')

        for y in range(game.GRID_HEIGHT):
            for x in range(game.GRID_WIDTH):
                tile = game.grid[y][x]
                if tile in [game.POWERUP_BOMB, game.POWERUP_FIRE, game.POWERUP_SPEED]:
                    if (x, y) not in danger_zones:
                        dist = abs(x - px) + abs(y - py)
                        if dist < nearest_dist:
                            nearest_dist = dist
                            nearest_powerup = (x, y)

        if nearest_powerup and nearest_dist < 8:  # Only go for nearby powerups
            tx, ty = nearest_powerup
            return self._pathfind_to(px, py, tx, ty, danger_zones)

        return None

    def _offensive_strategy(self, px, py, danger_zones):
        """Try to kill enemies by bombing bricks near them."""
        game = self.game

        # Don't place bombs too frequently
        if self.time - self.last_bomb_time < 1.0:
            return None

        # Can we place a bomb?
        if len(game.active_bombs) >= game.max_bombs:
            return None

        # Find bricks adjacent to current position
        adjacent_bricks = []
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            nx, ny = px + dx, py + dy
            if 0 <= nx < game.GRID_WIDTH and 0 <= ny < game.GRID_HEIGHT:
                if game.grid[ny][nx] == game.BRICK:
                    adjacent_bricks.append((nx, ny))

        if not adjacent_bricks:
            return None

        # Check if bombing here would hit an enemy (through brick destruction and chain)
        # Or if we should bomb anyway to make progress
        should_bomb = False

        # Check if any enemy is near a brick we'd destroy
        for bx, by in adjacent_bricks:
            for enemy in game.enemies:
                ex, ey = enemy['x'], enemy['y']
                # If enemy is within blast radius of the brick
                if abs(ex - bx) + abs(ey - by) <= game.fire_power + 1:
                    should_bomb = True
                    break

        # Also bomb to reveal exit or make progress
        if not should_bomb and not game.exit_revealed:
            should_bomb = True

        if should_bomb:
            # Make sure we have an escape route before bombing
            test_danger = danger_zones.copy()
            test_danger.add((px, py))
            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                for dist in range(1, game.fire_power + 1):
                    ex, ey = px + dx * dist, py + dy * dist
                    if 0 <= ex < game.GRID_WIDTH and 0 <= ey < game.GRID_HEIGHT:
                        if game.grid[ey][ex] == game.WALL:
                            break
                        test_danger.add((ex, ey))
                        if game.grid[ey][ex] == game.BRICK:
                            break

            # Check if we can escape
            escape_dir = self._find_escape_route(px, py, test_danger)
            if escape_dir:
                self.last_bomb_time = self.time
                return 'bomb'

        return None

    def _find_escape_route(self, px, py, danger_zones):
        """Check if there's an escape route from danger."""
        queue = deque([(px, py, None, 0)])
        visited = {(px, py)}

        while queue:
            x, y, first_dir, dist = queue.popleft()

            if (x, y) not in danger_zones and dist > 0:
                return first_dir

            for direction, (dx, dy) in [('up', (0, -1)), ('down', (0, 1)),
                                         ('left', (-1, 0)), ('right', (1, 0))]:
                nx, ny = x + dx, y + dy

                if (nx, ny) not in visited and self._can_walk(nx, ny):
                    visited.add((nx, ny))
                    dir_to_use = first_dir if first_dir else direction
                    queue.append((nx, ny, dir_to_use, dist + 1))

        return None

    def _explore_strategy(self, px, py, danger_zones):
        """Move toward unexplored areas (bricks to destroy)."""
        game = self.game

        # Find nearest brick we could bomb
        nearest_brick_pos = None
        nearest_dist = float('inf')

        for y in range(1, game.GRID_HEIGHT - 1):
            for x in range(1, game.GRID_WIDTH - 1):
                if game.grid[y][x] == game.BRICK:
                    # Check if there's an adjacent empty tile we could stand on
                    for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                        ax, ay = x + dx, y + dy
                        if self._can_walk(ax, ay) and (ax, ay) not in danger_zones:
                            dist = abs(ax - px) + abs(ay - py)
                            if dist < nearest_dist:
                                nearest_dist = dist
                                nearest_brick_pos = (ax, ay)

        if nearest_brick_pos:
            tx, ty = nearest_brick_pos
            direction = self._pathfind_to(px, py, tx, ty, danger_zones)
            if direction:
                return direction

        return None

    def _wander_safely(self, px, py, danger_zones):
        """Wander to a safe adjacent tile."""
        import random

        safe_moves = []
        for direction, (dx, dy) in [('up', (0, -1)), ('down', (0, 1)),
                                     ('left', (-1, 0)), ('right', (1, 0))]:
            nx, ny = px + dx, py + dy
            if self._can_walk(nx, ny) and (nx, ny) not in danger_zones:
                safe_moves.append(direction)

        if safe_moves:
            return random.choice(safe_moves)

        return None
