"""
Stick Runner Demo - AI Attract Mode
====================================
Stick Runner plays itself by timing jumps to cross rooftop gaps.

AI Strategy:
- The rooftops ahead are already built, so the only choice is when to jump
- Each frame a jump is possible, run the runner's own physics forward both
  ways (jump now / wait) and jump once that is safe and waiting no longer is
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.stickrunner import StickRunner


HORIZON = 70  # frames of lookahead: a jump (about 23), the landing, and the next jump
SLACK = 2     # frames left in hand: jump this long before the last safe moment
LOST = 64     # player_y past every roof's reach: the fall cannot be saved


class StickRunnerDemo(Visual):
    name = "STICK RUNNER"
    description = "AI runs and jumps"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = StickRunner(self.display)
        self.game.reset()
        self.should_jump = False
        self.decision_timer = 0.0
        self.decision_interval = 0.02  # Check frequently for responsive jumping
        self.game_over_timer = 0.0
        self.frame_dt = 1 / 30  # smoothed; the lookahead plans in frames this long

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
            return

        self.frame_dt += (dt - self.frame_dt) * 0.1

        # Make AI decisions
        self.decision_timer += dt
        if self.decision_timer >= self.decision_interval:
            self.decision_timer = 0.0
            self.should_jump = self._should_jump()

        # Create input state
        ai_input = InputState()
        if self.should_jump:
            ai_input.action_l = True
            self.should_jump = False  # Single jump per decision

        self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()

        # Overlay "DEMO" text (blinking)
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)

    def _should_jump(self):
        """Jump when that is safe and waiting SLACK more frames is not."""
        game = self.game
        if not (game.on_ground or game._near_ground()):
            return False

        start = (game.player_y, game.velocity_y, game.on_ground)
        self.known = max(b['x'] + b['width'] for b in game.buildings)
        # Careful first; if that finds no way through, plan tighter
        for hold in (SLACK, 0):
            plan = (hold, {})
            wait = self._survive(plan, 0, start, False)
            if wait >= HORIZON:
                return False
            jump = self._survive(plan, 0, start, True)
            if jump >= HORIZON:
                return True
        return jump > wait

    def _survive(self, plan, k, state, jump):
        """Frames survived (up to HORIZON) from frame k, given this frame's
        choice and the best choices after it. No jumps on frames 1..hold."""
        hold, memo = plan
        state = self._step(k, *state, jump)
        if state is None:
            return k
        if k + 1 >= HORIZON or state == 'unknown':
            return HORIZON
        key = (k,) + state
        if key not in memo:
            best = self._survive(plan, k + 1, state, False)
            if best < HORIZON and k + 1 > hold:
                best = max(best, self._survive(plan, k + 1, state, True))
            memo[key] = best
        return memo[key]

    def _step(self, k, y, vy, on_ground, jump):
        """One frame of StickRunner.update for the runner alone, in the same
        order. Building x is as of frame 0. Returns (y, vy, on_ground), None
        for a fall that cannot be saved, or 'unknown' past the last building
        generated so far."""
        game = self.game
        dt = self.frame_dt
        x = game.PLAYER_X + game.scroll_speed * dt * k  # where the runner is over frame-0 ground

        if jump:
            roof = self._roof(x)
            if on_ground or (roof is not None and abs(y + 4 - roof) <= 6):
                vy = game.JUMP_VELOCITY
        vy = min(vy + game.GRAVITY * dt, game.MAX_FALL_SPEED)
        y += vy * dt

        x += game.scroll_speed * dt
        if x > self.known:
            return 'unknown'
        on_ground = False
        roof = self._roof(x)
        if roof is not None and vy >= 0 and roof <= y + 4 <= roof + 10:
            y, vy, on_ground = roof - 4, 0.0, True
        if y > LOST:
            return None
        return (y, vy, on_ground)

    def _roof(self, x):
        """Landing height of the building under frame-0 position x, or None."""
        game = self.game
        for b in game.buildings:
            if b['x'] <= x <= b['x'] + b['width']:
                return game._get_landing_y(b, x)
        return None
