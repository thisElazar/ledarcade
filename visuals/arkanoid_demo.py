"""
Arkanoid Demo - AI Attract Mode
===============================
Arkanoid plays itself using simple AI for idle screen demos.
The AI predicts where the ball will land and moves the paddle to intercept.

AI Strategy:
- Launch ball automatically when waiting
- Predict ball trajectory accounting for wall bounces
- Move paddle toward predicted landing position
- Prioritize catching falling powerups
- Fire laser automatically when powerup is active
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

# Import the actual game
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.arkanoid import Arkanoid, PLAY_LEFT, PLAY_RIGHT


class ArkanoidDemo(Visual):
    name = "ARKANOID DEMO"
    description = "AI plays Arkanoid"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = Arkanoid(self.display)
        self.game.reset()
        self.decision_timer = 0.0
        self.decision_interval = 0.05  # Recalculate every 50ms
        self.current_action = None
        self.game_over_timer = 0.0

    def handle_input(self, input_state):
        # Demo doesn't respond to input (auto-plays)
        return False

    def update(self, dt):
        self.time += dt

        # If game over or win, restart after a pause
        if self.game.state in (GameState.GAME_OVER, GameState.WIN):
            self.game_over_timer += dt
            if self.game_over_timer > 3.0:
                self.game.reset()
                self.game_over_timer = 0.0
            return

        # Make AI decisions periodically
        self.decision_timer += dt
        if self.decision_timer >= self.decision_interval:
            self.decision_timer = 0.0
            self.current_action = self._decide_action()

        # Create input state with AI's chosen action
        ai_input = InputState()
        if self.current_action == 'launch':
            ai_input.action_l = True
        elif self.current_action == 'left':
            ai_input.left = True
        elif self.current_action == 'right':
            ai_input.right = True
        elif self.current_action == 'fire':
            ai_input.action_l = True

        self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()

        # Overlay "DEMO" text (blinking)
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)

    def _decide_action(self):
        """AI decision-making for paddle movement."""
        game = self.game

        # Check if any ball needs launching
        for ball in game.balls:
            if not ball['launched']:
                return 'launch'

        # Priority 1: Catch falling powerups (they're valuable)
        if game.falling_powerups:
            # Find the lowest (closest to paddle) powerup
            closest_powerup = max(game.falling_powerups, key=lambda p: p['y'])
            powerup_x = closest_powerup['x']
            paddle_center = game.paddle_x + game.paddle_width / 2

            # If powerup is getting close to paddle level, prioritize it
            if closest_powerup['y'] > game.paddle_y - 20:
                if abs(paddle_center - powerup_x) < 2:
                    return None  # Close enough
                elif paddle_center < powerup_x:
                    return 'right'
                else:
                    return 'left'

        # Priority 2: Fire laser if we have it and there are bricks
        if game.active_powerup == game.POWERUP_LASER and game.laser_cooldown <= 0:
            return 'fire'

        # Priority 3: Track the ball(s)
        # Find the most threatening ball (lowest one moving downward)
        threatening_ball = None
        lowest_y = -1

        for ball in game.balls:
            if ball['launched'] and ball['dy'] > 0:  # Moving down
                if ball['y'] > lowest_y:
                    lowest_y = ball['y']
                    threatening_ball = ball

        # If no ball is moving down, track any launched ball
        if threatening_ball is None:
            for ball in game.balls:
                if ball['launched']:
                    threatening_ball = ball
                    break

        if threatening_ball is None:
            return None  # No balls to track

        ball = threatening_ball

        # Predict where ball will hit paddle level
        if ball['dy'] > 0:  # Ball moving down
            # Calculate time to reach paddle
            if ball['dy'] == 0:
                return None
            time_to_paddle = (game.paddle_y - ball['y']) / ball['dy']
            # Predict x position
            predicted_x = ball['x'] + ball['dx'] * time_to_paddle

            # Account for wall bounces
            iterations = 0
            while (predicted_x < PLAY_LEFT or predicted_x > PLAY_RIGHT - 2) and iterations < 10:
                if predicted_x < PLAY_LEFT:
                    predicted_x = 2 * PLAY_LEFT - predicted_x  # Bounce off left wall
                if predicted_x > PLAY_RIGHT - 2:
                    predicted_x = 2 * (PLAY_RIGHT - 2) - predicted_x  # Bounce off right wall
                iterations += 1
        else:
            # Ball going up, move toward center or track ball's x
            predicted_x = ball['x']

        # Move paddle center toward predicted position
        paddle_center = game.paddle_x + game.paddle_width / 2

        if abs(paddle_center - predicted_x) < 2:
            return None  # Close enough
        elif paddle_center < predicted_x:
            return 'right'
        else:
            return 'left'
