"""
Connect 4 Demo - AI vs AI Attract Mode
=======================================
Two AIs play Connect 4 against each other for idle screen demos.

AI Strategy:
- Priority 1: Win — play a column that completes 4-in-a-row
- Priority 2: Block — prevent opponent from winning next move
- Priority 3: Prefer center columns (3 > 2,4 > 1,5 > 0,6)
- Priority 4: Random valid column as fallback
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState
import random
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.connect4 import Connect4, PLAYER_1, PLAYER_2

# Column preference: center first, edges last
COLUMN_PRIORITY = [3, 2, 4, 1, 5, 0, 6]


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
            self.target_col = self._choose_column()
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

    def _choose_column(self):
        """Pick the best column: win > block > center preference > random."""
        player = self.game.current_player
        opponent = PLAYER_2 if player == PLAYER_1 else PLAYER_1

        valid = [c for c in range(7) if self.game.get_drop_row(c) >= 0]
        if not valid:
            return None

        # Win: can we complete 4-in-a-row?
        for col in valid:
            if self._would_win(col, player):
                return col

        # Block: can opponent win next move?
        for col in valid:
            if self._would_win(col, opponent):
                return col

        # Center preference among valid columns
        for col in COLUMN_PRIORITY:
            if col in valid:
                return col

        return random.choice(valid)

    def _would_win(self, col, player):
        """Check if dropping player's piece in col would create 4-in-a-row."""
        row = self.game.get_drop_row(col)
        if row < 0:
            return False
        # Temporarily place piece
        self.game.board[row][col] = player
        win = bool(self.game.check_win(row, col, player))
        # Remove piece
        self.game.board[row][col] = 0
        return win
