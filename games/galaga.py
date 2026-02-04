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
    name = "GALAGA"
    description = "Shoot the aliens!"
    category = "arcade"

    # Player constants
    PLAYER_Y = 58
    PLAYER_SPEED = 50.0
    FIRE_COOLDOWN = 0.25
    MAX_BULLETS = 3

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
        self.fire_cooldown = 0

        # Bullets (player): list of {x, y}
        self.bullets = []

        # Enemy bullets
        self.enemy_bullets = []

        # Enemies in formation: dict of (col, row) -> {type, alive, x, y}
        self.formation = {}
        self.setup_formation()

        # Formation movement
        self.formation_offset_x = 0.0
        self.formation_dir = 1
        self.formation_speed = 8.0
        self.formation_time = 0

        # Diving enemies: list of {x, y, type, angle, speed, path_index, path}
        self.divers = []
        self.dive_timer = 0
        self.dive_interval = 2.0  # Seconds between dive attacks

        # Captured ship state
        self.captured_ship = None
        self.has_dual_ship = False

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
                    'alive': True,
                    'base_x': start_x + col * self.ENEMY_SPACING_X,
                    'base_y': self.FORMATION_TOP + row * self.ENEMY_SPACING_Y,
                }

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
        self.player_x = max(3, min(60, self.player_x))

        # Firing
        self.fire_cooldown -= dt
        if (input_state.action_l_held or input_state.action_r_held) or input_state.action_r_held and self.fire_cooldown <= 0 and len(self.bullets) < self.MAX_BULLETS:
            self.bullets.append({'x': self.player_x, 'y': self.PLAYER_Y - 2})
            if self.has_dual_ship:
                self.bullets.append({'x': self.player_x + 6, 'y': self.PLAYER_Y - 2})
            self.fire_cooldown = self.FIRE_COOLDOWN

        # Update bullets
        for bullet in self.bullets:
            bullet['y'] -= 120 * dt
        self.bullets = [b for b in self.bullets if b['y'] > 0]

        # Update enemy bullets (speed scales with level, capped for playability)
        enemy_bullet_speed = min(120, 60 + self.level * 8)  # Faster bullets, capped at 120
        for bullet in self.enemy_bullets:
            bullet['y'] += enemy_bullet_speed * dt
        self.enemy_bullets = [b for b in self.enemy_bullets if b['y'] < GRID_SIZE]

        # Formation movement (gentle sway that speeds up with level)
        self.formation_time += dt
        oscillation_speed = 1.5 + self.level * 0.15  # Faster oscillation at higher levels
        oscillation_amplitude = 6 + min(self.level, 5)  # Wider sway at higher levels (max +5)
        self.formation_offset_x = math.sin(self.formation_time * oscillation_speed) * oscillation_amplitude

        # Dive attack timing
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
                    enemy['alive'] = False
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    self.score += 50 if enemy['type'] == 'bee' else 80 if enemy['type'] == 'butterfly' else 150
                    break

            # Check divers
            for diver in self.divers[:]:
                if abs(bx - diver['x']) < 4 and abs(by - diver['y']) < 4:
                    self.divers.remove(diver)
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    self.score += 100
                    break

        # Collision: enemy bullets vs player
        if self.invincible <= 0:
            for bullet in self.enemy_bullets[:]:
                if abs(bullet['x'] - self.player_x) < 3 and abs(bullet['y'] - self.PLAYER_Y) < 3:
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

        # Check level complete
        if self.count_alive() == 0 and len(self.divers) == 0:
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
            enemy['alive'] = False  # Remove from formation

            # Create dive path toward player then loop back
            # Diver speed scales with level, capped for playability
            diver_speed = min(110, 45 + self.level * 8)  # Faster dive speed, capped at 110
            self.divers.append({
                'x': ex,
                'y': ey,
                'type': enemy['type'],
                'phase': 'dive',  # dive, attack, return
                'speed': diver_speed,
                'target_x': self.player_x,
                'shoot_timer': random.uniform(0.3, 1.2 - min(self.level * 0.05, 0.5)),  # Shoot more often at higher levels
            })

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

                # Switch to attack phase near player level
                if diver['y'] >= self.PLAYER_Y - 10:
                    diver['phase'] = 'attack'

            elif diver['phase'] == 'attack':
                # Swoop across
                diver['y'] += speed * 0.3 * dt
                diver['x'] += speed * dt * (1 if diver['x'] < 32 else -1)

                # Exit screen or return
                if diver['y'] > GRID_SIZE + 5:
                    diver['phase'] = 'return'
                    diver['y'] = -5

            elif diver['phase'] == 'return':
                # Return to formation area
                diver['y'] += speed * 0.8 * dt
                target_x = 32 + random.uniform(-10, 10)
                dx = target_x - diver['x']
                diver['x'] += math.copysign(min(abs(dx), speed * dt), dx)

                # Rejoin formation or disappear if at top
                if diver['y'] >= self.FORMATION_TOP:
                    self.divers.remove(diver)

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
        self.setup_formation()
        self.divers = []
        self.enemy_bullets = []

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
                self.draw_enemy(int(x), int(y), enemy['type'])

        # Draw divers
        for diver in self.divers:
            self.draw_enemy(int(diver['x']), int(diver['y']), diver['type'])

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

    def draw_enemy(self, x: int, y: int, enemy_type: str):
        """Draw an enemy."""
        if enemy_type == 'boss':
            # Green boss with wings
            color = Colors.GREEN
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
