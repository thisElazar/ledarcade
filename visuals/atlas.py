"""Atlas — interactive world atlas viewer for the 64×64 LED arcade cabinet.

Renders terrain, satellite imagery, night lights, political maps,
elevation, and historical empire overlays from pre-baked .npz atlas files.

Controls:
    Joystick          Pan the map
    Action L          Cycle visual mode
    Action R + ↑/↓    Zoom in / out
    Action R + ←/→    Step through historical eras (history mode)
"""

import os
import numpy as np
from . import Visual, Display, GRID_SIZE

# ── Atlas data search paths ──────────────────────────────────────────
_ATLAS_DIRS = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'data', 'atlas'),
    '/Users/fields/Documents/flightSim',
]

MODES = ['terrain', 'satellite', 'night', 'elevation', 'political', 'history']

# ── WorldCover colour LUTs ──────────────────────────────────────────
_WC_DAY = {
    0: (15, 40, 120), 10: (25, 65, 30), 20: (75, 90, 45),
    30: (110, 130, 60), 40: (150, 155, 60), 50: (140, 130, 125),
    60: (170, 155, 120), 70: (230, 235, 245), 80: (20, 50, 120),
    90: (40, 95, 70), 95: (30, 80, 55), 100: (90, 100, 75),
}
_WC_NIGHT = {
    0: (2, 4, 10), 10: (3, 7, 4), 20: (5, 7, 4), 30: (6, 8, 5),
    40: (7, 8, 5), 50: (10, 10, 10), 60: (8, 7, 6), 70: (15, 16, 18),
    80: (2, 5, 12), 90: (4, 8, 6), 95: (3, 7, 5), 100: (6, 7, 5),
}

_WC_LUT_DAY = np.zeros((256, 3), dtype=np.uint8)
_WC_LUT_NIGHT = np.zeros((256, 3), dtype=np.uint8)
for _k, _v in _WC_DAY.items():
    _WC_LUT_DAY[_k] = _v
for _k, _v in _WC_NIGHT.items():
    _WC_LUT_NIGHT[_k] = _v

_POLITICAL = {
    0: (15, 40, 120), 1: (180, 90, 85), 2: (90, 160, 110),
    3: (100, 130, 190), 4: (200, 175, 90), 5: (160, 110, 170),
    6: (110, 180, 175), 7: (190, 140, 100),
}

_ELEV_STOPS = [
    (-5000, (10, 30, 80)), (-2000, (20, 50, 120)), (-200, (30, 70, 140)),
    (0, (40, 90, 150)), (1, (40, 100, 50)), (200, (60, 120, 55)),
    (500, (90, 130, 60)), (1000, (130, 130, 70)), (2000, (170, 155, 110)),
    (3000, (200, 190, 170)), (4500, (230, 230, 235)), (7000, (255, 255, 255)),
]
_ELEV_LUT = np.zeros((12001, 3), dtype=np.uint8)
for _i in range(len(_ELEV_STOPS) - 1):
    _e0, _c0 = _ELEV_STOPS[_i]
    _e1, _c1 = _ELEV_STOPS[_i + 1]
    for _e in range(max(0, _e0 + 5000), min(12001, _e1 + 5000 + 1)):
        _t = (_e - (_e0 + 5000)) / max((_e1 - _e0), 1)
        _ELEV_LUT[_e] = [int(_c0[j] + (_c1[j] - _c0[j]) * _t) for j in range(3)]

_HIST_COLORS = np.array([
    [15, 40, 120], [180, 70, 65], [80, 155, 100], [95, 120, 185],
    [195, 170, 75], [155, 100, 165], [100, 175, 170], [185, 135, 90],
    [130, 85, 70], [75, 140, 70], [170, 120, 160], [120, 160, 95],
    [190, 150, 130], [100, 100, 170], [170, 170, 85], [140, 90, 130],
], dtype=np.uint8)


# ── Grid sampling ────────────────────────────────────────────────────

def _sample(grid, bounds, clat, clon, vdeg, size=GRID_SIZE, mode='nearest'):
    """Sample a pre-rasterised grid at a given centre/zoom."""
    min_lat, max_lat, min_lon, max_lon = bounds
    gh, gw = grid.shape[:2]
    res = (max_lat - min_lat) / gh
    cell_per_px = vdeg / size / res
    half = vdeg / 2

    if mode == 'nearest' or cell_per_px < 1.5:
        py = np.arange(size)
        px = np.arange(size)
        lats = clat + half - ((py + 0.5) / size) * vdeg
        lons = clon - half + ((px + 0.5) / size) * vdeg
        lon_range = max_lon - min_lon
        if lon_range >= 359:
            lons = ((lons - min_lon) % lon_range) + min_lon
        rows = np.clip(((max_lat - lats) / res).astype(np.int32), 0, gh - 1)
        cols = np.clip(((lons - min_lon) / res).astype(np.int32), 0, gw - 1)
        rr, cc = np.meshgrid(rows, cols, indexing='ij')
        return grid[rr, cc].copy()

    kernel = max(1, int(cell_per_px))
    out_shape = (size, size, 3) if len(grid.shape) == 3 else (size, size)
    out = np.zeros(out_shape, dtype=grid.dtype)
    lon_range = max_lon - min_lon

    for py in range(size):
        lat = clat + half - ((py + 0.5) / size) * vdeg
        r0 = max(0, int((max_lat - lat) / res - kernel / 2))
        r1 = min(gh, r0 + kernel)
        if r0 >= r1:
            continue
        for ppx in range(size):
            lon = clon - half + ((ppx + 0.5) / size) * vdeg
            if lon_range >= 359:
                lon = ((lon - min_lon) % lon_range) + min_lon
            c0 = max(0, int((lon - min_lon) / res - kernel / 2))
            c1 = min(gw, c0 + kernel)
            if c0 >= c1:
                continue
            block = grid[r0:r1, c0:c1]
            if mode == 'average':
                out[py, ppx] = block.mean(axis=(0, 1)).astype(grid.dtype)
            elif mode == 'majority':
                vals, counts = np.unique(block, return_counts=True)
                out[py, ppx] = vals[counts.argmax()]
    return out


def _hillshade(atlas, bounds, clat, clon, vdeg):
    elev = _sample(atlas['elevation'], bounds, clat, clon, vdeg,
                   mode='average').astype(np.float32)
    dx = np.zeros_like(elev)
    dy = np.zeros_like(elev)
    dx[:, 1:-1] = elev[:, 2:] - elev[:, :-2]
    dy[1:-1, :] = elev[2:, :] - elev[:-2, :]
    shade = 1.0 + dx * -0.002 + dy * -0.003
    return np.clip(shade, 0.5, 1.4), elev


def _apply_water(fb, atlas, bounds, clat, clon, vdeg, wcolor):
    if 'water' not in atlas:
        return
    w = _sample(atlas['water'], bounds, clat, clon, vdeg,
                mode='average').astype(np.float32)
    mask = w > 50
    if vdeg < 2 and 'water_detail' in atlas:
        d = _sample(atlas['water_detail'], bounds, clat, clon, vdeg,
                    mode='average').astype(np.float32)
        mask = mask | (d > 15)
    if mask.any():
        fb[mask] = wcolor


# ── Frame rendering ──────────────────────────────────────────────────

def _render(atlas, clat, clon, vdeg, mode, era_idx=0):
    """Produce a 64×64×3 uint8 framebuffer."""
    bounds = tuple(atlas['bounds'])
    shade, elev = _hillshade(atlas, bounds, clat, clon, vdeg)
    S = GRID_SIZE

    if mode == 'terrain':
        wc = _sample(atlas['worldcover'], bounds, clat, clon, vdeg,
                     mode='majority')
        fb = _WC_LUT_DAY[wc].copy()
        fb = np.clip(fb.astype(np.float32) * shade[..., None],
                     0, 255).astype(np.uint8)
        _apply_water(fb, atlas, bounds, clat, clon, vdeg,
                     np.array([20, 50, 120], np.uint8))

    elif mode == 'political':
        if '_countries_global' in atlas:
            countries = _sample(atlas['_countries_global'],
                                tuple(atlas['_countries_bounds']),
                                clat, clon, vdeg, mode='majority')
        elif 'countries' in atlas:
            countries = _sample(atlas['countries'], bounds, clat, clon, vdeg,
                                mode='majority')
        else:
            countries = np.zeros((S, S), dtype=np.uint8)
        fb = np.zeros((S, S, 3), dtype=np.uint8)
        for val, color in _POLITICAL.items():
            fb[countries == val] = color
        fb = np.clip(fb.astype(np.float32) * shade[..., None],
                     0, 255).astype(np.uint8)

    elif mode == 'satellite':
        if 'blue_marble' in atlas:
            fb = _sample(atlas['blue_marble'], bounds, clat, clon, vdeg,
                         mode='average').astype(np.uint8)
        else:
            fb = np.zeros((S, S, 3), dtype=np.uint8)

    elif mode == 'night':
        wc = _sample(atlas['worldcover'], bounds, clat, clon, vdeg,
                     mode='majority')
        fb = _WC_LUT_NIGHT[wc].copy()
        fb = np.clip(fb.astype(np.float32) * shade[..., None],
                     0, 255).astype(np.uint8)
        _apply_water(fb, atlas, bounds, clat, clon, vdeg,
                     np.array([5, 15, 40], np.uint8))
        if 'nightlights' in atlas:
            lights = _sample(atlas['nightlights'], bounds, clat, clon, vdeg,
                             mode='average').astype(np.float32)
            mask = lights > 20
            if mask.any():
                b = np.clip((lights - 20) / 180.0, 0, 1)
                lc = np.array([255, 200, 90], dtype=np.float32)
                for c in range(3):
                    fb[:, :, c] = np.where(
                        mask,
                        np.clip(fb[:, :, c].astype(np.float32) * (1 - b)
                                + lc[c] * b, 0, 255),
                        fb[:, :, c]).astype(np.uint8)

    elif mode == 'elevation':
        if 'bathymetry' in atlas:
            bathy = _sample(atlas['bathymetry'], bounds, clat, clon, vdeg,
                            mode='average').astype(np.int32)
        else:
            bathy = elev.astype(np.int32)
        idx = np.clip(bathy + 5000, 0, 12000).astype(np.int32)
        fb = _ELEV_LUT[idx].copy()
        fb = np.clip(fb.astype(np.float32) * shade[..., None],
                     0, 255).astype(np.uint8)

    elif mode == 'history':
        if '_history_grids' in atlas and '_history_years' in atlas:
            years = atlas['_history_years']
            grids = atlas['_history_grids']
            ei = max(0, min(len(years) - 1, era_idx))
            hb = tuple(atlas['_history_bounds'])
            hist = _sample(grids[ei], hb, clat, clon, vdeg, mode='majority')
            fb = _HIST_COLORS[np.clip(hist, 0, 15)].copy()
            fb = np.clip(fb.astype(np.float32) * shade[..., None],
                         0, 255).astype(np.uint8)
        else:
            fb = np.zeros((S, S, 3), dtype=np.uint8)

    else:
        fb = np.zeros((S, S, 3), dtype=np.uint8)

    # Roads overlay (subtle, when zoomed in)
    if vdeg < 5 and 'roads' in atlas:
        is_night = mode == 'night'
        rc = np.array([90, 80, 65] if not is_night else [18, 16, 12],
                      dtype=np.uint8)
        roads = _sample(atlas['roads'], bounds, clat, clon, vdeg)
        if (roads > 0).any():
            fb[roads > 0] = rc
        if 'rails' in atlas:
            rlc = np.array([110, 55, 45] if not is_night else [22, 12, 10],
                           dtype=np.uint8)
            rails = _sample(atlas['rails'], bounds, clat, clon, vdeg)
            if (rails > 0).any():
                fb[rails > 0] = rlc

    return fb


# ── File discovery ───────────────────────────────────────────────────

def _find_atlas():
    """Return (atlas_path, directory) or (None, None)."""
    for d in _ATLAS_DIRS:
        if not os.path.isdir(d):
            continue
        # Prefer world atlas
        p = os.path.join(d, 'world_atlas.npz')
        if os.path.exists(p):
            return p, d
        # Then mideast (sample atlas)
        p = os.path.join(d, 'atlas_mideast.npz')
        if os.path.exists(p):
            return p, d
        # Then norcal
        p = os.path.join(d, 'atlas_norcal.npz')
        if os.path.exists(p):
            return p, d
        # Then any atlas_*.npz
        for f in sorted(os.listdir(d)):
            if f.startswith('atlas_') and f.endswith('.npz'):
                return os.path.join(d, f), d
    return None, None


# ── Visual class ─────────────────────────────────────────────────────

class Atlas(Visual):
    name = "ATLAS"
    description = "World atlas viewer"
    category = "science_macro"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self._atlas = None
        self._fb = None
        self._needs_render = True

        # View state
        self._center_lat = 0.0
        self._center_lon = 0.0
        self._view_deg = 5.0
        self._mode_idx = 0
        self._era_idx = 0
        self._history_years = None
        self._max_zoom_out = 20.0

        # Input state (stored for update)
        self._pan_dx = 0
        self._pan_dy = 0
        self._zoom_dir = 0

        # Overlay
        self._overlay_timer = 0.0
        self._overlay_text = ""

        self._load()

    def _load(self):
        self._draw_loading(0.0, "SEARCHING")
        self.display.render()

        path, directory = _find_atlas()
        if path is None:
            return

        self._draw_loading(0.2, os.path.basename(path))
        self.display.render()

        d = np.load(path, allow_pickle=True)
        atlas = {}
        for key in d.files:
            atlas[key] = d[key]

        self._draw_loading(0.5, "OVERLAYS")
        self.display.render()

        # Load supplementary data from same directory
        cp = os.path.join(directory, 'countries_global.npz')
        if os.path.exists(cp):
            cd = np.load(cp)
            atlas['_countries_global'] = cd['grid']
            atlas['_countries_bounds'] = cd['bounds']

        hp = os.path.join(directory, 'history_global.npz')
        if os.path.exists(hp):
            hd = np.load(hp)
            years = hd['years']
            grids = hd['grids']
            order = np.argsort(years)
            atlas['_history_grids'] = grids[order]
            atlas['_history_years'] = years[order]
            atlas['_history_bounds'] = hd['bounds']
            self._history_years = atlas['_history_years']

        self._draw_loading(1.0, "READY")
        self.display.render()

        self._atlas = atlas

        # Set initial view to atlas centre
        bounds = tuple(atlas['bounds'])
        self._center_lat = (bounds[0] + bounds[1]) / 2
        self._center_lon = (bounds[2] + bounds[3]) / 2
        lat_range = bounds[1] - bounds[0]
        lon_range = bounds[3] - bounds[2]
        self._max_zoom_out = max(lat_range, lon_range)
        # Start at a comfortable zoom
        self._view_deg = min(self._max_zoom_out, 5.0)

        self._overlay_text = MODES[self._mode_idx].upper()
        self._overlay_timer = 2.0

    def handle_input(self, inp):
        if self._atlas is None:
            return False

        zoom_held = inp.action_r_held

        # Mode cycle
        if inp.action_l or inp.action_r:
            self._mode_idx = (self._mode_idx + 1) % len(MODES)
            self._needs_render = True
            mode = MODES[self._mode_idx]
            if mode == 'history' and self._history_years is not None:
                year = int(self._history_years[self._era_idx])
                ystr = f"{abs(year)} BC" if year < 0 else f"{year} AD"
                self._overlay_text = f"HISTORY {ystr}"
            else:
                self._overlay_text = mode.upper()
            self._overlay_timer = 2.0
            return True

        # Zoom (action_r held + up/down)
        if zoom_held:
            self._zoom_dir = -inp.dy  # up = zoom in (positive)
            self._pan_dy = 0
            # Era stepping in history mode (action_r held + left/right)
            if MODES[self._mode_idx] == 'history' and self._history_years is not None:
                self._pan_dx = 0
                if inp.left_pressed:
                    self._era_step(-1)
                if inp.right_pressed:
                    self._era_step(1)
            else:
                self._pan_dx = inp.dx
        else:
            self._pan_dx = inp.dx
            self._pan_dy = inp.dy
            self._zoom_dir = 0

        return bool(inp.any_direction or zoom_held)

    def _era_step(self, delta):
        n = len(self._history_years)
        self._era_idx = max(0, min(n - 1, self._era_idx + delta))
        year = int(self._history_years[self._era_idx])
        ystr = f"{abs(year)} BC" if year < 0 else f"{year} AD"
        self._overlay_text = ystr
        self._overlay_timer = 2.0
        self._needs_render = True

    def update(self, dt):
        super().update(dt)

        # Pan
        if self._pan_dx or self._pan_dy:
            speed = self._view_deg * 0.4 * dt
            self._center_lon += self._pan_dx * speed
            self._center_lat -= self._pan_dy * speed
            # Wrap longitude
            if self._center_lon > 180:
                self._center_lon -= 360
            elif self._center_lon < -180:
                self._center_lon += 360
            self._needs_render = True

        # Zoom
        if self._zoom_dir:
            if self._zoom_dir > 0:
                self._view_deg = max(0.5, self._view_deg * (1 - 0.8 * dt))
            else:
                self._view_deg = min(self._max_zoom_out,
                                     self._view_deg * (1 + 0.8 * dt))
            self._needs_render = True

        # Overlay fade
        if self._overlay_timer > 0:
            self._overlay_timer = max(0.0, self._overlay_timer - dt)

    def draw(self):
        if self._atlas is None:
            self.display.clear()
            self.display.draw_text_small(2, 24, "ATLAS", (200, 160, 40))
            self.display.draw_text_small(2, 32, "NO DATA", (200, 50, 50))
            self.display.draw_text_small(2, 40, "FOUND", (200, 50, 50))
            return

        # Re-render the map only when the view changed
        if self._needs_render:
            self._fb = _render(self._atlas, self._center_lat,
                               self._center_lon, self._view_deg,
                               MODES[self._mode_idx], self._era_idx)
            self._needs_render = False

        # Blit numpy framebuffer → display buffer
        fb = self._fb
        buf = self.display.buffer
        for y in range(GRID_SIZE):
            row = buf[y]
            for x in range(GRID_SIZE):
                px = fb[y, x]
                row[x] = (int(px[0]), int(px[1]), int(px[2]))

        # Year label (history mode)
        if MODES[self._mode_idx] == 'history' and self._history_years is not None:
            year = int(self._history_years[self._era_idx])
            ystr = f"{abs(year)} BC" if year < 0 else f"{year} AD"
            self.display.draw_rect(0, GRID_SIZE - 7, GRID_SIZE, 7, (0, 0, 0))
            tw = len(ystr) * 4
            self.display.draw_text_small(max(1, 32 - tw // 2),
                                         GRID_SIZE - 6, ystr,
                                         (200, 200, 200))

        # Mode overlay (fades out)
        if self._overlay_timer > 0:
            alpha = min(1.0, self._overlay_timer / 0.5)
            c = int(200 * alpha)
            self.display.draw_text_small(2, 2, self._overlay_text, (c, c, c))
