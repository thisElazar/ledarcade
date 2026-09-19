"""Every input backend must turn the same physical presses into the same InputState.

There are four hand-written backends: the sim's pygame `InputHandler`, and on the
cabinet `KeyboardInput` (SSH debugging), `GPIOInput` (the real joystick and
buttons) and `HardwareInput` (which ORs the two together, field by field).

Games rely on exact edge semantics — `action_l` / `up_pressed` are True for one
frame only, `*_held` / `up` for as long as the control is down. A backend that
gets this wrong makes a game that plays correctly on the laptop misfire on the
cabinet (double-fires, stuck menus). GPIO can't run on CI, so it is driven here
through a fake `RPi.GPIO`; everything above the pin read is production code.
"""
import collections

import pygame
import pytest

import arcade
import hardware
from _harness import BUTTONS, DIRECTIONS, INPUT_FIELDS

CONTROLS = DIRECTIONS + BUTTONS

# What is physically held down on each successive frame.
SCRIPT = [
    set(),
    {"up"}, {"up"}, {"up"}, set(),                 # press, hold, release
    {"action_l"}, {"action_l"}, set(),
    {"action_r"}, set(), {"action_r"}, set(),      # two distinct taps
    {"left", "action_l"}, {"left", "action_r"},    # swap buttons while steering
    {"action_l", "action_r"}, {"action_l", "action_r"}, {"action_r"}, set(),
    {"up", "right"}, {"right", "down"}, {"down", "left"}, set(),  # joystick roll
    set(CONTROLS), set(CONTROLS), set(),
]


def expected(held, prev):
    """The reference semantics, stated once."""
    out = {}
    for d in DIRECTIONS:
        out[d] = d in held
        out[d + "_pressed"] = d in held and d not in prev
    for b in BUTTONS:
        out[b + "_held"] = b in held
        out[b] = b in held and b not in prev
    return out


def snapshot(state):
    return {f: bool(getattr(state, f)) for f in INPUT_FIELDS}


# ── backends, each driven from a mutable `held` set ─────────────────

def make_sim(monkeypatch, held):
    keymap = {"up": pygame.K_UP, "down": pygame.K_DOWN, "left": pygame.K_LEFT,
              "right": pygame.K_RIGHT, "action_l": pygame.K_SPACE,
              "action_r": pygame.K_z}

    def get_pressed():
        keys = collections.defaultdict(bool)
        for name in held:
            keys[keymap[name]] = True
        return keys

    monkeypatch.setattr(pygame.key, "get_pressed", get_pressed)
    return arcade.InputHandler()


def make_keyboard(monkeypatch, held):
    # Never put the developer's terminal into cbreak mode from a test run.
    def no_tty(*a):
        raise OSError("no tty in tests")
    monkeypatch.setattr(hardware.termios, "tcgetattr", no_tty)
    kb = hardware.KeyboardInput()
    monkeypatch.setattr(kb, "_read_keys", lambda: set(held))
    return kb


class FakeGPIO:
    BCM = IN = PUD_UP = object()

    def __init__(self, held):
        self.held = held
        self.pin_names = {pin: name for name, pin in hardware.BUTTON_PINS.items()}

    def setmode(self, *a): pass
    def setwarnings(self, *a): pass
    def setup(self, *a, **k): pass
    def cleanup(self, *a): pass

    def input(self, pin):
        return 0 if self.pin_names[pin] in self.held else 1  # active low


def make_gpio(monkeypatch, held):
    monkeypatch.setattr(hardware, "GPIO", FakeGPIO(held), raising=False)
    monkeypatch.setattr(hardware, "HAS_GPIO", True)
    return hardware.GPIOInput()


def make_combined_gpio_driven(monkeypatch, held):
    make_keyboard(monkeypatch, set())  # patches the tty setup
    monkeypatch.setattr(hardware, "GPIO", FakeGPIO(held), raising=False)
    monkeypatch.setattr(hardware, "HAS_GPIO", True)
    combined = hardware.HardwareInput(use_gpio=True)
    assert combined.gpio is not None
    return combined


def make_combined_keyboard_driven(monkeypatch, held):
    combined = make_combined_gpio_driven(monkeypatch, set())
    monkeypatch.setattr(combined.keyboard, "_read_keys", lambda: set(held))
    return combined


def make_combined_no_gpio(monkeypatch, held):
    make_keyboard(monkeypatch, set())
    combined = hardware.HardwareInput(use_gpio=False)
    monkeypatch.setattr(combined.keyboard, "_read_keys", lambda: set(held))
    return combined


BACKENDS = {
    "sim-pygame": make_sim,
    "cabinet-keyboard": make_keyboard,
    "cabinet-gpio": make_gpio,
    "cabinet-combined(gpio)": make_combined_gpio_driven,
    "cabinet-combined(keyboard)": make_combined_keyboard_driven,
    "cabinet-combined(no gpio)": make_combined_no_gpio,
}


def test_button_pins_cover_every_control():
    assert set(hardware.BUTTON_PINS) == set(CONTROLS)
    pins = list(hardware.BUTTON_PINS.values())
    assert len(set(pins)) == len(pins), f"two controls share a GPIO pin: {pins}"


@pytest.mark.parametrize("backend", BACKENDS)
def test_backend_matches_reference_semantics(backend, monkeypatch):
    held = set()
    handler = BACKENDS[backend](monkeypatch, held)
    prev = set()
    for frame, now in enumerate(SCRIPT):
        held.clear()
        held.update(now)
        got = snapshot(handler.update())
        want = expected(now, prev)
        assert got == want, (
            f"{backend}, frame {frame} (held={sorted(now)}): "
            f"{ {k: (got[k], want[k]) for k in got if got[k] != want[k]} } (got, want)")
        prev = set(now)


@pytest.mark.parametrize("control", CONTROLS)
def test_combined_input_merges_both_sources(control, monkeypatch):
    """Keyboard holds one control, GPIO another: both must come through."""
    other = next(c for c in CONTROLS if c != control)
    gpio_held, kb_held = {control}, {other}
    combined = make_combined_gpio_driven(monkeypatch, gpio_held)
    monkeypatch.setattr(combined.keyboard, "_read_keys", lambda: set(kb_held))
    got = snapshot(combined.update())
    assert got == expected({control, other}, set())
    # Held across a second frame: levels stay, edges clear.
    got = snapshot(combined.update())
    assert got == expected({control, other}, {control, other})
