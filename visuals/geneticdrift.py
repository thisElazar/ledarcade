"""
Genetic Drift - Population Genetics
=======================================
Hardy-Weinberg equilibrium and genetic drift. In large populations,
allele frequencies stay stable. Shrink the population and watch
random chance fix or lose alleles -- drift overpowers selection.

Controls:
  Left/Right  - Population size
  Up/Down     - Selection pressure
  Space       - Bottleneck (kill 90%)
"""

import random
import math
from . import Visual, Display, Colors, GRID_SIZE

# Genotype constants
AA = 0
Aa = 1
aa = 2

# Colors
COLOR_AA = (40, 80, 220)      # deep blue -- homozygous dominant
COLOR_Aa = (160, 60, 200)     # purple/violet -- heterozygous
COLOR_aa = (240, 140, 40)     # warm orange -- homozygous recessive
COLOR_EMPTY = (8, 8, 12)      # very dark background
COLOR_A_ALLELE = (60, 100, 240)   # blue for A allele in freq bar
COLOR_a_ALLELE = (240, 160, 50)   # orange for a allele in freq bar


class Organism:
    """A diploid organism with two alleles at one locus."""
    __slots__ = ('x', 'y', 'allele1', 'allele2')

    def __init__(self, x, y, allele1, allele2):
        self.x = x
        self.y = y
        self.allele1 = allele1  # True = A, False = a
        self.allele2 = allele2

    @property
    def genotype(self):
        if self.allele1 and self.allele2:
            return AA
        elif self.allele1 or self.allele2:
            return Aa
        else:
            return aa

    def random_allele(self):
        """Contribute one random allele (meiosis)."""
        return self.allele1 if random.random() < 0.5 else self.allele2


class GeneticDrift(Visual):
    name = "GENETIC DRIFT"
    description = "Population genetics"
    category = "science"

    # Population bounds
    POP_MIN = 20
    POP_MAX = 500
    POP_DEFAULT = 200
    POP_STEP = 10

    # Selection bounds
    SEL_MIN = 0.0
    SEL_MAX = 0.5
    SEL_STEP = 0.05

    # Generation timing
    GEN_INTERVAL = 0.15

    # History chart dimensions
    HISTORY_Y_START = 2
    HISTORY_Y_END = 20
    HISTORY_WIDTH = GRID_SIZE  # one column per generation

    # Bottom strip layout
    FREQ_BAR_Y = 58       # rows 58-59: allele frequency
    GENO_BAR_Y = 60       # rows 60-61: observed genotype freq
    HW_BAR_Y = 62         # rows 62-63: expected Hardy-Weinberg

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.gen_timer = 0.0
        self.generation = 0

        # Parameters
        self.target_pop = self.POP_DEFAULT
        self.selection = 0.0  # selection coefficient

        # Overlay
        self.overlay_timer = 0.0
        self.overlay_text = ""

        # Fixation message
        self.fix_timer = 0.0
        self.fix_text = ""

        # Frequency history (list of p values, one per generation)
        self.freq_history = []

        # Population
        self.organisms = []
        self._init_population()

    def _init_population(self):
        """Create initial population with 50/50 allele frequencies."""
        self.organisms = []
        positions = self._random_positions(self.target_pop)
        for x, y in positions:
            a1 = random.random() < 0.5
            a2 = random.random() < 0.5
            self.organisms.append(Organism(x, y, a1, a2))
        self.generation = 0
        self.freq_history = []

    def _random_positions(self, n):
        """Generate n random unique positions on the grid."""
        # For populations up to grid capacity, avoid overlap
        max_cells = GRID_SIZE * GRID_SIZE
        if n >= max_cells:
            positions = [(x, y) for y in range(GRID_SIZE) for x in range(GRID_SIZE)]
            random.shuffle(positions)
            return positions[:n]

        used = set()
        positions = []
        for _ in range(n):
            attempts = 0
            while attempts < 100:
                x = random.randint(0, GRID_SIZE - 1)
                y = random.randint(0, GRID_SIZE - 1)
                if (x, y) not in used:
                    used.add((x, y))
                    positions.append((x, y))
                    break
                attempts += 1
            else:
                # fallback: just place somewhere
                x = random.randint(0, GRID_SIZE - 1)
                y = random.randint(0, GRID_SIZE - 1)
                positions.append((x, y))
        return positions

    def _allele_freq(self):
        """Return frequency of A allele (p). q = 1 - p."""
        if not self.organisms:
            return 0.5
        total = len(self.organisms) * 2
        a_count = sum(
            (1 if o.allele1 else 0) + (1 if o.allele2 else 0)
            for o in self.organisms
        )
        return a_count / total

    def _genotype_counts(self):
        """Return (count_AA, count_Aa, count_aa)."""
        counts = [0, 0, 0]
        for o in self.organisms:
            counts[o.genotype] += 1
        return counts

    def _fitness(self, genotype):
        """Fitness based on genotype and current selection pressure."""
        s = self.selection
        if genotype == AA:
            return 1.0 + s
        elif genotype == Aa:
            return 1.0 + s * 0.5  # codominant
        else:
            return 1.0

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Action: bottleneck (kill 90%)
        if input_state.action_l or input_state.action_r:
            if len(self.organisms) > 2:
                survivors = max(2, len(self.organisms) // 10)
                random.shuffle(self.organisms)
                self.organisms = self.organisms[:survivors]
                self.overlay_text = f"BOTTLENECK N={len(self.organisms)}"
                self.overlay_timer = 2.0
            consumed = True

        # Left/Right: population size (continuous)
        if input_state.left:
            self.target_pop = max(self.POP_MIN,
                                  self.target_pop - self.POP_STEP)
            self.overlay_text = f"N={self.target_pop}"
            self.overlay_timer = 1.5
            consumed = True
        if input_state.right:
            self.target_pop = min(self.POP_MAX,
                                  self.target_pop + self.POP_STEP)
            self.overlay_text = f"N={self.target_pop}"
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

        # Overlay fade
        if self.overlay_timer > 0:
            self.overlay_timer -= dt

        # Fixation message timer
        if self.fix_timer > 0:
            self.fix_timer -= dt
            if self.fix_timer <= 0:
                # Auto-reset after fixation display
                self._init_population()
            return  # pause simulation during fixation message

        # Generation timer
        self.gen_timer += dt
        if self.gen_timer >= self.GEN_INTERVAL:
            self.gen_timer -= self.GEN_INTERVAL
            self._step_generation()

    def _step_generation(self):
        """Run one generation of the population."""
        if len(self.organisms) < 2:
            self._init_population()
            return

        # --- 1. Mating: produce offspring pool ---
        offspring = []
        # Build spatial lookup for neighbor mating
        grid_lookup = {}
        for o in self.organisms:
            grid_lookup.setdefault((o.x, o.y), []).append(o)

        for parent in self.organisms:
            # Find a mate within radius 3
            mate = self._find_mate(parent, grid_lookup)
            if mate is None:
                # Self-fertilize (just copies own alleles)
                mate = parent

            # Each parent contributes one allele
            child_a1 = parent.random_allele()
            child_a2 = mate.random_allele()
            offspring.append((child_a1, child_a2, parent))

        # --- 2. Selection: survival weighted by fitness ---
        survivors = []
        for a1, a2, parent in offspring:
            # Determine genotype of offspring
            if a1 and a2:
                geno = AA
            elif a1 or a2:
                geno = Aa
            else:
                geno = aa
            fit = self._fitness(geno)
            # Survival probability proportional to fitness
            # Normalize: max fitness is 1 + selection, so divide by that
            max_fit = 1.0 + self.selection
            prob = fit / max_fit if max_fit > 0 else 1.0
            if random.random() < prob:
                survivors.append((a1, a2, parent))

        # --- 3. Regulate to target population ---
        target = self.target_pop

        if len(survivors) > target:
            # Cull randomly (weighted by inverse fitness)
            random.shuffle(survivors)
            survivors = survivors[:target]
        elif len(survivors) < target and survivors:
            # Reproduce: pick parents proportional to fitness to fill
            while len(survivors) < target:
                # Pick two random parents from survivors
                idx1 = random.randint(0, len(survivors) - 1)
                idx2 = random.randint(0, len(survivors) - 1)
                p1_a1, p1_a2, _ = survivors[idx1]
                p2_a1, p2_a2, _ = survivors[idx2]
                # Offspring gets one allele from each
                ca1 = p1_a1 if random.random() < 0.5 else p1_a2
                ca2 = p2_a1 if random.random() < 0.5 else p2_a2
                survivors.append((ca1, ca2, None))

        # --- 4. Place organisms on grid ---
        # Reuse positions from existing organisms where possible, drift by 1
        new_organisms = []
        old_positions = [(o.x, o.y) for o in self.organisms]

        for i, (a1, a2, parent) in enumerate(survivors):
            if parent is not None:
                # Drift from parent position by 1 cell
                nx = (parent.x + random.randint(-1, 1)) % GRID_SIZE
                ny = (parent.y + random.randint(-1, 1)) % GRID_SIZE
            elif i < len(old_positions):
                px, py = old_positions[i % len(old_positions)]
                nx = (px + random.randint(-1, 1)) % GRID_SIZE
                ny = (py + random.randint(-1, 1)) % GRID_SIZE
            else:
                nx = random.randint(0, GRID_SIZE - 1)
                ny = random.randint(0, GRID_SIZE - 1)
            new_organisms.append(Organism(nx, ny, a1, a2))

        self.organisms = new_organisms
        self.generation += 1

        # Record allele frequency
        p = self._allele_freq()
        self.freq_history.append(p)
        # Trim history to screen width
        if len(self.freq_history) > self.HISTORY_WIDTH:
            self.freq_history = self.freq_history[-self.HISTORY_WIDTH:]

        # Check for fixation
        if len(self.organisms) > 0:
            if p >= 1.0:
                self.fix_text = "A FIXED"
                self.fix_timer = 2.0
            elif p <= 0.0:
                self.fix_text = "a FIXED"
                self.fix_timer = 2.0

    def _find_mate(self, parent, grid_lookup):
        """Find a random mate within radius 3 of parent."""
        radius = 3
        candidates = []
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx == 0 and dy == 0:
                    continue
                nx = (parent.x + dx) % GRID_SIZE
                ny = (parent.y + dy) % GRID_SIZE
                cell_orgs = grid_lookup.get((nx, ny))
                if cell_orgs:
                    candidates.extend(cell_orgs)
        if candidates:
            return random.choice(candidates)
        return None

    def draw(self):
        N = GRID_SIZE

        # Clear to background
        for y in range(N):
            for x in range(N):
                self.display.set_pixel(x, y, COLOR_EMPTY)

        # --- Draw frequency history chart (y=2 to y=20) ---
        chart_h = self.HISTORY_Y_END - self.HISTORY_Y_START
        hist = self.freq_history
        num_cols = len(hist)
        # Right-align: most recent generation at right edge
        for i, p in enumerate(hist):
            col_x = N - num_cols + i
            if col_x < 0:
                continue
            # p = frequency of A allele
            # Draw column: top portion blue (A), bottom portion orange (a)
            split_y = self.HISTORY_Y_START + int((1.0 - p) * chart_h)
            for cy in range(self.HISTORY_Y_START, self.HISTORY_Y_END):
                if cy < split_y:
                    # a allele portion (top = high q means a-heavy)
                    # Dim orange
                    self.display.set_pixel(col_x, cy, (80, 50, 15))
                else:
                    # A allele portion
                    # Dim blue
                    self.display.set_pixel(col_x, cy, (15, 30, 80))

        # Thin separator line under chart
        for x in range(N):
            self.display.set_pixel(x, self.HISTORY_Y_END, (25, 25, 30))

        # --- Draw organisms on grid (y=21 to y=56) ---
        for o in self.organisms:
            # Only draw in the main area (skip bottom strip and top chart)
            # Wrap y into visible organism area
            draw_y = o.y
            if draw_y < self.HISTORY_Y_END + 1:
                # Remap to organism area
                draw_y = self.HISTORY_Y_END + 1 + (draw_y % (57 - self.HISTORY_Y_END - 1))
            if draw_y > 56:
                draw_y = self.HISTORY_Y_END + 1 + (draw_y % (57 - self.HISTORY_Y_END - 1))

            geno = o.genotype
            if geno == AA:
                color = COLOR_AA
            elif geno == Aa:
                color = COLOR_Aa
            else:
                color = COLOR_aa
            self.display.set_pixel(o.x, draw_y, color)

        # --- Bottom strip: frequency bars ---
        p = self._allele_freq()
        q = 1.0 - p
        counts = self._genotype_counts()
        total = max(1, sum(counts))

        # Row 58-59: Allele frequency bar (A blue vs a orange)
        split_x = int(p * N)
        for x in range(N):
            c = COLOR_A_ALLELE if x < split_x else COLOR_a_ALLELE
            self.display.set_pixel(x, self.FREQ_BAR_Y, c)
            self.display.set_pixel(x, self.FREQ_BAR_Y + 1, c)

        # Row 60-61: Observed genotype frequencies
        aa_end = int(counts[AA] / total * N)
        het_end = aa_end + int(counts[Aa] / total * N)
        for x in range(N):
            if x < aa_end:
                c = COLOR_AA
            elif x < het_end:
                c = COLOR_Aa
            else:
                c = COLOR_aa
            self.display.set_pixel(x, self.GENO_BAR_Y, c)
            self.display.set_pixel(x, self.GENO_BAR_Y + 1, c)

        # Row 62-63: Hardy-Weinberg expected (p^2, 2pq, q^2)
        hw_aa = p * p
        hw_het = 2 * p * q
        hw_aa_end = int(hw_aa * N)
        hw_het_end = hw_aa_end + int(hw_het * N)
        for x in range(N):
            if x < hw_aa_end:
                c = COLOR_AA
            elif x < hw_het_end:
                c = COLOR_Aa
            else:
                c = COLOR_aa
            self.display.set_pixel(x, self.HW_BAR_Y, c)
            self.display.set_pixel(x, self.HW_BAR_Y + 1, c)

        # Thin separator above bottom strip
        for x in range(N):
            self.display.set_pixel(x, self.FREQ_BAR_Y - 1, (25, 25, 30))

        # --- HUD text ---
        # Generation counter (top-left, above chart)
        gen_text = f"G{self.generation}"
        self.display.draw_text_small(2, 0, gen_text, (120, 120, 120))

        # Population count (top-right area)
        pop_text = f"N={len(self.organisms)}"
        # Estimate text width: 4px per char + 1px spacing
        text_w = len(pop_text) * 5
        self.display.draw_text_small(N - text_w - 1, 0, pop_text, (120, 120, 120))

        # Fixation message
        if self.fix_timer > 0:
            alpha = min(1.0, self.fix_timer / 0.5)
            brightness = int(255 * alpha)
            # Choose color based on which allele fixed
            if "A FIXED" in self.fix_text:
                fc = (int(60 * alpha), int(100 * alpha), brightness)
            else:
                fc = (brightness, int(180 * alpha), int(50 * alpha))
            # Center the text roughly
            tw = len(self.fix_text) * 5
            tx = (N - tw) // 2
            self.display.draw_text_small(tx, 28, self.fix_text, fc)
            # Also show generation count at fixation
            fix_gen = f"GEN {self.generation}"
            tw2 = len(fix_gen) * 5
            tx2 = (N - tw2) // 2
            self.display.draw_text_small(tx2, 35, fix_gen, (int(150 * alpha), int(150 * alpha), int(150 * alpha)))

        # Parameter overlay
        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            brightness = int(220 * alpha)
            oc = (brightness, brightness, brightness)
            self.display.draw_text_small(2, self.HISTORY_Y_END + 2, self.overlay_text, oc)
