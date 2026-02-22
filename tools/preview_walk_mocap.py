#!/usr/bin/env python3
"""
preview_walk_mocap.py — Live preview of mocap walk methods
==========================================================
Runs the actual 64x64 renderer with stick figure animation.
Cycles through: Procedural, Method A (Raw), B (Smooth), C (Angle), D (Averaged).

Controls:
  Left/Right arrow  - Previous/Next method (or clip in gallery mode)
  Space             - Pause/Resume
  +/-               - Speed up/slow down
  Q/Escape          - Quit

Usage:
  python3 tools/preview_walk_mocap.py                        # Single clip mode
  python3 tools/preview_walk_mocap.py --gallery              # All cached clips
  python3 tools/preview_walk_mocap.py --subject 60 --clip 60_01
"""

import sys
import os

# Add project root to path so we can import arcade modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

# --- Constants (match arcade.py) ---
GRID_SIZE = 64
SCALE = 10
FPS = 30
BLACK = (0, 0, 0)

# --- Rendering constants (from walk.py) ---
BODY_COLOR = (220, 200, 170)
JOINT_COLOR = (255, 240, 210)
HEAD_COLOR = (255, 245, 220)
HEAD_OUTLINE = (180, 165, 140)
GROUND_COLOR = (50, 45, 35)

HEAD_PIXELS = [
            (-1, -2), (0, -2), (1, -2),
    (-2, -1), (-1, -1), (0, -1), (1, -1), (2, -1),
    (-2,  0), (-1,  0), (0,  0), (1,  0), (2,  0),
    (-2,  1), (-1,  1), (0,  1), (1,  1), (2,  1),
            (-1,  2), (0,  2), (1,  2),
]
HEAD_OUTLINE_PIXELS = [
            (-1, -2), (0, -2), (1, -2),
    (-2, -1),                           (2, -1),
    (-2,  0),                           (2,  0),
    (-2,  1),                           (2,  1),
            (-1,  2), (0,  2), (1,  2),
]

BONES = [
    ('head', 'neck'),
    ('l_shoulder', 'r_shoulder'),
    ('neck', 'l_shoulder'),
    ('neck', 'r_shoulder'),
    ('l_shoulder', 'l_elbow'),
    ('l_elbow', 'l_hand'),
    ('r_shoulder', 'r_elbow'),
    ('r_elbow', 'r_hand'),
    ('neck', 'l_hip'),
    ('neck', 'r_hip'),
    ('l_hip', 'r_hip'),
    ('l_hip', 'l_knee'),
    ('l_knee', 'l_foot'),
    ('r_hip', 'r_knee'),
    ('r_knee', 'r_foot'),
]

JOINT_NAMES = [
    'head', 'neck', 'l_shoulder', 'r_shoulder',
    'l_elbow', 'r_elbow', 'l_hand', 'r_hand',
    'l_hip', 'r_hip', 'l_knee', 'r_knee',
    'l_foot', 'r_foot',
]

# --- 3x5 pixel font (minimal, for labels) ---
_FONT_3X5 = {
    'A': ['010','101','111','101','101'], 'B': ['110','101','110','101','110'],
    'C': ['011','100','100','100','011'], 'D': ['110','101','101','101','110'],
    'E': ['111','100','110','100','111'], 'F': ['111','100','110','100','100'],
    'G': ['011','100','101','101','011'], 'H': ['101','101','111','101','101'],
    'I': ['111','010','010','010','111'], 'J': ['111','001','001','101','010'],
    'K': ['101','110','100','110','101'], 'L': ['100','100','100','100','111'],
    'M': ['101','111','111','101','101'], 'N': ['101','111','111','111','101'],
    'O': ['010','101','101','101','010'], 'P': ['110','101','110','100','100'],
    'Q': ['010','101','101','011','001'], 'R': ['110','101','110','101','101'],
    'S': ['011','100','010','001','110'], 'T': ['111','010','010','010','010'],
    'U': ['101','101','101','101','010'], 'V': ['101','101','101','010','010'],
    'W': ['101','101','111','111','101'], 'X': ['101','101','010','101','101'],
    'Y': ['101','101','010','010','010'], 'Z': ['111','001','010','100','111'],
    '0': ['010','101','101','101','010'], '1': ['010','110','010','010','111'],
    '2': ['110','001','010','100','111'], '3': ['110','001','010','001','110'],
    '4': ['101','101','111','001','001'], '5': ['111','100','110','001','110'],
    '6': ['011','100','110','101','010'], '7': ['111','001','010','010','010'],
    '8': ['010','101','010','101','010'], '9': ['010','101','011','001','110'],
    ' ': ['000','000','000','000','000'], '.': ['000','000','000','000','010'],
    ':': ['000','010','000','010','000'], '(': ['010','100','100','100','010'],
    ')': ['010','001','001','001','010'], '-': ['000','000','111','000','000'],
    'X': ['101','101','010','101','101'],
}


# --- Simple buffer-based renderer ---
class Buffer:
    def __init__(self):
        self.buf = [[BLACK for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

    def clear(self):
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                self.buf[y][x] = BLACK

    def set_pixel(self, x, y, color):
        if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
            self.buf[y][x] = color

    def draw_line(self, x0, y0, x1, y1, color):
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.set_pixel(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def draw_text(self, x, y, text, color):
        cursor = x
        for char in text.upper():
            glyph = _FONT_3X5.get(char)
            if glyph:
                for row_idx, row in enumerate(glyph):
                    for col_idx, pixel in enumerate(row):
                        if pixel == '1':
                            self.set_pixel(cursor + col_idx, y + row_idx, color)
            cursor += 4

    def render_to(self, screen):
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                color = self.buf[y][x]
                rect = (x * SCALE, y * SCALE, SCALE, SCALE)
                pygame.draw.rect(screen, color, rect)


def draw_figure(buf, frame):
    """Draw stick figure from a frame dict."""
    # Ground line
    for x in range(10, 54):
        buf.set_pixel(x, 58, GROUND_COLOR)

    # Bones
    for j1, j2 in BONES:
        if j1 == 'head':
            continue
        x1, y1 = frame[j1]
        x2, y2 = frame[j2]
        is_torso = ((j1 == 'neck' and j2 in ('l_hip', 'r_hip'))
                    or (j1 == 'l_hip' and j2 == 'r_hip')
                    or (j1 == 'l_shoulder' and j2 == 'r_shoulder'))
        color = _color_scale(BODY_COLOR, 0.8) if is_torso else BODY_COLOR
        buf.draw_line(int(x1), int(y1), int(x2), int(y2), color)

    # Joints
    for name in JOINT_NAMES:
        if name == 'head':
            continue
        x, y = frame[name]
        buf.set_pixel(int(x), int(y), JOINT_COLOR)

    # Head
    hx, hy = frame['head']
    hx, hy = int(hx), int(hy)
    for ox, oy in HEAD_PIXELS:
        buf.set_pixel(hx + ox, hy + oy, HEAD_COLOR)
    for ox, oy in HEAD_OUTLINE_PIXELS:
        buf.set_pixel(hx + ox, hy + oy, HEAD_OUTLINE)


def _color_scale(color, scale):
    return (int(color[0] * scale), int(color[1] * scale), int(color[2] * scale))


def lerp_frame(frame_a, frame_b, t):
    """Interpolate between two frames."""
    result = {}
    for name in JOINT_NAMES:
        ax, ay = frame_a[name]
        bx, by = frame_b[name]
        result[name] = (ax + (bx - ax) * t, ay + (by - ay) * t)
    return result


def _load_clip(subject, clip_name, label_prefix=""):
    """Load a single clip through the full pipeline. Returns (label, frames, color) or None."""
    from build_walk_mocap import (download_walk_data, parse_asf, parse_amc,
                                   forward_kinematics_asf, extract_all_frames,
                                   normalize_mocap_to_screen, fix_limb_bends,
                                   JOINT_MAP, _JOINT_MAP_DEFAULTS)

    # Reset JOINT_MAP to defaults before each clip
    JOINT_MAP.clear()
    JOINT_MAP.update(_JOINT_MAP_DEFAULTS)

    asf_text, amc_text = download_walk_data(subject, clip_name)
    if not asf_text or not amc_text:
        return None

    bones, hierarchy, root_order, length_scale = parse_asf(asf_text)
    amc_frames = parse_amc(amc_text)

    # Check for missing joints and apply fallbacks
    sample_world = forward_kinematics_asf(bones, hierarchy, root_order,
                                          length_scale, amc_frames[0])
    missing = {our: cmu for our, cmu in JOINT_MAP.items() if cmu not in sample_world}
    if missing:
        alts = {'lwrist': ['lhand'], 'rwrist': ['rhand'],
                'lowerneck': ['upperneck', 'thorax'], 'head': ['upperneck']}
        for our_name, cmu_name in list(missing.items()):
            for alt in alts.get(cmu_name, []):
                if alt in sample_world:
                    JOINT_MAP[our_name] = alt
                    break

    try:
        all_frames = extract_all_frames(bones, hierarchy, root_order,
                                        length_scale, amc_frames)
        full_screen = normalize_mocap_to_screen(all_frames)
        full_screen = fix_limb_bends(full_screen)
        # Subsample 120fps → 30fps for playback
        full_30fps = full_screen[::4]
    except Exception as e:
        print(f"  {clip_name}: FAILED - {e}")
        return None

    label = f"{label_prefix}{clip_name}" if label_prefix else clip_name
    duration = len(full_30fps) / 30.0
    print(f"  {label}: {len(full_30fps)} frames ({duration:.1f}s)")
    return (label, full_30fps, (255, 200, 100))


def load_all_methods(subject=None, clip=None):
    """Generate all frame sets: procedural + 4 mocap methods."""
    print("Generating mocap data...", flush=True)

    from build_walk_mocap import (download_walk_data, parse_asf, parse_amc,
                                   forward_kinematics_asf, extract_all_frames,
                                   treadmill, detect_cycle,
                                   method_temporal, method_averaged,
                                   normalize_mocap_to_screen,
                                   fix_limb_bends, JOINT_MAP,
                                   _JOINT_MAP_DEFAULTS)

    # Reset JOINT_MAP to defaults
    JOINT_MAP.clear()
    JOINT_MAP.update(_JOINT_MAP_DEFAULTS)

    asf_text, amc_text = download_walk_data(subject, clip)
    if not asf_text or not amc_text:
        print("ERROR: Failed to download CMU data")
        sys.exit(1)

    bones, hierarchy, root_order, length_scale = parse_asf(asf_text)
    amc_frames = parse_amc(amc_text)

    # Check for missing joints and apply fallbacks
    sample_world = forward_kinematics_asf(bones, hierarchy, root_order,
                                          length_scale, amc_frames[0])
    missing = {our: cmu for our, cmu in JOINT_MAP.items() if cmu not in sample_world}
    if missing:
        alts = {'lwrist': ['lhand'], 'rwrist': ['rhand'],
                'lowerneck': ['upperneck', 'thorax'], 'head': ['upperneck']}
        for our_name, cmu_name in list(missing.items()):
            for alt in alts.get(cmu_name, []):
                if alt in sample_world:
                    JOINT_MAP[our_name] = alt
                    break

    all_frames = extract_all_frames(bones, hierarchy, root_order,
                                    length_scale, amc_frames)

    # Full clip: normalize without treadmill — preserves all natural motion
    full_screen = normalize_mocap_to_screen(all_frames)
    full_screen = fix_limb_bends(full_screen)
    # Subsample 120fps → 30fps for playback
    full_30fps = full_screen[::4]
    methods = [('FULL CLIP', full_30fps, (255, 200, 100))]
    print(f"  Full clip: {len(full_30fps)} frames ({len(full_30fps)/30:.1f}s)")

    # Cycle-based methods
    treadmilled = treadmill(all_frames)
    cycle_len, cycle_starts = detect_cycle(treadmilled)

    for key, label, color, method_fn in [
        ('B', 'CYCLE B',   (100, 200, 255), method_temporal),
        ('D', 'CYCLE D',   (200, 150, 255), method_averaged),
    ]:
        try:
            raw = method_fn(treadmilled, cycle_len, cycle_starts)
            screen = normalize_mocap_to_screen(raw)
            methods.append((label, screen, color))
            print(f"  {label}: {len(screen)} frames OK")
        except Exception as e:
            print(f"  {label}: FAILED - {e}")

    return methods


def load_gallery():
    """Load all cached clips as a gallery for comparison."""
    from pathlib import Path
    cache_dir = Path(os.path.dirname(os.path.abspath(__file__))) / '.dance_cache'

    if not cache_dir.exists():
        print("No cache directory found!")
        return []

    # Discover all cached AMC files, group by subject
    amc_files = sorted(cache_dir.glob('*.amc'))
    if not amc_files:
        print("No cached AMC files found!")
        return []

    # CMU clip descriptions for known subjects
    _CLIP_LABELS = {
        '14_01': 'BOXING',
        '35_01': 'WALK',
        '60_01': 'SALSA',
        '60_12': 'MOVEMENT',
        '85_09': 'HELICOPTER',
        '90_01': 'BACKFLIP',
        '90_27': 'MOONWALK',
        '135_03': 'FRONT KICK',
        '135_06': 'ROUNDHOUSE',
        '05_02': 'DANCE 02',
        '05_04': 'DANCE 04',
        '05_05': 'DANCE 05',
        '05_06': 'DANCE 06',
        '05_08': 'DANCE 08',
        '05_10': 'DANCE 10',
        '05_14': 'DANCE 14',
        '05_16': 'DANCE 16',
        '05_17': 'DANCE 17',
        '05_18': 'DANCE 18',
    }

    # Order: prioritize interesting new clips, then walk baseline, then dance/other
    _PRIORITY = {
        '135_03': 0, '135_06': 1,   # karate
        '90_01': 2, '90_27': 3,     # acrobatics
        '85_09': 4,                  # breakdance
        '14_01': 5,                  # boxing
        '35_01': 6,                  # walk (baseline)
        '60_01': 7, '60_12': 8,     # salsa/movement
    }
    amc_files = sorted(amc_files,
                       key=lambda p: _PRIORITY.get(p.stem, 100 + int(p.stem.split('_')[-1])))

    print(f"Loading gallery: {len(amc_files)} clips...", flush=True)
    gallery = []

    for amc_path in amc_files:
        clip_name = amc_path.stem  # e.g. "35_01"
        subject = clip_name.split('_')[0]

        # Check that matching ASF exists
        asf_path = cache_dir / f'{subject}.asf'
        if not asf_path.exists():
            print(f"  {clip_name}: skipped (no ASF)")
            continue

        label = _CLIP_LABELS.get(clip_name, clip_name.upper())
        result = _load_clip(subject, clip_name, label_prefix="")
        if result:
            # Override label with descriptive name
            _, frames, color = result
            # Color-code by subject
            colors = {
                '14': (255, 120, 120),   # red for boxing
                '35': (100, 255, 100),   # green for walk
                '60': (255, 200, 100),   # amber for salsa/movement
                '85': (255, 150, 255),   # pink for breakdance
                '90': (255, 255, 120),   # yellow for acrobatics
                '135': (120, 255, 255),  # cyan for karate
                '05': (150, 180, 255),   # blue for dance
            }
            c = colors.get(subject, (200, 200, 200))
            gallery.append((label, frames, c))

    print(f"Gallery loaded: {len(gallery)} clips")
    return gallery


def main():
    # Parse args
    subject = clip = None
    gallery_mode = False
    args = sys.argv[1:]
    if '--gallery' in args:
        gallery_mode = True
    if '--subject' in args:
        i = args.index('--subject')
        if i + 1 < len(args):
            subject = args[i + 1]
    if '--clip' in args:
        i = args.index('--clip')
        if i + 1 < len(args):
            clip = args[i + 1]

    if gallery_mode:
        methods = load_gallery()
    else:
        methods = load_all_methods(subject, clip)
    if not methods:
        print("No methods loaded!")
        sys.exit(1)

    pygame.init()
    screen = pygame.display.set_mode((GRID_SIZE * SCALE, GRID_SIZE * SCALE))
    pygame.display.set_caption("MoCap Walk Preview")
    clock = pygame.time.Clock()
    buf = Buffer()

    current_method = 0
    frame_float = 0.0
    speed = 1.0
    paused = False

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                elif event.key == pygame.K_RIGHT:
                    current_method = (current_method + 1) % len(methods)
                    frame_float = 0.0
                elif event.key == pygame.K_LEFT:
                    current_method = (current_method - 1) % len(methods)
                    frame_float = 0.0
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key in (pygame.K_EQUALS, pygame.K_PLUS):
                    speed = min(4.0, speed + 0.25)
                elif event.key == pygame.K_MINUS:
                    speed = max(0.25, speed - 0.25)

        dt = clock.tick(FPS) / 1000.0

        name, frames, label_color = methods[current_method]
        n = len(frames)

        if not paused:
            frame_float += dt * 30.0 * speed  # 30 fps base rate
            while frame_float >= n:
                frame_float -= n

        # Interpolate
        fi = int(frame_float)
        frac = frame_float - fi
        frame_a = frames[fi % n]
        frame_b = frames[(fi + 1) % n]
        current_frame = lerp_frame(frame_a, frame_b, frac)

        # Draw
        buf.clear()
        draw_figure(buf, current_frame)

        # Label
        buf.draw_text(2, 2, name, label_color)

        # Speed indicator
        if speed != 1.0:
            spd_str = f'{speed:.1f}X' if speed != int(speed) else f'{int(speed)}X'
            buf.draw_text(2, 58, spd_str, (100, 100, 100))

        # Pause indicator
        if paused:
            buf.draw_text(52, 58, 'II', (200, 100, 100))

        # Page indicator (dots)
        for i in range(len(methods)):
            x = 32 - (len(methods) * 2) + i * 4
            c = (200, 200, 200) if i == current_method else (60, 60, 60)
            buf.set_pixel(x, 62, c)

        buf.render_to(screen)
        pygame.display.flip()

    pygame.quit()


if __name__ == '__main__':
    main()
