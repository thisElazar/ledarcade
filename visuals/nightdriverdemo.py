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

    def handle_input(self, input_state):
        # Demo doesn't respond to input (auto-plays)
        return False

    def update(self, dt):
        self.time += dt

        # If game over, restart after a pause
        if self.game.state == GameState.GAME_OVER:
            self.restart_timer += dt
            if self.restart_timer > 3.0:
                self.game.reset()
                self.restart_timer = 0.0
            return

        # If crashed but not yet game over, wait
        if self.game.crashed:
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

        self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()

        # Overlay "DEMO" text (blinking)
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)

    def _decide_action(self):
        """AI decision-making for Night Driver."""
        game = self.game

        # Reset actions
        self.ai_steer_left = False
        self.ai_steer_right = False

        # Get current state
        player_x = game.player_x  # -1.0 to 1.0, 0 = center
        curve = game.curve  # Current curve amount (positive = road bends right)
        target_curve = game.target_curve  # Where we're heading
        speed = game.speed
        max_speed = game.max_speed

        # Road edges are at +/- 0.85 (crash at 0.85)
        # Want to stay well within that range
        safe_margin = 0.65  # Stay within +/- 0.65 for safety buffer

        # === AI LOGIC ===

        # 1. Calculate target position
        # We want to stay near center, but anticipate curves
        # When a curve is coming, pre-position slightly into the curve direction
        # This counters the curve push that will push us outward

        # Anticipation factor based on current and upcoming curve
        # Positive curve pushes player left (player_x decreases)
        # So we want to be positioned slightly right (positive x) before right curves
        curve_anticipation = 0.0

        if abs(target_curve) > 0.5:
            # Anticipate the upcoming curve direction
            # Position ourselves slightly into the curve to counter the push
            curve_anticipation = target_curve * 0.15

        if abs(curve) > 0.5:
            # Also react to current curve - counter the push
            curve_anticipation += curve * 0.2

        # Clamp anticipation to reasonable range
        curve_anticipation = max(-0.3, min(0.3, curve_anticipation))

        # Target position: slightly offset based on curve anticipation
        target_x = curve_anticipation

        # 2. Calculate position error
        position_error = target_x - player_x

        # 3. Steering decision
        # Use proportional control with some dead zone to avoid oscillation
        speed_factor = speed / max_speed

        # Steering sensitivity increases with speed since we need faster reactions
        # but also the game's steering is already speed-scaled
        dead_zone = 0.05  # Small dead zone to prevent jitter

        # Urgency increases if we're getting close to the edge
        edge_urgency = 0.0
        if abs(player_x) > 0.6:
            # Getting close to edge - increase urgency
            edge_urgency = (abs(player_x) - 0.6) * 3.0

        # Strong urgency when very close to crash zone
        if abs(player_x) > 0.75:
            edge_urgency = 2.0

        # Combine position error with edge urgency
        if player_x > 0.6:
            # Too far right - need to go left
            position_error -= edge_urgency
        elif player_x < -0.6:
            # Too far left - need to go right
            position_error += edge_urgency

        # Apply steering
        if position_error > dead_zone:
            self.ai_steer_right = True
        elif position_error < -dead_zone:
            self.ai_steer_left = True

        # 4. Emergency steering near edges
        # If very close to crash, override everything
        if player_x > 0.8:
            self.ai_steer_left = True
            self.ai_steer_right = False
        elif player_x < -0.8:
            self.ai_steer_right = True
            self.ai_steer_left = False

        # 5. Counter the curve push actively
        # The game pushes the player outward during curves
        # We need to steer into the curve to counter this
        if abs(curve) > 1.0:
            # Curve is pushing us - steer to counter
            # Positive curve pushes player_x negative (leftward)
            # So we steer right to counter positive curves
            if curve > 1.0 and not self.ai_steer_left:
                self.ai_steer_right = True
            elif curve < -1.0 and not self.ai_steer_right:
                self.ai_steer_left = True
