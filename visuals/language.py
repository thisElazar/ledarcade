"""
LANGUAGE - Hello in Every Language
===================================
Displays "Hello" (or equivalent greeting) in 45 world languages,
romanized to ASCII.  Non-Latin scripts get pixel-art glyph samples.
Auto-cycles with crossfade transitions.
"""

from . import Visual

# ---------------------------------------------------------------------------
# Pixel art glyphs for non-Latin scripts
# Each entry is a list of (dx, dy) pixel offsets drawn relative to a
# center position.  Glyphs are roughly 8-12 px tall.
# ---------------------------------------------------------------------------

# Chinese: simplified 你 (ni)
GLYPH_CHINESE = [
    # left radical 亻
    (0, 0), (1, 0),
    (1, 1), (1, 2),
    (0, 3), (1, 3),
    (-1, 4), (1, 4),
    (-2, 5), (1, 5),
    (1, 6), (1, 7),
    # right side 尔
    (3, 0), (5, 0), (7, 0),
    (4, 1), (6, 1),
    (5, 2),
    (3, 3), (4, 3), (5, 3), (6, 3), (7, 3),
    (5, 4),
    (4, 5), (6, 5),
    (3, 6), (7, 6),
    (3, 7), (7, 7),
]

# Japanese: hiragana あ (a)
GLYPH_JAPANESE = [
    (1, 0), (2, 0), (3, 0), (4, 0),
    (5, 1),
    (0, 2), (1, 2), (2, 2), (3, 2), (4, 2), (5, 2), (6, 2),
    (1, 3), (5, 3),
    (0, 4), (2, 4), (5, 4),
    (0, 5), (3, 5), (5, 5),
    (1, 6), (3, 6), (4, 6), (6, 6),
    (2, 7), (3, 7), (6, 7),
    (5, 8),
]

# Korean: hangul 한 (han)
GLYPH_KOREAN = [
    # ㅎ top
    (2, 0), (3, 0), (4, 0),
    (1, 1), (5, 1),
    (3, 2),
    (1, 3), (2, 3), (3, 3), (4, 3), (5, 3),
    # ㅏ right
    (7, 0), (7, 1), (7, 2), (7, 3), (7, 4), (7, 5),
    (8, 2), (9, 2),
    # ㄴ bottom
    (1, 6), (1, 7), (1, 8),
    (2, 8), (3, 8), (4, 8), (5, 8), (6, 8), (7, 8),
]

# Arabic: سلام (salaam) - connected script shape
GLYPH_ARABIC = [
    # baseline with connected letters
    (0, 6), (1, 6), (2, 6), (3, 6), (4, 6), (5, 6), (6, 6),
    (7, 6), (8, 6), (9, 6), (10, 6), (11, 6),
    # sin teeth
    (1, 5), (3, 5), (5, 5),
    (1, 4),
    # lam upstroke
    (7, 5), (7, 4), (7, 3), (7, 2), (7, 1),
    # alif upstroke
    (9, 5), (9, 4), (9, 3), (9, 2), (9, 1),
    # mim loop
    (11, 5), (12, 5), (12, 6), (11, 7), (12, 7),
]

# Hindi/Devanagari: न (na) with shirorekha headline
GLYPH_HINDI = [
    # shirorekha (headline bar)
    (0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0),
    (7, 0), (8, 0), (9, 0),
    # na character
    (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7),
    (2, 4), (3, 3), (4, 2),
    (5, 1), (5, 2), (5, 3), (5, 4), (5, 5), (5, 6), (5, 7),
    # ma character
    (8, 1), (8, 2), (8, 3), (8, 4), (8, 5), (8, 6), (8, 7),
    (9, 4),
]

# Russian/Cyrillic: Мир (Mir)
GLYPH_RUSSIAN = [
    # М
    (0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7),
    (1, 1), (2, 2), (3, 3),
    (4, 2), (5, 1),
    (6, 0), (6, 1), (6, 2), (6, 3), (6, 4), (6, 5), (6, 6), (6, 7),
    # и
    (8, 2), (8, 3), (8, 4), (8, 5), (8, 6), (8, 7),
    (9, 6), (10, 5), (11, 4),
    (12, 2), (12, 3), (12, 4), (12, 5), (12, 6), (12, 7),
]

# Greek: Γε (from Γεια = hello)
GLYPH_GREEK = [
    # Γ gamma (uppercase)
    (0, 0), (1, 0), (2, 0), (3, 0), (4, 0),
    (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7),
    (1, 1),
    # ε epsilon (lowercase)
    (7, 2), (8, 2), (9, 2),
    (6, 3),
    (6, 4), (7, 4), (8, 4),
    (6, 5),
    (7, 6), (8, 6), (9, 6),
]

# Hebrew: שלום (shalom)
GLYPH_HEBREW = [
    # shin ש
    (0, 2), (0, 3), (0, 4), (0, 5), (0, 6),
    (2, 2), (2, 3), (2, 4), (2, 5), (2, 6),
    (4, 2), (4, 3), (4, 4), (4, 5), (4, 6),
    (1, 6), (3, 6),
    # lamed ל
    (6, 0), (6, 1), (6, 2), (6, 3), (6, 4), (6, 5), (6, 6),
    (7, 6), (8, 5),
    # mem ם
    (10, 2), (11, 2), (12, 2),
    (10, 3), (12, 3),
    (10, 4), (12, 4),
    (10, 5), (12, 5),
    (10, 6), (11, 6), (12, 6),
]

# Thai: สวัสดี (sawasdee) - a few Thai characters
GLYPH_THAI = [
    # ส (sor suea) - stylized
    (0, 2), (1, 2), (2, 2),
    (0, 3), (2, 3),
    (0, 4), (1, 4), (2, 4),
    (2, 5),
    (0, 6), (1, 6), (2, 6),
    # ว (wor waen)
    (4, 2), (5, 2), (6, 2),
    (4, 3), (6, 3),
    (4, 4), (6, 4),
    (4, 5), (6, 5),
    (4, 6), (5, 6), (6, 6),
    # ด (dor dek)
    (8, 2), (9, 2), (10, 2),
    (8, 3),
    (8, 4), (9, 4), (10, 4),
    (8, 5), (10, 5),
    (8, 6), (9, 6), (10, 6),
    # sara ee vowel mark above
    (9, 0), (10, 0), (9, 1),
]

# Amharic/Ge'ez: ሰላም (selam)
GLYPH_AMHARIC = [
    # ሰ (se)
    (0, 1), (1, 1), (2, 1),
    (0, 2), (2, 2),
    (0, 3), (1, 3), (2, 3),
    (0, 4), (2, 4),
    (0, 5), (2, 5),
    (1, 6),
    # ላ (la)
    (4, 1), (5, 1),
    (5, 2), (5, 3),
    (4, 4), (5, 4), (6, 4),
    (5, 5),
    (4, 6), (5, 6), (6, 6),
    # ም (m)
    (8, 1), (9, 1), (10, 1),
    (8, 2), (10, 2),
    (8, 3), (9, 3), (10, 3),
    (9, 4),
    (9, 5),
    (8, 6), (9, 6), (10, 6),
]

# Georgian: გამ (gam)
GLYPH_GEORGIAN = [
    # გ (gan)
    (0, 2), (1, 2), (2, 2), (3, 2),
    (0, 3),
    (0, 4), (1, 4), (2, 4),
    (0, 5), (2, 5),
    (1, 6), (2, 6),
    # ა (an)
    (5, 2), (6, 2), (7, 2),
    (5, 3), (7, 3),
    (5, 4), (6, 4), (7, 4),
    (7, 5),
    (5, 6), (6, 6), (7, 6),
    # მ (man)
    (9, 2), (10, 2), (11, 2), (12, 2),
    (9, 3), (12, 3),
    (9, 4), (12, 4),
    (9, 5), (11, 5), (12, 5),
    (10, 6), (11, 6),
]

# Armenian: Բար (barev)
GLYPH_ARMENIAN = [
    # Բ (Ben)
    (0, 1), (1, 1), (2, 1), (3, 1),
    (0, 2), (3, 2),
    (0, 3), (1, 3), (2, 3), (3, 3),
    (0, 4), (3, 4),
    (0, 5), (3, 5),
    (0, 6), (1, 6), (2, 6), (3, 6),
    (0, 7),
    # ա (ayb)
    (5, 3), (6, 3), (7, 3),
    (5, 4), (7, 4),
    (5, 5), (6, 5), (7, 5),
    (7, 6),
    (5, 7), (6, 7), (7, 7),
    # ր (reh)
    (9, 3), (9, 4), (9, 5), (9, 6), (9, 7),
    (10, 3),
    (11, 4),
]

# Tamil: தமிழ (tamizh)
GLYPH_TAMIL = [
    # த (ta)
    (0, 1), (1, 1), (2, 1), (3, 1),
    (2, 2),
    (1, 3), (2, 3), (3, 3),
    (0, 4), (3, 4),
    (0, 5), (1, 5), (2, 5), (3, 5),
    # மி (mi)
    (5, 1), (6, 1), (7, 1), (8, 1),
    (5, 2), (8, 2),
    (5, 3), (6, 3), (7, 3), (8, 3),
    (5, 4), (8, 4),
    (5, 5), (8, 5),
    # vowel mark
    (9, 0), (9, 1),
    # ழ (zha)
    (11, 1), (12, 1), (13, 1),
    (11, 2),
    (11, 3), (12, 3),
    (12, 4),
    (11, 5), (12, 5), (13, 5),
]

# Persian uses Arabic script
GLYPH_PERSIAN = GLYPH_ARABIC

# Bengali uses a Devanagari-like script with similar headline
GLYPH_BENGALI = [
    # matra (headline)
    (0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0),
    (7, 0), (8, 0), (9, 0),
    # na
    (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6),
    (2, 3), (3, 3),
    (4, 1), (4, 2), (4, 3), (4, 4), (4, 5), (4, 6),
    # ma
    (7, 1), (7, 2), (7, 3), (7, 4), (7, 5), (7, 6),
    (8, 1), (9, 1),
    (9, 2), (9, 3), (9, 4), (9, 5), (9, 6),
    (8, 6),
]

# Urdu uses Arabic/Nastaliq script
GLYPH_URDU = GLYPH_ARABIC

# Ukrainian uses Cyrillic
GLYPH_UKRAINIAN = GLYPH_RUSSIAN

# Map script names to glyph data
SCRIPT_GLYPHS = {
    'chinese':    GLYPH_CHINESE,
    'japanese':   GLYPH_JAPANESE,
    'korean':     GLYPH_KOREAN,
    'arabic':     GLYPH_ARABIC,
    'hindi':      GLYPH_HINDI,
    'russian':    GLYPH_RUSSIAN,
    'greek':      GLYPH_GREEK,
    'hebrew':     GLYPH_HEBREW,
    'thai':       GLYPH_THAI,
    'amharic':    GLYPH_AMHARIC,
    'georgian':   GLYPH_GEORGIAN,
    'armenian':   GLYPH_ARMENIAN,
    'tamil':      GLYPH_TAMIL,
    'persian':    GLYPH_PERSIAN,
    'bengali':    GLYPH_BENGALI,
    'urdu':       GLYPH_URDU,
    'ukrainian':  GLYPH_UKRAINIAN,
}

# ---------------------------------------------------------------------------
# Greetings data: lang, text, accent color, script key (if non-Latin)
# ---------------------------------------------------------------------------
GREETINGS = [
    {'lang': 'ENGLISH',    'text': 'HELLO WORLD',           'color': (200, 60, 60)},
    {'lang': 'SPANISH',    'text': 'HOLA MUNDO',            'color': (220, 180, 30)},
    {'lang': 'FRENCH',     'text': 'BONJOUR LE MONDE',      'color': (50, 80, 200)},
    {'lang': 'GERMAN',     'text': 'HALLO WELT',            'color': (200, 160, 40)},
    {'lang': 'ITALIAN',    'text': 'CIAO MONDO',            'color': (40, 160, 60)},
    {'lang': 'PORTUGUESE', 'text': 'OLA MUNDO',             'color': (60, 180, 80)},
    {'lang': 'DUTCH',      'text': 'HALLO WERELD',          'color': (220, 120, 30)},
    {'lang': 'POLISH',     'text': 'CZESC SWIECIE',         'color': (200, 50, 50)},
    {'lang': 'RUSSIAN',    'text': 'PRIVET MIR',            'color': (60, 130, 200),   'script': 'russian'},
    {'lang': 'UKRAINIAN',  'text': 'PRYVIT SVITE',          'color': (50, 120, 200),   'script': 'ukrainian'},
    {'lang': 'GREEK',      'text': 'YEIA SOU KOSME',        'color': (80, 140, 220),   'script': 'greek'},
    {'lang': 'TURKISH',    'text': 'MERHABA DUNYA',         'color': (200, 40, 40)},
    {'lang': 'ARABIC',     'text': 'MARHABA',               'color': (40, 160, 80),    'script': 'arabic'},
    {'lang': 'HEBREW',     'text': 'SHALOM OLAM',           'color': (60, 100, 200),   'script': 'hebrew'},
    {'lang': 'PERSIAN',    'text': 'SALAM DONYA',           'color': (80, 180, 120),   'script': 'persian'},
    {'lang': 'HINDI',      'text': 'NAMASTE DUNIYA',        'color': (255, 150, 30),   'script': 'hindi'},
    {'lang': 'BENGALI',    'text': 'NAMASKAR',              'color': (40, 140, 60),    'script': 'bengali'},
    {'lang': 'URDU',       'text': 'SALAM DUNYA',           'color': (60, 160, 80),    'script': 'urdu'},
    {'lang': 'MANDARIN',   'text': 'NI HAO SHIJIE',         'color': (220, 40, 40),    'script': 'chinese'},
    {'lang': 'CANTONESE',  'text': 'NEI HOU SAIGAAI',       'color': (220, 80, 60),    'script': 'chinese'},
    {'lang': 'JAPANESE',   'text': 'KONNICHIWA',            'color': (220, 50, 80),    'script': 'japanese'},
    {'lang': 'KOREAN',     'text': 'ANNYEONG SEGYE',        'color': (60, 100, 200),   'script': 'korean'},
    {'lang': 'VIETNAMESE', 'text': 'XIN CHAO THE GIOI',     'color': (200, 60, 40)},
    {'lang': 'THAI',       'text': 'SAWASDEE',              'color': (180, 60, 160),   'script': 'thai'},
    {'lang': 'INDONESIAN', 'text': 'HALO DUNIA',            'color': (200, 40, 40)},
    {'lang': 'TAGALOG',    'text': 'KAMUSTA MUNDO',          'color': (40, 80, 180)},
    {'lang': 'MALAY',      'text': 'HAI DUNIA',             'color': (220, 180, 40)},
    {'lang': 'SWAHILI',    'text': 'HABARI DUNIA',          'color': (40, 180, 60)},
    {'lang': 'AMHARIC',    'text': 'SELAM ALEM',            'color': (60, 180, 40),    'script': 'amharic'},
    {'lang': 'HAUSA',      'text': 'SANNU DUNIYA',          'color': (120, 180, 40)},
    {'lang': 'IGBO',       'text': 'NDEWO UWA',              'color': (80, 200, 80)},
    {'lang': 'YORUBA',     'text': 'BAWO NI AIYE',          'color': (100, 180, 60)},
    {'lang': 'ZULU',       'text': 'SAWUBONA MHLABA',       'color': (200, 120, 40)},
    {'lang': 'HAWAIIAN',   'text': 'ALOHA HONUA',           'color': (80, 200, 180)},
    {'lang': 'MAORI',      'text': 'KIA ORA TE AO',         'color': (60, 160, 60)},
    {'lang': 'NAVAJO',     'text': "YA'AT'EEH",             'color': (180, 100, 40)},
    {'lang': 'QUECHUA',    'text': 'ALLIANCHU PACHA',       'color': (180, 80, 40)},
    {'lang': 'GUARANI',    'text': "MBA'EICHAPA",           'color': (120, 180, 60)},
    {'lang': 'FINNISH',    'text': 'HEI MAAILMA',           'color': (180, 200, 240)},
    {'lang': 'HUNGARIAN',  'text': 'HELLO VILAG',           'color': (180, 60, 40)},
    {'lang': 'WELSH',      'text': 'HELO BYD',              'color': (180, 40, 60)},
    {'lang': 'IRISH',      'text': 'DIA DUIT',              'color': (40, 160, 80)},
    {'lang': 'BASQUE',     'text': 'KAIXO MUNDUA',          'color': (180, 40, 40)},
    {'lang': 'LATIN',      'text': 'SALVE MUNDE',            'color': (180, 160, 80)},
    {'lang': 'ESPERANTO',  'text': 'SALUTON MONDO',         'color': (80, 180, 80)},
    {'lang': 'ARMENIAN',   'text': 'BAREV ASHKHARH',        'color': (200, 120, 60),   'script': 'armenian'},
    {'lang': 'GEORGIAN',   'text': 'GAMARJOBA',             'color': (160, 80, 40),    'script': 'georgian'},
    {'lang': 'TAMIL',      'text': 'VANAKKAM',              'color': (200, 100, 40),   'script': 'tamil'},
]

NUM_GREETINGS = len(GREETINGS)

# Layout constants
LINE1_CHARS = 14   # max chars on a single centered line
LINE2_CHARS = 28   # max chars across two lines before scrolling
SCROLL_SPEED = 15  # px/s (slow)


def _split_two_lines(text):
    """Split text at a word boundary into two lines, each <= 14 chars."""
    words = text.split()
    line1 = ""
    line2 = ""
    for w in words:
        candidate = (line1 + " " + w).strip() if line1 else w
        if len(candidate) <= LINE1_CHARS:
            line1 = candidate
        else:
            line2 = (line2 + " " + w).strip() if line2 else w
    return line1, line2


class Language(Visual):
    name = "LANGUAGE"
    description = "Hello in every language"
    category = "culture"

    def reset(self):
        self.time = 0.0
        self.index = 0
        self.prev_index = -1
        self.auto_advance = True
        self.display_timer = 0.0
        self.display_duration = 5.0
        self.fade_timer = 0.0
        self.fade_duration = 0.6
        self.scroll_offset = 0.0
        self.overlay_timer = 0.0
        self.overlay_text = ""
        self._input_cooldown = 0.0

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------
    def handle_input(self, input_state):
        if self._input_cooldown > 0:
            return False
        consumed = False

        if input_state.left_pressed:
            self._go(-1)
            consumed = True
        if input_state.right_pressed:
            self._go(1)
            consumed = True
        if input_state.up_pressed:
            self._go(-5)
            consumed = True
        if input_state.down_pressed:
            self._go(5)
            consumed = True

        if input_state.action_l or input_state.action_r:
            self.auto_advance = not self.auto_advance
            self.overlay_text = "AUTO ON" if self.auto_advance else "AUTO OFF"
            self.overlay_timer = 1.5
            consumed = True

        if consumed:
            self._input_cooldown = 0.15
        return consumed

    def _go(self, delta):
        self.prev_index = self.index
        self.index = (self.index + delta) % NUM_GREETINGS
        self.display_timer = 0.0
        self.scroll_offset = 0.0
        self.fade_timer = self.fade_duration

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    def update(self, dt):
        self.time += dt
        if self._input_cooldown > 0:
            self._input_cooldown -= dt

        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

        if self.fade_timer > 0:
            self.fade_timer = max(0.0, self.fade_timer - dt)

        # Scroll only for very long text (> 28 chars)
        entry = GREETINGS[self.index]
        if len(entry['text']) > LINE2_CHARS:
            self.scroll_offset += dt * SCROLL_SPEED

        # Auto-advance
        if self.auto_advance:
            self.display_timer += dt
            if self.display_timer >= self.display_duration:
                self.display_timer = 0.0
                self.prev_index = self.index
                self.index = (self.index + 1) % NUM_GREETINGS
                self.scroll_offset = 0.0
                self.fade_timer = self.fade_duration

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------
    def draw(self):
        d = self.display
        d.clear()

        fade_in = 1.0
        fade_out = 0.0
        if self.fade_timer > 0 and self.prev_index >= 0:
            t = self.fade_timer / self.fade_duration
            fade_out = t
            fade_in = 1.0 - t

        # Draw previous entry fading out
        if fade_out > 0 and self.prev_index >= 0:
            self._draw_entry(self.prev_index, fade_out, fading_out=True)

        # Draw current entry fading in
        self._draw_entry(self.index, fade_in, fading_out=False)

        # Footer: position indicator
        pos_text = "%d/%d" % (self.index + 1, NUM_GREETINGS)
        d.draw_text_small(2, 59, pos_text, (100, 100, 100))

        # Overlay
        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            c = (int(220 * alpha), int(220 * alpha), int(220 * alpha))
            ow = len(self.overlay_text) * 4
            ox = max(0, (64 - ow) // 2)
            d.draw_text_small(ox, 40, self.overlay_text, c)

    def _draw_entry(self, idx, alpha, fading_out=False):
        d = self.display
        entry = GREETINGS[idx]
        lang = entry['lang']
        text = entry['text']
        r, g, b = entry['color']
        script = entry.get('script')

        ar = int(r * alpha)
        ag = int(g * alpha)
        ab = int(b * alpha)
        color = (ar, ag, ab)

        dim_r = int(r * 0.4 * alpha)
        dim_g = int(g * 0.4 * alpha)
        dim_b = int(b * 0.4 * alpha)
        dim_color = (dim_r, dim_g, dim_b)

        # Language name at y=2, centered
        lang_w = len(lang) * 4
        lang_x = max(0, (64 - lang_w) // 2)
        d.draw_text_small(lang_x, 2, lang, color)

        # Pixel art glyph area y=12-24 (for non-Latin scripts)
        if script and script in SCRIPT_GLYPHS:
            glyph = SCRIPT_GLYPHS[script]
            self._draw_glyph(glyph, color)

        # Accent bar at y=25, 1px high
        for x in range(64):
            d.set_pixel(x, 25, dim_color)

        # Greeting text: two-line layout
        text_len = len(text)

        if text_len <= LINE1_CHARS:
            # Single line centered at y=28
            tw = text_len * 4
            tx = max(0, (64 - tw) // 2)
            d.draw_text_small(tx, 28, text, color)

        elif text_len <= LINE2_CHARS:
            # Two lines at y=28 and y=35
            l1, l2 = _split_two_lines(text)
            w1 = len(l1) * 4
            w2 = len(l2) * 4
            d.draw_text_small(max(0, (64 - w1) // 2), 28, l1, color)
            d.draw_text_small(max(0, (64 - w2) // 2), 35, l2, color)

        else:
            # Scrolling (very rare)
            if fading_out:
                offset = 0
            else:
                padded = text + "    " + text
                total_w = (len(text) + 4) * 4
                offset = int(self.scroll_offset) % total_w
                text = padded
            d.draw_text_small(2 - offset, 28, text, color)

    def _draw_glyph(self, glyph, color):
        """Draw a pixel-art glyph centered in the y=12-24 area."""
        if not glyph:
            return
        d = self.display
        # Find bounding box
        min_x = min(p[0] for p in glyph)
        max_x = max(p[0] for p in glyph)
        min_y = min(p[1] for p in glyph)
        max_y = max(p[1] for p in glyph)
        gw = max_x - min_x + 1
        gh = max_y - min_y + 1
        # Center in the 64-wide, y=12..24 (13px tall) area
        ox = (64 - gw) // 2 - min_x
        oy = 12 + (13 - gh) // 2 - min_y
        for dx, dy in glyph:
            px = ox + dx
            py = oy + dy
            if 0 <= px < 64 and 12 <= py <= 24:
                d.set_pixel(px, py, color)
