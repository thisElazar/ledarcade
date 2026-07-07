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

# The systemd service runs as root (the LED matrix needs it), but the checkout is
# owned by the cabinet user. Git's "dubious ownership" guard would otherwise block
# every command here — silently breaking auto-update AND the version readout. Trust
# this repo, the same way the in-app updater (visuals/refresh.py) does.
git_safe() { git -c safe.directory="$PWD" "$@"; }

# Update code (ignore errors if there's no network — run last-known code).
if [ -f .dev ]; then
    # Dev cabinet: always the latest main.
    git_safe pull --ff-only 2>/dev/null
else
    # Distribution cabinet: check out the highest version tag.
    # --prune --prune-tags is essential: without it, a tag deleted on GitHub
    # (the documented rollback path in DEPLOYMENT.md) stays on the cabinet
    # forever and gets re-checked-out every boot. Pruning lets tag deletion
    # actually roll the fleet back.
    git_safe fetch --tags --force --prune --prune-tags origin 2>/dev/null
    latest=$(git_safe tag -l 'v*' | sort -V | tail -1)
    if [ -n "$latest" ]; then
        git_safe checkout -q "$latest" 2>/dev/null
    fi
fi

# Record the deployed version for the SYSTEM INFO panel (resolved here, where git
# runs reliably, rather than from the service process where it was showing N/A).
git_safe describe --tags --match 'v*' --always > .version 2>/dev/null || echo "unknown" > .version

exec python3 run_hardware.py
