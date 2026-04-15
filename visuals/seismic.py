"""
Seismic - Earthquake Wave Propagation
======================================
Earthquake generates P-waves (fast, compressional) and S-waves (slower,
shear) that propagate through Earth's layered interior.  Waves refract
at layer boundaries via Snell's law.  S-waves are blocked by the liquid
outer core, creating a shadow zone -- literally how we discovered Earth
has a liquid core.

Controls:
  Left/Right  - Aim epicenter cursor on crust
  Up/Down     - Cycle focus mode (WAVES / SHADOW / REFLECT)
  Action      - Trigger quake (at cursor, or cycle positions if neutral)
  Both btns   - Toggle scrolling notes
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

# ── Intro phase durations (seconds) ────────────────────────────
INTRO_DURATIONS = [3.0, 3.0, 3.0, 3.0, 4.0, 2.0]

# ── Layer ring colors (brighter for boundary outlines) ─────────
LAYER_BOUNDARY_COLORS = [
    (255, 240, 180),  # inner core boundary (r=6)
    (220, 180,  60),  # outer core boundary (r=12)
    (180,  70,  40),  # lower mantle boundary (r=22)
    (200, 100,  60),  # upper mantle boundary (r=28)
]

LAYER_BOUNDARY_RADII = [6, 12, 22, 28]

# ── Precomputed layer lookup (2D list) ──────────────────────────
# earth_layer[y][x] = layer index, or -1 if outside earth
# Built once at module load.
_earth_layer = []
# Pre-built pixel lists: only earth-interior pixels (skip ~1200 empty bg pixels)
# Each entry: (x, y, color_waves, color_shadow)
_earth_pixels = []

def _init_earth_tables():
    """Build earth layer and background pixel tables once at import."""
    for y in range(GRID_SIZE):
        row_layer = []
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
                    cw = (int(c[0] * 0.35), int(c[1] * 0.35), int(c[2] * 0.35))
                    cs = (int(c[0] * 0.2), int(c[1] * 0.2), int(c[2] * 0.2))
                    _earth_pixels.append((x, y, cw, cs))
            else:
                row_layer.append(-1)
        _earth_layer.append(row_layer)

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
    category = "science_macro"

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
        self.source_angle = self.SOURCE_ANGLES[0]  # current quake angle

        # Ray data
        self.p_rays = []
        self.s_rays = []
        self.reflect_rays = []

        # Animation
        self.wave_time = 0.0
        self.propagating = False
        self.quake_flash = 0.0

        # Epicenter dot (persists until next quake)
        self.epicenter_pos = None  # (x, y) or None

        # Mode transition
        self.mode_transition = 0.0
        self._prev_focus_idx = 0

        # Auto-trigger / idle
        self.idle_timer = 0.0
        self.auto_mode_timer = 0.0
        self.auto_quake_timer = 0.0
        self._idle_active = False

        # Overlay
        self.overlay_timer = 0.0
        self.overlay_lines = []

        # Cached shadow zone
        self._shadow_pixels = []
        self._shadow_valid = False

        # Shadow zone narrative
        self._shadow_quake_count = 0  # quakes fired in SHADOW mode

        # Interactive cursor
        self._cursor_angle = None    # None = no joystick input
        self._cursor_pulse = 0.0

        # Button hint
        self._btn_hint_timer = 3.0   # show after 3s idle
        self._btn_hint_shown = False

        # Scrolling notes
        self.show_notes = False
        self.notes_scroll_offset = 0.0
        self.notes_segments = []
        self.notes_scroll_len = 1
        self._both_pressed_prev = False

        # Intro sequence
        self.intro_phase = 0         # 0..5 = intro phases, -1 = normal
        self._intro_timer = 0.0
        self._intro_p_rays = []
        self._intro_s_rays = []
        self._intro_wave_time = 0.0
        self._intro_max_ray_len = 0

        self._build_notes_segments()

        # Don't trigger quake during intro
        # (intro will trigger its own in phase 2)

    # ── Notes (scrolling info bar) ──────────────────────────────

    def _build_notes_segments(self):
        sep = '  --  '
        sep_color = (60, 55, 50)
        notes = [
            ("SEISMIC WAVES", (255, 255, 255)),
            ("P-WAVES: COMPRESSION", P_COLOR),
            ("S-WAVES: SHEAR", S_COLOR),
            ("LIQUID CORE BLOCKS S", (200, 50, 50)),
            ("INGE LEHMANN 1936", (255, 255, 255)),
        ]
        segments = []
        px_off = 0
        for i, (text, color) in enumerate(notes):
            if i > 0:
                segments.append((px_off, sep, sep_color))
                px_off += len(sep) * 4
            segments.append((px_off, text, color))
            px_off += len(text) * 4
        segments.append((px_off, sep, sep_color))
        px_off += len(sep) * 4
        self.notes_segments = segments
        self.notes_scroll_len = px_off

    def _draw_notes(self):
        d = self.display
        scroll_x = int(self.notes_scroll_offset) % self.notes_scroll_len
        for copy in (0, self.notes_scroll_len):
            for seg_off, text, color in self.notes_segments:
                px = 2 + seg_off + copy - scroll_x
                text_w = len(text) * 4
                if px + text_w < 0 or px > 64:
                    continue
                d.draw_text_small(px, 58, text, color)

    # ── Source / quake helpers ──────────────────────────────────

    def _get_source_pos(self):
        """Get earthquake source (x, y) on the crust surface."""
        angle = self.source_angle
        r = R_EARTH - 1.5  # just inside crust
        return CX + r * math.cos(angle), CY + r * math.sin(angle)

    def _trigger_quake(self):
        """Launch seismic rays from the current source position."""
        sx, sy = self._get_source_pos()

        # Store epicenter for persistent dot
        self.epicenter_pos = (int(sx), int(sy))

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
        self.auto_quake_timer = 0.0
        self.auto_mode_timer = 0.0
        self._idle_active = False

        # Track shadow quake count
        if FOCUS_MODES[self.focus_idx] == "SHADOW":
            self._shadow_quake_count += 1

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
            self.source_angle)) % 360

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

    # ── Intro sequence ──────────────────────────────────────────

    def _update_intro(self, dt):
        """Update intro sequence. Returns True if still in intro."""
        if self.intro_phase < 0:
            return False

        self._intro_timer += dt

        # Check if current phase is done
        if self._intro_timer >= INTRO_DURATIONS[self.intro_phase]:
            self._intro_timer = 0.0
            self.intro_phase += 1

            if self.intro_phase == 2:
                # Trigger first quake for P-wave demo
                self.source_angle = -math.pi / 2  # top
                self._trigger_intro_quake()
            elif self.intro_phase == 3:
                # Same quake continues, S-waves now visible
                pass
            elif self.intro_phase == 4:
                # Same quake continues, watch S block
                pass
            elif self.intro_phase >= len(INTRO_DURATIONS):
                # Intro done, hand off to normal mode
                self.intro_phase = -1
                self.source_angle = self.SOURCE_ANGLES[0]
                self._trigger_quake()
                return False

        # Animate intro wave propagation in phases 2-5
        if self.intro_phase >= 2 and self._intro_p_rays:
            self._intro_wave_time += dt * self.speed * 80.0

        return True

    def _trigger_intro_quake(self):
        """Launch intro-specific rays (reuses main ray tracing)."""
        angle = self.source_angle
        r = R_EARTH - 1.5
        sx = CX + r * math.cos(angle)
        sy = CY + r * math.sin(angle)
        src_angle = math.atan2(sy - CY, sx - CX)
        inward = src_angle + math.pi
        half_fan = math.radians(80)

        self._intro_p_rays = []
        self._intro_s_rays = []
        self._intro_wave_time = 0.0
        self._intro_max_ray_len = 0

        for i in range(NUM_RAYS):
            t = i / (NUM_RAYS - 1)
            ray_angle = inward - half_fan + t * 2 * half_fan
            p_path = _trace_ray(sx, sy, ray_angle, 'P')
            s_path = _trace_ray(sx, sy, ray_angle, 'S')
            if len(p_path) > 2:
                self._intro_p_rays.append(p_path)
            if len(s_path) > 2:
                self._intro_s_rays.append(s_path)

        for path in self._intro_p_rays:
            if len(path) > self._intro_max_ray_len:
                self._intro_max_ray_len = len(path)
        for path in self._intro_s_rays:
            if len(path) > self._intro_max_ray_len:
                self._intro_max_ray_len = len(path)

        # Flash
        self.quake_flash = 0.3
        self.epicenter_pos = (int(sx), int(sy))

    def _draw_intro(self):
        """Draw intro sequence frames."""
        d = self.display
        d.clear()
        set_pixel = d.set_pixel
        phase = self.intro_phase
        t = self._intro_timer

        if phase < 0:
            return

        # Phases 0-1: Earth cross-section with layers
        if phase <= 1:
            self._draw_intro_earth(d, set_pixel, phase, t)
            return

        # Phases 2-5: Draw full earth + propagating waves
        # Draw earth background
        for x, y, cw, cs in _earth_pixels:
            set_pixel(x, y, cw)

        # Draw layer boundary rings
        self._draw_boundary_rings(set_pixel)

        # Draw earth outline
        self._draw_earth_outline(set_pixel)

        wt = self._intro_wave_time

        # Phase 2: P-waves only
        if phase == 2:
            self._draw_rays(self._intro_p_rays, wt, P_COLOR, P_BRIGHT)
            # Quake flash
            self._draw_quake_flash(set_pixel)
            # Epicenter dot
            self._draw_epicenter_dot(set_pixel)
            # Label
            alpha = min(1.0, t / 0.5)
            c = int(255 * alpha)
            d.draw_text_small(2, 2, "P-WAVE: FAST", (int(P_COLOR[0] * alpha),
                int(P_COLOR[1] * alpha), int(P_COLOR[2] * alpha)))

        # Phase 3: P + S waves
        elif phase == 3:
            self._draw_rays(self._intro_p_rays, wt, P_COLOR, P_BRIGHT)
            s_wt = wt * 0.55
            self._draw_rays(self._intro_s_rays, s_wt, S_COLOR, S_BRIGHT)
            self._draw_epicenter_dot(set_pixel)
            alpha = min(1.0, t / 0.5)
            d.draw_text_small(2, 2, "S-WAVE: SLOW", (int(S_COLOR[0] * alpha),
                int(S_COLOR[1] * alpha), int(S_COLOR[2] * alpha)))

        # Phase 4: S-waves blocked by outer core
        elif phase == 4:
            self._draw_rays(self._intro_p_rays, wt, P_COLOR, P_BRIGHT)
            s_wt = wt * 0.55
            self._draw_rays(self._intro_s_rays, s_wt, S_COLOR, S_BRIGHT)
            self._draw_epicenter_dot(set_pixel)

            # Highlight outer core boundary pulsing
            pulse = 0.5 + 0.5 * math.sin(self.time * 4.0)
            oc_r = 12
            for deg in range(360):
                rad = math.radians(deg)
                px = int(CX + oc_r * math.cos(rad))
                py = int(CY + oc_r * math.sin(rad))
                if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                    bright = int(120 + 135 * pulse)
                    set_pixel(px, py, (bright, int(bright * 0.4), 0))

            alpha = min(1.0, t / 0.5)
            c = int(200 * alpha)
            d.draw_text_small(2, 2, "LIQUID BLOCKS S", (c, int(c * 0.3), int(c * 0.3)))

        # Phase 5: full view, handoff
        elif phase == 5:
            self._draw_rays(self._intro_p_rays, wt, P_COLOR, P_BRIGHT)
            s_wt = wt * 0.55
            self._draw_rays(self._intro_s_rays, s_wt, S_COLOR, S_BRIGHT)
            self._draw_epicenter_dot(set_pixel)

            alpha = min(1.0, t / 0.3)
            c = int(200 * alpha)
            d.draw_text_small(2, 56, "BTN: QUAKE", (c, c, int(c * 0.6)))

    def _draw_intro_earth(self, d, set_pixel, phase, t):
        """Draw earth cross-section for intro phases 0-1."""
        # Phase 0: layers light up one at a time from inside out
        # Phase 1: layer names flash one at a time

        # Layer info for intro: (name, r_inner, r_outer, color, label, label_y)
        intro_layers = [
            ("INNER CORE", 0,  6, (240, 220, 140), 30),
            ("OUTER CORE", 6, 12, (200, 160,  40), 22),
            ("MANTLE",    12, 22, (160,  50,  30), 14),
            ("CRUST",     28, 30, (160, 120,  80),  4),
        ]

        # Calculate which layers to show
        if phase == 0:
            # Progressive reveal: each layer lights up over 3 seconds
            # 4 layers in 3 seconds = ~0.75s each
            num_lit = min(4, int(t / 0.7) + 1)
            active_label = -1
        else:
            # Phase 1: all layers visible, labels flash one at a time
            num_lit = 4
            active_label = min(3, int(t / 0.7))

        # Draw earth layers
        for x, y, cw, cs in _earth_pixels:
            dx = x - CX
            dy = y - CY
            r = math.sqrt(dx * dx + dy * dy)
            layer_idx = _earth_layer[y][x]
            if layer_idx < 0:
                continue
            # Map layer_idx (0=inner_core..4=crust) to intro_layers index
            if layer_idx == 0:
                intro_idx = 0
            elif layer_idx == 1:
                intro_idx = 1
            elif layer_idx in (2, 3):
                intro_idx = 2  # mantle (lower + upper)
            else:
                intro_idx = 3  # crust

            if intro_idx < num_lit:
                # Lit: use wave color, with optional pulse for active label
                brightness = 0.35
                if phase == 1 and intro_idx == active_label:
                    pulse = 0.5 + 0.5 * math.sin(self.time * 8.0)
                    brightness = 0.35 + 0.35 * pulse
                c = LAYERS[layer_idx][3]
                set_pixel(x, y, (int(c[0] * brightness),
                                 int(c[1] * brightness),
                                 int(c[2] * brightness)))
            else:
                # Not yet lit: very dim
                c = LAYERS[layer_idx][3]
                set_pixel(x, y, (int(c[0] * 0.08),
                                 int(c[1] * 0.08),
                                 int(c[2] * 0.08)))

        # Draw earth outline
        self._draw_earth_outline(set_pixel)
        # Draw boundary rings
        self._draw_boundary_rings(set_pixel)

        if phase == 0:
            # Label at bottom
            d.draw_text_small(2, 56, "EARTH'S INTERIOR", (180, 180, 140))
        else:
            # Phase 1: show active layer name near its position
            if 0 <= active_label < len(intro_layers):
                name, _, _, color, label_y = intro_layers[active_label]
                alpha = min(1.0, (t - active_label * 0.7) / 0.3)
                if alpha < 0:
                    alpha = 0
                c = (int(color[0] * alpha), int(color[1] * alpha),
                     int(color[2] * alpha))
                # Center text roughly
                text_w = len(name) * 4
                tx = max(2, (64 - text_w) // 2)
                d.draw_text_small(tx, label_y, name, c)

    # ── Input ───────────────────────────────────────────────────

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Any input resets idle timer
        any_input = (input_state.action_l or input_state.action_r or
                     input_state.up_pressed or input_state.down_pressed or
                     input_state.left_pressed or input_state.right_pressed or
                     input_state.left or input_state.right or
                     input_state.up or input_state.down)
        if any_input:
            self.idle_timer = 0.0
            self.auto_quake_timer = 0.0
            self.auto_mode_timer = 0.0
            self._idle_active = False

        # Intro: any button press skips to normal mode
        if self.intro_phase >= 0:
            if input_state.action_l or input_state.action_r:
                self.intro_phase = -1
                self.source_angle = self.SOURCE_ANGLES[0]
                self._trigger_quake()
                return True
            return False

        # Both buttons: toggle notes
        both = input_state.action_l and input_state.action_r
        if both and not self._both_pressed_prev:
            self.show_notes = not self.show_notes
            self.notes_scroll_offset = 0.0
            if self.show_notes:
                self._build_notes_segments()
            consumed = True
            self._both_pressed_prev = both
            return consumed

        # Single action: trigger quake
        if not both and (input_state.action_l or input_state.action_r):
            self._btn_hint_shown = True
            if self._cursor_angle is not None:
                # Fire from cursor position
                self.source_angle = self._cursor_angle
            else:
                # Cycle through SOURCE_ANGLES
                self.source_idx = (self.source_idx + 1) % len(self.SOURCE_ANGLES)
                self.source_angle = self.SOURCE_ANGLES[self.source_idx]
            self._trigger_quake()
            consumed = True

        self._both_pressed_prev = both

        # Up/Down: cycle focus mode
        if input_state.up_pressed:
            self._prev_focus_idx = self.focus_idx
            self.focus_idx = (self.focus_idx - 1) % len(FOCUS_MODES)
            self.mode_transition = 0.5
            # Reset shadow count when entering shadow mode
            if FOCUS_MODES[self.focus_idx] == "SHADOW":
                self._shadow_quake_count = 0
            consumed = True
        if input_state.down_pressed:
            self._prev_focus_idx = self.focus_idx
            self.focus_idx = (self.focus_idx + 1) % len(FOCUS_MODES)
            self.mode_transition = 0.5
            if FOCUS_MODES[self.focus_idx] == "SHADOW":
                self._shadow_quake_count = 0
            consumed = True

        # Left/Right: aim epicenter cursor
        if input_state.left or input_state.right:
            # Map joystick to angle on crust
            dx = 0.0
            dy = 0.0
            if input_state.left:
                dx -= 1.0
            if input_state.right:
                dx += 1.0
            if input_state.up:
                dy -= 1.0
            if input_state.down:
                dy += 1.0

            if abs(dx) > 0.01 or abs(dy) > 0.01:
                target = math.atan2(dy, dx)
                if self._cursor_angle is None:
                    self._cursor_angle = target
                else:
                    # Smooth approach
                    diff = target - self._cursor_angle
                    while diff > math.pi:
                        diff -= 2 * math.pi
                    while diff < -math.pi:
                        diff += 2 * math.pi
                    self._cursor_angle += diff * 0.15
            consumed = True
        elif input_state.up or input_state.down:
            # Vertical joystick also moves cursor
            dy = 0.0
            if input_state.up:
                dy -= 1.0
            if input_state.down:
                dy += 1.0
            if abs(dy) > 0.01:
                target = math.atan2(dy, 0.0)
                if self._cursor_angle is None:
                    self._cursor_angle = target
                else:
                    diff = target - self._cursor_angle
                    while diff > math.pi:
                        diff -= 2 * math.pi
                    while diff < -math.pi:
                        diff += 2 * math.pi
                    self._cursor_angle += diff * 0.15
            # Don't consume - up/down also cycles mode on press
        else:
            # No joystick held: clear cursor (but keep angle for next press)
            pass

        return consumed

    # ── Update ──────────────────────────────────────────────────

    def update(self, dt: float):
        super().update(dt)

        # Intro sequence
        if self._update_intro(dt):
            # Still in intro - only update flash
            if self.quake_flash > 0:
                self.quake_flash -= dt
            return

        # Overlay fade
        if self.overlay_timer > 0:
            self.overlay_timer -= dt

        # Quake flash
        if self.quake_flash > 0:
            self.quake_flash -= dt

        # Mode transition fade
        if self.mode_transition > 0:
            self.mode_transition -= dt
            if self.mode_transition < 0:
                self.mode_transition = 0

        # Wave propagation
        if self.propagating:
            self.wave_time += dt * self.speed * 80.0  # steps per second

            if self.wave_time > self._max_ray_len + 60:
                self.propagating = False

        # Cursor pulse
        self._cursor_pulse += dt * 4.0

        # Button hint timer
        if not self._btn_hint_shown:
            if self._btn_hint_timer > 0:
                self._btn_hint_timer -= dt

        # Notes scrolling
        if self.show_notes:
            self.notes_scroll_offset += dt * 18

        # Idle / auto-advance
        self.idle_timer += dt
        if self.idle_timer >= 20.0:
            self._idle_active = True

        if self._idle_active:
            # Auto-trigger quakes every 8s
            self.auto_quake_timer += dt
            if self.auto_quake_timer >= 8.0:
                self.auto_quake_timer = 0.0
                self.source_idx = (self.source_idx + 1) % len(self.SOURCE_ANGLES)
                self.source_angle = self.SOURCE_ANGLES[self.source_idx]
                self._trigger_quake()
                # Keep idle active
                self._idle_active = True
                self.idle_timer = 20.0

            # Auto-cycle modes every 12s
            self.auto_mode_timer += dt
            if self.auto_mode_timer >= 12.0:
                self.auto_mode_timer = 0.0
                self._prev_focus_idx = self.focus_idx
                self.focus_idx = (self.focus_idx + 1) % len(FOCUS_MODES)
                self.mode_transition = 0.5
        elif not self.propagating:
            # Only auto-trigger if idle for 6s (old behavior as fallback)
            if self.idle_timer > 6.0 and not self._idle_active:
                self.source_idx = (self.source_idx + 1) % len(self.SOURCE_ANGLES)
                self.source_angle = self.SOURCE_ANGLES[self.source_idx]
                self._trigger_quake()

    # ── Drawing helpers ─────────────────────────────────────────

    def _draw_earth_outline(self, set_pixel):
        """Draw a 1px bright outline circle at R_EARTH."""
        for deg in range(360):
            rad = math.radians(deg)
            px = int(CX + R_EARTH * math.cos(rad))
            py = int(CY + R_EARTH * math.sin(rad))
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                set_pixel(px, py, (100, 90, 70))

    def _draw_boundary_rings(self, set_pixel):
        """Draw brighter 1px rings at each major layer boundary."""
        for i, radius in enumerate(LAYER_BOUNDARY_RADII):
            color = LAYER_BOUNDARY_COLORS[i]
            dim = (color[0] // 4, color[1] // 4, color[2] // 4)
            for deg in range(0, 360, 2):  # every other degree for subtlety
                rad = math.radians(deg)
                px = int(CX + radius * math.cos(rad))
                py = int(CY + radius * math.sin(rad))
                if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                    set_pixel(px, py, dim)

    def _draw_epicenter_dot(self, set_pixel):
        """Draw persistent bright dot at epicenter."""
        if self.epicenter_pos is None:
            return
        ex, ey = self.epicenter_pos
        if 0 <= ex < GRID_SIZE and 0 <= ey < GRID_SIZE:
            set_pixel(ex, ey, (255, 255, 200))
        # Small cross for visibility
        for ddx, ddy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = ex + ddx, ey + ddy
            if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                set_pixel(nx, ny, (180, 180, 140))

    def _draw_quake_flash(self, set_pixel):
        """Draw quake flash at epicenter."""
        if self.quake_flash <= 0:
            return
        if self.epicenter_pos is None:
            return
        isx, isy = self.epicenter_pos
        flash_r = int(3 * self.quake_flash / 0.3)
        bright = self.quake_flash / 0.15
        if bright > 1.0:
            bright = 1.0
        fr = int(255 * bright)
        fg = int(255 * bright)
        fb = int(200 * bright)
        for dy in range(-flash_r, flash_r + 1):
            for dx in range(-flash_r, flash_r + 1):
                if dx * dx + dy * dy <= flash_r * flash_r:
                    fx, fy = isx + dx, isy + dy
                    if 0 <= fx < GRID_SIZE and 0 <= fy < GRID_SIZE:
                        set_pixel(fx, fy, (fr, fg, fb))

    def _draw_cursor(self, set_pixel):
        """Draw pulsing dot on crust at cursor angle."""
        if self._cursor_angle is None:
            return
        if self.propagating:
            return  # Don't show cursor during propagation

        r = R_EARTH - 1.5
        cx = CX + r * math.cos(self._cursor_angle)
        cy = CY + r * math.sin(self._cursor_angle)
        ix, iy = int(cx), int(cy)

        pulse = 0.5 + 0.5 * math.sin(self._cursor_pulse)
        bright = int(150 + 105 * pulse)
        if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
            set_pixel(ix, iy, (bright, bright, int(bright * 0.7)))
        # Small halo
        for ddx, ddy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = ix + ddx, iy + ddy
            if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                dim = int(bright * 0.4)
                set_pixel(nx, ny, (dim, dim, int(dim * 0.7)))

    def _draw_rays(self, rays, wt, base_color, bright_color, dim_factor=1.0):
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
                        int(br + dr * t * dim_factor),
                        int(bg + dg * t * dim_factor),
                        int(bb + db * t * dim_factor),
                    ))
                else:
                    fade = 1.0 - (dist_from_front - wavefront_width) / 80.0
                    if fade < 0.15:
                        fade = 0.15
                    set_pixel(ix, iy, (
                        int(br * fade * dim_factor),
                        int(bg * fade * dim_factor),
                        int(bb * fade * dim_factor),
                    ))

    def _draw_hud(self):
        """Draw persistent bottom HUD with legend and mode name."""
        d = self.display

        # Bottom bar background (subtle)
        for x in range(64):
            for y in range(56, 64):
                if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                    cur = d.get_pixel(x, y)
                    # Darken existing pixels in HUD area
                    d.set_pixel(x, y, (cur[0] // 3, cur[1] // 3, cur[2] // 3))

        # P-wave legend: cyan dot + "P"
        d.set_pixel(2, 58, P_COLOR)
        d.set_pixel(2, 59, P_COLOR)
        d.set_pixel(3, 58, P_COLOR)
        d.set_pixel(3, 59, P_COLOR)
        d.draw_text_small(5, 57, "P", P_COLOR)

        # S-wave legend: red-orange dot + "S"
        d.set_pixel(14, 58, S_COLOR)
        d.set_pixel(14, 59, S_COLOR)
        d.set_pixel(15, 58, S_COLOR)
        d.set_pixel(15, 59, S_COLOR)
        d.draw_text_small(17, 57, "S", S_COLOR)

        # Mode name on right
        mode = FOCUS_MODES[self.focus_idx]
        text_w = len(mode) * 4
        mx = 62 - text_w
        d.draw_text_small(mx, 57, mode, (100, 100, 100))

        # Button hint (fades in after 3s idle, disappears after first press)
        if not self._btn_hint_shown and self._btn_hint_timer <= 0:
            # Gentle pulse
            pulse = 0.5 + 0.5 * math.sin(self.time * 2.0)
            c = int(120 + 60 * pulse)
            d.draw_text_small(24, 57, "BTN:QUAKE", (c, c, int(c * 0.6)))

    # ── Shadow zone narrative ───────────────────────────────────

    def _draw_shadow_narrative(self, wt):
        """Progressive shadow zone reveal in SHADOW mode."""
        d = self.display
        set_pixel = d.set_pixel

        if self._max_ray_len <= 0:
            return

        progress = wt / self._max_ray_len

        # Reveal thresholds depend on how many quakes we've seen in SHADOW mode
        if self._shadow_quake_count <= 1:
            question_at = 0.6
            highlight_at = 0.8
            answer_at = 1.0
        else:
            question_at = 0.4
            highlight_at = 0.55
            answer_at = 0.7

        if progress >= question_at and progress < answer_at:
            # "WHERE ARE THE S?" text
            alpha = min(1.0, (progress - question_at) / 0.1)
            c = int(200 * alpha)
            d.draw_text_small(2, 2, "WHERE ARE THE S?", (c, int(c * 0.4), int(c * 0.4)))

        if progress >= highlight_at:
            # Highlight shadow zone with pulsing red
            shadow_pixels = self._compute_shadow_zone()
            pulse = 0.5 + 0.5 * math.sin(self.time * 4.0)
            intensity = min(1.0, (progress - highlight_at) / 0.1)
            sc_mul = (0.5 + 0.5 * pulse) * intensity
            sc = (int(SHADOW_COLOR[0] * sc_mul * 2),
                  int(min(255, SHADOW_COLOR[1] * sc_mul * 2)),
                  int(SHADOW_COLOR[2] * sc_mul * 2))
            for px, py in shadow_pixels:
                set_pixel(px, py, sc)

        if progress >= answer_at:
            # Replace question with answer
            alpha = min(1.0, (progress - answer_at) / 0.1)
            c = int(220 * alpha)
            d.draw_text_small(2, 2, "BLOCKED BY LIQUID", (c, int(c * 0.3), int(c * 0.3)))

    # ── Main draw ───────────────────────────────────────────────

    def draw(self):
        # Intro sequence
        if self.intro_phase >= 0:
            self._draw_intro()
            return

        self.display.clear()

        focus = FOCUS_MODES[self.focus_idx]
        set_pixel = self.display.set_pixel

        # Draw earth background -- only interior pixels (~2800 vs 4096)
        shadow = focus == "SHADOW"
        for x, y, cw, cs in _earth_pixels:
            set_pixel(x, y, cs if shadow else cw)

        # Draw boundary rings and outline
        self._draw_boundary_rings(set_pixel)
        self._draw_earth_outline(set_pixel)

        wt = self.wave_time

        # Mode transition dimming
        transition_dim = 1.0
        if self.mode_transition > 0:
            # Fade from 0.3 to 1.0 over the transition period
            transition_dim = 1.0 - 0.7 * (self.mode_transition / 0.5)
            if transition_dim < 0.3:
                transition_dim = 0.3

        if focus == "WAVES" or focus == "SHADOW":
            # Draw P-wave rays
            self._draw_rays(self.p_rays, wt, P_COLOR, P_BRIGHT, transition_dim)

            # Draw S-wave rays (slower)
            s_wt = wt * 0.55
            self._draw_rays(self.s_rays, s_wt, S_COLOR, S_BRIGHT, transition_dim)

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
                            int((80 + 170 * t) * transition_dim),
                            int((200 + 55 * t) * transition_dim),
                            int((120 + 135 * t) * transition_dim),
                        ))
                    else:
                        fade = 1.0 - (dist_from_front - wavefront_width) / 80.0
                        if fade < 0.15:
                            fade = 0.15
                        set_pixel(ix, iy, (
                            int(80 * fade * transition_dim),
                            int(200 * fade * transition_dim),
                            int(120 * fade * transition_dim),
                        ))

        # Shadow zone narrative reveal
        if focus == "SHADOW" and self.propagating:
            self._draw_shadow_narrative(wt)
        elif focus == "SHADOW" and not self.propagating and wt > 0:
            # After propagation done, show final shadow state
            shadow_pixels = self._compute_shadow_zone()
            pulse = 0.5 + 0.5 * math.sin(self.time * 3.0)
            sc_mul = 0.5 + 0.5 * pulse
            sc = (int(SHADOW_COLOR[0] * sc_mul),
                  int(SHADOW_COLOR[1] * sc_mul),
                  int(SHADOW_COLOR[2] * sc_mul))
            for px, py in shadow_pixels:
                set_pixel(px, py, sc)
            self.display.draw_text_small(2, 2, "BLOCKED BY LIQUID",
                                         (180, 50, 50))

        # Quake flash
        self._draw_quake_flash(set_pixel)

        # Epicenter dot (persistent)
        self._draw_epicenter_dot(set_pixel)

        # Cursor
        self._draw_cursor(set_pixel)

        # Reflect mode label
        if focus == "REFLECT" and self.propagating and wt > 10:
            self.display.draw_text_small(2, 2, "PcP", (80, 200, 120))

        # Persistent HUD
        if not self.show_notes:
            self._draw_hud()

        # Scrolling notes (replaces HUD when active)
        if self.show_notes:
            self._draw_notes()
