"""
Space Invaders Demo - AI Attract Mode
=====================================
Space Invaders plays itself using simple AI for idle screen demos.
The AI tracks aliens, dodges bullets, and prioritizes the UFO.

AI Strategy:
- Dodge incoming bullets that are dangerously close
- Prioritize shooting the UFO when it appears
- Target the lowest (most dangerous) alien
- Move toward target and shoot when aligned
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

# Import the actual game
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.invaders import Invaders


class InvadersDemo(Visual):
    name = "INVADERS DEMO"
    description = "AI plays Space Invaders"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = Invaders(self.display)
        self.game.reset()
        self.decision_timer = 0.0
        self.decision_interval = 0.05  # Decide every 50ms for responsive play
        self.current_action = None
        self.game_over_timer = 0.0

    def handle_input(self, input_state):
        # Demo doesn't respond to input (auto-plays)
        return False

    def update(self, dt):
        self.time += dt

        # If game over, restart after a pause
        if self.game.state == GameState.GAME_OVER:
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
        if self.current_action == 'left':
            ai_input.left = True
        elif self.current_action == 'right':
            ai_input.right = True
        elif self.current_action == 'shoot':
            ai_input.action_l = True

        self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()

        # Overlay "DEMO" text (blinking)
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)

    def _decide_action(self):
        """AI decision-making for player movement and shooting."""
        game = self.game

        # No enemies left, just wait
        if not game.enemies:
            return None

        player_x = game.player_x

        # 1. Check for dangerous incoming bullets
        danger_bullets = [
            b for b in game.enemy_bullets
            if abs(b['x'] - player_x - 1) < 5 and b['y'] > 45
        ]

        if danger_bullets:
            # Dodge! Move away from nearest bullet
            nearest = min(danger_bullets, key=lambda b: abs(b['x'] - player_x - 1))
            if nearest['x'] > player_x + 1:
                return 'left'
            else:
                return 'right'

        # 2. If UFO exists, prioritize shooting it
        if game.ufo is not None:
            target_x = game.ufo['x'] + 2  # Center of UFO
        else:
            # 3. Find lowest (most dangerous) enemy - highest y value
            lowest_enemy = max(game.enemies, key=lambda e: e['y'])
            target_x = lowest_enemy['x'] + 1  # Center of enemy

        # Move toward target and shoot when aligned
        player_center = player_x + 1  # Center of player ship

        if abs(player_center - target_x) < 2:
            return 'shoot'
        elif player_center < target_x:
            return 'right'
        else:
            return 'left'
