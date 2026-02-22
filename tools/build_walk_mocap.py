#!/usr/bin/env python3
"""
build_walk_mocap.py — Extract walk cycle from real CMU motion capture data
=========================================================================
Downloads CMU Subject 35 (canonical gait subject), maps to our 14-joint rig,
and tests 4 processing methods side-by-side.

Methods:
  A) Raw projected — baseline, expect jitter
  B) Temporal smoothing — moving average + Savitzky-Golay
  C) Angle-space smoothing — smooth angles, reconstruct with Vitruvian proportions
  D) Multi-cycle average — average multiple gait cycles

Usage:
  python3 tools/build_walk_mocap.py              # All methods
  python3 tools/build_walk_mocap.py --method B   # Single method
  python3 tools/build_walk_mocap.py --debug      # Print diagnostics
  python3 tools/build_walk_mocap.py --compare    # Side-by-side stats vs procedural
"""

import math
import sys
from functools import partial

import numpy as np

# Reuse parsers and FK engine from build_dance.py
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from build_dance import (parse_asf, parse_amc, forward_kinematics_asf,
                         ensure_cache, CACHE_DIR, _download)
from build_walk import (normalize_to_screen, format_output, validate,
                        OUT_JOINTS, THIGH_LEN, SHIN_LEN, UPPER_ARM_LEN,
                        FOREARM_LEN, HEAD_CENTER, NECK_Y, SHOULDER_Y,
                        SHOULDER_HALF_W, HIP_Y, HIP_HALF_W)

eprint = partial(print, file=sys.stderr, flush=True)

# Defaults — CMU Subject 35 is most-cited walking subject in gait research
DEFAULT_SUBJECT = '35'
DEFAULT_CLIP = '35_01'   # normal walk

# CMU joint name → our 14-joint rig
# FK gives world_pos[joint_name] = END of that bone
_JOINT_MAP_DEFAULTS = {
    'head':       'head',         # end of head bone
    'neck':       'lowerneck',    # end of lowerneck
    'l_shoulder': 'lclavicle',    # end of clavicle = shoulder joint
    'r_shoulder': 'rclavicle',
    'l_elbow':    'lhumerus',     # end of humerus = elbow
    'r_elbow':    'rhumerus',
    'l_hand':     'lwrist',       # end of wrist = hand position
    'r_hand':     'rwrist',
    'l_hip':      'lhipjoint',    # end of hipjoint = hip socket
    'r_hip':      'rhipjoint',
    'l_knee':     'lfemur',       # end of femur = knee
    'r_knee':     'rfemur',
    'l_foot':     'lfoot',        # end of foot bone ≈ ground contact
    'r_foot':     'rfoot',
}
JOINT_MAP = dict(_JOINT_MAP_DEFAULTS)


# ---------------------------------------------------------------------------
# Step 1: Extract 14 joints from FK world positions
# ---------------------------------------------------------------------------

def extract_14_joints_3d(world_pos):
    """Map CMU FK positions to our 14-joint dict with full 3D coords.
    Returns dict {joint_name: (x, y, z)} or None if required joints missing."""
    result = {}
    for our_name, cmu_name in JOINT_MAP.items():
        if cmu_name not in world_pos:
            return None
        pos = world_pos[cmu_name]
        result[our_name] = (pos[0], pos[1], pos[2])
    return result


def extract_all_frames(bones, hierarchy, root_order, length_scale, amc_frames):
    """Run FK on every AMC frame, project to 2D with body-relative axes.
    Spine direction = screen vertical (always upright).
    Shoulder direction = screen horizontal, smoothed with heavy EMA so
    slow rotations are visible but fast turns don't cause jitter.
    Returns list of dicts {joint: (x, y_up)}."""
    # First pass: collect 3D joints and per-frame body axes
    all_3d = []
    raw_right_angles = []  # angle of shoulder direction in XZ plane
    for fdata in amc_frames:
        world = forward_kinematics_asf(bones, hierarchy, root_order,
                                       length_scale, fdata)
        joints_3d = extract_14_joints_3d(world)
        if joints_3d is None:
            continue
        all_3d.append(joints_3d)

        # Compute shoulder direction angle in XZ plane
        head = joints_3d['head']
        hip_mid = tuple((joints_3d['l_hip'][i] + joints_3d['r_hip'][i]) / 2
                        for i in range(3))
        spine = tuple(head[i] - hip_mid[i] for i in range(3))
        spine_len = math.sqrt(sum(s * s for s in spine))
        if spine_len < 1e-6:
            spine = (0, 1, 0)
            spine_len = 1.0
        up = tuple(s / spine_len for s in spine)

        ls = joints_3d['l_shoulder']
        rs = joints_3d['r_shoulder']
        shoulder = tuple(ls[i] - rs[i] for i in range(3))
        # Remove spine component
        dot = sum(shoulder[i] * up[i] for i in range(3))
        right = [shoulder[i] - dot * up[i] for i in range(3)]
        angle = math.atan2(right[2], right[0])
        raw_right_angles.append(angle)

    if not all_3d:
        return []

    # Unwrap and smooth the shoulder angle (heavy EMA, ~2s at 120fps)
    unwrapped = [raw_right_angles[0]]
    for i in range(1, len(raw_right_angles)):
        diff = raw_right_angles[i] - raw_right_angles[i - 1]
        while diff > math.pi:
            diff -= 2 * math.pi
        while diff < -math.pi:
            diff += 2 * math.pi
        unwrapped.append(unwrapped[-1] + diff)

    # Forward-backward EMA: smooth forward, smooth backward, average.
    # Eliminates phase lag while giving very strong smoothing.
    alpha = 1.0 / 360.0  # ~3 second time constant at 120fps
    fwd = [unwrapped[0]]
    for i in range(1, len(unwrapped)):
        fwd.append(fwd[-1] + alpha * (unwrapped[i] - fwd[-1]))
    bwd = [unwrapped[-1]]
    for i in range(len(unwrapped) - 2, -1, -1):
        bwd.append(bwd[-1] + alpha * (unwrapped[i] - bwd[-1]))
    bwd.reverse()
    smoothed = [(f + b) / 2 for f, b in zip(fwd, bwd)]

    eprint(f"  Projection: spine-up + smoothed shoulder "
           f"(rotation range {math.degrees(max(smoothed) - min(smoothed)):.0f} deg)")

    # Second pass: project each frame with per-frame spine, smoothed horizontal
    frames = []
    for i, joints_3d in enumerate(all_3d):
        head = joints_3d['head']
        hip_mid = tuple((joints_3d['l_hip'][i2] + joints_3d['r_hip'][i2]) / 2
                        for i2 in range(3))
        spine = tuple(head[i2] - hip_mid[i2] for i2 in range(3))
        spine_len = math.sqrt(sum(s * s for s in spine))
        if spine_len < 1e-6:
            continue
        up = tuple(s / spine_len for s in spine)

        # Smoothed horizontal direction
        a = smoothed[i]
        raw_right = (math.cos(a), 0.0, math.sin(a))

        # Orthogonalize: remove spine component from right
        dot = sum(raw_right[j] * up[j] for j in range(3))
        right = [raw_right[j] - dot * up[j] for j in range(3)]
        rlen = math.sqrt(sum(r * r for r in right))
        if rlen < 1e-6:
            right = [up[2], 0.0, -up[0]]
            rlen = math.sqrt(sum(r * r for r in right))
            if rlen < 1e-6:
                right = [1.0, 0.0, 0.0]
                rlen = 1.0
        right = tuple(r / rlen for r in right)

        result = {}
        for name, (px, py, pz) in joints_3d.items():
            rx = px - hip_mid[0]
            ry = py - hip_mid[1]
            rz = pz - hip_mid[2]
            h = rx * right[0] + ry * right[1] + rz * right[2]
            v = rx * up[0] + ry * up[1] + rz * up[2]
            result[name] = (h, v)
        frames.append(result)

    return frames


# ---------------------------------------------------------------------------
# Step 2: Treadmill mode — remove root drift
# ---------------------------------------------------------------------------

def treadmill(frames):
    """Subtract root X translation so figure walks in place. Center at X=0."""
    result = []
    for f in frames:
        # Use hip midpoint as root X reference
        root_x = (f['l_hip'][0] + f['r_hip'][0]) / 2
        shifted = {}
        for name, (x, y) in f.items():
            shifted[name] = (x - root_x, y)
        result.append(shifted)
    return result


# ---------------------------------------------------------------------------
# Step 3: Cycle detection via autocorrelation
# ---------------------------------------------------------------------------

def _autocorr_peak(signal, min_lag, max_lag, threshold=0.3):
    """Find strongest autocorrelation peak in a 1-D signal.
    Returns (lag, strength) or None."""
    signal = signal - np.mean(signal)
    n = len(signal)
    if n < max_lag:
        return None

    autocorr = np.correlate(signal, signal, mode='full')
    autocorr = autocorr[n - 1:]  # positive lags only
    if autocorr[0] < 1e-10:
        return None
    autocorr = autocorr / autocorr[0]

    best = None
    for i in range(min_lag, min(max_lag, len(autocorr) - 1)):
        if autocorr[i] > autocorr[i - 1] and autocorr[i] > autocorr[i + 1]:
            if autocorr[i] > threshold:
                if best is None or autocorr[i] > best[1]:
                    best = (i, autocorr[i])
                    break  # first strong peak is most likely fundamental
    return best


def detect_cycle(frames, fps=120):
    """Detect cycle length by trying multiple joint signals.
    Tests foot X (walking), hip Y (bouncing), shoulder X (torso rotation),
    and picks the signal with the strongest autocorrelation.
    Returns (cycle_length_in_frames, all_cycle_starts)."""
    min_lag = int(0.3 * fps)
    max_lag = min(int(3.0 * fps), len(frames) - 1)

    # Candidate signals: (name, 1-D array)
    candidates = [
        ('l_foot X',     np.array([f['l_foot'][0] for f in frames])),
        ('r_foot X',     np.array([f['r_foot'][0] for f in frames])),
        ('l_foot Y',     np.array([f['l_foot'][1] for f in frames])),
        ('hip Y',        np.array([(f['l_hip'][1] + f['r_hip'][1]) / 2
                                   for f in frames])),
        ('hip X',        np.array([(f['l_hip'][1] - f['r_hip'][1])
                                   for f in frames])),  # hip sway/rotation
        ('shoulder X',   np.array([(f['l_shoulder'][0] - f['r_shoulder'][0])
                                   for f in frames])),
        ('l_hand Y',     np.array([f['l_hand'][1] for f in frames])),
        ('l_knee Y',     np.array([f['l_knee'][1] for f in frames])),
    ]

    best_name = None
    best_result = None
    for name, signal in candidates:
        result = _autocorr_peak(signal, min_lag, max_lag)
        if result and (best_result is None or result[1] > best_result[1]):
            best_result = result
            best_name = name

    if best_result is None:
        eprint("  Warning: no cycle detected in any signal, using full clip")
        return len(frames), [0]

    cycle_len = best_result[0]
    eprint(f"  Cycle detected via {best_name}: {cycle_len} frames "
           f"({cycle_len / fps:.2f}s, strength={best_result[1]:.2f})")

    starts = list(range(0, len(frames) - cycle_len + 1, cycle_len))
    eprint(f"  Found {len(starts)} complete cycles")

    return cycle_len, starts


# ---------------------------------------------------------------------------
# Step 4A: Raw projected
# ---------------------------------------------------------------------------

def method_raw(frames, cycle_len, cycle_starts, target_frames=48):
    """Method A: Raw projection, subsample to target frame count."""
    # Use first complete cycle
    start = cycle_starts[0]
    cycle = frames[start:start + cycle_len]

    # Subsample evenly
    indices = np.linspace(0, len(cycle) - 1, target_frames, dtype=int)
    return [cycle[i] for i in indices]


# ---------------------------------------------------------------------------
# Step 4B: Temporal smoothing
# ---------------------------------------------------------------------------

def _moving_average(data, window):
    """Moving average along axis 0."""
    kernel = np.ones(window) / window
    result = np.empty_like(data)
    for col in range(data.shape[1]):
        padded = np.pad(data[:, col], (window // 2, window // 2), mode='wrap')
        result[:, col] = np.convolve(padded, kernel, mode='valid')[:len(data)]
    return result


def _savgol(data, window, order=3):
    """Simple Savitzky-Golay filter (preserves peaks better than box filter).
    Wrapping-aware for cyclic data."""
    if window % 2 == 0:
        window += 1
    half = window // 2
    n = len(data)
    result = np.empty_like(data)

    # Build Vandermonde for local polynomial fit
    x = np.arange(-half, half + 1, dtype=float)
    V = np.vander(x, order + 1, increasing=True)
    # Least-squares coefficients for evaluating at x=0: first row of pinv
    coeffs = np.linalg.pinv(V)[0]

    for col in range(data.shape[1]):
        padded = np.pad(data[:, col], (half, half), mode='wrap')
        for i in range(n):
            window_data = padded[i:i + window]
            result[i, col] = np.dot(coeffs, window_data)

    return result


def method_temporal(frames, cycle_len, cycle_starts, target_frames=48):
    """Method B: Moving average + Savitzky-Golay smoothing."""
    start = cycle_starts[0]
    cycle = frames[start:start + cycle_len]

    # Convert to array: (cycle_len, 28) — 14 joints × 2 coords
    arr = _frames_to_array(cycle)

    # Moving average (window=5 at 120fps = 42ms)
    smoothed = _moving_average(arr, window=5)

    # Savitzky-Golay (window=7, order=3)
    smoothed = _savgol(smoothed, window=7, order=3)

    # Subsample
    indices = np.linspace(0, len(smoothed) - 1, target_frames, dtype=int)
    smoothed = smoothed[indices]

    return _array_to_frames(smoothed)


# ---------------------------------------------------------------------------
# Step 4C: Angle-space smoothing
# ---------------------------------------------------------------------------

def _extract_angles(frame):
    """Extract joint angles from a position-space frame.
    Returns dict of angles (radians) for key joints."""
    angles = {}

    # Hip angles: angle of thigh from vertical
    for side in ('l', 'r'):
        hip = frame[f'{side}_hip']
        knee = frame[f'{side}_knee']
        dx = knee[0] - hip[0]
        dy = knee[1] - hip[1]  # Y-up: positive dy = downward
        angles[f'{side}_hip'] = math.atan2(dx, dy)  # angle from vertical

        # Knee angle: angle between thigh and shin
        foot = frame[f'{side}_foot']
        dx2 = foot[0] - knee[0]
        dy2 = foot[1] - knee[1]
        shin_angle = math.atan2(dx2, dy2)
        angles[f'{side}_knee'] = shin_angle - angles[f'{side}_hip']

        # Shoulder/arm angles
        shoulder = frame[f'{side}_shoulder']
        elbow = frame[f'{side}_elbow']
        dx3 = elbow[0] - shoulder[0]
        dy3 = elbow[1] - shoulder[1]
        angles[f'{side}_arm'] = math.atan2(dx3, dy3)

        # Elbow angle
        hand = frame[f'{side}_hand']
        dx4 = hand[0] - elbow[0]
        dy4 = hand[1] - elbow[1]
        forearm_angle = math.atan2(dx4, dy4)
        angles[f'{side}_elbow'] = forearm_angle - angles[f'{side}_arm']

    return angles


def _reconstruct_from_angles(angles):
    """Reconstruct positions from angles using Vitruvian proportions.
    Returns dict {joint: (x, y)} in normalized 0..1 space."""
    frame = {}

    # Fixed positions (upper body)
    cx = 0.0
    frame['head'] = (cx, HEAD_CENTER)
    frame['neck'] = (cx, NECK_Y)

    for side, sign in (('l', -1), ('r', 1)):
        # Shoulders
        frame[f'{side}_shoulder'] = (cx + sign * SHOULDER_HALF_W, SHOULDER_Y)

        # Arms from angles
        arm_angle = angles[f'{side}_arm']
        sx, sy = frame[f'{side}_shoulder']
        ex = sx + UPPER_ARM_LEN * math.sin(arm_angle)
        ey = sy + UPPER_ARM_LEN * math.cos(arm_angle)
        frame[f'{side}_elbow'] = (ex, ey)

        elbow_angle = angles[f'{side}_elbow']
        total_arm = arm_angle + elbow_angle
        hx = ex + FOREARM_LEN * math.sin(total_arm)
        hy = ey + FOREARM_LEN * math.cos(total_arm)
        frame[f'{side}_hand'] = (hx, hy)

        # Hips
        frame[f'{side}_hip'] = (cx + sign * HIP_HALF_W, HIP_Y)

        # Legs from angles
        hip_angle = angles[f'{side}_hip']
        hpx, hpy = frame[f'{side}_hip']
        kx = hpx + THIGH_LEN * math.sin(hip_angle)
        ky = hpy + THIGH_LEN * math.cos(hip_angle)
        frame[f'{side}_knee'] = (kx, ky)

        knee_angle = angles[f'{side}_knee']
        total_leg = hip_angle + knee_angle
        fx = kx + SHIN_LEN * math.sin(total_leg)
        fy = ky + SHIN_LEN * math.cos(total_leg)
        frame[f'{side}_foot'] = (fx, fy)

    return frame


def method_angles(frames, cycle_len, cycle_starts, target_frames=48):
    """Method C: Smooth in angle space, reconstruct with Vitruvian proportions."""
    start = cycle_starts[0]
    cycle = frames[start:start + cycle_len]

    # Flip Y: mocap is Y-up, but Vitruvian reconstruction assumes Y-down
    # (head at small Y, feet at large Y)
    cycle_flipped = []
    for f in cycle:
        flipped = {}
        for name, (x, y) in f.items():
            flipped[name] = (x, -y)
        cycle_flipped.append(flipped)
    cycle = cycle_flipped

    # Extract angles for every frame
    angle_keys = ['l_hip', 'r_hip', 'l_knee', 'r_knee',
                  'l_arm', 'r_arm', 'l_elbow', 'r_elbow']
    all_angles = []
    for f in cycle:
        a = _extract_angles(f)
        all_angles.append([a[k] for k in angle_keys])

    arr = np.array(all_angles)

    # Smooth angles (less artifact-prone than position smoothing)
    arr = _moving_average(arr, window=5)
    arr = _savgol(arr, window=9, order=3)

    # Subsample
    indices = np.linspace(0, len(arr) - 1, target_frames, dtype=int)
    arr = arr[indices]

    # Reconstruct with Vitruvian proportions
    result = []
    for row in arr:
        angles = {k: v for k, v in zip(angle_keys, row)}
        result.append(_reconstruct_from_angles(angles))

    return result


# ---------------------------------------------------------------------------
# Step 4D: Multi-cycle average
# ---------------------------------------------------------------------------

def method_averaged(frames, cycle_len, cycle_starts, target_frames=48):
    """Method D: Average multiple gait cycles to cancel noise."""
    if len(cycle_starts) < 2:
        eprint("  Warning: only 1 cycle found, falling back to temporal smoothing")
        return method_temporal(frames, cycle_len, cycle_starts, target_frames)

    # Resample each cycle to target_frames
    cycles = []
    for start in cycle_starts:
        end = start + cycle_len
        if end > len(frames):
            break
        cycle = frames[start:end]
        arr = _frames_to_array(cycle)
        # Resample to target_frames
        indices = np.linspace(0, len(arr) - 1, target_frames)
        resampled = np.empty((target_frames, arr.shape[1]))
        for col in range(arr.shape[1]):
            resampled[:, col] = np.interp(indices, np.arange(len(arr)), arr[:, col])
        cycles.append(resampled)

    eprint(f"  Averaging {len(cycles)} cycles")
    avg = np.mean(cycles, axis=0)

    return _array_to_frames(avg)


# ---------------------------------------------------------------------------
# Array conversion helpers
# ---------------------------------------------------------------------------

def _frames_to_array(frames):
    """Convert list of {joint: (x,y)} to (N, 28) array."""
    rows = []
    for f in frames:
        row = []
        for j in OUT_JOINTS:
            row.extend(f[j])
        rows.append(row)
    return np.array(rows, dtype=np.float64)


def _array_to_frames(arr):
    """Convert (N, 28) array back to list of {joint: (x,y)}."""
    frames = []
    for row in arr:
        f = {}
        for i, j in enumerate(OUT_JOINTS):
            f[j] = (row[i * 2], row[i * 2 + 1])
        frames.append(f)
    return frames


# ---------------------------------------------------------------------------
# Limb bend consistency
# ---------------------------------------------------------------------------

# Limbs: (parent_joint, bend_joint, child_joint)
_LIMBS = [
    ('l_hip', 'l_knee', 'l_foot'),
    ('r_hip', 'r_knee', 'r_foot'),
    ('l_shoulder', 'l_elbow', 'l_hand'),
    ('r_shoulder', 'r_elbow', 'r_hand'),
]


def _cross_2d(ax, ay, bx, by):
    """2D cross product: positive if b is to the left of a."""
    return ax * by - ay * bx


def fix_limb_bends(frames):
    """Enforce consistent limb bend direction across frames.
    For each limb (hip→knee→foot, shoulder→elbow→hand), tracks which side
    of the parent→child line the bend joint is on. If it briefly flips
    (projection artifact), mirrors it back to the dominant side."""
    if len(frames) < 3:
        return frames

    # For each limb, compute the cross-product sign per frame
    for parent, bend, child in _LIMBS:
        signs = []
        for f in frames:
            px, py = f[parent]
            bx, by = f[bend]
            cx, cy = f[child]
            # Vector from parent to child
            dx, dy = cx - px, cy - py
            # Vector from parent to bend
            ex, ey = bx - px, by - py
            cross = _cross_2d(dx, dy, ex, ey)
            signs.append(cross)

        # Determine dominant sign using a running majority
        # Smooth the sign with a median filter (window=11 frames ≈ 0.37s at 30fps)
        window = min(11, len(signs))
        half = window // 2
        dominant = []
        for i in range(len(signs)):
            start = max(0, i - half)
            end = min(len(signs), i + half + 1)
            neighborhood = signs[start:end]
            pos = sum(1 for s in neighborhood if s > 0)
            neg = sum(1 for s in neighborhood if s < 0)
            dominant.append(1 if pos >= neg else -1)

        # Fix frames where the bend is on the wrong side
        for i, f in enumerate(frames):
            actual_sign = 1 if signs[i] > 0 else -1
            if actual_sign != dominant[i] and abs(signs[i]) > 0.01:
                # Mirror the bend joint across the parent→child line
                px, py = f[parent]
                bx, by = f[bend]
                cx, cy = f[child]
                dx, dy = cx - px, cy - py
                line_len_sq = dx * dx + dy * dy
                if line_len_sq < 1e-6:
                    continue
                # Project bend onto parent→child line
                t = ((bx - px) * dx + (by - py) * dy) / line_len_sq
                proj_x = px + t * dx
                proj_y = py + t * dy
                # Mirror across the line
                f[bend] = (2 * proj_x - bx, 2 * proj_y - by)

    return frames


# ---------------------------------------------------------------------------
# Normalize mocap to screen coords
# ---------------------------------------------------------------------------

def normalize_mocap_to_screen(frames, figure_height=48, center_x=32,
                              ground_y=56):
    """Normalize mocap frames to screen pixels.
    Uses consistent scale from median figure height.  Detects the ground
    plane from foot positions so jumps/flips read as airborne rather than
    being squashed into crouches."""
    if not frames:
        return []

    arr = _frames_to_array(frames)

    # Compute median head-to-foot span for consistent scale
    head_y_vals = arr[:, 1]  # head v (index 0 in OUT_JOINTS → cols 0,1)
    l_foot_y_vals = arr[:, 25]  # l_foot v (index 12 → cols 24,25)
    r_foot_y_vals = arr[:, 27]  # r_foot v (index 13 → cols 26,27)

    med_head_y = np.median(head_y_vals)
    med_foot_y = np.median(np.minimum(l_foot_y_vals, r_foot_y_vals))
    src_span = med_head_y - med_foot_y

    if abs(src_span) < 1e-6:
        eprint("  Warning: no vertical span")
        return []

    scale = figure_height / abs(src_span)

    # Detect ground plane: the lowest foot position when grounded.
    # Use a low percentile (10th) of the per-frame lowest-foot values
    # so occasional noise doesn't pull it down, but we capture the
    # true floor level (where feet spend most of their time).
    per_frame_lowest = np.minimum(l_foot_y_vals, r_foot_y_vals)
    ground_v = np.percentile(per_frame_lowest, 10)

    result = []
    for f in frames:
        lowest_v = min(f['l_foot'][1], f['r_foot'][1])
        # How high is the lowest foot above the ground plane?
        air_height = max(0.0, lowest_v - ground_v)

        normed = {}
        hip_mid_x = (f['l_hip'][0] + f['r_hip'][0]) / 2
        for name, (x, v) in f.items():
            px = (x - hip_mid_x) * scale + center_x
            # v is up-positive; screen y is down-positive
            # Anchor relative to ground plane:
            #   ground_v maps to ground_y (feet on floor)
            #   when airborne, air_height pushes everything up
            py = ground_y - (v - lowest_v) * scale - air_height * scale
            px = max(1.0, min(62.0, px))
            py = max(1.0, min(62.0, py))
            normed[name] = (px, py)
        result.append(normed)

    return result


# ---------------------------------------------------------------------------
# Download helpers (using build_dance's cache)
# ---------------------------------------------------------------------------

def download_walk_data(subject=None, clip=None):
    """Download ASF skeleton + AMC clip for a CMU subject."""
    subject = subject or DEFAULT_SUBJECT
    clip = clip or DEFAULT_CLIP
    ensure_cache()
    base = 'https://mocap.cs.cmu.edu/subjects'

    # ASF skeleton
    asf_path = CACHE_DIR / f'{subject}.asf'
    asf_data = _download(f'{base}/{subject}/{subject}.asf',
                         asf_path, f'{subject}.asf')
    if not asf_data:
        return None, None

    # AMC clip
    amc_path = CACHE_DIR / f'{clip}.amc'
    amc_data = _download(f'{base}/{subject}/{clip}.amc',
                         amc_path, f'{clip}.amc')
    if not amc_data:
        return None, None

    asf_text = asf_data.decode('utf-8', errors='replace')
    amc_text = amc_data.decode('utf-8', errors='replace')
    return asf_text, amc_text


# ---------------------------------------------------------------------------
# Comparison with procedural baseline
# ---------------------------------------------------------------------------

def compare_with_procedural(methods):
    """Print per-joint RMSE between each mocap method and procedural WALK_FRAMES."""
    from build_walk import generate_cycle, MOVEMENTS

    proc_frames = generate_cycle(MOVEMENTS['WALK'])
    proc_frames = normalize_to_screen(proc_frames)

    eprint("\n" + "=" * 70)
    eprint("COMPARISON: mocap methods vs procedural WALK")
    eprint("=" * 70)

    for method_name, mocap_frames in methods.items():
        # Match frame counts by resampling
        n_proc = len(proc_frames)
        n_mocap = len(mocap_frames)

        # Resample mocap to match procedural frame count
        proc_arr = _frames_to_array(proc_frames)
        mocap_arr = _frames_to_array(mocap_frames)

        if n_mocap != n_proc:
            indices = np.linspace(0, n_mocap - 1, n_proc)
            resampled = np.empty((n_proc, mocap_arr.shape[1]))
            for col in range(mocap_arr.shape[1]):
                resampled[:, col] = np.interp(indices,
                                              np.arange(n_mocap),
                                              mocap_arr[:, col])
            mocap_arr = resampled

        # Per-joint RMSE
        eprint(f"\n  Method {method_name} ({n_mocap} frames):")
        total_rmse = 0
        for i, jname in enumerate(OUT_JOINTS):
            mx = mocap_arr[:, i * 2]
            my = mocap_arr[:, i * 2 + 1]
            px = proc_arr[:, i * 2]
            py = proc_arr[:, i * 2 + 1]
            rmse = np.sqrt(np.mean((mx - px) ** 2 + (my - py) ** 2))
            total_rmse += rmse
            eprint(f"    {jname:12s}: {rmse:5.2f} px")
        avg_rmse = total_rmse / len(OUT_JOINTS)
        eprint(f"    {'AVERAGE':12s}: {avg_rmse:5.2f} px")

    # Also compare methods against each other
    names = list(methods.keys())
    if len(names) > 1:
        eprint(f"\n  Inter-method RMSE:")
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a = _frames_to_array(methods[names[i]])
                b = _frames_to_array(methods[names[j]])
                # Resample to same length
                n = min(len(a), len(b))
                if len(a) != n:
                    idx = np.linspace(0, len(a) - 1, n)
                    a = np.array([np.interp(idx, np.arange(len(a)), a[:, c])
                                  for c in range(a.shape[1])]).T
                if len(b) != n:
                    idx = np.linspace(0, len(b) - 1, n)
                    b = np.array([np.interp(idx, np.arange(len(b)), b[:, c])
                                  for c in range(b.shape[1])]).T
                rmse = np.sqrt(np.mean((a - b) ** 2))
                eprint(f"    {names[i]} vs {names[j]}: {rmse:5.2f} px")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

METHODS = {
    'A': ('WALK_RAW',      method_raw),
    'B': ('WALK_SMOOTH',   method_temporal),
    'C': ('WALK_ANGLE',    method_angles),
    'D': ('WALK_AVERAGED', method_averaged),
}


def _parse_arg(args, flag):
    """Extract --flag VALUE from args, return value or None."""
    if flag in args:
        i = args.index(flag)
        if i + 1 < len(args):
            return args[i + 1]
    return None


def main():
    args = sys.argv[1:]
    debug = '--debug' in args
    compare = '--compare' in args
    selected_method = _parse_arg(args, '--method')
    if selected_method:
        selected_method = selected_method.upper()

    subject = _parse_arg(args, '--subject') or DEFAULT_SUBJECT
    clip = _parse_arg(args, '--clip') or DEFAULT_CLIP

    # Download data
    eprint(f"=== CMU Subject {subject}: Clip {clip} ===")
    asf_text, amc_text = download_walk_data(subject, clip)
    if not asf_text or not amc_text:
        eprint("ERROR: Failed to download CMU data")
        sys.exit(1)

    # Parse
    bones, hierarchy, root_order, length_scale = parse_asf(asf_text)
    amc_frames = parse_amc(amc_text)
    eprint(f"  Skeleton: {len(bones)} bones, scale={length_scale}")
    eprint(f"  Motion: {len(amc_frames)} frames")

    # Check available joints
    sample_world = forward_kinematics_asf(bones, hierarchy, root_order,
                                          length_scale, amc_frames[0])
    available = sorted(sample_world.keys())
    mapped = {our: cmu for our, cmu in JOINT_MAP.items() if cmu in sample_world}
    missing = {our: cmu for our, cmu in JOINT_MAP.items() if cmu not in sample_world}

    if missing:
        eprint(f"  WARNING: Missing CMU joints: {missing}")
        eprint(f"  Available: {available}")

        # Try to find alternatives
        for our_name, cmu_name in list(missing.items()):
            # Try common alternatives
            alts = {
                'lwrist': ['lhand'],
                'rwrist': ['rhand'],
                'lowerneck': ['upperneck', 'thorax'],
                'head': ['upperneck'],
            }
            for alt in alts.get(cmu_name, []):
                if alt in sample_world:
                    eprint(f"    Using {alt} for {our_name} (instead of {cmu_name})")
                    JOINT_MAP[our_name] = alt
                    break

    eprint(f"  Mapped {len(mapped)}/{len(JOINT_MAP)} joints")

    if debug:
        eprint(f"\n  Joint mapping:")
        for our, cmu in JOINT_MAP.items():
            pos = sample_world.get(cmu, None)
            status = f"({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f})" if pos else "MISSING"
            eprint(f"    {our:12s} → {cmu:12s} {status}")

    # Step 1: Extract all frames
    eprint("\nExtracting 14-joint positions from all frames...")
    all_frames = extract_all_frames(bones, hierarchy, root_order,
                                    length_scale, amc_frames)
    eprint(f"  Extracted {len(all_frames)} valid frames")

    if not all_frames:
        eprint("ERROR: No valid frames extracted")
        sys.exit(1)

    # Step 2: Treadmill mode
    eprint("Applying treadmill (removing X drift)...")
    all_frames = treadmill(all_frames)

    # Step 3: Detect gait cycle
    eprint("Detecting gait cycle...")
    cycle_len, cycle_starts = detect_cycle(all_frames)

    if debug:
        # Print first frame stats
        f0 = all_frames[0]
        eprint(f"\n  Frame 0 (treadmill'd):")
        for j in OUT_JOINTS:
            eprint(f"    {j:12s}: ({f0[j][0]:7.2f}, {f0[j][1]:7.2f})")

    # Step 4: Run methods
    methods_to_run = METHODS.items()
    if selected_method:
        if selected_method in METHODS:
            methods_to_run = [(selected_method, METHODS[selected_method])]
        else:
            eprint(f"Unknown method: {selected_method}")
            eprint(f"Available: {', '.join(METHODS.keys())}")
            sys.exit(1)

    results = {}
    for key, (var_name, method_fn) in methods_to_run:
        eprint(f"\nMethod {key}: {var_name}...")
        try:
            raw_frames = method_fn(all_frames, cycle_len, cycle_starts)

            if key == 'C':
                # Angle method outputs in normalized 0..1 space already
                screen_frames = normalize_to_screen(raw_frames)
            else:
                # Position methods need mocap→screen normalization
                screen_frames = normalize_mocap_to_screen(raw_frames)

            validate(var_name, screen_frames)
            eprint(f"  {var_name}: {len(screen_frames)} frames, validated OK")

            print(format_output(var_name, screen_frames))
            print()

            results[key] = screen_frames

            if debug:
                f0 = screen_frames[0]
                eprint(f"  Sample frame 0:")
                for j in OUT_JOINTS:
                    eprint(f"    {j:12s}: ({f0[j][0]:5.1f}, {f0[j][1]:5.1f})")

        except Exception as e:
            eprint(f"  ERROR in method {key}: {e}")
            import traceback
            traceback.print_exc(file=sys.stderr)

    # Compare
    if compare and results:
        compare_with_procedural(results)

    eprint("\nDone!")


if __name__ == '__main__':
    main()
