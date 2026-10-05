#!/usr/bin/env python3
"""
yoga_sheet.py — Contact sheet + proportion lint for the YOGA poses
==================================================================
The poses in visuals/yoga.py are hand-placed pixel coordinates. This renders
every pose through the real Yoga.draw() onto one PNG, and checks each bone
against its length in Mountain: a bone may be shorter (foreshortened toward the
viewer) but not much longer, which means the pose was drawn at the wrong scale.

Usage:
  python3 tools/yoga_sheet.py                 # all poses -> tools/yoga_sheet.png
  python3 tools/yoga_sheet.py Plank Cobra     # just these
  python3 tools/yoga_sheet.py -o /tmp/x.png

Exits 1 if any pose fails the lint.
"""

import argparse
import math
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from PIL import Image

from arcade import Display, GRID_SIZE
from visuals import yoga

REFERENCE = 'Mountain'
# Limbs and torso keep their length when they turn; anything past this is a
# scale error. The pixel slack is for rounding, which is a big fraction of a
# 7px forearm. Shoulder and hip width are left out: Mountain is drawn narrow,
# and the wide-stance poses legitimately spread them.
MAX_STRETCH = 1.25
SLACK_PX = 2
LINT_BONES = [
    ('l_shoulder', 'l_elbow'), ('l_elbow', 'l_hand'),
    ('r_shoulder', 'r_elbow'), ('r_elbow', 'r_hand'),
    ('l_hip', 'l_knee'), ('l_knee', 'l_foot'),
    ('r_hip', 'r_knee'), ('r_knee', 'r_foot'),
    ('neck', 'l_hip'), ('neck', 'r_hip'),
]
FLOOR_Y = 56          # where Mountain's feet stand
HEAD_RADIUS = 2

SCALE = 4
COLUMNS = 5
GAP = 4


def _length(pose, a, b):
    return math.dist(pose[a], pose[b])


def lint(name, pose):
    """Return a list of problems with one pose (empty = clean)."""
    problems = []
    ref = yoga.POSES[REFERENCE]
    for a, b in LINT_BONES:
        length, ref_length = _length(pose, a, b), _length(ref, a, b)
        if length > ref_length * MAX_STRETCH + SLACK_PX:
            problems.append(f'{a}-{b} is {length:.0f}px, {ref_length:.0f}px in {REFERENCE}')
    for joint, (x, y) in pose.items():
        margin = HEAD_RADIUS if joint == 'head' else 0
        if not (margin <= x < GRID_SIZE - margin and margin <= y < GRID_SIZE - margin):
            problems.append(f'{joint} at ({x},{y}) is off the panel')
    lowest = max(y for joint, (x, y) in pose.items())
    if abs(lowest - FLOOR_Y) > 2:
        problems.append(f'lowest joint is at y={lowest}, floor is y={FLOOR_Y}')
    if len(name) > 15:
        problems.append(f'name is {len(name)} chars, only 15 fit on the panel')
    return problems


def render(display, name):
    """Draw one pose with the real visual; return it as a 64x64 PIL image."""
    yoga.FLOWS = [('SHEET', [(name, 1.0)])]
    visual = yoga.Yoga(display)
    visual.draw()
    img = Image.new('RGB', (GRID_SIZE, GRID_SIZE))
    img.putdata([px for row in display.buffer for px in row])
    return img


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    ap.add_argument('poses', nargs='*', help='pose names (default: all)')
    ap.add_argument('-o', '--out', default=os.path.join(ROOT, 'tools', 'yoga_sheet.png'))
    args = ap.parse_args()

    names = args.poses or list(yoga.POSES)
    unknown = [n for n in names if n not in yoga.POSES]
    if unknown:
        sys.exit(f'unknown pose(s): {", ".join(unknown)}')

    display = Display()
    cell = GRID_SIZE * SCALE
    cols = min(COLUMNS, len(names))
    rows = math.ceil(len(names) / cols)
    sheet = Image.new('RGB', (cols * (cell + GAP) + GAP, rows * (cell + GAP) + GAP),
                      (60, 60, 60))
    failed = 0
    for i, name in enumerate(names):
        tile = render(display, name).resize((cell, cell), Image.NEAREST)
        sheet.paste(tile, (GAP + (i % cols) * (cell + GAP),
                           GAP + (i // cols) * (cell + GAP)))
        problems = lint(name, yoga.POSES[name])
        failed += bool(problems)
        print(f'{"FAIL" if problems else "ok  "} {name}')
        for p in problems:
            print(f'       {p}')

    sheet.save(args.out)
    print(f'\n{len(names)} poses -> {args.out}')
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
