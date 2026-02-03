"""
Pipe Dream Demo - AI Attract Mode
==================================
Pipe Dream plays itself using strategic AI for idle screen demos.
The AI places pipes to keep the flow going as long as possible.

AI Strategy:
- Track the current flow direction and position
- Look ahead in the piece queue to plan placement
- Prioritize placing pipes that connect to the flow path
- Place pipes that extend the path away from edges
- Avoid blocking yourself in corners
- Keep the path going as long as possible
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

# Import the actual game
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.pipedream import PipeDream, PipeType, PIPE_CONNECTIONS


class PipeDreamDemo(Visual):
    name = "PIPE DREAM DEMO"
    description = "AI connects pipes"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = PipeDream(self.display)
        self.game.reset()
        self.decision_timer = 0.0
        self.decision_interval = 0.15  # Time between AI decisions
        self.current_action = None
        self.game_over_timer = 0.0
        self.target_x = None
        self.target_y = None
        self.place_cooldown = 0.0

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
                self.target_x = None
                self.target_y = None
            return

        # Update cooldowns
        if self.place_cooldown > 0:
            self.place_cooldown -= dt

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
        elif self.current_action == 'place':
            ai_input.action_l = True
            self.place_cooldown = 0.3

        self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()

        # Overlay "DEMO" text (blinking)
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)

    def _decide_action(self):
        """AI decision-making for cursor movement and pipe placement."""
        game = self.game

        # Find best placement target
        best_target = self._find_best_placement()

        if best_target:
            self.target_x, self.target_y = best_target

        # If no target, place pipes near the flow path
        if self.target_x is None or self.target_y is None:
            self.target_x, self.target_y = self._get_default_target()

        # Move cursor toward target
        if game.cursor_x < self.target_x:
            return 'right'
        elif game.cursor_x > self.target_x:
            return 'left'
        elif game.cursor_y < self.target_y:
            return 'down'
        elif game.cursor_y > self.target_y:
            return 'up'
        else:
            # At target position - place pipe if valid
            if self.place_cooldown <= 0:
                if self._should_place_here():
                    self.target_x = None
                    self.target_y = None
                    return 'place'
                else:
                    # Find new target
                    self.target_x = None
                    self.target_y = None

        return None

    def _get_default_target(self):
        """Get a default target near the flow path."""
        game = self.game

        # Start near where the flow currently is or will be
        flow_col = game.flow_col
        flow_row = game.flow_row

        # Look ahead in the flow direction
        next_col, next_row = flow_col, flow_row
        if game.flow_dir == 'right':
            next_col = min(game.GRID_CELLS - 1, flow_col + 1)
        elif game.flow_dir == 'left':
            next_col = max(0, flow_col - 1)
        elif game.flow_dir == 'up':
            next_row = max(0, flow_row - 1)
        elif game.flow_dir == 'down':
            next_row = min(game.GRID_CELLS - 1, flow_row + 1)

        # If that cell is empty, target it
        if game.grid[next_row][next_col] == PipeType.EMPTY:
            return (next_col, next_row)

        # Otherwise find any empty cell
        for row in range(game.GRID_CELLS):
            for col in range(game.GRID_CELLS):
                if game.grid[row][col] == PipeType.EMPTY:
                    return (col, row)

        return (game.cursor_x, game.cursor_y)

    def _find_best_placement(self):
        """
        Find the best location to place the current pipe piece.
        Returns (col, row) or None.
        """
        game = self.game

        if not game.queue:
            return None

        current_pipe = game.queue[0]
        connections = PIPE_CONNECTIONS[current_pipe]

        # Find where flow will go next
        flow_col = game.flow_col
        flow_row = game.flow_row
        flow_dir = game.flow_dir

        # Calculate the next cell the flow will enter
        next_col, next_row = self._get_next_flow_cell(flow_col, flow_row, flow_dir)

        # Check if we can extend the path with current pipe at that location
        if self._is_valid_cell(next_col, next_row):
            if game.grid[next_row][next_col] == PipeType.EMPTY:
                # Check if current pipe connects from the flow direction
                if self._pipe_accepts_flow(current_pipe, flow_dir):
                    return (next_col, next_row)

        # Look further ahead - find cells along potential path
        best_score = -1
        best_pos = None

        for row in range(game.GRID_CELLS):
            for col in range(game.GRID_CELLS):
                if game.grid[row][col] != PipeType.EMPTY:
                    continue

                score = self._score_placement(col, row, current_pipe)
                if score > best_score:
                    best_score = score
                    best_pos = (col, row)

        return best_pos

    def _get_next_flow_cell(self, col, row, direction):
        """Get the next cell coordinates based on flow direction."""
        if direction == 'right':
            return (col + 1, row)
        elif direction == 'left':
            return (col - 1, row)
        elif direction == 'up':
            return (col, row - 1)
        elif direction == 'down':
            return (col, row + 1)
        return (col, row)

    def _is_valid_cell(self, col, row):
        """Check if coordinates are within the grid."""
        return 0 <= col < self.game.GRID_CELLS and 0 <= row < self.game.GRID_CELLS

    def _pipe_accepts_flow(self, pipe, from_dir):
        """Check if a pipe accepts flow from the given direction."""
        connections = PIPE_CONNECTIONS[pipe]
        up, down, left, right = connections

        # Flow entering from 'right' direction means it enters from the left side
        if from_dir == 'right':
            return left
        elif from_dir == 'left':
            return right
        elif from_dir == 'up':
            return down
        elif from_dir == 'down':
            return up
        return False

    def _score_placement(self, col, row, pipe):
        """
        Score a potential placement position.
        Higher score = better placement.
        """
        game = self.game
        score = 0

        # Prefer positions close to the current flow position
        dist_to_flow = abs(col - game.flow_col) + abs(row - game.flow_row)
        score -= dist_to_flow * 2

        # Prefer positions that could connect to existing pipes
        connections = PIPE_CONNECTIONS[pipe]
        up, down, left, right = connections

        # Check adjacent cells for connection opportunities
        if row > 0 and game.grid[row - 1][col] != PipeType.EMPTY:
            adj_pipe = game.grid[row - 1][col]
            adj_conn = PIPE_CONNECTIONS[adj_pipe]
            if up and adj_conn[1]:  # This pipe connects up, adjacent connects down
                score += 10

        if row < game.GRID_CELLS - 1 and game.grid[row + 1][col] != PipeType.EMPTY:
            adj_pipe = game.grid[row + 1][col]
            adj_conn = PIPE_CONNECTIONS[adj_pipe]
            if down and adj_conn[0]:  # This pipe connects down, adjacent connects up
                score += 10

        if col > 0 and game.grid[row][col - 1] != PipeType.EMPTY:
            adj_pipe = game.grid[row][col - 1]
            adj_conn = PIPE_CONNECTIONS[adj_pipe]
            if left and adj_conn[3]:  # This pipe connects left, adjacent connects right
                score += 10

        if col < game.GRID_CELLS - 1 and game.grid[row][col + 1] != PipeType.EMPTY:
            adj_pipe = game.grid[row][col + 1]
            adj_conn = PIPE_CONNECTIONS[adj_pipe]
            if right and adj_conn[2]:  # This pipe connects right, adjacent connects left
                score += 10

        # Penalize corners (less room to maneuver)
        if col == 0 or col == game.GRID_CELLS - 1:
            score -= 5
        if row == 0 or row == game.GRID_CELLS - 1:
            score -= 5

        # Bonus for being in the predicted flow path
        predicted_path = self._predict_flow_path()
        if (col, row) in predicted_path:
            path_index = predicted_path.index((col, row))
            score += 20 - path_index * 2  # Earlier in path = higher priority

        return score

    def _predict_flow_path(self):
        """
        Predict where the flow might go based on current direction.
        Returns list of (col, row) tuples.
        """
        game = self.game
        path = []

        col, row = game.flow_col, game.flow_row
        direction = game.flow_dir

        # Predict next few steps
        for _ in range(6):
            next_col, next_row = self._get_next_flow_cell(col, row, direction)

            if not self._is_valid_cell(next_col, next_row):
                break

            path.append((next_col, next_row))

            # Check if there's a pipe there that would change direction
            if game.grid[next_row][next_col] != PipeType.EMPTY:
                pipe = game.grid[next_row][next_col]
                new_dir = game.get_next_direction(pipe, direction)
                if new_dir:
                    direction = new_dir
                else:
                    break

            col, row = next_col, next_row

        return path

    def _should_place_here(self):
        """Decide if we should place a pipe at the current cursor position."""
        game = self.game

        # Don't place on start pipe
        if game.grid[game.cursor_y][game.cursor_x] == PipeType.START:
            return False

        # Don't replace filled pipes
        if game.flow[game.cursor_y][game.cursor_x] > 0:
            return False

        # Check if this placement helps the flow
        current_pipe = game.queue[0]

        # If we're on the predicted path, check if this pipe connects properly
        predicted = self._predict_flow_path()
        if (game.cursor_x, game.cursor_y) in predicted:
            idx = predicted.index((game.cursor_x, game.cursor_y))
            if idx == 0:
                # This is the immediate next cell - must connect!
                if self._pipe_accepts_flow(current_pipe, game.flow_dir):
                    return True
                # Wrong pipe for this position, but place anyway if empty
                # (might get lucky with flow direction changing)
                return game.grid[game.cursor_y][game.cursor_x] == PipeType.EMPTY

        # Otherwise, place if the cell is empty
        return game.grid[game.cursor_y][game.cursor_x] == PipeType.EMPTY
