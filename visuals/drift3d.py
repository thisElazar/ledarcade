"""
Drift 3D — Voxel Space Terrain Flyover
=======================================
Comanche-style voxel space renderer showing the Drift terrain simulation
as a 3D landscape with flowing water. Camera orbits the island while
springs feed water into valleys.
"""

import random
import math
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.drift_sim import (DriftSim, SPRING_FLOW_RATE, MAX_HEIGHT,
                             MIN_HEIGHT, _terrain_color, _water_color,
                             MIN_DEPTH)

W = 64   # screen width = grid width
H = 64   # screen height = grid height
GW = 64  # terrain grid width
GH = 64  # terrain grid height

TERRAIN_PRESETS = ['mountains', 'default', 'hills', 'plains']
PRESET_LABELS = ['MOUNTAINS', 'DEFAULT', 'HILLS', 'PLAINS']

# Camera — raised up, tilted down (lower horizon row)
CAM_RADIUS = 38.0
ORBIT_SPEED = 0.15  # rad/s, ~42s per orbit

# Camera view presets: (height, horizon_row, label)
VIEW_PRESETS = [
    (140.0, 12, 'HIGH'),
    (100.0, 16, 'MID'),
    (60.0,  20, 'LOW'),
]

# Time speed presets: (sim_speed_mult, orbit_speed_mult, label)
SPEED_PRESETS = [
    (0.3, 0.5,  'SLOW'),
    (0.6, 1.0,  'NORMAL'),
    (1.2, 2.0,  'FAST'),
    (2.5, 3.0,  '2X'),
]

# Rendering
FOV = math.pi / 3   # 60 degrees
DRAW_DIST = 130.0
MAX_STEPS = 200
SCALE_H = 220.0
STEP_NEAR = 0.4
STEP_FAR = 1.4
FOG_START = 40.0
FOG_END = 110.0
FOG_COLOR = (4, 6, 15)

# Water tuning for 3D visual
SPRING_MULT_LO = 2.5     # spring flow multiplier range
SPRING_MULT_HI = 4.0
EVAP_RESTORE = 0.00004   # added back per-cell per sec to counter evaporation

# --- Pre-compute LUTs at module load ---

# Terrain color: 256 entries mapping height bucket -> (r, g, b)
_TERRAIN_LUT = []
for _i in range(256):
    _h = MIN_HEIGHT + (MAX_HEIGHT - MIN_HEIGHT) * _i / 255.0
    _TERRAIN_LUT.append(_terrain_color(_h))

# Water color: 64 entries mapping depth bucket -> (r, g, b)
_WATER_LUT = []
for _i in range(64):
    _d = _i * 0.5  # 0..31.5 depth range
    _WATER_LUT.append(_water_color(_d))

# Per-column ray offsets (angle offset from center + cos correction)
_COL_ANGLES = []
_COL_COS = []
for _c in range(W):
    _ang = (_c / W - 0.5) * FOV
    _COL_ANGLES.append(_ang)
    _COL_COS.append(math.cos(_ang))


def _make_sky_grad(horizon):
    """Build sky gradient for a given horizon row."""
    grad = []
    for i in range(H):
        if i <= horizon:
            t = i / max(1, horizon)
            r = int(2 + 6 * t)
            g = int(2 + 10 * t)
            b = int(8 + 22 * t)
        else:
            t = (i - horizon) / max(1, H - horizon - 1)
            r = int(8 + (FOG_COLOR[0] - 8) * t)
            g = int(12 + (FOG_COLOR[1] - 12) * t)
            b = int(30 + (FOG_COLOR[2] - 30) * t)
        grad.append((r, g, b))
    return grad


# Pre-build sky gradients for each view preset
_SKY_GRADS = [_make_sky_grad(vp[1]) for vp in VIEW_PRESETS]


def _fog_lerp(r, g, b, dist):
    """Apply distance fog toward FOG_COLOR."""
    if dist <= FOG_START:
        return r, g, b
    t = (dist - FOG_START) / (FOG_END - FOG_START)
    if t >= 1.0:
        return FOG_COLOR
    fr, fg, fb = FOG_COLOR
    return (int(r + (fr - r) * t),
            int(g + (fg - g) * t),
            int(b + (fb - b) * t))


def _find_slopes(sim, count=4):
    """Find spring positions on slopes — mid-height with steep gradient."""
    w, h = sim.width, sim.height
    terrain = sim.terrain
    margin = max(3, w // 12)
    min_dist = max(8, w // 8)

    # Find height range of this terrain
    max_h = max(terrain)
    min_h = min(terrain)
    rng = max_h - min_h
    if rng < 1.0:
        return []

    # Target height band: 35-65% of range (the slopes)
    lo_h = min_h + rng * 0.35
    hi_h = min_h + rng * 0.65

    candidates = []
    for y in range(margin, h - margin):
        row = y * w
        for x in range(margin, w - margin):
            ht = terrain[row + x]
            if not (lo_h <= ht <= hi_h):
                continue
            # Compute gradient magnitude (max height diff to 4-neighbors)
            grad = 0.0
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ni = (y + dy) * w + (x + dx)
                diff = abs(terrain[ni] - ht)
                if diff > grad:
                    grad = diff
            if grad > rng * 0.04:  # meaningful slope
                candidates.append((grad, x, y))

    candidates.sort(reverse=True)  # steepest first

    # Pick spaced-out positions
    picks = []
    for _, px, py in candidates:
        too_close = False
        for ex, ey in picks:
            if abs(px - ex) + abs(py - ey) < min_dist:
                too_close = True
                break
        if not too_close:
            picks.append((px, py))
            if len(picks) >= count:
                break
    return picks


class Drift3D:
    """3D voxel-space flyover of Drift terrain with flowing water."""

    name = "DRIFT 3D"
    description = "Terrain flyover"
    category = "nature"

    def __init__(self, display):
        self.display = display
        self.time = 0.0
        self.wants_exit = False
        self.reset()

    def reset(self):
        self.time = 0.0
        self.sim = DriftSim(GW, GH)
        self.preset_idx = 0
        self.view_idx = 0
        self.speed_idx = 1  # NORMAL
        self.cam_angle = 0.0
        self._new_terrain()
        self.overlay_text = ''
        self.overlay_timer = 0.0

    def _new_terrain(self):
        preset = TERRAIN_PRESETS[self.preset_idx % len(TERRAIN_PRESETS)]
        self.sim.generate_terrain(preset=preset,
                                  seed=random.randint(0, 999999))
        slopes = _find_slopes(self.sim, 5)
        count = random.randint(3, min(4, len(slopes)))
        for px, py in slopes[:count]:
            self.sim.add_spring(px, py,
                                flow_rate=SPRING_FLOW_RATE * random.uniform(
                                    SPRING_MULT_LO, SPRING_MULT_HI))

    def handle_input(self, input_state):
        consumed = False

        # Action buttons: cycle terrain preset
        if input_state.action_l or input_state.action_r:
            self.preset_idx = (self.preset_idx + 1) % len(TERRAIN_PRESETS)
            self._new_terrain()
            self.overlay_text = PRESET_LABELS[self.preset_idx % len(PRESET_LABELS)]
            self.overlay_timer = 2.0
            consumed = True

        # Left/right: time speed
        if input_state.left_pressed:
            self.speed_idx = max(0, self.speed_idx - 1)
            self.overlay_text = SPEED_PRESETS[self.speed_idx][2]
            self.overlay_timer = 2.0
            consumed = True
        if input_state.right_pressed:
            self.speed_idx = min(len(SPEED_PRESETS) - 1, self.speed_idx + 1)
            self.overlay_text = SPEED_PRESETS[self.speed_idx][2]
            self.overlay_timer = 2.0
            consumed = True

        # Up/down: camera view
        if input_state.up_pressed:
            self.view_idx = (self.view_idx - 1) % len(VIEW_PRESETS)
            self.overlay_text = VIEW_PRESETS[self.view_idx][2]
            self.overlay_timer = 2.0
            consumed = True
        if input_state.down_pressed:
            self.view_idx = (self.view_idx + 1) % len(VIEW_PRESETS)
            self.overlay_text = VIEW_PRESETS[self.view_idx][2]
            self.overlay_timer = 2.0
            consumed = True

        return consumed

    def update(self, dt):
        self.time += dt

        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

        # Speed-adjusted orbit and simulation
        sim_mult, orbit_mult, _ = SPEED_PRESETS[self.speed_idx]
        self.cam_angle += ORBIT_SPEED * orbit_mult * dt
        self.sim.simulate(dt * sim_mult)

        # Counteract evaporation so water accumulates and pools
        restore = EVAP_RESTORE * dt
        water = self.sim.water
        for i in range(len(water)):
            if water[i] > MIN_DEPTH:
                water[i] += restore

    def draw(self):
        display = self.display
        display.clear()

        # Current view settings
        cam_h, horizon, _ = VIEW_PRESETS[self.view_idx]
        sky_grad = _SKY_GRADS[self.view_idx]

        # Cache locals for speed
        terrain = self.sim.terrain
        water = self.sim.water
        gw = GW
        gh = GH
        cam_angle = self.cam_angle
        time = self.time
        set_pixel = display.set_pixel
        gw_1 = gw - 1
        gh_1 = gh - 1

        # Camera position (orbiting terrain center)
        cx = gw * 0.5 + CAM_RADIUS * math.cos(cam_angle)
        cy = gh * 0.5 + CAM_RADIUS * math.sin(cam_angle)

        # Direction camera is looking (toward center)
        look_angle = math.atan2(gh * 0.5 - cy, gw * 0.5 - cx)

        sin_table = []
        cos_table = []
        for c in range(W):
            a = look_angle + _COL_ANGLES[c]
            sin_table.append(math.sin(a))
            cos_table.append(math.cos(a))

        # Sky: fill entire screen as backdrop (terrain overwrites below)
        for row in range(H):
            sr, sg, sb = sky_grad[row]
            for c in range(W):
                set_pixel(c, row, (sr, sg, sb))

        # Projection constant
        proj_k = SCALE_H / H

        # Voxel space ray march with bilinear interpolation
        for c in range(W):
            ray_sin = sin_table[c]
            ray_cos = cos_table[c]
            cos_corr = _COL_COS[c]
            max_y = H  # lowest unfilled row (draw upward from bottom)

            dist = 1.0
            step = STEP_NEAR
            steps = 0

            while dist < DRAW_DIST and steps < MAX_STEPS:
                # Sample position on terrain grid
                gx = cx + ray_cos * dist
                gy = cy + ray_sin * dist

                # Bilinear interpolation coords
                ix = int(gx)
                iy = int(gy)

                if 0 <= ix < gw and 0 <= iy < gh:
                    fx = gx - ix
                    fy = gy - iy
                    ix1 = ix + 1 if ix < gw_1 else ix
                    iy1 = iy + 1 if iy < gh_1 else iy

                    # Bilinear sample terrain height
                    i00 = iy * gw + ix
                    i10 = iy * gw + ix1
                    i01 = iy1 * gw + ix
                    i11 = iy1 * gw + ix1
                    w00 = (1 - fx) * (1 - fy)
                    w10 = fx * (1 - fy)
                    w01 = (1 - fx) * fy
                    w11 = fx * fy
                    t_h = (terrain[i00] * w00 + terrain[i10] * w10 +
                           terrain[i01] * w01 + terrain[i11] * w11)

                    # Bilinear sample water depth
                    w_d = (water[i00] * w00 + water[i10] * w10 +
                           water[i01] * w01 + water[i11] * w11)

                    # Determine surface height and color
                    if w_d > MIN_DEPTH:
                        surface_h = t_h + w_d
                        # Water color from LUT
                        wi = int(w_d * 2.0)
                        if wi > 63:
                            wi = 63
                        cr, cg, cb = _WATER_LUT[wi]
                        # Gentle shimmer
                        shimmer = math.sin(gx * 3.0 + time * 2.5) * math.sin(gy * 2.5 + time * 2.0)
                        shimmer_i = int(shimmer * 12)
                        cr = max(0, min(255, cr + shimmer_i))
                        cg = max(0, min(255, cg + shimmer_i))
                        cb = max(0, min(255, cb + shimmer_i))
                    else:
                        surface_h = t_h
                        # Terrain color from LUT
                        ti = int((t_h - MIN_HEIGHT) / (MAX_HEIGHT - MIN_HEIGHT) * 255)
                        if ti < 0:
                            ti = 0
                        elif ti > 255:
                            ti = 255
                        cr, cg, cb = _TERRAIN_LUT[ti]

                    # Corrected distance for projection (remove fisheye)
                    corr_dist = dist * cos_corr
                    if corr_dist < 0.5:
                        corr_dist = 0.5

                    # Project to screen Y
                    screen_y = horizon + (cam_h - surface_h) / corr_dist * proj_k

                    draw_y = int(screen_y)
                    if draw_y < 0:
                        draw_y = 0

                    if draw_y < max_y:
                        # Apply fog
                        cr, cg, cb = _fog_lerp(cr, cg, cb, dist)

                        color = (cr, cg, cb)

                        # Draw vertical strip from draw_y to max_y
                        y = draw_y
                        while y < max_y:
                            if y >= 0:
                                set_pixel(c, y, color)
                            y += 1
                        max_y = draw_y

                    if max_y <= 0:
                        break

                # Variable step size: fine near, coarse far
                dist += step
                step += (STEP_FAR - STEP_NEAR) / MAX_STEPS
                steps += 1

        # Overlay text
        if self.overlay_timer > 0 and self.overlay_text:
            oa = min(1.0, self.overlay_timer / 0.5)
            oc = (int(255 * oa), int(255 * oa), int(255 * oa))
            display.draw_text_small(2, 2, self.overlay_text, oc)
