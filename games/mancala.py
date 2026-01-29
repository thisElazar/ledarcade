"""
Mancala - Ancient Strategy Game
===============================
Sow seeds around the board and capture the most!

Controls:
  Left/Right - Select pit
  Space      - Sow seeds from selected pit
"""

from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


PLAYER_1 = 1  # Bottom row
PLAYER_2 = 2  # Top row


class Mancala(Game):
    name = "MANCALA"
    description = "Sow & Capture"
    category = "2_player"

    # Layout constants
    PIT_WIDTH = 8
    PIT_HEIGHT = 12
    STORE_WIDTH = 8
    BOARD_Y = 16

    # Colorful seed colors
    SEED_COLORS = [
        (255, 100, 100),  # Red
        (100, 255, 100),  # Green
        (100, 100, 255),  # Blue
        (255, 255, 100),  # Yellow
        (255, 100, 255),  # Magenta
        (100, 255, 255),  # Cyan
        (255, 180, 100),  # Orange
        (180, 100, 255),  # Purple
    ]

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0

        # Pits: indices 0-5 are player 1 (bottom, left to right)
        # indices 6-11 are player 2 (top, right to left from their view)
        # Initial 4 seeds per pit
        self.pits = [4] * 12

        # Stores (mancalas)
        self.store1 = 0  # Player 1's store (right side)
        self.store2 = 0  # Player 2's store (left side)

        self.current_player = PLAYER_1
        self.selected_pit = 0  # 0-5 for current player's pits

        # Animation state
        self.animating = False
        self.anim_seeds = 0
        self.anim_pos = 0
        self.anim_timer = 0

        self.winner = None
        self.input_cooldown = 0

    def get_player_pits(self, player: int) -> range:
        """Get pit indices for a player."""
        if player == PLAYER_1:
            return range(0, 6)
        else:
            return range(6, 12)

    def get_pit_screen_pos(self, pit_index: int) -> tuple:
        """Get screen position for a pit."""
        if pit_index < 6:
            # Player 1's pits (bottom row, left to right)
            x = self.STORE_WIDTH + 2 + pit_index * self.PIT_WIDTH
            y = self.BOARD_Y + self.PIT_HEIGHT + 2
        else:
            # Player 2's pits (top row, right to left visually)
            visual_index = 11 - pit_index
            x = self.STORE_WIDTH + 2 + visual_index * self.PIT_WIDTH
            y = self.BOARD_Y
        return x, y

    def sow_seeds(self, pit_index: int):
        """Sow seeds from the selected pit.

        Board layout (positions 0-13):
          [13=P2 Store]
        [11][10][9][8][7][6]  <- P2's pits (array indices 6-11, positions 7-12)
        [0] [1][2][3][4][5]   <- P1's pits (array indices 0-5, positions 0-5)
          [6=P1 Store]

        Seeds move counter-clockwise: 0->1->2->3->4->5->6(P1store)->7->8->9->10->11->12->13(P2store)->0...
        """
        seeds = self.pits[pit_index]
        if seeds == 0:
            return False

        self.pits[pit_index] = 0

        # Convert pit array index to position
        # P1 pits: array 0-5 = position 0-5
        # P2 pits: array 6-11 = position 7-12
        if pit_index < 6:
            current_pos = pit_index
        else:
            current_pos = pit_index + 1  # Shift by 1 to account for P1's store at position 6

        last_was_store = False
        landed_pit_idx = -1

        while seeds > 0:
            current_pos = (current_pos + 1) % 14

            # Skip opponent's store
            if self.current_player == PLAYER_1 and current_pos == 13:
                continue
            if self.current_player == PLAYER_2 and current_pos == 6:
                continue

            # Drop seed
            last_was_store = False
            if current_pos < 6:
                # P1's pits (positions 0-5 = array indices 0-5)
                self.pits[current_pos] += 1
                landed_pit_idx = current_pos
            elif current_pos == 6:
                # P1's store
                self.store1 += 1
                last_was_store = True
                landed_pit_idx = -1
            elif current_pos < 13:
                # P2's pits (positions 7-12 = array indices 6-11)
                arr_idx = current_pos - 1
                self.pits[arr_idx] += 1
                landed_pit_idx = arr_idx
            else:
                # P2's store (position 13)
                self.store2 += 1
                last_was_store = True
                landed_pit_idx = -1

            seeds -= 1

        # Check for extra turn (landed in own store)
        extra_turn = False
        if self.current_player == PLAYER_1 and current_pos == 6:
            extra_turn = True
        elif self.current_player == PLAYER_2 and current_pos == 13:
            extra_turn = True

        # Check for capture (landed in empty pit on own side)
        if not extra_turn and not last_was_store and landed_pit_idx >= 0:
            is_own_pit = False
            if self.current_player == PLAYER_1 and 0 <= landed_pit_idx <= 5:
                is_own_pit = True
            elif self.current_player == PLAYER_2 and 6 <= landed_pit_idx <= 11:
                is_own_pit = True

            if is_own_pit and self.pits[landed_pit_idx] == 1:  # Was empty, now has 1
                # Calculate opposite pit
                if landed_pit_idx < 6:
                    opposite = 11 - landed_pit_idx  # P1's pit 0 opposite to P2's pit 11, etc.
                else:
                    opposite = 11 - landed_pit_idx  # P2's pit 6 opposite to P1's pit 5, etc.

                if self.pits[opposite] > 0:
                    captured = self.pits[landed_pit_idx] + self.pits[opposite]
                    if self.current_player == PLAYER_1:
                        self.store1 += captured
                    else:
                        self.store2 += captured
                    self.pits[landed_pit_idx] = 0
                    self.pits[opposite] = 0

        # Switch player if no extra turn
        if not extra_turn:
            self.current_player = PLAYER_2 if self.current_player == PLAYER_1 else PLAYER_1
            self.selected_pit = 0

        # Check for game end
        self.check_game_end()

        return True

    def check_game_end(self):
        """Check if the game is over."""
        p1_empty = all(self.pits[i] == 0 for i in range(6))
        p2_empty = all(self.pits[i] == 0 for i in range(6, 12))

        if p1_empty or p2_empty:
            # Collect remaining seeds
            for i in range(6):
                self.store1 += self.pits[i]
                self.pits[i] = 0
            for i in range(6, 12):
                self.store2 += self.pits[i]
                self.pits[i] = 0

            # Determine winner
            if self.store1 > self.store2:
                self.winner = PLAYER_1
            elif self.store2 > self.store1:
                self.winner = PLAYER_2
            else:
                self.winner = 0  # Tie

            self.state = GameState.GAME_OVER

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        self.input_cooldown -= dt

        if self.input_cooldown <= 0:
            # Select pit
            if input_state.left:
                self.selected_pit = (self.selected_pit - 1) % 6
                self.input_cooldown = 0.15
            elif input_state.right:
                self.selected_pit = (self.selected_pit + 1) % 6
                self.input_cooldown = 0.15

            # Sow seeds
            if (input_state.action_l or input_state.action_r):
                pit_index = self.selected_pit if self.current_player == PLAYER_1 else self.selected_pit + 6
                if self.pits[pit_index] > 0:
                    self.sow_seeds(pit_index)
                self.input_cooldown = 0.3

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Draw board background
        self.display.draw_rect(0, self.BOARD_Y - 2, 64, 34, (60, 40, 20))

        # Draw stores
        self.draw_store(0, self.BOARD_Y, self.store2, PLAYER_2)  # Left store (P2)
        self.draw_store(56, self.BOARD_Y, self.store1, PLAYER_1)  # Right store (P1)

        # Draw pits
        for i in range(12):
            x, y = self.get_pit_screen_pos(i)
            is_selected = False
            if self.current_player == PLAYER_1 and i == self.selected_pit:
                is_selected = True
            elif self.current_player == PLAYER_2 and i == self.selected_pit + 6:
                is_selected = True
            self.draw_pit(x, y, self.pits[i], is_selected)

        # Draw HUD - both players use white for clarity
        p1_color = Colors.WHITE
        p2_color = Colors.WHITE

        if self.current_player == PLAYER_1:
            self.display.draw_text_small(2, 1, "P1", p1_color)
            # Arrow pointing to selected pit
            px, py = self.get_pit_screen_pos(self.selected_pit)
            self.display.set_pixel(px + 3, py - 2, Colors.YELLOW)
        else:
            self.display.draw_text_small(2, 1, "P2", p2_color)
            px, py = self.get_pit_screen_pos(self.selected_pit + 6)
            self.display.set_pixel(px + 3, py + self.PIT_HEIGHT + 1, Colors.YELLOW)

        # Scores
        self.display.draw_text_small(25, 1, f"{self.store2}", p2_color)
        self.display.draw_text_small(45, 1, f"{self.store1}", p1_color)

        # Draw turn indicator line
        if self.current_player == PLAYER_1:
            self.display.draw_line(8, 56, 55, 56, p1_color)
        else:
            self.display.draw_line(8, 10, 55, 10, p2_color)

        # Draw direction arrows (counter-clockwise flow)
        arrow_color = (80, 80, 80)

        # Bottom row arrow (P1 plays left to right) →
        self.display.set_pixel(30, 58, arrow_color)
        self.display.set_pixel(31, 58, arrow_color)
        self.display.set_pixel(32, 58, arrow_color)
        self.display.set_pixel(31, 57, arrow_color)  # Arrow head
        self.display.set_pixel(31, 59, arrow_color)

        # Top row arrow (plays right to left) ←
        self.display.set_pixel(30, 12, arrow_color)
        self.display.set_pixel(31, 12, arrow_color)
        self.display.set_pixel(32, 12, arrow_color)
        self.display.set_pixel(31, 11, arrow_color)  # Arrow head
        self.display.set_pixel(31, 13, arrow_color)

        # Right side arrow (going up to P2's side) ↑
        self.display.set_pixel(60, 30, arrow_color)
        self.display.set_pixel(60, 31, arrow_color)
        self.display.set_pixel(59, 31, arrow_color)
        self.display.set_pixel(61, 31, arrow_color)

        # Left side arrow (going down to P1's side) ↓
        self.display.set_pixel(3, 30, arrow_color)
        self.display.set_pixel(3, 31, arrow_color)
        self.display.set_pixel(2, 30, arrow_color)
        self.display.set_pixel(4, 30, arrow_color)

    def draw_store(self, x: int, y: int, seeds: int, player: int):
        """Draw a store (mancala)."""
        color = (80, 60, 40)
        self.display.draw_rect(x, y, self.STORE_WIDTH, self.PIT_HEIGHT * 2 + 4, color)

        # Draw seeds as dots
        self.draw_seeds(x + 1, y + 2, seeds, self.STORE_WIDTH - 2, self.PIT_HEIGHT * 2)

        # Player indicator on store - both use white
        player_color = Colors.WHITE
        # Highlight border if it's this player's turn
        if player == self.current_player:
            # Draw glowing border
            self.display.draw_line(x, y, x, y + self.PIT_HEIGHT * 2 + 3, player_color)
            self.display.draw_line(x + self.STORE_WIDTH - 1, y, x + self.STORE_WIDTH - 1, y + self.PIT_HEIGHT * 2 + 3, player_color)
        # Always show player label
        label = "P1" if player == PLAYER_1 else "P2"
        label_x = x + 1 if player == PLAYER_2 else x + 1
        self.display.draw_text_small(label_x, y + self.PIT_HEIGHT * 2 - 2, label, player_color)

    def draw_pit(self, x: int, y: int, seeds: int, selected: bool):
        """Draw a pit."""
        color = (100, 80, 50) if not selected else (150, 120, 70)
        self.display.draw_rect(x, y, self.PIT_WIDTH - 1, self.PIT_HEIGHT, color)

        # Draw seeds
        self.draw_seeds(x + 1, y + 1, seeds, self.PIT_WIDTH - 3, self.PIT_HEIGHT - 2)

        # Selection highlight
        if selected:
            self.display.set_pixel(x, y, Colors.YELLOW)
            self.display.set_pixel(x + self.PIT_WIDTH - 2, y, Colors.YELLOW)
            self.display.set_pixel(x, y + self.PIT_HEIGHT - 1, Colors.YELLOW)
            self.display.set_pixel(x + self.PIT_WIDTH - 2, y + self.PIT_HEIGHT - 1, Colors.YELLOW)

    def draw_seeds(self, x: int, y: int, count: int, width: int, height: int):
        """Draw seeds as 2x2 colored jewels, spread out for visibility."""
        if count == 0:
            return

        # Create a 2x3 grid of jewel positions (6 jewels visible, counter at 8+)
        # More spread out for better visibility
        positions = []
        # 2 columns, 3 rows with generous spacing
        col_spacing = max(3, width // 2)
        row_spacing = max(3, height // 3)
        for row in range(3):
            for col in range(2):
                px = x + col * col_spacing
                py = y + row * row_spacing
                positions.append((px, py))

        # Also add a 7th position in the middle if space allows
        if width >= 4 and height >= 8:
            positions.append((x + width // 2 - 1, y + height // 2 - 1))

        # Draw jewels for counts up to 7
        max_jewels = min(count, 7)
        for i in range(max_jewels):
            if i < len(positions):
                px, py = positions[i]
                seed_color = self.SEED_COLORS[i % len(self.SEED_COLORS)]
                self.display.set_pixel(px, py, seed_color)
                self.display.set_pixel(px + 1, py, seed_color)
                self.display.set_pixel(px, py + 1, seed_color)
                self.display.set_pixel(px + 1, py + 1, seed_color)

        # Show count only when 8 or more seeds
        if count >= 8:
            self.display.draw_text_small(x, y, str(count), Colors.WHITE)

    def draw_game_over(self):
        self.display.clear(Colors.BLACK)
        if self.winner == PLAYER_1:
            self.display.draw_text_small(2, 20, "P1 WINS!", Colors.WHITE)
        elif self.winner == PLAYER_2:
            self.display.draw_text_small(2, 20, "P2 WINS!", Colors.WHITE)
        else:
            self.display.draw_text_small(2, 20, "TIE!", Colors.YELLOW)

        self.display.draw_text_small(2, 35, f"P1:{self.store1} P2:{self.store2}", Colors.GRAY)
