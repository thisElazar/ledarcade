"""
Go - Ancient Strategy Board Game
================================
Surround territory and capture stones!

Controls:
  Arrow Keys - Move cursor
  Space      - Place stone
  Z          - Pass turn
"""

from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


BLACK = 1
WHITE = 2


class Go(Game):
    name = "GO"
    description = "9x9 Territory"
    category = "2_player"

    # Board layout
    BOARD_SIZE = 9
    CELL_SIZE = 6  # 6x6 per intersection = 54x54
    BOARD_OFFSET_X = 5
    BOARD_OFFSET_Y = 7

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0

        # Board: 0 = empty, BLACK = 1, WHITE = 2
        self.board = [[0] * self.BOARD_SIZE for _ in range(self.BOARD_SIZE)]

        self.current_player = BLACK
        self.cursor_x = 4
        self.cursor_y = 4

        # Captures
        self.black_captures = 0
        self.white_captures = 0

        # Pass tracking
        self.consecutive_passes = 0

        # Ko rule - prevent immediate recapture
        self.ko_point = None

        # Previous board state for ko detection
        self.previous_board = None

        self.winner = None
        self.input_cooldown = 0
        self.move_delay = 0.12

    def get_group(self, x: int, y: int) -> set:
        """Get all stones connected to the stone at (x, y)."""
        if self.board[y][x] == 0:
            return set()

        color = self.board[y][x]
        group = set()
        to_check = [(x, y)]

        while to_check:
            cx, cy = to_check.pop()
            if (cx, cy) in group:
                continue
            if not (0 <= cx < self.BOARD_SIZE and 0 <= cy < self.BOARD_SIZE):
                continue
            if self.board[cy][cx] != color:
                continue

            group.add((cx, cy))
            to_check.extend([(cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)])

        return group

    def get_liberties(self, group: set) -> set:
        """Get all liberties (empty adjacent points) of a group."""
        liberties = set()

        for x, y in group:
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.BOARD_SIZE and 0 <= ny < self.BOARD_SIZE:
                    if self.board[ny][nx] == 0:
                        liberties.add((nx, ny))

        return liberties

    def remove_group(self, group: set) -> int:
        """Remove a group from the board. Returns number of stones removed."""
        for x, y in group:
            self.board[y][x] = 0
        return len(group)

    def is_valid_move(self, x: int, y: int) -> bool:
        """Check if placing a stone at (x, y) is valid."""
        # Must be empty
        if self.board[y][x] != 0:
            return False

        # Ko rule
        if self.ko_point == (x, y):
            return False

        # Simulate the move
        original_board = [row[:] for row in self.board]
        self.board[y][x] = self.current_player

        # Check for captures first
        opponent = WHITE if self.current_player == BLACK else BLACK
        captured_any = False

        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.BOARD_SIZE and 0 <= ny < self.BOARD_SIZE:
                if self.board[ny][nx] == opponent:
                    adj_group = self.get_group(nx, ny)
                    if len(self.get_liberties(adj_group)) == 0:
                        captured_any = True

        # If no captures, check if own group has liberties (suicide rule)
        if not captured_any:
            own_group = self.get_group(x, y)
            if len(self.get_liberties(own_group)) == 0:
                # Suicide - not allowed
                self.board = original_board
                return False

        self.board = original_board
        return True

    def place_stone(self, x: int, y: int) -> bool:
        """Place a stone and handle captures."""
        if not self.is_valid_move(x, y):
            return False

        # Save board for ko detection
        self.previous_board = [row[:] for row in self.board]

        # Place stone
        self.board[y][x] = self.current_player

        # Check for captures
        opponent = WHITE if self.current_player == BLACK else BLACK
        total_captured = 0
        captured_point = None

        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.BOARD_SIZE and 0 <= ny < self.BOARD_SIZE:
                if self.board[ny][nx] == opponent:
                    adj_group = self.get_group(nx, ny)
                    if len(self.get_liberties(adj_group)) == 0:
                        captured = self.remove_group(adj_group)
                        total_captured += captured
                        if captured == 1:
                            captured_point = list(adj_group)[0]

        # Update captures
        if self.current_player == BLACK:
            self.black_captures += total_captured
        else:
            self.white_captures += total_captured

        # Set ko point if exactly one stone was captured
        if total_captured == 1 and captured_point:
            # Check if this creates a ko situation
            own_group = self.get_group(x, y)
            if len(own_group) == 1 and len(self.get_liberties(own_group)) == 1:
                self.ko_point = captured_point
            else:
                self.ko_point = None
        else:
            self.ko_point = None

        # Reset pass counter and switch player
        self.consecutive_passes = 0
        self.current_player = WHITE if self.current_player == BLACK else BLACK

        return True

    def pass_turn(self):
        """Pass the turn."""
        self.consecutive_passes += 1
        self.ko_point = None
        self.current_player = WHITE if self.current_player == BLACK else BLACK

        if self.consecutive_passes >= 2:
            self.end_game()

    def end_game(self):
        """End the game and calculate scores."""
        # Simple scoring: captures + territory (empty points surrounded)
        black_score = self.black_captures
        white_score = self.white_captures + 6.5  # Komi for white

        # Count territory (simplified - just count empty points with only one color adjacent)
        for y in range(self.BOARD_SIZE):
            for x in range(self.BOARD_SIZE):
                if self.board[y][x] == 0:
                    adjacent_colors = set()
                    for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.BOARD_SIZE and 0 <= ny < self.BOARD_SIZE:
                            if self.board[ny][nx] != 0:
                                adjacent_colors.add(self.board[ny][nx])

                    if adjacent_colors == {BLACK}:
                        black_score += 1
                    elif adjacent_colors == {WHITE}:
                        white_score += 1

        if black_score > white_score:
            self.winner = BLACK
        else:
            self.winner = WHITE

        self.black_score = black_score
        self.white_score = white_score
        self.state = GameState.GAME_OVER

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        self.input_cooldown -= dt

        if self.input_cooldown <= 0:
            moved = False

            if input_state.left:
                self.cursor_x = max(0, self.cursor_x - 1)
                moved = True
            elif input_state.right:
                self.cursor_x = min(self.BOARD_SIZE - 1, self.cursor_x + 1)
                moved = True
            elif input_state.up:
                self.cursor_y = max(0, self.cursor_y - 1)
                moved = True
            elif input_state.down:
                self.cursor_y = min(self.BOARD_SIZE - 1, self.cursor_y + 1)
                moved = True

            if moved:
                self.input_cooldown = self.move_delay

            # Place stone
            if input_state.action_l:
                if self.place_stone(self.cursor_x, self.cursor_y):
                    self.input_cooldown = 0.2

            # Pass turn
            if input_state.action_r:
                self.pass_turn()
                self.input_cooldown = 0.3

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Draw board background
        board_px = self.CELL_SIZE * (self.BOARD_SIZE - 1) + 4
        self.display.draw_rect(
            self.BOARD_OFFSET_X - 2,
            self.BOARD_OFFSET_Y - 2,
            board_px,
            board_px,
            (180, 150, 100)  # Wood color
        )

        # Draw grid lines
        for i in range(self.BOARD_SIZE):
            # Horizontal
            x1 = self.BOARD_OFFSET_X
            x2 = self.BOARD_OFFSET_X + (self.BOARD_SIZE - 1) * self.CELL_SIZE
            y = self.BOARD_OFFSET_Y + i * self.CELL_SIZE
            self.display.draw_line(x1, y, x2, y, (80, 60, 40))

            # Vertical
            y1 = self.BOARD_OFFSET_Y
            y2 = self.BOARD_OFFSET_Y + (self.BOARD_SIZE - 1) * self.CELL_SIZE
            x = self.BOARD_OFFSET_X + i * self.CELL_SIZE
            self.display.draw_line(x, y1, x, y2, (80, 60, 40))

        # Draw star points (hoshi)
        star_points = [(2, 2), (6, 2), (2, 6), (6, 6), (4, 4)]
        for sx, sy in star_points:
            px = self.BOARD_OFFSET_X + sx * self.CELL_SIZE
            py = self.BOARD_OFFSET_Y + sy * self.CELL_SIZE
            self.display.set_pixel(px, py, (60, 40, 20))

        # Draw stones
        for y in range(self.BOARD_SIZE):
            for x in range(self.BOARD_SIZE):
                if self.board[y][x] != 0:
                    self.draw_stone(x, y, self.board[y][x])

        # Draw cursor
        self.draw_cursor()

        # Draw HUD
        self.draw_hud()

    def draw_stone(self, x: int, y: int, color: int):
        """Draw a stone at board position."""
        px = self.BOARD_OFFSET_X + x * self.CELL_SIZE
        py = self.BOARD_OFFSET_Y + y * self.CELL_SIZE

        stone_color = (20, 20, 20) if color == BLACK else (240, 240, 240)
        highlight = (60, 60, 60) if color == BLACK else (255, 255, 255)

        # Draw 3x3 stone
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if abs(dx) + abs(dy) <= 1:  # Diamond shape
                    self.display.set_pixel(px + dx, py + dy, stone_color)

        # Highlight
        self.display.set_pixel(px - 1, py - 1, highlight)

    def draw_cursor(self):
        """Draw the cursor."""
        px = self.BOARD_OFFSET_X + self.cursor_x * self.CELL_SIZE
        py = self.BOARD_OFFSET_Y + self.cursor_y * self.CELL_SIZE

        cursor_color = Colors.CYAN

        # Draw cursor corners
        self.display.set_pixel(px - 2, py - 2, cursor_color)
        self.display.set_pixel(px + 2, py - 2, cursor_color)
        self.display.set_pixel(px - 2, py + 2, cursor_color)
        self.display.set_pixel(px + 2, py + 2, cursor_color)

        # Show valid move indicator
        if self.board[self.cursor_y][self.cursor_x] == 0:
            if self.is_valid_move(self.cursor_x, self.cursor_y):
                # Ghost stone
                ghost_color = (40, 40, 40) if self.current_player == BLACK else (200, 200, 200)
                self.display.set_pixel(px, py, ghost_color)

    def draw_hud(self):
        """Draw the heads-up display."""
        # Current player
        if self.current_player == BLACK:
            self.display.draw_text_small(1, 1, "B", Colors.WHITE)
            self.display.set_pixel(10, 2, (20, 20, 20))
        else:
            self.display.draw_text_small(1, 1, "W", Colors.WHITE)
            self.display.set_pixel(10, 2, (240, 240, 240))

        # Captures
        self.display.draw_text_small(45, 1, f"{self.black_captures}", Colors.WHITE)
        self.display.draw_text_small(55, 1, f"{self.white_captures}", Colors.GRAY)

        # Pass indicator
        if self.consecutive_passes > 0:
            self.display.draw_text_small(20, 1, "PASS", Colors.YELLOW)

    def draw_game_over(self):
        self.display.clear(Colors.BLACK)

        if self.winner == BLACK:
            self.display.draw_text_small(2, 18, "BLACK WINS", Colors.WHITE)
        else:
            self.display.draw_text_small(2, 18, "WHITE WINS", Colors.WHITE)

        self.display.draw_text_small(2, 32, f"B:{self.black_score:.1f}", Colors.WHITE)
        self.display.draw_text_small(32, 32, f"W:{self.white_score:.1f}", Colors.GRAY)

        self.display.draw_text_small(2, 50, "SPACE:RETRY", Colors.DARK_GRAY)
