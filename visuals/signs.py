"""
STREET SIGNS OF THE WORLD
==========================
Traffic signs from around the world showing how the same concepts
(stop, yield, speed limit, etc.) look different across countries.
Sign images loaded from PNG files in assets/signs/, pre-rendered
via tools/build_signs.py from Wikimedia Commons SVGs.
"""

import os
from PIL import Image
from . import Visual, Colors

# Sign dimensions and position
SIGN_SIZE = 44
SX = (64 - SIGN_SIZE) // 2   # 10
SY = 2
LABEL_Y = SY + SIGN_SIZE + 2  # 48

ASSETS_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'signs')

# (display_name, sign_type, filename_stem) — matches tools/build_signs.py
# Only entries whose PNGs exist on disk are loaded at runtime.
SIGN_MANIFEST = [
    # ===== STOP =====
    ('USA', 'stop', 'us_stop'),
    ('JAPAN', 'stop', 'jp_stop'),
    ('FRANCE', 'stop', 'fr_stop'),
    ('GERMANY', 'stop', 'de_stop'),
    ('MEXICO', 'stop', 'mx_stop'),
    ('BRAZIL', 'stop', 'br_stop'),
    ('TURKEY', 'stop', 'tr_stop'),
    ('IRAN', 'stop', 'ir_stop'),
    ('SOUTH KOREA', 'stop', 'kr_stop'),
    ('ISRAEL', 'stop', 'il_stop'),
    ('THAILAND', 'stop', 'th_stop'),
    ('ETHIOPIA', 'stop', 'et_stop'),
    ('INDIA', 'stop', 'in_stop'),
    ('CUBA', 'stop', 'cu_stop'),
    ('VIETNAM', 'stop', 'vn_stop'),
    # ===== YIELD =====
    ('USA', 'yield', 'us_yield'),
    ('JAPAN', 'yield', 'jp_yield'),
    ('GERMANY', 'yield', 'de_yield'),
    ('FRANCE', 'yield', 'fr_yield'),
    ('BRAZIL', 'yield', 'br_yield'),
    ('SOUTH KOREA', 'yield', 'kr_yield'),
    ('SWEDEN', 'yield', 'se_yield'),
    ('IRELAND', 'yield', 'ie_yield'),
    ('VIETNAM', 'yield', 'vn_yield'),
    # ===== SPEED LIMIT =====
    ('USA', 'speed', 'us_speed'),
    ('GERMANY', 'speed', 'de_speed'),
    ('JAPAN', 'speed', 'jp_speed'),
    ('UK', 'speed', 'gb_speed'),
    ('AUSTRALIA', 'speed', 'au_speed'),
    ('FRANCE', 'speed', 'fr_speed'),
    ('SOUTH KOREA', 'speed', 'kr_speed'),
    ('BRAZIL', 'speed', 'br_speed'),
    ('RUSSIA', 'speed', 'ru_speed'),
    # ===== NO ENTRY =====
    ('USA', 'no_entry', 'us_no_entry'),
    ('JAPAN', 'no_entry', 'jp_no_entry'),
    ('GERMANY', 'no_entry', 'de_no_entry'),
    ('FRANCE', 'no_entry', 'fr_no_entry'),
    ('SOUTH KOREA', 'no_entry', 'kr_no_entry'),
    ('INDIA', 'no_entry', 'in_no_entry'),
    ('BRAZIL', 'no_entry', 'br_no_entry'),
    ('SWEDEN', 'no_entry', 'se_no_entry'),
    ('VIETNAM', 'no_entry', 'vn_no_entry'),
    # ===== PEDESTRIAN =====
    ('USA', 'pedestrian', 'us_pedestrian'),
    ('JAPAN', 'pedestrian', 'jp_pedestrian'),
    ('GERMANY', 'pedestrian', 'de_pedestrian'),
    ('FRANCE', 'pedestrian', 'fr_pedestrian'),
    ('UK', 'pedestrian', 'gb_pedestrian'),
    ('SOUTH KOREA', 'pedestrian', 'kr_pedestrian'),
    ('BRAZIL', 'pedestrian', 'br_pedestrian'),
    ('SWEDEN', 'pedestrian', 'se_pedestrian'),
    ('AUSTRALIA', 'pedestrian', 'au_pedestrian'),
    ('RUSSIA', 'pedestrian', 'ru_pedestrian'),
    # ===== WARNING =====
    ('USA', 'warning', 'us_warning'),
    ('JAPAN', 'warning', 'jp_warning'),
    ('GERMANY', 'warning', 'de_warning'),
    ('FRANCE', 'warning', 'fr_warning'),
    ('UK', 'warning', 'gb_warning'),
    ('SOUTH KOREA', 'warning', 'kr_warning'),
    ('BRAZIL', 'warning', 'br_warning'),
    ('AUSTRALIA', 'warning', 'au_warning'),
    ('SWEDEN', 'warning', 'se_warning'),
    ('RUSSIA', 'warning', 'ru_warning'),
    ('INDIA', 'warning', 'in_warning'),
]

# Groups for filtering
GROUPS = [
    ('ALL',        'ALL SIGNS'),
    ('STOP',       'STOP'),
    ('YIELD',      'YIELD'),
    ('SPEED',      'SPEED LIMIT'),
    ('NO_ENTRY',   'NO ENTRY'),
    ('PEDESTRIAN', 'PEDESTRIAN'),
    ('WARNING',    'WARNING'),
]

# Map group keys to sign_type values
_GROUP_TO_TYPE = {
    'STOP': 'stop',
    'YIELD': 'yield',
    'SPEED': 'speed',
    'NO_ENTRY': 'no_entry',
    'PEDESTRIAN': 'pedestrian',
    'WARNING': 'warning',
}


def _filter_manifest():
    """Return only manifest entries whose PNG files exist on disk."""
    available = []
    for entry in SIGN_MANIFEST:
        name, stype, stem = entry
        path = os.path.join(ASSETS_DIR, f"{stem}.png")
        if os.path.exists(path):
            available.append(entry)
    return available


def _build_group_indices(manifest):
    """Build index lookup for each group."""
    all_sorted = sorted(range(len(manifest)), key=lambda i: manifest[i][0])
    indices = {'ALL': all_sorted}
    for key, stype in _GROUP_TO_TYPE.items():
        indices[key] = [i for i, entry in enumerate(manifest) if entry[1] == stype]
    return indices


def _load_sign_png(stem):
    """Load a sign PNG and return pixel rows as list of lists of RGB tuples."""
    path = os.path.join(ASSETS_DIR, f"{stem}.png")
    img = Image.open(path).convert('RGB')
    raw = img.tobytes()
    w = img.width
    pixels = []
    for y in range(img.height):
        row = []
        offset = y * w * 3
        for x in range(w):
            i = offset + x * 3
            row.append((raw[i], raw[i + 1], raw[i + 2]))
        pixels.append(row)
    return pixels


# Sign type display names for the label
_TYPE_LABELS = {
    'stop': 'STOP',
    'yield': 'YIELD',
    'speed': 'SPEED 50',
    'no_entry': 'NO ENTRY',
    'pedestrian': 'CROSSING',
    'warning': 'WARNING',
}


class Signs(Visual):
    name = "SIGNS"
    description = "Street signs of the world"
    category = "road_rail"

    def reset(self):
        self.time = 0.0
        self._manifest = _filter_manifest()
        if not self._manifest:
            self._manifest = SIGN_MANIFEST[:1]  # fallback
        self.group_indices = _build_group_indices(self._manifest)
        self.group_idx = 0
        self.sign_pos = 0
        self.auto_cycle = True
        self.cycle_timer = 0.0
        self.cycle_duration = 5.0
        self.overlay_timer = 0.0
        self.scroll_offset = 0.0
        self._pixel_cache = {}
        self._loaded = len(self._manifest) > 0

    def _current_list(self):
        key = GROUPS[self.group_idx][0]
        return self.group_indices.get(key, [])

    def _current_sign(self):
        lst = self._current_list()
        if not lst:
            return self._manifest[0]
        return self._manifest[lst[self.sign_pos % len(lst)]]

    def _get_pixels(self, stem):
        if stem not in self._pixel_cache:
            try:
                self._pixel_cache[stem] = _load_sign_png(stem)
            except Exception:
                return None
        return self._pixel_cache[stem]

    def handle_input(self, input_state):
        consumed = False
        if input_state.up_pressed:
            self.group_idx = (self.group_idx - 1) % len(GROUPS)
            self.sign_pos = 0
            self.cycle_timer = 0.0
            self.overlay_timer = 2.5
            consumed = True
        if input_state.down_pressed:
            self.group_idx = (self.group_idx + 1) % len(GROUPS)
            self.sign_pos = 0
            self.cycle_timer = 0.0
            self.overlay_timer = 2.5
            consumed = True
        if input_state.left_pressed:
            lst = self._current_list()
            if lst:
                self.sign_pos = (self.sign_pos - 1) % len(lst)
            self.cycle_timer = 0.0
            self.scroll_offset = 0.0
            consumed = True
        if input_state.right_pressed:
            lst = self._current_list()
            if lst:
                self.sign_pos = (self.sign_pos + 1) % len(lst)
            self.cycle_timer = 0.0
            self.scroll_offset = 0.0
            consumed = True
        if input_state.action_l or input_state.action_r:
            self.auto_cycle = not self.auto_cycle
            consumed = True
        return consumed

    def update(self, dt):
        self.time += dt
        self.scroll_offset += dt * 20
        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

        if self.auto_cycle:
            self.cycle_timer += dt
            if self.cycle_timer >= self.cycle_duration:
                self.cycle_timer = 0.0
                lst = self._current_list()
                if lst:
                    self.sign_pos = (self.sign_pos + 1) % len(lst)
                self.scroll_offset = 0.0

    def draw(self):
        d = self.display
        d.clear()

        if not self._loaded:
            d.draw_text_small(2, 28, "NO SIGNS", Colors.RED)
            d.draw_text_small(2, 36, "RUN BUILD", (180, 180, 180))
            return

        sign = self._current_sign()
        name, sign_type, stem = sign
        pixels = self._get_pixels(stem)

        if pixels is None:
            d.draw_text_small(2, 28, "MISSING", Colors.RED)
            return

        # Blit sign pixel data
        for y, row in enumerate(pixels):
            for x, color in enumerate(row):
                if color != (0, 0, 0):  # skip black background
                    d.set_pixel(SX + x, SY + y, color)

        # Country name + sign type label at bottom
        type_label = _TYPE_LABELS.get(sign_type, '')
        label = f"{name} {type_label}"
        max_chars = 14
        if len(label) > max_chars:
            padded = label + "    " + label
            total_w = len(label + "    ") * 4
            offset = int(self.scroll_offset) % total_w
            d.draw_text_small(2 - offset, LABEL_Y, padded, Colors.WHITE)
        else:
            d.draw_text_small(2, LABEL_Y, label, Colors.WHITE)

        # Counter: position in current list
        lst = self._current_list()
        if lst:
            pos = (self.sign_pos % len(lst)) + 1
            counter = f"{pos}/{len(lst)}"
            cw = len(counter) * 4
            d.draw_text_small(64 - cw - 1, 56, counter, (100, 100, 100))

        # Group overlay with fade
        if self.overlay_timer > 0:
            _, gname = GROUPS[self.group_idx]
            alpha = min(1.0, self.overlay_timer / 0.5)
            c = (int(200 * alpha), int(200 * alpha), int(200 * alpha))
            d.draw_text_small(2, 2, gname, c)
