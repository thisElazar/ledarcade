#!/usr/bin/env python3
"""
Render visuals to MP4 that looks like the real LED panel — for social posts.

    python tools/render_clip.py FIRE                          # 10 s square clip
    python tools/render_clip.py BOIDS --vertical              # 1080x1920 for Reels/TikTok
    python tools/render_clip.py FIRE --seconds 15 --skip 2 --out ../marketing/clips/fire.mp4
    python tools/render_clip.py --montage "FIRE,BOIDS,SLIME:8" --each 5   # idle reel; NAME:sec = warm-up
    python tools/render_clip.py BOIDS --vertical --title "flocking - 1986"   # text above panel
    python tools/render_clip.py CHLADNI --vertical --seconds 30 \
        --cards "0:CHLADNI FIGURES|3:CHLADNI FIGURES :: Ernst Chladni, 1787. Sand on a bowed plate gathers where it is still."
    python tools/render_clip.py --list                        # names you can pass

Vertical clips can carry a title above the panel and a brand line below, drawn
in the cabinet's own 3x5 pixel font through the same LED-dot look (wraps at 16
chars, max 2 lines). --cards replaces the title with timed placard cards:
"start:HEADING" or "start:HEADING :: body" separated by |, the heading in
panel-size LEDs and the body in half-size LEDs (32 chars, 3 lines). Montage
mode titles each slot with the visual's name unless --title is given. Square
clips never carry text.

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
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import numpy as np  # noqa: E402

CELL = 16          # output pixels per LED (64 * 16 = 1024)
DOT_RADIUS = 6.5   # LED dot radius in output pixels


def _dot_mask():
    yy, xx = np.mgrid[0:CELL, 0:CELL]
    d = np.hypot(xx + 0.5 - CELL / 2, yy + 0.5 - CELL / 2)
    m = np.clip(DOT_RADIUS + 0.5 - d, 0, 1)          # 1-px anti-aliased edge
    return np.tile(m, (64, 64))[..., None].astype(np.float32)


# Vertical layout (1080x1920): panel sits high so the brand line clears the
# Reels/TikTok UI at the bottom. Title above, brand below, both LED-styled.
V_W, V_H = 1080, 1920
PANEL_X, PANEL_Y = 28, 380
TITLE_GAP = 32
TITLE_COLOR = (200, 168, 110)
BRAND_COLOR = (110, 110, 110)
_FONT_MAP = str.maketrans({"·": "-", "×": "x", "—": "-", "–": "-", "’": "'"})


BODY_COLOR = (222, 214, 196)
BODY_CELL = 8      # placard body text: half-size LEDs, 32 chars per line
CARD_GAP = 24      # px between a card's heading and body


def _wrap(text, width, max_lines, what):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + (1 if cur else 0) <= width:
            cur = (cur + " " + w).strip()
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    if len(lines) > max_lines or any(len(l) > width for l in lines):
        sys.exit(f"{what} too long for the 3x5 font (max {max_lines} lines of {width}): {text!r}")
    return lines


def _text_strip(text, color, cell=CELL, width=16, max_lines=2, what="title"):
    """Render text in the cabinet's 3x5 font as LED dots. Returns (H, 1024, 3)
    uint8. cell = output px per LED: 16 matches the panel (16 chars/line),
    8 is the half-size placard body (32 chars/line)."""
    from arcade import _FONT_3X5
    lines = _wrap(text.translate(_FONT_MAP), width, max_lines, what)
    cols = 4 * width
    rows = 8 * len(lines) - 3
    grid = np.zeros((rows, cols), dtype=np.uint8)
    for i, line in enumerate(lines):
        x0 = (cols - (4 * len(line) - 1)) // 2
        for j, ch in enumerate(line):
            for r, row in enumerate(_FONT_3X5.get(ch, [])):
                for c, px in enumerate(row):
                    if px == "1":
                        grid[i * 8 + r, x0 + j * 4 + c] = 1
    yy, xx = np.mgrid[0:cell, 0:cell]
    d = np.hypot(xx + 0.5 - cell / 2, yy + 0.5 - cell / 2)
    dot = np.clip(DOT_RADIUS * cell / CELL + 0.5 - d, 0, 1)
    mask = np.tile(dot, (rows, cols))[..., None]
    big = np.repeat(np.repeat(grid, cell, 0), cell, 1)[..., None] * np.array(color, dtype=np.float32)
    return (big * mask).astype(np.uint8)


def _card_strip(card):
    """A card is 'HEADING' or 'HEADING :: body'. Heading in panel-size LEDs
    (2 lines of 16 alone, 1 line with a body); body half-size, 3 lines of 32."""
    head, _, body = card.partition("::")
    head, body = head.strip(), body.strip()
    if not body:
        return _text_strip(head, TITLE_COLOR)
    h = _text_strip(head, TITLE_COLOR, max_lines=1, what="card heading")
    b = _text_strip(body.upper(), BODY_COLOR, cell=BODY_CELL, width=32, max_lines=3, what="card body")
    strip = np.zeros((h.shape[0] + CARD_GAP + b.shape[0], 1024, 3), dtype=np.uint8)
    strip[:h.shape[0]] = h
    strip[h.shape[0] + CARD_GAP:] = b
    return strip


def catalog_label(cls):
    """'NAME :: CATEGORY - CREDIT' straight from site/guide.json, the cabinet's
    own catalog. Falls back to 'CATEGORY - YEAR' when the credit is too long
    for one line. Paintings resolve to 'TITLE :: ART - ARTIST, YEAR'."""
    import json
    import re
    g = json.load(open(os.path.join(os.path.dirname(HERE), "site", "guide.json")))
    name = getattr(cls, "name", cls.__name__)

    def label(title, cat, credit):
        sub = f"{cat} - {credit}" if credit else cat
        if len(sub) > 32:
            year = re.search(r"-?\d{3,4}$", credit)
            sub = f"{cat} - {year.group()}" if year else cat
        return f"{title.upper()} :: {sub.upper()}"

    for cat in g["categories"]:
        for it in cat.get("items", []):
            if it.get("cls") == cls.__name__ or it.get("name") == name:
                return label(it["name"], cat["name"], it.get("credit", ""))
        for p in cat.get("paintings", []):
            for w in p.get("works", []):
                if w["title"].upper() == name.upper():
                    return label(w["title"], cat["name"], f"{p['artist']}, {w['year']}")
    return name.upper()


def parse_cards(spec):
    """'0:FIRE|4:HEADING :: body|...' -> [(start_seconds, card), ...]"""
    cards = []
    for item in spec.split("|"):
        t, _, text = item.partition(":")
        cards.append((float(t), text.strip()))
    return sorted(cards)


class Composer:
    """Turns the 64x64 buffer into the full output frame (square or vertical)."""

    def __init__(self, vertical, title=None, brand="WONDER CABINET"):
        self.mask = _dot_mask()
        self.vertical = vertical
        self.w, self.h = (V_W, V_H) if vertical else (1080, 1080)
        self.canvas = np.zeros((self.h, self.w, 3), dtype=np.uint8)
        self.px = PANEL_X
        self.py = PANEL_Y if vertical else 28
        self.title = None
        if vertical and brand:
            strip = _text_strip(brand, BRAND_COLOR)
            y = self.py + 1024 + TITLE_GAP
            self.canvas[y:y + strip.shape[0], self.px:self.px + 1024] = strip
        if vertical and title:
            self.set_title(title)

    def set_title(self, title):
        if not self.vertical or title == self.title:
            return
        self.title = title
        self.canvas[:self.py, :] = 0
        strip = _card_strip(title)
        y = self.py - TITLE_GAP - strip.shape[0]
        if y < 0:
            sys.exit(f"card does not fit above the panel: {title!r}")
        self.canvas[y:y + strip.shape[0], self.px:self.px + 1024] = strip

    def set_time(self, cards, t):
        """Placard mode: show whichever card has started by time t."""
        for start, card in reversed(cards):
            if t >= start:
                self.set_title(card)
                return

    def frame(self, display):
        buf = np.asarray(display.buffer, dtype=np.uint8)
        big = np.repeat(np.repeat(buf, CELL, 0), CELL, 1)
        self.canvas[self.py:self.py + 1024, self.px:self.px + 1024] = (big * self.mask).astype(np.uint8)
        return self.canvas.tobytes()



# Paper layout (1080x1920), matching the site: white page, EB Garamond title,
# IBM Plex Mono category line, the panel black only inside a 1px ruled mount.
PAPER = (255, 255, 255)
INK, INK_3, RULE = (27, 26, 23), (124, 120, 110), (27, 26, 23)
P_PANEL_Y = 340
MOUNT_PAD = 14
FONTS = os.path.join(HERE, "fonts")


def _font(name, size):
    import pygame
    pygame.font.init()
    return pygame.font.Font(os.path.join(FONTS, name), size)


def _blit_text(canvas, font, text, y, color, spacing=0):
    """Draw one centred line of text onto a white numpy canvas."""
    import pygame
    chars = [font.render(c, True, color, PAPER) for c in text] if spacing else [font.render(text, True, color, PAPER)]
    w = sum(c.get_width() for c in chars) + spacing * (len(chars) - 1)
    x = (canvas.shape[1] - w) // 2
    for c in chars:
        arr = pygame.surfarray.array3d(c).transpose(1, 0, 2)
        h, cw = arr.shape[:2]
        canvas[y:y + h, x:x + cw] = arr
        x += cw + spacing


# 4:5 carousel slide: same page, shorter
S_H, S_PANEL_Y, S_BRAND_Y, S_BRAND_SIZE = 1350, 165, 30, 84


class PaperComposer(Composer):
    def __init__(self, title=None, brand="Wonder Cabinet", slide=False):
        self.mask = _dot_mask()
        self.vertical = True
        self.w, self.h = V_W, (S_H if slide else V_H)
        self.canvas = np.full((self.h, self.w, 3), 255, dtype=np.uint8)
        self.px, self.py = PANEL_X, (S_PANEL_Y if slide else P_PANEL_Y)
        self.slide = slide
        self.title = None
        self.serif = _font("EBGaramond.ttf", 60)
        self.mono = _font("IBMPlexMono-Regular.ttf", 24)
        if brand:
            _blit_text(self.canvas, _font("EBGaramond.ttf", S_BRAND_SIZE if slide else 104), brand,
                       S_BRAND_Y if slide else 118, INK)
        x0, y0 = self.px - MOUNT_PAD - 1, self.py - MOUNT_PAD - 1
        x1, y1 = self.px + 1024 + MOUNT_PAD, self.py + 1024 + MOUNT_PAD
        self.canvas[y0, x0:x1 + 1] = RULE
        self.canvas[y1, x0:x1 + 1] = RULE
        self.canvas[y0:y1 + 1, x0] = RULE
        self.canvas[y0:y1 + 1, x1] = RULE
        self.canvas[self.py:self.py + 1024, self.px:self.px + 1024] = 0
        if title:
            self.set_title(title)

    def set_title(self, title):
        """'NAME :: CATEGORY - CREDIT' -> serif title line, mono small-caps line."""
        if title == self.title:
            return
        self.title = title
        head, _, sub = title.partition("::")
        y = self.py + 1024 + MOUNT_PAD + 1
        self.canvas[y:, :] = 255
        dy_title, dy_sub = (26, 108) if self.slide else (34, 122)
        _blit_text(self.canvas, self.serif, head.strip().title() if head.isupper() else head.strip(), y + dy_title, INK)
        if sub.strip():
            _blit_text(self.canvas, self.mono, sub.strip().upper(), y + dy_sub, INK_3, spacing=3)


def _find(name):
    from visuals import ALL_VISUALS
    key = name.strip().upper()
    for v in ALL_VISUALS:
        if getattr(v, "name", "").upper() == key or v.__name__.upper() == key:
            return v
    sys.exit(f"no visual named {name!r} — try --list")


def _open_ffmpeg(out, fps, w, h, glow, box=None):
    # The blend must be followed by format=rgb24 or ffmpeg swaps G/B channels.
    if glow and box:   # glow only inside the panel so it never bleeds onto the paper
        x, y = box
        g = (f"split=3[a][b][c];[b]crop=1024:1024:{x}:{y}[pb];[c]crop=1024:1024:{x}:{y},gblur=sigma=10[pc];"
             f"[pb][pc]blend=all_mode=screen,format=rgb24[pg];[a][pg]overlay={x}:{y},")
    elif glow:
        g = "split[a][b];[b]gblur=sigma=10[b];[a][b]blend=all_mode=screen,format=rgb24,"
    else:
        g = ""
    if out.endswith(".png"):
        cmd = ["ffmpeg", "-y", "-loglevel", "error",
               "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(fps), "-i", "-",
               "-vf", f"{g}format=rgb24", "-frames:v", "1", out]
        return subprocess.Popen(cmd, stdin=subprocess.PIPE)
    vf = f"{g}format=yuv420p"
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(fps), "-i", "-",
           "-vf", vf, "-c:v", "libx264", "-crf", "18", "-movflags", "+faststart", out]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)


def _warm(vis, seconds, dt):
    """Run a visual silently so loading screens and slow starts are past."""
    for _ in range(int(seconds / dt)):
        vis.update(dt)
        vis.draw()


def _composer(a, title=None):
    title = title or a.title
    if a.paper:
        return PaperComposer(title, "Wonder Cabinet" if a.brand == "WONDER CABINET" else a.brand)
    return Composer(a.vertical, title, a.brand)


def render_single(cls, a, out):
    from arcade import Display
    display = Display()
    vis = cls(display)
    dt = 1.0 / a.fps
    if getattr(a, "set_state", None):
        _apply_state(vis, a.set_state)
    _warm(vis, a.skip, dt)
    cards = parse_cards(a.cards) if a.cards else None
    comp = _composer(a)
    ff = _open_ffmpeg(out, a.fps, comp.w, comp.h, not a.no_glow, (comp.px, comp.py) if a.paper else None)
    for i in range(int(a.seconds * a.fps)):
        if cards:
            comp.set_time(cards, i * dt)
        vis.update(dt)
        vis.draw()
        ff.stdin.write(comp.frame(display))
    ff.stdin.close()
    ff.wait()


def render_stills(cls, a, out):
    """Carousel slides: run the visual once and save a 4:5 PNG at each --stills time."""
    from arcade import Display
    display = Display()
    vis = cls(display)
    dt = 1.0 / a.fps
    if getattr(a, "set_state", None):
        _apply_state(vis, a.set_state)
    _warm(vis, a.skip, dt)
    comp = PaperComposer(a.title, "Wonder Cabinet" if a.brand == "WONDER CABINET" else a.brand, slide=True)
    times = sorted(float(t) for t in a.stills.split(","))
    base = out[:-4] if out.endswith(".png") else out
    t, k = 0.0, 0
    while k < len(times):
        vis.update(dt)
        vis.draw()
        t += dt
        if t >= times[k]:
            k += 1
            ff = _open_ffmpeg(f"{base}_{k}.png", a.fps, comp.w, comp.h, not a.no_glow, (comp.px, comp.py))
            ff.stdin.write(comp.frame(display))
            ff.stdin.close()
            ff.wait()
            print(f"{base}_{k}.png")


class _Press:
    """Fake input_state: one key reads as pressed, everything else False."""
    def __init__(self, key):
        self.key = key
    def __getattr__(self, name):
        return name == self.key or name == f"{self.key}_pressed"


def _apply_state(vis, spec):
    """'f=0.01,k=0.047'  set attributes
       'right*3'         press a key 3 times through handle_input (right/left/up/down/action_l/action_r)
       '_shuffle_and_start()'  call a method"""
    for tok in spec.split(","):
        tok = tok.strip()
        if not tok:
            continue
        if tok.endswith("()"):
            getattr(vis, tok[:-2])()
        elif "*" in tok and "=" not in tok:
            key, _, n = tok.partition("*")
            for _ in range(int(n or 1)):
                vis.handle_input(_Press(key.strip()))
        else:
            k, _, v = tok.partition("=")
            try:
                v = float(v) if "." in v else int(v)
            except ValueError:
                pass
            if not hasattr(vis, k.strip()):
                sys.exit(f"{type(vis).__name__} has no attribute {k.strip()!r}")
            setattr(vis, k.strip(), v)


def render_states(cls, a, out):
    """Carousel slides from one visual at several states: for each | group in
    --states, build a fresh instance, apply the group (see _apply_state), run
    --skip seconds, then save one 4:5 PNG — or, if --out ends in .mp4, record
    --seconds of 4:5 video. A param_overlay_timer, if present, is re-armed so
    the panel labels its own state."""
    from arcade import Display
    display = Display()
    dt = 1.0 / a.fps
    comp = PaperComposer(a.title, "Wonder Cabinet" if a.brand == "WONDER CABINET" else a.brand, slide=True)
    video = out.endswith(".mp4")
    base = out[:-4]
    for k, spec in enumerate(a.states.split("|"), 1):
        vis = cls(display)
        _apply_state(vis, spec)
        _warm(vis, a.skip, dt)
        if hasattr(vis, "param_overlay_timer"):
            vis.param_overlay_timer = 2.0
        fn = f"{base}_{k}.mp4" if video else f"{base}_{k}.png"
        ff = _open_ffmpeg(fn, a.fps, comp.w, comp.h, not a.no_glow, (comp.px, comp.py))
        for _ in range(int(a.seconds * a.fps) if video else 1):
            vis.update(dt)
            vis.draw()
            ff.stdin.write(comp.frame(display))
        ff.stdin.close()
        ff.wait()
        print(f"{fn}  {spec}")


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
    comp = _composer(a, a.title or visuals[0].name)
    ff = _open_ffmpeg(out, a.fps, comp.w, comp.h, not a.no_glow, (comp.px, comp.py) if a.paper else None)
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
            if not a.title:
                comp.set_title(cur.name)
        elif tm.transitioning:
            tm.update(dt)
            tm.draw(display)
            cur.update(dt)
        else:
            cur.update(dt)
            cur.draw()
        ff.stdin.write(comp.frame(display))
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
    ap.add_argument("--title", help="text above the panel (vertical only)")
    ap.add_argument("--states", help='carousel: "f=0.01,k=0.047|f=0.026,k=0.051" — one fresh run and one PNG per | group')
    ap.add_argument("--set", dest="set_state",
                    help='put the visual into a state before recording, same grammar as '
                         '--states: "attr=value", "method()", "right*3" (a key pressed n '
                         'times through handle_input). Several are comma-separated. '
                         'Replaces the one-off wrapper scripts in marketing/tools/.')
    ap.add_argument("--stills", help='carousel: comma-separated seconds, one 1080x1350 paper-style PNG each (e.g. "2,10,18")')
    ap.add_argument("--paper", action="store_true", help="site style: white page, serif title, ruled mount (implies --vertical)")
    ap.add_argument("--label", action="store_true", help="title from the catalog: NAME over CATEGORY - CREDIT (vertical only)")
    ap.add_argument("--cards", help='placard: "0:HEADING|4:HEADING :: body|..." timed cards above the panel (vertical only)')
    ap.add_argument("--brand", default="WONDER CABINET", help='text below the panel (vertical only; "" for none)')
    ap.add_argument("--out")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    if a.paper:
        a.vertical = True
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
        if a.label:
            a.title = catalog_label(cls)
        if a.stills or a.states:
            out = a.out or f"{cls.__name__.lower()}_slide.png"
            (render_states if a.states else render_stills)(cls, a, out)
            return
        out = a.out or f"{cls.__name__.lower()}{suffix}.mp4"
        render_single(cls, a, out)
    else:
        ap.error("give a visual name, --montage, or --list")
    print(out)


if __name__ == "__main__":
    main()
