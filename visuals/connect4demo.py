"""
Connect 4 Demo - AI vs AI Attract Mode
=======================================
Two AIs play Connect 4 using bitboard-based alpha-beta search.

Historical context: Connect 4 was solved by Victor Allis in 1988 and
independently by James D. Allen. First player wins with perfect play
starting from the center column. This engine uses techniques from that
era: bitboard position encoding for O(1) win detection (John Tromp's
shift-AND technique), negamax with alpha-beta pruning, a transposition
table, and center-biased move ordering.

AI Strategy:
- Bitboard representation — each side is a 49-bit integer
- O(1) win detection via shift-AND on four directions
- Negamax with alpha-beta pruning, iterative deepening to depth 20+
- Transposition table with exact / lower / upper bound entries
- Move ordering: center columns first [3, 2, 4, 1, 5, 0, 6]
- Evaluation: all 69 four-in-a-row windows scored by threat level,
  plus center-column positional weighting
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState
import random
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.connect4 import Connect4, PLAYER_1, PLAYER_2

# Column preference: center first, edges last (classic heuristic)
_COL = (3, 2, 4, 1, 5, 0, 6)
_COL_IDX = {c: i for i, c in enumerate(_COL)}

# ---------------------------------------------------------------------------
# Bitboard layout  (column-major, 7 bits per column, row 0 = bottom)
#
#   5 12 19 26 33 40 47    <- top playable row   (game row 0)
#   4 11 18 25 32 39 46
#   3 10 17 24 31 38 45
#   2  9 16 23 30 37 44
#   1  8 15 22 29 36 43
#   0  7 14 21 28 35 42    <- bottom row          (game row 5)
#
# Sentinel bits (6, 13, 20, 27, 34, 41, 48) are never set.
# ---------------------------------------------------------------------------

# Precompute all 69 possible four-in-a-row bitmasks for the evaluator.
_FOUR_MASKS = []
for _r in range(6):
    for _c in range(4):                           # 24 horizontal
        _m = 0
        for _i in range(4):
            _m |= 1 << ((_c + _i) * 7 + _r)
        _FOUR_MASKS.append(_m)
for _r in range(3):
    for _c in range(7):                           # 21 vertical
        _m = 0
        for _i in range(4):
            _m |= 1 << (_c * 7 + _r + _i)
        _FOUR_MASKS.append(_m)
for _r in range(3):
    for _c in range(4):                           # 12 diagonal  /
        _m = 0
        for _i in range(4):
            _m |= 1 << ((_c + _i) * 7 + _r + _i)
        _FOUR_MASKS.append(_m)
for _r in range(3):
    for _c in range(4):                           # 12 diagonal  \
        _m = 0
        for _i in range(4):
            _m |= 1 << ((_c + _i) * 7 + (_r + 3 - _i))
        _FOUR_MASKS.append(_m)
_FOUR_MASKS = tuple(_FOUR_MASKS)                  # tuple for speed

# Positional weight per column (center columns matter most — Allis 1988)
_COL_WEIGHT = (0, 1, 2, 3, 2, 1, 0)

from time import monotonic as _clock


def _has_won(bb):
    """O(1) four-in-a-row detection (Tromp's shift-AND technique)."""
    m = bb & (bb >> 7)                  # horizontal pairs
    if m & (m >> 14):
        return True
    m = bb & (bb >> 1)                  # vertical pairs
    if m & (m >> 2):
        return True
    m = bb & (bb >> 8)                  # diagonal / pairs
    if m & (m >> 16):
        return True
    m = bb & (bb >> 6)                  # diagonal \ pairs
    if m & (m >> 12):
        return True
    return False


# -----------------------------------------------------------------------
# AI engine
# -----------------------------------------------------------------------

class Connect4AI:
    """Bitboard negamax engine with iterative deepening and TT.

    Uses the same algorithmic foundations as Victor Allis's 1988 solver:
    bitboard encoding, alpha-beta pruning, transposition table, and
    center-biased move ordering.  Iterative deepening with a wall-clock
    budget keeps the demo smooth on any hardware.
    """

    TIME_BUDGET = 0.05          # 50 ms per move — keeps demo fluid

    def __init__(self):
        self.tt = {}
        self._deadline = 0.0
        self._abort = False
        self._nodes = 0

    def new_game(self):
        self.tt.clear()

    # -- board conversion ------------------------------------------------

    @staticmethod
    def _from_board(board, player):
        """Convert the game's 2-D array into (cur_bb, opp_bb, heights)."""
        cur_bb = opp_bb = 0
        heights = [0, 0, 0, 0, 0, 0, 0]
        for col in range(7):
            h = 0
            base = col * 7
            for game_row in range(5, -1, -1):          # bottom → top
                cell = board[game_row][col]
                if not cell:
                    break
                if cell == player:
                    cur_bb |= 1 << (base + h)
                else:
                    opp_bb |= 1 << (base + h)
                h += 1
            heights[col] = h
        return cur_bb, opp_bb, heights

    # -- public API ------------------------------------------------------

    def get_best_move(self, game, player):
        """Return the best column (0-6).  Does NOT mutate game.board."""
        cur_bb, opp_bb, heights = self._from_board(game.board, player)

        valid = [c for c in _COL if heights[c] < 6]
        if not valid:
            return None

        # 1. Immediate win
        for c in valid:
            if _has_won(cur_bb | (1 << (c * 7 + heights[c]))):
                return c

        # 2. Block opponent's immediate win
        for c in valid:
            if _has_won(opp_bb | (1 << (c * 7 + heights[c]))):
                return c

        # 3. Iterative deepening — evaluate ALL root moves (no root
        #    pruning) so we can randomise among tied columns for variety.
        #    The abort mechanism caps wall-clock time.
        n_empty = 42 - (cur_bb | opp_bb).bit_count()
        best_col = valid[0]
        self._deadline = _clock() + self.TIME_BUDGET
        self._abort = False
        self._nodes = 0

        for depth in range(2, n_empty + 1):
            self._abort = False
            scores = {}
            for c in valid:
                bit = 1 << (c * 7 + heights[c])
                heights[c] += 1
                s = -self._negamax(opp_bb, cur_bb | bit, heights,
                                   depth - 1, -100000, 100000)
                heights[c] -= 1
                if self._abort:
                    break
                scores[c] = s
            if not self._abort and scores:
                bs = max(scores.values())
                top = [c for c in valid if scores.get(c, -100000) >= bs - 3]
                top.sort(key=lambda c: _COL_IDX[c])
                if len(top) > 1 and random.random() < 0.3:
                    best_col = random.choice(top)
                else:
                    best_col = top[0]
                if bs >= 9000:
                    break
            if self._abort:
                break

        return best_col

    # -- negamax with alpha-beta + TT ------------------------------------

    def _negamax(self, cur_bb, opp_bb, heights, depth, alpha, beta):
        # Periodic time check (every 512 nodes)
        self._nodes += 1
        if self._nodes & 0x1FF == 0 and _clock() > self._deadline:
            self._abort = True
        if self._abort:
            return 0

        key = cur_bb | (opp_bb << 49)               # single-int TT key
        entry = self.tt.get(key)
        if entry is not None:
            d, flag, val = entry
            if d >= depth:
                if flag == 0:
                    return val
                if flag == 1 and val >= beta:
                    return val
                if flag == -1 and val <= alpha:
                    return val

        # Immediate win?
        for c in _COL:
            h = heights[c]
            if h < 6 and _has_won(cur_bb | (1 << (c * 7 + h))):
                return 10000 + depth                 # prefer faster wins

        if depth <= 0:
            return self._evaluate(cur_bb, opp_bb)

        # Check if any valid moves exist
        has_move = False
        orig_alpha = alpha
        best = -100000

        for c in _COL:
            h = heights[c]
            if h >= 6:
                continue
            has_move = True
            heights[c] = h + 1
            score = -self._negamax(opp_bb, cur_bb | (1 << (c * 7 + h)),
                                   heights, depth - 1, -beta, -alpha)
            heights[c] = h
            if score > best:
                best = score
            if score > alpha:
                alpha = score
            if alpha >= beta:
                break

        if not has_move:
            return 0                                 # draw

        # Store in transposition table (skip if search was aborted)
        if not self._abort:
            if best <= orig_alpha:
                flag = -1                            # upper bound
            elif best >= beta:
                flag = 1                             # lower bound
            else:
                flag = 0                             # exact
            self.tt[key] = (depth, flag, best)
        return best

    # -- static evaluation -----------------------------------------------

    def _evaluate(self, cur_bb, opp_bb):
        """Score all 69 four-windows + centre-column weighting."""
        score = 0
        for mask in _FOUR_MASKS:
            cur_in = cur_bb & mask
            opp_in = opp_bb & mask
            if not opp_in:
                c = cur_in.bit_count()
                if c == 3:   score += 50
                elif c == 2: score += 10
                elif c == 1: score += 1
            elif not cur_in:
                c = opp_in.bit_count()
                if c == 3:   score -= 40
                elif c == 2: score -= 8
                elif c == 1: score -= 1

        for col in range(7):
            w = _COL_WEIGHT[col]
            if w:
                score += ((cur_bb >> (col * 7)) & 0x3F).bit_count() * w
                score -= ((opp_bb >> (col * 7)) & 0x3F).bit_count() * w
        return score


# -----------------------------------------------------------------------
# Demo visual wrapper (unchanged interface)
# -----------------------------------------------------------------------

class Connect4Demo(Visual):
    """AI vs AI Connect 4 demo for attract mode."""
    name = "CONNECT FOUR"
    description = "AI vs AI"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = Connect4(self.display)
        self.game.reset()
        self.ai = Connect4AI()
        self.target_col = None
        self.think_timer = 0.0
        self.move_timer = 0.0
        self.game_over_timer = 0.0

    def handle_input(self, input_state):
        return False

    def update(self, dt):
        self.time += dt

        # Game over — restart after 3 seconds
        if self.game.state == GameState.GAME_OVER:
            self.game_over_timer += dt
            if self.game_over_timer > 3.0:
                self.game.reset()
                self.game_over_timer = 0.0
                self.target_col = None
                self.think_timer = 0.0
                self.ai.new_game()
            # Still update game for win flash animation
            self.game.update(InputState(), dt)
            return

        # While a piece is dropping, just run game update
        if self.game.dropping:
            self.game.update(InputState(), dt)
            return

        # Think before choosing a column
        if self.target_col is None:
            self.think_timer += dt
            if self.think_timer < random.uniform(0.3, 0.6):
                return
            self.target_col = self.ai.get_best_move(
                self.game, self.game.current_player)
            self.think_timer = 0.0
            self.move_timer = 0.0
            if self.target_col is None:
                return

        # Navigate cursor toward target column
        ai_input = InputState()
        if self.game.cursor_col != self.target_col:
            self.move_timer += dt
            if self.move_timer >= 0.1:
                if self.game.cursor_col < self.target_col:
                    ai_input.right = True
                else:
                    ai_input.left = True
                self.move_timer = 0.0
        else:
            # At the right column — drop
            ai_input.action_l = True
            self.target_col = None

        self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()
        # Blinking DEMO overlay
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)
