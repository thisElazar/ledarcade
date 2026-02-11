"""
Boids Lab - Flocking Parameter Explorer
========================================
Explore the separation x cohesion parameter space of the
Boids flocking simulation with joystick controls.

Controls:
  Left/Right - Adjust separation weight
  Up/Down    - Adjust cohesion weight
  Button     - Reseed flock
  Both       - Commit params to settings
"""

import random
import math
from . import Visual, Display, GRID_SIZE
import settings

# Named regions in separation x cohesion space
_REGIONS = [
    ('TIGHT FLOCK', 0.2, 0.8,  2.0, 3.0),
    ('LOOSE SWARM', 2.0, 3.0,  0.2, 0.8),
    ('BALANCED',    1.2, 2.0,  1.2, 2.0),
    ('TUG OF WAR', 2.4, 3.0,  2.4, 3.0),
    ('DRIFTING',    0.2, 0.8,  0.2, 0.8),
    ('SCHOOLING',   1.4, 2.2,  2.2, 3.0),
]


def _nearest_region(sep, coh):
    for name, s_lo, s_hi, c_lo, c_hi in _REGIONS:
        if s_lo <= sep <= s_hi and c_lo <= coh <= c_hi:
            return name
    return ''


class _Boid:
    __slots__ = ('x', 'y', 'vx', 'vy')

    def __init__(self, x, y, vx, vy):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy


class BoidsLab(Visual):
    name = "BOIDS LAB"
    description = "Explore Boids parameter space"
    category = "automata"

    NUM_BOIDS = 80
    PERCEPTION_RADIUS = 10.0
    SEPARATION_RADIUS = 2.5
    MIN_SPEED = 0.5
    MAX_SPEED = 3.0

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

        self.separation_weight = settings.get('boids_lab_sep', 1.8)
        self.cohesion_weight = settings.get('boids_lab_coh', 1.8)
        self.alignment_weight = 1.5

        self.palette_idx = settings.get('boids_lab_palette', 0)
        self._build_palettes()
        self.palette_idx = self.palette_idx % len(self.palettes)

        self.spawn_timer = 0.0
        self.spawn_interval = 0.15
        self.disruption_timer = 0.0
        self.disruption_interval = 3.0
        self.mega_flock_threshold = 12

        self.boids = []
        for _ in range(self.NUM_BOIDS // 2):
            self._spawn_random()

        self.param_overlay_timer = 2.0
        self.saved_timer = 0.0
        self.confirm_timer = 0.0
        self._both_held_prev = False

    def _build_palettes(self):
        """Color schemes: each is a function index -> (r,g,b) from heading."""
        # Palette 0: rainbow by heading (default)
        # Palette 1: warm tones (red-orange-yellow)
        # Palette 2: cool tones (blue-cyan-green)
        # Palette 3: monochrome white
        # Palette 4: neon pink-cyan
        self.palettes = ['rainbow', 'warm', 'cool', 'mono', 'neon']

    def _heading_color(self, heading):
        """Convert heading to color based on current palette."""
        hue = (heading + math.pi) / (2 * math.pi)  # 0-1
        palette = self.palettes[self.palette_idx]

        if palette == 'rainbow':
            return self._hsv_to_rgb(hue, 1.0, 1.0)
        elif palette == 'warm':
            # Map to red-orange-yellow range (hue 0.0-0.15)
            return self._hsv_to_rgb(hue * 0.15, 1.0, 1.0)
        elif palette == 'cool':
            # Map to blue-cyan-green range (hue 0.45-0.75)
            return self._hsv_to_rgb(0.45 + hue * 0.3, 1.0, 1.0)
        elif palette == 'mono':
            v = 0.6 + 0.4 * math.sin(hue * math.pi * 2)
            return (int(v * 255), int(v * 255), int(v * 255))
        else:  # neon
            # Alternate pink and cyan
            t = (math.sin(hue * math.pi * 2) + 1) / 2
            r = int(255 * t + 50 * (1 - t))
            g = int(50 * t + 255 * (1 - t))
            b = int(200)
            return (r, g, b)

    @staticmethod
    def _hsv_to_rgb(h, s, v):
        h6 = h * 6.0
        i = int(h6) % 6
        f = h6 - int(h6)
        p = v * (1 - s)
        q = v * (1 - s * f)
        t = v * (1 - s * (1 - f))
        if i == 0:
            r, g, b = v, t, p
        elif i == 1:
            r, g, b = q, v, p
        elif i == 2:
            r, g, b = p, v, t
        elif i == 3:
            r, g, b = p, q, v
        elif i == 4:
            r, g, b = t, p, v
        else:
            r, g, b = v, p, q
        return (int(r * 255), int(g * 255), int(b * 255))

    def _spawn_random(self):
        x = random.uniform(5, GRID_SIZE - 5)
        y = random.uniform(5, GRID_SIZE - 5)
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1.5, 2.5)
        self.boids.append(_Boid(x, y, math.cos(angle) * speed, math.sin(angle) * speed))

    def _disrupt_mega_flocks(self):
        if len(self.boids) < self.mega_flock_threshold:
            return
        for boid in self.boids:
            neighbors = self._get_neighbors(boid, self.PERCEPTION_RADIUS * 0.8)
            if len(neighbors) >= self.mega_flock_threshold:
                if random.random() < 0.3:
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(2.5, 3.5)
                    boid.vx = math.cos(angle) * speed
                    boid.vy = math.sin(angle) * speed

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.left_pressed:
            self.separation_weight = max(0.2, round(self.separation_weight - 0.2, 1))
            self.param_overlay_timer = 2.0
            consumed = True
        if input_state.right_pressed:
            self.separation_weight = min(3.0, round(self.separation_weight + 0.2, 1))
            self.param_overlay_timer = 2.0
            consumed = True
        if input_state.up_pressed:
            self.cohesion_weight = min(3.0, round(self.cohesion_weight + 0.2, 1))
            self.param_overlay_timer = 2.0
            consumed = True
        if input_state.down_pressed:
            self.cohesion_weight = max(0.2, round(self.cohesion_weight - 0.2, 1))
            self.param_overlay_timer = 2.0
            consumed = True
        both_held = input_state.action_l_held and input_state.action_r_held
        both_released = self._both_held_prev and not both_held
        if both_released:
            self.confirm_timer = 3.0
            consumed = True
        elif self.confirm_timer > 0 and not both_held:
            if input_state.action_r:
                settings.set('boids_lab_sep', round(self.separation_weight, 1))
                settings.set('boids_lab_coh', round(self.cohesion_weight, 1))
                settings.set('boids_lab_palette', self.palette_idx)
                self.saved_timer = 1.5
                self.confirm_timer = 0.0
                consumed = True
            elif input_state.action_l:
                self.confirm_timer = 0.0
                consumed = True
        elif not both_held:
            if input_state.action_l or input_state.action_r:
                self.palette_idx = (self.palette_idx + 1) % len(self.palettes)
                self.boids.clear()
                for _ in range(self.NUM_BOIDS // 2):
                    self._spawn_random()
                consumed = True
        self._both_held_prev = both_held
        return consumed

    def _toroidal_diff(self, a, b):
        diff = b - a
        if diff > GRID_SIZE / 2:
            diff -= GRID_SIZE
        elif diff < -GRID_SIZE / 2:
            diff += GRID_SIZE
        return diff

    def _distance(self, b1, b2):
        dx = abs(b1.x - b2.x)
        dy = abs(b1.y - b2.y)
        if dx > GRID_SIZE / 2:
            dx = GRID_SIZE - dx
        if dy > GRID_SIZE / 2:
            dy = GRID_SIZE - dy
        return math.sqrt(dx * dx + dy * dy)

    def _get_neighbors(self, boid, radius):
        neighbors = []
        for other in self.boids:
            if other is not boid:
                dist = self._distance(boid, other)
                if dist < radius:
                    neighbors.append((other, dist))
        return neighbors

    def _separation(self, boid, neighbors):
        sx, sy = 0.0, 0.0
        for other, dist in neighbors:
            if dist < self.SEPARATION_RADIUS and dist > 0:
                w = 1.0 / dist
                sx += self._toroidal_diff(other.x, boid.x) * w
                sy += self._toroidal_diff(other.y, boid.y) * w
        return sx, sy

    def _alignment(self, boid, neighbors):
        if not neighbors:
            return 0.0, 0.0
        ax, ay = 0.0, 0.0
        for other, _ in neighbors:
            ax += other.vx
            ay += other.vy
        n = len(neighbors)
        return (ax / n - boid.vx), (ay / n - boid.vy)

    def _cohesion(self, boid, neighbors):
        if not neighbors:
            return 0.0, 0.0
        cx, cy = 0.0, 0.0
        for other, _ in neighbors:
            cx += self._toroidal_diff(boid.x, other.x)
            cy += self._toroidal_diff(boid.y, other.y)
        n = len(neighbors)
        return cx / n, cy / n

    def _limit_speed(self, boid):
        speed = math.sqrt(boid.vx * boid.vx + boid.vy * boid.vy)
        if speed > 0:
            if speed < self.MIN_SPEED:
                boid.vx = (boid.vx / speed) * self.MIN_SPEED
                boid.vy = (boid.vy / speed) * self.MIN_SPEED
            elif speed > self.MAX_SPEED:
                boid.vx = (boid.vx / speed) * self.MAX_SPEED
                boid.vy = (boid.vy / speed) * self.MAX_SPEED

    def update(self, dt: float):
        self.time += dt

        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0
            self._spawn_random()

        self.disruption_timer += dt
        if self.disruption_timer >= self.disruption_interval:
            self.disruption_timer = 0
            self._disrupt_mega_flocks()

        new_velocities = []
        for boid in self.boids:
            neighbors = self._get_neighbors(boid, self.PERCEPTION_RADIUS)
            sep_x, sep_y = self._separation(boid, neighbors)
            ali_x, ali_y = self._alignment(boid, neighbors)
            coh_x, coh_y = self._cohesion(boid, neighbors)
            ax = sep_x * self.separation_weight + ali_x * self.alignment_weight + coh_x * self.cohesion_weight
            ay = sep_y * self.separation_weight + ali_y * self.alignment_weight + coh_y * self.cohesion_weight
            new_velocities.append((boid.vx + ax * dt, boid.vy + ay * dt))

        margin = 6
        turn_factor = 0.15
        for i, boid in enumerate(self.boids):
            boid.vx, boid.vy = new_velocities[i]
            self._limit_speed(boid)
            boid.x += boid.vx * dt
            boid.y += boid.vy * dt
            if boid.x < margin:
                boid.vx += turn_factor
            elif boid.x > GRID_SIZE - margin:
                boid.vx -= turn_factor
            if boid.y < margin:
                boid.vy += turn_factor
            elif boid.y > GRID_SIZE - margin:
                boid.vy -= turn_factor

        self.boids = [b for b in self.boids if -2 < b.x < GRID_SIZE + 2 and -2 < b.y < GRID_SIZE + 2]
        if len(self.boids) > int(self.NUM_BOIDS * 1.5):
            self.boids = self.boids[-self.NUM_BOIDS:]

        if self.param_overlay_timer > 0:
            self.param_overlay_timer = max(0.0, self.param_overlay_timer - dt)
        if self.saved_timer > 0:
            self.saved_timer = max(0.0, self.saved_timer - dt)
        if self.confirm_timer > 0:
            self.confirm_timer = max(0.0, self.confirm_timer - dt)

    def draw(self):
        self.display.clear((0, 0, 0))

        for boid in self.boids:
            heading = math.atan2(boid.vy, boid.vx)
            color = self._heading_color(heading)
            px, py = int(boid.x), int(boid.y)

            for dy in range(2):
                for dx in range(2):
                    bx = (px + dx) % GRID_SIZE
                    by = (py + dy) % GRID_SIZE
                    if 0 <= bx < GRID_SIZE and 0 <= by < GRID_SIZE:
                        self.display.set_pixel(bx, by, color)

            speed = math.sqrt(boid.vx * boid.vx + boid.vy * boid.vy)
            if speed > 0.1:
                tdx = -boid.vx / speed
                tdy = -boid.vy / speed
                for i in range(1, 4):
                    tx = int(px + tdx * i * 1.2) % GRID_SIZE
                    ty = int(py + tdy * i * 1.2) % GRID_SIZE
                    fade = 1.0 - (i / 4.0)
                    tc = (int(color[0] * fade * 0.5),
                          int(color[1] * fade * 0.5),
                          int(color[2] * fade * 0.5))
                    if 0 <= tx < GRID_SIZE and 0 <= ty < GRID_SIZE:
                        self.display.set_pixel(tx, ty, tc)

        if self.param_overlay_timer > 0:
            alpha = min(1.0, self.param_overlay_timer / 0.5)
            c = (int(255 * alpha), int(255 * alpha), int(255 * alpha))
            region = _nearest_region(self.separation_weight, self.cohesion_weight)
            if region:
                self.display.draw_text_small(2, 2, region, c)
                self.display.draw_text_small(2, 8, "sep=%.1f coh=%.1f" % (self.separation_weight, self.cohesion_weight), c)
            else:
                self.display.draw_text_small(2, 2, "sep=%.1f coh=%.1f" % (self.separation_weight, self.cohesion_weight), c)

        if self.confirm_timer > 0 and self.saved_timer <= 0:
            alpha = min(1.0, self.confirm_timer / 0.5)
            c = (int(255 * alpha), int(220 * alpha), int(80 * alpha))
            self.display.draw_text_small(2, 14, "SAVE?", c)
        if self.saved_timer > 0:
            alpha = min(1.0, self.saved_timer / 0.5)
            c = (int(80 * alpha), int(255 * alpha), int(80 * alpha))
            self.display.draw_text_small(2, 14, "SAVED", c)
