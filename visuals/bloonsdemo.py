"""
Bloons Demo - AI Attract Mode
==============================
Bloons plays itself using AI for idle screen demos.
The AI simulates trajectories and picks the angle/power
that pops the most bloons per dart (including child chains).

AI Strategy:
- Sweep angles × power levels, simulate full dart flight
- Score each trajectory by total pops (dart passes through bloons)
- Child bloons from multi-layer pops are included in the count
- Refine around best with fine grid search
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
    MONKEY_X, MONKEY_Y, MAX_SPEED, BASE_VY, GRAVITY, GROUND_Y,
    DART_RADIUS, BLOON_TYPES,
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

    def _simulate_pops(self, angle, power, alive_bloons):
        """Simulate dart flight and count total pops including child chains."""
        dart_x = float(MONKEY_X + 3)
        dart_y = float(MONKEY_Y - 2)
        vx = math.cos(angle) * power * MAX_SPEED
        vy = -math.sin(angle) * power * BASE_VY

        sim_dt = 0.005
        radius_sq = DART_RADIUS * DART_RADIUS

        # [x, y, type_idx, alive] — children appended during sim
        bloons = [[b['x'], b['y'], b['type'], True] for b in alive_bloons]
        total_pops = 0
        best_dist_sq = float('inf')

        for _ in range(600):
            vy += GRAVITY * sim_dt
            dart_x += vx * sim_dt
            dart_y += vy * sim_dt

            i = 0
            while i < len(bloons):
                b = bloons[i]
                if b[3]:
                    dx = dart_x - b[0]
                    dy = dart_y - b[1]
                    dsq = dx * dx + dy * dy
                    if dsq < radius_sq:
                        b[3] = False
                        total_pops += 1
                        child_idx = BLOON_TYPES[b[2]][2]
                        if child_idx >= 0:
                            bloons.append([b[0], b[1], child_idx, True])
                    elif dsq < best_dist_sq:
                        best_dist_sq = dsq
                i += 1

            if dart_x > 66 or dart_x < -5 or dart_y > GROUND_Y + 2 or dart_y < -20:
                break

        # Score: pops first, then closeness as tiebreaker
        return (total_pops, -best_dist_sq)

    def _compute_aim(self):
        """Sweep angle × power grid, pick trajectory that pops the most."""
        alive = [b for b in self.game.bloons if b['alive']]
        if not alive:
            self.target_angle = 0.7
            self.target_power = 0.5
            return

        best_score = (-1, float('-inf'))
        best_angle = 0.7
        best_power = 0.5

        # Coarse sweep: 12 angles × 6 power levels
        for ai in range(12):
            angle = MIN_ANGLE + (MAX_ANGLE - MIN_ANGLE) * ai / 11.0
            for pi in range(6):
                power = 0.15 + 0.8 * pi / 5.0
                score = self._simulate_pops(angle, power, alive)
                if score > best_score:
                    best_score = score
                    best_angle = angle
                    best_power = power

        # Refine: fine grid around best
        for da in [-0.05, -0.025, 0.025, 0.05]:
            for dp in [-0.06, -0.03, 0.0, 0.03, 0.06]:
                a = best_angle + da
                p = best_power + dp
                if a < MIN_ANGLE or a > MAX_ANGLE or p < 0.15 or p > 0.95:
                    continue
                score = self._simulate_pops(a, p, alive)
                if score > best_score:
                    best_score = score
                    best_angle = a
                    best_power = p

        self.target_angle = max(MIN_ANGLE, min(MAX_ANGLE, best_angle))
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
