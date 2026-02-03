"""
Flappy Bird Demo - AI Attract Mode
==================================
Flappy plays itself by timing flaps to navigate through pipe gaps.

AI Strategy:
- Look at the next pipe gap
- Flap when bird is below the gap center and falling
- Account for gravity and upward velocity from flaps
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.flappy import Flappy


class FlappyDemo(Visual):
    name = "FLAPPY DEMO"
    description = "AI plays Flappy Bird"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = Flappy(self.display)
        self.game.reset()
        self.should_flap = False
        self.decision_timer = 0.0
        self.decision_interval = 0.05  # Check frequently

    def handle_input(self, input_state):
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

        # Make AI decisions
        self.decision_timer += dt
        if self.decision_timer >= self.decision_interval:
            self.decision_timer = 0.0
            self.should_flap = self._should_flap()

        # Create input state
        ai_input = InputState()
        if self.should_flap:
            ai_input.action_l = True
            self.should_flap = False  # Single flap per decision

        self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()

        # Overlay "DEMO" text
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)

    def _should_flap(self):
        """Decide whether to flap based on upcoming pipe gap."""
        game = self.game

        # Auto-start the game
        if not game.started:
            return True

        bird_y = game.bird_y
        bird_vy = game.bird_vy

        # Find the next pipe to navigate
        next_pipe = None
        for pipe in game.pipes:
            if pipe['x'] + game.pipe_width > game.bird_x:
                if next_pipe is None or pipe['x'] < next_pipe['x']:
                    next_pipe = pipe

        if next_pipe is None:
            # No pipes ahead, just maintain altitude
            return bird_y > 30 and bird_vy > 0

        # Calculate target Y (center of gap)
        gap_center = next_pipe['gap_y'] + game.gap_height / 2

        # Predict where bird will be
        # Simple physics: y' = y + vy*t + 0.5*g*t^2
        look_ahead = 0.15  # seconds
        predicted_y = bird_y + bird_vy * look_ahead + 0.5 * game.gravity * look_ahead * look_ahead

        # Distance to pipe
        dist_to_pipe = next_pipe['x'] - game.bird_x

        # Adjust target based on distance
        # If far away, aim for gap center
        # If close, be more precise
        if dist_to_pipe < 15:
            # Close to pipe - need precise navigation
            target_offset = -2  # Aim slightly above center
        else:
            target_offset = 0

        target_y = gap_center + target_offset

        # Flap conditions:
        # 1. Bird is below target and falling (or about to fall)
        # 2. Bird is way below target
        # 3. About to hit ground

        should_flap = False

        # Critical: don't hit ground
        if bird_y > game.ground_y - 10:
            should_flap = True
        # Below target and falling
        elif bird_y > target_y and bird_vy > -10:
            should_flap = True
        # Predicted position too low
        elif predicted_y > target_y + 5:
            should_flap = True
        # Way below target
        elif bird_y > target_y + 8:
            should_flap = True

        # Don't flap if too high
        if bird_y < gap_center - game.gap_height / 2 + 2:
            should_flap = False

        return should_flap
