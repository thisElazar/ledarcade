"""
Starry Night - Van Gogh inspired visual
=======================================
A swirling night sky with twinkling stars, inspired by
Vincent van Gogh's masterpiece.

Controls:
  Up/Down    - Adjust swirl speed
  Left/Right - Adjust star twinkle rate
  Space      - Add a shooting star
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE


class StarryNight(Visual):
    name = "STARRYNIGHT"
    description = "Van Gogh's sky"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.swirl_speed = 1.0
        self.twinkle_rate = 1.0

        # Sky colors - Van Gogh's deep blues
        self.sky_darkest = (25, 25, 60)
        self.sky_dark = (40, 50, 100)
        self.sky_mid = (60, 80, 140)
        self.sky_light = (80, 110, 170)
        self.sky_highlight = (100, 140, 200)

        # Swirl accent colors
        self.swirl_teal = (60, 140, 160)
        self.swirl_green = (70, 130, 100)

        # Star colors
        self.star_white = (255, 255, 240)
        self.star_yellow = (255, 240, 150)
        self.star_orange = (255, 200, 100)

        # Moon color
        self.moon_color = (255, 250, 200)
        self.moon_glow = (255, 240, 150)

        # Generate stars
        self.stars = []
        self.generate_stars()

        # Generate swirl centers
        self.swirls = []
        self.generate_swirls()

        # Shooting stars
        self.shooting_stars = []

        # Village/hill silhouette
        self.generate_landscape()

    def generate_stars(self):
        """Generate twinkling stars."""
        self.stars = []
        num_stars = random.randint(15, 25)

        for _ in range(num_stars):
            self.stars.append({
                'x': random.uniform(2, GRID_SIZE - 2),
                'y': random.uniform(2, 45),  # Upper portion of sky
                'size': random.choice([1, 1, 1, 2, 2, 3]),  # Mostly small
                'phase': random.uniform(0, math.pi * 2),
                'speed': random.uniform(2, 5),
                'color_type': random.choice(['white', 'yellow', 'orange']),
            })

        # Add a prominent moon
        self.moon = {
            'x': random.uniform(45, 55),
            'y': random.uniform(8, 15),
            'radius': 5,
            'phase': 0,
        }

    def generate_swirls(self):
        """Generate eddy centers for turbulent sky like Van Gogh's painting."""
        self.eddies = []

        # Main large eddies - the prominent swirls in the painting
        # Upper sky swirls
        self.eddies.append({'x': 20, 'y': 18, 'radius': 12, 'strength': 1.0, 'direction': 1})
        self.eddies.append({'x': 45, 'y': 25, 'radius': 10, 'strength': 0.9, 'direction': -1})

        # Mid-sky eddies
        self.eddies.append({'x': 8, 'y': 30, 'radius': 8, 'strength': 0.7, 'direction': 1})
        self.eddies.append({'x': 32, 'y': 35, 'radius': 9, 'strength': 0.8, 'direction': 1})
        self.eddies.append({'x': 55, 'y': 32, 'radius': 7, 'strength': 0.6, 'direction': -1})

        # Smaller accent eddies
        for _ in range(6):
            self.eddies.append({
                'x': random.uniform(5, 59),
                'y': random.uniform(8, 45),
                'radius': random.uniform(4, 7),
                'strength': random.uniform(0.3, 0.6),
                'direction': random.choice([-1, 1]),
            })

    def generate_landscape(self):
        """Generate the village/hill silhouette."""
        self.hills = []

        # Rolling hills
        x = 0
        while x < GRID_SIZE:
            width = random.randint(15, 30)
            height = random.randint(8, 16)
            self.hills.append({
                'x': x,
                'width': width,
                'height': height,
            })
            x += width - random.randint(5, 10)

        # Cypress tree (iconic Van Gogh element)
        self.cypress = {
            'x': random.randint(5, 15),
            'height': random.randint(25, 35),
            'width': 4,
        }

        # Small village buildings
        self.buildings = []
        for _ in range(random.randint(3, 6)):
            self.buildings.append({
                'x': random.randint(20, GRID_SIZE - 10),
                'width': random.randint(3, 6),
                'height': random.randint(4, 10),
            })

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.up:
            self.swirl_speed = min(3.0, self.swirl_speed + 0.1)
            consumed = True
        if input_state.down:
            self.swirl_speed = max(0.2, self.swirl_speed - 0.1)
            consumed = True

        if input_state.right:
            self.twinkle_rate = min(3.0, self.twinkle_rate + 0.1)
            consumed = True
        if input_state.left:
            self.twinkle_rate = max(0.3, self.twinkle_rate - 0.1)
            consumed = True

        if input_state.action:
            # Add a shooting star
            self.shooting_stars.append({
                'x': random.uniform(0, GRID_SIZE // 2),
                'y': random.uniform(5, 20),
                'dx': random.uniform(2, 4),
                'dy': random.uniform(0.5, 1.5),
                'life': 1.0,
                'length': random.randint(5, 10),
            })
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt * self.swirl_speed

        # Update shooting stars
        for star in self.shooting_stars:
            star['x'] += star['dx'] * dt * 30
            star['y'] += star['dy'] * dt * 30
            star['life'] -= dt * 1.5

        self.shooting_stars = [s for s in self.shooting_stars if s['life'] > 0]

    def draw(self):
        # Draw swirling sky
        self.draw_sky()

        # Draw landscape silhouette
        self.draw_landscape()

        # Draw stars
        self.draw_stars()

        # Draw moon
        self.draw_moon()

        # Draw shooting stars
        for star in self.shooting_stars:
            self.draw_shooting_star(star)

    def draw_sky(self):
        """Draw the swirling night sky with turbulent eddies like Van Gogh."""
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                # Base gradient (darker at top)
                gradient_t = y / GRID_SIZE
                base_color = self.lerp_color(self.sky_darkest, self.sky_dark, gradient_t * 0.5)

                # Calculate flow at this point from all eddies
                # Flow is tangent to eddies (perpendicular to radius)
                flow_x = 0
                flow_y = 0
                swirl_intensity = 0

                for eddy in self.eddies:
                    dx = x - eddy['x']
                    dy = y - eddy['y']
                    dist = math.sqrt(dx * dx + dy * dy)

                    if dist < eddy['radius'] * 2.5 and dist > 0.1:
                        # Influence falls off with distance
                        influence = max(0, 1 - dist / (eddy['radius'] * 2.5))
                        influence = influence ** 0.6  # Softer falloff

                        # Tangent direction (perpendicular to radius) creates circular flow
                        # direction determines clockwise vs counter-clockwise
                        tangent_x = -dy / dist * eddy['direction']
                        tangent_y = dx / dist * eddy['direction']

                        flow_x += tangent_x * influence * eddy['strength']
                        flow_y += tangent_y * influence * eddy['strength']
                        swirl_intensity += influence * eddy['strength']

                # Normalize flow direction
                flow_mag = math.sqrt(flow_x * flow_x + flow_y * flow_y)
                if flow_mag > 0.01:
                    flow_x /= flow_mag
                    flow_y /= flow_mag

                # Sample along the flow direction to create streaky brushstrokes
                # This makes the texture follow the curves
                flow_angle = math.atan2(flow_y, flow_x)

                # Create swirling bands by sampling perpendicular to flow
                perp_x = -flow_y
                perp_y = flow_x
                perp_sample = x * perp_x + y * perp_y

                # Animated flowing pattern along the flow direction
                flow_sample = x * flow_x + y * flow_y + self.time * 8

                # Create light/dark bands that follow the swirl
                band_val = math.sin(perp_sample * 0.4 + self.time * 0.3)
                band_val += math.sin(perp_sample * 0.7 + flow_sample * 0.1) * 0.5

                # Modulate by swirl intensity - more contrast in swirls
                intensity_boost = 0.3 + swirl_intensity * 0.7
                band_val *= intensity_boost

                # Clamp
                band_val = max(-1, min(1, band_val))

                if band_val > 0:
                    t = band_val
                    color = self.lerp_color(base_color, self.sky_light, t * 0.4)
                    # Subtle teal/green tints in the swirls
                    tint_blend = math.sin(flow_sample * 0.1) * 0.5 + 0.5
                    tint = self.lerp_color(self.swirl_teal, self.swirl_green, tint_blend)
                    color = self.lerp_color(color, tint, t * swirl_intensity * 0.2)
                else:
                    t = -band_val
                    color = self.lerp_color(base_color, self.sky_darkest, t * 0.3)

                # Subtle texture that follows the flow direction
                brush_along_flow = math.sin(flow_sample * 0.8) * 3
                color = (
                    max(0, min(255, int(color[0] + brush_along_flow))),
                    max(0, min(255, int(color[1] + brush_along_flow * 1.1))),
                    max(0, min(255, int(color[2] + brush_along_flow * 0.8))),
                )

                self.display.set_pixel(x, y, color)

    def draw_stars(self):
        """Draw twinkling stars with halos."""
        for star in self.stars:
            # Twinkle effect
            twinkle = math.sin(self.time * star['speed'] * self.twinkle_rate + star['phase'])
            brightness = 0.6 + twinkle * 0.4

            if brightness < 0.3:
                continue  # Star is dim, skip drawing

            # Base color
            if star['color_type'] == 'white':
                color = self.star_white
            elif star['color_type'] == 'yellow':
                color = self.star_yellow
            else:
                color = self.star_orange

            # Apply brightness
            color = (
                int(color[0] * brightness),
                int(color[1] * brightness),
                int(color[2] * brightness),
            )

            x, y = int(star['x']), int(star['y'])
            size = star['size']

            # Draw halo (glow effect) for larger stars
            if size >= 2 and brightness > 0.7:
                halo_color = (
                    int(color[0] * 0.3),
                    int(color[1] * 0.3),
                    int(color[2] * 0.2),
                )
                for dx in range(-size, size + 1):
                    for dy in range(-size, size + 1):
                        if dx == 0 and dy == 0:
                            continue
                        dist = math.sqrt(dx * dx + dy * dy)
                        if dist <= size:
                            px, py = x + dx, y + dy
                            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                                # Blend with existing pixel
                                existing = self.display.get_pixel(px, py)
                                fade = 1 - dist / size
                                blended = self.lerp_color(existing, halo_color, fade * 0.5)
                                self.display.set_pixel(px, py, blended)

            # Draw star center
            if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                self.display.set_pixel(x, y, color)

            # Draw star rays for bright stars
            if size >= 2 and brightness > 0.8:
                ray_color = (
                    int(color[0] * 0.7),
                    int(color[1] * 0.7),
                    int(color[2] * 0.6),
                )
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    px, py = x + dx, y + dy
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        self.display.set_pixel(px, py, ray_color)

    def draw_moon(self):
        """Draw the crescent moon with glow."""
        cx, cy = int(self.moon['x']), int(self.moon['y'])
        radius = self.moon['radius']

        # Outer glow
        for dy in range(-radius - 3, radius + 4):
            for dx in range(-radius - 3, radius + 4):
                dist = math.sqrt(dx * dx + dy * dy)
                if dist <= radius + 3 and dist > radius:
                    px, py = cx + dx, cy + dy
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        fade = 1 - (dist - radius) / 3
                        glow = (
                            int(self.moon_glow[0] * fade * 0.4),
                            int(self.moon_glow[1] * fade * 0.4),
                            int(self.moon_glow[2] * fade * 0.3),
                        )
                        existing = self.display.get_pixel(px, py)
                        blended = (
                            min(255, existing[0] + glow[0]),
                            min(255, existing[1] + glow[1]),
                            min(255, existing[2] + glow[2]),
                        )
                        self.display.set_pixel(px, py, blended)

        # Moon body (crescent shape)
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                dist = math.sqrt(dx * dx + dy * dy)
                if dist <= radius:
                    # Crescent: cut out a circle offset to the right
                    cut_dist = math.sqrt((dx - 3) ** 2 + dy ** 2)
                    if cut_dist > radius - 1:
                        px, py = cx + dx, cy + dy
                        if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                            # Slight color variation
                            var = math.sin(dx * 0.5 + dy * 0.5) * 10
                            color = (
                                min(255, int(self.moon_color[0] + var)),
                                min(255, int(self.moon_color[1] + var)),
                                min(255, int(self.moon_color[2] + var * 0.5)),
                            )
                            self.display.set_pixel(px, py, color)

    def draw_landscape(self):
        """Draw the village silhouette."""
        # Dark silhouette colors
        hill_color = (15, 20, 35)
        building_color = (10, 15, 25)
        cypress_color = (8, 12, 20)
        window_color = (255, 220, 120)

        # Draw hills
        for hill in self.hills:
            cx = hill['x'] + hill['width'] // 2
            for x in range(hill['x'], hill['x'] + hill['width']):
                if 0 <= x < GRID_SIZE:
                    # Parabolic hill shape
                    dx = x - cx
                    height = hill['height'] * (1 - (dx / (hill['width'] / 2)) ** 2)
                    height = max(0, int(height))

                    for y in range(GRID_SIZE - height, GRID_SIZE):
                        if 0 <= y < GRID_SIZE:
                            self.display.set_pixel(x, y, hill_color)

        # Draw buildings
        for building in self.buildings:
            bx = building['x']
            bw = building['width']
            bh = building['height']

            for x in range(bx, bx + bw):
                for y in range(GRID_SIZE - bh - 5, GRID_SIZE - 5):
                    if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                        self.display.set_pixel(x, y, building_color)

            # Window
            if bw >= 3 and bh >= 4:
                wx = bx + bw // 2
                wy = GRID_SIZE - bh - 3
                if 0 <= wx < GRID_SIZE and 0 <= wy < GRID_SIZE:
                    # Flickering window light
                    flicker = 0.8 + math.sin(self.time * 3 + bx) * 0.2
                    wc = (
                        int(window_color[0] * flicker),
                        int(window_color[1] * flicker),
                        int(window_color[2] * flicker),
                    )
                    self.display.set_pixel(wx, wy, wc)

        # Draw cypress tree
        cx = self.cypress['x']
        ch = self.cypress['height']
        cw = self.cypress['width']

        for y in range(GRID_SIZE - ch, GRID_SIZE):
            # Tapered width
            progress = (y - (GRID_SIZE - ch)) / ch
            width = int(cw * (1 - progress * 0.7))
            width = max(1, width)

            for dx in range(-width // 2, width // 2 + 1):
                x = cx + dx
                if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                    # Wavy edges like Van Gogh's cypress
                    wave = math.sin(y * 0.5 + self.time) * 0.5
                    if abs(dx) <= width // 2 + wave:
                        self.display.set_pixel(x, y, cypress_color)

    def draw_shooting_star(self, star):
        """Draw a shooting star with trail."""
        x, y = int(star['x']), int(star['y'])
        length = star['length']
        life = star['life']

        for i in range(length):
            trail_x = int(x - star['dx'] * i * 0.3)
            trail_y = int(y - star['dy'] * i * 0.3)

            if 0 <= trail_x < GRID_SIZE and 0 <= trail_y < GRID_SIZE:
                fade = (1 - i / length) * life
                color = (
                    int(255 * fade),
                    int(250 * fade),
                    int(200 * fade * 0.8),
                )
                self.display.set_pixel(trail_x, trail_y, color)

    def lerp_color(self, c1, c2, t):
        """Linearly interpolate between two colors."""
        t = max(0, min(1, t))
        return (
            int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t),
        )
