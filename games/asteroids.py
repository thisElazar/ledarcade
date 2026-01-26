"""
Asteroids - Classic space shooter
=================================
Destroy the asteroids before they destroy you!

Controls:
  Left/Right - Rotate ship
  Up         - Thrust forward
  Space      - Fire
"""

import random
import math
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


class Asteroids(Game):
    name = "ASTEROIDS"
    description = "Destroy the rocks!"
    
    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()
    
    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0
        self.lives = 3
        self.level = 1
        
        # Player ship
        self.ship_x = GRID_SIZE // 2
        self.ship_y = GRID_SIZE // 2
        self.ship_angle = -math.pi / 2  # Pointing up
        self.ship_dx = 0.0
        self.ship_dy = 0.0
        self.ship_visible = True
        self.invulnerable_timer = 2.0  # Start invulnerable
        
        # Bullets
        self.bullets = []
        self.fire_cooldown = 0
        
        # Asteroids
        self.asteroids = []
        self.spawn_asteroids(3 + self.level)
        
        # Particles (for explosions and thrust)
        self.particles = []
    
    def spawn_asteroids(self, count):
        """Spawn asteroids away from the player."""
        for _ in range(count):
            # Spawn away from center
            while True:
                x = random.uniform(0, GRID_SIZE)
                y = random.uniform(8, GRID_SIZE)  # Below score area
                
                # Make sure it's not too close to player
                dist = math.sqrt((x - self.ship_x)**2 + (y - self.ship_y)**2)
                if dist > 20:
                    break
            
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(10, 20)
            
            self.asteroids.append({
                'x': x,
                'y': y,
                'dx': math.cos(angle) * speed,
                'dy': math.sin(angle) * speed,
                'size': 2,  # Large asteroid (scaled down for 64x64)
                'rotation': random.uniform(0, 2 * math.pi),
                'rot_speed': random.uniform(-2, 2),
            })
    
    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return
        
        # Update invulnerability
        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= dt
        
        # Ship rotation
        rotation_speed = 4.0
        if input_state.left:
            self.ship_angle -= rotation_speed * dt
        if input_state.right:
            self.ship_angle += rotation_speed * dt
        
        # Ship thrust
        if input_state.up:
            thrust = 50.0
            self.ship_dx += math.cos(self.ship_angle) * thrust * dt
            self.ship_dy += math.sin(self.ship_angle) * thrust * dt
            
            # Thrust particles
            if random.random() < 0.5:
                self.particles.append({
                    'x': self.ship_x - math.cos(self.ship_angle) * 3,
                    'y': self.ship_y - math.sin(self.ship_angle) * 3,
                    'dx': -math.cos(self.ship_angle) * 30 + random.uniform(-10, 10),
                    'dy': -math.sin(self.ship_angle) * 30 + random.uniform(-10, 10),
                    'life': 0.3,
                    'color': Colors.ORANGE,
                })
        
        # Limit speed
        max_speed = 60.0
        speed = math.sqrt(self.ship_dx**2 + self.ship_dy**2)
        if speed > max_speed:
            self.ship_dx = self.ship_dx / speed * max_speed
            self.ship_dy = self.ship_dy / speed * max_speed
        
        # Move ship
        self.ship_x += self.ship_dx * dt
        self.ship_y += self.ship_dy * dt
        
        # Wrap around screen
        self.ship_x = self.ship_x % GRID_SIZE
        self.ship_y = 8 + (self.ship_y - 8) % (GRID_SIZE - 8)
        
        # Drag (space friction)
        drag = 0.98
        self.ship_dx *= drag
        self.ship_dy *= drag
        
        # Fire bullets
        self.fire_cooldown = max(0, self.fire_cooldown - dt)
        if input_state.action and self.fire_cooldown <= 0:
            self.fire_cooldown = 0.2
            
            bullet_speed = 80.0
            self.bullets.append({
                'x': self.ship_x + math.cos(self.ship_angle) * 4,
                'y': self.ship_y + math.sin(self.ship_angle) * 4,
                'dx': math.cos(self.ship_angle) * bullet_speed + self.ship_dx * 0.5,
                'dy': math.sin(self.ship_angle) * bullet_speed + self.ship_dy * 0.5,
                'life': 1.0,
            })
        
        # Update bullets
        for bullet in self.bullets[:]:
            bullet['x'] += bullet['dx'] * dt
            bullet['y'] += bullet['dy'] * dt
            bullet['life'] -= dt
            
            # Wrap
            bullet['x'] = bullet['x'] % GRID_SIZE
            bullet['y'] = 8 + (bullet['y'] - 8) % (GRID_SIZE - 8)
            
            if bullet['life'] <= 0:
                self.bullets.remove(bullet)
        
        # Update asteroids
        for asteroid in self.asteroids:
            asteroid['x'] += asteroid['dx'] * dt
            asteroid['y'] += asteroid['dy'] * dt
            asteroid['rotation'] += asteroid['rot_speed'] * dt
            
            # Wrap
            asteroid['x'] = asteroid['x'] % GRID_SIZE
            asteroid['y'] = 8 + (asteroid['y'] - 8) % (GRID_SIZE - 8)
        
        # Update particles
        for particle in self.particles[:]:
            particle['x'] += particle['dx'] * dt
            particle['y'] += particle['dy'] * dt
            particle['life'] -= dt
            
            if particle['life'] <= 0:
                self.particles.remove(particle)
        
        # Bullet-asteroid collisions
        for bullet in self.bullets[:]:
            for asteroid in self.asteroids[:]:
                radius = asteroid['size'] * 2 + 1
                dist = math.sqrt((bullet['x'] - asteroid['x'])**2 + 
                               (bullet['y'] - asteroid['y'])**2)
                
                if dist < radius:
                    # Hit!
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    
                    self.asteroids.remove(asteroid)
                    
                    # Score based on size
                    self.score += (4 - asteroid['size']) * 20
                    
                    # Split asteroid
                    if asteroid['size'] > 1:
                        for _ in range(2):
                            angle = random.uniform(0, 2 * math.pi)
                            speed = random.uniform(15, 30)
                            self.asteroids.append({
                                'x': asteroid['x'],
                                'y': asteroid['y'],
                                'dx': math.cos(angle) * speed,
                                'dy': math.sin(angle) * speed,
                                'size': asteroid['size'] - 1,
                                'rotation': random.uniform(0, 2 * math.pi),
                                'rot_speed': random.uniform(-3, 3),
                            })
                    
                    # Explosion particles
                    for _ in range(8):
                        angle = random.uniform(0, 2 * math.pi)
                        speed = random.uniform(20, 50)
                        self.particles.append({
                            'x': asteroid['x'],
                            'y': asteroid['y'],
                            'dx': math.cos(angle) * speed,
                            'dy': math.sin(angle) * speed,
                            'life': 0.4,
                            'color': Colors.WHITE,
                        })
                    
                    break
        
        # Ship-asteroid collisions (if not invulnerable)
        if self.invulnerable_timer <= 0:
            for asteroid in self.asteroids:
                radius = asteroid['size'] * 2 + 3
                dist = math.sqrt((self.ship_x - asteroid['x'])**2 + 
                               (self.ship_y - asteroid['y'])**2)
                
                if dist < radius:
                    self.lives -= 1
                    
                    # Explosion
                    for _ in range(15):
                        angle = random.uniform(0, 2 * math.pi)
                        speed = random.uniform(30, 60)
                        self.particles.append({
                            'x': self.ship_x,
                            'y': self.ship_y,
                            'dx': math.cos(angle) * speed,
                            'dy': math.sin(angle) * speed,
                            'life': 0.5,
                            'color': Colors.CYAN,
                        })
                    
                    if self.lives <= 0:
                        self.state = GameState.GAME_OVER
                    else:
                        # Respawn
                        self.ship_x = GRID_SIZE // 2
                        self.ship_y = GRID_SIZE // 2
                        self.ship_dx = 0
                        self.ship_dy = 0
                        self.ship_angle = -math.pi / 2
                        self.invulnerable_timer = 2.0
                    break
        
        # Check if all asteroids destroyed
        if not self.asteroids:
            self.level += 1
            self.spawn_asteroids(3 + self.level)
    
    def draw(self):
        self.display.clear(Colors.BLACK)
        
        # Draw score
        self.display.draw_text_small(1, 1, f"{self.score}", Colors.WHITE)
        
        # Draw lives
        for i in range(self.lives):
            lx = 55 + i * 4
            ly = 2
            # Tiny ship icon
            self.display.set_pixel(lx + 1, ly, Colors.CYAN)
            self.display.set_pixel(lx, ly + 2, Colors.CYAN)
            self.display.set_pixel(lx + 2, ly + 2, Colors.CYAN)
        
        # Draw separator
        self.display.draw_line(0, 7, 63, 7, Colors.DARK_GRAY)
        
        # Draw asteroids (scaled down for 64x64)
        for asteroid in self.asteroids:
            ax, ay = int(asteroid['x']), int(asteroid['y'])
            radius = asteroid['size'] * 1.5
            
            # Draw as rough polygon
            points = 6
            for i in range(points):
                a1 = asteroid['rotation'] + i * (2 * math.pi / points)
                a2 = asteroid['rotation'] + (i + 1) * (2 * math.pi / points)
                
                # Slightly irregular radius
                r1 = radius * (0.8 + 0.4 * ((i * 7) % 3) / 3)
                r2 = radius * (0.8 + 0.4 * (((i + 1) * 7) % 3) / 3)
                
                x1 = int(ax + math.cos(a1) * r1)
                y1 = int(ay + math.sin(a1) * r1)
                x2 = int(ax + math.cos(a2) * r2)
                y2 = int(ay + math.sin(a2) * r2)
                
                self.display.draw_line(x1, y1, x2, y2, Colors.WHITE)
        
        # Draw bullets
        for bullet in self.bullets:
            bx, by = int(bullet['x']), int(bullet['y'])
            self.display.set_pixel(bx, by, Colors.YELLOW)
        
        # Draw particles
        for particle in self.particles:
            px, py = int(particle['x']), int(particle['y'])
            brightness = int(255 * (particle['life'] / 0.5))
            color = particle.get('color', Colors.WHITE)
            dim_color = (
                min(255, color[0] * brightness // 255),
                min(255, color[1] * brightness // 255),
                min(255, color[2] * brightness // 255),
            )
            self.display.set_pixel(px, py, dim_color)
        
        # Draw ship (blink if invulnerable)
        if self.invulnerable_timer <= 0 or int(self.invulnerable_timer * 10) % 2 == 0:
            sx, sy = int(self.ship_x), int(self.ship_y)
            
            # Ship as triangle
            nose_x = sx + int(math.cos(self.ship_angle) * 4)
            nose_y = sy + int(math.sin(self.ship_angle) * 4)
            
            left_x = sx + int(math.cos(self.ship_angle + 2.5) * 3)
            left_y = sy + int(math.sin(self.ship_angle + 2.5) * 3)
            
            right_x = sx + int(math.cos(self.ship_angle - 2.5) * 3)
            right_y = sy + int(math.sin(self.ship_angle - 2.5) * 3)
            
            self.display.draw_line(nose_x, nose_y, left_x, left_y, Colors.CYAN)
            self.display.draw_line(nose_x, nose_y, right_x, right_y, Colors.CYAN)
            self.display.draw_line(left_x, left_y, right_x, right_y, Colors.CYAN)
