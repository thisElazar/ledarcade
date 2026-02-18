"""
LANGUAGE - Hello in Every Language
===================================
Displays greetings in 48 world languages with native script pixel art.
Each slide shows four layers:
  1. Language name in English
  2. Language name in native script (pixel art or native Latin text)
  3. Greeting romanized to ASCII
  4. Greeting in native script (pixel art for non-Latin scripts)
Auto-cycles with crossfade transitions.
"""

import random
from . import Visual

# ---------------------------------------------------------------------------
# Bitmap helpers
# ---------------------------------------------------------------------------

def _bmp(*rows):
    """Convert bitmap string rows to pixel coordinate list.
    '#' = pixel on, anything else = pixel off."""
    pts = []
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == '#':
                pts.append((x, y))
    return pts


def _compose(*glyphs, gap=1):
    """Place multiple glyphs side by side with `gap` px between them.
    Returns combined coordinate list."""
    pts = []
    x_off = 0
    for g in glyphs:
        if not g:
            continue
        min_x = min(p[0] for p in g)
        max_x = max(p[0] for p in g)
        w = max_x - min_x + 1
        for dx, dy in g:
            pts.append((x_off + dx - min_x, dy))
        x_off += w + gap
    return pts


# ===================================================================
# Chinese Hanzi (5-7 wide x 7 tall)
# ===================================================================

_c_zhong = _bmp(  # 中
    '..#..',
    '.###.',
    '.#.#.',
    '#####',
    '.#.#.',
    '.###.',
    '..#..',
)

_c_wen = _bmp(  # 文
    '.###.',
    '..#..',
    '#####',
    '.#.#.',
    '..#..',
    '.#.#.',
    '#...#',
)

_c_ni = _bmp(  # 你
    '#..##.',
    '#.#...',
    '#.####',
    '#..#..',
    '.##.#.',
    '#..#.#',
    '....#.',
)

_c_hao = _bmp(  # 好
    '.#..#.',
    '.#.###',
    '###.#.',
    '.#.###',
    '.#..#.',
    '.##.#.',
    '#..###',
)

_c_ri = _bmp(  # 日
    '#####',
    '#...#',
    '#####',
    '#...#',
    '#...#',
    '#...#',
    '#####',
)

_c_hon = _bmp(  # 本
    '..#..',
    '#####',
    '..#..',
    '.###.',
    '.#.#.',
    '#.#.#',
    '..#..',
)

_c_go = _bmp(  # 語
    '##.####',
    '.#.#..#',
    '##.####',
    '.#..#..',
    '##.####',
    '.#.#..#',
    '##.####',
)

_c_yue = _bmp(  # 粵
    '.#.#.#.',
    '..###..',
    '#######',
    '..###..',
    '.#.#.#.',
    '.#####.',
    '.#...#.',
)

# Composed Chinese words
G_ZH_NAME  = _compose(_c_zhong, _c_wen)                # 中文
G_ZH_HELLO = _compose(_c_ni, _c_hao)                   # 你好
G_YUE_NAME = _compose(_c_yue, _c_go)                   # 粵語
G_JP_NAME  = _compose(_c_ri, _c_hon, _c_go)            # 日本語


# ===================================================================
# Japanese Hiragana (5 wide x 7 tall)
# ===================================================================

_h_ko = _bmp(  # こ
    '.####',
    '.....',
    '.....',
    '.....',
    '.....',
    '.####',
    '.....',
)

_h_n = _bmp(  # ん
    '.#...',
    '.#...',
    '..#..',
    '..#..',
    '...#.',
    '...#.',
    '..#..',
)

_h_ni = _bmp(  # に
    '#..#.',
    '#..#.',
    '#.##.',
    '#..#.',
    '#..#.',
    '#..#.',
    '#....',
)

_h_chi = _bmp(  # ち
    '..#..',
    '#####',
    '..#..',
    '..##.',
    '...#.',
    '...#.',
    '..#..',
)

_h_ha = _bmp(  # は
    '#.##.',
    '#.#.#',
    '#.#.#',
    '#.#.#',
    '#.##.',
    '#..#.',
    '#..#.',
)

# Composed hiragana word
G_JP_HELLO = _compose(_h_ko, _h_n, _h_ni, _h_chi, _h_ha)  # こんにちは


# ===================================================================
# Korean Hangul (word-level bitmaps, 7 tall)
# ===================================================================

G_KR_NAME = _bmp(  # 한국어
    # 한        국         어
    '.##.#..####...##..',
    '#..#.#.....#.#..#.',
    '.##.##.....#.#..##',
    '....#......#.....#',
    '....#..###.......#',
    '#...#..#.#..##..#.',
    '#####..###..##....',
)

G_KR_HELLO = _bmp(  # 안녕
    # 안       녕
    '.##.#..#....',
    '#..#.#.####.',
    '.##.#......#',
    '....#......#',
    '....#...##..',
    '#......#..#.',
    '#####...##..',
)


# ===================================================================
# Cyrillic letters (3 wide x 5 tall)
# ===================================================================

_cy = {}
_cy['R']    = _bmp('##.', '#.#', '##.', '#..', '#..')          # Р
_cy['u']    = _bmp('#.#', '#.#', '.#.', '.#.', '#..')          # у
_cy['s']    = _bmp('.##', '#..', '#..', '#..', '.##')          # с
_cy['k']    = _bmp('#.#', '#.#', '##.', '#.#', '#.#')         # к
_cy['i']    = _bmp('#.#', '#.#', '###', '#.#', '#.#')         # и
_cy['j']    = _bmp('.#.', '#.#', '###', '#.#', '#.#')         # й (и + breve)
_cy['P']    = _bmp('###', '#.#', '#.#', '#.#', '#.#')         # П
_cy['r']    = _bmp('##.', '#.#', '##.', '#..', '#..')          # р (same as Р)
_cy['v']    = _bmp('##.', '#.#', '##.', '#.#', '##.')         # в
_cy['e']    = _bmp('.##', '#..', '##.', '#..', '.##')         # е
_cy['t']    = _bmp('###', '.#.', '.#.', '.#.', '.#.')         # т
_cy['U']    = _bmp('#.#', '#.#', '.#.', '.#.', '.#.')         # У
_cy['a']    = _bmp('.#.', '#.#', '###', '#.#', '#.#')         # а
_cy['n']    = _bmp('#.#', '#.#', '###', '#.#', '#.#')         # н (same shape as и here)
_cy['soft'] = _bmp('#..', '#..', '##.', '#.#', '##.')         # ь
_cy['ii']   = _bmp('.#.', '...', '.#.', '.#.', '.#.')         # і
_cy['ji']   = _bmp('#.#', '...', '.#.', '.#.', '.#.')         # ї

# Composed Cyrillic words
G_RU_NAME  = _compose(_cy['R'], _cy['u'], _cy['s'], _cy['s'],
                       _cy['k'], _cy['i'], _cy['j'])           # Русский
G_RU_HELLO = _compose(_cy['P'], _cy['r'], _cy['i'], _cy['v'],
                       _cy['e'], _cy['t'])                     # Привет
G_UK_NAME  = _compose(_cy['U'], _cy['k'], _cy['r'], _cy['a'],
                       _cy['ji'], _cy['n'], _cy['s'],
                       _cy['soft'], _cy['k'], _cy['a'])        # Українська
G_UK_HELLO = _compose(_cy['P'], _cy['r'], _cy['i'], _cy['v'],
                       _cy['ii'], _cy['t'])                    # Привіт


# ===================================================================
# Greek letters (3 wide x 5 tall)
# ===================================================================

_gr = {}
_gr['E']   = _bmp('###', '#..', '##.', '#..', '###')          # Ε
_gr['l']   = _bmp('.#.', '.#.', '.#.', '#.#', '#.#')          # λ
_gr['h']   = _bmp('#..', '#..', '##.', '#.#', '#.#')          # η
_gr['n']   = _bmp('#.#', '#.#', '#.#', '.#.', '.#.')          # ν
_gr['i']   = _bmp('.#.', '.#.', '.#.', '.#.', '.#.')          # ι
_gr['k']   = _bmp('#.#', '#.#', '##.', '#.#', '#.#')          # κ
_gr['a']   = _bmp('.#.', '#.#', '###', '#.#', '#.#')          # α
_gr['G']   = _bmp('###', '#..', '#..', '#..', '#..')           # Γ

# Composed Greek words
G_EL_NAME  = _compose(_gr['E'], _gr['l'], _gr['l'], _gr['h'],
                       _gr['n'], _gr['i'], _gr['k'], _gr['a'])  # Ελληνικα
G_EL_HELLO = _compose(_gr['G'], _gr['E'], _gr['i'], _gr['a'])  # Γεια


# ===================================================================
# Arabic script (word-level bitmaps, ~8 tall)
# ===================================================================

G_AR_NAME = _bmp(  # العربية (al-arabiyya)
    '...............',
    '.#...#.........',
    '.#...#..#.##.#.',
    '.#...#..#.##.#.',
    '.#...####.##.#.',
    '.#####.........',
    '...............',
    '..........#.#..',
)

G_AR_HELLO = _bmp(  # مرحبا (marhaba)
    '................',
    '.#...#..........',
    '.#...#..##.#.#..',
    '.#...#.#..#.#.#.',
    '.#...#.#..#.#.#.',
    '.#####..##.####.',
    '................',
    '.............#...',
)

G_FA_NAME = _bmp(  # فارسی (farsi)
    '...............',
    '.#...#.#..#....',
    '.#...#.#..#.#..',
    '.#...#.#..####.',
    '.####..#.....#.',
    '..........####.',
    '...............',
    '..#..........#.',
)

G_SALAM = _bmp(  # سلام (salam) — shared by Persian/Urdu
    '...........',
    '.#...#.....',
    '.#...#..#..',
    '.#...#..#..',
    '.#...#..#..',
    '.#####.###.',
    '...........',
    '...........',
)

G_UR_NAME = _bmp(  # اردو (urdu)
    '.........',
    '.#...#...',
    '.#...#.#.',
    '.#...#.#.',
    '.#...####',
    '.#####...',
    '.........',
    '.........',
)


# ===================================================================
# Hebrew (word-level bitmaps, 7 tall)
# ===================================================================

G_HE_NAME = _bmp(  # עברית (ivrit)
    '...............',
    '#.#.##..##..#..',
    '#.#.#.#.#.#.#..',
    '#.#.##..#.#.#..',
    '#.#.#.#.#.#.#..',
    '.#..##..##..###',
    '...............',
)

G_HE_HELLO = _bmp(  # שלום (shalom)
    '.............',
    '#.#.#...##...',
    '#.#.#..#..#..',
    '#.#.#..#..#..',
    '#.#.#..#..#..',
    '.#..#...##...',
    '.............',
)


# ===================================================================
# Devanagari (word-level bitmaps, 8 tall — headline bar on top)
# ===================================================================

G_HI_NAME = _bmp(  # हिन्दी (hindi)
    '################',
    '#..#.#.#..#..#.#',
    '#..#.#.#..#..#.#',
    '##.#.#..#.#..#.#',
    '#..#.#..#.#..#.#',
    '#..#.#.#..#..#.#',
    '#..#.#.#..#.....',
    '................',
)

G_HI_HELLO = _bmp(  # नमस्ते (namaste)
    '#################',
    '#..#.#..#.##..#..',
    '#..#.#..#.#.#.#..',
    '#.##.####.##.###.',
    '#..#.#..#.#..#...',
    '#..#.#..#.#..#...',
    '#..#.#..#.#..#...',
    '.................',
)


# ===================================================================
# Bengali (word-level bitmaps, 8 tall — headline bar)
# ===================================================================

G_BN_NAME = _bmp(  # বাংলা (bangla)
    '#############',
    '#..#..##.#..#',
    '#..#..#..#..#',
    '#..#..#..#.##',
    '#..#..#..##.#',
    '#..#..##.#..#',
    '#..#.....#..#',
    '.............',
)

G_BN_HELLO = _bmp(  # নমস্কার (namaskar)
    '##################',
    '#..#.#..#.##.#..#.',
    '#..#.#..#.#..#..#.',
    '#.##.####.##.#.##.',
    '#..#.#..#.#..##.#.',
    '#..#.#..#.#..#..#.',
    '#..#.#..#.#..#..#.',
    '..................',
)


# ===================================================================
# Thai (word-level bitmaps, 8 tall)
# ===================================================================

G_TH_NAME = _bmp(  # ไทย (thai)
    '...........',
    '.#..##..#.#',
    '.#.#..#.#.#',
    '.#.#..#.#.#',
    '.#.#..#..#.',
    '.#..##...#.',
    '.#.......#.',
    '.#.........',
)

G_TH_HELLO = _bmp(  # สวัสดี (sawasdee)
    '......#.........',
    '.##..##..##..#..',
    '#..##..##..#.#..',
    '.##.#..#.##..#..',
    '#..##..##..#.#..',
    '.##..##..##..#..',
    '............#...',
    '................',
)


# ===================================================================
# Amharic / Ge'ez (word-level bitmaps, 7 tall)
# ===================================================================

G_AM_NAME = _bmp(  # አማርኛ (amarnya)
    '.##..##..##..##.',
    '#..##..##..##..#',
    '#..##..##..##..#',
    '.##..##..##..##.',
    '#..##..#.#.##..#',
    '#..##..#.#.##..#',
    '.##..##..#..##..',
)

G_AM_HELLO = _bmp(  # ሰላም (selam)
    '.##..#...##.',
    '#..#.#..#..#',
    '#..#.#..#..#',
    '.##..#...##.',
    '#..#.##.#..#',
    '#..#.##.#..#',
    '.##..#...##.',
)


# ===================================================================
# Georgian (word-level bitmaps, 7 tall)
# ===================================================================

G_KA_NAME = _bmp(  # ქართული (kartuli)
    '.##..##..##..#..',
    '#..##..##..#.#..',
    '#..##..##....#..',
    '#..#.##..##..#..',
    '#..##..##..#.#..',
    '.##.#..##..#.#..',
    '....#..#.##..###',
)

G_KA_HELLO = _bmp(  # გამარჯობა (gamarjoba)
    '.##..##..##..##.',
    '#..##..##..##..#',
    '#..##..##..##..#',
    '#...##..##.#.##.',
    '#..##..##..##..#',
    '.##.#..##..##..#',
    '....#..#.##..##.',
)


# ===================================================================
# Armenian (word-level bitmaps, 7 tall)
# ===================================================================

G_HY_NAME = _bmp(  # Հայերեն (hayeren)
    '#..##..#.##..##..##.',
    '#..##..#.#..#..##..#',
    '#..#.##..##.#..##..#',
    '####.##..#..#..#.##.',
    '#..#..#..##.#..##..#',
    '#..#..#..#..#..##..#',
    '#..#..#..#...##..##.',
)

G_HY_HELLO = _bmp(  # Բարև (barev)
    '###..##..##..#.#',
    '#..##..##..#.#.#',
    '###.#..##..#..#.',
    '#..##..####..#.#',
    '#..##..##..#.#.#',
    '###..##..##..#.#',
    '#................',
)


# ===================================================================
# Tamil (word-level bitmaps, 7 tall)
# ===================================================================

G_TA_NAME = _bmp(  # தமிழ் (tamizh)
    '.##..##..#..##.',
    '#..##..#.#.#...',
    '..#.#..#.#.#...',
    '.##.#..#.#..##.',
    '#..#.##..#....#',
    '#..#.##..#.#..#',
    '.##..##..#..##.',
)

G_TA_HELLO = _bmp(  # வணக்கம் (vanakkam)
    '.##..##..##..##..##.',
    '#..##..##..##..##..#',
    '#..##..#.##.#..##..#',
    '#..##..#.##.#..##..#',
    '.##..##..##..##.#..#',
    '..#..##..##..##..##.',
    '.##..##..##..##..##.',
)


# ===================================================================
# Gurmukhi / Punjabi (word-level bitmaps, 8 tall — headline bar)
# ===================================================================

G_PA_NAME = _bmp(  # ਪੰਜਾਬੀ (punjabi)
    '################',
    '#..#..#.##.#..#',
    '#.##..#..#.#..#',
    '#..#..#..#.#..#',
    '#..#..#.##.##.#',
    '#..#..#.#..#.##',
    '#..#..#.#..#..#',
    '................',
)

G_PA_HELLO = _bmp(  # ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ (sat sri akal)
    '###.###.###.###',
    '#.#..#..#.#.#.#',
    '###..#..#.#.#.#',
    '..#..#..###.##.',
    '###..#..#.#.#.#',
    '#....#..#.#.#.#',
    '###..#..#.#.###',
    '...............',
)


# ===================================================================
# Telugu (word-level bitmaps, 7 tall — rounded curvy script)
# ===================================================================

G_TE_NAME = _bmp(  # తెలుగు (telugu)
    '.##..##..##..##.',
    '#..##..#.#..#..#',
    '#..##..#.#..#..#',
    '.##..###.#...##.',
    '#..#...#.#..#..#',
    '#..#..#..#..#..#',
    '.##..##...##.##.',
)

G_TE_HELLO = _bmp(  # నమస్కారం (namaskaram)
    '.##..##..##..##..##.',
    '#..##..##..##..##..#',
    '#.##.####.##..##.##.',
    '#..#.#..#.##.#..#..#',
    '#..#.#..#.#..#..#..#',
    '#..#.#..#.#..#..#..#',
    '.##..##..##...##.##.',
)


# ===================================================================
# Additional Devanagari — Marathi & Nepali (8 tall, headline bar)
# ===================================================================

G_MR_NAME = _bmp(  # मराठी (marathi)
    '##############',
    '#..#.#..#..#.#',
    '#..#.#..#..#.#',
    '####.#..##.#.#',
    '#..#.#..#..#.#',
    '#..#.#..#..#.#',
    '#..#.#..#..#..',
    '..............',
)

G_MR_HELLO = _bmp(  # नमस्कार (namaskar)
    '#################',
    '#..#.#..#.##.#..#',
    '#..#.#..#.#..#..#',
    '#.##.####.##.#.##',
    '#..#.#..#.#..##.#',
    '#..#.#..#.#..#..#',
    '#..#.#..#.#..#..#',
    '.................',
)

G_NE_NAME = _bmp(  # नेपाली (nepali)
    '################',
    '#..#.#..#..#..#.',
    '#..#.#..#..#..#.',
    '#.##.####..#..#.',
    '#..#.#..#..#..#.',
    '#..#.#..#..#..#.',
    '#..#.#..#..#....',
    '................',
)

G_NE_HELLO = _bmp(  # नमस्ते (namaste) — same word as Hindi
    '#################',
    '#..#.#..#.##..#..',
    '#..#.#..#.#.#.#..',
    '#.##.####.##.###.',
    '#..#.#..#.#..#...',
    '#..#.#..#.#..#...',
    '#..#.#..#.#..#...',
    '.................',
)


# ===================================================================
# Additional Arabic script — Pashto (word-level, ~8 tall)
# ===================================================================

G_PS_NAME = _bmp(  # پښتو (pashto)
    '...........',
    '.#...#.#...',
    '.#...#.#.#.',
    '.#...#.#.#.',
    '.#...####.#',
    '.#####.....',
    '...........',
    '.#.#.......',
)

G_PS_HELLO = _bmp(  # سلام (salam) — same word, Pashto variant
    '...........',
    '.#...#.....',
    '.#...#..#..',
    '.#...#..#..',
    '.#...#..#..',
    '.#####.###.',
    '...........',
    '...........',
)


# ===================================================================
# Burmese (word-level bitmaps, 7 tall — circular/round characters)
# ===================================================================

G_MY_NAME = _bmp(  # မြန်မာ (myanma)
    '.##...##..##.',
    '#..#.#..##..#',
    '#..#.#..##..#',
    '#..#..##.#..#',
    '#..#.#..##..#',
    '#..#.#..##..#',
    '.##...##..##.',
)

G_MY_HELLO = _bmp(  # မင်္ဂလာပါ (mingalaba)
    '.##..##..##..##..##.',
    '#..##..##..##..##..#',
    '#..##..##..#.##.#..#',
    '#..#.##..##..##.#..#',
    '#..##..##..##..##..#',
    '#..##..##..##..##..#',
    '.##..##..##..##..##.',
)


# ===================================================================
# Malayalam (word-level bitmaps, 7 tall — loopy rounded script)
# ===================================================================

G_ML_NAME = _bmp(  # മലയാളം (malayalam)
    '.##..##..##..##..##.',
    '#..##..#.##.#..##..#',
    '#..##..#.##.#..##..#',
    '#..##..#.##.#..#.##.',
    '#..#.##..##.#..##..#',
    '#..#.##..##.#..##..#',
    '.##..##..##..##..##.',
)

G_ML_HELLO = _bmp(  # നമസ്കാരം (namaskaram)
    '.##..##..##..##..##.',
    '#..##..##..##..##..#',
    '#.##.####.##.#..#.#.',
    '#..#.#..#.##.#..#..#',
    '#..#.#..#.#..#..#..#',
    '#..#.#..#.#..#..#..#',
    '.##..##..##...##.##.',
)


# ===================================================================
# Odia (word-level bitmaps, 7 tall — rounded with curved top line)
# ===================================================================

G_OR_NAME = _bmp(  # ଓଡ଼ିଆ (odia)
    '.##..##..##..##.',
    '#..##..#.#..#..#',
    '#..##..#.#..#..#',
    '#..##..#.#..#..#',
    '#..##..#.#..#..#',
    '#..#.##..#..#..#',
    '.##..##..##..##.',
)

G_OR_HELLO = _bmp(  # ନମସ୍କାର (namaskar)
    '.##..##..##..##..##.',
    '#..##..##..##..##..#',
    '#.##.####.##.#..#..#',
    '#..#.#..#.##.##.#..#',
    '#..#.#..#.#..#..#..#',
    '#..#.#..#.#..#..#..#',
    '.##..##..##...##.##.',
)


# ===================================================================
# Tibetan (word-level bitmaps, 8 tall — angular with top line)
# ===================================================================

G_BO_NAME = _bmp(  # བོད་སྐད (bodskad — "Tibetan language")
    '................',
    '.##..##..##..##.',
    '#..##..##..##..#',
    '#..##..##..##..#',
    '#..#.##..##.#.#.',
    '#..##..##..##..#',
    '.##..##..##..##.',
    '################',
)

G_BO_HELLO = _bmp(  # བཀྲ་ཤིས་བདེ་ལེགས (tashi delek)
    '.................',
    '.##..##..##..##..',
    '#..##..##..##..#.',
    '#..##..#.##..##..',
    '#..#.##..##.#..#.',
    '#..##..##..##..#.',
    '.##..##..##..##..',
    '#################',
)


# ===================================================================
# Khmer (word-level bitmaps, 8 tall — elaborate ornate characters)
# ===================================================================

G_KM_NAME = _bmp(  # ខ្មែរ (khmer)
    '.##..##..##.',
    '#..##..##..#',
    '#..##..##..#',
    '#..#.##.#..#',
    '#..##..##..#',
    '#..##..##..#',
    '.##..##..##.',
    '............',
)

G_KM_HELLO = _bmp(  # សួស្តី (suostei)
    '.##..##..##..##.',
    '#..##..##..##..#',
    '#..##..##..##..#',
    '.##..##.#.#.##.#',
    '#..##..##..##..#',
    '#..##..##..##..#',
    '.##..##..##..##.',
    '................',
)


# ===================================================================
# Lao (word-level bitmaps, 7 tall — loopy, Thai-related)
# ===================================================================

G_LO_NAME = _bmp(  # ລາວ (lao)
    '.##..##..##.',
    '#..##..##..#',
    '#..##..##..#',
    '#..##..#.##.',
    '#..##..##..#',
    '#..##..##..#',
    '.##..##..##.',
)

G_LO_HELLO = _bmp(  # ສະບາຍດີ (sabaidee)
    '.##..##..##..##..##.',
    '#..##..##..##..##..#',
    '#..##..#.##.#..#.##.',
    '.##.#..##..##..##..#',
    '#..##..##..##..##..#',
    '#..##..##..##..#.##.',
    '.##..##..##..##..##.',
)


# ===================================================================
# Sinhala (word-level bitmaps, 7 tall — round bubbly characters)
# ===================================================================

G_SI_NAME = _bmp(  # සිංහල (sinhala)
    '.##..##..##..##.',
    '#..##..##..##..#',
    '#..##..##..##..#',
    '.##..##..##.#..#',
    '#..##..#.##.#..#',
    '#..##..##..##..#',
    '.##..##..##..##.',
)

G_SI_HELLO = _bmp(  # ආයුබෝවන් (ayubowan)
    '.##..##..##..##..##.',
    '#..##..##..##..##..#',
    '#..##..##..##..##..#',
    '.##.#..#.##..##.#..#',
    '#..##..##..##..##..#',
    '#..##..##..##..##..#',
    '.##..##..##..##..##.',
)


# ===================================================================
# Javanese / Aksara Jawa (word-level bitmaps, 7 tall)
# ===================================================================

G_JV_NAME = _bmp(  # ꦗꦮ (jawa in Javanese script)
    '.##..##.',
    '#..##..#',
    '#..##..#',
    '#.##.##.',
    '#..##..#',
    '#..##..#',
    '.##..##.',
)

G_JV_HELLO = _bmp(  # ꦱꦸꦒꦼꦁ (sugeng in Javanese script)
    '.##..##..##..##.',
    '#..##..##..##..#',
    '#..##..##..#.##.',
    '.##.#..#.##..##.',
    '#..##..##..##..#',
    '#..##..##..##..#',
    '.##..##..##..##.',
)


# ===================================================================
# Mongolian Cyrillic (composed from letters, 3x5)
# ===================================================================

_cy['M']    = _bmp('#.#', '###', '#.#', '#.#', '#.#')         # М
_cy['o']    = _bmp('.#.', '#.#', '#.#', '#.#', '.#.')         # о
_cy['g']    = _bmp('###', '#..', '#..', '#..', '#..')          # г
_cy['l']    = _bmp('.##', '.#.', '.#.', '#.#', '#.#')         # л
_cy['S']    = _bmp('.##', '#..', '.#.', '..#', '##.')         # С
_cy['b']    = _bmp('#..', '#..', '##.', '#.#', '##.')         # б
_cy['y2']   = _bmp('#.#', '#.#', '.#.', '.#.', '.#.')         # ы? no, й already exists
                                                                # y already exists as у

G_MN_NAME  = _compose(_cy['M'], _cy['o'], _cy['n'], _cy['g'],
                       _cy['o'], _cy['l'])                     # Монгол
G_MN_HELLO = _compose(_cy['S'], _cy['a'], _cy['j'], _cy['n'],
                       _cy['b'], _cy['a'], _cy['j'],
                       _cy['n'], _cy['a'])                     # Сайнбайна


# ===================================================================
# Greetings data
# ===================================================================
# Fields:
#   lang         - English name (layer 1)
#   native       - Native name in Latin script (layer 2 text), or None
#   text         - Romanized greeting (layer 3)
#   name_glyph   - Pixel art for native language name, or None
#   hello_glyph  - Pixel art for native greeting, or None
#   color        - Accent color (R, G, B)

GREETINGS = [
    # ── Latin-script languages ─────────────────────────────────
    {'lang': 'ENGLISH',    'native': None,          'text': 'HELLO WORLD',
     'name_glyph': None, 'hello_glyph': None, 'color': (200, 60, 60)},
    {'lang': 'SPANISH',    'native': 'ESPANOL',     'text': 'HOLA MUNDO',
     'name_glyph': None, 'hello_glyph': None, 'color': (220, 180, 30)},
    {'lang': 'FRENCH',     'native': 'FRANCAIS',    'text': 'BONJOUR LE MONDE',
     'name_glyph': None, 'hello_glyph': None, 'color': (50, 80, 200)},
    {'lang': 'GERMAN',     'native': 'DEUTSCH',     'text': 'HALLO WELT',
     'name_glyph': None, 'hello_glyph': None, 'color': (200, 160, 40)},
    {'lang': 'ITALIAN',    'native': 'ITALIANO',    'text': 'CIAO MONDO',
     'name_glyph': None, 'hello_glyph': None, 'color': (40, 160, 60)},
    {'lang': 'PORTUGUESE', 'native': 'PORTUGUES',   'text': 'OLA MUNDO',
     'name_glyph': None, 'hello_glyph': None, 'color': (60, 180, 80)},
    {'lang': 'DUTCH',      'native': 'NEDERLANDS',   'text': 'HALLO WERELD',
     'name_glyph': None, 'hello_glyph': None, 'color': (220, 120, 30)},
    {'lang': 'POLISH',     'native': 'POLSKI',      'text': 'WITAJ SWIECIE',
     'name_glyph': None, 'hello_glyph': None, 'color': (200, 50, 50)},
    {'lang': 'TURKISH',    'native': 'TURKCE',      'text': 'MERHABA DUNYA',
     'name_glyph': None, 'hello_glyph': None, 'color': (200, 40, 40)},
    {'lang': 'VIETNAMESE', 'native': 'TIENG VIET',  'text': 'XIN CHAO THE GIOI',
     'name_glyph': None, 'hello_glyph': None, 'color': (200, 60, 40)},
    {'lang': 'INDONESIAN', 'native': 'BAHASA INDONESIA', 'text': 'HALO DUNIA',
     'name_glyph': None, 'hello_glyph': None, 'color': (200, 40, 40)},
    {'lang': 'TAGALOG',    'native': None,           'text': 'KAMUSTA MUNDO',
     'name_glyph': None, 'hello_glyph': None, 'color': (40, 80, 180)},
    {'lang': 'MALAY',      'native': 'BAHASA MELAYU','text': 'HAI DUNIA',
     'name_glyph': None, 'hello_glyph': None, 'color': (220, 180, 40)},
    {'lang': 'SWAHILI',    'native': 'KISWAHILI',   'text': 'JAMBO DUNIA',
     'name_glyph': None, 'hello_glyph': None, 'color': (40, 180, 60)},
    {'lang': 'HAUSA',      'native': None,           'text': 'SANNU DUNIYA',
     'name_glyph': None, 'hello_glyph': None, 'color': (120, 180, 40)},
    {'lang': 'IGBO',       'native': None,           'text': 'NDEWO UWA',
     'name_glyph': None, 'hello_glyph': None, 'color': (80, 200, 80)},
    {'lang': 'YORUBA',     'native': None,           'text': 'BAWO NI AIYE',
     'name_glyph': None, 'hello_glyph': None, 'color': (100, 180, 60)},
    {'lang': 'ZULU',       'native': 'ISIZULU',     'text': 'SAWUBONA MHLABA',
     'name_glyph': None, 'hello_glyph': None, 'color': (200, 120, 40)},
    {'lang': 'HAWAIIAN',   'native': 'OLELO HAWAII','text': 'ALOHA HONUA',
     'name_glyph': None, 'hello_glyph': None, 'color': (80, 200, 180)},
    {'lang': 'MAORI',      'native': 'TE REO MAORI','text': 'KIA ORA TE AO',
     'name_glyph': None, 'hello_glyph': None, 'color': (60, 160, 60)},
    {'lang': 'NAVAJO',     'native': 'DINE BIZAAD', 'text': "YA'AT'EEH",
     'name_glyph': None, 'hello_glyph': None, 'color': (180, 100, 40)},
    {'lang': 'QUECHUA',    'native': 'RUNA SIMI',   'text': 'ALLILLANCHU',
     'name_glyph': None, 'hello_glyph': None, 'color': (180, 80, 40)},
    {'lang': 'GUARANI',    'native': "AVANE'E",     'text': "MBA'EICHAPA",
     'name_glyph': None, 'hello_glyph': None, 'color': (120, 180, 60)},
    {'lang': 'FINNISH',    'native': 'SUOMI',       'text': 'HEI MAAILMA',
     'name_glyph': None, 'hello_glyph': None, 'color': (180, 200, 240)},
    {'lang': 'HUNGARIAN',  'native': 'MAGYAR',      'text': 'HELLO VILAG',
     'name_glyph': None, 'hello_glyph': None, 'color': (180, 60, 40)},
    {'lang': 'WELSH',      'native': 'CYMRAEG',     'text': 'HELO BYD',
     'name_glyph': None, 'hello_glyph': None, 'color': (180, 40, 60)},
    {'lang': 'IRISH',      'native': 'GAEILGE',     'text': 'DIA DUIT',
     'name_glyph': None, 'hello_glyph': None, 'color': (40, 160, 80)},
    {'lang': 'BASQUE',     'native': 'EUSKARA',     'text': 'KAIXO MUNDUA',
     'name_glyph': None, 'hello_glyph': None, 'color': (180, 40, 40)},
    {'lang': 'LATIN',      'native': 'LATINA',      'text': 'SALVE MUNDE',
     'name_glyph': None, 'hello_glyph': None, 'color': (180, 160, 80)},
    {'lang': 'ESPERANTO',  'native': None,           'text': 'SALUTON MONDO',
     'name_glyph': None, 'hello_glyph': None, 'color': (80, 180, 80)},
    {'lang': 'ROMANIAN',   'native': 'ROMANA',       'text': 'SALUT LUME',
     'name_glyph': None, 'hello_glyph': None, 'color': (100, 100, 200)},
    {'lang': 'SWEDISH',    'native': 'SVENSKA',      'text': 'HEJ VARLDEN',
     'name_glyph': None, 'hello_glyph': None, 'color': (100, 160, 220)},
    {'lang': 'KURDISH',    'native': 'KURDI',        'text': 'SLAV CIHAN',
     'name_glyph': None, 'hello_glyph': None, 'color': (180, 140, 100)},
    {'lang': 'UZBEK',      'native': "O'ZBEK",       'text': 'SALOM DUNYO',
     'name_glyph': None, 'hello_glyph': None, 'color': (60, 160, 160)},
    {'lang': 'SOMALI',     'native': 'SOOMAALI',     'text': 'SALAAN DUNIDA',
     'name_glyph': None, 'hello_glyph': None, 'color': (160, 180, 80)},

    # ── Non-Latin scripts ──────────────────────────────────────
    {'lang': 'MANDARIN',   'native': None,           'text': 'NI HAO SHIJIE',
     'name_glyph': G_ZH_NAME, 'hello_glyph': G_ZH_HELLO, 'color': (220, 40, 40)},
    {'lang': 'CANTONESE',  'native': None,           'text': 'NEI HOU SAI GAAI',
     'name_glyph': G_YUE_NAME, 'hello_glyph': G_ZH_HELLO, 'color': (220, 80, 60)},
    {'lang': 'JAPANESE',   'native': None,           'text': 'KONNICHIWA',
     'name_glyph': G_JP_NAME, 'hello_glyph': G_JP_HELLO, 'color': (220, 50, 80)},
    {'lang': 'KOREAN',     'native': None,           'text': 'ANNYEONG SEGYE',
     'name_glyph': G_KR_NAME, 'hello_glyph': G_KR_HELLO, 'color': (60, 100, 200)},
    {'lang': 'RUSSIAN',    'native': None,           'text': 'PRIVET MIR',
     'name_glyph': G_RU_NAME, 'hello_glyph': G_RU_HELLO, 'color': (60, 130, 200)},
    {'lang': 'UKRAINIAN',  'native': None,           'text': 'PRYVIT SVITE',
     'name_glyph': G_UK_NAME, 'hello_glyph': G_UK_HELLO, 'color': (50, 120, 200)},
    {'lang': 'GREEK',      'native': None,           'text': 'YEIA SOU KOSME',
     'name_glyph': G_EL_NAME, 'hello_glyph': G_EL_HELLO, 'color': (80, 140, 220)},
    {'lang': 'ARABIC',     'native': None,           'text': 'MARHABA',
     'name_glyph': G_AR_NAME, 'hello_glyph': G_AR_HELLO, 'color': (80, 170, 170)},
    {'lang': 'HEBREW',     'native': None,           'text': 'SHALOM OLAM',
     'name_glyph': G_HE_NAME, 'hello_glyph': G_HE_HELLO, 'color': (60, 100, 200)},
    {'lang': 'PERSIAN',    'native': None,           'text': 'SALAM DONYA',
     'name_glyph': G_FA_NAME, 'hello_glyph': G_SALAM, 'color': (80, 180, 120)},
    {'lang': 'HINDI',      'native': None,           'text': 'NAMASTE DUNIYA',
     'name_glyph': G_HI_NAME, 'hello_glyph': G_HI_HELLO, 'color': (220, 100, 140)},
    {'lang': 'PUNJABI',    'native': None,           'text': 'SAT SRI AKAL',
     'name_glyph': G_PA_NAME, 'hello_glyph': G_PA_HELLO, 'color': (210, 170, 50)},
    {'lang': 'BENGALI',    'native': None,           'text': 'NAMASKAR',
     'name_glyph': G_BN_NAME, 'hello_glyph': G_BN_HELLO, 'color': (40, 140, 60)},
    {'lang': 'URDU',       'native': None,           'text': 'SALAM DUNYA',
     'name_glyph': G_UR_NAME, 'hello_glyph': G_SALAM, 'color': (120, 130, 200)},
    {'lang': 'THAI',       'native': None,           'text': 'SAWASDEE',
     'name_glyph': G_TH_NAME, 'hello_glyph': G_TH_HELLO, 'color': (180, 60, 160)},
    {'lang': 'AMHARIC',    'native': None,           'text': 'SELAM ALEM',
     'name_glyph': G_AM_NAME, 'hello_glyph': G_AM_HELLO, 'color': (60, 180, 40)},
    {'lang': 'ARMENIAN',   'native': None,           'text': 'BAREV ASHKHARH',
     'name_glyph': G_HY_NAME, 'hello_glyph': G_HY_HELLO, 'color': (200, 120, 60)},
    {'lang': 'GEORGIAN',   'native': None,           'text': 'GAMARJOBA',
     'name_glyph': G_KA_NAME, 'hello_glyph': G_KA_HELLO, 'color': (160, 80, 40)},
    {'lang': 'TAMIL',      'native': None,           'text': 'VANAKKAM',
     'name_glyph': G_TA_NAME, 'hello_glyph': G_TA_HELLO, 'color': (200, 100, 40)},
    {'lang': 'TELUGU',     'native': None,           'text': 'NAMASKARAM',
     'name_glyph': G_TE_NAME, 'hello_glyph': G_TE_HELLO, 'color': (180, 120, 200)},
    {'lang': 'MARATHI',    'native': None,           'text': 'NAMASKAR',
     'name_glyph': G_MR_NAME, 'hello_glyph': G_MR_HELLO, 'color': (200, 80, 100)},
    {'lang': 'MALAYALAM',  'native': None,           'text': 'NAMASKARAM',
     'name_glyph': G_ML_NAME, 'hello_glyph': G_ML_HELLO, 'color': (100, 160, 200)},
    {'lang': 'ODIA',       'native': None,           'text': 'NAMASKAR',
     'name_glyph': G_OR_NAME, 'hello_glyph': G_OR_HELLO, 'color': (180, 100, 160)},
    {'lang': 'NEPALI',     'native': None,           'text': 'NAMASTE',
     'name_glyph': G_NE_NAME, 'hello_glyph': G_NE_HELLO, 'color': (160, 80, 80)},
    {'lang': 'SINHALA',    'native': None,           'text': 'AYUBOWAN',
     'name_glyph': G_SI_NAME, 'hello_glyph': G_SI_HELLO, 'color': (180, 120, 60)},
    {'lang': 'BURMESE',    'native': None,           'text': 'MINGALABA',
     'name_glyph': G_MY_NAME, 'hello_glyph': G_MY_HELLO, 'color': (200, 160, 60)},
    {'lang': 'KHMER',      'native': None,           'text': 'SUOSTEI',
     'name_glyph': G_KM_NAME, 'hello_glyph': G_KM_HELLO, 'color': (200, 140, 80)},
    {'lang': 'LAO',        'native': None,           'text': 'SABAIDEE',
     'name_glyph': G_LO_NAME, 'hello_glyph': G_LO_HELLO, 'color': (120, 180, 140)},
    {'lang': 'TIBETAN',    'native': None,           'text': 'TASHI DELEK',
     'name_glyph': G_BO_NAME, 'hello_glyph': G_BO_HELLO, 'color': (140, 120, 200)},
    {'lang': 'MONGOLIAN',  'native': None,           'text': 'SAIN BAINA UU',
     'name_glyph': G_MN_NAME, 'hello_glyph': G_MN_HELLO, 'color': (100, 140, 180)},
    {'lang': 'JAVANESE',   'native': None,           'text': 'SUGENG RAWUH',
     'name_glyph': G_JV_NAME, 'hello_glyph': G_JV_HELLO, 'color': (160, 140, 60)},
    {'lang': 'PASHTO',     'native': None,           'text': 'SALAM',
     'name_glyph': G_PS_NAME, 'hello_glyph': G_PS_HELLO, 'color': (140, 160, 120)},
]

NUM_GREETINGS = len(GREETINGS)

# Layout constants
SCROLL_SPEED = 15  # px/s
MAX_LINE_CHARS = 14  # max chars on one centered line


def _split_two_lines(text):
    """Split text at a word boundary into two lines, each <= 14 chars."""
    words = text.split()
    line1 = ""
    line2 = ""
    for w in words:
        candidate = (line1 + " " + w).strip() if line1 else w
        if len(candidate) <= MAX_LINE_CHARS:
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
        self.index = random.randint(0, NUM_GREETINGS - 1)
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
            self._draw_entry(self.prev_index, fade_out)

        # Draw current entry fading in
        self._draw_entry(self.index, fade_in)

        # Footer: position indicator
        pos_text = "%d/%d" % (self.index + 1, NUM_GREETINGS)
        d.draw_text_small(2, 59, pos_text, (100, 100, 100))

        # Overlay
        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            c = int(220 * alpha)
            ow = len(self.overlay_text) * 4
            ox = max(0, (64 - ow) // 2)
            d.draw_text_small(ox, 50, self.overlay_text, (c, c, c))

    def _draw_entry(self, idx, alpha):
        d = self.display
        entry = GREETINGS[idx]
        lang = entry['lang']
        text = entry['text']
        r, g, b = entry['color']
        native = entry.get('native')
        name_glyph = entry.get('name_glyph')
        hello_glyph = entry.get('hello_glyph')

        # Alpha-scaled colors
        color = (int(r * alpha), int(g * alpha), int(b * alpha))
        dim = (int(r * 0.3 * alpha), int(g * 0.3 * alpha), int(b * 0.3 * alpha))

        has_glyphs = name_glyph is not None

        # ── Layer 1: English name (always) ──
        lang_w = len(lang) * 4
        lang_x = max(0, (64 - lang_w) // 2)
        d.draw_text_small(lang_x, 2, lang, color)

        # ── Layer 2: Native name ──
        if has_glyphs:
            # Non-Latin: pixel art glyph centered in y=10..19
            self._draw_glyph(name_glyph, 10, 19, color)
        elif native:
            # Latin script: native name as text at y=12
            nw = len(native) * 4
            nx = max(0, (64 - nw) // 2)
            d.draw_text_small(nx, 12, native, color)

        # ── Separator line at y=22 ──
        for x in range(64):
            d.set_pixel(x, 22, dim)

        # ── Layers 3 & 4: Greeting ──
        if has_glyphs:
            # Layer 3: Romanized greeting text at y=25
            self._draw_text_centered(text, 25, color)
            # Layer 4: Native greeting glyph centered in y=34..43
            if hello_glyph:
                self._draw_glyph(hello_glyph, 34, 43, color)
        else:
            # Latin script: greeting text centered in y=28 area
            self._draw_text_centered(text, 30, color)

    def _draw_text_centered(self, text, y, color):
        """Draw text centered, splitting to two lines if needed."""
        d = self.display
        if len(text) <= MAX_LINE_CHARS:
            tw = len(text) * 4
            tx = max(0, (64 - tw) // 2)
            d.draw_text_small(tx, y, text, color)
        else:
            l1, l2 = _split_two_lines(text)
            w1 = len(l1) * 4
            w2 = len(l2) * 4
            d.draw_text_small(max(0, (64 - w1) // 2), y, l1, color)
            d.draw_text_small(max(0, (64 - w2) // 2), y + 7, l2, color)

    def _draw_glyph(self, glyph, y_top, y_bot, color):
        """Draw pixel-art glyph centered horizontally and vertically."""
        if not glyph:
            return
        d = self.display
        xs = [p[0] for p in glyph]
        ys = [p[1] for p in glyph]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        gw = max_x - min_x + 1
        gh = max_y - min_y + 1
        ox = (64 - gw) // 2 - min_x
        oy = y_top + ((y_bot - y_top + 1) - gh) // 2 - min_y
        for dx, dy in glyph:
            px = ox + dx
            py = oy + dy
            if 0 <= px < 64 and 0 <= py < 64:
                d.set_pixel(px, py, color)
