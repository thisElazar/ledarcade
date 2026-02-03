"""
Bowling Demo - AI Attract Mode
==============================
Bowling plays itself using AI for idle screen demos.
The AI positions the ball, aims for the pocket, and times the power/spin.

AI Strategy:
- Select 1P mode automatically
- Position ball slightly off-center (pocket approach)
- Aim toward the 1-3 pocket for strikes
- Time power meter for center hit (max power, minimal spin)
- Add slight variation for realistic play
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState
import math
import random

# Import the actual game
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.bowling import (
    Bowling, PHASE_MODE_SELECT, PHASE_POSITION, PHASE_AIM, PHASE_POWER,
    PHASE_ROLLING, PHASE_SCORE_SHOW, PHASE_TURN_CHANGE, PHASE_GAME_OVER_2P,
    LANE_LEFT, LANE_RIGHT, MAX_AIM_ANGLE
)


class BowlingDemo(Visual):
    name = "BOWLING DEMO"
    description = "AI bowls strikes"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = Bowling(self.display)
        self.game.reset()
        self.game_over_timer = 0.0

        # AI targeting
        self._pick_new_target()

    def _pick_new_target(self):
        """Pick target position, aim, and power for this throw."""
        lane_center = (LANE_LEFT + LANE_RIGHT) / 2

        # Position: slightly right of center for right-handed pocket approach
        # Add some variation for realistic play
        offset = random.uniform(2, 6)  # Right of center for 1-3 pocket
        self.target_position = lane_center + offset

        # Aim: angle toward the pocket (slight left angle from right side)
        # Negative angle = aim left
        base_angle = -0.15  # Aim slightly left toward the pocket
        self.target_aim = base_angle + random.uniform(-0.08, 0.08)

        # Power: aim for center of the bar (max power, minimal spin)
        # 0.5 = center = green = max power, no spin
        self.target_power = 0.5 + random.uniform(-0.1, 0.1)

    def handle_input(self, input_state):
        # Demo doesn't respond to input (auto-plays)
        return False

    def update(self, dt):
        self.time += dt

        # If game over, restart after a pause
        if self.game.state == GameState.GAME_OVER:
            self.game_over_timer += dt
            if self.game_over_timer > 3.0:
                self.game.reset()
                self.game_over_timer = 0.0
                self._pick_new_target()
            return

        # Create AI input based on current phase
        ai_input = InputState()
        phase = self.game.phase

        if phase == PHASE_MODE_SELECT:
            # Select 1P mode (already selected by default)
            ai_input.action_l = True

        elif phase == PHASE_POSITION:
            # Wait for sweep to reach target position
            current_pos = self.game.sweep_pos
            if abs(current_pos - self.target_position) < 1.5:
                # Close enough, lock in position
                ai_input.action_l = True

        elif phase == PHASE_AIM:
            # Wait for aim to reach target angle
            current_aim = self.game.aim_angle
            if abs(current_aim - self.target_aim) < 0.05:
                # Close enough, lock in aim
                ai_input.action_l = True

        elif phase == PHASE_POWER:
            # Wait for power meter to reach target
            current_power = self.game.power_pos
            if abs(current_power - self.target_power) < 0.08:
                # Close enough, lock in power and throw
                ai_input.action_l = True

        elif phase == PHASE_ROLLING:
            # Just watch the ball roll
            pass

        elif phase == PHASE_SCORE_SHOW:
            # Wait for score display
            pass

        elif phase == PHASE_TURN_CHANGE:
            # Wait for turn change
            pass

        # Pick new target for next throw when starting position phase
        # (after a roll completes or at frame start)
        if phase == PHASE_POSITION and self.game.ball_in_frame == 0:
            # Check if we just started a new frame
            if not hasattr(self, '_last_frame') or self._last_frame != self.game.current_frame:
                self._last_frame = self.game.current_frame
                self._pick_new_target()
        elif phase == PHASE_POSITION and self.game.ball_in_frame == 1:
            # Second ball in frame - adjust strategy for remaining pins
            self._adjust_for_spare()

        self.game.update(ai_input, dt)

    def _adjust_for_spare(self):
        """Adjust aim for spare pickup based on remaining pins."""
        # Find the center of remaining standing pins
        standing_pins = [p for p in self.game.pins if not p.knocked and p.active]
        if not standing_pins:
            return

        avg_x = sum(p.home_x for p in standing_pins) / len(standing_pins)
        lane_center = (LANE_LEFT + LANE_RIGHT) / 2

        # Position to opposite side of pins
        if avg_x > lane_center:
            self.target_position = lane_center - random.uniform(3, 6)
            self.target_aim = 0.2 + random.uniform(-0.05, 0.05)  # Aim right
        else:
            self.target_position = lane_center + random.uniform(3, 6)
            self.target_aim = -0.2 + random.uniform(-0.05, 0.05)  # Aim left

        self.target_power = 0.5 + random.uniform(-0.1, 0.1)

    def draw(self):
        self.game.draw()

        # Overlay "DEMO" text (blinking)
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)
