"""
Night Driver - Arcade Racing
=============================
Race through the night on winding roads!

Controls:
  Left/Right - Steer
  Space      - Restart (when crashed)
"""

from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE
import math
import random


class NightDriver(Game):
    name = "NITE DRIVER"
    description = "Night Racing"
    category = "arcade"

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
    ROAD_EDGE_COLOR = (100, 100, 100)
    CAR_COLOR = (200, 50, 50)
    CAR_WINDOW = (100, 150, 200)

    # Oncoming traffic colors
    ONCOMING_CAR_COLOR = (255, 200, 50)  # Yellow/orange headlights
    ONCOMING_BODY_COLOR = (80, 80, 100)  # Dark body

    # Vehicle types with different sizes (width_mult, height_mult, headlight_sep_mult, name)
    # Multipliers are relative to base sedan size
    VEHICLE_TYPES = [
        {'name': 'sedan', 'width': 1.0, 'height': 1.0, 'hl_sep': 1.0, 'weight': 40},
        {'name': 'compact', 'width': 0.8, 'height': 0.8, 'hl_sep': 0.8, 'weight': 20},
        {'name': 'suv', 'width': 1.2, 'height': 1.3, 'hl_sep': 1.2, 'weight': 20},
        {'name': 'pickup', 'width': 1.1, 'height': 1.4, 'hl_sep': 1.0, 'weight': 15},
        {'name': 'semi', 'width': 1.4, 'height': 2.5, 'hl_sep': 1.3, 'weight': 5},  # 18-wheeler
    ]

    # Turn types with increasing difficulty
    TURN_NORMAL = 0
    TURN_HAIRPIN = 1      # Sharp 180-degree turn
    TURN_CHICANE = 2      # Quick left-right or right-left

    # Road sign types for visual interest
    SIGN_TYPES = [
        {'name': 'speed_limit', 'color': (255, 255, 255), 'bg': (40, 40, 40)},
        {'name': 'mile_marker', 'color': (100, 255, 100), 'bg': (0, 80, 0)},
        {'name': 'deer_xing', 'color': (255, 220, 0), 'bg': (0, 0, 0)},
        {'name': 'no_passing', 'color': (255, 255, 255), 'bg': (255, 50, 50)},
    ]

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0

        # Player position (-1.0 to 1.0, 0 = center of road)
        self.player_x = 0.0

        # Speed and distance
        self.speed = 25.0       # Units per second
        self.max_speed = 120.0  # Top speed when holding gas
        self.base_speed = 25.0  # Coast speed (no gas) - rises over time
        self.distance = 0.0     # Total distance traveled
        self.gas = False        # Whether gas button is held

        # Post positions (0.0 to POST_SPACING, cycles)
        self.post_offset = 0.0

        # Road curve system - sustained turns
        self.curve = 0.0           # Current curve amount
        self.target_curve = 0.0    # Where we're curving toward
        self.turn_duration = 0.0   # How long current turn lasts
        self.turn_timer = 0.0      # Time in current turn
        self.straight_timer = 0.0  # Time until next turn
        self.curve_intensity = 1.0 # Multiplier for curve tightness (increases with speed)
        self.current_turn_type = self.TURN_NORMAL
        self.chicane_phase = 0     # For chicane turns: 0=first curve, 1=second curve

        # Start with a short straight — pre-plan the first turn
        self.straight_timer = 2.0
        self.next_turn = self.plan_next_turn()
        self.warning_spawned = False

        # Crash state
        self.crashed = False
        self.crash_timer = 0.0

        # Oncoming traffic
        # Each car: {'z': distance (1.0=horizon, 0.0=at player), 'lane': -0.5 or 0.5}
        self.oncoming_cars = []
        self.next_car_timer = 3.0  # Time until next car spawns
        self.min_car_interval = 1.5  # Minimum time between cars
        self.max_car_interval = 4.0  # Maximum time between cars

        # Road signs for visual interest and warnings
        # Each sign: {'z': distance, 'type': sign_type_name, 'side': -1 or 1}
        self.road_signs = []
        self.next_sign_timer = 2.0
        self.warning_sign_active = False  # True when approaching special turn

    def update(self, input_state: InputState, dt: float):
        if self.state == GameState.GAME_OVER:
            if (input_state.action_l or input_state.action_r):
                self.reset()
            return

        if self.crashed:
            self.crash_timer -= dt
            if self.crash_timer <= 0:
                self.state = GameState.GAME_OVER
            return

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

        # Apply curve effect (pushes player toward outside of curve)
        # Physics balance:
        #   - curve_push = curve_value * 0.5 (raw push rate)
        #   - max_push capped at 75% of steer_speed (always survivable with good reflexes)
        #   - At max speed: steer=3.5, max_push=2.625/sec
        #   - Road width is 1.7 (-0.85 to 0.85), so worst case you have ~0.65 sec to react
        # This means hairpins are HARD but not impossible - requires anticipation
        curve_push = self.curve * 0.5
        max_push = steer_speed * 0.75  # Always beatable with good steering
        curve_push = max(-max_push, min(max_push, curve_push))
        self.player_x -= curve_push * dt

        # Update turn/straight timing
        if self.straight_timer > 0:
            # In a straight section
            self.straight_timer -= dt
            # Ease curve back to zero
            self.curve *= 0.95

            # Spawn warning sign 1 second before turn starts
            if self.straight_timer <= 1.0 and not self.warning_spawned and self.next_turn:
                if self.next_turn['sign_type']:
                    self.spawn_warning_sign(self.next_turn)
                self.warning_spawned = True

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
            elif self.current_turn_type == self.TURN_CHICANE:
                approach_rate = 4.0

            diff = self.target_curve - self.curve
            self.curve += diff * dt * approach_rate

            if self.turn_timer >= self.turn_duration:
                # Check if chicane needs second phase
                if self.current_turn_type == self.TURN_CHICANE and self.chicane_phase == 0:
                    # Start second phase - opposite direction
                    self.chicane_phase = 1
                    self.target_curve = -self.target_curve
                    self.turn_duration = random.uniform(0.8, 1.2)
                    self.turn_timer = 0.0
                else:
                    # End turn, start straight section and plan next turn
                    self.straight_timer = random.uniform(1.0, 3.0)
                    self.warning_sign_active = False
                    self.next_turn = self.plan_next_turn()
                    self.warning_spawned = False

        # Gas pedal: hold button to accelerate, release to coast down to base speed
        self.gas = input_state.action_l_held or input_state.action_r_held
        if self.gas:
            self.speed = min(self.speed + 20.0 * dt, self.max_speed)
        else:
            self.speed = max(self.speed - 25.0 * dt, self.base_speed)

        # Base speed rises slowly over time (game gets harder)
        # 25 → ~55 after 2 minutes
        self.base_speed = min(self.base_speed + 0.25 * dt, 60.0)

        # Difficulty scaling: tighter curves at higher speeds
        # But since push is capped, intensity mainly affects visual bend appearance
        # Range: 1.0 to 2.0 multiplier
        self.curve_intensity = 1.0 + speed_factor * 1.0

        # Update distance and post offset
        self.distance += self.speed * dt
        self.post_offset += self.speed * dt * 0.05
        if self.post_offset >= self.POST_SPACING:
            self.post_offset -= self.POST_SPACING

        # Score based on distance
        self.score = int(self.distance)

        # Update oncoming traffic
        self.update_oncoming_traffic(dt)

        # Update road signs
        self.update_road_signs(dt)

        # Check collision with posts
        if self.check_collision():
            self.crashed = True
            self.crash_timer = 1.5

        # Check collision with oncoming cars
        if self.check_car_collision():
            self.crashed = True
            self.crash_timer = 1.5

    def plan_next_turn(self):
        """Pre-compute the next turn so we can warn the player early."""
        speed_factor = self.speed / self.max_speed
        turn_roll = random.random()

        if speed_factor > 0.5 and turn_roll < 0.15:
            direction = random.choice([-1, 1])
            base_curve = direction * random.uniform(2.0, 2.5)
            target_curve = base_curve * self.curve_intensity
            return {
                'turn_type': self.TURN_CHICANE,
                'target_curve': target_curve,
                'turn_duration': random.uniform(0.8, 1.2),
                'sign_type': 'turn_warning',
                'sign_side': 1,
                'sign_direction': direction,
            }

        elif speed_factor > 0.4 and turn_roll < 0.25:
            direction = random.choice([-1, 1])
            base_curve = direction * random.uniform(2.5, 3.5)
            target_curve = base_curve * self.curve_intensity
            return {
                'turn_type': self.TURN_HAIRPIN,
                'target_curve': target_curve,
                'turn_duration': random.uniform(2.0, 3.5),
                'sign_type': 'turn_warning',
                'sign_side': 1,
                'sign_direction': direction,
            }

        else:
            base_options = [-1.5, -1.0, 1.0, 1.5]
            if speed_factor > 0.3:
                base_options.extend([-2.0, 2.0])
            if speed_factor > 0.6:
                base_options.extend([-2.5, 2.5])
            base_curve = random.choice(base_options)
            target_curve = base_curve * self.curve_intensity
            if abs(base_curve) >= 1.5:
                sign_type = 'turn_warning'
                sign_direction = 1 if base_curve > 0 else -1
            else:
                sign_type = None
                sign_direction = 0
            return {
                'turn_type': self.TURN_NORMAL,
                'target_curve': target_curve,
                'turn_duration': random.uniform(1.5, 3.5),
                'sign_type': sign_type,
                'sign_side': 1,
                'sign_direction': sign_direction,
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
        self.warning_sign_active = True
        if turn['turn_type'] == self.TURN_CHICANE:
            self.chicane_phase = 0
        self.next_turn = None

    def spawn_warning_sign(self, turn_info):
        """Spawn a warning sign for upcoming turn — always on right side."""
        self.road_signs.append({
            'z': 1.0,
            'type': 'turn_warning',
            'side': 1,  # Always right side of road
            'direction': turn_info['sign_direction'],
            'severity_color': self.get_turn_severity_color(turn_info['target_curve']),
        })

    def get_turn_severity_color(self, target_curve):
        """Get warning sign color based on turn severity."""
        severity = abs(target_curve)
        if severity < 2.5:
            return (0, 200, 0)      # Green - small turn
        elif severity < 4.0:
            return (255, 220, 0)    # Yellow - medium turn
        elif severity < 5.5:
            return (255, 140, 0)    # Orange - sharp turn
        else:
            return (255, 40, 40)    # Red - hairpin

    def check_collision(self) -> bool:
        """Check if player car hits a road post."""
        return abs(self.player_x) > 0.85

    def update_road_signs(self, dt: float):
        """Update road sign positions and spawn decorative signs."""
        # Move existing signs toward player
        approach_speed = self.speed * 0.04 * dt

        signs_to_remove = []
        for sign in self.road_signs:
            sign['z'] -= approach_speed
            if sign['z'] < -0.1:
                signs_to_remove.append(sign)

        for sign in signs_to_remove:
            self.road_signs.remove(sign)

        # Spawn decorative signs periodically
        self.next_sign_timer -= dt
        if self.next_sign_timer <= 0 and not self.warning_sign_active:
            # Random decorative sign
            decorative_signs = ['speed_limit', 'mile_marker', 'deer_xing', 'no_passing']
            sign_type = random.choice(decorative_signs)
            side = random.choice([-1, 1])
            self.road_signs.append({
                'z': 1.0,
                'type': sign_type,
                'side': side,
            })
            self.next_sign_timer = random.uniform(3.0, 6.0)

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
                # Check lateral collision
                # Player position is -1 to 1, car lane is around -0.4 or 0.4
                car_lane = car['lane']
                # Collision width based on vehicle type
                vehicle_type = car.get('type', self.VEHICLE_TYPES[0])
                base_collision_width = 0.35
                collision_width = base_collision_width * vehicle_type['width']
                if abs(self.player_x - car_lane) < collision_width:
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

        screen_x = self.VANISHING_X + world_x * road_half_width + curve_offset

        return int(screen_x), int(screen_y)

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Draw score
        self.display.draw_text_small(1, 1, f"{self.score}", Colors.WHITE)

        # Draw speed as MPH
        speed_mph = int(self.speed)
        self.display.draw_text_small(45, 1, f"{speed_mph}", Colors.YELLOW)

        # Draw turn indicator (flashing orange for hairpin/chicane)
        if abs(self.curve) > 0.3:
            # Color based on turn type intensity
            if self.current_turn_type == self.TURN_HAIRPIN:
                indicator_color = Colors.ORANGE if int(self.distance * 5) % 2 == 0 else Colors.RED
            elif self.current_turn_type == self.TURN_CHICANE:
                indicator_color = Colors.YELLOW if int(self.distance * 5) % 2 == 0 else Colors.ORANGE
            else:
                indicator_color = Colors.CYAN

            if self.curve > 0:
                self.display.draw_text_small(30, 1, ">", indicator_color)
            else:
                self.display.draw_text_small(26, 1, "<", indicator_color)

        # Draw road edges (perspective lines)
        self.draw_road_edges()

        # Draw posts
        self.draw_posts()

        # Draw road signs
        self.draw_road_signs()

        # Draw oncoming traffic
        self.draw_oncoming_cars()

        # Draw car
        if not self.crashed:
            self.draw_car()
        else:
            self.draw_crash()

        # Draw game over
        if self.state == GameState.GAME_OVER:
            self.display.draw_text_small(8, 25, "GAME OVER", Colors.RED)
            self.display.draw_text_small(8, 35, f"DIST:{self.score}", Colors.WHITE)

    def draw_road_edges(self):
        """Draw the road edge lines converging to vanishing point."""
        # Draw multiple segments to show the curve
        prev_lx, prev_ly = self.world_to_screen(0, -1.0)
        prev_rx, prev_ry = self.world_to_screen(0, 1.0)

        for i in range(1, 11):
            z = i / 10.0
            lx, ly = self.world_to_screen(z, -1.0)
            rx, ry = self.world_to_screen(z, 1.0)

            self.display.draw_line(prev_lx, prev_ly, lx, ly, self.ROAD_EDGE_COLOR)
            self.display.draw_line(prev_rx, prev_ry, rx, ry, self.ROAD_EDGE_COLOR)

            prev_lx, prev_ly = lx, ly
            prev_rx, prev_ry = rx, ry

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

    def draw_road_signs(self):
        """Draw road signs with perspective."""
        # Sort by z so farther signs are drawn first
        sorted_signs = sorted(self.road_signs, key=lambda s: s['z'], reverse=True)

        for sign in sorted_signs:
            z = sign['z']
            sign_type = sign['type']
            side = sign['side']

            # Don't draw signs too far or too close
            if z > 0.9 or z < 0.1:
                continue

            # Position sign outside the road edge
            x_pos = side * 1.15  # Just outside road edge
            screen_x, screen_y = self.world_to_screen(z, x_pos)

            # Size based on distance
            closeness = 1.0 - z
            sign_width = max(2, int(closeness * 8))
            sign_height = max(2, int(closeness * 8))

            # Compute sign position
            post_x = screen_x
            sign_x = screen_x - sign_width // 2
            sign_y = screen_y - sign_height - max(1, int(closeness * 3))

            # Sign post (all sign types)
            if 0 <= post_x < GRID_SIZE and 0 <= screen_y < GRID_SIZE:
                post_h = max(1, int(closeness * 4))
                for py in range(post_h):
                    if 0 <= sign_y + sign_height + py < GRID_SIZE:
                        self.display.set_pixel(post_x, sign_y + sign_height + py, (80, 80, 80))

            if sign_width < 2 or sign_height < 2:
                continue
            if not (0 <= sign_x < GRID_SIZE - sign_width and 0 <= sign_y < GRID_SIZE - sign_height):
                continue

            if sign_type == 'turn_warning':
                # Turn warning: colored triangle pointing in turn direction
                direction = sign.get('direction', 1)
                severity_color = sign.get('severity_color', (255, 220, 0))

                # Black background
                self.display.draw_rect(sign_x, sign_y, sign_width, sign_height, (0, 0, 0))

                # Draw triangle pointing in turn direction
                center_row = (sign_height - 1) / 2.0
                for row in range(sign_height):
                    dist = abs(row - center_row)
                    max_dist = sign_height / 2.0
                    fill = max(1, int(sign_width * (1.0 - dist / max_dist))) if max_dist > 0 else sign_width
                    for col in range(fill):
                        if direction > 0:  # Right turn - triangle points right
                            px = sign_x + col
                        else:  # Left turn - triangle points left
                            px = sign_x + sign_width - 1 - col
                        py = sign_y + row
                        if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                            self.display.set_pixel(px, py, severity_color)
            else:
                # Decorative signs - look up colors from SIGN_TYPES
                sign_info = None
                for st in self.SIGN_TYPES:
                    if st['name'] == sign_type:
                        sign_info = st
                        break
                if not sign_info:
                    continue

                fg_color = sign_info['color']
                bg_color = sign_info['bg']
                self.display.draw_rect(sign_x, sign_y, sign_width, sign_height, bg_color)

                cx = sign_x + sign_width // 2
                cy = sign_y + sign_height // 2

                if sign_type == 'speed_limit':
                    self.display.draw_rect(sign_x, sign_y, sign_width, sign_height, fg_color)
                    if sign_width > 2 and sign_height > 2:
                        self.display.draw_rect(sign_x + 1, sign_y + 1,
                                              sign_width - 2, sign_height - 2, bg_color)
                elif sign_type == 'mile_marker':
                    if sign_width >= 3 and sign_height >= 3:
                        self.display.set_pixel(cx, cy, fg_color)
                elif sign_type == 'deer_xing':
                    self.display.set_pixel(cx, cy - 1, fg_color)
                    self.display.set_pixel(cx, cy + 1, fg_color)
                    self.display.set_pixel(cx - 1, cy, fg_color)
                    self.display.set_pixel(cx + 1, cy, fg_color)
                elif sign_type == 'no_passing':
                    if sign_width >= 3:
                        self.display.set_pixel(sign_x + 1, sign_y + 1, (255, 255, 255))
                        if sign_height >= 3:
                            self.display.set_pixel(sign_x + sign_width - 2,
                                                  sign_y + sign_height - 2, (255, 255, 255))

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
        """Draw oncoming traffic with perspective (headlights approaching)."""
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
            # At z=1.0 (far), size is tiny; at z=0 (close), size is large
            closeness = 1.0 - z  # 0.0 = far, 1.0 = close

            # Apply vehicle type multipliers
            width_mult = vehicle_type['width']
            height_mult = vehicle_type['height']
            hl_sep_mult = vehicle_type['hl_sep']

            # Headlight size (the main visible element at night)
            headlight_size = max(1, int(closeness * 4))
            # Car body dimensions scaled by vehicle type
            body_width = max(2, int(closeness * 10 * width_mult))
            body_height = max(1, int(closeness * 6 * height_mult))

            # Headlight separation increases as car gets closer
            headlight_sep = max(1, int(closeness * 6 * hl_sep_mult))

            # Draw car body (dark, barely visible at night)
            if closeness > 0.3:  # Only visible when close enough
                body_x = screen_x - body_width // 2
                # For tall vehicles (semis), body extends upward more
                body_y = screen_y - int(body_height * 0.7)
                if 0 <= body_x < GRID_SIZE and 0 <= body_y < GRID_SIZE:
                    # Semis get a slightly different color (darker trailer)
                    body_color = (60, 60, 80) if vehicle_type['name'] == 'semi' else self.ONCOMING_BODY_COLOR
                    self.display.draw_rect(body_x, body_y, body_width, body_height, body_color)

                    # Draw cab for semi trucks (lighter section at bottom)
                    if vehicle_type['name'] == 'semi' and closeness > 0.5:
                        cab_height = max(2, body_height // 3)
                        cab_y = body_y + body_height - cab_height
                        self.display.draw_rect(body_x, cab_y, body_width, cab_height, self.ONCOMING_BODY_COLOR)

            # Draw headlights (bright, always visible)
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
