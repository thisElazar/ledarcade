"""
Camshaft
========
Rotating camshaft with egg-shaped lobes pushing valve followers.
Multiple cams offset so valves fire in sequence.

Controls:
  Left/Right - Adjust RPM
"""

import math
from . import Visual, Display, Colors, GRID_SIZE


# Colors
SHAFT_COLOR = (120, 120, 130)
SHAFT_HIGHLIGHT = (160, 160, 170)
CAM_COLOR = (180, 180, 190)
CAM_EDGE = (140, 140, 150)
FOLLOWER_COLOR = (200, 170, 50)
FOLLOWER_TOP = (220, 190, 80)
SPRING_COLOR = (100, 100, 110)
VALVE_COLOR = (200, 120, 60)
HOUSING_COLOR = (50, 50, 55)
RPM_COLOR = (180, 180, 190)

# Cam profile: base circle + lobe
BASE_R = 5
LOBE_R = 10  # max radius at lobe peak
LOBE_WIDTH = 0.4  # fraction of full rotation that is "lobe" (in 0-1)

# Layout
NUM_CAMS = 4
CAM_SPACING = 14
CAM_Y = 42  # shaft vertical center
FOLLOWER_W = 5
FOLLOWER_H = 6
GUIDE_TOP = 10  # top of follower travel


def cam_radius(angle):
    """Return cam radius at given angle. Lobe centered at angle=0."""
    # Normalize to [-pi, pi]
    a = angle % (2 * math.pi)
    if a > math.pi:
        a -= 2 * math.pi
    # Smooth lobe using raised cosine
    half_lobe = LOBE_WIDTH * math.pi
    if abs(a) < half_lobe:
        t = 0.5 * (1 + math.cos(math.pi * a / half_lobe))
        return BASE_R + (LOBE_R - BASE_R) * t
    return BASE_R


def follower_lift(angle):
    """Return follower lift (0 to 1) at given cam angle."""
    r = cam_radius(angle)
    return (r - BASE_R) / (LOBE_R - BASE_R)


class Camshaft(Visual):
    name = "CAMSHAFT"
    description = "Engine camshaft"
    category = "mechanics"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.rotation = 0.0
        self.speed_level = 3  # 1-6
        self.rpm = 180
        # Phase offsets for each cam (evenly spaced firing order)
        self.phase_offsets = [i * 2 * math.pi / NUM_CAMS for i in range(NUM_CAMS)]
        # X positions for each cam
        total_w = (NUM_CAMS - 1) * CAM_SPACING
        self.cam_xs = [int((GRID_SIZE - total_w) / 2 + i * CAM_SPACING) for i in range(NUM_CAMS)]

    def handle_input(self, input_state):
        consumed = False
        if input_state.right_pressed:
            self.speed_level = min(6, self.speed_level + 1)
            self.rpm = 60 * self.speed_level
            consumed = True
        elif input_state.left_pressed:
            self.speed_level = max(1, self.speed_level - 1)
            self.rpm = 60 * self.speed_level
            consumed = True
        return consumed

    def update(self, dt):
        self.time += dt
        self.rotation += (self.rpm / 60.0) * 2 * math.pi * dt

    def draw(self):
        d = self.display
        d.clear(Colors.BLACK)

        # Draw housing/block behind followers
        for i, cx in enumerate(self.cam_xs):
            x0 = cx - FOLLOWER_W // 2 - 1
            d.draw_rect(x0, GUIDE_TOP, FOLLOWER_W + 2, CAM_Y - LOBE_R - GUIDE_TOP, HOUSING_COLOR)

        # Draw shaft (horizontal line through cam centers)
        shaft_x0 = self.cam_xs[0] - LOBE_R - 2
        shaft_x1 = self.cam_xs[-1] + LOBE_R + 2
        d.draw_line(shaft_x0, CAM_Y, shaft_x1, CAM_Y, SHAFT_COLOR)
        d.draw_line(shaft_x0, CAM_Y - 1, shaft_x1, CAM_Y - 1, SHAFT_HIGHLIGHT)

        # Draw each cam and its follower
        for i, cx in enumerate(self.cam_xs):
            angle = self.rotation + self.phase_offsets[i]
            self._draw_cam(d, cx, CAM_Y, angle)
            lift = follower_lift(angle)
            self._draw_follower(d, cx, lift, i)

        # RPM text
        d.draw_text_small(2, 2, f"{self.rpm} RPM", RPM_COLOR)

    def _draw_cam(self, d, cx, cy, angle):
        """Draw a single cam lobe pixel-by-pixel."""
        margin = LOBE_R + 2
        for py in range(cy - margin, cy + margin + 1):
            if py < 0 or py >= GRID_SIZE:
                continue
            for px in range(cx - margin, cx + margin + 1):
                if px < 0 or px >= GRID_SIZE:
                    continue
                dx = px - cx
                dy = py - cy
                dist_sq = dx * dx + dy * dy
                if dist_sq > (LOBE_R + 1) ** 2:
                    continue
                dist = math.sqrt(dist_sq)
                # Angle of this pixel relative to cam rotation
                pixel_angle = math.atan2(dy, dx) - angle
                r_at_angle = cam_radius(pixel_angle)
                if dist <= r_at_angle:
                    if dist > r_at_angle - 1.2:
                        d.set_pixel(px, py, CAM_EDGE)
                    else:
                        d.set_pixel(px, py, CAM_COLOR)

        # Shaft center dot
        d.set_pixel(cx, cy, SHAFT_HIGHLIGHT)

    def _draw_follower(self, d, cx, lift, index):
        """Draw follower, spring, and valve stem above a cam."""
        # Follower travels from CAM_Y - LOBE_R (bottom) to GUIDE_TOP (top)
        max_travel = CAM_Y - LOBE_R - GUIDE_TOP - FOLLOWER_H
        follower_y = int(CAM_Y - LOBE_R - lift * max_travel)
        fx = cx - FOLLOWER_W // 2

        # Follower body
        d.draw_rect(fx, follower_y, FOLLOWER_W, FOLLOWER_H, FOLLOWER_COLOR)
        # Highlight top edge
        d.draw_line(fx, follower_y, fx + FOLLOWER_W - 1, follower_y, FOLLOWER_TOP)

        # Spring between follower top and guide top (zigzag)
        spring_bot = follower_y
        spring_top = GUIDE_TOP
        if spring_bot - spring_top > 2:
            teeth = 4
            seg_h = (spring_bot - spring_top) / (teeth * 2)
            for t in range(teeth * 2):
                y0 = int(spring_top + t * seg_h)
                y1 = int(spring_top + (t + 1) * seg_h)
                if t % 2 == 0:
                    d.draw_line(cx - 2, y0, cx + 2, y1, SPRING_COLOR)
                else:
                    d.draw_line(cx + 2, y0, cx - 2, y1, SPRING_COLOR)

        # Valve stem below the cam
        valve_top = CAM_Y + LOBE_R + 1
        valve_bot = min(63, valve_top + 6 + int(lift * 4))
        d.draw_line(cx, valve_top, cx, valve_bot, VALVE_COLOR)
        # Valve head
        d.draw_line(cx - 2, valve_bot, cx + 2, valve_bot, VALVE_COLOR)
