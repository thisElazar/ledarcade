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
from arcade import Display, InputHandler, Colors, GRID_SIZE, Game, GameState
from catalog import (
    register_games, register_visuals, get_all_categories,
    GAME_CATEGORIES, VISUAL_CATEGORIES
)

# Import all games and visuals
from games import ALL_GAMES
from visuals import ALL_VISUALS


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

    # Debounce for left/right navigation
    nav_cooldown = 0

    running = True
    while running:
        dt = clock.tick(30) / 1000.0
        nav_cooldown = max(0, nav_cooldown - dt)

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
            elif current_item:
                if is_game:
                    # Game logic
                    if current_item.state == GameState.GAME_OVER:
                        current_item.draw_game_over()
                        if input_state.action:
                            current_item.reset()
                    else:
                        current_item.update(input_state, dt)
                        current_item.draw()
                else:
                    # Visual logic
                    current_item.handle_input(input_state)
                    current_item.update(dt)
                    current_item.draw()

        display.render()

    pygame.quit()
    print("Thanks for playing!")


if __name__ == "__main__":
    main()
