"""DOOM's pre-game menu, its attract-mode visual, and the AFTER HOURS gate on
the idle screen. The engine itself never runs here (the sandbox blocks Popen)."""
import pytest

import catalog
import levers
import settings
from arcade import GameState, InputState
import games.doom as doom
from games.doom import Doom, _Choice, _Menu
from visuals.doomdemo import DoomDemo
from _harness import get_sim_display


@pytest.fixture(autouse=True)
def _no_saved_doom_state(sandbox):
    """Start every test from a cabinet that has never played DOOM."""
    settings._settings.pop("doom", None)


def _choices():
    return [_Choice("PHASE 1 E1", "/x/freedoom1.wad", 1, 9),
            _Choice("PHASE 1 E2", "/x/freedoom1.wad", 2, 9),
            _Choice("PHASE 2", "/x/freedoom2.wad", 0, 32)]


def test_menu_defaults_and_launch_args(sandbox):
    m = _Menu(_choices())
    assert [m.value(i) for i in range(3)] == ["PHASE 1 E1", "HURT ME", "E1M1"]
    assert m.new_game_args() == ["-skill", "3", "-warp", "1", "1"]
    m.move(1, 0)                                   # GAME row: next game
    m.move(1, 0)
    assert m.value(0) == "PHASE 2" and m.value(2) == "MAP01"
    assert m.new_game_args() == ["-skill", "3", "-warp", "1"]   # Doom II style warp
    m.move(0, 1)                                   # SKILL row
    m.move(-1, 0)
    m.move(-1, 0)
    m.move(-1, 0)
    assert m.skill == 5 and m.value(1) == "NIGHTMARE"
    m.move(0, 1)                                   # MAP row: nothing reached yet
    m.move(1, 0)
    assert m.map == 1


def test_menu_offers_maps_up_to_the_furthest_reached(sandbox):
    m = _Menu(_choices())
    m.row = 2
    m.record_cleared(m.choice, 4)                            # E1M3 done, E1M4 is next
    m.move(1, 0)
    m.move(1, 0)
    m.move(1, 0)
    assert m.value(2) == "E1M4"
    m.move(1, 0)
    assert m.value(2) == "E1M1"                    # wraps within the reached maps
    m.move(0, -2)                                  # back to the GAME row
    m.map = 4
    m.move(1, 0)                                   # another game: progress is per game
    assert m.value(0) == "PHASE 1 E2" and m.map == 1
    m.record_cleared(m.choice, 2)
    m.save()
    again = _Menu(_choices())                      # a fresh menu picks the saved state up
    assert again.game == 1 and again.skill == 3 and again.furthest() == 2
    assert again.progress == {"freedoom1.wad:1": 4, "freedoom1.wad:2": 2}
    assert settings.get("doom")["progress"] == again.progress


def test_menu_caps_progress_at_the_wads_last_map(sandbox):
    m = _Menu(_choices())
    m.record_cleared(m.choice, 99)
    assert m.furthest() == 9


def test_game_shows_the_menu_until_a_button_starts_the_engine(sandbox, monkeypatch):
    monkeypatch.setattr(doom, "_available", lambda: True)
    monkeypatch.setattr(doom, "_choices", _choices)
    g = Doom(get_sim_display())
    assert g.state == GameState.PLAYING and g._engine is None
    inp = InputState()
    for _ in range(5):
        inp.reset()
        g.update(inp, 1 / 30)
        g.draw()
    inp.reset()
    inp.down_pressed = True
    g.update(inp, 1 / 30)
    assert g._menu.row == 1
    inp.reset()
    inp.action_l = True
    g.update(inp, 1 / 30)                          # start: the sandbox blocks the engine
    assert g.state == GameState.GAME_OVER
    assert settings.get("doom")["skill"] == 3     # the choice was saved on the way in
    assert "doom_pipe" in str(sandbox[-1][0])
    g.reset()                                      # PLAY AGAIN: back to the menu, not game over
    assert g.state == GameState.PLAYING and g._engine is None


def test_game_without_engine_files_is_game_over(sandbox, monkeypatch):
    monkeypatch.setattr(doom, "_available", lambda: False)
    assert Doom(get_sim_display()).state == GameState.GAME_OVER


def test_demo_is_mature_and_kept_off_the_idle_screen(sandbox, monkeypatch):
    from visuals import Plasma
    from visuals.slideshow import AllVisuals
    import run_arcade
    monkeypatch.setattr(DoomDemo, "menu_visible", staticmethod(lambda: True))
    monkeypatch.setattr("visuals.ALL_VISUALS", [DoomDemo, Plasma])
    assert DoomDemo.mature and DoomDemo.category == "demos"
    assert not catalog.listed_now(DoomDemo) and catalog.listed_now(Plasma)
    assert DoomDemo not in AllVisuals._get_visual_classes(AllVisuals)
    for _ in range(10):
        assert type(run_arcade._pick_idle_visual(get_sim_display())) is Plasma
    levers.set_after_hours(True)
    assert catalog.listed_now(DoomDemo)
    assert DoomDemo in AllVisuals._get_visual_classes(AllVisuals)
    monkeypatch.setattr(DoomDemo, "menu_visible", staticmethod(lambda: False))
    assert not catalog.listed_now(DoomDemo)       # lever on but no engine installed


def test_demo_runs_blank_when_the_engine_cannot_start(sandbox):
    d = DoomDemo(get_sim_display())
    assert d._engine is None
    d.update(1 / 30)
    d.draw()
    d.close()
    d.close()
    d.reset()


def test_slideshow_closes_the_visual_it_drops(sandbox):
    from visuals.slideshow import Slideshow
    closed = []

    class Fake:
        def __init__(self, display):
            pass

        def reset(self):
            pass

        def handle_input(self, inp):
            return False

        def close(self):
            closed.append(self)

    class Show(Slideshow):
        visual_classes = [Fake, Fake]

    s = Show(get_sim_display())
    first = s._child
    s._advance()
    assert closed == [first]
    s.close()
    assert len(closed) == 2 and s._child is None


# ── saves ────────────────────────────────────────────────────────
# Slot 0 is AUTO (a new game saves itself there), 1-3 are FILE 1-3.

class _FakeProc:
    def poll(self):
        return None


class _FakeEngine:
    """Stands in for the engine: answers save() the way doom_pipe does."""

    def __init__(self, can_save=1, episode=1, level=2):
        self.proc, self.frame, self.mask = _FakeProc(), None, None
        self.saved_slots, self.closed = [], False
        self.state = dict(in_level=True, gamestate=0, health=100, can_save=can_save,
                          save_serial=0, episode=episode, map=level, owned=0, weapon=0,
                          ammo_all=[0] * 4, wi=dict(state=1, next=-1))

    def key(self, pressed, k):
        pass

    def save(self, slot):
        self.saved_slots.append(slot)
        if self.state['health'] > 0 and self.state['in_level']:
            self.state = dict(self.state, save_serial=self.state['save_serial'] + 1)

    def close(self):
        self.closed = True


@pytest.fixture
def save_dir(monkeypatch, tmp_path):
    """Point the save folder at a temp dir; returns a function that writes a slot's file."""
    monkeypatch.setattr(doom, "_DOOM_DIR", str(tmp_path))
    (tmp_path / ".savegame").mkdir()

    def write(slot, data=b"x"):
        (tmp_path / ".savegame" / f"doomsav{slot}.dsg").write_bytes(data)
    return write


def _playing(monkeypatch, engine, frames_idle=0):
    """A Doom whose engine is `engine`, started by pressing L on the menu's current row."""
    monkeypatch.setattr(doom, "_available", lambda: True)
    monkeypatch.setattr(doom, "_choices", _choices)
    launched = []
    monkeypatch.setattr(doom, "start_engine", lambda iwad, args: launched.append((iwad, args)) or engine)
    g = Doom(get_sim_display())
    inp = InputState()
    inp.action_l = True
    g.update(inp, 1 / 30)
    _idle(g, frames_idle)
    return g, launched


def _idle(g, frames, **held):
    inp = InputState()
    for k, v in held.items():
        setattr(inp, k, v)
    for _ in range(frames):
        g.update(inp, 1 / 30)


E1, E2, P2 = "freedoom1.wad:1", "freedoom1.wad:2", "freedoom2.wad:0"


def test_menu_lists_slots_only_while_their_files_exist(sandbox, save_dir):
    m = _Menu(_choices())
    assert m._rows() == [0, 1, 2] and m.row == 0 and m.hint() == "L OR R START"
    m.record_save(0, _choices()[0], "E1M3")
    assert m.held(0) is None and m._rows() == [0, 1, 2]     # recorded, but no file on disk
    save_dir(0)
    assert m.held(0)[1] == "E1M3"
    assert m._rows() == [0, 1, 2, 3, 4, 5, 6]               # AUTO, and three empty files to store it in
    m.move(0, -1)
    m.move(0, -1)
    m.move(0, -1)
    m.move(0, -1)
    assert m.row == 3 and m.value(3) == "E1M3" and m.hint() == "L OR R LOAD"
    choice, slot, args = m.press(False, True)
    assert (choice.key, slot, args) == (E1, 0, ["-loadgame", "0"])
    m.move(0, 1)
    assert m.row == 4 and m.value(4) == "EMPTY" and m.hint() == "R STORE AUTO"
    assert m.press(True, False) is None                     # nothing to load from an empty file


def test_storing_auto_into_a_file_and_replacing_one(sandbox, save_dir, tmp_path):
    m = _Menu(_choices())
    m.record_save(0, _choices()[0], "E1M3")
    save_dir(0, b"first game")
    m.row = 5                                               # FILE 2
    assert m.press(False, True) is None                     # R: store
    assert (tmp_path / ".savegame" / "doomsav2.dsg").read_bytes() == b"first game"
    assert m.held(2)[1] == "E1M3" and m.hint() == "L LOAD  R STORE"
    choice, slot, args = m.press(True, False)               # L: load it; it keeps saving to FILE 2
    assert (choice.key, slot, args) == (E1, 2, ["-loadgame", "2"])

    m.record_save(0, _choices()[2], "MAP07")                # a new game has taken AUTO since
    save_dir(0, b"second game")
    m.row = 5
    assert m.press(False, True) is None                     # R on a file in use: asks first
    assert m.armed == 2 and m.value(5) == "REPLACE?" and m.hint() == "R AGAIN REPLACES"
    assert (tmp_path / ".savegame" / "doomsav2.dsg").read_bytes() == b"first game"
    m.move(0, 1)                                            # moving away cancels
    assert m.armed is None and m.held(2)[1] == "E1M3"
    m.row = 5
    m.press(False, True)
    m.press(False, True)                                    # R twice: replaced
    assert (tmp_path / ".savegame" / "doomsav2.dsg").read_bytes() == b"second game"
    assert m.held(2)[0].key == P2 and m.held(2)[1] == "MAP07"

    again = _Menu(_choices())                               # all of it persists
    assert again.held(0)[1] == "MAP07" and again.held(2)[1] == "MAP07" and again.held(1) is None
    assert again.row == 3                                   # cursor starts on the slot played last


def test_a_slot_for_a_wad_that_is_not_installed_is_not_offered(sandbox, save_dir):
    settings.set("doom", {"saves": {"1": {"game": "plutonia.wad:0", "label": "MAP03"},
                                    "9": {"game": E1, "label": "E1M1"}, "2": "junk"}})
    save_dir(1)
    m = _Menu(_choices())
    assert m.held(1) is None and m._rows() == [0, 1, 2] and m.saves.keys() == {1}


def test_new_game_autosaves_to_auto_each_level(sandbox, save_dir, monkeypatch):
    e = _FakeEngine()
    g, launched = _playing(monkeypatch, e, frames_idle=20)
    assert launched == [("/x/freedoom1.wad", ["-skill", "3", "-warp", "1", "1"])] and e.saved_slots == []
    _idle(g, 15)                                            # a second into the level
    assert e.saved_slots == [0]
    _idle(g, 90)
    assert e.saved_slots == [0]                             # once per level
    assert g._menu.saves == {0: {"game": E1, "label": "E1M2"}} and g._menu.last == 0
    e.state = dict(e.state, health=0)                       # dying does not save
    _idle(g, 60)
    e.state = dict(e.state, gamestate=1)                    # nor does the tally
    _idle(g, 60)
    assert e.saved_slots == [0]
    e.state = dict(e.state, gamestate=0, health=80, map=3)
    _idle(g, 40)
    assert e.saved_slots == [0, 0]
    assert g._menu.saves[0] == {"game": E1, "label": "E1M3"}


def test_a_loaded_file_keeps_saving_to_itself(sandbox, save_dir, monkeypatch):
    settings.set("doom", {"game": 0, "last": 2, "saves": {"2": {"game": P2, "label": "MAP07"}}})
    save_dir(2)
    e = _FakeEngine(episode=1, level=7)
    g, launched = _playing(monkeypatch, e, frames_idle=40)  # the cursor starts on FILE 2
    assert launched == [("/x/freedoom2.wad", ["-loadgame", "2"])] and g._loading is None
    assert e.saved_slots == [2]
    e.state = dict(e.state, map=8)
    _idle(g, 40)
    assert e.saved_slots == [2, 2]
    assert g._menu.saves == {2: {"game": P2, "label": "MAP08"}}       # AUTO untouched


def test_quit_saves_first_and_stops_the_engine(sandbox, save_dir, monkeypatch):
    e = _FakeEngine()
    g, _ = _playing(monkeypatch, e, frames_idle=40)
    assert e.saved_slots == [0]
    _idle(g, 70, action_l_held=True, action_r_held=True)
    assert g.state == GameState.GAME_OVER and e.closed and g._engine is None
    assert e.saved_slots == [0, 0]                          # level start, then the quit
    assert e.state["save_serial"] == 2


def test_the_shells_own_exit_saves_too(sandbox, save_dir, monkeypatch):
    """The shell's hold-both exit calls close() without update() ever seeing the hold."""
    e = _FakeEngine()
    g, _ = _playing(monkeypatch, e, frames_idle=40)
    e.state = dict(e.state, map=5)
    g.close()
    assert e.saved_slots == [0, 0] and e.closed and g._engine is None
    assert g._menu.saves[0] == {"game": E1, "label": "E1M5"}
    g.close()                                               # closing twice is harmless
    assert e.saved_slots == [0, 0]


def test_quit_while_dead_keeps_the_level_start_save(sandbox, save_dir, monkeypatch):
    e = _FakeEngine()
    g, _ = _playing(monkeypatch, e, frames_idle=40)
    e.state = dict(e.state, health=0)
    g.close()
    assert e.closed and e.saved_slots == [0]


def test_an_engine_without_the_save_command_is_never_asked(sandbox, save_dir, monkeypatch):
    e = _FakeEngine(can_save=0)
    g, _ = _playing(monkeypatch, e, frames_idle=90)
    g.close()
    assert e.saved_slots == [] and g._menu.saves == {} and e.closed


def test_a_failed_load_forgets_the_slot_and_returns_to_the_menu(sandbox, save_dir, monkeypatch):
    settings.set("doom", {"game": 0, "last": 1, "saves": {"1": {"game": E1, "label": "E1M5"}}})
    save_dir(1)
    e = _FakeEngine()
    e.state = dict(e.state, in_level=False, gamestate=3)    # the load went nowhere
    monkeypatch.setattr(doom, "LOAD_TIMEOUT", 0.0)
    g, launched = _playing(monkeypatch, e, frames_idle=2)
    assert launched == [("/x/freedoom1.wad", ["-loadgame", "1"])]
    assert g._engine is None and g.state == GameState.PLAYING and e.closed     # back in the menu
    assert g._menu.saves == {} and g._menu.row == 0 and e.saved_slots == []
