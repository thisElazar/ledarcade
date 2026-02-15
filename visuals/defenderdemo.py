"""
Defender Demo - AI Attract Mode
================================
Defender plays itself using simple AI for idle screen demos.

AI Strategy:
- Priority 1: Rescue captured/falling humans (fly to intercept)
- Priority 2: Dodge nearby enemy bullets
- Priority 3: Attack nearest diving lander that has a human
- Priority 4: Attack nearest visible enemy
- Auto-fire when facing enemy in range
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.defender import Defender


class DefenderDemo(Visual):
    name = "DEFENDR"
    description = "AI plays Defender"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = Defender(self.display)
        self.game.reset()
        self.ai_move_x = 0   # -1 left, 0 none, 1 right
        self.ai_move_y = 0   # -1 up, 0 none, 1 down
        self.ai_shoot = False
        self.ai_bomb = False
        self.decision_timer = 0.0
        self.decision_interval = 0.08

    def handle_input(self, input_state):
        return False

    def update(self, dt):
        self.time += dt

        if self.game.state == GameState.GAME_OVER:
            self.decision_timer += dt
            if self.decision_timer > 3.0:
                self.game.reset()
                self.decision_timer = 0.0
            return

        self.decision_timer += dt
        if self.decision_timer >= self.decision_interval:
            self.decision_timer = 0.0
            self._decide_action()

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
            ai_input.action_l_held = True
        if self.ai_bomb:
            ai_input.action_r = True
            self.ai_bomb = False  # Single press

        self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()

        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)

    def _decide_action(self):
        g = self.game
        px, py = g.px, g.py

        # Priority 1: Rescue captured/falling humans
        target = self._find_rescue_target()
        if target:
            self._move_toward(target['wx'], target['wy'] - 2)
            self.ai_shoot = False
            return

        # Priority 2: Dodge nearby enemy bullets
        dodge_x, dodge_y = self._check_dodge()
        if dodge_x != 0 or dodge_y != 0:
            self.ai_move_x = dodge_x
            self.ai_move_y = dodge_y
            self.ai_shoot = False
            return

        # Priority 3: Use smart bomb if overwhelmed
        visible_enemies = sum(1 for e in g.enemies if e['alive'] and g._is_visible(e['wx']))
        if visible_enemies >= 5 and g.smart_bombs > 0:
            self.ai_bomb = True

        # Priority 4: Attack nearest enemy
        target_e = self._find_nearest_enemy()
        if target_e:
            dx = g._world_dist_x(px, target_e['wx'])
            dy = target_e['wy'] - py

            # Face the enemy
            if dx > 0:
                want_facing = 1
            else:
                want_facing = -1

            # If facing wrong way, turn around
            if g.facing != want_facing:
                self.ai_move_x = want_facing
                self.ai_shoot = False
                return

            # Move toward enemy's y level
            if abs(dy) > 3:
                self.ai_move_y = 1 if dy > 0 else -1
            else:
                self.ai_move_y = 0

            # Move toward enemy horizontally if far, but stay at range if close
            abs_dx = abs(dx)
            if abs_dx > 40:
                self.ai_move_x = want_facing
                self.ai_shoot = False
            elif abs_dx > 5:
                self.ai_move_x = want_facing
                self.ai_shoot = abs(dy) < 4  # Shoot if vertically aligned
            else:
                # Very close, keep some distance
                self.ai_move_x = -want_facing
                self.ai_shoot = abs(dy) < 4
        else:
            # No enemies visible, patrol
            self.ai_move_x = g.facing
            self.ai_move_y = -1 if py > 25 else (1 if py < 15 else 0)
            self.ai_shoot = False

    def _find_rescue_target(self):
        g = self.game
        best = None
        best_dist = float('inf')
        for h in g.humans:
            if h['state'] in ('captured', 'falling'):
                dist = abs(g._world_dist_x(g.px, h['wx']))
                if dist < best_dist:
                    best_dist = dist
                    best = h
        return best

    def _check_dodge(self):
        g = self.game
        for b in g.enemy_bullets:
            dx = g._world_dist_x(g.px, b['wx'])
            dy = b['wy'] - g.py
            if abs(dx) < 8 and abs(dy) < 8:
                # Dodge perpendicular to bullet direction
                dodge_x = -1 if dx > 0 else 1
                dodge_y = -1 if dy > 0 else 1
                return dodge_x, dodge_y
        # Also dodge close enemies
        for e in g.enemies:
            if not e['alive']:
                continue
            dx = g._world_dist_x(g.px, e['wx'])
            dy = e['wy'] - g.py
            if abs(dx) < 6 and abs(dy) < 6 and e['type'] == 'mutant':
                return (-1 if dx > 0 else 1), (-1 if dy > 0 else 1)
        return 0, 0

    def _find_nearest_enemy(self):
        g = self.game
        best = None
        best_dist = float('inf')
        for e in g.enemies:
            if not e['alive']:
                continue
            dist = abs(g._world_dist_x(g.px, e['wx']))
            # Prioritize landers that are diving (have a target human)
            priority = 0
            if e['type'] == 'lander' and e['target_human']:
                priority = -100  # Lower = higher priority
            if dist + priority < best_dist:
                best_dist = dist + priority
                best = e
        return best

    def _move_toward(self, target_wx, target_wy):
        g = self.game
        dx = g._world_dist_x(g.px, target_wx)
        dy = target_wy - g.py

        if abs(dx) > 3:
            self.ai_move_x = 1 if dx > 0 else -1
        else:
            self.ai_move_x = 0
        if abs(dy) > 2:
            self.ai_move_y = 1 if dy > 0 else -1
        else:
            self.ai_move_y = 0
