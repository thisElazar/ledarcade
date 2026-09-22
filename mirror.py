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

HDMI output is one more viewer: HdmiOutput keeps run_hdmi.py running on the
cabinet itself while a screen is plugged into the Pi. So is the web mirror:
WebOutput keeps run_web_mirror.py running while MIRROR > WEB is on, which
re-serves the frames to browsers on the network over HTTP, on the same port:
the mirror's own is UDP and a browser speaks TCP, so the two never collide.
"""

import glob
import os
import socket
import subprocess
import sys
import threading
import time

MIRROR_PORT = 30203          # "WONDE", each letter turned until it is a digit; a palindrome, like a mirror
PORT_RANGE = (1024, 32767)   # above the system ports, below the ones Linux hands out itself
HELLO = b"WCMIRROR"
VIEWER_TIMEOUT = 3.0   # seconds without a hello before the cabinet stops sending
MAX_VIEWERS = 4        # each one costs the cabinet's Wi-Fi about 3 Mbit/s


class MirrorTap:
    """Cabinet side: hand each rendered framebuffer to send()."""

    def __init__(self, port=MIRROR_PORT, host=""):
        """host "" serves the network; "127.0.0.1" only the cabinet's own HDMI output."""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # A frame is 12 KB; macOS refuses datagrams over 9 KB by default
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
        self.sock.bind((host, port))
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


class HdmiOutput:
    """Cabinet side: run_hdmi.py runs while a screen is plugged into the Pi."""

    SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_hdmi.py")

    def __init__(self, port):
        self.port = port
        self.proc = None
        self.started = self.checked = 0.0
        self.failures = 0

    def poll(self):
        """Call every frame; looks at the HDMI connector every two seconds."""
        now = time.monotonic()
        if now - self.checked < 2.0:
            return
        self.checked = now

        plugged = False
        for path in glob.glob("/sys/class/drm/card*-HDMI-A-*/status"):
            with open(path) as f:
                plugged = plugged or f.read().strip() == "connected"

        if self.proc is not None and self.proc.poll() is not None:
            # It quit on its own. Starting Python costs the game a second of CPU,
            # so a viewer that keeps dying at once (no GPU, say) is given up on.
            self.failures = self.failures + 1 if now - self.started < 10.0 else 0
            self.proc = None
        if plugged and self.proc is None and self.failures < 3:
            # stdin is the viewer's lifeline: it exits when our end closes,
            # which also covers a crash and the re-exec after UPDATE
            self.proc = subprocess.Popen(
                [sys.executable, self.SCRIPT, "--port", str(self.port), "--cabinet"],
                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL)
            self.started = now
        elif not plugged:
            self.close()
            self.failures = 0

    def close(self):
        if self.proc is not None:
            self.proc.stdin.close()
            self.proc = None


class WebOutput:
    """Cabinet side: run_web_mirror.py serves the panel to browsers while it is on."""

    SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_web_mirror.py")

    def __init__(self, port):
        self.port = port
        self.proc = None
        self.started = self.checked = 0.0
        self.failures = 0

    def poll(self):
        """Call every frame; looks in on the server every two seconds."""
        now = time.monotonic()
        if now - self.checked < 2.0:
            return
        self.checked = now

        if self.proc is not None and self.proc.poll() is not None:
            # As with HdmiOutput: a server that keeps dying at once (its port
            # already taken, say) is given up on rather than restarted forever.
            self.failures = self.failures + 1 if now - self.started < 10.0 else 0
            self.proc = None
        if self.proc is None and self.failures < 3:
            # stdin is the server's lifeline, as for run_hdmi.py
            self.proc = subprocess.Popen(
                [sys.executable, self.SCRIPT, "--port", str(self.port), "--cabinet"],
                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL)
            self.started = now

    def close(self):
        if self.proc is not None:
            self.proc.stdin.close()
            self.proc = None


def exit_with_parent():
    """Viewer side: the cabinet holds the other end of stdin. It closes when the
    cabinet exits, crashes, or re-execs itself after UPDATE; leave with it."""
    def wait():
        while os.read(0, 4096):   # the raw fd: a buffered read would hold a lock at shutdown
            pass
        os._exit(0)
    threading.Thread(target=wait, daemon=True).start()


def lan_address():
    """The cabinet's address on the network, as a browser must type it, or ""."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("192.0.2.1", 9))   # a reserved address: routed, never answered
        return sock.getsockname()[0]
    except OSError:
        return ""   # no network
    finally:
        sock.close()
