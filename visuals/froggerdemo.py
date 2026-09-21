"""
Frogger Demo - AI Attract Mode
==============================
Frogger plays itself using AI for idle screen demos.
The AI navigates through traffic and across water platforms.

AI Strategy:
- Everything in the game moves in a straight line, so where it will be is known
- Decide only at the moment a hop can happen; take a hop only if the frog
  survives the whole time it must sit there AND has a safe hop after that
- Prefer up, then toward an open home, then waiting, then anything that lives
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

# Import the actual game
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.frogger import Frogger


DEPTH = 5     # hops of lookahead
MARGIN = 1.5  # px of room the lookahead wants around a car or a platform edge
SAMPLE = 1 / 30


class FroggerDemo(Visual):
    name = "FROGGY"
    description = "AI plays Frogger"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = Frogger(self.display)
        self.game.reset()
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

        # Decide only on a frame where the game will act on it
        ai_input = InputState()
        game = self.game
        if not game.dying and game.move_cooldown - dt <= 0:
            direction = self._decide_direction(dt)
            if direction:
                setattr(ai_input, direction, True)

        self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()

        # Overlay "DEMO" text
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)

    def _decide_direction(self, dt):
        """First choice, in order of preference, that the frog survives."""
        game = self.game
        self.step = game.move_delay + dt  # time in a cell before the next hop
        col, row = game.frog_col, game.frog_row

        # Sideways goal: an open home once on the river; before that the
        # middle, because from an edge the first river row carries the frog off
        toward = None
        goal = self._open_home(col) if row >= 7 else game.cols // 2
        if goal is not None and abs(goal - col) > 0.5:
            toward = 'right' if goal > col else 'left'
        order = ['up', toward, None, 'left', 'right', 'down']
        if row == 11 and toward:
            order = [toward, 'up', None, 'left', 'right', 'down']
        moves = [m for i, m in enumerate(order) if m is not None or i == 2]

        for depth in range(DEPTH, -1, -1):
            memo = {}
            for move in moves:
                if self._survives(*self._hop(col, row, move), 0.0, depth, memo):
                    return move
        return None

    def _hop(self, col, row, move):
        game = self.game
        if move == 'up':
            return col, min(game.rows - 2, row + 1)
        if move == 'down':
            return col, max(0, row - 1)
        if move == 'left':
            return max(0, col - 1), row
        if move == 'right':
            return min(game.cols - 1, col + 1), row
        return col, row

    def _survives(self, col, row, t, depth, memo):
        """Arriving at (col, row) t seconds from now: does the frog live
        through its stay there, and is there a way on for depth more hops?"""
        key = (round(col * 4), row, round(t / self.step), depth)
        if key not in memo:
            memo[key] = self._survives_uncached(col, row, t, depth, memo)
        return memo[key]

    def _survives_uncached(self, col, row, t, depth, memo):
        if row == 12:
            return self._home_open(col)
        col = self._stay(col, row, t)
        if col is None:
            return False
        if depth == 0:
            return True
        return any(self._survives(*self._hop(col, row, move), t + self.step, depth - 1, memo)
                   for move in ('up', None, 'left', 'right', 'down'))

    def _stay(self, col, row, t):
        """Sit at (col, row) from t for one step. Returns the column the frog
        ends on (platforms carry it), or None if it dies."""
        game = self.game
        cell = game.cell_size
        x = col * cell

        if 1 <= row <= 5:
            for car in game.cars:
                if car['row'] != row:
                    continue
                length = car['length'] * cell
                ts = t
                while ts <= t + self.step:
                    cx = self._x_at(car, length, ts)
                    if x < cx + length + MARGIN and x + cell > cx - MARGIN:
                        return None
                    ts += SAMPLE
            return col

        if row == 6 and game.snake:
            ts = t
            while ts <= t + self.step:
                sx = self._snake_x(ts)
                if x < sx + 3 + MARGIN and x + cell > sx - MARGIN:
                    return None
                ts += SAMPLE
            return col

        if 7 <= row <= 11:
            for plat in game.logs + game.turtles:
                if plat['row'] != row:
                    continue
                length = plat['length'] * cell
                px = self._x_at(plat, length, t)
                # the game allows 2px of overhang; the plan wants to be well on
                if not (x >= px - 2 + MARGIN and x + cell <= px + length + 2 - MARGIN):
                    continue
                # The last row's logs run left: one is a dead end unless an
                # open home still lies at or left of its right end
                if row == 11 and not any(h * cell <= px + length - cell + 2
                                         for i, h in enumerate(game.home_positions) if not game.homes[i]):
                    return None
                if 'dive_phase' in plat:
                    # under from 7.0 to 9.0 of a 9 s cycle
                    start = (game.dive_clock + plat['dive_phase'] + t) % 9.0
                    if start + self.step + 0.2 >= 7.0:
                        return None
                end = col + plat['speed'] * self.step / cell
                if end < 0.25 or end > game.cols - 1.25:
                    return None  # carried off the screen
                return end
            return None

        return col

    def _x_at(self, obj, length, t):
        """Left edge of a car, log or turtle t seconds from now, with the
        game's wrap: off one side, back on at the other."""
        return (obj['x'] + length + obj['speed'] * t) % (GRID_SIZE + length) - length

    def _snake_x(self, t):
        """The median snake bounces between 0 and GRID_SIZE - 3."""
        snake = self.game.snake
        span = GRID_SIZE - 3
        x = (snake['x'] + snake['dir'] * snake['speed'] * t) % (2 * span)
        return 2 * span - x if x > span else x

    def _home_open(self, col):
        game = self.game
        for i, home_col in enumerate(game.home_positions):
            if abs(col - home_col) <= 0.9 and not game.homes[i]:
                bonus = game.home_bonus
                return not (bonus and bonus['slot'] == i and bonus['type'] == 'croc')
        return False

    def _open_home(self, col):
        """Column of the nearest unfilled home, or None."""
        game = self.game
        homes = [c for i, c in enumerate(game.home_positions) if not game.homes[i]]
        return min(homes, key=lambda c: abs(c - col), default=None)
