"""
Donkey Kong - Classic Arcade Platformer
=======================================
Climb ladders, jump barrels, rescue Pauline!

Controls:
  Arrow Keys - Move (Left/Right), Climb (Up/Down)
  Space      - Jump
"""

import random
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


class DonkeyKong(Game):
    name = "MONKEY KONG"
    description = "Climb & Rescue!"
    category = "arcade"
    GUIDE = {
        'desc': 'Climb platforms, jump over barrels, and beat the bonus timer to the top. Barrels steer down ladders toward you, a fireball prowls the girders, and the hammer smashes both — but you can’t jump or climb while holding it. Even levels are rivet boards: run over all 8 rivets to drop DK.',
    }

    # Colors
    GIRDER_COLOR = (255, 100, 50)      # Orange-red
    LADDER_COLOR = (150, 200, 255)     # Light blue
    MARIO_COLOR = Colors.RED
    MARIO_SKIN = (255, 200, 150)
    DK_COLOR = (139, 90, 43)           # Brown
    DK_LIGHT = (180, 120, 60)
    BARREL_COLOR = (180, 100, 50)      # Brown
    BARREL_DARK = (120, 70, 35)
    PAULINE_COLOR = (255, 150, 200)    # Pink
    PAULINE_HAIR = (139, 69, 19)
    HAMMER_COLOR = Colors.YELLOW
    OIL_COLOR = (50, 50, 200)          # Blue flame

    # Physics constants
    GRAVITY = 100.0
    MAX_FALL_SPEED = 80.0
    MOVE_SPEED = 24.0
    CLIMB_SPEED = 16.0
    BARREL_SPEED = 20.0

    # Explicit jump arc (parabolic, not physics-based)
    JUMP_DURATION = 0.5   # Total airtime in seconds
    JUMP_PEAK = 5         # Max height in pixels at apex

    # Player size
    PLAYER_WIDTH = 3
    PLAYER_HEIGHT = 4

    # Barrel size
    BARREL_SIZE = 3

    # Fireball
    FIREBALL_SPEED = 8.0

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0
        self.lives = 3
        self.level = 1

        # Player state (using pixel coordinates)
        self.player_x = 4.0
        self.player_y = 56.0
        self.velocity_y = 0.0
        self.on_ground = True
        self.on_ladder = False
        self.jumping = False
        self.jump_timer = 0.0
        self.jump_start_y = 0.0
        self.jump_barrels = 0  # Barrels cleared during the current jump
        self.facing = 1  # 1=right, -1=left
        self.has_hammer = False
        self.hammer_timer = 0.0
        self.hammer_swing = 0

        # Animation
        self.walk_frame = 0
        self.walk_timer = 0.0

        # Girders: each is a horizontal platform with optional slope
        # Format: {'x1': start_x, 'x2': end_x, 'y1': y at x1, 'y2': y at x2}
        self.girders = []

        # Ladders: vertical sections
        # Format: {'x': x_pos, 'y1': top, 'y2': bottom, 'broken': bool}
        self.ladders = []

        # Barrels
        self.barrels = []
        self.barrel_spawn_rate = 2.5  # seconds between barrels
        self.barrel_spawn_timer = self.barrel_spawn_rate

        # Hammer powerups: {'x': x, 'y': y, 'active': bool}
        self.hammers = []

        # DK animation
        self.dk_frame = 0
        self.dk_timer = 0.0

        # Oil drum position (barrels burn here)
        self.oil_x = 4
        self.oil_y = 52

        # Pauline position
        self.pauline_x = 28
        self.pauline_y = 4

        # Win animation
        self.win_timer = 0.0

        self.build_level()

    def build_level(self):
        """Build the current board: barrels (odd levels) or rivets (even)."""
        self.girders = []
        self.ladders = []
        self.hammers = []
        self.barrels = []
        self.rivets = []
        self.fireballs = []
        self.first_barrel_this_life = True
        self.fireball_spawn_timer = 6.0
        self.board_type = 'rivets' if self.level % 2 == 0 else 'barrels'

        # Bonus timer: ticks down in 100s; the remainder is the clear bonus
        self.bonus = 4000 + min(self.level, 4) * 1000
        self.bonus_tick = 0.0

        # Level speed increases with difficulty
        speed_mult = 1.0 + (self.level - 1) * 0.15
        self.barrel_spawn_rate = max(1.2, 2.5 - (self.level - 1) * 0.3)

        if self.board_type == 'rivets':
            self.build_rivets_board()
            return

        # Bottom platform (flat, where Mario starts)
        self.girders.append({'x1': 0, 'x2': 64, 'y1': 60, 'y2': 60})

        # Girder design: high side extends to wall, low side ends short.
        # Barrels roll downhill off the short end and land on the next
        # platform whose high side reaches the wall on that same side.

        # Row 1 - slopes down-right (high=left to wall, low=right short)
        self.girders.append({'x1': 0, 'x2': 52, 'y1': 51, 'y2': 54})

        # Row 2 - slopes down-left (high=right to wall, low=left short)
        self.girders.append({'x1': 12, 'x2': 64, 'y1': 44, 'y2': 41})

        # Row 3 - slopes down-right (high=left to wall, low=right short)
        self.girders.append({'x1': 0, 'x2': 52, 'y1': 33, 'y2': 36})

        # Row 4 - slopes down-left (high=right to wall, low=left short)
        self.girders.append({'x1': 12, 'x2': 64, 'y1': 26, 'y2': 23})

        # Row 5 - slopes down-right (high=left to wall, low=right short)
        self.girders.append({'x1': 0, 'x2': 52, 'y1': 15, 'y2': 18})

        # Top platform (DK and Pauline)
        self.girders.append({'x1': 12, 'x2': 40, 'y1': 8, 'y2': 8})

        # Ladders - main ladders near the low (drop-off) end of each
        # platform, broken ladders mid-platform for alternate routes
        # Bottom to Row 1
        self.ladders.append({'x': 50, 'y1': 54, 'y2': 60, 'broken': False})
        self.ladders.append({'x': 20, 'y1': 52, 'y2': 60, 'broken': True})

        # Row 1 to Row 2
        self.ladders.append({'x': 14, 'y1': 44, 'y2': 51, 'broken': False})
        self.ladders.append({'x': 38, 'y1': 43, 'y2': 53, 'broken': True})

        # Row 2 to Row 3
        self.ladders.append({'x': 50, 'y1': 36, 'y2': 42, 'broken': False})
        self.ladders.append({'x': 28, 'y1': 35, 'y2': 43, 'broken': True})

        # Row 3 to Row 4
        self.ladders.append({'x': 14, 'y1': 26, 'y2': 34, 'broken': False})
        self.ladders.append({'x': 38, 'y1': 25, 'y2': 35, 'broken': True})

        # Row 4 to Row 5
        self.ladders.append({'x': 50, 'y1': 18, 'y2': 24, 'broken': False})
        self.ladders.append({'x': 28, 'y1': 16, 'y2': 25, 'broken': True})

        # Row 5 to Top
        self.ladders.append({'x': 16, 'y1': 8, 'y2': 16, 'broken': False})

        # Hammer powerups
        self.hammers.append({'x': 6, 'y': 48, 'active': True})
        self.hammers.append({'x': 46, 'y': 30, 'active': True})

    def build_rivets_board(self):
        """Rivets board: flat girders; clear all 8 rivets to drop DK."""
        # Bottom platform (where Mario starts)
        self.girders.append({'x1': 0, 'x2': 64, 'y1': 60, 'y2': 60})

        # Flat floors
        for y in (51, 42, 33, 24, 15):
            self.girders.append({'x1': 4, 'x2': 60, 'y1': y, 'y2': y})

        # Top platform (DK and Pauline)
        self.girders.append({'x1': 12, 'x2': 40, 'y1': 8, 'y2': 8})

        # Ladders
        for x, y1, y2 in ((20, 51, 60), (50, 51, 60),
                          (14, 42, 51), (44, 42, 51),
                          (20, 33, 42), (50, 33, 42),
                          (14, 24, 33), (44, 24, 33),
                          (28, 15, 24), (50, 15, 24),
                          (16, 8, 15)):
            self.ladders.append({'x': x, 'y1': y1, 'y2': y2, 'broken': False})

        # 8 rivets, two per floor — walk or jump over one to remove it
        for y in (51, 42, 33, 24):
            for x in (26, 38):
                self.rivets.append({'x': x, 'y': y, 'removed': False})

        # Hammer powerups
        self.hammers.append({'x': 6, 'y': 48, 'active': True})
        self.hammers.append({'x': 46, 'y': 30, 'active': True})

    def get_girder_y_at_x(self, girder, x):
        """Get the Y position of a girder at a given X coordinate."""
        if girder['x2'] == girder['x1']:
            return girder['y1']
        progress = (x - girder['x1']) / (girder['x2'] - girder['x1'])
        progress = max(0, min(1, progress))
        return girder['y1'] + progress * (girder['y2'] - girder['y1'])

    def get_platform_at(self, x, y):
        """Find the girder at or just below position (x, y). Returns (girder, surface_y) or (None, None)."""
        for girder in self.girders:
            if girder['x1'] <= x <= girder['x2']:
                surface_y = self.get_girder_y_at_x(girder, x)
                # Player feet should be at or just above surface
                if surface_y - 2 <= y <= surface_y + 4:
                    return girder, surface_y
        return None, None

    def get_ladder_at(self, x, y):
        """Find a ladder at position (x, y). Returns ladder dict or None."""
        for ladder in self.ladders:
            # Check horizontal overlap (ladder is ~2 pixels wide visually)
            if abs(x - ladder['x']) < 3:
                # Check vertical overlap
                if ladder['y1'] <= y <= ladder['y2']:
                    return ladder
        return None

    def can_climb_ladder(self, ladder, going_up):
        """Check if player can climb this ladder in the given direction."""
        if ladder is None:
            return False
        if going_up and ladder.get('broken', False):
            # Broken ladders: can only climb partway up
            halfway = (ladder['y1'] + ladder['y2']) / 2
            return self.player_y > halfway
        return True

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        # Win animation
        if self.win_timer > 0:
            self.win_timer -= dt
            if self.win_timer <= 0:
                self.next_level()
            return

        # Update hammer timer
        if self.has_hammer:
            self.hammer_timer -= dt
            self.hammer_swing = (self.hammer_swing + 1) % 4
            if self.hammer_timer <= 0:
                self.has_hammer = False

        # Bonus timer ticks down; reaching 0 costs a life
        self.bonus_tick += dt
        if self.bonus_tick >= 1.7:
            self.bonus_tick = 0.0
            self.bonus = max(0, self.bonus - 100)
            if self.bonus <= 0:
                self.player_die()
                return

        # Get current state
        girder, surface_y = self.get_platform_at(self.player_x, self.player_y + self.PLAYER_HEIGHT)
        ladder = self.get_ladder_at(self.player_x, self.player_y + self.PLAYER_HEIGHT // 2)

        # Determine if on ground (skip during explicit jump arc)
        if not self.on_ladder and not self.jumping:
            if girder and abs(self.player_y + self.PLAYER_HEIGHT - surface_y) < 3:
                self.on_ground = True
                self.velocity_y = 0
                self.player_y = surface_y - self.PLAYER_HEIGHT
            else:
                self.on_ground = False

        # Handle climbing
        if self.on_ladder:
            # Safety: if we've climbed past the ladder bounds, exit ladder
            if not ladder:
                self.on_ladder = False
                girder_check, sy = self.get_platform_at(self.player_x, self.player_y + self.PLAYER_HEIGHT)
                if girder_check:
                    self.player_y = sy - self.PLAYER_HEIGHT
                    self.on_ground = True
            # On ladder - can move up/down
            elif input_state.up and ladder:
                if self.can_climb_ladder(ladder, going_up=True):
                    self.player_y -= self.CLIMB_SPEED * dt
                    # Check if reached top
                    if self.player_y + self.PLAYER_HEIGHT < ladder['y1'] + 2:
                        self.on_ladder = False
            elif input_state.down and ladder:
                self.player_y += self.CLIMB_SPEED * dt
                # Check if reached bottom
                if self.player_y + self.PLAYER_HEIGHT > ladder['y2']:
                    self.on_ladder = False

            # Can step off ladder horizontally
            if input_state.left or input_state.right:
                if self.on_ground:
                    self.on_ladder = False

        else:
            # Not on ladder - normal movement
            # Horizontal movement (allowed during jump too)
            if input_state.left:
                self.player_x -= self.MOVE_SPEED * dt
                self.facing = -1
                self.walk_timer += dt
            elif input_state.right:
                self.player_x += self.MOVE_SPEED * dt
                self.facing = 1
                self.walk_timer += dt
            else:
                self.walk_timer = 0
                self.walk_frame = 0

            # Walk animation
            if self.walk_timer > 0.15:
                self.walk_timer = 0
                self.walk_frame = (self.walk_frame + 1) % 2

            # Jumping — explicit arc, not physics-based.
            # No jumping while holding the hammer (the original's trade-off).
            if ((input_state.action_l or input_state.action_r) and self.on_ground
                    and not self.jumping and not self.has_hammer):
                self.jumping = True
                self.jump_timer = 0.0
                self.jump_start_y = self.player_y
                self.jump_barrels = 0
                self.on_ground = False

            # Grab ladder (not while jumping or holding the hammer)
            if not self.jumping and not self.has_hammer and (input_state.up or input_state.down) and ladder:
                if input_state.up and self.can_climb_ladder(ladder, going_up=True):
                    self.on_ladder = True
                    self.player_x = ladder['x']  # Snap to ladder
                elif input_state.down:
                    self.on_ladder = True
                    self.player_x = ladder['x']

            # Jump arc or gravity
            if self.jumping:
                self.jump_timer += dt
                if self.jump_timer >= self.JUMP_DURATION:
                    # Jump finished — land on nearest platform
                    self.jumping = False
                    self.player_y = self.jump_start_y
                    g, sy = self.get_platform_at(self.player_x, self.player_y + self.PLAYER_HEIGHT)
                    if g and abs(self.player_y + self.PLAYER_HEIGHT - sy) < 5:
                        self.on_ground = True
                        self.player_y = sy - self.PLAYER_HEIGHT
                    else:
                        self.on_ground = False
                        self.velocity_y = 0
                else:
                    # Parabolic arc: 0 at start, JUMP_PEAK at midpoint, 0 at end
                    p = self.jump_timer / self.JUMP_DURATION
                    offset = self.JUMP_PEAK * 4 * p * (1 - p)
                    self.player_y = self.jump_start_y - offset
            elif not self.on_ground:
                # Gravity only for falling off edges (not jumping)
                self.velocity_y += self.GRAVITY * dt
                self.velocity_y = min(self.velocity_y, self.MAX_FALL_SPEED)
                self.player_y += self.velocity_y * dt

        # Screen boundaries
        self.player_x = max(0, min(GRID_SIZE - self.PLAYER_WIDTH, self.player_x))
        self.player_y = max(0, min(GRID_SIZE - self.PLAYER_HEIGHT, self.player_y))

        # Rivets board: walking or jumping over a rivet removes it
        if self.board_type == 'rivets':
            px = self.player_x + self.PLAYER_WIDTH / 2
            feet = self.player_y + self.PLAYER_HEIGHT
            for rivet in self.rivets:
                if rivet['removed'] or abs(px - rivet['x'] - 1) >= 2:
                    continue
                if abs(feet - rivet['y']) < 3 or (self.jumping and 0 < rivet['y'] - feet <= 9):
                    rivet['removed'] = True
                    self.score += 100

        # Update barrels
        self.update_barrels(dt, input_state)

        # Spawn new barrels (barrels board) or fireballs (rivets board)
        if self.board_type == 'barrels':
            self.barrel_spawn_timer += dt
            if self.barrel_spawn_timer >= self.barrel_spawn_rate:
                self.barrel_spawn_timer = 0
                self.spawn_barrel()
        else:
            self.fireball_spawn_timer += dt
            if self.fireball_spawn_timer >= 8.0 and len(self.fireballs) < 3:
                self.fireball_spawn_timer = 0.0
                self.spawn_fireball()

        # Check barrel collisions
        self.check_barrel_collisions()

        # Update fireballs
        self.update_fireballs(dt)
        self.check_fireball_collisions()

        # Check hammer pickup
        self.check_hammer_pickup()

        # Check win condition (reach Pauline / clear all rivets)
        if self.check_win():
            self.win_timer = 1.5
            self.score += self.bonus  # Remaining bonus timer banked

        # DK animation
        self.dk_timer += dt
        if self.dk_timer > 0.3:
            self.dk_timer = 0
            self.dk_frame = (self.dk_frame + 1) % 2

    def spawn_barrel(self):
        """Spawn a new barrel from DK's position."""
        barrel = {
            'x': 20.0,
            'y': 8.0,
            'velocity_x': 1,  # 1=right, -1=left
            'on_ladder': False,
            'scored': False,
            'girder_idx': 6,  # Start on top platform
        }
        # The first barrel of each life rolls diagonally into the oil drum
        if self.first_barrel_this_life:
            self.first_barrel_this_life = False
            barrel['oil'] = True
        self.barrels.append(barrel)

    def find_girder_at(self, x, y):
        """Find the girder that contains point (x, y) on its surface."""
        for girder in self.girders:
            if girder['x1'] <= x <= girder['x2']:
                surface_y = self.get_girder_y_at_x(girder, x)
                if abs(y - surface_y) < 4:
                    return girder
        return None

    def find_girder_below(self, x, current_y):
        """Find the next girder below the current y position."""
        best_girder = None
        best_y = float('inf')
        for girder in self.girders:
            if girder['x1'] <= x <= girder['x2']:
                surface_y = self.get_girder_y_at_x(girder, x)
                if surface_y > current_y + 2 and surface_y < best_y:
                    best_girder = girder
                    best_y = surface_y
        return best_girder

    def barrel_takes_ladder(self, barrel, input_state):
        """Barrel-steering AI from the original: barrels hunt Mario.

        If Mario is on the girder below and the joystick is held toward the
        barrel's side (or down), the barrel takes the ladder. Otherwise it's
        a flat 25% roll.
        """
        mario_below = barrel['y'] < self.player_y <= barrel['y'] + 14
        if mario_below:
            toward = ((input_state.left and barrel['x'] < self.player_x) or
                      (input_state.right and barrel['x'] > self.player_x) or
                      input_state.down)
            if toward:
                return True
        return random.random() < 0.25

    def update_barrels(self, dt: float, input_state: InputState):
        """Update all barrels."""
        barrels_to_remove = []

        for barrel in self.barrels:
            if barrel.get('oil'):
                # First barrel of a life: DK rolls it left along the top,
                # then it drops down the screen edge into the oil drum and
                # ignites a fireball. Harmless choreography — it must not
                # dive-bomb Mario, who spawns beside the drum.
                if barrel['x'] > self.oil_x + 2:
                    barrel['x'] -= self.BARREL_SPEED * dt * 2.0
                    barrel['y'] += self.BARREL_SPEED * dt * 0.3
                else:
                    barrel['y'] += self.BARREL_SPEED * dt * 2.5
                if barrel['y'] + self.BARREL_SIZE >= self.oil_y:
                    barrels_to_remove.append(barrel)
                    self.spawn_fireball()
                continue

            if barrel.get('falling', False):
                # Barrel is falling between girders
                barrel['y'] += self.BARREL_SPEED * dt * 3
                # Only land on girders BELOW where we started falling
                fall_origin = barrel.get('fall_origin_y', 0)
                target = self.find_girder_below(barrel['x'], fall_origin + self.BARREL_SIZE)
                if target:
                    surface_y = self.get_girder_y_at_x(target, barrel['x'])
                    if barrel['y'] + self.BARREL_SIZE >= surface_y - 2:
                        barrel['y'] = surface_y - self.BARREL_SIZE
                        barrel['falling'] = False
                        # Set direction based on girder slope
                        if target['y2'] > target['y1']:
                            barrel['velocity_x'] = 1  # Roll right (downhill)
                        else:
                            barrel['velocity_x'] = -1  # Roll left (downhill)

            elif barrel['on_ladder']:
                # Barrel is rolling down a ladder
                barrel['y'] += self.BARREL_SPEED * dt * 1.5
                # Check if reached bottom of ladder
                ladder = self.get_ladder_at(barrel['x'], barrel['y'])
                if ladder is None or barrel['y'] >= ladder['y2'] - 2:
                    barrel['on_ladder'] = False
                    # Find next girder below ladder bottom
                    target = self.find_girder_below(barrel['x'], barrel['y'])
                    if target is None:
                        target = self.find_girder_at(barrel['x'], barrel['y'] + 4)
                    if target:
                        surface_y = self.get_girder_y_at_x(target, barrel['x'])
                        barrel['y'] = surface_y - self.BARREL_SIZE
                        # Set direction based on girder slope
                        if target['y2'] > target['y1']:
                            barrel['velocity_x'] = 1
                        else:
                            barrel['velocity_x'] = -1
            else:
                # Rolling along girder
                girder = self.find_girder_at(barrel['x'], barrel['y'] + self.BARREL_SIZE)

                if girder:
                    # Move horizontally
                    barrel['x'] += barrel['velocity_x'] * self.BARREL_SPEED * dt

                    # Update Y to follow slope
                    new_y = self.get_girder_y_at_x(girder, barrel['x'])
                    barrel['y'] = new_y - self.BARREL_SIZE

                    # Check for edge of girder
                    at_left_edge = barrel['x'] <= girder['x1'] + 1
                    at_right_edge = barrel['x'] >= girder['x2'] - 2

                    if at_left_edge or at_right_edge:
                        # Steering AI decides between ladder and rolling off
                        ladder = self.get_ladder_at(barrel['x'], barrel['y'] + self.BARREL_SIZE + 2)
                        if ladder and self.barrel_takes_ladder(barrel, input_state):
                            barrel['on_ladder'] = True
                            barrel['x'] = ladder['x']
                        else:
                            # Drop to next girder — save origin so we
                            # don't re-land on the same platform
                            barrel['falling'] = True
                            barrel['fall_origin_y'] = barrel['y']

                    # Steering AI mid-girder: one roll per ladder crossing
                    if not barrel.get('falling', False):
                        ladder = self.get_ladder_at(barrel['x'], barrel['y'] + self.BARREL_SIZE)
                        if ladder and not barrel['on_ladder']:
                            if barrel.get('ladder_roll_x') != ladder['x']:
                                barrel['ladder_roll_x'] = ladder['x']
                                if self.barrel_takes_ladder(barrel, input_state):
                                    barrel['on_ladder'] = True
                                    barrel['x'] = ladder['x']
                        else:
                            barrel['ladder_roll_x'] = None
                else:
                    # No girder found, start falling
                    barrel['falling'] = True
                    barrel['fall_origin_y'] = barrel['y']

            # Remove barrels that fall off screen
            if barrel['y'] > 62:
                barrels_to_remove.append(barrel)

            # Award points for jumping over barrels — 100/300/500/800
            # cumulative for 1/2/3/4+ barrels cleared in a single jump.
            # Only an actual jump counts, not merely falling.
            if not barrel['scored']:
                if (abs(self.player_x - barrel['x']) < 8 and
                    self.player_y + self.PLAYER_HEIGHT < barrel['y'] and
                    self.jumping):
                    barrel['scored'] = True
                    self.jump_barrels += 1
                    if self.jump_barrels <= 4:
                        self.score += (100, 200, 200, 300)[self.jump_barrels - 1]

        for barrel in barrels_to_remove:
            self.barrels.remove(barrel)

    def check_barrel_collisions(self):
        """Check if player collides with any barrel."""
        player_rect = (
            self.player_x, self.player_y,
            self.PLAYER_WIDTH, self.PLAYER_HEIGHT
        )

        for barrel in self.barrels[:]:  # Copy list to allow removal
            if barrel.get('oil'):
                # The scripted drum-delivery barrel is scenery, not a hazard
                continue
            barrel_rect = (
                barrel['x'], barrel['y'],
                self.BARREL_SIZE, self.BARREL_SIZE
            )

            if self.rect_overlap(player_rect, barrel_rect):
                if self.has_hammer:
                    # Destroy barrel with hammer
                    self.barrels.remove(barrel)
                    self.score += 300
                else:
                    # Player dies
                    self.player_die()
                    return

    def rect_overlap(self, r1, r2):
        """Check if two rectangles overlap. Format: (x, y, w, h)."""
        x1, y1, w1, h1 = r1
        x2, y2, w2, h2 = r2
        return (x1 < x2 + w2 and x1 + w1 > x2 and
                y1 < y2 + h2 and y1 + h1 > y2)

    def check_hammer_pickup(self):
        """Check if player picks up a hammer."""
        if self.has_hammer:
            return

        player_rect = (
            self.player_x, self.player_y,
            self.PLAYER_WIDTH, self.PLAYER_HEIGHT
        )

        for hammer in self.hammers:
            if hammer['active']:
                hammer_rect = (hammer['x'], hammer['y'], 4, 3)
                if self.rect_overlap(player_rect, hammer_rect):
                    hammer['active'] = False
                    self.has_hammer = True
                    self.hammer_timer = 6.0  # 6 seconds of hammer power
                    self.score += 50

    def spawn_fireball(self):
        """Spawn a fireball out of the oil drum."""
        self.fireballs.append({
            'x': float(self.oil_x + 2),
            'y': 58.0,  # Standing on the bottom girder
            'dir': 1,
            'on_ladder': False,
            'climb_dir': -1,
            'ladder': None,
            'decide_timer': random.uniform(1.0, 2.5),
            'flicker': 0.0,
            # Harmless while igniting — the drum sits beside Mario's spawn,
            # so an instantly-lethal fireball would spawn-kill an idle player
            'ignite': 1.5,
        })

    def update_fireballs(self, dt: float):
        """Fireballs random-walk girders and climb ladders."""
        for fb in self.fireballs:
            fb['flicker'] += dt
            if fb.get('ignite', 0) > 0:
                fb['ignite'] -= dt

            if fb['on_ladder']:
                fb['y'] += fb['climb_dir'] * self.FIREBALL_SPEED * dt
                ladder = fb['ladder']
                done = (fb['y'] + 2 <= ladder['y1'] if fb['climb_dir'] < 0
                        else fb['y'] + 2 >= ladder['y2'])
                if done:
                    fb['on_ladder'] = False
                    end_y = ladder['y1'] if fb['climb_dir'] < 0 else ladder['y2']
                    girder = self.find_girder_at(fb['x'], end_y)
                    if girder:
                        fb['y'] = self.get_girder_y_at_x(girder, fb['x']) - 2
                continue

            girder = self.find_girder_at(fb['x'], fb['y'] + 2)
            if girder is None:
                # Settle onto the nearest girder below
                below = self.find_girder_below(fb['x'], fb['y'])
                if below:
                    fb['y'] = self.get_girder_y_at_x(below, fb['x']) - 2
                continue

            fb['x'] += fb['dir'] * self.FIREBALL_SPEED * dt
            fb['x'] = max(1.0, min(float(GRID_SIZE - 3), fb['x']))
            fb['y'] = self.get_girder_y_at_x(girder, fb['x']) - 2

            # Reverse at girder edges
            if fb['x'] <= girder['x1'] + 1 or fb['x'] >= girder['x2'] - 2:
                fb['dir'] *= -1

            # Occasionally take a ladder or wander the other way
            fb['decide_timer'] -= dt
            if fb['decide_timer'] <= 0:
                fb['decide_timer'] = random.uniform(1.0, 2.5)
                ladder = self.get_ladder_at(fb['x'], fb['y'] + 2)
                if ladder and random.random() < 0.5:
                    fb['on_ladder'] = True
                    fb['ladder'] = ladder
                    fb['x'] = float(ladder['x'])
                    fb['climb_dir'] = -1 if ladder['y1'] < fb['y'] - 1 else 1
                elif random.random() < 0.4:
                    fb['dir'] *= -1

    def check_fireball_collisions(self):
        """Fireballs kill on touch; the hammer kills them for 500."""
        player_rect = (
            self.player_x, self.player_y,
            self.PLAYER_WIDTH, self.PLAYER_HEIGHT
        )
        for fb in self.fireballs[:]:
            if fb.get('ignite', 0) > 0 and not self.has_hammer:
                continue  # still igniting — harmless (but hammerable)
            if self.rect_overlap(player_rect, (fb['x'], fb['y'], 2, 2)):
                if self.has_hammer:
                    self.fireballs.remove(fb)
                    self.score += 500
                else:
                    self.player_die()
                    return

    def check_win(self):
        """Rivets board: all rivets cleared. Barrels board: reach Pauline."""
        if self.board_type == 'rivets':
            return all(r['removed'] for r in self.rivets)
        return (abs(self.player_x - self.pauline_x) < 6 and
                abs(self.player_y - self.pauline_y) < 6)

    def player_die(self):
        """Handle player death."""
        self.lives -= 1
        if self.lives <= 0:
            self.state = GameState.GAME_OVER
        else:
            # Reset position but keep level
            self.player_x = 4.0
            self.player_y = 56.0
            self.velocity_y = 0.0
            self.on_ground = True
            self.on_ladder = False
            self.jumping = False
            self.has_hammer = False
            self.barrels.clear()
            self.fireballs.clear()
            self.first_barrel_this_life = True
            self.fireball_spawn_timer = 6.0
            self.barrel_spawn_timer = self.barrel_spawn_rate
            # Bonus timer restarts each life
            self.bonus = 4000 + min(self.level, 4) * 1000
            self.bonus_tick = 0.0
            # Restore hammers
            for hammer in self.hammers:
                hammer['active'] = True

    def next_level(self):
        """Advance to next level."""
        self.level += 1
        self.score += 500 * self.level
        self.player_x = 4.0
        self.player_y = 56.0
        self.velocity_y = 0.0
        self.on_ground = True
        self.on_ladder = False
        self.jumping = False
        self.has_hammer = False
        self.barrels.clear()
        self.barrel_spawn_timer = self.barrel_spawn_rate
        self.build_level()

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Draw girders
        for girder in self.girders:
            self.draw_girder(girder)

        # Draw rivets
        for rivet in self.rivets:
            if not rivet['removed']:
                self.display.set_pixel(rivet['x'], rivet['y'] - 1, Colors.YELLOW)
                self.display.set_pixel(rivet['x'] + 1, rivet['y'] - 1, Colors.YELLOW)

        # Draw ladders
        for ladder in self.ladders:
            self.draw_ladder(ladder)

        # Draw oil drum
        self.draw_oil_drum()

        # Draw hammers
        for hammer in self.hammers:
            if hammer['active']:
                self.draw_hammer_pickup(hammer['x'], hammer['y'])

        # Draw Donkey Kong
        self.draw_dk()

        # Draw Pauline
        self.draw_pauline()

        # Draw barrels
        for barrel in self.barrels:
            self.draw_barrel(barrel)

        # Draw fireballs
        for fb in self.fireballs:
            self.draw_fireball(fb)

        # Draw player (Mario)
        self.draw_player()

        # Draw HUD
        self.draw_hud()

    def draw_girder(self, girder):
        """Draw a girder platform."""
        x1, x2 = int(girder['x1']), int(girder['x2'])
        for x in range(x1, x2):
            y = int(self.get_girder_y_at_x(girder, x))
            # Two-pixel thick girder with highlight
            self.display.set_pixel(x, y, self.GIRDER_COLOR)
            self.display.set_pixel(x, y + 1, (200, 80, 40))

    def draw_ladder(self, ladder):
        """Draw a ladder."""
        x = int(ladder['x'])
        y1, y2 = int(ladder['y1']), int(ladder['y2'])

        color = self.LADDER_COLOR
        if ladder.get('broken', False):
            color = (100, 140, 180)  # Dimmer for broken

        # Vertical rails
        for y in range(y1, y2 + 1):
            self.display.set_pixel(x - 1, y, color)
            self.display.set_pixel(x + 1, y, color)

        # Rungs every 3 pixels
        for y in range(y1 + 1, y2, 3):
            self.display.set_pixel(x, y, color)

        # Mark broken ladders
        if ladder.get('broken', False):
            halfway = (y1 + y2) // 2
            self.display.set_pixel(x - 1, halfway, Colors.BLACK)
            self.display.set_pixel(x, halfway, Colors.BLACK)
            self.display.set_pixel(x + 1, halfway, Colors.BLACK)

    def draw_oil_drum(self):
        """Draw the oil drum at the bottom."""
        x, y = self.oil_x, self.oil_y
        # Drum body
        for dy in range(6):
            for dx in range(5):
                self.display.set_pixel(x + dx, y + dy, (80, 80, 100))
        # Fire
        fire_color = Colors.ORANGE if (self.dk_timer * 10) % 2 < 1 else Colors.YELLOW
        self.display.set_pixel(x + 2, y - 1, fire_color)
        self.display.set_pixel(x + 1, y - 2, Colors.RED)
        self.display.set_pixel(x + 3, y - 2, Colors.RED)

    def draw_dk(self):
        """Draw Donkey Kong at top."""
        # DK position
        x, y = 14, 1

        # Body (8x7 rough shape)
        for dy in range(7):
            for dx in range(7):
                if dy < 2 or dy > 5 or dx < 1 or dx > 5:
                    continue
                self.display.set_pixel(x + dx, y + dy, self.DK_COLOR)

        # Head
        self.display.set_pixel(x + 2, y + 1, self.DK_LIGHT)
        self.display.set_pixel(x + 3, y + 1, self.DK_LIGHT)
        self.display.set_pixel(x + 4, y + 1, self.DK_LIGHT)
        self.display.set_pixel(x + 2, y + 2, self.DK_LIGHT)
        self.display.set_pixel(x + 4, y + 2, self.DK_LIGHT)

        # Eyes
        self.display.set_pixel(x + 2, y + 2, Colors.WHITE)
        self.display.set_pixel(x + 4, y + 2, Colors.WHITE)

        # Arms - animated when throwing
        if self.dk_frame == 0:
            self.display.set_pixel(x + 1, y + 3, self.DK_COLOR)
            self.display.set_pixel(x + 6, y + 3, self.DK_COLOR)
        else:
            self.display.set_pixel(x + 0, y + 2, self.DK_COLOR)
            self.display.set_pixel(x + 7, y + 4, self.DK_COLOR)

        # Barrel pile
        self.display.set_pixel(x - 2, y + 5, self.BARREL_COLOR)
        self.display.set_pixel(x - 1, y + 5, self.BARREL_COLOR)
        self.display.set_pixel(x - 2, y + 6, self.BARREL_COLOR)
        self.display.set_pixel(x - 1, y + 6, self.BARREL_COLOR)

    def draw_pauline(self):
        """Draw Pauline at top."""
        x, y = int(self.pauline_x), int(self.pauline_y)

        # Dress (pink)
        self.display.set_pixel(x, y + 1, self.PAULINE_COLOR)
        self.display.set_pixel(x + 1, y + 1, self.PAULINE_COLOR)
        self.display.set_pixel(x, y + 2, self.PAULINE_COLOR)
        self.display.set_pixel(x + 1, y + 2, self.PAULINE_COLOR)
        self.display.set_pixel(x, y + 3, self.PAULINE_COLOR)
        self.display.set_pixel(x + 1, y + 3, self.PAULINE_COLOR)

        # Head/hair
        self.display.set_pixel(x, y, self.PAULINE_HAIR)
        self.display.set_pixel(x + 1, y, self.PAULINE_HAIR)

        # "HELP" text above (small)
        if int(self.dk_timer * 4) % 2 == 0:
            self.display.set_pixel(x, y - 2, Colors.WHITE)
            self.display.set_pixel(x + 1, y - 2, Colors.WHITE)

    def draw_barrel(self, barrel):
        """Draw a barrel."""
        x, y = int(barrel['x']), int(barrel['y'])

        # 3x3 barrel
        for dy in range(3):
            for dx in range(3):
                if dx == 1 and dy == 1:
                    # Center darker
                    self.display.set_pixel(x + dx, y + dy, self.BARREL_DARK)
                else:
                    self.display.set_pixel(x + dx, y + dy, self.BARREL_COLOR)

    def draw_fireball(self, fb):
        """Draw a 2x2 flickering fireball."""
        x, y = int(fb['x']), int(fb['y'])
        hot = int(fb['flicker'] * 12) % 2 == 0
        if fb.get('ignite', 0) > 0:
            # Igniting: dim ember, only the top pixels sputter
            c = Colors.RED if hot else (100, 40, 0)
            self.display.set_pixel(x, y + 1, c)
            self.display.set_pixel(x + 1, y + 1, c)
            if hot:
                self.display.set_pixel(x, y, (100, 40, 0))
            return
        c1 = Colors.ORANGE if hot else Colors.YELLOW
        c2 = Colors.RED if hot else Colors.ORANGE
        self.display.set_pixel(x, y, c1)
        self.display.set_pixel(x + 1, y, c2)
        self.display.set_pixel(x, y + 1, c2)
        self.display.set_pixel(x + 1, y + 1, c1)

    def draw_player(self):
        """Draw Mario."""
        x, y = int(self.player_x), int(self.player_y)

        if self.has_hammer:
            self.draw_player_with_hammer(x, y)
            return

        if self.on_ladder:
            # Climbing pose
            self.display.set_pixel(x + 1, y, self.MARIO_COLOR)  # Head
            self.display.set_pixel(x, y + 1, self.MARIO_SKIN)   # Arm
            self.display.set_pixel(x + 1, y + 1, self.MARIO_COLOR)  # Body
            self.display.set_pixel(x + 2, y + 1, self.MARIO_SKIN)   # Arm
            self.display.set_pixel(x + 1, y + 2, Colors.BLUE)   # Legs
            self.display.set_pixel(x + 1, y + 3, Colors.BLUE)
        else:
            # Normal pose
            # Head (red cap)
            self.display.set_pixel(x + 1, y, self.MARIO_COLOR)

            # Face
            self.display.set_pixel(x + 1, y + 1, self.MARIO_SKIN)

            # Body (red)
            self.display.set_pixel(x, y + 2, self.MARIO_COLOR)
            self.display.set_pixel(x + 1, y + 2, self.MARIO_COLOR)
            self.display.set_pixel(x + 2, y + 2, self.MARIO_COLOR)

            # Legs (blue) - animated
            if self.walk_frame == 0 or not self.on_ground:
                self.display.set_pixel(x, y + 3, Colors.BLUE)
                self.display.set_pixel(x + 2, y + 3, Colors.BLUE)
            else:
                self.display.set_pixel(x + 1, y + 3, Colors.BLUE)

    def draw_player_with_hammer(self, x, y):
        """Draw Mario swinging hammer."""
        # Body
        self.display.set_pixel(x + 1, y, self.MARIO_COLOR)
        self.display.set_pixel(x + 1, y + 1, self.MARIO_SKIN)
        self.display.set_pixel(x + 1, y + 2, self.MARIO_COLOR)
        self.display.set_pixel(x, y + 3, Colors.BLUE)
        self.display.set_pixel(x + 2, y + 3, Colors.BLUE)

        # Hammer positions based on swing frame
        hx, hy = x, y
        if self.hammer_swing == 0:
            hx, hy = x + 3 * self.facing, y - 1
        elif self.hammer_swing == 1:
            hx, hy = x + 3 * self.facing, y
        elif self.hammer_swing == 2:
            hx, hy = x + 3 * self.facing, y + 1
        else:
            hx, hy = x + 2 * self.facing, y - 2

        # Draw hammer
        self.display.set_pixel(hx, hy, self.HAMMER_COLOR)
        self.display.set_pixel(hx + 1, hy, self.HAMMER_COLOR)
        self.display.set_pixel(hx, hy + 1, (139, 90, 43))  # Handle

    def draw_hammer_pickup(self, x, y):
        """Draw a hammer powerup."""
        # Hammer head
        self.display.set_pixel(x, y, self.HAMMER_COLOR)
        self.display.set_pixel(x + 1, y, self.HAMMER_COLOR)
        self.display.set_pixel(x + 2, y, self.HAMMER_COLOR)
        # Handle
        self.display.set_pixel(x + 1, y + 1, (139, 90, 43))
        self.display.set_pixel(x + 1, y + 2, (139, 90, 43))

    def draw_hud(self):
        """Draw the heads-up display."""
        # Score
        self.display.draw_text_small(1, 1, f"{self.score}", Colors.WHITE)

        # Bonus timer (top-right, replaces the level display)
        self.display.draw_text_small(40, 1, f"{self.bonus}", Colors.CYAN)

        # Lives (as small Mario icons)
        for i in range(self.lives - 1):
            lx = 34 - i * 4
            self.display.set_pixel(lx, 2, self.MARIO_COLOR)
            self.display.set_pixel(lx, 3, Colors.BLUE)

        # Hammer timer
        if self.has_hammer:
            bar_width = int(self.hammer_timer / 6.0 * 10)
            for i in range(bar_width):
                self.display.set_pixel(52 + i, 6, self.HAMMER_COLOR)

    def draw_game_over(self):
        """Draw game over screen."""
        self.display.clear(Colors.BLACK)
        self.display.draw_text_small(8, 20, "GAME OVER", Colors.RED)
        self.display.draw_text_small(8, 32, f"SCORE:{self.score}", Colors.WHITE)
        self.display.draw_text_small(12, 42, f"LEVEL:{self.level}", Colors.CYAN)
        self.display.draw_text_small(4, 54, "BTN:RETRY", Colors.GRAY)
