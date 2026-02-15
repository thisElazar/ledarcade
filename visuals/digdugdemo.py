"""
Dig Dug Demo - AI Attract Mode
==============================
Dig Dug plays itself using simple AI for idle screen demos.
The AI digs toward enemies and pumps them until they pop.

AI Strategy:
- Find nearest enemy that isn't in ghost mode
- Move toward that enemy through tunnels or by digging
- When adjacent to enemy (within pump range ~8 pixels), hold pump button
- Avoid enemies in ghost mode (they can move through dirt)
- Avoid falling rocks
"""

import math
from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

# Import the actual game
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.digdug import DigDug


class DigDugDemo(Visual):
    name = "DIG DIG"
    description = "AI plays Dig Dug"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = DigDug(self.display)
        self.game.reset()
        self.decision_timer = 0.0
        self.decision_interval = 0.05  # Recalculate every 50ms
        self.ai_move = {'left': False, 'right': False, 'up': False, 'down': False, 'pump': False}
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
            self.ai_move = self._decide_action()

        # Create input state with AI's chosen actions
        ai_input = InputState()
        ai_input.left = self.ai_move['left']
        ai_input.right = self.ai_move['right']
        ai_input.up = self.ai_move['up']
        ai_input.down = self.ai_move['down']
        ai_input.action_l_held = self.ai_move['pump']

        self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()

        # Overlay "DEMO" text
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)

    def _decide_action(self):
        """AI decision-making for Dig Dug movement and pumping."""
        game = self.game
        player_x = game.player_x
        player_y = game.player_y

        move = {'left': False, 'right': False, 'up': False, 'down': False, 'pump': False}

        # Priority 1: Avoid falling rocks
        for rock in game.rocks:
            if rock['falling']:
                # Rock is falling - avoid it
                rock_x, rock_y = rock['x'], rock['y']
                # If rock is above us and close horizontally
                if rock_y < player_y and abs(rock_x - player_x) <= 4:
                    # Move away horizontally
                    if rock_x <= player_x:
                        move['right'] = True
                    else:
                        move['left'] = True
                    return move

        # Priority 2: Avoid ghost mode enemies (they're dangerous)
        for enemy in game.enemies:
            if enemy['ghost_mode'] and enemy['inflate'] == 0:
                ex, ey = enemy['x'], enemy['y']
                dist = abs(ex - player_x) + abs(ey - player_y)
                if dist <= 8:
                    # Ghost enemy is close - move away
                    move = self._move_away_from(player_x, player_y, ex, ey)
                    return move

        # Priority 3: Find and attack nearest non-ghost enemy
        target_enemy = self._find_target_enemy()

        if target_enemy is None:
            # No enemies left, level will advance
            return move

        ex, ey = target_enemy['x'], target_enemy['y']
        dist = abs(ex - player_x) + abs(ey - player_y)

        # If we're close enough to pump, do it
        if dist <= 8:
            # Face toward the enemy and pump
            move['pump'] = True

            # Update facing direction toward enemy
            dx = ex - player_x
            dy = ey - player_y

            # Also move toward enemy to stay in range
            if abs(dx) > abs(dy):
                if dx > 0:
                    move['right'] = True
                elif dx < 0:
                    move['left'] = True
            else:
                if dy > 0:
                    move['down'] = True
                elif dy < 0:
                    move['up'] = True
        else:
            # Move toward the enemy
            move = self._move_toward(player_x, player_y, ex, ey)

        return move

    def _find_target_enemy(self):
        """Find the nearest enemy that isn't in ghost mode."""
        game = self.game
        player_x = game.player_x
        player_y = game.player_y

        nearest_enemy = None
        nearest_dist = float('inf')

        for enemy in game.enemies:
            # Skip ghost mode enemies (too dangerous to approach)
            if enemy['ghost_mode']:
                continue

            # Skip enemies that are about to pop
            if enemy['inflate'] >= 3:
                continue

            ex, ey = enemy['x'], enemy['y']
            dist = abs(ex - player_x) + abs(ey - player_y)

            if dist < nearest_dist:
                nearest_dist = dist
                nearest_enemy = enemy

        # If all enemies are in ghost mode, target the one with least ghost time
        if nearest_enemy is None and game.enemies:
            # Find enemy closest to exiting ghost mode
            for enemy in game.enemies:
                if enemy['inflate'] < 3:
                    ex, ey = enemy['x'], enemy['y']
                    dist = abs(ex - player_x) + abs(ey - player_y)
                    if dist < nearest_dist:
                        nearest_dist = dist
                        nearest_enemy = enemy

        return nearest_enemy

    def _move_toward(self, px, py, tx, ty):
        """Determine movement direction to move toward a target."""
        move = {'left': False, 'right': False, 'up': False, 'down': False, 'pump': False}

        dx = tx - px
        dy = ty - py

        # Prefer moving in the direction with larger distance
        if abs(dx) > abs(dy):
            if dx > 0:
                move['right'] = True
            elif dx < 0:
                move['left'] = True
        else:
            if dy > 0:
                move['down'] = True
            elif dy < 0:
                move['up'] = True

        return move

    def _move_away_from(self, px, py, ex, ey):
        """Determine movement direction to move away from a threat."""
        move = {'left': False, 'right': False, 'up': False, 'down': False, 'pump': False}

        dx = px - ex  # Opposite direction
        dy = py - ey

        # Move away, preferring the direction with more space
        if abs(dx) >= abs(dy):
            if dx >= 0 and px < GRID_SIZE - 3:
                move['right'] = True
            elif dx < 0 and px > 3:
                move['left'] = True
            elif dy >= 0 and py < GRID_SIZE - 3:
                move['down'] = True
            elif dy < 0 and py > 10:
                move['up'] = True
        else:
            if dy >= 0 and py < GRID_SIZE - 3:
                move['down'] = True
            elif dy < 0 and py > 10:
                move['up'] = True
            elif dx >= 0 and px < GRID_SIZE - 3:
                move['right'] = True
            elif dx < 0 and px > 3:
                move['left'] = True

        return move
