#!/usr/bin/env python3
"""
LED Arcade - Web Mirror
=======================
The cabinet's panel, live in a browser on the same Wi-Fi:

    http://arcade.local:30203

The cabinet starts this itself (mirror.WebOutput) while MIRROR > WEB is on. It
is one more viewer of the mirror (mirror.py), over 127.0.0.1, and re-serves
what it sees to any number of browsers at once. Browsers open the mirror's own
port: that one is UDP and this is TCP, so both live at the number in MIRROR.

The page draws the frames with site/shared.js's LEDRenderer, the same look as
the marketing clips, so the Pi does no compositing: it forwards 12 KB frames
and nothing else. A frame that is the same as the one before is not sent, so a
still screen (a menu, a paused game) costs a watching phone nothing.

The stream is simply one 64x64 RGB frame after another, 12288 bytes each, for
as long as the browser keeps reading.

To try it on a desktop against a cabinet:

    python run_web_mirror.py --host arcade.local
"""

import argparse
import ipaddress
import os
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from mirror import MIRROR_PORT, HELLO, exit_with_parent

GRID_SIZE = 64
FRAME_BYTES = GRID_SIZE * GRID_SIZE * 3
SITE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "site")
STILL_RESEND = 2.0    # seconds; a still screen still proves the browser is there.
                      # Must stay under the page's idle threshold below, or a
                      # screen that simply is not moving reads as a dead cabinet.

PAGE = b"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Wonder Cabinet</title>
<style>
  html, body { height: 100%; margin: 0; background: #000; }
  body { display: flex; align-items: center; justify-content: center;
         color: #6f6f6f; font: 12px/1 ui-monospace, SFMono-Regular, Menlo, monospace; }
  #panel { position: relative; width: min(100vw, 100vh); aspect-ratio: 1; }
  canvas { display: block; width: 100%; height: 100%; }
  #status { position: absolute; left: 0; right: 0; bottom: 6%; text-align: center;
            letter-spacing: .18em; text-transform: uppercase;
            opacity: 1; transition: opacity .5s; pointer-events: none; }
  #status.live { opacity: 0; }
</style>
</head>
<body>
<div id="panel"><canvas id="led"></canvas><div id="status">connecting</div></div>
<script src="shared.js"></script>
<script>
const FRAME = GRID * GRID * 3;
const renderer = new LEDRenderer(document.getElementById('led'));
const display = { buffer: new Uint8ClampedArray(FRAME) };
const statusEl = document.getElementById('status');
let drawing = false, idle = 0;

function say(text) {
  statusEl.textContent = text;
  statusEl.classList.toggle('live', text === '');
}

function draw() {
  drawing = false;
  renderer.render(display);
}

function frame(bytes) {
  display.buffer.set(bytes);
  if (!drawing) { drawing = true; requestAnimationFrame(draw); }
  clearTimeout(idle);
  idle = setTimeout(() => say('waiting for the cabinet'), 4000);
  say('');
}

// The stream is 12288-byte frames end to end; chunks arrive at any boundary.
async function watch() {
  const res = await fetch('stream', { cache: 'no-store' });
  if (!res.ok) throw new Error('stream ' + res.status);
  const reader = res.body.getReader();
  let held = new Uint8Array(0);
  for (;;) {
    const { value, done } = await reader.read();
    if (done) return;
    const buf = new Uint8Array(held.length + value.length);
    buf.set(held);
    buf.set(value, held.length);
    let at = 0;
    while (buf.length - at >= FRAME) {
      frame(buf.subarray(at, at + FRAME));
      at += FRAME;
    }
    held = buf.slice(at);
  }
}

(async function () {
  for (;;) {
    try {
      await watch();
    } catch (e) {
      // the cabinet restarted, the phone slept, the Wi-Fi dropped: wait and ask again
    }
    clearTimeout(idle);
    say('reconnecting');
    await new Promise(done => setTimeout(done, 1000));
  }
})();
</script>
</body>
</html>
"""


class Feed:
    """The newest frame from the cabinet, and how many new ones there have been."""

    def __init__(self):
        self.cond = threading.Condition()
        self.frame = None
        self.seq = 0

    def publish(self, frame):
        with self.cond:
            if frame == self.frame:
                return   # a still screen: nothing to send anyone
            self.frame, self.seq = frame, self.seq + 1
            self.cond.notify_all()

    def wait(self, seq):
        """Block for the next frame after seq; on a still screen, the same one
        again, which is also how a browser that has gone away is noticed."""
        with self.cond:
            if self.seq == seq:
                self.cond.wait(STILL_RESEND)
            return self.frame, self.seq


def subscribe(feed, host, port):
    """Cabinet side of the mirror protocol: hello in, frames out (mirror.py).

    Nothing watches this thread — WebOutput only sees that the process is
    alive — so if it ever died the page would sit on "waiting for the cabinet"
    for good. Every error here therefore ends in another turn of the loop.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.25)
    addr, next_resolve, last_hello, last_frame = None, 0.0, 0.0, 0.0
    while True:
        now = time.monotonic()
        # Resolving an mDNS name can block for hundreds of milliseconds, and
        # this is the thread draining the socket, so only look the cabinet up
        # while nothing is arriving from it anyway — which is also exactly when
        # it is worth looking up again, after a new lease moved it.
        if now >= next_resolve and now - last_frame > 5.0:
            try:
                addr = (socket.gethostbyname(host), port)
            except OSError:
                addr = None   # no DNS yet
            next_resolve = now + 5.0
        if addr is not None and now - last_hello > 0.2:
            try:
                sock.sendto(HELLO, addr)
            except OSError:
                pass   # the cabinet's tap is closed or moving: keep asking
            last_hello = now
        try:
            data = sock.recv(65535)
        except TimeoutError:
            continue   # nothing for 250 ms
        except OSError:
            time.sleep(0.25)   # a broken socket must not spin a core of a Pi 3B
            continue
        if len(data) == FRAME_BYTES:
            last_frame = now
            feed.publish(data)


class Server(ThreadingHTTPServer):
    """A thread per browser, and room for a houseful of them to arrive at once."""

    daemon_threads = True
    # The default backlog of 5 is easy to overflow when several screens open the
    # page together. macOS answers the overflow with a reset — one phone in six
    # was refused outright in testing; Linux, which is what the cabinet runs,
    # drops the SYN and makes the client wait instead. Neither is good. It must
    # be set before the socket listens.
    request_queue_size = 64
    # A viewer that cannot take a 12 KB frame in this long is asleep or gone.
    # Its thread ends, and the page reconnects by itself when it comes back.
    frame_timeout = 30.0


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    # Without this the stdlib never arms a socket timeout, and a connection that
    # goes quiet — a phone carried out of range mid-page-load, or anything that
    # opens a socket and says nothing — holds its thread for the life of the
    # process. The cabinet runs for weeks; threads cost 8 MB of stack each.
    timeout = 30.0

    def allowed_host(self):
        """An address, localhost or a .local name — never someone else's name.

        A page on the open web, served under a name that re-resolves to this
        cabinet, would otherwise become same-origin with it and could read the
        panel from outside the house. This is not authentication; it is the
        one hole a browser can open in "same Wi-Fi only".
        """
        host = self.headers.get("Host", "")
        if host.startswith("["):               # [::1]:30203
            host = host[1:].split("]")[0]
        elif host.count(":") == 1:             # 192.168.1.16:30203
            host = host.rsplit(":", 1)[0]
        host = host.lower()
        if host in ("", "localhost") or host.endswith(".local"):
            return True
        try:
            ipaddress.ip_address(host)
        except ValueError:
            return False
        return True

    def do_GET(self):
        if not self.allowed_host():
            self.send_error(403)
            return
        if self.path == "/":
            self.body("text/html; charset=utf-8", PAGE)
        elif self.path.split("?")[0] == "/shared.js":
            with open(os.path.join(SITE_DIR, "shared.js"), "rb") as f:
                self.body("text/javascript", f.read())
        elif self.path.split("?")[0] == "/stream":
            self.stream()
        else:
            self.send_error(404)

    def body(self, kind, data):
        self.send_response(200)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(data)
        except OSError:
            pass   # browser went away mid-load; a traceback would reach the console

    def stream(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True
        self.connection.settimeout(self.server.frame_timeout)
        seq = 0
        while True:
            frame, seq = self.server.feed.wait(seq)
            if frame is None:
                continue   # nothing from the cabinet yet
            try:
                self.wfile.write(frame)
            except OSError:
                return   # the tab was closed, the phone slept: let the thread go

    def version_string(self):
        return "Wonder Cabinet"   # not the Pi's exact CPython patch level

    def log_message(self, *args):
        pass   # the cabinet's console belongs to the game


def main(host, port, cabinet):
    if cabinet:
        os.nice(10)   # never compete with the game
        exit_with_parent()

    feed = Feed()
    threading.Thread(target=subscribe, args=(feed, host, port), daemon=True).start()

    server = Server(("", port), Handler)
    server.feed = feed
    if not cabinet:
        print(f"Watch the cabinet at http://localhost:{port}/")
    server.serve_forever()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Serve the cabinet's panel to browsers.")
    ap.add_argument("--host", default="127.0.0.1", help="the cabinet (default: this machine)")
    ap.add_argument("--port", type=int, default=MIRROR_PORT,
                    help="the cabinet's MIRROR port, which browsers open too")
    ap.add_argument("--cabinet", action="store_true",
                    help="started by the cabinet: low priority, and exit when it does")
    args = ap.parse_args()
    main(args.host, args.port, args.cabinet)
