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
    ENEMY_SPEED = 18.0
    INGREDIENT_FALL_SPEED = 80.0

    # Layout constants
    PLATFORM_Y = [56, 44, 32, 20]  # Y positions of platforms (bottom to top)
    PLATE_Y = 60  # Where completed burgers land

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
        self.chef_y = float(self.PLATFORM_Y[0])
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
        """Build platforms, ladders, ingredients, and enemies."""
        self.platforms = []
        self.ladders = []
        self.ingredients = []
        self.enemies = []
        self.plates = []

        # Create 4 burger columns
        burger_x_positions = [6, 22, 38, 54]

        # Platforms - full width rows
        for y in self.PLATFORM_Y:
            self.platforms.append({'x1': 0, 'x2': 64, 'y': y})

        # Ladders connecting platforms
        ladder_x_positions = [2, 14, 30, 46, 60]
        for lx in ladder_x_positions:
            for i in range(len(self.PLATFORM_Y) - 1):
                self.ladders.append({
                    'x': lx,
                    'y1': self.PLATFORM_Y[i+1],
                    'y2': self.PLATFORM_Y[i]
                })

        # Ingredients for each burger column
        ingredient_types = ['bun_top', 'lettuce', 'meat', 'tomato', 'bun_bottom']

        for bx in burger_x_positions:
            # Place one ingredient per platform level (except bottom which is plate)
            for i, ing_type in enumerate(ingredient_types[:4]):
                platform_idx = 3 - i  # Top platform first
                if platform_idx >= 0:
                    self.ingredients.append({
                        'type': ing_type,
                        'x': bx - 4,  # Center ingredient on column
                        'y': self.PLATFORM_Y[platform_idx] - 2,
                        'width': 8,
                        'walked': [False] * 8,  # Track which pixels chef walked over
                        'falling': False,
                        'fall_speed': 0,
                        'target_y': None,
                        'carrying_enemies': []
                    })

            # Bottom bun starts lower
            self.ingredients.append({
                'type': 'bun_bottom',
                'x': bx - 4,
                'y': self.PLATFORM_Y[0] - 2,
                'width': 8,
                'walked': [False] * 8,
                'falling': False,
                'fall_speed': 0,
                'target_y': None,
                'carrying_enemies': []
            })

            # Plate at bottom
            self.plates.append({'x': bx - 4, 'y': self.PLATE_Y})

        # Spawn enemies based on level
        num_enemies = min(2 + self.level, 5)
        enemy_types = ['hotdog', 'egg', 'pickle']

        for i in range(num_enemies):
            enemy_type = enemy_types[i % len(enemy_types)]
            # Start enemies on upper platforms
            platform_idx = random.randint(1, 3)
            self.enemies.append({
                'type': enemy_type,
                'x': random.randint(10, 54),
                'y': float(self.PLATFORM_Y[platform_idx]),
                'on_ladder': False,
                'stunned': 0.0,
                'direction': random.choice([-1, 1])
            })

    def get_platform_at(self, x, y):
        """Check if there's a platform at this position."""
        for platform in self.platforms:
            if platform['x1'] <= x <= platform['x2']:
                if abs(y - platform['y']) < 3:
                    return platform
        return None

    def get_ladder_at(self, x, y, prefer_up=False, prefer_down=False):
        """Check if there's a ladder at this position.

        When at a boundary between two ladders, prefer_up/prefer_down
        helps select the right one for the direction we want to go.
        """
        candidates = []
        for ladder in self.ladders:
            if abs(x - ladder['x']) < 3:
                if ladder['y1'] <= y <= ladder['y2']:
                    candidates.append(ladder)

        if not candidates:
            return None

        if len(candidates) == 1:
            return candidates[0]

        # Multiple ladders at this position (boundary case)
        if prefer_up:
            # Want the ladder where we can climb up (y1 < current y)
            for ladder in candidates:
                if ladder['y1'] < y:
                    return ladder
        elif prefer_down:
            # Want the ladder where we can climb down (y2 > current y)
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
        """Update chef movement."""
        moved = False

        # When checking for ladder, prefer direction player wants to go
        ladder = self.get_ladder_at(self.chef_x, self.chef_y,
                                     prefer_up=input_state.up,
                                     prefer_down=input_state.down)
        platform = self.get_platform_at(self.chef_x, self.chef_y)

        if self.on_ladder:
            # Climbing movement
            if input_state.up:
                self.chef_y -= self.CLIMB_SPEED * dt
                moved = True
                # Check if reached top of ladder
                if ladder and self.chef_y < ladder['y1']:
                    self.chef_y = ladder['y1']
                    self.on_ladder = False
            elif input_state.down:
                self.chef_y += self.CLIMB_SPEED * dt
                moved = True
                # Check if reached bottom of ladder
                if ladder and self.chef_y > ladder['y2']:
                    self.chef_y = ladder['y2']
                    self.on_ladder = False

            # Step off ladder horizontally
            if input_state.left or input_state.right:
                if platform:
                    self.on_ladder = False
        else:
            # Platform movement
            if input_state.left:
                self.chef_x -= self.MOVE_SPEED * dt
                self.facing = -1
                moved = True
            elif input_state.right:
                self.chef_x += self.MOVE_SPEED * dt
                self.facing = 1
                moved = True

            # Grab ladder
            if (input_state.up or input_state.down) and ladder:
                self.on_ladder = True
                self.chef_x = ladder['x']

        # Throw pepper
        if input_state.action_l and self.peppers > 0 and not self.pepper_active:
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

        # Bounds
        self.chef_x = max(2, min(60, self.chef_x))

        # Walk animation
        if moved:
            self.walk_timer += dt
            if self.walk_timer > 0.12:
                self.walk_timer = 0
                self.walk_frame = (self.walk_frame + 1) % 2

    def check_ingredient_walk(self):
        """Check if chef is walking over any ingredients."""
        chef_left = int(self.chef_x) - 1
        chef_right = int(self.chef_x) + 1

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
                    self.score += 50
                    self.drop_ingredient(ing)

    def drop_ingredient(self, ingredient):
        """Start dropping an ingredient."""
        ingredient['falling'] = True
        ingredient['fall_speed'] = self.INGREDIENT_FALL_SPEED
        ingredient['walked'] = [False] * ingredient['width']

        # Find target Y (next platform or plate)
        current_y = ingredient['y']
        target_y = self.PLATE_Y - 2  # Default to plate

        for platform in self.platforms:
            if platform['y'] > current_y + 4:
                # Check if there's an ingredient at this level
                for other in self.ingredients:
                    if other != ingredient and not other['falling']:
                        if abs(other['x'] - ingredient['x']) < 4:
                            if abs(other['y'] - (platform['y'] - 2)) < 4:
                                target_y = other['y'] - 3
                                break
                else:
                    target_y = platform['y'] - 2
                break

        ingredient['target_y'] = target_y

        # Check for enemies on this ingredient
        for enemy in self.enemies:
            if not enemy['stunned']:
                if (ingredient['x'] <= enemy['x'] <= ingredient['x'] + ingredient['width'] and
                    abs(enemy['y'] - ingredient['y']) < 5):
                    ingredient['carrying_enemies'].append(enemy)
                    enemy['stunned'] = 5.0
                    self.score += 100

    def update_ingredients(self, dt: float):
        """Update falling ingredients."""
        for ing in self.ingredients:
            if ing['falling']:
                ing['y'] += ing['fall_speed'] * dt

                # Move carried enemies
                for enemy in ing['carrying_enemies']:
                    enemy['y'] = ing['y']

                # Check if reached target
                if ing['y'] >= ing['target_y']:
                    ing['y'] = ing['target_y']
                    ing['falling'] = False
                    ing['carrying_enemies'] = []

                    # Check if this pushes down ingredients below
                    for other in self.ingredients:
                        if other != ing and not other['falling']:
                            if abs(other['x'] - ing['x']) < 4:
                                if abs(other['y'] - ing['y']) < 4:
                                    self.drop_ingredient(other)

    def update_enemies(self, dt: float):
        """Update enemy AI."""
        for enemy in self.enemies:
            if enemy['stunned'] > 0:
                enemy['stunned'] -= dt
                continue

            # Simple AI: move toward chef
            dx = self.chef_x - enemy['x']
            dy = self.chef_y - enemy['y']

            ladder = self.get_ladder_at(enemy['x'], enemy['y'])
            platform = self.get_platform_at(enemy['x'], enemy['y'])

            speed = self.ENEMY_SPEED * (1 + self.level * 0.1)

            if enemy['on_ladder']:
                # Climbing
                if abs(dy) > 2:
                    if dy < 0:
                        enemy['y'] -= speed * dt
                        if ladder and enemy['y'] < ladder['y1']:
                            enemy['y'] = ladder['y1']
                            enemy['on_ladder'] = False
                    else:
                        enemy['y'] += speed * dt
                        if ladder and enemy['y'] > ladder['y2']:
                            enemy['y'] = ladder['y2']
                            enemy['on_ladder'] = False
                else:
                    enemy['on_ladder'] = False
            else:
                # Horizontal movement
                if abs(dx) > 3:
                    if dx < 0:
                        enemy['x'] -= speed * dt
                        enemy['direction'] = -1
                    else:
                        enemy['x'] += speed * dt
                        enemy['direction'] = 1

                # Try to use ladder
                if ladder and abs(dy) > 8:
                    if random.random() < 0.02:
                        enemy['on_ladder'] = True
                        enemy['x'] = ladder['x']

            # Bounds
            enemy['x'] = max(2, min(60, enemy['x']))

    def check_enemy_collision(self):
        """Check if chef collides with any enemy."""
        for enemy in self.enemies:
            if enemy['stunned'] > 0:
                continue

            if (abs(enemy['x'] - self.chef_x) < 4 and
                abs(enemy['y'] - self.chef_y) < 4):
                self.die()
                return

    def die(self):
        """Chef loses a life."""
        self.lives -= 1
        if self.lives <= 0:
            self.state = GameState.GAME_OVER
        else:
            # Reset positions
            self.chef_x = 30.0
            self.chef_y = float(self.PLATFORM_Y[0])
            self.on_ladder = False

            # Reset enemies
            for i, enemy in enumerate(self.enemies):
                platform_idx = random.randint(1, 3)
                enemy['x'] = random.randint(10, 54)
                enemy['y'] = float(self.PLATFORM_Y[platform_idx])
                enemy['stunned'] = 2.0  # Brief grace period

    def check_win(self):
        """Check if all burgers are complete."""
        # All ingredients should be at plate level
        for ing in self.ingredients:
            if ing['y'] < self.PLATE_Y - 15:
                return False
        return True

    def next_level(self):
        """Advance to next level."""
        self.level += 1
        self.peppers = min(self.peppers + 2, 9)
        self.chef_x = 30.0
        self.chef_y = float(self.PLATFORM_Y[0])
        self.on_ladder = False
        self.build_level()

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Draw plates
        for plate in self.plates:
            self.display.draw_rect(plate['x'], plate['y'], 8, 2, Colors.GRAY)

        # Draw platforms
        for platform in self.platforms:
            for x in range(platform['x1'], platform['x2']):
                self.display.set_pixel(x, platform['y'], self.PLATFORM_COLOR)
                self.display.set_pixel(x, platform['y'] + 1, (80, 60, 40))

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
            # Hot dog body
            self.display.set_pixel(x, y - 2, self.HOTDOG_COLOR)
            self.display.set_pixel(x, y - 1, self.HOTDOG_COLOR)
            self.display.set_pixel(x, y, self.HOTDOG_COLOR)
            self.display.set_pixel(x - 1, y - 1, (200, 150, 100))  # Bun
            self.display.set_pixel(x + 1, y - 1, (200, 150, 100))
            # Eyes
            self.display.set_pixel(x - 1, y - 2, Colors.WHITE)
            self.display.set_pixel(x + 1, y - 2, Colors.WHITE)
        elif enemy['type'] == 'egg':
            # Egg body
            self.display.set_pixel(x, y - 2, self.EGG_COLOR)
            self.display.set_pixel(x - 1, y - 1, self.EGG_COLOR)
            self.display.set_pixel(x, y - 1, self.EGG_YOLK)
            self.display.set_pixel(x + 1, y - 1, self.EGG_COLOR)
            self.display.set_pixel(x, y, self.EGG_COLOR)
            # Eyes
            self.display.set_pixel(x - 1, y - 2, Colors.BLACK)
            self.display.set_pixel(x + 1, y - 2, Colors.BLACK)
        elif enemy['type'] == 'pickle':
            # Pickle body
            self.display.set_pixel(x, y - 3, self.PICKLE_COLOR)
            self.display.set_pixel(x, y - 2, self.PICKLE_COLOR)
            self.display.set_pixel(x, y - 1, self.PICKLE_COLOR)
            self.display.set_pixel(x, y, self.PICKLE_COLOR)
            # Bumps
            self.display.set_pixel(x - 1, y - 2, (60, 140, 60))
            self.display.set_pixel(x + 1, y - 1, (60, 140, 60))
            # Eyes
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
        """Draw the heads-up display."""
        # Score at top left
        self.display.draw_text_small(1, 1, f"{self.score}", Colors.WHITE)

        # Level
        self.display.draw_text_small(30, 1, f"L{self.level}", Colors.CYAN)

        # Lives (chef icons)
        for i in range(self.lives - 1):
            lx = 50 + i * 5
            self.display.set_pixel(lx, 2, self.CHEF_HAT)
            self.display.set_pixel(lx, 3, self.CHEF_BODY)

        # Pepper count
        self.display.draw_text_small(1, 8, f"P{self.peppers}", self.PEPPER_COLOR)

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
