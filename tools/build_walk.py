#!/usr/bin/env python3
"""
build_walk.py — Generate movement cycle frames from biomechanical models
========================================================================
Generates clean motion cycles with 14 joints based on human gait and
movement biomechanics. Outputs frame data for visuals/walk.py (MOVE visual).

Movements: see MOVEMENTS below (IDLE is generated but not shown in the visual).

Usage:
  python3 tools/build_walk.py              # All movements, printed
  python3 tools/build_walk.py walk         # Single movement
  python3 tools/build_walk.py --debug      # With diagnostics
  python3 tools/build_walk.py --write      # Re-bake the gait frames in visuals/walk.py
"""

import math
import os
import re
import sys
from functools import partial

eprint = partial(print, file=sys.stderr, flush=True)

# Output joint names
OUT_JOINTS = [
    'head', 'neck',
    'l_shoulder', 'r_shoulder',
    'l_elbow', 'r_elbow',
    'l_hand', 'r_hand',
    'l_hip', 'r_hip',
    'l_knee', 'r_knee',
    'l_foot', 'r_foot',
]

# Vitruvian proportions (fraction of total height = 8 head-lengths)
HEAD_CENTER = 1/16          # 0.0625
NECK_Y = 1/8                # 0.125
SHOULDER_Y = 3/16           # 0.1875
SHOULDER_HALF_W = 0.09
ELBOW_Y = 3/8               # 0.375
HAND_Y = 17/32              # 0.531
HIP_Y = 1/2                 # 0.5
HIP_HALF_W = 0.055
KNEE_Y = 3/4                # 0.75
FOOT_Y = 1.0

# Segment lengths (derived)
THIGH_LEN = KNEE_Y - HIP_Y      # 0.25
SHIN_LEN = FOOT_Y - KNEE_Y       # 0.25
UPPER_ARM_LEN = ELBOW_Y - SHOULDER_Y  # 0.1875
FOREARM_LEN = HAND_Y - ELBOW_Y   # 0.156


def _sin(phase):
    return math.sin(phase * 2 * math.pi)

def _cos(phase):
    return math.cos(phase * 2 * math.pi)


# ---------------------------------------------------------------------------
# Movement parameter sets
# ---------------------------------------------------------------------------
# Each movement is defined by a dict of parameters that control the gait.
# The same kinematic engine generates all of them.

MOVEMENTS = {
    'WALK': {
        'n_frames': 48,
        'hip_swing': 20,        # Hip flexion amplitude (degrees)
        'hip_bias': 5,          # Forward lean bias
        'knee_stance_peak': 15, # Stance phase knee flex
        'knee_swing_peak': 65,  # Swing phase knee flex peak
        'arm_swing': 18,        # Arm swing amplitude
        'elbow_base': 20,       # Base elbow flex
        'elbow_swing': 15,      # Additional elbow flex during back swing
        'bounce': 0.012,        # Vertical bounce amplitude
        'sway': 0.008,          # Lateral sway amplitude
        'crouch': 0.0,          # Crouch offset (lowers whole body)
    },
    'RUN': {
        'ground': True,
        'width': 0.15,          # Seen side-on
        'n_frames': 32,         # Faster cycle
        'hip_swing': 35,        # Bigger stride
        'hip_bias': 10,         # More forward lean
        'knee_stance_peak': 20,
        'knee_swing_peak': 90,  # High knee lift
        'arm_swing': 35,        # Vigorous pump
        'elbow_base': 45,       # Arms bent tighter
        'elbow_swing': 25,
        'bounce': 0.035,        # Much more bounce
        'sway': 0.005,          # Less sway (faster)
        'crouch': 0.0,
        'lean': 12,
        'air': 0.07,
    },
    'SNEAK': {
        'n_frames': 64,         # Slow, careful
        'hip_swing': 12,        # Short steps
        'hip_bias': 8,          # Slight lean
        'knee_stance_peak': 25, # Bent knees (crouching)
        'knee_swing_peak': 45,
        'arm_swing': 5,         # Arms barely move
        'elbow_base': 50,       # Arms held close, bent
        'elbow_swing': 5,
        'bounce': 0.004,        # Minimal bounce
        'sway': 0.003,
        'crouch': 0.04,         # Lowered stance
    },
    # Optional parameters (default 0 / off):
    #   lean     torso tilt toward the direction of travel (degrees)
    #   ground   plant the lower foot on the floor every frame, so the body
    #            rises and falls with the legs (bounce is then ignored)
    #   air      with ground: height of the flight phase between footfalls
    #   air_at   where in the stride the flight peaks: 0 = legs split (a run),
    #            0.25 = over the standing leg (a hop)
    #   l_leg    scales the left leg's swing and knee lift (<1 = stiff leg)
    #   reverse  play the cycle backwards
    #   width    scales shoulder and hip width; near 0 turns the body fully
    #            side-on, which a big forward knee or arm movement needs
    #   hip_lift a high-knee step: the knee rises in front by this many
    #            degrees of thigh and comes back down in one even beat, and
    #            the leg stands straight the rest of the time
    'JOG': {
        'ground': True,
        'width': 0.15,          # Seen side-on
        'n_frames': 40,
        'hip_swing': 26,
        'hip_bias': 7,
        'knee_stance_peak': 18,
        'knee_swing_peak': 75,
        'arm_swing': 24,
        'elbow_base': 70,       # Forearms carried level
        'elbow_swing': 10,
        'bounce': 0.02,
        'sway': 0.005,
        'crouch': 0.0,
        'lean': 6,
        'air': 0.04,
    },
    'SPRINT': {
        'ground': True,
        'width': 0.15,          # Seen side-on
        'n_frames': 24,
        'hip_swing': 42,        # Full stride
        'hip_bias': 12,
        'knee_stance_peak': 20,
        'knee_swing_peak': 110, # Heel to hip
        'arm_swing': 50,
        'elbow_base': 80,
        'elbow_swing': 15,
        'bounce': 0.02,
        'sway': 0.0,
        'crouch': 0.0,
        'lean': 22,
        'air': 0.11,
    },
    'MARCH': {
        'ground': True,
        'n_frames': 36,
        'hip_swing': 5,         # Barely any stride
        'hip_bias': 0,
        'knee_stance_peak': 0,
        'knee_swing_peak': 90,
        'hip_lift': 75,         # Thigh comes up level, shin hangs below it
        'width': 0.15,          # Seen side-on
        'arm_swing': -35,       # Negative: arm goes forward with the far knee
        'elbow_base': 8,
        'elbow_swing': 0,
        'bounce': 0.004,
        'sway': 0.0,
        'crouch': 0.0,
    },
    'HIGH_KNEES': {             # Shown under EXERCISE: a sprint-speed march
        'ground': True,
        'width': 0.15,          # Seen side-on
        'n_frames': 18,
        'hip_swing': 3,
        'hip_bias': 0,
        'knee_stance_peak': 0,
        'knee_swing_peak': 95,
        'hip_lift': 80,
        'arm_swing': -28,
        'elbow_base': 80,       # Arms pump, bent
        'elbow_swing': 0,
        'bounce': 0.0,
        'sway': 0.0,
        'crouch': 0.0,
        'lean': 4,
    },
    'TRUDGE': {
        'ground': True,
        'n_frames': 80,         # Slow and heavy
        'hip_swing': 11,
        'hip_bias': 6,
        'knee_stance_peak': 22,
        'knee_swing_peak': 35,
        'arm_swing': 4,         # Arms hang
        'elbow_base': 8,
        'elbow_swing': 0,
        'bounce': 0.006,
        'sway': 0.012,
        'crouch': 0.03,
        'lean': 24,
    },
    'SKIP': {
        'ground': True,
        'width': 0.15,          # Seen side-on
        'n_frames': 36,
        'hip_swing': 16,
        'hip_bias': 16,
        'knee_stance_peak': 8,
        'knee_swing_peak': 95,  # Knee drives up on every hop
        'arm_swing': 42,
        'elbow_base': 35,
        'elbow_swing': 20,
        'bounce': 0.02,
        'sway': 0.0,
        'crouch': 0.0,
        'air': 0.07,
        'air_at': 0.25,
    },
    'LIMP': {
        'ground': True,
        'n_frames': 60,
        'hip_swing': 16,
        'hip_bias': 4,
        'knee_stance_peak': 12,
        'knee_swing_peak': 60,
        'arm_swing': 12,
        'elbow_base': 25,
        'elbow_swing': 10,
        'bounce': 0.004,
        'sway': 0.01,
        'crouch': 0.0,
        'l_leg': 0.3,           # Left leg barely bends or swings
    },
    'MOONWALK': {
        'ground': True,
        'n_frames': 56,
        'hip_swing': 20,
        'hip_bias': 0,
        'knee_stance_peak': 0,
        'knee_swing_peak': 38,  # Low knee: the feet glide
        'arm_swing': 8,
        'elbow_base': 20,
        'elbow_swing': 5,
        'bounce': 0.0,
        'sway': 0.0,
        'crouch': 0.0,
        'lean': 5,
        'reverse': True,
    },
    'IDLE': {
        'n_frames': 60,         # Slow breathing cycle
        'hip_swing': 0,         # No walking
        'hip_bias': 2,          # Slight lean
        'knee_stance_peak': 5,  # Very slight flex
        'knee_swing_peak': 5,
        'arm_swing': 0,         # No arm swing
        'elbow_base': 15,       # Arms relaxed
        'elbow_swing': 0,
        'bounce': 0.008,        # Breathing motion
        'sway': 0.006,          # Weight shift
        'crouch': 0.0,
        'idle': True,           # Special: no gait cycle
    },
}


def generate_cycle(params):
    """Generate one motion cycle from parameter dict."""
    n = params['n_frames']
    is_idle = params.get('idle', False)
    lean = math.radians(params.get('lean', 0))
    air = params.get('air', 0.0)
    air_at = params.get('air_at', 0.0)
    l_leg = params.get('l_leg', 1.0)
    hip_lift = params.get('hip_lift', 0)
    width = params.get('width', 1.0)
    frames = []

    for i in range(n):
        phase = i / n

        # Lateral sway and vertical bounce
        cx = params['sway'] * _sin(phase * 2 if not is_idle else phase)
        bounce_freq = phase * 2 if not is_idle else phase
        bounce = -params['bounce'] * _cos(bounce_freq)
        crouch = params['crouch']

        if is_idle:
            # Idle: both legs slightly flexed, subtle weight shift
            r_hip_angle = math.radians(params['hip_bias'])
            l_hip_angle = math.radians(params['hip_bias'])
            r_knee_angle = math.radians(params['knee_stance_peak']
                                         + 3 * _sin(phase))
            l_knee_angle = math.radians(params['knee_stance_peak']
                                         + 3 * _sin(phase + 0.5))
            r_arm_angle = math.radians(2 * _sin(phase))
            l_arm_angle = math.radians(2 * _sin(phase + 0.5))
            r_elbow_flex = math.radians(params['elbow_base'])
            l_elbow_flex = math.radians(params['elbow_base'])
        else:
            # Gait cycle
            r_hip_angle = math.radians(
                params['hip_swing'] * _cos(phase) + params['hip_bias'])
            l_hip_angle = math.radians(
                params['hip_swing'] * l_leg * _cos(phase + 0.5)
                + params['hip_bias'])

            r_knee_base = phase
            l_knee_base = (phase + 0.5) % 1.0

            def knee_flex(p, stance_pk, swing_pk):
                if p < 0.15:
                    return math.radians(
                        stance_pk * math.sin(p / 0.15 * math.pi / 2))
                elif p < 0.40:
                    t = (p - 0.15) / 0.25
                    return math.radians(stance_pk * (1 - t) + 5 * t)
                elif p < 0.60:
                    t = (p - 0.40) / 0.20
                    return math.radians(5 + (swing_pk * 0.6) * t)
                elif p < 0.85:
                    t = (p - 0.60) / 0.25
                    return math.radians(
                        swing_pk * 0.6
                        + swing_pk * 0.4 * math.sin(t * math.pi / 2))
                else:
                    t = (p - 0.85) / 0.15
                    return math.radians(swing_pk * (1 - t) + 5 * t)

            if hip_lift:
                def knee_flex(p, stance_pk, swing_pk):
                    if not 0.55 < p < 0.95:
                        return 0.0
                    beat = math.sin(math.pi * (p - 0.55) / 0.4) ** 2
                    return math.radians(swing_pk) * beat

            r_knee_angle = knee_flex(r_knee_base,
                                      params['knee_stance_peak'],
                                      params['knee_swing_peak'])
            l_knee_angle = knee_flex(l_knee_base,
                                      params['knee_stance_peak'],
                                      params['knee_swing_peak'] * l_leg)

            if hip_lift:
                swing_pk = math.radians(params['knee_swing_peak'])
                r_hip_angle += math.radians(hip_lift) * r_knee_angle / swing_pk
                l_hip_angle += math.radians(hip_lift) * l_knee_angle / swing_pk

            r_arm_angle = math.radians(-params['arm_swing'] * _sin(phase))
            l_arm_angle = math.radians(-params['arm_swing']
                                        * _sin(phase + 0.5))

            r_elbow_flex = math.radians(
                params['elbow_base']
                + params['elbow_swing'] * max(0, _sin(phase)))
            l_elbow_flex = math.radians(
                params['elbow_base']
                + params['elbow_swing'] * max(0, _sin(phase + 0.5)))

        # --- Compute joint positions ---
        r_hip = (cx + HIP_HALF_W * width, HIP_Y + bounce + crouch)
        l_hip = (cx - HIP_HALF_W * width, HIP_Y + bounce + crouch)

        r_knee_x = r_hip[0] + THIGH_LEN * math.sin(r_hip_angle)
        r_knee_y = r_hip[1] + THIGH_LEN * math.cos(r_hip_angle)
        l_knee_x = l_hip[0] + THIGH_LEN * math.sin(l_hip_angle)
        l_knee_y = l_hip[1] + THIGH_LEN * math.cos(l_hip_angle)

        r_foot_x = r_knee_x + SHIN_LEN * math.sin(r_hip_angle - r_knee_angle)
        r_foot_y = r_knee_y + SHIN_LEN * math.cos(r_hip_angle - r_knee_angle)
        l_foot_x = l_knee_x + SHIN_LEN * math.sin(l_hip_angle - l_knee_angle)
        l_foot_y = l_knee_y + SHIN_LEN * math.cos(l_hip_angle - l_knee_angle)

        neck = (cx, NECK_Y + bounce + crouch)
        head = (cx, HEAD_CENTER + bounce + crouch)
        shoulder_c = (cx, SHOULDER_Y + bounce + crouch)
        if lean:
            # Tilt the spine about the hips; the shoulder bar stays level.
            hip_y = HIP_Y + bounce + crouch

            def tilt(point):
                up = hip_y - point[1]
                return (cx + up * math.sin(lean), hip_y - up * math.cos(lean))
            neck, head, shoulder_c = tilt(neck), tilt(head), tilt(shoulder_c)

        r_shoulder = (shoulder_c[0] + SHOULDER_HALF_W * width, shoulder_c[1])
        l_shoulder = (shoulder_c[0] - SHOULDER_HALF_W * width, shoulder_c[1])

        r_elbow_x = r_shoulder[0] + UPPER_ARM_LEN * math.sin(r_arm_angle)
        r_elbow_y = r_shoulder[1] + UPPER_ARM_LEN * math.cos(r_arm_angle)
        l_elbow_x = l_shoulder[0] + UPPER_ARM_LEN * math.sin(l_arm_angle)
        l_elbow_y = l_shoulder[1] + UPPER_ARM_LEN * math.cos(l_arm_angle)

        r_hand_x = r_elbow_x + FOREARM_LEN * math.sin(r_arm_angle + r_elbow_flex)
        r_hand_y = r_elbow_y + FOREARM_LEN * math.cos(r_arm_angle + r_elbow_flex)
        l_hand_x = l_elbow_x + FOREARM_LEN * math.sin(l_arm_angle + l_elbow_flex)
        l_hand_y = l_elbow_y + FOREARM_LEN * math.cos(l_arm_angle + l_elbow_flex)

        frame = {
            'head': head, 'neck': neck,
            'l_shoulder': l_shoulder, 'r_shoulder': r_shoulder,
            'l_elbow': (l_elbow_x, l_elbow_y),
            'r_elbow': (r_elbow_x, r_elbow_y),
            'l_hand': (l_hand_x, l_hand_y),
            'r_hand': (r_hand_x, r_hand_y),
            'l_hip': l_hip, 'r_hip': r_hip,
            'l_knee': (l_knee_x, l_knee_y),
            'r_knee': (r_knee_x, r_knee_y),
            'l_foot': (l_foot_x, l_foot_y),
            'r_foot': (r_foot_x, r_foot_y),
        }
        if params.get('ground'):
            lift = air * max(0.0, _cos((phase - air_at) * 2))
            dy = FOOT_Y - max(l_foot_y, r_foot_y) - lift
            frame = {j: (x, y + dy) for j, (x, y) in frame.items()}
        frames.append(frame)

    if params.get('reverse'):
        frames.reverse()
    return frames


def normalize_to_screen(frames, figure_height=48, center_x=32, top_y=8):
    """Scale normalized 0..1 coords to pixel positions on 64x64 screen."""
    result = []
    for f in frames:
        normed = {}
        for name, (x, y) in f.items():
            px = x * figure_height + center_x
            py = y * figure_height + top_y
            px = max(1.0, min(62.0, px))
            py = max(1.0, min(62.0, py))
            normed[name] = (px, py)
        result.append(normed)
    return result


def format_output(name, frames):
    """Format as Python literal for embedding."""
    var_name = f'{name}_FRAMES'
    lines = [f'{var_name} = [']
    for f in frames:
        parts = []
        for jname in OUT_JOINTS:
            x, y = f[jname]
            parts.append(f"'{jname}':({int(round(x))},{int(round(y))})")
        lines.append('    {' + ', '.join(parts) + '},')
    lines.append(']')
    return '\n'.join(lines)


def validate(name, frames):
    """Check that frames are sane."""
    for i, f in enumerate(frames):
        assert f['head'][1] < f['l_foot'][1], \
            f"{name} frame {i}: head below l_foot"
        assert f['head'][1] < f['r_foot'][1], \
            f"{name} frame {i}: head below r_foot"
        for jname, (x, y) in f.items():
            assert 1 <= x <= 62, f"{name} frame {i} {jname}: x={x} OOB"
            assert 1 <= y <= 62, f"{name} frame {i} {jname}: y={y} OOB"


# The cycles baked into visuals/walk.py, in the order they are written there.
BAKED = ['WALK', 'JOG', 'RUN', 'SPRINT', 'MARCH', 'SNEAK', 'TRUDGE', 'SKIP',
         'LIMP', 'MOONWALK', 'HIGH_KNEES']
WALK_PY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       'visuals', 'walk.py')
_GAIT_BLOCK = re.compile(r'(# BEGIN GAIT FRAMES\n).*?(# END GAIT FRAMES\n)', re.S)


def write_baked():
    """Replace the generated gait block in visuals/walk.py."""
    chunks = []
    for name in BAKED:
        frames = normalize_to_screen(generate_cycle(MOVEMENTS[name]))
        validate(name, frames)
        chunks.append(format_output(name, frames) + '\n')
    with open(WALK_PY) as f:
        src = f.read()
    new, count = _GAIT_BLOCK.subn(lambda m: m.group(1) + ''.join(chunks) + m.group(2), src)
    assert count == 1, 'gait frame markers not found in visuals/walk.py'
    with open(WALK_PY, 'w') as f:
        f.write(new)
    eprint(f"Wrote {len(BAKED)} cycles to {WALK_PY}")


def main():
    if '--write' in sys.argv:
        write_baked()
        return
    debug = '--debug' in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith('-')]

    targets = [a.upper() for a in args] if args else list(MOVEMENTS.keys())

    for name in targets:
        if name not in MOVEMENTS:
            eprint(f"Unknown movement: {name}")
            eprint(f"Available: {', '.join(MOVEMENTS.keys())}")
            continue

        params = MOVEMENTS[name]
        eprint(f"Generating {name} ({params['n_frames']} frames)...")
        frames = generate_cycle(params)
        frames = normalize_to_screen(frames)

        if debug:
            for i, f in enumerate(frames):
                eprint(f"  {i:2d}: head=({f['head'][0]:5.1f},{f['head'][1]:5.1f}) "
                       f"l_foot=({f['l_foot'][0]:5.1f},{f['l_foot'][1]:5.1f}) "
                       f"r_foot=({f['r_foot'][0]:5.1f},{f['r_foot'][1]:5.1f})")

        validate(name, frames)
        print(format_output(name, frames))
        print()
        eprint(f"  {name}: {len(frames)} frames, validated OK")

    eprint("Done!")


if __name__ == '__main__':
    main()
