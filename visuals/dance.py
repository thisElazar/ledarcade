"""
DANCE - Dance Forms of the World
=================================
Animated stick figures performing dance notation from around the world.
Smooth interpolation between research-based keyframes, floor path traces,
and beat indicators.

Controls:
  Up/Down    - Cycle dance families (BALLROOM / FOLK / CLASSICAL / STREET)
  Left/Right - Cycle dances within current family
  Action     - Pause / resume animation
"""

import math
from . import Visual, Display, Colors, GRID_SIZE

# ---------------------------------------------------------------------------
# Families
# ---------------------------------------------------------------------------
FAMILIES = ['BALLROOM', 'FOLK', 'CLASSICAL', 'STREET']

# ---------------------------------------------------------------------------
# Dance data - 12 dances with research-based keyframes
# Each keyframe: head, left hand, right hand, left foot, right foot
# ---------------------------------------------------------------------------
DANCES = [
    # 1. WALTZ - Wide frame, rise-and-fall
    {
        'name': 'WALTZ', 'origin': 'Vienna', 'family': 'BALLROOM',
        'tempo': 1.0, 'time_sig': '3/4',
        'color': (180, 140, 255),
        'keyframes': [
            {'hx':32,'hy':19, 'lhx':20,'lhy':20, 'rhx':48,'rhy':20,
             'lfx':27,'lfy':45, 'rfx':37,'rfy':43},
            {'hx':32,'hy':16, 'lhx':20,'lhy':18, 'rhx':48,'rhy':18,
             'lfx':24,'lfy':43, 'rfx':40,'rfy':43},
            {'hx':32,'hy':15, 'lhx':20,'lhy':17, 'rhx':48,'rhy':17,
             'lfx':30,'lfy':42, 'rfx':34,'rfy':42},
            {'hx':33,'hy':18, 'lhx':22,'lhy':20, 'rhx':46,'rhy':20,
             'lfx':29,'lfy':44, 'rfx':35,'rfy':44},
            {'hx':31,'hy':17, 'lhx':18,'lhy':20, 'rhx':44,'rhy':20,
             'lfx':25,'lfy':44, 'rfx':39,'rfy':44},
        ],
    },
    # 2. TANGO - Low grounded, head snap sideways
    {
        'name': 'TANGO', 'origin': 'Argentina', 'family': 'BALLROOM',
        'tempo': 0.8, 'time_sig': '4/4',
        'color': (255, 60, 60),
        'keyframes': [
            {'hx':36,'hy':19, 'lhx':20,'lhy':21, 'rhx':44,'rhy':21,
             'lfx':27,'lfy':44, 'rfx':37,'rfy':44},
            {'hx':36,'hy':19, 'lhx':20,'lhy':21, 'rhx':44,'rhy':21,
             'lfx':26,'lfy':43, 'rfx':38,'rfy':45},
            {'hx':30,'hy':20, 'lhx':18,'lhy':22, 'rhx':42,'rhy':22,
             'lfx':22,'lfy':44, 'rfx':38,'rfy':44},
            {'hx':34,'hy':18, 'lhx':20,'lhy':21, 'rhx':44,'rhy':21,
             'lfx':29,'lfy':44, 'rfx':33,'rfy':44},
            {'hx':32,'hy':18, 'lhx':20,'lhy':21, 'rhx':44,'rhy':20,
             'lfx':28,'lfy':44, 'rfx':36,'rfy':38},
        ],
    },
    # 3. FOXTROT - Long smooth strides, heel lead
    {
        'name': 'FOXTROT', 'origin': 'USA', 'family': 'BALLROOM',
        'tempo': 0.9, 'time_sig': '4/4',
        'color': (255, 200, 100),
        'keyframes': [
            {'hx':32,'hy':17, 'lhx':21,'lhy':20, 'rhx':45,'rhy':20,
             'lfx':22,'lfy':44, 'rfx':38,'rfy':44},
            {'hx':32,'hy':17, 'lhx':21,'lhy':20, 'rhx':45,'rhy':20,
             'lfx':26,'lfy':43, 'rfx':36,'rfy':44},
            {'hx':32,'hy':17, 'lhx':21,'lhy':20, 'rhx':45,'rhy':20,
             'lfx':27,'lfy':43, 'rfx':42,'rfy':43},
            {'hx':32,'hy':17, 'lhx':21,'lhy':20, 'rhx':45,'rhy':20,
             'lfx':30,'lfy':43, 'rfx':34,'rfy':43},
            {'hx':32,'hy':16, 'lhx':21,'lhy':19, 'rhx':45,'rhy':19,
             'lfx':24,'lfy':44, 'rfx':38,'rfy':44},
        ],
    },
    # 4. SALSA - Small quick steps, hip motion
    {
        'name': 'SALSA', 'origin': 'Cuba', 'family': 'STREET',
        'tempo': 1.2, 'time_sig': '4/4',
        'color': (255, 100, 50),
        'keyframes': [
            {'hx':32,'hy':18, 'lhx':24,'lhy':26, 'rhx':40,'rhy':26,
             'lfx':28,'lfy':44, 'rfx':36,'rfy':44},
            {'hx':32,'hy':18, 'lhx':24,'lhy':27, 'rhx':40,'rhy':27,
             'lfx':25,'lfy':43, 'rfx':37,'rfy':44},
            {'hx':32,'hy':18, 'lhx':24,'lhy':27, 'rhx':40,'rhy':27,
             'lfx':25,'lfy':44, 'rfx':37,'rfy':44},
            {'hx':32,'hy':18, 'lhx':24,'lhy':27, 'rhx':40,'rhy':27,
             'lfx':27,'lfy':44, 'rfx':39,'rfy':44},
            {'hx':32,'hy':17, 'lhx':24,'lhy':18, 'rhx':40,'rhy':22,
             'lfx':28,'lfy':44, 'rfx':36,'rfy':44},
            {'hx':32,'hy':17, 'lhx':26,'lhy':22, 'rhx':38,'rhy':22,
             'lfx':30,'lfy':43, 'rfx':34,'rfy':43},
        ],
    },
    # 5. BALLET - Extreme turnout, port de bras
    {
        'name': 'BALLET', 'origin': 'France', 'family': 'CLASSICAL',
        'tempo': 0.6, 'time_sig': '3/4',
        'color': (200, 180, 255),
        'keyframes': [
            {'hx':32,'hy':17, 'lhx':24,'lhy':23, 'rhx':40,'rhy':23,
             'lfx':26,'lfy':44, 'rfx':38,'rfy':44},
            {'hx':32,'hy':17, 'lhx':18,'lhy':23, 'rhx':46,'rhy':23,
             'lfx':22,'lfy':44, 'rfx':42,'rfy':44},
            {'hx':32,'hy':16, 'lhx':25,'lhy':22, 'rhx':39,'rhy':22,
             'lfx':30,'lfy':41, 'rfx':34,'rfy':41},
            {'hx':32,'hy':17, 'lhx':18,'lhy':22, 'rhx':44,'rhy':22,
             'lfx':30,'lfy':43, 'rfx':38,'rfy':37},
            {'hx':32,'hy':17, 'lhx':20,'lhy':21, 'rhx':42,'rhy':22,
             'lfx':30,'lfy':43, 'rfx':39,'rfy':35},
            {'hx':32,'hy':17, 'lhx':18,'lhy':22, 'rhx':46,'rhy':22,
             'lfx':29,'lfy':43, 'rfx':40,'rfy':26},
        ],
    },
    # 6. FLAMENCO - Arms overhead, zapateado heel stamps
    {
        'name': 'FLAMENCO', 'origin': 'Spain', 'family': 'FOLK',
        'tempo': 1.1, 'time_sig': '3/4',
        'color': (255, 80, 30),
        'keyframes': [
            {'hx':32,'hy':17, 'lhx':22,'lhy':9,  'rhx':42,'rhy':9,
             'lfx':28,'lfy':44, 'rfx':36,'rfy':44},
            {'hx':33,'hy':17, 'lhx':20,'lhy':13, 'rhx':42,'rhy':21,
             'lfx':27,'lfy':44, 'rfx':37,'rfy':43},
            {'hx':32,'hy':18, 'lhx':16,'lhy':27, 'rhx':44,'rhy':11,
             'lfx':27,'lfy':44, 'rfx':37,'rfy':44},
            {'hx':34,'hy':18, 'lhx':14,'lhy':22, 'rhx':48,'rhy':22,
             'lfx':30,'lfy':43, 'rfx':34,'rfy':43},
            {'hx':32,'hy':17, 'lhx':30,'lhy':15, 'rhx':34,'rhy':15,
             'lfx':27,'lfy':43, 'rfx':37,'rfy':44},
        ],
    },
    # 7. BHARATANATYAM - Aramandi squat, angular mudras
    {
        'name': 'BHARATA', 'origin': 'India', 'family': 'CLASSICAL',
        'tempo': 0.7, 'time_sig': '4/4',
        'color': (255, 180, 50),
        'keyframes': [
            {'hx':32,'hy':18, 'lhx':14,'lhy':22, 'rhx':50,'rhy':22,
             'lfx':18,'lfy':44, 'rfx':46,'rfy':44},
            {'hx':32,'hy':17, 'lhx':18,'lhy':23, 'rhx':44,'rhy':14,
             'lfx':20,'lfy':44, 'rfx':44,'rfy':44},
            {'hx':32,'hy':17, 'lhx':14,'lhy':22, 'rhx':44,'rhy':10,
             'lfx':22,'lfy':44, 'rfx':44,'rfy':44},
            {'hx':32,'hy':17, 'lhx':16,'lhy':22, 'rhx':48,'rhy':22,
             'lfx':28,'lfy':41, 'rfx':36,'rfy':41},
            {'hx':32,'hy':19, 'lhx':14,'lhy':22, 'rhx':50,'rhy':22,
             'lfx':15,'lfy':44, 'rfx':49,'rfy':44},
        ],
    },
    # 8. IRISH STEP - Rigid upper body, foot crossing
    {
        'name': 'IRISH', 'origin': 'Ireland', 'family': 'FOLK',
        'tempo': 1.3, 'time_sig': '4/4',
        'color': (50, 200, 80),
        'keyframes': [
            {'hx':32,'hy':17, 'lhx':28,'lhy':34, 'rhx':36,'rhy':34,
             'lfx':28,'lfy':44, 'rfx':34,'rfy':44},
            {'hx':32,'hy':17, 'lhx':28,'lhy':33, 'rhx':36,'rhy':33,
             'lfx':29,'lfy':44, 'rfx':36,'rfy':30},
            {'hx':32,'hy':16, 'lhx':28,'lhy':32, 'rhx':36,'rhy':32,
             'lfx':29,'lfy':39, 'rfx':35,'rfy':39},
            {'hx':32,'hy':17, 'lhx':28,'lhy':33, 'rhx':36,'rhy':33,
             'lfx':26,'lfy':44, 'rfx':32,'rfy':43},
            {'hx':32,'hy':17, 'lhx':28,'lhy':33, 'rhx':36,'rhy':33,
             'lfx':28,'lfy':42, 'rfx':38,'rfy':44},
        ],
    },
    # 9. SAMBA - Pendular bounce, hip swing
    {
        'name': 'SAMBA', 'origin': 'Brazil', 'family': 'STREET',
        'tempo': 1.4, 'time_sig': '2/4',
        'color': (0, 200, 100),
        'keyframes': [
            {'hx':32,'hy':19, 'lhx':24,'lhy':26, 'rhx':40,'rhy':26,
             'lfx':28,'lfy':45, 'rfx':36,'rfy':45},
            {'hx':32,'hy':17, 'lhx':24,'lhy':25, 'rhx':40,'rhy':25,
             'lfx':27,'lfy':44, 'rfx':38,'rfy':43},
            {'hx':32,'hy':18, 'lhx':24,'lhy':26, 'rhx':40,'rhy':26,
             'lfx':25,'lfy':44, 'rfx':38,'rfy':44},
            {'hx':33,'hy':17, 'lhx':18,'lhy':22, 'rhx':44,'rhy':22,
             'lfx':25,'lfy':43, 'rfx':38,'rfy':44},
            {'hx':32,'hy':18, 'lhx':16,'lhy':24, 'rhx':42,'rhy':24,
             'lfx':22,'lfy':44, 'rfx':38,'rfy':44},
        ],
    },
    # 10. SWING - Rock step, triple step, open position
    {
        'name': 'SWING', 'origin': 'USA', 'family': 'STREET',
        'tempo': 1.2, 'time_sig': '4/4',
        'color': (255, 220, 50),
        'keyframes': [
            {'hx':32,'hy':17, 'lhx':20,'lhy':21, 'rhx':44,'rhy':21,
             'lfx':28,'lfy':44, 'rfx':36,'rfy':44},
            {'hx':32,'hy':18, 'lhx':20,'lhy':21, 'rhx':44,'rhy':21,
             'lfx':26,'lfy':44, 'rfx':38,'rfy':43},
            {'hx':32,'hy':17, 'lhx':20,'lhy':21, 'rhx':44,'rhy':21,
             'lfx':25,'lfy':43, 'rfx':33,'rfy':43},
            {'hx':32,'hy':17, 'lhx':14,'lhy':20, 'rhx':46,'rhy':23,
             'lfx':24,'lfy':44, 'rfx':40,'rfy':44},
            {'hx':32,'hy':17, 'lhx':20,'lhy':22, 'rhx':44,'rhy':22,
             'lfx':26,'lfy':43, 'rfx':36,'rfy':44},
        ],
    },
    # 11. CAPOEIRA - Ginga, meia lua, au cartwheel
    {
        'name': 'CAPOEIRA', 'origin': 'Brazil', 'family': 'STREET',
        'tempo': 1.0, 'time_sig': '4/4',
        'color': (255, 200, 0),
        'keyframes': [
            {'hx':32,'hy':20, 'lhx':20,'lhy':25, 'rhx':44,'rhy':25,
             'lfx':20,'lfy':44, 'rfx':44,'rfy':44},
            {'hx':30,'hy':20, 'lhx':18,'lhy':27, 'rhx':42,'rhy':24,
             'lfx':18,'lfy':44, 'rfx':40,'rfy':44},
            {'hx':32,'hy':19, 'lhx':20,'lhy':26, 'rhx':42,'rhy':24,
             'lfx':26,'lfy':44, 'rfx':48,'rfy':28},
            {'hx':26,'hy':24, 'lhx':20,'lhy':22, 'rhx':44,'rhy':28,
             'lfx':20,'lfy':44, 'rfx':44,'rfy':44},
            {'hx':32,'hy':36, 'lhx':16,'lhy':30, 'rhx':48,'rhy':30,
             'lfx':20,'lfy':22, 'rfx':44,'rfy':22},
            {'hx':28,'hy':28, 'lhx':16,'lhy':34, 'rhx':40,'rhy':30,
             'lfx':16,'lfy':44, 'rfx':42,'rfy':44},
        ],
    },
    # 12. HULA - Kaholo, ami, storytelling hands
    {
        'name': 'HULA', 'origin': 'Hawaii', 'family': 'FOLK',
        'tempo': 0.6, 'time_sig': '4/4',
        'color': (100, 200, 150),
        'keyframes': [
            {'hx':33,'hy':17, 'lhx':22,'lhy':22, 'rhx':40,'rhy':22,
             'lfx':24,'lfy':44, 'rfx':36,'rfy':44},
            {'hx':31,'hy':17, 'lhx':24,'lhy':22, 'rhx':42,'rhy':22,
             'lfx':28,'lfy':44, 'rfx':36,'rfy':44},
            {'hx':32,'hy':17, 'lhx':22,'lhy':22, 'rhx':42,'rhy':22,
             'lfx':28,'lfy':44, 'rfx':36,'rfy':44},
            {'hx':32,'hy':17, 'lhx':22,'lhy':23, 'rhx':42,'rhy':23,
             'lfx':28,'lfy':43, 'rfx':36,'rfy':43},
            {'hx':32,'hy':17, 'lhx':16,'lhy':22, 'rhx':40,'rhy':24,
             'lfx':22,'lfy':44, 'rfx':42,'rfy':44},
            {'hx':32,'hy':16, 'lhx':20,'lhy':14, 'rhx':42,'rhy':18,
             'lfx':28,'lfy':44, 'rfx':36,'rfy':44},
        ],
    },
]

# Build family index
_FAMILY_MAP = {}
for _d in DANCES:
    _FAMILY_MAP.setdefault(_d['family'], []).append(_d)

# Full keyframe cycles before auto-advance
_AUTO_ADVANCE_CYCLES = 3

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _lerp(a, b, t):
    return a + (b - a) * t


def _smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _lerp_keyframe(kf_a, kf_b, t):
    t = _smoothstep(t)
    result = {}
    for key in ('hx', 'hy', 'lhx', 'lhy', 'rhx', 'rhy',
                'lfx', 'lfy', 'rfx', 'rfy'):
        result[key] = _lerp(kf_a[key], kf_b[key], t)
    return result


def _dim(color, factor=0.3):
    return (int(color[0] * factor), int(color[1] * factor),
            int(color[2] * factor))


def _brighten(color, amount=60):
    return (min(255, color[0] + amount), min(255, color[1] + amount),
            min(255, color[2] + amount))


def _alpha_blend(color, alpha):
    return (int(color[0] * alpha), int(color[1] * alpha),
            int(color[2] * alpha))


# ---------------------------------------------------------------------------
# Visual
# ---------------------------------------------------------------------------

class Dance(Visual):
    name = "DANCE"
    description = "Dance forms of the world"
    category = "culture"

    def reset(self):
        self._input_cooldown = 0.0
        self.family_idx = 0
        self.dance_idx = 0
        self.keyframe_idx = 0
        self.lerp_t = 0.0
        self.frame_timer = 0.0
        self.beat_timer = 0.0
        self.cycle_count = 0
        self.paused = False
        self.overlay_timer = 0.0
        self.floor_trail = []
        self.trail_timer = 0.0
        self._select_dance()

    def _select_dance(self):
        family = FAMILIES[self.family_idx]
        dances = _FAMILY_MAP.get(family, [])
        if not dances:
            self.dance_idx = 0
            return
        self.dance_idx = self.dance_idx % len(dances)
        self.current = dances[self.dance_idx]
        self.keyframe_idx = 0
        self.lerp_t = 0.0
        self.frame_timer = 0.0
        self.beat_timer = 0.0
        self.cycle_count = 0
        self.floor_trail = []
        self.trail_timer = 0.0
        self.overlay_timer = 2.5

    def _advance_dance(self):
        family = FAMILIES[self.family_idx]
        n = len(_FAMILY_MAP.get(family, []))
        if n > 1:
            self.dance_idx = (self.dance_idx + 1) % n
        else:
            self.family_idx = (self.family_idx + 1) % len(FAMILIES)
            self.dance_idx = 0
        self._select_dance()

    def handle_input(self, input_state):
        if self._input_cooldown > 0:
            return False

        consumed = False

        if input_state.up_pressed:
            self.family_idx = (self.family_idx - 1) % len(FAMILIES)
            self.dance_idx = 0
            self._select_dance()
            consumed = True
        elif input_state.down_pressed:
            self.family_idx = (self.family_idx + 1) % len(FAMILIES)
            self.dance_idx = 0
            self._select_dance()
            consumed = True

        if not consumed:
            family = FAMILIES[self.family_idx]
            n = len(_FAMILY_MAP.get(family, []))
            if input_state.left_pressed and n > 0:
                self.dance_idx = (self.dance_idx - 1) % n
                self._select_dance()
                consumed = True
            elif input_state.right_pressed and n > 0:
                self.dance_idx = (self.dance_idx + 1) % n
                self._select_dance()
                consumed = True

        if not consumed and (input_state.action_l or input_state.action_r):
            self.paused = not self.paused
            consumed = True

        if consumed:
            self._input_cooldown = 0.15
        return consumed

    def update(self, dt):
        super().update(dt)
        if self._input_cooldown > 0:
            self._input_cooldown = max(0.0, self._input_cooldown - dt)
        if self.overlay_timer > 0:
            self.overlay_timer -= dt

        if self.paused:
            return

        dance = self.current
        tempo = dance['tempo']
        kf_count = len(dance['keyframes'])
        if kf_count < 2:
            return

        # Advance interpolation between keyframes
        beat_dur = 1.0 / tempo
        self.frame_timer += dt
        self.lerp_t = self.frame_timer / beat_dur

        if self.lerp_t >= 1.0:
            self.frame_timer -= beat_dur
            self.lerp_t = self.frame_timer / beat_dur
            prev_idx = self.keyframe_idx
            self.keyframe_idx = (self.keyframe_idx + 1) % kf_count
            if self.keyframe_idx == 0 and prev_idx == kf_count - 1:
                self.cycle_count += 1

        # Beat timer for indicator dots
        self.beat_timer += dt * tempo
        if self.beat_timer >= 1.0:
            self.beat_timer -= 1.0

        # Floor trail: record foot midpoint periodically
        self.trail_timer += dt
        if self.trail_timer >= 0.15:
            self.trail_timer -= 0.15
            kfs = dance['keyframes']
            kf_a = kfs[self.keyframe_idx]
            kf_b = kfs[(self.keyframe_idx + 1) % kf_count]
            kf = _lerp_keyframe(kf_a, kf_b, self.lerp_t)
            tx = int((kf['lfx'] + kf['rfx']) / 2)
            self.floor_trail.append((tx, 52))
            if len(self.floor_trail) > 20:
                self.floor_trail.pop(0)

        # Auto-advance after several full cycles
        if self.cycle_count >= _AUTO_ADVANCE_CYCLES:
            self._advance_dance()

    # -------------------------------------------------------------------
    # Drawing helpers
    # -------------------------------------------------------------------

    def _draw_stick_figure(self, kf, color):
        d = self.display
        bright = _brighten(color, 50)

        hx = int(kf['hx'])
        hy = int(kf['hy'])
        lhx, lhy = int(kf['lhx']), int(kf['lhy'])
        rhx, rhy = int(kf['rhx']), int(kf['rhy'])
        lfx, lfy = int(kf['lfx']), int(kf['lfy'])
        rfx, rfy = int(kf['rfx']), int(kf['rfy'])

        neck_y = hy + 4
        shoulder_y = hy + 5
        hip_y = hy + 12

        # Head
        d.draw_circle(hx, hy, 3, color, filled=True)
        # Torso
        d.draw_line(hx, neck_y, hx, hip_y, color)
        # Arms
        d.draw_line(hx, shoulder_y, lhx, lhy, color)
        d.draw_line(hx, shoulder_y, rhx, rhy, color)
        # Legs
        d.draw_line(hx, hip_y, lfx, lfy, color)
        d.draw_line(hx, hip_y, rfx, rfy, color)

        # Bright dots on extremities
        d.set_pixel(lhx, lhy, bright)
        d.set_pixel(rhx, rhy, bright)
        d.set_pixel(lfx, lfy, bright)
        d.set_pixel(rfx, rfy, bright)

    def _draw_beat_indicator(self, dance):
        d = self.display
        color = dance['color']
        time_sig = dance['time_sig']
        beats = int(time_sig.split('/')[0]) if '/' in time_sig else 4
        beats = min(beats, 4)

        total_w = beats * 4 - 2
        start_x = 32 - total_w // 2
        current_beat = int(self.beat_timer * beats) % beats

        for b in range(beats):
            bx = start_x + b * 4
            if b == current_beat:
                phase = (self.beat_timer * beats) % 1.0
                alpha = max(0.2, 1.0 - phase * 1.5)
                bc = _alpha_blend(color, alpha)
            else:
                bc = _dim(color, 0.15)
            d.set_pixel(bx, 57, bc)
            d.set_pixel(bx + 1, 57, bc)

    def _draw_floor_trail(self, color):
        d = self.display
        n = len(self.floor_trail)
        if n == 0:
            return
        for i, (tx, ty) in enumerate(self.floor_trail):
            alpha = (i + 1) / n * 0.4
            c = _alpha_blend(color, alpha)
            d.set_pixel(tx, ty, c)

    def _draw_family_dots(self):
        d = self.display
        family = FAMILIES[self.family_idx]
        dances = _FAMILY_MAP.get(family, [])
        n = len(dances)
        if n <= 1:
            return
        total_w = n * 3 - 1
        start_x = 32 - total_w // 2
        for i in range(n):
            dx = start_x + i * 3
            c = (180, 180, 180) if i == self.dance_idx else (50, 50, 50)
            d.set_pixel(dx, 62, c)

    def _draw_overlay(self, dance):
        if self.overlay_timer <= 0:
            return
        d = self.display
        alpha = min(1.0, self.overlay_timer / 0.5)
        color = dance['color']

        d.draw_text_small(2, 1, dance['name'], _alpha_blend(color, alpha))
        d.draw_text_small(48, 1, dance['time_sig'],
                          _alpha_blend((200, 200, 200), alpha * 0.7))
        d.draw_text_small(2, 8, FAMILIES[self.family_idx],
                          _alpha_blend((255, 255, 255), alpha * 0.5))
        d.draw_text_small(2, 55, dance['origin'],
                          _alpha_blend((160, 160, 160), alpha * 0.6))

    # -------------------------------------------------------------------
    # Main draw
    # -------------------------------------------------------------------

    def draw(self):
        d = self.display
        d.clear()
        dance = self.current
        color = dance['color']
        kfs = dance['keyframes']
        kf_count = len(kfs)

        # Floor trail
        self._draw_floor_trail(color)

        # Interpolate and draw stick figure
        if kf_count >= 2:
            kf_a = kfs[self.keyframe_idx]
            kf_b = kfs[(self.keyframe_idx + 1) % kf_count]
            kf = _lerp_keyframe(kf_a, kf_b, self.lerp_t)
        else:
            kf = {k: float(v) for k, v in kfs[0].items()}

        self._draw_stick_figure(kf, color)

        # Beat indicator
        self._draw_beat_indicator(dance)

        # Family position dots
        self._draw_family_dots()

        # Persistent dim header when overlay is gone
        if self.overlay_timer <= 0:
            d.draw_text_small(2, 1, dance['name'], _dim(color, 0.5))
            d.draw_text_small(48, 1, dance['time_sig'], (60, 60, 60))

        # Overlay (fades out)
        self._draw_overlay(dance)

        # Pause indicator
        if self.paused:
            d.draw_text_small(26, 30, "||", (200, 200, 200))
