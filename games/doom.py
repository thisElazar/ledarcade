"""
Doom - Freedoom on a 64x64 LED panel
=====================================
Subprocess-based: runs the patched doomgeneric engine and pipes frames
through a numpy downscale pipeline into the cabinet's display buffer.

Controls:
  Stick       - Move / turn (always run)
  L           - Fire (use when dead)
  R tap       - Use / open doors
  R + L/R     - Strafe
  R + U/D     - Cycle weapon
  Hold L+R 2s - Quit to menu
"""

import os
import sys
import subprocess
import threading
import time

import numpy as np

from arcade import Game, GameState, InputState, Display, GRID_SIZE

# Doom's native resolution
_W, _H, _VIEW_H = 320, 200, 168

# Frame pipe header: int16 fields
_HDR_FIELDS = 36
_FRAME_BYTES = _W * _H * 4
_MSG_BYTES = 64

# Doom key codes (from doomdef.h)
_DK_RIGHT, _DK_LEFT, _DK_UP, _DK_DOWN = 0xae, 0xac, 0xad, 0xaf
_DK_STRAFE_L, _DK_STRAFE_R, _DK_USE, _DK_FIRE = 0xa0, 0xa1, 0xa2, 0xa3
_DK_RUN = 0x80 + 0x36

_WEAPON_AMMO = {1: 0, 2: 1, 3: 0, 4: 3, 5: 2, 6: 2, 8: 1}
_SLOT = {0: 1, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 5}

# Engine location (sibling to the led-arcade repo)
_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DOOM_DIR = os.path.join(os.path.dirname(_HERE), 'doom_preview')
_EXE = os.path.join(_DOOM_DIR, 'doomgeneric', 'doomgeneric', 'doom_pipe')
_WAD = os.path.join(_DOOM_DIR, 'freedoom-0.13.0', 'freedoom1.wad')


def _available():
    return os.path.isfile(_EXE) and os.path.isfile(_WAD)


# ── Scaling (from viewer.py, with caching) ──────────────────────

import functools

@functools.lru_cache(maxsize=8)
def _box_weights(n_in, n_out):
    s = n_in / n_out
    w = np.zeros((n_out, n_in), dtype=np.float32)
    for o in range(n_out):
        a, b = o * s, (o + 1) * s
        for i in range(int(a), min(n_in, int(np.ceil(b)))):
            w[o, i] = min(b, i + 1) - max(a, i)
    return w / s

_float_buf = {}

def _area(img, out_w, out_h):
    wy, wx = _box_weights(img.shape[0], out_h), _box_weights(img.shape[1], out_w)
    key = img.shape
    buf = _float_buf.get(key)
    if buf is None or buf.shape != img.shape:
        buf = _float_buf[key] = np.empty(img.shape, dtype=np.float32)
    np.copyto(buf, img, casting='unsafe')
    flat = buf.ndim == 2
    if flat:
        buf = buf[..., None]
    out = np.einsum("pj,ojc->opc", wx, np.einsum("oi,ijc->ojc", wy, buf))
    return out[..., 0] if flat else out


def _blur3(a):
    p = np.pad(a, ((1, 1), (1, 1), (0, 0)), mode="edge")
    return sum(p[y:y + a.shape[0], x:x + a.shape[1]] for y in range(3) for x in range(3)) / 9


# ── Rendering ────────────────────────────────────────────────────

_ZOOM = 0.8
_SHARPEN = 0.6

def _render_view(view, mask):
    """320x168 Doom view -> 64x40 uint8 RGB with highlight."""
    h, w = view.shape[:2]
    ch, cw = round(h * _ZOOM), round(w * _ZOOM)
    y0, x0 = (h - ch) // 2, (w - cw) // 2
    view = view[y0:y0 + ch, x0:x0 + cw]
    mask = None if mask is None else mask[y0:y0 + ch, x0:x0 + cw]
    out = _area(view, 64, 40)
    out = out + _SHARPEN * (out - _blur3(out))
    if mask is not None:
        for tag, target in ((2, 170), (1, 235)):
            cov = _area((mask == tag).astype(np.float32), 64, 40)
            if not cov.any():
                continue
            pop = np.clip(cov * 3, 0, 1)[..., None]
            gain = np.clip(target / np.maximum(out.max(-1, keepdims=True), 1), 1, 4)
            out = out * (1 - pop) + out * gain * pop
            if tag == 1:
                body = cov > 0.08
                grown = np.zeros_like(body)
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        grown |= np.roll(np.roll(body, dy, 0), dx, 1)
                out[grown & ~body] *= 0.35
    return np.clip(out + 0.5, 0, 255).astype(np.uint8)


# ── HUD (minimal status strip) ──────────────────────────────────

_FONT = {
    '0': [0x7c, 0x82, 0x82, 0x82, 0x7c], '1': [0x00, 0x42, 0xfe, 0x02, 0x00],
    '2': [0x46, 0x8a, 0x92, 0x92, 0x62], '3': [0x44, 0x82, 0x92, 0x92, 0x6c],
    '4': [0xf8, 0x08, 0x08, 0x08, 0xfe], '5': [0xe4, 0xa2, 0xa2, 0xa2, 0x9c],
    '6': [0x7c, 0x92, 0x92, 0x92, 0x4c], '7': [0x80, 0x80, 0x8e, 0xb0, 0xc0],
    '8': [0x6c, 0x92, 0x92, 0x92, 0x6c], '9': [0x64, 0x92, 0x92, 0x92, 0x7c],
    '%': [0xc6, 0xc8, 0x10, 0x26, 0xc6],
}

def _tiny_text(buf, x, y, text, color):
    for ch in text:
        glyph = _FONT.get(ch)
        if glyph is None:
            x += 3
            continue
        for col, bits in enumerate(glyph):
            cx = x + col
            if 0 <= cx < 64:
                for row in range(7):
                    if bits >> (7 - row) & 1:
                        ry = y + row
                        if 0 <= ry < 64:
                            buf[ry, cx] = color
        x += 6


def _draw_hud(buf, state):
    """Minimal status in the bottom 24 rows (rows 40-63)."""
    if state is None or not state.get('in_level'):
        return
    buf[40:] = 0
    hp = max(0, state['health'])
    armor = max(0, state['armor'])
    ammo = max(0, state['ammo'])
    hp_col = (0, 255, 0) if hp > 50 else (255, 255, 0) if hp > 25 else (255, 40, 40)
    _tiny_text(buf, 1, 42, f"{hp}%", hp_col)
    _tiny_text(buf, 1, 52, f"{armor}%", (100, 100, 255))
    _tiny_text(buf, 40, 42, str(ammo), (255, 200, 80))


# ── Cabinet controls adapter ────────────────────────────────────

class _Controls:
    """Translates InputState -> Doom key events."""
    TAP = 0.1
    EXIT_HOLD = 2.0

    def __init__(self):
        self.held = set()
        self.prev = {}
        self.tap_key = None
        self.tap_left = 0.0
        self.both_t = 0.0
        self.exit = False

    def update(self, inp, state, dt):
        edge = {k: inp[k] and not self.prev.get(k) for k in inp}
        self.prev = dict(inp)
        in_level = bool(state and state.get('in_level'))
        want = {_DK_RUN} if in_level else set()
        if inp['R']:
            want.add(_DK_USE)
            if inp['left']:
                want.add(_DK_STRAFE_L)
            if inp['right']:
                want.add(_DK_STRAFE_R)
            if in_level and (edge.get('up') or edge.get('down')):
                k = self._cycle(state, 1 if edge.get('up') else -1)
                if k:
                    self.tap_key, self.tap_left = k, self.TAP
        else:
            for d, k in (('up', _DK_UP), ('down', _DK_DOWN),
                         ('left', _DK_LEFT), ('right', _DK_RIGHT)):
                if inp[d]:
                    want.add(k)
        if inp['L']:
            want.add(_DK_USE if in_level and state['health'] <= 0 else _DK_FIRE)
        if self.tap_key:
            want.add(self.tap_key)
            self.tap_left -= dt
            if self.tap_left <= 0:
                self.tap_key = None
        self.both_t = self.both_t + dt if inp['L'] and inp['R'] else 0.0
        self.exit = self.both_t >= self.EXIT_HOLD
        events = [(False, k) for k in self.held - want] + [(True, k) for k in want - self.held]
        self.held = want
        return events

    @staticmethod
    def _cycle(state, step):
        usable = sorted({_SLOT[w] for w in range(9) if state['owned'] >> w & 1
                         and (w not in _WEAPON_AMMO or state['ammo_all'][_WEAPON_AMMO[w]] > 0)})
        cur = _SLOT.get(state['weapon'], 1)
        if len(usable) < 2:
            return None
        later = [n for n in usable if (n - cur) * step > 0]
        nxt = (min(later) if step > 0 else max(later)) if later else (usable[0] if step > 0 else usable[-1])
        return ord(str(nxt))


# ── Engine subprocess ────────────────────────────────────────────

class _Engine:
    """Runs doom_pipe, keeps the latest frame + state."""

    def __init__(self, exe, iwad):
        r, w = os.pipe()
        self.proc = subprocess.Popen(
            [exe, '-iwad', iwad, '-skill', '3', '-warp', '1', '1'],
            cwd=_DOOM_DIR, stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL, pass_fds=(w,),
            env={**os.environ, 'DOOM_FRAME_FD': str(w)})
        os.close(w)
        self.pipe = os.fdopen(r, 'rb', buffering=0)
        self.frame = None
        self.mask = None
        self.state = None
        self._send(5, 4)   # light +4
        self._send(6, 0)   # not full bright
        self._send(9, 0)   # damage tint off
        threading.Thread(target=self._read, daemon=True).start()

    def _read_exact(self, n):
        chunks = []
        while n:
            c = self.pipe.read(n)
            if not c:
                raise EOFError
            chunks.append(c)
            n -= len(c)
        return b''.join(chunks)

    def _read(self):
        try:
            while True:
                if self._read_exact(4) != b'DOOM':
                    continue
                h = np.frombuffer(self._read_exact(_HDR_FIELDS * 2), dtype=np.int16).tolist()
                self._read_exact(_MSG_BYTES)  # message
                self._read_exact(64)          # level names
                px = np.frombuffer(self._read_exact(_FRAME_BYTES), dtype=np.uint8)
                bgrx = px.reshape(_H, _W, 4)
                self.state = dict(
                    in_level=bool(h[0]), health=h[1], armor=h[2], ammo=h[3],
                    keys=h[4], weapon=h[5], damage=h[6], owned=h[7],
                    ammo_all=h[8:12], ammo_max=h[12:16], gamestate=h[23])
                self.mask = np.frombuffer(self._read_exact(_W * _H), dtype=np.uint8).reshape(_H, _W)
                self.frame = bgrx[..., 2::-1].copy()
        except (EOFError, OSError):
            self.frame = None

    def _send(self, a, b):
        try:
            self.proc.stdin.write(bytes([a, b]))
            self.proc.stdin.flush()
        except (BrokenPipeError, OSError):
            pass

    def key(self, pressed, doomkey):
        self._send(1 if pressed else 0, doomkey)

    def close(self):
        try:
            self.proc.kill()
        except OSError:
            pass


# ── Game class ───────────────────────────────────────────────────

class Doom(Game):
    name = 'DOOM'
    description = 'Freedoom on 64 LEDs'
    category = 'unique'
    dev_only = True
    GUIDE = {
        'desc': 'The original 1993 first-person shooter, rendered on a 64x64 LED grid via Freedoom.',
    }

    def __init__(self, display: Display):
        super().__init__(display)
        self._engine = None
        self._controls = _Controls()
        self._panel = np.zeros((64, 64, 3), dtype=np.uint8)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0
        if self._engine is not None:
            self._engine.close()
        if _available():
            self._engine = _Engine(_EXE, _WAD)
        else:
            self.state = GameState.GAME_OVER

    def close(self):
        if self._engine is not None:
            self._engine.close()
            self._engine = None

    def update(self, input_state: InputState, dt: float):
        if self._engine is None or self._engine.proc.poll() is not None:
            self.state = GameState.GAME_OVER
            return
        inp = dict(
            up=input_state.up, down=input_state.down,
            left=input_state.left, right=input_state.right,
            L=input_state.action_l_held, R=input_state.action_r_held)
        for pressed, k in self._controls.update(inp, self._engine.state, dt):
            self._engine.key(pressed, k)
        if self._controls.exit:
            self.state = GameState.GAME_OVER
            return
        frame = self._engine.frame
        if frame is None:
            return
        es = self._engine.state
        self._panel[:] = 0
        if es and es.get('gamestate') == 0 and es.get('in_level'):
            self._panel[:40] = _render_view(frame[:_VIEW_H], self._engine.mask[:_VIEW_H] if self._engine.mask is not None else None)
            _draw_hud(self._panel, es)
        else:
            scaled = _area(frame, 64, 48)
            self._panel[8:56] = np.clip(scaled + 0.5, 0, 255).astype(np.uint8)

    def draw(self):
        panel = self._panel
        fb = getattr(self.display, '_fb', None)
        if fb is not None:
            for y in range(GRID_SIZE):
                row = panel[y]
                off = y * GRID_SIZE * 3
                for x in range(GRID_SIZE):
                    px = row[x]
                    fb[off] = px[0]
                    fb[off + 1] = px[1]
                    fb[off + 2] = px[2]
                    off += 3
        else:
            buf = self.display.buffer
            for y in range(GRID_SIZE):
                row = panel[y]
                for x in range(GRID_SIZE):
                    px = row[x]
                    buf[y][x] = (int(px[0]), int(px[1]), int(px[2]))
