"""
Gray-Scott - Reaction-Diffusion Auto-Play
==========================================
Runs the Gray-Scott model at committed parameters (from GRAY-SCOTT LAB)
or sensible defaults. Simple controls: palette cycling and reseed.

Controls:
  Up/Down  - Cycle color palette
  Button   - Re-seed grid
"""

from . import Visual, Display, GRID_SIZE
from .turing import (PALETTES, _init_grid, _step_gray_scott, _draw_turing)
import settings


class GrayScott(Visual):
    name = "GRAY-SCOTT"
    description = "Reaction-diffusion patterns"
    category = "automata"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.f = settings.get('gs_lab_f', 0.035)
        self.k = settings.get('gs_lab_k', 0.065)
        self.palette_idx = settings.get('gs_lab_palette', 0) % len(PALETTES)
        self.steps_per_frame = 8
        self.u, self.v = _init_grid()
        self._both_pressed_prev = False

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.up_pressed:
            self.palette_idx = (self.palette_idx + 1) % len(PALETTES)
            consumed = True
        if input_state.down_pressed:
            self.palette_idx = (self.palette_idx - 1) % len(PALETTES)
            consumed = True
        both = input_state.action_l and input_state.action_r
        if not both and (input_state.action_l or input_state.action_r):
            if not self._both_pressed_prev:
                self.u, self.v = _init_grid()
                consumed = True
        self._both_pressed_prev = both
        return consumed

    def update(self, dt: float):
        self.time += dt
        self.u, self.v = _step_gray_scott(self.u, self.v, self.f, self.k,
                                           self.steps_per_frame)

    def draw(self):
        _draw_turing(self.display, self.v, self.palette_idx)
