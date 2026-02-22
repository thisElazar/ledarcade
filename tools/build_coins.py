#!/usr/bin/env python3
"""
Build pipeline: download coin images from Wikimedia Commons and the
Metropolitan Museum of Art Open Access API, process for 64x64 LED display.

All images are CC0, CC BY, or CC BY-SA (attribution preserved in manifest).

Usage:
    python tools/build_coins.py                # Build all
    python tools/build_coins.py --list         # Show status
    python tools/build_coins.py --preview      # Contact sheet
    python tools/build_coins.py --rebuild      # Force rebuild all
    python tools/build_coins.py lydian_stater  # Build specific item
"""

import json, os, sys, functools, time, math
import urllib.request, urllib.error, urllib.parse
from pathlib import Path

print = functools.partial(print, flush=True)

try:
    from PIL import Image, ImageOps, ImageEnhance, ImageDraw, ImageFilter
    import numpy as np
except ImportError:
    sys.exit("Pillow and numpy required: pip install Pillow numpy")

ROOT     = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "tools" / "coins_manifest.json"
CACHE    = ROOT / "tools" / ".coins_cache"
OUT_DIR  = ROOT / "assets" / "coins"
SIZE     = 64
UA       = "LEDArcadeCoinPipeline/1.0 (educational LED art project)"

# Polite delay between network requests (seconds)
REQUEST_DELAY = 2.0
RETRY_DELAY = 30       # seconds to wait after a 429
MAX_RETRIES = 3


# ── Source resolvers ─────────────────────────────────────────────

def _wikimedia_url(filename):
    """Resolve a Wikimedia Commons filename to a direct image URL."""
    params = urllib.parse.urlencode({
        "action": "query",
        "titles": f"File:{filename}",
        "prop": "imageinfo",
        "iiprop": "url",
        "format": "json",
    })
    url = f"https://commons.wikimedia.org/w/api.php?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read())
    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        info = page.get("imageinfo", [{}])[0]
        return info.get("url")
    return None


def _met_image_url(met_id):
    """Fetch the primary image URL for a Met Museum object."""
    url = f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{met_id}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read())
    if not data.get("isPublicDomain"):
        print(f"  WARNING: Met object {met_id} is not public domain")
    return data.get("primaryImageSmall") or data.get("primaryImage")


# ── Download ──────────────────────────────────────────────────────

def download(pid, entry):
    """Download source image, with caching and polite delays."""
    CACHE.mkdir(parents=True, exist_ok=True)

    # Check cache
    for ext in (".jpg", ".png", ".JPG", ".PNG", ".tif"):
        p = CACHE / f"{pid}{ext}"
        if p.exists():
            return p

    # Resolve image URL based on source
    source = entry.get("source", "wikimedia")
    if source == "met":
        met_id = entry["met_id"]
        print(f"  Fetching Met object {met_id}...")
        img_url = _met_image_url(met_id)
    else:
        filename = entry["file"]
        print(f"  Resolving Wikimedia: {filename[:60]}...")
        img_url = _wikimedia_url(filename)

    if not img_url:
        print(f"  FAIL: no image URL resolved")
        return None

    print(f"  GET {img_url[:90]}...")
    for attempt in range(MAX_RETRIES):
        req = urllib.request.Request(img_url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
                ct = r.headers.get("Content-Type", "")
            break
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < MAX_RETRIES - 1:
                wait = RETRY_DELAY * (attempt + 1)
                print(f"  Rate limited, waiting {wait}s (attempt {attempt + 1}/{MAX_RETRIES})...")
                time.sleep(wait)
                continue
            print(f"  FAIL: {e}")
            return None
        except Exception as e:
            print(f"  FAIL: {e}")
            return None

    ext = ".png" if "png" in ct.lower() else ".jpg"
    out = CACHE / f"{pid}{ext}"
    out.write_bytes(data)
    print(f"  Cached: {out.name} ({len(data) // 1024} KB)")

    # Be polite to servers
    time.sleep(REQUEST_DELAY)
    return out


# ── Image processing ──────────────────────────────────────────────

def remove_background(img):
    """Darken background to black for LED display.

    Samples border pixels to estimate background, then fades pixels
    that are close to that color — more aggressively near the edges,
    more conservatively toward the center.
    """
    arr = np.array(img, dtype=np.float32)
    h, w = arr.shape[:2]

    # Sample 3px-deep border to estimate background color
    border_pixels = []
    for y in range(h):
        for x in range(3):
            border_pixels.append(arr[y, x])
            border_pixels.append(arr[y, w - 1 - x])
    for x in range(w):
        for y in range(3):
            border_pixels.append(arr[y, x])
            border_pixels.append(arr[h - 1 - y, x])
    bg = np.median(border_pixels, axis=0)

    # Color distance from background
    dist = np.sqrt(np.sum((arr - bg) ** 2, axis=2))

    # Distance from nearest border edge
    yy, xx = np.mgrid[0:h, 0:w]
    edge_dist = np.minimum(np.minimum(xx, w - 1 - xx),
                           np.minimum(yy, h - 1 - yy))
    edge_factor = np.clip(edge_dist / 15.0, 0, 1)

    # Adaptive threshold: lenient at border, strict at center
    threshold = 20 + edge_factor * 40
    bg_amount = np.clip(1.0 - dist / threshold, 0, 1) * 0.95

    for c in range(3):
        arr[:, :, c] *= (1.0 - bg_amount)

    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def center_crop_square(img):
    """Crop to the largest centered square."""
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    return img.crop((left, top, left + side, top + side))


def apply_circular_vignette(img, coin_radius=28):
    """Darken pixels outside a circular region centered on the coin area.

    The coin sits at center (32, 32) of the 64x64 image with radius
    coin_radius.  Pixels beyond the radius are faded to black.
    """
    arr = np.array(img, dtype=np.float32)
    h, w = arr.shape[:2]
    cx, cy = w / 2.0, h / 2.0

    yy, xx = np.mgrid[0:h, 0:w]
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)

    # Smooth falloff from coin_radius-2 to coin_radius+2
    fade = np.clip((coin_radius + 2 - dist) / 4.0, 0, 1)

    for c in range(3):
        arr[:, :, c] *= fade

    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def color_correct(img, boost=1.4):
    """Boost saturation and contrast for LED panel."""
    img = ImageEnhance.Color(img).enhance(boost)
    img = ImageEnhance.Contrast(img).enhance(1.3)
    img = ImageEnhance.Brightness(img).enhance(1.1)
    return img


def crop_obverse(img):
    """If image shows both obverse and reverse side-by-side, crop to obverse.

    Detects this by aspect ratio: photos showing both sides are typically
    ~2:1 wide.  We take the left half (obverse by numismatic convention).
    """
    w, h = img.size
    ratio = w / h if h > 0 else 1.0
    if ratio > 1.4:
        # Take the left half (obverse), with a small margin trim
        half_w = w // 2
        margin = int(half_w * 0.03)  # trim 3% to avoid gap/border
        img = img.crop((margin, 0, half_w - margin, h))
        print(f"  Cropped to obverse: {img.size[0]}x{img.size[1]}")
    return img


def process_coin(img, entry):
    """Full processing pipeline for a coin image."""
    shape = entry.get("shape", "round")

    # Step 0: Crop to obverse if two-sided photo
    if shape != "knife":
        img = crop_obverse(img)

    # Step 1: Remove background
    img = remove_background(img)

    # Step 2: Crop to square, resize to 64x64
    if shape in ("knife",):
        # Non-square coins: pad to fit, preserving aspect ratio
        img = ImageOps.pad(img, (SIZE, SIZE), color=(0, 0, 0),
                           method=Image.LANCZOS)
    elif shape == "oval":
        # Oval coins: pad preserving shape
        img = ImageOps.pad(img, (SIZE, SIZE), color=(0, 0, 0),
                           method=Image.LANCZOS)
    else:
        # Round coins: pad to square (preserves full coin), then resize
        img = ImageOps.pad(img, (SIZE, SIZE), color=(0, 0, 0),
                           method=Image.LANCZOS)

    # Step 3: Circular vignette for round coins (fade edges)
    if shape in ("round", "round_square_hole", "round_with_hole"):
        img = apply_circular_vignette(img, coin_radius=30)

    # Step 4: Color boost for LED display
    img = color_correct(img)

    return img


# ── Build ─────────────────────────────────────────────────────────

def build_one(pid, entry, force=False):
    """Download, process, save one coin image."""
    title = entry.get("title", pid)
    out = OUT_DIR / f"{pid}.png"
    if out.exists() and not force:
        return True

    print(f"[{pid}] {title}")
    src = download(pid, entry)
    if not src:
        return False

    try:
        img = Image.open(src).convert("RGB")
    except Exception as e:
        print(f"  FAIL opening image: {e}")
        return False

    img = process_coin(img, entry)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG")
    print(f"  OK -> {out.name} ({out.stat().st_size:,} bytes)")
    return True


# ── Commands ──────────────────────────────────────────────────────

def load_manifest():
    return json.loads(MANIFEST.read_text())


def cmd_build(ids=None, force=False):
    coins = load_manifest()
    if ids:
        coins = [c for c in coins if c["id"] in ids]

    ok = fail = 0
    for entry in coins:
        if build_one(entry["id"], entry, force=force):
            ok += 1
        else:
            fail += 1
    print(f"\nDone: {ok} built, {fail} failed")


def cmd_list():
    coins = load_manifest()
    for era in ("ANCIENT", "MEDIEVAL", "MODERN"):
        group = [c for c in coins if c["era"] == era]
        if not group:
            continue
        print(f"\n  === {era} ===")
        for c in group:
            out = OUT_DIR / f"{c['id']}.png"
            status = "BUILT" if out.exists() else "missing"
            print(f"  [{status:7s}] {c['id']:25s} {c['title']}")


def cmd_preview():
    coins = load_manifest()
    imgs = []
    for c in coins:
        out = OUT_DIR / f"{c['id']}.png"
        if out.exists():
            imgs.append((c, Image.open(out).convert("RGB")))

    if not imgs:
        print("No built images. Run build first.")
        return

    margin = 4
    cols = min(6, len(imgs))
    rows = (len(imgs) + cols - 1) // cols
    sheet_w = (SIZE + margin) * cols + margin
    sheet_h = (SIZE + margin) * rows + margin
    sheet = Image.new("RGB", (sheet_w, sheet_h), (30, 30, 30))

    from PIL import ImageFont
    for i, (c, img) in enumerate(imgs):
        r, col = divmod(i, cols)
        x = margin + col * (SIZE + margin)
        y = margin + r * (SIZE + margin)
        sheet.paste(img, (x, y))

    out = ROOT / "tools" / "coins_preview.png"
    sheet.save(out)
    print(f"Saved {out} ({len(imgs)} items, {cols}x{rows} grid)")


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
    elif "--rebuild" in args:
        cmd_build(force=True)
    else:
        ids = {a for a in args if not a.startswith("-")} or None
        cmd_build(ids)
