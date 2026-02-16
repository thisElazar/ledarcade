"""
Naturalist Plate Collections
=============================
Vertical-panning plate visuals for scientific illustration collections.
Each collection (Haeckel, Audubon, Merian) is a single visual that cycles
through its plates with left/right, auto-panning vertically.

Controls:
  Left/Right     - Cycle between plates
  Up/Down held   - Manual pan
  Action L/R     - Toggle title overlay
"""

import os
import json
import unicodedata
from . import Visual, Display, Colors, GRID_SIZE


def _strip_accents(s):
    """Replace accented characters with ASCII equivalents for LED font."""
    nfkd = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))


try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Pre-loaded pixel data for emulator mode (injected before this module loads)
_HAECKEL_ATLAS = globals().get('_HAECKEL_PIXELS', {})
_AUDUBON_ATLAS = globals().get('_AUDUBON_PIXELS', {})
_MERIAN_ATLAS = globals().get('_MERIAN_PIXELS', {})

try:
    _ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    _ROOT = ""

# Overlay layout constants
_CHAR_W = 4
_VISIBLE_W = GRID_SIZE - 4   # usable text width (2px margin each side)
_SCROLL_SPEED = 24            # pixels per second
_SCROLL_PAUSE = 0.6           # seconds before scroll starts

# Overlay text: 2 lines — title and counter
_LINE_Y_TITLE = GRID_SIZE - 13  # title line
_LINE_Y_COUNT = GRID_SIZE - 6   # counter line
_DIM_TOP = _LINE_Y_TITLE - 3

# Pan speeds
_AUTO_PAN_SPEED = 35.0   # pixels per second
_MANUAL_PAN_SPEED = 60.0  # pixels per second
_PAUSE_DURATION = 1.5     # seconds to pause at top/bottom


class _PlatesBase(Visual):
    """Base class for plate collection visuals."""

    category = "nature"
    _collection = ""     # e.g. "haeckel"
    _manifest_file = ""  # e.g. "haeckel_plates.json"
    _atlas_ref = None    # reference to atlas dict

    def reset(self):
        self._plates = []       # list of {"id": ..., "title": ...}
        self._plate_idx = 0
        self.pixels = None
        self._img_height = GRID_SIZE

        # Pan state
        self._pan_y = 0.0
        self._pan_dir = 1       # +1 = down, -1 = up
        self._manual_pan = False
        self._pause_timer = _PAUSE_DURATION  # start paused at top

        # Overlay state
        self._show_overlay = False
        self._overlay_alpha = 0.0
        self._overlay_time = 0.0

        # Edge detection
        self._prev_left = False
        self._prev_right = False

        self._load_manifest()
        if self._plates:
            self._load_plate()

    def _load_manifest(self):
        """Load plate list from JSON manifest."""
        # Try filesystem first (hardware mode)
        if _ROOT:
            path = os.path.join(_ROOT, "tools", self._manifest_file)
            if os.path.exists(path):
                with open(path) as f:
                    self._plates = json.load(f)
                return
        # Emulator mode: build list from atlas keys
        atlas = self._get_atlas()
        if atlas:
            self._plates = [{"id": k, "title": k.replace("_", " ").title()}
                            for k in atlas]

    def _get_atlas(self):
        """Get the atlas dict for this collection."""
        if self._collection == "haeckel":
            return _HAECKEL_ATLAS
        elif self._collection == "audubon":
            return _AUDUBON_ATLAS
        elif self._collection == "merian":
            return _MERIAN_ATLAS
        return {}

    def _load_plate(self):
        """Load current plate's pixel data."""
        self.pixels = None
        if not self._plates:
            return

        pid = self._plates[self._plate_idx]["id"]
        atlas = self._get_atlas()

        # Emulator mode: decode from pre-loaded base64 atlas
        atlas_entry = atlas.get(pid)
        if atlas_entry and isinstance(atlas_entry, dict):
            import base64
            h = atlas_entry["h"]
            d = base64.b64decode(atlas_entry["data"])
            self._img_height = h
            self.pixels = [
                [(d[(y * GRID_SIZE + x) * 3],
                  d[(y * GRID_SIZE + x) * 3 + 1],
                  d[(y * GRID_SIZE + x) * 3 + 2])
                 for x in range(GRID_SIZE)]
                for y in range(h)
            ]
            return

        # Hardware mode: load PNG via PIL
        if not HAS_PIL or not _ROOT:
            return
        path = os.path.join(_ROOT, "assets", self._collection, f"{pid}.png")
        if not os.path.exists(path):
            return
        img = Image.open(path).convert("RGB")
        w, h = img.size
        if w != GRID_SIZE:
            h = int(h * GRID_SIZE / w)
            img = img.resize((GRID_SIZE, h), Image.NEAREST)
        self._img_height = h
        self.pixels = [
            [img.getpixel((x, y)) for x in range(GRID_SIZE)]
            for y in range(h)
        ]

    def _reset_pan(self):
        """Reset pan to top with initial pause."""
        self._pan_y = 0.0
        self._pan_dir = 1
        self._manual_pan = False
        self._pause_timer = _PAUSE_DURATION

    def handle_input(self, input_state):
        # Left/Right: cycle plates (edge-triggered)
        left_edge = input_state.left and not self._prev_left
        right_edge = input_state.right and not self._prev_right
        self._prev_left = input_state.left
        self._prev_right = input_state.right

        if left_edge or right_edge:
            if self._plates:
                if right_edge:
                    self._plate_idx = (self._plate_idx + 1) % len(self._plates)
                else:
                    self._plate_idx = (self._plate_idx - 1) % len(self._plates)
                self._load_plate()
                self._reset_pan()
                self._overlay_time = 0.0
            return True
        if input_state.left or input_state.right:
            return True  # consume held state

        # Up/Down held: manual pan
        if input_state.up or input_state.down:
            self._manual_pan = True
            max_y = max(0, self._img_height - GRID_SIZE)
            if input_state.up:
                self._pan_y = max(0, self._pan_y - _MANUAL_PAN_SPEED * 0.016)
            if input_state.down:
                self._pan_y = min(max_y, self._pan_y + _MANUAL_PAN_SPEED * 0.016)
            return True

        # Release from manual pan: resume auto from current position
        if self._manual_pan:
            self._manual_pan = False
            self._pause_timer = 0  # resume immediately

        # Action: toggle overlay
        if input_state.action_l or input_state.action_r:
            self._show_overlay = not self._show_overlay
            if self._show_overlay:
                self._overlay_time = 0.0
            return True

        return False

    def update(self, dt):
        self.time += dt

        # Auto-pan when not manually controlled
        if not self._manual_pan and self.pixels:
            max_y = max(0, self._img_height - GRID_SIZE)
            if max_y > 0:
                if self._pause_timer > 0:
                    self._pause_timer -= dt
                else:
                    self._pan_y += self._pan_dir * _AUTO_PAN_SPEED * dt
                    # Hit bottom
                    if self._pan_y >= max_y:
                        self._pan_y = max_y
                        self._pan_dir = -1
                        self._pause_timer = _PAUSE_DURATION
                    # Hit top
                    elif self._pan_y <= 0:
                        self._pan_y = 0
                        self._pan_dir = 1
                        self._pause_timer = _PAUSE_DURATION

        # Overlay fade
        target = 1.0 if self._show_overlay else 0.0
        if self._overlay_alpha < target:
            self._overlay_alpha = min(target, self._overlay_alpha + dt / 0.3)
        elif self._overlay_alpha > target:
            self._overlay_alpha = max(target, self._overlay_alpha - dt / 0.3)
        if self._overlay_alpha > 0.01:
            self._overlay_time += dt

    def _scroll_text(self, y, text, color):
        """Draw text with bounce-scroll for long strings."""
        text_w = len(text) * _CHAR_W
        if text_w <= _VISIBLE_W:
            self.display.draw_text_small(2, y, text, color)
            return
        max_offset = text_w - _VISIBLE_W
        scroll_time = max_offset / _SCROLL_SPEED
        cycle = _SCROLL_PAUSE + scroll_time + _SCROLL_PAUSE + scroll_time
        t = self._overlay_time % cycle
        if t < _SCROLL_PAUSE:
            offset = 0
        elif t < _SCROLL_PAUSE + scroll_time:
            offset = int((t - _SCROLL_PAUSE) * _SCROLL_SPEED)
        elif t < _SCROLL_PAUSE + scroll_time + _SCROLL_PAUSE:
            offset = max_offset
        else:
            offset = max_offset - int((t - 2 * _SCROLL_PAUSE - scroll_time) * _SCROLL_SPEED)
        offset = max(0, min(int(max_offset), offset))
        self.display.draw_text_small(2 - offset, y, text, color)

    def draw(self):
        if not self.pixels:
            self.display.clear()
            self.display.draw_text_small(2, 28, "NO IMAGE", Colors.RED)
            return

        # Draw 64x64 viewport from the tall image, offset by pan_y
        y_off = int(self._pan_y)
        for y in range(GRID_SIZE):
            src_y = y_off + y
            if src_y < len(self.pixels):
                for x in range(GRID_SIZE):
                    self.display.set_pixel(x, y, self.pixels[src_y][x])
            else:
                for x in range(GRID_SIZE):
                    self.display.set_pixel(x, y, (0, 0, 0))

        # Overlay
        alpha = self._overlay_alpha
        if alpha > 0.01 and self._plates:
            # Dim bottom strip with gradient
            for y in range(_DIM_TOP, GRID_SIZE):
                fade = alpha * min(1.0, (y - _DIM_TOP) / 5.0)
                src_y = int(self._pan_y) + y
                for x in range(GRID_SIZE):
                    if src_y < len(self.pixels):
                        r, g, b = self.pixels[src_y][x]
                    else:
                        r, g, b = 0, 0, 0
                    f = 0.7 * fade
                    self.display.set_pixel(x, y, (
                        int(r * (1 - f)),
                        int(g * (1 - f)),
                        int(b * (1 - f)),
                    ))

            # Title and counter
            plate = self._plates[self._plate_idx]
            title = plate.get("title", plate["id"])
            tc = (int(255 * alpha), int(255 * alpha), int(255 * alpha))
            cc = (int(180 * alpha), int(160 * alpha), int(80 * alpha))
            self._scroll_text(_LINE_Y_TITLE, title, tc)
            counter = f"{self._plate_idx + 1}/{len(self._plates)}"
            self.display.draw_text_small(2, _LINE_Y_COUNT, counter, cc)


class Haeckel(_PlatesBase):
    name = "HAECKEL"
    description = "Kunstformen der Natur"
    _collection = "haeckel"
    _manifest_file = "haeckel_plates.json"


class Audubon(_PlatesBase):
    name = "AUDUBON"
    description = "Birds of America"
    _collection = "audubon"
    _manifest_file = "audubon_plates.json"


class Merian(_PlatesBase):
    name = "MERIAN"
    description = "Metamorphosis Insectorum"
    _collection = "merian"
    _manifest_file = "merian_plates.json"
