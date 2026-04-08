"""
Cabinet Hardware Configuration
==============================
Per-cabinet hardware settings loaded from cabinet_config.json.
If the file is missing, defaults match the dev cabinet.
"""

import os
import json

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(_SCRIPT_DIR, "cabinet_config.json")

_DEFAULTS = {
    "hardware_mapping": "led-arcade",
    "gpio_slowdown": 4,
    "button_pins": {
        "up": 19, "down": 25, "left": 24,
        "right": 8, "action_l": 9, "action_r": 7,
    },
}

_config = None


def _load():
    global _config
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                _config = json.load(f)
        except Exception:
            _config = {}
    else:
        _config = {}


def _get(key):
    global _config
    if _config is None:
        _load()
    return _config.get(key, _DEFAULTS[key])


def get_hardware_mapping():
    return _get("hardware_mapping")


def get_gpio_slowdown():
    return _get("gpio_slowdown")


def get_button_pins():
    global _config
    if _config is None:
        _load()
    default = _DEFAULTS["button_pins"]
    override = _config.get("button_pins", {})
    merged = dict(default)
    merged.update(override)
    return merged
