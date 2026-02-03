"""
BurgerTime Demo - AI Attract Mode
=================================
Peter Pepper plays himself using simple AI for idle screen demos.
The AI navigates platforms and ladders to drop burger ingredients.

AI Strategy:
- Find burger ingredients that haven't been dropped yet
- Navigate to the platform containing the target ingredient
- Use ladders to reach higher/lower floors
- Walk across ingredients to drop them down
- Avoid enemies (hotdog, egg, pickle) - keep distance
- Use pepper to stun enemies when they get too close
"""

from collections import deque
from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

# Import the actual game
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.burgertime import BurgerTime, FLOOR_Y, BURGER_X, INGREDIENT_WIDTH


class BurgerTimeDemo(Visual):
    name = "BURGERTIME"
    description = "AI builds burgers"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = BurgerTime(self.display)
        self.game.reset()
        self.decision_timer = 0.0
        self.decision_interval = 0.1  # Recalculate every 100ms
        self.ai_action = {'left': False, 'right': False, 'up': False, 'down': False, 'pepper': False}
        self.target_ingredient = None
        self.path_recalc_timer = 0.0
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
                self.target_ingredient = None
            return

        # Make AI decisions periodically
        self.decision_timer += dt
        if self.decision_timer >= self.decision_interval:
            self.decision_timer = 0.0
            self.ai_action = self._decide_action()

        # Create input state with AI's chosen actions
        ai_input = InputState()
        ai_input.up = self.ai_action['up']
        ai_input.down = self.ai_action['down']
        ai_input.left = self.ai_action['left']
        ai_input.right = self.ai_action['right']
        if self.ai_action['pepper']:
            ai_input.action_l = True

        self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()

        # Overlay "DEMO" text with blinking
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)

    def _decide_action(self):
        """AI decision-making for chef movement."""
        game = self.game
        action = {'left': False, 'right': False, 'up': False, 'down': False, 'pepper': False}

        chef_x = game.chef_x
        chef_y = game.chef_y

        # Check for nearby enemies - use pepper if close
        if self._should_use_pepper():
            action['pepper'] = True
            return action

        # Check if we should flee from enemies
        flee_direction = self._get_flee_direction()
        if flee_direction:
            action[flee_direction] = True
            return action

        # If on a ladder, continue climbing to target floor
        if game.on_ladder:
            target_floor = self._get_target_floor()
            current_floor = self._get_current_floor()
            if target_floor is not None:
                target_y = FLOOR_Y[target_floor]
                if chef_y > target_y + 3:
                    action['up'] = True
                elif chef_y < target_y - 3:
                    action['down'] = True
                else:
                    # Reached target floor, step off ladder
                    action['left'] = True
            elif current_floor == 0:
                # At top floor, step off
                action['right'] = True
            else:
                # No target, just climb up
                action['up'] = True
            return action

        # Find the best ingredient to walk over
        target = self._find_target_ingredient()
        if target is None:
            return action

        self.target_ingredient = target
        target_floor = target['floor_idx']
        target_x_center = target['x'] + INGREDIENT_WIDTH // 2

        # Determine which floor we're on
        current_floor = self._get_current_floor()

        # If we're on the target floor, walk across the ingredient
        if current_floor == target_floor:
            # Walk across the ingredient
            ing_left = target['x']
            ing_right = target['x'] + INGREDIENT_WIDTH - 1

            if chef_x < ing_left:
                action['right'] = True
            elif chef_x > ing_right:
                action['left'] = True
            else:
                # We're on the ingredient, walk across it
                # Check which parts still need walking
                unwalked_left = None
                unwalked_right = None
                for i, walked in enumerate(target['walked']):
                    if not walked:
                        if unwalked_left is None:
                            unwalked_left = target['x'] + i
                        unwalked_right = target['x'] + i

                if unwalked_left is not None:
                    # Walk toward unwalked portions
                    if chef_x < unwalked_left:
                        action['right'] = True
                    elif chef_x > unwalked_right:
                        action['left'] = True
                    else:
                        # We're within unwalked area, keep walking in current direction
                        if game.facing > 0:
                            action['right'] = True
                        else:
                            action['left'] = True
        else:
            # Need to change floors - find a ladder
            need_up = current_floor > target_floor
            ladder = self._find_best_ladder(current_floor, need_up)

            if ladder:
                # Navigate to the ladder
                if abs(chef_x - ladder['x']) < 3:
                    # At the ladder, climb it
                    if need_up:
                        action['up'] = True
                    else:
                        action['down'] = True
                else:
                    # Walk toward the ladder
                    if chef_x < ladder['x']:
                        action['right'] = True
                    else:
                        action['left'] = True
            else:
                # No suitable ladder found, try moving toward target x
                if chef_x < target_x_center:
                    action['right'] = True
                else:
                    action['left'] = True

        return action

    def _get_current_floor(self):
        """Determine which floor index the chef is currently on."""
        game = self.game
        chef_y = game.chef_y

        best_floor = 0
        best_dist = float('inf')
        for i, floor_y in enumerate(FLOOR_Y):
            dist = abs(chef_y - floor_y)
            if dist < best_dist:
                best_dist = dist
                best_floor = i

        return best_floor

    def _get_target_floor(self):
        """Get the floor index we're trying to reach."""
        if self.target_ingredient:
            return self.target_ingredient['floor_idx']
        return None

    def _find_target_ingredient(self):
        """Find the best ingredient to walk over next."""
        game = self.game
        chef_x = game.chef_x
        chef_y = game.chef_y
        current_floor = self._get_current_floor()

        best_target = None
        best_score = float('inf')

        for ing in game.ingredients:
            # Skip ingredients that are falling or already at the plate
            if ing['falling'] or ing.get('at_plate', False):
                continue

            # Skip fully walked ingredients (they should be falling anyway)
            if all(ing['walked']):
                continue

            # Calculate score based on distance
            floor_diff = abs(current_floor - ing['floor_idx'])
            x_diff = abs(chef_x - (ing['x'] + INGREDIENT_WIDTH // 2))

            # Prioritize same floor, then closer floors, then closer x
            score = floor_diff * 100 + x_diff

            # Prefer ingredients that are higher up (need to drop first)
            score -= (5 - ing['floor_idx']) * 10

            if score < best_score:
                best_score = score
                best_target = ing

        return best_target

    def _find_best_ladder(self, current_floor, need_up):
        """Find the best ladder to reach target floor."""
        game = self.game
        chef_x = game.chef_x
        chef_y = game.chef_y

        best_ladder = None
        best_dist = float('inf')

        for ladder in game.ladders:
            # Check if this ladder spans our current floor
            floor_y = FLOOR_Y[current_floor]

            # Ladder must be accessible from current floor
            if ladder['y1'] > floor_y + 3 or ladder['y2'] < floor_y - 3:
                continue

            # Check if ladder goes in the right direction
            if need_up and ladder['y1'] >= floor_y - 1:
                continue  # Ladder doesn't go up from here
            if not need_up and ladder['y2'] <= floor_y + 1:
                continue  # Ladder doesn't go down from here

            # Check if ladder is reachable on current platform
            if not game._on_platform_segment(ladder['x'], floor_y):
                continue

            # Calculate distance to this ladder
            dist = abs(chef_x - ladder['x'])

            if dist < best_dist:
                best_dist = dist
                best_ladder = ladder

        return best_ladder

    def _should_use_pepper(self):
        """Check if we should use pepper to stun enemies."""
        game = self.game

        # Don't use if no peppers left
        if game.peppers <= 0 or game.pepper_active:
            return False

        # Check for very close enemies
        for enemy in game.enemies:
            if enemy['stunned'] > 0:
                continue

            dx = abs(enemy['x'] - game.chef_x)
            dy = abs(enemy['y'] - game.chef_y)

            # Use pepper if enemy is very close
            if dx < 6 and dy < 5:
                return True

        return False

    def _get_flee_direction(self):
        """Check if we need to flee from an enemy and return direction."""
        game = self.game
        chef_x = game.chef_x
        chef_y = game.chef_y

        # Don't flee if on ladder (climbing is escape)
        if game.on_ladder:
            return None

        for enemy in game.enemies:
            if enemy['stunned'] > 0:
                continue

            dx = enemy['x'] - chef_x
            dy = enemy['y'] - chef_y

            # Only consider enemies on roughly the same floor
            if abs(dy) > 6:
                continue

            # Flee if enemy is close
            if abs(dx) < 12:
                # Try to move away from enemy horizontally
                if dx > 0:
                    # Enemy is to our right, move left
                    if game._on_platform_segment(chef_x - 2, chef_y):
                        return 'left'
                else:
                    # Enemy is to our left, move right
                    if game._on_platform_segment(chef_x + 2, chef_y):
                        return 'right'

                # If can't move horizontally, try to find a ladder
                ladder = game.get_ladder_at(chef_x, chef_y, prefer_up=True, prefer_down=True)
                if ladder:
                    # Prefer going up (away from danger)
                    if ladder['y1'] < chef_y:
                        return 'up'
                    elif ladder['y2'] > chef_y:
                        return 'down'

        return None
