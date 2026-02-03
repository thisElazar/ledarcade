"""
Pong Demo - AI Attract Mode
===========================
AI vs AI Pong match for idle screen demos.
Both paddles are controlled by AI with slight imperfections for natural gameplay.

AI Strategy:
- Both paddles track the ball's Y position with slight delay
- Small random error prevents perfect play
- Auto-serves when waiting
"""

import random

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

# Import the actual game
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.pong import Pong


class PongDemo(Visual):
    name = "PONG DEMO"
    description = "AI plays Pong"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = Pong(self.display)
        self.game.reset()
        self.game_over_timer = 0.0

        # Left paddle AI state (right paddle uses game's built-in AI)
        self.left_target_y = GRID_SIZE // 2
        self.left_reaction_timer = 0.0
        self.left_reaction_delay = 0.12  # Slightly faster than default AI
        self.left_tracking_error = 4.0   # Moderate imperfection
        self.left_speed = 45.0           # Paddle speed

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
                # Reset left AI state
                self.left_target_y = GRID_SIZE // 2
                self.left_reaction_timer = 0.0
            return

        # Create input state for left paddle AI
        ai_input = InputState()

        # Auto-serve if waiting
        if self.game.serving:
            ai_input.action_l = True
        else:
            # Left paddle AI: track ball with delay and imperfection
            self.left_reaction_timer += dt

            if self.left_reaction_timer >= self.left_reaction_delay:
                self.left_reaction_timer = 0.0
                # Target ball Y with some randomness
                self.left_target_y = self.game.ball_y - self.game.paddle_height / 2
                self.left_target_y += random.uniform(-self.left_tracking_error, self.left_tracking_error)

            # Move toward target
            if self.game.player_y < self.left_target_y - 1:
                ai_input.down = True
            elif self.game.player_y > self.left_target_y + 1:
                ai_input.up = True

        self.game.update(ai_input, dt)

    def draw(self):
        # Draw game over screen if applicable
        if self.game.state in (GameState.GAME_OVER, GameState.WIN):
            self.game.draw_game_over()
        else:
            self.game.draw()

        # Overlay "DEMO" text (blinking)
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)
