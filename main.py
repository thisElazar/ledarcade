#!/usr/bin/env python3
"""
LED Arcade - Games Launcher
===========================

34 classic arcade games for a 64x64 LED matrix display.
Desktop emulator via PyGame for prototyping.

Controls:
  Arrow Keys  - Move / Navigate
  Space       - Action (fire, jump, select)
  Z           - Secondary action
  Escape      - Return to menu

For the full experience with games + visuals, run:
  python run_arcade.py

See README.md for complete game list and documentation.

Requirements:
  pip install pygame

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
