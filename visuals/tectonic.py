"""
Tectonic - Plate Dynamics Cross-Section
========================================
A textbook-style side-view cross-section showing tectonic plate dynamics
on a 64x64 LED matrix.  Left to right: oceanic crust approaching a
subduction zone, continental crust with mountains, a transform fault,
a mid-ocean ridge (divergent boundary), and oceanic crust spreading away.

Animated mantle convection cells, volcanic eruptions, magma upwelling at
the ridge, transform-fault earthquakes, and gentle ocean waves bring the
diagram to life.

Controls:
  Left/Right     - Adjust simulation speed
  Up/Down        - Cycle focus mode (ALL / SUBDUCTION / DIVERGENT / TRANSFORM)
  Action button  - Trigger earthquake at focused boundary
  Both held      - Toggle scrolling notes
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE

# ── Layout constants ────────────────────────────────────────────
# Vertical zones
SKY_TOP = 0
SKY_BOT = 5       # sky rows 0-4
WATER_Y = 5       # ocean surface
CRUST_TOP = 8     # top of crust layer
MANTLE_TOP = 12   # top of mantle
MANTLE_BOT = 52   # bottom of upper mantle
DEEP_BOT = 55     # bottom of lower/deep mantle
INFO_TOP = 56     # info/label area

# Horizontal feature centers
SUBDUCTION_X = 12
RIDGE_X = 44
TRANSFORM_X = 35
CONTINENT_L = 15  # left edge of continental crust
CONTINENT_R = 37  # right edge of continental crust

# ── Colors ──────────────────────────────────────────────────────
SKY_TOP_C = (5, 5, 20)
SKY_BOT_C = (10, 15, 40)
OCEAN_DEEP = (20, 40, 120)
OCEAN_LIGHT = (30, 60, 160)

CONT_CRUST_BASE = (160, 130, 80)
CONT_CRUST_DARK = (120, 100, 60)
OCEAN_CRUST_C = (60, 70, 50)
OCEAN_CRUST_L = (80, 90, 65)

MOUNTAIN_C = (180, 160, 110)
SNOW_C = (220, 220, 230)

MANTLE_WARM = (180, 60, 20)
MANTLE_HOT = (220, 100, 30)
DEEP_MANTLE_C = (140, 30, 40)
DEEP_MANTLE_H = (160, 20, 50)

MAGMA_BRIGHT = (255, 200, 50)
MAGMA_MED = (255, 120, 20)

SLAB_C = (100, 80, 60)

# Focus modes
FOCUS_MODES = ["ALL", "SUBDUCTION", "DIVERGENT", "TRANSFORM"]

# ── Terrain profile ─────────────────────────────────────────────

def _build_terrain():
    """Return surface_y[x] and crust_bottom[x] arrays for x in 0..63.

    surface_y    = top of solid surface (sea floor or land surface)
    crust_bottom = bottom of crust (interface to mantle)
    is_land      = True if pixel column is above water (continent / volcano)
    """
    surface_y = [0] * 64
    crust_bot = [0] * 64
    is_land = [False] * 64
    crust_color = [(0, 0, 0)] * 64

    for x in range(64):
        if x <= 10:
            # Oceanic crust approaching subduction
            surface_y[x] = CRUST_TOP
            crust_bot[x] = CRUST_TOP + 3
            crust_color[x] = OCEAN_CRUST_C
        elif x <= 14:
            # Transition: oceanic crust diving under continent
            t = (x - 10) / 4.0
            surface_y[x] = int(CRUST_TOP - t * 2)  # rises slightly
            crust_bot[x] = CRUST_TOP + 3 + int(t * 2)
            crust_color[x] = _lerp_color(OCEAN_CRUST_C, CONT_CRUST_BASE, t)
            if t > 0.5:
                is_land[x] = True
        elif x <= 20:
            # Continental crust with mountain ridge near subduction
            # Mountains peak around x=17-18
            dist_from_peak = abs(x - 17)
            elev = max(0, 4 - dist_from_peak)
            surface_y[x] = CRUST_TOP - 3 - elev
            crust_bot[x] = CRUST_TOP + 7  # thick continental crust
            crust_color[x] = CONT_CRUST_BASE
            is_land[x] = True
        elif x <= 32:
            # Continental interior -- gentle terrain
            surface_y[x] = CRUST_TOP - 2
            crust_bot[x] = CRUST_TOP + 6
            crust_color[x] = CONT_CRUST_DARK
            is_land[x] = True
        elif x <= 37:
            # Transform fault zone -- two plates, slight offset
            offset = 1 if x >= 35 else 0
            surface_y[x] = CRUST_TOP - 1 + offset
            crust_bot[x] = CRUST_TOP + 4 + offset
            t = (x - 32) / 5.0
            crust_color[x] = _lerp_color(CONT_CRUST_DARK, OCEAN_CRUST_L, t)
            is_land[x] = x < 35
        elif x <= 40:
            # Transition to ocean
            surface_y[x] = CRUST_TOP
            crust_bot[x] = CRUST_TOP + 3
            crust_color[x] = OCEAN_CRUST_L
        elif x <= 47:
            # Mid-ocean ridge area -- crust thins at center
            dist_from_ridge = abs(x - RIDGE_X)
            thin = max(0, 3 - dist_from_ridge)
            surface_y[x] = CRUST_TOP + thin  # ridge rises
            if dist_from_ridge <= 1:
                surface_y[x] = CRUST_TOP - 1  # ridge crest above normal
            crust_bot[x] = CRUST_TOP + 3 - thin
            if crust_bot[x] <= surface_y[x]:
                crust_bot[x] = surface_y[x] + 1
            crust_color[x] = OCEAN_CRUST_C
        else:
            # Oceanic crust spreading away from ridge
            surface_y[x] = CRUST_TOP
            crust_bot[x] = CRUST_TOP + 3
            crust_color[x] = OCEAN_CRUST_C

    return surface_y, crust_bot, is_land, crust_color


def _lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


def _lerp(a, b, t):
    return a + (b - a) * max(0.0, min(1.0, t))


# ── Subduction slab geometry ────────────────────────────────────

def _build_slab_pixels():
    """Return list of (x, y) pixels for the descending oceanic slab."""
    pixels = []
    # Diagonal line from surface (x~10, y~CRUST_TOP) diving down-right into mantle
    for i in range(40):
        x = 10 + int(i * 0.15)
        y = CRUST_TOP + 3 + int(i * 0.9)
        if 0 <= x < 64 and 0 <= y < MANTLE_BOT:
            pixels.append((x, y))
            if x + 1 < 64:
                pixels.append((x + 1, y))
    return pixels


# ── Convection flow field ──────────────────────────────────────

def _flow_velocity(x, y):
    """Return (vx, vy) for mantle convection at position (x, y).

    Two main convection cells:
    - Cell 1: rises at ridge (~x=44), flows left at crust, descends at subduction (~x=12)
    - Cell 2: rises at ridge (~x=44), flows right, descends at right edge (~x=60)
    Plus deep return flow.
    """
    # Normalize position
    # Mantle spans y = MANTLE_TOP..MANTLE_BOT, x = 0..63
    ny = (y - MANTLE_TOP) / max(1, MANTLE_BOT - MANTLE_TOP)  # 0 = top, 1 = bottom
    speed = 3.0

    # Cell 1: left cell (x=5..44)
    if x < RIDGE_X:
        nx = (x - 5) / max(1, RIDGE_X - 5)  # 0 at left, 1 at ridge
        # Rising at ridge (nx~1), descending at subduction (nx~0.15)
        # Top flow: leftward. Bottom flow: rightward.
        rise_x = 1.0  # ridge side
        sink_x = 0.15  # subduction side

        if nx > 0.85:
            # Rising column near ridge
            vx = (1.0 - ny) * 0.3 * speed
            vy = -(1.0 - abs(nx - 1.0) * 5) * speed * 1.2
        elif nx < 0.25:
            # Sinking column near subduction
            vx = -(1.0 - ny) * 0.2 * speed
            vy = nx * speed * 0.8
        elif ny < 0.3:
            # Top: flowing left (plate drag)
            vx = -speed * 0.7
            vy = 0.0
        elif ny > 0.7:
            # Bottom: return flow rightward
            vx = speed * 0.5
            vy = 0.0
        else:
            # Middle: transitional
            vx = speed * 0.3 * (ny - 0.5) * 2.0
            vy = speed * 0.15 * (0.5 - nx)
    else:
        # Cell 2: right cell (x=44..63)
        nx = (x - RIDGE_X) / max(1, 63 - RIDGE_X)
        if nx < 0.15:
            # Rising near ridge
            vx = -(1.0 - ny) * 0.3 * speed
            vy = -(1.0 - nx * 6) * speed * 1.2
        elif nx > 0.85:
            # Sinking at right edge
            vx = (1.0 - ny) * 0.2 * speed
            vy = (1.0 - abs(nx - 1.0) * 5) * speed * 0.6
        elif ny < 0.3:
            # Top: flowing right
            vx = speed * 0.7
            vy = 0.0
        elif ny > 0.7:
            # Bottom: return flow leftward
            vx = -speed * 0.5
            vy = 0.0
        else:
            vx = -speed * 0.3 * (ny - 0.5) * 2.0
            vy = speed * 0.15 * (nx - 0.5)

    return vx, vy


# ── Precompute static data ─────────────────────────────────────
_TERRAIN = _build_terrain()
_SLAB_PIXELS = _build_slab_pixels()


# ── Main visual class ──────────────────────────────────────────

class Tectonic(Visual):
    name = "TECTONIC"
    description = "Plate dynamics"
    category = "science_macro"

    def __init__(self, display: Display):
        super().__init__(display)

    # ── reset ───────────────────────────────────────────────────

    def reset(self):
        self.time = 0.0

        # Simulation speed multiplier
        self.sim_speed = 1.0

        # Focus mode
        self.focus_idx = 0

        # Overlay
        self.overlay_text = ''
        self.overlay_timer = 0.0

        # Scrolling notes
        self.show_notes = False
        self.notes_scroll_offset = 0.0
        self.notes_segments = []
        self.notes_scroll_len = 1
        self._both_pressed_prev = False

        # Terrain (precomputed)
        self.surface_y, self.crust_bot, self.is_land, self.crust_color = _TERRAIN

        # Convection particles
        self.particles = []
        self._init_particles()

        # Magma particles at ridge
        self.magma_particles = []
        self._init_magma()

        # Volcanic eruption state
        self.eruption_timer = random.uniform(4.0, 8.0)
        self.eruption_particles = []

        # Earthquake state
        self.quake_timer = random.uniform(5.0, 10.0)
        self.quake_flash = 0.0
        self.quake_jitter = 0

        # Slab dehydration particles
        self.dehydration_particles = []
        self.dehydration_timer = random.uniform(2.0, 5.0)

        # Plate motion arrow animation
        self.arrow_phase = 0.0

        # Label cycling
        self.label_timer = 0.0
        self.label_idx = 0

        self._build_notes_segments()

    # ── particles ───────────────────────────────────────────────

    def _init_particles(self):
        """Create convection particles distributed through the mantle."""
        self.particles = []
        for _ in range(70):
            x = random.uniform(2, 62)
            y = random.uniform(MANTLE_TOP + 2, MANTLE_BOT - 2)
            self.particles.append([x, y])

    def _init_magma(self):
        """Create magma particles rising at the mid-ocean ridge."""
        self.magma_particles = []
        for _ in range(12):
            x = RIDGE_X + random.uniform(-1.5, 1.5)
            y = random.uniform(MANTLE_TOP, MANTLE_BOT)
            self.magma_particles.append([x, y, random.uniform(0.5, 1.0)])  # x, y, heat

    # ── notes ───────────────────────────────────────────────────

    def _build_notes_segments(self):
        sep = '  --  '
        sep_color = (60, 55, 50)
        notes = [
            ("PLATE TECTONICS", (255, 255, 255)),
            ("DIVERGENT: PLATES PULL APART", (255, 160, 40)),
            ("CONVERGENT: PLATES COLLIDE", (80, 200, 220)),
            ("TRANSFORM: PLATES SLIDE", (255, 255, 80)),
            ("CONVECTION DRIVES MOTION", (220, 100, 30)),
            ("ALFRED WEGENER 1912", (255, 255, 255)),
        ]
        segments = []
        px_off = 0
        for i, (text, color) in enumerate(notes):
            if i > 0:
                segments.append((px_off, sep, sep_color))
                px_off += len(sep) * 4
            segments.append((px_off, text, color))
            px_off += len(text) * 4
        segments.append((px_off, sep, sep_color))
        px_off += len(sep) * 4
        self.notes_segments = segments
        self.notes_scroll_len = px_off

    def _draw_notes(self):
        d = self.display
        scroll_x = int(self.notes_scroll_offset) % self.notes_scroll_len
        for copy in (0, self.notes_scroll_len):
            for seg_off, text, color in self.notes_segments:
                px = 2 + seg_off + copy - scroll_x
                text_w = len(text) * 4
                if px + text_w < 0 or px > 64:
                    continue
                d.draw_text_small(px, 58, text, color)

    # ── overlay ─────────────────────────────────────────────────

    def _show_overlay(self, text):
        self.overlay_text = text
        self.overlay_timer = 2.0

    def _draw_overlay(self):
        if self.overlay_timer <= 0:
            return
        alpha = min(1.0, self.overlay_timer / 0.5)
        c = (int(255 * alpha), int(255 * alpha), int(255 * alpha))
        self.display.draw_text_small(2, 2, self.overlay_text, c)

    # ── input ───────────────────────────────────────────────────

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Left/Right: adjust simulation speed
        if input_state.left_pressed:
            self.sim_speed = max(0.25, self.sim_speed - 0.25)
            self._show_overlay(f"SPEED {self.sim_speed:.1f}X" if self.sim_speed != 1.0 else "SPEED 1X")
            consumed = True
        if input_state.right_pressed:
            self.sim_speed = min(4.0, self.sim_speed + 0.25)
            self._show_overlay(f"SPEED {self.sim_speed:.1f}X" if self.sim_speed != 1.0 else "SPEED 1X")
            consumed = True

        # Up/Down: cycle focus
        if input_state.up_pressed:
            self.focus_idx = (self.focus_idx - 1) % len(FOCUS_MODES)
            self._show_overlay(FOCUS_MODES[self.focus_idx])
            consumed = True
        if input_state.down_pressed:
            self.focus_idx = (self.focus_idx + 1) % len(FOCUS_MODES)
            self._show_overlay(FOCUS_MODES[self.focus_idx])
            consumed = True

        # Both buttons: toggle notes
        both = (input_state.action_l_held or input_state.action_l) and \
               (input_state.action_r_held or input_state.action_r)
        if both and not self._both_pressed_prev:
            self.show_notes = not self.show_notes
            self.notes_scroll_offset = 0.0
            consumed = True
        elif (input_state.action_l or input_state.action_r) and not both:
            # Single press: trigger earthquake at focused boundary
            if not self._both_pressed_prev:
                self._trigger_event()
                consumed = True
        self._both_pressed_prev = both

        return consumed

    def _trigger_event(self):
        """Trigger an earthquake or eruption at the focused boundary."""
        mode = FOCUS_MODES[self.focus_idx]
        if mode == "SUBDUCTION" or mode == "ALL":
            # Trigger eruption
            self._start_eruption()
        if mode == "TRANSFORM" or mode == "ALL":
            # Trigger earthquake flash
            self.quake_flash = 0.2
            self.quake_jitter = 2
        if mode == "DIVERGENT" or mode == "ALL":
            # Boost magma
            for mp in self.magma_particles:
                mp[2] = 1.0  # max heat

    # ── update ──────────────────────────────────────────────────

    def update(self, dt: float):
        self.time += dt
        sdt = dt * self.sim_speed

        # Overlay
        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

        # Notes scroll
        if self.show_notes:
            self.notes_scroll_offset += dt * 18

        # Arrow animation phase
        self.arrow_phase += sdt * 1.5

        # Label cycling
        self.label_timer += dt
        if self.label_timer > 3.0:
            self.label_timer = 0.0
            self.label_idx = (self.label_idx + 1) % 3

        # Update convection particles
        self._update_convection(sdt)

        # Update magma
        self._update_magma(sdt)

        # Volcanic eruption
        self.eruption_timer -= sdt
        if self.eruption_timer <= 0:
            self._start_eruption()
            self.eruption_timer = random.uniform(4.0, 8.0)
        self._update_eruption(sdt)

        # Transform earthquake
        self.quake_timer -= sdt
        if self.quake_timer <= 0:
            self.quake_flash = 0.2
            self.quake_jitter = 2
            self.quake_timer = random.uniform(5.0, 10.0)
        if self.quake_flash > 0:
            self.quake_flash = max(0, self.quake_flash - dt)
        if self.quake_jitter > 0 and self.quake_flash <= 0:
            self.quake_jitter = 0

        # Slab dehydration
        self.dehydration_timer -= sdt
        if self.dehydration_timer <= 0:
            self._spawn_dehydration()
            self.dehydration_timer = random.uniform(2.0, 5.0)
        self._update_dehydration(sdt)

    def _update_convection(self, dt):
        """Move convection particles along the flow field."""
        for p in self.particles:
            vx, vy = _flow_velocity(p[0], p[1])
            p[0] += vx * dt * 0.4
            p[1] += vy * dt * 0.4

            # Wrap / recycle particles that leave the mantle
            if p[1] < MANTLE_TOP + 1:
                p[1] = MANTLE_TOP + 1
            if p[1] > MANTLE_BOT - 1:
                p[1] = MANTLE_BOT - 1
            if p[0] < 1:
                p[0] = 62
            if p[0] > 62:
                p[0] = 1

    def _update_magma(self, dt):
        """Move magma particles upward at the ridge."""
        for mp in self.magma_particles:
            mp[1] -= dt * 4.0  # rise
            mp[0] += random.uniform(-0.1, 0.1)  # slight wobble
            mp[2] -= dt * 0.08  # cool slowly

            # When reaching crust level, respawn at bottom
            if mp[1] < CRUST_TOP or mp[2] <= 0:
                mp[0] = RIDGE_X + random.uniform(-1.5, 1.5)
                mp[1] = random.uniform(MANTLE_BOT - 10, MANTLE_BOT)
                mp[2] = random.uniform(0.6, 1.0)

    def _start_eruption(self):
        """Spawn volcanic eruption particles above the volcanic arc."""
        volcano_x = random.randint(16, 19)
        surface = self.surface_y[volcano_x]
        for _ in range(8):
            self.eruption_particles.append([
                float(volcano_x) + random.uniform(-0.5, 0.5),
                float(surface),
                random.uniform(-0.5, 0.5),   # vx
                random.uniform(-8.0, -4.0),   # vy (upward)
                random.uniform(0.8, 1.5),      # lifetime
            ])

    def _update_eruption(self, dt):
        """Update eruption particles (gravity, fade, remove dead)."""
        alive = []
        for ep in self.eruption_particles:
            ep[0] += ep[2] * dt
            ep[1] += ep[3] * dt
            ep[3] += 12.0 * dt  # gravity
            ep[4] -= dt
            if ep[4] > 0:
                alive.append(ep)
        self.eruption_particles = alive

    def _spawn_dehydration(self):
        """Spawn small particles breaking off the subducting slab."""
        if len(_SLAB_PIXELS) < 5:
            return
        idx = random.randint(len(_SLAB_PIXELS) // 3, len(_SLAB_PIXELS) - 1)
        sx, sy = _SLAB_PIXELS[idx]
        self.dehydration_particles.append([
            float(sx), float(sy),
            random.uniform(-0.5, 0.5),
            random.uniform(-2.0, -0.5),
            random.uniform(0.6, 1.2),
        ])

    def _update_dehydration(self, dt):
        alive = []
        for dp in self.dehydration_particles:
            dp[0] += dp[2] * dt
            dp[1] += dp[3] * dt
            dp[4] -= dt
            if dp[4] > 0:
                alive.append(dp)
        self.dehydration_particles = alive

    # ── draw ────────────────────────────────────────────────────

    def draw(self):
        d = self.display
        d.clear()
        set_pixel = d.set_pixel

        jitter = 0
        if self.quake_jitter > 0:
            jitter = random.choice([-1, 0, 1])

        self._draw_sky(d, set_pixel)
        self._draw_ocean(d, set_pixel)
        self._draw_crust(d, set_pixel, jitter)
        self._draw_mantle(d, set_pixel)
        self._draw_slab(d, set_pixel)
        self._draw_convection(d, set_pixel)
        self._draw_magma(d, set_pixel)
        self._draw_eruption(d, set_pixel)
        self._draw_dehydration(d, set_pixel)
        self._draw_quake_flash(d, set_pixel)
        self._draw_plate_arrows(d, set_pixel)
        self._draw_focus_highlight(d, set_pixel)
        self._draw_labels(d)

        if self.show_notes:
            self._draw_notes()
        self._draw_overlay()

    # ── sky ─────────────────────────────────────────────────────

    def _draw_sky(self, d, set_pixel):
        for y in range(SKY_TOP, SKY_BOT):
            t = y / max(1, SKY_BOT - 1)
            c = _lerp_color(SKY_TOP_C, SKY_BOT_C, t)
            for x in range(64):
                set_pixel(x, y, c)

    # ── ocean ───────────────────────────────────────────────────

    def _draw_ocean(self, d, set_pixel):
        """Draw ocean water over non-land columns with wave animation."""
        for x in range(64):
            if self.is_land[x]:
                continue
            # Wave offset
            wave = int(math.sin(self.time * 2.0 + x * 0.5) * 0.6)
            water_top = WATER_Y + wave
            water_bot = self.surface_y[x]
            for y in range(max(0, water_top), water_bot):
                depth_t = (y - water_top) / max(1, water_bot - water_top)
                c = _lerp_color(OCEAN_LIGHT, OCEAN_DEEP, depth_t)
                set_pixel(x, y, c)

    # ── crust ───────────────────────────────────────────────────

    def _draw_crust(self, d, set_pixel, jitter):
        for x in range(64):
            top = self.surface_y[x]
            bot = self.crust_bot[x]
            base_color = self.crust_color[x]

            # Apply jitter near transform fault
            jx = x
            if jitter != 0 and 33 <= x <= 37:
                jx = max(0, min(63, x + jitter))

            for y in range(top, bot):
                # Slight depth gradient
                t = (y - top) / max(1, bot - top)
                dark = (
                    max(0, int(base_color[0] * (1.0 - t * 0.3))),
                    max(0, int(base_color[1] * (1.0 - t * 0.3))),
                    max(0, int(base_color[2] * (1.0 - t * 0.3))),
                )
                set_pixel(jx, y, dark)

            # Mountains and snow caps
            if self.is_land[x] and 15 <= x <= 20:
                peak_y = self.surface_y[x]
                if peak_y <= CRUST_TOP - 5:
                    # Snow cap on the highest peaks
                    set_pixel(x, peak_y, SNOW_C)
                    if peak_y + 1 < CRUST_TOP:
                        set_pixel(x, peak_y + 1, MOUNTAIN_C)
                elif peak_y <= CRUST_TOP - 3:
                    set_pixel(x, peak_y, MOUNTAIN_C)

    # ── mantle ──────────────────────────────────────────────────

    def _draw_mantle(self, d, set_pixel):
        """Draw mantle background with temperature gradient."""
        for y in range(MANTLE_TOP, DEEP_BOT):
            for x in range(64):
                if y < MANTLE_BOT:
                    # Upper mantle
                    t = (y - MANTLE_TOP) / max(1, MANTLE_BOT - MANTLE_TOP)
                    c = _lerp_color(MANTLE_WARM, MANTLE_HOT, t)
                    # Slightly brighter near ridge
                    ridge_dist = abs(x - RIDGE_X)
                    if ridge_dist < 5 and y > MANTLE_TOP + 5:
                        bright = 1.0 + (5 - ridge_dist) * 0.06
                        c = (min(255, int(c[0] * bright)),
                             min(255, int(c[1] * bright)),
                             min(255, int(c[2] * bright)))
                    # Dim the mantle to ~40% to leave room for particles
                    c = (int(c[0] * 0.35), int(c[1] * 0.35), int(c[2] * 0.35))
                else:
                    # Deep mantle
                    t = (y - MANTLE_BOT) / max(1, DEEP_BOT - MANTLE_BOT)
                    c = _lerp_color(DEEP_MANTLE_C, DEEP_MANTLE_H, t)
                    c = (int(c[0] * 0.4), int(c[1] * 0.4), int(c[2] * 0.4))
                set_pixel(x, y, c)

    # ── subduction slab ─────────────────────────────────────────

    def _draw_slab(self, d, set_pixel):
        for sx, sy in _SLAB_PIXELS:
            if 0 <= sx < 64 and 0 <= sy < 64:
                set_pixel(sx, sy, SLAB_C)

    # ── convection particles ────────────────────────────────────

    def _draw_convection(self, d, set_pixel):
        for p in self.particles:
            ix, iy = int(p[0]), int(p[1])
            if 0 <= ix < 64 and MANTLE_TOP <= iy < MANTLE_BOT:
                # Color based on depth: brighter/yellower near top
                ny = (iy - MANTLE_TOP) / max(1, MANTLE_BOT - MANTLE_TOP)
                if ny < 0.3:
                    c = _lerp_color(MAGMA_BRIGHT, MANTLE_HOT, ny / 0.3)
                else:
                    c = _lerp_color(MANTLE_HOT, DEEP_MANTLE_C, (ny - 0.3) / 0.7)
                # Brighter near ridge
                ridge_dist = abs(p[0] - RIDGE_X)
                if ridge_dist < 6:
                    boost = 1.0 + (6 - ridge_dist) * 0.08
                    c = (min(255, int(c[0] * boost)),
                         min(255, int(c[1] * boost)),
                         min(255, int(c[2] * boost)))
                set_pixel(ix, iy, c)

    # ── magma at ridge ──────────────────────────────────────────

    def _draw_magma(self, d, set_pixel):
        for mp in self.magma_particles:
            ix, iy = int(mp[0]), int(mp[1])
            heat = mp[2]
            if 0 <= ix < 64 and 0 <= iy < 64:
                c = _lerp_color(MAGMA_MED, MAGMA_BRIGHT, heat)
                set_pixel(ix, iy, c)
                # Glow: dim adjacent pixels
                if heat > 0.6:
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        gx, gy = ix + dx, iy + dy
                        if 0 <= gx < 64 and 0 <= gy < 64:
                            cur = d.get_pixel(gx, gy)
                            glow = (
                                min(255, cur[0] + int(40 * heat)),
                                min(255, cur[1] + int(20 * heat)),
                                min(255, cur[2] + int(5 * heat)),
                            )
                            set_pixel(gx, gy, glow)

    # ── eruption particles ──────────────────────────────────────

    def _draw_eruption(self, d, set_pixel):
        for ep in self.eruption_particles:
            ix, iy = int(ep[0]), int(ep[1])
            life = ep[4]
            if 0 <= ix < 64 and 0 <= iy < 64:
                if life > 0.8:
                    c = MAGMA_BRIGHT
                elif life > 0.4:
                    c = MAGMA_MED
                else:
                    c = (180, 50, 20)
                set_pixel(ix, iy, c)

    # ── dehydration particles ───────────────────────────────────

    def _draw_dehydration(self, d, set_pixel):
        for dp in self.dehydration_particles:
            ix, iy = int(dp[0]), int(dp[1])
            if 0 <= ix < 64 and 0 <= iy < 64:
                life = dp[4]
                alpha = min(1.0, life)
                c = (int(120 * alpha), int(160 * alpha), int(200 * alpha))
                set_pixel(ix, iy, c)

    # ── earthquake flash ────────────────────────────────────────

    def _draw_quake_flash(self, d, set_pixel):
        if self.quake_flash <= 0:
            return
        alpha = min(1.0, self.quake_flash / 0.1)
        # Flash at transform fault line
        for y in range(max(0, self.surface_y[TRANSFORM_X] - 2), self.crust_bot[TRANSFORM_X] + 2):
            for dx in range(-1, 2):
                px = TRANSFORM_X + dx
                if 0 <= px < 64 and 0 <= y < 64:
                    c = (int(255 * alpha), int(255 * alpha), int(200 * alpha))
                    set_pixel(px, y, c)

    # ── plate motion arrows ─────────────────────────────────────

    def _draw_plate_arrows(self, d, set_pixel):
        """Draw subtle animated arrows showing plate direction on the surface."""
        phase = self.arrow_phase
        arrow_y = CRUST_TOP - 1

        # Left plate moves left (toward subduction)
        for ax in [5, 8]:
            anim = int(phase) % 3
            px = ax - anim
            if 0 <= px < 64 and 0 <= arrow_y < 64:
                set_pixel(px, arrow_y, (100, 100, 60))

        # Right plate moves right (away from ridge)
        for ax in [50, 54, 58]:
            anim = int(phase) % 3
            px = ax + anim
            if 0 <= px < 64 and 0 <= arrow_y < 64:
                set_pixel(px, arrow_y, (100, 100, 60))

        # Arrows spreading from ridge
        anim = int(phase) % 3
        # Left of ridge
        px = RIDGE_X - 2 - anim
        if 0 <= px < 64 and 0 <= arrow_y < 64:
            set_pixel(px, arrow_y, (180, 120, 40))
        # Right of ridge
        px = RIDGE_X + 2 + anim
        if 0 <= px < 64 and 0 <= arrow_y < 64:
            set_pixel(px, arrow_y, (180, 120, 40))

    # ── focus highlight ─────────────────────────────────────────

    def _draw_focus_highlight(self, d, set_pixel):
        """Draw a subtle highlight on the focused boundary."""
        mode = FOCUS_MODES[self.focus_idx]
        if mode == "ALL":
            return

        pulse = 0.5 + 0.5 * math.sin(self.time * 3.0)
        alpha = int(30 + 40 * pulse)

        if mode == "SUBDUCTION":
            # Highlight subduction zone area
            for x in range(8, 22):
                for y in range(max(0, self.surface_y[min(x, 63)] - 2), min(64, MANTLE_TOP + 10)):
                    if 0 <= x < 64 and 0 <= y < 64:
                        cur = d.get_pixel(x, y)
                        c = (min(255, cur[0] + alpha // 3),
                             min(255, cur[1] + alpha),
                             min(255, cur[2] + alpha))
                        set_pixel(x, y, c)
        elif mode == "DIVERGENT":
            for x in range(RIDGE_X - 5, RIDGE_X + 6):
                for y in range(max(0, CRUST_TOP - 2), min(64, MANTLE_TOP + 10)):
                    if 0 <= x < 64 and 0 <= y < 64:
                        cur = d.get_pixel(x, y)
                        c = (min(255, cur[0] + alpha),
                             min(255, cur[1] + alpha // 2),
                             min(255, cur[2]))
                        set_pixel(x, y, c)
        elif mode == "TRANSFORM":
            for x in range(TRANSFORM_X - 3, TRANSFORM_X + 4):
                for y in range(max(0, self.surface_y[min(x, 63)] - 2),
                               min(64, self.crust_bot[min(x, 63)] + 2)):
                    if 0 <= x < 64 and 0 <= y < 64:
                        cur = d.get_pixel(x, y)
                        c = (min(255, cur[0] + alpha),
                             min(255, cur[1] + alpha),
                             min(255, cur[2]))
                        set_pixel(x, y, c)

    # ── labels ──────────────────────────────────────────────────

    def _draw_labels(self, d):
        """Draw boundary labels in the info area at the bottom."""
        if self.show_notes:
            return  # notes override labels

        labels = [
            ("SUB", 4, (80, 200, 220)),
            ("TRN", 28, (255, 255, 80)),
            ("DIV", 42, (255, 160, 40)),
        ]

        mode = FOCUS_MODES[self.focus_idx]
        for text, x, color in labels:
            # Dim if not the focused mode (unless ALL)
            if mode == "ALL":
                c = color
            elif (mode == "SUBDUCTION" and text == "SUB") or \
                 (mode == "TRANSFORM" and text == "TRN") or \
                 (mode == "DIVERGENT" and text == "DIV"):
                c = color
            else:
                c = (color[0] // 3, color[1] // 3, color[2] // 3)
            d.draw_text_small(x, INFO_TOP + 1, text, c)
