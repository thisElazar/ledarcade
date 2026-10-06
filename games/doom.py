"""
Doom - Freedoom on a 64x64 LED panel
=====================================
Subprocess-based: runs the patched doomgeneric engine and pipes frames
through a numpy downscale pipeline into the cabinet's display buffer.

Controls:
  Stick       - Move / turn (always run); in the menu, pick game, skill and map
  L or R      - Start (in the menu)
  L           - Fire (use when dead)
  R tap       - Use / open doors
  R + L/R     - Strafe
  R + U/D     - Cycle weapon
  Hold L+R 2s - Quit to menu
"""

import os
import re
import sys
import subprocess
import threading
import time

import numpy as np

import settings
from arcade import Game, GameState, InputState, Display, GRID_SIZE, _FONT_3X5

# Doom's native resolution
_W, _H, _VIEW_H = 320, 200, 168

# Frame pipe header: int16 fields
_HDR_FIELDS = 40
_FRAME_BYTES = _W * _H * 4
_MSG_BYTES = 64

# Doom key codes (from doomdef.h)
_DK_RIGHT, _DK_LEFT, _DK_UP, _DK_DOWN = 0xae, 0xac, 0xad, 0xaf
_DK_STRAFE_L, _DK_STRAFE_R, _DK_USE, _DK_FIRE = 0xa0, 0xa1, 0xa2, 0xa3
_DK_RUN = 0x80 + 0x36

_WEAPON_AMMO = {1: 0, 2: 1, 3: 0, 4: 3, 5: 2, 6: 2, 8: 1}
_SLOT = {0: 1, 7: 1, 1: 2, 2: 3, 8: 3, 3: 4, 4: 5, 5: 6, 6: 7}   # weapontype_t -> key 1-7

# Engine location (sibling to the led-arcade repo)
_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DOOM_DIR = os.path.join(os.path.dirname(_HERE), 'doom_preview')
_EXE = os.path.join(_DOOM_DIR, 'doomgeneric', 'doomgeneric', 'doom_pipe')
_WAD_DIR = os.path.join(_DOOM_DIR, 'freedoom-0.13.0')
# Freedoom Phase 1 is episodic (E1M1 style, Doom I rules), Phase 2 is one long
# campaign (MAP01 style, Doom II rules). Either or both may be installed.
_WADS = (('PHASE 1', 'freedoom1.wad'), ('PHASE 2', 'freedoom2.wad'))


def _installed_wads():
    """[(label, path)] of the Freedoom IWADs present on disk."""
    found = []
    for label, name in _WADS:
        path = os.path.join(_WAD_DIR, name)
        if os.path.isfile(path):
            found.append((label, path))
    return found


def _available():
    return os.path.isfile(_EXE) and bool(_installed_wads())


# ── Scaling ──────────────────────────────────────────────────────
# Same area-average as viewer.py, without einsum: the Pi's numpy uses
# reference BLAS, where einsum/matmul took ~80 ms per frame.

import functools

@functools.lru_cache(maxsize=16)
def _edges(n_in, n_out):
    """Source positions of the n_out + 1 output edges: whole part, fraction."""
    x = np.arange(n_out + 1) * (n_in / n_out)
    i = np.minimum(x.astype(np.intp), n_in - 1)
    return i, (x - i).astype(np.float32).reshape(-1, 1, 1)


def _area(img, out_w, out_h):
    """Area-average to (out_h, out_w, c) float32. Columns must divide evenly
    (zoomed view 256->64, full screen 320->64, face 24->12); rows may not."""
    r = img.shape[1] // out_w
    if img.ndim == 2:
        img = img[..., None]
    acc = img[:, 0::r].astype(np.float32)
    for j in range(1, r):
        acc += img[:, j::r]
    # rows: difference of the running sum, read at fractional edges
    i, f = _edges(acc.shape[0], out_h)
    c = np.zeros((acc.shape[0] + 1,) + acc.shape[1:], np.float32)
    np.cumsum(acc, axis=0, out=c[1:])
    at = c[i] + f * acc[i]
    return (at[1:] - at[:-1]) * np.float32(out_h / (img.shape[0] * r))


def _blur3(a):
    p = np.pad(a, ((1, 1), (1, 1), (0, 0)), mode="edge")
    return sum(p[y:y + a.shape[0], x:x + a.shape[1]] for y in range(3) for x in range(3)) / 9


# ── Rendering ────────────────────────────────────────────────────

_ZOOM = 0.8
_SHARPEN = 0.6

def _render_view(view, mask, zoom=True):
    """320x168 Doom view -> 64x40 uint8 RGB with highlight (mask None: no highlight)."""
    if zoom:
        h, w = view.shape[:2]
        ch, cw = round(h * _ZOOM), round(w * _ZOOM)
        y0, x0 = (h - ch) // 2, (w - cw) // 2
        view = view[y0:y0 + ch, x0:x0 + cw]
        mask = None if mask is None else mask[y0:y0 + ch, x0:x0 + cw]
    out = _area(view, 64, 40)
    out = out + _SHARPEN * (out - _blur3(out))
    if mask is not None:
        for tag, target in ((2, 170), (1, 235)):
            hit = mask == tag
            if not hit.any():
                continue
            cov = _area(hit, 64, 40)[..., 0]
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


# ── View overlay + quit bar (from viewer.py) ────────────────────

HIT_FADE = 0.7                 # s the damage-direction glow lasts after a hit
EXIT_BAR_AFTER = 0.3           # s both buttons are held before the quit bar shows (fire + use is normal play)


def _view_overlay(buf, s, mask, hud, now):
    """On the 64x40 view: red glow on the edge you're being hit from, and a
    crosshair that lights up when a monster is in the line of fire (Doom
    auto-aims vertically, so any monster in the centre column counts)."""
    if s.get("hit") and s["damage"] > 0:
        hud.hit_t, hud.hit_angle = now, s["hit_angle"]      # Doom's own count drains in ~0.2 s
    fade = 1 - (now - hud.hit_t) / HIT_FADE
    if fade > 0:
        yy, xx = np.mgrid[0:40, 0:64]
        dx, dy = xx - 31.5, yy - 19.5
        edge = np.minimum(np.minimum(xx, 63 - xx), np.minimum(yy, 39 - yy))
        ring = np.where(edge == 0, 1.0, np.where(edge == 1, 0.5, 0.0))
        rel = np.arctan2(-dx, -dy) - hud.hit_angle * 2 * np.pi / 4096   # 0 = ahead
        w = np.clip(np.cos(rel), 0, 1) ** 3 * ring * fade
        view = buf[:40].astype(np.float32)
        buf[:40] = (view * (1 - w[..., None]) + np.array([255, 40, 20]) * w[..., None]).astype(np.uint8)
    on_target = mask is not None and (mask[:_VIEW_H, 157:163] == 1).any()
    if on_target:
        buf[20, 32] = (255, 255, 255)
        buf[20, 30] = buf[20, 34] = (255, 60, 40)
    else:
        buf[20, 32] = (120, 120, 120)


def _draw_exit_bar(buf, frac):
    """Hold-both-buttons quit progress across the top of the panel."""
    buf[:3] = 0
    n = int(round(64 * min(1.0, frac)))
    buf[1, :64] = (40, 40, 40)
    buf[1, :n] = (255, 255, 255) if frac < 1 else (255, 60, 40)


# ── HUD (viewer.py's STATUS style) ──────────────────────────────
# Rows 40-63: numbers left, Doomguy's face centre, ammo gauges + keys right;
# rows 58-62 are the weapon row, replaced by a message when Doom posts one.

KEY_COLORS = [(40, 90, 255), (255, 220, 0), (230, 20, 20)]      # blue, yellow, red
AMMO_COLORS = [(230, 200, 60), (240, 120, 40), (60, 200, 230), (210, 60, 40)]  # clip shell cell rocket
DIM, LABEL, TRACK = (35, 35, 35), (110, 110, 110), (30, 30, 30)
FACE = (slice(170, 200), slice(148, 172))       # Doom's status-bar face, 24x30
MSG_SPEED = 40                                   # marquee px per second
MSG_HOLD = 2.5                                   # s a short message stays up
HEALTH_C, ARMOR_C, AMMO_C, WEAPON_C, POWER_C = ((60, 220, 60), (80, 160, 255), (255, 170, 60),
                                               (255, 255, 255), (220, 120, 255))
SHORT = {   # Doom's pickup messages (d_englsh.h) -> panel text; 16 chars fit without scrolling
    "Picked up the armor.": ("ARMOR", ARMOR_C),
    "Picked up the MegaArmor!": ("MEGA ARMOR", ARMOR_C),
    "Picked up a health bonus.": ("+1 HEALTH", HEALTH_C),
    "Picked up an armor bonus.": ("+1 ARMOR", ARMOR_C),
    "Picked up a stimpack.": ("+10 HEALTH", HEALTH_C),
    "Picked up a medikit that you REALLY need!": ("+25 HEALTH", HEALTH_C),
    "Picked up a medikit.": ("+25 HEALTH", HEALTH_C),
    "Supercharge!": ("SUPERCHARGE", HEALTH_C),
    "Picked up a blue keycard.": ("BLUE KEY", KEY_COLORS[0]),
    "Picked up a yellow keycard.": ("YELLOW KEY", KEY_COLORS[1]),
    "Picked up a red keycard.": ("RED KEY", KEY_COLORS[2]),
    "Picked up a blue skull key.": ("BLUE SKULL", KEY_COLORS[0]),
    "Picked up a yellow skull key.": ("YELLOW SKULL", KEY_COLORS[1]),
    "Picked up a red skull key.": ("RED SKULL", KEY_COLORS[2]),
    "Invulnerability!": ("INVULNERABLE", POWER_C),
    "Berserk!": ("BERSERK", POWER_C),
    "Partial Invisibility": ("INVISIBLE", POWER_C),
    "Radiation Shielding Suit": ("RAD SUIT", POWER_C),
    "Computer Area Map": ("MAP", POWER_C),
    "Light Amplification Visor": ("LIGHT AMP", POWER_C),
    "MegaSphere!": ("MEGASPHERE", POWER_C),
    "Picked up a clip.": ("CLIP", AMMO_COLORS[0]),
    "Picked up a box of bullets.": ("BULLET BOX", AMMO_COLORS[0]),
    "Picked up a rocket.": ("ROCKET", AMMO_COLORS[3]),
    "Picked up a box of rockets.": ("ROCKET BOX", AMMO_COLORS[3]),
    "Picked up an energy cell.": ("CELL", AMMO_COLORS[2]),
    "Picked up an energy cell pack.": ("CELL PACK", AMMO_COLORS[2]),
    "Picked up 4 shotgun shells.": ("4 SHELLS", AMMO_COLORS[1]),
    "Picked up a box of shotgun shells.": ("SHELL BOX", AMMO_COLORS[1]),
    "Picked up a backpack full of ammo!": ("BACKPACK", AMMO_C),
    "You got the BFG9000! Oh, yes.": ("BFG9000!", WEAPON_C),
    "You got the chaingun!": ("CHAINGUN!", WEAPON_C),
    "A chainsaw! Find some meat!": ("CHAINSAW!", WEAPON_C),
    "You got the rocket launcher!": ("ROCKET LAUNCHER!", WEAPON_C),
    "You got the plasma gun!": ("PLASMA GUN!", WEAPON_C),
    "You got the shotgun!": ("SHOTGUN!", WEAPON_C),
    "You got the super shotgun!": ("SUPER SHOTGUN!", WEAPON_C),
}
KEY_NAMES = ["blue", "yellow", "red"]
WI_FIELDS = ("state", "sp_state", "kills", "items", "secret", "time", "par", "episode", "last", "next")
WI_ROWS = [("KILLS", "kills", (255, 80, 60)), ("ITEMS", "items", (255, 210, 60)),
           ("SECRET", "secret", (80, 200, 255))]


def _text(buf, x, y, text, color):
    """3x5 cabinet font, clipped to the panel (so it can scroll off an edge)."""
    for j, ch in enumerate(text):
        for r, row in enumerate(_FONT_3X5.get(ch, [])):
            for c, px in enumerate(row):
                xx = x + j * 4 + c
                if px == "1" and 0 <= xx < 64:
                    buf[y + r, xx] = color


def _hp_color(hp):
    return (60, 220, 60) if hp > 50 else (255, 200, 0) if hp > 25 else (255, 40, 40)


def _armor_color(s):
    return [(90, 90, 90), (60, 200, 60), (80, 140, 255)][min(s["armortype"], 2)]


def _bar(buf, x, y, w, h, frac, col):
    buf[y:y + h, x:x + w] = TRACK
    n = int(round(w * max(0.0, min(1.0, frac))))
    buf[y:y + h, x:x + n] = col


def _short_message(msg):
    """(panel text, colour, needed-key index or None) for a Doom message."""
    if msg in SHORT:
        return (*SHORT[msg], None)
    for i, name in enumerate(KEY_NAMES):
        if msg.startswith(f"You need a {name} key"):
            return f"NEED {name.upper()} KEY", KEY_COLORS[i], i
    return msg.upper(), (230, 230, 230), None


class _Hud:
    """STATUS HUD; remembers the message marquee between frames."""

    def __init__(self):
        self.serial, self.msg, self.msg_t = 0, "", 0.0
        self.msg_col, self.need_key = (230, 230, 230), None
        self.hit_t, self.hit_angle = -1e9, 0

    def draw(self, buf, frame, s, now):
        if s["msg_serial"] != self.serial:
            self.serial, self.msg_t = s["msg_serial"], now
            self.msg, self.msg_col, self.need_key = _short_message(s["msg"])
        _text(buf, 1, 41, "H", LABEL)
        _text(buf, 6, 41, f"{max(s['health'], 0):3d}", _hp_color(s["health"]))
        _text(buf, 1, 47, "A", LABEL)
        _text(buf, 6, 47, f"{s['armor']:3d}", _armor_color(s))
        if s["ammo_type"] < 4 and s["ammo"] >= 0:
            buf[54:56, 1:4] = AMMO_COLORS[s["ammo_type"]]
            _text(buf, 6, 53, f"{s['ammo']:3d}", AMMO_COLORS[s["ammo_type"]])
        buf[41:56, 22:34] = np.clip(_area(frame[FACE], 12, 15) + 0.5, 0, 255).astype(np.uint8)
        for i in range(4):
            y = 41 + i * 3
            if s["ammo_type"] == i:
                buf[y:y + 2, 37] = (255, 255, 255)
            _bar(buf, 39, y, 24, 2, s["ammo_all"][i] / max(1, s["ammo_max"][i]), AMMO_COLORS[i])
        for i, col in enumerate(KEY_COLORS):     # card = solid block, skull key = dark centre
            card, skull = s["keys"] >> i & 1, s["keys"] >> (i + 3) & 1
            if card or skull:
                x = 39 + i * 8
                buf[54:57, x:x + 5] = col
                if skull and not card:
                    buf[55, x + 1:x + 4] = 0
        self._bottom_row(buf, s, now)
        if self.need_key is not None and now - self.msg_t < MSG_HOLD and (now * 4) % 2 < 1:
            x = 39 + 8 * self.need_key           # blink the empty key slot the door asked for
            buf[54:57, x:x + 5] = KEY_COLORS[self.need_key]

    def intermission(self, buf, wi):
        """Level-end tally: title band over the picture, stats in the HUD strip.
        Values count up with Doom's own animation (-1 = not reached yet)."""
        def right(y, text, col):
            _text(buf, 64 - 4 * len(text), y, text, col)
        ep, done = wi["episode"] + 1, wi["state"] == 0
        title = f"E{ep}M{wi['last'] + 1} CLEAR" if done else f"NEXT E{ep}M{wi['next'] + 1}"
        name = wi["names"][0 if done else 1].split(":", 1)[-1].strip().upper()
        lines, cur = [], ""
        for w in name.split():                   # wrap to 16-char lines, max 2
            if cur and len(cur) + 1 + len(w) > 16:
                lines.append(cur)
                cur = w
            else:
                cur = f"{cur} {w}".strip()
        lines = (lines + [cur])[:2]
        band = 8 + 7 * len(lines)
        buf[:band] = (buf[:band] * 0.2).astype(np.uint8)
        _text(buf, (65 - 4 * len(title)) // 2, 1, title, (255, 255, 255))
        for i, ln in enumerate(lines):
            _text(buf, (65 - 4 * len(ln[:16])) // 2, 8 + 7 * i, ln[:16], (255, 200, 90))
        for i, (label, key, col) in enumerate(WI_ROWS):
            y = 41 + i * 6
            _text(buf, 1, y, label, LABEL)
            if wi[key] >= 0:
                right(y, f"{wi[key]}%", (80, 255, 120) if wi[key] >= 100 else col)
        _text(buf, 1, 59, "TIME", LABEL)
        if wi["time"] >= 0:
            _text(buf, 19, 59, f"{wi['time'] // 60}:{wi['time'] % 60:02d}", (255, 255, 255))
        if wi["par"] >= 0:
            right(59, f"/{wi['par'] // 60}:{wi['par'] % 60:02d}", LABEL)

    def _bottom_row(self, buf, s, now):
        """Scrolling message if one is up, else weapons 1-7 (owned grey, held white)."""
        if self.msg:
            if len(self.msg) <= 16:              # fits: hold it still, centred
                if now - self.msg_t < MSG_HOLD:
                    _text(buf, (65 - 4 * len(self.msg)) // 2, 58, self.msg, self.msg_col)
                    return
            else:
                x = 64 - int((now - self.msg_t) * MSG_SPEED)
                if x + 4 * len(self.msg) > 0:
                    _text(buf, x, 58, self.msg, self.msg_col)
                    return
            self.msg = ""
        owned = {_SLOT[w] for w in range(9) if s["owned"] >> w & 1}
        held = _SLOT.get(s["weapon"])
        for n in range(1, 8):
            col = (255, 255, 255) if n == held else LABEL if n in owned else DIM
            _text(buf, 1 + (n - 1) * 5, 58, str(n), col)


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

def _wad_directory(iwad):
    """[(lump name, offset, size)] from the WAD's directory."""
    import struct
    with open(iwad, 'rb') as f:
        n, off = struct.unpack('<ii', f.read(12)[4:])
        f.seek(off)
        directory = f.read(16 * n)
    return [(name.rstrip(b'\0').decode('latin-1'), o, size)
            for o, size, name in (struct.unpack_from('<ii8s', directory, 16 * i) for i in range(n))]


def _wad_level_names(iwad):
    """Level names from the WAD's DEHACKED lump ({"E1M1": "E1M1: Outer Prison"}).
    doomgeneric is built without DEHACKED, so the engine only knows id's names."""
    for name, o, size in _wad_directory(iwad):
        if name == 'DEHACKED':
            with open(iwad, 'rb') as f:
                f.seek(o)
                text = f.read(size).decode('latin-1')
            names = {}
            for line in text.splitlines():
                key, eq, val = line.partition('=')
                if eq and key.strip().startswith('HUSTR_') and ':' in val:
                    names[val.split(':')[0].strip().upper()] = val.strip()
            return names
    return {}


_MAP_LUMP = re.compile(r'^(?:E(\d)M(\d)|MAP(\d\d))$')


@functools.lru_cache(maxsize=4)
def _wad_maps(iwad):
    """{episode: map count}; episode 0 for a Doom II style WAD (MAP01...)."""
    maps = {}
    for name, _, _ in _wad_directory(iwad):
        m = _MAP_LUMP.match(name)
        if m:
            ep = int(m.group(1)) if m.group(1) else 0
            maps[ep] = maps.get(ep, 0) + 1
    return maps


@functools.lru_cache(maxsize=4)
def _wad_demos(iwad):
    """Names of the WAD's recorded demo lumps (DEMO1...), lower-case for -playdemo."""
    return [name.lower() for name, _, _ in _wad_directory(iwad) if re.match(r'^DEMO\d$', name)]


class _Engine:
    """Runs doom_pipe, keeps the latest frame + state.
    args: the rest of the command line ('-skill 3 -warp 1 1', or '-playdemo demo1')."""

    def __init__(self, exe, iwad, args):
        r, w = os.pipe()
        self.proc = subprocess.Popen(
            [exe, '-iwad', iwad] + list(args),
            cwd=_DOOM_DIR, stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL, pass_fds=(w,),
            env={**os.environ, 'DOOM_FRAME_FD': str(w)})
        os.close(w)
        self.pipe = os.fdopen(r, 'rb', buffering=0)
        self.frame = None
        self.mask = None
        self.state = None
        self.level_names = _wad_level_names(iwad)
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
                msg = self._read_exact(_MSG_BYTES).split(b'\0')[0].decode('latin-1')
                names = [n.split(b'\0')[0].decode('latin-1') for n in
                         (self._read_exact(32), self._read_exact(32))]
                names = [self._level_name(n) for n in names]
                px = np.frombuffer(self._read_exact(_FRAME_BYTES), dtype=np.uint8)
                bgrx = px.reshape(_H, _W, 4)
                self.state = dict(
                    in_level=bool(h[0]), health=h[1], armor=h[2], ammo=h[3],
                    keys=h[4], weapon=h[5], damage=h[6], owned=h[7],
                    ammo_all=h[8:12], ammo_max=h[12:16], armortype=h[16],
                    ammo_type=h[18], msg_serial=h[19], msg=msg, gamestate=h[23],
                    wi=dict(zip(WI_FIELDS, h[24:34]), names=names),
                    hit=h[34], hit_angle=h[35])
                self.mask = np.frombuffer(self._read_exact(_W * _H), dtype=np.uint8).reshape(_H, _W)
                self.frame = bgrx[..., 2::-1]   # RGB view; _area copies
        except (EOFError, OSError):
            self.frame = None

    def _level_name(self, engine_name):
        """Freedoom's name for a level the engine calls by id's name ("E1M1: Hangar",
        "level 1: entryway"); the DEHACKED keys are E1M1 / MAP01."""
        key = engine_name.split(':')[0].strip().upper()
        m = re.match(r'LEVEL (\d+)$', key)
        if m:
            key = f"MAP{int(m.group(1)):02d}"
        return self.level_names.get(key, engine_name)

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


def compose(panel, engine, hud, now):
    """Latest engine frame -> the 64x64 panel: view + HUD in a level, the tally
    at level end, else the unzoomed picture (title, text screens). Returns False
    while no frame has arrived yet. Shared with the attract-mode visual."""
    frame = engine.frame
    if frame is None:
        return False
    es, mask = engine.state, engine.mask
    panel[:] = 0
    if es and es.get('gamestate') == 0 and es.get('in_level'):
        panel[:40] = _render_view(frame[:_VIEW_H], None if mask is None else mask[:_VIEW_H])
        _view_overlay(panel, es, mask, hud, now)
        hud.draw(panel, frame, es, now)
    else:   # tally / text / title screens: unzoomed picture, no highlight
        panel[:40] = _render_view(frame[:_VIEW_H], None, zoom=False)
        if es and es.get('gamestate') == 1:
            hud.intermission(panel, es['wi'])
    return True


def blit(display, panel):
    """Copy a 64x64 uint8 panel into the display (fast path on the cabinet)."""
    fb = getattr(display, '_fb', None)
    if fb is not None:
        fb[:] = panel.tobytes()
    else:
        buf = display.buffer
        for y in range(GRID_SIZE):
            row = panel[y]
            for x in range(GRID_SIZE):
                px = row[x]
                buf[y][x] = (int(px[0]), int(px[1]), int(px[2]))


def start_engine(iwad, args):
    """An _Engine, or None when the engine won't start (wrong build, no memory,
    or the test sandbox)."""
    try:
        return _Engine(_EXE, iwad, args)
    except OSError:
        return None


# ── Pre-game menu ────────────────────────────────────────────────
# Doom's own menu is unreadable at 64 pixels, so the game, skill and starting
# map are picked here and passed on the command line. Choices and the furthest
# map reached per game persist in settings under 'doom'.

SKILLS = ("TOO YOUNG", "NOT ROUGH", "HURT ME", "ULTRA", "NIGHTMARE")   # Doom's five, shortened
_SETTINGS_KEY = 'doom'


class _Choice:
    """One entry of the GAME row: a Phase 1 episode or the whole of Phase 2."""

    def __init__(self, label, iwad, episode, maps):
        self.label, self.iwad, self.episode, self.maps = label, iwad, episode, maps
        self.key = f"{os.path.basename(iwad)}:{episode}"          # progress key in settings

    def map_name(self, m):
        return f"E{self.episode}M{m}" if self.episode else f"MAP{m:02d}"

    def warp(self, m):
        return ['-warp', str(self.episode), str(m)] if self.episode else ['-warp', str(m)]


def _choices():
    out = []
    for label, path in _installed_wads():
        maps = _wad_maps(path)
        if 0 in maps:
            out.append(_Choice(label, path, 0, maps[0]))
        for ep in sorted(e for e in maps if e):
            out.append(_Choice(f"{label} E{ep}", path, ep, maps[ep]))
    return out


class _Menu:
    """GAME / SKILL / MAP rows; stick moves, either button starts."""
    ROWS = ("GAME", "SKILL", "MAP")

    def __init__(self, choices):
        self.choices = choices
        saved = settings.get(_SETTINGS_KEY, {}) or {}
        self.progress = dict(saved.get('progress', {}))
        self.row = 0
        self.game = min(max(saved.get('game', 0), 0), len(choices) - 1)
        self.skill = min(max(saved.get('skill', 3), 1), 5)
        self.map = min(max(saved.get('map', 1), 1), self.furthest())

    @property
    def choice(self):
        return self.choices[self.game]

    def furthest(self):
        """Highest map worth offering: the furthest reached, capped by the WAD."""
        return min(max(self.progress.get(self.choice.key, 1), 1), self.choice.maps)

    def move(self, dx, dy):
        if dy:
            self.row = (self.row + dy) % len(self.ROWS)
        if dx:
            if self.row == 0:
                self.game = (self.game + dx) % len(self.choices)
                self.map = min(self.map, self.furthest())
            elif self.row == 1:
                self.skill = (self.skill - 1 + dx) % 5 + 1
            else:
                self.map = (self.map - 1 + dx) % self.furthest() + 1

    def value(self, row):
        if row == 0:
            return self.choice.label
        if row == 1:
            return SKILLS[self.skill - 1]
        return self.choice.map_name(self.map)

    def launch_args(self):
        return ['-skill', str(self.skill)] + self.choice.warp(self.map)

    def record_cleared(self, next_map):
        """A level ended: the next map (1-based) is reachable from the menu now."""
        if next_map > self.progress.get(self.choice.key, 1):
            self.progress[self.choice.key] = next_map
            self.save()

    def save(self):
        settings.set(_SETTINGS_KEY, {'game': self.game, 'skill': self.skill,
                                     'map': self.map, 'progress': self.progress})

    def draw(self, panel, now):
        panel[:] = 0
        _text(panel, 24, 3, "DOOM", (255, 50, 30))
        panel[10, 8:56] = (90, 20, 10)
        for i, label in enumerate(self.ROWS):
            y = 16 + 10 * i
            sel = i == self.row
            _text(panel, 2, y, label, (255, 255, 255) if sel else LABEL)
            val = self.value(i)
            col = (255, 210, 60) if sel else (170, 170, 170)
            _text(panel, 63 - 4 * len(val) + 1, y, val, col)
            if sel and (now * 2) % 1 < 0.7:                    # blinking cursor
                panel[y + 2, 25] = col
        _text(panel, 2, 52, "L OR R", LABEL)
        _text(panel, 30, 52, "START", (255, 255, 255))
        _text(panel, 2, 58, "STICK", LABEL)
        _text(panel, 26, 58, "CHANGE", (170, 170, 170))


# ── Game class ───────────────────────────────────────────────────

class Doom(Game):
    name = 'DOOM'
    description = 'Freedoom on 64 LEDs'
    category = 'unique'
    mature = True                          # listed only while the AFTER HOURS lever is on
    menu_visible = staticmethod(_available)  # ...and the engine is installed
    GUIDE = {
        'desc': 'The original 1993 first-person shooter, rendered on a 64x64 LED grid via Freedoom.',
    }

    def __init__(self, display: Display):
        super().__init__(display)
        self._engine = None
        self._menu = None
        self._controls = _Controls()
        self._panel = np.zeros((64, 64, 3), dtype=np.uint8)
        self._hud = _Hud()
        self.reset()

    def reset(self):
        """Back to the pre-game menu; the engine starts when the player does."""
        self.state = GameState.PLAYING
        self.score = 0
        self.close()
        self._controls = _Controls()
        self._hud = _Hud()
        self._cleared = None               # msg_serial-like guard: tally already recorded
        choices = _choices() if _available() else []
        if not choices:
            self.state = GameState.GAME_OVER
            return
        self._menu = _Menu(choices)

    def _start(self):
        self._menu.save()
        self._engine = start_engine(self._menu.choice.iwad, self._menu.launch_args())
        if self._engine is None:           # engine won't start (wrong build, no memory)
            self.state = GameState.GAME_OVER

    def close(self):
        if self._engine is not None:
            self._engine.close()
            self._engine = None

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return
        now = time.monotonic()
        inp = dict(
            up=input_state.up, down=input_state.down,
            left=input_state.left, right=input_state.right,
            L=input_state.action_l_held, R=input_state.action_r_held)
        events = self._controls.update(inp, self._engine.state if self._engine else None, dt)
        if self._controls.exit:
            self.state = GameState.GAME_OVER
            return
        if self._engine is None:           # in the menu
            m = self._menu
            m.move((1 if input_state.right_pressed else 0) - (1 if input_state.left_pressed else 0),
                   (1 if input_state.down_pressed else 0) - (1 if input_state.up_pressed else 0))
            m.draw(self._panel, now)
            if input_state.action_l or input_state.action_r:
                self._start()
        else:
            if self._engine.proc.poll() is not None:
                self.state = GameState.GAME_OVER
                return
            for pressed, k in events:
                self._engine.key(pressed, k)
            compose(self._panel, self._engine, self._hud, now)
            self._track_progress(self._engine.state)
        if self._controls.both_t > EXIT_BAR_AFTER:
            _draw_exit_bar(self._panel, self._controls.both_t / self._controls.EXIT_HOLD)

    def _track_progress(self, es):
        """At the level-end tally, remember the next map for the menu's MAP row."""
        if not es or es.get('gamestate') != 1:
            self._cleared = None
            return
        wi = es['wi']
        if wi['state'] == 0 and wi['next'] >= 0 and self._cleared != wi['next']:
            self._cleared = wi['next']
            self._menu.record_cleared(wi['next'] + 1)

    def draw(self):
        blit(self.display, self._panel)
