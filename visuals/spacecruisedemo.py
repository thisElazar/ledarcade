"""
SpaceCruise Demo - AI Attract Mode
==================================
SpaceCruise plays itself using simple AI for idle screen demos.
The AI builds math combos by targeting numbers and operators.

AI Strategy:
- Look for targets that will maximize score
- If no combo active, target a number to start one
- If have a number, look for an operator
- If have number + operator, look for another number to complete combo
- Move rocket and crosshair to align with target, then fire
"""

import math
from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

# Import the actual game
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.spacecruise import SpaceCruise


class SpaceCruiseDemo(Visual):
    name = "SPACE CRUISE"
    description = "AI explores space"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = SpaceCruise(self.display)
        self.game.reset()
        self.decision_timer = 0.0
        self.decision_interval = 0.08  # Recalculate every 80ms
        self.ai_move_y = 0  # -1 up, 0 none, 1 down (for rocket)
        self.ai_move_x = 0  # -1 left, 0 none, 1 right (for crosshair)
        self.ai_shoot = False
        self.restart_timer = 0.0

    def handle_input(self, input_state):
        # Demo doesn't respond to input (auto-plays)
        return False

    def update(self, dt):
        self.time += dt

        # If game over, restart after a pause
        if self.game.state == GameState.GAME_OVER:
            self.restart_timer += dt
            if self.restart_timer > 3.0:
                self.game.reset()
                self.restart_timer = 0.0
            return

        # Make AI decisions periodically
        self.decision_timer += dt
        if self.decision_timer >= self.decision_interval:
            self.decision_timer = 0.0
            self._decide_action()

        # Create input state with AI's chosen actions
        ai_input = InputState()
        if self.ai_move_y < 0:
            ai_input.up = True
        elif self.ai_move_y > 0:
            ai_input.down = True
        if self.ai_move_x < 0:
            ai_input.left = True
        elif self.ai_move_x > 0:
            ai_input.right = True
        if self.ai_shoot:
            ai_input.action_l = True

        self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()

        # Overlay "DEMO" text
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)

    def _decide_action(self):
        """AI decision-making for SpaceCruise."""
        game = self.game

        # Reset actions
        self.ai_move_y = 0
        self.ai_move_x = 0
        self.ai_shoot = False

        # Find best target based on combo state
        target = self._find_best_target()
        if target is None:
            return

        target_x, target_y = target

        # Get current crosshair position
        crosshair_x = game.crosshair_x
        crosshair_y = game.crosshair_y

        # Calculate differences
        dx = target_x - crosshair_x
        dy = target_y - crosshair_y

        # Move crosshair toward target
        if abs(dx) > 3:
            self.ai_move_x = 1 if dx > 0 else -1
        if abs(dy) > 3:
            self.ai_move_y = 1 if dy > 0 else -1

        # Shoot when aligned (within tolerance) and cooldown is ready
        if abs(dx) <= 4 and abs(dy) <= 4 and game.fire_cooldown <= 0:
            self.ai_shoot = True

    def _find_best_target(self):
        """Find the best target based on current combo state."""
        game = self.game

        # Filter alive targets
        alive_targets = [t for t in game.targets if t.alive]
        if not alive_targets:
            return None

        # Separate numbers and operators
        numbers = [t for t in alive_targets if t.is_number]
        operators = [t for t in alive_targets if not t.is_number]

        # Decide what we need based on combo state
        if game.combo_first_number is None:
            # Need to start a combo - target a high number
            best = self._find_best_number(numbers)
            if best:
                return self._get_target_position(best)
        elif game.combo_operator is None:
            # Have a number, need an operator (prefer multiplication for higher scores)
            best = self._find_best_operator(operators)
            if best:
                return self._get_target_position(best)
            # If no operator available, target another number (will score first number)
            best = self._find_nearest_target(numbers)
            if best:
                return self._get_target_position(best)
        else:
            # Have number + operator, need another number to complete
            # For multiplication, prefer higher numbers; for addition, any number works
            best = self._find_best_number(numbers)
            if best:
                return self._get_target_position(best)

        # Fallback: target anything
        best = self._find_nearest_target(alive_targets)
        if best:
            return self._get_target_position(best)

        return None

    def _get_target_position(self, target):
        """Get the center position of a target including float offset."""
        game = self.game
        float_y = target.y + math.sin(game.time * target.float_speed + target.float_offset) * target.float_amplitude
        return (target.x + 1.5, float_y + 2.5)

    def _find_best_number(self, numbers):
        """Find the best number target - prefer higher values that are reachable."""
        if not numbers:
            return None

        game = self.game
        crosshair_x = game.crosshair_x

        # Filter to targets we can realistically hit (not too far left)
        reachable = [n for n in numbers if n.x > 15]
        if not reachable:
            reachable = numbers

        # Score based on value and proximity
        best = None
        best_score = -1

        for n in reachable:
            # Higher value is better, closer is better
            dist = abs(n.x - crosshair_x) + abs(n.y - game.crosshair_y)
            # Score: value * 10 - distance (prioritize value but consider distance)
            score = n.value * 10 - dist * 0.5
            if score > best_score:
                best_score = score
                best = n

        return best

    def _find_best_operator(self, operators):
        """Find the best operator - prefer multiplication."""
        if not operators:
            return None

        game = self.game

        # Prefer 'x' for multiplication (higher scores)
        multipliers = [o for o in operators if o.symbol == 'x']
        if multipliers:
            return self._find_nearest_target(multipliers)

        # Then prefer '+'
        adders = [o for o in operators if o.symbol == '+']
        if adders:
            return self._find_nearest_target(adders)

        # Any operator
        return self._find_nearest_target(operators)

    def _find_nearest_target(self, targets):
        """Find the nearest target to the crosshair."""
        if not targets:
            return None

        game = self.game
        crosshair_x = game.crosshair_x
        crosshair_y = game.crosshair_y

        nearest = None
        nearest_dist = float('inf')

        for t in targets:
            # Get target position with float
            tx, ty = self._get_target_position(t)
            dist = math.sqrt((tx - crosshair_x) ** 2 + (ty - crosshair_y) ** 2)
            if dist < nearest_dist:
                nearest_dist = dist
                nearest = t

        return nearest
