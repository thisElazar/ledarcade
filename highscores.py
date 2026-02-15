"""
High Score Manager
==================
Handles persistent high score storage with JSON file backend.
Supports per-game leaderboards with player initials.
"""

import json
import os
import time
from typing import List, Tuple, Optional
from pathlib import Path


class HighScoreManager:
    """Manages high scores for all games with JSON persistence."""

    MAX_SCORES_PER_GAME = 5  # Top 5 leaderboard

    # Games renamed in commit 7f69468 — map old keys to new keys
    _RENAME_MAP = {
        "STICKRUN": "STICK RUN",
        "FLAPPY": "FLAPPY BIRD",
        "SPACECRUISE": "SPACE CRUISE",
        "CONNECT4": "CONNECT 4",
        "DONKEY K": "DONKEY KONG",
    }

    def __init__(self, filepath: Optional[str] = None):
        """Initialize the high score manager.

        Args:
            filepath: Path to the JSON file. Defaults to ~/.led-arcade/highscores.json
        """
        if filepath is None:
            # Default to user's home directory
            data_dir = Path(__file__).resolve().parent / "data"
            data_dir.mkdir(exist_ok=True)
            self.filepath = data_dir / "highscores.json"
        else:
            self.filepath = Path(filepath)

        self.scores = {}  # {game_name: [(initials, score, timestamp), ...]}
        self.load_scores()
        self._migrate_renamed_games()

    def load_scores(self):
        """Load scores from JSON file."""
        if self.filepath.exists():
            try:
                with open(self.filepath, 'r') as f:
                    data = json.load(f)
                    # Convert lists back to list of tuples
                    # Backward-compatible: old 2-element entries get timestamp 0
                    self.scores = {
                        game: [
                            (entry[0], entry[1], entry[2] if len(entry) > 2 else 0)
                            for entry in entries
                        ]
                        for game, entries in data.items()
                    }
            except (json.JSONDecodeError, KeyError, IndexError):
                # Corrupted file, start fresh
                self.scores = {}
        else:
            self.scores = {}

    def save_scores(self):
        """Save scores to JSON file."""
        try:
            with open(self.filepath, 'w') as f:
                json.dump(self.scores, f, indent=2)
        except IOError:
            # Can't save, fail silently (scores still work in memory)
            pass

    def _migrate_renamed_games(self):
        """Migrate scores from old game names to new names (one-time on init)."""
        changed = False
        for old_key, new_key in self._RENAME_MAP.items():
            if old_key not in self.scores:
                continue
            if new_key not in self.scores:
                # Simple rename
                self.scores[new_key] = self.scores.pop(old_key)
            else:
                # Merge old into new, keep top 5
                merged = self.scores[new_key] + self.scores.pop(old_key)
                merged.sort(key=lambda x: x[1], reverse=True)
                self.scores[new_key] = merged[:self.MAX_SCORES_PER_GAME]
            changed = True
        if changed:
            self.save_scores()

    def get_top_scores(self, game_name: str) -> List[Tuple[str, int]]:
        """Get the top scores for a game.

        Args:
            game_name: The game's name attribute

        Returns:
            List of (initials, score) tuples, sorted by score descending
        """
        return self.scores.get(game_name, [])

    def is_high_score(self, game_name: str, score: int) -> bool:
        """Check if a score qualifies for the leaderboard.

        Args:
            game_name: The game's name attribute
            score: The player's score

        Returns:
            True if the score would make the leaderboard
        """
        if score <= 0:
            return False

        current_scores = self.scores.get(game_name, [])

        # If leaderboard isn't full, any positive score qualifies
        if len(current_scores) < self.MAX_SCORES_PER_GAME:
            return True

        # Otherwise, must beat the lowest score
        lowest = min(entry[1] for entry in current_scores)
        return score > lowest

    def add_score(self, game_name: str, initials: str, score: int) -> int:
        """Add a score to the leaderboard.

        Args:
            game_name: The game's name attribute
            initials: Player's 3-letter initials
            score: The player's score

        Returns:
            The rank (1-3) of the new score, or -1 if it didn't make the board
        """
        if score <= 0:
            return -1

        # Ensure initials are valid
        initials = initials.upper()[:3].ljust(3, 'A')

        if game_name not in self.scores:
            self.scores[game_name] = []

        # Add the new score with timestamp
        self.scores[game_name].append((initials, score, int(time.time())))

        # Sort by score descending
        self.scores[game_name].sort(key=lambda x: x[1], reverse=True)

        # Trim to max size
        self.scores[game_name] = self.scores[game_name][:self.MAX_SCORES_PER_GAME]

        # Find the rank of the new score
        for i, (init, sc, _ts) in enumerate(self.scores[game_name]):
            if init == initials and sc == score:
                self.save_scores()
                return i + 1  # 1-indexed rank

        # Score didn't make it (was trimmed)
        return -1

    def get_rank(self, game_name: str, score: int) -> int:
        """Get what rank a score would be without adding it.

        Args:
            game_name: The game's name attribute
            score: The score to check

        Returns:
            The rank (1-3) it would be, or -1 if it wouldn't make the board
        """
        if score <= 0:
            return -1

        current_scores = self.scores.get(game_name, [])

        # Count how many scores are higher
        rank = 1
        for _, existing_score, *_ in current_scores:
            if existing_score > score:
                rank += 1

        if rank <= self.MAX_SCORES_PER_GAME:
            return rank

        # Check if board isn't full
        if len(current_scores) < self.MAX_SCORES_PER_GAME:
            return len(current_scores) + 1

        return -1

    def log_play(self, game_name: str, score: int, initials: str = ""):
        """Log a game play to the play history file (JSONL, one line per play)."""
        try:
            history_path = self.filepath.parent / "play_history.jsonl"
            entry = json.dumps({
                "game": game_name,
                "score": score,
                "initials": initials,
                "ts": int(time.time()),
            })
            with open(history_path, 'a') as f:
                f.write(entry + "\n")
        except IOError:
            pass


# Global instance for easy access
_manager: Optional[HighScoreManager] = None


def get_high_score_manager() -> HighScoreManager:
    """Get the global high score manager instance."""
    global _manager
    if _manager is None:
        _manager = HighScoreManager()
    return _manager
