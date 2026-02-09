"""
Mancala Demo - AI vs AI Attract Mode
=====================================
Two AIs play Mancala using minimax with alpha-beta pruning at depth 8.
Handles free turns, captures, and store difference evaluation.
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState
import random
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.mancala import Mancala, PLAYER_1, PLAYER_2


class MancalaAI:
    """Minimax AI with alpha-beta pruning for Mancala."""

    DEPTH = 8

    def _save_state(self, game):
        """Save game state as a tuple for restore after search."""
        return (
            list(game.pits),
            game.store1,
            game.store2,
            game.current_player,
            game.state,
            game.winner,
            game.selected_pit,
        )

    def _restore_state(self, game, state):
        """Restore game state from saved tuple."""
        game.pits = list(state[0])
        game.store1 = state[1]
        game.store2 = state[2]
        game.current_player = state[3]
        game.state = state[4]
        game.winner = state[5]
        game.selected_pit = state[6]

    def get_best_move(self, game, player):
        """Find the best pit (0-5) using minimax."""
        offset = 0 if player == PLAYER_1 else 6
        valid = [i for i in range(6) if game.pits[offset + i] > 0]
        if not valid:
            return 0

        best_pit = valid[0]
        best_score = float('-inf')

        for pit in valid:
            saved = self._save_state(game)
            pit_index = pit if player == PLAYER_1 else pit + 6
            game.sow_seeds(pit_index)

            # After sow_seeds, current_player may have changed (or not, if free turn)
            score = self._minimax(game, self.DEPTH - 1, float('-inf'), float('inf'),
                                  game.current_player == player, player)

            self._restore_state(game, saved)

            if score > best_score:
                best_score = score
                best_pit = pit

        return best_pit

    def _minimax(self, game, depth, alpha, beta, maximizing, root_player):
        """Minimax with alpha-beta. root_player is the AI we're optimizing for."""
        from arcade import GameState as GS
        if game.state == GS.GAME_OVER or depth == 0:
            return self._evaluate(game, root_player)

        current = game.current_player
        offset = 0 if current == PLAYER_1 else 6
        valid = [i for i in range(6) if game.pits[offset + i] > 0]
        if not valid:
            return self._evaluate(game, root_player)

        if maximizing:
            value = float('-inf')
            for pit in valid:
                saved = self._save_state(game)
                pit_index = pit if current == PLAYER_1 else pit + 6
                game.sow_seeds(pit_index)

                # If same player goes again (free turn), still maximizing
                is_max = game.current_player == root_player
                score = self._minimax(game, depth - 1, alpha, beta, is_max, root_player)

                self._restore_state(game, saved)
                value = max(value, score)
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        else:
            value = float('inf')
            for pit in valid:
                saved = self._save_state(game)
                pit_index = pit if current == PLAYER_1 else pit + 6
                game.sow_seeds(pit_index)

                is_max = game.current_player == root_player
                score = self._minimax(game, depth - 1, alpha, beta, is_max, root_player)

                self._restore_state(game, saved)
                value = min(value, score)
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value

    def _evaluate(self, game, player):
        """Evaluate position for player."""
        opponent = PLAYER_2 if player == PLAYER_1 else PLAYER_1

        if player == PLAYER_1:
            own_store = game.store1
            opp_store = game.store2
            own_pits = game.pits[0:6]
            opp_pits = game.pits[6:12]
        else:
            own_store = game.store2
            opp_store = game.store1
            own_pits = game.pits[6:12]
            opp_pits = game.pits[0:6]

        score = 0.0

        # Store difference (most important)
        score += (own_store - opp_store) * 10.0

        # Seeds on own side (potential)
        score += sum(own_pits) * 2.0
        score -= sum(opp_pits) * 1.0

        # Free turn setups: pits where seeds == distance to store
        for i in range(6):
            if own_pits[i] == 6 - i:
                score += 5.0

        # Capture setups: empty own pits with seeds in opposite
        for i in range(6):
            if own_pits[i] == 0 and opp_pits[5 - i] > 0:
                score += 2.0

        return score


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
        self.ai = MancalaAI()
        self.think_timer = 0.0
        self.think_delay = 0.0
        self.target_pit = None
        self.nav_timer = 0.0
        self.game_over_timer = 0.0
        self.ai_state = "thinking"

    def handle_input(self, input_state):
        return False

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
                self.target_pit = self.ai.get_best_move(self.game, self.game.current_player)
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
