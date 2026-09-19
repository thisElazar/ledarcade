"""Shared helpers for the parity tests.

The arcade has three hand-written copies of its platform layer — the desktop sim
(`arcade.py`), the cabinet driver (`hardware.py`) and the web emulator's Python
shim (embedded in `site/emulator.html`). These helpers make all three loadable on
a CI runner so tests can hold them against each other.
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMULATOR_HTML = os.path.join(ROOT, "site", "emulator.html")

# Every field an InputState carries, split by meaning. `*_pressed`/`action_*` are
# one-frame edges; the rest are levels.
DIRECTIONS = ("up", "down", "left", "right")
BUTTONS = ("action_l", "action_r")
INPUT_FIELDS = (
    DIRECTIONS
    + tuple(d + "_pressed" for d in DIRECTIONS)
    + BUTTONS
    + tuple(b + "_held" for b in BUTTONS)
)


# ── sim ──────────────────────────────────────────────────────────────

_sim_display = None


def get_sim_display():
    """One shared headless sim Display for the session."""
    global _sim_display
    if _sim_display is None:
        from arcade import Display
        _sim_display = Display()
    return _sim_display


# ── cabinet ──────────────────────────────────────────────────────────

class _FakeCanvas:
    def SetImage(self, *a, **k):
        pass

    def SetPixel(self, *a, **k):
        pass


class _FakeMatrix:
    def __init__(self, options=None):
        pass

    def CreateFrameCanvas(self):
        return _FakeCanvas()

    def SwapOnVSync(self, canvas):
        return canvas


class _FakeOptions:
    pass


def make_hw_display():
    """The real `hardware.HardwareDisplay`, with only the rgbmatrix library stubbed.

    Everything the cabinet executes per pixel — the bytearray framebuffer, bounds
    checks, the `_fb` fast paths visuals branch on, gamma/safety in render() — is
    the production code.
    """
    import hardware
    hardware.HAS_MATRIX = True
    hardware.RGBMatrix = _FakeMatrix
    hardware.RGBMatrixOptions = _FakeOptions
    return hardware.HardwareDisplay()


_hw_display = None


def get_hw_display():
    global _hw_display
    if _hw_display is None:
        _hw_display = make_hw_display()
    return _hw_display


# ── web emulator ─────────────────────────────────────────────────────

_emulator_ns = None


def load_emulator_shim():
    """Execute the emulator's embedded platform shim and return its namespace.

    Only the part that defines Colors/Display/InputState/Game/Visual is run; the
    `sys.modules` shimming that follows it would clobber the real modules.
    """
    global _emulator_ns
    if _emulator_ns is None:
        with open(EMULATOR_HTML) as f:
            html = f.read()
        blocks = re.findall(r"runPythonAsync\(`\n(.*?)`\)", html, re.S)
        shim = next(b for b in blocks if "class InputState" in b)
        marker = "# --- sys.modules shimming ---"
        assert marker in shim, (
            "emulator.html shim layout changed — update tests/_harness.py")
        ns = {}
        exec(compile(shim.split(marker)[0], "emulator.html<shim>", "exec"), ns)
        _emulator_ns = ns
    return _emulator_ns


def emulator_js():
    with open(EMULATOR_HTML) as f:
        return f.read()


# ── input scripts ────────────────────────────────────────────────────

def make_input(state_cls, **fields):
    s = state_cls()
    for k, v in fields.items():
        assert k in INPUT_FIELDS, k
        setattr(s, k, v)
    return s


def fuzz_script(state_cls):
    """A short script that exercises every input the panel can produce:
    each direction pressed then held, each button pressed then held, both
    buttons together, then idle frames."""
    frames = []
    for d in DIRECTIONS:
        frames.append(make_input(state_cls, **{d: True, d + "_pressed": True}))
        frames.append(make_input(state_cls, **{d: True}))
    for b in BUTTONS:
        frames.append(make_input(state_cls, **{b: True, b + "_held": True}))
        frames.append(make_input(state_cls, **{b + "_held": True}))
    frames.append(make_input(state_cls, action_l=True, action_r=True,
                             action_l_held=True, action_r_held=True))
    frames.append(make_input(state_cls, up=True, left=True,
                             action_l_held=True, action_r_held=True))
    frames.extend(state_cls() for _ in range(3))
    return frames


def script_from_held(state_cls, held_frames):
    """Turn per-frame sets of held controls into InputStates with correct edges."""
    frames, prev = [], set()
    for held in held_frames:
        s = state_cls()
        for d in DIRECTIONS:
            setattr(s, d, d in held)
            setattr(s, d + "_pressed", d in held and d not in prev)
        for b in BUTTONS:
            setattr(s, b + "_held", b in held)
            setattr(s, b, b in held and b not in prev)
        frames.append(s)
        prev = set(held)
    return frames
