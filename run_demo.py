#!/usr/bin/env python3
"""
LED Arcade - Demo Launcher
==========================
The arcade (run_arcade.py) in the look of the square marketing clips: round
LED dots with a soft glow on black. Same controls.

    python run_demo.py
"""

from paper_display import PanelDisplay
from run_arcade import main

if __name__ == "__main__":
    main(PanelDisplay)
