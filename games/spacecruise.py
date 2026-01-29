"""
SpaceCruise - MathBlasters Math Shooting Game
==============================================
Pilot your rocket through space and shoot floating numbers and operators!
Build math combos to maximize your score.

Combo System:
  - Hit a number: Loads it as your first operand
  - Hit another number: Score the first number's value
  - Hit an operator (+, -, x): Start building an equation
  - Hit a number after operator: Compute result and bank it as score!
  - Miss your 3rd shot in a combo: Combo disappears

Controls:
  Up/Down    - Move rocket vertically
  Left/Right - Move crosshair horizontally
  Space      - Fire at crosshair position
  Escape     - Exit
"""

import random
import math
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


class Star:
    """Background star for the starfield."""
    def __init__(self, layer: int):
        self.layer = layer
        self.reset()

    def reset(self):
        self.x = random.uniform(GRID_SIZE, GRID_SIZE + 20)
        self.y = random.uniform(0, GRID_SIZE)
        base_brightness = 60 + self.layer * 50
        self.brightness = random.randint(base_brightness - 20, base_brightness + 20)
        self.brightness = max(30, min(200, self.brightness))


class MathTarget:
    """Floating number or operator that can be shot."""
    NUMBERS = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    OPERATORS = ['+', '-', 'x']

    COLORS = {
        'number': (255, 255, 0),     # Yellow for numbers
        'operator': (0, 255, 255),   # Cyan for operators
    }

    def __init__(self):
        self.reset()

    def reset(self):
        self.x = random.uniform(GRID_SIZE, GRID_SIZE + 40)
        self.y = random.uniform(10, GRID_SIZE - 14)

        # 75% numbers, 25% operators
        if random.random() < 0.75:
            self.symbol = random.choice(self.NUMBERS)
            self.is_number = True
            self.value = int(self.symbol)
            self.color = self.COLORS['number']
        else:
            self.symbol = random.choice(self.OPERATORS)
            self.is_number = False
            self.value = 0
            self.color = self.COLORS['operator']

        self.float_offset = random.uniform(0, math.pi * 2)
        self.float_speed = random.uniform(1.5, 2.5)
        self.float_amplitude = random.uniform(1.0, 2.5)
        self.alive = True

    def get_hitbox(self):
        """Return (x, y, width, height) for collision."""
        return (self.x, self.y, 4, 6)


class Explosion:
    """Small explosion when hitting a target."""
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.time = 0.0
        self.duration = 0.3
        self.alive = True

    def update(self, dt):
        self.time += dt
        if self.time >= self.duration:
            self.alive = False


class FloatingText:
    """Score or combo text that floats up."""
    def __init__(self, x, y, text, color):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.time = 0.0
        self.duration = 1.0
        self.alive = True

    def update(self, dt):
        self.time += dt
        self.y -= 10 * dt
        if self.time >= self.duration:
            self.alive = False


class LaserShot:
    """Laser beam from rocket to target."""
    def __init__(self, start_x, start_y, end_x, end_y):
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y
        self.time = 0.0
        self.duration = 0.15
        self.alive = True

    def update(self, dt):
        self.time += dt
        if self.time >= self.duration:
            self.alive = False


class SpaceCruise(Game):
    name = "SPACECRUISE"
    description = "Math shooter!"
    category = "retro"

    # Colors
    SPACE_BLACK = (5, 5, 15)
    ROCKET_BODY = (220, 220, 240)
    ROCKET_BODY_DARK = (150, 150, 170)
    ROCKET_NOSE = (255, 80, 80)
    ROCKET_WINDOW = (100, 200, 255)
    ROCKET_FIN = (255, 100, 100)
    EXHAUST_CORE = (255, 255, 200)
    EXHAUST_MID = (255, 200, 50)
    EXHAUST_OUTER = (255, 100, 30)
    CROSSHAIR_COLOR = (0, 255, 100)
    CROSSHAIR_ACTIVE = (255, 100, 100)

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.time = 0.0
        self.score = 0

        # Rocket position
        self.rocket_x = 10
        self.rocket_y = GRID_SIZE // 2
        self.target_y = self.rocket_y
        self.bob_phase = 0.0

        # Crosshair position (relative to rocket, extends right)
        self.crosshair_x = 35
        self.crosshair_y = GRID_SIZE // 2

        # Fire cooldown
        self.fire_cooldown = 0.0
        self.fire_delay = 0.3

        # Stars
        self.stars = []
        for layer in range(3):
            for _ in range(12 + layer * 8):
                star = Star(layer)
                star.x = random.uniform(0, GRID_SIZE)
                self.stars.append(star)

        # Math targets
        self.targets = []
        for _ in range(8):
            target = MathTarget()
            target.x = random.uniform(25, GRID_SIZE - 5)
            self.targets.append(target)

        # Effects
        self.explosions = []
        self.floating_texts = []
        self.laser_shots = []

        # Math combo state
        self.combo_first_number = None   # First number in combo
        self.combo_operator = None       # Operator (+, -, x)
        self.combo_shots = 0             # Shots since combo started
        self.combo_display_timer = 0.0   # Timer for showing combo

        # Spawn timer
        self.spawn_timer = 0.0
        self.spawn_interval = 0.8

    def _fire(self):
        """Fire at crosshair position."""
        if self.fire_cooldown > 0:
            return

        self.fire_cooldown = self.fire_delay

        # Create laser shot
        rocket_nose_x = self.rocket_x + 4
        rocket_nose_y = int(self.rocket_y)
        shot = LaserShot(rocket_nose_x, rocket_nose_y, self.crosshair_x, self.crosshair_y)
        self.laser_shots.append(shot)

        # Check for hits
        hit_target = None
        for target in self.targets:
            if not target.alive:
                continue

            # Simple distance check
            tx = target.x + 1.5  # Center of target
            ty = target.y + 2.5 + math.sin(self.time * target.float_speed + target.float_offset) * target.float_amplitude

            dx = self.crosshair_x - tx
            dy = self.crosshair_y - ty
            dist = math.sqrt(dx * dx + dy * dy)

            if dist < 5:  # Hit radius
                hit_target = target
                break

        if hit_target:
            self._process_hit(hit_target)
        else:
            self._process_miss()

    def _process_hit(self, target):
        """Process hitting a target."""
        # Create explosion
        ty = target.y + math.sin(self.time * target.float_speed + target.float_offset) * target.float_amplitude
        explosion = Explosion(target.x + 1.5, ty + 2.5, target.color)
        self.explosions.append(explosion)
        target.alive = False

        if target.is_number:
            self._hit_number(target.value, target.x, ty)
        else:
            self._hit_operator(target.symbol, target.x, ty)

    def _hit_number(self, value, x, y):
        """Handle hitting a number."""
        if self.combo_first_number is None:
            # First number - load it
            self.combo_first_number = value
            self.combo_operator = None
            self.combo_shots = 0
            self.combo_display_timer = 3.0

            text = FloatingText(x, y, str(value), (100, 255, 100))
            self.floating_texts.append(text)

        elif self.combo_operator is None:
            # Second number without operator - score first number
            points = self.combo_first_number
            self.score += points

            text = FloatingText(x, y, f"+{points}", (255, 255, 100))
            self.floating_texts.append(text)

            # New number becomes first
            self.combo_first_number = value
            self.combo_shots = 0
            self.combo_display_timer = 3.0

        else:
            # Have operator - compute result!
            result = self._compute_result(self.combo_first_number, self.combo_operator, value)
            self.score += result

            # Show the equation
            eq_text = f"{self.combo_first_number}{self.combo_operator}{value}={result}"
            text = FloatingText(x - 8, y, eq_text, (255, 255, 0))
            self.floating_texts.append(text)

            # Reset combo
            self.combo_first_number = None
            self.combo_operator = None
            self.combo_shots = 0

    def _hit_operator(self, op, x, y):
        """Handle hitting an operator."""
        if self.combo_first_number is not None and self.combo_operator is None:
            # Valid - set operator
            self.combo_operator = op
            self.combo_shots = 0
            self.combo_display_timer = 3.0

            text = FloatingText(x, y, op, (0, 255, 255))
            self.floating_texts.append(text)
        else:
            # Invalid - just a small bonus
            self.score += 1
            text = FloatingText(x, y, "+1", (100, 100, 255))
            self.floating_texts.append(text)

    def _compute_result(self, a, op, b):
        """Compute math result."""
        if op == '+':
            return a + b
        elif op == '-':
            return max(0, a - b)  # No negative scores
        elif op == 'x':
            return a * b
        return a

    def _process_miss(self):
        """Process missing a shot."""
        if self.combo_first_number is not None:
            self.combo_shots += 1

            # If we've taken 3 shots in a combo without completing it, lose it
            if self.combo_shots >= 3:
                # Show lost combo
                text = FloatingText(self.crosshair_x, self.crosshair_y, "MISS!", (255, 50, 50))
                self.floating_texts.append(text)

                self.combo_first_number = None
                self.combo_operator = None
                self.combo_shots = 0

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        self.time += dt
        self.bob_phase += dt * 2.5

        # Handle input
        if input_state.up:
            self.target_y = max(8, self.target_y - 1.2)
            self.crosshair_y = max(4, self.crosshair_y - 1.2)
        if input_state.down:
            self.target_y = min(GRID_SIZE - 8, self.target_y + 1.2)
            self.crosshair_y = min(GRID_SIZE - 4, self.crosshair_y + 1.2)
        if input_state.left:
            self.crosshair_x = max(20, self.crosshair_x - 1.5)
        if input_state.right:
            self.crosshair_x = min(GRID_SIZE - 4, self.crosshair_x + 1.5)

        if (input_state.action_l or input_state.action_r):
            self._fire()

        # Update fire cooldown
        if self.fire_cooldown > 0:
            self.fire_cooldown -= dt

        # Smoothly move rocket
        y_diff = self.target_y - self.rocket_y
        self.rocket_y += y_diff * dt * 4.0

        # Update combo display timer
        if self.combo_display_timer > 0:
            self.combo_display_timer -= dt

        # Update stars
        layer_speeds = [12.0, 25.0, 40.0]
        for star in self.stars:
            star.x -= layer_speeds[star.layer] * dt
            if star.x < -2:
                star.reset()

        # Update targets
        target_speed = 30.0
        for target in self.targets:
            if target.alive:
                target.x -= target_speed * dt
                if target.x < -10:
                    target.reset()

        # Spawn new targets
        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0
            if len([t for t in self.targets if t.alive]) < 10:
                self.targets.append(MathTarget())

        # Clean up dead targets
        self.targets = [t for t in self.targets if t.alive or t.x > -10]

        # Update effects
        for e in self.explosions:
            e.update(dt)
        self.explosions = [e for e in self.explosions if e.alive]

        for t in self.floating_texts:
            t.update(dt)
        self.floating_texts = [t for t in self.floating_texts if t.alive]

        for s in self.laser_shots:
            s.update(dt)
        self.laser_shots = [s for s in self.laser_shots if s.alive]

    def _draw_star(self, star):
        x, y = int(star.x), int(star.y)
        if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
            b = star.brightness
            self.display.set_pixel(x, y, (b, b, b))

    def _draw_target(self, target):
        """Draw a math target with its symbol."""
        x = int(target.x)
        float_y = target.y + math.sin(self.time * target.float_speed + target.float_offset) * target.float_amplitude
        y = int(float_y)

        color = target.color
        char = target.symbol

        patterns = {
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
            '-': [(0,2),(1,2),(2,2)],
            'x': [(0,0),(2,0),(1,1),(1,2),(1,3),(0,4),(2,4)],
        }

        if char in patterns:
            for dx, dy in patterns[char]:
                px, py = x + dx, y + dy
                if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                    self.display.set_pixel(px, py, color)

    def _draw_rocket(self, x, y):
        """Draw the rocket ship."""
        # Main body
        for dy in range(-2, 2):
            for dx in range(-2, 2):
                px, py = x + dx, y + dy
                if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                    color = self.ROCKET_BODY if dy < 0 else self.ROCKET_BODY_DARK
                    self.display.set_pixel(px, py, color)

        # Nose cone
        for dx, dy in [(2, -1), (2, 0), (3, -1), (3, 0), (4, 0)]:
            px, py = x + dx, y + dy
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                self.display.set_pixel(px, py, self.ROCKET_NOSE)

        # Window
        for dx, dy in [(0, -1), (1, -1), (0, 0), (1, 0)]:
            px, py = x + dx, y + dy
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                self.display.set_pixel(px, py, self.ROCKET_WINDOW)

        # Fins
        for dx, dy in [(-2, -3), (-1, -3), (-2, -2), (-2, 2), (-1, 2), (-2, 1)]:
            px, py = x + dx, y + dy
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                self.display.set_pixel(px, py, self.ROCKET_FIN)

        # Exhaust
        self._draw_exhaust(x - 3, y)

    def _draw_exhaust(self, x, y):
        """Draw flickering exhaust."""
        flicker = math.sin(self.time * 30) * 0.5 + 0.5

        core_len = 2 + int(flicker * 2)
        for i in range(core_len):
            px = x - i
            if 0 <= px < GRID_SIZE and 0 <= y < GRID_SIZE:
                self.display.set_pixel(px, y, self.EXHAUST_CORE)

        for i in range(1 + int(flicker * 1.5)):
            px, py = x - i, y - 1
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                self.display.set_pixel(px, py, self.EXHAUST_MID if i < 1 else self.EXHAUST_OUTER)
            py = y + 1
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                self.display.set_pixel(px, py, self.EXHAUST_MID if i < 1 else self.EXHAUST_OUTER)

    def _draw_crosshair(self):
        """Draw targeting crosshair."""
        x, y = int(self.crosshair_x), int(self.crosshair_y)

        color = self.CROSSHAIR_ACTIVE if self.laser_shots else self.CROSSHAIR_COLOR

        # Crosshair pattern
        for d in [-2, -1, 1, 2]:
            if 0 <= x + d < GRID_SIZE:
                self.display.set_pixel(x + d, y, color)
            if 0 <= y + d < GRID_SIZE:
                self.display.set_pixel(x, y + d, color)

    def _draw_laser(self, shot):
        """Draw laser beam."""
        fade = 1.0 - (shot.time / shot.duration)
        brightness = int(255 * fade)
        color = (brightness, brightness, int(brightness * 0.5))

        # Simple line
        dx = shot.end_x - shot.start_x
        dy = shot.end_y - shot.start_y
        steps = max(abs(int(dx)), abs(int(dy)), 1)

        for i in range(steps + 1):
            t = i / steps
            px = int(shot.start_x + dx * t)
            py = int(shot.start_y + dy * t)
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                self.display.set_pixel(px, py, color)

    def _draw_explosion(self, exp):
        """Draw explosion effect."""
        progress = exp.time / exp.duration
        fade = 1.0 - progress
        radius = int(progress * 5) + 1

        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            px = int(exp.x + math.cos(rad) * radius)
            py = int(exp.y + math.sin(rad) * radius)
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                c = exp.color
                color = (int(c[0] * fade), int(c[1] * fade), int(c[2] * fade))
                self.display.set_pixel(px, py, color)

    def _draw_digit(self, x, y, char, color):
        """Draw a character."""
        patterns = {
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
            '-': [(0,2),(1,2),(2,2)],
            'x': [(0,0),(2,0),(1,1),(1,2),(1,3),(0,4),(2,4)],
            '=': [(0,1),(1,1),(2,1),(0,3),(1,3),(2,3)],
        }
        if char in patterns:
            for dx, dy in patterns[char]:
                px, py = x + dx, y + dy
                if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                    self.display.set_pixel(px, py, color)

    def _draw_number(self, x, y, num, color):
        """Draw a number."""
        s = str(num)
        for i, c in enumerate(s):
            self._draw_digit(x + i * 4, y, c, color)

    def _draw_combo_display(self):
        """Draw current combo state."""
        if self.combo_first_number is not None and self.combo_display_timer > 0:
            # Draw in top-right area
            x = GRID_SIZE - 20
            y = 2

            # First number
            self._draw_digit(x, y, str(self.combo_first_number), (100, 255, 100))

            if self.combo_operator:
                # Operator
                self._draw_digit(x + 5, y, self.combo_operator, (0, 255, 255))
                # Question mark for next number
                self._draw_digit(x + 10, y, '?', (255, 255, 0))

    def _draw_score(self):
        """Draw score display."""
        self._draw_number(2, 2, self.score, (0, 200, 100))

    def draw(self):
        self.display.clear(self.SPACE_BLACK)

        # Draw stars (back to front)
        for star in self.stars:
            self._draw_star(star)

        # Draw targets
        for target in self.targets:
            if target.alive:
                self._draw_target(target)

        # Draw laser shots
        for shot in self.laser_shots:
            self._draw_laser(shot)

        # Draw explosions
        for exp in self.explosions:
            self._draw_explosion(exp)

        # Draw floating texts
        for text in self.floating_texts:
            fade = 1.0 - (text.time / text.duration)
            color = (int(text.color[0] * fade), int(text.color[1] * fade), int(text.color[2] * fade))
            x_pos = int(text.x)
            for i, c in enumerate(text.text):
                if c in '0123456789+-x=':
                    self._draw_digit(x_pos + i * 4, int(text.y), c, color)
                elif c == '!':
                    # Simple exclamation
                    if 0 <= x_pos + i * 4 < GRID_SIZE:
                        for dy in range(4):
                            if 0 <= int(text.y) + dy < GRID_SIZE:
                                self.display.set_pixel(x_pos + i * 4, int(text.y) + dy, color)

        # Draw rocket
        bob_offset = math.sin(self.bob_phase) * 1.5
        rocket_draw_x = int(self.rocket_x)
        rocket_draw_y = int(self.rocket_y + bob_offset)
        self._draw_rocket(rocket_draw_x, rocket_draw_y)

        # Draw crosshair
        self._draw_crosshair()

        # Draw combo display
        self._draw_combo_display()

        # Draw score
        self._draw_score()
