#!/bin/bash
# LED Arcade startup script
# Pulls latest code then launches the arcade.
# Used by the led-arcade.service systemd unit.

cd /home/thiselazar/led-arcade

# Show a boot splash immediately so the display isn't dark.
# run_hardware.py will kill it before taking over the matrix.
python3 boot_splash.py &

# Pull latest code (ignore errors if no network)
git pull --ff-only 2>/dev/null

exec python3 run_hardware.py
