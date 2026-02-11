#!/usr/bin/env python3
"""
Build pipeline: download paintings from Wikimedia Commons,
crop to square, resize to 64x64, color-correct for LED display.

Usage:
    python tools/build_paintings.py                # Build all
    python tools/build_paintings.py starry_night   # Build specific
    python tools/build_paintings.py --list         # Show status
    python tools/build_paintings.py --meta         # Print Python dict
    python tools/build_paintings.py --preview      # Contact sheet
    python tools/build_paintings.py --search "van gogh starry"
    python tools/build_paintings.py --atlas         # Build web emulator atlas
    python tools/build_paintings.py --clean         # Clear download cache
"""

import json, os, sys, time
import urllib.request, urllib.parse
from pathlib import Path

try:
    from PIL import Image, ImageEnhance
except ImportError:
    sys.exit("Pillow required: pip install Pillow")

ROOT     = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "tools" / "paintings.json"
OUT_DIR  = ROOT / "assets" / "paintings"
CACHE    = ROOT / "tools" / ".painting_cache"
SIZE     = 64
UA       = "LEDArcadePaintingPipeline/1.0"


# ── Wikimedia Commons API ──────────────────────────────────────────

def wikimedia_thumb_url(filename, width=800):
    """Resolve a Commons filename to a thumbnail URL."""
    params = urllib.parse.urlencode({
        "action": "query",
        "titles": f"File:{filename}",
        "prop": "imageinfo",
        "iiprop": "url",
        "iiurlwidth": width,
        "format": "json",
    })
    url = f"https://commons.wikimedia.org/w/api.php?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        for page in data["query"]["pages"].values():
            if "imageinfo" in page:
                info = page["imageinfo"][0]
                return info.get("thumburl") or info["url"]
    except Exception as e:
        print(f"  API error: {e}")
    return None


def wikimedia_search(query, limit=8):
    """Search Commons for files matching a query."""
    params = urllib.parse.urlencode({
        "action": "query",
        "list": "search",
        "srsearch": f"{query} filetype:bitmap",
        "srnamespace": "6",
        "srlimit": limit,
        "format": "json",
    })
    url = f"https://commons.wikimedia.org/w/api.php?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read())
    results = data.get("query", {}).get("search", [])
    return [r["title"].replace("File:", "") for r in results]


# ── Download ───────────────────────────────────────────────────────

def download(pid, entry):
    """Download source image, with caching."""
    CACHE.mkdir(parents=True, exist_ok=True)

    # Check cache (any extension)
    for ext in (".jpg", ".png", ".gif", ".jpeg"):
        p = CACHE / f"{pid}{ext}"
        if p.exists():
            return p

    # Resolve URL
    if "url" in entry:
        url = entry["url"]
    elif "file" in entry:
        url = wikimedia_thumb_url(entry["file"])
        if not url:
            print(f"  FAIL: cannot resolve '{entry['file']}'")
            return None
    else:
        print(f"  FAIL: no 'file' or 'url' for {pid}")
        return None

    print(f"  GET {url[:90]}...")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read()
            ct = r.headers.get("Content-Type", "")
    except Exception as e:
        print(f"  FAIL: {e}")
        return None

    ext = ".png" if "png" in ct else ".jpg"
    out = CACHE / f"{pid}{ext}"
    out.write_bytes(data)
    return out


# ── Image processing ──────────────────────────────────────────────

def crop_square(img, mode="center"):
    """Crop to square using specified anchor point."""
    w, h = img.size
    if w == h:
        return img

    if mode == "fill":
        side = max(w, h)
        bg = Image.new("RGB", (side, side), (0, 0, 0))
        bg.paste(img, ((side - w) // 2, (side - h) // 2))
        return bg

    s = min(w, h)
    anchors = {
        "center": ((w - s) // 2, (h - s) // 2),
        "top":    ((w - s) // 2, 0),
        "bottom": ((w - s) // 2, h - s),
        "left":   (0, (h - s) // 2),
        "right":  (w - s, (h - s) // 2),
    }
    x, y = anchors.get(mode, anchors["center"])
    return img.crop((x, y, x + s, y + s))


def color_correct(img, entry):
    """LED panel color correction — boost sat/contrast for small bright display."""
    sat = entry.get("saturation", 1.2)
    con = entry.get("contrast", 1.15)
    bri = entry.get("brightness", 1.0)

    if sat != 1.0:
        img = ImageEnhance.Color(img).enhance(sat)
    if con != 1.0:
        img = ImageEnhance.Contrast(img).enhance(con)
    if bri != 1.0:
        img = ImageEnhance.Brightness(img).enhance(bri)
    return img


# ── Build ─────────────────────────────────────────────────────────

def build_one(pid, entry):
    """Download, process, save one painting."""
    title = entry.get("title", pid)
    artist = entry.get("artist", "?")
    year = entry.get("year", "?")
    print(f"[{pid}] {title} — {artist}, {year}")

    src = download(pid, entry)
    if not src:
        return False

    img = Image.open(src).convert("RGB")
    img = crop_square(img, entry.get("crop", "center"))
    img = color_correct(img, entry)
    img = img.resize((SIZE, SIZE), Image.LANCZOS)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{pid}.png"
    img.save(out, "PNG")
    print(f"  OK → {out.name} ({out.stat().st_size:,} bytes)")
    return True


# ── Commands ──────────────────────────────────────────────────────

def cmd_build(ids=None):
    manifest = json.loads(MANIFEST.read_text())
    targets = {k: v for k, v in manifest.items() if not ids or k in ids}
    if ids:
        missing = ids - set(manifest.keys())
        for m in missing:
            print(f"Unknown painting: {m}")

    ok = fail = 0
    for pid, entry in targets.items():
        if build_one(pid, entry):
            ok += 1
        else:
            fail += 1
        time.sleep(0.3)  # polite to Wikimedia

    print(f"\nDone: {ok} built, {fail} failed out of {ok + fail}")
    if ok:
        print(f"Output: {OUT_DIR}/")


def cmd_list():
    manifest = json.loads(MANIFEST.read_text())
    built = 0
    for pid, e in manifest.items():
        exists = (OUT_DIR / f"{pid}.png").exists()
        mark = "✓" if exists else " "
        built += exists
        print(f"  [{mark}] {pid}: {e['title']} — {e['artist']}, {e['year']}")
    print(f"\n  {built}/{len(manifest)} built")


def cmd_meta():
    """Print Python metadata dict for use in salon visual."""
    manifest = json.loads(MANIFEST.read_text())
    print("PAINTING_META = {")
    for pid, e in manifest.items():
        if (OUT_DIR / f"{pid}.png").exists():
            print(f'    "{pid}": ("{e["title"]}", "{e["artist"]}", {e["year"]}),')
    print("}")


def cmd_preview():
    """Generate a contact sheet of all built paintings."""
    manifest = json.loads(MANIFEST.read_text())
    built = [(pid, e) for pid, e in manifest.items()
             if (OUT_DIR / f"{pid}.png").exists()]
    if not built:
        print("No paintings built yet.")
        return

    cols = 8
    rows = (len(built) + cols - 1) // cols
    cell = SIZE + 2
    sheet = Image.new("RGB", (cols * cell, rows * cell), (32, 32, 32))

    for i, (pid, _) in enumerate(built):
        img = Image.open(OUT_DIR / f"{pid}.png")
        x = (i % cols) * cell + 1
        y = (i // cols) * cell + 1
        sheet.paste(img, (x, y))

    out = ROOT / "tools" / "painting_preview.png"
    sheet.save(out)
    print(f"Contact sheet: {out} ({len(built)} paintings, {cols}x{rows} grid)")


def cmd_search(query):
    """Search Wikimedia Commons for painting files."""
    print(f"Searching Commons for: {query}")
    results = wikimedia_search(query)
    if not results:
        print("  No results.")
        return
    for r in results:
        print(f"  {r}")
    print(f"\nCopy the filename into paintings.json as the \"file\" value.")


def cmd_atlas():
    """Generate paintings atlas JSON for the web emulator.

    Packs all built 64x64 painting PNGs into a single JSON file
    with base64-encoded raw RGB data per painting.
    """
    import base64
    manifest = json.loads(MANIFEST.read_text())
    atlas = {}
    for pid in manifest:
        png_path = OUT_DIR / f"{pid}.png"
        if not png_path.exists():
            continue
        img = Image.open(png_path).convert("RGB")
        if img.size != (SIZE, SIZE):
            img = img.resize((SIZE, SIZE), Image.NEAREST)
        raw = bytearray()
        for y in range(SIZE):
            for x in range(SIZE):
                r, g, b = img.getpixel((x, y))
                raw.extend([r, g, b])
        atlas[pid] = base64.b64encode(bytes(raw)).decode('ascii')

    out_path = ROOT / "site" / "paintings_atlas.json"
    with open(out_path, 'w') as f:
        json.dump(atlas, f)
    print(f"Atlas: {out_path} ({len(atlas)} paintings, {out_path.stat().st_size:,} bytes)")


def cmd_clean():
    import shutil
    if CACHE.exists():
        shutil.rmtree(CACHE)
        print("Cache cleared.")
    else:
        print("No cache to clear.")


def main():
    args = sys.argv[1:]
    if not args:
        cmd_build()
    elif args[0] == "--list":
        cmd_list()
    elif args[0] == "--meta":
        cmd_meta()
    elif args[0] == "--preview":
        cmd_preview()
    elif args[0] == "--search" and len(args) > 1:
        cmd_search(" ".join(args[1:]))
    elif args[0] == "--atlas":
        cmd_atlas()
    elif args[0] == "--clean":
        cmd_clean()
    else:
        cmd_build(set(args))


if __name__ == "__main__":
    main()
