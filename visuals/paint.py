"""
Paint - Pixel Art Editor
========================
MS Paint-style pixel art editor on a 32x32 canvas displayed at 2x zoom.
Create sprites, save/load PNG files.

Controls:
  Joystick      - Move cursor
  Button (hold) - Paint with current tool
  Button (tap)  - Open menu overlay (color/tool/file)
  Hold both 2s  - Exit to launcher
"""

import os
from collections import deque
from . import Visual, Display, Colors, GRID_SIZE

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

CANVAS_SIZE = 32
SAVE_DIR = os.path.expanduser("~/.led-arcade/paint")

# 24-color palette: 8 columns x 3 rows
PALETTE = [
    # Row 0 — Neutrals + browns
    (0, 0, 0), (80, 80, 80), (128, 128, 128), (192, 192, 192),
    (255, 255, 255), (139, 90, 43), (80, 40, 20), (210, 180, 140),
    # Row 1 — Warm + greens
    (139, 0, 0), (255, 0, 0), (255, 140, 0), (255, 255, 0),
    (0, 255, 0), (0, 160, 0), (0, 80, 0), (0, 128, 128),
    # Row 2 — Cool + pinks
    (0, 0, 139), (0, 0, 255), (0, 255, 255), (100, 149, 237),
    (128, 0, 128), (255, 0, 255), (255, 105, 180), (200, 162, 255),
]

PALETTE_COLS = 8
PALETTE_ROWS = 3

# Tools
TOOL_PENCIL = 0
TOOL_ERASER = 1
TOOL_FILL = 2
TOOL_EYEDROP = 3
TOOL_UNDO = 4
TOOL_REDO = 5
TOOL_SAVE = 6
TOOL_LOAD = 7
TOOL_CLEAR = 8
TOOL_STAMP = 9

TOOL_NAMES = ["PENCIL", "ERASER", "FILL", "EYEDROP",
              "UNDO", "REDO", "SAVE", "LOAD", "CLEAR", "STAMP"]
TOOL_INITIALS = ["P", "E", "F", "D", "U", "R", "S", "L", "C", "W"]

UNDO_MAX = 32

# ── Wonder Cabinet text stamp ─────────────────────────────────────
# Render directly at canvas resolution (1 font pixel = 1 canvas pixel).
# 3x5 font, 4px stride.  Center each word on the 32px-wide canvas.
# Vertical: WONDER at y=12, CABINET at y=18  (mirroring the standard
# screen positions 24/34 halved, with a 1px gap between the two words).
_FONT_3X5 = {
    'A': ['010', '101', '111', '101', '101'],
    'B': ['110', '101', '110', '101', '110'],
    'C': ['011', '100', '100', '100', '011'],
    'D': ['110', '101', '101', '101', '110'],
    'E': ['111', '100', '110', '100', '111'],
    'I': ['111', '010', '010', '010', '111'],
    'N': ['101', '111', '111', '111', '101'],
    'O': ['010', '101', '101', '101', '010'],
    'R': ['110', '101', '110', '101', '101'],
    'T': ['111', '010', '010', '010', '010'],
    'W': ['101', '101', '111', '111', '101'],
}


def _build_stamp(text, canvas_y):
    """Build set of canvas (x,y) for one line of text, centered on 32px."""
    width = len(text) * 4 - 1  # 3px per char + 1px gap, minus trailing
    x0 = (CANVAS_SIZE - width) // 2
    pixels = set()
    cx = x0
    for ch in text:
        glyph = _FONT_3X5.get(ch)
        if glyph:
            for row_idx, row in enumerate(glyph):
                for col_idx, pixel in enumerate(row):
                    if pixel == '1':
                        pixels.add((cx + col_idx, canvas_y + row_idx))
        cx += 4
    return pixels


TEMPLATE_PIXELS = frozenset(
    _build_stamp("WONDER", 12) | _build_stamp("CABINET", 18)
)

# Modes
MODE_DRAW = 0
MODE_MENU = 1
MODE_LOAD = 2


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _color_dist_sq(c1, c2):
    return (c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2 + (c1[2] - c2[2]) ** 2


class Paint(Visual):
    name = "PAINT"
    description = "Pixel art editor"
    category = "utility"
    custom_exit = True

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        # Canvas: 32x32, None = empty (black)
        self.canvas = [[None] * CANVAS_SIZE for _ in range(CANVAS_SIZE)]

        # Cursor
        self.cx = CANVAS_SIZE // 2
        self.cy = CANVAS_SIZE // 2
        self.blink_timer = 0.0

        # Current color and tool
        self.color_idx = 9  # red
        self.tool = TOOL_PENCIL

        # Mode
        self.mode = MODE_DRAW

        # Input timing (joystick repeat)
        self.move_timer = 0.0

        # Button hold/tap detection
        self.btn_hold_time = 0.0
        self.btn_was_held = False
        self.painting = False

        # Exit hold (both buttons)
        self.exit_hold = 0.0

        # Debounce: suppress button input briefly after mode switch
        self.debounce = 0.0

        # Menu cursor (indexes into PALETTE and TOOL_NAMES directly)
        self.menu_color = self.color_idx
        self.menu_tool = self.tool

        # Load browser
        self.load_files = []
        self.load_idx = 0

        # Undo/redo stacks
        self.undo_stack = []
        self.redo_stack = []
        self.stroke_saved = False  # True once snapshot taken for current stroke

        # Overlay text feedback
        self.overlay_text = ""
        self.overlay_timer = 0.0

    def handle_input(self, input_state) -> bool:
        self._input = input_state
        return True

    def update(self, dt: float):
        self.time += dt
        self.blink_timer += dt

        inp = getattr(self, '_input', None)
        if not inp:
            return

        # Exit hold: both buttons held 2s
        if inp.action_l_held and inp.action_r_held:
            self.exit_hold += dt
            if self.exit_hold >= 2.0:
                self.wants_exit = True
                return
        else:
            self.exit_hold = 0.0

        # Overlay timer countdown
        if self.overlay_timer > 0:
            self.overlay_timer -= dt

        # Debounce: skip button processing briefly after mode switch
        if self.debounce > 0:
            self.debounce -= dt
            self.btn_hold_time = 0.0
            self.btn_was_held = False
            self.painting = False
            return

        if self.mode == MODE_DRAW:
            self._update_draw(inp, dt)
        elif self.mode == MODE_MENU:
            self._update_menu(inp, dt)
        elif self.mode == MODE_LOAD:
            self._update_load(inp, dt)

    def _update_draw(self, inp, dt):
        # Joystick movement with repeat
        self.move_timer += dt
        rate = 0.06
        moved = False
        if inp.any_direction:
            if inp.up_pressed or inp.down_pressed or inp.left_pressed or inp.right_pressed:
                self.move_timer = 0.0
                moved = True
            elif self.move_timer >= rate:
                self.move_timer = 0.0
                moved = True
        if moved:
            self.cx = _clamp(self.cx + inp.dx, 0, CANVAS_SIZE - 1)
            self.cy = _clamp(self.cy + inp.dy, 0, CANVAS_SIZE - 1)

        # Button hold/tap detection (unified both buttons)
        btn_now = inp.action_l_held or inp.action_r_held
        if btn_now:
            self.btn_hold_time += dt
            if self.btn_hold_time >= 0.15:
                if not self.painting:
                    # Stroke start — snapshot for undo
                    if self.tool in (TOOL_PENCIL, TOOL_ERASER, TOOL_FILL, TOOL_EYEDROP):
                        self._snapshot()
                self.painting = True
        else:
            if self.btn_was_held and self.btn_hold_time < 0.15:
                # Tap → open menu
                self.mode = MODE_MENU
                self.debounce = 0.12
                self.menu_color = self.color_idx
                self.menu_tool = self.tool
            self.btn_hold_time = 0.0
            self.painting = False
        self.btn_was_held = btn_now

        # Apply tool while painting
        if self.painting:
            self._apply_tool()

    def _apply_tool(self):
        x, y = self.cx, self.cy
        if self.tool == TOOL_PENCIL:
            self.canvas[y][x] = PALETTE[self.color_idx]
        elif self.tool == TOOL_ERASER:
            self.canvas[y][x] = None
        elif self.tool == TOOL_FILL:
            self._flood_fill(x, y)
            # Only fill once per hold
            self.painting = False
        elif self.tool == TOOL_EYEDROP:
            pixel = self.canvas[y][x]
            if pixel:
                # Find closest palette color
                best = 0
                best_d = _color_dist_sq(pixel, PALETTE[0])
                for i in range(1, len(PALETTE)):
                    d = _color_dist_sq(pixel, PALETTE[i])
                    if d < best_d:
                        best_d = d
                        best = i
                self.color_idx = best
            self.tool = TOOL_PENCIL
            self.painting = False

    def _flood_fill(self, sx, sy):
        target = self.canvas[sy][sx]
        fill_color = PALETTE[self.color_idx]
        if target == fill_color:
            return
        queue = deque([(sx, sy)])
        visited = set()
        count = 0
        while queue and count < 1024:
            x, y = queue.popleft()
            if (x, y) in visited:
                continue
            if x < 0 or x >= CANVAS_SIZE or y < 0 or y >= CANVAS_SIZE:
                continue
            if self.canvas[y][x] != target:
                continue
            visited.add((x, y))
            self.canvas[y][x] = fill_color
            count += 1
            queue.append((x - 1, y))
            queue.append((x + 1, y))
            queue.append((x, y - 1))
            queue.append((x, y + 1))

    def _snapshot(self):
        """Save current canvas to undo stack, clear redo."""
        snap = [row[:] for row in self.canvas]
        self.undo_stack.append(snap)
        if len(self.undo_stack) > UNDO_MAX:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def _do_undo(self):
        if not self.undo_stack:
            self.overlay_text = "NO UNDO"
            self.overlay_timer = 1.5
            return
        self.redo_stack.append([row[:] for row in self.canvas])
        if len(self.redo_stack) > UNDO_MAX:
            self.redo_stack.pop(0)
        self.canvas = self.undo_stack.pop()
        self.overlay_text = "UNDO"
        self.overlay_timer = 1.0

    def _do_redo(self):
        if not self.redo_stack:
            self.overlay_text = "NO REDO"
            self.overlay_timer = 1.5
            return
        self.undo_stack.append([row[:] for row in self.canvas])
        if len(self.undo_stack) > UNDO_MAX:
            self.undo_stack.pop(0)
        self.canvas = self.redo_stack.pop()
        self.overlay_text = "REDO"
        self.overlay_timer = 1.0

    def _update_menu(self, inp, dt):
        # Left/Right cycles colors, Up/Down cycles tools
        if inp.left_pressed:
            self.menu_color = (self.menu_color - 1) % len(PALETTE)
        if inp.right_pressed:
            self.menu_color = (self.menu_color + 1) % len(PALETTE)
        if inp.up_pressed:
            self.menu_tool = (self.menu_tool - 1) % len(TOOL_NAMES)
        if inp.down_pressed:
            self.menu_tool = (self.menu_tool + 1) % len(TOOL_NAMES)

        # Button tap to confirm
        btn_tap = inp.action_l or inp.action_r
        if btn_tap:
            # Always apply the selected color
            self.color_idx = self.menu_color
            t = self.menu_tool
            if t == TOOL_UNDO:
                self._do_undo()
                self.mode = MODE_DRAW
                self.debounce = 0.12
            elif t == TOOL_REDO:
                self._do_redo()
                self.mode = MODE_DRAW
                self.debounce = 0.12
            elif t == TOOL_SAVE:
                self._do_save()
                self.mode = MODE_DRAW
                self.debounce = 0.12
            elif t == TOOL_LOAD:
                self._enter_load_browser()
            elif t == TOOL_CLEAR:
                self._snapshot()
                self.canvas = [[None] * CANVAS_SIZE for _ in range(CANVAS_SIZE)]
                self.overlay_text = "CLEARED!"
                self.overlay_timer = 1.5
                self.mode = MODE_DRAW
                self.debounce = 0.12
            elif t == TOOL_STAMP:
                self._snapshot()
                color = PALETTE[self.color_idx]
                for cx, cy in TEMPLATE_PIXELS:
                    if 0 <= cx < CANVAS_SIZE and 0 <= cy < CANVAS_SIZE:
                        self.canvas[cy][cx] = color
                self.overlay_text = "STAMPED!"
                self.overlay_timer = 1.0
                self.mode = MODE_DRAW
                self.debounce = 0.12
            else:
                # Selectable tool (pencil, eraser, fill, eyedrop)
                self.tool = t
                self.mode = MODE_DRAW
                self.debounce = 0.12

    def _update_load(self, inp, dt):
        if not self.load_files:
            # No files, go back
            self.mode = MODE_MENU
            self.debounce = 0.12
            return

        if inp.up_pressed:
            self.load_idx = (self.load_idx - 1) % len(self.load_files)
        if inp.down_pressed:
            self.load_idx = (self.load_idx + 1) % len(self.load_files)
        if inp.left_pressed:
            # Cancel
            self.mode = MODE_MENU
            self.debounce = 0.12
        btn_tap = inp.action_l or inp.action_r
        if btn_tap:
            self._do_load(self.load_files[self.load_idx])
            self.mode = MODE_DRAW
            self.debounce = 0.12

    def _enter_load_browser(self):
        self.load_files = []
        if os.path.isdir(SAVE_DIR):
            for f in sorted(os.listdir(SAVE_DIR)):
                if f.endswith(".png"):
                    self.load_files.append(f)
        if not self.load_files:
            self.overlay_text = "NO FILES"
            self.overlay_timer = 1.5
            self.mode = MODE_DRAW
            self.debounce = 0.12
            return
        self.load_idx = 0
        self.mode = MODE_LOAD
        self.debounce = 0.12

    def _do_save(self):
        if not HAS_PIL:
            self.overlay_text = "NO PIL!"
            self.overlay_timer = 1.5
            return
        os.makedirs(SAVE_DIR, exist_ok=True)
        # Find next number
        num = 1
        while os.path.exists(os.path.join(SAVE_DIR, f"paint_{num:03d}.png")):
            num += 1
        img = Image.new("RGB", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0))
        for y in range(CANVAS_SIZE):
            for x in range(CANVAS_SIZE):
                c = self.canvas[y][x]
                if c:
                    img.putpixel((x, y), c)
        path = os.path.join(SAVE_DIR, f"paint_{num:03d}.png")
        img.save(path)
        self.overlay_text = f"SAVED {num:03d}"
        self.overlay_timer = 1.5

    def _do_load(self, filename):
        self._snapshot()
        if not HAS_PIL:
            self.overlay_text = "NO PIL!"
            self.overlay_timer = 1.5
            return
        path = os.path.join(SAVE_DIR, filename)
        if not os.path.exists(path):
            self.overlay_text = "NOT FOUND"
            self.overlay_timer = 1.5
            return
        img = Image.open(path).convert("RGB")
        if img.size != (CANVAS_SIZE, CANVAS_SIZE):
            img = img.resize((CANVAS_SIZE, CANVAS_SIZE), Image.NEAREST)
        for y in range(CANVAS_SIZE):
            for x in range(CANVAS_SIZE):
                r, g, b = img.getpixel((x, y))
                if r == 0 and g == 0 and b == 0:
                    self.canvas[y][x] = None
                else:
                    self.canvas[y][x] = (r, g, b)
        self.overlay_text = "LOADED!"
        self.overlay_timer = 1.5

    # ── Drawing ──────────────────────────────────────────────────────

    def draw(self):
        self.display.clear()

        if self.mode == MODE_DRAW:
            self._draw_canvas()
            self._draw_hud()
            self._draw_cursor()
        elif self.mode == MODE_MENU:
            self._draw_menu()
        elif self.mode == MODE_LOAD:
            self._draw_load_browser()

        # Overlay feedback text
        if self.overlay_timer > 0 and self.overlay_text:
            alpha = min(1.0, self.overlay_timer / 0.5)
            c = int(255 * alpha)
            self.display.draw_text_small(2, 57, self.overlay_text, (c, c, 0))

    def _draw_canvas(self):
        for cy in range(CANVAS_SIZE):
            for cx in range(CANVAS_SIZE):
                pixel = self.canvas[cy][cx]
                if pixel:
                    # 2x zoom: each canvas pixel = 2x2 screen pixels
                    sx = cx * 2
                    sy = cy * 2
                    self.display.set_pixel(sx, sy, pixel)
                    self.display.set_pixel(sx + 1, sy, pixel)
                    self.display.set_pixel(sx, sy + 1, pixel)
                    self.display.set_pixel(sx + 1, sy + 1, pixel)

    def _draw_hud(self):
        # Color swatch in top-left: 3x3
        c = PALETTE[self.color_idx]
        for dy in range(3):
            for dx in range(3):
                self.display.set_pixel(dx, dy, c)
        # Tool initial in top-right
        letter = TOOL_INITIALS[self.tool]
        self.display.draw_text_small(60, 0, letter, (180, 180, 180))

    def _draw_cursor(self):
        # Blink at ~4Hz
        blink = int(self.blink_timer * 4) % 2 == 0
        if not blink:
            return
        sx = self.cx * 2
        sy = self.cy * 2
        cursor_color = (255, 255, 255)
        self.display.set_pixel(sx, sy, cursor_color)
        self.display.set_pixel(sx + 1, sy, cursor_color)
        self.display.set_pixel(sx, sy + 1, cursor_color)
        self.display.set_pixel(sx + 1, sy + 1, cursor_color)

    def _draw_menu(self):
        n_colors = len(PALETTE)
        # ── Color strip: 7 swatches, current in center (larger) ──
        # Neighbor swatches: 6x6 at y=4, center swatch: 10x10 at y=2
        center_slot = 3  # 0-indexed, 7 slots total
        for slot in range(7):
            idx = (self.menu_color + slot - center_slot) % n_colors
            c = PALETTE[idx]
            if slot == center_slot:
                # Current color: large swatch centered
                x0 = 27
                self.display.draw_rect(x0, 2, 10, 10, c)
                # White border
                for i in range(12):
                    self.display.set_pixel(x0 - 1 + i, 1, (255, 255, 255))
                    self.display.set_pixel(x0 - 1 + i, 12, (255, 255, 255))
                for i in range(11):
                    self.display.set_pixel(x0 - 1, 2 + i, (255, 255, 255))
                    self.display.set_pixel(x0 + 10, 2 + i, (255, 255, 255))
            else:
                # Neighbor swatch
                if slot < center_slot:
                    x0 = slot * 9
                else:
                    x0 = 27 + 12 + (slot - center_slot - 1) * 9
                dim = tuple(v // 2 for v in c)
                self.display.draw_rect(x0, 4, 7, 6, dim)

        # Left/right arrows
        self.display.draw_text_small(1, 14, "<", (120, 120, 120))
        self.display.draw_text_small(59, 14, ">", (120, 120, 120))

        # ── Separator ──
        for x in range(GRID_SIZE):
            self.display.set_pixel(x, 21, (40, 40, 40))

        # ── Tool: show prev / current / next ──
        n_tools = len(TOOL_NAMES)
        prev_t = (self.menu_tool - 1) % n_tools
        next_t = (self.menu_tool + 1) % n_tools

        # Previous tool (dim)
        self.display.draw_text_small(7, 25, TOOL_NAMES[prev_t], (60, 60, 60))
        # Current tool (bright, with arrow)
        cur_name = TOOL_NAMES[self.menu_tool]
        self.display.draw_text_small(2, 34, ">", (255, 255, 255))
        self.display.draw_text_small(7, 34, cur_name, (255, 255, 255))
        # Next tool (dim)
        self.display.draw_text_small(7, 43, TOOL_NAMES[next_t], (60, 60, 60))

        # Up/down arrows
        self.display.draw_text_small(55, 25, "^", (120, 120, 120))
        self.display.draw_text_small(55, 43, "v", (120, 120, 120))

    def _draw_load_browser(self):
        self.display.draw_text_small(2, 1, "LOAD FILE", (200, 200, 200))
        # Separator
        for x in range(GRID_SIZE):
            self.display.set_pixel(x, 8, (40, 40, 40))

        visible = 7
        total = len(self.load_files)
        scroll = max(0, min(self.load_idx - visible // 2, total - visible))

        y = 10
        for i in range(scroll, min(scroll + visible, total)):
            name = self.load_files[i]
            # Strip .png, show just the name
            label = name[:-4] if name.endswith(".png") else name
            if i == self.load_idx:
                self.display.draw_text_small(2, y, ">", (255, 255, 255))
                self.display.draw_text_small(7, y, label, (255, 255, 255))
            else:
                self.display.draw_text_small(7, y, label, (100, 100, 100))
            y += 7

        # Hint at bottom
        self.display.draw_text_small(2, 57, "< CANCEL", (80, 80, 80))
