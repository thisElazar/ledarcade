"""
Bloons TD Demo - AI Attract Mode
=================================
Bloons Tower Defense plays itself using a predefined build order.
The AI moves the cursor toward strategic positions near path bends,
places towers when it can afford them, and watches waves play out.

AI Strategy:
- Follow a predefined build order of tower positions near path bends
- Move cursor one grid step at a time for natural-looking movement
- Place towers when affordable, skip if position is blocked
- Let waves auto-start via the 15-second countdown
- Restart automatically after game over or win
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

# Pre-planned tower placements: (grid_x, grid_y, tower_type)
# Positions are near path bends where bloons spend the most time in range
BUILD_ORDER = [
    (14, 7, TOWER_DART),      # near first horizontal pass, top side
    (14, 14, TOWER_DART),     # between first and second passes
    (28, 14, TOWER_TACK),     # near bend area
    (28, 7, TOWER_DART),      # top area coverage
    (14, 20, TOWER_DART),     # near second pass
    (28, 20, TOWER_CANNON),   # splash near bends
    (14, 26, TOWER_ICE),      # slow near third pass
    (28, 26, TOWER_DART),     # third pass area
    (20, 7, TOWER_TACK),      # more top coverage
    (20, 20, TOWER_DART),     # mid coverage
    (8, 26, TOWER_CANNON),    # lower splash
    (20, 14, TOWER_DART),     # fill in middle
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
        self.placing = True          # True = moving toward target; False = idle/watching
        self.cycling_type = False     # True = navigating to cycle tower type
        self.cycle_done = False       # True = type is correct, move to real target
        self.wait_timer = 0.0        # pause between placements

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

    def _ai_step(self, ai_input):
        """One step of AI logic: move cursor or press action."""
        game = self.game
        target_gx, target_gy, target_type = BUILD_ORDER[self.build_index]

        # Check if we can afford this tower
        cost = TOWER_DEFS[target_type]['cost']
        if game.money < cost:
            # Can't afford — just wait, waves will earn money
            return

        # If tower type doesn't match, cycle it first
        if game.selected_tower_type != target_type and not self.cycle_done:
            # Press action on current spot to cycle (works on invalid spots)
            # First move somewhere that isn't a tower to avoid selecting it
            if game._tower_at(game.cursor_gx, game.cursor_gy) is not None:
                # Move away from any tower first
                ai_input.right_pressed = True
                return
            if (game.cursor_gx, game.cursor_gy) in PATH_CELLS or \
               game._can_place(game.cursor_gx, game.cursor_gy):
                # On path or valid spot — move to ensure we're on invalid non-path
                # Actually, pressing action on path cells cycles type too
                pass
            ai_input.action_l = True
            return

        self.cycle_done = True

        # Move cursor toward target position
        dx = target_gx - game.cursor_gx
        dy = target_gy - game.cursor_gy

        if dx != 0 or dy != 0:
            # Move one step — prefer larger delta first
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
            # Position blocked (already has a tower or invalid) — skip
            self._advance_build()

    def _advance_build(self):
        """Move to the next entry in the build order."""
        self.build_index += 1
        self.cycle_done = False
        self.move_timer = -0.3  # brief pause between placements

    def draw(self):
        self.game.draw()

        # Overlay blinking "DEMO" in top-right area
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)
