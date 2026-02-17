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

# Pre-loaded texture data for emulator mode (injected before this module loads)
_PRELOADED_GALLERY = globals().get('_GALLERY_PIXELS', {})
# Painting atlas (shared with painting.py, for Salon)
_PRELOADED_PAINTINGS = globals().get('_PAINTING_PIXELS', {})

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
        # Emulator mode: use pre-loaded gallery atlas
        cls_name = type(self).__name__
        preloaded = _PRELOADED_GALLERY.get(cls_name)
        if preloaded:
            self._decode_preloaded(preloaded)
            return

        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        assets = os.path.join(project_dir, "assets")

        for cell_id, spec in self.PAINTINGS.items():
            kind = spec[0]
            if kind == "png":
                # Check paintings atlas for Salon/Art gallery paintings
                self._load_png_or_atlas(cell_id, os.path.join(assets, spec[1]))
            elif kind == "png_seq":
                paths = [os.path.join(assets, p) for p in spec[1]]
                self._load_png_sequence(cell_id, paths)
            elif kind == "gif":
                self._load_gif_frames(cell_id, os.path.join(assets, spec[1]))
            elif kind == "visual":
                self._capture_visual(cell_id, spec[1], spec[2])

        self._load_immersive_textures()

    def _decode_preloaded(self, preloaded):
        """Decode pre-loaded base64 texture data into self.textures."""
        import base64 as b64mod
        for cell_id_str, frames_b64 in preloaded.items():
            cell_id = int(cell_id_str)
            frames = []
            for b64_data in frames_b64:
                raw = b64mod.b64decode(b64_data)
                tex = []
                for i in range(0, len(raw), 3):
                    tex.append((raw[i], raw[i + 1], raw[i + 2]))
                frames.append(tex)
            self.textures[cell_id] = frames

    def _load_png_or_atlas(self, slot, path):
        """Load PNG from file, or fall back to paintings atlas for emulator."""
        # Check paintings atlas (for Salon and Art gallery in emulator)
        if _PRELOADED_PAINTINGS:
            basename = os.path.basename(path)
            if basename.endswith('.png'):
                pid = basename[:-4]
                b64 = _PRELOADED_PAINTINGS.get(pid)
                if b64:
                    import base64 as b64mod
                    raw = b64mod.b64decode(b64)
                    tex = []
                    for i in range(0, len(raw), 3):
                        tex.append((raw[i], raw[i + 1], raw[i + 2]))
                    self.textures[slot] = [tex]
                    return
        self.textures[slot] = [self._read_png(path)]

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
        if input_state.action_l or input_state.action_r:
            self.auto_walk = not self.auto_walk
            if self.auto_walk and self.WAYPOINTS:
                self._snap_to_nearest_waypoint()
                self.wp_pause = 0.0

        # When auto-walking, left/right adjust walk speed
        if self.auto_walk:
            if input_state.left:
                self.move_speed = max(0.5, self.move_speed - 0.1)
            if input_state.right:
                self.move_speed = min(9.6, self.move_speed + 0.1)

        self._input = input_state
        return input_state.any_direction or input_state.action_l or input_state.action_r

    def _snap_to_nearest_waypoint(self):
        best_i, best_d = 0, float('inf')
        for i, wp in enumerate(self.WAYPOINTS):
            dx = wp[0] - self.px
            dy = wp[1] - self.py
            d = dx * dx + dy * dy
            if d < best_d:
                best_d = d
                best_i = i
        self.wp_idx = best_i

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
        # Scale rotation rate with movement speed for tight turns at high speeds
        speed_factor = self.move_speed / 3.0  # 3.0 is default/medium speed
        self.pa += diff * min(1.0, 4.0 * dt * speed_factor)
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
        if not self.MAP or mx < 0 or mx >= self.MAP_W or my < 0 or my >= self.MAP_H:
            return 0
        for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            cx, cy = mx + dx, my + dy
            for _ in range(8):
                if cx < 0 or cx >= self.MAP_W or cy < 0 or cy >= self.MAP_H:
                    break
                if cy >= len(self.MAP) or cx >= len(self.MAP[cy]):
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
    dev_only = True

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

    _P = "paintings/"
    PAINTINGS = {
        2: ("png", _P + "great_wave.png"),
        3: ("png", _P + "the_scream.png"),
        4: ("png", _P + "starry_night.png"),
        5: ("png", _P + "water_lilies.png"),
        6: ("png", _P + "broadway_boogie.png"),
        7: ("png", _P + "girl_pearl_earring.png"),
        8: ("png", _P + "mona_lisa.png"),
        9: ("png", _P + "nighthawks.png"),
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
    dev_only = True

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
    dev_only = True

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
    dev_only = True

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
    dev_only = True

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
    dev_only = True

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
#  Gallery 7: SALON — connected gallery rooms, paintings 5 high
# ══════════════════════════════════════════════════════════════════

class GallerySalon(_Gallery3DBase):
    """Paris Salon: 4 connected rooms, paintings stacked 5 panels high."""

    name = "SALON"
    description = "Wall-to-wall paintings"
    category = "gallery"

    _WALL_SCALE = 5  # paintings stacked 5 panels high

    def __init__(self, display):
        import random as _rng

        # 4 rooms in a line, each 10 wide × 12 tall
        # Doorways at rows 5-6 in dividing walls
        # Painting slots: end rooms 30, middle rooms 28  →  30+28+28+30=116
        RW, RH = 10, 12
        N_ROOMS = 4
        W = RW * N_ROOMS  # 40
        H = RH             # 12
        self.MAP_W = W
        self.MAP_H = H
        self.START_POS = (RW / 2.0, H / 2.0)  # center of Room 1

        # Collect painting PIDs
        proj = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        paint_dir = os.path.join(proj, "assets", "paintings")
        try:
            from visuals.painting import PAINTING_META
            pids = [p for p in PAINTING_META
                    if (os.path.exists(os.path.join(paint_dir, f"{p}.png"))
                        or p in _PRELOADED_PAINTINGS)]
        except ImportError:
            pids = []
        _rng.shuffle(pids)

        # Build MAP + PAINTINGS dict
        _P = "paintings/"
        self.PAINTINGS = {}
        cell_id = 2
        paint_cells = []
        pid_iter = iter(pids)

        def _next():
            nonlocal cell_id
            pid = next(pid_iter, None)
            if pid is None:
                return 1
            cid = cell_id
            self.PAINTINGS[cid] = ("png", _P + f"{pid}.png")
            paint_cells.append(cid)
            cell_id += 1
            return cid

        # Start with solid grid, carve rooms
        grid = [[1] * W for _ in range(H)]

        DOOR_ROWS = (5, 6)  # doorway position (center of 8-row interior)

        for room in range(N_ROOMS):
            x0 = room * RW
            x1 = x0 + RW - 1

            # Carve interior (rows 2..H-3, cols x0+1..x1-1)
            for r in range(2, H - 2):
                for c in range(x0 + 1, x1):
                    grid[r][c] = 0

            # North painting wall (row 1)
            for c in range(x0 + 1, x1):
                grid[1][c] = _next()

            # South painting wall (row H-2)
            for c in range(x0 + 1, x1):
                grid[H - 2][c] = _next()

            # West wall (col x0)
            for r in range(2, H - 2):
                if room > 0 and r in DOOR_ROWS:
                    grid[r][x0] = 0       # doorway
                else:
                    grid[r][x0] = _next()

            # East wall (col x1)
            for r in range(2, H - 2):
                if room < N_ROOMS - 1 and r in DOOR_ROWS:
                    grid[r][x1] = 0       # doorway
                else:
                    grid[r][x1] = _next()

        self.MAP = grid

        # Stack map: 4 paintings above each ground-level painting (no repeats)
        self._stack_map = {}
        if paint_cells:
            n_stack = self._WALL_SCALE - 1  # 4 panels above ground
            for cid in paint_cells:
                pool = [c for c in paint_cells if c != cid]
                if len(pool) >= n_stack:
                    self._stack_map[cid] = _rng.sample(pool, n_stack)
                else:
                    self._stack_map[cid] = (pool * ((n_stack // len(pool)) + 1))[:n_stack]

        # Waypoints: (x, y, face_angle, pause_time)
        # Walk through each room, stopping to face each painting wall
        # face_angle: direction camera looks while paused
        FACE_N = -math.pi / 2   # look north (up, -Y)
        FACE_S = math.pi / 2    # look south (down, +Y)
        FACE_W = math.pi        # look west (-X)
        FACE_E = 0.0            # look east (+X)
        VIEW_PAUSE = 3.5        # seconds to gaze at a wall section
        TRANSIT = 0.2           # quick transit pause

        wps = []
        CORNER = 0.1  # brief corner-transition pause

        # Walk path distances from walls:
        # Interior rows 2-9, cols x0+1..x0+8
        # Stand 0.5 into the interior from the walkable edge
        NY = 2.5   # north walk path (row 2 center, close to north wall at row 1)
        SY = 9.5   # south walk path (row 9 center, close to south wall at row 10)

        for room in range(N_ROOMS):
            x0 = room * RW
            # Painting stop x-positions: center on groups of paintings
            # Paintings at cols x0+1..x0+8; 3 stops centered on thirds
            lx = x0 + 2.5   # left group (cols 1-3)
            mx = x0 + 5.0   # center group (cols 4-5)
            rx = x0 + 7.5   # right group (cols 6-8)
            # East/west walk x-positions (close to side walls)
            ex = x0 + 8.0   # east path (col 8 center, near east wall at col 9)
            wx = x0 + 2.0   # west path (col 2 center, near west wall at col 0)

            # -- North wall: walk left→right, camera faces north --
            for spot_x in (lx, mx, rx):
                wps.append((spot_x, NY, FACE_N, VIEW_PAUSE))

            # Corner: transition to east wall
            wps.append((ex, NY, FACE_E, CORNER))

            # -- East wall: walk top→bottom, camera faces east --
            for spot_y in (3.5, 6.0, 8.5):
                wps.append((ex, spot_y, FACE_E, VIEW_PAUSE))

            # Corner: transition to south wall
            wps.append((rx, SY, FACE_S, CORNER))

            # -- South wall: walk right→left, camera faces south --
            for spot_x in (rx, mx, lx):
                wps.append((spot_x, SY, FACE_S, VIEW_PAUSE))

            # Corner: transition to west wall
            wps.append((wx, SY, FACE_W, CORNER))

            # -- West wall: walk bottom→top, camera faces west --
            # Skip doorway rows (5-6) for rooms after the first
            west_stops = [8.5, 6.0, 3.5]
            if room > 0:
                west_stops = [y for y in west_stops
                              if not (4.5 < y < 7.0)]
            for spot_y in west_stops:
                wps.append((wx, spot_y, FACE_W, VIEW_PAUSE))

            # Through doorway to next room (enter directly onto north wall)
            if room < N_ROOMS - 1:
                door_x = x0 + RW - 0.5
                wps.append((door_x, 5.5, FACE_E, TRANSIT))

        self.WAYPOINTS = wps
        super().__init__(display)

    def _load_textures(self):
        if self.textures:
            return  # already loaded — skip on subsequent resets
        super()._load_textures()

    def reset(self):
        super().reset()
        self.move_speed = 1.6       # slow gallery stroll
        self._face_angle = None   # target angle during viewing pause

    # -- Auto-walk override: (x, y, face_angle, pause) waypoints --

    def _auto_walk(self, dt):
        if not self.WAYPOINTS:
            return
        # During viewing pause: hold position, smoothly face target
        if self.wp_pause > 0:
            self.wp_pause -= dt
            if self._face_angle is not None:
                diff = self._face_angle - self.pa
                while diff > math.pi:
                    diff -= 2 * math.pi
                while diff < -math.pi:
                    diff += 2 * math.pi
                if abs(diff) < 0.005:
                    self.pa = self._face_angle  # snap to stop jitter
                else:
                    self.pa += diff * min(1.0, 2.0 * dt)
            return

        wp = self.WAYPOINTS[self.wp_idx]
        tx, ty, face, pause = wp[0], wp[1], wp[2], wp[3]

        dx = tx - self.px
        dy = ty - self.py
        dist = math.sqrt(dx * dx + dy * dy)

        if dist < 0.15:
            self.px, self.py = tx, ty  # snap exactly
            self._face_angle = face
            self.wp_pause = pause
            self.wp_idx = (self.wp_idx + 1) % len(self.WAYPOINTS)
            return

        # Move directly toward target (not camera-relative)
        move_angle = math.atan2(dy, dx)
        speed = min(self.move_speed * dt, dist)  # natural deceleration
        self.px += math.cos(move_angle) * speed
        self.py += math.sin(move_angle) * speed

        # Camera: smoothly rotate toward face_angle of current target
        target_a = face if face is not None else move_angle
        diff = target_a - self.pa
        while diff > math.pi:
            diff -= 2 * math.pi
        while diff < -math.pi:
            diff += 2 * math.pi
        self.pa += diff * min(1.0, 3.0 * dt)

    # -- Emissive ceiling + white marble floor --

    def _render_frame(self):
        half = GRID_SIZE // 2
        # Bright emissive ceiling (gallery lighting)
        ceil = (220, 215, 200)
        for y in range(half):
            for x in range(GRID_SIZE):
                self.display.set_pixel(x, y, ceil)
        # White marble floor with perspective gradient
        for y in range(half, GRID_SIZE):
            f = (y - half) / (GRID_SIZE - half)   # 0 at horizon, 1 at viewer
            v = int(160 + 60 * f)                  # 160 (far) → 220 (near)
            marble = (v, v, v - 5)
            for x in range(GRID_SIZE):
                self.display.set_pixel(x, y, marble)
        for col in range(GRID_SIZE):
            self._cast_ray(col, self.pa + self.ray_offsets[col])

    # -- Raycaster with 5-panel stacking + bright gallery lighting --

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
        for _ in range(48):
            if side_dist_x < side_dist_y:
                side_dist_x += delta_x
                map_x += step_x
                side = 0
            else:
                side_dist_y += delta_y
                map_y += step_y
                side = 1
            if (map_x < 0 or map_x >= self.MAP_W
                    or map_y < 0 or map_y >= self.MAP_H):
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

        # Texture column
        if side == 0:
            wall_x = self.py + perp_dist * sin_a
        else:
            wall_x = self.px + perp_dist * cos_a
        wall_x -= int(wall_x)
        tex_col = int(wall_x * GRID_SIZE)
        if tex_col >= GRID_SIZE:
            tex_col = GRID_SIZE - 1

        # Well-lit gallery: much brighter than base class fog
        fog = min(1.0, 5.0 / (perp_dist + 1.0))
        if side == 1:
            fog *= 0.85

        # --- 5-panel stacked wall ---
        scale = self._WALL_SCALE
        unit_h = GRID_SIZE / perp_dist          # screen pixels per world unit
        half = GRID_SIZE // 2
        # Camera at 0.5 units; wall spans 0 (floor) to scale (top)
        draw_top = half - (scale - 0.5) * unit_h
        draw_bot = half + 0.5 * unit_h
        ds = max(0, int(draw_top))
        de = min(GRID_SIZE - 1, int(draw_bot))

        is_painting = cell >= 2 and cell in self.textures

        for y in range(ds, de + 1):
            # World height from floor (0 = floor, scale = ceiling)
            world_h = (draw_bot - y) / unit_h
            panel = int(world_h)
            panel = max(0, min(scale - 1, panel))
            frac = world_h - panel           # 0 at panel bottom, ~1 at top
            tex_y = int((1.0 - frac) * GRID_SIZE)
            tex_y = max(0, min(GRID_SIZE - 1, tex_y))

            tex = None
            if is_painting:
                if panel == 0:
                    tex_cell = cell          # ground level = actual painting
                else:
                    stack = self._stack_map.get(cell)
                    tex_cell = stack[panel - 1] if stack else cell
                frames = self.textures.get(tex_cell)
                if frames:
                    tex = frames[0]

            if tex is not None:
                r, g, b = tex[tex_y * GRID_SIZE + tex_col]
                # Gold frame at panel edges
                if (tex_col <= 1 or tex_col >= GRID_SIZE - 2
                        or tex_y <= 1 or tex_y >= GRID_SIZE - 2):
                    r, g, b = GOLD if (tex_col + tex_y) % 2 == 0 else GOLD_DARK
            else:
                r, g, b = 210, 205, 195      # bright warm plaster

            r = int(r * fog)
            g = int(g * fog)
            b = int(b * fog)
            self.display.set_pixel(col, y, (r, g, b))


# ══════════════════════════════════════════════════════════════════
#  Grand Museum — paintings organized by art-historical period
# ══════════════════════════════════════════════════════════════════

MOVEMENT_TO_WING = {
    # Ancient & Medieval
    "Ancient Egypt": "Ancient & Medieval",
    "Roman Fresco": "Ancient & Medieval",
    "Roman Mosaic": "Ancient & Medieval",
    "Fayum (Roman Egypt)": "Ancient & Medieval",
    "Byzantine": "Ancient & Medieval",
    "Gothic Illumination": "Ancient & Medieval",
    "Insular Illumination": "Ancient & Medieval",
    "Ethiopian": "Ancient & Medieval",
    "Indian (Gupta)": "Ancient & Medieval",
    # Renaissance
    "Renaissance": "Renaissance",
    "Northern Renaissance": "Renaissance",
    "Proto-Renaissance": "Renaissance",
    "Mannerism": "Renaissance",
    # Baroque & Rococo
    "Baroque": "Baroque & Rococo",
    "Rococo": "Baroque & Rococo",
    "Veduta": "Baroque & Rococo",
    # Asian
    "Ukiyo-e": "Asian",
    "Chinese (Five Dynasties)": "Asian",
    "Chinese (Song Dynasty)": "Asian",
    "Korean (Joseon)": "Asian",
    "Japanese (Momoyama)": "Asian",
    "Japanese (Muromachi)": "Asian",
    "Japanese (Rinpa)": "Asian",
    "Indian (Rajput)": "Asian",
    "Mughal": "Asian",
    "Persian (Safavid)": "Asian",
    "Persian (Timurid)": "Asian",
    "Ottoman": "Asian",
    # Romanticism & Realism
    "Romanticism": "Romanticism & Realism",
    "Realism": "Romanticism & Realism",
    "Neoclassicism": "Romanticism & Realism",
    "Hudson River School": "Romanticism & Realism",
    "Academic": "Romanticism & Realism",
    "Pre-Raphaelite": "Romanticism & Realism",
    "Scientific": "Romanticism & Realism",
    "Regionalism": "Romanticism & Realism",
    # Impressionism
    "Impressionism": "Impressionism",
    "Post-Impressionism": "Impressionism",
    "Pointillism": "Impressionism",
    "Art Nouveau": "Impressionism",
    # Modern
    "Expressionism": "Modern",
    "Abstract": "Modern",
    "Cubism": "Modern",
    "Fauvism": "Modern",
    "Suprematism": "Modern",
    "Futurism": "Modern",
    "Constructivism": "Modern",
}

WING_ORDER = [
    "Ancient & Medieval",
    "Renaissance",
    "Baroque & Rococo",
    "Asian",
    "Romanticism & Realism",
    "Impressionism",
    "Modern",
]

WING_COLORS = {
    "Ancient & Medieval": (200, 195, 180),
    "Renaissance": (210, 205, 195),
    "Baroque & Rococo": (200, 195, 205),
    "Asian": (195, 205, 195),
    "Romanticism & Realism": (210, 200, 195),
    "Impressionism": (205, 210, 210),
    "Modern": (210, 210, 210),
}


class GalleryMuseum(_Gallery3DBase):
    """Grand Museum: intimate serpentine gallery with interior baffles.

    Paintings organized by period into color-coded wings.  Lower ceilings
    (2-panel walls), spaced paintings with plaster between, interior
    partition walls creating winding paths through each wing.
    """

    name = "GRAND MUSEUM"
    description = "Paintings by period"
    category = "gallery"

    _WALL_SCALE = 2  # Normal-height walls: painting on bottom, plaster above

    def __init__(self, display):
        import random as _rng
        import json as _json

        # Load movement data from paintings.json
        proj = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        paint_dir = os.path.join(proj, "assets", "paintings")
        pj_path = os.path.join(proj, "tools", "paintings.json")
        try:
            with open(pj_path) as f:
                pj_data = _json.load(f)
        except (OSError, ValueError):
            pj_data = {}

        # Get available PIDs
        try:
            from visuals.painting import PAINTING_META
            pids = [p for p in PAINTING_META
                    if (os.path.exists(os.path.join(paint_dir, f"{p}.png"))
                        or p in _PRELOADED_PAINTINGS)]
        except ImportError:
            pids = []

        # Sort PIDs into wings
        wing_pids = {w: [] for w in WING_ORDER}
        for pid in pids:
            movement = pj_data.get(pid, {}).get("movement", "")
            wing = MOVEMENT_TO_WING.get(movement, "Modern")
            wing_pids[wing].append(pid)

        # Shuffle within each wing
        for w in WING_ORDER:
            _rng.shuffle(wing_pids[w])

        # Allocate rooms per wing — enough capacity for every painting
        n_paintings = sum(len(v) for v in wing_pids.values())
        wing_rooms = {}
        for w in WING_ORDER:
            count = len(wing_pids[w])
            wing_rooms[w] = -(-count // 24) if count > 0 else 0  # ceil

        total_rooms = sum(wing_rooms.values())
        # Trim if over-allocated
        total_rooms = min(total_rooms, max(1, -(-n_paintings // 24)))

        # Room: 14 wide × 15 tall — 2-cell corridors, no side-wall paintings
        #
        #   ##############      row 0:  outer wall
        #   #P_P_P_P_P_P#      row 1:  N paintings (6 + spacers)
        #   #............#      row 2:  walk ┐ 2-cell corridor
        #   #............#      row 3:  walk ┘ (view N wall ~1.5 away)
        #   #.PWPWPWPW...#      row 4:  left baffle  (cols 2-9, gap 10-12)
        #   #............#      row 5:  walk ┐ 2-cell corridor
        #   #............#      row 6:  walk ┘ (view baffles 4 & 7)
        #   #...WPWPWPWP.#      row 7:  right baffle (cols 4-11, gap 1-3)
        #   #............#      row 8:  walk ┐ 2-cell corridor / doorway
        #   #............#      row 9:  walk ┘
        #   #.PWPWPWPW...#      row 10: left baffle  (cols 2-9, gap 10-12)
        #   #............#      row 11: walk ┐ 2-cell corridor
        #   #............#      row 12: walk ┘ (view baffle 10 & S wall)
        #   #P_P_P_P_P_P#      row 13: S paintings (6 + spacers)
        #   ##############      row 14: outer wall

        RW, RH = 14, 15
        W = RW * total_rooms
        H = RH
        self.MAP_W = W
        self.MAP_H = H
        self.START_POS = (RW / 2.0, 2.5)

        # Build wing boundaries for wall coloring
        self._wing_boundaries = []
        room_idx = 0
        for w in WING_ORDER:
            n = wing_rooms[w]
            x_start = room_idx * RW
            x_end = (room_idx + n) * RW
            self._wing_boundaries.append((x_start, x_end, WING_COLORS[w]))
            room_idx += n

        # Build ordered PID list: wing by wing
        ordered_pids = []
        for w in WING_ORDER:
            ordered_pids.extend(wing_pids[w])

        # Build MAP + PAINTINGS dict
        _P = "paintings/"
        self.PAINTINGS = {}
        cell_id = 2
        pid_iter = iter(ordered_pids)

        def _next():
            nonlocal cell_id
            pid = next(pid_iter, None)
            if pid is None:
                return 1  # plain wall when out of paintings
            cid = cell_id
            self.PAINTINGS[cid] = ("png", _P + f"{pid}.png")
            cell_id += 1
            return cid

        # Start with solid grid, carve rooms with baffles
        grid = [[1] * W for _ in range(H)]
        DOOR_ROWS = (8, 9)

        for room in range(total_rooms):
            x0 = room * RW

            # Carve walkable interior (rows 2-12, cols x0+1..x0+12)
            for r in range(2, 13):
                for c in range(x0 + 1, x0 + 13):
                    grid[r][c] = 0

            # North painting wall (row 1): 6 paintings with spacers
            for i in range(12):
                c = x0 + 1 + i
                grid[1][c] = _next() if i % 2 == 0 else 1

            # South painting wall (row 13): 6 paintings with spacers
            for i in range(12):
                c = x0 + 1 + i
                grid[13][c] = _next() if i % 2 == 0 else 1

            # E/W walls: no paintings — plain wall + doorway only
            for r in range(2, 13):
                if room > 0 and r in DOOR_ROWS:
                    grid[r][x0] = 0
                else:
                    grid[r][x0] = 1
            for r in range(2, 13):
                if room < total_rooms - 1 and r in DOOR_ROWS:
                    grid[r][x0 + 13] = 0
                else:
                    grid[r][x0 + 13] = 1

            # Left baffles (rows 4, 10): cols x0+2..x0+9
            for br in (4, 10):
                for c in range(x0 + 2, x0 + 10):
                    if (c - x0) % 2 == 0:
                        grid[br][c] = _next()
                    else:
                        grid[br][c] = 1

            # Right baffle (row 7): cols x0+4..x0+11
            for c in range(x0 + 4, x0 + 12):
                if (c - x0) % 2 == 1:
                    grid[7][c] = _next()
                else:
                    grid[7][c] = 1

        self.MAP = grid

        # ── Serpentine waypoints ──────────────────────────────────
        # Snake through 2-cell corridors, viewing paintings ~1.5 cells away.
        # (x, y, face_angle, pause_time)
        FACE_N = -math.pi / 2
        FACE_S = math.pi / 2
        FACE_W = math.pi
        FACE_E = 0.0
        VIEW = 3.0    # seconds to gaze at a wall section
        TRANSIT = 0.3  # quick transit pause

        wps = []
        for room in range(total_rooms):
            x0 = room * RW
            # Viewing positions for N/S walls (6 paintings → 3 pair-stops)
            wl = x0 + 2.0     # left pair  (cols 1, 3)
            wm = x0 + 6.0     # mid pair   (cols 5, 7)
            wr = x0 + 10.0    # right pair (cols 9, 11)
            # Viewing positions for left baffles (paintings at cols 2,4,6,8)
            bl = x0 + 3.0     # left pair  (cols 2, 4)
            br = x0 + 7.0     # right pair (cols 6, 8)
            # Viewing positions for right baffle (paintings at cols 5,7,9,11)
            rl = x0 + 6.0     # left pair  (cols 5, 7)
            rr = x0 + 10.0    # right pair (cols 9, 11)
            # Gap positions
            rgap = x0 + 11.5  # right gap (left-baffle gap at cols 10-12)
            lgap = x0 + 2.5   # left gap  (right-baffle gap at cols 1-3)

            # Entry: rooms > 0 enter from west doorway at rows 8-9,
            # route via col 12 (always in gap) up to north corridor
            if room > 0:
                wps.append((x0 + 1.5, 8.5, FACE_E, TRANSIT))
                wps.append((x0 + 12.5, 8.5, FACE_N, TRANSIT))
                wps.append((x0 + 12.5, 2.5, FACE_W, TRANSIT))

            # 1. North wall from row 2.5 (~1.5 cells away), face N
            wps.append((wl, 2.5, FACE_N, VIEW))
            wps.append((wm, 2.5, FACE_N, VIEW))
            wps.append((wr, 2.5, FACE_N, VIEW))

            # Down through right gap to corridor 5-6
            wps.append((rgap, 5.5, FACE_W, TRANSIT))

            # 2. Baffle 4 south face from row 5.5, face N
            wps.append((br, 5.5, FACE_N, VIEW))
            wps.append((bl, 5.5, FACE_N, VIEW))

            # 3. Baffle 7 north face from row 5.5, face S
            wps.append((rl, 5.5, FACE_S, VIEW))
            wps.append((rr, 5.5, FACE_S, VIEW))

            # Through left gap to corridor 8-9
            wps.append((lgap, 5.5, FACE_S, TRANSIT))
            wps.append((lgap, 8.5, FACE_E, TRANSIT))

            # 4. Baffle 10 north face from row 8.5, face S
            wps.append((bl, 8.5, FACE_S, VIEW))
            wps.append((br, 8.5, FACE_S, VIEW))

            # Down through right gap to corridor 11-12
            wps.append((rgap, 11.5, FACE_W, TRANSIT))

            # 5. South wall from row 12.5 (~1.5 cells away), face S
            wps.append((wr, 12.5, FACE_S, VIEW))
            wps.append((wm, 12.5, FACE_S, VIEW))
            wps.append((wl, 12.5, FACE_S, VIEW))

            # Exit: back up through right gap to doorway row
            wps.append((rgap, 11.5, FACE_N, TRANSIT))
            wps.append((rgap, 8.5, FACE_E, TRANSIT))

            # Through east doorway to next room
            if room < total_rooms - 1:
                wps.append((x0 + 13.5, 8.5, FACE_E, TRANSIT))

        self.WAYPOINTS = wps
        super().__init__(display)

    def _load_textures(self):
        if self.textures:
            return
        super()._load_textures()

    def reset(self):
        super().reset()
        self.move_speed = 1.6
        self._face_angle = None

    def _auto_walk(self, dt):
        if not self.WAYPOINTS:
            return
        if self.wp_pause > 0:
            self.wp_pause -= dt
            if self._face_angle is not None:
                diff = self._face_angle - self.pa
                while diff > math.pi:
                    diff -= 2 * math.pi
                while diff < -math.pi:
                    diff += 2 * math.pi
                if abs(diff) < 0.005:
                    self.pa = self._face_angle
                else:
                    self.pa += diff * min(1.0, 2.0 * dt)
            return

        wp = self.WAYPOINTS[self.wp_idx]
        tx, ty, face, pause = wp[0], wp[1], wp[2], wp[3]

        dx = tx - self.px
        dy = ty - self.py
        dist = math.sqrt(dx * dx + dy * dy)

        if dist < 0.15:
            self.px, self.py = tx, ty
            self._face_angle = face
            self.wp_pause = pause
            self.wp_idx = (self.wp_idx + 1) % len(self.WAYPOINTS)
            return

        move_angle = math.atan2(dy, dx)
        speed = min(self.move_speed * dt, dist)
        self.px += math.cos(move_angle) * speed
        self.py += math.sin(move_angle) * speed

        target_a = face if face is not None else move_angle
        diff = target_a - self.pa
        while diff > math.pi:
            diff -= 2 * math.pi
        while diff < -math.pi:
            diff += 2 * math.pi
        self.pa += diff * min(1.0, 3.0 * dt)

    def _get_wall_color(self, map_x):
        for x_start, x_end, color in self._wing_boundaries:
            if x_start <= map_x < x_end:
                return color
        return (210, 205, 195)

    def _render_frame(self):
        half = GRID_SIZE // 2
        ceil = (220, 215, 200)
        for y in range(half):
            for x in range(GRID_SIZE):
                self.display.set_pixel(x, y, ceil)
        for y in range(half, GRID_SIZE):
            f = (y - half) / (GRID_SIZE - half)
            v = int(160 + 60 * f)
            marble = (v, v, v - 5)
            for x in range(GRID_SIZE):
                self.display.set_pixel(x, y, marble)
        for col in range(GRID_SIZE):
            self._cast_ray(col, self.pa + self.ray_offsets[col])

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
        for _ in range(48):
            if side_dist_x < side_dist_y:
                side_dist_x += delta_x
                map_x += step_x
                side = 0
            else:
                side_dist_y += delta_y
                map_y += step_y
                side = 1
            if (map_x < 0 or map_x >= self.MAP_W
                    or map_y < 0 or map_y >= self.MAP_H):
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

        if side == 0:
            wall_x = self.py + perp_dist * sin_a
        else:
            wall_x = self.px + perp_dist * cos_a
        wall_x -= int(wall_x)
        tex_col = int(wall_x * GRID_SIZE)
        if tex_col >= GRID_SIZE:
            tex_col = GRID_SIZE - 1

        fog = min(1.0, 5.0 / (perp_dist + 1.0))
        if side == 1:
            fog *= 0.85

        # 2-panel wall: panel 0 = painting, panel 1 = plaster
        scale = self._WALL_SCALE
        unit_h = GRID_SIZE / perp_dist
        half = GRID_SIZE // 2
        draw_top = half - (scale - 0.5) * unit_h
        draw_bot = half + 0.5 * unit_h
        ds = max(0, int(draw_top))
        de = min(GRID_SIZE - 1, int(draw_bot))

        is_painting = cell >= 2 and cell in self.textures
        wall_color = self._get_wall_color(map_x)

        for y in range(ds, de + 1):
            world_h = (draw_bot - y) / unit_h
            panel = int(world_h)
            panel = max(0, min(scale - 1, panel))
            frac = world_h - panel
            tex_y = int((1.0 - frac) * GRID_SIZE)
            tex_y = max(0, min(GRID_SIZE - 1, tex_y))

            tex = None
            if is_painting and panel == 0:
                frames = self.textures.get(cell)
                if frames:
                    tex = frames[0]

            if tex is not None:
                r, g, b = tex[tex_y * GRID_SIZE + tex_col]
                if (tex_col <= 1 or tex_col >= GRID_SIZE - 2
                        or tex_y <= 1 or tex_y >= GRID_SIZE - 2):
                    r, g, b = GOLD if (tex_col + tex_y) % 2 == 0 else GOLD_DARK
            else:
                r, g, b = wall_color

            r = int(r * fog)
            g = int(g * fog)
            b = int(b * fog)
            self.display.set_pixel(col, y, (r, g, b))


# Legacy alias — keep old import working
Gallery3D = GalleryArt
