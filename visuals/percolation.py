"""
Percolation - Phase Transition
===============================
Site percolation on a 64x64 grid. Each cell is open with probability p.
At the critical threshold (p ~ 0.593), a giant cluster suddenly connects
across the entire grid -- a dramatic phase transition.

The auto-sweep slowly raises p from below critical to above, lingering
at the transition so you can watch the spanning cluster ignite.

Controls:
  Left/Right  - Adjust occupation probability p
  Action      - Regenerate grid
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

SMALL_THRESHOLD = 8
MEDIUM_THRESHOLD = 40

BLOCKED_COLOR = (4, 3, 8)
DIM_CLUSTER_COLOR = (25, 25, 35)

P_CRIT = 0.593
N = GRID_SIZE  # 64


class _UnionFind:
    """Weighted quick-union with path compression."""
    __slots__ = ('parent', 'rank')

    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x):
        p = self.parent
        while p[x] != x:
            p[x] = p[p[x]]
            x = p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1


class Percolation(Visual):
    name = "PERCOLATION"
    description = "Critical threshold"
    category = "automata"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.p = 0.50

        # Pre-baked pixel buffer: (r,g,b) per pixel, set in _generate()
        self._pixels = [[(0, 0, 0)] * N for _ in range(N)]
        # List of (x, y) coords that belong to the spanning cluster (for pulse)
        self._spanning_coords = []
        self.has_spanning = False

        # Overlay
        self.overlay_timer = 0.0
        self.spans_flash_timer = 0.0

        # Auto-sweep
        self.idle_timer = 0.0
        self.auto_sweep = False
        self.sweep_p = 0.40
        self.sweep_speed = 0.01
        self.sweep_interval = 0.8
        self.sweep_timer = 0.0
        self.sweep_pause = 0.0

        self._generate()

    def _generate(self):
        """Generate grid, compute clusters, and pre-bake the pixel buffer."""
        p = self.p

        # Random grid (flat list for speed)
        grid = [random.random() < p for _ in range(N * N)]

        # Union-Find
        uf = _UnionFind(N * N)
        for y in range(N):
            row = y * N
            for x in range(N):
                idx = row + x
                if not grid[idx]:
                    continue
                if x + 1 < N and grid[idx + 1]:
                    uf.union(idx, idx + 1)
                if y + 1 < N and grid[idx + N]:
                    uf.union(idx, idx + N)

        # Compute cluster sizes by root
        root_sizes = {}
        for idx in range(N * N):
            if grid[idx]:
                root = uf.find(idx)
                root_sizes[root] = root_sizes.get(root, 0) + 1

        # Detect spanning clusters (left↔right or top↔bottom)
        left_roots = set()
        right_roots = set()
        top_roots = set()
        bottom_roots = set()
        for i in range(N):
            idx = i * N  # left column
            if grid[idx]:
                left_roots.add(uf.find(idx))
            idx = i * N + N - 1  # right column
            if grid[idx]:
                right_roots.add(uf.find(idx))
            idx = i  # top row
            if grid[idx]:
                top_roots.add(uf.find(idx))
            idx = (N - 1) * N + i  # bottom row
            if grid[idx]:
                bottom_roots.add(uf.find(idx))

        spanning_roots = (left_roots & right_roots) | (top_roots & bottom_roots)
        self.has_spanning = len(spanning_roots) > 0

        # Assign colors to roots by size (largest get vivid colors)
        sorted_roots = sorted(root_sizes.items(), key=lambda x: -x[1])
        root_colors = {}
        vivid_idx = 0
        for root, size in sorted_roots:
            if root in spanning_roots:
                root_colors[root] = None  # sentinel: spanning
            elif size >= MEDIUM_THRESHOLD:
                root_colors[root] = VIVID_COLORS[vivid_idx % len(VIVID_COLORS)]
                vivid_idx += 1
            elif size >= SMALL_THRESHOLD:
                base = VIVID_COLORS[vivid_idx % len(VIVID_COLORS)]
                root_colors[root] = (base[0] // 3, base[1] // 3, base[2] // 3)
                vivid_idx += 1
            else:
                root_colors[root] = DIM_CLUSTER_COLOR

        # Pre-bake pixel buffer and collect spanning coords
        pixels = self._pixels
        spanning_coords = []
        for y in range(N):
            row = pixels[y]
            for x in range(N):
                idx = y * N + x
                if not grid[idx]:
                    row[x] = BLOCKED_COLOR
                    continue
                root = uf.find(idx)
                col = root_colors.get(root, DIM_CLUSTER_COLOR)
                if col is None:
                    # Spanning cluster: store base gold, will pulse in draw()
                    row[x] = (255, 220, 120)  # base color, overwritten each frame
                    spanning_coords.append((x, y))
                else:
                    row[x] = col

        self._spanning_coords = spanning_coords

        # Overlays
        self.overlay_timer = 2.0
        if self.has_spanning:
            self.spans_flash_timer = 3.0

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.action_l or input_state.action_r:
            self._generate()
            self.idle_timer = 0.0
            self.auto_sweep = False
            consumed = True

        if input_state.left_pressed:
            self.p = max(0.20, round(self.p - 0.01, 2))
            self._generate()
            self.idle_timer = 0.0
            self.auto_sweep = False
            consumed = True
        if input_state.right_pressed:
            self.p = min(0.80, round(self.p + 0.01, 2))
            self._generate()
            self.idle_timer = 0.0
            self.auto_sweep = False
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt

        if self.overlay_timer > 0:
            self.overlay_timer -= dt
        if self.spans_flash_timer > 0:
            self.spans_flash_timer -= dt

        # Auto-sweep
        if not self.auto_sweep:
            self.idle_timer += dt
            if self.idle_timer >= 6.0:
                self.auto_sweep = True
                self.sweep_p = 0.40
                self.sweep_timer = 0.0
                self.sweep_pause = 0.0
                self.p = self.sweep_p
                self._generate()
        else:
            if self.sweep_pause > 0:
                self.sweep_pause -= dt
                return

            self.sweep_timer += dt
            if self.sweep_timer >= self.sweep_interval:
                self.sweep_timer -= self.sweep_interval
                self.sweep_p += self.sweep_speed

                if self.sweep_p > 0.72:
                    self.sweep_p = 0.40
                    self.sweep_timer = 0.0
                    self.sweep_pause = 2.0

                self.p = round(self.sweep_p, 3)
                self._generate()

                if abs(self.p - P_CRIT) < 0.03:
                    self.sweep_pause = 1.5

    def draw(self):
        d = self.display
        d.clear()
        set_pixel = d.set_pixel
        t = self.time

        # Blit pre-baked pixel buffer (fast: no per-pixel logic)
        pixels = self._pixels
        for y in range(N):
            row = pixels[y]
            for x in range(N):
                c = row[x]
                if c != BLOCKED_COLOR:
                    set_pixel(x, y, c)

        # Pulse spanning cluster pixels (only those, not all 4096)
        if self._spanning_coords:
            pulse = 0.55 + 0.45 * math.sin(t * 3.5)
            hue_t = t * 0.4
            sr = int(255 * (0.9 + 0.1 * math.sin(hue_t)) * pulse)
            sg = int(220 * (0.8 + 0.2 * math.sin(hue_t + 1.0)) * pulse)
            sb = int(120 * (0.6 + 0.4 * math.sin(hue_t + 2.0)) * pulse)
            sr = min(255, sr)
            sg = min(255, sg)
            sb = min(255, sb)
            span_col = (sr, sg, sb)
            for x, y in self._spanning_coords:
                set_pixel(x, y, span_col)

        # P-value bar at bottom (row 63)
        bar_fill = int(self.p * N)
        near_crit = abs(self.p - P_CRIT) < 0.015
        crit_pixel = int(P_CRIT * N)

        for x in range(N):
            if x < bar_fill:
                if near_crit:
                    set_pixel(x, 63, (255, 140, 40))
                else:
                    set_pixel(x, 63, (60, 80, 140))
            else:
                set_pixel(x, 63, (8, 8, 15))

        # Critical threshold tick
        set_pixel(crit_pixel, 62, (120, 60, 60))

        # "SPANS!" flash
        if self.spans_flash_timer > 0 and self.has_spanning:
            alpha = min(1.0, self.spans_flash_timer / 0.5)
            flash = 0.5 + 0.5 * math.sin(t * 8.0)
            bright = int(255 * alpha * (0.5 + 0.5 * flash))
            col = (bright, bright, min(255, int(bright * 0.6)))
            d.draw_text_small(2, 2, "SPANS!", col)

        # P value overlay
        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            p_str = f"P {self.p:.2f}"
            c = int(200 * alpha)
            d.draw_text_small(2, 56, p_str, (c, c, int(220 * alpha)))
