"""
Bloons TD Demo - AI Attract Mode
=================================
Bloons Tower Defense plays itself using a predefined build order
with upgrades. The AI places towers near path bends for maximum
coverage and upgrades them for increased effectiveness.

AI Strategy:
- Follow expanded build order of tower placements and upgrades
- Position towers near path bends where bloons spend the most time
- Upgrade existing towers for increased range and fire rate
- Cycle tower type efficiently when needed
- Idle gracefully after build order exhausted
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState
import random
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.bloonstd import (
    BloonsTD, PHASE_PLACE, PHASE_WAVE, PHASE_WAVE_END,
    TOWER_DART, TOWER_TACK, TOWER_CANNON, TOWER_ICE,
    TOWER_DEFS, CELL_SIZE, PATH_CELLS, WAVE_AUTO_START
)

# Build steps: (grid_x, grid_y, tower_type, is_upgrade)
# is_upgrade=True means navigate to existing tower and upgrade it
# Positions chosen near path bends for maximum coverage
BUILD_ORDER = [
    # Phase 1: Early defense near first bend
    (14, 7, TOWER_DART, False),       # near first horizontal pass
    (14, 14, TOWER_DART, False),      # between first and second passes
    # Upgrade first two darts for better range
    (14, 7, TOWER_DART, True),
    (14, 14, TOWER_DART, True),
    # Phase 2: Second bend coverage
    (28, 14, TOWER_TACK, False),      # tack near bend area
    (28, 7, TOWER_DART, False),       # top area coverage
    (14, 20, TOWER_DART, False),      # near second pass
    # Upgrade tack for burst damage
    (28, 14, TOWER_TACK, True),
    # Phase 3: Splash and slow
    (28, 20, TOWER_CANNON, False),    # splash near bends
    (14, 26, TOWER_ICE, False),       # slow near third pass
    (28, 26, TOWER_DART, False),      # third pass coverage
    # Upgrade cannon and ice
    (28, 20, TOWER_CANNON, True),
    (14, 26, TOWER_ICE, True),
    # Phase 4: Fill coverage gaps
    (20, 7, TOWER_TACK, False),       # more top coverage
    (20, 20, TOWER_DART, False),      # mid coverage
    (8, 26, TOWER_CANNON, False),     # lower splash
    # Upgrade mid towers
    (20, 7, TOWER_TACK, True),
    (20, 20, TOWER_DART, True),
    # Phase 5: Late game reinforcement
    (20, 14, TOWER_DART, False),      # fill middle
    (8, 14, TOWER_ICE, False),        # extra slow
    (28, 4, TOWER_DART, False),       # top right
    (8, 20, TOWER_DART, False),       # left mid
    # Final upgrades
    (28, 26, TOWER_DART, True),
    (8, 26, TOWER_CANNON, True),
    (20, 14, TOWER_DART, True),
    (8, 14, TOWER_ICE, True),
]

MOVE_INTERVAL = 0.08  # seconds between cursor steps


class BloonsTDDemo(Visual):
    name = "BLOONS TD"
    description = "AI tower defense"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = BloonsTD(self.display)
        self.game.reset()
        self.build_index = 0
        self.move_timer = 0.0
        self.game_over_timer = 0.0
        self.placing = True
        self.wait_timer = 0.0
        self.target_type_set = False  # whether we've set the right tower type

    def handle_input(self, input_state):
        return False

    def update(self, dt):
        self.time += dt

        # Handle game over or win — restart after delay
        if self.game.state in (GameState.GAME_OVER, GameState.WIN):
            self.game_over_timer += dt
            if self.game_over_timer > 3.0:
                self.reset()
            return

        # Build AI input each frame
        ai_input = InputState()

        if self.build_index < len(BUILD_ORDER) and self.placing:
            self.move_timer += dt
            if self.move_timer >= MOVE_INTERVAL:
                self.move_timer -= MOVE_INTERVAL
                self._ai_step(ai_input)

        self.game.update(ai_input, dt)

    def _find_tower_at(self, gx, gy):
        """Find tower near the given grid position."""
        for i, t in enumerate(self.game.towers):
            if abs(t['gx'] - gx) <= 1 and abs(t['gy'] - gy) <= 1:
                return i
        return None

    def _ai_step(self, ai_input):
        """One step of AI logic: move cursor or press action."""
        game = self.game
        target_gx, target_gy, target_type, is_upgrade = BUILD_ORDER[self.build_index]

        if is_upgrade:
            # Upgrade step: navigate to existing tower and upgrade
            tower_idx = self._find_tower_at(target_gx, target_gy)
            if tower_idx is None:
                # Tower doesn't exist, skip
                self._advance_build()
                return

            tower = game.towers[tower_idx]
            tdef = TOWER_DEFS[tower['type']]

            # Check if already upgraded or can't afford
            if tower['upgraded'] or game.money < tdef['upgrade_cost']:
                if tower['upgraded']:
                    self._advance_build()
                # else wait for money
                return

            # Navigate cursor to tower
            dx = tower['gx'] - game.cursor_gx
            dy = tower['gy'] - game.cursor_gy

            if abs(dx) > 1 or abs(dy) > 1:
                # Move toward tower
                if abs(dx) >= abs(dy):
                    if dx > 0:
                        ai_input.right_pressed = True
                    else:
                        ai_input.left_pressed = True
                else:
                    if dy > 0:
                        ai_input.down_pressed = True
                    else:
                        ai_input.up_pressed = True
                return

            # At tower position
            if game.selected_tower == tower_idx:
                # Already selected, press to upgrade
                ai_input.action_l = True
                self._advance_build()
            else:
                # Select the tower first
                ai_input.action_l = True
            return

        # Place step: need correct tower type and navigate to position
        cost = TOWER_DEFS[target_type]['cost']
        if game.money < cost:
            return  # Wait for money

        # Ensure correct tower type is selected
        if game.selected_tower_type != target_type and not self.target_type_set:
            # Cycle tower type by pressing action on an invalid/path cell
            # First make sure we're not on a tower
            if game._tower_at(game.cursor_gx, game.cursor_gy) is not None:
                ai_input.right_pressed = True
                return
            ai_input.action_l = True
            # Check if cycling got us to the right type
            # (The action will cycle type if on non-placeable spot)
            return

        self.target_type_set = True

        # Move cursor toward target position
        dx = target_gx - game.cursor_gx
        dy = target_gy - game.cursor_gy

        if dx != 0 or dy != 0:
            if abs(dx) >= abs(dy):
                if dx > 0:
                    ai_input.right_pressed = True
                else:
                    ai_input.left_pressed = True
            else:
                if dy > 0:
                    ai_input.down_pressed = True
                else:
                    ai_input.up_pressed = True
            return

        # At target position — try to place
        if game._can_place(target_gx, target_gy):
            ai_input.action_l = True
            self._advance_build()
        else:
            # Position blocked — skip
            self._advance_build()

    def _advance_build(self):
        """Move to the next entry in the build order."""
        self.build_index += 1
        self.target_type_set = False
        self.move_timer = -0.3  # brief pause between placements

        # If build order exhausted, stop placing
        if self.build_index >= len(BUILD_ORDER):
            self.placing = False

    def draw(self):
        self.game.draw()

        # Overlay blinking "DEMO" in top-right area
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)
