#!/usr/bin/env python3
"""
Build constellation data from real astronomical catalogs.

Data sources (all fetched at build time):
  - Stellarium index.json (modern_st sky culture):
      constellation stick-figure polylines (HIP-ID chains)
      common star names
  - VizieR Hipparcos catalog I/239:
      RA (rad), Dec (rad), Vmag per HIP-ID

Every coordinate, line, and name is derived from hard catalog data.
No hand-placed positions, no guesswork.

Run:
  python3 tools/build_constellations.py
Outputs the CONSTELLATIONS list to stdout — paste into visuals/constellations.py.
"""

import json
import math
import urllib.request
import urllib.parse
import csv
import io
import sys

# ── Which constellations we want, and static metadata ───────────
#    Stellarium abbreviation → (display name, season, zodiac)

META = {
    'Ari': ('ARIES',           'AUTUMN', True),
    'Tau': ('TAURUS',          'WINTER', True),
    'Gem': ('GEMINI',          'WINTER', True),
    'Cnc': ('CANCER',          'SPRING', True),
    'Leo': ('LEO',             'SPRING', True),
    'Vir': ('VIRGO',           'SPRING', True),
    'Lib': ('LIBRA',           'SPRING', True),
    'Sco': ('SCORPIUS',        'SUMMER', True),
    'Sgr': ('SAGITTARIUS',     'SUMMER', True),
    'Cap': ('CAPRICORNUS',     'AUTUMN', True),
    'Aqr': ('AQUARIUS',        'AUTUMN', True),
    'Psc': ('PISCES',          'AUTUMN', True),
    'Ori': ('ORION',           'WINTER', False),
    'UMa': ('URSA MAJOR',      'SPRING', False),
    'UMi': ('URSA MINOR',      'SUMMER', False),
    'Cas': ('CASSIOPEIA',      'AUTUMN', False),
    'Cyg': ('CYGNUS',          'SUMMER', False),
    'Lyr': ('LYRA',            'SUMMER', False),
    'Aql': ('AQUILA',          'SUMMER', False),
    'CMa': ('CANIS MAJOR',     'WINTER', False),
    'Peg': ('PEGASUS',         'AUTUMN', False),
    'And': ('ANDROMEDA',       'AUTUMN', False),
    'Per': ('PERSEUS',         'WINTER', False),
    'Dra': ('DRACO',           'SUMMER', False),
    'CrB': ('CORONA BOREALIS', 'SUMMER', False),
    'Crv': ('CORVUS',          'SPRING', False),
    'Cru': ('CRUX',            'SPRING', False),
    'Cen': ('CENTAURUS',       'SPRING', False),
}

ZODIAC_ORDER = [
    'Ari', 'Tau', 'Gem', 'Cnc', 'Leo', 'Vir',
    'Lib', 'Sco', 'Sgr', 'Cap', 'Aqr', 'Psc',
]
OTHER_ORDER = [
    'Ori', 'UMa', 'UMi', 'Cas', 'Cyg', 'Lyr', 'Aql', 'CMa',
    'Peg', 'And', 'Per', 'Dra', 'CrB', 'Crv', 'Cru', 'Cen',
]


def log(msg):
    print(msg, file=sys.stderr)


def fetch(url):
    """GET a URL, return bytes."""
    req = urllib.request.Request(url, headers={'User-Agent': 'led-arcade/1.0'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


# ── Stellarium index.json parser ────────────────────────────────

def parse_stellarium_json(data):
    """Parse Stellarium modern_st/index.json.

    Returns:
      constellations: {abbrev: [(hip1, hip2), ...]}  — line segment pairs
      star_names:     {hip: 'Common Name'}
    """
    js = json.loads(data)

    # --- Constellation polylines ---
    # Each constellation has "lines": [[hip, hip, hip, ...], ...]
    # Consecutive HIP IDs in a sub-array are connected.
    # A repeated HIP ID (h, h) is a pen-lift (skip).
    constellations = {}
    for entry in js.get('constellations', []):
        cid = entry.get('id', '')
        # ID format: "CON modern_st Ori"
        parts = cid.split()
        if len(parts) < 3:
            continue
        abbrev = parts[-1]

        pairs = []
        for chain in entry.get('lines', []):
            for i in range(len(chain) - 1):
                h1, h2 = chain[i], chain[i + 1]
                if h1 != h2:  # skip pen-lift markers
                    pairs.append((h1, h2))
        constellations[abbrev] = pairs

    # --- Star names ---
    # "common_names": {"HIP 677": [{"native": "Alpheratz"}], ...}
    star_names = {}
    for key, names_list in js.get('common_names', {}).items():
        if key.startswith('HIP '):
            try:
                hip = int(key[4:])
            except ValueError:
                continue
            for entry in names_list:
                name = entry.get('native', '') or entry.get('english', '')
                if name:
                    star_names[hip] = name
                    break

    return constellations, star_names


# ── VizieR star catalog query ──────────────────────────────────

def fetch_stars_vizier(hip_ids):
    """Query VizieR Hipparcos I/239 for RA/Dec/Vmag.
    Returns {hip: (ra_deg, dec_deg, vmag)}.
    Uses POST to handle long IN-clauses, batched.
    """
    hip_list = sorted(hip_ids)
    all_results = {}
    batch_size = 200

    for start in range(0, len(hip_list), batch_size):
        batch = hip_list[start:start + batch_size]
        in_clause = ','.join(str(h) for h in batch)
        query = (f'SELECT HIP, RAICRS, DEICRS, Vmag '
                 f'FROM "I/239/hip_main" '
                 f'WHERE HIP IN ({in_clause})')

        body = urllib.parse.urlencode({
            'request': 'doQuery',
            'lang': 'adql',
            'format': 'csv',
            'query': query,
        }).encode()

        url = 'https://tapvizier.cds.unistra.fr/TAPVizieR/tap/sync'
        req = urllib.request.Request(url, data=body,
                                     headers={'User-Agent': 'led-arcade/1.0'})
        with urllib.request.urlopen(req, timeout=60) as r:
            text = r.read().decode('utf-8')

        reader = csv.reader(io.StringIO(text))
        header = next(reader, None)
        if header is None:
            continue
        for row in reader:
            if len(row) < 4:
                continue
            try:
                hip = int(row[0])
                ra_deg = float(row[1])   # RAICRS already in degrees
                dec_deg = float(row[2])  # DEICRS already in degrees
                vmag = float(row[3]) if row[3].strip() else 6.0
                all_results[hip] = (ra_deg, dec_deg, vmag)
            except (ValueError, IndexError):
                pass

        log(f"  batch {start // batch_size + 1}: "
            f"{len(all_results)} stars retrieved so far")

    return all_results


# ── Projection math ─────────────────────────────────────────────

def spherical_centroid(coords):
    """Mean direction of [(ra_deg, dec_deg), …] — handles RA wraparound."""
    x = y = z = 0.0
    for ra, dec in coords:
        a, d = math.radians(ra), math.radians(dec)
        x += math.cos(d) * math.cos(a)
        y += math.cos(d) * math.sin(a)
        z += math.sin(d)
    n = len(coords)
    x /= n; y /= n; z /= n
    dec0 = math.degrees(math.atan2(z, math.sqrt(x * x + y * y)))
    ra0 = math.degrees(math.atan2(y, x)) % 360
    return ra0, dec0


def gnomonic(ra, dec, ra0, dec0):
    """Gnomonic (tangent-plane) projection.
    Returns (x, y) where +x = East, +y = North (in radians from center).
    Returns None if point is behind the tangent plane.
    """
    a  = math.radians(ra);   d  = math.radians(dec)
    a0 = math.radians(ra0);  d0 = math.radians(dec0)
    cos_c = (math.sin(d0) * math.sin(d) +
             math.cos(d0) * math.cos(d) * math.cos(a - a0))
    if cos_c <= 0.001:
        return None
    x = math.cos(d) * math.sin(a - a0) / cos_c
    y = (math.cos(d0) * math.sin(d) -
         math.sin(d0) * math.cos(d) * math.cos(a - a0)) / cos_c
    return x, y


def mag_class(vmag):
    """Vmag → display magnitude class: 1 (bright cross), 2 (medium), 3 (dot)."""
    if vmag < 1.5:
        return 1
    if vmag < 3.5:
        return 2
    return 3


# ── Build one constellation ─────────────────────────────────────

def build(abbrev, line_pairs, star_data, star_names):
    """Build one constellation entry from catalog data."""
    name, season, zodiac = META[abbrev]

    # All HIP IDs referenced in Stellarium lines
    all_hips = set()
    for h1, h2 in line_pairs:
        all_hips.add(h1)
        all_hips.add(h2)

    # Keep only stars with catalog data, sorted brightest-first
    have = sorted([h for h in all_hips if h in star_data],
                  key=lambda h: star_data[h][2])
    if len(have) < 2:
        log(f"  SKIP {name}: only {len(have)} star(s) with data")
        return None

    # Brightest star name
    bright_name = star_names.get(have[0], f'HIP {have[0]}').upper()

    # Centroid (RA-wraparound safe)
    positions = [(star_data[h][0], star_data[h][1]) for h in have]
    ra0, dec0 = spherical_centroid(positions)

    # Project all stars via gnomonic projection
    projected = []
    for h in have:
        ra, dec, vmag = star_data[h]
        pt = gnomonic(ra, dec, ra0, dec0)
        if pt is None:
            log(f"    {name}: HIP {h} behind tangent plane, skipping")
            continue
        projected.append((h, pt[0], pt[1], vmag))

    if len(projected) < 2:
        return None

    # Scale to 50×50 grid with 2px margin
    xs = [p[1] for p in projected]
    ys = [p[2] for p in projected]
    range_x = max(xs) - min(xs) or 0.001
    range_y = max(ys) - min(ys) or 0.001
    margin = 2
    usable = 50 - 2 * margin          # 46 px
    scale = usable / max(range_x, range_y)
    cx = (min(xs) + max(xs)) / 2
    cy = (min(ys) + max(ys)) / 2

    stars = []
    final_idx = {}
    for i, (h, px, py, vmag) in enumerate(projected):
        # Mirror x → East is left (sky-chart orientation looking up)
        # Flip y  → North is up   (display y grows downward)
        sx = int(round(25 - (px - cx) * scale))
        sy = int(round(25 - (py - cy) * scale))
        sx = max(0, min(49, sx))
        sy = max(0, min(49, sy))
        stars.append((sx, sy, mag_class(vmag)))
        final_idx[h] = i

    # Build lines from Stellarium pairs, skip missing, dedup
    lines = []
    seen = set()
    for h1, h2 in line_pairs:
        if h1 in final_idx and h2 in final_idx:
            a, b = final_idx[h1], final_idx[h2]
            if a != b:
                key = (min(a, b), max(a, b))
                if key not in seen:
                    seen.add(key)
                    lines.append((a, b))

    return {
        'name': name, 'season': season, 'zodiac': zodiac,
        'bright_star': bright_name, 'stars': stars, 'lines': lines,
    }


# ── Pretty-print the Python list ───────────────────────────────

def format_entry(entry):
    """Format one constellation as Python code lines."""
    z = 'True' if entry['zodiac'] else 'False'
    out = []
    out.append(f"    {{'name': '{entry['name']}', "
               f"'season': '{entry['season']}', 'zodiac': {z},")
    out.append(f"     'bright_star': '{entry['bright_star']}',")

    # Stars — wrap to ~80 cols
    items = [f'({x}, {y}, {m})' for x, y, m in entry['stars']]
    star_body = ', '.join(items)
    if len(star_body) <= 55:
        out.append(f"     'stars': [{star_body}],")
    else:
        out.append("     'stars': [")
        line = '              '
        for item in items:
            if len(line) + len(item) + 2 > 80 and line.strip():
                out.append(line.rstrip(' '))
                line = '              '
            line += item + ', '
        if line.strip():
            out.append(line.rstrip(', '))
        out.append("     ],")

    # Lines
    l_items = [f'({a}, {b})' for a, b in entry['lines']]
    l_body = ', '.join(l_items)
    if len(l_body) <= 55:
        out.append(f"     'lines': [{l_body}]}},")
    else:
        out.append("     'lines': [")
        line = '              '
        for item in l_items:
            if len(line) + len(item) + 2 > 80 and line.strip():
                out.append(line.rstrip(' '))
                line = '              '
            line += item + ', '
        if line.strip():
            out.append(line.rstrip(', '))
        out.append("     ]},")

    return out


# ── Main ────────────────────────────────────────────────────────

def main():
    # 1. Fetch Stellarium sky-culture data (polylines + star names)
    log("Fetching Stellarium modern_st/index.json ...")
    raw = fetch(
        'https://raw.githubusercontent.com/Stellarium/stellarium/'
        'master/skycultures/modern_st/index.json')
    constellations, star_names = parse_stellarium_json(raw)
    log(f"  {len(constellations)} constellations, "
        f"{len(star_names)} named stars")

    # 2. Collect all HIP IDs we need
    need = set()
    for abbrev in META:
        for h1, h2 in constellations.get(abbrev, []):
            need.add(h1)
            need.add(h2)
    log(f"Total unique HIP IDs needed: {len(need)}")

    # 3. Fetch real coordinates from VizieR Hipparcos catalog
    log("Querying VizieR Hipparcos I/239 ...")
    star_data = fetch_stars_vizier(need)
    log(f"Catalog data: {len(star_data)} / {len(need)} stars")

    missing = need - set(star_data)
    if missing:
        log(f"Missing: {sorted(missing)[:20]}"
            f"{'…' if len(missing) > 20 else ''}")

    # 4. Build each constellation
    results = []

    log("\n── Zodiac ──")
    for abbrev in ZODIAC_ORDER:
        if abbrev not in constellations:
            log(f"  {META[abbrev][0]}: NOT in Stellarium data!")
            continue
        entry = build(abbrev, constellations[abbrev], star_data, star_names)
        if entry:
            results.append(entry)
            log(f"  {entry['name']:20s}  "
                f"{len(entry['stars']):2d} stars  "
                f"{len(entry['lines']):2d} lines  "
                f"brightest: {entry['bright_star']}")

    log("\n── Non-zodiac ──")
    for abbrev in OTHER_ORDER:
        if abbrev not in constellations:
            log(f"  {META[abbrev][0]}: NOT in Stellarium data!")
            continue
        entry = build(abbrev, constellations[abbrev], star_data, star_names)
        if entry:
            results.append(entry)
            log(f"  {entry['name']:20s}  "
                f"{len(entry['stars']):2d} stars  "
                f"{len(entry['lines']):2d} lines  "
                f"brightest: {entry['bright_star']}")

    # 5. Output Python code
    print("CONSTELLATIONS = [")
    prev_zodiac = None
    for entry in results:
        if entry['zodiac'] and prev_zodiac is not True:
            print("    # ==================== ZODIAC (12) ====================")
        elif not entry['zodiac'] and prev_zodiac is not False:
            print("\n    # ==================== NON-ZODIAC (16) ====================")
        prev_zodiac = entry['zodiac']
        for line in format_entry(entry):
            print(line)

    print("]")
    log(f"\nDone — {len(results)} constellations generated from catalog data.")


if __name__ == '__main__':
    main()
