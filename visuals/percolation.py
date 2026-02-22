"""
Percolation - Critical Threshold
==================================
Bond/site percolation on a 64x64 grid. Each cell (or bond) is open
with probability p. Connected clusters of open cells are flood-filled
with distinct colors. At the critical threshold (p ~ 0.593 for site,
p = 0.50 for bond), a giant cluster suddenly spans the entire grid --
a dramatic phase transition.

Part of a phase-transition trilogy with Sandpile and Crystallize.

Controls:
  Left/Right  - Adjust occupation probability p
  Up/Down     - Toggle bond vs. site percolation
  Action      - Regenerate grid
  Escape      - Exit
"""

import random
import math
from . import Visual, Display, Colors, GRID_SIZE

# Distinct vivid colors for clusters, assigned by size rank
CLUSTER_COLORS = [
    (255, 60, 60), (60, 180, 255), (60, 255, 100), (255, 200, 40),
    (200, 60, 255), (255, 120, 40), (40, 255, 220), (255, 60, 180),
    (120, 255, 60), (60, 60, 255), (255, 160, 200), (200, 255, 60),
    (180, 120, 255), (255, 80, 120), (80, 220, 160),
]

BLOCKED_COLOR = (5, 5, 15)
SPAN_COLOR_BASE = (255, 240, 200)  # bright gold/white for spanning cluster


class _UnionFind:
    """Weighted quick-union with path compression."""
    __slots__ = ('parent', 'rank')

    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x):
        p = self.parent
        while p[x] != x:
            p[x] = p[p[x]]  # path halving
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
        self.p = 0.50  # occupation probability, start just below site critical
        self.bond_mode = False  # False = site, True = bond

        # Grid state
        self.grid_open = None       # [y][x] bool -- cell open?
        self.cluster_id = None      # [y][x] int -- cluster label (-1 if blocked)
        self.cluster_colors = {}    # cluster_id -> (r,g,b)
        self.spanning_ids = set()   # cluster ids that span
        self.num_clusters = 0

        # Bond arrays (only used in bond mode)
        self.h_bonds = None  # [y][x] bool -- horizontal bond to right neighbor
        self.v_bonds = None  # [y][x] bool -- vertical bond to downward neighbor

        # Animation state
        self.reveal_order = []      # list of (cluster_id, size) sorted large-first
        self.reveal_idx = 0         # how many clusters revealed so far
        self.reveal_timer = 0.0
        self.reveal_done = False
        self.clusters_per_frame = 4

        # Overlay for "SPANS!" text and mode/p display
        self.overlay_timer = 0.0
        self.spans_timer = 0.0

        # Auto-sweep
        self.idle_timer = 0.0
        self.auto_sweep = False
        self.sweep_p = 0.30
        self.sweep_dir = 1  # +1 = increasing, -1 = decreasing
        self.sweep_regen_timer = 0.0

        # Generate initial grid
        self._generate()

    def _generate(self):
        """Generate a new random grid and compute clusters."""
        N = GRID_SIZE

        if self.bond_mode:
            self._generate_bond()
        else:
            self._generate_site()

        # Build reveal order: clusters sorted by size, largest first
        cluster_sizes = {}
        for y in range(N):
            for x in range(N):
                cid = self.cluster_id[y][x]
                if cid >= 0:
                    cluster_sizes[cid] = cluster_sizes.get(cid, 0) + 1

        self.num_clusters = len(cluster_sizes)

        # Detect spanning: touches left+right OR top+bottom
        left_ids = set()
        right_ids = set()
        top_ids = set()
        bottom_ids = set()
        for i in range(N):
            cid = self.cluster_id[i][0]
            if cid >= 0:
                left_ids.add(cid)
            cid = self.cluster_id[i][N - 1]
            if cid >= 0:
                right_ids.add(cid)
            cid = self.cluster_id[0][i]
            if cid >= 0:
                top_ids.add(cid)
            cid = self.cluster_id[N - 1][i]
            if cid >= 0:
                bottom_ids.add(cid)

        self.spanning_ids = (left_ids & right_ids) | (top_ids & bottom_ids)

        # Sort clusters by size descending
        sorted_clusters = sorted(cluster_sizes.items(), key=lambda x: -x[1])

        # Assign colors: spanning clusters get special treatment, rest get palette
        self.cluster_colors = {}
        color_idx = 0
        for cid, size in sorted_clusters:
            if cid in self.spanning_ids:
                self.cluster_colors[cid] = SPAN_COLOR_BASE  # will pulse in draw
            else:
                self.cluster_colors[cid] = CLUSTER_COLORS[color_idx % len(CLUSTER_COLORS)]
                color_idx += 1

        # Reveal animation setup
        self.reveal_order = sorted_clusters
        self.reveal_idx = 0
        self.reveal_timer = 0.0
        self.reveal_done = False

        # Show overlay
        self.overlay_timer = 2.5
        if self.spanning_ids:
            self.spans_timer = 3.0

    def _generate_site(self):
        """Site percolation: each cell open with probability p."""
        N = GRID_SIZE
        p = self.p

        # Random grid
        self.grid_open = [[random.random() < p for _ in range(N)] for _ in range(N)]
        self.h_bonds = None
        self.v_bonds = None

        # Union-Find for connected components (4-connectivity)
        uf = _UnionFind(N * N)
        open_grid = self.grid_open

        for y in range(N):
            for x in range(N):
                if not open_grid[y][x]:
                    continue
                idx = y * N + x
                # Right neighbor
                if x + 1 < N and open_grid[y][x + 1]:
                    uf.union(idx, y * N + x + 1)
                # Down neighbor
                if y + 1 < N and open_grid[y + 1][x]:
                    uf.union(idx, (y + 1) * N + x)

        # Build cluster_id grid
        self.cluster_id = [[-1] * N for _ in range(N)]
        root_map = {}
        next_id = 0
        for y in range(N):
            for x in range(N):
                if not open_grid[y][x]:
                    continue
                root = uf.find(y * N + x)
                if root not in root_map:
                    root_map[root] = next_id
                    next_id += 1
                self.cluster_id[y][x] = root_map[root]

    def _generate_bond(self):
        """Bond percolation: all cells open, edges open with probability p."""
        N = GRID_SIZE
        p = self.p

        # All cells are open in bond percolation
        self.grid_open = [[True] * N for _ in range(N)]

        # Random bonds
        self.h_bonds = [[random.random() < p for _ in range(N)] for _ in range(N)]
        self.v_bonds = [[random.random() < p for _ in range(N)] for _ in range(N)]

        # Union-Find: connectivity via open bonds only
        uf = _UnionFind(N * N)

        for y in range(N):
            for x in range(N):
                idx = y * N + x
                # Right bond
                if x + 1 < N and self.h_bonds[y][x]:
                    uf.union(idx, y * N + x + 1)
                # Down bond
                if y + 1 < N and self.v_bonds[y][x]:
                    uf.union(idx, (y + 1) * N + x)

        # Build cluster_id grid
        self.cluster_id = [[-1] * N for _ in range(N)]
        root_map = {}
        next_id = 0
        for y in range(N):
            for x in range(N):
                root = uf.find(y * N + x)
                if root not in root_map:
                    root_map[root] = next_id
                    next_id += 1
                self.cluster_id[y][x] = root_map[root]

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Action: regenerate
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
            self.overlay_timer = 2.5
            consumed = True
        if input_state.right_pressed:
            self.p = min(0.80, round(self.p + 0.01, 2))
            self._generate()
            self.idle_timer = 0.0
            self.auto_sweep = False
            self.overlay_timer = 2.5
            consumed = True

        # Up/Down: toggle bond vs site
        if input_state.up_pressed or input_state.down_pressed:
            self.bond_mode = not self.bond_mode
            self._generate()
            self.idle_timer = 0.0
            self.auto_sweep = False
            self.overlay_timer = 2.5
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt

        # Decrement overlay timers
        if self.overlay_timer > 0:
            self.overlay_timer -= dt
        if self.spans_timer > 0:
            self.spans_timer -= dt

        # Reveal animation: reveal clusters progressively
        if not self.reveal_done:
            self.reveal_timer += dt
            # Reveal a batch of clusters per tick
            clusters_to_reveal = max(1, int(self.num_clusters * dt * 3))
            # At minimum reveal a few per frame so it doesn't drag
            clusters_to_reveal = max(clusters_to_reveal, self.clusters_per_frame)
            self.reveal_idx = min(self.reveal_idx + clusters_to_reveal,
                                  len(self.reveal_order))
            if self.reveal_idx >= len(self.reveal_order):
                self.reveal_done = True

        # Auto-sweep logic
        if not self.auto_sweep:
            self.idle_timer += dt
            if self.idle_timer >= 5.0:
                self.auto_sweep = True
                self.sweep_p = 0.30
                self.sweep_dir = 1
                self.sweep_regen_timer = 0.0
                self.p = self.sweep_p
                self._generate()
        else:
            self.sweep_regen_timer += dt
            if self.sweep_regen_timer >= 1.5:
                self.sweep_regen_timer -= 1.5
                # Advance p
                self.sweep_p += self.sweep_dir * 0.02
                if self.sweep_p >= 0.75:
                    self.sweep_p = 0.75
                    self.sweep_dir = -1
                elif self.sweep_p <= 0.30:
                    self.sweep_p = 0.30
                    self.sweep_dir = 1
                self.p = round(self.sweep_p, 2)
                self._generate()

    def draw(self):
        d = self.display
        N = GRID_SIZE

        # Build set of revealed cluster IDs
        revealed = set()
        for i in range(self.reveal_idx):
            revealed.add(self.reveal_order[i][0])

        # Pulse factor for spanning cluster
        pulse = 0.5 + 0.5 * math.sin(self.time * 4.0)

        grid_open = self.grid_open
        cluster_id = self.cluster_id
        spanning = self.spanning_ids
        colors = self.cluster_colors
        set_pixel = d.set_pixel

        for y in range(N):
            for x in range(N):
                if not grid_open[y][x]:
                    set_pixel(x, y, BLOCKED_COLOR)
                    continue

                cid = cluster_id[y][x]
                if cid < 0 or cid not in revealed:
                    # Not yet revealed or no cluster -- dark open cell
                    set_pixel(x, y, (12, 12, 20))
                    continue

                base = colors.get(cid, (80, 80, 80))

                if cid in spanning:
                    # Pulse between gold and bright white
                    r = int(base[0] * (0.6 + 0.4 * pulse))
                    g = int(base[1] * (0.6 + 0.4 * pulse))
                    b = int(base[2] * (0.5 + 0.5 * pulse))
                    set_pixel(x, y, (min(255, r), min(255, g), min(255, b)))
                else:
                    set_pixel(x, y, base)

        # HUD overlay
        alpha = min(1.0, self.overlay_timer / 0.5) if self.overlay_timer > 0 else 0
        if alpha > 0:
            mode_str = "BOND" if self.bond_mode else "SITE"
            p_str = f"p={self.p:.2f}"
            c_str = f"{self.num_clusters} clusters"

            def fade(c):
                return tuple(int(v * alpha) for v in c)

            d.draw_text_small(2, 2, mode_str, fade((200, 200, 255)))
            d.draw_text_small(2, 8, p_str, fade((255, 255, 200)))
            d.draw_text_small(2, 14, c_str, fade((180, 180, 180)))

            # Critical threshold indicator
            crit = 0.50 if self.bond_mode else 0.593
            if abs(self.p - crit) < 0.03:
                d.draw_text_small(2, 20, "~CRITICAL~", fade((255, 100, 100)))

        # "SPANS!" flash
        if self.spans_timer > 0 and self.spanning_ids:
            sa = min(1.0, self.spans_timer / 0.5)
            flash = 0.5 + 0.5 * math.sin(self.time * 8.0)
            bright = int(255 * sa * (0.5 + 0.5 * flash))
            d.draw_text_small(2, 56, "SPANS!", (bright, bright, min(255, int(bright * 0.7))))
