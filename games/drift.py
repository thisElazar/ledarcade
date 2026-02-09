"""
Drift - LED Arcade
==================
Terrain & water simulation sandbox. Sculpt terrain and place water springs
on a 64x64 grid, watching water flow downhill in real-time.

Controls:
  Joystick     - Move cursor
  Space        - Cycle tool: Raise / Lower / Smooth / Spring / Water
  Z            - Apply current tool at cursor
"""

import math
from arcade import Game, GameState, Display, Colors, InputState
from .drift_sim import DriftSim, clamp

W = 64
H = 64
SIM_TOP = 6  # rows 0-5 are HUD

TOOLS = ['raise', 'lower', 'smooth', 'spring', 'water']
TOOL_NAMES = ['RAISE', 'LOWER', 'SMOOTH', 'SPRING', 'WATER']
TOOL_COLORS = [
    (200, 160, 80),   # raise - gold
    (160, 80, 60),    # lower - dark red
    (140, 180, 140),  # smooth - soft green
    (60, 200, 255),   # spring - cyan
    (40, 100, 220),   # water - blue
]


class Drift(Game):
    name = "DRIFT"
    description = "Terrain sandbox"
    category = "modern"

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0

        self.sim = DriftSim(W, H)
        self.sim.generate_terrain()

        # Auto-place a couple springs on peaks
        peaks = self.sim.find_peaks(3)
        for px, py in peaks[:2]:
            self.sim.add_spring(px, py)

        # Cursor
        self.cx = W // 2
        self.cy = H // 2

        # Tool
        self.tool_idx = 0
        self.blink_timer = 0.0
        self.move_timer = 0.0

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        self.blink_timer += dt

        # Cycle tool with action_l (Space)
        if input_state.action_l:
            self.tool_idx = (self.tool_idx + 1) % len(TOOLS)

        # Move cursor
        self.move_timer += dt
        rate = 0.07
        if input_state.any_direction:
            if (input_state.up_pressed or input_state.down_pressed or
                    input_state.left_pressed or input_state.right_pressed):
                self.move_timer = 0.0
                self.cx = clamp(self.cx + input_state.dx, 0, W - 1)
                self.cy = clamp(self.cy + input_state.dy, SIM_TOP, H - 1)
            elif self.move_timer >= rate:
                self.move_timer = 0.0
                self.cx = clamp(self.cx + input_state.dx, 0, W - 1)
                self.cy = clamp(self.cy + input_state.dy, SIM_TOP, H - 1)

        # Apply tool with action_r (Z) - works while held
        if input_state.action_r_held:
            tool = TOOLS[self.tool_idx]
            self.sim.apply_brush(self.cx, self.cy, tool, radius=3, strength=2.0)

        # Run simulation
        self.sim.simulate(dt)

    def draw(self):
        self.display.clear()

        # HUD: tool name + color
        name = TOOL_NAMES[self.tool_idx]
        color = TOOL_COLORS[self.tool_idx]
        self.display.draw_text_small(1, 1, name, color)

        # Divider
        for x in range(W):
            self.display.set_pixel(x, SIM_TOP - 1, (40, 40, 40))

        # Render terrain + water
        for y in range(SIM_TOP, H):
            for x in range(W):
                c = self.sim.get_combined_color(x, y)
                self.display.set_pixel(x, y, c)

        # Draw springs as pulsing cyan dots
        pulse = int((math.sin(self.blink_timer * 6.0) + 1.0) * 60) + 100
        for s in self.sim.springs:
            sx, sy = s['x'], s['y']
            if SIM_TOP <= sy < H:
                self.display.set_pixel(sx, sy, (0, pulse, pulse))

        # Draw cursor as blinking crosshair
        blink = int(self.blink_timer * 5) % 2 == 0
        if blink:
            cc = (255, 255, 255)
        else:
            cc = TOOL_COLORS[self.tool_idx]

        self.display.set_pixel(self.cx, self.cy, cc)
        # Crosshair arms (1 pixel each direction)
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = self.cx + dx, self.cy + dy
            if 0 <= nx < W and SIM_TOP <= ny < H:
                self.display.set_pixel(nx, ny, cc)
