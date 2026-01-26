"""
Road Trip - Desert driving visual
=================================
A beautiful desert road trip with two views:
- Driver's view: Road stretching ahead with signs
- Window view: Parallax desert landscape with cacti and mountains

Controls:
  Space      - Toggle between views
  Up/Down    - Adjust speed
  Left/Right - (Window view) Look left/right
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE


class Road(Visual):
    name = "ROAD"
    description = "Desert drive"
    category = "nature"

    # Color palette - beautiful desert day
    SKY_TOP = (135, 206, 235)      # Light sky blue
    SKY_BOTTOM = (200, 230, 255)   # Pale horizon
    SUN_COLOR = (255, 250, 205)    # Warm sun
    SUN_GLOW = (255, 245, 180)

    MOUNTAIN_FAR = (180, 160, 200)   # Distant purple mountains
    MOUNTAIN_MID = (160, 140, 170)   # Mid mountains
    MOUNTAIN_NEAR = (140, 115, 130)  # Closer hills

    DESERT_FAR = (230, 200, 150)     # Distant sand
    DESERT_MID = (210, 180, 130)     # Mid ground
    DESERT_NEAR = (190, 160, 110)    # Near ground
    DESERT_CLOSE = (180, 150, 100)   # Closest

    ROAD_COLOR = (60, 60, 65)
    ROAD_EDGE = (80, 80, 85)
    LANE_MARKING = (255, 255, 200)
    SIGN_POST = (120, 100, 80)
    SIGN_GREEN = (0, 120, 60)
    SIGN_WHITE = (255, 255, 255)

    CACTUS_DARK = (40, 90, 45)
    CACTUS_LIGHT = (60, 130, 65)

    CLOUD_WHITE = (255, 255, 255)
    CLOUD_SHADOW = (220, 225, 235)

    TUMBLEWEED_DARK = (139, 90, 43)
    TUMBLEWEED_LIGHT = (160, 120, 80)

    # Sign colors
    SIGN_BROWN = (101, 67, 33)
    SIGN_YELLOW = (255, 200, 0)
    SIGN_BLUE = (0, 80, 160)

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed = 40.0  # Base speed
        self.view_mode = 0  # 0 = driver view, 1 = side window

        # Road elements (driver view)
        self.road_offset = 0.0
        self.signs = []  # List of {distance, type, text}
        self.spawn_timer = 0.0

        # Parallax layers (side view)
        self.layer_offsets = [0.0, 0.0, 0.0, 0.0]  # Far to near
        self.layer_speeds = [0.1, 0.3, 0.6, 1.0]   # Parallax speeds

        # Cacti positions (regenerate on view switch)
        self.cacti = []
        self.generate_cacti()

        # Mountains (static shapes but scroll slowly)
        self.mountains = []
        self.generate_mountains()

        # Side view look direction
        self.look_offset = 0.0

        # Clouds
        self.clouds = []
        self.generate_clouds()

        # Tumbleweeds
        self.tumbleweeds = []
        self.tumbleweed_timer = 0.0

    def generate_clouds(self):
        """Generate fluffy clouds for the sky."""
        self.clouds = []
        for _ in range(6):
            self.clouds.append({
                'x': random.uniform(0, 128),
                'y': random.randint(3, 15),
                'size': random.randint(6, 14),
                'puffs': random.randint(2, 4),
            })

    def spawn_tumbleweed(self):
        """Spawn a new tumbleweed."""
        self.tumbleweeds.append({
            'x': random.choice([-10, GRID_SIZE + 10]),
            'y': random.randint(45, 58),
            'speed': random.uniform(20, 40),
            'size': random.randint(3, 6),
            'rotation': 0.0,
            'bounce_phase': random.uniform(0, math.pi * 2),
        })

    def generate_cacti(self):
        """Generate random cactus positions for side view."""
        self.cacti = []
        for _ in range(12):
            self.cacti.append({
                'x': random.uniform(0, 128),  # Wide range for scrolling
                'layer': random.choice([2, 3]),  # Mid or near ground
                'type': random.randint(0, 2),  # Different cactus shapes
                'height': random.randint(8, 16),
            })

    def generate_mountains(self):
        """Generate mountain silhouette points."""
        self.mountains = []
        # Far mountains
        x = 0
        while x < 128:
            peak_h = random.randint(8, 16)
            width = random.randint(15, 30)
            self.mountains.append({
                'x': x,
                'height': peak_h,
                'width': width,
                'layer': 0,
            })
            x += width - random.randint(3, 8)  # Overlap slightly

        # Mid hills
        x = 0
        while x < 128:
            peak_h = random.randint(4, 10)
            width = random.randint(10, 20)
            self.mountains.append({
                'x': x,
                'height': peak_h,
                'width': width,
                'layer': 1,
            })
            x += width - random.randint(2, 5)

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.action:
            self.view_mode = 1 - self.view_mode
            if self.view_mode == 1:
                self.generate_cacti()
            consumed = True

        if input_state.up:
            self.speed = min(80.0, self.speed + 2.0)
            consumed = True
        if input_state.down:
            self.speed = max(15.0, self.speed - 2.0)
            consumed = True

        # Look left/right in side view
        if self.view_mode == 1:
            if input_state.left:
                self.look_offset = max(-20, self.look_offset - 1)
                consumed = True
            if input_state.right:
                self.look_offset = min(20, self.look_offset + 1)
                consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt

        if self.view_mode == 0:
            self.update_driver_view(dt)
        else:
            self.update_side_view(dt)

    def update_driver_view(self, dt: float):
        """Update driver's forward view."""
        # Road line animation
        self.road_offset += self.speed * dt * 2
        if self.road_offset > 20:
            self.road_offset -= 20

        # Spawn signs occasionally
        self.spawn_timer += dt
        if self.spawn_timer > random.uniform(2.0, 5.0):
            self.spawn_timer = 0
            sign_type = random.choice([
                'speed', 'speed',  # Common
                'mile_marker',
                'exit', 'exit',
                'attraction',  # "GAS", "FOOD", etc.
                'warning',  # Yellow diamond
                'rest_stop',
                'route',  # Blue shield
            ])
            self.signs.append({
                'distance': 60.0,
                'type': sign_type,
                'side': random.choice([-1, 1]),
                'value': random.choice([65, 75, 55, 40]) if sign_type == 'speed' else random.randint(1, 999),
            })

        # Update signs
        for sign in self.signs:
            sign['distance'] -= self.speed * dt * 0.5

        # Remove passed signs
        self.signs = [s for s in self.signs if s['distance'] > -5]

    def update_side_view(self, dt: float):
        """Update side window parallax view."""
        for i in range(len(self.layer_offsets)):
            self.layer_offsets[i] += self.speed * dt * self.layer_speeds[i]
            if self.layer_offsets[i] > 128:
                self.layer_offsets[i] -= 128

        # Spawn tumbleweeds occasionally
        self.tumbleweed_timer += dt
        if self.tumbleweed_timer > random.uniform(3.0, 8.0):
            self.tumbleweed_timer = 0
            self.spawn_tumbleweed()

        # Update tumbleweeds
        for tw in self.tumbleweeds:
            direction = 1 if tw['x'] < 0 else -1
            tw['x'] += direction * tw['speed'] * dt
            tw['rotation'] += dt * 5
            # Bouncing motion
            tw['bounce_phase'] += dt * 8

        # Remove off-screen tumbleweeds
        self.tumbleweeds = [tw for tw in self.tumbleweeds
                           if -15 < tw['x'] < GRID_SIZE + 15]

    def draw(self):
        if self.view_mode == 0:
            self.draw_driver_view()
        else:
            self.draw_side_view()

    def draw_driver_view(self):
        """Draw the driver's forward view of the road."""
        # Sky gradient
        for y in range(30):
            t = y / 30
            color = self.lerp_color(self.SKY_TOP, self.SKY_BOTTOM, t)
            for x in range(GRID_SIZE):
                self.display.set_pixel(x, y, color)

        # Sun
        sun_x, sun_y = 48, 8
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                dist = math.sqrt(dx*dx + dy*dy)
                if dist < 3:
                    self.display.set_pixel(sun_x + dx, sun_y + dy, self.SUN_COLOR)
                elif dist < 4.5:
                    self.display.set_pixel(sun_x + dx, sun_y + dy, self.SUN_GLOW)

        # Distant mountains (horizon)
        mountain_y = 28
        for x in range(GRID_SIZE):
            # Simple mountain silhouette
            h = int(3 + 2 * math.sin(x * 0.2) + 1.5 * math.sin(x * 0.35))
            for y in range(h):
                self.display.set_pixel(x, mountain_y - y, self.MOUNTAIN_FAR)

        # Desert ground
        for y in range(30, GRID_SIZE):
            t = (y - 30) / 34
            color = self.lerp_color(self.DESERT_FAR, self.DESERT_CLOSE, t)
            for x in range(GRID_SIZE):
                self.display.set_pixel(x, y, color)

        # Road (perspective trapezoid)
        self.draw_perspective_road()

        # Signs
        for sign in self.signs:
            self.draw_road_sign(sign)

    def draw_perspective_road(self):
        """Draw road with perspective."""
        horizon_y = 30
        vanishing_x = 32

        for y in range(horizon_y, GRID_SIZE):
            # Calculate road width at this y (perspective)
            t = (y - horizon_y) / (GRID_SIZE - horizon_y)
            road_width = int(4 + t * 28)
            left = vanishing_x - road_width // 2
            right = vanishing_x + road_width // 2

            # Road surface
            for x in range(left, right + 1):
                if 0 <= x < GRID_SIZE:
                    # Edge lines
                    if x == left or x == right:
                        self.display.set_pixel(x, y, self.LANE_MARKING)
                    else:
                        self.display.set_pixel(x, y, self.ROAD_COLOR)

            # Center lane markings (dashed)
            center = vanishing_x
            # Adjust dash position based on road_offset and perspective
            dash_period = max(2, int(20 * (1 - t * 0.8)))
            dash_phase = int(self.road_offset * (1 - t * 0.7)) % dash_period

            if dash_phase < dash_period // 2:
                if 0 <= center < GRID_SIZE:
                    self.display.set_pixel(center, y, self.LANE_MARKING)

    def draw_road_sign(self, sign):
        """Draw a road sign in perspective."""
        if sign['distance'] < 5 or sign['distance'] > 50:
            return

        # Calculate position based on distance
        t = 1.0 - (sign['distance'] / 60.0)
        y = int(30 + t * 25)

        # X position based on side and perspective
        offset = int(sign['side'] * (5 + t * 18))
        x = 32 + offset

        if y < 30 or y > 55:
            return

        # Sign size based on distance
        size = max(2, int(t * 6))

        # Post
        for py in range(y, min(y + size + 4, GRID_SIZE)):
            if 0 <= x < GRID_SIZE:
                self.display.set_pixel(x, py, self.SIGN_POST)

        # Sign board dimensions and color based on type
        sign_type = sign['type']

        if sign_type == 'speed':
            # White rectangle
            sign_w = max(3, size + 1)
            sign_h = max(3, size + 1)
            sign_color = self.SIGN_WHITE
        elif sign_type == 'warning':
            # Yellow diamond (drawn as rotated square)
            sign_w = max(3, size)
            sign_h = max(3, size)
            sign_color = self.SIGN_YELLOW
        elif sign_type == 'mile_marker':
            # Small green rectangle
            sign_w = max(2, size - 1)
            sign_h = max(2, size)
            sign_color = self.SIGN_GREEN
        elif sign_type == 'attraction':
            # Brown rectangle (gas, food, lodging)
            sign_w = max(4, size + 2)
            sign_h = max(2, size)
            sign_color = self.SIGN_BROWN
        elif sign_type == 'route':
            # Blue shield
            sign_w = max(3, size)
            sign_h = max(3, size + 1)
            sign_color = self.SIGN_BLUE
        elif sign_type == 'rest_stop':
            # Blue rectangle
            sign_w = max(4, size + 2)
            sign_h = max(2, size)
            sign_color = self.SIGN_BLUE
        else:  # exit, distance
            # Green rectangle
            sign_w = max(4, size + 3)
            sign_h = max(2, size)
            sign_color = self.SIGN_GREEN

        sign_x = x - sign_w // 2
        sign_y = y - sign_h

        # Draw sign shape
        if sign_type == 'warning':
            # Diamond shape
            for sy in range(sign_h):
                for sx in range(sign_w):
                    # Diamond check
                    cx, cy = sign_w // 2, sign_h // 2
                    if abs(sx - cx) + abs(sy - cy) <= max(cx, cy):
                        px, py = sign_x + sx, sign_y + sy
                        if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                            self.display.set_pixel(px, py, sign_color)
        else:
            # Rectangle
            for sy in range(sign_h):
                for sx in range(sign_w):
                    px, py = sign_x + sx, sign_y + sy
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        self.display.set_pixel(px, py, sign_color)

            # Add white border/text hint on some signs
            if sign_type in ['exit', 'route', 'rest_stop'] and size > 3:
                # White text area
                if sign_h > 2:
                    for sx in range(1, sign_w - 1):
                        px = sign_x + sx
                        py = sign_y + 1
                        if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                            self.display.set_pixel(px, py, self.SIGN_WHITE)

    def draw_side_view(self):
        """Draw the side window view with parallax."""
        # Sky gradient (clear sky above)
        for y in range(28):
            t = y / 28
            color = self.lerp_color(self.SKY_TOP, self.SKY_BOTTOM, t)
            for x in range(GRID_SIZE):
                self.display.set_pixel(x, y, color)

        # Sun (off to the side)
        sun_x = int(50 + self.look_offset * 0.3)
        sun_y = 8
        if 0 <= sun_x < GRID_SIZE:
            for dy in range(-5, 6):
                for dx in range(-5, 6):
                    dist = math.sqrt(dx*dx + dy*dy)
                    px = sun_x + dx
                    if 0 <= px < GRID_SIZE and 0 <= sun_y + dy < GRID_SIZE:
                        if dist < 4:
                            self.display.set_pixel(px, sun_y + dy, self.SUN_COLOR)
                        elif dist < 6:
                            # Sun rays
                            if int(self.time * 2 + dist) % 2 == 0:
                                self.display.set_pixel(px, sun_y + dy, self.SUN_GLOW)

        # Draw clouds (in sky, very slow parallax)
        self.draw_clouds()

        # Horizon line - clear separation between sky and land
        for x in range(GRID_SIZE):
            self.display.set_pixel(x, 28, self.DESERT_FAR)

        # Far mountains (layer 0) - these are LAND, not sky
        self.draw_mountain_layer(0, 35, self.MOUNTAIN_FAR)

        # Mid hills (layer 1)
        self.draw_mountain_layer(1, 40, self.MOUNTAIN_MID)

        # Desert ground layers
        self.draw_ground_layer(2, 42, 50, self.DESERT_MID)
        self.draw_ground_layer(3, 50, GRID_SIZE, self.DESERT_NEAR)

        # Cacti
        for cactus in self.cacti:
            self.draw_cactus(cactus)

        # Tumbleweeds
        for tw in self.tumbleweeds:
            self.draw_tumbleweed(tw)

        # Near ground detail
        for y in range(55, GRID_SIZE):
            for x in range(GRID_SIZE):
                # Add some texture
                if random.random() < 0.02:
                    shade = random.randint(-20, 10)
                    color = (
                        max(0, min(255, self.DESERT_CLOSE[0] + shade)),
                        max(0, min(255, self.DESERT_CLOSE[1] + shade)),
                        max(0, min(255, self.DESERT_CLOSE[2] + shade)),
                    )
                    self.display.set_pixel(x, y, color)

    def draw_clouds(self):
        """Draw fluffy clouds with slow parallax."""
        cloud_speed = 0.05  # Very slow
        offset = int(self.layer_offsets[0] * cloud_speed + self.look_offset * 0.1)

        for cloud in self.clouds:
            cx = int(cloud['x'] - offset) % 128 - 32
            cy = cloud['y']
            size = cloud['size']

            # Draw cloud as overlapping circles (puffs)
            for i in range(cloud['puffs']):
                puff_x = cx + i * (size // 2)
                puff_y = cy + (1 if i % 2 == 0 else -1)
                puff_r = size // 2 - abs(i - cloud['puffs'] // 2)

                for dy in range(-puff_r, puff_r + 1):
                    for dx in range(-puff_r, puff_r + 1):
                        if dx * dx + dy * dy <= puff_r * puff_r:
                            px = puff_x + dx
                            py = puff_y + dy
                            if 0 <= px < GRID_SIZE and 0 <= py < 25:
                                # Slight shading on bottom
                                color = self.CLOUD_SHADOW if dy > puff_r // 2 else self.CLOUD_WHITE
                                self.display.set_pixel(px, py, color)

    def draw_tumbleweed(self, tw):
        """Draw a rolling tumbleweed."""
        x = int(tw['x'])
        # Bouncing motion
        bounce = int(abs(math.sin(tw['bounce_phase'])) * 3)
        y = tw['y'] - bounce
        size = tw['size']
        rotation = tw['rotation']

        # Draw as a rough circle with some texture
        for dy in range(-size, size + 1):
            for dx in range(-size, size + 1):
                dist = math.sqrt(dx * dx + dy * dy)
                if dist <= size:
                    # Rotate the texture
                    rx = dx * math.cos(rotation) - dy * math.sin(rotation)
                    ry = dx * math.sin(rotation) + dy * math.cos(rotation)

                    # Create spiky texture
                    angle = math.atan2(ry, rx)
                    spikiness = 0.7 + 0.3 * math.sin(angle * 8)

                    if dist <= size * spikiness:
                        px, py = x + dx, y + dy
                        if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                            # Vary color slightly
                            color = self.TUMBLEWEED_LIGHT if (dx + dy) % 2 == 0 else self.TUMBLEWEED_DARK
                            self.display.set_pixel(px, py, color)

    def draw_mountain_layer(self, layer_idx, base_y, color):
        """Draw a mountain layer with parallax."""
        offset = int(self.layer_offsets[layer_idx] + self.look_offset * self.layer_speeds[layer_idx] * 0.5)

        for mountain in self.mountains:
            if mountain['layer'] != layer_idx:
                continue

            peak_x = int(mountain['x'] - offset) % 128 - 32
            peak_h = mountain['height']
            width = mountain['width']

            # Draw triangular mountain
            for dx in range(-width // 2, width // 2 + 1):
                x = peak_x + dx
                if 0 <= x < GRID_SIZE:
                    # Height at this x
                    dist_from_peak = abs(dx)
                    h = int(peak_h * (1 - dist_from_peak / (width / 2)))
                    for dy in range(h):
                        y = base_y - dy
                        if 0 <= y < GRID_SIZE:
                            self.display.set_pixel(x, y, color)

    def draw_ground_layer(self, layer_idx, y_start, y_end, color):
        """Draw a ground layer."""
        for y in range(y_start, y_end):
            t = (y - y_start) / max(1, (y_end - y_start))
            # Slight color variation
            shade = int(t * 15)
            c = (
                max(0, color[0] - shade),
                max(0, color[1] - shade),
                max(0, color[2] - shade),
            )
            for x in range(GRID_SIZE):
                self.display.set_pixel(x, y, c)

    def draw_cactus(self, cactus):
        """Draw a cactus with parallax."""
        layer = cactus['layer']
        offset = int(self.layer_offsets[layer] + self.look_offset * self.layer_speeds[layer] * 0.5)

        x = int(cactus['x'] - offset) % 128 - 32
        if x < -10 or x > GRID_SIZE + 10:
            return

        # Base Y depends on layer (adjusted for new ground positions)
        base_y = 52 if layer == 2 else 60
        height = cactus['height']
        cactus_type = cactus['type']

        # Scale based on layer (farther = smaller)
        scale = 0.6 if layer == 2 else 1.0
        height = int(height * scale)

        # Draw cactus based on type
        if cactus_type == 0:
            # Classic saguaro with arms
            self.draw_saguaro(x, base_y, height)
        elif cactus_type == 1:
            # Simple tall cactus
            self.draw_simple_cactus(x, base_y, height)
        else:
            # Prickly pear (round segments)
            self.draw_prickly_pear(x, base_y, int(height * 0.5))

    def draw_saguaro(self, x, base_y, height):
        """Draw a saguaro cactus with arms."""
        # Main trunk
        for dy in range(height):
            y = base_y - dy
            if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                self.display.set_pixel(x, y, self.CACTUS_DARK)
            if 0 <= x + 1 < GRID_SIZE and 0 <= y < GRID_SIZE:
                self.display.set_pixel(x + 1, y, self.CACTUS_LIGHT)

        # Left arm
        arm_y = base_y - height * 2 // 3
        for dx in range(-3, 0):
            if 0 <= x + dx < GRID_SIZE and 0 <= arm_y < GRID_SIZE:
                self.display.set_pixel(x + dx, arm_y, self.CACTUS_DARK)
        for dy in range(height // 3):
            if 0 <= x - 3 < GRID_SIZE and 0 <= arm_y - dy < GRID_SIZE:
                self.display.set_pixel(x - 3, arm_y - dy, self.CACTUS_LIGHT)

        # Right arm (if tall enough)
        if height > 10:
            arm_y = base_y - height // 2
            for dx in range(1, 4):
                if 0 <= x + dx < GRID_SIZE and 0 <= arm_y < GRID_SIZE:
                    self.display.set_pixel(x + dx, arm_y, self.CACTUS_LIGHT)
            for dy in range(height // 4):
                if 0 <= x + 3 < GRID_SIZE and 0 <= arm_y - dy < GRID_SIZE:
                    self.display.set_pixel(x + 3, arm_y - dy, self.CACTUS_DARK)

    def draw_simple_cactus(self, x, base_y, height):
        """Draw a simple columnar cactus."""
        for dy in range(height):
            y = base_y - dy
            if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                self.display.set_pixel(x, y, self.CACTUS_DARK)
            if 0 <= x + 1 < GRID_SIZE and 0 <= y < GRID_SIZE:
                self.display.set_pixel(x + 1, y, self.CACTUS_LIGHT)

    def draw_prickly_pear(self, x, base_y, size):
        """Draw a prickly pear cactus (stacked ovals)."""
        # Bottom pad
        for dy in range(-size, size + 1):
            for dx in range(-size, size + 1):
                if dx * dx + dy * dy <= size * size:
                    px, py = x + dx, base_y - size + dy
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        color = self.CACTUS_LIGHT if dx > 0 else self.CACTUS_DARK
                        self.display.set_pixel(px, py, color)

        # Top pad (smaller, offset)
        top_size = max(1, size - 1)
        top_y = base_y - size * 2
        for dy in range(-top_size, top_size + 1):
            for dx in range(-top_size, top_size + 1):
                if dx * dx + dy * dy <= top_size * top_size:
                    px, py = x + dx + 1, top_y + dy
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        color = self.CACTUS_LIGHT if dx > 0 else self.CACTUS_DARK
                        self.display.set_pixel(px, py, color)

    def lerp_color(self, c1, c2, t):
        """Linearly interpolate between two colors."""
        return (
            int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t),
        )
