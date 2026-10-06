"""
Handheld - Game Boy ROMs on a 64x64 LED panel
=============================================
Runs a Game Boy / Game Boy Color ROM in PyBoy (pip install pyboy) and
downscales the 160x144 screen onto the panel. No ROMs ship with the
cabinet: drop your own dumps (.gb / .gbc) into ../gb_roms/, next to the
led-arcade checkout. tools/build_gb_rom.py writes an original test ROM.

Two views: ZOOM crops 128x128 around the sprites and halves it (sharp, but
you see 80% of the screen), FIT squeezes the whole screen to 64x58.

Controls:
  Stick         - D-pad
  L             - B button
  R             - A button
  Tap L+R       - START
  L+R + Down    - SELECT
  L+R + Up      - Switch ZOOM / FIT view
  Hold L+R 2s   - Quit to menu (the game is saved and resumes next time)
"""

import importlib.util
import os
import time
import warnings

import numpy as np

import settings
from arcade import Game, GameState, InputState, Display
from games.doom import blit, _text, _draw_exit_bar

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROM_DIR = os.path.join(os.path.dirname(_HERE), 'gb_roms')
_EXTS = ('.gb', '.gbc')
_SETTINGS_KEY = 'handheld'

GB_W, GB_H = 160, 144
GB_FPS = 4194304 / 70224                 # 59.73
MAX_FRAMES_PER_UPDATE = 4                # behind by more than this: drop time, don't spiral
# Pea-green DMG shades: the LED panel at full white is harsh, and it looks the part
DMG_PALETTE = (0x9BBC0F, 0x8BAC0F, 0x306230, 0x0F380F)

CHORD_WINDOW = 0.06                      # s for the second button to count as L+R together
START_TAP_MAX = 0.6                      # s; held longer than this, L+R is heading for quit
TAP_FRAMES = 4                           # emulated frames a tapped button stays down
LABEL, DIM = (110, 110, 110), (170, 170, 170)


def _roms():
    if not os.path.isdir(ROM_DIR):
        return []
    return sorted(os.path.join(ROM_DIR, f) for f in os.listdir(ROM_DIR)
                  if f.lower().endswith(_EXTS))


def _available():
    return importlib.util.find_spec('pyboy') is not None and bool(_roms())


def rom_title(path):
    """The cartridge header title (0x134-0x143), else the file name."""
    try:
        with open(path, 'rb') as f:
            f.seek(0x134)
            raw = f.read(16)
        title = ''.join(chr(b) for b in raw.split(b'\0')[0] if 32 <= b < 127).strip()
    except OSError:
        title = ''
    return (title or os.path.splitext(os.path.basename(path))[0]).upper()[:15]


# ── Rendering ────────────────────────────────────────────────────

def render_zoom(screen, cam_x, cam_y):
    """128x128 window of the 160x144 screen at (cam_x, cam_y), 2x2-averaged to 64x64."""
    x, y = int(round(cam_x)), int(round(cam_y))
    crop = screen[y:y + 128, x:x + 128, :3].astype(np.uint16)
    return (crop.reshape(64, 2, 64, 2, 3).sum((1, 3)) >> 2).astype(np.uint8)


def render_fit(screen):
    """The whole screen, area-averaged to 64x58 and letterboxed into 64x64."""
    from PIL import Image
    small = Image.fromarray(np.ascontiguousarray(screen[..., :3])).resize((64, 58), Image.BOX)
    out = np.zeros((64, 64, 3), np.uint8)
    out[3:61] = np.asarray(small)
    return out


def sprite_focus(oam, lcdc):
    """Centre of the on-screen sprites in screen pixels, or None.
    oam is the 160-byte OAM table (y+16, x+8, tile, flags per sprite)."""
    if not lcdc & 0x02:
        return None
    ys = np.asarray(oam[0::4], np.int16) - 16
    xs = np.asarray(oam[1::4], np.int16) - 8
    on = (ys > -8) & (ys < GB_H) & (xs > -8) & (xs < GB_W)
    if not on.any():
        return None
    return float(xs[on].mean()) + 4, float(ys[on].mean()) + 4


class _Camera:
    """ZOOM view position: eases toward the sprites, clamped to the screen."""
    EASE = 6.0

    def __init__(self):
        self.x, self.y = (GB_W - 128) / 2, (GB_H - 128) / 2

    def follow(self, focus, dt):
        if focus is None:
            return
        tx = min(max(focus[0] - 64, 0), GB_W - 128)
        ty = min(max(focus[1] - 64, 0), GB_H - 128)
        k = min(1.0, dt * self.EASE)
        self.x += (tx - self.x) * k
        self.y += (ty - self.y) * k


# ── Cabinet controls -> Game Boy buttons ─────────────────────────

class Controls:
    """Two buttons and a stick in, the Game Boy's eight buttons out.

    A lone button press waits CHORD_WINDOW before it reaches the game, so
    pressing both together reads as a chord (START / SELECT / view) rather
    than A+B. Once a button is through, the other one is just a second
    button: holding B and then pressing A is A+B, as on the real thing."""

    def __init__(self, held_l=False, held_r=False):
        self.prev = {'L': held_l, 'R': held_r}     # already down: ignored until released
        self.prev_dir = set()
        self.pending = None            # (button, seconds waited) before it goes through
        self.through = set()           # cabinet buttons currently passed to the game
        self.chord = None              # seconds both have been held, or None
        self.chord_used = False
        self.taps = {}                 # gb button -> emulated frames left
        self.toggle_view = False       # one-shot, read by the game
        self.both_t = 0.0

    def update(self, inp, dt):
        """inp: dict up/down/left/right/L/R (held). Returns the set of GB buttons held."""
        self.toggle_view = False
        dirs = {d for d in ('up', 'down', 'left', 'right') if inp[d]}
        new_dirs, self.prev_dir = dirs - self.prev_dir, dirs
        down = {b for b in ('L', 'R') if inp[b] and not self.prev[b]}
        up = {b for b in ('L', 'R') if not inp[b] and self.prev[b]}
        self.prev = {'L': inp['L'], 'R': inp['R']}
        self.both_t = self.both_t + dt if inp['L'] and inp['R'] else 0.0

        if self.chord is not None:
            if inp['L'] or inp['R']:
                if inp['L'] and inp['R']:
                    self.chord += dt
                if not self.chord_used:
                    if 'down' in new_dirs:
                        self._tap('select')
                        self.chord_used = True
                    elif 'up' in new_dirs:
                        self.toggle_view = True
                        self.chord_used = True
                return self._held(inp, dpad=False)
            if not self.chord_used and self.chord < START_TAP_MAX:
                self._tap('start')
            self.chord = None
            self.chord_used = False
            down = set()

        self.through -= up
        if self.pending:
            b, waited = self.pending
            if down - {b} and not self.through:
                self.pending, self.chord = None, 0.0            # both together: a chord
                return self._held(inp, dpad=False)
            if b in up:                                         # quick tap: still a press
                self.pending = None
                self._tap(self._gb(b))
            elif waited + dt >= CHORD_WINDOW:
                self.pending = None
                self.through.add(b)
            else:
                self.pending = (b, waited + dt)
            down = down - {b}
        for b in down:
            if self.through or self.pending:
                self.through.add(b)
            else:
                self.pending = (b, 0.0)
        if inp['L'] and inp['R'] and len(down) == 2:               # both on the same frame
            self.pending, self.chord = None, 0.0
            self.through.clear()
        return self._held(inp, dpad=self.chord is None)

    @staticmethod
    def _gb(b):
        return 'b' if b == 'L' else 'a'

    def _tap(self, button):
        self.taps[button] = TAP_FRAMES

    def frames_elapsed(self, n):
        """Count down tapped buttons by emulated frames."""
        for k in list(self.taps):
            self.taps[k] -= n
            if self.taps[k] <= 0:
                del self.taps[k]

    def _held(self, inp, dpad):
        held = {self._gb(b) for b in self.through} | set(self.taps)
        if dpad:
            held |= {d for d in ('up', 'down', 'left', 'right') if inp[d]}
        return held


# ── Emulator ─────────────────────────────────────────────────────

class _Emu:
    """One PyBoy instance. Battery saves go next to the ROM (.ram), and a
    save state (.state) lets a quit-to-menu pick up exactly where it left off."""

    def __init__(self, rom, resume):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')     # pysdl2-dll announces itself on import
            from pyboy import PyBoy
        self.rom = rom
        self.state_path = rom + '.state'
        self.pb = PyBoy(rom, window='null', sound_emulated=False,
                        color_palette=DMG_PALETTE, log_level='ERROR')
        self.pb.set_emulation_speed(0)
        if resume and os.path.isfile(self.state_path):
            try:
                with open(self.state_path, 'rb') as f:
                    self.pb.load_state(f)
            except Exception:
                pass                            # stale/corrupt state: cold boot instead
        self.held = set()
        self.debt = 0.0

    def set_buttons(self, want):
        for b in self.held - want:
            self.pb.button_release(b)
        for b in want - self.held:
            self.pb.button_press(b)
        self.held = set(want)

    def run(self, dt):
        """Advance by dt of Game Boy time; returns the frames emulated."""
        self.debt += dt * GB_FPS
        n = int(self.debt)
        if n > MAX_FRAMES_PER_UPDATE:
            n, self.debt = MAX_FRAMES_PER_UPDATE, 0.0
        else:
            self.debt -= n
        if n:
            self.pb.tick(n, True)
        return n

    @property
    def screen(self):
        return self.pb.screen.ndarray

    def oam(self):
        return self.pb.memory[0xFE00:0xFEA0]

    def lcdc(self):
        return self.pb.memory[0xFF40]

    def close(self):
        try:
            with open(self.state_path + '.tmp', 'wb') as f:
                self.pb.save_state(f)
            os.replace(self.state_path + '.tmp', self.state_path)
        except Exception:
            pass
        self.pb.stop(save=True)


# ── Pre-game menu ────────────────────────────────────────────────

class _Menu:
    ROWS = ("GAME", "PLAY")

    def __init__(self, roms):
        saved = settings.get(_SETTINGS_KEY, {}) or {}
        self.roms = roms
        self.titles = [rom_title(r) for r in roms]
        last = saved.get('rom')
        self.index = roms.index(last) if last in roms else 0
        self.row = 0
        self.restart = False

    @property
    def rom(self):
        return self.roms[self.index]

    def can_resume(self):
        return os.path.isfile(self.rom + '.state')

    def move(self, dx, dy):
        if dy:
            self.row = (self.row + dy) % len(self.ROWS)
        if dx:
            if self.row == 0:
                self.index = (self.index + dx) % len(self.roms)
            elif self.can_resume():
                self.restart = not self.restart

    def value(self, row):
        if row == 0:
            return self.titles[self.index]
        return "RESTART" if self.restart or not self.can_resume() else "RESUME"

    def draw(self, panel, now):
        panel[:] = 0
        _text(panel, 16, 3, "HANDHELD", (155, 188, 15))
        panel[10, 8:56] = (48, 98, 48)
        for i, label in enumerate(self.ROWS):
            y = 16 + 14 * i
            sel = i == self.row
            _text(panel, 2, y, label, (255, 255, 255) if sel else LABEL)
            val = self.value(i)
            col = (255, 210, 60) if sel else DIM
            _text(panel, 63 - 4 * len(val) + 1, y + 7, val, col)
            if sel and (now * 2) % 1 < 0.7:
                panel[y + 9, 0] = col
        _text(panel, 2, 52, "L OR R", LABEL)
        _text(panel, 30, 52, "START", (255, 255, 255))
        _text(panel, 2, 58, "STICK", LABEL)
        _text(panel, 26, 58, "CHANGE", DIM)


# ── Game class ───────────────────────────────────────────────────

class Handheld(Game):
    name = 'HANDHELD'
    description = 'Game Boy ROMs on 64 LEDs'
    category = 'unique'
    menu_visible = staticmethod(_available)   # listed only with PyBoy and a ROM installed
    GUIDE = {
        'desc': 'A Game Boy emulator (PyBoy) for cartridges you dump yourself, shrunk onto the 64x64 grid.',
    }

    VIEW_LABEL_TIME = 1.0

    def __init__(self, display: Display):
        super().__init__(display)
        self._emu = None
        self._menu = None
        self._panel = np.zeros((64, 64, 3), dtype=np.uint8)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0
        self.close()
        self._controls = Controls()
        self._camera = _Camera()
        saved = settings.get(_SETTINGS_KEY, {}) or {}
        self._view = saved.get('view', 'zoom')
        self._view_t = -1e9
        roms = _roms() if _available() else []
        if not roms:
            self.state = GameState.GAME_OVER
            return
        self._menu = _Menu(roms)

    def _save_settings(self):
        settings.set(_SETTINGS_KEY, {'rom': self._menu.rom, 'view': self._view})

    def _start(self):
        self._save_settings()
        try:
            self._emu = _Emu(self._menu.rom, resume=not self._menu.restart)
        except Exception:
            self._emu = None
            self.state = GameState.GAME_OVER
            return

    def close(self):
        if self._emu is not None:
            self._emu.close()
            self._emu = None

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return
        now = time.monotonic()
        if self._emu is None:
            m = self._menu
            m.move((1 if input_state.right_pressed else 0) - (1 if input_state.left_pressed else 0),
                   (1 if input_state.down_pressed else 0) - (1 if input_state.up_pressed else 0))
            m.draw(self._panel, now)
            if input_state.action_l or input_state.action_r:
                self._start()
                self._controls = Controls(input_state.action_l_held, input_state.action_r_held)
            return
        inp = dict(up=input_state.up, down=input_state.down,
                   left=input_state.left, right=input_state.right,
                   L=input_state.action_l_held, R=input_state.action_r_held)
        c = self._controls
        self._emu.set_buttons(c.update(inp, dt))
        if c.toggle_view:
            self._view = 'fit' if self._view == 'zoom' else 'zoom'
            self._view_t = now
            self._save_settings()
        c.frames_elapsed(self._emu.run(dt))
        self._compose(dt, now)

    def _compose(self, dt, now):
        screen = self._emu.screen
        if self._view == 'zoom':
            self._camera.follow(sprite_focus(self._emu.oam(), self._emu.lcdc()), dt)
            self._panel[:] = render_zoom(screen, self._camera.x, self._camera.y)
        else:
            self._panel[:] = render_fit(screen)
        if now - self._view_t < self.VIEW_LABEL_TIME:
            label = self._view.upper()
            self._panel[56:63, 0:4 * len(label) + 3] = 0
            _text(self._panel, 2, 57, label, (255, 255, 255))
        if self._controls.both_t > START_TAP_MAX:
            _draw_exit_bar(self._panel, self._controls.both_t / 2.0)

    def draw(self):
        blit(self.display, self._panel)
