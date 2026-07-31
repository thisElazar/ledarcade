"""
Galaga - Classic Space Shooter
==============================
Destroy enemy formations! Watch out for diving attacks.

Controls:
  Left/Right - Move ship
  Space      - Fire
"""

import random
import math
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


class Galaga(Game):
    name = "GALAXA"
    description = "Shoot the aliens!"
    category = "arcade"
    GUIDE = {
        'desc': 'Fixed-position shooter. Enemies swoop in along entrance arcs, form up, then dive — and dodged divers loop back into formation. Bosses take two hits and can trap your ship in a tractor beam; shoot the captor while it dives to free the ship and fight as a dual fighter. Every 4th level from level 3 is a no-fire bonus challenge stage.',
    }

    # Player constants
    PLAYER_Y = 58
    PLAYER_SPEED = 34.0
    MAX_BULLETS = 2

    # In-flight (diver/entrant) kill scores by type
    DIVE_SCORES = {'bee': 100, 'butterfly': 160, 'boss': 400}

    # Enemy constants
    FORMATION_TOP = 10
    FORMATION_COLS = 8
    FORMATION_ROWS = 4
    ENEMY_SPACING_X = 7
    ENEMY_SPACING_Y = 6

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0
        self.lives = 3
        self.level = 1

        # Player state
        self.player_x = 32.0

        # Bullets (player): list of {x, y}
        self.bullets = []

        # Enemy bullets
        self.enemy_bullets = []

        # Formation movement
        self.formation_offset_x = 0.0
        self.formation_dir = 1
        self.formation_speed = 8.0
        self.formation_time = 0

        # Dive timing
        self.dive_interval = 2.0  # Seconds between dive attacks

        # Captured ship state
        self.has_dual_ship = False

        # Formation slots, divers, entrance choreography, challenge state
        self._setup_wave()

        # Animation
        self.anim_frame = 0
        self.anim_timer = 0

        # Respawn invincibility
        self.invincible = 0

    def setup_formation(self):
        """Set up enemy formation."""
        self.formation = {}
        start_x = (GRID_SIZE - (self.FORMATION_COLS - 1) * self.ENEMY_SPACING_X) // 2

        for row in range(self.FORMATION_ROWS):
            for col in range(self.FORMATION_COLS):
                # Different enemy types per row
                if row == 0:
                    enemy_type = 'boss'  # Top row - bosses (can capture)
                elif row == 1:
                    enemy_type = 'butterfly'
                else:
                    enemy_type = 'bee'

                self.formation[(col, row)] = {
                    'type': enemy_type,
                    'alive': False,  # Slots fill as enemies fly their entrance
                    'hp': 2 if enemy_type == 'boss' else 1,
                    'captured': False,  # Boss holding a captured fighter
                    'base_x': start_x + col * self.ENEMY_SPACING_X,
                    'base_y': self.FORMATION_TOP + row * self.ENEMY_SPACING_Y,
                }

    def _setup_wave(self):
        """Set up formation slots and entrance choreography for this level."""
        self.challenge = self.level >= 3 and (self.level - 3) % 4 == 0
        self.setup_formation()
        self.divers = []
        self.enemy_bullets = []
        self.entrants = []
        self.spawn_queue = []
        self.entry_timer = 0.0
        self.dive_timer = 0

        if self.challenge:
            # Challenging stage: 5 flights of 8 fly through and exit — no
            # formation, no enemy fire. 1000 per wiped flight, 10000 perfect.
            flight_types = ['bee', 'butterfly', 'bee', 'butterfly', 'boss']
            self.flight_remaining = [8] * 5
            self.flight_kills = [0] * 5
            for f in range(5):
                side = 1 if f % 2 == 0 else -1
                for i in range(8):
                    self.spawn_queue.append({
                        'delay': f * 3.0 + i * 0.25,
                        'side': side, 'type': flight_types[f],
                        'col': None, 'row': None, 'flight': f,
                    })
        else:
            # Entrance: 4 mirrored streams of 8 (one per formation row), each
            # enemy peeling off the arc to its own slot
            for row in range(self.FORMATION_ROWS):
                side = 1 if row % 2 == 0 else -1
                for i, col in enumerate(range(self.FORMATION_COLS)):
                    self.spawn_queue.append({
                        'delay': row * 2.4 + i * 0.22,
                        'side': side, 'type': self.formation[(col, row)]['type'],
                        'col': col, 'row': row, 'flight': None,
                    })

    def _entrance_pos(self, side: int, t: float) -> tuple:
        """Point along the mirrored entrance arc (side=+1 right, -1 left):
        swoop in from the top edge, then half-loop back up mid-screen."""
        if t < 0.4:
            u = t / 0.4
            return 32 + side * (34 - 26 * u), -4.0 + 44 * u
        u = (t - 0.4) / 0.6
        cx, cy, r = 32 + side * 8, 30.0, 10.0
        a = math.pi * (0.5 + u)
        return cx + side * r * math.cos(a), cy + r * math.sin(a)

    def _update_entrants(self, dt: float):
        """Spawn queued enemies and fly them along their entrance arcs."""
        if self.spawn_queue:
            self.entry_timer += dt
            while self.spawn_queue and self.spawn_queue[0]['delay'] <= self.entry_timer:
                spec = self.spawn_queue.pop(0)
                x, y = self._entrance_pos(spec['side'], 0.0)
                self.entrants.append({
                    'x': x, 'y': y, 't': 0.0,
                    'side': spec['side'], 'type': spec['type'],
                    'col': spec['col'], 'row': spec['row'],
                    'flight': spec['flight'], 'phase': 'arc',
                    'hp': 2 if spec['type'] == 'boss' else 1,
                })

        for ent in self.entrants[:]:
            if ent['phase'] == 'arc':
                ent['t'] += dt * 0.55
                ent['x'], ent['y'] = self._entrance_pos(ent['side'], min(ent['t'], 1.0))
                if ent['t'] >= 1.0:
                    ent['phase'] = 'exit' if ent['flight'] is not None else 'to_slot'
            elif ent['phase'] == 'to_slot':
                tx, ty = self.get_formation_pos(ent['col'], ent['row'])
                dx, dy = tx - ent['x'], ty - ent['y']
                dist = math.hypot(dx, dy)
                if dist < 2:
                    slot = self.formation[(ent['col'], ent['row'])]
                    slot['alive'] = True
                    slot['hp'] = ent['hp']
                    self.entrants.remove(ent)
                else:
                    step = 45 * dt
                    ent['x'] += dx / dist * step
                    ent['y'] += dy / dist * step
            else:  # 'exit' — challenge flights climb off the top
                ent['x'] += -ent['side'] * 30 * dt
                ent['y'] -= 35 * dt
                if ent['y'] < -4:
                    self.entrants.remove(ent)
                    self._flight_resolved(ent['flight'], killed=False)

    def _flight_resolved(self, flight, killed: bool):
        """Track challenge-flight results; bonus for wiping a full flight."""
        if flight is None:
            return
        self.flight_remaining[flight] -= 1
        if killed:
            self.flight_kills[flight] += 1
        if self.flight_remaining[flight] == 0 and self.flight_kills[flight] == 8:
            self.score += 1000

    def get_formation_pos(self, col: int, row: int) -> tuple:
        """Get current screen position of formation slot."""
        enemy = self.formation.get((col, row))
        if enemy:
            x = enemy['base_x'] + self.formation_offset_x
            y = enemy['base_y']
            return x, y
        return None, None

    def count_alive(self) -> int:
        """Count living enemies."""
        return sum(1 for e in self.formation.values() if e['alive'])

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        # Animation
        self.anim_timer += dt
        if self.anim_timer >= 0.15:
            self.anim_timer = 0
            self.anim_frame = (self.anim_frame + 1) % 2

        # Invincibility timer
        if self.invincible > 0:
            self.invincible -= dt

        # Player movement
        if input_state.left:
            self.player_x -= self.PLAYER_SPEED * dt
        if input_state.right:
            self.player_x += self.PLAYER_SPEED * dt
        # Dual fighter sits at +6, so keep both ships on the field
        max_x = 55 if self.has_dual_ship else 60
        self.player_x = max(3, min(max_x, self.player_x))

        # Firing: one shot per button press, classic two-shot limit
        if (input_state.action_l or input_state.action_r) and len(self.bullets) < self.MAX_BULLETS:
            self.bullets.append({'x': self.player_x, 'y': self.PLAYER_Y - 2})
            if self.has_dual_ship:
                self.bullets.append({'x': self.player_x + 6, 'y': self.PLAYER_Y - 2})

        # Update bullets
        for bullet in self.bullets:
            bullet['y'] -= 80 * dt
        self.bullets = [b for b in self.bullets if b['y'] > 0]

        # Update enemy bullets (speed scales with level, capped for playability)
        enemy_bullet_speed = min(80, 40 + self.level * 6)  # Faster bullets, capped at 80
        for bullet in self.enemy_bullets:
            bullet['y'] += enemy_bullet_speed * dt
        self.enemy_bullets = [b for b in self.enemy_bullets if b['y'] < GRID_SIZE]

        # Formation movement (gentle sway that speeds up with level)
        self.formation_time += dt
        oscillation_speed = 1.5 + self.level * 0.15  # Faster oscillation at higher levels
        oscillation_amplitude = 6 + min(self.level, 5)  # Wider sway at higher levels (max +5)
        self.formation_offset_x = math.sin(self.formation_time * oscillation_speed) * oscillation_amplitude

        # Entrance choreography / challenge flights
        self._update_entrants(dt)

        # Dive attack timing (waits until the entrance is complete)
        if not self.spawn_queue and not self.entrants and not self.challenge:
            self.dive_timer += dt
            if self.dive_timer >= self.dive_interval and self.count_alive() > 0:
                self.dive_timer = 0
                self.start_dive_attack()

        # Update divers
        self.update_divers(dt)

        # Collision: bullets vs formation
        for bullet in self.bullets[:]:
            bx, by = bullet['x'], bullet['y']

            # Check formation enemies
            for (col, row), enemy in self.formation.items():
                if not enemy['alive']:
                    continue
                ex, ey = self.get_formation_pos(col, row)
                if abs(bx - ex) < 4 and abs(by - ey) < 4:
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    enemy['hp'] -= 1
                    if enemy['hp'] <= 0:
                        enemy['alive'] = False
                        enemy['captured'] = False
                        self.score += 50 if enemy['type'] == 'bee' else 80 if enemy['type'] == 'butterfly' else 150
                    break
            if bullet not in self.bullets:
                continue

            # Check divers
            for diver in self.divers[:]:
                if abs(bx - diver['x']) < 4 and abs(by - diver['y']) < 4:
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    diver['hp'] -= 1
                    if diver['hp'] <= 0:
                        self.divers.remove(diver)
                        self.score += self.DIVE_SCORES.get(diver['type'], 100)
                        if diver.get('has_captured'):
                            # Freed the captured fighter — dual ship!
                            self.has_dual_ship = True
                    break
            if bullet not in self.bullets:
                continue

            # Check entering enemies (entrance arcs / challenge flights)
            for ent in self.entrants[:]:
                if abs(bx - ent['x']) < 4 and abs(by - ent['y']) < 4:
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    ent['hp'] -= 1
                    if ent['hp'] <= 0:
                        self.entrants.remove(ent)
                        self.score += self.DIVE_SCORES.get(ent['type'], 100)
                        self._flight_resolved(ent['flight'], killed=True)
                    break

        # Collision: enemy bullets vs player (dual covers both ships)
        if self.invincible <= 0:
            for bullet in self.enemy_bullets[:]:
                bdx = bullet['x'] - self.player_x
                in_x = (-3 < bdx < 8) if self.has_dual_ship else abs(bdx) < 3
                if in_x and abs(bullet['y'] - self.PLAYER_Y) < 3:
                    self.player_hit()
                    self.enemy_bullets.remove(bullet)
                    break

        # Collision: divers vs player
        if self.invincible <= 0:
            for diver in self.divers[:]:
                if abs(diver['x'] - self.player_x) < 4 and abs(diver['y'] - self.PLAYER_Y) < 4:
                    self.player_hit()
                    self.divers.remove(diver)
                    break

        # Check level complete (challenge stages end when all flights resolve)
        if (self.count_alive() == 0 and not self.divers and
                not self.entrants and not self.spawn_queue):
            if self.challenge and all(k == 8 for k in self.flight_kills):
                self.score += 10000  # Perfect challenge stage
            self.next_level()

    def start_dive_attack(self):
        """Start a dive attack with enemies scaling by level."""
        alive_enemies = [(col, row, e) for (col, row), e in self.formation.items() if e['alive']]
        if not alive_enemies:
            return

        # More simultaneous divers at higher levels (1-2 at level 1, up to 2-5 at higher levels)
        min_divers = 1 + min(self.level // 3, 2)  # 1 -> 2 -> 3 as levels increase
        max_divers = 2 + min(self.level // 2, 3)  # 2 -> 3 -> 4 -> 5 as levels increase
        num_divers = min(len(alive_enemies), random.randint(min_divers, max_divers))
        chosen = random.sample(alive_enemies, num_divers)

        for col, row, enemy in chosen:
            ex, ey = self.get_formation_pos(col, row)
            enemy['alive'] = False  # Leaves formation while diving

            # Create dive path toward player then loop back
            # Diver speed scales with level, capped for playability
            diver_speed = min(75, 30 + self.level * 6)  # Faster dive speed, capped at 75
            diver = {
                'x': ex,
                'y': ey,
                'col': col,  # Remembers its slot so it can rejoin
                'row': row,
                'type': enemy['type'],
                'phase': 'dive',  # dive, beam, attack, return
                'speed': diver_speed,
                'target_x': self.player_x,
                'hp': enemy['hp'],
                'has_captured': enemy['captured'],
                'shoot_timer': random.uniform(0.3, 1.2 - min(self.level * 0.05, 0.5)),  # Shoot more often at higher levels
            }
            # Bosses may stop mid-dive and fire a tractor beam
            if (enemy['type'] == 'boss' and not diver['has_captured']
                    and not self.has_dual_ship and random.random() < 0.4):
                diver['will_beam'] = True
            enemy['captured'] = False
            self.divers.append(diver)

    def update_divers(self, dt: float):
        """Update diving enemies."""
        for diver in self.divers[:]:
            speed = diver['speed']

            if diver['phase'] == 'dive':
                # Move toward player's x while descending
                dx = diver['target_x'] - diver['x']
                if abs(dx) > 2:
                    diver['x'] += math.copysign(speed * 0.7 * dt, dx)
                diver['y'] += speed * dt

                # Shoot occasionally (more frequently at higher levels)
                diver['shoot_timer'] -= dt
                if diver['shoot_timer'] <= 0:
                    self.enemy_bullets.append({'x': diver['x'], 'y': diver['y'] + 3})
                    # Shorter intervals between shots at higher levels
                    min_interval = max(0.4, 0.8 - self.level * 0.04)
                    max_interval = max(0.8, 1.5 - self.level * 0.06)
                    diver['shoot_timer'] = random.uniform(min_interval, max_interval)

                # Bosses may stop mid-dive and fire the tractor beam
                if diver.get('will_beam') and diver['y'] >= 36:
                    diver['phase'] = 'beam'
                    diver['beam_timer'] = 1.5
                # Switch to attack phase near player level
                elif diver['y'] >= self.PLAYER_Y - 10:
                    diver['phase'] = 'attack'

            elif diver['phase'] == 'beam':
                # Hover and sweep an expanding tractor cone below
                diver['beam_timer'] -= dt
                spread = 1.0 - max(diver['beam_timer'], 0) / 1.5
                half_w = 2 + 8 * spread
                if (self.invincible <= 0 and spread > 0.3 and
                        abs(self.player_x - diver['x']) < half_w):
                    # Caught in the beam: fighter is captured, boss carries it
                    self.player_hit()
                    if self.state == GameState.PLAYING:
                        diver['has_captured'] = True
                    diver['beam_timer'] = 0
                if diver['beam_timer'] <= 0:
                    diver['will_beam'] = False
                    diver['phase'] = 'return'

            elif diver['phase'] == 'attack':
                # Swoop across
                diver['y'] += speed * 0.3 * dt
                diver['x'] += speed * dt * (1 if diver['x'] < 32 else -1)

                # Exit screen or return
                if diver['y'] > GRID_SIZE + 5:
                    diver['phase'] = 'return'
                    diver['y'] = -5

            elif diver['phase'] == 'return':
                # Fly back to this enemy's own slot and rejoin the formation
                tx, ty = self.get_formation_pos(diver['col'], diver['row'])
                dx = tx - diver['x']
                dy = ty - diver['y']
                dist = math.hypot(dx, dy)
                if dist < 2:
                    slot = self.formation[(diver['col'], diver['row'])]
                    slot['alive'] = True
                    slot['hp'] = diver['hp']
                    slot['captured'] = diver.get('has_captured', False)
                    self.divers.remove(diver)
                else:
                    step = speed * 0.8 * dt
                    diver['x'] += dx / dist * step
                    diver['y'] += dy / dist * step

    def player_hit(self):
        """Handle player getting hit."""
        self.lives -= 1
        self.has_dual_ship = False

        if self.lives <= 0:
            self.state = GameState.GAME_OVER
        else:
            self.invincible = 2.0  # 2 seconds invincibility
            self.player_x = 32

    def next_level(self):
        """Advance to next level."""
        self.level += 1
        self.dive_interval = max(1.0, 2.0 - self.level * 0.1)
        self._setup_wave()

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Stars background
        random.seed(42)
        for _ in range(30):
            sx = random.randint(0, 63)
            sy = random.randint(0, 63)
            self.display.set_pixel(sx, sy, (60, 60, 80))
        random.seed()

        # Draw formation enemies
        for (col, row), enemy in self.formation.items():
            if enemy['alive']:
                x, y = self.get_formation_pos(col, row)
                self.draw_enemy(int(x), int(y), enemy['type'], enemy['hp'])
                if enemy['captured']:
                    self._draw_captured_ship(int(x), int(y) - 3)

        # Draw divers (and any active tractor beam)
        for diver in self.divers:
            if diver['phase'] == 'beam':
                self._draw_beam(diver)
            self.draw_enemy(int(diver['x']), int(diver['y']), diver['type'], diver['hp'])
            if diver.get('has_captured'):
                self._draw_captured_ship(int(diver['x']), int(diver['y']) - 3)

        # Draw entering enemies
        for ent in self.entrants:
            self.draw_enemy(int(ent['x']), int(ent['y']), ent['type'], ent['hp'])

        # Draw bullets
        for bullet in self.bullets:
            self.display.set_pixel(int(bullet['x']), int(bullet['y']), Colors.WHITE)
            self.display.set_pixel(int(bullet['x']), int(bullet['y']) + 1, Colors.YELLOW)

        # Draw enemy bullets
        for bullet in self.enemy_bullets:
            self.display.set_pixel(int(bullet['x']), int(bullet['y']), Colors.RED)

        # Draw player (blink if invincible)
        if self.invincible <= 0 or int(self.invincible * 10) % 2 == 0:
            self.draw_player(int(self.player_x), self.PLAYER_Y)
            if self.has_dual_ship:
                self.draw_player(int(self.player_x) + 6, self.PLAYER_Y)

        # HUD
        self.display.draw_text_small(1, 1, f"{self.score}", Colors.WHITE)
        # Lives
        for i in range(self.lives - 1):
            self.display.set_pixel(60 - i * 4, 2, Colors.CYAN)
            self.display.set_pixel(59 - i * 4, 3, Colors.CYAN)
            self.display.set_pixel(61 - i * 4, 3, Colors.CYAN)

    def draw_player(self, x: int, y: int):
        """Draw player ship."""
        # Triangle ship
        self.display.set_pixel(x, y - 2, Colors.CYAN)
        self.display.set_pixel(x - 1, y - 1, Colors.CYAN)
        self.display.set_pixel(x, y - 1, Colors.CYAN)
        self.display.set_pixel(x + 1, y - 1, Colors.CYAN)
        self.display.set_pixel(x - 2, y, Colors.CYAN)
        self.display.set_pixel(x - 1, y, Colors.WHITE)
        self.display.set_pixel(x, y, Colors.WHITE)
        self.display.set_pixel(x + 1, y, Colors.WHITE)
        self.display.set_pixel(x + 2, y, Colors.CYAN)

    def _draw_beam(self, diver):
        """Expanding cyan/yellow tractor cone below a beaming boss."""
        bx = int(diver['x'])
        top = int(diver['y']) + 2
        spread = 1.0 - max(diver['beam_timer'], 0) / 1.5
        for sy in range(top, self.PLAYER_Y + 1):
            frac = (sy - top) / max(1, self.PLAYER_Y - top)
            half_w = int((2 + 8 * spread) * frac)
            color = Colors.CYAN if (sy + self.anim_frame) % 2 == 0 else Colors.YELLOW
            self.display.set_pixel(bx - half_w, sy, color)
            self.display.set_pixel(bx + half_w, sy, color)

    def _draw_captured_ship(self, x: int, y: int):
        """Small red fighter carried by a boss."""
        self.display.set_pixel(x, y - 1, Colors.RED)
        self.display.set_pixel(x - 1, y, Colors.RED)
        self.display.set_pixel(x, y, Colors.RED)
        self.display.set_pixel(x + 1, y, Colors.RED)

    def draw_enemy(self, x: int, y: int, enemy_type: str, hp: int = 2):
        """Draw an enemy."""
        if enemy_type == 'boss':
            # Green boss with wings (turns blue after the first hit)
            color = Colors.GREEN if hp >= 2 else Colors.BLUE
            self.display.set_pixel(x, y - 1, color)
            self.display.set_pixel(x - 1, y, color)
            self.display.set_pixel(x, y, Colors.WHITE)
            self.display.set_pixel(x + 1, y, color)
            if self.anim_frame == 0:
                self.display.set_pixel(x - 2, y + 1, color)
                self.display.set_pixel(x + 2, y + 1, color)
            else:
                self.display.set_pixel(x - 2, y - 1, color)
                self.display.set_pixel(x + 2, y - 1, color)
            self.display.set_pixel(x, y + 1, color)

        elif enemy_type == 'butterfly':
            # Red butterfly
            color = Colors.RED
            self.display.set_pixel(x, y - 1, color)
            self.display.set_pixel(x - 1, y, color)
            self.display.set_pixel(x, y, color)
            self.display.set_pixel(x + 1, y, color)
            if self.anim_frame == 0:
                self.display.set_pixel(x - 2, y, color)
                self.display.set_pixel(x + 2, y, color)
            else:
                self.display.set_pixel(x - 1, y + 1, color)
                self.display.set_pixel(x + 1, y + 1, color)

        else:  # bee
            # Yellow bee
            color = Colors.YELLOW
            self.display.set_pixel(x, y - 1, color)
            self.display.set_pixel(x - 1, y, color)
            self.display.set_pixel(x, y, color)
            self.display.set_pixel(x + 1, y, color)
            self.display.set_pixel(x, y + 1, color)

    def draw_game_over(self):
        self.display.clear(Colors.BLACK)
        self.display.draw_text_small(8, 20, "GAME OVER", Colors.RED)
        self.display.draw_text_small(10, 32, f"SCORE:{self.score}", Colors.WHITE)
        self.display.draw_text_small(4, 50, "BTN:RETRY", Colors.GRAY)
