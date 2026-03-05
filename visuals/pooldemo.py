"""
Pool Demo - AI Attract Mode
============================
AI plays pool for idle screen demos using ghost ball targeting.

AI Strategy:
- Select 1P mode automatically
- AIMING: For each ball × pocket, compute ghost ball position
  (behind ball, opposite pocket). Check line-of-sight from cue.
  Score by clear path, distance, cut angle. Aim at best ghost ball.
- POWER: Proportional to distance from cue to ghost ball.
- SHOOTING/SCORING/FOUL/TURN_CHANGE: no input, let timers handle.
- GAME_OVER: restart after 3 second pause.
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
    POCKETS, BALL_COLLISION_DIST, BALL_VALUES, POCKET_RADIUS,
    TABLE_LEFT, TABLE_RIGHT, TABLE_TOP, TABLE_BOTTOM,
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
        self.game.demo_mode = True  # cue ball can't scratch
        self.game_over_timer = 0.0

        # AI state
        self.target_angle = 0.0
        self.target_power = 0.5
        self._was_aiming = False
        self._pick_target()

    def _pick_target(self):
        """Choose best shot using ghost ball pocket targeting."""
        cue = self.game._cue_ball()
        objects = self.game._object_balls()
        if not cue or not objects:
            self.target_angle = random.uniform(0, 2 * math.pi)
            self.target_power = 0.5
            return

        best_score = -999
        best_angle = None
        best_dist = 30.0

        for ball in objects:
            for px, py, mult in POCKETS:
                # Ghost ball position: BALL_COLLISION_DIST behind ball, away from pocket
                dx_bp = ball.x - px
                dy_bp = ball.y - py
                dist_bp = math.sqrt(dx_bp * dx_bp + dy_bp * dy_bp)
                if dist_bp < 1.0:
                    continue

                # Normalize direction from pocket to ball
                nx = dx_bp / dist_bp
                ny = dy_bp / dist_bp

                # Ghost ball center = ball center + collision_dist along that direction
                ghost_x = ball.x + nx * BALL_COLLISION_DIST
                ghost_y = ball.y + ny * BALL_COLLISION_DIST

                # Check ghost ball is on table
                if (ghost_x < TABLE_LEFT + 2 or ghost_x > TABLE_RIGHT - 2 or
                        ghost_y < TABLE_TOP + 2 or ghost_y > TABLE_BOTTOM - 2):
                    continue

                # Distance from cue to ghost
                dx_cg = ghost_x - cue.x
                dy_cg = ghost_y - cue.y
                dist_cg = math.sqrt(dx_cg * dx_cg + dy_cg * dy_cg)
                if dist_cg < 2.0:
                    continue

                # Angle from cue to ghost
                aim_angle = math.atan2(dy_cg, dx_cg)

                # Cut angle: angle between cue->ball line and ball->pocket line
                # Lower is easier
                dx_cb = ball.x - cue.x
                dy_cb = ball.y - cue.y
                dist_cb = math.sqrt(dx_cb * dx_cb + dy_cb * dy_cb)
                if dist_cb < 1.0:
                    continue
                # Direction cue->ball
                dir_cb_x = dx_cb / dist_cb
                dir_cb_y = dy_cb / dist_cb
                # Direction ball->pocket
                dir_bp_x = -nx
                dir_bp_y = -ny
                # Dot product for cut angle
                dot = dir_cb_x * dir_bp_x + dir_cb_y * dir_bp_y
                dot = max(-1.0, min(1.0, dot))
                cut_angle = math.acos(dot)

                # Skip very sharp cuts (>70 degrees)
                if cut_angle > 1.22:
                    continue

                # Direction from cue to ghost (for line-of-sight checks)
                dir_x = dx_cg / dist_cg
                dir_y = dy_cg / dist_cg

                # Check line-of-sight from cue to ghost (no blocking balls)
                blocked = False
                for other in objects:
                    if other is ball:
                        continue
                    # Point-to-line distance from other ball to the cue->ghost line
                    ox = other.x - cue.x
                    oy = other.y - cue.y
                    proj = ox * dir_x + oy * dir_y
                    if proj < 1.0 or proj > dist_cg - 1.0:
                        continue
                    perp = abs(ox * dir_y - oy * dir_x)
                    if perp < BALL_COLLISION_DIST + 0.5:
                        blocked = True
                        break

                # Check if cue path crosses any pocket before reaching the ball
                pocket_in_path = False
                for ppx, ppy, _ in POCKETS:
                    ox = ppx - cue.x
                    oy = ppy - cue.y
                    proj = ox * dir_x + oy * dir_y
                    if proj < 1.0 or proj > dist_cg:
                        continue
                    perp = abs(ox * dir_y - oy * dir_x)
                    if perp < POCKET_RADIUS + 1.0:
                        pocket_in_path = True
                        break

                # Estimate post-collision cue ball scratch risk.
                # After elastic collision, cue deflects perpendicular to
                # the contact normal. For straight shots the cue nearly
                # stops but retains some forward speed. Trace the cue's
                # likely post-collision direction and see if it hits a pocket.
                scratch_risk = 0.0

                # Cue approach direction
                cue_dir_x = dir_x
                cue_dir_y = dir_y
                # Contact normal: ghost->ball direction (= toward pocket)
                cn_x = -nx
                cn_y = -ny
                # After collision: subtract normal component
                vn = cue_dir_x * cn_x + cue_dir_y * cn_y
                post_dx = cue_dir_x - vn * cn_x
                post_dy = cue_dir_y - vn * cn_y
                post_speed = math.sqrt(post_dx * post_dx + post_dy * post_dy)

                if post_speed < 0.05:
                    # Near-straight shot: cue nearly stops but may creep
                    # forward. Check if ball->pocket line has a pocket nearby.
                    for ppx, ppy, _ in POCKETS:
                        d = math.sqrt((ball.x - ppx) ** 2 +
                                      (ball.y - ppy) ** 2)
                        if d < 8.0:
                            scratch_risk = 120.0
                else:
                    # Cue deflects in post_d direction. Check if it
                    # heads toward a pocket.
                    pd_x = post_dx / post_speed
                    pd_y = post_dy / post_speed
                    for ppx, ppy, _ in POCKETS:
                        ox = ppx - ball.x
                        oy = ppy - ball.y
                        proj = ox * pd_x + oy * pd_y
                        if proj < 0:
                            continue
                        perp = abs(ox * pd_y - oy * pd_x)
                        if perp < POCKET_RADIUS + 2.0:
                            scratch_risk = max(scratch_risk, 80.0)

                # Score this shot
                score = 0.0
                if not blocked:
                    score += 100.0
                else:
                    score -= 50.0

                if pocket_in_path:
                    score -= 200.0

                score -= scratch_risk

                # Distance penalty (prefer closer shots)
                score -= dist_cg * 0.5

                # Cut angle penalty
                score -= cut_angle * 30.0

                # Pocket multiplier bonus
                score += mult * 15.0

                # Ball value bonus
                score += BALL_VALUES.get(ball.num, 10) * 0.5

                if score > best_score:
                    best_score = score
                    best_angle = aim_angle
                    best_dist = dist_cg

        if best_angle is None:
            # No valid shot found — aim at a safe angle away from all pockets
            best_angle = self._safe_angle(cue)

        # Add small random perturbation to break deterministic loops
        self.target_angle = (best_angle + random.gauss(0, 0.03)) % (2 * math.pi)
        # Power: enough to reach the pocket with margin for friction
        self.target_power = min(0.9, max(0.35, best_dist / 35.0))

    def _safe_angle(self, cue):
        """Find an angle that doesn't shoot toward any pocket."""
        pocket_angles = []
        for px, py, _ in POCKETS:
            pocket_angles.append(math.atan2(py - cue.y, px - cue.x))
        # Pick angle maximally distant from all pockets
        best_angle = 0.0
        best_min_dist = -1
        for test in range(36):
            a = test * math.pi / 18
            min_dist = min(abs((a - pa + math.pi) % (2 * math.pi) - math.pi)
                          for pa in pocket_angles)
            if min_dist > best_min_dist:
                best_min_dist = min_dist
                best_angle = a
        return best_angle

    def _steer_toward(self, target_angle, current_angle):
        """Return (left, right) bools to steer current toward target angle."""
        diff = (target_angle - current_angle + math.pi) % (2 * math.pi) - math.pi
        if diff > 0.05:
            return False, True
        elif diff < -0.05:
            return True, False
        return False, False

    def handle_input(self, input_state):
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
            # Wait for power to reach target, then fire
            # IMPORTANT: no direction input or it cancels back to aiming
            if abs(self.game.power - self.target_power) < 0.06:
                ai_input.action_l = True

        # Pick a new target each time we enter aiming phase
        if phase == PHASE_AIMING and not self._was_aiming:
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
