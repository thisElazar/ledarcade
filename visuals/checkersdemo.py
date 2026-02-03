"""
Checkers Demo - AI vs AI Attract Mode
=====================================
Two AIs play checkers against each other for idle screen demos.

AI emulates Arthur Samuel's Checkers Program (1959) - the pioneering
machine learning program developed at IBM that beat a Connecticut
state champion in 1962.

Historical AI Strategy:
- Alpha-beta search with 4-6 ply depth
- Evaluation features: piece count, kings, advancement, center control
- "Piece advantage" and "denial of occupancy" heuristics
- Original learned feature weights through self-play

Reference: https://en.wikipedia.org/wiki/Arthur_Samuel#Checkers_program
"""

import random
from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.checkers import Checkers, PLAYER_1, PLAYER_2


class SamuelAI:
    """
    Checkers AI emulating Arthur Samuel's program (1959).

    Samuel's key innovations:
    - One of the first programs to use machine learning
    - Evaluated positions using weighted features
    - Used alpha-beta pruning for efficient search
    """

    SEARCH_DEPTH = 4  # 4-ply search

    # Positional bonus for advancement (encouraging forward movement)
    # Row 0 = opponent's back rank (promotion), Row 7 = our back rank
    ADVANCE_BONUS_P1 = [7, 6, 5, 4, 3, 2, 1, 0]  # P1 moves up (row 0 = goal)
    ADVANCE_BONUS_P2 = [0, 1, 2, 3, 4, 5, 6, 7]  # P2 moves down (row 7 = goal)

    # Center control bonus - Samuel valued "area control"
    CENTER_BONUS = [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 0, 1, 1, 0, 1, 0],
        [0, 0, 2, 0, 0, 2, 0, 0],
        [0, 1, 0, 3, 3, 0, 1, 0],
        [0, 1, 0, 3, 3, 0, 1, 0],
        [0, 0, 2, 0, 0, 2, 0, 0],
        [0, 1, 0, 1, 1, 0, 1, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
    ]

    def __init__(self):
        self._move_stack = []

    def get_best_move(self, game, player):
        """Find the best move using alpha-beta search."""
        moves = self._get_all_moves(game, player)
        if not moves:
            return None

        # Prioritize jumps (mandatory in checkers)
        jump_moves = [m for m in moves if m['is_jump']]
        if jump_moves:
            moves = jump_moves

        best_move = None
        best_score = float('-inf')
        alpha = float('-inf')
        beta = float('inf')

        # Shuffle for variety
        random.shuffle(moves)

        for move in moves:
            self._make_temp_move(game, move)

            opponent = PLAYER_2 if player == PLAYER_1 else PLAYER_1
            score = -self._alphabeta(game, self.SEARCH_DEPTH - 1, -beta, -alpha, opponent)

            self._undo_temp_move(game)

            if score > best_score:
                best_score = score
                best_move = move

            alpha = max(alpha, score)

        return best_move

    def _get_all_moves(self, game, player):
        """Get all legal moves for a player."""
        moves = []
        for row in range(8):
            for col in range(8):
                piece = game.get_piece(col, row)
                if piece and piece.player == player:
                    regular, jumps = game.get_moves_for_piece(col, row)

                    for to_col, to_row in jumps:
                        moves.append({
                            'from': (col, row),
                            'to': (to_col, to_row),
                            'is_jump': True
                        })

                    for to_col, to_row in regular:
                        moves.append({
                            'from': (col, row),
                            'to': (to_col, to_row),
                            'is_jump': False
                        })

        return moves

    def _alphabeta(self, game, depth, alpha, beta, player):
        """Alpha-beta search."""
        if depth == 0:
            return self._evaluate(game, player)

        moves = self._get_all_moves(game, player)

        # No moves = loss (can't move)
        if not moves:
            return -500

        # Must take jumps
        jump_moves = [m for m in moves if m['is_jump']]
        if jump_moves:
            moves = jump_moves

        for move in moves:
            self._make_temp_move(game, move)

            opponent = PLAYER_2 if player == PLAYER_1 else PLAYER_1
            score = -self._alphabeta(game, depth - 1, -beta, -alpha, opponent)

            self._undo_temp_move(game)

            if score >= beta:
                return beta
            alpha = max(alpha, score)

        return alpha

    def _evaluate(self, game, player):
        """
        Samuel's evaluation features:
        1. Piece count (kings worth more)
        2. Advancement toward promotion
        3. Center control
        4. Back row defense (keeps back row pieces for defense)
        """
        score = 0
        opponent = PLAYER_2 if player == PLAYER_1 else PLAYER_1

        my_pieces = 0
        my_kings = 0
        opp_pieces = 0
        opp_kings = 0
        my_advance = 0
        opp_advance = 0
        my_center = 0
        opp_center = 0

        for row in range(8):
            for col in range(8):
                piece = game.get_piece(col, row)
                if not piece:
                    continue

                is_mine = piece.player == player

                # Piece count
                if is_mine:
                    my_pieces += 1
                    if piece.is_king:
                        my_kings += 1
                else:
                    opp_pieces += 1
                    if piece.is_king:
                        opp_kings += 1

                # Advancement bonus (not for kings - they can move both ways)
                if not piece.is_king:
                    if piece.player == PLAYER_1:
                        adv = self.ADVANCE_BONUS_P1[row]
                    else:
                        adv = self.ADVANCE_BONUS_P2[row]

                    if is_mine:
                        my_advance += adv
                    else:
                        opp_advance += adv

                # Center control
                center = self.CENTER_BONUS[row][col]
                if is_mine:
                    my_center += center
                else:
                    opp_center += center

        # Samuel's weighted combination
        # Pieces: regular=30, king=50 (kings are valuable)
        piece_score = (my_pieces * 30 + my_kings * 50) - (opp_pieces * 30 + opp_kings * 50)

        # Advancement encourages pushing forward
        advance_score = (my_advance - opp_advance) * 2

        # Center control
        center_score = (my_center - opp_center) * 3

        score = piece_score + advance_score + center_score

        return score

    def _make_temp_move(self, game, move):
        """Make a temporary move for evaluation."""
        from_col, from_row = move['from']
        to_col, to_row = move['to']

        piece = game.board[from_row][from_col]
        captured = None
        captured_pos = None

        # Handle jump capture
        if move['is_jump']:
            cap_row = (from_row + to_row) // 2
            cap_col = (from_col + to_col) // 2
            captured = game.board[cap_row][cap_col]
            captured_pos = (cap_col, cap_row)
            game.board[cap_row][cap_col] = None

        # Store state
        was_king = piece.is_king

        # Make move
        game.board[to_row][to_col] = piece
        game.board[from_row][from_col] = None

        # Check promotion
        promoted = False
        if piece.player == PLAYER_1 and to_row == 0 and not piece.is_king:
            piece.is_king = True
            promoted = True
        elif piece.player == PLAYER_2 and to_row == 7 and not piece.is_king:
            piece.is_king = True
            promoted = True

        self._move_stack.append({
            'from': (from_col, from_row),
            'to': (to_col, to_row),
            'piece': piece,
            'captured': captured,
            'captured_pos': captured_pos,
            'was_king': was_king,
            'promoted': promoted,
        })

    def _undo_temp_move(self, game):
        """Undo a temporary move."""
        if not self._move_stack:
            return

        state = self._move_stack.pop()
        from_col, from_row = state['from']
        to_col, to_row = state['to']
        piece = state['piece']

        # Undo promotion
        if state['promoted']:
            piece.is_king = state['was_king']

        # Move piece back
        game.board[from_row][from_col] = piece
        game.board[to_row][to_col] = None

        # Restore captured piece
        if state['captured']:
            cap_col, cap_row = state['captured_pos']
            game.board[cap_row][cap_col] = state['captured']


class CheckersDemo(Visual):
    name = "CHECKERS"
    description = "AI vs AI checkers"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = Checkers(self.display)
        self.game.reset()
        self.ai = SamuelAI()
        self.move_timer = 0.0
        self.move_delay = 0.8  # Time between moves
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

        # Wait between moves for visual effect
        self.move_timer += dt
        if self.move_timer < self.move_delay:
            return

        # Handle multi-jump sequences
        if self.game.multi_jump_pos:
            # Continue the multi-jump
            more_jumps = self.game.can_continue_jumping(
                self.game.multi_jump_pos[0],
                self.game.multi_jump_pos[1]
            )
            if more_jumps:
                to_col, to_row = more_jumps[0]  # Take first available jump
                self.game.make_move(
                    self.game.multi_jump_pos[0],
                    self.game.multi_jump_pos[1],
                    to_col, to_row
                )
                self.move_timer = 0.0
                return

        # Get AI move
        if self.pending_move is None:
            self.pending_move = self.ai.get_best_move(self.game, self.game.current_player)

        if self.pending_move:
            from_col, from_row = self.pending_move['from']
            to_col, to_row = self.pending_move['to']
            self.game.make_move(from_col, from_row, to_col, to_row)
            self.pending_move = None
            self.move_timer = 0.0

    def draw(self):
        # Hide cursor
        self.game.cursor_x = -1
        self.game.cursor_y = -1
        self.game.draw()

        # Overlay "DEMO" text
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)
