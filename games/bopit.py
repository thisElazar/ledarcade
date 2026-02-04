"""
Bop It - Classic Reaction Toy
==============================
The classic 1996 Hasbro reaction game.
Follow the commands as fast as you can!
Speed increases with each successful action.

Commands:
  BOP IT   - Press Action button
  TWIST IT - Left then Right (or Right then Left)
  PULL IT  - Up then Down (or Down then Up)
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

        # Input state tracking for motion detection
        self.last_left = False
        self.last_right = False
        self.last_up = False
        self.last_down = False

        # Motion tracking - first direction of a twist/pull
        self.motion_start = None  # 'left', 'right', 'up', 'down'
        self.motion_timer = 0  # Time window to complete motion

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
            self.motion_start = None
            return True

        # Detect new direction presses (edge detection)
        left_pressed = input_state.left and not self.last_left
        right_pressed = input_state.right and not self.last_right
        up_pressed = input_state.up and not self.last_up
        down_pressed = input_state.down and not self.last_down

        # TWIST - left then right, or right then left
        if left_pressed or right_pressed:
            if self.motion_start in ('left', 'right') and self.motion_timer > 0:
                # Check if this completes a twist (opposite direction)
                if (self.motion_start == 'left' and right_pressed) or \
                   (self.motion_start == 'right' and left_pressed):
                    if self.command == self.CMD_TWIST:
                        self.success()
                    else:
                        self.fail()
                    self.motion_start = None
                    return True
            # Start a new horizontal motion
            self.motion_start = 'left' if left_pressed else 'right'
            self.motion_timer = 0.5  # 500ms to complete the motion

        # PULL - up then down, or down then up
        if up_pressed or down_pressed:
            if self.motion_start in ('up', 'down') and self.motion_timer > 0:
                # Check if this completes a pull (opposite direction)
                if (self.motion_start == 'up' and down_pressed) or \
                   (self.motion_start == 'down' and up_pressed):
                    if self.command == self.CMD_PULL:
                        self.success()
                    else:
                        self.fail()
                    self.motion_start = None
                    return True
            # Start a new vertical motion
            self.motion_start = 'up' if up_pressed else 'down'
            self.motion_timer = 0.5  # 500ms to complete the motion

        return False

    def update(self, input_state: InputState, dt: float):
        self.timer -= dt
        if self.motion_timer > 0:
            self.motion_timer -= dt

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
                hint = "L-R"
            elif self.command == self.CMD_PULL:
                hint = "U-D"
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
