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
NUM_RAYS = 50
RAY_STEP = 0.15         # spatial step per iteration
MAX_RAY_STEPS = 600     # prevent infinite loops

# ── Focus modes ─────────────────────────────────────────────────
FOCUS_MODES = ["WAVES", "SHADOW", "REFLECT"]

# ── Colors ──────────────────────────────────────────────────────
P_COLOR = (80, 180, 255)     # cyan-blue
P_BRIGHT = (140, 220, 255)
S_COLOR = (255, 100, 50)     # red-orange
S_BRIGHT = (255, 180, 100)
SHADOW_COLOR = (120, 20, 20) # dim red arc for shadow zone


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
    Returns list of (x, y) points along the ray path.
    """
    path = []
    x, y = source_x, source_y
    dx = math.cos(angle)
    dy = math.sin(angle)

    speed_idx = 4 if wave_type == 'P' else 5

    for _ in range(MAX_RAY_STEPS):
        path.append((x, y))

        # Current radius
        rx, ry = x - CX, y - CY
        r = math.sqrt(rx * rx + ry * ry)

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
        nr = math.sqrt(nrx * nrx + nry * nry)

        new_layer_idx = _get_layer(nr)

        # If we crossed a layer boundary, apply Snell's law
        if new_layer_idx != layer_idx and new_layer_idx >= 0:
            new_speed = LAYERS[new_layer_idx][speed_idx]

            # S-wave entering outer core
            if wave_type == 'S' and LAYERS[new_layer_idx][0] == "outer_core":
                path.append((nx, ny))
                break

            if new_speed <= 0:
                break

            # Normal at boundary = radial direction
            if r > 0.01:
                norm_x, norm_y = rx / r, ry / r
            else:
                norm_x, norm_y = 0.0, -1.0

            # Angle of incidence (between ray and inward normal)
            # Ensure normal points in the direction the ray is crossing
            dot = dx * norm_x + dy * norm_y
            if dot > 0:
                norm_x, norm_y = -norm_x, -norm_y
                dot = -dot

            sin_i = math.sqrt(max(0, 1.0 - dot * dot))
            ratio = new_speed / current_speed

            sin_r = sin_i * ratio

            if sin_r >= 1.0:
                # Total internal reflection
                dot_r = dx * norm_x + dy * norm_y
                dx = dx - 2 * dot_r * norm_x
                dy = dy - 2 * dot_r * norm_y
                mag = math.sqrt(dx * dx + dy * dy)
                if mag > 0:
                    dx /= mag
                    dy /= mag
            else:
                # Snell's law refraction
                cos_r = math.sqrt(max(0, 1.0 - sin_r * sin_r))

                # Tangent direction (perpendicular to normal, in plane of incidence)
                tan_x = dx - dot * norm_x
                tan_y = dy - dot * norm_y
                tan_mag = math.sqrt(tan_x * tan_x + tan_y * tan_y)
                if tan_mag > 0.001:
                    tan_x /= tan_mag
                    tan_y /= tan_mag
                    # New direction
                    dx = sin_r * tan_x + cos_r * norm_x
                    dy = sin_r * tan_y + cos_r * norm_y
                else:
                    # Head-on, no refraction needed
                    pass

                mag = math.sqrt(dx * dx + dy * dy)
                if mag > 0:
                    dx /= mag
                    dy /= mag

        x, y = nx, ny

    return path


def _trace_reflected_ray(source_x, source_y, angle, wave_type, reflect_layer_name):
    """Trace a ray that reflects off a specific layer boundary.

    Used for REFLECT mode to show PcP, ScS, PKP type waves.
    """
    path = []
    x, y = source_x, source_y
    dx = math.cos(angle)
    dy = math.sin(angle)
    speed_idx = 4 if wave_type == 'P' else 5
    reflected = False

    for _ in range(MAX_RAY_STEPS):
        path.append((x, y))

        rx, ry = x - CX, y - CY
        r = math.sqrt(rx * rx + ry * ry)

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
        nr = math.sqrt(nrx * nrx + nry * nry)
        new_layer_idx = _get_layer(nr)

        # Reflect at target boundary
        if not reflected and new_layer_idx != layer_idx and new_layer_idx >= 0:
            if LAYERS[new_layer_idx][0] == reflect_layer_name:
                # Reflect
                if r > 0.01:
                    norm_x, norm_y = rx / r, ry / r
                else:
                    norm_x, norm_y = 0.0, -1.0
                dot = dx * norm_x + dy * norm_y
                dx = dx - 2 * dot * norm_x
                dy = dy - 2 * dot * norm_y
                mag = math.sqrt(dx * dx + dy * dy)
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
                sin_i = math.sqrt(max(0, 1.0 - dot * dot))
                ratio = new_speed / current_speed
                sin_r = sin_i * ratio
                if sin_r < 1.0:
                    cos_r = math.sqrt(max(0, 1.0 - sin_r * sin_r))
                    tan_x = dx - dot * norm_x
                    tan_y = dy - dot * norm_y
                    tan_mag = math.sqrt(tan_x * tan_x + tan_y * tan_y)
                    if tan_mag > 0.001:
                        tan_x /= tan_mag
                        tan_y /= tan_mag
                        dx = sin_r * tan_x + cos_r * norm_x
                        dy = sin_r * tan_y + cos_r * norm_y
                    mag = math.sqrt(dx * dx + dy * dy)
                    if mag > 0:
                        dx /= mag
                        dy /= mag
                else:
                    dot2 = dx * norm_x + dy * norm_y
                    dx = dx - 2 * dot2 * norm_x
                    dy = dy - 2 * dot2 * norm_y
                    mag = math.sqrt(dx * dx + dy * dy)
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

        # Precompute earth pixel map
        self._build_earth_map()

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

        # Trigger initial quake
        self._trigger_quake()

    def _build_earth_map(self):
        """Precompute which pixel belongs to which layer."""
        self.earth_map = {}
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                dx = x - CX
                dy = y - CY
                r = math.sqrt(dx * dx + dy * dy)
                if r < R_EARTH:
                    layer_idx = _get_layer(r)
                    if layer_idx >= 0:
                        self.earth_map[(x, y)] = layer_idx

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

        # PKP: P-waves through the core (already in p_rays, highlight them)

        self.wave_time = 0.0
        self.propagating = True
        self.quake_flash = 0.3
        self.idle_timer = 0.0

    def _compute_shadow_zone(self):
        """Find surface angles where no direct S-waves arrive.

        Returns list of (x, y) pixel positions on the crust that are
        in the shadow zone.
        """
        # Collect angles on the surface where S-wave rays arrived
        s_arrival_angles = set()
        for path in self.s_rays:
            if len(path) < 3:
                continue
            ex, ey = path[-1]
            er = math.sqrt((ex - CX) ** 2 + (ey - CY) ** 2)
            if er >= R_EARTH - 3:
                # Ray reached near surface
                a = math.atan2(ey - CY, ex - CX)
                # Quantize to degrees
                s_arrival_angles.add(int(math.degrees(a)) % 360)

        # Shadow zone: surface pixels where no S-wave arrived
        shadow_pixels = []
        src_angle_deg = int(math.degrees(
            self.SOURCE_ANGLES[self.source_idx])) % 360

        for deg in range(360):
            # Skip near source
            diff = (deg - src_angle_deg + 180) % 360 - 180
            if abs(diff) < 15:
                continue

            if deg not in s_arrival_angles:
                rad = math.radians(deg)
                for r in range(28, 31):
                    px = int(CX + r * math.cos(rad))
                    py = int(CY + r * math.sin(rad))
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        shadow_pixels.append((px, py))

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

            # Check if propagation is done (all rays fully drawn)
            max_len = 0
            for path in self.p_rays:
                max_len = max(max_len, len(path))
            for path in self.s_rays:
                max_len = max(max_len, len(path))

            if self.wave_time > max_len + 60:
                self.propagating = False

        # Auto-trigger
        if not self.propagating:
            self.idle_timer += dt
            if self.idle_timer > 6.0:
                self.source_idx = (self.source_idx + 1) % len(self.SOURCE_ANGLES)
                self._trigger_quake()

    def draw(self):
        self.display.clear()

        focus = FOCUS_MODES[self.focus_idx]

        # Draw background
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if (x, y) in self.earth_map:
                    layer_idx = self.earth_map[(x, y)]
                    color = LAYERS[layer_idx][3]
                    # Dim the earth layers to let waves stand out
                    dim = 0.35
                    if focus == "SHADOW":
                        dim = 0.2
                    color = (int(color[0] * dim), int(color[1] * dim),
                             int(color[2] * dim))
                    self.display.set_pixel(x, y, color)
                else:
                    self.display.set_pixel(x, y, BG_COLOR)

        wt = self.wave_time
        wavefront_width = 8  # pixels of bright front

        if focus == "WAVES" or focus == "SHADOW":
            # Draw P-wave rays
            for path in self.p_rays:
                drawn = int(min(wt, len(path)))
                for j in range(drawn):
                    px, py = path[j]
                    ix, iy = int(round(px)), int(round(py))
                    if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                        # Brightness based on distance from wavefront
                        dist_from_front = drawn - j
                        if dist_from_front < wavefront_width:
                            t = 1.0 - dist_from_front / wavefront_width
                            color = (
                                int(P_COLOR[0] + (P_BRIGHT[0] - P_COLOR[0]) * t),
                                int(P_COLOR[1] + (P_BRIGHT[1] - P_COLOR[1]) * t),
                                int(P_COLOR[2] + (P_BRIGHT[2] - P_COLOR[2]) * t),
                            )
                        else:
                            # Trail fades
                            fade = max(0.15, 1.0 - (dist_from_front - wavefront_width) / 80.0)
                            color = (int(P_COLOR[0] * fade),
                                     int(P_COLOR[1] * fade),
                                     int(P_COLOR[2] * fade))
                        self.display.set_pixel(ix, iy, color)

            # Draw S-wave rays (slower, so use reduced time)
            s_time_factor = 0.55  # S-waves are ~55% speed of P-waves on average
            s_wt = wt * s_time_factor

            for path in self.s_rays:
                drawn = int(min(s_wt, len(path)))
                for j in range(drawn):
                    px, py = path[j]
                    ix, iy = int(round(px)), int(round(py))
                    if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                        dist_from_front = drawn - j
                        if dist_from_front < wavefront_width:
                            t = 1.0 - dist_from_front / wavefront_width
                            color = (
                                int(S_COLOR[0] + (S_BRIGHT[0] - S_COLOR[0]) * t),
                                int(S_COLOR[1] + (S_BRIGHT[1] - S_COLOR[1]) * t),
                                int(S_COLOR[2] + (S_BRIGHT[2] - S_COLOR[2]) * t),
                            )
                        else:
                            fade = max(0.15, 1.0 - (dist_from_front - wavefront_width) / 80.0)
                            color = (int(S_COLOR[0] * fade),
                                     int(S_COLOR[1] * fade),
                                     int(S_COLOR[2] * fade))
                        self.display.set_pixel(ix, iy, color)

        if focus == "REFLECT":
            # Draw reflected rays
            for label, path in self.reflect_rays:
                drawn = int(min(wt * 0.7, len(path)))
                for j in range(drawn):
                    px, py = path[j]
                    ix, iy = int(round(px)), int(round(py))
                    if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                        dist_from_front = drawn - j
                        if dist_from_front < wavefront_width:
                            t = 1.0 - dist_from_front / wavefront_width
                            color = (
                                int(80 + 170 * t),
                                int(200 + 55 * t),
                                int(120 + 135 * t),
                            )
                        else:
                            fade = max(0.15, 1.0 - (dist_from_front - wavefront_width) / 80.0)
                            color = (int(80 * fade), int(200 * fade), int(120 * fade))
                        self.display.set_pixel(ix, iy, color)

        # Shadow zone highlighting
        if focus == "SHADOW" and wt > 100:
            shadow_pixels = self._compute_shadow_zone()
            pulse = 0.5 + 0.5 * math.sin(self.time * 3.0)
            for px, py in shadow_pixels:
                if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                    sc = (int(SHADOW_COLOR[0] * (0.5 + 0.5 * pulse)),
                          int(SHADOW_COLOR[1] * (0.5 + 0.5 * pulse)),
                          int(SHADOW_COLOR[2] * (0.5 + 0.5 * pulse)))
                    self.display.set_pixel(px, py, sc)

            # Label
            self.display.draw_text_small(2, 56, "SHADOW ZONE", (180, 60, 60))

        # Quake flash: bright spot at source
        if self.quake_flash > 0:
            sx, sy = self._get_source_pos()
            flash_r = int(3 * self.quake_flash / 0.3)
            bright = min(1.0, self.quake_flash / 0.15)
            for dy in range(-flash_r, flash_r + 1):
                for dx in range(-flash_r, flash_r + 1):
                    if dx * dx + dy * dy <= flash_r * flash_r:
                        fx, fy = int(sx) + dx, int(sy) + dy
                        if 0 <= fx < GRID_SIZE and 0 <= fy < GRID_SIZE:
                            self.display.set_pixel(fx, fy,
                                (int(255 * bright), int(255 * bright), int(200 * bright)))

        # Wavefront labels
        if focus == "WAVES" and self.propagating and wt > 10:
            # Find P-wave front position (use middle ray)
            if self.p_rays:
                mid_p = self.p_rays[len(self.p_rays) // 2]
                p_idx = int(min(wt, len(mid_p) - 1))
                if 0 < p_idx < len(mid_p):
                    px, py = mid_p[p_idx]
                    lx = int(round(px))
                    ly = max(2, int(round(py)) - 4)
                    if 2 <= lx < 50 and 2 <= ly < 60:
                        self.display.draw_text_small(lx, ly, "P", P_BRIGHT)

            # S-wave label
            if self.s_rays:
                mid_s = self.s_rays[len(self.s_rays) // 2]
                s_idx = int(min(wt * 0.55, len(mid_s) - 1))
                if 0 < s_idx < len(mid_s):
                    sx2, sy2 = mid_s[s_idx]
                    lx = int(round(sx2))
                    ly = max(2, int(round(sy2)) - 4)
                    if 2 <= lx < 50 and 2 <= ly < 60:
                        self.display.draw_text_small(lx, ly, "S", S_BRIGHT)

        if focus == "REFLECT" and self.propagating and wt > 10:
            self.display.draw_text_small(2, 2, "PcP", (80, 200, 120))

        # Overlay
        if self.overlay_timer > 0 and self.overlay_lines:
            alpha = min(1.0, self.overlay_timer / 0.5)
            for i, line in enumerate(self.overlay_lines):
                r = int(255 * alpha)
                g = int(255 * alpha)
                b = int(255 * alpha)
                self.display.draw_text_small(2, 2 + i * 8, line, (r, g, b))
