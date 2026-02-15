"""
Pac-Man Demo - AI Attract Mode
==============================
Pac-Man plays itself using simple AI for idle screen demos.
The AI navigates toward pellets while avoiding ghosts.

AI Strategy:
- Find nearest reachable pellet using BFS
- Avoid tiles near ghosts (unless powered up)
- Chase frightened ghosts for bonus points
- Grab power pellets when ghosts are close
"""

import math
from collections import deque
from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

# Import the actual game
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.pacman import PacMan


class PacManDemo(Visual):
    name = "PAK-MAN"
    description = "AI plays Pac-Man"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = PacMan(self.display)
        self.game.reset()
        self.ai_dir = (0, 0)
        self.decision_timer = 0.0
        self.decision_interval = 0.1  # Recalculate every 100ms

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
            self.ai_dir = self._decide_direction()

        # Create input state with AI's chosen direction
        ai_input = InputState()
        if self.ai_dir == (0, -1):
            ai_input.up = True
        elif self.ai_dir == (0, 1):
            ai_input.down = True
        elif self.ai_dir == (-1, 0):
            ai_input.left = True
        elif self.ai_dir == (1, 0):
            ai_input.right = True

        self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()

        # Overlay "DEMO" text
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)

    def _decide_direction(self):
        """AI decision-making for Pac-Man movement."""
        game = self.game
        pac_x, pac_y = int(round(game.pac_x)), int(round(game.pac_y))

        # Check if any ghost is frightened (we should chase them)
        any_frightened = any(g['frightened'] and not g['eaten'] for g in game.ghosts)

        # Check if any ghost is dangerously close
        ghost_danger = self._get_ghost_danger_map()

        # Find target based on situation
        if any_frightened:
            # Chase the nearest frightened ghost
            target = self._find_nearest_frightened_ghost(pac_x, pac_y)
        else:
            # Find nearest safe pellet
            target = self._find_nearest_pellet(pac_x, pac_y, ghost_danger)

        if target is None:
            # No target found, try to survive
            return self._get_escape_direction(pac_x, pac_y, ghost_danger)

        # Get direction toward target using BFS path
        direction = self._get_direction_to_target(pac_x, pac_y, target, ghost_danger, any_frightened)
        return direction if direction else game.pac_dir

    def _get_ghost_danger_map(self):
        """Create a map of tiles that are dangerous due to nearby ghosts."""
        danger = set()
        game = self.game

        for ghost in game.ghosts:
            if ghost['eaten'] or ghost['in_house']:
                continue
            if ghost['frightened']:
                continue  # Frightened ghosts aren't dangerous

            gx, gy = int(round(ghost['x'])), int(round(ghost['y']))
            danger_radius = 3  # Tiles to avoid around each ghost

            for dx in range(-danger_radius, danger_radius + 1):
                for dy in range(-danger_radius, danger_radius + 1):
                    if abs(dx) + abs(dy) <= danger_radius:
                        tx, ty = gx + dx, gy + dy
                        if 0 <= tx < game.maze_width and 0 <= ty < game.maze_height:
                            danger.add((tx, ty))

        return danger

    def _find_nearest_pellet(self, start_x, start_y, danger):
        """BFS to find nearest pellet, preferring safe paths."""
        game = self.game
        queue = deque([(start_x, start_y, 0)])
        visited = {(start_x, start_y)}

        # First pass: look for safe pellets
        while queue:
            x, y, dist = queue.popleft()

            # Check if this tile has a pellet
            if 0 <= x < game.maze_width and 0 <= y < game.maze_height:
                tile = game.maze[y][x]
                if tile == 2 or tile == 3:  # Dot or power pellet
                    # Prefer power pellets if ghosts are close
                    if tile == 3 and len(danger) > 0:
                        return (x, y)
                    if (x, y) not in danger:
                        return (x, y)

            # Explore neighbors
            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                nx, ny = x + dx, y + dy
                # Handle tunnel wrap
                if nx < 0:
                    nx = game.maze_width - 1
                elif nx >= game.maze_width:
                    nx = 0

                if (nx, ny) not in visited:
                    if game.tile_passable(nx, ny, is_ghost=False):
                        visited.add((nx, ny))
                        queue.append((nx, ny, dist + 1))

        # If no safe pellets, find any pellet
        queue = deque([(start_x, start_y, 0)])
        visited = {(start_x, start_y)}

        while queue:
            x, y, dist = queue.popleft()

            if 0 <= x < game.maze_width and 0 <= y < game.maze_height:
                tile = game.maze[y][x]
                if tile == 2 or tile == 3:
                    return (x, y)

            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                nx, ny = x + dx, y + dy
                if nx < 0:
                    nx = game.maze_width - 1
                elif nx >= game.maze_width:
                    nx = 0

                if (nx, ny) not in visited:
                    if game.tile_passable(nx, ny, is_ghost=False):
                        visited.add((nx, ny))
                        queue.append((nx, ny, dist + 1))

        return None

    def _find_nearest_frightened_ghost(self, start_x, start_y):
        """Find the nearest frightened ghost to chase."""
        game = self.game
        nearest = None
        nearest_dist = float('inf')

        for ghost in game.ghosts:
            if ghost['frightened'] and not ghost['eaten']:
                gx, gy = int(round(ghost['x'])), int(round(ghost['y']))
                dist = abs(gx - start_x) + abs(gy - start_y)
                if dist < nearest_dist:
                    nearest_dist = dist
                    nearest = (gx, gy)

        return nearest

    def _get_direction_to_target(self, start_x, start_y, target, danger, ignore_danger=False):
        """BFS to find best direction toward target."""
        if target is None:
            return None

        game = self.game
        target_x, target_y = target

        # BFS to find path
        queue = deque([(start_x, start_y, None)])  # x, y, first_direction
        visited = {(start_x, start_y)}

        while queue:
            x, y, first_dir = queue.popleft()

            if x == target_x and y == target_y:
                return first_dir

            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                nx, ny = x + dx, y + dy

                # Handle tunnel wrap
                if nx < 0:
                    nx = game.maze_width - 1
                elif nx >= game.maze_width:
                    nx = 0

                if (nx, ny) not in visited:
                    if game.tile_passable(nx, ny, is_ghost=False):
                        # Avoid danger unless ignoring it
                        if not ignore_danger and (nx, ny) in danger:
                            continue
                        visited.add((nx, ny))
                        # Track the first direction taken
                        dir_to_use = first_dir if first_dir else (dx, dy)
                        queue.append((nx, ny, dir_to_use))

        # If no path avoiding danger, try ignoring danger
        if not ignore_danger:
            return self._get_direction_to_target(start_x, start_y, target, danger, True)

        return None

    def _get_escape_direction(self, pac_x, pac_y, danger):
        """Find direction that moves away from ghosts."""
        game = self.game
        best_dir = None
        best_safety = -1

        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            nx, ny = pac_x + dx, pac_y + dy

            # Handle tunnel wrap
            if nx < 0:
                nx = game.maze_width - 1
            elif nx >= game.maze_width:
                nx = 0

            if not game.tile_passable(nx, ny, is_ghost=False):
                continue

            # Calculate safety as distance from nearest ghost
            min_ghost_dist = float('inf')
            for ghost in game.ghosts:
                if ghost['eaten'] or ghost['in_house'] or ghost['frightened']:
                    continue
                gx, gy = int(round(ghost['x'])), int(round(ghost['y']))
                dist = abs(nx - gx) + abs(ny - gy)
                min_ghost_dist = min(min_ghost_dist, dist)

            if min_ghost_dist > best_safety:
                best_safety = min_ghost_dist
                best_dir = (dx, dy)

        return best_dir if best_dir else (0, 0)
