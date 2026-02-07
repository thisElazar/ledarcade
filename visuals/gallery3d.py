"""
3D Gallery - Raycaster art museum
==================================
Walk through a Wolfenstein-style 3D gallery displaying the project's
own paintings and sprites on the walls.

Controls:
  Up/Down    - Move forward/backward
  Left/Right - Rotate view
  (starts in auto-walk mode; any input takes manual control)
"""

import math
import os
from . import Visual, Display, Colors, GRID_SIZE

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Map dimensions
MAP_W = 16
MAP_H = 36

# 16x36 map: 0=empty, 1=wall, 2-9=painting, 10-15=immersive room walls
MAP = [
    # --- Original gallery (rows 0-15) ---
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],       # 0
    [1,0,0,0,1,0,0,0,0,0,0,1,0,0,0,1],       # 1
    [1,0,0,0,2,0,0,0,0,0,0,3,0,0,0,1],       # 2
    [1,0,0,0,1,0,0,0,0,0,0,1,0,0,0,1],       # 3
    [1,1,4,1,1,0,0,0,0,0,0,1,1,5,1,1],       # 4
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],       # 5
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],       # 6
    [1,0,0,0,0,0,0,1,1,0,0,0,0,0,0,1],       # 7
    [1,0,0,0,0,0,0,1,1,0,0,0,0,0,0,1],       # 8
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],       # 9
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],       # 10
    [1,1,6,1,1,0,0,0,0,0,0,1,1,7,1,1],       # 11
    [1,0,0,0,1,0,0,0,0,0,0,1,0,0,0,1],       # 12
    [1,0,0,0,8,0,0,0,0,0,0,9,0,0,0,1],       # 13
    [1,0,0,0,1,0,0,0,0,0,0,1,0,0,0,1],       # 14
    [1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1],       # 15 doorway at cols 7-8
    # --- South corridor + rooms (rows 16-35) ---
    [1,0,0,0,0,0,1,0,0,1,0,0,0,0,0,1],       # 16 corridor
    [1,0,0,0,0,0,1,0,0,1,0,0,0,0,0,1],       # 17 corridor
    [1,10,10,10,10,1,1,0,0,1,1,11,11,11,11,1],# 18 room top walls
    [1,10,0,0,10,10,1,0,0,1,11,11,0,0,11,1], # 19
    [1,10,0,0,0,0,0,0,0,0,0,0,0,0,11,1],     # 20 doorways face corridor
    [1,10,0,0,10,10,1,0,0,1,11,11,0,0,11,1], # 21
    [1,10,10,10,10,1,1,0,0,1,1,11,11,11,11,1],# 22 room bottom walls
    [1,0,0,0,0,0,1,0,0,1,0,0,0,0,0,1],       # 23 corridor
    [1,12,12,12,12,1,1,0,0,1,1,13,13,13,13,1],# 24 room top walls
    [1,12,0,0,12,12,1,0,0,1,13,13,0,0,13,1], # 25
    [1,12,0,0,0,0,0,0,0,0,0,0,0,0,13,1],     # 26 doorways
    [1,12,0,0,12,12,1,0,0,1,13,13,0,0,13,1], # 27
    [1,12,12,12,12,1,1,0,0,1,1,13,13,13,13,1],# 28 room bottom walls
    [1,0,0,0,0,0,1,0,0,1,0,0,0,0,0,1],       # 29 corridor
    [1,14,14,14,14,1,1,0,0,1,1,15,15,15,15,1],# 30 room top walls
    [1,14,0,0,14,14,1,0,0,1,15,15,0,0,15,1], # 31
    [1,14,0,0,0,0,0,0,0,0,0,0,0,0,15,1],     # 32 doorways
    [1,14,0,0,14,14,1,0,0,1,15,15,0,0,15,1], # 33
    [1,14,14,14,14,1,1,0,0,1,1,15,15,15,15,1],# 34 room bottom walls
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],       # 35 dead-end wall
]

# Auto-walk waypoints (x, y) in map coords
WAYPOINTS = [
    # --- Original gallery tour ---
    (2.5, 2.5),   # NW room
    (2.5, 6.0),   # exit NW room south
    (5.5, 6.0),   # central hall west
    (5.5, 2.5),   # look at painting 2 (east wall NW)
    (5.5, 6.0),   # back
    (8.0, 2.5),   # central north
    (10.5, 2.5),  # look at painting 3 (west wall NE)
    (13.5, 2.5),  # NE room
    (13.5, 6.0),  # exit NE room south
    (10.5, 6.0),  # central hall east
    (10.5, 9.5),  # central hall south
    (13.5, 9.5),  # SE approach
    (13.5, 13.5), # SE room
    (10.5, 13.5), # look at painting 9 (west wall SE)
    (10.5, 9.5),  # back
    (5.5, 9.5),   # central hall west
    (5.5, 13.5),  # look at painting 8 (east wall SW)
    (2.5, 13.5),  # SW room
    (2.5, 9.5),   # exit SW room north
    (8.0, 9.5),   # center south
    # --- South wing tour ---
    (7.5, 15.5),  # enter corridor doorway
    (7.5, 17.5),  # corridor south
    # Room 1: Plasma (left)
    (5.0, 20.5),  # enter Plasma room
    (3.0, 20.5),  # center of Plasma room
    (5.0, 20.5),  # exit Plasma room
    # Room 2: Fire (right)
    (11.0, 20.5), # enter Fire room
    (13.0, 20.5), # center of Fire room
    (11.0, 20.5), # exit Fire room
    (7.5, 20.5),  # corridor
    (7.5, 23.5),  # corridor south
    # Room 3: Matrix (left)
    (5.0, 26.5),  # enter Matrix room
    (3.0, 26.5),  # center of Matrix room
    (5.0, 26.5),  # exit Matrix room
    # Room 4: Starfield (right)
    (11.0, 26.5), # enter Starfield room
    (13.0, 26.5), # center of Starfield room
    (11.0, 26.5), # exit Starfield room
    (7.5, 26.5),  # corridor
    (7.5, 29.5),  # corridor south
    # Room 5: Demon Spirals (left)
    (5.0, 32.5),  # enter DemonSpirals room
    (3.0, 32.5),  # center of DemonSpirals room
    (5.0, 32.5),  # exit DemonSpirals room
    # Room 6: Moire (right)
    (11.0, 32.5), # enter Moire room
    (13.0, 32.5), # center of Moire room
    (11.0, 32.5), # exit Moire room
    # Return north
    (7.5, 32.5),  # corridor
    (7.5, 23.5),  # corridor north
    (7.5, 17.5),  # corridor north
    (7.5, 14.0),  # back through doorway
    (5.5, 6.0),   # back to center
]

# Gold frame color
GOLD = (180, 150, 50)
GOLD_DARK = (120, 100, 30)

# Immersive room definitions: cell_id -> (module, class, ceiling_tint, floor_tint)
IMMERSIVE_ROOMS = {
    10: ("plasma",       "Plasma",       (40, 20, 50), (50, 25, 60)),
    11: ("fire",         "Fire",         (60, 25, 10), (70, 30, 10)),
    12: ("matrix",       "Matrix",       (5, 30, 10),  (10, 40, 15)),
    13: ("starfield",    "Starfield",    (5, 5, 20),   (10, 10, 30)),
    14: ("demonspirals", "DemonSpirals", (40, 10, 40), (50, 15, 50)),
    15: ("moire",        "Moire",        (20, 20, 40), (30, 30, 50)),
}

# Immersive animation constants
IMMERSIVE_FPS = 8
IMMERSIVE_FRAMES = 24


class Gallery3D(Visual):
    name = "3D GALLERY"
    description = "Raycaster museum"
    category = "art"

    # Animation speed for sprite walls (frames per second)
    SPRITE_FPS = 6

    def __init__(self, display: Display):
        self.textures = {}  # slot_id -> list of flat 4096-RGB-tuple frames
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        # Player state
        self.px = 2.5   # position x (map coords)
        self.py = 6.0   # position y
        self.pa = 0.0   # angle (radians, 0 = east)
        self.move_speed = 3.0
        self.rot_speed = 2.5
        # FOV
        self.fov = math.pi / 3  # 60 degrees
        # Pre-compute ray angle offsets
        self.ray_offsets = []
        for col in range(GRID_SIZE):
            offset = (col / GRID_SIZE - 0.5) * self.fov
            self.ray_offsets.append(offset)
        # Auto-walk
        self.auto_walk = True
        self.wp_idx = 0
        self.wp_pause = 0.0
        # Load textures
        self._load_textures()

    # ------------------------------------------------------------------
    # Texture loading
    # ------------------------------------------------------------------

    def _load_textures(self):
        """Load all painting textures, sprites, and immersive room textures."""
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        assets = os.path.join(project_dir, "assets")

        # Static paintings (single frame each)
        self._load_png(2, os.path.join(assets, "greatwave.png"))
        self._load_png(3, os.path.join(assets, "scream.png"))
        self._capture_visual(4, "starrynight", "StarryNight")
        self._capture_visual(5, "waterlilies", "WaterLilies")
        self._capture_visual(6, "mondrian", "Mondrian")

        # Animated sprites (multiple frames)
        self._load_png_sequence(7, [
            os.path.join(assets, "mario_walk1.png"),
            os.path.join(assets, "mario_walk2.png"),
            os.path.join(assets, "mario_walk3.png"),
        ])
        self._load_png_sequence(8, [
            os.path.join(assets, "sonic_run1.png"),
            os.path.join(assets, "sonic_run2.png"),
            os.path.join(assets, "sonic_run3.png"),
            os.path.join(assets, "sonic_run4.png"),
        ])
        self._load_gif_frames(9, os.path.join(assets, "ani_link_spin.gif"))

        # Immersive room textures (multi-frame animated)
        self._load_immersive_textures()

    def _load_png(self, slot, path):
        """Load a single PNG as a one-frame texture."""
        self.textures[slot] = [self._read_png(path)]

    def _load_png_sequence(self, slot, paths):
        """Load multiple PNGs as animation frames for one slot."""
        frames = [self._read_png(p) for p in paths]
        self.textures[slot] = frames

    def _read_png(self, path):
        """Read a PNG into a flat 64x64 pixel list."""
        if not HAS_PIL or not os.path.exists(path):
            return self._solid_texture((80, 80, 80))
        try:
            img = Image.open(path).convert("RGB")
            img = img.resize((GRID_SIZE, GRID_SIZE), Image.Resampling.NEAREST)
            tex = []
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    tex.append(img.getpixel((x, y)))
            return tex
        except Exception:
            return self._solid_texture((80, 80, 80))

    def _load_gif_frames(self, slot, path, max_frames=12):
        """Load frames from an animated GIF with alpha onto a dark background."""
        if not HAS_PIL or not os.path.exists(path):
            self.textures[slot] = [self._solid_texture((80, 80, 80))]
            return
        try:
            bg = (20, 20, 30)
            gif = Image.open(path)
            n_frames = getattr(gif, 'n_frames', 1)
            # Sample evenly across the full animation
            step = max(1, n_frames // max_frames)
            frames = []
            for i in range(0, n_frames, step):
                gif.seek(i)
                frame = gif.convert("RGBA")
                frame = frame.resize((GRID_SIZE, GRID_SIZE), Image.Resampling.NEAREST)
                tex = []
                for y in range(GRID_SIZE):
                    for x in range(GRID_SIZE):
                        r, g, b, a = frame.getpixel((x, y))
                        if a > 128:
                            tex.append((r, g, b))
                        else:
                            tex.append(bg)
                frames.append(tex)
                if len(frames) >= max_frames:
                    break
            self.textures[slot] = frames if frames else [self._solid_texture((80, 80, 80))]
        except Exception:
            self.textures[slot] = [self._solid_texture((80, 80, 80))]

    def _capture_visual(self, slot, module_name, class_name):
        """Instantiate a visual, render one frame, capture as single-frame texture."""
        try:
            import importlib
            mod = importlib.import_module(f".{module_name}", package="visuals")
            cls = getattr(mod, class_name)
            vis = cls(self.display)
            vis.update(0.5)
            vis.draw()
            tex = []
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    tex.append(self.display.get_pixel(x, y))
            self.textures[slot] = [tex]
        except Exception:
            self.textures[slot] = [self._solid_texture((80, 80, 80))]

    def _load_immersive_textures(self):
        """Capture multi-frame animation sequences for immersive room walls."""
        import importlib
        dt = 1.0 / IMMERSIVE_FPS
        for cell_id, (mod_name, cls_name, _, _) in IMMERSIVE_ROOMS.items():
            try:
                mod = importlib.import_module(f".{mod_name}", package="visuals")
                cls = getattr(mod, cls_name)
                vis = cls(self.display)
                frames = []
                for _ in range(IMMERSIVE_FRAMES):
                    vis.update(dt)
                    vis.draw()
                    tex = []
                    for y in range(GRID_SIZE):
                        for x in range(GRID_SIZE):
                            tex.append(self.display.get_pixel(x, y))
                    frames.append(tex)
                self.textures[cell_id] = frames
            except Exception:
                self.textures[cell_id] = [self._solid_texture((80, 80, 80))]

    @staticmethod
    def _solid_texture(color):
        return [color] * (GRID_SIZE * GRID_SIZE)

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def handle_input(self, input_state) -> bool:
        if input_state.any_direction:
            self.auto_walk = False
        self._input = input_state
        return input_state.any_direction

    def update(self, dt: float):
        self.time += dt
        if self.auto_walk:
            self._auto_walk(dt)
        else:
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
        margin = 0.25
        if not self._solid(nx, self.py, margin):
            self.px = nx
        if not self._solid(self.px, ny, margin):
            self.py = ny

    # ------------------------------------------------------------------
    # Auto-walk AI
    # ------------------------------------------------------------------

    def _auto_walk(self, dt):
        if self.wp_pause > 0:
            self.wp_pause -= dt
            return
        tx, ty = WAYPOINTS[self.wp_idx]
        dx = tx - self.px
        dy = ty - self.py
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < 0.3:
            self.wp_pause = 0.8  # pause at waypoint
            self.wp_idx = (self.wp_idx + 1) % len(WAYPOINTS)
            return
        # Desired angle
        target_a = math.atan2(dy, dx)
        # Lerp angle
        diff = target_a - self.pa
        while diff > math.pi:
            diff -= 2 * math.pi
        while diff < -math.pi:
            diff += 2 * math.pi
        self.pa += diff * min(1.0, 4.0 * dt)
        # Move
        speed = self.move_speed * dt
        cos_a = math.cos(self.pa)
        sin_a = math.sin(self.pa)
        nx = self.px + cos_a * speed
        ny = self.py + sin_a * speed
        margin = 0.25
        if not self._solid(nx, self.py, margin):
            self.px = nx
        if not self._solid(self.px, ny, margin):
            self.py = ny

    # ------------------------------------------------------------------
    # Collision
    # ------------------------------------------------------------------

    def _solid(self, x, y, margin):
        """Check if position collides with any wall."""
        for dx in (-margin, margin):
            for dy in (-margin, margin):
                mx = int(x + dx)
                my = int(y + dy)
                if mx < 0 or mx >= MAP_W or my < 0 or my >= MAP_H:
                    return True
                if MAP[my][mx] != 0:
                    return True
        return False

    def _get_room_cell(self):
        """Return the immersive cell ID if player is inside one, else 0."""
        mx, my = int(self.px), int(self.py)
        if mx < 0 or mx >= MAP_W or my < 0 or my >= MAP_H:
            return 0
        # Check surrounding walls to detect which room we're in
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                cx, cy = mx + dx, my + dy
                if 0 <= cx < MAP_W and 0 <= cy < MAP_H:
                    c = MAP[cy][cx]
                    if c >= 10:
                        return c
        return 0

    # ------------------------------------------------------------------
    # Raycaster + draw
    # ------------------------------------------------------------------

    def draw(self):
        self._render_frame()

    def _render_frame(self):
        # Check if player is in an immersive room for atmosphere tinting
        room_cell = self._get_room_cell()
        if room_cell in IMMERSIVE_ROOMS:
            _, _, ceil_color, floor_color = IMMERSIVE_ROOMS[room_cell]
        else:
            ceil_color = (30, 30, 50)
            floor_color = (50, 40, 35)
        half = GRID_SIZE // 2

        # Fill ceiling and floor
        for y in range(half):
            for x in range(GRID_SIZE):
                self.display.set_pixel(x, y, ceil_color)
        for y in range(half, GRID_SIZE):
            for x in range(GRID_SIZE):
                self.display.set_pixel(x, y, floor_color)

        # Cast rays
        for col in range(GRID_SIZE):
            ray_angle = self.pa + self.ray_offsets[col]
            self._cast_ray(col, ray_angle)

    def _cast_ray(self, col, angle):
        """DDA ray cast for one screen column."""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        # Avoid division by zero
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
        side = 0  # 0 = x-side, 1 = y-side
        for _ in range(50):
            if side_dist_x < side_dist_y:
                side_dist_x += delta_x
                map_x += step_x
                side = 0
            else:
                side_dist_y += delta_y
                map_y += step_y
                side = 1

            if map_x < 0 or map_x >= MAP_W or map_y < 0 or map_y >= MAP_H:
                break
            cell = MAP[map_y][map_x]
            if cell != 0:
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

        # Wall strip height
        line_height = int(GRID_SIZE / perp_dist)
        draw_start = max(0, GRID_SIZE // 2 - line_height // 2)
        draw_end = min(GRID_SIZE - 1, GRID_SIZE // 2 + line_height // 2)

        # Texture coordinate (where on the wall was hit)
        if side == 0:
            wall_x = self.py + perp_dist * sin_a
        else:
            wall_x = self.px + perp_dist * cos_a
        wall_x -= int(wall_x)  # fractional part [0, 1)

        # Distance fog factor
        fog = min(1.0, 2.0 / (perp_dist + 0.5))
        # Side shading
        if side == 1:
            fog *= 0.75

        is_textured = cell >= 2
        is_immersive = cell >= 10
        tex_col = int(wall_x * GRID_SIZE)
        if tex_col >= GRID_SIZE:
            tex_col = GRID_SIZE - 1

        # Select animation frame for this texture
        tex = None
        if is_textured and cell in self.textures:
            frames = self.textures[cell]
            fps = IMMERSIVE_FPS if is_immersive else self.SPRITE_FPS
            frame_idx = int(self.time * fps) % len(frames)
            tex = frames[frame_idx]

        for y in range(draw_start, draw_end + 1):
            # Texture y coordinate
            tex_y = int((y - (GRID_SIZE // 2 - line_height // 2)) * GRID_SIZE / line_height)
            if tex_y >= GRID_SIZE:
                tex_y = GRID_SIZE - 1
            if tex_y < 0:
                tex_y = 0

            if tex is not None:
                r, g, b = tex[tex_y * GRID_SIZE + tex_col]

                # Gold frame border only for gallery paintings (not immersive)
                if not is_immersive:
                    if tex_col <= 1 or tex_col >= GRID_SIZE - 2 or tex_y <= 1 or tex_y >= GRID_SIZE - 2:
                        r, g, b = GOLD if (tex_col + tex_y) % 2 == 0 else GOLD_DARK
            else:
                # Plain wall — stone gray
                r, g, b = 100, 100, 110

            # Apply fog
            r = int(r * fog)
            g = int(g * fog)
            b = int(b * fog)

            self.display.set_pixel(col, y, (r, g, b))
