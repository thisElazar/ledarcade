"""
Signals - NEMA Signal Phasing Intersection
============================================
4-way intersection with real NEMA-style signal phases.
NS green -> yellow -> all-red -> EW green -> yellow -> all-red.
Cars queue at red lights and stream through on green.

Controls:
  Space    - Toggle protected left turns
  Up/Down  - Adjust cycle length
"""

import random
import math
from . import Visual, Display, Colors, GRID_SIZE


# Signal states
SIG_GREEN = 0
SIG_YELLOW = 1
SIG_RED = 2

# Directions
DIR_N = 0
DIR_S = 1
DIR_E = 2
DIR_W = 3

# Road geometry
CENTER = GRID_SIZE // 2   # 32
ROAD_W = 14               # Road width
HALF_W = ROAD_W // 2      # 7


class Intersection(Visual):
    name = "SIGNALS"
    description = "NEMA signal phasing"
    category = "road_rail"

    ROAD_COLOR = (50, 50, 55)
    LANE_DASH = (80, 70, 20)
    CROSSWALK = (80, 80, 85)
    GROUND = (35, 50, 35)

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.cycle_length = 8.0  # Total cycle in seconds
        self.protected_lefts = False
        self.phase_timer = 0.0

        # Phase durations (fractions of cycle)
        self._build_phases()

        # Cars: list of dicts with pos, direction, speed, waiting
        self.cars = []
        self.spawn_timers = {DIR_N: 0, DIR_S: 0, DIR_E: 0, DIR_W: 0}

    def _build_phases(self):
        """Build signal phase list based on cycle length."""
        if self.protected_lefts:
            # NS left -> NS thru -> EW left -> EW thru
            g = self.cycle_length * 0.30
            y = 0.6
            ar = 0.3
            self.phases = [
                ('NS', SIG_GREEN, g),
                ('NS', SIG_YELLOW, y),
                ('ALL', SIG_RED, ar),
                ('EW', SIG_GREEN, g),
                ('EW', SIG_YELLOW, y),
                ('ALL', SIG_RED, ar),
            ]
        else:
            g = self.cycle_length * 0.40
            y = 0.6
            ar = 0.3
            self.phases = [
                ('NS', SIG_GREEN, g),
                ('NS', SIG_YELLOW, y),
                ('ALL', SIG_RED, ar),
                ('EW', SIG_GREEN, g),
                ('EW', SIG_YELLOW, y),
                ('ALL', SIG_RED, ar),
            ]
        self.total_cycle = sum(p[2] for p in self.phases)

    def _get_signal(self, direction):
        """Get current signal state for a direction."""
        t = self.phase_timer % self.total_cycle
        elapsed = 0
        for axis, state, dur in self.phases:
            if t < elapsed + dur:
                if axis == 'ALL':
                    return SIG_RED
                is_ns = direction in (DIR_N, DIR_S)
                if (axis == 'NS' and is_ns) or (axis == 'EW' and not is_ns):
                    return state
                else:
                    return SIG_RED
            elapsed += dur
        return SIG_RED

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.action_l or input_state.action_r:
            self.protected_lefts = not self.protected_lefts
            self._build_phases()
            consumed = True

        if input_state.up_pressed:
            self.cycle_length = min(16.0, self.cycle_length + 1.0)
            self._build_phases()
            consumed = True

        if input_state.down_pressed:
            self.cycle_length = max(4.0, self.cycle_length - 1.0)
            self._build_phases()
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt
        self.phase_timer += dt

        # Spawn cars (fixed interval per direction)
        for d in [DIR_N, DIR_S, DIR_E, DIR_W]:
            self.spawn_timers[d] += dt
            if self.spawn_timers[d] >= 0.8:
                self.spawn_timers[d] = 0
                self._spawn_car(d)

        # Update cars
        for car in self.cars:
            self._update_car(car, dt)

        # Remove off-screen cars
        self.cars = [c for c in self.cars if self._on_screen(c)]

    def _spawn_car(self, direction):
        """Spawn a car approaching from given direction."""
        lane_offset = random.choice([1, 3])
        colors = [
            (255, 60, 60), (60, 120, 255), (255, 255, 80),
            (80, 255, 80), (255, 140, 60), (200, 80, 255),
            (255, 255, 255), (80, 255, 200),
        ]
        color = random.choice(colors)

        if direction == DIR_N:
            x = CENTER + lane_offset
            y = float(GRID_SIZE + 2)
        elif direction == DIR_S:
            x = CENTER - lane_offset
            y = -3.0
        elif direction == DIR_E:
            x = -3.0
            y = CENTER + lane_offset
        elif direction == DIR_W:
            x = float(GRID_SIZE + 2)
            y = CENTER - lane_offset

        # Don't spawn if another same-direction car is near the entry
        for other in self.cars:
            if other['dir'] != direction:
                continue
            if direction in (DIR_N, DIR_S):
                if abs(other['x'] - x) <= 1:
                    if direction == DIR_N and other['y'] > GRID_SIZE - 5:
                        return
                    if direction == DIR_S and other['y'] < 5:
                        return
            else:
                if abs(other['y'] - y) <= 1:
                    if direction == DIR_E and other['x'] < 5:
                        return
                    if direction == DIR_W and other['x'] > GRID_SIZE - 5:
                        return

        self.cars.append({'x': float(x), 'y': float(y), 'dir': direction,
                          'speed': 20.0, 'color': color})

    def _update_car(self, car, dt):
        """Update a car's position, braking at red lights."""
        d = car['dir']
        sig = self._get_signal(d)

        # Stop line positions
        stop_lines = {
            DIR_N: CENTER + HALF_W + 1,
            DIR_S: CENTER - HALF_W - 2,
            DIR_E: CENTER - HALF_W - 2,
            DIR_W: CENTER + HALF_W + 1,
        }
        stop = stop_lines[d]

        # Cars already past the stop line / in the intersection always proceed
        in_intersection = (CENTER - HALF_W <= car['x'] <= CENTER + HALF_W and
                           CENTER - HALF_W <= car['y'] <= CENTER + HALF_W)
        past_stop = False
        if d == DIR_N and car['y'] <= stop:
            past_stop = True
        elif d == DIR_S and car['y'] >= stop:
            past_stop = True
        elif d == DIR_E and car['x'] >= stop:
            past_stop = True
        elif d == DIR_W and car['x'] <= stop:
            past_stop = True

        should_stop = False

        # Red/yellow light: only stop if approaching (not past stop line)
        if not past_stop and sig != SIG_GREEN:
            if d == DIR_N and car['y'] > stop and car['y'] < stop + 14:
                should_stop = True
            elif d == DIR_S and car['y'] < stop and car['y'] > stop - 14:
                should_stop = True
            elif d == DIR_E and car['x'] < stop and car['x'] > stop - 14:
                should_stop = True
            elif d == DIR_W and car['x'] > stop and car['x'] < stop + 14:
                should_stop = True

        # Lane-aware following distance (same direction AND same lane)
        if not should_stop:
            for other in self.cars:
                if other is car or other['dir'] != d:
                    continue
                # Same lane check
                if d in (DIR_N, DIR_S):
                    if abs(other['x'] - car['x']) > 1:
                        continue
                else:
                    if abs(other['y'] - car['y']) > 1:
                        continue
                gap = 999
                if d == DIR_N and other['y'] < car['y']:
                    gap = car['y'] - other['y']
                elif d == DIR_S and other['y'] > car['y']:
                    gap = other['y'] - car['y']
                elif d == DIR_E and other['x'] > car['x']:
                    gap = other['x'] - car['x']
                elif d == DIR_W and other['x'] < car['x']:
                    gap = car['x'] - other['x']
                if gap < 4:
                    should_stop = True
                    break

        if should_stop:
            speed = 0.0
        else:
            speed = car['speed']

        if d == DIR_N:
            car['y'] -= speed * dt
        elif d == DIR_S:
            car['y'] += speed * dt
        elif d == DIR_E:
            car['x'] += speed * dt
        elif d == DIR_W:
            car['x'] -= speed * dt

    def _on_screen(self, car):
        return -5 < car['x'] < GRID_SIZE + 5 and -5 < car['y'] < GRID_SIZE + 5

    def draw(self):
        # Ground
        self.display.clear(self.GROUND)

        # NS road
        for y in range(GRID_SIZE):
            for x in range(CENTER - HALF_W, CENTER + HALF_W):
                if 0 <= x < GRID_SIZE:
                    self.display.set_pixel(x, y, self.ROAD_COLOR)

        # EW road
        for y in range(CENTER - HALF_W, CENTER + HALF_W):
            for x in range(GRID_SIZE):
                if 0 <= y < GRID_SIZE:
                    self.display.set_pixel(x, y, self.ROAD_COLOR)

        # Center lane dashes (NS road, outside intersection)
        for y in range(GRID_SIZE):
            if CENTER - HALF_W <= y < CENTER + HALF_W:
                continue  # Skip intersection
            if y % 4 < 2:
                self.display.set_pixel(CENTER, y, self.LANE_DASH)

        # Center lane dashes (EW road, outside intersection)
        for x in range(GRID_SIZE):
            if CENTER - HALF_W <= x < CENTER + HALF_W:
                continue
            if x % 4 < 2:
                self.display.set_pixel(x, CENTER, self.LANE_DASH)

        # Crosswalk markings
        for i in range(0, ROAD_W, 3):
            # North crosswalk
            cx = CENTER - HALF_W + i
            cy = CENTER - HALF_W - 1
            if 0 <= cx < GRID_SIZE and 0 <= cy < GRID_SIZE:
                self.display.set_pixel(cx, cy, self.CROSSWALK)
            # South crosswalk
            cy = CENTER + HALF_W
            if 0 <= cx < GRID_SIZE and 0 <= cy < GRID_SIZE:
                self.display.set_pixel(cx, cy, self.CROSSWALK)
            # East crosswalk
            cx = CENTER + HALF_W
            cy2 = CENTER - HALF_W + i
            if 0 <= cx < GRID_SIZE and 0 <= cy2 < GRID_SIZE:
                self.display.set_pixel(cx, cy2, self.CROSSWALK)
            # West crosswalk
            cx = CENTER - HALF_W - 1
            if 0 <= cx < GRID_SIZE and 0 <= cy2 < GRID_SIZE:
                self.display.set_pixel(cx, cy2, self.CROSSWALK)

        # Signal heads (small 1x3 blocks at each corner)
        self._draw_signal_head(CENTER - HALF_W - 3, CENTER - HALF_W - 3, DIR_S)
        self._draw_signal_head(CENTER + HALF_W + 1, CENTER + HALF_W + 1, DIR_N)
        self._draw_signal_head(CENTER + HALF_W + 1, CENTER - HALF_W - 3, DIR_W)
        self._draw_signal_head(CENTER - HALF_W - 3, CENTER + HALF_W + 1, DIR_E)

        # Cars
        for car in self.cars:
            cx = int(car['x'])
            cy = int(car['y'])
            if 0 <= cx < GRID_SIZE and 0 <= cy < GRID_SIZE:
                self.display.set_pixel(cx, cy, car['color'])
                # 2px car body
                if car['dir'] in (DIR_N, DIR_S):
                    if 0 <= cy - 1 < GRID_SIZE:
                        self.display.set_pixel(cx, cy - 1, car['color'])
                else:
                    if 0 <= cx + 1 < GRID_SIZE:
                        self.display.set_pixel(cx + 1, cy, car['color'])

    def _draw_signal_head(self, x, y, direction):
        """Draw a signal head (R/Y/G stack)."""
        sig = self._get_signal(direction)
        colors = {
            SIG_RED: ((255, 0, 0), (60, 60, 0), (0, 60, 0)),
            SIG_YELLOW: ((60, 0, 0), (255, 255, 0), (0, 60, 0)),
            SIG_GREEN: ((60, 0, 0), (60, 60, 0), (0, 255, 0)),
        }
        r, ye, g = colors[sig]
        if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
            self.display.set_pixel(x, y, r)
        if 0 <= x < GRID_SIZE and 0 <= y + 1 < GRID_SIZE:
            self.display.set_pixel(x, y + 1, ye)
        if 0 <= x < GRID_SIZE and 0 <= y + 2 < GRID_SIZE:
            self.display.set_pixel(x, y + 2, g)
