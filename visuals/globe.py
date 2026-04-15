"""Earth — real-data rotating Earth on a 64×64 LED matrix.

Replaces the old GIF-based Earth visual with live Blue Marble satellite
imagery, terrain, city lights, and real-time day/night terminator.

Controls:
    Joystick          Rotate the globe (overrides auto-rotation)
    Action L          Cycle visual mode
    Action R + ↑/↓    Zoom in / out
"""

import os
import numpy as np
from . import Visual, Display, GRID_SIZE
from .atlas import (
    _ATLAS_DIRS, _RELEASE_URL, _ATLAS_FILES, _PROJECT,
    _WC_LUT_DAY, _ELEV_LUT, _sample_at, _find_atlas, _cached_atlas,
)
import urllib.request

MODES = ['satellite', 'terrain', 'live', 'night', 'elevation']


def _render_globe(atlas, rot_lat, rot_lon, mode, radius=27.0):
    """Render atlas data on a 3D sphere with variable radius."""
    S = GRID_SIZE
    bounds = tuple(atlas['bounds'])
    fb = np.zeros((S, S, 3), dtype=np.uint8)

    cx, cy = S / 2, S / 2
    py = np.arange(S)
    px = np.arange(S)
    xx, yy = np.meshgrid((px - cx + 0.5) / radius, (cy - py - 0.5) / radius)

    # Ray-sphere intersection (orthographic)
    zz_sq = 1.0 - xx ** 2 - yy ** 2
    on_sphere = zz_sq > 0
    zz = np.sqrt(np.where(on_sphere, zz_sq, 0))

    # Rotate: Y-axis (longitude), then X-axis (latitude tilt)
    rlat = np.radians(rot_lat)
    rlon = np.radians(rot_lon)
    cos_rlon, sin_rlon = np.cos(rlon), np.sin(rlon)
    cos_rlat, sin_rlat = np.cos(rlat), np.sin(rlat)

    x1 = xx * cos_rlon + zz * sin_rlon
    z1 = -xx * sin_rlon + zz * cos_rlon
    y1 = yy
    y2 = y1 * cos_rlat - z1 * sin_rlat
    z2 = y1 * sin_rlat + z1 * cos_rlat
    x2 = x1

    lat = np.degrees(np.arcsin(np.clip(y2, -1, 1)))
    lon = np.degrees(np.arctan2(x2, z2))

    # Lambertian shading — bright frontal lighting
    shade = np.clip(x2 * 0.1 + y2 * 0.2 + zz * 0.85 + 0.25, 0.3, 1.3)

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
        sat = 255.0 * (sat / 255.0) ** 0.65
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

        dec_r = np.radians(
            23.45 * np.sin(np.radians((284 + doy) / 365 * 360)))
        ha = np.radians((utc_hour - 12) * 15 + lon)
        sin_e = (np.sin(np.radians(lat)) * np.sin(dec_r) +
                 np.cos(np.radians(lat)) * np.cos(dec_r) * np.cos(ha))
        sun_e = np.degrees(np.arcsin(np.clip(sin_e, -1, 1)))
        t = np.clip((sun_e + 6) / 12.0, 0, 1)[..., None]

        mixed = sat * t + night_img * (1 - t)
        if 'nightlights' in atlas:
            lights = _sample_at(atlas['nightlights'], bounds,
                                lat, lon).astype(np.float32)
            dark = (t[..., 0] < 0.8) & (lights > 10)
            if dark.any():
                b = (np.clip((lights - 10) / 120.0, 0, 1)
                     * (1.0 - t[..., 0]))
                lc = np.array([255, 200, 90], dtype=np.float32)
                for c in range(3):
                    mixed[:, :, c] = np.where(
                        dark,
                        mixed[:, :, c] * (1 - b) + lc[c] * b,
                        mixed[:, :, c])
        globe = np.clip(mixed * shade[..., None], 0, 255).astype(np.uint8)

    elif mode == 'night':
        sat = _sample_at(atlas['blue_marble'], bounds, lat, lon).astype(
            np.float32) if 'blue_marble' in atlas else np.zeros(
            lat.shape + (3,), dtype=np.float32)
        mixed = sat * 0.08
        if 'nightlights' in atlas:
            lights = _sample_at(atlas['nightlights'], bounds,
                                lat, lon).astype(np.float32)
            mask = lights > 10
            if mask.any():
                b = np.clip((lights - 10) / 120.0, 0, 1)
                lc = np.array([255, 200, 90], dtype=np.float32)
                for c in range(3):
                    mixed[:, :, c] = np.where(
                        mask,
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

    fb[on_sphere] = globe[on_sphere]

    # Subtle atmosphere rim glow (only when sphere is smaller than frame)
    if radius < 40:
        edge = on_sphere & (zz_sq < 0.05)
        if edge.any():
            glow = np.array([10, 20, 45], dtype=np.uint8)
            fb[edge] = np.clip(fb[edge].astype(np.int16) + glow,
                               0, 255).astype(np.uint8)

    return fb


class Earth(Visual):
    name = "EARTH"
    description = "Rotating Earth"
    category = "science_macro"

    AUTO_SPEED = 8.0      # degrees/sec auto-rotation
    IDLE_TIMEOUT = 0.5    # seconds before auto-rotation resumes after input

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self._atlas = None
        self._fb = None
        self._needs_render = True

        # Earth state
        self._rot_lon = 20.0     # start facing Europe/Africa
        self._rot_lat = 30.0    # tilt to show populated latitudes
        self._radius = 27.0      # default sphere size
        self._mode_idx = 0

        # Auto-rotation
        self._auto_rotate = True
        self._idle_timer = 0.0
        self._speed = self.AUTO_SPEED

        # Input state
        self._pan_dx = 0
        self._pan_dy = 0
        self._zoom_dir = 0

        # Overlay
        self._overlay_timer = 0.0
        self._overlay_text = ""
        self._live_timer = 0.0

        # action_r toggle tracking
        self._action_r_used = False  # True if speed/zoom used during hold
        self._action_r_was_held = False

        # Stars background (fixed random positions, very subtle)
        rng = np.random.RandomState(42)
        self._star_x = rng.randint(0, GRID_SIZE, 40)
        self._star_y = rng.randint(0, GRID_SIZE, 40)
        self._star_bright = rng.randint(12, 35, 40)

        self._load()

    def _load(self):
        global _cached_atlas
        from .atlas import _cached_atlas

        if _cached_atlas is not None:
            self._atlas = _cached_atlas
            return

        self._draw_loading(0.0, "THE WORLD")
        self.display.render()

        path, directory = _find_atlas()
        if path is None:
            # Try downloading from GitHub Releases (same as Atlas)
            from .atlas import Atlas
            _downloader = Atlas.__new__(Atlas)
            _downloader.display = self.display
            _downloader.name = self.name
            if not _downloader._ensure_atlas_data():
                return
            path, directory = _find_atlas()
            if path is None:
                return

        self._draw_loading(0.3, "THE WORLD")
        self.display.render()

        d = np.load(path, allow_pickle=True)
        atlas = {}
        for key in d.files:
            atlas[key] = d[key]

        self._draw_loading(1.0, "READY")
        self.display.render()

        self._atlas = atlas

        # Share cache with Atlas visual
        import visuals.atlas as _atlas_mod
        _atlas_mod._cached_atlas = atlas

    def handle_input(self, inp):
        if self._atlas is None:
            return False

        # Mode cycle
        if inp.action_l:
            self._mode_idx = (self._mode_idx + 1) % len(MODES)
            self._overlay_text = MODES[self._mode_idx].upper()
            self._overlay_timer = 2.0
            self._needs_render = True
            return True

        # action_r held: up/down = zoom, left/right = rotation speed
        if inp.action_r_held:
            self._zoom_dir = -inp.dy
            if inp.left:
                self._speed = max(0.5, self._speed * 0.97)
                self._action_r_used = True
            if inp.right:
                self._speed = min(360.0, self._speed * 1.03)
                self._action_r_used = True
            if inp.dy:
                self._action_r_used = True
            self._pan_dx = 0
            self._pan_dy = 0
        else:
            # Toggle on release — only if action_r was held and not used for speed/zoom
            if self._action_r_was_held and not self._action_r_used:
                self._auto_rotate = not self._auto_rotate
                self._overlay_text = "SPIN ON" if self._auto_rotate else "SPIN OFF"
                self._overlay_timer = 1.5
            if self._action_r_was_held:
                self._action_r_used = False
            self._pan_dx = inp.dx
            self._pan_dy = inp.dy
            self._zoom_dir = 0

        self._action_r_was_held = inp.action_r_held

        # Manual joystick input — auto-rotate picks back up after idle
        if inp.any_direction and not inp.action_r_held:
            self._idle_timer = 0.0

        return bool(inp.any_direction or inp.action_r_held)

    def update(self, dt):
        super().update(dt)

        # Manual rotation
        if self._pan_dx or self._pan_dy:
            rot_speed = 60.0 * dt
            self._rot_lon -= self._pan_dx * rot_speed
            self._rot_lat += self._pan_dy * rot_speed
            self._needs_render = True

        # Zoom
        if self._zoom_dir:
            if self._zoom_dir > 0:
                self._radius = min(120.0, self._radius * (1 + 1.2 * dt))
            else:
                self._radius = max(12.0, self._radius * (1 - 1.2 * dt))
            self._needs_render = True

        # Auto-rotate (pauses briefly during manual input)
        self._idle_timer += dt
        if self._auto_rotate and self._idle_timer > self.IDLE_TIMEOUT:
            self._rot_lon -= self._speed * dt
            self._needs_render = True

        # Wrap longitude
        if self._rot_lon > 180:
            self._rot_lon -= 360
        elif self._rot_lon < -180:
            self._rot_lon += 360

        # Live mode auto-refresh
        if MODES[self._mode_idx] == 'live':
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
            self.display.draw_text_small(2, 24, "GLOBE", (200, 160, 40))
            self.display.draw_text_small(2, 32, "NO DATA", (200, 50, 50))
            return

        if self._needs_render:
            self._fb = _render_globe(self._atlas, self._rot_lat,
                                     self._rot_lon,
                                     MODES[self._mode_idx],
                                     self._radius)
            # Subtle stars on black background (behind the sphere)
            for i in range(len(self._star_x)):
                sx, sy = int(self._star_x[i]), int(self._star_y[i])
                if self._fb[sy, sx, 0] == 0 and self._fb[sy, sx, 1] == 0:
                    b = int(self._star_bright[i])
                    self._fb[sy, sx] = (b, b, b)
            self._needs_render = False

        # Blit
        fb = self._fb
        if hasattr(self.display, '_fb'):
            self.display._fb[:] = fb.tobytes()
        else:
            buf = self.display.buffer
            for y in range(GRID_SIZE):
                row = buf[y]
                for x in range(GRID_SIZE):
                    px = fb[y, x]
                    row[x] = (int(px[0]), int(px[1]), int(px[2]))

        # Mode overlay
        if self._overlay_timer > 0:
            alpha = min(1.0, self._overlay_timer / 0.5)
            c = int(200 * alpha)
            self.display.draw_text_small(2, 2, self._overlay_text, (c, c, c))
