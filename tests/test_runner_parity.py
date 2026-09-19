"""The laptop launcher and the cabinet launcher must treat a running item alike.

`run_arcade.py` (sim) and `run_hardware.py` (cabinet, under systemd) are two
hand-maintained copies of the same ~1000-line state machine: menu, launch,
hold-both-to-exit, custom-exit visuals, game over, initials entry, play again.
A fix applied to one and forgotten in the other ships a cabinet that behaves
differently from everything that was tested on the laptop.

Both launchers are run here for real against a tiny spy catalog, fed the same
scripted session with a deterministic clock. Every call the launcher makes into
an item (and into the high-score table) is logged, and the two logs must match
exactly. Absolute assertions pin the behaviour itself, so two launchers that are
wrong in the same way still fail.
"""
import pytest

import arcade
import run_arcade
import run_hardware
from arcade import GameState
from catalog import Category
from _harness import script_from_held

TICK = 1 / 32  # exact in binary, so both launchers accumulate identical timers
BOTH = {"action_l", "action_r"}


def secs(s):
    return int(round(s / TICK))


# ── spy catalog ─────────────────────────────────────────────────────

def make_catalog(log):
    def note(*event):
        log.append(event + (log.frame,))

    class SpyVisual:
        name = "SPY VISUAL"
        category = "spy"

        def __init__(self, display):
            self.wants_exit = False
            note("init", self.name)

        def reset(self):
            note("reset", self.name)

        def handle_input(self, inp):
            note("handle_input", self.name)
            if inp.right_pressed:
                self.wants_exit = True
            return False

        def update(self, dt):
            note("update", self.name, dt)

        def draw(self):
            note("draw", self.name)

    class SpyOwnExit(SpyVisual):
        """Like CONTROLS: opts out of hold-to-exit and leaves on its own terms."""
        name = "SPY OWN EXIT"
        custom_exit = True

        def handle_input(self, inp):
            note("handle_input", self.name)
            if inp.up_pressed:
                self.wants_exit = True
            return True

    class SpyGame:
        name = "SPY GAME"
        category = "spy"

        def __init__(self, display):
            self.state = GameState.PLAYING
            self.score = 0
            note("init", self.name)

        def reset(self):
            self.state = GameState.PLAYING
            self.score = 0
            note("reset", self.name)

        def update(self, inp, dt):
            note("update", self.name, dt)
            if inp.action_r and not inp.action_l_held:
                self.score = 4200
                self.state = GameState.GAME_OVER
            elif inp.down_pressed:
                self.score = 99
                self.state = GameState.WIN

        def draw(self):
            note("draw", self.name)

    class SpyTwoPlayer(SpyGame):
        name = "SPY VERSUS"
        category = "2_player"

        def draw_game_over(self, selection=0):
            note("draw_game_over", self.name)

    return [
        Category("SPY VISUALS", (1, 2, 3), "spy", [SpyVisual, SpyOwnExit]),
        Category("SPY GAMES", (3, 2, 1), "spy_games", [SpyGame, SpyTwoPlayer]),
    ]


class Log(list):
    frame = -1


class FakeScores:
    def __init__(self, log, high):
        self.log, self.high = log, high

    def log_play(self, name, score):
        self.log.append(("hsm.log_play", name, score, self.log.frame))

    def is_high_score(self, name, score):
        return self.high

    def get_top_scores(self, name, *a, **k):
        return [("AAA", 10, 0.0)] if self.high else []

    def add_score(self, name, initials, score):
        self.log.append(("hsm.add_score", name, initials, score, self.log.frame))
        return 2


class NullDisplay:
    def __init__(self, *a, **k):
        pass

    def __getattr__(self, name):
        if name == "set_label":  # only PaperDisplay has it; the sim checks
            raise AttributeError(name)
        return lambda *a, **k: None


class ScriptedInput:
    def __init__(self, log, frames):
        self.log, self.frames = log, frames

    def update(self):
        self.log.frame += 1
        if self.log.frame >= len(self.frames):
            raise KeyboardInterrupt  # end of session
        return self.frames[self.log.frame]

    def cleanup(self):
        pass


class FakeTime:
    """Stands in for the `time` module: the clock only moves when told to."""
    def __init__(self):
        self.now = 1000.0

    def time(self):
        return self.now

    def sleep(self, _seconds):
        self.now += TICK


def _common_patches(monkeypatch, mod, log, high):
    monkeypatch.setattr(mod, "register_games", lambda *_: None)
    monkeypatch.setattr(mod, "register_visuals", lambda *_: None)
    monkeypatch.setattr(mod, "get_all_categories", lambda *_: make_catalog(log))
    monkeypatch.setattr(mod, "sync_conditional_items", lambda: False)
    monkeypatch.setattr(mod, "get_high_score_manager", lambda: FakeScores(log, high))
    monkeypatch.setattr(mod, "_show_splash", lambda *a, **k: None)
    monkeypatch.setattr(mod.update_checker, "start", lambda: None)
    monkeypatch.setattr("builtins.print", lambda *a, **k: None)


def run_cabinet(monkeypatch, held_frames, high=False):
    log = Log()
    _common_patches(monkeypatch, run_hardware, log, high)
    frames = script_from_held(arcade.InputState, held_frames)
    monkeypatch.setattr(run_hardware, "_kill_boot_splash", lambda: None)
    monkeypatch.setattr(run_hardware, "HardwareDisplay", NullDisplay)
    monkeypatch.setattr(run_hardware, "HardwareInput",
                        lambda **k: ScriptedInput(log, frames))
    monkeypatch.setattr(run_hardware, "time", FakeTime())
    run_hardware.main()  # handles the KeyboardInterrupt itself
    return list(log)


def run_sim(monkeypatch, held_frames, high=False):
    log = Log()
    _common_patches(monkeypatch, run_arcade, log, high)
    frames = script_from_held(arcade.InputState, held_frames)
    clock = FakeTime()

    class FakeClock:
        def tick(self, _fps):
            clock.now += TICK
            return TICK * 1000.0

    monkeypatch.setattr(run_arcade, "InputHandler", lambda: ScriptedInput(log, frames))
    monkeypatch.setattr(run_arcade.pygame.time, "Clock", FakeClock)
    monkeypatch.setattr(run_arcade.pygame.event, "get", lambda: [])
    monkeypatch.setattr(run_arcade, "time", clock)
    monkeypatch.setattr(run_arcade.sys, "argv", ["run_arcade.py"])
    with pytest.raises(KeyboardInterrupt):
        run_arcade.main(NullDisplay)
    return list(log)


# ── scripted sessions ───────────────────────────────────────────────

def idle(n):
    return [set()] * n


def tap(*controls):
    return [set(controls), set()]


def hold(seconds, *controls):
    return [set(controls)] * secs(seconds)


SESSIONS = {
    # Launch a visual, poke it, leave by holding both buttons.
    "visual: hold both to exit":
        idle(2) + tap("action_l") + idle(3) + tap("up") + hold(0.3, "left")
        + hold(2.5, *BOTH) + idle(5),
    # One button held is not an exit; the right button launches too.
    "visual: one button never exits":
        idle(2) + tap("action_r") + hold(3.0, "action_l") + hold(3.0, "action_r") + idle(3),
    # Releasing just before 2s restarts the hold timer.
    "visual: interrupted hold restarts":
        tap("action_l") + hold(1.9, *BOTH) + idle(1) + hold(1.9, *BOTH) + idle(3),
    # custom_exit visuals are immune to hold-both and leave via wants_exit.
    "visual: custom exit":
        tap("down") + tap("action_l") + hold(3.0, *BOTH) + idle(2) + tap("up") + idle(5),
    # A hold cut short by wants_exit must not carry into the next visual.
    "visual: hold timer does not leak into the next launch":
        tap("action_l") + hold(1.5, *BOTH) + [BOTH | {"right"}] + idle(3)
        + [{"action_r"}] + hold(1.0, *BOTH) + idle(3),   # launch, never letting go
    "game: hold both to exit":
        tap("right") + tap("action_l") + idle(5) + hold(2.5, *BOTH) + idle(5),
    "game: game over, play again, game over, menu":
        tap("right") + tap("action_l") + idle(3) + tap("action_r") + idle(secs(1.7))
        + tap("action_l") + idle(2) + tap("action_l") + idle(5)            # play again
        + tap("action_r") + idle(secs(1.7)) + tap("action_l") + idle(2)
        + tap("down") + tap("action_l") + idle(5),                         # menu
    "game: input during game-over lockout is ignored":
        tap("right") + tap("action_l") + idle(2) + tap("action_r")
        + tap("action_l") + tap("action_l") + tap("down") + idle(secs(1.7))
        + tap("action_l") + tap("action_l") + idle(5),
    "game: win":
        tap("right") + tap("action_l") + idle(2) + tap("down") + idle(secs(1.7))
        + tap("action_l") + tap("down") + tap("action_r") + idle(3),
    "game: hold both exits from the game-over screen":
        tap("right") + tap("action_l") + tap("action_r") + idle(10)
        + hold(2.5, *BOTH) + idle(5),
    "2 player: no high scores":
        tap("right") + tap("down") + tap("action_l") + idle(2) + tap("action_r")
        + idle(secs(1.7)) + tap("down") + tap("action_l") + idle(5),
}

HIGH_SCORE_SESSION = (
    tap("right") + tap("action_l") + idle(2) + tap("action_r") + idle(secs(3.2))   # milestone
    + idle(secs(1.7))
    + tap("down") + idle(8) + tap("down") + idle(8)                                # A -> C
    + tap("right") + idle(8) + tap("up") + idle(8)                                 # A -> Z
    + tap("action_l") + idle(8) + tap("left") + idle(8) + tap("action_r") + idle(8)
    + tap("action_r") + idle(secs(1.2)) + tap("action_l") + tap("down") + tap("action_l")
    + idle(5)
)


@pytest.mark.parametrize("session", SESSIONS)
def test_launchers_drive_items_identically(session, monkeypatch):
    sim = run_sim(monkeypatch, SESSIONS[session])
    cabinet = run_cabinet(monkeypatch, SESSIONS[session])
    assert sim, "the session never reached an item"
    _assert_same(sim, cabinet)


def test_launchers_agree_on_high_score_entry(monkeypatch):
    sim = run_sim(monkeypatch, HIGH_SCORE_SESSION, high=True)
    cabinet = run_cabinet(monkeypatch, HIGH_SCORE_SESSION, high=True)
    _assert_same(sim, cabinet)
    added = [e for e in cabinet if e[0] == "hsm.add_score"]
    assert [e[1:4] for e in added] == [("SPY GAME", "CZA", 4200)]


def _assert_same(sim, cabinet):
    for i, (a, b) in enumerate(zip(sim, cabinet)):
        assert a == b, (
            f"launchers diverge at event {i}: sim {a} vs cabinet {b} "
            "(event, item, ..., input frame)")
    assert len(sim) == len(cabinet), (
        f"sim logged {len(sim)} events, cabinet {len(cabinet)}; "
        f"first extra: {(sim + cabinet)[min(len(sim), len(cabinet))]}")


# ── the behaviour itself, per launcher ──────────────────────────────

RUNNERS = {"sim": run_sim, "cabinet": run_cabinet}


def _frames(log, event, name):
    return [e[-1] for e in log if e[0] == event and e[1] == name]


@pytest.mark.parametrize("runner", RUNNERS)
def test_hold_both_exits_a_visual_after_two_seconds(runner, monkeypatch):
    lead = idle(2) + tap("action_l") + idle(3)
    log = RUNNERS[runner](monkeypatch, lead + hold(2.5, *BOTH) + idle(5))
    drawn = _frames(log, "draw", "SPY VISUAL")
    assert drawn, "visual never launched"
    held_for = (drawn[-1] - len(lead) + 1) * TICK
    assert 1.9 <= held_for <= 2.0, f"exited after {held_for:.2f}s of holding"


@pytest.mark.parametrize("runner", RUNNERS)
def test_single_button_never_exits_a_visual(runner, monkeypatch):
    script = SESSIONS["visual: one button never exits"]
    log = RUNNERS[runner](monkeypatch, script)
    assert _frames(log, "draw", "SPY VISUAL")[-1] == len(script) - 1


@pytest.mark.parametrize("runner", RUNNERS)
def test_custom_exit_visual_ignores_hold_and_leaves_via_wants_exit(runner, monkeypatch):
    lead = tap("down") + tap("action_l")
    script = lead + hold(3.0, *BOTH) + idle(2) + tap("up") + idle(5)
    log = RUNNERS[runner](monkeypatch, script)
    up_frame = len(lead) + secs(3.0) + 2
    seen = _frames(log, "handle_input", "SPY OWN EXIT")
    assert seen[-1] == up_frame, "did not survive the hold, or outlived wants_exit"
    # The frame that sets wants_exit is not updated or drawn.
    assert _frames(log, "draw", "SPY OWN EXIT")[-1] == up_frame - 1


@pytest.mark.parametrize("runner", RUNNERS)
def test_visual_gets_input_before_update_before_draw(runner, monkeypatch):
    log = RUNNERS[runner](monkeypatch, tap("action_l") + idle(4))
    per_frame = {}
    for e in log:
        if e[1] == "SPY VISUAL" and e[0] in ("handle_input", "update", "draw"):
            per_frame.setdefault(e[-1], []).append(e[0])
    assert per_frame and all(
        calls == ["handle_input", "update", "draw"] for calls in per_frame.values())


@pytest.mark.parametrize("runner", RUNNERS)
def test_hold_both_exits_a_game(runner, monkeypatch):
    lead = tap("right") + tap("action_l") + idle(5)
    log = RUNNERS[runner](monkeypatch, lead + hold(2.5, *BOTH) + idle(5))
    updates = _frames(log, "update", "SPY GAME")
    held_for = (updates[-1] - len(lead) + 1) * TICK
    assert 1.9 <= held_for <= 2.0, f"exited after {held_for:.2f}s of holding"


@pytest.mark.parametrize("runner", RUNNERS)
def test_every_play_is_logged_once(runner, monkeypatch):
    log = RUNNERS[runner](
        monkeypatch, SESSIONS["game: game over, play again, game over, menu"])
    plays = [e for e in log if e[0] == "hsm.log_play"]
    assert [e[1:3] for e in plays] == [("SPY GAME", 4200)] * 2
