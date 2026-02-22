"""
Network - Small-World & Scale-Free Graphs
==========================================
Watts-Strogatz and Barabasi-Albert network models on a 64x64 LED grid.

Ring lattice with rewiring probability p. At p~0.1: small-world regime
(high clustering AND short paths). Signal propagation animated from a
source node via BFS -- the "six degrees" moment.

In a regular lattice (p=0), signal crawls around the ring (~30 hops).
Add just a few shortcuts (p=0.1) and it arrives almost instantly (~3-5 hops).

Controls:
  Left/Right  - Adjust rewiring probability p
  Up/Down     - Toggle Watts-Strogatz / Barabasi-Albert
  Action      - Send signal pulse from random node
  Escape      - Exit
"""

import random
import math
from collections import deque
from . import Visual, Display, Colors, GRID_SIZE


# --- Colors ---
COLOR_BG = (5, 5, 12)
COLOR_NODE_IDLE = (40, 120, 160)
COLOR_EDGE_NORMAL = (20, 30, 40)
COLOR_EDGE_SHORTCUT = (40, 50, 70)
COLOR_SIGNAL_ACTIVE = (255, 255, 220)
COLOR_SIGNAL_YELLOW = (255, 200, 60)
COLOR_SIGNAL_ORANGE = (255, 120, 30)
COLOR_SIGNAL_RED = (200, 60, 20)

# --- Network parameters ---
NUM_NODES = 56
K_NEIGHBORS = 4          # each-side count = K/2 = 2
CIRCLE_RADIUS = 24.5
CENTER_X = 31.5
CENTER_Y = 31.5
SIGNAL_HOP_TIME = 0.30   # seconds per BFS hop
SIGNAL_FADE_TIME = 1.8   # seconds for activated nodes to fade back to idle
IDLE_PULSE_SPEED = 1.5    # Hz for idle breathing


class Network(Visual):
    name = "NETWORK"
    description = "Small-world graphs"
    category = "math"

    def __init__(self, display: Display):
        super().__init__(display)

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------
    def reset(self):
        self.time = 0.0
        self.rewire_p = 0.00
        self.model = 0  # 0 = Watts-Strogatz, 1 = Barabasi-Albert

        # Node positions (fixed circle layout)
        self.node_x = []
        self.node_y = []
        for i in range(NUM_NODES):
            angle = 2.0 * math.pi * i / NUM_NODES - math.pi / 2.0
            self.node_x.append(CENTER_X + CIRCLE_RADIUS * math.cos(angle))
            self.node_y.append(CENTER_Y + CIRCLE_RADIUS * math.sin(angle))

        # Adjacency list and edge metadata
        self.adj = [set() for _ in range(NUM_NODES)]
        self.edges = []          # list of (i, j)
        self.edge_is_shortcut = set()  # set of (min,max) tuples for rewired edges

        # Signal propagation state
        self.signal_active = False
        self.signal_time = [None] * NUM_NODES   # BFS hop number when activated
        self.signal_activated = [0.0] * NUM_NODES  # wall-clock time when activated
        self.signal_max_hops = 0
        self.signal_current_hop = 0
        self.signal_hop_timer = 0.0
        self.bfs_frontier = deque()
        self.bfs_visited = [False] * NUM_NODES
        self.hops_display = ""

        # Overlay
        self.overlay_timer = 0.0

        # Idle timer for auto-demo
        self.idle_timer = 0.0
        self.auto_demo = False
        self.auto_timer = 0.0
        self.auto_phase = 0  # 0=lattice signal, 1=pause, 2=set p=0.10, 3=small-world signal, 4=pause

        # Generate initial network
        self._generate()

    # ------------------------------------------------------------------
    # Network generation
    # ------------------------------------------------------------------
    def _generate(self):
        """Generate network based on current model and parameters."""
        self.adj = [set() for _ in range(NUM_NODES)]
        self.edges = []
        self.edge_is_shortcut = set()
        self._stop_signal()

        if self.model == 0:
            self._generate_watts_strogatz()
        else:
            self._generate_barabasi_albert()

    def _generate_watts_strogatz(self):
        """Watts-Strogatz small-world model."""
        n = NUM_NODES
        k_half = K_NEIGHBORS // 2  # 2

        # Step 1: ring lattice -- connect each node to K nearest neighbors
        ring_edges = []
        for i in range(n):
            for j in range(1, k_half + 1):
                neighbor = (i + j) % n
                ring_edges.append((i, neighbor))
                self.adj[i].add(neighbor)
                self.adj[neighbor].add(i)

        # Step 2: rewire with probability p
        p = self.rewire_p
        for (u, v) in ring_edges:
            if random.random() < p:
                # Remove edge u-v
                if v in self.adj[u]:
                    self.adj[u].discard(v)
                    self.adj[v].discard(u)
                # Pick random new target for u (not self, not existing neighbor)
                candidates = [w for w in range(n) if w != u and w not in self.adj[u]]
                if candidates:
                    w = random.choice(candidates)
                    self.adj[u].add(w)
                    self.adj[w].add(u)
                    # Mark as shortcut
                    key = (min(u, w), max(u, w))
                    self.edge_is_shortcut.add(key)
                else:
                    # No candidates; re-add original
                    self.adj[u].add(v)
                    self.adj[v].add(u)

        # Build edge list
        seen = set()
        for i in range(n):
            for j in self.adj[i]:
                key = (min(i, j), max(i, j))
                if key not in seen:
                    seen.add(key)
                    self.edges.append(key)

    def _generate_barabasi_albert(self):
        """Barabasi-Albert scale-free model with preferential attachment."""
        n = NUM_NODES
        m = 2  # edges per new node

        # Start with m0=3 fully connected nodes
        m0 = 3
        for i in range(m0):
            for j in range(i + 1, m0):
                self.adj[i].add(j)
                self.adj[j].add(i)

        # Degree list for preferential attachment (repeat node id by degree)
        degree_list = []
        for i in range(m0):
            for j in range(m0 - 1):
                degree_list.append(i)

        # Add nodes one at a time
        for new_node in range(m0, n):
            targets = set()
            attempts = 0
            while len(targets) < m and attempts < 200:
                attempts += 1
                if degree_list:
                    candidate = degree_list[random.randint(0, len(degree_list) - 1)]
                else:
                    candidate = random.randint(0, new_node - 1)
                if candidate != new_node and candidate not in targets:
                    targets.add(candidate)

            for t in targets:
                self.adj[new_node].add(t)
                self.adj[t].add(new_node)
                degree_list.append(new_node)
                degree_list.append(t)

        # Build edge list and detect hubs
        seen = set()
        for i in range(n):
            for j in self.adj[i]:
                key = (min(i, j), max(i, j))
                if key not in seen:
                    seen.add(key)
                    self.edges.append(key)

    # ------------------------------------------------------------------
    # Signal propagation
    # ------------------------------------------------------------------
    def _start_signal(self, source=None):
        """Start BFS signal propagation from a random (or given) node."""
        if source is None:
            source = random.randint(0, NUM_NODES - 1)

        self.signal_active = True
        self.signal_time = [None] * NUM_NODES
        self.signal_activated = [0.0] * NUM_NODES
        self.signal_time[source] = 0
        self.signal_activated[source] = self.time
        self.signal_max_hops = 0
        self.signal_current_hop = 0
        self.signal_hop_timer = 0.0
        self.bfs_frontier = deque()
        self.bfs_visited = [False] * NUM_NODES
        self.bfs_visited[source] = True
        self.hops_display = "HOPS: 0"

        # Queue neighbors at hop 1
        for nb in self.adj[source]:
            self.bfs_frontier.append((nb, 1))

    def _stop_signal(self):
        """Reset signal state."""
        self.signal_active = False
        self.signal_time = [None] * NUM_NODES
        self.signal_activated = [0.0] * NUM_NODES
        self.signal_max_hops = 0
        self.signal_current_hop = 0
        self.hops_display = ""

    def _advance_signal(self):
        """Advance BFS by one hop level."""
        if not self.bfs_frontier:
            return False  # done

        next_hop = None
        newly_activated = []

        while self.bfs_frontier:
            node, hop = self.bfs_frontier[0]
            if next_hop is None:
                next_hop = hop
            if hop != next_hop:
                break  # next hop level -- stop here
            self.bfs_frontier.popleft()

            if self.bfs_visited[node]:
                continue
            self.bfs_visited[node] = True
            self.signal_time[node] = hop
            self.signal_activated[node] = self.time
            newly_activated.append(node)
            if hop > self.signal_max_hops:
                self.signal_max_hops = hop

            # Enqueue neighbors
            for nb in self.adj[node]:
                if not self.bfs_visited[nb]:
                    self.bfs_frontier.append((nb, hop + 1))

        if next_hop is not None:
            self.signal_current_hop = next_hop
            self.hops_display = f"HOPS: {next_hop}"

        return bool(self.bfs_frontier)

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------
    def handle_input(self, input_state) -> bool:
        consumed = False

        # Action: send signal pulse
        if input_state.action_l or input_state.action_r:
            self._start_signal()
            self.idle_timer = 0.0
            self.auto_demo = False
            consumed = True

        # Left/Right: adjust rewiring probability
        if input_state.left:
            old_p = self.rewire_p
            self.rewire_p = max(0.00, round(self.rewire_p - 0.02, 2))
            if self.rewire_p != old_p:
                self._generate()
                self.overlay_timer = 2.0
            self.idle_timer = 0.0
            self.auto_demo = False
            consumed = True
        if input_state.right:
            old_p = self.rewire_p
            self.rewire_p = min(1.00, round(self.rewire_p + 0.02, 2))
            if self.rewire_p != old_p:
                self._generate()
                self.overlay_timer = 2.0
            self.idle_timer = 0.0
            self.auto_demo = False
            consumed = True

        # Up/Down: toggle model
        if input_state.up_pressed or input_state.down_pressed:
            self.model = 1 - self.model
            self._generate()
            self.overlay_timer = 2.5
            self.idle_timer = 0.0
            self.auto_demo = False
            consumed = True

        return consumed

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    def update(self, dt: float):
        self.time += dt

        # Overlay timer
        if self.overlay_timer > 0:
            self.overlay_timer -= dt

        # Signal propagation
        if self.signal_active:
            self.signal_hop_timer += dt
            if self.signal_hop_timer >= SIGNAL_HOP_TIME:
                self.signal_hop_timer -= SIGNAL_HOP_TIME
                has_more = self._advance_signal()
                if not has_more:
                    # Signal finished -- keep displaying hops for a while
                    self.signal_active = False

        # Auto-demo after idle
        if not self.auto_demo:
            if not self.signal_active:
                self.idle_timer += dt
            if self.idle_timer >= 8.0:
                self.auto_demo = True
                self.auto_timer = 0.0
                self.auto_phase = 0
                # Reset to regular lattice
                self.rewire_p = 0.00
                self.model = 0
                self._generate()
                self._start_signal()
                self.overlay_timer = 2.0
        else:
            self._update_auto_demo(dt)

    def _update_auto_demo(self, dt):
        """Auto-demo: show regular lattice signal, then small-world signal."""
        if self.signal_active:
            return  # wait for signal to finish

        self.auto_timer += dt

        if self.auto_phase == 0:
            # Just finished regular lattice signal -- pause to show hops
            if self.auto_timer >= 2.5:
                self.auto_phase = 1
                self.auto_timer = 0.0
                # Switch to small-world
                self.rewire_p = 0.10
                self._generate()
                self.overlay_timer = 2.0
        elif self.auto_phase == 1:
            # Pause before firing small-world signal
            if self.auto_timer >= 1.0:
                self.auto_phase = 2
                self.auto_timer = 0.0
                self._start_signal()
        elif self.auto_phase == 2:
            # Just finished small-world signal -- pause to show hops
            if self.auto_timer >= 3.0:
                self.auto_phase = 3
                self.auto_timer = 0.0
                # Switch to BA model
                self.model = 1
                self.rewire_p = 0.00
                self._generate()
                self.overlay_timer = 2.0
        elif self.auto_phase == 3:
            if self.auto_timer >= 1.0:
                self.auto_phase = 4
                self.auto_timer = 0.0
                self._start_signal()
        elif self.auto_phase == 4:
            # BA signal done -- loop back to lattice
            if self.auto_timer >= 3.0:
                self.auto_phase = 0
                self.auto_timer = 0.0
                self.model = 0
                self.rewire_p = 0.00
                self._generate()
                self._start_signal()
                self.overlay_timer = 2.0

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------
    def _node_color(self, i):
        """Compute color for node i based on signal state."""
        activated_time = self.signal_activated[i]
        hop = self.signal_time[i]

        if hop is not None and activated_time > 0:
            elapsed = self.time - activated_time
            if elapsed < 0.15:
                # Flash bright white
                return COLOR_SIGNAL_ACTIVE
            elif elapsed < SIGNAL_FADE_TIME:
                # Fade: white -> yellow -> orange -> red -> idle
                t = elapsed / SIGNAL_FADE_TIME
                if t < 0.25:
                    # white to yellow
                    f = t / 0.25
                    return _lerp_color(COLOR_SIGNAL_ACTIVE, COLOR_SIGNAL_YELLOW, f)
                elif t < 0.5:
                    f = (t - 0.25) / 0.25
                    return _lerp_color(COLOR_SIGNAL_YELLOW, COLOR_SIGNAL_ORANGE, f)
                elif t < 0.75:
                    f = (t - 0.5) / 0.25
                    return _lerp_color(COLOR_SIGNAL_ORANGE, COLOR_SIGNAL_RED, f)
                else:
                    f = (t - 0.75) / 0.25
                    return _lerp_color(COLOR_SIGNAL_RED, COLOR_NODE_IDLE, f)

        # Idle: gentle pulse
        pulse = 0.7 + 0.3 * math.sin(self.time * IDLE_PULSE_SPEED + i * 0.15)
        return (int(COLOR_NODE_IDLE[0] * pulse),
                int(COLOR_NODE_IDLE[1] * pulse),
                int(COLOR_NODE_IDLE[2] * pulse))

    def _node_size(self, i):
        """Node render size. Hubs in BA model get larger."""
        if self.model == 1:
            deg = len(self.adj[i])
            if deg >= 8:
                return 3
        # Signal active nodes get a brief size boost
        if self.signal_time[i] is not None and self.signal_activated[i] > 0:
            elapsed = self.time - self.signal_activated[i]
            if elapsed < 0.2:
                return 3
        return 2

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------
    def draw(self):
        d = self.display
        d.clear(COLOR_BG)

        # Draw edges
        for (i, j) in self.edges:
            key = (min(i, j), max(i, j))
            if key in self.edge_is_shortcut:
                ec = COLOR_EDGE_SHORTCUT
            else:
                ec = COLOR_EDGE_NORMAL

            # If both endpoints are signal-active, brighten the edge
            if (self.signal_time[i] is not None and self.signal_time[j] is not None
                    and self.signal_activated[i] > 0 and self.signal_activated[j] > 0):
                ei = self.time - self.signal_activated[i]
                ej = self.time - self.signal_activated[j]
                if ei < SIGNAL_FADE_TIME and ej < SIGNAL_FADE_TIME:
                    bright = max(0.0, 1.0 - max(ei, ej) / SIGNAL_FADE_TIME)
                    ec = (int(ec[0] + (120 - ec[0]) * bright),
                          int(ec[1] + (140 - ec[1]) * bright),
                          int(ec[2] + (80 - ec[2]) * bright))

            x0 = int(round(self.node_x[i]))
            y0 = int(round(self.node_y[i]))
            x1 = int(round(self.node_x[j]))
            y1 = int(round(self.node_y[j]))
            d.draw_line(x0, y0, x1, y1, ec)

        # Draw nodes (on top of edges)
        for i in range(NUM_NODES):
            color = self._node_color(i)
            size = self._node_size(i)
            cx = int(round(self.node_x[i]))
            cy = int(round(self.node_y[i]))

            if size == 3:
                # 3x3 block centered
                for dy in range(-1, 2):
                    for dx in range(-1, 2):
                        px, py = cx + dx, cy + dy
                        if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                            # Slightly dim corners
                            if abs(dx) + abs(dy) == 2:
                                d.set_pixel(px, py, _dim(color, 0.6))
                            else:
                                d.set_pixel(px, py, color)
            else:
                # 2x2 block
                for dy in range(2):
                    for dx in range(2):
                        px, py = cx + dx, cy + dy
                        if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                            d.set_pixel(px, py, color)

        # --- HUD ---
        # Bottom stats
        p_str = f"p={self.rewire_p:.2f}"
        d.draw_text_small(2, 57, p_str, (160, 160, 120))

        if self.hops_display:
            # Show hops on right side
            d.draw_text_small(34, 57, self.hops_display, (255, 255, 180))

        # Overlay (model name, parameter changes)
        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)

            def fade(c):
                return (int(c[0] * alpha), int(c[1] * alpha), int(c[2] * alpha))

            if self.model == 0:
                label = "WATTS-STROGATZ"
            else:
                label = "BARABASI-ALBERT"
            d.draw_text_small(2, 2, label, fade((200, 200, 255)))

            # Show regime description
            if self.model == 0:
                if self.rewire_p < 0.02:
                    desc = "REGULAR LATTICE"
                    desc_color = (180, 180, 180)
                elif self.rewire_p <= 0.15:
                    desc = "SMALL WORLD"
                    desc_color = (100, 255, 140)
                else:
                    desc = "RANDOM GRAPH"
                    desc_color = (255, 180, 100)
                d.draw_text_small(2, 9, desc, fade(desc_color))
            else:
                d.draw_text_small(2, 9, "SCALE-FREE", fade((255, 180, 100)))


# ------------------------------------------------------------------
# Utility functions
# ------------------------------------------------------------------
def _lerp_color(c1, c2, t):
    """Linearly interpolate between two colors."""
    t = max(0.0, min(1.0, t))
    return (int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t))


def _dim(color, factor):
    """Dim a color by a factor."""
    return (int(color[0] * factor), int(color[1] * factor), int(color[2] * factor))
