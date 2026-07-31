"""
Space Invaders - Classic arcade shooter
=======================================
Defend Earth from the alien invasion!

Controls:
  Left/Right - Move ship
  Space      - Fire
"""

import random
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


class Invaders(Game):
    name = "INVADERS"
    description = "Defend Earth!"
    category = "arcade"
    GUIDE = {
        'desc': 'Shoot rows of aliens before they reach the bottom. One shot on screen at a time; the rack marches faster as it thins, and invaders grind through your shields. Saucer bonus depends on how many shots you have fired. Inspired by the 1978 classic.',
    }

    # Authentic saucer score table, indexed by player shot count mod 15
    # (from the 8080 ROM's fixed lookup — the "300 on the 23rd shot" trick)
    SAUCER_SCORES = [100, 50, 50, 100, 150, 100, 100, 50, 300, 100, 100, 100, 50, 150, 100]

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()
    
    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0
        self.lives = 3
        self.level = 1
        
        # Player
        self.player_x = GRID_SIZE // 2
        self.player_y = GRID_SIZE - 5  # Slightly higher for smaller ship

        # Player bullet (classic rule: one shot on screen at a time)
        self.bullets = []
        self.shot_count = 0  # Total shots fired; drives saucer score and direction
        
        # Enemies
        self.enemies = []
        self.enemy_bullets = []
        self.enemy_dir = 1  # 1 = right, -1 = left
        self.enemy_move_timer = 0
        self.enemy_move_delay = 0.5
        self.enemy_drop = False
        
        # Setup enemies
        self.setup_enemies()
        
        # Shields/barriers
        self.shields = []
        self.setup_shields()
        
        # Effects
        self.explosion_particles = []
        self.player_hit_timer = 0

        # UFO/Mystery ship
        self.ufo = None  # {'x': float, 'dir': 1 or -1}
        self.ufo_timer = 25.0  # Fixed saucer timer (authentic ~25s cadence)
    
    def setup_enemies(self):
        """Create the enemy grid."""
        self.enemies = []

        # 4 rows x 8 cols of enemies (tighter spacing)
        # Rack starts lower on later waves (authentic pressure ramp)
        start_y = 10 + min(self.level - 1, 4) * 3
        for row in range(4):
            for col in range(8):
                enemy = {
                    'x': 6 + col * 6,  # Closer horizontal spacing
                    'y': start_y + row * 4,  # Closer vertical spacing
                    'type': row,  # Different enemy types
                    'frame': 0,   # Animation frame
                }
                self.enemies.append(enemy)

        # March delay is emergent: recomputed each update from remaining count
        self.initial_enemy_count = len(self.enemies)
        self.enemy_move_delay = self._rack_delay()

    def _rack_delay(self):
        """March delay proportional to remaining invaders — the rack speeds up
        as it thins (emergent, like the original's draw-loop timing), with a
        mild per-level ramp."""
        level_factor = max(0.4, 1.0 - (self.level - 1) * 0.1)
        return 0.03 + 0.45 * level_factor * len(self.enemies) / max(1, self.initial_enemy_count)
    
    def setup_shields(self):
        """Create defensive shields."""
        self.shields = []
        
        # 3 shields spread across bottom
        shield_positions = [10, 28, 46]
        
        for sx in shield_positions:
            for dy in range(4):
                for dx in range(8):
                    # Create shield shape (arch)
                    if dy == 0 and (dx < 2 or dx > 5):
                        continue
                    if dy == 3 and (dx > 2 and dx < 5):
                        continue
                    
                    self.shields.append({
                        'x': sx + dx,
                        'y': GRID_SIZE - 14 + dy,
                        'health': 3,
                    })
    
    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return
        
        # Player hit cooldown
        if self.player_hit_timer > 0:
            self.player_hit_timer -= dt
            return

        # Mystery saucer: fixed ~25s timer, only while at least 8 invaders remain
        self.ufo_timer -= dt
        if self.ufo_timer <= 0:
            self.ufo_timer = 25.0
            if self.ufo is None and len(self.enemies) >= 8:
                # Direction comes from shot-count parity (authentic rule)
                direction = 1 if self.shot_count % 2 == 0 else -1
                start_x = -5 if direction == 1 else GRID_SIZE + 5
                # UFO speed increases with level (25 base, +3 per level, max 50)
                ufo_speed = min(50, 25 + (self.level - 1) * 3)
                self.ufo = {'x': float(start_x), 'dir': direction, 'speed': ufo_speed}

        # Update UFO position
        if self.ufo is not None:
            ufo_speed = self.ufo.get('speed', 25)
            self.ufo['x'] += self.ufo['dir'] * ufo_speed * dt
            # Check if UFO went off screen
            if self.ufo['dir'] == 1 and self.ufo['x'] > GRID_SIZE + 5:
                self.ufo = None
            elif self.ufo['dir'] == -1 and self.ufo['x'] < -5:
                self.ufo = None

        # Player movement (adjusted for smaller ship)
        player_speed = 34
        if input_state.left:
            self.player_x = max(2, self.player_x - player_speed * dt)
        if input_state.right:
            self.player_x = min(GRID_SIZE - 4, self.player_x + player_speed * dt)

        # Fire bullet (classic rule: only one player shot on screen at a time)
        if (input_state.action_l or input_state.action_r) and not self.bullets:
            self.bullets.append({
                'x': int(self.player_x) + 1,  # Center of smaller ship
                'y': self.player_y - 1,
            })
            self.shot_count += 1

        # Update player bullet (keep prev_y so fast bullets get swept hit
        # tests; off-screen removal happens after the collision checks)
        for bullet in self.bullets[:]:
            bullet['prev_y'] = bullet['y']
            bullet['y'] -= 90 * dt
        
        # Update explosion particles
        for particle in self.explosion_particles[:]:
            particle['life'] -= dt
            particle['x'] += particle['dx'] * dt
            particle['y'] += particle['dy'] * dt
            if particle['life'] <= 0:
                self.explosion_particles.remove(particle)
        
        # Enemy movement (emergent speedup: delay tracks remaining rack size)
        self.enemy_move_delay = self._rack_delay()
        self.enemy_move_timer += dt
        if self.enemy_move_timer >= self.enemy_move_delay:
            self.enemy_move_timer = 0
            self.move_enemies()

        # Enemy shooting: rate stays steady as the rack shrinks (the danger
        # never drops off), capped at 3 bullets in flight
        if len(self.enemy_bullets) < 3 and random.random() < (1.0 + 0.15 * (self.level - 1)) * dt:
            self.enemy_shoot()
        
        # Update enemy bullets
        for bullet in self.enemy_bullets[:]:
            bullet['y'] += 28 * dt
            
            # Hit player (adjusted for smaller ship - 3 wide, 2 tall)
            if (abs(bullet['x'] - self.player_x - 1) < 2 and
                abs(bullet['y'] - self.player_y) < 2):
                self.enemy_bullets.remove(bullet)
                self.player_hit()
                continue
            
            # Hit shield
            for shield in self.shields[:]:
                if abs(bullet['x'] - shield['x']) < 1 and abs(bullet['y'] - shield['y']) < 1:
                    shield['health'] -= 1
                    if shield['health'] <= 0:
                        self.shields.remove(shield)
                    if bullet in self.enemy_bullets:
                        self.enemy_bullets.remove(bullet)
                    break
            
            # Off screen
            if bullet['y'] > GRID_SIZE:
                if bullet in self.enemy_bullets:
                    self.enemy_bullets.remove(bullet)

        # Player bullet vs enemy bullets — both are destroyed
        for eb in self.enemy_bullets[:]:
            for pb in self.bullets[:]:
                if abs(pb['x'] - eb['x']) < 2 and abs(pb['y'] - eb['y']) < 3:
                    self.enemy_bullets.remove(eb)
                    self.bullets.remove(pb)
                    break

        # Check bullet-enemy collisions (multiple bullets)
        for bullet in self.bullets[:]:
            bullet_ix = int(bullet['x'])
            bullet_iy = int(bullet['y'])
            # Swept test: bullet moves >=3px/frame, so check the whole span
            # it travelled this frame [bullet_iy, prev_iy] against hit windows
            prev_iy = int(bullet.get('prev_y', bullet['y']))
            bullet_removed = False

            for enemy in self.enemies[:]:
                if (abs(bullet_ix - enemy['x'] - 1) < 2 and
                    bullet_iy < enemy['y'] + 3 and prev_iy > enemy['y'] - 1):

                    # Hit!
                    self.enemies.remove(enemy)
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    bullet_removed = True
                    self.score += (4 - enemy['type']) * 10 + 10

                    # Create explosion
                    for _ in range(5):
                        self.explosion_particles.append({
                            'x': enemy['x'] + 2,
                            'y': enemy['y'] + 2,
                            'dx': random.uniform(-30, 30),
                            'dy': random.uniform(-30, 30),
                            'life': 0.3,
                        })
                    break

            # Check bullet-UFO collision (if bullet not already removed)
            if not bullet_removed and bullet in self.bullets and self.ufo is not None:
                ufo_x = int(self.ufo['x'])
                ufo_y = 9  # UFO flies at y=9 (just below the separator line)
                # UFO is 5 pixels wide
                if (abs(bullet_ix - ufo_x - 2) < 3 and
                        bullet_iy < ufo_y + 2 and prev_iy > ufo_y - 2):
                    # Hit UFO!
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    bullet_removed = True
                    # Authentic saucer score table, indexed by shots fired
                    bonus = self.SAUCER_SCORES[self.shot_count % 15]
                    self.score += bonus

                    # Create explosion at UFO position
                    for _ in range(8):
                        self.explosion_particles.append({
                            'x': ufo_x + 2,
                            'y': ufo_y,
                            'dx': random.uniform(-40, 40),
                            'dy': random.uniform(-40, 40),
                            'life': 0.4,
                        })

                    self.ufo = None

            # Check bullet-shield collision (if bullet not already removed)
            if not bullet_removed and bullet in self.bullets:
                for shield in self.shields[:]:
                    if abs(bullet_ix - shield['x']) < 1 and abs(bullet_iy - shield['y']) < 1:
                        shield['health'] -= 1
                        if shield['health'] <= 0:
                            self.shields.remove(shield)
                        if bullet in self.bullets:
                            self.bullets.remove(bullet)
                        break

            # Off the top — removed after collisions so the final swept
            # segment past the UFO row still counts
            if bullet in self.bullets and bullet['y'] < 8:
                self.bullets.remove(bullet)

        # Check win condition
        if not self.enemies:
            self.level += 1
            self.setup_enemies()
            self.setup_shields()
        
        # Check if enemies reached bottom
        for enemy in self.enemies:
            if enemy['y'] >= GRID_SIZE - 10:
                self.state = GameState.GAME_OVER
                break
    
    def move_enemies(self):
        """Move all enemies."""
        # Check if we need to change direction
        should_drop = False

        for enemy in self.enemies:
            if self.enemy_dir > 0 and enemy['x'] >= GRID_SIZE - 6:
                should_drop = True
                break
            if self.enemy_dir < 0 and enemy['x'] <= 3:
                should_drop = True
                break
        
        if should_drop:
            self.enemy_dir *= -1
            for enemy in self.enemies:
                enemy['y'] += 3
        else:
            for enemy in self.enemies:
                enemy['x'] += self.enemy_dir * 2

        # Invaders grind away any shield pixels they overlap while marching
        if self.shields:
            for enemy in self.enemies:
                ex, ey = enemy['x'], enemy['y']
                self.shields = [s for s in self.shields
                                if not (ex <= s['x'] <= ex + 2 and ey <= s['y'] <= ey + 2)]

        # Animate enemies
        for enemy in self.enemies:
            enemy['frame'] = (enemy['frame'] + 1) % 2
    
    def enemy_shoot(self):
        """An enemy fires. One of the (up to 3) shots in flight is the
        'rolling' shot, which always comes from the column nearest the player."""
        if not self.enemies:
            return

        # Bottom-most enemy in each column
        columns = {}
        for enemy in self.enemies:
            col = enemy['x'] // 6  # Updated for tighter spacing
            if col not in columns or enemy['y'] > columns[col]['y']:
                columns[col] = enemy

        if not columns:
            return

        if not any(b.get('kind') == 'rolling' for b in self.enemy_bullets):
            # Rolling shot: aimed, from the column nearest the player
            shooter = min(columns.values(),
                          key=lambda e: abs(e['x'] + 2 - (self.player_x + 1)))
            kind = 'rolling'
        else:
            shooter = random.choice(list(columns.values()))
            kind = 'plunger'
        self.enemy_bullets.append({
            'x': shooter['x'] + 2,
            'y': shooter['y'] + 4,
            'kind': kind,
        })
    
    def player_hit(self):
        """Player was hit by enemy bullet."""
        self.lives -= 1
        self.player_hit_timer = 1.0

        if self.lives <= 0:
            self.state = GameState.GAME_OVER
        else:
            # Respawn under a shield for protection
            self.player_x = self._find_safe_spawn_x()

    def _find_safe_spawn_x(self):
        """Find x position to spawn under a shield. Prefer middle, then any remaining."""
        if not self.shields:
            # No shields left, spawn in center
            return GRID_SIZE // 2

        # Shield positions (centers): 10+4=14, 28+4=32, 46+4=50
        # Check for shields at each position
        shield_centers = [14, 32, 50]  # left, middle, right

        # Count shields near each center position
        shield_counts = {14: 0, 32: 0, 50: 0}
        for shield in self.shields:
            for center in shield_centers:
                if abs(shield['x'] - center) < 6:
                    shield_counts[center] += 1
                    break

        # Prefer middle (32), then check others
        if shield_counts[32] > 0:
            return 32 - 1  # Center player under middle shield
        elif shield_counts[14] > 0:
            return 14 - 1  # Under left shield
        elif shield_counts[50] > 0:
            return 50 - 1  # Under right shield
        else:
            # Fallback to center
            return GRID_SIZE // 2
    
    def draw(self):
        self.display.clear(Colors.BLACK)
        
        # Draw score and lives
        self.display.draw_text_small(1, 1, f"{self.score}", Colors.WHITE)
        
        # Draw lives
        for i in range(self.lives):
            self.display.set_pixel(55 + i * 3, 2, Colors.GREEN)
            self.display.set_pixel(55 + i * 3, 3, Colors.GREEN)
        
        # Draw separator
        self.display.draw_line(0, 7, 63, 7, Colors.DARK_GRAY)

        # Draw UFO/Mystery ship
        if self.ufo is not None:
            ux = int(self.ufo['x'])
            uy = 9  # Just below the separator
            # Draw UFO shape (5 wide, 2 tall) - classic saucer shape
            # Only draw pixels that are on screen
            if 0 <= ux + 2 < GRID_SIZE:
                self.display.set_pixel(ux + 2, uy, Colors.RED)      # Top center
            if 0 <= ux + 1 < GRID_SIZE:
                self.display.set_pixel(ux + 1, uy + 1, Colors.MAGENTA)  # Bottom row
            if 0 <= ux + 2 < GRID_SIZE:
                self.display.set_pixel(ux + 2, uy + 1, Colors.RED)
            if 0 <= ux + 3 < GRID_SIZE:
                self.display.set_pixel(ux + 3, uy + 1, Colors.MAGENTA)
            if 0 <= ux < GRID_SIZE:
                self.display.set_pixel(ux, uy + 1, Colors.MAGENTA)
            if 0 <= ux + 4 < GRID_SIZE:
                self.display.set_pixel(ux + 4, uy + 1, Colors.MAGENTA)

        # Draw shields
        for shield in self.shields:
            shade = 64 + shield['health'] * 60
            self.display.set_pixel(shield['x'], shield['y'], (0, shade, 0))
        
        # Draw enemies
        enemy_colors = [Colors.WHITE, Colors.CYAN, Colors.YELLOW, Colors.GREEN]
        
        for enemy in self.enemies:
            color = enemy_colors[enemy['type']]
            ex, ey = enemy['x'], enemy['y']

            # Smaller 3x3 enemy sprite (changes with frame)
            if enemy['frame'] == 0:
                # Frame 1
                self.display.set_pixel(ex, ey, color)
                self.display.set_pixel(ex + 2, ey, color)
                self.display.set_pixel(ex, ey + 1, color)
                self.display.set_pixel(ex + 1, ey + 1, color)
                self.display.set_pixel(ex + 2, ey + 1, color)
                self.display.set_pixel(ex + 1, ey + 2, color)
            else:
                # Frame 2
                self.display.set_pixel(ex + 1, ey, color)
                self.display.set_pixel(ex, ey + 1, color)
                self.display.set_pixel(ex + 1, ey + 1, color)
                self.display.set_pixel(ex + 2, ey + 1, color)
                self.display.set_pixel(ex, ey + 2, color)
                self.display.set_pixel(ex + 2, ey + 2, color)
        
        # Draw enemy bullets
        for bullet in self.enemy_bullets:
            self.display.set_pixel(int(bullet['x']), int(bullet['y']), Colors.RED)
            self.display.set_pixel(int(bullet['x']), int(bullet['y']) + 1, Colors.RED)
        
        # Draw player (smaller ship - only if not in hit cooldown or flashing)
        if self.player_hit_timer <= 0 or int(self.player_hit_timer * 10) % 2 == 0:
            px = int(self.player_x)
            py = self.player_y

            # Smaller ship shape (3 wide, 2 tall)
            self.display.set_pixel(px + 1, py, Colors.GREEN)      # Top center
            self.display.set_pixel(px, py + 1, Colors.GREEN)      # Bottom left
            self.display.set_pixel(px + 1, py + 1, Colors.GREEN)  # Bottom center
            self.display.set_pixel(px + 2, py + 1, Colors.GREEN)  # Bottom right

        # Draw player bullets (multiple, larger and visible)
        for bullet in self.bullets:
            bx, by = int(bullet['x']), int(bullet['y'])
            self.display.set_pixel(bx, by, Colors.WHITE)
            self.display.set_pixel(bx, by + 1, Colors.WHITE)
            self.display.set_pixel(bx, by + 2, Colors.YELLOW)
            self.display.set_pixel(bx, by + 3, Colors.ORANGE)
        
        # Draw explosion particles
        for particle in self.explosion_particles:
            px, py = int(particle['x']), int(particle['y'])
            brightness = min(255, int(255 * (particle['life'] / 0.3)))
            self.display.set_pixel(px, py, (brightness, brightness // 2, 0))
