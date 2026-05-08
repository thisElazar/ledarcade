"""
Tectonic - Three Plate Boundary Cross-Sections
================================================
Three full-screen textbook-style side-view cross-sections on a 64x64
LED matrix, one for each tectonic boundary type:

  1. DIVERGENT  -- rift valley, magma rising, plates pulling apart
  2. CONVERGENT -- subduction zone, oceanic trench, volcanic arc
  3. TRANSFORM  -- strike-slip fault, earthquake events, offset terrain

Auto-cycles every 10 seconds with a 0.5s fade transition.

Controls:
  Left/Right     - Cycle scenes manually (pauses auto-cycle 15s)
  Up/Down        - Adjust animation speed
  Action button  - Trigger event (eruption / earthquake / magma burst)
  Both held      - Toggle scrolling notes
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE

# ── Helpers ────────────────────────────────────────────────────────

def _lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


def _scale_color(c, s):
    return (
        min(255, max(0, int(c[0] * s))),
        min(255, max(0, int(c[1] * s))),
        min(255, max(0, int(c[2] * s))),
    )


def _add_color(c1, c2):
    return (
        min(255, c1[0] + c2[0]),
        min(255, c1[1] + c2[1]),
        min(255, c1[2] + c2[2]),
    )


# ── Scene constants ────────────────────────────────────────────────

SCENES = ["DIVERGENT", "CONVERGENT", "TRANSFORM", "HOTSPOT", "TSUNAMI", "MOUNTAIN"]
SCENE_DURATION = 10.0          # seconds per scene before auto-cycle
FADE_DURATION = 0.5            # fade transition
MANUAL_PAUSE = 15.0            # seconds to pause auto-cycle after manual input

# Vertical zones shared across scenes
LABEL_Y = 59                   # y for label text
MANTLE_BOTTOM = 52             # below this is deep mantle
DEEP_BOTTOM = 57               # below this is label area

# Mantle gradient colors
MANTLE_TOP_C = (200, 80, 20)   # warm orange near crust
MANTLE_MID_C = (140, 30, 20)   # dark red mid-depth
MANTLE_BOT_C = (80, 15, 15)    # very dark near bottom
DEEP_C = (40, 10, 10)          # deep mantle / lower mantle


# ── Main visual class ─────────────────────────────────────────────

class Tectonic(Visual):
    name = "TECTONIC"
    description = "Plate dynamics"
    category = "science_macro"

    def __init__(self, display: Display):
        super().__init__(display)

    # ── reset ──────────────────────────────────────────────────────

    def reset(self):
        self.time = 0.0

        # Scene state
        self.scene_idx = 0
        self.scene_timer = SCENE_DURATION
        self.auto_cycle = True
        self.pause_timer = 0.0
        self.fade_timer = 0.0          # >0 during transition
        self.fade_from = 0             # scene fading out
        self.fade_to = 0               # scene fading in
        self.fading = False

        # Speed multiplier
        self.sim_speed = 1.0

        # Overlay
        self.overlay_text = ''
        self.overlay_timer = 0.0

        # Scrolling notes
        self.show_notes = False
        self.notes_scroll_offset = 0.0
        self.notes_segments = []
        self.notes_scroll_len = 1
        self._both_pressed_prev = False

        # Per-scene particle systems
        self._div_particles = []       # divergent magma
        self._div_convection = []      # divergent convection
        self._con_slab_particles = []  # convergent slab flow
        self._con_eruption = []        # convergent eruption
        self._con_eruption_timer = 0.0
        self._trn_quake_flash = 0.0    # transform earthquake flash
        self._trn_quake_timer = 0.0
        self._trn_ripple = []          # transform ripple particles
        self._trn_offset_shift = 0.0   # animated offset for plates

        # Hotspot
        self._hot_plume = []
        self._hot_plate_offset = 0.0
        self._hot_eruption = []

        # Tsunami
        self._tsu_wave_x = -5.0
        self._tsu_active = False
        self._tsu_timer = 2.0
        self._tsu_rupture_flash = 0.0

        # Mountain
        self._mtn_compression = 0.0
        self._mtn_fold_heights = [0.0] * 20

        self._init_scene(self.scene_idx)
        self._build_notes_segments()
        self._show_overlay("DIVERGENT")

    # ── scene init ─────────────────────────────────────────────────

    def _init_scene(self, idx):
        """Initialize particles for the given scene."""
        if idx == 0:
            self._init_divergent()
        elif idx == 1:
            self._init_convergent()
        elif idx == 2:
            self._init_transform()
        elif idx == 3:
            self._init_hotspot()
        elif idx == 4:
            self._init_tsunami()
        elif idx == 5:
            self._init_mountain()

    def _init_divergent(self):
        """Magma particles rising through rift, convection particles."""
        self._div_particles = []
        for _ in range(35):
            x = 32 + random.uniform(-3, 3)
            y = random.uniform(20, 52)
            heat = random.uniform(0.3, 1.0)
            self._div_particles.append([x, y, heat])
        self._div_convection = []
        for _ in range(30):
            x = random.uniform(2, 62)
            y = random.uniform(22, 50)
            self._div_convection.append([x, y])

    def _init_convergent(self):
        """Slab flow particles, eruption timer."""
        self._con_slab_particles = []
        for _ in range(20):
            t = random.uniform(0.0, 1.0)
            x = 30 - t * 12
            y = 14 + t * 30
            self._con_slab_particles.append([x, y, t])
        self._con_eruption = []
        self._con_eruption_timer = random.uniform(5.0, 8.0)

    def _init_transform(self):
        """Earthquake timer, ripple particles."""
        self._trn_quake_flash = 0.0
        self._trn_quake_timer = random.uniform(5.0, 10.0)
        self._trn_ripple = []
        self._trn_offset_shift = 0.0

    def _init_hotspot(self):
        self._hot_plume = []
        for _ in range(25):
            x = 24 + random.uniform(-3, 3)
            y = random.uniform(25, 52)
            heat = random.uniform(0.4, 1.0)
            self._hot_plume.append([x, y, heat])
        self._hot_plate_offset = 0.0
        self._hot_eruption = []

    def _init_tsunami(self):
        self._tsu_wave_x = -5.0
        self._tsu_active = False
        self._tsu_timer = 2.0
        self._tsu_rupture_flash = 0.0

    def _init_mountain(self):
        self._mtn_compression = 0.0
        self._mtn_fold_heights = [0.0] * 20

    # ── notes ──────────────────────────────────────────────────────

    def _build_notes_segments(self):
        sep = '  --  '
        sep_color = (60, 55, 50)
        notes = [
            ("PLATE TECTONICS", (255, 255, 255)),
            ("DIVERGENT: RIFT", (255, 160, 40)),
            ("CONVERGENT: TRENCH", (80, 200, 220)),
            ("TRANSFORM: FAULT", (255, 255, 80)),
            ("HOTSPOT: PLUME", (255, 100, 50)),
            ("TSUNAMI: WAVE", (80, 180, 255)),
            ("MOUNTAIN: OROGENY", (180, 200, 140)),
            ("WEGENER 1912", (255, 255, 255)),
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

    # ── overlay ────────────────────────────────────────────────────

    def _show_overlay(self, text):
        self.overlay_text = text
        self.overlay_timer = 2.0

    def _draw_overlay(self):
        if self.overlay_timer <= 0:
            return
        alpha = min(1.0, self.overlay_timer / 0.5)
        c = (int(255 * alpha), int(255 * alpha), int(255 * alpha))
        self.display.draw_text_small(2, 2, self.overlay_text, c)

    # ── input ──────────────────────────────────────────────────────

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Left/Right: cycle scenes manually
        if input_state.left_pressed:
            self._manual_scene((self.scene_idx - 1) % len(SCENES))
            consumed = True
        if input_state.right_pressed:
            self._manual_scene((self.scene_idx + 1) % len(SCENES))
            consumed = True

        # Up/Down: adjust speed
        if input_state.up_pressed:
            self.sim_speed = min(4.0, self.sim_speed + 0.25)
            spd = f"{self.sim_speed:.1f}" if self.sim_speed != int(self.sim_speed) else f"{int(self.sim_speed)}"
            self._show_overlay(f"SPEED {spd}X")
            consumed = True
        if input_state.down_pressed:
            self.sim_speed = max(0.25, self.sim_speed - 0.25)
            spd = f"{self.sim_speed:.1f}" if self.sim_speed != int(self.sim_speed) else f"{int(self.sim_speed)}"
            self._show_overlay(f"SPEED {spd}X")
            consumed = True

        # Both buttons: toggle notes
        both = (input_state.action_l_held or input_state.action_l) and \
               (input_state.action_r_held or input_state.action_r)
        if both and not self._both_pressed_prev:
            self.show_notes = not self.show_notes
            self.notes_scroll_offset = 0.0
            consumed = True
        elif (input_state.action_l or input_state.action_r) and not both:
            if not self._both_pressed_prev:
                self._trigger_event()
                consumed = True
        self._both_pressed_prev = both

        return consumed

    def _manual_scene(self, idx):
        """Switch to scene idx, pause auto-cycle."""
        if not self.fading:
            self._start_fade(idx)
        self.auto_cycle = False
        self.pause_timer = MANUAL_PAUSE

    def _start_fade(self, to_idx):
        """Begin fade transition to a new scene."""
        self.fading = True
        self.fade_timer = FADE_DURATION
        self.fade_from = self.scene_idx
        self.fade_to = to_idx
        self._init_scene(to_idx)
        self._show_overlay(SCENES[to_idx])

    def _trigger_event(self):
        """Trigger a scene-specific event."""
        if self.scene_idx == 0:
            # Divergent: magma burst
            for mp in self._div_particles:
                mp[2] = 1.0
            # Extra burst particles
            for _ in range(8):
                x = 32 + random.uniform(-2, 2)
                y = random.uniform(30, 48)
                self._div_particles.append([x, y, 1.0])
        elif self.scene_idx == 1:
            # Convergent: eruption
            self._start_eruption()
        elif self.scene_idx == 2:
            # Transform: earthquake
            self._trn_quake_flash = 0.3
            self._spawn_ripple()
        elif self.scene_idx == 3:
            for mp in self._hot_plume:
                mp[2] = 1.0
            for _ in range(6):
                self._hot_eruption.append([24.0, 8.0, random.uniform(-8, 8),
                                           random.uniform(-15, -25), 1.0])
        elif self.scene_idx == 4:
            self._tsu_active = True
            self._tsu_wave_x = 20.0
            self._tsu_rupture_flash = 0.3

    # ── update ─────────────────────────────────────────────────────

    def update(self, dt: float):
        self.time += dt
        sdt = dt * self.sim_speed

        # Overlay
        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

        # Notes scroll
        if self.show_notes:
            self.notes_scroll_offset += dt * 18

        # Fade transition
        if self.fading:
            self.fade_timer -= dt
            if self.fade_timer <= 0:
                self.fading = False
                self.scene_idx = self.fade_to
                self.scene_timer = SCENE_DURATION

        # Auto-cycle
        if not self.auto_cycle:
            self.pause_timer -= dt
            if self.pause_timer <= 0:
                self.auto_cycle = True
        if self.auto_cycle and not self.fading:
            self.scene_timer -= dt
            if self.scene_timer <= 0:
                next_idx = (self.scene_idx + 1) % len(SCENES)
                self._start_fade(next_idx)

        # Update active scene(s)
        active = self.scene_idx
        if self.fading:
            self._update_scene(self.fade_from, sdt)
            self._update_scene(self.fade_to, sdt)
        else:
            self._update_scene(active, sdt)

    def _update_scene(self, idx, dt):
        if idx == 0:
            self._update_divergent(dt)
        elif idx == 1:
            self._update_convergent(dt)
        elif idx == 2:
            self._update_transform(dt)
        elif idx == 3:
            self._update_hotspot(dt)
        elif idx == 4:
            self._update_tsunami(dt)
        elif idx == 5:
            self._update_mountain(dt)

    # ── divergent update ───────────────────────────────────────────

    def _update_divergent(self, dt):
        """Update magma and convection particles."""
        # Magma rises through rift
        alive = []
        for mp in self._div_particles:
            mp[1] -= dt * random.uniform(2.5, 4.5)  # rise
            mp[0] += random.uniform(-0.15, 0.15)     # wobble
            mp[2] -= dt * 0.06                        # cool

            # Respawn at bottom when cooled or reached crust
            if mp[1] < 12 or mp[2] <= 0:
                mp[0] = 32 + random.uniform(-3, 3)
                mp[1] = random.uniform(40, 52)
                mp[2] = random.uniform(0.5, 1.0)
            alive.append(mp)
        # Cap particle count
        self._div_particles = alive[:45]

        # Convection: drift outward from center at shallow depth, inward at deep
        for cp in self._div_convection:
            depth_t = (cp[1] - 20) / 32.0  # 0 at top, 1 at bottom
            # Horizontal: outward at top, inward at bottom
            if cp[0] < 32:
                vx = -1.5 * (1.0 - depth_t) + 1.0 * depth_t
            else:
                vx = 1.5 * (1.0 - depth_t) - 1.0 * depth_t
            # Vertical: rise in center, sink at edges
            dist_center = abs(cp[0] - 32)
            if dist_center < 8:
                vy = -1.0
            else:
                vy = 0.5
            cp[0] += vx * dt
            cp[1] += vy * dt
            # Wrap
            if cp[1] < 20:
                cp[1] = 50
            elif cp[1] > 52:
                cp[1] = 22
            if cp[0] < 2:
                cp[0] = 62
            elif cp[0] > 62:
                cp[0] = 2

    # ── convergent update ──────────────────────────────────────────

    def _update_convergent(self, dt):
        """Update slab particles, eruption."""
        # Slab flow: particles move along the descending slab
        for sp in self._con_slab_particles:
            sp[2] += dt * 0.05  # advance along slab parameter
            if sp[2] > 1.0:
                sp[2] = 0.0
            t = sp[2]
            sp[0] = 30 - t * 12
            sp[1] = 14 + t * 30

        # Eruption timer
        self._con_eruption_timer -= dt
        if self._con_eruption_timer <= 0:
            self._start_eruption()
            self._con_eruption_timer = random.uniform(5.0, 8.0)

        # Update eruption particles
        alive = []
        for ep in self._con_eruption:
            ep[0] += ep[2] * dt
            ep[1] += ep[3] * dt
            ep[3] += 10.0 * dt  # gravity
            ep[4] -= dt
            if ep[4] > 0:
                alive.append(ep)
        self._con_eruption = alive

    def _start_eruption(self):
        """Spawn eruption particles from volcanic arc."""
        vx = random.randint(37, 40)
        vy = 8  # top of mountain area
        for _ in range(10):
            self._con_eruption.append([
                float(vx) + random.uniform(-0.5, 0.5),
                float(vy),
                random.uniform(-1.0, 1.0),    # vx
                random.uniform(-7.0, -3.0),    # vy (upward)
                random.uniform(0.8, 1.5),       # lifetime
            ])

    # ── transform update ───────────────────────────────────────────

    def _update_transform(self, dt):
        """Update earthquake timer, flash, ripple."""
        self._trn_quake_timer -= dt
        if self._trn_quake_timer <= 0:
            self._trn_quake_flash = 0.3
            self._spawn_ripple()
            self._trn_quake_timer = random.uniform(5.0, 10.0)

        if self._trn_quake_flash > 0:
            self._trn_quake_flash = max(0, self._trn_quake_flash - dt)

        # Update ripple particles
        alive = []
        for rp in self._trn_ripple:
            rp[0] += rp[2] * dt  # expand x
            rp[1] += rp[3] * dt  # expand y
            rp[4] -= dt           # lifetime
            if rp[4] > 0:
                alive.append(rp)
        self._trn_ripple = alive

        # Slowly shift offset to show plate motion
        self._trn_offset_shift += dt * 0.08

    def _spawn_ripple(self):
        """Spawn ripple particles from the fault line."""
        fx = 32
        fy = random.randint(12, 22)
        for _ in range(12):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(6, 18)
            self._trn_ripple.append([
                float(fx), float(fy),
                math.cos(angle) * speed,
                math.sin(angle) * speed,
                random.uniform(0.3, 0.7),
            ])

    # ── draw ───────────────────────────────────────────────────────

    def draw(self):
        d = self.display
        d.clear()

        if self.fading:
            # During fade: draw old scene dimmed, new scene brightening
            progress = 1.0 - (self.fade_timer / FADE_DURATION)  # 0→1
            self._draw_scene(self.fade_from, 1.0 - progress)
            self._draw_scene(self.fade_to, progress)
        else:
            self._draw_scene(self.scene_idx, 1.0)

        if self.show_notes:
            self._draw_notes()
        self._draw_overlay()

    def _draw_scene(self, idx, brightness):
        """Draw a complete scene at given brightness (0-1)."""
        if brightness <= 0.01:
            return
        if idx == 0:
            self._draw_divergent(brightness)
        elif idx == 1:
            self._draw_convergent(brightness)
        elif idx == 2:
            self._draw_transform(brightness)
        elif idx == 3:
            self._draw_hotspot(brightness)
        elif idx == 4:
            self._draw_tsunami(brightness)
        elif idx == 5:
            self._draw_mountain(brightness)

    # ── shared drawing helpers ─────────────────────────────────────

    def _draw_mantle_bg(self, crust_bottom_y, brightness):
        """Draw mantle gradient from crust_bottom_y down to DEEP_BOTTOM."""
        d = self.display
        for y in range(crust_bottom_y, DEEP_BOTTOM + 1):
            if y < MANTLE_BOTTOM:
                t = (y - crust_bottom_y) / max(1, MANTLE_BOTTOM - crust_bottom_y)
                if t < 0.5:
                    c = _lerp_color(MANTLE_TOP_C, MANTLE_MID_C, t * 2)
                else:
                    c = _lerp_color(MANTLE_MID_C, MANTLE_BOT_C, (t - 0.5) * 2)
            else:
                c = DEEP_C
            c = _scale_color(c, brightness * 0.35)
            for x in range(64):
                cur = d.get_pixel(x, y)
                d.set_pixel(x, y, _add_color(cur, c))

    def _draw_label(self, text, brightness):
        """Draw scene label centered at bottom."""
        d = self.display
        text_w = len(text) * 4
        x = max(0, (64 - text_w) // 2)
        a = brightness
        c = (int(255 * a), int(255 * a), int(255 * a))
        d.draw_text_small(x, LABEL_Y, text, c)

    def _draw_arrow_right(self, x, y, brightness):
        """Draw a small right-pointing arrow (5px wide)."""
        d = self.display
        c = _scale_color((255, 255, 200), brightness)
        # Shaft: 3px horizontal line
        for dx in range(3):
            px = x + dx
            if 0 <= px < 64 and 0 <= y < 64:
                d.set_pixel(px, y, c)
        # Chevron
        if 0 <= x + 3 < 64:
            if 0 <= y - 1 < 64:
                d.set_pixel(x + 3, y - 1, c)
            if 0 <= y < 64:
                d.set_pixel(x + 3, y, c)
            if 0 <= y + 1 < 64:
                d.set_pixel(x + 3, y + 1, c)
        if 0 <= x + 4 < 64 and 0 <= y < 64:
            d.set_pixel(x + 4, y, c)

    def _draw_arrow_left(self, x, y, brightness):
        """Draw a small left-pointing arrow (5px wide). x is the leftmost pixel."""
        d = self.display
        c = _scale_color((255, 255, 200), brightness)
        # Tip
        if 0 <= x < 64 and 0 <= y < 64:
            d.set_pixel(x, y, c)
        # Chevron
        if 0 <= x + 1 < 64:
            if 0 <= y - 1 < 64:
                d.set_pixel(x + 1, y - 1, c)
            if 0 <= y < 64:
                d.set_pixel(x + 1, y, c)
            if 0 <= y + 1 < 64:
                d.set_pixel(x + 1, y + 1, c)
        # Shaft
        for dx in range(2, 5):
            px = x + dx
            if 0 <= px < 64 and 0 <= y < 64:
                d.set_pixel(px, y, c)

    # ================================================================
    #  SCENE 1: DIVERGENT (Rift Valley)
    # ================================================================

    def _draw_divergent(self, br):
        d = self.display
        t = self.time

        # -- Crust: two plates with a gap in the center --
        # Left plate: x=0..27, right plate: x=36..63
        # Gap: x=28..35 (rift valley)
        crust_top = 10
        crust_bot = 18

        # Surface terrain on top of plates (sparse green/brown)
        for x in range(64):
            in_gap = 28 <= x <= 35
            if in_gap:
                continue

            for y in range(crust_top, crust_bot):
                # Layered texture: top rows darker (soil), lower rows lighter (rock)
                layer_t = (y - crust_top) / max(1, crust_bot - crust_top - 1)
                if layer_t < 0.25:
                    base = (110, 85, 50)    # dark soil
                elif layer_t < 0.5:
                    base = (140, 110, 65)   # lighter soil
                elif layer_t < 0.75:
                    base = (160, 130, 80)   # tan rock
                else:
                    base = (130, 105, 65)   # deeper rock
                c = _scale_color(base, br)
                cur = d.get_pixel(x, y)
                d.set_pixel(x, y, _add_color(cur, c))

            # Sparse surface vegetation
            if x % 5 == 2 or x % 7 == 0:
                py = crust_top - 1
                if 0 <= py < 64 and not in_gap:
                    green = _scale_color((40, 80, 30), br)
                    cur = d.get_pixel(x, py)
                    d.set_pixel(x, py, _add_color(cur, green))

        # -- Rift valley walls (sloping sides) --
        for x in range(28, 36):
            # Valley walls slope deeper toward center
            dist_from_edge = min(x - 28, 35 - x)
            wall_top = crust_top + 1 + dist_from_edge // 2
            wall_bot = crust_bot
            # Draw shadow/rock on the valley sides
            for y in range(wall_top, wall_bot):
                layer_t = (y - wall_top) / max(1, wall_bot - wall_top - 1)
                base = _lerp_color((80, 60, 40), (60, 40, 25), layer_t)
                c = _scale_color(base, br)
                cur = d.get_pixel(x, y)
                d.set_pixel(x, y, _add_color(cur, c))

        # -- Mantle below --
        self._draw_mantle_bg(crust_bot, br)

        # Brighter mantle near rift center (magma glow)
        for y in range(crust_bot, MANTLE_BOTTOM):
            for x in range(26, 38):
                dist = abs(x - 32)
                if dist < 6:
                    glow_strength = (6 - dist) / 6.0 * 0.3
                    depth_fade = 1.0 - (y - crust_bot) / max(1, MANTLE_BOTTOM - crust_bot)
                    glow = _scale_color((255, 140, 20),
                                        br * glow_strength * (0.3 + 0.7 * depth_fade))
                    cur = d.get_pixel(x, y)
                    d.set_pixel(x, y, _add_color(cur, glow))

        # -- Convection particles --
        for cp in self._div_convection:
            ix, iy = int(cp[0]), int(cp[1])
            if 0 <= ix < 64 and 20 <= iy < 52:
                depth_t = (iy - 20) / 32.0
                base = _lerp_color((220, 100, 30), (100, 25, 15), depth_t)
                c = _scale_color(base, br * 0.7)
                cur = d.get_pixel(ix, iy)
                d.set_pixel(ix, iy, _add_color(cur, c))

        # -- Magma particles rising through rift --
        for mp in self._div_particles:
            ix, iy = int(mp[0]), int(mp[1])
            heat = mp[2]
            if 0 <= ix < 64 and 0 <= iy < 64:
                # Color shift: hot=yellow, cooling=orange→red→dark
                if heat > 0.7:
                    base = _lerp_color((255, 160, 20), (255, 230, 60), (heat - 0.7) / 0.3)
                elif heat > 0.4:
                    base = _lerp_color((220, 80, 10), (255, 160, 20), (heat - 0.4) / 0.3)
                else:
                    base = _lerp_color((120, 25, 10), (220, 80, 10), heat / 0.4)
                c = _scale_color(base, br)
                cur = d.get_pixel(ix, iy)
                d.set_pixel(ix, iy, _add_color(cur, c))
                # Glow for hot particles
                if heat > 0.6:
                    for dx2, dy2 in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        gx, gy = ix + dx2, iy + dy2
                        if 0 <= gx < 64 and 0 <= gy < 64:
                            glow = _scale_color((60, 30, 5), br * heat)
                            cur2 = d.get_pixel(gx, gy)
                            d.set_pixel(gx, gy, _add_color(cur2, glow))

        # -- Plate arrows --
        # Left plate: arrow pointing left
        self._draw_arrow_left(8, crust_top + 3, br)
        self._draw_arrow_left(18, crust_top + 3, br)
        # Right plate: arrow pointing right
        self._draw_arrow_right(42, crust_top + 3, br)
        self._draw_arrow_right(52, crust_top + 3, br)

        # -- Label --
        self._draw_label("DIVERGENT", br)

    # ================================================================
    #  SCENE 2: CONVERGENT (Subduction / Trench)
    # ================================================================

    def _draw_convergent(self, br):
        d = self.display
        t = self.time

        # -- Ocean over left (oceanic) side --
        # Oceanic plate: x=0..29, thinner, darker
        # Continental plate: x=30..63, thicker, lighter, with mountains

        ocean_surface = 6
        oceanic_crust_top = 10
        oceanic_crust_bot = 14
        cont_crust_top = 8
        cont_crust_bot = 18

        # Ocean water with wave animation
        for x in range(0, 32):
            wave = math.sin(t * 2.0 + x * 0.4) * 0.8
            water_top = max(0, int(ocean_surface + wave))
            water_bot = oceanic_crust_top
            # Trench dip near boundary
            if 26 <= x <= 30:
                water_bot = oceanic_crust_top + (x - 26)
            for y in range(water_top, water_bot):
                depth_t = (y - water_top) / max(1, water_bot - water_top)
                base = _lerp_color((40, 80, 180), (20, 40, 120), depth_t)
                c = _scale_color(base, br)
                cur = d.get_pixel(x, y)
                d.set_pixel(x, y, _add_color(cur, c))

        # Ocean surface shimmer
        for x in range(0, 32):
            wave = math.sin(t * 2.0 + x * 0.4) * 0.8
            sy = max(0, int(ocean_surface + wave))
            if 0 <= sy < 64:
                shimmer = _scale_color((70, 120, 220), br)
                cur = d.get_pixel(x, sy)
                d.set_pixel(x, sy, _add_color(cur, shimmer))

        # -- Oceanic crust (thin, gray-blue) --
        for x in range(0, 30):
            top = oceanic_crust_top
            bot = oceanic_crust_bot
            # Near boundary, crust bends down (subduction)
            if x >= 24:
                bend = (x - 24) * 1.5
                top = int(oceanic_crust_top + bend)
                bot = int(oceanic_crust_bot + bend)
            for y in range(top, bot):
                if y >= 64:
                    break
                layer_t = (y - top) / max(1, bot - top - 1)
                base = _lerp_color((70, 80, 95), (50, 60, 75), layer_t)
                c = _scale_color(base, br)
                cur = d.get_pixel(x, y)
                d.set_pixel(x, y, _add_color(cur, c))

        # -- Descending slab (diagonal into mantle) --
        for i in range(35):
            sx = 30 - int(i * 0.35)
            sy = 14 + int(i * 1.0)
            if 0 <= sx < 64 and 0 <= sy < 55:
                slab_c = _scale_color((80, 90, 100), br)
                cur = d.get_pixel(sx, sy)
                d.set_pixel(sx, sy, _add_color(cur, slab_c))
                if sx + 1 < 64:
                    slab_c2 = _scale_color((65, 75, 85), br)
                    cur2 = d.get_pixel(sx + 1, sy)
                    d.set_pixel(sx + 1, sy, _add_color(cur2, slab_c2))

        # -- Continental crust (thick, tan/brown, with mountains) --
        for x in range(30, 64):
            top = cont_crust_top
            bot = cont_crust_bot

            # Mountains near boundary (x=35-42)
            mountain_height = 0
            if 34 <= x <= 42:
                dist_peak = abs(x - 38)
                mountain_height = max(0, 5 - dist_peak)
                top = cont_crust_top - mountain_height

            for y in range(top, bot):
                layer_t = (y - top) / max(1, bot - top - 1)
                if y < cont_crust_top:
                    # Mountain portion
                    base = _lerp_color((170, 150, 100), (150, 125, 80), layer_t)
                else:
                    base = _lerp_color((160, 130, 80), (120, 100, 60), layer_t)
                c = _scale_color(base, br)
                cur = d.get_pixel(x, y)
                d.set_pixel(x, y, _add_color(cur, c))

            # Snow caps on tallest peaks
            if mountain_height >= 4 and 0 <= top < 64:
                snow = _scale_color((220, 220, 235), br)
                cur = d.get_pixel(x, top)
                d.set_pixel(x, top, _add_color(cur, snow))

        # -- Mantle below --
        mantle_top = max(cont_crust_bot, oceanic_crust_bot)
        self._draw_mantle_bg(mantle_top, br)

        # -- Slab flow particles --
        for sp in self._con_slab_particles:
            ix, iy = int(sp[0]), int(sp[1])
            if 0 <= ix < 64 and 0 <= iy < 55:
                flow_c = _scale_color((160, 60, 20), br * 0.8)
                cur = d.get_pixel(ix, iy)
                d.set_pixel(ix, iy, _add_color(cur, flow_c))

        # -- Eruption particles (volcanic arc) --
        for ep in self._con_eruption:
            ix, iy = int(ep[0]), int(ep[1])
            life = ep[4]
            if 0 <= ix < 64 and 0 <= iy < 64:
                if life > 0.8:
                    base = (255, 220, 60)
                elif life > 0.4:
                    base = (255, 120, 20)
                else:
                    base = (180, 50, 20)
                c = _scale_color(base, br)
                cur = d.get_pixel(ix, iy)
                d.set_pixel(ix, iy, _add_color(cur, c))

        # -- Plate arrows --
        # Oceanic plate: arrow pointing right
        self._draw_arrow_right(6, oceanic_crust_top + 2, br)
        self._draw_arrow_right(15, oceanic_crust_top + 2, br)
        # Continental plate: arrow pointing left
        self._draw_arrow_left(46, cont_crust_top + 4, br)
        self._draw_arrow_left(54, cont_crust_top + 4, br)

        # -- Label --
        self._draw_label("CONVERGENT", br)

    # ================================================================
    #  SCENE 3: TRANSFORM (Strike-Slip Fault)
    # ================================================================

    def _draw_transform(self, br):
        d = self.display
        t = self.time

        # Fault line at x=32 (1-2px wide dark crack)
        crust_top = 10
        crust_bot = 22
        fault_x = 32

        # Jitter during earthquake
        jitter = 0
        if self._trn_quake_flash > 0.1:
            jitter = random.choice([-1, 0, 1])

        # -- Two crust plates side by side --
        # Left plate: x=0..31, right plate: x=33..63
        # Offset terrain features to show strike-slip displacement

        # Animated offset that slowly grows
        offset = int(self._trn_offset_shift * 2) % 4

        for x in range(64):
            if x == fault_x or x == fault_x - 1:
                # Fault line: dark crack
                for y in range(crust_top - 1, crust_bot + 1):
                    if 0 <= y < 64:
                        crack_c = _scale_color((25, 20, 15), br)
                        cur = d.get_pixel(x, y)
                        d.set_pixel(x, y, _add_color(cur, crack_c))
                continue

            on_left = x < fault_x - 1

            # Apply jitter near fault
            draw_x = x
            if jitter != 0 and abs(x - fault_x) < 4:
                draw_x = max(0, min(63, x + jitter))

            for y in range(crust_top, crust_bot):
                layer_t = (y - crust_top) / max(1, crust_bot - crust_top - 1)
                if layer_t < 0.2:
                    base = (120, 95, 60)
                elif layer_t < 0.5:
                    base = (150, 120, 75)
                elif layer_t < 0.8:
                    base = (140, 110, 70)
                else:
                    base = (110, 90, 55)
                c = _scale_color(base, br)
                cur = d.get_pixel(draw_x, y)
                d.set_pixel(draw_x, y, _add_color(cur, c))

            # Horizontal stripe features (offset to show displacement)
            # Left plate stripes at one y, right plate at different y
            for stripe_base_y in [crust_top + 3, crust_top + 7]:
                if on_left:
                    sy = stripe_base_y + offset
                else:
                    sy = stripe_base_y - offset + 2  # visibly offset
                if crust_top <= sy < crust_bot and 0 <= draw_x < 64:
                    stripe_c = _scale_color((90, 70, 45), br)
                    cur = d.get_pixel(draw_x, sy)
                    d.set_pixel(draw_x, sy, _add_color(cur, stripe_c))

        # Surface features: sparse brown terrain, slightly different elevation
        for x in range(64):
            if x == fault_x or x == fault_x - 1:
                continue
            on_left = x < fault_x - 1
            surface_y = crust_top - 1
            if on_left:
                surface_y = crust_top - 2 if x % 6 < 3 else crust_top - 1
            else:
                surface_y = crust_top - 1 if x % 6 < 3 else crust_top - 2
            if 0 <= surface_y < 64:
                terrain_c = _scale_color((80, 65, 40), br)
                cur = d.get_pixel(x, surface_y)
                d.set_pixel(x, surface_y, _add_color(cur, terrain_c))

        # -- Mantle below (quiet, no significant flow) --
        self._draw_mantle_bg(crust_bot, br)

        # -- Earthquake flash at fault line --
        if self._trn_quake_flash > 0:
            flash_alpha = min(1.0, self._trn_quake_flash / 0.15)
            for y in range(crust_top - 2, crust_bot + 3):
                for dx in range(-2, 3):
                    px = fault_x + dx
                    if 0 <= px < 64 and 0 <= y < 64:
                        dist = abs(dx)
                        intensity = flash_alpha * (1.0 - dist * 0.3)
                        if intensity > 0:
                            flash_c = _scale_color((255, 255, 200),
                                                   br * intensity)
                            cur = d.get_pixel(px, y)
                            d.set_pixel(px, y, _add_color(cur, flash_c))

        # -- Ripple particles --
        for rp in self._trn_ripple:
            ix, iy = int(rp[0]), int(rp[1])
            life = rp[4]
            if 0 <= ix < 64 and 0 <= iy < 64 and life > 0:
                alpha = min(1.0, life / 0.3)
                rip_c = _scale_color((255, 255, 180), br * alpha * 0.6)
                cur = d.get_pixel(ix, iy)
                d.set_pixel(ix, iy, _add_color(cur, rip_c))

        # -- Plate arrows (opposing horizontal) --
        # Left plate: arrow pointing left (up on screen = toward viewer)
        self._draw_arrow_left(6, crust_top + 5, br)
        self._draw_arrow_left(18, crust_top + 5, br)
        # Right plate: arrow pointing right (down on screen = away)
        self._draw_arrow_right(40, crust_top + 5, br)
        self._draw_arrow_right(52, crust_top + 5, br)

        # -- Label --
        self._draw_label("TRANSFORM", br)

    # ================================================================
    #  SCENE 4: HOTSPOT (Mantle Plume / Hawaii)
    # ================================================================

    def _update_hotspot(self, dt):
        for mp in self._hot_plume:
            mp[1] -= dt * random.uniform(2.0, 4.0)
            mp[0] += random.uniform(-0.1, 0.1)
            mp[2] -= dt * 0.05
            if mp[1] < 10 or mp[2] <= 0:
                mp[0] = 24 + random.uniform(-3, 3)
                mp[1] = random.uniform(35, 52)
                mp[2] = random.uniform(0.4, 1.0)
        self._hot_plume = self._hot_plume[:30]
        self._hot_plate_offset += dt * 1.5
        alive = []
        for ep in self._hot_eruption:
            ep[0] += ep[2] * dt
            ep[1] += ep[3] * dt
            ep[3] += 20.0 * dt
            ep[4] -= dt * 0.8
            if ep[4] > 0:
                alive.append(ep)
        self._hot_eruption = alive

    def _draw_hotspot(self, br):
        d = self.display
        crust_y = 12

        self._draw_mantle_bg(crust_y, br)

        # Plume channel glow
        for y in range(crust_y, 53):
            dist = abs(y - 30) / 20.0
            glow = max(0, 1.0 - dist) * 0.3
            for dx in range(-4, 5):
                x = 24 + dx
                if 0 <= x < 64:
                    g = glow * (1.0 - abs(dx) / 5.0)
                    cur = d.get_pixel(x, y)
                    add = _scale_color((255, 100, 20), br * g)
                    d.set_pixel(x, y, _add_color(cur, add))

        # Plume particles
        for mp in self._hot_plume:
            ix, iy = int(mp[0]), int(mp[1])
            if 0 <= ix < 64 and crust_y <= iy < 55:
                heat = mp[2]
                c = _lerp_color((80, 20, 10), (255, 200, 50), heat)
                c = _scale_color(c, br)
                d.set_pixel(ix, iy, c)

        # Crust / plate with island chain
        plate_off = self._hot_plate_offset % 50
        for x in range(64):
            c = _scale_color((90, 70, 50), br)
            for y in range(crust_y, crust_y + 3):
                d.set_pixel(x, y, c)

        # Island chain: volcanoes drift right as plate moves
        plume_x = 24
        for i in range(5):
            island_x = int(plume_x + (i * 10) + plate_off) % 80 - 8
            age = i
            if age == 0:
                # Active volcano over plume
                peak_h = 6
                color = _scale_color((200, 80, 30), br)
                lava = _scale_color((255, 150, 30), br)
            elif age == 1:
                peak_h = 5
                color = _scale_color((140, 100, 60), br)
                lava = None
            elif age == 2:
                peak_h = 4
                color = _scale_color((100, 90, 70), br)
                lava = None
            else:
                peak_h = 3
                color = _scale_color((80, 80, 70), br)
                lava = None

            for dy in range(peak_h):
                w = 1 + dy
                ty = crust_y - peak_h + dy
                for dx in range(-w, w + 1):
                    px = island_x + dx
                    if 0 <= px < 64 and 0 <= ty < 64:
                        d.set_pixel(px, ty, color)
            if lava:
                if 0 <= island_x < 64 and crust_y - peak_h - 1 >= 0:
                    d.set_pixel(island_x, crust_y - peak_h - 1, lava)

        # Eruption particles
        for ep in self._hot_eruption:
            ix, iy = int(ep[0]), int(ep[1])
            if 0 <= ix < 64 and 0 <= iy < 64:
                c = _scale_color((255, 200, 50), br * ep[4])
                d.set_pixel(ix, iy, c)

        # Plate arrow (rightward drift)
        self._draw_arrow_right(8, crust_y + 1, br)
        self._draw_arrow_right(45, crust_y + 1, br)

        self._draw_label("HOTSPOT", br)

    # ================================================================
    #  SCENE 5: TSUNAMI (Seafloor Displacement)
    # ================================================================

    def _update_tsunami(self, dt):
        self._tsu_timer -= dt
        if self._tsu_timer <= 0 and not self._tsu_active:
            self._tsu_active = True
            self._tsu_wave_x = 20.0
            self._tsu_rupture_flash = 0.2
            self._tsu_timer = 0.0
        if self._tsu_active:
            self._tsu_wave_x += dt * 12.0
            if self._tsu_wave_x > 75:
                self._tsu_active = False
                self._tsu_timer = random.uniform(4.0, 7.0)
        if self._tsu_rupture_flash > 0:
            self._tsu_rupture_flash -= dt

    def _draw_tsunami(self, br):
        d = self.display
        sea_y = 20
        floor_y = 45
        shelf_x = 50

        # Sky
        for y in range(sea_y):
            c = _scale_color(_lerp_color((20, 30, 60), (40, 60, 100), y / sea_y), br)
            for x in range(64):
                d.set_pixel(x, y, c)

        # Ocean body
        for y in range(sea_y, floor_y):
            depth_t = (y - sea_y) / (floor_y - sea_y)
            c = _scale_color(_lerp_color((20, 60, 140), (10, 25, 70), depth_t), br)
            for x in range(64):
                d.set_pixel(x, y, c)

        # Seafloor
        for y in range(floor_y, 58):
            c = _scale_color((60, 50, 40), br)
            for x in range(64):
                d.set_pixel(x, y, c)

        # Continental shelf (right side rises)
        for x in range(shelf_x, 64):
            shelf_top = floor_y - int((x - shelf_x) * (floor_y - sea_y - 4) / (64 - shelf_x))
            c = _scale_color((80, 65, 45), br)
            for y in range(shelf_top, floor_y):
                d.set_pixel(x, y, c)
            # Beach/land above water
            if shelf_top <= sea_y:
                land_c = _scale_color((60, 120, 40), br)
                for y in range(max(0, shelf_top - 2), sea_y):
                    d.set_pixel(x, y, land_c)

        # Rupture zone marker
        rupture_x = 20
        if self._tsu_rupture_flash > 0:
            flash = self._tsu_rupture_flash / 0.2
            fc = _scale_color((255, 255, 180), br * flash)
            for dy in range(-2, 3):
                y = floor_y + dy
                if 0 <= y < 64:
                    for dx in range(-1, 2):
                        px = rupture_x + dx
                        if 0 <= px < 64:
                            d.set_pixel(px, y, fc)

        # Wave
        if self._tsu_active:
            wx = self._tsu_wave_x
            # Wave height grows as water gets shallower near shelf
            if wx < shelf_x:
                wave_h = 2
            else:
                approach = min(1.0, (wx - shelf_x) / 12.0)
                wave_h = int(2 + 8 * approach)

            wix = int(wx)
            for dx in range(-3, 4):
                px = wix + dx
                if 0 <= px < 64:
                    h = max(1, wave_h - abs(dx))
                    for dy in range(h):
                        py = sea_y - dy
                        if 0 <= py < 64:
                            c = _scale_color((100, 180, 255), br * (1.0 - abs(dx) / 4.0))
                            d.set_pixel(px, py, c)

        # Fault line on seafloor
        c = _scale_color((200, 80, 60), br * 0.6)
        for dy in range(-1, 2):
            y = floor_y + dy
            if 0 <= y < 64 and 0 <= rupture_x < 64:
                d.set_pixel(rupture_x, y, c)

        self._draw_label("TSUNAMI", br)

    # ================================================================
    #  SCENE 6: MOUNTAIN (Continental Collision / Orogeny)
    # ================================================================

    def _update_mountain(self, dt):
        self._mtn_compression = min(1.0, self._mtn_compression + dt * 0.06)
        comp = self._mtn_compression
        for i in range(len(self._mtn_fold_heights)):
            cx = i / (len(self._mtn_fold_heights) - 1) - 0.5
            envelope = max(0, 1.0 - abs(cx) * 3.0)
            fold = math.sin(i * 1.8 + comp * 2) * 0.5 + 0.5
            self._mtn_fold_heights[i] = envelope * fold * comp * 18

    def _draw_mountain(self, br):
        d = self.display
        crust_y = 30

        self._draw_mantle_bg(crust_y + 8, br)

        # Crust layers (two plates converging)
        gap = int(20 * (1.0 - self._mtn_compression))

        # Left plate
        left_edge = 32 - gap // 2
        for x in range(0, left_edge):
            for dy in range(8):
                y = crust_y + dy
                t = dy / 7.0
                c = _scale_color(_lerp_color((120, 100, 70), (80, 60, 50), t), br)
                if 0 <= y < 64:
                    d.set_pixel(x, y, c)

        # Right plate
        right_edge = 32 + gap // 2
        for x in range(right_edge, 64):
            for dy in range(8):
                y = crust_y + dy
                t = dy / 7.0
                c = _scale_color(_lerp_color((100, 90, 75), (70, 55, 50), t), br)
                if 0 <= y < 64:
                    d.set_pixel(x, y, c)

        # Mountain fold belt
        n = len(self._mtn_fold_heights)
        for i in range(n):
            x_center = int(12 + i * (40 / (n - 1)))
            h = int(self._mtn_fold_heights[i])
            if h < 1:
                continue
            for dx in range(-2, 3):
                px = x_center + dx
                if not (0 <= px < 64):
                    continue
                col_h = max(0, h - abs(dx) * 2)
                for dy in range(col_h):
                    py = crust_y - dy
                    if 0 <= py < 64:
                        t = dy / max(1, col_h)
                        base = _lerp_color((140, 120, 80), (200, 190, 170), t)
                        # Snow cap
                        if dy > col_h - 3 and col_h > 8:
                            base = (230, 235, 240)
                        d.set_pixel(px, py, _scale_color(base, br))

        # Sky
        for y in range(0, crust_y):
            has_mountain = False
            for x in range(64):
                cur = d.get_pixel(x, y)
                if cur != (0, 0, 0):
                    has_mountain = True
                    break
            if not has_mountain:
                t = y / crust_y
                sky = _scale_color(_lerp_color((30, 50, 100), (60, 80, 130), t), br)
                for x in range(64):
                    if d.get_pixel(x, y) == (0, 0, 0):
                        d.set_pixel(x, y, sky)

        # Plate arrows (converging)
        self._draw_arrow_right(4, crust_y + 4, br)
        self._draw_arrow_left(53, crust_y + 4, br)

        self._draw_label("MOUNTAIN", br)
