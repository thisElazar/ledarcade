#!/usr/bin/env python3
"""
build_exercise.py — Bake the EXERCISE and WALL cycles for visuals/walk.py
==========================================================================
These don't fit the gait model in build_walk.py, so each one is a short
loop of hand-placed key poses (same 14-joint rig and scale as the YOGA poses,
some borrowed from there). This eases between the keys and writes the frames
into visuals/walk.py.

Usage:
  python3 tools/build_exercise.py            # lint the key poses, report
  python3 tools/build_exercise.py --write    # ...and re-bake visuals/walk.py
"""

import math
import os
import re
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from visuals.yoga import POSES as YOGA, JOINT_NAMES, _ease
from yoga_sheet import lint

WALK_PY = os.path.join(ROOT, 'visuals', 'walk.py')
_BLOCK = re.compile(r'(# BEGIN EXERCISE FRAMES\n).*?(# END EXERCISE FRAMES\n)', re.S)


def _pose(head, neck, shoulder, elbow, hand, hip, knee, foot):
    """Build a pose. A limb joint is either an (l, r) pair of points or, for a
    figure seen side-on, one point: the far side is drawn 1px behind it."""
    pose = {'head': head, 'neck': neck}
    for name, value in (('shoulder', shoulder), ('elbow', elbow), ('hand', hand),
                        ('hip', hip), ('knee', knee), ('foot', foot)):
        if isinstance(value[0], int):
            value = (value, (value[0] - 1, value[1]))
        pose['l_' + name], pose['r_' + name] = value
    return pose


# ── Key poses (pixel coords on the 64x64 grid, floor at y=56) ─────
POSES = {
    # Facing the viewer
    'Stand': YOGA['Mountain'],
    'Reach': YOGA['Upward Salute'],
    'Fold': YOGA['Forward Fold'],
    'Jack': _pose((32, 11), (32, 14), ((28, 17), (36, 17)), ((22, 11), (42, 11)),
                  ((19, 5), (45, 5)), ((29, 32), (35, 32)), ((26, 44), (38, 44)),
                  ((22, 56), (42, 56))),
    # Side-on, facing right
    'Side Stand': _pose((33, 10), (32, 13), (32, 16), (32, 24), (33, 31),
                        (32, 31), (33, 43), (32, 56)),
    'Hips Stand': _pose((33, 10), (32, 13), (32, 16), (28, 23), (32, 29),
                        (32, 31), (33, 43), (32, 56)),
    'Jump': _pose((33, 10), (32, 13), (32, 16), (37, 10), (42, 5),
                  (32, 31), (33, 43), (32, 56)),
    'Squat': _pose((40, 30), (38, 32), (37, 35), (45, 35), (52, 35),
                   (28, 47), (40, 46), (32, 56)),
    'Crouch': _pose((47, 37), (44, 39), (44, 42), (45, 49), (47, 56),
                    (30, 50), (41, 47), (32, 56)),
    'Plank': YOGA['Plank'],
    'Push Low': _pose((52, 50), (49, 52), (49, 52), (44, 51), (49, 56),
                      (32, 54), (21, 55), (9, 56)),
    'Climb A': _pose((52, 39), (49, 41), (49, 41), (49, 49), (49, 56), (32, 47),
                     ((43, 51), (20, 51)), ((31, 56), (8, 56))),
    'Climb B': _pose((52, 39), (49, 41), (49, 41), (49, 49), (49, 56), (32, 47),
                     ((20, 51), (43, 51)), ((8, 56), (31, 56))),
    'Sit Down': _pose((11, 54), (15, 55), (18, 55), (16, 48), (12, 53),
                      (33, 55), (39, 45), (46, 56)),
    'Sit Up': _pose((37, 34), (36, 37), (36, 40), (31, 35), (35, 33),
                    (33, 55), (39, 45), (46, 56)),
    'Lunge A': _pose((33, 22), (32, 25), (32, 28), (28, 35), (32, 41), (32, 43),
                     ((44, 43), (27, 54)), ((44, 56), (14, 56))),
    'Lunge B': _pose((33, 22), (32, 25), (32, 28), (28, 35), (32, 41), (32, 43),
                     ((27, 54), (44, 43)), ((14, 56), (44, 56))),
}

# Against a wall. Where the wall stands for each move is WALLS in visuals/walk.py:
# a side-on wall at x=21-22 for the first group, at x=5-6 for the second.
POSES.update({
    'Wall Stand': _pose((25, 11), (24, 14), (24, 17), (24, 25), (25, 32),
                        (24, 32), (29, 44), (34, 56)),
    'Wall Sit': _pose((25, 23), (24, 26), (24, 29), (27, 36), (33, 41),
                      (24, 44), (36, 44), (36, 56)),
    'Wall Sit Low': _pose((25, 24), (24, 27), (24, 30), (27, 37), (33, 42),
                          (24, 45), (36, 45), (36, 56)),
    # Leaning back on it, one foot up flat on the wall
    'Lean': _pose((25, 11), (24, 14), (24, 17), (27, 24), (32, 21), (26, 32),
                  ((30, 44), (35, 39)), ((33, 56), (23, 45))),
    'Lean Look': _pose((26, 11), (24, 14), (24, 17), (27, 24), (33, 18), (26, 32),
                       ((30, 44), (35, 39)), ((33, 56), (23, 45))),
    # Facing it: a standing push-up
    'Wall Push Far': _pose((37, 11), (38, 14), (39, 17), (31, 18), (23, 19),
                           (42, 32), (45, 44), (48, 56)),
    'Wall Push Near': _pose((28, 14), (29, 17), (30, 20), (27, 26), (23, 19),
                            (37, 34), (43, 45), (48, 56)),

    # Trying to push it over, feet slipping
    'Shove A': _pose((18, 31), (21, 33), (21, 33), (14, 32), (7, 31), (35, 45),
                     ((24, 50), (46, 50)), ((34, 56), (57, 56))),
    'Shove B': _pose((18, 32), (21, 34), (21, 34), (14, 33), (7, 31), (35, 46),
                     ((46, 51), (24, 51)), ((57, 56), (34, 56))),
    # Run at it, plant a foot, kick off
    'Wall Jump Ready': _pose((30, 29), (33, 31), (34, 34), (40, 38), (46, 41),
                             (44, 45), (33, 48), (40, 56)),
    'Wall Jump Plant': _pose((21, 10), (22, 13), (22, 16), (16, 13), (10, 10), (18, 30),
                             ((10, 23), (22, 41)), ((8, 34), (26, 53))),
    'Wall Jump Fly': _pose((38, 7), (38, 10), (38, 13), (42, 7), (47, 3),
                           (36, 28), (28, 36), (20, 44)),
    # At a corner (x=46), leaning out to look round it
    'Peek': _pose((47, 14), (43, 16), ((38, 17), (46, 20)), ((32, 23), (49, 27)),
                  ((27, 29), (46, 33)), ((29, 32), (35, 32)),
                  ((29, 44), (35, 44)), ((29, 56), (35, 56))),
})

# Key poses that are meant to be off the floor.
AIRBORNE = {'Wall Jump Plant', 'Wall Jump Fly'}


def _sidle(x, feet, knees):
    """Facing out, back and palms flat to the wall behind, centred on x."""
    return _pose((x, 11), (x, 14), ((x - 4, 17), (x + 4, 17)),
                 ((x - 9, 23), (x + 9, 23)), ((x - 12, 30), (x + 12, 30)),
                 ((x - 3, 32), (x + 3, 32)), ((x - knees, 44), (x + knees, 44)),
                 ((x - feet, 56), (x + feet, 56)))


# A sidle step: feet together at x, lead foot out (centre moves 3px), trail
# foot closes at x+6. Four steps across the panel and four back.
SIDLE_XS = [20, 26, 32, 38, 44]
for _x in SIDLE_XS:
    POSES[f'Sidle {_x}'] = _sidle(_x, 3, 3)
for _x in SIDLE_XS[:-1]:
    POSES[f'Sidle {_x + 3}'] = _sidle(_x + 3, 6, 5)
_sidle_path = [x for a in SIDLE_XS[:-1] for x in (a, a + 3)]
_sidle_steps = ([(f'Sidle {x}', 2, 6, 0) for x in _sidle_path]
                + [(f'Sidle {SIDLE_XS[-1]}', 10, 6, 0)]
                + [(f'Sidle {x}', 2, 6, 0) for x in reversed(_sidle_path[1:])]
                + [(f'Sidle {SIDLE_XS[0]}', 10, 6, 0)])
_sidle_steps = [_sidle_steps[-1]] + _sidle_steps[:-1]

# ── Exercises: a loop of (pose, hold, move, hop) ──────────────────
# hold = frames spent in the pose, move = frames easing to the next one,
# hop = pixels the body leaves the floor by at the middle of that move.
# Played at 30 fps. Names are drawn with the speed after them: 10 chars max.
EXERCISES = {
    'JUMP JACKS': [('Stand', 3, 11, 3), ('Jack', 3, 11, 3)],
    'SQUAT': [('Side Stand', 6, 16, 0), ('Squat', 6, 16, 0)],
    'PUSH-UP': [('Plank', 5, 18, 0), ('Push Low', 3, 18, 0)],
    'CLIMBER': [('Climb A', 1, 8, 0), ('Climb B', 1, 8, 0)],   # Mountain climber
    'SIT-UP': [('Sit Down', 5, 16, 0), ('Sit Up', 4, 16, 0)],
    'LUNGE': [('Hips Stand', 4, 14, 0), ('Lunge A', 6, 14, 0),
              ('Hips Stand', 4, 14, 0), ('Lunge B', 6, 14, 0)],
    'TOE TOUCH': [('Reach', 5, 16, 0), ('Fold', 5, 16, 0)],
    'BURPEE': [('Side Stand', 6, 12, 0), ('Crouch', 3, 10, 0), ('Plank', 6, 10, 0),
               ('Crouch', 3, 10, 0), ('Jump', 1, 14, 6)],
    # WALL category
    'SIDLE': _sidle_steps,
    'PEEK': [('Sidle 20', 8, 6, 0), ('Sidle 23', 2, 6, 0), ('Sidle 26', 2, 6, 0),
             ('Sidle 29', 2, 6, 0), ('Sidle 32', 8, 8, 0), ('Peek', 30, 5, 0),
             ('Sidle 32', 14, 8, 0), ('Peek', 16, 5, 0), ('Sidle 32', 4, 6, 0),
             ('Sidle 29', 2, 6, 0), ('Sidle 26', 2, 6, 0), ('Sidle 23', 2, 6, 0)],
    'WALL SIT': ([('Wall Stand', 12, 24, 0)]
                 + [('Wall Sit', 6, 3, 0), ('Wall Sit Low', 6, 3, 0)] * 4
                 + [('Wall Sit', 4, 24, 0)]),
    'LEAN': [('Lean', 60, 10, 0), ('Lean Look', 25, 10, 0)],
    'WALL PUSH': [('Wall Push Far', 5, 16, 0), ('Wall Push Near', 3, 16, 0)],
    'SHOVE': [('Shove A', 4, 10, 0), ('Shove B', 4, 10, 0)],
    'WALL JUMP': [('Wall Jump Ready', 10, 10, 0), ('Wall Jump Plant', 2, 9, 0),
                  ('Wall Jump Fly', 1, 10, 0)],
}


def bake(steps):
    """Expand a loop of key poses into frames."""
    frames = []
    for i, (name, hold, move, hop) in enumerate(steps):
        a = POSES[name]
        b = POSES[steps[(i + 1) % len(steps)][0]]
        frames.extend([dict(a)] * hold)
        for k in range(1, move):
            t = _ease(k / move)
            lift = hop * math.sin(math.pi * k / move)
            frames.append({j: (a[j][0] + (b[j][0] - a[j][0]) * t,
                               a[j][1] + (b[j][1] - a[j][1]) * t - lift)
                           for j in JOINT_NAMES})
    return frames


def var_name(exercise):
    return re.sub(r'\W', '_', exercise) + '_FRAMES'


def format_frames(exercise, frames):
    lines = [f'{var_name(exercise)} = [']
    for f in frames:
        parts = [f"'{j}':({round(f[j][0])},{round(f[j][1])})" for j in JOINT_NAMES]
        lines.append('    {' + ', '.join(parts) + '},')
    lines.append(']')
    return '\n'.join(lines) + '\n'


def main():
    failed = False
    for name, pose in POSES.items():
        for problem in lint(name, pose):
            if name in AIRBORNE and problem.startswith('lowest joint'):
                continue
            failed = True
            print(f'FAIL {name}: {problem}')
    for exercise in EXERCISES:
        if len(exercise) > 10:
            failed = True
            print(f'FAIL {exercise}: name is over 10 chars')
    if failed:
        sys.exit(1)

    chunks = []
    for exercise, steps in EXERCISES.items():
        frames = bake(steps)
        chunks.append(format_frames(exercise, frames))
        print(f'{exercise:10s} {len(frames):3d} frames ({len(frames) / 30:.1f}s)')

    if '--write' in sys.argv:
        with open(WALK_PY) as f:
            src = f.read()
        new, count = _BLOCK.subn(lambda m: m.group(1) + ''.join(chunks) + m.group(2), src)
        assert count == 1, 'exercise frame markers not found in visuals/walk.py'
        with open(WALK_PY, 'w') as f:
            f.write(new)
        print(f'Wrote {len(chunks)} exercises to {WALK_PY}')


if __name__ == '__main__':
    main()
