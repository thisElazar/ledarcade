"""
Defender - Side-Scrolling Shooter
=================================
Protect 10 humans from alien Landers in a wrapping 256px world.

Controls:
  Left/Right - Thrust + set facing direction
  Up/Down    - Vertical movement
  Space      - Fire laser (hold for auto-fire)
  Z          - Smart bomb (kills all visible enemies)
"""

import random
import math
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE

# World constants
WORLD_WIDTH = 256
VIEW_WIDTH = 64
VIEW_HEIGHT = 56  # Playfield above scanner
SCANNER_Y = 57    # Scanner starts at row 57
SCANNER_HEIGHT = 7

# Player constants
PLAYER_ACCEL = 160.0
PLAYER_DRAG = 0.92
PLAYER_MAX_SPEED = 80.0
PLAYER_VERT_SPEED = 60.0
FIRE_COOLDOWN = 0.15
MAX_BULLETS = 4
BULLET_SPEED = 200.0

# Terrain
TERRAIN_SEGMENTS = 32
TERRAIN_MIN_Y = 48
TERRAIN_MAX_Y = 54


class Defender(Game):
    name = "DEFENDER"
    description = "Protect humans from aliens!"
    category = "arcade"

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0
        self.lives = 3
        self.smart_bombs = 3
        self.wave = 1
        self.wave_clear_timer = 0

        # Player
        self.px = WORLD_WIDTH / 2  # world x
        self.py = 28.0             # screen y
        self.vx = 0.0              # horizontal velocity
        self.facing = 1            # 1=right, -1=left
        self.fire_cooldown = 0.0
        self.invincible = 0.0

        # Camera
        self.cam_x = self.px - VIEW_WIDTH / 2

        # Terrain (height map, indexed by world x)
        self._generate_terrain()

        # Bullets
        self.bullets = []     # {wx, wy, dir}
        self.enemy_bullets = []  # {wx, wy, vx, vy}

        # Humans
        self.humans = []
        self._spawn_humans(10)

        # Enemies
        self.enemies = []
        self._spawn_wave()

        # Animation
        self.anim_timer = 0.0
        self.anim_frame = 0

    def _generate_terrain(self):
        """Generate a mountain silhouette terrain for the entire world."""
        self.terrain = []
        # Create smooth terrain using sine waves
        for x in range(WORLD_WIDTH):
            h = TERRAIN_MIN_Y
            h += 2 * math.sin(x * 0.05)
            h += 1.5 * math.sin(x * 0.12 + 1.0)
            h += 1 * math.sin(x * 0.03 + 2.5)
            self.terrain.append(int(h))

    def _terrain_y(self, wx):
        """Get terrain height at world x (wrapping)."""
        return self.terrain[int(wx) % WORLD_WIDTH]

    def _spawn_humans(self, count):
        """Place humans on the terrain."""
        self.humans = []
        for i in range(count):
            wx = (i * WORLD_WIDTH // count) + random.randint(0, 10)
            wx %= WORLD_WIDTH
            wy = self._terrain_y(wx) - 1
            self.humans.append({
                'wx': float(wx),
                'wy': float(wy),
                'state': 'walking',  # walking, captured, falling, dead
                'walk_dir': random.choice([-1, 1]),
                'captor': None,      # ref to lander carrying this human
            })

    def _spawn_wave(self):
        """Spawn enemies for the current wave."""
        self.enemies = []
        num_landers = 6 + self.wave * 2
        num_bombers = 1 + self.wave
        num_pods = max(0, self.wave - 2)

        for _ in range(num_landers):
            self._spawn_enemy('lander')
        for _ in range(num_bombers):
            self._spawn_enemy('bomber')
        for _ in range(num_pods):
            self._spawn_enemy('pod')

    def _spawn_enemy(self, etype, wx=None, wy=None):
        """Spawn a single enemy."""
        if wx is None:
            wx = random.uniform(0, WORLD_WIDTH)
        if wy is None:
            wy = random.uniform(5, 25)
        enemy = {
            'type': etype,
            'wx': float(wx),
            'wy': float(wy),
            'vx': random.uniform(-20, 20),
            'vy': random.uniform(-5, 5),
            'target_human': None,
            'shoot_timer': random.uniform(1.0, 3.0),
            'alive': True,
        }
        if etype == 'mutant':
            enemy['vx'] = random.uniform(-40, 40)
        elif etype == 'swarmer':
            enemy['vx'] = random.uniform(-60, 60)
            enemy['vy'] = random.uniform(-30, 30)
        self.enemies.append(enemy)
        return enemy

    def _wrap_x(self, x):
        """Wrap world x coordinate."""
        return x % WORLD_WIDTH

    def _world_dist_x(self, x1, x2):
        """Signed shortest distance in wrapping world (x2 - x1)."""
        d = (x2 - x1) % WORLD_WIDTH
        if d > WORLD_WIDTH / 2:
            d -= WORLD_WIDTH
        return d

    def _world_to_screen(self, wx, wy):
        """Convert world coords to screen coords. Returns (sx, sy) or None if off-screen."""
        dx = self._world_dist_x(self.cam_x, wx)
        if dx < -2 or dx >= VIEW_WIDTH + 2:
            return None
        return int(dx), int(wy)

    def _is_visible(self, wx):
        """Check if world x is within the visible area."""
        dx = self._world_dist_x(self.cam_x, wx)
        return -4 <= dx < VIEW_WIDTH + 4

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        # Wave clear pause
        if self.wave_clear_timer > 0:
            self.wave_clear_timer -= dt
            if self.wave_clear_timer <= 0:
                self.wave += 1
                self._spawn_wave()
            return

        # Animation
        self.anim_timer += dt
        if self.anim_timer >= 0.15:
            self.anim_timer = 0
            self.anim_frame = (self.anim_frame + 1) % 2

        # Invincibility
        if self.invincible > 0:
            self.invincible -= dt

        # Player movement
        if input_state.left:
            self.vx -= PLAYER_ACCEL * dt
            self.facing = -1
        if input_state.right:
            self.vx += PLAYER_ACCEL * dt
            self.facing = 1

        # Drag
        self.vx *= PLAYER_DRAG
        # Clamp speed
        if abs(self.vx) > PLAYER_MAX_SPEED:
            self.vx = math.copysign(PLAYER_MAX_SPEED, self.vx)
        if abs(self.vx) < 0.5:
            self.vx = 0

        self.px = self._wrap_x(self.px + self.vx * dt)

        # Vertical movement
        if input_state.up:
            self.py -= PLAYER_VERT_SPEED * dt
        if input_state.down:
            self.py += PLAYER_VERT_SPEED * dt
        self.py = max(2, min(VIEW_HEIGHT - 3, self.py))

        # Camera follows player with facing offset
        target_cam = self.px - VIEW_WIDTH / 2 + self.facing * 10
        cam_diff = self._world_dist_x(self.cam_x, target_cam)
        self.cam_x = self._wrap_x(self.cam_x + cam_diff * 0.3)

        # Hard clamp: ensure player stays on visible screen with margin
        screen_x = self._world_dist_x(self.cam_x, self.px)
        margin = 6
        if screen_x < margin:
            self.cam_x = self._wrap_x(self.px - margin)
        elif screen_x > VIEW_WIDTH - margin:
            self.cam_x = self._wrap_x(self.px - VIEW_WIDTH + margin)

        # Firing
        self.fire_cooldown -= dt
        firing = input_state.action_l_held or input_state.action_r_held
        if firing and self.fire_cooldown <= 0 and len(self.bullets) < MAX_BULLETS:
            self.bullets.append({
                'wx': self.px + self.facing * 3,
                'wy': self.py,
                'dir': self.facing,
            })
            self.fire_cooldown = FIRE_COOLDOWN

        # Smart bomb (both buttons)
        if input_state.action_l_held and input_state.action_r_held and self.smart_bombs > 0:
            self.smart_bombs -= 1
            self._smart_bomb()

        # Update bullets
        for b in self.bullets:
            b['wx'] = self._wrap_x(b['wx'] + b['dir'] * BULLET_SPEED * dt)
        self.bullets = [b for b in self.bullets if self._bullet_alive(b)]

        # Update enemy bullets
        for b in self.enemy_bullets:
            b['wx'] = self._wrap_x(b['wx'] + b['vx'] * dt)
            b['wy'] += b['vy'] * dt
        self.enemy_bullets = [b for b in self.enemy_bullets
                              if 0 < b['wy'] < VIEW_HEIGHT]

        # Update humans
        self._update_humans(dt)

        # Update enemies
        self._update_enemies(dt)

        # Collision: player bullets vs enemies
        self._check_bullet_enemy_collisions()

        # Collision: enemy bullets vs player
        if self.invincible <= 0:
            for b in self.enemy_bullets[:]:
                dist_x = abs(self._world_dist_x(b['wx'], self.px))
                if dist_x < 3 and abs(b['wy'] - self.py) < 3:
                    self._player_hit()
                    self.enemy_bullets.remove(b)
                    break

        # Collision: enemies vs player
        if self.invincible <= 0:
            for e in self.enemies:
                if not e['alive']:
                    continue
                dist_x = abs(self._world_dist_x(e['wx'], self.px))
                if dist_x < 4 and abs(e['wy'] - self.py) < 4:
                    self._player_hit()
                    e['alive'] = False
                    break

        # Collision: player catches falling humans
        for h in self.humans:
            if h['state'] == 'falling':
                dist_x = abs(self._world_dist_x(h['wx'], self.px))
                if dist_x < 5 and abs(h['wy'] - self.py) < 5:
                    # Caught! Set back on terrain
                    h['state'] = 'walking'
                    h['wy'] = self._terrain_y(h['wx']) - 1
                    self.score += 500

        # Clean dead enemies
        self.enemies = [e for e in self.enemies if e['alive']]

        # Check all humans dead -> all landers become mutants
        if all(h['state'] == 'dead' for h in self.humans):
            for e in self.enemies:
                if e['type'] == 'lander':
                    e['type'] = 'mutant'
                    e['vx'] = random.uniform(-40, 40)

        # Check wave clear
        if len(self.enemies) == 0:
            self.wave_clear_timer = 1.5

    def _bullet_alive(self, b):
        """Check if a bullet has traveled too far (>80px)."""
        # Simple lifetime check: we track by checking if still on-ish screen
        # Bullets travel fast, just keep them for ~0.5s worth of travel
        return True  # cleaned by collision or off-screen check in draw

    def _smart_bomb(self):
        """Kill all visible enemies."""
        for e in self.enemies:
            if self._is_visible(e['wx']):
                pts = {'lander': 100, 'mutant': 150, 'bomber': 250,
                       'pod': 1000, 'swarmer': 150}.get(e['type'], 100)
                self.score += pts
                # Release captured humans
                for h in self.humans:
                    if h['captor'] is e:
                        h['state'] = 'falling'
                        h['captor'] = None
                if e['type'] == 'pod':
                    pass  # No swarmers from smart bomb
                e['alive'] = False
        self.enemy_bullets = [b for b in self.enemy_bullets
                              if not self._is_visible(b['wx'])]

    def _update_humans(self, dt):
        for h in self.humans:
            if h['state'] == 'walking':
                h['wx'] = self._wrap_x(h['wx'] + h['walk_dir'] * 3 * dt)
                h['wy'] = self._terrain_y(h['wx']) - 1
                if random.random() < 0.005:
                    h['walk_dir'] *= -1
            elif h['state'] == 'captured':
                captor = h['captor']
                if captor and captor['alive']:
                    h['wx'] = captor['wx']
                    h['wy'] = captor['wy'] + 3
                else:
                    # Captor died
                    h['state'] = 'falling'
                    h['captor'] = None
            elif h['state'] == 'falling':
                h['wy'] += 40 * dt
                terrain_y = self._terrain_y(h['wx'])
                if h['wy'] >= terrain_y - 1:
                    # Landed safely back on ground
                    h['wy'] = terrain_y - 1
                    h['state'] = 'walking'

    def _update_enemies(self, dt):
        for e in self.enemies:
            if not e['alive']:
                continue

            if e['type'] == 'lander':
                self._update_lander(e, dt)
            elif e['type'] == 'mutant':
                self._update_mutant(e, dt)
            elif e['type'] == 'bomber':
                self._update_bomber(e, dt)
            elif e['type'] == 'pod':
                self._update_pod(e, dt)
            elif e['type'] == 'swarmer':
                self._update_swarmer(e, dt)

            # Shooting (landers, mutants)
            if e['type'] in ('lander', 'mutant', 'bomber'):
                e['shoot_timer'] -= dt
                if e['shoot_timer'] <= 0 and self._is_visible(e['wx']):
                    self._enemy_shoot(e)
                    e['shoot_timer'] = random.uniform(1.5, 3.5)

    def _update_lander(self, e, dt):
        """Lander: patrol, then dive to grab a human."""
        # Find a target human if we don't have one
        if e['target_human'] is None:
            walking = [h for h in self.humans if h['state'] == 'walking']
            if walking and random.random() < 0.01:
                e['target_human'] = random.choice(walking)

        target = e['target_human']
        if target and target['state'] == 'walking':
            # Move toward human
            dx = self._world_dist_x(e['wx'], target['wx'])
            e['vx'] += math.copysign(30, dx) * dt
            # Descend toward human
            if e['wy'] < target['wy'] - 3:
                e['vy'] = 25
            else:
                e['vy'] = -5
            # Grab if close
            if abs(dx) < 3 and abs(e['wy'] - target['wy']) < 5:
                target['state'] = 'captured'
                target['captor'] = e
                e['target_human'] = None
                e['vy'] = -20  # Start carrying upward
        elif target and target['state'] == 'captured' and target['captor'] is e:
            # Carrying human upward
            e['vy'] = -20
            if e['wy'] < 2:
                # Reached top - human dies, lander becomes mutant
                target['state'] = 'dead'
                target['captor'] = None
                e['type'] = 'mutant'
                e['vy'] = random.uniform(-10, 10)
                e['vx'] = random.uniform(-40, 40)
                return
        else:
            # Patrol
            e['target_human'] = None
            e['vy'] *= 0.95
            if e['wy'] < 8:
                e['vy'] += 15 * dt
            elif e['wy'] > 35:
                e['vy'] -= 15 * dt

        e['vx'] = max(-30, min(30, e['vx']))
        e['wx'] = self._wrap_x(e['wx'] + e['vx'] * dt)
        e['wy'] = max(3, min(VIEW_HEIGHT - 5, e['wy'] + e['vy'] * dt))

    def _update_mutant(self, e, dt):
        """Mutant: aggressively homes toward player."""
        dx = self._world_dist_x(e['wx'], self.px)
        dy = self.py - e['wy']
        e['vx'] += math.copysign(50, dx) * dt
        e['vy'] += math.copysign(40, dy) * dt
        e['vx'] = max(-50, min(50, e['vx']))
        e['vy'] = max(-40, min(40, e['vy']))
        e['wx'] = self._wrap_x(e['wx'] + e['vx'] * dt)
        e['wy'] = max(3, min(VIEW_HEIGHT - 3, e['wy'] + e['vy'] * dt))

    def _update_bomber(self, e, dt):
        """Bomber: flies horizontally, drops mines."""
        e['wx'] = self._wrap_x(e['wx'] + e['vx'] * dt)
        e['vy'] *= 0.98
        e['wy'] = max(5, min(40, e['wy'] + e['vy'] * dt))
        # Occasionally drop a mine
        if random.random() < 0.01 and self._is_visible(e['wx']):
            self.enemy_bullets.append({
                'wx': e['wx'], 'wy': e['wy'],
                'vx': 0, 'vy': 15,
            })

    def _update_pod(self, e, dt):
        """Pod: drifts slowly."""
        e['wx'] = self._wrap_x(e['wx'] + e['vx'] * 0.3 * dt)
        e['wy'] += math.sin(self.anim_timer * 2 + e['wx']) * 3 * dt

    def _update_swarmer(self, e, dt):
        """Swarmer: tiny, fast, erratic."""
        e['vx'] += random.uniform(-80, 80) * dt
        e['vy'] += random.uniform(-60, 60) * dt
        # Tend toward player
        dx = self._world_dist_x(e['wx'], self.px)
        e['vx'] += math.copysign(20, dx) * dt
        e['vx'] = max(-70, min(70, e['vx']))
        e['vy'] = max(-50, min(50, e['vy']))
        e['wx'] = self._wrap_x(e['wx'] + e['vx'] * dt)
        e['wy'] = max(3, min(VIEW_HEIGHT - 3, e['wy'] + e['vy'] * dt))

    def _enemy_shoot(self, e):
        """Enemy fires a bullet toward the player."""
        dx = self._world_dist_x(e['wx'], self.px)
        dy = self.py - e['wy']
        dist = max(1, math.sqrt(dx * dx + dy * dy))
        speed = 50
        self.enemy_bullets.append({
            'wx': e['wx'],
            'wy': e['wy'],
            'vx': dx / dist * speed,
            'vy': dy / dist * speed,
        })

    def _check_bullet_enemy_collisions(self):
        for b in self.bullets[:]:
            hit = False
            for e in self.enemies:
                if not e['alive']:
                    continue
                dist_x = abs(self._world_dist_x(b['wx'], e['wx']))
                dist_y = abs(b['wy'] - e['wy'])
                size = 1 if e['type'] == 'swarmer' else 3
                if dist_x < size + 1 and dist_y < size + 1:
                    # Hit!
                    pts = {'lander': 100, 'mutant': 150, 'bomber': 250,
                           'pod': 1000, 'swarmer': 150}.get(e['type'], 100)
                    self.score += pts

                    # Release captured human
                    for h in self.humans:
                        if h['captor'] is e:
                            h['state'] = 'falling'
                            h['captor'] = None

                    # Pod releases swarmers
                    if e['type'] == 'pod':
                        for _ in range(3):
                            self._spawn_enemy('swarmer', e['wx'] + random.uniform(-3, 3),
                                              e['wy'] + random.uniform(-3, 3))

                    e['alive'] = False
                    if b in self.bullets:
                        self.bullets.remove(b)
                    hit = True
                    break
            # Remove bullets that have traveled far
            if not hit:
                # Check if bullet is far from player (traveled > half world)
                dist = abs(self._world_dist_x(b['wx'], self.px))
                if dist > 80:
                    if b in self.bullets:
                        self.bullets.remove(b)

    def _player_hit(self):
        self.lives -= 1
        if self.lives <= 0:
            self.state = GameState.GAME_OVER
        else:
            self.invincible = 2.0
            self.py = 28
            self.vx = 0

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Stars background
        random.seed(42)
        for _ in range(20):
            sx = random.randint(0, 63)
            sy = random.randint(0, VIEW_HEIGHT - 1)
            self.display.set_pixel(sx, sy, (40, 40, 60))
        random.seed()

        # Draw terrain
        self._draw_terrain()

        # Draw humans
        for h in self.humans:
            if h['state'] == 'dead':
                continue
            pos = self._world_to_screen(h['wx'], h['wy'])
            if pos:
                sx, sy = pos
                color = Colors.GREEN if h['state'] == 'walking' else Colors.WHITE
                if h['state'] == 'falling':
                    color = Colors.YELLOW
                self.display.set_pixel(sx, sy - 1, color)
                self.display.set_pixel(sx, sy, color)

        # Draw enemies
        for e in self.enemies:
            if not e['alive']:
                continue
            pos = self._world_to_screen(e['wx'], e['wy'])
            if pos:
                sx, sy = pos
                self._draw_enemy(sx, sy, e['type'])

        # Draw player bullets (laser line)
        for b in self.bullets:
            pos = self._world_to_screen(b['wx'], b['wy'])
            if pos:
                sx, sy = pos
                self.display.set_pixel(sx, sy, Colors.WHITE)
                self.display.set_pixel(sx + b['dir'], sy, Colors.YELLOW)
                self.display.set_pixel(sx + b['dir'] * 2, sy, Colors.YELLOW)

        # Draw enemy bullets
        for b in self.enemy_bullets:
            pos = self._world_to_screen(b['wx'], b['wy'])
            if pos:
                sx, sy = pos
                self.display.set_pixel(sx, sy, Colors.RED)

        # Draw player (blink if invincible)
        if self.invincible <= 0 or int(self.invincible * 10) % 2 == 0:
            self._draw_player()

        # Draw scanner
        self._draw_scanner()

        # HUD
        self.display.draw_text_small(1, 1, f"{self.score}", Colors.WHITE)
        # Lives
        for i in range(self.lives - 1):
            self.display.set_pixel(50 - i * 4, 1, Colors.CYAN)
            self.display.set_pixel(49 - i * 4, 2, Colors.CYAN)
            self.display.set_pixel(51 - i * 4, 2, Colors.CYAN)
        # Smart bombs
        for i in range(self.smart_bombs):
            self.display.set_pixel(60 - i * 3, 1, Colors.ORANGE)
            self.display.set_pixel(59 - i * 3, 2, Colors.ORANGE)
            self.display.set_pixel(61 - i * 3, 2, Colors.ORANGE)

    def _draw_terrain(self):
        """Draw visible terrain as a mountain silhouette."""
        for sx in range(VIEW_WIDTH):
            wx = self._wrap_x(self.cam_x + sx)
            ty = self._terrain_y(wx)
            # Draw terrain from ty to VIEW_HEIGHT as dark green
            for sy in range(int(ty), VIEW_HEIGHT):
                self.display.set_pixel(sx, sy, (0, 60, 0))
            # Mountain top highlight
            self.display.set_pixel(sx, int(ty), (0, 100, 0))

    def _draw_player(self):
        """Draw the player ship."""
        sx = int(VIEW_WIDTH / 2 + self.facing * 0)  # Player at center-ish
        # Recalculate: player screen x from camera
        dx = self._world_dist_x(self.cam_x, self.px)
        sx = int(dx)
        sy = int(self.py)

        if self.facing == 1:
            # Pointing right: >=>
            self.display.set_pixel(sx - 2, sy, Colors.CYAN)
            self.display.set_pixel(sx - 1, sy - 1, Colors.CYAN)
            self.display.set_pixel(sx - 1, sy, Colors.WHITE)
            self.display.set_pixel(sx - 1, sy + 1, Colors.CYAN)
            self.display.set_pixel(sx, sy, Colors.WHITE)
            self.display.set_pixel(sx + 1, sy, Colors.CYAN)
            self.display.set_pixel(sx + 2, sy, Colors.YELLOW)
        else:
            # Pointing left: <=<
            self.display.set_pixel(sx + 2, sy, Colors.CYAN)
            self.display.set_pixel(sx + 1, sy - 1, Colors.CYAN)
            self.display.set_pixel(sx + 1, sy, Colors.WHITE)
            self.display.set_pixel(sx + 1, sy + 1, Colors.CYAN)
            self.display.set_pixel(sx, sy, Colors.WHITE)
            self.display.set_pixel(sx - 1, sy, Colors.CYAN)
            self.display.set_pixel(sx - 2, sy, Colors.YELLOW)

    def _draw_enemy(self, sx, sy, etype):
        """Draw an enemy sprite."""
        if etype == 'lander':
            c = Colors.GREEN
            self.display.set_pixel(sx, sy - 1, c)
            self.display.set_pixel(sx - 1, sy, c)
            self.display.set_pixel(sx, sy, c)
            self.display.set_pixel(sx + 1, sy, c)
            self.display.set_pixel(sx - 1, sy + 1, c)
            self.display.set_pixel(sx + 1, sy + 1, c)
        elif etype == 'mutant':
            c = Colors.PURPLE
            self.display.set_pixel(sx, sy - 1, c)
            self.display.set_pixel(sx - 1, sy, c)
            self.display.set_pixel(sx, sy, Colors.WHITE)
            self.display.set_pixel(sx + 1, sy, c)
            self.display.set_pixel(sx, sy + 1, c)
        elif etype == 'bomber':
            c = Colors.BLUE
            self.display.set_pixel(sx - 1, sy, c)
            self.display.set_pixel(sx, sy - 1, c)
            self.display.set_pixel(sx, sy, c)
            self.display.set_pixel(sx, sy + 1, c)
            self.display.set_pixel(sx + 1, sy, c)
        elif etype == 'pod':
            c = Colors.YELLOW
            self.display.set_pixel(sx, sy, c)
            self.display.set_pixel(sx + 1, sy, c)
            self.display.set_pixel(sx, sy + 1, c)
            self.display.set_pixel(sx + 1, sy + 1, c)
        elif etype == 'swarmer':
            self.display.set_pixel(sx, sy, Colors.YELLOW)

    def _draw_scanner(self):
        """Draw the radar/scanner at the bottom of the screen."""
        # Dark green background
        for sy in range(SCANNER_Y, 64):
            for sx in range(64):
                self.display.set_pixel(sx, sy, (0, 20, 0))
        # Separator line
        for sx in range(64):
            self.display.set_pixel(sx, SCANNER_Y - 1, (0, 60, 0))

        # Scale: 256px world -> 64px scanner
        scale = VIEW_WIDTH / WORLD_WIDTH  # 0.25

        # Terrain on scanner
        for sx in range(64):
            wx = int(sx / scale) % WORLD_WIDTH
            ty = self._terrain_y(wx)
            scanner_ty = SCANNER_Y + int((ty / VIEW_HEIGHT) * SCANNER_HEIGHT)
            for sy in range(scanner_ty, 64):
                self.display.set_pixel(sx, sy, (0, 40, 0))

        # Player on scanner
        psx = int((self.px * scale) % 64)
        self.display.set_pixel(psx, SCANNER_Y + 3, Colors.WHITE)

        # Humans on scanner
        for h in self.humans:
            if h['state'] == 'dead':
                continue
            hsx = int((h['wx'] * scale) % 64)
            self.display.set_pixel(hsx, SCANNER_Y + 4, Colors.GREEN)

        # Enemies on scanner
        for e in self.enemies:
            if not e['alive']:
                continue
            esx = int((e['wx'] * scale) % 64)
            self.display.set_pixel(esx, SCANNER_Y + 2, Colors.RED)

        # View window indicator
        cam_sx = int((self.cam_x * scale) % 64)
        view_w = max(1, int(VIEW_WIDTH * scale))
        for i in range(view_w):
            sx = (cam_sx + i) % 64
            self.display.set_pixel(sx, SCANNER_Y, (0, 80, 0))
