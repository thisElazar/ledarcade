"""
Snake Demo - AI Attract Mode
=============================
Snake plays itself using BFS pathfinding for idle screen demos.
The AI navigates toward food while avoiding self-collision and walls.

AI Strategy:
- Use BFS from head to food
- Avoid tiles occupied by snake body (except tail which will move)
- If no path to food, follow tail to stay alive
"""

from collections import deque
from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

# Import the actual game
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.snake import Snake


class SnakeDemo(Visual):
    name = "SNAKE"
    description = "AI plays Snake"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = Snake(self.display)
        self.game.reset()
        self.ai_dir = (1, 0)  # Start moving right
        self.decision_timer = 0.0
        self.decision_interval = 0.05  # Recalculate frequently for responsive AI
        self.game_over_timer = 0.0

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
                self.ai_dir = (1, 0)
            return

        # Make AI decisions periodically
        self.decision_timer += dt
        if self.decision_timer >= self.decision_interval:
            self.decision_timer = 0.0
            self.ai_dir = self._decide_direction()

        # Create input state with AI's chosen direction
        ai_input = InputState()
        if self.ai_dir == (0, -1):
            ai_input.up = True
        elif self.ai_dir == (0, 1):
            ai_input.down = True
        elif self.ai_dir == (-1, 0):
            ai_input.left = True
        elif self.ai_dir == (1, 0):
            ai_input.right = True

        self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()

        # Overlay "DEMO" text (blinking)
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)

    def _decide_direction(self):
        """AI decision-making for Snake movement."""
        game = self.game
        head = game.snake[0]
        food = game.food

        # Get set of occupied cells (excluding tail since it will move)
        # When snake eats food, tail doesn't move, so be conservative
        body_set = set(game.snake[:-1])

        # Try to find path to food
        direction = self._bfs_path_to_target(head, food, body_set)

        if direction:
            return direction

        # No path to food - try to follow tail to stay alive
        tail = game.snake[-1]
        direction = self._bfs_path_to_target(head, tail, body_set)

        if direction:
            return direction

        # Last resort: find any safe direction
        return self._get_safe_direction(head, body_set)

    def _bfs_path_to_target(self, start, target, body_set):
        """BFS to find direction toward target, avoiding body."""
        game = self.game

        queue = deque([(start[0], start[1], None)])  # x, y, first_direction
        visited = {start}

        while queue:
            x, y, first_dir = queue.popleft()

            if (x, y) == target:
                return first_dir

            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                nx, ny = x + dx, y + dy

                # Check bounds (play area is 0 to GAME_WIDTH-1, 4 to GAME_HEIGHT-1)
                if nx < 0 or nx >= game.GAME_WIDTH:
                    continue
                if ny < 4 or ny >= game.GAME_HEIGHT:
                    continue

                if (nx, ny) in visited:
                    continue

                # Avoid snake body
                if (nx, ny) in body_set:
                    continue

                visited.add((nx, ny))
                # Track the first direction taken from start
                dir_to_use = first_dir if first_dir else (dx, dy)
                queue.append((nx, ny, dir_to_use))

        return None

    def _get_safe_direction(self, head, body_set):
        """Find any safe direction to move."""
        game = self.game
        current_dir = game.direction

        # Try directions in order of preference: continue straight, then turn
        directions = [
            current_dir,  # Prefer continuing straight
            (current_dir[1], current_dir[0]),  # Turn one way
            (-current_dir[1], -current_dir[0]),  # Turn other way
            (-current_dir[0], -current_dir[1]),  # Reverse (usually blocked)
        ]

        for dx, dy in directions:
            nx, ny = head[0] + dx, head[1] + dy

            # Check bounds
            if nx < 0 or nx >= game.GAME_WIDTH:
                continue
            if ny < 4 or ny >= game.GAME_HEIGHT:
                continue

            # Check body collision
            if (nx, ny) in body_set:
                continue

            # Can't reverse direction
            if (dx, dy) == (-game.direction[0], -game.direction[1]):
                continue

            return (dx, dy)

        # No safe direction - return current (game will end)
        return current_dir
