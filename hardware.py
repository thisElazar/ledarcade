#!/usr/bin/env python3
"""
Hardware Display Driver for LED Arcade
=======================================
Provides Display and Input classes that work with the RGB LED matrix
and GPIO buttons on Raspberry Pi.

Uses the same interface as arcade.py so games work unchanged.
"""

import sys
import time
from typing import Tuple, Optional

# PIL for bulk pixel transfer to LED matrix
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# RGB Matrix library (only available on Pi)
try:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions
    HAS_MATRIX = True
except ImportError:
    HAS_MATRIX = False
    print("Warning: rgbmatrix not found - hardware display unavailable")

# GPIO for buttons (only available on Pi)
try:
    import RPi.GPIO as GPIO
    HAS_GPIO = True
except ImportError:
    HAS_GPIO = False

# Keyboard input fallback
import select
import termios
import tty

# =============================================================================
# CONFIGURATION
# =============================================================================

GRID_SIZE = 64

# Our custom GPIO mapping pins (directly wired, no HAT)
# These match the "led-arcade" hardware mapping we added to the library

# Button GPIO pins (directly connect button between GPIO and GND)
BUTTON_PINS = {
    'up': 19,         # Joystick wired normally on v2
    'down': 25,
    'left': 24,
    'right': 8,
    'action_l': 9,    # Buttons wired reversed: physical right = left
    'action_r': 7,    # physical left = right
}


# =============================================================================
# COLORS (same as arcade.py)
# =============================================================================

class Colors:
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    YELLOW = (255, 255, 0)
    CYAN = (0, 255, 255)
    MAGENTA = (255, 0, 255)
    ORANGE = (255, 128, 0)
    PINK = (255, 128, 128)
    LIME = (128, 255, 0)
    PURPLE = (128, 0, 255)
    GRAY = (128, 128, 128)
    DARK_GRAY = (64, 64, 64)


# =============================================================================
# SHARED 3x5 FONT
# =============================================================================

_FONT_3X5 = {
    'A': ['010', '101', '111', '101', '101'],
    'B': ['110', '101', '110', '101', '110'],
    'C': ['011', '100', '100', '100', '011'],
    'D': ['110', '101', '101', '101', '110'],
    'E': ['111', '100', '110', '100', '111'],
    'F': ['111', '100', '110', '100', '100'],
    'G': ['011', '100', '101', '101', '011'],
    'H': ['101', '101', '111', '101', '101'],
    'I': ['111', '010', '010', '010', '111'],
    'J': ['001', '001', '001', '101', '010'],
    'K': ['101', '110', '100', '110', '101'],
    'L': ['100', '100', '100', '100', '111'],
    'M': ['101', '111', '111', '101', '101'],
    'N': ['101', '111', '111', '111', '101'],
    'O': ['010', '101', '101', '101', '010'],
    'P': ['110', '101', '110', '100', '100'],
    'Q': ['010', '101', '101', '110', '011'],
    'R': ['110', '101', '110', '101', '101'],
    'S': ['011', '100', '010', '001', '110'],
    'T': ['111', '010', '010', '010', '010'],
    'U': ['101', '101', '101', '101', '011'],
    'V': ['101', '101', '101', '010', '010'],
    'W': ['101', '101', '111', '111', '101'],
    'X': ['101', '101', '010', '101', '101'],
    'Y': ['101', '101', '010', '010', '010'],
    'Z': ['111', '001', '010', '100', '111'],
    '0': ['111', '101', '101', '101', '111'],
    '1': ['010', '110', '010', '010', '111'],
    '2': ['110', '001', '010', '100', '111'],
    '3': ['110', '001', '010', '001', '110'],
    '4': ['101', '101', '111', '001', '001'],
    '5': ['111', '100', '110', '001', '110'],
    '6': ['011', '100', '110', '101', '010'],
    '7': ['111', '001', '010', '010', '010'],
    '8': ['010', '101', '010', '101', '010'],
    '9': ['010', '101', '011', '001', '110'],
    ' ': ['000', '000', '000', '000', '000'],
    ':': ['000', '010', '000', '010', '000'],
    '-': ['000', '000', '111', '000', '000'],
    '.': ['000', '000', '000', '000', '010'],
    '!': ['010', '010', '010', '000', '010'],
    '?': ['110', '001', '010', '000', '010'],
    '+': ['000', '010', '111', '010', '000'],
    '>': ['100', '010', '001', '010', '100'],
    '#': ['010', '111', '010', '111', '010'],
    '^': ['010', '101', '000', '000', '000'],
    '/': ['001', '010', '010', '010', '100'],
    # Lowercase
    'a': ['000', '011', '101', '101', '011'],
    'b': ['100', '100', '110', '101', '110'],
    'c': ['000', '011', '100', '100', '011'],
    'd': ['001', '001', '011', '101', '011'],
    'e': ['000', '010', '111', '100', '011'],
    'f': ['001', '010', '110', '010', '010'],
    'g': ['000', '011', '101', '011', '110'],
    'h': ['100', '100', '110', '101', '101'],
    'i': ['010', '000', '010', '010', '010'],
    'j': ['010', '000', '010', '010', '100'],
    'k': ['100', '101', '110', '110', '101'],
    'l': ['110', '010', '010', '010', '010'],
    'm': ['000', '000', '111', '111', '101'],
    'n': ['000', '000', '110', '101', '101'],
    'o': ['000', '000', '010', '101', '010'],
    'p': ['000', '110', '101', '110', '100'],
    'q': ['000', '011', '101', '011', '001'],
    'r': ['000', '000', '011', '100', '100'],
    's': ['000', '011', '010', '010', '110'],
    't': ['010', '010', '111', '010', '011'],
    'u': ['000', '000', '101', '101', '011'],
    'v': ['000', '000', '101', '101', '010'],
    'w': ['000', '000', '101', '111', '111'],
    'x': ['000', '000', '101', '010', '101'],
    'y': ['000', '101', '101', '011', '110'],
    'z': ['000', '000', '111', '010', '111'],
    # Symbols
    '@': ['011', '101', '111', '100', '011'],
    '_': ['000', '000', '000', '000', '111'],
    '$': ['011', '110', '010', '011', '110'],
    '%': ['101', '001', '010', '100', '101'],
    '&': ['010', '101', '010', '101', '011'],
    '*': ['000', '101', '010', '101', '000'],
    '(': ['001', '010', '010', '010', '001'],
    ')': ['100', '010', '010', '010', '100'],
    '=': ['000', '111', '000', '111', '000'],
    '~': ['000', '000', '011', '110', '000'],
    "'": ['010', '010', '000', '000', '000'],
    '"': ['101', '101', '000', '000', '000'],
    ',': ['000', '000', '000', '010', '100'],
    ';': ['000', '010', '000', '010', '100'],
    '<': ['001', '010', '100', '010', '001'],
}

# =============================================================================
# HARDWARE DISPLAY
# =============================================================================

class HardwareDisplay:
    """
    64x64 LED Matrix display driver.
    Drop-in replacement for arcade.py Display class.
    """

    def __init__(self, brightness: int = 80, gpio_slowdown: int = 2, gamma: float = 2.2, toe: float = 0.25):
        if not HAS_MATRIX:
            raise RuntimeError("rgbmatrix library not available")

        options = RGBMatrixOptions()
        options.rows = 64
        options.cols = 64
        options.hardware_mapping = 'led-arcade'
        options.gpio_slowdown = gpio_slowdown
        options.brightness = brightness
        options.drop_privileges = False

        self.matrix = RGBMatrix(options=options)

        # Double-buffered: draw to offscreen canvas, then swap atomically
        self.canvas = self.matrix.CreateFrameCanvas()

        # Flat bytearray framebuffer: RGBRGBRGB... row-major, 3 bytes per pixel
        self._fb = bytearray(GRID_SIZE * GRID_SIZE * 3)
        # Pre-allocated zero buffer for fast black clear
        self._zeros = bytes(GRID_SIZE * GRID_SIZE * 3)

        # Gamma correction with toe lift for shadow detail preservation.
        # Pure gamma (x^2.2) crushes darks too aggressively on LED panels.
        # The toe term [toe * x * (1-x)^2] lifts shadows while fading out
        # in highlights, so colors still pop but grays remain visible.
        # Black (0) and white (255) are pinned. toe=0 gives pure gamma.
        self._gamma_lut = self._build_lut(gamma, toe)

    @staticmethod
    def _build_lut(gamma, toe):
        """Build gamma lookup table with toe lift."""
        return bytes([
            min(255, max(0, int(round(255 * (
                (i / 255) ** gamma + toe * (i / 255) * (1 - i / 255) ** 2
            )))))
            for i in range(256)
        ])

    def set_gamma(self, gamma, toe):
        """Rebuild gamma LUT at runtime. Takes effect on next render()."""
        self._gamma_lut = self._build_lut(gamma, toe)

    def clear(self, color=Colors.BLACK):
        """Clear the display to a solid color."""
        if color[0] == 0 and color[1] == 0 and color[2] == 0:
            self._fb[:] = self._zeros
        else:
            row = bytes(color) * GRID_SIZE
            self._fb[:] = row * GRID_SIZE

    def set_pixel(self, x: int, y: int, color: Tuple[int, int, int]):
        """Set a single pixel. Coordinates are 0-63."""
        if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
            offset = (y * GRID_SIZE + x) * 3
            self._fb[offset] = color[0]
            self._fb[offset + 1] = color[1]
            self._fb[offset + 2] = color[2]

    def get_pixel(self, x: int, y: int) -> Tuple[int, int, int]:
        """Get color of a pixel."""
        if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
            offset = (y * GRID_SIZE + x) * 3
            return (self._fb[offset], self._fb[offset + 1], self._fb[offset + 2])
        return Colors.BLACK

    def draw_rect(self, x: int, y: int, w: int, h: int, color: Tuple[int, int, int], filled: bool = True):
        """Draw a rectangle."""
        for dy in range(h):
            for dx in range(w):
                if filled or dx == 0 or dx == w-1 or dy == 0 or dy == h-1:
                    self.set_pixel(x + dx, y + dy, color)

    def draw_line(self, x0: int, y0: int, x1: int, y1: int, color: Tuple[int, int, int]):
        """Draw a line using Bresenham's algorithm."""
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        while True:
            self.set_pixel(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def draw_circle(self, cx: int, cy: int, r: int, color: Tuple[int, int, int], filled: bool = False):
        """Draw a circle."""
        for y in range(-r, r + 1):
            for x in range(-r, r + 1):
                dist = x*x + y*y
                if filled:
                    if dist <= r*r:
                        self.set_pixel(cx + x, cy + y, color)
                else:
                    if abs(dist - r*r) < r * 2:
                        self.set_pixel(cx + x, cy + y, color)

    def _render_font(self, x, y, text, color):
        """Internal: render glyphs from _FONT_3X5 at (x, y)."""
        cursor = x
        for char in text:
            glyph = _FONT_3X5.get(char)
            if glyph:
                for row_idx, row in enumerate(glyph):
                    for col_idx, pixel in enumerate(row):
                        if pixel == '1':
                            self.set_pixel(cursor + col_idx, y + row_idx, color)
            cursor += 4

    def draw_text_small(self, x: int, y: int, text: str, color: Tuple[int, int, int]):
        """Draw tiny 3x5 pixel text (uppercased). 3 wide + 1 space per char."""
        self._render_font(x, y, text.upper(), color)

    def draw_text_raw(self, x: int, y: int, text: str, color: Tuple[int, int, int]):
        """Draw tiny 3x5 text WITHOUT uppercasing — supports lowercase + symbols."""
        self._render_font(x, y, text, color)

    def render(self):
        """Render the buffer to the LED matrix using bulk SetImage."""
        canvas = self.canvas
        # Apply gamma correction to a copy (keeps _fb at logical values for get_pixel)
        corrected = self._fb.translate(self._gamma_lut)
        if HAS_PIL:
            # Bulk transfer: PIL Image from bytearray, single C call to matrix
            img = Image.frombuffer('RGB', (GRID_SIZE, GRID_SIZE), corrected, 'raw', 'RGB', 0, 1)
            canvas.SetImage(img)
        else:
            # Fallback: per-pixel from flat bytearray (slower)
            for y in range(GRID_SIZE):
                row_offset = y * GRID_SIZE * 3
                for x in range(GRID_SIZE):
                    offset = row_offset + x * 3
                    canvas.SetPixel(x, y, corrected[offset], corrected[offset+1], corrected[offset+2])
        self.canvas = self.matrix.SwapOnVSync(canvas)


# =============================================================================
# INPUT HANDLING
# =============================================================================

class InputState:
    """Tracks the state of all inputs for the current frame."""

    def __init__(self):
        self.reset()

    def reset(self):
        # Directions (held — True while joystick is held)
        self.up = False
        self.down = False
        self.left = False
        self.right = False
        # Directions (pressed — True only on first frame)
        self.up_pressed = False
        self.down_pressed = False
        self.left_pressed = False
        self.right_pressed = False
        # Buttons
        self.action_l = False
        self.action_r = False
        self.action_l_held = False
        self.action_r_held = False

    @property
    def dx(self) -> int:
        return (1 if self.right else 0) - (1 if self.left else 0)

    @property
    def dy(self) -> int:
        return (1 if self.down else 0) - (1 if self.up else 0)

    @property
    def any_direction(self) -> bool:
        return self.up or self.down or self.left or self.right


class KeyboardInput:
    """
    Keyboard input handler for terminal.
    Works over SSH without pygame.
    """

    def __init__(self):
        self.state = InputState()
        self._prev_keys = set()
        self._current_keys = set()
        self._available = False
        self._old_settings = None

        # Try to set up terminal - may fail if no TTY
        try:
            if sys.stdin.isatty():
                self._old_settings = termios.tcgetattr(sys.stdin)
                tty.setcbreak(sys.stdin.fileno())
                self._available = True
        except Exception:
            pass  # No terminal available

    def __del__(self):
        # Restore terminal settings
        if self._old_settings:
            try:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self._old_settings)
            except:
                pass

    def cleanup(self):
        """Restore terminal settings."""
        if self._old_settings:
            try:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self._old_settings)
            except:
                pass

    def _read_keys(self) -> set:
        """Read currently pressed keys without blocking."""
        keys = set()

        if not self._available:
            return keys

        while select.select([sys.stdin], [], [], 0)[0]:
            ch = sys.stdin.read(1)
            if ch == '\x1b':  # Escape sequence
                # Check for arrow keys
                if select.select([sys.stdin], [], [], 0.01)[0]:
                    ch2 = sys.stdin.read(1)
                    if ch2 == '[':
                        if select.select([sys.stdin], [], [], 0.01)[0]:
                            ch3 = sys.stdin.read(1)
                            if ch3 == 'A': keys.add('up')
                            elif ch3 == 'B': keys.add('down')
                            elif ch3 == 'C': keys.add('right')
                            elif ch3 == 'D': keys.add('left')
                else:
                    pass  # Plain escape (no longer mapped)
            elif ch == ' ':
                keys.add('action_l')
            elif ch == 'z' or ch == 'Z':
                keys.add('action_r')
            elif ch == 'w' or ch == 'W':
                keys.add('up')
            elif ch == 's' or ch == 'S':
                keys.add('down')
            elif ch == 'a' or ch == 'A':
                keys.add('left')
            elif ch == 'd' or ch == 'D':
                keys.add('right')

        return keys

    def update(self) -> InputState:
        """Update input state. Call once per frame."""
        self._prev_keys = self._current_keys
        self._current_keys = self._read_keys()

        # Directions (held)
        self.state.up = 'up' in self._current_keys
        self.state.down = 'down' in self._current_keys
        self.state.left = 'left' in self._current_keys
        self.state.right = 'right' in self._current_keys

        # Directions (fresh press)
        self.state.up_pressed = 'up' in self._current_keys and 'up' not in self._prev_keys
        self.state.down_pressed = 'down' in self._current_keys and 'down' not in self._prev_keys
        self.state.left_pressed = 'left' in self._current_keys and 'left' not in self._prev_keys
        self.state.right_pressed = 'right' in self._current_keys and 'right' not in self._prev_keys

        # Buttons (fresh press detection)
        self.state.action_l = 'action_l' in self._current_keys and 'action_l' not in self._prev_keys
        self.state.action_r = 'action_r' in self._current_keys and 'action_r' not in self._prev_keys

        # Held state
        self.state.action_l_held = 'action_l' in self._current_keys
        self.state.action_r_held = 'action_r' in self._current_keys

        return self.state


class GPIOInput:
    """
    GPIO button input handler.
    For physical arcade buttons connected to Pi GPIO.
    """

    def __init__(self):
        if not HAS_GPIO:
            raise RuntimeError("RPi.GPIO not available")

        self.state = InputState()
        self._prev_buttons = {}

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # Set up button pins with pull-up resistors
        for name, pin in BUTTON_PINS.items():
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            self._prev_buttons[name] = False

    def __del__(self):
        try:
            GPIO.cleanup()
        except:
            pass

    def cleanup(self):
        GPIO.cleanup()

    def update(self) -> InputState:
        """Update input state from GPIO buttons."""
        current = {}
        for name, pin in BUTTON_PINS.items():
            # Active low: pressed = GPIO reads LOW
            current[name] = not GPIO.input(pin)

        # Directions (held)
        self.state.up = current['up']
        self.state.down = current['down']
        self.state.left = current['left']
        self.state.right = current['right']

        # Directions (fresh press)
        self.state.up_pressed = current['up'] and not self._prev_buttons['up']
        self.state.down_pressed = current['down'] and not self._prev_buttons['down']
        self.state.left_pressed = current['left'] and not self._prev_buttons['left']
        self.state.right_pressed = current['right'] and not self._prev_buttons['right']

        # Fresh press detection
        self.state.action_l = current['action_l'] and not self._prev_buttons['action_l']
        self.state.action_r = current['action_r'] and not self._prev_buttons['action_r']

        # Held state
        self.state.action_l_held = current['action_l']
        self.state.action_r_held = current['action_r']

        self._prev_buttons = current
        return self.state


# =============================================================================
# COMBINED INPUT (Keyboard + GPIO)
# =============================================================================

class HardwareInput:
    """
    Combined input handler that supports both keyboard and GPIO.
    Keyboard always works (for debugging), GPIO used when available.
    """

    def __init__(self, use_gpio: bool = True):
        self.keyboard = KeyboardInput()
        self.gpio = None

        if use_gpio and HAS_GPIO:
            try:
                self.gpio = GPIOInput()
                print("GPIO buttons enabled")
            except Exception as e:
                print(f"GPIO init failed: {e}, using keyboard only")

        self.state = InputState()

    def cleanup(self):
        self.keyboard.cleanup()
        if self.gpio:
            self.gpio.cleanup()

    def update(self) -> InputState:
        """Update from both keyboard and GPIO, merge results."""
        kb = self.keyboard.update()

        if self.gpio:
            gp = self.gpio.update()
            # Merge: either source can trigger
            self.state.up = kb.up or gp.up
            self.state.down = kb.down or gp.down
            self.state.left = kb.left or gp.left
            self.state.right = kb.right or gp.right
            self.state.up_pressed = kb.up_pressed or gp.up_pressed
            self.state.down_pressed = kb.down_pressed or gp.down_pressed
            self.state.left_pressed = kb.left_pressed or gp.left_pressed
            self.state.right_pressed = kb.right_pressed or gp.right_pressed
            self.state.action_l = kb.action_l or gp.action_l
            self.state.action_r = kb.action_r or gp.action_r
            self.state.action_l_held = kb.action_l_held or gp.action_l_held
            self.state.action_r_held = kb.action_r_held or gp.action_r_held
        else:
            self.state = kb

        return self.state


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("Hardware Display Test")
    print("=" * 40)

    if not HAS_MATRIX:
        print("ERROR: rgbmatrix library not found")
        print("This must run on a Raspberry Pi with the library installed")
        sys.exit(1)

    display = HardwareDisplay()

    # Draw test pattern
    print("Drawing test pattern...")

    # Red corner
    for y in range(32):
        for x in range(32):
            display.set_pixel(x, y, (255, 0, 0))

    # Green corner
    for y in range(32):
        for x in range(32, 64):
            display.set_pixel(x, y, (0, 255, 0))

    # Blue corner
    for y in range(32, 64):
        for x in range(32):
            display.set_pixel(x, y, (0, 0, 255))

    # Yellow corner
    for y in range(32, 64):
        for x in range(32, 64):
            display.set_pixel(x, y, (255, 255, 0))

    # Text
    display.draw_text_small(8, 28, "LED ARCADE", (255, 255, 255))

    display.render()

    print("Test pattern displayed! Press Ctrl+C to exit")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nDone!")
