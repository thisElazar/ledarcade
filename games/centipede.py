"""
Centipede - Classic Arcade Shooter
==================================
Blast the centipede through the mushroom field!

Controls:
  Arrow Keys - Move (full movement in lower area)
  Space      - Fire
"""

import random
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


class Centipede(Game):
    name = "CENTIPEED"
    description = "Blast the bugs!"
    category = "arcade"
    GUIDE = {
        'desc': 'Shoot a centipede weaving down through a mushroom field. Hit a segment and it splits in two. Scorpions poison mushrooms — a segment that touches one dives straight down at you. Spiders score more the closer you shoot them (300/600/900). Losing a life repairs the field at +5 a mushroom. Extra life every 12,000. Clear the wave to advance.',
    }

    # Player constants
    PLAYER_AREA_TOP = 48  # Player can only move in bottom area
    PLAYER_SPEED = 32.0
    FIRE_COOLDOWN = 0.18

    # Centipede constants
    SEGMENT_SPEED = 16.0
    SEGMENT_SIZE = 3

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0
        self.lives = 3
        self.level = 1

        # Player position
        self.player_x = 32.0
        self.player_y = 58.0
        self.fire_cooldown = 0

        # Bullet (only one at a time)
        self.bullet = None

        # Mushrooms: set of (x, y) with health
        self.mushrooms = {}
        self.poisoned = set()  # (x, y) of scorpion-poisoned mushrooms
        self.spawn_mushrooms()

        # Centipede segments: list of {x, y, dir_x, is_head}
        self.segments = []
        self.spawn_centipede()

        # Spider
        self.spider = None
        self.spider_timer = 0

        # Flea (drops down creating mushrooms)
        self.flea = None
        self.flea_timer = 0

        # Scorpion (poisons mushrooms)
        self.scorpion = None
        self.scorpion_timer = 0

        # Lone-head pressure while the centipede camps the player zone
        self.head_spawn_timer = 0

        # Extra life every 12,000 points
        self.next_extra_life = 12000

        # Invincibility after death
        self.invincible = 0

    def spawn_mushrooms(self):
        """Spawn random mushrooms in the field."""
        self.mushrooms = {}
        # Spawn mushrooms in upper play area (fewer to keep field open)
        for _ in range(12 + self.level * 2):
            x = random.randint(1, 62)
            y = random.randint(8, self.PLAYER_AREA_TOP - 2)
            # Align to grid
            x = (x // 4) * 4 + 2
            y = (y // 4) * 4 + 2
            if (x, y) not in self.mushrooms:
                self.mushrooms[(x, y)] = 4  # 4 hits to destroy

    def spawn_centipede(self):
        """Spawn a new centipede wave.

        Waves total 12 units like the original: wave n has a chain of
        max(12-(n-1), 6) body segments plus min(n-1, 6) independent fast
        heads entering at random positions near the top.
        """
        self.segments = []
        length = max(12 - (self.level - 1), 6)
        num_heads = min(self.level - 1, 6)

        # Start from top — ensure start_x is high enough for all segments
        min_start_x = length * 3 + 2
        start_x = max(min_start_x, random.randint(10, 54))
        start_y = 6

        for i in range(length):
            seg_x = float(start_x - i * 3)
            # Clamp any segment that would be off-screen
            seg_x = max(2.0, seg_x)
            self.segments.append({
                'x': seg_x,
                'y': float(start_y),
                'dir_x': 1,  # Moving right
                'is_head': i == 0
            })

        # Independent fast heads enter at random x near the top
        for _ in range(num_heads):
            self.segments.append({
                'x': float(random.randint(6, 58)),
                'y': float(start_y),
                'dir_x': random.choice([1, -1]),
                'is_head': True,
                'speed_mult': 1.5,
            })

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        # Invincibility
        if self.invincible > 0:
            self.invincible -= dt

        # Player movement (confined to lower area)
        if input_state.left:
            self.player_x -= self.PLAYER_SPEED * dt
        if input_state.right:
            self.player_x += self.PLAYER_SPEED * dt
        if input_state.up:
            self.player_y -= self.PLAYER_SPEED * dt
        if input_state.down:
            self.player_y += self.PLAYER_SPEED * dt

        # Clamp player position
        self.player_x = max(2, min(61, self.player_x))
        self.player_y = max(self.PLAYER_AREA_TOP, min(61, self.player_y))

        # Firing
        self.fire_cooldown -= dt
        if (input_state.action_l_held or input_state.action_r_held) and self.fire_cooldown <= 0 and self.bullet is None:
            self.bullet = {'x': self.player_x, 'y': self.player_y - 2}
            self.fire_cooldown = self.FIRE_COOLDOWN

        # Update bullet
        if self.bullet:
            self.bullet['y'] -= 65 * dt
            if self.bullet['y'] < 0:
                self.bullet = None

        # Bullet collisions
        if self.bullet:
            bx, by = self.bullet['x'], self.bullet['y']

            # Check mushrooms
            for (mx, my), health in list(self.mushrooms.items()):
                if abs(bx - mx) < 3 and abs(by - my) < 3:
                    self.mushrooms[(mx, my)] = health - 1
                    if self.mushrooms[(mx, my)] <= 0:
                        del self.mushrooms[(mx, my)]
                        self.poisoned.discard((mx, my))
                        self.score += 1
                    self.bullet = None
                    break

            # Check centipede segments
            if self.bullet:
                for seg in self.segments[:]:
                    if abs(bx - seg['x']) < 3 and abs(by - seg['y']) < 3:
                        self.hit_segment(seg)
                        self.bullet = None
                        break

            # Check spider — proximity scoring, closer kills are worth more
            if self.bullet and self.spider:
                if abs(bx - self.spider['x']) < 4 and abs(by - self.spider['y']) < 4:
                    dy = abs(self.player_y - self.spider['y'])
                    self.score += 900 if dy < 8 else 600 if dy < 16 else 300
                    self.spider = None
                    self.bullet = None

            # Check flea
            if self.bullet and self.flea:
                if abs(bx - self.flea['x']) < 3 and abs(by - self.flea['y']) < 3:
                    self.flea['hits'] -= 1
                    if self.flea['hits'] <= 0:
                        self.flea = None
                        self.score += 200
                    else:
                        # First hit doubles its descent speed
                        self.flea['vy'] *= 2
                    self.bullet = None

            # Check scorpion
            if self.bullet and self.scorpion:
                if abs(bx - self.scorpion['x']) < 4 and abs(by - self.scorpion['y']) < 3:
                    self.scorpion = None
                    self.score += 1000
                    self.bullet = None

        # Update centipede
        self.update_centipede(dt)

        # Anti-camping pressure: while any segment is in the player zone,
        # lone heads periodically enter from the sides at player-zone rows
        if any(seg['y'] >= self.PLAYER_AREA_TOP for seg in self.segments):
            self.head_spawn_timer += dt
            if self.head_spawn_timer >= 4.0:
                self.head_spawn_timer = 0
                from_left = random.random() < 0.5
                self.segments.append({
                    'x': 2.0 if from_left else 62.0,
                    'y': float(random.choice([50, 54, 58])),
                    'dir_x': 1 if from_left else -1,
                    'is_head': True,
                    'speed_mult': 1.5,
                })
        else:
            self.head_spawn_timer = 0

        # Update spider
        self.update_spider(dt)

        # Update flea
        self.update_flea(dt)

        # Update scorpion
        self.update_scorpion(dt)

        # Player collision with enemies
        if self.invincible <= 0:
            # Check centipede
            for seg in self.segments:
                if abs(self.player_x - seg['x']) < 3 and abs(self.player_y - seg['y']) < 3:
                    self.player_hit()
                    break

            # Check spider
            if self.spider:
                if abs(self.player_x - self.spider['x']) < 4 and abs(self.player_y - self.spider['y']) < 4:
                    self.player_hit()

        # Extra life every 12,000 points
        if self.score >= self.next_extra_life:
            self.lives += 1
            self.next_extra_life += 12000

        # Check if centipede is cleared
        if len(self.segments) == 0:
            self.next_level()

    def hit_segment(self, segment):
        """Handle hitting a centipede segment."""
        # Create mushroom where segment was hit
        mx = (int(segment['x']) // 4) * 4 + 2
        my = (int(segment['y']) // 4) * 4 + 2
        if 8 <= my < self.PLAYER_AREA_TOP:
            self.mushrooms[(mx, my)] = 4

        # Score
        self.score += 100 if segment['is_head'] else 10

        # Find segment index
        idx = self.segments.index(segment)

        # Split centipede - segments after this one become a new head
        if idx < len(self.segments) - 1:
            self.segments[idx + 1]['is_head'] = True

        # Remove the hit segment
        self.segments.remove(segment)

    def update_centipede(self, dt: float):
        """Update centipede movement — grid-row dropping, one row at a time."""
        speed = self.SEGMENT_SPEED + self.level * 2
        base_step = speed * dt

        for seg in self.segments:
            step = base_step * seg.get('speed_mult', 1.0)

            # --- vertical drop phase (animate one row down) ---
            if seg.get('dropping'):
                seg['drop_progress'] += step
                if seg['drop_progress'] >= 4.0:
                    # Landed on target row
                    seg['y'] = seg['drop_target']
                    del seg['dropping']
                    del seg['drop_progress']
                    del seg['drop_target']
                    del seg['drop_start']
                    if seg.get('plummet') and seg['y'] < self.PLAYER_AREA_TOP \
                            and seg['y'] + 4.0 <= 60:
                        # Poisoned: keep plummeting row-by-row until the
                        # player zone, then resume normal behavior
                        seg['dropping'] = True
                        seg['drop_start'] = seg['y']
                        seg['drop_target'] = seg['y'] + 4.0
                        seg['drop_progress'] = 0.0
                    else:
                        seg.pop('plummet', None)
                        # Must travel one grid cell horizontally before
                        # mushroom collisions re-enable (prevents cascade)
                        seg['h_since_drop'] = 0.0
                else:
                    seg['y'] = seg['drop_start'] + seg['drop_progress']
                continue  # no horizontal movement while dropping

            # --- horizontal phase ---
            new_x = seg['x'] + seg['dir_x'] * step
            h_moved = seg.get('h_since_drop', 99.0) + abs(new_x - seg['x'])

            hit = False

            # Wall collision (always checked, boundaries match grid edges)
            if new_x < 2 or new_x > 62:
                hit = True

            # Mushroom collision — same row only, requires one grid cell
            # of horizontal travel after a drop to prevent cascade
            if not hit and h_moved >= 4.0:
                row_y = round((seg['y'] - 2) / 4) * 4 + 2
                for (mx, my) in self.mushrooms:
                    if abs(my - row_y) < 1 and abs(new_x - mx) < 3:
                        hit = True
                        if (mx, my) in self.poisoned:
                            seg['plummet'] = True  # dive to the player zone
                        break

            if hit:
                seg['dir_x'] *= -1
                seg['x'] = round((seg['x'] - 2) / 4) * 4 + 2  # snap to grid
                drop_target = seg['y'] + 4.0
                if drop_target > 60:
                    # At bottom — just reverse, don't drop further
                    seg['y'] = min(seg['y'], 60.0)
                else:
                    seg['dropping'] = True
                    seg['drop_start'] = seg['y']
                    seg['drop_target'] = drop_target
                    seg['drop_progress'] = 0.0
            else:
                seg['x'] = new_x
                seg['h_since_drop'] = h_moved

    def update_spider(self, dt: float):
        """Update spider enemy."""
        self.spider_timer += dt

        if self.spider is None:
            if self.spider_timer > 5.0:
                self.spider_timer = 0
                # Spawn spider from side
                self.spider = {
                    'x': 0 if random.random() < 0.5 else 63,
                    'y': random.randint(self.PLAYER_AREA_TOP, 58),
                    'vx': random.choice([-20, 20]),
                    'vy': random.choice([-14, 14]),
                    'lifetime': 0.0,
                    'exiting': False,
                }
        else:
            # Track lifetime
            self.spider['lifetime'] += dt

            if self.spider.get('exiting', False):
                # Move toward nearest edge to exit
                if self.spider['x'] < 32:
                    self.spider['vx'] = -28
                else:
                    self.spider['vx'] = 28
                self.spider['vy'] = 0

                self.spider['x'] += self.spider['vx'] * dt
                self.spider['y'] += self.spider['vy'] * dt
            else:
                # Check lifetime — start exiting after ~8s
                if self.spider['lifetime'] >= 8.0:
                    self.spider['exiting'] = True

                # Move erratically
                self.spider['x'] += self.spider['vx'] * dt
                self.spider['y'] += self.spider['vy'] * dt

                # Bounce off walls
                if self.spider['x'] < 2 or self.spider['x'] > 61:
                    self.spider['vx'] *= -1
                if self.spider['y'] < self.PLAYER_AREA_TOP or self.spider['y'] > 60:
                    self.spider['vy'] *= -1

                # Random direction changes — biased toward player
                if random.random() < 0.02:
                    if random.random() < 0.6:
                        # Bias toward player
                        self.spider['vx'] = 20 if self.player_x > self.spider['x'] else -20
                        self.spider['vy'] = 14 if self.player_y > self.spider['y'] else -14
                    else:
                        self.spider['vx'] = random.choice([-20, 20])
                        self.spider['vy'] = random.choice([-14, 14])

            # Spider eats mushrooms
            for (mx, my) in list(self.mushrooms.keys()):
                if my >= self.PLAYER_AREA_TOP - 4:
                    if abs(self.spider['x'] - mx) < 4 and abs(self.spider['y'] - my) < 4:
                        del self.mushrooms[(mx, my)]
                        self.poisoned.discard((mx, my))
                        break

            # Exit screen
            if self.spider['x'] < -5 or self.spider['x'] > 68:
                self.spider = None

    def update_flea(self, dt: float):
        """Update flea enemy (drops creating mushrooms)."""
        self.flea_timer += dt

        # Spawn flea if few mushrooms in player area
        mushrooms_in_player_area = sum(1 for (_, my) in self.mushrooms if my >= self.PLAYER_AREA_TOP - 8)

        if self.flea is None:
            if self.flea_timer > 8.0 and mushrooms_in_player_area < 3:
                self.flea_timer = 0
                self.flea = {
                    'x': random.randint(10, 54),
                    'y': 0,
                    'hits': 2,
                    'vy': 30,  # doubles after the first hit
                }
        else:
            self.flea['y'] += self.flea['vy'] * dt

            # Drop mushrooms
            if random.random() < 0.1:
                mx = (int(self.flea['x']) // 4) * 4 + 2
                my = (int(self.flea['y']) // 4) * 4 + 2
                if (mx, my) not in self.mushrooms and 8 <= my < 60:
                    self.mushrooms[(mx, my)] = 4

            # Exit screen
            if self.flea['y'] > 65:
                self.flea = None

    def update_scorpion(self, dt: float):
        """Update scorpion enemy (poisons mushrooms)."""
        self.scorpion_timer += dt

        if self.scorpion is None:
            if self.scorpion_timer > 15.0 and self.level >= 2:
                self.scorpion_timer = 0
                side = random.choice([-1, 1])
                self.scorpion = {
                    'x': 0 if side > 0 else 63,
                    # Snap to a mushroom grid row so it passes over caps
                    'y': (random.randint(10, 30) // 4) * 4 + 2,
                    'dir': side
                }
        else:
            self.scorpion['x'] += self.scorpion['dir'] * 16 * dt

            # Poison every mushroom the scorpion passes over
            for (mx, my) in self.mushrooms:
                if abs(my - self.scorpion['y']) < 2 and abs(mx - self.scorpion['x']) < 3:
                    self.poisoned.add((mx, my))

            # Exit screen
            if self.scorpion['x'] < -5 or self.scorpion['x'] > 68:
                self.scorpion = None

    def player_hit(self):
        """Handle player death."""
        self.lives -= 1

        # Mushroom repair tally: every damaged or poisoned mushroom is
        # restored to full health at +5 points each (like the original)
        for pos, health in self.mushrooms.items():
            if health < 4 or pos in self.poisoned:
                self.mushrooms[pos] = 4
                self.score += 5
        self.poisoned.clear()

        if self.lives <= 0:
            self.state = GameState.GAME_OVER
        else:
            self.invincible = 2.0
            self.player_x = 32
            self.player_y = 58

            # Reset centipede to top
            self.spawn_centipede()
            self.spider = None
            self.flea = None

    def next_level(self):
        """Advance to next level."""
        self.level += 1
        self.spawn_centipede()
        # Don't reset mushrooms - they persist

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Draw mushrooms
        for (mx, my), health in self.mushrooms.items():
            self.draw_mushroom(mx, my, health)

        # Draw centipede
        for seg in self.segments:
            self.draw_segment(int(seg['x']), int(seg['y']), seg['is_head'])

        # Draw spider
        if self.spider:
            self.draw_spider(int(self.spider['x']), int(self.spider['y']))

        # Draw flea
        if self.flea:
            self.draw_flea(int(self.flea['x']), int(self.flea['y']))

        # Draw scorpion
        if self.scorpion:
            self.draw_scorpion(int(self.scorpion['x']), int(self.scorpion['y']))

        # Draw bullet
        if self.bullet:
            bx, by = int(self.bullet['x']), int(self.bullet['y'])
            self.display.set_pixel(bx, by, Colors.WHITE)
            self.display.set_pixel(bx, by + 1, Colors.WHITE)

        # Draw player (blink if invincible)
        if self.invincible <= 0 or int(self.invincible * 10) % 2 == 0:
            self.draw_player(int(self.player_x), int(self.player_y))

        # HUD
        self.display.draw_text_small(1, 1, f"{self.score}", Colors.WHITE)
        # Lives
        for i in range(self.lives - 1):
            self.display.set_pixel(58 - i * 4, 2, Colors.CYAN)

    def draw_mushroom(self, x: int, y: int, health: int):
        """Draw a mushroom."""
        # Color based on health (poisoned caps are purple)
        if (x, y) in self.poisoned:
            color = (170, 0, 255)
        elif health == 4:
            color = Colors.GREEN
        elif health == 3:
            color = (150, 200, 50)
        elif health == 2:
            color = Colors.YELLOW
        else:
            color = Colors.ORANGE

        # Simple mushroom shape
        self.display.set_pixel(x, y - 1, color)
        self.display.set_pixel(x - 1, y, color)
        self.display.set_pixel(x, y, color)
        self.display.set_pixel(x + 1, y, color)
        self.display.set_pixel(x, y + 1, (139, 90, 43))  # Stem

    def draw_segment(self, x: int, y: int, is_head: bool):
        """Draw a centipede segment."""
        color = Colors.MAGENTA if is_head else Colors.GREEN

        self.display.set_pixel(x - 1, y, color)
        self.display.set_pixel(x, y, color)
        self.display.set_pixel(x + 1, y, color)
        self.display.set_pixel(x, y - 1, color)
        self.display.set_pixel(x, y + 1, color)

        if is_head:
            # Eyes
            self.display.set_pixel(x - 1, y - 1, Colors.WHITE)
            self.display.set_pixel(x + 1, y - 1, Colors.WHITE)

    def draw_player(self, x: int, y: int):
        """Draw the player ship."""
        self.display.set_pixel(x, y - 1, Colors.CYAN)
        self.display.set_pixel(x - 1, y, Colors.CYAN)
        self.display.set_pixel(x, y, Colors.WHITE)
        self.display.set_pixel(x + 1, y, Colors.CYAN)
        self.display.set_pixel(x, y + 1, Colors.CYAN)

    def draw_spider(self, x: int, y: int):
        """Draw the spider."""
        color = Colors.ORANGE
        self.display.set_pixel(x, y, color)
        self.display.set_pixel(x - 2, y - 1, color)
        self.display.set_pixel(x + 2, y - 1, color)
        self.display.set_pixel(x - 2, y + 1, color)
        self.display.set_pixel(x + 2, y + 1, color)
        self.display.set_pixel(x - 1, y, color)
        self.display.set_pixel(x + 1, y, color)

    def draw_flea(self, x: int, y: int):
        """Draw the flea."""
        color = Colors.PINK
        self.display.set_pixel(x, y - 1, color)
        self.display.set_pixel(x, y, color)
        self.display.set_pixel(x, y + 1, color)
        self.display.set_pixel(x - 1, y, color)
        self.display.set_pixel(x + 1, y, color)

    def draw_scorpion(self, x: int, y: int):
        """Draw the scorpion."""
        color = Colors.BLUE
        self.display.set_pixel(x - 2, y, color)
        self.display.set_pixel(x - 1, y, color)
        self.display.set_pixel(x, y, color)
        self.display.set_pixel(x + 1, y, color)
        self.display.set_pixel(x + 2, y - 1, color)  # Tail

    def draw_game_over(self):
        self.display.clear(Colors.BLACK)
        self.display.draw_text_small(8, 20, "GAME OVER", Colors.RED)
        self.display.draw_text_small(10, 32, f"SCORE:{self.score}", Colors.WHITE)
        self.display.draw_text_small(4, 50, "BTN:RETRY", Colors.GRAY)
