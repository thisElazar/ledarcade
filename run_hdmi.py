#!/usr/bin/env python3
"""
LED Arcade - HDMI Output
========================
The cabinet's panel, live and full screen, on a TV or monitor plugged into the
Pi's HDMI port, in the look of the marketing clips. The cabinet starts this
itself (mirror.HdmiOutput) while MIRROR > HDMI is on and a screen is connected;
it is one more viewer of the mirror (mirror.py), over 127.0.0.1.

A Pi 3B running a game has no CPU to spare for PanelDisplay's compositing, so
here the GPU does the work. Each frame uploads two 64x64 textures and draws
three quads:

    the frame, scaled up unfiltered          square LEDs
    x a dot mask (render_clip's)             round LEDs on black
    + the blurred frame, scaled up filtered  the glow, screen-blended

To try it on a desktop against a cabinet:

    python run_hdmi.py --window --host arcade.local
"""

import argparse
import os
import socket
import threading
import time

import numpy as np

from mirror import MIRROR_PORT, HELLO

GRID_SIZE = 64
FRAME_BYTES = GRID_SIZE * GRID_SIZE * 3

# SDL_ComposeCustomBlendMode(ONE_MINUS_DST_COLOR, ONE, ADD, ZERO, ONE, ADD):
# dst = src * (1 - dst) + dst, which is "screen". pygame doesn't wrap the call,
# but the mode is only this packed integer.
BLENDMODE_SCREEN = 0x1 | 0x8 << 4 | 0x2 << 8 | 0x1 << 16 | 0x1 << 20 | 0x2 << 24


def exit_with_parent():
    """The cabinet holds the other end of stdin. It closes when the cabinet
    exits, crashes, or re-execs itself after UPDATE; leave with it."""
    def wait():
        while os.read(0, 4096):   # the raw fd: a buffered read would hold a lock at shutdown
            pass
        os._exit(0)
    threading.Thread(target=wait, daemon=True).start()


def main(host, port, window, cabinet):
    if cabinet:
        os.nice(10)   # never compete with the game
        exit_with_parent()
    if not window:
        os.environ.setdefault("SDL_VIDEODRIVER", "kmsdrm")

    import pygame
    from pygame._sdl2.video import Window, Renderer, Texture
    pygame.display.init()
    # After display.init(): render_clip defaults SDL to the headless dummy driver at import
    from tools.render_clip import _dot_mask

    if window:
        win = Window("Wonder Cabinet - HDMI", size=(1280, 720))
    else:
        win = Window("Wonder Cabinet", fullscreen_desktop=True)
        pygame.mouse.set_visible(False)
    renderer = Renderer(win, vsync=True)
    w, h = win.size
    side = min(w, h) // GRID_SIZE * GRID_SIZE   # whole pixels per LED
    panel = pygame.Rect((w - side) // 2, (h - side) // 2, side, side)

    mask = _dot_mask()[..., 0]
    gain = float(mask.mean())   # lit share of each LED cell, as in PanelDisplay
    dots = np.repeat((mask * 255).astype(np.uint8)[..., None], 3, axis=2)

    def texture(filtered, surface=None):
        os.environ["SDL_RENDER_SCALE_QUALITY"] = "1" if filtered else "0"   # read when a texture is created
        if surface is not None:
            return Texture.from_surface(renderer, surface)
        return Texture(renderer, (GRID_SIZE, GRID_SIZE), streaming=True)

    leds = texture(False)
    glow = texture(True)
    dot_mask = texture(True, pygame.image.frombuffer(dots.tobytes(), dots.shape[1::-1], "RGB"))
    dot_mask.blend_mode = pygame.BLENDMODE_MOD
    try:
        glow.blend_mode = BLENDMODE_SCREEN
    except pygame.error:
        glow.blend_mode = pygame.BLENDMODE_ADD   # renderer without custom blend modes

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.25)
    addr = (socket.gethostbyname(host), port)
    last_hello = 0.0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN
                                             and event.key == pygame.K_ESCAPE):
                return

        now = time.monotonic()
        if now - last_hello > 0.2:
            sock.sendto(HELLO, addr)
            last_hello = now

        # Wait for a frame, then skip to the newest one waiting
        frame = None
        try:
            data = sock.recv(65535)
            sock.setblocking(False)
            while True:
                if len(data) == FRAME_BYTES:
                    frame = data
                data = sock.recv(65535)
        except OSError:
            pass
        sock.settimeout(0.25)
        if frame is None:
            continue

        # PanelDisplay's glow: [1 4 1]/6 blur at LED resolution; the GPU's
        # filtered upscale stands in for its smoothscale
        buf = np.frombuffer(frame, dtype=np.uint8).reshape(GRID_SIZE, GRID_SIZE, 3)
        g = np.pad(buf * gain, ((1, 1), (1, 1), (0, 0)), mode="edge")
        g = (g[:-2] + 4 * g[1:-1] + g[2:]) / 6
        g = (g[:, :-2] + 4 * g[:, 1:-1] + g[:, 2:]) / 6

        leds.update(pygame.image.frombuffer(frame, (GRID_SIZE, GRID_SIZE), "RGB"))
        glow.update(pygame.image.frombuffer(g.astype(np.uint8).tobytes(), (GRID_SIZE, GRID_SIZE), "RGB"))
        renderer.draw_color = (0, 0, 0, 255)
        renderer.clear()
        leds.draw(dstrect=panel)
        dot_mask.draw(dstrect=panel)
        glow.draw(dstrect=panel)
        renderer.present()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Show the cabinet's panel full screen on HDMI.")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=MIRROR_PORT)
    ap.add_argument("--window", action="store_true", help="a desktop window instead of the HDMI screen")
    ap.add_argument("--cabinet", action="store_true",
                    help="started by the cabinet: low priority, and exit when it does")
    args = ap.parse_args()
    main(args.host, args.port, args.window, args.cabinet)
