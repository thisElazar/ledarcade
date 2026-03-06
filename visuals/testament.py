"""
Testament - Biblical Scenes
=============================
Ambient looping scenes from the Bible on 64x64 LED matrix.
Each scene is a stable, gently animated symbol.

Scenes:
  1. Burning Bush    - Fire that does not consume, sandals set aside
  2. Noah's Ark      - Ark on calm waters after the flood, rainbow above
  3. Star of Bethlehem - Brilliant star over a quiet stable
  4. Dove & Rainbow  - Dove with olive branch, rainbow of promise

Controls:
  Up/Down     - Switch scene
  Left/Right  - Adjust speed
  Space/Z     - Scene action
  Escape      - Exit
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE

NUM_SCENES = 4


# ── Helpers ──────────────────────────────────────────────────────────

def _add_color(c1, c2):
    return (min(255, c1[0] + c2[0]), min(255, c1[1] + c2[1]), min(255, c1[2] + c2[2]))


def _scale_color(c, s):
    return (min(255, int(c[0] * s)), min(255, int(c[1] * s)), min(255, int(c[2] * s)))


# ── Bush shape ───────────────────────────────────────────────────────

def _make_bush():
    pixels = set()
    cx, cy = 32, 40
    for y in range(28, 53):
        for x in range(20, 45):
            dx = (x - cx) / 12.0
            dy = (y - cy) / 11.0
            dist = dx * dx + dy * dy
            if dist < 1.0:
                noise = math.sin(x * 1.7 + y * 0.9) * 0.15 + math.sin(y * 2.3) * 0.1
                if dist < 0.85 + noise:
                    pixels.add((x, y))
    for y in range(50, 56):
        for x in range(30, 35):
            pixels.add((x, y))
    for bx, by in [(22, 34), (24, 30), (42, 33), (40, 29), (35, 27), (28, 28)]:
        pixels.add((bx, by))
        pixels.add((bx, by + 1))
    return pixels


BUSH_PIXELS = _make_bush()
SPAWN_POINTS = [(x, y) for x, y in BUSH_PIXELS if y < 38 or
                ((x, y - 1) not in BUSH_PIXELS and y < 48)]
if not SPAWN_POINTS:
    SPAWN_POINTS = [(x, y) for x, y in BUSH_PIXELS if y < 42]


def _make_sandals(base_x, base_y):
    leather = (160, 120, 70)
    strap = (130, 95, 50)
    sole_dark = (100, 75, 40)
    pixels = []
    lx, ly = base_x, base_y
    for dx in range(4):
        pixels.append((lx + dx, ly + 1, leather))
        pixels.append((lx + dx, ly, sole_dark))
    pixels.append((lx + 4, ly + 1, sole_dark))
    pixels.append((lx + 1, ly - 1, strap))
    pixels.append((lx + 2, ly - 1, strap))
    rx, ry = base_x + 1, base_y + 3
    for dx in range(4):
        pixels.append((rx + dx, ry + 1, leather))
        pixels.append((rx + dx, ry, sole_dark))
    pixels.append((rx + 4, ry + 1, sole_dark))
    pixels.append((rx + 1, ry - 1, strap))
    pixels.append((rx + 2, ry - 1, strap))
    return pixels


# ── Ark shape ────────────────────────────────────────────────────────

def _make_ark():
    """Simple ark silhouette: hull + cabin structure."""
    pixels = []
    wood = (140, 90, 40)
    wood_dark = (100, 65, 25)
    wood_light = (170, 120, 60)

    # Hull — curved bottom, wide body (centered at x=32)
    # Hull spans x=14..50, widest at y=44, narrowing to keel at y=50
    for y in range(42, 51):
        depth = y - 42  # 0..8
        # Narrowing toward keel
        half_w = max(3, 18 - depth * 2)
        for x in range(32 - half_w, 32 + half_w + 1):
            edge = abs(x - 32) > half_w - 2
            pixels.append((x, y, wood_dark if edge else wood))

    # Deck line
    for x in range(14, 51):
        pixels.append((x, 41, wood_light))

    # Cabin structure (simple rectangular house on deck)
    for y in range(35, 41):
        for x in range(20, 45):
            if x == 20 or x == 44 or y == 35:
                pixels.append((x, y, wood_dark))
            else:
                pixels.append((x, y, wood))

    # Roof (peaked)
    for x in range(18, 47):
        dist_from_center = abs(x - 32)
        roof_y = 34 - max(0, 2 - dist_from_center // 5)
        for ry in range(roof_y, 35):
            pixels.append((x, ry, wood_dark))

    # Small window
    pixels.append((32, 37, (180, 180, 140)))
    pixels.append((33, 37, (180, 180, 140)))

    return pixels


ARK_PIXELS = _make_ark()


# ── Fire particle ────────────────────────────────────────────────────

class _Particle:
    __slots__ = ('x', 'y', 'vx', 'vy', 'life', 'max_life', 'heat')

    def __init__(self, x, y, vx, vy, life):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.heat = 1.0


# =====================================================================
# Main Visual
# =====================================================================

class Testament(Visual):
    name = "TESTAMENT"
    description = "Biblical scenes"
    category = "culture"

    MAX_PARTICLES = 300

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed = 1.0
        self.scene = 0

        # -- Burning Bush --
        self.particles = []
        self.divine_flash = 0.0
        self.glow = [[0.0] * GRID_SIZE for _ in range(GRID_SIZE)]

        random.seed(33)
        self.bush_ground = [54 + int(2 * math.sin(x * 0.3)) for x in range(GRID_SIZE)]
        random.seed()

        random.seed(77)
        self.bush_stars = [(random.randint(0, 63), random.randint(0, 20),
                            random.random() * math.pi * 2,
                            0.3 + random.random() * 1.5)
                           for _ in range(25)]
        random.seed()

        sandal_x = 48
        self.sandal_pixels = _make_sandals(sandal_x, self.bush_ground[sandal_x] - 2)

        # -- Noah's Ark --
        random.seed(55)
        self.ark_stars = [(random.randint(0, 63), random.randint(0, 18),
                           random.random() * math.pi * 2,
                           0.3 + random.random() * 1.0)
                          for _ in range(20)]
        random.seed()

        # -- Star of Bethlehem --
        random.seed(25)
        self.beth_stars = [(random.randint(0, 63), random.randint(0, 35),
                            random.random() * math.pi * 2,
                            0.3 + random.random() * 1.5)
                           for _ in range(40)]
        random.seed()

        random.seed(88)
        self.beth_hills = [48 + int(6 * math.sin(x * 0.08) + 3 * math.sin(x * 0.2))
                           for x in range(GRID_SIZE)]
        random.seed()

        # -- Dove & Rainbow --
        random.seed(66)
        self.dove_stars = [(random.randint(0, 63), random.randint(0, 15),
                            random.random() * math.pi * 2,
                            0.3 + random.random() * 1.2)
                           for _ in range(15)]
        random.seed()

    # ── Input ────────────────────────────────────────────────────────

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.up_pressed:
            self.scene = (self.scene - 1) % NUM_SCENES
            consumed = True
        if input_state.down_pressed:
            self.scene = (self.scene + 1) % NUM_SCENES
            consumed = True

        if input_state.left:
            self.speed = max(0.3, self.speed - 0.2)
            consumed = True
        if input_state.right:
            self.speed = min(3.0, self.speed + 0.2)
            consumed = True

        if input_state.action_l or input_state.action_r:
            if self.scene == 0:
                self.divine_flash = 1.0
            consumed = True

        return consumed

    # ── Update ───────────────────────────────────────────────────────

    def update(self, dt: float):
        self.time += dt
        scaled_dt = dt * self.speed

        if self.scene == 0:
            self._update_bush(scaled_dt)

    def _update_bush(self, scaled_dt):
        if self.divine_flash > 0:
            self.divine_flash = max(0, self.divine_flash - scaled_dt * 2.0)

        for _ in range(12):
            if len(self.particles) >= self.MAX_PARTICLES:
                break
            sx, sy = random.choice(SPAWN_POINTS)
            vx = random.gauss(0, 0.8)
            vy = random.gauss(-3.0, 1.0)
            life = 0.4 + random.random() * 0.8
            self.particles.append(
                _Particle(sx + random.gauss(0, 0.5), sy, vx, vy, life))

        alive = []
        for p in self.particles:
            p.life -= scaled_dt
            if p.life <= 0:
                continue
            p.x += p.vx * scaled_dt
            p.y += p.vy * scaled_dt
            p.vy -= 2.0 * scaled_dt
            p.vx += random.gauss(0, 1.5) * scaled_dt
            p.heat = p.life / p.max_life
            alive.append(p)
        self.particles = alive

        for y in range(GRID_SIZE):
            row = self.glow[y]
            for x in range(GRID_SIZE):
                row[x] *= 0.85

        for p in self.particles:
            px, py = int(p.x), int(p.y)
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                self.glow[py][px] = min(1.0, self.glow[py][px] + p.heat * 0.4)

    # ── Draw ─────────────────────────────────────────────────────────

    def draw(self):
        display = self.display
        t = self.time * self.speed

        display.clear(Colors.BLACK)

        if self.scene == 0:
            self._draw_bush(display, t)
        elif self.scene == 1:
            self._draw_ark(display, t)
        elif self.scene == 2:
            self._draw_bethlehem(display, t)
        elif self.scene == 3:
            self._draw_dove(display, t)

    # ═════════════════════════════════════════════════════════════════
    # SCENE 0: BURNING BUSH
    # ═════════════════════════════════════════════════════════════════

    def _draw_bush(self, display, t):
        # Night sky
        for y in range(GRID_SIZE):
            depth = y / GRID_SIZE
            r = int(8 + 6 * (1 - depth))
            g = int(4 + 4 * (1 - depth))
            b = int(20 + 15 * (1 - depth))
            for x in range(GRID_SIZE):
                display.set_pixel(x, y, (r, g, b))

        for sx, sy, phase, spd in self.bush_stars:
            brightness = 0.2 + 0.8 * max(0, math.sin(t * spd + phase))
            gray = int(120 * brightness)
            display.set_pixel(sx, sy, (gray, gray, int(gray * 0.9)))

        # Desert ground
        for x in range(GRID_SIZE):
            gy = self.bush_ground[x]
            for y in range(gy, GRID_SIZE):
                depth = (y - gy) / max(1, GRID_SIZE - gy)
                display.set_pixel(x, y, (max(0, int(80 - 30 * depth)),
                                         max(0, int(55 - 20 * depth)),
                                         max(0, int(30 - 15 * depth))))

        # Sandals
        for sx, sy, sc in self.sandal_pixels:
            if 0 <= sx < GRID_SIZE and 0 <= sy < GRID_SIZE:
                display.set_pixel(sx, sy, sc)

        # Bush (always intact)
        for bx, by in BUSH_PIXELS:
            noise = math.sin(bx * 0.7 + by * 0.5) * 0.2
            display.set_pixel(bx, by, (max(0, int(20 + 15 * noise)),
                                       max(0, int(50 + 30 * noise)),
                                       max(0, int(15 + 10 * noise))))

        # Fire glow
        for y in range(GRID_SIZE):
            row = self.glow[y]
            for x in range(GRID_SIZE):
                heat = row[x]
                if heat > 0.02:
                    if heat > 0.7:
                        fc = (255, int(220 + 35 * heat), int(150 * heat))
                    elif heat > 0.4:
                        fc = (255, int(180 * heat / 0.7), int(30 * heat))
                    else:
                        fc = (int(255 * heat / 0.4), int(80 * heat / 0.4), 0)
                    existing = display.get_pixel(x, y)
                    display.set_pixel(x, y, _add_color(existing,
                                                       _scale_color(fc, min(1.0, heat))))

        # Particles
        for p in self.particles:
            px, py = int(p.x), int(p.y)
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                h = p.heat
                if h > 0.6:
                    color = (255, int(200 + 55 * h), int(100 * h))
                elif h > 0.3:
                    color = (int(255 * h / 0.6), int(150 * h / 0.6), 0)
                else:
                    color = (int(180 * h / 0.3), int(40 * h / 0.3), 0)
                display.set_pixel(px, py, _add_color(display.get_pixel(px, py), color))

        # Ground glow
        for x in range(22, 44):
            gy = self.bush_ground[x]
            fire_intensity = self.glow[min(63, gy - 1)][x] if gy > 0 else 0
            if fire_intensity > 0.01:
                glow_c = (int(100 * fire_intensity), int(40 * fire_intensity), 0)
                for dy in range(3):
                    if gy + dy < GRID_SIZE:
                        existing = display.get_pixel(x, gy + dy)
                        display.set_pixel(x, gy + dy,
                                          _add_color(existing,
                                                     _scale_color(glow_c, 1.0 - dy * 0.3)))

        # Divine flash
        if self.divine_flash > 0:
            flash = self.divine_flash ** 2
            white = int(200 * flash)
            wc = (white, white, int(white * 0.8))
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    display.set_pixel(x, y, _add_color(display.get_pixel(x, y), wc))

    # ═════════════════════════════════════════════════════════════════
    # SCENE 1: NOAH'S ARK — calm day at sea after the flood
    # ═════════════════════════════════════════════════════════════════

    def _draw_ark(self, display, t):
        horizon = 28

        # Sky gradient — clear day, soft blue
        for y in range(horizon):
            sky_t = y / horizon
            r = int(100 + 80 * sky_t)
            g = int(150 + 70 * sky_t)
            b = int(230 - 20 * sky_t)
            for x in range(GRID_SIZE):
                display.set_pixel(x, y, (min(255, r), min(255, g), min(255, b)))

        # Rainbow arc in the sky
        rainbow_colors = [
            (200, 50, 50), (220, 130, 40), (220, 210, 50),
            (50, 190, 50), (50, 100, 220), (90, 50, 180), (140, 50, 170),
        ]
        rcx, rcy = 32, 40
        for y in range(4, horizon):
            for x in range(GRID_SIZE):
                dx = x - rcx
                dy = y - rcy
                dist = math.sqrt(dx * dx + dy * dy)
                band = dist - 28
                if 0 <= band < 7 and dy < 0:
                    bi = int(band)
                    rc = rainbow_colors[bi]
                    # Soft blend with sky
                    alpha = 0.35 + 0.1 * math.sin(t * 0.5 + x * 0.1)
                    existing = display.get_pixel(x, y)
                    blended = (int(existing[0] * (1 - alpha) + rc[0] * alpha),
                               int(existing[1] * (1 - alpha) + rc[1] * alpha),
                               int(existing[2] * (1 - alpha) + rc[2] * alpha))
                    display.set_pixel(x, y, blended)

        # Ocean — gentle rolling waves
        for y in range(horizon, GRID_SIZE):
            water_depth = (y - horizon) / (GRID_SIZE - horizon)
            for x in range(GRID_SIZE):
                wave1 = math.sin(x * 0.15 + t * 0.6 + y * 0.2) * 0.12
                wave2 = math.sin(x * 0.4 - t * 0.4 + y * 0.1) * 0.06
                brightness = max(0, min(1, 0.65 - 0.25 * water_depth + wave1 + wave2))
                r = int(20 * brightness)
                g = int(80 * brightness)
                b = int(180 * brightness)
                display.set_pixel(x, y, (r, g, b))

        # Horizon shimmer
        for x in range(GRID_SIZE):
            shimmer = 0.4 + 0.3 * math.sin(x * 0.3 + t * 1.0)
            c = int(160 * shimmer)
            display.set_pixel(x, horizon, (c, min(255, c + 20), min(255, c + 40)))

        # Ark — gently bobbing
        bob_y = int(1.5 * math.sin(t * 0.7))
        bob_x = int(0.5 * math.sin(t * 0.3))
        for ax, ay, ac in ARK_PIXELS:
            px = ax + bob_x
            py = ay + bob_y
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                display.set_pixel(px, py, ac)

        # Water reflection of ark (subtle)
        for ax, ay, ac in ARK_PIXELS:
            if ay >= 44:  # only reflect the hull
                px = ax + bob_x
                ry = 50 + (50 - (ay + bob_y)) + 2
                if 0 <= px < GRID_SIZE and 0 <= ry < GRID_SIZE:
                    existing = display.get_pixel(px, ry)
                    ref_c = _scale_color(ac, 0.15)
                    display.set_pixel(px, ry, _add_color(existing, ref_c))

    # ═════════════════════════════════════════════════════════════════
    # SCENE 2: STAR OF BETHLEHEM
    # ═════════════════════════════════════════════════════════════════

    def _draw_bethlehem(self, display, t):
        # Deep night sky
        for y in range(GRID_SIZE):
            depth = y / GRID_SIZE
            r = int(6 + 8 * (1 - depth))
            g = int(6 + 10 * (1 - depth))
            b = int(25 + 30 * (1 - depth))
            for x in range(GRID_SIZE):
                display.set_pixel(x, y, (r, g, b))

        # Stars
        for sx, sy, phase, spd in self.beth_stars:
            brightness = 0.2 + 0.8 * max(0, math.sin(t * spd + phase))
            gray = int(140 * brightness)
            display.set_pixel(sx, sy, (gray, gray, int(gray * 0.95)))

        # The Star — large, brilliant, with rays
        star_x, star_y = 38, 10
        pulse = 0.85 + 0.15 * math.sin(t * 1.5)

        # Glow halo
        for dy in range(-6, 7):
            for dx in range(-6, 7):
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < 6:
                    intensity = (1.0 - dist / 6) ** 2 * pulse * 0.5
                    glow = (int(255 * intensity), int(240 * intensity), int(180 * intensity))
                    px, py = star_x + dx, star_y + dy
                    if 0 <= px < 64 and 0 <= py < 64:
                        display.set_pixel(px, py, _add_color(display.get_pixel(px, py), glow))

        # Bright core
        core_c = _scale_color((255, 250, 220), pulse)
        display.set_pixel(star_x, star_y, core_c)
        for d in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            display.set_pixel(star_x + d[0], star_y + d[1], _scale_color(core_c, 0.7))

        # Four long rays (cross shape)
        for length in range(2, 8):
            intensity = max(0, 1.0 - length / 8) * pulse * 0.6
            ray_c = (int(255 * intensity), int(230 * intensity), int(150 * intensity))
            display.set_pixel(star_x + length, star_y, _add_color(display.get_pixel(star_x + length, star_y), ray_c))
            display.set_pixel(star_x - length, star_y, _add_color(display.get_pixel(star_x - length, star_y), ray_c))
            if star_y + length < 64:
                display.set_pixel(star_x, star_y + length, _add_color(display.get_pixel(star_x, star_y + length), ray_c))
            if star_y - length >= 0:
                display.set_pixel(star_x, star_y - length, _add_color(display.get_pixel(star_x, star_y - length), ray_c))

        # Diagonal rays (shorter)
        for length in range(1, 5):
            intensity = max(0, 1.0 - length / 5) * pulse * 0.35
            ray_c = (int(255 * intensity), int(220 * intensity), int(130 * intensity))
            for ddx, ddy in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                rx, ry = star_x + ddx * length, star_y + ddy * length
                if 0 <= rx < 64 and 0 <= ry < 64:
                    display.set_pixel(rx, ry, _add_color(display.get_pixel(rx, ry), ray_c))

        # Beam of light downward toward the stable
        stable_x = 38
        for y in range(star_y + 8, 50):
            beam_intensity = 0.08 + 0.04 * math.sin(t * 1.2 + y * 0.3)
            beam_width = 1 + (y - star_y) // 10
            for dx in range(-beam_width, beam_width + 1):
                bx = stable_x + dx
                if 0 <= bx < 64:
                    falloff = 1.0 - abs(dx) / (beam_width + 1)
                    bc = (int(255 * beam_intensity * falloff),
                          int(230 * beam_intensity * falloff),
                          int(140 * beam_intensity * falloff))
                    display.set_pixel(bx, y, _add_color(display.get_pixel(bx, y), bc))

        # Desert hills
        for x in range(GRID_SIZE):
            hy = self.beth_hills[x]
            for y in range(hy, GRID_SIZE):
                depth = (y - hy) / max(1, GRID_SIZE - hy)
                display.set_pixel(x, y, (max(0, int(60 - 25 * depth)),
                                         max(0, int(45 - 20 * depth)),
                                         max(0, int(30 - 15 * depth))))

        # Simple stable silhouette
        sx = 34
        sy_base = self.beth_hills[sx] - 1
        wood = (50, 30, 15)
        # Walls
        for dy in range(0, 8):
            display.set_pixel(sx, sy_base - dy, wood)
            display.set_pixel(sx + 9, sy_base - dy, wood)
        # Roof peak
        for dx in range(10):
            roof_y = sy_base - 8 - max(0, 3 - abs(dx - 5) * 2 // 3)
            for ry in range(roof_y, sy_base - 7):
                display.set_pixel(sx + dx, ry, wood)
        # Manger glow inside
        glow_pulse = 0.7 + 0.3 * math.sin(t * 1.0)
        for dx in range(1, 9):
            for dy in range(0, 3):
                glow_i = glow_pulse * (0.3 - dy * 0.08)
                gc = (int(255 * glow_i), int(200 * glow_i), int(100 * glow_i))
                display.set_pixel(sx + dx, sy_base - dy, _add_color(display.get_pixel(sx + dx, sy_base - dy), gc))

    # ═════════════════════════════════════════════════════════════════
    # SCENE 3: DOVE & RAINBOW
    # ═════════════════════════════════════════════════════════════════

    def _draw_dove(self, display, t):
        # Soft sky after rain — lighter blue
        for y in range(GRID_SIZE):
            sky_t = y / GRID_SIZE
            r = int(130 + 60 * sky_t)
            g = int(170 + 50 * sky_t)
            b = int(230 - 20 * sky_t)
            for x in range(GRID_SIZE):
                display.set_pixel(x, y, (min(255, r), min(255, g), min(255, b)))

        # Rainbow — large arc across the sky (behind the dove)
        rainbow_colors = [
            (220, 60, 60), (230, 140, 40), (230, 220, 50),
            (60, 200, 60), (60, 120, 230), (100, 60, 200), (160, 60, 180),
        ]
        rcx, rcy = 32, 60
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                dx = x - rcx
                dy = y - rcy
                dist = math.sqrt(dx * dx + dy * dy)
                band = dist - 42
                if 0 <= band < 7 and dy < 0:
                    bi = int(band)
                    rc = rainbow_colors[bi]
                    alpha = 0.45 + 0.08 * math.sin(t * 0.4 + x * 0.15)
                    existing = display.get_pixel(x, y)
                    blended = (int(existing[0] * (1 - alpha) + rc[0] * alpha),
                               int(existing[1] * (1 - alpha) + rc[1] * alpha),
                               int(existing[2] * (1 - alpha) + rc[2] * alpha))
                    display.set_pixel(x, y, blended)

        # Soft clouds
        for cx_cloud, cy_cloud, w in [(10, 50, 9), (50, 52, 10), (30, 54, 8)]:
            for ddx in range(-w, w + 1):
                for ddy in range(-2, 3):
                    dist = (ddx / w) ** 2 + (ddy / 2.5) ** 2
                    if dist < 1.0:
                        alpha = (1.0 - dist) * 0.2
                        px, py = cx_cloud + ddx, cy_cloud + ddy
                        if 0 <= px < 64 and 0 <= py < 64:
                            existing = display.get_pixel(px, py)
                            cloud = (int(240 * alpha), int(240 * alpha), int(245 * alpha))
                            display.set_pixel(px, py, _add_color(existing, cloud))

        # ── Large dove ── centered, ~24px wingspan, facing right
        # Gentle bob and drift
        cx = 30 + int(3 * math.sin(t * 0.2))
        cy = 28 + int(2 * math.sin(t * 0.35))
        wing_phase = math.sin(t * 1.8)  # slow, graceful flap
        wing_lift = wing_phase * 3  # wings move 3px up/down

        white = (240, 240, 235)
        light = (220, 220, 215)
        shadow = (190, 195, 200)
        dark = (160, 165, 170)

        # ── Body (elongated oval, ~10px long, 4px tall) ──
        # Body center at (cx, cy), extends left (tail) to right (head)
        body_pixels = []
        for bx in range(-4, 6):
            # Vertical thickness tapers at ends
            if bx <= -3:
                ys = [0]
            elif bx <= -1:
                ys = [-1, 0, 1]
            elif bx <= 3:
                ys = [-1, 0, 1, 2]  # chest is rounder underneath
            else:
                ys = [0, 1]
            for by in ys:
                # Shading: lighter on top, darker underneath
                if by <= -1:
                    c = white
                elif by == 0:
                    c = light if bx < 3 else white
                else:
                    c = shadow
                body_pixels.append((cx + bx, cy + by, c))

        for px, py, pc in body_pixels:
            if 0 <= px < 64 and 0 <= py < 64:
                display.set_pixel(px, py, pc)

        # ── Head (round, 3x3) ──
        head_x = cx + 7
        head_y = cy - 1
        for hdx in range(-1, 2):
            for hdy in range(-1, 2):
                if abs(hdx) + abs(hdy) < 3:  # rounded square
                    c = white if hdy <= 0 else light
                    hpx, hpy = head_x + hdx, head_y + hdy
                    if 0 <= hpx < 64 and 0 <= hpy < 64:
                        display.set_pixel(hpx, hpy, c)

        # Eye
        eye_x, eye_y = head_x + 1, head_y - 1
        if 0 <= eye_x < 64 and 0 <= eye_y < 64:
            display.set_pixel(eye_x, eye_y, (30, 30, 35))

        # Beak
        beak_x = head_x + 2
        beak_c = (200, 170, 80)
        if 0 <= beak_x < 64:
            display.set_pixel(beak_x, head_y, beak_c)
            if beak_x + 1 < 64:
                display.set_pixel(beak_x + 1, head_y, (180, 150, 60))

        # ── Olive branch (hanging from beak) ──
        branch = (70, 130, 40)
        leaf = (50, 110, 30)
        br_x = beak_x + 1
        br_y = head_y + 1
        for i in range(4):
            bpx, bpy = br_x + i // 2, br_y + i
            if 0 <= bpx < 64 and 0 <= bpy < 64:
                display.set_pixel(bpx, bpy, branch)
        # Leaves on the branch
        for lx, ly in [(br_x - 1, br_y + 1), (br_x + 1, br_y + 2),
                        (br_x - 1, br_y + 3), (br_x + 1, br_y + 4)]:
            if 0 <= lx < 64 and 0 <= ly < 64:
                display.set_pixel(lx, ly, leaf)

        # ── Tail (fan shape, spreading left and slightly up) ──
        tail_x = cx - 5
        tail_y = cy
        for fan in range(-3, 4):
            tx = tail_x - abs(fan) // 2
            ty = tail_y + fan
            c = light if abs(fan) < 2 else shadow
            if 0 <= tx < 64 and 0 <= ty < 64:
                display.set_pixel(tx, ty, c)
            if tx - 1 >= 0 and 0 <= ty < 64:
                display.set_pixel(tx - 1, ty, dark if abs(fan) > 1 else shadow)

        # ── Wings (large, sweeping, with feather detail) ──
        # Each wing: ~10px span, arcs upward from body sides
        wl = int(wing_lift)

        # Left wing (extends up-left from body)
        for i in range(10):
            # Wing curves upward and outward
            wx = cx - 2 - i
            # Parabolic arc: highest at wing tip
            base_arc = -int((i * i) / 12)
            wy = cy - 1 + base_arc - wl
            # Wing is 2-3 px thick near body, 1px at tip
            thickness = 3 if i < 3 else (2 if i < 7 else 1)
            for th in range(thickness):
                c = white if th == 0 else (light if th == 1 else shadow)
                wpx, wpy = wx, wy + th
                if 0 <= wpx < 64 and 0 <= wpy < 64:
                    display.set_pixel(wpx, wpy, c)

        # Right wing (extends up-right from body)
        for i in range(10):
            wx = cx + 3 + i
            base_arc = -int((i * i) / 12)
            wy = cy - 1 + base_arc - wl
            thickness = 3 if i < 3 else (2 if i < 7 else 1)
            for th in range(thickness):
                c = white if th == 0 else (light if th == 1 else shadow)
                wpx, wpy = wx, wy + th
                if 0 <= wpx < 64 and 0 <= wpy < 64:
                    display.set_pixel(wpx, wpy, c)

        # ── Soft glow/halo around the dove ──
        for dy in range(-8, 10):
            for dx in range(-14, 16):
                px, py = cx + dx, cy + dy
                if 0 <= px < 64 and 0 <= py < 64:
                    dist = math.sqrt(dx * dx + dy * dy)
                    if 8 < dist < 16:
                        glow_i = (1.0 - (dist - 8) / 8) * 0.08
                        gc = (int(255 * glow_i), int(255 * glow_i), int(240 * glow_i))
                        display.set_pixel(px, py, _add_color(display.get_pixel(px, py), gc))
