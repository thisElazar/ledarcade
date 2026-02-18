"""
Pottery
=======
World ceramic traditions from the Metropolitan Museum of Art Open Access
collection (CC0 public domain).  Displays 64×64 photographs of real
vessels with metadata overlay (title, culture, date, medium/technique).

Images are pre-built by tools/build_pottery.py from the Met's API.

Controls:
  Left/Right - Cycle vessels
  Action     - Toggle info overlay
"""

import json
import os
import random
import unicodedata
from . import Visual, Display, Colors, GRID_SIZE

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Pre-loaded pixel data for emulator mode (injected before this module loads)
_POTTERY_ATLAS = globals().get('_POTTERY_PIXELS', {})

try:
    _ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    _ROOT = ""

# ── Layout constants ──────────────────────────────────────────────

_CHAR_W = 4
_VISIBLE_W = GRID_SIZE - 4       # usable text width (2px margin each side)
_SCROLL_SPEED = 24                # pixels per second
_SCROLL_PAUSE = 0.6              # seconds before scroll starts

_DISPLAY_DURATION = 8.0          # seconds before auto-advance
_CROSSFADE_TIME = 0.6            # seconds for crossfade between vessels

# Overlay text layout (from bottom)
_LINE_Y_1 = 2                    # title
_LINE_Y_2 = 9                    # culture + date
_LINE_Y_3 = 52                   # medium line 1
_LINE_Y_4 = 58                   # medium line 2 / counter


def _strip_accents(s):
    nfkd = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))


# ── Visual class ──────────────────────────────────────────────────

class Pottery(Visual):
    name = "POTTERY"
    description = "World ceramic traditions"
    category = "culture"

    def reset(self):
        self.time = 0.0
        self._vessels = []
        self._idx = 0
        self._pixels = None        # current vessel: list of list of (r,g,b)
        self._prev_pixels = None   # previous vessel for crossfade
        self._fade = 1.0           # 0→1 crossfade progress
        self._timer = 0.0          # auto-advance timer

        # Overlay
        self._show_overlay = True
        self._overlay_alpha = 1.0
        self._overlay_time = 0.0
        self._overlay_hold = 3.0   # auto-hide after 3s on first show

        # Edge detection for L/R
        self._prev_left = False
        self._prev_right = False

        self._load_manifest()
        if self._vessels:
            self._idx = random.randint(0, len(self._vessels) - 1)
            self._load_vessel()

    def _load_manifest(self):
        """Load vessel list from JSON manifest."""
        if _ROOT:
            path = os.path.join(_ROOT, "tools", "pottery_manifest.json")
            if os.path.exists(path):
                with open(path) as f:
                    self._vessels = json.load(f)
                return
        # Emulator mode: build from atlas keys
        if _POTTERY_ATLAS:
            self._vessels = [{"id": k, "title": k.replace("_", " ").title()}
                             for k in _POTTERY_ATLAS]

    def _load_vessel(self):
        """Load current vessel's pixel data."""
        self._prev_pixels = self._pixels
        self._pixels = None
        self._fade = 0.0
        if not self._vessels:
            return

        vid = self._vessels[self._idx]["id"]

        # Emulator mode: pre-loaded atlas
        atlas_entry = _POTTERY_ATLAS.get(vid)
        if atlas_entry and isinstance(atlas_entry, dict):
            import base64
            d = base64.b64decode(atlas_entry["data"])
            self._pixels = [
                [(d[(y * GRID_SIZE + x) * 3],
                  d[(y * GRID_SIZE + x) * 3 + 1],
                  d[(y * GRID_SIZE + x) * 3 + 2])
                 for x in range(GRID_SIZE)]
                for y in range(GRID_SIZE)
            ]
            return

        # Hardware mode: load PNG via PIL
        if not HAS_PIL or not _ROOT:
            return
        path = os.path.join(_ROOT, "assets", "pottery", f"{vid}.png")
        if not os.path.exists(path):
            return
        img = Image.open(path).convert("RGB")
        w, h = img.size
        if w != GRID_SIZE or h != GRID_SIZE:
            img = img.resize((GRID_SIZE, GRID_SIZE), Image.NEAREST)
        self._pixels = [
            [img.getpixel((x, y)) for x in range(GRID_SIZE)]
            for y in range(GRID_SIZE)
        ]

    def handle_input(self, input_state):
        left_edge = input_state.left and not self._prev_left
        right_edge = input_state.right and not self._prev_right
        self._prev_left = input_state.left
        self._prev_right = input_state.right

        if left_edge or right_edge:
            if self._vessels:
                if right_edge:
                    self._idx = (self._idx + 1) % len(self._vessels)
                else:
                    self._idx = (self._idx - 1) % len(self._vessels)
                self._load_vessel()
                self._timer = 0.0
                self._show_overlay = True
                self._overlay_hold = 3.0
                self._overlay_time = 0.0
            return True
        if input_state.left or input_state.right:
            return True

        if input_state.action_l or input_state.action_r:
            self._show_overlay = not self._show_overlay
            if self._show_overlay:
                self._overlay_time = 0.0
                self._overlay_hold = 0.0  # manual toggle stays on
            return True

        return False

    def update(self, dt):
        self.time += dt

        # Crossfade
        if self._fade < 1.0:
            self._fade = min(1.0, self._fade + dt / _CROSSFADE_TIME)

        # Auto-advance
        if self._vessels and len(self._vessels) > 1:
            self._timer += dt
            if self._timer >= _DISPLAY_DURATION:
                self._idx = (self._idx + 1) % len(self._vessels)
                self._load_vessel()
                self._timer = 0.0
                self._show_overlay = True
                self._overlay_hold = 3.0
                self._overlay_time = 0.0

        # Auto-hide overlay
        if self._overlay_hold > 0:
            self._overlay_hold -= dt
            if self._overlay_hold <= 0:
                self._show_overlay = False

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
            offset = max_offset - int(
                (t - 2 * _SCROLL_PAUSE - scroll_time) * _SCROLL_SPEED)
        offset = max(0, min(int(max_offset), offset))
        self.display.draw_text_small(2 - offset, y, text, color)

    def _split_medium(self, medium):
        """Split medium string into two lines that fit the display."""
        max_chars = _VISIBLE_W // _CHAR_W
        if len(medium) <= max_chars:
            return medium, ""
        # Try to split at a natural break near the midpoint
        mid = max_chars
        for sep in ("; ", ", ", " (", " "):
            pos = medium.rfind(sep, 0, mid + 2)
            if pos > max_chars // 3:
                return medium[:pos + len(sep)].rstrip(), medium[pos + len(sep):]
        return medium[:mid], medium[mid:]

    def draw(self):
        d = self.display
        d.clear()

        if not self._pixels:
            d.draw_text_small(2, 28, "NO IMAGES", Colors.RED)
            d.draw_text_small(2, 36, "RUN BUILD", Colors.RED)
            return

        # Draw vessel image with crossfade
        f = self._fade
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                r, g, b = self._pixels[y][x]
                if f < 1.0 and self._prev_pixels:
                    pr, pg, pb = self._prev_pixels[y][x]
                    r = int(pr + (r - pr) * f)
                    g = int(pg + (g - pg) * f)
                    b = int(pb + (b - pb) * f)
                d.set_pixel(x, y, (r, g, b))

        # Info overlay
        alpha = self._overlay_alpha
        if alpha < 0.01 or not self._vessels:
            return

        vessel = self._vessels[self._idx]

        # Dim strips at top and bottom for text readability
        for y in range(0, 16):
            fade = alpha * min(1.0, (16 - y) / 8.0)
            if fade < 0.01:
                continue
            for x in range(GRID_SIZE):
                r, g, b = self._pixels[y][x]
                f2 = 0.65 * fade
                d.set_pixel(x, y, (int(r * (1 - f2)),
                                   int(g * (1 - f2)),
                                   int(b * (1 - f2))))
        for y in range(48, GRID_SIZE):
            fade = alpha * min(1.0, (y - 48) / 8.0)
            if fade < 0.01:
                continue
            for x in range(GRID_SIZE):
                r, g, b = self._pixels[y][x]
                f2 = 0.65 * fade
                d.set_pixel(x, y, (int(r * (1 - f2)),
                                   int(g * (1 - f2)),
                                   int(b * (1 - f2))))

        # Title
        title = _strip_accents(vessel.get("title", vessel["id"]))
        tc = (int(255 * alpha), int(255 * alpha), int(255 * alpha))
        self._scroll_text(_LINE_Y_1, title.upper(), tc)

        # Culture + date
        culture = vessel.get("culture", "")
        date = vessel.get("date", "")
        sub = f"{culture}  {date}" if culture and date else culture or date
        sc = (int(180 * alpha), int(170 * alpha), int(120 * alpha))
        self._scroll_text(_LINE_Y_2, sub.upper(), sc)

        # Medium (technique/glaze info) at bottom
        medium = _strip_accents(vessel.get("medium", ""))
        if medium:
            mc = (int(160 * alpha), int(160 * alpha), int(160 * alpha))
            line1, line2 = self._split_medium(medium.upper())
            self._scroll_text(_LINE_Y_3, line1, mc)
            if line2:
                self._scroll_text(_LINE_Y_4, line2, mc)
            elif len(self._vessels) > 1:
                counter = f"{self._idx + 1}/{len(self._vessels)}"
                cc = (int(100 * alpha), int(100 * alpha), int(100 * alpha))
                d.draw_text_small(2, _LINE_Y_4, counter, cc)
        elif len(self._vessels) > 1:
            counter = f"{self._idx + 1}/{len(self._vessels)}"
            cc = (int(100 * alpha), int(100 * alpha), int(100 * alpha))
            d.draw_text_small(2, _LINE_Y_3, counter, cc)
