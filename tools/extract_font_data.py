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
#
# Philosophy: ≤175 scripts → include everything in the font's cmap
#             >175 scripts → maximalist curation
#
# The extraction loop filters candidates through the font's cmap, so
# returning a wider range than what's in the font is safe.


def _range(*pairs):
    """Build codepoint list from (start, end) pairs (inclusive start, exclusive end)."""
    out = []
    for i in range(0, len(pairs), 2):
        out.extend(range(pairs[i], pairs[i + 1]))
    return out


# ── COMPLETE scripts (≤175 available — take everything) ──────────────

def _latin_codepoints():
    # Basic Latin A-Z a-z + Latin-1 Supplement accented letters (~116)
    return _range(0x0041, 0x005B, 0x0061, 0x007B, 0x00C0, 0x0100)

def _phoenician_codepoints():
    return _range(0x10900, 0x1091C)  # Full Phoenician alphabet + number signs

def _hebrew_codepoints():
    # Full Hebrew block: letters + points + marks
    return _range(0x0590, 0x05FF)

def _arabic_codepoints():
    # Core Arabic letters and marks (exclude presentation forms)
    return _range(0x0621, 0x0656)

def _greek_codepoints():
    # Full Greek and Coptic block
    return _range(0x0370, 0x03FF)

def _cyrillic_codepoints():
    # Basic Cyrillic + extended A (~124 letters)
    return _range(0x0400, 0x0480)

def _runic_codepoints():
    # Full Runic block
    return _range(0x16A0, 0x16F9)

def _ogham_codepoints():
    # Full Ogham block
    return _range(0x1680, 0x169D)

def _armenian_codepoints():
    # Full Armenian block
    return _range(0x0531, 0x058A)

def _georgian_codepoints():
    # Full Georgian block (Mkhedruli + Asomtavruli)
    return _range(0x10A0, 0x10FF)

def _devanagari_codepoints():
    # Full Devanagari block
    return _range(0x0900, 0x097F)

def _gujarati_codepoints():
    return _range(0x0A80, 0x0AFF)

def _gurmukhi_codepoints():
    return _range(0x0A00, 0x0A7F)

def _bengali_codepoints():
    return _range(0x0980, 0x09FF)

def _tamil_codepoints():
    return _range(0x0B80, 0x0BFF)

def _telugu_codepoints():
    return _range(0x0C00, 0x0C7F)

def _kannada_codepoints():
    return _range(0x0C80, 0x0CFF)

def _malayalam_codepoints():
    return _range(0x0D00, 0x0D7F)

def _sinhala_codepoints():
    return _range(0x0D80, 0x0DFF)

def _tibetan_codepoints():
    # Full Tibetan block
    return _range(0x0F00, 0x0FD0)

def _thai_codepoints():
    return _range(0x0E00, 0x0E7F)

def _lao_codepoints():
    return _range(0x0E80, 0x0EFF)

def _burmese_codepoints():
    # Full Myanmar block
    return _range(0x1000, 0x109F)

def _khmer_codepoints():
    return _range(0x1780, 0x17FF)

def _hiragana_codepoints():
    return _range(0x3040, 0x309F)

def _katakana_codepoints():
    return _range(0x30A0, 0x30FF)

def _tifinagh_codepoints():
    return _range(0x2D30, 0x2D80)

def _nko_codepoints():
    return _range(0x07C0, 0x07FB)

def _mongolian_codepoints():
    return _range(0x1800, 0x18AF)

def _baybayin_codepoints():
    return _range(0x1700, 0x171F)

def _cherokee_codepoints():
    return _range(0x13A0, 0x13FE)


# ── CURATED scripts (>175 available — hand-picked selection) ─────────

def _korean_hangul_codepoints():
    """Jamo consonants/vowels + most-used hangul syllables (~100)."""
    # All compatibility jamo (consonants + vowels)
    jamo = _range(0x3131, 0x3164)
    # Most common hangul syllables (가나다라마바사아자차카타파하 + frequent)
    syllables = [
        0xAC00,  # 가
        0xAC01,  # 각
        0xAC04,  # 간
        0xAC10,  # 감
        0xAC15,  # 갑
        0xAC19,  # 강
        0xAC1C,  # 개
        0xAC70,  # 거
        0xAC74,  # 건
        0xACBD,  # 경
        0xACE0,  # 고
        0xACF5,  # 공
        0xAD00,  # 관
        0xAD11,  # 광
        0xAD50,  # 교
        0xAD6C,  # 구
        0xAD6D,  # 국
        0xAD70,  # 군
        0xADE0,  # 글
        0xADF8,  # 그
        0xAE08,  # 금
        0xAE30,  # 기
        0xB098,  # 나
        0xB0B4,  # 내
        0xB108,  # 너
        0xB178,  # 노
        0xB204,  # 누
        0xB2C8,  # 니
        0xB2E4,  # 다
        0xB300,  # 대
        0xB3C4,  # 도
        0xB3D9,  # 동
        0xB450,  # 두
        0xB4DC,  # 드
        0xB77C,  # 라
        0xB798,  # 래
        0xB7EC,  # 러
        0xB85C,  # 로
        0xB8CC,  # 료
        0xB9AC,  # 리
        0xB9C8,  # 마
        0xB9CC,  # 만
        0xBA38,  # 머
        0xBA54,  # 메
        0xBAA8,  # 모
        0xBB34,  # 무
        0xBBFC,  # 민
        0xBC14,  # 바
        0xBC18,  # 반
        0xBC1C,  # 발
        0xBC29,  # 방
        0xBC30,  # 배
        0xBC84,  # 버
        0xBCC0,  # 변
        0xBCF4,  # 보
        0xBD80,  # 부
        0xBD81,  # 북
        0xBD84,  # 분
        0xBE44,  # 비
        0xC0AC,  # 사
        0xC0B0,  # 산
        0xC0C1,  # 상
        0xC0C8,  # 새
        0xC11C,  # 서
        0xC120,  # 선
        0xC138,  # 세
        0xC18C,  # 소
        0xC218,  # 수
        0xC2DC,  # 시
        0xC2E0,  # 신
        0xC544,  # 아
        0xC548,  # 안
        0xC554,  # 암
        0xC57C,  # 야
        0xC5B4,  # 어
        0xC5EC,  # 여
        0xC5F0,  # 연
        0xC601,  # 영
        0xC624,  # 오
        0xC6B0,  # 우
        0xC6D0,  # 원
        0xC6D4,  # 월
        0xC704,  # 위
        0xC720,  # 유
        0xC740,  # 은
        0xC744,  # 을
        0xC74C,  # 음
        0xC758,  # 의
        0xC774,  # 이
        0xC778,  # 인
        0xC77C,  # 일
        0xC790,  # 자
        0xC7A5,  # 장
        0xC800,  # 저
        0xC804,  # 전
        0xC815,  # 정
        0xC81C,  # 제
        0xC870,  # 조
        0xC8FC,  # 주
        0xC911,  # 중
        0xC9C0,  # 지
        0xCC28,  # 차
        0xCC98,  # 처
        0xCC9C,  # 천
        0xCCAD,  # 청
        0xCD08,  # 초
        0xCD5C,  # 최
        0xCE58,  # 치
        0xCE68,  # 침
        0xCF54,  # 코
        0xD06C,  # 크
        0xD0C0,  # 타
        0xD0DC,  # 태
        0xD1A0,  # 토
        0xD2B8,  # 트
        0xD30C,  # 파
        0xD310,  # 판
        0xD3C9,  # 평
        0xD3EC,  # 포
        0xD488,  # 품
        0xD504,  # 프
        0xD53C,  # 피
        0xD558,  # 하
        0xD559,  # 학
        0xD55C,  # 한
        0xD574,  # 해
        0xD589,  # 행
        0xD604,  # 현
        0xD615,  # 형
        0xD638,  # 호
        0xD654,  # 화
        0xD68C,  # 회
        0xD6C4,  # 후
        0xD798,  # 힘
    ]
    return jamo + syllables

def _cjk_common():
    """~100 most common/meaningful CJK characters."""
    return [
        # Numbers
        0x4E00,  # 一 one
        0x4E8C,  # 二 two
        0x4E09,  # 三 three
        0x56DB,  # 四 four
        0x4E94,  # 五 five
        0x516D,  # 六 six
        0x4E03,  # 七 seven
        0x516B,  # 八 eight
        0x4E5D,  # 九 nine
        0x5341,  # 十 ten
        0x767E,  # 百 hundred
        0x5343,  # 千 thousand
        0x4E07,  # 万 ten thousand
        # Nature
        0x5C71,  # 山 mountain
        0x6C34,  # 水 water
        0x706B,  # 火 fire
        0x6728,  # 木 tree/wood
        0x6797,  # 林 forest
        0x68EE,  # 森 deep forest
        0x5DDD,  # 川 river
        0x6D77,  # 海 sea
        0x7A7A,  # 空 sky/empty
        0x96E8,  # 雨 rain
        0x96EA,  # 雪 snow
        0x98A8,  # 風 wind
        0x96F2,  # 雲 cloud
        0x82B1,  # 花 flower
        0x8349,  # 草 grass
        0x7AF9,  # 竹 bamboo
        # Celestial
        0x65E5,  # 日 sun/day
        0x6708,  # 月 moon/month
        0x661F,  # 星 star
        0x5149,  # 光 light
        0x5929,  # 天 heaven/sky
        0x5730,  # 地 earth/ground
        # Body
        0x53E3,  # 口 mouth
        0x76EE,  # 目 eye
        0x8033,  # 耳 ear
        0x624B,  # 手 hand
        0x8DB3,  # 足 foot
        0x9996,  # 首 head/neck
        0x5FC3,  # 心 heart/mind
        0x9AA8,  # 骨 bone
        0x8840,  # 血 blood
        # People
        0x4EBA,  # 人 person
        0x5973,  # 女 woman
        0x5B50,  # 子 child
        0x7236,  # 父 father
        0x6BCD,  # 母 mother
        0x738B,  # 王 king
        0x795E,  # 神 god/spirit
        0x53CB,  # 友 friend
        # Animals
        0x9CE5,  # 鳥 bird
        0x9B5A,  # 魚 fish
        0x99AC,  # 馬 horse
        0x725B,  # 牛 cow
        0x7F8A,  # 羊 sheep
        0x72AC,  # 犬 dog
        0x8C9D,  # 貝 shell
        0x866B,  # 虫 insect
        0x9F8D,  # 龍 dragon
        # Elements & materials
        0x91D1,  # 金 gold/metal
        0x571F,  # 土 earth/soil
        0x77F3,  # 石 stone
        0x7389,  # 玉 jade
        0x9244,  # 鉄 iron
        # Actions
        0x98DF,  # 食 eat
        0x898B,  # 見 see
        0x805E,  # 聞 hear
        0x8A00,  # 言 say
        0x8ACB,  # 請 ask/please
        0x884C,  # 行 go/travel
        0x6765,  # 来 come
        0x7ACB,  # 立 stand
        0x5EA7,  # 座 sit
        0x751F,  # 生 life/birth
        0x6B7B,  # 死 death
        # Concepts
        0x5927,  # 大 big
        0x5C0F,  # 小 small
        0x4E2D,  # 中 middle
        0x4E0A,  # 上 above
        0x4E0B,  # 下 below
        0x524D,  # 前 before
        0x5F8C,  # 後 after
        0x5DE6,  # 左 left
        0x53F3,  # 右 right
        0x5185,  # 内 inside
        0x5916,  # 外 outside
        0x6B63,  # 正 correct
        0x7F8E,  # 美 beauty
        0x611B,  # 愛 love
        0x9053,  # 道 way/path
        0x529B,  # 力 power
        0x6C17,  # 気 spirit/energy
        # Places
        0x5BB6,  # 家 home
        0x7530,  # 田 field
        0x9580,  # 門 gate
        0x5E02,  # 市 city
        0x56FD,  # 国 country
    ]

def _ethiopic_codepoints():
    """~150 Ethiopic: all 7 vowel orders for the 20 most common consonant rows."""
    cps = []
    # Each consonant row has 7 vowel orders (ä, u, i, a, é, e/ə, o)
    # ha=1200, la=1208, Ha=1210, ma=1218, sza=1220, ra=1228, sa=1230,
    # sha=1238, qa=1240, ba=1260, ta=1270, cha=1278, na=1290, nya=1298,
    # a=12A0, ka=12A8, wa=12C8, za=12D8, ya=12E8, da=12F0, ga=1308,
    # pa=1350, tsa=1358
    rows = [0x1200, 0x1208, 0x1210, 0x1218, 0x1228, 0x1230, 0x1238,
            0x1240, 0x1260, 0x1270, 0x1278, 0x1290, 0x1298, 0x12A0,
            0x12A8, 0x12C8, 0x12D8, 0x12E8, 0x12F0, 0x1308, 0x1350, 0x1358]
    for row in rows:
        cps.extend(range(row, row + 7))
    return cps  # 22 rows × 7 = 154

def _vai_codepoints():
    """~150 Vai syllables covering all consonant series × common vowels."""
    # Vai syllabary: each consonant has ~5 vowel forms
    # Cover broadly across the block, picking visually distinct syllables
    cps = []
    # Full first section (most common syllables)
    cps.extend(range(0xA500, 0xA596))  # First 150 syllables
    return cps

def _inuktitut_codepoints():
    """~150 Canadian Syllabics: all 4 vowel rotations for main consonant series + finals."""
    cps = []
    # e/i/o/a rotations for each consonant series
    # Each series: 4 short vowels + 4 long vowels (sometimes) + final
    series = [
        (0x1401, 8),   # e-series (ᐁ-ᐈ)
        (0x140A, 6),   # i-series (ᐊ-ᐏ)
        (0x1410, 8),   # o-series
        (0x1418, 8),   # a-series
        (0x1420, 8),   # p-series (ᐠ-ᐧ)
        (0x1428, 8),   # t-series
        (0x1430, 8),   # k-series
        (0x1438, 8),   # c-series
        (0x1440, 8),   # m-series
        (0x1448, 8),   # n-series
        (0x1450, 8),   # s-series
        (0x1458, 8),   # l-series
        (0x1460, 8),   # y-series
        (0x1468, 8),   # f-series
        (0x1470, 8),   # r-series
        (0x1478, 8),   # q-series
        (0x1480, 8),   # ng-series
        (0x1488, 8),   # nng-series
        (0x1490, 8),   # th-series
    ]
    for start, count in series:
        cps.extend(range(start, start + count))
    # Finals
    cps.extend(range(0x1550, 0x1574))
    return cps

def _hieroglyph_codepoints():
    """~80 Egyptian Hieroglyphs across all major Gardiner categories."""
    return [
        # A - Seated figures
        0x13000,  # A001 seated man
        0x13001,  # A002 man with hand to mouth
        0x1301E,  # A028 man with hands raised
        0x13024,  # A034 man pounding
        0x1302A,  # A040 seated god
        # B - Women
        0x13030,  # B001 seated woman
        0x13031,  # B002 pregnant woman
        # C - Anthropomorphic deities
        0x13036,  # C001 god with sun disk
        0x13037,  # C002 god with falcon head
        0x1303A,  # C006 god with ibis head (Thoth)
        0x1303C,  # C010 goddess with horns
        # D - Body parts
        0x13080,  # D001 head in profile
        0x13082,  # D002 face
        0x13091,  # D010 eye of horus
        0x130A4,  # D021 mouth
        0x130B7,  # D036 forearm
        0x130BA,  # D039 forearm with bread
        0x130C0,  # D046 hand
        0x130C4,  # D050 finger
        0x130CB,  # D054 legs walking
        0x130CF,  # D058 foot
        # E - Mammals
        0x130D6,  # E001 bull
        0x130DD,  # E009 newborn calf
        0x130E1,  # E015 lying dog/jackal
        0x130E6,  # E020 lion
        0x130E8,  # E023 lying lion
        0x130EC,  # E026 elephant
        # F - Parts of mammals
        0x130F0,  # F001 ox head
        0x130F3,  # F004 forepart of lion
        # G - Birds
        0x130F4,  # G001 Egyptian vulture
        0x130F8,  # G005 falcon
        0x13100,  # G017 owl
        0x13107,  # G025 crested ibis
        0x13109,  # G027 flamingo
        0x1310B,  # G029 jabiru
        0x13110,  # G036 swallow
        0x13113,  # G039 pintail duck
        0x13117,  # G043 quail chick
        # I - Reptiles
        0x13153,  # I010 cobra
        0x13155,  # I012 erect cobra
        0x13148,  # I003 crocodile
        0x13157,  # I014 serpent
        # K - Fish
        0x1315E,  # K001 tilapia
        0x13160,  # K003 mullet
        # L - Invertebrates
        0x13163,  # L001 dung beetle (scarab)
        0x13164,  # L002 bee
        0x13167,  # L006 scorpion
        # M - Plants
        0x13174,  # M001 tree
        0x13179,  # M003 branch
        0x13190,  # M017 reed
        0x13192,  # M018 reed+reed
        0x131A0,  # M029 seed pod
        # N - Sky, earth, water
        0x131CB,  # N001 sky
        0x131CE,  # N005 sun disk
        0x131D0,  # N008 sunshine
        0x131D5,  # N014 star
        0x131E1,  # N021 tongue of land
        0x131E9,  # N029 hill/slope
        0x131EE,  # N035 ripple of water
        # O - Buildings
        0x13200,  # O001 house
        0x13203,  # O004 shelter
        0x1320C,  # O018 shrine
        0x13210,  # O024 pyramid
        # P - Ships and parts
        0x13228,  # P001 boat
        # Q - Furniture
        0x13254,  # Q001 seat/throne
        0x13256,  # Q003 stool
        # R - Temple
        0x13274,  # R004 altar with loaf
        0x1327B,  # R008 standard
        # S - Crowns, clothing
        0x13280,  # S001 white crown
        0x13281,  # S002 combined crown
        0x13286,  # S012 collar
        0x13289,  # S020 seal/signet
        # T - Warfare
        0x132A4,  # T001 mace
        0x132B0,  # T014 throwstick
        # U - Agriculture
        0x132B9,  # U001 sickle
        0x132C8,  # U015 sledge
        # V - Rope, baskets
        0x132D0,  # V001 coil of rope
        0x132D4,  # V004 lasso
        # W - Vessels
        0x132F0,  # W001 oil jar
        0x132F4,  # W009 stone jug
        0x132F9,  # W014 water jar
        # X - Bread, cakes
        0x13300,  # X001 bread loaf
        # Y - Games, writing
        0x13308,  # Y001 game board
        0x1330A,  # Y003 scribe's palette
        # Z - Strokes
        0x1330E,  # Z001 single stroke
        # Aa - Unclassified
        0x13313,  # Aa001 placenta
        0x13315,  # Aa002 pustule
    ]

def _cuneiform_codepoints():
    """~80 core Sumerian cuneiform signs."""
    return [
        0x12000,  # A
        0x12001,  # A2
        0x1200D,  # AN (god/sky)
        0x1200E,  # AN (variant)
        0x12033,  # ASH (one)
        0x12034,  # ASH2
        0x12038,  # BA
        0x1203C,  # BAD
        0x12041,  # BAL
        0x12049,  # BI
        0x1204D,  # BU
        0x12051,  # BUR
        0x12070,  # DA
        0x12071,  # DA (variant)
        0x1207A,  # DI
        0x12083,  # DINGIR (divine)
        0x12084,  # DISH (1)
        0x12089,  # DU (go/walk)
        0x1208A,  # DU (variant)
        0x12092,  # DUG (vessel)
        0x1209A,  # E
        0x1209B,  # E2 (house)
        0x120A0,  # EN (lord)
        0x120A5,  # ERIN2
        0x120AD,  # GA
        0x120AE,  # GA2 (container)
        0x120B7,  # GAL (great)
        0x120B8,  # GAL (variant)
        0x120C7,  # GI
        0x120CA,  # GI4
        0x120CE,  # GIG
        0x120D5,  # GU
        0x120D6,  # GU2 (neck)
        0x120E0,  # GUD (bull)
        0x120EE,  # HA
        0x120F8,  # HU
        0x120FD,  # HUL
        0x12107,  # IGI (eye)
        0x12109,  # IL
        0x1210A,  # IL2
        0x12113,  # KA (mouth)
        0x12114,  # KA2 (gate)
        0x12122,  # KI (earth/place)
        0x12127,  # KU
        0x12129,  # KU3 (pure/silver)
        0x1212D,  # KUR (mountain/land)
        0x12134,  # LA
        0x12138,  # LAGAB
        0x1213C,  # LAL
        0x12146,  # LI
        0x12148,  # LIL
        0x1214E,  # LU (man)
        0x12151,  # LU2 (person)
        0x12158,  # LUGAL (king)
        0x1215F,  # MA
        0x12163,  # MAH (great)
        0x12168,  # MAR
        0x1216A,  # MASH
        0x12171,  # ME
        0x12178,  # MIN (two)
        0x1217A,  # MU
        0x12181,  # MUL (star)
        0x12191,  # NA
        0x12195,  # NAM (fate)
        0x1219E,  # NI
        0x121A3,  # NIM
        0x121A5,  # NINDA2 (bread)
        0x121AC,  # NU
        0x121B2,  # NUN
        0x121B8,  # PA
        0x121C6,  # RA
        0x121D2,  # SA
        0x121D7,  # SAG (head)
        0x121DB,  # SAL (woman)
        0x121DE,  # SAR
        0x121EB,  # SHA
        0x121F2,  # SHE (grain)
        0x121F8,  # SHU (hand)
        0x12204,  # TA
        0x1220E,  # TI (life)
        0x12211,  # TIL
        0x12217,  # TU
        0x12222,  # U (ten)
        0x12223,  # U2 (plant)
        0x1222B,  # UD (sun/day)
        0x12229,  # UD (variant)
        0x12234,  # UM
        0x12236,  # UN (people)
        0x1223E,  # UR (dog/servant)
        0x12245,  # UR2 (root)
        0x12248,  # URI3
        0x12249,  # URU (city)
    ]

def _linear_b_codepoints():
    """~150 Linear B syllabograms + key ideograms."""
    # Syllabograms: B000-B089 (0x10000-0x1005D)
    syllabograms = _range(0x10000, 0x1005E)
    # Ideograms: B100-B250 (0x10080-0x100FA)
    ideograms = _range(0x10080, 0x100FB)
    return syllabograms + ideograms

def _braille_codepoints():
    """~100 Braille: letters, digits, punctuation, common contractions."""
    # Full A-Z (dots patterns for letters)
    cps = _range(0x2801, 0x281B)  # a-z (26 patterns)
    # Capital sign + number sign + common punctuation patterns
    cps += [
        0x2820,  # dot 6 (capital sign)
        0x283C,  # number sign
        0x2800,  # blank
        0x2824,  # dot 3,6
        0x2834,  # dot 3,5,6
        0x2826,  # dot 2,3,6
        0x2830,  # dot 5,6
        0x2822,  # dot 2,6
        0x2836,  # dot 2,3,5,6
        0x2832,  # dot 2,5,6
    ]
    # Extended set: all 256 patterns for visual variety
    cps += _range(0x281B, 0x2840)
    # Deduplicate and sort
    return sorted(set(cps))


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
                       'LATIN LETTER ',
                       'GREEK SMALL LETTER ', 'GREEK CAPITAL LETTER ',
                       'GREEK LETTER ',
                       'CYRILLIC SMALL LETTER ', 'CYRILLIC CAPITAL LETTER ',
                       'CYRILLIC LETTER ',
                       'HEBREW LETTER ', 'HEBREW POINT ', 'HEBREW MARK ',
                       'ARABIC LETTER ', 'ARABIC SIGN ', 'ARABIC MARK ',
                       'DEVANAGARI LETTER ', 'DEVANAGARI VOWEL SIGN ',
                       'DEVANAGARI SIGN ', 'DEVANAGARI DIGIT ',
                       'BENGALI LETTER ', 'BENGALI VOWEL SIGN ',
                       'BENGALI SIGN ', 'BENGALI DIGIT ',
                       'GUJARATI LETTER ', 'GUJARATI VOWEL SIGN ',
                       'GUJARATI SIGN ', 'GUJARATI DIGIT ',
                       'GURMUKHI LETTER ', 'GURMUKHI VOWEL SIGN ',
                       'GURMUKHI SIGN ', 'GURMUKHI DIGIT ',
                       'TAMIL LETTER ', 'TAMIL VOWEL SIGN ',
                       'TAMIL SIGN ', 'TAMIL DIGIT ',
                       'TELUGU LETTER ', 'TELUGU VOWEL SIGN ',
                       'TELUGU SIGN ', 'TELUGU DIGIT ',
                       'KANNADA LETTER ', 'KANNADA VOWEL SIGN ',
                       'KANNADA SIGN ', 'KANNADA DIGIT ',
                       'MALAYALAM LETTER ', 'MALAYALAM VOWEL SIGN ',
                       'MALAYALAM SIGN ', 'MALAYALAM DIGIT ',
                       'SINHALA LETTER ', 'SINHALA VOWEL SIGN ',
                       'SINHALA SIGN ',
                       'TIBETAN LETTER ', 'TIBETAN SUBJOINED LETTER ',
                       'TIBETAN SIGN ', 'TIBETAN DIGIT ', 'TIBETAN MARK ',
                       'THAI CHARACTER ', 'THAI DIGIT ',
                       'LAO LETTER ', 'LAO VOWEL SIGN ', 'LAO DIGIT ',
                       'MYANMAR LETTER ', 'MYANMAR VOWEL SIGN ',
                       'MYANMAR SIGN ', 'MYANMAR DIGIT ',
                       'KHMER LETTER ', 'KHMER VOWEL SIGN ',
                       'KHMER SIGN ', 'KHMER DIGIT ',
                       'HANGUL LETTER ', 'HANGUL SYLLABLE ',
                       'HIRAGANA LETTER ', 'KATAKANA LETTER ',
                       'ETHIOPIC SYLLABLE ',
                       'TIFINAGH LETTER ', 'NKO LETTER ', 'NKO DIGIT ',
                       'VAI SYLLABLE ', 'CHEROKEE LETTER ',
                       'CHEROKEE SMALL LETTER ',
                       'CANADIAN SYLLABICS ', 'MONGOLIAN LETTER ',
                       'MONGOLIAN DIGIT ',
                       'TAGALOG LETTER ', 'EGYPTIAN HIEROGLYPH ',
                       'CUNEIFORM SIGN ', 'LINEAR B SYLLABLE ',
                       'LINEAR B IDEOGRAM ',
                       'BRAILLE PATTERN ', 'ARMENIAN CAPITAL LETTER ',
                       'ARMENIAN SMALL LETTER ', 'GEORGIAN LETTER ',
                       'GEORGIAN CAPITAL LETTER ', 'GEORGIAN SMALL LETTER ',
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
                0x4E00: 'ONE', 0x4E8C: 'TWO', 0x4E09: 'THREE',
                0x56DB: 'FOUR', 0x4E94: 'FIVE', 0x516D: 'SIX',
                0x4E03: 'SEVEN', 0x516B: 'EIGHT', 0x4E5D: 'NINE',
                0x5341: 'TEN', 0x767E: 'HUNDRED', 0x5343: 'THOUSAND',
                0x4E07: 'TEN THOUSAND',
                0x5C71: 'MOUNTAIN', 0x6C34: 'WATER', 0x706B: 'FIRE',
                0x6728: 'TREE / WOOD', 0x6797: 'FOREST', 0x68EE: 'DEEP FOREST',
                0x5DDD: 'RIVER', 0x6D77: 'SEA', 0x7A7A: 'SKY / EMPTY',
                0x96E8: 'RAIN', 0x96EA: 'SNOW', 0x98A8: 'WIND',
                0x96F2: 'CLOUD', 0x82B1: 'FLOWER', 0x8349: 'GRASS',
                0x7AF9: 'BAMBOO',
                0x65E5: 'SUN / DAY', 0x6708: 'MOON / MONTH', 0x661F: 'STAR',
                0x5149: 'LIGHT', 0x5929: 'HEAVEN / SKY', 0x5730: 'EARTH',
                0x53E3: 'MOUTH', 0x76EE: 'EYE', 0x8033: 'EAR',
                0x624B: 'HAND', 0x8DB3: 'FOOT', 0x9996: 'HEAD',
                0x5FC3: 'HEART / MIND', 0x9AA8: 'BONE', 0x8840: 'BLOOD',
                0x4EBA: 'PERSON', 0x5973: 'WOMAN', 0x5B50: 'CHILD',
                0x7236: 'FATHER', 0x6BCD: 'MOTHER', 0x738B: 'KING',
                0x795E: 'GOD / SPIRIT', 0x53CB: 'FRIEND',
                0x9CE5: 'BIRD', 0x9B5A: 'FISH', 0x99AC: 'HORSE',
                0x725B: 'COW', 0x7F8A: 'SHEEP', 0x72AC: 'DOG',
                0x8C9D: 'SHELL', 0x866B: 'INSECT', 0x9F8D: 'DRAGON',
                0x91D1: 'GOLD / METAL', 0x571F: 'EARTH / SOIL',
                0x77F3: 'STONE', 0x7389: 'JADE', 0x9244: 'IRON',
                0x98DF: 'EAT', 0x898B: 'SEE', 0x805E: 'HEAR',
                0x8A00: 'SAY', 0x8ACB: 'ASK', 0x884C: 'GO / TRAVEL',
                0x6765: 'COME', 0x7ACB: 'STAND', 0x5EA7: 'SIT',
                0x751F: 'LIFE / BIRTH', 0x6B7B: 'DEATH',
                0x5927: 'BIG', 0x5C0F: 'SMALL', 0x4E2D: 'MIDDLE',
                0x4E0A: 'ABOVE', 0x4E0B: 'BELOW', 0x524D: 'BEFORE',
                0x5F8C: 'AFTER', 0x5DE6: 'LEFT', 0x53F3: 'RIGHT',
                0x5185: 'INSIDE', 0x5916: 'OUTSIDE', 0x6B63: 'CORRECT',
                0x7F8E: 'BEAUTY', 0x611B: 'LOVE', 0x9053: 'WAY / PATH',
                0x529B: 'POWER', 0x6C17: 'SPIRIT / QI',
                0x5BB6: 'HOME', 0x7530: 'FIELD', 0x9580: 'GATE',
                0x5E02: 'CITY', 0x56FD: 'COUNTRY',
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
