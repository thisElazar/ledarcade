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
import urllib.request
import numpy as np
from . import Visual, Display, GRID_SIZE

# ── Atlas data search paths ──────────────────────────────────────────
_PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ATLAS_DIRS = [
    os.path.join(_PROJECT, 'assets', 'atlas'),
    os.path.join(_PROJECT, 'data', 'atlas'),
    '/Users/fields/Documents/flightSim',
]

MODES = ['terrain', 'satellite', 'live', 'night', 'elevation']

# ── Auto-download from GitHub Releases ───────────────────────────────
# Module-level atlas cache — survives visual reset so data loads only once
_cached_atlas = None

_RELEASE_URL = 'https://github.com/thisElazar/ledarcade/releases/download/atlas-data'
_ATLAS_FILES = [
    ('world_atlas_pi.npz', True),    # (filename, required)
]

# Political mode removed — history mode handles it better

# ── WorldCover colour LUTs ──────────────────────────────────────────
_WC_DAY = {
    0: (15, 40, 120), 10: (25, 65, 30), 20: (75, 90, 45),
    30: (110, 130, 60), 40: (150, 155, 60), 50: (140, 130, 125),
    60: (170, 155, 120), 70: (180, 185, 195), 80: (20, 50, 120),
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

    if True:  # Always use fast numpy point-sampling (area avg too slow for Pi)
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
    # Satellite imagery handles water at all zoom levels — disabled
    return


def _sample_at(grid, bounds, lats, lons):
    """Sample a grid at arbitrary lat/lon arrays (any shape)."""
    min_lat, max_lat, min_lon, max_lon = bounds
    gh, gw = grid.shape[:2]
    res = (max_lat - min_lat) / gh
    lon_range = max_lon - min_lon
    if lon_range >= 359:
        lons = ((lons - min_lon) % lon_range) + min_lon
    rows = np.clip(((max_lat - lats) / res).astype(np.int32), 0, gh - 1)
    cols = np.clip(((lons - min_lon) / res).astype(np.int32), 0, gw - 1)
    return grid[rows, cols]


# Globe threshold — switch from flat map to globe above this view angle
GLOBE_THRESHOLD = 50.0


def _render_globe(atlas, rot_lat, rot_lon, mode):
    """Render atlas data on a 3D sphere."""
    S = GRID_SIZE
    bounds = tuple(atlas['bounds'])
    fb = np.zeros((S, S, 3), dtype=np.uint8)

    # Sphere geometry — fills most of the frame
    radius = 29.0
    cx, cy = S / 2, S / 2

    py = np.arange(S)
    px = np.arange(S)
    xx, yy = np.meshgrid((px - cx + 0.5) / radius, (cy - py - 0.5) / radius)

    # Ray-sphere intersection (orthographic projection)
    zz_sq = 1.0 - xx ** 2 - yy ** 2
    on_sphere = zz_sq > 0
    zz = np.sqrt(np.where(on_sphere, zz_sq, 0))

    # Rotate sphere: Y-axis (longitude), then X-axis (latitude tilt)
    rlat = np.radians(rot_lat)
    rlon = np.radians(rot_lon)
    cos_rlon, sin_rlon = np.cos(rlon), np.sin(rlon)
    cos_rlat, sin_rlat = np.cos(rlat), np.sin(rlat)

    # Y-axis rotation (longitude)
    x1 = xx * cos_rlon + zz * sin_rlon
    z1 = -xx * sin_rlon + zz * cos_rlon
    y1 = yy

    # X-axis rotation (latitude tilt)
    y2 = y1 * cos_rlat - z1 * sin_rlat
    z2 = y1 * sin_rlat + z1 * cos_rlat
    x2 = x1

    # Sphere normals → lat/lon
    lat = np.degrees(np.arcsin(np.clip(y2, -1, 1)))
    lon = np.degrees(np.arctan2(x2, z2))

    # Lambertian shading — mostly frontal with slight upper-right bias
    shade = np.clip(x2 * 0.15 + y2 * 0.25 + zz * 0.95, 0.15, 1.0)

    # Sample atlas at globe lat/lons
    if mode == 'terrain':
        wc = _sample_at(atlas['worldcover'], bounds, lat, lon)
        colors = _WC_LUT_DAY[wc].astype(np.float32)
        if 'blue_marble' in atlas:
            sat = _sample_at(atlas['blue_marble'], bounds, lat, lon).astype(
                np.float32)
            colors = colors * 0.4 + sat * 0.6
        globe = np.clip(colors * shade[..., None], 0, 255).astype(np.uint8)

    elif mode == 'satellite':
        sat = _sample_at(atlas['blue_marble'], bounds, lat, lon).astype(
            np.float32) if 'blue_marble' in atlas else np.full(
            lat.shape + (3,), 40, dtype=np.float32)
        sat = 255.0 * (sat / 255.0) ** 0.65  # gamma lift
        globe = np.clip(sat * shade[..., None], 0, 255).astype(np.uint8)

    elif mode == 'live':
        import datetime
        now = datetime.datetime.now(datetime.UTC)
        utc_hour = now.hour + now.minute / 60.0
        doy = now.timetuple().tm_yday

        sat = _sample_at(atlas['blue_marble'], bounds, lat, lon).astype(
            np.float32) if 'blue_marble' in atlas else np.full(
            lat.shape + (3,), 40, dtype=np.float32)
        night_img = sat * 0.06

        dec_r = np.radians(23.45 * np.sin(np.radians((284 + doy) / 365 * 360)))
        ha = np.radians((utc_hour - 12) * 15 + lon)
        sin_e = np.sin(np.radians(lat)) * np.sin(dec_r) + \
                np.cos(np.radians(lat)) * np.cos(dec_r) * np.cos(ha)
        sun_e = np.degrees(np.arcsin(np.clip(sin_e, -1, 1)))
        t = np.clip((sun_e + 6) / 12.0, 0, 1)[..., None]

        mixed = sat * t + night_img * (1 - t)
        if 'nightlights' in atlas:
            lights = _sample_at(atlas['nightlights'], bounds, lat, lon).astype(
                np.float32)
            dark = (t[..., 0] < 0.8) & (lights > 10)
            if dark.any():
                b = np.clip((lights - 10) / 120.0, 0, 1) * (1.0 - t[..., 0])
                lc = np.array([255, 200, 90], dtype=np.float32)
                for c in range(3):
                    mixed[:, :, c] = np.where(dark,
                        mixed[:, :, c] * (1 - b) + lc[c] * b,
                        mixed[:, :, c])
        globe = np.clip(mixed * shade[..., None], 0, 255).astype(np.uint8)

    elif mode == 'night':
        sat = _sample_at(atlas['blue_marble'], bounds, lat, lon).astype(
            np.float32) if 'blue_marble' in atlas else np.zeros(
            lat.shape + (3,), dtype=np.float32)
        mixed = sat * 0.08
        if 'nightlights' in atlas:
            lights = _sample_at(atlas['nightlights'], bounds, lat, lon).astype(
                np.float32)
            mask = lights > 10
            if mask.any():
                b = np.clip((lights - 10) / 120.0, 0, 1)
                lc = np.array([255, 200, 90], dtype=np.float32)
                for c in range(3):
                    mixed[:, :, c] = np.where(mask,
                        mixed[:, :, c] * (1 - b) + lc[c] * b,
                        mixed[:, :, c])
        globe = np.clip(mixed * shade[..., None], 0, 255).astype(np.uint8)

    elif mode == 'elevation':
        elev = _sample_at(atlas.get('bathymetry', atlas['elevation']),
                          bounds, lat, lon).astype(np.int32)
        idx = np.clip(elev + 5000, 0, 12000).astype(np.int32)
        colors = _ELEV_LUT[idx].astype(np.float32)
        globe = np.clip(colors * shade[..., None], 0, 255).astype(np.uint8)

    else:
        globe = np.zeros((S, S, 3), dtype=np.uint8)

    # Composite: globe pixels on sphere, black background
    fb[on_sphere] = globe[on_sphere]

    # Subtle atmosphere rim glow
    edge = on_sphere & (zz_sq < 0.08)
    if edge.any():
        glow = np.array([30, 60, 120], dtype=np.uint8)
        fb[edge] = np.clip(fb[edge].astype(np.int16) + glow, 0, 255).astype(
            np.uint8)

    return fb


# ── Frame rendering ──────────────────────────────────────────────────

def _render(atlas, clat, clon, vdeg, mode, era_idx=0):
    """Produce a 64×64×3 uint8 framebuffer."""
    bounds = tuple(atlas['bounds'])
    shade, elev = _hillshade(atlas, bounds, clat, clon, vdeg)
    S = GRID_SIZE

    if mode == 'terrain':
        wc = _sample(atlas['worldcover'], bounds, clat, clon, vdeg,
                     mode='majority')
        wc_colors = _WC_LUT_DAY[wc].astype(np.float32)
        if 'blue_marble' in atlas:
            sat = _sample(atlas['blue_marble'], bounds, clat, clon, vdeg,
                          mode='average').astype(np.float32)
            fb = np.clip(wc_colors * 0.4 + sat * 0.6, 0, 255).astype(np.uint8)
        else:
            fb = wc_colors.astype(np.uint8)
        fb = np.clip(fb.astype(np.float32) * shade[..., None],
                     0, 255).astype(np.uint8)

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
            sat = _sample(atlas['blue_marble'], bounds, clat, clon, vdeg,
                          mode='average').astype(np.float32)
            # Gamma lift to match elevation brightness
            sat = np.clip(255.0 * (sat / 255.0) ** 0.65, 0, 255)
            fb = sat.astype(np.uint8)
        else:
            fb = np.zeros((S, S, 3), dtype=np.uint8)

    elif mode == 'live':
        # Real-time day/night — satellite where sun is up, city lights where down
        import datetime
        now = datetime.datetime.now(datetime.UTC)
        utc_hour = now.hour + now.minute / 60.0
        doy = now.timetuple().tm_yday
        half = vdeg / 2

        if 'blue_marble' in atlas:
            day_img = _sample(atlas['blue_marble'], bounds, clat, clon, vdeg,
                              mode='average').astype(np.float32)
        else:
            day_img = np.full((S, S, 3), 40, dtype=np.float32)

        night_img = day_img * 0.06

        # Vectorised sun elevation for all pixels
        py = np.arange(S)
        px = np.arange(S)
        lats = clat + half - ((py + 0.5) / S) * vdeg
        lons = clon - half + ((px + 0.5) / S) * vdeg
        lat_grid, lon_grid = np.meshgrid(lats, lons, indexing='ij')
        lat_r = np.radians(lat_grid)
        dec_r = np.radians(23.45 * np.sin(np.radians((284 + doy) / 365 * 360)))
        ha = np.radians((utc_hour - 12) * 15 + lon_grid)
        sin_e = np.sin(lat_r) * np.sin(dec_r) + np.cos(lat_r) * np.cos(dec_r) * np.cos(ha)
        sun_e = np.degrees(np.arcsin(np.clip(sin_e, -1, 1)))
        t = np.clip((sun_e + 6) / 12.0, 0, 1)[..., np.newaxis]

        fb = np.clip(day_img * t + night_img * (1 - t), 0, 255)

        # City lights in dark areas
        if 'nightlights' in atlas:
            lights = _sample(atlas['nightlights'], bounds, clat, clon, vdeg,
                             mode='average').astype(np.float32)
            dark = (t[..., 0] < 0.8) & (lights > 10)
            if dark.any():
                b = (np.clip((lights - 10) / 120.0, 0, 1) * (1.0 - t[..., 0]))
                lc = np.array([255, 200, 90], dtype=np.float32)
                for c in range(3):
                    fb[:, :, c] = np.where(dark,
                        fb[:, :, c] * (1 - b) + lc[c] * b,
                        fb[:, :, c])

        fb = fb.astype(np.uint8)

    elif mode == 'night':
        # Dimmed satellite as base
        if 'blue_marble' in atlas:
            sat = _sample(atlas['blue_marble'], bounds, clat, clon, vdeg,
                          mode='average').astype(np.float32)
            fb = np.clip(sat * 0.08, 0, 255).astype(np.uint8)
        else:
            fb = np.zeros((S, S, 3), dtype=np.uint8)
        # City lights glow
        if 'nightlights' in atlas:
            lights = _sample(atlas['nightlights'], bounds, clat, clon, vdeg,
                             mode='average').astype(np.float32)
            mask = lights > 10
            if mask.any():
                b = np.clip((lights - 10) / 120.0, 0, 1)
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
            # Dimmed satellite as base for unclaimed land
            if 'blue_marble' in atlas:
                sat = _sample(atlas['blue_marble'], bounds, clat, clon, vdeg,
                              mode='average').astype(np.float32)
                fb = np.clip(sat * 0.35, 0, 255).astype(np.uint8)
            else:
                fb = np.zeros((S, S, 3), dtype=np.uint8)
            # Empire territories overlaid
            hb = tuple(atlas['_history_bounds'])
            hist = _sample(grids[ei], hb, clat, clon, vdeg, mode='majority')
            claimed = hist > 0
            empire_colors = _HIST_COLORS[np.clip(hist, 0, 15)].astype(np.float32)
            if 'blue_marble' in atlas:
                blended = np.clip(empire_colors * 0.6 + sat * 0.4,
                                  0, 255).astype(np.uint8)
            else:
                blended = empire_colors.astype(np.uint8)
            fb[claimed] = blended[claimed]
        else:
            fb = np.zeros((S, S, 3), dtype=np.uint8)

    else:
        fb = np.zeros((S, S, 3), dtype=np.uint8)

    # Roads overlay
    if vdeg < 5 and 'roads' in atlas:
        is_night = mode == 'night'
        rc = np.array([90, 80, 65] if not is_night else [220, 190, 140],
                      dtype=np.uint8)
        roads = _sample(atlas['roads'], bounds, clat, clon, vdeg)
        if (roads > 0).any():
            fb[roads > 0] = rc
        if 'rails' in atlas:
            rlc = np.array([110, 55, 45] if not is_night else [180, 160, 120],
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
        # Prefer world atlas (Pi-optimised, then full)
        for name in ('world_atlas_pi.npz', 'world_atlas.npz'):
            p = os.path.join(d, name)
            if os.path.exists(p):
                return p, d
        # Then regional fallbacks
        for name in ('atlas_norcal.npz', 'atlas_mideast.npz'):
            p = os.path.join(d, name)
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
    category = "road_rail"

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
        self._max_zoom_out = 145.0

        # Input state (stored for update)
        self._pan_dx = 0
        self._pan_dy = 0
        self._zoom_dir = 0

        # Overlay
        self._overlay_timer = 0.0
        self._overlay_text = ""
        self._live_timer = 0.0
        self._both_pressed_prev = False

        self._load()
        if self._atlas is not None:
            self._init_view()

    def _download_file(self, url, dest, label=""):
        """Download a file with progress shown on the loading screen."""
        try:
            req = urllib.request.Request(url)
            resp = urllib.request.urlopen(req, timeout=30)
            total = int(resp.headers.get('Content-Length', 0))
            chunk_size = 64 * 1024
            downloaded = 0
            with open(dest + '.tmp', 'wb') as f:
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        pct = downloaded / total
                        mb = downloaded / 1e6
                        self._draw_loading(pct, f"{label} {mb:.0f}MB")
                        self.display.render()
            os.rename(dest + '.tmp', dest)
            return True
        except Exception:
            # Clean up partial download
            for p in (dest + '.tmp', dest):
                if os.path.exists(p) and p.endswith('.tmp'):
                    os.remove(p)
            return False

    def _ensure_atlas_data(self):
        """Download atlas data from GitHub Releases if not present locally."""
        # Use first writable directory (prefer assets/atlas/)
        dest_dir = os.path.join(_PROJECT, 'assets', 'atlas')
        os.makedirs(dest_dir, exist_ok=True)

        for filename, required in _ATLAS_FILES:
            # Already exists somewhere?
            for d in _ATLAS_DIRS:
                if os.path.exists(os.path.join(d, filename)):
                    break
            else:
                # Not found — download it
                url = f"{_RELEASE_URL}/{filename}"
                dest = os.path.join(dest_dir, filename)
                self._draw_loading(0.0, f"DOWNLOAD")
                self.display.render()
                if not self._download_file(url, dest, filename.split('.')[0]):
                    if required:
                        return False
        return True

    def _load(self):
        global _cached_atlas

        # Reuse cached atlas if available (instant after first load)
        if _cached_atlas is not None:
            self._atlas = _cached_atlas
            return

        self._draw_loading(0.0, "THE WORLD")
        self.display.render()

        path, directory = _find_atlas()
        if path is None:
            # Try downloading from GitHub Releases
            if not self._ensure_atlas_data():
                return
            path, directory = _find_atlas()
            if path is None:
                return

        self._draw_loading(0.2, "THE WORLD")
        self.display.render()

        d = np.load(path, allow_pickle=True)
        atlas = {}
        for key in d.files:
            atlas[key] = d[key]

        self._draw_loading(0.5, "THE WORLD")
        self.display.render()

        # Load supplementary data from same directory
        # Countries: only load separate file if atlas lacks built-in countries
        if 'countries' not in atlas:
            cp = os.path.join(directory, 'countries_global.npz')
            if os.path.exists(cp):
                cd = np.load(cp)
                atlas['_countries_global'] = cd['grid']
                atlas['_countries_bounds'] = cd['bounds']

        # History disabled for now — grids too large for Pi's 906 MB RAM
        # TODO: re-bake history at 8x downscale to fit in memory

        self._draw_loading(1.0, "READY")
        self.display.render()

        self._atlas = atlas
        _cached_atlas = atlas

    def _init_view(self):
        """Set initial view — called after every reset, even with cache."""
        bounds = tuple(self._atlas['bounds'])
        lat_range = bounds[1] - bounds[0]
        lon_range = bounds[3] - bounds[2]
        self._max_zoom_out = min(max(lat_range, lon_range), 145.0)
        is_global = lon_range >= 350
        if is_global:
            # Start on Stockton, CA
            self._center_lat = 37.95
            self._center_lon = -121.29
        else:
            self._center_lat = (bounds[0] + bounds[1]) / 2
            self._center_lon = (bounds[2] + bounds[3]) / 2
        self._view_deg = 5.0

        self._overlay_text = MODES[self._mode_idx].upper()
        self._overlay_timer = 2.0

    def handle_input(self, inp):
        if self._atlas is None:
            return False

        # Antipodal flip — both buttons pressed simultaneously
        both_now = inp.action_l_held and inp.action_r_held
        if both_now and not self._both_pressed_prev:
            self._center_lat = -self._center_lat
            self._center_lon = self._center_lon + 180
            if self._center_lon > 180:
                self._center_lon -= 360
            self._overlay_text = "ANTIPODE"
            self._overlay_timer = 2.0
            self._needs_render = True
            self._both_pressed_prev = True
            return True
        self._both_pressed_prev = both_now

        zoom_held = inp.action_r_held

        # Mode cycle (action_l only — action_r is zoom modifier)
        if inp.action_l:
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
            speed = self._view_deg * 1.2 * dt
            self._center_lon += self._pan_dx * speed
            self._center_lat -= self._pan_dy * speed
            # Wrap longitude, clamp latitude
            if self._center_lon > 180:
                self._center_lon -= 360
            elif self._center_lon < -180:
                self._center_lon += 360
            half_view = self._view_deg / 2
            self._center_lat = max(-60 + half_view,
                                   min(85 - half_view, self._center_lat))
            self._needs_render = True

        # Zoom
        if self._zoom_dir:
            if self._zoom_dir > 0:
                self._view_deg = max(0.5, self._view_deg * (1 - 0.8 * dt))
            else:
                self._view_deg = min(self._max_zoom_out,
                                     self._view_deg * (1 + 0.8 * dt))
            self._needs_render = True

        # In flat mode, clamp so view stays within atlas lat bounds
        if self._view_deg < GLOBE_THRESHOLD:
            max_vdeg_for_lat = 145.0  # 85 - (-60)
            if self._view_deg > max_vdeg_for_lat:
                self._view_deg = max_vdeg_for_lat
            half_view = self._view_deg / 2
            self._center_lat = max(-60 + half_view,
                                   min(85 - half_view, self._center_lat))

        # Live mode auto-refresh every 10 seconds
        if MODES[self._mode_idx] == 'live':
            if not hasattr(self, '_live_timer'):
                self._live_timer = 0.0
            self._live_timer += dt
            if self._live_timer > 10:
                self._live_timer = 0.0
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

        # Blit numpy framebuffer → display
        fb = self._fb
        if hasattr(self.display, '_fb'):
            # Hardware: single memcpy into flat bytearray
            self.display._fb[:] = fb.tobytes()
        else:
            # Emulator: write to 2D buffer list
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
