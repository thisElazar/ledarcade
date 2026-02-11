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
TOOL_SAVE = 4
TOOL_LOAD = 5
TOOL_CLEAR = 6

TOOL_NAMES = ["PENCIL", "ERASER", "FILL", "EYEDROP", "SAVE", "LOAD", "CLEAR"]
TOOL_INITIALS = ["P", "E", "F", "D", "S", "L", "C"]

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

        # Menu cursor
        self.menu_row = 0  # 0..2 = palette rows, 3..9 = tool/file rows
        self.menu_col = 0

        # Load browser
        self.load_files = []
        self.load_idx = 0

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
                self.painting = True
        else:
            if self.btn_was_held and self.btn_hold_time < 0.15:
                # Tap → open menu
                self.mode = MODE_MENU
                self.menu_row = 0
                self.menu_col = min(self.color_idx % PALETTE_COLS, PALETTE_COLS - 1)
                # Position menu row to match current color
                self.menu_row = self.color_idx // PALETTE_COLS
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

    def _update_menu(self, inp, dt):
        # Total rows: 3 palette rows + 7 tool rows = 10
        total_rows = PALETTE_ROWS + len(TOOL_NAMES)

        if inp.up_pressed:
            self.menu_row = (self.menu_row - 1) % total_rows
        if inp.down_pressed:
            self.menu_row = (self.menu_row + 1) % total_rows
        if inp.left_pressed:
            if self.menu_row < PALETTE_ROWS:
                self.menu_col = (self.menu_col - 1) % PALETTE_COLS
        if inp.right_pressed:
            if self.menu_row < PALETTE_ROWS:
                self.menu_col = (self.menu_col + 1) % PALETTE_COLS

        # Button tap to select
        btn_tap = inp.action_l or inp.action_r
        if btn_tap:
            if self.menu_row < PALETTE_ROWS:
                # Color selection
                idx = self.menu_row * PALETTE_COLS + self.menu_col
                if 0 <= idx < len(PALETTE):
                    self.color_idx = idx
                self.mode = MODE_DRAW
            else:
                # Tool/file selection
                tool_idx = self.menu_row - PALETTE_ROWS
                if tool_idx == TOOL_SAVE:
                    self._do_save()
                    self.mode = MODE_DRAW
                elif tool_idx == TOOL_LOAD:
                    self._enter_load_browser()
                elif tool_idx == TOOL_CLEAR:
                    self.canvas = [[None] * CANVAS_SIZE for _ in range(CANVAS_SIZE)]
                    self.overlay_text = "CLEARED!"
                    self.overlay_timer = 1.5
                    self.mode = MODE_DRAW
                else:
                    self.tool = tool_idx
                    self.mode = MODE_DRAW

    def _update_load(self, inp, dt):
        if not self.load_files:
            # No files, go back
            self.mode = MODE_MENU
            return

        if inp.up_pressed:
            self.load_idx = (self.load_idx - 1) % len(self.load_files)
        if inp.down_pressed:
            self.load_idx = (self.load_idx + 1) % len(self.load_files)
        if inp.left_pressed:
            # Cancel
            self.mode = MODE_MENU
        btn_tap = inp.action_l or inp.action_r
        if btn_tap:
            self._do_load(self.load_files[self.load_idx])
            self.mode = MODE_DRAW

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
            return
        self.load_idx = 0
        self.mode = MODE_LOAD

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
        # Color palette grid: 8x3, each swatch 7x7 with 1px gap = 8px cells
        for row in range(PALETTE_ROWS):
            for col in range(PALETTE_COLS):
                idx = row * PALETTE_COLS + col
                c = PALETTE[idx]
                x0 = col * 8
                y0 = row * 8
                self.display.draw_rect(x0, y0, 7, 7, c)
                # Highlight selected color
                if idx == self.color_idx:
                    # White corner dots
                    self.display.set_pixel(x0, y0, (255, 255, 255))
                    self.display.set_pixel(x0 + 6, y0, (255, 255, 255))
                    self.display.set_pixel(x0, y0 + 6, (255, 255, 255))
                    self.display.set_pixel(x0 + 6, y0 + 6, (255, 255, 255))

        # Cursor highlight on palette
        if self.menu_row < PALETTE_ROWS:
            cx0 = self.menu_col * 8
            cy0 = self.menu_row * 8
            # Draw border around selected cell
            for i in range(8):
                self.display.set_pixel(cx0 + i, cy0, (255, 255, 255))
                self.display.set_pixel(cx0 + i, cy0 + 7, (255, 255, 255))
            for i in range(8):
                self.display.set_pixel(cx0, cy0 + i, (255, 255, 255))
                self.display.set_pixel(cx0 + 7, cy0 + i, (255, 255, 255))

        # Tool + file list below palette
        list_y = PALETTE_ROWS * 8 + 2  # 26
        for i, name in enumerate(TOOL_NAMES):
            y = list_y + i * 7
            is_selected = (self.menu_row == PALETTE_ROWS + i)
            if is_selected:
                # Active tool gets bright color + arrow
                if i == self.tool:
                    color = (255, 255, 0)
                else:
                    color = (255, 255, 255)
                self.display.draw_text_small(2, y, ">", color)
                self.display.draw_text_small(7, y, name, color)
            else:
                if i == self.tool:
                    color = (180, 180, 0)
                else:
                    color = (100, 100, 100)
                self.display.draw_text_small(7, y, name, color)

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
