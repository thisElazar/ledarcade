#!/usr/bin/env python3
"""Generate guide.json for the website Field Guide by scanning source modules.

Single source of truth: each game/visual module documents itself.
For every class registered in games/__init__.py / visuals/__init__.py:

  1. If the class has a GUIDE dict attribute, that is the curated entry:
       GUIDE = {
           "desc":    "Public one-or-two sentence description.",
           "origin":  "Optional origin story / attribution line.",
           "year":    "Optional year or era string (e.g. '1979', 'c. 100 BC').",
           "credit":  "Optional creator credit (e.g. 'Craig Reynolds').",
           "controls": {"Joystick": "Steer", "Button": "Fire"},  # optional override
       }
  2. Otherwise the entry falls back to the module docstring: the prose
     paragraph(s) become desc, and the 'Controls:' block is parsed into
     a controls mapping. Fallback entries are flagged "stub": true so we
     can find and polish them over time.

Categories mirror the cabinet menu exactly (via generate_catalog's scan).
Output: site/guide.json — fetched by guide.html at runtime from GitHub raw,
so guide content goes live by merging to main (no FTP needed).
"""

import ast
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_catalog import (  # noqa: E402
    GAME_CATEGORIES, VISUAL_CATEGORIES, ROOT,
    scan_exported_classes, scan_file, scan_painting_entries,
)


def parse_docstring(doc):
    """Split a module docstring into (title, prose, controls_dict).

    Expected shape (used across the whole codebase):
        Name - Short Tagline
        =====================
        Prose paragraphs...

        Controls:
          Up/Down    - Does something
          Space      - Does something else
    """
    if not doc:
        return None, None, {}
    lines = doc.strip().splitlines()
    title = lines[0].strip() if lines else None

    prose_lines = []
    controls = {}
    in_controls = False
    for line in lines[1:]:
        stripped = line.strip()
        if re.match(r'^=+$', stripped):
            continue
        # Section heading: "Controls:", "Commands:", "Keys:", "Controls (X):"...
        if re.match(r'^(controls?|commands?|keys|keyboard|inputs?)\b'
                    r'[\w\s()/&-]*:\s*$', stripped, re.IGNORECASE):
            in_controls = True
            continue
        if in_controls:
            # Accept a dash separator OR two-or-more spaces (aligned columns).
            m = re.match(r'^(.+?)(?:\s+[-–—]\s+|\s{2,})(.+)$', stripped)
            if m:
                controls[m.group(1).strip()] = m.group(2).strip()
            elif not stripped:
                in_controls = False
            continue
        prose_lines.append(line)

    prose = '\n'.join(prose_lines).strip()
    # Collapse internal whitespace but keep paragraph breaks
    paragraphs = [re.sub(r'\s+', ' ', p).strip()
                  for p in re.split(r'\n\s*\n', prose) if p.strip()]
    return title, paragraphs, controls


def extract_guide_attr(class_node):
    """Extract a GUIDE dict literal from a class body, if present."""
    for item in class_node.body:
        if isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Name) and target.id == 'GUIDE':
                    try:
                        value = ast.literal_eval(item.value)
                    except (ValueError, SyntaxError):
                        return None
                    if isinstance(value, dict):
                        return value
    return None


def scan_module_guides(filepath):
    """Return (module_docstring_parts, {class_name: GUIDE dict}) for a file."""
    try:
        with open(filepath, 'r') as f:
            tree = ast.parse(f.read())
    except (SyntaxError, UnicodeDecodeError, FileNotFoundError):
        return (None, None, {}), {}

    doc_parts = parse_docstring(ast.get_docstring(tree))
    guides = {}
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            guide = extract_guide_attr(node)
            if guide is not None:
                guides[node.name] = guide
    return doc_parts, guides


def build_entry(item, doc_parts, guide):
    """Merge GUIDE attr (curated) over docstring fallback (stub)."""
    title, paragraphs, doc_controls = doc_parts
    entry = {'name': item['name'], 'cls': item['cls'], 'module': item['module']}

    if guide:
        entry['desc'] = guide.get('desc', '')
        for key in ('origin', 'year', 'credit'):
            if guide.get(key):
                entry[key] = guide[key]
        entry['controls'] = guide.get('controls', doc_controls)
    else:
        entry['desc'] = ' '.join(paragraphs or [])
        entry['controls'] = doc_controls
        entry['stub'] = True
    return entry


def build_painting_groups():
    """Read PAINTING_META and return artist-grouped painting lists.

    Only paintings with a built PNG asset are included (matching the cabinet).
    Returns a list of {'artist': str, 'works': [{'title','year'}, ...]} sorted
    by each artist's earliest work, so the ART section reads chronologically.
    """
    painting_path = os.path.join(ROOT, 'visuals', 'painting.py')
    paintings_dir = os.path.join(ROOT, 'assets', 'paintings')
    if not os.path.isfile(painting_path):
        return []
    src = open(painting_path).read()
    start = src.find('PAINTING_META = {')
    if start < 0:
        return []
    start = src.index('{', start)
    depth, end = 0, start
    for i in range(start, len(src)):
        if src[i] == '{':
            depth += 1
        elif src[i] == '}':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    try:
        meta = ast.literal_eval(src[start:end])
    except (ValueError, SyntaxError):
        return []

    by_artist = {}
    for pid, (title, artist, year) in meta.items():
        if not os.path.isfile(os.path.join(paintings_dir, f'{pid}.png')):
            continue
        by_artist.setdefault(artist, []).append({'title': title, 'year': year})
    groups = []
    for artist, works in by_artist.items():
        works.sort(key=lambda w: w['year'])
        groups.append({'artist': artist, 'works': works,
                       '_first': works[0]['year']})
    groups.sort(key=lambda g: (g['_first'], g['artist']))
    for g in groups:
        del g['_first']
    return groups


def attach_playlists(items_by_cat):
    """Copy playlist membership (names) from catalog.json onto MIX items."""
    catalog_path = os.path.join(ROOT, 'site', 'catalog.json')
    try:
        catalog = json.load(open(catalog_path))
    except (FileNotFoundError, ValueError):
        return
    members = {}
    for cat in catalog['categories']:
        for it in cat['items']:
            if it.get('playlist'):
                members[(cat['key'], it['name'])] = [
                    m['name'] for m in it['playlist']]
    for key, items in items_by_cat.items():
        for it in items:
            names = members.get((key, it['name']))
            if names:
                it['members'] = names


def build_meta(categories, painting_groups):
    """Headline counts for the guide page, derived from the real content."""
    game_keys = {c['key'] for c in GAME_CATEGORIES}
    def total(pred):
        return sum(1 for c in categories for i in c['items'] if pred(c, i))
    paintings = sum(len(g['works']) for g in painting_groups)
    return {
        'games': total(lambda c, i: c['key'] in game_keys
                       and c['key'] != 'game_mix'),
        'visuals': total(lambda c, i: c['key'] not in game_keys
                         and c['key'] not in ('demos', 'titles', 'utility',
                                              'visual_mix', 'art')),
        'paintings': paintings,
        'demos': next((len(c['items']) for c in categories
                       if c['key'] == 'demos'), 0),
        'titles': next((len(c['items']) for c in categories
                        if c['key'] == 'titles'), 0),
    }


def main():
    items_by_cat = {}
    module_cache = {}

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
            mod_name = fname.replace('.py', '')
            if pkg_exports and mod_name not in pkg_exports:
                continue
            filepath = os.path.join(pkg_dir, fname)
            module_path = f"{pkg}/{fname}"
            exported = pkg_exports.get(mod_name) if pkg_exports else None
            classes, _deps, _numpy = scan_file(filepath, pkg, exported)
            if not classes:
                continue
            if module_path not in module_cache:
                module_cache[module_path] = scan_module_guides(filepath)
            doc_parts, guides = module_cache[module_path]

            for cls_info in classes:
                cat_key = cls_info['category'] or default_cat
                item = {'name': cls_info['name'], 'cls': cls_info['cls'],
                        'module': module_path}
                entry = build_entry(item, doc_parts,
                                    guides.get(cls_info['cls']))
                items_by_cat.setdefault(cat_key, []).append(entry)

    # ART: paintings are created at runtime; group them by artist for display.
    painting_groups = build_painting_groups()
    if painting_groups:
        # Placeholder items list keeps ART in the category order; the real
        # content rides in the 'paintings' key attached below.
        items_by_cat.setdefault('art', [])

    # Sort like the cabinet menu (numbers after letters)
    for items in items_by_cat.values():
        items.sort(key=lambda x: ('~' + x['name'].upper())
                   if x['name'][0].isdigit() else x['name'].upper())

    # Attach playlist membership (names only) to the MIX categories, read from
    # the already-generated catalog.json so the two stay in lockstep.
    attach_playlists(items_by_cat)

    categories = []
    for cat_def in GAME_CATEGORIES + VISUAL_CATEGORIES:
        key = cat_def['key']
        if key in items_by_cat and (items_by_cat[key] or key == 'art'):
            cat = {
                'name': cat_def['name'],
                'color': cat_def['color'],
                'key': key,
                'items': items_by_cat[key],
            }
            if key == 'art' and painting_groups:
                cat['paintings'] = painting_groups
            categories.append(cat)

    meta = build_meta(categories, painting_groups)
    out_path = os.path.join(ROOT, 'site', 'guide.json')
    with open(out_path, 'w') as f:
        json.dump({'meta': meta, 'categories': categories}, f, indent=1)

    total = sum(len(c['items']) for c in categories)
    stubs = sum(1 for c in categories for i in c['items'] if i.get('stub'))
    no_desc = [i['name'] for c in categories for i in c['items']
               if not i.get('desc')]
    print(f"Generated {out_path}: {len(categories)} categories, "
          f"{total} entries ({total - stubs} curated, {stubs} stubs), "
          f"{meta['paintings']} paintings")
    if no_desc:
        print(f"WARNING — {len(no_desc)} entries have no description at all: "
              f"{', '.join(no_desc[:15])}{'...' if len(no_desc) > 15 else ''}")


if __name__ == '__main__':
    main()
