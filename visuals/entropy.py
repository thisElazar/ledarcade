"""
Entropy - The Arrow of Time
===========================
A gas of particles starts packed against one wall of a box, then spreads
until it fills the box evenly. Entropy climbs. That is the second law.

But the rules the particles follow are *exactly reversible* (an HPP
lattice gas: particles hop one pixel per tick, head-on pairs scatter
sideways, everything else passes through - all in integer arithmetic).
Press Action and every velocity flips: the haze un-mixes, pixel by
pixel, back against the wall it came from, and the entropy meter
falls. Nothing about the rules prefers "mixed" - there are simply
astronomically more mixed arrangements than packed ones, so mixed is
where a system spends its time.

The meter is *coarse-grained* entropy: the box is divided into blocks,
particles counted per block, and H = -sum p_i log2 p_i taken over the
block distribution, normalised to log2(#blocks). Up/Down changes the
block size - entropy depends on what you choose not to resolve. The
faint block tint behind the particles is that macrostate.

Left alone it cycles: mix -> reverse -> un-mix -> hold at order -> repeat.

Controls:
  Action      - Reverse time (flip every velocity)
  Up/Down     - Coarse-grain block size for the entropy meter
  Left/Right  - Gas density (restarts)
"""

import math
import random
from . import Visual, Display, GRID_SIZE

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
CH_Y0 = 8            # chamber top row (HUD above)
CH_H = 48            # chamber height (divisible by every block size)
CH_W = GRID_SIZE     # 64 wide: one Python int per row per direction
MASK = (1 << CH_W) - 1
TOP = 1 << (CH_W - 1)

METER_Y = 58
METER_X0 = 4
METER_W = 56
METER_H = 4

# ---------------------------------------------------------------------------
# Tunables
# ---------------------------------------------------------------------------
STEPS_PER_SEC = 40
CYCLE_STEPS = 12 * STEPS_PER_SEC     # auto-reverse after this many steps
HOLD_AT_ORIGIN = 1.5                 # seconds to rest on the ordered state
SEED_WIDTH = 16                      # initial packed strip is x < SEED_WIDTH
DENSITIES = [0.25, 0.40, 0.55, 0.70, 0.85]
BLOCK_SIZES = [4, 8, 16]
DIM_BG = (4, 4, 12)
OBSTACLE_COLOR = (70, 70, 85)


def _build_obstacles():
    """Fixed 2x2 pillars, staggered, outside the seed strip. Without them
    the free-streaming gas crosses the box as a rigid slab; pillars scatter
    it into something that reads as diffusion. Bounces are reversible."""
    rows = [0] * CH_H
    for j, y in enumerate(range(5, CH_H - 2, 12)):
        for x in range(28 + (6 if j % 2 else 0), CH_W - 2, 12):
            bits = 0b11 << x
            rows[y] |= bits
            rows[y + 1] |= bits
    return rows


OBSTACLES = _build_obstacles()

# Particle colour by how many share a pixel (1..4)
COUNT_COLORS = [None,
                (70, 170, 255),
                (150, 220, 255),
                (230, 245, 255),
                (255, 255, 255)]


def _popcount(v):
    return bin(v).count("1")


class Entropy(Visual):
    name = "ENTROPY"
    description = "The arrow of time"
    category = "math"
    GUIDE = {
        'desc': 'A gas spreads from one wall until it fills the box - entropy '
                'climbs. Press Action and every velocity reverses: the gas '
                'un-mixes back to where it started. The rules never changed; '
                'there are just vastly more mixed arrangements than ordered '
                'ones.',
        'credit': 'Ludwig Boltzmann, 1877 / Claude Shannon, 1948',
        'controls': {
            'Action': 'Reverse time',
            'Up/Down': 'Block size for the entropy meter',
            'Left/Right': 'Gas density',
        },
    }

    def __init__(self, display: Display):
        super().__init__(display)

    # -----------------------------------------------------------------
    # Reset
    # -----------------------------------------------------------------
    def reset(self):
        self.time = 0.0
        self.density_idx = 2
        self.block_idx = 1
        self.overlay_timer = 0.0
        self.overlay_text = ""
        self._seed_gas()

    def _seed_gas(self):
        """Pack the gas into the left strip with random velocities."""
        p = DENSITIES[self.density_idx]
        seed_mask = (1 << SEED_WIDTH) - 1
        self.e, self.w, self.n, self.s = [], [], [], []
        for _ in range(CH_H):
            row = []
            for _ch in range(4):
                bits = 0
                for x in range(SEED_WIDTH):
                    if random.random() < p:
                        bits |= 1 << x
                row.append(bits & seed_mask)
            self.e.append(row[0])
            self.w.append(row[1])
            self.n.append(row[2])
            self.s.append(row[3])
        self.tau = 0            # signed step count from the ordered state
        self.direction = 1      # +1 forward, -1 reversed
        self.step_accum = 0.0
        self.hold_timer = 0.0
        # Entropy is defined up to an additive constant; the meter shows
        # the rise above the packed state, per block size.
        self.h_floor = []
        for bi in range(len(BLOCK_SIZES)):
            self.h_floor.append(self._entropy_norm(self._block_counts(bi)[0]))

    def _show_overlay(self, text):
        self.overlay_text = text
        self.overlay_timer = 1.5

    # -----------------------------------------------------------------
    # Lattice gas dynamics (propagate, then collide) - bit-exact reversible
    # -----------------------------------------------------------------
    def _propagate(self):
        e, w, n, s = self.e, self.w, self.n, self.s
        ne = [0] * CH_H
        nw = [0] * CH_H
        nn = [0] * CH_H
        ns = [0] * CH_H
        for y in range(CH_H):
            o = OBSTACLES[y]
            # East/west hop. A particle hitting the side wall or a pillar
            # stays put and turns around.
            me = (e[y] << 1) & MASK
            mw = w[y] >> 1
            ne[y] = (me & ~o) | (w[y] & 1) | ((mw & o) << 1)
            nw[y] = (mw & ~o) | (e[y] & TOP) | ((me & o) >> 1)
            # North/south hop into this row; top and bottom walls likewise.
            mn = n[y + 1] if y < CH_H - 1 else s[y]
            ms = s[y - 1] if y > 0 else n[y]
            nn[y] = mn & ~o
            ns[y] = ms & ~o
        # Vertical pillar bounces: stay in the source row, reversed.
        for y in range(CH_H):
            o = OBSTACLES[y]
            if y < CH_H - 1:
                ns[y + 1] |= n[y + 1] & o
            if y > 0:
                nn[y - 1] |= s[y - 1] & o
        self.e, self.w, self.n, self.s = ne, nw, nn, ns

    def _collide(self):
        e, w, n, s = self.e, self.w, self.n, self.s
        for y in range(CH_H):
            a, b, c, d = e[y], w[y], n[y], s[y]
            ew = a & b & ~c & ~d      # head-on E+W -> scatter to N+S
            ns = c & d & ~a & ~b      # head-on N+S -> scatter to E+W
            e[y] = (a & ~ew) | ns
            w[y] = (b & ~ew) | ns
            n[y] = (c & ~ns) | ew
            s[y] = (d & ~ns) | ew

    def _step(self):
        self._propagate()
        self._collide()
        self.tau += self.direction

    def _reverse(self):
        """Flip every velocity. Undo the last collision first so the
        retraced path is exact (collision is its own inverse)."""
        self._collide()
        self.e, self.w = self.w, self.e
        self.n, self.s = self.s, self.n
        self.direction = -self.direction

    # -----------------------------------------------------------------
    # Coarse-grained entropy
    # -----------------------------------------------------------------
    def _block_counts(self, block_idx=None):
        """Particles per block, row-major, for the given block size."""
        if block_idx is None:
            block_idx = self.block_idx
        B = BLOCK_SIZES[block_idx]
        bx_n = CH_W // B
        by_n = CH_H // B
        bmask = (1 << B) - 1
        counts = [0] * (bx_n * by_n)
        for y in range(CH_H):
            base = (y // B) * bx_n
            for ch in (self.e[y], self.w[y], self.n[y], self.s[y]):
                bx = 0
                while ch:
                    if ch & bmask:
                        counts[base + bx] += _popcount(ch & bmask)
                    ch >>= B
                    bx += 1
        return counts, bx_n, by_n

    @staticmethod
    def _entropy_norm(counts):
        total = sum(counts)
        if total == 0 or len(counts) < 2:
            return 0.0
        h = 0.0
        for c in counts:
            if c:
                p = c / total
                h -= p * math.log2(p)
        return h / math.log2(len(counts))

    # -----------------------------------------------------------------
    # Input
    # -----------------------------------------------------------------
    def handle_input(self, inp) -> bool:
        consumed = False
        if inp.action_l or inp.action_r:
            self._reverse()
            self.hold_timer = 0.0
            self._show_overlay("REVERSE")
            consumed = True
        if inp.up_pressed:
            self.block_idx = min(len(BLOCK_SIZES) - 1, self.block_idx + 1)
            self._show_overlay(f"BLOCK {BLOCK_SIZES[self.block_idx]}")
            consumed = True
        if inp.down_pressed:
            self.block_idx = max(0, self.block_idx - 1)
            self._show_overlay(f"BLOCK {BLOCK_SIZES[self.block_idx]}")
            consumed = True
        if inp.right_pressed:
            self.density_idx = min(len(DENSITIES) - 1, self.density_idx + 1)
            self._seed_gas()
            self._show_overlay(f"DENSITY {int(DENSITIES[self.density_idx] * 100)}")
            consumed = True
        if inp.left_pressed:
            self.density_idx = max(0, self.density_idx - 1)
            self._seed_gas()
            self._show_overlay(f"DENSITY {int(DENSITIES[self.density_idx] * 100)}")
            consumed = True
        return consumed

    # -----------------------------------------------------------------
    # Update
    # -----------------------------------------------------------------
    def update(self, dt: float):
        self.time += dt
        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

        if self.hold_timer > 0:
            self.hold_timer = max(0.0, self.hold_timer - dt)
            return

        self.step_accum += dt * STEPS_PER_SEC
        while self.step_accum >= 1.0:
            self.step_accum -= 1.0
            self._step()

            if self.tau == 0:
                # Back at the ordered state: rest so the eye can register it.
                self.hold_timer = HOLD_AT_ORIGIN
                self.step_accum = 0.0
                self._show_overlay("ORDER")
                break

            # Heading away from order and far enough out: turn around.
            if abs(self.tau) >= CYCLE_STEPS and self.tau * self.direction > 0:
                self._reverse()
                self._show_overlay("REVERSE")

    # -----------------------------------------------------------------
    # Draw
    # -----------------------------------------------------------------
    def draw(self):
        d = self.display
        d.clear(DIM_BG)

        counts, bx_n, by_n = self._block_counts()
        floor = self.h_floor[self.block_idx]
        h_norm = (self._entropy_norm(counts) - floor) / max(1e-9, 1.0 - floor)
        h_norm = max(0.0, min(1.0, h_norm))

        # Macrostate: faint block tint by density
        B = BLOCK_SIZES[self.block_idx]
        peak = max(counts) if counts else 1
        if peak > 0:
            for by in range(by_n):
                for bx in range(bx_n):
                    c = counts[by * bx_n + bx]
                    if c == 0:
                        continue
                    t = c / peak
                    tint = (int(6 + 14 * t), int(6 + 14 * t), int(14 + 40 * t))
                    d.draw_rect(bx * B, CH_Y0 + by * B, B, B, tint)

        # Pillars
        for y in range(CH_H):
            bits = OBSTACLES[y]
            while bits:
                low = bits & -bits
                d.set_pixel(low.bit_length() - 1, CH_Y0 + y, OBSTACLE_COLOR)
                bits ^= low

        # Microstate: particles, brighter where several share a pixel
        for y in range(CH_H):
            e, w, n, s = self.e[y], self.w[y], self.n[y], self.s[y]
            any1 = e | w | n | s
            if not any1:
                continue
            ge2 = (e & w) | (e & n) | (e & s) | (w & n) | (w & s) | (n & s)
            ge3 = (e & w & n) | (e & w & s) | (e & n & s) | (w & n & s)
            eq4 = e & w & n & s
            py = CH_Y0 + y
            bits = any1
            while bits:
                low = bits & -bits
                x = low.bit_length() - 1
                if eq4 & low:
                    col = COUNT_COLORS[4]
                elif ge3 & low:
                    col = COUNT_COLORS[3]
                elif ge2 & low:
                    col = COUNT_COLORS[2]
                else:
                    col = COUNT_COLORS[1]
                d.set_pixel(x, py, col)
                bits ^= low

        # Entropy meter: blue (ordered) -> red (mixed), white tick = max
        for yy in range(METER_Y, METER_Y + METER_H):
            for xx in range(METER_X0, METER_X0 + METER_W):
                d.set_pixel(xx, yy, (20, 20, 30))
        fill_w = int(h_norm * METER_W + 0.5)
        for xx in range(METER_X0, METER_X0 + fill_w):
            t = (xx - METER_X0) / max(1, METER_W - 1)
            col = (int(40 + 215 * t), int(120 - 80 * t), int(255 - 200 * t))
            for yy in range(METER_Y, METER_Y + METER_H):
                d.set_pixel(xx, yy, col)
        for yy in range(METER_Y, METER_Y + METER_H):
            d.set_pixel(METER_X0 + METER_W - 1, yy, (255, 255, 255))

        # HUD
        d.draw_text_small(2, 0, "ENTROPY", (200, 200, 200))
        if self.direction < 0:
            d.draw_text_small(48, 0, "REV", (255, 120, 60))
        else:
            d.draw_text_small(48, 0, "FWD", (100, 160, 220))

        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            oc = (int(230 * alpha), int(230 * alpha), int(230 * alpha))
            d.draw_rect(0, 28, 4 * len(self.overlay_text) + 3, 9, DIM_BG)
            d.draw_text_small(2, 30, self.overlay_text, oc)
