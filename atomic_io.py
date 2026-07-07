"""
Atomic JSON persistence
=======================
Power-loss-safe writes for unattended cabinets. A plain open('w') + json.dump
can leave a truncated (invalid) file if the Pi loses power mid-write — the
loaders then reset to empty and a kid's high scores vanish.

write_json_atomic writes to a temp file in the SAME directory, fsyncs it to
physical media, then os.replace()s it over the target. os.replace is atomic on
POSIX, so a reader (or a power cut) sees either the whole old file or the whole
new one, never a half-written one. This mirrors the pattern already used for
the atlas download in visuals/atlas.py.
"""

import json
import os
import tempfile


def write_json_atomic(path, obj, indent=2):
    """Atomically serialize `obj` to `path` as JSON. Raises on failure."""
    path = os.fspath(path)
    directory = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".tmp-", suffix=".json")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(obj, f, indent=indent)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        # Clean up the temp file so a failed write leaves no litter.
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise
