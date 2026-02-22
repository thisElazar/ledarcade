"""
Genetic Drift - Population Genetics
=======================================
Hardy-Weinberg equilibrium and genetic drift visualized as a smooth
population map. Large populations hold steady allele frequencies;
shrink the population and watch random drift fix or lose alleles.

Wright-Fisher model: discrete, non-overlapping generations in a
well-mixed population. Each generation, 2N alleles are sampled
from the previous generation weighted by fitness.

Controls:
  Left/Right  - Population size
  Up/Down     - Selection pressure (favors A)
  Action      - Bottleneck (kill 90%)
"""

import random
import math
from . import Visual, Display, Colors, GRID_SIZE

# Layout constants
N = GRID_SIZE  # 64

# History chart: top portion
HISTORY_Y0 = 2      # first row of chart
HISTORY_Y1 = 30     # last row of chart (exclusive)
HISTORY_H = HISTORY_Y1 - HISTORY_Y0

# Population map: middle portion
MAP_Y0 = 32
MAP_Y1 = 58
MAP_COLS = 8         # 8x8 blocks => each block is 8x~3 pixels
MAP_ROWS = 6         # 6 rows of blocks to fill 26 pixel rows

# Allele frequency bar: bottom
BAR_Y0 = 60
BAR_Y1 = 63          # inclusive, 4 rows tall

# Colors
BG = (6, 6, 10)
COLOR_A = (40, 90, 220)       # blue -- A allele
COLOR_a = (230, 140, 40)      # orange -- a allele
COLOR_SEP = (20, 20, 25)      # separator lines

# Chart dim colors
CHART_A = (15, 30, 80)
CHART_a = (70, 45, 12)

# For the population map gradient
# Pure A (p=1) = deep blue, pure a (p=0) = warm orange, mixed = purple
def _freq_color(p):
    """Map allele frequency p (0=all a, 1=all A) to a color."""
    # Blue channel: rises with p
    # Red channel: rises with q = 1-p
    # Green: low throughout, slight bump in middle
    q = 1.0 - p
    r = int(40 * p + 220 * q)
    g = int(60 * p + 80 * q + 40 * p * q * 4)  # bump in middle
    b = int(220 * p + 30 * q)
    return (min(255, r), min(255, g), min(255, b))


class GeneticDrift(Visual):
    name = "GENETIC DRIFT"
    description = "Population genetics"
    category = "science"

    # Population bounds
    POP_MIN = 10
    POP_MAX = 500
    POP_DEFAULT = 200
    POP_STEP = 10

    # Selection bounds
    SEL_MIN = 0.0
    SEL_MAX = 0.5
    SEL_STEP = 0.05

    # Generation timing
    GEN_INTERVAL = 0.15

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.gen_timer = 0.0
        self.generation = 0

        # Parameters
        self.target_pop = self.POP_DEFAULT
        self.selection = 0.0

        # Overlay
        self.overlay_timer = 0.0
        self.overlay_text = ""

        # Fixation message
        self.fix_timer = 0.0
        self.fix_text = ""

        # Frequency history (list of p values)
        self.freq_history = []

        # Region assignments: which region index each organism belongs to
        self.num_regions = MAP_COLS * MAP_ROWS
        self.region_assign = []

        # Population: list of (allele1, allele2) tuples
        # True = A, False = a
        self.population = []
        self._init_population()

    def _init_population(self):
        """Create initial population with ~50/50 allele frequencies."""
        self.population = []
        for _ in range(self.target_pop):
            a1 = random.random() < 0.5
            a2 = random.random() < 0.5
            self.population.append((a1, a2))
        self.generation = 0
        self.freq_history = []
        self._assign_regions()

    def _assign_regions(self):
        """Randomly assign each organism to a display region."""
        self.region_assign = [
            random.randint(0, self.num_regions - 1)
            for _ in range(len(self.population))
        ]

    def _allele_freq(self):
        """Return frequency of A allele (p)."""
        if not self.population:
            return 0.5
        total = len(self.population) * 2
        a_count = sum((1 if a1 else 0) + (1 if a2 else 0)
                      for a1, a2 in self.population)
        return a_count / total

    def _fitness(self, a1, a2):
        """Fitness based on genotype and current selection pressure."""
        s = self.selection
        if a1 and a2:       # AA
            return 1.0 + s
        elif a1 or a2:      # Aa
            return 1.0 + s * 0.5
        else:               # aa
            return 1.0

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Action: bottleneck (kill 90%)
        if input_state.action_l or input_state.action_r:
            if len(self.population) > 2:
                survivors = max(2, len(self.population) // 10)
                random.shuffle(self.population)
                self.population = self.population[:survivors]
                self._assign_regions()
                self.overlay_text = f"BOTTLENECK N={len(self.population)}"
                self.overlay_timer = 2.0
            consumed = True

        # Left/Right: population size (continuous)
        if input_state.left:
            self.target_pop = max(self.POP_MIN,
                                  self.target_pop - self.POP_STEP)
            self.overlay_text = f"POP {self.target_pop}"
            self.overlay_timer = 1.5
            consumed = True
        if input_state.right:
            self.target_pop = min(self.POP_MAX,
                                  self.target_pop + self.POP_STEP)
            self.overlay_text = f"POP {self.target_pop}"
            self.overlay_timer = 1.5
            consumed = True

        # Up/Down: selection pressure (single-press)
        if input_state.up_pressed:
            self.selection = min(self.SEL_MAX,
                                 round(self.selection + self.SEL_STEP, 2))
            self.overlay_text = f"SEL {self.selection:.2f}"
            self.overlay_timer = 1.5
            consumed = True
        if input_state.down_pressed:
            self.selection = max(self.SEL_MIN,
                                 round(self.selection - self.SEL_STEP, 2))
            self.overlay_text = f"SEL {self.selection:.2f}"
            self.overlay_timer = 1.5
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt

        if self.overlay_timer > 0:
            self.overlay_timer -= dt

        if self.fix_timer > 0:
            self.fix_timer -= dt
            if self.fix_timer <= 0:
                self._init_population()
            return  # pause during fixation message

        self.gen_timer += dt
        if self.gen_timer >= self.GEN_INTERVAL:
            self.gen_timer -= self.GEN_INTERVAL
            self._step_generation()

    def _step_generation(self):
        """Wright-Fisher model: sample next generation."""
        pop = self.population
        n = len(pop)
        if n < 2:
            self._init_population()
            return

        # Build fitness-weighted parent pool
        weights = [self._fitness(a1, a2) for a1, a2 in pop]
        total_w = sum(weights)
        cum_weights = []
        acc = 0.0
        for w in weights:
            acc += w / total_w
            cum_weights.append(acc)

        def pick_parent():
            r = random.random()
            lo, hi = 0, n - 1
            while lo < hi:
                mid = (lo + hi) // 2
                if cum_weights[mid] < r:
                    lo = mid + 1
                else:
                    hi = mid
            return lo

        # Produce target_pop offspring
        new_pop = []
        new_regions = []
        target = self.target_pop
        for _ in range(target):
            p1 = pick_parent()
            p2 = pick_parent()
            # Each parent contributes one allele
            a1 = pop[p1][0] if random.random() < 0.5 else pop[p1][1]
            a2 = pop[p2][0] if random.random() < 0.5 else pop[p2][1]
            new_pop.append((a1, a2))
            # Offspring inherits parent's region with some drift
            if p1 < len(self.region_assign):
                region = self.region_assign[p1]
                # 20% chance to drift to adjacent region
                if random.random() < 0.2:
                    row = region // MAP_COLS
                    col = region % MAP_COLS
                    dr = random.choice([-1, 0, 0, 1])
                    dc = random.choice([-1, 0, 0, 1])
                    row = max(0, min(MAP_ROWS - 1, row + dr))
                    col = max(0, min(MAP_COLS - 1, col + dc))
                    region = row * MAP_COLS + col
                new_regions.append(region)
            else:
                new_regions.append(random.randint(0, self.num_regions - 1))

        self.population = new_pop
        self.region_assign = new_regions
        self.generation += 1

        # Record allele frequency
        p = self._allele_freq()
        self.freq_history.append(p)
        if len(self.freq_history) > N:
            self.freq_history = self.freq_history[-N:]

        # Check for fixation
        if p >= 1.0:
            self.fix_text = "A FIXED"
            self.fix_timer = 2.5
        elif p <= 0.0:
            self.fix_text = "a FIXED"
            self.fix_timer = 2.5

    def draw(self):
        d = self.display
        d.clear()
        set_pixel = d.set_pixel
        draw_rect = d.draw_rect

        # --- History chart (y = HISTORY_Y0 to HISTORY_Y1-1) ---
        hist = self.freq_history
        num_cols = len(hist)
        for i, p in enumerate(hist):
            col_x = N - num_cols + i
            if col_x < 0:
                continue
            split_y = HISTORY_Y0 + int((1.0 - p) * HISTORY_H)
            # Top portion (a allele) and bottom portion (A allele)
            if split_y > HISTORY_Y0:
                draw_rect(col_x, HISTORY_Y0, 1, split_y - HISTORY_Y0, CHART_a)
            if split_y < HISTORY_Y1:
                draw_rect(col_x, split_y, 1, HISTORY_Y1 - split_y, CHART_A)

        # Draw the p=0.5 line as a subtle dotted guide
        mid_y = HISTORY_Y0 + HISTORY_H // 2
        for x in range(0, N, 3):
            set_pixel(x, mid_y, (30, 30, 40))

        # Separator under chart
        draw_rect(0, HISTORY_Y1, N, 1, COLOR_SEP)

        # --- Population map (y = MAP_Y0 to MAP_Y1-1) ---
        region_a_count = [0] * self.num_regions
        region_total = [0] * self.num_regions
        for idx, (a1, a2) in enumerate(self.population):
            if idx < len(self.region_assign):
                r = self.region_assign[idx]
                region_total[r] += 2
                region_a_count[r] += (1 if a1 else 0) + (1 if a2 else 0)

        map_h = MAP_Y1 - MAP_Y0
        block_h = map_h / MAP_ROWS
        block_w = N / MAP_COLS
        global_p = self._allele_freq()

        for row in range(MAP_ROWS):
            for col in range(MAP_COLS):
                r = row * MAP_COLS + col
                if region_total[r] > 0:
                    p = region_a_count[r] / region_total[r]
                else:
                    p = global_p

                color = _freq_color(p)

                x0 = int(col * block_w)
                x1 = int((col + 1) * block_w)
                y0 = MAP_Y0 + int(row * block_h)
                y1 = MAP_Y0 + int((row + 1) * block_h)

                draw_rect(x0, y0, x1 - x0, y1 - y0, color)

                # Subtle grid lines (darken edges)
                edge = (max(0, color[0] - 25),
                        max(0, color[1] - 25),
                        max(0, color[2] - 25))
                if col > 0:
                    draw_rect(x0, y0, 1, y1 - y0, edge)
                if row > 0:
                    draw_rect(x0, y0, x1 - x0, 1, edge)

        # Separator above bar
        draw_rect(0, BAR_Y0 - 1, N, 1, COLOR_SEP)

        # --- Allele frequency bar (y = BAR_Y0 to BAR_Y1) ---
        p = self._allele_freq()
        split_x = int(p * N)
        bar_h = BAR_Y1 - BAR_Y0 + 1
        if split_x > 0:
            draw_rect(0, BAR_Y0, split_x, bar_h, COLOR_A)
        if split_x < N:
            draw_rect(split_x, BAR_Y0, N - split_x, bar_h, COLOR_a)

        # --- HUD ---
        gen_text = f"G{self.generation}"
        self.display.draw_text_small(2, 0, gen_text, (100, 100, 100))

        pop_text = f"N={len(self.population)}"
        text_w = len(pop_text) * 5
        self.display.draw_text_small(N - text_w - 1, 0, pop_text, (100, 100, 100))

        # Fixation message
        if self.fix_timer > 0:
            alpha = min(1.0, self.fix_timer / 0.5)
            if "A FIXED" in self.fix_text:
                fc = (int(50 * alpha), int(90 * alpha), int(255 * alpha))
            else:
                fc = (int(240 * alpha), int(150 * alpha), int(40 * alpha))
            tw = len(self.fix_text) * 5
            tx = (N - tw) // 2
            self.display.draw_text_small(tx, 44, self.fix_text, fc)
            fix_gen = f"GEN {self.generation}"
            tw2 = len(fix_gen) * 5
            tx2 = (N - tw2) // 2
            self.display.draw_text_small(tx2, 50, fix_gen,
                                         (int(120 * alpha),) * 3)

        # Parameter overlay
        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            brightness = int(200 * alpha)
            self.display.draw_text_small(2, MAP_Y0 + 1, self.overlay_text,
                                         (brightness, brightness, brightness))
