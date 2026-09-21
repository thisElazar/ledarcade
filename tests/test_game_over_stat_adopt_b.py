"""
Tests for game_over_stat() adoption across game files.

Each game must implement game_over_stat() to return the stat line
drawn on its game-over screen (besides the score), in 16 chars or less.
"""

import pytest
from tests._harness import get_sim_display
from games.skifree import SkiFree
from games.bloonstd import BloonsTD
from games.monstermaze import MonsterMaze
from games.windowwasher import WindowWasher
from games.portal import Portal
from games.pong import Pong


class TestSkiFreeGameOverStat:
    def test_game_over_stat_returns_style(self):
        display = get_sim_display()
        game = SkiFree(display)
        game.reset()
        game.style = 42

        stat = game.game_over_stat()
        assert stat == "STYLE:42"
        assert len(stat) <= 16

    def test_game_over_stat_zero_style(self):
        display = get_sim_display()
        game = SkiFree(display)
        game.reset()
        game.style = 0

        stat = game.game_over_stat()
        assert stat == "STYLE:0"
        assert len(stat) <= 16

    def test_game_over_stat_high_style(self):
        display = get_sim_display()
        game = SkiFree(display)
        game.reset()
        game.style = 999

        stat = game.game_over_stat()
        assert stat == "STYLE:999"
        assert len(stat) <= 16


class TestBloonsTDGameOverStat:
    def test_game_over_stat_returns_wave(self):
        display = get_sim_display()
        game = BloonsTD(display)
        game.reset()
        game.wave_num = 5

        stat = game.game_over_stat()
        assert stat == "WAVE:5"
        assert len(stat) <= 16

    def test_game_over_stat_zero_wave(self):
        display = get_sim_display()
        game = BloonsTD(display)
        game.reset()
        game.wave_num = 0

        stat = game.game_over_stat()
        assert stat == "WAVE:0"
        assert len(stat) <= 16

    def test_game_over_stat_high_wave(self):
        display = get_sim_display()
        game = BloonsTD(display)
        game.reset()
        game.wave_num = 20

        stat = game.game_over_stat()
        assert stat == "WAVE:20"
        assert len(stat) <= 16


class TestMonsterMazeGameOverStat:
    def test_game_over_stat_returns_level(self):
        display = get_sim_display()
        game = MonsterMaze(display)
        game.reset()
        game.level = 3

        stat = game.game_over_stat()
        assert stat == "LEVEL:3"
        assert len(stat) <= 16

    def test_game_over_stat_level_one(self):
        display = get_sim_display()
        game = MonsterMaze(display)
        game.reset()
        game.level = 1

        stat = game.game_over_stat()
        assert stat == "LEVEL:1"
        assert len(stat) <= 16

    def test_game_over_stat_high_level(self):
        display = get_sim_display()
        game = MonsterMaze(display)
        game.reset()
        game.level = 99

        stat = game.game_over_stat()
        assert stat == "LEVEL:99"
        assert len(stat) <= 16


class TestWindowWasherGameOverStat:
    def test_game_over_stat_returns_level(self):
        display = get_sim_display()
        game = WindowWasher(display)
        game.reset()
        game.level = 2

        stat = game.game_over_stat()
        assert stat == "LEVEL:2"
        assert len(stat) <= 16

    def test_game_over_stat_level_one(self):
        display = get_sim_display()
        game = WindowWasher(display)
        game.reset()
        game.level = 1

        stat = game.game_over_stat()
        assert stat == "LEVEL:1"
        assert len(stat) <= 16

    def test_game_over_stat_high_level(self):
        display = get_sim_display()
        game = WindowWasher(display)
        game.reset()
        game.level = 50

        stat = game.game_over_stat()
        assert stat == "LEVEL:50"
        assert len(stat) <= 16


class TestPortalGameOverStat:
    def test_game_over_stat_returns_chamber(self):
        display = get_sim_display()
        game = Portal(display)
        game.reset()
        game.chamber = 3

        stat = game.game_over_stat()
        assert stat == "CHAMBER 4"
        assert len(stat) <= 16

    def test_game_over_stat_chamber_one(self):
        display = get_sim_display()
        game = Portal(display)
        game.reset()
        game.chamber = 0

        stat = game.game_over_stat()
        assert stat == "CHAMBER 1"
        assert len(stat) <= 16

    def test_game_over_stat_high_chamber(self):
        display = get_sim_display()
        game = Portal(display)
        game.reset()
        game.chamber = 99

        stat = game.game_over_stat()
        assert stat == "CHAMBER 100"
        assert len(stat) <= 16


class TestPongGameOverStat:
    def test_game_over_stat_returns_final_score(self):
        display = get_sim_display()
        game = Pong(display)
        game.reset()
        game.score = 8
        game.ai_score = 11

        stat = game.game_over_stat()
        assert stat == "FINAL:8-11"
        assert len(stat) <= 16

    def test_game_over_stat_zero_scores(self):
        display = get_sim_display()
        game = Pong(display)
        game.reset()
        game.score = 0
        game.ai_score = 0

        stat = game.game_over_stat()
        assert stat == "FINAL:0-0"
        assert len(stat) <= 16

    def test_game_over_stat_high_scores(self):
        display = get_sim_display()
        game = Pong(display)
        game.reset()
        game.score = 11
        game.ai_score = 9

        stat = game.game_over_stat()
        assert stat == "FINAL:11-9"
        assert len(stat) <= 16
