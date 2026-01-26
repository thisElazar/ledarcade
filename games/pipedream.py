"""
Pipe Dream - Puzzle Game
=========================
Build a pipe to carry the flow as far as possible!

Controls:
  Arrow Keys - Move cursor
  Space      - Place pipe piece
"""

from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE
import random
from enum import IntEnum


class PipeType(IntEnum):
    EMPTY = 0
    HORIZONTAL = 1   # --
    VERTICAL = 2     # |
    CORNER_NE = 3    # bottom-left to top (└)
    CORNER_NW = 4    # bottom-right to top (┘)
    CORNER_SE = 5    # top-left to bottom (┌)
    CORNER_SW = 6    # top-right to bottom (┐)
    CROSS = 7        # +
    START = 8        # Starting point


# Pipe connections: which directions each pipe connects
# Format: (connects_up, connects_down, connects_left, connects_right)
PIPE_CONNECTIONS = {
    PipeType.EMPTY: (False, False, False, False),
    PipeType.HORIZONTAL: (False, False, True, True),
    PipeType.VERTICAL: (True, True, False, False),
    PipeType.CORNER_NE: (True, False, True, False),   # └
    PipeType.CORNER_NW: (True, False, False, True),   # ┘
    PipeType.CORNER_SE: (False, True, True, False),   # ┌
    PipeType.CORNER_SW: (False, True, False, True),   # ┐
    PipeType.CROSS: (True, True, True, True),
    PipeType.START: (False, False, False, True),  # Flows right
}


class PipeDream(Game):
    name = "PIPE DREAM"
    description = "Build Pipes"
    category = "retro"

    # Grid layout
    GRID_CELLS = 6
    CELL_SIZE = 8
    BOARD_X = 2
    BOARD_Y = 10

    # Queue
    QUEUE_X = 52
    QUEUE_Y = 10
    QUEUE_SIZE = 5

    # Colors
    BOARD_BG = (40, 40, 50)
    PIPE_COLOR = (180, 180, 200)
    PIPE_BORDER = (100, 100, 120)
    FLOW_COLOR = (50, 200, 50)  # Green fluid
    CURSOR_COLOR = Colors.YELLOW
    START_COLOR = (200, 100, 50)

    # Timing
    START_DELAY = 12.0  # Seconds before flow starts
    FLOW_SPEED = 1.2    # Seconds per pipe segment

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0
        self.level = 1

        # Grid of pipe types
        self.grid = [[PipeType.EMPTY] * self.GRID_CELLS for _ in range(self.GRID_CELLS)]

        # Flow state: how full each cell is (0.0 to 1.0)
        self.flow = [[0.0] * self.GRID_CELLS for _ in range(self.GRID_CELLS)]

        # Place start pipe on left edge
        self.start_row = random.randint(1, self.GRID_CELLS - 2)
        self.grid[self.start_row][0] = PipeType.START
        self.flow[self.start_row][0] = 0.0

        # Current flow position and direction
        self.flow_col = 0
        self.flow_row = self.start_row
        self.flow_dir = 'right'  # Direction flow is traveling
        self.flow_progress = 0.0  # Progress through current pipe
        self.flowing = False
        self.flow_started = False

        # Pipe queue
        self.queue = [self.random_pipe() for _ in range(self.QUEUE_SIZE)]

        # Cursor
        self.cursor_x = 2
        self.cursor_y = self.start_row

        # Countdown timer
        self.countdown = self.START_DELAY
        self.pipes_filled = 0

        # Input timing
        self.move_timer = 0
        self.move_delay = 0.1
        self.last_direction = (0, 0)

    def random_pipe(self) -> PipeType:
        """Generate a random pipe piece."""
        # Weighted distribution - crosses are rarer
        pipes = [
            PipeType.HORIZONTAL,
            PipeType.VERTICAL,
            PipeType.CORNER_NE,
            PipeType.CORNER_NW,
            PipeType.CORNER_SE,
            PipeType.CORNER_SW,
        ]
        weights = [2, 2, 1, 1, 1, 1]

        # Add cross with low probability
        if random.random() < 0.15:
            return PipeType.CROSS

        total = sum(weights)
        r = random.random() * total
        for pipe, weight in zip(pipes, weights):
            r -= weight
            if r <= 0:
                return pipe
        return pipes[0]

    def place_pipe(self):
        """Place the current pipe at cursor position."""
        if self.grid[self.cursor_y][self.cursor_x] not in (PipeType.EMPTY, PipeType.START):
            # Can replace unfilled pipes (costs points)
            if self.flow[self.cursor_y][self.cursor_x] == 0:
                self.score = max(0, self.score - 5)
            else:
                return  # Can't replace filled pipe

        if self.grid[self.cursor_y][self.cursor_x] == PipeType.START:
            return  # Can't replace start

        # Place pipe
        self.grid[self.cursor_y][self.cursor_x] = self.queue[0]

        # Shift queue
        self.queue.pop(0)
        self.queue.append(self.random_pipe())

    def get_next_direction(self, pipe: PipeType, from_dir: str) -> str:
        """Get the exit direction when entering a pipe from a direction."""
        connections = PIPE_CONNECTIONS[pipe]
        up, down, left, right = connections

        # from_dir is where we came FROM, so we entered from opposite
        if from_dir == 'right':  # Entered from left
            if up:
                return 'up'
            if down:
                return 'down'
            if right:
                return 'right'
        elif from_dir == 'left':  # Entered from right
            if up:
                return 'up'
            if down:
                return 'down'
            if left:
                return 'left'
        elif from_dir == 'down':  # Entered from top
            if left:
                return 'left'
            if right:
                return 'right'
            if down:
                return 'down'
        elif from_dir == 'up':  # Entered from bottom
            if left:
                return 'left'
            if right:
                return 'right'
            if up:
                return 'up'

        return None  # Dead end

    def can_flow_into(self, col: int, row: int, from_dir: str) -> bool:
        """Check if flow can enter a cell from the given direction."""
        if not (0 <= col < self.GRID_CELLS and 0 <= row < self.GRID_CELLS):
            return False

        pipe = self.grid[row][col]
        if pipe == PipeType.EMPTY:
            return False

        connections = PIPE_CONNECTIONS[pipe]
        up, down, left, right = connections

        # Check if pipe accepts flow from this direction
        if from_dir == 'right':  # Flow coming from left
            return left
        elif from_dir == 'left':  # Flow coming from right
            return right
        elif from_dir == 'down':  # Flow coming from top
            return up
        elif from_dir == 'up':  # Flow coming from bottom
            return down

        return False

    def advance_flow(self, dt: float):
        """Advance the flow through pipes."""
        self.flow_progress += dt / self.FLOW_SPEED

        # Update current cell fill
        self.flow[self.flow_row][self.flow_col] = min(1.0, self.flow_progress)

        if self.flow_progress >= 1.0:
            # Current pipe filled
            self.pipes_filled += 1
            self.score += 10

            # Find next cell
            next_col, next_row = self.flow_col, self.flow_row
            if self.flow_dir == 'right':
                next_col += 1
            elif self.flow_dir == 'left':
                next_col -= 1
            elif self.flow_dir == 'up':
                next_row -= 1
            elif self.flow_dir == 'down':
                next_row += 1

            # Check if flow can continue
            if self.can_flow_into(next_col, next_row, self.flow_dir):
                self.flow_col = next_col
                self.flow_row = next_row
                self.flow_progress = 0.0

                # Determine new direction
                new_dir = self.get_next_direction(
                    self.grid[self.flow_row][self.flow_col],
                    self.flow_dir
                )
                if new_dir:
                    self.flow_dir = new_dir
                else:
                    self.game_over()
            else:
                self.game_over()

    def game_over(self):
        """End the game."""
        self.state = GameState.GAME_OVER
        # Bonus for pipes filled
        if self.pipes_filled >= 10:
            self.score += self.pipes_filled * 5

    def update(self, input_state: InputState, dt: float):
        if self.state == GameState.GAME_OVER:
            if input_state.action:
                self.reset()
            return

        # Countdown before flow starts
        if not self.flow_started:
            self.countdown -= dt
            if self.countdown <= 0:
                self.flow_started = True
                self.flowing = True
                self.flow_progress = 0.0

        # Advance flow
        if self.flowing:
            self.advance_flow(dt)

        # Cursor movement
        dx, dy = input_state.dx, input_state.dy

        if (dx, dy) != (0, 0):
            if (dx, dy) != self.last_direction:
                self.cursor_x = max(0, min(self.GRID_CELLS - 1, self.cursor_x + dx))
                self.cursor_y = max(0, min(self.GRID_CELLS - 1, self.cursor_y + dy))
                self.move_timer = 0
                self.last_direction = (dx, dy)
            else:
                self.move_timer += dt
                if self.move_timer >= self.move_delay:
                    self.cursor_x = max(0, min(self.GRID_CELLS - 1, self.cursor_x + dx))
                    self.cursor_y = max(0, min(self.GRID_CELLS - 1, self.cursor_y + dy))
                    self.move_timer = 0
        else:
            self.last_direction = (0, 0)
            self.move_timer = 0

        # Place pipe
        if input_state.action:
            self.place_pipe()

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Draw HUD
        self.draw_hud()

        # Draw board
        self.display.draw_rect(
            self.BOARD_X, self.BOARD_Y,
            self.GRID_CELLS * self.CELL_SIZE,
            self.GRID_CELLS * self.CELL_SIZE,
            self.BOARD_BG
        )

        # Draw pipes
        for row in range(self.GRID_CELLS):
            for col in range(self.GRID_CELLS):
                self.draw_cell(col, row)

        # Draw cursor
        self.draw_cursor()

        # Draw queue
        self.draw_queue()

        # Game over
        if self.state == GameState.GAME_OVER:
            self.draw_game_over()

    def draw_hud(self):
        """Draw score and countdown."""
        self.display.draw_text_small(1, 1, f"S:{self.score}", Colors.WHITE)

        if not self.flow_started:
            countdown_int = int(self.countdown) + 1
            color = Colors.RED if countdown_int <= 2 else Colors.YELLOW
            self.display.draw_text_small(28, 1, f"{countdown_int}", color)
        else:
            self.display.draw_text_small(28, 1, f"P:{self.pipes_filled}", Colors.GREEN)

    def draw_cell(self, col: int, row: int):
        """Draw a single cell with pipe."""
        x = self.BOARD_X + col * self.CELL_SIZE
        y = self.BOARD_Y + row * self.CELL_SIZE

        pipe = self.grid[row][col]
        fill = self.flow[row][col]

        if pipe == PipeType.EMPTY:
            return

        if pipe == PipeType.START:
            self.draw_start_pipe(x, y, fill)
        else:
            self.draw_pipe(x, y, pipe, fill)

    def draw_start_pipe(self, x: int, y: int, fill: float):
        """Draw the starting pipe."""
        # Draw arrow/start indicator
        cx = x + self.CELL_SIZE // 2
        cy = y + self.CELL_SIZE // 2

        self.display.draw_rect(x, cy - 1, self.CELL_SIZE, 3, self.START_COLOR)

        # Flow
        if fill > 0:
            flow_width = int(self.CELL_SIZE * fill)
            self.display.draw_rect(x, cy - 1, flow_width, 3, self.FLOW_COLOR)

    def draw_pipe(self, x: int, y: int, pipe: PipeType, fill: float):
        """Draw a pipe piece with optional flow."""
        cx = x + self.CELL_SIZE // 2
        cy = y + self.CELL_SIZE // 2
        half = self.CELL_SIZE // 2

        # Draw pipe shape
        if pipe == PipeType.HORIZONTAL:
            self.display.draw_rect(x, cy - 1, self.CELL_SIZE, 3, self.PIPE_COLOR)
            if fill > 0:
                fw = int(self.CELL_SIZE * fill)
                self.display.draw_rect(x, cy - 1, fw, 3, self.FLOW_COLOR)

        elif pipe == PipeType.VERTICAL:
            self.display.draw_rect(cx - 1, y, 3, self.CELL_SIZE, self.PIPE_COLOR)
            if fill > 0:
                fh = int(self.CELL_SIZE * fill)
                self.display.draw_rect(cx - 1, y, 3, fh, self.FLOW_COLOR)

        elif pipe == PipeType.CORNER_NE:  # └
            self.display.draw_rect(x, cy - 1, half + 2, 3, self.PIPE_COLOR)
            self.display.draw_rect(cx - 1, y, 3, half + 2, self.PIPE_COLOR)
            if fill > 0:
                if fill < 0.5:
                    fw = int(half * fill * 2)
                    self.display.draw_rect(x, cy - 1, fw, 3, self.FLOW_COLOR)
                else:
                    self.display.draw_rect(x, cy - 1, half + 1, 3, self.FLOW_COLOR)
                    fh = int(half * (fill - 0.5) * 2)
                    self.display.draw_rect(cx - 1, cy - fh, 3, fh + 1, self.FLOW_COLOR)

        elif pipe == PipeType.CORNER_NW:  # ┘
            self.display.draw_rect(cx - 1, cy - 1, half + 2, 3, self.PIPE_COLOR)
            self.display.draw_rect(cx - 1, y, 3, half + 2, self.PIPE_COLOR)
            if fill > 0:
                if fill < 0.5:
                    fw = int(half * fill * 2)
                    self.display.draw_rect(x + self.CELL_SIZE - fw, cy - 1, fw, 3, self.FLOW_COLOR)
                else:
                    self.display.draw_rect(cx - 1, cy - 1, half + 1, 3, self.FLOW_COLOR)
                    fh = int(half * (fill - 0.5) * 2)
                    self.display.draw_rect(cx - 1, cy - fh, 3, fh + 1, self.FLOW_COLOR)

        elif pipe == PipeType.CORNER_SE:  # ┌
            self.display.draw_rect(x, cy - 1, half + 2, 3, self.PIPE_COLOR)
            self.display.draw_rect(cx - 1, cy - 1, 3, half + 2, self.PIPE_COLOR)
            if fill > 0:
                if fill < 0.5:
                    fw = int(half * fill * 2)
                    self.display.draw_rect(x, cy - 1, fw, 3, self.FLOW_COLOR)
                else:
                    self.display.draw_rect(x, cy - 1, half + 1, 3, self.FLOW_COLOR)
                    fh = int(half * (fill - 0.5) * 2)
                    self.display.draw_rect(cx - 1, cy, 3, fh + 1, self.FLOW_COLOR)

        elif pipe == PipeType.CORNER_SW:  # ┐
            self.display.draw_rect(cx - 1, cy - 1, half + 2, 3, self.PIPE_COLOR)
            self.display.draw_rect(cx - 1, cy - 1, 3, half + 2, self.PIPE_COLOR)
            if fill > 0:
                if fill < 0.5:
                    fw = int(half * fill * 2)
                    self.display.draw_rect(x + self.CELL_SIZE - fw, cy - 1, fw, 3, self.FLOW_COLOR)
                else:
                    self.display.draw_rect(cx - 1, cy - 1, half + 1, 3, self.FLOW_COLOR)
                    fh = int(half * (fill - 0.5) * 2)
                    self.display.draw_rect(cx - 1, cy, 3, fh + 1, self.FLOW_COLOR)

        elif pipe == PipeType.CROSS:
            self.display.draw_rect(x, cy - 1, self.CELL_SIZE, 3, self.PIPE_COLOR)
            self.display.draw_rect(cx - 1, y, 3, self.CELL_SIZE, self.PIPE_COLOR)
            if fill > 0:
                # Cross fills from entry direction - simplified: just fill center
                self.display.draw_rect(cx - 1, cy - 1, 3, 3, self.FLOW_COLOR)

    def draw_cursor(self):
        """Draw cursor around selected cell."""
        x = self.BOARD_X + self.cursor_x * self.CELL_SIZE
        y = self.BOARD_Y + self.cursor_y * self.CELL_SIZE
        size = self.CELL_SIZE

        c = self.CURSOR_COLOR

        # Draw border
        self.display.draw_rect(x, y, size, 1, c)
        self.display.draw_rect(x, y + size - 1, size, 1, c)
        self.display.draw_rect(x, y, 1, size, c)
        self.display.draw_rect(x + size - 1, y, 1, size, c)

    def draw_queue(self):
        """Draw the pipe queue."""
        self.display.draw_text_small(self.QUEUE_X, self.BOARD_Y - 8, "NEXT", Colors.GRAY)

        for i, pipe in enumerate(self.queue):
            x = self.QUEUE_X
            y = self.BOARD_Y + i * 10

            # Highlight first pipe
            if i == 0:
                self.display.draw_rect(x - 1, y - 1, 10, 10, Colors.YELLOW)

            # Draw mini pipe
            self.draw_mini_pipe(x, y, pipe)

    def draw_mini_pipe(self, x: int, y: int, pipe: PipeType):
        """Draw a small pipe preview."""
        cx = x + 4
        cy = y + 4

        c = self.PIPE_COLOR

        if pipe == PipeType.HORIZONTAL:
            self.display.draw_rect(x + 1, cy, 6, 2, c)
        elif pipe == PipeType.VERTICAL:
            self.display.draw_rect(cx, y + 1, 2, 6, c)
        elif pipe == PipeType.CORNER_NE:
            self.display.draw_rect(x + 1, cy, 4, 2, c)
            self.display.draw_rect(cx, y + 1, 2, 4, c)
        elif pipe == PipeType.CORNER_NW:
            self.display.draw_rect(cx, cy, 4, 2, c)
            self.display.draw_rect(cx, y + 1, 2, 4, c)
        elif pipe == PipeType.CORNER_SE:
            self.display.draw_rect(x + 1, cy, 4, 2, c)
            self.display.draw_rect(cx, cy, 2, 4, c)
        elif pipe == PipeType.CORNER_SW:
            self.display.draw_rect(cx, cy, 4, 2, c)
            self.display.draw_rect(cx, cy, 2, 4, c)
        elif pipe == PipeType.CROSS:
            self.display.draw_rect(x + 1, cy, 6, 2, c)
            self.display.draw_rect(cx, y + 1, 2, 6, c)

    def draw_game_over(self):
        """Draw game over screen."""
        self.display.draw_text_small(8, 1, "GAME OVER", Colors.RED)
