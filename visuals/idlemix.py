"""
Idle Mix - Configure idle playlist weights and per-visual favorites/blacklist
=============================================================================
Two-page utility:
  Page 1: Category weight editor (0-5 per category)
  Page 2: Per-visual browser (normal / favorite / blacklisted)

Controls:
  Page 1:
    Up/Down    - Navigate categories
    Left/Right - Adjust weight (0=off, 1-5)
    Button     - Enter visual browser for selected category
  Page 2:
    Up/Down    - Navigate visuals
    Button     - Cycle state: normal -> favorite -> blacklisted -> normal
    Left       - Back to Page 1
"""

from . import Visual, Display, Colors, GRID_SIZE
from visuals.slideshow import Slideshow, AllVisuals

# Row layout constants
ROW_HEIGHT = 7       # 5px text + 2px gap
TITLE_Y = 2
SEP1_Y = 9
CONTENT_Y = 12
SEP2_Y = 55
FOOTER_Y = 58
VISIBLE_ROWS = 6     # (SEP2_Y - CONTENT_Y) // ROW_HEIGHT

# Category display info: key -> (display_name, color)
# Built from catalog but we define colors here to avoid import cycles at class level
_CAT_INFO = {
    'art':         ('ART',       (224, 165, 45)),
    'automata':    ('AUTOMATA',  (65, 217, 200)),
    'cooking':     ('COOKING',   (217, 65, 136)),
    'culture':     ('CULTURE',   (65, 217, 85)),
    'demos':       ('DEMOS',     (217, 191, 65)),
    'digital':     ('DIGITAL',   (56, 208, 224)),
    'gallery':     ('GALLERY',   (204, 194, 163)),
    'household':   ('HOUSEHOLD', (217, 65, 106)),
    'math':        ('MATH',      (56, 107, 224)),
    'mechanics':   ('MECHANICS', (166, 65, 217)),
    'music':       ('MUSIC',     (65, 75, 217)),
    'nature':      ('OUTDOORS',  (56, 224, 73)),
    'road_rail':   ('ROAD+RAIL', (197, 65, 217)),
    'science':     ('SCIENCE',   (75, 45, 224)),
    'sprites':     ('SPRITES',   (160, 217, 65)),
    'superheroes': ('HEROES',    (230, 52, 35)),
    'titles':      ('TITLES',    (217, 217, 65)),
}

# Default weights from AllVisuals.CATEGORY_WEIGHTS
_DEFAULT_WEIGHTS = dict(AllVisuals.CATEGORY_WEIGHTS)


def _dim(color, factor=0.3):
    return tuple(max(0, min(255, int(c * factor))) for c in color)


class IdleMix(Visual):
    name = "IDLE MIX"
    description = "Configure idle playlist"
    category = "utility"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.page = 1  # 1 = categories, 2 = visual browser
        self.cat_cursor = 0
        self.cat_scroll = 0
        self.vis_cursor = 0
        self.vis_scroll = 0
        self.exit_hold = 0.0
        self._both_pressed_prev = False

        # Load settings
        import settings as persistent
        self._user_weights = dict(persistent.get_idle_category_weights())
        self._favorites = set(persistent.get_idle_favorites())
        self._blacklist = set(persistent.get_idle_blacklist())

        # Build category list from ALL_VISUALS
        self._build_category_list()

    def _build_category_list(self):
        """Build ordered list of categories that have visuals."""
        from visuals import ALL_VISUALS
        # Collect visuals per category
        cat_visuals = {}
        for v in ALL_VISUALS:
            if issubclass(v, Slideshow):
                continue
            cat = getattr(v, 'category', '')
            if cat in ('utility', 'visual_mix'):
                continue
            if cat not in cat_visuals:
                cat_visuals[cat] = []
            cat_visuals[cat].append(v)

        # Sort visuals within each category alphabetically
        for cat in cat_visuals:
            cat_visuals[cat].sort(key=lambda v: v.name.upper())

        # Build ordered category list (keep _CAT_INFO order)
        self._categories = []
        for key in _CAT_INFO:
            if key in cat_visuals:
                name, color = _CAT_INFO[key]
                weight = self._user_weights.get(key, _DEFAULT_WEIGHTS.get(key, 2))
                self._categories.append({
                    'key': key,
                    'name': name,
                    'color': color,
                    'weight': weight,
                    'visuals': cat_visuals[key],
                })

        # Add any categories not in _CAT_INFO
        for key in cat_visuals:
            if key not in _CAT_INFO:
                weight = self._user_weights.get(key, _DEFAULT_WEIGHTS.get(key, 2))
                self._categories.append({
                    'key': key,
                    'name': key.upper()[:8],
                    'color': Colors.WHITE,
                    'weight': weight,
                    'visuals': cat_visuals[key],
                })

    def _save_weights(self):
        import settings as persistent
        # Only save non-default weights
        d = {}
        for cat in self._categories:
            key = cat['key']
            default = _DEFAULT_WEIGHTS.get(key, 2)
            if cat['weight'] != default:
                d[key] = cat['weight']
        persistent.set_idle_category_weights(d)

    def _save_favorites(self):
        import settings as persistent
        persistent.set_idle_favorites(list(self._favorites))

    def _save_blacklist(self):
        import settings as persistent
        persistent.set_idle_blacklist(list(self._blacklist))

    def _vis_state(self, cls_name):
        """Return 'favorite', 'blacklisted', or 'normal'."""
        if cls_name in self._favorites:
            return 'favorite'
        if cls_name in self._blacklist:
            return 'blacklisted'
        return 'normal'

    def _cycle_vis_state(self, cls_name):
        """Cycle: normal -> favorite -> blacklisted -> normal."""
        state = self._vis_state(cls_name)
        if state == 'normal':
            self._favorites.add(cls_name)
            self._save_favorites()
        elif state == 'favorite':
            self._favorites.discard(cls_name)
            self._blacklist.add(cls_name)
            self._save_favorites()
            self._save_blacklist()
        else:  # blacklisted
            self._blacklist.discard(cls_name)
            self._save_blacklist()

    def handle_input(self, input_state) -> bool:
        both_held = input_state.action_l_held and input_state.action_r_held
        both_now = input_state.action_l or input_state.action_r

        # Both-button hold: accumulate in update(), suppress single-press
        if both_held:
            self._both_pressed_prev = True
            return True

        # If both were held last frame, swallow the release
        if self._both_pressed_prev:
            if not both_now:
                self._both_pressed_prev = False
            self.exit_hold = 0.0
            return True

        self.exit_hold = 0.0

        if self.page == 1:
            return self._handle_page1(input_state)
        else:
            return self._handle_page2(input_state)

    def _handle_page1(self, input_state):
        n = len(self._categories)
        if n == 0:
            return False

        if input_state.up_pressed:
            self.cat_cursor = (self.cat_cursor - 1) % n
            self._clamp_scroll('cat')
            return True
        if input_state.down_pressed:
            self.cat_cursor = (self.cat_cursor + 1) % n
            self._clamp_scroll('cat')
            return True

        if input_state.left_pressed:
            cat = self._categories[self.cat_cursor]
            cat['weight'] = max(0, cat['weight'] - 1)
            self._save_weights()
            return True
        if input_state.right_pressed:
            cat = self._categories[self.cat_cursor]
            cat['weight'] = min(5, cat['weight'] + 1)
            self._save_weights()
            return True

        if input_state.action_l or input_state.action_r:
            # Enter visual browser for selected category
            self.page = 2
            self.vis_cursor = 0
            self.vis_scroll = 0
            return True

        return False

    def _handle_page2(self, input_state):
        cat = self._categories[self.cat_cursor]
        visuals = cat['visuals']
        n = len(visuals)

        if input_state.left_pressed:
            self.page = 1
            return True

        if n == 0:
            return False

        if input_state.up_pressed:
            self.vis_cursor = (self.vis_cursor - 1) % n
            self._clamp_scroll('vis')
            return True
        if input_state.down_pressed:
            self.vis_cursor = (self.vis_cursor + 1) % n
            self._clamp_scroll('vis')
            return True

        if input_state.action_l or input_state.action_r:
            cls_name = visuals[self.vis_cursor].__name__
            self._cycle_vis_state(cls_name)
            return True

        return False

    def _clamp_scroll(self, which):
        if which == 'cat':
            cursor, scroll = self.cat_cursor, self.cat_scroll
        else:
            cursor, scroll = self.vis_cursor, self.vis_scroll

        # Keep cursor visible with 1 row margin when possible
        if cursor < scroll:
            scroll = cursor
        elif cursor >= scroll + VISIBLE_ROWS:
            scroll = cursor - VISIBLE_ROWS + 1

        if which == 'cat':
            self.cat_scroll = scroll
        else:
            self.vis_scroll = scroll

    def update(self, dt: float):
        self.time += dt
        if self._both_pressed_prev:
            self.exit_hold += dt
            if self.exit_hold >= 2.0:
                self.wants_exit = True

    def draw(self):
        self.display.clear(Colors.BLACK)
        if self.page == 1:
            self._draw_page1()
        else:
            self._draw_page2()
        # Exit hold progress bar
        if self.exit_hold > 0:
            bar_w = min(60, int((self.exit_hold / 2.0) * 60))
            if bar_w > 0:
                self.display.draw_rect(2, 62, bar_w, 2, Colors.RED)

    def _draw_page1(self):
        d = self.display
        # Title
        d.draw_text_small(2, TITLE_Y, "IDLE MIX", Colors.CYAN)
        d.draw_line(0, SEP1_Y, 63, SEP1_Y, Colors.DARK_GRAY)

        n = len(self._categories)
        for i in range(VISIBLE_ROWS):
            idx = self.cat_scroll + i
            if idx >= n:
                break
            cat = self._categories[idx]
            y = CONTENT_Y + i * ROW_HEIGHT
            selected = (idx == self.cat_cursor)
            w = cat['weight']
            color = cat['color']

            # Dim everything if weight is 0
            if w == 0:
                color = _dim(color, 0.3)
                text_color = _dim(Colors.WHITE, 0.3)
            else:
                text_color = Colors.WHITE

            # Selection indicator
            if selected:
                d.draw_rect(0, y - 1, 64, ROW_HEIGHT, (30, 30, 50))

            # Cursor arrow
            arrow_color = Colors.WHITE if selected else Colors.BLACK
            d.set_pixel(1, y + 1, arrow_color)
            if selected:
                d.set_pixel(2, y + 2, arrow_color)
                d.set_pixel(1, y + 3, arrow_color)

            # Category name (truncated to 8 chars)
            name = cat['name'][:8]
            d.draw_text_small(5, y, name, color)

            # Weight bar at right side: 5 segments starting at x=47
            bar_x = 47
            for s in range(5):
                px = bar_x + s * 3
                if s < w:
                    d.draw_rect(px, y + 1, 2, 3, color)
                else:
                    d.set_pixel(px, y + 2, (40, 40, 40))

            # Weight number
            d.draw_text_small(62 - 3, y, str(w), text_color)

        # Footer
        d.draw_line(0, SEP2_Y, 63, SEP2_Y, Colors.DARK_GRAY)
        d.draw_text_small(2, FOOTER_Y, "LR:WT BTN:", Colors.GRAY)
        # Small arrow to indicate "enter"
        d.set_pixel(52, FOOTER_Y + 2, Colors.GRAY)
        d.set_pixel(53, FOOTER_Y + 3, Colors.GRAY)
        d.set_pixel(52, FOOTER_Y + 4, Colors.GRAY)

        # Scroll indicators
        if self.cat_scroll > 0:
            d.set_pixel(62, CONTENT_Y, Colors.GRAY)
            d.set_pixel(61, CONTENT_Y + 1, Colors.GRAY)
            d.set_pixel(63, CONTENT_Y + 1, Colors.GRAY)
        if self.cat_scroll + VISIBLE_ROWS < n:
            by = SEP2_Y - 3
            d.set_pixel(62, by + 2, Colors.GRAY)
            d.set_pixel(61, by + 1, Colors.GRAY)
            d.set_pixel(63, by + 1, Colors.GRAY)

    def _draw_page2(self):
        d = self.display
        cat = self._categories[self.cat_cursor]
        visuals = cat['visuals']
        n = len(visuals)

        # Title: back arrow + category name
        # Small left arrow
        d.set_pixel(2, TITLE_Y + 2, Colors.WHITE)
        d.set_pixel(3, TITLE_Y + 1, Colors.WHITE)
        d.set_pixel(3, TITLE_Y + 3, Colors.WHITE)
        d.draw_text_small(6, TITLE_Y, cat['name'][:10], cat['color'])
        d.draw_line(0, SEP1_Y, 63, SEP1_Y, Colors.DARK_GRAY)

        for i in range(VISIBLE_ROWS):
            idx = self.vis_scroll + i
            if idx >= n:
                break
            vis_cls = visuals[idx]
            cls_name = vis_cls.__name__
            state = self._vis_state(cls_name)
            y = CONTENT_Y + i * ROW_HEIGHT
            selected = (idx == self.vis_cursor)

            # Row background
            if selected:
                d.draw_rect(0, y - 1, 64, ROW_HEIGHT, (30, 30, 50))

            # Cursor arrow
            if selected:
                d.set_pixel(1, y + 1, Colors.WHITE)
                d.set_pixel(2, y + 2, Colors.WHITE)
                d.set_pixel(1, y + 3, Colors.WHITE)

            # Visual name (truncated to fit)
            vis_name = vis_cls.name[:9]
            if state == 'favorite':
                name_color = (80, 220, 80)
            elif state == 'blacklisted':
                name_color = (120, 40, 40)
            else:
                name_color = Colors.WHITE
            d.draw_text_small(5, y, vis_name, name_color)

            # State indicator at right edge
            ix = 59
            if state == 'favorite':
                # Green filled block
                d.draw_rect(ix, y + 1, 3, 3, (80, 220, 80))
            elif state == 'blacklisted':
                # Red X
                rc = (180, 50, 50)
                d.set_pixel(ix, y + 1, rc)
                d.set_pixel(ix + 2, y + 1, rc)
                d.set_pixel(ix + 1, y + 2, rc)
                d.set_pixel(ix, y + 3, rc)
                d.set_pixel(ix + 2, y + 3, rc)
            else:
                # White dot
                d.set_pixel(ix + 1, y + 2, (100, 100, 100))

        # Footer
        d.draw_line(0, SEP2_Y, 63, SEP2_Y, Colors.DARK_GRAY)
        d.draw_text_small(2, FOOTER_Y, "BTN:CYCLE", Colors.GRAY)
        # Left arrow + BACK
        d.set_pixel(50, FOOTER_Y + 2, Colors.GRAY)
        d.set_pixel(51, FOOTER_Y + 1, Colors.GRAY)
        d.set_pixel(51, FOOTER_Y + 3, Colors.GRAY)

        # Scroll indicators
        if self.vis_scroll > 0:
            d.set_pixel(62, CONTENT_Y, Colors.GRAY)
            d.set_pixel(61, CONTENT_Y + 1, Colors.GRAY)
            d.set_pixel(63, CONTENT_Y + 1, Colors.GRAY)
        if self.vis_scroll + VISIBLE_ROWS < n:
            by = SEP2_Y - 3
            d.set_pixel(62, by + 2, Colors.GRAY)
            d.set_pixel(61, by + 1, Colors.GRAY)
            d.set_pixel(63, by + 1, Colors.GRAY)
