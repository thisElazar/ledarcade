"""
Display Mirror
==============
Watch the cabinet's panel live in a window on a laptop:

    python run_mirror.py             # on the laptop; cabinet at arcade.local

The viewer sends a small hello datagram to MIRROR_PORT once a second. While
hellos keep arriving, the cabinet answers every rendered frame with one
datagram holding the 64x64 RGB framebuffer. With nobody watching, the cost is
one non-blocking recvfrom per frame.

UDP on purpose: a slow or vanished viewer can never stall the render loop, and
a lost frame is simply skipped.
"""

import socket
import time

MIRROR_PORT = 6464
HELLO = b"WCMIRROR"
VIEWER_TIMEOUT = 3.0   # seconds without a hello before the cabinet stops sending


class MirrorTap:
    """Cabinet side: hand each rendered framebuffer to send()."""

    def __init__(self, port=MIRROR_PORT):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # A frame is 12 KB; macOS refuses datagrams over 9 KB by default
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
        self.sock.bind(("", port))
        self.sock.setblocking(False)
        self.viewer = None
        self.seen = 0.0

    def send(self, fb):
        try:
            for _ in range(4):
                data, addr = self.sock.recvfrom(64)
                if data == HELLO:
                    self.viewer, self.seen = addr, time.monotonic()
        except OSError:
            pass   # nothing waiting
        if self.viewer is None:
            return
        if time.monotonic() - self.seen > VIEWER_TIMEOUT:
            self.viewer = None
            return
        try:
            self.sock.sendto(fb, self.viewer)
        except OSError:
            pass   # send buffer full or network down: drop the frame
