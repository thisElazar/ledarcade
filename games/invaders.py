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
        self.player_y = GRID_SIZE - 6
        
        # Player bullet
        self.bullet_x = -1
        self.bullet_y = -1
        self.bullet_active = False
        
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
    
    def setup_enemies(self):
        """Create the enemy grid."""
        self.enemies = []
        
        # 5 columns, 4 rows of enemies (smaller spacing for smaller aliens)
        for row in range(4):
            for col in range(8):
                enemy = {
                    'x': 4 + col * 7,
                    'y': 10 + row * 5,
                    'type': row,  # Different enemy types
                    'frame': 0,   # Animation frame
                }
                self.enemies.append(enemy)
        
        # Speed up based on level
        self.enemy_move_delay = max(0.15, 0.5 - (self.level - 1) * 0.08)
    
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
        
        # Player movement
        player_speed = 50
        if input_state.left:
            self.player_x = max(3, self.player_x - player_speed * dt)
        if input_state.right:
            self.player_x = min(GRID_SIZE - 6, self.player_x + player_speed * dt)
        
        # Fire bullet (can fire again once bullet is past halfway up screen)
        if input_state.action and (not self.bullet_active or self.bullet_y < GRID_SIZE // 2):
            self.bullet_x = int(self.player_x) + 2
            self.bullet_y = self.player_y - 1
            self.bullet_active = True
        
        # Update player bullet
        if self.bullet_active:
            self.bullet_y -= 80 * dt
            if self.bullet_y < 8:
                self.bullet_active = False
        
        # Update explosion particles
        for particle in self.explosion_particles[:]:
            particle['life'] -= dt
            particle['x'] += particle['dx'] * dt
            particle['y'] += particle['dy'] * dt
            if particle['life'] <= 0:
                self.explosion_particles.remove(particle)
        
        # Enemy movement
        self.enemy_move_timer += dt
        if self.enemy_move_timer >= self.enemy_move_delay:
            self.enemy_move_timer = 0
            self.move_enemies()
        
        # Enemy shooting
        if random.random() < 0.02 * len(self.enemies) * dt * 10:
            self.enemy_shoot()
        
        # Update enemy bullets
        for bullet in self.enemy_bullets[:]:
            bullet['y'] += 40 * dt
            
            # Hit player
            if (abs(bullet['x'] - self.player_x - 2) < 3 and
                abs(bullet['y'] - self.player_y) < 3):
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
        
        # Check bullet-enemy collisions
        if self.bullet_active:
            bullet_ix = int(self.bullet_x)
            bullet_iy = int(self.bullet_y)
            
            for enemy in self.enemies[:]:
                if (abs(bullet_ix - enemy['x'] - 1) < 2 and
                    abs(bullet_iy - enemy['y'] - 1) < 2):
                    
                    # Hit!
                    self.enemies.remove(enemy)
                    self.bullet_active = False
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
                    
                    # Speed up remaining enemies
                    self.enemy_move_delay = max(0.08, self.enemy_move_delay - 0.01)
                    break
            
            # Check bullet-shield collision
            for shield in self.shields[:]:
                if abs(bullet_ix - shield['x']) < 1 and abs(bullet_iy - shield['y']) < 1:
                    shield['health'] -= 1
                    if shield['health'] <= 0:
                        self.shields.remove(shield)
                    self.bullet_active = False
                    break
        
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
            if self.enemy_dir > 0 and enemy['x'] >= GRID_SIZE - 8:
                should_drop = True
                break
            if self.enemy_dir < 0 and enemy['x'] <= 2:
                should_drop = True
                break
        
        if should_drop:
            self.enemy_dir *= -1
            for enemy in self.enemies:
                enemy['y'] += 3
        else:
            for enemy in self.enemies:
                enemy['x'] += self.enemy_dir * 2
        
        # Animate enemies
        for enemy in self.enemies:
            enemy['frame'] = (enemy['frame'] + 1) % 2
    
    def enemy_shoot(self):
        """Random enemy fires a bullet."""
        if not self.enemies:
            return
        
        # Pick random enemy from bottom row in each column
        columns = {}
        for enemy in self.enemies:
            col = enemy['x'] // 7
            if col not in columns or enemy['y'] > columns[col]['y']:
                columns[col] = enemy
        
        if columns:
            shooter = random.choice(list(columns.values()))
            self.enemy_bullets.append({
                'x': shooter['x'] + 2,
                'y': shooter['y'] + 4,
            })
    
    def player_hit(self):
        """Player was hit by enemy bullet."""
        self.lives -= 1
        self.player_hit_timer = 1.0
        
        if self.lives <= 0:
            self.state = GameState.GAME_OVER
    
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
        
        # Draw player (only if not in hit cooldown or flashing)
        if self.player_hit_timer <= 0 or int(self.player_hit_timer * 10) % 2 == 0:
            px = int(self.player_x)
            py = self.player_y
            
            # Ship shape
            self.display.set_pixel(px + 2, py, Colors.GREEN)
            self.display.set_pixel(px + 1, py + 1, Colors.GREEN)
            self.display.set_pixel(px + 2, py + 1, Colors.GREEN)
            self.display.set_pixel(px + 3, py + 1, Colors.GREEN)
            self.display.set_pixel(px, py + 2, Colors.GREEN)
            self.display.set_pixel(px + 1, py + 2, Colors.GREEN)
            self.display.set_pixel(px + 2, py + 2, Colors.GREEN)
            self.display.set_pixel(px + 3, py + 2, Colors.GREEN)
            self.display.set_pixel(px + 4, py + 2, Colors.GREEN)
        
        # Draw player bullet
        if self.bullet_active:
            bx, by = int(self.bullet_x), int(self.bullet_y)
            self.display.set_pixel(bx, by, Colors.WHITE)
            self.display.set_pixel(bx, by + 1, Colors.YELLOW)
        
        # Draw explosion particles
        for particle in self.explosion_particles:
            px, py = int(particle['x']), int(particle['y'])
            brightness = int(255 * (particle['life'] / 0.3))
            self.display.set_pixel(px, py, (brightness, brightness // 2, 0))
