"""
Lunar Lander Demo - AI Attract Mode
====================================
Lunar Lander plays itself using AI to land safely on the moon.

AI Strategy:
- Control descent velocity - don't fall too fast
- Aim for the landing pad horizontally
- Use rotation to orient thrust direction
- Use main thrust to slow descent when getting close
- Keep vertical velocity low and angle upright for safe landing
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.lunarlander import LunarLander


class LunarLanderDemo(Visual):
    name = "LUNAR LANDER"
    description = "AI lands the module"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = LunarLander(self.display)
        self.game.reset()
        self.restart_timer = 0.0
        self.decision_timer = 0.0
        self.decision_interval = 0.05  # Recalculate every 50ms
        self.ai_rotate_left = False
        self.ai_rotate_right = False
        self.ai_thrust = False

    def handle_input(self, input_state):
        # Demo doesn't respond to input (auto-plays)
        return False

    def update(self, dt):
        self.time += dt

        # If game over (crashed), restart after a pause
        if self.game.state == GameState.GAME_OVER:
            self.restart_timer += dt
            if self.restart_timer > 3.0:
                self.game.reset()
                self.restart_timer = 0.0
            return

        # If landed successfully, advance to next level after a pause
        if self.game.landed:
            self.restart_timer += dt
            if self.restart_timer > 3.0:
                self.game.level += 1
                self.game.start_new_descent()
                self.restart_timer = 0.0
            return

        # Make AI decisions periodically
        self.decision_timer += dt
        if self.decision_timer >= self.decision_interval:
            self.decision_timer = 0.0
            self._decide_action()

        # Create input state with AI's chosen actions
        ai_input = InputState()
        if self.ai_rotate_left:
            ai_input.left = True
        if self.ai_rotate_right:
            ai_input.right = True
        if self.ai_thrust:
            ai_input.action_l_held = True
            ai_input.action_r_held = True

        self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()

        # Overlay "DEMO" text (blinking)
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)

    def _decide_action(self):
        """AI decision-making for Lunar Lander."""
        game = self.game

        # Reset actions
        self.ai_rotate_left = False
        self.ai_rotate_right = False
        self.ai_thrust = False

        # Get lander state
        x = game.x
        y = game.y
        vx = game.vx
        vy = game.vy
        angle = game.angle
        fuel = game.fuel

        # Find the nearest landing pad
        target_pad = self._find_best_pad()
        if target_pad is None:
            return

        pad_x_start, pad_x_end, pad_y, multiplier = target_pad
        pad_center_x = (pad_x_start + pad_x_end) / 2
        pad_width = pad_x_end - pad_x_start

        # Calculate horizontal error (how far from pad center)
        dx = pad_center_x - x

        # Calculate altitude above ground
        lander_bottom = y + game.LANDER_HEIGHT
        altitude = pad_y - lander_bottom

        # === AI LOGIC ===

        # 1. First priority: keep angle upright
        # If tilted, correct angle before doing anything else
        angle_tolerance = 0.15  # About 8 degrees
        if abs(angle) > angle_tolerance:
            if angle > 0:
                self.ai_rotate_left = True
            else:
                self.ai_rotate_right = True
            # Don't thrust while correcting angle significantly
            if abs(angle) > 0.3:
                return

        # 2. Horizontal positioning
        # If not over the pad, need to move horizontally
        # Use small angle adjustments to create horizontal thrust component
        horizontal_tolerance = pad_width / 3

        if abs(dx) > horizontal_tolerance:
            # Need to move toward pad
            # Desired horizontal velocity toward pad
            desired_vx = dx * 0.3  # Proportional control
            desired_vx = max(-8, min(8, desired_vx))  # Limit max horizontal speed

            vx_error = desired_vx - vx

            # Tilt slightly to create horizontal thrust component
            if vx_error > 1 and abs(angle) < 0.4:
                self.ai_rotate_right = True  # Tilt right to move right
            elif vx_error < -1 and abs(angle) < 0.4:
                self.ai_rotate_left = True  # Tilt left to move left

        # 3. Vertical velocity control
        # The key is to maintain a safe descent rate based on altitude

        # Calculate desired descent rate based on altitude
        # Higher up = can fall faster, lower = need to slow down
        if altitude > 30:
            max_safe_vy = 15  # Can fall faster when high
        elif altitude > 15:
            max_safe_vy = 10
        elif altitude > 8:
            max_safe_vy = 6
        else:
            max_safe_vy = 3  # Very slow near ground

        # Also slow down horizontal speed when close to ground
        if altitude < 15:
            if abs(vx) > 5:
                # Need to reduce horizontal speed
                if vx > 0 and abs(angle) < 0.3:
                    self.ai_rotate_left = True
                elif vx < 0 and abs(angle) < 0.3:
                    self.ai_rotate_right = True

        # Thrust control
        # Thrust if falling too fast OR need to counteract horizontal velocity
        should_thrust = False

        # Falling too fast?
        if vy > max_safe_vy:
            should_thrust = True

        # Very close to ground - be extra careful
        if altitude < 10:
            if vy > 5:  # Any significant downward velocity
                should_thrust = True
            # Also thrust if horizontal speed is too high for landing
            if abs(vx) > game.MAX_LATERAL_SPEED * 0.8:
                should_thrust = True

        # Don't waste fuel when high up and falling slowly
        if altitude > 35 and vy < 8:
            should_thrust = False

        # Out of fuel? Nothing we can do
        if fuel <= 0:
            should_thrust = False

        self.ai_thrust = should_thrust

    def _find_best_pad(self):
        """Find the best landing pad to target."""
        game = self.game
        x = game.x
        y = game.y

        if not game.pads:
            return None

        # Find the closest pad horizontally that we can still reach
        best_pad = None
        best_score = float('inf')

        for pad in game.pads:
            pad_x_start, pad_x_end, pad_y, multiplier = pad
            pad_center_x = (pad_x_start + pad_x_end) / 2

            # Distance to pad center
            dx = abs(pad_center_x - x)

            # Prefer closer pads, but also consider pad width (easier to land on wider pads)
            pad_width = pad_x_end - pad_x_start
            score = dx - pad_width * 0.5  # Wider pads get bonus

            # Bonus for higher multiplier pads (but don't prioritize too much)
            score -= multiplier * 2

            if score < best_score:
                best_score = score
                best_pad = pad

        return best_pad
