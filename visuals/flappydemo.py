"""
Flappy Bird Demo - AI Attract Mode
==================================
Flappy plays itself by timing flaps to navigate through pipe gaps.

AI Strategy:
- Rule of thumb: flap when below the next gap's center and falling
- Before trusting it, fly the bird's own physics ahead through the next
  pipes; if the rule's choice crashes and the other does not, take the other.
  (A gap lower than the last one has to be set up before the last pipe ends.)
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.flappy import Flappy


HORIZON = 45   # frames flown ahead: the pipe at hand and the one after
FLAP_EVERY = 3 # the plan only considers a flap every this many frames
MARGIN = 1.0   # px of room the plan wants from a pipe or the ground (1.5 leaves no way through)
BUDGET = 1500  # frames simulated per decision, at most


class FlappyDemo(Visual):
    name = "FLAPPY"
    description = "AI plays Flappy Bird"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = Flappy(self.display)
        self.game.reset()
        self.should_flap = False
        self.decision_timer = 0.0
        self.decision_interval = 0.05  # Check frequently
        self.frame_dt = 1 / 30  # smoothed; the plan flies in frames this long

    def handle_input(self, input_state):
        return False

    def update(self, dt):
        self.time += dt

        # If game over, restart after a pause
        if self.game.state == GameState.GAME_OVER:
            self.decision_timer += dt
            if self.decision_timer > 3.0:
                self.game.reset()
                self.decision_timer = 0.0
            return

        self.frame_dt += (dt - self.frame_dt) * 0.1

        # Make AI decisions
        self.decision_timer += dt
        if self.decision_timer >= self.decision_interval:
            self.decision_timer = 0.0
            self.should_flap = self._should_flap()

        # Create input state
        ai_input = InputState()
        if self.should_flap:
            ai_input.action_l = True
            self.should_flap = False  # Single flap per decision

        self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()

        # Overlay "DEMO" text
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)

    def _should_flap(self):
        """The rule of thumb's choice, unless flying ahead says otherwise."""
        game = self.game
        if not game.started:
            return True  # Auto-start the game

        self.budget = BUDGET
        first = self._rule(0, game.bird_y, game.bird_vy)
        results = {}
        for flap in (first, not first):
            results[flap] = self._fly(0, game.bird_y, game.bird_vy, flap)
            if results[flap] >= HORIZON:
                return flap
        return max(results, key=results.get)

    def _rule(self, k, y, vy):
        """Flap when below the next gap's center (a bit low is safer) and falling."""
        game = self.game
        shift = game.pipe_speed * self.frame_dt * k
        ahead = [p for p in game.pipes if p['x'] - shift + game.pipe_width > game.bird_x]
        if not ahead:
            return y > 30 and vy > 0
        gap_y = min(ahead, key=lambda p: p['x'])['gap_y']
        return y > gap_y + game.gap_height / 2 + 2 and vy >= 0

    def _fly(self, k, y, vy, flap):
        """Frames survived (up to HORIZON) taking this choice at frame k and
        the best choices after it, trying the rule of thumb's first."""
        self.budget -= 1
        state = self._step(k, y, vy, flap)
        if state is None:
            return k
        k += 1
        if k >= HORIZON:
            return HORIZON
        y, vy = state
        if k % FLAP_EVERY:
            return self._fly(k, y, vy, False)
        first = self._rule(k, y, vy)
        best = self._fly(k, y, vy, first)
        if best < HORIZON and self.budget > 0:
            best = max(best, self._fly(k, y, vy, not first))
        return best

    def _step(self, k, y, vy, flap):
        """One frame of Flappy.update for the bird alone. Pipe x is as of
        frame 0. Returns (y, vy), or None for a crash."""
        game = self.game
        dt = self.frame_dt
        if flap:
            vy = game.flap_strength
        vy = min(vy + game.gravity * dt, game.max_fall_speed)
        y += vy * dt
        if y >= game.ground_y - 2 - MARGIN:
            return None
        if y < 8:
            y, vy = 8, 0.0

        shift = game.pipe_speed * dt * (k + 1)
        top, bottom = int(y) - 1, int(y) + 2
        for pipe in game.pipes:
            px = int(pipe['x'] - shift)
            if game.bird_x - 1 < px + game.pipe_width + MARGIN and game.bird_x + 2 > px - MARGIN:
                if top < pipe['gap_y'] + MARGIN or bottom > pipe['gap_y'] + game.gap_height - MARGIN:
                    return None
        return y, vy
