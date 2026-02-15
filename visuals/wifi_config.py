"""
WiFi Configuration Utility
===========================
Configure WiFi using the arcade's d-pad + 2 buttons on the 64x64 LED display.

Screens:
  SCAN      - Discover and list SSIDs
  PASSWORD  - Scroll-wheel character entry
  CONNECTING - Animated wait
  RESULT    - Success/failure feedback

Controls:
  Up/Down   - Navigate list / cycle characters
  Left      - (PASSWORD) backspace
  Right     - (PASSWORD) confirm char, advance
  Action    - Select / Connect / Back
"""

import shutil
import subprocess
import socket
import threading
from . import Visual, Display, Colors, GRID_SIZE

# Character set for password entry (space included)
CHARS = (
    'abcdefghijklmnopqrstuvwxyz'
    'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    '0123456789'
    '!@#$%&*_-+.()~ '
)

# Auto-repeat timing (matches menu behavior)
_REPEAT_DELAY = 0.4    # seconds before repeat starts
_REPEAT_FAST = 0.06    # fastest repeat interval
_REPEAT_SLOW = 0.18    # initial repeat interval
_REPEAT_RAMP = 1.5     # seconds to reach fastest

# State constants
_SCAN = 0
_PASSWORD = 1
_SSID_ENTRY = 2
_CONNECTING = 3
_RESULT = 4

# Colors
_TITLE_COLOR = (0, 180, 255)
_HIGHLIGHT_COLOR = (255, 220, 0)
_DIM = (80, 80, 80)
_SUCCESS = (0, 200, 60)
_FAIL = (220, 40, 40)
_WHITE = (200, 200, 200)
_CURSOR_COLOR = (255, 255, 255)


class WiFiConfig(Visual):
    name = "WIFI"
    description = "Configure WiFi"
    category = "utility"

    def __init__(self, display: Display):
        self._has_nmcli = shutil.which('nmcli') is not None
        super().__init__(display)

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    def reset(self):
        self.time = 0.0
        self._state = _SCAN
        # Scan screen
        self._networks = []       # list of (ssid, signal_pct)
        self._scan_cursor = 0
        self._scroll_offset = 0
        self._scanning = False
        self._scan_thread = None
        # Password / SSID-entry screen
        self._selected_ssid = ''
        self._password = []        # list of chars
        self._char_idx = 0         # index into CHARS
        self._pw_scroll = 0        # horizontal scroll for long passwords
        # Connection
        self._connect_thread = None
        self._connecting = False
        self._connect_result = None  # True/False/None
        self._result_ip = ''
        self._result_timer = 0.0
        # Auto-repeat scroll state
        self._scroll_dir = 0       # -1=up, +1=down
        self._scroll_held = 0.0    # how long held
        self._scroll_accum = 0.0   # accumulator for repeat timing
        self._input_held_up = False
        self._input_held_down = False
        # Dot animation
        self._dot_timer = 0.0
        # Current IP for status line
        self._current_ip = self._get_ip()
        # Kick off first scan
        self._start_scan()

    # ------------------------------------------------------------------
    # Networking helpers
    # ------------------------------------------------------------------

    def _get_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0.1)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return ''

    def _start_scan(self):
        if self._scanning:
            return
        self._scanning = True
        t = threading.Thread(target=self._scan_worker, daemon=True)
        t.start()
        self._scan_thread = t

    def _scan_worker(self):
        try:
            networks = self._do_scan()
        except Exception:
            networks = []
        # Deduplicate, sort by signal descending
        seen = {}
        for ssid, sig in networks:
            if ssid and (ssid not in seen or sig > seen[ssid]):
                seen[ssid] = sig
        result = sorted(seen.items(), key=lambda x: -x[1])
        self._networks = result
        self._scanning = False

    def _do_scan(self):
        if not self._has_nmcli:
            # Desktop mock
            return [
                ('HomeNetwork', 85),
                ('Neighbors_5G', 62),
                ('CoffeeShop', 45),
                ('xfinitywifi', 30),
                ('NETGEAR-Guest', 20),
            ]
        try:
            out = subprocess.check_output(
                ['nmcli', '-t', '-f', 'SSID,SIGNAL', 'dev', 'wifi', 'list',
                 '--rescan', 'yes'],
                timeout=15, text=True, stderr=subprocess.DEVNULL
            )
            results = []
            for line in out.strip().split('\n'):
                if ':' in line:
                    parts = line.rsplit(':', 1)
                    ssid = parts[0].strip()
                    try:
                        sig = int(parts[1].strip())
                    except ValueError:
                        sig = 0
                    if ssid:
                        results.append((ssid, sig))
            return results
        except Exception:
            return []

    def _start_connect(self, ssid, password):
        self._state = _CONNECTING
        self._connecting = True
        self._connect_result = None
        self._dot_timer = 0.0
        t = threading.Thread(target=self._connect_worker,
                             args=(ssid, password), daemon=True)
        t.start()
        self._connect_thread = t

    def _connect_worker(self, ssid, password):
        try:
            success = self._do_connect(ssid, password)
        except Exception:
            success = False
        if success:
            self._result_ip = self._get_ip()
        self._connect_result = success
        self._connecting = False

    def _do_connect(self, ssid, password):
        if not self._has_nmcli:
            import time
            time.sleep(2.0)
            return True
        try:
            subprocess.check_call(
                ['nmcli', 'dev', 'wifi', 'connect', ssid,
                 'password', password],
                timeout=30, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def handle_input(self, input_state) -> bool:
        # Track held directions for auto-repeat in update()
        self._input_held_up = input_state.up
        self._input_held_down = input_state.down

        if self._state == _SCAN:
            return self._handle_scan(input_state)
        elif self._state == _PASSWORD:
            return self._handle_password(input_state)
        elif self._state == _SSID_ENTRY:
            return self._handle_ssid_entry(input_state)
        elif self._state == _CONNECTING:
            return True  # swallow input while connecting
        elif self._state == _RESULT:
            return self._handle_result(input_state)
        return False

    def _step_up_down(self, direction):
        """Apply one scroll step in the given direction (-1=up, +1=down).
        Works for whichever screen is active."""
        if self._state == _SCAN:
            total = len(self._networks) + 1
            self._scan_cursor = (self._scan_cursor + direction) % total
        elif self._state in (_PASSWORD, _SSID_ENTRY):
            self._char_idx = (self._char_idx + direction) % len(CHARS)

    def _handle_scan(self, inp):
        if inp.up_pressed:
            self._step_up_down(-1)
            self._scroll_dir = -1
            self._scroll_held = 0.0
            self._scroll_accum = 0.0
            return True
        if inp.down_pressed:
            self._step_up_down(1)
            self._scroll_dir = 1
            self._scroll_held = 0.0
            self._scroll_accum = 0.0
            return True
        if inp.action_l or inp.action_r:
            if self._scan_cursor >= len(self._networks):
                # OTHER... → manual SSID entry
                self._password = []
                self._char_idx = 0
                self._pw_scroll = 0
                self._state = _SSID_ENTRY
            else:
                ssid, _ = self._networks[self._scan_cursor]
                self._selected_ssid = ssid
                self._password = []
                self._char_idx = 0
                self._pw_scroll = 0
                self._state = _PASSWORD
            self._scroll_dir = 0
            return True
        return False

    def _handle_password(self, inp):
        if inp.up_pressed:
            self._step_up_down(-1)
            self._scroll_dir = -1
            self._scroll_held = 0.0
            self._scroll_accum = 0.0
            return True
        if inp.down_pressed:
            self._step_up_down(1)
            self._scroll_dir = 1
            self._scroll_held = 0.0
            self._scroll_accum = 0.0
            return True
        if inp.right_pressed:
            # Confirm current char and advance
            self._password.append(CHARS[self._char_idx])
            self._char_idx = 0
            return True
        if inp.left_pressed:
            # Backspace
            if self._password:
                self._password.pop()
            else:
                # Back to scan
                self._state = _SCAN
            return True
        if inp.action_l or inp.action_r:
            # Include the currently selected character, then connect
            self._password.append(CHARS[self._char_idx])
            pw = ''.join(self._password)
            self._start_connect(self._selected_ssid, pw)
            return True
        return False

    def _handle_ssid_entry(self, inp):
        # Same scroll-wheel as password, but building SSID string
        if inp.up_pressed:
            self._step_up_down(-1)
            self._scroll_dir = -1
            self._scroll_held = 0.0
            self._scroll_accum = 0.0
            return True
        if inp.down_pressed:
            self._step_up_down(1)
            self._scroll_dir = 1
            self._scroll_held = 0.0
            self._scroll_accum = 0.0
            return True
        if inp.right_pressed:
            self._password.append(CHARS[self._char_idx])
            self._char_idx = 0
            return True
        if inp.left_pressed:
            if self._password:
                self._password.pop()
            else:
                self._state = _SCAN
            return True
        if inp.action_l or inp.action_r:
            # Include current char, then move to password
            self._password.append(CHARS[self._char_idx])
            self._selected_ssid = ''.join(self._password)
            self._password = []
            self._char_idx = 0
            self._pw_scroll = 0
            if self._selected_ssid:
                self._state = _PASSWORD
            return True
        return False

    def _handle_result(self, inp):
        if inp.action_l or inp.action_r:
            if self._connect_result:
                # Success → back to menu
                self.wants_exit = True
            else:
                # Failure → back to password
                self._state = _PASSWORD
            return True
        return False

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float):
        self.time += dt
        self._dot_timer += dt

        # Auto-repeat for held up/down (matches menu scroll acceleration)
        if self._scroll_dir != 0:
            still_held = ((self._scroll_dir == -1 and self._input_held_up) or
                          (self._scroll_dir == 1 and self._input_held_down))
            if still_held:
                self._scroll_held += dt
                if self._scroll_held >= _REPEAT_DELAY:
                    t_accel = min(self._scroll_held - _REPEAT_DELAY, _REPEAT_RAMP)
                    interval = _REPEAT_SLOW - ((_REPEAT_SLOW - _REPEAT_FAST) * t_accel / _REPEAT_RAMP)
                    self._scroll_accum += dt
                    while self._scroll_accum >= interval:
                        self._scroll_accum -= interval
                        self._step_up_down(self._scroll_dir)
            else:
                self._scroll_dir = 0
                self._scroll_held = 0.0
                self._scroll_accum = 0.0

        if self._state == _CONNECTING and not self._connecting:
            # Thread finished
            self._state = _RESULT
            self._result_timer = 0.0

        if self._state == _RESULT and self._connect_result:
            self._result_timer += dt
            if self._result_timer > 3.0:
                self.wants_exit = True

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self):
        self.display.clear()
        if self._state == _SCAN:
            self._draw_scan()
        elif self._state == _PASSWORD:
            self._draw_password()
        elif self._state == _SSID_ENTRY:
            self._draw_ssid_entry()
        elif self._state == _CONNECTING:
            self._draw_connecting()
        elif self._state == _RESULT:
            self._draw_result()

    @staticmethod
    def _char_label(ch):
        """Display label for a character — 'SPC' for space, char otherwise."""
        return 'SPC' if ch == ' ' else ch

    def _draw_char_wheel(self, d, y_start, n_visible=5):
        """Draw the character selection wheel centered on self._char_idx."""
        half = n_visible // 2
        for offset in range(-half, half + 1):
            ci = (self._char_idx + offset) % len(CHARS)
            ch = self._char_label(CHARS[ci])
            wy = y_start + (offset + half) * 7
            if wy < 0 or wy > 60:
                continue
            col = _HIGHLIGHT_COLOR if offset == 0 else _DIM
            if offset == 0:
                d.draw_rect(0, wy - 1, 64, 7, (30, 30, 60))
                d.draw_text_raw(10, wy, '> ' + ch + ' <', col)
            else:
                d.draw_text_raw(14, wy, ch, col)

    def _draw_scan(self):
        d = self.display
        # Title
        d.draw_text_small(2, 1, 'WIFI', _TITLE_COLOR)
        # Status line
        if self._current_ip:
            d.draw_text_small(22, 1, self._current_ip, _SUCCESS)
        else:
            d.draw_text_small(22, 1, 'NO CONN', _FAIL)
        d.draw_line(0, 7, 63, 7, _DIM)

        # Network list — 7 visible rows (y=9..51, 7px each)
        max_visible = 7
        total = len(self._networks) + 1
        # Scroll to keep cursor visible
        if self._scan_cursor < self._scroll_offset:
            self._scroll_offset = self._scan_cursor
        if self._scan_cursor >= self._scroll_offset + max_visible:
            self._scroll_offset = self._scan_cursor - max_visible + 1

        for i in range(max_visible):
            idx = self._scroll_offset + i
            if idx >= total:
                break
            row_y = 9 + i * 7
            selected = (idx == self._scan_cursor)
            if selected:
                d.draw_rect(0, row_y, 64, 7, (30, 30, 60))

            if idx < len(self._networks):
                ssid, sig = self._networks[idx]
                # Truncate SSID to fit (max ~12 chars at 4px each = 48px, leave room for bars)
                max_chars = 12
                label = ssid[:max_chars]
                col = _HIGHLIGHT_COLOR if selected else _WHITE
                d.draw_text_small(2, row_y + 1, label, col)
                # Signal bars (1-4 dots) at right edge
                bars = max(1, min(4, sig // 25 + 1))
                for b in range(bars):
                    bx = 58 + b
                    by = row_y + 5 - b
                    d.set_pixel(bx, by, _SUCCESS if selected else _DIM)
            else:
                # OTHER...
                col = _HIGHLIGHT_COLOR if selected else _WHITE
                d.draw_text_small(2, row_y + 1, 'OTHER...', col)

        # Scanning indicator
        if self._scanning:
            frame = int(self._dot_timer * 3) % 4
            dots = '.' * (frame + 1)
            d.draw_text_small(2, 58, 'SCAN' + dots, _DIM)

        # Scroll indicators
        if self._scroll_offset > 0:
            d.set_pixel(62, 8, _DIM)
        if self._scroll_offset + max_visible < total:
            d.set_pixel(62, 57, _DIM)

    def _draw_password(self):
        d = self.display
        # SSID header
        label = self._selected_ssid[:15]
        d.draw_text_small(2, 1, label, _TITLE_COLOR)
        d.draw_line(0, 7, 63, 7, _DIM)

        # Password field
        pw_str = ''.join(self._password)
        # Add blinking cursor character
        cursor_char = CHARS[self._char_idx]
        blink = int(self.time * 3) % 2 == 0

        # Calculate visible window (max ~14 chars fit at 4px)
        max_vis = 14
        display_str = pw_str + (cursor_char if blink else '_')
        if len(display_str) > max_vis:
            display_str = display_str[len(display_str) - max_vis:]

        d.draw_text_raw(2, 12, display_str, _WHITE)

        # Underline for cursor position
        cursor_x = min(len(self._password), max_vis - 1) * 4 + 2
        d.draw_line(cursor_x, 18, cursor_x + 2, 18, _CURSOR_COLOR)

        # Character wheel — show 5 chars centered on current
        d.draw_text_small(2, 24, 'CHAR:', _DIM)
        self._draw_char_wheel(d, 32)

        # Case/region indicator at bottom
        c = CHARS[self._char_idx]
        if c == ' ':
            indicator = 'SPC'
        elif c.islower():
            indicator = 'abc'
        elif c.isupper():
            indicator = 'ABC'
        elif c.isdigit():
            indicator = '123'
        else:
            indicator = '!@#'
        d.draw_text_raw(2, 58, indicator, _DIM)

        # Hint: connect
        pw_len = len(self._password)
        if pw_len > 0:
            d.draw_text_small(34, 58, 'BTN:GO', _DIM)

    def _draw_ssid_entry(self):
        d = self.display
        d.draw_text_small(2, 1, 'ENTER SSID', _TITLE_COLOR)
        d.draw_line(0, 7, 63, 7, _DIM)

        # Current SSID so far
        ssid_str = ''.join(self._password)
        cursor_char = CHARS[self._char_idx]
        blink = int(self.time * 3) % 2 == 0
        max_vis = 14
        display_str = ssid_str + (cursor_char if blink else '_')
        if len(display_str) > max_vis:
            display_str = display_str[len(display_str) - max_vis:]
        d.draw_text_raw(2, 12, display_str, _WHITE)

        cursor_x = min(len(self._password), max_vis - 1) * 4 + 2
        d.draw_line(cursor_x, 18, cursor_x + 2, 18, _CURSOR_COLOR)

        # Character wheel
        self._draw_char_wheel(d, 24)

        d.draw_text_small(30, 58, 'BTN:OK', _DIM)

    def _draw_connecting(self):
        d = self.display
        frame = int(self._dot_timer * 2) % 4
        dots = '.' * (frame + 1) + ' ' * (3 - frame)
        d.draw_text_small(2, 24, 'CONNECTING', _TITLE_COLOR)
        d.draw_text_small(2, 32, dots, _WHITE)
        # Show SSID
        label = self._selected_ssid[:15]
        d.draw_text_small(2, 14, label, _DIM)

    def _draw_result(self):
        d = self.display
        if self._connect_result:
            d.draw_text_small(2, 18, 'CONNECTED!', _SUCCESS)
            if self._result_ip:
                d.draw_text_small(2, 28, self._result_ip, _WHITE)
            # Countdown hint
            remaining = max(0, 3.0 - self._result_timer)
            d.draw_text_small(2, 40, 'OK', _DIM)
        else:
            d.draw_text_small(2, 18, 'FAILED', _FAIL)
            label = self._selected_ssid[:15]
            d.draw_text_small(2, 28, label, _DIM)
            d.draw_text_small(2, 40, 'BTN:RETRY', _WHITE)
            d.draw_text_small(2, 50, 'LEFT:BACK', _DIM)
