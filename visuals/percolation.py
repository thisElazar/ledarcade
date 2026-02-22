"""
Percolation - Phase Transition
===============================
Site percolation on a 64x64 grid. Each cell is open with probability p.
At the critical threshold (p ~ 0.593), a giant cluster suddenly connects
across the entire grid -- a dramatic phase transition.

Controls:
  Left/Right  - Adjust occupation probability p
  Action      - Regenerate grid
"""

import random
import math
from . import Visual, Display, Colors, GRID_SIZE

# Small clusters are dim gray; large ones get vivid colors from this palette
VIVID_COLORS = [
    (60, 180, 255), (60, 255, 100), (255, 200, 40),
    (200, 60, 255), (255, 120, 40), (40, 255, 220),
    (255, 60, 180), (120, 255, 60), (255, 80, 120),
]

# Size thresholds for coloring (cells in cluster)
SMALL_THRESHOLD = 8       # below this: dim
MEDIUM_THRESHOLD = 40     # below this: muted color

BLOCKED_COLOR = (4, 3, 8)
DIM_CLUSTER_COLOR = (25, 25, 35)

# Critical threshold for site percolation on a square lattice
P_CRIT = 0.593


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

        # Grid state
        self.grid_open = None
        self.cluster_id = None       # [y][x] int, -1 if blocked
        self.cluster_sizes = {}      # cluster_id -> size
        self.cluster_colors = {}     # cluster_id -> (r,g,b)
        self.spanning_ids = set()
        self.has_spanning = False

        # Overlay
        self.overlay_timer = 0.0
        self.spans_flash_timer = 0.0

        # Auto-sweep: idle triggers a slow sweep from low p to high
        self.idle_timer = 0.0
        self.auto_sweep = False
        self.sweep_p = 0.30
        self.sweep_speed = 0.012     # p increment per step
        self.sweep_interval = 0.8    # seconds between steps
        self.sweep_timer = 0.0
        self.sweep_pause = 0.0       # extra pause near critical threshold

        self._generate()

    def _generate(self):
        """Generate grid and compute clusters via union-find."""
        N = GRID_SIZE
        p = self.p

        # Random grid
        grid = [[random.random() < p for _ in range(N)] for _ in range(N)]
        self.grid_open = grid

        # Union-Find for connected components
        uf = _UnionFind(N * N)
        for y in range(N):
            for x in range(N):
                if not grid[y][x]:
                    continue
                idx = y * N + x
                if x + 1 < N and grid[y][x + 1]:
                    uf.union(idx, idx + 1)
                if y + 1 < N and grid[y + 1][x]:
                    uf.union(idx, idx + N)

        # Assign cluster IDs
        cluster_id = [[-1] * N for _ in range(N)]
        root_map = {}
        next_id = 0
        for y in range(N):
            for x in range(N):
                if not grid[y][x]:
                    continue
                root = uf.find(y * N + x)
                if root not in root_map:
                    root_map[root] = next_id
                    next_id += 1
                cluster_id[y][x] = root_map[root]
        self.cluster_id = cluster_id

        # Compute cluster sizes
        sizes = {}
        for y in range(N):
            for x in range(N):
                cid = cluster_id[y][x]
                if cid >= 0:
                    sizes[cid] = sizes.get(cid, 0) + 1
        self.cluster_sizes = sizes

        # Detect spanning: left-right or top-bottom
        left_ids = set()
        right_ids = set()
        top_ids = set()
        bottom_ids = set()
        for i in range(N):
            c = cluster_id[i][0]
            if c >= 0:
                left_ids.add(c)
            c = cluster_id[i][N - 1]
            if c >= 0:
                right_ids.add(c)
            c = cluster_id[0][i]
            if c >= 0:
                top_ids.add(c)
            c = cluster_id[N - 1][i]
            if c >= 0:
                bottom_ids.add(c)

        self.spanning_ids = (left_ids & right_ids) | (top_ids & bottom_ids)
        self.has_spanning = len(self.spanning_ids) > 0

        # Assign colors based on cluster size
        # Sort clusters by size descending to assign vivid colors to largest
        sorted_clusters = sorted(sizes.items(), key=lambda x: -x[1])
        self.cluster_colors = {}
        vivid_idx = 0
        for cid, size in sorted_clusters:
            if cid in self.spanning_ids:
                # Spanning cluster: bright gold, will pulse in draw()
                self.cluster_colors[cid] = None  # sentinel: handled specially
            elif size >= MEDIUM_THRESHOLD:
                self.cluster_colors[cid] = VIVID_COLORS[vivid_idx % len(VIVID_COLORS)]
                vivid_idx += 1
            elif size >= SMALL_THRESHOLD:
                # Muted version of a vivid color
                base = VIVID_COLORS[vivid_idx % len(VIVID_COLORS)]
                self.cluster_colors[cid] = (base[0] // 3, base[1] // 3, base[2] // 3)
                vivid_idx += 1
            else:
                self.cluster_colors[cid] = DIM_CLUSTER_COLOR

        # Show overlay briefly
        self.overlay_timer = 2.0
        if self.has_spanning:
            self.spans_flash_timer = 3.0

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Action: regenerate at current p
        if input_state.action_l or input_state.action_r:
            self._generate()
            self.idle_timer = 0.0
            self.auto_sweep = False
            consumed = True

        # Left/Right: adjust p
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

        # Auto-sweep: start after idle period
        if not self.auto_sweep:
            self.idle_timer += dt
            if self.idle_timer >= 6.0:
                self.auto_sweep = True
                self.sweep_p = 0.30
                self.sweep_timer = 0.0
                self.sweep_pause = 0.0
                self.p = self.sweep_p
                self._generate()
        else:
            # Handle pause near critical threshold
            if self.sweep_pause > 0:
                self.sweep_pause -= dt
                return

            self.sweep_timer += dt
            interval = self.sweep_interval
            if self.sweep_timer >= interval:
                self.sweep_timer -= interval
                self.sweep_p += self.sweep_speed

                if self.sweep_p > 0.78:
                    # Reset: start over from low
                    self.sweep_p = 0.30
                    self.sweep_timer = 0.0
                    self.sweep_pause = 2.0  # pause before restarting

                self.p = round(self.sweep_p, 3)
                self._generate()

                # Pause longer near critical threshold for dramatic effect
                if abs(self.p - P_CRIT) < 0.03:
                    self.sweep_pause = 1.5

    def draw(self):
        d = self.display
        N = GRID_SIZE
        t = self.time

        grid_open = self.grid_open
        cluster_id = self.cluster_id
        spanning = self.spanning_ids
        colors = self.cluster_colors
        set_pixel = d.set_pixel

        # Spanning cluster pulse: strong, slow throb
        # Oscillates brightness between 0.55 and 1.0 for a vivid glow
        pulse = 0.55 + 0.45 * math.sin(t * 3.5)

        # Spanning cluster base hue shifts slowly for visual interest
        span_hue_t = t * 0.4
        span_r = int(255 * (0.9 + 0.1 * math.sin(span_hue_t)))
        span_g = int(220 * (0.8 + 0.2 * math.sin(span_hue_t + 1.0)))
        span_b = int(120 * (0.6 + 0.4 * math.sin(span_hue_t + 2.0)))

        for y in range(N):
            row_open = grid_open[y]
            row_cid = cluster_id[y]
            for x in range(N):
                if not row_open[x]:
                    set_pixel(x, y, BLOCKED_COLOR)
                    continue

                cid = row_cid[x]
                if cid < 0:
                    set_pixel(x, y, BLOCKED_COLOR)
                    continue

                if cid in spanning:
                    # Pulsing golden glow for spanning cluster
                    r = min(255, int(span_r * pulse))
                    g = min(255, int(span_g * pulse))
                    b = min(255, int(span_b * pulse))
                    set_pixel(x, y, (r, g, b))
                else:
                    c = colors.get(cid, DIM_CLUSTER_COLOR)
                    set_pixel(x, y, c)

        # --- HUD: minimal ---

        # P-value bar at bottom (row 62-63): a thin horizontal bar
        # showing p as a fill level across the 64-pixel width
        bar_fill = int(self.p * N)
        near_crit = abs(self.p - P_CRIT) < 0.015
        crit_pixel = int(P_CRIT * N)  # mark where critical threshold is

        for x in range(N):
            if x < bar_fill:
                if near_crit:
                    # Near critical: bar glows warm
                    set_pixel(x, 63, (255, 140, 40))
                else:
                    # Subtle blue-white fill
                    set_pixel(x, 63, (60, 80, 140))
            else:
                set_pixel(x, 63, (8, 8, 15))

        # Tick mark at critical threshold
        set_pixel(crit_pixel, 62, (120, 60, 60))

        # "SPANS!" overlay when spanning cluster detected
        if self.spans_flash_timer > 0 and self.has_spanning:
            alpha = min(1.0, self.spans_flash_timer / 0.5)
            flash = 0.5 + 0.5 * math.sin(t * 8.0)
            bright = int(255 * alpha * (0.5 + 0.5 * flash))
            col = (bright, bright, min(255, int(bright * 0.6)))
            d.draw_text_small(2, 2, "SPANS!", col)

        # P value shown briefly on overlay
        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            p_str = f"P {self.p:.2f}"
            col = tuple(int(v * alpha) for v in (200, 200, 220))
            d.draw_text_small(2, 56, p_str, col)
