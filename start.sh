#!/bin/bash
# LED Arcade startup script
# Pulls latest code then launches the arcade.
# Used by the led-arcade.service systemd unit.

cd /home/thiselazar/led-arcade

# Pull latest code (ignore errors if no network)
git pull --ff-only 2>/dev/null

exec python3 run_hardware.py
