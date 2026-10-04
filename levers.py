"""
Switch-room levers (the secret room behind GRAND MUSEUM's push-wall).

Levers only change what the menu lists. They never touch the `.dev` file,
which picks the update channel (a kid must not be able to put a cabinet on
untested `main`).

  BACKSTAGE    lists dev_only items. Saved in user_settings.json.
  AFTER HOURS  lists mature items (DOOM). Kept in memory only, so a reboot
               or an update restart switches it off. Needs the owner's code.
"""

import hashlib

import settings

CODE_LENGTH = 8
# sha256 of the AFTER HOURS stick sequence, e.g. "up up down ...". Only the
# hash lives in this public repo; the code itself is on the owner's card.
_CODE_SHA256 = "8c600d1bb1c41f7698b786fb6857d20b7b7f314d112edf8e9409bac9c09d2fc6"

_after_hours = False


def backstage():
    return bool(settings.get('backstage', False))


def set_backstage(on):
    settings.set('backstage', bool(on))


def after_hours():
    return _after_hours


def set_after_hours(on):
    global _after_hours
    _after_hours = bool(on)


def code_matches(moves):
    """moves: list of 'up'/'down'/'left'/'right'."""
    return hashlib.sha256(" ".join(moves).encode()).hexdigest() == _CODE_SHA256
