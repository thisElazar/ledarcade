"""
Astrolabe - Medieval Astronomical Instrument
=============================================
A brass astrolabe viewed from the front - the "medieval smartphone" that could
tell time, find latitude, predict sunrise/sunset, and locate stars.

Components:
- Mater: Outer ring with degree markings
- Tympan: Climate plate with altitude/azimuth curves (fixed)
- Rete: Star map overlay with pointed star markers (rotates slowly)
- Alidade: Rotating rule/sighting bar across the face

Controls:
  Left/Right - Adjust rotation speed
"""

import math
from . import Visual, Display, Colors, GRID_SIZE


# Brass color palette
BRASS_POLISHED = (200, 170, 50)
BRASS_AGED = (160, 130, 40)
BRASS_DARK = (100, 80, 25)
BRASS_LIGHT = (220, 190, 70)
BRASS_HIGHLIGHT = (240, 210, 100)

# Background and markings
BACKGROUND = (8, 8, 12)
MARKING_DARK = (60, 50, 20)
TYMPAN_LINE = (80, 65, 30)
STAR_COLOR = (255, 240, 180)
STAR_DIM = (180, 160, 100)

# Center coordinates
CX, CY = 32, 32

# Radii for different components
OUTER_RADIUS = 30      # Outer edge of mater
MATER_INNER = 27       # Inner edge of mater ring
TYMPAN_RADIUS = 26     # Tympan plate
RETE_RADIUS = 25       # Rete overlay
ALIDADE_LENGTH = 28    # Alidade extends past center

# Speed levels (radians per second for rete)
SPEED_LEVELS = [0.02, 0.05, 0.1, 0.2, 0.4, 0.8]

# Star positions on the rete (angle offset from rete zero, radius from center)
# Based on typical astrolabe star pointers
RETE_STARS = [
    {"name": "Vega", "angle": 0.0, "radius": 8, "bright": True},
    {"name": "Altair", "angle": 0.8, "radius": 14, "bright": True},
    {"name": "Deneb", "angle": 1.5, "radius": 10, "bright": False},
    {"name": "Capella", "angle": 2.2, "radius": 18, "bright": True},
    {"name": "Aldebaran", "angle": 3.0, "radius": 22, "bright": True},
    {"name": "Rigel", "angle": 3.8, "radius": 20, "bright": False},
    {"name": "Sirius", "angle": 4.5, "radius": 24, "bright": True},
    {"name": "Procyon", "angle": 5.2, "radius": 16, "bright": False},
    {"name": "Regulus", "angle": 5.8, "radius": 12, "bright": False},
]


class Astrolabe(Visual):
    name = "ASTROLABE"
    description = "Medieval astronomical instrument"
    category = "mechanics"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed_level = 2  # Medium speed
        self.rete_speed = SPEED_LEVELS[self.speed_level]

        # Rotation angles
        self.rete_angle = 0.0       # Star map rotation
        self.alidade_angle = 0.3    # Rule rotation (slightly offset)

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.right_pressed:
            self.speed_level = min(len(SPEED_LEVELS) - 1, self.speed_level + 1)
            self.rete_speed = SPEED_LEVELS[self.speed_level]
            consumed = True
        elif input_state.left_pressed:
            self.speed_level = max(0, self.speed_level - 1)
            self.rete_speed = SPEED_LEVELS[self.speed_level]
            consumed = True
        return consumed

    def update(self, dt):
        self.time += dt

        # Rotate rete (star map) slowly
        self.rete_angle += self.rete_speed * dt

        # Alidade rotates slower, in opposite direction
        self.alidade_angle -= self.rete_speed * 0.3 * dt

    def draw(self):
        d = self.display
        d.clear(BACKGROUND)

        # Draw from back to front
        self._draw_mater(d)           # Outer ring with markings
        self._draw_tympan(d)          # Climate plate (fixed)
        self._draw_rete(d)            # Star map (rotates)
        self._draw_alidade(d)         # Sighting rule (rotates)
        self._draw_center_pin(d)      # Central pivot

    def _draw_mater(self, d):
        """Draw the outer mater ring with degree tick marks."""
        TWO_PI = 2.0 * math.pi

        # Draw outer ring body
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                dx = x - CX
                dy = y - CY
                dist_sq = dx * dx + dy * dy
                dist = math.sqrt(dist_sq)

                # Main brass ring
                if MATER_INNER <= dist <= OUTER_RADIUS:
                    # Slight shading for 3D effect
                    shade = 0.8 + 0.2 * (dx + dy) / (OUTER_RADIUS * 1.4)
                    shade = max(0.6, min(1.0, shade))
                    color = (
                        int(BRASS_POLISHED[0] * shade),
                        int(BRASS_POLISHED[1] * shade),
                        int(BRASS_POLISHED[2] * shade)
                    )
                    d.set_pixel(x, y, color)

        # Draw degree tick marks on outer edge
        num_major = 12   # Major ticks (every 30 degrees)
        num_minor = 36   # Minor ticks (every 10 degrees)

        # Minor ticks
        for i in range(num_minor):
            angle = i * TWO_PI / num_minor
            # Tick on outer edge
            r_start = OUTER_RADIUS - 1
            r_end = OUTER_RADIUS
            for r in range(int(r_start), int(r_end) + 1):
                px = int(round(CX + r * math.cos(angle)))
                py = int(round(CY + r * math.sin(angle)))
                if 0 <= px < 64 and 0 <= py < 64:
                    d.set_pixel(px, py, MARKING_DARK)

        # Major ticks (longer)
        for i in range(num_major):
            angle = i * TWO_PI / num_major
            r_start = MATER_INNER + 1
            r_end = OUTER_RADIUS
            for r in range(int(r_start), int(r_end) + 1):
                px = int(round(CX + r * math.cos(angle)))
                py = int(round(CY + r * math.sin(angle)))
                if 0 <= px < 64 and 0 <= py < 64:
                    d.set_pixel(px, py, BRASS_DARK)

    def _draw_tympan(self, d):
        """Draw the tympan (climate plate) with altitude/azimuth curves."""
        # Fill tympan area with dark brass
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                dx = x - CX
                dy = y - CY
                dist = math.sqrt(dx * dx + dy * dy)

                if dist <= TYMPAN_RADIUS and dist > 3:
                    d.set_pixel(x, y, BRASS_DARK)

        # Draw altitude circles (almucantars) - concentric arcs
        # In a real astrolabe these are projected circles of equal altitude
        altitude_radii = [6, 12, 18, 24]
        for r in altitude_radii:
            self._draw_circle_outline(d, CX, CY, r, TYMPAN_LINE)

        # Draw azimuth lines (radial lines from center)
        num_azimuth = 8
        TWO_PI = 2.0 * math.pi
        for i in range(num_azimuth):
            angle = i * TWO_PI / num_azimuth
            # Line from center outward
            for dist in range(4, TYMPAN_RADIUS + 1, 2):
                px = int(round(CX + dist * math.cos(angle)))
                py = int(round(CY + dist * math.sin(angle)))
                if 0 <= px < 64 and 0 <= py < 64:
                    d.set_pixel(px, py, TYMPAN_LINE)

        # Draw horizon line (horizontal across middle)
        for x in range(CX - TYMPAN_RADIUS, CX + TYMPAN_RADIUS + 1):
            dx = x - CX
            if dx * dx <= TYMPAN_RADIUS * TYMPAN_RADIUS:
                d.set_pixel(x, CY, BRASS_AGED)

    def _draw_rete(self, d):
        """Draw the rete (star map overlay) - rotates with time."""
        TWO_PI = 2.0 * math.pi

        # Draw ecliptic circle (offset, rotates with rete)
        # The ecliptic on an astrolabe is an off-center circle
        ecliptic_offset = 8
        ecliptic_radius = 16
        ecl_cx = CX + ecliptic_offset * math.cos(self.rete_angle + math.pi/2)
        ecl_cy = CY + ecliptic_offset * math.sin(self.rete_angle + math.pi/2)

        # Draw ecliptic as dotted circle
        steps = 48
        for i in range(steps):
            if i % 2 == 0:  # Dotted pattern
                angle = i * TWO_PI / steps
                px = int(round(ecl_cx + ecliptic_radius * math.cos(angle)))
                py = int(round(ecl_cy + ecliptic_radius * math.sin(angle)))
                dist_from_center = math.sqrt((px - CX)**2 + (py - CY)**2)
                if dist_from_center <= RETE_RADIUS and 0 <= px < 64 and 0 <= py < 64:
                    d.set_pixel(px, py, BRASS_AGED)

        # Draw rete frame (Gothic/Arabic decorative cutouts represented as arcs)
        # Draw partial arcs representing the open metalwork
        for arc_idx in range(4):
            arc_angle = self.rete_angle + arc_idx * math.pi / 2
            arc_r = 20
            arc_span = 0.6
            for i in range(12):
                angle = arc_angle - arc_span/2 + i * arc_span / 11
                px = int(round(CX + arc_r * math.cos(angle)))
                py = int(round(CY + arc_r * math.sin(angle)))
                if 0 <= px < 64 and 0 <= py < 64:
                    dist = math.sqrt((px - CX)**2 + (py - CY)**2)
                    if dist <= RETE_RADIUS:
                        d.set_pixel(px, py, BRASS_LIGHT)

        # Draw star pointers
        for star in RETE_STARS:
            # Calculate star position based on rete rotation
            star_angle = self.rete_angle + star["angle"]
            star_r = star["radius"]

            sx = int(round(CX + star_r * math.cos(star_angle)))
            sy = int(round(CY + star_r * math.sin(star_angle)))

            if 0 <= sx < 64 and 0 <= sy < 64:
                # Check if within rete bounds
                dist = math.sqrt((sx - CX)**2 + (sy - CY)**2)
                if dist <= RETE_RADIUS:
                    # Draw pointer arm (thin line from nearby arc to star)
                    pointer_start_r = star_r - 3
                    for pr in range(max(3, int(pointer_start_r)), int(star_r)):
                        ppx = int(round(CX + pr * math.cos(star_angle)))
                        ppy = int(round(CY + pr * math.sin(star_angle)))
                        if 0 <= ppx < 64 and 0 <= ppy < 64:
                            d.set_pixel(ppx, ppy, BRASS_AGED)

                    # Draw star point
                    if star["bright"]:
                        d.set_pixel(sx, sy, STAR_COLOR)
                        # Add small glow for bright stars
                        pulse = 0.7 + 0.3 * math.sin(self.time * 2 + star["angle"])
                        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            nx, ny = sx + dx, sy + dy
                            if 0 <= nx < 64 and 0 <= ny < 64:
                                dist_n = math.sqrt((nx - CX)**2 + (ny - CY)**2)
                                if dist_n <= RETE_RADIUS:
                                    glow = (
                                        int(STAR_DIM[0] * pulse * 0.5),
                                        int(STAR_DIM[1] * pulse * 0.5),
                                        int(STAR_DIM[2] * pulse * 0.5)
                                    )
                                    d.set_pixel(nx, ny, glow)
                    else:
                        d.set_pixel(sx, sy, STAR_DIM)

    def _draw_alidade(self, d):
        """Draw the alidade (sighting rule) that rotates across the face."""
        # Alidade is a straight rule passing through the center
        # It rotates to measure angles

        # Draw line across entire instrument
        for i in range(-ALIDADE_LENGTH, ALIDADE_LENGTH + 1):
            px = int(round(CX + i * math.cos(self.alidade_angle)))
            py = int(round(CY + i * math.sin(self.alidade_angle)))

            dist = math.sqrt((px - CX)**2 + (py - CY)**2)
            if dist <= OUTER_RADIUS - 1 and 0 <= px < 64 and 0 <= py < 64:
                # Rule is brass with slight variation
                if abs(i) < 2:
                    continue  # Skip center (will draw pivot)
                elif dist <= ALIDADE_LENGTH - 2:
                    d.set_pixel(px, py, BRASS_HIGHLIGHT)

        # Draw sighting holes at the ends of the alidade
        for end in [-1, 1]:
            hole_r = ALIDADE_LENGTH - 4
            hx = int(round(CX + end * hole_r * math.cos(self.alidade_angle)))
            hy = int(round(CY + end * hole_r * math.sin(self.alidade_angle)))
            if 0 <= hx < 64 and 0 <= hy < 64:
                d.set_pixel(hx, hy, BRASS_DARK)

    def _draw_center_pin(self, d):
        """Draw the central pivot pin."""
        # Central pivot is a small brass circle
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                dist_sq = dx * dx + dy * dy
                if dist_sq <= 4:
                    px, py = CX + dx, CY + dy
                    if dist_sq <= 1:
                        # Center highlight
                        d.set_pixel(px, py, BRASS_HIGHLIGHT)
                    else:
                        d.set_pixel(px, py, BRASS_POLISHED)

    def _draw_circle_outline(self, d, cx, cy, r, color):
        """Draw a circle outline using midpoint algorithm."""
        # Simple circle drawing
        steps = max(16, int(r * 4))
        TWO_PI = 2.0 * math.pi
        for i in range(steps):
            angle = i * TWO_PI / steps
            px = int(round(cx + r * math.cos(angle)))
            py = int(round(cy + r * math.sin(angle)))
            if 0 <= px < 64 and 0 <= py < 64:
                d.set_pixel(px, py, color)
