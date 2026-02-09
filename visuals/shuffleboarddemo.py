"""
Shuffleboard Demo - AI Attract Mode
====================================
Shuffleboard plays itself using AI for idle screen demos.
The AI aims near center and picks medium-high power for consistent scoring.

AI Strategy:
- Select 1P mode automatically
- Aim near center (small random offset) when oscillating aim crosses target
- Power in the 0.55-0.85 range for good zone reach
- Pick fresh targets after each shot
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState
import random

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.shuffleboard import (
    Shuffleboard, PHASE_MODE_SELECT, PHASE_AIM, PHASE_POWER,
    PHASE_SLIDING, PHASE_SCORE_SHOW, PHASE_TURN_CHANGE, PHASE_GAME_OVER_2P,
    MAX_AIM_ANGLE
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
            if abs(self.game.power - self.power_target) < 0.06:
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
        """Choose random aim and power targets for the next shot."""
        self.aim_target = random.uniform(-0.1, 0.1)
        self.power_target = random.uniform(0.55, 0.85)
