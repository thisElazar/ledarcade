"""The one vocabulary for documenting controls.

The panel has a joystick and two buttons — nothing else. Every key in a
`Controls:` docstring block or a `GUIDE['controls']` dict must reduce to those
physical inputs. Keyboard names from the desktop sim (Space, Z, arrows) are
accepted as aliases because the sim maps them 1:1; names for inputs the panel
does not have (Escape, X, Enter, mouse) are not.

Used by tests/test_controls_contract.py (enforcement) and
tools/build_timeline.py (the parity table).
"""
import re

UP, DOWN, LEFT, RIGHT = "up", "down", "left", "right"
BTN_L, BTN_R = "action_l", "action_r"
JOYSTICK = frozenset({UP, DOWN, LEFT, RIGHT})
BUTTONS = frozenset({BTN_L, BTN_R})

_ALIASES = {
    "up": {UP}, "down": {DOWN}, "left": {LEFT}, "right": {RIGHT},
    "↑": {UP}, "↓": {DOWN}, "←": {LEFT}, "→": {RIGHT},
    "joystick": JOYSTICK, "stick": JOYSTICK, "any direction": JOYSTICK,
    "arrows": JOYSTICK, "arrow keys": JOYSTICK,
    # Either button / unspecified button.
    "button": BUTTONS, "buttons": BUTTONS, "btn": BUTTONS, "action": BUTTONS,
    "action button": BUTTONS, "any button": BUTTONS, "either button": BUTTONS,
    "single button": BUTTONS, "both": BUTTONS, "both buttons": BUTTONS,
    "both btns": BUTTONS, "hold both": BUTTONS, "l/r": BUTTONS,
    # Left button (Space in the sim).
    "space": {BTN_L}, "action l": {BTN_L}, "action_l": {BTN_L}, "l": {BTN_L},
    "left button": {BTN_L}, "left btn": {BTN_L},
    # Right button (Z in the sim).
    "z": {BTN_R}, "action r": {BTN_R}, "action_r": {BTN_R}, "r": {BTN_R},
    "right button": {BTN_R}, "right btn": {BTN_R},
    "any": JOYSTICK | BUTTONS, "any input": JOYSTICK | BUTTONS,
}

# Sim-only keys that the Field Guide drops; allowed in docstrings, map to nothing.
SIM_ONLY = {"escape", "esc"}

_MODIFIERS = re.compile(
    r"\b(held|hold|tap|tapped|pressed|press|release|released|double[- ]tap|2s|\d+s)\b")


def parse_key(key):
    """Return the set of physical inputs a documented control key refers to,
    an empty set for a sim-only key, or None if it names something the panel
    does not have (or is not recognisable)."""
    text = re.sub(r"\(.*?\)", " ", key.lower())
    text = _MODIFIERS.sub(" ", text)
    text = re.sub(r"\s+", " ", text).strip(" :")
    if text in SIM_ONLY:
        return set()
    if text in _ALIASES:
        return set(_ALIASES[text])
    inputs = set()
    # "left button"/"action l" style phrases must win over their parts.
    parts = [p.strip() for p in re.split(r"\s*(?:/|\+|,|&|\bor\b|\band\b)\s*", text)]
    for part in parts:
        if part in SIM_ONLY:
            continue
        if part not in _ALIASES:
            return None
        inputs |= _ALIASES[part]
    return inputs or None


def parse_controls(controls):
    """{key: inputs-or-None} for a whole controls mapping."""
    return {k: parse_key(k) for k in (controls or {})}


# ── Docs vs code ─────────────────────────────────────────────────────
#
# Static (AST-only, no pygame) so the table builder can run under bare python3.

import ast
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Buttons are audited as one input: nearly every item accepts either button and
# documents it as "Button"/"Space", and the Field Guide renders both the same.
BUTTON = "button"
AXES = (UP, DOWN, LEFT, RIGHT, BUTTON)

_READS = {
    UP: r"\.up\b|\bup_pressed\b|\.dy\b|\bany_direction\b",
    DOWN: r"\.down\b|\bdown_pressed\b|\.dy\b|\bany_direction\b",
    LEFT: r"\.left\b|\bleft_pressed\b|\.dx\b|\bany_direction\b",
    RIGHT: r"\.right\b|\bright_pressed\b|\.dx\b|\bany_direction\b",
    BUTTON: r"\baction_[lr](_held)?\b",
}

_class_index = None


def _index_classes():
    """{module path: {class name: (source text, ClassDef)}} for games/ and visuals/."""
    global _class_index
    if _class_index is None:
        _class_index = {}
        for pkg in ("games", "visuals"):
            folder = os.path.join(ROOT, pkg)
            for fn in sorted(os.listdir(folder)):
                if not fn.endswith(".py"):
                    continue
                with open(os.path.join(folder, fn)) as f:
                    src = f.read()
                try:
                    tree = ast.parse(src)
                except SyntaxError:
                    continue
                _class_index[f"{pkg}/{fn}"] = {
                    node.name: (src, node) for node in tree.body
                    if isinstance(node, ast.ClassDef)}
    return _class_index


def _find_class(cls_name, module):
    """Prefer the class in `module`; helper classes elsewhere can share a name."""
    index = _index_classes()
    if cls_name in index.get(module, {}):
        return module, index[module][cls_name]
    for mod, classes in index.items():
        if cls_name in classes:
            return mod, classes[cls_name]
    return None, None


def class_source(cls_name, module, _seen=None):
    """Source of a class plus every base class defined in games/ or visuals/."""
    seen = _seen if _seen is not None else set()
    mod, found = _find_class(cls_name, module)
    if found is None or (mod, cls_name) in seen:
        return ""
    seen.add((mod, cls_name))
    src, node = found
    text = ast.get_source_segment(src, node) or ""
    for base in node.bases:
        name = getattr(base, "id", getattr(base, "attr", None))
        if name and name not in ("Visual", "Game"):
            text += "\n" + class_source(name, mod, seen)
    return text


def inputs_read(cls_name, module):
    src = class_source(cls_name, module)
    return {axis for axis, pat in _READS.items() if re.search(pat, src)}


def inputs_documented(controls):
    out = set()
    for inputs in parse_controls(controls).values():
        for i in inputs or ():
            out.add(BUTTON if i in BUTTONS else i)
    return out


def audit(item):
    """Audit one guide.json entry. Returns a dict of findings (all empty = clean)."""
    controls = item.get("controls") or {}
    parsed = parse_controls(controls)
    read = inputs_read(item["cls"], item["module"])
    documented = inputs_documented(controls)
    return {
        "unknown_keys": sorted(k for k, v in parsed.items() if v is None),
        "sim_only_keys": sorted(k for k, v in parsed.items() if v == set()),
        # Only meaningful when the entry documents something at all.
        "documented_not_read": sorted(documented - read) if controls else [],
        "read_not_documented": sorted(read - documented) if controls else [],
        "reads": sorted(read),
    }
