"""
Build a tiny original Game Boy test ROM for the GAME BOY player.

No Nintendo code or data: a hand-assembled program that shows a 256x256
tile "overworld", a sprite the D-pad walks around, A/B held to scroll the
map instead, SELECT to toggle a dialogue-style window along the bottom and
START to invert the palette. It polls LY instead of HALTing, so it is a
worst case for emulator speed.

    python tools/build_gb_rom.py [out.gb]      # default: ../gb_roms/ledtest.gb
"""

import os
import random
import sys

# ── Tiles (2bpp; '0'-'3' are shades, 0 lightest / transparent for sprites) ──

TILES = [
    # 0 grass
    ["00000000", "00010000", "00000000", "00000001",
     "00000000", "01000000", "00000000", "00000100"],
    # 1 tree
    ["00333300", "03322330", "33222233", "32222223",
     "33222233", "03333330", "00011000", "00111100"],
    # 2 water
    ["22222222", "22122222", "21212222", "22222122",
     "22221212", "22222222", "12222222", "21222222"],
    # 3 hero (sprite)
    ["00333300", "03111130", "03131310", "00111100",
     "03222230", "31222213", "00222200", "00300300"],
    # 4 text box
    ["00000000", "00000000", "00000000", "00000000",
     "00000000", "00000000", "00000000", "00000000"],
    # 5 "text"
    ["00000000", "03330330", "00000000", "03303330",
     "00000000", "03333000", "00000000", "00000000"],
    # 6 text box border
    ["33333333", "00000000", "00000000", "00000000",
     "00000000", "00000000", "00000000", "00000000"],
]


def encode_tile(rows):
    out = bytearray()
    for row in rows:
        lo = hi = 0
        for i, ch in enumerate(row):
            v = int(ch)
            lo |= (v & 1) << (7 - i)
            hi |= (v >> 1) << (7 - i)
        out += bytes((lo, hi))
    return out


def world_map(seed=7):
    """32x32 tiles: grass with tree clumps, a lake and a tree border."""
    rnd = random.Random(seed)
    m = [[0] * 32 for _ in range(32)]
    for _ in range(40):
        x, y = rnd.randrange(32), rnd.randrange(32)
        for dy in range(rnd.randrange(1, 3)):
            for dx in range(rnd.randrange(1, 4)):
                m[(y + dy) % 32][(x + dx) % 32] = 1
    for y in range(18, 26):
        for x in range(4, 14):
            if (x - 9) ** 2 / 25 + (y - 22) ** 2 / 16 < 1:
                m[y][x] = 2
    for i in range(32):
        m[0][i] = m[31][i] = m[i][0] = m[i][31] = 1
    return bytes(t for row in m for t in row)


def window_map():
    """Dialogue box: a border row, then rows of 'text'."""
    m = bytearray([4] * 1024)
    for x in range(20):
        m[x] = 6
    for y in (1, 3):
        for x in range(1, 19):
            m[y * 32 + x] = 5 if (x * 7 + y) % 5 else 4
    return bytes(m)


# ── A minimal SM83 assembler ─────────────────────────────────────

class Asm:
    def __init__(self, org):
        self.org, self.code, self.labels, self.fixups = org, bytearray(), {}, []

    def label(self, name):
        self.labels[name] = self.org + len(self.code)

    def db(self, *bs):
        self.code += bytes(bs)

    def jr(self, op, name):
        self.db(op, 0)
        self.fixups.append((len(self.code) - 1, name))

    def call(self, name, op=0xCD):
        self.db(op, 0, 0)
        self.fixups.append((len(self.code) - 2, name, 'abs'))

    def jp(self, name):
        self.call(name, 0xC3)

    def link(self):
        for f in self.fixups:
            at, name = f[0], f[1]
            target = self.labels[name]
            if len(f) == 3:
                self.code[at:at + 2] = target.to_bytes(2, 'little')
            else:
                rel = target - (self.org + at + 1)
                assert -128 <= rel < 128, name
                self.code[at] = rel & 0xFF
        return bytes(self.code)


JR, JR_NZ, JR_Z = 0x18, 0x20, 0x28
LDH_A, LDH_TO = 0xF0, 0xE0
LCDC, STAT, SCY, SCX, LY, BGP, OBP0, WY, WX, P1 = 0x40, 0x41, 0x42, 0x43, 0x44, 0x47, 0x48, 0x4A, 0x4B, 0x00
JOY, PREV, PRESSED = 0x80, 0x81, 0x82          # HRAM variables
TILE_DATA, BG_DATA, WIN_DATA = 0x1000, 0x2000, 0x2400
OAM_Y, OAM_X = 0xFE00, 0xFE01


def program():
    a = Asm(0x150)
    a.db(0xF3, 0x31, 0xFE, 0xFF)                # di; ld sp, $FFFE
    a.label('vb0')                              # LCD off only in vblank
    a.db(LDH_A, LY, 0xFE, 144); a.jr(JR_NZ, 'vb0')
    a.db(0xAF, LDH_TO, LCDC)                    # xor a; ldh (LCDC), a
    for src, dst, n in ((TILE_DATA, 0x8000, 16 * len(TILES)), (BG_DATA, 0x9800, 1024),
                        (WIN_DATA, 0x9C00, 1024)):
        a.db(0x21, *src.to_bytes(2, 'little'), 0x11, *dst.to_bytes(2, 'little'),
             0x01, *n.to_bytes(2, 'little'))
        a.call('copy')
    a.db(0x21, 0x00, 0xFE, 0x06, 160, 0xAF)     # clear OAM: ld hl,$FE00; ld b,160; xor a
    a.label('oam'); a.db(0x22, 0x05); a.jr(JR_NZ, 'oam')
    a.db(0x3E, 88, 0xEA, *OAM_Y.to_bytes(2, 'little'))   # hero mid-screen
    a.db(0x3E, 84, 0xEA, *OAM_X.to_bytes(2, 'little'))
    a.db(0x3E, 3, 0xEA, 0x02, 0xFE)             # tile 3
    a.db(0x3E, 0xE4, LDH_TO, BGP, LDH_TO, OBP0)
    a.db(0x3E, 104, LDH_TO, WY, 0x3E, 7, LDH_TO, WX)
    a.db(0xAF, LDH_TO, SCX, LDH_TO, SCY, LDH_TO, PREV)
    a.db(0x3E, 0xD3, LDH_TO, LCDC)              # LCD on, window map $9C00, window off

    a.label('main')
    a.label('vb'); a.db(LDH_A, LY, 0xFE, 144); a.jr(JR_NZ, 'vb')
    a.call('joy')                               # a = held (buttons << 4 | dpad)
    a.db(0x47)                                  # ld b, a
    a.db(LDH_A, PREV, 0x2F, 0xA0, LDH_TO, PRESSED)   # pressed = ~prev & held
    a.db(0x78, LDH_TO, PREV)
    a.db(0x78, 0xE6, 0x30); a.jr(JR_Z, 'walk')  # A or B held: scroll the map
    for bit, reg, op in ((0, SCX, 0x3C), (1, SCX, 0x3D), (2, SCY, 0x3D), (3, SCY, 0x3C)):
        a.db(0xCB, 0x40 + 8 * bit); a.jr(JR_Z, f's{bit}')
        a.db(LDH_A, reg, op, LDH_TO, reg)
        a.label(f's{bit}')
    a.jr(JR, 'btn')
    a.label('walk')
    for bit, addr, op in ((0, OAM_X, 0x3C), (1, OAM_X, 0x3D), (2, OAM_Y, 0x3D), (3, OAM_Y, 0x3C)):
        a.db(0xCB, 0x40 + 8 * bit); a.jr(JR_Z, f'w{bit}')
        a.db(0xFA, *addr.to_bytes(2, 'little'), op, 0xEA, *addr.to_bytes(2, 'little'))
        a.label(f'w{bit}')
    a.label('btn')
    a.db(LDH_A, PRESSED, 0x47)                  # b = pressed
    a.db(0xCB, 0x70); a.jr(JR_Z, 'nosel')       # bit 6 = SELECT: toggle window
    a.db(LDH_A, LCDC, 0xEE, 0x20, LDH_TO, LCDC)
    a.label('nosel')
    a.db(0xCB, 0x78); a.jr(JR_Z, 'nostart')     # bit 7 = START: invert palette
    a.db(LDH_A, BGP, 0x2F, LDH_TO, BGP)
    a.label('nostart')
    a.label('out'); a.db(LDH_A, LY, 0xFE, 144); a.jr(JR_Z, 'out')
    a.jp('main')

    a.label('copy')                             # BC bytes from HL to DE
    a.db(0x2A, 0x12, 0x13, 0x0B, 0x78, 0xB1); a.jr(JR_NZ, 'copy')
    a.db(0xC9)

    a.label('joy')                              # -> a = buttons << 4 | dpad, 1 = held
    a.db(0x3E, 0x20, LDH_TO, P1, LDH_A, P1, LDH_A, P1, 0x2F, 0xE6, 0x0F, 0x4F)
    a.db(0x3E, 0x10, LDH_TO, P1, LDH_A, P1, LDH_A, P1, 0x2F, 0xE6, 0x0F, 0xCB, 0x37, 0xB1)
    a.db(0x4F, 0x3E, 0x30, LDH_TO, P1, 0x79, 0xC9)
    return a.link()


def build():
    rom = bytearray(32 * 1024)
    rom[0x100:0x104] = bytes((0x00, 0xC3, 0x50, 0x01))     # nop; jp $0150
    title = b'LEDTEST'
    rom[0x134:0x134 + len(title)] = title
    rom[0x147:0x14A] = bytes((0x00, 0x00, 0x00))            # ROM only, 32 KB, no RAM
    rom[0x14D] = (-sum(rom[0x134:0x14D]) - (0x14D - 0x134)) & 0xFF
    code = program()
    assert 0x150 + len(code) <= TILE_DATA
    rom[0x150:0x150 + len(code)] = code
    tiles = b''.join(encode_tile(t) for t in TILES)
    rom[TILE_DATA:TILE_DATA + len(tiles)] = tiles
    rom[BG_DATA:BG_DATA + 1024] = world_map()
    rom[WIN_DATA:WIN_DATA + 1024] = window_map()
    total = (sum(rom) - rom[0x14E] - rom[0x14F]) & 0xFFFF
    rom[0x14E:0x150] = total.to_bytes(2, 'big')
    return bytes(rom)


if __name__ == '__main__':
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(here), 'gb_roms', 'ledtest.gb')
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, 'wb') as f:
        f.write(build())
    print(out)
