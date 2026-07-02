"""Guard against undocumented controls in the Field Guide.

The website Field Guide (site/guide.html) renders from site/guide.json, which is
generated from each module's `GUIDE` dict or its docstring `Controls:` block
(see site/generate_guide.py). If a game or visual reads the joystick/buttons but
nobody wrote its controls into either place, the shipped guide shows an entry
with no controls — the exact gap this project set out to close.

This test drives off the committed guide.json (the artifact the site actually
serves) so it also catches a stale guide.json. For every detailed entry whose
class actually reads input, it asserts the entry carries controls.

Categories that don't render per-item controls are out of scope: DEMOS and
TITLES (compact name lists), ART (paintings), and the GAME/VISUAL MIX playlists
(which list members, not controls). Passive visuals that ignore input are exempt.
A tiny allowlist covers interactive items whose "controls" are self-evident
(the CONTROLS input-tester).
"""
import inspect
import json
import os
import re

import pytest

from visuals import ALL_VISUALS
from games import ALL_GAMES

GUIDE_JSON = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "site", "guide.json")

# Categories whose entries are not rendered with per-item control chips.
SKIP_CATEGORIES = {"demos", "titles", "art", "game_mix", "visual_mix"}

# Game categories: every entry is a playable game and therefore interactive by
# definition, so we require controls unconditionally (games read input through
# helper methods that per-method source inspection can't reliably detect).
GAME_CATEGORIES = {"arcade", "retro", "modern", "toys", "bar", "2_player",
                   "unique"}

# Interactive items intentionally left without documented controls because the
# activity IS pressing/reading controls. Keyed by class name.
ALLOWLIST = {"Controls"}

# Any read of an input field inside an input handler marks a class interactive.
_INPUT_RE = re.compile(
    r"\b(up_pressed|down_pressed|left_pressed|right_pressed"
    r"|action_l|action_r|action_l_held|action_r_held)\b"
    r"|\b(input_state|inp)\.(up|down|left|right)\b"
)

# Map class name -> class, so a guide.json entry can find its live class.
_CLASS_BY_NAME = {c.__name__: c for c in list(ALL_VISUALS) + list(ALL_GAMES)}


def _reads_input(cls):
    """True if the class's handle_input/update actually reads an input field."""
    for method_name in ("handle_input", "update"):
        fn = getattr(cls, method_name, None)
        if fn is None:
            continue
        try:
            src = inspect.getsource(fn)
        except (OSError, TypeError):
            continue
        if _INPUT_RE.search(src):
            return True
    return False


def _detailed_entries():
    """(category_key, item) for every entry that should carry controls."""
    with open(GUIDE_JSON) as f:
        guide = json.load(f)
    out = []
    for cat in guide["categories"]:
        if cat["key"] in SKIP_CATEGORIES:
            continue
        for item in cat["items"]:
            out.append((cat["key"], item))
    return out


_ENTRIES = _detailed_entries()


def test_guide_json_exists_and_is_populated():
    # A missing/empty guide.json means the site would show nothing — and would
    # make every parametrized case below vacuously pass.
    assert _ENTRIES, (
        "guide.json has no detailed entries — regenerate it with "
        "`python3 site/generate_guide.py`."
    )


@pytest.mark.parametrize(
    "entry", _ENTRIES, ids=lambda e: f"{e[0]}/{e[1]['cls']}")
def test_interactive_entry_has_controls(entry):
    cat_key, item = entry
    cls = _CLASS_BY_NAME.get(item["cls"])
    if cls is None:
        pytest.skip(f"{item['cls']} not in runtime catalog (dynamic/paintings)")
    if cls.__name__ in ALLOWLIST:
        pytest.skip("allowlisted")
    # Games are always interactive; visuals only if they read input.
    if cat_key not in GAME_CATEGORIES and not _reads_input(cls):
        pytest.skip("passive visual — no controls expected")
    assert item.get("controls"), (
        f"{item['name']} ({item['cls']}, {item['module']}) reads input but its "
        "guide.json entry has no controls. Add GUIDE['controls'] or a docstring "
        "'Controls:' block, then run `python3 site/generate_guide.py`."
    )
