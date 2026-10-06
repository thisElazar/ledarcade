"""
How fast does HANDHELD run on this machine? Run it on the cabinet's Pi.

    python tools/build_gb_rom.py /tmp/gb/ledtest.gb
    python tools/gb_bench.py /tmp/gb/ledtest.gb [your_rom.gb ...]

For each ROM: raw emulator speed (frames per second, real time is 59.7),
then the per-frame cost of the whole HANDHELD update (emulate + downscale)
in each view. Under ~16 ms per cabinet frame keeps full speed at 60 fps;
under ~33 ms is full speed at 30 fps (the game catches up by running up
to 4 Game Boy frames per update).
"""

import os
import sys
import time
import warnings

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np                                   # noqa: E402

from games import handheld as hh                     # noqa: E402

BOOT_FRAMES = 300
FRAMES = 600


def bench(rom):
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        from pyboy import PyBoy
    pb = PyBoy(rom, window='null', sound_emulated=False, log_level='ERROR')
    pb.set_emulation_speed(0)
    pb.tick(BOOT_FRAMES, False)
    t = time.perf_counter()
    pb.tick(FRAMES, True)
    emu = FRAMES / (time.perf_counter() - t)
    screen = np.array(pb.screen.ndarray)
    oam, lcdc = pb.memory[0xFE00:0xFEA0], pb.memory[0xFF40]
    pb.stop(save=False)

    print(f'{hh.rom_title(rom)}')
    print(f'  emulator      {emu:7.0f} fps  ({emu / hh.GB_FPS:.1f}x real time)')
    per_frame = 1000 / emu
    def zoom():
        hh.sprite_focus(oam, lcdc)
        return hh.render_zoom(screen, 16, 8)

    for name, fn in (('zoom', zoom), ('fit', lambda: hh.render_fit(screen))):
        t = time.perf_counter()
        for _ in range(200):
            fn()
        ms = (time.perf_counter() - t) / 200 * 1000
        print(f'  {name:4} view     {ms:6.2f} ms downscale, '
              f'{per_frame + ms:6.2f} ms per 60 fps frame')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for path in sys.argv[1:]:
        bench(path)
