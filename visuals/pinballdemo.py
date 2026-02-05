"""
Pinball Demo - AI Attract Mode
==============================
Pinball plays itself using AI for idle screen demos.
The AI tracks ball position and velocity, predicting trajectory to time flipper hits.

AI Strategy:
- Launch ball automatically when waiting (charged plunger)
- Track ball position and velocity
- Activate left flipper when ball approaches from the left side
- Activate right flipper when ball approaches from the right side
- Predict ball trajectory to time flipper hits
"""

import math
from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

# Import the actual game
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.pinball import (
    Pinball, PHASE_PLUNGER, PHASE_PLAYING, PHASE_DRAIN, PHASE_BALL_OVER,
    FLIPPER_LEFT_PIVOT, FLIPPER_RIGHT_PIVOT, FLIPPER_LENGTH,
    DRAIN_Y, TABLE_W
)


class PinballDemo(Visual):
    name = "PINBALL"
    description = "AI plays pinball"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = Pinball(self.display)
        self.game.reset()
        self.game_over_timer = 0.0

        # AI state
        self.plunger_charge_time = 0.0
        self.launch_delay = 0.5  # Wait before launching

        # Flipper timing — hold briefly after flipping, then release
        self.flip_l_timer = 0.0
        self.flip_r_timer = 0.0
        self.flip_hold_duration = 0.12  # hold flipper up this long after trigger

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
            return

        # Create AI input
        ai_input = self._decide_action(dt)
        self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()

        # Overlay "DEMO" text (blinking)
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)

    def _decide_action(self, dt):
        """AI decision-making for flipper control and plunger."""
        ai_input = InputState()
        game = self.game

        # Handle plunger phase - charge and launch
        if game.phase == PHASE_PLUNGER:
            self.plunger_charge_time += dt
            if self.plunger_charge_time > self.launch_delay:
                # Charge the plunger
                ai_input.down = True
                # Release after charging enough (0.6-0.9 charge for varied launches)
                if game.plunger_charge > 0.6 + (self.time % 0.3):
                    ai_input.down = False
            return ai_input

        # Reset charge timer when ball is launched
        if game.phase != PHASE_PLUNGER:
            self.plunger_charge_time = 0.0

        # Handle ball-over phase - just wait
        if game.phase in (PHASE_DRAIN, PHASE_BALL_OVER):
            return ai_input

        # Playing phase - control flippers based on ball trajectory
        ball_x = game.ball_x
        ball_y = game.ball_y
        ball_vx = game.ball_vx
        ball_vy = game.ball_vy

        flipper_y = FLIPPER_LEFT_PIVOT[1]  # Both at same y (173)

        # Decrement flip hold timers
        self.flip_l_timer = max(0.0, self.flip_l_timer - dt)
        self.flip_r_timer = max(0.0, self.flip_r_timer - dt)

        # The key insight: the flipper must be SWINGING when it contacts the
        # ball (angular_vel > 1.0) for a strong hit.  If we raise it too early,
        # the flipper is stationary and the ball just sits on it.
        #
        # Flipper extends in ~0.06s (1.05 rad / 18 rad/s).  So we trigger
        # when the ball is only ~3-6 px away (≈0.03-0.06s at typical speeds).

        distance_to_flippers = flipper_y - ball_y
        trigger_new_flip = False

        if ball_vy > 5 and 0 < distance_to_flippers < 30:
            # Ball approaching flippers — predict x at flipper level
            time_to_flipper = distance_to_flippers / ball_vy
            predicted_x = ball_x + ball_vx * time_to_flipper
            if predicted_x < 2:
                predicted_x = 4 - predicted_x
            elif predicted_x > 55:
                predicted_x = 110 - predicted_x

            # Trigger distance: scale with speed so fast balls are flipped a
            # little earlier (flipper needs to already be moving on contact)
            speed = math.sqrt(ball_vx * ball_vx + ball_vy * ball_vy)
            trigger_dist = 4.0 + min(4.0, speed / 80.0)

            if distance_to_flippers < trigger_dist:
                # Left flipper zone (pivot x=18, tip sweeps to ~x=7)
                if 5 < predicted_x < 33 and self.flip_l_timer <= 0:
                    self.flip_l_timer = self.flip_hold_duration
                    trigger_new_flip = True
                # Right flipper zone (pivot x=45, tip sweeps to ~x=56)
                if 30 < predicted_x < 58 and self.flip_r_timer <= 0:
                    self.flip_r_timer = self.flip_hold_duration
                    trigger_new_flip = True

        # If the ball is rolling slowly right at flipper level (e.g. rolling
        # along a raised flipper), let it drop first then flip
        # — don't hold the flipper up, that traps it.

        # Activate flippers based on hold timers
        if self.flip_l_timer > 0:
            ai_input.action_l_held = True
            ai_input.action_l = True
        if self.flip_r_timer > 0:
            ai_input.action_r_held = True
            ai_input.action_r = True

        return ai_input
