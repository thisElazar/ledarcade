"""
LED Arcade - Unified Catalog System
====================================
Category registry for games and visuals with alphabetized sorting.

Navigation:
  Left/Right - Switch category (page)
  Up/Down    - Select item within category
  Space      - Launch selected item
  Escape     - Back to menu / Exit
"""

import os
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any
from arcade import Colors

DEV_MODE = os.environ.get('LED_DEV', '') == '1'


@dataclass
class Category:
    """A category/page in the menu system."""
    name: str
    color: Tuple[int, int, int]
    key: str = ""  # Lookup key used by game/visual classes
    items: List[Any] = field(default_factory=list)

    def add(self, item_class):
        """Add an item and keep sorted alphabetically (numbers after letters)."""
        self.items.append(item_class)
        # Sort with numbers after letters: prefix digits with ~ (sorts after Z)
        self.items.sort(key=lambda x: ('~' + x.name.upper()) if x.name[0].isdigit() else x.name.upper())

    def __len__(self):
        return len(self.items)


# ── Color scheme ──────────────────────────────────────────────────
# Games: rainbow spectrum (R O Y G B P Pk) at s=0.85 v=0.90
# Visuals: family clusters — Creative (golds), Nature (greens),
#   Digital (cyans), Knowledge (blues), Mechanical (purples),
#   Domestic (pinks), Meta (desaturated)
# See docs or git log for full hue/family rationale.

# Game categories (chronological era → social → mix)
GAME_CATEGORIES = [
    Category("ARCADE GAMES",   (230, 35, 35),   "arcade"),     # 0° red
    Category("RETRO GAMES",    (230, 132, 35),   "retro"),     # 30° orange
    Category("MODERN GAMES",   (230, 197, 35),   "modern"),    # 50° yellow
    Category("TOYS",           (35, 230, 35),    "toys"),      # 120° green
    Category("BAR GAMES",      (35, 116, 230),   "bar"),       # 215° blue
    Category("2 PLAYER GAMES", (132, 35, 230),   "2_player"),  # 270° purple
    Category("UNIQUE GAMES",   (230, 35, 132),   "unique"),    # 330° pink
    Category("GAME MIX",       (195, 195, 210),  "game_mix"),  # desaturated
]

# Visual categories (alphabetical, VISUAL MIX + UTILITY last)
VISUAL_CATEGORIES = [
    # Creative family (golds, 40°-60°)
    Category("ART",         (224, 165, 45),  "art"),         # 40°
    # Digital family (cyans, 174°-186°)
    Category("AUTOMATA",    (65, 217, 200),  "automata"),    # 174°
    # Domestic family (pinks, 332°-344°)
    Category("COOKING",     (217, 65, 136),  "cooking"),     # 332°
    # Nature family (greens, 112°-126°)
    Category("CULTURE",     (65, 217, 85),   "culture"),     # 112°
    # Creative family
    Category("DEMOS",       (217, 191, 65),  "demos"),       # 50°
    # Digital family
    Category("DIGITAL",     (56, 208, 224),  "digital"),     # 186°
    # Meta (desaturated)
    Category("GALLERY",     (204, 194, 163), "gallery"),     # 45° low-sat
    # Domestic family
    Category("HOUSEHOLD",   (217, 65, 106),  "household"),   # 344°
    # Knowledge family (blues, 222°-250°)
    Category("MATH",        (56, 107, 224),  "math"),        # 222°
    # Mechanical family (purples, 280°-292°)
    Category("MECHANICS",   (166, 65, 217),  "mechanics"),   # 280°
    # Knowledge family
    Category("MUSIC",       (65, 75, 217),   "music"),       # 236°
    # Nature family
    Category("OUTDOORS",    (56, 224, 73),   "nature"),      # 126°
    # Mechanical family
    Category("ROAD+RAIL",   (197, 65, 217),  "road_rail"),   # 292°
    # Knowledge family
    Category("SCIENCE",     (75, 45, 224),   "science"),     # 250°
    # Optional / local-only
    Category("SPRITES",     (160, 217, 65),  "sprites"),     # 85°
    Category("SUPERHEROES", (230, 52, 35),   "superheroes"), # 5°
    # Creative family
    Category("TITLES",      (217, 217, 65),  "titles"),      # 60°
    # Meta (desaturated)
    Category("VISUAL MIX",  (173, 204, 194), "visual_mix"),  # 160° low-sat
    Category("UTILITY",     (204, 204, 204), "utility"),     # neutral gray
]

# Category key to object mapping for easy lookup
GAME_CATEGORY_MAP: Dict[str, Category] = {cat.key: cat for cat in GAME_CATEGORIES}
VISUAL_CATEGORY_MAP: Dict[str, Category] = {cat.key: cat for cat in VISUAL_CATEGORIES}


def register_games(game_classes):
    """Register game classes into their categories."""
    for cat in GAME_CATEGORIES:
        cat.items = []

    for game_class in game_classes:
        category_key = getattr(game_class, 'category', 'arcade')
        if category_key in GAME_CATEGORY_MAP:
            GAME_CATEGORY_MAP[category_key].add(game_class)
        else:
            GAME_CATEGORY_MAP['arcade'].add(game_class)


def register_visuals(visual_classes):
    """Register visual classes into their categories."""
    for cat in VISUAL_CATEGORIES:
        cat.items = []

    for visual_class in visual_classes:
        if not DEV_MODE and getattr(visual_class, 'dev_only', False):
            continue
        category_key = getattr(visual_class, 'category', 'nature')
        if category_key in VISUAL_CATEGORY_MAP:
            VISUAL_CATEGORY_MAP[category_key].add(visual_class)
        else:
            VISUAL_CATEGORY_MAP['nature'].add(visual_class)


def get_all_categories(mode='all'):
    """
    Get categories based on mode.
    mode: 'games', 'visuals', or 'all'
    """
    if mode == 'games':
        return [c for c in GAME_CATEGORIES if len(c) > 0]
    elif mode == 'visuals':
        return [c for c in VISUAL_CATEGORIES if len(c) > 0]
    else:
        # All categories - games first, then visuals
        all_cats = []
        all_cats.extend([c for c in GAME_CATEGORIES if len(c) > 0])
        all_cats.extend([c for c in VISUAL_CATEGORIES if len(c) > 0])
        return all_cats
