"""
Indy 500 Demo - AI Attract Mode
================================
AI races around the oval track for idle screen demos.
The AI follows the racing line, accelerating on straights and steering through turns.

AI Strategy:
- Calculate ideal angle to follow the track centerline
- Steer to match the ideal racing angle
- Always accelerate (hold gas pedal)
- Adjust steering based on upcoming track curvature
"""

import math
from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

# Import the actual game
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.indy500 import Indy500


class Indy500Demo(Visual):
    name = "INDY 500"
    description = "AI races"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = Indy500(self.display)
        self.game.reset()
        self.game_over_timer = 0.0

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

        # Compute AI steering decision
        steer_left, steer_right = self._decide_steering()

        # Create input state with AI's chosen controls
        ai_input = InputState()
        ai_input.left = steer_left
        ai_input.right = steer_right
        # Always accelerate
        ai_input.action_l_held = True

        self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()

        # Overlay "DEMO" text (blinking)
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)

    def _decide_steering(self):
        """AI decision-making for steering."""
        game = self.game

        # Current car position and angle
        car_x = game.x
        car_y = game.y
        car_angle = game.angle

        # Calculate the ideal angle to follow the track centerline
        # The track is an oval centered at (TRACK_CENTER_X, TRACK_CENTER_Y)
        # We want to drive tangent to the ellipse, moving counterclockwise

        # Vector from track center to car
        dx = car_x - game.TRACK_CENTER_X
        dy = car_y - game.TRACK_CENTER_Y

        # Calculate the angle from center to car (in ellipse space)
        # Account for ellipse aspect ratio
        track_angle = math.atan2(dy / game.TRACK_RADIUS_Y, dx / game.TRACK_RADIUS_X)

        # The tangent direction for counterclockwise motion on an ellipse
        # Derivative of ellipse parameterization: (-a*sin(t), b*cos(t))
        # Normalized to get direction
        tangent_x = -game.TRACK_RADIUS_X * math.sin(track_angle)
        tangent_y = game.TRACK_RADIUS_Y * math.cos(track_angle)

        # Target angle is the tangent direction (counterclockwise around track)
        target_angle = math.atan2(tangent_y, tangent_x)

        # Calculate angle difference (normalized to -pi to pi)
        angle_diff = target_angle - car_angle
        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi

        # Steering threshold (dead zone to prevent oscillation)
        threshold = 0.15

        # Steer to match target angle
        steer_left = False
        steer_right = False

        if angle_diff < -threshold:
            steer_left = True
        elif angle_diff > threshold:
            steer_right = True

        return steer_left, steer_right
