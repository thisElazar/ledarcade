"""
Geometry Dash Demo - AI Attract Mode
=====================================
Geometry Dash plays itself by timing jumps to clear obstacles.

AI Strategy:
- Look ahead at upcoming obstacles (spikes, blocks)
- Jump when an obstacle is approaching at the right distance
- Time jumps to clear spikes and gaps
- The game auto-scrolls, so AI just needs to decide when to jump
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.geometrydash import GeometryDash


class GeometryDemo(Visual):
    name = "GEOMETRY"
    description = "AI plays Geometry Dash"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = GeometryDash(self.display)
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
        if self.should_jump and self.game.on_ground:
            ai_input.action_l_held = True

        self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()

        # Overlay "DEMO" text (blinking)
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)

    def _should_jump(self):
        """Decide whether to jump based on upcoming obstacles."""
        game = self.game

        # Can only jump when on ground
        if not game.on_ground:
            return False

        player_x = game.PLAYER_X
        player_y = game.player_y
        player_size = game.PLAYER_SIZE
        player_right = player_x + player_size
        player_bottom = player_y + player_size

        # Find obstacles ahead of the player
        threats = []
        for obs in game.obstacles:
            obs_left = obs['x']
            obs_right = obs['x'] + obs.get('width', 6)
            obs_top = obs['y']
            obs_bottom = obs['y'] + obs.get('height', 6)

            # Only consider obstacles ahead of player
            if obs_right < player_x:
                continue

            # Calculate horizontal distance to obstacle
            dist = obs_left - player_right

            # Skip obstacles too far away
            if dist > 40:
                continue

            threats.append({
                'type': obs['type'],
                'dist': dist,
                'left': obs_left,
                'right': obs_right,
                'top': obs_top,
                'bottom': obs_bottom,
                'width': obs.get('width', 6),
                'height': obs.get('height', 6)
            })

        if not threats:
            return False

        # Sort by distance
        threats.sort(key=lambda t: t['dist'])

        # Analyze the nearest threat
        nearest = threats[0]

        # Calculate jump timing based on obstacle type and distance
        # Jump arc: player jumps up and forward, lands after about jump_distance pixels
        jump_distance = game.jump_distance  # Pre-calculated in game

        # Optimal jump distance depends on obstacle type
        if nearest['type'] == 'spike':
            # For spikes, jump early enough to clear them
            # Jump needs to peak around or after the spike
            optimal_dist = jump_distance * 0.45  # Jump when spike is about 45% of jump distance away
            trigger_range = (optimal_dist - 8, optimal_dist + 4)

        elif nearest['type'] == 'block':
            # For blocks, we might want to land on top or jump over
            block_height = nearest['height']
            if block_height <= 5:
                # Small blocks - can land on or jump over
                optimal_dist = jump_distance * 0.4
                trigger_range = (optimal_dist - 6, optimal_dist + 6)
            else:
                # Tall blocks - need to jump over completely
                optimal_dist = jump_distance * 0.45
                trigger_range = (optimal_dist - 8, optimal_dist + 4)

        elif nearest['type'] == 'platform':
            # Platforms are safe to land on, only jump if there's a spike nearby
            # Check if there are spikes in the vicinity
            has_nearby_spike = False
            for t in threats:
                if t['type'] == 'spike' and t['dist'] < jump_distance * 0.6:
                    has_nearby_spike = True
                    break
            if has_nearby_spike:
                optimal_dist = jump_distance * 0.45
                trigger_range = (optimal_dist - 8, optimal_dist + 4)
            else:
                return False
        else:
            # Unknown type, be cautious
            optimal_dist = jump_distance * 0.4
            trigger_range = (optimal_dist - 8, optimal_dist + 6)

        # Check if we should jump based on distance
        if trigger_range[0] <= nearest['dist'] <= trigger_range[1]:
            return True

        # Emergency jump - obstacle is very close
        if nearest['dist'] < 5 and nearest['type'] == 'spike':
            # Very close spike, jump immediately
            return True

        # Look for grouped obstacles (multiple spikes in a row)
        # If there are multiple obstacles close together, jump earlier
        grouped_count = 0
        for t in threats:
            if t['dist'] < jump_distance * 0.7:
                grouped_count += 1

        if grouped_count >= 2:
            # Multiple obstacles ahead, check if first is in range
            first_dist = threats[0]['dist']
            if first_dist < jump_distance * 0.55 and first_dist > 2:
                return True

        return False
