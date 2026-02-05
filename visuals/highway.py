"""
Highway - Nagel-Schreckenberg Traffic Model
=============================================
1D cellular automaton per lane. Each timestep:
  1. Accelerate: v = min(v+1, v_max)
  2. Brake:      v = min(v, gap-1)
  3. Random slow: with probability p, v = max(v-1, 0)
  4. Move:       position += v

Phantom traffic jams spontaneously form and propagate backward.

Controls:
  Up/Down    - Adjust density
  Left/Right - Adjust randomization probability p
"""

import random
from . import Visual, Display, Colors, GRID_SIZE


def speed_color(v, v_max):
    """Map speed to color: red(stopped) -> orange -> yellow -> green -> white(fast)."""
    if v_max == 0:
        return (255, 0, 0)
    t = v / v_max
    if t < 0.25:
        r, g, b = 255, int(t * 4 * 80), 0
    elif t < 0.5:
        r, g, b = 255, 80 + int((t - 0.25) * 4 * 175), 0
    elif t < 0.75:
        r, g, b = 255 - int((t - 0.5) * 4 * 55), 255, int((t - 0.5) * 4 * 80)
    else:
        r, g, b = 200 + int((t - 0.75) * 4 * 55), 255, 80 + int((t - 0.75) * 4 * 175)
    return (min(255, r), min(255, g), min(255, b))


class Highway(Visual):
    name = "HIGHWAY"
    description = "Nagel-Schreckenberg model"
    category = "road_rail"

    V_MAX = 5
    NUM_LANES = 5
    ROAD_LEN = 256  # 4x screen width for smooth wrap

    ROAD_BG = (50, 50, 55)
    LANE_DASH = (80, 70, 20)
    SHOULDER = (70, 70, 60)

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.step_timer = 0.0
        self.step_interval = 0.08
        self.density = 0.25
        self.p_slow = 0.3
        self.viewport = 0.0

        # Each lane: list of (position, velocity)
        self.lanes = [[] for _ in range(self.NUM_LANES)]
        self._populate()

    def _populate(self):
        """Fill lanes at current density."""
        for lane_idx in range(self.NUM_LANES):
            self.lanes[lane_idx] = []
            positions = list(range(self.ROAD_LEN))
            random.shuffle(positions)
            n_cars = int(self.ROAD_LEN * self.density)
            chosen = sorted(positions[:n_cars])
            for pos in chosen:
                self.lanes[lane_idx].append([pos, random.randint(0, self.V_MAX)])

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.up_pressed:
            self.density = min(0.60, self.density + 0.05)
            self._populate()
            consumed = True

        if input_state.down_pressed:
            self.density = max(0.05, self.density - 0.05)
            self._populate()
            consumed = True

        if input_state.right_pressed:
            self.p_slow = min(0.9, self.p_slow + 0.1)
            consumed = True

        if input_state.left_pressed:
            self.p_slow = max(0.0, self.p_slow - 0.1)
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt
        self.step_timer += dt
        if self.step_timer >= self.step_interval:
            self.step_timer -= self.step_interval
            self._step()
            # Scroll viewport
            self.viewport = (self.viewport + 1) % self.ROAD_LEN

    def _step(self):
        """One NaSch timestep for all lanes."""
        for lane in self.lanes:
            if not lane:
                continue
            n = len(lane)
            # Build occupied set for gap calculation
            occupied = set(car[0] for car in lane)

            for i in range(n):
                pos, v = lane[i]

                # 1. Accelerate
                v = min(v + 1, self.V_MAX)

                # 2. Brake: find gap to next car ahead
                gap = 1
                while gap <= self.V_MAX:
                    if (pos + gap) % self.ROAD_LEN in occupied and gap <= v:
                        break
                    gap += 1
                if gap <= v:
                    v = gap - 1

                # 3. Random slow
                if v > 0 and random.random() < self.p_slow:
                    v -= 1

                lane[i][1] = v

            # 4. Move
            for car in lane:
                car[0] = (car[0] + car[1]) % self.ROAD_LEN

    def draw(self):
        self.display.clear((30, 30, 30))

        vp = int(self.viewport)

        # Lane geometry: 5 lanes centered vertically
        # Each lane is 8px tall (6 road + 2 gap), lanes from y=12 to y=51
        lane_height = 8
        first_lane_y = (GRID_SIZE - self.NUM_LANES * lane_height) // 2

        for lane_idx in range(self.NUM_LANES):
            lane_y = first_lane_y + lane_idx * lane_height

            # Draw road surface for this lane
            for row in range(lane_height - 1):
                y = lane_y + row
                if 0 <= y < GRID_SIZE:
                    for x in range(GRID_SIZE):
                        self.display.set_pixel(x, y, self.ROAD_BG)

            # Lane dashes (between lanes)
            if lane_idx < self.NUM_LANES - 1:
                dash_y = lane_y + lane_height - 1
                if 0 <= dash_y < GRID_SIZE:
                    for x in range(GRID_SIZE):
                        if (x + vp) % 8 < 4:
                            self.display.set_pixel(x, dash_y, self.LANE_DASH)
                        else:
                            self.display.set_pixel(x, dash_y, self.ROAD_BG)

            # Draw cars
            car_y = lane_y + (lane_height - 1) // 2
            for pos, vel in self.lanes[lane_idx]:
                screen_x = (pos - vp) % self.ROAD_LEN
                if 0 <= screen_x < GRID_SIZE:
                    color = speed_color(vel, self.V_MAX)
                    if 0 <= car_y < GRID_SIZE:
                        self.display.set_pixel(screen_x, car_y, color)
                        # Car is 2px wide
                        if 0 <= screen_x - 1 < GRID_SIZE:
                            self.display.set_pixel(screen_x - 1, car_y, color)

        # Shoulder lines
        top_shoulder = first_lane_y - 1
        bot_shoulder = first_lane_y + self.NUM_LANES * lane_height
        for x in range(GRID_SIZE):
            if 0 <= top_shoulder < GRID_SIZE:
                self.display.set_pixel(x, top_shoulder, self.SHOULDER)
            if 0 <= bot_shoulder < GRID_SIZE:
                self.display.set_pixel(x, bot_shoulder, self.SHOULDER)
