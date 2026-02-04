"""
Orrery - Clockwork Solar System
===============================
A brass clockwork model of the solar system. Central sun with planets
on arms orbiting at different speeds and distances. Inner planets zip
around while outer planets crawl. Gears visible at the base driving the arms.

Controls:
  Left/Right - Adjust time scale
"""

import math
from . import Visual, Display, Colors, GRID_SIZE


# Brass/gold color palette
BRASS = (200, 170, 50)
BRASS_DARK = (140, 120, 35)
BRASS_LIGHT = (220, 190, 70)
GOLD = (218, 190, 80)
GOLD_DARK = (160, 135, 50)
COPPER = (190, 120, 70)
STEEL = (150, 155, 165)

# Sun and planet colors
SUN_COLOR = (255, 200, 50)
SUN_GLOW = (255, 160, 30)

# Background
BACKGROUND = (10, 10, 15)
PLATE_COLOR = (20, 20, 25)

# Planet definitions: name, color, orbital_radius, orbital_period_ratio
# Using simplified orbital period ratios relative to Mercury (innermost = 1.0)
# Real ratios: Mercury=1, Venus=2.55, Earth=4.15, Mars=7.8, Jupiter=49, Saturn=122
# Simplified for visibility on 64x64
PLANETS = [
    {"name": "Mercury", "color": (180, 180, 180), "radius": 8,  "period": 1.0,    "size": 1},
    {"name": "Venus",   "color": (230, 200, 150), "radius": 13, "period": 2.5,    "size": 1},
    {"name": "Earth",   "color": (100, 150, 255), "radius": 18, "period": 4.0,    "size": 2},
    {"name": "Mars",    "color": (255, 100, 80),  "radius": 23, "period": 7.5,    "size": 1},
    {"name": "Jupiter", "color": (255, 200, 150), "radius": 28, "period": 20.0,   "size": 3},
]

# Gear definitions for the base mechanism
GEARS = [
    {"teeth": 8,  "r": 5, "cx": 10, "cy": 56, "color": BRASS},
    {"teeth": 12, "r": 7, "cx": 22, "cy": 56, "color": COPPER},
    {"teeth": 10, "r": 6, "cx": 35, "cy": 56, "color": BRASS_LIGHT},
    {"teeth": 8,  "r": 5, "cx": 46, "cy": 56, "color": GOLD},
    {"teeth": 6,  "r": 4, "cx": 55, "cy": 56, "color": STEEL},
]

# Speed levels (Mercury revolutions per second)
SPEED_LEVELS = [0.05, 0.1, 0.2, 0.4, 0.8, 1.5]


class Orrery(Visual):
    name = "ORRERY"
    description = "Brass clockwork solar system"
    category = "mechanics"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed_level = 2  # Start at medium speed
        self.base_speed = SPEED_LEVELS[self.speed_level] * 2.0 * math.pi

        # Planet angles (radians)
        self.planet_angles = [0.0] * len(PLANETS)

        # Gear rotation angles
        self.gear_angles = [0.0] * len(GEARS)

        # Sun pulse phase
        self.sun_pulse = 0.0

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.right_pressed:
            self.speed_level = min(len(SPEED_LEVELS) - 1, self.speed_level + 1)
            self.base_speed = SPEED_LEVELS[self.speed_level] * 2.0 * math.pi
            consumed = True
        elif input_state.left_pressed:
            self.speed_level = max(0, self.speed_level - 1)
            self.base_speed = SPEED_LEVELS[self.speed_level] * 2.0 * math.pi
            consumed = True
        return consumed

    def update(self, dt):
        self.time += dt

        # Update planet angles - inner planets orbit faster
        for i, planet in enumerate(PLANETS):
            angular_velocity = self.base_speed / planet["period"]
            self.planet_angles[i] += angular_velocity * dt

        # Update gear angles (purely decorative, linked to base speed)
        for i in range(len(GEARS)):
            # Alternate direction, varying speeds
            direction = 1 if i % 2 == 0 else -1
            speed_factor = 1.0 + (i * 0.3)
            self.gear_angles[i] += direction * self.base_speed * speed_factor * dt

        # Sun pulse
        self.sun_pulse += dt * 3.0

    def draw(self):
        d = self.display
        d.clear(BACKGROUND)

        # Center of orrery (slightly above center to leave room for gears)
        cx, cy = 32, 26

        # Draw gear mechanism at the base first (behind everything)
        self._draw_gears(d)

        # Draw plate/base edge
        self._draw_base_edge(d)

        # Draw orbital paths (subtle rings)
        self._draw_orbital_paths(d, cx, cy)

        # Draw arms and planets
        self._draw_arms_and_planets(d, cx, cy)

        # Draw central sun (on top)
        self._draw_sun(d, cx, cy)

    def _draw_gears(self, d):
        """Draw decorative gear mechanism at the base."""
        TWO_PI = 2.0 * math.pi

        for gi, gear in enumerate(GEARS):
            gcx, gcy = gear["cx"], gear["cy"]
            r = gear["r"]
            n_teeth = gear["teeth"]
            rotation = self.gear_angles[gi]
            color = gear["color"]
            dark = tuple(max(0, c - 40) for c in color)

            # Draw gear body and teeth
            root_r = r - 1.0
            tip_r = r + 1.0

            for py in range(max(0, gcy - int(tip_r) - 1), min(64, gcy + int(tip_r) + 2)):
                for px in range(max(0, gcx - int(tip_r) - 1), min(64, gcx + int(tip_r) + 2)):
                    dx = px - gcx
                    dy = py - gcy
                    dist_sq = dx * dx + dy * dy
                    dist = math.sqrt(dist_sq)

                    if dist <= tip_r:
                        if dist <= 1.5:
                            # Hub
                            d.set_pixel(px, py, dark)
                        elif dist <= root_r:
                            # Body
                            d.set_pixel(px, py, color)
                        else:
                            # Teeth region
                            angle = math.atan2(dy, dx) - rotation
                            tooth_phase = (angle * n_teeth / TWO_PI) % 1.0
                            if tooth_phase < 0:
                                tooth_phase += 1.0
                            if tooth_phase < 0.5:
                                d.set_pixel(px, py, color)

    def _draw_base_edge(self, d):
        """Draw decorative brass edge at the base."""
        # Horizontal brass bar above the gears
        for x in range(64):
            d.set_pixel(x, 49, BRASS_DARK)
            d.set_pixel(x, 50, BRASS)

    def _draw_orbital_paths(self, d, cx, cy):
        """Draw subtle orbital ring paths."""
        for planet in PLANETS:
            r = planet["radius"]
            # Draw a dotted/dashed orbital path
            steps = int(r * 4)
            for i in range(steps):
                angle = i * 2.0 * math.pi / steps
                if i % 3 == 0:  # Dotted pattern
                    px = int(round(cx + r * math.cos(angle)))
                    py = int(round(cy + r * math.sin(angle)))
                    if 0 <= px < 64 and 0 <= py < 49:  # Stay above base
                        d.set_pixel(px, py, (40, 40, 50))

    def _draw_arms_and_planets(self, d, cx, cy):
        """Draw the brass arms and planets."""
        for i, planet in enumerate(PLANETS):
            angle = self.planet_angles[i]
            r = planet["radius"]

            # Calculate planet position
            px = cx + r * math.cos(angle)
            py = cy + r * math.sin(angle)

            # Draw brass arm from center to planet
            self._draw_arm(d, cx, cy, int(round(px)), int(round(py)))

            # Draw planet
            self._draw_planet(d, int(round(px)), int(round(py)),
                              planet["color"], planet["size"])

    def _draw_arm(self, d, x0, y0, x1, y1):
        """Draw a brass arm using Bresenham's line algorithm."""
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        # Skip first few pixels near center (sun area)
        dist_total = math.sqrt(dx * dx + dy * dy)
        skip_dist = 4  # Skip near sun

        x, y = x0, y0
        steps = 0
        max_steps = int(dist_total) + 1

        while steps < max_steps:
            # Current distance from start
            curr_dist = math.sqrt((x - x0) ** 2 + (y - y0) ** 2)

            if curr_dist > skip_dist and 0 <= x < 64 and 0 <= y < 49:
                d.set_pixel(x, y, BRASS_DARK)

            if x == x1 and y == y1:
                break

            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

            steps += 1

    def _draw_planet(self, d, px, py, color, size):
        """Draw a planet at the given position."""
        # Stay above base plate
        if py >= 49:
            return

        if size == 1:
            # Single pixel
            if 0 <= px < 64 and 0 <= py < 64:
                d.set_pixel(px, py, color)
        elif size == 2:
            # 2x2 block
            for dy in range(-1, 1):
                for dx in range(-1, 1):
                    if 0 <= px + dx < 64 and 0 <= py + dy < 49:
                        d.set_pixel(px + dx, py + dy, color)
        elif size >= 3:
            # Circle
            r = size // 2
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    if dx * dx + dy * dy <= r * r:
                        npx, npy = px + dx, py + dy
                        if 0 <= npx < 64 and 0 <= npy < 49:
                            d.set_pixel(npx, npy, color)

    def _draw_sun(self, d, cx, cy):
        """Draw the central sun with a subtle glow effect."""
        # Sun pulse for glow effect
        pulse = 0.5 + 0.5 * math.sin(self.sun_pulse)

        # Outer glow (subtle)
        glow_r = 5
        for dy in range(-glow_r, glow_r + 1):
            for dx in range(-glow_r, glow_r + 1):
                dist_sq = dx * dx + dy * dy
                if dist_sq <= glow_r * glow_r and dist_sq > 9:
                    npx, npy = cx + dx, cy + dy
                    if 0 <= npx < 64 and 0 <= npy < 49:
                        # Dim glow
                        intensity = (1.0 - dist_sq / (glow_r * glow_r)) * (0.3 + 0.2 * pulse)
                        glow_color = (
                            int(SUN_GLOW[0] * intensity),
                            int(SUN_GLOW[1] * intensity),
                            int(SUN_GLOW[2] * intensity)
                        )
                        d.set_pixel(npx, npy, glow_color)

        # Sun core
        sun_r = 3
        for dy in range(-sun_r, sun_r + 1):
            for dx in range(-sun_r, sun_r + 1):
                dist_sq = dx * dx + dy * dy
                if dist_sq <= sun_r * sun_r:
                    npx, npy = cx + dx, cy + dy
                    if 0 <= npx < 64 and 0 <= npy < 49:
                        # Brighter at center
                        if dist_sq <= 1:
                            d.set_pixel(npx, npy, (255, 255, 200))
                        elif dist_sq <= 4:
                            d.set_pixel(npx, npy, SUN_COLOR)
                        else:
                            d.set_pixel(npx, npy, SUN_GLOW)

        # Central pivot (brass)
        d.set_pixel(cx, cy, GOLD)
