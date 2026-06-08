# LED Arcade

A self-contained **64×64 RGB LED arcade cabinet** — **60+ playable games** and **590+ visual scenes** running on a Raspberry Pi, with a full desktop emulator for development.

![resolution 64x64](https://img.shields.io/badge/resolution-64%C3%9764-blue)
![python 3.11–3.13](https://img.shields.io/badge/python-3.11–3.13-green)
![pygame 2.x](https://img.shields.io/badge/pygame-2.x-orange)

The same code runs two ways: on a desktop via PyGame (a 640×640 window, 10× scale) for development, and on real hardware via an HUB75 LED matrix and arcade controls. Games and visuals are written once against a shared display interface; `arcade.py` backs it with PyGame, `hardware.py` backs it with the LED matrix — neither the games nor the visuals know the difference.

---

## Quick Start (desktop)

```bash
cd led-arcade
pip install -r requirements.txt      # pygame, numpy, Pillow

python run_arcade.py                 # unified launcher — games + visuals
# or:
python main.py                       # games only
python run_visuals.py                # visuals only
```

> **Python version:** use **3.11–3.13**. Python 3.14 currently trips a circular-import bug in `pygame.font`.

On real hardware, `run_hardware.py` is the entry point (launched by a systemd service). See **[HARDWARE.md](HARDWARE.md)** for the build and **[DEPLOYMENT.md](DEPLOYMENT.md)** for how cabinets are provisioned and updated.

---

## Controls

The cabinet has a **4-way joystick** and **two action buttons**. By convention the two buttons are unified — either button performs the action — so anyone can play without thinking about which button to press. (A few games that genuinely need two distinct actions, like pinball flippers, are the exception.)

| Input | Cabinet | Desktop |
|-------|---------|---------|
| Navigate / move | Joystick | Arrow keys |
| Action / select | Either button | Space or Z |
| Switch category | Joystick left / right | Left / Right |
| Select item | Joystick up / down | Up / Down |
| Back to menu | Hold both buttons | Hold both / Escape |

---

## What's inside

Content is organized into categories you page through in the menu. **The in-app menu is the source of truth** — the counts below are a snapshot as of **v1.0**.

### Games — 60+ across 7 categories

In-app names are lightly genericized takes on the classics (no trademarked titles), e.g. `ASTROIDS`, `PAK-MAN`, `MONKEY KONG`.

| Category | Count | Examples (as shown in the menu) |
|----------|-------|----------|
| Arcade   | 20 | SNAKE, PING, BREAK OUT, INVADERS, TETROMINOS, ASTROIDS, PAK-MAN, GALAXA, FROGGY, MONKEY KONG, DIG DIG, CENTIPEED |
| Modern   | 10 | 2048, FLAPPY BIRD, GEODASH, STACK, AGAR.IO, PORTAL, BLOONS, BLOONS TD, POWDER GAME |
| Retro    | 9  | ARCANOID, INDIE 500, JAZZBALL, PIPE MAZE, SPACE CRUISE, 3D MONSTR MAZE, SKI RUN, DND |
| 2-Player | 6  | CHESS, CHECKERS, CONNECT FOUR, GO, REVERSI, MANCALA |
| Toys     | 6  | 15 PUZZLE, LITE OUT, MASTER CODE, RUSH HR, SAIMON, TAP IT |
| Bar      | 5  | POOL, DARTS, BOWLING, SHUFFLEBOARD, PINBALL |
| Unique   | 4  | DRIFT, FISHING, LASER MIRRORS, WINDOW WASHER |

Plus curated **playlists** (All Games, Arcade Mix, Quick Play, …) that shuffle through a themed set.

### Visuals — 590+ scenes across 20+ categories

Ambient art, simulations, and demos. Many "visuals" are whole collections of scenes, which is why the scene count is large. Headline categories:

| Category | Scenes | What it is |
|----------|--------|------------|
| Art | 236 | Painting and generative-art galleries |
| Titles | 71 | Wonder-cabinet title screens |
| Demos | 48 | Demoscene-style effects |
| Automata | 26 | Cellular automata, flocking, slime mold |
| Mechanics | 20 | Machines, engines, linkages |
| Digital | 18 | Plasma, Matrix rain, attractors, moiré |
| Science (micro/macro/bench) | ~40 | Cells, DNA, orbits, tectonics, lab instruments |
| Math · Music · Nature · Household · Gallery · Culture · Cooking · Sprites · Superheroes · … | the rest | |

Utility screens live here too — including **SYSTEM INFO**, which shows the cabinet's IP, temperature, Python version, and deployed release (e.g. `VER: v1.0`).

---

## Development & deployment

This repo follows a simple, enforced workflow:

- **`main`** is the always-green trunk. All work lands via pull requests; **CI** (GitHub Actions) runs a headless smoke test that constructs and animates every visual and game, plus a sim↔hardware interface-parity check. Don't commit directly to `main`.
- **Releases are version tags** (`vMAJOR.MINOR`). A tag is cut from a `main` commit after it's verified on the dev cabinet. Distribution cabinets run the latest `v*` tag — never `main`'s tip.

Run the test suite locally the same way CI does:

```bash
pip install -r requirements-dev.txt
SDL_VIDEODRIVER=dummy pytest -q tests/
```

The full workflow — branching, cutting a release, how cabinets update, and rollback — is documented in **[DEPLOYMENT.md](DEPLOYMENT.md)**.

---

## Adding content

### A game

```python
# games/mygame.py
from arcade import Game, GameState, Colors

class MyGame(Game):
    name = "MYGAME"            # short menu name
    description = "Fun game!"
    category = "arcade"        # arcade, modern, retro, 2_player, toys, bar, unique

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0

    def update(self, input_state, dt):
        # Unify both buttons unless the game truly needs two actions.
        if input_state.action_l or input_state.action_r:
            ...

    def draw(self):
        self.display.clear(Colors.BLACK)
        self.display.draw_text_small(10, 30, "HELLO!", Colors.GREEN)
```

Register it in `games/__init__.py` (import the class and add it to `ALL_GAMES`).

### A visual

```python
# visuals/myvisual.py
from visuals import Visual, Colors

class MyVisual(Visual):
    name = "MYVISUAL"
    description = "Cool effect"
    category = "digital"

    def reset(self):
        ...

    def update(self, dt):
        self.time += dt

    def draw(self):
        self.display.clear(Colors.BLACK)
        ...
```

Register it in `visuals/__init__.py` (import the class and add it to `ALL_VISUALS`).

> The CI smoke test will construct and run your new game/visual headless — if it crashes on creation or in its first frames, the PR goes red before it can reach a cabinet.

---

## Display API

```python
display.clear(color)                        # fill screen
display.set_pixel(x, y, color)              # single pixel
display.get_pixel(x, y)                     # read a pixel
display.draw_rect(x, y, w, h, color)        # rectangle
display.draw_line(x0, y0, x1, y1, color)    # line
display.draw_circle(x, y, r, color)         # circle
display.draw_text_small(x, y, text, color)  # 3×5 pixel font (left-align at x=2)
```

**General-purpose colors:** `Colors.BLACK`, `WHITE`, `RED`, `GREEN`, `BLUE`, `YELLOW`, `CYAN`, `MAGENTA`, `ORANGE`, `PINK`, `PURPLE`, `LIME`, `GRAY`, `DARK_GRAY` (plus semantic ones like `PLAYER`, `ENEMY`, `FOOD`).

---

## Project structure

```
led-arcade/
├── run_arcade.py        # desktop unified launcher (games + visuals)
├── run_visuals.py       # desktop visuals-only launcher
├── main.py              # desktop games-only launcher
├── run_hardware.py      # hardware entry point (Raspberry Pi)
├── arcade.py            # core framework + PyGame display/input (the shared interface)
├── hardware.py          # LED matrix + GPIO driver (same interface as arcade.py)
├── catalog.py           # menu categories / registration
├── settings.py          # persisted user settings (brightness, timers, …)
├── highscores.py        # high-score persistence
├── cabinet_config.py    # per-cabinet hardware config (gitignored JSON)
├── provision.sh         # one-command setup for a fresh cabinet
├── start.sh             # boot-time updater + launcher (systemd)
├── requirements.txt     # runtime deps   ·  requirements-dev.txt  # + test/build deps
├── DEPLOYMENT.md        # branch/release/deploy workflow
├── HARDWARE.md          # wiring + Pi build guide
├── tests/               # headless smoke + interface-parity tests
├── games/               # 60+ game implementations + playlists
└── visuals/             # 590+ visual scenes
```

---

## Design principles

**64×64 constraints**
- Every pixel matters — bold, readable shapes; high contrast reads best on LED.
- Reserve the top rows for HUD/score; the 3×5 font is uppercase + numbers + punctuation.

**Performance**
- Target **30 FPS**; drive motion with delta time (`dt`) so speed is frame-rate independent.
- The Pi is far weaker than a dev machine — if something is smooth on desktop, still check it on the cabinet.

---

## License

MIT — do whatever you want with it.
