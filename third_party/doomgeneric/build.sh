#!/bin/sh
# Build doom_pipe, the headless Doom engine the cabinet talks to over a pipe.
# One command, no Makefile edits. JOBS defaults to 2: a full build on a 1 GB
# Pi 3B while the cabinet is running should not take every core.
set -e
cd "$(dirname "$0")/doomgeneric"
make -f Makefile.pipe -j"${JOBS:-2}"
echo "built: $(pwd)/doom_pipe"
