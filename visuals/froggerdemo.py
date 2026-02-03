"""
Frogger Demo - AI Attract Mode
==============================
Frogger plays itself using AI for idle screen demos.
The AI navigates through traffic and across water platforms.

AI Strategy:
- Check safety of forward moves (avoid cars, land on platforms)
- Look ahead to predict object positions
- Prefer moving up when safe, dodge sideways when needed
- Target unfilled home slots
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

# Import the actual game
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.frogger import Frogger


class FroggerDemo(Visual):
    name = "FROGGER"
    description = "AI plays Frogger"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = Frogger(self.display)
        self.game.reset()
        self.ai_direction = None
        self.decision_timer = 0.0
        self.decision_interval = 0.15  # Recalculate every 150ms
        self.wait_timer = 0.0  # Time spent waiting at current position

    def handle_input(self, input_state):
        # Demo doesn't respond to input (auto-plays)
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

        # Make AI decisions periodically
        self.decision_timer += dt
        if self.decision_timer >= self.decision_interval:
            self.decision_timer = 0.0
            self.ai_direction = self._decide_direction()

        # Create input state with AI's chosen direction
        ai_input = InputState()
        if self.ai_direction == 'up':
            ai_input.up = True
        elif self.ai_direction == 'down':
            ai_input.down = True
        elif self.ai_direction == 'left':
            ai_input.left = True
        elif self.ai_direction == 'right':
            ai_input.right = True

        self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()

        # Overlay "DEMO" text
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)

    def _is_safe_at(self, col, row, look_ahead_time=0.3):
        """Check if position will be safe after look_ahead_time."""
        game = self.game
        cell_size = game.cell_size
        frog_x = col * cell_size

        # Bounds check
        if col < 0 or col >= game.cols:
            return False

        # Start zone and safe zone are always safe
        if row == 0 or row == 6:
            return True

        # Road rows: check for cars
        if 1 <= row <= 5:
            for car in game.cars:
                if car['row'] == row:
                    future_x = car['x'] + car['speed'] * look_ahead_time
                    car_left = future_x
                    car_right = future_x + car['length'] * cell_size
                    frog_right = frog_x + cell_size
                    if frog_x < car_right and frog_right > car_left:
                        return False
            return True

        # Water rows: check for logs/turtles to land on
        if 7 <= row <= 11:
            # Check logs
            for log in game.logs:
                if log['row'] == row:
                    future_x = log['x'] + log['speed'] * look_ahead_time
                    log_left = future_x - 2
                    log_right = future_x + log['length'] * cell_size + 2
                    if log_left <= frog_x <= log_right - cell_size:
                        return True

            # Check turtles (only if not diving)
            for turtle in game.turtles:
                if turtle['row'] == row and not turtle['diving']:
                    # Also check if turtle might dive soon
                    if turtle['dive_timer'] < 0.5:
                        continue  # About to dive, not safe
                    future_x = turtle['x'] + turtle['speed'] * look_ahead_time
                    turtle_left = future_x - 2
                    turtle_right = future_x + turtle['length'] * cell_size + 2
                    if turtle_left <= frog_x <= turtle_right - cell_size:
                        return True

            return False  # No platform = death

        # Home row - check if there's an unfilled slot
        if row == 12:
            for i, home_col in enumerate(game.home_positions):
                if abs(col - home_col) <= 1 and not game.homes[i]:
                    return True
            return False  # No valid home slot

        return True  # Default safe

    def _get_best_home_col(self):
        """Find the column of the nearest unfilled home."""
        game = self.game
        frog_col = int(game.frog_col)

        # Find nearest unfilled home
        best_col = None
        best_dist = float('inf')

        for i, home_col in enumerate(game.home_positions):
            if not game.homes[i]:
                dist = abs(home_col - frog_col)
                if dist < best_dist:
                    best_dist = dist
                    best_col = home_col

        return best_col if best_col is not None else 7

    def _decide_direction(self):
        """AI decision-making for Frogger movement."""
        game = self.game
        frog_col = int(game.frog_col)
        frog_row = game.frog_row

        # If on water, account for platform drift
        if 7 <= frog_row <= 11 and game.frog_riding:
            # Recalculate actual column based on float position
            frog_col = int(game.frog_col)

        # Get target column (for homes)
        target_col = self._get_best_home_col()

        # Check possible moves with look-ahead
        up_safe = self._is_safe_at(frog_col, frog_row + 1, 0.2)
        left_safe = self._is_safe_at(frog_col - 1, frog_row, 0.2)
        right_safe = self._is_safe_at(frog_col + 1, frog_row, 0.2)
        stay_safe = self._is_safe_at(frog_col, frog_row, 0.3)

        # On water rows, check if we're drifting off screen
        if 7 <= frog_row <= 11:
            if game.frog_col < 1:
                # Drifting left off screen, try to move right
                if right_safe:
                    return 'right'
                elif up_safe:
                    return 'up'
            elif game.frog_col > game.cols - 2:
                # Drifting right off screen, try to move left
                if left_safe:
                    return 'left'
                elif up_safe:
                    return 'up'

        # Priority 1: Move up if safe
        if up_safe:
            # On approach to home (row 11), align with target home
            if frog_row == 11:
                if frog_col < target_col - 1:
                    if right_safe:
                        return 'right'
                elif frog_col > target_col + 1:
                    if left_safe:
                        return 'left'
            return 'up'

        # Priority 2: Move toward target column if it helps
        if frog_col < target_col and right_safe:
            # Check if moving right and then up would be safe
            if self._is_safe_at(frog_col + 1, frog_row + 1, 0.4):
                return 'right'
        if frog_col > target_col and left_safe:
            if self._is_safe_at(frog_col - 1, frog_row + 1, 0.4):
                return 'left'

        # Priority 3: Dodge sideways
        if right_safe:
            return 'right'
        if left_safe:
            return 'left'

        # Priority 4: Check if up will be safe soon (with longer look-ahead)
        for t in [0.3, 0.4, 0.5, 0.6]:
            if self._is_safe_at(frog_col, frog_row + 1, t):
                # Wait - it will be safe soon
                return None

        # Priority 5: Retreat if nothing else works
        if self._is_safe_at(frog_col, frog_row - 1, 0.2) and frog_row > 0:
            return 'down'

        # Wait for better opportunity
        return None
