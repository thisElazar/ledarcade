"""
Doom Demo - Attract Mode
========================
Freedoom's own recorded demos (the WAD's DEMO1-4 lumps) played back by the
engine and rendered exactly like the game: zoomed view, monster highlight,
STATUS HUD. The engine quits when a demo ends and another one starts.

Listed, and picked for the idle screen, only while the AFTER HOURS lever is on
and the engine is installed (catalog.listed_now), like the game itself.
"""

import random
import time

import numpy as np

from . import Visual, Display

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.doom import (_Hud, _available, _installed_wads, _wad_demos,
                        blit, compose, start_engine)

MIN_RUN = 3.0      # s; an engine that dies sooner is broken, so stop relaunching it


class DoomDemo(Visual):
    name = "DOOM"
    description = "Freedoom plays itself"
    category = "demos"
    mature = True                             # AFTER HOURS only, like the game
    menu_visible = staticmethod(_available)   # ...and only with the engine installed

    def reset(self):
        self.time = 0.0
        self.close()
        self._panel = np.zeros((64, 64, 3), dtype=np.uint8)
        self._next_demo()

    def _next_demo(self):
        self.close()
        self._hud = _Hud()
        self._started = time.monotonic()
        wads = _installed_wads() if _available() else []
        if wads:
            iwad = random.choice(wads)[1]
            demos = _wad_demos(iwad)
            if demos:
                self._engine = start_engine(iwad, ['-playdemo', random.choice(demos)])

    def handle_input(self, input_state):
        return False      # auto-plays

    def update(self, dt):
        self.time += dt
        if self._engine is None:
            return
        if self._engine.proc.poll() is not None:        # the demo ended
            if time.monotonic() - self._started < MIN_RUN:
                self.close()                            # ...far too soon: give up
            else:
                self._next_demo()
            return
        compose(self._panel, self._engine, self._hud, time.monotonic())

    def draw(self):
        blit(self.display, self._panel)

    def close(self):
        engine = getattr(self, '_engine', None)
        if engine is not None:
            engine.close()
        self._engine = None
