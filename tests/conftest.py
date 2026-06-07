"""Pytest configuration for the LED Arcade smoke tests.

The tests construct the real pygame `Display`, so we force SDL into headless
("dummy") mode before pygame is ever imported. This lets the whole catalog be
exercised on a CI runner with no screen, audio device, or LED matrix.
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

# Tests import top-level modules (arcade, visuals, games) — make sure the repo
# root is importable regardless of where pytest is invoked from.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
