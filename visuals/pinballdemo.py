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

        # Get flipper positions
        left_pivot_x, left_pivot_y = FLIPPER_LEFT_PIVOT
        right_pivot_x, right_pivot_y = FLIPPER_RIGHT_PIVOT

        # Define flipper activation zones
        # Flippers are at y~173, activate when ball is approaching and nearby
        flipper_y = left_pivot_y  # Both at same y

        # Predict where ball will be when it reaches flipper level
        if ball_vy > 5:  # Ball moving down toward flippers
            time_to_flipper = (flipper_y - ball_y) / ball_vy if ball_vy > 0 else 999
            predicted_x = ball_x + ball_vx * time_to_flipper

            # Account for wall bounces (simplified)
            if predicted_x < 2:
                predicted_x = 4 - predicted_x
            elif predicted_x > 55:
                predicted_x = 110 - predicted_x

            # Activation distance - how close the ball needs to be
            activation_distance_y = 25  # Start preparing when ball is this close
            trigger_distance_y = 12     # Actually flip when ball is this close

            distance_to_flippers = flipper_y - ball_y

            if distance_to_flippers < activation_distance_y and distance_to_flippers > 0:
                # Ball is approaching flippers

                # Left flipper: activate for balls on left side
                # Left flipper pivot at x=18, covers roughly x=7 to x=29
                left_zone_min = 5
                left_zone_max = 32

                # Right flipper: activate for balls on right side
                # Right flipper pivot at x=45, covers roughly x=34 to x=56
                right_zone_min = 30
                right_zone_max = 56

                # Use predicted position for early activation, current position for triggering
                use_predicted = distance_to_flippers > trigger_distance_y
                check_x = predicted_x if use_predicted else ball_x

                # Timing adjustment - flip earlier for faster balls
                speed = math.sqrt(ball_vx * ball_vx + ball_vy * ball_vy)
                speed_factor = min(1.0, speed / 150.0)  # Normalize speed
                adjusted_trigger = trigger_distance_y + speed_factor * 8

                # Left flipper activation
                if left_zone_min < check_x < left_zone_max:
                    if distance_to_flippers < adjusted_trigger:
                        ai_input.action_l_held = True
                        ai_input.action_l = True

                # Right flipper activation
                if right_zone_min < check_x < right_zone_max:
                    if distance_to_flippers < adjusted_trigger:
                        ai_input.action_r_held = True
                        ai_input.action_r = True

        else:
            # Ball going up or sideways - hold flippers down (rest position)
            # But activate if ball is very close and moving across
            if ball_y > flipper_y - 10 and ball_y < flipper_y + 5:
                # Ball is at flipper level, react quickly
                if ball_x < 32 and ball_vy > -20:
                    ai_input.action_l_held = True
                    ai_input.action_l = True
                if ball_x > 32 and ball_vy > -20:
                    ai_input.action_r_held = True
                    ai_input.action_r = True

        return ai_input
