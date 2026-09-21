"""
Tests for three mid-word truncation bugs found in the legend audit:

1. games/rushhour.py: difficulty tier names were sliced with `diff.upper()[:6]`,
   turning 'beginner' into 'BEGINN' (the only tier that doesn't fit 6 chars).
2. visuals/idlemix.py: 9-char category display names were sliced to 8 chars,
   e.g. 'SCI MICRO' -> 'SCI MICR'.
3. visuals/effects.py: transition names were sliced to 10 chars for the list
   row, e.g. 'Dither Dissolve' -> 'Dither Dis'.

Each test also asserts everything stays within the 64px panel width.
"""

from tests._harness import get_sim_display
from games.rushhour import RushHour
from visuals.idlemix import IdleMix
from visuals.effects import Effects
from transitions import TRANSITION_TYPES


def _capture(display):
    """Wrap display.draw_text_small to record every (x, y, text, color) call."""
    drawn = []
    original = display.draw_text_small

    def capture_text(x, y, text, color):
        drawn.append((x, y, text, color))
        original(x, y, text, color)

    display.draw_text_small = capture_text
    return drawn


class TestRushHourDifficultyLabel:
    """BEGINNER must not be truncated to BEGINN on the level-select screen."""

    def test_beginner_shown_in_full_and_fits(self):
        display = get_sim_display()
        game = RushHour(display)
        game.reset()
        game.phase = 'select'
        game.difficulty_idx = 0  # 'beginner' is first in DIFFICULTY_ORDER
        assert game.DIFFICULTY_ORDER[0] == 'beginner'

        drawn = _capture(display)
        game.draw()

        # Old broken mid-word cut must be gone.
        bad = [t for t in drawn if t[2] == 'BEGINN']
        assert not bad, f"Found old truncated label: {bad}"

        # Full word must appear.
        full = [t for t in drawn if t[2] == 'BEGINNER']
        assert full, f"Full 'BEGINNER' label not found in: {[t[2] for t in drawn]}"

        # Stay within the 64px panel (3x5 font, 4px/char).
        for x, y, text, color in drawn:
            assert x + 4 * len(text) <= 64, f"'{text}' at x={x} overflows 64px"

    def test_all_difficulty_labels_are_full_words_and_fit(self):
        """Every tier (not just beginner) should render whole and unclipped."""
        display = get_sim_display()
        game = RushHour(display)
        game.reset()
        game.phase = 'select'

        for idx, diff in enumerate(game.DIFFICULTY_ORDER):
            game.difficulty_idx = idx
            drawn = _capture(display)
            game.draw()

            texts = [t[2] for t in drawn]
            assert diff.upper() in texts, (
                f"Full label for '{diff}' not found in drawn texts: {texts}"
            )
            # No strict mid-word prefix of the full word (i.e. a truncation).
            for t in texts:
                if t != diff.upper() and diff.upper().startswith(t) and t:
                    raise AssertionError(f"Mid-word cut of '{diff}' found: '{t}'")

            for x, y, text, color in drawn:
                assert x + 4 * len(text) <= 64, f"'{text}' at x={x} overflows 64px"


class TestIdleMixCategoryLabels:
    """9-char category names (SCI MICRO/BENCH/MACRO) must not be cut to 8."""

    def test_science_category_names_shown_in_full(self, sandbox):
        display = get_sim_display()
        visual = IdleMix(display)
        visual.reset()

        # Confirm the tricky 9-char categories are actually present.
        names = {c['key']: c['name'] for c in visual._categories}
        expected = {
            'science_micro': 'SCI MICRO',
            'science_bench': 'SCI BENCH',
            'science_macro': 'SCI MACRO',
        }
        for key, full_name in expected.items():
            assert names.get(key) == full_name, (
                f"Expected category '{key}' display name '{full_name}', got {names.get(key)}"
            )

        drawn = _capture(display)
        visual.draw()

        texts = [t[2] for t in drawn]

        # Old broken 8-char mid-word cuts must be gone.
        for bad in ('SCI MICR', 'SCI BENC', 'SCI MACR'):
            assert bad not in texts, f"Found old truncated label: {bad!r} in {texts}"

        # Full names must appear somewhere among the visible rows.
        for full_name in expected.values():
            if full_name not in texts:
                # Might be scrolled off-screen; scroll cursor down through the
                # whole category list and re-check.
                for _ in range(len(visual._categories)):
                    visual.cat_cursor = min(visual.cat_cursor + 1, len(visual._categories) - 1)
                    if visual.cat_cursor >= visual.cat_scroll + 6:
                        visual.cat_scroll = visual.cat_cursor - 6 + 1
                    drawn2 = _capture(display)
                    visual.draw()
                    texts.extend(t[2] for t in drawn2)
                break
        for full_name in expected.values():
            assert full_name in texts, f"Full label '{full_name}' never drawn: {texts}"

        # Stay within the 64px panel.
        for x, y, text, color in drawn:
            assert x + 4 * len(text) <= 64, f"'{text}' at x={x} overflows 64px"


class TestEffectsTransitionNames:
    """Long transition names must not be cut mid-word, and must stay unique."""

    OLD_BROKEN = {'Dither Dis', 'Fade to Bl', 'Random Dis', 'Vertical W'}

    def test_no_mid_word_cuts_and_names_fit(self):
        display = get_sim_display()
        visual = Effects(display)
        visual.reset()
        visual.max_visible = len(TRANSITION_TYPES)  # show every row, no scrolling

        drawn = _capture(display)
        visual.draw()

        texts = [t[2] for t in drawn]

        for bad in self.OLD_BROKEN:
            assert bad not in texts, f"Found old truncated label: {bad!r}"

        full_names = [t.name for t in TRANSITION_TYPES]
        for t in texts:
            # No drawn row text may be a strict (partial, non-word-boundary)
            # mid-word prefix of a full transition name it doesn't equal.
            for full in full_names:
                if t != full and full.startswith(t):
                    # Allowed only if t is itself a real, complete word (i.e.
                    # the cut lands exactly on a space boundary), never a
                    # bare character slice like the old bug.
                    cut_word = full[:len(t)]
                    assert cut_word == t and (len(full) == len(t) or full[len(t)] == ' '), (
                        f"Mid-word cut of '{full}' found: '{t}'"
                    )

        for x, y, text, color in drawn:
            assert x + 4 * len(text) <= 64, f"'{text}' at x={x} overflows 64px"

    def test_no_two_transitions_render_identically(self):
        display = get_sim_display()
        visual = Effects(display)
        visual.reset()
        visual.max_visible = len(TRANSITION_TYPES)

        drawn = _capture(display)
        visual.draw()

        # Row texts are everything drawn at x==10 (the name column).
        row_texts = [t[2] for t in drawn if t[0] == 10]
        assert len(row_texts) == len(TRANSITION_TYPES)
        assert len(set(row_texts)) == len(row_texts), (
            f"Two transitions render identically: {row_texts}"
        )
