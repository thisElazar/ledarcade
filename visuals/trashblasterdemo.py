"""
TrashBlaster Demo - AI Attract Mode
====================================
TrashBlaster plays itself using simple AI for idle screen demos.
The AI moves the crosshair to track and blast floating trash.

AI Strategy:
- Find the nearest trash target
- Move crosshair toward target
- Fire when aligned with target center
- Prioritize larger trash (easier to hit, clears screen faster)
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

# Import the actual game
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.trashblaster import TrashBlaster


class TrashBlasterDemo(Visual):
    name = "TRASH BLASTER"
    description = "AI blasts trash"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = TrashBlaster(self.display)
        self.game.reset()
        self.ai_move_x = 0  # -1 left, 0 none, 1 right
        self.ai_move_y = 0  # -1 up, 0 none, 1 down
        self.ai_shoot = False
        self.decision_timer = 0.0
        self.decision_interval = 0.05  # 50ms - fast reactions
        self.current_target = None

    def handle_input(self, input_state):
        # Demo doesn't respond to input (auto-plays)
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

        # Make AI decisions periodically
        self.decision_timer += dt
        if self.decision_timer >= self.decision_interval:
            self.decision_timer = 0.0
            self._decide_action()

        # Create input state with AI's chosen actions
        ai_input = InputState()
        if self.ai_move_x < 0:
            ai_input.left = True
        elif self.ai_move_x > 0:
            ai_input.right = True
        if self.ai_move_y < 0:
            ai_input.up = True
        elif self.ai_move_y > 0:
            ai_input.down = True
        if self.ai_shoot:
            ai_input.action_l = True

        self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()

        # Overlay "DEMO" text (blinking)
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)

    def _decide_action(self):
        """AI decision-making for crosshair movement and shooting."""
        game = self.game
        crosshair_x = game.crosshair_x
        crosshair_y = game.crosshair_y

        # Find the best target
        target = self._find_best_target(crosshair_x, crosshair_y)

        if target is None:
            # No targets, stay still
            self.ai_move_x = 0
            self.ai_move_y = 0
            self.ai_shoot = False
            return

        # Calculate distance to target
        dx = target.x - crosshair_x
        dy = target.y - crosshair_y
        target_radius = target.get_radius()

        # Check if we're aligned enough to shoot
        if abs(dx) <= target_radius and abs(dy) <= target_radius:
            # Aligned - stop and shoot
            self.ai_move_x = 0
            self.ai_move_y = 0
            self.ai_shoot = True
        else:
            # Move toward target
            if abs(dx) > target_radius:
                self.ai_move_x = 1 if dx > 0 else -1
            else:
                self.ai_move_x = 0

            if abs(dy) > target_radius:
                self.ai_move_y = 1 if dy > 0 else -1
            else:
                self.ai_move_y = 0

            # Don't shoot while moving (unless close)
            self.ai_shoot = abs(dx) <= target_radius + 2 and abs(dy) <= target_radius + 2

    def _find_best_target(self, crosshair_x, crosshair_y):
        """Find the best trash target to aim at.

        Strategy: Prioritize larger trash (easier to hit) that is closest.
        Score = size_bonus - distance
        """
        game = self.game
        best_target = None
        best_score = float('-inf')

        for trash in game.trash:
            if not trash.alive:
                continue

            # Calculate distance
            dx = trash.x - crosshair_x
            dy = trash.y - crosshair_y
            distance = (dx * dx + dy * dy) ** 0.5

            # Larger trash is easier to hit, so prioritize it
            # But also consider distance
            size_bonus = trash.size * 5
            score = size_bonus - distance

            # Slight preference for trash in the viewport (not near edges)
            margin = game.viewport_margin
            if margin + 5 < trash.x < GRID_SIZE - margin - 5:
                if margin + 5 < trash.y < GRID_SIZE - margin - 5:
                    score += 3

            if score > best_score:
                best_score = score
                best_target = trash

        return best_target
