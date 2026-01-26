#!/usr/bin/env python3
"""
LED Arcade - Visual Effects Runner
==================================
Standalone runner for visual effects on the 64x64 LED matrix.

Controls:
  Left/Right - Previous/Next visual
  Space      - Visual-specific action
  Escape     - Return to menu / Exit

Run with: python run_visuals.py
"""

import pygame
import sys
from arcade import Display, InputHandler, Colors, GRID_SIZE

# Import all visuals
from visuals import ALL_VISUALS


def draw_menu(display, visuals, selection):
    """Draw the visual selection menu."""
    display.clear(Colors.BLACK)

    # Title
    display.draw_text_small(4, 2, "VISUALS", Colors.MAGENTA)
    display.draw_line(0, 9, 63, 9, Colors.DARK_GRAY)

    # Visual list
    visible = 6
    start_idx = max(0, selection - visible // 2)

    for i, vis_class in enumerate(visuals[start_idx:start_idx + visible]):
        actual_idx = start_idx + i
        y = 14 + i * 8

        if actual_idx == selection:
            display.draw_rect(0, y - 1, 64, 7, Colors.DARK_GRAY)
            display.draw_text_small(2, y, f">{vis_class.name}", Colors.CYAN)
        else:
            display.draw_text_small(2, y, f" {vis_class.name}", Colors.WHITE)

    # Instructions
    display.draw_line(0, 56, 63, 56, Colors.DARK_GRAY)
    display.draw_text_small(2, 58, "SPACE:SELECT", Colors.GRAY)


def main():
    print("LED Arcade - Visual Effects")
    print("===========================")

    if not ALL_VISUALS:
        print("No visuals found! Add visuals to the visuals/ folder.")
        sys.exit(1)

    for vis in ALL_VISUALS:
        print(f"Loaded: {vis.name}")

    print("\n" + "=" * 30)
    print("Starting visual runner...")

    # Initialize
    display = Display()
    input_handler = InputHandler()
    clock = pygame.time.Clock()

    # State
    in_menu = True
    menu_selection = 0
    current_visual = None

    running = True
    while running:
        dt = clock.tick(30) / 1000.0

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update input
        input_state = input_handler.update()

        if in_menu:
            # Menu navigation
            if input_state.up and menu_selection > 0:
                menu_selection -= 1
            elif input_state.down and menu_selection < len(ALL_VISUALS) - 1:
                menu_selection += 1
            elif input_state.action and ALL_VISUALS:
                # Start selected visual
                current_visual = ALL_VISUALS[menu_selection](display)
                current_visual.reset()
                in_menu = False
            elif input_state.back:
                running = False

            draw_menu(display, ALL_VISUALS, menu_selection)

        else:
            # Running visual
            if input_state.back:
                # Return to menu
                in_menu = True
                current_visual = None
            elif current_visual:
                # Let visual handle input
                current_visual.handle_input(input_state)

                # Update and draw
                current_visual.update(dt)
                current_visual.draw()

        display.render()

    pygame.quit()
    print("Visual runner closed.")


if __name__ == "__main__":
    main()
