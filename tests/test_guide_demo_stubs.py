"""Demo entries in the public guide.json never carry developer docstring text.

A demo module's docstring names the game it imitates ("Tetris plays itself",
"Mario plays himself"), not the cabinet's own item (TETROMINOS, MONKEY KONG).
guide.json is public, so a demo publishes text only once it has a curated GUIDE.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_demo_stubs_publish_no_docstring_text():
    with open(os.path.join(ROOT, "site", "guide.json")) as f:
        guide = json.load(f)
    demos = next(c for c in guide["categories"] if c["key"] == "demos")
    leaked = [i["name"] for i in demos["items"] if i.get("stub") and i.get("desc")]
    assert not leaked, f"demo stubs carrying docstring text: {leaked}"
