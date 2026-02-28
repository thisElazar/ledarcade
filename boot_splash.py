#!/usr/bin/env python3
"""
Boot Splash - instant feedback while the arcade loads.

Minimal imports so this starts as fast as possible.
Shows a single pulsing dot in the center of the display.
Killed by start.sh once the main process is ready.
"""

import sys
import time
import math
import signal
import os

# Write PID so start.sh / run_hardware.py can kill us
PID_FILE = "/tmp/led-arcade-bootsplash.pid"
os.makedirs(os.path.dirname(PID_FILE), exist_ok=True)
with open(PID_FILE, "w") as f:
    f.write(str(os.getpid()))


def cleanup(*_):
    try:
        os.remove(PID_FILE)
    except OSError:
        pass
    sys.exit(0)

signal.signal(signal.SIGTERM, cleanup)
signal.signal(signal.SIGINT, cleanup)

try:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions
except ImportError:
    print("boot_splash: rgbmatrix not available, exiting")
    cleanup()

# Minimal matrix init — match hardware settings
options = RGBMatrixOptions()
options.rows = 64
options.cols = 64
options.hardware_mapping = 'led-arcade'
options.gpio_slowdown = 4
options.brightness = 80
options.drop_privileges = False

matrix = RGBMatrix(options=options)
canvas = matrix.CreateFrameCanvas()

# Pulsing dot in center
CX, CY = 31, 31
t = 0.0

while True:
    # Breathe: brightness oscillates smoothly
    breath = (math.sin(t * 2.5) + 1.0) / 2.0  # 0..1
    bright = int(30 + 225 * breath)
    dim = int(10 + 50 * breath)

    canvas.Clear()
    # Core pixel
    canvas.SetPixel(CX, CY, bright, bright, bright)
    # Soft halo (4 neighbors)
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        canvas.SetPixel(CX + dx, CY + dy, dim, dim, dim)

    canvas = matrix.SwapOnVSync(canvas)
    time.sleep(1 / 30.0)
    t += 1 / 30.0
