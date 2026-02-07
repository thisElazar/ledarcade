"""
Windows 95 3D Maze Screensaver
==============================
First-person raycasted walk through a randomly generated maze with
procedural brick-textured walls, auto-navigation, distance fog, and
periodic maze regeneration with cycling wall themes.
"""

import math
import random
from . import Visual, Display, GRID_SIZE

# Maze grid dimensions (odd numbers ensure walls on borders and corridors on odd cells)
MAZE_W = 21
MAZE_H = 21

# Wall themes: (name, brick_base, mortar, ceiling, floor)
THEMES = [
    # Brick - classic Win95 red brick
    ((180, 60, 40), (80, 40, 30), (60, 60, 80), (50, 40, 35)),
    # Stone - gray castle stone
    ((140, 140, 150), (80, 80, 90), (40, 40, 55), (55, 50, 45)),
    # Hedge - garden maze
    ((30, 120, 40), (20, 70, 25), (100, 150, 200), (45, 80, 35)),
    # Blue Panel - tech corridors
    ((40, 80, 180), (25, 50, 120), (20, 20, 40), (40, 40, 50)),
]

TEX_SIZE = 16


class Win95Maze(Visual):
    name = "MAZE"
    description = "3D maze screensaver"
    category = "digital"

    def reset(self):
        self.time = 0.0
        self.theme_idx = 0
        self.regen_timer = 0.0
        self.regen_interval = 50.0

        # FOV and ray setup
        self.fov = math.pi / 3  # 60 degrees
        self.ray_offsets = []
        for col in range(GRID_SIZE):
            self.ray_offsets.append((col / GRID_SIZE - 0.5) * self.fov)

        # Movement
        self.move_speed = 2.5
        self.rot_speed = 2.5
        self.auto_walk = True

        # Generate first maze
        self._new_maze()

    def _new_maze(self):
        """Generate a new maze and reset player/navigation state."""
        self._generate_maze()
        self._build_texture()

        # Find a random open cell to start in
        open_cells = []
        for y in range(1, MAZE_H, 2):
            for x in range(1, MAZE_W, 2):
                if not self.maze[y][x]:
                    open_cells.append((x, y))
        if open_cells:
            sx, sy = random.choice(open_cells)
        else:
            sx, sy = 1, 1
        self.px = sx + 0.5
        self.py = sy + 0.5
        self.pa = random.uniform(0, 2 * math.pi)

        # Navigation state
        self.target_x = self.px
        self.target_y = self.py
        self.has_target = False
        self.stuck_timer = 0.0
        self.manual_idle = 0.0

    def _generate_maze(self):
        """Recursive backtracker maze generation on a MAZE_W x MAZE_H grid."""
        self.maze = [[True] * MAZE_W for _ in range(MAZE_H)]

        # Carve from (1,1)
        stack = [(1, 1)]
        self.maze[1][1] = False
        directions = [(0, -2), (0, 2), (-2, 0), (2, 0)]

        while stack:
            cx, cy = stack[-1]
            neighbors = []
            for dx, dy in directions:
                nx, ny = cx + dx, cy + dy
                if 0 < nx < MAZE_W - 1 and 0 < ny < MAZE_H - 1 and self.maze[ny][nx]:
                    neighbors.append((nx, ny, dx, dy))

            if neighbors:
                nx, ny, dx, dy = random.choice(neighbors)
                # Carve the wall between current and neighbor
                self.maze[cy + dy // 2][cx + dx // 2] = False
                self.maze[ny][nx] = False
                stack.append((nx, ny))
            else:
                stack.pop()

    def _build_texture(self):
        """Build a 16x16 procedural brick texture for current theme."""
        brick, mortar, self.ceil_color, self.floor_color = THEMES[self.theme_idx]
        self.texture = []
        for ty in range(TEX_SIZE):
            for tx in range(TEX_SIZE):
                # Determine if this pixel is mortar
                row_band = ty % 4
                is_h_mortar = (row_band == 0)
                # Vertical mortar offset every other row-group
                row_group = ty // 4
                offset = 4 if (row_group % 2) else 0
                col_band = (tx + offset) % 8
                is_v_mortar = (col_band == 0)
                if is_h_mortar or is_v_mortar:
                    self.texture.append(mortar)
                else:
                    # Slight per-brick variation
                    variation = ((tx * 7 + ty * 13) % 5) - 2
                    r = max(0, min(255, brick[0] + variation * 3))
                    g = max(0, min(255, brick[1] + variation * 2))
                    b = max(0, min(255, brick[2] + variation * 2))
                    self.texture.append((r, g, b))

    def _solid(self, x, y, margin=0.2):
        """Check collision against maze walls."""
        for dx in (-margin, margin):
            for dy in (-margin, margin):
                mx = int(x + dx)
                my = int(y + dy)
                if mx < 0 or mx >= MAZE_W or my < 0 or my >= MAZE_H:
                    return True
                if self.maze[my][mx]:
                    return True
        return False

    # ------------------------------------------------------------------
    # Auto-navigation (right-hand wall follower)
    # ------------------------------------------------------------------

    def _navigate(self, dt):
        """Move toward current target cell, pick new targets using wall-following."""
        # Pick a new target if we don't have one or reached current target
        dx = self.target_x - self.px
        dy = self.target_y - self.py
        dist = math.sqrt(dx * dx + dy * dy)

        if not self.has_target or dist < 0.3:
            self._pick_next_target()
            dx = self.target_x - self.px
            dy = self.target_y - self.py
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < 0.01:
                return

        # Smooth rotation toward target
        target_a = math.atan2(dy, dx)
        diff = target_a - self.pa
        while diff > math.pi:
            diff -= 2 * math.pi
        while diff < -math.pi:
            diff += 2 * math.pi
        self.pa += diff * min(1.0, 4.0 * dt)

        # Only move forward when roughly facing the target
        if abs(diff) < 1.0:
            speed = self.move_speed * dt
            cos_a = math.cos(self.pa)
            sin_a = math.sin(self.pa)
            nx = self.px + cos_a * speed
            ny = self.py + sin_a * speed
            moved = False
            if not self._solid(nx, self.py):
                self.px = nx
                moved = True
            if not self._solid(self.px, ny):
                self.py = ny
                moved = True
            if not moved:
                self.stuck_timer += dt
                if self.stuck_timer > 1.5:
                    # Unstick: pick a new target
                    self.has_target = False
                    self.stuck_timer = 0.0
            else:
                self.stuck_timer = 0.0

    def _pick_next_target(self):
        """Choose next cell to navigate to using right-hand wall following."""
        # Current cell
        cx = int(self.px)
        cy = int(self.py)

        # Get the direction we're roughly facing as a cardinal
        # 0=E, 1=S, 2=W, 3=N
        a = self.pa % (2 * math.pi)
        if a < 0:
            a += 2 * math.pi
        if a < math.pi * 0.25 or a >= math.pi * 1.75:
            facing = 0  # East
        elif a < math.pi * 0.75:
            facing = 1  # South
        elif a < math.pi * 1.25:
            facing = 2  # West
        else:
            facing = 3  # North

        # Cardinal direction vectors: E, S, W, N
        dirs = [(1, 0), (0, 1), (-1, 0), (0, -1)]

        # Right-hand rule: try right, then straight, then left, then back
        for turn in [1, 0, 3, 2]:
            d = (facing + turn) % 4
            ddx, ddy = dirs[d]
            nx, ny = cx + ddx, cy + ddy
            if 0 <= nx < MAZE_W and 0 <= ny < MAZE_H and not self.maze[ny][nx]:
                self.target_x = nx + 0.5
                self.target_y = ny + 0.5
                self.has_target = True
                return

        # Fallback: stay put
        self.target_x = cx + 0.5
        self.target_y = cy + 0.5
        self.has_target = True

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def handle_input(self, input_state) -> bool:
        # Button press regenerates the maze
        if input_state.action_l or input_state.action_r:
            self.regen_timer = 0.0
            self.theme_idx = (self.theme_idx + 1) % len(THEMES)
            self._new_maze()
            self.auto_walk = True
            return True
        # Arrow keys take manual control; auto-walk resumes after 1s idle
        if input_state.any_direction:
            self.auto_walk = False
            self.manual_idle = 0.0
        self._input = input_state
        return input_state.any_direction

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float):
        self.time += dt
        self.regen_timer += dt

        # Regenerate maze periodically
        if self.regen_timer >= self.regen_interval:
            self.regen_timer = 0.0
            self.theme_idx = (self.theme_idx + 1) % len(THEMES)
            self._new_maze()
            self.auto_walk = True
            return

        if self.auto_walk:
            self._navigate(dt)
        else:
            inp = getattr(self, '_input', None)
            if inp and inp.any_direction:
                self.manual_idle = 0.0
            else:
                self.manual_idle = getattr(self, 'manual_idle', 0.0) + dt
                if self.manual_idle >= 1.0:
                    self.auto_walk = True
                    self.has_target = False
            self._manual_move(dt)

    def _manual_move(self, dt):
        inp = getattr(self, '_input', None)
        if inp is None:
            return
        cos_a = math.cos(self.pa)
        sin_a = math.sin(self.pa)
        speed = self.move_speed * dt
        nx, ny = self.px, self.py
        if inp.up:
            nx += cos_a * speed
            ny += sin_a * speed
        if inp.down:
            nx -= cos_a * speed
            ny -= sin_a * speed
        if inp.left:
            self.pa -= self.rot_speed * dt
        if inp.right:
            self.pa += self.rot_speed * dt
        if not self._solid(nx, self.py):
            self.px = nx
        if not self._solid(self.px, ny):
            self.py = ny

    # ------------------------------------------------------------------
    # Raycaster + draw
    # ------------------------------------------------------------------

    def draw(self):
        half = GRID_SIZE // 2

        # Fill ceiling and floor
        ceil = self.ceil_color
        flr = self.floor_color
        for y in range(half):
            for x in range(GRID_SIZE):
                self.display.set_pixel(x, y, ceil)
        for y in range(half, GRID_SIZE):
            for x in range(GRID_SIZE):
                self.display.set_pixel(x, y, flr)

        # Cast rays
        for col in range(GRID_SIZE):
            ray_angle = self.pa + self.ray_offsets[col]
            self._cast_ray(col, ray_angle)

    def _cast_ray(self, col, angle):
        """DDA ray cast for one screen column."""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        if abs(cos_a) < 1e-8:
            cos_a = 1e-8
        if abs(sin_a) < 1e-8:
            sin_a = 1e-8

        # DDA setup
        map_x = int(self.px)
        map_y = int(self.py)

        delta_x = abs(1.0 / cos_a)
        delta_y = abs(1.0 / sin_a)

        if cos_a < 0:
            step_x = -1
            side_dist_x = (self.px - map_x) * delta_x
        else:
            step_x = 1
            side_dist_x = (map_x + 1.0 - self.px) * delta_x

        if sin_a < 0:
            step_y = -1
            side_dist_y = (self.py - map_y) * delta_y
        else:
            step_y = 1
            side_dist_y = (map_y + 1.0 - self.py) * delta_y

        # DDA loop
        hit = False
        side = 0
        for _ in range(40):
            if side_dist_x < side_dist_y:
                side_dist_x += delta_x
                map_x += step_x
                side = 0
            else:
                side_dist_y += delta_y
                map_y += step_y
                side = 1

            if map_x < 0 or map_x >= MAZE_W or map_y < 0 or map_y >= MAZE_H:
                break
            if self.maze[map_y][map_x]:
                hit = True
                break

        if not hit:
            return

        # Perpendicular distance (fisheye correction)
        if side == 0:
            perp_dist = (map_x - self.px + (1 - step_x) / 2) / cos_a
        else:
            perp_dist = (map_y - self.py + (1 - step_y) / 2) / sin_a

        if perp_dist < 0.01:
            perp_dist = 0.01

        # Wall strip
        line_height = int(GRID_SIZE / perp_dist)
        draw_start = max(0, GRID_SIZE // 2 - line_height // 2)
        draw_end = min(GRID_SIZE - 1, GRID_SIZE // 2 + line_height // 2)

        # Texture u coordinate
        if side == 0:
            wall_x = self.py + perp_dist * sin_a
        else:
            wall_x = self.px + perp_dist * cos_a
        wall_x -= int(wall_x)

        tex_u = int(wall_x * TEX_SIZE)
        if tex_u >= TEX_SIZE:
            tex_u = TEX_SIZE - 1

        # Fog factor
        fog = min(1.0, 2.0 / (perp_dist + 0.5))
        if side == 1:
            fog *= 0.75

        for y in range(draw_start, draw_end + 1):
            # Texture v coordinate
            tex_v = int((y - (GRID_SIZE // 2 - line_height // 2)) * TEX_SIZE / line_height)
            if tex_v >= TEX_SIZE:
                tex_v = TEX_SIZE - 1
            if tex_v < 0:
                tex_v = 0

            r, g, b = self.texture[tex_v * TEX_SIZE + tex_u]
            r = int(r * fog)
            g = int(g * fog)
            b = int(b * fog)
            self.display.set_pixel(col, y, (r, g, b))
