"""
Download traffic sign images from Wikimedia Commons and pre-render to
tiny PNGs in assets/signs/.  Uses Wikimedia's CDN for downloads and
the search API to verify filenames.

Requirements: pip install Pillow
"""

import hashlib
import json
import os
import sys
import time
import urllib.request
import urllib.parse
from collections import Counter
from io import BytesIO

from PIL import Image

# Output dimensions — square canvas (signs are various shapes)
SIGN_SIZE = 44

# ---------------------------------------------------------------------------
# Curated sign sources: (display_name, country_code, sign_type, wikimedia_filename)
# Filenames verified against Wikimedia Commons search API.
# Underscores and spaces are interchangeable in Wikimedia filenames.
# ---------------------------------------------------------------------------
SIGN_SOURCES = [
    # ========== STOP ==========
    ('USA',         'us', 'stop', 'MUTCD_R1-1.svg'),
    ('JAPAN',       'jp', 'stop', 'Japan_road_sign_330.svg'),
    ('FRANCE',      'fr', 'stop', 'France_road_sign_AB4.svg'),
    ('GERMANY',     'de', 'stop', 'Zeichen_206_-_Halt!_Vorfahrt_gewähren!_StVO_2017.svg'),
    ('MEXICO',      'mx', 'stop', 'MX_road_sign_SR-6.svg'),
    ('BRAZIL',      'br', 'stop', 'Brasil_R-1.svg'),
    ('TURKEY',      'tr', 'stop', 'Turkey_road_sign_TT-2.svg'),
    ('IRAN',        'ir', 'stop', 'Iran_road_sign_-_stop.svg'),
    ('SOUTH KOREA', 'kr', 'stop', 'Korean_Traffic_sign_(Stop).svg'),
    ('ISRAEL',      'il', 'stop', 'Israel_road_sign_302.svg'),
    ('THAILAND',    'th', 'stop', 'Thailand_road_sign_บ-1.svg'),
    ('ETHIOPIA',    'et', 'stop', 'Ethiopian_Stop_Sign.svg'),
    ('INDIA',       'in', 'stop', 'Indian_Road_Sign_I-I-1_(EN).svg'),
    ('CUBA',        'cu', 'stop', 'Cuban_Stop_Sign.svg'),
    ('VIETNAM',     'vn', 'stop', 'Vietnam_road_sign_P122.svg'),

    # ========== YIELD / GIVE WAY ==========
    ('USA',         'us', 'yield', 'MUTCD_R1-2.svg'),
    ('JAPAN',       'jp', 'yield', 'Japan_road_sign_329-2.svg'),
    ('GERMANY',     'de', 'yield', 'Zeichen_205_-_Vorfahrt_gewähren!_StVO_1970.svg'),
    ('FRANCE',      'fr', 'yield', 'France_road_sign_AB3a.svg'),
    ('BRAZIL',      'br', 'yield', 'BR_road_sign_R-2.svg'),
    ('SOUTH KOREA', 'kr', 'yield', 'Korea_Traffic_Safety_Sign_-_Road_Mark_-_522_Yield.svg'),
    ('SWEDEN',      'se', 'yield', 'Swedish_yield_sign.svg'),
    ('IRELAND',     'ie', 'yield', 'IE_road_sign_RUS-026.svg'),
    # Turkey yield: no SVG found on Commons
    ('VIETNAM',     'vn', 'yield', 'Vietnam_road_sign_W208.svg'),

    # ========== SPEED LIMIT (50) ==========
    ('USA',         'us', 'speed', 'MUTCD_R2-1.svg'),
    ('GERMANY',     'de', 'speed', 'Zeichen_274-50_-_Zulässige_Höchstgeschwindigkeit,_StVO_2017.svg'),
    ('JAPAN',       'jp', 'speed', 'Japan_road_sign_323_(50).svg'),
    ('UK',          'gb', 'speed', 'UK_traffic_sign_670V50.svg'),
    ('AUSTRALIA',   'au', 'speed', 'Australia_road_sign_R4-1_(50).svg'),
    ('FRANCE',      'fr', 'speed', 'France_road_sign_B14_(50).svg'),
    ('SOUTH KOREA', 'kr', 'speed', 'Korean_Traffic_sign_(Maximum_Speed_Limit_50kph).svg'),
    ('BRAZIL',      'br', 'speed', 'Brasil_R-19_(50).svg'),
    ('RUSSIA',      'ru', 'speed', 'RU_road_sign_3.24-50.svg'),

    # ========== NO ENTRY ==========
    ('USA',         'us', 'no_entry', 'MUTCD_R5-1.svg'),
    ('JAPAN',       'jp', 'no_entry', 'Japan_road_sign_303.svg'),
    ('GERMANY',     'de', 'no_entry', 'Zeichen_267_-_Verbot_der_Einfahrt,_StVO_1970.svg'),
    ('FRANCE',      'fr', 'no_entry', 'France_road_sign_B1.svg'),
    ('SOUTH KOREA', 'kr', 'no_entry', 'KR_road_sign_211.svg'),
    ('INDIA',       'in', 'no_entry', 'No_Entry_sign_India.svg'),
    ('BRAZIL',      'br', 'no_entry', 'Brasil_R-3.svg'),
    ('SWEDEN',      'se', 'no_entry', 'Sweden_road_sign_C1.svg'),
    ('VIETNAM',     'vn', 'no_entry', 'Vietnam_road_sign_P102.svg'),

    # ========== PEDESTRIAN CROSSING ==========
    ('USA',         'us', 'pedestrian', 'MUTCD_W11-2.svg'),
    ('JAPAN',       'jp', 'pedestrian', 'Japan_road_sign_407-A.svg'),
    ('GERMANY',     'de', 'pedestrian', 'Zeichen_133_-_Fußgänger,_StVO_1970.svg'),
    ('FRANCE',      'fr', 'pedestrian', 'France_road_sign_A13a.svg'),
    ('UK',          'gb', 'pedestrian', 'UK_traffic_sign_544.svg'),
    ('SOUTH KOREA', 'kr', 'pedestrian', 'KR_road_sign_322.svg'),
    ('BRAZIL',      'br', 'pedestrian', 'Brasil_A-32a.svg'),
    ('SWEDEN',      'se', 'pedestrian', 'Sweden_road_sign_A13.svg'),
    ('AUSTRALIA',   'au', 'pedestrian', 'AU_road_sign_W6-2.svg'),
    ('RUSSIA',      'ru', 'pedestrian', 'RU_road_sign_1.22.svg'),

    # ========== WARNING (triangles with pictograms) ==========
    ('USA',         'us', 'warning', 'MUTCD_W1-1L.svg'),
    ('JAPAN',       'jp', 'warning', 'Japan_road_sign_212.svg'),
    ('GERMANY',     'de', 'warning', 'Zeichen_103-10_-_Kurve_(links),_StVO_1992.svg'),
    ('FRANCE',      'fr', 'warning', 'France_road_sign_A1a.svg'),
    ('UK',          'gb', 'warning', 'UK_traffic_sign_512_(right).svg'),
    ('SOUTH KOREA', 'kr', 'warning', 'KR_road_sign_112.svg'),
    ('BRAZIL',      'br', 'warning', 'Brasil_A-1a.svg'),
    ('AUSTRALIA',   'au', 'warning', 'Australia_road_sign_W1-3-L.svg'),
    ('SWEDEN',      'se', 'warning', 'Sweden_road_sign_A1-1.svg'),
    ('RUSSIA',      'ru', 'warning', 'RU_road_sign_1.11.1.svg'),
    ('INDIA',       'in', 'warning', 'Indian_Road_Sign_II-2.svg'),
]


def _wikimedia_thumb_url(filename, width=256):
    """Compute the direct CDN thumbnail URL for a Wikimedia Commons file.

    Wikimedia uses MD5-hashed paths:
      upload.wikimedia.org/wikipedia/commons/thumb/{a}/{ab}/{filename}/{width}px-{filename}.png
    """
    # Wikimedia normalizes spaces to underscores for hashing
    normalized = filename.replace(' ', '_')
    md5 = hashlib.md5(normalized.encode('utf-8')).hexdigest()
    encoded = urllib.parse.quote(normalized)
    return (
        f"https://upload.wikimedia.org/wikipedia/commons/thumb/"
        f"{md5[0]}/{md5[:2]}/{encoded}/{width}px-{encoded}.png"
    )


def _download_thumb(filename, cache_dir, width=256):
    """Download a Wikimedia Commons thumbnail PNG via CDN."""
    # Check both new and old cache naming conventions
    cache_candidates = [
        os.path.join(cache_dir, filename.replace('/', '_') + f'.{width}px.png'),
        os.path.join(cache_dir, filename.replace('/', '_') + '.thumb.png'),
    ]
    for cp in cache_candidates:
        if os.path.exists(cp):
            with open(cp, 'rb') as f:
                return f.read()

    url = _wikimedia_thumb_url(filename, 200)  # 200px is a standard Wikimedia step
    # Retry with exponential backoff
    for attempt in range(3):
        delay = 5 * (2 ** attempt)  # 5, 10, 20 seconds
        time.sleep(delay)
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'LEDArcadeSigns/1.0 (educational LED art project)',
            })
            resp = urllib.request.urlopen(req, timeout=15)
            data = resp.read()
            cache_path = cache_candidates[0]
            with open(cache_path, 'wb') as f:
                f.write(data)
            return data
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"    Rate limited (attempt {attempt+1}/3), waiting...")
                continue
            elif e.code == 404:
                print(f"    Not found on CDN: {filename}")
                return None
            else:
                print(f"    HTTP {e.code}: {e}")
                return None
        except Exception as e:
            print(f"    Download failed: {e}")
            return None
    print(f"    Giving up after 3 attempts (rate limited)")
    return None


def _color_dist_sq(c1, c2):
    return (c1[0]-c2[0])**2 + (c1[1]-c2[1])**2 + (c1[2]-c2[2])**2


def _extract_palette(img, max_colors=12):
    """Extract dominant colors using quantization."""
    quantized = img.quantize(colors=max_colors, method=Image.Quantize.MEDIANCUT)
    palette_data = quantized.getpalette()
    hist = quantized.histogram()
    colors_with_count = []
    for i in range(max_colors):
        count = hist[i] if i < len(hist) else 0
        if count > 0:
            r = palette_data[i * 3]
            g = palette_data[i * 3 + 1]
            b = palette_data[i * 3 + 2]
            colors_with_count.append(((r, g, b), count))

    merge_threshold = 900
    merged = []
    for color, count in sorted(colors_with_count, key=lambda x: -x[1]):
        found = False
        for j, (mc, mtotal) in enumerate(merged):
            if _color_dist_sq(color, mc) < merge_threshold:
                w1, w2 = mtotal, count
                wt = w1 + w2
                new_c = (
                    int((mc[0]*w1 + color[0]*w2) / wt),
                    int((mc[1]*w1 + color[1]*w2) / wt),
                    int((mc[2]*w1 + color[2]*w2) / wt),
                )
                merged[j] = (new_c, wt)
                found = True
                break
        if not found:
            merged.append((color, count))
    return [c for c, _ in merged]


def _snap_to_palette(pixels, palette):
    cache = {}
    result = []
    for row in pixels:
        new_row = []
        for pixel in row:
            if pixel in cache:
                new_row.append(cache[pixel])
            else:
                best = min(palette, key=lambda c: _color_dist_sq(pixel, c))
                cache[pixel] = best
                new_row.append(best)
        result.append(tuple(new_row))
    return tuple(result)


def _cleanup_minor_colors(pixels, min_pct=3.0):
    total = len(pixels) * len(pixels[0])

    def _recount(px):
        c = Counter()
        for row in px:
            for v in row:
                c[v] += 1
        return c

    def _remap(px, old, new):
        return tuple(
            tuple(new if c == old else c for c in row)
            for row in px
        )

    # Phase 1: absorb tiny colors
    while True:
        counts = _recount(pixels)
        smallest = None
        smallest_n = total
        for c, n in counts.items():
            if (n / total * 100) < min_pct and n < smallest_n:
                smallest = c
                smallest_n = n
        if smallest is None:
            break
        others = [c for c in counts if c != smallest]
        if not others:
            break
        nearest = min(others, key=lambda c: _color_dist_sq(smallest, c))
        pixels = _remap(pixels, smallest, nearest)

    # Phase 2: merge blend artifacts
    changed = True
    while changed:
        changed = False
        counts = _recount(pixels)
        ranked = counts.most_common()
        for i, (color, n) in enumerate(ranked):
            if i < 3:
                continue
            larger = [(c, cn) for c, cn in ranked if cn > n]
            if len(larger) < 2:
                continue
            nearest_large = min(larger, key=lambda x: _color_dist_sq(color, x[0]))
            dist = _color_dist_sq(color, nearest_large[0])
            if dist < 10800:
                pixels = _remap(pixels, color, nearest_large[0])
                changed = True
                break

    return pixels


def process_sign(png_data):
    """Resize sign to SIGN_SIZE x SIGN_SIZE, palette-snap, and clean up."""
    img = Image.open(BytesIO(png_data)).convert('RGBA')

    # Create black background, composite alpha
    bg = Image.new('RGB', img.size, (0, 0, 0))
    bg.paste(img, (0, 0), img)
    img = bg

    # Extract palette from full-res
    palette = _extract_palette(img)

    # Fit within SIGN_SIZE preserving aspect ratio
    w, h = img.size
    scale = min(SIGN_SIZE / w, SIGN_SIZE / h)
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))
    img = img.resize((new_w, new_h), Image.LANCZOS)

    # Composite onto black canvas
    canvas = Image.new('RGB', (SIGN_SIZE, SIGN_SIZE), (0, 0, 0))
    ox = (SIGN_SIZE - new_w) // 2
    oy = (SIGN_SIZE - new_h) // 2
    canvas.paste(img, (ox, oy))

    # Extract pixels
    raw_pixels = []
    for y in range(SIGN_SIZE):
        row = []
        for x in range(SIGN_SIZE):
            row.append(canvas.getpixel((x, y)))
        raw_pixels.append(tuple(row))

    # Add black to palette (for background)
    if (0, 0, 0) not in palette:
        palette.append((0, 0, 0))

    snapped = _snap_to_palette(raw_pixels, palette)
    return _cleanup_minor_colors(snapped)


def main():
    cache_dir = os.path.join(os.path.dirname(__file__), '.sign_cache')
    os.makedirs(cache_dir, exist_ok=True)

    assets_dir = os.path.join(os.path.dirname(__file__), '..', 'assets', 'signs')
    os.makedirs(assets_dir, exist_ok=True)

    succeeded = []
    failed = []
    total = len(SIGN_SOURCES)

    print(f"Processing {total} signs...")

    for i, (display_name, country_code, sign_type, wiki_fn) in enumerate(SIGN_SOURCES):
        stem = f"{country_code}_{sign_type}"
        out_path = os.path.join(assets_dir, f"{stem}.png")

        # Skip if already processed
        if os.path.exists(out_path):
            print(f"  [{i+1}/{total}] [cached] {stem}")
            succeeded.append((display_name, sign_type, stem))
            continue

        print(f"  [{i+1}/{total}] {display_name} {sign_type}...")

        # Download thumbnail from CDN
        png_data = _download_thumb(wiki_fn, cache_dir)
        if png_data is None:
            failed.append((display_name, sign_type, wiki_fn))
            continue

        # Process: resize, palette-snap, clean
        try:
            pixels = process_sign(png_data)
        except Exception as e:
            print(f"    Process failed: {e}")
            failed.append((display_name, sign_type, wiki_fn))
            continue

        # Save PNG
        img = Image.new('RGB', (SIGN_SIZE, SIGN_SIZE))
        for y, row in enumerate(pixels):
            for x, color in enumerate(row):
                img.putpixel((x, y), color)
        img.save(out_path)
        succeeded.append((display_name, sign_type, stem))

    # Summary
    print(f"\nDone! {len(succeeded)} signs processed, {len(failed)} failed.")
    if failed:
        print("Failed:")
        for name, stype, fn in failed:
            print(f"  {name} ({stype}): {fn}")

    # Write manifest
    manifest_lines = ['# Generated by tools/build_signs.py', '']
    manifest_lines.append('SIGN_MANIFEST = [')
    sign_types = ['stop', 'yield', 'speed', 'no_entry', 'pedestrian', 'warning']
    for stype in sign_types:
        type_signs = [(n, t, s) for n, t, s in succeeded if t == stype]
        if type_signs:
            manifest_lines.append(f'    # ===== {stype.upper()} =====')
            for name, _, stem in sorted(type_signs):
                manifest_lines.append(f"    ({name!r}, {stype!r}, {stem!r}),")
    manifest_lines.append(']')
    manifest_lines.append('')

    manifest_path = os.path.join(assets_dir, 'manifest.py')
    with open(manifest_path, 'w') as f:
        f.write('\n'.join(manifest_lines))

    total_size = sum(
        os.path.getsize(os.path.join(assets_dir, f))
        for f in os.listdir(assets_dir) if f.endswith('.png')
    )
    print(f"{len(succeeded)} PNGs in assets/signs/ ({total_size / 1024:.0f} KB total)")


if __name__ == '__main__':
    main()
