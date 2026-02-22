"""
Seismic - Earthquake Wave Propagation
======================================
Earthquake generates P-waves (fast, compressional) and S-waves (slower,
shear) that propagate through Earth's layered interior.  Waves refract
at layer boundaries via Snell's law.  S-waves are blocked by the liquid
outer core, creating a shadow zone -- literally how we discovered Earth
has a liquid core.

Controls:
  Left/Right  - Cycle focus mode (WAVES / SHADOW / REFLECT)
  Up/Down     - Adjust speed
  Action      - Trigger quake at different positions
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE

# ── Earth geometry ──────────────────────────────────────────────
CX, CY = 32, 32        # Earth center
R_EARTH = 30            # Outer radius

# Layer boundaries (inner radius of each shell)
LAYERS = [
    # (name, r_inner, r_outer, color, p_speed, s_speed)
    ("inner_core",  0,  6, (240, 220, 140), 11.0, 3.5),
    ("outer_core",  6, 12, (200, 160,  40),  8.0, 0.0),  # liquid!
    ("lower_mantle",12, 22, (160,  50,  30), 13.0, 7.0),
    ("upper_mantle",22, 28, (180,  80,  40),  8.0, 4.5),
    ("crust",       28, 30, (160, 120,  80),  6.0, 3.5),
]

BG_COLOR = (5, 5, 15)

# ── Ray tracing parameters ─────────────────────────────────────
NUM_RAYS = 30
RAY_STEP = 0.15         # spatial step per iteration
MAX_RAY_STEPS = 400     # prevent infinite loops

# ── Focus modes ─────────────────────────────────────────────────
FOCUS_MODES = ["WAVES", "SHADOW", "REFLECT"]

# ── Colors ──────────────────────────────────────────────────────
P_COLOR = (80, 180, 255)     # cyan-blue
P_BRIGHT = (140, 220, 255)
S_COLOR = (255, 100, 50)     # red-orange
S_BRIGHT = (255, 180, 100)
SHADOW_COLOR = (120, 20, 20) # dim red arc for shadow zone

# ── Precomputed layer lookup (2D list) ──────────────────────────
# earth_layer[y][x] = layer index, or -1 if outside earth
# Built once at module load.
_earth_layer = []
_earth_bg_waves = []   # pre-dimmed colors for WAVES/REFLECT mode (dim=0.35)
_earth_bg_shadow = []  # pre-dimmed colors for SHADOW mode (dim=0.2)

def _init_earth_tables():
    """Build earth layer and background color tables once at import."""
    for y in range(GRID_SIZE):
        row_layer = []
        row_bg_w = []
        row_bg_s = []
        for x in range(GRID_SIZE):
            dx = x - CX
            dy = y - CY
            r = math.sqrt(dx * dx + dy * dy)
            if r < R_EARTH:
                layer_idx = -1
                for i, (_, r_in, r_out, _, _, _) in enumerate(LAYERS):
                    if r_in <= r < r_out:
                        layer_idx = i
                        break
                row_layer.append(layer_idx)
                if layer_idx >= 0:
                    c = LAYERS[layer_idx][3]
                    row_bg_w.append((int(c[0] * 0.35), int(c[1] * 0.35), int(c[2] * 0.35)))
                    row_bg_s.append((int(c[0] * 0.2), int(c[1] * 0.2), int(c[2] * 0.2)))
                else:
                    row_bg_w.append(BG_COLOR)
                    row_bg_s.append(BG_COLOR)
            else:
                row_layer.append(-1)
                row_bg_w.append(BG_COLOR)
                row_bg_s.append(BG_COLOR)
        _earth_layer.append(row_layer)
        _earth_bg_waves.append(row_bg_w)
        _earth_bg_shadow.append(row_bg_s)

_init_earth_tables()


def _get_layer(r):
    """Return layer index for a given radius from center."""
    for i, (_, r_in, r_out, _, _, _) in enumerate(LAYERS):
        if r_in <= r < r_out:
            return i
    return -1


def _get_speeds(r):
    """Return (p_speed, s_speed) at radius r."""
    idx = _get_layer(r)
    if idx < 0:
        return (0.0, 0.0)
    return (LAYERS[idx][4], LAYERS[idx][5])


def _trace_ray(source_x, source_y, angle, wave_type):
    """Trace a single seismic ray through the earth.

    wave_type: 'P' or 'S'
    Returns list of (x, y) points along the ray path, snapped to int pixels.
    Each point is (ix, iy) already rounded for fast drawing.
    """
    path = []
    x, y = source_x, source_y
    dx = math.cos(angle)
    dy = math.sin(angle)

    speed_idx = 4 if wave_type == 'P' else 5
    _sqrt = math.sqrt

    for _ in range(MAX_RAY_STEPS):
        # Snap to pixel grid and store
        ix = int(x + 0.5)
        iy = int(y + 0.5)
        if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
            path.append((ix, iy))
        else:
            # If off-screen but still inside earth radius, keep tracing
            # but don't store the point
            pass

        # Current radius
        rx, ry = x - CX, y - CY
        r = _sqrt(rx * rx + ry * ry)

        # Outside earth?
        if r >= R_EARTH:
            break

        # Get current layer speed
        layer_idx = _get_layer(r)
        if layer_idx < 0:
            break

        current_speed = LAYERS[layer_idx][speed_idx]

        # S-wave in outer core = blocked
        if wave_type == 'S' and LAYERS[layer_idx][0] == "outer_core":
            break

        if current_speed <= 0:
            break

        # Step forward
        step = RAY_STEP
        nx = x + dx * step
        ny = y + dy * step

        # Check new radius
        nrx, nry = nx - CX, ny - CY
        nr = _sqrt(nrx * nrx + nry * nry)

        new_layer_idx = _get_layer(nr)

        # If we crossed a layer boundary, apply Snell's law
        if new_layer_idx != layer_idx and new_layer_idx >= 0:
            new_speed = LAYERS[new_layer_idx][speed_idx]

            # S-wave entering outer core
            if wave_type == 'S' and LAYERS[new_layer_idx][0] == "outer_core":
                nix = int(nx + 0.5)
                niy = int(ny + 0.5)
                if 0 <= nix < GRID_SIZE and 0 <= niy < GRID_SIZE:
                    path.append((nix, niy))
                break

            if new_speed <= 0:
                break

            # Normal at boundary = radial direction
            if r > 0.01:
                norm_x, norm_y = rx / r, ry / r
            else:
                norm_x, norm_y = 0.0, -1.0

            # Angle of incidence
            dot = dx * norm_x + dy * norm_y
            if dot > 0:
                norm_x, norm_y = -norm_x, -norm_y
                dot = -dot

            sin_i = _sqrt(max(0, 1.0 - dot * dot))
            ratio = new_speed / current_speed
            sin_r = sin_i * ratio

            if sin_r >= 1.0:
                # Total internal reflection
                dot_r = dx * norm_x + dy * norm_y
                dx = dx - 2 * dot_r * norm_x
                dy = dy - 2 * dot_r * norm_y
                mag = _sqrt(dx * dx + dy * dy)
                if mag > 0:
                    dx /= mag
                    dy /= mag
            else:
                # Snell's law refraction
                cos_r = _sqrt(max(0, 1.0 - sin_r * sin_r))
                tan_x = dx - dot * norm_x
                tan_y = dy - dot * norm_y
                tan_mag = _sqrt(tan_x * tan_x + tan_y * tan_y)
                if tan_mag > 0.001:
                    tan_x /= tan_mag
                    tan_y /= tan_mag
                    dx = sin_r * tan_x + cos_r * norm_x
                    dy = sin_r * tan_y + cos_r * norm_y

                mag = _sqrt(dx * dx + dy * dy)
                if mag > 0:
                    dx /= mag
                    dy /= mag

        x, y = nx, ny

    return path


def _trace_reflected_ray(source_x, source_y, angle, wave_type, reflect_layer_name):
    """Trace a ray that reflects off a specific layer boundary."""
    path = []
    x, y = source_x, source_y
    dx = math.cos(angle)
    dy = math.sin(angle)
    speed_idx = 4 if wave_type == 'P' else 5
    reflected = False
    _sqrt = math.sqrt

    for _ in range(MAX_RAY_STEPS):
        ix = int(x + 0.5)
        iy = int(y + 0.5)
        if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
            path.append((ix, iy))

        rx, ry = x - CX, y - CY
        r = _sqrt(rx * rx + ry * ry)

        if r >= R_EARTH:
            break

        layer_idx = _get_layer(r)
        if layer_idx < 0:
            break

        current_speed = LAYERS[layer_idx][speed_idx]
        if current_speed <= 0:
            break

        step = RAY_STEP
        nx = x + dx * step
        ny = y + dy * step

        nrx, nry = nx - CX, ny - CY
        nr = _sqrt(nrx * nrx + nry * nry)
        new_layer_idx = _get_layer(nr)

        # Reflect at target boundary
        if not reflected and new_layer_idx != layer_idx and new_layer_idx >= 0:
            if LAYERS[new_layer_idx][0] == reflect_layer_name:
                if r > 0.01:
                    norm_x, norm_y = rx / r, ry / r
                else:
                    norm_x, norm_y = 0.0, -1.0
                dot = dx * norm_x + dy * norm_y
                dx = dx - 2 * dot * norm_x
                dy = dy - 2 * dot * norm_y
                mag = _sqrt(dx * dx + dy * dy)
                if mag > 0:
                    dx /= mag
                    dy /= mag
                reflected = True
                x, y = nx, ny
                continue

        # Normal refraction at other boundaries
        if new_layer_idx != layer_idx and new_layer_idx >= 0:
            new_speed = LAYERS[new_layer_idx][speed_idx]
            if new_speed > 0 and current_speed > 0:
                if r > 0.01:
                    norm_x, norm_y = rx / r, ry / r
                else:
                    norm_x, norm_y = 0.0, -1.0
                dot = dx * norm_x + dy * norm_y
                if dot > 0:
                    norm_x, norm_y = -norm_x, -norm_y
                    dot = -dot
                sin_i = _sqrt(max(0, 1.0 - dot * dot))
                ratio = new_speed / current_speed
                sin_r = sin_i * ratio
                if sin_r < 1.0:
                    cos_r = _sqrt(max(0, 1.0 - sin_r * sin_r))
                    tan_x = dx - dot * norm_x
                    tan_y = dy - dot * norm_y
                    tan_mag = _sqrt(tan_x * tan_x + tan_y * tan_y)
                    if tan_mag > 0.001:
                        tan_x /= tan_mag
                        tan_y /= tan_mag
                        dx = sin_r * tan_x + cos_r * norm_x
                        dy = sin_r * tan_y + cos_r * norm_y
                    mag = _sqrt(dx * dx + dy * dy)
                    if mag > 0:
                        dx /= mag
                        dy /= mag
                else:
                    dot2 = dx * norm_x + dy * norm_y
                    dx = dx - 2 * dot2 * norm_x
                    dy = dy - 2 * dot2 * norm_y
                    mag = _sqrt(dx * dx + dy * dy)
                    if mag > 0:
                        dx /= mag
                        dy /= mag

        x, y = nx, ny

    return path


class Seismic(Visual):
    name = "SEISMIC"
    description = "Earthquake wave propagation"
    category = "science"

    # Source positions: angles around the crust (in radians)
    SOURCE_ANGLES = [
        -math.pi / 2,       # top
        -math.pi / 4,       # upper right
        0,                   # right
        math.pi / 4,        # lower right
        -3 * math.pi / 4,   # upper left
        math.pi,             # left
    ]

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

        # Focus mode
        self.focus_idx = 0

        # Speed multiplier
        self.speed = 1.0

        # Source position
        self.source_idx = 0

        # Ray data
        self.p_rays = []
        self.s_rays = []
        self.reflect_rays = []

        # Animation
        self.wave_time = 0.0
        self.propagating = False
        self.quake_flash = 0.0

        # Auto-trigger timer
        self.idle_timer = 0.0

        # Overlay
        self.overlay_timer = 0.0
        self.overlay_lines = []

        # Cached shadow zone
        self._shadow_pixels = []
        self._shadow_valid = False

        # Trigger initial quake
        self._trigger_quake()

    def _get_source_pos(self):
        """Get earthquake source (x, y) on the crust surface."""
        angle = self.SOURCE_ANGLES[self.source_idx]
        r = R_EARTH - 1.5  # just inside crust
        return CX + r * math.cos(angle), CY + r * math.sin(angle)

    def _trigger_quake(self):
        """Launch seismic rays from the current source position."""
        sx, sy = self._get_source_pos()

        # Source angle (from center to source)
        src_angle = math.atan2(sy - CY, sx - CX)

        # Fan rays inward: spread 160 degrees centered on the inward direction
        inward = src_angle + math.pi
        half_fan = math.radians(80)

        self.p_rays = []
        self.s_rays = []
        self.reflect_rays = []

        for i in range(NUM_RAYS):
            t = i / (NUM_RAYS - 1)  # 0..1
            ray_angle = inward - half_fan + t * 2 * half_fan

            p_path = _trace_ray(sx, sy, ray_angle, 'P')
            s_path = _trace_ray(sx, sy, ray_angle, 'S')

            if len(p_path) > 2:
                self.p_rays.append(p_path)
            if len(s_path) > 2:
                self.s_rays.append(s_path)

        # Reflected rays for REFLECT mode
        # PcP: P-wave reflected off outer core boundary
        for i in range(NUM_RAYS):
            t = i / (NUM_RAYS - 1)
            ray_angle = inward - half_fan + t * 2 * half_fan
            ref_path = _trace_reflected_ray(sx, sy, ray_angle, 'P', "outer_core")
            if len(ref_path) > 5:
                self.reflect_rays.append(('PcP', ref_path))

        # Precompute max ray length for propagation-done check
        self._max_ray_len = 0
        for path in self.p_rays:
            if len(path) > self._max_ray_len:
                self._max_ray_len = len(path)
        for path in self.s_rays:
            if len(path) > self._max_ray_len:
                self._max_ray_len = len(path)

        self.wave_time = 0.0
        self.propagating = True
        self.quake_flash = 0.3
        self.idle_timer = 0.0

        # Invalidate shadow zone cache
        self._shadow_valid = False

    def _compute_shadow_zone(self):
        """Find surface pixels where no direct S-waves arrive. Cached."""
        if self._shadow_valid:
            return self._shadow_pixels

        # Collect angles on the surface where S-wave rays arrived
        s_arrival_angles = set()
        for path in self.s_rays:
            if len(path) < 3:
                continue
            ex, ey = path[-1]
            # Check if last point is near surface using the layer table
            if 0 <= ex < GRID_SIZE and 0 <= ey < GRID_SIZE:
                layer = _earth_layer[ey][ex]
                if layer < 0:
                    # outside earth = reached surface
                    a = int(math.degrees(math.atan2(ey - CY, ex - CX))) % 360
                    s_arrival_angles.add(a)
                elif layer >= 3:  # upper_mantle or crust
                    a = int(math.degrees(math.atan2(ey - CY, ex - CX))) % 360
                    s_arrival_angles.add(a)

        # Shadow zone: surface pixels where no S-wave arrived
        shadow_pixels = []
        src_angle_deg = int(math.degrees(
            self.SOURCE_ANGLES[self.source_idx])) % 360

        for deg in range(360):
            diff = (deg - src_angle_deg + 180) % 360 - 180
            if abs(diff) < 15:
                continue
            if deg not in s_arrival_angles:
                rad = math.radians(deg)
                cos_r = math.cos(rad)
                sin_r = math.sin(rad)
                for r in range(28, 31):
                    px = int(CX + r * cos_r)
                    py = int(CY + r * sin_r)
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        shadow_pixels.append((px, py))

        self._shadow_pixels = shadow_pixels
        self._shadow_valid = True
        return shadow_pixels

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Action: trigger quake at next position
        if input_state.action_l or input_state.action_r:
            self.source_idx = (self.source_idx + 1) % len(self.SOURCE_ANGLES)
            self._trigger_quake()
            self.overlay_timer = 2.0
            self.overlay_lines = ["QUAKE!"]
            consumed = True

        # Left/Right: cycle focus mode
        if input_state.left_pressed:
            self.focus_idx = (self.focus_idx - 1) % len(FOCUS_MODES)
            self.overlay_timer = 2.0
            self.overlay_lines = [FOCUS_MODES[self.focus_idx]]
            consumed = True
        if input_state.right_pressed:
            self.focus_idx = (self.focus_idx + 1) % len(FOCUS_MODES)
            self.overlay_timer = 2.0
            self.overlay_lines = [FOCUS_MODES[self.focus_idx]]
            consumed = True

        # Up/Down: speed
        if input_state.up_pressed:
            self.speed = min(3.0, self.speed + 0.25)
            self.overlay_timer = 2.0
            self.overlay_lines = [f"SPEED {self.speed:.1f}x"]
            consumed = True
        if input_state.down_pressed:
            self.speed = max(0.25, self.speed - 0.25)
            self.overlay_timer = 2.0
            self.overlay_lines = [f"SPEED {self.speed:.1f}x"]
            consumed = True

        return consumed

    def update(self, dt: float):
        super().update(dt)

        # Overlay fade
        if self.overlay_timer > 0:
            self.overlay_timer -= dt

        # Quake flash
        if self.quake_flash > 0:
            self.quake_flash -= dt

        # Wave propagation
        if self.propagating:
            self.wave_time += dt * self.speed * 80.0  # steps per second

            if self.wave_time > self._max_ray_len + 60:
                self.propagating = False

        # Auto-trigger
        if not self.propagating:
            self.idle_timer += dt
            if self.idle_timer > 6.0:
                self.source_idx = (self.source_idx + 1) % len(self.SOURCE_ANGLES)
                self._trigger_quake()

    def _draw_rays(self, rays, wt, base_color, bright_color):
        """Draw a set of rays, only iterating near the wavefront + trail."""
        wavefront_width = 8
        trail_len = 80
        window = wavefront_width + trail_len  # total visible portion behind front
        set_pixel = self.display.set_pixel
        br, bg, bb = base_color
        hr, hg, hb = bright_color
        dr, dg, db = hr - br, hg - bg, hb - bb

        for path in rays:
            path_len = len(path)
            drawn = int(wt) if int(wt) < path_len else path_len

            # Only iterate the visible window near the wavefront
            start = drawn - window
            if start < 0:
                start = 0

            for j in range(start, drawn):
                ix, iy = path[j]
                dist_from_front = drawn - j
                if dist_from_front < wavefront_width:
                    t = 1.0 - dist_from_front / wavefront_width
                    set_pixel(ix, iy, (
                        int(br + dr * t),
                        int(bg + dg * t),
                        int(bb + db * t),
                    ))
                else:
                    fade = 1.0 - (dist_from_front - wavefront_width) / 80.0
                    if fade < 0.15:
                        fade = 0.15
                    set_pixel(ix, iy, (
                        int(br * fade),
                        int(bg * fade),
                        int(bb * fade),
                    ))

    def draw(self):
        self.display.clear()

        focus = FOCUS_MODES[self.focus_idx]
        set_pixel = self.display.set_pixel

        # Draw earth background from pre-rendered table
        bg_table = _earth_bg_shadow if focus == "SHADOW" else _earth_bg_waves
        for y in range(GRID_SIZE):
            bg_row = bg_table[y]
            for x in range(GRID_SIZE):
                set_pixel(x, y, bg_row[x])

        wt = self.wave_time

        if focus == "WAVES" or focus == "SHADOW":
            # Draw P-wave rays
            self._draw_rays(self.p_rays, wt, P_COLOR, P_BRIGHT)

            # Draw S-wave rays (slower)
            s_wt = wt * 0.55
            self._draw_rays(self.s_rays, s_wt, S_COLOR, S_BRIGHT)

        if focus == "REFLECT":
            # Draw reflected rays
            ref_wt = wt * 0.7
            ref_base = (80, 200, 120)
            ref_bright = (250, 255, 255)
            wavefront_width = 8

            for _, path in self.reflect_rays:
                path_len = len(path)
                drawn = int(ref_wt) if int(ref_wt) < path_len else path_len

                start = drawn - 88
                if start < 0:
                    start = 0

                for j in range(start, drawn):
                    ix, iy = path[j]
                    dist_from_front = drawn - j
                    if dist_from_front < wavefront_width:
                        t = 1.0 - dist_from_front / wavefront_width
                        set_pixel(ix, iy, (
                            int(80 + 170 * t),
                            int(200 + 55 * t),
                            int(120 + 135 * t),
                        ))
                    else:
                        fade = 1.0 - (dist_from_front - wavefront_width) / 80.0
                        if fade < 0.15:
                            fade = 0.15
                        set_pixel(ix, iy, (
                            int(80 * fade),
                            int(200 * fade),
                            int(120 * fade),
                        ))

        # Shadow zone highlighting
        if focus == "SHADOW" and wt > 100:
            shadow_pixels = self._compute_shadow_zone()
            pulse = 0.5 + 0.5 * math.sin(self.time * 3.0)
            sc_mul = 0.5 + 0.5 * pulse
            sc = (int(SHADOW_COLOR[0] * sc_mul),
                  int(SHADOW_COLOR[1] * sc_mul),
                  int(SHADOW_COLOR[2] * sc_mul))
            for px, py in shadow_pixels:
                set_pixel(px, py, sc)

            self.display.draw_text_small(2, 56, "SHADOW ZONE", (180, 60, 60))

        # Quake flash: bright spot at source
        if self.quake_flash > 0:
            sx, sy = self._get_source_pos()
            flash_r = int(3 * self.quake_flash / 0.3)
            bright = self.quake_flash / 0.15
            if bright > 1.0:
                bright = 1.0
            fr = int(255 * bright)
            fg = int(255 * bright)
            fb = int(200 * bright)
            isx, isy = int(sx), int(sy)
            for dy in range(-flash_r, flash_r + 1):
                for dx in range(-flash_r, flash_r + 1):
                    if dx * dx + dy * dy <= flash_r * flash_r:
                        fx, fy = isx + dx, isy + dy
                        if 0 <= fx < GRID_SIZE and 0 <= fy < GRID_SIZE:
                            set_pixel(fx, fy, (fr, fg, fb))

        # Wavefront labels
        if focus == "WAVES" and self.propagating and wt > 10:
            if self.p_rays:
                mid_p = self.p_rays[len(self.p_rays) // 2]
                p_idx = int(wt)
                if p_idx >= len(mid_p):
                    p_idx = len(mid_p) - 1
                if 0 < p_idx < len(mid_p):
                    px, py = mid_p[p_idx]
                    ly = py - 4
                    if ly < 2:
                        ly = 2
                    if 2 <= px < 50 and 2 <= ly < 60:
                        self.display.draw_text_small(px, ly, "P", P_BRIGHT)

            if self.s_rays:
                mid_s = self.s_rays[len(self.s_rays) // 2]
                s_idx = int(wt * 0.55)
                if s_idx >= len(mid_s):
                    s_idx = len(mid_s) - 1
                if 0 < s_idx < len(mid_s):
                    sx2, sy2 = mid_s[s_idx]
                    ly = sy2 - 4
                    if ly < 2:
                        ly = 2
                    if 2 <= sx2 < 50 and 2 <= ly < 60:
                        self.display.draw_text_small(sx2, ly, "S", S_BRIGHT)

        if focus == "REFLECT" and self.propagating and wt > 10:
            self.display.draw_text_small(2, 2, "PcP", (80, 200, 120))

        # Overlay
        if self.overlay_timer > 0 and self.overlay_lines:
            alpha = self.overlay_timer / 0.5
            if alpha > 1.0:
                alpha = 1.0
            c = int(255 * alpha)
            for i, line in enumerate(self.overlay_lines):
                self.display.draw_text_small(2, 2 + i * 8, line, (c, c, c))
