"""
COINS OF THE WORLD -- Historic Coinage on 64x64 LED Matrix
============================================================
29 historic coins from world civilizations spanning ancient to modern eras.
Photographs sourced from Wikimedia Commons (CC BY-SA / CC0) and the
Metropolitan Museum of Art Open Access API (CC0).

Images are pre-built by tools/build_coins.py.

Controls:
  Up/Down    - Cycle eras (ANCIENT / MEDIEVAL / MODERN)
  Left/Right - Cycle coins within era
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

# Pre-loaded pixel data for emulator mode
_COINS_ATLAS = globals().get('_COINS_PIXELS', {})

try:
    _ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    _ROOT = ""

# ── Constants ────────────────────────────────────────────────────

ERAS = ['ANCIENT', 'MEDIEVAL', 'MODERN']
ERA_COLORS = {
    'ANCIENT':  (220, 190, 100),
    'MEDIEVAL': (180, 160, 120),
    'MODERN':   (160, 180, 210),
}

_CHAR_W = 4
_VISIBLE_W = GRID_SIZE - 4
_SCROLL_SPEED = 24
_SCROLL_PAUSE = 0.6

_DISPLAY_DURATION = 8.0
_CROSSFADE_TIME = 0.6
_IDLE_OVERLAY_HOLD = 4.0
_IDLE_OVERLAY_FADE_IN = 0.4
_IDLE_OVERLAY_FADE_OUT = 0.8

# Overlay text positions
_LINE_Y_TITLE = 2
_LINE_Y_SUB = 9
_LINE_Y_NOTE = 52
_LINE_Y_COUNTER = 58


def _strip_accents(s):
    nfkd = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))


# ── Visual class ──────────────────────────────────────────────────

class Coins(Visual):
    """Historic coins of the world displayed as photographs on 64x64 LED."""

    name = "COINS"
    description = "Historic coins of the world"
    category = "culture"

    def reset(self):
        self.time = 0.0
        self._coins = []           # full manifest
        self._era_coins = {}       # {era: [indices into _coins]}
        self._era_idx = 0
        self._coin_idx = 0         # index within current era
        self._pixels = None
        self._prev_pixels = None
        self._fade = 1.0
        self._timer = 0.0

        # Overlay
        self._show_overlay = False
        self._overlay_alpha = 0.0
        self._overlay_time = 0.0
        self._idle_overlay_timer = 0.0

        # Era overlay (brief flash when switching eras)
        self._era_overlay_timer = 0.0

        # Edge detection
        self._prev_left = False
        self._prev_right = False
        self._prev_up = False
        self._prev_down = False

        self._load_manifest()
        if self._coins:
            self._era_idx = 0
            era = ERAS[self._era_idx]
            if self._era_coins.get(era):
                self._coin_idx = random.randint(
                    0, len(self._era_coins[era]) - 1)
            self._load_coin()

    def _load_manifest(self):
        """Load coin list from JSON manifest."""
        if _ROOT:
            path = os.path.join(_ROOT, "tools", "coins_manifest.json")
            if os.path.exists(path):
                with open(path) as f:
                    self._coins = json.load(f)
                # Build per-era index
                self._era_coins = {era: [] for era in ERAS}
                for i, c in enumerate(self._coins):
                    era = c.get("era", "ANCIENT")
                    if era in self._era_coins:
                        self._era_coins[era].append(i)
                return
        # Emulator mode: build from atlas keys
        if _COINS_ATLAS:
            self._coins = [{"id": k, "title": k.replace("_", " ").title(),
                            "era": "ANCIENT"}
                           for k in _COINS_ATLAS]
            self._era_coins = {"ANCIENT": list(range(len(self._coins))),
                               "MEDIEVAL": [], "MODERN": []}

    def _current_coin(self):
        """Return the current coin dict."""
        if not self._coins:
            return None
        era = ERAS[self._era_idx]
        indices = self._era_coins.get(era, [])
        if not indices:
            return None
        idx = indices[self._coin_idx % len(indices)]
        return self._coins[idx]

    def _load_coin(self):
        """Load current coin's pixel data."""
        self._prev_pixels = self._pixels
        self._pixels = None
        self._fade = 0.0

        coin = self._current_coin()
        if not coin:
            return

        cid = coin["id"]

        # Emulator mode: pre-loaded atlas
        atlas_entry = _COINS_ATLAS.get(cid)
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
        path = os.path.join(_ROOT, "assets", "coins", f"{cid}.png")
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
        up_edge = input_state.up and not self._prev_up
        down_edge = input_state.down and not self._prev_down
        left_edge = input_state.left and not self._prev_left
        right_edge = input_state.right and not self._prev_right
        self._prev_up = input_state.up
        self._prev_down = input_state.down
        self._prev_left = input_state.left
        self._prev_right = input_state.right

        # Up/Down: cycle eras
        if up_edge or down_edge:
            d = -1 if up_edge else 1
            self._era_idx = (self._era_idx + d) % len(ERAS)
            self._coin_idx = 0
            self._load_coin()
            self._timer = 0.0
            self._era_overlay_timer = 1.5
            self._idle_overlay_timer = 0.0
            if self._show_overlay:
                self._overlay_time = 0.0
            return True
        if input_state.up or input_state.down:
            return True

        # Left/Right: cycle coins within era
        if left_edge or right_edge:
            era = ERAS[self._era_idx]
            n = len(self._era_coins.get(era, []))
            if n > 0:
                if right_edge:
                    self._coin_idx = (self._coin_idx + 1) % n
                else:
                    self._coin_idx = (self._coin_idx - 1) % n
                self._load_coin()
                self._timer = 0.0
                self._idle_overlay_timer = 0.0
                if self._show_overlay:
                    self._overlay_time = 0.0
            return True
        if input_state.left or input_state.right:
            return True

        # Action: toggle overlay
        if input_state.action_l or input_state.action_r:
            self._show_overlay = not self._show_overlay
            if self._show_overlay:
                self._overlay_time = 0.0
            return True

        return False

    def update(self, dt):
        self.time += dt

        # Crossfade
        if self._fade < 1.0:
            self._fade = min(1.0, self._fade + dt / _CROSSFADE_TIME)

        # Era overlay countdown
        if self._era_overlay_timer > 0:
            self._era_overlay_timer = max(0.0, self._era_overlay_timer - dt)

        # Auto-advance within era
        era = ERAS[self._era_idx]
        era_coins = self._era_coins.get(era, [])
        if len(era_coins) > 1:
            self._timer += dt
            if self._timer >= _DISPLAY_DURATION:
                self._coin_idx = (self._coin_idx + 1) % len(era_coins)
                self._load_coin()
                self._timer = 0.0
                self._overlay_time = 0.0
                if not self._show_overlay:
                    self._idle_overlay_timer = (_IDLE_OVERLAY_FADE_IN
                                                + _IDLE_OVERLAY_HOLD
                                                + _IDLE_OVERLAY_FADE_OUT)

        # Idle overlay countdown
        if self._idle_overlay_timer > 0:
            self._idle_overlay_timer = max(0, self._idle_overlay_timer - dt)

        # Compute effective overlay alpha
        toggle_target = 1.0 if self._show_overlay else 0.0
        toggle_alpha = self._overlay_alpha
        if toggle_alpha < toggle_target:
            toggle_alpha = min(toggle_target, toggle_alpha + dt / 0.3)
        elif toggle_alpha > toggle_target:
            toggle_alpha = max(toggle_target, toggle_alpha - dt / 0.3)

        # Idle fade
        idle_alpha = 0.0
        remaining = self._idle_overlay_timer
        total = _IDLE_OVERLAY_FADE_IN + _IDLE_OVERLAY_HOLD + _IDLE_OVERLAY_FADE_OUT
        if remaining > 0:
            elapsed = total - remaining
            if elapsed < _IDLE_OVERLAY_FADE_IN:
                idle_alpha = elapsed / _IDLE_OVERLAY_FADE_IN
            elif remaining > _IDLE_OVERLAY_FADE_OUT:
                idle_alpha = 1.0
            else:
                idle_alpha = remaining / _IDLE_OVERLAY_FADE_OUT

        self._overlay_alpha = max(toggle_alpha, idle_alpha)
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

    def draw(self):
        d = self.display
        d.clear()

        if not self._pixels:
            d.draw_text_small(2, 24, "NO IMAGES", Colors.RED)
            d.draw_text_small(2, 32, "RUN:", Colors.RED)
            d.draw_text_small(2, 40, "BUILD_COINS", Colors.RED)
            return

        # Draw coin image with crossfade
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

        # Era overlay (brief flash when switching eras)
        if self._era_overlay_timer > 0:
            alpha = min(1.0, self._era_overlay_timer / 0.5)
            era_name = ERAS[self._era_idx]
            ec = ERA_COLORS.get(era_name, (180, 180, 180))
            oc = tuple(int(c * alpha) for c in ec)
            # Dim band behind text
            bg_alpha = alpha * 0.7
            for y in range(24, 34):
                for x in range(GRID_SIZE):
                    pr, pg, pb = self._pixels[y][x] if self._pixels else (0, 0, 0)
                    d.set_pixel(x, y, (int(pr * (1 - bg_alpha)),
                                       int(pg * (1 - bg_alpha)),
                                       int(pb * (1 - bg_alpha))))
            ew = len(era_name) * 5
            ex = max(0, (GRID_SIZE - ew) // 2)
            d.draw_text_small(ex, 27, era_name, oc)

        # Info overlay
        alpha = self._overlay_alpha
        if alpha < 0.01:
            return

        coin = self._current_coin()
        if not coin:
            return

        # Dim strips at top and bottom
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
        title = _strip_accents(coin.get("title", coin["id"]))
        tc = (int(255 * alpha), int(255 * alpha), int(255 * alpha))
        self._scroll_text(_LINE_Y_TITLE, title.upper(), tc)

        # Culture + date
        culture = coin.get("culture", "")
        date = coin.get("date", "")
        sub = f"{culture}  {date}" if culture and date else culture or date
        sc = (int(180 * alpha), int(170 * alpha), int(120 * alpha))
        self._scroll_text(_LINE_Y_SUB, sub.upper(), sc)

        # Note at bottom (historical significance)
        note = _strip_accents(coin.get("note", ""))
        if note:
            nc = (int(160 * alpha), int(160 * alpha), int(160 * alpha))
            self._scroll_text(_LINE_Y_NOTE, note.upper(), nc)

        # Counter
        era = ERAS[self._era_idx]
        era_coins = self._era_coins.get(era, [])
        if len(era_coins) > 1:
            counter = f"{self._coin_idx + 1}/{len(era_coins)} {era}"
            cc = (int(100 * alpha), int(100 * alpha), int(100 * alpha))
            d.draw_text_small(2, _LINE_Y_COUNTER, counter, cc)
