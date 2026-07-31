"""
Simon - Classic Memory Toy
===========================
The classic 1978 Milton Bradley memory game.
Watch the sequence of colors, then repeat it back.
Each round adds one more to the sequence.
Reach the selected goal length to win.

Controls:
  Up    - Green (top)
  Right - Red (right)
  Down  - Blue (bottom)
  Left  - Yellow (left)
  Left/Right (idle) - Set goal (8/14/20/31)
  Space - Start game
"""

import random
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


class Simon(Game):
    name = "SAIMON"
    description = "1978 Milton Bradley"
    category = "toys"
    GUIDE = {
        'desc': 'Four colored quadrants flash in sequence - each color has its own flash signature. Repeat the pattern, but hesitate more than 3 seconds and you lose. Left/Right at idle picks the goal (8/14/20/31 signals); reach it for the victory salute. Playback tempo lurches faster at 6 and 14 signals, just like the original.',
    }

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
    PHASE_FAIL = 6         # Wrong input (or timeout)
    PHASE_WIN = 7          # Reached the goal — victory salute

    # Selectable goal lengths (the original's skill levels 1-4)
    GOALS = [8, 14, 20, 31]

    # Seconds the player has to make each press
    PLAYER_TIMEOUT = 3.0

    def __init__(self, display: Display):
        super().__init__(display)
        self.high_score = 0
        self.goal_idx = 0
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
        self.lit_time = 0.0
        self.lit_duration = 0.5
        self.show_speed = 0.5
        self.input_cooldown = 0
        self.fail_correct = None
        self.win_timer = 0.0
        self.win_color = 'green'

    @property
    def goal(self):
        return self.GOALS[self.goal_idx]

    def start_game(self):
        """Start a new game."""
        self.sequence = []
        self.score = 0
        self.add_to_sequence()

    def _speed_for_length(self, length):
        """Stepped playback tempo — the original's signature lurches."""
        if length <= 5:
            return 0.50
        elif length <= 13:
            return 0.32
        return 0.22

    def _set_lit(self, name, duration):
        """Light a button and start its flash signature clock."""
        self.lit_button = name
        self.lit_time = 0.0
        self.lit_duration = duration

    def add_to_sequence(self):
        """Add a random color and start showing the sequence."""
        colors = ['green', 'red', 'blue', 'yellow']
        self.sequence.append(random.choice(colors))
        self.show_speed = self._speed_for_length(len(self.sequence))
        self.show_index = 0
        self.phase = self.PHASE_SHOWING
        self.timer = self.show_speed
        self._set_lit(self.sequence[0], self.show_speed)

    def _fail(self, correct):
        """Enter the fail state, remembering the button that was correct."""
        self.phase = self.PHASE_FAIL
        self.timer = 2.0
        self.lit_button = None
        self.fail_correct = correct
        self.high_score = max(self.high_score, self.score)

    def update(self, input_state: InputState, dt: float):
        self.timer -= dt
        self.lit_time += dt
        if self.input_cooldown > 0:
            self.input_cooldown -= dt

        if self.phase == self.PHASE_IDLE:
            # Waiting to start — left/right selects the goal
            if input_state.left_pressed:
                self.goal_idx = (self.goal_idx - 1) % len(self.GOALS)
            elif input_state.right_pressed:
                self.goal_idx = (self.goal_idx + 1) % len(self.GOALS)
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
                    self.timer = self.PLAYER_TIMEOUT
                else:
                    # Show next in sequence
                    self.phase = self.PHASE_SHOWING
                    self._set_lit(self.sequence[self.show_index],
                                  self.show_speed)
                    self.timer = self.show_speed

        elif self.phase == self.PHASE_PLAYER:
            # Waiting for player input — hesitation is a loss
            if self.timer <= 0:
                self._fail(self.sequence[self.player_index])
                return

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
                    self.input_cooldown = 0.25

                    if pressed == self.sequence[self.player_index]:
                        # Correct!
                        self._set_lit(pressed, 0.2)
                        self.player_index += 1
                        self.phase = self.PHASE_PLAYER_LIT
                        self.timer = 0.2
                    else:
                        # Wrong!
                        self._fail(self.sequence[self.player_index])

        elif self.phase == self.PHASE_PLAYER_LIT:
            # Showing player's button press
            if self.timer <= 0:
                self.lit_button = None
                if self.player_index >= len(self.sequence):
                    # Completed the sequence!
                    self.score = len(self.sequence)
                    self.high_score = max(self.high_score, self.score)
                    if self.score >= self.goal:
                        # Reached the goal — victory salute
                        self.phase = self.PHASE_WIN
                        self.win_timer = 0.0
                        self.win_color = self.sequence[-1]
                    else:
                        self.phase = self.PHASE_SUCCESS
                        self.timer = 0.5
                else:
                    # Wait for next input
                    self.phase = self.PHASE_PLAYER
                    self.timer = self.PLAYER_TIMEOUT

        elif self.phase == self.PHASE_SUCCESS:
            # Brief celebration, then next round
            if self.timer <= 0:
                self.add_to_sequence()

        elif self.phase == self.PHASE_WIN:
            # Victory salute — six flashes at 0.2s cadence
            self.win_timer += dt
            if self.win_timer >= 2.4:
                self.state = GameState.WIN

        elif self.phase == self.PHASE_FAIL:
            # Game over display
            if self.timer <= 0:
                if input_state.action_l or input_state.action_r:
                    self.reset()

    def _lit_color(self, name):
        """Visual 'tone' — each color flashes with a distinct signature."""
        dim, lit = self.COLORS[name]
        frac = min(1.0, self.lit_time / max(0.05, self.lit_duration))
        if name == 'green':
            # Single steady pulse
            return lit
        if name == 'red':
            # Double-blink
            return lit if (frac < 0.4 or frac >= 0.55) else dim
        if name == 'blue':
            # Bright-to-dim sweep
            return tuple(int(d + (l - d) * (1.0 - frac))
                         for d, l in zip(dim, lit))
        # Yellow: rapid flicker
        return lit if int(self.lit_time * 16) % 2 == 0 else dim

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Victory salute flash state
        win_on = (self.phase == self.PHASE_WIN
                  and int(self.win_timer / 0.2) % 2 == 0)

        # Draw the four buttons
        for name, cx, cy in self.BUTTONS:
            dim, lit = self.COLORS[name]
            if self.phase == self.PHASE_WIN:
                # Flash the last color; at 31, flash all four
                flash = win_on and (self.goal == 31 or name == self.win_color)
                color = lit if flash else dim
            elif (self.phase == self.PHASE_FAIL and name == self.fail_correct
                    and self.timer > 0.8):
                # Briefly reveal the button that was correct
                color = (150, 150, 150)
            elif self.lit_button == name:
                color = self._lit_color(name)
            else:
                color = dim
            size = 20
            self.display.draw_rect(cx - size//2, cy - size//2, size, size, color)

        # Draw center circle (black)
        self.display.draw_rect(25, 25, 14, 14, Colors.BLACK)

        # Center text
        if self.phase == self.PHASE_IDLE:
            self.display.draw_text_small(24, 27, "GO", Colors.WHITE)
            goal_str = str(self.goal)
            x = 30 if len(goal_str) == 1 else 28
            self.display.draw_text_small(x, 33, goal_str, Colors.CYAN)
        elif self.phase == self.PHASE_FAIL:
            self.display.draw_text_small(27, 29, "X", Colors.RED)
        elif self.phase == self.PHASE_WIN:
            if self.goal == 31:
                self.display.draw_text_small(28, 29, "!!", Colors.YELLOW)
            else:
                self.display.draw_text_small(26, 29, "WIN", Colors.GREEN)
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
            self.display.draw_text_small(2, 57, "</>: GOAL", Colors.GRAY)
        elif self.phase == self.PHASE_FAIL:
            self.display.draw_text_small(2, 1, "GAME OVER", Colors.RED)
            self.display.draw_text_small(2, 57, f"SCORE:{self.score}", Colors.WHITE)
        elif self.phase == self.PHASE_WIN:
            self.display.draw_text_small(2, 1, "YOU WIN!", Colors.GREEN)
        elif self.phase in (self.PHASE_SHOWING, self.PHASE_BETWEEN):
            self.display.draw_text_small(2, 1, "WATCH...", Colors.CYAN)
        elif self.phase in (self.PHASE_PLAYER, self.PHASE_PLAYER_LIT):
            self.display.draw_text_small(2, 1, "YOUR TURN", Colors.GREEN)
            # Hesitation meter — remaining time to press
            if self.phase == self.PHASE_PLAYER:
                w = max(0, int(20 * self.timer / self.PLAYER_TIMEOUT))
                if w > 0:
                    color = Colors.GREEN if self.timer > 1.0 else Colors.RED
                    self.display.draw_rect(42, 2, w, 2, color)
        elif self.phase == self.PHASE_SUCCESS:
            self.display.draw_text_small(2, 1, "CORRECT!", Colors.GREEN)
