# doomgeneric in the Wonder Cabinet

This folder is [doomgeneric](https://github.com/ozkl/doomgeneric), a portable
Doom engine, at upstream commit `dcb7a8d`, plus one patch of our own: the
headless backend `doomgeneric/doomgeneric_pipe.c` and the engine hooks it
needs. `git log -- third_party/doomgeneric` shows the two apart.

**Licence: GPL-2.0** (see `LICENSE` here). It is the only part of this
repository that is not MIT.

The cabinet never links against this code. `games/doom.py` starts `doom_pipe`
as a child process and talks to it over a pipe, which is why the rest of the
repository stays MIT. Keep it that way: no Python extension, no copying engine
C into the cabinet's own code.

Build with `./build.sh` (writes `doomgeneric/doom_pipe`). The engine needs a
Doom IWAD to run; the cabinet uses Freedoom, which is not in git.
