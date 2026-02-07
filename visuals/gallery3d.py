"""
3D Gallery - Modular raycaster museum system
=============================================
Walk through Wolfenstein-style 3D galleries displaying paintings,
sprites, and immersive animated rooms on the walls.

Six themed galleries share a common raycaster base class.
Each subclass provides only data: MAP, PAINTINGS, IMMERSIVE, WAYPOINTS.

Controls:
  Up/Down    - Move forward/backward
  Left/Right - Rotate view
  (starts in auto-walk mode; any input takes manual control)
"""

import math
import os
import pickle
from . import Visual, Display, Colors, GRID_SIZE

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Gold frame color
GOLD = (180, 150, 50)
GOLD_DARK = (120, 100, 30)

# Immersive animation constants
IMMERSIVE_FPS = 8
IMMERSIVE_FRAMES = 24

# Animation speed for sprite/painting walls
SPRITE_FPS = 6


# ══════════════════════════════════════════════════════════════════
#  Base class — all raycaster logic lives here
# ══════════════════════════════════════════════════════════════════

class _Gallery3DBase(Visual):
    """Shared raycaster engine. Subclasses set class-level data."""

    # --- Subclass data (override these) ---
    MAP = []
    MAP_W = 16
    MAP_H = 16
    START_POS = (8.0, 8.0)
    WAYPOINTS = []

    # cell_id -> ("png", "path.png")
    #          | ("png_seq", ["frame1.png", "frame2.png", ...])
    #          | ("gif", "path.gif")
    #          | ("visual", "module", "ClassName")
    PAINTINGS = {}

    # cell_id -> ("module", "ClassName", (ceil_r,g,b), (floor_r,g,b))
    IMMERSIVE = {}

    def __init__(self, display: Display):
        self.textures = {}
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        sx, sy = self.START_POS
        self.px = sx
        self.py = sy
        self.pa = 0.0
        self.move_speed = 3.0
        self.rot_speed = 2.5
        self.fov = math.pi / 3
        self.ray_offsets = []
        for col in range(GRID_SIZE):
            offset = (col / GRID_SIZE - 0.5) * self.fov
            self.ray_offsets.append(offset)
        self.auto_walk = True
        self.wp_idx = 0
        self.wp_pause = 0.0
        self._load_textures()

    # ------------------------------------------------------------------
    # Generic texture loading — reads PAINTINGS + IMMERSIVE dicts
    # ------------------------------------------------------------------

    def _load_textures(self):
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        assets = os.path.join(project_dir, "assets")

        for cell_id, spec in self.PAINTINGS.items():
            kind = spec[0]
            if kind == "png":
                self._load_png(cell_id, os.path.join(assets, spec[1]))
            elif kind == "png_seq":
                paths = [os.path.join(assets, p) for p in spec[1]]
                self._load_png_sequence(cell_id, paths)
            elif kind == "gif":
                self._load_gif_frames(cell_id, os.path.join(assets, spec[1]))
            elif kind == "visual":
                self._capture_visual(cell_id, spec[1], spec[2])

        self._load_immersive_textures()

    def _load_png(self, slot, path):
        self.textures[slot] = [self._read_png(path)]

    def _load_png_sequence(self, slot, paths):
        self.textures[slot] = [self._read_png(p) for p in paths]

    def _read_png(self, path):
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
        if not HAS_PIL or not os.path.exists(path):
            self.textures[slot] = [self._solid_texture((80, 80, 80))]
            return
        try:
            bg = (20, 20, 30)
            gif = Image.open(path)
            n_frames = getattr(gif, 'n_frames', 1)
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
        if not self.IMMERSIVE:
            return
        import importlib
        visuals_dir = os.path.dirname(os.path.abspath(__file__))
        cache_dir = os.path.join(visuals_dir, ".gallery_cache")
        os.makedirs(cache_dir, exist_ok=True)

        for cell_id, (mod_name, cls_name, _, _) in self.IMMERSIVE.items():
            try:
                src_path = os.path.join(visuals_dir, f"{mod_name}.py")
                cache_path = os.path.join(cache_dir, f"{mod_name}.cache")
                if os.path.exists(cache_path) and os.path.exists(src_path):
                    if os.path.getmtime(cache_path) >= os.path.getmtime(src_path):
                        with open(cache_path, 'rb') as f:
                            self.textures[cell_id] = pickle.load(f)
                            continue
                mod = importlib.import_module(f".{mod_name}", package="visuals")
                cls = getattr(mod, cls_name)
                vis = cls(self.display)
                dt = 1.0 / IMMERSIVE_FPS
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
                try:
                    with open(cache_path, 'wb') as f:
                        pickle.dump(frames, f, protocol=pickle.HIGHEST_PROTOCOL)
                except Exception:
                    pass
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
        if not self.WAYPOINTS:
            return
        if self.wp_pause > 0:
            self.wp_pause -= dt
            return
        tx, ty = self.WAYPOINTS[self.wp_idx]
        dx = tx - self.px
        dy = ty - self.py
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < 0.3:
            self.wp_pause = 0.8
            self.wp_idx = (self.wp_idx + 1) % len(self.WAYPOINTS)
            return
        target_a = math.atan2(dy, dx)
        diff = target_a - self.pa
        while diff > math.pi:
            diff -= 2 * math.pi
        while diff < -math.pi:
            diff += 2 * math.pi
        self.pa += diff * min(1.0, 4.0 * dt)
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
        for dx in (-margin, margin):
            for dy in (-margin, margin):
                mx = int(x + dx)
                my = int(y + dy)
                if mx < 0 or mx >= self.MAP_W or my < 0 or my >= self.MAP_H:
                    return True
                if self.MAP[my][mx] != 0:
                    return True
        return False

    def _get_room_cell(self):
        mx, my = int(self.px), int(self.py)
        if mx < 0 or mx >= self.MAP_W or my < 0 or my >= self.MAP_H:
            return 0
        for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            cx, cy = mx + dx, my + dy
            for _ in range(8):
                if cx < 0 or cx >= self.MAP_W or cy < 0 or cy >= self.MAP_H:
                    break
                c = self.MAP[cy][cx]
                if c in self.IMMERSIVE:
                    return c
                if c != 0:
                    break
                cx += dx
                cy += dy
        return 0

    # ------------------------------------------------------------------
    # Raycaster + draw
    # ------------------------------------------------------------------

    def draw(self):
        self._render_frame()

    def _render_frame(self):
        room_cell = self._get_room_cell()
        if room_cell in self.IMMERSIVE:
            _, _, ceil_color, floor_color = self.IMMERSIVE[room_cell]
        else:
            ceil_color = (30, 30, 50)
            floor_color = (50, 40, 35)
        half = GRID_SIZE // 2

        for y in range(half):
            for x in range(GRID_SIZE):
                self.display.set_pixel(x, y, ceil_color)
        for y in range(half, GRID_SIZE):
            for x in range(GRID_SIZE):
                self.display.set_pixel(x, y, floor_color)

        for col in range(GRID_SIZE):
            ray_angle = self.pa + self.ray_offsets[col]
            self._cast_ray(col, ray_angle)

    def _cast_ray(self, col, angle):
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        if abs(cos_a) < 1e-8:
            cos_a = 1e-8
        if abs(sin_a) < 1e-8:
            sin_a = 1e-8

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

        hit = False
        side = 0
        for _ in range(64):
            if side_dist_x < side_dist_y:
                side_dist_x += delta_x
                map_x += step_x
                side = 0
            else:
                side_dist_y += delta_y
                map_y += step_y
                side = 1

            if map_x < 0 or map_x >= self.MAP_W or map_y < 0 or map_y >= self.MAP_H:
                break
            cell = self.MAP[map_y][map_x]
            if cell != 0:
                hit = True
                break

        if not hit:
            return

        if side == 0:
            perp_dist = (map_x - self.px + (1 - step_x) / 2) / cos_a
        else:
            perp_dist = (map_y - self.py + (1 - step_y) / 2) / sin_a
        if perp_dist < 0.01:
            perp_dist = 0.01

        line_height = int(GRID_SIZE / perp_dist)
        draw_start = max(0, GRID_SIZE // 2 - line_height // 2)
        draw_end = min(GRID_SIZE - 1, GRID_SIZE // 2 + line_height // 2)

        if side == 0:
            wall_x = self.py + perp_dist * sin_a
        else:
            wall_x = self.px + perp_dist * cos_a
        wall_x -= int(wall_x)

        fog = min(1.0, 2.0 / (perp_dist + 0.5))
        if side == 1:
            fog *= 0.75

        is_textured = cell >= 2
        is_immersive = cell in self.IMMERSIVE
        tex_col = int(wall_x * GRID_SIZE)
        if tex_col >= GRID_SIZE:
            tex_col = GRID_SIZE - 1

        tex = None
        if is_textured and cell in self.textures:
            frames = self.textures[cell]
            fps = IMMERSIVE_FPS if is_immersive else SPRITE_FPS
            frame_idx = int(self.time * fps) % len(frames)
            tex = frames[frame_idx]

        for y in range(draw_start, draw_end + 1):
            tex_y = int((y - (GRID_SIZE // 2 - line_height // 2)) * GRID_SIZE / line_height)
            if tex_y >= GRID_SIZE:
                tex_y = GRID_SIZE - 1
            if tex_y < 0:
                tex_y = 0

            if tex is not None:
                r, g, b = tex[tex_y * GRID_SIZE + tex_col]
                if not is_immersive:
                    if tex_col <= 1 or tex_col >= GRID_SIZE - 2 or tex_y <= 1 or tex_y >= GRID_SIZE - 2:
                        r, g, b = GOLD if (tex_col + tex_y) % 2 == 0 else GOLD_DARK
            else:
                r, g, b = 100, 100, 110

            r = int(r * fog)
            g = int(g * fog)
            b = int(b * fog)
            self.display.set_pixel(col, y, (r, g, b))


# ══════════════════════════════════════════════════════════════════
#  Gallery 1: ART GALLERY — 16x16 hall with 4 alcoves, 5 paintings
# ══════════════════════════════════════════════════════════════════

class GalleryArt(_Gallery3DBase):
    name = "ART GALLERY"
    description = "Classic paintings museum"
    category = "gallery"

    MAP_W = 16
    MAP_H = 16
    START_POS = (2.5, 6.0)

    MAP = [
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
        [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],       # 15
    ]

    PAINTINGS = {
        2: ("png", "greatwave.png"),
        3: ("png", "scream.png"),
        4: ("visual", "starrynight", "StarryNight"),
        5: ("visual", "waterlilies", "WaterLilies"),
        6: ("visual", "mondrian", "Mondrian"),
        7: ("visual", "greatwave", "GreatWave"),
        8: ("visual", "scream", "Scream"),
        9: ("visual", "starrynight", "StarryNight"),
    }

    WAYPOINTS = [
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
    ]


# ══════════════════════════════════════════════════════════════════
#  Gallery 2: SPRITE MUSEUM — 16x16 hall with 4 alcoves, 8 sprites
# ══════════════════════════════════════════════════════════════════

class GallerySprites(_Gallery3DBase):
    name = "SPRITE MUSEUM"
    description = "Classic game characters"
    category = "gallery"

    MAP_W = 16
    MAP_H = 16
    START_POS = (2.5, 6.0)

    # Same hall layout as Art Gallery but all 8 alcove walls are sprites
    MAP = [
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
        [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],       # 15
    ]

    PAINTINGS = {
        2: ("png_seq", ["mario_walk1.png", "mario_walk2.png", "mario_walk3.png"]),
        3: ("png_seq", ["sonic_run1.png", "sonic_run2.png", "sonic_run3.png", "sonic_run4.png"]),
        4: ("gif", "ani_link_spin.gif"),
        5: ("gif", "SamusRunningR.gif"),
        6: ("gif", "yoshi_tongue.gif"),
        7: ("gif", "kirby_eats.gif"),
        8: ("gif", "megamanxpack2.gif"),
        9: ("gif", "Metroidgif.gif"),
    }

    WAYPOINTS = [
        (2.5, 2.5),   # NW room - Mario
        (2.5, 6.0),   # exit NW room south
        (5.5, 6.0),   # central hall west
        (5.5, 2.5),   # look at Mario (east wall NW)
        (5.5, 6.0),   # back
        (8.0, 2.5),   # central north
        (10.5, 2.5),  # look at Sonic (west wall NE)
        (13.5, 2.5),  # NE room - Sonic
        (13.5, 6.0),  # exit NE room south
        (10.5, 6.0),  # central hall east
        (10.5, 9.5),  # central hall south
        (13.5, 9.5),  # SE approach
        (13.5, 13.5), # SE room - Metroid
        (10.5, 13.5), # look at Metroid (west wall SE)
        (10.5, 9.5),  # back
        (5.5, 9.5),   # central hall west
        (5.5, 13.5),  # look at MegaMan (east wall SW)
        (2.5, 13.5),  # SW room - MegaMan
        (2.5, 9.5),   # exit SW room north
        (8.0, 9.5),   # center south
    ]


# ══════════════════════════════════════════════════════════════════
#  Gallery 3: AUTOMATA WING — 16x20 corridor + 6 rooms
# ══════════════════════════════════════════════════════════════════

class GalleryAutomata(_Gallery3DBase):
    name = "AUTOMATA WING"
    description = "Living pattern rooms"
    category = "gallery"

    MAP_W = 16
    MAP_H = 20
    START_POS = (7.5, 1.5)

    MAP = [
        [1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1],       # 0 entry doorway
        [1,0,0,0,0,0,1,0,0,1,0,0,0,0,0,1],       # 1 corridor
        [1,0,0,0,0,0,1,0,0,1,0,0,0,0,0,1],       # 2 corridor
        [1,10,10,10,10,1,1,0,0,1,1,11,11,11,11,1],# 3 Life (L) / Hodge (R)
        [1,10,0,0,10,10,1,0,0,1,11,11,0,0,11,1], # 4
        [1,10,0,0,0,0,0,0,0,0,0,0,0,0,11,1],     # 5 doorways
        [1,10,0,0,10,10,1,0,0,1,11,11,0,0,11,1], # 6
        [1,10,10,10,10,1,1,0,0,1,1,11,11,11,11,1],# 7
        [1,0,0,0,0,0,1,0,0,1,0,0,0,0,0,1],       # 8 corridor
        [1,12,12,12,12,1,1,0,0,1,1,13,13,13,13,1],# 9 DemonSpirals (L) / Coral (R)
        [1,12,0,0,12,12,1,0,0,1,13,13,0,0,13,1], # 10
        [1,12,0,0,0,0,0,0,0,0,0,0,0,0,13,1],     # 11 doorways
        [1,12,0,0,12,12,1,0,0,1,13,13,0,0,13,1], # 12
        [1,12,12,12,12,1,1,0,0,1,1,13,13,13,13,1],# 13
        [1,0,0,0,0,0,1,0,0,1,0,0,0,0,0,1],       # 14 corridor
        [1,14,14,14,14,1,1,0,0,1,1,15,15,15,15,1],# 15 Aurora (L) / Ripples (R)
        [1,14,0,0,14,14,1,0,0,1,15,15,0,0,15,1], # 16
        [1,14,0,0,0,0,0,0,0,0,0,0,0,0,15,1],     # 17 doorways
        [1,14,0,0,14,14,1,0,0,1,15,15,0,0,15,1], # 18
        [1,14,14,14,14,1,1,1,1,1,1,15,15,15,15,1],# 19 dead end
    ]

    IMMERSIVE = {
        10: ("life",         "Life",         (10, 15, 10), (15, 20, 15)),
        11: ("hodge",        "Hodge",        (30, 15, 40), (40, 20, 50)),
        12: ("demonspirals", "DemonSpirals", (40, 10, 40), (50, 15, 50)),
        13: ("turing",       "TuringCoral",  (15, 25, 30), (20, 35, 40)),
        14: ("aurora",       "Aurora",       (20, 10, 30), (25, 15, 40)),
        15: ("ripples",      "Ripples",      (10, 10, 30), (15, 15, 40)),
    }

    WAYPOINTS = [
        (7.5, 2.5),   # corridor entrance
        # Life (left)
        (5.0, 5.5),   # enter Life room
        (3.0, 5.5),   # center
        (5.0, 5.5),   # exit
        # Hodge (right)
        (11.0, 5.5),  # enter Hodge room
        (13.0, 5.5),  # center
        (11.0, 5.5),  # exit
        (7.5, 5.5),   # corridor
        (7.5, 8.5),   # corridor south
        # DemonSpirals (left)
        (5.0, 11.5),  # enter DemonSpirals room
        (3.0, 11.5),  # center
        (5.0, 11.5),  # exit
        # Coral (right)
        (11.0, 11.5), # enter Coral room
        (13.0, 11.5), # center
        (11.0, 11.5), # exit
        (7.5, 11.5),  # corridor
        (7.5, 14.5),  # corridor south
        # Aurora (left)
        (5.0, 17.5),  # enter Aurora room
        (3.0, 17.5),  # center
        (5.0, 17.5),  # exit
        # Ripples (right)
        (11.0, 17.5), # enter Ripples room
        (13.0, 17.5), # center
        (11.0, 17.5), # exit
        # Return north
        (7.5, 17.5),  # corridor
        (7.5, 14.5),  # corridor
        (7.5, 8.5),   # corridor
        (7.5, 2.5),   # corridor north
    ]


# ══════════════════════════════════════════════════════════════════
#  Gallery 4: SCIENCE WING — 16x20 corridor + 6 rooms
# ══════════════════════════════════════════════════════════════════

class GalleryScience(_Gallery3DBase):
    name = "SCIENCE WING"
    description = "Science visualization rooms"
    category = "gallery"

    MAP_W = 16
    MAP_H = 20
    START_POS = (7.5, 1.5)

    MAP = [
        [1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1],       # 0 entry doorway
        [1,0,0,0,0,0,1,0,0,1,0,0,0,0,0,1],       # 1 corridor
        [1,0,0,0,0,0,1,0,0,1,0,0,0,0,0,1],       # 2 corridor
        [1,10,10,10,10,1,1,0,0,1,1,11,11,11,11,1],# 3 TuringSpots (L) / TuringStripes (R)
        [1,10,0,0,10,10,1,0,0,1,11,11,0,0,11,1], # 4
        [1,10,0,0,0,0,0,0,0,0,0,0,0,0,11,1],     # 5 doorways
        [1,10,0,0,10,10,1,0,0,1,11,11,0,0,11,1], # 6
        [1,10,10,10,10,1,1,0,0,1,1,11,11,11,11,1],# 7
        [1,0,0,0,0,0,1,0,0,1,0,0,0,0,0,1],       # 8 corridor
        [1,12,12,12,12,1,1,0,0,1,1,13,13,13,13,1],# 9 FluidInk (L) / Neurons (R)
        [1,12,0,0,12,12,1,0,0,1,13,13,0,0,13,1], # 10
        [1,12,0,0,0,0,0,0,0,0,0,0,0,0,13,1],     # 11 doorways
        [1,12,0,0,12,12,1,0,0,1,13,13,0,0,13,1], # 12
        [1,12,12,12,12,1,1,0,0,1,1,13,13,13,13,1],# 13
        [1,0,0,0,0,0,1,0,0,1,0,0,0,0,0,1],       # 14 corridor
        [1,14,14,14,14,1,1,0,0,1,1,15,15,15,15,1],# 15 Chladni (L) / Lattice (R)
        [1,14,0,0,14,14,1,0,0,1,15,15,0,0,15,1], # 16
        [1,14,0,0,0,0,0,0,0,0,0,0,0,0,15,1],     # 17 doorways
        [1,14,0,0,14,14,1,0,0,1,15,15,0,0,15,1], # 18
        [1,14,14,14,14,1,1,1,1,1,1,15,15,15,15,1],# 19 dead end
    ]

    IMMERSIVE = {
        10: ("turing",   "TuringSpots",   (5, 10, 40),  (10, 15, 50)),
        11: ("turing",   "TuringStripes", (10, 5, 0),   (20, 10, 5)),
        12: ("fluid",    "FluidInk",      (10, 10, 15),  (15, 15, 25)),
        13: ("neurons",  "Neurons",       (5, 10, 20),  (10, 15, 30)),
        14: ("chladni",  "Chladni",       (15, 15, 20), (25, 25, 35)),
        15: ("lattice",  "Lattice",       (10, 20, 10), (15, 30, 15)),
    }

    WAYPOINTS = [
        (7.5, 2.5),   # corridor entrance
        # TuringSpots (left)
        (5.0, 5.5),   # enter room
        (3.0, 5.5),   # center
        (5.0, 5.5),   # exit
        # TuringStripes (right)
        (11.0, 5.5),  # enter room
        (13.0, 5.5),  # center
        (11.0, 5.5),  # exit
        (7.5, 5.5),   # corridor
        (7.5, 8.5),   # corridor south
        # FluidInk (left)
        (5.0, 11.5),  # enter room
        (3.0, 11.5),  # center
        (5.0, 11.5),  # exit
        # Neurons (right)
        (11.0, 11.5), # enter room
        (13.0, 11.5), # center
        (11.0, 11.5), # exit
        (7.5, 11.5),  # corridor
        (7.5, 14.5),  # corridor south
        # Chladni (left)
        (5.0, 17.5),  # enter room
        (3.0, 17.5),  # center
        (5.0, 17.5),  # exit
        # Lattice (right)
        (11.0, 17.5), # enter room
        (13.0, 17.5), # center
        (11.0, 17.5), # exit
        # Return north
        (7.5, 17.5),
        (7.5, 14.5),
        (7.5, 8.5),
        (7.5, 2.5),
    ]


# ══════════════════════════════════════════════════════════════════
#  Gallery 5: DIGITAL WING — 16x20 corridor + 6 rooms
# ══════════════════════════════════════════════════════════════════

class GalleryDigital(_Gallery3DBase):
    name = "DIGITAL WING"
    description = "Digital art installations"
    category = "gallery"

    MAP_W = 16
    MAP_H = 20
    START_POS = (7.5, 1.5)

    MAP = [
        [1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1],       # 0 entry doorway
        [1,0,0,0,0,0,1,0,0,1,0,0,0,0,0,1],       # 1 corridor
        [1,0,0,0,0,0,1,0,0,1,0,0,0,0,0,1],       # 2 corridor
        [1,10,10,10,10,1,1,0,0,1,1,11,11,11,11,1],# 3 XOR (L) / Truchet (R)
        [1,10,0,0,10,10,1,0,0,1,11,11,0,0,11,1], # 4
        [1,10,0,0,0,0,0,0,0,0,0,0,0,0,11,1],     # 5 doorways
        [1,10,0,0,10,10,1,0,0,1,11,11,0,0,11,1], # 6
        [1,10,10,10,10,1,1,0,0,1,1,11,11,11,11,1],# 7
        [1,0,0,0,0,0,1,0,0,1,0,0,0,0,0,1],       # 8 corridor
        [1,12,12,12,12,1,1,0,0,1,1,13,13,13,13,1],# 9 Moire (L) / Rotozoom (R)
        [1,12,0,0,12,12,1,0,0,1,13,13,0,0,13,1], # 10
        [1,12,0,0,0,0,0,0,0,0,0,0,0,0,13,1],     # 11 doorways
        [1,12,0,0,12,12,1,0,0,1,13,13,0,0,13,1], # 12
        [1,12,12,12,12,1,1,0,0,1,1,13,13,13,13,1],# 13
        [1,0,0,0,0,0,1,0,0,1,0,0,0,0,0,1],       # 14 corridor
        [1,14,14,14,14,1,1,0,0,1,1,15,15,15,15,1],# 15 Plasma (L) / Fire (R)
        [1,14,0,0,14,14,1,0,0,1,15,15,0,0,15,1], # 16
        [1,14,0,0,0,0,0,0,0,0,0,0,0,0,15,1],     # 17 doorways
        [1,14,0,0,14,14,1,0,0,1,15,15,0,0,15,1], # 18
        [1,14,14,14,14,1,1,1,1,1,1,15,15,15,15,1],# 19 dead end
    ]

    IMMERSIVE = {
        10: ("xorpattern", "XORPattern",  (15, 15, 20), (25, 25, 35)),
        11: ("truchet",    "Truchet",     (10, 15, 10), (15, 20, 15)),
        12: ("moire",      "Moire",       (10, 10, 20), (15, 15, 30)),
        13: ("rotozoom",   "Rotozoom",    (20, 10, 15), (30, 15, 20)),
        14: ("plasma",     "Plasma",      (20, 10, 30), (30, 15, 40)),
        15: ("fire",       "Fire",        (30, 15, 5),  (40, 20, 8)),
    }

    WAYPOINTS = [
        (7.5, 2.5),   # corridor entrance
        # XOR (left)
        (5.0, 5.5),   # enter room
        (3.0, 5.5),   # center
        (5.0, 5.5),   # exit
        # Truchet (right)
        (11.0, 5.5),  # enter room
        (13.0, 5.5),  # center
        (11.0, 5.5),  # exit
        (7.5, 5.5),   # corridor
        (7.5, 8.5),   # corridor south
        # Moire (left)
        (5.0, 11.5),  # enter room
        (3.0, 11.5),  # center
        (5.0, 11.5),  # exit
        # Rotozoom (right)
        (11.0, 11.5), # enter room
        (13.0, 11.5), # center
        (11.0, 11.5), # exit
        (7.5, 11.5),  # corridor
        (7.5, 14.5),  # corridor south
        # Plasma (left)
        (5.0, 17.5),  # enter room
        (3.0, 17.5),  # center
        (5.0, 17.5),  # exit
        # Fire (right)
        (11.0, 17.5), # enter room
        (13.0, 17.5), # center
        (11.0, 17.5), # exit
        # Return north
        (7.5, 17.5),
        (7.5, 14.5),
        (7.5, 8.5),
        (7.5, 2.5),
    ]


# ══════════════════════════════════════════════════════════════════
#  Gallery 6: EFFECTS LAB — vestibule + 2 large rooms
# ══════════════════════════════════════════════════════════════════

class GalleryEffects(_Gallery3DBase):
    name = "EFFECTS LAB"
    description = "Starfield and Matrix rooms"
    category = "gallery"

    MAP_W = 16
    MAP_H = 23
    START_POS = (7.5, 1.5)

    MAP = [
        [1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1],       # 0  entry doorway
        [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],       # 1  vestibule
        [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],       # 2  vestibule
        # Starfield Pillar Hall — pillars in diamond pattern
        [1,16,16,16,16,16,16,0,0,16,16,16,16,16,16,1],# 3  top wall, doorway 7-8
        [1,16,0,0,0,0,0,0,0,0,0,0,0,0,16,1],     # 4
        [1,16,0,16,0,0,0,0,0,0,0,0,16,0,16,1],   # 5  pillars at 3,12
        [1,16,0,0,0,0,0,0,0,0,0,0,0,0,16,1],     # 6
        [1,16,0,0,0,0,16,0,0,16,0,0,0,0,16,1],   # 7  pillars at 6,9
        [1,16,0,0,0,0,0,0,0,0,0,0,0,0,16,1],     # 8
        [1,16,0,16,0,0,0,0,0,0,0,0,16,0,16,1],   # 9  pillars at 3,12
        [1,16,0,0,0,0,0,0,0,0,0,0,0,0,16,1],     # 10
        [1,16,16,16,16,16,16,0,0,16,16,16,16,16,16,1],# 11 bottom wall, doorway
        [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],       # 12 corridor
        # Matrix Maze — L-walls and cross-walls
        [1,17,17,17,17,17,17,0,0,17,17,17,17,17,17,1],# 13 top wall, doorway
        [1,17,0,0,0,0,0,0,0,0,0,0,0,0,17,1],     # 14
        [1,17,0,17,17,0,0,0,0,0,0,17,17,0,17,1], # 15 L-walls
        [1,17,0,17,0,0,0,0,0,0,0,0,17,0,17,1],   # 16 L-corners
        [1,17,0,0,0,0,17,0,0,17,0,0,0,0,17,1],   # 17 cross-walls
        [1,17,0,0,0,0,0,0,0,0,0,0,0,0,17,1],     # 18 open center
        [1,17,0,0,0,0,17,0,0,17,0,0,0,0,17,1],   # 19 cross-walls
        [1,17,0,17,0,0,0,0,0,0,0,0,17,0,17,1],   # 20 L-corners
        [1,17,0,17,17,0,0,0,0,0,0,17,17,0,17,1], # 21 L-walls
        [1,17,17,17,17,17,17,17,17,17,17,17,17,17,17,1],# 22 dead-end wall
    ]

    IMMERSIVE = {
        16: ("starfield", "Starfield", (3, 3, 15),  (8, 8, 25)),
        17: ("matrix",    "Matrix",    (3, 20, 5),  (8, 30, 10)),
    }

    WAYPOINTS = [
        (7.5, 2.5),   # vestibule
        # Starfield Pillar Hall — weave through pillars
        (7.5, 4.5),   # enter starfield room
        (2.5, 4.5),   # left wall
        (2.5, 8.5),   # down left side
        (5.0, 8.5),   # between pillars
        (7.5, 6.5),   # center upper
        (12.0, 6.5),  # right upper
        (12.0, 8.5),  # right lower
        (7.5, 10.5),  # bottom center
        (7.5, 12.5),  # exit to corridor
        # Matrix Maze — navigate L-walls and alcoves
        (7.5, 14.5),  # enter matrix room
        (2.5, 14.5),  # left side
        (2.5, 18.5),  # down left channel
        (5.0, 18.5),  # toward left alcove
        (5.0, 16.5),  # in left alcove
        (7.5, 16.5),  # center
        (11.0, 16.5), # right alcove
        (11.0, 18.5), # down from right alcove
        (13.0, 18.5), # right channel
        (13.0, 14.5), # up right side
        (7.5, 14.5),  # back to center
        # Return north
        (7.5, 12.5),  # corridor
        (7.5, 2.5),   # vestibule
    ]


# ══════════════════════════════════════════════════════════════════
#  Gallery 7: SALON — dense painting room, every wall is art
# ══════════════════════════════════════════════════════════════════

class GallerySalon(_Gallery3DBase):
    name = "SALON"
    description = "Wall-to-wall paintings"
    category = "gallery"

    MAP_W = 16
    MAP_H = 10
    START_POS = (7.5, 5.0)

    # One big room — paintings on every wall surface
    MAP = [
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],       # 0
        [1, 2, 3, 4, 5, 6, 7, 8, 9,10,11,12,13,14,15, 1],       # 1  north wall
        [16,0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,17],       # 2  side paintings
        [18,0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,19],       # 3  side paintings
        [20,0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,21],       # 4  side paintings
        [22,0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,23],       # 5  side paintings
        [24,0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,25],       # 6  side paintings
        [26,0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,27],       # 7  side paintings
        [1,28,29,30,31,32,33,34,35,36,37,38,39,40,41, 1],       # 8  south wall
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],       # 9
    ]

    PAINTINGS = {
        # North wall — the masters + vivid generative art
        2:  ("png", "greatwave.png"),
        3:  ("visual", "starrynight", "StarryNight"),
        4:  ("png", "scream.png"),
        5:  ("visual", "waterlilies", "WaterLilies"),
        6:  ("visual", "mondrian", "Mondrian"),
        7:  ("visual", "plasma", "Plasma"),
        8:  ("visual", "fire", "Fire"),
        9:  ("visual", "aurora", "Aurora"),
        10: ("visual", "life", "Life"),
        11: ("visual", "hodge", "Hodge"),
        12: ("visual", "demonspirals", "DemonSpirals"),
        13: ("visual", "ripples", "Ripples"),
        14: ("visual", "xorpattern", "XORPattern"),
        15: ("visual", "truchet", "Truchet"),
        # West wall
        16: ("visual", "moire", "Moire"),
        18: ("visual", "boids", "Boids"),
        20: ("visual", "lava", "Lava"),
        22: ("visual", "earth", "Earth"),
        24: ("visual", "gyre", "Gyre"),
        26: ("visual", "slime", "Slime"),
        # East wall
        17: ("visual", "rotozoom", "Rotozoom"),
        19: ("visual", "starfield", "Starfield"),
        21: ("visual", "matrix", "Matrix"),
        23: ("visual", "lattice", "Lattice"),
        25: ("visual", "flux", "Flux"),
        27: ("visual", "attractors", "Attractors"),
        # South wall — science + abstract
        28: ("visual", "chladni", "Chladni"),
        29: ("visual", "neurons", "Neurons"),
        30: ("visual", "fluid", "FluidInk"),
        31: ("visual", "wolfram", "Wolfram"),
        32: ("visual", "sandpile", "Sandpile"),
        33: ("visual", "faders", "Faders"),
        34: ("visual", "trance", "Trance"),
        35: ("visual", "copperbars", "CopperBars"),
        36: ("visual", "rainbow", "Rainbow"),
        37: ("visual", "quarks", "Quarks"),
        38: ("visual", "mobius", "Mobius"),
        39: ("visual", "lake", "Lake"),
        40: ("visual", "greatwave", "GreatWave"),
        41: ("visual", "scream", "Scream"),
    }

    WAYPOINTS = [
        # Open facing north wall
        (7.5, 2.5),    # approach north paintings
        # Walk along north wall
        (2.0, 2.5),    # far left
        (5.0, 2.5),    # left-center
        (10.0, 2.5),   # right-center
        (13.0, 2.5),   # far right
        # East wall
        (13.5, 4.0),   # upper east
        (13.5, 6.0),   # lower east
        # South wall
        (13.0, 7.5),   # far right south
        (10.0, 7.5),   # right-center
        (5.0, 7.5),    # left-center
        (2.0, 7.5),    # far left south
        # West wall
        (1.5, 6.0),    # lower west
        (1.5, 4.0),    # upper west
        # Back to center
        (7.5, 5.0),    # center
    ]


# ══════════════════════════════════════════════════════════════════
#  Gallery 8: SMB3 MUSEUM — NES sprite sheets auto-extracted
#  Dynamically generates a serpentine corridor map sized to fit
#  ALL extracted sprites, kept in sheet order for animation grouping.
# ══════════════════════════════════════════════════════════════════

class GallerySMB3(_Gallery3DBase):
    name = "SMB3 MUSEUM"
    description = "Super Mario Bros. 3 sprites"
    category = "gallery"

    # Defaults — overridden dynamically in reset()
    MAP_W = 16
    MAP_H = 4
    START_POS = (7.5, 2.5)
    MAP = [[1]*16, [1]*16, [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1], [1]*16]
    WAYPOINTS = [(7.5, 2.5)]

    _SHEET = "smb3_heroes.png"

    def reset(self):
        self.time = 0.0
        self.move_speed = 3.0
        self.rot_speed = 2.5
        self.fov = math.pi / 3
        self.ray_offsets = []
        for col in range(GRID_SIZE):
            self.ray_offsets.append((col / GRID_SIZE - 0.5) * self.fov)
        self.auto_walk = True
        self.wp_idx = 0
        self.wp_pause = 0.0
        self.textures = {}
        self._load_textures()
        sx, sy = self.START_POS
        self.px, self.py, self.pa = sx, sy, 0.0

    def _load_textures(self):
        """Extract ALL sprites from sheet, build map to fit."""
        if not HAS_PIL:
            return
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        assets = os.path.join(project_dir, "assets")
        cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 ".gallery_cache")
        os.makedirs(cache_dir, exist_ok=True)
        sheet_path = os.path.join(assets, self._SHEET)
        if not os.path.exists(sheet_path):
            return

        # Try cache
        cache_path = os.path.join(cache_dir, f"{self._SHEET}.all.cache")
        textures_list = None
        if os.path.exists(cache_path):
            if os.path.getmtime(cache_path) >= os.path.getmtime(sheet_path):
                try:
                    with open(cache_path, 'rb') as f:
                        textures_list = pickle.load(f)
                except Exception:
                    pass

        if textures_list is None:
            textures_list = self._extract_all(sheet_path)
            try:
                with open(cache_path, 'wb') as f:
                    pickle.dump(textures_list, f, protocol=pickle.HIGHEST_PROTOCOL)
            except Exception:
                pass

        n = len(textures_list)
        if n == 0:
            return

        # Build serpentine map and assign textures
        self._build_serpentine(n)
        for i, tex in enumerate(textures_list):
            self.textures[i + 2] = [tex]  # cell IDs start at 2

    def _extract_all(self, path):
        """BFS-extract ALL sprites from sheet, in sheet order (y then x)."""
        from PIL import Image
        import numpy as np
        from collections import deque

        img = Image.open(path).convert("RGBA")
        w, h = img.size
        pixels = np.array(img)
        bg = pixels[0, 0, :3].astype(int)
        bg_rgb = tuple(bg)

        diff = np.abs(pixels[:, :, :3].astype(int) - bg[None, None, :])
        alpha = pixels[:, :, 3]
        mask = (diff.max(axis=2) > 30) & (alpha > 128)

        visited = np.zeros((h, w), dtype=bool)
        components = []

        for sy in range(h):
            for sx in range(w):
                if mask[sy, sx] and not visited[sy, sx]:
                    queue = deque([(sy, sx)])
                    visited[sy, sx] = True
                    min_x, max_x = sx, sx
                    min_y, max_y = sy, sy
                    area = 0
                    while queue:
                        cy, cx = queue.popleft()
                        area += 1
                        min_x = min(min_x, cx)
                        max_x = max(max_x, cx)
                        min_y = min(min_y, cy)
                        max_y = max(max_y, cy)
                        for dy, dx in [(-1,0),(1,0),(0,-1),(0,1)]:
                            ny, nx = cy+dy, cx+dx
                            if 0 <= ny < h and 0 <= nx < w and not visited[ny, nx] and mask[ny, nx]:
                                visited[ny, nx] = True
                                queue.append((ny, nx))
                    cw = max_x - min_x + 1
                    ch = max_y - min_y + 1
                    if (min(cw, ch) >= 14 and max(cw, ch) <= 120
                            and 0.2 <= cw/ch <= 5.0 and area / (cw*ch) > 0.08):
                        components.append((min_x, min_y, cw, ch, area))

        # Sheet order: sort by y then x — preserves animation grouping
        components.sort(key=lambda c: (c[1], c[0]))

        # Convert all to 64x64 textures
        dark_bg = (20, 20, 30)
        textures = []
        for (cx, cy, cw, ch, _) in components:
            crop = img.crop((cx, cy, cx+cw, cy+ch))
            sz = max(cw, ch)
            square = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
            square.paste(crop, ((sz-cw)//2, (sz-ch)//2))
            sized = square.resize((GRID_SIZE, GRID_SIZE), Image.Resampling.NEAREST)
            tex = []
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    r, g, b, a = sized.getpixel((x, y))
                    if a > 128 and not (abs(r-bg_rgb[0]) < 30
                                        and abs(g-bg_rgb[1]) < 30
                                        and abs(b-bg_rgb[2]) < 30):
                        tex.append((r, g, b))
                    else:
                        tex.append(dark_bg)
            textures.append(tex)
        return textures

    def _build_serpentine(self, n_sprites):
        """Generate a serpentine corridor map sized to fit n_sprites paintings.

        Layout: painting rows alternate with corridor rows. Painting walls
        have a 1-cell opening at alternating ends to create a serpentine path.
        """
        W = 16
        cell_id = 2
        rows = []
        waypoints = []
        placed = 0
        side_idx = 0  # cycles through sprite IDs for side walls

        def _side():
            """Return a cycling cell ID for side-wall sprites."""
            nonlocal side_idx
            sid = 2 + (side_idx % n_sprites)
            side_idx += 1
            return sid

        rows.append([1] * W)  # top wall

        # First painting row (full width, 14 paintings + side sprites)
        row = [1] * W
        row[0] = _side()
        for c in range(1, 15):
            if placed < n_sprites:
                row[c] = cell_id; cell_id += 1; placed += 1
        row[15] = _side()
        rows.append(row)

        corridor_num = 0
        while placed < n_sprites:
            # Corridor row — sprites on side walls
            row = [_side()] + [0] * 14 + [_side()]
            rows.append(row)
            cy = len(rows) - 1
            if corridor_num % 2 == 0:
                waypoints.append((2.0, cy + 0.5))
                waypoints.append((13.5, cy + 0.5))
            else:
                waypoints.append((13.5, cy + 0.5))
                waypoints.append((2.0, cy + 0.5))
            corridor_num += 1

            # Painting row with doorway for serpentine turn
            row = [1] * W
            row[0] = _side()
            row[15] = _side()
            if corridor_num % 2 == 1:
                # Opening on right (col 14)
                for c in range(1, 14):
                    if placed < n_sprites:
                        row[c] = cell_id; cell_id += 1; placed += 1
                row[14] = 0
                waypoints.append((14.5, cy + 0.5))
                waypoints.append((14.5, cy + 2.5))
            else:
                # Opening on left (col 1)
                row[1] = 0
                for c in range(2, 15):
                    if placed < n_sprites:
                        row[c] = cell_id; cell_id += 1; placed += 1
                waypoints.append((1.5, cy + 0.5))
                waypoints.append((1.5, cy + 2.5))
            rows.append(row)

        # Final corridor to view last painting row
        row = [_side()] + [0] * 14 + [_side()]
        rows.append(row)
        cy = len(rows) - 1
        if corridor_num % 2 == 0:
            waypoints.append((2.0, cy + 0.5))
            waypoints.append((13.5, cy + 0.5))
        else:
            waypoints.append((13.5, cy + 0.5))
            waypoints.append((2.0, cy + 0.5))

        rows.append([1] * W)  # bottom wall

        self.MAP = rows
        self.MAP_W = W
        self.MAP_H = len(rows)
        self.WAYPOINTS = waypoints
        self.START_POS = (7.5, 2.5)


# Legacy alias — keep old import working
Gallery3D = GalleryArt
