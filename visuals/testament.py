"""
Testament - Sacred Scenes
=============================
Ambient looping scenes from the world's sacred stories on 64x64 LED matrix.
Each scene is a stable, gently animated symbol.

Scenes:
  1. Burning Bush       - Fire that does not consume, sandals set aside
  2. Noah's Ark         - Ark on calm waters after the flood, rainbow above
  3. Star of Bethlehem  - Brilliant star over a quiet stable
  4. Hanuman's Mountain - Hanuman carries the Himalayan peak (Ramayana)
  5. The Bodhi Tree     - Siddhartha's night of enlightenment (Buddhism)
  6. Cave of Hira       - First revelation, light flooding the cave (Islam)
  7. The River          - Guru Nanak emerges from the river (Sikhism)

Controls:
  Up/Down     - Switch scene
  Left/Right  - Adjust speed
  Space/Z     - Scene action
  Escape      - Exit
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE

NUM_SCENES = 7


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


# ── Hanuman silhouette ──────────────────────────────────────────────

def _make_hanuman():
    """Hanuman flying silhouette — carrying mountain in raised right hand."""
    pixels = set()
    cx, cy = 30, 36  # body center

    # Head (round, ~4px)
    for dy in range(-2, 2):
        for dx in range(-2, 2):
            if dx * dx + dy * dy <= 4:
                pixels.add((cx + 6 + dx, cy - 6 + dy))

    # Crown / crest on head
    pixels.add((cx + 6, cy - 9))
    pixels.add((cx + 7, cy - 9))
    pixels.add((cx + 6, cy - 10))

    # Torso (angled, flying forward-right)
    for i in range(10):
        tx = cx + 4 - i
        ty = cy - 4 + i // 2
        for w in range(-1, 2):
            pixels.add((tx, ty + w))

    # Right arm — reaching UP to hold mountain
    for i in range(10):
        pixels.add((cx + 7 + i // 3, cy - 7 - i))
        pixels.add((cx + 8 + i // 3, cy - 7 - i))

    # Left arm — trailing back
    for i in range(7):
        pixels.add((cx - 2 - i, cy - 2 + i // 3))

    # Legs trailing behind and down
    for i in range(8):
        pixels.add((cx - 3 - i, cy + 2 + i // 2))
        pixels.add((cx - 2 - i, cy + 4 + i // 2))

    # Tail — long, curving upward behind
    tail_pts = []
    for i in range(14):
        tx = cx - 5 - i
        ty = cy + 1 - int(2.5 * math.sin(i * 0.35))
        tail_pts.append((tx, ty))
    for tx, ty in tail_pts:
        pixels.add((tx, ty))

    return pixels


HANUMAN_PIXELS = _make_hanuman()


def _make_mountain_chunk():
    """Irregular mountain chunk with trees/herbs on top, carried by Hanuman."""
    pixels = []
    rock = (120, 110, 95)
    rock_dark = (80, 72, 60)
    herb_glow = (80, 200, 80)
    tree_green = (30, 100, 30)

    mcx, mcy = 34, 14  # mountain center

    # Rocky mass — irregular ellipse
    for dy in range(-6, 5):
        for dx in range(-8, 9):
            dist = (dx / 8.0) ** 2 + (dy / 5.0) ** 2
            noise = math.sin(dx * 1.3 + dy * 0.7) * 0.15
            if dist + noise < 0.85:
                edge = dist > 0.6
                pixels.append((mcx + dx, mcy + dy,
                               rock_dark if edge else rock))

    # Trees on top of the mountain
    for tx_off in [-5, -2, 1, 4, 6]:
        tree_x = mcx + tx_off
        tree_top = mcy - 5 + int(abs(tx_off) * 0.3)
        # Trunk
        pixels.append((tree_x, tree_top + 2, (80, 55, 30)))
        pixels.append((tree_x, tree_top + 3, (80, 55, 30)))
        # Canopy
        for ddy in range(-1, 2):
            for ddx in range(-1, 2):
                if abs(ddx) + abs(ddy) <= 1:
                    pixels.append((tree_x + ddx, tree_top + ddy, tree_green))

    # Glowing herbs (sanjeevani) — a few bright spots
    for hx, hy in [(-3, -4), (2, -3), (5, -5), (-6, -3), (0, -5)]:
        pixels.append((mcx + hx, mcy + hy, herb_glow))

    return pixels


MOUNTAIN_PIXELS = _make_mountain_chunk()


# ── Bodhi Tree ──────────────────────────────────────────────────────

def _make_bodhi_tree():
    """Large Bodhi tree with spreading canopy."""
    pixels = []
    trunk_color = (90, 60, 30)
    trunk_dark = (60, 40, 20)
    tcx = 32  # tree center x
    trunk_base_y = 52

    # Trunk — thick, gnarled
    for y in range(35, trunk_base_y + 1):
        width = 2 + (y - 35) // 6
        for dx in range(-width, width + 1):
            wobble = int(1.5 * math.sin(y * 0.4))
            edge = abs(dx) >= width
            pixels.append((tcx + dx + wobble, y,
                           trunk_dark if edge else trunk_color))

    # Major roots spreading at base
    for side in [-1, 1]:
        for i in range(6):
            rx = tcx + side * (3 + i)
            ry = trunk_base_y + i // 3
            pixels.append((rx, ry, trunk_dark))
            pixels.append((rx, ry + 1, trunk_dark))

    # Branches — radiating outward from crown
    branches = [
        (-12, -4), (-9, -8), (-6, -12), (-3, -15),
        (0, -17), (3, -15), (6, -12), (9, -8), (12, -4),
        (-8, -12), (8, -12), (-4, -16), (4, -16),
    ]
    for bx, by in branches:
        # Draw branch line from trunk top to branch end
        steps = max(abs(bx), abs(by))
        for s in range(steps):
            t = s / max(1, steps)
            px = int(tcx + bx * t)
            py = int(35 + by * t)
            pixels.append((px, py, trunk_dark))

    # Canopy — large, spreading, heart-shaped leaves implied by density
    for y in range(16, 37):
        for x in range(14, 51):
            dx = (x - tcx) / 17.0
            dy = (y - 26) / 10.0
            # Rounded canopy shape — wider at middle, tapered at top and bottom
            dist = dx * dx + dy * dy
            noise = math.sin(x * 1.1 + y * 0.8) * 0.12 + math.sin(x * 2.3 - y * 1.5) * 0.08
            if dist + noise < 0.9:
                pixels.append((x, y, None))  # None = filled at draw time with leaf color

    return pixels


BODHI_TREE = _make_bodhi_tree()


def _make_seated_figure():
    """Small seated meditation figure, ~8px tall."""
    pixels = set()
    cx, cy = 32, 49  # sitting at base of tree

    # Head
    for dy in range(-1, 1):
        for dx in range(-1, 1):
            pixels.add((cx + dx, cy - 7 + dy))

    # Shoulders and torso
    for dx in range(-3, 4):
        pixels.add((cx + dx, cy - 5))
    for dy in range(-4, -1):
        for dx in range(-2, 3):
            pixels.add((cx + dx, cy + dy))

    # Crossed legs
    for dx in range(-4, 5):
        pixels.add((cx + dx, cy - 1))
        pixels.add((cx + dx, cy))
    for dx in range(-3, 4):
        pixels.add((cx + dx, cy + 1))

    return pixels


SEATED_FIGURE = _make_seated_figure()


# ── Cave of Hira ────────────────────────────────────────────────────

def _make_hira_mountain():
    """Mountain silhouette with cave opening."""
    pixels = []
    rock = (50, 42, 35)
    rock_light = (70, 60, 48)

    # Mountain shape — large, fills bottom 2/3
    peak_x, peak_y = 32, 12
    for y in range(peak_y, GRID_SIZE):
        # Mountain widens as y increases
        progress = (y - peak_y) / (GRID_SIZE - peak_y)
        half_w = int(4 + 28 * progress)
        for x in range(peak_x - half_w, peak_x + half_w + 1):
            if 0 <= x < GRID_SIZE:
                noise = math.sin(x * 0.5 + y * 0.3) * 0.1
                edge_dist = abs(x - peak_x) / max(1, half_w)
                is_light = noise > 0 and edge_dist < 0.7
                # Cave opening — don't draw rock here
                cave_cx, cave_cy = 32, 38
                cave_dx = (x - cave_cx) / 7.0
                cave_dy = (y - cave_cy) / 6.0
                in_cave = cave_dx * cave_dx + (cave_dy * 1.2) ** 2 < 1.0 and y >= cave_cy - 5
                if not in_cave:
                    pixels.append((x, y, rock_light if is_light else rock))

    return pixels


HIRA_MOUNTAIN = _make_hira_mountain()


# ── Guru Nanak figure ───────────────────────────────────────────────

def _make_nanak_figure():
    """Standing figure in the river, ~14px tall."""
    pixels = set()
    cx, cy = 32, 34  # chest center, standing in river (legs submerged)

    # Head with turban
    for dy in range(-3, 0):
        for dx in range(-2, 3):
            if dx * dx + dy * dy <= 5:
                pixels.add((cx + dx, cy - 10 + dy))
    # Turban top
    for dx in range(-2, 3):
        pixels.add((cx + dx, cy - 13))
        pixels.add((cx + dx, cy - 14))
    pixels.add((cx - 1, cy - 15))
    pixels.add((cx, cy - 15))
    pixels.add((cx + 1, cy - 15))

    # Neck
    pixels.add((cx, cy - 7))

    # Torso / robes — wider, flowing
    for dy in range(-6, 6):
        width = 3 + abs(dy) // 3
        for dx in range(-width, width + 1):
            pixels.add((cx + dx, cy + dy))

    # Arms slightly out to sides (palms up gesture)
    for i in range(4):
        pixels.add((cx - 4 - i, cy - 3 + i))
        pixels.add((cx + 4 + i, cy - 3 + i))

    return pixels


NANAK_FIGURE = _make_nanak_figure()


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
    description = "Sacred scenes"
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

        # -- Hanuman's Mountain --
        random.seed(42)
        self.hanu_stars = [(random.randint(0, 63), random.randint(0, 28),
                            random.random() * math.pi * 2,
                            0.3 + random.random() * 1.5)
                           for _ in range(35)]
        random.seed()
        self.hanu_wind = []  # wind trail particles
        self.hanu_herb_phase = 0.0

        # -- Bodhi Tree --
        random.seed(108)
        self.bodhi_leaves = []  # falling leaf particles
        self.bodhi_leaf_timer = 0.0
        self.bodhi_dawn = 0.0  # dawn light progression, cycles slowly
        random.seed()

        # -- Cave of Hira --
        random.seed(99)
        self.hira_stars = [(random.randint(0, 63), random.randint(0, 20),
                            random.random() * math.pi * 2,
                            0.3 + random.random() * 1.2)
                           for _ in range(30)]
        random.seed()
        self.hira_light_particles = []
        self.hira_pulse = 0.0

        # -- Guru Nanak --
        random.seed(52)
        self.nanak_stars = [(random.randint(0, 63), random.randint(0, 22),
                             random.random() * math.pi * 2,
                             0.3 + random.random() * 1.0)
                            for _ in range(25)]
        random.seed()
        self.nanak_ripples = []  # (cx, cy, radius, life)
        self.nanak_ripple_timer = 0.0
        self.nanak_glow = 0.0


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
        elif self.scene == 3:
            self._update_hanuman(scaled_dt)
        elif self.scene == 4:
            self._update_bodhi(scaled_dt)
        elif self.scene == 5:
            self._update_hira(scaled_dt)
        elif self.scene == 6:
            self._update_nanak(scaled_dt)

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
            self._draw_hanuman(display, t)
        elif self.scene == 4:
            self._draw_bodhi(display, t)
        elif self.scene == 5:
            self._draw_hira(display, t)
        elif self.scene == 6:
            self._draw_nanak(display, t)

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
    # SCENE 3: HANUMAN CARRYING THE MOUNTAIN (Ramayana)
    # ═════════════════════════════════════════════════════════════════

    def _update_hanuman(self, scaled_dt):
        self.hanu_herb_phase += scaled_dt

        # Wind trail particles streaming behind Hanuman
        if random.random() < 0.6:
            # Spawn from behind the figure
            wx = random.randint(10, 22)
            wy = random.randint(30, 42)
            self.hanu_wind.append([wx, wy, 0.5 + random.random() * 0.6])

        alive = []
        for w in self.hanu_wind:
            w[0] -= 12.0 * scaled_dt  # stream leftward
            w[1] += random.gauss(0, 0.5) * scaled_dt
            w[2] -= scaled_dt
            if w[2] > 0 and w[0] > -2:
                alive.append(w)
        self.hanu_wind = alive[-150:]

    def _draw_hanuman(self, display, t):
        # Night sky — deep indigo
        for y in range(GRID_SIZE):
            depth = y / GRID_SIZE
            r = int(8 + 10 * (1 - depth))
            g = int(5 + 8 * (1 - depth))
            b = int(30 + 25 * (1 - depth))
            for x in range(GRID_SIZE):
                display.set_pixel(x, y, (r, g, b))

        # Stars
        for sx, sy, phase, spd in self.hanu_stars:
            brightness = 0.2 + 0.8 * max(0, math.sin(t * spd + phase))
            gray = int(130 * brightness)
            display.set_pixel(sx, sy, (gray, gray, int(gray * 0.9)))

        # Ocean below — dark, distant
        for y in range(50, GRID_SIZE):
            for x in range(GRID_SIZE):
                wave = math.sin(x * 0.2 + t * 0.5 + y * 0.3) * 0.1
                depth = (y - 50) / 14.0
                b_val = max(0, int(60 * (0.5 - depth * 0.3 + wave)))
                g_val = max(0, int(30 * (0.5 - depth * 0.3 + wave)))
                display.set_pixel(x, y, (0, g_val, b_val))

        # Clouds — a few wisps drifting
        for ci, (cloud_y, cloud_phase) in enumerate([(44, 0), (47, 1.5), (52, 3.0)]):
            cloud_x = (t * 3 + cloud_phase * 20) % 80 - 10
            for dx in range(12):
                for dy in range(-1, 2):
                    cx_pos = int(cloud_x + dx)
                    cy_pos = cloud_y + dy
                    if 0 <= cx_pos < 64 and 0 <= cy_pos < 64:
                        dist = abs(dx - 6) / 6.0 + abs(dy) / 2.0
                        if dist < 1.0:
                            alpha = (1.0 - dist) * 0.15
                            existing = display.get_pixel(cx_pos, cy_pos)
                            cloud_c = (int(80 * alpha), int(80 * alpha), int(100 * alpha))
                            display.set_pixel(cx_pos, cy_pos, _add_color(existing, cloud_c))

        # Wind trails
        for wx, wy, life in self.hanu_wind:
            px, py = int(wx), int(wy)
            if 0 <= px < 64 and 0 <= py < 64:
                alpha = life * 0.4
                wc = (int(100 * alpha), int(80 * alpha), int(50 * alpha))
                display.set_pixel(px, py, _add_color(display.get_pixel(px, py), wc))

        # Mountain chunk with herbs
        herb_phase = self.hanu_herb_phase
        for mx, my, mc in MOUNTAIN_PIXELS:
            if 0 <= mx < 64 and 0 <= my < 64:
                if mc == (80, 200, 80):  # herb — pulsing glow
                    pulse = 0.6 + 0.4 * math.sin(herb_phase * 3.0 + mx * 0.5)
                    gc = _scale_color(mc, pulse)
                    display.set_pixel(mx, my, gc)
                else:
                    display.set_pixel(mx, my, mc)

        # Hanuman silhouette — warm amber/golden
        for hx, hy in HANUMAN_PIXELS:
            if 0 <= hx < 64 and 0 <= hy < 64:
                display.set_pixel(hx, hy, (180, 120, 40))

        # Divine glow around Hanuman
        glow_cx, glow_cy = 30, 34
        for dy in range(-8, 9):
            for dx in range(-8, 9):
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < 8:
                    gx, gy = glow_cx + dx, glow_cy + dy
                    if 0 <= gx < 64 and 0 <= gy < 64:
                        intensity = (1.0 - dist / 8) ** 2 * 0.2
                        pulse = 0.8 + 0.2 * math.sin(t * 2.0)
                        gc = (int(200 * intensity * pulse),
                              int(130 * intensity * pulse),
                              int(40 * intensity * pulse))
                        display.set_pixel(gx, gy, _add_color(display.get_pixel(gx, gy), gc))

    # ═════════════════════════════════════════════════════════════════
    # SCENE 4: SIDDHARTHA UNDER THE BODHI TREE (Buddhism)
    # ═════════════════════════════════════════════════════════════════

    def _update_bodhi(self, scaled_dt):
        self.bodhi_dawn += scaled_dt * 0.03  # very slow dawn cycle

        # Spawn falling leaves
        self.bodhi_leaf_timer += scaled_dt
        if self.bodhi_leaf_timer > 0.3:
            self.bodhi_leaf_timer = 0.0
            lx = random.randint(16, 48)
            ly = random.randint(16, 30)
            self.bodhi_leaves.append([
                float(lx), float(ly),
                random.gauss(0, 0.3),  # vx — gentle drift
                0.8 + random.random() * 0.6,  # vy — falling
                2.0 + random.random() * 3.0,  # life
                random.random() * math.pi * 2,  # sway phase
            ])

        alive = []
        for lf in self.bodhi_leaves:
            lf[4] -= scaled_dt
            if lf[4] <= 0:
                continue
            lf[0] += (lf[2] + 0.4 * math.sin(lf[5] + self.time * 1.5)) * scaled_dt
            lf[1] += lf[3] * scaled_dt
            alive.append(lf)
        self.bodhi_leaves = alive[-80:]

    def _draw_bodhi(self, display, t):
        # Sky — pre-dawn gradient, slowly cycling
        dawn = 0.3 + 0.2 * math.sin(self.bodhi_dawn)
        for y in range(GRID_SIZE):
            sky_t = y / GRID_SIZE
            r = int((10 + 50 * dawn) * (1 - sky_t * 0.5))
            g = int((8 + 30 * dawn) * (1 - sky_t * 0.3))
            b = int((30 + 15 * dawn) * (1 - sky_t * 0.2))
            # Warm horizon glow
            horizon_glow = max(0, 1.0 - abs(y - 55) / 12.0) * dawn * 0.6
            r = min(255, r + int(180 * horizon_glow))
            g = min(255, g + int(100 * horizon_glow))
            b = min(255, b + int(40 * horizon_glow))
            for x in range(GRID_SIZE):
                display.set_pixel(x, y, (r, g, b))

        # Morning star (Venus)
        star_x, star_y = 48, 14
        pulse = 0.7 + 0.3 * math.sin(t * 1.8)
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                dist = abs(dx) + abs(dy)
                if dist <= 2:
                    intensity = (1.0 - dist / 3.0) * pulse
                    sc = (int(255 * intensity), int(250 * intensity), int(200 * intensity))
                    px, py = star_x + dx, star_y + dy
                    if 0 <= px < 64 and 0 <= py < 64:
                        display.set_pixel(px, py, _add_color(display.get_pixel(px, py), sc))

        # Ground
        for y in range(53, GRID_SIZE):
            depth = (y - 53) / 11.0
            for x in range(GRID_SIZE):
                r = max(0, int(45 - 15 * depth))
                g = max(0, int(55 - 20 * depth))
                b = max(0, int(25 - 10 * depth))
                display.set_pixel(x, y, (r, g, b))

        # Bodhi tree — canopy, trunk, roots
        leaf_green_base = (25, 80, 20)
        leaf_green_light = (50, 120, 35)
        for bx, by, bc in BODHI_TREE:
            if 0 <= bx < 64 and 0 <= by < 64:
                if bc is None:
                    # Leaf pixel — vary color with noise
                    noise = math.sin(bx * 0.9 + by * 0.7 + t * 0.3) * 0.5
                    if noise > 0:
                        display.set_pixel(bx, by, leaf_green_light)
                    else:
                        display.set_pixel(bx, by, leaf_green_base)
                else:
                    display.set_pixel(bx, by, bc)

        # Falling leaves
        for lf in self.bodhi_leaves:
            lx, ly = int(lf[0]), int(lf[1])
            if 0 <= lx < 64 and 0 <= ly < 64:
                fade = min(1.0, lf[4] / 1.0)
                lc = (int(60 * fade), int(130 * fade), int(30 * fade))
                display.set_pixel(lx, ly, lc)

        # Seated figure — dark silhouette
        for fx, fy in SEATED_FIGURE:
            if 0 <= fx < 64 and 0 <= fy < 64:
                display.set_pixel(fx, fy, (30, 25, 20))

        # Soft enlightenment glow around the figure
        glow_cx, glow_cy = 32, 47
        pulse = 0.7 + 0.3 * math.sin(t * 0.8)
        for dy in range(-10, 11):
            for dx in range(-10, 11):
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < 10:
                    gx, gy = glow_cx + dx, glow_cy + dy
                    if 0 <= gx < 64 and 0 <= gy < 64:
                        intensity = (1.0 - dist / 10) ** 2 * 0.18 * pulse
                        gc = (int(255 * intensity), int(220 * intensity), int(120 * intensity))
                        display.set_pixel(gx, gy, _add_color(display.get_pixel(gx, gy), gc))

    # ═════════════════════════════════════════════════════════════════
    # SCENE 5: CAVE OF HIRA (Islam — First Revelation)
    # ═════════════════════════════════════════════════════════════════

    def _update_hira(self, scaled_dt):
        self.hira_pulse += scaled_dt

        # Light particles emanating from cave
        cave_cx, cave_cy = 32, 38
        if random.random() < 0.4:
            angle = random.gauss(0, 0.8) - math.pi / 2  # mostly upward
            speed = 1.5 + random.random() * 2.0
            self.hira_light_particles.append([
                float(cave_cx + random.gauss(0, 2)),
                float(cave_cy - 2),
                math.cos(angle) * speed,
                math.sin(angle) * speed,
                1.0 + random.random() * 1.5,  # life
            ])

        alive = []
        for p in self.hira_light_particles:
            p[4] -= scaled_dt
            if p[4] <= 0:
                continue
            p[0] += p[2] * scaled_dt
            p[1] += p[3] * scaled_dt
            alive.append(p)
        self.hira_light_particles = alive[-100:]

    def _draw_hira(self, display, t):
        # Deep desert night sky
        for y in range(GRID_SIZE):
            depth = y / GRID_SIZE
            r = int(6 + 6 * (1 - depth))
            g = int(4 + 6 * (1 - depth))
            b = int(18 + 22 * (1 - depth))
            for x in range(GRID_SIZE):
                display.set_pixel(x, y, (r, g, b))

        # Stars
        for sx, sy, phase, spd in self.hira_stars:
            brightness = 0.2 + 0.8 * max(0, math.sin(t * spd + phase))
            gray = int(120 * brightness)
            display.set_pixel(sx, sy, (gray, gray, int(gray * 0.9)))

        # Crescent moon
        moon_x, moon_y = 50, 10
        for dy in range(-5, 6):
            for dx in range(-5, 6):
                dist = math.sqrt(dx * dx + dy * dy)
                # Outer circle minus inner offset circle = crescent
                inner_dist = math.sqrt((dx - 2) ** 2 + dy * dy)
                if dist <= 5 and inner_dist > 4.5:
                    px, py = moon_x + dx, moon_y + dy
                    if 0 <= px < 64 and 0 <= py < 64:
                        intensity = (1.0 - dist / 6.0) * 0.9
                        mc = (int(240 * intensity), int(230 * intensity), int(190 * intensity))
                        display.set_pixel(px, py, mc)

        # Moon glow
        for dy in range(-8, 9):
            for dx in range(-8, 9):
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < 8:
                    px, py = moon_x + dx, moon_y + dy
                    if 0 <= px < 64 and 0 <= py < 64:
                        intensity = (1.0 - dist / 8) ** 2 * 0.08
                        gc = (int(200 * intensity), int(190 * intensity), int(150 * intensity))
                        display.set_pixel(px, py, _add_color(display.get_pixel(px, py), gc))

        # Desert floor
        for y in range(56, GRID_SIZE):
            depth = (y - 56) / 8.0
            for x in range(GRID_SIZE):
                display.set_pixel(x, y, (max(0, int(50 - 20 * depth)),
                                         max(0, int(40 - 15 * depth)),
                                         max(0, int(25 - 10 * depth))))

        # Mountain with cave
        for mx, my, mc in HIRA_MOUNTAIN:
            if 0 <= mx < 64 and 0 <= my < 64:
                display.set_pixel(mx, my, mc)

        # Cave interior — dark
        cave_cx, cave_cy = 32, 38
        for dy in range(-5, 6):
            for dx in range(-6, 7):
                cave_dx = dx / 7.0
                cave_dy = dy / 6.0
                if cave_dx ** 2 + (cave_dy * 1.2) ** 2 < 1.0 and cave_cy + dy >= 33:
                    px, py = cave_cx + dx, cave_cy + dy
                    if 0 <= px < 64 and 0 <= py < 64:
                        display.set_pixel(px, py, (4, 3, 8))

        # Divine light flooding the cave — pulsing, golden-white
        light_pulse = 0.6 + 0.4 * math.sin(self.hira_pulse * 1.2)
        # Light source from above/within
        light_cx, light_cy = 32, 34
        for dy in range(-8, 12):
            for dx in range(-10, 11):
                px, py = light_cx + dx, light_cy + dy
                if 0 <= px < 64 and 0 <= py < 64:
                    dist = math.sqrt(dx * dx + (dy * 1.3) ** 2)
                    if dist < 10:
                        # Check if inside or near cave area
                        cave_dx = dx / 7.0
                        cave_dy = (py - cave_cy) / 6.0
                        in_cave = cave_dx ** 2 + (cave_dy * 1.2) ** 2 < 1.2
                        if in_cave or dy < -2:
                            intensity = (1.0 - dist / 10) ** 1.5 * 0.5 * light_pulse
                            lc = (int(255 * intensity),
                                  int(240 * intensity),
                                  int(180 * intensity))
                            display.set_pixel(px, py,
                                              _add_color(display.get_pixel(px, py), lc))

        # Light particles rising from cave
        for p in self.hira_light_particles:
            px, py = int(p[0]), int(p[1])
            if 0 <= px < 64 and 0 <= py < 64:
                fade = min(1.0, p[4] / 0.5)
                lc = (int(255 * fade * 0.5), int(240 * fade * 0.5), int(180 * fade * 0.4))
                display.set_pixel(px, py, _add_color(display.get_pixel(px, py), lc))

        # Rim light on cave edges
        for angle_deg in range(-60, 61, 5):
            angle = math.radians(angle_deg)
            for r_off in range(1, 3):
                rim_x = int(cave_cx + math.cos(angle) * (6 + r_off * 0.5))
                rim_y = int(cave_cy - 3 + math.sin(angle) * 5)
                if 0 <= rim_x < 64 and 0 <= rim_y < 64:
                    rim_i = 0.15 * light_pulse
                    rc = (int(200 * rim_i), int(180 * rim_i), int(120 * rim_i))
                    display.set_pixel(rim_x, rim_y,
                                      _add_color(display.get_pixel(rim_x, rim_y), rc))

    # ═════════════════════════════════════════════════════════════════
    # SCENE 6: GURU NANAK AT THE RIVER (Sikhism)
    # ═════════════════════════════════════════════════════════════════

    def _update_nanak(self, scaled_dt):
        self.nanak_glow += scaled_dt

        # Spawn ripples periodically from the figure
        self.nanak_ripple_timer += scaled_dt
        if self.nanak_ripple_timer > 0.8:
            self.nanak_ripple_timer = 0.0
            self.nanak_ripples.append([32.0, 42.0, 0.0, 3.5])  # cx, cy, radius, life

        alive = []
        for rip in self.nanak_ripples:
            rip[2] += 4.0 * scaled_dt  # expand
            rip[3] -= scaled_dt  # fade
            if rip[3] > 0:
                alive.append(rip)
        self.nanak_ripples = alive

    def _draw_nanak(self, display, t):
        # Dawn sky — warm, golden hour
        for y in range(GRID_SIZE):
            sky_t = y / GRID_SIZE
            r = int(30 + 60 * (1 - sky_t))
            g = int(20 + 40 * (1 - sky_t))
            b = int(50 + 30 * (1 - sky_t))
            # Horizon warmth
            horizon = max(0, 1.0 - abs(y - 30) / 15.0) * 0.5
            r = min(255, r + int(150 * horizon))
            g = min(255, g + int(80 * horizon))
            b = min(255, b + int(30 * horizon))
            for x in range(GRID_SIZE):
                display.set_pixel(x, y, (r, g, b))

        # Stars (fading with dawn)
        dawn_fade = 0.4
        for sx, sy, phase, spd in self.nanak_stars:
            brightness = (0.2 + 0.8 * max(0, math.sin(t * spd + phase))) * dawn_fade
            gray = int(100 * brightness)
            if gray > 5:
                display.set_pixel(sx, sy, (gray, gray, int(gray * 0.9)))

        # Riverbanks — earth tones
        for y in range(36, GRID_SIZE):
            for x in list(range(0, 10)) + list(range(54, 64)):
                depth = (y - 36) / 28.0
                bank_noise = math.sin(x * 0.5 + y * 0.3) * 0.1
                r = max(0, int((60 - 20 * depth) * (1 + bank_noise)))
                g = max(0, int((70 - 25 * depth) * (1 + bank_noise)))
                b = max(0, int((30 - 10 * depth) * (1 + bank_noise)))
                display.set_pixel(x, y, (r, g, b))

        # Trees on banks
        for tree_x, bank_side in [(4, -1), (7, -1), (57, 1), (61, 1)]:
            trunk_y_base = 38
            # Trunk
            for ty in range(trunk_y_base, trunk_y_base + 6):
                display.set_pixel(tree_x, ty, (60, 40, 20))
            # Canopy
            for cdy in range(-4, 1):
                for cdx in range(-2, 3):
                    cx_p = tree_x + cdx
                    cy_p = trunk_y_base + cdy
                    if 0 <= cx_p < 64 and 0 <= cy_p < 64:
                        if abs(cdx) + abs(cdy) <= 3:
                            noise = math.sin(cx_p + cy_p * 1.5) * 0.3
                            g_val = int(70 + 30 * noise)
                            display.set_pixel(cx_p, cy_p, (20, g_val, 15))

        # River water
        for y in range(36, GRID_SIZE):
            for x in range(10, 54):
                wave1 = math.sin(x * 0.2 + t * 0.8 + y * 0.15) * 0.1
                wave2 = math.sin(x * 0.5 - t * 0.5 + y * 0.1) * 0.05
                depth = (y - 36) / 28.0
                brightness = max(0, min(1, 0.5 - 0.15 * depth + wave1 + wave2))
                r = int(20 * brightness)
                g = int(60 * brightness)
                b = int(130 * brightness)
                display.set_pixel(x, y, (r, g, b))

        # Ripples expanding from figure
        for rip in self.nanak_ripples:
            rcx, rcy, radius, life = rip
            if radius < 1:
                continue
            alpha = (life / 3.5) * 0.3
            for angle_step in range(60):
                a = angle_step * math.pi * 2 / 60
                rx = int(rcx + math.cos(a) * radius)
                ry = int(rcy + math.sin(a) * radius * 0.4)  # flatten vertically
                if 10 <= rx < 54 and 36 <= ry < 64:
                    rc = (int(180 * alpha), int(200 * alpha), int(255 * alpha))
                    display.set_pixel(rx, ry, _add_color(display.get_pixel(rx, ry), rc))

        # Nanak figure — warm white/cream robes
        robe_color = (200, 190, 170)
        turban_color = (180, 160, 130)
        skin_color = (170, 130, 90)
        cx, cy = 32, 34
        for fx, fy in NANAK_FIGURE:
            if 0 <= fx < 64 and 0 <= fy < 64:
                if fy <= cy - 13:
                    display.set_pixel(fx, fy, turban_color)
                elif fy <= cy - 7:
                    display.set_pixel(fx, fy, skin_color)
                else:
                    display.set_pixel(fx, fy, robe_color)

        # Divine glow around Nanak
        glow_pulse = 0.7 + 0.3 * math.sin(self.nanak_glow * 1.0)
        for dy in range(-14, 15):
            for dx in range(-10, 11):
                dist = math.sqrt(dx * dx + (dy * 0.7) ** 2)
                if dist < 12:
                    gx, gy = cx + dx, cy + dy
                    if 0 <= gx < 64 and 0 <= gy < 64:
                        intensity = (1.0 - dist / 12) ** 2 * 0.2 * glow_pulse
                        gc = (int(255 * intensity),
                              int(230 * intensity),
                              int(180 * intensity))
                        display.set_pixel(gx, gy,
                                          _add_color(display.get_pixel(gx, gy), gc))

        # Water glow — reflection of the divine light in the river
        for y in range(40, 56):
            for x in range(20, 44):
                dx = x - 32
                dy = y - 42
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < 14:
                    wave = math.sin(x * 0.3 + t * 1.2 + y * 0.2) * 0.3
                    intensity = (1.0 - dist / 14) ** 2 * 0.15 * glow_pulse * (0.7 + wave)
                    if intensity > 0:
                        gc = (int(200 * intensity), int(180 * intensity), int(120 * intensity))
                        display.set_pixel(x, y,
                                          _add_color(display.get_pixel(x, y), gc))


