"""
Asteroids Demo - AI Attract Mode
================================
Asteroids plays itself using simple AI for idle screen demos.
The AI navigates, shoots asteroids, and dodges threats.

AI Strategy:
- Find nearest asteroid (or UFO if present)
- Rotate ship toward target
- Thrust to approach (but not too close)
- Shoot when aimed at target
- Dodge when threats are very close
"""

import math
from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

# Import the actual game
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.asteroids import Asteroids


class AsteroidsDemo(Visual):
    name = "ASTROIDS"
    description = "AI plays Asteroids"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = Asteroids(self.display)
        self.game.reset()
        self.decision_timer = 0.0
        self.decision_interval = 0.05  # Recalculate every 50ms
        self.ai_rotate = 0  # -1 left, 0 none, 1 right
        self.ai_thrust = False
        self.ai_shoot = False
        self.restart_timer = 0.0

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

        # Make AI decisions periodically
        self.decision_timer += dt
        if self.decision_timer >= self.decision_interval:
            self.decision_timer = 0.0
            self._decide_action()

        # Create input state with AI's chosen actions
        ai_input = InputState()
        if self.ai_rotate < 0:
            ai_input.left = True
        elif self.ai_rotate > 0:
            ai_input.right = True
        if self.ai_thrust:
            ai_input.up = True
        if self.ai_shoot:
            ai_input.action_l = True

        self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()

        # Overlay "DEMO" text
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)

    def _decide_action(self):
        """AI decision-making for Asteroids."""
        game = self.game
        ship_x, ship_y = game.ship_x, game.ship_y
        ship_angle = game.ship_angle

        # Reset actions
        self.ai_rotate = 0
        self.ai_thrust = False
        self.ai_shoot = False

        # Check for immediate danger (very close asteroid or UFO bullet)
        danger_dist, danger_angle = self._find_nearest_danger()
        if danger_dist < 8:
            # Dodge: thrust perpendicular to danger
            escape_angle = danger_angle + math.pi / 2
            angle_diff = self._normalize_angle(escape_angle - ship_angle)
            if abs(angle_diff) > 0.5:
                self.ai_rotate = 1 if angle_diff > 0 else -1
            self.ai_thrust = True
            return

        # Find target (UFO if present, otherwise nearest asteroid)
        target = self._find_target()
        if target is None:
            return

        target_x, target_y = target

        # Calculate angle to target
        target_angle = math.atan2(target_y - ship_y, target_x - ship_x)
        angle_diff = self._normalize_angle(target_angle - ship_angle)

        # Rotate toward target
        if abs(angle_diff) > 0.1:
            self.ai_rotate = 1 if angle_diff > 0 else -1

        # Calculate distance to target
        dist = self._wrapped_distance(ship_x, ship_y, target_x, target_y)

        # Thrust to approach if not too close
        if dist > 15:
            # Only thrust if roughly aimed in the right direction
            if abs(angle_diff) < 1.0:
                self.ai_thrust = True
        elif dist < 10:
            # Too close, maybe back off (thrust opposite direction)
            # For now, just don't thrust forward
            pass

        # Shoot when aimed at target
        if abs(angle_diff) < 0.3:
            self.ai_shoot = True

    def _find_target(self):
        """Find the best target to shoot at."""
        game = self.game
        ship_x, ship_y = game.ship_x, game.ship_y

        # Prioritize UFO if present
        if game.ufo:
            return (game.ufo['x'], game.ufo['y'])

        # Find nearest asteroid
        nearest_dist = float('inf')
        nearest_pos = None

        for asteroid in game.asteroids:
            dist = self._wrapped_distance(ship_x, ship_y, asteroid['x'], asteroid['y'])
            if dist < nearest_dist:
                nearest_dist = dist
                nearest_pos = (asteroid['x'], asteroid['y'])

        return nearest_pos

    def _find_nearest_danger(self):
        """Find the nearest danger (asteroid or UFO bullet) and return distance and angle."""
        game = self.game
        ship_x, ship_y = game.ship_x, game.ship_y

        nearest_dist = float('inf')
        nearest_angle = 0

        # Check asteroids
        for asteroid in game.asteroids:
            dist = self._wrapped_distance(ship_x, ship_y, asteroid['x'], asteroid['y'])
            # Account for asteroid size
            effective_dist = dist - asteroid['size'] * 2
            if effective_dist < nearest_dist:
                nearest_dist = effective_dist
                nearest_angle = math.atan2(asteroid['y'] - ship_y, asteroid['x'] - ship_x)

        # Check UFO bullets
        for bullet in game.ufo_bullets:
            dist = self._wrapped_distance(ship_x, ship_y, bullet['x'], bullet['y'])
            if dist < nearest_dist:
                nearest_dist = dist
                nearest_angle = math.atan2(bullet['y'] - ship_y, bullet['x'] - ship_x)

        # Check UFO itself
        if game.ufo:
            dist = self._wrapped_distance(ship_x, ship_y, game.ufo['x'], game.ufo['y'])
            if dist < nearest_dist:
                nearest_dist = dist
                nearest_angle = math.atan2(game.ufo['y'] - ship_y, game.ufo['x'] - ship_x)

        return nearest_dist, nearest_angle

    def _wrapped_distance(self, x1, y1, x2, y2):
        """Calculate distance accounting for screen wrap."""
        # Simple distance for now (screen wrap makes this complex)
        dx = x2 - x1
        dy = y2 - y1

        # Account for horizontal wrap
        if abs(dx) > GRID_SIZE / 2:
            dx = GRID_SIZE - abs(dx) if dx > 0 else -(GRID_SIZE - abs(dx))

        # Account for vertical wrap (play area is 8 to 64)
        play_height = GRID_SIZE - 8
        if abs(dy) > play_height / 2:
            dy = play_height - abs(dy) if dy > 0 else -(play_height - abs(dy))

        return math.sqrt(dx * dx + dy * dy)

    def _normalize_angle(self, angle):
        """Normalize angle to -pi to pi."""
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        return angle
