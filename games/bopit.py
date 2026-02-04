"""
Bop It - Classic Reaction Toy
==============================
The classic 1996 Hasbro reaction game.
Follow the commands as fast as you can!
Speed increases with each successful action.

Commands:
  BOP IT   - Press Space/Action
  TWIST IT - Press Left + Right together
  PULL IT  - Press Up + Down together
  FLICK IT - Tap Left or Right quickly twice
"""

import random
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


class BopIt(Game):
    name = "BOP IT"
    description = "Reaction toy game"
    category = "toys"

    # Commands
    CMD_BOP = 'BOP'
    CMD_TWIST = 'TWIST'
    CMD_PULL = 'PULL'

    # Phases
    PHASE_IDLE = 0
    PHASE_SHOW = 1
    PHASE_WAIT = 2
    PHASE_SUCCESS = 3
    PHASE_FAIL = 4

    # Colors
    CMD_COLORS = {
        'BOP': Colors.RED,
        'TWIST': Colors.YELLOW,
        'PULL': Colors.CYAN,
    }

    def __init__(self, display: Display):
        super().__init__(display)
        self.high_score = 0
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.phase = self.PHASE_IDLE
        self.score = 0
        self.command = None
        self.timer = 0
        self.time_limit = 2.0  # Time to respond
        self.speed_mult = 1.0

        # Input state tracking
        self.last_left = False
        self.last_right = False
        self.last_up = False
        self.last_down = False

    def start_game(self):
        """Start a new game."""
        self.score = 0
        self.time_limit = 2.0
        self.speed_mult = 1.0
        self.next_command()

    def next_command(self):
        """Show next command."""
        self.command = random.choice([self.CMD_BOP, self.CMD_TWIST, self.CMD_PULL])
        self.phase = self.PHASE_SHOW
        self.timer = 0.3  # Brief flash before countdown

    def success(self):
        """Player got it right."""
        self.score += 1
        self.high_score = max(self.high_score, self.score)
        self.phase = self.PHASE_SUCCESS
        self.timer = 0.3

        # Speed up
        self.speed_mult = min(2.5, self.speed_mult + 0.08)
        self.time_limit = max(0.6, 2.0 / self.speed_mult)

    def fail(self):
        """Player failed."""
        self.phase = self.PHASE_FAIL
        self.timer = 2.0

    def check_input(self, input_state: InputState):
        """Check if player performed the correct action."""
        # BOP - press action button
        if input_state.action_l or input_state.action_r:
            if self.command == self.CMD_BOP:
                self.success()
            else:
                self.fail()
            return True

        # TWIST - press left AND right together
        if input_state.left and input_state.right:
            if self.command == self.CMD_TWIST:
                self.success()
            else:
                self.fail()
            return True

        # PULL - press up AND down together
        if input_state.up and input_state.down:
            if self.command == self.CMD_PULL:
                self.success()
            else:
                self.fail()
            return True

        # Wrong single button press
        if input_state.left or input_state.right or input_state.up or input_state.down:
            # Give a tiny grace period for combo inputs
            pass

        return False

    def update(self, input_state: InputState, dt: float):
        self.timer -= dt

        if self.phase == self.PHASE_IDLE:
            if input_state.action_l or input_state.action_r:
                self.start_game()

        elif self.phase == self.PHASE_SHOW:
            if self.timer <= 0:
                self.phase = self.PHASE_WAIT
                self.timer = self.time_limit

        elif self.phase == self.PHASE_WAIT:
            # Check for correct input
            self.check_input(input_state)

            # Time's up?
            if self.timer <= 0:
                self.fail()

        elif self.phase == self.PHASE_SUCCESS:
            if self.timer <= 0:
                self.next_command()

        elif self.phase == self.PHASE_FAIL:
            if self.timer <= 0:
                self.phase = self.PHASE_IDLE

        # Track input state
        self.last_left = input_state.left
        self.last_right = input_state.right
        self.last_up = input_state.up
        self.last_down = input_state.down

    def draw(self):
        self.display.clear(Colors.BLACK)

        if self.phase == self.PHASE_IDLE:
            # Title screen
            self.display.draw_text_small(16, 20, "BOP IT!", Colors.RED)
            self.display.draw_text_small(8, 35, "BTN:START", Colors.GRAY)
            self.display.draw_text_small(2, 50, f"BEST:{self.high_score}", Colors.YELLOW)

        elif self.phase in (self.PHASE_SHOW, self.PHASE_WAIT):
            # Show command
            color = self.CMD_COLORS.get(self.command, Colors.WHITE)

            # Command text - big and centered
            cmd_text = f"{self.command}!"
            x = 32 - len(cmd_text) * 2
            self.display.draw_text_small(x, 25, cmd_text, color)

            # Instruction hint
            if self.command == self.CMD_BOP:
                hint = "BUTTON"
            elif self.command == self.CMD_TWIST:
                hint = "L + R"
            elif self.command == self.CMD_PULL:
                hint = "U + D"
            else:
                hint = ""
            hx = 32 - len(hint) * 2
            self.display.draw_text_small(hx, 38, hint, Colors.GRAY)

            # Timer bar
            if self.phase == self.PHASE_WAIT:
                bar_width = int(50 * (self.timer / self.time_limit))
                bar_color = Colors.GREEN if self.timer > self.time_limit * 0.3 else Colors.RED
                self.display.draw_rect(7, 52, bar_width, 4, bar_color)

            # Score
            self.display.draw_text_small(2, 2, f"SCORE:{self.score}", Colors.WHITE)

        elif self.phase == self.PHASE_SUCCESS:
            # Flash success
            self.display.draw_text_small(16, 28, "YEAH!", Colors.GREEN)
            self.display.draw_text_small(2, 2, f"SCORE:{self.score}", Colors.WHITE)

        elif self.phase == self.PHASE_FAIL:
            # Game over
            self.display.draw_text_small(20, 20, "GAME", Colors.RED)
            self.display.draw_text_small(20, 30, "OVER", Colors.RED)
            self.display.draw_text_small(12, 45, f"SCORE:{self.score}", Colors.WHITE)
            if self.score >= self.high_score:
                self.display.draw_text_small(8, 55, "NEW BEST!", Colors.YELLOW)
