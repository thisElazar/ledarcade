"""
Download flag images from flagcdn.com and pre-render to pixel data.
Generates visuals/flag_data.py with RGB pixel arrays for each flag.
"""

import json
import math
import os
import sys
import urllib.request
from collections import Counter
from PIL import Image
from io import BytesIO

# Output dimensions
FLAG_W = 60
FLAG_H = 40

# Map our display names to ISO 3166-1 alpha-2 codes
NAME_TO_ISO = {
    # Africa
    'ALGERIA': 'dz', 'CAMEROON': 'cm', 'CHAD': 'td', 'EGYPT': 'eg',
    'ETHIOPIA': 'et', 'GHANA': 'gh', 'IVORY COAST': 'ci', 'KENYA': 'ke',
    'LIBYA': 'ly', 'MADAGASCAR': 'mg', 'MALI': 'ml', 'MOROCCO': 'ma',
    'MOZAMBIQUE': 'mz', 'NIGER': 'ne', 'NIGERIA': 'ng', 'SENEGAL': 'sn',
    'SOUTH AFRICA': 'za', 'TANZANIA': 'tz', 'TUNISIA': 'tn', 'UGANDA': 'ug',
    # Americas
    'ARGENTINA': 'ar', 'BAHAMAS': 'bs', 'BOLIVIA': 'bo', 'BRAZIL': 'br',
    'CANADA': 'ca', 'CHILE': 'cl', 'COLOMBIA': 'co', 'COSTA RICA': 'cr',
    'CUBA': 'cu', 'DOM. REPUBLIC': 'do', 'ECUADOR': 'ec',
    'EL SALVADOR': 'sv', 'GUATEMALA': 'gt', 'HAITI': 'ht',
    'HONDURAS': 'hn', 'JAMAICA': 'jm', 'MEXICO': 'mx',
    'NICARAGUA': 'ni', 'PANAMA': 'pa', 'PARAGUAY': 'py', 'PERU': 'pe',
    'TRINIDAD': 'tt', 'URUGUAY': 'uy', 'USA': 'us', 'VENEZUELA': 've',
    # Asia
    'BANGLADESH': 'bd', 'CAMBODIA': 'kh', 'CHINA': 'cn', 'INDIA': 'in',
    'INDONESIA': 'id', 'IRAN': 'ir', 'IRAQ': 'iq', 'ISRAEL': 'il',
    'JAPAN': 'jp', 'JORDAN': 'jo', 'KUWAIT': 'kw', 'LAOS': 'la',
    'LEBANON': 'lb', 'MALAYSIA': 'my', 'MONGOLIA': 'mn', 'MYANMAR': 'mm',
    'NEPAL': 'np', 'NORTH KOREA': 'kp', 'PAKISTAN': 'pk',
    'PALESTINE': 'ps', 'PHILIPPINES': 'ph', 'QATAR': 'qa',
    'SAUDI ARABIA': 'sa', 'SINGAPORE': 'sg', 'SOUTH KOREA': 'kr',
    'SRI LANKA': 'lk', 'THAILAND': 'th', 'TURKEY': 'tr', 'UAE': 'ae',
    'UZBEKISTAN': 'uz', 'VIETNAM': 'vn',
    # Europe
    'ALBANIA': 'al', 'AUSTRIA': 'at', 'BELGIUM': 'be', 'BULGARIA': 'bg',
    'CROATIA': 'hr', 'CZECH REPUBLIC': 'cz', 'DENMARK': 'dk',
    'ESTONIA': 'ee', 'FINLAND': 'fi', 'FRANCE': 'fr', 'GERMANY': 'de',
    'GREECE': 'gr', 'HUNGARY': 'hu', 'ICELAND': 'is', 'IRELAND': 'ie',
    'ITALY': 'it', 'LATVIA': 'lv', 'LITHUANIA': 'lt', 'LUXEMBOURG': 'lu',
    'MALTA': 'mt', 'MONACO': 'mc', 'NETHERLANDS': 'nl', 'NORWAY': 'no',
    'POLAND': 'pl', 'PORTUGAL': 'pt', 'ROMANIA': 'ro', 'RUSSIA': 'ru',
    'SERBIA': 'rs', 'SLOVAKIA': 'sk', 'SLOVENIA': 'si', 'SPAIN': 'es',
    'SWEDEN': 'se', 'SWITZERLAND': 'ch', 'UK': 'gb', 'UKRAINE': 'ua',
    # Oceania
    'AUSTRALIA': 'au', 'FIJI': 'fj', 'MARSHALL IS.': 'mh',
    'MICRONESIA': 'fm', 'NAURU': 'nr', 'NEW ZEALAND': 'nz',
    'PALAU': 'pw', 'PAPUA N.G.': 'pg', 'SAMOA': 'ws',
    'SOLOMON IS.': 'sb', 'TONGA': 'to', 'VANUATU': 'vu',
}

# Continent assignments
NAME_TO_CONTINENT = {
    # Africa
    'ALGERIA': 'AFRICA', 'CAMEROON': 'AFRICA', 'CHAD': 'AFRICA',
    'EGYPT': 'AFRICA', 'ETHIOPIA': 'AFRICA', 'GHANA': 'AFRICA',
    'IVORY COAST': 'AFRICA', 'KENYA': 'AFRICA', 'LIBYA': 'AFRICA',
    'MADAGASCAR': 'AFRICA', 'MALI': 'AFRICA', 'MOROCCO': 'AFRICA',
    'MOZAMBIQUE': 'AFRICA', 'NIGER': 'AFRICA', 'NIGERIA': 'AFRICA',
    'SENEGAL': 'AFRICA', 'SOUTH AFRICA': 'AFRICA', 'TANZANIA': 'AFRICA',
    'TUNISIA': 'AFRICA', 'UGANDA': 'AFRICA',
    # Americas
    'ARGENTINA': 'AMERICAS', 'BAHAMAS': 'AMERICAS', 'BOLIVIA': 'AMERICAS',
    'BRAZIL': 'AMERICAS', 'CANADA': 'AMERICAS', 'CHILE': 'AMERICAS',
    'COLOMBIA': 'AMERICAS', 'COSTA RICA': 'AMERICAS', 'CUBA': 'AMERICAS',
    'DOM. REPUBLIC': 'AMERICAS', 'ECUADOR': 'AMERICAS',
    'EL SALVADOR': 'AMERICAS', 'GUATEMALA': 'AMERICAS', 'HAITI': 'AMERICAS',
    'HONDURAS': 'AMERICAS', 'JAMAICA': 'AMERICAS', 'MEXICO': 'AMERICAS',
    'NICARAGUA': 'AMERICAS', 'PANAMA': 'AMERICAS', 'PARAGUAY': 'AMERICAS',
    'PERU': 'AMERICAS', 'TRINIDAD': 'AMERICAS', 'URUGUAY': 'AMERICAS',
    'USA': 'AMERICAS', 'VENEZUELA': 'AMERICAS',
    # Asia
    'BANGLADESH': 'ASIA', 'CAMBODIA': 'ASIA', 'CHINA': 'ASIA',
    'INDIA': 'ASIA', 'INDONESIA': 'ASIA', 'IRAN': 'ASIA', 'IRAQ': 'ASIA',
    'ISRAEL': 'ASIA', 'JAPAN': 'ASIA', 'JORDAN': 'ASIA', 'KUWAIT': 'ASIA',
    'LAOS': 'ASIA', 'LEBANON': 'ASIA', 'MALAYSIA': 'ASIA',
    'MONGOLIA': 'ASIA', 'MYANMAR': 'ASIA', 'NEPAL': 'ASIA',
    'NORTH KOREA': 'ASIA', 'PAKISTAN': 'ASIA', 'PALESTINE': 'ASIA',
    'PHILIPPINES': 'ASIA', 'QATAR': 'ASIA', 'SAUDI ARABIA': 'ASIA',
    'SINGAPORE': 'ASIA', 'SOUTH KOREA': 'ASIA', 'SRI LANKA': 'ASIA',
    'THAILAND': 'ASIA', 'TURKEY': 'ASIA', 'UAE': 'ASIA',
    'UZBEKISTAN': 'ASIA', 'VIETNAM': 'ASIA',
    # Europe
    'ALBANIA': 'EUROPE', 'AUSTRIA': 'EUROPE', 'BELGIUM': 'EUROPE',
    'BULGARIA': 'EUROPE', 'CROATIA': 'EUROPE', 'CZECH REPUBLIC': 'EUROPE',
    'DENMARK': 'EUROPE', 'ESTONIA': 'EUROPE', 'FINLAND': 'EUROPE',
    'FRANCE': 'EUROPE', 'GERMANY': 'EUROPE', 'GREECE': 'EUROPE',
    'HUNGARY': 'EUROPE', 'ICELAND': 'EUROPE', 'IRELAND': 'EUROPE',
    'ITALY': 'EUROPE', 'LATVIA': 'EUROPE', 'LITHUANIA': 'EUROPE',
    'LUXEMBOURG': 'EUROPE', 'MALTA': 'EUROPE', 'MONACO': 'EUROPE',
    'NETHERLANDS': 'EUROPE', 'NORWAY': 'EUROPE', 'POLAND': 'EUROPE',
    'PORTUGAL': 'EUROPE', 'ROMANIA': 'EUROPE', 'RUSSIA': 'EUROPE',
    'SERBIA': 'EUROPE', 'SLOVAKIA': 'EUROPE', 'SLOVENIA': 'EUROPE',
    'SPAIN': 'EUROPE', 'SWEDEN': 'EUROPE', 'SWITZERLAND': 'EUROPE',
    'UK': 'EUROPE', 'UKRAINE': 'EUROPE',
    # Oceania
    'AUSTRALIA': 'OCEANIA', 'FIJI': 'OCEANIA', 'MARSHALL IS.': 'OCEANIA',
    'MICRONESIA': 'OCEANIA', 'NAURU': 'OCEANIA', 'NEW ZEALAND': 'OCEANIA',
    'PALAU': 'OCEANIA', 'PAPUA N.G.': 'OCEANIA', 'SAMOA': 'OCEANIA',
    'SOLOMON IS.': 'OCEANIA', 'TONGA': 'OCEANIA', 'VANUATU': 'OCEANIA',
}


def download_flag(iso_code):
    """Download flag PNG from flagcdn.com at 256px width."""
    url = f"https://flagcdn.com/w320/{iso_code}.png"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=10)
        return resp.read()
    except Exception as e:
        print(f"  FAILED to download {iso_code}: {e}")
        return None


def _color_dist_sq(c1, c2):
    """Squared Euclidean distance between two RGB tuples."""
    return (c1[0]-c2[0])**2 + (c1[1]-c2[1])**2 + (c1[2]-c2[2])**2


def _extract_palette(img, max_colors=12):
    """Extract dominant colors from a flag image using Pillow's quantize.

    Returns a list of RGB tuples representing the flag's true palette.
    """
    # Quantize to find dominant colors
    quantized = img.quantize(colors=max_colors, method=Image.Quantize.MEDIANCUT)
    palette_data = quantized.getpalette()  # flat [r,g,b,r,g,b,...]
    # Count how many pixels map to each palette index
    hist = quantized.histogram()
    colors_with_count = []
    for i in range(max_colors):
        count = hist[i] if i < len(hist) else 0
        if count > 0:
            r = palette_data[i * 3]
            g = palette_data[i * 3 + 1]
            b = palette_data[i * 3 + 2]
            colors_with_count.append(((r, g, b), count))

    # Merge colors that are very close together (within threshold)
    merge_threshold = 900  # ~30 per channel squared
    merged = []
    for color, count in sorted(colors_with_count, key=lambda x: -x[1]):
        found = False
        for j, (mc, mtotal) in enumerate(merged):
            if _color_dist_sq(color, mc) < merge_threshold:
                # Weighted average merge
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
    """Snap each pixel to the nearest palette color."""
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
    """Iteratively merge artifact colors into their nearest dominant neighbor.

    Two-phase approach:
    1. Absorb any color below min_pct into its nearest neighbor.
    2. Merge any remaining color that is "close" to a larger color —
       catches anti-aliasing blends (e.g. pink between red and white)
       even when they're above the population threshold.
    """
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

    # Phase 2: merge blend artifacts — if a color is between two larger
    # colors (i.e., it looks like an interpolation), absorb it.
    changed = True
    while changed:
        changed = False
        counts = _recount(pixels)
        ranked = counts.most_common()

        for i, (color, n) in enumerate(ranked):
            pct = n / total * 100
            # Only consider non-dominant colors (not in top 3 by count)
            if i < 3:
                continue
            # Check if this color sits between two larger colors
            # (i.e. it's a blend artifact from anti-aliasing)
            larger = [(c, cn) for c, cn in ranked if cn > n]
            if len(larger) < 2:
                continue
            nearest_large = min(larger, key=lambda x: _color_dist_sq(color, x[0]))
            dist = _color_dist_sq(color, nearest_large[0])
            # If it's close enough to a larger color, it's a blend artifact.
            # Threshold: colors within ~60 per channel (dist < 10800)
            # are likely blends rather than distinct flag colors.
            if dist < 10800:
                pixels = _remap(pixels, color, nearest_large[0])
                changed = True
                break  # Restart counting after each merge

    return pixels


def process_flag(png_data, name):
    """Resize flag image to FLAG_W x FLAG_H and extract pixel data.

    Uses LANCZOS for accurate geometry, then snaps to the flag's
    extracted color palette for crisp boundaries.
    """
    img = Image.open(BytesIO(png_data)).convert('RGB')

    # Nepal is non-rectangular — handle specially
    if name == 'NEPAL':
        bg = Image.new('RGB', (img.width, img.height), (20, 20, 40))
        img_rgba = Image.open(BytesIO(png_data)).convert('RGBA')
        bg.paste(img_rgba, (0, 0), img_rgba)
        img = bg

    # Extract palette from full-res image first
    palette = _extract_palette(img)

    # Downscale with LANCZOS for accurate geometry
    img = img.resize((FLAG_W, FLAG_H), Image.LANCZOS)

    # Extract raw pixels
    raw_pixels = []
    for y in range(FLAG_H):
        row = []
        for x in range(FLAG_W):
            row.append(img.getpixel((x, y)))
        raw_pixels.append(tuple(row))

    # Snap to palette for crisp boundaries
    snapped = _snap_to_palette(raw_pixels, palette)

    # Absorb rare anti-aliasing artifacts into dominant colors
    return _cleanup_minor_colors(snapped)


def main():
    cache_dir = os.path.join(os.path.dirname(__file__), '.flag_cache')
    os.makedirs(cache_dir, exist_ok=True)

    output_path = os.path.join(os.path.dirname(__file__), '..', 'visuals', 'flag_data.py')

    flags = {}
    failed = []

    names = sorted(NAME_TO_ISO.keys())
    print(f"Processing {len(names)} flags at {FLAG_W}x{FLAG_H}...")

    for i, name in enumerate(names):
        iso = NAME_TO_ISO[name]
        cache_file = os.path.join(cache_dir, f"{iso}.png")

        # Use cache if available
        if os.path.exists(cache_file):
            with open(cache_file, 'rb') as f:
                png_data = f.read()
        else:
            print(f"  [{i+1}/{len(names)}] Downloading {name} ({iso})...")
            png_data = download_flag(iso)
            if png_data is None:
                failed.append(name)
                continue
            with open(cache_file, 'wb') as f:
                f.write(png_data)

        pixels = process_flag(png_data, name)
        continent = NAME_TO_CONTINENT[name]
        flags[name] = (continent, pixels)

    if failed:
        print(f"\nFailed to download: {failed}")

    # Write PNGs to assets/flags/
    assets_dir = os.path.join(os.path.dirname(__file__), '..', 'assets', 'flags')
    os.makedirs(assets_dir, exist_ok=True)

    for name, (continent, pixels) in flags.items():
        iso = NAME_TO_ISO[name]
        img = Image.new('RGB', (FLAG_W, FLAG_H))
        for y, row in enumerate(pixels):
            for x, color in enumerate(row):
                img.putpixel((x, y), color)
        img.save(os.path.join(assets_dir, f"{iso}.png"))

    # Write manifest with flag metadata
    manifest_path = os.path.join(assets_dir, 'manifest.py')
    with open(manifest_path, 'w') as f:
        f.write(f'"""Flag manifest — generated by tools/build_flags.py"""\n\n')
        f.write(f"FLAG_W = {FLAG_W}\n")
        f.write(f"FLAG_H = {FLAG_H}\n\n")
        f.write("# (display_name, continent, iso_code)\n")
        f.write("FLAGS = [\n")
        for continent in ['AFRICA', 'AMERICAS', 'ASIA', 'EUROPE', 'OCEANIA']:
            f.write(f"    # ===== {continent} =====\n")
            continent_flags = sorted(
                [(n, c) for n, (c, _) in flags.items() if c == continent]
            )
            for name, cont in continent_flags:
                iso = NAME_TO_ISO[name]
                f.write(f"    ({name!r}, {cont!r}, {iso!r}),\n")
            f.write("\n")
        f.write("]\n")

    total_size = sum(
        os.path.getsize(os.path.join(assets_dir, f))
        for f in os.listdir(assets_dir) if f.endswith('.png')
    )
    print(f"Done! {len(flags)} PNGs written to assets/flags/ ({total_size / 1024:.0f} KB total)")


if __name__ == '__main__':
    main()
