"""
Bloons TD Demo - AI Attract Mode
=================================
Bloons Tower Defense plays itself. The AI places towers near path bends,
upgrades them, and lets waves auto-start for income. Skips steps it
can't afford and retries when money comes in.

AI Strategy:
- Walk through a build order of placements and upgrades
- Skip steps that are too expensive; retry when income arrives
- Directly set tower type (demo privilege) to avoid cycling bugs
- Idle gracefully between builds, letting waves generate income
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.bloonstd import (
    BloonsTD, PHASE_PLACE, PHASE_WAVE, PHASE_WAVE_END,
    TOWER_DART, TOWER_TACK, TOWER_CANNON, TOWER_ICE,
    TOWER_DEFS, CELL_SIZE, PATH_CELLS, WAVE_AUTO_START
)

# Build steps: (grid_x, grid_y, tower_type, is_upgrade)
# Positions near path bends (avoid gx>=28 near vertical path at x=58)
BUILD_ORDER = [
    # Phase 1: Cheap darts for early waves ($150 each)
    (14, 7, TOWER_DART, False),
    (26, 7, TOWER_DART, False),
    # Phase 2: Cover second horizontal pass
    (14, 14, TOWER_DART, False),
    # Upgrade first dart while saving for tack
    (14, 7, TOWER_DART, True),
    # Tack near second bend for burst damage
    (26, 14, TOWER_TACK, False),
    (26, 7, TOWER_DART, True),
    # Phase 3: Third pass + splash
    (14, 20, TOWER_DART, False),
    (26, 20, TOWER_CANNON, False),
    (26, 14, TOWER_TACK, True),
    (26, 20, TOWER_CANNON, True),
    # Phase 4: Slow + fourth pass
    (14, 26, TOWER_ICE, False),
    (26, 26, TOWER_DART, False),
    (20, 7, TOWER_TACK, False),
    (14, 14, TOWER_DART, True),
    (14, 26, TOWER_ICE, True),
    (20, 7, TOWER_TACK, True),
    # Phase 5: Fill gaps
    (20, 14, TOWER_DART, False),
    (20, 20, TOWER_DART, False),
    (8, 14, TOWER_ICE, False),
    (8, 26, TOWER_CANNON, False),
    # Late upgrades
    (14, 20, TOWER_DART, True),
    (26, 26, TOWER_DART, True),
    (20, 14, TOWER_DART, True),
    (20, 20, TOWER_DART, True),
    (8, 26, TOWER_CANNON, True),
    (8, 14, TOWER_ICE, True),
]

MOVE_INTERVAL = 0.10   # seconds between cursor steps
PAUSE_AFTER_ACTION = 0.4  # brief pause after placing/upgrading


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
        self.game.money = 1200  # demo gets extra money for a fuller defense
        self.build_index = 0
        self.move_timer = 0.0
        self.game_over_timer = 0.0
        self.pending_input = None

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

        # Send pending single-frame input, then clear
        if self.pending_input:
            self.game.update(self.pending_input, dt)
            self.pending_input = None
            return

        # AI decision tick
        self.move_timer += dt
        if self.move_timer >= MOVE_INTERVAL:
            self.move_timer -= MOVE_INTERVAL
            inp = self._ai_step()
            if inp:
                self.pending_input = inp
                return

        # Tick game with blank input
        self.game.update(InputState(), dt)

    def _find_tower_at(self, gx, gy):
        """Find tower near the given grid position."""
        for i, t in enumerate(self.game.towers):
            if abs(t['gx'] - gx) <= 1 and abs(t['gy'] - gy) <= 1:
                return i
        return None

    def _ai_step(self):
        """One step of AI logic. Returns InputState or None."""
        game = self.game

        # During wave-end phase, press action to advance
        if game.phase == PHASE_WAVE_END:
            inp = InputState()
            inp.action_l = True
            return inp

        # Speed up wave starts when nothing to build
        if game.phase == PHASE_PLACE and game.wave_countdown > 3.0:
            game.wave_countdown = 3.0

        # Scan build order for first actionable step
        target = self._find_next_target()
        if target is None:
            return None

        idx, gx, gy, ttype, is_upgrade = target
        self.build_index = idx
        inp = InputState()

        if is_upgrade:
            return self._handle_upgrade(game, gx, gy, inp)
        else:
            return self._handle_place(game, gx, gy, ttype, inp)

    def _find_next_target(self):
        """Find the first build step that can be acted on now."""
        game = self.game
        for i, (gx, gy, ttype, is_up) in enumerate(BUILD_ORDER):
            if is_up:
                idx = self._find_tower_at(gx, gy)
                if idx is None:
                    continue  # tower not placed yet
                if game.towers[idx]['upgraded']:
                    continue  # already upgraded
                if game.money < TOWER_DEFS[game.towers[idx]['type']]['upgrade_cost']:
                    continue  # can't afford
                return (i, gx, gy, ttype, True)
            else:
                if self._find_tower_at(gx, gy) is not None:
                    continue  # already placed
                if game.money < TOWER_DEFS[ttype]['cost']:
                    continue  # can't afford
                return (i, gx, gy, ttype, False)
        return None

    def _handle_upgrade(self, game, target_gx, target_gy, inp):
        """Handle an upgrade build step."""
        tower_idx = self._find_tower_at(target_gx, target_gy)
        if tower_idx is None:
            return None

        tower = game.towers[tower_idx]

        # Navigate cursor to tower
        dx = tower['gx'] - game.cursor_gx
        dy = tower['gy'] - game.cursor_gy

        if abs(dx) > 1 or abs(dy) > 1:
            return self._move_toward(dx, dy, inp)

        # At tower — select or upgrade
        if game.selected_tower == tower_idx:
            inp.action_l = True
            self.move_timer = -PAUSE_AFTER_ACTION
        else:
            inp.action_l = True
        return inp

    def _handle_place(self, game, target_gx, target_gy, target_type, inp):
        """Handle a tower placement build step."""
        # Set tower type directly (demo privilege)
        game.selected_tower_type = target_type

        # Move cursor toward target
        dx = target_gx - game.cursor_gx
        dy = target_gy - game.cursor_gy

        if dx != 0 or dy != 0:
            return self._move_toward(dx, dy, inp)

        # At target — place
        if game._can_place(target_gx, target_gy):
            inp.action_l = True
            self.move_timer = -PAUSE_AFTER_ACTION
        return inp

    def _move_toward(self, dx, dy, inp):
        """Move cursor one step toward target."""
        if abs(dx) >= abs(dy):
            if dx > 0:
                inp.right_pressed = True
            else:
                inp.left_pressed = True
        else:
            if dy > 0:
                inp.down_pressed = True
            else:
                inp.up_pressed = True
        return inp

    def draw(self):
        self.game.draw()

        # Overlay blinking "DEMO"
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)
