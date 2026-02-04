"""
Rush Hour - Sliding Block Puzzle
================================
The classic 1970s sliding block puzzle by Nob Yoshigahara.
Get the red car (X) to the exit on the right!

Controls:
  Arrow Keys - Move cursor / Select vehicle
  Action     - Select vehicle, then direction to slide

Puzzle data from Michael Fogleman's Rush Hour database (MIT License)
https://github.com/fogleman/rush
"""

import random
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


class RushHour(Game):
    name = "RUSH HOUR"
    description = "Sliding block puzzle"
    category = "toys"

    # Board is 6x6, exit is on right side at row 2 (0-indexed)
    BOARD_SIZE = 6
    CELL_SIZE = 9
    GAP = 1
    BOARD_PIXELS = CELL_SIZE * BOARD_SIZE + GAP * (BOARD_SIZE + 1)  # 61
    BOARD_X = (GRID_SIZE - BOARD_PIXELS) // 2
    BOARD_Y = (GRID_SIZE - BOARD_PIXELS) // 2 + 4  # Offset for HUD

    EXIT_ROW = 2  # Red car must reach right edge at this row

    # Vehicle colors (A is always red car)
    VEHICLE_COLORS = {
        'A': Colors.RED,
        'B': (50, 150, 50),    # Green
        'C': (50, 50, 200),    # Blue
        'D': (200, 200, 50),   # Yellow
        'E': (200, 50, 200),   # Magenta
        'F': (50, 200, 200),   # Cyan
        'G': (200, 150, 50),   # Orange
        'H': (150, 50, 150),   # Purple
        'I': (100, 150, 100),  # Sage
        'J': (150, 100, 50),   # Brown
        'K': (100, 100, 200),  # Light blue
        'L': (200, 100, 100),  # Pink
        'M': (100, 200, 100),  # Light green
        'N': (150, 150, 50),   # Olive
        'O': (50, 150, 150),   # Teal
    }
    WALL_COLOR = (60, 60, 60)
    EMPTY_COLOR = (25, 25, 30)
    CURSOR_COLOR = Colors.WHITE
    EXIT_COLOR = (100, 50, 50)

    # Puzzles organized by difficulty (moves to solve)
    # Format: 36-char string, row-major order
    # 'o' = empty, 'x' = wall, 'A' = red car, B-O = other vehicles
    # Puzzles verified solvable, sorted by actual moves required
    # Data from Michael Fogleman's Rush Hour database (MIT License)
    # https://github.com/fogleman/rush
    PUZZLES = {
        'beginner': [  # 7-14 moves
            "ooHBBBooHCCJoAAIoJoooIDDooooooooxFFx",  # 7 moves
            "oBBBoooCCCooAAoGoooooGooDDEExooooooo",  # 8 moves
            "ooxCCoooooGoAAooGooDDEEooooFFooooooo",  # 9 moves
            "oooBBxooooFGAAooFGoooooooDDoEEoooooo",  # 9 moves
            "HBBBooHooJKoIAAJKoIoooooIxDDoxFFFGGo",  # 10 moves
            "oBBxooooFGoHAAFGoHooooooooxEEooooooo",  # 10 moves
            "ooCCoxoEEKLMxAAKLMIoJFFFIoJoooIGGHHH",  # 12 moves
            "ooxoxoooEoFoAAEoFoooDDDooooooooooooo",  # 12 moves
            "ooxCCCDDoIJoAAoIJoHEEEJoHoooooxooGGo",  # 13 moves
            "GBBBoKGoCCoKAAIJoKooIJDDHoooooHEEFFo",  # 14 moves
        ],
        'easy': [  # 16-22 moves
            "xCCoJKooIoJKAAIooKoHDDoooHEEEooHFFGG",  # 16 moves
            "oooIBBCCoIKLHoAAKLHDDDxLoooJooFFoJGG",  # 17 moves
            "ooooxLxDDoKLAAJoKLoIJEEoHIooooHIFFGG",  # 17 moves
            "oxCCCJooooIJAAoHIJDDDHIoGEEEooGoFFFo",  # 19 moves
            "ooBBCCoDDDxKoAAIJKooHIJxooHIGGoooooo",  # 19 moves
            "oBBCCCxooLEEAAoLooKooFFFKxHHoMIIIJJM",  # 21 moves
            "HIooooHIBBCCAAoJKLDDoJKLooEExoooGGoo",  # 21 moves
            "oHBBBooHJoooAAJoKoCCJoKoGIDDDoGIEEFF",  # 22 moves
            "HBBBoMHCCCoMHAALoMIJKLDDIJKoooxJFFGG",  # 22 moves
            "HoIBBxHoIJooHAAJooDDoxoKoooooKFFFGGK",  # 22 moves
        ],
        'medium': [  # 27-31 moves
            "GHoJBBGHIJoKoHIAAKooxooxEEEoooFFFooo",  # 27 moves
            "oooHIJBBBHIJoAAoIoooGoooxoGDDxoooFFo",  # 27 moves
            "BBCCCLDDDoKLAAooKMJEEFFMJooGGMJHHoII",  # 27 moves
            "BBCCMNHDDoMNHJKAANIJKLEEIJoLooIFFGGo",  # 28 moves
            "ooooooooxHIoAAGHIoCCGoJoFDDoJoFEEooo",  # 28 moves
            "oxoCCCooxoLooAAKLooEEKFFooJGGMHHJIIM",  # 29 moves
            "oHBBLMGHoKLMGAAKooCCJKoooIJDDooIEEFF",  # 29 moves
            "JBBBoxJoLDDDAALooNKEEFFNKGGMooHHoMox",  # 30 moves
            "oooBBoCCCxKLAAoJKLGEEJKLGHIoooGHIFFo",  # 31 moves
            "ooJoBBCCJoLMHIAALMHIDDDMoooKooxxoKGG",  # 31 moves
        ],
        'hard': [  # 41-43 moves
            "BBoxLoooxoLMAAJoLMooJEEMIFFKooIGGKHH",  # 41 moves
            "ooBBCCooxoxLAAJooLFFJoKMoIGGKMoIHHHM",  # 41 moves
            "oooxooxooJDDHAAJKLHoEEKLooIFFFGGIooo",  # 41 moves
            "xJCCCMIJDDLMIAAoLNEEKoLNooKFFFxHHooo",  # 41 moves
            "HIBBLNHIJoLNAAJoMooCCCMoDDoKoxoxoKGG",  # 42 moves
            "HoJBBMHoJoLMHAAoLMoICCxooIoKEEFFFKGG",  # 42 moves
            "oooIxoCCCIJoAAoIJoGoDDJoGoHEEoFFHooo",  # 42 moves
            "oIBBLMHIoKLMHAAKoNCCDDoNooJxoooxJGGG",  # 42 moves
            "HxoCCoHJooMxIJAAMNIEELoNIoKLFFGGKooo",  # 43 moves
            "oIxooooIJoCCAAJooLHDDEELHFFKoLGGGKoo",  # 43 moves
        ],
        'expert': [  # 56-61 moves
            "BBoLoMCCCLoMAAoooNJoDDxNJxKGGGHHKoII",  # 56 moves
            "GoJBBBGoJKoLHAAKoLHCCDDLoIEEooxIoooo",  # 56 moves
            "ooHxooooHICCoAAIoooGDDJooGooJKEEFFJK",  # 56 moves
            "oHoBBooHoxKLAAoJKLGDDJoLGoIEEoGoIFFF",  # 57 moves
            "BBBJoooooJxoAAoKLoHDDKLoHoIEEoFFIGGG",  # 57 moves
            "HooJBBHCCJoLooIAALooIKDDEEEKoooxGGGo",  # 57 moves
            "oBBoxKooIDDKAAIJoKHEEJooHooJFFHGGGoo",  # 58 moves
            "HoBBxoHooJoMAAIJoMDDIKEEFFFKLooGGGLo",  # 58 moves
            "oBBoxoooIJoxAAIJooooIKEEHFFKoLHGGGoL",  # 59 moves
            "BBBKxoooJKDDAAJKLooxFFLoIoGGooIooHHo",  # 61 moves
        ],
    }

    DIFFICULTY_ORDER = ['beginner', 'easy', 'medium', 'hard', 'expert']
    DIFFICULTY_COLORS = {
        'beginner': Colors.GREEN,
        'easy': Colors.CYAN,
        'medium': Colors.YELLOW,
        'hard': (255, 150, 50),
        'expert': Colors.RED,
    }

    def __init__(self, display: Display):
        super().__init__(display)
        self.best_moves = {}  # (difficulty, level) -> best moves
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.phase = 'select'  # 'select' level, 'playing', 'won'
        self.difficulty_idx = 0
        self.level_idx = 0
        self.board = None
        self.vehicles = {}
        self.selected = None
        self.cursor = [2, 2]  # Default to exit row
        self.moves = 0
        self.input_cooldown = 0

    def load_puzzle(self, puzzle_str):
        """Load a puzzle from the 36-character string format."""
        self.board = [[None for _ in range(6)] for _ in range(6)]
        self.vehicles = {}

        for i, char in enumerate(puzzle_str):
            row, col = i // 6, i % 6
            if char == 'o':
                continue  # Empty
            elif char == 'x':
                self.board[row][col] = 'x'  # Wall
            else:
                self.board[row][col] = char
                if char not in self.vehicles:
                    self.vehicles[char] = []
                self.vehicles[char].append((row, col))

        # Determine vehicle orientations
        self.vehicle_info = {}
        for v, cells in self.vehicles.items():
            cells.sort()
            if len(cells) >= 2:
                if cells[0][0] == cells[1][0]:
                    orientation = 'H'
                else:
                    orientation = 'V'
            else:
                orientation = 'H'  # Single cell, assume horizontal
            self.vehicle_info[v] = {
                'cells': cells,
                'orientation': orientation,
                'length': len(cells),
            }

        self.moves = 0
        self.selected = None
        # Start cursor on red car
        if 'A' in self.vehicles:
            self.cursor = list(self.vehicles['A'][0])

    def can_move(self, vehicle, direction):
        """Check if vehicle can move in direction (-1 or +1)."""
        info = self.vehicle_info[vehicle]
        cells = info['cells']
        orientation = info['orientation']

        if orientation == 'H':
            # Horizontal vehicle moves left/right
            row = cells[0][0]
            if direction < 0:
                new_col = cells[0][1] - 1
            else:
                new_col = cells[-1][1] + 1

            if new_col < 0 or new_col >= 6:
                # Check for exit (only red car at exit row)
                if vehicle == 'A' and row == self.EXIT_ROW and new_col >= 6:
                    return 'exit'
                return False
            if self.board[row][new_col] is not None:
                return False
        else:
            # Vertical vehicle moves up/down
            col = cells[0][1]
            if direction < 0:
                new_row = cells[0][0] - 1
            else:
                new_row = cells[-1][0] + 1

            if new_row < 0 or new_row >= 6:
                return False
            if self.board[new_row][col] is not None:
                return False

        return True

    def move_vehicle(self, vehicle, direction):
        """Move vehicle one cell in direction."""
        info = self.vehicle_info[vehicle]
        cells = info['cells']
        orientation = info['orientation']

        # Clear old positions
        for r, c in cells:
            self.board[r][c] = None

        # Calculate new positions
        if orientation == 'H':
            new_cells = [(r, c + direction) for r, c in cells]
        else:
            new_cells = [(r + direction, c) for r, c in cells]

        # Set new positions
        for r, c in new_cells:
            self.board[r][c] = vehicle

        # Update vehicle info
        self.vehicle_info[vehicle]['cells'] = sorted(new_cells)
        self.vehicles[vehicle] = sorted(new_cells)

    def check_win(self):
        """Check if red car has reached the exit."""
        if 'A' not in self.vehicles:
            return False
        cells = self.vehicles['A']
        # Red car wins when rightmost cell is at column 5 (can exit)
        rightmost = max(c for r, c in cells)
        return rightmost == 5 and cells[0][0] == self.EXIT_ROW

    def start_level(self):
        """Start the current level."""
        diff = self.DIFFICULTY_ORDER[self.difficulty_idx]
        puzzle = self.PUZZLES[diff][self.level_idx]
        self.load_puzzle(puzzle)
        self.phase = 'playing'

    def update(self, input_state: InputState, dt: float):
        if self.input_cooldown > 0:
            self.input_cooldown -= dt

        if self.phase == 'select':
            self.update_select(input_state)
        elif self.phase == 'playing':
            self.update_playing(input_state)
        elif self.phase == 'won':
            self.update_won(input_state)

    def update_select(self, input_state: InputState):
        """Level selection screen."""
        if self.input_cooldown > 0:
            return

        if input_state.up:
            self.difficulty_idx = (self.difficulty_idx - 1) % len(self.DIFFICULTY_ORDER)
            self.level_idx = 0
            self.input_cooldown = 0.15
        elif input_state.down:
            self.difficulty_idx = (self.difficulty_idx + 1) % len(self.DIFFICULTY_ORDER)
            self.level_idx = 0
            self.input_cooldown = 0.15
        elif input_state.left:
            diff = self.DIFFICULTY_ORDER[self.difficulty_idx]
            max_level = len(self.PUZZLES[diff]) - 1
            self.level_idx = (self.level_idx - 1) % (max_level + 1)
            self.input_cooldown = 0.15
        elif input_state.right:
            diff = self.DIFFICULTY_ORDER[self.difficulty_idx]
            max_level = len(self.PUZZLES[diff]) - 1
            self.level_idx = (self.level_idx + 1) % (max_level + 1)
            self.input_cooldown = 0.15
        elif input_state.action_l or input_state.action_r:
            self.start_level()
            self.input_cooldown = 0.2

    def update_playing(self, input_state: InputState):
        """Main gameplay."""
        if self.input_cooldown > 0:
            return

        if self.selected:
            # Vehicle selected - try to move it
            info = self.vehicle_info[self.selected]
            moved = False

            if info['orientation'] == 'H':
                if input_state.left:
                    result = self.can_move(self.selected, -1)
                    if result:
                        self.move_vehicle(self.selected, -1)
                        moved = True
                elif input_state.right:
                    result = self.can_move(self.selected, 1)
                    if result == 'exit':
                        # Win!
                        self.move_vehicle(self.selected, 1)
                        self.moves += 1
                        self.phase = 'won'
                        self.record_best()
                        return
                    elif result:
                        self.move_vehicle(self.selected, 1)
                        moved = True
            else:  # Vertical
                if input_state.up:
                    if self.can_move(self.selected, -1):
                        self.move_vehicle(self.selected, -1)
                        moved = True
                elif input_state.down:
                    if self.can_move(self.selected, 1):
                        self.move_vehicle(self.selected, 1)
                        moved = True

            if moved:
                self.moves += 1
                self.input_cooldown = 0.1
                if self.check_win():
                    self.phase = 'won'
                    self.record_best()

            # Deselect with action or perpendicular movement
            if input_state.action_l or input_state.action_r:
                self.selected = None
                self.input_cooldown = 0.15

        else:
            # No selection - move cursor
            if input_state.up:
                self.cursor[0] = max(0, self.cursor[0] - 1)
                self.input_cooldown = 0.12
            elif input_state.down:
                self.cursor[0] = min(5, self.cursor[0] + 1)
                self.input_cooldown = 0.12
            elif input_state.left:
                self.cursor[1] = max(0, self.cursor[1] - 1)
                self.input_cooldown = 0.12
            elif input_state.right:
                self.cursor[1] = min(5, self.cursor[1] + 1)
                self.input_cooldown = 0.12
            elif input_state.action_l or input_state.action_r:
                # Try to select vehicle at cursor
                cell = self.board[self.cursor[0]][self.cursor[1]]
                if cell and cell != 'x':
                    self.selected = cell
                    self.input_cooldown = 0.15

    def update_won(self, input_state: InputState):
        """Win screen."""
        if self.input_cooldown > 0:
            return

        if input_state.action_l or input_state.action_r:
            # Next level or back to select
            diff = self.DIFFICULTY_ORDER[self.difficulty_idx]
            if self.level_idx < len(self.PUZZLES[diff]) - 1:
                self.level_idx += 1
                self.start_level()
            else:
                self.phase = 'select'
            self.input_cooldown = 0.2

    def record_best(self):
        """Record best moves for this level."""
        key = (self.difficulty_idx, self.level_idx)
        if key not in self.best_moves or self.moves < self.best_moves[key]:
            self.best_moves[key] = self.moves

    def draw(self):
        self.display.clear(Colors.BLACK)

        if self.phase == 'select':
            self.draw_select()
        elif self.phase == 'playing':
            self.draw_playing()
        elif self.phase == 'won':
            self.draw_won()

    def draw_select(self):
        """Draw level selection screen."""
        self.display.draw_text_small(8, 2, "RUSH HOUR", Colors.RED)

        y = 14
        for i, diff in enumerate(self.DIFFICULTY_ORDER):
            color = self.DIFFICULTY_COLORS[diff]
            if i == self.difficulty_idx:
                # Selected difficulty
                self.display.draw_text_small(2, y, ">", Colors.WHITE)
                self.display.draw_text_small(8, y, diff.upper()[:6], color)
                # Show level number
                self.display.draw_text_small(44, y, f"L{self.level_idx + 1}", Colors.WHITE)
            else:
                self.display.draw_text_small(8, y, diff.upper()[:6], (color[0]//2, color[1]//2, color[2]//2))
            y += 8

        # Show best for selected level
        key = (self.difficulty_idx, self.level_idx)
        if key in self.best_moves:
            self.display.draw_text_small(2, 56, f"BEST:{self.best_moves[key]}", Colors.YELLOW)

        self.display.draw_text_small(32, 56, "GO!", Colors.GREEN)

    def draw_playing(self):
        """Draw the game board."""
        # HUD
        diff = self.DIFFICULTY_ORDER[self.difficulty_idx]
        self.display.draw_text_small(2, 1, f"M:{self.moves}", Colors.WHITE)
        key = (self.difficulty_idx, self.level_idx)
        if key in self.best_moves:
            self.display.draw_text_small(32, 1, f"B:{self.best_moves[key]}", Colors.YELLOW)

        # Draw exit marker
        exit_y = self.BOARD_Y + self.GAP + self.EXIT_ROW * (self.CELL_SIZE + self.GAP)
        self.display.draw_rect(
            self.BOARD_X + self.BOARD_PIXELS - 1, exit_y,
            2, self.CELL_SIZE, self.EXIT_COLOR
        )

        # Draw board background
        self.display.draw_rect(
            self.BOARD_X, self.BOARD_Y,
            self.BOARD_PIXELS - 1, self.BOARD_PIXELS,
            self.EMPTY_COLOR
        )

        # Draw cells
        for row in range(6):
            for col in range(6):
                self.draw_cell(row, col)

        # Draw cursor
        if not self.selected:
            cx = self.BOARD_X + self.GAP + self.cursor[1] * (self.CELL_SIZE + self.GAP)
            cy = self.BOARD_Y + self.GAP + self.cursor[0] * (self.CELL_SIZE + self.GAP)
            # Draw cursor corners
            for dx, dy in [(-1, -1), (-1, self.CELL_SIZE), (self.CELL_SIZE, -1), (self.CELL_SIZE, self.CELL_SIZE)]:
                self.display.set_pixel(cx + dx, cy + dy, self.CURSOR_COLOR)

    def draw_cell(self, row, col):
        """Draw a single cell."""
        x = self.BOARD_X + self.GAP + col * (self.CELL_SIZE + self.GAP)
        y = self.BOARD_Y + self.GAP + row * (self.CELL_SIZE + self.GAP)

        cell = self.board[row][col]

        if cell is None:
            return  # Empty, already drawn as background
        elif cell == 'x':
            # Wall
            self.display.draw_rect(x, y, self.CELL_SIZE, self.CELL_SIZE, self.WALL_COLOR)
        else:
            # Vehicle
            color = self.VEHICLE_COLORS.get(cell, Colors.GRAY)

            # Highlight selected vehicle
            if cell == self.selected:
                color = (min(255, color[0] + 60), min(255, color[1] + 60), min(255, color[2] + 60))

            self.display.draw_rect(x, y, self.CELL_SIZE, self.CELL_SIZE, color)

            # Draw vehicle label (only on first cell)
            info = self.vehicle_info.get(cell)
            if info and (row, col) == info['cells'][0]:
                # Draw letter on first cell
                label = 'X' if cell == 'A' else cell
                tx = x + 2
                ty = y + 1
                self.display.draw_text_small(tx, ty, label, Colors.WHITE)

    def draw_won(self):
        """Draw win screen."""
        self.display.clear(Colors.BLACK)

        self.display.draw_text_small(12, 15, "SOLVED!", Colors.GREEN)
        self.display.draw_text_small(8, 28, f"MOVES:{self.moves}", Colors.WHITE)

        key = (self.difficulty_idx, self.level_idx)
        if key in self.best_moves and self.moves <= self.best_moves[key]:
            self.display.draw_text_small(8, 40, "NEW BEST!", Colors.YELLOW)

        diff = self.DIFFICULTY_ORDER[self.difficulty_idx]
        if self.level_idx < len(self.PUZZLES[diff]) - 1:
            self.display.draw_text_small(8, 52, "NEXT LVL", Colors.CYAN)
        else:
            self.display.draw_text_small(12, 52, "COMPLETE", Colors.MAGENTA)
