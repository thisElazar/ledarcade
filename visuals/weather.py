"""
Weather - Abstract weather effects
==================================
Animated weather patterns cycling through 8 types.

Controls:
  Button - Cycle weather type
"""

import random
import math
from . import Visual, Display, Colors, GRID_SIZE

WEATHERS = [
    ('RAIN', (100, 150, 255)),
    ('SNOW', (200, 200, 230)),
    ('SUN', (255, 255, 100)),
    ('CLOUDS', (180, 180, 190)),
    ('FOG', (160, 160, 170)),
    ('THUNDER', (200, 180, 255)),
    ('HAIL', (180, 220, 255)),
    ('RAINBOW', (255, 200, 100)),
]


class Particle:
    __slots__ = ('x', 'y', 'vx', 'vy', 'size', 'val')
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.size = 1
        self.val = 0.0


class Weather(Visual):
    name = "WEATHER"
    description = "Weather effects"
    category = "nature"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.weather_index = 0
        self.particles = []
        self.overlay_timer = 2.5
        self.lightning_flash = 0.0
        self.lightning_bolts = []
        self._init_weather()

    def _init_weather(self):
        self.particles = []
        self.lightning_flash = 0.0
        self.lightning_bolts = []
        wtype = WEATHERS[self.weather_index][0]

        if wtype == 'RAIN':
            for _ in range(80):
                p = Particle()
                p.x = random.uniform(0, GRID_SIZE)
                p.y = random.uniform(-GRID_SIZE, GRID_SIZE)
                p.vy = random.uniform(80, 120)
                p.vx = random.uniform(10, 20)
                p.size = random.choice([2, 3, 4])
                self.particles.append(p)

        elif wtype == 'SNOW':
            for _ in range(60):
                p = Particle()
                p.x = random.uniform(0, GRID_SIZE)
                p.y = random.uniform(-GRID_SIZE, GRID_SIZE)
                p.vy = random.uniform(10, 25)
                p.vx = random.uniform(-5, 5)
                p.size = random.choice([1, 2])
                self.particles.append(p)

        elif wtype == 'CLOUDS':
            for _ in range(8):
                p = Particle()
                p.x = random.uniform(-20, GRID_SIZE + 20)
                p.y = random.uniform(5, 30)
                p.vx = random.uniform(3, 8)
                p.size = random.randint(8, 16)
                self.particles.append(p)

        elif wtype == 'FOG':
            for _ in range(20):
                p = Particle()
                p.x = random.uniform(-30, GRID_SIZE + 30)
                p.y = random.uniform(10, GRID_SIZE - 5)
                p.vx = random.uniform(1, 4)
                p.size = random.randint(10, 22)
                p.val = random.uniform(0.3, 0.7)
                self.particles.append(p)

        elif wtype == 'THUNDER':
            for _ in range(60):
                p = Particle()
                p.x = random.uniform(0, GRID_SIZE)
                p.y = random.uniform(-GRID_SIZE, GRID_SIZE)
                p.vy = random.uniform(90, 140)
                p.vx = random.uniform(15, 25)
                p.size = random.choice([2, 3, 4, 5])
                self.particles.append(p)

        elif wtype == 'HAIL':
            for _ in range(40):
                p = Particle()
                p.x = random.uniform(0, GRID_SIZE)
                p.y = random.uniform(-GRID_SIZE, GRID_SIZE)
                p.vy = random.uniform(60, 100)
                p.vx = random.uniform(5, 15)
                p.size = random.choice([1, 2, 3])
                p.val = 0.0
                self.particles.append(p)

    def handle_input(self, input_state) -> bool:
        if input_state.action_l or input_state.action_r:
            self.weather_index = (self.weather_index + 1) % len(WEATHERS)
            self.overlay_timer = 2.5
            self._init_weather()
            return True
        return False

    def _make_bolt(self):
        x = random.randint(5, GRID_SIZE - 5)
        points = [(x, 0)]
        y = 0
        while y < GRID_SIZE - 10:
            y += random.randint(3, 8)
            x += random.randint(-4, 4)
            x = max(2, min(GRID_SIZE - 2, x))
            points.append((x, min(y, GRID_SIZE - 10)))
        return points

    def update(self, dt: float):
        self.time += dt
        wtype = WEATHERS[self.weather_index][0]

        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

        if wtype == 'RAIN':
            for p in self.particles:
                p.x += p.vx * dt
                p.y += p.vy * dt
                if p.y > GRID_SIZE:
                    p.y = random.uniform(-10, -2)
                    p.x = random.uniform(0, GRID_SIZE)
                if p.x > GRID_SIZE:
                    p.x = 0

        elif wtype == 'SNOW':
            for p in self.particles:
                p.vx = math.sin(self.time * 2 + p.y * 0.1) * 8
                p.x += p.vx * dt
                p.y += p.vy * dt
                if p.y > GRID_SIZE:
                    p.y = random.uniform(-5, -1)
                    p.x = random.uniform(0, GRID_SIZE)
                if p.x < 0:
                    p.x = GRID_SIZE
                if p.x > GRID_SIZE:
                    p.x = 0

        elif wtype == 'CLOUDS':
            for p in self.particles:
                p.x += p.vx * dt
                if p.x > GRID_SIZE + 20:
                    p.x = -20
                    p.y = random.uniform(5, 30)

        elif wtype == 'FOG':
            for p in self.particles:
                p.x += p.vx * dt
                p.val = 0.3 + 0.2 * math.sin(self.time * 0.5 + p.y * 0.1)
                if p.x > GRID_SIZE + 30:
                    p.x = -30
                    p.y = random.uniform(10, GRID_SIZE - 5)

        elif wtype == 'THUNDER':
            for p in self.particles:
                p.x += p.vx * dt
                p.y += p.vy * dt
                if p.y > GRID_SIZE:
                    p.y = random.uniform(-10, -2)
                    p.x = random.uniform(0, GRID_SIZE)
                if p.x > GRID_SIZE:
                    p.x = 0
            if self.lightning_flash > 0:
                self.lightning_flash -= dt
            elif random.random() < 0.008:
                self.lightning_flash = 0.15
                self.lightning_bolts = [self._make_bolt()]
                if random.random() < 0.3:
                    self.lightning_bolts.append(self._make_bolt())

        elif wtype == 'HAIL':
            for p in self.particles:
                p.x += p.vx * dt
                p.y += p.vy * dt
                if p.val > 0:
                    p.val -= dt * 3
                    p.vy = -40 * p.val
                    p.vx = 0
                elif p.y > GRID_SIZE - 5:
                    p.val = random.uniform(0.3, 0.6)
                    p.vy = -40 * p.val
                if p.y > GRID_SIZE + 5 or (p.val <= 0 and p.y > GRID_SIZE):
                    p.y = random.uniform(-10, -2)
                    p.x = random.uniform(0, GRID_SIZE)
                    p.vy = random.uniform(60, 100)
                    p.vx = random.uniform(5, 15)
                    p.val = 0.0

    def draw(self):
        wtype = WEATHERS[self.weather_index][0]

        if wtype == 'RAIN':
            self._draw_rain()
        elif wtype == 'SNOW':
            self._draw_snow()
        elif wtype == 'SUN':
            self._draw_sun()
        elif wtype == 'CLOUDS':
            self._draw_clouds()
        elif wtype == 'FOG':
            self._draw_fog()
        elif wtype == 'THUNDER':
            self._draw_thunder()
        elif wtype == 'HAIL':
            self._draw_hail()
        elif wtype == 'RAINBOW':
            self._draw_rainbow()

        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            _, oc = WEATHERS[self.weather_index]
            color = (int(oc[0] * alpha), int(oc[1] * alpha), int(oc[2] * alpha))
            self.display.draw_text_small(2, 2, wtype, color)

    def _draw_rain(self):
        self.display.clear((5, 10, 25))
        for p in self.particles:
            x = int(p.x)
            y = int(p.y)
            for i in range(p.size):
                py = y - i
                if 0 <= x < GRID_SIZE and 0 <= py < GRID_SIZE:
                    brightness = 150 - i * 30
                    self.display.set_pixel(x, py, (brightness, brightness, 255))

    def _draw_snow(self):
        self.display.clear((15, 15, 30))
        for x in range(GRID_SIZE):
            height = 3 + int(math.sin(x * 0.3) * 2)
            for y in range(GRID_SIZE - height, GRID_SIZE):
                self.display.set_pixel(x, y, (200, 200, 220))
        for p in self.particles:
            x, y = int(p.x), int(p.y)
            if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                self.display.set_pixel(x, y, Colors.WHITE)
                if p.size >= 2:
                    if 0 < x:
                        self.display.set_pixel(x - 1, y, (180, 180, 200))
                    if x < GRID_SIZE - 1:
                        self.display.set_pixel(x + 1, y, (180, 180, 200))

    def _draw_sun(self):
        for y in range(GRID_SIZE):
            blue = 200 - y
            self.display.draw_line(0, y, GRID_SIZE - 1, y, (100, 150, blue))
        cx, cy = 48, 12
        for r in range(12, 6, -1):
            brightness = int(255 * (12 - r) / 6)
            color = (255, 200 + brightness // 4, brightness)
            for angle in range(0, 360, 5):
                rad = angle * math.pi / 180
                x = int(cx + math.cos(rad) * r)
                y = int(cy + math.sin(rad) * r)
                if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                    self.display.set_pixel(x, y, color)
        for dy in range(-6, 7):
            for dx in range(-6, 7):
                if dx * dx + dy * dy <= 36:
                    x, y = cx + dx, cy + dy
                    if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                        self.display.set_pixel(x, y, (255, 255, 100))
        num_rays = 8
        ray_len = 8 + int(math.sin(self.time * 3) * 2)
        for i in range(num_rays):
            angle = i * math.pi / 4 + self.time * 0.5
            for r in range(8, 8 + ray_len):
                x = int(cx + math.cos(angle) * r)
                y = int(cy + math.sin(angle) * r)
                if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                    self.display.set_pixel(x, y, (255, 255, 150))
        for y in range(GRID_SIZE - 10, GRID_SIZE):
            green = 100 + (y - (GRID_SIZE - 10)) * 5
            self.display.draw_line(0, y, GRID_SIZE - 1, y, (30, green, 30))

    def _draw_clouds(self):
        self.display.clear((80, 80, 100))
        self._draw_cloud_puffs()
        for y in range(GRID_SIZE - 8, GRID_SIZE):
            self.display.draw_line(0, y, GRID_SIZE - 1, y, (40, 60, 40))

    def _draw_cloud_puffs(self):
        for p in self.particles:
            cx, cy = int(p.x), int(p.y)
            size = p.size
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
                                dist = math.sqrt(dx * dx + dy * dy)
                                brightness = int(200 + (1 - dist / r) * 50)
                                self.display.set_pixel(x, y, (brightness, brightness, min(255, brightness + 5)))

    def _draw_fog(self):
        for y in range(GRID_SIZE):
            t = y / GRID_SIZE
            g = int(50 + 30 * t)
            self.display.draw_line(0, y, GRID_SIZE - 1, y, (g - 10, g, g + 5))
        for y in range(GRID_SIZE - 6, GRID_SIZE):
            green = 30 + (y - (GRID_SIZE - 6)) * 4
            self.display.draw_line(0, y, GRID_SIZE - 1, y, (20, green, 20))
        for x in range(0, GRID_SIZE, 12):
            trunk_x = x + 6
            for ty in range(GRID_SIZE - 14, GRID_SIZE - 6):
                if 0 <= trunk_x < GRID_SIZE:
                    self.display.set_pixel(trunk_x, ty, (40, 30, 20))
            for dy in range(-4, 1):
                for dx in range(-3, 4):
                    if dx * dx + dy * dy <= 10:
                        px = trunk_x + dx
                        py = GRID_SIZE - 14 + dy
                        if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                            self.display.set_pixel(px, py, (25, 50, 25))
        for p in self.particles:
            cx, cy = int(p.x), int(p.y)
            r = p.size
            alpha = p.val
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    if dx * dx + dy * dy <= r * r:
                        x = cx + dx
                        y = cy + dy
                        if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                            dist = math.sqrt(dx * dx + dy * dy)
                            fade = (1.0 - dist / r) * alpha
                            cur = self.display.get_pixel(x, y)
                            fog = (160, 165, 170)
                            blended = (
                                int(cur[0] + (fog[0] - cur[0]) * fade),
                                int(cur[1] + (fog[1] - cur[1]) * fade),
                                int(cur[2] + (fog[2] - cur[2]) * fade),
                            )
                            self.display.set_pixel(x, y, blended)

    def _draw_thunder(self):
        if self.lightning_flash > 0:
            flash_t = self.lightning_flash / 0.15
            bg = int(30 + 180 * flash_t)
            self.display.clear((bg, bg, min(255, bg + 40)))
        else:
            self.display.clear((3, 5, 15))

        for p in self.particles:
            x, y = int(p.x), int(p.y)
            for i in range(p.size):
                py = y - i
                if 0 <= x < GRID_SIZE and 0 <= py < GRID_SIZE:
                    brightness = 120 - i * 20
                    self.display.set_pixel(x, py, (brightness, brightness, 200))

        if self.lightning_flash > 0:
            flash_t = self.lightning_flash / 0.15
            for bolt in self.lightning_bolts:
                bright = int(255 * flash_t)
                color = (bright, bright, min(255, int(bright * 1.2)))
                for i in range(len(bolt) - 1):
                    x1, y1 = bolt[i]
                    x2, y2 = bolt[i + 1]
                    self.display.draw_line(x1, y1, x2, y2, color)

    def _draw_hail(self):
        self.display.clear((20, 25, 35))
        for y in range(GRID_SIZE - 4, GRID_SIZE):
            self.display.draw_line(0, y, GRID_SIZE - 1, y, (50, 55, 60))
        for p in self.particles:
            x, y = int(p.x), int(p.y)
            if not (0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE):
                continue
            if p.val > 0:
                self.display.set_pixel(x, y, (220, 230, 255))
            else:
                r = max(1, p.size)
                for dy in range(-r, r + 1):
                    for dx in range(-r, r + 1):
                        if dx * dx + dy * dy <= r * r:
                            px, py = x + dx, y + dy
                            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                                self.display.set_pixel(px, py, (200, 220, 255))

    def _draw_rainbow(self):
        for y in range(GRID_SIZE):
            t = y / GRID_SIZE
            b = int(180 - 80 * t)
            self.display.draw_line(0, y, GRID_SIZE - 1, y, (int(80 + 40 * t), int(140 - 20 * t), b))
        for y in range(GRID_SIZE - 8, GRID_SIZE):
            green = 80 + (y - (GRID_SIZE - 8)) * 8
            self.display.draw_line(0, y, GRID_SIZE - 1, y, (30, green, 30))

        cx, cy = 32, GRID_SIZE + 8
        rainbow_colors = [
            (255, 0, 0), (255, 127, 0), (255, 255, 0),
            (0, 200, 0), (0, 0, 255), (75, 0, 130), (148, 0, 211),
        ]
        base_r = 42
        for i, color in enumerate(rainbow_colors):
            r = base_r + i * 2
            for angle_deg in range(0, 181):
                rad = math.radians(180 + angle_deg)
                x = int(cx + math.cos(rad) * r)
                y = int(cy + math.sin(rad) * r)
                if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                    self.display.set_pixel(x, y, color)
                x2 = int(cx + math.cos(rad) * (r + 1))
                y2 = int(cy + math.sin(rad) * (r + 1))
                if 0 <= x2 < GRID_SIZE and 0 <= y2 < GRID_SIZE:
                    self.display.set_pixel(x2, y2, color)

        pulse = 0.7 + 0.3 * math.sin(self.time * 2)
        sx, sy = 50, 10
        for r in range(8, 4, -1):
            brightness = int(200 * pulse * (8 - r) / 4)
            sc = (255, 200 + brightness // 4, brightness)
            for a in range(0, 360, 6):
                rad = math.radians(a)
                x = int(sx + math.cos(rad) * r)
                y = int(sy + math.sin(rad) * r)
                if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                    self.display.set_pixel(x, y, sc)
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                if dx * dx + dy * dy <= 16:
                    x, y = sx + dx, sy + dy
                    if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                        self.display.set_pixel(x, y, (255, 255, int(140 * pulse)))
