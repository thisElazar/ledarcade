"""dev_only visuals are hidden from a distribution cabinet's menu, and must stay
out of its idle screensaver and the ALL VISUALS slideshow too. COINS stays out
of the idle screen even on a dev cabinet: its photos are gitignored."""
import pytest

import catalog
import run_arcade
import run_hardware
from visuals import ALL_VISUALS, Coins, Plasma
from visuals.slideshow import AllVisuals
from _harness import get_sim_display


def test_there_are_dev_only_visuals_to_hide():
    assert any(getattr(v, "dev_only", False) for v in ALL_VISUALS)
    assert Coins.dev_only


def test_dev_only_is_not_listed_on_a_distribution_cabinet(monkeypatch):
    monkeypatch.setattr(catalog, "DEV_MODE", False)
    assert catalog.listed_now(Plasma)
    assert not [v.__name__ for v in ALL_VISUALS
                if getattr(v, "dev_only", False) and catalog.listed_now(v)]
    assert not [v.__name__ for v in AllVisuals._get_visual_classes(AllVisuals)
                if getattr(v, "dev_only", False)]
    monkeypatch.setattr(catalog, "DEV_MODE", True)
    assert catalog.listed_now(Coins)


@pytest.mark.parametrize("runner", [run_arcade, run_hardware])
@pytest.mark.parametrize("dev_mode", [False, True])
def test_idle_screen_never_picks_coins(sandbox, monkeypatch, runner, dev_mode):
    monkeypatch.setattr(catalog, "DEV_MODE", dev_mode)
    monkeypatch.setattr("visuals.ALL_VISUALS", [Coins, Plasma])
    for _ in range(10):
        assert type(runner._pick_idle_visual(get_sim_display())) is Plasma


@pytest.mark.parametrize("runner", [run_arcade, run_hardware])
def test_idle_screen_skips_dev_only_on_a_distribution_cabinet(sandbox, monkeypatch, runner):
    class Hidden(Plasma):
        dev_only = True

    monkeypatch.setattr(catalog, "DEV_MODE", False)
    monkeypatch.setattr("visuals.ALL_VISUALS", [Hidden])
    assert runner._pick_idle_visual(get_sim_display()) is None
    monkeypatch.setattr(catalog, "DEV_MODE", True)
    assert type(runner._pick_idle_visual(get_sim_display())) is Hidden
