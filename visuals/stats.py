"""
Stats - Play Statistics Display
================================
Scrolling display of play history and high score statistics.

Controls:
  Up/Down  - Slow down / speed up scroll
  Button   - Exit to menu
"""

import json
from collections import Counter
from . import Visual, Display, Colors, GRID_SIZE


class Stats(Visual):
    name = "STATS"
    description = "Play statistics"
    category = "utility"

    def __init__(self, display: Display):
        super().__init__(display)

    def _load_data(self):
        """Load play history and high scores from data dir."""
        from highscores import get_high_score_manager
        mgr = get_high_score_manager()
        data_dir = mgr.filepath.parent

        # Load play history
        plays = []
        history_path = data_dir / "play_history.jsonl"
        if history_path.exists():
            try:
                with open(history_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                plays.append(json.loads(line))
                            except json.JSONDecodeError:
                                pass
            except IOError:
                pass

        # High scores already loaded via manager
        scores = mgr.scores
        return plays, scores

    def reset(self):
        self.time = 0.0
        self.scroll_y = 0.0
        self.base_speed = 12.0
        self.scroll_speed = 12.0
        self.speed_mult = 1.0

        plays, scores = self._load_data()

        C = Colors.CYAN
        W = Colors.WHITE
        G = Colors.GRAY
        Y = Colors.YELLOW
        M = Colors.MAGENTA
        GR = Colors.GREEN

        self.lines = [
            ("ARCADE STATS", C),
            ("", G),
        ]

        # --- Overview ---
        total_plays = len(plays)
        game_counts = Counter(p.get("game", "?") for p in plays)
        unique_games = len(game_counts)

        self.lines.append(("- OVERVIEW -", M))
        self.lines.append(("", G))
        self.lines.append((f"TOTAL PLAYS {total_plays}", W))
        self.lines.append((f"UNIQUE GAMES {unique_games}", W))
        self.lines.append(("", G))

        # --- Most Played ---
        if game_counts:
            self.lines.append(("- MOST PLAYED -", M))
            self.lines.append(("", G))
            for game, count in game_counts.most_common(8):
                self.lines.append((game, C))
                self.lines.append((f"  {count} PLAYS", G))
            self.lines.append(("", G))

        # --- High Scores ---
        if scores:
            # Sort games by their #1 score descending
            ranked = sorted(scores.items(),
                            key=lambda kv: kv[1][0][1] if kv[1] else 0,
                            reverse=True)
            self.lines.append(("- HIGH SCORES -", M))
            self.lines.append(("", G))
            for game, entries in ranked[:6]:
                self.lines.append((game, C))
                for initials, score, *_ in entries[:3]:
                    self.lines.append((f" {initials} {score}", Y))
                self.lines.append(("", G))

        # --- Leaderboard ---
        # Count how many leaderboard entries each player has
        player_counts = Counter()
        for entries in scores.values():
            for initials, _score, *_ in entries:
                player_counts[initials] += 1
        if player_counts:
            self.lines.append(("- LEADERBOARD -", M))
            self.lines.append(("", G))
            for initials, count in player_counts.most_common(8):
                self.lines.append((f"{initials}  {count} ENTRIES", W))
            self.lines.append(("", G))

        self.lines.append(("", G))
        self.lines.append(("", G))

        self.line_height = 8
        self.total_height = len(self.lines) * self.line_height

    def handle_input(self, input_state) -> bool:
        if input_state.action_l or input_state.action_r:
            self.wants_exit = True
            return True
        if input_state.down:
            self.speed_mult = 4.0
            return True
        elif input_state.up:
            self.speed_mult = -1.5
            return True
        else:
            self.speed_mult = 1.0
        return False

    def update(self, dt: float):
        self.time += dt
        self.scroll_speed = self.base_speed * self.speed_mult
        self.scroll_y += self.scroll_speed * dt

        if self.scroll_y < 0.0:
            self.scroll_y = 0.0

        if self.scroll_y > self.total_height + GRID_SIZE:
            self.scroll_y = 0.0

    def draw(self):
        self.display.clear(Colors.BLACK)

        for i, (text, color) in enumerate(self.lines):
            if not text:
                continue
            y = int(GRID_SIZE - self.scroll_y + i * self.line_height)
            if -8 < y < GRID_SIZE:
                self.display.draw_text_small(2, y, text, color)
