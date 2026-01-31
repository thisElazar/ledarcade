"""
D&D - Dungeon Crawler (Inspired by AD&D: Cloudy Mountain, 1982)
===============================================================
Explore procedural dungeons shrouded in darkness!
Find the exit ladder, guarded by a boss monster.

Controls:
  Arrow Keys - Move through dungeon
  Space      - Shoot arrow in facing direction
"""

import random
import math
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


class DnD(Game):
    name = "D&D"
    description = "Dungeon Crawler!"
    category = "retro"

    # Display layout
    HUD_HEIGHT = 8
    VIEW_WIDTH = 64
    VIEW_HEIGHT = 56  # 64 - HUD

    # Dungeon size (larger than viewport for scrolling)
    DUNGEON_WIDTH = 160
    DUNGEON_HEIGHT = 120

    # Colors
    WALL_COLOR = (60, 55, 70)
    WALL_HIGHLIGHT = (80, 75, 90)
    FLOOR_COLOR = (35, 30, 25)
    FOG_COLOR = (0, 0, 0)
    REVEALED_TINT = (20, 18, 15)  # Slightly visible explored areas

    PLAYER_COLOR = Colors.CYAN
    PLAYER_DARK = (0, 180, 180)
    ARROW_COLOR = Colors.YELLOW

    # Monster colors
    RAT_COLOR = (120, 100, 80)
    SPIDER_COLOR = (40, 40, 50)
    SPIDER_EYE = Colors.RED
    BLOB_COLOR = (100, 200, 100)  # Green, invincible!
    SNAKE_COLOR = (200, 50, 50)
    SNAKE_PATTERN = (150, 40, 40)
    DRAGON_COLOR = (200, 150, 50)
    DRAGON_WING = (180, 130, 40)

    # Item colors
    QUIVER_COLOR = Colors.YELLOW
    HEALTH_COLOR = Colors.RED
    EXIT_COLOR = Colors.MAGENTA

    # Game constants
    MOVE_SPEED = 40.0
    ARROW_SPEED = 120.0
    REVEAL_RADIUS = 12  # How far player can see

    # Tile types
    TILE_WALL = 1
    TILE_FLOOR = 0

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0
        self.level = 1
        self.health = 3
        self.max_health = 3
        self.arrows = 10

        # Player position (in dungeon coordinates)
        self.player_x = 20.0
        self.player_y = 20.0
        self.facing_x = 1
        self.facing_y = 0
        self.move_cooldown = 0.0

        # Camera position (top-left of viewport in dungeon coords)
        self.camera_x = 0.0
        self.camera_y = 0.0

        # Arrows in flight
        self.active_arrows = []

        # Animation
        self.anim_timer = 0.0
        self.hurt_timer = 0.0
        self.walk_frame = 0

        # Generate dungeon
        self.generate_dungeon()

    def generate_dungeon(self):
        """Generate a room-based dungeon with corridors."""
        # Initialize all walls
        self.dungeon = [[self.TILE_WALL for _ in range(self.DUNGEON_WIDTH)]
                        for _ in range(self.DUNGEON_HEIGHT)]

        # Fog of war - False = not revealed, True = revealed
        self.revealed = [[False for _ in range(self.DUNGEON_WIDTH)]
                         for _ in range(self.DUNGEON_HEIGHT)]

        self.monsters = []
        self.items = []
        self.rooms = []

        # Generate rooms
        num_rooms = 5 + self.level
        attempts = 0
        while len(self.rooms) < num_rooms and attempts < 100:
            self.try_place_room()
            attempts += 1

        # Connect rooms with corridors
        self.connect_rooms()

        # Place player in first room
        if self.rooms:
            first_room = self.rooms[0]
            self.player_x = float(first_room['cx'])
            self.player_y = float(first_room['cy'])

        # Place exit in last room (guarded by boss)
        if len(self.rooms) >= 2:
            last_room = self.rooms[-1]
            self.exit_x = last_room['cx']
            self.exit_y = last_room['cy']

            # Place boss at exit
            boss_type = 'snake' if self.level < 3 else 'dragon'
            self.monsters.append({
                'type': boss_type,
                'x': float(self.exit_x + 2),
                'y': float(self.exit_y),
                'hp': 2 if boss_type == 'snake' else 3,
                'is_boss': True,
                'move_timer': 0.0,
                'direction': (-1, 0)
            })
        else:
            self.exit_x = 40
            self.exit_y = 40

        # Place monsters in rooms (skip first and last)
        self.place_monsters()

        # Place items
        self.place_items()

        # Initial reveal around player
        self.update_fog_of_war()

    def try_place_room(self):
        """Try to place a room in the dungeon."""
        room_w = random.randint(12, 24)
        room_h = random.randint(10, 18)
        room_x = random.randint(4, self.DUNGEON_WIDTH - room_w - 4)
        room_y = random.randint(4, self.DUNGEON_HEIGHT - room_h - 4)

        # Check for overlap with existing rooms (with margin)
        margin = 3
        for room in self.rooms:
            if (room_x - margin < room['x'] + room['w'] + margin and
                room_x + room_w + margin > room['x'] - margin and
                room_y - margin < room['y'] + room['h'] + margin and
                room_y + room_h + margin > room['y'] - margin):
                return  # Overlap, reject

        # Carve out the room
        for y in range(room_y, room_y + room_h):
            for x in range(room_x, room_x + room_w):
                self.dungeon[y][x] = self.TILE_FLOOR

        self.rooms.append({
            'x': room_x, 'y': room_y,
            'w': room_w, 'h': room_h,
            'cx': room_x + room_w // 2,
            'cy': room_y + room_h // 2
        })

    def connect_rooms(self):
        """Connect all rooms with corridors."""
        for i in range(len(self.rooms) - 1):
            room_a = self.rooms[i]
            room_b = self.rooms[i + 1]

            # Corridor from center of A to center of B
            x1, y1 = room_a['cx'], room_a['cy']
            x2, y2 = room_b['cx'], room_b['cy']

            # L-shaped corridor
            if random.random() < 0.5:
                self.carve_h_corridor(x1, x2, y1)
                self.carve_v_corridor(y1, y2, x2)
            else:
                self.carve_v_corridor(y1, y2, x1)
                self.carve_h_corridor(x1, x2, y2)

    def carve_h_corridor(self, x1, x2, y):
        """Carve a horizontal corridor."""
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for dy in range(-1, 2):  # 3-wide corridor
                if 0 <= y + dy < self.DUNGEON_HEIGHT:
                    self.dungeon[y + dy][x] = self.TILE_FLOOR

    def carve_v_corridor(self, y1, y2, x):
        """Carve a vertical corridor."""
        for y in range(min(y1, y2), max(y1, y2) + 1):
            for dx in range(-1, 2):  # 3-wide corridor
                if 0 <= x + dx < self.DUNGEON_WIDTH:
                    self.dungeon[y][x + dx] = self.TILE_FLOOR

    def place_monsters(self):
        """Place monsters throughout the dungeon."""
        # Skip first room (player start) and last room (boss only)
        for i, room in enumerate(self.rooms[1:-1], 1):
            num_monsters = random.randint(1, 2 + self.level // 2)

            for _ in range(num_monsters):
                monster_type = self.choose_monster_type()
                mx = room['x'] + random.randint(2, room['w'] - 3)
                my = room['y'] + random.randint(2, room['h'] - 3)

                hp = 1
                if monster_type == 'spider':
                    hp = 1
                elif monster_type == 'blob':
                    hp = 999  # Invincible!

                self.monsters.append({
                    'type': monster_type,
                    'x': float(mx),
                    'y': float(my),
                    'hp': hp,
                    'is_boss': False,
                    'move_timer': random.random() * 2,
                    'direction': random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
                })

    def choose_monster_type(self):
        """Choose a monster type based on level."""
        weights = {
            'rat': 40,
            'spider': 30,
            'blob': 20 + self.level * 5,  # More blobs at higher levels
        }
        total = sum(weights.values())
        r = random.randint(0, total - 1)
        cumulative = 0
        for monster_type, weight in weights.items():
            cumulative += weight
            if r < cumulative:
                return monster_type
        return 'rat'

    def place_items(self):
        """Place items in rooms."""
        for room in self.rooms[1:]:  # Skip starting room
            # Quivers
            if random.random() < 0.6:
                ix = room['x'] + random.randint(2, room['w'] - 3)
                iy = room['y'] + random.randint(2, room['h'] - 3)
                self.items.append({'type': 'quiver', 'x': ix, 'y': iy})

            # Health
            if random.random() < 0.3:
                ix = room['x'] + random.randint(2, room['w'] - 3)
                iy = room['y'] + random.randint(2, room['h'] - 3)
                self.items.append({'type': 'health', 'x': ix, 'y': iy})

    def is_passable(self, x, y):
        """Check if a position is walkable."""
        ix, iy = int(x), int(y)
        if ix < 0 or ix >= self.DUNGEON_WIDTH or iy < 0 or iy >= self.DUNGEON_HEIGHT:
            return False
        return self.dungeon[iy][ix] == self.TILE_FLOOR

    def update_fog_of_war(self):
        """Reveal area around player."""
        px, py = int(self.player_x), int(self.player_y)
        radius = self.REVEAL_RADIUS

        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                dist = math.sqrt(dx * dx + dy * dy)
                if dist <= radius:
                    rx, ry = px + dx, py + dy
                    if 0 <= rx < self.DUNGEON_WIDTH and 0 <= ry < self.DUNGEON_HEIGHT:
                        self.revealed[ry][rx] = True

    def update_camera(self):
        """Update camera to follow player smoothly."""
        # Target: center player in viewport
        target_x = self.player_x - self.VIEW_WIDTH // 2
        target_y = self.player_y - self.VIEW_HEIGHT // 2

        # Clamp to dungeon bounds
        target_x = max(0, min(self.DUNGEON_WIDTH - self.VIEW_WIDTH, target_x))
        target_y = max(0, min(self.DUNGEON_HEIGHT - self.VIEW_HEIGHT, target_y))

        # Smooth camera movement
        self.camera_x += (target_x - self.camera_x) * 0.15
        self.camera_y += (target_y - self.camera_y) * 0.15

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        self.anim_timer += dt
        if self.hurt_timer > 0:
            self.hurt_timer -= dt

        self.move_cooldown -= dt

        # Player movement
        if self.move_cooldown <= 0:
            dx, dy = 0, 0
            if input_state.up:
                dy = -1
            elif input_state.down:
                dy = 1
            if input_state.left:
                dx = -1
            elif input_state.right:
                dx = 1

            if dx != 0 or dy != 0:
                # Update facing
                self.facing_x = dx if dx != 0 else self.facing_x
                self.facing_y = dy if dy != 0 else self.facing_y

                # Try to move
                new_x = self.player_x + dx * self.MOVE_SPEED * dt
                new_y = self.player_y + dy * self.MOVE_SPEED * dt

                # Check collision (check multiple points for sprite size)
                can_move_x = True
                can_move_y = True

                for check_dy in range(3):  # Player is ~3 pixels tall collision
                    if not self.is_passable(new_x, self.player_y + check_dy):
                        can_move_x = False
                    if not self.is_passable(self.player_x, new_y + check_dy):
                        can_move_y = False

                if can_move_x:
                    self.player_x = new_x
                if can_move_y:
                    self.player_y = new_y

                if can_move_x or can_move_y:
                    self.walk_frame = (self.walk_frame + 1) % 4
                    self.update_fog_of_war()

                    # Check item pickup
                    self.check_item_pickup()

                    # Check exit
                    if (abs(self.player_x - self.exit_x) < 3 and
                        abs(self.player_y - self.exit_y) < 3):
                        # Check if boss is dead
                        boss_alive = any(m['is_boss'] for m in self.monsters)
                        if not boss_alive:
                            self.next_level()
                            return

        # Shoot arrow
        if input_state.action_l and self.arrows > 0 and len(self.active_arrows) < 3:
            self.arrows -= 1
            # Shoot in facing direction
            dir_x = self.facing_x if self.facing_x != 0 else 0
            dir_y = self.facing_y if self.facing_y != 0 else 0
            if dir_x == 0 and dir_y == 0:
                dir_x = 1  # Default right

            self.active_arrows.append({
                'x': self.player_x + 1,
                'y': self.player_y + 1,
                'dx': dir_x,
                'dy': dir_y
            })

        # Update arrows
        self.update_arrows(dt)

        # Update monsters
        self.update_monsters(dt)

        # Check monster collision
        self.check_monster_collision()

        # Update camera
        self.update_camera()

    def update_arrows(self, dt: float):
        """Update arrows in flight."""
        arrows_to_remove = []

        for arrow in self.active_arrows:
            arrow['x'] += arrow['dx'] * self.ARROW_SPEED * dt
            arrow['y'] += arrow['dy'] * self.ARROW_SPEED * dt

            ax, ay = int(arrow['x']), int(arrow['y'])

            # Wall collision
            if not self.is_passable(ax, ay):
                arrows_to_remove.append(arrow)
                continue

            # Monster collision
            for monster in self.monsters[:]:
                mx, my = int(monster['x']), int(monster['y'])
                if abs(ax - mx) < 3 and abs(ay - my) < 3:
                    if monster['type'] == 'blob':
                        # Arrows pass through blobs harmlessly
                        continue

                    monster['hp'] -= 1
                    arrows_to_remove.append(arrow)

                    if monster['hp'] <= 0:
                        self.monsters.remove(monster)
                        # Score based on type
                        scores = {'rat': 25, 'spider': 50, 'snake': 100, 'dragon': 200}
                        self.score += scores.get(monster['type'], 25)
                    break

        for arrow in arrows_to_remove:
            if arrow in self.active_arrows:
                self.active_arrows.remove(arrow)

    def update_monsters(self, dt: float):
        """Update monster AI."""
        for monster in self.monsters:
            monster['move_timer'] -= dt

            if monster['move_timer'] <= 0:
                # Reset timer
                base_speed = 1.0
                if monster['type'] == 'blob':
                    base_speed = 2.0  # Slow
                elif monster['type'] == 'spider':
                    base_speed = 0.5  # Fast
                elif monster['type'] == 'rat':
                    base_speed = 0.8

                monster['move_timer'] = base_speed * (0.8 + random.random() * 0.4)

                # Movement AI
                if monster['type'] == 'blob':
                    # Blobs wander randomly
                    monster['direction'] = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
                else:
                    # Other monsters chase player if nearby
                    dx = self.player_x - monster['x']
                    dy = self.player_y - monster['y']
                    dist = math.sqrt(dx * dx + dy * dy)

                    if dist < 30:  # Chase range
                        if abs(dx) > abs(dy):
                            monster['direction'] = (1 if dx > 0 else -1, 0)
                        else:
                            monster['direction'] = (0, 1 if dy > 0 else -1)
                    else:
                        # Wander
                        if random.random() < 0.3:
                            monster['direction'] = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])

                # Try to move
                new_x = monster['x'] + monster['direction'][0] * 2
                new_y = monster['y'] + monster['direction'][1] * 2

                if self.is_passable(new_x, new_y):
                    monster['x'] = new_x
                    monster['y'] = new_y

    def check_monster_collision(self):
        """Check collision between player and monsters."""
        if self.hurt_timer > 0:
            return

        px, py = int(self.player_x), int(self.player_y)

        for monster in self.monsters:
            mx, my = int(monster['x']), int(monster['y'])

            if abs(px - mx) < 3 and abs(py - my) < 3:
                if monster['type'] == 'spider':
                    # Spiders steal arrows!
                    stolen = min(3, self.arrows)
                    self.arrows -= stolen
                    self.monsters.remove(monster)
                    continue

                # Take damage
                self.health -= 1
                self.hurt_timer = 1.0

                if self.health <= 0:
                    self.state = GameState.GAME_OVER
                return

    def check_item_pickup(self):
        """Check for item pickups."""
        px, py = int(self.player_x), int(self.player_y)

        for item in self.items[:]:
            if abs(item['x'] - px) < 3 and abs(item['y'] - py) < 3:
                if item['type'] == 'quiver':
                    self.arrows += 5
                    self.score += 10
                elif item['type'] == 'health':
                    self.health = min(self.health + 1, self.max_health)
                    self.score += 25
                self.items.remove(item)

    def next_level(self):
        """Advance to next level."""
        self.level += 1
        self.score += 100 * self.level
        self.arrows = min(self.arrows + 5, 20)
        self.active_arrows.clear()
        self.generate_dungeon()

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Draw dungeon with fog of war
        self.draw_dungeon()

        # Draw items
        self.draw_items()

        # Draw exit
        self.draw_exit()

        # Draw monsters
        self.draw_monsters()

        # Draw arrows
        self.draw_arrows()

        # Draw player
        self.draw_player()

        # Draw HUD
        self.draw_hud()

    def world_to_screen(self, wx, wy):
        """Convert world coordinates to screen coordinates."""
        sx = int(wx - self.camera_x)
        sy = int(wy - self.camera_y) + self.HUD_HEIGHT
        return sx, sy

    def draw_dungeon(self):
        """Draw the dungeon with fog of war."""
        cam_x, cam_y = int(self.camera_x), int(self.camera_y)

        for sy in range(self.VIEW_HEIGHT):
            for sx in range(self.VIEW_WIDTH):
                wx = cam_x + sx
                wy = cam_y + sy

                if 0 <= wx < self.DUNGEON_WIDTH and 0 <= wy < self.DUNGEON_HEIGHT:
                    screen_y = sy + self.HUD_HEIGHT

                    if self.revealed[wy][wx]:
                        # Revealed tile
                        if self.dungeon[wy][wx] == self.TILE_WALL:
                            self.display.set_pixel(sx, screen_y, self.WALL_COLOR)
                        else:
                            self.display.set_pixel(sx, screen_y, self.FLOOR_COLOR)
                    # Unrevealed stays black (already cleared)

    def draw_items(self):
        """Draw items."""
        for item in self.items:
            sx, sy = self.world_to_screen(item['x'], item['y'])

            if 0 <= sx < self.VIEW_WIDTH and self.HUD_HEIGHT <= sy < GRID_SIZE:
                # Only draw if revealed
                if self.revealed[int(item['y'])][int(item['x'])]:
                    if item['type'] == 'quiver':
                        self.display.set_pixel(sx, sy, self.QUIVER_COLOR)
                        self.display.set_pixel(sx + 1, sy, self.QUIVER_COLOR)
                    elif item['type'] == 'health':
                        if int(self.anim_timer * 4) % 2 == 0:
                            self.display.set_pixel(sx, sy, self.HEALTH_COLOR)

    def draw_exit(self):
        """Draw the exit ladder."""
        sx, sy = self.world_to_screen(self.exit_x, self.exit_y)

        if 0 <= sx < self.VIEW_WIDTH and self.HUD_HEIGHT <= sy < GRID_SIZE:
            if self.revealed[self.exit_y][self.exit_x]:
                # Ladder shape
                boss_alive = any(m['is_boss'] for m in self.monsters)
                color = Colors.GRAY if boss_alive else self.EXIT_COLOR

                # Pulsing if accessible
                if not boss_alive and int(self.anim_timer * 4) % 2 == 0:
                    color = Colors.WHITE

                # Draw ladder
                for dy in range(4):
                    self.display.set_pixel(sx, sy + dy, color)
                    self.display.set_pixel(sx + 2, sy + dy, color)
                self.display.set_pixel(sx + 1, sy + 1, color)
                self.display.set_pixel(sx + 1, sy + 3, color)

    def draw_monsters(self):
        """Draw all monsters."""
        for monster in self.monsters:
            mx, my = int(monster['x']), int(monster['y'])

            # Only draw if in revealed area
            if not self.revealed[my][mx]:
                continue

            sx, sy = self.world_to_screen(monster['x'], monster['y'])

            if not (0 <= sx < self.VIEW_WIDTH - 3 and self.HUD_HEIGHT <= sy < GRID_SIZE - 4):
                continue

            if monster['type'] == 'rat':
                # Small rat: 3x2
                self.display.set_pixel(sx, sy + 1, self.RAT_COLOR)
                self.display.set_pixel(sx + 1, sy, self.RAT_COLOR)
                self.display.set_pixel(sx + 1, sy + 1, self.RAT_COLOR)
                self.display.set_pixel(sx + 2, sy + 1, self.RAT_COLOR)

            elif monster['type'] == 'spider':
                # Spider: 3x3 with eyes
                self.display.set_pixel(sx, sy, self.SPIDER_COLOR)
                self.display.set_pixel(sx + 2, sy, self.SPIDER_COLOR)
                self.display.set_pixel(sx + 1, sy + 1, self.SPIDER_COLOR)
                self.display.set_pixel(sx, sy + 2, self.SPIDER_COLOR)
                self.display.set_pixel(sx + 2, sy + 2, self.SPIDER_COLOR)
                # Eyes
                if int(self.anim_timer * 6) % 3 == 0:
                    self.display.set_pixel(sx + 1, sy, self.SPIDER_EYE)

            elif monster['type'] == 'blob':
                # Blob: 4x3, pulsing
                pulse = int(self.anim_timer * 3) % 2
                color = self.BLOB_COLOR if pulse == 0 else (80, 180, 80)
                for dy in range(3):
                    for dx in range(3 + pulse):
                        self.display.set_pixel(sx + dx, sy + dy, color)

            elif monster['type'] == 'snake':
                # Snake: coiled 4x3
                self.display.set_pixel(sx + 1, sy, self.SNAKE_COLOR)
                self.display.set_pixel(sx + 2, sy, self.SNAKE_COLOR)
                self.display.set_pixel(sx, sy + 1, self.SNAKE_COLOR)
                self.display.set_pixel(sx + 2, sy + 1, self.SNAKE_PATTERN)
                self.display.set_pixel(sx + 1, sy + 2, self.SNAKE_COLOR)
                self.display.set_pixel(sx + 2, sy + 2, self.SNAKE_COLOR)
                # Tongue flick
                if int(self.anim_timer * 5) % 3 == 0:
                    self.display.set_pixel(sx + 3, sy + 1, Colors.RED)

            elif monster['type'] == 'dragon':
                # Dragon: 5x4
                # Body
                for dx in range(4):
                    self.display.set_pixel(sx + dx, sy + 2, self.DRAGON_COLOR)
                # Head
                self.display.set_pixel(sx + 4, sy + 1, self.DRAGON_COLOR)
                self.display.set_pixel(sx + 4, sy + 2, self.DRAGON_COLOR)
                # Wings
                wing_frame = int(self.anim_timer * 4) % 2
                self.display.set_pixel(sx + 1, sy + wing_frame, self.DRAGON_WING)
                self.display.set_pixel(sx + 2, sy + wing_frame, self.DRAGON_WING)
                # Tail
                self.display.set_pixel(sx, sy + 3, self.DRAGON_COLOR)
                # Fire breath
                if int(self.anim_timer * 6) % 4 == 0:
                    self.display.set_pixel(sx + 5, sy + 1, Colors.ORANGE)
                    self.display.set_pixel(sx + 5, sy + 2, Colors.YELLOW)

    def draw_arrows(self):
        """Draw arrows in flight."""
        for arrow in self.active_arrows:
            sx, sy = self.world_to_screen(arrow['x'], arrow['y'])
            if 0 <= sx < self.VIEW_WIDTH and self.HUD_HEIGHT <= sy < GRID_SIZE:
                self.display.set_pixel(sx, sy, self.ARROW_COLOR)
                # Trail
                tx = sx - arrow['dx']
                ty = sy - arrow['dy']
                if 0 <= tx < self.VIEW_WIDTH and self.HUD_HEIGHT <= ty < GRID_SIZE:
                    self.display.set_pixel(tx, ty, (180, 180, 0))

    def draw_player(self):
        """Draw the player character."""
        sx, sy = self.world_to_screen(self.player_x, self.player_y)

        # Blink when hurt
        if self.hurt_timer > 0 and int(self.hurt_timer * 10) % 2 == 0:
            return

        if not (0 <= sx < self.VIEW_WIDTH - 3 and self.HUD_HEIGHT <= sy < GRID_SIZE - 5):
            return

        # Body (3x4 sprite)
        # Head
        self.display.set_pixel(sx + 1, sy, self.PLAYER_COLOR)

        # Torso
        self.display.set_pixel(sx, sy + 1, self.PLAYER_COLOR)
        self.display.set_pixel(sx + 1, sy + 1, self.PLAYER_DARK)
        self.display.set_pixel(sx + 2, sy + 1, self.PLAYER_COLOR)

        # Legs (animated)
        if self.walk_frame % 2 == 0:
            self.display.set_pixel(sx, sy + 2, self.PLAYER_COLOR)
            self.display.set_pixel(sx + 2, sy + 2, self.PLAYER_COLOR)
        else:
            self.display.set_pixel(sx + 1, sy + 2, self.PLAYER_COLOR)

        # Bow in facing direction
        bow_x = sx + 1 + self.facing_x * 2
        bow_y = sy + 1 + self.facing_y * 2
        if 0 <= bow_x < GRID_SIZE and 0 <= bow_y < GRID_SIZE:
            self.display.set_pixel(bow_x, bow_y, Colors.YELLOW)

    def draw_hud(self):
        """Draw the heads-up display."""
        # Background bar
        self.display.draw_rect(0, 0, 64, self.HUD_HEIGHT, (20, 20, 30))

        # Score
        self.display.draw_text_small(1, 1, f"{self.score}", Colors.WHITE)

        # Level/Depth
        self.display.draw_text_small(28, 1, f"D{self.level}", Colors.CYAN)

        # Health hearts
        for i in range(self.max_health):
            hx = 48 + i * 5
            color = Colors.RED if i < self.health else Colors.DARK_GRAY
            self.display.set_pixel(hx, 1, color)
            self.display.set_pixel(hx + 1, 1, color)
            self.display.set_pixel(hx, 2, color)
            self.display.set_pixel(hx + 1, 2, color)

        # Arrow count
        self.display.draw_text_small(1, 4, f"A{self.arrows}", self.QUIVER_COLOR)

        # Boss indicator
        boss_alive = any(m['is_boss'] for m in self.monsters)
        if boss_alive:
            self.display.draw_text_small(28, 4, "BOSS", Colors.RED)

    def draw_game_over(self, selection: int = 0):
        """Draw game over screen."""
        self.display.clear(Colors.BLACK)

        self.display.draw_text_small(8, 12, "YOU DIED", Colors.RED)
        self.display.draw_text_small(8, 24, f"SCORE:{self.score}", Colors.WHITE)
        self.display.draw_text_small(8, 34, f"DEPTH:{self.level}", Colors.CYAN)

        if selection == 0:
            self.display.draw_text_small(4, 48, ">RETRY", Colors.YELLOW)
            self.display.draw_text_small(36, 48, " MENU", Colors.GRAY)
        else:
            self.display.draw_text_small(4, 48, " RETRY", Colors.GRAY)
            self.display.draw_text_small(36, 48, ">MENU", Colors.YELLOW)
