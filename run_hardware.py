#!/usr/bin/env python3
"""
LED Arcade - Cabinet Launcher
=============================
The shell (shell.py) on the LED matrix, driven by the joystick and buttons.
start.sh execs this under the led-arcade systemd service.
"""

import subprocess

import settings
import shell
from cabinet_config import get_gpio_slowdown
from hardware import HardwareDisplay, HardwareInput


def _kill_boot_splash():
    """Stop the boot splash service so we can take over the LED matrix."""
    try:
        subprocess.run(["systemctl", "stop", "led-arcade-splash"],
                       timeout=5, capture_output=True)
        print("Boot splash stopped.")
    except Exception:
        pass  # no splash running, that's fine


def main():
    _kill_boot_splash()
    print("Initializing display...")
    display = HardwareDisplay(brightness=settings.get_brightness(),
                              gpio_slowdown=get_gpio_slowdown(),
                              gamma=settings.get_gamma(), toe=settings.get_toe(),
                              limit_refresh_hz=settings.get_refresh_hz())
    display.set_mirror(settings.get_mirror_enabled(), settings.get_mirror_port(),
                       settings.get_mirror_hdmi(), settings.get_mirror_web())
    print("Initializing input...")
    shell.run(display, HardwareInput(use_gpio=True))


if __name__ == "__main__":
    main()
