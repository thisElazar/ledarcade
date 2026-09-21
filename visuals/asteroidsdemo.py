"""
Asteroids Demo - AI Attract Mode
================================
Asteroids plays itself using simple AI for idle screen demos.
The AI navigates, shoots asteroids, and dodges threats.

AI Strategy:
- Hold position like a turret: drifting through a 64-pixel field is what kills
- A rock is a threat only if its path crosses the ship; shoot the one that
  arrives soonest, leading the shot
- With nothing incoming, shoot the UFO, then whichever rock is quickest to hit
- If something cannot be shot in time, thrust out of its path; if even that
  is too late, hyperspace
"""

import math
from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

# Import the actual game
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.asteroids import Asteroids


BULLET_SPEED = 80.0   # the game's
TURN_SPEED = 4.0      # the game's, rad/s
LOOKAHEAD = 2.0       # seconds of rock paths worth worrying about
CLEARANCE = 2.0       # px beyond the hit radius that still counts as a threat
PANIC = 0.3           # seconds to impact at which only hyperspace is left


class AsteroidsDemo(Visual):
    name = "ASTROIDS"
    description = "AI plays Asteroids"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = Asteroids(self.display)
        self.game.reset()
        self.decision_timer = 0.0
        self.decision_interval = 0.05  # Recalculate every 50ms
        self.ai_rotate = 0  # -1 left, 0 none, 1 right
        self.ai_thrust = False
        self.ai_shoot = False
        self.ai_hyperspace = False
        self.restart_timer = 0.0

    def handle_input(self, input_state):
        # Demo doesn't respond to input (auto-plays)
        return False

    def update(self, dt):
        self.time += dt

        # If game over, restart after a pause
        if self.game.state == GameState.GAME_OVER:
            self.restart_timer += dt
            if self.restart_timer > 3.0:
                self.game.reset()
                self.restart_timer = 0.0
            return

        # Make AI decisions periodically
        self.decision_timer += dt
        if self.decision_timer >= self.decision_interval:
            self.decision_timer = 0.0
            self._decide_action()

        # Create input state with AI's chosen actions
        ai_input = InputState()
        if self.ai_rotate < 0:
            ai_input.left = True
        elif self.ai_rotate > 0:
            ai_input.right = True
        if self.ai_thrust:
            ai_input.up = True
        if self.ai_shoot:
            ai_input.action_l = True
        if self.ai_hyperspace:
            ai_input.down_pressed = True
            self.ai_hyperspace = False

        self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()

        # Overlay "DEMO" text
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)

    def _decide_action(self):
        """AI decision-making for Asteroids."""
        game = self.game
        self.ai_rotate = 0
        self.ai_thrust = False
        self.ai_shoot = False
        if game.hyperspace_timer > 0:
            return

        # Everything that can hit the ship: (body, hit radius, can be shot)
        bodies = [(a, a['size'] * 2 + 3, True) for a in game.asteroids]
        bodies += [(b, 3, False) for b in game.ufo_bullets]
        if game.ufo:
            bodies.append((game.ufo, 4, True))

        threats = []
        for body, radius, shootable in bodies:
            t_hit = self._time_to_hit(body, radius + CLEARANCE)
            if t_hit is not None:
                threats.append((t_hit, body, radius, shootable))
        threats.sort(key=lambda th: th[0])

        # What to shoot: the soonest threat that can be shot, else the UFO,
        # else the rock that takes least turning and flying to hit
        target = next((th[1] for th in threats if th[3]), None)
        if target is None:
            target = game.ufo or min(game.asteroids, key=self._cost_to_hit, default=None)
        aim_time = 0.0
        if target is not None:
            aim, dist = self._aim_at(target)
            diff = self._normalize_angle(aim - game.ship_angle)
            size = target.get('size', 1) * 2 + 1
            if abs(diff) < max(0.06, math.atan2(size * 0.6, dist)):
                self.ai_shoot = True
            else:
                self.ai_rotate = 1 if diff > 0 else -1
            aim_time = abs(diff) / TURN_SPEED + dist / BULLET_SPEED

        # Evade the soonest threat if it cannot be shot away in time
        if threats and game.invulnerable_timer <= 0:
            t_hit, body, radius, shootable = threats[0]
            if not (shootable and body is target and aim_time < t_hit - 0.15):
                # hyperspace is a gamble: only for a certain hit, not a near miss
                sure = self._time_to_hit(body, radius)
                if sure is not None and sure < PANIC:
                    self.ai_hyperspace = True
                else:
                    self._dodge(body)

    def _relative(self, body):
        """Body's position and velocity relative to the ship, across the wrap."""
        game = self.game
        px = (body['x'] - game.ship_x + GRID_SIZE / 2) % GRID_SIZE - GRID_SIZE / 2
        height = GRID_SIZE - 8
        py = (body['y'] - game.ship_y + height / 2) % height - height / 2
        return px, py, body['dx'] - game.ship_dx, body['dy'] - game.ship_dy

    def _time_to_hit(self, body, radius):
        """Seconds until the body comes within radius of the ship, or None."""
        px, py, vx, vy = self._relative(body)
        c = px * px + py * py - radius * radius
        if c <= 0:
            return 0.0
        a = vx * vx + vy * vy
        b = px * vx + py * vy
        if a == 0 or b >= 0:
            return None  # not moving relative to us, or moving away
        disc = b * b - a * c
        if disc < 0:
            return None  # passes clear
        t = (-b - math.sqrt(disc)) / a
        return t if t < LOOKAHEAD else None

    def _aim_at(self, body):
        """(angle to fire at so the bullet meets the body, distance to there)."""
        game = self.game
        px, py, vx, vy = self._relative(body)
        # a bullet keeps half the ship's velocity
        vx += game.ship_dx * 0.5
        vy += game.ship_dy * 0.5
        a = vx * vx + vy * vy - BULLET_SPEED * BULLET_SPEED
        b = px * vx + py * vy
        c = px * px + py * py
        t = (-b - math.sqrt(b * b - a * c)) / a  # a < 0: always one future meeting
        mx, my = px + vx * t, py + vy * t
        return math.atan2(my, mx), math.hypot(mx, my)

    def _cost_to_hit(self, body):
        aim, dist = self._aim_at(body)
        return abs(self._normalize_angle(aim - self.game.ship_angle)) / TURN_SPEED + dist / BULLET_SPEED

    def _dodge(self, body):
        """Thrust if the ship is facing out of the body's path; else turn to."""
        px, py, vx, vy = self._relative(body)
        path = math.atan2(vy, vx)
        # leave on the side of the path the ship is already on
        side = 1 if px * vy - py * vx > 0 else -1
        escape = path + side * math.pi / 2
        diff = self._normalize_angle(escape - self.game.ship_angle)
        if abs(diff) < 1.0:
            self.ai_thrust = True
        else:
            self.ai_rotate = 1 if diff > 0 else -1
            self.ai_shoot = False

    def _normalize_angle(self, angle):
        """Normalize angle to -pi to pi."""
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        return angle
