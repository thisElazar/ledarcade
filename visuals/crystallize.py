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

# MC sweeps per physics frame
SWEEPS_PER_FRAME = 8

# Ghost memory parameters
GHOST_DECAY = 0.7      # per cycle
GHOST_DEPOSIT = 0.15   # per cycle

# Pre-built coordinate grids (used for vectorized noise + shimmer)
_YS, _XS = np.mgrid[0:N, 0:N]
_YS_F = _YS.astype(np.float32)
_XS_F = _XS.astype(np.float32)

# Checkerboard mask (precomputed)
_EVEN_MASK = ((_YS + _XS) % 2 == 0)
_ODD_MASK = ~_EVEN_MASK


# ── Palettes ──────────────────────────────────────────────────────

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


# ── Vectorized fog noise (numpy sin on grids) ────────────────────

def _fog_noise_vectorized(t):
    """Smooth breathing fog field via layered numpy sines. Returns [N,N] 0-1."""
    v = (np.sin(_XS_F * 0.09 + _YS_F * 0.13 + t * 0.4) * 0.4
         + np.sin(_XS_F * 0.17 - _YS_F * 0.11 + t * 0.25) * 0.3
         + np.sin((_XS_F + _YS_F) * 0.07 + t * 0.55) * 0.2
         + np.sin(_XS_F * 0.23 + _YS_F * 0.05 - t * 0.35) * 0.1)
    return (v + 1.0) * 0.5


def _crystal_texture_vectorized(seed):
    """Static spatial texture for crystal internals. Returns [N,N] 0-1."""
    xs = _XS_F * 0.8
    ys = _YS_F * 0.8
    v = (np.sin(xs * 0.09 + ys * 0.13 + seed * 0.4) * 0.4
         + np.sin(xs * 0.17 - ys * 0.11 + seed * 0.25) * 0.3
         + np.sin((xs + ys) * 0.07 + seed * 0.55) * 0.2
         + np.sin(xs * 0.23 + ys * 0.05 - seed * 0.35) * 0.1)
    return (v + 1.0) * 0.5


# ── Vectorized MC Sweep (checkerboard decomposition) ─────────────

def _mc_sweep_checkerboard(spins, beta, ghost, mask):
    """One half-sweep: update all sites matching mask."""
    up    = np.roll(spins, -1, axis=0)
    down  = np.roll(spins,  1, axis=0)
    left  = np.roll(spins, -1, axis=1)
    right = np.roll(spins,  1, axis=1)

    neighbor_counts = np.zeros((N, N, Q), dtype=np.float32)
    for nb in (up, down, left, right):
        for q in range(Q):
            neighbor_counts[:, :, q] += (nb == q).astype(np.float32)

    energy = -(neighbor_counts + ghost)
    weights = np.exp(-beta * energy)
    total = weights.sum(axis=2, keepdims=True)
    probs = weights / total
    cum_probs = np.cumsum(probs, axis=2)
    rand_vals = np.random.random((N, N)).astype(np.float32)

    new_spins = np.zeros((N, N), dtype=np.int8)
    for q in range(Q - 1, -1, -1):
        new_spins = np.where(rand_vals <= cum_probs[:, :, q], q, new_spins)

    spins[mask] = new_spins[mask]


def _mc_sweeps(spins, T, ghost, n_sweeps):
    """Run n full MC sweeps (each = 2 half-sweeps)."""
    beta = 1.0 / max(T, 0.01)
    for _ in range(n_sweeps):
        _mc_sweep_checkerboard(spins, beta, ghost, _EVEN_MASK)
        _mc_sweep_checkerboard(spins, beta, ghost, _ODD_MASK)


# ── Commitment detection (vectorized) ────────────────────────────

def _detect_committed(spins, committed):
    """Mark pixels as committed where pixel + >=2 neighbors agree."""
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
    return (~committed) & (up | down | left | right)


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

        # Cycle count
        self._cycle = 0

        # Crystal texture (generated once per cycle)
        self._crystal_texture = _crystal_texture_vectorized(
            random.uniform(0, 100))

        # Proximity to committed pixels (for anticipation flicker)
        self._proximity = np.zeros((N, N), dtype=np.float32)

        # Frame interpolation: pixel buffers
        self._pixels_prev = np.zeros((N, N, 3), dtype=np.float32)
        self._pixels_curr = np.zeros((N, N, 3), dtype=np.float32)
        self._pixels_display = np.zeros((N, N, 3), dtype=np.uint8)
        self._sim_frame = 0
        self._built_this_frame = False
        self._needs_full_rebuild = True

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.up_pressed:
            self.palette_idx = (self.palette_idx + 1) % len(PALETTES)
            self.overlay_text = PALETTES[self.palette_idx]["name"]
            self.overlay_timer = 1.5
            self._needs_full_rebuild = True
            consumed = True
        if input_state.down_pressed:
            self.palette_idx = (self.palette_idx - 1) % len(PALETTES)
            self.overlay_text = PALETTES[self.palette_idx]["name"]
            self.overlay_timer = 1.5
            self._needs_full_rebuild = True
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
                self._start_dissolution()
            else:
                self._force_seed()
            self._needs_full_rebuild = True
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
        boundaries = _detect_boundaries(self.spins, self.committed)
        max_ct = self.commit_time.max() + 1.0
        priority = np.where(boundaries, 0.0, max_ct - self.commit_time)
        pmax = priority.max()
        if pmax > 0:
            priority = priority / pmax
        self._dissolve_order = priority
        self._dissolve_progress = 0.0

    # ── Phase transitions ─────────────────────────────────────────

    def _advance_phase(self):
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
            self._update_ghost()
            self._cycle += 1
            self.spins = np.random.randint(0, Q, size=(N, N), dtype=np.int8)
            self.committed[:] = False
            self.commit_time[:] = 0.0
            self._nuc_flash[:] = 0.0
            self._proximity[:] = 0.0
            self._crystal_texture = _crystal_texture_vectorized(
                random.uniform(0, 100))
            self.T = T_HIGH
            self.phase = PH_FOG
            self.phase_timer = random.uniform(*PHASE_DURATIONS[PH_FOG])
        self._needs_full_rebuild = True

    def _update_ghost(self):
        self.ghost *= GHOST_DECAY
        rows = np.arange(N)[:, None]
        cols = np.arange(N)[None, :]
        self.ghost[rows, cols, self.spins] += GHOST_DEPOSIT

    def _update_proximity(self):
        """Distance-to-committed for anticipation flicker (vectorized dilation)."""
        if not self.committed.any():
            self._proximity[:] = 0.0
            return
        dist = np.full((N, N), 7.0, dtype=np.float32)
        dist[self.committed] = 0.0
        current = self.committed.copy()
        for d in range(1, 7):
            expanded = (np.roll(current, -1, 0) | np.roll(current, 1, 0) |
                        np.roll(current, -1, 1) | np.roll(current, 1, 1))
            newly = expanded & ~self.committed & (dist > d)
            dist[newly] = d
            current = expanded
        self._proximity = np.clip(1.0 - (dist - 1.0) / 5.0, 0.0, 1.0)
        self._proximity[self.committed] = 0.0

    # ── Update ────────────────────────────────────────────────────

    def update(self, dt):
        self.time += dt
        effective_dt = dt * self.speed_mult

        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

        # Flash decay (every frame — fast snap)
        self._nuc_flash = np.maximum(0.0, self._nuc_flash - dt * 15.0)

        # Phase timer
        self.phase_timer -= effective_dt
        if self.phase_timer <= 0:
            self._advance_phase()
            return

        # Physics: run every 2nd frame (odd frames interpolate)
        self._sim_frame += 1
        is_physics_frame = (self._sim_frame % 2 == 0) or self._needs_full_rebuild
        self._built_this_frame = is_physics_frame

        if is_physics_frame:
            self._run_physics(effective_dt)
            self._needs_full_rebuild = False

        # Breathing advances every frame (smooth)
        if self.phase == PH_HOLD:
            self._breath_phase += effective_dt * 0.8

    def _run_physics(self, effective_dt):
        """Full physics step: MC sweeps + commitment + proximity."""
        if self.phase == PH_FOG:
            self.T = T_HIGH
            _mc_sweeps(self.spins, self.T, self.ghost, SWEEPS_PER_FRAME)

        elif self.phase == PH_NUCLEATION:
            dur = PHASE_DURATIONS[PH_NUCLEATION]
            base_dur = (dur[0] + dur[1]) / 2.0
            frac = max(0.0, min(1.0, 1.0 - self.phase_timer / base_dur))
            self.T = T_HIGH - (T_HIGH - T_C * 0.9) * frac
            _mc_sweeps(self.spins, self.T, self.ghost, SWEEPS_PER_FRAME)
            self.committed, newly = _detect_committed(self.spins, self.committed)
            self.commit_time[newly] = self.time
            self._nuc_flash[newly] = 1.0
            self._update_proximity()

        elif self.phase == PH_GROWTH:
            dur = PHASE_DURATIONS[PH_GROWTH]
            base_dur = (dur[0] + dur[1]) / 2.0
            frac = max(0.0, min(1.0, 1.0 - self.phase_timer / base_dur))
            self.T = T_C * 0.9 - (T_C * 0.9 - T_LOW) * frac
            _mc_sweeps(self.spins, self.T, self.ghost, SWEEPS_PER_FRAME)
            self.committed, newly = _detect_committed(self.spins, self.committed)
            self.commit_time[newly] = self.time
            self._nuc_flash[newly] = 0.6
            self._update_proximity()

        elif self.phase == PH_COMPETITION:
            self.T = T_LOW
            _mc_sweeps(self.spins, self.T, self.ghost, SWEEPS_PER_FRAME)
            self.committed, newly = _detect_committed(self.spins, self.committed)
            self.commit_time[newly] = self.time
            self._update_proximity()
            if 1.0 - self.committed.sum() / (N * N) < 0.02:
                self.phase_timer = min(self.phase_timer, 0.3)

        elif self.phase == PH_HOLD:
            self.T = T_LOW

        elif self.phase == PH_DISSOLUTION:
            dur = PHASE_DURATIONS[PH_DISSOLUTION]
            base_dur = (dur[0] + dur[1]) / 2.0
            frac = 1.0 - self.phase_timer / base_dur
            self._dissolve_progress = max(0.0, min(1.0, frac))
            if self._dissolve_order is not None:
                self.committed[self._dissolve_order <= self._dissolve_progress] = False
            self.T = T_LOW + (T_HIGH - T_LOW) * self._dissolve_progress
            _mc_sweeps(self.spins, self.T, self.ghost, SWEEPS_PER_FRAME // 2)

    # ── Pixel buffer (fully vectorized) ───────────────────────────

    def _build_pixel_buffer(self):
        """Build full RGB[N,N,3] float buffer using numpy — no Python per-pixel."""
        pal = PALETTES[self.palette_idx]
        fog_lo = pal["fog_lo"]
        fog_hi = pal["fog_hi"]
        crystals = pal["crystals"]  # [Q, 3]
        boundary_color = pal["boundary"]
        front_color = pal["front"]

        # Masks
        boundaries = _detect_boundaries(self.spins, self.committed)
        growth_front = _detect_growth_front(self.committed)
        uncommitted = ~self.committed & ~growth_front

        # ── Fog layer (everywhere, overwritten later for committed/front) ──
        fog = _fog_noise_vectorized(self.time)
        fog_t = fog[:, :, np.newaxis] * 0.4  # [N,N,1]
        pixels = fog_lo + (fog_hi - fog_lo) * fog_t  # [N,N,3]

        # Ghost tint on uncommitted fog
        ghost_str = np.minimum(np.max(self.ghost, axis=2), 1.0)
        ghost_max_q = np.argmax(self.ghost, axis=2)
        ghost_colors = crystals[ghost_max_q]  # [N,N,3]
        ghost_mask = uncommitted & (ghost_str > 0.05)
        if ghost_mask.any():
            tint = (ghost_str * 0.25)[:, :, np.newaxis]
            pixels[ghost_mask] += (ghost_colors * tint)[ghost_mask]

        # Anticipation flicker on uncommitted pixels near fronts
        if self.phase in (PH_NUCLEATION, PH_GROWTH, PH_COMPETITION):
            prox = self._proximity
            flick_mask = uncommitted & (prox > 0.05)
            if flick_mask.any():
                rand_noise = np.random.random((N, N)).astype(np.float32)
                spin_colors = crystals[self.spins]  # [N,N,3]
                flick = (rand_noise * prox * 0.15)[:, :, np.newaxis]
                pixels[flick_mask] += (spin_colors * flick)[flick_mask]

        # ── Growth front layer ──
        if growth_front.any():
            rand_front = np.random.random((N, N)).astype(np.float32)
            intensity = (0.6 + rand_front * 0.4)[:, :, np.newaxis]
            pixels[growth_front] = (front_color * intensity)[growth_front]

        # ── Committed crystal layer ──
        if self.committed.any():
            crystal_colors = crystals[self.spins]  # [N,N,3]
            tex = (0.88 + self._crystal_texture * 0.24)[:, :, np.newaxis]
            crystal_px = crystal_colors * tex

            # Breathing in HOLD
            if self.phase == PH_HOLD:
                breath = 1.0 + math.sin(self._breath_phase) * 0.08
                crystal_px = crystal_px * breath

            # Boundary shimmer
            if boundaries.any():
                shimmer = (0.85 + 0.15 * np.sin(
                    self.time * 3.0 + _XS_F * 0.5 + _YS_F * 0.7))
                shimmer3 = shimmer[:, :, np.newaxis]
                boundary_px = crystal_px * 0.3 + boundary_color * 0.7 * shimmer3
                crystal_px[boundaries] = boundary_px[boundaries]

            # Nucleation flash (white snap)
            flash_mask = self._nuc_flash > 0
            if flash_mask.any():
                f = self._nuc_flash[:, :, np.newaxis]
                flashed = crystal_px + (255.0 - crystal_px) * f
                crystal_px[flash_mask] = flashed[flash_mask]

            # Write committed pixels
            pixels[self.committed] = crystal_px[self.committed]

        return pixels

    # ── Draw ──────────────────────────────────────────────────────

    def draw(self):
        # Build or interpolate pixel buffer
        if self._built_this_frame:
            # Full rebuild: swap buffers and compute new target
            self._pixels_prev[:] = self._pixels_curr
            self._pixels_curr[:] = self._build_pixel_buffer()
            self._pixels_display[:] = np.clip(
                self._pixels_curr, 0, 255).astype(np.uint8)
        else:
            # Cheap interp frame: lerp prev→curr (no fog recompute)
            np.clip((self._pixels_prev + self._pixels_curr) * 0.5,
                    0, 255, out=self._pixels_prev)  # reuse as scratch
            self._pixels_display[:] = self._pixels_prev.astype(np.uint8)
            self._pixels_prev[:] = self._pixels_curr  # restore for next interp

        # Render to display — the only Python loop (unavoidable)
        pixels = self._pixels_display
        display = self.display
        for y in range(N):
            row = pixels[y]
            for x in range(N):
                p = row[x]
                display.set_pixel(x, y, (int(p[0]), int(p[1]), int(p[2])))

        # Overlay text
        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            c = (int(255 * alpha), int(255 * alpha), int(255 * alpha))
            display.draw_text_small(2, 2, self.overlay_text, c)
