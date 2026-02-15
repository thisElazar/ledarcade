"""
Mastermind - Code Breaking Game
================================
The classic 1970 Mordecai Meirowitz code-breaking game.
Guess the secret 4-color code in 10 tries or less.
After each guess, get feedback on correct colors and positions.

Controls:
  Left/Right - Move cursor
  Up/Down    - Change color at cursor
  Space      - Submit guess
"""

import random
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


class Mastermind(Game):
    name = "MASTER CODE"
    description = "Break the code"
    category = "toys"

    # Available colors (6 colors like the original)
    PEG_COLORS = [
        Colors.RED,
        Colors.GREEN,
        Colors.BLUE,
        Colors.YELLOW,
        Colors.CYAN,
        Colors.MAGENTA,
    ]

    # Feedback peg colors
    BLACK_PEG = Colors.WHITE  # Correct color AND position
    WHITE_PEG = Colors.GRAY   # Correct color, wrong position

    # Layout
    CODE_LENGTH = 4
    MAX_GUESSES = 10
    PEG_SIZE = 5
    ROW_HEIGHT = 6
    BOARD_X = 4
    BOARD_Y = 2

    def __init__(self, display: Display):
        super().__init__(display)
        self.best_score = 99  # Best (fewest) guesses to win
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING

        # Generate secret code
        self.secret = [random.randint(0, len(self.PEG_COLORS) - 1) for _ in range(self.CODE_LENGTH)]

        # Game state
        self.guesses = []  # List of (guess, feedback) tuples
        self.current_guess = [0] * self.CODE_LENGTH
        self.cursor = 0
        self.won = False
        self.lost = False

        # Input timing
        self.input_cooldown = 0

    def evaluate_guess(self, guess):
        """
        Evaluate a guess against the secret code.
        Returns (black_pegs, white_pegs).
        Black = correct color and position
        White = correct color, wrong position
        """
        black = 0
        white = 0

        secret_copy = list(self.secret)
        guess_copy = list(guess)

        # First pass: find exact matches (black pegs)
        for i in range(self.CODE_LENGTH):
            if guess_copy[i] == secret_copy[i]:
                black += 1
                secret_copy[i] = -1
                guess_copy[i] = -2

        # Second pass: find color matches (white pegs)
        for i in range(self.CODE_LENGTH):
            if guess_copy[i] >= 0:
                if guess_copy[i] in secret_copy:
                    white += 1
                    secret_copy[secret_copy.index(guess_copy[i])] = -1

        return (black, white)

    def submit_guess(self):
        """Submit the current guess."""
        guess = list(self.current_guess)
        feedback = self.evaluate_guess(guess)
        self.guesses.append((guess, feedback))

        if feedback[0] == self.CODE_LENGTH:
            # All black = win!
            self.won = True
            if len(self.guesses) < self.best_score:
                self.best_score = len(self.guesses)
        elif len(self.guesses) >= self.MAX_GUESSES:
            # Out of guesses
            self.lost = True
        else:
            # Reset for next guess
            self.current_guess = [0] * self.CODE_LENGTH
            self.cursor = 0

    def update(self, input_state: InputState, dt: float):
        if self.input_cooldown > 0:
            self.input_cooldown -= dt

        if self.won or self.lost:
            if input_state.action_l or input_state.action_r:
                self.reset()
            return

        if self.input_cooldown <= 0:
            # Move cursor
            if input_state.left:
                self.cursor = (self.cursor - 1) % self.CODE_LENGTH
                self.input_cooldown = 0.15
            elif input_state.right:
                self.cursor = (self.cursor + 1) % self.CODE_LENGTH
                self.input_cooldown = 0.15

            # Change color
            elif input_state.up:
                self.current_guess[self.cursor] = (self.current_guess[self.cursor] + 1) % len(self.PEG_COLORS)
                self.input_cooldown = 0.12
            elif input_state.down:
                self.current_guess[self.cursor] = (self.current_guess[self.cursor] - 1) % len(self.PEG_COLORS)
                self.input_cooldown = 0.12

            # Submit guess
            elif input_state.action_l or input_state.action_r:
                self.submit_guess()
                self.input_cooldown = 0.3

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Draw previous guesses
        for row, (guess, feedback) in enumerate(self.guesses):
            y = self.BOARD_Y + row * self.ROW_HEIGHT

            # Draw guess pegs
            for col, color_idx in enumerate(guess):
                x = self.BOARD_X + col * (self.PEG_SIZE + 1)
                self.display.draw_rect(x, y, self.PEG_SIZE, self.PEG_SIZE, self.PEG_COLORS[color_idx])

            # Draw feedback pegs (smaller, to the right)
            fx = self.BOARD_X + self.CODE_LENGTH * (self.PEG_SIZE + 1) + 2
            black_pegs, white_pegs = feedback
            for i in range(black_pegs):
                self.display.draw_rect(fx + (i % 2) * 3, y + (i // 2) * 3, 2, 2, self.BLACK_PEG)
            for i in range(white_pegs):
                pi = black_pegs + i
                self.display.draw_rect(fx + (pi % 2) * 3, y + (pi // 2) * 3, 2, 2, self.WHITE_PEG)

        # Draw current guess row (if game not over)
        if not self.won and not self.lost:
            row = len(self.guesses)
            y = self.BOARD_Y + row * self.ROW_HEIGHT

            for col, color_idx in enumerate(self.current_guess):
                x = self.BOARD_X + col * (self.PEG_SIZE + 1)
                self.display.draw_rect(x, y, self.PEG_SIZE, self.PEG_SIZE, self.PEG_COLORS[color_idx])

                # Draw cursor
                if col == self.cursor:
                    self.display.draw_rect(x, y + self.PEG_SIZE, self.PEG_SIZE, 1, Colors.WHITE)

        # Draw remaining guesses indicator
        remaining = self.MAX_GUESSES - len(self.guesses)
        self.display.draw_text_small(40, 2, f"LEFT:{remaining}", Colors.GRAY)

        # Draw best score if any
        if self.best_score < 99:
            self.display.draw_text_small(40, 56, f"BEST:{self.best_score}", Colors.YELLOW)

        # Win/lose message
        if self.won:
            self.display.draw_text_small(36, 30, "WIN!", Colors.GREEN)
            self.display.draw_text_small(32, 40, f"IN {len(self.guesses)}", Colors.WHITE)
            if len(self.guesses) <= self.best_score:
                self.display.draw_text_small(32, 52, "BEST!", Colors.YELLOW)
        elif self.lost:
            self.display.draw_text_small(32, 25, "LOSE", Colors.RED)
            # Show the secret code
            self.display.draw_text_small(32, 35, "CODE:", Colors.GRAY)
            for col, color_idx in enumerate(self.secret):
                x = 34 + col * (self.PEG_SIZE + 1)
                self.display.draw_rect(x, 44, self.PEG_SIZE, self.PEG_SIZE, self.PEG_COLORS[color_idx])
