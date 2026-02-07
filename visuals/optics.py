"""
Optics - Geometric Ray Tracing Visualization
=============================================
2D geometric optics on a 64x64 LED matrix. Rays of light propagate
across the grid, interacting with prisms, lenses, and mirrors via
Snell's law and reflection.

Scenarios: PRISM, LENS, MIRRORS, DOUBLE PRISM, KALEIDOSCOPE

Controls:
  Left/Right     - Adjust beam angle (or kaleidoscope rotation speed)
  Up/Down        - Cycle color palette
  Single button  - Cycle scenario / sub-variant
  Both buttons   - Toggle scrolling notes
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE

# ── Ray tracing parameters ──────────────────────────────────────

RAY_STEP = 0.5
MAX_RAY_STEPS = 200

# ── Spectral colors (ROYGBIV) ──────────────────────────────────

SPECTRUM = [
    {'name': 'RED',    'wavelength': 700, 'color': (255,   0,   0), 'n': 1.510},
    {'name': 'ORANGE', 'wavelength': 620, 'color': (255, 127,   0), 'n': 1.516},
    {'name': 'YELLOW', 'wavelength': 580, 'color': (255, 255,   0), 'n': 1.520},
    {'name': 'GREEN',  'wavelength': 530, 'color': (  0, 255,   0), 'n': 1.525},
    {'name': 'BLUE',   'wavelength': 470, 'color': (  0,   0, 255), 'n': 1.530},
    {'name': 'INDIGO', 'wavelength': 440, 'color': ( 75,   0, 130), 'n': 1.535},
    {'name': 'VIOLET', 'wavelength': 410, 'color': (148,   0, 211), 'n': 1.540},
]

# ── Palettes ────────────────────────────────────────────────────

PALETTES = [
    # Dark: black bg, white elements, full color rays
    {'bg': (0, 0, 0), 'elem': (200, 200, 200), 'fill': (30, 30, 40), 'mono': False},
    # Blueprint: dark blue bg, light blue elements
    {'bg': (5, 5, 25), 'elem': (100, 150, 255), 'fill': (15, 20, 50), 'mono': False},
    # Warm: dark red bg, gold elements
    {'bg': (15, 5, 5), 'elem': (255, 200, 80), 'fill': (40, 20, 15), 'mono': False},
    # Green: dark green bg, bright elements
    {'bg': (5, 15, 5), 'elem': (100, 255, 100), 'fill': (15, 40, 15), 'mono': False},
    # Mono: black bg, gray elements, white rays only
    {'bg': (0, 0, 0), 'elem': (150, 150, 150), 'fill': (25, 25, 25), 'mono': True},
]

# ── Scenarios ───────────────────────────────────────────────────

_SCENARIOS = ['PRISM', 'LENS', 'MIRRORS', 'DOUBLE PRISM', 'KALEIDOSCOPE']


# ── Geometry helpers ────────────────────────────────────────────

def _point_in_triangle(px, py, v0, v1, v2):
    """Check if point (px, py) is inside triangle (v0, v1, v2)."""
    def _sign(p1, p2, p3):
        return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])
    d1 = _sign((px, py), v0, v1)
    d2 = _sign((px, py), v1, v2)
    d3 = _sign((px, py), v2, v0)
    has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
    has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
    return not (has_neg and has_pos)


def _triangle_normal_at_exit(px, py, v0, v1, v2):
    """Find the outward normal of the nearest edge of the triangle."""
    edges = [(v0, v1), (v1, v2), (v2, v0)]
    best_dist = 1e9
    best_nx, best_ny = 0.0, 1.0
    for (ax, ay), (bx, by) in edges:
        # Distance from point to edge
        ex, ey = bx - ax, by - ay
        elen2 = ex * ex + ey * ey
        if elen2 < 0.001:
            continue
        t = max(0.0, min(1.0, ((px - ax) * ex + (py - ay) * ey) / elen2))
        cx, cy = ax + t * ex, ay + t * ey
        dx, dy = px - cx, py - cy
        d = math.sqrt(dx * dx + dy * dy)
        if d < best_dist:
            best_dist = d
            # Normal is perpendicular to edge, pointing outward
            nx, ny = -ey, ex
            nlen = math.sqrt(nx * nx + ny * ny)
            if nlen > 0.001:
                nx /= nlen
                ny /= nlen
            # Ensure normal points outward (away from triangle centroid)
            tcx = (v0[0] + v1[0] + v2[0]) / 3.0
            tcy = (v0[1] + v1[1] + v2[1]) / 3.0
            if nx * (px - tcx) + ny * (py - tcy) < 0:
                nx, ny = -nx, -ny
            best_nx, best_ny = nx, ny
    return best_nx, best_ny


def _reflect(dx, dy, nx, ny):
    """Reflect direction (dx, dy) across normal (nx, ny)."""
    dot = dx * nx + dy * ny
    return dx - 2 * dot * nx, dy - 2 * dot * ny


def _refract(dx, dy, nx, ny, n1, n2):
    """Refract direction through interface. Returns None for total internal reflection."""
    # Ensure normal faces against incoming ray
    cos_i = -(dx * nx + dy * ny)
    if cos_i < 0:
        nx, ny = -nx, -ny
        cos_i = -cos_i
    ratio = n1 / n2
    sin2_t = ratio * ratio * (1.0 - cos_i * cos_i)
    if sin2_t > 1.0:
        return None  # Total internal reflection
    cos_t = math.sqrt(1.0 - sin2_t)
    tx = ratio * dx + (ratio * cos_i - cos_t) * nx
    ty = ratio * dy + (ratio * cos_i - cos_t) * ny
    tlen = math.sqrt(tx * tx + ty * ty)
    if tlen > 0.001:
        tx /= tlen
        ty /= tlen
    return tx, ty


def _dist_to_segment(px, py, x1, y1, x2, y2):
    """Distance from point to line segment."""
    ex, ey = x2 - x1, y2 - y1
    elen2 = ex * ex + ey * ey
    if elen2 < 0.001:
        dx, dy = px - x1, py - y1
        return math.sqrt(dx * dx + dy * dy)
    t = max(0.0, min(1.0, ((px - x1) * ex + (py - y1) * ey) / elen2))
    cx, cy = x1 + t * ex, y1 + t * ey
    dx, dy = px - cx, py - cy
    return math.sqrt(dx * dx + dy * dy)


def _segment_normal(x1, y1, x2, y2):
    """Return unit normal of line segment (one of two directions)."""
    ex, ey = x2 - x1, y2 - y1
    elen = math.sqrt(ex * ex + ey * ey)
    if elen < 0.001:
        return 0.0, 1.0
    return -ey / elen, ex / elen


# ── Optics visual ──────────────────────────────────────────────

class Optics(Visual):
    name = "OPTICS"
    description = "Geometric ray tracing"
    category = "science"

    def __init__(self, display: Display):
        super().__init__(display)

    # ── notes ────────────────────────────────────────────────────

    def _get_notes(self):
        pal = PALETTES[self.palette_idx]
        mid = pal['elem']
        return [
            ("GEOMETRIC OPTICS", (255, 255, 255)),
            ("SNELL'S LAW: N1 SIN A1 = N2 SIN A2", mid),
            ("PRISMS SPLIT LIGHT BY WAVELENGTH", mid),
            ("LENSES FOCUS BY REFRACTION", mid),
            ("ISAAC NEWTON 1704", (255, 255, 255)),
        ]

    def _build_notes_segments(self):
        sep = '  --  '
        sep_color = (60, 55, 50)
        segments = []
        px_off = 0
        for i, (text, color) in enumerate(self._get_notes()):
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

    # ── overlay ──────────────────────────────────────────────────

    def _draw_overlay(self):
        if self.overlay_timer <= 0:
            return
        alpha = min(1.0, self.overlay_timer / 0.5)
        c = (int(255 * alpha), int(255 * alpha), int(255 * alpha))
        self.display.draw_text_small(2, 2, self.overlay_text, c)

    def _show_overlay(self, text):
        self.overlay_text = text
        self.overlay_timer = 2.0

    # ── reset / setup ────────────────────────────────────────────

    def reset(self):
        self.time = 0.0
        self.palette_idx = 0
        self.scenario_idx = 0
        self.sub_variant = 0
        self.overlay_text = ''
        self.overlay_timer = 0.0
        self.show_notes = False
        self.notes_scroll_offset = 0.0
        self.notes_segments = []
        self.notes_scroll_len = 1
        self._both_pressed_prev = False

        # User-controlled angle / speed
        self.user_angle = 0.0            # beam angle offset (radians)
        self.kaleidoscope_speed = 0.15   # rotation speed for kaleidoscope

        # Optical elements
        self.prisms = []
        self.lenses = []
        self.mirrors = []
        self.sources = []  # Ray sources: {'x','y','dx','dy','color','wavelength','n'}

        self._build_notes_segments()
        self._setup_scenario()

    def _setup_scenario(self):
        """Build optical elements and ray sources for the current scenario."""
        self.prisms = []
        self.lenses = []
        self.mirrors = []
        self.sources = []
        self.sub_variant = 0

        scenario = _SCENARIOS[self.scenario_idx]

        if scenario == 'PRISM':
            self._setup_prism()
        elif scenario == 'LENS':
            self._setup_lens()
        elif scenario == 'MIRRORS':
            self._setup_mirrors()
        elif scenario == 'DOUBLE PRISM':
            self._setup_double_prism()
        elif scenario == 'KALEIDOSCOPE':
            self._setup_kaleidoscope()

    def _setup_prism(self):
        """White light -> prism -> rainbow spectrum."""
        cx, cy = 32, 32
        size = 12
        # Equilateral triangle pointing right
        v0 = (cx - size * 0.5, cy - size * 0.58)
        v1 = (cx - size * 0.5, cy + size * 0.58)
        v2 = (cx + size * 0.6, cy)
        self.prisms.append({
            'vertices': [v0, v1, v2],
            'n_base': 1.52,
        })
        # White beam: 7 rays (ROYGBIV), bundled together from left
        for s in SPECTRUM:
            self.sources.append({
                'x': 2.0, 'y': cy, 'dx': 1.0, 'dy': 0.0,
                'color': s['color'], 'wavelength': s['wavelength'], 'n': s['n'],
            })

    def _setup_lens(self):
        """Convex lens focuses parallel rays; concave diverges."""
        # Sub-variant 0 = convex, 1 = concave
        cx = 32
        cy = 32
        self.lenses.append({
            'cx': cx, 'cy': cy, 'radius': 18, 'focal_len': 20.0, 'type': 'convex',
        })
        # Parallel colored rays from left
        colors = [
            (255, 60, 60), (255, 160, 0), (255, 255, 0), (0, 255, 0),
            (0, 180, 255), (100, 60, 255), (200, 0, 255), (255, 100, 100),
            (0, 255, 180), (180, 180, 255),
        ]
        for i in range(10):
            y = 10 + i * 4.4
            self.sources.append({
                'x': 2.0, 'y': y, 'dx': 1.0, 'dy': 0.0,
                'color': colors[i], 'wavelength': 550, 'n': 1.52,
            })

    def _setup_mirrors(self):
        """Two angled flat mirrors, beam bounces between them."""
        # Mirror 1: angled at ~30 deg from horizontal, upper-left
        self.mirrors.append({'x1': 10, 'y1': 15, 'x2': 40, 'y2': 10})
        # Mirror 2: angled, lower-right
        self.mirrors.append({'x1': 25, 'y1': 55, 'x2': 58, 'y2': 35})
        # Single bright beam
        colors = [
            (255, 255, 255), (255, 200, 100), (100, 200, 255),
            (255, 100, 100), (100, 255, 100),
        ]
        for i in range(5):
            self.sources.append({
                'x': 2.0, 'y': 30.0 + i * 1.5, 'dx': 0.9, 'dy': -0.44,
                'color': colors[i], 'wavelength': 550, 'n': 1.0,
            })

    def _setup_double_prism(self):
        """Two prisms: first disperses, second recombines (Newton's experiment)."""
        # First prism - left side
        cx1, cy1 = 18, 32
        size = 9
        v0 = (cx1 - size * 0.5, cy1 - size * 0.58)
        v1 = (cx1 - size * 0.5, cy1 + size * 0.58)
        v2 = (cx1 + size * 0.6, cy1)
        self.prisms.append({'vertices': [v0, v1, v2], 'n_base': 1.52})

        # Second prism - right side, inverted
        cx2, cy2 = 48, 32
        v3 = (cx2 + size * 0.5, cy2 - size * 0.58)
        v4 = (cx2 + size * 0.5, cy2 + size * 0.58)
        v5 = (cx2 - size * 0.6, cy2)
        self.prisms.append({'vertices': [v3, v4, v5], 'n_base': 1.52})

        # White beam from left
        for s in SPECTRUM:
            self.sources.append({
                'x': 2.0, 'y': 32.0, 'dx': 1.0, 'dy': 0.0,
                'color': s['color'], 'wavelength': s['wavelength'], 'n': s['n'],
            })

    def _setup_kaleidoscope(self):
        """Triangular mirror arrangement with colored light sources."""
        cx, cy = 32, 32
        r = 22
        # Three mirrors forming equilateral triangle
        angles = [math.pi / 2, math.pi / 2 + 2 * math.pi / 3, math.pi / 2 + 4 * math.pi / 3]
        verts = [(cx + r * math.cos(a), cy + r * math.sin(a)) for a in angles]
        for i in range(3):
            j = (i + 1) % 3
            self.mirrors.append({
                'x1': verts[i][0], 'y1': verts[i][1],
                'x2': verts[j][0], 'y2': verts[j][1],
            })
        # Colored point sources inside the triangle, radiating outward
        source_colors = [
            (255, 60, 60), (60, 255, 60), (60, 60, 255),
            (255, 255, 0), (0, 255, 255), (255, 0, 255),
        ]
        for i in range(6):
            angle = 2 * math.pi * i / 6
            sx = cx + 3 * math.cos(angle)
            sy = cy + 3 * math.sin(angle)
            for j in range(3):
                a2 = angle + (j - 1) * 0.3
                self.sources.append({
                    'x': sx, 'y': sy,
                    'dx': math.cos(a2), 'dy': math.sin(a2),
                    'color': source_colors[i], 'wavelength': 550, 'n': 1.0,
                })

    # ── ray tracing ──────────────────────────────────────────────

    def _trace_ray(self, src, anim_angle):
        """Trace a single ray and return list of (x, y, r, g, b) pixels."""
        points = []
        x, y = float(src['x']), float(src['y'])
        dx, dy = float(src['dx']), float(src['dy'])
        color = src['color']
        n_glass = src['n']
        in_prism = -1  # Index of prism we're inside, or -1
        mono = PALETTES[self.palette_idx]['mono']
        if mono:
            color = (220, 220, 220)

        # Normalize direction
        dlen = math.sqrt(dx * dx + dy * dy)
        if dlen > 0.001:
            dx /= dlen
            dy /= dlen

        # Apply animation angle offset to initial direction
        if anim_angle != 0.0:
            cos_a = math.cos(anim_angle)
            sin_a = math.sin(anim_angle)
            dx, dy = dx * cos_a - dy * sin_a, dx * sin_a + dy * cos_a

        max_reflections = 12
        reflections = 0

        for step in range(MAX_RAY_STEPS):
            ix, iy = int(x), int(y)
            if ix < 0 or ix >= GRID_SIZE or iy < 0 or iy >= GRID_SIZE:
                break

            # Brightness fades along ray
            fade = max(0.3, 1.0 - step / (MAX_RAY_STEPS * 1.2))
            r = int(color[0] * fade)
            g = int(color[1] * fade)
            b = int(color[2] * fade)
            points.append((ix, iy, r, g, b))

            # Step forward
            nx = x + RAY_STEP * dx
            ny = y + RAY_STEP * dy

            # Check prism interactions
            interacted = False
            for pi, prism in enumerate(self.prisms):
                v = prism['vertices']
                was_inside = _point_in_triangle(x, y, v[0], v[1], v[2])
                now_inside = _point_in_triangle(nx, ny, v[0], v[1], v[2])

                if not was_inside and now_inside:
                    # Entering prism: refract air -> glass
                    norm = _triangle_normal_at_exit(nx, ny, v[0], v[1], v[2])
                    # Flip normal inward for entry
                    norm = (-norm[0], -norm[1])
                    result = _refract(dx, dy, norm[0], norm[1], 1.0, n_glass)
                    if result:
                        dx, dy = result
                    in_prism = pi
                    interacted = True
                    break
                elif was_inside and not now_inside:
                    # Exiting prism: refract glass -> air
                    norm = _triangle_normal_at_exit(x, y, v[0], v[1], v[2])
                    result = _refract(dx, dy, norm[0], norm[1], n_glass, 1.0)
                    if result:
                        dx, dy = result
                    else:
                        # Total internal reflection
                        dx, dy = _reflect(dx, dy, norm[0], norm[1])
                        reflections += 1
                    in_prism = -1
                    interacted = True
                    break

            # Check lens interactions
            if not interacted:
                for lens in self.lenses:
                    lcx, lcy = lens['cx'], lens['cy']
                    lr = lens['radius']
                    fl = lens['focal_len']
                    ltype = lens['type']
                    if self.sub_variant == 1:
                        ltype = 'concave'
                    # Thin lens approximation: when ray crosses the lens plane (x = lcx)
                    if (x - lcx) * (nx - lcx) <= 0 and abs(ny - lcy) < lr:
                        # Ray is crossing the lens plane
                        # Compute y at crossing
                        if abs(dx) > 0.001:
                            t_cross = (lcx - x) / dx
                            cross_y = y + t_cross * dy
                        else:
                            cross_y = y
                        if abs(cross_y - lcy) < lr:
                            # Deflect ray based on thin lens formula
                            y_off = cross_y - lcy
                            if ltype == 'convex':
                                # Bend toward focal point
                                deflection = -y_off / fl
                            else:
                                # Bend away from axis
                                deflection = y_off / fl
                            dy += deflection
                            # Re-normalize
                            dlen2 = math.sqrt(dx * dx + dy * dy)
                            if dlen2 > 0.001:
                                dx /= dlen2
                                dy /= dlen2
                            interacted = True
                            break

            # Check mirror interactions
            if not interacted:
                for mirror in self.mirrors:
                    mx1, my1 = mirror['x1'], mirror['y1']
                    mx2, my2 = mirror['x2'], mirror['y2']
                    d = _dist_to_segment(nx, ny, mx1, my1, mx2, my2)
                    if d < 1.0:
                        mnx, mny = _segment_normal(mx1, my1, mx2, my2)
                        # Ensure normal faces incoming ray
                        if dx * mnx + dy * mny > 0:
                            mnx, mny = -mnx, -mny
                        dx, dy = _reflect(dx, dy, mnx, mny)
                        reflections += 1
                        # Nudge away from mirror
                        nx = x + RAY_STEP * dx * 2
                        ny = y + RAY_STEP * dy * 2
                        # Dim slightly on reflection
                        color = (
                            max(0, int(color[0] * 0.85)),
                            max(0, int(color[1] * 0.85)),
                            max(0, int(color[2] * 0.85)),
                        )
                        interacted = True
                        if reflections >= max_reflections:
                            x, y = nx, ny
                            break
                        break

            if reflections >= max_reflections:
                break

            x, y = nx, ny

        return points

    # ── input ────────────────────────────────────────────────────

    def handle_input(self, input_state) -> bool:
        consumed = False
        scenario = _SCENARIOS[self.scenario_idx]

        # Left/Right: adjust beam angle or kaleidoscope rotation speed
        if input_state.left_pressed or input_state.left:
            if scenario == 'KALEIDOSCOPE':
                self.kaleidoscope_speed = max(-1.0, self.kaleidoscope_speed - 0.05)
            else:
                self.user_angle -= 0.06
            consumed = True
        if input_state.right_pressed or input_state.right:
            if scenario == 'KALEIDOSCOPE':
                self.kaleidoscope_speed = min(1.0, self.kaleidoscope_speed + 0.05)
            else:
                self.user_angle += 0.06
            consumed = True

        # Up/Down: cycle palette
        if input_state.up_pressed:
            self.palette_idx = (self.palette_idx + 1) % len(PALETTES)
            if self.show_notes:
                self._build_notes_segments()
            consumed = True
        if input_state.down_pressed:
            self.palette_idx = (self.palette_idx - 1) % len(PALETTES)
            if self.show_notes:
                self._build_notes_segments()
            consumed = True

        # Both buttons: toggle notes
        both = input_state.action_l and input_state.action_r
        if both and not self._both_pressed_prev:
            self.show_notes = not self.show_notes
            self.notes_scroll_offset = 0.0
            if self.show_notes:
                self._build_notes_segments()
            consumed = True
        elif input_state.action_l or input_state.action_r:
            if not both:
                # Single button: cycle through scenario, then sub-variants
                self._cycle_scenario()
                consumed = True
        self._both_pressed_prev = both

        return consumed

    def _cycle_scenario(self):
        """Advance to next sub-variant, or next scenario if at last sub-variant."""
        scenario = _SCENARIOS[self.scenario_idx]
        max_sub = self._max_sub_variant(scenario)

        if self.sub_variant < max_sub - 1:
            # Advance sub-variant within current scenario
            self.sub_variant += 1
            label = self._sub_variant_label(scenario, self.sub_variant)
            if scenario == 'MIRRORS':
                self._rearrange_mirrors()
            elif scenario == 'KALEIDOSCOPE':
                self._rearrange_kaleidoscope()
            self._show_overlay(label)
        else:
            # Advance to next scenario
            self.scenario_idx = (self.scenario_idx + 1) % len(_SCENARIOS)
            self.user_angle = 0.0
            self._setup_scenario()
            new_scenario = _SCENARIOS[self.scenario_idx]
            label = self._sub_variant_label(new_scenario, 0)
            self._show_overlay(label)

    @staticmethod
    def _max_sub_variant(scenario):
        if scenario == 'LENS':
            return 2        # convex, concave
        elif scenario == 'MIRRORS':
            return 3        # double, corner, parallel
        elif scenario == 'KALEIDOSCOPE':
            return 3        # 3-fold, 4-fold, 6-fold
        return 1            # PRISM, DOUBLE PRISM have no sub-variants

    @staticmethod
    def _sub_variant_label(scenario, sub):
        if scenario == 'LENS':
            return ['CONVEX LENS', 'CONCAVE LENS'][sub]
        elif scenario == 'MIRRORS':
            return ['DOUBLE', 'CORNER', 'PARALLEL'][sub]
        elif scenario == 'KALEIDOSCOPE':
            return ['3-FOLD', '4-FOLD', '6-FOLD'][sub]
        return scenario

    def _rearrange_mirrors(self):
        """Rearrange mirrors for sub-variants."""
        self.mirrors = []
        self.sources = []
        if self.sub_variant == 0:
            # Double: two angled mirrors
            self.mirrors.append({'x1': 10, 'y1': 15, 'x2': 40, 'y2': 10})
            self.mirrors.append({'x1': 25, 'y1': 55, 'x2': 58, 'y2': 35})
            colors = [
                (255, 255, 255), (255, 200, 100), (100, 200, 255),
                (255, 100, 100), (100, 255, 100),
            ]
            for i in range(5):
                self.sources.append({
                    'x': 2.0, 'y': 30.0 + i * 1.5, 'dx': 0.9, 'dy': -0.44,
                    'color': colors[i], 'wavelength': 550, 'n': 1.0,
                })
        elif self.sub_variant == 1:
            # Corner: two perpendicular mirrors
            self.mirrors.append({'x1': 50, 'y1': 5, 'x2': 50, 'y2': 50})
            self.mirrors.append({'x1': 5, 'y1': 50, 'x2': 50, 'y2': 50})
            colors = [
                (255, 80, 80), (80, 255, 80), (80, 80, 255),
                (255, 255, 80), (255, 80, 255), (80, 255, 255),
            ]
            for i in range(6):
                self.sources.append({
                    'x': 5.0, 'y': 10.0 + i * 6, 'dx': 1.0, 'dy': 0.15,
                    'color': colors[i], 'wavelength': 550, 'n': 1.0,
                })
        else:
            # Parallel: two parallel mirrors
            self.mirrors.append({'x1': 10, 'y1': 8, 'x2': 54, 'y2': 8})
            self.mirrors.append({'x1': 10, 'y1': 56, 'x2': 54, 'y2': 56})
            colors = [
                (255, 100, 50), (50, 255, 100), (100, 50, 255),
                (255, 255, 100),
            ]
            for i in range(4):
                self.sources.append({
                    'x': 5.0, 'y': 20.0 + i * 5, 'dx': 0.95, 'dy': 0.31,
                    'color': colors[i], 'wavelength': 550, 'n': 1.0,
                })

    def _rearrange_kaleidoscope(self):
        """Rearrange kaleidoscope mirror geometry for sub-variants."""
        self.mirrors = []
        self.sources = []
        cx, cy = 32, 32

        folds = [3, 4, 6][self.sub_variant]
        r = 22
        angles = [math.pi / 2 + 2 * math.pi * i / folds for i in range(folds)]
        verts = [(cx + r * math.cos(a), cy + r * math.sin(a)) for a in angles]
        for i in range(folds):
            j = (i + 1) % folds
            self.mirrors.append({
                'x1': verts[i][0], 'y1': verts[i][1],
                'x2': verts[j][0], 'y2': verts[j][1],
            })

        source_colors = [
            (255, 60, 60), (60, 255, 60), (60, 60, 255),
            (255, 255, 0), (0, 255, 255), (255, 0, 255),
        ]
        n_sources = min(6, folds * 2)
        for i in range(n_sources):
            angle = 2 * math.pi * i / n_sources
            sx = cx + 3 * math.cos(angle)
            sy = cy + 3 * math.sin(angle)
            for j in range(3):
                a2 = angle + (j - 1) * 0.3
                self.sources.append({
                    'x': sx, 'y': sy,
                    'dx': math.cos(a2), 'dy': math.sin(a2),
                    'color': source_colors[i % len(source_colors)],
                    'wavelength': 550, 'n': 1.0,
                })

    # ── update ───────────────────────────────────────────────────

    def update(self, dt: float):
        self.time += dt

        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

        if self.show_notes:
            self.notes_scroll_offset += dt * 18

    # ── draw ─────────────────────────────────────────────────────

    def draw(self):
        pal = PALETTES[self.palette_idx]
        self.display.clear(pal['bg'])

        scenario = _SCENARIOS[self.scenario_idx]

        # Compute animation angle
        anim_angle = self._get_anim_angle(scenario)

        # Draw optical elements first (behind rays)
        self._draw_elements(pal)

        # Trace and draw all rays
        self._draw_all_rays(anim_angle)

        # Overlays
        if self.show_notes:
            self._draw_notes()
        self._draw_overlay()

    def _get_anim_angle(self, scenario):
        """Return beam angle based on user control."""
        if scenario == 'KALEIDOSCOPE':
            return self.time * self.kaleidoscope_speed
        return self.user_angle

    def _draw_elements(self, pal):
        """Draw prisms, lenses, and mirrors."""
        elem_color = pal['elem']
        fill_color = pal['fill']
        d = self.display

        # Draw prisms
        for prism in self.prisms:
            v = prism['vertices']
            # Fill triangle
            self._fill_triangle(v[0], v[1], v[2], fill_color)
            # Outline
            d.draw_line(int(v[0][0]), int(v[0][1]), int(v[1][0]), int(v[1][1]), elem_color)
            d.draw_line(int(v[1][0]), int(v[1][1]), int(v[2][0]), int(v[2][1]), elem_color)
            d.draw_line(int(v[2][0]), int(v[2][1]), int(v[0][0]), int(v[0][1]), elem_color)

        # Draw lenses
        for lens in self.lenses:
            lcx, lcy = int(lens['cx']), int(lens['cy'])
            lr = lens['radius']
            ltype = lens['type']
            if self.sub_variant == 1 and _SCENARIOS[self.scenario_idx] == 'LENS':
                ltype = 'concave'
            # Draw lens as curved shape
            lens_color = (
                min(255, int(elem_color[0] * 0.7 + 80)),
                min(255, int(elem_color[1] * 0.7 + 80)),
                min(255, int(elem_color[2] * 0.8 + 80)),
            )
            for iy in range(-int(lr), int(lr) + 1):
                py = lcy + iy
                if py < 0 or py >= GRID_SIZE:
                    continue
                # Lens width varies with y (thicker in middle for convex)
                t = abs(iy) / lr
                if ltype == 'convex':
                    half_w = max(0, int(2.5 * (1.0 - t * t)))
                else:
                    half_w = max(0, int(0.5 + 2.0 * t * t))
                for ix in range(-half_w, half_w + 1):
                    px = lcx + ix
                    if 0 <= px < GRID_SIZE:
                        d.set_pixel(px, py, lens_color)
            # Lens outline edges
            for iy in range(-int(lr), int(lr) + 1):
                py = lcy + iy
                if py < 0 or py >= GRID_SIZE:
                    continue
                t = abs(iy) / lr
                if ltype == 'convex':
                    half_w = max(0, int(2.5 * (1.0 - t * t)))
                else:
                    half_w = max(0, int(0.5 + 2.0 * t * t))
                for edge_x in (-half_w, half_w):
                    px = lcx + edge_x
                    if 0 <= px < GRID_SIZE:
                        d.set_pixel(px, py, elem_color)

        # Draw mirrors
        for mirror in self.mirrors:
            mx1, my1, mx2, my2 = int(mirror['x1']), int(mirror['y1']), int(mirror['x2']), int(mirror['y2'])
            d.draw_line(mx1, my1, mx2, my2, Colors.WHITE)
            # Draw a faint highlight line next to mirror
            nx, ny = _segment_normal(mirror['x1'], mirror['y1'], mirror['x2'], mirror['y2'])
            d.draw_line(
                mx1 + int(nx), my1 + int(ny),
                mx2 + int(nx), my2 + int(ny),
                (80, 80, 100),
            )

    def _fill_triangle(self, v0, v1, v2, color):
        """Scanline fill a triangle."""
        # Bounding box
        min_y = max(0, int(min(v0[1], v1[1], v2[1])))
        max_y = min(GRID_SIZE - 1, int(max(v0[1], v1[1], v2[1])))
        min_x = max(0, int(min(v0[0], v1[0], v2[0])))
        max_x = min(GRID_SIZE - 1, int(max(v0[0], v1[0], v2[0])))
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                if _point_in_triangle(x + 0.5, y + 0.5, v0, v1, v2):
                    self.display.set_pixel(x, y, color)

    def _draw_all_rays(self, anim_angle):
        """Trace and draw all source rays."""
        for src in self.sources:
            points = self._trace_ray(src, anim_angle)
            for (px, py, r, g, b) in points:
                if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                    # Additive blend onto existing pixel
                    cur = self.display.get_pixel(px, py)
                    blended = (
                        min(255, cur[0] + r),
                        min(255, cur[1] + g),
                        min(255, cur[2] + b),
                    )
                    self.display.set_pixel(px, py, blended)
