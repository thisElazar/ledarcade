"""
Archimedes' Screw
=================
One of the oldest machines still in use today (c. 250 BC). A helical screw
inside a tube, when rotated, lifts water from a lower level to a higher level.
Used for irrigation, draining mines, and moving grain. Elegantly simple
demonstration of mechanical advantage.

Side-view cutaway showing:
- Angled tube/cylinder from bottom-left to upper-right
- Helical screw blade visible inside (rotating diagonal lines)
- Water pockets trapped between screw flights rise as screw turns
- Pool of water at bottom, stream/drops at top output
- Hand crank at top driving the rotation

Controls:
  Left/Right - Adjust rotation speed (6 levels)
"""

import math
from . import Visual, Display, Colors, GRID_SIZE


# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------
WOOD = (140, 100, 60)
WOOD_DARK = (100, 70, 40)
BRONZE = (180, 140, 60)
BRONZE_DARK = (130, 100, 40)
BRONZE_LIGHT = (210, 170, 90)
WATER = (60, 120, 200)
WATER_LIGHT = (100, 160, 230)
WATER_DARK = (40, 80, 160)
TUBE_COLOR = (120, 90, 50)
TUBE_EDGE = (90, 65, 35)
SCREW_BLADE = (160, 125, 70)
SCREW_EDGE = (200, 160, 100)
HUD_COLOR = (160, 160, 170)
CRANK_COLOR = (180, 140, 60)
GROUND = (80, 60, 40)
POOL_BED = (50, 40, 30)

# Speed levels (rotations per minute)
SPEED_RPMS = [15, 30, 45, 60, 90, 120]


class Archimedes(Visual):
    name = "ARCHIMEDES"
    description = "Ancient water screw"
    category = "mechanics"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.theta = 0.0  # Screw rotation angle in radians
        self.speed_level = 3  # 1-6
        self.rpm = SPEED_RPMS[self.speed_level - 1]

        # Water particles moving through the screw
        # Each particle has a phase (0.0 to 1.0 = position along screw)
        self.water_particles = []
        self._spawn_particles()

        # Water drops at output
        self.drops = []  # [(x, y, vy), ...]

    def _spawn_particles(self):
        """Initialize water particles at various phases along the screw."""
        self.water_particles = []
        # Spawn particles at regular intervals
        for i in range(6):
            phase = i / 6.0
            self.water_particles.append(phase)

    def handle_input(self, input_state):
        consumed = False
        if input_state.right_pressed:
            self.speed_level = min(6, self.speed_level + 1)
            self.rpm = SPEED_RPMS[self.speed_level - 1]
            consumed = True
        elif input_state.left_pressed:
            self.speed_level = max(1, self.speed_level - 1)
            self.rpm = SPEED_RPMS[self.speed_level - 1]
            consumed = True
        return consumed

    def update(self, dt):
        self.time += dt

        # Rotate screw
        omega = (self.rpm / 60.0) * 2.0 * math.pi
        self.theta += omega * dt

        # Move water particles through the screw
        # Particles advance based on screw rotation
        particle_speed = (self.rpm / 60.0) * dt * 0.5  # Phase advance per frame
        new_particles = []
        for phase in self.water_particles:
            phase += particle_speed
            if phase >= 1.0:
                # Particle exits at top - spawn drop
                self._spawn_drop()
                # Respawn at bottom
                phase = 0.0
            new_particles.append(phase)
        self.water_particles = new_particles

        # Update drops (falling water at output)
        new_drops = []
        for x, y, vy in self.drops:
            y += vy * dt
            vy += 120 * dt  # Gravity
            if y < 64:
                new_drops.append((x, y, vy))
        self.drops = new_drops

    def _spawn_drop(self):
        """Spawn a water drop at the output."""
        # Output is at top-right of screw
        x = 54 + (self.time * 7) % 3 - 1  # Slight variation
        y = 10
        vy = 20 + (self.theta % 10)  # Initial downward velocity
        self.drops.append((x, y, vy))

    def draw(self):
        d = self.display
        d.clear(Colors.BLACK)

        # --- Screw geometry ---
        # Screw runs from bottom-left to top-right at ~35 degree angle
        # Bottom end: (8, 54), Top end: (56, 14)
        screw_x1, screw_y1 = 8, 54   # Bottom (in water)
        screw_x2, screw_y2 = 56, 14  # Top (output)

        # Draw order: back to front

        # 1. Background ground/earth on sides
        self._draw_ground(d)

        # 2. Water pool at bottom
        self._draw_water_pool(d)

        # 3. Tube/cylinder (back half - before screw)
        self._draw_tube_back(d, screw_x1, screw_y1, screw_x2, screw_y2)

        # 4. Water pockets inside screw
        self._draw_water_pockets(d, screw_x1, screw_y1, screw_x2, screw_y2)

        # 5. Screw blades (helical lines)
        self._draw_screw_blades(d, screw_x1, screw_y1, screw_x2, screw_y2)

        # 6. Tube edges (front)
        self._draw_tube_front(d, screw_x1, screw_y1, screw_x2, screw_y2)

        # 7. Hand crank at top
        self._draw_crank(d, screw_x2, screw_y2)

        # 8. Water output (drops/stream)
        self._draw_output(d)

        # 9. Support frame
        self._draw_frame(d, screw_x1, screw_y1, screw_x2, screw_y2)

        # 10. HUD
        self._draw_hud(d)

    def _draw_ground(self, d):
        """Draw ground/earth at bottom and sides."""
        # Bottom ground
        d.draw_rect(0, 58, 64, 6, GROUND)
        # Left bank
        for y in range(52, 64):
            width = (y - 52) // 2 + 2
            d.draw_rect(0, y, width, 1, GROUND)
        # Right bank (elevated for output)
        for y in range(20, 64):
            width = max(0, (y - 40) // 3)
            if width > 0:
                d.draw_rect(64 - width, y, width, 1, GROUND)

    def _draw_water_pool(self, d):
        """Draw water pool at bottom-left."""
        # Pool bed
        d.draw_rect(2, 56, 20, 2, POOL_BED)
        # Water surface with slight wave
        wave_offset = int(math.sin(self.time * 3) * 0.5)
        for x in range(3, 22):
            # Water column
            depth = 4 + int(math.sin(x * 0.5 + self.time * 2) * 0.8)
            for y in range(52 + wave_offset, 56):
                shade = WATER if (x + y) % 3 != 0 else WATER_LIGHT
                d.set_pixel(x, y, shade)
        # Surface highlight
        for x in range(4, 20, 2):
            y = 52 + wave_offset
            d.set_pixel(x, y, WATER_LIGHT)

    def _draw_tube_back(self, d, x1, y1, x2, y2):
        """Draw the back portion of the tube (behind screw blades)."""
        # Tube is ~8 pixels diameter
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx * dx + dy * dy)
        steps = int(length)

        # Perpendicular offset for tube width
        perp_x = -dy / length * 4
        perp_y = dx / length * 4

        for i in range(steps):
            t = i / steps
            cx = x1 + dx * t
            cy = y1 + dy * t
            # Draw tube interior (dark)
            for offset in range(-3, 4):
                px = int(cx + perp_x * offset / 4)
                py = int(cy + perp_y * offset / 4)
                if 0 <= px < 64 and 0 <= py < 64:
                    # Darker towards edges
                    if abs(offset) >= 3:
                        d.set_pixel(px, py, TUBE_EDGE)
                    else:
                        d.set_pixel(px, py, TUBE_COLOR)

    def _draw_water_pockets(self, d, x1, y1, x2, y2):
        """Draw water pockets moving through the screw."""
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx * dx + dy * dy)

        # Perpendicular for pocket positioning
        perp_x = -dy / length
        perp_y = dx / length

        for phase in self.water_particles:
            # Position along screw
            t = phase
            cx = x1 + dx * t
            cy = y1 + dy * t

            # Water pocket (small cluster of blue pixels)
            # Pocket rotates with screw and sits in lower part of tube
            pocket_angle = self.theta + phase * math.pi * 4  # Multiple turns
            # Water settles toward bottom of tube cross-section
            offset = math.sin(pocket_angle) * 1.5

            for px_off in range(-1, 2):
                for py_off in range(-1, 2):
                    px = int(cx + perp_x * offset + px_off)
                    py = int(cy + perp_y * offset + py_off)
                    if 0 <= px < 64 and 0 <= py < 64:
                        # Brighter center
                        color = WATER_LIGHT if px_off == 0 and py_off == 0 else WATER
                        d.set_pixel(px, py, color)

    def _draw_screw_blades(self, d, x1, y1, x2, y2):
        """Draw the helical screw blades inside the tube."""
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx * dx + dy * dy)
        steps = int(length)

        # Perpendicular offset for blade extent
        perp_x = -dy / length
        perp_y = dx / length

        # Number of blade turns visible
        num_turns = 4

        for i in range(steps):
            t = i / steps
            cx = x1 + dx * t
            cy = y1 + dy * t

            # Blade angle at this position (changes along length and with rotation)
            blade_angle = self.theta + t * num_turns * 2 * math.pi

            # Blade visible when facing toward/away from viewer
            visibility = math.sin(blade_angle)

            if abs(visibility) > 0.3:
                # Draw blade edge
                blade_extent = visibility * 3  # How far blade extends
                px = int(cx + perp_x * blade_extent)
                py = int(cy + perp_y * blade_extent)

                if 0 <= px < 64 and 0 <= py < 64:
                    # Blade color varies with angle for 3D effect
                    if visibility > 0:
                        d.set_pixel(px, py, SCREW_EDGE)
                    else:
                        d.set_pixel(px, py, SCREW_BLADE)

    def _draw_tube_front(self, d, x1, y1, x2, y2):
        """Draw tube edges (front portion visible)."""
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx * dx + dy * dy)

        # Perpendicular offset
        perp_x = -dy / length * 4
        perp_y = dx / length * 4

        # Top edge of tube
        for i in range(int(length)):
            t = i / length
            cx = x1 + dx * t
            cy = y1 + dy * t
            px = int(cx + perp_x)
            py = int(cy + perp_y)
            if 0 <= px < 64 and 0 <= py < 64:
                d.set_pixel(px, py, WOOD)

        # Bottom edge of tube
        for i in range(int(length)):
            t = i / length
            cx = x1 + dx * t
            cy = y1 + dy * t
            px = int(cx - perp_x)
            py = int(cy - perp_y)
            if 0 <= px < 64 and 0 <= py < 64:
                d.set_pixel(px, py, WOOD_DARK)

    def _draw_crank(self, d, x2, y2):
        """Draw hand crank at top of screw."""
        # Hub at screw axis end
        d.draw_circle(x2, y2, 2, BRONZE, filled=True)

        # Crank arm rotates with screw
        arm_length = 6
        arm_x = int(x2 + arm_length * math.cos(self.theta))
        arm_y = int(y2 + arm_length * math.sin(self.theta))
        d.draw_line(x2, y2, arm_x, arm_y, BRONZE)

        # Handle at end of arm
        d.set_pixel(arm_x, arm_y, BRONZE_LIGHT)
        if 0 <= arm_x + 1 < 64:
            d.set_pixel(arm_x + 1, arm_y, WOOD)
        if 0 <= arm_y + 1 < 64:
            d.set_pixel(arm_x, arm_y + 1, WOOD)

    def _draw_output(self, d):
        """Draw water output stream and drops."""
        # Output spout
        d.draw_rect(54, 15, 4, 2, WOOD_DARK)

        # Falling water drops
        for x, y, vy in self.drops:
            ix, iy = int(x), int(y)
            if 0 <= ix < 64 and 0 <= iy < 64:
                d.set_pixel(ix, iy, WATER_LIGHT)
                if iy + 1 < 64:
                    d.set_pixel(ix, iy + 1, WATER)

        # Water stream at output (continuous drip effect)
        stream_y = 17 + int((self.time * 30) % 8)
        if stream_y < 25:
            d.set_pixel(55, stream_y, WATER_LIGHT)
            d.set_pixel(56, stream_y + 1, WATER)

        # Collected water at bottom right
        for x in range(52, 60):
            for y in range(55, 58):
                if (x + y + int(self.time * 5)) % 3 != 0:
                    d.set_pixel(x, y, WATER_DARK)

    def _draw_frame(self, d, x1, y1, x2, y2):
        """Draw wooden support frame."""
        # Support legs
        # Left leg (under bottom of screw)
        d.draw_line(x1 + 5, y1 - 2, x1 + 3, 58, WOOD_DARK)
        # Right leg (under top of screw)
        d.draw_line(x2 - 5, y2 + 5, x2 - 8, 40, WOOD_DARK)

        # Horizontal brace
        d.draw_line(x1 + 3, 48, x2 - 8, 35, WOOD_DARK)

    def _draw_hud(self, d):
        """Draw RPM display."""
        d.draw_text_small(2, 1, f"{self.rpm}RPM", HUD_COLOR)

        # Speed level indicator (small dots)
        for i in range(6):
            dx = 50 + i * 2
            if i < self.speed_level:
                d.set_pixel(dx, 2, BRONZE_LIGHT)
            else:
                d.set_pixel(dx, 2, (50, 50, 55))
