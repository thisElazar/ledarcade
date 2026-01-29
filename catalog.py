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

from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any
from arcade import Colors


@dataclass
class Category:
    """A category/page in the menu system."""
    name: str
    color: Tuple[int, int, int]
    key: str = ""  # Lookup key used by game/visual classes
    items: List[Any] = field(default_factory=list)

    def add(self, item_class):
        """Add an item and keep sorted alphabetically by name."""
        self.items.append(item_class)
        self.items.sort(key=lambda x: x.name.upper())

    def __len__(self):
        return len(self.items)


# Game categories
GAME_CATEGORIES = [
    Category("ARCADE GAMES", Colors.YELLOW, "arcade"),
    Category("RETRO GAMES", Colors.GREEN, "retro"),
    Category("MODERN GAMES", Colors.CYAN, "modern"),
    Category("2 PLAYER GAMES", Colors.MAGENTA, "2_player"),
]

# Visual categories
VISUAL_CATEGORIES = [
    Category("AUTOMATA", Colors.MAGENTA, "automata"),
    Category("NATURE", Colors.GREEN, "nature"),
    Category("DIGITAL", Colors.CYAN, "digital"),
    Category("ART", Colors.YELLOW, "art"),
    Category("SPRITES", Colors.LIME, "sprites"),
    Category("HOUSEHOLD", Colors.ORANGE, "household"),
    Category("UTILITY", Colors.WHITE, "utility"),
]

# Category key to object mapping for easy lookup
GAME_CATEGORY_MAP: Dict[str, Category] = {cat.key: cat for cat in GAME_CATEGORIES}
VISUAL_CATEGORY_MAP: Dict[str, Category] = {cat.key: cat for cat in VISUAL_CATEGORIES}


def register_games(game_classes):
    """Register game classes into their categories."""
    # Clear existing items
    for cat in GAME_CATEGORIES:
        cat.items = []

    for game_class in game_classes:
        category_key = getattr(game_class, 'category', 'arcade')
        if category_key in GAME_CATEGORY_MAP:
            GAME_CATEGORY_MAP[category_key].add(game_class)
        else:
            # Default to arcade if category not found
            GAME_CATEGORY_MAP['arcade'].add(game_class)


def register_visuals(visual_classes):
    """Register visual classes into their categories."""
    # Clear existing items
    for cat in VISUAL_CATEGORIES:
        cat.items = []

    for visual_class in visual_classes:
        category_key = getattr(visual_class, 'category', 'nature')
        if category_key in VISUAL_CATEGORY_MAP:
            VISUAL_CATEGORY_MAP[category_key].add(visual_class)
        else:
            # Default to nature if category not found
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
