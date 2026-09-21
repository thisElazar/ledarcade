"""
Tests for game_over_stat() adoption across game files.

Each game must implement game_over_stat() to return the stat line
drawn on its game-over screen (besides the score), in 16 chars or less.
"""

import pytest
from tests._harness import get_sim_display
from games.tetris import Tetris
from games.burgertime import BurgerTime
from games.qbert import QBert
from games.jezzball import JezzBall
from games.bomberman import Bomberman
from games.dnd import DnD


class TestTetrisGameOverStat:
    def test_game_over_stat_returns_lines(self):
        display = get_sim_display()
        game = Tetris(display)
        game.reset()
        game.lines = 5

        stat = game.game_over_stat()
        assert stat == "LINES:5"
        assert len(stat) <= 16

    def test_game_over_stat_zero_lines(self):
        display = get_sim_display()
        game = Tetris(display)
        game.reset()
        game.lines = 0

        stat = game.game_over_stat()
        assert stat == "LINES:0"
        assert len(stat) <= 16

    def test_game_over_stat_high_lines(self):
        display = get_sim_display()
        game = Tetris(display)
        game.reset()
        game.lines = 100

        stat = game.game_over_stat()
        assert stat == "LINES:100"
        assert len(stat) <= 16


class TestBurgerTimeGameOverStat:
    def test_game_over_stat_returns_level(self):
        display = get_sim_display()
        game = BurgerTime(display)
        game.reset()
        game.level = 3

        stat = game.game_over_stat()
        assert stat == "LEVEL:3"
        assert len(stat) <= 16

    def test_game_over_stat_level_one(self):
        display = get_sim_display()
        game = BurgerTime(display)
        game.reset()
        game.level = 1

        stat = game.game_over_stat()
        assert stat == "LEVEL:1"
        assert len(stat) <= 16

    def test_game_over_stat_high_level(self):
        display = get_sim_display()
        game = BurgerTime(display)
        game.reset()
        game.level = 99

        stat = game.game_over_stat()
        assert stat == "LEVEL:99"
        assert len(stat) <= 16


class TestQBertGameOverStat:
    def test_game_over_stat_returns_level(self):
        display = get_sim_display()
        game = QBert(display)
        game.reset()
        game.level = 3

        stat = game.game_over_stat()
        assert stat == "LEVEL:3"
        assert len(stat) <= 16

    def test_game_over_stat_level_one(self):
        display = get_sim_display()
        game = QBert(display)
        game.reset()
        game.level = 1

        stat = game.game_over_stat()
        assert stat == "LEVEL:1"
        assert len(stat) <= 16

    def test_game_over_stat_high_level(self):
        display = get_sim_display()
        game = QBert(display)
        game.reset()
        game.level = 50

        stat = game.game_over_stat()
        assert stat == "LEVEL:50"
        assert len(stat) <= 16


class TestJezzBallGameOverStat:
    def test_game_over_stat_returns_level(self):
        display = get_sim_display()
        game = JezzBall(display)
        game.reset()
        game.level = 2

        stat = game.game_over_stat()
        assert stat == "LEVEL:2"
        assert len(stat) <= 16

    def test_game_over_stat_level_one(self):
        display = get_sim_display()
        game = JezzBall(display)
        game.reset()
        game.level = 1

        stat = game.game_over_stat()
        assert stat == "LEVEL:1"
        assert len(stat) <= 16

    def test_game_over_stat_high_level(self):
        display = get_sim_display()
        game = JezzBall(display)
        game.reset()
        game.level = 50

        stat = game.game_over_stat()
        assert stat == "LEVEL:50"
        assert len(stat) <= 16


class TestBombermanGameOverStat:
    def test_game_over_stat_returns_level(self):
        display = get_sim_display()
        game = Bomberman(display)
        game.reset()
        game.level = 2

        stat = game.game_over_stat()
        assert stat == "LEVEL:2"
        assert len(stat) <= 16

    def test_game_over_stat_level_one(self):
        display = get_sim_display()
        game = Bomberman(display)
        game.reset()
        game.level = 1

        stat = game.game_over_stat()
        assert stat == "LEVEL:1"
        assert len(stat) <= 16

    def test_game_over_stat_high_level(self):
        display = get_sim_display()
        game = Bomberman(display)
        game.reset()
        game.level = 50

        stat = game.game_over_stat()
        assert stat == "LEVEL:50"
        assert len(stat) <= 16


class TestDnDGameOverStat:
    def test_game_over_stat_returns_depth(self):
        display = get_sim_display()
        game = DnD(display)
        game.reset()
        game.level = 3

        stat = game.game_over_stat()
        assert stat == "DEPTH:3"
        assert len(stat) <= 16

    def test_game_over_stat_level_one(self):
        display = get_sim_display()
        game = DnD(display)
        game.reset()
        game.level = 1

        stat = game.game_over_stat()
        assert stat == "DEPTH:1"
        assert len(stat) <= 16

    def test_game_over_stat_high_level(self):
        display = get_sim_display()
        game = DnD(display)
        game.reset()
        game.level = 99

        stat = game.game_over_stat()
        assert stat == "DEPTH:99"
        assert len(stat) <= 16
