"""
Water Lilies - Monet-inspired visual
====================================
A serene pond with lily pads and flowers drifting gently on the water.
Inspired by Claude Monet's impressionist masterpieces.

Controls:
  Up/Down    - Adjust drift speed
  Left/Right - Change time of day (lighting)
  Space      - Add a ripple
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE


class WaterLilies(Visual):
    name = "WATERLILIES"
    description = "Monet's pond"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.drift_speed = 1.0
        self.time_of_day = 0.5  # 0 = dawn, 0.5 = day, 1.0 = dusk

        # Water colors (will be modulated by time of day)
        self.update_palette()

        # Generate lily pads
        self.lily_pads = []
        self.generate_lily_pads()

        # Ripples (from interactions or random)
        self.ripples = []

        # Ambient ripple timer
        self.ambient_ripple_timer = 0.0

    def update_palette(self):
        """Update color palette based on time of day."""
        t = self.time_of_day

        if t < 0.3:
            # Dawn - pink and purple tints
            dawn = t / 0.3
            self.water_deep = self.lerp_color((60, 50, 80), (40, 70, 100), dawn)
            self.water_mid = self.lerp_color((80, 70, 110), (60, 100, 130), dawn)
            self.water_light = self.lerp_color((120, 100, 140), (100, 140, 170), dawn)
            self.water_highlight = self.lerp_color((180, 150, 180), (160, 190, 210), dawn)
        elif t < 0.7:
            # Day - classic blue-greens
            self.water_deep = (40, 70, 100)
            self.water_mid = (60, 100, 130)
            self.water_light = (100, 140, 170)
            self.water_highlight = (160, 190, 210)
        else:
            # Dusk - golden and orange tints
            dusk = (t - 0.7) / 0.3
            self.water_deep = self.lerp_color((40, 70, 100), (80, 60, 70), dusk)
            self.water_mid = self.lerp_color((60, 100, 130), (120, 90, 80), dusk)
            self.water_light = self.lerp_color((100, 140, 170), (160, 120, 100), dusk)
            self.water_highlight = self.lerp_color((160, 190, 210), (200, 160, 120), dusk)

        # Lily pad greens (also affected by lighting)
        if t < 0.3:
            self.pad_dark = (30, 60, 40)
            self.pad_mid = (50, 90, 55)
            self.pad_light = (70, 120, 70)
        elif t < 0.7:
            self.pad_dark = (35, 70, 45)
            self.pad_mid = (55, 100, 60)
            self.pad_light = (80, 130, 75)
        else:
            self.pad_dark = (50, 65, 40)
            self.pad_mid = (75, 90, 50)
            self.pad_light = (100, 115, 60)

    def generate_lily_pads(self):
        """Generate lily pads with flowers, spread out across the pond."""
        self.lily_pads = []

        num_pads = random.randint(8, 12)

        # Use a grid-based approach to spread pads out
        # Divide screen into regions and place one pad per region
        grid_size = int(math.ceil(math.sqrt(num_pads)))
        cell_w = GRID_SIZE / grid_size
        cell_h = GRID_SIZE / grid_size

        positions = []
        for gy in range(grid_size):
            for gx in range(grid_size):
                # Random position within each cell, with padding from edges
                x = cell_w * gx + random.uniform(cell_w * 0.2, cell_w * 0.8)
                y = cell_h * gy + random.uniform(cell_h * 0.2, cell_h * 0.8)
                positions.append((x, y))

        # Shuffle and take only the number we need
        random.shuffle(positions)
        positions = positions[:num_pads]

        for x, y in positions:
            pad = {
                'x': x,
                'y': y,
                'radius': random.uniform(4, 7),
                'angle': random.uniform(0, math.pi * 2),
                'notch_angle': random.uniform(0, math.pi * 2),  # The "bite" in the lily pad
                'drift_offset': random.uniform(0, math.pi * 2),
                'bob_offset': random.uniform(0, math.pi * 2),
                'has_flower': random.random() < 0.7,
                'flower_type': random.choice(['white', 'pink', 'yellow']),
                'flower_stage': random.uniform(0.5, 1.0),  # How open the flower is
                'ripple_timer': random.uniform(0, 5),  # Timer for creating ripples
            }
            self.lily_pads.append(pad)

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.up:
            self.drift_speed = min(3.0, self.drift_speed + 0.1)
            consumed = True
        if input_state.down:
            self.drift_speed = max(0.2, self.drift_speed - 0.1)
            consumed = True

        if input_state.left:
            self.time_of_day = (self.time_of_day - 0.02) % 1.0
            self.update_palette()
            consumed = True
        if input_state.right:
            self.time_of_day = (self.time_of_day + 0.02) % 1.0
            self.update_palette()
            consumed = True

        if input_state.action:
            # Add a ripple at center
            self.ripples.append({
                'x': GRID_SIZE // 2,
                'y': GRID_SIZE // 2,
                'radius': 0,
                'max_radius': 25,
                'strength': 1.0,
            })
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt * self.drift_speed

        # Update lily pad positions (gentle drift)
        for pad in self.lily_pads:
            # Circular drifting motion
            drift_x = math.sin(self.time * 0.3 + pad['drift_offset']) * 0.5
            drift_y = math.cos(self.time * 0.2 + pad['drift_offset']) * 0.3
            pad['x'] += drift_x * dt * self.drift_speed
            pad['y'] += drift_y * dt * self.drift_speed

            # Gentle rotation
            pad['angle'] += math.sin(self.time * 0.5 + pad['drift_offset']) * 0.01

            # Lily pads create ripples from their centers
            pad['ripple_timer'] = pad.get('ripple_timer', 0) + dt
            ripple_interval = random.uniform(3.0, 7.0)
            if pad['ripple_timer'] > ripple_interval:
                pad['ripple_timer'] = 0
                self.ripples.append({
                    'x': pad['x'],
                    'y': pad['y'],
                    'radius': 0,
                    'max_radius': random.uniform(8, 15),
                    'strength': random.uniform(0.2, 0.5),
                })

            # Wrap around screen
            if pad['x'] < -pad['radius']:
                pad['x'] = GRID_SIZE + pad['radius']
            elif pad['x'] > GRID_SIZE + pad['radius']:
                pad['x'] = -pad['radius']
            if pad['y'] < -pad['radius']:
                pad['y'] = GRID_SIZE + pad['radius']
            elif pad['y'] > GRID_SIZE + pad['radius']:
                pad['y'] = -pad['radius']

        # Update ripples
        for ripple in self.ripples:
            ripple['radius'] += dt * 20
            ripple['strength'] *= 0.97

        # Remove faded ripples
        self.ripples = [r for r in self.ripples if r['strength'] > 0.05 and r['radius'] < r['max_radius']]

        # Ambient ripples
        self.ambient_ripple_timer += dt
        if self.ambient_ripple_timer > random.uniform(2.0, 5.0):
            self.ambient_ripple_timer = 0
            self.ripples.append({
                'x': random.uniform(10, GRID_SIZE - 10),
                'y': random.uniform(10, GRID_SIZE - 10),
                'radius': 0,
                'max_radius': random.uniform(10, 20),
                'strength': random.uniform(0.3, 0.6),
            })

    def draw(self):
        # Draw water background
        self.draw_water()

        # Sort lily pads by y position for proper overlap
        sorted_pads = sorted(self.lily_pads, key=lambda p: p['y'])

        # Draw lily pads and flowers
        for pad in sorted_pads:
            self.draw_lily_pad(pad)
            if pad['has_flower']:
                self.draw_flower(pad)

    def draw_water(self):
        """Draw the water surface with impressionistic effect."""
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                # Base water color with depth variation
                depth_noise = math.sin(x * 0.3 + y * 0.2 + self.time) * 0.5 + 0.5

                # Add ripple effects
                ripple_offset = 0
                for ripple in self.ripples:
                    dist = math.sqrt((x - ripple['x'])**2 + (y - ripple['y'])**2)
                    if abs(dist - ripple['radius']) < 3:
                        wave = math.sin((dist - ripple['radius']) * 2) * ripple['strength']
                        ripple_offset += wave * 0.3

                # Combine noise sources for impressionistic effect
                noise1 = math.sin(x * 0.4 + self.time * 0.5) * math.cos(y * 0.3 + self.time * 0.3)
                noise2 = math.sin((x + y) * 0.2 + self.time * 0.7) * 0.5
                combined = (depth_noise + noise1 * 0.3 + noise2 * 0.2 + ripple_offset) / 1.5

                # Select base color based on combined value
                if combined < 0.3:
                    color = self.water_deep
                elif combined < 0.5:
                    t = (combined - 0.3) / 0.2
                    color = self.lerp_color(self.water_deep, self.water_mid, t)
                elif combined < 0.7:
                    t = (combined - 0.5) / 0.2
                    color = self.lerp_color(self.water_mid, self.water_light, t)
                else:
                    t = (combined - 0.7) / 0.3
                    color = self.lerp_color(self.water_light, self.water_highlight, min(1, t))

                # Impressionistic color variations - like brushstrokes
                # Multiple overlapping noise patterns at different scales
                micro_noise = math.sin(x * 1.7 + y * 1.3 + self.time * 0.8)
                brush_noise = math.sin(x * 0.8 - y * 0.6 + self.time * 0.4) * math.cos(x * 0.5 + y * 0.9)
                detail_noise = math.sin((x * 2.1 + self.time) * 0.7) * math.sin((y * 1.9 - self.time) * 0.6)

                # Combine for varied brushstroke effect
                variation = (micro_noise * 0.4 + brush_noise * 0.35 + detail_noise * 0.25)

                # Slight hue shifts - more blue in shadows, more green in highlights
                hue_shift_r = variation * 12
                hue_shift_g = variation * 8 + math.sin(x * 0.3 + y * 0.4 + self.time * 0.6) * 6
                hue_shift_b = -variation * 6 + math.cos(x * 0.25 + y * 0.35 + self.time * 0.5) * 8

                # Apply variations with clamping
                color = (
                    max(0, min(255, int(color[0] + hue_shift_r))),
                    max(0, min(255, int(color[1] + hue_shift_g))),
                    max(0, min(255, int(color[2] + hue_shift_b))),
                )

                self.display.set_pixel(x, y, color)

    def draw_lily_pad(self, pad):
        """Draw a single lily pad."""
        cx, cy = pad['x'], pad['y']
        radius = pad['radius']
        notch_angle = pad['notch_angle'] + pad['angle']

        # Bobbing effect
        bob = math.sin(self.time * 2 + pad['bob_offset']) * 0.5

        for dy in range(-int(radius) - 1, int(radius) + 2):
            for dx in range(-int(radius) - 1, int(radius) + 2):
                px, py = cx + dx, cy + dy + bob

                if not (0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE):
                    continue

                # Check if point is within pad (with notch)
                dist = math.sqrt(dx * dx + dy * dy)
                if dist > radius:
                    continue

                # Create notch (wedge cut out)
                angle = math.atan2(dy, dx)
                angle_diff = abs(((angle - notch_angle + math.pi) % (2 * math.pi)) - math.pi)
                if angle_diff < 0.4 and dist > radius * 0.3:
                    continue

                # Color based on position (center lighter)
                dist_ratio = dist / radius

                # Add vein pattern
                vein_angle = (angle - pad['angle']) * 6
                is_vein = abs(math.sin(vein_angle)) < 0.15 and dist > radius * 0.2

                if dist_ratio < 0.3:
                    color = self.pad_light
                elif dist_ratio < 0.7:
                    color = self.pad_mid if not is_vein else self.pad_dark
                else:
                    color = self.pad_dark

                # Edge highlight
                if dist > radius - 1:
                    color = self.lerp_color(color, self.pad_light, 0.3)

                self.display.set_pixel(int(px), int(py), color)

    def draw_flower(self, pad):
        """Draw a water lily flower on a pad."""
        cx = pad['x']
        cy = pad['y'] - 1  # Slightly above pad center
        bob = math.sin(self.time * 2 + pad['bob_offset']) * 0.5
        cy += bob

        flower_type = pad['flower_type']
        stage = pad['flower_stage']

        # Flower colors
        if flower_type == 'white':
            petal_outer = (255, 255, 250)
            petal_inner = (255, 250, 230)
            center = (255, 220, 100)
        elif flower_type == 'pink':
            petal_outer = (255, 180, 200)
            petal_inner = (255, 210, 220)
            center = (255, 230, 120)
        else:  # yellow
            petal_outer = (255, 240, 150)
            petal_inner = (255, 250, 200)
            center = (255, 200, 80)

        # Draw petals
        num_petals = 8
        petal_length = 2 + stage * 2

        for i in range(num_petals):
            angle = (i / num_petals) * math.pi * 2 + pad['angle'] + self.time * 0.1
            # Outer petals
            for d in range(1, int(petal_length) + 1):
                px = cx + math.cos(angle) * d * stage
                py = cy + math.sin(angle) * d * 0.7 * stage  # Slightly flattened

                if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                    # Gradient from inner to outer
                    t = d / petal_length
                    color = self.lerp_color(petal_inner, petal_outer, t)
                    self.display.set_pixel(int(px), int(py), color)

        # Inner petals (smaller, rotated)
        for i in range(num_petals):
            angle = (i / num_petals) * math.pi * 2 + pad['angle'] + math.pi / num_petals + self.time * 0.1
            for d in range(1, int(petal_length * 0.6) + 1):
                px = cx + math.cos(angle) * d * stage
                py = cy + math.sin(angle) * d * 0.7 * stage

                if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                    self.display.set_pixel(int(px), int(py), petal_inner)

        # Center of flower
        if 0 <= cx < GRID_SIZE and 0 <= cy < GRID_SIZE:
            self.display.set_pixel(int(cx), int(cy), center)
            # Slightly larger center for bigger flowers
            if stage > 0.7:
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    px, py = int(cx + dx), int(cy + dy)
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        self.display.set_pixel(px, py, center)

    def lerp_color(self, c1, c2, t):
        """Linearly interpolate between two colors."""
        t = max(0, min(1, t))
        return (
            int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t),
        )
