"""Color Theory - Educational color theory reference on 64x64 LED matrix.

10 pages: Spectrum, Color Wheel, Complementary, Analogous, Triadic,
Split-Complementary, RGB Mixing, CMY Mixing, Tints/Shades, Temperature.
"""

import math
from . import Visual

# ── Helpers ────────────────────────────────────────────────────────

def _hsv_to_rgb(h, s, v):
    """Convert HSV (h: 0-360, s: 0-1, v: 0-1) to RGB tuple."""
    h = h % 360
    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c
    if h < 60:
        r, g, b = c, x, 0
    elif h < 120:
        r, g, b = x, c, 0
    elif h < 180:
        r, g, b = 0, c, x
    elif h < 240:
        r, g, b = 0, x, c
    elif h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x
    return (int((r + m) * 255), int((g + m) * 255), int((b + m) * 255))


def _dim(color, factor):
    return (int(color[0] * factor), int(color[1] * factor), int(color[2] * factor))


def _blend(c1, c2, t):
    """Lerp between two colors, t in 0..1."""
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


def _add_rgb(c1, c2):
    """Additive color mixing (light)."""
    return (min(255, c1[0] + c2[0]), min(255, c1[1] + c2[1]), min(255, c1[2] + c2[2]))


def _sub_cmy(c1, c2):
    """Subtractive color mixing (pigment). Colors given as RGB of the pigment."""
    # Subtractive: multiply the absorption
    r = c1[0] * c2[0] // 255
    g = c1[1] * c2[1] // 255
    b = c1[2] * c2[2] // 255
    return (r, g, b)


# 12-hue wheel: hue degrees for traditional RYB-ish mapping rendered in RGB
# We use standard HSV hues (0=red, 60=yellow, 120=green, 180=cyan, 240=blue, 300=magenta)
WHEEL_HUES = [i * 30 for i in range(12)]  # 0, 30, 60, ..., 330
WHEEL_NAMES = ['R', 'RO', 'O', 'YO', 'Y', 'YG', 'G', 'BG', 'C', 'CB', 'B', 'BV', 'V', 'RV']
# Simplified 12 names
WHEEL_12 = ['R', '', 'O', '', 'Y', '', 'G', '', 'C', '', 'B', '', 'M', '']

PAGE_NAMES = [
    'SPECTRUM',
    'COLOR WHEEL',
    'COMPLEMENT',
    'ANALOGOUS',
    'TRIADIC',
    'SPLIT COMP',
    'RGB MIX',
    'CMY MIX',
    'TINT/SHADE',
    'TEMPERATURE',
]

NUM_PAGES = len(PAGE_NAMES)

SEP_COLOR = (50, 50, 70)
HEADER_BG = (20, 20, 30)
TEXT_DIM = (100, 100, 120)
TITLE_COLOR = (200, 200, 220)


class ColorTheory(Visual):
    name = "COLOR THEORY"
    description = "Color theory reference"
    category = "science"

    def reset(self):
        self.time = 0.0
        self.page = 0
        self.hue_offset = 0.0       # user-controlled hue rotation
        self.sub_index = 0           # sub-selection within a page
        self.value = 1.0             # brightness for SPECTRUM page
        self.overlay_timer = 0.0
        self.overlay_text = ''

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.up_pressed:
            self.page = (self.page - 1) % NUM_PAGES
            self.sub_index = 0
            self._show_overlay(PAGE_NAMES[self.page])
            consumed = True
        elif input_state.down_pressed:
            self.page = (self.page + 1) % NUM_PAGES
            self.sub_index = 0
            self._show_overlay(PAGE_NAMES[self.page])
            consumed = True

        if input_state.left_pressed:
            if self.page == 0:  # SPECTRUM: adjust brightness
                self.value = max(0.0, self.value - 0.1)
            else:
                self.hue_offset -= 15
                self.sub_index = (self.sub_index - 1)
            consumed = True
        elif input_state.right_pressed:
            if self.page == 0:  # SPECTRUM: adjust brightness
                self.value = min(1.0, self.value + 0.1)
            else:
                self.hue_offset += 15
                self.sub_index = (self.sub_index + 1)
            consumed = True

        if input_state.action_l or input_state.action_r:
            # Toggle related views on certain pages
            if self.page == 0:       # SPECTRUM: reset brightness
                self.value = 1.0
            elif self.page == 6:     # RGB -> CMY
                self.page = 7
                self._show_overlay(PAGE_NAMES[self.page])
            elif self.page == 7:     # CMY -> RGB
                self.page = 6
                self._show_overlay(PAGE_NAMES[self.page])
            else:
                self.hue_offset = 0
                self.sub_index = 0
            consumed = True

        return consumed

    def _show_overlay(self, text):
        self.overlay_text = text
        self.overlay_timer = 1.0

    def update(self, dt: float):
        self.time += dt
        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

    def draw(self):
        d = self.display
        d.clear()

        # Title
        title = PAGE_NAMES[self.page]
        d.draw_text_small(2, 1, title, TITLE_COLOR)

        # Separator under title
        for x in range(64):
            d.set_pixel(x, 7, SEP_COLOR)

        # Page content area: y=9 to y=56
        page_fn = [
            self._draw_spectrum,
            self._draw_wheel,
            self._draw_complement,
            self._draw_analogous,
            self._draw_triadic,
            self._draw_split_comp,
            self._draw_rgb_mix,
            self._draw_cmy_mix,
            self._draw_tint_shade,
            self._draw_temperature,
        ]
        page_fn[self.page]()

        # Footer: page dots
        self._draw_footer()

        # Overlay
        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            oc = (int(255 * alpha), int(255 * alpha), int(255 * alpha))
            bg = (int(20 * alpha), int(20 * alpha), int(30 * alpha))
            text = self.overlay_text
            tw = len(text) * 4
            tx = max(1, (64 - tw) // 2)
            d.draw_rect(0, 28, 64, 9, bg)
            d.draw_text_small(tx, 30, text, oc)

    # ── Footer ────────────────────────────────────────────────────

    def _draw_footer(self):
        d = self.display
        for x in range(64):
            d.set_pixel(x, 58, SEP_COLOR)
        # Page indicator dots
        total_w = NUM_PAGES * 3 + (NUM_PAGES - 1) * 2  # 3px dot + 2px gap
        start_x = (64 - total_w) // 2
        for i in range(NUM_PAGES):
            x = start_x + i * 5
            color = TITLE_COLOR if i == self.page else (40, 40, 50)
            d.set_pixel(x, 61, color)
            d.set_pixel(x + 1, 61, color)
            d.set_pixel(x, 62, color)
            d.set_pixel(x + 1, 62, color)

    # ── Wheel drawing helper ──────────────────────────────────────

    def _draw_color_wheel(self, cx, cy, r_outer, r_inner, offset_deg=0.0,
                          highlight_hues=None, dim_others=False, labels=True):
        """Draw a color wheel ring. highlight_hues: list of hue indices (0-11) to highlight."""
        d = self.display
        for py in range(cy - r_outer - 1, cy + r_outer + 2):
            for px in range(cx - r_outer - 1, cx + r_outer + 2):
                dx = px - cx
                dy = py - cy
                dist_sq = dx * dx + dy * dy
                if dist_sq < r_inner * r_inner or dist_sq > r_outer * r_outer:
                    continue
                angle = math.degrees(math.atan2(dy, dx)) + offset_deg
                hue = angle % 360
                idx = int(hue / 30) % 12

                color = _hsv_to_rgb(idx * 30, 1.0, 1.0)
                if dim_others and highlight_hues is not None and idx not in highlight_hues:
                    color = _dim(color, 0.15)
                elif highlight_hues is not None and idx in highlight_hues:
                    # slightly brighten
                    color = _hsv_to_rgb(idx * 30, 1.0, 1.0)

                if 0 <= px < 64 and 0 <= py < 64:
                    d.set_pixel(px, py, color)

        # Labels for primaries
        if labels:
            label_r = r_outer + 3
            primaries = [(0, 'R'), (4, 'Y'), (8, 'B')]
            for idx, lbl in primaries:
                angle_rad = math.radians(idx * 30 - offset_deg)
                lx = int(cx + label_r * math.cos(angle_rad)) - 1
                ly = int(cy + label_r * math.sin(angle_rad)) - 2
                if 0 <= lx < 62 and 0 <= ly < 59:
                    c = _hsv_to_rgb(idx * 30, 1.0, 1.0)
                    d.draw_text_small(lx, ly, lbl, c)

    # ── Page 1: Spectrum (H×S plane) ─────────────────────────────

    def _draw_spectrum(self):
        d = self.display
        v = self.value

        # Label: brightness percentage
        pct = int(round(v * 100))
        d.draw_text_small(2, 9, f'V:{pct}%', TEXT_DIM)

        # H×S grid: x=2..61 (60px), y=14..53 (40px)
        for px in range(2, 62):
            hue = (px - 2) * 6.0  # 0 to 360 across 60 pixels
            for py in range(14, 54):
                sat = 1.0 - (py - 14) / 39.0  # 1.0 at top, 0.0 at bottom
                color = _hsv_to_rgb(hue, sat, v)
                d.set_pixel(px, py, color)

        # V slider bar: y=55..56 (2px), x=2..61
        for px in range(2, 62):
            bri = (px - 2) / 59.0
            gray = int(bri * 255)
            for py in range(55, 57):
                d.set_pixel(px, py, (gray, gray, gray))

        # Marker on slider showing current V
        marker_x = int(2 + v * 59)
        marker_x = max(2, min(61, marker_x))
        for py in range(54, 57):
            d.set_pixel(marker_x, py, (255, 255, 255))

    # ── Page 2: Color Wheel ───────────────────────────────────────

    def _draw_wheel(self):
        auto_rot = self.time * 5  # slow auto rotation
        self._draw_color_wheel(31, 32, 18, 10,
                               offset_deg=-(self.hue_offset + auto_rot),
                               labels=True)

    # ── Page 3: Complementary ─────────────────────────────────────

    def _draw_complement(self):
        d = self.display
        # Any hue and its complement (opposite on the 12-hue wheel)
        i1 = self.sub_index % 12
        i2 = (i1 + 6) % 12

        # Small wheel with highlighted pair
        self._draw_color_wheel(18, 28, 13, 7,
                               highlight_hues=[i1, i2], dim_others=True, labels=False)

        # Line between the two on the wheel
        a1 = math.radians(i1 * 30)
        a2 = math.radians(i2 * 30)
        x1, y1 = int(18 + 10 * math.cos(a1)), int(28 + 10 * math.sin(a1))
        x2, y2 = int(18 + 10 * math.cos(a2)), int(28 + 10 * math.sin(a2))
        d.draw_line(x1, y1, x2, y2, (80, 80, 100))

        # Swatches on right
        c1 = _hsv_to_rgb(i1 * 30, 1.0, 1.0)
        c2 = _hsv_to_rgb(i2 * 30, 1.0, 1.0)
        d.draw_rect(38, 14, 10, 10, c1)
        d.draw_rect(50, 14, 10, 10, c2)

        # Blend swatch
        mid = _blend(c1, c2, 0.5)
        d.draw_rect(44, 30, 10, 10, mid)
        d.draw_text_small(38, 44, 'PAIR', TEXT_DIM)

    # ── Page 3: Analogous ─────────────────────────────────────────

    def _draw_analogous(self):
        d = self.display
        base = self.sub_index % 12
        group = [base % 12, (base + 1) % 12, (base + 2) % 12]

        self._draw_color_wheel(18, 28, 13, 7,
                               highlight_hues=group, dim_others=True, labels=False)

        # Draw arc connecting the group
        for idx in group:
            a = math.radians(idx * 30)
            x = int(18 + 10 * math.cos(a))
            y = int(28 + 10 * math.sin(a))
            c = _hsv_to_rgb(idx * 30, 1.0, 1.0)
            d.draw_circle(x, y, 1, c, filled=True)

        # Swatches on right
        for i, idx in enumerate(group):
            c = _hsv_to_rgb(idx * 30, 1.0, 1.0)
            d.draw_rect(38, 12 + i * 12, 22, 10, c)

        d.draw_text_small(38, 49, 'GROUP', TEXT_DIM)

    # ── Page 4: Triadic ───────────────────────────────────────────

    def _draw_triadic(self):
        d = self.display
        auto_rot = self.time * 8
        base_offset = self.hue_offset + auto_rot
        # 3 equally spaced hues
        tri = [int((base_offset / 30 + i * 4) % 12) for i in range(3)]

        self._draw_color_wheel(24, 30, 15, 8, labels=False)

        # Draw triangle
        pts = []
        for idx in tri:
            a = math.radians(idx * 30)
            pts.append((int(24 + 12 * math.cos(a)), int(30 + 12 * math.sin(a))))

        for i in range(3):
            j = (i + 1) % 3
            d.draw_line(pts[i][0], pts[i][1], pts[j][0], pts[j][1], (180, 180, 200))

        # Swatches
        for i, idx in enumerate(tri):
            c = _hsv_to_rgb(idx * 30, 1.0, 1.0)
            d.draw_rect(46, 10 + i * 14, 14, 12, c)

    # ── Page 5: Split-Complementary ───────────────────────────────

    def _draw_split_comp(self):
        d = self.display
        base = self.sub_index % 12
        comp = (base + 6) % 12
        split1 = (comp - 1) % 12
        split2 = (comp + 1) % 12
        group = [base, split1, split2]

        self._draw_color_wheel(18, 28, 13, 7,
                               highlight_hues=group, dim_others=True, labels=False)

        # Lines from base to splits
        a0 = math.radians(base * 30)
        x0, y0 = int(18 + 10 * math.cos(a0)), int(28 + 10 * math.sin(a0))
        for idx in [split1, split2]:
            a = math.radians(idx * 30)
            x, y = int(18 + 10 * math.cos(a)), int(28 + 10 * math.sin(a))
            d.draw_line(x0, y0, x, y, (80, 80, 100))

        # Swatches
        colors = [_hsv_to_rgb(i * 30, 1.0, 1.0) for i in group]
        d.draw_rect(38, 12, 22, 8, colors[0])
        d.draw_text_small(38, 22, 'BASE', _dim(colors[0], 0.6))
        d.draw_rect(38, 30, 10, 8, colors[1])
        d.draw_rect(50, 30, 10, 8, colors[2])
        d.draw_text_small(38, 40, 'SPLIT', TEXT_DIM)

    # ── RGB Mixing (Additive) ───────────────────────────────────────

    def _draw_rgb_mix(self):
        d = self.display
        R = (255, 0, 0)
        G = (0, 255, 0)
        B = (0, 0, 255)

        cx, cy = 31, 30
        radius = 12
        offset = max(4, min(10, 7 + self.sub_index))  # L/R adjusts overlap

        # Circle centers
        centers = [
            (cx, cy - offset, R),       # Red top
            (cx - offset, cy + 5, G),    # Green bottom-left
            (cx + offset, cy + 5, B),    # Blue bottom-right
        ]

        # For each pixel in the area, determine which circles it's in
        for py in range(9, 54):
            for px in range(4, 60):
                inside = []
                for ccx, ccy, cc in centers:
                    dx = px - ccx
                    dy = py - ccy
                    if dx * dx + dy * dy <= radius * radius:
                        inside.append(cc)
                if inside:
                    result = (0, 0, 0)
                    for c in inside:
                        result = _add_rgb(result, c)
                    d.set_pixel(px, py, result)

        # Labels
        d.draw_text_small(2, 52, 'ADDITIVE', (200, 200, 220))

    # ── Page 8: CMY Mixing (Subtractive) ──────────────────────────

    def _draw_cmy_mix(self):
        d = self.display
        C = (0, 255, 255)
        M = (255, 0, 255)
        Y = (255, 255, 0)

        cx, cy = 31, 30
        radius = 12
        offset = max(4, min(10, 7 + self.sub_index))  # L/R adjusts overlap

        centers = [
            (cx, cy - offset, C),
            (cx - offset, cy + 5, M),
            (cx + offset, cy + 5, Y),
        ]

        for py in range(9, 54):
            for px in range(4, 60):
                inside = []
                for ccx, ccy, cc in centers:
                    dx = px - ccx
                    dy = py - ccy
                    if dx * dx + dy * dy <= radius * radius:
                        inside.append(cc)
                if inside:
                    result = (255, 255, 255)
                    for c in inside:
                        result = _sub_cmy(result, c)
                    d.set_pixel(px, py, result)

        d.draw_text_small(2, 52, 'SUBTRACT', (200, 200, 220))

    # ── Page 9: Tint / Shade ──────────────────────────────────────

    def _draw_tint_shade(self):
        d = self.display
        base_hue = (self.sub_index * 30) % 360
        base_color = _hsv_to_rgb(base_hue, 1.0, 1.0)

        # Show hue name
        hue_idx = (base_hue // 30) % 12
        hue_labels = ['RED', 'ORG', 'YEL', 'YGR', 'GRN', 'CYN',
                      'CYN', 'SKY', 'BLU', 'IND', 'VIO', 'MAG']
        d.draw_text_small(2, 9, hue_labels[hue_idx], base_color)

        # Tint strip (pure -> white): y=16, height=8
        d.draw_text_small(2, 16, 'TINT', _dim(TITLE_COLOR, 0.5))
        for px in range(2, 62):
            t = (px - 2) / 60.0
            c = _blend(base_color, (255, 255, 255), t)
            for py in range(22, 30):
                d.set_pixel(px, py, c)

        # Pure color bar
        for px in range(2, 62):
            for py in range(32, 36):
                d.set_pixel(px, py, base_color)
        d.draw_text_small(2, 37, 'PURE', _dim(TITLE_COLOR, 0.5))

        # Shade strip (pure -> black): y=44, height=8
        d.draw_text_small(2, 42, 'SHADE', _dim(TITLE_COLOR, 0.5))
        for px in range(2, 62):
            t = (px - 2) / 60.0
            c = _blend(base_color, (0, 0, 0), t)
            for py in range(48, 56):
                d.set_pixel(px, py, c)

    # ── Page 10: Temperature ──────────────────────────────────────

    def _draw_temperature(self):
        d = self.display
        # Draw a simple scene (mountains + sun/moon) in warm vs cool palettes
        # Left half: warm, Right half: cool
        warm_sky = (60, 20, 10)
        warm_sun = (255, 200, 40)
        warm_ground = (140, 80, 20)
        warm_peak = (200, 120, 40)

        cool_sky = (10, 20, 60)
        cool_moon = (180, 200, 255)
        cool_ground = (30, 60, 120)
        cool_peak = (60, 100, 180)

        # Two scenes side by side
        scenes = [
            (0, 31, warm_sky, warm_sun, warm_ground, warm_peak),
            (33, 63, cool_sky, cool_moon, cool_ground, cool_peak),
        ]

        for x0, x1, sky, orb, ground, peak in scenes:
            w = x1 - x0 + 1
            mid_x = (x0 + x1) // 2

            # Sky fill
            for py in range(9, 56):
                for px in range(x0, x1 + 1):
                    if 0 <= px < 64 and 0 <= py < 64:
                        d.set_pixel(px, py, sky)

            # Sun/Moon
            orb_cx = mid_x
            orb_cy = 18
            for py in range(orb_cy - 4, orb_cy + 5):
                for px in range(orb_cx - 4, orb_cx + 5):
                    if (px - orb_cx)**2 + (py - orb_cy)**2 <= 16:
                        if x0 <= px <= x1 and 0 <= py < 64:
                            d.set_pixel(px, py, orb)

            # Mountain (triangle)
            peak_x = mid_x
            peak_y = 28
            base_y = 55
            for py in range(peak_y, base_y + 1):
                t = (py - peak_y) / max(1, base_y - peak_y)
                half_w = int(t * (w // 2))
                for px in range(peak_x - half_w, peak_x + half_w + 1):
                    if x0 <= px <= x1 and 0 <= py < 64:
                        d.set_pixel(px, py, _blend(peak, ground, t))

        # Divider
        for py in range(9, 56):
            d.set_pixel(32, py, (0, 0, 0))

        # Labels
        d.draw_text_small(4, 9, 'WARM', (255, 180, 60))
        d.draw_text_small(37, 9, 'COOL', (100, 160, 255))
