"""
Weather - Abstract weather effects
==================================
Animated weather patterns: rain, snow, sun, clouds.

Controls:
  Space - Cycle weather type
  Escape - Exit
"""

import random
import math
from . import Visual, Display, Colors, GRID_SIZE


class Particle:
    """A weather particle (raindrop, snowflake, etc.)."""
    def __init__(self):
        self.x = 0
        self.y = 0
        self.vx = 0
        self.vy = 0
        self.size = 1


class Weather(Visual):
    name = "WEATHER"
    description = "Weather effects"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.weather_index = 0
        self.weathers = ["rain", "snow", "sun", "clouds"]
        self.particles = []
        self._init_weather()

    def _init_weather(self):
        """Initialize particles for current weather."""
        self.particles = []
        weather = self.weathers[self.weather_index]

        if weather == "rain":
            for _ in range(80):
                p = Particle()
                p.x = random.uniform(0, GRID_SIZE)
                p.y = random.uniform(-GRID_SIZE, GRID_SIZE)
                p.vy = random.uniform(80, 120)
                p.vx = random.uniform(10, 20)  # Slight wind
                p.size = random.choice([2, 3, 4])
                self.particles.append(p)

        elif weather == "snow":
            for _ in range(60):
                p = Particle()
                p.x = random.uniform(0, GRID_SIZE)
                p.y = random.uniform(-GRID_SIZE, GRID_SIZE)
                p.vy = random.uniform(10, 25)
                p.vx = random.uniform(-5, 5)
                p.size = random.choice([1, 2])
                self.particles.append(p)

        elif weather == "sun":
            # Sun rays stored as angles
            pass

        elif weather == "clouds":
            # Create some cloud puffs
            for _ in range(8):
                p = Particle()
                p.x = random.uniform(-20, GRID_SIZE + 20)
                p.y = random.uniform(5, 30)
                p.vx = random.uniform(3, 8)
                p.size = random.randint(8, 16)
                self.particles.append(p)

    def handle_input(self, input_state) -> bool:
        if input_state.action:
            self.weather_index = (self.weather_index + 1) % len(self.weathers)
            self._init_weather()
            return True
        return False

    def update(self, dt: float):
        self.time += dt
        weather = self.weathers[self.weather_index]

        if weather == "rain":
            for p in self.particles:
                p.x += p.vx * dt
                p.y += p.vy * dt
                if p.y > GRID_SIZE:
                    p.y = random.uniform(-10, -2)
                    p.x = random.uniform(0, GRID_SIZE)
                if p.x > GRID_SIZE:
                    p.x = 0

        elif weather == "snow":
            for p in self.particles:
                # Gentle swaying motion
                p.vx = math.sin(self.time * 2 + p.y * 0.1) * 8
                p.x += p.vx * dt
                p.y += p.vy * dt
                if p.y > GRID_SIZE:
                    p.y = random.uniform(-5, -1)
                    p.x = random.uniform(0, GRID_SIZE)
                # Wrap horizontally
                if p.x < 0:
                    p.x = GRID_SIZE
                if p.x > GRID_SIZE:
                    p.x = 0

        elif weather == "clouds":
            for p in self.particles:
                p.x += p.vx * dt
                if p.x > GRID_SIZE + 20:
                    p.x = -20
                    p.y = random.uniform(5, 30)

    def _draw_rain(self):
        """Draw rain effect."""
        # Dark blue background
        self.display.clear((5, 10, 25))

        # Rain streaks
        for p in self.particles:
            x = int(p.x)
            y = int(p.y)

            # Draw streak
            for i in range(p.size):
                py = y - i
                if 0 <= x < GRID_SIZE and 0 <= py < GRID_SIZE:
                    brightness = 150 - i * 30
                    self.display.set_pixel(x, py, (brightness, brightness, 255))

        # Occasional lightning flash
        if random.random() < 0.002:
            self.display.clear((200, 200, 255))

    def _draw_snow(self):
        """Draw snow effect."""
        # Dark gray-blue background
        self.display.clear((15, 15, 30))

        # Ground accumulation
        for x in range(GRID_SIZE):
            height = 3 + int(math.sin(x * 0.3) * 2)
            for y in range(GRID_SIZE - height, GRID_SIZE):
                self.display.set_pixel(x, y, (200, 200, 220))

        # Snowflakes
        for p in self.particles:
            x = int(p.x)
            y = int(p.y)

            if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                if p.size == 1:
                    self.display.set_pixel(x, y, Colors.WHITE)
                else:
                    # Slightly larger flake
                    self.display.set_pixel(x, y, Colors.WHITE)
                    if x > 0:
                        self.display.set_pixel(x - 1, y, (180, 180, 200))
                    if x < GRID_SIZE - 1:
                        self.display.set_pixel(x + 1, y, (180, 180, 200))

    def _draw_sun(self):
        """Draw sunny day effect."""
        # Light blue sky gradient
        for y in range(GRID_SIZE):
            blue = 200 - y
            self.display.draw_line(0, y, GRID_SIZE - 1, y, (100, 150, blue))

        # Sun
        cx, cy = 48, 12

        # Glow
        for r in range(12, 6, -1):
            brightness = int(255 * (12 - r) / 6)
            color = (255, 200 + brightness // 4, brightness)
            for angle in range(0, 360, 5):
                rad = angle * math.pi / 180
                x = int(cx + math.cos(rad) * r)
                y = int(cy + math.sin(rad) * r)
                if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                    self.display.set_pixel(x, y, color)

        # Sun body
        for dy in range(-6, 7):
            for dx in range(-6, 7):
                if dx * dx + dy * dy <= 36:
                    x, y = cx + dx, cy + dy
                    if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                        self.display.set_pixel(x, y, (255, 255, 100))

        # Animated rays
        num_rays = 8
        ray_len = 8 + int(math.sin(self.time * 3) * 2)
        for i in range(num_rays):
            angle = i * math.pi / 4 + self.time * 0.5
            for r in range(8, 8 + ray_len):
                x = int(cx + math.cos(angle) * r)
                y = int(cy + math.sin(angle) * r)
                if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                    self.display.set_pixel(x, y, (255, 255, 150))

        # Green ground
        for y in range(GRID_SIZE - 10, GRID_SIZE):
            green = 100 + (y - (GRID_SIZE - 10)) * 5
            self.display.draw_line(0, y, GRID_SIZE - 1, y, (30, green, 30))

    def _draw_clouds(self):
        """Draw cloudy day effect."""
        # Gray sky
        self.display.clear((80, 80, 100))

        # Draw clouds as overlapping circles
        for p in self.particles:
            cx, cy = int(p.x), int(p.y)
            size = p.size

            # Cloud is several overlapping circles
            offsets = [
                (0, 0, size),
                (-size // 2, size // 4, size * 3 // 4),
                (size // 2, size // 4, size * 3 // 4),
                (0, -size // 4, size * 2 // 3),
            ]

            for ox, oy, r in offsets:
                if r <= 0:
                    continue
                for dy in range(-r, r + 1):
                    for dx in range(-r, r + 1):
                        if dx * dx + dy * dy <= r * r:
                            x = cx + ox + dx
                            y = cy + oy + dy
                            if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                                # Lighter toward center
                                dist = math.sqrt(dx * dx + dy * dy)
                                brightness = int(200 + (1 - dist / r) * 50)
                                self.display.set_pixel(x, y, (brightness, brightness, min(255, brightness + 5)))

        # Darker ground
        for y in range(GRID_SIZE - 8, GRID_SIZE):
            self.display.draw_line(0, y, GRID_SIZE - 1, y, (40, 60, 40))

    def draw(self):
        weather = self.weathers[self.weather_index]

        if weather == "rain":
            self._draw_rain()
        elif weather == "snow":
            self._draw_snow()
        elif weather == "sun":
            self._draw_sun()
        elif weather == "clouds":
            self._draw_clouds()
