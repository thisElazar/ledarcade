#!/bin/bash
# LED Arcade startup script
# Updates code then launches the arcade.
# Used by the led-arcade.service systemd unit.
#
# Two update modes, chosen by the gitignored `.dev` flag file:
#   - Dev cabinet (.dev present):     follow the tip of `main` (the test bed).
#   - Distribution cabinet (no .dev): run the latest released version tag.
# A release is cut by tagging a verified commit on main (vMAJOR.MINOR, e.g. v1.4).

cd "$(dirname "$(readlink -f "$0")")"

# Update code (ignore errors if there's no network — run last-known code).
if [ -f .dev ]; then
    # Dev cabinet: always the latest main.
    git pull --ff-only 2>/dev/null
else
    # Distribution cabinet: check out the highest version tag.
    git fetch --tags --force origin 2>/dev/null
    latest=$(git tag -l 'v*' | sort -V | tail -1)
    if [ -n "$latest" ]; then
        git checkout -q "$latest" 2>/dev/null
    fi
fi

exec python3 run_hardware.py
