"""Regression tests for legend-audit truncation fixes (batch B):

1. visuals/scales.py — scale subtitles were hard-cut at 14 chars (cutting
   words like "HUNGARIAN MINOR" mid-word) and the display-mode footer
   indicator showed 3-letter cuts ('NOT'/'NUM'/'DEG') instead of real words.
2. visuals/wifi_config.py — network names in the scan list were cut to 12
   chars with no indication; the selected row must scroll to reveal the
   full SSID, and unselected cut rows must be visibly marked.
3. visuals/scripts.py — the glyph table baked in mid-word-cut names like
   'A WITH DIAER' (DIAERESIS); the data now holds the full accurate name
   and the on-screen label scrolls (existing _draw_scrolling pattern) when
   it doesn't fit statically.
4. visuals/credits.py — 'NAGEL-SCHRECK.' was a cut of the traffic-model
   name NAGEL-SCHRECKENBERG; it must now show in full, split across two
   lines in the file's existing multi-line-credit style.
"""
from _harness import get_sim_display
from visuals.scales import Scales, SCALES, MODE_NAMES
from visuals.wifi_config import WiFiConfig
from visuals.scripts import Scripts, CHARACTERS
from visuals.credits import Credits

DISPLAY_W = 64


def _spy(display, monkeypatch, attr="draw_text_small"):
    """Monkeypatch display.<attr> to record every (x, y, text) drawn."""
    recorded = []
    real = getattr(display, attr)

    def spy_fn(x, y, text, color):
        recorded.append((x, y, text))
        return real(x, y, text, color)

    monkeypatch.setattr(display, attr, spy_fn)
    return recorded


def _rightmost_col(x, text):
    """Upper bound on the rightmost pixel column a drawn string can touch
    (3px-wide glyphs, 4px advance per char — see arcade.py _render_font)."""
    if not text:
        return x
    return x + 4 * (len(text) - 1) + 2


# ── Task 1: visuals/scales.py ──────────────────────────────────────────

def _find_scale(name):
    return next(i for i, s in enumerate(SCALES) if s['name'] == name)


def test_all_scale_subtitles_fit_without_mid_word_cuts():
    for s in SCALES:
        sub = s.get('subtitle', '')
        assert len(sub) <= 15, (s['name'], sub)
        # None of the fixed subtitles should still end mid-word (the old
        # 14-char cutoff chopped these specific strings).
        assert sub not in (
            'HUNGARIAN MINO', 'BLUE NOTE ADDE', 'DOMINANT BLUES',
            'DREAMY FLOATIN', 'IN SCALE - KOT',
        ), sub


def test_hungarian_subtitle_draws_in_full(monkeypatch):
    display = get_sim_display()
    v = Scales(display)
    v.scale_idx = _find_scale('HUNGARIAN')
    recorded = _spy(display, monkeypatch, "draw_text_raw")
    v.draw()
    texts = [t for (_, _, t) in recorded]
    assert 'HUNGARIAN MINO' not in texts
    assert 'HUNGARIAN MINOR' in texts


def test_blue_note_added_subtitle_draws_in_full(monkeypatch):
    display = get_sim_display()
    v = Scales(display)
    v.scale_idx = _find_scale('BLUES')
    recorded = _spy(display, monkeypatch, "draw_text_raw")
    v.draw()
    texts = [t for (_, _, t) in recorded]
    assert 'BLUE NOTE ADDE' not in texts
    assert 'BLUE NOTE ADDED' in texts


def test_mode_indicator_shows_full_word_not_abbreviation(monkeypatch):
    display = get_sim_display()
    v = Scales(display)
    for mode_idx, full_name in enumerate(MODE_NAMES):
        v.display_mode = mode_idx
        recorded = _spy(display, monkeypatch, "draw_text_raw")
        v.draw()
        texts = [t for (_, _, t) in recorded]
        assert full_name in texts, (full_name, texts)
        # The old bug drew a bare 3-letter cut, and 'NOT' in particular
        # reads as an unrelated English word.
        assert 'NOT' not in texts
        assert 'NUM' not in texts
        assert 'DEG' not in texts


def test_scales_header_and_footer_text_fits_on_screen(monkeypatch):
    display = get_sim_display()
    v = Scales(display)
    recorded = _spy(display, monkeypatch, "draw_text_raw")
    for scale_idx in range(len(SCALES)):
        for mode_idx in range(len(MODE_NAMES)):
            v.scale_idx = scale_idx
            v.display_mode = mode_idx
            recorded.clear()
            v.draw()
            for x, y, text in recorded:
                assert x >= 0, (scale_idx, mode_idx, x, text)
                assert _rightmost_col(x, text) <= DISPLAY_W - 1, (
                    scale_idx, mode_idx, x, text)


# ── Task 2: visuals/wifi_config.py ─────────────────────────────────────

def test_wifi_scan_list_selected_row_scrolls_full_ssid(sandbox, monkeypatch):
    display = get_sim_display()
    # Don't scan real networks — inject a fake list instead.
    monkeypatch.setattr(WiFiConfig, "_start_scan", lambda self: None)
    wc = WiFiConfig(display)

    ssid_a = 'NETGEAR-Guest-North'
    ssid_b = 'NETGEAR-Guest-South'
    assert ssid_a[:12] == ssid_b[:12], "test fixture must share a 12-char prefix"
    wc._networks = [(ssid_a, 80), (ssid_b, 60)]
    wc._scroll_offset = 0
    max_chars = 12

    def label_at_row(cursor, t, row_idx):
        wc._scan_cursor = cursor
        wc.time = t
        recorded = _spy(display, monkeypatch, "draw_text_small")
        wc.draw()
        y = 9 + row_idx * 7 + 1
        matches = [text for (x, yy, text) in recorded if yy == y]
        assert matches, (cursor, t, row_idx, recorded)
        return matches[0]

    # t=0: selected row (network 0) shows the shared prefix window.
    label0_t0 = label_at_row(cursor=0, t=0.0, row_idx=0)
    assert label0_t0 == ssid_a[:max_chars]

    # Later: the selected row scrolls to reveal the distinguishing tail.
    tail_time = (len(ssid_a) - max_chars) / 2.0 + 0.01
    label0_later = label_at_row(cursor=0, t=tail_time, row_idx=0)
    assert label0_later == ssid_a[len(ssid_a) - max_chars:]
    assert label0_later != label0_t0

    # Unselected row (network 1) is visibly marked as cut, never silently
    # truncated.
    label1_unselected = label_at_row(cursor=0, t=0.0, row_idx=1)
    assert label1_unselected != ssid_b[:max_chars]
    assert label1_unselected.endswith('>')
    assert label1_unselected[:-1] == ssid_b[:max_chars - 1]

    # Selecting the OTHER same-prefix network reveals ITS full tail —
    # the two networks are now distinguishable once selected.
    tail_time_b = (len(ssid_b) - max_chars) / 2.0 + 0.01
    label1_selected = label_at_row(cursor=1, t=tail_time_b, row_idx=1)
    assert label1_selected == ssid_b[len(ssid_b) - max_chars:]
    assert label1_selected != label0_later


def test_wifi_scan_short_ssid_unaffected(sandbox, monkeypatch):
    """An SSID that already fits should draw unchanged (no marker, no scroll)."""
    display = get_sim_display()
    monkeypatch.setattr(WiFiConfig, "_start_scan", lambda self: None)
    wc = WiFiConfig(display)
    wc._networks = [('ShortNet', 90)]
    wc._scroll_offset = 0
    wc._scan_cursor = 0
    wc.time = 0.0
    recorded = _spy(display, monkeypatch, "draw_text_small")
    wc.draw()
    labels = [text for (x, y, text) in recorded if y == 10]
    assert labels == ['ShortNet']


# ── Task 3: visuals/scripts.py ──────────────────────────────────────────

_FIXED_LATIN_NAMES = [
    'A WITH CIRCUMFLEX', 'A WITH DIAERESIS', 'A WITH RING ABOVE',
    'C WITH CEDILLA', 'E WITH CIRCUMFLEX', 'E WITH DIAERESIS',
    'I WITH CIRCUMFLEX', 'I WITH DIAERESIS', 'O WITH CIRCUMFLEX',
    'O WITH DIAERESIS', 'O WITH STROKE', 'U WITH CIRCUMFLEX',
    'U WITH DIAERESIS', 'Y WITH DIAERESIS',
]

_OLD_CUT_NAMES = [
    'A WITH CIRCU', 'A WITH DIAER', 'A WITH RING ', 'C WITH CEDIL',
    'E WITH CIRCU', 'E WITH DIAER', 'I WITH CIRCU', 'I WITH DIAER',
    'O WITH CIRCU', 'O WITH DIAER', 'O WITH STROK', 'U WITH CIRCU',
    'U WITH DIAER', 'Y WITH DIAER',
]


def _find_char_idx(name, script='LATIN'):
    for i, ch in enumerate(CHARACTERS):
        if ch['name'] == name and ch['script'] == script:
            return i
    raise AssertionError(f"no CHARACTERS entry named {name!r} ({script})")


def test_glyph_table_no_longer_has_cut_diacritic_names():
    for old in _OLD_CUT_NAMES:
        for ch in CHARACTERS:
            assert ch['name'] != old, ch
            assert ch['concept'] != old, ch
    for full in _FIXED_LATIN_NAMES:
        assert _find_char_idx(full) is not None


def test_diaeresis_glyph_label_draws_full_word_not_cut(monkeypatch):
    display = get_sim_display()
    v = Scripts(display)
    v._start_char(_find_char_idx('A WITH DIAERESIS'))
    v.time = 0.0
    recorded = _spy(display, monkeypatch, "draw_text_small")
    v.draw()
    texts = [t for (_, _, t) in recorded]
    assert 'A WITH DIAER' not in texts
    assert 'A WITH DIAERESIS' in texts


def test_circumflex_glyph_label_scrolls_to_reveal_full_word(monkeypatch):
    """17 chars doesn't fit statically — it must scroll (existing
    _draw_scrolling pattern), never draw the old cut string."""
    display = get_sim_display()
    v = Scripts(display)
    v._start_char(_find_char_idx('A WITH CIRCUMFLEX'))
    v.overlay_timer = 0  # unrelated overlay text also draws at y=7; skip it

    seen_texts = set()
    for t in (0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0):
        v.time = t
        recorded = _spy(display, monkeypatch, "draw_text_small")
        v.draw()
        for x, y, text in recorded:
            if y == 7:
                seen_texts.add(text)
                # The string passed to draw_text_small is always the full,
                # correct word — never a mid-word-cut version. Any pixel
                # clipping happens off-screen, not in the data.
                assert text != 'A WITH CIRCU'
                assert text == 'A WITH CIRCUMFLEX'
    assert seen_texts == {'A WITH CIRCUMFLEX'}


# ── Task 4: visuals/credits.py ──────────────────────────────────────────

def test_credits_every_line_fits_the_panel():
    """15 chars at x=2 with a 4px advance is the most the 64px panel shows."""
    c = Credits(get_sim_display())
    too_wide = [t for (t, _color) in c.lines if len(t) > 15]
    assert too_wide == []


def test_credits_nagel_schreckenberg_shown_in_full():
    display = get_sim_display()
    c = Credits(display)
    texts = [t for (t, _color) in c.lines]
    assert 'NAGEL-SCHRECK.' not in texts
    # Split across two lines in the file's existing multi-line-credit style.
    idx = texts.index('SCHRECKENBERG')
    assert texts[idx - 1] == 'NAGEL &' and texts[idx + 1] == '1992'


def test_credits_nagel_schreckenberg_draws_within_bounds(monkeypatch):
    display = get_sim_display()
    c = Credits(display)
    idx = [t for (t, _c) in c.lines].index('NAGEL &')
    # Position the reel so this line (and the one after it) is on screen.
    c.scroll_y = DISPLAY_W + (idx * c.line_height) - 10
    recorded = _spy(display, monkeypatch, "draw_text_small")
    c.draw()
    texts = [t for (_, _, t) in recorded]
    assert 'NAGEL &' in texts
    assert 'SCHRECKENBERG' in texts
    for x, y, text in recorded:
        assert x >= 0
        assert _rightmost_col(x, text) <= DISPLAY_W - 1, (x, text)
