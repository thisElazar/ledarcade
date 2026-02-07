"""
Agar.io Demo - AI Attract Mode
===============================
AI-controlled Agar.io for idle screen demos.
The AI chases nearest edible target and flees threats.
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.agario import Agario


class AgarioDemo(Visual):
    name = "AGAR.IO"
    description = "AI plays Agar.io"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = Agario(self.display)
        self.game.reset()
        self.game_over_timer = 0.0

    def handle_input(self, input_state):
        return False

    def update(self, dt):
        self.time += dt

        if self.game.state == GameState.GAME_OVER:
            self.game_over_timer += dt
            if self.game_over_timer > 3.0:
                self.game.reset()
                self.game_over_timer = 0.0
            return

        # AI: build input by chasing nearest edible or fleeing threat
        ai_input = InputState()
        player = self.game.player

        # Find nearest threat (bigger cell)
        nearest_threat = None
        threat_dist = float('inf')
        # Find nearest edible (food or smaller cell)
        nearest_edible = None
        edible_dist = float('inf')

        # Check AI cells
        for ai in self.game.ai_cells:
            d = self.game._wrap_dist(player.x, player.y, ai.x, ai.y)
            if ai.radius > player.radius:
                if d < threat_dist:
                    threat_dist = d
                    nearest_threat = ai
            elif player.radius > ai.radius:
                if d < edible_dist:
                    edible_dist = d
                    nearest_edible = ai

        # Check food
        for f in self.game.food:
            d = self.game._wrap_dist(player.x, player.y, f['x'], f['y'])
            if d < edible_dist:
                edible_dist = d
                nearest_edible = f

        # Decide direction (using wrapped deltas)
        dx, dy = 0, 0
        if nearest_threat and threat_dist < 12:
            # Flee: direction from threat toward player (away)
            dx, dy = self.game._wrap_delta(nearest_threat.x, nearest_threat.y, player.x, player.y)
        elif nearest_edible:
            if hasattr(nearest_edible, 'x'):
                dx, dy = self.game._wrap_delta(player.x, player.y, nearest_edible.x, nearest_edible.y)
            else:
                dx, dy = self.game._wrap_delta(player.x, player.y, nearest_edible['x'], nearest_edible['y'])

        if abs(dx) > 0.5 or abs(dy) > 0.5:
            if abs(dx) > abs(dy):
                if dx > 0:
                    ai_input.right = True
                else:
                    ai_input.left = True
            else:
                if dy > 0:
                    ai_input.down = True
                else:
                    ai_input.up = True
            # Also set secondary direction for diagonal movement
            if abs(dx) > 1:
                if dx > 0:
                    ai_input.right = True
                else:
                    ai_input.left = True
            if abs(dy) > 1:
                if dy > 0:
                    ai_input.down = True
                else:
                    ai_input.up = True

        self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()

        # Overlay "DEMO" text (blinking)
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)
