"""
Life Lab - Set up a pattern and run it
=======================================
A bench for Conway's Life. Pick a famous seed, pick a rule, and set it
running. LIFE itself only ever shows a random soup; here you choose what
goes on the grid and watch that specific thing unfold — a glider gun firing
on schedule, the R-pentomino thrashing for a thousand generations, a
diehard vanishing exactly when it should.

The rule is any life-like B/S rulestring, so the same seed can be run under
Conway's B3/S23, HighLife's B36/S23 (which builds replicators), or Day &
Night, and you can watch the same pattern behave completely differently.

Controls:
  Left/Right - Cycle seed pattern
  Up/Down    - Cycle rule
  Action L   - Run / pause
  Action R   - Reseed the current pattern
  Both       - Commit rule + pattern to settings
"""

import random
from . import Visual, Display, GRID_SIZE
import settings

N = GRID_SIZE


# ── Seed patterns ────────────────────────────────────────────────────
# Plotted as strings so the shapes stay readable and checkable against the
# standard Life literature. 'O' is a live cell.

_PATTERNS = [
    ("GLIDER GUN", [
        "........................O...........",
        "......................O.O...........",
        "............OO......OO............OO",
        "...........O...O....OO............OO",
        "OO........O.....O...OO..............",
        "OO........O...O.OO....O.O...........",
        "..........O.....O.......O...........",
        "...........O...O....................",
        "............OO......................",
    ]),
    ("PULSAR", [
        "..OOO...OOO..",
        ".............",
        "O....O.O....O",
        "O....O.O....O",
        "O....O.O....O",
        "..OOO...OOO..",
        ".............",
        "..OOO...OOO..",
        "O....O.O....O",
        "O....O.O....O",
        "O....O.O....O",
        ".............",
        "..OOO...OOO..",
    ]),
    ("R-PENTOMINO", [
        ".OO",
        "OO.",
        ".O.",
    ]),
    ("ACORN", [
        ".O.....",
        "...O...",
        "OO..OOO",
    ]),
    ("DIEHARD", [
        "......O.",
        "OO......",
        ".O...OOO",
    ]),
    ("LWSS", [
        ".OOOO",
        "O...O",
        "....O",
        "O..O.",
    ]),
    ("BLOCKS", None),     # tiled still lifes, to show a rule's stable states
    ("SOUP", None),       # random fill, the classic
]

# ── Life-like rules (birth counts / survival counts) ────────────────
_RULES = [
    ("CONWAY", (3,), (2, 3)),
    ("HIGHLIFE", (3, 6), (2, 3)),
    ("DAY+NIGHT", (3, 6, 7, 8), (3, 4, 6, 7, 8)),
    ("MORLEY", (3, 6, 8), (2, 4, 5)),
    ("34 LIFE", (3, 4), (3, 4)),
    ("DIAMOEBA", (3, 5, 6, 7, 8), (5, 6, 7, 8)),
    ("SEEDS", (2,), ()),
]

_SPEEDS = [0.25, 0.14, 0.08, 0.04]     # seconds per generation

# Live cells run a slow hue drift; a cell born this generation flashes so
# growth fronts are visible at speed.
_BIRTH_COLOR = (255, 255, 235)


def _rulestring(birth, survive):
    return "B" + "".join(str(b) for b in birth) + "/S" + "".join(
        str(s) for s in survive)


class LifeLab(Visual):
    name = "LIFE LAB"
    description = "Explore Life seeds and rules"
    category = "automata"
    GUIDE = {
        'desc': 'A bench for Conway\'s Life. Load a famous seed — Gosper\'s glider gun, the R-pentomino, a diehard — choose a life-like rule, and set it running. The same seed under a different rule behaves nothing like itself.',
        'credit': 'John Conway, 1970',
        'legend': {
            'LWSS': 'Light-Weight Spaceship: a small pattern that glides steadily.',
            'G#': 'Generation count: simulation steps run since pattern was seeded.',
            'B#/S#': 'Life-like rulestring: B digits = birth, S digits = survival by neighbor count.',
        },
    }

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.step_timer = 0.0
        self.generation = 0

        self.pattern_idx = settings.get('life_lab_pattern', 0) % len(_PATTERNS)
        self.rule_idx = settings.get('life_lab_rule', 0) % len(_RULES)
        self.speed_idx = 1

        self.grid = [0] * (N * N)
        self.born = set()
        self.running = False

        self.overlay_timer = 2.5
        self.saved_timer = 0.0
        self.confirm_timer = 0.0
        self._both_held_prev = False

        # A seed can simply die under a given rule (the R-pentomino lasts
        # eight generations under HighLife); the bench moves on rather than
        # sitting on an empty grid that reads as a crash.
        self._extinct_timer = 0.0

        self._seed()

    # -- seeding ------------------------------------------------------

    def _seed(self):
        name, rows = _PATTERNS[self.pattern_idx]
        self.grid = [0] * (N * N)
        self.generation = 0
        self.born = set()
        self._extinct_timer = 0.0
        self.running = False

        if rows is not None:
            h = len(rows)
            w = max(len(r) for r in rows)
            y0 = (N - h) // 2
            x0 = (N - w) // 2
            for dy, row in enumerate(rows):
                for dx, ch in enumerate(row):
                    if ch == 'O':
                        self.grid[(y0 + dy) * N + (x0 + dx)] = 1
        elif name == "BLOCKS":
            for by in range(4, N - 4, 6):
                for bx in range(4, N - 4, 6):
                    self.grid[by * N + bx] = 1
                    self.grid[by * N + bx + 1] = 1
                    self.grid[(by + 1) * N + bx] = 1
                    self.grid[(by + 1) * N + bx + 1] = 1
        else:   # SOUP
            for i in range(N * N):
                self.grid[i] = 1 if random.random() < 0.32 else 0

    # -- rule ---------------------------------------------------------

    def _step(self):
        """One generation under the current rule.

        Neighbour counts come from per-row triple sums rather than eight
        wrapped lookups per cell: on a 64x64 grid that is ~4k additions a
        generation instead of ~33k index-and-modulo operations, which is the
        difference between this keeping up on a Pi and not.
        """
        grid = self.grid
        _, birth, survive = _RULES[self.rule_idx]

        # rowsum[y][x] = grid[y][x-1] + grid[y][x] + grid[y][x+1], wrapped.
        rowsum = []
        for y in range(N):
            base = y * N
            row = grid[base:base + N]
            rs = [0] * N
            for x in range(N):
                rs[x] = row[x - 1] + row[x] + row[(x + 1) % N]
            rowsum.append(rs)

        new = [0] * (N * N)
        born = set()
        for y in range(N):
            above = rowsum[y - 1]
            here = rowsum[y]
            below = rowsum[(y + 1) % N]
            base = y * N
            for x in range(N):
                alive = grid[base + x]
                n = above[x] + here[x] + below[x] - alive
                if alive:
                    if n in survive:
                        new[base + x] = 1
                elif n in birth:
                    new[base + x] = 1
                    born.add(base + x)

        self.grid = new
        self.born = born
        self.generation += 1

    def _check_extinct(self, dt):
        """Track how long the grid has been empty.

        Only *death* counts. A still life or an oscillator is a legitimate
        end state worth sitting on — BLOCKS under Conway is frozen on
        purpose — so nothing auto-advances just because the screen stopped
        changing. An empty grid is the one state with nothing left to show.
        """
        if sum(self.grid) == 0:
            self._extinct_timer += dt
        else:
            self._extinct_timer = 0.0

    # -- input --------------------------------------------------------

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.left_pressed:
            self.pattern_idx = (self.pattern_idx - 1) % len(_PATTERNS)
            self._seed()
            self.overlay_timer = 2.5
            consumed = True
        if input_state.right_pressed:
            self.pattern_idx = (self.pattern_idx + 1) % len(_PATTERNS)
            self._seed()
            self.overlay_timer = 2.5
            consumed = True
        if input_state.up_pressed:
            self.rule_idx = (self.rule_idx - 1) % len(_RULES)
            self._seed()
            self.overlay_timer = 2.5
            consumed = True
        if input_state.down_pressed:
            self.rule_idx = (self.rule_idx + 1) % len(_RULES)
            self._seed()
            self.overlay_timer = 2.5
            consumed = True

        both_held = input_state.action_l_held and input_state.action_r_held
        both_released = self._both_held_prev and not both_held

        if both_released:
            self.confirm_timer = 3.0
            consumed = True
        elif self.confirm_timer > 0 and not both_held:
            if input_state.action_r:
                settings.set('life_lab_pattern', self.pattern_idx)
                settings.set('life_lab_rule', self.rule_idx)
                self.saved_timer = 1.5
                self.confirm_timer = 0.0
                consumed = True
            elif input_state.action_l:
                self.confirm_timer = 0.0
                consumed = True
        elif not both_held:
            if input_state.action_l:
                self.running = not self.running
                self.overlay_timer = 1.5
                consumed = True
            elif input_state.action_r:
                self._seed()
                self.overlay_timer = 2.5
                consumed = True

        self._both_held_prev = both_held
        return consumed

    # -- update -------------------------------------------------------

    def update(self, dt: float):
        self.time += dt
        for attr in ('overlay_timer', 'saved_timer', 'confirm_timer'):
            v = getattr(self, attr)
            if v > 0:
                setattr(self, attr, max(0.0, v - dt))

        if not self.running:
            return

        self.step_timer += dt
        interval = _SPEEDS[self.speed_idx]
        if self.step_timer >= interval:
            self.step_timer -= interval
            self._step()
            self._check_extinct(interval)
            if self._extinct_timer > 2.0:
                # Advance rather than replay: reseeding the same corpse under
                # the same rule would just loop the same eight generations.
                self.pattern_idx = (self.pattern_idx + 1) % len(_PATTERNS)
                self._seed()
                self.running = True
                self.overlay_timer = 2.5

    # -- draw ---------------------------------------------------------

    def draw(self):
        d = self.display
        d.clear()
        set_pixel = d.set_pixel

        col = self._live_color()
        grid = self.grid
        born = self.born
        i = 0
        for y in range(N):
            for x in range(N):
                if grid[i]:
                    set_pixel(x, y, _BIRTH_COLOR if i in born else col)
                i += 1

        self._draw_hud()

    def _live_color(self):
        """Slow hue drift, so a long run doesn't sit on one flat colour."""
        h = (self.time * 0.04) % 1.0
        seg = h * 6.0
        k = int(seg)
        f = seg - k
        up = int(255 * f)
        dn = int(255 * (1 - f))
        return ((255, up, 40), (dn, 255, 40), (40, 255, up),
                (40, dn, 255), (up, 40, 255), (255, 40, dn))[k % 6]

    def _draw_hud(self):
        d = self.display

        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            name = _PATTERNS[self.pattern_idx][0]
            rule_name, birth, survive = _RULES[self.rule_idx]
            c = int(235 * alpha)
            dim = int(150 * alpha)
            d.draw_rect(0, 0, N, 19, (0, 0, 0), filled=True)
            d.draw_text_small(1, 1, name[:12], (c, c, c))
            d.draw_text_small(1, 7, rule_name[:12], (dim, dim, int(220 * alpha)))
            d.draw_text_small(1, 13, _rulestring(birth, survive)[:15],
                              (dim, dim, dim))

        if self.confirm_timer > 0 and self.saved_timer <= 0:
            a = min(1.0, self.confirm_timer / 0.5)
            d.draw_text_small(1, N - 6, "SAVE?",
                              (int(255 * a), int(220 * a), int(80 * a)))
        elif self.saved_timer > 0:
            a = min(1.0, self.saved_timer / 0.5)
            d.draw_text_small(1, N - 6, "SAVED",
                              (int(80 * a), int(255 * a), int(80 * a)))
        elif not self.running:
            # The bench state needs to say so, or a still life looks identical
            # to a paused grid.
            d.draw_text_small(1, N - 6, "READY", (120, 170, 120))
        else:
            d.draw_text_small(1, N - 6, f"G{self.generation}"[:5],
                              (90, 110, 130))
