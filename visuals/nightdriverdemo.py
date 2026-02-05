"""
Night Driver Demo - AI Attract Mode
====================================
Night Driver plays itself with AI navigating the road at night.

AI Strategy:
- Stay on the road by tracking road edges/markers
- Steer toward center of road
- Adjust steering based on upcoming curves
- Maintain appropriate speed for turns
- Counter the curve push force to stay centered
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.nightdriver import NightDriver


class NightDriverDemo(Visual):
    name = "NIGHT DRIVER"
    description = "AI drives at night"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = NightDriver(self.display)
        self.game.reset()
        self.restart_timer = 0.0
        self.decision_timer = 0.0
        self.decision_interval = 0.03  # Recalculate every 30ms for responsive steering
        self.ai_steer_left = False
        self.ai_steer_right = False
        self.ai_gas = True  # AI holds gas by default

    def handle_input(self, input_state):
        # Demo doesn't respond to input (auto-plays)
        return False

    def update(self, dt):
        self.time += dt

        # If game over, restart after a pause by pressing gas
        if self.game.state == GameState.GAME_OVER:
            self.restart_timer += dt
            if self.restart_timer > 3.0:
                restart_input = InputState()
                restart_input.action_l = True
                self.game.update(restart_input, dt)
                self.restart_timer = 0.0
            return

        # If crashed but not yet game over, keep updating so crash_timer runs
        if self.game.crashed:
            self.game.update(InputState(), dt)
            return

        # Make AI decisions periodically
        self.decision_timer += dt
        if self.decision_timer >= self.decision_interval:
            self.decision_timer = 0.0
            self._decide_action()

        # Create input state with AI's chosen actions
        ai_input = InputState()
        if self.ai_steer_left:
            ai_input.left = True
        if self.ai_steer_right:
            ai_input.right = True
        if self.ai_gas:
            ai_input.action_l = True

        self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()

        # Overlay "DEMO" text (blinking)
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)

    def _decide_action(self):
        """AI decision-making for Night Driver.

        Physics-based approach: calculate the curve push rate the game applies,
        add a position correction term, and steer based on the net desired rate.
        """
        game = self.game

        self.ai_steer_left = False
        self.ai_steer_right = False

        player_x = game.player_x  # -1.0 to 1.0, 0 = center
        curve = game.curve
        speed = game.speed
        max_speed = game.max_speed

        # Gas control: let off gas in sharp curves, floor it on straights
        # Sharper curve + higher speed = more reason to coast
        curve_severity = abs(curve) * (speed / max_speed)
        self.ai_gas = curve_severity < 0.4

        # Replicate the game's physics to know the exact push rate
        speed_factor = speed / max_speed
        steer_speed = 2.0 + speed_factor * 1.5
        curve_push = curve * 0.5
        curve_push = max(-steer_speed * 0.75, min(steer_speed * 0.75, curve_push))
        # Positive curve_push → player_x decreases (pushed left)
        # To counter, we need positive steer rate (steer right)

        # Check for oncoming traffic - emergency dodge if in danger zone
        oncoming_near = False
        for car in game.oncoming_cars:
            if car['z'] < 0.7 and car['z'] > -0.05:
                oncoming_near = True
                break

        # Emergency: oncoming car close and we're in their lane
        # Danger zone extends to x~0.14 for wide vehicles (semi trucks)
        if oncoming_near and player_x < 0.15:
            self.ai_steer_right = True
            return

        # Slight right bias to avoid oncoming traffic in left lane
        # Oncoming cars at x = -0.55 to -0.35, collision width ~0.35
        target_x = 0.2 if oncoming_near else 0.08

        # Position correction: steer toward target with proportional gain
        correction = (target_x - player_x) * 4.0

        # Total desired steering rate = counter curve + correct position
        desired_rate = curve_push + correction

        # Dead zone to prevent oscillation when nearly centered
        if desired_rate > 0.15:
            self.ai_steer_right = True
        elif desired_rate < -0.15:
            self.ai_steer_left = True

        # Emergency override near road edges (crash at ±0.85)
        if player_x > 0.75:
            self.ai_steer_left = True
            self.ai_steer_right = False
        elif player_x < -0.75:
            self.ai_steer_right = True
            self.ai_steer_left = False
