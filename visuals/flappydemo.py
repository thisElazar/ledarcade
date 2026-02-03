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
    name = "FLAPPY"
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
            # No pipes ahead, stay in middle
            return bird_y > 30 and bird_vy > 0

        # Gap boundaries
        gap_top = next_pipe['gap_y']
        gap_bottom = next_pipe['gap_y'] + game.gap_height
        gap_center = (gap_top + gap_bottom) / 2

        # Simple approach: aim to be at gap_center + a bit lower (safer)
        target_y = gap_center + 2  # Aim slightly below center

        # Don't flap if above target and not falling fast
        if bird_y < target_y - 3:
            return False

        # Don't flap if moving up
        if bird_vy < -20:
            return False

        # Flap if below target and falling
        if bird_y > target_y and bird_vy >= 0:
            return True

        # Flap if falling fast
        if bird_vy > 40:
            return True

        # Critical: don't hit ground
        if bird_y > game.ground_y - 8:
            return True

        return False
