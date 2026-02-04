"""
Pipe Dream Demo - AI Attract Mode
==================================
Pipe Dream plays itself using strategic AI for idle screen demos.
The AI places pipes to keep the flow going as long as possible.

AI Strategy:
- Build a connected path AHEAD of the flow during countdown
- Always ensure the immediate next cell has a matching pipe
- Create serpentine paths to maximize pipe count
- Discard non-fitting pipes in safe locations away from the path
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

# Import the actual game
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.pipedream import PipeDream, PipeType, PIPE_CONNECTIONS


class PipeDreamDemo(Visual):
    name = "PIPE DREAM"
    description = "AI connects pipes"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = PipeDream(self.display)
        self.game.reset()
        self.decision_timer = 0.0
        self.decision_interval = 0.12  # Time between AI decisions
        self.current_action = None
        self.game_over_timer = 0.0
        self.target_x = None
        self.target_y = None
        self.place_cooldown = 0.0
        self.planned_path = []  # List of (col, row, direction_entering)

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
                self.planned_path = []
            return

        # Update cooldowns
        if self.place_cooldown > 0:
            self.place_cooldown -= dt

        # Make AI decisions periodically - only send input on decision frame
        ai_input = InputState()
        self.decision_timer += dt
        if self.decision_timer >= self.decision_interval:
            self.decision_timer = 0.0
            action = self._decide_action()

            # Apply the action for this frame only
            if action == 'up':
                ai_input.up = True
            elif action == 'down':
                ai_input.down = True
            elif action == 'left':
                ai_input.left = True
            elif action == 'right':
                ai_input.right = True
            elif action == 'place':
                ai_input.action_l = True
                self.place_cooldown = 0.25

        self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()

        # Overlay "DEMO" text (blinking)
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)

    def _decide_action(self):
        """AI decision-making for cursor movement and pipe placement."""
        game = self.game

        # Find the best target for the current pipe
        target = self._find_best_target()

        if target:
            self.target_x, self.target_y = target

        # If no target found, pick somewhere safe to discard
        if self.target_x is None or self.target_y is None:
            self.target_x, self.target_y = self._find_discard_location()

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
            # At target position - place pipe
            if self.place_cooldown <= 0 and self._can_place_here():
                self.target_x = None
                self.target_y = None
                return 'place'

        return None

    def _find_best_target(self):
        """Find the best location for the current pipe piece."""
        game = self.game

        if not game.queue:
            return None

        current_pipe = game.queue[0]

        # Get the current flow head and trace the path to find where we need pipes
        path_cells = self._trace_current_path()

        # Find the first empty cell in the path that needs a pipe
        for col, row, entry_dir in path_cells:
            if game.grid[row][col] == PipeType.EMPTY:
                # This cell needs a pipe! Does the current piece fit?
                if self._pipe_accepts_flow(current_pipe, entry_dir):
                    # Check that the pipe has a valid exit that doesn't lead off the grid
                    exit_dir = self._get_pipe_exit(current_pipe, entry_dir)
                    if exit_dir:
                        # Check if exit leads to a valid cell with room to maneuver
                        next_col, next_row = self._get_next_cell(col, row, exit_dir)
                        if self._is_valid_cell(next_col, next_row):
                            # Avoid placing if exit leads to edge (low maneuverability)
                            # unless flow is already started
                            if self._has_room_to_grow(next_col, next_row, exit_dir) or game.flow_started:
                                return (col, row)
                            # Exit leads to edge with no good options - discard
                            return self._find_discard_location()
                        # Exit leads off grid - discard this pipe
                        if not game.flow_started or game.flow_progress < 0.5:
                            return self._find_discard_location()
                        return (col, row)
                # Current pipe doesn't fit here - need to discard it elsewhere
                return self._find_discard_location()

        # Path is complete or blocked - look for ways to extend it
        if path_cells:
            last_col, last_row, last_dir = path_cells[-1]
            extension = self._find_path_extension(last_col, last_row, last_dir, current_pipe)
            if extension:
                return extension

        return None

    def _has_room_to_grow(self, col, row, direction):
        """Check if a cell has room to grow (not cornered)."""
        game = self.game

        # Count how many adjacent cells are available (not edges, not filled)
        available = 0
        for dc, dr, d in [(0, -1, 'up'), (0, 1, 'down'), (-1, 0, 'left'), (1, 0, 'right')]:
            nc, nr = col + dc, row + dr
            if self._is_valid_cell(nc, nr) and game.grid[nr][nc] == PipeType.EMPTY:
                available += 1

        # If going toward an edge, require at least 2 escape routes
        edge_count = 0
        if col == 0 or col == game.GRID_CELLS - 1:
            edge_count += 1
        if row == 0 or row == game.GRID_CELLS - 1:
            edge_count += 1

        # Corner cells (2 edges) need at least 1 available
        # Edge cells (1 edge) need at least 2 available
        # Center cells always ok
        if edge_count >= 2:
            return available >= 1
        elif edge_count == 1:
            return available >= 2
        return True

    def _trace_current_path(self):
        """
        Trace the path from flow head through existing pipes.
        Returns list of (col, row, entry_direction) for cells the flow will visit.
        """
        game = self.game
        path = []

        col, row = game.flow_col, game.flow_row
        direction = game.flow_dir
        visited = set()

        # Start from the cell AFTER current flow position
        for _ in range(game.GRID_CELLS * game.GRID_CELLS):
            # Get next cell
            next_col, next_row = self._get_next_cell(col, row, direction)

            if not self._is_valid_cell(next_col, next_row):
                break

            if (next_col, next_row) in visited:
                break  # Avoid infinite loops
            visited.add((next_col, next_row))

            # Record this cell with the direction flow enters from
            path.append((next_col, next_row, direction))

            # Check what's in this cell
            pipe = game.grid[next_row][next_col]
            if pipe == PipeType.EMPTY:
                break  # Path ends here - needs a pipe

            # Get exit direction from this pipe
            exit_dir = self._get_pipe_exit(pipe, direction)
            if exit_dir is None:
                break  # Dead end

            col, row = next_col, next_row
            direction = exit_dir

        return path

    def _get_next_cell(self, col, row, direction):
        """Get the next cell coordinates based on direction."""
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
        """Check if a pipe accepts flow coming FROM the given direction."""
        connections = PIPE_CONNECTIONS[pipe]
        up, down, left, right = connections

        # Flow coming FROM 'right' means it enters the LEFT side of this pipe
        if from_dir == 'right':
            return left
        elif from_dir == 'left':
            return right
        elif from_dir == 'up':
            return down
        elif from_dir == 'down':
            return up
        return False

    def _get_pipe_exit(self, pipe, entry_dir):
        """
        Get the exit direction when flow enters a pipe from entry_dir.
        Returns None if the pipe doesn't accept flow from that direction.
        """
        if not self._pipe_accepts_flow(pipe, entry_dir):
            return None

        connections = PIPE_CONNECTIONS[pipe]
        up, down, left, right = connections

        # Entry side is opposite of entry_dir
        entry_side = {'right': 'left', 'left': 'right', 'up': 'down', 'down': 'up'}[entry_dir]

        # Find exit (a connected side that isn't the entry)
        exits = []
        if up and entry_side != 'up':
            exits.append('up')
        if down and entry_side != 'down':
            exits.append('down')
        if left and entry_side != 'left':
            exits.append('left')
        if right and entry_side != 'right':
            exits.append('right')

        if not exits:
            return None

        # For cross pipes, prefer continuing straight
        if entry_dir in exits:
            return entry_dir
        return exits[0]

    def _find_path_extension(self, last_col, last_row, last_dir, current_pipe):
        """
        Find where to place current_pipe to extend the path from the last cell.
        """
        game = self.game

        # Get the pipe at the last filled cell
        last_pipe = game.grid[last_row][last_col]
        if last_pipe == PipeType.EMPTY:
            return None

        # Get where the path would exit
        exit_dir = self._get_pipe_exit(last_pipe, last_dir)
        if exit_dir is None:
            return None

        # Get the next cell after the path
        next_col, next_row = self._get_next_cell(last_col, last_row, exit_dir)

        if not self._is_valid_cell(next_col, next_row):
            return None

        if game.grid[next_row][next_col] != PipeType.EMPTY:
            return None

        # Check if current pipe fits here
        if self._pipe_accepts_flow(current_pipe, exit_dir):
            return (next_col, next_row)

        return None

    def _find_discard_location(self):
        """Find a safe place to discard a pipe that doesn't fit the path."""
        game = self.game

        # Build a danger zone - all cells that MIGHT be on the flow path
        danger_cells = set()

        # Add all cells currently in the path
        path = self._trace_current_path()
        for col, row, _ in path:
            danger_cells.add((col, row))
            # Also mark neighbors as risky
            for dc, dr in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                danger_cells.add((col + dc, row + dr))

        # Add cells in the general "flow corridor" - from start to opposite edge
        start_row = game.start_row
        for c in range(game.GRID_CELLS):
            for r in range(max(0, start_row - 2), min(game.GRID_CELLS, start_row + 3)):
                danger_cells.add((c, r))

        # Find closest safe empty cell, preferring edges/corners
        best_cell = None
        best_score = -999

        for row in range(game.GRID_CELLS):
            for col in range(game.GRID_CELLS):
                if game.grid[row][col] != PipeType.EMPTY:
                    continue
                if (col, row) in danger_cells:
                    continue

                # Score based on: distance from cursor (closer is better) + edge bonus
                dist = abs(col - game.cursor_x) + abs(row - game.cursor_y)
                edge_bonus = 0
                if row == 0 or row == game.GRID_CELLS - 1:
                    edge_bonus += 3
                if col == 0 or col == game.GRID_CELLS - 1:
                    edge_bonus += 3

                score = edge_bonus - dist  # Prefer edges, but not too far
                if score > best_score:
                    best_score = score
                    best_cell = (col, row)

        if best_cell:
            return best_cell

        # If all safe cells are taken, find ANY empty cell far from flow
        best_cell = None
        best_dist = -1
        for row in range(game.GRID_CELLS):
            for col in range(game.GRID_CELLS):
                if game.grid[row][col] != PipeType.EMPTY:
                    continue
                dist = abs(col - game.flow_col) + abs(row - game.flow_row)
                if dist > best_dist:
                    best_dist = dist
                    best_cell = (col, row)

        if best_cell:
            return best_cell

        return (game.cursor_x, game.cursor_y)

    def _can_place_here(self):
        """Check if we can place a pipe at the current cursor position."""
        game = self.game

        # Can't place on start
        if game.grid[game.cursor_y][game.cursor_x] == PipeType.START:
            return False

        # Can't replace filled pipes
        if game.flow[game.cursor_y][game.cursor_x] > 0:
            return False

        return True
