"""
Paint GIF - Frame-by-Frame Animation Editor
============================================
Create short frame-by-frame animations and export as GIF.
64x64 pixel art, per-frame undo/redo, onion skin, preview playback.

Controls:
  Joystick      - Move cursor
  Button (hold) - Paint with current tool
  Button (tap)  - Open menu overlay
  Hold both 2s  - Exit to launcher
"""

import os
from collections import deque
from . import Visual, Display, Colors, GRID_SIZE

from .paint import (
    PALETTE, PALETTE_COLS, PALETTE_ROWS,
    CANVAS_SIZE, UNDO_MAX,
    TOOL_PENCIL, TOOL_MARKER, TOOL_BRUSH, TOOL_ERASER, TOOL_FILL, TOOL_EYEDROP,
    _TOOL_BRUSH, _clamp, _color_dist_sq,
)

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

SAVE_DIR = os.path.expanduser("~/.led-arcade/paint_gif")

# Extended tool list (19 tools)
# 0-5 reuse paint.py constants
TOOL_UNDO = 6
TOOL_REDO = 7
TOOL_PREV = 8
TOOL_NEXT = 9
TOOL_ADD = 10
TOOL_DUP = 11
TOOL_DEL = 12
TOOL_ONION = 13
TOOL_PLAY = 14
TOOL_EXPORT = 15
TOOL_CLEAR = 16
TOOL_SAVE = 17
TOOL_LOAD = 18

TOOL_NAMES = [
    "PENCIL", "MARKER", "BRUSH", "ERASER", "FILL", "EYEDROP",
    "UNDO", "REDO", "PREV", "NEXT", "ADD", "DUP", "DEL",
    "ONION", "PLAY", "EXPORT", "CLEAR", "SAVE", "LOAD",
]
TOOL_INITIALS = [
    "P", "M", "B", "E", "F", "D",
    "U", "R", "<", ">", "+", "2", "X",
    "O", "!", "G", "C", "S", "L",
]

# Draw tools (tools that paint on canvas)
_DRAW_TOOLS = {TOOL_PENCIL, TOOL_MARKER, TOOL_BRUSH, TOOL_ERASER, TOOL_FILL, TOOL_EYEDROP}

# Per-frame undo limit (reduced to manage memory across frames)
FRAME_UNDO_MAX = 16

# Modes
MODE_DRAW = 0
MODE_MENU = 1
MODE_LOAD = 2
MODE_PREVIEW = 3
MODE_NAME = 4

# Name entry charset
NAME_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-"
NAME_LEN = 8


class PaintGif(Visual):
    name = "PAINT GIF"
    description = "Frame-by-frame animation editor"
    category = "utility"
    custom_exit = True

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        # Frames: list of 64x64 canvases (None = empty/black pixel)
        self.frames = [self._blank_canvas()]
        self.frame_idx = 0

        # Per-frame undo/redo stacks
        self.undo_stacks = {}  # {frame_idx: [snapshot, ...]}
        self.redo_stacks = {}  # {frame_idx: [snapshot, ...]}

        # Onion skin
        self.onion_skin = False

        # Preview
        self.preview_fps = 6
        self.preview_timer = 0.0

        # Name entry
        self.name_chars = [0] * NAME_LEN  # indices into NAME_CHARS
        self.name_cursor = 0

        # Cursor
        self.cx = CANVAS_SIZE // 2
        self.cy = CANVAS_SIZE // 2
        self.blink_timer = 0.0

        # Current color and tool
        self.color_idx = 9  # red
        self.tool = TOOL_MARKER
        self.brush_size = 2

        # Mode
        self.mode = MODE_DRAW

        # Input timing
        self.move_timer = 0.0

        # Button hold/tap detection
        self.btn_hold_time = 0.0
        self.btn_was_held = False
        self.painting = False

        # Exit hold (both buttons)
        self.exit_hold = 0.0

        # Debounce
        self.debounce = 0.0

        # Menu cursor
        self.menu_color = self.color_idx
        self.menu_tool = self.tool

        # Load browser
        self.load_dirs = []
        self.load_idx = 0

        # Overlay
        self.overlay_text = ""
        self.overlay_timer = 0.0

    @staticmethod
    def _blank_canvas():
        return [[None] * CANVAS_SIZE for _ in range(CANVAS_SIZE)]

    @property
    def canvas(self):
        return self.frames[self.frame_idx]

    @canvas.setter
    def canvas(self, value):
        self.frames[self.frame_idx] = value

    @property
    def _brush(self):
        return _TOOL_BRUSH.get(self.tool, self.brush_size)

    # ── Input / Update ────────────────────────────────────────────────

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

        # Overlay timer
        if self.overlay_timer > 0:
            self.overlay_timer -= dt

        # Debounce
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
        elif self.mode == MODE_PREVIEW:
            self._update_preview(inp, dt)
        elif self.mode == MODE_NAME:
            self._update_name(inp, dt)

    # ── Draw mode ─────────────────────────────────────────────────────

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
        b = self._brush
        if moved:
            self.cx = _clamp(self.cx + inp.dx * b, 0, CANVAS_SIZE - b)
            self.cy = _clamp(self.cy + inp.dy * b, 0, CANVAS_SIZE - b)

        # Button hold/tap detection (unified both buttons)
        btn_now = inp.action_l_held or inp.action_r_held
        if btn_now:
            self.btn_hold_time += dt
            if self.btn_hold_time >= 0.15:
                if not self.painting:
                    if self.tool in _DRAW_TOOLS:
                        self._snapshot()
                self.painting = True
        else:
            if self.btn_was_held and self.btn_hold_time < 0.15:
                # Tap -> open menu
                self.mode = MODE_MENU
                self.debounce = 0.12
                self.menu_color = self.color_idx
                self.menu_tool = self.tool
            self.btn_hold_time = 0.0
            self.painting = False
        self.btn_was_held = btn_now

        if self.painting:
            self._apply_tool()

    def _paint_brush(self, color):
        b = self._brush
        canvas = self.canvas
        for dy in range(b):
            for dx in range(b):
                px, py = self.cx + dx, self.cy + dy
                if 0 <= px < CANVAS_SIZE and 0 <= py < CANVAS_SIZE:
                    canvas[py][px] = color

    def _apply_tool(self):
        if self.tool in (TOOL_PENCIL, TOOL_MARKER, TOOL_BRUSH):
            self._paint_brush(PALETTE[self.color_idx])
        elif self.tool == TOOL_ERASER:
            self._paint_brush(None)
        elif self.tool == TOOL_FILL:
            self._flood_fill(self.cx, self.cy)
            self.painting = False
        elif self.tool == TOOL_EYEDROP:
            pixel = self.canvas[self.cy][self.cx]
            if pixel:
                best = 0
                best_d = _color_dist_sq(pixel, PALETTE[0])
                for i in range(1, len(PALETTE)):
                    d = _color_dist_sq(pixel, PALETTE[i])
                    if d < best_d:
                        best_d = d
                        best = i
                self.color_idx = best
            self.tool = TOOL_MARKER
            self.painting = False

    def _flood_fill(self, sx, sy):
        canvas = self.canvas
        target = canvas[sy][sx]
        fill_color = PALETTE[self.color_idx]
        if target == fill_color:
            return
        queue = deque([(sx, sy)])
        visited = set()
        count = 0
        while queue and count < 4096:
            x, y = queue.popleft()
            if (x, y) in visited:
                continue
            if x < 0 or x >= CANVAS_SIZE or y < 0 or y >= CANVAS_SIZE:
                continue
            if canvas[y][x] != target:
                continue
            visited.add((x, y))
            canvas[y][x] = fill_color
            count += 1
            queue.append((x - 1, y))
            queue.append((x + 1, y))
            queue.append((x, y - 1))
            queue.append((x, y + 1))

    # ── Per-frame undo/redo ───────────────────────────────────────────

    def _snapshot(self):
        idx = self.frame_idx
        stack = self.undo_stacks.setdefault(idx, [])
        stack.append([row[:] for row in self.canvas])
        if len(stack) > FRAME_UNDO_MAX:
            stack.pop(0)
        self.redo_stacks.pop(idx, None)

    def _do_undo(self):
        idx = self.frame_idx
        stack = self.undo_stacks.get(idx, [])
        if not stack:
            self.overlay_text = "NO UNDO"
            self.overlay_timer = 1.5
            return
        redo = self.redo_stacks.setdefault(idx, [])
        redo.append([row[:] for row in self.canvas])
        if len(redo) > FRAME_UNDO_MAX:
            redo.pop(0)
        self.canvas = stack.pop()
        self.overlay_text = "UNDO"
        self.overlay_timer = 1.0

    def _do_redo(self):
        idx = self.frame_idx
        redo = self.redo_stacks.get(idx, [])
        if not redo:
            self.overlay_text = "NO REDO"
            self.overlay_timer = 1.5
            return
        stack = self.undo_stacks.setdefault(idx, [])
        stack.append([row[:] for row in self.canvas])
        if len(stack) > FRAME_UNDO_MAX:
            stack.pop(0)
        self.canvas = redo.pop()
        self.overlay_text = "REDO"
        self.overlay_timer = 1.0

    # ── Frame management ──────────────────────────────────────────────

    def _shift_stacks(self, from_idx, delta):
        """Shift undo/redo stack keys >= from_idx by delta (+1 or -1)."""
        for stacks in (self.undo_stacks, self.redo_stacks):
            new = {}
            for k, v in stacks.items():
                if k >= from_idx:
                    nk = k + delta
                    if nk >= 0:
                        new[nk] = v
                else:
                    new[k] = v
            stacks.clear()
            stacks.update(new)

    def _go_prev_frame(self):
        self.frame_idx = (self.frame_idx - 1) % len(self.frames)
        self.overlay_text = f"{self.frame_idx+1}/{len(self.frames)}"
        self.overlay_timer = 1.0

    def _go_next_frame(self):
        self.frame_idx = (self.frame_idx + 1) % len(self.frames)
        self.overlay_text = f"{self.frame_idx+1}/{len(self.frames)}"
        self.overlay_timer = 1.0

    def _add_frame(self):
        new_idx = self.frame_idx + 1
        self.frames.insert(new_idx, self._blank_canvas())
        self._shift_stacks(new_idx, 1)
        self.frame_idx = new_idx
        self.overlay_text = f"+F {self.frame_idx+1}/{len(self.frames)}"
        self.overlay_timer = 1.0

    def _dup_frame(self):
        new_idx = self.frame_idx + 1
        dup = [row[:] for row in self.canvas]
        self.frames.insert(new_idx, dup)
        self._shift_stacks(new_idx, 1)
        self.frame_idx = new_idx
        self.overlay_text = f"DUP {self.frame_idx+1}/{len(self.frames)}"
        self.overlay_timer = 1.0

    def _del_frame(self):
        if len(self.frames) <= 1:
            self.overlay_text = "LAST FRAME"
            self.overlay_timer = 1.5
            return
        del_idx = self.frame_idx
        self.frames.pop(del_idx)
        # Remove stacks for deleted frame
        self.undo_stacks.pop(del_idx, None)
        self.redo_stacks.pop(del_idx, None)
        # Shift stacks above deleted frame down
        self._shift_stacks(del_idx + 1, -1)
        if self.frame_idx >= len(self.frames):
            self.frame_idx = len(self.frames) - 1
        self.overlay_text = f"DEL {self.frame_idx+1}/{len(self.frames)}"
        self.overlay_timer = 1.0

    # ── Menu mode ─────────────────────────────────────────────────────

    def _update_menu(self, inp, dt):
        if inp.left_pressed:
            self.menu_color = (self.menu_color - 1) % len(PALETTE)
        if inp.right_pressed:
            self.menu_color = (self.menu_color + 1) % len(PALETTE)
        if inp.up_pressed:
            self.menu_tool = (self.menu_tool - 1) % len(TOOL_NAMES)
        if inp.down_pressed:
            self.menu_tool = (self.menu_tool + 1) % len(TOOL_NAMES)

        btn_tap = inp.action_l or inp.action_r
        if not btn_tap:
            return

        self.color_idx = self.menu_color
        t = self.menu_tool

        if t == TOOL_UNDO:
            self._do_undo()
            self._to_draw()
        elif t == TOOL_REDO:
            self._do_redo()
            self._to_draw()
        elif t == TOOL_PREV:
            self._go_prev_frame()
            self._to_draw()
        elif t == TOOL_NEXT:
            self._go_next_frame()
            self._to_draw()
        elif t == TOOL_ADD:
            self._add_frame()
            self._to_draw()
        elif t == TOOL_DUP:
            self._dup_frame()
            self._to_draw()
        elif t == TOOL_DEL:
            self._del_frame()
            self._to_draw()
        elif t == TOOL_ONION:
            self.onion_skin = not self.onion_skin
            self.overlay_text = "ONION ON" if self.onion_skin else "ONION OFF"
            self.overlay_timer = 1.0
            self._to_draw()
        elif t == TOOL_PLAY:
            self.mode = MODE_PREVIEW
            self.preview_timer = 0.0
            self.frame_idx = 0
            self.debounce = 0.2
        elif t == TOOL_EXPORT:
            self.name_chars = [0] * NAME_LEN
            self.name_cursor = 0
            self.mode = MODE_NAME
            self.debounce = 0.15
        elif t == TOOL_CLEAR:
            self._snapshot()
            self.canvas = self._blank_canvas()
            self.overlay_text = "CLEARED!"
            self.overlay_timer = 1.5
            self._to_draw()
        elif t == TOOL_SAVE:
            self._do_save()
            self._to_draw()
        elif t == TOOL_LOAD:
            self._enter_load_browser()
        else:
            # Draw tool selected
            self.tool = t
            if t in _TOOL_BRUSH:
                self.brush_size = _TOOL_BRUSH[t]
            self._to_draw()

    def _to_draw(self):
        self.mode = MODE_DRAW
        self.debounce = 0.12

    # ── Load browser ──────────────────────────────────────────────────

    def _enter_load_browser(self):
        self.load_dirs = []
        if os.path.isdir(SAVE_DIR):
            for d in sorted(os.listdir(SAVE_DIR)):
                full = os.path.join(SAVE_DIR, d)
                if os.path.isdir(full) and d.startswith("proj_"):
                    self.load_dirs.append(d)
        if not self.load_dirs:
            self.overlay_text = "NO PROJECTS"
            self.overlay_timer = 1.5
            self._to_draw()
            return
        self.load_idx = 0
        self.mode = MODE_LOAD
        self.debounce = 0.12

    def _update_load(self, inp, dt):
        if not self.load_dirs:
            self.mode = MODE_MENU
            self.debounce = 0.12
            return

        if inp.up_pressed:
            self.load_idx = (self.load_idx - 1) % len(self.load_dirs)
        if inp.down_pressed:
            self.load_idx = (self.load_idx + 1) % len(self.load_dirs)
        if inp.left_pressed:
            self.mode = MODE_MENU
            self.debounce = 0.12
            return

        btn_tap = inp.action_l or inp.action_r
        if btn_tap:
            self._do_load(self.load_dirs[self.load_idx])
            self._to_draw()

    def _do_save(self):
        if not HAS_PIL:
            self.overlay_text = "NO PIL!"
            self.overlay_timer = 1.5
            return
        os.makedirs(SAVE_DIR, exist_ok=True)
        num = 1
        while os.path.exists(os.path.join(SAVE_DIR, f"proj_{num:03d}")):
            num += 1
        proj_dir = os.path.join(SAVE_DIR, f"proj_{num:03d}")
        os.makedirs(proj_dir)
        for i, frame in enumerate(self.frames):
            img = Image.new("RGB", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0))
            for y in range(CANVAS_SIZE):
                for x in range(CANVAS_SIZE):
                    c = frame[y][x]
                    if c:
                        img.putpixel((x, y), c)
            img.save(os.path.join(proj_dir, f"frame_{i:03d}.png"))
        self.overlay_text = f"SAVED {num:03d}"
        self.overlay_timer = 1.5

    def _do_load(self, dirname):
        if not HAS_PIL:
            self.overlay_text = "NO PIL!"
            self.overlay_timer = 1.5
            return
        proj_dir = os.path.join(SAVE_DIR, dirname)
        pngs = sorted(f for f in os.listdir(proj_dir) if f.endswith(".png"))
        if not pngs:
            self.overlay_text = "EMPTY PROJ"
            self.overlay_timer = 1.5
            return
        new_frames = []
        for png in pngs:
            path = os.path.join(proj_dir, png)
            img = Image.open(path).convert("RGB")
            if img.size != (CANVAS_SIZE, CANVAS_SIZE):
                img = img.resize((CANVAS_SIZE, CANVAS_SIZE), Image.NEAREST)
            canvas = self._blank_canvas()
            for y in range(CANVAS_SIZE):
                for x in range(CANVAS_SIZE):
                    r, g, b = img.getpixel((x, y))
                    if r or g or b:
                        canvas[y][x] = (r, g, b)
            new_frames.append(canvas)
        self.frames = new_frames
        self.frame_idx = 0
        self.undo_stacks.clear()
        self.redo_stacks.clear()
        self.overlay_text = f"LOADED {len(self.frames)}F"
        self.overlay_timer = 1.5

    # ── Preview mode ──────────────────────────────────────────────────

    def _update_preview(self, inp, dt):
        # Adjust FPS
        if inp.left_pressed:
            self.preview_fps = max(1, self.preview_fps - 1)
        if inp.right_pressed:
            self.preview_fps = min(24, self.preview_fps + 1)

        # Advance frames
        self.preview_timer += dt
        interval = 1.0 / self.preview_fps
        if self.preview_timer >= interval:
            self.preview_timer -= interval
            self.frame_idx = (self.frame_idx + 1) % len(self.frames)

        # Button tap exits
        btn_tap = inp.action_l or inp.action_r
        if btn_tap:
            self._to_draw()

    # ── Name entry mode ───────────────────────────────────────────────

    def _update_name(self, inp, dt):
        if inp.up_pressed:
            self.name_chars[self.name_cursor] = (self.name_chars[self.name_cursor] - 1) % len(NAME_CHARS)
        if inp.down_pressed:
            self.name_chars[self.name_cursor] = (self.name_chars[self.name_cursor] + 1) % len(NAME_CHARS)

        if inp.left_pressed:
            if self.name_cursor == 0:
                # Cancel
                self.mode = MODE_MENU
                self.debounce = 0.12
                return
            self.name_cursor -= 1

        if inp.right_pressed:
            if self.name_cursor < NAME_LEN - 1:
                self.name_cursor += 1
            else:
                self._do_export()
                return

        btn_tap = inp.action_l or inp.action_r
        if btn_tap:
            if self.name_cursor < NAME_LEN - 1:
                self.name_cursor += 1
            else:
                self._do_export()

    def _do_export(self):
        if not HAS_PIL:
            self.overlay_text = "NO PIL!"
            self.overlay_timer = 1.5
            self._to_draw()
            return

        # Build name
        raw = "".join(NAME_CHARS[c] for c in self.name_chars)
        name = raw.rstrip("-").lower()
        if not name:
            name = "anim"

        os.makedirs(SAVE_DIR, exist_ok=True)
        path = os.path.join(SAVE_DIR, f"{name}.gif")

        images = []
        for frame in self.frames:
            img = Image.new("RGB", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0))
            for y in range(CANVAS_SIZE):
                for x in range(CANVAS_SIZE):
                    c = frame[y][x]
                    if c:
                        img.putpixel((x, y), c)
            images.append(img)

        duration = int(1000 / self.preview_fps)
        images[0].save(path, save_all=True, append_images=images[1:],
                       duration=duration, loop=0)

        self.overlay_text = f"GIF {name}"
        self.overlay_timer = 2.0
        self._to_draw()

    # ── Drawing ───────────────────────────────────────────────────────

    def draw(self):
        self.display.clear()

        if self.mode == MODE_DRAW:
            self._draw_onion()
            self._draw_canvas()
            self._draw_hud()
            self._draw_cursor()
        elif self.mode == MODE_MENU:
            self._draw_menu()
        elif self.mode == MODE_LOAD:
            self._draw_load_browser()
        elif self.mode == MODE_PREVIEW:
            self._draw_canvas()
            self._draw_preview_hud()
        elif self.mode == MODE_NAME:
            self._draw_name_entry()

        # Overlay feedback text
        if self.overlay_timer > 0 and self.overlay_text:
            alpha = min(1.0, self.overlay_timer / 0.5)
            c = int(255 * alpha)
            self.display.draw_text_small(2, 57, self.overlay_text, (c, c, 0))

    def _draw_onion(self):
        if not self.onion_skin or self.frame_idx == 0:
            return
        prev = self.frames[self.frame_idx - 1]
        for y in range(CANVAS_SIZE):
            row = prev[y]
            for x in range(CANVAS_SIZE):
                pixel = row[x]
                if pixel:
                    # ~30% brightness: * 77 >> 8
                    r = pixel[0] * 77 >> 8
                    g = pixel[1] * 77 >> 8
                    b = pixel[2] * 77 >> 8
                    self.display.set_pixel(x, y, (r, g, b))

    def _draw_canvas(self):
        canvas = self.canvas
        for y in range(CANVAS_SIZE):
            row = canvas[y]
            for x in range(CANVAS_SIZE):
                pixel = row[x]
                if pixel:
                    self.display.set_pixel(x, y, pixel)

    def _draw_hud(self):
        # Color swatch top-left: 3x3
        c = PALETTE[self.color_idx]
        for dy in range(3):
            for dx in range(3):
                self.display.set_pixel(dx, dy, c)

        # Tool initial top-right
        letter = TOOL_INITIALS[self.tool]
        self.display.draw_text_small(60, 0, letter, (180, 180, 180))

        # Frame counter bottom-left
        label = f"{self.frame_idx+1}-{len(self.frames)}"
        self.display.draw_text_small(2, 57, label, (120, 120, 120))

        # Onion skin indicator bottom-right
        if self.onion_skin:
            self.display.draw_text_small(59, 57, "O", (0, 100, 0))

    def _draw_cursor(self):
        blink = int(self.blink_timer * 4) % 2 == 0
        if not blink:
            return
        b = self._brush
        for dy in range(b):
            for dx in range(b):
                self.display.set_pixel(self.cx + dx, self.cy + dy, (255, 255, 255))

    def _draw_preview_hud(self):
        label = f"FPS:{self.preview_fps}"
        self.display.draw_text_small(2, 57, label, (120, 120, 120))

    def _draw_menu(self):
        n_colors = len(PALETTE)
        # Color strip: 7 swatches, current in center (larger)
        center_slot = 3
        for slot in range(7):
            idx = (self.menu_color + slot - center_slot) % n_colors
            c = PALETTE[idx]
            if slot == center_slot:
                x0 = 27
                self.display.draw_rect(x0, 2, 10, 10, c)
                for i in range(12):
                    self.display.set_pixel(x0 - 1 + i, 1, (255, 255, 255))
                    self.display.set_pixel(x0 - 1 + i, 12, (255, 255, 255))
                for i in range(11):
                    self.display.set_pixel(x0 - 1, 2 + i, (255, 255, 255))
                    self.display.set_pixel(x0 + 10, 2 + i, (255, 255, 255))
            else:
                if slot < center_slot:
                    x0 = slot * 9
                else:
                    x0 = 27 + 12 + (slot - center_slot - 1) * 9
                dim = tuple(v // 2 for v in c)
                self.display.draw_rect(x0, 4, 7, 6, dim)

        self.display.draw_text_small(1, 14, "<", (120, 120, 120))
        self.display.draw_text_small(59, 14, ">", (120, 120, 120))

        # Separator
        for x in range(GRID_SIZE):
            self.display.set_pixel(x, 21, (40, 40, 40))

        # Tool: show prev / current / next
        n_tools = len(TOOL_NAMES)
        prev_t = (self.menu_tool - 1) % n_tools
        next_t = (self.menu_tool + 1) % n_tools

        self.display.draw_text_small(7, 25, TOOL_NAMES[prev_t], (60, 60, 60))
        self.display.draw_text_small(2, 34, ">", (255, 255, 255))
        self.display.draw_text_small(7, 34, TOOL_NAMES[self.menu_tool], (255, 255, 255))
        self.display.draw_text_small(7, 43, TOOL_NAMES[next_t], (60, 60, 60))

        self.display.draw_text_small(55, 25, "^", (120, 120, 120))
        self.display.draw_text_small(55, 43, "v", (120, 120, 120))

        # Frame info at bottom
        info = f"F{self.frame_idx+1}/{len(self.frames)}"
        self.display.draw_text_small(2, 55, info, (80, 120, 80))

    def _draw_load_browser(self):
        self.display.draw_text_small(2, 1, "LOAD PROJ", (200, 200, 200))
        for x in range(GRID_SIZE):
            self.display.set_pixel(x, 8, (40, 40, 40))

        visible = 7
        total = len(self.load_dirs)
        scroll = max(0, min(self.load_idx - visible // 2, total - visible))

        y = 10
        for i in range(scroll, min(scroll + visible, total)):
            name = self.load_dirs[i]
            label = name.replace("proj_", "P")
            if i == self.load_idx:
                self.display.draw_text_small(2, y, ">", (255, 255, 255))
                self.display.draw_text_small(7, y, label, (255, 255, 255))
            else:
                self.display.draw_text_small(7, y, label, (100, 100, 100))
            y += 7

        self.display.draw_text_small(2, 57, "< CANCEL", (80, 80, 80))

    def _draw_name_entry(self):
        self.display.draw_text_small(2, 2, "EXPORT GIF", (200, 160, 40))

        # Separator
        for x in range(GRID_SIZE):
            self.display.set_pixel(x, 10, (40, 40, 40))

        # Draw characters
        x_start = 2
        char_w = 7  # 4px char + 3px gap
        y_char = 28

        for i in range(NAME_LEN):
            ch = NAME_CHARS[self.name_chars[i]]
            x = x_start + i * char_w

            if i == self.name_cursor:
                # Active character — bright with triangle arrows
                self.display.draw_text_small(x, y_char, ch, (255, 255, 255))

                # Up triangle (3 pixels wide): centered above char
                cx = x + 1
                self.display.set_pixel(cx, y_char - 5, (0, 200, 0))
                self.display.set_pixel(cx - 1, y_char - 4, (0, 200, 0))
                self.display.set_pixel(cx, y_char - 4, (0, 200, 0))
                self.display.set_pixel(cx + 1, y_char - 4, (0, 200, 0))

                # Down triangle: centered below char
                self.display.set_pixel(cx - 1, y_char + 7, (0, 200, 0))
                self.display.set_pixel(cx, y_char + 7, (0, 200, 0))
                self.display.set_pixel(cx + 1, y_char + 7, (0, 200, 0))
                self.display.set_pixel(cx, y_char + 8, (0, 200, 0))
            else:
                self.display.draw_text_small(x, y_char, ch, (80, 80, 80))

        # Instructions
        self.display.draw_text_small(2, 45, "U/D CHAR", (60, 60, 60))
        self.display.draw_text_small(2, 52, "BTN NEXT", (60, 60, 60))
        self.display.draw_text_small(2, 57, "< CANCEL", (80, 80, 80))
