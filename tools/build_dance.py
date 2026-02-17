#!/usr/bin/env python3
"""
build_dance.py — Extract dance keyframes from real motion capture data
======================================================================
Two pipelines:
  A) ASF/AMC (CMU MoCap, public domain) — auto-download, parse, FK
  B) MediaPipe pose estimation — user-provided dance videos

Outputs keyframes in {hx, hy, lhx, lhy, ...} format for visuals/dance.py.

Usage:
  python3 tools/build_dance.py salsa          # CMU pipeline, auto-downloads
  python3 tools/build_dance.py bharata        # MediaPipe pipeline (video in cache)
  python3 tools/build_dance.py all            # All configured dances
  python3 tools/build_dance.py --list         # Show configured sources and status
  python3 tools/build_dance.py salsa --k 8    # Override keyframe count
  python3 tools/build_dance.py --clean        # Clear cache
"""

import json
import math
import ssl
import sys
import urllib.request
from pathlib import Path
from functools import partial

eprint = partial(print, file=sys.stderr, flush=True)

CACHE_DIR = Path(__file__).parent / '.dance_cache'

# ---------------------------------------------------------------------------
# Source manifest — CMU MoCap (public domain, no restrictions)
# ASF = skeleton definition, AMC = per-frame joint angles
# https://mocap.cs.cmu.edu/
# ---------------------------------------------------------------------------
CMU_BASE = 'https://mocap.cs.cmu.edu/subjects'

SOURCES = {
    'salsa': {
        'pipeline': 'cmu',
        'subject': '60',
        # CMU subject 60: salsa dance (15 clips at 60fps)
        'clips': ['60_01', '60_02', '60_04', '60_06', '60_08',
                  '60_10', '60_12', '60_13', '60_14'],
        'k': 6,
    },
    'charleston': {
        'pipeline': 'cmu',
        'subject': '93',
        # CMU subject 93: charleston dance
        'clips': ['93_03', '93_05', '93_07'],
        'k': 5,
    },
    'ballet': {
        'pipeline': 'cmu',
        'subject': '05',
        # CMU subject 05: modern dance with ballet vocabulary
        # (arabesques, jetés, pirouettes, attitudes)
        'clips': ['05_02', '05_04', '05_05', '05_06', '05_08',
                  '05_10', '05_14', '05_18'],
        'k': 6,
    },
    'bharata': {
        'pipeline': 'mediapipe',
        'video': 'bharata.mp4',
        'k': 5,
    },
    'hula': {
        'pipeline': 'mediapipe',
        'video': 'hula.mp4',
        'k': 6,
    },
    'capoeira': {
        'pipeline': 'mediapipe',
        'video': 'capoeira.mp4',
        'k': 6,
    },
    'irish': {
        'pipeline': 'mediapipe',
        'video': 'irish.mp4',
        'k': 5,
    },
}

# Joints we track → their CMU skeleton names
TARGET_JOINTS = ['head', 'lhand', 'rhand', 'lfoot', 'rfoot']

# ---------------------------------------------------------------------------
# ASF Parser — skeleton definition
# ---------------------------------------------------------------------------
# ASF format: :bonedata section defines each bone (direction, length, axis,
# dof), and :hierarchy section defines the parent-child tree.

def parse_asf(text):
    """Parse ASF skeleton file.
    Returns (bones, hierarchy, root_order, length_scale).
    bones: dict name → {direction, length, axis, axis_order, dof}
    hierarchy: dict parent → [children]
    """
    lines = text.strip().split('\n')
    bones = {}
    hierarchy = {}
    root_order = 'XYZ'
    length_scale = 1.0
    i = 0

    # Track current section
    section = None
    bone = None

    while i < len(lines):
        line = lines[i].strip()
        i += 1

        if not line or line.startswith('#'):
            continue

        # Section headers
        if line.startswith(':'):
            section = line.split()[0].lower()
            if section == ':units':
                # Parse units for length scale
                while i < len(lines):
                    uline = lines[i].strip()
                    if uline.startswith(':') or (not uline.startswith(' ') and
                                                  not uline.startswith('\t') and uline):
                        if not uline.startswith('mass') and not uline.startswith('length') \
                                and not uline.startswith('angle'):
                            break
                    parts = uline.split()
                    if len(parts) >= 2 and parts[0] == 'length':
                        length_scale = float(parts[1])
                    i += 1
            elif section == ':root':
                while i < len(lines):
                    rline = lines[i].strip()
                    if rline.startswith(':') or rline.startswith('begin'):
                        break
                    parts = rline.split()
                    if parts and parts[0] == 'order':
                        # e.g. "order TX TY TZ RX RY RZ"
                        rot_chs = [p for p in parts[1:] if p.startswith('R')]
                        root_order = ''.join(p[1] for p in rot_chs)
                    i += 1
            continue

        if section == ':bonedata':
            if line == 'begin':
                bone = {}
                continue
            elif line == 'end':
                if bone and 'name' in bone:
                    bones[bone['name']] = bone
                bone = None
                continue

            if bone is not None:
                parts = line.split()
                if parts[0] == 'name':
                    bone['name'] = parts[1]
                elif parts[0] == 'direction':
                    bone['direction'] = (float(parts[1]), float(parts[2]),
                                         float(parts[3]))
                elif parts[0] == 'length':
                    bone['length'] = float(parts[1])
                elif parts[0] == 'axis':
                    bone['axis'] = (float(parts[1]), float(parts[2]),
                                    float(parts[3]))
                    bone['axis_order'] = parts[4] if len(parts) > 4 else 'XYZ'
                elif parts[0] == 'dof':
                    bone['dof'] = parts[1:]  # e.g. ['rx', 'ry', 'rz']

        elif section == ':hierarchy':
            if line in ('begin', 'end'):
                continue
            parts = line.split()
            if len(parts) >= 2:
                parent = parts[0]
                children = parts[1:]
                hierarchy[parent] = children

    return bones, hierarchy, root_order, length_scale


# ---------------------------------------------------------------------------
# AMC Parser — per-frame joint angles
# ---------------------------------------------------------------------------

def parse_amc(text):
    """Parse AMC motion file.
    Returns list of frames, each frame is dict: joint_name → [values]."""
    lines = text.strip().split('\n')
    frames = []
    current_frame = None
    i = 0

    while i < len(lines):
        line = lines[i].strip()
        i += 1

        if not line or line.startswith('#') or line.startswith(':'):
            continue

        parts = line.split()

        # Frame number (single integer on its own line)
        if len(parts) == 1:
            try:
                _frame_num = int(parts[0])
                if current_frame is not None:
                    frames.append(current_frame)
                current_frame = {}
                continue
            except ValueError:
                pass

        # Joint data: name val1 val2 ...
        if current_frame is not None and len(parts) >= 2:
            name = parts[0]
            vals = [float(v) for v in parts[1:]]
            current_frame[name] = vals

    if current_frame is not None:
        frames.append(current_frame)

    return frames


# ---------------------------------------------------------------------------
# Forward Kinematics for ASF/AMC
# ---------------------------------------------------------------------------

def _deg2rad(d):
    return d * math.pi / 180.0


def _euler_to_matrix(ax, ay, az, order='XYZ'):
    """Euler angles (degrees) → 3×3 rotation matrix."""
    ax, ay, az = _deg2rad(ax), _deg2rad(ay), _deg2rad(az)
    cx, sx = math.cos(ax), math.sin(ax)
    cy, sy = math.cos(ay), math.sin(ay)
    cz, sz = math.cos(az), math.sin(az)

    Rx = [[1, 0, 0], [0, cx, -sx], [0, sx, cx]]
    Ry = [[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]
    Rz = [[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]

    mats = {'X': Rx, 'Y': Ry, 'Z': Rz}

    R = mats[order[0]]
    for ch in order[1:]:
        R = _mat_mul(R, mats[ch])
    return R


def _mat_mul(A, B):
    return [
        [sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)]
        for i in range(3)
    ]


def _mat_transpose(M):
    return [[M[j][i] for j in range(3)] for i in range(3)]


def _mat_vec(M, v):
    return [sum(M[i][j] * v[j] for j in range(3)) for i in range(3)]


def _vec_add(a, b):
    return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]


def _vec_scale(v, s):
    return [v[0] * s, v[1] * s, v[2] * s]


def _identity():
    return [[1, 0, 0], [0, 1, 0], [0, 0, 1]]


def forward_kinematics_asf(bones, hierarchy, root_order, length_scale,
                            frame_data):
    """Compute world positions for all joints in one AMC frame.
    Returns dict: joint_name → (x, y, z) world position."""
    world_pos = {}

    # Root position and rotation
    root_vals = frame_data.get('root', [0, 0, 0, 0, 0, 0])
    # Root: TX TY TZ RX RY RZ
    root_pos = [root_vals[0] * length_scale,
                root_vals[1] * length_scale,
                root_vals[2] * length_scale]
    root_rot = _euler_to_matrix(root_vals[3], root_vals[4], root_vals[5],
                                root_order)

    world_pos['root'] = tuple(root_pos)

    def fk_recursive(joint_name, parent_pos, parent_rot):
        if joint_name not in bones:
            return

        bone = bones[joint_name]
        direction = bone.get('direction', (0, 0, 0))
        length = bone.get('length', 0.0) * length_scale
        axis = bone.get('axis', (0, 0, 0))
        axis_order = bone.get('axis_order', 'XYZ')
        dof = bone.get('dof', [])

        # Bone vector in local space: direction * length
        bone_vec = _vec_scale(list(direction), length)

        # The axis rotation defines the bone's local coordinate frame
        # C = axis rotation matrix, C_inv = its inverse (transpose)
        C = _euler_to_matrix(axis[0], axis[1], axis[2], axis_order)
        C_inv = _mat_transpose(C)

        # Build local rotation from AMC data
        # AMC gives rotations in the bone's local frame
        joint_vals = frame_data.get(joint_name, [])
        rx = ry = rz = 0.0
        vi = 0
        for d in dof:
            if vi < len(joint_vals):
                if d == 'rx':
                    rx = joint_vals[vi]
                elif d == 'ry':
                    ry = joint_vals[vi]
                elif d == 'rz':
                    rz = joint_vals[vi]
                vi += 1

        # Local rotation in bone's coordinate frame
        # R_local = C * R_amc * C_inv
        R_amc = _euler_to_matrix(rx, ry, rz, axis_order)
        R_local = _mat_mul(C, _mat_mul(R_amc, C_inv))

        # World rotation for this joint
        world_rot = _mat_mul(parent_rot, R_local)

        # World position: parent + world_rot * bone_vector
        rotated_bone = _mat_vec(world_rot, bone_vec)
        pos = _vec_add(parent_pos, rotated_bone)
        world_pos[joint_name] = tuple(pos)

        # Recurse into children
        if joint_name in hierarchy:
            for child in hierarchy[joint_name]:
                fk_recursive(child, pos, world_rot)

    # Process root's children
    for child in hierarchy.get('root', []):
        fk_recursive(child, root_pos, root_rot)

    return world_pos


def extract_poses_cmu(bones, hierarchy, root_order, length_scale,
                      frames, subsample=4):
    """Extract 5-point poses from CMU AMC frames.
    Returns list of 10-tuples: (hx,hy,lhx,lhy,rhx,rhy,lfx,lfy,rfx,rfy)."""
    # Find which joint names exist for our targets
    all_joints = set(bones.keys())
    joint_map = {}
    for target in TARGET_JOINTS:
        # Direct match
        if target in all_joints:
            joint_map[target] = target
        else:
            # Try variants
            for jname in all_joints:
                if jname.lower() == target.lower():
                    joint_map[target] = jname
                    break

    missing = [t for t in TARGET_JOINTS if t not in joint_map]
    if missing:
        eprint(f"  Warning: missing joints {missing}")
        eprint(f"  Available: {sorted(all_joints)}")
        # Try partial matches for missing joints
        for t in missing:
            for jname in all_joints:
                if t.replace('l', 'l').replace('r', 'r') in jname.lower():
                    joint_map[t] = jname
                    break
    eprint(f"  Joint mapping: {joint_map}")

    # Verify we have all 5
    for t in TARGET_JOINTS:
        if t not in joint_map:
            eprint(f"  ERROR: Cannot map joint '{t}'")
            return []

    poses = []
    skipped = 0
    for fi in range(0, len(frames), subsample):
        world = forward_kinematics_asf(bones, hierarchy, root_order,
                                        length_scale, frames[fi])

        positions = {}
        for target in TARGET_JOINTS:
            jname = joint_map[target]
            if jname in world:
                positions[target] = world[jname]
            else:
                break
        else:
            # CMU mocap: Y-up. We project to X (horizontal) and Y (vertical).
            # Negate Y for display (Y-down on screen).
            # Ignore Z (depth into screen).
            h = positions['head']
            lf = positions['lfoot']
            rf = positions['rfoot']

            # Sanity: head above feet (Y-up → head Y > foot Y)
            foot_y = max(lf[1], rf[1])
            if h[1] < foot_y:
                skipped += 1
                continue

            # Filter extreme crouching: head-to-foot span should be
            # at least 60% of a standing pose (~7 mocap units)
            span = h[1] - foot_y
            if span < 4.0:
                skipped += 1
                continue

            poses.append((
                h[0], -h[1],
                positions['lhand'][0], -positions['lhand'][1],
                positions['rhand'][0], -positions['rhand'][1],
                lf[0], -lf[1],
                rf[0], -rf[1],
            ))

    if skipped:
        eprint(f"  Filtered {skipped} inverted poses ({len(poses)} valid)")
    if poses:
        p0 = poses[0]
        eprint(f"  Sample raw: head=({p0[0]:.1f},{p0[1]:.1f}) "
               f"lhand=({p0[2]:.1f},{p0[3]:.1f}) "
               f"lfoot=({p0[6]:.1f},{p0[7]:.1f})")
    return poses


# ---------------------------------------------------------------------------
# MediaPipe Pipeline
# ---------------------------------------------------------------------------

def extract_poses_mediapipe(video_path, subsample=3):
    """Extract 5-point poses from video via MediaPipe Pose.
    Returns list of 10-tuples (same format as CMU pipeline)."""
    try:
        import cv2
        import mediapipe as mp
    except ImportError:
        eprint("ERROR: MediaPipe pipeline requires: pip install mediapipe opencv-python")
        return []

    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        eprint(f"ERROR: Cannot open video: {video_path}")
        return []

    w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    eprint(f"  Video: {int(w)}x{int(h)}, {total} frames")

    # MediaPipe landmark indices
    NOSE = 0
    L_WRIST = 15
    R_WRIST = 16
    L_ANKLE = 27
    R_ANKLE = 28

    poses = []
    frame_idx = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame_idx += 1
        if frame_idx % subsample != 0:
            continue

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)

        if not results.pose_landmarks:
            continue

        lm = results.pose_landmarks.landmark

        # Check visibility of key landmarks
        key_lms = [lm[NOSE], lm[L_WRIST], lm[R_WRIST], lm[L_ANKLE], lm[R_ANKLE]]
        if any(l.visibility < 0.5 for l in key_lms):
            continue

        # Landmarks normalized [0,1] → pixel coords
        poses.append((
            lm[NOSE].x * w, lm[NOSE].y * h,
            lm[L_WRIST].x * w, lm[L_WRIST].y * h,
            lm[R_WRIST].x * w, lm[R_WRIST].y * h,
            lm[L_ANKLE].x * w, lm[L_ANKLE].y * h,
            lm[R_ANKLE].x * w, lm[R_ANKLE].y * h,
        ))

    cap.release()
    pose.close()
    eprint(f"  Extracted {len(poses)} valid poses from {frame_idx} frames")
    return poses


# ---------------------------------------------------------------------------
# Normalization (shared by both pipelines)
# ---------------------------------------------------------------------------

def normalize_poses(poses):
    """Normalize poses to LED grid coordinates.
    Target: head~y=17, feet~y=44, center x=32, body ~40px wide.
    Returns list of 10-tuples clamped to [2..61]."""
    if not poses:
        return []

    import numpy as np
    arr = np.array(poses, dtype=np.float64)  # (N, 10)

    # y-coords: head=1, lfoot=7, rfoot=9
    head_y = arr[:, 1]
    lfoot_y = arr[:, 7]
    rfoot_y = arr[:, 9]

    # Median head and foot y for robust scaling
    med_head_y = np.median(head_y)
    med_foot_y = np.median(np.maximum(lfoot_y, rfoot_y))

    # Target: head at y=17, feet at y=44 → span = 27px
    target_head_y = 17.0
    target_span = 27.0  # 44 - 17

    src_span = med_foot_y - med_head_y
    if abs(src_span) < 1e-6:
        eprint("  Warning: no vertical span in poses, using fallback scale")
        scale = 1.0
    else:
        scale = target_span / src_span

    x_indices = [0, 2, 4, 6, 8]
    y_indices = [1, 3, 5, 7, 9]

    # Apply uniform scale + translation for Y (global centering)
    normalized = np.copy(arr)
    for yi in y_indices:
        normalized[:, yi] = (arr[:, yi] - med_head_y) * scale + target_head_y

    # Center X per-frame: shift each frame so head x = 32
    # This removes lateral drift while preserving limb relative positions
    for xi in x_indices:
        normalized[:, xi] = (arr[:, xi] - arr[:, 0]) * scale + 32.0

    # Clamp to [2..61]
    normalized = np.clip(normalized, 2, 61)

    return [tuple(row) for row in normalized]


# ---------------------------------------------------------------------------
# K-means keyframe selection (numpy, no scipy)
# ---------------------------------------------------------------------------

def kmeans_keyframes(poses, k=6, max_iter=50, seed=42):
    """Select k keyframes via K-means clustering in 10-dim pose space.
    Returns indices of actual frames closest to each centroid, sorted by time."""
    import numpy as np

    if len(poses) <= k:
        return list(range(len(poses)))

    arr = np.array(poses, dtype=np.float64)
    n = len(arr)
    rng = np.random.RandomState(seed)

    # K-means++ initialization
    centroids = np.empty((k, 10))
    idx = rng.randint(n)
    centroids[0] = arr[idx]
    for c in range(1, k):
        dists = np.min([np.sum((arr - centroids[j]) ** 2, axis=1)
                        for j in range(c)], axis=0)
        probs = dists / dists.sum()
        idx = rng.choice(n, p=probs)
        centroids[c] = arr[idx]

    # Iterate
    for _ in range(max_iter):
        dists = np.array([np.sum((arr - c) ** 2, axis=1) for c in centroids])
        labels = np.argmin(dists, axis=0)

        new_centroids = np.copy(centroids)
        for c in range(k):
            mask = labels == c
            if mask.any():
                new_centroids[c] = arr[mask].mean(axis=0)

        if np.allclose(centroids, new_centroids, atol=1e-6):
            break
        centroids = new_centroids

    # Pick actual frame closest to each centroid
    selected = []
    for c in range(k):
        dists_to_c = np.sum((arr - centroids[c]) ** 2, axis=1)
        selected.append(int(np.argmin(dists_to_c)))

    # Sort by time for natural animation order
    selected.sort()

    # Deduplicate
    seen = set()
    unique = []
    for s in selected:
        if s not in seen:
            seen.add(s)
            unique.append(s)

    return unique


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def format_keyframes(name, poses, indices):
    """Format selected keyframes as Python dict literals for dance.py."""
    lines = [f"        # {name} - {len(indices)} keyframes from motion capture"]
    for fi in indices:
        p = poses[fi]
        hx, hy = int(round(p[0])), int(round(p[1]))
        lhx, lhy = int(round(p[2])), int(round(p[3]))
        rhx, rhy = int(round(p[4])), int(round(p[5]))
        lfx, lfy = int(round(p[6])), int(round(p[7]))
        rfx, rfy = int(round(p[8])), int(round(p[9]))
        lines.append(
            f"            {{'hx':{hx},'hy':{hy}, "
            f"'lhx':{lhx},'lhy':{lhy}, 'rhx':{rhx},'rhy':{rhy},"
            f"\n             'lfx':{lfx},'lfy':{lfy}, 'rfx':{rfx},'rfy':{rfy}}},"
        )
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Download / cache
# ---------------------------------------------------------------------------

def ensure_cache():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _download(url, cache_path, label):
    """Download a file with caching. Returns bytes or None."""
    if cache_path.exists():
        eprint(f"  Cached: {cache_path.name}")
        return cache_path.read_bytes()

    eprint(f"  Downloading {label} ...")
    req = urllib.request.Request(url, headers={
        'User-Agent': 'led-arcade-dance-tool/1.0'
    })
    # CMU's cert chain may not be in macOS's default trust store
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            data = resp.read()
        cache_path.write_bytes(data)
        eprint(f"  Saved: {cache_path.name} ({len(data):,} bytes)")
        return data
    except Exception as e:
        eprint(f"  ERROR downloading {label}: {e}")
        return None


def download_asf(subject):
    """Download ASF skeleton file for a CMU subject."""
    url = f'{CMU_BASE}/{subject}/{subject}.asf'
    path = CACHE_DIR / f'{subject}.asf'
    data = _download(url, path, f'{subject}.asf')
    return data.decode('utf-8', errors='replace') if data else None


def download_amc(clip_id, subject):
    """Download AMC motion file for a CMU clip."""
    url = f'{CMU_BASE}/{subject}/{clip_id}.amc'
    path = CACHE_DIR / f'{clip_id}.amc'
    data = _download(url, path, f'{clip_id}.amc')
    return data.decode('utf-8', errors='replace') if data else None


# ---------------------------------------------------------------------------
# Pipeline runners
# ---------------------------------------------------------------------------

def run_cmu_pipeline(name, source, k_override=None):
    """Run full CMU ASF/AMC pipeline for a dance source."""
    k = k_override or source['k']
    subject = source['subject']
    all_poses = []

    # Download skeleton once per subject
    asf_text = download_asf(subject)
    if not asf_text:
        eprint(f"  ERROR: Cannot download skeleton for subject {subject}")
        return None

    bones, hierarchy, root_order, length_scale = parse_asf(asf_text)
    eprint(f"  Skeleton: {len(bones)} bones, scale={length_scale}")

    for clip_id in source['clips']:
        eprint(f"\n  Processing clip: {clip_id}")
        amc_text = download_amc(clip_id, subject)
        if not amc_text:
            continue

        frames = parse_amc(amc_text)
        eprint(f"  Parsed: {len(frames)} frames")

        poses = extract_poses_cmu(bones, hierarchy, root_order, length_scale,
                                   frames, subsample=4)
        if not poses:
            eprint(f"  Skipping clip {clip_id} - no valid poses")
            continue

        # Normalize this clip independently (different clips may drift)
        normalized = normalize_poses(poses)
        all_poses.extend(normalized)
        eprint(f"  Got {len(normalized)} normalized poses from {clip_id}")

    if not all_poses:
        eprint(f"ERROR: No poses extracted for {name}")
        return None

    eprint(f"\n  Total poses: {len(all_poses)}")
    eprint(f"  Clustering into {k} keyframes...")

    indices = kmeans_keyframes(all_poses, k=k)
    eprint(f"  Selected frames: {indices}")

    return all_poses, indices


def run_mediapipe_pipeline(name, source, k_override=None):
    """Run MediaPipe pipeline for a dance source."""
    k = k_override or source['k']
    video_path = CACHE_DIR / source['video']

    if not video_path.exists():
        eprint(f"ERROR: Video not found: {video_path}")
        eprint(f"  Place your {source['video']} in {CACHE_DIR}/")
        return None

    eprint(f"  Processing video: {source['video']}")
    poses = extract_poses_mediapipe(video_path)
    if not poses:
        return None

    normalized = normalize_poses(poses)
    eprint(f"  {len(normalized)} normalized poses")
    eprint(f"  Clustering into {k} keyframes...")

    indices = kmeans_keyframes(normalized, k=k)
    eprint(f"  Selected frames: {indices}")

    return normalized, indices


# ---------------------------------------------------------------------------
# Cache save/load for reproducibility
# ---------------------------------------------------------------------------

def save_cache(name, poses, indices):
    cache_file = CACHE_DIR / f'{name}_keyframes.json'
    data = {
        'name': name,
        'total_poses': len(poses),
        'k': len(indices),
        'indices': indices,
        'keyframes': [list(poses[i]) for i in indices],
    }
    cache_file.write_text(json.dumps(data, indent=2))
    eprint(f"  Cached keyframes to {cache_file.name}")


def load_cache(name):
    cache_file = CACHE_DIR / f'{name}_keyframes.json'
    if not cache_file.exists():
        return None
    return json.loads(cache_file.read_text())


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def process_dance(name, k_override=None, force=False):
    """Process a single dance source. Returns (poses, indices) or None."""
    if name not in SOURCES:
        eprint(f"Unknown dance: {name}")
        eprint(f"Available: {', '.join(SOURCES.keys())}")
        return None

    if not force:
        cached = load_cache(name)
        if cached:
            eprint(f"\n=== {name.upper()} (cached) ===")
            poses = [tuple(kf) for kf in cached['keyframes']]
            indices = list(range(len(poses)))
            output = format_keyframes(name.upper(), poses, indices)
            print(output)
            return poses, indices

    source = SOURCES[name]
    eprint(f"\n=== {name.upper()} ({source['pipeline']} pipeline) ===")

    if source['pipeline'] == 'cmu':
        result = run_cmu_pipeline(name, source, k_override)
    elif source['pipeline'] == 'mediapipe':
        result = run_mediapipe_pipeline(name, source, k_override)
    else:
        eprint(f"Unknown pipeline: {source['pipeline']}")
        return None

    if result is None:
        return None

    poses, indices = result
    save_cache(name, poses, indices)

    output = format_keyframes(name.upper(), poses, indices)
    print(output)
    return poses, indices


def show_list():
    eprint("Configured dance sources:\n")
    for name, src in SOURCES.items():
        pipeline = src['pipeline']
        k = src['k']
        cached = (CACHE_DIR / f'{name}_keyframes.json').exists()
        status = 'cached' if cached else 'not built'

        if pipeline == 'cmu':
            clips = len(src['clips'])
            eprint(f"  {name:12s}  {pipeline:10s}  subject {src['subject']}  "
                   f"{clips} clips  k={k}  [{status}]")
        else:
            video = src['video']
            video_exists = (CACHE_DIR / video).exists()
            vid_status = 'found' if video_exists else 'MISSING'
            eprint(f"  {name:12s}  {pipeline:10s}  {video} ({vid_status})  "
                   f"k={k}  [{status}]")


def clean_cache():
    if not CACHE_DIR.exists():
        eprint("No cache directory.")
        return
    count = 0
    for f in CACHE_DIR.iterdir():
        if f.is_file():
            f.unlink()
            count += 1
    eprint(f"Removed {count} cached files.")


def main():
    args = sys.argv[1:]

    if not args or '--help' in args or '-h' in args:
        print(__doc__)
        return

    if '--list' in args:
        show_list()
        return

    if '--clean' in args:
        clean_cache()
        return

    # Parse --k option
    k_override = None
    if '--k' in args:
        ki = args.index('--k')
        if ki + 1 < len(args):
            k_override = int(args[ki + 1])
            args = args[:ki] + args[ki + 2:]

    force = '--force' in args
    if force:
        args.remove('--force')

    ensure_cache()

    targets = args if args else []
    if 'all' in targets:
        targets = [n for n, s in SOURCES.items() if s['pipeline'] == 'cmu']

    for name in targets:
        process_dance(name, k_override=k_override, force=force)


if __name__ == '__main__':
    main()
