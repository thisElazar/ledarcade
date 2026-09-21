"""Guard the Field Guide's new collapsed-disclosure sections.

site/guide.html now shows a single closed-by-default disclosure per entry
("How it works") holding, in order: Controls, How to play (GUIDE['how']),
On screen (GUIDE['legend']), and More (GUIDE['notes']) — whichever of those
have content. site/generate_guide.py must pass those keys through from a
class's GUIDE dict the same way it already passes origin/year/credit.

(a) build_entry() passes how/legend/notes through when present, and omits
    them entirely when absent (so guide.html can tell "no section" from
    "empty section").
(b) For every class in games/*.py and visuals/*.py that has a GUIDE dict, IF
    it sets 'how'/'legend'/'notes', those values must be well-formed:
    how/notes non-empty strings, legend a non-empty dict of short strings.
    No module has these keys yet, so (b) currently passes vacuously — that
    is expected until a later step writes them.
"""
import ast
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_DIR = os.path.join(ROOT, "site")
if SITE_DIR not in sys.path:
    sys.path.insert(0, SITE_DIR)

from generate_guide import build_entry, scan_module_guides  # noqa: E402

BASE_ITEM = {"name": "Widget", "cls": "Widget", "module": "games/widget.py"}
BASE_DOC_PARTS = (None, [], {})


# ── (a) build_entry passthrough ─────────────────────────────────────

def test_build_entry_passes_through_how_legend_notes():
    guide = {
        "desc": "A thing.",
        "how": "Do the thing.\n\nThen do it again.",
        "legend": {"C:": "combo counter", "top-left number": "lives left"},
        "notes": "Based on an unreleased prototype.",
    }
    entry = build_entry(BASE_ITEM, BASE_DOC_PARTS, guide)
    assert entry["how"] == guide["how"]
    assert entry["legend"] == guide["legend"]
    assert entry["notes"] == guide["notes"]


def test_build_entry_omits_how_legend_notes_when_absent():
    guide = {"desc": "A thing."}
    entry = build_entry(BASE_ITEM, BASE_DOC_PARTS, guide)
    assert "how" not in entry
    assert "legend" not in entry
    assert "notes" not in entry


def test_build_entry_omits_how_legend_notes_when_blank():
    guide = {"desc": "A thing.", "how": "", "legend": {}, "notes": ""}
    entry = build_entry(BASE_ITEM, BASE_DOC_PARTS, guide)
    assert "how" not in entry
    assert "legend" not in entry
    assert "notes" not in entry


def test_build_entry_still_omits_on_docstring_stub():
    # Stub (docstring-fallback) entries never carry how/legend/notes.
    entry = build_entry(BASE_ITEM, (None, ["Some prose."], {}), None)
    assert entry.get("stub") is True
    assert "how" not in entry
    assert "legend" not in entry
    assert "notes" not in entry


# ── (b) shape-check every real GUIDE dict that already has these keys ──

def _all_guides():
    """[(module_path, class_name, guide_dict), ...] for games/ and visuals/."""
    out = []
    for pkg in ("games", "visuals"):
        pkg_dir = os.path.join(ROOT, pkg)
        for fname in sorted(os.listdir(pkg_dir)):
            if not fname.endswith(".py") or fname.startswith("_"):
                continue
            filepath = os.path.join(pkg_dir, fname)
            _doc_parts, guides = scan_module_guides(filepath)
            for cls_name, guide in guides.items():
                out.append((f"{pkg}/{fname}", cls_name, guide))
    return out


_GUIDES = _all_guides()


def test_found_guide_dicts():
    # Sanity check that the scan itself works before trusting a vacuous pass.
    assert len(_GUIDES) > 100, "expected many GUIDE dicts across games/visuals"


@pytest.mark.parametrize(
    "entry", _GUIDES, ids=lambda e: f"{e[0]}:{e[1]}")
def test_how_is_a_non_empty_string_when_present(entry):
    _module, _cls, guide = entry
    if "how" not in guide:
        pytest.skip("no 'how' key")
    assert isinstance(guide["how"], str) and guide["how"].strip()


@pytest.mark.parametrize(
    "entry", _GUIDES, ids=lambda e: f"{e[0]}:{e[1]}")
def test_notes_is_a_non_empty_string_when_present(entry):
    _module, _cls, guide = entry
    if "notes" not in guide:
        pytest.skip("no 'notes' key")
    assert isinstance(guide["notes"], str) and guide["notes"].strip()


@pytest.mark.parametrize(
    "entry", _GUIDES, ids=lambda e: f"{e[0]}:{e[1]}")
def test_legend_is_a_short_string_to_string_dict_when_present(entry):
    module, cls, guide = entry
    if "legend" not in guide:
        pytest.skip("no 'legend' key")
    legend = guide["legend"]
    assert isinstance(legend, dict) and legend, (
        f"{module}:{cls} GUIDE['legend'] must be a non-empty dict")
    for key, value in legend.items():
        assert isinstance(key, str) and isinstance(value, str), (
            f"{module}:{cls} GUIDE['legend'] must map str -> str")
        assert len(key) <= 24, (
            f"{module}:{cls} GUIDE['legend'] key too long: {key!r}")
        assert len(value) <= 140, (
            f"{module}:{cls} GUIDE['legend'] value too long: {value!r}")


# ── the glossary ledger and the Field Guide stay in step ──────────────

# Items whose only undecoded labels are developer error screens, which the
# Field Guide deliberately does not explain.
_NO_LEGEND_NEEDED = {
    "visuals/usb_share.py::UsbShare",   # 'NO PIL' (missing dependency)
    # TITLES are listed by name only on the page; their text is set dressing.
    "visuals/wondercabinet.py::WonderDOS",
    "visuals/wondercabinet.py::WonderInsertCoin",
    "visuals/wondercabinet.py::WonderVHS",
}


def test_every_item_the_ledger_flags_has_a_legend():
    """tools/legend_ledger.json lists on-screen labels a viewer has to decode.

    Any item with a label the panel itself never spells out must explain it in
    GUIDE['legend'], so the Field Guide gives players what the cabinet doesn't.
    """
    import json
    with open(os.path.join(ROOT, "tools", "legend_ledger.json")) as f:
        entries = json.load(f)["entries"]
    have = {f"{module}::{cls}" for module, cls, guide in _GUIDES
            if guide.get("legend")}
    missing = sorted(
        key for key, entry in entries.items()
        if any(not rec["explained_same_screen"]
               for rec in entry["labels"].values())
        and key not in have and key not in _NO_LEGEND_NEEDED)
    assert not missing, f"ledger items with no GUIDE['legend']: {missing}"
