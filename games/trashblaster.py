"""
TrashBlaster - Zap floating trash from your spaceship!
======================================================
Inspired by MathBlasters. You're piloting an alien vessel through a debris
field. Look through your cockpit window and use your targeting crosshair
to blast floating trash. Move the crosshair with the joystick and fire
with the action button! Score as many points as you can in 2 minutes!

Controls:
  Arrow Keys - Move targeting crosshair
  Space/Action - Fire laser at crosshair position
"""

import random
import math
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


class Trash:
    """A floating piece of trash in space."""
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.size = 1  # 1=small, 2=medium, 3=large
        self.shape = "can"
        self.color = (100, 100, 100)
        self.points = 10
        self.alive = True
        self.rotation = 0.0
        self.rot_speed = 0.0

    def get_radius(self):
        """Get collision radius based on size."""
        return self.size + 1

    def get_pixels(self):
        """Return list of (dx, dy, color) offsets for this trash shape."""
        pixels = []
        c = self.color
        bright = (min(255, c[0] + 50), min(255, c[1] + 50), min(255, c[2] + 50))
        darker = (c[0] * 2 // 3, c[1] * 2 // 3, c[2] * 2 // 3)

        if self.size == 1:  # Small - bottle cap / wrapper scrap
            pixels = [
                (0, 0, bright), (1, 0, c),
                (0, 1, c), (1, 1, bright),
            ]
        elif self.size == 2:  # Medium - crushed can / bottle
            # Can shape with highlight
            pixels = [
                        (1, 0, bright),
                (0, 1, c), (1, 1, bright), (2, 1, c),
                (0, 2, c), (1, 2, c), (2, 2, darker),
                        (1, 3, darker),
            ]
        else:  # Large - box / crumpled junk
            # Irregular box shape
            pixels = [
                (0, 0, darker), (1, 0, c), (2, 0, bright), (3, 0, c),
                (0, 1, c), (1, 1, bright), (2, 1, c), (3, 1, darker),
                (0, 2, bright), (1, 2, c), (2, 2, c),
                (0, 3, c), (1, 3, darker), (2, 3, darker), (3, 3, darker),
            ]

        # Center the shape
        offset = self.size
        return [(dx - offset, dy - offset, col) for dx, dy, col in pixels]


class Explosion:
    """A colorful starburst explosion."""
    def __init__(self, x, y, size=1):
        self.x = x
        self.y = y
        self.time = 0.0
        self.duration = 0.4 + size * 0.1
        self.size = size
        self.particles = []
        self.alive = True

        num_particles = 8 + size * 4
        colors = [
            (255, 100, 50),   # Orange
            (255, 255, 100),  # Yellow
            (255, 50, 50),    # Red
            (100, 255, 100),  # Green
            (100, 200, 255),  # Cyan
        ]
        for i in range(num_particles):
            angle = i * 2 * math.pi / num_particles + random.uniform(-0.3, 0.3)
            speed = random.uniform(20, 40) * (1 + size * 0.3)
            self.particles.append({
                'angle': angle,
                'speed': speed,
                'color': random.choice(colors),
            })

    def update(self, dt):
        self.time += dt
        if self.time >= self.duration:
            self.alive = False

    def get_pixels(self):
        if not self.alive:
            return []

        pixels = []
        progress = self.time / self.duration
        radius = progress * (5 + self.size * 2)
        fade = 1.0 - progress

        for p in self.particles:
            px = self.x + math.cos(p['angle']) * radius
            py = self.y + math.sin(p['angle']) * radius
            c = p['color']
            faded = (int(c[0] * fade), int(c[1] * fade), int(c[2] * fade))
            if 0 <= int(px) < GRID_SIZE and 0 <= int(py) < GRID_SIZE:
                pixels.append((int(px), int(py), faded))

        return pixels


class FloatingScore:
    """A score that floats up and fades."""
    def __init__(self, x, y, points):
        self.x = x
        self.y = y
        self.points = points
        self.time = 0.0
        self.duration = 0.8
        self.alive = True

        if points >= 30:
            self.color = (255, 255, 100)  # Gold
        elif points >= 20:
            self.color = (100, 255, 100)  # Green
        else:
            self.color = (200, 200, 255)  # Light blue

    def update(self, dt):
        self.time += dt
        self.y -= 12 * dt
        if self.time >= self.duration:
            self.alive = False


class LaserBlast:
    """A laser shot from crosshair to target."""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.time = 0.0
        self.duration = 0.2
        self.alive = True

    def update(self, dt):
        self.time += dt
        if self.time >= self.duration:
            self.alive = False


class TrashBlaster(Game):
    name = "TRASHBLASTER"
    description = "Blast the trash!"
    category = "retro"

    TRASH_COLORS = [
        (180, 180, 180),  # Bright gray (tin can)
        (200, 140, 80),   # Orange-brown (cardboard)
        (120, 200, 120),  # Bright green (bottle)
        (180, 100, 180),  # Purple (plastic)
        (200, 200, 100),  # Yellow (wrapper)
        (100, 180, 220),  # Cyan (container)
    ]

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.time = 0.0
        self.time_limit = 120.0
        self.time_remaining = 120.0
        self.score = 0
        self.trash = []
        self.explosions = []
        self.floating_scores = []
        self.laser_blasts = []

        # Crosshair position (center of screen initially)
        self.crosshair_x = GRID_SIZE // 2
        self.crosshair_y = GRID_SIZE // 2
        self.crosshair_speed = 40  # Pixels per second

        # Movement accumulator for smooth diagonal movement
        self.move_accum_x = 0.0
        self.move_accum_y = 0.0

        # Fire cooldown
        self.fire_cooldown = 0.0
        self.fire_delay = 0.25  # Minimum time between shots

        # Spawn control
        self.spawn_timer = 0.0
        self.spawn_interval = 1.5
        self.difficulty_timer = 0.0

        # Cockpit viewport area (where trash can appear)
        self.viewport_margin = 8

        # Spawn initial trash
        for _ in range(5):
            self._spawn_trash()

    def _spawn_trash(self):
        """Spawn trash from edges of the viewport."""
        t = Trash()

        # Spawn from edges
        edge = random.choice(['top', 'bottom', 'left', 'right'])
        margin = self.viewport_margin

        if edge == 'top':
            t.x = random.uniform(margin, GRID_SIZE - margin)
            t.y = margin - 2
            t.vy = random.uniform(3, 10)
            t.vx = random.uniform(-3, 3)
        elif edge == 'bottom':
            t.x = random.uniform(margin, GRID_SIZE - margin)
            t.y = GRID_SIZE - margin + 2
            t.vy = random.uniform(-10, -3)
            t.vx = random.uniform(-3, 3)
        elif edge == 'left':
            t.x = margin - 2
            t.y = random.uniform(margin, GRID_SIZE - margin)
            t.vx = random.uniform(3, 10)
            t.vy = random.uniform(-3, 3)
        else:
            t.x = GRID_SIZE - margin + 2
            t.y = random.uniform(margin, GRID_SIZE - margin)
            t.vx = random.uniform(-10, -3)
            t.vy = random.uniform(-3, 3)

        # Random size and attributes
        t.size = random.choices([1, 2, 3], weights=[50, 35, 15])[0]
        t.color = random.choice(self.TRASH_COLORS)
        t.rot_speed = random.uniform(-2, 2)

        # Points based on size (smaller = harder to hit = more points)
        t.points = {1: 30, 2: 20, 3: 10}[t.size]

        self.trash.append(t)

    def _fire_at_crosshair(self):
        """Fire a laser at the current crosshair position."""
        if self.fire_cooldown > 0:
            return False

        self.fire_cooldown = self.fire_delay

        # Create laser blast effect at crosshair
        blast = LaserBlast(self.crosshair_x, self.crosshair_y)
        self.laser_blasts.append(blast)

        # Check for hits
        hit_trash = None
        for t in self.trash:
            if not t.alive:
                continue

            # Distance from crosshair to trash center
            dx = t.x - self.crosshair_x
            dy = t.y - self.crosshair_y
            dist = math.sqrt(dx * dx + dy * dy)

            # Hit if within radius
            if dist <= t.get_radius() + 1:
                hit_trash = t
                break

        if hit_trash:
            # Create explosion
            explosion = Explosion(hit_trash.x, hit_trash.y, hit_trash.size)
            self.explosions.append(explosion)

            # Create floating score
            score = FloatingScore(hit_trash.x, hit_trash.y, hit_trash.points)
            self.floating_scores.append(score)

            # Add to score
            self.score += hit_trash.points

            # Kill the trash
            hit_trash.alive = False
            return True

        return False

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        self.time += dt
        self.time_remaining -= dt
        if self.time_remaining <= 0:
            self.time_remaining = 0
            self.state = GameState.GAME_OVER
            return

        self.difficulty_timer += dt

        # Increase difficulty over time
        if self.difficulty_timer > 30:
            self.spawn_interval = max(0.5, self.spawn_interval - 0.1)
            self.difficulty_timer = 0

        # Handle crosshair movement (smooth)
        move_x = 0.0
        move_y = 0.0
        if input_state.left:
            move_x -= 1.0
        if input_state.right:
            move_x += 1.0
        if input_state.up:
            move_y -= 1.0
        if input_state.down:
            move_y += 1.0

        # Normalize diagonal movement
        if move_x != 0 and move_y != 0:
            move_x *= 0.707
            move_y *= 0.707

        # Apply movement with accumulator for sub-pixel precision
        self.move_accum_x += move_x * self.crosshair_speed * dt
        self.move_accum_y += move_y * self.crosshair_speed * dt

        # Convert accumulated movement to integer steps
        if abs(self.move_accum_x) >= 1.0:
            step = int(self.move_accum_x)
            self.crosshair_x += step
            self.move_accum_x -= step

        if abs(self.move_accum_y) >= 1.0:
            step = int(self.move_accum_y)
            self.crosshair_y += step
            self.move_accum_y -= step

        # Clamp crosshair to viewport
        margin = self.viewport_margin + 2
        self.crosshair_x = max(margin, min(GRID_SIZE - margin, self.crosshair_x))
        self.crosshair_y = max(margin, min(GRID_SIZE - margin, self.crosshair_y))

        # Fire on action button
        if (input_state.action_l or input_state.action_r):
            self._fire_at_crosshair()

        # Update fire cooldown
        if self.fire_cooldown > 0:
            self.fire_cooldown -= dt

        # Spawn new trash
        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0
            if len([t for t in self.trash if t.alive]) < 12:
                self._spawn_trash()

        # Update trash positions
        for t in self.trash:
            if t.alive:
                t.x += t.vx * dt
                t.y += t.vy * dt
                t.rotation += t.rot_speed * dt

                # Remove if off screen
                margin = self.viewport_margin
                if (t.x < margin - 5 or t.x > GRID_SIZE - margin + 5 or
                    t.y < margin - 5 or t.y > GRID_SIZE - margin + 5):
                    t.alive = False

        # Clean up dead trash
        self.trash = [t for t in self.trash if t.alive]

        # Update explosions
        for e in self.explosions:
            e.update(dt)
        self.explosions = [e for e in self.explosions if e.alive]

        # Update floating scores
        for s in self.floating_scores:
            s.update(dt)
        self.floating_scores = [s for s in self.floating_scores if s.alive]

        # Update laser blasts
        for l in self.laser_blasts:
            l.update(dt)
        self.laser_blasts = [l for l in self.laser_blasts if l.alive]

    def _draw_cockpit_frame(self):
        """Draw the cockpit window frame around the viewport."""
        margin = self.viewport_margin
        frame_color = (40, 45, 55)
        frame_accent = (60, 70, 85)

        # Top frame
        for y in range(margin):
            for x in range(GRID_SIZE):
                if y == margin - 1:
                    self.display.set_pixel(x, y, frame_accent)
                else:
                    self.display.set_pixel(x, y, frame_color)

        # Bottom frame
        for y in range(GRID_SIZE - margin, GRID_SIZE):
            for x in range(GRID_SIZE):
                if y == GRID_SIZE - margin:
                    self.display.set_pixel(x, y, frame_accent)
                else:
                    self.display.set_pixel(x, y, frame_color)

        # Left frame
        for y in range(margin, GRID_SIZE - margin):
            for x in range(margin):
                if x == margin - 1:
                    self.display.set_pixel(x, y, frame_accent)
                else:
                    self.display.set_pixel(x, y, frame_color)

        # Right frame
        for y in range(margin, GRID_SIZE - margin):
            for x in range(GRID_SIZE - margin, GRID_SIZE):
                if x == GRID_SIZE - margin:
                    self.display.set_pixel(x, y, frame_accent)
                else:
                    self.display.set_pixel(x, y, frame_color)

        # Corner accents (cockpit bolts/rivets)
        rivet_color = (80, 90, 100)
        corners = [(2, 2), (GRID_SIZE-3, 2), (2, GRID_SIZE-3), (GRID_SIZE-3, GRID_SIZE-3)]
        for cx, cy in corners:
            self.display.set_pixel(cx, cy, rivet_color)

    def _draw_crosshair(self):
        """Draw the targeting crosshair."""
        x, y = self.crosshair_x, self.crosshair_y

        # Crosshair color - brighter when firing
        if self.laser_blasts:
            color = (255, 100, 100)
            inner = (255, 200, 200)
        else:
            color = (0, 255, 100)
            inner = (150, 255, 200)

        # Draw crosshair pattern
        # Horizontal line
        for dx in [-3, -2, 2, 3]:
            px = x + dx
            if self.viewport_margin < px < GRID_SIZE - self.viewport_margin:
                self.display.set_pixel(px, y, color)

        # Vertical line
        for dy in [-3, -2, 2, 3]:
            py = y + dy
            if self.viewport_margin < py < GRID_SIZE - self.viewport_margin:
                self.display.set_pixel(x, py, color)

        # Center dot
        self.display.set_pixel(x, y, inner)

    def _draw_laser_blasts(self):
        """Draw laser blast effects."""
        for blast in self.laser_blasts:
            progress = blast.time / blast.duration
            fade = 1.0 - progress

            # Expanding ring effect
            radius = int(progress * 6)
            brightness = int(255 * fade)
            color = (brightness, brightness // 2, brightness // 4)

            for angle in range(0, 360, 30):
                rad = math.radians(angle)
                px = int(blast.x + math.cos(rad) * radius)
                py = int(blast.y + math.sin(rad) * radius)
                if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                    self.display.set_pixel(px, py, color)

    def _draw_digit(self, x, y, digit, color):
        """Draw a single digit (3x5 font)."""
        digits = {
            '0': [(0,0),(1,0),(2,0),(0,1),(2,1),(0,2),(2,2),(0,3),(2,3),(0,4),(1,4),(2,4)],
            '1': [(1,0),(1,1),(1,2),(1,3),(1,4)],
            '2': [(0,0),(1,0),(2,0),(2,1),(0,2),(1,2),(2,2),(0,3),(0,4),(1,4),(2,4)],
            '3': [(0,0),(1,0),(2,0),(2,1),(1,2),(2,2),(2,3),(0,4),(1,4),(2,4)],
            '4': [(0,0),(2,0),(0,1),(2,1),(0,2),(1,2),(2,2),(2,3),(2,4)],
            '5': [(0,0),(1,0),(2,0),(0,1),(0,2),(1,2),(2,2),(2,3),(0,4),(1,4),(2,4)],
            '6': [(0,0),(1,0),(2,0),(0,1),(0,2),(1,2),(2,2),(0,3),(2,3),(0,4),(1,4),(2,4)],
            '7': [(0,0),(1,0),(2,0),(2,1),(2,2),(2,3),(2,4)],
            '8': [(0,0),(1,0),(2,0),(0,1),(2,1),(0,2),(1,2),(2,2),(0,3),(2,3),(0,4),(1,4),(2,4)],
            '9': [(0,0),(1,0),(2,0),(0,1),(2,1),(0,2),(1,2),(2,2),(2,3),(0,4),(1,4),(2,4)],
            '+': [(1,1),(0,2),(1,2),(2,2),(1,3)],
        }
        if digit in digits:
            for dx, dy in digits[digit]:
                px, py = x + dx, y + dy
                if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                    self.display.set_pixel(px, py, color)

    def _draw_number(self, x, y, number, color):
        """Draw a number."""
        s = str(number)
        for i, char in enumerate(s):
            self._draw_digit(x + i * 4, y, char, color)

    def _draw_score_display(self):
        """Draw score and countdown in the cockpit frame area."""
        # Score in top-left of frame
        self._draw_number(2, 2, self.score, (0, 200, 100))

        # Countdown timer in top-right of frame
        secs = max(0, int(self.time_remaining))
        mins = secs // 60
        secs = secs % 60
        timer_color = (255, 50, 50) if self.time_remaining < 10 else (200, 200, 0)
        timer_str = f"{mins}:{secs:02d}"
        self.display.draw_text_small(42, 2, timer_str, timer_color)

    def draw(self):
        # Space background (visible through viewport)
        self.display.clear((5, 5, 20))

        # Draw stars in viewport area
        margin = self.viewport_margin
        random.seed(42)
        for _ in range(40):
            sx = random.randint(margin, GRID_SIZE - margin - 1)
            sy = random.randint(margin, GRID_SIZE - margin - 1)
            brightness = random.randint(40, 120)
            self.display.set_pixel(sx, sy, (brightness, brightness, brightness + 30))
        random.seed()

        # Draw trash
        for t in self.trash:
            if not t.alive:
                continue
            pixels = t.get_pixels()
            for dx, dy, color in pixels:
                px, py = int(t.x + dx), int(t.y + dy)
                if margin <= px < GRID_SIZE - margin and margin <= py < GRID_SIZE - margin:
                    self.display.set_pixel(px, py, color)

        # Draw laser blasts
        self._draw_laser_blasts()

        # Draw explosions
        for e in self.explosions:
            for x, y, color in e.get_pixels():
                if margin <= x < GRID_SIZE - margin and margin <= y < GRID_SIZE - margin:
                    self.display.set_pixel(x, y, color)

        # Draw floating scores
        for s in self.floating_scores:
            fade = 1.0 - (s.time / s.duration)
            color = (int(s.color[0] * fade), int(s.color[1] * fade), int(s.color[2] * fade))
            self._draw_digit(int(s.x) - 2, int(s.y), '+', color)
            self._draw_number(int(s.x) + 2, int(s.y), s.points, color)

        # Draw cockpit frame (on top of everything except crosshair)
        self._draw_cockpit_frame()

        # Draw crosshair (always visible)
        self._draw_crosshair()

        # Draw score display in frame
        self._draw_score_display()
