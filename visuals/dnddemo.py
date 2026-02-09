"""
D&D Demo - AI Attract Mode
===========================
AI-controlled dungeon crawler for idle screen demos.
The AI explores rooms, collects items, fights monsters with arrows,
and descends deeper when the boss is slain.
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState
import math
import random
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.dnd import DnD


class DnDDemo(Visual):
    name = "DND"
    description = "AI dungeon crawl"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = DnD(self.display)
        self.game.reset()
        self.game_over_timer = 0.0
        self.target_x = self.game.player_x
        self.target_y = self.game.player_y
        self.retarget_timer = 0.0
        self.last_x = self.game.player_x
        self.last_y = self.game.player_y
        self.stuck_timer = 0.0
        self.shoot_cooldown = 0.0

    def handle_input(self, input_state):
        return False

    def _is_visible(self, x, y):
        """True if dungeon tile at (x,y) has been revealed."""
        ix, iy = int(x), int(y)
        if not (0 <= ix < self.game.DUNGEON_WIDTH and 0 <= iy < self.game.DUNGEON_HEIGHT):
            return False
        return self.game.revealed[iy][ix]

    def _find_nearby_monster(self, max_range=20):
        """Return closest visible monster within max_range, or None."""
        px, py = self.game.player_x, self.game.player_y
        best, best_dist = None, float('inf')
        for m in self.game.monsters:
            if not self._is_visible(m['x'], m['y']):
                continue
            d = math.hypot(m['x'] - px, m['y'] - py)
            if d < best_dist and d < max_range:
                best_dist, best = d, m
        return best

    def _random_floor_target(self):
        """Pick a random revealed floor tile as a wander target."""
        for _ in range(80):
            x = random.randint(2, self.game.DUNGEON_WIDTH - 3)
            y = random.randint(2, self.game.DUNGEON_HEIGHT - 3)
            if self.game.dungeon[y][x] == 0 and self.game.revealed[y][x]:
                return float(x), float(y)
        return self.game.player_x, self.game.player_y

    def _pick_target(self):
        """Choose target: items > exit (if boss dead) > boss > random."""
        px, py = self.game.player_x, self.game.player_y

        # Nearby visible items (prefer health when hurt)
        best_item, best_d = None, float('inf')
        for item in self.game.items:
            if not self._is_visible(item['x'], item['y']):
                continue
            d = math.hypot(item['x'] - px, item['y'] - py)
            if self.game.health < self.game.max_health and item['type'] == 'health':
                d *= 0.4
            if d < best_d:
                best_d, best_item = d, item
        if best_item and best_d < 50:
            return float(best_item['x']), float(best_item['y'])

        boss_alive = any(m['is_boss'] for m in self.game.monsters)
        if not boss_alive:
            return float(self.game.exit_x), float(self.game.exit_y)

        for m in self.game.monsters:
            if m['is_boss'] and self._is_visible(m['x'], m['y']):
                return float(m['x']), float(m['y'])

        return self._random_floor_target()

    def _reset_ai(self):
        """Reset AI state after game restart."""
        self.game_over_timer = 0.0
        self.retarget_timer = 0.0
        self.stuck_timer = 0.0
        self.shoot_cooldown = 0.0
        self.target_x = self.game.player_x
        self.target_y = self.game.player_y
        self.last_x = self.game.player_x
        self.last_y = self.game.player_y

    def update(self, dt):
        self.time += dt

        # Game over: restart after 3s
        if self.game.state == GameState.GAME_OVER:
            self.game_over_timer += dt
            if self.game_over_timer > 3.0:
                self.game.reset()
                self._reset_ai()
            return

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= dt

        # Stuck detection: if barely moved in 0.5s, pick new random target
        self.stuck_timer += dt
        if self.stuck_timer >= 0.5:
            moved = math.hypot(self.game.player_x - self.last_x,
                               self.game.player_y - self.last_y)
            self.last_x = self.game.player_x
            self.last_y = self.game.player_y
            self.stuck_timer = 0.0
            if moved < 1.5:
                self.target_x, self.target_y = self._random_floor_target()
                self.retarget_timer = random.uniform(2.0, 4.0)

        # Periodic retarget
        self.retarget_timer -= dt
        if self.retarget_timer <= 0:
            self.target_x, self.target_y = self._pick_target()
            self.retarget_timer = random.uniform(2.0, 4.0)

        # Build AI input
        ai_input = InputState()
        px, py = self.game.player_x, self.game.player_y

        # Combat: face nearby monster and shoot
        threat = self._find_nearby_monster(20)
        if threat and threat['type'] != 'blob':
            tdx, tdy = threat['x'] - px, threat['y'] - py
            if abs(tdx) > abs(tdy):
                ai_input.right = tdx > 0
                ai_input.left = tdx <= 0
            else:
                ai_input.down = tdy > 0
                ai_input.up = tdy <= 0
            if (self.game.arrows > 3 and len(self.game.active_arrows) < 2
                    and self.shoot_cooldown <= 0):
                ai_input.action_l = True
                self.shoot_cooldown = 0.35
        else:
            # Move toward target
            dx, dy = self.target_x - px, self.target_y - py
            if abs(dx) > 1:
                ai_input.right = dx > 0
                ai_input.left = dx <= 0
            if abs(dy) > 1:
                ai_input.down = dy > 0
                ai_input.up = dy <= 0

        self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)
