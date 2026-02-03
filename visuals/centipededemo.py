"""
Centipede Demo - AI Attract Mode
================================
Centipede plays itself using simple AI for idle screen demos.
The AI shoots at centipede segments while avoiding the spider.

AI Strategy:
- Prioritize spider if close (within 15px) - it's dangerous and worth 600 points
- Target nearest centipede head segment
- If no heads, target nearest body segment
- Move toward target's x position
- Move up/down to get clear shot (avoid mushrooms blocking)
- Shoot when roughly aligned
"""

import math
from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

# Import the actual game
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.centipede import Centipede


class CentipedeDemo(Visual):
    name = "CENTIPEDE DEMO"
    description = "AI plays Centipede"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = Centipede(self.display)
        self.game.reset()
        self.decision_timer = 0.0
        self.decision_interval = 0.05  # Recalculate every 50ms
        self.ai_move = {'left': False, 'right': False, 'up': False, 'down': False, 'shoot': False}

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
            self.ai_move = self._decide_action()

        # Create input state with AI's chosen actions
        ai_input = InputState()
        ai_input.left = self.ai_move['left']
        ai_input.right = self.ai_move['right']
        ai_input.up = self.ai_move['up']
        ai_input.down = self.ai_move['down']
        ai_input.action_l_held = self.ai_move['shoot']

        self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()

        # Overlay "DEMO" text
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)

    def _decide_action(self):
        """AI decision-making for Centipede movement and shooting."""
        game = self.game
        player_x = game.player_x
        player_y = game.player_y

        move = {'left': False, 'right': False, 'up': False, 'down': False, 'shoot': False}

        # Find target
        target = self._find_target()

        if target is None:
            # No target, just shoot upward
            move['shoot'] = True
            return move

        target_x, target_y = target

        # Calculate distance to target
        dx = target_x - player_x
        dy = target_y - player_y

        # Move toward target's x position
        if abs(dx) > 2:
            if dx > 0:
                move['right'] = True
            else:
                move['left'] = True

        # Check if we have a clear shot (no mushrooms blocking)
        has_clear_shot = self._has_clear_shot(player_x, player_y, target_x, target_y)

        if not has_clear_shot:
            # Move up/down to find clear shot
            # Try moving up if we can
            if player_y > game.PLAYER_AREA_TOP:
                move['up'] = True
            elif player_y < 61:
                move['down'] = True
        else:
            # We have a clear shot, try to align horizontally
            if abs(dx) <= 3:
                # Aligned enough to shoot
                move['shoot'] = True
                # Stop horizontal movement when shooting
                move['left'] = False
                move['right'] = False

        # Avoid spider - move away if too close
        if game.spider:
            spider_dx = game.spider['x'] - player_x
            spider_dy = game.spider['y'] - player_y
            spider_dist = math.sqrt(spider_dx * spider_dx + spider_dy * spider_dy)

            if spider_dist < 10:
                # Spider is close, prioritize dodging
                if abs(spider_dx) < 8:
                    # Move away horizontally
                    if spider_dx > 0:
                        move['left'] = True
                        move['right'] = False
                    else:
                        move['right'] = True
                        move['left'] = False

                if abs(spider_dy) < 8:
                    # Move away vertically
                    if spider_dy > 0 and player_y > game.PLAYER_AREA_TOP:
                        move['up'] = True
                        move['down'] = False
                    elif spider_dy < 0 and player_y < 61:
                        move['down'] = True
                        move['up'] = False

        return move

    def _find_target(self):
        """Find the best target to shoot at."""
        game = self.game
        player_x = game.player_x
        player_y = game.player_y

        # Priority 1: Spider if close (within 15px)
        if game.spider:
            spider_dx = game.spider['x'] - player_x
            spider_dy = game.spider['y'] - player_y
            spider_dist = math.sqrt(spider_dx * spider_dx + spider_dy * spider_dy)

            if spider_dist < 15:
                return (game.spider['x'], game.spider['y'])

        # Priority 2: Nearest centipede head
        nearest_head = None
        nearest_head_dist = float('inf')

        for seg in game.segments:
            if seg['is_head']:
                dx = seg['x'] - player_x
                dy = seg['y'] - player_y
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < nearest_head_dist:
                    nearest_head_dist = dist
                    nearest_head = (seg['x'], seg['y'])

        if nearest_head:
            return nearest_head

        # Priority 3: Nearest body segment
        nearest_body = None
        nearest_body_dist = float('inf')

        for seg in game.segments:
            if not seg['is_head']:
                dx = seg['x'] - player_x
                dy = seg['y'] - player_y
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < nearest_body_dist:
                    nearest_body_dist = dist
                    nearest_body = (seg['x'], seg['y'])

        if nearest_body:
            return nearest_body

        # No centipede segments, target spider or flea if present
        if game.spider:
            return (game.spider['x'], game.spider['y'])

        if game.flea:
            return (game.flea['x'], game.flea['y'])

        if game.scorpion:
            return (game.scorpion['x'], game.scorpion['y'])

        return None

    def _has_clear_shot(self, player_x, player_y, target_x, target_y):
        """Check if there's a clear vertical path to the target."""
        game = self.game

        # Check if any mushroom is blocking the shot
        # We shoot straight up, so check mushrooms in our column
        for (mx, my), _ in game.mushrooms.items():
            # Mushroom is in our column (within 3 pixels)
            if abs(mx - player_x) < 4:
                # Mushroom is between us and the target
                if my < player_y and my > target_y:
                    return False

        return True
