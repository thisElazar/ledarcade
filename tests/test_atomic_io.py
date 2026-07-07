"""Tests for atomic_io.write_json_atomic — the power-loss-safe JSON writer
that settings.py and highscores.py rely on so a mid-write power cut can't
truncate a cabinet's saved state."""

import json
import os

import pytest

from atomic_io import write_json_atomic


def test_roundtrip(tmp_path):
    p = tmp_path / "d.json"
    write_json_atomic(p, {"a": [1, 2, 3], "b": "x"})
    assert json.loads(p.read_text()) == {"a": [1, 2, 3], "b": "x"}


def test_overwrite_replaces_cleanly(tmp_path):
    p = tmp_path / "d.json"
    write_json_atomic(p, {"v": 1})
    write_json_atomic(p, {"v": 2})
    assert json.loads(p.read_text()) == {"v": 2}


def test_leaves_no_temp_files(tmp_path):
    p = tmp_path / "d.json"
    write_json_atomic(p, {"v": 1})
    assert [f.name for f in tmp_path.iterdir()] == ["d.json"]


def test_failed_serialization_preserves_old_file_and_no_litter(tmp_path):
    p = tmp_path / "d.json"
    write_json_atomic(p, {"good": 1})
    with pytest.raises(TypeError):
        write_json_atomic(p, {"bad": object()})  # not JSON-serializable
    # Old contents intact — the target was never touched by the failed write.
    assert json.loads(p.read_text()) == {"good": 1}
    # And the aborted write left no temp file behind.
    assert sorted(f.name for f in tmp_path.iterdir()) == ["d.json"]
