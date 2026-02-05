"""
Rotary - Roundabout with Gap Acceptance
=========================================
Vehicles approach from 4 directions, yield at entry by scanning
for gaps in circulating traffic (critical gap ~1.5s). Once entered,
vehicles circulate counterclockwise and exit at their destination leg.

Controls:
  Up/Down - Adjust traffic volume
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE


CENTER_X = 32
CENTER_Y = 32
ISLAND_R = 8      # Central island radius
ROAD_R = 14       # Outer edge of circulatory road
APPROACH_W = 6    # Approach road width

# Entry/exit angles (radians, 0=east, CCW positive)
LEGS = [0, math.pi / 2, math.pi, 3 * math.pi / 2]  # E, N, W, S
LEG_NAMES = ['E', 'N', 'W', 'S']

# Approach road endpoints (outside the roundabout)
APPROACH_DIRS = [
    (1, 0),    # East
    (0, -1),   # North
    (-1, 0),   # West
    (0, 1),    # South
]


class Roundabout(Visual):
    name = "ROTARY"
    description = "Roundabout gap acceptance"
    category = "road_rail"

    ISLAND_COLOR = (30, 70, 30)
    ROAD_COLOR = (55, 55, 60)
    CURB_COLOR = (90, 90, 80)
    APPROACH_COLOR = (50, 50, 55)
    GROUND = (35, 50, 35)
    YIELD_COLOR = (255, 255, 200)

    CAR_COLORS = [
        (255, 60, 60), (60, 120, 255), (255, 255, 80),
        (80, 255, 80), (255, 140, 60), (200, 80, 255),
        (255, 200, 200), (80, 255, 200),
    ]

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.spawn_rate = 1.5  # Cars per second total (all approaches)
        self.spawn_timer = 0.0

        # Circulating vehicles: angle, angular_speed, exit_leg, color
        self.circ_cars = []
        # Approaching vehicles: leg_index, distance (positive = farther), target_exit, color
        self.approach_cars = []

        self.circ_speed = 1.8  # radians/sec
        self.critical_gap = 1.2  # seconds worth of angular gap

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.up_pressed:
            self.spawn_rate = min(4.0, self.spawn_rate + 0.3)
            consumed = True
        if input_state.down_pressed:
            self.spawn_rate = max(0.3, self.spawn_rate - 0.3)
            consumed = True
        return consumed

    def update(self, dt: float):
        self.time += dt

        # Spawn approaching cars
        self.spawn_timer += dt
        if self.spawn_timer >= 1.0 / max(0.1, self.spawn_rate):
            self.spawn_timer = 0
            leg = random.randint(0, 3)
            # Pick a different exit
            exit_leg = (leg + random.choice([1, 2, 3])) % 4
            color = random.choice(self.CAR_COLORS)
            self.approach_cars.append({
                'leg': leg,
                'dist': 28.0,
                'exit': exit_leg,
                'color': color,
                'waiting': False,
            })

        # Update approaching cars
        for car in self.approach_cars:
            yield_dist = ROAD_R + 1
            if car['dist'] > yield_dist:
                car['dist'] -= 18.0 * dt
                car['waiting'] = False
            else:
                # At yield point - check for gap
                car['dist'] = max(yield_dist, car['dist'] - 18.0 * dt)
                entry_angle = LEGS[car['leg']]
                if self._check_gap(entry_angle):
                    # Enter roundabout
                    self.circ_cars.append({
                        'angle': entry_angle,
                        'exit': car['exit'],
                        'color': car['color'],
                    })
                    car['dist'] = -999  # Mark for removal
                else:
                    car['waiting'] = True

        self.approach_cars = [c for c in self.approach_cars if c['dist'] > -100]

        # Update circulating cars
        for car in self.circ_cars:
            car['angle'] = (car['angle'] + self.circ_speed * dt) % (2 * math.pi)

        # Check exits
        new_circ = []
        for car in self.circ_cars:
            exit_angle = LEGS[car['exit']]
            diff = abs(car['angle'] - exit_angle)
            if diff > math.pi:
                diff = 2 * math.pi - diff
            if diff < 0.15:
                # Exit - spawn departing (just remove for simplicity)
                continue
            new_circ.append(car)
        self.circ_cars = new_circ

        # Cap circulating to avoid overcrowding
        if len(self.circ_cars) > 20:
            self.circ_cars = self.circ_cars[-20:]

    def _check_gap(self, entry_angle):
        """Check if there's a sufficient gap at the entry angle."""
        gap_angle = self.critical_gap * self.circ_speed  # angular gap needed
        for car in self.circ_cars:
            # How far behind entry is this car? (CCW direction)
            diff = (entry_angle - car['angle']) % (2 * math.pi)
            if diff < gap_angle:
                return False
        return True

    def draw(self):
        self.display.clear(self.GROUND)

        # Draw approach roads
        for i, (dx, dy) in enumerate(APPROACH_DIRS):
            half = APPROACH_W // 2
            if dx != 0:
                # Horizontal road
                start_x = CENTER_X + (ROAD_R if dx > 0 else -GRID_SIZE)
                end_x = CENTER_X + (GRID_SIZE if dx > 0 else -ROAD_R)
                for x in range(max(0, start_x), min(GRID_SIZE, end_x)):
                    for y in range(CENTER_Y - half, CENTER_Y + half):
                        if 0 <= y < GRID_SIZE:
                            self.display.set_pixel(x, y, self.APPROACH_COLOR)
            else:
                # Vertical road
                start_y = CENTER_Y + (ROAD_R if dy > 0 else -GRID_SIZE)
                end_y = CENTER_Y + (GRID_SIZE if dy > 0 else -ROAD_R)
                for y in range(max(0, start_y), min(GRID_SIZE, end_y)):
                    for x in range(CENTER_X - half, CENTER_X + half):
                        if 0 <= x < GRID_SIZE:
                            self.display.set_pixel(x, y, self.APPROACH_COLOR)

        # Draw circulatory road (ring)
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                dx = x - CENTER_X
                dy = y - CENTER_Y
                dist = math.sqrt(dx * dx + dy * dy)
                if ISLAND_R < dist <= ROAD_R:
                    self.display.set_pixel(x, y, self.ROAD_COLOR)
                elif abs(dist - ISLAND_R) < 0.8:
                    self.display.set_pixel(x, y, self.CURB_COLOR)
                elif abs(dist - ROAD_R) < 0.8:
                    self.display.set_pixel(x, y, self.CURB_COLOR)

        # Draw central island
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                dx = x - CENTER_X
                dy = y - CENTER_Y
                if dx * dx + dy * dy <= ISLAND_R * ISLAND_R:
                    self.display.set_pixel(x, y, self.ISLAND_COLOR)

        # Draw yield triangles at entries
        for i in range(4):
            angle = LEGS[i]
            yx = int(CENTER_X + (ROAD_R + 1) * math.cos(angle))
            yy = int(CENTER_Y - (ROAD_R + 1) * math.sin(angle))
            if 0 <= yx < GRID_SIZE and 0 <= yy < GRID_SIZE:
                self.display.set_pixel(yx, yy, self.YIELD_COLOR)

        # Draw circulating cars
        ring_mid = (ISLAND_R + ROAD_R) / 2
        for car in self.circ_cars:
            cx = int(CENTER_X + ring_mid * math.cos(car['angle']))
            cy = int(CENTER_Y - ring_mid * math.sin(car['angle']))
            if 0 <= cx < GRID_SIZE and 0 <= cy < GRID_SIZE:
                self.display.set_pixel(cx, cy, car['color'])
                # 2px dot
                cx2 = int(CENTER_X + (ring_mid - 1) * math.cos(car['angle']))
                cy2 = int(CENTER_Y - (ring_mid - 1) * math.sin(car['angle']))
                if 0 <= cx2 < GRID_SIZE and 0 <= cy2 < GRID_SIZE:
                    self.display.set_pixel(cx2, cy2, car['color'])

        # Draw approaching cars
        for car in self.approach_cars:
            leg = car['leg']
            dx, dy = APPROACH_DIRS[leg]
            dist = car['dist']
            cx = int(CENTER_X + dx * dist)
            cy = int(CENTER_Y + dy * dist)
            if 0 <= cx < GRID_SIZE and 0 <= cy < GRID_SIZE:
                color = car['color']
                if car['waiting']:
                    # Flash when waiting
                    if int(self.time * 4) % 2 == 0:
                        color = (255, 200, 100)
                self.display.set_pixel(cx, cy, color)
