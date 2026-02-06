"""
Chess Demo - AI vs AI Attract Mode
==================================
Two chess AIs play against each other for idle screen demos.

AI emulates the Bernstein Chess Program (1957) - one of the first
complete chess programs, developed by Alex Bernstein at IBM.

Historical AI Strategy:
- 4-ply minimax search (2 moves ahead per side)
- Only considers 7 "most plausible" moves per position
- Evaluation: material, mobility, area control, king defense
- Original ran on IBM 704, took ~8 minutes per move

Reference: https://www.chessprogramming.org/The_Bernstein_Chess_Program
"""

import random
from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.chess import Chess, WHITE, BLACK, KING, QUEEN, ROOK, BISHOP, KNIGHT, PAWN


# Piece values - classic Bernstein style (simple integer values)
PIECE_VALUES = {
    PAWN: 1,
    KNIGHT: 3,
    BISHOP: 3,
    ROOK: 5,
    QUEEN: 9,
    KING: 100,  # Effectively infinite for checkmate detection
}


class BernsteinAI:
    """
    Fast Chess AI inspired by Bernstein Chess Program (1957).

    Optimized for Pi 3 real-time play:
    - 2-ply search (1 move ahead per side)
    - Selective search: only 7 most plausible moves
    - Fast evaluation: material + piece-square tables (no mobility)
    - Alpha-beta pruning for speed
    """

    MAX_PLAUSIBLE_MOVES = 7  # Bernstein's key innovation
    SEARCH_DEPTH = 2  # Reduced for speed

    # Piece-square tables for positional bonuses (simplified)
    # Positive = good for piece to be there
    PAWN_TABLE = [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [5, 5, 5, 5, 5, 5, 5, 5],
        [1, 1, 2, 3, 3, 2, 1, 1],
        [0, 0, 1, 2, 2, 1, 0, 0],
        [0, 0, 0, 2, 2, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
    ]

    KNIGHT_TABLE = [
        [0, 1, 1, 1, 1, 1, 1, 0],
        [1, 2, 2, 2, 2, 2, 2, 1],
        [1, 2, 3, 3, 3, 3, 2, 1],
        [1, 2, 3, 3, 3, 3, 2, 1],
        [1, 2, 3, 3, 3, 3, 2, 1],
        [1, 2, 3, 3, 3, 3, 2, 1],
        [1, 2, 2, 2, 2, 2, 2, 1],
        [0, 1, 1, 1, 1, 1, 1, 0],
    ]

    CENTER_BONUS = [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 1, 1, 1, 0, 0],
        [0, 1, 2, 2, 2, 2, 1, 0],
        [0, 1, 2, 3, 3, 2, 1, 0],
        [0, 1, 2, 3, 3, 2, 1, 0],
        [0, 1, 2, 2, 2, 2, 1, 0],
        [0, 0, 1, 1, 1, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
    ]

    OPENING_MOVES = 4  # Per side: add variety for first N moves
    OPENING_JITTER = 8  # Extra randomness during opening

    def __init__(self):
        self._move_stack = []
        self.move_count = 0

    def get_best_move(self, game, color):
        """Find the best move using selective search with alpha-beta."""
        moves = self._get_plausible_moves(game, color)
        if not moves:
            return None

        best_move = None
        best_score = float('-inf')
        alpha = float('-inf')
        beta = float('inf')

        for from_pos, to_pos in moves:
            self._make_temp_move(game, from_pos, to_pos)

            enemy = BLACK if color == WHITE else WHITE
            score = -self._alphabeta(game, self.SEARCH_DEPTH - 1, -beta, -alpha, enemy)

            self._undo_temp_move(game)

            if score > best_score:
                best_score = score
                best_move = (from_pos, to_pos)

            alpha = max(alpha, score)

        return best_move

    def _get_plausible_moves(self, game, color):
        """Get the 7 most plausible moves - fast scoring."""
        all_moves = []
        for y in range(8):
            for x in range(8):
                piece = game.get_piece(x, y)
                if piece and piece.color == color:
                    for to_pos in game.get_legal_moves(x, y):
                        all_moves.append(((x, y), to_pos))

        if not all_moves:
            return []

        # Fast move scoring (no expensive checks)
        scored_moves = []

        for from_pos, to_pos in all_moves:
            score = 0
            fx, fy = from_pos
            tx, ty = to_pos
            piece = game.get_piece(fx, fy)
            captured = game.get_piece(tx, ty)

            # Captures - MVV-LVA (Most Valuable Victim - Least Valuable Attacker)
            if captured:
                score += 100 + PIECE_VALUES[captured.type] * 10 - PIECE_VALUES[piece.type]

            # Center control bonus
            score += self.CENTER_BONUS[ty][tx]

            # Piece development
            if piece.type in [KNIGHT, BISHOP]:
                back_rank = 7 if color == WHITE else 0
                if fy == back_rank:
                    score += 5

            # Castling
            if piece.type == KING and abs(tx - fx) == 2:
                score += 15

            # Pawn advancement toward promotion
            if piece.type == PAWN:
                promo_rank = 0 if color == WHITE else 7
                if ty == promo_rank:
                    score += 50
                else:
                    # Use pawn table (flip for black)
                    table_y = ty if color == WHITE else 7 - ty
                    score += self.PAWN_TABLE[table_y][tx]

            # Opening variety: extra jitter for the first few moves per side
            if self.move_count < self.OPENING_MOVES * 2:
                score += random.randint(0, self.OPENING_JITTER)
            else:
                score += random.randint(0, 2)

            scored_moves.append((score, random.random(), from_pos, to_pos))

        scored_moves.sort(reverse=True)
        return [(m[2], m[3]) for m in scored_moves[:self.MAX_PLAUSIBLE_MOVES]]

    def _alphabeta(self, game, depth, alpha, beta, color):
        """Alpha-beta search for speed."""
        if depth == 0:
            return self._evaluate(game, color)

        moves = self._get_plausible_moves(game, color)
        if not moves:
            king_pos = game.find_king(color)
            enemy = BLACK if color == WHITE else WHITE
            if king_pos and game.is_square_attacked(king_pos[0], king_pos[1], enemy):
                return -1000
            return 0

        for from_pos, to_pos in moves:
            self._make_temp_move(game, from_pos, to_pos)

            enemy = BLACK if color == WHITE else WHITE
            score = -self._alphabeta(game, depth - 1, -beta, -alpha, enemy)

            self._undo_temp_move(game)

            if score >= beta:
                return beta  # Beta cutoff
            alpha = max(alpha, score)

        return alpha

    def _evaluate(self, game, color):
        """Fast evaluation: material + piece positions only."""
        score = 0
        enemy = BLACK if color == WHITE else WHITE

        for y in range(8):
            for x in range(8):
                piece = game.get_piece(x, y)
                if not piece:
                    continue

                # Material value
                value = PIECE_VALUES[piece.type] * 10

                # Positional bonus
                if piece.type == PAWN:
                    table_y = y if piece.color == WHITE else 7 - y
                    value += self.PAWN_TABLE[table_y][x]
                elif piece.type == KNIGHT:
                    value += self.KNIGHT_TABLE[y][x]
                elif piece.type in [BISHOP, QUEEN]:
                    value += self.CENTER_BONUS[y][x]

                if piece.color == color:
                    score += value
                else:
                    score -= value

        return score

    def _make_temp_move(self, game, from_pos, to_pos):
        """Make a temporary move for evaluation (uses stack for recursion)."""
        fx, fy = from_pos
        tx, ty = to_pos
        piece = game.board[fy][fx]
        captured = game.board[ty][tx]

        if piece is None:
            self._move_stack.append({'valid': False})
            return

        # Store state for undo
        state = {
            'valid': True,
            'from': from_pos,
            'to': to_pos,
            'piece': piece,
            'captured': captured,
            'en_passant': game.en_passant_target,
            'has_moved': piece.has_moved,
        }

        # Handle en passant capture
        if piece.type == PAWN and (tx, ty) == game.en_passant_target:
            ep_y = ty + (1 if piece.color == WHITE else -1)
            state['ep_captured'] = game.board[ep_y][tx]
            state['ep_pos'] = (tx, ep_y)
            game.board[ep_y][tx] = None

        # Handle castling
        if piece.type == KING and abs(tx - fx) == 2:
            if tx == 6:  # Kingside
                rook = game.board[ty][7]
                state['castle'] = ('kingside', rook, rook.has_moved if rook else False)
                game.board[ty][7] = None
                game.board[ty][5] = rook
                if rook:
                    rook.has_moved = True
            elif tx == 2:  # Queenside
                rook = game.board[ty][0]
                state['castle'] = ('queenside', rook, rook.has_moved if rook else False)
                game.board[ty][0] = None
                game.board[ty][3] = rook
                if rook:
                    rook.has_moved = True

        # Push state to stack before making move
        self._move_stack.append(state)

        # Make the move
        game.board[ty][tx] = piece
        game.board[fy][fx] = None
        piece.has_moved = True

        # Update en passant target
        game.en_passant_target = None
        if piece.type == PAWN and abs(ty - fy) == 2:
            game.en_passant_target = (tx, (fy + ty) // 2)

    def _undo_temp_move(self, game):
        """Undo the temporary move (pops from stack)."""
        if not self._move_stack:
            return

        state = self._move_stack.pop()

        if not state.get('valid', False):
            return

        fx, fy = state['from']
        tx, ty = state['to']

        game.board[fy][fx] = state['piece']
        game.board[ty][tx] = state['captured']
        game.en_passant_target = state['en_passant']
        state['piece'].has_moved = state['has_moved']

        # Restore en passant captured piece
        if 'ep_captured' in state:
            ex, ey = state['ep_pos']
            game.board[ey][ex] = state['ep_captured']

        # Restore castling
        if 'castle' in state:
            castle_type, rook, rook_had_moved = state['castle']
            if castle_type == 'kingside':
                game.board[ty][5] = None
                game.board[ty][7] = rook
            else:  # queenside
                game.board[ty][3] = None
                game.board[ty][0] = rook
            if rook:
                rook.has_moved = rook_had_moved


class ChessDemo(Visual):
    name = "CHESS"
    description = "AI vs AI chess"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = Chess(self.display)
        self.game.reset()
        self.ai = BernsteinAI()  # Historical 1957 AI
        self.move_timer = 0.0
        self.move_delay = 1.0  # Time between moves
        self.game_over_timer = 0.0
        self.thinking = False
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
                self.ai.move_count = 0
                self.game_over_timer = 0.0
                self.pending_move = None
            return

        # Handle pawn promotion automatically (always queen)
        if self.game.promoting_pawn:
            self.game.promote_pawn(QUEEN)
            return

        # Wait between moves for visual effect
        self.move_timer += dt
        if self.move_timer < self.move_delay:
            return

        # Get AI move
        if self.pending_move is None:
            self.pending_move = self.ai.get_best_move(self.game, self.game.current_turn)

        if self.pending_move:
            from_pos, to_pos = self.pending_move
            self.game.make_move(from_pos[0], from_pos[1], to_pos[0], to_pos[1])
            self.ai.move_count += 1
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
