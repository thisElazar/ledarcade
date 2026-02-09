"""
Pool Demo - AI Attract Mode
============================
AI plays pool for idle screen demos.

AI Strategy:
- Select 1P mode automatically
- AIMING: pick a random object ball, compute angle from cue ball to target,
  steer aim_angle toward that angle using left/right held input, add slight
  random offset for variety. Press action when within tolerance.
- POWER: wait for the oscillating power bar to reach the 0.45-0.7 sweet spot,
  then fire. Must not send any direction input (would cancel back to aiming).
- SHOOTING/SCORING/FOUL/TURN_CHANGE: no input, let timers handle.
- GAME_OVER: restart after 3 second pause, pick fresh target.
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState
import math
import random

# Import the actual game
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.pool import (
    Pool, PHASE_MODE_SELECT, PHASE_AIMING, PHASE_POWER,
    PHASE_SHOOTING, PHASE_SCORING, PHASE_FOUL, PHASE_TURN_CHANGE,
)


class PoolDemo(Visual):
    name = "POOL"
    description = "AI plays pool"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = Pool(self.display)
        self.game.reset()
        self.game_over_timer = 0.0

        # AI state
        self.target_angle = 0.0
        self._pick_target()

    def _pick_target(self):
        """Choose a random object ball and compute target angle with small offset."""
        cue = self.game._cue_ball()
        objects = self.game._object_balls()
        if not cue or not objects:
            self.target_angle = random.uniform(0, 2 * math.pi)
            return

        target_ball = random.choice(objects)
        dx = target_ball.x - cue.x
        dy = target_ball.y - cue.y
        angle = math.atan2(dy, dx)

        # Add slight random offset for variety (+/- ~6 degrees)
        angle += random.uniform(-0.1, 0.1)
        self.target_angle = angle % (2 * math.pi)

    def _steer_toward(self, target_angle, current_angle):
        """Return (left, right) bools to steer current toward target angle."""
        diff = (target_angle - current_angle + math.pi) % (2 * math.pi) - math.pi
        # diff in (-pi, pi]: positive means turn right, negative means turn left
        if diff > 0.05:
            return False, True
        elif diff < -0.05:
            return True, False
        return False, False

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
                self._pick_target()
            return

        # Create AI input based on current phase
        ai_input = InputState()
        phase = self.game.phase

        if phase == PHASE_MODE_SELECT:
            # Select 1P mode (already selected by default)
            ai_input.action_l = True

        elif phase == PHASE_AIMING:
            # Steer toward target angle
            left, right = self._steer_toward(self.target_angle, self.game.aim_angle)
            ai_input.left = left
            ai_input.right = right

            # When close enough, press action to start power
            diff = abs((self.target_angle - self.game.aim_angle + math.pi)
                       % (2 * math.pi) - math.pi)
            if diff < 0.05:
                ai_input.left = False
                ai_input.right = False
                ai_input.action_l = True

        elif phase == PHASE_POWER:
            # Wait for power to reach sweet spot (0.45-0.7), then fire
            # IMPORTANT: no direction input or it cancels back to aiming
            if 0.45 <= self.game.power <= 0.7:
                ai_input.action_l = True

        elif phase == PHASE_SHOOTING:
            # Physics running, no input needed
            pass

        elif phase == PHASE_SCORING:
            # Timer-based, auto-advances
            pass

        elif phase == PHASE_FOUL:
            # Timer-based, auto-advances
            pass

        elif phase == PHASE_TURN_CHANGE:
            # Timer-based, auto-advances
            pass

        # Pick a new target each time we enter aiming phase
        if phase == PHASE_AIMING and not hasattr(self, '_was_aiming'):
            self._was_aiming = True
            self._pick_target()
        elif phase != PHASE_AIMING:
            self._was_aiming = False

        self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()

        # Overlay "DEMO" text (blinking)
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)
