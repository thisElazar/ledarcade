"""UPDATE and RLBK against real git checkouts.

The rest of the suite fakes subprocess (the `sandbox` fixture), which cannot
show what git does with a checkout. These tests build a throwaway origin and
a throwaway cabinet clone and run the real commands on them.
"""
import os
import shutil
import subprocess

import pytest

from arcade import Display, InputState
import visuals.refresh as refresh

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="needs git")


def git(cwd, *args):
    r = subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com"] + list(args),
        cwd=cwd, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


class World:
    """An origin, a developer clone that publishes to it, and a cabinet clone."""

    def __init__(self, tmp_path):
        self.origin = str(tmp_path / "origin.git")
        self.dev = str(tmp_path / "dev")
        self.cab = str(tmp_path / "cab")
        git(str(tmp_path), "init", "-q", "--bare", "-b", "main", self.origin)
        git(str(tmp_path), "clone", "-q", self.origin, self.dev)
        self.release("one", "v1.0")
        self.release("two", "v1.1")
        git(str(tmp_path), "clone", "-q", self.origin, self.cab)

    def release(self, text, tag=None):
        with open(os.path.join(self.dev, "game.py"), "w") as f:
            f.write(text + "\n")
        git(self.dev, "add", "game.py")
        git(self.dev, "commit", "-qm", text)
        git(self.dev, "push", "-q", "origin", "main")
        if tag:
            git(self.dev, "tag", "-a", tag, "-m", tag)
            git(self.dev, "push", "-q", "origin", tag)

    def running(self):
        with open(os.path.join(self.cab, "game.py")) as f:
            return f.read().strip()

    def head(self):
        return git(self.cab, "rev-parse", "HEAD")

    def clean(self):
        return git(self.cab, "status", "--porcelain", "--untracked-files=no") == ""

    def boot(self):
        """Run the cabinet's start.sh with a python3 that does nothing."""
        shutil.copy(os.path.join(REPO, "start.sh"), os.path.join(self.cab, "start.sh"))
        bindir = os.path.join(self.cab, ".stubbin")
        os.makedirs(bindir, exist_ok=True)
        stub = os.path.join(bindir, "python3")
        with open(stub, "w") as f:
            f.write("#!/bin/sh\nexit 0\n")
        os.chmod(stub, 0o755)
        env = dict(os.environ, PATH=bindir + os.pathsep + os.environ["PATH"])
        subprocess.run(["bash", os.path.join(self.cab, "start.sh")], env=env,
                       capture_output=True, text=True, check=True)


@pytest.fixture
def world(tmp_path, monkeypatch):
    w = World(tmp_path)
    monkeypatch.setattr(refresh, "REPO_DIR", w.cab)
    monkeypatch.setattr(refresh, "ROLLBACK_FILE", os.path.join(w.cab, ".rollback_ref"))
    monkeypatch.setattr(refresh, "HOLD_FILE", os.path.join(w.cab, ".rollback_hold"))
    monkeypatch.setattr(refresh, "LOG_FILE", os.path.join(w.cab, ".update.log"))
    monkeypatch.setattr(refresh, "_last_error", "")
    return w


def as_distribution(world, monkeypatch, at="v1.0"):
    monkeypatch.setattr(refresh, "DEV", False)
    git(world.cab, "checkout", "-q", at)


def as_dev(world, monkeypatch):
    monkeypatch.setattr(refresh, "DEV", True)
    open(os.path.join(world.cab, ".dev"), "w").close()


# --- rollback -----------------------------------------------------------------

@pytest.mark.parametrize("mode", ["distribution", "dev"])
def test_rollback_moves_head_and_leaves_a_clean_checkout(world, monkeypatch, mode):
    if mode == "dev":
        as_dev(world, monkeypatch)
        git(world.cab, "reset", "-q", "--hard", "v1.0")
    else:
        as_distribution(world, monkeypatch)
    old = world.head()
    assert refresh._apply_update() == (True, "UPDATED")
    new = world.head()
    assert world.running() == "two"

    assert refresh._apply_rollback(old)
    assert world.head() == old            # the old code moved only the files
    assert world.running() == "one"
    assert world.clean()
    with open(refresh.HOLD_FILE) as f:
        assert f.read().strip() == new


@pytest.mark.parametrize("mode", ["distribution", "dev"])
def test_update_after_rollback_really_updates(world, monkeypatch, mode):
    """The bug: after RLBK, UPDATE said UP TO DATE and kept the old files."""
    if mode == "dev":
        as_dev(world, monkeypatch)
        git(world.cab, "reset", "-q", "--hard", "v1.0")
    else:
        as_distribution(world, monkeypatch)
    old = world.head()
    refresh._apply_update()
    refresh._apply_rollback(old)

    assert refresh._apply_update() == (True, "UPDATED")
    assert world.running() == "two"
    assert world.clean()
    assert not os.path.exists(refresh.HOLD_FILE)

    world.release("three", "v1.2")        # and the release after that still lands
    assert refresh._apply_update() == (True, "UPDATED")
    assert world.running() == "three"


@pytest.mark.parametrize("mode", ["distribution", "dev"])
def test_rollback_survives_a_power_cycle_until_a_newer_version(world, monkeypatch, mode):
    if mode == "dev":
        as_dev(world, monkeypatch)
        git(world.cab, "reset", "-q", "--hard", "v1.0")
    else:
        as_distribution(world, monkeypatch)
    old = world.head()
    refresh._apply_update()
    refresh._apply_rollback(old)

    world.boot()
    world.boot()
    assert world.running() == "one"       # start.sh did not undo the rollback

    world.release("three", "v1.2")
    world.boot()
    assert world.running() == "three"     # a newer version ends the hold
    assert not os.path.exists(refresh.HOLD_FILE)


@pytest.mark.parametrize("mode", ["distribution", "dev"])
def test_boot_still_updates_a_cabinet_that_never_rolled_back(world, monkeypatch, mode):
    if mode == "dev":
        as_dev(world, monkeypatch)
        git(world.cab, "reset", "-q", "--hard", "v1.0")
    else:
        as_distribution(world, monkeypatch)
    world.boot()
    assert world.running() == "two"


# --- failures are recorded and shown -------------------------------------------

def test_a_failed_fetch_is_a_failure_and_is_logged(world, monkeypatch):
    as_distribution(world, monkeypatch, at="v1.1")
    git(world.cab, "remote", "set-url", "origin", os.path.join(world.cab, "nowhere.git"))

    assert refresh._apply_update() == (False, "FAILED")   # was: UP TO DATE
    with open(refresh.LOG_FILE) as f:
        log = f.read()
    assert "git fetch --tags --force origin" in log
    assert "nowhere.git" in log                           # git's own words
    assert refresh._reason(refresh._last_error) == "NO NETWORK"


def test_a_blocked_checkout_names_its_reason(world, monkeypatch):
    as_distribution(world, monkeypatch)
    with open(os.path.join(world.cab, "game.py"), "w") as f:
        f.write("edited on the cabinet\n")

    assert refresh._apply_update() == (False, "FAILED")
    assert refresh._reason(refresh._last_error) == "FILES CHANGED"
    assert world.running() == "edited on the cabinet"


def test_a_timeout_is_logged(world, monkeypatch):
    def slow(*a, **k):
        raise subprocess.TimeoutExpired(a[0], k.get("timeout"))
    monkeypatch.setattr(subprocess, "run", slow)
    assert refresh._git("fetch", "origin", timeout=7) == (False, "")
    assert refresh._reason(refresh._last_error) == "TIMED OUT"
    with open(refresh.LOG_FILE) as f:
        assert "timed out after 7s" in f.read()


def test_a_failed_update_stays_on_screen_and_does_not_restart(sandbox, monkeypatch):
    def no_restart(*a):
        raise AssertionError("restarted after a failed update")
    monkeypatch.setattr(os, "execv", no_restart)
    def failing_update():
        refresh._last_error = "timed out after 180s"
        return False, "FAILED"
    monkeypatch.setattr(refresh, "_last_error", "")
    monkeypatch.setattr(refresh, "_apply_update", failing_update)

    v = refresh.Refresh(Display())
    v.reset()
    v.selection, v.confirmed = 0, True
    for _ in range(120):                   # four seconds
        v.update(1 / 30)
        v.draw()
    assert v.fail_reason == "TIMED OUT"
    assert not getattr(v, "wants_exit", False)

    press = InputState()
    press.action_l = True
    v.handle_input(press)
    assert v.wants_exit


# --- a ref file emptied by a power cut ------------------------------------------

def _empty_a_ref(world):
    """What a power cut mid-fetch leaves behind: a ref file with nothing in it.
    Every later fetch then dies with "bad object refs/remotes/origin/..."."""
    d = os.path.join(world.cab, ".git", "refs", "remotes", "origin", "fix")
    os.makedirs(d)
    open(os.path.join(d, "gone"), "w").close()


def test_boot_updates_past_an_empty_ref(world, monkeypatch):
    as_distribution(world, monkeypatch)
    _empty_a_ref(world)
    world.release("three", "v1.2")
    world.boot()
    assert world.running() == "three"


def test_menu_updates_past_an_empty_ref(world, monkeypatch):
    as_distribution(world, monkeypatch)
    _empty_a_ref(world)
    world.release("three", "v1.2")
    assert refresh._apply_update() == (True, "UPDATED")
    assert world.running() == "three"
