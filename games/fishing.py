"""
Fishing - Catch fish, don't let them escape!
=============================================
Side-view underwater fishing game. Score accumulates across catches.
Press button on the bite (not the nibbles!) and hold/mash to reel in.

Controls:
  Up/Down    - Adjust lure depth
  Space/Z    - Hook fish (hold or mash to reel)
  Escape     - Return to menu
"""

import random
import math
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE

# ── Fish color palette ──────────────────────────────────────────────────────
FISH_COLORS = [
    (255, 140, 50),   # orange
    (180, 220, 80),   # yellow-green
    (200, 200, 210),  # silver
    (80, 200, 190),   # teal
    (240, 130, 160),  # pink
]

# ── Sky / water gradients ──────────────────────────────────────────────────
SKY_COLORS = [
    (10, 10, 40),
    (15, 15, 50),
    (20, 20, 60),
    (25, 25, 70),
    (30, 30, 80),
]

WATER_LINE_COLOR = (100, 180, 230)
SAND_COLOR = (140, 110, 60)
SAND_DARK = (110, 85, 45)
SEAWEED_COLOR = (40, 140, 50)


def _water_color(y):
    """Return a blue gradient color for depth y (13-59)."""
    t = (y - 13) / 46.0
    r = int(5 + t * 5)
    g = int(30 + (1 - t) * 40)
    b = int(80 + (1 - t) * 60)
    return (r, g, b)


def _lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


class _Fish:
    """A single swimming fish."""

    def __init__(self):
        self.respawn()

    def respawn(self):
        self.heading = random.choice([-1, 1])
        self.y = random.uniform(18, 55)
        if self.heading > 0:
            self.x = random.uniform(-10, -2)
        else:
            self.x = random.uniform(66, 74)
        self.speed = random.uniform(6, 14)
        self.sin_amp = random.uniform(0.5, 2.0)
        self.sin_freq = random.uniform(0.8, 2.0)
        self.sin_phase = random.uniform(0, math.tau)
        self.color = random.choice(FISH_COLORS)
        # Weight via log-normal-ish distribution
        self.weight = round(random.uniform(0.5, 1.5) ** 3 * 10, 1)
        self.weight = max(0.1, self.weight)
        self.alive = True
        self.attracted = False  # currently swimming toward lure
        self.attract_target = None

    @property
    def size_cat(self):
        if self.weight < 2:
            return 0  # tiny
        if self.weight < 5:
            return 1  # small
        if self.weight < 12:
            return 2  # medium
        return 3  # large

    @property
    def body_len(self):
        return [2, 3, 4, 5][self.size_cat]

    @property
    def tail_len(self):
        return [1, 1, 2, 2][self.size_cat]

    def update(self, dt, time_acc):
        if self.attracted and self.attract_target:
            tx, ty = self.attract_target
            dx = tx - self.x
            dy = ty - self.y
            dist = math.hypot(dx, dy)
            if dist > 0.5:
                self.x += (dx / dist) * self.speed * 0.7 * dt
                self.y += (dy / dist) * self.speed * 0.7 * dt
                self.heading = 1 if dx > 0 else -1
        else:
            self.x += self.heading * self.speed * dt
            self.y += math.sin(time_acc * self.sin_freq + self.sin_phase) * self.sin_amp * dt

    def off_screen(self):
        return self.x < -15 or self.x > 79


class Fishing(Game):
    name = "FISHING"
    description = "Catch fish, don't let them escape!"
    category = "unique"

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0.0
        self.fish_count = 0
        self.time = 0.0

        # Phase state machine
        self.phase = "casting"
        self.phase_timer = 0.0

        # Lure / line
        self.lure_depth = 35.0  # target row (18-55)
        self.lure_y = 12.0     # current animated y
        self.bobber_y = 12.0
        self.bobber_base_y = 12.0

        # Fish pool
        self.fish = [_Fish() for _ in range(5)]

        # Target fish (during attracting/nibbling/biting)
        self.target = None

        # Nibble state
        self.nibbles_remaining = 0
        self.nibble_pause = 0.0
        self.nibble_active = False
        self.nibble_bob_timer = 0.0

        # Catch meter
        self.catch_meter = 50.0
        self.catch_duration = 0.0

        # Flash overlay
        self.flash_timer = 0.0
        self.flash_text = ""
        self.flash_color = Colors.WHITE

        # Seaweed positions (fixed per reset)
        self.seaweed = []
        for _ in range(8):
            sx = random.randint(0, 63)
            sh = random.randint(2, 5)
            self.seaweed.append((sx, sh))

        # Bubbles
        self.bubbles = []

        # "!" indicator
        self.exclaim_timer = 0.0

    # ── UPDATE ──────────────────────────────────────────────────────────────

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        self.time += dt

        # Spawn bubbles occasionally
        if random.random() < 0.3 * dt:
            self.bubbles.append([random.uniform(0, 63), random.uniform(40, 58), random.uniform(8, 20)])
        # Update bubbles
        self.bubbles = [
            [bx, by - bspd * dt, bspd]
            for bx, by, bspd in self.bubbles
            if by - bspd * dt > 13
        ]

        # Respawn off-screen fish
        for f in self.fish:
            if f.off_screen() and not f.attracted:
                f.respawn()

        # Update fish movement
        for f in self.fish:
            if f.alive:
                f.update(dt, self.time)

        # Decrement flash
        if self.flash_timer > 0:
            self.flash_timer -= dt

        if self.exclaim_timer > 0:
            self.exclaim_timer -= dt

        # Phase dispatch
        handler = getattr(self, f"_update_{self.phase}", None)
        if handler:
            handler(input_state, dt)

    def _update_casting(self, inp, dt):
        """Line drops to lure depth."""
        self.phase_timer += dt
        t = min(1.0, self.phase_timer / 0.8)
        self.lure_y = 12 + (self.lure_depth - 12) * t
        if t >= 1.0:
            self.phase = "waiting"
            self.phase_timer = 0.0

    def _update_waiting(self, inp, dt):
        """Player adjusts depth; fish swim around. Check for attraction."""
        # Depth adjustment
        if inp.up:
            self.lure_depth = max(18, self.lure_depth - 20 * dt)
        if inp.down:
            self.lure_depth = min(55, self.lure_depth + 20 * dt)
        self.lure_y += (self.lure_depth - self.lure_y) * 5 * dt

        # Check if any fish is heading toward lure
        lx, ly = 10, self.lure_y  # lure position (x=10, below bobber)
        for f in self.fish:
            if f.attracted:
                continue
            # Fish must be swimming toward the lure and within range
            dx = lx - f.x
            dy = ly - f.y
            dist = math.hypot(dx, dy)
            # Fish heading toward lure (within ~8px ahead, within ~6px vertically)
            if (f.heading > 0 and 0 < dx < 12) or (f.heading < 0 and -12 < dx < 0):
                if abs(dy) < 6 and dist < 15:
                    # Probability increases as fish gets closer
                    if random.random() < 0.5 * dt:
                        self._start_attract(f)
                        return

    def _start_attract(self, fish):
        self.target = fish
        fish.attracted = True
        fish.attract_target = (10, self.lure_y)
        self.phase = "attracting"
        self.phase_timer = 0.0
        # Attract nearby fish too (visual only)
        for f in self.fish:
            if f is not fish and not f.attracted:
                d = math.hypot(f.x - fish.x, f.y - fish.y)
                if d < 12:
                    f.attracted = True
                    f.attract_target = (10 + random.uniform(-3, 3),
                                        self.lure_y + random.uniform(-3, 3))

    def _update_attracting(self, inp, dt):
        """Target fish curves toward lure."""
        self.phase_timer += dt
        if self.target:
            self.target.attract_target = (10, self.lure_y)
            d = math.hypot(self.target.x - 10, self.target.y - self.lure_y)
            if d < 2.0 or self.phase_timer > 2.5:
                self._start_nibble()

    def _start_nibble(self):
        w = self.target.weight
        if w < 2:
            self.nibbles_remaining = random.randint(1, 2)
            self.nibble_pause = random.uniform(1.0, 2.0)
            self.catch_duration = 1.5
        elif w < 5:
            self.nibbles_remaining = random.randint(2, 3)
            self.nibble_pause = random.uniform(0.7, 1.5)
            self.catch_duration = 2.5
        elif w < 12:
            self.nibbles_remaining = random.randint(3, 5)
            self.nibble_pause = random.uniform(0.4, 1.0)
            self.catch_duration = 4.0
        else:
            self.nibbles_remaining = random.randint(4, 6)
            self.nibble_pause = random.uniform(0.2, 0.7)
            self.catch_duration = 6.0
        self.nibble_active = False
        self.phase = "nibbling"
        self.phase_timer = 0.0

    def _update_nibbling(self, inp, dt):
        """Bobber bobs. Button press during nibble = game over."""
        # Any button press during nibbles is a fail
        if inp.action_l or inp.action_r:
            self.state = GameState.GAME_OVER
            return

        self.phase_timer += dt

        if self.nibble_active:
            # Bobber bob animation
            self.nibble_bob_timer += dt
            self.bobber_y = self.bobber_base_y + math.sin(self.nibble_bob_timer * 15) * 1.0
            if self.nibble_bob_timer > 0.3:
                self.nibble_active = False
                self.bobber_y = self.bobber_base_y
                self.nibbles_remaining -= 1
                if self.nibbles_remaining <= 0:
                    self._start_bite()
                    return
                # Next pause
                w = self.target.weight
                if w < 2:
                    self.nibble_pause = random.uniform(1.0, 2.0)
                elif w < 5:
                    self.nibble_pause = random.uniform(0.7, 1.5)
                elif w < 12:
                    self.nibble_pause = random.uniform(0.4, 1.0)
                else:
                    self.nibble_pause = random.uniform(0.2, 0.7)
                self.phase_timer = 0.0
        else:
            # Waiting between nibbles
            if self.phase_timer >= self.nibble_pause:
                self.nibble_active = True
                self.nibble_bob_timer = 0.0

    def _start_bite(self):
        self.phase = "biting"
        self.phase_timer = 0.0
        self.catch_meter = 50.0
        self.exclaim_timer = 0.8
        self.bobber_y = self.bobber_base_y + 3  # plunge

    def _update_biting(self, inp, dt):
        """Player must hold or mash to fill catch meter."""
        self.phase_timer += dt

        # Button hold raises meter
        if inp.action_l_held or inp.action_r_held:
            self.catch_meter += 60 * dt
        # Button press (mash) adds burst
        if inp.action_l or inp.action_r:
            self.catch_meter += 15

        # Fish resistance drains meter
        resistance = self.target.weight * 3
        self.catch_meter -= resistance * dt

        # Clamp
        self.catch_meter = max(0, min(100, self.catch_meter))

        # Bobber oscillation during fight
        self.bobber_y = self.bobber_base_y + 2 + math.sin(self.time * 8) * 1.0

        if self.catch_meter >= 100:
            self._catch_fish()
        elif self.catch_meter <= 0:
            # Fish escaped
            self.state = GameState.GAME_OVER

    def _catch_fish(self):
        self.phase = "caught"
        self.phase_timer = 0.0
        self.score += self.target.weight
        self.score = round(self.score, 1)
        self.fish_count += 1
        self.flash_text = f"{self.target.weight}LB"
        self.flash_timer = 2.0
        self.flash_color = Colors.YELLOW
        # Remove caught fish
        self.target.alive = False
        if self.target in self.fish:
            self.fish.remove(self.target)
            self.fish.append(_Fish())

    def _update_caught(self, inp, dt):
        """Brief celebration, then auto-cast."""
        self.phase_timer += dt
        # Release attracted fish
        for f in self.fish:
            f.attracted = False
            f.attract_target = None
        if self.phase_timer > 2.0:
            self.target = None
            self.phase = "casting"
            self.phase_timer = 0.0
            self.bobber_y = self.bobber_base_y
            self.lure_y = 12.0

    # ── DRAW ────────────────────────────────────────────────────────────────

    def draw(self):
        self.display.clear(Colors.BLACK)
        self._draw_scene()
        self._draw_fish_sprites()
        self._draw_line_and_lure()
        self._draw_hud()

        # Catch meter during biting phase
        if self.phase == "biting":
            self._draw_catch_meter()

        # Exclamation mark
        if self.exclaim_timer > 0:
            ex = 10
            ey = int(self.bobber_y) - 5
            self.display.draw_text_small(ex - 1, max(7, ey), "!", Colors.YELLOW)

        # Flash text (caught fish)
        if self.flash_timer > 0:
            alpha = min(1.0, self.flash_timer / 0.5)
            fc = _lerp_color(Colors.BLACK, self.flash_color, alpha)
            self.display.draw_text_small(20, 28, self.flash_text, fc)

    def _draw_scene(self):
        # Sky (rows 7-11)
        for y in range(7, 12):
            idx = min(len(SKY_COLORS) - 1, y - 7)
            for x in range(GRID_SIZE):
                self.display.set_pixel(x, y, SKY_COLORS[idx])

        # Waterline (row 12)
        for x in range(GRID_SIZE):
            shimmer = int(20 * math.sin(self.time * 2 + x * 0.5))
            c = (100 + shimmer, 180 + shimmer, 230)
            self.display.set_pixel(x, 12, c)

        # Underwater (rows 13-59)
        for y in range(13, 60):
            c = _water_color(y)
            for x in range(GRID_SIZE):
                self.display.set_pixel(x, y, c)

        # Seabed (rows 60-63)
        for y in range(60, 64):
            for x in range(GRID_SIZE):
                c = SAND_DARK if (x + y) % 3 == 0 else SAND_COLOR
                self.display.set_pixel(x, y, c)

        # Seaweed
        for sx, sh in self.seaweed:
            sway = math.sin(self.time * 1.5 + sx) * 1.0
            for dy in range(sh):
                wy = 59 - dy
                wx = int(sx + sway * (dy / sh))
                if 0 <= wx < 64 and 13 <= wy < 60:
                    self.display.set_pixel(wx, wy, SEAWEED_COLOR)

        # Bubbles
        for bx, by, _ in self.bubbles:
            ix, iy = int(bx), int(by)
            if 0 <= ix < 64 and 13 <= iy < 60:
                self.display.set_pixel(ix, iy, (180, 220, 255))

    def _draw_fish_sprites(self):
        for f in self.fish:
            if not f.alive:
                continue
            fx, fy = int(f.x), int(f.y)
            bl = f.body_len
            tl = f.tail_len
            # Body
            for dx in range(bl):
                px = fx + dx * f.heading
                if 0 <= px < 64 and 13 <= fy < 60:
                    self.display.set_pixel(px, fy, f.color)
                # Taller body for medium/large
                if f.size_cat >= 2 and 13 <= fy - 1 < 60 and 0 <= px < 64:
                    self.display.set_pixel(px, fy - 1, f.color)
            # Tail
            tail_start = fx - f.heading * 1
            for dx in range(tl):
                px = tail_start - dx * f.heading
                if 0 <= px < 64 and 13 <= fy < 60:
                    tc = _lerp_color(f.color, (80, 80, 80), 0.4)
                    self.display.set_pixel(px, fy, tc)
            # Eye
            eye_x = fx + (bl - 1) * f.heading
            eye_y = fy - 1 if f.size_cat >= 2 else fy
            if 0 <= eye_x < 64 and 13 <= eye_y < 60:
                self.display.set_pixel(eye_x, eye_y, Colors.WHITE)

    def _draw_line_and_lure(self):
        # Rod tip at (2, 7)
        rod_x, rod_y = 2, 7
        bob_x = 10
        bob_y = int(self.bobber_y)
        lure_y = int(self.lure_y)

        # Line: rod tip to bobber
        self.display.draw_line(rod_x, rod_y, bob_x, bob_y, (180, 180, 180))
        # Line: bobber to lure
        self.display.draw_line(bob_x, bob_y, bob_x, lure_y, (180, 180, 180))

        # Bobber (2px wide red/white)
        if 0 <= bob_y < 64:
            self.display.set_pixel(bob_x, bob_y, Colors.RED)
            self.display.set_pixel(bob_x, bob_y - 1, Colors.WHITE)
            self.display.set_pixel(bob_x + 1, bob_y, Colors.RED)

        # Lure (small hook)
        if 13 <= lure_y < 60:
            self.display.set_pixel(bob_x, lure_y, Colors.YELLOW)
            self.display.set_pixel(bob_x, lure_y + 1, (200, 200, 200))

    def _draw_catch_meter(self):
        """Vertical meter bar on right side."""
        bar_x = 60
        bar_top = 10
        bar_bottom = 55
        bar_height = bar_bottom - bar_top
        fill = int(self.catch_meter / 100.0 * bar_height)

        # Background
        for y in range(bar_top, bar_bottom + 1):
            self.display.set_pixel(bar_x, y, (40, 40, 40))
            self.display.set_pixel(bar_x + 1, y, (40, 40, 40))

        # Filled portion (from bottom up)
        for y in range(bar_bottom - fill, bar_bottom + 1):
            t = (bar_bottom - y) / bar_height
            c = _lerp_color(Colors.RED, Colors.GREEN, t)
            self.display.set_pixel(bar_x, y, c)
            self.display.set_pixel(bar_x + 1, y, c)

    def _draw_hud(self):
        # Separator
        self.display.draw_line(0, 6, 63, 6, Colors.DARK_GRAY)
        # Score (total weight)
        score_str = f"{self.score:.1f}LB" if self.score > 0 else "0.0LB"
        self.display.draw_text_small(1, 1, score_str, Colors.WHITE)
        # Fish count
        count_str = f"x{self.fish_count}"
        self.display.draw_text_small(48, 1, count_str, Colors.CYAN)

    def draw_game_over(self, selection=0):
        self.display.clear(Colors.BLACK)
        self.display.draw_text_small(8, 16, "GAME OVER", Colors.RED)
        score_str = f"{self.score:.1f}LB"
        self.display.draw_text_small(2, 26, f"TOTAL:{score_str}", Colors.WHITE)
        self.display.draw_text_small(2, 34, f"FISH:{self.fish_count}", Colors.CYAN)
        if selection == 0:
            self.display.draw_text_small(4, 46, ">PLAY AGAIN", Colors.YELLOW)
            self.display.draw_text_small(4, 54, " MENU", Colors.GRAY)
        else:
            self.display.draw_text_small(4, 46, " PLAY AGAIN", Colors.GRAY)
            self.display.draw_text_small(4, 54, ">MENU", Colors.YELLOW)
