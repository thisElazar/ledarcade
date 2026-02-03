"""
JezzBall Demo - AI Attract Mode
===============================
JezzBall plays itself using strategic AI for idle screen demos.
The AI builds walls to divide the playing field and trap atoms.

AI Strategy:
- Track ball positions and predict trajectories
- Find safe locations to build walls (away from balls)
- Build walls to divide the playing field
- Choose horizontal or vertical walls based on ball positions
- Aim to trap balls in smaller sections
- Wait for balls to clear an area before building
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

# Import the actual game
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.jezzball import JezzBall


class JezzBallDemo(Visual):
    name = "JEZZBALL DEMO"
    description = "AI divides space"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = JezzBall(self.display)
        self.game.reset()
        self.decision_timer = 0.0
        self.decision_interval = 0.1  # Recalculate every 100ms
        self.current_action = None
        self.game_over_timer = 0.0
        self.wall_cooldown = 0.0  # Time to wait after wall attempt
        self.target_x = None
        self.target_y = None
        self.target_horizontal = True

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
            return

        # Update cooldowns
        if self.wall_cooldown > 0:
            self.wall_cooldown -= dt

        # Make AI decisions periodically
        self.decision_timer += dt
        if self.decision_timer >= self.decision_interval:
            self.decision_timer = 0.0
            self.current_action = self._decide_action()

        # Create input state with AI's chosen action
        ai_input = InputState()
        if self.current_action == 'up':
            ai_input.up = True
        elif self.current_action == 'down':
            ai_input.down = True
        elif self.current_action == 'left':
            ai_input.left = True
        elif self.current_action == 'right':
            ai_input.right = True
        elif self.current_action == 'build':
            ai_input.action_l = True

        self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()

        # Overlay "DEMO" text (blinking)
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)

    def _decide_action(self):
        """AI decision-making for cursor movement and wall building."""
        game = self.game

        # Don't act if walls are currently building
        if game.walls:
            return None

        # Don't try to build too frequently
        if self.wall_cooldown > 0:
            return self._move_to_target()

        # Find a safe location to build a wall
        safe_pos = self._find_safe_build_location()

        if safe_pos:
            self.target_x, self.target_y, self.target_horizontal = safe_pos
            self.wall_cooldown = 1.0  # Wait after attempting wall

            # Check if we're at the target position
            if game.cursor_x == self.target_x and game.cursor_y == self.target_y:
                # Set correct orientation
                if game.horizontal != self.target_horizontal:
                    # Need to change direction
                    if self.target_horizontal:
                        return 'left'  # Switch to horizontal
                    else:
                        return 'up'  # Switch to vertical
                # Build the wall!
                return 'build'

        return self._move_to_target()

    def _move_to_target(self):
        """Move cursor toward target position."""
        game = self.game

        if self.target_x is None or self.target_y is None:
            # No target, pick center of playfield
            self.target_x = game.width // 2
            self.target_y = game.height // 2
            self.target_horizontal = True

        # Move toward target
        dx = self.target_x - game.cursor_x
        dy = self.target_y - game.cursor_y

        # Prefer moving in direction that sets the right orientation
        if abs(dx) > abs(dy):
            if dx > 0:
                return 'right'
            elif dx < 0:
                return 'left'
        else:
            if dy > 0:
                return 'down'
            elif dy < 0:
                return 'up'

        return None

    def _find_safe_build_location(self):
        """
        Find a safe location to build a wall.
        Returns (x, y, horizontal) or None if no safe location found.
        """
        game = self.game

        # Get atom positions and velocities for prediction
        atom_info = []
        for atom in game.atoms:
            ax, ay = int(atom['x']), int(atom['y'])
            atom_info.append({
                'x': ax,
                'y': ay,
                'dx': atom['dx'],
                'dy': atom['dy'],
            })

        # Safety margin around atoms (larger for faster prediction)
        safety_margin = 8

        # Try to find a good dividing line
        best_pos = None
        best_score = -1

        # Try horizontal walls at various y positions
        for test_y in range(10, game.height - 10, 4):
            # Check if this line is safe from all atoms
            safe = True
            for atom in atom_info:
                # Current position check
                if abs(atom['y'] - test_y) < safety_margin:
                    # Predict where atom will be in next ~0.5 seconds
                    pred_y = atom['y'] + atom['dy'] * 0.5
                    if abs(pred_y - test_y) < safety_margin:
                        safe = False
                        break

            if safe:
                # Find a good x position for the cursor
                for test_x in range(game.width // 4, 3 * game.width // 4, 4):
                    if not game.grid[test_y][test_x]:
                        # Check if atoms are clear of this position
                        pos_safe = True
                        for atom in atom_info:
                            dist = abs(atom['x'] - test_x) + abs(atom['y'] - test_y)
                            if dist < safety_margin:
                                pos_safe = False
                                break

                        if pos_safe:
                            # Score based on how much area we could divide
                            score = self._estimate_division_score(test_x, test_y, True)
                            if score > best_score:
                                best_score = score
                                best_pos = (test_x, test_y, True)

        # Try vertical walls at various x positions
        for test_x in range(10, game.width - 10, 4):
            # Check if this line is safe from all atoms
            safe = True
            for atom in atom_info:
                # Current position check
                if abs(atom['x'] - test_x) < safety_margin:
                    # Predict where atom will be
                    pred_x = atom['x'] + atom['dx'] * 0.5
                    if abs(pred_x - test_x) < safety_margin:
                        safe = False
                        break

            if safe:
                # Find a good y position for the cursor
                for test_y in range(game.height // 4, 3 * game.height // 4, 4):
                    if not game.grid[test_y][test_x]:
                        # Check if atoms are clear of this position
                        pos_safe = True
                        for atom in atom_info:
                            dist = abs(atom['x'] - test_x) + abs(atom['y'] - test_y)
                            if dist < safety_margin:
                                pos_safe = False
                                break

                        if pos_safe:
                            # Score based on how much area we could divide
                            score = self._estimate_division_score(test_x, test_y, False)
                            if score > best_score:
                                best_score = score
                                best_pos = (test_x, test_y, False)

        return best_pos

    def _estimate_division_score(self, x, y, horizontal):
        """
        Estimate how effective a wall at this position would be.
        Higher score = better division of space.
        """
        game = self.game

        if horizontal:
            # Count empty space that would be divided
            left_empty = 0
            right_empty = 0
            # Check left side
            for check_x in range(x - 1, 0, -1):
                if game.grid[y][check_x]:
                    break
                left_empty += 1
            # Check right side
            for check_x in range(x + 1, game.width):
                if game.grid[y][check_x]:
                    break
                right_empty += 1
            return min(left_empty, right_empty)  # Balance is good
        else:
            # Vertical wall
            up_empty = 0
            down_empty = 0
            # Check up
            for check_y in range(y - 1, 0, -1):
                if game.grid[check_y][x]:
                    break
                up_empty += 1
            # Check down
            for check_y in range(y + 1, game.height):
                if game.grid[check_y][x]:
                    break
                down_empty += 1
            return min(up_empty, down_empty)  # Balance is good
