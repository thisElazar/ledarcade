#!/usr/bin/env python3
"""
Render visuals to MP4 that looks like the real LED panel — for social posts.

    python tools/render_clip.py FIRE                          # 10 s square clip
    python tools/render_clip.py BOIDS --vertical              # 1080x1920 for Reels/TikTok
    python tools/render_clip.py FIRE --seconds 15 --skip 2 --out ../marketing/clips/fire.mp4
    python tools/render_clip.py --montage "FIRE,BOIDS,SLIME:8" --each 5   # idle reel; NAME:sec = warm-up
    python tools/render_clip.py --list                        # names you can pass

Montage mode mimics the cabinet's idle screen: each visual plays for --each
seconds (transition included), switched by the real TransitionManager (the same
random wipes and fades the cabinet uses).

Runs headless (SDL dummy driver). Needs ffmpeg on PATH and a Python with pygame
(3.11–3.13 — see README). Each LED becomes a round dot on black with a soft glow.
"""
import argparse
import os
import subprocess
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402

CELL = 16          # output pixels per LED (64 * 16 = 1024)
DOT_RADIUS = 6.5   # LED dot radius in output pixels


def _dot_mask():
    yy, xx = np.mgrid[0:CELL, 0:CELL]
    d = np.hypot(xx + 0.5 - CELL / 2, yy + 0.5 - CELL / 2)
    m = np.clip(DOT_RADIUS + 0.5 - d, 0, 1)          # 1-px anti-aliased edge
    return np.tile(m, (64, 64))[..., None].astype(np.float32)


def _find(name):
    from visuals import ALL_VISUALS
    key = name.strip().upper()
    for v in ALL_VISUALS:
        if getattr(v, "name", "").upper() == key or v.__name__.upper() == key:
            return v
    sys.exit(f"no visual named {name!r} — try --list")


def _open_ffmpeg(out, fps, vertical, glow):
    w, h = (1080, 1920) if vertical else (1080, 1080)
    # The blend must be followed by format=rgb24 or ffmpeg swaps G/B channels.
    g = ",split[a][b];[b]gblur=sigma=10[b];[a][b]blend=all_mode=screen,format=rgb24" if glow else ""
    vf = (f"scale=1024:1024:flags=neighbor{g},"
          f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,format=yuv420p")
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1024x1024", "-r", str(fps), "-i", "-",
           "-vf", vf, "-c:v", "libx264", "-crf", "18", "-movflags", "+faststart", out]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)


def _write_frame(ff, display, mask):
    buf = np.asarray(display.buffer, dtype=np.uint8)          # 64x64x3
    big = np.repeat(np.repeat(buf, CELL, 0), CELL, 1)          # 1024x1024x3
    ff.stdin.write((big * mask).astype(np.uint8).tobytes())


def _warm(vis, seconds, dt):
    """Run a visual silently so loading screens and slow starts are past."""
    for _ in range(int(seconds / dt)):
        vis.update(dt)
        vis.draw()


def render_single(cls, a, out):
    from arcade import Display
    display = Display()
    vis = cls(display)
    dt = 1.0 / a.fps
    _warm(vis, a.skip, dt)
    ff = _open_ffmpeg(out, a.fps, a.vertical, not a.no_glow)
    mask = _dot_mask()
    for _ in range(int(a.seconds * a.fps)):
        vis.update(dt)
        vis.draw()
        _write_frame(ff, display, mask)
    ff.stdin.close()
    ff.wait()


def render_montage(classes, a, out):
    from arcade import Display
    from transitions import TransitionManager
    display = Display()
    dt = 1.0 / a.fps
    visuals = []
    for cls, skip in classes:
        v = cls(display)
        _warm(v, skip, dt)
        visuals.append(v)

    tm = TransitionManager()
    ff = _open_ffmpeg(out, a.fps, a.vertical, not a.no_glow)
    mask = _dot_mask()
    idx, cycle = 0, 0.0
    cur = visuals[0]
    total = int(a.each * len(visuals) * a.fps)
    for _ in range(total):
        # Same loop shape as run_hardware.py's idle screen, except the slot
        # timer keeps running through the transition so every visual gets
        # exactly --each seconds and the total length is predictable.
        cycle += dt
        if cycle >= a.each and idx < len(visuals) - 1:
            old, idx = cur, idx + 1
            cur = visuals[idx]
            tm.start(old, cur)
            tm.draw(display)
            cycle = 0.0
        elif tm.transitioning:
            tm.update(dt)
            tm.draw(display)
            cur.update(dt)
        else:
            cur.update(dt)
            cur.draw()
        _write_frame(ff, display, mask)
    ff.stdin.close()
    ff.wait()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name", nargs="?", help="menu name or class name of a visual")
    ap.add_argument("--montage", help="comma-separated visual names, played in order with real transitions")
    ap.add_argument("--each", type=float, default=5, help="seconds per visual in montage mode")
    ap.add_argument("--seconds", type=float, default=10)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--skip", type=float, default=2, help="seconds to simulate before recording")
    ap.add_argument("--vertical", action="store_true", help="1080x1920 instead of 1080x1080")
    ap.add_argument("--no-glow", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    if a.list:
        from visuals import ALL_VISUALS
        for v in ALL_VISUALS:
            print(f"{getattr(v, 'name', '?'):24} {getattr(v, 'category', ''):12} {v.__name__}")
        return

    suffix = "_v" if a.vertical else ""
    if a.montage:
        classes = []
        for item in a.montage.split(","):
            if not item.strip():
                continue
            name, _, skip = item.rpartition(":")   # "GRAY-SCOTT:20" = warm 20 s
            if not name or not skip.replace(".", "").isdigit():
                name, skip = item, a.skip
            classes.append((_find(name), float(skip)))
        out = a.out or f"montage{suffix}.mp4"
        render_montage(classes, a, out)
    elif a.name:
        cls = _find(a.name)
        out = a.out or f"{cls.__name__.lower()}{suffix}.mp4"
        render_single(cls, a, out)
    else:
        ap.error("give a visual name, --montage, or --list")
    print(out)


if __name__ == "__main__":
    main()
