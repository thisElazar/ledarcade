"""
WINDOW WASHER — Side-Scrolling Job Game
=========================================
Clean all windows on a building before time runs out.
Building scrolls horizontally wider than the 64px screen.

Controls:
  Arrows      - Move washer
  Space (hold) - Clean window
"""

import math
import random
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE

# ═══════════════════════════════════════════════════════════════════
#  Constants
# ═══════════════════════════════════════════════════════════════════

PLAYER_W = 4
PLAYER_H = 6
MOVE_SPEED = 40.0  # pixels per second
CLEAN_TIME = 1.5   # seconds to clean a window
WINDOW_W = 8
WINDOW_H = 8
WINDOW_ROWS = 5
WINDOW_GAP_X = 2   # gap between windows
WINDOW_GAP_Y = 2   # gap between window rows
WINDOW_TOP_Y = 6   # first row y offset from top of building
RAIL_Y = 2          # rail at top of building
BUILDING_TOP = 4    # top of building facade

# Bayer 4x4 threshold matrix for dissolve effect
BAYER_4X4 = [
    [0,  8,  2, 10],
    [12, 4, 14,  6],
    [3, 11,  1,  9],
    [15, 7, 13,  5],
]

# Colors
BRICK = (140, 70, 40)
BRICK_DARK = (110, 55, 30)
MORTAR = (100, 80, 60)
DIRTY_WINDOW = (60, 70, 90)
FRAME_COLOR = (80, 85, 95)
ROPE_COLOR = (160, 140, 80)
HARDHAT = (255, 200, 0)
OVERALLS = (40, 80, 180)
SKIN = (220, 180, 140)
SKY_TOP = (30, 50, 100)
SKY_BOT = (60, 90, 140)
RAIL_COLOR = (120, 120, 130)

# ═══════════════════════════════════════════════════════════════════
#  Window scene definitions (6x6 pixel vignettes)
# ═══════════════════════════════════════════════════════════════════

def _scene_cat(buf):
    """Cat sitting on table."""
    # Table
    for x in range(6):
        buf[4][x] = (120, 80, 50)
    # Cat body
    buf[2][2] = buf[2][3] = (80, 80, 80)
    buf[3][2] = buf[3][3] = (80, 80, 80)
    # Ears
    buf[1][2] = buf[1][3] = (90, 90, 90)
    # Eyes
    buf[2][2] = (0, 200, 0)
    buf[2][3] = (0, 200, 0)
    # Tail
    buf[3][4] = buf[3][5] = (80, 80, 80)

def _scene_phone(buf):
    """Person on phone."""
    # Head
    buf[1][3] = SKIN
    buf[0][3] = (60, 40, 20)  # hair
    # Body
    buf[2][3] = buf[3][3] = (200, 60, 60)
    # Phone
    buf[1][4] = buf[2][4] = (40, 40, 40)
    # Arm
    buf[2][4] = (40, 40, 40)

def _scene_dance(buf):
    """Couple dancing."""
    # Person 1
    buf[1][1] = SKIN
    buf[2][1] = (200, 60, 60)
    buf[3][1] = (200, 60, 60)
    # Person 2
    buf[1][4] = SKIN
    buf[2][4] = (60, 60, 200)
    buf[3][4] = (60, 60, 200)
    # Arms together
    buf[2][2] = buf[2][3] = SKIN

def _scene_skeleton(buf):
    """Skeleton."""
    # Skull
    buf[0][2] = buf[0][3] = (240, 240, 230)
    buf[1][2] = (40, 40, 40)  # eye
    buf[1][3] = (40, 40, 40)  # eye
    # Spine
    buf[2][2] = buf[2][3] = (240, 240, 230)
    buf[3][2] = buf[3][3] = (240, 240, 230)
    # Ribs
    buf[2][1] = buf[2][4] = (220, 220, 210)
    buf[3][1] = buf[3][4] = (220, 220, 210)
    # Legs
    buf[4][2] = buf[4][3] = (240, 240, 230)

def _scene_alien(buf):
    """Alien."""
    # Big head
    buf[0][2] = buf[0][3] = (120, 200, 120)
    buf[1][1] = buf[1][2] = buf[1][3] = buf[1][4] = (120, 200, 120)
    # Eyes
    buf[1][2] = (0, 0, 0)
    buf[1][3] = (0, 0, 0)
    # Body
    buf[2][2] = buf[2][3] = (100, 180, 100)
    buf[3][2] = buf[3][3] = (100, 180, 100)

def _scene_fishtank(buf):
    """Fish tank."""
    # Water bg
    for y in range(6):
        for x in range(6):
            buf[y][x] = (30, 60, 120)
    # Fish
    buf[2][1] = buf[2][2] = buf[2][3] = (255, 140, 0)
    buf[2][4] = (255, 140, 0)  # tail
    buf[1][3] = (255, 140, 0)  # tail top
    buf[2][1] = (255, 255, 255)  # eye
    # Bubbles
    buf[0][4] = (100, 160, 220)
    # Gravel
    buf[5][0] = buf[5][2] = buf[5][4] = (120, 100, 60)
    buf[5][1] = buf[5][3] = buf[5][5] = (100, 80, 50)

def _scene_plants(buf):
    """Window with plants."""
    # Pot
    buf[4][2] = buf[4][3] = (180, 100, 60)
    buf[5][2] = buf[5][3] = (160, 80, 40)
    # Stems + leaves
    buf[3][2] = buf[3][3] = (40, 160, 40)
    buf[2][1] = buf[2][3] = (60, 200, 60)
    buf[1][2] = buf[1][4] = (40, 180, 40)
    buf[0][3] = (60, 200, 60)

def _scene_piano(buf):
    """Piano."""
    # Piano body
    for x in range(6):
        buf[3][x] = (40, 30, 20)
        buf[4][x] = (40, 30, 20)
    # Keys
    for x in range(6):
        buf[2][x] = (240, 240, 240) if x % 2 == 0 else (20, 20, 20)

def _scene_tv(buf):
    """Person watching TV."""
    # TV
    buf[1][0] = buf[1][1] = buf[1][2] = (40, 40, 45)
    buf[2][0] = buf[2][1] = buf[2][2] = (80, 120, 200)  # screen
    # Person on couch
    buf[3][4] = SKIN  # head
    buf[4][4] = (60, 60, 60)  # body
    # Couch
    buf[4][3] = buf[4][5] = (150, 60, 60)

def _scene_cooking(buf):
    """Cooking."""
    # Stove
    for x in range(4):
        buf[4][x] = (60, 60, 65)
    # Pot
    buf[3][1] = buf[3][2] = (140, 140, 145)
    # Steam
    buf[1][1] = buf[0][2] = buf[1][3] = (200, 200, 210)
    # Person
    buf[3][4] = SKIN
    buf[4][4] = (255, 255, 255)  # apron

def _scene_reading(buf):
    """Person reading."""
    # Chair
    buf[4][3] = buf[4][4] = (120, 80, 40)
    # Person
    buf[2][4] = SKIN  # head
    buf[3][4] = (60, 120, 60)  # body
    # Book
    buf[3][2] = buf[3][3] = (240, 230, 200)
    buf[2][3] = (240, 230, 200)

def _scene_yoga(buf):
    """Yoga pose."""
    # Head
    buf[0][3] = SKIN
    # Body
    buf[1][3] = (200, 80, 200)
    buf[2][3] = (200, 80, 200)
    # Arms out
    buf[1][1] = buf[1][5] = SKIN
    buf[1][2] = buf[1][4] = SKIN
    # Legs
    buf[3][2] = buf[3][4] = (200, 80, 200)
    # Mat
    for x in range(6):
        buf[4][x] = (80, 160, 80)

def _scene_dog(buf):
    """Dog."""
    # Body
    buf[3][1] = buf[3][2] = buf[3][3] = (180, 140, 80)
    buf[2][1] = buf[2][2] = (180, 140, 80)
    # Head
    buf[2][0] = (180, 140, 80)
    buf[1][0] = (180, 140, 80)
    # Eye
    buf[1][0] = (40, 40, 40)
    # Ears
    buf[0][0] = (150, 110, 60)
    # Tail
    buf[2][4] = buf[1][5] = (180, 140, 80)

def _scene_ghost(buf):
    """Ghost."""
    # Ghost body
    buf[1][2] = buf[1][3] = (220, 220, 230)
    buf[2][1] = buf[2][2] = buf[2][3] = buf[2][4] = (220, 220, 230)
    buf[3][1] = buf[3][2] = buf[3][3] = buf[3][4] = (220, 220, 230)
    buf[4][1] = buf[4][3] = (220, 220, 230)
    # Eyes
    buf[2][2] = (20, 20, 40)
    buf[2][3] = (20, 20, 40)

def _scene_robot(buf):
    """Robot."""
    # Head
    buf[0][2] = buf[0][3] = (160, 160, 170)
    buf[1][2] = buf[1][3] = (160, 160, 170)
    # Eyes (LEDs)
    buf[1][2] = (255, 0, 0)
    buf[1][3] = (0, 255, 0)
    # Body
    buf[2][1] = buf[2][2] = buf[2][3] = buf[2][4] = (140, 140, 150)
    buf[3][1] = buf[3][2] = buf[3][3] = buf[3][4] = (140, 140, 150)
    # Arms
    buf[2][0] = buf[2][5] = (120, 120, 130)

def _scene_boxing(buf):
    """Boxing."""
    # Person 1
    buf[1][1] = SKIN
    buf[2][1] = (255, 0, 0)
    # Person 2
    buf[1][4] = SKIN
    buf[2][4] = (0, 0, 255)
    # Gloves meeting
    buf[2][2] = buf[2][3] = (200, 0, 0)

def _scene_empty(buf):
    """Empty room — just light coming in."""
    for y in range(6):
        for x in range(6):
            shade = 160 + (x * 10)
            buf[y][x] = (shade, shade - 10, shade - 20)

def _scene_disco(buf):
    """Disco ball."""
    # Ball
    buf[0][3] = (200, 200, 200)
    buf[1][2] = buf[1][3] = buf[1][4] = (220, 220, 230)
    buf[2][3] = (200, 200, 200)
    # Light rays
    buf[3][1] = (255, 100, 100)
    buf[3][5] = (100, 100, 255)
    buf[4][0] = (255, 255, 100)
    buf[4][4] = (100, 255, 100)

def _scene_bath(buf):
    """Bathtub."""
    # Tub
    for x in range(6):
        buf[4][x] = (220, 220, 230)
    buf[3][0] = buf[3][5] = (220, 220, 230)
    # Water
    buf[3][1] = buf[3][2] = buf[3][3] = buf[3][4] = (100, 160, 220)
    # Bubbles
    buf[2][2] = buf[2][4] = (240, 240, 250)

def _scene_weights(buf):
    """Weightlifter."""
    # Head
    buf[0][3] = SKIN
    # Body
    buf[1][3] = buf[2][3] = (255, 60, 60)
    # Arms up holding bar
    buf[0][1] = buf[0][2] = buf[0][4] = buf[0][5] = (80, 80, 90)
    buf[1][1] = buf[1][5] = SKIN
    # Legs
    buf[3][2] = buf[3][4] = (40, 40, 120)

# Scene pool
SCENES = [
    _scene_cat, _scene_phone, _scene_dance, _scene_skeleton,
    _scene_alien, _scene_fishtank, _scene_plants, _scene_piano,
    _scene_tv, _scene_cooking, _scene_reading, _scene_yoga,
    _scene_dog, _scene_ghost, _scene_robot, _scene_boxing,
    _scene_empty, _scene_disco, _scene_bath, _scene_weights,
]


# ═══════════════════════════════════════════════════════════════════
#  Game Class
# ═══════════════════════════════════════════════════════════════════

class WindowWasher(Game):
    name = "WINDOW WASHER"
    description = "Clean all windows"
    category = "unique"

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0
        self.level = 1
        self.time = 0.0
        self.phase = 'title'
        self.phase_timer = 2.5

        self._load_level(1)

    def _load_level(self, level):
        """Set up a new building for the given level."""
        self.level = level
        self.level_complete = False

        # Building dimensions
        self.num_cols = 5 + level  # windows per row
        self.building_w = self.num_cols * (WINDOW_W + WINDOW_GAP_X) + WINDOW_GAP_X + 8  # padding
        self.building_h = GRID_SIZE

        # Timer
        self.timer = max(30.0, 90.0 - (level - 1) * 10.0)
        self.par_time = self.timer * 0.6  # par = 60% of time

        # Cleaning speed (gets slower at higher levels)
        self.clean_speed = 1.0 / max(1.0, CLEAN_TIME + (level - 1) * 0.2)

        # Player position (world coords)
        self.player_x = float(self.building_w // 2)
        self.player_y = float(BUILDING_TOP + WINDOW_TOP_Y + 2)

        # Camera
        self.camera_x = 0.0

        # Windows: list of dicts
        self.windows = []
        scene_pool = list(SCENES)
        for row in range(WINDOW_ROWS):
            for col in range(self.num_cols):
                wx = 4 + col * (WINDOW_W + WINDOW_GAP_X)
                wy = BUILDING_TOP + WINDOW_TOP_Y + row * (WINDOW_H + WINDOW_GAP_Y)
                scene_fn = random.choice(scene_pool)
                # Pre-render scene into 6x6 buffer
                scene_buf = [[(0, 0, 0)] * 6 for _ in range(6)]
                scene_fn(scene_buf)
                self.windows.append({
                    'x': wx,
                    'y': wy,
                    'clean': 0.0,  # 0=dirty, 1=clean
                    'scene': scene_buf,
                })

        # Rope sway
        self.rope_sway = 0.0

        self.phase = 'playing'

    def _window_at_player(self):
        """Find window overlapping player position, if any."""
        px = int(self.player_x)
        py = int(self.player_y)
        for w in self.windows:
            if (w['x'] <= px <= w['x'] + WINDOW_W - 1 and
                    w['y'] <= py <= w['y'] + WINDOW_H - 1):
                return w
        return None

    # ─────────────────────────────────────────────────────────────
    #  Update
    # ─────────────────────────────────────────────────────────────

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        self.time += dt

        if self.phase == 'title':
            self.phase_timer -= dt
            if self.phase_timer <= 0:
                self.phase = 'playing'
            return

        if self.phase == 'fired':
            self.phase_timer -= dt
            if self.phase_timer <= 0:
                self.state = GameState.GAME_OVER
            return

        if self.phase == 'level_clear':
            self.phase_timer -= dt
            if self.phase_timer <= 0:
                self._load_level(self.level + 1)
            return

        # Timer
        self.timer -= dt
        if self.timer <= 0:
            self.timer = 0
            self.phase = 'fired'
            self.phase_timer = 2.5
            return

        # Movement
        nx = self.player_x
        ny = self.player_y
        if input_state.left:
            nx -= MOVE_SPEED * dt
        if input_state.right:
            nx += MOVE_SPEED * dt
        if input_state.up:
            ny -= MOVE_SPEED * dt
        if input_state.down:
            ny += MOVE_SPEED * dt

        # Clamp to building bounds
        nx = max(2.0, min(float(self.building_w - 3), nx))
        ny = max(float(BUILDING_TOP + 2), min(float(GRID_SIZE - PLAYER_H - 1), ny))
        self.player_x = nx
        self.player_y = ny

        # Smooth camera follow
        target_cam = self.player_x - GRID_SIZE / 2
        target_cam = max(0.0, min(float(self.building_w - GRID_SIZE), target_cam))
        self.camera_x += (target_cam - self.camera_x) * min(1.0, 5.0 * dt)

        # Rope sway
        self.rope_sway = math.sin(self.time * 1.5) * 1.5

        # Cleaning
        if input_state.action_l_held:
            w = self._window_at_player()
            if w and w['clean'] < 1.0:
                w['clean'] = min(1.0, w['clean'] + self.clean_speed * dt)

        # Check level complete
        if all(w['clean'] >= 1.0 for w in self.windows):
            if not self.level_complete:
                self.level_complete = True
                # Score
                time_bonus = max(0, self.timer) * 5
                window_pts = len(self.windows) * 10
                par_bonus = 0
                if self.timer >= self.par_time:
                    par_bonus = window_pts  # double bonus
                self.score += int(window_pts + time_bonus + par_bonus)
                self.phase = 'level_clear'
                self.phase_timer = 2.5

    # ─────────────────────────────────────────────────────────────
    #  Drawing
    # ─────────────────────────────────────────────────────────────

    def draw(self):
        self.display.clear(Colors.BLACK)

        if self.phase == 'title':
            self._draw_title()
            return

        if self.phase == 'fired':
            self._draw_fired()
            return

        if self.phase == 'level_clear':
            self._draw_level_clear()
            return

        cam = int(self.camera_x)

        # Sky gradient
        for y in range(BUILDING_TOP):
            t = y / max(1, BUILDING_TOP - 1)
            r = int(SKY_TOP[0] * (1 - t) + SKY_BOT[0] * t)
            g = int(SKY_TOP[1] * (1 - t) + SKY_BOT[1] * t)
            b = int(SKY_TOP[2] * (1 - t) + SKY_BOT[2] * t)
            for x in range(GRID_SIZE):
                self.display.set_pixel(x, y, (r, g, b))

        # Rail at top of building
        for x in range(GRID_SIZE):
            wx = x + cam
            if 0 <= wx < self.building_w:
                self.display.set_pixel(x, BUILDING_TOP, RAIL_COLOR)
                if wx % 4 == 0:
                    self.display.set_pixel(x, BUILDING_TOP - 1, RAIL_COLOR)

        # Brick facade
        for y in range(BUILDING_TOP + 1, GRID_SIZE):
            for x in range(GRID_SIZE):
                wx = x + cam
                if wx < 0 or wx >= self.building_w:
                    continue
                # Brick pattern
                brick_row = (y - BUILDING_TOP) // 3
                offset = 4 if brick_row % 2 else 0
                brick_col = (wx + offset) % 8
                if (y - BUILDING_TOP) % 3 == 0 or brick_col == 0:
                    self.display.set_pixel(x, y, MORTAR)
                else:
                    # Vary brick color slightly
                    seed = (wx * 7 + y * 13) % 17
                    if seed < 3:
                        self.display.set_pixel(x, y, BRICK_DARK)
                    else:
                        self.display.set_pixel(x, y, BRICK)

        # Windows
        for w in self.windows:
            self._draw_window(w, cam)

        # Rope from rail to player
        rope_x = int(self.player_x - cam)
        rail_screen_y = BUILDING_TOP
        player_screen_y = int(self.player_y)
        if 0 <= rope_x < GRID_SIZE:
            for y in range(rail_screen_y, player_screen_y):
                t = (y - rail_screen_y) / max(1, player_screen_y - rail_screen_y)
                sway = int(self.rope_sway * t * t)
                rx = rope_x + sway
                if 0 <= rx < GRID_SIZE:
                    self.display.set_pixel(rx, y, ROPE_COLOR)

        # Player
        self._draw_player(cam)

        # HUD
        # Timer
        secs = int(self.timer)
        timer_color = Colors.WHITE
        if secs <= 10:
            timer_color = Colors.RED
        elif secs <= 20:
            timer_color = Colors.ORANGE
        timer_txt = str(secs)
        self.display.draw_text_small(2, 1, timer_txt, timer_color)

        # Score (top right)
        score_txt = str(self.score)
        sx = 63 - len(score_txt) * 4
        self.display.draw_text_small(sx, 1, score_txt, Colors.WHITE)

        # Windows remaining (bottom)
        remaining = sum(1 for w in self.windows if w['clean'] < 1.0)
        self.display.draw_text_small(2, 58, f"L{self.level}", (100, 255, 180))
        rem_txt = f"{remaining}"
        rx = 63 - len(rem_txt) * 4
        dirty_color = Colors.YELLOW if remaining > 0 else Colors.GREEN
        self.display.draw_text_small(rx, 58, rem_txt, dirty_color)

    def _draw_window(self, w, cam):
        """Draw a single window with cleaning dissolve effect."""
        sx = w['x'] - cam
        sy = w['y']

        # Frame (1px border)
        for x in range(WINDOW_W):
            scx = sx + x
            if 0 <= scx < GRID_SIZE:
                if 0 <= sy < GRID_SIZE:
                    self.display.set_pixel(scx, sy, FRAME_COLOR)
                if 0 <= sy + WINDOW_H - 1 < GRID_SIZE:
                    self.display.set_pixel(scx, sy + WINDOW_H - 1, FRAME_COLOR)
        for y in range(WINDOW_H):
            scy = sy + y
            if 0 <= scy < GRID_SIZE:
                if 0 <= sx < GRID_SIZE:
                    self.display.set_pixel(sx, scy, FRAME_COLOR)
                if 0 <= sx + WINDOW_W - 1 < GRID_SIZE:
                    self.display.set_pixel(sx + WINDOW_W - 1, scy, FRAME_COLOR)

        # Interior (6x6 inside frame)
        clean = w['clean']
        threshold = int(clean * 16)  # 0..16 Bayer levels

        for py in range(6):
            for px in range(6):
                scx = sx + 1 + px
                scy = sy + 1 + py
                if not (0 <= scx < GRID_SIZE and 0 <= scy < GRID_SIZE):
                    continue

                bayer_val = BAYER_4X4[py % 4][px % 4]
                if bayer_val < threshold:
                    # Clean — show scene
                    r, g, b = w['scene'][py][px]
                    if r == 0 and g == 0 and b == 0:
                        # Default interior warm light
                        r, g, b = 180, 160, 120
                    self.display.set_pixel(scx, scy, (r, g, b))
                else:
                    # Dirty
                    self.display.set_pixel(scx, scy, DIRTY_WINDOW)

    def _draw_player(self, cam):
        """Draw the window washer character (4x6)."""
        sx = int(self.player_x) - cam - 1
        sy = int(self.player_y)

        # Hard hat (row 0)
        for x in range(PLAYER_W):
            px = sx + x
            if 0 <= px < GRID_SIZE and 0 <= sy < GRID_SIZE:
                self.display.set_pixel(px, sy, HARDHAT)

        # Head/face (row 1)
        for x in range(1, PLAYER_W - 1):
            px = sx + x
            if 0 <= px < GRID_SIZE and 0 <= sy + 1 < GRID_SIZE:
                self.display.set_pixel(px, sy + 1, SKIN)

        # Overalls (rows 2-4)
        for dy in range(2, 5):
            for x in range(PLAYER_W):
                px = sx + x
                if 0 <= px < GRID_SIZE and 0 <= sy + dy < GRID_SIZE:
                    self.display.set_pixel(px, sy + dy, OVERALLS)

        # Boots (row 5)
        for x in range(PLAYER_W):
            px = sx + x
            if 0 <= px < GRID_SIZE and 0 <= sy + 5 < GRID_SIZE:
                self.display.set_pixel(px, sy + 5, (40, 30, 20))

    def _draw_title(self):
        """Title screen."""
        self.display.clear((30, 50, 100))

        # Building silhouette
        for y in range(30, 64):
            for x in range(10, 54):
                self.display.set_pixel(x, y, (80, 50, 35))
        # Some windows on silhouette
        for row in range(4):
            for col in range(5):
                wx = 14 + col * 8
                wy = 34 + row * 7
                for dy in range(4):
                    for dx in range(4):
                        self.display.set_pixel(wx + dx, wy + dy, (200, 180, 100))

        self.display.draw_text_small(6, 4, "WINDOW", Colors.YELLOW)
        self.display.draw_text_small(6, 12, "WASHER", Colors.CYAN)

        if int(self.time * 3) % 2 == 0:
            self.display.draw_text_small(6, 22, "PRESS START", Colors.ORANGE)

    def _draw_fired(self):
        """Game over — YOU'RE FIRED."""
        self.display.clear((60, 10, 10))
        self.display.draw_text_small(2, 14, "YOU'RE", Colors.RED)
        self.display.draw_text_small(2, 22, "FIRED!", Colors.RED)
        self.display.draw_text_small(2, 36, f"SCORE:{self.score}", Colors.WHITE)
        self.display.draw_text_small(2, 46, f"LEVEL:{self.level}", Colors.GRAY)

    def _draw_level_clear(self):
        """Level complete screen."""
        self.display.clear((10, 30, 10))
        self.display.draw_text_small(2, 8, f"LEVEL {self.level}", Colors.GREEN)
        self.display.draw_text_small(2, 16, "COMPLETE!", (100, 255, 180))

        window_pts = len(self.windows) * 10
        time_bonus = int(max(0, self.timer) * 5)
        par_bonus = window_pts if self.timer >= self.par_time else 0

        self.display.draw_text_small(2, 28, f"CLEAN:{window_pts}", Colors.WHITE)
        self.display.draw_text_small(2, 36, f"TIME:+{time_bonus}", Colors.YELLOW)
        if par_bonus > 0:
            self.display.draw_text_small(2, 44, f"PAR:+{par_bonus}", Colors.CYAN)
        self.display.draw_text_small(2, 54, f"TOTAL:{self.score}", Colors.ORANGE)

    def draw_game_over(self, selection: int = 0):
        """Game over screen."""
        self._draw_fired()
        if selection == 0:
            self.display.draw_text_small(2, 54, ">RETRY", Colors.YELLOW)
            self.display.draw_text_small(34, 54, " MENU", Colors.GRAY)
        else:
            self.display.draw_text_small(2, 54, " RETRY", Colors.GRAY)
            self.display.draw_text_small(34, 54, ">MENU", Colors.YELLOW)
