"""The web mirror serves browsers the newest frame, and only what it should."""
import re
import threading
import time

from run_web_mirror import FRAME_BYTES, PAGE, STILL_RESEND, Feed, Handler

FRAME_A = bytes(FRAME_BYTES)
FRAME_B = b"\xff" + bytes(FRAME_BYTES - 1)


def _host_allowed(value):
    handler = Handler.__new__(Handler)      # no socket needed for the Host check
    handler.headers = {"Host": value}
    return handler.allowed_host()


def test_identical_frames_are_not_resent():
    """A still screen should cost a watching phone nothing."""
    feed = Feed()
    feed.publish(FRAME_A)
    feed.publish(FRAME_A)
    feed.publish(FRAME_A)
    assert feed.seq == 1
    feed.publish(FRAME_B)
    assert feed.seq == 2


def test_a_new_browser_gets_the_current_frame_at_once():
    """First paint must not wait for the next frame the cabinet draws."""
    feed = Feed()
    feed.publish(FRAME_A)
    start = time.monotonic()
    frame, seq = feed.wait(0)              # a browser that has seen nothing yet
    assert frame == FRAME_A and seq == 1
    assert time.monotonic() - start < 0.5


def test_only_the_newest_frame_is_kept():
    """A slow screen skips frames rather than falling behind a queue."""
    feed = Feed()
    for _ in range(50):
        feed.publish(FRAME_A)
        feed.publish(FRAME_B)
    frame, _ = feed.wait(0)
    assert frame == FRAME_B


def test_a_waiting_browser_is_woken_by_a_new_frame():
    feed = Feed()
    feed.publish(FRAME_A)
    woke = []

    def watcher():
        woke.append(feed.wait(1))          # already seen seq 1, so this blocks

    t = threading.Thread(target=watcher)
    t.start()
    time.sleep(0.1)
    feed.publish(FRAME_B)
    t.join(timeout=2.0)
    assert woke == [(FRAME_B, 2)]


def test_still_screen_resends_sooner_than_the_page_gives_up():
    """The regression guard for a real bug: with STILL_RESEND at 10s and the
    page calling the cabinet gone after 4s, any screen that simply was not
    moving — the MIRROR settings screen included — flashed 'waiting for the
    cabinet' while it was perfectly live."""
    page_gives_up = int(re.search(r"waiting for the cabinet'\), (\d+)\)", PAGE.decode()).group(1))
    assert STILL_RESEND * 1000 < page_gives_up


def test_only_addresses_and_local_names_are_served():
    """A name someone else controls, re-resolved to the cabinet, would make
    their page same-origin with it — the one hole a browser can open in
    'same Wi-Fi only'."""
    for host in ("192.168.1.16:30203", "192.168.1.16", "localhost", "localhost:30203",
                 "arcade.local:30203", "[::1]:30203", ""):
        assert _host_allowed(host), host
    for host in ("evil.attacker.com", "evil.attacker.com:30203", "wondercabinet.example"):
        assert not _host_allowed(host), host


def test_the_settings_screen_says_when_the_port_is_taken():
    """MIRROR used to read ON after a failed bind, with nothing mirrored."""
    import settings as persistent
    from visuals.mirror import Mirror

    class Panel:
        def __init__(self, opened):
            self.opened, self.text = opened, []
        def clear(self, *a): self.text = []
        def draw_line(self, *a): pass
        def draw_text_small(self, x, y, s, c): self.text.append(s)
        def set_mirror(self, *a): return self.opened

    saved, persistent.set = persistent.set, lambda k, v: None
    try:
        for opened, expected in ((True, False), (False, True)):
            screen = Mirror(Panel(opened))
            screen.reset()
            screen.display = Panel(opened)
            screen._apply()
            screen.draw()
            assert ("PORT IN USE" in screen.display.text) is expected, opened
    finally:
        persistent.set = saved
