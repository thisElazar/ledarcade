"""
Turing Machine - Universal Computation
=========================================
A visual Turing machine running real programs on a tape.
Watch the read/write head shuttle back and forth, writing symbols
and changing states -- the foundation of all computation.

Controls:
  Left/Right  - Speed
  Up/Down     - Cycle program
  Space       - Pause/Step
"""

import math
from . import Visual, Display, Colors, GRID_SIZE

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
BG_COLOR = (5, 5, 15)
BLANK_COLOR = (10, 10, 20)
SYM1_COLOR = (0, 200, 255)       # cyan
SYM2_COLOR = (255, 220, 0)       # yellow (3-symbol machines)
HEAD_COLOR = (255, 255, 255)     # bright white
HALT_FLASH = (255, 60, 60)

STATE_COLORS = {
    'A': (255, 60, 60),
    'B': (60, 220, 60),
    'C': (60, 100, 255),
    'D': (255, 220, 0),
    'E': (220, 80, 255),
    'HALT': (255, 255, 255),
}

SYMBOL_COLORS = [
    BLANK_COLOR,   # 0
    SYM1_COLOR,    # 1
    SYM2_COLOR,    # 2
]

# Direction constants
R = 1
L = -1

# ---------------------------------------------------------------------------
# Programs -- each is (name, description, states, initial_tape_fn)
#   states: dict of (state, symbol) -> (write_symbol, direction, new_state)
#   initial_tape_fn: callable returning (tape_dict, head_pos, start_state)
# ---------------------------------------------------------------------------

def _blank_tape():
    return ({}, 0, 'A')



PROGRAMS = [
    (
        "BINARY CTR",
        "Increments binary",
        {
            # State A: scanning right over 1s
            ('A', 0): (1, R, 'A'),   # write 1, keep going right
            ('A', 1): (0, L, 'B'),   # flip 1->0, carry left
            # State B: propagate carry
            ('B', 0): (1, R, 'A'),   # write 1 (carry absorbed), go back right
            ('B', 1): (0, L, 'B'),   # flip 1->0, keep carrying
        },
        _blank_tape,
    ),
    (
        "BB-3",
        "Busy Beaver 3: 6 ones, 14 steps",
        {
            ('A', 0): (1, R, 'B'),
            ('A', 1): (1, L, 'C'),
            ('B', 0): (1, L, 'A'),
            ('B', 1): (1, R, 'B'),
            ('C', 0): (1, L, 'B'),
            ('C', 1): (1, R, 'HALT'),
        },
        _blank_tape,
    ),
    (
        "BB-4",
        "Busy Beaver 4: 13 ones, 107 steps",
        {
            ('A', 0): (1, R, 'B'),
            ('A', 1): (1, L, 'B'),
            ('B', 0): (1, L, 'A'),
            ('B', 1): (0, L, 'C'),
            ('C', 0): (1, R, 'HALT'),
            ('C', 1): (1, L, 'D'),
            ('D', 0): (1, R, 'D'),
            ('D', 1): (0, R, 'A'),
        },
        _blank_tape,
    ),
    (
        "BB-5",
        "Busy Beaver 5: 47M steps!",
        {
            ('A', 0): (1, R, 'B'),
            ('A', 1): (1, L, 'C'),
            ('B', 0): (1, R, 'C'),
            ('B', 1): (1, R, 'B'),
            ('C', 0): (1, R, 'D'),
            ('C', 1): (0, L, 'E'),
            ('D', 0): (1, L, 'A'),
            ('D', 1): (1, L, 'D'),
            ('E', 0): (1, R, 'HALT'),
            ('E', 1): (0, L, 'A'),
        },
        _blank_tape,
    ),
    (
        "ADD",
        "Unary 3 + 4",
        {
            # Unary addition: 111 0 1111 → 1111111
            # Replace separator 0 with 1, erase last 1 of second number
            # A: scan right to find the separator
            ('A', 0): (1, R, 'B'),   # found separator, replace with 1
            ('A', 1): (1, R, 'A'),   # skip first number
            # B: scan right to end of second number
            ('B', 0): (0, L, 'C'),   # past end, back up
            ('B', 1): (1, R, 'B'),   # skip second number
            # C: erase the last 1 (compensates for added separator)
            ('C', 1): (0, L, 'D'),   # erase it
            ('C', 0): (0, R, 'HALT'),  # degenerate case
            # D: scan left back to start
            ('D', 0): (0, R, 'HALT'),  # reached left of result, done
            ('D', 1): (1, L, 'D'),     # scan left over result
        },
        {i: 1 for i in range(3)} | {3: 0} | {i: 1 for i in range(4, 8)},
    ),
]

# ---------------------------------------------------------------------------
# Tape window size
# ---------------------------------------------------------------------------
TAPE_WINDOW = GRID_SIZE  # 64 cells visible

# History waterfall dimensions
HISTORY_TOP = 18
HISTORY_BOTTOM = 45
HISTORY_ROWS = HISTORY_BOTTOM - HISTORY_TOP + 1  # 28 rows

# Close-up tape strip
TAPE_STRIP_Y = 48
TAPE_STRIP_H = 4

# Head indicator
HEAD_Y = 53

# State indicator
STATE_Y = 55
STATE_H = 3

# Speed settings
SPEED_MIN = 1
SPEED_MAX = 100
SPEED_DEFAULT = 1
STEP_INTERVAL = 0.03  # seconds between step batches


class TuringMachine(Visual):
    name = "TURING MACHINE"
    description = "Universal computation"
    category = "mechanics"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.program_index = 0
        self.speed = SPEED_DEFAULT
        self.paused = False
        self.step_timer = 0.0

        # Overlay
        self.overlay_timer = 0.0
        self.overlay_text = ""

        # Halt state
        self.halted = False
        self.halt_timer = 0.0

        self._load_program()

    def _load_program(self):
        """Load the current program and reset machine state."""
        name, desc, transitions, tape_fn = PROGRAMS[self.program_index]
        self.transitions = transitions
        tape_dict, head, state = tape_fn()

        # Tape: sparse dict, default 0
        self.tape = dict(tape_dict)
        self.head_pos = head
        self.state = state
        self.step_count = 0
        self.halted = False
        self.halt_timer = 0.0

        # Camera follows head
        self.camera_x = self.head_pos

        # History waterfall: ring buffer of tape snapshots
        # Each entry: (window_offset, [64 symbols], head_local_x, state)
        self.history = []

        # Record initial state
        self._record_history()

    def _tape_read(self, pos):
        return self.tape.get(pos, 0)

    def _tape_write(self, pos, sym):
        if sym == 0:
            self.tape.pop(pos, None)
        else:
            self.tape[pos] = sym

    def _get_window(self):
        """Get the 64-cell window centered on camera_x."""
        offset = self.camera_x - TAPE_WINDOW // 2
        cells = []
        for i in range(TAPE_WINDOW):
            cells.append(self._tape_read(offset + i))
        head_local = self.head_pos - offset
        return offset, cells, head_local

    def _record_history(self):
        """Snapshot current tape window into history."""
        offset, cells, head_local = self._get_window()
        self.history.append((offset, list(cells), head_local, self.state))
        # Keep only what we need for the waterfall
        if len(self.history) > HISTORY_ROWS:
            self.history = self.history[-HISTORY_ROWS:]

    def _step(self):
        """Execute one step of the Turing machine."""
        if self.halted:
            return False

        sym = self._tape_read(self.head_pos)
        key = (self.state, sym)

        if key not in self.transitions:
            # No transition: halt
            self.halted = True
            self.halt_timer = 0.0
            return False

        write_sym, direction, new_state = self.transitions[key]
        self._tape_write(self.head_pos, write_sym)
        self.head_pos += direction
        self.state = new_state
        self.step_count += 1

        if new_state == 'HALT':
            self.halted = True
            self.halt_timer = 0.0
            return False

        # Smoothly track the head
        self.camera_x = self.head_pos

        # Record snapshot
        self._record_history()
        return True

    def _show_overlay(self, text):
        self.overlay_text = text
        self.overlay_timer = 1.5

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Up/Down: cycle program
        if input_state.up_pressed:
            self.program_index = (self.program_index - 1) % len(PROGRAMS)
            self._load_program()
            self.paused = False
            self.speed = SPEED_DEFAULT
            self._show_overlay(PROGRAMS[self.program_index][0])
            consumed = True
        elif input_state.down_pressed:
            self.program_index = (self.program_index + 1) % len(PROGRAMS)
            self._load_program()
            self.paused = False
            self.speed = SPEED_DEFAULT
            self._show_overlay(PROGRAMS[self.program_index][0])
            consumed = True

        # Left/Right: speed (also unpauses)
        if input_state.left_pressed:
            if self.speed <= 5:
                self.speed = max(SPEED_MIN, self.speed - 1)
            elif self.speed <= 20:
                self.speed = max(5, self.speed - 5)
            else:
                self.speed = max(20, self.speed - 20)
            self.paused = False
            self._show_overlay(f"SPD {self.speed}")
            consumed = True
        elif input_state.right_pressed:
            if self.speed < 5:
                self.speed = min(5, self.speed + 1)
            elif self.speed < 20:
                self.speed = min(20, self.speed + 5)
            else:
                self.speed = min(SPEED_MAX, self.speed + 20)
            self.paused = False
            self._show_overlay(f"SPD {self.speed}")
            consumed = True

        # Action: pause/step
        if input_state.action_l or input_state.action_r:
            if self.halted:
                # Advance to next program
                self.program_index = (self.program_index + 1) % len(PROGRAMS)
                self._load_program()
                self.paused = False
                self._show_overlay(PROGRAMS[self.program_index][0])
            elif self.paused:
                # Single step
                self._step()
            else:
                # Pause
                self.paused = True
                self._show_overlay("PAUSED")
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt

        # Overlay fade
        if self.overlay_timer > 0:
            self.overlay_timer = max(0, self.overlay_timer - dt)

        # Halt auto-advance
        if self.halted:
            self.halt_timer += dt
            if self.halt_timer > 4.0:
                self.program_index = (self.program_index + 1) % len(PROGRAMS)
                self._load_program()
                self._show_overlay(PROGRAMS[self.program_index][0])
            return

        if self.paused:
            return

        # Step the machine
        self.step_timer += dt
        if self.step_timer >= STEP_INTERVAL:
            self.step_timer -= STEP_INTERVAL
            for _ in range(self.speed):
                if not self._step():
                    break

    def draw(self):
        d = self.display
        d.clear()

        # Fill background
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                d.set_pixel(x, y, BG_COLOR)

        prog_name = PROGRAMS[self.program_index][0]
        prog_desc = PROGRAMS[self.program_index][1]

        # --- Row 0-3: Program name and info ---
        d.draw_text_small(2, 0, prog_name, (200, 180, 80))

        # Step count
        if self.step_count < 10000:
            step_str = str(self.step_count)
        elif self.step_count < 1000000:
            step_str = f"{self.step_count // 1000}K"
        else:
            step_str = f"{self.step_count // 1000000}M"
        d.draw_text_small(2, 6, f"STEP {step_str}", (140, 140, 160))

        # --- Row 8-15: State transition table ---
        self._draw_transition_table(d)

        # --- Row 18-45: History waterfall ---
        self._draw_waterfall(d)

        # --- Row 47-51: Current tape close-up ---
        self._draw_tape_strip(d)

        # --- Row 53: Head indicator ---
        self._draw_head_indicator(d)

        # --- Row 55-57: State indicator ---
        self._draw_state_indicator(d)

        # --- Row 60-63: HUD ---
        state_color = STATE_COLORS.get(self.state, (180, 180, 180))
        d.draw_text_small(2, 60, f"Q:{self.state}", state_color)
        if self.paused and not self.halted:
            # Blink "PAUSE" indicator
            if int(self.time * 3) % 2 == 0:
                d.draw_text_small(34, 60, "PAUSE", (200, 200, 60))

        # --- Halt flash ---
        if self.halted:
            flash = min(1.0, self.halt_timer / 0.3)
            blink = int(self.time * 4) % 2 == 0 if self.halt_timer < 2.0 else True
            if blink:
                bright = int(255 * flash)
                d.draw_text_small(18, 28, "HALT!", (bright, bright, bright))
            # Show final count
            d.draw_text_small(2, 34, f"{self.step_count} STEPS", (180, 180, 200))
            # Count ones on tape
            ones = sum(1 for v in self.tape.values() if v == 1)
            d.draw_text_small(2, 40, f"{ones} ONES", SYM1_COLOR)

        # --- Overlay ---
        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            oc = int(220 * alpha)
            d.draw_text_small(2, 28, self.overlay_text, (oc, oc, oc))

    def _draw_transition_table(self, d):
        """Draw the state transition rules, highlighting the active one.

        For machines with many rules, we show a scrolling window of rules
        centered on the currently active rule.
        """
        table_y = 8
        max_visible = 2  # rows of rules that fit (y=8..16, 5px each)

        # Build ordered list of all rules
        all_rules = []
        states_used = sorted(set(s for s, _ in self.transitions.keys()))
        max_sym = max(s for _, s in self.transitions.keys()) + 1
        active_idx = 0
        current_sym = self._tape_read(self.head_pos)

        for st in states_used:
            for sym in range(max_sym):
                key = (st, sym)
                if key not in self.transitions:
                    continue
                write_sym, direction, new_state = self.transitions[key]
                is_active = (st == self.state and sym == current_sym
                             and not self.halted)
                if is_active:
                    active_idx = len(all_rules)
                all_rules.append((st, sym, write_sym, direction, new_state,
                                  is_active))

        # Scroll window so active rule is visible
        if len(all_rules) <= max_visible:
            start = 0
        else:
            start = max(0, min(active_idx - max_visible // 2,
                               len(all_rules) - max_visible))

        for row, idx in enumerate(range(start, min(start + max_visible,
                                                    len(all_rules)))):
            st, sym, write_sym, direction, new_state, is_active = all_rules[idx]
            dir_char = 'R' if direction == R else 'L'
            y = table_y + row * 5

            sc = STATE_COLORS.get(st, (180, 180, 180))

            if is_active:
                # Highlight background
                for hx in range(GRID_SIZE):
                    for hy in range(y, min(y + 4, GRID_SIZE)):
                        d.set_pixel(hx, hy, (30, 30, 50))

            rule_text = f"{st},{sym}>{write_sym},{dir_char},{new_state}"
            dim = 0.4 if not is_active else 1.0
            color = (int(sc[0] * dim), int(sc[1] * dim), int(sc[2] * dim))
            d.draw_text_small(2, y, rule_text, color)

    def _draw_waterfall(self, d):
        """Draw history waterfall -- tape snapshots stacked vertically."""
        if not self.history:
            return

        num_rows = len(self.history)
        # Map history entries to waterfall rows, most recent at bottom
        for i, (offset, cells, head_local, state) in enumerate(self.history):
            # Vertical position: stack from bottom of waterfall area up
            y = HISTORY_BOTTOM - (num_rows - 1 - i)
            if y < HISTORY_TOP:
                continue

            # Fade older rows
            age = num_rows - 1 - i  # 0 = newest
            fade = max(0.15, 1.0 - age / (HISTORY_ROWS * 1.2))

            for x in range(TAPE_WINDOW):
                sym = cells[x]
                if sym == 0:
                    # Very subtle background for blank cells
                    c = (int(8 * fade), int(8 * fade), int(15 * fade))
                else:
                    base = SYMBOL_COLORS[min(sym, len(SYMBOL_COLORS) - 1)]
                    c = (int(base[0] * fade),
                         int(base[1] * fade),
                         int(base[2] * fade))

                # Head position: draw bright dot
                if x == head_local and 0 <= head_local < TAPE_WINDOW:
                    sc = STATE_COLORS.get(state, (180, 180, 180))
                    c = (int(sc[0] * fade),
                         int(sc[1] * fade),
                         int(sc[2] * fade))

                d.set_pixel(x, y, c)

    def _draw_tape_strip(self, d):
        """Draw the close-up tape strip -- 64 cells, each colored by symbol."""
        offset, cells, head_local = self._get_window()

        for x in range(TAPE_WINDOW):
            sym = cells[x]
            color = SYMBOL_COLORS[min(sym, len(SYMBOL_COLORS) - 1)]

            # Brighten cell near head
            dist = abs(x - head_local)
            if dist < 3:
                glow = 1.0 - dist * 0.25
                color = (min(255, int(color[0] + 40 * glow)),
                         min(255, int(color[1] + 40 * glow)),
                         min(255, int(color[2] + 40 * glow)))

            for y in range(TAPE_STRIP_Y, TAPE_STRIP_Y + TAPE_STRIP_H):
                d.set_pixel(x, y, color)

        # Tape cell borders (subtle dark lines between cells every 8 pixels)
        for x in range(0, TAPE_WINDOW, 8):
            for y in range(TAPE_STRIP_Y, TAPE_STRIP_Y + TAPE_STRIP_H):
                c = d.get_pixel(x, y)
                if c:
                    d.set_pixel(x, y, (max(0, c[0] - 15),
                                       max(0, c[1] - 15),
                                       max(0, c[2] - 15)))

    def _draw_head_indicator(self, d):
        """Draw the head position as a bright marker below the tape."""
        _, _, head_local = self._get_window()

        if 0 <= head_local < TAPE_WINDOW:
            x = head_local
            sc = STATE_COLORS.get(self.state, HEAD_COLOR)

            # Small arrow/triangle pointing up
            d.set_pixel(x, HEAD_Y, sc)
            if x > 0:
                d.set_pixel(x - 1, HEAD_Y + 1, (sc[0] // 2, sc[1] // 2, sc[2] // 2))
            if x < TAPE_WINDOW - 1:
                d.set_pixel(x + 1, HEAD_Y + 1, (sc[0] // 2, sc[1] // 2, sc[2] // 2))

            # Pulsing glow
            pulse = 0.6 + 0.4 * (0.5 + 0.5 * math.sin(self.time * 6))
            glow_color = (int(sc[0] * pulse), int(sc[1] * pulse), int(sc[2] * pulse))
            d.set_pixel(x, HEAD_Y, glow_color)

    def _draw_state_indicator(self, d):
        """Draw colored blocks showing current state."""
        # Draw all states as small blocks, highlight current
        states_used = sorted(set(s for s, _ in self.transitions.keys()))

        block_w = 3
        gap = 1
        total_w = len(states_used) * (block_w + gap)
        start_x = max(2, (GRID_SIZE - total_w) // 2)

        for i, st in enumerate(states_used):
            x0 = start_x + i * (block_w + gap)
            sc = STATE_COLORS.get(st, (180, 180, 180))
            is_current = (st == self.state and not self.halted)

            for dx in range(block_w):
                for dy in range(STATE_H):
                    px = x0 + dx
                    py = STATE_Y + dy
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        if is_current:
                            d.set_pixel(px, py, sc)
                        else:
                            # Dim
                            d.set_pixel(px, py,
                                        (sc[0] // 5, sc[1] // 5, sc[2] // 5))

        # If halted, show HALT block
        if self.halted:
            hc = STATE_COLORS['HALT']
            blink = int(self.time * 3) % 2 == 0
            if blink:
                hx = start_x + len(states_used) * (block_w + gap)
                for dx in range(block_w):
                    for dy in range(STATE_H):
                        px = hx + dx
                        py = STATE_Y + dy
                        if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                            d.set_pixel(px, py, hc)
