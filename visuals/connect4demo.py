"""
Connect 4 Demo - AI vs AI Attract Mode
=======================================
Two AIs play Connect 4 using minimax with alpha-beta pruning.

AI Strategy:
- Negamax with alpha-beta, depth 7
- Move ordering: center columns first [3, 2, 4, 1, 5, 0, 6]
- Evaluation: center control, 4-window scoring (3-in-a-row threats,
  2-in-a-row setups, opponent threat penalties)
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState
import random
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.connect4 import Connect4, PLAYER_1, PLAYER_2

# Column preference: center first, edges last
COLUMN_ORDER = [3, 2, 4, 1, 5, 0, 6]


class Connect4AI:
    """Minimax AI with alpha-beta pruning for Connect 4."""

    DEPTH = 7

    def __init__(self):
        pass

    def get_best_move(self, game, player):
        """Find the best column using negamax with alpha-beta."""
        valid = [c for c in COLUMN_ORDER if game.get_drop_row(c) >= 0]
        if not valid:
            return None

        opponent = PLAYER_2 if player == PLAYER_1 else PLAYER_1

        # Check for immediate win
        for col in valid:
            row = game.get_drop_row(col)
            game.board[row][col] = player
            if game.check_win(row, col, player):
                game.board[row][col] = 0
                return col
            game.board[row][col] = 0

        # Check for immediate block
        for col in valid:
            row = game.get_drop_row(col)
            game.board[row][col] = opponent
            if game.check_win(row, col, opponent):
                game.board[row][col] = 0
                return col
            game.board[row][col] = 0

        best_col = valid[0]
        best_score = float('-inf')
        alpha = float('-inf')
        beta = float('inf')

        # Shuffle same-priority columns for variety
        random.shuffle(valid)
        # But keep center bias by re-sorting by column order preference
        valid.sort(key=lambda c: COLUMN_ORDER.index(c))

        for col in valid:
            row = game.get_drop_row(col)
            game.board[row][col] = player
            score = -self._negamax(game, self.DEPTH - 1, -beta, -alpha, opponent)
            game.board[row][col] = 0

            if score > best_score:
                best_score = score
                best_col = col
            alpha = max(alpha, score)
            if alpha >= beta:
                break

        return best_col

    def _negamax(self, game, depth, alpha, beta, player):
        """Negamax with alpha-beta pruning."""
        opponent = PLAYER_2 if player == PLAYER_1 else PLAYER_1

        # Terminal checks
        if depth == 0:
            return self._evaluate(game, player)

        valid = [c for c in COLUMN_ORDER if game.get_drop_row(c) >= 0]
        if not valid:
            return 0  # Draw

        for col in valid:
            row = game.get_drop_row(col)
            game.board[row][col] = player

            # Check win
            if game.check_win(row, col, player):
                game.board[row][col] = 0
                return 10000 + depth  # Prefer faster wins

            score = -self._negamax(game, depth - 1, -beta, -alpha, opponent)
            game.board[row][col] = 0

            alpha = max(alpha, score)
            if alpha >= beta:
                break

        return alpha

    def _evaluate(self, game, player):
        """Evaluate board position for player."""
        opponent = PLAYER_2 if player == PLAYER_1 else PLAYER_1
        score = 0

        # Center column control
        center_col = 3
        for row in range(6):
            if game.board[row][center_col] == player:
                score += 3
            elif game.board[row][center_col] == opponent:
                score -= 3

        # Evaluate all possible 4-windows
        # Horizontal
        for row in range(6):
            for col in range(4):
                score += self._score_window(game, row, col, 0, 1, player, opponent)

        # Vertical
        for row in range(3):
            for col in range(7):
                score += self._score_window(game, row, col, 1, 0, player, opponent)

        # Diagonal down-right
        for row in range(3):
            for col in range(4):
                score += self._score_window(game, row, col, 1, 1, player, opponent)

        # Diagonal down-left
        for row in range(3):
            for col in range(3, 7):
                score += self._score_window(game, row, col, 1, -1, player, opponent)

        return score

    def _score_window(self, game, row, col, dr, dc, player, opponent):
        """Score a 4-cell window."""
        own = 0
        opp = 0
        empty = 0
        for i in range(4):
            r = row + dr * i
            c = col + dc * i
            cell = game.board[r][c]
            if cell == player:
                own += 1
            elif cell == opponent:
                opp += 1
            else:
                empty += 1

        if own == 3 and empty == 1:
            return 20
        if own == 2 and empty == 2:
            return 4
        if opp == 3 and empty == 1:
            return -18
        if opp == 2 and empty == 2:
            return -2
        return 0


class Connect4Demo(Visual):
    """AI vs AI Connect 4 demo for attract mode."""
    name = "CONNECT 4"
    description = "AI vs AI"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = Connect4(self.display)
        self.game.reset()
        self.ai = Connect4AI()
        self.target_col = None
        self.think_timer = 0.0
        self.move_timer = 0.0
        self.game_over_timer = 0.0

    def handle_input(self, input_state):
        return False

    def update(self, dt):
        self.time += dt

        # Game over — restart after 3 seconds
        if self.game.state == GameState.GAME_OVER:
            self.game_over_timer += dt
            if self.game_over_timer > 3.0:
                self.game.reset()
                self.game_over_timer = 0.0
                self.target_col = None
                self.think_timer = 0.0
            # Still update game for win flash animation
            self.game.update(InputState(), dt)
            return

        # While a piece is dropping, just run game update
        if self.game.dropping:
            self.game.update(InputState(), dt)
            return

        # Think before choosing a column
        if self.target_col is None:
            self.think_timer += dt
            if self.think_timer < random.uniform(0.3, 0.6):
                return
            self.target_col = self.ai.get_best_move(self.game, self.game.current_player)
            self.think_timer = 0.0
            self.move_timer = 0.0
            if self.target_col is None:
                return

        # Navigate cursor toward target column
        ai_input = InputState()
        if self.game.cursor_col != self.target_col:
            self.move_timer += dt
            if self.move_timer >= 0.1:
                if self.game.cursor_col < self.target_col:
                    ai_input.right = True
                else:
                    ai_input.left = True
                self.move_timer = 0.0
        else:
            # At the right column — drop
            ai_input.action_l = True
            self.target_col = None

        self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()
        # Blinking DEMO overlay
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)
