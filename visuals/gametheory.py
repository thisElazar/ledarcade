"""
Game Theory - Prisoner's Dilemma
====================================
Iterated Prisoner's Dilemma on a 64x64 grid. Four strategies compete:
Always Cooperate, Always Defect, Tit-for-Tat, and Random. After each
round, cells adopt the strategy of their most successful neighbor.
Watch Tit-for-Tat's cooperative clusters resist waves of defectors.

Controls:
  Left/Right  - Temptation payoff (defection reward)
  Up/Down     - Cycle initial strategy mix
  Space       - Inject defector cluster
"""

import random
from . import Visual, Display, Colors, GRID_SIZE

# Strategies
COOPERATE = 0
DEFECT = 1
TIT_FOR_TAT = 2
RANDOM = 3

STRATEGY_NAMES = ["COOPERATE", "DEFECT", "TIT-FOR-TAT", "RANDOM"]

# Actions
C = 0  # cooperate
D = 1  # defect

# Strategy colors (base)
STRATEGY_COLORS = {
    COOPERATE:   (60, 120, 255),
    DEFECT:      (255, 50, 50),
    TIT_FOR_TAT: (50, 220, 80),
    RANDOM:      (220, 200, 50),
}

# Moore neighborhood offsets (8 neighbors)
MOORE = [(-1, -1), (0, -1), (1, -1),
         (-1,  0),          (1,  0),
         (-1,  1), (0,  1), (1,  1)]

# Initial mix presets: name and (cooperate%, defect%, tft%, random%)
MIXES = [
    ("EQUAL",       0.25, 0.25, 0.25, 0.25),
    ("COOP WORLD",  0.90, 0.05, 0.05, 0.00),
    ("DEFECT WORLD",0.05, 0.90, 0.05, 0.00),
    ("TFT vs DEFECT",0.00, 0.50, 0.50, 0.00),
]


class GameTheory(Visual):
    name = "GAME THEORY"
    description = "Prisoner's Dilemma"
    category = "automata"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.step_timer = 0.0
        self.step_interval = 0.15

        # Payoff parameters
        self.R = 3    # reward (both cooperate)
        self.T = 5.0  # temptation (I defect, they cooperate) -- adjustable
        self.S = 0    # sucker (I cooperate, they defect)
        self.P = 1    # punishment (both defect)
        self.T_min = 3.5
        self.T_max = 7.0

        # Mix index
        self.mix_index = 0

        # Grids
        N = GRID_SIZE
        self.strategy = [[COOPERATE] * N for _ in range(N)]
        self.last_action = [[C] * N for _ in range(N)]
        self.score = [[0.0] * N for _ in range(N)]

        # Overlay
        self.overlay_timer = 0.0
        self.overlay_text = ""
        self.overlay_lines = []  # list of (text, color) for multi-line

        # Auto-reset state
        self.uniform_timer = 0.0
        self.result_shown = False

        # Population counts
        self.pop = [0, 0, 0, 0]

        # Generation counter
        self.generation = 0

        self._seed()

    def _seed(self):
        """Populate grid according to current mix preset."""
        N = GRID_SIZE
        name, pc, pd, pt, pr = MIXES[self.mix_index]

        # Build cumulative thresholds
        cum_c = pc
        cum_d = cum_c + pd
        cum_t = cum_d + pt
        # remainder is random

        for y in range(N):
            for x in range(N):
                r = random.random()
                if r < cum_c:
                    self.strategy[y][x] = COOPERATE
                elif r < cum_d:
                    self.strategy[y][x] = DEFECT
                elif r < cum_t:
                    self.strategy[y][x] = TIT_FOR_TAT
                else:
                    self.strategy[y][x] = RANDOM
                # TFT cooperates on first round
                self.last_action[y][x] = C
                self.score[y][x] = 0.0

        self.generation = 0
        self.uniform_timer = 0.0
        self.result_shown = False
        self._count_pop()

    def _count_pop(self):
        """Count population of each strategy."""
        counts = [0, 0, 0, 0]
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                counts[self.strategy[y][x]] += 1
        self.pop = counts

    def _payoff(self, my_action, their_action):
        """Return payoff for my_action vs their_action."""
        if my_action == C and their_action == C:
            return self.R
        elif my_action == D and their_action == C:
            return self.T
        elif my_action == C and their_action == D:
            return self.S
        else:  # both defect
            return self.P

    def _choose_action(self, strategy, neighbor_last_action):
        """Determine action for a cell given its strategy."""
        if strategy == COOPERATE:
            return C
        elif strategy == DEFECT:
            return D
        elif strategy == TIT_FOR_TAT:
            # Copy what this specific neighbor did last round
            return neighbor_last_action
        else:  # RANDOM
            return C if random.random() < 0.5 else D

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Action: inject defector cluster
        if input_state.action_l or input_state.action_r:
            cx = random.randint(0, GRID_SIZE - 1)
            cy = random.randint(0, GRID_SIZE - 1)
            half = 3  # 7x7 block
            for dy in range(-half, half + 1):
                for dx in range(-half, half + 1):
                    nx = (cx + dx) % GRID_SIZE
                    ny = (cy + dy) % GRID_SIZE
                    self.strategy[ny][nx] = DEFECT
                    self.last_action[ny][nx] = D
            self._count_pop()
            self.overlay_text = "DEFECTORS!"
            self.overlay_timer = 1.5
            self.uniform_timer = 0.0
            self.result_shown = False
            consumed = True

        # Left/Right: temptation payoff
        if input_state.left:
            self.T = max(self.T_min, round(self.T - 0.1, 1))
            self.overlay_text = f"T={self.T:.1f}"
            self.overlay_timer = 1.5
            consumed = True
        if input_state.right:
            self.T = min(self.T_max, round(self.T + 0.1, 1))
            self.overlay_text = f"T={self.T:.1f}"
            self.overlay_timer = 1.5
            consumed = True

        # Up/Down: cycle mix
        if input_state.up_pressed:
            self.mix_index = (self.mix_index + 1) % len(MIXES)
            self._seed()
            name = MIXES[self.mix_index][0]
            self.overlay_text = name
            self.overlay_timer = 2.0
            consumed = True
        if input_state.down_pressed:
            self.mix_index = (self.mix_index - 1) % len(MIXES)
            self._seed()
            name = MIXES[self.mix_index][0]
            self.overlay_text = name
            self.overlay_timer = 2.0
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt

        # Overlay fade
        if self.overlay_timer > 0:
            self.overlay_timer -= dt

        # Check for uniform grid (auto-reset)
        if not self.result_shown:
            nonzero = [i for i in range(4) if self.pop[i] > 0]
            if len(nonzero) == 1:
                self.uniform_timer += dt
                if self.uniform_timer >= 3.0:
                    winner = nonzero[0]
                    self.overlay_text = f"{STRATEGY_NAMES[winner]} WINS"
                    self.overlay_timer = 3.0
                    self.result_shown = True
                    self.uniform_timer = 0.0
            else:
                self.uniform_timer = 0.0
        else:
            self.uniform_timer += dt
            if self.uniform_timer >= 3.0:
                # Auto-advance to next mix and reseed
                self.mix_index = (self.mix_index + 1) % len(MIXES)
                self._seed()
                name = MIXES[self.mix_index][0]
                self.overlay_text = name
                self.overlay_timer = 2.0

        # Step simulation on timer
        self.step_timer += dt
        if self.step_timer >= self.step_interval:
            self.step_timer -= self.step_interval
            if not self.result_shown:
                self._step()

    def _step(self):
        """Run one round of iterated Prisoner's Dilemma."""
        N = GRID_SIZE

        # Phase 1: Each cell plays PD with all 8 neighbors, accumulate scores
        new_score = [[0.0] * N for _ in range(N)]
        # Track actions taken this round (for TFT memory)
        # For TFT, it plays differently against each neighbor, but we need
        # a single "action" per cell for neighbors to reference next round.
        # We'll record the majority action taken.
        action_counts = [[0] * N for _ in range(N)]  # count of cooperations

        for y in range(N):
            for x in range(N):
                strat = self.strategy[y][x]
                total_payoff = 0.0
                coop_count = 0
                for dx, dy in MOORE:
                    nx = (x + dx) % N
                    ny = (y + dy) % N
                    # My action toward this neighbor
                    my_act = self._choose_action(strat,
                                                 self.last_action[ny][nx])
                    # Neighbor's action toward me
                    n_strat = self.strategy[ny][nx]
                    their_act = self._choose_action(n_strat,
                                                    self.last_action[y][x])
                    total_payoff += self._payoff(my_act, their_act)
                    if my_act == C:
                        coop_count += 1

                new_score[y][x] = total_payoff
                action_counts[y][x] = coop_count

        # Update last_action: majority action (>= 4 cooperations out of 8)
        new_last_action = [[C] * N for _ in range(N)]
        for y in range(N):
            for x in range(N):
                new_last_action[y][x] = C if action_counts[y][x] >= 4 else D

        # Phase 2: Each cell adopts strategy of highest-scoring in neighborhood
        new_strategy = [[COOPERATE] * N for _ in range(N)]
        for y in range(N):
            for x in range(N):
                best_score = new_score[y][x]
                best_strat = self.strategy[y][x]
                for dx, dy in MOORE:
                    nx = (x + dx) % N
                    ny = (y + dy) % N
                    if new_score[ny][nx] > best_score:
                        best_score = new_score[ny][nx]
                        best_strat = self.strategy[ny][nx]
                new_strategy[y][x] = best_strat

        self.strategy = new_strategy
        self.last_action = new_last_action
        self.score = new_score
        self.generation += 1
        self._count_pop()

    def draw(self):
        N = GRID_SIZE

        # Find score range for brightness modulation
        min_score = 0.0
        max_score = 1.0
        for y in range(N):
            for x in range(N):
                s = self.score[y][x]
                if s > max_score:
                    max_score = s
                if s < min_score:
                    min_score = s
        score_range = max_score - min_score if max_score > min_score else 1.0

        for y in range(N):
            for x in range(N):
                strat = self.strategy[y][x]
                base_r, base_g, base_b = STRATEGY_COLORS[strat]

                # Brightness modulation: 0.35 to 1.0 based on score
                t = (self.score[y][x] - min_score) / score_range
                brightness = 0.35 + 0.65 * t

                r = int(base_r * brightness)
                g = int(base_g * brightness)
                b = int(base_b * brightness)
                self.display.set_pixel(x, y, (r, g, b))

        # Population bar at bottom row (y=63)
        total = sum(self.pop)
        if total > 0:
            # Draw proportional bar
            bar_x = 0
            for strat_idx in range(4):
                px_count = int(N * self.pop[strat_idx] / total)
                if strat_idx == 3:
                    # Last strategy gets remaining pixels to avoid gaps
                    px_count = N - bar_x
                color = STRATEGY_COLORS[strat_idx]
                # Dim the bar colors slightly
                bar_color = (color[0] // 2, color[1] // 2, color[2] // 2)
                for bx in range(bar_x, min(bar_x + px_count, N)):
                    self.display.set_pixel(bx, N - 1, bar_color)
                bar_x += px_count

        # Faint generation counter
        gen_text = f"G:{self.generation}"
        self.display.draw_text_small(2, 57, gen_text, (60, 60, 60))

        # Overlay text (parameter changes, mix name, results)
        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            brightness = int(220 * alpha)
            oc = (brightness, brightness, brightness)
            self.display.draw_text_small(2, 1, self.overlay_text, oc)
