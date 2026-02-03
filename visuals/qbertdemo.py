"""
Q*bert Demo - AI Attract Mode
==============================
Q*bert plays itself using simple AI for idle screen demos.
The AI hops around the pyramid coloring cubes while avoiding enemies.

AI Strategy:
- Avoid Coily (purple snake) - move away if on same row or adjacent
- Catch Slick/Sam if close (worth 300 points)
- Find nearest uncolored cube using BFS on pyramid graph
- Move in direction that gets closer to target
"""

from collections import deque
from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

# Import the actual game
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.qbert import QBert


class QBertDemo(Visual):
    name = "Q*BERT"
    description = "AI plays Q*bert"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = QBert(self.display)
        self.game.reset()
        self.decision_timer = 0.0
        self.decision_interval = 0.2  # Q*bert moves slowly with hops
        self.target_move = None  # (row, col) of intended move

    def handle_input(self, input_state):
        # Demo doesn't respond to input (auto-plays)
        return False

    def update(self, dt):
        self.time += dt

        # If game over, restart after a pause
        if self.game.state == GameState.GAME_OVER:
            self.decision_timer += dt
            if self.decision_timer > 3.0:
                self.game.reset()
                self.decision_timer = 0.0
            return

        # Make AI decisions periodically
        self.decision_timer += dt
        if self.decision_timer >= self.decision_interval:
            self.decision_timer = 0.0
            self.target_move = self._decide_move()

        # Create input state with AI's chosen direction
        ai_input = InputState()
        if self.target_move and not self.game.is_hopping and not self.game.on_disc:
            target_row, target_col = self.target_move
            qrow, qcol = self.game.qbert_row, self.game.qbert_col

            # Determine which direction to press based on target
            # up-left: row-1, col-1
            # up-right: row-1, col (same col)
            # down-left: row+1, col (same col)
            # down-right: row+1, col+1

            if target_row == qrow - 1 and target_col == qcol - 1:
                # up-left
                ai_input.up = True
                ai_input.left = True
            elif target_row == qrow - 1 and target_col == qcol:
                # up-right
                ai_input.up = True
                ai_input.right = True
            elif target_row == qrow + 1 and target_col == qcol:
                # down-left
                ai_input.down = True
                ai_input.left = True
            elif target_row == qrow + 1 and target_col == qcol + 1:
                # down-right
                ai_input.down = True
                ai_input.right = True

        self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()

        # Overlay "DEMO" text
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)

    def _decide_move(self):
        """AI decision-making for Q*bert movement."""
        game = self.game
        qrow, qcol = game.qbert_row, game.qbert_col

        # Don't decide if hopping or on disc
        if game.is_hopping or game.on_disc or game.level_complete:
            return None

        # Get all valid moves from current position
        valid_moves = self._get_valid_moves(qrow, qcol)
        if not valid_moves:
            return None

        # Check for Coily danger
        coily = self._find_coily()
        if coily:
            escape_move = self._get_escape_move(qrow, qcol, coily, valid_moves)
            if escape_move:
                return escape_move

        # Check for nearby Slick/Sam to catch
        catch_target = self._find_catchable_enemy(qrow, qcol, valid_moves)
        if catch_target:
            return catch_target

        # Find nearest uncolored cube
        target = self._find_nearest_uncolored(qrow, qcol)
        if target:
            # Get direction toward target using BFS
            next_move = self._get_move_toward_target(qrow, qcol, target)
            if next_move and next_move in valid_moves:
                return next_move

        # If no uncolored cubes, just pick a random valid move
        if valid_moves:
            import random
            return random.choice(valid_moves)

        return None

    def _get_valid_moves(self, row, col):
        """Get all valid adjacent cube positions."""
        moves = []
        game = self.game

        # Four diagonal directions
        candidates = [
            (row - 1, col - 1),  # up-left
            (row - 1, col),      # up-right
            (row + 1, col),      # down-left
            (row + 1, col + 1),  # down-right
        ]

        for r, c in candidates:
            if game.is_valid_cube(r, c):
                moves.append((r, c))

        return moves

    def _find_coily(self):
        """Find active Coily snake (not egg)."""
        for enemy in self.game.enemies:
            if enemy['type'] == 'coily' and not enemy.get('is_egg'):
                return enemy
        return None

    def _get_escape_move(self, qrow, qcol, coily, valid_moves):
        """Find a move that increases distance from Coily."""
        crow, ccol = coily['row'], coily['col']

        # Calculate Manhattan distance from Coily
        current_dist = abs(qrow - crow) + abs(qcol - ccol)

        # If Coily is close (within 2 tiles), try to escape
        if current_dist <= 3:
            best_move = None
            best_dist = current_dist

            for move in valid_moves:
                mrow, mcol = move
                dist = abs(mrow - crow) + abs(mcol - ccol)
                if dist > best_dist:
                    best_dist = dist
                    best_move = move

            return best_move

        return None

    def _find_catchable_enemy(self, qrow, qcol, valid_moves):
        """Find Slick/Sam that can be caught in one hop."""
        for enemy in self.game.enemies:
            if enemy['type'] in ['slick', 'sam']:
                erow, ecol = enemy['row'], enemy['col']
                if (erow, ecol) in valid_moves:
                    return (erow, ecol)
        return None

    def _find_nearest_uncolored(self, start_row, start_col):
        """BFS to find nearest uncolored cube."""
        game = self.game

        # If current cube is uncolored, stay (but we should still hop to trigger)
        # Actually, we need to find a target to move toward

        queue = deque([(start_row, start_col, 0)])
        visited = {(start_row, start_col)}

        while queue:
            row, col, dist = queue.popleft()

            # Check if this cube is uncolored (skip starting position)
            if dist > 0 and game.cubes[row][col] == 0:
                return (row, col)

            # Explore neighbors
            for nrow, ncol in self._get_valid_moves(row, col):
                if (nrow, ncol) not in visited:
                    visited.add((nrow, ncol))
                    queue.append((nrow, ncol, dist + 1))

        return None

    def _get_move_toward_target(self, start_row, start_col, target):
        """BFS to find the first move toward target."""
        target_row, target_col = target
        game = self.game

        # BFS storing the first move taken
        queue = deque([(start_row, start_col, None)])
        visited = {(start_row, start_col)}

        while queue:
            row, col, first_move = queue.popleft()

            if row == target_row and col == target_col:
                return first_move

            for nrow, ncol in self._get_valid_moves(row, col):
                if (nrow, ncol) not in visited:
                    visited.add((nrow, ncol))
                    # Track first move
                    move = first_move if first_move else (nrow, ncol)
                    queue.append((nrow, ncol, move))

        return None
