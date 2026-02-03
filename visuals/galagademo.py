"""
Galaga Demo - AI Attract Mode
=============================
Galaga plays itself using simple AI for idle screen demos.
The AI dodges bullets, shoots enemies, and prioritizes UFOs.

AI Strategy:
- Dodge enemy bullets when they're close and threatening
- Prioritize UFO if present
- Target the lowest alive enemy in formation or nearest diver
- Move toward target x, shoot when aligned
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

# Import the actual game
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.galaga import Galaga


class GalagaDemo(Visual):
    name = "GALAGA DEMO"
    description = "AI plays Galaga"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = Galaga(self.display)
        self.game.reset()
        self.ai_move = 0  # -1 left, 0 none, 1 right
        self.ai_shoot = False
        self.decision_timer = 0.0
        self.decision_interval = 0.05  # 50ms - fast reactions needed

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
        if self.ai_move < 0:
            ai_input.left = True
        elif self.ai_move > 0:
            ai_input.right = True
        if self.ai_shoot:
            ai_input.action_l_held = True

        self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()

        # Overlay "DEMO" text
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)

    def _decide_action(self):
        """AI decision-making for Galaga movement and shooting."""
        game = self.game
        player_x = game.player_x
        player_y = game.PLAYER_Y

        # Priority 1: Dodge enemy bullets
        dodge_dir = self._check_bullet_dodge(player_x, player_y)
        if dodge_dir != 0:
            self.ai_move = dodge_dir
            self.ai_shoot = False  # Focus on dodging
            return

        # Priority 2: Target UFO if present
        target_x = None
        if hasattr(game, 'ufo') and game.ufo is not None:
            target_x = game.ufo['x'] + 2

        # Priority 3: Target nearest diver
        if target_x is None:
            nearest_diver = self._find_nearest_diver(player_x)
            if nearest_diver is not None:
                target_x = nearest_diver

        # Priority 4: Target lowest alive enemy in formation
        if target_x is None:
            target_x = self._find_lowest_formation_enemy()

        # Move toward target and shoot when aligned
        if target_x is not None:
            diff = target_x - player_x
            if abs(diff) <= 2:
                # Aligned - stop and shoot
                self.ai_move = 0
                self.ai_shoot = True
            else:
                # Move toward target
                self.ai_move = 1 if diff > 0 else -1
                self.ai_shoot = False
        else:
            # No targets, stay still
            self.ai_move = 0
            self.ai_shoot = False

    def _check_bullet_dodge(self, player_x, player_y):
        """Check if we need to dodge an incoming bullet. Returns dodge direction."""
        game = self.game

        for bullet in game.enemy_bullets:
            bx, by = bullet['x'], bullet['y']

            # Only react to bullets that are close vertically (y > 45) and horizontally (within 5px)
            if by > 45 and abs(bx - player_x) < 5:
                # Bullet is threatening - move away from it
                if bx < player_x:
                    # Bullet is to our left, move right (unless at edge)
                    if player_x < 57:
                        return 1
                    else:
                        return -1
                else:
                    # Bullet is to our right, move left (unless at edge)
                    if player_x > 6:
                        return -1
                    else:
                        return 1

        return 0  # No dodge needed

    def _find_nearest_diver(self, player_x):
        """Find the x position of the nearest diver."""
        game = self.game

        if not game.divers:
            return None

        nearest_dist = float('inf')
        nearest_x = None

        for diver in game.divers:
            dist = abs(diver['x'] - player_x)
            if dist < nearest_dist:
                nearest_dist = dist
                nearest_x = diver['x']

        return nearest_x

    def _find_lowest_formation_enemy(self):
        """Find the x position of the lowest alive enemy in the formation."""
        game = self.game

        lowest_row = -1
        lowest_x = None

        for (col, row), enemy in game.formation.items():
            if enemy['alive'] and row > lowest_row:
                lowest_row = row
                ex, ey = game.get_formation_pos(col, row)
                lowest_x = ex

        # If multiple enemies in the lowest row, pick the closest to center
        if lowest_row >= 0:
            candidates = []
            for (col, row), enemy in game.formation.items():
                if enemy['alive'] and row == lowest_row:
                    ex, ey = game.get_formation_pos(col, row)
                    candidates.append(ex)

            if candidates:
                # Pick the one closest to player for better tracking
                player_x = game.player_x
                lowest_x = min(candidates, key=lambda x: abs(x - player_x))

        return lowest_x
