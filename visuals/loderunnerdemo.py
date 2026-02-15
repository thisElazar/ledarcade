"""
Lode Runner Demo - AI Attract Mode
==================================
Lode Runner plays itself using simple AI for idle screen demos.
The AI collects all gold and escapes via the exit ladder.

AI Strategy:
- Find nearest gold piece to collect
- Pathfind using platforms, ladders, and ropes
- Avoid enemies (monks) - find safe routes
- Dig holes to trap enemies blocking the path
- Once all gold collected, head for the exit ladder at top
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

# Import the actual game
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.loderunner import LodeRunner


class LodeRunnerDemo(Visual):
    name = "GOLD RUNNER"
    description = "AI collects gold"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = LodeRunner(self.display)
        self.game.reset()
        self.decision_timer = 0.0
        self.decision_interval = 0.06  # Recalculate every 60ms
        self.ai_action = {
            'left': False, 'right': False,
            'up': False, 'down': False,
            'dig': False
        }
        self.game_over_timer = 0.0
        self.target_gold = None
        self.last_player_pos = None
        self.stuck_timer = 0.0

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
                self.target_gold = None
                self.stuck_timer = 0.0
            return

        # Make AI decisions periodically
        self.decision_timer += dt
        if self.decision_timer >= self.decision_interval:
            self.decision_timer = 0.0
            self.ai_action = self._decide_action()

        # Create input state with AI's chosen actions
        ai_input = InputState()
        ai_input.left = self.ai_action['left']
        ai_input.right = self.ai_action['right']
        ai_input.up = self.ai_action['up']
        ai_input.down = self.ai_action['down']
        if self.ai_action['dig']:
            ai_input.action_l = True

        self.game.update(ai_input, dt)

        # Check if stuck
        current_pos = (self.game.player_x, self.game.player_y)
        if current_pos == self.last_player_pos:
            self.stuck_timer += dt
            if self.stuck_timer > 1.0:
                # Try digging to get unstuck
                self.target_gold = None
                self.stuck_timer = 0.0
        else:
            self.stuck_timer = 0.0
        self.last_player_pos = current_pos

    def draw(self):
        self.game.draw()

        # Overlay "DEMO" text (blinking)
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)

    def _decide_action(self):
        """AI decision-making for Lode Runner movement."""
        game = self.game
        px, py = game.player_x, game.player_y

        action = {
            'left': False, 'right': False,
            'up': False, 'down': False,
            'dig': False
        }

        # Priority 1: Check for immediate danger from enemies
        danger_dir = self._check_enemy_danger()
        if danger_dir:
            # Try to evade or dig
            if danger_dir == 'left':
                # Enemy on left, try to dig left or move right
                if self._can_dig_left():
                    action['dig'] = True
                    game.player_facing = -1
                elif not game.is_solid(px + 1, py):
                    action['right'] = True
            elif danger_dir == 'right':
                # Enemy on right, try to dig right or move left
                if self._can_dig_right():
                    action['dig'] = True
                    game.player_facing = 1
                elif not game.is_solid(px - 1, py):
                    action['left'] = True
            elif danger_dir == 'below':
                # Enemy below, try to climb up or move away
                if self._can_climb_up():
                    action['up'] = True
                elif not game.is_solid(px - 1, py):
                    action['left'] = True
                elif not game.is_solid(px + 1, py):
                    action['right'] = True
            return action

        # Priority 2: If exit is open, head for exit
        if game.exit_open:
            return self._move_to_exit()

        # Priority 3: Find and collect gold
        target = self._find_best_gold()
        if target:
            return self._move_toward_gold(target)

        # Default: wander if no target
        return action

    def _check_enemy_danger(self):
        """Check if any enemy is dangerously close. Returns direction of threat."""
        game = self.game
        px, py = game.player_x, game.player_y

        for enemy in game.enemies:
            if enemy['trapped']:
                continue

            ex, ey = enemy['x'], enemy['y']
            dx = ex - px
            dy = ey - py

            # Very close enemy - immediate danger
            if abs(dx) <= 2 and abs(dy) <= 1:
                if dx < 0:
                    return 'left'
                elif dx > 0:
                    return 'right'
                elif dy > 0:
                    return 'below'

        return None

    def _can_dig_left(self):
        """Check if we can dig a hole to the left."""
        game = self.game
        dig_x = game.player_x - 1
        dig_y = game.player_y + 1
        return (0 <= dig_x < game.LEVEL_WIDTH and
                0 <= dig_y < game.LEVEL_HEIGHT and
                game.tiles[dig_y][dig_x] == game.BRICK and
                game.dig_cooldown <= 0)

    def _can_dig_right(self):
        """Check if we can dig a hole to the right."""
        game = self.game
        dig_x = game.player_x + 1
        dig_y = game.player_y + 1
        return (0 <= dig_x < game.LEVEL_WIDTH and
                0 <= dig_y < game.LEVEL_HEIGHT and
                game.tiles[dig_y][dig_x] == game.BRICK and
                game.dig_cooldown <= 0)

    def _can_climb_up(self):
        """Check if we can climb up from current position."""
        game = self.game
        px, py = game.player_x, game.player_y
        current_tile = game.tiles[py][px]

        if current_tile == game.LADDER:
            return py > 0 and not game.is_solid(px, py - 1)
        if py > 0 and game.tiles[py - 1][px] == game.LADDER:
            return not game.is_solid(px, py - 1)
        return False

    def _find_best_gold(self):
        """Find the best gold piece to collect (nearest accessible one)."""
        game = self.game
        px, py = game.player_x, game.player_y

        best_gold = None
        best_score = float('inf')

        for y in range(game.LEVEL_HEIGHT):
            for x in range(game.LEVEL_WIDTH):
                if game.tiles[y][x] == game.GOLD:
                    # Calculate distance (Manhattan with vertical penalty)
                    dist = abs(x - px) + abs(y - py) * 2

                    # Prefer gold that's easier to reach
                    if y >= py:
                        dist -= 2  # Slight preference for gold at same level or below

                    # Check if path seems safe from enemies
                    if self._is_path_dangerous(px, py, x, y):
                        dist += 20  # Heavy penalty for dangerous paths

                    if dist < best_score:
                        best_score = dist
                        best_gold = (x, y)

        return best_gold

    def _is_path_dangerous(self, px, py, gx, gy):
        """Check if path to gold is blocked by enemies."""
        game = self.game

        for enemy in game.enemies:
            if enemy['trapped']:
                continue

            ex, ey = enemy['x'], enemy['y']

            # Check if enemy is roughly between player and gold
            min_x, max_x = min(px, gx), max(px, gx)
            min_y, max_y = min(py, gy), max(py, gy)

            if min_x - 2 <= ex <= max_x + 2 and min_y - 2 <= ey <= max_y + 2:
                return True

        return False

    def _move_toward_gold(self, target):
        """Determine movement to reach gold target."""
        game = self.game
        px, py = game.player_x, game.player_y
        gx, gy = target

        action = {
            'left': False, 'right': False,
            'up': False, 'down': False,
            'dig': False
        }

        dx = gx - px
        dy = gy - py

        current_tile = game.tiles[py][px]
        on_ladder = current_tile == game.LADDER
        on_rope = current_tile == game.ROPE

        # If we're at the gold position, we should collect it
        if dx == 0 and dy == 0:
            return action

        # If gold is above us, find a way up
        if dy < 0:
            # Try to climb if on ladder
            if on_ladder and not game.is_solid(px, py - 1):
                action['up'] = True
                return action

            # Look for ladder above
            if py > 0 and game.tiles[py - 1][px] == game.LADDER:
                action['up'] = True
                return action

            # Need to find a ladder - move toward nearest one going up
            ladder_x = self._find_ladder_going_up()
            if ladder_x is not None:
                if px < ladder_x and not game.is_solid(px + 1, py):
                    action['right'] = True
                elif px > ladder_x and not game.is_solid(px - 1, py):
                    action['left'] = True
                elif px == ladder_x:
                    action['up'] = True
                return action

        # If gold is below us, find a way down
        if dy > 0:
            # Try to climb down if on or above a ladder
            if on_ladder:
                below_y = py + 1
                if below_y < game.LEVEL_HEIGHT:
                    if game.tiles[below_y][px] == game.LADDER or not game.is_solid(px, below_y):
                        action['down'] = True
                        return action

            # Check if there's a ladder below
            if py + 1 < game.LEVEL_HEIGHT and game.tiles[py + 1][px] == game.LADDER:
                action['down'] = True
                return action

            # Try falling through a hole
            if (px, py + 1) in game.holes:
                action['down'] = True
                return action

            # Try to dig down if standing on brick
            if self._should_dig_to_descend(gx):
                action['dig'] = True
                return action

            # Find ladder going down
            ladder_x = self._find_ladder_going_down()
            if ladder_x is not None:
                if px < ladder_x and not game.is_solid(px + 1, py):
                    action['right'] = True
                elif px > ladder_x and not game.is_solid(px - 1, py):
                    action['left'] = True
                return action

        # Move horizontally toward gold
        if dx > 0 and not game.is_solid(px + 1, py):
            action['right'] = True
        elif dx < 0 and not game.is_solid(px - 1, py):
            action['left'] = True
        elif dx > 0:
            # Blocked right, try to dig
            if self._can_dig_right() and dy >= 0:
                action['dig'] = True
                game.player_facing = 1
            elif not game.is_solid(px - 1, py):
                action['left'] = True  # Go around
        elif dx < 0:
            # Blocked left, try to dig
            if self._can_dig_left() and dy >= 0:
                action['dig'] = True
                game.player_facing = -1
            elif not game.is_solid(px + 1, py):
                action['right'] = True  # Go around

        return action

    def _find_ladder_going_up(self):
        """Find the nearest ladder that goes up from current level."""
        game = self.game
        px, py = game.player_x, game.player_y

        best_ladder_x = None
        best_dist = float('inf')

        for x in range(game.LEVEL_WIDTH):
            # Check if there's a ladder at current level that goes up
            if py > 0 and game.tiles[py][x] == game.LADDER:
                # Verify it goes up
                if game.tiles[py - 1][x] == game.LADDER or game.tiles[py - 1][x] == game.EMPTY:
                    dist = abs(x - px)
                    if dist < best_dist:
                        best_dist = dist
                        best_ladder_x = x

            # Also check ladder starting above
            if py > 0 and game.tiles[py - 1][x] == game.LADDER:
                dist = abs(x - px)
                if dist < best_dist:
                    best_dist = dist
                    best_ladder_x = x

        return best_ladder_x

    def _find_ladder_going_down(self):
        """Find the nearest ladder that goes down from current level."""
        game = self.game
        px, py = game.player_x, game.player_y

        best_ladder_x = None
        best_dist = float('inf')

        for x in range(game.LEVEL_WIDTH):
            # Check if there's a ladder at or below current level
            if py + 1 < game.LEVEL_HEIGHT and game.tiles[py + 1][x] == game.LADDER:
                dist = abs(x - px)
                if dist < best_dist:
                    best_dist = dist
                    best_ladder_x = x

        return best_ladder_x

    def _should_dig_to_descend(self, target_x):
        """Check if we should dig a hole to descend toward target."""
        game = self.game
        px, py = game.player_x, game.player_y

        if game.dig_cooldown > 0:
            return False

        # Check which direction to dig based on target
        if target_x > px:
            # Target is to the right, dig right
            dig_x = px + 1
            game.player_facing = 1
        else:
            # Target is to the left, dig left
            dig_x = px - 1
            game.player_facing = -1

        dig_y = py + 1

        if 0 <= dig_x < game.LEVEL_WIDTH and 0 <= dig_y < game.LEVEL_HEIGHT:
            return game.tiles[dig_y][dig_x] == game.BRICK

        return False

    def _move_to_exit(self):
        """Move toward the exit at the top of the level."""
        game = self.game
        px, py = game.player_x, game.player_y
        exit_x = game.exit_x

        action = {
            'left': False, 'right': False,
            'up': False, 'down': False,
            'dig': False
        }

        # Exit is at the top, need to climb
        current_tile = game.tiles[py][px]

        # If on exit ladder, climb!
        if current_tile == game.LADDER:
            if py > 1:
                action['up'] = True
                return action

        # Move toward exit ladder
        dx = exit_x - px

        if abs(dx) <= 1 and current_tile == game.LADDER:
            action['up'] = True
        elif dx > 0 and not game.is_solid(px + 1, py):
            action['right'] = True
        elif dx < 0 and not game.is_solid(px - 1, py):
            action['left'] = True
        elif dx == 0:
            # We're at exit x, try to climb
            if py > 0 and game.tiles[py - 1][px] == game.LADDER:
                action['up'] = True
            elif game.tiles[py][px] == game.LADDER:
                action['up'] = True

        return action
