#!/usr/bin/env python3
"""
build_walk.py — Generate movement cycle frames from biomechanical models
========================================================================
Generates clean motion cycles with 14 joints based on human gait and
movement biomechanics. Outputs frame data for visuals/walk.py (MOVE visual).

Movements: WALK, RUN, SNEAK, MARCH, IDLE

Usage:
  python3 tools/build_walk.py              # All movements
  python3 tools/build_walk.py walk         # Single movement
  python3 tools/build_walk.py --debug      # With diagnostics
"""

import math
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
    'MARCH': {
        'n_frames': 40,
        'hip_swing': 45,        # Thigh lifts high in front
        'hip_bias': 2,          # Very upright
        'knee_stance_peak': 3,  # Locked straight on stance
        'knee_swing_peak': 0,   # Unused — march uses special knee logic
        'arm_swing': 35,        # Crisp arm pump
        'elbow_base': 80,       # Arms at sharp right angles
        'elbow_swing': 5,
        'bounce': 0.005,        # Minimal bounce (stiff gait)
        'sway': 0.004,          # Minimal sway
        'crouch': 0.0,
        'march': True,          # Special: shin hangs vertical on lift
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
    is_march = params.get('march', False)
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
        elif is_march:
            # March: thigh lifts high, shin hangs vertical, stance leg straight
            r_hip_deg = params['hip_swing'] * _cos(phase) + params['hip_bias']
            l_hip_deg = params['hip_swing'] * _cos(phase + 0.5) + params['hip_bias']
            r_hip_angle = math.radians(r_hip_deg)
            l_hip_angle = math.radians(l_hip_deg)

            # Knee tracks hip angle when leg is forward (shin stays vertical)
            # When leg is behind or neutral, knee is nearly locked straight
            def march_knee(hip_deg):
                if hip_deg > 5:
                    return math.radians(hip_deg * 0.92)
                else:
                    return math.radians(params['knee_stance_peak'])

            r_knee_angle = march_knee(r_hip_deg)
            l_knee_angle = march_knee(l_hip_deg)

            r_arm_angle = math.radians(-params['arm_swing'] * _sin(phase))
            l_arm_angle = math.radians(-params['arm_swing']
                                        * _sin(phase + 0.5))
            r_elbow_flex = math.radians(params['elbow_base'])
            l_elbow_flex = math.radians(params['elbow_base'])
        else:
            # Gait cycle
            r_hip_angle = math.radians(
                params['hip_swing'] * _cos(phase) + params['hip_bias'])
            l_hip_angle = math.radians(
                params['hip_swing'] * _cos(phase + 0.5) + params['hip_bias'])

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

            r_knee_angle = knee_flex(r_knee_base,
                                      params['knee_stance_peak'],
                                      params['knee_swing_peak'])
            l_knee_angle = knee_flex(l_knee_base,
                                      params['knee_stance_peak'],
                                      params['knee_swing_peak'])

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
        r_hip = (cx + HIP_HALF_W, HIP_Y + bounce + crouch)
        l_hip = (cx - HIP_HALF_W, HIP_Y + bounce + crouch)

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

        r_shoulder = (cx + SHOULDER_HALF_W, SHOULDER_Y + bounce + crouch)
        l_shoulder = (cx - SHOULDER_HALF_W, SHOULDER_Y + bounce + crouch)

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
        frames.append(frame)

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


def main():
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
