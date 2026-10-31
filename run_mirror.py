#!/usr/bin/env python3
"""
LED Arcade - Cabinet Mirror
===========================
Whatever the cabinet's panel is showing, live in a window, in the look of the
square marketing clips (paper_display.PanelDisplay). Watch only: play on the
cabinet.

    python run_mirror.py                  # cabinet at arcade.local
    python run_mirror.py 192.168.1.42
    python run_mirror.py --delay 0.4      # deeper buffer for rough Wi-Fi; 0 = none
    python run_mirror.py --port 6464      # if the cabinet's MIRROR menu sets another port

The window resizes, the panel staying square in the middle of it. ESC or closing it quits. See mirror.py for the protocol.
"""

import argparse
import socket
import time
from collections import deque

import numpy as np
import pygame

from arcade import GRID_SIZE
from mirror import MIRROR_PORT, HELLO
from paper_display import PanelDisplay

FRAME_BYTES = GRID_SIZE * GRID_SIZE * 3
FPS = 30   # the cabinet's nominal rate, until arrivals have been measured


def main(host="arcade.local", delay=0.2, port=MIRROR_PORT):
    addr = (socket.gethostbyname(host), port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(False)

    display = PanelDisplay()

    # Frames wait `delay` seconds in a queue and play out at an even pace, so
    # Wi-Fi hiccups (frames held up ~150 ms, then delivered in a burst) don't
    # show. The packets carry no timestamps; the pace is the measured arrival
    # rate, nudged by how full the queue is: slower while it is short, faster
    # after a burst. That also rides out clock drift and visuals under 30 fps.
    queue = deque(maxlen=int(delay * FPS) * 3 + 10)
    arrivals = deque(maxlen=2 * FPS)
    next_play = last_hello = last_frame = 0.0
    live = None

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN
                                             and event.key == pygame.K_ESCAPE):
                return

        now = time.monotonic()
        # 5 hellos a second, far more than the subscription needs: the steady
        # trickle keeps the Pi's Wi-Fi out of power save. At one a second its
        # radio dozes, the send queue backs up, and 30 fps arrives as 8.
        if now - last_hello > 0.2:
            try:
                sock.sendto(HELLO, addr)
            except OSError:
                pass   # network down (laptop asleep, Wi-Fi dropped): keep waiting
            last_hello = now

        try:
            while True:
                data = sock.recv(65535)
                if len(data) == FRAME_BYTES:
                    queue.append(data)
                    arrivals.append(now)
        except OSError:
            pass   # socket drained

        if queue and now >= next_play:
            frame = queue.popleft()
            display.buffer = np.frombuffer(frame, dtype=np.uint8).reshape(GRID_SIZE, GRID_SIZE, 3)
            display.render()
            last_frame = now

            source = 1 / FPS
            if len(arrivals) > 10 and 0.2 < now - arrivals[0] < 4.0 and arrivals[-1] > arrivals[0]:
                source = (arrivals[-1] - arrivals[0]) / (len(arrivals) - 1)
            short = delay / source - len(queue)   # frames below the target depth
            interval = source * min(1.5, max(0.5, 1 + 0.1 * short))
            next_play = next_play + interval if now - next_play < interval else now + interval

        was_live, live = live, last_frame > 0 and now - last_frame < 2.0
        if live != was_live:
            pygame.display.set_caption(f"Wonder Cabinet - {host}" if live
                                       else f"Wonder Cabinet - waiting for {host}...")
        time.sleep(0.002)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Watch the cabinet's panel live.")
    ap.add_argument("host", nargs="?", default="arcade.local")
    ap.add_argument("--delay", type=float, default=0.2,
                    help="seconds of playback buffer (default 0.2; 0 shows frames as they arrive)")
    ap.add_argument("--port", type=int, default=MIRROR_PORT,
                    help=f"the cabinet's MIRROR port (default {MIRROR_PORT})")
    args = ap.parse_args()
    main(args.host, args.delay, args.port)
