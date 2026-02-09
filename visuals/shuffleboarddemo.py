"""
Shuffleboard Demo - AI Attract Mode
====================================
Shuffleboard plays itself using AI for idle screen demos.
The AI uses physics-correct power calculations to land pucks
in high-scoring zones consistently.

AI Strategy:
- Select 1P mode automatically
- Target zone 4 (70%) or zone 3 (30%) for best scoring
- Compute physics-correct power: v0 = sqrt(2 * friction * distance)
- Aim near center with minimal variance
- Small power variance for natural feel
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState
import math
import random

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.shuffleboard import (
    Shuffleboard, PHASE_MODE_SELECT, PHASE_AIM, PHASE_POWER,
    PHASE_SLIDING, PHASE_SCORE_SHOW, PHASE_TURN_CHANGE, PHASE_GAME_OVER_2P,
    MAX_AIM_ANGLE, FRICTION, MAX_POWER, LAUNCH_BOTTOM,
    ZONE4_TOP, ZONE4_BOTTOM, ZONE3_TOP, ZONE3_BOTTOM
)


class ShuffleboardDemo(Visual):
    name = "SHUFFLEBOARD"
    description = "AI slides pucks"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = Shuffleboard(self.display)
        self.game.reset()
        self.game_over_timer = 0.0
        self._pick_targets()

    def handle_input(self, input_state):
        return False

    def update(self, dt):
        self.time += dt

        # Restart after game over pause
        if self.game.state == GameState.GAME_OVER:
            self.game_over_timer += dt
            if self.game_over_timer > 3.0:
                self.game.reset()
                self.game_over_timer = 0.0
                self._pick_targets()
            return

        # Build AI input based on current phase
        ai_input = InputState()
        phase = self.game.phase

        if phase == PHASE_MODE_SELECT:
            # Pick 1P (default mode_select=0) immediately
            ai_input.action_l = True

        elif phase == PHASE_AIM:
            # Wait for oscillating aim to cross near the target angle
            if abs(self.game.aim_angle - self.aim_target) < 0.08:
                ai_input.action_l = True

        elif phase == PHASE_POWER:
            # Wait for oscillating power to reach target
            if abs(self.game.power - self.power_target) < 0.04:
                ai_input.action_l = True
                # Pick fresh targets for the next shot
                self._pick_targets()

        # Phases that need no input: SLIDING, SCORE_SHOW, TURN_CHANGE

        # Handle 2P game over phase (shouldn't occur in 1P demo, but be safe)
        if phase == PHASE_GAME_OVER_2P:
            ai_input.action_l = True

        self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()

        # Blinking "DEMO" overlay
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)

    def _pick_targets(self):
        """Choose aim and power targets using physics-correct calculations."""
        # Aim near center with small variance
        self.aim_target = random.uniform(-0.06, 0.06)

        # Target zone 4 (4 pts) 70% of the time, zone 3 (3 pts) 30%
        if random.random() < 0.7:
            # Zone 4: y ranges from ZONE4_TOP(2) to ZONE4_BOTTOM(10), target middle
            target_y = (ZONE4_TOP + ZONE4_BOTTOM) / 2.0  # ~6
        else:
            # Zone 3: y ranges from ZONE3_TOP(11) to ZONE3_BOTTOM(19), target middle
            target_y = (ZONE3_TOP + ZONE3_BOTTOM) / 2.0  # ~15

        # Launch y is LAUNCH_BOTTOM - 2 (where puck spawns)
        launch_y = LAUNCH_BOTTOM - 2  # 52

        # Distance the puck needs to travel (upward, so positive)
        distance = launch_y - target_y

        # Physics: puck decelerates at FRICTION px/s^2
        # v0 = sqrt(2 * friction * distance) to stop at target
        # power = v0 / MAX_POWER
        v0 = math.sqrt(2.0 * FRICTION * distance)
        self.power_target = v0 / MAX_POWER

        # Add tiny variance for natural feel
        self.power_target += random.uniform(-0.02, 0.02)
        self.power_target = max(0.15, min(0.85, self.power_target))
