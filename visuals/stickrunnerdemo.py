"""
Stick Runner Demo - AI Attract Mode
====================================
Stick Runner plays itself by timing jumps to cross rooftop gaps.

AI Strategy:
- Look ahead for gaps between buildings
- Calculate when to jump based on gap distance and scroll speed
- Account for building height differences (jump earlier for higher targets)
- Use the game's physics to estimate jump distance
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.stickrunner import StickRunner


class StickRunnerDemo(Visual):
    name = "STICK RUNNER DEMO"
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
        """Decide whether to jump based on upcoming gaps and building heights."""
        game = self.game

        # Can only jump when on ground or near ground
        can_jump_now = game.on_ground or game._near_ground()
        if not can_jump_now:
            return False

        player_x = game.PLAYER_X
        player_y = game.player_y

        # Find the current building we're on
        current_building = None
        for b in game.buildings:
            if b['x'] <= player_x <= b['x'] + b['width']:
                current_building = b
                break

        if current_building is None:
            # Not on a building - we're falling, can't do much
            return False

        # Find the next building (the one we need to jump to)
        next_building = None
        current_end = current_building['x'] + current_building['width']

        for b in game.buildings:
            # Building starts after our current building ends
            if b['x'] > current_building['x'] + current_building['width'] - 5:
                if next_building is None or b['x'] < next_building['x']:
                    next_building = b

        if next_building is None:
            # No upcoming building
            return False

        # Calculate the gap distance
        gap_start = current_end
        gap_end = next_building['x']
        gap_width = gap_end - gap_start

        # Distance from player to the gap
        dist_to_gap = gap_start - player_x

        # Get the jump distance from game physics
        jump_dist = game._get_jump_distance()

        # Calculate height difference
        current_height = game._get_landing_y(current_building, player_x)
        next_height = next_building['y']  # Landing Y at start of next building
        height_diff = next_height - current_height  # Negative means jumping UP

        # Calculate optimal jump timing
        # We need to jump so we land on the next building
        # Jump distance tells us how far we travel horizontally during a jump

        # Ideal jump point: we want to land about 3-5 pixels into the next building
        target_landing = gap_end + 4
        ideal_jump_dist = target_landing - player_x

        # Adjust for height - jumping UP requires earlier jump
        if height_diff < -3:  # Jumping up significantly
            # Jump earlier when going up
            trigger_dist = ideal_jump_dist - jump_dist * 0.1
        elif height_diff > 3:  # Jumping down
            # Can jump a bit later when going down (more air time)
            trigger_dist = ideal_jump_dist - jump_dist * 0.05
        else:
            trigger_dist = ideal_jump_dist - jump_dist * 0.08

        # Safety margin - don't wait until the very edge
        # Jump when we're within optimal range
        min_trigger = trigger_dist - 6
        max_trigger = trigger_dist + 3

        # Emergency jump - very close to edge
        edge_dist = gap_start - player_x
        if edge_dist < 5 and edge_dist > 0:
            return True

        # Check if we're in the jump window
        if min_trigger <= dist_to_gap <= max_trigger:
            return True

        # Account for scroll speed changes - at higher speeds, need to jump earlier
        speed_factor = game.scroll_speed / 40.0  # Base speed is 40
        if speed_factor > 1.2:
            # At higher speeds, expand the trigger window
            early_trigger = min_trigger - (speed_factor - 1.0) * 5
            if early_trigger <= dist_to_gap <= max_trigger:
                return True

        return False
