"""
Stats - Play Statistics Display
================================
Scrolling display of play history and high score statistics.

Controls:
  Left/Right - Switch pages (ALL, Overview, Most Played, High Scores, Leaderboard)
  Up/Down    - Scroll content (speed control on ALL page, directional on sections)
  Button     - Exit to menu
"""

import json
from collections import Counter
from . import Visual, Display, Colors, GRID_SIZE


class Stats(Visual):
    name = "STATS"
    description = "Play statistics"
    category = "utility"

    HEADER_H = 8
    SEP_Y = 7
    CONTENT_TOP = 8
    FOOTER_H = 4
    CONTENT_BOT = GRID_SIZE - FOOTER_H  # 60
    SCROLL_SPEED = 60.0

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
        # Page 0 (ALL) scroll state
        self.scroll_y = 0.0
        self.base_speed = 12.0
        self.scroll_speed = 12.0
        self.speed_mult = 1.0
        # Section page state
        self.page = 0
        self._section_scroll_y = 0.0
        self._scroll_dir = 0

        plays, scores = self._load_data()

        C = Colors.CYAN
        W = Colors.WHITE
        G = Colors.GRAY
        Y = Colors.YELLOW
        M = Colors.MAGENTA

        # === Build flat lines list (ALL page, unchanged) ===
        self.lines = [
            ("ARCADE STATS", C),
            ("", G),
        ]

        total_plays = len(plays)
        game_counts = Counter(p.get("game", "?") for p in plays)
        unique_games = len(game_counts)

        self.lines.append(("- OVERVIEW -", M))
        self.lines.append(("", G))
        self.lines.append((f"TOTAL PLAYS {total_plays}", W))
        self.lines.append((f"UNIQUE GAMES {unique_games}", W))
        self.lines.append(("", G))

        if game_counts:
            self.lines.append(("- MOST PLAYED -", M))
            self.lines.append(("", G))
            for game, count in game_counts.most_common():
                self.lines.append((game, C))
                self.lines.append((f"  {count} PLAYS", G))
            self.lines.append(("", G))

        if scores:
            ranked = sorted(scores.items(), key=lambda kv: kv[0])
            self.lines.append(("- HIGH SCORES -", M))
            self.lines.append(("", G))
            for game, entries in ranked:
                self.lines.append((game, C))
                for initials, score, *_ in entries:
                    self.lines.append((f" {initials} {score}", Y))
                self.lines.append(("", G))

        player_counts = Counter()
        for entries in scores.values():
            for initials, _score, *_ in entries:
                player_counts[initials] += 1
        if player_counts:
            self.lines.append(("- LEADERBOARD -", M))
            self.lines.append(("", G))
            for initials, count in player_counts.most_common():
                self.lines.append((f"{initials}  {count} ENTRIES", W))
            self.lines.append(("", G))

        self.lines.append(("", G))
        self.lines.append(("", G))

        self.line_height = 8
        self.total_height = len(self.lines) * self.line_height

        # === Build section pages ===
        self.sections = []

        # Section 1: OVERVIEW
        sec_lines = [
            (f"TOTAL PLAYS {total_plays}", W),
            ("", G),
            (f"UNIQUE GAMES {unique_games}", W),
        ]
        self.sections.append({'title': 'OVERVIEW', 'lines': sec_lines})

        # Section 2: MOST PLAYED
        sec_lines = []
        if game_counts:
            for game, count in game_counts.most_common():
                sec_lines.append((game, C))
                sec_lines.append((f"  {count} PLAYS", G))
                sec_lines.append(("", G))
        else:
            sec_lines.append(("NO DATA", G))
        self.sections.append({'title': 'MOST PLAYED', 'lines': sec_lines})

        # Section 3: HIGH SCORES
        sec_lines = []
        if scores:
            ranked = sorted(scores.items(), key=lambda kv: kv[0])
            for game, entries in ranked:
                sec_lines.append((game, C))
                for initials, score, *_ in entries:
                    sec_lines.append((f" {initials} {score}", Y))
                sec_lines.append(("", G))
        else:
            sec_lines.append(("NO DATA", G))
        self.sections.append({'title': 'HIGH SCORES', 'lines': sec_lines})

        # Section 4: LEADERBOARD
        sec_lines = []
        if player_counts:
            for initials, count in player_counts.most_common():
                sec_lines.append((f"{initials}  {count} ENTRIES", W))
                sec_lines.append(("", G))
        else:
            sec_lines.append(("NO DATA", G))
        self.sections.append({'title': 'LEADERBOARD', 'lines': sec_lines})

        self.num_pages = 1 + len(self.sections)  # page 0 = ALL

    def handle_input(self, input_state) -> bool:
        if input_state.action_l or input_state.action_r:
            self.wants_exit = True
            return True

        # Left/Right: switch pages
        if input_state.left_pressed:
            self.page = (self.page - 1) % self.num_pages
            self._section_scroll_y = 0.0
            self._scroll_dir = 0
            return True
        if input_state.right_pressed:
            self.page = (self.page + 1) % self.num_pages
            self._section_scroll_y = 0.0
            self._scroll_dir = 0
            return True

        # Up/Down behavior depends on page
        if self.page == 0:
            # ALL page: speed control (existing behavior)
            if input_state.down:
                self.speed_mult = 4.0
                return True
            elif input_state.up:
                self.speed_mult = -1.5
                return True
            else:
                self.speed_mult = 1.0
        else:
            # Section pages: directional scroll
            if input_state.up:
                self._scroll_dir = -1
                return True
            elif input_state.down:
                self._scroll_dir = 1
                return True
            else:
                self._scroll_dir = 0

        return False

    def update(self, dt: float):
        self.time += dt

        if self.page == 0:
            # ALL page: existing auto-scroll
            self.scroll_speed = self.base_speed * self.speed_mult
            self.scroll_y += self.scroll_speed * dt
            if self.scroll_y < 0.0:
                self.scroll_y = 0.0
            if self.scroll_y > self.total_height + GRID_SIZE:
                self.scroll_y = 0.0
        else:
            # Section pages: manual scroll
            if self._scroll_dir != 0:
                section = self.sections[self.page - 1]
                content_h = len(section['lines']) * self.line_height
                view_h = self.CONTENT_BOT - self.CONTENT_TOP
                max_scroll = max(0.0, content_h - view_h)

                self._section_scroll_y += self._scroll_dir * self.SCROLL_SPEED * dt
                self._section_scroll_y = max(0.0, min(max_scroll, self._section_scroll_y))

    def draw(self):
        self.display.clear(Colors.BLACK)

        if self.page == 0:
            self._draw_all_page()
        else:
            self._draw_section_page()

        self._draw_footer_dots()

    def _draw_all_page(self):
        """Draw the full auto-scrolling ALL page."""
        for i, (text, color) in enumerate(self.lines):
            if not text:
                continue
            y = int(GRID_SIZE - self.scroll_y + i * self.line_height)
            if -8 < y < GRID_SIZE - self.FOOTER_H:
                self.display.draw_text_small(2, y, text, color)

    def _draw_section_page(self):
        """Draw a section page with header, content, and navigation arrows."""
        section = self.sections[self.page - 1]
        d = self.display

        # Header: title centered
        title = section['title']
        # draw_text_small uses 4px wide chars + 1px gap = 5px per char
        tw = len(title) * 5 - 1
        tx = max(0, (GRID_SIZE - tw) // 2)
        d.draw_text_small(tx, 0, title, Colors.WHITE)

        # Navigation arrows
        dim = (80, 80, 80)
        if self.num_pages > 1:
            d.draw_text_small(0, 0, "<", dim)
            arrow_x = GRID_SIZE - 4
            d.draw_text_small(arrow_x, 0, ">", dim)

        # Separator line at y=7
        for x in range(GRID_SIZE):
            d.set_pixel(x, self.SEP_Y, (40, 40, 40))

        # Content area (clipped to CONTENT_TOP..CONTENT_BOT)
        for i, (text, color) in enumerate(section['lines']):
            if not text:
                continue
            y = self.CONTENT_TOP + i * self.line_height - int(self._section_scroll_y)
            if self.CONTENT_TOP - 8 < y < self.CONTENT_BOT:
                d.draw_text_small(2, y, text, color)

    def _draw_footer_dots(self):
        """Draw page indicator dots at the bottom."""
        d = self.display
        dot_y = GRID_SIZE - 2  # y=62
        dot_spacing = 4
        total_w = self.num_pages * dot_spacing - 2  # each dot 2px wide, gaps of 2px
        start_x = (GRID_SIZE - total_w) // 2

        for i in range(self.num_pages):
            x = start_x + i * dot_spacing
            color = Colors.WHITE if i == self.page else (50, 50, 50)
            d.set_pixel(x, dot_y, color)
            d.set_pixel(x + 1, dot_y, color)
