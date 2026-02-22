"""
Entropy - Shannon Entropy & Information Theory
================================================
TODO: RETHINK THIS VISUAL. The current implementation has 4 modes but 3 of
them (RLE, Huffman, Entropy grid) are chart/text-based and don't work well
on a 64x64 LED panel. Only the Parity mode reads clearly as a visual.
Consider: a single strong concept (e.g. entropy as disorder/order,
reversible vs irreversible mixing, Maxwell's demon) rather than 4 weak ones.

Current modes:
  1. ENTROPY  - Watch disorder grow on a grid of symbols
  2. RLE      - Run-length encoding compresses patterns
  3. HUFFMAN  - Frequency-based coding: short codes for common symbols
  4. PARITY   - Error detection and correction with parity bits

Controls:
  Left/Right  - Alphabet size (2-8 symbols)
  Up/Down     - Cycle demo mode
  Action      - Mode-specific reset/action
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE

# ---------------------------------------------------------------------------
# Symbol palette
# ---------------------------------------------------------------------------
SYMBOL_COLORS = [
    (60, 120, 255),   # blue
    (255, 80, 60),    # red
    (60, 220, 80),    # green
    (255, 200, 40),   # yellow
    (200, 60, 255),   # purple
    (255, 140, 40),   # orange
    (40, 220, 220),   # cyan
    (220, 60, 160),   # pink
]

MODE_NAMES = ["ENTROPY", "RLE", "HUFFMAN", "PARITY"]
DIM_BG = (4, 4, 12)


def shannon_entropy(counts, total):
    """Compute Shannon entropy H = -sum(p_i * log2(p_i))."""
    if total == 0:
        return 0.0
    h = 0.0
    for c in counts:
        if c > 0:
            p = c / total
            h -= p * math.log2(p)
    return h


# =========================================================================
# Mode 1 helpers: Entropy grid
# =========================================================================

ENTROPY_GRID_W = 56
ENTROPY_GRID_H = 50
ENTROPY_GRID_X0 = 4
ENTROPY_GRID_Y0 = 7


# =========================================================================
# Mode 2 helpers: RLE
# =========================================================================

def generate_rle_message(alphabet, length=56):
    """Generate a message with deliberate runs for good compression."""
    msg = []
    while len(msg) < length:
        sym = random.choice(range(alphabet))
        run = random.choice([1, 1, 2, 3, 3, 4, 5, 6, 8])
        run = min(run, length - len(msg))
        msg.extend([sym] * run)
    return msg[:length]


def rle_encode(msg):
    """Run-length encode: list of (symbol, count) pairs."""
    if not msg:
        return []
    runs = []
    cur_sym = msg[0]
    cur_count = 1
    for s in msg[1:]:
        if s == cur_sym:
            cur_count += 1
        else:
            runs.append((cur_sym, cur_count))
            cur_sym = s
            cur_count = 1
    runs.append((cur_sym, cur_count))
    return runs


# =========================================================================
# Mode 3 helpers: Huffman
# =========================================================================

class _HuffNode:
    __slots__ = ('sym', 'freq', 'left', 'right')

    def __init__(self, sym, freq, left=None, right=None):
        self.sym = sym
        self.freq = freq
        self.left = left
        self.right = right


def build_huffman_tree(freq_map):
    """Build a Huffman tree from {symbol: frequency}. Returns root node."""
    nodes = [_HuffNode(sym, f) for sym, f in freq_map.items() if f > 0]
    if len(nodes) == 0:
        return None
    if len(nodes) == 1:
        return _HuffNode(None, nodes[0].freq, nodes[0])
    # Sort-based (small alphabet, no need for heap)
    while len(nodes) > 1:
        nodes.sort(key=lambda n: n.freq)
        a, b = nodes.pop(0), nodes.pop(0)
        merged = _HuffNode(None, a.freq + b.freq, a, b)
        nodes.append(merged)
    return nodes[0]


def huffman_codes(root, prefix=""):
    """Extract code table from Huffman tree."""
    if root is None:
        return {}
    if root.sym is not None:
        return {root.sym: prefix or "0"}
    codes = {}
    codes.update(huffman_codes(root.left, prefix + "0"))
    codes.update(huffman_codes(root.right, prefix + "1"))
    return codes


def generate_huffman_message(alphabet, length=200):
    """Generate a message with skewed frequencies (Zipf-ish)."""
    weights = [1.0 / (i + 1) ** 1.2 for i in range(alphabet)]
    total = sum(weights)
    probs = [w / total for w in weights]
    msg = []
    for _ in range(length):
        r = random.random()
        cumul = 0.0
        for sym, p in enumerate(probs):
            cumul += p
            if r <= cumul:
                msg.append(sym)
                break
        else:
            msg.append(0)
    return msg


# =========================================================================
# Main Visual
# =========================================================================

class Entropy(Visual):
    name = "ENTROPY"
    description = "Information theory"
    category = "math"

    def __init__(self, display: Display):
        super().__init__(display)

    # -----------------------------------------------------------------
    # Reset / init
    # -----------------------------------------------------------------
    def reset(self):
        self.time = 0.0
        self.mode = 0  # 0=entropy, 1=rle, 2=huffman, 3=parity
        self.alphabet = 4

        # Overlay
        self.overlay_timer = 0.0
        self.overlay_text = ""

        # Init all modes
        self._reset_entropy()
        self._reset_rle()
        self._reset_huffman()
        self._reset_parity()

    def _show_overlay(self, text):
        self.overlay_text = text
        self.overlay_timer = 1.5

    # -----------------------------------------------------------------
    # Mode 0: ENTROPY
    # -----------------------------------------------------------------
    def _reset_entropy(self):
        """All cells = 0 (ordered), zero entropy."""
        self.e_grid = [[0] * ENTROPY_GRID_W for _ in range(ENTROPY_GRID_H)]
        self.e_timer = 0.0
        self.e_flips = 0
        self.e_step_interval = 0.02
        self.e_flips_per_step = 4  # flip several cells per tick for speed

    def _update_entropy(self, dt):
        self.e_timer += dt
        while self.e_timer >= self.e_step_interval:
            self.e_timer -= self.e_step_interval
            for _ in range(self.e_flips_per_step):
                x = random.randint(0, ENTROPY_GRID_W - 1)
                y = random.randint(0, ENTROPY_GRID_H - 1)
                self.e_grid[y][x] = random.randint(0, self.alphabet - 1)
                self.e_flips += 1

    def _draw_entropy(self):
        d = self.display

        # Draw symbol grid
        for y in range(ENTROPY_GRID_H):
            for x in range(ENTROPY_GRID_W):
                sym = self.e_grid[y][x]
                c = SYMBOL_COLORS[sym % len(SYMBOL_COLORS)]
                d.set_pixel(ENTROPY_GRID_X0 + x, ENTROPY_GRID_Y0 + y, c)

        # Compute current entropy
        counts = [0] * self.alphabet
        total = ENTROPY_GRID_W * ENTROPY_GRID_H
        for row in self.e_grid:
            for sym in row:
                counts[sym] += 1
        h = shannon_entropy(counts, total)
        h_max = math.log2(self.alphabet) if self.alphabet > 1 else 1.0

        # Entropy bar at bottom (y=59-62)
        bar_y = 59
        bar_x0 = 4
        bar_w = 56
        bar_h = 4

        # Background of bar
        for yy in range(bar_y, bar_y + bar_h):
            for xx in range(bar_x0, bar_x0 + bar_w):
                d.set_pixel(xx, yy, (20, 20, 30))

        # Fill proportional to H / H_max
        fill = h / h_max if h_max > 0 else 0.0
        fill_w = int(fill * bar_w)
        for yy in range(bar_y, bar_y + bar_h):
            for xx in range(bar_x0, bar_x0 + fill_w):
                # Gradient: blue (ordered) -> red (disordered)
                t = (xx - bar_x0) / max(1, bar_w - 1)
                r = int(40 + 215 * t)
                g = int(120 - 80 * t)
                b = int(255 - 200 * t)
                d.set_pixel(xx, yy, (r, g, b))

        # Max entropy target line
        target_x = bar_x0 + bar_w - 1
        for yy in range(bar_y, bar_y + bar_h):
            d.set_pixel(target_x, yy, (255, 255, 255))

        # HUD: entropy value
        h_str = f"H={h:.2f}/{h_max:.1f}"
        d.draw_text_small(2, 0, "ENTROPY", (200, 200, 200))
        d.draw_text_small(34, 0, f"K={self.alphabet}", (140, 180, 220))

    # -----------------------------------------------------------------
    # Mode 1: RLE
    # -----------------------------------------------------------------
    def _reset_rle(self):
        self.rle_msg = generate_rle_message(self.alphabet, 56)
        self.rle_encoded = rle_encode(self.rle_msg)
        self.rle_cursor = 0  # scanning position in original
        self.rle_emit = 0    # how many encoded tokens emitted
        self.rle_timer = 0.0
        self.rle_step_interval = 0.05
        self.rle_done = False
        self.rle_done_timer = 0.0

    def _update_rle(self, dt):
        self.rle_timer += dt
        if self.rle_done:
            self.rle_done_timer += dt
            if self.rle_done_timer > 4.0:
                self._reset_rle()
            return
        while self.rle_timer >= self.rle_step_interval:
            self.rle_timer -= self.rle_step_interval
            if self.rle_cursor < len(self.rle_msg):
                self.rle_cursor += 1
                # Check if cursor passed an encoded token boundary
                pos = 0
                emit = 0
                for sym, count in self.rle_encoded:
                    pos += count
                    emit += 1
                    if pos >= self.rle_cursor:
                        break
                self.rle_emit = min(emit, len(self.rle_encoded))
            else:
                self.rle_done = True
                self.rle_done_timer = 0.0

    def _draw_rle(self):
        d = self.display

        d.draw_text_small(2, 0, "RLE", (200, 200, 200))
        d.draw_text_small(20, 0, f"K={self.alphabet}", (140, 180, 220))

        msg = self.rle_msg
        encoded = self.rle_encoded

        # Original message: row at y=10..13 (4px tall cells)
        orig_y = 10
        cell_h = 4
        x0 = 4
        for i, sym in enumerate(msg):
            c = SYMBOL_COLORS[sym % len(SYMBOL_COLORS)]
            if i >= self.rle_cursor:
                # Not yet scanned: dim
                c = tuple(max(0, v // 4) for v in c)
            px = x0 + i
            if px < GRID_SIZE:
                for yy in range(orig_y, orig_y + cell_h):
                    d.set_pixel(px, yy, c)

        # Scanning cursor
        cx = x0 + min(self.rle_cursor, len(msg) - 1)
        if cx < GRID_SIZE:
            for yy in range(orig_y - 1, orig_y + cell_h + 1):
                if 0 <= yy < GRID_SIZE:
                    d.set_pixel(cx, yy, (255, 255, 255))

        # Label
        d.draw_text_small(2, 16, "ORIG", (120, 120, 120))
        orig_bits = len(msg) * max(1, math.ceil(math.log2(max(2, self.alphabet))))
        d.draw_text_small(28, 16, f"{orig_bits}b", (180, 180, 180))

        # Encoded tokens: row at y=26..33 (wider cells representing runs)
        enc_y = 26
        enc_h = 6
        ex = x0
        for i, (sym, count) in enumerate(encoded):
            if i >= self.rle_emit:
                break
            c = SYMBOL_COLORS[sym % len(SYMBOL_COLORS)]
            # Width = 1 pixel per token (compressed representation)
            # Show symbol color with a brightness boost proportional to count
            bright = min(1.5, 0.6 + count * 0.15)
            rc = min(255, int(c[0] * bright))
            gc = min(255, int(c[1] * bright))
            bc = min(255, int(c[2] * bright))
            # Each token gets 2 pixels wide to be visible
            for dx in range(2):
                if ex + dx < GRID_SIZE:
                    for yy in range(enc_y, enc_y + enc_h):
                        d.set_pixel(ex + dx, yy, (rc, gc, bc))
            # Small count indicator: top pixel brightness
            if ex < GRID_SIZE and count > 1:
                cnt_bright = min(255, 80 + count * 25)
                d.set_pixel(ex, enc_y - 1, (cnt_bright, cnt_bright, cnt_bright))
            ex += 2

        d.draw_text_small(2, 34, "COMP", (120, 120, 120))
        # Compressed bits: each token = bits_per_sym + bits for count
        bits_sym = max(1, math.ceil(math.log2(max(2, self.alphabet))))
        bits_count = 3  # up to 8 run length
        comp_bits = self.rle_emit * (bits_sym + bits_count)
        d.draw_text_small(28, 34, f"{comp_bits}b", (180, 180, 180))

        # Compression ratio bar (y=42..48)
        if self.rle_done and orig_bits > 0:
            total_comp = len(encoded) * (bits_sym + bits_count)
            ratio = total_comp / orig_bits
            self._draw_ratio_bar(42, ratio)

            # Ratio text
            pct = int(ratio * 100)
            d.draw_text_small(2, 50, f"{pct}%", (60, 220, 80) if ratio < 0.8 else (255, 200, 40))

        # "DONE" flash
        if self.rle_done:
            alpha = min(1.0, self.rle_done_timer / 0.3)
            sc = int(200 * alpha)
            saved = orig_bits - len(encoded) * (bits_sym + bits_count)
            d.draw_text_small(2, 56, f"SAVED {max(0,saved)}b", (sc, sc, 0))

    def _draw_ratio_bar(self, y, ratio):
        """Draw a compression ratio bar: full width = original, filled = compressed."""
        d = self.display
        bar_x0 = 4
        bar_w = 56
        bar_h = 5
        # Background
        for yy in range(y, y + bar_h):
            for xx in range(bar_x0, bar_x0 + bar_w):
                d.set_pixel(xx, yy, (25, 25, 35))
        # Original size reference (full bar, dim)
        for yy in range(y, y + bar_h):
            for xx in range(bar_x0, bar_x0 + bar_w):
                d.set_pixel(xx, yy, (30, 30, 50))
        # Compressed size (filled, green)
        fill_w = max(1, int(min(1.0, ratio) * bar_w))
        for yy in range(y, y + bar_h):
            for xx in range(bar_x0, bar_x0 + fill_w):
                t = (xx - bar_x0) / max(1, bar_w - 1)
                g = int(100 + 155 * (1.0 - t))
                d.set_pixel(xx, yy, (30, g, 60))

    # -----------------------------------------------------------------
    # Mode 2: HUFFMAN
    # -----------------------------------------------------------------
    def _reset_huffman(self):
        self.huf_msg = generate_huffman_message(self.alphabet, 200)
        # Compute frequencies
        freq = {}
        for s in self.huf_msg:
            freq[s] = freq.get(s, 0) + 1
        self.huf_freq = freq
        self.huf_total = len(self.huf_msg)
        # Build tree and codes
        tree = build_huffman_tree(freq)
        self.huf_codes = huffman_codes(tree)
        # Sort symbols by frequency (descending)
        self.huf_sorted = sorted(freq.keys(), key=lambda s: -freq[s])
        # Animation state
        self.huf_phase = 0  # 0=show freq bars, 1=show codes, 2=compare bits
        self.huf_timer = 0.0
        self.huf_anim_step = 0
        self.huf_phase_time = 0.0

    def _update_huffman(self, dt):
        self.huf_timer += dt
        self.huf_phase_time += dt

        if self.huf_phase == 0:
            # Frequency bar phase: show for 3 seconds then advance
            if self.huf_phase_time > 3.0:
                self.huf_phase = 1
                self.huf_phase_time = 0.0
                self.huf_anim_step = 0
        elif self.huf_phase == 1:
            # Code reveal phase: reveal one code every 0.4s
            step = int(self.huf_phase_time / 0.4)
            self.huf_anim_step = min(step, len(self.huf_sorted))
            if self.huf_anim_step >= len(self.huf_sorted) and self.huf_phase_time > len(self.huf_sorted) * 0.4 + 1.5:
                self.huf_phase = 2
                self.huf_phase_time = 0.0
        elif self.huf_phase == 2:
            # Comparison phase: hold for 5s then restart
            if self.huf_phase_time > 5.0:
                self._reset_huffman()

    def _draw_huffman(self):
        d = self.display

        d.draw_text_small(2, 0, "HUFFMAN", (200, 200, 200))
        d.draw_text_small(40, 0, f"K={self.alphabet}", (140, 180, 220))

        sorted_syms = self.huf_sorted
        freq = self.huf_freq
        codes = self.huf_codes
        total = self.huf_total
        max_freq = max(freq.values()) if freq else 1

        if self.huf_phase == 0:
            # Phase 0: Frequency bar chart
            d.draw_text_small(2, 6, "FREQ", (120, 120, 120))
            bar_x0 = 14
            bar_max_w = 46
            y = 12
            for i, sym in enumerate(sorted_syms):
                if y + 5 > 62:
                    break
                c = SYMBOL_COLORS[sym % len(SYMBOL_COLORS)]
                f = freq[sym]
                bar_w = max(1, int(f / max_freq * bar_max_w))
                # Symbol indicator (2px square)
                for dy in range(4):
                    for dx in range(2):
                        d.set_pixel(bar_x0 - 4 + dx, y + dy, c)
                # Bar
                for yy in range(y, y + 4):
                    for xx in range(bar_x0, bar_x0 + bar_w):
                        # Slightly dimmer version of symbol color
                        d.set_pixel(xx, yy, (c[0] // 2, c[1] // 2, c[2] // 2))
                # Count text
                pct = int(100 * f / total)
                d.draw_text_small(bar_x0 + bar_w + 2, y, f"{pct}%", (100, 100, 100))
                y += 7

        elif self.huf_phase == 1:
            # Phase 1: Reveal Huffman codes
            d.draw_text_small(2, 6, "CODES", (120, 120, 120))
            y = 12
            for i, sym in enumerate(sorted_syms):
                if y + 5 > 58:
                    break
                c = SYMBOL_COLORS[sym % len(SYMBOL_COLORS)]
                revealed = i < self.huf_anim_step
                # Symbol indicator
                for dy in range(4):
                    for dx in range(2):
                        d.set_pixel(8 + dx, y + dy, c if revealed else (30, 30, 30))
                if revealed:
                    code = codes.get(sym, "?")
                    # Draw code as colored bits
                    bx = 14
                    for bit_ch in code:
                        if bx >= GRID_SIZE - 2:
                            break
                        if bit_ch == '1':
                            d.set_pixel(bx, y + 1, (255, 255, 200))
                            d.set_pixel(bx, y + 2, (255, 255, 200))
                        else:
                            d.set_pixel(bx, y + 1, (40, 40, 60))
                            d.set_pixel(bx, y + 2, (40, 40, 60))
                        bx += 2
                    # Code length
                    d.draw_text_small(bx + 2, y, f"{len(code)}b", (100, 100, 100))
                y += 7

        elif self.huf_phase == 2:
            # Phase 2: Compare original vs Huffman bits
            bits_per_sym = max(1, math.ceil(math.log2(max(2, self.alphabet))))
            orig_bits = total * bits_per_sym
            huf_bits = sum(len(codes.get(s, "0")) for s in self.huf_msg)

            d.draw_text_small(2, 8, "ORIGINAL", (180, 100, 100))
            d.draw_text_small(2, 14, f"{orig_bits} bits", (255, 100, 100))

            d.draw_text_small(2, 24, "HUFFMAN", (100, 180, 100))
            d.draw_text_small(2, 30, f"{huf_bits} bits", (100, 255, 100))

            # Visual comparison: two bars
            bar_y1 = 40
            bar_y2 = 48
            bar_x0 = 4
            bar_max_w = 56

            # Original bar (full width = orig_bits)
            for yy in range(bar_y1, bar_y1 + 5):
                for xx in range(bar_x0, bar_x0 + bar_max_w):
                    d.set_pixel(xx, yy, (120, 40, 40))

            # Huffman bar (proportional)
            huf_w = max(1, int(huf_bits / orig_bits * bar_max_w))
            for yy in range(bar_y2, bar_y2 + 5):
                for xx in range(bar_x0, bar_x0 + huf_w):
                    d.set_pixel(xx, yy, (40, 120, 40))

            # Savings
            if orig_bits > 0:
                saved_pct = int(100 * (1.0 - huf_bits / orig_bits))
                d.draw_text_small(2, 56, f"SAVE {saved_pct}%",
                                  (60, 220, 80) if saved_pct > 0 else (200, 200, 200))

    # -----------------------------------------------------------------
    # Mode 3: PARITY
    # -----------------------------------------------------------------
    def _reset_parity(self):
        """8x8 data bits + parity bits. Cycle: clean -> error -> detect -> correct."""
        self.par_data = [[random.randint(0, 1) for _ in range(8)] for _ in range(8)]
        self._par_compute_parities()
        self.par_phase = 0  # 0=clean, 1=inject, 2=detect, 3=correct, 4=hold
        self.par_timer = 0.0
        self.par_error_r = -1
        self.par_error_c = -1
        self.par_bad_row = -1
        self.par_bad_col = -1
        self.par_flash = 0.0

    def _par_compute_parities(self):
        """Compute row, column, and corner parity."""
        self.par_row_parity = [0] * 8
        self.par_col_parity = [0] * 8
        for r in range(8):
            s = 0
            for c in range(8):
                s ^= self.par_data[r][c]
            self.par_row_parity[r] = s
        for c in range(8):
            s = 0
            for r in range(8):
                s ^= self.par_data[r][c]
            self.par_col_parity[c] = s
        # Corner parity = parity of all bits
        self.par_corner = 0
        for r in range(8):
            for c in range(8):
                self.par_corner ^= self.par_data[r][c]

    def _update_parity(self, dt):
        self.par_timer += dt
        self.par_flash += dt * 6.0  # for blink effects

        if self.par_phase == 0:
            # Clean: show for 1.5s
            if self.par_timer > 1.5:
                self.par_phase = 1
                self.par_timer = 0.0
                # Inject error
                self.par_error_r = random.randint(0, 7)
                self.par_error_c = random.randint(0, 7)
                self.par_data[self.par_error_r][self.par_error_c] ^= 1

        elif self.par_phase == 1:
            # Error injected: show for 1s
            if self.par_timer > 1.0:
                self.par_phase = 2
                self.par_timer = 0.0
                # Detect: check parities to find error
                self.par_bad_row = -1
                self.par_bad_col = -1
                for r in range(8):
                    s = 0
                    for c in range(8):
                        s ^= self.par_data[r][c]
                    if s != self.par_row_parity[r]:
                        self.par_bad_row = r
                for c in range(8):
                    s = 0
                    for r in range(8):
                        s ^= self.par_data[r][c]
                    if s != self.par_col_parity[c]:
                        self.par_bad_col = c

        elif self.par_phase == 2:
            # Detection: highlight row/col for 1.5s
            if self.par_timer > 1.5:
                self.par_phase = 3
                self.par_timer = 0.0
                # Correct the error
                if self.par_bad_row >= 0 and self.par_bad_col >= 0:
                    self.par_data[self.par_bad_row][self.par_bad_col] ^= 1

        elif self.par_phase == 3:
            # Corrected: flash green for 1.5s
            if self.par_timer > 1.5:
                self.par_phase = 4
                self.par_timer = 0.0

        elif self.par_phase == 4:
            # Hold, then restart
            if self.par_timer > 1.0:
                self._reset_parity()

    def _draw_parity(self):
        d = self.display

        d.draw_text_small(2, 0, "PARITY", (200, 200, 200))

        # Draw 8x8 grid with parity indicators on edges
        gx0 = 4
        gy0 = 8
        cell_size = 5
        gap = 1

        phase_labels = ["CLEAN", "ERROR!", "DETECT", "FIXED!", ""]
        if self.par_phase < len(phase_labels):
            label = phase_labels[self.par_phase]
            lc = (200, 200, 200)
            if self.par_phase == 1:
                lc = (255, 60, 60)
            elif self.par_phase == 3:
                lc = (60, 255, 60)
            d.draw_text_small(36, 0, label, lc)

        for r in range(8):
            for c in range(8):
                bit = self.par_data[r][c]
                px = gx0 + c * (cell_size + gap)
                py = gy0 + r * (cell_size + gap)

                # Base color
                if bit == 1:
                    color = (60, 130, 255)
                else:
                    color = (20, 25, 40)

                # Highlights per phase
                is_error_cell = (r == self.par_error_r and c == self.par_error_c)

                if self.par_phase == 1 and is_error_cell:
                    # Blinking red for injected error
                    blink = int(math.sin(self.par_flash) * 0.5 + 0.5)
                    if blink:
                        color = (255, 40, 40)

                elif self.par_phase == 2:
                    # Highlight detected row and column
                    in_bad_row = (r == self.par_bad_row)
                    in_bad_col = (c == self.par_bad_col)
                    if in_bad_row and in_bad_col:
                        # Intersection: bright yellow blinking
                        blink = math.sin(self.par_flash) * 0.5 + 0.5
                        color = (int(255 * blink), int(220 * blink), 0)
                    elif in_bad_row:
                        # Row highlight: orange tint
                        color = (min(255, color[0] + 100), min(255, color[1] + 40), color[2])
                    elif in_bad_col:
                        # Column highlight: orange tint
                        color = (min(255, color[0] + 100), min(255, color[1] + 40), color[2])

                elif self.par_phase == 3 and is_error_cell:
                    # Corrected: green flash
                    blink = math.sin(self.par_flash) * 0.5 + 0.5
                    color = (0, int(255 * blink), int(60 * blink))

                # Draw cell
                for dy in range(cell_size):
                    for dx in range(cell_size):
                        if px + dx < GRID_SIZE and py + dy < GRID_SIZE:
                            d.set_pixel(px + dx, py + dy, color)

        # Draw parity bits along edges
        # Row parities: right side
        prx = gx0 + 8 * (cell_size + gap) + 1
        for r in range(8):
            py = gy0 + r * (cell_size + gap)
            p = self.par_row_parity[r]
            pc = (80, 200, 80) if p == 0 else (200, 80, 80)
            if self.par_phase == 2 and r == self.par_bad_row:
                blink = math.sin(self.par_flash) * 0.5 + 0.5
                pc = (int(255 * blink), int(100 * blink), 0)
            for dy in range(min(3, cell_size)):
                if prx < GRID_SIZE and py + dy < GRID_SIZE:
                    d.set_pixel(prx, py + dy, pc)

        # Column parities: bottom
        pcy = gy0 + 8 * (cell_size + gap) + 1
        for c in range(8):
            px = gx0 + c * (cell_size + gap)
            p = self.par_col_parity[c]
            pc = (80, 200, 80) if p == 0 else (200, 80, 80)
            if self.par_phase == 2 and c == self.par_bad_col:
                blink = math.sin(self.par_flash) * 0.5 + 0.5
                pc = (int(255 * blink), int(100 * blink), 0)
            for dx in range(min(3, cell_size)):
                if px + dx < GRID_SIZE and pcy < GRID_SIZE:
                    d.set_pixel(px + dx, pcy, pc)

    # -----------------------------------------------------------------
    # Input
    # -----------------------------------------------------------------
    def handle_input(self, input_state) -> bool:
        consumed = False

        # Up/Down: cycle mode
        if input_state.up_pressed:
            self.mode = (self.mode - 1) % len(MODE_NAMES)
            self._show_overlay(MODE_NAMES[self.mode])
            consumed = True
        elif input_state.down_pressed:
            self.mode = (self.mode + 1) % len(MODE_NAMES)
            self._show_overlay(MODE_NAMES[self.mode])
            consumed = True

        # Left/Right: alphabet size
        if input_state.left_pressed:
            self.alphabet = max(2, self.alphabet - 1)
            self._show_overlay(f"ALPHA={self.alphabet}")
            # Refresh modes that depend on alphabet
            self._reset_entropy()
            self._reset_rle()
            self._reset_huffman()
            consumed = True
        elif input_state.right_pressed:
            self.alphabet = min(8, self.alphabet + 1)
            self._show_overlay(f"ALPHA={self.alphabet}")
            self._reset_entropy()
            self._reset_rle()
            self._reset_huffman()
            consumed = True

        # Action: mode-specific reset
        if input_state.action_l or input_state.action_r:
            if self.mode == 0:
                self._reset_entropy()
                self._show_overlay("RESET")
            elif self.mode == 1:
                self._reset_rle()
                self._show_overlay("NEW MSG")
            elif self.mode == 2:
                self._reset_huffman()
                self._show_overlay("NEW MSG")
            elif self.mode == 3:
                self._reset_parity()
                self._show_overlay("RESET")
            consumed = True

        return consumed

    # -----------------------------------------------------------------
    # Update & Draw
    # -----------------------------------------------------------------
    def update(self, dt: float):
        self.time += dt

        if self.overlay_timer > 0:
            self.overlay_timer = max(0, self.overlay_timer - dt)

        if self.mode == 0:
            self._update_entropy(dt)
        elif self.mode == 1:
            self._update_rle(dt)
        elif self.mode == 2:
            self._update_huffman(dt)
        elif self.mode == 3:
            self._update_parity(dt)

    def draw(self):
        d = self.display
        d.clear(DIM_BG)

        if self.mode == 0:
            self._draw_entropy()
        elif self.mode == 1:
            self._draw_rle()
        elif self.mode == 2:
            self._draw_huffman()
        elif self.mode == 3:
            self._draw_parity()

        # Overlay
        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            oc = (int(220 * alpha), int(220 * alpha), int(220 * alpha))
            d.draw_text_small(2, 28, self.overlay_text, oc)
