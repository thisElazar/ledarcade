#!/usr/bin/env python3
"""
LED Arcade - Cabinet Mirror
===========================
Whatever the cabinet's panel is showing, live in a window, in the look of the
square marketing clips (paper_display.PanelDisplay). Watch only: play on the
cabinet.

    python run_mirror.py             # cabinet at arcade.local
    python run_mirror.py 192.168.1.42

ESC or closing the window quits. See mirror.py for the protocol.
"""

import socket
import sys
import time

import numpy as np
import pygame

from arcade import GRID_SIZE
from mirror import MIRROR_PORT, HELLO
from paper_display import PanelDisplay

FRAME_BYTES = GRID_SIZE * GRID_SIZE * 3


def main(host="arcade.local"):
    addr = (socket.gethostbyname(host), MIRROR_PORT)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(False)

    display = PanelDisplay()
    clock = pygame.time.Clock()
    last_hello = last_frame = 0.0
    live = None

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN
                                             and event.key == pygame.K_ESCAPE):
                return

        now = time.monotonic()
        if now - last_hello > 1.0:
            sock.sendto(HELLO, addr)
            last_hello = now

        # Drain the socket, keep only the newest frame
        frame = None
        try:
            while True:
                data = sock.recv(65535)
                if len(data) == FRAME_BYTES:
                    frame = data
        except OSError:
            pass
        if frame is not None:
            display.buffer = np.frombuffer(frame, dtype=np.uint8).reshape(GRID_SIZE, GRID_SIZE, 3)
            display.render()
            last_frame = now

        was_live, live = live, last_frame > 0 and now - last_frame < 2.0
        if live != was_live:
            pygame.display.set_caption(f"Wonder Cabinet - {host}" if live
                                       else f"Wonder Cabinet - waiting for {host}...")
        clock.tick(60)


if __name__ == "__main__":
    main(*sys.argv[1:2])
