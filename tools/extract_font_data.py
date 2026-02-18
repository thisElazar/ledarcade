#!/usr/bin/env python3
"""
Extract real glyph data from system fonts for Scripts and Language visuals.

Part A: Outline extraction via fontTools → stroke data for scripts.py
Part B: Bitmap rendering via Pillow → _bmp() data for language.py

Usage:
    python3 tools/extract_font_data.py scripts   # Generate scripts.py character data
    python3 tools/extract_font_data.py language   # Generate language.py bitmap data
    python3 tools/extract_font_data.py both       # Generate both
"""

import math
import sys
import unicodedata
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
from PIL import Image, ImageFont, ImageDraw

# ── Target drawing area (matches scripts.py PAPER constants) ────────
PAPER_X0, PAPER_Y0 = 10, 14
PAPER_X1, PAPER_Y1 = 54, 56
# Inset by 2px for margin inside the paper
DRAW_X0 = PAPER_X0 + 2
DRAW_Y0 = PAPER_Y0 + 2
DRAW_X1 = PAPER_X1 - 2
DRAW_Y1 = PAPER_Y1 - 2
DRAW_W = DRAW_X1 - DRAW_X0
DRAW_H = DRAW_Y1 - DRAW_Y0

# ── Font paths ──────────────────────────────────────────────────────
SUPP = '/System/Library/Fonts/Supplemental'
SYS = '/System/Library/Fonts'

FONTS = {
    'arial_unicode': f'{SUPP}/Arial Unicode.ttf',
    'geneva': f'{SYS}/Geneva.ttf',
    'apple_braille': f'{SYS}/Apple Braille.ttf',
    'phoenician': f'{SUPP}/NotoSansPhoenician-Regular.ttf',
    'cuneiform': f'{SUPP}/NotoSansCuneiform-Regular.ttf',
    'hieroglyphs': f'{SUPP}/NotoSansEgyptianHieroglyphs-Regular.ttf',
    'linear_b': f'{SUPP}/NotoSansLinearB-Regular.ttf',
    'nko': f'{SUPP}/NotoSansNKo-Regular.ttf',
    'vai': f'{SUPP}/NotoSansVai-Regular.ttf',
    'mongolian': f'{SUPP}/NotoSansMongolian-Regular.ttf',
    'tagalog': f'{SUPP}/NotoSansTagalog-Regular.ttf',
    'myanmar': f'{SYS}/NotoSerifMyanmar.ttc',
    'kefa': f'{SUPP}/Kefa.ttc',
    'khmer': f'{SUPP}/Khmer Sangam MN.ttf',
    'sinhala': f'{SUPP}/Sinhala Sangam MN.ttc',
    'cherokee': f'{SUPP}/PlantagenetCherokee.ttf',
    'canadian': f'{SUPP}/NotoSansCanadianAboriginal-Regular.otf',
    'tifinagh': f'{SUPP}/NotoSansTifinagh-Regular.otf',
    'armenian': f'{SYS}/NotoSansArmenian.ttc',
    'kannada_noto': f'{SYS}/NotoSansKannada.ttc',
    'javanese': f'{SUPP}/NotoSansJavanese-Regular.otf',
    'devanagari': f'{SUPP}/Devanagari Sangam MN.ttc',
    'bengali': f'{SUPP}/Bangla Sangam MN.ttc',
    'tamil': f'{SUPP}/Tamil Sangam MN.ttc',
    'telugu': f'{SUPP}/Telugu Sangam MN.ttc',
    'kannada': f'{SUPP}/Kannada Sangam MN.ttc',
    'malayalam': f'{SUPP}/Malayalam Sangam MN.ttc',
    'gujarati': f'{SUPP}/Gujarati Sangam MN.ttc',
    'gurmukhi': f'{SUPP}/Gurmukhi Sangam MN.ttc',
    'sinhala_mn': f'{SUPP}/Sinhala MN.ttc',
    'lao': f'{SUPP}/Lao Sangam MN.ttf',
    'myanmar_mn': f'{SUPP}/Myanmar Sangam MN.ttc',
    'tibetan': f'{SUPP}/Kailasa.ttc',
    'thai': f'{SUPP}/Ayuthaya.ttf',
    'sf_arabic': f'{SYS}/SFArabic.ttf',
    'sf_hebrew': f'{SYS}/SFHebrew.ttf',
    'sf_georgian': f'{SYS}/SFGeorgian.ttf',
    'sf_armenian': f'{SYS}/SFArmenian.ttf',
    'oriya': f'{SUPP}/Oriya Sangam MN.ttc',
}


# ═══════════════════════════════════════════════════════════════════
# PART A: Scripts outline extraction
# ═══════════════════════════════════════════════════════════════════

# ── Per-script definitions ──────────────────────────────────────────
# Each script: font_key, codepoints list, origin string, ink/paper colors

def _latin_codepoints():
    return list(range(0x0041, 0x005B)) + list(range(0x0061, 0x007B))  # A-Z, a-z

def _greek_codepoints():
    return list(range(0x0391, 0x03AA)) + list(range(0x03B1, 0x03CA))  # Α-Ω, α-ω (skip gaps)

def _cyrillic_codepoints():
    return list(range(0x0410, 0x0450))  # А-я

def _hebrew_codepoints():
    return list(range(0x05D0, 0x05EB))  # א-ת

def _arabic_codepoints():
    return list(range(0x0621, 0x063B)) + list(range(0x0641, 0x064B))  # Basic Arabic letters

def _devanagari_codepoints():
    return list(range(0x0905, 0x093A))  # अ-ह vowels + consonants

def _bengali_codepoints():
    return list(range(0x0985, 0x09B0)) + [0x09B2] + list(range(0x09B6, 0x09BA))

def _gujarati_codepoints():
    return list(range(0x0A85, 0x0A8E)) + list(range(0x0A8F, 0x0A92)) + \
           list(range(0x0A93, 0x0AB0)) + [0x0AB2, 0x0AB3] + list(range(0x0AB5, 0x0ABA))

def _gurmukhi_codepoints():
    return list(range(0x0A05, 0x0A0B)) + list(range(0x0A0F, 0x0A11)) + \
           list(range(0x0A13, 0x0A29)) + list(range(0x0A2A, 0x0A31)) + \
           list(range(0x0A32, 0x0A34)) + list(range(0x0A35, 0x0A37)) + \
           list(range(0x0A38, 0x0A3A))

def _tamil_codepoints():
    return [0x0B85, 0x0B86, 0x0B87, 0x0B88, 0x0B89, 0x0B8A, 0x0B8E, 0x0B8F, 0x0B90,
            0x0B92, 0x0B93, 0x0B94, 0x0B95, 0x0B99, 0x0B9A, 0x0B9C, 0x0B9E, 0x0B9F,
            0x0BA3, 0x0BA4, 0x0BA8, 0x0BA9, 0x0BAA, 0x0BAE, 0x0BAF, 0x0BB0, 0x0BB1,
            0x0BB2, 0x0BB3, 0x0BB5]

def _telugu_codepoints():
    return list(range(0x0C05, 0x0C0D)) + list(range(0x0C0E, 0x0C11)) + \
           list(range(0x0C12, 0x0C29)) + list(range(0x0C2A, 0x0C3A))

def _kannada_codepoints():
    return list(range(0x0C85, 0x0C8D)) + list(range(0x0C8E, 0x0C91)) + \
           list(range(0x0C92, 0x0CA9)) + list(range(0x0CAA, 0x0CB4)) + \
           list(range(0x0CB5, 0x0CBA))

def _malayalam_codepoints():
    return list(range(0x0D05, 0x0D0D)) + list(range(0x0D0E, 0x0D11)) + \
           list(range(0x0D12, 0x0D3A))

def _sinhala_codepoints():
    return list(range(0x0D85, 0x0D97)) + list(range(0x0D9A, 0x0DB2)) + \
           list(range(0x0DB3, 0x0DBC)) + [0x0DBD]

def _thai_codepoints():
    return list(range(0x0E01, 0x0E2F))  # ก-ฮ consonants

def _lao_codepoints():
    return [0x0E81, 0x0E82, 0x0E84, 0x0E87, 0x0E88, 0x0E8A, 0x0E8D,
            0x0E94, 0x0E95, 0x0E96, 0x0E97, 0x0E99, 0x0E9A, 0x0E9B,
            0x0E9C, 0x0E9D, 0x0E9E, 0x0E9F, 0x0EA1, 0x0EA2, 0x0EA3,
            0x0EA5, 0x0EA7, 0x0EAA, 0x0EAB, 0x0EAD, 0x0EAE]

def _tibetan_codepoints():
    return list(range(0x0F40, 0x0F48)) + list(range(0x0F49, 0x0F5E))

def _georgian_codepoints():
    return list(range(0x10D0, 0x10F1))  # ა-ჰ

def _armenian_codepoints():
    return list(range(0x0531, 0x0557))  # Ա-Ֆ

def _korean_hangul_codepoints():
    return list(range(0x3131, 0x3164))  # ㄱ-ㅎ, ㅏ-ㅣ jamo

def _hiragana_codepoints():
    return list(range(0x3041, 0x3094))  # ぁ-ゔ (skip gaps naturally)

def _katakana_codepoints():
    return list(range(0x30A1, 0x30F7))  # ァ-ヶ

def _cjk_common():
    """25 basic/common CJK characters."""
    return [0x5C71, 0x6C34, 0x706B, 0x4EBA, 0x6728, 0x65E5, 0x6708, 0x5929,
            0x5730, 0x98A8, 0x82B1, 0x9CE5, 0x9B5A, 0x99AC, 0x7530, 0x53E3,
            0x624B, 0x8DB3, 0x76EE, 0x8033, 0x5FC3, 0x91D1, 0x571F, 0x77F3, 0x96E8]

def _phoenician_codepoints():
    return list(range(0x10900, 0x10916))  # 22 letters

def _runic_codepoints():
    return list(range(0x16A0, 0x16B8))  # Elder Futhark subset

def _ogham_codepoints():
    return list(range(0x1681, 0x1695))  # Ogham letters

def _ethiopic_codepoints():
    return list(range(0x1200, 0x1221))  # First 33 Ethiopic syllables

def _cherokee_codepoints():
    # Representative subset ~50 characters
    return list(range(0x13A0, 0x13D4))

def _inuktitut_codepoints():
    # Canadian Syllabics subset
    return [0x1401, 0x1402, 0x1403, 0x1404, 0x1405, 0x1406,
            0x140A, 0x140B, 0x140C, 0x140D, 0x1410, 0x1411,
            0x1412, 0x1413, 0x1414, 0x1431, 0x1432, 0x1433,
            0x1434, 0x1438, 0x1439, 0x143A, 0x143B, 0x1450,
            0x1451, 0x1452, 0x1453, 0x1455, 0x1456, 0x1457]

def _nko_codepoints():
    return list(range(0x07C0, 0x07DB))  # N'Ko digits + letters

def _vai_codepoints():
    return list(range(0xA500, 0xA52A))  # First ~42 Vai syllables

def _mongolian_codepoints():
    return list(range(0x1820, 0x1843))  # Mongolian letters

def _baybayin_codepoints():
    return list(range(0x1700, 0x1712))  # Baybayin

def _hieroglyph_codepoints():
    return list(range(0x13000, 0x13014))  # First 20 hieroglyphs

def _cuneiform_codepoints():
    return list(range(0x12000, 0x12014))  # First 20 cuneiform signs

def _linear_b_codepoints():
    return list(range(0x10000, 0x10014))  # First 20 Linear B syllables

def _braille_codepoints():
    return list(range(0x2801, 0x281B))  # Braille patterns for a-z

def _tifinagh_codepoints():
    return list(range(0x2D30, 0x2D56))  # Basic Tifinagh letters

def _burmese_codepoints():
    return list(range(0x1000, 0x1021))  # Myanmar consonants

def _khmer_codepoints():
    return list(range(0x1780, 0x17A3))  # Khmer consonants


# ── Ink/Paper color presets (matching scripts.py) ───────────────────
SCRIPT_PRESETS = {
    'LATIN':      {'ink': (30, 30, 80),   'paper': (230, 228, 220), 'origin': 'PHOENICIAN ADAPTATION ~700 BC'},
    'PHOENICIAN': {'ink': (90, 50, 25),   'paper': (210, 190, 155), 'origin': 'BYBLOS ~1050 BC'},
    'HEBREW':     {'ink': (30, 25, 20),   'paper': (225, 220, 200), 'origin': 'PALEO-HEBREW ~1000 BC'},
    'ARABIC':     {'ink': (30, 25, 20),   'paper': (225, 215, 190), 'origin': 'NABATAEAN SCRIPT ~400 AD'},
    'GREEK':      {'ink': (25, 40, 120),  'paper': (225, 220, 210), 'origin': 'ADAPTED FROM PHOENICIAN ~800 BC'},
    'CYRILLIC':   {'ink': (20, 20, 20),   'paper': (225, 225, 230), 'origin': 'SAINTS CYRIL & METHODIUS ~900 AD'},
    'RUNIC':      {'ink': (20, 20, 20),   'paper': (200, 190, 170), 'origin': 'ELDER FUTHARK ~150 AD'},
    'OGHAM':      {'ink': (30, 40, 25),   'paper': (190, 185, 165), 'origin': 'IRELAND ~400 AD'},
    'ARMENIAN':   {'ink': (60, 30, 20),   'paper': (225, 218, 200), 'origin': 'MESROP MASHTOTS ~405 AD'},
    'GEORGIAN':   {'ink': (40, 30, 20),   'paper': (225, 215, 200), 'origin': 'ASOMTAVRULI ~430 AD'},
    'DEVANAGARI': {'ink': (160, 60, 20),  'paper': (230, 220, 200), 'origin': 'BRAHMI DESCENDANT ~700 AD'},
    'GUJARATI':   {'ink': (160, 50, 20),  'paper': (230, 222, 200), 'origin': 'DEVANAGARI VARIANT ~1600 AD'},
    'GURMUKHI':   {'ink': (30, 40, 120),  'paper': (225, 225, 215), 'origin': 'GURU ANGAD ~1540 AD'},
    'BENGALI':    {'ink': (140, 40, 25),  'paper': (230, 225, 205), 'origin': 'EASTERN NAGARI ~1100 AD'},
    'TAMIL':      {'ink': (20, 60, 20),   'paper': (225, 220, 210), 'origin': 'TAMIL BRAHMI ~300 BC'},
    'TELUGU':     {'ink': (30, 60, 130),  'paper': (230, 225, 210), 'origin': 'BHATTIPROLU ~400 AD'},
    'KANNADA':    {'ink': (140, 40, 20),  'paper': (228, 222, 205), 'origin': 'KADAMBA ~500 AD'},
    'MALAYALAM':  {'ink': (20, 50, 20),   'paper': (225, 225, 210), 'origin': 'GRANTHA DESCENDANT ~830 AD'},
    'SINHALA':    {'ink': (120, 40, 30),  'paper': (228, 225, 210), 'origin': 'BRAHMI DESCENDANT ~300 BC'},
    'TIBETAN':    {'ink': (130, 30, 30),  'paper': (225, 220, 200), 'origin': 'THONMI SAMBHOTA ~650 AD'},
    'THAI':       {'ink': (80, 30, 100),  'paper': (230, 225, 215), 'origin': 'KHMER ADAPTATION ~1283 AD'},
    'LAO':        {'ink': (80, 30, 100),  'paper': (228, 225, 215), 'origin': 'THAI RELATED ~1400 AD'},
    'BURMESE':    {'ink': (30, 30, 30),   'paper': (230, 225, 200), 'origin': 'MON ADAPTATION ~1050 AD'},
    'KHMER':      {'ink': (60, 40, 20),   'paper': (225, 218, 195), 'origin': 'PALLAVA GRANTHA ~600 AD'},
    'KOREAN':     {'ink': (20, 30, 80),   'paper': (225, 225, 230), 'origin': 'KING SEJONG ~1443 AD'},
    'HIRAGANA':   {'ink': (20, 20, 20),   'paper': (230, 225, 215), 'origin': 'HEIAN PERIOD ~800 AD'},
    'KATAKANA':   {'ink': (20, 20, 20),   'paper': (230, 225, 215), 'origin': 'HEIAN PERIOD ~800 AD'},
    'CHINESE':    {'ink': (180, 30, 20),  'paper': (230, 220, 190), 'origin': 'ORACLE BONE ~1200 BC', 'thick': True},
    'ETHIOPIC':   {'ink': (40, 30, 20),   'paper': (220, 210, 185), 'origin': "GE'EZ SCRIPT ~500 BC"},
    'TIFINAGH':   {'ink': (50, 35, 100),  'paper': (215, 205, 180), 'origin': 'LIBYCO-BERBER ~200 BC'},
    'NKO':        {'ink': (50, 30, 20),   'paper': (225, 215, 185), 'origin': "SOLOMANA KANTE ~1949 AD"},
    'VAI':        {'ink': (40, 30, 20),   'paper': (225, 215, 195), 'origin': 'MƆMƆLU DUWALU BUKƐLƐ ~1833 AD'},
    'CHEROKEE':   {'ink': (120, 60, 30),  'paper': (220, 210, 185), 'origin': 'SEQUOYAH ~1821 AD'},
    'INUKTITUT':  {'ink': (80, 100, 160), 'paper': (225, 230, 240), 'origin': 'JAMES EVANS ~1840 AD'},
    'MONGOLIAN':  {'ink': (30, 30, 30),   'paper': (220, 215, 200), 'origin': 'UYGHUR ADAPTATION ~1204 AD'},
    'BAYBAYIN':   {'ink': (80, 40, 20),   'paper': (220, 210, 185), 'origin': 'BRAHMI DESCENDANT ~1300 AD'},
    'HIEROGLYPH': {'ink': (40, 100, 60),  'paper': (210, 195, 160), 'origin': 'ANCIENT EGYPT ~3200 BC'},
    'CUNEIFORM':  {'ink': (50, 40, 30),   'paper': (180, 160, 130), 'origin': 'SUMER ~3400 BC'},
    'LINEAR_B':   {'ink': (50, 40, 100),  'paper': (215, 210, 195), 'origin': 'MYCENAEAN GREECE ~1450 BC'},
    'BRAILLE':    {'ink': (40, 40, 40),   'paper': (225, 225, 225), 'origin': 'LOUIS BRAILLE ~1824 AD'},
}

# Map script name to (font_key, codepoint_function, optional font_number for .ttc)
SCRIPT_FONT_MAP = {
    'LATIN':      ('arial_unicode', _latin_codepoints, None),
    'PHOENICIAN': ('phoenician', _phoenician_codepoints, None),
    'HEBREW':     ('arial_unicode', _hebrew_codepoints, None),
    'ARABIC':     ('arial_unicode', _arabic_codepoints, None),
    'GREEK':      ('arial_unicode', _greek_codepoints, None),
    'CYRILLIC':   ('arial_unicode', _cyrillic_codepoints, None),
    'RUNIC':      ('geneva', _runic_codepoints, None),
    'OGHAM':      ('geneva', _ogham_codepoints, None),
    'ARMENIAN':   ('arial_unicode', _armenian_codepoints, None),
    'GEORGIAN':   ('arial_unicode', _georgian_codepoints, None),
    'DEVANAGARI': ('arial_unicode', _devanagari_codepoints, None),
    'GUJARATI':   ('arial_unicode', _gujarati_codepoints, None),
    'GURMUKHI':   ('arial_unicode', _gurmukhi_codepoints, None),
    'BENGALI':    ('arial_unicode', _bengali_codepoints, None),
    'TAMIL':      ('arial_unicode', _tamil_codepoints, None),
    'TELUGU':     ('arial_unicode', _telugu_codepoints, None),
    'KANNADA':    ('arial_unicode', _kannada_codepoints, None),
    'MALAYALAM':  ('arial_unicode', _malayalam_codepoints, None),
    'SINHALA':    ('sinhala', _sinhala_codepoints, 0),
    'TIBETAN':    ('arial_unicode', _tibetan_codepoints, None),
    'THAI':       ('arial_unicode', _thai_codepoints, None),
    'LAO':        ('arial_unicode', _lao_codepoints, None),
    'BURMESE':    ('myanmar', _burmese_codepoints, 0),
    'KHMER':      ('khmer', _khmer_codepoints, None),
    'KOREAN':     ('arial_unicode', _korean_hangul_codepoints, None),
    'HIRAGANA':   ('arial_unicode', _hiragana_codepoints, None),
    'KATAKANA':   ('arial_unicode', _katakana_codepoints, None),
    'CHINESE':    ('arial_unicode', _cjk_common, None),
    'ETHIOPIC':   ('kefa', _ethiopic_codepoints, 0),
    'TIFINAGH':   ('tifinagh', _tifinagh_codepoints, None),
    'NKO':        ('nko', _nko_codepoints, None),
    'VAI':        ('vai', _vai_codepoints, None),
    'CHEROKEE':   ('cherokee', _cherokee_codepoints, None),
    'INUKTITUT':  ('canadian', _inuktitut_codepoints, None),
    'MONGOLIAN':  ('mongolian', _mongolian_codepoints, None),
    'BAYBAYIN':   ('tagalog', _baybayin_codepoints, None),
    'HIEROGLYPH': ('hieroglyphs', _hieroglyph_codepoints, None),
    'CUNEIFORM':  ('cuneiform', _cuneiform_codepoints, None),
    'LINEAR_B':   ('linear_b', _linear_b_codepoints, None),
    'BRAILLE':    ('apple_braille', _braille_codepoints, None),
}

# Family ordering for FAMILIES list in scripts.py
FAMILIES_ORDER = [
    'LATIN', 'PHOENICIAN', 'HEBREW', 'ARABIC', 'GREEK', 'CYRILLIC',
    'RUNIC', 'OGHAM', 'ARMENIAN', 'GEORGIAN',
    'DEVANAGARI', 'GUJARATI', 'GURMUKHI', 'BENGALI',
    'TAMIL', 'TELUGU', 'KANNADA', 'MALAYALAM', 'SINHALA',
    'TIBETAN', 'THAI', 'LAO', 'BURMESE', 'KHMER',
    'KOREAN', 'HIRAGANA', 'KATAKANA', 'CHINESE',
    'ETHIOPIC', 'TIFINAGH', 'NKO', 'VAI',
    'CHEROKEE', 'INUKTITUT', 'MONGOLIAN', 'BAYBAYIN',
    'HIEROGLYPH', 'CUNEIFORM', 'LINEAR_B', 'BRAILLE',
]


# ── Geometry utilities ──────────────────────────────────────────────

def _flatten_quad_bezier(p0, p1, p2, steps=4):
    """Flatten a quadratic Bezier curve to line segments."""
    pts = []
    for i in range(1, steps + 1):
        t = i / steps
        t1 = 1 - t
        x = t1*t1*p0[0] + 2*t1*t*p1[0] + t*t*p2[0]
        y = t1*t1*p0[1] + 2*t1*t*p1[1] + t*t*p2[1]
        pts.append((x, y))
    return pts


def _flatten_cubic_bezier(p0, p1, p2, p3, steps=5):
    """Flatten a cubic Bezier curve to line segments."""
    pts = []
    for i in range(1, steps + 1):
        t = i / steps
        t1 = 1 - t
        x = t1**3*p0[0] + 3*t1**2*t*p1[0] + 3*t1*t**2*p2[0] + t**3*p3[0]
        y = t1**3*p0[1] + 3*t1**2*t*p1[1] + 3*t1*t**2*p2[1] + t**3*p3[1]
        pts.append((x, y))
    return pts


def _rdp_simplify(points, tolerance=1.5):
    """Ramer-Douglas-Peucker line simplification."""
    if len(points) <= 2:
        return list(points)

    # Find point with max distance from line between first and last
    start, end = points[0], points[-1]
    max_dist = 0
    max_idx = 0

    dx = end[0] - start[0]
    dy = end[1] - start[1]
    line_len_sq = dx*dx + dy*dy

    for i in range(1, len(points) - 1):
        if line_len_sq == 0:
            dist = math.sqrt((points[i][0]-start[0])**2 + (points[i][1]-start[1])**2)
        else:
            t = ((points[i][0]-start[0])*dx + (points[i][1]-start[1])*dy) / line_len_sq
            t = max(0, min(1, t))
            proj_x = start[0] + t*dx
            proj_y = start[1] + t*dy
            dist = math.sqrt((points[i][0]-proj_x)**2 + (points[i][1]-proj_y)**2)
        if dist > max_dist:
            max_dist = dist
            max_idx = i

    if max_dist > tolerance:
        left = _rdp_simplify(points[:max_idx+1], tolerance)
        right = _rdp_simplify(points[max_idx:], tolerance)
        return left[:-1] + right
    else:
        return [start, end]


def _contours_from_recording(operations):
    """Convert recording pen operations to list of contours (point lists)."""
    contours = []
    current = []

    for op, args in operations:
        if op == 'moveTo':
            if current:
                contours.append(current)
            current = [args[0]]
        elif op == 'lineTo':
            current.append(args[0])
        elif op == 'qCurveTo':
            # TrueType quadratic: may have multiple off-curve points
            # with implied on-curve points between them
            if not current:
                continue
            start = current[-1]
            points = list(args)
            if len(points) == 2:
                # Simple quad: one off-curve, one on-curve
                current.extend(_flatten_quad_bezier(start, points[0], points[1]))
            else:
                # Multiple off-curve points with implied on-curve between them
                off_curves = points[:-1]
                on_curve_end = points[-1]
                prev = start
                for i, off in enumerate(off_curves):
                    if i < len(off_curves) - 1:
                        # Implied on-curve point
                        next_off = off_curves[i + 1]
                        implied = ((off[0] + next_off[0]) / 2, (off[1] + next_off[1]) / 2)
                        current.extend(_flatten_quad_bezier(prev, off, implied))
                        prev = implied
                    else:
                        # Last off-curve to final on-curve
                        current.extend(_flatten_quad_bezier(prev, off, on_curve_end))
                        prev = on_curve_end
        elif op == 'curveTo':
            # PostScript cubic Bezier
            if not current:
                continue
            start = current[-1]
            current.extend(_flatten_cubic_bezier(start, args[0], args[1], args[2]))
        elif op == 'closePath':
            if current and len(current) > 1:
                # Close the contour by connecting back to start
                if current[-1] != current[0]:
                    current.append(current[0])
                contours.append(current)
                current = []
        elif op == 'endPath':
            if current:
                contours.append(current)
                current = []

    if current:
        contours.append(current)
    return contours


def _scale_contours(contours, target_x0, target_y0, target_w, target_h):
    """Scale contours to fit within target bounding box, preserving aspect ratio."""
    if not contours:
        return contours

    # Find bounding box of all points
    all_pts = [p for c in contours for p in c]
    if not all_pts:
        return contours

    min_x = min(p[0] for p in all_pts)
    max_x = max(p[0] for p in all_pts)
    min_y = min(p[1] for p in all_pts)
    max_y = max(p[1] for p in all_pts)

    src_w = max_x - min_x
    src_h = max_y - min_y

    if src_w == 0 and src_h == 0:
        return contours

    # Scale to fit, preserving aspect ratio
    if src_w == 0:
        scale = target_h / src_h
    elif src_h == 0:
        scale = target_w / src_w
    else:
        scale = min(target_w / src_w, target_h / src_h)

    # Center in target area
    scaled_w = src_w * scale
    scaled_h = src_h * scale
    off_x = target_x0 + (target_w - scaled_w) / 2
    off_y = target_y0 + (target_h - scaled_h) / 2

    result = []
    for contour in contours:
        scaled = []
        for x, y in contour:
            sx = off_x + (x - min_x) * scale
            # Font Y is upward, display Y is downward → flip
            sy = off_y + (max_y - y) * scale
            scaled.append((round(sx), round(sy)))
        result.append(scaled)
    return result


def extract_glyph_strokes(font_path, codepoint, font_number=None):
    """Extract stroke contours for a single glyph from a font file."""
    if font_number is not None:
        font = TTFont(font_path, fontNumber=font_number)
    else:
        font = TTFont(font_path)

    cmap = font.getBestCmap()
    if codepoint not in cmap:
        font.close()
        return None

    glyph_name = cmap[codepoint]
    glyphset = font.getGlyphSet()

    if glyph_name not in glyphset:
        font.close()
        return None

    pen = DecomposingRecordingPen(glyphset)
    glyphset[glyph_name].draw(pen)
    font.close()

    contours = _contours_from_recording(pen.value)
    if not contours:
        return None

    # Scale to drawing area
    contours = _scale_contours(contours, DRAW_X0, DRAW_Y0, DRAW_W, DRAW_H)

    # Simplify each contour
    simplified = []
    for contour in contours:
        if len(contour) < 2:
            continue
        simp = _rdp_simplify(contour, tolerance=1.5)
        if len(simp) >= 2:
            simplified.append(simp)

    return simplified if simplified else None


def _get_char_name(codepoint):
    """Get a short name for a character from Unicode data."""
    try:
        name = unicodedata.name(chr(codepoint))
        # Shorten common prefixes
        for prefix in ['LATIN SMALL LETTER ', 'LATIN CAPITAL LETTER ',
                       'GREEK SMALL LETTER ', 'GREEK CAPITAL LETTER ',
                       'CYRILLIC SMALL LETTER ', 'CYRILLIC CAPITAL LETTER ',
                       'HEBREW LETTER ', 'ARABIC LETTER ',
                       'DEVANAGARI LETTER ', 'BENGALI LETTER ',
                       'GUJARATI LETTER ', 'GURMUKHI LETTER ',
                       'TAMIL LETTER ', 'TELUGU LETTER ',
                       'KANNADA LETTER ', 'MALAYALAM LETTER ',
                       'SINHALA LETTER ', 'TIBETAN LETTER ',
                       'THAI CHARACTER ', 'LAO LETTER ',
                       'MYANMAR LETTER ', 'KHMER LETTER ',
                       'HANGUL LETTER ', 'HIRAGANA LETTER ',
                       'KATAKANA LETTER ', 'ETHIOPIC SYLLABLE ',
                       'TIFINAGH LETTER ', 'NKO LETTER ', 'NKO DIGIT ',
                       'VAI SYLLABLE ', 'CHEROKEE LETTER ',
                       'CANADIAN SYLLABICS ', 'MONGOLIAN LETTER ',
                       'TAGALOG LETTER ', 'EGYPTIAN HIEROGLYPH ',
                       'CUNEIFORM SIGN ', 'LINEAR B SYLLABLE ',
                       'BRAILLE PATTERN ', 'ARMENIAN CAPITAL LETTER ',
                       'ARMENIAN SMALL LETTER ', 'GEORGIAN LETTER ',
                       'PHOENICIAN LETTER ', 'RUNIC LETTER ',
                       'OGHAM LETTER ', 'CJK UNIFIED IDEOGRAPH-']:
            if name.startswith(prefix):
                name = name[len(prefix):]
                break
        return name.upper()[:12]  # Cap length
    except ValueError:
        return f'U+{codepoint:04X}'


def _get_concept(codepoint):
    """Get a concept/meaning string for a character."""
    try:
        name = unicodedata.name(chr(codepoint))
        # For CJK, try to get meaning from the name
        if name.startswith('CJK UNIFIED IDEOGRAPH'):
            # Common CJK meanings
            cjk_meanings = {
                0x5C71: 'MOUNTAIN', 0x6C34: 'WATER', 0x706B: 'FIRE',
                0x4EBA: 'PERSON', 0x6728: 'TREE', 0x65E5: 'SUN / DAY',
                0x6708: 'MOON / MONTH', 0x5929: 'HEAVEN / SKY',
                0x5730: 'EARTH / GROUND', 0x98A8: 'WIND', 0x82B1: 'FLOWER',
                0x9CE5: 'BIRD', 0x9B5A: 'FISH', 0x99AC: 'HORSE',
                0x7530: 'FIELD', 0x53E3: 'MOUTH', 0x624B: 'HAND',
                0x8DB3: 'FOOT', 0x76EE: 'EYE', 0x8033: 'EAR',
                0x5FC3: 'HEART / MIND', 0x91D1: 'GOLD / METAL',
                0x571F: 'EARTH / SOIL', 0x77F3: 'STONE', 0x96E8: 'RAIN',
            }
            return cjk_meanings.get(codepoint, 'IDEOGRAPH')
        # For scripts with phonetic names, use the phonetic value
        return _get_char_name(codepoint)
    except ValueError:
        return f'U+{codepoint:04X}'


def extract_all_scripts():
    """Extract stroke data for all scripts. Returns list of character dicts."""
    characters = []
    font_cache = {}

    for script in FAMILIES_ORDER:
        if script not in SCRIPT_FONT_MAP:
            print(f'  SKIP {script} — no font mapping')
            continue

        font_key, cp_func, font_num = SCRIPT_FONT_MAP[script]
        font_path = FONTS[font_key]
        preset = SCRIPT_PRESETS[script]
        codepoints = cp_func()

        print(f'  {script}: {len(codepoints)} codepoints from {Path(font_path).name}')

        # Open font once per font file
        cache_key = (font_path, font_num)
        if cache_key not in font_cache:
            if font_num is not None:
                font_cache[cache_key] = TTFont(font_path, fontNumber=font_num)
            else:
                font_cache[cache_key] = TTFont(font_path)

        font = font_cache[cache_key]
        cmap = font.getBestCmap()
        glyphset = font.getGlyphSet()

        extracted = 0
        for cp in codepoints:
            if cp not in cmap:
                continue

            glyph_name = cmap[cp]
            if glyph_name not in glyphset:
                continue

            pen = DecomposingRecordingPen(glyphset)
            try:
                glyphset[glyph_name].draw(pen)
            except Exception:
                continue

            contours = _contours_from_recording(pen.value)
            if not contours:
                continue

            contours = _scale_contours(contours, DRAW_X0, DRAW_Y0, DRAW_W, DRAW_H)

            strokes = []
            for contour in contours:
                if len(contour) < 2:
                    continue
                simp = _rdp_simplify(contour, tolerance=1.5)
                if len(simp) >= 2:
                    # Convert to integer tuples
                    strokes.append([(int(x), int(y)) for x, y in simp])

            if not strokes:
                continue

            char_entry = {
                'name': _get_char_name(cp),
                'script': script,
                'concept': _get_concept(cp),
                'origin': preset['origin'],
                'ink': preset['ink'],
                'paper': preset['paper'],
                'strokes': strokes,
            }
            if preset.get('thick'):
                char_entry['thick'] = True

            characters.append(char_entry)
            extracted += 1

        print(f'    → {extracted} characters extracted')

    # Close cached fonts
    for font in font_cache.values():
        font.close()

    return characters


def format_scripts_output(characters):
    """Format extracted characters as Python source code for scripts.py."""
    lines = []

    # Group by script for readability
    current_script = None
    for ch in characters:
        if ch['script'] != current_script:
            current_script = ch['script']
            lines.append(f"    # ── {current_script} {'─' * (55 - len(current_script))}")

        lines.append('    {')
        lines.append(f"        'name': {ch['name']!r}, 'script': {ch['script']!r}, "
                     f"'concept': {ch['concept']!r},")
        lines.append(f"        'origin': {ch['origin']!r},")
        lines.append(f"        'ink': {ch['ink']!r}, 'paper': {ch['paper']!r},")
        if ch.get('thick'):
            lines.append(f"        'thick': True,")
        lines.append(f"        'strokes': [")
        for stroke in ch['strokes']:
            pts_str = ', '.join(f'({x}, {y})' for x, y in stroke)
            lines.append(f'            [{pts_str}],')
        lines.append('        ],')
        lines.append('    },')

    return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════════
# PART B: Language bitmap extraction
# ═══════════════════════════════════════════════════════════════════

# Languages that need bitmap extraction (non-Latin scripts with placeholder glyphs)
# All HELLO glyphs render "hello world" in native script.
LANGUAGE_BITMAPS = [
    # (var_name, text, font_path, font_number, comment)
    # Arabic script — "hello world" = مرحبا عالم / سلام دنیا / سلام دنیا
    ('G_AR_NAME',  'العربية',       FONTS['sf_arabic'], None, 'al-arabiyya'),
    ('G_AR_HELLO', 'مرحبا عالم',    FONTS['sf_arabic'], None, 'marhaba aalam'),
    ('G_FA_NAME',  'فارسی',         FONTS['sf_arabic'], None, 'farsi'),
    ('G_SALAM',    'سلام دنیا',     FONTS['sf_arabic'], None, 'salam donya'),
    ('G_UR_NAME',  'اردو',          FONTS['sf_arabic'], None, 'urdu'),
    ('G_PS_NAME',  'پښتو',          FONTS['sf_arabic'], None, 'pashto'),
    ('G_PS_HELLO', 'سلام نړی',      FONTS['sf_arabic'], None, 'salam nurai'),

    # Hebrew — שלום עולם
    ('G_HE_NAME',  'עברית',         FONTS['sf_hebrew'], None, 'ivrit'),
    ('G_HE_HELLO', 'שלום עולם',     FONTS['sf_hebrew'], None, 'shalom olam'),

    # Devanagari — hello world versions
    ('G_HI_NAME',  'हिन्दी',          FONTS['devanagari'], 0, 'hindi'),
    ('G_HI_HELLO', 'नमस्ते दुनिया',    FONTS['devanagari'], 0, 'namaste duniya'),
    ('G_MR_NAME',  'मराठी',          FONTS['devanagari'], 0, 'marathi'),
    ('G_MR_HELLO', 'नमस्कार जग',     FONTS['devanagari'], 0, 'namaskar jag'),
    ('G_NE_NAME',  'नेपाली',         FONTS['devanagari'], 0, 'nepali'),
    ('G_NE_HELLO', 'नमस्ते संसार',    FONTS['devanagari'], 0, 'namaste sansar'),

    # Bengali — নমস্কার পৃথিবী
    ('G_BN_NAME',  'বাংলা',         FONTS['bengali'], 0, 'bangla'),
    ('G_BN_HELLO', 'নমস্কার বিশ্ব',  FONTS['bengali'], 0, 'namaskar bishwa'),

    # Gurmukhi / Punjabi — ਸਤ ਸ੍ਰੀ ਅਕਾਲ ਦੁਨੀਆ
    ('G_PA_NAME',  'ਪੰਜਾਬੀ',        FONTS['gurmukhi'], 0, 'punjabi'),
    ('G_PA_HELLO', 'ਸਤ ਸ੍ਰੀ ਅਕਾਲ ਦੁਨੀਆ', FONTS['gurmukhi'], 0, 'sat sri akal duniya'),

    # Tamil — வணக்கம் உலகே (shorter "world" = ulake, vocative)
    ('G_TA_NAME',  'தமிழ்',         FONTS['tamil'], 0, 'tamizh'),
    ('G_TA_HELLO', 'வணக்கம் உலகே', FONTS['tamil'], 0, 'vanakkam ulake'),

    # Telugu — నమస్కారం లోకం (lokam = world, shorter than prapancham)
    ('G_TE_NAME',  'తెలుగు',        FONTS['telugu'], 0, 'telugu'),
    ('G_TE_HELLO', 'నమస్కారం లోకం', FONTS['telugu'], 0, 'namaskaram lokam'),

    # Malayalam — നമസ്കാരം ലോകം (hello world)
    ('G_ML_NAME',  'മലയാളം',        FONTS['malayalam'], 0, 'malayalam'),
    ('G_ML_HELLO', 'നമസ്കാരം',      FONTS['malayalam'], 0, 'namaskaram'),

    # Odia — ନମସ୍କାର ଦୁନିଆ
    ('G_OR_NAME',  'ଓଡ଼ିଆ',         FONTS['oriya'], 0, 'odia'),
    ('G_OR_HELLO', 'ନମସ୍କାର ଦୁନିଆ', FONTS['oriya'], 0, 'namaskar duniya'),

    # Thai — สวัสดีโลก
    ('G_TH_NAME',  'ไทย',           FONTS['thai'], None, 'thai'),
    ('G_TH_HELLO', 'สวัสดีโลก',     FONTS['thai'], None, 'sawasdee lok'),

    # Tibetan — བཀྲ་ཤིས་བདེ་ལེགས (already full greeting — tashi delek)
    ('G_BO_NAME',  'བོད་སྐད',         FONTS['tibetan'], 0, 'bodskad'),
    ('G_BO_HELLO', 'བཀྲ་ཤིས་བདེ་ལེགས', FONTS['tibetan'], 0, 'tashi delek'),

    # Khmer — សួស្តីពិភពលោក
    ('G_KM_NAME',  'ខ្មែរ',          FONTS['khmer'], None, 'khmer'),
    ('G_KM_HELLO', 'សួស្តីលោក',     FONTS['khmer'], None, 'suostei lok'),

    # Lao — ສະບາຍດີໂລກ
    ('G_LO_NAME',  'ລາວ',           FONTS['lao'], None, 'lao'),
    ('G_LO_HELLO', 'ສະບາຍດີໂລກ',   FONTS['lao'], None, 'sabaidee lok'),

    # Sinhala — ආයුබෝවන් ලෝකය
    ('G_SI_NAME',  'සිංහල',         FONTS['sinhala'], 0, 'sinhala'),
    ('G_SI_HELLO', 'ආයුබෝවන් ලෝකය', FONTS['sinhala'], 0, 'ayubowan lokaya'),

    # Burmese — မင်္ဂလာပါ ကမ္ဘာ
    ('G_MY_NAME',  'မြန်မာ',           FONTS['myanmar_mn'], 0, 'myanma'),
    ('G_MY_HELLO', 'မင်္ဂလာပါ',         FONTS['myanmar_mn'], 0, 'mingalaba'),

    # Armenian — Բարև Աշխարh
    ('G_HY_NAME',  '\u0540\u0561\u0575\u0565\u0580\u0565\u0576',   FONTS['sf_armenian'], None, 'hayeren'),
    ('G_HY_HELLO', '\u0532\u0561\u0580\u0587 \u0531\u0577\u056d\u0561\u0580\u0570', FONTS['sf_armenian'], None, 'barev ashkharh'),

    # Georgian — გამარჯობა მსოფლიო (gamarjoba msoplio = hello world)
    ('G_KA_NAME',  'ქართული',       FONTS['sf_georgian'], None, 'kartuli'),
    ('G_KA_HELLO', 'გამარჯობა სამყარო', FONTS['sf_georgian'], None, 'gamarjoba samqaro'),

    # Amharic / Ethiopic — ሰላም ዓለም
    ('G_AM_NAME',  'አማርኛ',          FONTS['kefa'], 0, 'amarnya'),
    ('G_AM_HELLO', 'ሰላም ዓለም',      FONTS['kefa'], 0, 'selam alem'),

    # Javanese
    ('G_JV_NAME',  'ꦗꦮ',             FONTS['javanese'], None, 'jawa'),
    ('G_JV_HELLO', 'ꦱꦸꦒꦼꦁ',          FONTS['javanese'], None, 'sugeng'),
]


def render_text_bitmap(text, font_path, font_number=None, max_width=60, max_height=12):
    """Render text using Pillow and return _bmp() format strings."""
    # Try multiple sizes to find best fit
    best_rows = None
    best_score = 0

    for size in [6, 7, 8, 9, 10, 11, 12, 14, 16, 18, 20]:
        try:
            if font_number is not None:
                font = ImageFont.truetype(font_path, size=size, index=font_number)
            else:
                font = ImageFont.truetype(font_path, size=size)
        except Exception:
            continue

        # Get text dimensions
        bbox = font.getbbox(text)
        if bbox is None:
            continue
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        if tw <= 0 or th <= 0:
            continue

        # Render with padding
        pad = 2
        img = Image.new('L', (tw + pad*2, th + pad*2), 0)
        draw = ImageDraw.Draw(img)
        draw.text((pad - bbox[0], pad - bbox[1]), text, font=font, fill=255)

        # Crop to content
        pixels = img.load()
        w, h = img.size
        min_x, min_y, max_x, max_y = w, h, 0, 0
        for py in range(h):
            for px in range(w):
                if pixels[px, py] > 80:  # threshold
                    min_x = min(min_x, px)
                    min_y = min(min_y, py)
                    max_x = max(max_x, px)
                    max_y = max(max_y, py)

        if max_x < min_x:
            continue

        cw = max_x - min_x + 1
        ch = max_y - min_y + 1

        if cw > max_width or ch > max_height:
            continue

        # Skip renderings that are too thin to be readable
        if ch < 5:
            continue

        # Score: prefer larger renderings that still fit
        score = cw * ch

        if score > best_score:
            best_score = score
            # Extract as row strings
            rows = []
            for py in range(min_y, max_y + 1):
                row = ''
                for px in range(min_x, max_x + 1):
                    row += '#' if pixels[px, py] > 80 else '.'
                rows.append(row)
            best_rows = rows

    return best_rows


def extract_all_bitmaps():
    """Extract bitmap data for all language glyphs."""
    results = []
    for var_name, text, font_path, font_num, comment in LANGUAGE_BITMAPS:
        print(f'  {var_name}: "{text}" ({comment})')
        rows = render_text_bitmap(text, font_path, font_num)
        if rows:
            results.append((var_name, rows, comment))
            h = len(rows)
            w = len(rows[0]) if rows else 0
            print(f'    → {w}x{h} bitmap')
        else:
            print(f'    → FAILED (no renderable size found)')
            results.append((var_name, None, comment))
    return results


def format_bitmaps_output(results):
    """Format extracted bitmaps as Python source code."""
    lines = []
    for var_name, rows, comment in results:
        if rows is None:
            lines.append(f'# {var_name} — extraction failed for: {comment}')
            continue
        lines.append(f'{var_name} = _bmp(  # {comment}')
        for row in rows:
            lines.append(f"    '{row}',")
        lines.append(')')
        lines.append('')
    return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'both'

    if mode in ('scripts', 'both'):
        print('=== Extracting script character data ===')
        characters = extract_all_scripts()
        print(f'\nTotal characters: {len(characters)}')

        output_path = Path(__file__).parent / 'extracted_scripts_data.py'
        with open(output_path, 'w') as f:
            f.write('# Auto-generated script character data from system fonts\n')
            f.write(f'# Total: {len(characters)} characters\n\n')

            # Write FAMILIES list
            f.write('FAMILIES = [\n')
            for i, fam in enumerate(FAMILIES_ORDER):
                comma = ',' if i < len(FAMILIES_ORDER) - 1 else ','
                f.write(f"    '{fam}'{comma}\n")
            f.write(']\n\n')

            # Write CHARACTERS
            f.write('CHARACTERS = [\n')
            f.write(format_scripts_output(characters))
            f.write('\n]\n')

        print(f'Written to {output_path}')

        # Print family counts
        from collections import Counter
        counts = Counter(ch['script'] for ch in characters)
        print('\nCharacters per script:')
        for fam in FAMILIES_ORDER:
            print(f'  {fam}: {counts.get(fam, 0)}')

    if mode in ('language', 'both'):
        print('\n=== Extracting language bitmap data ===')
        results = extract_all_bitmaps()

        output_path = Path(__file__).parent / 'extracted_language_data.py'
        with open(output_path, 'w') as f:
            f.write('# Auto-generated language bitmap data from system fonts\n\n')
            f.write(format_bitmaps_output(results))

        print(f'Written to {output_path}')

        # Count successes
        ok = sum(1 for _, rows, _ in results if rows is not None)
        fail = sum(1 for _, rows, _ in results if rows is None)
        print(f'\nSuccess: {ok}, Failed: {fail}')


if __name__ == '__main__':
    main()
