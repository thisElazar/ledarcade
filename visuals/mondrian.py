"""
Mondrian - Procedural geometric composition
============================================
A procedural Piet Mondrian-style composition with geometric grids
and primary color blocks, inspired by his neoplastic art movement.

Controls:
  Left/Right - Adjust animation speed (breathing/regeneration)
  Up/Down    - Cycle color palette (classic, pastel, neon, monochrome)
  Space      - Generate new composition
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE


class Mondrian(Visual):
    name = "MONDRIAN"
    description = "Geometric composition"
    category = "art"

    # Color palettes
    PALETTES = [
        {
            'name': 'classic',
            'red': (255, 0, 0),
            'blue': (0, 0, 180),
            'yellow': (255, 220, 0),
            'white': (255, 255, 250),
            'black': (0, 0, 0),
        },
        {
            'name': 'pastel',
            'red': (255, 150, 150),
            'blue': (150, 180, 255),
            'yellow': (255, 255, 180),
            'white': (255, 255, 255),
            'black': (80, 80, 80),
        },
        {
            'name': 'neon',
            'red': (255, 50, 100),
            'blue': (50, 100, 255),
            'yellow': (255, 255, 50),
            'white': (200, 200, 200),
            'black': (20, 20, 40),
        },
        {
            'name': 'monochrome',
            'red': (40, 40, 40),
            'blue': (80, 80, 80),
            'yellow': (160, 160, 160),
            'white': (255, 255, 255),
            'black': (0, 0, 0),
        },
    ]

    # Minimum rectangle size for subdivision
    MIN_SIZE = 8

    # Line thickness
    LINE_WIDTH = 2

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.animation_speed = 1.0
        self.palette_index = 0
        self.palette = self.PALETTES[0]

        # Breathing animation phase
        self.breath_phase = 0.0

        # Regeneration timer
        self.regen_timer = 0.0
        self.regen_interval = 15.0  # Seconds between auto-regeneration

        # Generate initial composition
        self.rectangles = []
        self.generate_composition()

    def generate_composition(self):
        """Generate a new Mondrian-style composition using recursive subdivision."""
        self.rectangles = []

        # Start with the full canvas (leaving room for border lines)
        initial_rect = {
            'x': self.LINE_WIDTH,
            'y': self.LINE_WIDTH,
            'w': GRID_SIZE - 2 * self.LINE_WIDTH,
            'h': GRID_SIZE - 2 * self.LINE_WIDTH,
        }

        # Recursively subdivide
        self._subdivide(initial_rect, depth=0)

        # Assign colors to rectangles
        self._assign_colors()

    def _subdivide(self, rect, depth):
        """Recursively subdivide a rectangle."""
        x, y, w, h = rect['x'], rect['y'], rect['w'], rect['h']

        # Stop conditions: too small or random chance to stop (increases with depth)
        if w < self.MIN_SIZE * 2 or h < self.MIN_SIZE * 2:
            self.rectangles.append(rect)
            return

        stop_chance = 0.1 + depth * 0.15
        if random.random() < stop_chance:
            self.rectangles.append(rect)
            return

        # Decide split direction based on aspect ratio with some randomness
        if w > h * 1.5:
            split_horizontal = False  # Split vertically (make it less wide)
        elif h > w * 1.5:
            split_horizontal = True  # Split horizontally (make it less tall)
        else:
            split_horizontal = random.random() < 0.5

        if split_horizontal:
            # Horizontal split
            min_split = max(self.MIN_SIZE, int(h * 0.25))
            max_split = min(h - self.MIN_SIZE, int(h * 0.75))
            if min_split >= max_split:
                self.rectangles.append(rect)
                return

            split_pos = random.randint(min_split, max_split)

            rect1 = {'x': x, 'y': y, 'w': w, 'h': split_pos - self.LINE_WIDTH}
            rect2 = {'x': x, 'y': y + split_pos, 'w': w, 'h': h - split_pos}
        else:
            # Vertical split
            min_split = max(self.MIN_SIZE, int(w * 0.25))
            max_split = min(w - self.MIN_SIZE, int(w * 0.75))
            if min_split >= max_split:
                self.rectangles.append(rect)
                return

            split_pos = random.randint(min_split, max_split)

            rect1 = {'x': x, 'y': y, 'w': split_pos - self.LINE_WIDTH, 'h': h}
            rect2 = {'x': x + split_pos, 'y': y, 'w': w - split_pos, 'h': h}

        # Recursively subdivide the new rectangles
        self._subdivide(rect1, depth + 1)
        self._subdivide(rect2, depth + 1)

    def _assign_colors(self):
        """Assign colors to rectangles - most white, some primary colors."""
        # Calculate total area
        total_area = sum(r['w'] * r['h'] for r in self.rectangles)

        # Sort by area (larger rectangles more likely to get color)
        sorted_rects = sorted(self.rectangles, key=lambda r: r['w'] * r['h'], reverse=True)

        # Assign colors
        color_budget = {'red': 1, 'blue': 1, 'yellow': 1}
        extra_colors = random.randint(0, 2)
        for _ in range(extra_colors):
            color = random.choice(['red', 'blue', 'yellow'])
            color_budget[color] += 1

        for rect in sorted_rects:
            rect_area = rect['w'] * rect['h']
            area_ratio = rect_area / total_area

            # Larger rectangles have higher chance of getting color
            color_chance = 0.3 + area_ratio * 2

            assigned_color = 'white'

            if random.random() < color_chance:
                # Try to assign a primary color
                available_colors = [c for c, count in color_budget.items() if count > 0]
                if available_colors:
                    chosen = random.choice(available_colors)
                    color_budget[chosen] -= 1
                    assigned_color = chosen

            rect['color'] = assigned_color
            rect['breath_offset'] = random.uniform(0, math.pi * 2)

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.left:
            self.animation_speed = max(0.2, self.animation_speed - 0.1)
            consumed = True
        if input_state.right:
            self.animation_speed = min(3.0, self.animation_speed + 0.1)
            consumed = True

        if input_state.up:
            self.palette_index = (self.palette_index - 1) % len(self.PALETTES)
            self.palette = self.PALETTES[self.palette_index]
            consumed = True
        if input_state.down:
            self.palette_index = (self.palette_index + 1) % len(self.PALETTES)
            self.palette = self.PALETTES[self.palette_index]
            consumed = True

        if input_state.action:
            self.generate_composition()
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt * self.animation_speed

        # Update breathing phase
        self.breath_phase = self.time * 0.5

        # Auto-regeneration timer
        self.regen_timer += dt * self.animation_speed
        if self.regen_timer >= self.regen_interval:
            self.regen_timer = 0.0
            self.generate_composition()

    def draw(self):
        # Fill background with black (the grid lines)
        self.display.clear(self.palette['black'])

        # Draw each rectangle
        for rect in self.rectangles:
            self._draw_rectangle(rect)

    def _draw_rectangle(self, rect):
        """Draw a single rectangle with its color and breathing effect."""
        x, y, w, h = rect['x'], rect['y'], rect['w'], rect['h']
        color_name = rect['color']
        base_color = self.palette[color_name]

        # Apply breathing effect (subtle brightness pulse)
        breath = math.sin(self.breath_phase + rect['breath_offset'])
        breath_amount = 0.05  # Subtle effect

        if color_name == 'white':
            # White rectangles breathe less noticeably
            brightness = 1.0 + breath * breath_amount * 0.5
        else:
            # Colored rectangles have more visible breathing
            brightness = 1.0 + breath * breath_amount

        # Apply brightness
        color = (
            max(0, min(255, int(base_color[0] * brightness))),
            max(0, min(255, int(base_color[1] * brightness))),
            max(0, min(255, int(base_color[2] * brightness))),
        )

        # Draw filled rectangle
        for py in range(y, y + h):
            for px in range(x, x + w):
                if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                    self.display.set_pixel(px, py, color)

    def lerp_color(self, c1, c2, t):
        """Linearly interpolate between two colors."""
        t = max(0, min(1, t))
        return (
            int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t),
        )
