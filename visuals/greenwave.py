"""
Green Wave - Signal Coordination
==================================
Vertical corridor with 7 signalized intersections. Signal offsets
timed so a platoon at target speed hits green at every signal.
Based on FHWA signal coordination principles.

Optional toggle to time-space diagram view.

Controls:
  Up/Down  - Adjust platoon speed
  Space    - Toggle time-space diagram view
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE


NUM_SIGNALS = 7
ROAD_X = 32           # Center of main corridor
ROAD_W = 8            # Corridor width
CROSS_W = 4           # Cross-street width

# Signal colors
SIG_GREEN = (0, 220, 0)
SIG_YELLOW = (255, 255, 0)
SIG_RED = (255, 0, 0)
SIG_DIM_GREEN = (0, 60, 0)
SIG_DIM_RED = (60, 0, 0)


class GreenWave(Visual):
    name = "GREENWAVE"
    description = "Signal coordination"
    category = "road_rail"

    ROAD_COLOR = (50, 50, 55)
    CROSS_COLOR = (45, 45, 50)
    LANE_DASH = (80, 70, 20)
    GROUND = (30, 40, 30)

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed = 24.0  # pixels/sec platoon speed
        self.cycle_length = 6.0
        self.green_fraction = 0.55
        self.diagram_mode = False

        # Signal positions (evenly spaced top to bottom)
        margin = 6
        spacing = (GRID_SIZE - 2 * margin) / (NUM_SIGNALS - 1)
        self.signal_ys = [int(margin + i * spacing) for i in range(NUM_SIGNALS)]

        # Compute offsets so platoon hits green
        self._compute_offsets()

        # Platoon vehicles: y position, speed
        self.platoon = []
        self.spawn_timer = 0.0

        # Cross traffic
        self.cross_cars = []
        self.cross_timer = 0.0

        # Time-space diagram history
        self.ts_history = []

    def _compute_offsets(self):
        """Compute signal offsets for green wave at current speed."""
        self.offsets = []
        base_y = self.signal_ys[0]
        for sy in self.signal_ys:
            dist = sy - base_y
            if self.speed > 0:
                offset = (dist / self.speed) % self.cycle_length
            else:
                offset = 0
            self.offsets.append(offset)

    def _signal_state(self, signal_idx):
        """Get state of signal: 'green', 'yellow', or 'red'."""
        offset = self.offsets[signal_idx]
        phase = (self.time - offset) % self.cycle_length
        green_dur = self.cycle_length * self.green_fraction
        yellow_dur = 0.5
        if phase < green_dur:
            return 'green'
        elif phase < green_dur + yellow_dur:
            return 'yellow'
        else:
            return 'red'

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.up_pressed:
            self.speed = min(50.0, self.speed + 4.0)
            self._compute_offsets()
            consumed = True
        if input_state.down_pressed:
            self.speed = max(8.0, self.speed - 4.0)
            self._compute_offsets()
            consumed = True
        if input_state.action_l or input_state.action_r:
            self.diagram_mode = not self.diagram_mode
            if self.diagram_mode:
                self.ts_history = []
            consumed = True
        return consumed

    def update(self, dt: float):
        self.time += dt

        # Spawn platoon vehicles from top
        self.spawn_timer += dt
        if self.spawn_timer >= 0.3:
            self.spawn_timer = 0
            # Random lane offset
            lx = ROAD_X + random.choice([-2, -1, 1, 2])
            self.platoon.append({
                'x': lx, 'y': -2.0,
                'speed': self.speed + random.uniform(-2, 2),
                'color': (200, 220, 255),
            })

        # Update platoon
        for car in self.platoon:
            # Check if should stop at red
            stopped = False
            for i, sy in enumerate(self.signal_ys):
                state = self._signal_state(i)
                if state == 'red':
                    if sy - 3 < car['y'] < sy - 1:
                        stopped = True
                        break
            if not stopped:
                car['y'] += car['speed'] * dt

        self.platoon = [c for c in self.platoon if c['y'] < GRID_SIZE + 5]

        # Cross traffic
        self.cross_timer += dt
        if self.cross_timer >= 0.8:
            self.cross_timer = 0
            sig_idx = random.randint(0, NUM_SIGNALS - 1)
            state = self._signal_state(sig_idx)
            if state == 'red':  # Cross traffic goes on main-red
                sy = self.signal_ys[sig_idx]
                direction = random.choice([-1, 1])
                self.cross_cars.append({
                    'x': -2.0 if direction > 0 else GRID_SIZE + 2.0,
                    'y': sy,
                    'dx': direction,
                    'speed': random.uniform(15, 25),
                    'color': (255, 160, 80),
                })

        for car in self.cross_cars:
            car['x'] += car['dx'] * car['speed'] * dt
        self.cross_cars = [c for c in self.cross_cars if -5 < c['x'] < GRID_SIZE + 5]

        # Record time-space data
        if self.diagram_mode:
            row = [0] * GRID_SIZE
            for i, sy in enumerate(self.signal_ys):
                state = self._signal_state(i)
                if state == 'green':
                    row[sy] = 1
                elif state == 'yellow':
                    row[sy] = 2
                else:
                    row[sy] = 3
            for car in self.platoon:
                yi = int(car['y'])
                if 0 <= yi < GRID_SIZE:
                    row[yi] = 4
            self.ts_history.append(row)
            if len(self.ts_history) > GRID_SIZE:
                self.ts_history.pop(0)

    def draw(self):
        if self.diagram_mode:
            self._draw_diagram()
        else:
            self._draw_map()

    def _draw_map(self):
        """Draw the overhead corridor view."""
        self.display.clear(self.GROUND)

        # Main corridor
        for y in range(GRID_SIZE):
            for x in range(ROAD_X - ROAD_W // 2, ROAD_X + ROAD_W // 2):
                if 0 <= x < GRID_SIZE:
                    self.display.set_pixel(x, y, self.ROAD_COLOR)

        # Center dashes
        for y in range(GRID_SIZE):
            skip = False
            for sy in self.signal_ys:
                if abs(y - sy) <= CROSS_W // 2:
                    skip = True
            if not skip and y % 4 < 2:
                self.display.set_pixel(ROAD_X, y, self.LANE_DASH)

        # Cross streets and signals
        for i, sy in enumerate(self.signal_ys):
            state = self._signal_state(i)

            # Cross street
            for x in range(GRID_SIZE):
                for dy in range(-CROSS_W // 2, CROSS_W // 2):
                    y = sy + dy
                    if 0 <= y < GRID_SIZE:
                        if not (ROAD_X - ROAD_W // 2 <= x < ROAD_X + ROAD_W // 2):
                            self.display.set_pixel(x, y, self.CROSS_COLOR)

            # Signal heads on both sides of corridor
            if state == 'green':
                sc = SIG_GREEN
            elif state == 'yellow':
                sc = SIG_YELLOW
            else:
                sc = SIG_RED

            lx = ROAD_X - ROAD_W // 2 - 1
            rx = ROAD_X + ROAD_W // 2
            if 0 <= lx < GRID_SIZE and 0 <= sy < GRID_SIZE:
                self.display.set_pixel(lx, sy, sc)
            if 0 <= rx < GRID_SIZE and 0 <= sy < GRID_SIZE:
                self.display.set_pixel(rx, sy, sc)

        # Platoon cars
        for car in self.platoon:
            cx, cy = int(car['x']), int(car['y'])
            if 0 <= cx < GRID_SIZE and 0 <= cy < GRID_SIZE:
                self.display.set_pixel(cx, cy, car['color'])

        # Cross traffic
        for car in self.cross_cars:
            cx, cy = int(car['x']), int(car['y'])
            if 0 <= cx < GRID_SIZE and 0 <= cy < GRID_SIZE:
                self.display.set_pixel(cx, cy, car['color'])

    def _draw_diagram(self):
        """Draw time-space diagram: x=time, y=space (position along corridor)."""
        self.display.clear(Colors.BLACK)

        # Map colors for diagram
        colors = {
            0: (15, 15, 15),       # Background
            1: (0, 80, 0),         # Green signal
            2: (80, 80, 0),        # Yellow signal
            3: (80, 0, 0),         # Red signal
            4: (200, 220, 255),    # Vehicle
        }

        for x, row in enumerate(self.ts_history):
            for y in range(GRID_SIZE):
                val = row[y] if y < len(row) else 0
                color = colors.get(val, (15, 15, 15))
                if 0 <= x < GRID_SIZE:
                    self.display.set_pixel(x, y, color)

        self.display.draw_text_small(2, 1, "T-S", (180, 180, 180))
