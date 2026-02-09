"""
D&D Demo - AI Attract Mode
===========================
AI-controlled dungeon crawler for idle screen demos.
Uses BFS pathfinding to navigate corridors, collect items,
fight monsters with arrows, and descend deeper when the boss is slain.
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState
import math
import random
from collections import deque
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
        self.shoot_cooldown = 0.0
        self.path = []
        self.path_target = None
        self.retarget_timer = 0.0

    def handle_input(self, input_state):
        return False

    def _bfs_path(self, sx, sy, tx, ty):
        """BFS on dungeon grid. Returns list of (x, y) steps from start to target."""
        sx, sy, tx, ty = int(sx), int(sy), int(tx), int(ty)
        dungeon = self.game.dungeon
        w = self.game.DUNGEON_WIDTH
        h = self.game.DUNGEON_HEIGHT

        if not (0 <= tx < w and 0 <= ty < h):
            return []
        if dungeon[ty][tx] != 0:
            return []

        visited = set()
        visited.add((sx, sy))
        parent = {}
        queue = deque()
        queue.append((sx, sy))

        while queue:
            cx, cy = queue.popleft()
            if abs(cx - tx) <= 1 and abs(cy - ty) <= 1:
                # Reconstruct path
                path = [(cx, cy)]
                while (cx, cy) in parent:
                    cx, cy = parent[(cx, cy)]
                    path.append((cx, cy))
                path.reverse()
                return path[1:]  # skip start position

            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = cx + dx, cy + dy
                if (nx, ny) in visited:
                    continue
                if not (0 <= nx < w and 0 <= ny < h):
                    continue
                if dungeon[ny][nx] != 0:
                    continue
                visited.add((nx, ny))
                parent[(nx, ny)] = (cx, cy)
                queue.append((nx, ny))

        return []

    def _pick_target(self):
        """Choose target: items > exit (if boss dead) > boss > explore."""
        px, py = self.game.player_x, self.game.player_y

        # Nearby visible items (prefer health when hurt)
        best_item, best_d = None, float('inf')
        for item in self.game.items:
            ix, iy = int(item['x']), int(item['y'])
            if not (0 <= ix < self.game.DUNGEON_WIDTH and 0 <= iy < self.game.DUNGEON_HEIGHT):
                continue
            if not self.game.revealed[iy][ix]:
                continue
            d = math.hypot(item['x'] - px, item['y'] - py)
            if self.game.health < self.game.max_health and item['type'] == 'health':
                d *= 0.4
            if d < best_d:
                best_d, best_item = d, item
        if best_item and best_d < 60:
            return float(best_item['x']), float(best_item['y'])

        boss_alive = any(m['is_boss'] for m in self.game.monsters)
        if not boss_alive:
            return float(self.game.exit_x), float(self.game.exit_y)

        for m in self.game.monsters:
            if m['is_boss']:
                mx, my = int(m['x']), int(m['y'])
                if 0 <= mx < self.game.DUNGEON_WIDTH and 0 <= my < self.game.DUNGEON_HEIGHT:
                    if self.game.revealed[my][mx]:
                        return float(m['x']), float(m['y'])

        # Explore: pick a random revealed floor tile
        for _ in range(80):
            x = random.randint(2, self.game.DUNGEON_WIDTH - 3)
            y = random.randint(2, self.game.DUNGEON_HEIGHT - 3)
            if self.game.dungeon[y][x] == 0 and self.game.revealed[y][x]:
                return float(x), float(y)

        return px, py

    def _recompute_path(self):
        """Pick a target and compute BFS path to it."""
        tx, ty = self._pick_target()
        self.path_target = (tx, ty)
        self.path = self._bfs_path(self.game.player_x, self.game.player_y, tx, ty)

    def _find_nearby_monster(self, max_range=20):
        """Return closest visible monster within max_range, or None."""
        px, py = self.game.player_x, self.game.player_y
        best, best_dist = None, float('inf')
        for m in self.game.monsters:
            mx, my = int(m['x']), int(m['y'])
            if not (0 <= mx < self.game.DUNGEON_WIDTH and 0 <= my < self.game.DUNGEON_HEIGHT):
                continue
            if not self.game.revealed[my][mx]:
                continue
            d = math.hypot(m['x'] - px, m['y'] - py)
            if d < best_dist and d < max_range:
                best_dist, best = d, m
        return best

    def update(self, dt):
        self.time += dt

        # Game over: restart after 3s
        if self.game.state == GameState.GAME_OVER:
            self.game_over_timer += dt
            if self.game_over_timer > 3.0:
                self.game.reset()
                self.game_over_timer = 0.0
                self.path = []
                self.path_target = None
                self.retarget_timer = 0.0
                self.shoot_cooldown = 0.0
            return

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= dt

        # Periodic retarget or when path exhausted
        self.retarget_timer -= dt
        if self.retarget_timer <= 0 or not self.path:
            self._recompute_path()
            self.retarget_timer = random.uniform(1.5, 3.0)

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
        elif self.path:
            # Follow BFS path
            next_x, next_y = self.path[0]
            dx = next_x - px
            dy = next_y - py

            # If close enough to waypoint, advance to next
            if abs(dx) < 1.5 and abs(dy) < 1.5:
                self.path.pop(0)
                if self.path:
                    next_x, next_y = self.path[0]
                    dx = next_x - px
                    dy = next_y - py
                else:
                    dx, dy = 0, 0

            if abs(dx) > 0.5:
                ai_input.right = dx > 0
                ai_input.left = dx <= 0
            if abs(dy) > 0.5:
                ai_input.down = dy > 0
                ai_input.up = dy <= 0

        self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)
