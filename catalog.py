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


# Game categories
GAME_CATEGORIES = [
    Category("ARCADE GAMES", Colors.YELLOW, "arcade"),
    Category("RETRO GAMES", Colors.GREEN, "retro"),
    Category("MODERN GAMES", Colors.CYAN, "modern"),
    Category("TOYS", Colors.PINK, "toys"),
    Category("2 PLAYER GAMES", Colors.MAGENTA, "2_player"),
    Category("BAR GAMES", (200, 150, 50), "bar"),
    Category("UNIQUE GAMES", (100, 255, 180), "unique"),
    Category("GAME MIX", Colors.ORANGE, "game_mix"),
]

# Visual categories
VISUAL_CATEGORIES = [
    Category("ART", Colors.YELLOW, "art"),
    Category("AUTOMATA", Colors.MAGENTA, "automata"),
    Category("DEMOS", (255, 100, 100), "demos"),
    Category("DIGITAL", Colors.CYAN, "digital"),
    Category("GALLERY", (180, 150, 50), "gallery"),
    Category("COOKING", (120, 160, 100), "cooking"),
    Category("HOUSEHOLD", Colors.ORANGE, "household"),
    Category("MECHANICS", Colors.PURPLE, "mechanics"),
    Category("MUSIC", (255, 180, 50), "music"),
    Category("OUTDOORS", Colors.GREEN, "nature"),
    Category("ROAD+RAIL", (255, 160, 0), "road_rail"),
    Category("SCIENCE", Colors.BLUE, "science"),
    Category("SPRITES", Colors.LIME, "sprites"),
    Category("SUPERHEROES", Colors.RED, "superheroes"),
    Category("TITLES", (200, 180, 255), "titles"),
    Category("VISUAL MIX", (100, 255, 100), "visual_mix"),
    Category("UTILITY", Colors.WHITE, "utility"),      # Always last
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
