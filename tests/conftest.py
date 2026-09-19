"""Pytest configuration for the LED Arcade smoke tests.

The tests construct the real pygame `Display`, so we force SDL into headless
("dummy") mode before pygame is ever imported. This lets the whole catalog be
exercised on a CI runner with no screen, audio device, or LED matrix.
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

# Tests import top-level modules (arcade, visuals, games) — make sure the repo
# root is importable regardless of where pytest is invoked from.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import copy
import subprocess

import pytest


@pytest.fixture
def sandbox(monkeypatch, tmp_path):
    """Make it safe to press buttons on everything.

    Pressing the action button on the utility screens has real effects: SHUTDOWN
    runs `sudo shutdown`, UPDATE runs git, the settings and lab screens rewrite
    user_settings.json, PAINT saves files. Tests that feed input to the whole
    catalog must use this fixture. Returns the list of shell commands attempted.
    """
    import settings
    import visuals.paint
    import visuals.paint_gif
    import visuals.refresh

    attempted = []

    def fake_system(cmd):
        attempted.append(cmd)
        return 0

    def fake_run(cmd, *a, **k):
        attempted.append(cmd)
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="")

    def fake_check_output(cmd, *a, **k):
        attempted.append(cmd)
        raise subprocess.CalledProcessError(1, cmd)

    def fake_popen(cmd, *a, **k):
        attempted.append(cmd)
        raise OSError("subprocess blocked by the test sandbox")

    monkeypatch.setattr(os, "system", fake_system)
    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(subprocess, "call", lambda cmd, *a, **k: fake_run(cmd).returncode)
    monkeypatch.setattr(subprocess, "check_output", fake_check_output)
    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    # Settings stay in memory and are rolled back afterwards.
    settings.get("brightness")  # force the lazy load before snapshotting
    monkeypatch.setattr(settings, "_settings", copy.deepcopy(settings._settings))
    monkeypatch.setattr(settings, "_save", lambda: None)

    monkeypatch.setattr(visuals.paint, "SAVE_DIR", str(tmp_path / "paint"))
    monkeypatch.setattr(visuals.paint, "GIF_DIR", str(tmp_path / "paint_gif"))
    monkeypatch.setattr(visuals.paint_gif, "SAVE_DIR", str(tmp_path / "paint_gif"))
    monkeypatch.setattr(visuals.refresh, "ROLLBACK_FILE", str(tmp_path / ".rollback_ref"))
    return attempted
