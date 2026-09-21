"""
Display Mirror
==============
Watch the cabinet's panel live in a window on a laptop:

    python run_mirror.py             # on the laptop; cabinet at arcade.local

Off until it is switched on in the cabinet's MIRROR menu, which also sets the port.

The viewer sends a small hello datagram to MIRROR_PORT a few times a second. While
hellos keep arriving, the cabinet answers every rendered frame with one
datagram holding the 64x64 RGB framebuffer. Up to MAX_VIEWERS can watch at
once. With nobody watching, the cost is one non-blocking recvfrom per frame.

UDP on purpose: a slow or vanished viewer can never stall the render loop, and
a lost frame is simply skipped.
"""

import socket
import time

MIRROR_PORT = 30203          # "WONDE", each letter turned until it is a digit; a palindrome, like a mirror
PORT_RANGE = (1024, 32767)   # above the system ports, below the ones Linux hands out itself
HELLO = b"WCMIRROR"
VIEWER_TIMEOUT = 3.0   # seconds without a hello before the cabinet stops sending
MAX_VIEWERS = 4        # each one costs the cabinet's Wi-Fi about 3 Mbit/s


class MirrorTap:
    """Cabinet side: hand each rendered framebuffer to send()."""

    def __init__(self, port=MIRROR_PORT):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # A frame is 12 KB; macOS refuses datagrams over 9 KB by default
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
        self.sock.bind(("", port))
        self.sock.setblocking(False)
        self.viewers = {}   # address -> time of its last hello

    def close(self):
        self.sock.close()

    def send(self, fb):
        now = time.monotonic()
        try:
            for _ in range(8):
                data, addr = self.sock.recvfrom(64)
                if data == HELLO and (addr in self.viewers or len(self.viewers) < MAX_VIEWERS):
                    self.viewers[addr] = now
        except OSError:
            pass   # nothing waiting
        for addr, seen in list(self.viewers.items()):
            if now - seen > VIEWER_TIMEOUT:
                del self.viewers[addr]
                continue
            try:
                self.sock.sendto(fb, addr)
            except OSError:
                pass   # send buffer full or network down: drop the frame
