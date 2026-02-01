"""
Pinball - LED Arcade
====================
Scrolling 64x192 virtual playfield on a 64x64 LED matrix.
Physics inspired by 3D Pinball: Space Cadet — field-effect gravity with
speed-proportional drag, separated direction/speed model, elasticity +
smoothness collision, distance-scaled flipper momentum.

Controls:
  Space (held)  - Left flipper
  Z (held)      - Right flipper
  Down (held)   - Charge plunger
  Down (release) - Launch ball
"""

import math
import random
from arcade import Game, GameState, Display, Colors, InputState

# Phases
PHASE_PLUNGER = 0
PHASE_PLAYING = 1
PHASE_DRAIN = 2
PHASE_BALL_OVER = 3

# Table dimensions
TABLE_W = 64
TABLE_H = 192
SCREEN_H = 64

# ---------------------------------------------------------------------------
# Physics — modelled after Space Cadet's field-effect system
# ---------------------------------------------------------------------------
GRAVITY_STRENGTH = 28.0    # base gravity magnitude (SC default ~25)
GRAVITY_DRAG = 0.25        # speed-proportional drag (reduced from SC ~0.5 for smaller table)
SPEED_CAP = 350.0
BALL_RADIUS = 1.5
SUBSTEPS = 4

# Collision material defaults (SC: elasticity 0.6, smoothness 0.95)
ELASTICITY = 0.6
SMOOTHNESS = 0.95
WALL_ELASTICITY = 0.65
WALL_SMOOTHNESS = 0.9

# Ball
BALL_START_X = 60.0
BALL_START_Y = 180.0

# Plunger — charges on 0.025s ticks like SC, ±10% launch randomness
PLUNGER_CHUTE_LEFT = 57
PLUNGER_CHUTE_TOP = 155
PLUNGER_MAX_SPEED = 300.0
PLUNGER_CHARGE_RATE = 1.6   # 0→1 per second
PLUNGER_QUICK_FRAC = 0.65

# Chute exit: curved rail from (62, 8) down to (CHUTE_LEFT, CHUTE_TOP)
# Modelled as arc segments the ball rolls along
CHUTE_RAIL = [
    # (x0,y0, x1,y1) — segments of the curved top rail, right to left
    (62, 4, 54, 2),
    (54, 2, 40, 2),
    (40, 2, 30, 4),
]

# Flippers — SC-style with distance-scaled momentum and front/back
FLIPPER_LEFT_PIVOT = (18.0, 173.0)
FLIPPER_RIGHT_PIVOT = (45.0, 173.0)
FLIPPER_LENGTH = 11.0
FLIPPER_REST_LEFT = 0.50       # tips down-outward
FLIPPER_REST_RIGHT = math.pi - 0.50
FLIPPER_ACTIVE_LEFT = -0.55    # tips up-inward
FLIPPER_ACTIVE_RIGHT = math.pi + 0.55
FLIPPER_EXTEND_SPEED = 18.0    # rad/s (fast snap up)
FLIPPER_RETRACT_SPEED = 10.0   # rad/s (slower return)
FLIPPER_COLLISION_MULT = 1.6   # SC CollisionMult — boost on active face
FLIPPER_TIP_RADIUS = 1.5
FLIPPER_BASE_RADIUS = 2.0

# Bumpers — SC-style: boost added to elastic reflection
BUMPER_BOOST = 100.0           # additional kick in collision normal direction
BUMPER_COOLDOWN = 0.08

# Scoring (inspired by SC tier system)
BUMPER_PTS_BASE = 500
BUMPER_PTS_HOT = 1500
ROLLOVER_PTS = 500
ROLLOVER_ALL_BONUS = 5000
SPINNER_PTS = 75
DROP_TARGET_PTS = 750
DROP_RESET_BONUS = 5000
SLINGSHOT_PTS = 25
SKILL_SHOT_PTS = [0, 5000, 15000, 25000]  # by # lights passed

# Drain
DRAIN_Y = 186

# Camera
CAMERA_LERP = 0.12
CAMERA_LEAD = 0.15


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def _closest_point_on_seg(px, py, x0, y0, x1, y1):
    dx, dy = x1 - x0, y1 - y0
    len_sq = dx * dx + dy * dy
    if len_sq < 0.0001:
        return x0, y0
    t = max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy) / len_sq))
    return x0 + t * dx, y0 + t * dy


def _dot(ax, ay, bx, by):
    return ax * bx + ay * by


def _mag(x, y):
    return math.sqrt(x * x + y * y)


def _normalize(x, y):
    m = _mag(x, y)
    if m < 0.0001:
        return 0.0, 0.0, 0.0
    return x / m, y / m, m


# ---------------------------------------------------------------------------
# SC-style basic_collision:  direction/speed separated, elasticity+smoothness
# ---------------------------------------------------------------------------

def _basic_collision(bvx, bvy, nx, ny, elasticity, smoothness, boost=0.0):
    """
    Reflect ball velocity off surface with normal (nx,ny).
    Returns new (bvx, bvy).
    SC formula: tangential scaled by smoothness, normal reflected by elasticity,
    then optional boost added along normal.
    """
    speed = _mag(bvx, bvy)
    if speed < 0.1:
        # Just apply boost if any
        return bvx + nx * boost, bvy + ny * boost

    # Decompose into normal & tangential
    dx, dy = bvx / speed, bvy / speed
    rebound_proj = -_dot(nx, ny, dx, dy)

    if rebound_proj <= 0:
        # Not approaching — just apply boost
        return bvx + nx * boost, bvy + ny * boost

    # SC formula: reconstruct direction
    dx1 = rebound_proj * nx
    dy1 = rebound_proj * ny
    new_dx = (dx1 + dx) * smoothness + dx1 * elasticity
    new_dy = (dy1 + dy) * smoothness + dy1 * elasticity
    ndx, ndy, _ = _normalize(new_dx, new_dy)

    # Reduce speed by energy loss
    new_speed = speed - (1.0 - elasticity) * rebound_proj * speed
    new_speed = max(new_speed, 0.0)

    # Apply boost along normal if rebound was strong enough
    out_vx = ndx * new_speed + nx * boost
    out_vy = ndy * new_speed + ny * boost

    return out_vx, out_vy


# ---------------------------------------------------------------------------
# Static wall segments for line-segment collision
# ---------------------------------------------------------------------------

def _build_wall_segments():
    segs = []
    # Left outer wall
    segs.append((1, 0, 1, 191))
    # Right outer wall (above chute)
    segs.append((62, 0, 62, PLUNGER_CHUTE_TOP))
    # Top wall
    segs.append((1, 1, 62, 1))
    # Chute left wall
    segs.append((PLUNGER_CHUTE_LEFT, PLUNGER_CHUTE_TOP, PLUNGER_CHUTE_LEFT, 191))
    # Chute right wall
    segs.append((62, PLUNGER_CHUTE_TOP, 62, 191))
    # Chute exit curved rail segments
    for seg in CHUTE_RAIL:
        segs.append(seg)
    # Guide walls funneling to flippers
    segs.append((1, 148, 10, 168))
    segs.append((62, 148, 53, 168))
    # Return lane walls (continue funnel to just above flipper pivots)
    segs.append((10, 168, 17, 174))
    segs.append((53, 168, 46, 174))
    return segs

WALL_SEGMENTS = _build_wall_segments()


# ===========================================================================
# Flipper
# ===========================================================================

class Flipper:
    def __init__(self, px, py, length, rest, active, side):
        self.px = px
        self.py = py
        self.length = length
        self.rest_angle = rest
        self.active_angle = active
        self.angle = rest
        self.prev_angle = rest
        self.angular_vel = 0.0
        self.side = side

    def update(self, pressed, dt):
        self.prev_angle = self.angle
        target = self.active_angle if pressed else self.rest_angle
        diff = target - self.angle
        if abs(diff) < 0.02:
            self.angle = target
            self.angular_vel = 0.0
            return
        speed = FLIPPER_EXTEND_SPEED if pressed else FLIPPER_RETRACT_SPEED
        direction = 1.0 if diff > 0 else -1.0
        self.angular_vel = direction * speed
        self.angle += self.angular_vel * dt
        # Clamp to range
        lo = min(self.rest_angle, self.active_angle)
        hi = max(self.rest_angle, self.active_angle)
        self.angle = max(lo, min(hi, self.angle))

    def tip(self):
        return (self.px + math.cos(self.angle) * self.length,
                self.py + math.sin(self.angle) * self.length)

    def collide_ball(self, bx, by, bvx, bvy):
        """SC-style: distance-scaled momentum, front/back distinction."""
        tx, ty = self.tip()
        cx, cy = _closest_point_on_seg(bx, by, self.px, self.py, tx, ty)
        dx, dy = bx - cx, by - cy
        dist = _mag(dx, dy)
        min_dist = BALL_RADIUS + 1.0
        if dist >= min_dist or dist < 0.001:
            return None

        nx, ny = dx / dist, dy / dist
        # Push out
        overlap = min_dist - dist
        bx += nx * overlap
        by += ny * overlap

        # Distance from pivot (0..1), affects momentum transfer
        rx, ry = cx - self.px, cy - self.py
        dist_from_pivot_sq = rx * rx + ry * ry
        dist_div_sq = self.length * self.length
        dist_frac = math.sqrt(min(dist_from_pivot_sq / dist_div_sq, 1.0))

        # Surface velocity at contact point
        surf_vx = -self.angular_vel * ry
        surf_vy = self.angular_vel * rx

        # Is flipper swinging toward ball? (front hit vs back hit)
        is_active_hit = abs(self.angular_vel) > 1.0

        if is_active_hit:
            # Front hit: boost scales with distance from pivot (tip = max)
            flip_speed = abs(self.angular_vel) * math.sqrt(dist_from_pivot_sq)
            boost = FLIPPER_COLLISION_MULT * flip_speed * dist_frac

            # Reflect off surface with boost
            bvx, bvy = _basic_collision(
                bvx - surf_vx, bvy - surf_vy, nx, ny,
                ELASTICITY, SMOOTHNESS, boost)
            bvx += surf_vx * 0.3
            bvy += surf_vy * 0.3
        else:
            # Back/passive hit: reduced elasticity, ball just bounces weakly
            reduced_e = ELASTICITY * (1.0 - dist_frac * 0.5)
            bvx, bvy = _basic_collision(
                bvx, bvy, nx, ny, reduced_e, SMOOTHNESS)

        return bx, by, bvx, bvy


# ===========================================================================
# Bumper — SC-style: elastic reflection + boost, cooldown timer
# ===========================================================================

class Bumper:
    def __init__(self, x, y, radius, points=BUMPER_PTS_BASE):
        self.x = float(x)
        self.y = float(y)
        self.radius = float(radius)
        self.points = points
        self.flash = 0.0
        self.cooldown = 0.0

    def update(self, dt):
        if self.flash > 0:
            self.flash -= dt
        if self.cooldown > 0:
            self.cooldown -= dt

    def collide_ball(self, bx, by, bvx, bvy):
        if self.cooldown > 0:
            return None
        dx, dy = bx - self.x, by - self.y
        dist = _mag(dx, dy)
        min_dist = self.radius + BALL_RADIUS
        if dist >= min_dist or dist < 0.001:
            return None
        nx, ny = dx / dist, dy / dist
        # Push out
        bx = self.x + nx * min_dist
        by = self.y + ny * min_dist
        # SC-style: reflect + boost (not override)
        bvx, bvy = _basic_collision(bvx, bvy, nx, ny,
                                    ELASTICITY, SMOOTHNESS, BUMPER_BOOST)
        self.flash = 0.12
        self.cooldown = BUMPER_COOLDOWN
        return bx, by, bvx, bvy, self.points


# ===========================================================================
# Drop Target
# ===========================================================================

class DropTarget:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.active = True

    def collide_ball(self, bx, by, bvx, bvy):
        if not self.active:
            return None
        if abs(bx - self.x) < 2.5 and abs(by - self.y) < 2.5:
            self.active = False
            # Reflect ball upward with elasticity
            nx, ny = 0.0, -1.0
            bvx, bvy = _basic_collision(bvx, bvy, nx, ny, 0.5, 0.8, 20.0)
            return bvx, bvy
        return None


# ===========================================================================
# Rollover Lane
# ===========================================================================

class RolloverLane:
    def __init__(self, x, y_top, y_bottom, width=4):
        self.x = float(x)
        self.y_top = float(y_top)
        self.y_bottom = float(y_bottom)
        self.width = float(width)
        self.lit = False

    def check(self, bx, by):
        if not self.lit and abs(bx - self.x) < self.width / 2:
            if self.y_top <= by <= self.y_bottom:
                self.lit = True
                return True
        return False


# ===========================================================================
# Pinball Game
# ===========================================================================

class Pinball(Game):
    name = "PINBALL"
    description = "Scrolling pinball with flippers and bumpers"
    category = "bar"

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.phase = PHASE_PLUNGER
        self.score = 0
        self.balls_left = 3
        self.ball_number = 1

        # Ball — direction/speed separated like SC
        self.ball_x = BALL_START_X
        self.ball_y = BALL_START_Y
        self.ball_vx = 0.0
        self.ball_vy = 0.0

        # Plunger
        self.plunger_charge = 0.0
        self.plunger_charging = False

        # Skill shot tracking
        self.skill_lights_passed = 0
        self.skill_shot_active = True

        # Flippers
        self.flipper_l = Flipper(
            *FLIPPER_LEFT_PIVOT, FLIPPER_LENGTH,
            FLIPPER_REST_LEFT, FLIPPER_ACTIVE_LEFT, 'left')
        self.flipper_r = Flipper(
            *FLIPPER_RIGHT_PIVOT, FLIPPER_LENGTH,
            FLIPPER_REST_RIGHT, FLIPPER_ACTIVE_RIGHT, 'right')

        # Camera
        self.camera_y = float(TABLE_H - SCREEN_H)

        # Bumpers — top zone pop bumpers (3 like SC attack bumpers)
        self.bumpers = [
            Bumper(20, 38, 3, BUMPER_PTS_BASE),
            Bumper(44, 38, 3, BUMPER_PTS_BASE),
            Bumper(32, 28, 3, BUMPER_PTS_BASE),
            # Mid zone cluster
            Bumper(32, 72, 4, BUMPER_PTS_BASE),
            Bumper(18, 90, 4, BUMPER_PTS_BASE),
            Bumper(46, 90, 4, BUMPER_PTS_BASE),
        ]
        # Bumper upgrade tier (SC: blue→green→yellow→red)
        self.bumper_tier = 0  # 0-3
        self.bumper_tier_timer = 0.0

        # Rollover lanes (3 re-entry lanes like SC)
        self.rollovers = [
            RolloverLane(16, 6, 16),
            RolloverLane(32, 6, 16),
            RolloverLane(48, 6, 16),
        ]

        # Spinner
        self.spinner_x = 32.0
        self.spinner_y = 52.0
        self.spinner_angle = 0.0
        self.spinner_speed = 0.0

        # Drop targets (3 like SC medal targets)
        self.drop_targets = [
            DropTarget(14, 108),
            DropTarget(32, 108),
            DropTarget(50, 108),
        ]
        self.drops_cleared = 0  # times all 3 cleared

        # One-way gate
        self.gate_y = 60.0

        # Slingshot cooldowns
        self.sling_l_timer = 0.0
        self.sling_r_timer = 0.0

        # Phase timer
        self.phase_timer = 0.0
        # Play timer (for tilt bias)
        self.play_time = 0.0

        # Multiplier (SC-style, earned by clearing drop targets)
        self.multiplier = 1

        # Ball in chute flag
        self.in_chute = True

        # Stall timer: nudge ball if nearly stopped (simulates table tilt)
        self.stall_time = 0.0

    def _reset_ball(self):
        self.ball_x = BALL_START_X
        self.ball_y = BALL_START_Y
        self.ball_vx = 0.0
        self.ball_vy = 0.0
        self.plunger_charge = 0.0
        self.plunger_charging = False
        self.in_chute = True
        self.skill_shot_active = True
        self.skill_lights_passed = 0
        self.play_time = 0.0
        self.phase = PHASE_PLUNGER

    def _add_score(self, pts):
        self.score += pts * self.multiplier

    def _launch_ball(self, power):
        power = max(0.15, min(1.0, power))
        # SC-style ±10% random variation
        variation = 1.0 + random.uniform(-0.1, 0.1)
        speed = PLUNGER_MAX_SPEED * power * variation
        self.ball_vy = -speed
        self.ball_vx = random.uniform(-2, 2)
        self.phase = PHASE_PLAYING

    # ===== PHYSICS =====

    def _field_effect(self, dt):
        """SC-style gravity: constant downward + speed-proportional drag."""
        speed = _mag(self.ball_vx, self.ball_vy)

        # Gravity (table tilted toward player = positive Y)
        # After 10s, gradually increase gravity to prevent infinite orbits
        tilt_bonus = min(15.0, max(0.0, (self.play_time - 10.0) * 1.5))
        self.ball_vy += (GRAVITY_STRENGTH + tilt_bonus) * dt

        # Speed-proportional drag: higher speed = more resistance
        if speed > 0.5:
            drag = GRAVITY_DRAG * dt
            self.ball_vx -= self.ball_vx * drag
            self.ball_vy -= self.ball_vy * drag

    def _physics_step(self, dt):
        # Field effect (gravity + drag)
        self._field_effect(dt)

        # Move ball
        self.ball_x += self.ball_vx * dt
        self.ball_y += self.ball_vy * dt

        # Speed cap
        spd = _mag(self.ball_vx, self.ball_vy)
        if spd > SPEED_CAP:
            f = SPEED_CAP / spd
            self.ball_vx *= f
            self.ball_vy *= f

        # Collisions
        self._collide_walls()
        self._collide_bumpers()
        self._collide_flippers()
        self._check_targets()
        self._check_rollovers()
        self._check_spinner(dt)
        self._check_one_way_gate()
        self._check_slingshots()

    def _collide_walls(self):
        """Collide against boundary walls and static line segments."""
        if self.in_chute:
            # Chute walls
            if self.ball_x < PLUNGER_CHUTE_LEFT + BALL_RADIUS:
                self.ball_x = PLUNGER_CHUTE_LEFT + BALL_RADIUS
                self.ball_vx, self.ball_vy = _basic_collision(
                    self.ball_vx, self.ball_vy, 1, 0,
                    WALL_ELASTICITY, WALL_SMOOTHNESS)
            if self.ball_x > 61 - BALL_RADIUS:
                self.ball_x = 61 - BALL_RADIUS
                self.ball_vx, self.ball_vy = _basic_collision(
                    self.ball_vx, self.ball_vy, -1, 0,
                    WALL_ELASTICITY, WALL_SMOOTHNESS)
            # Exit chute: ball rises above chute top
            if self.ball_y < PLUNGER_CHUTE_TOP:
                self.in_chute = False
                # Skill shot: award based on how many lights ball passed
                if self.skill_shot_active:
                    # Count rollover lights the ball is near at exit
                    idx = min(self.skill_lights_passed, len(SKILL_SHOT_PTS) - 1)
                    if idx > 0:
                        self._add_score(SKILL_SHOT_PTS[idx])
                    self.skill_shot_active = False
            return

        # Main playfield walls — use line segment collisions for everything
        for x0, y0, x1, y1 in WALL_SEGMENTS:
            cx, cy = _closest_point_on_seg(
                self.ball_x, self.ball_y, x0, y0, x1, y1)
            dx, dy = self.ball_x - cx, self.ball_y - cy
            dist = _mag(dx, dy)
            min_dist = BALL_RADIUS + 0.5
            if dist < min_dist and dist > 0.001:
                nx, ny = dx / dist, dy / dist
                overlap = min_dist - dist
                self.ball_x += nx * overlap
                self.ball_y += ny * overlap
                self.ball_vx, self.ball_vy = _basic_collision(
                    self.ball_vx, self.ball_vy, nx, ny,
                    WALL_ELASTICITY, WALL_SMOOTHNESS)

        # Extra: right boundary below chute top (the divider wall)
        if self.ball_y >= PLUNGER_CHUTE_TOP:
            chute_wall_x = PLUNGER_CHUTE_LEFT - BALL_RADIUS - 0.5
            if self.ball_x > chute_wall_x:
                self.ball_x = chute_wall_x
                self.ball_vx, self.ball_vy = _basic_collision(
                    self.ball_vx, self.ball_vy, -1, 0,
                    WALL_ELASTICITY, WALL_SMOOTHNESS)

    def _collide_bumpers(self):
        for bumper in self.bumpers:
            result = bumper.collide_ball(
                self.ball_x, self.ball_y, self.ball_vx, self.ball_vy)
            if result:
                self.ball_x, self.ball_y, self.ball_vx, self.ball_vy, pts = result
                # SC: bumper points scale with tier
                tier_mult = [1, 2, 4, 8][min(self.bumper_tier, 3)]
                self._add_score(pts * tier_mult)

    def _collide_flippers(self):
        for flipper in [self.flipper_l, self.flipper_r]:
            result = flipper.collide_ball(
                self.ball_x, self.ball_y, self.ball_vx, self.ball_vy)
            if result:
                self.ball_x, self.ball_y, self.ball_vx, self.ball_vy = result

    def _check_targets(self):
        for target in self.drop_targets:
            result = target.collide_ball(
                self.ball_x, self.ball_y, self.ball_vx, self.ball_vy)
            if result:
                self.ball_vx, self.ball_vy = result
                self._add_score(DROP_TARGET_PTS)
        # All cleared — bonus + reset (SC medal target system)
        if all(not t.active for t in self.drop_targets):
            self.drops_cleared += 1
            self._add_score(DROP_RESET_BONUS)
            # Increase multiplier (SC: 2x→3x→5x→10x)
            mult_table = [1, 2, 3, 5, 10]
            self.multiplier = mult_table[min(self.drops_cleared, len(mult_table) - 1)]
            for t in self.drop_targets:
                t.active = True

    def _check_rollovers(self):
        for lane in self.rollovers:
            if lane.check(self.ball_x, self.ball_y):
                self._add_score(ROLLOVER_PTS)
                # Track for skill shot
                if self.skill_shot_active:
                    self.skill_lights_passed += 1
        # All 3 lit: upgrade bumpers (SC re-entry lane mechanic)
        if all(l.lit for l in self.rollovers):
            self.bumper_tier = min(self.bumper_tier + 1, 3)
            self.bumper_tier_timer = 60.0  # SC: degrades after 60s
            for l in self.rollovers:
                l.lit = False

    def _check_spinner(self, dt):
        dx = self.ball_x - self.spinner_x
        dy = self.ball_y - self.spinner_y
        if abs(dx) < 3 and abs(dy) < 3:
            spd = _mag(self.ball_vx, self.ball_vy)
            if spd > 15:
                self.spinner_speed = spd * 0.08
                self._add_score(SPINNER_PTS)
        if self.spinner_speed > 0:
            self.spinner_angle += self.spinner_speed * dt
            self.spinner_speed *= 0.94

    def _check_one_way_gate(self):
        # Ball falls DOWN freely. Blocks UPWARD re-entry to top bonus zone
        # (like a real pinball orbit gate). Strong flipper shots can punch through.
        if (self.gate_y - 1.0 < self.ball_y < self.gate_y + 1.0 and
                self.ball_vy < -15 and 8 < self.ball_x < 55):
            # Weak upward motion: reflect back down
            self.ball_y = self.gate_y + 1.5
            self.ball_vx, self.ball_vy = _basic_collision(
                self.ball_vx, self.ball_vy, 0, 1,
                0.3, 0.85)

    def _check_slingshots(self):
        # Left slingshot — only fires when ball approaches from right (vx < 0)
        if (8 < self.ball_x < 14 and 140 < self.ball_y < 168 and
                self.sling_l_timer <= 0 and self.ball_vx < -5):
            cx, cy = _closest_point_on_seg(
                self.ball_x, self.ball_y, 8, 152, 14, 168)
            dx, dy = self.ball_x - cx, self.ball_y - cy
            dist = _mag(dx, dy)
            if dist < BALL_RADIUS + 1.5 and dist > 0.001:
                nx, ny = dx / dist, dy / dist
                self.ball_vx, self.ball_vy = _basic_collision(
                    self.ball_vx, self.ball_vy, nx, ny,
                    0.8, 0.9, 60.0)
                self._add_score(SLINGSHOT_PTS)
                self.sling_l_timer = 0.3
        # Right slingshot — only fires when ball approaches from left (vx > 0)
        if (49 < self.ball_x < 55 and 140 < self.ball_y < 168 and
                self.sling_r_timer <= 0 and self.ball_vx > 5):
            cx, cy = _closest_point_on_seg(
                self.ball_x, self.ball_y, 55, 152, 49, 168)
            dx, dy = self.ball_x - cx, self.ball_y - cy
            dist = _mag(dx, dy)
            if dist < BALL_RADIUS + 1.5 and dist > 0.001:
                nx, ny = dx / dist, dy / dist
                self.ball_vx, self.ball_vy = _basic_collision(
                    self.ball_vx, self.ball_vy, nx, ny,
                    0.8, 0.9, 60.0)
                self._add_score(SLINGSHOT_PTS)
                self.sling_r_timer = 0.3

    # ===== CAMERA =====

    def _update_camera(self, dt):
        target_y = self.ball_y - SCREEN_H / 2 + self.ball_vy * CAMERA_LEAD
        target_y = max(0.0, min(float(TABLE_H - SCREEN_H), target_y))
        self.camera_y += (target_y - self.camera_y) * CAMERA_LERP
        self.camera_y = max(0.0, min(float(TABLE_H - SCREEN_H), self.camera_y))

    # ===== UPDATE =====

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return
        if self.phase == PHASE_PLUNGER:
            self._update_plunger(input_state, dt)
        elif self.phase == PHASE_PLAYING:
            self._update_playing(input_state, dt)
        elif self.phase == PHASE_DRAIN:
            self._update_drain(dt)
        elif self.phase == PHASE_BALL_OVER:
            self._update_ball_over(input_state, dt)

    def _update_plunger(self, inp, dt):
        self.flipper_l.update(inp.action_l_held, dt)
        self.flipper_r.update(inp.action_r_held, dt)

        if inp.down:
            self.plunger_charging = True
            self.plunger_charge = min(1.0, self.plunger_charge + PLUNGER_CHARGE_RATE * dt)
        elif self.plunger_charging:
            self._launch_ball(self.plunger_charge)
            self.plunger_charge = 0.0
            self.plunger_charging = False

        # Quick launch with button (no charge needed)
        if (inp.action_l or inp.action_r) and not self.plunger_charging:
            self._launch_ball(PLUNGER_QUICK_FRAC)

        self._update_camera(dt)

    def _update_playing(self, inp, dt):
        self.flipper_l.update(inp.action_l_held, dt)
        self.flipper_r.update(inp.action_r_held, dt)

        for b in self.bumpers:
            b.update(dt)
        if self.sling_l_timer > 0:
            self.sling_l_timer -= dt
        if self.sling_r_timer > 0:
            self.sling_r_timer -= dt

        # Bumper tier decay (SC: degrades after 60s)
        if self.bumper_tier > 0:
            self.bumper_tier_timer -= dt
            if self.bumper_tier_timer <= 0:
                self.bumper_tier = max(0, self.bumper_tier - 1)
                self.bumper_tier_timer = 60.0

        self.play_time += dt

        sub_dt = dt / SUBSTEPS
        for _ in range(SUBSTEPS):
            self._physics_step(sub_dt)

        # Stall detection: if ball barely moving for 2s, nudge toward drain
        spd_now = _mag(self.ball_vx, self.ball_vy)
        if spd_now < 8.0 and not self.in_chute:
            self.stall_time += dt
            if self.stall_time > 2.0:
                # Table tilt: push ball toward drain center
                cx = 32.0
                dx = cx - self.ball_x
                ndx = 1.0 if dx > 0 else -1.0
                self.ball_vx = ndx * 20.0
                self.ball_vy = 40.0
                self.stall_time = 0.0
        else:
            self.stall_time = 0.0

        if self.ball_y > DRAIN_Y:
            self.phase = PHASE_DRAIN
            self.phase_timer = 1.0

        self._update_camera(dt)

    def _update_drain(self, dt):
        self.phase_timer -= dt
        if self.phase_timer <= 0:
            self.balls_left -= 1
            if self.balls_left <= 0:
                self.state = GameState.GAME_OVER
            else:
                self.ball_number += 1
                self.phase = PHASE_BALL_OVER
                self.phase_timer = 1.5

    def _update_ball_over(self, inp, dt):
        self.phase_timer -= dt
        if self.phase_timer <= 0 or inp.action_l or inp.action_r:
            self._reset_ball()
            self.camera_y = float(TABLE_H - SCREEN_H)

    # ===== DRAW =====

    def draw(self):
        d = self.display
        d.clear(Colors.BLACK)
        cy = int(self.camera_y)

        self._draw_playfield(d, cy)
        self._draw_rollovers(d, cy)
        self._draw_spinner(d, cy)
        self._draw_bumpers(d, cy)
        self._draw_drop_targets(d, cy)
        self._draw_gate(d, cy)
        self._draw_slingshots(d, cy)
        self._draw_return_lanes(d, cy)
        self._draw_flippers(d, cy)
        self._draw_chute(d, cy)
        self._draw_ball(d, cy)
        self._draw_hud(d)

        if self.phase == PHASE_PLUNGER and self.plunger_charging:
            self._draw_power_bar(d)
        elif self.phase == PHASE_DRAIN:
            self._draw_drain_msg(d)
        elif self.phase == PHASE_BALL_OVER:
            self._draw_ball_over(d)

    def _vis(self, wy, cy):
        """Is world-y visible on screen?"""
        return 0 <= wy - cy < SCREEN_H

    def _draw_playfield(self, d, cy):
        WALL_C = (50, 50, 70)
        RAIL_C = (70, 70, 90)
        # Left wall
        for wy in range(max(0, cy), min(TABLE_H, cy + SCREEN_H)):
            d.set_pixel(0, wy - cy, WALL_C)
        # Right wall (above chute)
        for wy in range(max(0, cy), min(PLUNGER_CHUTE_TOP, cy + SCREEN_H)):
            d.set_pixel(63, wy - cy, WALL_C)
        # Top wall
        if cy <= 2:
            for x in range(64):
                d.set_pixel(x, max(0, 1 - cy), WALL_C)
        # Curved top rail
        for x0, y0, x1, y1 in CHUTE_RAIL:
            sy0, sy1 = y0 - cy, y1 - cy
            if sy0 < SCREEN_H and sy1 >= -5:
                d.draw_line(x0, sy0, x1, sy1, RAIL_C)
        # Guide walls + return lane walls
        for x0, y0, x1, y1 in [(1, 148, 10, 168), (62, 148, 53, 168),
                                (10, 168, 17, 174), (53, 168, 46, 174)]:
            sy0, sy1 = y0 - cy, y1 - cy
            if sy0 < SCREEN_H and sy1 >= 0:
                d.draw_line(x0, sy0, x1, sy1, (80, 80, 100))

    def _draw_rollovers(self, d, cy):
        for lane in self.rollovers:
            lx = int(lane.x)
            for wy in range(int(lane.y_top), int(lane.y_bottom) + 1):
                sy = wy - cy
                if 0 <= sy < SCREEN_H:
                    c = Colors.YELLOW if lane.lit else (35, 35, 0)
                    d.set_pixel(lx - 1, sy, c)
                    d.set_pixel(lx + 1, sy, c)

    def _draw_spinner(self, d, cy):
        sy = int(self.spinner_y) - cy
        if 0 <= sy < SCREEN_H:
            sx = int(self.spinner_x)
            phase = int(self.spinner_angle * 3) % 4
            c = Colors.CYAN
            if phase % 2 == 0:
                d.set_pixel(sx - 1, sy, c)
                d.set_pixel(sx + 1, sy, c)
            else:
                d.set_pixel(sx, sy - 1, c)
                d.set_pixel(sx, sy + 1, c)
            d.set_pixel(sx, sy, c)

    def _draw_bumpers(self, d, cy):
        TIER_COLORS = [
            ((40, 40, 200), (30, 30, 120)),    # blue
            ((40, 200, 40), (30, 120, 30)),     # green
            ((220, 200, 40), (130, 120, 20)),   # yellow
            ((220, 40, 40), (130, 20, 20)),     # red
        ]
        tier = min(self.bumper_tier, 3)
        fill_c, ring_c = TIER_COLORS[tier]
        for bumper in self.bumpers:
            sy = int(bumper.y) - cy
            sx = int(bumper.x)
            r = int(bumper.radius)
            if sy - r >= SCREEN_H or sy + r < 0:
                continue
            if bumper.flash > 0:
                fc, rc = Colors.WHITE, Colors.YELLOW
            else:
                fc, rc = fill_c, ring_c
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    dsq = dx * dx + dy * dy
                    if dsq <= r * r:
                        c = rc if dsq >= (r - 1) * (r - 1) else fc
                        d.set_pixel(sx + dx, sy + dy, c)

    def _draw_drop_targets(self, d, cy):
        for target in self.drop_targets:
            sy = int(target.y) - cy
            sx = int(target.x)
            if sy < -1 or sy >= SCREEN_H + 1:
                continue
            if target.active:
                d.set_pixel(sx, sy, Colors.GREEN)
                d.set_pixel(sx - 1, sy, Colors.GREEN)
                d.set_pixel(sx + 1, sy, Colors.GREEN)
                d.set_pixel(sx, sy - 1, (0, 180, 0))
                d.set_pixel(sx, sy + 1, (0, 180, 0))
            else:
                d.set_pixel(sx, sy, (25, 50, 25))

    def _draw_gate(self, d, cy):
        sy = int(self.gate_y) - cy
        if 0 <= sy < SCREEN_H:
            for x in range(9, 55):
                d.set_pixel(x, sy, (50, 50, 25))

    def _draw_slingshots(self, d, cy):
        lc = Colors.YELLOW if self.sling_l_timer > 0 else (70, 55, 0)
        rc = Colors.YELLOW if self.sling_r_timer > 0 else (70, 55, 0)
        for x0, y0, x1, y1, c in [
            (8, 140, 8, 152, lc), (8, 152, 14, 168, lc),
            (55, 140, 55, 152, rc), (55, 152, 49, 168, rc),
        ]:
            sy0, sy1 = y0 - cy, y1 - cy
            if sy1 >= 0 and sy0 < SCREEN_H:
                d.draw_line(x0, sy0, x1, sy1, c)

    def _draw_return_lanes(self, d, cy):
        c = (25, 25, 45)
        for wy in range(140, 172):
            sy = wy - cy
            if 0 <= sy < SCREEN_H:
                d.set_pixel(3, sy, c)
                d.set_pixel(4, sy, c)
                d.set_pixel(59, sy, c)
                d.set_pixel(60, sy, c)

    def _draw_flippers(self, d, cy):
        for flipper in [self.flipper_l, self.flipper_r]:
            tx, ty = flipper.tip()
            px_s, py_s = int(flipper.px), int(flipper.py) - cy
            tx_s, ty_s = int(tx), int(ty) - cy
            if -5 <= py_s < SCREEN_H + 5:
                d.draw_line(px_s, py_s, tx_s, ty_s, Colors.ORANGE)
                # Thicken the flipper with offset lines
                nx = -(ty - flipper.py)
                ny = (tx - flipper.px)
                ln = _mag(nx, ny)
                if ln > 0.1:
                    nx, ny = nx / ln, ny / ln
                    d.draw_line(px_s + int(nx), py_s + int(ny),
                                tx_s + int(nx * 0.5), ty_s + int(ny * 0.5),
                                (180, 100, 0))
                    d.draw_line(px_s - int(nx), py_s - int(ny),
                                tx_s - int(nx * 0.5), ty_s - int(ny * 0.5),
                                (180, 100, 0))
                d.set_pixel(px_s, py_s, Colors.WHITE)

    def _draw_chute(self, d, cy):
        WALL_C = (50, 50, 70)
        for wy in range(max(PLUNGER_CHUTE_TOP, cy), min(192, cy + SCREEN_H)):
            sy = wy - cy
            d.set_pixel(PLUNGER_CHUTE_LEFT - 1, sy, WALL_C)
            d.set_pixel(63, sy, WALL_C)
        # Plunger spring visual
        if self.phase == PHASE_PLUNGER:
            spring_y = int(BALL_START_Y + 4 + self.plunger_charge * 6) - cy
            if 0 <= spring_y < SCREEN_H:
                for x in range(PLUNGER_CHUTE_LEFT + 1, 62):
                    d.set_pixel(x, spring_y, Colors.RED)
                # Spring coils
                for wy_off in range(1, int(self.plunger_charge * 6) + 1, 2):
                    coil_y = spring_y - wy_off
                    if 0 <= coil_y < SCREEN_H:
                        d.set_pixel(PLUNGER_CHUTE_LEFT + 1, coil_y, (150, 50, 50))
                        d.set_pixel(61, coil_y, (150, 50, 50))

    def _draw_ball(self, d, cy):
        if self.phase == PHASE_DRAIN and self.phase_timer < 0.5:
            return
        bx = int(self.ball_x)
        by = int(self.ball_y) - cy
        if -2 <= by < SCREEN_H + 2:
            d.set_pixel(bx, by, Colors.WHITE)
            d.set_pixel(bx - 1, by, (200, 200, 210))
            d.set_pixel(bx + 1, by, (200, 200, 210))
            d.set_pixel(bx, by - 1, (200, 200, 210))
            d.set_pixel(bx, by + 1, (200, 200, 210))

    def _draw_hud(self, d):
        d.draw_rect(0, 0, 64, 7, Colors.BLACK)
        d.draw_text_small(2, 1, f"{self.score}", Colors.WHITE)
        # Ball indicator dots
        for i in range(self.balls_left):
            d.set_pixel(58 - i * 3, 3, Colors.WHITE)
        # Multiplier indicator
        if self.multiplier > 1:
            d.draw_text_small(38, 1, f"{self.multiplier}X", Colors.YELLOW)

    def _draw_power_bar(self, d):
        bar_x, bar_y, bar_w = 2, 58, 60
        d.draw_rect(bar_x, bar_y, bar_w, 3, (25, 25, 25))
        fill_w = int(self.plunger_charge * bar_w)
        for px in range(fill_w):
            frac = px / max(bar_w - 1, 1)
            r = int(255 * frac)
            g = int(255 * (1.0 - frac))
            c = (r, g, 0)
            d.set_pixel(bar_x + px, bar_y, c)
            d.set_pixel(bar_x + px, bar_y + 1, c)
            d.set_pixel(bar_x + px, bar_y + 2, c)

    def _draw_drain_msg(self, d):
        d.draw_rect(12, 28, 40, 9, Colors.BLACK)
        d.draw_text_small(14, 30, "DRAIN!", Colors.RED)

    def _draw_ball_over(self, d):
        d.draw_rect(6, 24, 52, 16, Colors.BLACK)
        d.draw_text_small(12, 26, f"BALL {self.ball_number}", Colors.CYAN)
        d.draw_text_small(2, 34, f"SCORE:{self.score}", Colors.WHITE)
