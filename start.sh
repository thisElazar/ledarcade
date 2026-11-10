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

# Failures go to the same log the UPDATE menu writes (visuals/refresh.py).
# Keep only its tail, so a cabinet that boots offline for years cannot fill the card.
[ -f .update.log ] && tail -n 200 .update.log > .update.log.tmp && mv .update.log.tmp .update.log
log_fail() { echo "$(date '+%Y-%m-%d %H:%M:%S')  start.sh: $1 failed" >> .update.log; }

# A rollback from the UPDATE menu writes .rollback_hold: the commit it rolled
# back from. While that is still the newest version, leave the checkout alone,
# or every power cycle would undo the rollback. A newer version clears the hold.
held() {
    [ -f .rollback_hold ] || return 1
    [ "$(cat .rollback_hold)" = "$(git_safe rev-parse "$1^{commit}" 2>/dev/null)" ] && return 0
    rm -f .rollback_hold
    return 1
}

# Update code (ignore errors if there's no network — run last-known code).
if [ -f .dev ]; then
    # Dev cabinet: always the latest main.
    git_safe fetch origin main 2>>.update.log || log_fail "fetch origin main"
    if ! held origin/main; then
        git_safe merge --ff-only origin/main >/dev/null 2>>.update.log || log_fail "merge --ff-only origin/main"
    fi
else
    # Distribution cabinet: check out the highest version tag.
    # --prune --prune-tags is essential: without it, a tag deleted on GitHub
    # (the documented rollback path in DEPLOYMENT.md) stays on the cabinet
    # forever and gets re-checked-out every boot. Pruning lets tag deletion
    # actually roll the fleet back.
    git_safe fetch --tags --force --prune --prune-tags origin 2>>.update.log || log_fail "fetch tags"
    latest=$(git_safe tag -l 'v*' | sort -V | tail -1)
    if [ -n "$latest" ] && ! held "$latest"; then
        git_safe checkout -q "$latest" 2>>.update.log || log_fail "checkout $latest"
    fi
fi

# Record the deployed version for the SYSTEM INFO panel (resolved here, where git
# runs reliably, rather than from the service process where it was showing N/A).
git_safe describe --tags --match 'v*' --always > .version 2>/dev/null || echo "unknown" > .version

exec python3 run_hardware.py
