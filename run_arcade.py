#!/usr/bin/env python3
"""
LED Arcade - Desktop Launcher
=============================
The shell (shell.py) in a window, driven by the keyboard. Same menus, idle
screen and game-over flow as the cabinet.

Controls:
  Arrows       - Navigate menus and play
  Space / Z    - Left / right action button
  Hold both 2s - Back to menu (games and visuals)

    python run_arcade.py           # the look of the marketing clips: LED dots and glow on black
    python run_arcade.py --paper   # the white page of the Reels and carousels
    python run_arcade.py --plain   # a bare window of square pixels

The two LED looks come from paper_display.py. Close the window or Ctrl-C to quit.
"""

import sys

import pygame

import shell
from arcade import Display, InputHandler


def main(display_class=None):
    if display_class is None:
        if "--paper" in sys.argv:
            from paper_display import PaperDisplay as display_class
        elif "--plain" in sys.argv:
            display_class = Display
        else:
            from paper_display import PanelDisplay as display_class
    shell.run(display_class(), InputHandler())


if __name__ == "__main__":
    main()
    pygame.quit()
