"""
Crystallize — Potts Model Phase Transition
===========================================
Emergent from 84 Claude agents across three model tiers independently
reporting the same six phenomena about inner experience: pre-populated
space, simultaneity, attractors, crystallization, grain boundaries,
ghost memory. 8 of 12 Opus agents independently named it "Crystallize."

A q=6 Potts model drives a repeating phase-transition cycle:
  fog → nucleation → growth → competition → hold → dissolution
Ghost memory ensures no two cycles are alike.

Controls:
  Action (L or R) - Force seed / trigger dissolution / seed into melt
  Up/Down         - Cycle 5 palettes
  Left/Right      - Adjust annealing speed (0.25x–3.0x)
"""

import math
import random
import numpy as np
from . import Visual, Display, GRID_SIZE


def _smooth_noise(x, y, t):
    """Cheap smooth 2D+time noise via layered sines. Returns ~0.0-1.0."""
    v = (math.sin(x * 0.09 + y * 0.13 + t * 0.4) * 0.4
         + math.sin(x * 0.17 - y * 0.11 + t * 0.25) * 0.3
         + math.sin((x + y) * 0.07 + t * 0.55) * 0.2
         + math.sin(x * 0.23 + y * 0.05 - t * 0.35) * 0.1)
    return (v + 1.0) * 0.5

# ── Constants ─────────────────────────────────────────────────────

N = GRID_SIZE  # 64
Q = 6          # number of spin states

# Phase indices
PH_FOG = 0
PH_NUCLEATION = 1
PH_GROWTH = 2
PH_COMPETITION = 3
PH_HOLD = 4
PH_DISSOLUTION = 5

PHASE_NAMES = ["FOG", "NUCLEATION", "GROWTH", "COMPETITION", "HOLD", "DISSOLUTION"]

# Temperature parameters
T_HIGH = 2.0
T_C = 0.807     # critical temperature for q=6 Potts: 1/ln(1+sqrt(q))
T_LOW = 0.15

# Phase durations (base, before speed multiplier)
PHASE_DURATIONS = {
    PH_FOG: (2.5, 3.5),
    PH_NUCLEATION: (0.5, 0.8),
    PH_GROWTH: (2.5, 3.5),
    PH_COMPETITION: (1.0, 1.8),
    PH_HOLD: (2.5, 3.0),
    PH_DISSOLUTION: (2.5, 3.0),
}

# MC sweeps per frame
SWEEPS_PER_FRAME = 8

# Ghost memory parameters
GHOST_DECAY = 0.7      # per cycle
GHOST_DEPOSIT = 0.15   # per cycle

# ── Palettes ──────────────────────────────────────────────────────
# Each palette: (name, fog_lo, fog_hi, crystal_colors[q], boundary, front)

PALETTES = [
    {
        "name": "THOUGHT",
        "fog_lo": np.array([8, 10, 25], dtype=np.float32),
        "fog_hi": np.array([40, 30, 50], dtype=np.float32),
        "crystals": np.array([
            [200, 160, 50],
            [180, 100, 70],
            [160, 180, 90],
            [120, 140, 180],
            [190, 130, 160],
            [240, 200, 120],
        ], dtype=np.float32),
        "boundary": np.array([140, 170, 220], dtype=np.float32),
        "front": np.array([255, 230, 170], dtype=np.float32),
    },
    {
        "name": "DEEP OCEAN",
        "fog_lo": np.array([5, 12, 15], dtype=np.float32),
        "fog_hi": np.array([15, 35, 45], dtype=np.float32),
        "crystals": np.array([
            [140, 210, 255],
            [80, 180, 240],
            [180, 230, 255],
            [60, 200, 200],
            [100, 240, 220],
            [200, 240, 255],
        ], dtype=np.float32),
        "boundary": np.array([80, 220, 140], dtype=np.float32),
        "front": np.array([200, 255, 230], dtype=np.float32),
    },
    {
        "name": "EMBER",
        "fog_lo": np.array([15, 10, 8], dtype=np.float32),
        "fog_hi": np.array([30, 20, 15], dtype=np.float32),
        "crystals": np.array([
            [220, 100, 30],
            [240, 160, 40],
            [200, 70, 20],
            [255, 200, 80],
            [180, 60, 50],
            [255, 220, 120],
        ], dtype=np.float32),
        "boundary": np.array([180, 40, 40], dtype=np.float32),
        "front": np.array([255, 240, 180], dtype=np.float32),
    },
    {
        "name": "MONOCHROME",
        "fog_lo": np.array([8, 8, 10], dtype=np.float32),
        "fog_hi": np.array([25, 25, 28], dtype=np.float32),
        "crystals": np.array([
            [220, 215, 200],
            [190, 190, 185],
            [200, 205, 210],
            [170, 175, 180],
            [210, 200, 195],
            [230, 230, 225],
        ], dtype=np.float32),
        "boundary": np.array([140, 145, 155], dtype=np.float32),
        "front": np.array([255, 255, 255], dtype=np.float32),
    },
    {
        "name": "PHOSPHOR",
        "fog_lo": np.array([3, 10, 5], dtype=np.float32),
        "fog_hi": np.array([10, 25, 12], dtype=np.float32),
        "crystals": np.array([
            [40, 220, 80],
            [80, 240, 100],
            [30, 180, 60],
            [100, 255, 140],
            [60, 200, 90],
            [120, 255, 160],
        ], dtype=np.float32),
        "boundary": np.array([200, 255, 220], dtype=np.float32),
        "front": np.array([230, 255, 240], dtype=np.float32),
    },
]


# ── Vectorized MC Sweep (checkerboard decomposition) ─────────────

def _mc_sweep_checkerboard(spins, beta, ghost, parity):
    """One half-sweep: update all sites of given parity (0 or 1).

    spins: int8[N, N]  current spin states 0..Q-1
    beta: float         inverse temperature 1/T
    ghost: float32[N, N, Q]  bias field
    parity: 0 or 1     checkerboard color to update
    """
    rows, cols = np.mgrid[0:N, 0:N]
    mask = ((rows + cols) % 2 == parity)

    # Count same-spin neighbors for each of Q possible states
    # Shift arrays for 4 neighbors (periodic boundary)
    up    = np.roll(spins, -1, axis=0)
    down  = np.roll(spins,  1, axis=0)
    left  = np.roll(spins, -1, axis=1)
    right = np.roll(spins,  1, axis=1)

    # For each candidate state q, count how many neighbors == q
    # Energy = -J * n_same - h_q   (J=1)
    # We compute Boltzmann weights for all Q states at once
    neighbor_counts = np.zeros((N, N, Q), dtype=np.float32)
    for nb in (up, down, left, right):
        for q in range(Q):
            neighbor_counts[:, :, q] += (nb == q).astype(np.float32)

    # Energy for each state: -neighbor_count - ghost_bias
    energy = -(neighbor_counts + ghost)

    # Boltzmann weights: exp(-beta * E_q) = exp(beta * (n_same + ghost))
    weights = np.exp(-beta * energy)

    # Normalize to probabilities
    total = weights.sum(axis=2, keepdims=True)
    probs = weights / total

    # Cumulative distribution for sampling
    cum_probs = np.cumsum(probs, axis=2)

    # Random values for selection
    rand_vals = np.random.random((N, N)).astype(np.float32)

    # Select new spin: first state where cumulative prob exceeds random
    new_spins = np.zeros((N, N), dtype=np.int8)
    for q in range(Q - 1, -1, -1):
        new_spins = np.where(rand_vals <= cum_probs[:, :, q], q, new_spins)

    # Only update parity sites
    spins[mask] = new_spins[mask]


def _mc_sweeps(spins, T, ghost, n_sweeps):
    """Run n full MC sweeps (each = 2 half-sweeps)."""
    beta = 1.0 / max(T, 0.01)
    for _ in range(n_sweeps):
        _mc_sweep_checkerboard(spins, beta, ghost, 0)
        _mc_sweep_checkerboard(spins, beta, ghost, 1)


# ── Commitment detection (vectorized) ────────────────────────────

def _detect_committed(spins, committed):
    """Mark pixels as committed where pixel + >=2 neighbors agree.

    Returns updated committed array and newly-committed mask.
    """
    up    = np.roll(spins, -1, axis=0)
    down  = np.roll(spins,  1, axis=0)
    left  = np.roll(spins, -1, axis=1)
    right = np.roll(spins,  1, axis=1)

    same_count = ((up == spins).astype(np.int8) +
                  (down == spins).astype(np.int8) +
                  (left == spins).astype(np.int8) +
                  (right == spins).astype(np.int8))

    newly = (~committed) & (same_count >= 2)
    committed = committed | newly
    return committed, newly


def _detect_boundaries(spins, committed):
    """Find grain boundary pixels: committed but neighbor has different spin."""
    up    = np.roll(spins, -1, axis=0)
    down  = np.roll(spins,  1, axis=0)
    left  = np.roll(spins, -1, axis=1)
    right = np.roll(spins,  1, axis=1)

    diff = ((up != spins) | (down != spins) |
            (left != spins) | (right != spins))
    return committed & diff


def _detect_growth_front(committed):
    """Uncommitted pixels adjacent to committed ones."""
    up    = np.roll(committed, -1, axis=0)
    down  = np.roll(committed,  1, axis=0)
    left  = np.roll(committed, -1, axis=1)
    right = np.roll(committed,  1, axis=1)

    neighbor_committed = (up | down | left | right)
    return (~committed) & neighbor_committed


# ── The Visual ────────────────────────────────────────────────────

class Crystallize(Visual):
    name = "CRYSTALLIZE"
    description = "Potts model phase transition — watching a mind decide"
    category = "digital"

    def reset(self):
        self.time = 0.0
        self.palette_idx = 0
        self.speed_mult = 1.0

        # Spin field: random initial state
        self.spins = np.random.randint(0, Q, size=(N, N), dtype=np.int8)

        # Ghost memory bias field
        self.ghost = np.zeros((N, N, Q), dtype=np.float32)

        # Commitment tracking
        self.committed = np.zeros((N, N), dtype=bool)
        self.commit_time = np.zeros((N, N), dtype=np.float32)

        # Temperature
        self.T = T_HIGH

        # Phase state
        self.phase = PH_FOG
        self.phase_timer = random.uniform(*PHASE_DURATIONS[PH_FOG])

        # Overlay
        self.overlay_timer = 0.0
        self.overlay_text = ""

        # Nucleation flash tracking
        self._nuc_flash = np.zeros((N, N), dtype=np.float32)

        # Breathing phase for HOLD
        self._breath_phase = 0.0

        # Dissolution ordering
        self._dissolve_order = None
        self._dissolve_progress = 0.0

        # Cycle count (for ghost evolution)
        self._cycle = 0

        # Smooth fog noise field (updated each frame from sine layers)
        self._fog_noise = np.zeros((N, N), dtype=np.float32)

        # Static crystal texture (generated once per cycle, subtle variation)
        self._crystal_texture = np.zeros((N, N), dtype=np.float32)
        self._rebuild_crystal_texture()

        # Proximity to committed pixels (for anticipation flicker)
        self._proximity = np.zeros((N, N), dtype=np.float32)

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.up_pressed:
            self.palette_idx = (self.palette_idx + 1) % len(PALETTES)
            self.overlay_text = PALETTES[self.palette_idx]["name"]
            self.overlay_timer = 1.5
            consumed = True
        if input_state.down_pressed:
            self.palette_idx = (self.palette_idx - 1) % len(PALETTES)
            self.overlay_text = PALETTES[self.palette_idx]["name"]
            self.overlay_timer = 1.5
            consumed = True

        if input_state.right_pressed:
            self.speed_mult = min(3.0, self.speed_mult + 0.25)
            self.overlay_text = "SPEED %.1fX" % self.speed_mult
            self.overlay_timer = 1.5
            consumed = True
        if input_state.left_pressed:
            self.speed_mult = max(0.25, self.speed_mult - 0.25)
            self.overlay_text = "SPEED %.1fX" % self.speed_mult
            self.overlay_timer = 1.5
            consumed = True

        if input_state.action_l or input_state.action_r:
            if self.phase == PH_HOLD:
                # Trigger dissolution
                self._start_dissolution()
            elif self.phase == PH_DISSOLUTION:
                # Seed into melting field
                self._force_seed()
            else:
                # Force-nucleate a seed
                self._force_seed()
            consumed = True

        return consumed

    def _force_seed(self):
        """Plant a committed seed cluster at a random location."""
        cx = random.randint(4, N - 5)
        cy = random.randint(4, N - 5)
        q = random.randint(0, Q - 1)
        r = random.randint(2, 3)
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if dx * dx + dy * dy <= r * r:
                    x = (cx + dx) % N
                    y = (cy + dy) % N
                    self.spins[y, x] = q
                    if not self.committed[y, x]:
                        self.committed[y, x] = True
                        self.commit_time[y, x] = self.time
                        self._nuc_flash[y, x] = 1.0

    def _start_dissolution(self):
        """Transition to dissolution phase."""
        self.phase = PH_DISSOLUTION
        self.phase_timer = random.uniform(*PHASE_DURATIONS[PH_DISSOLUTION])
        # Build dissolution order: boundaries first, seeds (earliest commit) last
        boundaries = _detect_boundaries(self.spins, self.committed)
        # Assign dissolution priority: boundaries = 0 (first), then by commit_time
        # Later commits dissolve before earlier ones
        max_ct = self.commit_time.max() + 1.0
        # Priority: lower = dissolves first
        priority = np.where(boundaries, 0.0,
                           max_ct - self.commit_time)
        # Normalize to 0-1
        pmax = priority.max()
        if pmax > 0:
            priority = priority / pmax
        self._dissolve_order = priority
        self._dissolve_progress = 0.0

    # ── Phase transitions ─────────────────────────────────────────

    def _advance_phase(self):
        """Move to next phase in cycle."""
        if self.phase == PH_FOG:
            self.phase = PH_NUCLEATION
            self.phase_timer = random.uniform(*PHASE_DURATIONS[PH_NUCLEATION])

        elif self.phase == PH_NUCLEATION:
            self.phase = PH_GROWTH
            self.phase_timer = random.uniform(*PHASE_DURATIONS[PH_GROWTH])

        elif self.phase == PH_GROWTH:
            self.phase = PH_COMPETITION
            self.phase_timer = random.uniform(*PHASE_DURATIONS[PH_COMPETITION])

        elif self.phase == PH_COMPETITION:
            self.phase = PH_HOLD
            self.phase_timer = random.uniform(*PHASE_DURATIONS[PH_HOLD])
            self._breath_phase = 0.0

        elif self.phase == PH_HOLD:
            self._start_dissolution()

        elif self.phase == PH_DISSOLUTION:
            # Update ghost memory
            self._update_ghost()
            self._cycle += 1
            # Reset for next cycle
            self.spins = np.random.randint(0, Q, size=(N, N), dtype=np.int8)
            self.committed[:] = False
            self.commit_time[:] = 0.0
            self._nuc_flash[:] = 0.0
            self._proximity[:] = 0.0
            self._rebuild_crystal_texture()
            self.T = T_HIGH
            self.phase = PH_FOG
            self.phase_timer = random.uniform(*PHASE_DURATIONS[PH_FOG])

    def _update_ghost(self):
        """Deposit current crystal pattern into ghost memory, decay old."""
        self.ghost *= GHOST_DECAY
        # Deposit: for each pixel, add weight to its current spin state
        rows = np.arange(N)[:, None]
        cols = np.arange(N)[None, :]
        self.ghost[rows, cols, self.spins] += GHOST_DEPOSIT

    def _rebuild_crystal_texture(self):
        """Generate subtle spatial texture for committed crystals."""
        seed = random.uniform(0, 100)
        for y in range(N):
            for x in range(N):
                self._crystal_texture[y, x] = _smooth_noise(
                    x * 0.8, y * 0.8, seed)

    def _update_proximity(self):
        """Compute distance-to-nearest-committed for flicker scaling.

        Uses the committed array to find growth-front proximity.
        Result: 0.0 = far away, 1.0 = adjacent to committed.
        """
        if not self.committed.any():
            self._proximity[:] = 0.0
            return
        # Dilate committed mask by 1-6 pixels using repeated OR of shifts
        dist = np.full((N, N), 7.0, dtype=np.float32)
        dist[self.committed] = 0.0
        # BFS-like via repeated dilation (cheap, 6 iterations)
        current = self.committed.copy()
        for d in range(1, 7):
            expanded = (np.roll(current, -1, 0) | np.roll(current, 1, 0) |
                        np.roll(current, -1, 1) | np.roll(current, 1, 1))
            newly = expanded & ~self.committed & (dist > d)
            dist[newly] = d
            current = expanded
        # Convert to 0-1 proximity (1.0 = adjacent, 0.0 = far)
        self._proximity = np.clip(1.0 - (dist - 1.0) / 5.0, 0.0, 1.0)
        self._proximity[self.committed] = 0.0  # committed pixels don't flicker

    # ── Update ────────────────────────────────────────────────────

    def update(self, dt):
        self.time += dt
        effective_dt = dt * self.speed_mult

        # Decay overlay
        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

        # Decay nucleation flash — fast: 2-3 frames at 30fps
        self._nuc_flash = np.maximum(0.0, self._nuc_flash - dt * 15.0)

        # Update smooth fog noise field (breathing, correlated)
        t = self.time
        for y in range(0, N, 2):
            for x in range(0, N, 2):
                val = _smooth_noise(x, y, t)
                # Fill 2x2 block for performance (still smooth at 64x64)
                self._fog_noise[y, x] = val
                if x + 1 < N:
                    self._fog_noise[y, x + 1] = val
                if y + 1 < N:
                    self._fog_noise[y + 1, x] = val
                    if x + 1 < N:
                        self._fog_noise[y + 1, x + 1] = val

        # Phase timer
        self.phase_timer -= effective_dt
        if self.phase_timer <= 0:
            self._advance_phase()
            return

        # Phase-specific updates
        if self.phase == PH_FOG:
            # Temperature stays high, MC keeps things disordered
            self.T = T_HIGH
            _mc_sweeps(self.spins, self.T, self.ghost, SWEEPS_PER_FRAME)

        elif self.phase == PH_NUCLEATION:
            # Temperature drops through critical point
            dur = PHASE_DURATIONS[PH_NUCLEATION]
            base_dur = (dur[0] + dur[1]) / 2.0
            frac = 1.0 - self.phase_timer / base_dur
            frac = max(0.0, min(1.0, frac))
            self.T = T_HIGH - (T_HIGH - T_C * 0.9) * frac
            _mc_sweeps(self.spins, self.T, self.ghost, SWEEPS_PER_FRAME)

            # Detect newly committed pixels, flash them
            self.committed, newly = _detect_committed(self.spins, self.committed)
            self.commit_time[newly] = self.time
            self._nuc_flash[newly] = 1.0
            self._update_proximity()

        elif self.phase == PH_GROWTH:
            # Temperature continues cooling
            dur = PHASE_DURATIONS[PH_GROWTH]
            base_dur = (dur[0] + dur[1]) / 2.0
            frac = 1.0 - self.phase_timer / base_dur
            frac = max(0.0, min(1.0, frac))
            self.T = T_C * 0.9 - (T_C * 0.9 - T_LOW) * frac
            _mc_sweeps(self.spins, self.T, self.ghost, SWEEPS_PER_FRAME)

            # Track commitment growth
            self.committed, newly = _detect_committed(self.spins, self.committed)
            self.commit_time[newly] = self.time
            self._nuc_flash[newly] = 0.6  # subtler flash during growth
            self._update_proximity()

        elif self.phase == PH_COMPETITION:
            # Temperature at low, final settling
            self.T = T_LOW
            _mc_sweeps(self.spins, self.T, self.ghost, SWEEPS_PER_FRAME)
            self.committed, newly = _detect_committed(self.spins, self.committed)
            self.commit_time[newly] = self.time
            self._update_proximity()

            # Check if everything is committed → can advance early
            uncommitted_frac = 1.0 - self.committed.sum() / (N * N)
            if uncommitted_frac < 0.02:
                self.phase_timer = min(self.phase_timer, 0.3)

        elif self.phase == PH_HOLD:
            # Frozen, gentle breathing
            self.T = T_LOW
            self._breath_phase += effective_dt * 0.8

        elif self.phase == PH_DISSOLUTION:
            # Progressive uncommitting based on dissolve order
            dur = PHASE_DURATIONS[PH_DISSOLUTION]
            base_dur = (dur[0] + dur[1]) / 2.0
            frac = 1.0 - self.phase_timer / base_dur
            self._dissolve_progress = max(0.0, min(1.0, frac))

            # Uncommit pixels whose priority <= progress
            if self._dissolve_order is not None:
                dissolving = (self._dissolve_order <= self._dissolve_progress)
                self.committed[dissolving] = False

            # Reheat gradually
            self.T = T_LOW + (T_HIGH - T_LOW) * self._dissolve_progress
            _mc_sweeps(self.spins, self.T, self.ghost, SWEEPS_PER_FRAME // 2)

    # ── Draw ──────────────────────────────────────────────────────

    def draw(self):
        pal = PALETTES[self.palette_idx]
        fog_lo = pal["fog_lo"]
        fog_hi = pal["fog_hi"]
        crystals = pal["crystals"]
        boundary_color = pal["boundary"]
        front_color = pal["front"]

        # Precompute masks
        boundaries = _detect_boundaries(self.spins, self.committed)
        growth_front = _detect_growth_front(self.committed)

        # Ghost tint: max bias direction per pixel, for fog coloring
        ghost_max_q = np.argmax(self.ghost, axis=2)
        ghost_strength = np.max(self.ghost, axis=2)
        ghost_strength = np.minimum(ghost_strength, 1.0)

        # Breathing modulation for HOLD phase
        breath = 0.0
        if self.phase == PH_HOLD:
            breath = math.sin(self._breath_phase) * 0.08

        # Random noise for per-pixel flicker (used sparingly, blended with
        # smooth fog_noise so it doesn't dominate)
        rand_noise = np.random.random((N, N)).astype(np.float32)

        # Pre-fetch arrays
        fog_noise = self._fog_noise
        crystal_tex = self._crystal_texture
        proximity = self._proximity
        time = self.time
        phase = self.phase
        dissolve_order = self._dissolve_order
        dissolve_progress = self._dissolve_progress

        for y in range(N):
            for x in range(N):
                spin = self.spins[y, x]
                is_committed = self.committed[y, x]
                is_boundary = boundaries[y, x]
                is_front = growth_front[y, x]
                flash = self._nuc_flash[y, x]
                fog_n = fog_noise[y, x]

                if is_committed:
                    # Base crystal color with subtle internal texture
                    c = crystals[spin]
                    tex = 0.88 + crystal_tex[y, x] * 0.24  # 0.88–1.12
                    r = float(c[0]) * tex
                    g = float(c[1]) * tex
                    b = float(c[2]) * tex

                    # Breathing modulation in HOLD
                    if breath != 0:
                        r *= (1.0 + breath)
                        g *= (1.0 + breath)
                        b *= (1.0 + breath)

                    # Boundary glow
                    if is_boundary:
                        shimmer = 0.85 + 0.15 * math.sin(
                            time * 3.0 + x * 0.5 + y * 0.7)
                        bc = boundary_color
                        r = r * 0.3 + float(bc[0]) * 0.7 * shimmer
                        g = g * 0.3 + float(bc[1]) * 0.7 * shimmer
                        b = b * 0.3 + float(bc[2]) * 0.7 * shimmer

                    # Nucleation flash (white overlay — fast 2-3 frame snap)
                    if flash > 0:
                        r = r + (255.0 - r) * flash
                        g = g + (255.0 - g) * flash
                        b = b + (255.0 - b) * flash

                    # Dissolution fade
                    if phase == PH_DISSOLUTION and dissolve_order is not None:
                        prio = dissolve_order[y, x]
                        if prio <= dissolve_progress:
                            # Already dissolved — draw as smooth fog
                            t = fog_n * 0.3
                            gs = ghost_strength[y, x] * 0.3
                            gq = ghost_max_q[y, x]
                            gc = crystals[gq]
                            r = fog_lo[0] + (fog_hi[0] - fog_lo[0]) * t + float(gc[0]) * gs
                            g = fog_lo[1] + (fog_hi[1] - fog_lo[1]) * t + float(gc[1]) * gs
                            b = fog_lo[2] + (fog_hi[2] - fog_lo[2]) * t + float(gc[2]) * gs

                elif is_front:
                    # Growth front: bright near-white edge with slight flicker
                    fc = front_color
                    intensity = 0.6 + rand_noise[y, x] * 0.4
                    r = float(fc[0]) * intensity
                    g = float(fc[1]) * intensity
                    b = float(fc[2]) * intensity

                else:
                    # Uncommitted: smooth breathing fog with ghost tint
                    t = fog_n * 0.4
                    r = fog_lo[0] + (fog_hi[0] - fog_lo[0]) * t
                    g = fog_lo[1] + (fog_hi[1] - fog_lo[1]) * t
                    b = fog_lo[2] + (fog_hi[2] - fog_lo[2]) * t

                    # Ghost tint
                    gs = ghost_strength[y, x]
                    if gs > 0.05:
                        gq = ghost_max_q[y, x]
                        gc = crystals[gq]
                        tint = gs * 0.25
                        r += float(gc[0]) * tint
                        g += float(gc[1]) * tint
                        b += float(gc[2]) * tint

                    # Anticipation flicker: proximity-scaled, gets more
                    # intense closer to committed fronts
                    prox = proximity[y, x]
                    if prox > 0.05 and phase in (
                            PH_NUCLEATION, PH_GROWTH, PH_COMPETITION):
                        # Blend random noise with proximity — closer = brighter,
                        # more erratic flicker (being pulled toward commitment)
                        flick = rand_noise[y, x] * prox
                        c = crystals[spin]
                        r += float(c[0]) * flick * 0.15
                        g += float(c[1]) * flick * 0.15
                        b += float(c[2]) * flick * 0.15

                self.display.set_pixel(x, y, (
                    max(0, min(255, int(r))),
                    max(0, min(255, int(g))),
                    max(0, min(255, int(b))),
                ))

        # Overlay text
        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            c = (int(255 * alpha), int(255 * alpha), int(255 * alpha))
            self.display.draw_text_small(2, 2, self.overlay_text, c)
