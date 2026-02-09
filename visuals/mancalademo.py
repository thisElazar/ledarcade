"""
Mancala Demo - AI vs AI Attract Mode
=====================================
Two AIs play Mancala using simple heuristics: prefer free turns,
then captures, then the pit with the most seeds.
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState
import random
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.mancala import Mancala, PLAYER_1, PLAYER_2


class MancalaDemo(Visual):
    name = "MANCALA"
    description = "AI plays Mancala"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = Mancala(self.display)
        self.game.reset()
        self.think_timer = 0.0
        self.think_delay = 0.0
        self.target_pit = None
        self.nav_timer = 0.0
        self.game_over_timer = 0.0
        self.ai_state = "thinking"

    def handle_input(self, input_state):
        return False

    def _lands_in_store(self, pit_local):
        """Check if sowing from pit_local (0-5) lands in own store."""
        player = self.game.current_player
        offset = 0 if player == PLAYER_1 else 6
        seeds = self.game.pits[offset + pit_local]
        if seeds == 0:
            return False
        # Both players: store is 6 positions past pit 0, 5 past pit 1, etc.
        return seeds == 6 - pit_local

    def _choose_pit(self):
        """Choose best pit index (0-5) using simple heuristics."""
        player = self.game.current_player
        offset = 0 if player == PLAYER_1 else 6
        valid = [i for i in range(6) if self.game.pits[offset + i] > 0]
        if not valid:
            return 0

        # Priority 1: free turn (lands in own store)
        for i in valid:
            if self._lands_in_store(i):
                return i

        # Priority 2: capture (land in empty own pit, opposite has seeds)
        for i in valid:
            pit_index = offset + i
            seeds = self.game.pits[pit_index]
            pos = i if player == PLAYER_1 else pit_index + 1
            remaining = seeds
            while remaining > 0:
                pos = (pos + 1) % 14
                skip = 13 if player == PLAYER_1 else 6
                if pos == skip:
                    continue
                remaining -= 1
            if player == PLAYER_1 and 0 <= pos <= 5:
                if self.game.pits[pos] == 0 and self.game.pits[11 - pos] > 0:
                    return i
            elif player == PLAYER_2 and 7 <= pos <= 12:
                arr = pos - 1
                if self.game.pits[arr] == 0 and self.game.pits[11 - arr] > 0:
                    return i

        # Priority 3: pit with the most seeds
        return max(valid, key=lambda i: self.game.pits[offset + i])

    def update(self, dt):
        self.time += dt

        if self.game.state == GameState.GAME_OVER:
            self.game_over_timer += dt
            if self.game_over_timer > 3.0:
                self.game.reset()
                self.game_over_timer = 0.0
                self.ai_state = "thinking"
                self.target_pit = None
            return

        # Build AI input, then always call game.update exactly once
        ai_input = InputState()

        if self.ai_state == "thinking":
            self.think_timer += dt
            if self.think_timer >= self.think_delay:
                self.target_pit = self._choose_pit()
                self.ai_state = "navigating"
                self.nav_timer = 0.0

        elif self.ai_state == "navigating":
            if self.game.input_cooldown <= 0:
                if self.game.selected_pit == self.target_pit:
                    ai_input.action_l = True
                    self.ai_state = "thinking"
                    self.think_timer = 0.0
                    self.think_delay = random.uniform(0.3, 0.8)
                    self.target_pit = None
                else:
                    self.nav_timer += dt
                    if self.nav_timer >= 0.1:
                        self.nav_timer = 0.0
                        diff = (self.target_pit - self.game.selected_pit) % 6
                        if diff <= 3:
                            ai_input.right = True
                        else:
                            ai_input.left = True

        self.game.update(ai_input, dt)

    def draw(self):
        if self.game.state == GameState.GAME_OVER:
            self.game.draw_game_over()
        else:
            self.game.draw()
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)
