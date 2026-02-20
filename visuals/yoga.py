"""
YOGA - Yoga Flows
==================
A stick figure flows through yoga poses with smooth interpolation.
14 joints, Vitruvian proportions. Poses sourced from MediaPipe datasets
(Manoj-2702) with hand-authored corrections.

Controls:
  Action       - Cycle flow (Sun Salute, Warrior, Balance)
  Left/Right   - Slow down / speed up
"""

from . import Visual, Display, Colors, GRID_SIZE

# ── Skeleton rig ──────────────────────────────────────────────────
JOINT_NAMES = [
    'head', 'neck', 'l_shoulder', 'r_shoulder', 'l_elbow', 'r_elbow',
    'l_hand', 'r_hand', 'l_hip', 'r_hip', 'l_knee', 'r_knee',
    'l_foot', 'r_foot',
]

BONES = [
    ('neck', 'l_shoulder'), ('neck', 'r_shoulder'),
    ('l_shoulder', 'r_shoulder'),
    ('l_shoulder', 'l_elbow'), ('l_elbow', 'l_hand'),
    ('r_shoulder', 'r_elbow'), ('r_elbow', 'r_hand'),
    ('neck', 'l_hip'), ('neck', 'r_hip'), ('l_hip', 'r_hip'),
    ('l_hip', 'l_knee'), ('l_knee', 'l_foot'),
    ('r_hip', 'r_knee'), ('r_knee', 'r_foot'),
]

HEAD_PIXELS = [
            (-1, -2), (0, -2), (1, -2),
    (-2, -1), (-1, -1), (0, -1), (1, -1), (2, -1),
    (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0),
    (-2, 1), (-1, 1), (0, 1), (1, 1), (2, 1),
            (-1, 2), (0, 2), (1, 2),
]
HEAD_OUTLINE_PIXELS = [
            (-1, -2), (0, -2), (1, -2),
    (-2, -1),                          (2, -1),
    (-2, 0),                           (2, 0),
    (-2, 1),                           (2, 1),
            (-1, 2), (0, 2), (1, 2),
]

# ── Colors ────────────────────────────────────────────────────────
BODY_COLOR = (220, 200, 170)
JOINT_COLOR = (255, 240, 210)
HEAD_COLOR = (255, 245, 220)
HEAD_OUTLINE = (180, 165, 140)
GROUND_COLOR = (40, 35, 28)
SHADOW_COLOR = (30, 25, 18)

# ── Baked poses (pixel coords on 64x64 grid) ─────────────────────
# fmt: off
POSES = {
    'Bound Angle': {'head':(32,10), 'neck':(32,22), 'l_shoulder':(43,22), 'r_shoulder':(22,22), 'l_elbow':(41,39), 'r_elbow':(23,39), 'l_hand':(38,52), 'r_hand':(27,53), 'l_hip':(38,47), 'r_hip':(26,47), 'l_knee':(60,47), 'r_knee':(2,49), 'l_foot':(37,55), 'r_foot':(27,56)},
    'Chair': {'head':(32,10), 'neck':(32,13), 'l_shoulder':(28,16), 'r_shoulder':(36,16), 'l_elbow':(28,9), 'r_elbow':(36,9), 'l_hand':(30,3), 'r_hand':(34,3), 'l_hip':(29,31), 'r_hip':(35,31), 'l_knee':(26,42), 'r_knee':(38,42), 'l_foot':(29,54), 'r_foot':(35,54)},
    'Dancer': {'head':(46,12), 'neck':(41,17), 'l_shoulder':(45,19), 'r_shoulder':(37,15), 'l_elbow':(54,19), 'r_elbow':(28,13), 'l_hand':(62,17), 'r_hand':(20,10), 'l_hip':(33,32), 'r_hip':(31,28), 'l_knee':(32,44), 'r_knee':(18,24), 'l_foot':(34,56), 'r_foot':(19,12)},
    'Downward Dog': {'head':(46,43), 'neck':(48,32), 'l_shoulder':(47,32), 'r_shoulder':(48,32), 'l_elbow':(52,42), 'r_elbow':(55,46), 'l_hand':(58,49), 'r_hand':(62,56), 'l_hip':(32,11), 'r_hip':(32,10), 'l_knee':(23,31), 'r_knee':(22,31), 'l_foot':(15,49), 'r_foot':(13,52)},
    'Forward Fold': {'head':(32,42), 'neck':(32,38), 'l_shoulder':(29,35), 'r_shoulder':(35,35), 'l_elbow':(29,42), 'r_elbow':(35,42), 'l_hand':(30,50), 'r_hand':(34,50), 'l_hip':(30,31), 'r_hip':(34,31), 'l_knee':(30,43), 'r_knee':(34,43), 'l_foot':(30,56), 'r_foot':(34,56)},
    'Goddess': {'head':(32,10), 'neck':(32,18), 'l_shoulder':(39,18), 'r_shoulder':(25,18), 'l_elbow':(49,20), 'r_elbow':(15,20), 'l_hand':(50,10), 'r_hand':(14,10), 'l_hip':(36,36), 'r_hip':(28,36), 'l_knee':(49,42), 'r_knee':(14,42), 'l_foot':(49,56), 'r_foot':(14,56)},
    'Half Lift': {'head':(32,27), 'neck':(32,28), 'l_shoulder':(29,30), 'r_shoulder':(35,30), 'l_elbow':(29,36), 'r_elbow':(35,36), 'l_hand':(30,42), 'r_hand':(34,42), 'l_hip':(30,31), 'r_hip':(34,31), 'l_knee':(30,43), 'r_knee':(34,43), 'l_foot':(30,56), 'r_foot':(34,56)},
    'Half Moon': {'head':(51,34), 'neck':(46,32), 'l_shoulder':(44,37), 'r_shoulder':(48,27), 'l_elbow':(44,47), 'r_elbow':(48,18), 'l_hand':(44,54), 'r_hand':(49,10), 'l_hip':(32,28), 'r_hip':(32,22), 'l_knee':(31,42), 'r_knee':(19,18), 'l_foot':(32,56), 'r_foot':(8,13)},
    'Low Lunge': {'head':(32,12), 'neck':(32,16), 'l_shoulder':(28,19), 'r_shoulder':(36,19), 'l_elbow':(26,27), 'r_elbow':(38,27), 'l_hand':(27,33), 'r_hand':(37,33), 'l_hip':(30,33), 'r_hip':(34,33), 'l_knee':(24,44), 'r_knee':(38,48), 'l_foot':(20,56), 'r_foot':(42,56)},
    'Mountain': {'head':(32,10), 'neck':(32,13), 'l_shoulder':(28,16), 'r_shoulder':(36,16), 'l_elbow':(27,24), 'r_elbow':(37,24), 'l_hand':(28,31), 'r_hand':(36,31), 'l_hip':(29,31), 'r_hip':(35,31), 'l_knee':(29,43), 'r_knee':(35,43), 'l_foot':(29,56), 'r_foot':(35,56)},
    'Tree': {'head':(32,18), 'neck':(33,22), 'l_shoulder':(38,22), 'r_shoulder':(27,22), 'l_elbow':(42,15), 'r_elbow':(23,16), 'l_hand':(33,10), 'r_hand':(30,10), 'l_hip':(36,36), 'r_hip':(28,36), 'l_knee':(34,47), 'r_knee':(16,42), 'l_foot':(32,56), 'r_foot':(30,45)},
    'Triangle': {'head':(46,25), 'neck':(43,31), 'l_shoulder':(44,36), 'r_shoulder':(42,26), 'l_elbow':(44,44), 'r_elbow':(41,18), 'l_hand':(44,53), 'r_hand':(42,10), 'l_hip':(33,36), 'r_hip':(31,33), 'l_knee':(39,46), 'r_knee':(26,44), 'l_foot':(44,55), 'r_foot':(23,56)},
    'Upward Salute': {'head':(32,8), 'neck':(32,12), 'l_shoulder':(28,16), 'r_shoulder':(36,16), 'l_elbow':(29,8), 'r_elbow':(35,8), 'l_hand':(31,2), 'r_hand':(33,2), 'l_hip':(29,31), 'r_hip':(35,31), 'l_knee':(29,43), 'r_knee':(35,43), 'l_foot':(29,56), 'r_foot':(35,56)},
    'Warrior': {'head':(29,10), 'neck':(32,18), 'l_shoulder':(37,18), 'r_shoulder':(27,18), 'l_elbow':(45,18), 'r_elbow':(20,16), 'l_hand':(52,18), 'r_hand':(12,15), 'l_hip':(35,37), 'r_hip':(29,37), 'l_knee':(43,46), 'r_knee':(18,40), 'l_foot':(53,56), 'r_foot':(18,55)},
}
# fmt: on

# ── Flows ─────────────────────────────────────────────────────────
FLOWS = [
    ('SUN SALUTE', [
        ('Mountain', 2.5), ('Upward Salute', 2.0), ('Forward Fold', 2.0),
        ('Half Lift', 1.5), ('Low Lunge', 2.0), ('Half Lift', 1.5),
        ('Forward Fold', 2.0), ('Upward Salute', 2.0), ('Mountain', 2.5),
    ]),
    ('WARRIOR', [
        ('Mountain', 2.0), ('Warrior', 3.0), ('Triangle', 3.0),
        ('Goddess', 3.0), ('Tree', 3.0),
        ('Upward Salute', 1.5), ('Mountain', 2.0),
    ]),
    ('BALANCE', [
        ('Mountain', 2.0), ('Tree', 3.0), ('Dancer', 3.0),
        ('Half Moon', 3.0), ('Warrior', 2.0),
        ('Upward Salute', 1.5), ('Mountain', 2.0),
    ]),
]

TRANSITION_TIME = 1.8
SPEED_MIN = 0.3
SPEED_MAX = 3.0
SPEED_STEP = 0.1


# ── Helpers ───────────────────────────────────────────────────────
def _ease(t):
    """Cubic ease-in-out."""
    t = max(0.0, min(1.0, t))
    if t < 0.5:
        return 4 * t * t * t
    return 1 - (-2 * t + 2) ** 3 / 2


def _lerp(a, b, t):
    return a + (b - a) * t


def _color_scale(color, s):
    return (int(color[0] * s), int(color[1] * s), int(color[2] * s))


# ── Visual class ──────────────────────────────────────────────────
class Yoga(Visual):
    name = "YOGA"
    description = "Yoga flows"
    category = "household"

    def reset(self):
        self.time = 0.0
        self._flow_idx = 0
        self._pose_idx = 0
        self._pose_time = 0.0
        self._transitioning = False
        self._trans_time = 0.0
        self._speed = 1.0
        self._overlay_timer = 0.0
        self._init_positions()

    def _init_positions(self):
        flow_name, flow = FLOWS[self._flow_idx]
        pose = POSES[flow[0][0]]
        self._drawn_pos = {}
        self._float_pos = {}
        for name in JOINT_NAMES:
            p = pose[name]
            self._drawn_pos[name] = (int(p[0]), int(p[1]))
            self._float_pos[name] = (float(p[0]), float(p[1]))

    def handle_input(self, input_state):
        consumed = False

        if input_state.action_l or input_state.action_r:
            self._flow_idx = (self._flow_idx + 1) % len(FLOWS)
            self._pose_idx = 0
            self._pose_time = 0.0
            self._transitioning = False
            self._trans_time = 0.0
            self._init_positions()
            self._overlay_timer = 2.0
            consumed = True

        if input_state.left_pressed:
            self._speed = max(SPEED_MIN, self._speed - SPEED_STEP)
            self._overlay_timer = 2.0
            consumed = True
        elif input_state.right_pressed:
            self._speed = min(SPEED_MAX, self._speed + SPEED_STEP)
            self._overlay_timer = 2.0
            consumed = True

        return consumed

    def update(self, dt):
        self.time += dt
        sdt = dt * self._speed

        flow_name, flow = FLOWS[self._flow_idx]
        n_poses = len(flow)

        if self._transitioning:
            self._trans_time += sdt
            if self._trans_time >= TRANSITION_TIME:
                self._transitioning = False
                self._pose_idx = (self._pose_idx + 1) % n_poses
                self._pose_time = 0.0
        else:
            self._pose_time += sdt
            if self._pose_time >= flow[self._pose_idx][1]:
                self._transitioning = True
                self._trans_time = 0.0

        # Compute target joint positions
        pose_name = flow[self._pose_idx][0]
        cur_pose = POSES[pose_name]

        if self._transitioning:
            ni = (self._pose_idx + 1) % n_poses
            next_name = flow[ni][0]
            next_pose = POSES[next_name]
            t = _ease(self._trans_time / TRANSITION_TIME)
            for name in JOINT_NAMES:
                fx = _lerp(cur_pose[name][0], next_pose[name][0], t)
                fy = _lerp(cur_pose[name][1], next_pose[name][1], t)
                self._float_pos[name] = (fx, fy)
        else:
            for name in JOINT_NAMES:
                self._float_pos[name] = (float(cur_pose[name][0]),
                                         float(cur_pose[name][1]))

        # Hysteresis: only update drawn pixel when float moves >0.55px
        for name in JOINT_NAMES:
            fx, fy = self._float_pos[name]
            dx, dy = self._drawn_pos[name]
            if (fx - dx) ** 2 + (fy - dy) ** 2 > 0.55 * 0.55:
                self._drawn_pos[name] = (int(round(fx)), int(round(fy)))

        if self._overlay_timer > 0:
            self._overlay_timer = max(0, self._overlay_timer - dt)

    def draw(self):
        d = self.display
        d.clear()

        # Ground line
        for x in range(10, 54):
            d.set_pixel(x, 58, GROUND_COLOR)

        # Shadow
        for foot in ('l_foot', 'r_foot'):
            fx, fy = self._drawn_pos[foot]
            for dx in range(-1, 2):
                px = fx + dx
                if 0 <= px < GRID_SIZE:
                    alpha = 0.5 if dx == 0 else 0.3
                    c = _color_scale(SHADOW_COLOR, alpha / 0.5)
                    d.set_pixel(px, 57, c)

        # Bones
        for j1, j2 in BONES:
            x1, y1 = self._drawn_pos[j1]
            x2, y2 = self._drawn_pos[j2]
            is_torso = ((j1 == 'neck' and j2 in ('l_hip', 'r_hip'))
                        or (j1 == 'l_hip' and j2 == 'r_hip')
                        or (j1 == 'l_shoulder' and j2 == 'r_shoulder'))
            color = _color_scale(BODY_COLOR, 0.8) if is_torso else BODY_COLOR
            d.draw_line(x1, y1, x2, y2, color)

        # Joints
        for name in JOINT_NAMES:
            if name == 'head':
                continue
            x, y = self._drawn_pos[name]
            if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                d.set_pixel(x, y, JOINT_COLOR)

        # Head
        hx, hy = self._drawn_pos['head']
        for ox, oy in HEAD_PIXELS:
            px, py = hx + ox, hy + oy
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                d.set_pixel(px, py, HEAD_COLOR)
        for ox, oy in HEAD_OUTLINE_PIXELS:
            px, py = hx + ox, hy + oy
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                d.set_pixel(px, py, HEAD_OUTLINE)

        # Pose name (always shown, subtle)
        flow_name, flow = FLOWS[self._flow_idx]
        if self._transitioning:
            t = self._trans_time / TRANSITION_TIME
            ni = (self._pose_idx + 1) % len(flow)
            dname = flow[ni][0] if t > 0.5 else flow[self._pose_idx][0]
        else:
            dname = flow[self._pose_idx][0]
        d.draw_text_small(2, 2, dname.upper(), (80, 72, 56))

        # Overlay (flow name + speed on button press)
        if self._overlay_timer > 0:
            alpha = min(1.0, self._overlay_timer / 0.5)
            spd = f'{self._speed:.1f}x' if self._speed != int(self._speed) else f'{int(self._speed)}x'
            oc = (int(200 * alpha), int(200 * alpha), int(200 * alpha))
            d.draw_text_small(2, 57, f"{flow_name} {spd}", oc)
