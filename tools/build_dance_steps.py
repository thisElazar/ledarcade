#!/usr/bin/env python3
"""
build_dance_steps.py — Generate footprint step data for visuals/dance.py
========================================================================
Encodes standardized basic figures from published dance syllabi (ISTD/WDSF
Bronze, Vaganova, CLRG, etc.) using compass-direction step descriptions,
then converts to pixel coordinates for a 50×50 floor diagram.

Input format per step:
  (foot, direction, distance, beat, action)
  foot:      'L' or 'R'
  direction: compass 'N','NE','E','SE','S','SW','W','NW', or 'C' (close)
  distance:  pixels to move in that direction (0 for close)
  beat:      beat number (1.0, 2.0, etc.)
  action:    'step', 'close', 'tap', 'stamp', 'slide', 'hook'

Processing: walk steps accumulating position from center, normalize bounding
box to fit 50×50 floor area, output pixel coords.

Usage:
  python3 tools/build_dance_steps.py all          # All dances
  python3 tools/build_dance_steps.py waltz         # Single dance
  python3 tools/build_dance_steps.py --list        # Show available
"""

import json
import math
import sys
from functools import partial

eprint = partial(print, file=sys.stderr, flush=True)

# ---------------------------------------------------------------------------
# Compass directions → (dx, dy) unit vectors
# Note: Y increases downward (screen coords), so N = -Y, S = +Y
# ---------------------------------------------------------------------------
_D = 1.0 / math.sqrt(2)
COMPASS = {
    'N':  ( 0, -1),
    'NE': ( _D, -_D),
    'E':  ( 1,  0),
    'SE': ( _D,  _D),
    'S':  ( 0,  1),
    'SW': (-_D,  _D),
    'W':  (-1,  0),
    'NW': (-_D, -_D),
    'C':  ( 0,  0),     # close — handled specially
}

# ---------------------------------------------------------------------------
# Dance figure definitions
# (foot, direction, distance, beat, action)
# Distances in abstract units; normalized later.
# ---------------------------------------------------------------------------

FIGURES = {
    'waltz': [
        {
            'name': 'Natural Turn',
            'steps': [
                ('R', 'N',  8, 1.0, 'step'),
                ('L', 'NE', 6, 2.0, 'step'),
                ('R', 'C',  0, 3.0, 'close'),
                ('L', 'S',  8, 1.0, 'step'),
                ('R', 'SW', 6, 2.0, 'step'),
                ('L', 'C',  0, 3.0, 'close'),
            ],
        },
        {
            'name': 'Reverse Turn',
            'steps': [
                ('L', 'N',  8, 1.0, 'step'),
                ('R', 'NW', 6, 2.0, 'step'),
                ('L', 'C',  0, 3.0, 'close'),
                ('R', 'S',  8, 1.0, 'step'),
                ('L', 'SE', 6, 2.0, 'step'),
                ('R', 'C',  0, 3.0, 'close'),
            ],
        },
    ],
    'tango': [
        {
            'name': 'Walk + Link',
            'steps': [
                ('L', 'N', 8, 1.0, 'step'),
                ('R', 'N', 8, 2.0, 'step'),
                ('L', 'N', 6, 3.0, 'step'),
                ('R', 'E', 5, 4.0, 'step'),
                ('L', 'C', 0, 4.5, 'close'),
            ],
        },
        {
            'name': 'Closed Promenade',
            'steps': [
                ('L', 'NW', 7, 1.0, 'step'),
                ('R', 'N',  8, 2.0, 'step'),
                ('L', 'NE', 6, 3.0, 'step'),
                ('R', 'C',  0, 4.0, 'close'),
            ],
        },
    ],
    'foxtrot': [
        {
            'name': 'Feather Step',
            'steps': [
                ('R', 'N',  8, 1.0, 'step'),
                ('L', 'N',  8, 2.0, 'step'),
                ('R', 'NE', 7, 3.0, 'step'),
                ('L', 'N',  6, 4.0, 'step'),
            ],
        },
        {
            'name': 'Three Step',
            'steps': [
                ('R', 'N', 8, 1.0, 'step'),
                ('L', 'N', 8, 2.0, 'step'),
                ('R', 'N', 8, 3.0, 'step'),
            ],
        },
    ],
    'salsa': [
        {
            'name': 'Basic',
            'steps': [
                ('L', 'N',  6, 1.0, 'step'),
                ('R', 'C',  0, 2.0, 'step'),
                ('L', 'C',  0, 3.0, 'close'),
                ('R', 'S',  6, 5.0, 'step'),
                ('L', 'C',  0, 6.0, 'step'),
                ('R', 'C',  0, 7.0, 'close'),
            ],
        },
        {
            'name': 'Cross Body Lead',
            'steps': [
                ('L', 'N',  6, 1.0, 'step'),
                ('R', 'C',  0, 2.0, 'step'),
                ('L', 'W',  5, 3.0, 'step'),
                ('R', 'S',  6, 5.0, 'step'),
                ('L', 'SE', 5, 6.0, 'step'),
                ('R', 'C',  0, 7.0, 'close'),
            ],
        },
    ],
    'swing': [
        {
            'name': 'East Coast Basic',
            'steps': [
                ('L', 'SW', 5, 1.0, 'step'),
                ('R', 'C',  0, 2.0, 'close'),
                ('R', 'SE', 5, 3.0, 'step'),
                ('L', 'C',  0, 4.0, 'close'),
                ('L', 'S',  4, 5.0, 'step'),
                ('R', 'S',  4, 6.0, 'step'),
            ],
        },
    ],
    'ballet': [
        {
            'name': 'Pas de Bourree',
            'steps': [
                ('R', 'E',  4, 1.0, 'step'),
                ('L', 'E',  3, 2.0, 'step'),
                ('R', 'E',  4, 3.0, 'step'),
            ],
        },
        {
            'name': 'Chasse',
            'steps': [
                ('R', 'E',  5, 1.0, 'step'),
                ('L', 'C',  0, 2.0, 'close'),
                ('R', 'E',  5, 3.0, 'step'),
                ('L', 'C',  0, 4.0, 'close'),
            ],
        },
    ],
    'flamenco': [
        {
            'name': 'Zapateado',
            'steps': [
                ('R', 'S',  3, 1.0, 'stamp'),
                ('L', 'S',  3, 2.0, 'stamp'),
                ('R', 'C',  0, 3.0, 'stamp'),
                ('L', 'C',  0, 3.5, 'stamp'),
                ('R', 'S',  3, 4.0, 'stamp'),
                ('L', 'C',  0, 4.5, 'stamp'),
            ],
        },
    ],
    'bharata': [
        {
            'name': 'Tat Adavu',
            'steps': [
                ('R', 'E',  6, 1.0, 'stamp'),
                ('L', 'C',  0, 2.0, 'stamp'),
                ('L', 'W',  6, 3.0, 'stamp'),
                ('R', 'C',  0, 4.0, 'stamp'),
            ],
        },
        {
            'name': 'Natta Adavu',
            'steps': [
                ('R', 'E',  7, 1.0, 'stamp'),
                ('L', 'E',  4, 2.0, 'tap'),
                ('L', 'W',  7, 3.0, 'stamp'),
                ('R', 'W',  4, 4.0, 'tap'),
            ],
        },
    ],
    'irish': [
        {
            'name': 'Threes',
            'steps': [
                ('R', 'E',  4, 1.0, 'step'),
                ('L', 'C',  0, 2.0, 'close'),
                ('R', 'E',  4, 3.0, 'step'),
                ('L', 'E',  4, 4.0, 'step'),
                ('R', 'C',  0, 5.0, 'close'),
                ('L', 'E',  4, 6.0, 'step'),
            ],
        },
        {
            'name': 'Sevens',
            'steps': [
                ('R', 'E', 3, 1.0, 'step'),
                ('L', 'E', 3, 2.0, 'step'),
                ('R', 'E', 3, 3.0, 'step'),
                ('L', 'E', 3, 4.0, 'step'),
                ('R', 'E', 3, 5.0, 'step'),
                ('L', 'E', 3, 6.0, 'step'),
                ('R', 'E', 3, 7.0, 'step'),
            ],
        },
    ],
    'samba': [
        {
            'name': 'Basic',
            'steps': [
                ('L', 'N',  5, 1.0, 'step'),
                ('R', 'C',  0, 1.5, 'close'),
                ('L', 'C',  0, 2.0, 'step'),
                ('R', 'S',  5, 1.0, 'step'),
                ('L', 'C',  0, 1.5, 'close'),
                ('R', 'C',  0, 2.0, 'step'),
            ],
        },
        {
            'name': 'Whisk',
            'steps': [
                ('L', 'N',  5, 1.0, 'step'),
                ('R', 'C',  0, 1.5, 'close'),
                ('L', 'SW', 5, 2.0, 'step'),
                ('R', 'S',  5, 1.0, 'step'),
                ('L', 'C',  0, 1.5, 'close'),
                ('R', 'SE', 5, 2.0, 'step'),
            ],
        },
    ],
    'capoeira': [
        {
            'name': 'Ginga',
            'steps': [
                ('L', 'SW', 6, 1.0, 'step'),
                ('R', 'C',  0, 2.0, 'step'),
                ('L', 'C',  0, 3.0, 'close'),
                ('R', 'SE', 6, 4.0, 'step'),
                ('L', 'C',  0, 5.0, 'step'),
                ('R', 'C',  0, 6.0, 'close'),
            ],
        },
    ],
    'hula': [
        {
            'name': 'Kaholo',
            'steps': [
                ('R', 'E', 5, 1.0, 'step'),
                ('L', 'E', 5, 2.0, 'step'),
                ('R', 'E', 5, 3.0, 'step'),
                ('L', 'C', 0, 4.0, 'close'),
                ('L', 'W', 5, 5.0, 'step'),
                ('R', 'W', 5, 6.0, 'step'),
                ('L', 'W', 5, 7.0, 'step'),
                ('R', 'C', 0, 8.0, 'close'),
            ],
        },
        {
            'name': 'Ami',
            'steps': [
                ('R', 'E',  4, 1.0, 'step'),
                ('L', 'SE', 4, 2.0, 'step'),
                ('R', 'S',  4, 3.0, 'step'),
                ('L', 'SW', 4, 4.0, 'step'),
                ('R', 'W',  4, 5.0, 'step'),
                ('L', 'NW', 4, 6.0, 'step'),
                ('R', 'N',  4, 7.0, 'step'),
                ('L', 'NE', 4, 8.0, 'step'),
            ],
        },
    ],
}


# ---------------------------------------------------------------------------
# Dance metadata
# ---------------------------------------------------------------------------
DANCE_META = {
    'waltz':    {'name': 'WALTZ',     'origin': 'Vienna',    'family': 'BALLROOM', 'tempo': 1.0,  'time_sig': '3/4', 'color': (180, 140, 255)},
    'tango':    {'name': 'TANGO',     'origin': 'Argentina', 'family': 'BALLROOM', 'tempo': 0.8,  'time_sig': '4/4', 'color': (255, 60, 60)},
    'foxtrot':  {'name': 'FOXTROT',   'origin': 'USA',       'family': 'BALLROOM', 'tempo': 0.9,  'time_sig': '4/4', 'color': (255, 200, 100)},
    'salsa':    {'name': 'SALSA',     'origin': 'Cuba',      'family': 'STREET',   'tempo': 1.2,  'time_sig': '4/4', 'color': (255, 100, 50)},
    'swing':    {'name': 'SWING',     'origin': 'USA',       'family': 'STREET',   'tempo': 1.2,  'time_sig': '4/4', 'color': (255, 220, 50)},
    'ballet':   {'name': 'BALLET',    'origin': 'France',    'family': 'CLASSICAL','tempo': 0.6,  'time_sig': '3/4', 'color': (200, 180, 255)},
    'flamenco': {'name': 'FLAMENCO',  'origin': 'Spain',     'family': 'FOLK',     'tempo': 1.1,  'time_sig': '3/4', 'color': (255, 80, 30)},
    'bharata':  {'name': 'BHARATA',   'origin': 'India',     'family': 'CLASSICAL','tempo': 0.7,  'time_sig': '4/4', 'color': (255, 180, 50)},
    'irish':    {'name': 'IRISH',     'origin': 'Ireland',   'family': 'FOLK',     'tempo': 1.3,  'time_sig': '4/4', 'color': (50, 200, 80)},
    'samba':    {'name': 'SAMBA',     'origin': 'Brazil',    'family': 'STREET',   'tempo': 1.4,  'time_sig': '2/4', 'color': (0, 200, 100)},
    'capoeira': {'name': 'CAPOEIRA',  'origin': 'Brazil',    'family': 'STREET',   'tempo': 1.0,  'time_sig': '4/4', 'color': (255, 200, 0)},
    'hula':     {'name': 'HULA',      'origin': 'Hawaii',    'family': 'FOLK',     'tempo': 0.6,  'time_sig': '4/4', 'color': (100, 200, 150)},
}


# ---------------------------------------------------------------------------
# Step processing
# ---------------------------------------------------------------------------

def process_figure(raw_steps):
    """Convert compass-direction steps to (foot, x, y, beat, action) tuples.

    Walk steps accumulating position. 'C' (close) moves to the other foot's
    last position.
    """
    # Track last known position for each foot
    pos = {'L': [0.0, 0.0], 'R': [0.0, 0.0]}
    results = []

    for foot, direction, dist, beat, action in raw_steps:
        other = 'L' if foot == 'R' else 'R'

        if direction == 'C':
            # Close: move to the other foot's position
            pos[foot] = list(pos[other])
        else:
            dx, dy = COMPASS[direction]
            pos[foot] = [pos[foot][0] + dx * dist,
                         pos[foot][1] + dy * dist]

        results.append({
            'foot': foot,
            'x': pos[foot][0],
            'y': pos[foot][1],
            'beat': beat,
            'action': action,
        })

    return results


def normalize_figure(steps, floor_w=44, floor_h=44):
    """Normalize step positions to fit within floor_w × floor_h pixels,
    centered. Returns steps with integer x, y."""
    if not steps:
        return steps

    xs = [s['x'] for s in steps]
    ys = [s['y'] for s in steps]

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    span_x = max_x - min_x
    span_y = max_y - min_y

    # Scale to fit, preserving aspect ratio
    if span_x == 0 and span_y == 0:
        scale = 1.0
    elif span_x == 0:
        scale = floor_h / span_y
    elif span_y == 0:
        scale = floor_w / span_x
    else:
        scale = min(floor_w / span_x, floor_h / span_y)

    # Don't scale up more than 3x (keeps small patterns small)
    scale = min(scale, 3.0)

    cx = (min_x + max_x) / 2.0
    cy = (min_y + max_y) / 2.0

    out = []
    for s in steps:
        out.append({
            'foot': s['foot'],
            'x': int(round((s['x'] - cx) * scale + floor_w / 2)),
            'y': int(round((s['y'] - cy) * scale + floor_h / 2)),
            'beat': s['beat'],
            'action': s['action'],
        })
    return out


def build_dance(dance_key):
    """Build complete dance data dict for one dance."""
    meta = DANCE_META[dance_key]
    raw_figures = FIGURES[dance_key]

    figures = []
    for fig in raw_figures:
        raw = process_figure(fig['steps'])
        norm = normalize_figure(raw)
        figures.append({
            'name': fig['name'],
            'steps': norm,
        })

    return {
        'name': meta['name'],
        'origin': meta['origin'],
        'family': meta['family'],
        'tempo': meta['tempo'],
        'time_sig': meta['time_sig'],
        'color': meta['color'],
        'figures': figures,
    }


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def format_dance(data):
    """Format a dance dict as a Python literal for pasting into dance.py."""
    lines = []
    lines.append('    {')
    lines.append(f"        'name': {data['name']!r}, "
                 f"'origin': {data['origin']!r}, "
                 f"'family': {data['family']!r},")
    lines.append(f"        'tempo': {data['tempo']}, "
                 f"'time_sig': {data['time_sig']!r}, "
                 f"'color': {data['color']!r},")
    lines.append("        'figures': [")
    for fig in data['figures']:
        lines.append(f"            {{'name': {fig['name']!r}, 'steps': [")
        for s in fig['steps']:
            lines.append(
                f"                {{'foot': {s['foot']!r}, "
                f"'x': {s['x']}, 'y': {s['y']}, "
                f"'beat': {s['beat']}, 'action': {s['action']!r}}},"
            )
        lines.append("            ]},")
    lines.append("        ],")
    lines.append('    },')
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

# Canonical order for output
DANCE_ORDER = [
    'waltz', 'tango', 'foxtrot',       # Ballroom
    'salsa', 'swing', 'samba', 'capoeira',  # Street
    'ballet', 'bharata',                # Classical
    'flamenco', 'irish', 'hula',        # Folk
]


def main():
    args = sys.argv[1:]

    if not args or '--help' in args or '-h' in args:
        print(__doc__)
        return

    if '--list' in args:
        for key in DANCE_ORDER:
            m = DANCE_META[key]
            figs = FIGURES[key]
            fig_names = ', '.join(f['name'] for f in figs)
            eprint(f"  {m['name']:12s}  {m['family']:10s}  "
                   f"{len(figs)} figure(s): {fig_names}")
        return

    targets = args
    if 'all' in targets:
        targets = DANCE_ORDER

    print("DANCES = [")
    for key in targets:
        if key not in DANCE_META:
            eprint(f"Unknown dance: {key}")
            continue
        eprint(f"Processing {key}...")
        data = build_dance(key)
        print(format_dance(data))

        # Summary to stderr
        for fig in data['figures']:
            eprint(f"  {fig['name']}: {len(fig['steps'])} steps")
            for s in fig['steps']:
                eprint(f"    {s['foot']} ({s['x']:3d},{s['y']:3d}) "
                       f"beat={s['beat']} {s['action']}")
    print("]")


if __name__ == '__main__':
    main()
