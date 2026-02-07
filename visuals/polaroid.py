"""
Polaroid Camera - Interactive camera visual
============================================
A cute polaroid camera that rotates and takes pictures!

Controls:
  Left/Right - Rotate camera
  Space      - Take a picture (flash!)
  Up/Down    - Zoom in/out
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE


class Polaroid(Visual):
    name = "POLAROID"
    description = "Say cheese!"
    category = "household"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.angle = 0.0  # Rotation angle in radians
        self.target_angle = 0.0
        self.scale = 1.0

        # Flash effect
        self.flash_intensity = 0.0

        # Photo ejection animation
        self.photo_active = False
        self.photo_y = 0.0  # How far the photo has ejected
        self.photo_color = Colors.WHITE
        self.photo_developing = 0.0  # 0 = white, 1 = fully developed

        # Camera colors
        self.body_color = (60, 60, 70)
        self.body_highlight = (80, 80, 90)
        self.lens_outer = (30, 30, 35)
        self.lens_inner = (20, 20, 80)
        self.lens_reflect = (100, 100, 150)
        self.rainbow_stripe = [
            (255, 0, 0),
            (255, 165, 0),
            (255, 255, 0),
            (0, 128, 0),
            (0, 0, 255),
        ]
        self.viewfinder_color = (40, 40, 45)
        self.button_color = (200, 50, 50)

        # Input timing
        self.rotate_held = 0.0

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Track if we're actively rotating
        is_rotating = input_state.left or input_state.right
        was_rotating = getattr(self, '_was_rotating', False)

        # Rotation
        if input_state.left:
            self.target_angle += 0.08
            consumed = True
        if input_state.right:
            self.target_angle -= 0.08
            consumed = True

        # Snap to 90-degree angles when releasing rotation keys
        if was_rotating and not is_rotating:
            snap_threshold = 0.7  # About 40 degrees - generous snapping
            half_pi = math.pi / 2

            # Normalize angle to 0 to 2π range
            normalized = self.target_angle % (2 * math.pi)
            if normalized < 0:
                normalized += 2 * math.pi

            # Find the closest snap angle and the smallest rotation to get there
            snap_angles = [0, half_pi, math.pi, 3 * half_pi, 2 * math.pi]
            best_snap = None
            best_diff = float('inf')

            for snap_angle in snap_angles:
                # Calculate shortest angular distance
                diff = normalized - snap_angle
                # Wrap to [-π, π] range for shortest path
                while diff > math.pi:
                    diff -= 2 * math.pi
                while diff < -math.pi:
                    diff += 2 * math.pi

                if abs(diff) < snap_threshold and abs(diff) < abs(best_diff):
                    best_diff = diff
                    best_snap = snap_angle

            if best_snap is not None:
                # Apply the small correction to current angle
                self.target_angle -= best_diff

        self._was_rotating = is_rotating

        # Zoom
        if input_state.up:
            self.scale = min(1.5, self.scale + 0.02)
            consumed = True
        if input_state.down:
            self.scale = max(0.5, self.scale - 0.02)
            consumed = True

        # Take picture
        if (input_state.action_l or input_state.action_r):
            self.take_picture()
            consumed = True

        return consumed

    def take_picture(self):
        """Trigger the flash and eject a photo."""
        self.flash_intensity = 1.0

        # Start photo ejection
        self.photo_active = True
        self.photo_y = 0.0
        self.photo_developing = 0.0
        self.photo_phase = 'ejecting'
        self.photo_display_y = 0.0
        self.hold_timer = 0.0
        self.fade_alpha = 1.0

        # Choose a random photo style
        self.photo_style = random.choice([
            'sunset', 'sunrise', 'portrait', 'landscape', 'abstract',
            'stripes', 'gradient', 'dots', 'nature', 'beach',
            'city', 'night_sky', 'rainbow', 'mountains', 'retro'
        ])

        # Generate colors based on style with variations
        if self.photo_style == 'sunset':
            variation = random.choice(['warm', 'pink', 'purple'])
            if variation == 'warm':
                self.photo_colors = [
                    (255, random.randint(80, 120), random.randint(30, 70)),
                    (255, random.randint(160, 200), random.randint(80, 120)),
                    (random.randint(180, 220), random.randint(60, 100), random.randint(100, 140)),
                    (random.randint(60, 100), random.randint(40, 80), random.randint(100, 140)),
                ]
            elif variation == 'pink':
                self.photo_colors = [
                    (255, 150, 180), (255, 200, 150), (200, 100, 150), (100, 80, 140)
                ]
            else:
                self.photo_colors = [
                    (255, 120, 80), (180, 80, 160), (120, 60, 140), (60, 40, 100)
                ]
        elif self.photo_style == 'sunrise':
            self.photo_colors = [
                (random.randint(40, 80), random.randint(60, 100), random.randint(120, 160)),
                (255, random.randint(180, 220), random.randint(100, 140)),
                (255, random.randint(200, 240), random.randint(150, 190)),
                (random.randint(200, 240), random.randint(160, 200), random.randint(100, 140)),
            ]
        elif self.photo_style == 'portrait':
            skin = random.choice([
                (255, 224, 189), (241, 194, 125), (224, 172, 105),
                (198, 134, 66), (141, 85, 36), (100, 60, 30)
            ])
            bg_style = random.choice(['blue', 'green', 'warm', 'neutral'])
            if bg_style == 'blue':
                bg = (random.randint(100, 150), random.randint(130, 180), random.randint(180, 230))
            elif bg_style == 'green':
                bg = (random.randint(80, 130), random.randint(150, 200), random.randint(80, 130))
            elif bg_style == 'warm':
                bg = (random.randint(180, 230), random.randint(140, 180), random.randint(100, 140))
            else:
                v = random.randint(120, 180)
                bg = (v, v, v + random.randint(-20, 20))
            hair = random.choice([(40, 30, 20), (80, 50, 30), (60, 40, 30), (20, 15, 10), (180, 140, 80)])
            self.photo_colors = [bg, skin, hair, bg]
        elif self.photo_style == 'landscape':
            season = random.choice(['summer', 'autumn', 'spring'])
            if season == 'summer':
                self.photo_colors = [
                    (random.randint(120, 160), random.randint(190, 230), random.randint(220, 255)),
                    (random.randint(120, 160), random.randint(190, 230), random.randint(220, 255)),
                    (random.randint(30, 80), random.randint(140, 180), random.randint(30, 80)),
                    (random.randint(20, 60), random.randint(100, 140), random.randint(20, 60)),
                ]
            elif season == 'autumn':
                self.photo_colors = [
                    (180, 200, 220), (180, 200, 220),
                    (random.randint(180, 220), random.randint(100, 140), random.randint(30, 70)),
                    (random.randint(140, 180), random.randint(80, 120), random.randint(20, 60)),
                ]
            else:
                self.photo_colors = [
                    (170, 210, 240), (170, 210, 240),
                    (random.randint(100, 160), random.randint(180, 220), random.randint(100, 160)),
                    (random.randint(80, 140), random.randint(160, 200), random.randint(80, 140)),
                ]
        elif self.photo_style == 'nature':
            flower1 = random.choice([(255, 200, 100), (255, 150, 180), (200, 100, 255), (255, 100, 100)])
            flower2 = random.choice([(255, 255, 150), (255, 180, 200), (180, 150, 255), (255, 200, 150)])
            self.photo_colors = [
                (random.randint(100, 150), random.randint(180, 220), 255),
                (random.randint(60, 100), random.randint(140, 180), random.randint(60, 100)),
                flower1, flower2
            ]
        elif self.photo_style == 'beach':
            self.photo_colors = [
                (random.randint(100, 150), random.randint(180, 220), random.randint(230, 255)),
                (random.randint(30, 80), random.randint(140, 180), random.randint(180, 220)),
                (random.randint(230, 255), random.randint(220, 245), random.randint(180, 210)),
                (random.randint(210, 240), random.randint(190, 220), random.randint(150, 180)),
            ]
        elif self.photo_style == 'city':
            self.photo_colors = [
                (random.randint(40, 80), random.randint(50, 90), random.randint(80, 120)),
                (random.randint(60, 100), random.randint(70, 110), random.randint(90, 130)),
                (random.randint(80, 120), random.randint(80, 120), random.randint(100, 140)),
                (random.randint(255, 255), random.randint(200, 240), random.randint(100, 150)),
            ]
        elif self.photo_style == 'night_sky':
            self.photo_colors = [
                (random.randint(10, 30), random.randint(10, 40), random.randint(40, 80)),
                (random.randint(20, 50), random.randint(20, 60), random.randint(60, 100)),
                (255, 255, random.randint(200, 255)),
                (random.randint(200, 255), random.randint(200, 255), 255),
            ]
        elif self.photo_style == 'rainbow':
            self.photo_colors = [
                (255, random.randint(50, 100), random.randint(50, 100)),
                (255, random.randint(180, 220), random.randint(50, 100)),
                (random.randint(50, 100), 255, random.randint(50, 100)),
                (random.randint(50, 100), random.randint(150, 200), 255),
            ]
        elif self.photo_style == 'mountains':
            self.photo_colors = [
                (random.randint(180, 220), random.randint(200, 240), random.randint(240, 255)),
                (random.randint(100, 140), random.randint(110, 150), random.randint(140, 180)),
                (random.randint(60, 100), random.randint(80, 120), random.randint(60, 100)),
                (random.randint(40, 80), random.randint(60, 100), random.randint(40, 80)),
            ]
        elif self.photo_style == 'retro':
            # Faded, vintage colors
            base = random.choice(['orange', 'teal', 'sepia'])
            if base == 'orange':
                self.photo_colors = [
                    (230, 180, 140), (200, 150, 120), (180, 120, 100), (150, 100, 80)
                ]
            elif base == 'teal':
                self.photo_colors = [
                    (150, 200, 190), (120, 170, 160), (100, 140, 140), (80, 110, 120)
                ]
            else:
                self.photo_colors = [
                    (210, 190, 160), (190, 170, 140), (170, 150, 120), (140, 120, 100)
                ]
        elif self.photo_style == 'stripes':
            c1 = (random.randint(100, 255), random.randint(50, 150), random.randint(50, 150))
            c2 = (random.randint(50, 150), random.randint(100, 255), random.randint(100, 255))
            self.photo_colors = [c1, c2, c1, c2]
        elif self.photo_style == 'gradient':
            c1 = (random.randint(150, 255), random.randint(50, 150), random.randint(100, 200))
            c2 = (random.randint(50, 150), random.randint(100, 200), random.randint(150, 255))
            self.photo_colors = [c1, c1, c2, c2]
        elif self.photo_style == 'dots':
            bg = (random.randint(200, 255), random.randint(200, 255), random.randint(200, 255))
            dot = (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))
            self.photo_colors = [bg, dot, bg, dot]
        else:  # abstract
            self.photo_colors = [
                (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
                for _ in range(4)
            ]

    def update(self, dt: float):
        self.time += dt

        # Smooth rotation
        angle_diff = self.target_angle - self.angle
        self.angle += angle_diff * min(1.0, dt * 8)

        # Flash decay
        if self.flash_intensity > 0:
            self.flash_intensity -= dt * 4
            if self.flash_intensity < 0:
                self.flash_intensity = 0

        # Photo animation phases:
        # 1. Ejecting: photo slides down out of camera
        # 2. Rising: photo floats up to cover camera, developing starts
        # 3. Holding: photo stays centered while finishing development
        # 4. Fading: photo fades away
        if self.photo_active:
            phase = getattr(self, 'photo_phase', 'ejecting')

            if phase == 'ejecting':
                # Slide down until fully ejected (photo_y = 35 means it's well below camera)
                self.photo_y += dt * 50
                if self.photo_y >= 35:
                    self.photo_y = 35
                    self.photo_phase = 'rising'
                    self.photo_display_y = self.photo_y  # Start tracking display position

            elif phase == 'rising':
                # Float up to center (display_y moves toward -14 to center the photo)
                # Also start developing
                target_y = -14  # Centers the 28px photo on the 64px display
                self.photo_display_y += (target_y - self.photo_display_y) * dt * 3
                self.photo_developing += dt * 0.4

                if abs(self.photo_display_y - target_y) < 0.5:
                    self.photo_display_y = target_y
                    self.photo_phase = 'holding'

            elif phase == 'holding':
                # Stay centered while finishing development
                self.photo_developing += dt * 0.5
                if self.photo_developing >= 1.0:
                    self.photo_developing = 1.0
                    self.hold_timer = getattr(self, 'hold_timer', 0) + dt
                    if self.hold_timer > 1.5:  # Hold for 1.5 seconds
                        self.photo_phase = 'fading'
                        self.fade_alpha = 1.0

            elif phase == 'fading':
                # Fade out
                self.fade_alpha = getattr(self, 'fade_alpha', 1.0) - dt * 1.5
                if self.fade_alpha <= 0:
                    self.photo_active = False
                    self.photo_phase = 'ejecting'
                    self.hold_timer = 0

    def rotate_point(self, x: float, y: float, cx: float, cy: float) -> tuple:
        """Rotate a point around center."""
        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)

        # Translate to origin
        x -= cx
        y -= cy

        # Apply scale
        x *= self.scale
        y *= self.scale

        # Rotate
        new_x = x * cos_a - y * sin_a
        new_y = x * sin_a + y * cos_a

        # Translate back
        return (new_x + cx, new_y + cy)

    def draw_rotated_rect(self, cx: int, cy: int, x: int, y: int, w: int, h: int, color: tuple):
        """Draw a filled rectangle rotated around center (inverse mapping)."""
        center_x, center_y = GRID_SIZE // 2, GRID_SIZE // 2
        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)

        # Source rect bounds in local coords
        lx1, ly1 = x - cx, y - cy
        lx2, ly2 = lx1 + w, ly1 + h

        # Forward-map corners to find screen bounding box
        corners = [(lx1, ly1), (lx2, ly1), (lx1, ly2), (lx2, ly2)]
        sxs = []
        sys = []
        for lx, ly in corners:
            sx = lx * self.scale
            sy = ly * self.scale
            sxs.append(sx * cos_a - sy * sin_a + center_x)
            sys.append(sx * sin_a + sy * cos_a + center_y)

        min_sx = max(0, int(min(sxs)) - 1)
        max_sx = min(GRID_SIZE - 1, int(max(sxs)) + 1)
        min_sy = max(0, int(min(sys)) - 1)
        max_sy = min(GRID_SIZE - 1, int(max(sys)) + 1)

        inv_scale = 1.0 / self.scale if self.scale != 0 else 1.0

        for sy in range(min_sy, max_sy + 1):
            for sx in range(min_sx, max_sx + 1):
                dx = sx - center_x
                dy = sy - center_y
                lx = (dx * cos_a + dy * sin_a) * inv_scale
                ly = (-dx * sin_a + dy * cos_a) * inv_scale
                if lx1 <= lx < lx2 and ly1 <= ly < ly2:
                    self.display.set_pixel(sx, sy, color)

    def draw_rotated_circle(self, cx: int, cy: int, x: int, y: int, r: int, color: tuple, filled: bool = True):
        """Draw a circle rotated around center (inverse mapping)."""
        center_x, center_y = GRID_SIZE // 2, GRID_SIZE // 2
        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)

        # Circle center in local coords
        ccx, ccy = x - cx, y - cy

        # Forward-map bounding box corners to find screen bounds
        corners = [(ccx - r, ccy - r), (ccx + r, ccy - r),
                    (ccx - r, ccy + r), (ccx + r, ccy + r)]
        sxs = []
        sys = []
        for lx, ly in corners:
            sx = lx * self.scale
            sy = ly * self.scale
            sxs.append(sx * cos_a - sy * sin_a + center_x)
            sys.append(sx * sin_a + sy * cos_a + center_y)

        min_sx = max(0, int(min(sxs)) - 1)
        max_sx = min(GRID_SIZE - 1, int(max(sxs)) + 1)
        min_sy = max(0, int(min(sys)) - 1)
        max_sy = min(GRID_SIZE - 1, int(max(sys)) + 1)

        inv_scale = 1.0 / self.scale if self.scale != 0 else 1.0
        r_sq = r * r

        for sy in range(min_sy, max_sy + 1):
            for sx in range(min_sx, max_sx + 1):
                dx = sx - center_x
                dy = sy - center_y
                lx = (dx * cos_a + dy * sin_a) * inv_scale
                ly = (-dx * sin_a + dy * cos_a) * inv_scale
                dist_sq = (lx - ccx) ** 2 + (ly - ccy) ** 2
                if filled:
                    if dist_sq <= r_sq:
                        self.display.set_pixel(sx, sy, color)
                else:
                    if abs(dist_sq - r_sq) < r * 2:
                        self.display.set_pixel(sx, sy, color)

    def draw(self):
        # Background with flash effect
        if self.flash_intensity > 0:
            flash = int(255 * self.flash_intensity)
            self.display.clear((flash, flash, flash))
        else:
            # Subtle gradient background
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    shade = 10 + int(15 * (y / GRID_SIZE))
                    self.display.set_pixel(x, y, (shade, shade, shade + 5))

        # Camera dimensions (relative to center at 0,0)
        cam_w, cam_h = 40, 32
        cam_x, cam_y = -cam_w // 2, -cam_h // 2

        # Draw camera body
        self.draw_rotated_rect(0, 0, cam_x, cam_y, cam_w, cam_h, self.body_color)

        # Body highlight (top edge)
        self.draw_rotated_rect(0, 0, cam_x + 1, cam_y + 1, cam_w - 2, 2, self.body_highlight)

        # Rainbow stripe (classic Polaroid look)
        stripe_y = cam_y + cam_h - 6
        stripe_w = cam_w - 8
        stripe_x = cam_x + 4
        for i, color in enumerate(self.rainbow_stripe):
            self.draw_rotated_rect(0, 0, stripe_x + i * (stripe_w // 5), stripe_y, stripe_w // 5, 4, color)

        # Lens (outer ring)
        lens_x, lens_y = 0, -2
        self.draw_rotated_circle(0, 0, lens_x, lens_y, 10, self.lens_outer)

        # Lens (middle)
        self.draw_rotated_circle(0, 0, lens_x, lens_y, 8, self.lens_inner)

        # Lens (inner dark)
        self.draw_rotated_circle(0, 0, lens_x, lens_y, 5, (10, 10, 40))

        # Lens reflection/highlight
        self.draw_rotated_circle(0, 0, lens_x - 2, lens_y - 2, 2, self.lens_reflect)

        # Viewfinder (top right)
        vf_x, vf_y = cam_x + cam_w - 10, cam_y + 3
        self.draw_rotated_rect(0, 0, vf_x, vf_y, 6, 4, self.viewfinder_color)
        # Viewfinder glass
        self.draw_rotated_rect(0, 0, vf_x + 1, vf_y + 1, 4, 2, (60, 80, 100))

        # Shutter button (top)
        btn_x, btn_y = cam_x + 8, cam_y - 3
        # Button base
        self.draw_rotated_rect(0, 0, btn_x, btn_y, 8, 4, (100, 30, 30))
        # Button top
        self.draw_rotated_rect(0, 0, btn_x + 1, btn_y, 6, 2, self.button_color)

        # Flash unit (top left)
        flash_x, flash_y = cam_x + 2, cam_y + 3
        self.draw_rotated_rect(0, 0, flash_x, flash_y, 8, 6, (50, 50, 55))
        # Flash bulb
        flash_color = (200, 200, 220) if self.flash_intensity == 0 else (255, 255, 255)
        self.draw_rotated_rect(0, 0, flash_x + 1, flash_y + 1, 6, 4, flash_color)

        # Photo slot (bottom)
        slot_x, slot_y = cam_x + 8, cam_y + cam_h - 2
        self.draw_rotated_rect(0, 0, slot_x, slot_y, cam_w - 16, 2, (20, 20, 25))

        # Draw ejecting photo
        if self.photo_active:
            self.draw_photo()

    def draw_photo(self):
        """Draw the ejecting/developing photo."""
        center_x, center_y = GRID_SIZE // 2, GRID_SIZE // 2

        # Photo dimensions
        photo_w, photo_h = 24, 28
        photo_x = -photo_w // 2

        # Get current animation phase
        phase = getattr(self, 'photo_phase', 'ejecting')
        fade_alpha = getattr(self, 'fade_alpha', 1.0)

        # Camera bottom is at y=16 relative to center
        camera_bottom = 16

        if phase == 'ejecting':
            # During ejecting: photo slides down, only show emerged portion
            eject_progress = int(self.photo_y)
            photo_bottom = camera_bottom + eject_progress
            photo_top = photo_bottom - photo_h
            clip_top = camera_bottom  # Only show below camera
        else:
            # During rising/holding/fading: show full photo at display position
            photo_display_y = getattr(self, 'photo_display_y', 0)
            photo_top = int(photo_display_y)
            clip_top = -100  # No clipping, show full photo

        # Draw photo border (white)
        for dy in range(photo_h):
            py = photo_top + dy
            if py >= clip_top:
                for dx in range(photo_w):
                    px = photo_x + dx
                    rx, ry = self.rotate_point(px + center_x, py + center_y, center_x, center_y)
                    ix, iy = int(rx), int(ry)
                    if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                        if phase == 'fading':
                            # Fade to background
                            bg = 10 + int(15 * (iy / GRID_SIZE))
                            color = (
                                int(255 * fade_alpha + bg * (1 - fade_alpha)),
                                int(255 * fade_alpha + bg * (1 - fade_alpha)),
                                int(255 * fade_alpha + (bg + 5) * (1 - fade_alpha)),
                            )
                            self.display.set_pixel(ix, iy, color)
                        else:
                            self.display.set_pixel(ix, iy, Colors.WHITE)

        # Photo image area (develops over time)
        img_margin = 3
        img_w = photo_w - img_margin * 2
        img_h = photo_h - img_margin - 6  # Extra space at bottom like real Polaroid

        for dy in range(img_h):
            img_y = photo_top + img_margin + dy
            if img_y >= clip_top:
                for dx in range(img_w):
                    px = photo_x + img_margin + dx
                    py = img_y

                    # Calculate pattern coordinates
                    pattern_x = dx / img_w
                    pattern_y = dy / img_h

                    # Get target color based on photo style
                    target = self.get_photo_pixel_color(dx, dy, img_w, img_h, pattern_x, pattern_y)

                    if self.photo_developing < 1.0:
                        # Developing - blend from sepia/gray to color
                        dev = self.photo_developing
                        # Start with greenish-gray (like real developing polaroid)
                        gray_r = 180 - int(30 * dev)
                        gray_g = 190 - int(40 * dev)
                        gray_b = 170 - int(20 * dev)

                        color = (
                            int(gray_r * (1 - dev) + target[0] * dev),
                            int(gray_g * (1 - dev) + target[1] * dev),
                            int(gray_b * (1 - dev) + target[2] * dev),
                        )
                    else:
                        color = target

                    # Apply fade if in fading phase
                    if phase == 'fading':
                        rx, ry = self.rotate_point(px + center_x, py + center_y, center_x, center_y)
                        ix, iy = int(rx), int(ry)
                        if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                            bg = 10 + int(15 * (iy / GRID_SIZE))
                            color = (
                                int(color[0] * fade_alpha + bg * (1 - fade_alpha)),
                                int(color[1] * fade_alpha + bg * (1 - fade_alpha)),
                                int(color[2] * fade_alpha + (bg + 5) * (1 - fade_alpha)),
                            )

                    rx, ry = self.rotate_point(px + center_x, py + center_y, center_x, center_y)
                    ix, iy = int(rx), int(ry)
                    if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                        self.display.set_pixel(ix, iy, color)

    def get_photo_pixel_color(self, dx, dy, img_w, img_h, px, py):
        """Get the color for a photo pixel based on style."""
        style = getattr(self, 'photo_style', 'abstract')

        if style == 'sunset' or style == 'sunrise':
            # Horizontal gradient with sun
            row = int(py * 4)
            base = self.photo_colors[min(row, 3)]
            # Add a sun circle
            sun_x = img_w * (0.7 if style == 'sunset' else 0.3)
            sun_y = img_h * 0.3
            dist = math.sqrt((dx - sun_x)**2 + (dy - sun_y)**2)
            if dist < 3:
                return (255, 250, 200) if style == 'sunrise' else (255, 230, 150)
            elif dist < 4.5:
                # Sun glow
                t = (dist - 3) / 1.5
                glow = (255, 240, 180)
                return (
                    int(glow[0] * (1-t) + base[0] * t),
                    int(glow[1] * (1-t) + base[1] * t),
                    int(glow[2] * (1-t) + base[2] * t),
                )
            return base

        elif style == 'portrait':
            # Simple face shape
            cx, cy = img_w // 2, img_h // 2 - 1
            dist = math.sqrt((dx - cx)**2 + ((dy - cy) * 0.8)**2)  # Oval face
            if dist < img_w * 0.32:
                # Face area
                if dy < cy - 2:
                    return self.photo_colors[2]  # Hair
                return self.photo_colors[1]  # Skin
            elif dist < img_w * 0.45 and dy < cy:
                return self.photo_colors[2]  # Hair around face
            return self.photo_colors[0]  # Background

        elif style == 'landscape':
            # Sky and ground with horizon
            if py < 0.4:
                return self.photo_colors[0]  # Sky
            elif py < 0.45:
                # Horizon blend
                return self.photo_colors[1]
            else:
                # Ground with texture
                noise = ((dx * 17 + dy * 31) % 5) / 5
                if noise < 0.3:
                    return self.photo_colors[3]
                return self.photo_colors[2]

        elif style == 'nature':
            # Flowers on grass with sky
            if py < 0.25:
                return self.photo_colors[0]  # Sky
            else:
                # Ground with scattered flowers
                flower_pattern = (dx * 7 + dy * 13) % 13
                if flower_pattern == 0:
                    return self.photo_colors[2]
                elif flower_pattern == 1:
                    return self.photo_colors[3]
                # Grass variation
                grass_var = ((dx + dy * 3) % 3)
                c = self.photo_colors[1]
                shade = -15 if grass_var == 0 else (10 if grass_var == 1 else 0)
                return (max(0, c[0]+shade), max(0, c[1]+shade), max(0, c[2]+shade))

        elif style == 'beach':
            # Sky, ocean, sand
            if py < 0.3:
                return self.photo_colors[0]  # Sky
            elif py < 0.5:
                # Ocean with wave hints
                wave = math.sin(dx * 0.8 + py * 10) > 0.5
                return self.photo_colors[1] if not wave else (
                    min(255, self.photo_colors[1][0] + 30),
                    min(255, self.photo_colors[1][1] + 30),
                    min(255, self.photo_colors[1][2] + 20)
                )
            else:
                # Sand with texture
                if (dx + dy) % 4 == 0:
                    return self.photo_colors[3]
                return self.photo_colors[2]

        elif style == 'city':
            # Skyline silhouette
            if py < 0.35:
                return self.photo_colors[0]  # Sky
            # Buildings
            building_pattern = (dx * 3) % 7
            building_height = 0.35 + (building_pattern / 7) * 0.3
            if py < building_height:
                return self.photo_colors[0]
            # Building with windows
            if py < 0.75:
                window = (dx % 3 == 1) and (int(py * 20) % 3 == 1)
                if window:
                    return self.photo_colors[3]  # Lit window
                return self.photo_colors[1]  # Building
            return self.photo_colors[2]  # Street level

        elif style == 'night_sky':
            # Dark sky with stars
            base = self.photo_colors[0] if py < 0.5 else self.photo_colors[1]
            # Random stars
            star_pattern = (dx * 31 + dy * 17) % 23
            if star_pattern == 0:
                return self.photo_colors[2]  # Bright star
            elif star_pattern == 1:
                return self.photo_colors[3]  # Dim star
            return base

        elif style == 'rainbow':
            # Diagonal rainbow stripes
            band = int((px + py) * 4) % 4
            return self.photo_colors[band]

        elif style == 'mountains':
            if py < 0.25:
                return self.photo_colors[0]  # Sky
            # Mountain silhouette
            mountain_line = 0.25 + 0.15 * math.sin(px * math.pi * 2) + 0.1 * math.sin(px * math.pi * 5)
            if py < mountain_line + 0.1:
                return self.photo_colors[1]  # Far mountains
            elif py < mountain_line + 0.25:
                return self.photo_colors[2]  # Near mountains/forest
            return self.photo_colors[3]  # Foreground

        elif style == 'retro':
            # Faded photo with vignette effect
            cx, cy = 0.5, 0.5
            dist = math.sqrt((px - cx)**2 + (py - cy)**2)
            vignette = min(1.0, dist * 1.5)
            # Blend between colors based on position
            idx = int(py * 3)
            base = self.photo_colors[min(idx, 3)]
            # Apply vignette darkening
            return (
                int(base[0] * (1 - vignette * 0.3)),
                int(base[1] * (1 - vignette * 0.3)),
                int(base[2] * (1 - vignette * 0.3)),
            )

        elif style == 'stripes':
            # Vertical stripes with slight variation
            stripe = (dx // 2) % 2
            c = self.photo_colors[stripe]
            # Add subtle variation
            var = ((dx + dy) % 3 - 1) * 8
            return (
                max(0, min(255, c[0] + var)),
                max(0, min(255, c[1] + var)),
                max(0, min(255, c[2] + var)),
            )

        elif style == 'gradient':
            # Smooth diagonal gradient
            t = (px + py) / 2
            c1, c2 = self.photo_colors[0], self.photo_colors[2]
            return (
                int(c1[0] + (c2[0] - c1[0]) * t),
                int(c1[1] + (c2[1] - c1[1]) * t),
                int(c1[2] + (c2[2] - c1[2]) * t),
            )

        elif style == 'dots':
            # Polka dots pattern
            dot_spacing = 4
            dot_x = dx % dot_spacing
            dot_y = dy % dot_spacing
            cx, cy = dot_spacing // 2, dot_spacing // 2
            if (dot_x - cx)**2 + (dot_y - cy)**2 <= 1:
                return self.photo_colors[1]  # Dot color
            return self.photo_colors[0]  # Background

        else:  # abstract
            # Quadrant-based colors with some blending
            qx = int(px * 2)
            qy = int(py * 2)
            quad = qx + qy * 2
            base = self.photo_colors[quad % len(self.photo_colors)]
            # Add some noise
            noise = ((dx * 13 + dy * 7) % 5 - 2) * 10
            return (
                max(0, min(255, base[0] + noise)),
                max(0, min(255, base[1] + noise)),
                max(0, min(255, base[2] + noise)),
            )
