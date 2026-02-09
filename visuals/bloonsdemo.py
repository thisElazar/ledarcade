"""
Bloons Demo - AI Attract Mode
==============================
Bloons plays itself using AI for idle screen demos.
The AI uses trajectory simulation to find the optimal
angle and power to hit the densest bloon cluster.

AI Strategy:
- Pick target bloon from densest cluster (most neighbors within 8px)
- Sweep angles × power levels, simulate projectile trajectory
- Pick angle/power with smallest distance to target bloon
- Refine with binary search around best angle
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

    def _find_best_target(self, alive):
        """Pick the bloon in the densest cluster (most neighbors within 8px)."""
        if len(alive) == 1:
            return alive[0]

        best_bloon = alive[0]
        best_count = 0
        for b in alive:
            count = 0
            for other in alive:
                if other is b:
                    continue
                d = math.hypot(b['x'] - other['x'], b['y'] - other['y'])
                if d < 8.0:
                    count += 1
            if count > best_count:
                best_count = count
                best_bloon = b
        return best_bloon

    def _simulate_trajectory(self, angle, power, target_x, target_y):
        """Simulate dart flight and return minimum distance to target.
        Uses small dt matching game's 3-substep physics for accuracy."""
        dart_x = float(MONKEY_X + 3)
        dart_y = float(MONKEY_Y - 2)
        vx = math.cos(angle) * power * MAX_SPEED
        vy = -math.sin(angle) * BASE_VY

        # Match game's substep size (~0.016/3 ≈ 0.005) for accurate trajectory
        sim_dt = 0.005
        best_dist = float('inf')

        for _ in range(800):
            vy += GRAVITY * sim_dt
            dart_x += vx * sim_dt
            dart_y += vy * sim_dt

            d = math.hypot(dart_x - target_x, dart_y - target_y)
            if d < best_dist:
                best_dist = d

            # Out of bounds
            if dart_x > 66 or dart_x < -5 or dart_y > GROUND_Y + 2 or dart_y < -20:
                break

        return best_dist

    def _compute_aim(self):
        """Calculate target angle and power using trajectory simulation."""
        alive = [b for b in self.game.bloons if b['alive']]
        if not alive:
            self.target_angle = 0.7
            self.target_power = 0.5
            return

        target = self._find_best_target(alive)
        tx = target['x']  # collision checks distance to top-left corner
        ty = target['y']

        # Coarse sweep: 14 angles × 7 power levels
        best_dist = float('inf')
        best_angle = 0.7
        best_power = 0.5

        for ai in range(14):
            angle = MIN_ANGLE + (MAX_ANGLE - MIN_ANGLE) * ai / 13.0
            for pi in range(7):
                power = 0.2 + 0.7 * pi / 6.0
                d = self._simulate_trajectory(angle, power, tx, ty)
                if d < best_dist:
                    best_dist = d
                    best_angle = angle
                    best_power = power

        # Refine angle with binary search (±0.1 around best)
        lo = max(MIN_ANGLE, best_angle - 0.1)
        hi = min(MAX_ANGLE, best_angle + 0.1)
        for _ in range(8):
            mid = (lo + hi) / 2.0
            d_lo = self._simulate_trajectory(lo, best_power, tx, ty)
            d_hi = self._simulate_trajectory(hi, best_power, tx, ty)
            if d_lo < d_hi:
                hi = mid
            else:
                lo = mid
        refined_angle = (lo + hi) / 2.0

        # Also refine power
        d_refined = self._simulate_trajectory(refined_angle, best_power, tx, ty)
        for dp in [-0.05, 0.05, -0.1, 0.1]:
            p = best_power + dp
            if p < 0.15 or p > 0.95:
                continue
            d = self._simulate_trajectory(refined_angle, p, tx, ty)
            if d < d_refined:
                d_refined = d
                best_power = p

        self.target_angle = max(MIN_ANGLE, min(MAX_ANGLE, refined_angle))
        self.target_power = max(0.15, min(0.95, best_power))

    def _ai_aim(self, ai_input, dt):
        """Steer toward target angle, press action when close enough."""
        diff = self.target_angle - self.game.angle
        if abs(diff) > 0.03:
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
