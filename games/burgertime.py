"""
BurgerTime - Classic Arcade Game (1982 Data East)
==================================================
Walk over burger ingredients to drop them down!
Avoid the enemies - use pepper to stun them.

Controls:
  Arrow Keys - Move (4-way on platforms/ladders)
  Space      - Throw pepper (limited supply)
"""

import random
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


# =============================================================================
# Layout constants
# =============================================================================

FLOOR_Y = [8, 16, 24, 32, 40, 48]     # 6 floors, 8px apart, shifted up for plate room
PLATE_Y = 62                           # Where completed burgers land (near bottom)

BURGER_X = [4, 20, 36, 52]            # Left edge of each 8px ingredient
INGREDIENT_WIDTH = 8

# Base burger platform zones (always present on every active floor)
# Each burger column gets a walkable zone around it
BURGER_ZONES = [
    (0, 12),    # Burger 0
    (19, 28),   # Burger 1
    (35, 44),   # Burger 2
    (51, 63),   # Burger 3
]


def compute_platform_segments(floor_code):
    """Convert a 3-char connectivity code into platform segments.

    floor_code is a 3-char string for the 3 gaps between 4 burger zones:
      'X' = walkway connects adjacent zones
      '.' = gap (no walkway)

    Returns list of (x1, x2) tuples for each contiguous platform segment.
    """
    # Start with 4 isolated zones
    zones = [list(z) for z in BURGER_ZONES]

    # Merge adjacent zones where connected
    # Process right-to-left so indices stay valid
    for i in range(2, -1, -1):
        if floor_code[i] == 'X':
            # Merge zone i and zone i+1
            zones[i][1] = zones[i + 1][1]
            zones.pop(i + 1)

    return [(z[0], z[1]) for z in zones]


# =============================================================================
# Level definitions
# =============================================================================
# Each level defines:
#   floors  - 6 connectivity codes (top to bottom)
#   ladders - list of (x, top_floor_idx, bottom_floor_idx)
#   ingredients - list of (burger_col, floor_idx, type)
#     burger_col 0-3, floor_idx 0-5

LEVELS = [
    # Level 1 — "Getting Started" — generous ladders, mostly connected
    {
        'floors': ['XXX', 'X.X', 'XXX', '.X.', 'X.X', 'XXX'],
        'ladders': [
            (6,  0, 1), (6,  2, 3), (6,  4, 5),
            (22, 0, 1), (22, 1, 2), (22, 3, 4),
            (38, 1, 2), (38, 2, 3), (38, 3, 4),
            (54, 0, 1), (54, 2, 3), (54, 4, 5),
            (60, 1, 2), (60, 3, 4),
        ],
        'ingredients': [
            (0, 0, 'bun_top'), (0, 1, 'lettuce'), (0, 2, 'meat'), (0, 3, 'bun_bottom'),
            (1, 0, 'bun_top'), (1, 1, 'tomato'),  (1, 3, 'meat'), (1, 4, 'bun_bottom'),
            (2, 0, 'bun_top'), (2, 1, 'lettuce'), (2, 2, 'meat'), (2, 3, 'bun_bottom'),
            (3, 0, 'bun_top'), (3, 1, 'tomato'),  (3, 3, 'meat'), (3, 4, 'bun_bottom'),
        ],
    },
    # Level 2 — "Staircase" — zigzag connectivity forces ladder use
    {
        'floors': ['X..', '.X.', '..X', 'X..', '.X.', 'XXX'],
        'ladders': [
            (6,  0, 1), (26, 0, 1), (42, 0, 1), (60, 0, 1),
            (6,  1, 2), (26, 1, 2), (38, 1, 2), (54, 1, 2),
            (10, 2, 3), (22, 2, 3), (38, 2, 3), (54, 2, 3),
            (6,  3, 4), (22, 3, 4), (38, 3, 4), (54, 3, 4),
            (6,  4, 5), (26, 4, 5), (54, 4, 5),
        ],
        'ingredients': [
            (0, 0, 'bun_top'), (0, 1, 'meat'),    (0, 3, 'lettuce'), (0, 4, 'bun_bottom'),
            (1, 0, 'bun_top'), (1, 2, 'tomato'),  (1, 3, 'meat'),    (1, 4, 'bun_bottom'),
            (2, 1, 'bun_top'), (2, 2, 'lettuce'), (2, 4, 'meat'),    (2, 5, 'bun_bottom'),
            (3, 1, 'bun_top'), (3, 2, 'tomato'),  (3, 3, 'meat'),    (3, 5, 'bun_bottom'),
        ],
    },
    # Level 3 — "Checkerboard" — alternating center/edge connected
    {
        'floors': ['.X.', 'X.X', '.X.', 'X.X', '.X.', 'XXX'],
        'ladders': [
            (6,  0, 1), (6,  2, 3), (6,  4, 5),
            (26, 0, 1), (26, 1, 2), (26, 2, 3), (26, 3, 4), (26, 4, 5),
            (42, 0, 1), (42, 1, 2), (42, 2, 3), (42, 3, 4), (42, 4, 5),
            (60, 0, 1), (60, 2, 3), (60, 4, 5),
        ],
        'ingredients': [
            (0, 0, 'bun_top'), (0, 2, 'meat'),    (0, 3, 'lettuce'), (0, 4, 'bun_bottom'),
            (1, 0, 'bun_top'), (1, 1, 'tomato'),  (1, 3, 'meat'),    (1, 4, 'bun_bottom'),
            (2, 0, 'bun_top'), (2, 2, 'lettuce'), (2, 3, 'meat'),    (2, 4, 'bun_bottom'),
            (3, 0, 'bun_top'), (3, 1, 'tomato'),  (3, 2, 'meat'),    (3, 4, 'bun_bottom'),
        ],
    },
    # Level 4 — "Dense Open" — wide top, fragmented bottom, many ladders
    {
        'floors': ['XXX', 'XXX', '.X.', 'XXX', 'XXX', '...'],
        'ladders': [
            (6,  0, 1), (6,  2, 3), (6,  4, 5),
            (22, 0, 1), (22, 1, 2), (22, 3, 4),
            (26, 2, 3), (26, 4, 5),
            (38, 1, 2), (38, 2, 3), (38, 3, 4),
            (42, 0, 1), (42, 4, 5),
            (54, 1, 2), (54, 3, 4),
            (60, 0, 1), (60, 2, 3), (60, 4, 5),
        ],
        'ingredients': [
            (0, 0, 'bun_top'), (0, 1, 'lettuce'), (0, 3, 'meat'),    (0, 4, 'bun_bottom'),
            (1, 0, 'bun_top'), (1, 2, 'tomato'),  (1, 3, 'lettuce'), (1, 4, 'bun_bottom'),
            (2, 0, 'bun_top'), (2, 2, 'meat'),    (2, 3, 'tomato'),  (2, 4, 'bun_bottom'),
            (3, 0, 'bun_top'), (3, 1, 'meat'),    (3, 3, 'lettuce'), (3, 4, 'bun_bottom'),
        ],
    },
    # Level 5 — "Most Fragmented" — isolated islands, heavy ladder reliance
    {
        'floors': ['...', '.X.', '...', 'X.X', '...', 'XXX'],
        'ladders': [
            (6,  0, 1), (6,  2, 3), (6,  4, 5),
            (10, 1, 2), (10, 3, 4),
            (26, 0, 1), (26, 2, 3), (26, 4, 5),
            (42, 0, 1), (42, 1, 2), (42, 2, 3), (42, 3, 4), (42, 4, 5),
            (54, 1, 2), (54, 3, 4),
            (60, 0, 1), (60, 2, 3), (60, 4, 5),
        ],
        'ingredients': [
            (0, 0, 'bun_top'), (0, 2, 'lettuce'), (0, 3, 'meat'),    (0, 4, 'bun_bottom'),
            (1, 1, 'bun_top'), (1, 2, 'tomato'),  (1, 3, 'meat'),    (1, 5, 'bun_bottom'),
            (2, 1, 'bun_top'), (2, 2, 'lettuce'), (2, 3, 'tomato'),  (2, 5, 'bun_bottom'),
            (3, 0, 'bun_top'), (3, 2, 'meat'),    (3, 3, 'lettuce'), (3, 4, 'bun_bottom'),
        ],
    },
    # Level 6 — "Split Left-Right" — left on even floors, right on odd
    {
        'floors': ['X..', '..X', '...', 'X..', '..X', 'XXX'],
        'ladders': [
            (6,  0, 1), (22, 0, 1), (42, 0, 1), (54, 0, 1),
            (10, 1, 2), (42, 1, 2), (60, 1, 2),
            (6,  2, 3), (22, 2, 3), (54, 2, 3),
            (10, 3, 4), (26, 3, 4), (42, 3, 4), (60, 3, 4),
            (6,  4, 5), (26, 4, 5), (54, 4, 5), (60, 4, 5),
        ],
        'ingredients': [
            (0, 0, 'bun_top'), (0, 2, 'meat'),    (0, 3, 'lettuce'), (0, 4, 'bun_bottom'),
            (1, 0, 'bun_top'), (1, 1, 'tomato'),  (1, 3, 'meat'),    (1, 4, 'bun_bottom'),
            (2, 1, 'bun_top'), (2, 2, 'lettuce'), (2, 4, 'meat'),    (2, 5, 'bun_bottom'),
            (3, 1, 'bun_top'), (3, 2, 'tomato'),  (3, 3, 'lettuce'), (3, 5, 'bun_bottom'),
        ],
    },
]


class BurgerTime(Game):
    name = "BURGERTIME"
    description = "Stack the burgers!"
    category = "arcade"

    # Colors
    CHEF_COLOR = Colors.WHITE
    CHEF_HAT = Colors.WHITE
    CHEF_BODY = (100, 100, 200)  # Blue clothes
    CHEF_SKIN = (255, 200, 150)

    PLATFORM_COLOR = (100, 80, 60)  # Brown
    PLATFORM_EDGE = (80, 60, 40)
    LADDER_COLOR = (150, 200, 255)  # Light blue

    # Ingredient colors
    BUN_TOP_COLOR = (210, 160, 80)     # Golden brown
    LETTUCE_COLOR = (80, 200, 80)      # Green
    MEAT_COLOR = (139, 69, 19)         # Brown
    TOMATO_COLOR = (200, 50, 50)       # Red
    BUN_BOTTOM_COLOR = (180, 140, 60)  # Darker golden

    # Enemy colors
    HOTDOG_COLOR = (200, 100, 80)
    EGG_COLOR = Colors.WHITE
    EGG_YOLK = Colors.YELLOW
    PICKLE_COLOR = (80, 160, 80)

    PEPPER_COLOR = Colors.YELLOW

    # Game constants
    MOVE_SPEED = 30.0
    CLIMB_SPEED = 25.0
    ENEMY_SPEED = 12.0
    ENEMY_CLIMB_SPEED = 8.0
    INGREDIENT_FALL_SPEED = 45.0
    CASCADE_DELAY = 0.12  # Stagger between cascade steps

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0
        self.lives = 3
        self.level = 1
        self.peppers = 5

        # Chef position
        self.chef_x = 30.0
        self.chef_y = float(FLOOR_Y[5])
        self.on_ladder = False
        self.facing = 1  # 1=right, -1=left
        self.walk_frame = 0
        self.walk_timer = 0.0

        # Pepper attack
        self.pepper_active = False
        self.pepper_x = 0
        self.pepper_y = 0
        self.pepper_timer = 0.0

        # Build level
        self.build_level()

        # Win check
        self.win_timer = 0.0

    def build_level(self):
        """Build platforms, ladders, ingredients, and enemies from level data."""
        self.platforms = []
        self.ladders = []
        self.ingredients = []
        self.enemies = []
        self.plates = []
        self.plate_slots = [0] * len(BURGER_X)  # Track stacking per column

        level_data = LEVELS[(self.level - 1) % len(LEVELS)]

        # Build platforms from floor connectivity codes
        for floor_idx, floor_code in enumerate(level_data['floors']):
            y = FLOOR_Y[floor_idx]
            segments = compute_platform_segments(floor_code)
            for x1, x2 in segments:
                self.platforms.append({
                    'x1': x1, 'x2': x2, 'y': y,
                    'floor_idx': floor_idx,
                })

        # Build ladders
        for lx, top_floor, bot_floor in level_data['ladders']:
            self.ladders.append({
                'x': lx,
                'y1': FLOOR_Y[top_floor],
                'y2': FLOOR_Y[bot_floor],
            })

        # Build ingredients
        for burger_col, floor_idx, ing_type in level_data['ingredients']:
            self.ingredients.append({
                'type': ing_type,
                'x': BURGER_X[burger_col],
                'y': FLOOR_Y[floor_idx] - 2,
                'width': INGREDIENT_WIDTH,
                'walked': [False] * INGREDIENT_WIDTH,
                'falling': False,
                'fall_speed': 0,
                'fall_delay': 0.0,
                'target_y': None,
                'carrying_enemies': [],
                'col_idx': burger_col,
                'floor_idx': floor_idx,
                'at_plate': False,
            })

        # Plates at bottom for each burger column
        for bx in BURGER_X:
            self.plates.append({'x': bx, 'y': PLATE_Y})

        # Spawn enemies — arcade-accurate staged composition
        # (hotdogs, eggs, pickles) per level
        spawn_table = [
            (2, 1, 0),  # Level 1: 2 hotdogs, 1 egg
            (3, 1, 0),  # Level 2: 3 hotdogs, 1 egg
            (2, 1, 1),  # Level 3: 2 hotdogs, 1 egg, 1 pickle
            (2, 1, 2),  # Level 4: 2 hotdogs, 1 egg, 2 pickles
            (3, 1, 2),  # Level 5+: 3 hotdogs, 1 egg, 2 pickles
        ]
        idx = min(self.level - 1, len(spawn_table) - 1)
        n_hotdog, n_egg, n_pickle = spawn_table[idx]
        enemy_list = (['hotdog'] * n_hotdog +
                      ['egg'] * n_egg +
                      ['pickle'] * n_pickle)

        for enemy_type in enemy_list:
            # Spawn on upper floors (0-3), avoiding bottom floor
            floor_idx = random.randint(0, 3)
            ex = self._random_x_on_floor(floor_idx)
            self.enemies.append({
                'type': enemy_type,
                'x': float(ex),
                'y': float(FLOOR_Y[floor_idx]),
                'on_ladder': False,
                'stunned': 2.0,  # Brief grace period at level start
                'direction': random.choice([-1, 1]),
                'wander_timer': 0.0,
                'reverse_cooldown': 0.0,
                'ladder_target_y': None,
                'ladder_encounter_cd': 0.0,
            })

    def _random_x_on_floor(self, floor_idx):
        """Return a random valid x position on the given floor."""
        level_data = LEVELS[(self.level - 1) % len(LEVELS)]
        floor_code = level_data['floors'][floor_idx]
        segments = compute_platform_segments(floor_code)
        seg = random.choice(segments)
        # Pick a position with some margin from edges
        margin = 3
        x1 = seg[0] + margin
        x2 = seg[1] - margin
        if x2 < x1:
            return (seg[0] + seg[1]) // 2
        return random.randint(x1, x2)

    def get_platform_at(self, x, y):
        """Check if there's a platform at this position."""
        for platform in self.platforms:
            if platform['x1'] <= x <= platform['x2']:
                if abs(y - platform['y']) < 3:
                    return platform
        return None

    def _on_platform_segment(self, x, y):
        """Check if position (x, y) is on a valid platform segment.

        Returns True if x is within some platform at floor y.
        """
        for platform in self.platforms:
            if abs(y - platform['y']) < 3:
                if platform['x1'] <= x <= platform['x2']:
                    return True
        return False

    def get_ladder_at(self, x, y, prefer_up=False, prefer_down=False):
        """Check if there's a ladder at this position.

        When at a boundary between two ladders, prefer_up/prefer_down
        helps select the right one for the direction we want to go.
        """
        candidates = []
        for ladder in self.ladders:
            if abs(x - ladder['x']) < 3:
                if ladder['y1'] - 2 <= y <= ladder['y2'] + 2:
                    candidates.append(ladder)

        if not candidates:
            return None

        if len(candidates) == 1:
            return candidates[0]

        # Multiple ladders at this position (boundary case)
        if prefer_up:
            for ladder in candidates:
                if ladder['y1'] < y:
                    return ladder
        elif prefer_down:
            for ladder in candidates:
                if ladder['y2'] > y:
                    return ladder

        return candidates[0]

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        # Win animation
        if self.win_timer > 0:
            self.win_timer -= dt
            if self.win_timer <= 0:
                self.next_level()
            return

        # Update pepper
        if self.pepper_active:
            self.pepper_timer -= dt
            if self.pepper_timer <= 0:
                self.pepper_active = False

        # Chef movement
        self.update_chef(input_state, dt)

        # Check ingredient walking
        self.check_ingredient_walk()

        # Update falling ingredients
        self.update_ingredients(dt)

        # Update enemies
        self.update_enemies(dt)

        # Check enemy collision with chef
        self.check_enemy_collision()

        # Check win condition
        if self.check_win():
            self.win_timer = 1.5
            self.score += 100 * self.level

    def update_chef(self, input_state: InputState, dt: float):
        """Update chef movement with platform-edge bounds checking."""
        moved = False

        ladder = self.get_ladder_at(self.chef_x, self.chef_y,
                                     prefer_up=input_state.up,
                                     prefer_down=input_state.down)
        platform = self.get_platform_at(self.chef_x, self.chef_y)

        if self.on_ladder:
            # Safety: if we've climbed past the ladder bounds, exit ladder
            if not ladder:
                self.on_ladder = False
                nearest_floor = min(FLOOR_Y, key=lambda f: abs(f - self.chef_y))
                if abs(self.chef_y - nearest_floor) < 4:
                    self.chef_y = float(nearest_floor)
            # Climbing movement
            elif input_state.up:
                self.chef_y -= self.CLIMB_SPEED * dt
                moved = True
                if ladder and self.chef_y < ladder['y1']:
                    self.chef_y = ladder['y1']
                    self.on_ladder = False
            elif input_state.down:
                self.chef_y += self.CLIMB_SPEED * dt
                moved = True
                if ladder and self.chef_y > ladder['y2']:
                    self.chef_y = ladder['y2']
                    self.on_ladder = False

            # Step off ladder horizontally
            if input_state.left or input_state.right:
                if platform:
                    self.on_ladder = False
        else:
            # Snap y to nearest floor to prevent drift
            nearest_floor = min(FLOOR_Y, key=lambda f: abs(f - self.chef_y))
            if abs(self.chef_y - nearest_floor) < 3:
                self.chef_y = float(nearest_floor)

            # Platform movement with edge checking
            if input_state.left:
                new_x = self.chef_x - self.MOVE_SPEED * dt
                if self._on_platform_segment(new_x, self.chef_y):
                    self.chef_x = new_x
                    self.facing = -1
                    moved = True
                else:
                    self.facing = -1
            elif input_state.right:
                new_x = self.chef_x + self.MOVE_SPEED * dt
                if self._on_platform_segment(new_x, self.chef_y):
                    self.chef_x = new_x
                    self.facing = 1
                    moved = True
                else:
                    self.facing = 1

            # Grab ladder — only if there's room to climb in the desired direction
            if input_state.up and ladder and ladder['y1'] < self.chef_y - 1:
                self.on_ladder = True
                self.chef_x = float(ladder['x'])
            elif input_state.down and ladder and ladder['y2'] > self.chef_y + 1:
                self.on_ladder = True
                self.chef_x = float(ladder['x'])

        # Throw pepper (either action button)
        if (input_state.action_l or input_state.action_r) and self.peppers > 0 and not self.pepper_active:
            self.peppers -= 1
            self.pepper_active = True
            self.pepper_x = self.chef_x + (self.facing * 6)
            self.pepper_y = self.chef_y
            self.pepper_timer = 0.5

            # Stun nearby enemies
            for enemy in self.enemies:
                if abs(enemy['x'] - self.pepper_x) < 10 and abs(enemy['y'] - self.pepper_y) < 8:
                    enemy['stunned'] = 3.0
                    self.score += 25

        # Walk animation
        if moved:
            self.walk_timer += dt
            if self.walk_timer > 0.12:
                self.walk_timer = 0
                self.walk_frame = (self.walk_frame + 1) % 2

    def check_ingredient_walk(self):
        """Check if chef is walking over any ingredients."""
        chef_left = int(self.chef_x) - 2
        chef_right = int(self.chef_x) + 2

        for ing in self.ingredients:
            if ing['falling']:
                continue

            # Check if chef is on this ingredient's level and overlapping
            if abs(self.chef_y - (ing['y'] + 2)) < 3:
                for i in range(ing['width']):
                    pixel_x = ing['x'] + i
                    if chef_left <= pixel_x <= chef_right:
                        ing['walked'][i] = True

                # Check if fully walked - award points for dropping
                if all(ing['walked']):
                    # Don't drop if this column already has a cascade in progress
                    col_busy = any(
                        o['falling'] and o['col_idx'] == ing['col_idx']
                        for o in self.ingredients
                    )
                    if not col_busy:
                        self.score += 50
                        self.drop_ingredient(ing)

    def drop_ingredient(self, ingredient, delay=0.0):
        """Drop an ingredient to the next floor, recursively cascading anything below.

        The entire cascade chain is set up deterministically with staggered
        delays so each piece visually pushes the next one down.
        """
        ingredient['walked'] = [False] * ingredient['width']

        # Check for enemies riding on this ingredient
        num_riding = 0
        for enemy in self.enemies:
            if enemy['stunned'] > 0:
                continue
            if (ingredient['x'] <= enemy['x'] <= ingredient['x'] + ingredient['width'] and
                    abs(enemy['y'] - ingredient['y'] - 2) < 5):
                ingredient['carrying_enemies'].append(enemy)
                enemy['stunned'] = 5.0
                num_riding += 1

        if num_riding > 0:
            self.score += 500 * (2 ** (num_riding - 1))

        extra_levels = num_riding * 2

        col = ingredient['col_idx']
        current_y = ingredient['y']

        # Find floors below with a platform under this burger column
        bx_center = BURGER_X[col] + INGREDIENT_WIDTH // 2
        floors_below = []
        for fy in FLOOR_Y:
            if fy <= current_y + 4:
                continue
            for plat in self.platforms:
                if abs(plat['y'] - fy) < 2 and plat['x1'] <= bx_center <= plat['x2']:
                    floors_below.append(fy)
                    break

        # Skip extra floors for enemies riding the ingredient
        target_floor = None
        skip = extra_levels
        for fy in floors_below:
            if skip > 0:
                skip -= 1
                continue
            target_floor = fy
            break

        if target_floor is not None:
            target_y = target_floor - 2

            # Recursive cascade: push any ingredient sitting at target floor first
            for other in self.ingredients:
                if other is not ingredient and not other['falling']:
                    if other.get('at_plate'):
                        continue
                    if other['col_idx'] == col and abs(other['y'] - target_y) < 3:
                        self.drop_ingredient(other, delay=delay + self.CASCADE_DELAY)
        else:
            # No more floors — land at the plate with proper stacking
            slot = self.plate_slots[col]
            target_y = PLATE_Y - 2 - (slot * 2)
            self.plate_slots[col] += 1
            ingredient['at_plate'] = True

        ingredient['target_y'] = target_y
        ingredient['falling'] = True
        ingredient['fall_delay'] = delay
        ingredient['fall_speed'] = self.INGREDIENT_FALL_SPEED

    def update_ingredients(self, dt: float):
        """Update falling ingredients (cascade is pre-computed in drop_ingredient)."""
        for ing in self.ingredients:
            if not ing['falling']:
                continue

            # Wait for cascade delay before starting to fall
            if ing['fall_delay'] > 0:
                ing['fall_delay'] -= dt
                continue

            ing['y'] += ing['fall_speed'] * dt

            # Move carried enemies
            for enemy in ing['carrying_enemies']:
                enemy['y'] = ing['y']

            # Crush enemies in the path of the falling ingredient
            for enemy in self.enemies:
                if enemy in ing['carrying_enemies']:
                    continue
                if enemy['stunned'] > 0:
                    continue
                if (ing['x'] - 1 <= enemy['x'] <= ing['x'] + ing['width'] + 1 and
                        abs(enemy['y'] - ing['y'] - 2) < 4):
                    enemy['stunned'] = 5.0
                    self.score += 300

            # Check if reached target
            if ing['y'] >= ing['target_y']:
                ing['y'] = ing['target_y']
                ing['falling'] = False
                ing['carrying_enemies'] = []
                # Update floor_idx to match new y position
                if not ing.get('at_plate'):
                    for fi, fy in enumerate(FLOOR_Y):
                        if abs((ing['y'] + 2) - fy) < 3:
                            ing['floor_idx'] = fi
                            break

    def _find_target_ladder(self, ex, ey, want_up):
        """Find nearest reachable ladder that goes up or down from (ex, ey)."""
        # Find which platform segment the enemy is on
        on_seg = None
        for plat in self.platforms:
            if abs(plat['y'] - ey) < 3 and plat['x1'] <= ex <= plat['x2']:
                on_seg = plat
                break
        if not on_seg:
            return None

        best = None
        best_dist = float('inf')
        for ladder in self.ladders:
            # Ladder must be on our platform segment (walkable)
            if ladder['x'] < on_seg['x1'] or ladder['x'] > on_seg['x2']:
                continue
            # Ladder must span our floor
            if ladder['y1'] > ey + 3 or ladder['y2'] < ey - 3:
                continue
            # Must extend in the desired direction
            if want_up and ladder['y1'] >= ey - 2:
                continue
            if not want_up and ladder['y2'] <= ey + 2:
                continue

            dist = abs(ladder['x'] - ex)
            if dist < best_dist:
                best_dist = dist
                best = ladder

        return best

    def update_enemies(self, dt: float):
        """Update enemy AI — ladder-happy pathfinding with no-reverse constraint."""
        for enemy in self.enemies:
            if enemy['stunned'] > 0:
                enemy['stunned'] -= dt
                continue

            # Tick down cooldowns
            if enemy['reverse_cooldown'] > 0:
                enemy['reverse_cooldown'] -= dt
            if enemy['ladder_encounter_cd'] > 0:
                enemy['ladder_encounter_cd'] -= dt

            dx = self.chef_x - enemy['x']
            dy = self.chef_y - enemy['y']

            h_speed = self.ENEMY_SPEED * (1 + self.level * 0.05)
            v_speed = self.ENEMY_CLIMB_SPEED * (1 + self.level * 0.05)

            if enemy['on_ladder']:
                ladder = self.get_ladder_at(enemy['x'], enemy['y'])
                # Use ladder_target_y if set (from ladder-happy encounter),
                # otherwise climb toward chef's floor
                target_y = enemy.get('ladder_target_y')
                if target_y is not None:
                    climb_dy = target_y - enemy['y']
                else:
                    climb_dy = dy

                if abs(climb_dy) > 2:
                    if climb_dy < 0:
                        enemy['y'] -= v_speed * dt
                        if ladder and enemy['y'] < ladder['y1']:
                            enemy['y'] = float(ladder['y1'])
                            enemy['on_ladder'] = False
                            enemy['ladder_target_y'] = None
                            enemy['wander_timer'] = 0.4
                    else:
                        enemy['y'] += v_speed * dt
                        if ladder and enemy['y'] > ladder['y2']:
                            enemy['y'] = float(ladder['y2'])
                            enemy['on_ladder'] = False
                            enemy['ladder_target_y'] = None
                            enemy['wander_timer'] = 0.4
                else:
                    # Reached target floor — snap and step off
                    enemy['on_ladder'] = False
                    enemy['ladder_target_y'] = None
                    nearest = min(FLOOR_Y, key=lambda f: abs(f - enemy['y']))
                    enemy['y'] = float(nearest)
                    enemy['wander_timer'] = 0.4
            else:
                # Snap y to nearest floor to prevent drift
                nearest = min(FLOOR_Y, key=lambda f: abs(f - enemy['y']))
                if abs(enemy['y'] - nearest) < 3:
                    enemy['y'] = float(nearest)

                # Wander mode: patrol back and forth, don't pathfind
                if enemy['wander_timer'] > 0:
                    enemy['wander_timer'] -= dt
                    self._enemy_wander(enemy, h_speed, dt)
                elif abs(dy) > 6:
                    # Different floor — find a ladder to get closer
                    want_up = dy < 0
                    target_ladder = self._find_target_ladder(
                        enemy['x'], enemy['y'], want_up)

                    if target_ladder:
                        ldx = target_ladder['x'] - enemy['x']
                        if abs(ldx) < 3:
                            # At the ladder — take it
                            enemy['on_ladder'] = True
                            enemy['x'] = float(target_ladder['x'])
                        else:
                            # Walk toward the ladder
                            direction = 1 if ldx > 0 else -1
                            # Respect reverse cooldown
                            if direction != enemy['direction'] and enemy['reverse_cooldown'] > 0:
                                direction = enemy['direction']
                            new_x = enemy['x'] + direction * h_speed * dt
                            if self._on_platform_segment(new_x, enemy['y']):
                                enemy['x'] = new_x
                                if direction != enemy['direction']:
                                    enemy['reverse_cooldown'] = 0.3
                                enemy['direction'] = direction
                            else:
                                # Can't reach ladder — wander to find another path
                                enemy['direction'] = -direction
                                enemy['reverse_cooldown'] = 0.3
                                enemy['wander_timer'] = 0.6
                    else:
                        # No useful ladder — wander until one becomes reachable
                        enemy['wander_timer'] = 0.8
                        self._enemy_wander(enemy, h_speed, dt)
                else:
                    # Same floor — chase player, but occasionally wander
                    if random.random() < 0.005:
                        enemy['wander_timer'] = random.uniform(0.4, 1.0)
                        enemy['direction'] = random.choice([-1, 1])
                    else:
                        self._enemy_chase_horizontal(enemy, dx, h_speed, dt)

                # Ladder-happy: check if we walked over a ladder (even on same floor).
                # Skip during wander (post-ladder cooldown) and encounter cooldown
                # (ensures one roll per ladder crossing, not per frame).
                if (not enemy['on_ladder'] and enemy['wander_timer'] <= 0
                        and enemy['ladder_encounter_cd'] <= 0):
                    self._check_ladder_encounter(enemy)

    def _enemy_wander(self, enemy, speed, dt):
        """Patrol in current direction, reversing at platform edges (with cooldown)."""
        new_x = enemy['x'] + enemy['direction'] * speed * dt
        if self._on_platform_segment(new_x, enemy['y']):
            enemy['x'] = new_x
        else:
            # Only reverse if cooldown has expired
            if enemy['reverse_cooldown'] <= 0:
                enemy['direction'] *= -1
                enemy['reverse_cooldown'] = 0.3

    def _enemy_chase_horizontal(self, enemy, dx, speed, dt):
        """Move enemy toward player horizontally, with no-reverse cooldown."""
        # Determine chase direction
        chase_dir = -1 if dx < 0 else 1

        # If chase wants a reversal but cooldown is active, keep current direction
        if chase_dir != enemy['direction'] and enemy['reverse_cooldown'] > 0:
            chase_dir = enemy['direction']

        new_x = enemy['x'] + chase_dir * speed * dt
        if self._on_platform_segment(new_x, enemy['y']):
            enemy['x'] = new_x
            if chase_dir != enemy['direction']:
                enemy['reverse_cooldown'] = 0.3
            enemy['direction'] = chase_dir
        else:
            # Hit edge — only reverse if cooldown allows
            if enemy['reverse_cooldown'] <= 0:
                enemy['direction'] = -chase_dir
                enemy['reverse_cooldown'] = 0.3

    def _check_ladder_encounter(self, enemy):
        """Ladder-happy: 30% chance to grab any ladder the enemy walks over.

        Sets ladder_target_y so the climbing code knows which floor to exit at,
        like the demo AI's ladder_exit_y pattern.
        """
        for ladder in self.ladders:
            if abs(enemy['x'] - ladder['x']) < 3:
                # Must span our current floor
                if ladder['y1'] > enemy['y'] + 3 or ladder['y2'] < enemy['y'] - 3:
                    continue
                # Find adjacent floors reachable via this ladder
                floors_up = [fy for fy in FLOOR_Y
                             if fy < enemy['y'] - 2 and fy >= ladder['y1'] - 2]
                floors_down = [fy for fy in FLOOR_Y
                               if fy > enemy['y'] + 2 and fy <= ladder['y2'] + 2]
                if not floors_up and not floors_down:
                    continue
                # One roll per ladder crossing — cooldown prevents re-checking
                enemy['ladder_encounter_cd'] = 1.0
                # 30% chance to take it
                if random.random() < 0.30:
                    # Pick climb direction: prefer toward player, 30% wrong way
                    dy = self.chef_y - enemy['y']
                    want_up = dy < 0
                    if floors_up and floors_down:
                        if random.random() < 0.30:
                            want_up = not want_up  # Go wrong way
                    elif floors_up:
                        want_up = True
                    else:
                        want_up = False

                    # Pick the nearest floor in the chosen direction
                    if want_up and floors_up:
                        target_y = max(floors_up)  # closest floor above
                    elif not want_up and floors_down:
                        target_y = min(floors_down)  # closest floor below
                    elif floors_up:
                        target_y = max(floors_up)
                    else:
                        target_y = min(floors_down)

                    enemy['on_ladder'] = True
                    enemy['x'] = float(ladder['x'])
                    enemy['ladder_target_y'] = float(target_y)
                    return
                break  # Decided to walk past — skip remaining ladders

    def check_enemy_collision(self):
        """Check if chef collides with any enemy."""
        for enemy in self.enemies:
            if enemy['stunned'] > 0:
                continue

            if (abs(enemy['x'] - self.chef_x) < 3 and
                    abs(enemy['y'] - self.chef_y) < 3):
                self.die()
                return

    def die(self):
        """Chef loses a life."""
        self.lives -= 1
        if self.lives <= 0:
            self.state = GameState.GAME_OVER
        else:
            # Respawn chef on bottom floor
            self.chef_x = float(self._random_x_on_floor(5))
            self.chef_y = float(FLOOR_Y[5])
            self.on_ladder = False

            # Reset enemies to upper floors
            for enemy in self.enemies:
                floor_idx = random.randint(0, 3)
                enemy['x'] = float(self._random_x_on_floor(floor_idx))
                enemy['y'] = float(FLOOR_Y[floor_idx])
                enemy['stunned'] = 2.0
                enemy['on_ladder'] = False
                enemy['wander_timer'] = 0.0
                enemy['reverse_cooldown'] = 0.0
                enemy['ladder_target_y'] = None
                enemy['ladder_encounter_cd'] = 0.0

    def check_win(self):
        """Check if all ingredients have reached the plate."""
        for ing in self.ingredients:
            if ing['falling']:
                return False
            if not ing['at_plate']:
                return False
        return True

    def next_level(self):
        """Advance to next level."""
        self.level += 1
        self.peppers = min(self.peppers + 2, 9)
        self.chef_x = float(self._random_x_on_floor(5))
        self.chef_y = float(FLOOR_Y[5])
        self.on_ladder = False
        self.build_level()

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Draw plates
        for plate in self.plates:
            self.display.draw_rect(plate['x'], plate['y'], INGREDIENT_WIDTH, 2, Colors.GRAY)

        # Draw platforms
        for platform in self.platforms:
            for x in range(platform['x1'], platform['x2'] + 1):
                self.display.set_pixel(x, platform['y'], self.PLATFORM_COLOR)
                self.display.set_pixel(x, platform['y'] + 1, self.PLATFORM_EDGE)

        # Draw ladders
        for ladder in self.ladders:
            for y in range(ladder['y1'], ladder['y2'] + 1):
                self.display.set_pixel(ladder['x'] - 1, y, self.LADDER_COLOR)
                self.display.set_pixel(ladder['x'] + 1, y, self.LADDER_COLOR)
                if y % 3 == 0:
                    self.display.set_pixel(ladder['x'], y, self.LADDER_COLOR)

        # Draw ingredients
        for ing in self.ingredients:
            self.draw_ingredient(ing)

        # Draw pepper effect
        if self.pepper_active:
            for i in range(3):
                px = int(self.pepper_x) + random.randint(-2, 2)
                py = int(self.pepper_y) + random.randint(-2, 2)
                self.display.set_pixel(px, py, self.PEPPER_COLOR)

        # Draw enemies
        for enemy in self.enemies:
            self.draw_enemy(enemy)

        # Draw chef
        self.draw_chef()

        # Draw HUD
        self.draw_hud()

    def draw_ingredient(self, ing):
        """Draw a burger ingredient."""
        x, y = int(ing['x']), int(ing['y'])

        if ing['type'] == 'bun_top':
            color = self.BUN_TOP_COLOR
            # Rounded bun top
            self.display.draw_rect(x + 1, y, 6, 1, color)
            self.display.draw_rect(x, y + 1, 8, 1, color)
            # Sesame seeds
            self.display.set_pixel(x + 2, y, Colors.WHITE)
            self.display.set_pixel(x + 5, y, Colors.WHITE)
        elif ing['type'] == 'lettuce':
            color = self.LETTUCE_COLOR
            for i in range(8):
                offset = 1 if i % 2 == 0 else 0
                self.display.set_pixel(x + i, y + offset, color)
                self.display.set_pixel(x + i, y + 1 - offset, (60, 180, 60))
        elif ing['type'] == 'meat':
            color = self.MEAT_COLOR
            self.display.draw_rect(x, y, 8, 2, color)
            # Grill marks
            self.display.set_pixel(x + 2, y, (100, 50, 10))
            self.display.set_pixel(x + 5, y, (100, 50, 10))
        elif ing['type'] == 'tomato':
            color = self.TOMATO_COLOR
            self.display.draw_rect(x, y, 8, 2, color)
            # Seeds
            self.display.set_pixel(x + 2, y + 1, (255, 200, 200))
            self.display.set_pixel(x + 5, y + 1, (255, 200, 200))
        elif ing['type'] == 'bun_bottom':
            color = self.BUN_BOTTOM_COLOR
            self.display.draw_rect(x, y, 8, 2, color)

        # Show walked portions
        for i, walked in enumerate(ing['walked']):
            if walked:
                self.display.set_pixel(x + i, y + 2, (50, 50, 50))

    def draw_enemy(self, enemy):
        """Draw an enemy."""
        x, y = int(enemy['x']), int(enemy['y'])

        # Blink when stunned
        if enemy['stunned'] > 0:
            if int(enemy['stunned'] * 8) % 2 == 0:
                return

        if enemy['type'] == 'hotdog':
            self.display.set_pixel(x, y - 2, self.HOTDOG_COLOR)
            self.display.set_pixel(x, y - 1, self.HOTDOG_COLOR)
            self.display.set_pixel(x, y, self.HOTDOG_COLOR)
            self.display.set_pixel(x - 1, y - 1, (200, 150, 100))
            self.display.set_pixel(x + 1, y - 1, (200, 150, 100))
            self.display.set_pixel(x - 1, y - 2, Colors.WHITE)
            self.display.set_pixel(x + 1, y - 2, Colors.WHITE)
        elif enemy['type'] == 'egg':
            self.display.set_pixel(x, y - 2, self.EGG_COLOR)
            self.display.set_pixel(x - 1, y - 1, self.EGG_COLOR)
            self.display.set_pixel(x, y - 1, self.EGG_YOLK)
            self.display.set_pixel(x + 1, y - 1, self.EGG_COLOR)
            self.display.set_pixel(x, y, self.EGG_COLOR)
            self.display.set_pixel(x - 1, y - 2, Colors.BLACK)
            self.display.set_pixel(x + 1, y - 2, Colors.BLACK)
        elif enemy['type'] == 'pickle':
            self.display.set_pixel(x, y - 3, self.PICKLE_COLOR)
            self.display.set_pixel(x, y - 2, self.PICKLE_COLOR)
            self.display.set_pixel(x, y - 1, self.PICKLE_COLOR)
            self.display.set_pixel(x, y, self.PICKLE_COLOR)
            self.display.set_pixel(x - 1, y - 2, (60, 140, 60))
            self.display.set_pixel(x + 1, y - 1, (60, 140, 60))
            self.display.set_pixel(x - 1, y - 3, Colors.WHITE)
            self.display.set_pixel(x + 1, y - 3, Colors.WHITE)

    def draw_chef(self):
        """Draw Peter Pepper the chef."""
        x, y = int(self.chef_x), int(self.chef_y)

        # Hat
        self.display.set_pixel(x - 1, y - 4, self.CHEF_HAT)
        self.display.set_pixel(x, y - 4, self.CHEF_HAT)
        self.display.set_pixel(x + 1, y - 4, self.CHEF_HAT)
        self.display.set_pixel(x, y - 5, self.CHEF_HAT)

        # Head
        self.display.set_pixel(x, y - 3, self.CHEF_SKIN)

        # Body
        self.display.set_pixel(x - 1, y - 2, self.CHEF_BODY)
        self.display.set_pixel(x, y - 2, self.CHEF_BODY)
        self.display.set_pixel(x + 1, y - 2, self.CHEF_BODY)
        self.display.set_pixel(x, y - 1, self.CHEF_BODY)

        # Legs - animated
        if self.walk_frame == 0:
            self.display.set_pixel(x - 1, y, self.CHEF_BODY)
            self.display.set_pixel(x + 1, y, self.CHEF_BODY)
        else:
            self.display.set_pixel(x, y, self.CHEF_BODY)

    def draw_hud(self):
        """Draw HUD — single compact line above floor 0."""
        # Score (left)
        self.display.draw_text_small(2, 1, f"{self.score}", Colors.WHITE)
        # Level + pepper (center-right)
        self.display.draw_text_small(26, 1, f"L{self.level}", Colors.CYAN)
        self.display.draw_text_small(40, 1, f"P{self.peppers}", self.PEPPER_COLOR)
        # Lives (chef icons, far right)
        for i in range(self.lives - 1):
            lx = 55 + i * 5
            self.display.set_pixel(lx, 2, self.CHEF_HAT)
            self.display.set_pixel(lx, 3, self.CHEF_BODY)

    def draw_game_over(self, selection: int = 0):
        """Draw game over screen."""
        self.display.clear(Colors.BLACK)
        self.display.draw_text_small(4, 16, "GAME OVER", Colors.RED)
        self.display.draw_text_small(8, 28, f"SCORE:{self.score}", Colors.WHITE)
        self.display.draw_text_small(12, 38, f"LEVEL:{self.level}", Colors.CYAN)

        if selection == 0:
            self.display.draw_text_small(2, 50, ">RETRY", Colors.YELLOW)
            self.display.draw_text_small(34, 50, " MENU", Colors.GRAY)
        else:
            self.display.draw_text_small(2, 50, " RETRY", Colors.GRAY)
            self.display.draw_text_small(34, 50, ">MENU", Colors.YELLOW)
