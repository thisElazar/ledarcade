"""
Fire - Classic demoscene fire effect
====================================
Heat rises from the bottom, creating a realistic fire simulation.

Controls:
  Left/Right - Fire speed
  Up/Down    - Flame height
  Space      - Toggle color palette
"""

import random
from . import Visual, Display, Colors, GRID_SIZE


class Fire(Visual):
    name = "FIRE"
    description = "Classic fire effect"
    category = "nature"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.update_timer = 0.0

        # Fire parameters
        self.intensity = 0.75        # Heat source intensity
        self.speed = 1.0             # Simulation speed multiplier
        self.flame_height = 0.5      # 0=short, 1=tall (affects cooling)
        self.base_cooling = 4        # Base cooling per step

        # Color palettes
        self.palette_index = 0
        self.palettes = ["fire", "ice", "poison"]

        # Heat buffer - values 0-255
        self.heat = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]

    def _get_color(self, heat_val):
        """Convert heat value to color based on current palette."""
        v = heat_val / 255.0
        palette = self.palettes[self.palette_index]

        if palette == "fire":
            # Black -> red -> orange -> yellow -> white
            if v < 0.25:
                t = v / 0.25
                return (int(128 * t), 0, 0)
            elif v < 0.5:
                t = (v - 0.25) / 0.25
                return (128 + int(127 * t), int(64 * t), 0)
            elif v < 0.75:
                t = (v - 0.5) / 0.25
                return (255, 64 + int(128 * t), 0)
            else:
                t = (v - 0.75) / 0.25
                return (255, 192 + int(63 * t), int(255 * t))

        elif palette == "ice":
            # Black -> dark blue -> cyan -> white
            if v < 0.33:
                t = v / 0.33
                return (0, 0, int(128 * t))
            elif v < 0.66:
                t = (v - 0.33) / 0.33
                return (0, int(200 * t), 128 + int(127 * t))
            else:
                t = (v - 0.66) / 0.34
                return (int(255 * t), 200 + int(55 * t), 255)

        else:  # poison
            # Black -> dark green -> bright green -> yellow-green
            if v < 0.33:
                t = v / 0.33
                return (0, int(100 * t), 0)
            elif v < 0.66:
                t = (v - 0.33) / 0.33
                return (0, 100 + int(155 * t), int(50 * t))
            else:
                t = (v - 0.66) / 0.34
                return (int(180 * t), 255, 50 + int(50 * t))

    def handle_input(self, input_state) -> bool:
        consumed = False
        # Left/Right - fire speed
        if input_state.right:
            self.speed = min(3.0, self.speed + 0.2)
            consumed = True
        if input_state.left:
            self.speed = max(0.2, self.speed - 0.2)
            consumed = True
        # Up/Down - flame height
        if input_state.up:
            self.flame_height = min(1.0, self.flame_height + 0.1)
            consumed = True
        if input_state.down:
            self.flame_height = max(0.0, self.flame_height - 0.1)
            consumed = True
        # Space - toggle color palette
        if input_state.action:
            self.palette_index = (self.palette_index + 1) % len(self.palettes)
            consumed = True
        return consumed

    def update(self, dt: float):
        self.time += dt
        self.update_timer += dt * self.speed

        # Cap to prevent death spiral
        step_interval = 0.02
        if self.update_timer > step_interval * 3:
            self.update_timer = step_interval

        # Run simulation steps based on speed
        while self.update_timer >= step_interval:
            self.update_timer -= step_interval
            self._step_fire()

    def _step_fire(self):
        """Single step of fire simulation."""
        # Generate heat at the bottom row
        for x in range(GRID_SIZE):
            if random.random() < self.intensity:
                self.heat[GRID_SIZE - 1][x] = random.randint(160, 255)
            else:
                self.heat[GRID_SIZE - 1][x] = random.randint(0, 100)

        # Cooling based on flame_height (0=max cooling/short, 1=min cooling/tall)
        max_cooling = int(self.base_cooling * (1.5 - self.flame_height))

        # Propagate heat upward with cooling
        for y in range(GRID_SIZE - 2, -1, -1):
            for x in range(GRID_SIZE):
                # Average of pixels below with some randomness
                below = self.heat[y + 1][x]
                left = self.heat[y + 1][max(0, x - 1)]
                right = self.heat[y + 1][min(GRID_SIZE - 1, x + 1)]

                # Weighted average favoring directly below
                avg = (below * 3 + left + right) // 5

                # Cooling as heat rises
                cooling = random.randint(0, max(1, max_cooling))
                self.heat[y][x] = max(0, avg - cooling)

    def draw(self):
        self.display.clear(Colors.BLACK)

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                heat_val = self.heat[y][x]
                if heat_val > 0:
                    color = self._get_color(heat_val)
                    self.display.set_pixel(x, y, color)
