"""
SkiFree Demo - AI Attract Mode
==============================
SkiFree plays itself using AI for idle screen demos.
The AI navigates downhill, avoiding trees, rocks, and other obstacles.

AI Strategy:
- Look ahead at upcoming obstacles (trees, rocks)
- Steer left/right to avoid obstacles within a distance threshold
- Prefer center of screen when no obstacles ahead
- Use boost occasionally to escape the Yeti
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

# Import the actual game
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.skifree import SkiFree


class SkiFreeDemo(Visual):
    name = "SKIFREE DEMO"
    description = "AI skis down"
    category = "demos"

    # AI constants
    LOOK_AHEAD_NEAR = 15    # Close obstacle distance
    LOOK_AHEAD_FAR = 35     # Far obstacle distance
    AVOID_WIDTH = 8         # How wide to check for obstacles
    CENTER_PULL = 0.3       # How much AI wants to stay centered

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = SkiFree(self.display)
        self.game.reset()
        self.decision_timer = 0.0
        self.decision_interval = 0.1  # Recalculate every 100ms
        self.ai_direction = 0  # -1 left, 0 straight, 1 right
        self.ai_boost = False
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
                self.decision_timer = 0.0
            return

        # Make AI decisions periodically
        self.decision_timer += dt
        if self.decision_timer >= self.decision_interval:
            self.decision_timer = 0.0
            self._decide_action()

        # Create input state with AI's chosen action
        ai_input = InputState()
        if self.ai_direction < 0:
            ai_input.left = True
        elif self.ai_direction > 0:
            ai_input.right = True

        if self.ai_boost:
            ai_input.action_l_held = True

        self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()

        # Overlay "DEMO" text (blinking)
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)

    def _decide_action(self):
        """AI decision-making for SkiFree movement."""
        game = self.game

        # If crashed, just wait
        if game.crashed:
            self.ai_direction = 0
            self.ai_boost = False
            return

        # Get player position in world space
        player_x = game.player_x
        player_y = game.distance + game.player_y  # World Y position

        # Scan for obstacles ahead
        threat_left = 0.0
        threat_right = 0.0
        threat_center = 0.0

        for obs in game.obstacles:
            # Only consider solid obstacles (trees, rocks)
            if obs['type'] not in ('small_tree', 'large_tree', 'rock'):
                continue

            # Distance ahead (positive = in front)
            obs_distance = obs['y'] - player_y

            # Only look at obstacles ahead, within look-ahead range
            if obs_distance < 0 or obs_distance > self.LOOK_AHEAD_FAR:
                continue

            # Horizontal offset from player
            dx = obs['x'] - player_x
            obs_width = obs['w']

            # Calculate threat level (closer = more threat)
            if obs_distance < self.LOOK_AHEAD_NEAR:
                threat_factor = 2.0  # High threat when close
            else:
                threat_factor = 1.0 - (obs_distance - self.LOOK_AHEAD_NEAR) / (self.LOOK_AHEAD_FAR - self.LOOK_AHEAD_NEAR)

            # Check which zone the obstacle is in
            if dx < -self.AVOID_WIDTH:
                # Obstacle is far left, no concern
                pass
            elif dx > self.AVOID_WIDTH:
                # Obstacle is far right, no concern
                pass
            elif dx < -2:
                # Obstacle is to the left
                threat_left += threat_factor
            elif dx > 2:
                # Obstacle is to the right
                threat_right += threat_factor
            else:
                # Obstacle is dead center
                threat_center += threat_factor * 2.0

        # Decide direction based on threats
        if threat_center > 0.5 or threat_left > 0 or threat_right > 0:
            # Need to dodge
            if threat_left > threat_right:
                # More threats on left, go right
                self.ai_direction = 1
            elif threat_right > threat_left:
                # More threats on right, go left
                self.ai_direction = -1
            elif threat_center > 0:
                # Something dead ahead, pick a direction
                # Prefer to stay near center of world (around x=32)
                if player_x > 32:
                    self.ai_direction = -1
                else:
                    self.ai_direction = 1
            else:
                self.ai_direction = 0
        else:
            # No immediate threats - drift toward center
            if player_x < 20:
                self.ai_direction = 1  # Go right
            elif player_x > 44:
                self.ai_direction = -1  # Go left
            else:
                self.ai_direction = 0  # Straight down

        # Boost logic - use when Yeti is close
        self.ai_boost = False
        if game.yeti_active and game.boost_fuel > 0.5:
            # Calculate distance to Yeti
            yeti_dx = game.yeti_x - player_x
            yeti_dy = game.yeti_y - player_y
            yeti_dist = (yeti_dx * yeti_dx + yeti_dy * yeti_dy) ** 0.5

            # Boost if Yeti is getting close
            if yeti_dist < 30:
                self.ai_boost = True
