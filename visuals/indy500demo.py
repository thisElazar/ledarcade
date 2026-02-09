"""
Indy 500 Demo - AI Attract Mode
================================
AI races around the oval track for idle screen demos.

AI Strategy:
- Steer toward a lookahead point on the track centerline
- Lookahead distance increases when car drifts off-center (self-correcting)
- Always accelerate (hold gas pedal)
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
        """AI decision-making: steer toward a lookahead point on the centerline."""
        game = self.game

        car_x = game.x
        car_y = game.y
        car_angle = game.angle

        # Find car's parametric angle on the ellipse
        dx = car_x - game.TRACK_CENTER_X
        dy = car_y - game.TRACK_CENTER_Y
        track_angle = math.atan2(dy / game.TRACK_RADIUS_Y,
                                 dx / game.TRACK_RADIUS_X)

        # Centerline point at car's current angle
        center_x = game.TRACK_CENTER_X + game.TRACK_RADIUS_X * math.cos(track_angle)
        center_y = game.TRACK_CENTER_Y + game.TRACK_RADIUS_Y * math.sin(track_angle)

        # Distance from centerline — look further ahead when drifting off-center
        off_x = car_x - center_x
        off_y = car_y - center_y
        offset_dist = math.sqrt(off_x * off_x + off_y * off_y)
        half_width = game.TRACK_WIDTH / 2

        base_lookahead = 0.25
        correction = min(offset_dist / half_width, 1.0) * 0.2
        lookahead = base_lookahead + correction

        # Target point on centerline ahead of car (track_angle increases in
        # the driving direction — counterclockwise on screen)
        ahead_angle = track_angle + lookahead
        target_x = game.TRACK_CENTER_X + game.TRACK_RADIUS_X * math.cos(ahead_angle)
        target_y = game.TRACK_CENTER_Y + game.TRACK_RADIUS_Y * math.sin(ahead_angle)

        # Desired heading toward the lookahead point
        desired_angle = math.atan2(target_y - car_y, target_x - car_x)

        # Angle difference (normalized to -pi..pi)
        angle_diff = desired_angle - car_angle
        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi

        threshold = 0.08
        steer_left = angle_diff < -threshold
        steer_right = angle_diff > threshold

        return steer_left, steer_right
