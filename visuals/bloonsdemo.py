"""
Bloons Demo - AI Attract Mode
==============================
Bloons plays itself using AI for idle screen demos.
The AI estimates angle and power from bloon positions,
aims toward the center of mass of alive bloons, and
charges power proportional to distance.

AI Strategy:
- PHASE_AIM: Steer toward a target angle based on bloon cluster position
- PHASE_POWER: Hold button to charge, release when target power reached
- PHASE_LEVEL_WIN / PHASE_LEVEL_FAIL: Press action to advance
- GAME_OVER: Restart after 3 seconds
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState
import math
import random
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.bloons import (
    Bloons, PHASE_AIM, PHASE_POWER, PHASE_FLIGHT, PHASE_RESULT,
    PHASE_LEVEL_WIN, PHASE_LEVEL_FAIL, MIN_ANGLE, MAX_ANGLE,
    MONKEY_X, MONKEY_Y, MAX_SPEED, BASE_VY, GRAVITY, GROUND_Y
)


class BloonsDemo(Visual):
    name = "BLOONS"
    description = "AI pops bloons"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = Bloons(self.display)
        self.game.reset()
        self.game_over_timer = 0.0

        # AI state
        self.target_angle = 0.7
        self.target_power = 0.5
        self.charge_timer = 0.0
        self._compute_aim()

    def handle_input(self, input_state):
        return False

    def update(self, dt):
        self.time += dt

        # Restart after game over
        if self.game.state == GameState.GAME_OVER:
            self.game_over_timer += dt
            if self.game_over_timer > 3.0:
                self.game.reset()
                self.game_over_timer = 0.0
                self._compute_aim()
            return

        ai_input = InputState()

        if self.game.phase == PHASE_AIM:
            self._ai_aim(ai_input, dt)
        elif self.game.phase == PHASE_POWER:
            self._ai_power(ai_input, dt)
        elif self.game.phase == PHASE_LEVEL_WIN:
            ai_input.action_l = True
        elif self.game.phase == PHASE_LEVEL_FAIL:
            ai_input.action_l = True

        self.game.update(ai_input, dt)

        # Recompute aim when returning to aim phase after a throw
        if self.game.phase == PHASE_AIM and self.charge_timer > 0:
            self.charge_timer = 0.0
            self._compute_aim()

    def draw(self):
        self.game.draw()

        # Blinking DEMO overlay
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)

    def _compute_aim(self):
        """Calculate target angle and power from alive bloon positions."""
        alive = [b for b in self.game.bloons if b['alive']]
        if not alive:
            self.target_angle = 0.7
            self.target_power = 0.5
            return

        avg_x = sum(b['x'] for b in alive) / len(alive)
        avg_y = sum(b['y'] for b in alive) / len(alive)

        dx = avg_x - MONKEY_X
        dy = MONKEY_Y - avg_y
        dist = math.sqrt(dx * dx + dy * dy)

        # Angle: steeper for closer/higher targets, shallower for far targets
        raw_angle = math.atan2(dy, dx) * 0.7
        self.target_angle = max(MIN_ANGLE, min(MAX_ANGLE, raw_angle))
        # Add small random variation for natural feel
        self.target_angle += random.uniform(-0.08, 0.08)
        self.target_angle = max(MIN_ANGLE, min(MAX_ANGLE, self.target_angle))

        # Power: proportional to distance
        self.target_power = max(0.3, min(0.9, dist / 60.0))
        self.target_power += random.uniform(-0.05, 0.05)
        self.target_power = max(0.3, min(0.9, self.target_power))

    def _ai_aim(self, ai_input, dt):
        """Steer toward target angle, press action when close enough."""
        diff = self.target_angle - self.game.angle
        if abs(diff) > 0.05:
            if diff > 0:
                ai_input.up = True
            else:
                ai_input.down = True
        else:
            # Close enough -- start charging
            ai_input.action_l = True
            self.charge_timer = 0.0

    def _ai_power(self, ai_input, dt):
        """Hold button until target power reached, then release."""
        charge_duration = self.target_power / 0.8  # POWER_CHARGE_SPEED is 0.8/s
        self.charge_timer += dt
        if self.charge_timer < charge_duration:
            ai_input.action_l_held = True
        # else: release (action_l_held stays False) -- dart fires
