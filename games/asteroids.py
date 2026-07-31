"""
Asteroids - Classic space shooter
=================================
Destroy the asteroids before they destroy you!

Controls:
  Left/Right - Rotate ship
  Up         - Thrust forward
  Down       - Hyperspace (risky teleport)
  Space      - Fire
"""

import random
import math
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


class Asteroids(Game):
    name = "ASTROIDS"
    description = "Destroy the rocks!"
    category = "arcade"
    GUIDE = {
        'desc': 'Rotate and thrust your ship, shoot asteroids that split large-medium-small — the small ones score the most (20/50/100). Down triggers hyperspace: a random teleport with a death risk that grows with rock count. Extra ship every 10,000 points. Screen wraps. Inspired by the 1979 vector arcade classic.',
    }

    # Authentic 1979 scoring — small rocks are worth the most
    ROCK_SCORES = {3: 20, 2: 50, 1: 100}

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
        self.hyperspace_timer = 0.0  # Ship is dematerialized while > 0
        self.hyperspace_death = False
        self.next_extra_life = 10000  # Extra ship every 10,000 points
        
        # Bullets
        self.bullets = []
        self.fire_cooldown = 0
        
        # Asteroids
        self.asteroids = []
        self.spawn_asteroids(3 + self.level)
        
        # Particles (for explosions and thrust)
        self.particles = []

        # UFO (like original 1979 Asteroids)
        self.ufo = None  # Active UFO dict or None
        self.ufo_spawn_timer = 10.0  # Time until next UFO spawn
        self.ufo_bullets = []  # UFO's bullets
    
    def spawn_asteroids(self, count):
        """Spawn asteroids away from the player. Speed increases with level."""
        # Base speed range increases with level (like original 1979 Asteroids)
        base_speed_min = 6 + (self.level - 1) * 1.5
        base_speed_max = 12 + (self.level - 1) * 2.5
        # Cap maximum speed to keep game playable
        base_speed_min = min(base_speed_min, 25)
        base_speed_max = min(base_speed_max, 45)

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
            speed = random.uniform(base_speed_min, base_speed_max)

            self.asteroids.append({
                'x': x,
                'y': y,
                'dx': math.cos(angle) * speed,
                'dy': math.sin(angle) * speed,
                'size': 3,  # Large asteroid (splits 3 -> 2 -> 1)
                'rotation': random.uniform(0, 2 * math.pi),
                'rot_speed': random.uniform(-2, 2),
            })

    def split_asteroid(self, asteroid, impact_angle):
        """Destroy a rock: score it, split it into two children, spawn debris."""
        self.asteroids.remove(asteroid)
        self.score += self.ROCK_SCORES[asteroid['size']]

        # Split asteroid - children deflect sideways from the impact path
        if asteroid['size'] > 1:
            # Child asteroids are faster, and scale with level
            child_speed_min = 9 + (self.level - 1) * 2
            child_speed_max = 18 + (self.level - 1) * 3
            child_speed_min = min(child_speed_min, 35)
            child_speed_max = min(child_speed_max, 55)
            # Two children deflect to opposite sides (60-120° off impact path)
            for side in (-1, 1):
                spread = random.uniform(math.pi / 3, 2 * math.pi / 3)
                angle = impact_angle + side * spread
                speed = random.uniform(child_speed_min, child_speed_max)
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

    def destroy_ship(self):
        """Lose a ship: explosion, then respawn or game over."""
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

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return
        
        # Update invulnerability
        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= dt

        # Hyperspace re-entry (ship is dematerialized while timer runs)
        if self.hyperspace_timer > 0:
            self.hyperspace_timer -= dt
            if self.hyperspace_timer <= 0:
                self.hyperspace_timer = 0.0
                if self.hyperspace_death:
                    self.hyperspace_death = False
                    self.destroy_ship()

        # Ship rotation
        rotation_speed = 4.0
        if input_state.left:
            self.ship_angle -= rotation_speed * dt
        if input_state.right:
            self.ship_angle += rotation_speed * dt
        
        # Ship thrust (forward)
        if input_state.up and self.hyperspace_timer <= 0:
            thrust = 50.0
            self.ship_dx += math.cos(self.ship_angle) * thrust * dt
            self.ship_dy += math.sin(self.ship_angle) * thrust * dt

            # Thrust particles
            if random.random() < 0.5:
                self.particles.append({
                    'x': self.ship_x - math.cos(self.ship_angle) * 2,
                    'y': self.ship_y - math.sin(self.ship_angle) * 2,
                    'dx': -math.cos(self.ship_angle) * 30 + random.uniform(-10, 10),
                    'dy': -math.sin(self.ship_angle) * 30 + random.uniform(-10, 10),
                    'life': 0.3,
                    'color': Colors.ORANGE,
                })

        # Hyperspace (down) — random teleport, like the original.
        # Death chance rises with the number of rocks on screen.
        if input_state.down_pressed and self.hyperspace_timer <= 0:
            # Departure sparkle at the old position
            for _ in range(6):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(10, 25)
                self.particles.append({
                    'x': self.ship_x,
                    'y': self.ship_y,
                    'dx': math.cos(angle) * speed,
                    'dy': math.sin(angle) * speed,
                    'life': 0.3,
                    'color': Colors.CYAN,
                })
            self.ship_x = random.uniform(4, GRID_SIZE - 4)
            self.ship_y = random.uniform(12, GRID_SIZE - 4)
            self.ship_dx = 0.0
            self.ship_dy = 0.0
            self.hyperspace_timer = 0.6
            self.hyperspace_death = (
                random.random() < min(0.05 + 0.02 * len(self.asteroids), 0.3))
        
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
        
        # Light drag, frame-rate independent — the original coasts a long way
        drag = 0.66 ** dt
        self.ship_dx *= drag
        self.ship_dy *= drag
        
        # Fire bullets
        self.fire_cooldown = max(0, self.fire_cooldown - dt)
        if (input_state.action_l or input_state.action_r) and self.fire_cooldown <= 0 \
                and self.hyperspace_timer <= 0:
            self.fire_cooldown = 0.2
            
            bullet_speed = 80.0
            self.bullets.append({
                'x': self.ship_x + math.cos(self.ship_angle) * 3,
                'y': self.ship_y + math.sin(self.ship_angle) * 3,
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

                    # Children deflect sideways from the bullet path
                    bullet_angle = math.atan2(bullet['dy'], bullet['dx'])
                    self.split_asteroid(asteroid, bullet_angle)
                    break
        
        # Ship-asteroid collisions (if not invulnerable or in hyperspace)
        if self.invulnerable_timer <= 0 and self.hyperspace_timer <= 0:
            for asteroid in self.asteroids:
                radius = asteroid['size'] * 2 + 3
                dist = math.sqrt((self.ship_x - asteroid['x'])**2 +
                               (self.ship_y - asteroid['y'])**2)

                if dist < radius:
                    # Ramming a rock splits and scores it too (like the original)
                    impact_angle = math.atan2(asteroid['dy'], asteroid['dx'])
                    self.split_asteroid(asteroid, impact_angle)
                    self.destroy_ship()
                    break
        
        # UFO logic (like original 1979 Asteroids)
        if self.ufo is None:
            self.ufo_spawn_timer -= dt
            if self.ufo_spawn_timer <= 0:
                # Spawn UFO - small saucer probability rises with score
                # (like the original); mostly small above ~4000 points
                is_small = random.random() < min(0.2 + self.score / 8000.0, 0.85)
                # UFO enters from left or right edge
                from_left = random.random() < 0.5
                self.ufo = {
                    'x': 0 if from_left else GRID_SIZE - 1,
                    'y': random.uniform(12, GRID_SIZE - 8),
                    'dx': 25 if from_left else -25,  # Moves horizontally
                    'dy': 0,
                    'small': is_small,
                    'fire_timer': 1.5,  # Time until next shot
                    'direction_timer': 2.0,  # Time until direction change
                }
                self.ufo_spawn_timer = random.uniform(15, 25)  # Next UFO spawn time
        else:
            # Move UFO
            self.ufo['x'] += self.ufo['dx'] * dt
            self.ufo['y'] += self.ufo['dy'] * dt

            # Periodic vertical direction change
            self.ufo['direction_timer'] -= dt
            if self.ufo['direction_timer'] <= 0:
                self.ufo['dy'] = random.uniform(-15, 15)
                self.ufo['direction_timer'] = random.uniform(1.0, 2.5)

            # Keep UFO in play area vertically
            if self.ufo['y'] < 10:
                self.ufo['y'] = 10
                self.ufo['dy'] = abs(self.ufo['dy'])
            elif self.ufo['y'] > GRID_SIZE - 4:
                self.ufo['y'] = GRID_SIZE - 4
                self.ufo['dy'] = -abs(self.ufo['dy'])

            # UFO exits screen
            if self.ufo['x'] < -5 or self.ufo['x'] > GRID_SIZE + 5:
                self.ufo = None
            else:
                # UFO fires at player
                self.ufo['fire_timer'] -= dt
                if self.ufo['fire_timer'] <= 0:
                    # Small UFO aims more accurately (like original)
                    if self.ufo['small']:
                        # Aim error tightens with score — near-perfect above ~4000
                        aim_error = max(0.05, 0.35 - self.score * (0.30 / 4000.0))
                        aim_angle = math.atan2(self.ship_y - self.ufo['y'],
                                               self.ship_x - self.ufo['x'])
                        aim_angle += random.uniform(-aim_error, aim_error)
                    else:
                        # Large UFO shoots more randomly
                        aim_angle = math.atan2(self.ship_y - self.ufo['y'],
                                               self.ship_x - self.ufo['x'])
                        aim_angle += random.uniform(-0.8, 0.8)

                    bullet_speed = 50.0
                    self.ufo_bullets.append({
                        'x': self.ufo['x'],
                        'y': self.ufo['y'],
                        'dx': math.cos(aim_angle) * bullet_speed,
                        'dy': math.sin(aim_angle) * bullet_speed,
                        'life': 1.5,
                    })
                    self.ufo['fire_timer'] = 1.2 if self.ufo['small'] else 1.8

        # Update UFO bullets
        for bullet in self.ufo_bullets[:]:
            bullet['x'] += bullet['dx'] * dt
            bullet['y'] += bullet['dy'] * dt
            bullet['life'] -= dt

            # Wrap
            bullet['x'] = bullet['x'] % GRID_SIZE
            bullet['y'] = 8 + (bullet['y'] - 8) % (GRID_SIZE - 8)

            if bullet['life'] <= 0:
                self.ufo_bullets.remove(bullet)

        # Player bullet hits UFO
        if self.ufo:
            ufo_radius = 2 if self.ufo['small'] else 3
            for bullet in self.bullets[:]:
                dist = math.sqrt((bullet['x'] - self.ufo['x'])**2 +
                                 (bullet['y'] - self.ufo['y'])**2)
                if dist < ufo_radius + 1:
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    # Score: small UFO worth more (like original)
                    self.score += 1000 if self.ufo['small'] else 200
                    # Explosion
                    for _ in range(10):
                        angle = random.uniform(0, 2 * math.pi)
                        speed = random.uniform(25, 45)
                        self.particles.append({
                            'x': self.ufo['x'],
                            'y': self.ufo['y'],
                            'dx': math.cos(angle) * speed,
                            'dy': math.sin(angle) * speed,
                            'life': 0.4,
                            'color': Colors.RED,
                        })
                    self.ufo = None
                    break

        # UFO bullet hits player (if not invulnerable or in hyperspace)
        if self.invulnerable_timer <= 0 and self.hyperspace_timer <= 0:
            for bullet in self.ufo_bullets[:]:
                dist = math.sqrt((bullet['x'] - self.ship_x)**2 +
                                 (bullet['y'] - self.ship_y)**2)
                if dist < 3:
                    self.ufo_bullets.remove(bullet)
                    self.destroy_ship()
                    break

        # Extra ship every 10,000 points (like the original)
        if self.score >= self.next_extra_life:
            self.lives += 1
            self.next_extra_life += 10000

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

        # Draw UFO
        if self.ufo:
            ux, uy = int(self.ufo['x']), int(self.ufo['y'])
            if self.ufo['small']:
                # Small UFO - simple ellipse shape
                self.display.draw_line(ux - 2, uy, ux + 2, uy, Colors.RED)
                self.display.set_pixel(ux, uy - 1, Colors.RED)
            else:
                # Large UFO - classic saucer shape
                self.display.draw_line(ux - 3, uy, ux + 3, uy, Colors.RED)
                self.display.draw_line(ux - 2, uy - 1, ux + 2, uy - 1, Colors.RED)
                self.display.set_pixel(ux, uy + 1, Colors.RED)

        # Draw UFO bullets
        for bullet in self.ufo_bullets:
            bx, by = int(bullet['x']), int(bullet['y'])
            self.display.set_pixel(bx, by, Colors.RED)
        
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
        
        # Draw ship (hidden during hyperspace, blink if invulnerable)
        if self.hyperspace_timer <= 0 and \
                (self.invulnerable_timer <= 0 or int(self.invulnerable_timer * 10) % 2 == 0):
            sx, sy = int(self.ship_x), int(self.ship_y)

            # Ship as smaller triangle
            nose_x = sx + int(math.cos(self.ship_angle) * 3)
            nose_y = sy + int(math.sin(self.ship_angle) * 3)

            left_x = sx + int(math.cos(self.ship_angle + 2.5) * 2)
            left_y = sy + int(math.sin(self.ship_angle + 2.5) * 2)

            right_x = sx + int(math.cos(self.ship_angle - 2.5) * 2)
            right_y = sy + int(math.sin(self.ship_angle - 2.5) * 2)

            self.display.draw_line(nose_x, nose_y, left_x, left_y, Colors.CYAN)
            self.display.draw_line(nose_x, nose_y, right_x, right_y, Colors.CYAN)
            self.display.draw_line(left_x, left_y, right_x, right_y, Colors.CYAN)
