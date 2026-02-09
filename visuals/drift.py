"""
Drift Visual - LED Arcade
==========================
Ambient terrain & water simulation. Auto-generates terrain using the original
Drift presets (default, hills, mountains, plains), places springs on peaks,
and watches water flow and fill valleys. Regenerates every ~30 seconds.
"""

import random
import math
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.drift_sim import DriftSim, SPRING_FLOW_RATE

W = 64
H = 64
CYCLE_TIME = 30.0   # seconds before regeneration
FADE_TIME = 2.0     # fade-out duration
TERRAIN_PRESETS = ['default', 'hills', 'mountains', 'plains']


class DriftVisual:
    """Ambient auto-playing Drift simulation."""

    name = "DRIFT"
    description = "Flowing water"
    category = "nature"

    def __init__(self, display):
        self.display = display
        self.time = 0.0
        self.wants_exit = False
        self.reset()

    def reset(self):
        self.time = 0.0
        self.sim = DriftSim(W, H)
        self.preset_idx = 0
        self._new_terrain()
        self.cycle_timer = 0.0
        self.fade_alpha = 1.0
        self.fading_out = False

    def _new_terrain(self):
        """Generate fresh terrain with springs on peaks."""
        preset = TERRAIN_PRESETS[self.preset_idx % len(TERRAIN_PRESETS)]
        self.preset_idx += 1
        self.sim.generate_terrain(preset=preset,
                                  seed=random.randint(0, 999999))
        peaks = self.sim.find_peaks(4)
        count = random.randint(3, min(4, len(peaks)))
        for px, py in peaks[:count]:
            self.sim.add_spring(px, py,
                                flow_rate=SPRING_FLOW_RATE * random.uniform(0.7, 1.3))

    def update(self, dt):
        self.time += dt
        self.cycle_timer += dt

        self.sim.simulate(dt)

        if not self.fading_out and self.cycle_timer >= CYCLE_TIME - FADE_TIME:
            self.fading_out = True

        if self.fading_out:
            self.fade_alpha = max(0.0,
                1.0 - (self.cycle_timer - (CYCLE_TIME - FADE_TIME)) / FADE_TIME)
            if self.cycle_timer >= CYCLE_TIME:
                self._new_terrain()
                self.cycle_timer = 0.0
                self.fading_out = False
                self.fade_alpha = 1.0

    def draw(self):
        self.display.clear()

        # Fade-in ramp for the first second
        if self.cycle_timer < 1.0:
            alpha = self.cycle_timer
        else:
            alpha = self.fade_alpha

        for y in range(H):
            for x in range(W):
                r, g, b = self.sim.get_combined_color(x, y)
                if alpha < 1.0:
                    r = int(r * alpha)
                    g = int(g * alpha)
                    b = int(b * alpha)
                self.display.set_pixel(x, y, (r, g, b))

        # Draw springs as subtle pulsing cyan dots
        pulse = int((math.sin(self.time * 5.0) + 1.0) * 40) + 80
        pa = int(pulse * alpha) if alpha < 1.0 else pulse
        for s in self.sim.springs:
            self.display.set_pixel(s['x'], s['y'], (0, pa, pa))

    def handle_input(self, input_state):
        return False
