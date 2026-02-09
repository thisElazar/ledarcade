#!/usr/bin/env python3
"""Generate catalog.json for the web emulator by scanning game/visual source files.

Matches the arcade machine's catalog.py registration logic:
  - Resolves category inheritance (subclasses inherit parent's category)
  - Skips abstract base classes (GamePlaylist, Slideshow)
  - Skips dev_only classes (hidden on production arcade)
"""

import ast
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Category definitions matching catalog.py exactly
GAME_CATEGORIES = [
    {"name": "ARCADE GAMES", "color": [255, 255, 0], "key": "arcade"},
    {"name": "RETRO GAMES", "color": [0, 255, 0], "key": "retro"},
    {"name": "MODERN GAMES", "color": [0, 255, 255], "key": "modern"},
    {"name": "TOYS", "color": [255, 128, 128], "key": "toys"},
    {"name": "2 PLAYER GAMES", "color": [255, 0, 255], "key": "2_player"},
    {"name": "BAR GAMES", "color": [200, 150, 50], "key": "bar"},
    {"name": "UNIQUE GAMES", "color": [100, 255, 180], "key": "unique"},
    {"name": "GAME MIX", "color": [255, 128, 0], "key": "game_mix"},
]

VISUAL_CATEGORIES = [
    {"name": "ART", "color": [255, 255, 0], "key": "art"},
    {"name": "AUTOMATA", "color": [255, 0, 255], "key": "automata"},
    {"name": "DEMOS", "color": [255, 100, 100], "key": "demos"},
    {"name": "DIGITAL", "color": [0, 255, 255], "key": "digital"},
    {"name": "GALLERY", "color": [180, 150, 50], "key": "gallery"},
    {"name": "HOUSEHOLD", "color": [255, 128, 0], "key": "household"},
    {"name": "MECHANICS", "color": [128, 0, 255], "key": "mechanics"},
    {"name": "MUSIC", "color": [255, 180, 50], "key": "music"},
    {"name": "OUTDOORS", "color": [0, 255, 0], "key": "nature"},
    {"name": "ROAD+RAIL", "color": [255, 160, 0], "key": "road_rail"},
    {"name": "SCIENCE", "color": [0, 0, 255], "key": "science"},
    {"name": "SPRITES", "color": [128, 255, 0], "key": "sprites"},
    {"name": "SUPERHEROES", "color": [255, 0, 0], "key": "superheroes"},
    {"name": "TITLES", "color": [200, 180, 255], "key": "titles"},
    {"name": "VISUAL MIX", "color": [100, 255, 100], "key": "visual_mix"},
    {"name": "UTILITY", "color": [255, 255, 255], "key": "utility"},
]

# Base classes that aren't actual menu items (not in ALL_GAMES / ALL_VISUALS)
SKIP_CLASSES = {'GamePlaylist', 'Slideshow'}


def extract_string(node):
    """Extract string value from an AST Constant node."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def extract_bool(node):
    """Extract boolean value from an AST Constant node."""
    if isinstance(node, ast.Constant) and isinstance(node.value, bool):
        return node.value
    return None


def scan_file(filepath, pkg):
    """Scan a Python file for Game/Visual classes and cross-package deps.

    Resolves category inheritance: if a class doesn't set its own category,
    it inherits from its base class (matching runtime getattr behavior).
    """
    try:
        with open(filepath, 'r') as f:
            source = f.read()
        tree = ast.parse(source)
    except (SyntaxError, UnicodeDecodeError):
        return [], []

    deps = []

    # Detect cross-package imports (e.g. demos importing from games)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            other = 'games' if pkg == 'visuals' else 'visuals'
            if node.module.startswith(other + '.'):
                dep_path = node.module.replace('.', '/') + '.py'
                if dep_path not in deps:
                    deps.append(dep_path)

    # First pass: collect all classes with their attributes and bases
    class_info = {}
    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        if node.name.startswith('_'):
            continue

        # Get base class names (for same-file inheritance resolution)
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)

        name_val = None
        cat_val = None
        dev_only = False

        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        if target.id == 'name':
                            name_val = extract_string(item.value)
                        elif target.id == 'category':
                            cat_val = extract_string(item.value)
                        elif target.id == 'dev_only':
                            dev_only = extract_bool(item.value) or False

        if name_val:
            class_info[node.name] = {
                'cls': node.name,
                'name': name_val,
                'category': cat_val,
                'bases': bases,
                'dev_only': dev_only,
            }

    # Second pass: resolve category inheritance (walk up base chain)
    def resolve_category(cls_name, visited=None):
        if visited is None:
            visited = set()
        if cls_name in visited:
            return None
        visited.add(cls_name)
        info = class_info.get(cls_name)
        if not info:
            return None
        if info['category']:
            return info['category']
        for base_name in info['bases']:
            cat = resolve_category(base_name, visited)
            if cat:
                return cat
        return None

    for cls_name, info in class_info.items():
        if info['category'] is None:
            info['category'] = resolve_category(cls_name)

    # Build result list, skipping base classes and dev_only items
    classes = []
    for cls_name, info in class_info.items():
        if cls_name in SKIP_CLASSES:
            continue
        if info['dev_only']:
            continue
        classes.append({
            'cls': info['cls'],
            'name': info['name'],
            'category': info['category'],
        })

    return classes, deps


def main():
    items_by_cat = {}

    for pkg in ['games', 'visuals']:
        pkg_dir = os.path.join(ROOT, pkg)
        if not os.path.isdir(pkg_dir):
            continue

        is_game = pkg == 'games'
        default_cat = 'arcade' if is_game else 'nature'

        for fname in sorted(os.listdir(pkg_dir)):
            if not fname.endswith('.py') or fname.startswith('_'):
                continue

            filepath = os.path.join(pkg_dir, fname)
            module_path = f"{pkg}/{fname}"
            classes, deps = scan_file(filepath, pkg)

            for cls_info in classes:
                cat_key = cls_info['category'] or default_cat
                entry = {
                    'name': cls_info['name'],
                    'cls': cls_info['cls'],
                    'module': module_path,
                    'is_game': is_game,
                }
                if deps:
                    entry['deps'] = deps

                items_by_cat.setdefault(cat_key, []).append(entry)

    # Sort items within each category (numbers after letters, matching catalog.py)
    for items in items_by_cat.values():
        items.sort(key=lambda x: ('~' + x['name'].upper())
                   if x['name'][0].isdigit() else x['name'].upper())

    # Assemble categories in canonical order, skip empty ones
    categories = []
    for cat_def in GAME_CATEGORIES + VISUAL_CATEGORIES:
        key = cat_def['key']
        if key in items_by_cat:
            categories.append({
                'name': cat_def['name'],
                'color': cat_def['color'],
                'key': key,
                'items': items_by_cat[key],
            })

    out_path = os.path.join(ROOT, 'site', 'catalog.json')
    with open(out_path, 'w') as f:
        json.dump({'categories': categories}, f, indent=2)

    total = sum(len(c['items']) for c in categories)
    print(f"Generated {out_path}: {len(categories)} categories, {total} items")


if __name__ == '__main__':
    main()
