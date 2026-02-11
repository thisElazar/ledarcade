#!/usr/bin/env python3
"""Generate catalog.json for the web emulator by scanning game/visual source files.

Matches the arcade machine's catalog.py registration logic:
  - Only includes classes imported in each package's __init__.py
  - Resolves category inheritance (subclasses inherit parent's category)
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

def scan_exported_classes(pkg):
    """Parse __init__.py to find which classes are in ALL_GAMES / ALL_VISUALS.

    Returns a dict mapping module basename -> set of class names, e.g.
    {'turing': {'TuringPatterns'}, 'emfield': {'Coulomb'}, ...}
    Only classes registered in the ALL_* list will appear in the catalog,
    exactly matching the device's runtime registration.
    """
    init_path = os.path.join(ROOT, pkg, '__init__.py')
    try:
        with open(init_path, 'r') as f:
            tree = ast.parse(f.read())
    except (SyntaxError, FileNotFoundError):
        return None  # Fall back to including all classes

    # Step 1: build name -> module mapping from relative imports
    #   from .turing import TuringPatterns  =>  TuringPatterns -> turing
    name_to_module = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level >= 1 and node.module:
            mod = node.module.split('.')[0]
            for alias in node.names:
                imported_name = alias.asname or alias.name
                name_to_module[imported_name] = mod

    # Step 2: find ALL_GAMES or ALL_VISUALS list and extract names
    list_name = 'ALL_GAMES' if pkg == 'games' else 'ALL_VISUALS'
    registered_names = set()
    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == list_name:
                if isinstance(node.value, ast.List):
                    for elt in node.value.elts:
                        if isinstance(elt, ast.Name):
                            registered_names.add(elt.id)

    if not registered_names:
        return None  # Fall back if list not found

    # Step 3: build module -> set of registered class names
    exported = {}
    for cls_name in registered_names:
        mod = name_to_module.get(cls_name)
        if mod:
            exported.setdefault(mod, set()).add(cls_name)
    return exported


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


def scan_file(filepath, pkg, exported_classes=None):
    """Scan a Python file for Game/Visual classes and cross-package deps.

    If exported_classes is provided, only classes in that set are included.
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
    needs_numpy = False
    module_name = os.path.splitext(os.path.basename(filepath))[0]

    # Detect import dependencies (cross-package AND intra-package)
    for node in ast.walk(tree):
        # Detect numpy imports: import numpy / import numpy as np
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == 'numpy' or alias.name.startswith('numpy.'):
                    needs_numpy = True
        # Detect numpy imports: from numpy import ...
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module == 'numpy' or node.module.startswith('numpy.'):
                needs_numpy = True
            other = 'games' if pkg == 'visuals' else 'visuals'
            # Cross-package: visuals importing from games (or vice versa)
            if node.module.startswith(other + '.'):
                dep_path = node.module.replace('.', '/') + '.py'
                if dep_path not in deps:
                    deps.append(dep_path)
            # Intra-package: importing a sibling module (e.g. games.arkanoid_levels)
            elif node.module.startswith(pkg + '.'):
                sub = node.module[len(pkg) + 1:]
                if sub != module_name:  # skip self-imports
                    dep_path = pkg + '/' + sub + '.py'
                    if dep_path not in deps:
                        deps.append(dep_path)
        # Relative sibling import: from .foo import ... (level >= 1, module set)
        if (isinstance(node, ast.ImportFrom) and node.level >= 1
                and node.module and node.module != module_name):
            dep_path = pkg + '/' + node.module + '.py'
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

    # Build result list, filtering to exported classes and skipping dev_only
    classes = []
    for cls_name, info in class_info.items():
        if exported_classes is not None and cls_name not in exported_classes:
            continue
        if info['dev_only']:
            continue
        classes.append({
            'cls': info['cls'],
            'name': info['name'],
            'category': info['category'],
        })

    return classes, deps, needs_numpy


def scan_painting_entries():
    """Generate catalog entries for dynamically-created painting visuals.

    painting.py creates classes at runtime via type(), which the AST scanner
    can't see. This reads PAINTING_META and generates entries for each painting
    that has a built PNG asset.
    """
    painting_path = os.path.join(ROOT, 'visuals', 'painting.py')
    paintings_dir = os.path.join(ROOT, 'assets', 'paintings')
    if not os.path.isfile(painting_path):
        return []

    with open(painting_path) as f:
        source = f.read()

    # Extract PAINTING_META dict literal from source
    start = source.find('PAINTING_META = {')
    if start < 0:
        return []
    start = source.index('{', start)
    depth = 0
    end = start
    for i in range(start, len(source)):
        if source[i] == '{':
            depth += 1
        elif source[i] == '}':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    else:
        return []

    try:
        meta = ast.literal_eval(source[start:end])
    except (ValueError, SyntaxError):
        return []

    entries = []
    for pid, (title, artist, year) in meta.items():
        if not os.path.isfile(os.path.join(paintings_dir, f'{pid}.png')):
            continue
        cls_name = 'Painting' + ''.join(w.capitalize() for w in pid.split('_'))
        entries.append({
            'name': title.upper(),
            'cls': cls_name,
            'module': 'visuals/painting.py',
            'is_game': False,
        })
    return entries


def resolve_transitive_deps(file_deps):
    """Expand deps transitively: if A needs B and B needs C, A needs [B, C]."""
    resolved = {}
    def _resolve(path, visiting=None):
        if path in resolved:
            return resolved[path]
        if visiting is None:
            visiting = set()
        if path in visiting:
            return []
        visiting.add(path)
        direct = file_deps.get(path, [])
        full = list(direct)
        for dep in direct:
            for sub in _resolve(dep, visiting):
                if sub not in full:
                    full.append(sub)
        resolved[path] = full
        return full
    for path in file_deps:
        _resolve(path)
    return resolved


def scan_playlists(items_by_cat):
    """Extract playlist membership from shuffle.py and slideshow.py ASTs.

    Attaches a 'playlist' list to each playlist item in items_by_cat.
    """
    # Build class-name -> item lookup
    cls_lookup = {}
    for items in items_by_cat.values():
        for item in items:
            if item['cls'] not in cls_lookup:
                cls_lookup[item['cls']] = item

    def extract_method_imports(class_node, method_name):
        """Extract imported class names from a method body."""
        for item in class_node.body:
            if isinstance(item, ast.FunctionDef) and item.name == method_name:
                names = []
                for stmt in ast.walk(item):
                    if isinstance(stmt, ast.ImportFrom):
                        for alias in stmt.names:
                            names.append(alias.asname or alias.name)
                return names
        return None

    def resolve_items(class_names):
        """Map class names to mini catalog entries."""
        result = []
        seen = set()
        for cn in class_names:
            if cn in cls_lookup and cn not in seen:
                seen.add(cn)
                src = cls_lookup[cn]
                e = {'name': src['name'], 'cls': src['cls'],
                     'module': src['module']}
                if src.get('deps'):
                    e['deps'] = src['deps']
                if src.get('needs_numpy'):
                    e['needs_numpy'] = True
                result.append(e)
        return result

    def attach(cls_name, members):
        if cls_name in cls_lookup and members:
            cls_lookup[cls_name]['playlist'] = members

    # --- Game playlists (shuffle.py) ---
    shuffle_path = os.path.join(ROOT, 'games', 'shuffle.py')
    try:
        with open(shuffle_path) as f:
            shuffle_tree = ast.parse(f.read())
    except (SyntaxError, FileNotFoundError):
        shuffle_tree = None

    if shuffle_tree:
        for node in ast.iter_child_nodes(shuffle_tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if not any(isinstance(b, ast.Name) and b.id == 'GamePlaylist'
                       for b in node.bases):
                continue
            if node.name == 'AllGames':
                # All single-player, non-playlist games
                members = []
                for cat_key, cat_items in items_by_cat.items():
                    if cat_key in ('2_player', 'game_mix'):
                        continue
                    for it in cat_items:
                        if it['is_game']:
                            members.append(it)
                attach('AllGames', resolve_items([m['cls'] for m in members]))
            else:
                imports = extract_method_imports(node, '_init_games')
                if imports:
                    attach(node.name, resolve_items(imports))

    # --- Visual playlists (slideshow.py) ---
    slideshow_path = os.path.join(ROOT, 'visuals', 'slideshow.py')
    try:
        with open(slideshow_path) as f:
            slideshow_tree = ast.parse(f.read())
    except (SyntaxError, FileNotFoundError):
        slideshow_tree = None

    if slideshow_tree:
        for node in ast.iter_child_nodes(slideshow_tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if not any(isinstance(b, ast.Name) and b.id == 'Slideshow'
                       for b in node.bases):
                continue
            if node.name == 'AllVisuals':
                members = []
                for cat_key, cat_items in items_by_cat.items():
                    if cat_key in ('utility', 'visual_mix'):
                        continue
                    for it in cat_items:
                        if not it['is_game']:
                            members.append(it)
                attach('AllVisuals', resolve_items([m['cls'] for m in members]))
            elif node.name == 'Title':
                members = items_by_cat.get('titles', [])
                attach('Title', resolve_items([m['cls'] for m in members]))
            elif node.name == 'Demos':
                members = [m for m in items_by_cat.get('demos', [])
                           if m['cls'] != 'Demos']
                attach('Demos', resolve_items([m['cls'] for m in members]))
            else:
                imports = extract_method_imports(node, '_get_visual_classes')
                if imports:
                    attach(node.name, resolve_items(imports))


def main():
    items_by_cat = {}
    file_deps = {}  # module_path -> direct deps from scan_file
    file_numpy = {}  # module_path -> True if file directly imports numpy

    for pkg in ['games', 'visuals']:
        pkg_dir = os.path.join(ROOT, pkg)
        if not os.path.isdir(pkg_dir):
            continue

        is_game = pkg == 'games'
        default_cat = 'arcade' if is_game else 'nature'
        pkg_exports = scan_exported_classes(pkg)

        for fname in sorted(os.listdir(pkg_dir)):
            if not fname.endswith('.py') or fname.startswith('_'):
                continue

            filepath = os.path.join(pkg_dir, fname)
            module_path = f"{pkg}/{fname}"
            mod_name = fname.replace('.py', '')
            exported = pkg_exports.get(mod_name) if pkg_exports else None
            classes, deps, needs_numpy = scan_file(filepath, pkg, exported)
            if deps:
                file_deps[module_path] = deps
            if needs_numpy:
                file_numpy[module_path] = True

            for cls_info in classes:
                cat_key = cls_info['category'] or default_cat
                entry = {
                    'name': cls_info['name'],
                    'cls': cls_info['cls'],
                    'module': module_path,
                    'is_game': is_game,
                }
                items_by_cat.setdefault(cat_key, []).append(entry)

    # Add dynamically-generated painting visual entries
    for entry in scan_painting_entries():
        items_by_cat.setdefault('art', []).append(entry)

    # Resolve transitive deps and attach to items
    all_deps = resolve_transitive_deps(file_deps)
    for items in items_by_cat.values():
        for entry in items:
            mod = entry['module']
            deps = all_deps.get(mod, [])
            if deps:
                entry['deps'] = deps
            # needs_numpy if the module or any transitive dep imports numpy
            if file_numpy.get(mod) or any(file_numpy.get(d) for d in deps):
                entry['needs_numpy'] = True

    # Extract playlist membership and attach to playlist items
    scan_playlists(items_by_cat)

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
