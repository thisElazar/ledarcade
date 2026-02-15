"""
Frozen Lake
===========
A frozen black lake under an absent sky. The ice is not dead — it is
held. Tension in the surface. Hairline cracks with soft glow halos.
Something drifting with intention far below. Trapped things that are
not quite still.

When you press a button, presence arrives — spreading outward from
the cracks like warmth through ice. The surface shifts from window
to floor. Cracks widen into glowing channels. The boundary between
above and below becomes less certain. Things that were held begin
to rise.

Based on convergent imagination experiments (basin-mapping-findings.md):
252 independent AI invocations across two model architectures
converged on this same scene.

Controls:
  Action (Space/Z) - Presence arrives (hold or tap to sustain)
  Joystick         - Shift viewpoint across the lake
"""

import math
import random
from collections import deque
from . import Visual, Display, Colors, GRID_SIZE


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _noise2d(x, y, seed=0.0):
    """Cheap 2D noise via layered sines. Returns ~0.0-1.0."""
    v = (math.sin(x * 0.37 + y * 0.71 + seed * 1.3) * 0.5
         + math.sin(x * 0.13 - y * 0.53 + seed * 0.7) * 0.3
         + math.sin((x + y) * 0.29 + seed * 2.1) * 0.2)
    return (v + 1.0) * 0.5


def _soft_blob(px, py, bx, by, radius):
    """Gaussian-ish falloff from (bx,by). Returns 0.0-1.0."""
    dx = px - bx
    dy = py - by
    d2 = dx * dx + dy * dy
    r2 = radius * radius
    if d2 > r2 * 4:
        return 0.0
    return math.exp(-d2 / (2.0 * r2))


def _lerp(a, b, t):
    return a + (b - a) * t


# ---------------------------------------------------------------------------
# Crack generation
# ---------------------------------------------------------------------------

def _generate_cracks(num_seeds=4, grid=GRID_SIZE):
    cracks = []
    for _ in range(num_seeds):
        sx = random.randint(10, grid - 11)
        sy = random.randint(10, grid - 11)
        angle = random.uniform(0, 2 * math.pi)
        _grow_crack(cracks, sx, sy, angle, length=random.randint(12, 28),
                    generation=0, max_gen=3, grid=grid)
    return cracks


def _grow_crack(cracks, x, y, angle, length, generation, max_gen, grid):
    seen = set()
    for step in range(length):
        ix, iy = int(round(x)), int(round(y))
        if not (0 <= ix < grid and 0 <= iy < grid):
            break
        if (ix, iy) not in seen:
            cracks.append((ix, iy, generation))
            seen.add((ix, iy))
        angle += random.uniform(-0.25, 0.25)
        x += math.cos(angle)
        y += math.sin(angle)
        if generation < max_gen and step > 3 and random.random() < 0.2:
            branch_angle = angle + random.choice([-1, 1]) * random.uniform(0.5, 1.0)
            branch_len = random.randint(4, max(5, length - step))
            _grow_crack(cracks, x, y, branch_angle, branch_len,
                        generation + 1, max_gen, grid)


# ---------------------------------------------------------------------------
# Deep shapes — things that drift with intention
# ---------------------------------------------------------------------------

_ST_DRIFT = 0
_ST_PAUSE = 1
_ST_TURN  = 2
_ST_SURGE = 3


def _make_deep_shapes(count=3):
    shapes = []
    for _ in range(count):
        heading = random.uniform(0, 2 * math.pi)
        shapes.append({
            "cx": random.uniform(14, GRID_SIZE - 15),
            "cy": random.uniform(14, GRID_SIZE - 15),
            "radius": random.uniform(6, 11),
            "speed": random.uniform(0.12, 0.22),
            "heading": heading,
            "vx": math.cos(heading) * 0.15,
            "vy": math.sin(heading) * 0.15,
            "state": _ST_DRIFT,
            "state_timer": random.uniform(6, 14),
            "surge_amount": 0.0,      # 0-1, how close to surface
            "base_glow": 1.0,
        })
    return shapes


# ---------------------------------------------------------------------------
# Trapped objects
# ---------------------------------------------------------------------------

def _make_trapped_objects(count=7):
    objects = []
    for _ in range(count):
        x = random.uniform(4, GRID_SIZE - 5)
        y = random.uniform(4, GRID_SIZE - 5)
        objects.append({
            "x": x, "y": y,
            "home_x": x, "home_y": y,
            "depth": random.uniform(0.3, 0.85),
            "size": random.choice([1, 1, 1, 2]),
            "hue": random.choice(["bubble", "bubble", "leaf", "leaf", "sediment"]),
            "phase": random.uniform(0, 2 * math.pi),
            # micro-drift state
            "drift_vx": 0.0, "drift_vy": 0.0,
            "drift_timer": random.uniform(5, 20),
        })
    return objects


# ---------------------------------------------------------------------------
# The visual
# ---------------------------------------------------------------------------

class FrozenLake(Visual):
    name = "FROZEN LAKE"
    description = "Black ice, hairline cracks, something moving below"
    category = "digital"

    # Presence timing
    PRESENCE_PER_PRESS = 4.0
    PRESENCE_MAX = 20.0
    PRESENCE_FADE_IN = 2.5
    PRESENCE_FADE_OUT = 4.0

    # --- Palette: STILL ---
    ICE_BASE = (2, 4, 9)
    ICE_RANGE = 7
    CRACK_STILL = (10, 14, 24)
    CRACK_GLOW_STILL = (3, 5, 10)
    DEPTH_STILL = (6, 12, 22)

    # --- Palette: PRESENT ---
    ICE_PRESENT = (10, 16, 32)
    CRACK_PRESENT = (100, 140, 220)
    CRACK_GLOW_PRESENT = (25, 40, 75)
    DEPTH_PRESENT = (30, 55, 100)

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.presence_timer = 0.0
        self.presence_amount = 0.0
        self._fading_in = False
        self._held = False

        # Generate landscape
        self.cracks = _generate_cracks(num_seeds=4)
        self.crack_set = {}
        for cx, cy, gen in self.cracks:
            if (cx, cy) not in self.crack_set or gen < self.crack_set[(cx, cy)]:
                self.crack_set[(cx, cy)] = gen

        # Crack glow halo — rebuilt when cracks change
        self.crack_glow = {}
        self._rebuild_crack_glow()

        # Distance-to-nearest-crack (BFS)
        self.crack_dist = [[999.0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self._rebuild_crack_dist()

        # Crack adjacency for stress waves
        self._crack_adj = {}
        self._rebuild_crack_adj()

        self.trapped = _make_trapped_objects(7)
        self.deep_shapes = _make_deep_shapes(3)
        self.noise_offset = random.uniform(0, 100)
        self.pulse_travelers = []
        self.view_x = 0.0
        self.view_y = 0.0

        # Ice texture — generated once, the surface is frozen
        self._ice_texture = [[0.0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self._rebuild_ice_texture()

        # Memory field — where deep shapes have passed
        self._memory = [[0.0] * GRID_SIZE for _ in range(GRID_SIZE)]

        # Settling crack events
        self._next_crack_event = random.uniform(12, 25)

        # Propagating cracks (pixel-by-pixel drawing)
        self._propagating = []  # list of {pixels: [(x,y,gen),...], idx: int, timer: float}

        # Stress waves through crack network
        self._stress_waves = {}  # (x,y) -> brightness 0-1

        # Pressure front (slow diagonal sweep)
        self._pressure_front = None  # {pos, angle_x, angle_y, speed}
        self._next_pressure = random.uniform(20, 40)

        # Rare deep glints
        self._glint = None  # {x, y, timer}
        self._next_glint = random.uniform(8, 18)

    # -------------------------------------------------------------------
    # Precomputation
    # -------------------------------------------------------------------

    def _rebuild_crack_glow(self):
        """Build glow halo around all crack pixels. Radius depends on presence at draw time."""
        self.crack_glow = {}
        for (cx, cy), gen in self.crack_set.items():
            gen_fade = max(0.25, 1.0 - gen * 0.25)
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                        if (nx, ny) not in self.crack_set:
                            dist_fade = 0.7 if (dx == 0 or dy == 0) else 0.4
                            val = gen_fade * dist_fade
                            self.crack_glow[(nx, ny)] = max(
                                self.crack_glow.get((nx, ny), 0), val)

    def _rebuild_crack_dist(self):
        """BFS distance from all crack pixels, capped at 20."""
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                self.crack_dist[y][x] = 999.0
        q = deque()
        for (cx, cy) in self.crack_set:
            self.crack_dist[cy][cx] = 0.0
            q.append((cx, cy))
        while q:
            x, y = q.popleft()
            d = self.crack_dist[y][x]
            if d >= 20:
                continue
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                        step = 1.0 if (dx == 0 or dy == 0) else 1.414
                        nd = d + step
                        if nd < self.crack_dist[ny][nx]:
                            self.crack_dist[ny][nx] = nd
                            q.append((nx, ny))

    def _rebuild_crack_adj(self):
        """Build adjacency for crack pixels (for stress wave propagation)."""
        self._crack_adj = {}
        for (cx, cy) in self.crack_set:
            neighbors = []
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = cx + dx, cy + dy
                    if (nx, ny) in self.crack_set:
                        neighbors.append((nx, ny))
            self._crack_adj[(cx, cy)] = neighbors

    def _rebuild_ice_texture(self):
        """Two-scale ice texture — generated once."""
        off = self.noise_offset
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                base = _noise2d(x * 0.035 + off, y * 0.035 + off, seed=off * 0.1)
                detail = _noise2d(x * 0.09 + off * 1.3, y * 0.09 - off * 0.7, seed=17.0)
                self._ice_texture[y][x] = base * 0.7 + detail * 0.3

    # -------------------------------------------------------------------
    # Input
    # -------------------------------------------------------------------

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.action_l or input_state.action_r:
            self.presence_timer = min(
                self.presence_timer + self.PRESENCE_PER_PRESS,
                self.PRESENCE_MAX)
            self._fading_in = True
            consumed = True
        self._held = input_state.action_l_held or input_state.action_r_held
        if input_state.dx != 0 or input_state.dy != 0:
            self.view_x = max(-16, min(16, self.view_x + input_state.dx * 0.5))
            self.view_y = max(-16, min(16, self.view_y + input_state.dy * 0.5))
            consumed = True
        return consumed

    # -------------------------------------------------------------------
    # Update
    # -------------------------------------------------------------------

    def update(self, dt):
        self.time += dt
        t = self.time

        # --- Presence ---
        # Holding the button continuously sustains presence
        if self._held:
            self.presence_timer = min(
                self.presence_timer + dt * 2.0, self.PRESENCE_MAX)
            self._fading_in = True

        if self.presence_timer > 0:
            self.presence_timer -= dt
            if self.presence_timer <= 0:
                self.presence_timer = 0
                self._fading_in = False

        if self.presence_timer > 0 and self._fading_in:
            self.presence_amount = min(1.0,
                self.presence_amount + dt / self.PRESENCE_FADE_IN)
        else:
            self.presence_amount = max(0.0,
                self.presence_amount - dt / self.PRESENCE_FADE_OUT)

        p = self.presence_amount

        # --- Deep shapes: velocity-based with behavioral states ---
        for shape in self.deep_shapes:
            shape["state_timer"] -= dt

            if shape["state"] == _ST_DRIFT:
                if shape["state_timer"] <= 0:
                    # Transition: maybe pause, maybe surge
                    roll = random.random()
                    if roll < 0.15 and p < 0.2:
                        shape["state"] = _ST_SURGE
                        shape["surge_duration"] = random.uniform(2.0, 3.5)
                        shape["state_timer"] = shape["surge_duration"]
                    elif roll < 0.5:
                        shape["state"] = _ST_PAUSE
                        shape["state_timer"] = random.uniform(3.0, 8.0)
                        shape["base_glow"] = 1.3  # brightens when pausing
                    else:
                        shape["state"] = _ST_TURN
                        shape["state_timer"] = random.uniform(1.0, 2.0)
                        shape["target_heading"] = shape["heading"] + random.uniform(-1.2, 1.2)

                # Move with current velocity
                shape["cx"] += shape["vx"] * dt
                shape["cy"] += shape["vy"] * dt

            elif shape["state"] == _ST_PAUSE:
                # Held still — the "watching" moment
                if shape["state_timer"] <= 0:
                    shape["state"] = _ST_TURN
                    shape["state_timer"] = random.uniform(1.0, 2.0)
                    shape["target_heading"] = shape["heading"] + random.uniform(-1.2, 1.2)
                    shape["base_glow"] = 1.0

            elif shape["state"] == _ST_TURN:
                # Gradually shift heading toward stored target
                diff = shape.get("target_heading", shape["heading"]) - shape["heading"]
                shape["heading"] += diff * dt * 2.0
                spd = shape["speed"]
                shape["vx"] = math.cos(shape["heading"]) * spd
                shape["vy"] = math.sin(shape["heading"]) * spd
                if shape["state_timer"] <= 0:
                    shape["state"] = _ST_DRIFT
                    shape["state_timer"] = random.uniform(6, 14)
                # Still move while turning
                shape["cx"] += shape["vx"] * dt
                shape["cy"] += shape["vy"] * dt

            elif shape["state"] == _ST_SURGE:
                # Press toward surface — surge_amount rises then falls
                dur = shape.get("surge_duration", 3.5)
                progress = 1.0 - shape["state_timer"] / dur
                shape["surge_amount"] = math.sin(min(1.0, progress) * math.pi)
                if shape["state_timer"] <= 0:
                    shape["surge_amount"] = 0.0
                    shape["state"] = _ST_DRIFT
                    shape["state_timer"] = random.uniform(8, 16)

            # During presence: bias toward center (approaching)
            if p > 0.2:
                cx_diff = GRID_SIZE / 2 - shape["cx"]
                cy_diff = GRID_SIZE / 2 - shape["cy"]
                shape["cx"] += cx_diff * dt * 0.02 * p
                shape["cy"] += cy_diff * dt * 0.02 * p

            # Boundary avoidance (gentle)
            margin = 8
            if shape["cx"] < margin:
                shape["vx"] += dt * 0.3
            elif shape["cx"] > GRID_SIZE - margin:
                shape["vx"] -= dt * 0.3
            if shape["cy"] < margin:
                shape["vy"] += dt * 0.3
            elif shape["cy"] > GRID_SIZE - margin:
                shape["vy"] -= dt * 0.3

            # Deposit into memory field
            icx, icy = int(shape["cx"]), int(shape["cy"])
            rad = int(shape["radius"])
            for my in range(max(0, icy - rad), min(GRID_SIZE, icy + rad + 1)):
                for mx in range(max(0, icx - rad), min(GRID_SIZE, icx + rad + 1)):
                    d2 = (mx - shape["cx"])**2 + (my - shape["cy"])**2
                    r2 = shape["radius"] * shape["radius"]
                    if d2 < r2:
                        deposit = (1.0 - d2 / r2) * dt * 0.25
                        self._memory[my][mx] = min(1.0,
                            self._memory[my][mx] + deposit)

        # Decay memory field
        decay = dt * 0.015  # ~60 seconds to fully fade
        for y in range(GRID_SIZE):
            row = self._memory[y]
            for x in range(GRID_SIZE):
                if row[x] > 0:
                    row[x] = max(0.0, row[x] - decay)

        # --- Trapped objects: micro-drift in still state ---
        for obj in self.trapped:
            if p > 0.15:
                # Presence: things begin to rise
                if obj["hue"] == "bubble":
                    obj["y"] -= dt * 0.6 * p
                    if obj["y"] < -2:
                        obj["y"] = GRID_SIZE + 2
                        obj["x"] = random.uniform(4, GRID_SIZE - 5)
                elif obj["hue"] == "leaf":
                    obj["x"] += dt * 0.3 * math.sin(t + obj["phase"])
            else:
                # Still state: imperceptible micro-drift
                obj["drift_timer"] -= dt
                if obj["drift_timer"] <= 0:
                    # New micro-drift impulse
                    obj["drift_vx"] = random.uniform(-0.015, 0.015)
                    obj["drift_vy"] = random.uniform(-0.015, 0.015)
                    obj["drift_timer"] = random.uniform(5, 20)

                obj["x"] += obj["drift_vx"] * dt
                obj["y"] += obj["drift_vy"] * dt

                # Gentle restoring force toward home
                obj["x"] += (obj["home_x"] - obj["x"]) * dt * 0.01
                obj["y"] += (obj["home_y"] - obj["y"]) * dt * 0.01

        # --- Pulse travelers (presence only) ---
        if p > 0.2:
            if random.random() < dt * 1.5:  # slower spawn rate
                self._spawn_pulse_traveler()

        alive = []
        for trav in self.pulse_travelers:
            trav["pos"] += dt * trav["speed"]
            if trav["pos"] < len(trav["path"]):
                alive.append(trav)
        self.pulse_travelers = alive

        # --- Settling cracks (still state): propagate pixel by pixel ---
        if p < 0.1:
            self._next_crack_event -= dt
            if self._next_crack_event <= 0:
                self._start_settling_crack()
                self._next_crack_event = random.uniform(12, 25)

        # Advance propagating cracks
        new_propagating = []
        for prop in self._propagating:
            prop["timer"] -= dt
            while prop["timer"] <= 0 and prop["idx"] < len(prop["pixels"]):
                cx, cy, gen = prop["pixels"][prop["idx"]]
                self.cracks.append((cx, cy, gen))
                if (cx, cy) not in self.crack_set or gen < self.crack_set[(cx, cy)]:
                    self.crack_set[(cx, cy)] = gen
                # Flash at the propagating tip
                self._stress_waves[(cx, cy)] = 1.0
                prop["idx"] += 1
                prop["timer"] += prop["interval"]
            if prop["idx"] < len(prop["pixels"]):
                new_propagating.append(prop)
            else:
                # Crack finished propagating — trigger stress wave through network
                self._trigger_stress_wave(prop["pixels"])
                # Rebuild spatial data
                self._rebuild_crack_glow()
                self._rebuild_crack_dist()
                self._rebuild_crack_adj()
        self._propagating = new_propagating

        # Decay stress waves
        expired = []
        for key in self._stress_waves:
            self._stress_waves[key] -= dt * 2.0
            if self._stress_waves[key] <= 0:
                expired.append(key)
        for key in expired:
            del self._stress_waves[key]

        # --- Pressure front (slow diagonal sweep) ---
        self._next_pressure -= dt
        if self._next_pressure <= 0 and self._pressure_front is None:
            angle = random.uniform(0, 2 * math.pi)
            self._pressure_front = {
                "pos": -10.0,
                "nx": math.cos(angle),
                "ny": math.sin(angle),
                "speed": random.uniform(1.5, 3.0),
            }
            self._next_pressure = random.uniform(25, 45)
        if self._pressure_front is not None:
            self._pressure_front["pos"] += dt * self._pressure_front["speed"]
            if self._pressure_front["pos"] > GRID_SIZE + 20:
                self._pressure_front = None

        # --- Rare deep glints ---
        self._next_glint -= dt
        if self._next_glint <= 0 and self._glint is None:
            # Pick a non-crack pixel
            for _ in range(20):
                gx = random.randint(2, GRID_SIZE - 3)
                gy = random.randint(2, GRID_SIZE - 3)
                if (gx, gy) not in self.crack_set:
                    self._glint = {"x": gx, "y": gy, "timer": 0.12}
                    break
            self._next_glint = random.uniform(8, 18)
        if self._glint is not None:
            self._glint["timer"] -= dt
            if self._glint["timer"] <= 0:
                self._glint = None

    def _spawn_pulse_traveler(self):
        if not self.cracks:
            return
        start_idx = random.randint(0, len(self.cracks) - 1)
        sx, sy, _ = self.cracks[start_idx]
        path = [(sx, sy)]
        visited = {(sx, sy)}
        cx, cy = sx, sy
        for _ in range(40):
            neighbors = self._crack_adj.get((cx, cy), [])
            unvisited = [(nx, ny) for nx, ny in neighbors if (nx, ny) not in visited]
            if not unvisited:
                break
            cx, cy = random.choice(unvisited)
            visited.add((cx, cy))
            path.append((cx, cy))
        if len(path) > 3:
            self.pulse_travelers.append({
                "path": path,
                "pos": 0.0,
                "speed": random.uniform(3, 6),  # slower, more visible
            })

    def _start_settling_crack(self):
        """Begin a new crack that will propagate pixel by pixel."""
        sx = random.randint(8, GRID_SIZE - 9)
        sy = random.randint(8, GRID_SIZE - 9)
        angle = random.uniform(0, 2 * math.pi)
        pixels = []
        _grow_crack(pixels, sx, sy, angle,
                    length=random.randint(4, 10), generation=1,
                    max_gen=2, grid=GRID_SIZE)
        if pixels:
            interval = random.uniform(0.06, 0.12)  # time per pixel
            self._propagating.append({
                "pixels": pixels,
                "idx": 0,
                "timer": 0.0,
                "interval": interval,
            })

    def _trigger_stress_wave(self, new_crack_pixels):
        """BFS stress wave through existing crack network from new crack."""
        if not new_crack_pixels:
            return
        q = deque()
        visited = set()
        for cx, cy, _ in new_crack_pixels:
            for nx, ny in self._crack_adj.get((cx, cy), []):
                if (nx, ny) not in visited:
                    q.append((nx, ny, 0))
                    visited.add((nx, ny))
        while q:
            x, y, dist = q.popleft()
            if dist > 30:
                continue
            brightness = max(0.0, 1.0 - dist / 30.0) * 0.4
            self._stress_waves[(x, y)] = max(
                self._stress_waves.get((x, y), 0), brightness)
            for nx, ny in self._crack_adj.get((x, y), []):
                if (nx, ny) not in visited:
                    visited.add((nx, ny))
                    q.append((nx, ny, dist + 1))

    # -------------------------------------------------------------------
    # Draw
    # -------------------------------------------------------------------

    def draw(self):
        p_global = self.presence_amount
        vx = self.view_x
        vy = self.view_y
        t = self.time

        # Pre-compute pulse traveler brightness buffer
        pulse_buf = {}
        for trav in self.pulse_travelers:
            pos_i = int(trav["pos"])
            for offset in range(-3, 4):
                idx = pos_i + offset
                if 0 <= idx < len(trav["path"]):
                    px, py = trav["path"][idx]
                    dist = abs(offset) / 4.0
                    brightness = max(0, 1.0 - dist)
                    pulse_buf[(px, py)] = max(
                        pulse_buf.get((px, py), 0), brightness)

        # Pre-compute deep shape positions for pressure shadow
        deep_info = []
        for shape in self.deep_shapes:
            surge = shape.get("surge_amount", 0.0)
            glow = shape.get("base_glow", 1.0) + surge * 0.5
            deep_info.append((shape["cx"], shape["cy"], shape["radius"], glow, surge))

        # Presence glow radius: widens from 1px to 3px during presence
        glow_extra_radius = int(p_global * 2.0)  # 0, 1, or 2 extra pixels

        # Pressure front value function
        pf = self._pressure_front
        pf_nx = pf["nx"] if pf else 0
        pf_ny = pf["ny"] if pf else 0
        pf_pos = pf["pos"] if pf else -999

        # Glint info
        glint = self._glint

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                # View offset only shifts the "light angle" on the surface,
                # not object positions — everything stays fixed in the ice
                lx = x + vx
                ly = y + vy

                # --- Spatial presence: spreads from cracks ---
                crack_d = self.crack_dist[y][x]
                arrival_delay = min(crack_d / 25.0, 0.6)
                p = max(0.0, min(1.0,
                    (p_global - arrival_delay) / max(0.01, 1.0 - arrival_delay)))

                # --- Layer 1: Ice surface ---
                noise_val = self._ice_texture[y][x]
                # Light angle subtly shifts ice brightness based on view
                light_shift = (lx - x) * 0.08 + (ly - y) * 0.08
                ice_r = _lerp(self.ICE_BASE[0], self.ICE_PRESENT[0], p)
                ice_g = _lerp(self.ICE_BASE[1], self.ICE_PRESENT[1], p)
                ice_b = _lerp(self.ICE_BASE[2], self.ICE_PRESENT[2], p)
                r = ice_r + noise_val * self.ICE_RANGE + light_shift
                g = ice_g + noise_val * self.ICE_RANGE + light_shift
                b = ice_b + noise_val * self.ICE_RANGE + light_shift * 1.5

                # --- Pressure front (subtle diagonal sweep) ---
                if pf is not None:
                    dot = x * pf_nx + y * pf_ny
                    dist_to_front = abs(dot - pf_pos)
                    if dist_to_front < 8:
                        front_val = (1.0 - dist_to_front / 8.0) * 1.5
                        r += front_val
                        g += front_val * 1.2
                        b += front_val * 2.0

                # --- Memory field (ghost of where shapes passed) ---
                mem = self._memory[y][x]
                if mem > 0.01:
                    r += mem * 1.5
                    g += mem * 2.5
                    b += mem * 5.0

                # --- Layer 2: Deep shapes (pressure shadows on surface) ---
                for dcx, dcy, drad, dglow, dsurge in deep_info:
                    blob_val = _soft_blob(x, y, dcx, dcy, drad)
                    if blob_val > 0.01:
                        # Depth color — brighter during presence or surge
                        effective_p = min(1.0, p + dsurge * 0.6)
                        dr = _lerp(self.DEPTH_STILL[0], self.DEPTH_PRESENT[0], effective_p)
                        dg = _lerp(self.DEPTH_STILL[1], self.DEPTH_PRESENT[1], effective_p)
                        db = _lerp(self.DEPTH_STILL[2], self.DEPTH_PRESENT[2], effective_p)
                        r += blob_val * dr * dglow
                        g += blob_val * dg * dglow
                        b += blob_val * db * dglow

                        # Pressure shadow: surface brightens above deep shapes
                        if dsurge > 0.1:
                            shadow_str = blob_val * dsurge * 4.0
                            r += shadow_str
                            g += shadow_str * 1.5
                            b += shadow_str * 3.0

                # --- Layer 3: Trapped objects ---
                for obj in self.trapped:
                    ox, oy = obj["x"], obj["y"]
                    dist = abs(x - ox) + abs(y - oy)
                    if dist < obj["size"] + 0.5:
                        depth_fade = 1.0 - obj["depth"] * (1.0 - p * 0.6)
                        # Brightness varies with proximity to deep shapes
                        backlit = 0.0
                        for dcx, dcy, drad, dglow, _ in deep_info:
                            bl = _soft_blob(ox, oy, dcx, dcy, drad + 3)
                            backlit = max(backlit, bl)
                        brightness = depth_fade * (0.3 + 0.4 * backlit)
                        brightness *= (1.0 + p * 3.0)

                        if obj["hue"] == "bubble":
                            r += brightness * 5
                            g += brightness * 9
                            b += brightness * 16
                        elif obj["hue"] == "leaf":
                            r += brightness * 7
                            g += brightness * 9
                            b += brightness * 4
                        else:
                            r += brightness * 6
                            g += brightness * 5
                            b += brightness * 3

                # --- Layer 4: Crack glow halo ---
                # Base 1px glow (pre-computed)
                glow_val = self.crack_glow.get((x, y), 0)
                # During presence: wider glow from crack distance
                if glow_extra_radius > 0 and glow_val == 0 and crack_d <= glow_extra_radius + 1:
                    glow_val = max(0, 1.0 - crack_d / (glow_extra_radius + 1.5)) * 0.5

                if glow_val > 0:
                    gr = _lerp(self.CRACK_GLOW_STILL[0],
                               self.CRACK_GLOW_PRESENT[0], p)
                    gg = _lerp(self.CRACK_GLOW_STILL[1],
                               self.CRACK_GLOW_PRESENT[1], p)
                    gb = _lerp(self.CRACK_GLOW_STILL[2],
                               self.CRACK_GLOW_PRESENT[2], p)
                    r += glow_val * gr
                    g += glow_val * gg
                    b += glow_val * gb

                # --- Layer 5: Crack lines (ADDITIVE, not replacement) ---
                if (x, y) in self.crack_set:
                    gen = self.crack_set[(x, y)]
                    gen_fade = max(0.3, 1.0 - gen * 0.22)

                    cr = _lerp(self.CRACK_STILL[0], self.CRACK_PRESENT[0], p)
                    cg = _lerp(self.CRACK_STILL[1], self.CRACK_PRESENT[1], p)
                    cb = _lerp(self.CRACK_STILL[2], self.CRACK_PRESENT[2], p)

                    # Depth-crack coupling: cracks brighten where depth is near
                    for dcx, dcy, drad, dglow, _ in deep_info:
                        depth_near = _soft_blob(x, y, dcx, dcy, drad + 2)
                        if depth_near > 0.05:
                            coupling = depth_near * 8.0
                            cr += coupling
                            cg += coupling * 1.5
                            cb += coupling * 3.0

                    # Pulse travelers
                    pulse_val = pulse_buf.get((x, y), 0)
                    if pulse_val > 0:
                        cr += pulse_val * 60 * p_global
                        cg += pulse_val * 80 * p_global
                        cb += pulse_val * 120 * p_global

                    # Stress wave (settling resonance)
                    stress = self._stress_waves.get((x, y), 0)
                    if stress > 0:
                        cr += stress * 35
                        cg += stress * 45
                        cb += stress * 60

                    r += cr * gen_fade
                    g += cg * gen_fade
                    b += cb * gen_fade

                # --- Rare deep glint ---
                if glint is not None and x == glint["x"] and y == glint["y"]:
                    gt = glint["timer"] / 0.12
                    flash = math.sin(gt * math.pi)  # bell curve
                    r += flash * 13
                    g += flash * 21
                    b += flash * 36

                # Clamp and set
                self.display.set_pixel(x, y, (
                    max(0, min(255, int(r))),
                    max(0, min(255, int(g))),
                    max(0, min(255, int(b))),
                ))
