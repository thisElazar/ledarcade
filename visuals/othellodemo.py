"""
Othello Demo - AI vs AI Attract Mode
====================================
Two AIs play Othello against each other for idle screen demos.

AI emulates Iago/Logistello style programs from the 1980s - the era
when Othello programs first achieved master-level play.

Historical AI Strategy:
- Corner control is paramount (corners can never be flipped)
- Edge stability - pieces on edges are hard to flip
- Mobility - having more moves available is good
- Disc count only matters in endgame
- Avoid "X-squares" (diagonal to corners) and "C-squares" (adjacent to corners)

Reference: https://en.wikipedia.org/wiki/Computer_Othello
"""

import random
from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.othello import Othello, PLAYER_1, PLAYER_2


class IagoAI:
    """
    Othello AI emulating 1980s programs like Iago and Logistello.

    Key insight: Position matters more than piece count until endgame.
    Corners are worth ~25 pieces. X-squares (diagonal to corner) are
    dangerous because they give opponent access to corners.
    """

    SEARCH_DEPTH = 4  # 4-ply search (fast on Pi)

    # Position values - corners are king, X-squares are death
    # Based on classic Othello strategy guides
    POSITION_WEIGHTS = [
        [100, -20,  10,   5,   5,  10, -20, 100],
        [-20, -50,  -2,  -2,  -2,  -2, -50, -20],
        [ 10,  -2,   1,   1,   1,   1,  -2,  10],
        [  5,  -2,   1,   0,   0,   1,  -2,   5],
        [  5,  -2,   1,   0,   0,   1,  -2,   5],
        [ 10,  -2,   1,   1,   1,   1,  -2,  10],
        [-20, -50,  -2,  -2,  -2,  -2, -50, -20],
        [100, -20,  10,   5,   5,  10, -20, 100],
    ]

    # Corner positions
    CORNERS = [(0, 0), (0, 7), (7, 0), (7, 7)]

    # X-squares (diagonal to corners) - very dangerous
    X_SQUARES = [(1, 1), (1, 6), (6, 1), (6, 6)]

    # C-squares (adjacent to corners) - somewhat dangerous
    C_SQUARES = [(0, 1), (1, 0), (0, 6), (1, 7), (6, 0), (7, 1), (6, 7), (7, 6)]

    def __init__(self):
        self._move_stack = []

    def get_best_move(self, game, player):
        """Find the best move using alpha-beta search."""
        moves = game.get_valid_moves(player)
        if not moves:
            return None

        best_move = None
        best_score = float('-inf')
        alpha = float('-inf')
        beta = float('inf')

        # Order moves: corners first, then edges, avoid X-squares
        moves = self._order_moves(moves, game)

        for col, row in moves:
            self._make_temp_move(game, col, row, player)

            opponent = PLAYER_2 if player == PLAYER_1 else PLAYER_1
            score = -self._alphabeta(game, self.SEARCH_DEPTH - 1, -beta, -alpha, opponent)

            self._undo_temp_move(game)

            if score > best_score:
                best_score = score
                best_move = (col, row)

            alpha = max(alpha, score)

        return best_move

    def _order_moves(self, moves, game):
        """Order moves for better alpha-beta pruning."""
        scored = []
        for col, row in moves:
            # Quick heuristic for move ordering
            score = self.POSITION_WEIGHTS[row][col]
            # Bonus for corners
            if (col, row) in self.CORNERS:
                score += 1000
            scored.append((score, random.random(), col, row))

        scored.sort(reverse=True)
        return [(m[2], m[3]) for m in scored]

    def _alphabeta(self, game, depth, alpha, beta, player):
        """Alpha-beta search."""
        # Count total pieces to detect endgame
        total_pieces = sum(1 for r in range(8) for c in range(8) if game.board[r][c] != 0)

        if depth == 0 or total_pieces >= 60:
            return self._evaluate(game, player, total_pieces)

        moves = game.get_valid_moves(player)

        if not moves:
            # Must pass - check if opponent can move
            opponent = PLAYER_2 if player == PLAYER_1 else PLAYER_1
            opp_moves = game.get_valid_moves(opponent)
            if not opp_moves:
                # Game over - count pieces
                return self._final_score(game, player)
            # Pass to opponent
            return -self._alphabeta(game, depth - 1, -beta, -alpha, opponent)

        moves = self._order_moves(moves, game)

        for col, row in moves:
            self._make_temp_move(game, col, row, player)

            opponent = PLAYER_2 if player == PLAYER_1 else PLAYER_1
            score = -self._alphabeta(game, depth - 1, -beta, -alpha, opponent)

            self._undo_temp_move(game)

            if score >= beta:
                return beta
            alpha = max(alpha, score)

        return alpha

    def _evaluate(self, game, player, total_pieces):
        """
        Iago-style evaluation:
        1. Corner control (huge)
        2. Position weights (avoid X-squares)
        3. Mobility (number of moves)
        4. Disc count (only in endgame)
        """
        opponent = PLAYER_2 if player == PLAYER_1 else PLAYER_1
        score = 0

        # Position-based evaluation
        position_score = 0
        my_pieces = 0
        opp_pieces = 0

        for row in range(8):
            for col in range(8):
                piece = game.board[row][col]
                if piece == player:
                    position_score += self.POSITION_WEIGHTS[row][col]
                    my_pieces += 1
                elif piece == opponent:
                    position_score -= self.POSITION_WEIGHTS[row][col]
                    opp_pieces += 1

        score += position_score

        # Corner ownership is critical - adjust nearby square values
        for corner_col, corner_row in self.CORNERS:
            if game.board[corner_row][corner_col] == player:
                score += 25  # Corner bonus
            elif game.board[corner_row][corner_col] == opponent:
                score -= 25

        # Mobility: more moves = more options
        my_mobility = len(game.get_valid_moves(player))
        opp_mobility = len(game.get_valid_moves(opponent))
        mobility_score = (my_mobility - opp_mobility) * 5

        # In early/mid game, mobility matters more than disc count
        # In endgame (>50 pieces), disc count matters
        if total_pieces < 50:
            score += mobility_score
        else:
            # Endgame: disc count matters
            score += (my_pieces - opp_pieces) * 3

        return score

    def _final_score(self, game, player):
        """Score for completed game."""
        opponent = PLAYER_2 if player == PLAYER_1 else PLAYER_1
        my_count = 0
        opp_count = 0

        for row in range(8):
            for col in range(8):
                if game.board[row][col] == player:
                    my_count += 1
                elif game.board[row][col] == opponent:
                    opp_count += 1

        if my_count > opp_count:
            return 1000 + (my_count - opp_count)
        elif opp_count > my_count:
            return -1000 - (opp_count - my_count)
        return 0

    def _make_temp_move(self, game, col, row, player):
        """Make a temporary move for evaluation."""
        # Get flips before making move
        flips = game.get_flips(col, row, player)

        # Store state
        state = {
            'col': col,
            'row': row,
            'player': player,
            'flips': flips,
            'original_values': {}
        }

        # Store original values of flipped cells
        for flip_col, flip_row in flips:
            state['original_values'][(flip_col, flip_row)] = game.board[flip_row][flip_col]

        self._move_stack.append(state)

        # Make the move
        game.board[row][col] = player
        for flip_col, flip_row in flips:
            game.board[flip_row][flip_col] = player

    def _undo_temp_move(self, game):
        """Undo a temporary move."""
        if not self._move_stack:
            return

        state = self._move_stack.pop()

        # Remove placed piece
        game.board[state['row']][state['col']] = 0

        # Restore flipped pieces
        for (flip_col, flip_row), original in state['original_values'].items():
            game.board[flip_row][flip_col] = original


class OthelloDemo(Visual):
    name = "OTHELLO"
    description = "AI vs AI Othello"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = Othello(self.display)
        self.game.reset()
        self.ai = IagoAI()
        self.move_timer = 0.0
        self.move_delay = 0.6  # Time between moves
        self.game_over_timer = 0.0
        self.pending_move = None

    def handle_input(self, input_state):
        return False

    def update(self, dt):
        self.time += dt

        # If game over, restart after a pause
        if self.game.state == GameState.GAME_OVER:
            self.game_over_timer += dt
            if self.game_over_timer > 5.0:
                self.game.reset()
                self.game_over_timer = 0.0
                self.pending_move = None
            return

        # Wait for flip animation to complete
        if self.game.flipping:
            self.game.flip_timer += dt
            if self.game.flip_timer >= self.game.FLIP_DURATION:
                self.game.finish_flip()
            return

        # Wait between moves for visual effect
        self.move_timer += dt
        if self.move_timer < self.move_delay:
            return

        # Check if current player has moves
        if not self.game.valid_moves:
            # No moves - game handles pass/end automatically in finish_flip
            return

        # Get AI move
        if self.pending_move is None:
            self.pending_move = self.ai.get_best_move(self.game, self.game.current_player)

        if self.pending_move:
            col, row = self.pending_move
            self.game.make_move(col, row)
            self.pending_move = None
            self.move_timer = 0.0

    def draw(self):
        # Hide cursor by moving it off-board
        self.game.cursor_x = -1
        self.game.cursor_y = -1
        self.game.draw()

        # Overlay "DEMO" text
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)
