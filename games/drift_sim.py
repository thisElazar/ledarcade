"""
Drift Simulation Engine
=======================
LED arcade port of the Drift WebDemo water simulation.
Faithful to the original: same permutation table, terrain presets with island
falloff, 8-neighbor pressure-based flow with wall detection, and exact color
gradients from terrainMesh.js / waterMesh.js.
"""

import random
import math

# --- Constants (from constants.js) ---
FLOW_RATE = 0.15
MIN_DEPTH = 0.01
EVAPORATION_RATE = 0.00005
SPRING_FLOW_RATE = 3.0   # scaled down from 10.0 for 64x64 (vs 256x256)
MAX_HEIGHT = 350.0
MIN_HEIGHT = -100.0

# Default terrain preset params (from terrain.js)
NOISE_SCALE = 0.015
NOISE_OCTAVES = 5
NOISE_PERSISTENCE = 0.5

# 8-directional neighbors: (dx, dy, distance_multiplier) — from water.js
NEIGHBORS = [
    (-1,  0, 1.0),    # West
    ( 1,  0, 1.0),    # East
    ( 0, -1, 1.0),    # North
    ( 0,  1, 1.0),    # South
    (-1, -1, 1.414),  # NW
    ( 1, -1, 1.414),  # NE
    (-1,  1, 1.414),  # SW
    ( 1,  1, 1.414),  # SE
]

# Terrain presets (from terrain.js)
PRESETS = {
    'default':   {'scale': 0.015, 'octaves': 5, 'persistence': 0.5,
                  'height_mult': 0.7, 'falloff_power': 2,   'base_height': 0},
    'hills':     {'scale': 0.012, 'octaves': 4, 'persistence': 0.4,
                  'height_mult': 0.4, 'falloff_power': 1.5, 'base_height': 20},
    'mountains': {'scale': 0.02,  'octaves': 6, 'persistence': 0.55,
                  'height_mult': 1.0, 'falloff_power': 3,   'base_height': -50},
    'plains':    {'scale': 0.008, 'octaves': 3, 'persistence': 0.3,
                  'height_mult': 0.15,'falloff_power': 1.2, 'base_height': 30},
}

# -----------------------------------------------------------------------
# Perlin noise — exact permutation table from Drift WebDemo noise.js
# -----------------------------------------------------------------------
_PERM_BASE = [
    151,160,137,91,90,15,131,13,201,95,96,53,194,233,7,225,140,36,103,30,69,142,
    8,99,37,240,21,10,23,190,6,148,247,120,234,75,0,26,197,62,94,252,219,203,117,
    35,11,32,57,177,33,88,237,149,56,87,174,20,125,136,171,168,68,175,74,165,71,
    134,139,48,27,166,77,146,158,231,83,111,229,122,60,211,133,230,220,105,92,41,
    55,46,245,40,244,102,143,54,65,25,63,161,1,216,80,73,209,76,132,187,208,89,
    18,169,200,196,135,130,116,188,159,86,164,100,109,198,173,186,3,64,52,217,226,
    250,124,123,5,202,38,147,118,126,255,82,85,212,207,206,59,227,47,16,58,17,182,
    189,28,42,223,183,170,213,119,248,152,2,44,154,163,70,221,153,101,155,167,43,
    172,9,129,22,39,253,19,98,108,110,79,113,224,232,178,185,112,104,218,246,97,
    228,251,34,242,193,238,210,144,12,191,179,162,241,81,51,145,235,249,14,239,
    107,49,192,214,31,181,199,106,157,184,84,204,176,115,121,50,45,127,4,150,254,
    138,236,205,93,222,114,67,29,24,72,243,141,128,195,78,66,215,61,156,180,
]
_P = _PERM_BASE + _PERM_BASE  # doubled for wrapping


def _fade(t):
    return t * t * t * (t * (t * 6 - 15) + 10)


def _lerp(t, a, b):
    return a + t * (b - a)


def _grad(h, x, y):
    """Gradient function matching noise.js."""
    h &= 3
    u = x if h < 2 else y
    v = y if h < 2 else x
    return (u if (h & 1) == 0 else -u) + (v if (h & 2) == 0 else -v)


def noise2d(x, y):
    """2D Perlin noise matching Drift WebDemo noise.js."""
    X = int(math.floor(x)) & 255
    Y = int(math.floor(y)) & 255
    x -= math.floor(x)
    y -= math.floor(y)
    u = _fade(x)
    v = _fade(y)
    A = _P[X] + Y
    B = _P[X + 1] + Y
    return _lerp(v,
        _lerp(u, _grad(_P[A], x, y), _grad(_P[B], x - 1, y)),
        _lerp(u, _grad(_P[A + 1], x, y - 1), _grad(_P[B + 1], x - 1, y - 1)),
    )


def fbm(x, y, octaves=4, persistence=0.5):
    """Fractal brownian motion — matches noise.js fbm (normalized)."""
    total = 0.0
    frequency = 1.0
    amplitude = 1.0
    max_value = 0.0
    for _ in range(octaves):
        total += noise2d(x * frequency, y * frequency) * amplitude
        max_value += amplitude
        amplitude *= persistence
        frequency *= 2.0
    return total / max_value


# -----------------------------------------------------------------------
# Color helpers
# -----------------------------------------------------------------------
def _color_lerp(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _terrain_color(height):
    """Height-based terrain color matching terrainMesh.js getHeightColor.

    Normalizes height to 0-1 over MIN_HEIGHT..MAX_HEIGHT, then applies
    the exact same color-stop ladder from the WebDemo.
    """
    t = (height - MIN_HEIGHT) / (MAX_HEIGHT - MIN_HEIGHT)

    # Color stops — values are 0-255 (original was 0-1 floats)
    if t < 0.10:
        return _color_lerp((31, 28, 26), (56, 54, 48), t / 0.10)
    elif t < 0.15:
        return _color_lerp((56, 54, 48), (31, 56, 31), (t - 0.10) / 0.05)
    elif t < 0.30:
        return _color_lerp((31, 56, 31), (38, 89, 64), (t - 0.15) / 0.15)
    elif t < 0.35:
        return _color_lerp((209, 184, 115), (166, 140, 89), (t - 0.30) / 0.05)
    elif t < 0.60:
        return _color_lerp((46, 140, 38), (64, 122, 46), (t - 0.35) / 0.25)
    elif t < 0.75:
        return _color_lerp((26, 97, 26), (56, 82, 46), (t - 0.60) / 0.15)
    elif t < 0.90:
        return _color_lerp((89, 87, 82), (133, 128, 122), (t - 0.75) / 0.15)
    else:
        return _color_lerp((217, 217, 230), (250, 250, 255), (t - 0.90) / 0.10)


# Water color palette (from waterMesh.js)
_SHALLOW = (77, 191, 204)   # r:0.3 g:0.75 b:0.8
_MID     = (38, 115, 191)   # r:0.15 g:0.45 b:0.75
_DEEP    = (13, 38, 102)    # r:0.05 g:0.15 b:0.4
_FOAM    = (230, 242, 255)  # r:0.9 g:0.95 b:1.0

_SHALLOW_DEPTH = 2.0
_MID_DEPTH = 6.0
_DEEP_DEPTH = 15.0


def _water_color(depth):
    """Depth-based water color matching waterMesh.js."""
    if depth < _SHALLOW_DEPTH:
        return _SHALLOW
    elif depth < _MID_DEPTH:
        return _color_lerp(_SHALLOW, _MID,
                           (depth - _SHALLOW_DEPTH) / (_MID_DEPTH - _SHALLOW_DEPTH))
    elif depth < _DEEP_DEPTH:
        return _color_lerp(_MID, _DEEP,
                           (depth - _MID_DEPTH) / (_DEEP_DEPTH - _MID_DEPTH))
    return _DEEP


# -----------------------------------------------------------------------
# Simulation
# -----------------------------------------------------------------------
class DriftSim:
    """Terrain + water simulation engine — port of Drift WebDemo."""

    def __init__(self, width=64, height=64):
        self.width = width
        self.height = height
        n = width * height
        self.terrain = [0.0] * n
        self.water = [0.0] * n
        self.water_next = [0.0] * n
        self.velocity_x = [0.0] * n
        self.velocity_y = [0.0] * n
        self.springs = []

    # ---- terrain generation (terrain.js) ----

    def generate_terrain(self, preset='default', seed=None):
        """Generate terrain using fbm noise with island falloff."""
        if seed is None:
            seed = random.random() * 1000
        p = PRESETS.get(preset, PRESETS['default'])
        ns = p['scale']
        octaves = p['octaves']
        persistence = p['persistence']
        h_mult = p['height_mult']
        fp = p['falloff_power']
        base_h = p['base_height']

        # Scale noise for 64x64: original uses noiseScale on 256-wide grid.
        # Multiply scale by (256/64)=4 so terrain features are the same
        # relative size on the smaller grid.
        ns *= 4.0

        w, h = self.width, self.height
        for y in range(h):
            for x in range(w):
                nx = (x + seed) * ns
                ny = (y + seed) * ns
                val = fbm(nx, ny, octaves, persistence)
                # Second variation layer (matches terrain.js)
                val += 0.3 * fbm(nx * 2 + 100, ny * 2 + 100, 2, 0.5)

                # Island falloff
                dx = (x / w) * 2 - 1
                dy = (y / h) * 2 - 1
                dist = math.sqrt(dx * dx + dy * dy)
                falloff = max(0.0, 1.0 - dist ** fp)

                ht = base_h + val * falloff * MAX_HEIGHT * h_mult
                self.terrain[y * w + x] = max(MIN_HEIGHT, min(MAX_HEIGHT, ht))

        # Clear water
        n = w * h
        self.water = [0.0] * n
        self.water_next = [0.0] * n
        self.velocity_x = [0.0] * n
        self.velocity_y = [0.0] * n
        self.springs.clear()

    # ---- peak finding (water.js findPeaks) ----

    def find_peaks(self, count=4):
        """Find terrain peaks, matching water.js findPeaks."""
        w, h = self.width, self.height
        margin = max(2, w // 16)  # ~4 at 64
        min_dist = max(8, w // 8)  # ~8 at 64
        min_height = 20.0

        candidates = []
        for y in range(margin, h - margin):
            for x in range(margin, w - margin):
                idx = y * w + x
                ht = self.terrain[idx]
                if ht <= min_height:
                    continue
                # Check 8-neighbor local maximum
                is_peak = True
                for dx, dy, _ in NEIGHBORS:
                    ni = (y + dy) * w + (x + dx)
                    if self.terrain[ni] >= ht:
                        is_peak = False
                        break
                if is_peak:
                    candidates.append((ht, x, y))

        candidates.sort(reverse=True)

        peaks = []
        for ht, px, py in candidates:
            too_close = False
            for ex, ey in peaks:
                if math.sqrt((px - ex) ** 2 + (py - ey) ** 2) < min_dist:
                    too_close = True
                    break
            if not too_close:
                peaks.append((px, py))
                if len(peaks) >= count:
                    break
        return peaks

    # ---- springs ----

    def add_spring(self, x, y, flow_rate=None):
        if flow_rate is None:
            flow_rate = SPRING_FLOW_RATE
        self.springs.append({'x': int(x), 'y': int(y), 'rate': flow_rate})

    def remove_spring(self, x, y, radius=3):
        self.springs = [
            s for s in self.springs
            if math.sqrt((s['x'] - x) ** 2 + (s['y'] - y) ** 2) > radius
        ]

    # ---- brush tools ----

    def apply_brush(self, x, y, tool, radius=3, strength=2.0):
        """Apply terrain/water tool. Gaussian falloff matching terrain.js."""
        w, h = self.width, self.height

        if tool == 'spring':
            before = len(self.springs)
            self.remove_spring(x, y, radius=2)
            if len(self.springs) == before:
                self.add_spring(x, y)
            return

        sigma_sq = radius * radius / 2.0  # for Gaussian falloff

        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                dist = math.sqrt(dx * dx + dy * dy)
                if dist > radius:
                    continue
                nx, ny = x + dx, y + dy
                if not (0 <= nx < w and 0 <= ny < h):
                    continue
                idx = ny * w + nx
                falloff = math.exp(-(dist * dist) / sigma_sq)

                if tool == 'raise':
                    self.terrain[idx] = min(MAX_HEIGHT,
                        self.terrain[idx] + strength * falloff)
                elif tool == 'lower':
                    self.terrain[idx] = max(MIN_HEIGHT,
                        self.terrain[idx] - strength * falloff)
                elif tool == 'smooth':
                    total = self.terrain[idx]
                    cnt = 1
                    for ax, ay in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        sx, sy = nx + ax, ny + ay
                        if 0 <= sx < w and 0 <= sy < h:
                            total += self.terrain[sy * w + sx]
                            cnt += 1
                    self.terrain[idx] += (total / cnt - self.terrain[idx]) * 0.3 * falloff
                elif tool == 'water':
                    self.water[idx] += strength * 0.5 * falloff

    # ---- water simulation (water.js simulate) ----

    def simulate(self, dt):
        """Pressure-based 8-neighbor flow matching water.js."""
        w, h = self.width, self.height
        terrain = self.terrain
        water = self.water
        wn = self.water_next

        # Springs
        for s in self.springs:
            idx = s['y'] * w + s['x']
            water[idx] += s['rate'] * dt

        # Copy to next buffer
        for i in range(w * h):
            wn[i] = water[i]

        # Pressure-based flow with 8 neighbors
        for y in range(h):
            row = y * w
            for x in range(w):
                idx = row + x
                depth = water[idx]
                if depth < MIN_DEPTH:
                    continue

                t_here = terrain[idx]
                surface = t_here + depth

                total_flow = 0.0
                flow_vx = 0.0
                flow_vy = 0.0

                for ndx, ndy, dist_mult in NEIGHBORS:
                    nx, ny = x + ndx, y + ndy
                    if not (0 <= nx < w and 0 <= ny < h):
                        continue
                    ni = ny * w + nx
                    t_neighbor = terrain[ni]
                    s_neighbor = t_neighbor + water[ni]
                    pressure_diff = surface - s_neighbor

                    if pressure_diff <= 0:
                        continue

                    # Wall detection (water.js: heightDiff > waterHere * 0.5)
                    height_diff = t_neighbor - t_here
                    if height_diff > depth * 0.5:
                        continue

                    max_flow = depth * 0.25
                    flow = min(pressure_diff * FLOW_RATE / dist_mult, max_flow)

                    if flow > 0.0001:
                        wn[idx] -= flow
                        wn[ni] += flow
                        total_flow += flow
                        flow_vx += ndx * flow
                        flow_vy += ndy * flow

                # Update velocity (smoothed)
                if total_flow > 0:
                    self.velocity_x[idx] = self.velocity_x[idx] * 0.8 + flow_vx * 0.2
                    self.velocity_y[idx] = self.velocity_y[idx] * 0.8 + flow_vy * 0.2
                else:
                    self.velocity_x[idx] *= 0.95
                    self.velocity_y[idx] *= 0.95

        # Evaporation
        for i in range(w * h):
            water[i] = max(0.0, wn[i] - EVAPORATION_RATE * dt)

    # ---- rendering (terrainMesh.js + waterMesh.js colors) ----

    def get_terrain_color(self, x, y):
        return _terrain_color(self.terrain[y * self.width + x])

    def get_water_color(self, x, y):
        depth = self.water[y * self.width + x]
        if depth < MIN_DEPTH:
            return None
        return _water_color(depth)

    def get_combined_color(self, x, y):
        """Terrain + water blend. Foam boost at shorelines and fast flow."""
        w = self.width
        idx = y * w + x
        tc = _terrain_color(self.terrain[idx])
        depth = self.water[idx]
        if depth < MIN_DEPTH:
            return tc

        wc = _water_color(depth)

        # Foam from shoreline + flow speed (simplified waterMesh.js)
        foam = 0.0
        # Shoreline check: any dry 4-neighbor?
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < self.height:
                if self.water[ny * w + nx] < MIN_DEPTH:
                    foam += 0.4
                    break
        # Flow speed foam
        vx = self.velocity_x[idx]
        vy = self.velocity_y[idx]
        speed = math.sqrt(vx * vx + vy * vy)
        foam += min(0.3, speed * 0.3)
        foam = min(0.7, foam)

        # Blend foam into water color
        wr = int(wc[0] + (_FOAM[0] - wc[0]) * foam)
        wg = int(wc[1] + (_FOAM[1] - wc[1]) * foam)
        wb = int(wc[2] + (_FOAM[2] - wc[2]) * foam)

        # Alpha blend water over terrain
        alpha = min(1.0, 0.5 + depth / 10.0)
        return (
            clamp(int(tc[0] * (1 - alpha) + wr * alpha), 0, 255),
            clamp(int(tc[1] * (1 - alpha) + wg * alpha), 0, 255),
            clamp(int(tc[2] * (1 - alpha) + wb * alpha), 0, 255),
        )

    def get_spring_at(self, x, y, radius=2):
        for s in self.springs:
            if abs(s['x'] - x) + abs(s['y'] - y) <= radius:
                return s
        return None
