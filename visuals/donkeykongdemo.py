"""
Donkey Kong Demo - AI Attract Mode
==================================
Mario plays himself using simple AI for idle screen demos.
The AI navigates toward Pauline while avoiding barrels.

AI Strategy:
- Goal: reach Pauline at top
- Find nearest safe ladder going up (check for barrels)
- If barrel approaching, jump over it
- Move toward ladders, climb when reached
- On broken ladders, can only climb halfway
- Simple pathfinding: move right/left toward ladder x, then climb
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

# Import the actual game
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.donkeykong import DonkeyKong


class DonkeyKongDemo(Visual):
    name = "DK DEMO"
    description = "AI plays Donkey Kong"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = DonkeyKong(self.display)
        self.game.reset()
        self.decision_timer = 0.0
        self.decision_interval = 0.08  # Recalculate every 80ms
        self.ai_action = {'left': False, 'right': False, 'up': False, 'down': False, 'jump': False}

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
            self.ai_action = self._decide_action()

        # Create input state with AI's chosen actions
        ai_input = InputState()
        ai_input.up = self.ai_action['up']
        ai_input.down = self.ai_action['down']
        ai_input.left = self.ai_action['left']
        ai_input.right = self.ai_action['right']
        if self.ai_action['jump']:
            ai_input.action_l = True

        self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()

        # Overlay "DEMO" text
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)

    def _decide_action(self):
        """AI decision-making for Mario movement."""
        game = self.game
        action = {'left': False, 'right': False, 'up': False, 'down': False, 'jump': False}

        player_x = game.player_x
        player_y = game.player_y

        # Check for approaching barrels - need to jump
        if self._should_jump():
            action['jump'] = True
            return action

        # If on a ladder, continue climbing
        if game.on_ladder:
            ladder = game.get_ladder_at(player_x, player_y + game.PLAYER_HEIGHT // 2)
            if ladder:
                # Check if we can continue climbing
                if game.can_climb_ladder(ladder, going_up=True):
                    action['up'] = True
                else:
                    # Broken ladder - need to step off and find another route
                    action['right'] = True
            return action

        # If jumping, don't change direction
        if game.jumping:
            return action

        # Find the best ladder to climb toward Pauline
        target_ladder = self._find_best_ladder()

        if target_ladder:
            ladder_x = target_ladder['x']

            # Check if we're at the ladder
            if abs(player_x - ladder_x) < 3:
                # Check if ladder goes up from our current position
                player_feet = player_y + game.PLAYER_HEIGHT
                if target_ladder['y2'] >= player_feet - 4 and target_ladder['y1'] < player_feet:
                    # We can climb this ladder
                    if game.can_climb_ladder(target_ladder, going_up=True):
                        action['up'] = True
                        return action

            # Move toward the ladder
            if player_x < ladder_x - 2:
                action['right'] = True
            elif player_x > ladder_x + 2:
                action['left'] = True
        else:
            # No good ladder found, move toward Pauline's x position
            if player_x < game.pauline_x - 3:
                action['right'] = True
            elif player_x > game.pauline_x + 3:
                action['left'] = True

        return action

    def _should_jump(self):
        """Check if we should jump to avoid a barrel."""
        game = self.game
        player_x = game.player_x
        player_y = game.player_y

        # Don't jump if not on ground or already jumping
        if not game.on_ground or game.jumping or game.on_ladder:
            return False

        for barrel in game.barrels:
            barrel_x = barrel['x']
            barrel_y = barrel['y']

            # Check horizontal distance
            dx = barrel_x - player_x
            horizontal_dist = abs(dx)

            # Check vertical distance (barrel should be roughly on same platform)
            dy = barrel_y - player_y
            vertical_dist = abs(dy)

            # Barrel is approaching if within range and at similar height
            if horizontal_dist < 8 and vertical_dist < 6:
                # Check if barrel is moving toward us
                barrel_moving_right = barrel.get('velocity_x', 0) > 0
                barrel_coming = (barrel_moving_right and dx < 0 and dx > -8) or \
                               (not barrel_moving_right and dx > 0 and dx < 8)

                # Also jump if barrel is very close regardless of direction
                if horizontal_dist < 5 and vertical_dist < 4:
                    return True

                if barrel_coming and horizontal_dist < 6:
                    return True

        return False

    def _find_best_ladder(self):
        """Find the best ladder to climb toward Pauline."""
        game = self.game
        player_x = game.player_x
        player_y = game.player_y
        player_feet = player_y + game.PLAYER_HEIGHT

        best_ladder = None
        best_score = float('inf')

        for ladder in game.ladders:
            # Skip ladders that don't go up from our position
            # Ladder must have its bottom near or below our feet
            if ladder['y2'] < player_feet - 4:
                continue

            # Skip ladders that are above us (we can't reach them)
            if ladder['y2'] < player_feet - 8:
                continue

            # Check if this ladder is safe (no barrels nearby)
            if not self._is_ladder_safe(ladder):
                continue

            # For broken ladders, check if we're below the break point
            if ladder.get('broken', False):
                halfway = (ladder['y1'] + ladder['y2']) / 2
                if player_feet < halfway + 4:
                    # We're above the break, can't use this ladder
                    continue

            # Score: prefer ladders that are closer and lead higher up
            horizontal_dist = abs(ladder['x'] - player_x)
            vertical_benefit = player_feet - ladder['y1']  # How much we'd climb

            # Penalize horizontal distance, reward vertical climb
            score = horizontal_dist - vertical_benefit * 0.5

            if score < best_score:
                best_score = score
                best_ladder = ladder

        return best_ladder

    def _is_ladder_safe(self, ladder):
        """Check if a ladder is safe from barrels."""
        game = self.game
        ladder_x = ladder['x']
        ladder_y1 = ladder['y1']
        ladder_y2 = ladder['y2']

        for barrel in game.barrels:
            barrel_x = barrel['x']
            barrel_y = barrel['y']

            # Check if barrel is near the ladder
            if abs(barrel_x - ladder_x) < 6:
                # Check vertical overlap with ladder
                if barrel_y >= ladder_y1 - 4 and barrel_y <= ladder_y2 + 4:
                    return False

            # Check if barrel is about to fall onto the ladder
            if barrel.get('falling', False) or barrel.get('on_ladder', False):
                if abs(barrel_x - ladder_x) < 4:
                    return False

        return True
