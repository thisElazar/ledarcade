"""
Night Driver - Arcade Racing
=============================
A 90-second timed run through the dark. Only the roadside posts
and oncoming headlights are visible - the sparse night look IS the game.
Crashes stall you for 2 seconds; the run only ends when the clock does.

Controls:
  Left/Right - Steer (and choose course before start)
  Up/Down    - Shift gear (1-4)
  Space      - Gas (hold)
"""

from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE
import math
import random


class NightDriver(Game):
    name = "NITE DRIVER"
    description = "Night Racing"
    category = "arcade"
    GUIDE = {
        'desc': 'A 90-second timed run inspired by one of the earliest first-person driving games: only white posts and oncoming headlights pierce the dark. Pick NOVICE, PRO, or EXPERT - each is a fixed curve script, not random. Shift up through 4 gears to build speed; the road visibly swings in turns and drifting off it costs a 2-second stall. Score is distance; 4000 earns +15 seconds. The run ends only at 0:00.',
    }

    # Road parameters
    HORIZON_Y = 20          # Y position of vanishing point
    ROAD_BOTTOM_Y = 62      # Bottom of visible road
    VANISHING_X = 32        # X position of vanishing point (center)

    # Road width at bottom and top (perspective)
    ROAD_WIDTH_BOTTOM = 50
    ROAD_WIDTH_TOP = 8

    # Post spacing
    NUM_POSTS = 8           # Number of post pairs visible
    POST_SPACING = 1.0      # Distance between posts (in world units)

    # Player car
    CAR_Y = 56
    CAR_WIDTH = 8
    CAR_HEIGHT = 6

    # Colors
    POST_COLOR = (255, 255, 255)
    CAR_COLOR = (200, 50, 50)
    CAR_WINDOW = (100, 150, 200)

    # Oncoming traffic colors
    ONCOMING_CAR_COLOR = (255, 200, 50)  # Yellow/orange headlights

    # Vehicle types with different sizes (width_mult, headlight_sep_mult)
    # Only their headlight pairs are ever drawn — bodies stay invisible at night
    VEHICLE_TYPES = [
        {'name': 'sedan', 'width': 1.0, 'hl_sep': 1.0, 'weight': 40},
        {'name': 'compact', 'width': 0.8, 'hl_sep': 0.8, 'weight': 20},
        {'name': 'suv', 'width': 1.2, 'hl_sep': 1.2, 'weight': 20},
        {'name': 'pickup', 'width': 1.1, 'hl_sep': 1.0, 'weight': 15},
        {'name': 'semi', 'width': 1.4, 'hl_sep': 1.3, 'weight': 5},  # 18-wheeler
    ]

    # Turn types
    TURN_NORMAL = 0
    TURN_HAIRPIN = 1      # Sharp turn (|curve| >= 3)

    # Timed-run structure
    RUN_TIME = 90.0         # Seconds on the clock
    CRASH_STALL = 2.0       # Seconds lost standing still after a crash
    EXTEND_SCORE = 4000     # Distance that earns bonus time (once)
    EXTEND_BONUS = 15.0

    # Gearbox: top speed per gear
    GEAR_CAPS = [30.0, 55.0, 85.0, 120.0]

    # Courses: fixed curve scripts as (straight_secs, base_curve, duration).
    # The script loops; harder courses have sharper turns and shorter breathers.
    COURSES = ['NOVICE', 'PRO', 'EXPERT']
    CURVE_SCRIPTS = {
        'NOVICE': [
            (2.5, -1.0, 2.0), (2.0, 1.2, 2.2), (2.5, -1.5, 2.0),
            (3.0, 1.0, 2.5), (2.0, -1.2, 2.0), (2.5, 1.5, 2.2),
        ],
        'PRO': [
            (2.0, -1.5, 2.0), (1.5, 2.0, 2.2), (2.0, -2.5, 2.0),
            (0.5, 2.5, 1.5), (1.5, -2.0, 2.5), (1.0, 1.5, 1.8),
            (0.4, -1.5, 1.8),
        ],
        'EXPERT': [
            (1.5, -2.0, 1.8), (1.0, 3.0, 2.5), (0.4, -3.0, 1.2),
            (0.4, 3.0, 1.2), (1.2, -2.5, 2.0), (0.8, 3.5, 2.8),
            (1.0, -3.5, 2.5), (0.4, 2.0, 1.0),
        ],
    }

    def __init__(self, display: Display):
        super().__init__(display)
        self.course = 0
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0

        # Course select screen before the run starts
        self.started = False

        # Run clock
        self.time_left = self.RUN_TIME
        self.extend_awarded = False
        self.extend_flash = 0.0

        # Player position (-1.0 to 1.0, 0 = center of screen)
        self.player_x = 0.0

        # Where the near-field road center currently sits (lags the curve so
        # the posts visibly swing at you in a turn — this drives collision)
        self.road_center = 0.0

        # Speed and distance
        self.gear = 1
        self.speed = 25.0       # Units per second
        self.max_speed = 120.0  # Top speed (gear 4)
        self.base_speed = 25.0  # Coast speed (no gas) - rises over time
        self.distance = 0.0     # Total distance traveled
        self.gas = False        # Whether gas button is held

        # Post positions (0.0 to POST_SPACING, cycles)
        self.post_offset = 0.0

        # Road curve system - scripted turns
        self.curve = 0.0           # Current curve amount
        self.target_curve = 0.0    # Where we're curving toward
        self.turn_duration = 0.0   # How long current turn lasts
        self.turn_timer = 0.0      # Time in current turn
        self.straight_timer = 0.0  # Time until next turn
        self.curve_intensity = 1.0 # Multiplier for curve tightness (rises with speed)
        self.current_turn_type = self.TURN_NORMAL
        self.script_index = 0      # Position in the course's curve script

        # Start with a short straight — pre-plan the first turn
        self.next_turn = self.plan_next_turn()
        self.straight_timer = 2.0

        # Crash state (a stall, not the end of the run)
        self.crashed = False
        self.crash_timer = 0.0

        # Oncoming traffic
        # Each car: {'z': distance (1.0=horizon, 0.0=at player), 'lane': lane offset}
        self.oncoming_cars = []
        self.next_car_timer = 3.0  # Time until next car spawns
        self.min_car_interval = 1.5  # Minimum time between cars
        self.max_car_interval = 4.0  # Maximum time between cars

    def update(self, input_state: InputState, dt: float):
        if self.state == GameState.GAME_OVER:
            if (input_state.action_l or input_state.action_r):
                self.reset()
            return

        # Course select screen
        if not self.started:
            if input_state.left_pressed:
                self.course = (self.course - 1) % len(self.COURSES)
            elif input_state.right_pressed:
                self.course = (self.course + 1) % len(self.COURSES)
            if input_state.action_l or input_state.action_r:
                self.script_index = 0
                self.next_turn = self.plan_next_turn()
                self.started = True
            return

        # The clock is the only thing that ends the run — it keeps ticking
        # through crashes
        self.time_left -= dt
        if self.time_left <= 0:
            self.time_left = 0
            self.state = GameState.GAME_OVER
            return
        if self.extend_flash > 0:
            self.extend_flash -= dt

        if self.crashed:
            self.crash_timer -= dt
            if self.crash_timer <= 0:
                # Back on the road, speed reset, run continues
                self.crashed = False
                self.speed = self.base_speed
                self.gear = 1
                self.player_x = self.road_center
                # Clear traffic close enough to instantly re-crash us
                self.oncoming_cars = [c for c in self.oncoming_cars
                                      if c['z'] > 0.35]
            return

        # Gear shift (up/down), capping top speed per gear
        if input_state.up_pressed and self.gear < len(self.GEAR_CAPS):
            self.gear += 1
        if input_state.down_pressed and self.gear > 1:
            self.gear -= 1
        gear_cap = self.GEAR_CAPS[self.gear - 1]

        # Steering - scales slightly with speed so player can handle faster curves
        # Base steer of 2.0, up to 3.5 at max speed
        speed_factor = self.speed / self.max_speed
        steer_speed = 2.0 + speed_factor * 1.5
        if input_state.left:
            self.player_x -= steer_speed * dt
        if input_state.right:
            self.player_x += steer_speed * dt

        # Clamp player position
        self.player_x = max(-1.0, min(1.0, self.player_x))

        # The near-field road swings toward the curve with a lag: in a turn the
        # posts sweep sideways at you, and you crash because one visibly
        # reaches you — not because of an invisible force.
        target_center = max(-0.6, min(0.6, self.curve * 0.22))
        self.road_center += (target_center - self.road_center) * min(1.0, dt * 1.6)

        # Update turn/straight timing
        if self.straight_timer > 0:
            # In a straight section
            self.straight_timer -= dt
            # Ease curve back to zero (frame-rate independent, 0.95/frame at 30fps)
            self.curve *= 0.95 ** (dt * 30.0)
            if self.straight_timer <= 0:
                # Apply the pre-planned turn
                self.apply_next_turn()
        else:
            # In a turn
            self.turn_timer += dt

            # Smoothly approach target curve (faster for hairpins)
            approach_rate = 2.0
            if self.current_turn_type == self.TURN_HAIRPIN:
                approach_rate = 3.0

            diff = self.target_curve - self.curve
            self.curve += diff * dt * approach_rate

            if self.turn_timer >= self.turn_duration:
                # End turn — the script says how long until the next one
                self.next_turn = self.plan_next_turn()
                self.straight_timer = self.next_turn['straight']

        # Gas pedal: hold button to accelerate up to the gear cap,
        # release to coast down to base speed
        self.gas = input_state.action_l_held or input_state.action_r_held
        if self.gas and self.speed < gear_cap:
            self.speed = min(self.speed + 20.0 * dt, gear_cap)
        elif self.speed > gear_cap:
            # Engine braking after a downshift
            self.speed = max(self.speed - 40.0 * dt, gear_cap)
        elif not self.gas:
            self.speed = max(self.speed - 25.0 * dt,
                             min(self.base_speed, gear_cap))

        # Base speed rises slowly over time (game gets harder)
        self.base_speed = min(self.base_speed + 0.25 * dt, 60.0)

        # Difficulty scaling: tighter curves at higher speeds
        # Range: 1.0 to 2.0 multiplier
        self.curve_intensity = 1.0 + speed_factor * 1.0

        # Update distance and post offset
        self.distance += self.speed * dt
        self.post_offset += self.speed * dt * 0.05
        if self.post_offset >= self.POST_SPACING:
            self.post_offset -= self.POST_SPACING

        # Score based on distance
        self.score = int(self.distance)

        # Extended play: big distance earns bonus time, once
        if not self.extend_awarded and self.score >= self.EXTEND_SCORE:
            self.extend_awarded = True
            self.time_left += self.EXTEND_BONUS
            self.extend_flash = 2.0

        # Update oncoming traffic
        self.update_oncoming_traffic(dt)

        # Check collision with posts
        if self.check_collision():
            self.crashed = True
            self.crash_timer = self.CRASH_STALL

        # Check collision with oncoming cars
        if self.check_car_collision():
            self.crashed = True
            self.crash_timer = self.CRASH_STALL

    def plan_next_turn(self):
        """Read the next turn from the course's fixed curve script."""
        script = self.CURVE_SCRIPTS[self.COURSES[self.course]]
        straight, base_curve, duration = script[self.script_index % len(script)]
        self.script_index += 1

        turn_type = (self.TURN_HAIRPIN if abs(base_curve) >= 3.0
                     else self.TURN_NORMAL)
        return {
            'turn_type': turn_type,
            'target_curve': base_curve * self.curve_intensity,
            'turn_duration': duration,
            'straight': straight,
        }

    def apply_next_turn(self):
        """Activate the pre-planned turn."""
        turn = self.next_turn
        if not turn:
            return
        self.current_turn_type = turn['turn_type']
        self.target_curve = turn['target_curve']
        self.turn_duration = turn['turn_duration']
        self.turn_timer = 0.0
        self.next_turn = None

    def check_collision(self) -> bool:
        """Crash when the swinging road actually leaves the player behind."""
        return abs(self.player_x - self.road_center) > 0.85

    def update_oncoming_traffic(self, dt: float):
        """Update oncoming car positions and spawn new cars."""
        # Spawn new cars
        self.next_car_timer -= dt
        if self.next_car_timer <= 0:
            # Spawn a new car at the horizon
            # In USA, we drive on the right, so oncoming traffic is in the LEFT lane (negative X)
            # from our perspective. They're in THEIR right lane, we're in OUR right lane.
            # Left lane spans roughly -0.7 to -0.2, we spawn in the safe middle portion
            lane = random.uniform(-0.55, -0.35)

            # Choose vehicle type based on weights
            total_weight = sum(v['weight'] for v in self.VEHICLE_TYPES)
            roll = random.uniform(0, total_weight)
            cumulative = 0
            vehicle_type = self.VEHICLE_TYPES[0]  # Default to sedan
            for vtype in self.VEHICLE_TYPES:
                cumulative += vtype['weight']
                if roll <= cumulative:
                    vehicle_type = vtype
                    break

            self.oncoming_cars.append({
                'z': 1.0,
                'lane': lane,
                'type': vehicle_type
            })

            # Next car interval decreases with speed (more traffic at higher speeds)
            speed_factor = self.speed / self.max_speed
            interval_range = self.max_car_interval - self.min_car_interval
            # Higher speed = shorter intervals
            base_interval = self.max_car_interval - (speed_factor * interval_range * 0.7)
            self.next_car_timer = random.uniform(base_interval * 0.7, base_interval * 1.3)

        # Move cars toward player (they approach as we drive toward them)
        # Combined approach speed: our speed + their speed
        approach_speed = self.speed * 0.04 * dt  # How fast z decreases

        cars_to_remove = []
        for car in self.oncoming_cars:
            car['z'] -= approach_speed
            # Remove cars that have passed the player
            if car['z'] < -0.1:
                cars_to_remove.append(car)

        for car in cars_to_remove:
            self.oncoming_cars.remove(car)

    def check_car_collision(self) -> bool:
        """Check if player collides with an oncoming car."""
        for car in self.oncoming_cars:
            # Collision zone: car is close (z < 0.15) and in same lateral position
            if car['z'] < 0.15 and car['z'] > -0.05:
                # Check lateral collision — car lanes ride the road, so compare
                # against the player's position relative to the road center
                car_lane = car['lane']
                # Collision width based on vehicle type
                vehicle_type = car.get('type', self.VEHICLE_TYPES[0])
                base_collision_width = 0.35
                collision_width = base_collision_width * vehicle_type['width']
                if abs((self.player_x - self.road_center) - car_lane) < collision_width:
                    return True
        return False

    def world_to_screen(self, world_z: float, world_x: float) -> tuple:
        """Convert world coordinates to screen coordinates with perspective."""
        # world_z: 0 = at car, 1 = at horizon
        # world_x: -1 = left edge, 0 = center, 1 = right edge

        # Perspective factor
        z = max(0.01, world_z)
        perspective = 1.0 - (z * 0.9)

        # Y position (interpolate from bottom to horizon)
        screen_y = self.ROAD_BOTTOM_Y - (self.ROAD_BOTTOM_Y - self.HORIZON_Y) * (1 - perspective)

        # X position (road narrows toward horizon)
        road_half_width = (self.ROAD_WIDTH_BOTTOM / 2) * perspective + (self.ROAD_WIDTH_TOP / 2) * (1 - perspective)

        # Apply curve offset - stronger effect in distance, creates bend appearance
        # The curve shifts the vanishing point, making the road appear to bend
        curve_offset = self.curve * (1 - perspective) * (1 - perspective) * 25

        # The near field follows the lagging road center, so the whole road
        # (posts, traffic) visibly swings in a turn
        center_offset = self.road_center * 20 * perspective

        screen_x = self.VANISHING_X + world_x * road_half_width + curve_offset + center_offset

        return int(screen_x), int(screen_y)

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Course select screen
        if not self.started and self.state != GameState.GAME_OVER:
            self.display.draw_text_small(12, 10, "NIGHT", Colors.WHITE)
            self.display.draw_text_small(12, 18, "DRIVER", Colors.YELLOW)
            course = self.COURSES[self.course]
            cx = (GRID_SIZE - (len(course) * 4 + 15)) // 2
            self.display.draw_text_small(cx, 34, f"< {course} >", Colors.CYAN)
            self.display.draw_text_small(6, 50, "BTN: START", Colors.GRAY)
            return

        # Draw score
        self.display.draw_text_small(1, 1, f"{self.score}", Colors.WHITE)

        # Draw run clock (center top)
        secs = int(math.ceil(self.time_left))
        timer_color = Colors.RED if self.time_left < 10 else Colors.WHITE
        if self.extend_flash > 0 and int(self.extend_flash * 5) % 2 == 0:
            timer_color = Colors.GREEN
        self.display.draw_text_small(27, 1, f"{secs}", timer_color)

        # Draw speed and gear
        speed_mph = int(self.speed)
        self.display.draw_text_small(41, 1, f"{speed_mph}", Colors.YELLOW)
        self.display.draw_text_small(55, 1, f"G{self.gear}", Colors.CYAN)

        # Bonus time announcement
        if self.extend_flash > 0:
            self.display.draw_text_small(18, 8, "TIME+15", Colors.GREEN)

        # Draw posts
        self.draw_posts()

        # Draw oncoming traffic
        self.draw_oncoming_cars()

        # Draw car
        if not self.crashed:
            self.draw_car()
        else:
            self.draw_crash()

        # Draw game over
        if self.state == GameState.GAME_OVER:
            self.display.draw_text_small(12, 25, "TIME UP", Colors.RED)
            self.display.draw_text_small(8, 35, f"DIST:{self.score}", Colors.WHITE)

    def draw_posts(self):
        """Draw the road posts with perspective, scrolling toward player."""
        for i in range(self.NUM_POSTS):
            # Calculate z position (0 = near, 1 = far)
            # Posts scroll from far to near
            z = (i * self.POST_SPACING + self.post_offset) / (self.NUM_POSTS * self.POST_SPACING)

            if z > 1.0 or z < 0.05:
                continue

            # Post size decreases with distance
            post_height = int(6 * (1 - z * 0.8))
            post_width = max(1, int(2 * (1 - z * 0.7)))

            if post_height < 1:
                continue

            # Left post
            lx, ly = self.world_to_screen(z, -1.0)
            if 0 <= lx < GRID_SIZE and 0 <= ly < GRID_SIZE:
                self.display.draw_rect(lx - post_width // 2, ly - post_height,
                                       post_width, post_height, self.POST_COLOR)

            # Right post
            rx, ry = self.world_to_screen(z, 1.0)
            if 0 <= rx < GRID_SIZE and 0 <= ry < GRID_SIZE:
                self.display.draw_rect(rx - post_width // 2, ry - post_height,
                                       post_width, post_height, self.POST_COLOR)

    def draw_car(self):
        """Draw the player's car at bottom of screen."""
        car_center_x = self.VANISHING_X + int(self.player_x * 20)
        car_x = car_center_x - self.CAR_WIDTH // 2
        car_y = self.CAR_Y

        # Car body
        self.display.draw_rect(car_x, car_y, self.CAR_WIDTH, self.CAR_HEIGHT, self.CAR_COLOR)

        # Windshield
        self.display.draw_rect(car_x + 2, car_y, 4, 2, self.CAR_WINDOW)

        # Hood details
        self.display.set_pixel(car_x + 1, car_y + 3, (150, 30, 30))
        self.display.set_pixel(car_x + 6, car_y + 3, (150, 30, 30))

    def draw_crash(self):
        """Draw crash effect."""
        car_center_x = self.VANISHING_X + int(self.player_x * 20)

        flash = int(self.crash_timer * 10) % 2
        color = Colors.YELLOW if flash else Colors.RED

        for i in range(5):
            px = car_center_x + (hash(i + int(self.crash_timer * 20)) % 12) - 6
            py = self.CAR_Y + (hash(i * 3 + int(self.crash_timer * 15)) % 8) - 4
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                self.display.set_pixel(px, py, color)

    def draw_oncoming_cars(self):
        """Draw oncoming traffic as approaching headlight pairs — nothing else
        is visible at night."""
        # Sort by z so farther cars are drawn first (painter's algorithm)
        sorted_cars = sorted(self.oncoming_cars, key=lambda c: c['z'], reverse=True)

        for car in sorted_cars:
            z = car['z']
            lane = car['lane']
            vehicle_type = car.get('type', self.VEHICLE_TYPES[0])

            # Don't draw cars too far away or past player
            if z > 0.95 or z < 0.0:
                continue

            # Get screen position
            screen_x, screen_y = self.world_to_screen(z, lane)

            # Size increases as car gets closer (perspective)
            closeness = 1.0 - z  # 0.0 = far, 1.0 = close

            # Headlight size (the only visible element at night)
            headlight_size = max(1, int(closeness * 4))

            # Headlight separation increases as car gets closer
            headlight_sep = max(1, int(closeness * 6 * vehicle_type['hl_sep']))

            # Left headlight
            hl_left_x = screen_x - headlight_sep // 2
            # Right headlight
            hl_right_x = screen_x + headlight_sep // 2

            # Headlight brightness increases as car gets closer
            brightness = int(155 + closeness * 100)
            headlight_color = (brightness, brightness, min(255, int(brightness * 0.8)))

            # Draw headlights
            if 0 <= hl_left_x < GRID_SIZE and 0 <= screen_y < GRID_SIZE:
                if headlight_size == 1:
                    self.display.set_pixel(hl_left_x, screen_y, headlight_color)
                else:
                    self.display.draw_rect(hl_left_x - headlight_size // 2,
                                          screen_y - headlight_size // 2,
                                          headlight_size, headlight_size,
                                          headlight_color)

            if 0 <= hl_right_x < GRID_SIZE and 0 <= screen_y < GRID_SIZE:
                if headlight_size == 1:
                    self.display.set_pixel(hl_right_x, screen_y, headlight_color)
                else:
                    self.display.draw_rect(hl_right_x - headlight_size // 2,
                                          screen_y - headlight_size // 2,
                                          headlight_size, headlight_size,
                                          headlight_color)
