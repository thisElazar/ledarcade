"""
Bloons - LED Arcade
===================
Classic dart-throwing game. Aim a monkey's throw with angle + power,
pop balloon clusters with limited darts, progress through 15 levels.

Controls:
  Up/Down      - Adjust aim angle
  Space (hold) - Hold to charge power, release to fire
  Z            - Cancel back to aiming (during power phase)
"""

import math
import random
from arcade import Game, GameState, Display, Colors, InputState

# Phases
PHASE_AIM = 0
PHASE_POWER = 1
PHASE_FLIGHT = 2
PHASE_RESULT = 3
PHASE_LEVEL_WIN = 4
PHASE_LEVEL_FAIL = 5

# Physics
MAX_SPEED = 100.0      # px/s at full power
GRAVITY = 60.0         # px/s^2
DART_RADIUS = 3.0      # collision radius
TRAIL_LEN = 3

# Display regions
HUD_HEIGHT = 6
GROUND_Y = 54
SKY_COLOR = (100, 150, 220)
GROUND_COLOR = (40, 120, 40)
MONKEY_X = 5
MONKEY_Y = 48

# Aim
MIN_ANGLE = 0.1        # radians above horizontal
MAX_ANGLE = 1.4        # ~80 degrees
AIM_SPEED = 1.2        # rad/s

# Power bar
POWER_BAR_X = 1
POWER_BAR_W = 2
POWER_BAR_TOP = 8
POWER_BAR_BOT = 52
POWER_CHARGE_SPEED = 0.8  # power per second while holding

# Bloon types: (name, color, child_type_index, points)
BLOON_TYPES = [
    ('red',    (255, 40, 40),    -1, 1),
    ('blue',   (40, 80, 255),     0, 2),
    ('green',  (40, 200, 40),     1, 3),
    ('yellow', (255, 255, 40),    2, 4),
    ('pink',   (255, 120, 160),   3, 5),
]

# Levels: list of (darts, [(type_index, x, y), ...])
LEVELS = [
    # L1: Big red cluster, easy pickings
    {'darts': 4, 'bloons': [
        (0, 35, 28), (0, 39, 28), (0, 43, 28), (0, 47, 28), (0, 51, 28),
        (0, 37, 24), (0, 41, 24), (0, 45, 24), (0, 49, 24),
        (0, 39, 20), (0, 43, 20), (0, 47, 20),
        (0, 37, 32), (0, 41, 32), (0, 45, 32), (0, 49, 32),
    ]},
    # L2: Red pyramid right side
    {'darts': 4, 'bloons': [
        (0, 44, 38), (0, 48, 38), (0, 52, 38), (0, 56, 38),
        (0, 46, 34), (0, 50, 34), (0, 54, 34),
        (0, 48, 30), (0, 52, 30),
        (0, 50, 26),
        (0, 44, 42), (0, 48, 42), (0, 52, 42), (0, 56, 42),
    ]},
    # L3: Reds everywhere
    {'darts': 5, 'bloons': [
        (0, 25, 15), (0, 30, 15), (0, 35, 15), (0, 40, 15),
        (0, 28, 25), (0, 33, 25), (0, 38, 25), (0, 43, 25), (0, 48, 25),
        (0, 30, 35), (0, 35, 35), (0, 40, 35), (0, 45, 35), (0, 50, 35),
        (0, 35, 45), (0, 40, 45), (0, 45, 45), (0, 50, 45), (0, 55, 45),
    ]},
    # L4: Blues introduced, dense cluster
    {'darts': 4, 'bloons': [
        (1, 38, 26), (1, 42, 26), (1, 46, 26), (1, 50, 26), (1, 54, 26),
        (1, 40, 22), (1, 44, 22), (1, 48, 22), (1, 52, 22),
        (0, 42, 18), (0, 46, 18), (0, 50, 18),
        (0, 38, 30), (0, 42, 30), (0, 46, 30), (0, 50, 30), (0, 54, 30),
    ]},
    # L5: Blue columns
    {'darts': 5, 'bloons': [
        (1, 35, 12), (1, 35, 18), (1, 35, 24), (1, 35, 30), (1, 35, 36),
        (1, 45, 12), (1, 45, 18), (1, 45, 24), (1, 45, 30), (1, 45, 36),
        (1, 55, 12), (1, 55, 18), (1, 55, 24), (1, 55, 30), (1, 55, 36),
        (0, 40, 42), (0, 50, 42), (0, 45, 46),
    ]},
    # L6: Blue diamond
    {'darts': 5, 'bloons': [
        (1, 44, 14),
        (1, 40, 18), (1, 48, 18),
        (1, 36, 22), (1, 44, 22), (1, 52, 22),
        (1, 40, 26), (1, 48, 26),
        (1, 44, 30),
        (0, 36, 34), (0, 40, 34), (0, 44, 34), (0, 48, 34), (0, 52, 34),
        (0, 38, 38), (0, 42, 38), (0, 46, 38), (0, 50, 38),
    ]},
    # L7: Greens with red/blue fillers
    {'darts': 5, 'bloons': [
        (2, 40, 20), (2, 44, 20), (2, 48, 20), (2, 52, 20),
        (2, 42, 16), (2, 46, 16), (2, 50, 16),
        (1, 38, 24), (1, 42, 24), (1, 46, 24), (1, 50, 24), (1, 54, 24),
        (0, 40, 28), (0, 44, 28), (0, 48, 28), (0, 52, 28),
        (0, 42, 32), (0, 46, 32), (0, 50, 32),
    ]},
    # L8: Green and blue mix, wide spread
    {'darts': 5, 'bloons': [
        (2, 30, 18), (2, 35, 18), (2, 40, 18), (2, 50, 18), (2, 55, 18),
        (1, 28, 28), (1, 33, 28), (1, 38, 28), (1, 43, 28), (1, 48, 28),
        (1, 53, 28), (1, 58, 28),
        (0, 30, 38), (0, 35, 38), (0, 40, 38), (0, 45, 38),
        (0, 50, 38), (0, 55, 38),
    ]},
    # L9: Green wall, tight grid
    {'darts': 5, 'bloons': [
        (2, 36, 14), (2, 40, 14), (2, 44, 14), (2, 48, 14), (2, 52, 14), (2, 56, 14),
        (2, 38, 18), (2, 42, 18), (2, 46, 18), (2, 50, 18), (2, 54, 18),
        (2, 36, 22), (2, 40, 22), (2, 44, 22), (2, 48, 22), (2, 52, 22), (2, 56, 22),
        (1, 38, 26), (1, 42, 26), (1, 46, 26), (1, 50, 26), (1, 54, 26),
    ]},
    # L10: Yellows with supporting bloons
    {'darts': 6, 'bloons': [
        (3, 50, 12), (3, 55, 12), (3, 50, 18), (3, 55, 18),
        (2, 40, 22), (2, 45, 22), (2, 50, 22), (2, 55, 22),
        (1, 35, 30), (1, 40, 30), (1, 45, 30), (1, 50, 30), (1, 55, 30),
        (0, 30, 38), (0, 35, 38), (0, 40, 38), (0, 45, 38),
        (0, 50, 38), (0, 55, 38),
    ]},
    # L11: Yellow cluster with green base
    {'darts': 5, 'bloons': [
        (3, 40, 16), (3, 44, 16), (3, 48, 16), (3, 52, 16),
        (3, 42, 12), (3, 46, 12), (3, 50, 12),
        (2, 38, 20), (2, 42, 20), (2, 46, 20), (2, 50, 20), (2, 54, 20),
        (1, 40, 24), (1, 44, 24), (1, 48, 24), (1, 52, 24),
        (0, 42, 28), (0, 46, 28), (0, 50, 28),
    ]},
    # L12: Spread yellows and greens
    {'darts': 6, 'bloons': [
        (3, 28, 14), (3, 38, 14), (3, 48, 14), (3, 58, 14),
        (3, 33, 24), (3, 43, 24), (3, 53, 24),
        (2, 28, 34), (2, 38, 34), (2, 48, 34), (2, 58, 34),
        (1, 33, 44), (1, 43, 44), (1, 53, 44),
        (0, 28, 48), (0, 38, 48), (0, 48, 48), (0, 58, 48),
    ]},
    # L13: Pinks introduced with big support
    {'darts': 5, 'bloons': [
        (4, 44, 16), (4, 48, 16), (4, 52, 16),
        (3, 40, 20), (3, 44, 20), (3, 48, 20), (3, 52, 20), (3, 56, 20),
        (2, 42, 24), (2, 46, 24), (2, 50, 24), (2, 54, 24),
        (1, 40, 30), (1, 44, 30), (1, 48, 30), (1, 52, 30),
        (0, 42, 36), (0, 46, 36), (0, 50, 36), (0, 54, 36),
    ]},
    # L14: Pink cluster, lots of pops
    {'darts': 5, 'bloons': [
        (4, 38, 16), (4, 42, 16), (4, 46, 16), (4, 50, 16), (4, 54, 16),
        (4, 40, 20), (4, 44, 20), (4, 48, 20), (4, 52, 20),
        (3, 38, 24), (3, 42, 24), (3, 46, 24), (3, 50, 24), (3, 54, 24),
        (2, 40, 28), (2, 44, 28), (2, 48, 28), (2, 52, 28),
    ]},
    # L15: Grand finale, packed field
    {'darts': 6, 'bloons': [
        (4, 35, 12), (4, 40, 12), (4, 45, 12), (4, 50, 12), (4, 55, 12),
        (4, 37, 18), (4, 42, 18), (4, 47, 18), (4, 52, 18),
        (3, 35, 24), (3, 40, 24), (3, 45, 24), (3, 50, 24), (3, 55, 24),
        (3, 37, 30), (3, 42, 30), (3, 47, 30), (3, 52, 30),
        (2, 35, 36), (2, 40, 36), (2, 45, 36), (2, 50, 36), (2, 55, 36),
        (1, 37, 42), (1, 42, 42), (1, 47, 42), (1, 52, 42),
    ]},
]


class Bloons(Game):
    name = "BLOONS"
    description = "Pop balloons with darts"
    category = "modern"

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0
        self.level = 0
        self._load_level()

    def _load_level(self):
        """Load current level data."""
        lvl = LEVELS[self.level]
        self.darts_left = lvl['darts']
        self.bloons = []
        for type_idx, bx, by in lvl['bloons']:
            self.bloons.append({
                'type': type_idx,
                'x': float(bx),
                'y': float(by),
                'alive': True,
            })
        self.phase = PHASE_AIM
        self.angle = 0.7  # starting angle ~40 degrees
        self.power = 0.0
        self.dart_x = 0.0
        self.dart_y = 0.0
        self.dart_vx = 0.0
        self.dart_vy = 0.0
        self.trail = []
        self.phase_timer = 0.0
        self.pops_this_throw = 0
        self.result_text = ""

    def _alive_bloons(self):
        return [b for b in self.bloons if b['alive']]

    def _fire_dart(self):
        """Launch dart from monkey position."""
        self.dart_x = float(MONKEY_X + 3)
        self.dart_y = float(MONKEY_Y - 2)
        speed = self.power * MAX_SPEED
        self.dart_vx = math.cos(self.angle) * speed
        self.dart_vy = -math.sin(self.angle) * speed
        self.trail = []
        self.pops_this_throw = 0
        self.phase = PHASE_FLIGHT

    def _pop_bloon(self, bloon):
        """Pop a bloon - may spawn child."""
        bloon['alive'] = False
        type_idx = bloon['type']
        _, _, child_idx, points = BLOON_TYPES[type_idx]
        self.score += points
        self.pops_this_throw += 1

        # Spawn child at same position
        if child_idx >= 0:
            self.bloons.append({
                'type': child_idx,
                'x': bloon['x'],
                'y': bloon['y'],
                'alive': True,
            })

    # ==== UPDATE ====

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        if self.phase == PHASE_AIM:
            self._update_aim(input_state, dt)
        elif self.phase == PHASE_POWER:
            self._update_power(input_state, dt)
        elif self.phase == PHASE_FLIGHT:
            self._update_flight(dt)
        elif self.phase == PHASE_RESULT:
            self._update_result(dt)
        elif self.phase == PHASE_LEVEL_WIN:
            self._update_level_win(input_state, dt)
        elif self.phase == PHASE_LEVEL_FAIL:
            self._update_level_fail(input_state)

    def _update_aim(self, inp, dt):
        if inp.up:
            self.angle = min(MAX_ANGLE, self.angle + AIM_SPEED * dt)
        if inp.down:
            self.angle = max(MIN_ANGLE, self.angle - AIM_SPEED * dt)
        if inp.action_l:
            # Start charging power
            self.power = 0.0
            self.phase = PHASE_POWER

    def _update_power(self, inp, dt):
        if inp.action_r:
            # Cancel back to aim
            self.phase = PHASE_AIM
            return

        if inp.action_l_held:
            # Charge while holding
            self.power = min(1.0, self.power + POWER_CHARGE_SPEED * dt)
        else:
            # Released — fire with current power (minimum 0.15 so it always goes somewhere)
            self.power = max(0.15, self.power)
            self._fire_dart()

    def _update_flight(self, dt):
        # Substep for collision accuracy
        substeps = 3
        sub_dt = dt / substeps
        for _ in range(substeps):
            # Save trail position
            self.trail.append((self.dart_x, self.dart_y))
            if len(self.trail) > TRAIL_LEN:
                self.trail.pop(0)

            # Apply gravity
            self.dart_vy += GRAVITY * sub_dt

            # Move
            self.dart_x += self.dart_vx * sub_dt
            self.dart_y += self.dart_vy * sub_dt

            # Check bloon collisions
            for bloon in self._alive_bloons():
                dx = self.dart_x - bloon['x']
                dy = self.dart_y - bloon['y']
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < DART_RADIUS:
                    self._pop_bloon(bloon)

            # Out of bounds?
            if (self.dart_x > 64 or self.dart_x < -5 or
                    self.dart_y > 64 or self.dart_y < -20):
                self._end_throw()
                return

        # Check if hit ground
        if self.dart_y >= GROUND_Y:
            self._end_throw()

    def _end_throw(self):
        """Dart finished flying."""
        self.darts_left -= 1

        alive = self._alive_bloons()
        if len(alive) == 0:
            # Level complete!
            self.phase = PHASE_LEVEL_WIN
            self.phase_timer = 2.0
            self.result_text = "LEVEL CLEAR!"
            return

        if self.darts_left <= 0:
            # Out of darts
            self.phase = PHASE_LEVEL_FAIL
            self.result_text = "OUT OF DARTS"
            return

        # Show result briefly
        if self.pops_this_throw > 0:
            self.result_text = f"+{self.pops_this_throw} POP"
        else:
            self.result_text = "MISS"
        self.phase = PHASE_RESULT
        self.phase_timer = 0.8

    def _update_result(self, dt):
        self.phase_timer -= dt
        if self.phase_timer <= 0:
            self.phase = PHASE_AIM
            self.angle = 0.7

    def _update_level_win(self, inp, dt):
        self.phase_timer -= dt
        if self.phase_timer <= 0 or inp.action_l:
            self.level += 1
            if self.level >= len(LEVELS):
                # Beat all levels!
                self.state = GameState.GAME_OVER
            else:
                self._load_level()

    def _update_level_fail(self, inp):
        if inp.action_l or inp.action_r:
            self.state = GameState.GAME_OVER

    # ==== DRAW ====

    def draw(self):
        self.display.clear(Colors.BLACK)

        if self.phase == PHASE_LEVEL_WIN:
            self._draw_level_win()
            return
        if self.phase == PHASE_LEVEL_FAIL:
            self._draw_level_fail()
            return

        # Sky
        self.display.draw_rect(0, HUD_HEIGHT, 64, GROUND_Y - HUD_HEIGHT, SKY_COLOR)
        # Clouds
        self._draw_clouds()
        # Ground
        self.display.draw_rect(0, GROUND_Y, 64, 64 - GROUND_Y, GROUND_COLOR)

        # Bloons
        self._draw_bloons()

        # Monkey
        self._draw_monkey()

        # Power bar (during power phase)
        if self.phase == PHASE_POWER:
            self._draw_power_bar()

        # Trajectory preview (during aim)
        if self.phase == PHASE_AIM:
            self._draw_trajectory_preview()

        # Dart in flight
        if self.phase == PHASE_FLIGHT:
            self._draw_dart()

        # Result text
        if self.phase == PHASE_RESULT:
            self._draw_result_text()

        # HUD
        self._draw_hud()

    def _draw_bloons(self):
        for bloon in self._alive_bloons():
            _, color, _, _ = BLOON_TYPES[bloon['type']]
            bx = int(bloon['x'])
            by = int(bloon['y'])
            # 3x3 sprite (cross shape for roundness)
            for dy in range(3):
                for dx in range(3):
                    self.display.set_pixel(bx + dx, by + dy, color)
            # Highlight top-left 2x1 for shine
            highlight = (min(255, color[0] + 60), min(255, color[1] + 60), min(255, color[2] + 60))
            self.display.set_pixel(bx, by, highlight)
            self.display.set_pixel(bx + 1, by, highlight)

    def _draw_clouds(self):
        """Draw a few small clouds in the sky."""
        cloud = (180, 210, 240)
        cloud_hi = (210, 230, 250)
        # Cloud 1: upper right
        for dx in range(5):
            self.display.set_pixel(45 + dx, 12, cloud)
        for dx in range(3):
            self.display.set_pixel(46 + dx, 11, cloud_hi)
        for dx in range(4):
            self.display.set_pixel(45 + dx, 13, cloud)
        # Cloud 2: mid left
        for dx in range(4):
            self.display.set_pixel(18 + dx, 20, cloud)
        for dx in range(3):
            self.display.set_pixel(18 + dx, 19, cloud_hi)
        for dx in range(3):
            self.display.set_pixel(19 + dx, 21, cloud)
        # Cloud 3: lower right
        for dx in range(6):
            self.display.set_pixel(50 + dx, 36, cloud)
        for dx in range(4):
            self.display.set_pixel(51 + dx, 35, cloud_hi)
        for dx in range(5):
            self.display.set_pixel(50 + dx, 37, cloud)

    def _draw_monkey(self):
        """Draw monkey sprite at fixed position."""
        brown = (139, 90, 43)
        dark_brown = (100, 60, 30)
        face = (200, 150, 100)

        mx, my = MONKEY_X, MONKEY_Y
        # Body (3x4)
        for dy in range(4):
            for dx in range(3):
                self.display.set_pixel(mx + dx, my + dy, brown)
        # Head (3x2)
        for dy in range(-2, 0):
            for dx in range(3):
                self.display.set_pixel(mx + dx, my + dy, brown)
        # Face
        self.display.set_pixel(mx + 1, my - 2, face)
        self.display.set_pixel(mx + 2, my - 2, face)
        self.display.set_pixel(mx + 1, my - 1, face)
        self.display.set_pixel(mx + 2, my - 1, face)
        # Eye
        self.display.set_pixel(mx + 2, my - 2, dark_brown)

        # Arm line at aim angle
        arm_len = 4
        ax = mx + 2 + int(math.cos(self.angle) * arm_len)
        ay = my - 1 - int(math.sin(self.angle) * arm_len)
        self.display.draw_line(mx + 2, my - 1, ax, ay, dark_brown)

    def _draw_trajectory_preview(self):
        """Dotted line showing approximate trajectory at mid power."""
        preview_power = 0.5
        speed = preview_power * MAX_SPEED
        vx = math.cos(self.angle) * speed
        vy = -math.sin(self.angle) * speed
        px = float(MONKEY_X + 3)
        py = float(MONKEY_Y - 2)
        dt = 0.05
        gray = (80, 80, 80)
        step = 0
        for _ in range(40):
            vy += GRAVITY * dt
            px += vx * dt
            py += vy * dt
            step += 1
            if step % 3 == 0:
                ix, iy = int(px), int(py)
                if 0 <= ix < 64 and HUD_HEIGHT <= iy < GROUND_Y:
                    self.display.set_pixel(ix, iy, gray)
            if py > GROUND_Y or px > 63 or px < 0:
                break

    def _draw_power_bar(self):
        """Vertical power bar on left edge."""
        bar_height = POWER_BAR_BOT - POWER_BAR_TOP
        filled = int(self.power * bar_height)

        # Background
        for y in range(POWER_BAR_TOP, POWER_BAR_BOT):
            for x in range(POWER_BAR_X, POWER_BAR_X + POWER_BAR_W):
                self.display.set_pixel(x, y, (30, 30, 30))

        # Filled portion (bottom to top)
        for i in range(filled):
            y = POWER_BAR_BOT - 1 - i
            ratio = i / bar_height
            if ratio < 0.5:
                color = Colors.GREEN
            elif ratio < 0.8:
                color = Colors.YELLOW
            else:
                color = Colors.RED
            for x in range(POWER_BAR_X, POWER_BAR_X + POWER_BAR_W):
                self.display.set_pixel(x, y, color)

    def _draw_dart(self):
        """Draw dart and trail."""
        # Trail
        for i, (tx, ty) in enumerate(self.trail):
            intensity = 40 + i * 25
            gray = (intensity, intensity, intensity)
            ix, iy = int(tx), int(ty)
            if 0 <= ix < 64 and 0 <= iy < 64:
                self.display.set_pixel(ix, iy, gray)

        # Dart head
        dx, dy = int(self.dart_x), int(self.dart_y)
        if 0 <= dx < 64 and 0 <= dy < 64:
            self.display.set_pixel(dx, dy, Colors.WHITE)

    def _draw_result_text(self):
        text = self.result_text
        tw = len(text) * 4
        tx = max(2, (64 - tw) // 2)
        self.display.draw_rect(tx - 1, 28, tw + 2, 7, (0, 0, 0))
        color = Colors.YELLOW if "POP" in text else Colors.RED
        self.display.draw_text_small(tx, 29, text, color)

    def _draw_hud(self):
        """Draw HUD bar at top."""
        # Dark background
        self.display.draw_rect(0, 0, 64, HUD_HEIGHT, Colors.BLACK)

        # Level number
        self.display.draw_text_small(2, 1, f"L{self.level + 1}", Colors.WHITE)

        # Score
        self.display.draw_text_small(18, 1, f"{self.score}", Colors.YELLOW)

        # Dart icons remaining (right side)
        for i in range(self.darts_left):
            x = 58 - i * 4
            # Small dart icon: 2px line
            self.display.set_pixel(x, 2, Colors.WHITE)
            self.display.set_pixel(x + 1, 2, Colors.WHITE)
            self.display.set_pixel(x + 1, 1, Colors.GRAY)

    def _draw_level_win(self):
        self.display.clear(Colors.BLACK)
        self.display.draw_text_small(6, 20, "LEVEL CLEAR!", Colors.GREEN)
        self.display.draw_text_small(10, 32, f"SCORE:{self.score}", Colors.WHITE)
        if self.level + 1 < len(LEVELS):
            self.display.draw_text_small(10, 44, f"NEXT: L{self.level + 2}", Colors.YELLOW)
        else:
            self.display.draw_text_small(10, 44, "YOU WIN!", Colors.YELLOW)

    def _draw_level_fail(self):
        self.display.clear(Colors.BLACK)
        self.display.draw_text_small(2, 20, "OUT OF DARTS", Colors.RED)
        self.display.draw_text_small(10, 32, f"SCORE:{self.score}", Colors.WHITE)
        self.display.draw_text_small(6, 48, "BTN:RETRY", Colors.GRAY)
