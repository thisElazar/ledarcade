"""
Simon - Classic Memory Toy
===========================
The classic 1978 Milton Bradley memory game.
Watch the sequence of colors, then repeat it back.
Each round adds one more to the sequence.

Controls:
  Up    - Green (top)
  Right - Red (right)
  Down  - Blue (bottom)
  Left  - Yellow (left)
  Space - Start game
"""

import random
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


class Simon(Game):
    name = "SAIMON"
    description = "1978 Milton Bradley"
    category = "toys"

    # Colors for the four buttons (dim and lit versions)
    COLORS = {
        'green':  ((20, 80, 20), (50, 255, 50)),
        'red':    ((80, 20, 20), (255, 50, 50)),
        'blue':   ((20, 20, 80), (50, 50, 255)),
        'yellow': ((80, 80, 20), (255, 255, 50)),
    }

    # Button positions (name, center_x, center_y)
    BUTTONS = [
        ('green', 32, 14),
        ('red', 50, 32),
        ('blue', 32, 50),
        ('yellow', 14, 32),
    ]

    # Game phases
    PHASE_IDLE = 0
    PHASE_SHOWING = 1      # Showing sequence to player
    PHASE_BETWEEN = 2      # Pause between sequence items
    PHASE_PLAYER = 3       # Player's turn
    PHASE_PLAYER_LIT = 4   # Player pressed, showing feedback
    PHASE_SUCCESS = 5      # Completed sequence, brief celebration
    PHASE_FAIL = 6         # Wrong input

    def __init__(self, display: Display):
        super().__init__(display)
        self.high_score = 0
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.phase = self.PHASE_IDLE
        self.sequence = []
        self.show_index = 0
        self.player_index = 0
        self.score = 0
        self.timer = 0
        self.lit_button = None
        self.show_speed = 0.5
        self.input_cooldown = 0

    def start_game(self):
        """Start a new game."""
        self.sequence = []
        self.score = 0
        self.show_speed = 0.5
        self.add_to_sequence()

    def add_to_sequence(self):
        """Add a random color and start showing the sequence."""
        colors = ['green', 'red', 'blue', 'yellow']
        self.sequence.append(random.choice(colors))
        self.show_index = 0
        self.phase = self.PHASE_SHOWING
        self.timer = self.show_speed
        self.lit_button = self.sequence[0]

    def update(self, input_state: InputState, dt: float):
        self.timer -= dt
        if self.input_cooldown > 0:
            self.input_cooldown -= dt

        if self.phase == self.PHASE_IDLE:
            # Waiting to start
            if input_state.action_l or input_state.action_r:
                self.start_game()

        elif self.phase == self.PHASE_SHOWING:
            # Showing a lit button
            if self.timer <= 0:
                self.lit_button = None
                self.phase = self.PHASE_BETWEEN
                self.timer = 0.2  # Pause between lights

        elif self.phase == self.PHASE_BETWEEN:
            # Pause between sequence items
            if self.timer <= 0:
                self.show_index += 1
                if self.show_index >= len(self.sequence):
                    # Done showing, player's turn
                    self.phase = self.PHASE_PLAYER
                    self.player_index = 0
                    self.lit_button = None
                else:
                    # Show next in sequence
                    self.phase = self.PHASE_SHOWING
                    self.lit_button = self.sequence[self.show_index]
                    self.timer = self.show_speed

        elif self.phase == self.PHASE_PLAYER:
            # Waiting for player input
            if self.input_cooldown <= 0:
                pressed = None
                if input_state.up:
                    pressed = 'green'
                elif input_state.right:
                    pressed = 'red'
                elif input_state.down:
                    pressed = 'blue'
                elif input_state.left:
                    pressed = 'yellow'

                if pressed:
                    self.lit_button = pressed
                    self.input_cooldown = 0.25

                    if pressed == self.sequence[self.player_index]:
                        # Correct!
                        self.player_index += 1
                        self.phase = self.PHASE_PLAYER_LIT
                        self.timer = 0.2
                    else:
                        # Wrong!
                        self.phase = self.PHASE_FAIL
                        self.timer = 2.0
                        self.high_score = max(self.high_score, self.score)

        elif self.phase == self.PHASE_PLAYER_LIT:
            # Showing player's button press
            if self.timer <= 0:
                self.lit_button = None
                if self.player_index >= len(self.sequence):
                    # Completed the sequence!
                    self.score = len(self.sequence)
                    self.high_score = max(self.high_score, self.score)
                    self.phase = self.PHASE_SUCCESS
                    self.timer = 0.5
                    # Speed up slightly
                    self.show_speed = max(0.2, self.show_speed - 0.03)
                else:
                    # Wait for next input
                    self.phase = self.PHASE_PLAYER

        elif self.phase == self.PHASE_SUCCESS:
            # Brief celebration, then next round
            if self.timer <= 0:
                self.add_to_sequence()

        elif self.phase == self.PHASE_FAIL:
            # Game over display
            if self.timer <= 0:
                if input_state.action_l or input_state.action_r:
                    self.reset()

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Draw the four buttons
        for name, cx, cy in self.BUTTONS:
            dim, lit = self.COLORS[name]
            color = lit if self.lit_button == name else dim
            size = 20
            self.display.draw_rect(cx - size//2, cy - size//2, size, size, color)

        # Draw center circle (black)
        self.display.draw_rect(25, 25, 14, 14, Colors.BLACK)

        # Center text
        if self.phase == self.PHASE_IDLE:
            self.display.draw_text_small(24, 29, "GO", Colors.WHITE)
        elif self.phase == self.PHASE_FAIL:
            self.display.draw_text_small(27, 29, "X", Colors.RED)
        elif self.phase in (self.PHASE_SHOWING, self.PHASE_BETWEEN):
            self.display.draw_text_small(26, 29, "?", Colors.GRAY)
        else:
            # Show current score/level
            score_str = str(len(self.sequence))
            x = 30 if len(score_str) == 1 else 27
            self.display.draw_text_small(x, 29, score_str, Colors.WHITE)

        # Status text at top
        if self.phase == self.PHASE_IDLE:
            self.display.draw_text_small(2, 1, f"BEST:{self.high_score}", Colors.YELLOW)
        elif self.phase == self.PHASE_FAIL:
            self.display.draw_text_small(2, 1, "GAME OVER", Colors.RED)
            self.display.draw_text_small(2, 57, f"SCORE:{self.score}", Colors.WHITE)
        elif self.phase in (self.PHASE_SHOWING, self.PHASE_BETWEEN):
            self.display.draw_text_small(2, 1, "WATCH...", Colors.CYAN)
        elif self.phase in (self.PHASE_PLAYER, self.PHASE_PLAYER_LIT):
            self.display.draw_text_small(2, 1, "YOUR TURN", Colors.GREEN)
        elif self.phase == self.PHASE_SUCCESS:
            self.display.draw_text_small(2, 1, "CORRECT!", Colors.GREEN)
