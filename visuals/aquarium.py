"""
Aquarium - LED Arcade
=====================
Ambient tropical aquarium with swimming fish, swaying plants, rising bubbles,
and shimmering water surface. The display is the tank -- fish bounce off walls.

Controls:
  Left/Right   - Adjust plant sway speed
  Up/Down      - Cycle color scheme
  Space        - Spawn bubble burst
"""

import random
import math
from . import Visual, Display, Colors, GRID_SIZE

W = 64
H = 64
SURFACE_Y = 3       # rows 0-2 are surface shimmer
SUBSTRATE_Y = 54     # rows 54-63 are substrate
WATER_TOP = SURFACE_Y
WATER_BOT = SUBSTRATE_Y - 1

# Tank wall margins (fish swim area)
WALL_L = 2
WALL_R = W - 3
WALL_TOP = WATER_TOP + 2
WALL_BOT = WATER_BOT - 2

# Color schemes
COLOR_SCHEMES = [
    {
        'name': 'TROPICAL',
        'water_top': (20, 80, 180),
        'water_bot': (5, 30, 80),
        'surface': (60, 140, 220),
        'plants': [(20, 140, 30), (30, 180, 40), (15, 120, 50), (40, 160, 25)],
        'sub_top': (160, 140, 90),
        'sub_bot': (100, 80, 50),
        'bubble': (180, 220, 255),
    },
    {
        'name': 'MOONLIGHT',
        'water_top': (10, 20, 60),
        'water_bot': (2, 8, 30),
        'surface': (20, 40, 90),
        'plants': [(10, 60, 30), (15, 50, 40), (8, 70, 25), (20, 55, 35)],
        'sub_top': (60, 55, 45),
        'sub_bot': (30, 25, 20),
        'bubble': (100, 120, 150),
    },
    {
        'name': 'SUNSET',
        'water_top': (80, 50, 20),
        'water_bot': (30, 15, 5),
        'surface': (140, 90, 30),
        'plants': [(50, 100, 15), (60, 120, 20), (40, 90, 25), (70, 110, 10)],
        'sub_top': (140, 110, 60),
        'sub_bot': (80, 60, 30),
        'bubble': (200, 180, 140),
    },
]

# Fish species: (name, base_color, secondary_color)
FISH_SPECIES = [
    ('clown',    (255, 100, 30),  (255, 255, 255)),  # clownfish
    ('tetra',    (30, 120, 255),  (200, 220, 255)),   # neon tetra
    ('guppy',    (255, 220, 40),  (255, 160, 20)),    # guppy
    ('cardinal', (220, 40, 40),   (255, 100, 100)),   # cardinal tetra
    ('angel',    (180, 180, 200), (220, 220, 240)),   # angelfish silver
    ('betta',    (160, 20, 200),  (220, 80, 255)),    # betta purple
    ('danio',    (40, 200, 180),  (80, 255, 220)),    # zebra danio teal
    ('rasbora',  (255, 140, 60),  (255, 200, 120)),   # harlequin rasbora
]


def lerp_color(c1, c2, t):
    """Linearly interpolate between two colors."""
    t = max(0.0, min(1.0, t))
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


class Fish:
    """A small tropical fish with schooling behavior."""
    def __init__(self, species_idx, y_range_top, y_range_bot):
        species = FISH_SPECIES[species_idx]
        self.species_idx = species_idx
        self.x = random.uniform(WALL_L + 5, WALL_R - 5)
        self.y = random.uniform(y_range_top, y_range_bot)
        self.color = species[1]
        self.color2 = species[2]
        self.dir = 1 if random.random() < 0.5 else -1
        self.speed = random.uniform(4.0, 8.0)
        self.vx = self.dir * self.speed
        self.vy = 0.0
        self.bob_phase = random.uniform(0, math.pi * 2)
        self.bob_amp = random.uniform(0.3, 0.6)
        self.tail_timer = 0.0
        self.change_timer = random.uniform(3.0, 8.0)

    def update(self, dt, school_vx, school_vy):
        """Update fish with schooling influence."""
        # Apply schooling forces (loose)
        self.vx += school_vx * dt
        self.vy += school_vy * dt

        # Vertical bob
        self.bob_phase += dt * 2.0
        self.vy += math.sin(self.bob_phase) * self.bob_amp * 2.0 * dt

        # Dampen vertical velocity
        self.vy *= 0.95

        # Clamp speed
        spd = math.sqrt(self.vx * self.vx + self.vy * self.vy)
        max_spd = 10.0
        if spd > max_spd:
            self.vx = self.vx / spd * max_spd
            self.vy = self.vy / spd * max_spd

        # Update position
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Wall bounce (tank boundaries, no wrapping)
        if self.x < WALL_L:
            self.x = WALL_L
            self.vx = abs(self.vx) * 0.6
            self.dir = 1
        elif self.x > WALL_R:
            self.x = WALL_R
            self.vx = -abs(self.vx) * 0.6
            self.dir = -1

        if self.y < WALL_TOP:
            self.y = WALL_TOP
            self.vy = abs(self.vy) * 0.5
        elif self.y > WALL_BOT:
            self.y = WALL_BOT
            self.vy = -abs(self.vy) * 0.5

        # Update facing direction based on velocity
        if abs(self.vx) > 0.5:
            self.dir = 1 if self.vx > 0 else -1

        # Tail animation
        self.tail_timer += dt

        # Occasional random impulse
        self.change_timer -= dt
        if self.change_timer <= 0:
            self.change_timer = random.uniform(3.0, 8.0)
            self.vx += random.uniform(-3.0, 3.0)
            self.vy += random.uniform(-1.5, 1.5)


class PlantSegment:
    """A segment of an aquatic plant."""
    def __init__(self, x_off, y_off):
        self.x_off = x_off
        self.y_off = y_off


class Plant:
    """An aquatic plant anchored in the substrate."""
    def __init__(self, base_x, plant_type, color):
        self.base_x = base_x
        self.base_y = SUBSTRATE_Y
        self.color = color
        self.plant_type = plant_type  # 'tall', 'bushy', 'carpet'
        self.segments = []
        self.max_height = 0
        self.growth_timer = 0.0

        if plant_type == 'tall':
            self.max_height = random.randint(8, 15)
        elif plant_type == 'bushy':
            self.max_height = random.randint(6, 10)
        else:  # carpet
            self.max_height = random.randint(3, 5)

        # Start with a few segments
        initial = max(2, self.max_height // 2)
        self._grow_to(initial)

    def _grow_to(self, count):
        """Grow plant to the given number of segments."""
        while len(self.segments) < count:
            h = len(self.segments)
            if self.plant_type == 'tall':
                self.segments.append(PlantSegment(0, -h))
            elif self.plant_type == 'bushy':
                if h < self.max_height - 2:
                    self.segments.append(PlantSegment(0, -h))
                else:
                    dx = random.choice([-1, 0, 1])
                    self.segments.append(PlantSegment(dx, -h))
            else:  # carpet
                dx = h // 2 * (1 if h % 2 == 0 else -1)
                self.segments.append(PlantSegment(dx, -min(h, 2)))

    def update(self, dt):
        self.growth_timer += dt
        if self.growth_timer > 2.0 and len(self.segments) < self.max_height:
            self.growth_timer = 0.0
            self._grow_to(len(self.segments) + 1)


class Bubble:
    """A rising bubble."""
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.speed = random.uniform(4.0, 8.0)
        self.wobble_phase = random.uniform(0, math.pi * 2)
        self.wobble_amp = random.uniform(0.3, 0.8)

    def update(self, dt):
        self.y -= self.speed * dt
        self.wobble_phase += dt * 3.0
        self.x += math.sin(self.wobble_phase) * self.wobble_amp * dt

    @property
    def alive(self):
        return self.y >= SURFACE_Y - 1


class Aquarium(Visual):
    name = "AQUARIUM"
    description = "Tropical fish aquarium"
    category = "household"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.scheme_idx = 0
        self.sway_speed = 1.0

        # Generate substrate noise
        self.sub_noise = [[random.randint(-20, 20) for _ in range(W)] for _ in range(H - SUBSTRATE_Y)]

        # Create plants
        plant_types = ['tall', 'bushy', 'carpet', 'tall', 'bushy']
        plant_xs = [8, 22, 35, 48, 56]
        scheme = COLOR_SCHEMES[self.scheme_idx]
        self.plants = []
        for i, (px, pt) in enumerate(zip(plant_xs, plant_types)):
            color = scheme['plants'][i % len(scheme['plants'])]
            self.plants.append(Plant(px, pt, color))

        # Create 8 fish (one of each species)
        self.fish = []
        for i in range(8):
            self.fish.append(Fish(i, WALL_TOP, WALL_BOT))

        # Schooling cooldown: when fish cluster too long, they scatter
        self.school_timer = 0.0      # time fish have been clustered
        self.scatter_timer = 0.0     # remaining scatter duration
        self.school_threshold = 10.0 # seconds of clustering before scatter
        self.scatter_duration = 2.0  # seconds of scattering

        # Bubbles
        self.bubbles = []
        self.bubble_timer = 0.0

        # Rocks (1-2 static decorations)
        self.rocks = []
        rock_x = random.randint(15, 50)
        self.rocks.append({'x': rock_x, 'y': SUBSTRATE_Y - 2, 'w': 4, 'h': 3})
        if random.random() < 0.6:
            rock_x2 = random.randint(5, 55)
            while abs(rock_x2 - rock_x) < 10:
                rock_x2 = random.randint(5, 55)
            self.rocks.append({'x': rock_x2, 'y': SUBSTRATE_Y - 1, 'w': 3, 'h': 2})

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.right:
            self.sway_speed = min(3.0, self.sway_speed + 0.05)
            consumed = True
        if input_state.left:
            self.sway_speed = max(0.2, self.sway_speed - 0.05)
            consumed = True
        if input_state.up_pressed:
            self.scheme_idx = (self.scheme_idx + 1) % len(COLOR_SCHEMES)
            self._update_plant_colors()
            consumed = True
        if input_state.down_pressed:
            self.scheme_idx = (self.scheme_idx - 1) % len(COLOR_SCHEMES)
            self._update_plant_colors()
            consumed = True
        if input_state.action_l:
            # Spawn burst of bubbles
            for _ in range(random.randint(3, 5)):
                bx = random.randint(5, W - 5)
                by = random.uniform(SUBSTRATE_Y - 5, SUBSTRATE_Y)
                self.bubbles.append(Bubble(bx, by))
            consumed = True
        return consumed

    def _update_plant_colors(self):
        scheme = COLOR_SCHEMES[self.scheme_idx]
        for i, plant in enumerate(self.plants):
            plant.color = scheme['plants'][i % len(scheme['plants'])]

    def _compute_schooling(self, fish_idx):
        """Compute loose schooling forces for a fish.
        Three rules (Reynolds boids, simplified):
          1. Cohesion: steer toward center of nearby fish
          2. Alignment: match heading of nearby fish
          3. Separation: avoid getting too close
        During scatter phase, cohesion/alignment flip to repulsion.
        """
        f = self.fish[fish_idx]
        coh_x, coh_y = 0.0, 0.0
        ali_x, ali_y = 0.0, 0.0
        sep_x, sep_y = 0.0, 0.0
        count = 0
        scattering = self.scatter_timer > 0

        school_radius = 18.0
        sep_radius = 5.0 if not scattering else 15.0  # bigger personal space when scattering

        for j, other in enumerate(self.fish):
            if j == fish_idx:
                continue
            dx = other.x - f.x
            dy = other.y - f.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < school_radius and dist > 0:
                count += 1
                coh_x += dx
                coh_y += dy
                ali_x += other.vx
                ali_y += other.vy
                if dist < sep_radius:
                    sep_x -= dx / dist * (sep_radius - dist)
                    sep_y -= dy / dist * (sep_radius - dist)

        steer_x, steer_y = 0.0, 0.0
        if count > 0:
            coh_x /= count
            coh_y /= count
            ali_x /= count
            ali_y /= count

            if scattering:
                # Scatter: repel from group center, ignore alignment
                steer_x -= coh_x * 0.6
                steer_y -= coh_y * 0.6
            else:
                # Normal schooling
                steer_x += coh_x * 0.3
                steer_y += coh_y * 0.3
                steer_x += (ali_x - f.vx) * 0.15
                steer_y += (ali_y - f.vy) * 0.15

        # Separation always applies
        steer_x += sep_x * 2.0
        steer_y += sep_y * 2.0

        return steer_x, steer_y

    def update(self, dt: float):
        super().update(dt)

        # Update plants
        for plant in self.plants:
            plant.update(dt)

        # Compute schooling forces, then update fish
        for i, fish in enumerate(self.fish):
            sx, sy = self._compute_schooling(i)
            fish.update(dt, sx, sy)

        # Schooling cooldown: detect if fish are clustered
        if self.scatter_timer > 0:
            self.scatter_timer -= dt
            if self.scatter_timer <= 0:
                self.scatter_timer = 0.0
                self.school_timer = 0.0
        else:
            # Measure clustering: average distance to group center
            cx = sum(f.x for f in self.fish) / len(self.fish)
            cy = sum(f.y for f in self.fish) / len(self.fish)
            avg_dist = sum(math.sqrt((f.x - cx) ** 2 + (f.y - cy) ** 2) for f in self.fish) / len(self.fish)
            if avg_dist < 12.0:
                self.school_timer += dt
            else:
                self.school_timer = max(0.0, self.school_timer - dt * 0.5)
            if self.school_timer >= self.school_threshold:
                # Trigger scatter: give each fish a random impulse outward
                self.scatter_timer = self.scatter_duration
                for f in self.fish:
                    f.vx += random.uniform(-6.0, 6.0)
                    f.vy += random.uniform(-4.0, 4.0)

        # Update bubbles
        for b in self.bubbles:
            b.update(dt)
        self.bubbles = [b for b in self.bubbles if b.alive]

        # Auto-spawn bubbles (~1/s)
        self.bubble_timer += dt
        if self.bubble_timer > 1.0:
            self.bubble_timer = 0.0
            if len(self.bubbles) < 5:
                if self.plants and random.random() < 0.7:
                    p = random.choice(self.plants)
                    bx = p.base_x + random.randint(-1, 1)
                    by = p.base_y - len(p.segments)
                else:
                    bx = random.randint(2, W - 2)
                    by = SUBSTRATE_Y - 1
                self.bubbles.append(Bubble(bx, by))

    def draw(self):
        scheme = COLOR_SCHEMES[self.scheme_idx]

        # 1. Water background gradient
        for y in range(SURFACE_Y, SUBSTRATE_Y):
            t = (y - SURFACE_Y) / max(1, SUBSTRATE_Y - SURFACE_Y - 1)
            c = lerp_color(scheme['water_top'], scheme['water_bot'], t)
            for x in range(W):
                self.display.set_pixel(x, y, c)

        # 2. Substrate gradient + noise
        for y in range(SUBSTRATE_Y, H):
            t = (y - SUBSTRATE_Y) / max(1, H - SUBSTRATE_Y - 1)
            base = lerp_color(scheme['sub_top'], scheme['sub_bot'], t)
            for x in range(W):
                noise = self.sub_noise[y - SUBSTRATE_Y][x]
                c = (clamp(base[0] + noise, 0, 255),
                     clamp(base[1] + noise, 0, 255),
                     clamp(base[2] + noise, 0, 255))
                self.display.set_pixel(x, y, c)

        # 3. Caustic light on top rows of substrate
        for dy in range(3):
            y = SUBSTRATE_Y + dy
            if y >= H:
                break
            for x in range(W):
                v1 = math.sin(x * 0.4 + self.time * 1.5) * 0.5 + 0.5
                v2 = math.sin(x * 0.7 - self.time * 1.1 + 2.0) * 0.5 + 0.5
                brightness = int((v1 * v2) * 40)
                if brightness > 10:
                    old = self.display.get_pixel(x, y)
                    c = (clamp(old[0] + brightness, 0, 255),
                         clamp(old[1] + brightness, 0, 255),
                         clamp(old[2] + brightness // 2, 0, 255))
                    self.display.set_pixel(x, y, c)

        # 4. Rocks
        rock_color = lerp_color(scheme['sub_top'], (80, 80, 80), 0.5)
        for rock in self.rocks:
            for ry in range(rock['h']):
                for rx in range(rock['w']):
                    px = rock['x'] + rx
                    py = rock['y'] + ry
                    if 0 <= px < W and 0 <= py < H:
                        v = random.randint(-10, 10) if (rx + ry) % 2 == 0 else 0
                        c = (clamp(rock_color[0] + v, 0, 255),
                             clamp(rock_color[1] + v, 0, 255),
                             clamp(rock_color[2] + v, 0, 255))
                        self.display.set_pixel(px, py, c)

        # 5. Plants with sway
        sway_time = self.time * self.sway_speed
        for plant in self.plants:
            for seg in plant.segments:
                height = -seg.y_off  # positive = higher
                sway = math.sin(sway_time * 1.5 + plant.base_x * 0.3 + height * 0.2) * min(height * 0.15, 2.0)
                px = int(plant.base_x + seg.x_off + sway)
                py = plant.base_y + seg.y_off
                if 0 <= px < W and 0 <= py < H:
                    t = height / max(1, plant.max_height)
                    c = (clamp(int(plant.color[0] * (0.6 + 0.4 * t)), 0, 255),
                         clamp(int(plant.color[1] * (0.6 + 0.4 * t)), 0, 255),
                         clamp(int(plant.color[2] * (0.6 + 0.4 * t)), 0, 255))
                    self.display.set_pixel(px, py, c)

        # 6. Fish sprites (3px: tail + body + head)
        for fish in self.fish:
            fx = int(fish.x)
            fy = int(fish.y)
            d = fish.dir

            # Tail (animated)
            tail_up = int(fish.tail_timer / 0.15) % 2 == 0
            tail_x = fx - d
            tail_y = fy + (-1 if tail_up else 1)
            tail_color = (fish.color[0] // 2, fish.color[1] // 2, fish.color[2] // 2)
            if 0 <= tail_x < W and 0 <= tail_y < H:
                self.display.set_pixel(tail_x, tail_y, tail_color)

            # Body
            if 0 <= fx < W and 0 <= fy < H:
                self.display.set_pixel(fx, fy, fish.color)

            # Head (secondary color for stripe/accent)
            head_x = fx + d
            if 0 <= head_x < W and 0 <= fy < H:
                self.display.set_pixel(head_x, fy, fish.color2)

        # 7. Bubbles
        for b in self.bubbles:
            bx = int(b.x)
            by = int(b.y)
            if 0 <= bx < W and SURFACE_Y <= by < H:
                self.display.set_pixel(bx, by, scheme['bubble'])

        # 8. Surface shimmer (overwrite top rows)
        for y in range(SURFACE_Y):
            for x in range(W):
                phase = x * 0.5 + self.time * 2.5
                v = math.sin(phase) * 0.5 + 0.5
                bright = lerp_color(scheme['water_top'], scheme['surface'], v)
                sparkle = math.sin(x * 1.3 + self.time * 4.0 + y * 2.0)
                if sparkle > 0.85:
                    bright = (min(255, bright[0] + 60),
                              min(255, bright[1] + 60),
                              min(255, bright[2] + 60))
                self.display.set_pixel(x, y, bright)
