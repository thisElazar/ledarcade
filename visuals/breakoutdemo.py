"""
Breakout Demo - AI Attract Mode
===============================
Breakout plays itself using simple AI for idle screen demos.
The AI predicts where the ball will land and moves the paddle to intercept.

AI Strategy:
- Launch ball automatically when waiting
- Predict ball trajectory accounting for wall bounces
- Move paddle toward predicted landing position
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

# Import the actual game
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.breakout import Breakout, PLAY_LEFT, PLAY_RIGHT


class BreakoutDemo(Visual):
    name = "BREAK OUT"
    description = "AI plays Breakout"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = Breakout(self.display)
        self.game.reset()
        self.decision_timer = 0.0
        self.decision_interval = 0.05  # Recalculate every 50ms
        self.current_action = None
        self.game_over_timer = 0.0

    def handle_input(self, input_state):
        # Demo doesn't respond to input (auto-plays)
        return False

    def update(self, dt):
        self.time += dt

        # If game over or win, restart after a pause
        if self.game.state in (GameState.GAME_OVER, GameState.WIN):
            self.game_over_timer += dt
            if self.game_over_timer > 3.0:
                self.game.reset()
                self.game_over_timer = 0.0
            return

        # Make AI decisions periodically
        self.decision_timer += dt
        if self.decision_timer >= self.decision_interval:
            self.decision_timer = 0.0
            self.current_action = self._decide_action()

        # Create input state with AI's chosen action
        ai_input = InputState()
        if self.current_action == 'launch':
            ai_input.action_l = True
        elif self.current_action == 'left':
            ai_input.left = True
        elif self.current_action == 'right':
            ai_input.right = True

        self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()

        # Overlay "DEMO" text (blinking)
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)

    def _decide_action(self):
        """AI decision-making for paddle movement."""
        game = self.game

        # Launch ball if not launched
        if not game.ball_launched:
            return 'launch'

        # Predict where ball will hit paddle level
        if game.ball_dy > 0:  # Ball moving down
            # Calculate time to reach paddle
            time_to_paddle = (game.paddle_y - game.ball_y) / game.ball_dy
            # Predict x position
            predicted_x = game.ball_x + game.ball_dx * time_to_paddle

            # Account for wall bounces
            iterations = 0
            while (predicted_x < PLAY_LEFT or predicted_x > PLAY_RIGHT - 2) and iterations < 10:
                if predicted_x < PLAY_LEFT:
                    predicted_x = 2 * PLAY_LEFT - predicted_x  # Bounce off left wall
                if predicted_x > PLAY_RIGHT - 2:
                    predicted_x = 2 * (PLAY_RIGHT - 2) - predicted_x  # Bounce off right wall
                iterations += 1
        else:
            # Ball going up, just track its current x
            predicted_x = game.ball_x

        # Move paddle center toward predicted position
        paddle_center = game.paddle_x + game.paddle_width / 2

        if abs(paddle_center - predicted_x) < 2:
            return None  # Close enough
        elif paddle_center < predicted_x:
            return 'right'
        else:
            return 'left'
