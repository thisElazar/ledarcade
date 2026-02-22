"""
Sorting - Algorithm Visualization
====================================
64 bars sorted by classic algorithms. Watch bubble sort's O(n^2) struggle
vs merge sort's elegant O(n log n) divide-and-conquer.

Controls:
  Left/Right  - Adjust speed (steps per tick)
  Up/Down     - Cycle algorithm
  Action      - Reshuffle and restart
"""

import random
from . import Visual, Display, Colors, GRID_SIZE

# Bar drawing area: top of bars at y=4, bottom at y=58 (54 pixels of height)
BAR_TOP = 4
BAR_BOTTOM = 58
BAR_HEIGHT_MAX = BAR_BOTTOM - BAR_TOP  # 54 pixels
N = GRID_SIZE  # 64 bars

SPEED_MIN = 1
SPEED_MAX = 40
SPEED_DEFAULT = 4

ALGORITHMS = [
    ("BUBBLE", "bubble_sort"),
    ("SELECTION", "selection_sort"),
    ("INSERTION", "insertion_sort"),
    ("MERGE", "merge_sort"),
    ("QUICK", "quick_sort"),
    ("HEAP", "heap_sort"),
]


def bar_color(value, max_val=N):
    """Map value to rainbow: blue (short) -> cyan -> green -> yellow -> red (tall)."""
    t = value / max_val
    if t < 0.25:
        return (0, int(t * 4 * 255), 255)
    elif t < 0.5:
        return (0, 255, int((0.5 - t) * 4 * 255))
    elif t < 0.75:
        return (int((t - 0.5) * 4 * 255), 255, 0)
    else:
        return (255, int((1.0 - t) * 4 * 255), 0)


# ---------------------------------------------------------------------------
# Sorting algorithm generators
# Each yields tuples: ('compare', i, j), ('swap', i, j), ('done',)
# Some also yield ('pivot', i) or ('range', lo, hi) for visual hints.
# ---------------------------------------------------------------------------

def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        swapped = False
        for j in range(n - 1 - i):
            yield ('compare', j, j + 1)
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                yield ('swap', j, j + 1)
                swapped = True
        if not swapped:
            break
    yield ('done',)


def selection_sort(arr):
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            yield ('compare', min_idx, j)
            if arr[j] < arr[min_idx]:
                min_idx = j
        if min_idx != i:
            arr[i], arr[min_idx] = arr[min_idx], arr[i]
            yield ('swap', i, min_idx)
    yield ('done',)


def insertion_sort(arr):
    n = len(arr)
    for i in range(1, n):
        j = i
        while j > 0:
            yield ('compare', j - 1, j)
            if arr[j - 1] > arr[j]:
                arr[j - 1], arr[j] = arr[j], arr[j - 1]
                yield ('swap', j - 1, j)
                j -= 1
            else:
                break
    yield ('done',)


def merge_sort(arr):
    """In-place merge sort using auxiliary merge, yielding each step."""
    yield from _merge_sort_rec(arr, 0, len(arr) - 1)
    yield ('done',)


def _merge_sort_rec(arr, lo, hi):
    if lo >= hi:
        return
    mid = (lo + hi) // 2
    yield from _merge_sort_rec(arr, lo, mid)
    yield from _merge_sort_rec(arr, mid + 1, hi)
    yield from _merge(arr, lo, mid, hi)


def _merge(arr, lo, mid, hi):
    """Merge two sorted halves in-place using rotation (no extra array)."""
    yield ('range', lo, hi)
    left = lo
    right = mid + 1
    while left <= mid and right <= hi:
        yield ('compare', left, right)
        if arr[left] <= arr[right]:
            left += 1
        else:
            # Rotate arr[left..right-1] right by one to insert arr[right] at left
            val = arr[right]
            for k in range(right, left, -1):
                arr[k] = arr[k - 1]
                yield ('swap', k - 1, k)
            arr[left] = val
            left += 1
            mid += 1
            right += 1


def quick_sort(arr):
    yield from _quick_sort_rec(arr, 0, len(arr) - 1)
    yield ('done',)


def _quick_sort_rec(arr, lo, hi):
    if lo >= hi:
        return
    yield ('range', lo, hi)
    # Median-of-three pivot selection
    mid = (lo + hi) // 2
    if arr[lo] > arr[mid]:
        arr[lo], arr[mid] = arr[mid], arr[lo]
        yield ('swap', lo, mid)
    if arr[lo] > arr[hi]:
        arr[lo], arr[hi] = arr[hi], arr[lo]
        yield ('swap', lo, hi)
    if arr[mid] > arr[hi]:
        arr[mid], arr[hi] = arr[hi], arr[mid]
        yield ('swap', mid, hi)
    # Use mid as pivot, move to hi-1
    if hi - lo >= 2:
        arr[mid], arr[hi - 1] = arr[hi - 1], arr[mid]
        yield ('swap', mid, hi - 1)
        pivot_val = arr[hi - 1]
        pivot_pos = hi - 1
    else:
        pivot_val = arr[hi]
        pivot_pos = hi

    yield ('pivot', pivot_pos)

    # Partition
    i = lo
    j = pivot_pos - 1 if hi - lo >= 2 else lo - 1
    if hi - lo >= 2:
        i = lo
        j = pivot_pos
        # Lomuto partition
        store = lo
        for k in range(lo, pivot_pos):
            yield ('compare', k, pivot_pos)
            if arr[k] < pivot_val:
                if store != k:
                    arr[store], arr[k] = arr[k], arr[store]
                    yield ('swap', store, k)
                store += 1
        # Move pivot to its final position
        if store != pivot_pos:
            arr[store], arr[pivot_pos] = arr[pivot_pos], arr[store]
            yield ('swap', store, pivot_pos)
        yield ('pivot', store)

        yield from _quick_sort_rec(arr, lo, store - 1)
        yield from _quick_sort_rec(arr, store + 1, hi)
    # If hi - lo < 2, the three elements are already sorted by median-of-three


def heap_sort(arr):
    n = len(arr)

    # Build max heap
    for i in range(n // 2 - 1, -1, -1):
        yield from _sift_down(arr, i, n)

    # Extract elements
    for end in range(n - 1, 0, -1):
        arr[0], arr[end] = arr[end], arr[0]
        yield ('swap', 0, end)
        yield from _sift_down(arr, 0, end)

    yield ('done',)


def _sift_down(arr, start, end):
    root = start
    while True:
        child = 2 * root + 1
        if child >= end:
            break
        # Pick larger child
        if child + 1 < end:
            yield ('compare', child, child + 1)
            if arr[child] < arr[child + 1]:
                child += 1
        yield ('compare', root, child)
        if arr[root] < arr[child]:
            arr[root], arr[child] = arr[child], arr[root]
            yield ('swap', root, child)
            root = child
        else:
            break


class Sorting(Visual):
    name = "SORTING"
    description = "Algorithm races"
    category = "math"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.algo_index = 0
        self.speed = SPEED_DEFAULT  # steps per tick
        self.tick_interval = 1.0 / 60.0  # 60 ticks per second
        self.tick_timer = 0.0

        # Overlay
        self.overlay_timer = 0.0
        self.overlay_text = ""

        # Stats
        self.comparisons = 0
        self.swaps = 0

        # Highlight state
        self.compare_indices = set()
        self.swap_indices = {}    # index -> fade timer
        self.pivot_index = -1
        self.active_range = None  # (lo, hi) for merge/quick visual hint

        # Done state
        self.done = False
        self.done_timer = 0.0
        self.sorted_sweep = -1  # for green sweep animation when done

        # Build array and start
        self._shuffle_and_start()

    def _shuffle_and_start(self):
        """Shuffle the array and create a fresh generator."""
        self.arr = list(range(1, N + 1))
        random.shuffle(self.arr)
        self.comparisons = 0
        self.swaps = 0
        self.compare_indices = set()
        self.swap_indices = {}
        self.pivot_index = -1
        self.active_range = None
        self.done = False
        self.done_timer = 0.0
        self.sorted_sweep = -1

        algo_name, algo_func = ALGORITHMS[self.algo_index]
        self.gen = globals()[algo_func](self.arr)

    def _show_overlay(self, text):
        self.overlay_text = text
        self.overlay_timer = 1.5

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Action: reshuffle
        if input_state.action_l or input_state.action_r:
            self._shuffle_and_start()
            self._show_overlay(ALGORITHMS[self.algo_index][0])
            consumed = True

        # Up/Down: cycle algorithm
        if input_state.up_pressed:
            self.algo_index = (self.algo_index - 1) % len(ALGORITHMS)
            self._shuffle_and_start()
            self._show_overlay(ALGORITHMS[self.algo_index][0])
            consumed = True
        elif input_state.down_pressed:
            self.algo_index = (self.algo_index + 1) % len(ALGORITHMS)
            self._shuffle_and_start()
            self._show_overlay(ALGORITHMS[self.algo_index][0])
            consumed = True

        # Left/Right: speed
        if input_state.left_pressed:
            self.speed = max(SPEED_MIN, self.speed - 1 if self.speed <= 5 else self.speed - 5)
            self._show_overlay(f"SPD {self.speed}")
            consumed = True
        elif input_state.right_pressed:
            self.speed = min(SPEED_MAX, self.speed + 1 if self.speed < 5 else self.speed + 5)
            self._show_overlay(f"SPD {self.speed}")
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt

        # Overlay fade
        if self.overlay_timer > 0:
            self.overlay_timer = max(0, self.overlay_timer - dt)

        # Fade swap highlights
        faded = []
        for idx in list(self.swap_indices):
            self.swap_indices[idx] -= dt
            if self.swap_indices[idx] <= 0:
                faded.append(idx)
        for idx in faded:
            del self.swap_indices[idx]

        # Done state: sweep then auto-advance
        if self.done:
            self.done_timer += dt
            # Green sweep animation
            sweep_speed = 200.0  # pixels per second
            self.sorted_sweep = int(self.done_timer * sweep_speed)
            if self.done_timer > 2.5:
                # Auto-advance to next algorithm
                self.algo_index = (self.algo_index + 1) % len(ALGORITHMS)
                self._shuffle_and_start()
            return

        # Step the algorithm
        self.tick_timer += dt
        if self.tick_timer >= self.tick_interval:
            self.tick_timer -= self.tick_interval
            self.compare_indices = set()
            steps = self.speed
            for _ in range(steps):
                try:
                    event = next(self.gen)
                except StopIteration:
                    self.done = True
                    break
                if event[0] == 'compare':
                    self.comparisons += 1
                    self.compare_indices.add(event[1])
                    self.compare_indices.add(event[2])
                elif event[0] == 'swap':
                    self.swaps += 1
                    self.swap_indices[event[1]] = 0.15
                    self.swap_indices[event[2]] = 0.15
                elif event[0] == 'pivot':
                    self.pivot_index = event[1]
                elif event[0] == 'range':
                    self.active_range = (event[1], event[2])
                elif event[0] == 'done':
                    self.done = True
                    break

    def draw(self):
        d = self.display
        d.clear()

        # Background
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                d.set_pixel(x, y, (5, 5, 15))

        # Draw bars
        for x in range(N):
            val = self.arr[x]
            # Bar height proportional to value
            bar_h = max(1, int(val * BAR_HEIGHT_MAX / N))
            # Base color from value
            r, g, b = bar_color(val)

            # Determine highlight
            is_compare = x in self.compare_indices
            is_swap = x in self.swap_indices
            is_pivot = (x == self.pivot_index)
            in_range = (self.active_range is not None and
                        self.active_range[0] <= x <= self.active_range[1])

            # Done sweep: green flash
            if self.done and self.sorted_sweep >= 0 and x <= self.sorted_sweep:
                bright = 1.3
                r = min(255, int(r * 0.3 + 0 * 0.7))
                g = min(255, int(g * 0.3 + 255 * 0.7))
                b = min(255, int(b * 0.3 + 80 * 0.7))

            if is_compare:
                # White highlight for compared elements
                r = min(255, r + 160)
                g = min(255, g + 160)
                b = min(255, b + 160)
            elif is_swap:
                # Yellow flash for swapped elements
                fade = min(1.0, self.swap_indices[x] / 0.1)
                boost = int(120 * fade)
                r = min(255, r + boost)
                g = min(255, g + boost)
                b = max(0, b - int(60 * fade))
            elif is_pivot:
                # Green for pivot
                r = 40
                g = 255
                b = 40
            elif in_range and not self.done:
                # Subtle brightening for active range
                r = min(255, int(r * 1.15))
                g = min(255, int(g * 1.15))
                b = min(255, int(b * 1.15))

            # Draw the bar from bottom up
            for y in range(BAR_BOTTOM - bar_h, BAR_BOTTOM):
                d.set_pixel(x, y, (r, g, b))

        # --- HUD ---
        algo_name = ALGORITHMS[self.algo_index][0]

        # Algorithm name at top-left
        d.draw_text_small(2, 0, algo_name, (200, 200, 200))

        # Comparison and swap counts at bottom
        cmp_str = f"C:{self.comparisons}"
        swp_str = f"S:{self.swaps}"
        d.draw_text_small(2, 59, cmp_str, (140, 180, 220))
        d.draw_text_small(34, 59, swp_str, (220, 180, 140))

        # "SORTED!" message when done
        if self.done:
            alpha = min(1.0, self.done_timer / 0.3)
            sc = int(220 * alpha)
            d.draw_text_small(14, 28, "SORTED!", (sc, sc, 0))

        # Overlay (speed/algo changes)
        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            oc = (int(220 * alpha), int(220 * alpha), int(220 * alpha))
            # Center-ish overlay
            d.draw_text_small(2, 28, self.overlay_text, oc)
