"""On-screen labels that a viewer has to decode.

Some HUDs draw a bare abbreviation with a number ("C:123", "S:45") and nothing
on screen or in the Field Guide says what it means. This finds the candidates
by static scan and joins them to tools/legend_ledger.json, where a human
records what each one means and where (if anywhere) it is explained.

The scan is a worklist generator, not a verdict: it only sees "LABEL:value"
strings, so it misses bare letters, colour codes and symbols. The ledger is
the source of truth for what has been audited.

Used by tools/build_timeline.py. Static (AST only), runs under bare python3.
"""
import ast
import json
import os
import re

from controls_vocab import ROOT, class_source

LEDGER = os.path.join(ROOT, "tools", "legend_ledger.json")

# Item status, derived from its label records (every record in the ledger is
# a label that needs a legend). "unreviewed" is a candidate with no entry.
def status_of(entry):
    labels = list(entry["labels"].values())
    if not labels:
        return "clear"
    if all(l["explained_same_screen"] for l in labels):
        return "on-panel"
    if all(l["explained_same_screen"] or l["on_site"] for l in labels):
        return "site-only"      # nothing in GUIDE reaches the cabinet
    return "unexplained"


# A string that *starts* with LABEL: then a value (digit, other text, or an
# f-string placeholder, which the AST joins as \x00).
_LABEL = re.compile(r"^([A-Z]{1,4}):\s*(?=\x00|\d|\S)")

# Input hints ("BTN:A") aren't data readouts; the controls audit owns those.
_IGNORE = {"BTN:"}


def _text(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(v.value if isinstance(v, ast.Constant) else "\x00"
                       for v in node.values)
    return None


def labels_in(cls_name, module):
    """Sorted list of 'X:' style labels the class draws."""
    try:
        tree = ast.parse(class_source(cls_name, module))
    except SyntaxError:
        return []
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Constant, ast.JoinedStr)):
            m = _LABEL.match(_text(node) or "")
            if m and m.group(1) + ":" not in _IGNORE:
                found.add(m.group(1) + ":")
    return sorted(found)


KINDS = ("abbreviation", "coded-value", "bare-number", "notation",
         "truncation", "mislabel")


def load_ledger():
    with open(LEDGER) as f:
        entries = json.load(f)["entries"]
    for key, e in entries.items():
        for label, rec in e["labels"].items():
            if rec["kind"] not in KINDS:
                raise ValueError(f"{key} {label}: unknown kind {rec['kind']!r}")
    return entries
