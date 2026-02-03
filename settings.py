"""
Persistent User Settings
========================
Saves and loads user preferences to a JSON file.
Settings persist across restarts.
"""

import os
import json

# Settings file location (same directory as this script)
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(_SCRIPT_DIR, "user_settings.json")

# Default settings
DEFAULTS = {
    "brightness": 80,
    "enabled_transitions": None,  # None means all enabled
}

# In-memory settings cache
_settings = None


def _load():
    """Load settings from disk."""
    global _settings
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                _settings = json.load(f)
        except Exception:
            _settings = {}
    else:
        _settings = {}


def _save():
    """Save settings to disk."""
    if _settings is None:
        return
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(_settings, f, indent=2)
    except Exception:
        pass


def get(key, default=None):
    """Get a setting value."""
    global _settings
    if _settings is None:
        _load()
    if default is None:
        default = DEFAULTS.get(key)
    return _settings.get(key, default)


def set(key, value):
    """Set a setting value and save to disk."""
    global _settings
    if _settings is None:
        _load()
    _settings[key] = value
    _save()


def get_brightness():
    """Get brightness setting (10-100)."""
    return get("brightness", 80)


def set_brightness(value):
    """Set brightness setting (10-100)."""
    value = max(10, min(100, value))
    set("brightness", value)


def get_enabled_transition_names():
    """Get list of enabled transition names, or None for all."""
    return get("enabled_transitions", None)


def set_enabled_transition_names(names):
    """Set list of enabled transition names, or None for all."""
    set("enabled_transitions", names)
