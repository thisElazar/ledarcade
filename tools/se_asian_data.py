"""
Generated stroke data for SE Asian scripts: Burmese, Khmer, and Lao.
Copy these into the CHARACTERS list in visuals/scripts.py.
"""

# ── Color constants ──────────────────────────────────────────────────
_BURMESE_INK = (30, 30, 30)
_BURMESE_PAPER = (230, 225, 200)
_KHMER_INK = (60, 40, 20)
_KHMER_PAPER = (225, 218, 195)
_LAO_INK = (80, 30, 100)
_LAO_PAPER = (228, 225, 215)

# =====================================================================
# BURMESE / MYANMAR  (33 consonants)
# Famously circular script - almost every letter based on circles.
# Written on palm leaves, so straight lines avoided (would tear leaf).
# Stroke zone: roughly x=18-46, y=20-50
# =====================================================================

BURMESE_CHARS = [
    # 1. Ka - basic circle
    {
        'name': 'Ka', 'script': 'BURMESE', 'concept': 'Ka',
        'origin': 'MYANMAR ~1050 AD',
        'ink': _BURMESE_INK, 'paper': _BURMESE_PAPER,
        'strokes': [
            [(30, 22), (22, 26), (20, 34), (22, 42), (30, 46), (38, 42), (40, 34), (38, 26), (30, 22)],
        ],
    },
    # 2. Kha - circle with right tail
    {
        'name': 'Kha', 'script': 'BURMESE', 'concept': 'Kha',
        'origin': 'MYANMAR ~1050 AD',
        'ink': _BURMESE_INK, 'paper': _BURMESE_PAPER,
        'strokes': [
            [(30, 22), (22, 26), (20, 34), (22, 42), (30, 46), (38, 42), (40, 34), (38, 26), (30, 22)],
            [(40, 34), (46, 30)],
        ],
    },
    # 3. Ga - circle open at top-right
    {
        'name': 'Ga', 'script': 'BURMESE', 'concept': 'Ga',
        'origin': 'MYANMAR ~1050 AD',
        'ink': _BURMESE_INK, 'paper': _BURMESE_PAPER,
        'strokes': [
            [(36, 22), (28, 22), (20, 28), (20, 36), (24, 44), (32, 46), (40, 42), (42, 34), (40, 26)],
            [(40, 26), (44, 22)],
        ],
    },
    # 4. Gha - circle with downward tail
    {
        'name': 'Gha', 'script': 'BURMESE', 'concept': 'Gha',
        'origin': 'MYANMAR ~1050 AD',
        'ink': _BURMESE_INK, 'paper': _BURMESE_PAPER,
        'strokes': [
            [(30, 20), (22, 24), (20, 32), (22, 40), (30, 44), (38, 40), (40, 32), (38, 24), (30, 20)],
            [(30, 44), (28, 50)],
        ],
    },
    # 5. Nga - figure-eight / double circle
    {
        'name': 'Nga', 'script': 'BURMESE', 'concept': 'Nga',
        'origin': 'MYANMAR ~1050 AD',
        'ink': _BURMESE_INK, 'paper': _BURMESE_PAPER,
        'strokes': [
            [(30, 20), (24, 22), (20, 28), (24, 34), (30, 34)],
            [(30, 34), (24, 36), (20, 42), (24, 48), (32, 48), (36, 44), (36, 38), (30, 34)],
        ],
    },
    # 6. Sa - small circle with horizontal bar
    {
        'name': 'Sa', 'script': 'BURMESE', 'concept': 'Sa',
        'origin': 'MYANMAR ~1050 AD',
        'ink': _BURMESE_INK, 'paper': _BURMESE_PAPER,
        'strokes': [
            [(28, 24), (22, 28), (22, 36), (28, 40), (36, 36), (36, 28), (28, 24)],
            [(36, 32), (44, 32)],
        ],
    },
    # 7. Hsa - circle with top hook
    {
        'name': 'Hsa', 'script': 'BURMESE', 'concept': 'Hsa',
        'origin': 'MYANMAR ~1050 AD',
        'ink': _BURMESE_INK, 'paper': _BURMESE_PAPER,
        'strokes': [
            [(34, 20), (30, 22), (28, 20)],
            [(30, 24), (22, 28), (20, 36), (24, 44), (32, 46), (40, 42), (42, 34), (38, 26), (30, 24)],
        ],
    },
    # 8. Za - circle with left extension
    {
        'name': 'Za', 'script': 'BURMESE', 'concept': 'Za',
        'origin': 'MYANMAR ~1050 AD',
        'ink': _BURMESE_INK, 'paper': _BURMESE_PAPER,
        'strokes': [
            [(18, 34), (22, 30)],
            [(28, 24), (22, 30), (20, 38), (24, 44), (32, 46), (40, 42), (42, 34), (38, 26), (28, 24)],
        ],
    },
    # 9. Zha - wide circle with inner dot
    {
        'name': 'Zha', 'script': 'BURMESE', 'concept': 'Zha',
        'origin': 'MYANMAR ~1050 AD',
        'ink': _BURMESE_INK, 'paper': _BURMESE_PAPER,
        'strokes': [
            [(32, 22), (24, 24), (20, 32), (22, 40), (30, 46), (38, 42), (42, 34), (40, 26), (32, 22)],
            [(30, 34), (32, 34)],
        ],
    },
    # 10. Nya - double circle side by side
    {
        'name': 'Nya', 'script': 'BURMESE', 'concept': 'Nya',
        'origin': 'MYANMAR ~1050 AD',
        'ink': _BURMESE_INK, 'paper': _BURMESE_PAPER,
        'strokes': [
            [(26, 24), (20, 28), (20, 36), (26, 40), (30, 36), (30, 28), (26, 24)],
            [(34, 24), (30, 28), (30, 36), (34, 40), (40, 36), (40, 28), (34, 24)],
        ],
    },
    # 11. Ta_retro - circle with top-right serif
    {
        'name': 'Ta_retro', 'script': 'BURMESE', 'concept': 'Ta (retroflex)',
        'origin': 'MYANMAR ~1050 AD',
        'ink': _BURMESE_INK, 'paper': _BURMESE_PAPER,
        'strokes': [
            [(32, 22), (24, 26), (20, 34), (24, 42), (32, 46), (40, 42), (42, 34), (38, 26), (32, 22)],
            [(38, 26), (42, 22), (44, 20)],
        ],
    },
    # 12. Hta_retro - circle with horizontal top bar
    {
        'name': 'Hta_retro', 'script': 'BURMESE', 'concept': 'Hta (retroflex)',
        'origin': 'MYANMAR ~1050 AD',
        'ink': _BURMESE_INK, 'paper': _BURMESE_PAPER,
        'strokes': [
            [(22, 22), (40, 22)],
            [(30, 22), (22, 28), (20, 36), (24, 44), (32, 46), (40, 42), (42, 34), (40, 26), (30, 22)],
        ],
    },
    # 13. Da_retro - oval tilted right
    {
        'name': 'Da_retro', 'script': 'BURMESE', 'concept': 'Da (retroflex)',
        'origin': 'MYANMAR ~1050 AD',
        'ink': _BURMESE_INK, 'paper': _BURMESE_PAPER,
        'strokes': [
            [(36, 20), (24, 26), (20, 36), (24, 44), (34, 48), (42, 42), (44, 32), (40, 24), (36, 20)],
        ],
    },
    # 14. Dha_retro - circle with bottom-left curl
    {
        'name': 'Dha_retro', 'script': 'BURMESE', 'concept': 'Dha (retroflex)',
        'origin': 'MYANMAR ~1050 AD',
        'ink': _BURMESE_INK, 'paper': _BURMESE_PAPER,
        'strokes': [
            [(30, 22), (22, 26), (20, 34), (22, 42), (30, 46), (38, 42), (40, 34), (38, 26), (30, 22)],
            [(22, 42), (18, 48), (22, 50)],
        ],
    },
    # 15. Na_retro - circle with inner horizontal
    {
        'name': 'Na_retro', 'script': 'BURMESE', 'concept': 'Na (retroflex)',
        'origin': 'MYANMAR ~1050 AD',
        'ink': _BURMESE_INK, 'paper': _BURMESE_PAPER,
        'strokes': [
            [(30, 22), (22, 26), (20, 34), (22, 42), (30, 46), (38, 42), (40, 34), (38, 26), (30, 22)],
            [(24, 34), (36, 34)],
        ],
    },
    # 16. Ta - circle open at bottom
    {
        'name': 'Ta', 'script': 'BURMESE', 'concept': 'Ta',
        'origin': 'MYANMAR ~1050 AD',
        'ink': _BURMESE_INK, 'paper': _BURMESE_PAPER,
        'strokes': [
            [(24, 44), (20, 36), (22, 28), (30, 22), (38, 28), (40, 36), (36, 44)],
        ],
    },
    # 17. Hta - circle with vertical line through
    {
        'name': 'Hta', 'script': 'BURMESE', 'concept': 'Hta',
        'origin': 'MYANMAR ~1050 AD',
        'ink': _BURMESE_INK, 'paper': _BURMESE_PAPER,
        'strokes': [
            [(30, 20), (22, 24), (20, 32), (22, 40), (30, 44), (38, 40), (40, 32), (38, 24), (30, 20)],
            [(30, 20), (30, 50)],
        ],
    },
    # 18. Da - small tight circle
    {
        'name': 'Da', 'script': 'BURMESE', 'concept': 'Da',
        'origin': 'MYANMAR ~1050 AD',
        'ink': _BURMESE_INK, 'paper': _BURMESE_PAPER,
        'strokes': [
            [(32, 24), (26, 26), (22, 32), (24, 40), (30, 44), (36, 42), (40, 36), (40, 28), (36, 24), (32, 24)],
            [(40, 28), (44, 24)],
        ],
    },
    # 19. Dha - circle with right descender
    {
        'name': 'Dha', 'script': 'BURMESE', 'concept': 'Dha',
        'origin': 'MYANMAR ~1050 AD',
        'ink': _BURMESE_INK, 'paper': _BURMESE_PAPER,
        'strokes': [
            [(32, 22), (24, 26), (20, 34), (24, 42), (32, 44), (40, 40), (42, 32), (38, 24), (32, 22)],
            [(40, 40), (42, 48)],
        ],
    },
    # 20. Na - circle with right hook curling up
    {
        'name': 'Na', 'script': 'BURMESE', 'concept': 'Na',
        'origin': 'MYANMAR ~1050 AD',
        'ink': _BURMESE_INK, 'paper': _BURMESE_PAPER,
        'strokes': [
            [(30, 24), (22, 28), (20, 36), (24, 44), (32, 46), (40, 42), (42, 34), (38, 26), (30, 24)],
            [(42, 34), (46, 32), (44, 28)],
        ],
    },
    # 21. Pa - circle with left tail curving down
    {
        'name': 'Pa', 'script': 'BURMESE', 'concept': 'Pa',
        'origin': 'MYANMAR ~1050 AD',
        'ink': _BURMESE_INK, 'paper': _BURMESE_PAPER,
        'strokes': [
            [(30, 22), (22, 26), (20, 34), (22, 42), (30, 46), (38, 42), (40, 34), (38, 26), (30, 22)],
            [(20, 34), (18, 42), (20, 48)],
        ],
    },
    # 22. Hpa - wide circle with top notch
    {
        'name': 'Hpa', 'script': 'BURMESE', 'concept': 'Hpa',
        'origin': 'MYANMAR ~1050 AD',
        'ink': _BURMESE_INK, 'paper': _BURMESE_PAPER,
        'strokes': [
            [(28, 22), (22, 28), (20, 36), (24, 44), (32, 46), (40, 42), (42, 34), (40, 26), (34, 22)],
            [(28, 22), (30, 20)],
            [(32, 20), (34, 22)],
        ],
    },
    # 23. Ba - circle with bottom hook
    {
        'name': 'Ba', 'script': 'BURMESE', 'concept': 'Ba',
        'origin': 'MYANMAR ~1050 AD',
        'ink': _BURMESE_INK, 'paper': _BURMESE_PAPER,
        'strokes': [
            [(30, 22), (22, 26), (20, 34), (22, 42), (30, 46), (38, 42), (40, 34), (38, 26), (30, 22)],
            [(30, 46), (34, 50), (38, 48)],
        ],
    },
    # 24. Bha - circle with double bottom hook
    {
        'name': 'Bha', 'script': 'BURMESE', 'concept': 'Bha',
        'origin': 'MYANMAR ~1050 AD',
        'ink': _BURMESE_INK, 'paper': _BURMESE_PAPER,
        'strokes': [
            [(30, 20), (22, 24), (20, 32), (22, 40), (30, 44), (38, 40), (40, 32), (38, 24), (30, 20)],
            [(30, 44), (26, 48), (30, 50)],
            [(30, 50), (36, 48)],
        ],
    },
    # 25. Ma - circle with inner circle (concentric)
    {
        'name': 'Ma', 'script': 'BURMESE', 'concept': 'Ma',
        'origin': 'MYANMAR ~1050 AD',
        'ink': _BURMESE_INK, 'paper': _BURMESE_PAPER,
        'strokes': [
            [(32, 20), (24, 24), (20, 32), (24, 42), (32, 46), (40, 42), (44, 32), (40, 24), (32, 20)],
            [(32, 28), (28, 30), (26, 34), (28, 38), (32, 40), (36, 38), (38, 34), (36, 30), (32, 28)],
        ],
    },
    # 26. Ya - tall oval
    {
        'name': 'Ya', 'script': 'BURMESE', 'concept': 'Ya',
        'origin': 'MYANMAR ~1050 AD',
        'ink': _BURMESE_INK, 'paper': _BURMESE_PAPER,
        'strokes': [
            [(32, 20), (26, 24), (22, 32), (22, 40), (26, 48), (34, 50), (38, 46), (40, 38), (40, 30), (36, 22), (32, 20)],
        ],
    },
    # 27. Ra - circle open at right
    {
        'name': 'Ra', 'script': 'BURMESE', 'concept': 'Ra',
        'origin': 'MYANMAR ~1050 AD',
        'ink': _BURMESE_INK, 'paper': _BURMESE_PAPER,
        'strokes': [
            [(38, 24), (30, 22), (22, 26), (20, 34), (22, 42), (30, 46), (38, 44)],
            [(38, 44), (44, 40)],
        ],
    },
    # 28. La - circle with bottom-right curl out
    {
        'name': 'La', 'script': 'BURMESE', 'concept': 'La',
        'origin': 'MYANMAR ~1050 AD',
        'ink': _BURMESE_INK, 'paper': _BURMESE_PAPER,
        'strokes': [
            [(32, 22), (24, 26), (20, 34), (24, 42), (32, 46), (40, 42), (42, 34), (38, 26), (32, 22)],
            [(40, 42), (44, 46), (44, 50)],
        ],
    },
    # 29. Wa - circle with right bump
    {
        'name': 'Wa', 'script': 'BURMESE', 'concept': 'Wa',
        'origin': 'MYANMAR ~1050 AD',
        'ink': _BURMESE_INK, 'paper': _BURMESE_PAPER,
        'strokes': [
            [(30, 22), (22, 26), (20, 34), (22, 42), (30, 46), (38, 42), (40, 34), (38, 26), (30, 22)],
            [(40, 34), (44, 36), (44, 30), (40, 28)],
        ],
    },
    # 30. Tha - circle with top-left notch
    {
        'name': 'Tha', 'script': 'BURMESE', 'concept': 'Tha',
        'origin': 'MYANMAR ~1050 AD',
        'ink': _BURMESE_INK, 'paper': _BURMESE_PAPER,
        'strokes': [
            [(26, 24), (22, 30), (20, 38), (24, 44), (32, 48), (40, 44), (42, 36), (40, 28), (34, 22)],
            [(26, 24), (24, 20)],
            [(34, 22), (36, 20)],
        ],
    },
    # 31. Ha - circle with top crossbar
    {
        'name': 'Ha', 'script': 'BURMESE', 'concept': 'Ha',
        'origin': 'MYANMAR ~1050 AD',
        'ink': _BURMESE_INK, 'paper': _BURMESE_PAPER,
        'strokes': [
            [(20, 24), (42, 24)],
            [(26, 24), (20, 30), (20, 38), (24, 44), (32, 48), (40, 44), (42, 38), (42, 30), (36, 24)],
        ],
    },
    # 32. Lla - two stacked circles
    {
        'name': 'Lla', 'script': 'BURMESE', 'concept': 'Lla',
        'origin': 'MYANMAR ~1050 AD',
        'ink': _BURMESE_INK, 'paper': _BURMESE_PAPER,
        'strokes': [
            [(30, 20), (24, 22), (22, 28), (26, 32), (32, 32), (36, 28), (34, 22), (30, 20)],
            [(30, 34), (24, 36), (22, 42), (26, 48), (32, 48), (36, 44), (34, 38), (30, 34)],
        ],
    },
    # 33. A - large circle with inner vertical
    {
        'name': 'A', 'script': 'BURMESE', 'concept': 'A',
        'origin': 'MYANMAR ~1050 AD',
        'ink': _BURMESE_INK, 'paper': _BURMESE_PAPER,
        'strokes': [
            [(32, 20), (24, 24), (20, 32), (22, 42), (30, 48), (38, 44), (42, 36), (40, 26), (32, 20)],
            [(32, 20), (32, 34)],
        ],
    },
]

# =====================================================================
# KHMER  (33 consonants)
# One of the most ornate scripts - elaborate curves, serifs, loops.
# Many letters have a distinctive "hair" (serif) at top.
# Stroke zone: roughly x=18-46, y=20-50
# =====================================================================

KHMER_CHARS = [
    # 1. Ko
    {
        'name': 'Ko', 'script': 'KHMER', 'concept': 'Ko',
        'origin': 'KHMER ~600 AD',
        'ink': _KHMER_INK, 'paper': _KHMER_PAPER,
        'strokes': [
            [(24, 20), (24, 46)],
            [(24, 20), (28, 22), (30, 20)],
            [(24, 30), (30, 28), (36, 30), (38, 36), (36, 42), (28, 44)],
        ],
    },
    # 2. Kho
    {
        'name': 'Kho', 'script': 'KHMER', 'concept': 'Kho',
        'origin': 'KHMER ~600 AD',
        'ink': _KHMER_INK, 'paper': _KHMER_PAPER,
        'strokes': [
            [(22, 20), (22, 48)],
            [(22, 20), (26, 22), (28, 20)],
            [(22, 28), (28, 26), (34, 28), (38, 34), (36, 40), (28, 42)],
            [(38, 34), (42, 30), (44, 34), (42, 38)],
        ],
    },
    # 3. Ko_2
    {
        'name': 'Ko_2', 'script': 'KHMER', 'concept': 'Ko (2nd series)',
        'origin': 'KHMER ~600 AD',
        'ink': _KHMER_INK, 'paper': _KHMER_PAPER,
        'strokes': [
            [(24, 20), (24, 48)],
            [(24, 28), (32, 26), (38, 30), (40, 38), (36, 44), (28, 46)],
            [(24, 20), (28, 22), (30, 20)],
        ],
    },
    # 4. Kho_2
    {
        'name': 'Kho_2', 'script': 'KHMER', 'concept': 'Kho (2nd series)',
        'origin': 'KHMER ~600 AD',
        'ink': _KHMER_INK, 'paper': _KHMER_PAPER,
        'strokes': [
            [(22, 20), (22, 48)],
            [(22, 20), (26, 22), (28, 20)],
            [(22, 30), (30, 26), (38, 30), (40, 38), (36, 44), (28, 46), (22, 44)],
            [(40, 38), (44, 36)],
        ],
    },
    # 5. Ngo
    {
        'name': 'Ngo', 'script': 'KHMER', 'concept': 'Ngo',
        'origin': 'KHMER ~600 AD',
        'ink': _KHMER_INK, 'paper': _KHMER_PAPER,
        'strokes': [
            [(24, 20), (24, 48)],
            [(24, 20), (28, 22), (30, 20)],
            [(24, 32), (32, 28), (38, 32), (38, 40), (32, 44), (24, 42)],
            [(32, 44), (32, 48)],
        ],
    },
    # 6. Cho
    {
        'name': 'Cho', 'script': 'KHMER', 'concept': 'Cho',
        'origin': 'KHMER ~600 AD',
        'ink': _KHMER_INK, 'paper': _KHMER_PAPER,
        'strokes': [
            [(22, 20), (22, 48)],
            [(22, 20), (26, 22), (28, 20)],
            [(22, 28), (32, 24), (40, 28), (42, 36), (38, 42), (30, 44), (22, 40)],
        ],
    },
    # 7. Chho
    {
        'name': 'Chho', 'script': 'KHMER', 'concept': 'Chho',
        'origin': 'KHMER ~600 AD',
        'ink': _KHMER_INK, 'paper': _KHMER_PAPER,
        'strokes': [
            [(24, 20), (24, 48)],
            [(24, 20), (28, 22), (30, 20)],
            [(24, 26), (32, 24), (38, 28), (40, 34)],
            [(40, 34), (38, 40), (30, 44), (24, 42)],
            [(40, 34), (44, 32), (44, 38)],
        ],
    },
    # 8. Cho_2
    {
        'name': 'Cho_2', 'script': 'KHMER', 'concept': 'Cho (2nd series)',
        'origin': 'KHMER ~600 AD',
        'ink': _KHMER_INK, 'paper': _KHMER_PAPER,
        'strokes': [
            [(22, 20), (22, 48)],
            [(22, 20), (26, 22), (28, 20)],
            [(22, 30), (30, 26), (38, 30), (38, 38), (30, 42), (22, 40)],
            [(38, 38), (42, 42), (40, 46)],
        ],
    },
    # 9. Chho_2
    {
        'name': 'Chho_2', 'script': 'KHMER', 'concept': 'Chho (2nd series)',
        'origin': 'KHMER ~600 AD',
        'ink': _KHMER_INK, 'paper': _KHMER_PAPER,
        'strokes': [
            [(24, 20), (24, 48)],
            [(24, 20), (28, 22), (30, 20)],
            [(24, 28), (34, 24), (42, 28), (44, 36), (40, 42), (30, 44)],
            [(30, 44), (24, 42)],
        ],
    },
    # 10. Nyo
    {
        'name': 'Nyo', 'script': 'KHMER', 'concept': 'Nyo',
        'origin': 'KHMER ~600 AD',
        'ink': _KHMER_INK, 'paper': _KHMER_PAPER,
        'strokes': [
            [(22, 20), (22, 48)],
            [(22, 20), (26, 22), (28, 20)],
            [(22, 30), (28, 28), (34, 30), (34, 38), (28, 40), (22, 38)],
            [(34, 30), (40, 28), (44, 32), (42, 36), (38, 38)],
        ],
    },
    # 11. Do
    {
        'name': 'Do', 'script': 'KHMER', 'concept': 'Do',
        'origin': 'KHMER ~600 AD',
        'ink': _KHMER_INK, 'paper': _KHMER_PAPER,
        'strokes': [
            [(24, 20), (24, 48)],
            [(24, 20), (28, 22), (30, 20)],
            [(24, 26), (30, 24), (36, 28), (36, 38), (30, 44), (24, 46)],
        ],
    },
    # 12. Tho
    {
        'name': 'Tho', 'script': 'KHMER', 'concept': 'Tho',
        'origin': 'KHMER ~600 AD',
        'ink': _KHMER_INK, 'paper': _KHMER_PAPER,
        'strokes': [
            [(22, 20), (22, 48)],
            [(22, 20), (26, 22), (28, 20)],
            [(22, 28), (30, 24), (38, 28), (40, 36), (36, 44), (26, 46)],
            [(40, 36), (44, 34), (46, 38)],
        ],
    },
    # 13. Do_2
    {
        'name': 'Do_2', 'script': 'KHMER', 'concept': 'Do (2nd series)',
        'origin': 'KHMER ~600 AD',
        'ink': _KHMER_INK, 'paper': _KHMER_PAPER,
        'strokes': [
            [(24, 20), (24, 48)],
            [(24, 20), (28, 22), (30, 20)],
            [(24, 30), (32, 26), (40, 30), (42, 38), (38, 44), (28, 46)],
            [(28, 46), (24, 48)],
        ],
    },
    # 14. Tho_2
    {
        'name': 'Tho_2', 'script': 'KHMER', 'concept': 'Tho (2nd series)',
        'origin': 'KHMER ~600 AD',
        'ink': _KHMER_INK, 'paper': _KHMER_PAPER,
        'strokes': [
            [(22, 20), (22, 48)],
            [(22, 20), (26, 22), (28, 20)],
            [(22, 26), (30, 22), (38, 26), (42, 34), (38, 42), (28, 46), (22, 44)],
            [(42, 34), (46, 30)],
        ],
    },
    # 15. No
    {
        'name': 'No', 'script': 'KHMER', 'concept': 'No',
        'origin': 'KHMER ~600 AD',
        'ink': _KHMER_INK, 'paper': _KHMER_PAPER,
        'strokes': [
            [(24, 20), (24, 48)],
            [(24, 20), (28, 22), (30, 20)],
            [(24, 30), (30, 28), (36, 30), (38, 36), (36, 42), (30, 44), (24, 42)],
        ],
    },
    # 16. To
    {
        'name': 'To', 'script': 'KHMER', 'concept': 'To',
        'origin': 'KHMER ~600 AD',
        'ink': _KHMER_INK, 'paper': _KHMER_PAPER,
        'strokes': [
            [(22, 20), (22, 48)],
            [(22, 20), (26, 22), (28, 20)],
            [(22, 32), (28, 28), (36, 30), (40, 36), (38, 44), (28, 48)],
            [(22, 48), (28, 48)],
        ],
    },
    # 17. Tho_3
    {
        'name': 'Tho_3', 'script': 'KHMER', 'concept': 'Tho (3rd)',
        'origin': 'KHMER ~600 AD',
        'ink': _KHMER_INK, 'paper': _KHMER_PAPER,
        'strokes': [
            [(24, 20), (24, 48)],
            [(24, 20), (28, 22), (30, 20)],
            [(24, 28), (32, 24), (40, 28), (42, 36), (38, 44), (28, 48)],
            [(38, 44), (42, 46), (44, 44)],
        ],
    },
    # 18. To_2
    {
        'name': 'To_2', 'script': 'KHMER', 'concept': 'To (2nd series)',
        'origin': 'KHMER ~600 AD',
        'ink': _KHMER_INK, 'paper': _KHMER_PAPER,
        'strokes': [
            [(22, 20), (22, 48)],
            [(22, 20), (26, 22), (28, 20)],
            [(22, 30), (30, 26), (38, 30), (40, 38), (36, 46), (28, 48)],
        ],
    },
    # 19. Tho_4
    {
        'name': 'Tho_4', 'script': 'KHMER', 'concept': 'Tho (4th)',
        'origin': 'KHMER ~600 AD',
        'ink': _KHMER_INK, 'paper': _KHMER_PAPER,
        'strokes': [
            [(24, 20), (24, 48)],
            [(24, 20), (28, 22), (30, 20)],
            [(24, 26), (34, 22), (42, 28), (44, 38), (38, 46), (28, 48)],
            [(44, 38), (46, 42)],
        ],
    },
    # 20. No_2
    {
        'name': 'No_2', 'script': 'KHMER', 'concept': 'No (2nd series)',
        'origin': 'KHMER ~600 AD',
        'ink': _KHMER_INK, 'paper': _KHMER_PAPER,
        'strokes': [
            [(22, 20), (22, 48)],
            [(22, 20), (26, 22), (28, 20)],
            [(22, 32), (28, 28), (36, 32), (36, 40), (28, 44), (22, 42)],
            [(36, 40), (40, 44), (40, 48)],
        ],
    },
    # 21. Bo
    {
        'name': 'Bo', 'script': 'KHMER', 'concept': 'Bo',
        'origin': 'KHMER ~600 AD',
        'ink': _KHMER_INK, 'paper': _KHMER_PAPER,
        'strokes': [
            [(24, 20), (24, 48)],
            [(24, 20), (28, 22), (30, 20)],
            [(24, 28), (32, 26), (38, 30), (36, 38), (28, 40)],
            [(28, 40), (36, 42), (38, 48)],
        ],
    },
    # 22. Pho
    {
        'name': 'Pho', 'script': 'KHMER', 'concept': 'Pho',
        'origin': 'KHMER ~600 AD',
        'ink': _KHMER_INK, 'paper': _KHMER_PAPER,
        'strokes': [
            [(22, 20), (22, 48)],
            [(22, 20), (26, 22), (28, 20)],
            [(22, 28), (30, 24), (38, 28), (40, 36), (36, 42), (26, 44)],
            [(40, 36), (44, 34), (46, 38), (44, 42)],
        ],
    },
    # 23. Bo_2
    {
        'name': 'Bo_2', 'script': 'KHMER', 'concept': 'Bo (2nd series)',
        'origin': 'KHMER ~600 AD',
        'ink': _KHMER_INK, 'paper': _KHMER_PAPER,
        'strokes': [
            [(24, 20), (24, 48)],
            [(24, 20), (28, 22), (30, 20)],
            [(24, 30), (32, 26), (40, 30), (42, 38), (36, 44), (28, 46)],
        ],
    },
    # 24. Pho_2
    {
        'name': 'Pho_2', 'script': 'KHMER', 'concept': 'Pho (2nd series)',
        'origin': 'KHMER ~600 AD',
        'ink': _KHMER_INK, 'paper': _KHMER_PAPER,
        'strokes': [
            [(22, 20), (22, 48)],
            [(22, 20), (26, 22), (28, 20)],
            [(22, 26), (30, 22), (40, 26), (44, 34), (40, 42), (30, 46), (22, 44)],
        ],
    },
    # 25. Mo
    {
        'name': 'Mo', 'script': 'KHMER', 'concept': 'Mo',
        'origin': 'KHMER ~600 AD',
        'ink': _KHMER_INK, 'paper': _KHMER_PAPER,
        'strokes': [
            [(24, 20), (24, 48)],
            [(24, 20), (28, 22), (30, 20)],
            [(24, 28), (30, 26), (36, 28), (38, 34), (36, 38), (30, 40), (24, 38)],
            [(36, 38), (40, 42), (38, 48)],
        ],
    },
    # 26. Yo
    {
        'name': 'Yo', 'script': 'KHMER', 'concept': 'Yo',
        'origin': 'KHMER ~600 AD',
        'ink': _KHMER_INK, 'paper': _KHMER_PAPER,
        'strokes': [
            [(22, 20), (22, 48)],
            [(22, 20), (26, 22), (28, 20)],
            [(22, 30), (30, 26), (36, 30), (36, 40), (30, 44), (22, 42)],
            [(22, 48), (30, 48)],
        ],
    },
    # 27. Ro
    {
        'name': 'Ro', 'script': 'KHMER', 'concept': 'Ro',
        'origin': 'KHMER ~600 AD',
        'ink': _KHMER_INK, 'paper': _KHMER_PAPER,
        'strokes': [
            [(24, 20), (24, 48)],
            [(24, 20), (28, 22), (30, 20)],
            [(24, 30), (32, 28), (38, 32), (38, 40), (32, 44), (24, 42)],
            [(38, 32), (42, 28), (44, 32)],
        ],
    },
    # 28. Lo
    {
        'name': 'Lo', 'script': 'KHMER', 'concept': 'Lo',
        'origin': 'KHMER ~600 AD',
        'ink': _KHMER_INK, 'paper': _KHMER_PAPER,
        'strokes': [
            [(22, 20), (22, 48)],
            [(22, 20), (26, 22), (28, 20)],
            [(22, 28), (28, 26), (34, 28), (38, 34), (36, 42), (28, 46), (22, 44)],
        ],
    },
    # 29. Vo
    {
        'name': 'Vo', 'script': 'KHMER', 'concept': 'Vo',
        'origin': 'KHMER ~600 AD',
        'ink': _KHMER_INK, 'paper': _KHMER_PAPER,
        'strokes': [
            [(24, 20), (24, 48)],
            [(24, 20), (28, 22), (30, 20)],
            [(24, 30), (30, 26), (38, 30), (40, 38), (34, 44), (24, 46)],
            [(40, 38), (44, 40), (44, 46)],
        ],
    },
    # 30. Sho
    {
        'name': 'Sho', 'script': 'KHMER', 'concept': 'Sho',
        'origin': 'KHMER ~600 AD',
        'ink': _KHMER_INK, 'paper': _KHMER_PAPER,
        'strokes': [
            [(22, 20), (22, 48)],
            [(22, 20), (26, 22), (28, 20)],
            [(22, 26), (32, 22), (40, 26), (42, 34), (38, 40), (28, 42)],
            [(28, 42), (34, 46), (40, 44)],
        ],
    },
    # 31. So
    {
        'name': 'So', 'script': 'KHMER', 'concept': 'So',
        'origin': 'KHMER ~600 AD',
        'ink': _KHMER_INK, 'paper': _KHMER_PAPER,
        'strokes': [
            [(24, 20), (24, 48)],
            [(24, 20), (28, 22), (30, 20)],
            [(24, 28), (34, 24), (42, 28), (44, 36), (40, 44), (30, 48)],
        ],
    },
    # 32. Ho
    {
        'name': 'Ho', 'script': 'KHMER', 'concept': 'Ho',
        'origin': 'KHMER ~600 AD',
        'ink': _KHMER_INK, 'paper': _KHMER_PAPER,
        'strokes': [
            [(22, 20), (22, 48)],
            [(22, 20), (26, 22), (28, 20)],
            [(22, 28), (30, 24), (38, 28), (38, 38), (30, 42), (22, 40)],
            [(38, 38), (42, 42), (44, 38), (42, 34)],
        ],
    },
    # 33. Lo_2
    {
        'name': 'Lo_2', 'script': 'KHMER', 'concept': 'Lo (2nd)',
        'origin': 'KHMER ~600 AD',
        'ink': _KHMER_INK, 'paper': _KHMER_PAPER,
        'strokes': [
            [(24, 20), (24, 48)],
            [(24, 20), (28, 22), (30, 20)],
            [(24, 32), (32, 28), (40, 32), (42, 40), (36, 46), (28, 48)],
            [(42, 40), (46, 42)],
        ],
    },
]

# =====================================================================
# LAO  (27 consonants)
# Related to Thai but simpler and more rounded.
# Characteristic loops at head of letters.
# Stroke zone: roughly x=18-46, y=20-50
# =====================================================================

LAO_CHARS = [
    # 1. Ko
    {
        'name': 'Ko', 'script': 'LAO', 'concept': 'Ko',
        'origin': 'LAO ~1400 AD',
        'ink': _LAO_INK, 'paper': _LAO_PAPER,
        'strokes': [
            [(24, 24), (22, 22), (24, 20), (26, 22), (24, 24)],
            [(24, 24), (24, 40), (28, 46), (36, 46), (40, 40), (40, 34)],
        ],
    },
    # 2. Kho
    {
        'name': 'Kho', 'script': 'LAO', 'concept': 'Kho',
        'origin': 'LAO ~1400 AD',
        'ink': _LAO_INK, 'paper': _LAO_PAPER,
        'strokes': [
            [(24, 24), (22, 22), (24, 20), (26, 22), (24, 24)],
            [(24, 24), (24, 40), (28, 46), (36, 46), (40, 40)],
            [(40, 40), (44, 36), (42, 32)],
        ],
    },
    # 3. Kho_sung (high class)
    {
        'name': 'Kho_sung', 'script': 'LAO', 'concept': 'Kho (high)',
        'origin': 'LAO ~1400 AD',
        'ink': _LAO_INK, 'paper': _LAO_PAPER,
        'strokes': [
            [(26, 24), (24, 22), (26, 20), (28, 22), (26, 24)],
            [(26, 24), (26, 38), (30, 44), (38, 46), (42, 42)],
            [(42, 42), (44, 38), (42, 34), (38, 36)],
        ],
    },
    # 4. Ngo
    {
        'name': 'Ngo', 'script': 'LAO', 'concept': 'Ngo',
        'origin': 'LAO ~1400 AD',
        'ink': _LAO_INK, 'paper': _LAO_PAPER,
        'strokes': [
            [(28, 24), (26, 22), (28, 20), (30, 22), (28, 24)],
            [(28, 24), (28, 40), (32, 46), (38, 46), (42, 42), (42, 34)],
            [(42, 34), (40, 30), (36, 32)],
        ],
    },
    # 5. Cho
    {
        'name': 'Cho', 'script': 'LAO', 'concept': 'Cho',
        'origin': 'LAO ~1400 AD',
        'ink': _LAO_INK, 'paper': _LAO_PAPER,
        'strokes': [
            [(24, 24), (22, 22), (24, 20), (26, 22), (24, 24)],
            [(24, 24), (24, 36), (28, 42), (36, 44), (40, 38)],
            [(40, 38), (40, 46)],
        ],
    },
    # 6. So_1
    {
        'name': 'So_1', 'script': 'LAO', 'concept': 'So (1st)',
        'origin': 'LAO ~1400 AD',
        'ink': _LAO_INK, 'paper': _LAO_PAPER,
        'strokes': [
            [(26, 24), (24, 22), (26, 20), (28, 22), (26, 24)],
            [(26, 24), (26, 34), (30, 40), (36, 42), (40, 38), (40, 30)],
            [(40, 30), (38, 26), (34, 28)],
        ],
    },
    # 7. Nyo
    {
        'name': 'Nyo', 'script': 'LAO', 'concept': 'Nyo',
        'origin': 'LAO ~1400 AD',
        'ink': _LAO_INK, 'paper': _LAO_PAPER,
        'strokes': [
            [(24, 24), (22, 22), (24, 20), (26, 22), (24, 24)],
            [(24, 24), (24, 38), (28, 44), (34, 46), (40, 42), (42, 36)],
            [(42, 36), (44, 30), (42, 26), (38, 28)],
        ],
    },
    # 8. Do
    {
        'name': 'Do', 'script': 'LAO', 'concept': 'Do',
        'origin': 'LAO ~1400 AD',
        'ink': _LAO_INK, 'paper': _LAO_PAPER,
        'strokes': [
            [(28, 24), (26, 22), (28, 20), (30, 22), (28, 24)],
            [(28, 24), (28, 36), (32, 44), (40, 46), (44, 40), (44, 32)],
        ],
    },
    # 9. To
    {
        'name': 'To', 'script': 'LAO', 'concept': 'To',
        'origin': 'LAO ~1400 AD',
        'ink': _LAO_INK, 'paper': _LAO_PAPER,
        'strokes': [
            [(26, 24), (24, 22), (26, 20), (28, 22), (26, 24)],
            [(26, 24), (26, 36), (30, 44), (38, 46), (42, 42)],
            [(42, 42), (42, 48)],
        ],
    },
    # 10. Tho_sung (high class)
    {
        'name': 'Tho_sung', 'script': 'LAO', 'concept': 'Tho (high)',
        'origin': 'LAO ~1400 AD',
        'ink': _LAO_INK, 'paper': _LAO_PAPER,
        'strokes': [
            [(24, 24), (22, 22), (24, 20), (26, 22), (24, 24)],
            [(24, 24), (24, 38), (28, 46), (36, 48), (42, 44), (44, 38)],
            [(44, 38), (44, 30), (40, 26)],
        ],
    },
    # 11. Tho
    {
        'name': 'Tho', 'script': 'LAO', 'concept': 'Tho',
        'origin': 'LAO ~1400 AD',
        'ink': _LAO_INK, 'paper': _LAO_PAPER,
        'strokes': [
            [(26, 24), (24, 22), (26, 20), (28, 22), (26, 24)],
            [(26, 24), (26, 36), (30, 42), (38, 44), (42, 38), (40, 30)],
        ],
    },
    # 12. No
    {
        'name': 'No', 'script': 'LAO', 'concept': 'No',
        'origin': 'LAO ~1400 AD',
        'ink': _LAO_INK, 'paper': _LAO_PAPER,
        'strokes': [
            [(28, 24), (26, 22), (28, 20), (30, 22), (28, 24)],
            [(28, 24), (28, 38), (32, 46), (40, 48), (44, 42)],
            [(44, 42), (44, 36), (40, 34)],
        ],
    },
    # 13. Bo
    {
        'name': 'Bo', 'script': 'LAO', 'concept': 'Bo',
        'origin': 'LAO ~1400 AD',
        'ink': _LAO_INK, 'paper': _LAO_PAPER,
        'strokes': [
            [(24, 24), (22, 22), (24, 20), (26, 22), (24, 24)],
            [(24, 24), (24, 36), (28, 44), (36, 46), (42, 42), (44, 34)],
            [(44, 34), (42, 28), (36, 28)],
        ],
    },
    # 14. Po
    {
        'name': 'Po', 'script': 'LAO', 'concept': 'Po',
        'origin': 'LAO ~1400 AD',
        'ink': _LAO_INK, 'paper': _LAO_PAPER,
        'strokes': [
            [(26, 24), (24, 22), (26, 20), (28, 22), (26, 24)],
            [(26, 24), (26, 40), (30, 46), (38, 48), (42, 44), (42, 36)],
        ],
    },
    # 15. Pho_sung (high class)
    {
        'name': 'Pho_sung', 'script': 'LAO', 'concept': 'Pho (high)',
        'origin': 'LAO ~1400 AD',
        'ink': _LAO_INK, 'paper': _LAO_PAPER,
        'strokes': [
            [(24, 24), (22, 22), (24, 20), (26, 22), (24, 24)],
            [(24, 24), (24, 38), (28, 44), (36, 46), (42, 42)],
            [(42, 42), (46, 38), (44, 32), (40, 34)],
        ],
    },
    # 16. Fo
    {
        'name': 'Fo', 'script': 'LAO', 'concept': 'Fo',
        'origin': 'LAO ~1400 AD',
        'ink': _LAO_INK, 'paper': _LAO_PAPER,
        'strokes': [
            [(28, 24), (26, 22), (28, 20), (30, 22), (28, 24)],
            [(28, 24), (28, 36), (32, 44), (40, 46), (44, 40)],
            [(44, 40), (44, 48)],
        ],
    },
    # 17. Pho
    {
        'name': 'Pho', 'script': 'LAO', 'concept': 'Pho',
        'origin': 'LAO ~1400 AD',
        'ink': _LAO_INK, 'paper': _LAO_PAPER,
        'strokes': [
            [(24, 24), (22, 22), (24, 20), (26, 22), (24, 24)],
            [(24, 24), (24, 40), (28, 48), (36, 48), (42, 44), (44, 36), (42, 28)],
        ],
    },
    # 18. Mo
    {
        'name': 'Mo', 'script': 'LAO', 'concept': 'Mo',
        'origin': 'LAO ~1400 AD',
        'ink': _LAO_INK, 'paper': _LAO_PAPER,
        'strokes': [
            [(26, 24), (24, 22), (26, 20), (28, 22), (26, 24)],
            [(26, 24), (26, 36), (30, 44), (38, 46), (44, 42), (44, 34), (40, 28), (34, 30)],
        ],
    },
    # 19. Yo
    {
        'name': 'Yo', 'script': 'LAO', 'concept': 'Yo',
        'origin': 'LAO ~1400 AD',
        'ink': _LAO_INK, 'paper': _LAO_PAPER,
        'strokes': [
            [(24, 24), (22, 22), (24, 20), (26, 22), (24, 24)],
            [(24, 24), (24, 42), (28, 48), (36, 48), (40, 44)],
            [(40, 44), (40, 34), (36, 30)],
        ],
    },
    # 20. Ro
    {
        'name': 'Ro', 'script': 'LAO', 'concept': 'Ro',
        'origin': 'LAO ~1400 AD',
        'ink': _LAO_INK, 'paper': _LAO_PAPER,
        'strokes': [
            [(28, 24), (26, 22), (28, 20), (30, 22), (28, 24)],
            [(28, 24), (28, 38), (32, 44), (38, 44), (42, 40)],
        ],
    },
    # 21. Lo
    {
        'name': 'Lo', 'script': 'LAO', 'concept': 'Lo',
        'origin': 'LAO ~1400 AD',
        'ink': _LAO_INK, 'paper': _LAO_PAPER,
        'strokes': [
            [(26, 24), (24, 22), (26, 20), (28, 22), (26, 24)],
            [(26, 24), (26, 38), (30, 46), (38, 48), (44, 44), (44, 36)],
        ],
    },
    # 22. Wo
    {
        'name': 'Wo', 'script': 'LAO', 'concept': 'Wo',
        'origin': 'LAO ~1400 AD',
        'ink': _LAO_INK, 'paper': _LAO_PAPER,
        'strokes': [
            [(24, 24), (22, 22), (24, 20), (26, 22), (24, 24)],
            [(24, 24), (24, 36), (28, 42), (36, 44), (42, 40), (42, 32), (38, 28)],
            [(42, 40), (44, 46)],
        ],
    },
    # 23. Ho_sung (high class)
    {
        'name': 'Ho_sung', 'script': 'LAO', 'concept': 'Ho (high)',
        'origin': 'LAO ~1400 AD',
        'ink': _LAO_INK, 'paper': _LAO_PAPER,
        'strokes': [
            [(26, 24), (24, 22), (26, 20), (28, 22), (26, 24)],
            [(26, 24), (26, 34), (30, 42), (38, 44), (44, 40), (44, 32)],
            [(44, 32), (42, 28), (38, 30)],
        ],
    },
    # 24. O
    {
        'name': 'O', 'script': 'LAO', 'concept': 'O',
        'origin': 'LAO ~1400 AD',
        'ink': _LAO_INK, 'paper': _LAO_PAPER,
        'strokes': [
            [(28, 24), (26, 22), (28, 20), (30, 22), (28, 24)],
            [(28, 24), (28, 38), (32, 46), (40, 48), (44, 42), (44, 34), (40, 28), (32, 28)],
        ],
    },
    # 25. Ho
    {
        'name': 'Ho', 'script': 'LAO', 'concept': 'Ho',
        'origin': 'LAO ~1400 AD',
        'ink': _LAO_INK, 'paper': _LAO_PAPER,
        'strokes': [
            [(24, 24), (22, 22), (24, 20), (26, 22), (24, 24)],
            [(24, 24), (24, 40), (28, 46), (36, 48), (42, 44), (42, 34)],
            [(42, 34), (40, 30), (36, 32)],
        ],
    },
    # 26. Ho_tam (low class)
    {
        'name': 'Ho_tam', 'script': 'LAO', 'concept': 'Ho (low)',
        'origin': 'LAO ~1400 AD',
        'ink': _LAO_INK, 'paper': _LAO_PAPER,
        'strokes': [
            [(26, 24), (24, 22), (26, 20), (28, 22), (26, 24)],
            [(26, 24), (26, 38), (30, 44), (38, 46), (42, 42)],
            [(42, 42), (46, 40), (44, 34), (40, 36)],
        ],
    },
    # 27. Fo_tam (low class)
    {
        'name': 'Fo_tam', 'script': 'LAO', 'concept': 'Fo (low)',
        'origin': 'LAO ~1400 AD',
        'ink': _LAO_INK, 'paper': _LAO_PAPER,
        'strokes': [
            [(24, 24), (22, 22), (24, 20), (26, 22), (24, 24)],
            [(24, 24), (24, 36), (28, 44), (36, 48), (42, 44), (44, 38), (42, 32)],
            [(44, 38), (46, 42)],
        ],
    },
]


# ── Verification ─────────────────────────────────────────────────────
if __name__ == '__main__':
    for name, chars in [('BURMESE', BURMESE_CHARS), ('KHMER', KHMER_CHARS), ('LAO', LAO_CHARS)]:
        print(f'{name}: {len(chars)} chars')
        for ch in chars:
            for si, stroke in enumerate(ch['strokes']):
                for x, y in stroke:
                    assert 8 <= x <= 56 and 14 <= y <= 56, f"OOB: {ch['name']} ({x},{y})"
    print('All OK')
