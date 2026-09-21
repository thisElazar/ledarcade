"""Record every string each game and visual actually draws.

Not a test (the filename keeps it out of the normal run). It lives here because
it presses buttons on the whole catalog and so needs the `sandbox` fixture:

    pytest tests/record_drawn_text.py -q      # writes tools/drawn_text.json

The static scan in tools/legend_audit.py guesses at labels from source text;
this is what reaches the panel, however the code built the string. It only
sees states a short scripted run reaches (no late levels, rare modes), and
only text drawn through the Display's text methods (not hand-drawn glyphs), so
the two are read together. Digit runs are collapsed to '#'.
"""
import json
import os
import random
import re

from arcade import InputState
from games import ALL_GAMES
from visuals import ALL_VISUALS
from _harness import ROOT, get_sim_display, script_from_held

DT = 1.0 / 30.0
SECONDS = 20
MAX_STRINGS = 150
OUT = os.path.join(ROOT, "tools", "drawn_text.json")
TEXT_METHODS = ("draw_text_small", "draw_text_raw", "draw_text_clipped")
HOLDS = [set()] * 4 + [{"up"}, {"down"}, {"left"}, {"right"},
                       {"action_l"}, {"action_r"}]

_recorded = {}
_crashed = {}


def _script():
    rng = random.Random(1)
    held = [set()] * 45          # let title cards play
    while len(held) < SECONDS * 30:
        held += [rng.choice(HOLDS)] * rng.choice((1, 6, 12))
    return script_from_held(InputState, held)


def _record(cls, sandbox, monkeypatch, is_game):
    random.seed(1)
    display = get_sim_display()
    seen = set()
    for name in TEXT_METHODS:
        real = getattr(display, name)

        def spy(*args, _real=real, **kwargs):
            seen.update(re.sub(r"\d+", "#", a) for a in args if isinstance(a, str))
            return _real(*args, **kwargs)
        monkeypatch.setattr(display, name, spy)

    key = cls.__module__.replace(".", "/") + ".py::" + cls.__name__
    try:
        obj = cls(display)
        obj.reset()
        for inp in _script():
            if is_game:
                obj.update(inp, DT)
            else:
                obj.handle_input(inp)
                if getattr(obj, "wants_exit", False):
                    break
                obj.update(DT)
            obj.draw()
    except Exception as e:  # keep what was drawn; the crash is a finding too
        _crashed[key] = f"{type(e).__name__}: {e}"
    _recorded[key] = sorted(seen)[:MAX_STRINGS]


def test_record_visuals(sandbox, monkeypatch):
    for cls in ALL_VISUALS:
        with monkeypatch.context() as m:
            _record(cls, sandbox, m, is_game=False)


def test_record_games(sandbox, monkeypatch):
    for cls in ALL_GAMES:
        if hasattr(cls, "games"):
            continue
        with monkeypatch.context() as m:
            _record(cls, sandbox, m, is_game=True)


def test_write():
    with open(OUT, "w") as f:
        json.dump({"crashed": _crashed, "drawn": _recorded}, f, indent=1, sort_keys=True, ensure_ascii=False)
        f.write("\n")
