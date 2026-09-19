"""The controls contract, checked against every game and visual in the catalog.

1. Pressing things never crashes — on the sim display *or* the cabinet's. The
   smoke tests run every item with an idle joystick; nothing else ever pressed a
   button on all ~300 of them, and nothing ran them through the cabinet's
   bytearray framebuffer (which rejects floats and out-of-range colours the sim
   happily accepts, and takes `_fb` fast paths the sim never reaches).
2. Nobody gets trapped. The cabinet has no Escape key: holding both buttons is
   the only way out. The launcher guarantees that for games and ordinary
   visuals (tests/test_runner_parity.py); a visual that sets `custom_exit` takes
   that responsibility on itself and must honour it.
3. The documentation speaks the panel's language and matches the code. Keys must
   parse under tools/controls_vocab.py, must not fall through the Field Guide's
   label table as raw text, and the inputs a class documents must be the inputs
   it reads.
"""
import json
import os
import random
import re

import pytest

from arcade import GameState, InputState
from games import ALL_GAMES
from visuals import ALL_VISUALS
from tools.controls_vocab import audit, parse_key
from _harness import (
    ROOT, fuzz_script, get_hw_display, get_sim_display, load_emulator_shim,
    script_from_held,
)

DT = 1.0 / 30.0
REAL_GAMES = [g for g in ALL_GAMES if not hasattr(g, "games")]
DISPLAYS = {"sim": get_sim_display, "cabinet": get_hw_display}


# ── 1. pressing things never crashes ────────────────────────────────

def _drive_visual(obj, display, frames):
    for inp in frames:
        obj.handle_input(inp)
        if getattr(obj, "wants_exit", False):
            return  # the launcher drops the item here
        obj.update(DT)
        obj.draw()
        display.render()


def _drive_game(obj, display, frames):
    for inp in frames:
        obj.update(inp, DT)
        obj.draw()
        display.render()


@pytest.mark.parametrize("platform", DISPLAYS)
@pytest.mark.parametrize("cls", ALL_VISUALS, ids=lambda c: c.__name__)
def test_visual_survives_every_input(cls, platform, sandbox):
    random.seed(1)
    display = DISPLAYS[platform]()
    obj = cls(display)
    _drive_visual(obj, display, fuzz_script(InputState) * 2)
    assert not any("shutdown" in str(c) for c in sandbox), (
        "a few seconds of button mashing reached a real shutdown command")


@pytest.mark.parametrize("platform", DISPLAYS)
@pytest.mark.parametrize("cls", REAL_GAMES, ids=lambda c: c.__name__)
def test_game_survives_every_input(cls, platform, sandbox):
    random.seed(1)
    display = DISPLAYS[platform]()
    obj = cls(display)
    _drive_game(obj, display, fuzz_script(InputState) * 2)
    assert isinstance(obj.state, GameState)


@pytest.mark.parametrize("cls", REAL_GAMES, ids=lambda c: c.__name__)
def test_game_restarts_cleanly_after_input(cls, sandbox):
    """PLAY AGAIN calls reset() on a game that has already been played."""
    random.seed(1)
    display = get_sim_display()
    obj = cls(display)
    _drive_game(obj, display, fuzz_script(InputState))
    obj.reset()
    assert obj.state not in (GameState.GAME_OVER, GameState.WIN), (
        "reset() left the game in a terminal state — PLAY AGAIN would loop "
        "straight back to GAME OVER")
    _drive_game(obj, display, fuzz_script(InputState))


# The web emulator runs the same modules against its own Display (the shim in
# site/emulator.html). It only offers what site/catalog.json lists.

def _emulator_catalog():
    with open(os.path.join(ROOT, "site", "catalog.json")) as f:
        catalog = json.load(f)
    listed = {item["cls"] for cat in catalog["categories"] for item in cat["items"]}
    return [c for c in list(ALL_VISUALS) + REAL_GAMES if c.__name__ in listed]


@pytest.mark.parametrize("cls", _emulator_catalog(), ids=lambda c: c.__name__)
def test_item_survives_every_input_on_the_emulator_display(cls, sandbox):
    random.seed(1)
    display = load_emulator_shim()["Display"]()
    obj = cls(display)
    drive = _drive_visual if hasattr(obj, "handle_input") else _drive_game
    drive(obj, display, fuzz_script(InputState) * 2)


# ── 2. nobody gets trapped ──────────────────────────────────────────

CUSTOM_EXIT = [v for v in ALL_VISUALS if getattr(v, "custom_exit", False)]


def test_custom_exit_is_only_used_by_visuals():
    # The launchers only consult custom_exit for visuals; on a game it would be
    # silently ignored.
    assert not [g.__name__ for g in ALL_GAMES if getattr(g, "custom_exit", False)]


@pytest.mark.parametrize("cls", CUSTOM_EXIT, ids=lambda c: c.__name__)
def test_custom_exit_visual_can_be_left_by_holding_both(cls, sandbox):
    display = get_sim_display()
    obj = cls(display)
    both = {"action_l", "action_r"}
    frames = script_from_held(InputState, [set()] * 5 + [both] * int(3.0 / DT))
    for inp in frames:
        obj.handle_input(inp)
        if obj.wants_exit:
            return
        obj.update(DT)
        if obj.wants_exit:
            return
        obj.draw()
    pytest.fail(
        f"{cls.__name__} sets custom_exit but holding both buttons for 3s did not "
        "set wants_exit. On the cabinet that leaves no way back to the menu.")


# ── 3. documentation ────────────────────────────────────────────────

# Categories rendered as plain name lists, without per-item controls.
SKIP_CATEGORIES = {"demos", "titles", "art", "game_mix", "visual_mix"}

# Known docs-vs-code mismatches. Empty since 2026-09-19 — keep it that way. If an
# entry ever has to be parked here, give the reason; the test fails once it is
# fixed, so the list can only shrink.
KNOWN_MISMATCHES = {}


def _guide_entries():
    with open(os.path.join(ROOT, "site", "guide.json")) as f:
        guide = json.load(f)
    return [(cat["key"], item) for cat in guide["categories"]
            if cat["key"] not in SKIP_CATEGORIES for item in cat["items"]]


_ENTRIES = _guide_entries()
_WITH_CONTROLS = [e for e in _ENTRIES if e[1].get("controls")]


def test_there_are_documented_entries():
    assert len(_WITH_CONTROLS) > 100, "guide.json looks empty — regenerate it"


@pytest.mark.parametrize("entry", _WITH_CONTROLS, ids=lambda e: f"{e[0]}/{e[1]['cls']}")
def test_documented_keys_name_real_panel_inputs(entry):
    _, item = entry
    unknown = [k for k in item["controls"] if parse_key(k) is None]
    assert not unknown, (
        f"{item['name']} ({item['module']}) documents {unknown}. The panel has a "
        "joystick and two buttons; use Up/Down/Left/Right/Joystick/Button/Both/"
        "Action L/Action R (see tools/controls_vocab.py), then run "
        "`python3 site/generate_guide.py`.")


def _field_guide_tables():
    with open(os.path.join(ROOT, "site", "guide.html")) as f:
        html = f.read()
    known = set()
    for name in ("KEY_LABELS", "LEFT_BTN", "RIGHT_BTN"):
        body = re.search(r"var %s = \{(.*?)\};" % name, html, re.S).group(1)
        for key in re.findall(r"'((?:[^'\\]|\\.)+)'\s*:", body):
            known.add(key.encode().decode("unicode_escape"))
    return known


def _field_guide_norm(key):
    """Port of normKey() in site/guide.html."""
    key = re.sub(r"\s*\(.*?\)\s*", "", key.lower())
    return re.sub(r"\s*held$", "", key).strip()


def test_field_guide_has_a_label_for_every_documented_key():
    """guide.html falls back to printing the raw key in capitals, which is how
    'ARROW KEYS' and 'SPACE/Z' end up on the public page of a joystick cabinet."""
    known = _field_guide_tables()
    raw = {}
    for _, item in _WITH_CONTROLS:
        for key, text in item["controls"].items():
            if re.search("escape", key, re.I) or re.search(
                    "return to menu|back to menu", text, re.I):
                continue  # guide.html drops these
            if _field_guide_norm(key) not in known:
                raw.setdefault(key, []).append(item["cls"])
    assert not raw, (
        f"These keys would be shown raw on the Field Guide: {raw}. Use a standard "
        "key in the module, or add the spelling to KEY_LABELS in site/guide.html.")


@pytest.mark.parametrize("entry", _WITH_CONTROLS, ids=lambda e: f"{e[0]}/{e[1]['cls']}")
def test_documented_inputs_match_inputs_read(entry):
    _, item = entry
    found = audit(item)
    problems = {k: found[k] for k in ("documented_not_read", "read_not_documented")
                if found[k]}
    if item["cls"] in KNOWN_MISMATCHES:
        assert problems, (
            f"{item['cls']} is fixed — remove it from KNOWN_MISMATCHES.")
        pytest.xfail(KNOWN_MISMATCHES[item["cls"]])
    assert not problems, (
        f"{item['name']} ({item['module']}): documentation and code disagree: "
        f"{problems}. The class reads {found['reads']}.")


def test_known_mismatches_are_all_real_entries():
    names = {item["cls"] for _, item in _WITH_CONTROLS}
    stale = sorted(set(KNOWN_MISMATCHES) - names)
    assert not stale, f"KNOWN_MISMATCHES lists entries that no longer exist: {stale}"
