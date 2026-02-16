#!/usr/bin/env python3
"""
Build pipeline: download naturalist plates from Wikimedia Commons,
resize to 64px wide (maintaining aspect ratio), color-correct for LED display.

Usage:
    python tools/build_plates.py haeckel              # Build all Haeckel plates
    python tools/build_plates.py audubon              # Build all Audubon plates
    python tools/build_plates.py merian               # Build all Merian plates
    python tools/build_plates.py haeckel --list        # Show status
    python tools/build_plates.py haeckel --preview     # Contact sheet
    python tools/build_plates.py haeckel --atlas       # Build web emulator atlas
    python tools/build_plates.py haeckel --search "jellyfish"
    python tools/build_plates.py haeckel discomedusae  # Build specific plate
    python tools/build_plates.py --clean               # Clear download cache
"""

import json, os, sys, time, base64, functools
import urllib.request, urllib.parse, urllib.error

# Unbuffered print so background builds show progress
print = functools.partial(print, flush=True)
from pathlib import Path

try:
    from PIL import Image, ImageEnhance
except ImportError:
    sys.exit("Pillow required: pip install Pillow")

ROOT     = Path(__file__).resolve().parent.parent
CACHE    = ROOT / "tools" / ".plates_cache"
WIDTH    = 64
UA       = "LEDArcadePlatePipeline/1.0"

COLLECTIONS = {
    "haeckel": {
        "manifest": ROOT / "tools" / "haeckel_plates.json",
        "out_dir":  ROOT / "assets" / "haeckel",
        "atlas":    ROOT / "site" / "haeckel_atlas.json",
    },
    "audubon": {
        "manifest": ROOT / "tools" / "audubon_plates.json",
        "out_dir":  ROOT / "assets" / "audubon",
        "atlas":    ROOT / "site" / "audubon_atlas.json",
    },
    "merian": {
        "manifest": ROOT / "tools" / "merian_plates.json",
        "out_dir":  ROOT / "assets" / "merian",
        "atlas":    ROOT / "site" / "merian_atlas.json",
    },
}


# ── Wikimedia Commons API ──────────────────────────────────────────

def wikimedia_thumb_url(filename, width=800):
    """Resolve a Commons filename to a thumbnail URL.

    Tries common cached thumbnail widths first (1024, 640) to avoid
    triggering server-side renders, then falls back to the requested width.
    """
    widths_to_try = []
    for common in (1024, 640):
        if common >= width and common not in widths_to_try:
            widths_to_try.append(common)
    if width not in widths_to_try:
        widths_to_try.append(width)

    for w in widths_to_try:
        params = urllib.parse.urlencode({
            "action": "query",
            "titles": f"File:{filename}",
            "prop": "imageinfo",
            "iiprop": "url",
            "iiurlwidth": w,
            "format": "json",
        })
        url = f"https://commons.wikimedia.org/w/api.php?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        for attempt in range(5):
            try:
                with urllib.request.urlopen(req, timeout=15) as r:
                    data = json.loads(r.read())
                for page in data["query"]["pages"].values():
                    if "imageinfo" in page:
                        info = page["imageinfo"][0]
                        thumb = info.get("thumburl") or info["url"]
                        if thumb:
                            return thumb
                break
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt < 4:
                    wait = (attempt + 1) * 15
                    print(f"  API rate limited, waiting {wait}s...")
                    time.sleep(wait)
                    continue
                print(f"  API error: {e}")
                if w != widths_to_try[-1]:
                    break  # try next width
                return None
            except Exception as e:
                print(f"  API error: {e}")
                if w != widths_to_try[-1]:
                    break
                return None
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
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
                ct = r.headers.get("Content-Type", "")
            break
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 4:
                wait = (attempt + 1) * 15
                print(f"  Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            print(f"  FAIL: {e}")
            return None
        except Exception as e:
            print(f"  FAIL: {e}")
            return None

    ext = ".png" if "png" in ct else ".jpg"
    out = CACHE / f"{pid}{ext}"
    out.write_bytes(data)
    return out


# ── Image processing ──────────────────────────────────────────────

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

def build_one(pid, entry, out_dir):
    """Download, process, save one plate (64px wide, variable height)."""
    title = entry.get("title", pid)

    # Skip if already built
    out = out_dir / f"{pid}.png"
    if out.exists():
        return True

    print(f"[{pid}] {title}")
    src = download(pid, entry)
    if not src:
        return False

    img = Image.open(src).convert("RGB")
    # Resize to 64px wide, maintaining aspect ratio
    w, h = img.size
    new_h = int(h * WIDTH / w)
    img = img.resize((WIDTH, new_h), Image.LANCZOS)
    img = color_correct(img, entry)

    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{pid}.png"
    img.save(out, "PNG")
    print(f"  OK → {out.name} ({WIDTH}x{new_h}, {out.stat().st_size:,} bytes)")
    return True


# ── Commands ──────────────────────────────────────────────────────

def load_manifest(collection):
    cfg = COLLECTIONS[collection]
    return json.loads(cfg["manifest"].read_text())


def cmd_build(collection, ids=None):
    cfg = COLLECTIONS[collection]
    plates = load_manifest(collection)
    if ids:
        plates = [p for p in plates if p["id"] in ids]
        found = {p["id"] for p in plates}
        for m in ids - found:
            print(f"Unknown plate: {m}")

    ok = fail = skip = 0
    for entry in plates:
        already = (cfg["out_dir"] / f"{entry['id']}.png").exists()
        if build_one(entry["id"], entry, cfg["out_dir"]):
            ok += 1
        else:
            fail += 1
        if not already:
            time.sleep(5.0)  # Wikimedia robot policy: be polite

    print(f"\nDone: {ok} built, {fail} failed out of {ok + fail}")
    if ok:
        print(f"Output: {cfg['out_dir']}/")


def cmd_list(collection):
    cfg = COLLECTIONS[collection]
    plates = load_manifest(collection)
    built = 0
    for p in plates:
        exists = (cfg["out_dir"] / f"{p['id']}.png").exists()
        mark = "✓" if exists else " "
        built += exists
        print(f"  [{mark}] {p['id']}: {p['title']}")
    print(f"\n  {built}/{len(plates)} built")


def cmd_preview(collection):
    """Generate a contact sheet of all built plates."""
    cfg = COLLECTIONS[collection]
    plates = load_manifest(collection)
    built = [p for p in plates if (cfg["out_dir"] / f"{p['id']}.png").exists()]
    if not built:
        print("No plates built yet.")
        return

    cols = 8
    rows = (len(built) + cols - 1) // cols
    cell_w = WIDTH + 2
    # Find max height among built plates
    max_h = 0
    for p in built:
        img = Image.open(cfg["out_dir"] / f"{p['id']}.png")
        max_h = max(max_h, img.size[1])
    cell_h = max_h + 2
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), (32, 32, 32))

    for i, p in enumerate(built):
        img = Image.open(cfg["out_dir"] / f"{p['id']}.png")
        x = (i % cols) * cell_w + 1
        y = (i // cols) * cell_h + 1
        sheet.paste(img, (x, y))

    out = ROOT / "tools" / f"{collection}_preview.png"
    sheet.save(out)
    print(f"Contact sheet: {out} ({len(built)} plates, {cols}x{rows} grid)")


def cmd_search(query):
    """Search Wikimedia Commons for plate files."""
    print(f"Searching Commons for: {query}")
    results = wikimedia_search(query)
    if not results:
        print("  No results.")
        return
    for r in results:
        print(f"  {r}")
    print(f"\nCopy the filename into the plates manifest as the \"file\" value.")


def cmd_atlas(collection):
    """Generate plates atlas JSON for the web emulator.

    Packs all built plate PNGs into a single JSON file
    with base64-encoded raw RGB data per plate, plus height info.
    """
    cfg = COLLECTIONS[collection]
    plates = load_manifest(collection)
    atlas = {}
    for p in plates:
        png_path = cfg["out_dir"] / f"{p['id']}.png"
        if not png_path.exists():
            continue
        img = Image.open(png_path).convert("RGB")
        w, h = img.size
        if w != WIDTH:
            h = int(h * WIDTH / w)
            img = img.resize((WIDTH, h), Image.NEAREST)
        raw = bytearray()
        for y in range(h):
            for x in range(WIDTH):
                r, g, b = img.getpixel((x, y))
                raw.extend([r, g, b])
        atlas[p["id"]] = {
            "h": h,
            "data": base64.b64encode(bytes(raw)).decode('ascii'),
        }

    out_path = cfg["atlas"]
    with open(out_path, 'w') as f:
        json.dump(atlas, f)
    print(f"Atlas: {out_path} ({len(atlas)} plates, {out_path.stat().st_size:,} bytes)")


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
        print("Usage: python tools/build_plates.py <collection> [options]")
        print("Collections: haeckel, audubon, merian")
        print("Options: --list, --preview, --atlas, --search <query>, --clean")
        return

    if args[0] == "--clean":
        cmd_clean()
        return

    if args[0] == "--search" and len(args) > 1:
        cmd_search(" ".join(args[1:]))
        return

    collection = args[0]
    if collection not in COLLECTIONS:
        print(f"Unknown collection: {collection}")
        print(f"Available: {', '.join(COLLECTIONS.keys())}")
        return

    rest = args[1:]
    if not rest:
        cmd_build(collection)
    elif rest[0] == "--list":
        cmd_list(collection)
    elif rest[0] == "--preview":
        cmd_preview(collection)
    elif rest[0] == "--atlas":
        cmd_atlas(collection)
    elif rest[0] == "--search" and len(rest) > 1:
        cmd_search(" ".join(rest[1:]))
    else:
        cmd_build(collection, set(rest))


if __name__ == "__main__":
    main()
