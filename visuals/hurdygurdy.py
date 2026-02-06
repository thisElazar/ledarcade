"""
Hurdy Gurdy
===========
Medieval crank-driven string instrument. A rosined wheel rotates continuously,
bowing the strings. Keys press tangents against melody strings to change pitch
while drone strings sound continuously.

The hurdy gurdy works by:
1. A rosined wheel (like a violin bow) continuously rotates against the strings
2. Drone strings always sound when the wheel turns
3. Melody strings are shortened by pressing keys that slide tangents against them
4. Each key produces a different pitch by changing the vibrating length

Controls:
  Left/Right - Adjust tempo (6 levels)
"""

import math
from . import Visual, Display, Colors, GRID_SIZE


# --- Color Palette ---

# Steel gray (for wheel, strings)
STEEL_GRAY = (180, 180, 190)
STEEL_BRIGHT = (220, 220, 230)
STEEL_DARK = (140, 140, 150)

# Dark iron (for body structure)
DARK_IRON = (80, 80, 90)
DARK_IRON_LIGHT = (100, 100, 110)
DARK_IRON_DARK = (50, 50, 60)

# Brass/gold (for keys, decorations)
BRASS = (200, 170, 50)
BRASS_BRIGHT = (230, 200, 70)
BRASS_DIM = (150, 125, 35)

# Copper (for strings, accents)
COPPER = (200, 120, 60)
COPPER_BRIGHT = (230, 150, 80)
COPPER_DIM = (150, 90, 45)

# Wood body
WOOD_MAIN = (100, 65, 30)
WOOD_LIGHT = (130, 85, 40)
WOOD_DARK = (70, 45, 20)
WOOD_EDGE = (50, 30, 15)

# Rosin glow on wheel
ROSIN_GLOW = (255, 240, 200)
ROSIN_DIM = (200, 180, 140)

# String vibration flash
STRING_FLASH = (255, 255, 220)

# Background
BG_COLOR = (15, 12, 10)

# HUD
HUD_COLOR = (160, 160, 170)

# --- Layout Constants ---

# Wheel (the bow that turns)
WHEEL_CX = 48
WHEEL_CY = 40
WHEEL_R = 9

# Crank handle
CRANK_R = 6
CRANK_HANDLE_LEN = 4

# String positions (vertical y-positions where strings cross the wheel)
# Drone strings on edges, melody strings in middle
STRING_Y_DRONE_TOP = WHEEL_CY - 6
STRING_Y_MELODY_1 = WHEEL_CY - 2
STRING_Y_MELODY_2 = WHEEL_CY + 2
STRING_Y_DRONE_BOT = WHEEL_CY + 6

STRING_LEFT = 4
STRING_RIGHT = WHEEL_CX - 1  # strings go from pegbox to wheel

# Keybox (where tangent keys are)
KEYBOX_LEFT = 18
KEYBOX_RIGHT = 35
KEYBOX_TOP = WHEEL_CY - 10
KEYBOX_BOTTOM = WHEEL_CY + 10

# Keys (tangent levers)
NUM_KEYS = 8
KEY_WIDTH = 2
KEY_SPACING = (KEYBOX_RIGHT - KEYBOX_LEFT - NUM_KEYS * KEY_WIDTH) // (NUM_KEYS - 1) + KEY_WIDTH

# Pegbox (left end where strings attach)
PEGBOX_LEFT = 2
PEGBOX_RIGHT = 10
PEGBOX_TOP = WHEEL_CY - 10
PEGBOX_BOTTOM = WHEEL_CY + 10

# Body outline
BODY_TOP = 20
BODY_BOTTOM = 56
BODY_LEFT = 2
BODY_RIGHT = 60

# Speed levels (notes per minute)
SPEED_NPMS = [30, 45, 60, 80, 100, 120]

# Folk melody (relative pitch indices 0-7 for the 8 keys)
# A simple medieval folk tune pattern
FOLK_MELODY = [
    0, 2, 4, 5, 4, 2, 0, 0,
    2, 4, 5, 7, 5, 4, 2, 2,
    4, 5, 7, 5, 4, 2, 4, 0,
    2, 0, 2, 4, 2, 0, 0, 0,
]


class HurdyGurdy(Visual):
    name = "HURDY GURDY"
    description = "Crank string instrument"
    category = "music"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.wheel_angle = 0.0
        self.speed_level = 3

        # Current note being played
        self.melody_index = 0
        self.note_time = 0.0
        self.current_key = 0  # which key is pressed (0-7)

        # String vibration energies
        self.drone_top_energy = 0.0
        self.drone_bot_energy = 0.0
        self.melody_energy = 0.0

        # Vibration phases (for oscillation)
        self.drone_top_phase = 0.0
        self.drone_bot_phase = 0.0
        self.melody_phase = 0.0

        # Key states (how far each key is pressed, 0.0-1.0)
        self.key_press = [0.0] * NUM_KEYS

    def handle_input(self, input_state):
        consumed = False
        if input_state.right_pressed:
            self.speed_level = min(6, self.speed_level + 1)
            consumed = True
        elif input_state.left_pressed:
            self.speed_level = max(1, self.speed_level - 1)
            consumed = True
        return consumed

    def update(self, dt):
        self.time += dt

        # Wheel rotation speed based on tempo
        npm = SPEED_NPMS[self.speed_level - 1]
        # Wheel makes one full rotation per beat (visual effect)
        wheel_speed = npm / 60.0 * 2.0 * math.pi * 0.5
        self.wheel_angle += wheel_speed * dt

        # Note timing
        note_duration = 60.0 / npm
        self.note_time += dt

        if self.note_time >= note_duration:
            self.note_time -= note_duration
            self.melody_index = (self.melody_index + 1) % len(FOLK_MELODY)
            self.current_key = FOLK_MELODY[self.melody_index]

        # Animate key presses
        for i in range(NUM_KEYS):
            target = 1.0 if i == self.current_key else 0.0
            # Smooth key movement
            diff = target - self.key_press[i]
            self.key_press[i] += diff * min(1.0, dt * 15.0)

        # Drone strings always vibrate when wheel is turning
        wheel_turning = wheel_speed > 0.1
        if wheel_turning:
            self.drone_top_energy = min(1.0, self.drone_top_energy + dt * 8.0)
            self.drone_bot_energy = min(1.0, self.drone_bot_energy + dt * 8.0)
        else:
            self.drone_top_energy *= (1.0 - dt * 3.0)
            self.drone_bot_energy *= (1.0 - dt * 3.0)

        # Melody string vibrates when a key is pressed
        if max(self.key_press) > 0.5:
            self.melody_energy = min(1.0, self.melody_energy + dt * 10.0)
        else:
            self.melody_energy *= (1.0 - dt * 5.0)

        # Update vibration phases
        self.drone_top_phase += dt * 20.0
        self.drone_bot_phase += dt * 18.0
        self.melody_phase += dt * 25.0

    def draw(self):
        d = self.display
        d.clear(BG_COLOR)

        self._draw_body(d)
        self._draw_pegbox(d)
        self._draw_keybox(d)
        self._draw_wheel(d)
        self._draw_crank(d)
        self._draw_strings(d)
        self._draw_keys(d)
        self._draw_hud(d)

    def _draw_body(self, d):
        """Draw the wooden body of the hurdy gurdy."""
        # Main body shape (elongated oval/rectangular with rounded ends)
        d.draw_rect(BODY_LEFT, BODY_TOP, BODY_RIGHT - BODY_LEFT, BODY_BOTTOM - BODY_TOP, WOOD_MAIN)

        # Top edge highlight
        d.draw_line(BODY_LEFT, BODY_TOP, BODY_RIGHT - 1, BODY_TOP, WOOD_LIGHT)

        # Bottom edge shadow
        d.draw_line(BODY_LEFT, BODY_BOTTOM - 1, BODY_RIGHT - 1, BODY_BOTTOM - 1, WOOD_EDGE)

        # Side edges
        d.draw_line(BODY_LEFT, BODY_TOP, BODY_LEFT, BODY_BOTTOM - 1, WOOD_EDGE)
        d.draw_line(BODY_RIGHT - 1, BODY_TOP, BODY_RIGHT - 1, BODY_BOTTOM - 1, WOOD_DARK)

        # Sound hole (decorative circle)
        hole_cx = 12
        hole_cy = BODY_BOTTOM - 8
        hole_r = 3
        d.draw_circle(hole_cx, hole_cy, hole_r, WOOD_DARK, filled=False)
        d.draw_circle(hole_cx, hole_cy, hole_r - 1, WOOD_EDGE, filled=True)

        # Decorative rosette around sound hole
        for i in range(8):
            angle = i * math.pi / 4.0
            rx = hole_cx + int((hole_r + 1) * math.cos(angle))
            ry = hole_cy + int((hole_r + 1) * math.sin(angle))
            d.set_pixel(rx, ry, BRASS_DIM)

    def _draw_pegbox(self, d):
        """Draw the pegbox where strings attach on the left."""
        # Pegbox housing
        d.draw_rect(PEGBOX_LEFT, PEGBOX_TOP, PEGBOX_RIGHT - PEGBOX_LEFT,
                   PEGBOX_BOTTOM - PEGBOX_TOP, DARK_IRON)
        d.draw_line(PEGBOX_LEFT, PEGBOX_TOP, PEGBOX_RIGHT - 1, PEGBOX_TOP, DARK_IRON_LIGHT)
        d.draw_line(PEGBOX_RIGHT - 1, PEGBOX_TOP, PEGBOX_RIGHT - 1, PEGBOX_BOTTOM - 1, DARK_IRON_DARK)

        # Tuning pegs (brass knobs)
        peg_positions = [
            (PEGBOX_LEFT + 2, STRING_Y_DRONE_TOP),
            (PEGBOX_LEFT + 2, STRING_Y_MELODY_1),
            (PEGBOX_LEFT + 2, STRING_Y_MELODY_2),
            (PEGBOX_LEFT + 2, STRING_Y_DRONE_BOT),
        ]
        for px, py in peg_positions:
            d.set_pixel(px, py, BRASS_BRIGHT)
            d.set_pixel(px - 1, py, BRASS_DIM)

    def _draw_keybox(self, d):
        """Draw the keybox housing."""
        # Keybox frame
        d.draw_rect(KEYBOX_LEFT, KEYBOX_TOP, KEYBOX_RIGHT - KEYBOX_LEFT,
                   KEYBOX_BOTTOM - KEYBOX_TOP, DARK_IRON, filled=False)

        # Fill keybox interior
        d.draw_rect(KEYBOX_LEFT + 1, KEYBOX_TOP + 1,
                   KEYBOX_RIGHT - KEYBOX_LEFT - 2,
                   KEYBOX_BOTTOM - KEYBOX_TOP - 2, WOOD_DARK)

    def _draw_wheel(self, d):
        """Draw the rosined wheel that bows the strings."""
        cx, cy, r = WHEEL_CX, WHEEL_CY, WHEEL_R

        # Wheel cover/housing (partial arc on right side)
        for angle_deg in range(-60, 61, 10):
            angle = math.radians(angle_deg)
            hx = cx + int((r + 2) * math.cos(angle))
            hy = cy + int((r + 2) * math.sin(angle))
            d.set_pixel(hx, hy, DARK_IRON)

        # Wheel body (filled circle with spoke pattern)
        for py in range(cy - r, cy + r + 1):
            for px in range(cx - r, cx + r + 1):
                dx = px - cx
                dy = py - cy
                dist_sq = dx * dx + dy * dy
                if dist_sq <= r * r:
                    dist = math.sqrt(dist_sq)
                    if dist > r - 1.5:
                        # Rim
                        d.set_pixel(px, py, STEEL_BRIGHT)
                    elif dist > r - 2.5:
                        d.set_pixel(px, py, STEEL_GRAY)
                    else:
                        # Inner wheel with rosin coating
                        d.set_pixel(px, py, ROSIN_DIM)

        # Rotating spoke pattern
        num_spokes = 6
        for s in range(num_spokes):
            angle = self.wheel_angle + s * 2.0 * math.pi / num_spokes
            for dist in range(2, r - 1):
                sx = cx + int(dist * math.cos(angle))
                sy = cy + int(dist * math.sin(angle))
                if 0 <= sx < GRID_SIZE and 0 <= sy < GRID_SIZE:
                    d.set_pixel(sx, sy, STEEL_DARK)

        # Wheel axle (center hub)
        d.set_pixel(cx, cy, BRASS_BRIGHT)
        for ddx, ddy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            d.set_pixel(cx + ddx, cy + ddy, BRASS)

        # Contact points with strings (bright spots where wheel touches strings)
        contact_x = cx - r + 1
        contact_points = [STRING_Y_DRONE_TOP, STRING_Y_MELODY_1, STRING_Y_MELODY_2, STRING_Y_DRONE_BOT]
        for contact_y in contact_points:
            # Glow effect based on vibration
            d.set_pixel(contact_x, contact_y, ROSIN_GLOW)
            d.set_pixel(contact_x - 1, contact_y, ROSIN_DIM)

    def _draw_crank(self, d):
        """Draw the crank handle that turns the wheel."""
        cx, cy = WHEEL_CX, WHEEL_CY

        # Crank arm rotates with wheel
        crank_x = cx + int(CRANK_R * math.cos(self.wheel_angle))
        crank_y = cy + int(CRANK_R * math.sin(self.wheel_angle))

        # Crank arm (connects wheel center to handle pivot)
        d.draw_line(cx, cy, crank_x, crank_y, DARK_IRON_LIGHT)

        # Handle pivot
        d.set_pixel(crank_x, crank_y, BRASS_BRIGHT)

        # Handle (perpendicular to crank arm, wooden)
        # Calculate perpendicular direction
        perp_angle = self.wheel_angle + math.pi / 2.0
        for i in range(CRANK_HANDLE_LEN):
            hx = crank_x + int(i * math.cos(perp_angle) * 0.8)
            hy = crank_y + int(i * math.sin(perp_angle) * 0.8)
            if 0 <= hx < GRID_SIZE and 0 <= hy < GRID_SIZE:
                d.set_pixel(hx, hy, WOOD_LIGHT if i > 0 else BRASS)

    def _draw_strings(self, d):
        """Draw the strings with vibration effect."""
        wheel_contact_x = WHEEL_CX - WHEEL_R + 1

        # Drone string (top) - always vibrating
        self._draw_single_string(d, STRING_Y_DRONE_TOP, STRING_LEFT, wheel_contact_x,
                                  self.drone_top_energy, self.drone_top_phase, COPPER)

        # Melody strings (middle two)
        # Find where the active key's tangent touches the string
        active_key = self.current_key
        key_x = KEYBOX_LEFT + 2 + active_key * KEY_SPACING // NUM_KEYS * NUM_KEYS // (NUM_KEYS - 1)
        key_x = min(key_x, KEYBOX_RIGHT - 3)

        # Melody string 1
        tangent_x_1 = key_x if self.key_press[active_key] > 0.5 else wheel_contact_x
        self._draw_single_string(d, STRING_Y_MELODY_1, STRING_LEFT, tangent_x_1,
                                  self.melody_energy, self.melody_phase, STEEL_GRAY)
        # Draw from tangent to wheel
        if tangent_x_1 < wheel_contact_x:
            self._draw_single_string(d, STRING_Y_MELODY_1, tangent_x_1, wheel_contact_x,
                                      self.melody_energy * 0.3, self.melody_phase, STEEL_DARK)

        # Melody string 2
        self._draw_single_string(d, STRING_Y_MELODY_2, STRING_LEFT, tangent_x_1,
                                  self.melody_energy, self.melody_phase * 1.1, STEEL_GRAY)
        if tangent_x_1 < wheel_contact_x:
            self._draw_single_string(d, STRING_Y_MELODY_2, tangent_x_1, wheel_contact_x,
                                      self.melody_energy * 0.3, self.melody_phase, STEEL_DARK)

        # Drone string (bottom) - always vibrating
        self._draw_single_string(d, STRING_Y_DRONE_BOT, STRING_LEFT, wheel_contact_x,
                                  self.drone_bot_energy, self.drone_bot_phase, COPPER)

    def _draw_single_string(self, d, base_y, x_start, x_end, energy, phase, color):
        """Draw a single string with vibration effect."""
        string_len = x_end - x_start
        if string_len <= 0:
            return

        for x in range(x_start, x_end + 1):
            # Vibration amplitude varies along string (max at center)
            pos_frac = (x - x_start) / max(1, string_len)
            # Sinusoidal shape - max amplitude at center
            amp_factor = math.sin(pos_frac * math.pi)

            # Vibration offset
            vibration = energy * amp_factor * math.sin(phase + pos_frac * 6.0)
            dy = int(round(vibration * 1.5))

            y = base_y + dy
            if 0 <= y < GRID_SIZE:
                # Brighter color when vibrating strongly
                if energy > 0.7 and abs(vibration) > 0.3:
                    final_color = STRING_FLASH
                elif energy > 0.3:
                    # Blend toward bright
                    blend = energy * 0.5
                    final_color = (
                        int(color[0] + (STEEL_BRIGHT[0] - color[0]) * blend),
                        int(color[1] + (STEEL_BRIGHT[1] - color[1]) * blend),
                        int(color[2] + (STEEL_BRIGHT[2] - color[2]) * blend),
                    )
                else:
                    final_color = color
                d.set_pixel(x, y, final_color)

    def _draw_keys(self, d):
        """Draw the tangent keys."""
        # Keys are arranged vertically in the keybox
        # Each key slides horizontally to press against the melody strings

        for i in range(NUM_KEYS):
            key_base_x = KEYBOX_LEFT + 2
            key_y = KEYBOX_TOP + 2 + i * (KEYBOX_BOTTOM - KEYBOX_TOP - 4) // (NUM_KEYS - 1)

            # Key slides right when pressed
            press_amount = self.key_press[i]
            key_extend = int(press_amount * 8)  # max extension

            # Key body (horizontal bar)
            key_end_x = key_base_x + 6 + key_extend

            # Draw key
            for kx in range(key_base_x, min(key_end_x, KEYBOX_RIGHT - 1)):
                # Key color - brass, brighter when pressed
                if press_amount > 0.5:
                    color = BRASS_BRIGHT
                else:
                    color = BRASS_DIM
                d.set_pixel(kx, key_y, color)

            # Tangent tip (the part that touches the string)
            if key_extend > 2:
                tangent_x = key_end_x - 1
                if KEYBOX_LEFT < tangent_x < KEYBOX_RIGHT:
                    d.set_pixel(tangent_x, key_y, STEEL_BRIGHT)

            # Key cap (left end, where player presses)
            d.set_pixel(key_base_x - 1, key_y, WOOD_LIGHT if press_amount < 0.5 else BRASS_BRIGHT)

    def _draw_hud(self, d):
        """Draw tempo indicator."""
        npm = SPEED_NPMS[self.speed_level - 1]
        d.draw_text_small(2, 2, f"{npm} NPM", HUD_COLOR)

        # Current note indicator (which key)
        note_names = ["C", "D", "E", "F", "G", "A", "B", "C"]
        note_name = note_names[self.current_key]
        d.draw_text_small(2, 8, f"NOTE:{note_name}", HUD_COLOR)
