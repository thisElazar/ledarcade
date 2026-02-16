#!/usr/bin/env python3
"""
LED Arcade - Unified Launcher
=============================
Combined games and visuals with category-based navigation.

Controls:
  Left/Right - Switch category (page)
  Up/Down    - Select item within category
  Space      - Launch selected item
  Hold both   - Back to menu (games) / Exit
"""

import pygame
import sys
import time
import math
import random
from enum import Enum, auto
from arcade import Display, InputHandler, Colors, GRID_SIZE, Game, GameState
from catalog import (
    register_games, register_visuals, get_all_categories,
    GAME_CATEGORIES, VISUAL_CATEGORIES
)
from highscores import get_high_score_manager

# Import all games and visuals
from games import ALL_GAMES
from visuals import ALL_VISUALS


# Game over sub-states
class GameOverState(Enum):
    FLASHING = auto()      # Alternating between score and leaderboard
    MILESTONE = auto()     # New #1 champion celebration
    ENTER_INITIALS = auto() # Player entering their initials
    CHOOSE_ACTION = auto()  # PLAY AGAIN / MENU selection


def center_x(text):
    """Calculate x position to center text (4px per char + 1px spacing)."""
    width = len(text) * 5 - 1
    return max(0, (GRID_SIZE - width) // 2)


def draw_game_over_score(display, score):
    """Draw the GAME OVER screen with player's score."""
    display.clear(Colors.BLACK)
    display.draw_text_small(center_x("GAME OVER"), 20, "GAME OVER", Colors.RED)
    score_text = f"SCORE:{score}"
    display.draw_text_small(center_x(score_text), 32, score_text, Colors.WHITE)


def draw_leaderboard(display, game_name, highlight_rank=-1):
    """Draw the high scores leaderboard.

    Args:
        display: The display to draw on
        game_name: Name of the game to show scores for
        highlight_rank: 1-3 to highlight that rank, -1 for no highlight
    """
    display.clear(Colors.BLACK)
    display.draw_text_small(center_x("HIGH SCORES"), 2, "HIGH SCORES", Colors.YELLOW)
    display.draw_line(0, 9, 63, 9, Colors.DARK_GRAY)

    hsm = get_high_score_manager()
    scores = hsm.get_top_scores(game_name)

    if not scores:
        display.draw_text_small(center_x("NO SCORES"), 28, "NO SCORES", Colors.GRAY)
        display.draw_text_small(center_x("YET!"), 38, "YET!", Colors.GRAY)
        return

    y = 14
    for i, (initials, score, _ts) in enumerate(scores):
        rank = i + 1
        # Highlight the player's new score
        if rank == highlight_rank:
            color = Colors.YELLOW
        else:
            color = Colors.WHITE

        # Format: "1 AAA 12345" - rank, initials, score
        display.draw_text_small(2, y, f"{rank}", color)
        display.draw_text_small(10, y, initials, color)
        # Right-align score
        score_str = str(score)
        score_x = 62 - len(score_str) * 4
        display.draw_text_small(score_x, y, score_str, color)
        y += 8


def draw_initials_entry(display, initials, cursor_pos, score):
    """Draw the initials entry screen.

    Args:
        display: The display to draw on
        initials: List of 3 characters
        cursor_pos: 0-2 indicating which letter is being edited
        score: The player's score to display
    """
    display.clear(Colors.BLACK)
    display.draw_text_small(center_x("HIGH SCORE!"), 2, "HIGH SCORE!", Colors.YELLOW)
    score_text = f"SCORE:{score}"
    display.draw_text_small(center_x(score_text), 12, score_text, Colors.WHITE)

    display.draw_line(0, 22, 63, 22, Colors.DARK_GRAY)
    display.draw_text_small(center_x("ENTER NAME:"), 26, "ENTER NAME:", Colors.GRAY)

    # Draw the three letter slots
    slot_x = 20
    for i, letter in enumerate(initials):
        x = slot_x + i * 10
        if i == cursor_pos:
            # Draw cursor indicators (up/down arrows)
            display.draw_text_small(x + 1, 34, "^", Colors.YELLOW)
            display.draw_text_small(x, 42, letter, Colors.CYAN)
            display.draw_text_small(x + 1, 50, "v", Colors.YELLOW)
        else:
            display.draw_text_small(x, 42, letter, Colors.WHITE)

    display.draw_line(0, 56, 63, 56, Colors.DARK_GRAY)
    display.draw_text_small(4, 58, "BTN:NEXT", Colors.GRAY)


def draw_action_selection(display, selection, score, made_leaderboard=False, rank=-1, first_option="PLAY AGAIN"):
    """Draw the PLAY AGAIN / MENU selection.

    Args:
        display: The display to draw on
        selection: 0 = first option, 1 = MENU
        score: The player's score
        made_leaderboard: Whether player made the leaderboard
        rank: Player's rank if they made leaderboard
        first_option: Text for the first option (default "PLAY AGAIN")
    """
    display.clear(Colors.BLACK)

    if made_leaderboard:
        rank_text = f"RANK {rank}!"
        display.draw_text_small(center_x(rank_text), 8, rank_text, Colors.CYAN)
        score_text = f"SCORE:{score}"
        display.draw_text_small(center_x(score_text), 18, score_text, Colors.WHITE)
    else:
        display.draw_text_small(center_x("GAME OVER"), 12, "GAME OVER", Colors.RED)
        score_text = f"SCORE:{score}"
        display.draw_text_small(center_x(score_text), 22, score_text, Colors.WHITE)

    # Draw selection options
    if selection == 0:
        display.draw_text_small(2, 40, f">{first_option}", Colors.YELLOW)
        display.draw_text_small(2, 50, " MENU", Colors.GRAY)
    else:
        display.draw_text_small(2, 40, f" {first_option}", Colors.GRAY)
        display.draw_text_small(2, 50, ">MENU", Colors.YELLOW)


def _text_width(text):
    """Width in pixels of text rendered with draw_text_small (4px per char)."""
    return len(text) * 4 - 1 if text else 0


def draw_menu(display, categories, cat_index, item_index, name_scroll_x=0):
    """Draw the category-based menu."""
    display.clear(Colors.BLACK)

    if not categories:
        display.draw_text_small(2, 30, "NO ITEMS", Colors.RED)
        return

    category = categories[cat_index]

    # Category name with navigation arrows
    cat_color = category.color
    display.draw_text_small(4, 2, category.name, cat_color)

    # Draw navigation arrows if multiple categories
    if len(categories) > 1:
        # Left arrow
        display.set_pixel(1, 4, Colors.GRAY)
        display.set_pixel(0, 5, Colors.GRAY)
        display.set_pixel(1, 6, Colors.GRAY)
        # Right arrow
        display.set_pixel(62, 4, Colors.GRAY)
        display.set_pixel(63, 5, Colors.GRAY)
        display.set_pixel(62, 6, Colors.GRAY)

    # Category indicator dots (scrolling window of 12 visible)
    n = len(categories)
    visible_dots = 12
    spacing = 4

    # Calculate window position (keep selected dot roughly centered)
    window_start = max(0, min(cat_index - visible_dots // 2, n - visible_dots))
    window_end = min(window_start + visible_dots, n)

    # Center the visible dots
    total_width = (window_end - window_start) * spacing
    dot_start_x = 32 - total_width // 2

    # Draw arrow hints if there are more categories beyond view
    if window_start > 0:
        display.set_pixel(2, 9, Colors.GRAY)
        display.set_pixel(3, 8, Colors.GRAY)
        display.set_pixel(3, 10, Colors.GRAY)
    if window_end < n:
        display.set_pixel(61, 9, Colors.GRAY)
        display.set_pixel(60, 8, Colors.GRAY)
        display.set_pixel(60, 10, Colors.GRAY)

    # Draw visible dots
    for i in range(window_start, window_end):
        x = dot_start_x + (i - window_start) * spacing
        color = Colors.WHITE if i == cat_index else Colors.DARK_GRAY
        display.set_pixel(x, 9, color)

    display.draw_line(0, 11, 63, 11, Colors.DARK_GRAY)

    # Item list
    items = category.items
    if not items:
        display.draw_text_small(8, 30, "EMPTY", Colors.GRAY)
        return

    visible = 5
    start_idx = max(0, item_index - visible // 2)
    if start_idx + visible > len(items):
        start_idx = max(0, len(items) - visible)

    # Selected item name: ">" prefix is 4px, then name starts at x=6
    # Available width for name: 64 - 6 = 58px
    NAME_X = 6
    MAX_NAME_W = 58  # pixels available for the name

    for i, item_class in enumerate(items[start_idx:start_idx + visible]):
        actual_idx = start_idx + i
        y = 14 + i * 8

        if actual_idx == item_index:
            display.draw_rect(0, y - 1, 64, 7, Colors.DARK_GRAY)
            display.draw_text_small(2, y, ">", cat_color)
            name_w = _text_width(item_class.name)
            if name_w > MAX_NAME_W:
                # Scroll: shift name left by name_scroll_x pixels
                display.draw_text_small(NAME_X - int(name_scroll_x), y, item_class.name, cat_color)
            else:
                display.draw_text_small(NAME_X, y, item_class.name, cat_color)
        else:
            display.draw_text_small(2, y, f" {item_class.name}", Colors.WHITE)

    # Scroll indicators
    if start_idx > 0:
        display.draw_text_small(58, 14, "^", Colors.GRAY)
    if start_idx + visible < len(items):
        display.draw_text_small(58, 14 + (visible - 1) * 8, "v", Colors.GRAY)

    # Instructions
    display.draw_line(0, 56, 63, 56, Colors.DARK_GRAY)
    display.draw_text_small(2, 58, "SPACE:GO", Colors.GRAY)
    display.draw_text_small(34, 58, "HOLD:EXIT", Colors.GRAY)


KONAMI_CODE = ['U', 'U', 'D', 'D', 'L', 'R', 'L', 'R', 'A', 'B']


def _hue_to_rgb(h):
    """Convert hue (0.0-1.0) to RGB tuple."""
    h = h % 1.0
    r = max(0.0, min(1.0, abs(h * 6.0 - 3.0) - 1.0))
    g = max(0.0, min(1.0, 2.0 - abs(h * 6.0 - 2.0)))
    b = max(0.0, min(1.0, 2.0 - abs(h * 6.0 - 4.0)))
    return (int(r * 255), int(g * 255), int(b * 255))


def draw_konami_egg(display, timer):
    """Draw the 30 LIVES easter egg."""
    display.clear(Colors.BLACK)

    # Brief white flash at start
    if timer < 0.15:
        display.clear(Colors.WHITE)
        return

    t = timer - 0.15
    hue = (t * 2.0) % 1.0
    color = _hue_to_rgb(hue)

    # Random sparkles
    for _ in range(25):
        sx = random.randint(0, GRID_SIZE - 1)
        sy = random.randint(0, GRID_SIZE - 1)
        display.set_pixel(sx, sy, _hue_to_rgb((hue + random.random() * 0.5) % 1.0))

    # "30" with glow effect
    cx = center_x("30")
    cy = 22
    for ox in [-1, 0, 1]:
        for oy in [-1, 0, 1]:
            if ox == 0 and oy == 0:
                continue
            glow = (color[0] // 4, color[1] // 4, color[2] // 4)
            display.draw_text_small(cx + ox, cy + oy, "30", glow)
    display.draw_text_small(cx, cy, "30", color)

    # "LIVES" below
    display.draw_text_small(center_x("LIVES"), 34, "LIVES", color)


def draw_milestone_celebration(display, timer):
    """Draw the NEW CHAMPION milestone celebration (1.5s)."""
    t = timer
    hue = (t * 1.5) % 1.0

    display.clear(Colors.BLACK)

    # Pulsing gold border
    pulse = 0.6 + 0.4 * math.sin(t * 10)
    gold = (int(255 * pulse), int(200 * pulse), 0)
    for i in range(GRID_SIZE):
        display.set_pixel(i, 0, gold)
        display.set_pixel(i, GRID_SIZE - 1, gold)
        display.set_pixel(0, i, gold)
        display.set_pixel(GRID_SIZE - 1, i, gold)

    # Sparkles
    for _ in range(15):
        sx = random.randint(1, GRID_SIZE - 2)
        sy = random.randint(1, GRID_SIZE - 2)
        display.set_pixel(sx, sy, _hue_to_rgb((hue + random.random() * 0.3) % 1.0))

    # "TOP SCORE" text with glow
    new_color = (255, 255, int(100 + 155 * pulse))
    cx = center_x("TOP SCORE")
    for ox in [-1, 0, 1]:
        for oy in [-1, 0, 1]:
            if ox == 0 and oy == 0:
                continue
            glow = (new_color[0] // 4, new_color[1] // 4, new_color[2] // 4)
            display.draw_text_small(cx + ox, 20 + oy, "TOP SCORE", glow)
    display.draw_text_small(cx, 20, "TOP SCORE", new_color)

    # "CHAMPION!" text
    champ_color = _hue_to_rgb(hue)
    cx2 = center_x("CHAMPION!")
    display.draw_text_small(cx2, 34, "CHAMPION!", champ_color)


def draw_spin_egg(display, timer):
    """Draw the TURBO! spin easter egg animation (2s)."""
    display.clear(Colors.BLACK)

    # Brief white flash at start
    if timer < 0.15:
        display.clear(Colors.WHITE)
        return

    t = timer - 0.15
    hue = (t * 3.0) % 1.0

    # Spinning ring of rainbow border pixels
    ring_count = 16
    cx, cy = GRID_SIZE // 2, GRID_SIZE // 2
    radius = 24
    for i in range(ring_count):
        angle = (i / ring_count) * 2 * math.pi + t * 8
        px = int(cx + radius * math.cos(angle))
        py = int(cy + radius * math.sin(angle))
        if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
            display.set_pixel(px, py, _hue_to_rgb((hue + i / ring_count) % 1.0))

    # Random sparkles
    for _ in range(20):
        sx = random.randint(0, GRID_SIZE - 1)
        sy = random.randint(0, GRID_SIZE - 1)
        display.set_pixel(sx, sy, _hue_to_rgb((hue + random.random() * 0.5) % 1.0))

    # "TURBO!" with glow effect
    color = _hue_to_rgb(hue)
    tx = center_x("TURBO!")
    ty = 28
    for ox in [-1, 0, 1]:
        for oy in [-1, 0, 1]:
            if ox == 0 and oy == 0:
                continue
            glow = (color[0] // 4, color[1] // 4, color[2] // 4)
            display.draw_text_small(tx + ox, ty + oy, "TURBO!", glow)
    display.draw_text_small(tx, ty, "TURBO!", color)


def _show_splash(display):
    """Show the WONDER CABINET startup splash (~3 seconds)."""
    import pygame
    clock = pygame.time.Clock()
    duration = 3.0
    t = 0.0
    while t < duration:
        dt = clock.tick(30) / 1000.0
        t += dt

        display.clear(Colors.BLACK)

        if t < 0.3:
            # Black screen
            pass
        elif t < 1.0:
            # "WONDER" fades in
            progress = (t - 0.3) / 0.7
            brightness = min(1.0, progress)
            c = int(255 * brightness)
            color = (c, c, c)
            wx = center_x("WONDER") + 1
            display.draw_text_small(wx, 24, "WONDER", color)
        elif t < 1.7:
            # "WONDER" stays, "CABINET" fades in
            wx = center_x("WONDER") + 1
            display.draw_text_small(wx, 24, "WONDER", Colors.WHITE)
            progress = (t - 1.0) / 0.7
            brightness = min(1.0, progress)
            c = int(255 * brightness)
            color = (c, c, c)
            cx = center_x("CABINET") + 1
            display.draw_text_small(cx, 34, "CABINET", color)
        else:
            # Rainbow glow + sparkles
            phase = t - 1.7
            hue = (phase * 0.5) % 1.0
            pulse = 0.7 + 0.3 * math.sin(phase * 4.0)
            color = _hue_to_rgb(hue)
            color = (int(color[0] * pulse), int(color[1] * pulse), int(color[2] * pulse))

            # Sparkles
            for _ in range(20):
                sx = random.randint(0, GRID_SIZE - 1)
                sy = random.randint(0, GRID_SIZE - 1)
                display.set_pixel(sx, sy, _hue_to_rgb((hue + random.random() * 0.5) % 1.0))

            # "WONDER" with glow
            wx = center_x("WONDER") + 1
            for ox in [-1, 0, 1]:
                for oy in [-1, 0, 1]:
                    if ox == 0 and oy == 0:
                        continue
                    glow = (color[0] // 4, color[1] // 4, color[2] // 4)
                    display.draw_text_small(wx + ox, 24 + oy, "WONDER", glow)
            display.draw_text_small(wx, 24, "WONDER", color)

            # "CABINET" with glow
            hue2 = (hue + 0.15) % 1.0
            color2 = _hue_to_rgb(hue2)
            color2 = (int(color2[0] * pulse), int(color2[1] * pulse), int(color2[2] * pulse))
            cx = center_x("CABINET") + 1
            for ox in [-1, 0, 1]:
                for oy in [-1, 0, 1]:
                    if ox == 0 and oy == 0:
                        continue
                    glow2 = (color2[0] // 4, color2[1] // 4, color2[2] // 4)
                    display.draw_text_small(cx + ox, 34 + oy, "CABINET", glow2)
            display.draw_text_small(cx, 34, "CABINET", color2)

        display.render()

        # Allow quitting or skipping during splash
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN:
                return


def has_any_input(input_state):
    """Return True if any button or direction is active."""
    return (input_state.up_pressed or input_state.down_pressed or
            input_state.left_pressed or input_state.right_pressed or
            input_state.action_l or input_state.action_r or
            input_state.action_l_held or input_state.action_r_held)


def _pick_idle_visual(display):
    """Pick a weighted random visual for idle screen."""
    from visuals import ALL_VISUALS
    from visuals.slideshow import Slideshow, AllVisuals, _randomize_style
    import settings

    # Load user overrides
    user_weights = settings.get_idle_category_weights()
    favorites = set(settings.get_idle_favorites())
    blacklist = set(settings.get_idle_blacklist())

    # Base weights: user overrides > built-in defaults
    base_weights = dict(AllVisuals.CATEGORY_WEIGHTS)
    base_weights.update(user_weights)

    candidates = []
    for v in ALL_VISUALS:
        if issubclass(v, Slideshow):
            continue
        cat = getattr(v, 'category', '')
        if cat == 'utility':
            continue

        name = v.__name__
        if name in blacklist:
            continue

        weight = base_weights.get(cat, 2)
        if weight <= 0:
            continue

        if name in favorites:
            weight *= 2

        candidates.extend([v] * weight)

    if not candidates:
        return None
    cls = random.choice(candidates)
    vis = cls(display)
    vis.reset()
    _randomize_style(vis)
    # Preload: call draw() once to trigger any lazy loading (GIF frames, etc.)
    # This ensures smooth transitions without loading hitches
    vis.draw()
    return vis


def main():
    print("=" * 50)
    print("LED ARCADE")
    print("=" * 50)
    print()

    # Register all games and visuals into categories
    register_games(ALL_GAMES)
    register_visuals(ALL_VISUALS)

    # Get all non-empty categories (games then visuals)
    categories = get_all_categories('all')

    print("Categories loaded:")
    for cat in categories:
        print(f"  {cat.name}: {len(cat.items)} items")
        for item in cat.items:
            print(f"    - {item.name}")

    print()
    print("Controls:")
    print("  Left/Right - Switch category")
    print("  Up/Down    - Select item")
    print("  Space      - Launch")
    print("  Hold both  - Back/Exit (games)")
    print()
    print("=" * 50)

    # Initialize
    display = Display()
    _show_splash(display)
    input_handler = InputHandler()
    clock = pygame.time.Clock()

    # State
    in_menu = True
    cat_index = 0
    item_index = 0
    current_item = None
    is_game = False
    is_two_player = False  # 2-player games skip high scores
    exit_hold = 0.0         # Timer for hold-to-exit (menu and gameplay)
    visual_exit_hold = 0.0  # Timer for hold-to-exit visuals (both buttons)

    # Idle screen state
    idle_timer = 0.0
    in_idle = False
    idle_visual = None
    idle_cycle_timer = 0.0

    # Menu name scroll state
    name_scroll_x = 0.0       # current scroll offset in pixels
    name_scroll_timer = 0.0   # time since current item was selected
    prev_cat_index = -1
    prev_item_index = -1
    NAME_SCROLL_DELAY = 0.8   # seconds before scrolling starts
    NAME_SCROLL_SPEED = 20.0  # pixels per second
    NAME_SCROLL_PAUSE = 1.0   # pause at end before resetting

    # Idle transition manager
    from transitions import TransitionManager
    idle_transition = TransitionManager()

    # Shuffle mode state
    in_shuffle_mode = False
    shuffle_playlist = None

    # Konami code state
    konami_buffer = []
    konami_active = False
    konami_timer = 0.0

    # Spin easter egg state
    spin_buffer = []         # Last 4 directional inputs (L/D/R/U only)
    spin_circle_times = []   # Timestamps of completed circles
    spin_active = False
    spin_timer = 0.0

    # Game over state
    game_over_state = GameOverState.FLASHING
    game_over_selection = 0  # 0 = PLAY AGAIN, 1 = MENU
    flash_timer = 0.0  # Timer for alternating screens
    flash_show_leaderboard = False  # Which screen to show
    player_initials = ['A', 'A', 'A']  # Current initials being entered
    initials_cursor = 0  # Which letter is being edited (0-2)
    player_made_leaderboard = False
    player_rank = -1
    final_score = 0  # Store score when game ends
    game_over_initialized = False  # Track if game over has been processed
    game_over_lockout = 0.0  # Input lockout when entering game over
    milestone_timer = 0.0  # Timer for milestone celebration

    # High score manager
    hsm = get_high_score_manager()

    # Debounce for left/right navigation
    input_cooldown = 0  # Cooldown for initials entry

    # Scroll acceleration state (vertical - items)
    scroll_held_time = 0.0   # How long up/down has been held
    scroll_accum = 0.0       # Accumulator for auto-scroll timing
    scroll_dir = 0           # -1 = up, +1 = down, 0 = none

    # Horizontal scroll state (categories)
    cat_scroll_held_time = 0.0   # How long left/right has been held
    cat_scroll_accum = 0.0       # Accumulator for auto-scroll timing
    cat_scroll_dir = 0           # -1 = left, +1 = right, 0 = none

    running = True
    while running:
        dt = clock.tick(30) / 1000.0
        input_cooldown = max(0, input_cooldown - dt)

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update input
        input_state = input_handler.update()

        if in_menu:
            # Idle screen logic
            if in_idle:
                if has_any_input(input_state):
                    # Any input returns to menu instantly
                    in_idle = False
                    idle_visual = None
                    idle_timer = 0.0
                    idle_transition.transitioning = False
                else:
                    # Handle ongoing transition
                    if idle_transition.transitioning:
                        idle_transition.update(dt)
                        idle_transition.draw(display)
                        # Also update new visual during transition
                        if idle_visual:
                            idle_visual.update(dt)
                    else:
                        idle_cycle_timer += dt
                        if idle_cycle_timer >= 30.0:
                            # Start transition to new visual
                            old_visual = idle_visual
                            new_visual = _pick_idle_visual(display)
                            if old_visual and new_visual:
                                idle_transition.start(old_visual, new_visual)
                                # Draw first transition frame to mask preload flash
                                idle_transition.draw(display)
                            idle_visual = new_visual
                            idle_cycle_timer = 0.0
                        if idle_visual and not idle_transition.transitioning:
                            idle_visual.update(dt)
                            idle_visual.draw()
            elif konami_active:
                konami_timer += dt
                if konami_timer >= 2.0:
                    konami_active = False
                    idle_timer = 0.0
                else:
                    draw_konami_egg(display, konami_timer)
            elif spin_active:
                spin_timer += dt
                if spin_timer >= 2.0:
                    spin_active = False
                    idle_timer = 0.0
                else:
                    draw_spin_egg(display, spin_timer)
            else:
                # Hold either button 2 sec to quit app
                if input_state.action_l_held or input_state.action_r_held:
                    exit_hold += dt
                    if exit_hold >= 2.0:
                        running = False
                else:
                    exit_hold = 0.0

                # Track idle time
                if has_any_input(input_state):
                    idle_timer = 0.0
                else:
                    idle_timer += dt
                    if idle_timer >= 60.0:
                        in_idle = True
                        idle_visual = _pick_idle_visual(display)
                        idle_cycle_timer = 0.0

                # Konami code tracking
                _ki = None
                if input_state.up_pressed: _ki = 'U'
                elif input_state.down_pressed: _ki = 'D'
                elif input_state.left_pressed: _ki = 'L'
                elif input_state.right_pressed: _ki = 'R'
                elif input_state.action_l: _ki = 'A'
                elif input_state.action_r: _ki = 'B'
                if _ki:
                    konami_buffer.append(_ki)
                    konami_buffer = konami_buffer[-10:]
                konami_match = konami_buffer == KONAMI_CODE
                if konami_match:
                    konami_active = True
                    konami_timer = 0.0
                    konami_buffer = []
                # Intercept button presses mid-sequence (9th input is A)
                konami_intercept = (len(konami_buffer) >= 9 and
                                    konami_buffer[-9:] == KONAMI_CODE[:9])

                # Spin easter egg tracking (directional only, independent of konami)
                _si = None
                if input_state.left_pressed: _si = 'L'
                elif input_state.down_pressed: _si = 'D'
                elif input_state.right_pressed: _si = 'R'
                elif input_state.up_pressed: _si = 'U'
                if _si:
                    spin_buffer.append(_si)
                    spin_buffer = spin_buffer[-4:]
                    if spin_buffer == ['L', 'D', 'R', 'U'] or spin_buffer == ['R', 'D', 'L', 'U']:
                        spin_circle_times.append(time.time())
                        spin_buffer = []
                        # Keep only recent circles
                        now_t = time.time()
                        spin_circle_times = [t for t in spin_circle_times if now_t - t <= 2.5]
                        if len(spin_circle_times) >= 3:
                            spin_active = True
                            spin_timer = 0.0
                            spin_circle_times = []
                            spin_buffer = []

                if not categories:
                    draw_menu(display, categories, 0, 0)
                elif not konami_match:
                    category = categories[cat_index]

                    # Category navigation (left/right) with scroll acceleration
                    if len(categories) > 1:
                        if input_state.left_pressed:
                            cat_index = (cat_index - 1) % len(categories)
                            item_index = 0
                            cat_scroll_dir = -1
                            cat_scroll_held_time = 0.0
                            cat_scroll_accum = 0.0
                            scroll_held_time = 0.0
                            scroll_accum = 0.0
                            scroll_dir = 0
                        elif input_state.right_pressed:
                            cat_index = (cat_index + 1) % len(categories)
                            item_index = 0
                            cat_scroll_dir = 1
                            cat_scroll_held_time = 0.0
                            cat_scroll_accum = 0.0
                            scroll_held_time = 0.0
                            scroll_accum = 0.0
                            scroll_dir = 0
                        elif cat_scroll_dir != 0 and ((cat_scroll_dir == -1 and input_state.left) or (cat_scroll_dir == 1 and input_state.right)):
                            cat_scroll_held_time += dt
                            if cat_scroll_held_time >= 0.4:
                                t_accel = min(cat_scroll_held_time - 0.4, 1.5)
                                interval = 0.18 - (0.12 * t_accel / 1.5)
                                cat_scroll_accum += dt
                                while cat_scroll_accum >= interval:
                                    cat_scroll_accum -= interval
                                    cat_index = (cat_index + cat_scroll_dir) % len(categories)
                                    item_index = 0
                        else:
                            cat_scroll_dir = 0
                            cat_scroll_held_time = 0.0
                            cat_scroll_accum = 0.0

                    # Item navigation (up/down) with scroll acceleration
                    if category.items:
                        n_items = len(category.items)
                        if input_state.up_pressed:
                            item_index = (item_index - 1) % n_items
                            scroll_dir = -1
                            scroll_held_time = 0.0
                            scroll_accum = 0.0
                        elif input_state.down_pressed:
                            item_index = (item_index + 1) % n_items
                            scroll_dir = 1
                            scroll_held_time = 0.0
                            scroll_accum = 0.0
                        elif scroll_dir != 0 and ((scroll_dir == -1 and input_state.up) or (scroll_dir == 1 and input_state.down)):
                            scroll_held_time += dt
                            if scroll_held_time >= 0.4:
                                t_accel = min(scroll_held_time - 0.4, 1.5)
                                interval = 0.18 - (0.12 * t_accel / 1.5)
                                scroll_accum += dt
                                while scroll_accum >= interval:
                                    scroll_accum -= interval
                                    item_index = (item_index + scroll_dir) % n_items
                        else:
                            scroll_dir = 0
                            scroll_held_time = 0.0
                            scroll_accum = 0.0

                        # Launch item (skip if mid-konami intercept)
                        if not konami_intercept and (input_state.action_l or input_state.action_r):
                            item_class = category.items[item_index]

                            # Game playlist (shuffle mode)
                            if hasattr(item_class, 'games'):
                                shuffle_playlist = item_class
                                game_class = random.choice(item_class.games)
                                current_item = game_class(display)
                                current_item.reset()
                                is_game = True
                                is_two_player = False
                                in_shuffle_mode = True
                                in_menu = False
                                exit_hold = 0.0
                            else:
                                current_item = item_class(display)
                                current_item.reset()
                                is_game = hasattr(current_item, 'state') and isinstance(current_item.state, GameState)
                                is_two_player = getattr(current_item, 'category', '') == '2_player'
                                in_shuffle_mode = False
                                shuffle_playlist = None
                                in_menu = False
                                exit_hold = 0.0

                    # Update name scroll for selected item
                    if cat_index != prev_cat_index or item_index != prev_item_index:
                        name_scroll_x = 0.0
                        name_scroll_timer = 0.0
                        prev_cat_index = cat_index
                        prev_item_index = item_index
                    else:
                        name_scroll_timer += dt
                        if name_scroll_timer > NAME_SCROLL_DELAY:
                            items = categories[cat_index].items
                            if items:
                                name = items[item_index].name
                                name_w = _text_width(name)
                                max_name_w = 58  # pixels available
                                if name_w > max_name_w:
                                    max_scroll = name_w - max_name_w
                                    if name_scroll_x < max_scroll:
                                        name_scroll_x += NAME_SCROLL_SPEED * dt
                                        name_scroll_x = min(name_scroll_x, max_scroll)
                                    elif name_scroll_timer > NAME_SCROLL_DELAY + max_scroll / NAME_SCROLL_SPEED + NAME_SCROLL_PAUSE:
                                        name_scroll_x = 0.0
                                        name_scroll_timer = 0.0

                    draw_menu(display, categories, cat_index, item_index, name_scroll_x)

        else:
            # Running item (game or visual)
            # Hold BOTH buttons 2 sec to return to menu (games need both to avoid conflicts)
            if input_state.action_l_held and input_state.action_r_held:
                exit_hold += dt
                if exit_hold >= 2.0:
                    in_menu = True
                    current_item = None
                    game_over_initialized = False
                    in_shuffle_mode = False
                    shuffle_playlist = None
                    idle_timer = 0.0
                    exit_hold = 0.0
            else:
                exit_hold = 0.0

            if current_item:
                if is_game:
                    # Game logic
                    if current_item.state == GameState.GAME_OVER:
                        # First time entering game over
                        if not game_over_initialized:
                            game_over_initialized = True
                            final_score = current_item.score
                            hsm.log_play(current_item.name, final_score)
                            game_over_lockout = 1.5  # Ignore inputs for 1.5 seconds

                            if is_two_player:
                                # 2-player games: skip high scores, go straight to action selection
                                game_over_state = GameOverState.CHOOSE_ACTION
                                game_over_selection = 0
                                player_made_leaderboard = False
                            else:
                                # Single player: check for high score
                                player_made_leaderboard = hsm.is_high_score(current_item.name, final_score)
                                if player_made_leaderboard:
                                    # Check if this beats the current #1 (milestone)
                                    existing = hsm.get_top_scores(current_item.name)
                                    if existing and final_score > existing[0][1]:
                                        game_over_state = GameOverState.MILESTONE
                                        milestone_timer = 0.0
                                    else:
                                        game_over_state = GameOverState.ENTER_INITIALS
                                    player_initials = ['A', 'A', 'A']
                                    initials_cursor = 0
                                else:
                                    game_over_state = GameOverState.FLASHING
                                    flash_timer = 0.0
                                    flash_show_leaderboard = False

                        # Tick down the lockout timer
                        if game_over_lockout > 0:
                            game_over_lockout -= dt

                        # Handle based on current game over sub-state (only if lockout expired)
                        if game_over_state == GameOverState.MILESTONE:
                            milestone_timer += dt
                            draw_milestone_celebration(display, milestone_timer)
                            if milestone_timer >= 3.0:
                                game_over_state = GameOverState.ENTER_INITIALS

                        elif game_over_state == GameOverState.FLASHING:
                            flash_timer += dt
                            if flash_timer >= 2.0:
                                flash_timer = 0.0
                                flash_show_leaderboard = not flash_show_leaderboard

                            # Any input skips to action selection (if lockout expired)
                            if game_over_lockout <= 0:
                                if input_state.action_l or input_state.action_r or input_state.up_pressed or input_state.down_pressed:
                                    game_over_state = GameOverState.CHOOSE_ACTION
                                    game_over_selection = 0

                            # Draw appropriate screen
                            if flash_show_leaderboard:
                                draw_leaderboard(display, current_item.name, player_rank)
                            else:
                                draw_game_over_score(display, final_score)

                        elif game_over_state == GameOverState.ENTER_INITIALS:
                            if input_cooldown <= 0 and game_over_lockout <= 0:
                                # Up/Down cycles letter
                                if input_state.up_pressed:
                                    letter = player_initials[initials_cursor]
                                    if letter == 'A':
                                        player_initials[initials_cursor] = 'Z'
                                    else:
                                        player_initials[initials_cursor] = chr(ord(letter) - 1)
                                    input_cooldown = 0.15
                                elif input_state.down_pressed:
                                    letter = player_initials[initials_cursor]
                                    if letter == 'Z':
                                        player_initials[initials_cursor] = 'A'
                                    else:
                                        player_initials[initials_cursor] = chr(ord(letter) + 1)
                                    input_cooldown = 0.15
                                # Left goes back a letter
                                elif input_state.left_pressed:
                                    if initials_cursor > 0:
                                        initials_cursor -= 1
                                    input_cooldown = 0.2
                                # Right or action confirms current letter
                                elif input_state.right_pressed or input_state.action_l or input_state.action_r:
                                    if initials_cursor < 2:
                                        initials_cursor += 1
                                    else:
                                        # Last letter — submit, then show flashing with highlight
                                        initials_str = ''.join(player_initials)
                                        player_rank = hsm.add_score(current_item.name, initials_str, final_score)
                                        game_over_state = GameOverState.FLASHING
                                        flash_timer = 0.0
                                        flash_show_leaderboard = True
                                        game_over_lockout = 1.0
                                    input_cooldown = 0.2

                            draw_initials_entry(display, player_initials, initials_cursor, final_score)

                        elif game_over_state == GameOverState.CHOOSE_ACTION:
                            if game_over_lockout <= 0:
                                if input_state.up_pressed or input_state.down_pressed:
                                    game_over_selection = 1 - game_over_selection
                                elif input_state.action_l or input_state.action_r:
                                    if game_over_selection == 0:
                                        if in_shuffle_mode and shuffle_playlist:
                                            # Next game from playlist
                                            game_class = random.choice(shuffle_playlist.games)
                                            current_item = game_class(display)
                                            current_item.reset()
                                        else:
                                            # Play again
                                            current_item.reset()
                                        final_score = 0
                                        game_over_initialized = False
                                        player_made_leaderboard = False
                                        player_rank = -1
                                    else:
                                        # Return to menu
                                        in_menu = True
                                        current_item = None
                                        final_score = 0
                                        game_over_initialized = False
                                        player_made_leaderboard = False
                                        player_rank = -1
                                        in_shuffle_mode = False
                                        shuffle_playlist = None
                                        idle_timer = 0.0
                                    game_over_selection = 0

                            if current_item:
                                if is_two_player:
                                    # Use game's own draw_game_over (shows winner)
                                    current_item.draw_game_over()
                                    # Add play again / menu options at bottom
                                    if game_over_selection == 0:
                                        display.draw_text_small(4, 50, ">AGAIN", Colors.YELLOW)
                                        display.draw_text_small(32, 50, " MENU", Colors.GRAY)
                                    else:
                                        display.draw_text_small(4, 50, " AGAIN", Colors.GRAY)
                                        display.draw_text_small(32, 50, ">MENU", Colors.YELLOW)
                                else:
                                    first_opt = "NEXT GAME" if in_shuffle_mode else "PLAY AGAIN"
                                    draw_action_selection(display, game_over_selection, final_score,
                                                          player_made_leaderboard, player_rank,
                                                          first_option=first_opt)
                    else:
                        current_item.update(input_state, dt)
                        current_item.draw()
                else:
                    # Visual — hold both buttons 2s to return to menu
                    # Skip for visuals that handle their own exit (e.g. Controls)
                    if not getattr(current_item, 'custom_exit', False):
                        if input_state.action_l_held and input_state.action_r_held:
                            visual_exit_hold += dt
                            if visual_exit_hold >= 2.0:
                                in_menu = True
                                current_item = None
                                visual_exit_hold = 0.0
                                idle_timer = 0.0
                        else:
                            visual_exit_hold = 0.0

                    if current_item:
                        current_item.handle_input(input_state)
                        if getattr(current_item, 'wants_exit', False):
                            in_menu = True
                            current_item = None
                            idle_timer = 0.0
                        else:
                            current_item.update(dt)
                            current_item.draw()

        display.render()

    pygame.quit()
    print("Thanks for playing!")


if __name__ == "__main__":
    main()
