#!/usr/bin/env python3
"""
Build pipeline: download pottery images from the Metropolitan Museum of Art
Open Access API, resize to 64x64, color-correct for LED display.

All objects are CC0 (public domain).

Usage:
    python tools/build_pottery.py                # Build all
    python tools/build_pottery.py --list         # Show status
    python tools/build_pottery.py --preview      # Contact sheet
    python tools/build_pottery.py greek_amphora  # Build specific item
"""

import json, os, sys, functools
import urllib.request, urllib.error
from pathlib import Path

print = functools.partial(print, flush=True)

try:
    from PIL import Image, ImageOps, ImageEnhance
    import numpy as np
except ImportError:
    sys.exit("Pillow and numpy required: pip install Pillow numpy")

ROOT     = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "tools" / "pottery_manifest.json"
CACHE    = ROOT / "tools" / ".pottery_cache"
OUT_DIR  = ROOT / "assets" / "pottery"
SIZE     = 64
UA       = "LEDArcadePotteryPipeline/1.0"


# ── Met Museum API ────────────────────────────────────────────────

def met_image_url(met_id):
    """Fetch the primary image URL for a Met object."""
    url = f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{met_id}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read())
    if not data.get("isPublicDomain"):
        print(f"  WARNING: object {met_id} is not public domain")
    return data.get("primaryImageSmall") or data.get("primaryImage")


# ── Download ──────────────────────────────────────────────────────

def download(pid, entry):
    """Download source image, with caching."""
    CACHE.mkdir(parents=True, exist_ok=True)

    # Check cache
    for ext in (".jpg", ".png"):
        p = CACHE / f"{pid}{ext}"
        if p.exists():
            return p

    # Resolve URL from Met API
    met_id = entry["met_id"]
    print(f"  Fetching Met object {met_id}...")
    img_url = met_image_url(met_id)
    if not img_url:
        print(f"  FAIL: no image for object {met_id}")
        return None

    print(f"  GET {img_url[:90]}...")
    req = urllib.request.Request(img_url, headers={"User-Agent": UA})
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
    print(f"  Cached: {out.name} ({len(data) // 1024} KB)")
    return out


# ── Image processing ──────────────────────────────────────────────

def remove_background(img):
    """Darken museum-gray background to black for LED display.

    Uses gradient falloff: pixels near the border that match the border
    color are strongly darkened; pixels toward the center need to be a
    much closer match to be affected.  This preserves pot surfaces that
    happen to share hues with the studio backdrop.
    """
    arr = np.array(img, dtype=np.float32)
    h, w = arr.shape[:2]

    # Sample 2px-deep border to estimate background color
    border_pixels = []
    for y in range(h):
        for x in range(2):
            border_pixels.append(arr[y, x])
            border_pixels.append(arr[y, w - 1 - x])
    for x in range(w):
        for y in range(2):
            border_pixels.append(arr[y, x])
            border_pixels.append(arr[h - 1 - y, x])
    bg = np.median(border_pixels, axis=0)

    # Color distance from background
    dist = np.sqrt(np.sum((arr - bg) ** 2, axis=2))

    # Distance from nearest border edge (0 at border, large at center)
    yy, xx = np.mgrid[0:h, 0:w]
    edge_dist = np.minimum(np.minimum(xx, w - 1 - xx),
                           np.minimum(yy, h - 1 - yy))
    edge_factor = np.clip(edge_dist / 12.0, 0, 1)

    # Adaptive threshold: lenient at border (25), strict at center (60)
    threshold = 25 + edge_factor * 35
    bg_amount = np.clip(1.0 - dist / threshold, 0, 1) * 0.9

    for c in range(3):
        arr[:, :, c] *= (1.0 - bg_amount)

    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def color_correct(img):
    """Boost saturation and contrast for LED panel."""
    img = ImageEnhance.Color(img).enhance(1.4)
    img = ImageEnhance.Contrast(img).enhance(1.3)
    return img


def build_one(pid, entry):
    """Download, process, save one pottery image (64x64)."""
    title = entry.get("title", pid)
    out = OUT_DIR / f"{pid}.png"
    if out.exists():
        return True

    print(f"[{pid}] {title}")
    src = download(pid, entry)
    if not src:
        return False

    img = Image.open(src).convert("RGB")

    # Fit to 64x64 with black padding (preserves aspect ratio)
    img = ImageOps.pad(img, (SIZE, SIZE), color=(0, 0, 0), method=Image.LANCZOS)

    # Remove museum background, boost for LED
    img = remove_background(img)
    img = color_correct(img)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG")
    print(f"  OK -> {out.name} ({out.stat().st_size:,} bytes)")
    return True


# ── Commands ──────────────────────────────────────────────────────

def load_manifest():
    return json.loads(MANIFEST.read_text())


def cmd_build(ids=None):
    plates = load_manifest()
    if ids:
        plates = [p for p in plates if p["id"] in ids]

    ok = fail = 0
    for entry in plates:
        if build_one(entry["id"], entry):
            ok += 1
        else:
            fail += 1
    print(f"\nDone: {ok} built, {fail} failed")


def cmd_list():
    plates = load_manifest()
    for p in plates:
        out = OUT_DIR / f"{p['id']}.png"
        status = "BUILT" if out.exists() else "missing"
        print(f"  [{status:7s}] {p['id']:25s} {p['title']}")


def cmd_preview():
    plates = load_manifest()
    imgs = []
    for p in plates:
        out = OUT_DIR / f"{p['id']}.png"
        if out.exists():
            imgs.append((p, Image.open(out).convert("RGB")))

    if not imgs:
        print("No built images. Run build first.")
        return

    margin = 4
    cols = min(5, len(imgs))
    rows = (len(imgs) + cols - 1) // cols
    sheet_w = (SIZE + margin) * cols + margin
    sheet_h = (SIZE + margin) * rows + margin
    sheet = Image.new("RGB", (sheet_w, sheet_h), (30, 30, 30))

    for i, (p, img) in enumerate(imgs):
        r, c = divmod(i, cols)
        x = margin + c * (SIZE + margin)
        y = margin + r * (SIZE + margin)
        sheet.paste(img, (x, y))

    out = ROOT / "tools" / "pottery_preview.png"
    sheet.save(out)
    print(f"Saved {out} ({len(imgs)} items)")


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--list" in args:
        cmd_list()
    elif "--preview" in args:
        cmd_preview()
    elif "--clean" in args:
        import shutil
        if CACHE.exists():
            shutil.rmtree(CACHE)
            print("Cache cleared")
    else:
        ids = {a for a in args if not a.startswith("-")} or None
        cmd_build(ids)
