"""
Epidemic - SIR Disease Model
==============================
Susceptible-Infected-Recovered model on a 64x64 spatial grid.

Infection spreads from infected cells to adjacent susceptible cells with
probability beta (transmission rate). Infected cells recover after gamma
timesteps. R0 = beta * 4 / (1/gamma) determines outbreak dynamics.

At low R0 the outbreak fizzles. At high R0 a wavefront sweeps the grid.
Vaccination creates firebreaks -- at ~60-70% coverage, herd immunity
protects the remaining susceptible population.

Controls:
  Left/Right  - Adjust transmission rate beta
  Up/Down     - Adjust recovery time gamma
  Action      - Seed new infection at random location
  Both held   - Toggle vaccination (60% random immunity)
"""

import random
from . import Visual, Display, Colors, GRID_SIZE


# Cell states
SUSCEPTIBLE = 0
INFECTED = 1
RECOVERED = 2
VACCINATED = 3

# Colors for each state
COLOR_SUSCEPTIBLE = (40, 80, 200)
COLOR_INFECTED = (255, 40, 40)
COLOR_RECOVERED = (100, 100, 110)
COLOR_VACCINATED = (40, 200, 100)
COLOR_BG = (5, 5, 15)

# Infected cells glow brighter when freshly infected
COLOR_INFECTED_FRESH = (255, 120, 40)


class Epidemic(Visual):
    name = "EPIDEMIC"
    description = "SIR disease spread"
    category = "automata"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.step_timer = 0.0
        self.step_interval = 0.05

        # SIR parameters
        self.beta = 0.30       # transmission probability per neighbor
        self.gamma = 10        # recovery time in steps
        self.beta_min = 0.05
        self.beta_max = 0.80
        self.gamma_min = 3
        self.gamma_max = 30

        # Grid state: cell type
        self.grid = [[SUSCEPTIBLE] * GRID_SIZE for _ in range(GRID_SIZE)]
        # Per-cell infection timer (how many steps since infected)
        self.inf_timer = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]

        # Generation counter
        self.generation = 0

        # Vaccination state
        self.vaccinated = False

        # Both-button detection
        self._both_pressed_prev = False

        # Overlay for parameter display
        self.overlay_timer = 0.0
        self.overlay_text = ""

        # Pause after outbreak dies before auto-reseed
        self.reseed_delay = 0.0

        # Seed initial infections
        self._seed_infections(4)

    def _seed_infections(self, count):
        """Place count new infections at random susceptible locations."""
        candidates = []
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if self.grid[y][x] == SUSCEPTIBLE:
                    candidates.append((x, y))
        if not candidates:
            return
        random.shuffle(candidates)
        for i in range(min(count, len(candidates))):
            x, y = candidates[i]
            self.grid[y][x] = INFECTED
            self.inf_timer[y][x] = 0

    def _count_infected(self):
        """Return number of currently infected cells."""
        count = 0
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if self.grid[y][x] == INFECTED:
                    count += 1
        return count

    def _toggle_vaccination(self):
        """Toggle vaccination on/off. Vaccinate ~60% of susceptible cells."""
        if not self.vaccinated:
            # Apply vaccination
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    if self.grid[y][x] == SUSCEPTIBLE:
                        if random.random() < 0.62:
                            self.grid[y][x] = VACCINATED
            self.vaccinated = True
            self.overlay_text = "VAX ON"
            self.overlay_timer = 1.5
        else:
            # Remove vaccination -- vaccinated become susceptible again
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    if self.grid[y][x] == VACCINATED:
                        self.grid[y][x] = SUSCEPTIBLE
            self.vaccinated = False
            self.overlay_text = "VAX OFF"
            self.overlay_timer = 1.5

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Both-button held detection for vaccination toggle
        both_held = input_state.action_l_held and input_state.action_r_held
        if both_held and not self._both_pressed_prev:
            self._toggle_vaccination()
            consumed = True
        self._both_pressed_prev = both_held

        # Single press: seed new infection (skip if both-button just triggered)
        if not both_held and (input_state.action_l or input_state.action_r):
            self._seed_infections(3)
            self.reseed_delay = 0.0
            consumed = True

        # Left/Right: adjust beta (transmission rate)
        if input_state.left:
            self.beta = max(self.beta_min, round(self.beta - 0.01, 2))
            self.overlay_text = f"B {self.beta:.2f}"
            self.overlay_timer = 1.5
            consumed = True
        if input_state.right:
            self.beta = min(self.beta_max, round(self.beta + 0.01, 2))
            self.overlay_text = f"B {self.beta:.2f}"
            self.overlay_timer = 1.5
            consumed = True

        # Up/Down: adjust gamma (recovery time)
        if input_state.up_pressed:
            self.gamma = min(self.gamma_max, self.gamma + 1)
            self.overlay_text = f"G {self.gamma}"
            self.overlay_timer = 1.5
            consumed = True
        if input_state.down_pressed:
            self.gamma = max(self.gamma_min, self.gamma - 1)
            self.overlay_text = f"G {self.gamma}"
            self.overlay_timer = 1.5
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt

        # Overlay fade
        if self.overlay_timer > 0:
            self.overlay_timer -= dt

        # Auto-reseed when no infected remain
        if self._count_infected() == 0:
            self.reseed_delay += dt
            if self.reseed_delay >= 2.0:
                # Full reset: clear recovered, keep vaccinated
                for y in range(GRID_SIZE):
                    for x in range(GRID_SIZE):
                        if self.grid[y][x] == RECOVERED:
                            self.grid[y][x] = SUSCEPTIBLE
                        self.inf_timer[y][x] = 0
                self._seed_infections(4)
                self.reseed_delay = 0.0
                self.generation = 0
            return

        self.reseed_delay = 0.0

        # Step the simulation on a timer
        self.step_timer += dt
        if self.step_timer >= self.step_interval:
            self.step_timer -= self.step_interval
            self._step()

    def _step(self):
        """Advance one SIR step."""
        self.generation += 1
        new_grid = [row[:] for row in self.grid]
        new_timer = [row[:] for row in self.inf_timer]

        # 4-neighbor offsets
        neighbors = [(0, -1), (0, 1), (-1, 0), (1, 0)]

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                state = self.grid[y][x]

                if state == INFECTED:
                    # Increment infection timer
                    new_timer[y][x] = self.inf_timer[y][x] + 1
                    # Check for recovery
                    if new_timer[y][x] >= self.gamma:
                        new_grid[y][x] = RECOVERED
                        new_timer[y][x] = 0
                    else:
                        # Try to infect neighbors
                        for dx, dy in neighbors:
                            nx = (x + dx) % GRID_SIZE
                            ny = (y + dy) % GRID_SIZE
                            if self.grid[ny][nx] == SUSCEPTIBLE:
                                if random.random() < self.beta:
                                    new_grid[ny][nx] = INFECTED
                                    new_timer[ny][nx] = 0

        self.grid = new_grid
        self.inf_timer = new_timer

    def draw(self):
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                state = self.grid[y][x]
                if state == SUSCEPTIBLE:
                    color = COLOR_SUSCEPTIBLE
                elif state == INFECTED:
                    # Brighter when freshly infected, fades toward red
                    age = self.inf_timer[y][x]
                    t = min(1.0, age / max(1, self.gamma))
                    # Lerp from fresh (orange-ish) to deep red
                    r = int(COLOR_INFECTED_FRESH[0] + (COLOR_INFECTED[0] - COLOR_INFECTED_FRESH[0]) * t)
                    g = int(COLOR_INFECTED_FRESH[1] + (COLOR_INFECTED[1] - COLOR_INFECTED_FRESH[1]) * t)
                    b = int(COLOR_INFECTED_FRESH[2] + (COLOR_INFECTED[2] - COLOR_INFECTED_FRESH[2]) * t)
                    color = (r, g, b)
                elif state == RECOVERED:
                    color = COLOR_RECOVERED
                elif state == VACCINATED:
                    color = COLOR_VACCINATED
                else:
                    color = COLOR_BG
                self.display.set_pixel(x, y, color)

        # Generation counter (bottom-left)
        gen_str = f"G{self.generation}"
        self.display.draw_text_small(2, 59, gen_str, (140, 140, 140))

        # Parameter overlay (fades out)
        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            brightness = int(220 * alpha)
            oc = (brightness, brightness, brightness)
            self.display.draw_text_small(2, 1, self.overlay_text, oc)

        # "NO INFECTED" flash when waiting to reseed
        if self._count_infected() == 0 and self.reseed_delay > 0:
            if int(self.time * 3) % 2 == 0:
                self.display.draw_text_small(2, 28, "CLEAR", (60, 200, 60))
