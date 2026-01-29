#!/usr/bin/env python3
"""
LED Arcade - Hardware Launcher
==============================
Runs the arcade on the LED matrix hardware.

Controls (keyboard over SSH):
  Arrow Keys or WASD - Joystick
  Space              - Left action button
  Z                  - Right action button
  Hold button 2s     - Back/Exit
"""

import sys
import time
from enum import Enum, auto

# Hardware display and input
from hardware import HardwareDisplay, HardwareInput, Colors, GRID_SIZE

# Game/visual catalogs
from catalog import register_games, register_visuals, get_all_categories
from games import ALL_GAMES
from visuals import ALL_VISUALS

# Game state from arcade module
sys.path.insert(0, '.')
from arcade import GameState

# High scores
from highscores import get_high_score_manager


# =============================================================================
# GAME OVER STATES
# =============================================================================

class GameOverState(Enum):
    FLASHING = auto()
    ENTER_INITIALS = auto()
    CHOOSE_ACTION = auto()


# =============================================================================
# DRAWING FUNCTIONS
# =============================================================================

def draw_game_over_score(display, score):
    display.clear(Colors.BLACK)
    display.draw_text_small(2, 20, "GAME OVER", Colors.RED)
    display.draw_text_small(2, 32, f"SCORE:{score}", Colors.WHITE)


def draw_leaderboard(display, game_name, highlight_rank=-1):
    display.clear(Colors.BLACK)
    display.draw_text_small(2, 2, "HIGH SCORES", Colors.YELLOW)
    display.draw_line(0, 9, 63, 9, Colors.DARK_GRAY)

    hsm = get_high_score_manager()
    scores = hsm.get_top_scores(game_name)

    if not scores:
        display.draw_text_small(2, 28, "NO SCORES", Colors.GRAY)
        display.draw_text_small(2, 38, "YET!", Colors.GRAY)
        return

    y = 14
    for i, (initials, score) in enumerate(scores):
        rank = i + 1
        color = Colors.CYAN if rank == highlight_rank else Colors.WHITE
        display.draw_text_small(2, y, f"{rank}", color)
        display.draw_text_small(10, y, initials, color)
        score_str = str(score)
        score_x = 62 - len(score_str) * 4
        display.draw_text_small(score_x, y, score_str, color)
        y += 8


def draw_initials_entry(display, initials, cursor_pos, score):
    display.clear(Colors.BLACK)
    display.draw_text_small(2, 2, "NEW RECORD!", Colors.YELLOW)
    display.draw_text_small(2, 12, f"SCORE:{score}", Colors.WHITE)
    display.draw_line(0, 22, 63, 22, Colors.DARK_GRAY)
    display.draw_text_small(2, 26, "ENTER NAME:", Colors.GRAY)

    slot_x = 20
    for i, letter in enumerate(initials):
        x = slot_x + i * 10
        if i == cursor_pos:
            display.draw_text_small(x + 1, 34, "^", Colors.YELLOW)
            display.draw_text_small(x, 42, letter, Colors.CYAN)
            display.draw_text_small(x + 1, 50, "v", Colors.YELLOW)
        else:
            display.draw_text_small(x, 42, letter, Colors.WHITE)

    display.draw_line(0, 56, 63, 56, Colors.DARK_GRAY)
    display.draw_text_small(4, 58, "BTN:CONFIRM", Colors.GRAY)


def draw_action_selection(display, selection, score, made_leaderboard=False, rank=-1):
    display.clear(Colors.BLACK)

    if made_leaderboard:
        display.draw_text_small(2, 8, f"RANK {rank}!", Colors.CYAN)
        display.draw_text_small(2, 18, f"SCORE:{score}", Colors.WHITE)
    else:
        display.draw_text_small(2, 12, "GAME OVER", Colors.RED)
        display.draw_text_small(2, 22, f"SCORE:{score}", Colors.WHITE)

    if selection == 0:
        display.draw_text_small(2, 40, ">PLAY AGAIN", Colors.YELLOW)
        display.draw_text_small(2, 50, " MENU", Colors.GRAY)
    else:
        display.draw_text_small(2, 40, " PLAY AGAIN", Colors.GRAY)
        display.draw_text_small(2, 50, ">MENU", Colors.YELLOW)


def draw_menu(display, categories, cat_index, item_index):
    display.clear(Colors.BLACK)

    if not categories:
        display.draw_text_small(8, 30, "NO ITEMS", Colors.RED)
        return

    category = categories[cat_index]
    cat_color = category.color
    display.draw_text_small(4, 2, category.name, cat_color)

    if len(categories) > 1:
        display.set_pixel(1, 4, Colors.GRAY)
        display.set_pixel(0, 5, Colors.GRAY)
        display.set_pixel(1, 6, Colors.GRAY)
        display.set_pixel(62, 4, Colors.GRAY)
        display.set_pixel(63, 5, Colors.GRAY)
        display.set_pixel(62, 6, Colors.GRAY)

    dot_start_x = 32 - (len(categories) * 2)
    for i in range(len(categories)):
        color = Colors.WHITE if i == cat_index else Colors.DARK_GRAY
        display.set_pixel(dot_start_x + i * 4, 9, color)

    display.draw_line(0, 11, 63, 11, Colors.DARK_GRAY)

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

    if start_idx > 0:
        display.draw_text_small(58, 14, "^", Colors.GRAY)
    if start_idx + visible < len(items):
        display.draw_text_small(58, 14 + (visible - 1) * 8, "v", Colors.GRAY)

    display.draw_line(0, 56, 63, 56, Colors.DARK_GRAY)
    display.draw_text_small(2, 58, "SPC:GO", Colors.GRAY)
    display.draw_text_small(34, 58, "HOLD:EXIT", Colors.GRAY)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 50)
    print("LED ARCADE - HARDWARE MODE")
    print("=" * 50)
    print()
    print("Controls:")
    print("  Arrow keys / WASD - Navigate")
    print("  Space             - Left action")
    print("  Z                 - Right action")
    print("  Hold button 2s    - Back / Exit")
    print()

    # Register content
    register_games(ALL_GAMES)
    register_visuals(ALL_VISUALS)
    categories = get_all_categories('all')

    print(f"Loaded {len(categories)} categories")
    for cat in categories:
        print(f"  {cat.name}: {len(cat.items)} items")
    print()

    # Initialize hardware
    print("Initializing display...")
    display = HardwareDisplay(brightness=80, gpio_slowdown=4)

    print("Initializing input...")
    input_handler = HardwareInput(use_gpio=True)

    print("=" * 50)
    print("READY! Use keyboard to control.")
    print("=" * 50)

    # State
    in_menu = True
    cat_index = 0
    item_index = 0
    is_two_player = False  # 2-player games skip high scores
    current_item = None
    is_game = False
    exit_hold = 0.0         # Timer for hold-to-exit (menu and gameplay)
    visual_exit_hold = 0.0

    # Game over state
    game_over_state = GameOverState.FLASHING
    game_over_selection = 0
    flash_timer = 0.0
    flash_show_leaderboard = False
    player_initials = ['A', 'A', 'A']
    initials_cursor = 0
    player_made_leaderboard = False
    player_rank = -1
    final_score = 0
    game_over_initialized = False
    game_over_lockout = 0.0

    hsm = get_high_score_manager()
    input_cooldown = 0

    FPS = 30
    last_time = time.time()

    running = True
    try:
        while running:
            # Delta time
            now = time.time()
            dt = now - last_time
            last_time = now

            input_cooldown = max(0, input_cooldown - dt)

            # Update input
            input_state = input_handler.update()

            if in_menu:
                # Hold either button 2 sec to quit app
                if input_state.action_l_held or input_state.action_r_held:
                    exit_hold += dt
                    if exit_hold >= 2.0:
                        running = False
                else:
                    exit_hold = 0.0

                if not categories:
                    draw_menu(display, categories, 0, 0)
                else:
                    category = categories[cat_index]

                    if input_state.left_pressed and len(categories) > 1:
                        cat_index = (cat_index - 1) % len(categories)
                        item_index = 0
                    elif input_state.right_pressed and len(categories) > 1:
                        cat_index = (cat_index + 1) % len(categories)
                        item_index = 0

                    if category.items:
                        if input_state.up_pressed and item_index > 0:
                            item_index -= 1
                        elif input_state.down_pressed and item_index < len(category.items) - 1:
                            item_index += 1

                        if input_state.action_l or input_state.action_r:
                            item_class = category.items[item_index]
                            current_item = item_class(display)
                            current_item.reset()
                            is_game = hasattr(current_item, 'state') and isinstance(current_item.state, GameState)
                            is_two_player = getattr(current_item, 'category', '') == '2_player'
                            in_menu = False
                            exit_hold = 0.0

                    draw_menu(display, categories, cat_index, item_index)

            else:
                # Running game or visual
                # Hold either button 2 sec to return to menu
                if input_state.action_l_held or input_state.action_r_held:
                    exit_hold += dt
                    if exit_hold >= 2.0:
                        in_menu = True
                        current_item = None
                        game_over_initialized = False
                        exit_hold = 0.0
                else:
                    exit_hold = 0.0

                if current_item:
                    if is_game:
                        if current_item.state == GameState.GAME_OVER:
                            if not game_over_initialized:
                                game_over_initialized = True
                                final_score = current_item.score
                                game_over_lockout = 1.5

                                if is_two_player:
                                    # 2-player games: skip high scores
                                    game_over_state = GameOverState.CHOOSE_ACTION
                                    game_over_selection = 0
                                    player_made_leaderboard = False
                                else:
                                    # Single player: check for high score
                                    player_made_leaderboard = hsm.is_high_score(current_item.name, final_score)
                                    if player_made_leaderboard:
                                        game_over_state = GameOverState.ENTER_INITIALS
                                        player_initials = ['A', 'A', 'A']
                                        initials_cursor = 0
                                    else:
                                        game_over_state = GameOverState.FLASHING
                                        flash_timer = 0.0
                                        flash_show_leaderboard = False

                            if game_over_lockout > 0:
                                game_over_lockout -= dt

                            if game_over_state == GameOverState.FLASHING:
                                flash_timer += dt
                                if flash_timer >= 2.0:
                                    flash_timer = 0.0
                                    flash_show_leaderboard = not flash_show_leaderboard

                                if game_over_lockout <= 0:
                                    if input_state.action_l or input_state.action_r or input_state.up_pressed or input_state.down_pressed:
                                        game_over_state = GameOverState.CHOOSE_ACTION
                                        game_over_selection = 0

                                if flash_show_leaderboard:
                                    draw_leaderboard(display, current_item.name)
                                else:
                                    draw_game_over_score(display, final_score)

                            elif game_over_state == GameOverState.ENTER_INITIALS:
                                if input_cooldown <= 0 and game_over_lockout <= 0:
                                    if input_state.up_pressed:
                                        letter = player_initials[initials_cursor]
                                        player_initials[initials_cursor] = 'Z' if letter == 'A' else chr(ord(letter) - 1)
                                        input_cooldown = 0.15
                                    elif input_state.down_pressed:
                                        letter = player_initials[initials_cursor]
                                        player_initials[initials_cursor] = 'A' if letter == 'Z' else chr(ord(letter) + 1)
                                        input_cooldown = 0.15
                                    elif input_state.left_pressed and initials_cursor > 0:
                                        initials_cursor -= 1
                                        input_cooldown = 0.2
                                    elif input_state.right_pressed and initials_cursor < 2:
                                        initials_cursor += 1
                                        input_cooldown = 0.2
                                    elif input_state.action_l or input_state.action_r:
                                        initials_str = ''.join(player_initials)
                                        player_rank = hsm.add_score(current_item.name, initials_str, final_score)
                                        game_over_state = GameOverState.CHOOSE_ACTION
                                        game_over_selection = 0
                                        input_cooldown = 0.2

                                draw_initials_entry(display, player_initials, initials_cursor, final_score)

                            elif game_over_state == GameOverState.CHOOSE_ACTION:
                                if game_over_lockout <= 0:
                                    if input_state.up_pressed or input_state.down_pressed:
                                        game_over_selection = 1 - game_over_selection
                                    elif input_state.action_l or input_state.action_r:
                                        if game_over_selection == 0:
                                            current_item.reset()
                                            final_score = 0
                                            game_over_initialized = False
                                            player_made_leaderboard = False
                                            player_rank = -1
                                        else:
                                            in_menu = True
                                            current_item = None
                                            final_score = 0
                                            game_over_initialized = False
                                            player_made_leaderboard = False
                                            player_rank = -1
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
                                        draw_action_selection(display, game_over_selection, final_score,
                                                              player_made_leaderboard, player_rank)
                        else:
                            current_item.update(input_state, dt)
                            current_item.draw()
                    else:
                        # Visual
                        if input_state.action_l_held or input_state.action_r_held:
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

            # Frame rate limiting
            elapsed = time.time() - now
            sleep_time = (1.0 / FPS) - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        input_handler.cleanup()

    print("Thanks for playing!")


if __name__ == "__main__":
    main()
