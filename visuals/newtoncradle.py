"""
Newton's Cradle
===============
Classic desk toy with swinging steel balls transferring momentum.

Controls:
  Left/Right - Add/remove balls
  Up/Down    - Adjust swing amplitude
"""

import math
from . import Visual, Display, Colors, GRID_SIZE


# Warm metallic palette for the balls
BALL_COLOR = (200, 200, 210)
BALL_HIGHLIGHT = (255, 255, 255)
STRING_COLOR = (80, 80, 80)
FRAME_COLOR = (120, 120, 130)


class NewtonCradle(Visual):
    name = "NEWTON"
    description = "Newton's cradle"
    category = "household"

    BALL_RADIUS = 4
    STRING_LEN = 30
    ANCHOR_Y = 6         # Top bar y position
    DAMPING = 0.9997     # Very slow energy loss
    GRAVITY = 120.0      # Gravity constant for pendulum

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.num_balls = 5
        self.pull_count = 1
        self._rebuild()
        self._start_swing()

    def _rebuild(self):
        """Recalculate anchors for current ball count."""
        self.spacing = self.BALL_RADIUS * 2 + 1
        total_w = (self.num_balls - 1) * self.spacing
        self.anchor_x_start = (GRID_SIZE - total_w) // 2

        self.anchors = []
        for i in range(self.num_balls):
            ax = self.anchor_x_start + i * self.spacing
            self.anchors.append((ax, self.ANCHOR_Y))

        self.angles = [0.0] * self.num_balls
        self.velocities = [0.0] * self.num_balls

    def _start_swing(self):
        """Pull the left ball(s) to start swinging."""
        for i in range(self.num_balls):
            self.velocities[i] = 0.0
            self.angles[i] = 0.0
        count = min(self.pull_count, self.num_balls - 1)
        for i in range(count):
            self.angles[i] = -0.8  # Pull left

    def handle_input(self, input_state):
        consumed = False
        # Up/Down: adjust swing amplitude (visual)
        if input_state.up_pressed:
            for i in range(self.num_balls):
                self.angles[i] *= 1.3
            consumed = True
        elif input_state.down_pressed:
            for i in range(self.num_balls):
                self.angles[i] *= 0.7
            consumed = True
        # Left/Right: add/remove balls
        if input_state.right_pressed:
            if self.num_balls < 7:
                self.num_balls += 1
                self._rebuild()
                self._start_swing()
            consumed = True
        elif input_state.left_pressed:
            if self.num_balls > 2:
                self.num_balls -= 1
                self.pull_count = min(self.pull_count, self.num_balls - 1)
                self._rebuild()
                self._start_swing()
            consumed = True
        return consumed

    def update(self, dt):
        self.time += dt
        # Sub-step for stability
        steps = 8
        sub_dt = dt / steps
        for _ in range(steps):
            self._physics_step(sub_dt)

    def _physics_step(self, dt):
        """Simulate Newton's cradle physics."""
        n = self.num_balls
        g_over_l = self.GRAVITY / self.STRING_LEN

        for i in range(n):
            accel = -g_over_l * math.sin(self.angles[i])
            self.velocities[i] += accel * dt
            self.velocities[i] *= self.DAMPING

        for i in range(n):
            self.angles[i] += self.velocities[i] * dt

        # Collision detection between adjacent balls
        for i in range(n - 1):
            ax1, ay1 = self.anchors[i]
            ax2, ay2 = self.anchors[i + 1]
            bx1 = ax1 + self.STRING_LEN * math.sin(self.angles[i])
            by1 = ay1 + self.STRING_LEN * math.cos(self.angles[i])
            bx2 = ax2 + self.STRING_LEN * math.sin(self.angles[i + 1])
            by2 = ay2 + self.STRING_LEN * math.cos(self.angles[i + 1])

            dx = bx2 - bx1
            dy = by2 - by1
            dist = math.sqrt(dx * dx + dy * dy)
            min_dist = self.BALL_RADIUS * 2

            if dist < min_dist and dist > 0:
                # Elastic collision - swap velocities (equal mass)
                self.velocities[i], self.velocities[i + 1] = (
                    self.velocities[i + 1], self.velocities[i]
                )
                overlap = (min_dist - dist) / 2
                norm_x = dx / dist
                self.angles[i] -= overlap * norm_x / self.STRING_LEN
                self.angles[i + 1] += overlap * norm_x / self.STRING_LEN

    def _ball_pos(self, i):
        """Get (x, y) of ball center for ball index i."""
        ax, ay = self.anchors[i]
        bx = ax + self.STRING_LEN * math.sin(self.angles[i])
        by = ay + self.STRING_LEN * math.cos(self.angles[i])
        return bx, by

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Draw top frame bar
        bar_x1 = self.anchor_x_start - self.BALL_RADIUS - 2
        bar_x2 = self.anchor_x_start + (self.num_balls - 1) * self.spacing + self.BALL_RADIUS + 2
        self.display.draw_line(bar_x1, self.ANCHOR_Y, bar_x2, self.ANCHOR_Y, FRAME_COLOR)
        self.display.draw_line(bar_x1, self.ANCHOR_Y - 1, bar_x2, self.ANCHOR_Y - 1, FRAME_COLOR)

        for i in range(self.num_balls):
            ax, ay = self.anchors[i]
            bx, by = self._ball_pos(i)
            ibx, iby = int(round(bx)), int(round(by))

            # Draw string
            self.display.draw_line(ax, ay, ibx, iby, STRING_COLOR)

            # Draw ball (filled circle)
            self.display.draw_circle(ibx, iby, self.BALL_RADIUS, BALL_COLOR, filled=True)

            # Highlight on top-left of ball
            hx = ibx - 1
            hy = iby - 1
            if 0 <= hx < GRID_SIZE and 0 <= hy < GRID_SIZE:
                self.display.set_pixel(hx, hy, BALL_HIGHLIGHT)
