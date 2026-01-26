#!/usr/bin/env python3
"""
LED Arcade - Main Entry Point
=============================

A collection of classic arcade games designed for a 64x64 LED matrix display.
Currently runs on desktop via PyGame for prototyping.

Controls:
  Arrow Keys  - Joystick (4-way/8-way depending on game)
  Space       - Primary action button (fire/select/hard drop)
  Z           - Secondary button (rarely used)
  Escape      - Return to menu

Games Included:
  - Snake     : Classic snake game
  - Pong      : 1v1 versus AI
  - Breakout  : Brick breaker
  - Invaders  : Space Invaders clone
  - Tetris    : Falling block puzzle
  - Asteroids : Vector space shooter

To run:
  python main.py

Requirements:
  pip install pygame

Author: LED Arcade Project
License: MIT
"""

import sys
import os

# Add the project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from arcade import Arcade
from games import ALL_GAMES


def main():
    """Main entry point."""
    print("=" * 50)
    print("LED ARCADE - 64x64 Pixel Games")
    print("=" * 50)
    print()
    print("Controls:")
    print("  Arrow Keys  - Move / Navigate")
    print("  Space       - Action / Select / Fire")
    print("  Escape      - Back to Menu")
    print()
    print("Starting arcade...")
    print()
    
    # Create arcade system
    arcade = Arcade()
    
    # Register all games
    for game_class in ALL_GAMES:
        arcade.register_game(game_class)
        print(f"  Loaded: {game_class.name}")
    
    print()
    print("=" * 50)
    print()
    
    # Run the arcade!
    arcade.run()
    
    print("Thanks for playing!")


if __name__ == "__main__":
    main()
