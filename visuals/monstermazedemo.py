"""
3D Monster Maze Demo - AI Attract Mode
========================================
AI navigates the maze using BFS to find the exit while fleeing the Rex.
Auto-restarts on game over.
"""

from collections import deque
from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.monstermaze import MonsterMaze, MAZE_SIZE, DX, DY, RexState


class MonsterMazeDemo(Visual):
    name = "3D MONSTR MAZE"
    description = "AI escapes the T-Rex"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = MonsterMaze(self.display)
        self.game.reset()
        self.decision_timer = 0.0
        self.decision_interval = 0.55
        self.pending_input = None  # single-frame input to send next frame
        self.game_over_timer = 0.0

    def handle_input(self, input_state):
        return False

    def update(self, dt):
        self.time += dt

        if self.game.state == GameState.GAME_OVER:
            self.game_over_timer += dt
            if self.game_over_timer > 3.0:
                self.game.reset()
                self.game_over_timer = 0.0
            return

        # Send pending single-frame input, then clear it
        if self.pending_input:
            self.game.update(self.pending_input, dt)
            self.pending_input = None
            return

        # Tick with blank input between decisions
        self.decision_timer += dt
        if self.decision_timer >= self.decision_interval:
            self.decision_timer = 0.0
            self.pending_input = self._decide()

        self.game.update(InputState(), dt)

    def draw(self):
        if self.game.state == GameState.GAME_OVER:
            self.game.draw_game_over(0)
        else:
            self.game.draw()

        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, STATUS_Y, "DEMO", Colors.GRAY)

    def _decide(self):
        """AI: BFS to exit, flee Rex when close."""
        inp = InputState()
        g = self.game

        # During non-playing phases just wait for auto-advance
        if g.phase != 'playing':
            return inp

        px, py = g.px, g.py
        facing = g.facing

        # Find BFS path to exit
        target_x, target_y = g.exit_x, g.exit_y

        # If Rex is close and in pursuit, flee
        if g.rex_state in (RexState.SEEN, RexState.BEHIND):
            rex_dist = _bfs_dist(g.walls, px, py, g.rex_x, g.rex_y)
            if rex_dist != -1 and rex_dist <= 3:
                flee_target = self._flee_target(g)
                if flee_target:
                    target_x, target_y = flee_target

        # BFS next step toward target
        nxt = _bfs_next(g.walls, px, py, target_x, target_y)
        if nxt is None:
            return inp

        nx, ny = nxt
        # Determine required facing
        ddx, ddy = nx - px, ny - py
        needed_facing = -1
        for d in range(4):
            if DX[d] == ddx and DY[d] == ddy:
                needed_facing = d
                break

        if needed_facing == -1:
            return inp

        if needed_facing == facing:
            inp.up_pressed = True
        elif (facing + 1) % 4 == needed_facing:
            inp.right_pressed = True
        elif (facing - 1) % 4 == needed_facing:
            inp.left_pressed = True
        else:
            # 180: turn right (will take 2 decisions)
            inp.right_pressed = True

        return inp

    def _flee_target(self, g):
        """Find an open cell far from Rex to flee toward."""
        best = None
        best_dist = -1
        for y in range(MAZE_SIZE):
            for x in range(MAZE_SIZE):
                if g.walls[y][x]:
                    continue
                rd = abs(x - g.rex_x) + abs(y - g.rex_y)
                pd = abs(x - g.px) + abs(y - g.py)
                score = rd - pd
                if score > best_dist:
                    best_dist = score
                    best = (x, y)
        return best


# Status bar y for "DEMO" overlay
STATUS_Y = 44


def _bfs_dist(walls, sx, sy, tx, ty):
    if walls[sy][sx] or walls[ty][tx]:
        return -1
    if sx == tx and sy == ty:
        return 0
    visited = set()
    visited.add((sx, sy))
    q = deque([(sx, sy, 0)])
    while q:
        cx, cy, d = q.popleft()
        for i in range(4):
            nx, ny = cx + DX[i], cy + DY[i]
            if 0 <= nx < MAZE_SIZE and 0 <= ny < MAZE_SIZE and not walls[ny][nx] and (nx, ny) not in visited:
                if nx == tx and ny == ty:
                    return d + 1
                visited.add((nx, ny))
                q.append((nx, ny, d + 1))
    return -1


def _bfs_next(walls, sx, sy, tx, ty):
    if sx == tx and sy == ty:
        return None
    if walls[sy][sx] or walls[ty][tx]:
        return None
    visited = set()
    visited.add((sx, sy))
    parent = {}
    q = deque([(sx, sy)])
    while q:
        cx, cy = q.popleft()
        for i in range(4):
            nx, ny = cx + DX[i], cy + DY[i]
            if 0 <= nx < MAZE_SIZE and 0 <= ny < MAZE_SIZE and not walls[ny][nx] and (nx, ny) not in visited:
                visited.add((nx, ny))
                parent[(nx, ny)] = (cx, cy)
                if nx == tx and ny == ty:
                    cur = (tx, ty)
                    while parent[cur] != (sx, sy):
                        cur = parent[cur]
                    return cur
                q.append((nx, ny))
    return None
