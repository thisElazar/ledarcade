"""
Darts Demo - AI Attract Mode
============================
Darts plays itself using AI for idle screen demos.
The AI aims for high-value targets like triple 20 and bullseye.

AI Strategy:
- Automatically select 1P mode
- Track sweeping aim bars
- Target triple 20 (top of board, x~32, y~16) or bullseye (x~32, y~32)
- Also attempt bonus tiles when convenient
- Time throws when sweep line crosses target position
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

# Import the actual game
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.darts import (
    Darts, PHASE_MODE_SELECT, PHASE_AIM_X, PHASE_AIM_Y,
    PHASE_DART_LAND, PHASE_TURN_CHANGE, PHASE_GAME_OVER_2P,
    CX, CY, INNER_BULL_R, TRIPLE_R, INNER_SINGLE_R
)


# Target positions (x, y) for high-value throws
# Triple 20 is at the top of the board (~16 pixels from center upward)
TRIPLE_20_X = 32
TRIPLE_20_Y = 16  # top of board, triple ring

# Bullseye
BULLSEYE_X = 32
BULLSEYE_Y = 32

# Triple 19 (bottom-left area)
TRIPLE_19_X = 24
TRIPLE_19_Y = 46

# Aim tolerance - how close the sweep needs to be to trigger
AIM_TOLERANCE = 3


class DartsDemo(Visual):
    name = "DARTS"
    description = "AI throws darts"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = Darts(self.display)
        self.game.reset()
        self.game_over_timer = 0.0

        # AI state
        self.current_target = None  # (x, y) target for current throw
        self.select_delay = 0.5  # Delay before selecting mode
        self.select_timer = 0.0
        self._pick_target()

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
                self.select_timer = 0.0
                self._pick_target()
            return

        # Create AI input
        ai_input = self._decide_action(dt)
        self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()

        # Overlay "DEMO" text (blinking)
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)

    def _pick_target(self):
        """Pick a target for the next throw."""
        # Weight towards triple 20 and bullseye, occasionally others
        r = random.random()
        if r < 0.5:
            # Triple 20 - most valuable consistent target
            self.current_target = (TRIPLE_20_X, TRIPLE_20_Y)
        elif r < 0.75:
            # Bullseye - 50 points
            self.current_target = (BULLSEYE_X, BULLSEYE_Y)
        elif r < 0.9:
            # Triple 19
            self.current_target = (TRIPLE_19_X, TRIPLE_19_Y)
        else:
            # Random spot on the board for variety
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(10, 25)
            x = int(CX + dist * math.cos(angle))
            y = int(CY + dist * math.sin(angle))
            self.current_target = (x, y)

    def _check_bonus_target(self):
        """Check if bonus tile is a better target than current."""
        if not self.game.bonus_pixels:
            return

        # Get center of bonus area
        bonus_list = list(self.game.bonus_pixels)
        if not bonus_list:
            return

        # Average position of bonus pixels
        avg_x = sum(p[0] for p in bonus_list) / len(bonus_list)
        avg_y = sum(p[1] for p in bonus_list) / len(bonus_list)

        # 30% chance to go for bonus instead
        if random.random() < 0.3:
            self.current_target = (int(avg_x), int(avg_y))

    def _decide_action(self, dt):
        """AI decision-making for aiming and throwing darts."""
        ai_input = InputState()
        game = self.game

        # Handle mode select - choose 1P
        if game.phase == PHASE_MODE_SELECT:
            self.select_timer += dt
            if self.select_timer > self.select_delay:
                # Make sure 1P is selected (mode_select == 0), then confirm
                if game.mode_select != 0:
                    ai_input.up_pressed = True
                else:
                    ai_input.action_l = True
            return ai_input

        # Handle waiting phases
        if game.phase in (PHASE_DART_LAND, PHASE_TURN_CHANGE):
            return ai_input

        # Handle 2P game over (shouldn't happen in demo, but just in case)
        if game.phase == PHASE_GAME_OVER_2P:
            ai_input.action_l = True
            return ai_input

        # Check if we should aim for bonus tile
        if game.phase == PHASE_AIM_X:
            self._check_bonus_target()

        # AIM_X phase - lock X when sweep is at target X
        if game.phase == PHASE_AIM_X:
            target_x = self.current_target[0]
            current_x = game.sweep_x

            # Check if sweep is close enough to target
            if abs(current_x - target_x) <= AIM_TOLERANCE:
                ai_input.action_l = True
            return ai_input

        # AIM_Y phase - lock Y when sweep is at target Y
        if game.phase == PHASE_AIM_Y:
            target_y = self.current_target[1]
            current_y = game.sweep_y

            # Check if sweep is close enough to target
            if abs(current_y - target_y) <= AIM_TOLERANCE:
                ai_input.action_l = True
                # Pick new target for next throw
                self._pick_target()
            return ai_input

        return ai_input
