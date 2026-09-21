"""
Wolfram - Elementary Cellular Automata
======================================
Implementation of Stephen Wolfram's 1D elementary cellular automata.
Each row represents a generation, computed from the previous using
a 3-cell neighborhood rule. The 8 possible neighborhood patterns
map to outcomes determined by the rule number (0-255).

Notable rules:
  Rule 30  - Chaotic, used for random number generation
  Rule 90  - Sierpinski triangle pattern
  Rule 110 - Proven Turing complete
  Rule 184 - Traffic flow modeling

Controls:
  Left/Right - Cycle through all 256 rules
  Up/Down    - Cycle color palette
  Button     - Reseed pattern
"""

from . import Visual, Display, Colors, GRID_SIZE
import settings


class Wolfram(Visual):
    name = "WOLFRAM"
    description = "1D cellular automata"
    category = "automata"
    GUIDE = {
        'desc': '256 elementary 1D cellular automata, each defined by a single number. Rule 30 generates randomness; Rule 110 is Turing-complete.',
        'credit': 'Stephen Wolfram, 1983',
    }

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed = 1.2
        self.update_timer = 0.0
        self.update_interval = 0.05

        self.rule = settings.get('wolfram_rule', 30) % 256
        self.build_rule_table()

        self.overlay_timer = 2.5

        # Clean monochrome color palettes - single color, no age gradient
        self.palettes = [
            (0, 255, 0),      # Green (classic terminal)
            (255, 255, 255),  # White (pure)
            (0, 200, 255),    # Cyan
            (255, 180, 0),    # Amber
            (255, 100, 100),  # Soft red
            (180, 100, 255),  # Purple
        ]
        self.current_palette = 0
        self.cell_color = self.palettes[self.current_palette]

        # History buffer - stores GRID_SIZE rows of history
        # Each row is GRID_SIZE cells (0 or 1)
        self.history = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

        # Current generation (bottom row of display)
        self.current_gen = [0 for _ in range(GRID_SIZE)]
        self.blank_rows = 0

        self.init_pattern()

    def build_rule_table(self):
        """Build lookup table for the current rule.

        The rule number encodes 8 bits, each determining the output
        for one of the 8 possible 3-cell neighborhood patterns:
        111, 110, 101, 100, 011, 010, 001, 000
        """
        self.rule_table = {}
        for i in range(8):
            # i represents the 3-bit neighborhood pattern
            # Rule bit i determines output for pattern i
            pattern = (
                (i >> 2) & 1,  # left neighbor
                (i >> 1) & 1,  # center
                (i >> 0) & 1,  # right neighbor
            )
            # Get the corresponding bit from the rule number
            self.rule_table[pattern] = (self.rule >> i) & 1

    def init_pattern(self):
        """Initialize the automaton with starting pattern."""
        # Clear history
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                self.history[y][x] = 0

        # Initialize current generation - single cell in center
        self.current_gen = [0 for _ in range(GRID_SIZE)]
        self.current_gen[GRID_SIZE // 2] = 1

        # Copy to bottom of history
        for x in range(GRID_SIZE):
            self.history[GRID_SIZE - 1][x] = self.current_gen[x]

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.up_pressed:
            self.current_palette = (self.current_palette + 1) % len(self.palettes)
            self.cell_color = self.palettes[self.current_palette]
            consumed = True

        if input_state.down_pressed:
            self.current_palette = (self.current_palette - 1) % len(self.palettes)
            self.cell_color = self.palettes[self.current_palette]
            consumed = True

        if input_state.right_pressed:
            self.rule = (self.rule + 1) % 256
            self.build_rule_table()
            self._reset_current_gen()
            self.overlay_timer = 2.5
            settings.set('wolfram_rule', self.rule)
            consumed = True

        if input_state.left_pressed:
            self.rule = (self.rule - 1) % 256
            self.build_rule_table()
            self._reset_current_gen()
            self.overlay_timer = 2.5
            settings.set('wolfram_rule', self.rule)
            consumed = True

        if input_state.action_l or input_state.action_r:
            self.init_pattern()
            consumed = True

        return consumed

    def _reset_current_gen(self):
        """Reset just the current generation seed without clearing history."""
        self.current_gen = [0 for _ in range(GRID_SIZE)]
        # Always use single cell in center
        self.current_gen[GRID_SIZE // 2] = 1

    def update(self, dt: float):
        self.time += dt
        self.update_timer += dt * self.speed

        while self.update_timer >= self.update_interval:
            self.update_timer -= self.update_interval
            self.step_generation()

        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

    def step_generation(self):
        """Compute next generation and scroll display."""
        # Compute next generation from current
        next_gen = [0 for _ in range(GRID_SIZE)]

        for x in range(GRID_SIZE):
            # Get 3-cell neighborhood (wrap at edges)
            left = self.current_gen[(x - 1) % GRID_SIZE]
            center = self.current_gen[x]
            right = self.current_gen[(x + 1) % GRID_SIZE]

            # Look up result from rule table
            pattern = (left, center, right)
            next_gen[x] = self.rule_table[pattern]

        # Scroll history up (older generations move up)
        for y in range(GRID_SIZE - 1):
            for x in range(GRID_SIZE):
                self.history[y][x] = self.history[y + 1][x]

        # New generation goes at bottom
        for x in range(GRID_SIZE):
            self.history[GRID_SIZE - 1][x] = next_gen[x]

        self.current_gen = next_gen

        # Some rules wipe the row out (rule 90 cancels itself after 32 rows on a
        # 64-cell ring), which would leave the panel black for good. After a
        # short gap, plant the single cell again.
        if any(next_gen):
            self.blank_rows = 0
        else:
            self.blank_rows += 1
            if self.blank_rows >= 8:
                self.blank_rows = 0
                self._reset_current_gen()

    def draw(self):
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if self.history[y][x]:
                    # Cell is alive - use current color
                    self.display.set_pixel(x, y, self.cell_color)
                else:
                    self.display.set_pixel(x, y, (0, 0, 0))

        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            c = (int(255 * alpha), int(255 * alpha), int(255 * alpha))
            self.display.draw_text_small(2, 2, "RULE %d" % self.rule, c)
