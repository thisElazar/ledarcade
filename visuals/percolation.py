"""
Percolation - Critical Threshold
=================================
Site percolation on a fixed lattice. Every site is dealt a hidden
threshold once; a site is open when p rises past its threshold. So p only
ever *opens* sites -- clusters grow, touch, and swallow each other, and at
the critical point (p ~ 0.593) one of them abruptly spans the whole grid.

Dealing the thresholds once is the whole point. Re-rolling the lattice at
each p shows only disconnected snapshots of noise; holding it fixed makes
the transition a single continuous story you can watch ignite.

Controls:
  Left/Right  - Raise / lower p
  Action      - Deal a fresh lattice
"""

import random
import math
from . import Visual, Display, Colors, GRID_SIZE

# Cluster coloring
VIVID_COLORS = [
    (60, 180, 255), (60, 255, 100), (255, 200, 40),
    (200, 60, 255), (255, 120, 40), (40, 255, 220),
    (255, 60, 180), (120, 255, 60), (255, 80, 120),
]

# A cluster earns a vivid color once it reaches this many sites; below it
# stays dim, so growth reads as clusters *lighting up* one after another.
VIVID_THRESHOLD = 14

BLOCKED_COLOR = (4, 3, 8)
DIM_CLUSTER_COLOR = (30, 30, 42)
FRESH_COLOR = (150, 170, 200)   # a site the rising p just opened

P_CRIT = 0.593

# Layout: lattice on top, HUD strip along the bottom. The old build drew the
# p-bar straight over row 63, eating the bottom row of the lattice.
W = GRID_SIZE               # 64
H = 58                      # lattice rows 0..57
HUD_Y = 59                  # 5-row HUD band (3x5 font) at rows 59..63
BAR_Y = 61
BAR_X0 = 26

P_MIN, P_MAX = 0.20, 0.85


class _Lattice:
    """Union-find over the sites, grown by raising p.

    Weighted union by size with path compression, plus two things the plain
    algorithm doesn't carry: each root keeps the list of its members (so a
    merge can repaint just the absorbed side) and the four edges its cluster
    touches (so spanning is O(1) at union time, not an O(N) rescan per step).
    """

    __slots__ = ('parent', 'size', 'members', 'edges', 'color', 'is_open',
                 'threshold', 'order', 'cursor', 'spanning_root', '_vivid_i')

    def __init__(self):
        n = W * H
        self.parent = list(range(n))
        self.size = [1] * n
        self.members = [None] * n          # only maintained for live roots
        self.edges = [0] * n               # bit 1=left 2=right 4=top 8=bottom
        self.color = [None] * n
        self.is_open = [False] * n
        self.threshold = [random.random() for _ in range(n)]
        # Sites in the order p will open them.
        self.order = sorted(range(n), key=self.threshold.__getitem__)
        self.cursor = 0
        self.spanning_root = None
        self._vivid_i = 0

    def find(self, x):
        p = self.parent
        while p[x] != x:
            p[x] = p[p[x]]
            x = p[x]
        return x

    def _edge_bits(self, idx):
        x = idx % W
        y = idx // W
        bits = 0
        if x == 0:
            bits |= 1
        if x == W - 1:
            bits |= 2
        if y == 0:
            bits |= 4
        if y == H - 1:
            bits |= 8
        return bits

    def _next_vivid(self):
        c = VIVID_COLORS[self._vivid_i % len(VIVID_COLORS)]
        self._vivid_i += 1
        return c

    def open_to(self, p, repaint):
        """Open every site whose threshold has fallen below p.

        `repaint(idx, color)` is called for each pixel that changed, so the
        caller only touches what actually moved.
        """
        order = self.order
        thr = self.threshold
        n = len(order)
        while self.cursor < n and thr[order[self.cursor]] <= p:
            idx = order[self.cursor]
            self.cursor += 1
            self._open_site(idx, repaint)

    def _open_site(self, idx, repaint):
        self.is_open[idx] = True
        self.members[idx] = [idx]
        self.edges[idx] = self._edge_bits(idx)
        self.size[idx] = 1
        self.color[idx] = None
        repaint(idx, FRESH_COLOR)

        x = idx % W
        y = idx // W
        if x > 0 and self.is_open[idx - 1]:
            self._union(idx, idx - 1, repaint)
        if x < W - 1 and self.is_open[idx + 1]:
            self._union(idx, idx + 1, repaint)
        if y > 0 and self.is_open[idx - W]:
            self._union(idx, idx - W, repaint)
        if y < H - 1 and self.is_open[idx + W]:
            self._union(idx, idx + W, repaint)

        # Settle just this pixel into its cluster's color -- unless the site
        # tipped the cluster over the vivid threshold, which lights it up whole.
        self._refresh_color(self.find(idx), repaint, [idx])

    def _union(self, a, b, repaint):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        # Larger cluster wins: it keeps its identity and color, the smaller
        # one is absorbed and repainted. That asymmetry is what makes the
        # giant cluster read as *eating* its neighbours near p_c.
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]
        self.edges[ra] |= self.edges[rb]
        absorbed = self.members[rb]
        self.members[ra].extend(absorbed)
        self.members[rb] = None
        if self.color[ra] is None:
            self.color[ra] = self.color[rb]
        self.color[rb] = None

        bits = self.edges[ra]
        if self.spanning_root is None and ((bits & 3) == 3 or (bits & 12) == 12):
            self.spanning_root = ra

        self._refresh_color(ra, repaint, absorbed)

    def _refresh_color(self, root, repaint, only):
        """Settle a cluster's color and repaint `only` those of its members.

        `only` matters: near p_c the giant cluster holds thousands of sites,
        and repainting all of them every time one more joins is what turns a
        cheap sweep into a stall. The one case worth the full sweep is the
        frame a cluster crosses into vivid -- it lights up all at once.
        """
        if self.size[root] >= VIVID_THRESHOLD and self.color[root] is None:
            self.color[root] = self._next_vivid()
            only = self.members[root]
        col = self.color[root] or DIM_CLUSTER_COLOR
        for i in only:
            repaint(i, col)

    def spanning_members(self):
        if self.spanning_root is None:
            return ()
        return self.members[self.find(self.spanning_root)]


class Percolation(Visual):
    name = "PERCOLATION"
    description = "Critical threshold"
    category = "math"
    GUIDE = {
        'desc': 'A phase transition in connectivity. Below a critical threshold, clusters stay isolated. Above it, a spanning cluster suddenly connects the entire grid.',
        'credit': 'Broadbent & Hammersley, 1957',
    }

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.p = P_MIN
        self.idle_timer = 0.0
        self.auto_sweep = True
        self.hold_timer = 0.0
        self.overlay_timer = 2.0
        self.spans_flash_timer = 0.0
        self._deal()

    def _deal(self):
        """Deal a fresh hidden threshold per site and flood back up to p."""
        self._pixels = [BLOCKED_COLOR] * (W * H)
        self.lattice = _Lattice()
        self._spanning_cache = ()
        self._had_spanning = False
        self.lattice.open_to(self.p, self._repaint)
        self._sync_spanning()

    def _repaint(self, idx, color):
        self._pixels[idx] = color

    def _set_p(self, p):
        """Move p. Rising just opens more sites; falling re-deals, because a
        site that has opened cannot un-open without rebuilding the clusters."""
        p = min(P_MAX, max(P_MIN, p))
        if p < self.p:
            self.p = p
            self._deal()
            return
        self.p = p
        self.lattice.open_to(p, self._repaint)
        self._sync_spanning()

    def _sync_spanning(self):
        self._spanning_cache = self.lattice.spanning_members()
        if self._spanning_cache and not self._had_spanning:
            self._had_spanning = True
            self.spans_flash_timer = 3.0

    # -- input --------------------------------------------------------

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.action_l or input_state.action_r:
            self.p = P_MIN
            self._deal()
            self.overlay_timer = 2.0
            self.idle_timer = 0.0
            self.auto_sweep = False
            consumed = True

        if input_state.left_pressed:
            self._set_p(round(self.p - 0.01, 3))
            self.overlay_timer = 2.0
            self.idle_timer = 0.0
            self.auto_sweep = False
            consumed = True
        if input_state.right_pressed:
            self._set_p(round(self.p + 0.01, 3))
            self.overlay_timer = 2.0
            self.idle_timer = 0.0
            self.auto_sweep = False
            consumed = True

        return consumed

    # -- update -------------------------------------------------------

    def update(self, dt: float):
        self.time += dt
        if self.overlay_timer > 0:
            self.overlay_timer -= dt
        if self.spans_flash_timer > 0:
            self.spans_flash_timer -= dt

        if not self.auto_sweep:
            self.idle_timer += dt
            if self.idle_timer >= 6.0:
                self.auto_sweep = True
                self.p = P_MIN
                self.hold_timer = 0.0
                self._deal()
            return

        if self.hold_timer > 0:
            self.hold_timer -= dt
            return

        # Crawl through the transition and hurry along the dull ends, so the
        # interesting 0.55-0.62 window gets most of the screen time.
        dist = abs(self.p - P_CRIT)
        speed = 0.010 if dist < 0.04 else (0.030 if dist < 0.12 else 0.055)
        self._set_p(self.p + speed * dt)

        if self._spanning_cache and self.hold_timer <= 0 and self.p >= P_CRIT:
            # Let the spanning cluster sit for a beat, then start over.
            if self.p >= P_CRIT + 0.06:
                self.hold_timer = 3.0
                self.p = P_MIN
                self._deal()
                self.overlay_timer = 2.0

    # -- draw ---------------------------------------------------------

    def draw(self):
        d = self.display
        d.clear()
        set_pixel = d.set_pixel
        pixels = self._pixels

        i = 0
        for y in range(H):
            for x in range(W):
                c = pixels[i]
                i += 1
                if c is not BLOCKED_COLOR:
                    set_pixel(x, y, c)

        # The spanning cluster pulses, but never dims to nothing -- the old
        # build let the pulse bottom out and the punchline vanished mid-swing.
        if self._spanning_cache:
            pulse = 0.88 + 0.12 * math.sin(self.time * 3.5)
            span_col = (min(255, int(255 * pulse)),
                        min(255, int(225 * pulse)),
                        min(255, int(130 * pulse)))
            for idx in self._spanning_cache:
                set_pixel(idx % W, idx // W, span_col)

        self._draw_hud()

        if self.spans_flash_timer > 0:
            alpha = min(1.0, self.spans_flash_timer / 0.5)
            flash = 0.5 + 0.5 * math.sin(self.time * 8.0)
            b = int(255 * alpha * (0.55 + 0.45 * flash))
            d.draw_text_small(2, 2, "SPANS!", (b, b, min(255, int(b * 0.6))))

    def _draw_hud(self):
        d = self.display
        set_pixel = d.set_pixel

        near_crit = abs(self.p - P_CRIT) < 0.015
        spanning = bool(self._spanning_cache)

        # p readout, left of the scale.
        if spanning:
            text_col = (255, 210, 110)
        elif near_crit:
            text_col = (255, 150, 60)
        else:
            text_col = (150, 160, 200)
        d.draw_text_small(1, HUD_Y, f"P{self.p:.2f}"[:5], text_col)

        # Scale bar: filled proportion of the P_MIN..P_MAX window.
        span = P_MAX - P_MIN
        width = W - BAR_X0
        fill = int(round((self.p - P_MIN) / span * width))
        crit_x = BAR_X0 + int(round((P_CRIT - P_MIN) / span * width))
        bar_col = (255, 150, 50) if near_crit else (70, 95, 160)
        for x in range(BAR_X0, W):
            lit = x - BAR_X0 < fill
            set_pixel(x, BAR_Y, bar_col if lit else (10, 10, 18))
            set_pixel(x, BAR_Y + 1, bar_col if lit else (10, 10, 18))

        # Critical-threshold tick, above and below the bar.
        if BAR_X0 <= crit_x < W:
            set_pixel(crit_x, BAR_Y - 1, (200, 90, 70))
            set_pixel(crit_x, BAR_Y + 2, (200, 90, 70))
