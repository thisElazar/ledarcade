#!/usr/bin/env python3
"""
LED Arcade - Unified Launcher
=============================
Combined games and visuals with category-based navigation.

Controls:
  Left/Right - Switch category (page)
  Up/Down    - Select item within category
  Space      - Launch selected item
  Escape     - Back to menu / Exit
"""

import pygame
import sys
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
    ENTER_INITIALS = auto() # Player entering their initials
    CHOOSE_ACTION = auto()  # PLAY AGAIN / MENU selection


def draw_game_over_score(display, score):
    """Draw the GAME OVER screen with player's score."""
    display.clear(Colors.BLACK)
    display.draw_text_small(8, 20, "GAME OVER", Colors.RED)
    display.draw_text_small(12, 32, f"SCORE:{score}", Colors.WHITE)


def draw_leaderboard(display, game_name, highlight_rank=-1):
    """Draw the high scores leaderboard.

    Args:
        display: The display to draw on
        game_name: Name of the game to show scores for
        highlight_rank: 1-3 to highlight that rank, -1 for no highlight
    """
    display.clear(Colors.BLACK)
    display.draw_text_small(4, 2, "HIGH SCORES", Colors.YELLOW)
    display.draw_line(0, 9, 63, 9, Colors.DARK_GRAY)

    hsm = get_high_score_manager()
    scores = hsm.get_top_scores(game_name)

    if not scores:
        display.draw_text_small(12, 28, "NO SCORES", Colors.GRAY)
        display.draw_text_small(16, 38, "YET!", Colors.GRAY)
        return

    y = 14
    for i, (initials, score) in enumerate(scores):
        rank = i + 1
        # Highlight the player's new score
        if rank == highlight_rank:
            color = Colors.CYAN
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
    display.draw_text_small(4, 2, "NEW RECORD!", Colors.YELLOW)
    display.draw_text_small(12, 12, f"SCORE:{score}", Colors.WHITE)

    display.draw_line(0, 22, 63, 22, Colors.DARK_GRAY)
    display.draw_text_small(2, 26, "ENTER NAME:", Colors.GRAY)

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
    display.draw_text_small(4, 58, "BTN:CONFIRM", Colors.GRAY)


def draw_action_selection(display, selection, score, made_leaderboard=False, rank=-1):
    """Draw the PLAY AGAIN / MENU selection.

    Args:
        display: The display to draw on
        selection: 0 = PLAY AGAIN, 1 = MENU
        score: The player's score
        made_leaderboard: Whether player made the leaderboard
        rank: Player's rank if they made leaderboard
    """
    display.clear(Colors.BLACK)

    if made_leaderboard:
        display.draw_text_small(8, 8, f"RANK #{rank}!", Colors.CYAN)
        display.draw_text_small(12, 18, f"SCORE:{score}", Colors.WHITE)
    else:
        display.draw_text_small(8, 12, "GAME OVER", Colors.RED)
        display.draw_text_small(12, 22, f"SCORE:{score}", Colors.WHITE)

    # Draw selection options
    if selection == 0:
        display.draw_text_small(4, 40, ">PLAY AGAIN", Colors.YELLOW)
        display.draw_text_small(4, 50, " MENU", Colors.GRAY)
    else:
        display.draw_text_small(4, 40, " PLAY AGAIN", Colors.GRAY)
        display.draw_text_small(4, 50, ">MENU", Colors.YELLOW)


def draw_menu(display, categories, cat_index, item_index):
    """Draw the category-based menu."""
    display.clear(Colors.BLACK)

    if not categories:
        display.draw_text_small(8, 30, "NO ITEMS", Colors.RED)
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

    # Category indicator dots
    dot_start_x = 32 - (len(categories) * 2)
    for i, _ in enumerate(categories):
        color = Colors.WHITE if i == cat_index else Colors.DARK_GRAY
        display.set_pixel(dot_start_x + i * 4, 9, color)

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

    for i, item_class in enumerate(items[start_idx:start_idx + visible]):
        actual_idx = start_idx + i
        y = 14 + i * 8

        if actual_idx == item_index:
            display.draw_rect(0, y - 1, 64, 7, Colors.DARK_GRAY)
            display.draw_text_small(2, y, f">{item_class.name}", cat_color)
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
    display.draw_text_small(36, 58, "ESC:EXIT", Colors.GRAY)


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
    print("  Escape     - Back/Exit")
    print()
    print("=" * 50)

    # Initialize
    display = Display()
    input_handler = InputHandler()
    clock = pygame.time.Clock()

    # State
    in_menu = True
    cat_index = 0
    item_index = 0
    current_item = None
    is_game = False
    visual_exit_hold = 0.0  # Timer for hold-to-exit visuals

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

    # High score manager
    hsm = get_high_score_manager()

    # Debounce for left/right navigation
    nav_cooldown = 0
    input_cooldown = 0  # Cooldown for initials entry

    running = True
    while running:
        dt = clock.tick(30) / 1000.0
        nav_cooldown = max(0, nav_cooldown - dt)
        input_cooldown = max(0, input_cooldown - dt)

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update input
        input_state = input_handler.update()

        if in_menu:
            if not categories:
                if input_state.back:
                    running = False
                draw_menu(display, categories, 0, 0)
            else:
                category = categories[cat_index]

                # Category navigation (left/right) with cooldown
                if nav_cooldown <= 0:
                    if input_state.left and len(categories) > 1:
                        cat_index = (cat_index - 1) % len(categories)
                        item_index = 0
                        nav_cooldown = 0.2
                    elif input_state.right and len(categories) > 1:
                        cat_index = (cat_index + 1) % len(categories)
                        item_index = 0
                        nav_cooldown = 0.2

                # Item navigation (up/down)
                if category.items:
                    if input_state.up and item_index > 0:
                        item_index -= 1
                    elif input_state.down and item_index < len(category.items) - 1:
                        item_index += 1

                    # Launch item
                    if input_state.action:
                        item_class = category.items[item_index]
                        current_item = item_class(display)
                        current_item.reset()
                        # Check if it's a game (has GameState) or visual
                        is_game = hasattr(current_item, 'state') and isinstance(current_item.state, GameState)
                        in_menu = False

                if input_state.back:
                    running = False

                draw_menu(display, categories, cat_index, item_index)

        else:
            # Running item (game or visual)
            if input_state.back:
                in_menu = True
                current_item = None
                game_over_initialized = False
            elif current_item:
                if is_game:
                    # Game logic
                    if current_item.state == GameState.GAME_OVER:
                        # First time entering game over - check for high score
                        if not game_over_initialized:
                            game_over_initialized = True
                            final_score = current_item.score
                            player_made_leaderboard = hsm.is_high_score(current_item.name, final_score)
                            game_over_lockout = 1.5  # Ignore inputs for 1.5 seconds
                            if player_made_leaderboard:
                                # Go straight to initials entry
                                game_over_state = GameOverState.ENTER_INITIALS
                                player_initials = ['A', 'A', 'A']
                                initials_cursor = 0
                            else:
                                # Start flashing between score and leaderboard
                                game_over_state = GameOverState.FLASHING
                                flash_timer = 0.0
                                flash_show_leaderboard = False

                        # Tick down the lockout timer
                        if game_over_lockout > 0:
                            game_over_lockout -= dt

                        # Handle based on current game over sub-state (only if lockout expired)
                        if game_over_state == GameOverState.FLASHING:
                            flash_timer += dt
                            if flash_timer >= 2.0:
                                flash_timer = 0.0
                                flash_show_leaderboard = not flash_show_leaderboard

                            # Any input skips to action selection (if lockout expired)
                            if game_over_lockout <= 0:
                                if input_state.action or input_state.up or input_state.down:
                                    game_over_state = GameOverState.CHOOSE_ACTION
                                    game_over_selection = 0

                            # Draw appropriate screen
                            if flash_show_leaderboard:
                                draw_leaderboard(display, current_item.name)
                            else:
                                draw_game_over_score(display, final_score)

                        elif game_over_state == GameOverState.ENTER_INITIALS:
                            if input_cooldown <= 0 and game_over_lockout <= 0:
                                # Up/Down cycles letter
                                if input_state.up:
                                    letter = player_initials[initials_cursor]
                                    if letter == 'A':
                                        player_initials[initials_cursor] = 'Z'
                                    else:
                                        player_initials[initials_cursor] = chr(ord(letter) - 1)
                                    input_cooldown = 0.15
                                elif input_state.down:
                                    letter = player_initials[initials_cursor]
                                    if letter == 'Z':
                                        player_initials[initials_cursor] = 'A'
                                    else:
                                        player_initials[initials_cursor] = chr(ord(letter) + 1)
                                    input_cooldown = 0.15
                                # Left/Right moves cursor
                                elif input_state.left and initials_cursor > 0:
                                    initials_cursor -= 1
                                    input_cooldown = 0.2
                                elif input_state.right and initials_cursor < 2:
                                    initials_cursor += 1
                                    input_cooldown = 0.2
                                # Action confirms initials
                                elif input_state.action:
                                    initials_str = ''.join(player_initials)
                                    player_rank = hsm.add_score(current_item.name, initials_str, final_score)
                                    game_over_state = GameOverState.CHOOSE_ACTION
                                    game_over_selection = 0
                                    input_cooldown = 0.2

                            draw_initials_entry(display, player_initials, initials_cursor, final_score)

                        elif game_over_state == GameOverState.CHOOSE_ACTION:
                            if input_state.up or input_state.down:
                                game_over_selection = 1 - game_over_selection
                            elif input_state.action:
                                if game_over_selection == 0:
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
                                game_over_selection = 0

                            if current_item:
                                draw_action_selection(display, game_over_selection, final_score,
                                                      player_made_leaderboard, player_rank)
                    else:
                        current_item.update(input_state, dt)
                        current_item.draw()
                else:
                    # Visual logic
                    # Hold action button for 2 seconds to return to menu
                    if input_state.action_held:
                        visual_exit_hold += dt
                        if visual_exit_hold >= 2.0:
                            in_menu = True
                            current_item = None
                            visual_exit_hold = 0.0
                    else:
                        visual_exit_hold = 0.0

                    if current_item:
                        current_item.handle_input(input_state)
                        current_item.update(dt)
                        current_item.draw()

        display.render()

    pygame.quit()
    print("Thanks for playing!")


if __name__ == "__main__":
    main()
