# LED Arcade

A collection of **35 classic arcade games** and **44 visual effects** designed for a **64x64 RGB LED matrix**, with a desktop emulator for prototyping.

![64x64 resolution](https://img.shields.io/badge/resolution-64x64-blue)
![Python 3.7+](https://img.shields.io/badge/python-3.7+-green)
![PyGame](https://img.shields.io/badge/pygame-2.0+-orange)

---

## Quick Start

```bash
# Clone or download the project
cd led-arcade

# Install dependencies
pip install pygame

# Run the unified arcade (games + visuals)
python run_arcade.py

# Or run games only
python main.py

# Or run visuals only
python run_visuals.py
```

A 640x640 window opens (10x scale of the 64x64 display).

---

## Controls

| Key | Action |
|-----|--------|
| **Arrow Keys** | Move / Navigate menu |
| **Space** | Action (fire, select, jump, place bomb) |
| **Z** | Secondary action (rarely used) |
| **Escape** | Return to menu |

**In unified launcher (`run_arcade.py`):**
- **Left/Right** - Switch category
- **Up/Down** - Select item
- **Space** - Launch

---

## Games (35 Total)

Games are organized into categories in the menu:

### Arcade (17 games)
Classic coin-op arcade machines.

| Game | Description | Controls |
|------|-------------|----------|
| **Asteroids** | Destroy asteroids in space | Arrows rotate/thrust, Space fires |
| **Bomberman** | Place bombs, destroy enemies | Arrows move, Space places bomb |
| **Breakout** | Break all bricks with the ball | Left/Right moves paddle, Space launches |
| **Centipede** | Shoot the descending centipede | Arrows move, Space fires |
| **Dig Dug** | Dig tunnels, pump up enemies | Arrows dig/move, Space pumps |
| **Donkey Kong** | Climb ladders, jump barrels | Arrows move/climb, Space jumps |
| **Frogger** | Cross traffic and river | Arrows hop |
| **Galaga** | Formation-based shooter | Left/Right moves, Space fires |
| **Invaders** | Defend Earth from aliens | Left/Right moves, Space fires |
| **Lode Runner** | Collect gold, trap enemies | Arrows move/climb, Space digs |
| **Lunar Lander** | Land safely on the pad | Arrows thrust |
| **Night Driver** | First-person night racing | Left/Right steers |
| **Pac-Man** | Eat dots, avoid ghosts | Arrows set direction |
| **Pong** | Classic paddle game vs AI | Up/Down moves paddle |
| **Q*bert** | Hop on cubes to change color | Arrows hop diagonally |
| **Snake** | Eat food, grow longer | Arrows change direction |
| **Tetris** | Stack blocks, clear lines | Arrows move, Up rotates, Space drops |

### Retro (6 games)
Classic computer and console games.

| Game | Description | Controls |
|------|-------------|----------|
| **Arkanoid** | 1986 Taito classic | Left/Right moves paddle |
| **Indy 500** | Top-down racing | Arrows steer, Space gas |
| **JezzBall** | Trap bouncing atoms | Arrows + Space builds walls |
| **Pipe Dream** | Connect pipes before flood | Arrows move, Space places |
| **Space Cruise** | Space exploration | Arrows move |
| **Trash Blaster** | Shoot trash | Arrows aim, Space fires |

### Modern (6 games)
Mobile-era and puzzle games.

| Game | Description | Controls |
|------|-------------|----------|
| **2048** | Slide tiles to combine | Arrows slide all tiles |
| **Flappy** | Tap to fly through pipes | Space flaps |
| **Geometry Dash** | Jump over obstacles | Space jumps |
| **Lights Out** | Toggle all lights off | Arrows select, Space toggles |
| **Stack** | Stack blocks perfectly | Space drops block |
| **Stick Runner** | Endless runner | Space jumps |

### 2-Player (6 games)
Turn-based multiplayer with shared controller.

| Game | Description | Controls |
|------|-------------|----------|
| **Checkers** | Classic checkers | Arrows select, Space moves |
| **Chess** | Full chess game | Arrows select, Space confirms |
| **Connect 4** | Get 4 in a row | Left/Right selects, Space drops |
| **Go** | 9x9 Go board | Arrows place, Space confirms |
| **Mancala** | Sow seeds, capture | Arrows select, Space sows |
| **Othello** | Flip opponent's discs | Arrows place, Space confirms |

---

## Visuals (44 Total)

Ambient visual effects organized by category:

### Automata (11)
Cellular automata and agent simulations.

| Visual | Description |
|--------|-------------|
| **Aurora** | Northern lights patterns |
| **Boids** | Flocking bird simulation |
| **Faders** | Color gradient transitions |
| **Gyre** | Spiral vortex patterns |
| **Hodge** | Hodgepodge machine |
| **Life** | Conway's Game of Life |
| **Mitosis** | Cell division patterns |
| **Quarks** | Particle physics sim |
| **Rug** | Rug-like CA patterns |
| **Slime** | Physarum slime mold |
| **Wolfram** | 1D elementary CA |

### Nature (7)
Natural phenomena.

| Visual | Description |
|--------|-------------|
| **Fire** | Realistic fire effect |
| **Lake** | Calm water reflections |
| **Plasma** | Classic plasma effect |
| **Ripples** | Water ripple effects |
| **Road** | Endless road journey |
| **Starfield** | 3D starfield flythrough |
| **Weather** | Rain, snow, storms |

### Digital (13)
Mathematical and computer visualizations.

| Visual | Description |
|--------|-------------|
| **Attractors** | Strange attractor trajectories |
| **Copper Bars** | Amiga raster bars |
| **Cylon** | Larson scanner |
| **Flux** | Flowing energy patterns |
| **Matrix** | Falling green code |
| **Mobius** | Twisting surface |
| **Moire** | Interference patterns |
| **Rainbow** | Color wheel cycle |
| **Rotozoom** | Rotating zoom |
| **Sine Scroller** | Wavy scroller |
| **Trance** | Hypnotic patterns |
| **Twister** | Rotating bars |
| **XOR Pattern** | Fractal patterns |

### Art (3)
Famous painting interpretations.

| Visual | Description |
|--------|-------------|
| **Mondrian** | Geometric composition |
| **Starry Night** | Van Gogh's masterpiece |
| **Water Lilies** | Monet's garden |

### Household (5)
Domestic nostalgia.

| Visual | Description |
|--------|-------------|
| **Cat** | Stretching on pillow |
| **DVD** | Bouncing DVD logo |
| **Lava Lamp** | Flowing lava lamp |
| **Polaroid** | Photo slideshow |
| **Solitaire** | Win card cascade |

### Utility (5)
Functional displays.

| Visual | Description |
|--------|-------------|
| **About** | Credits |
| **Clock** | Time display |
| **Settings** | Display settings |
| **Sysinfo** | System info |
| **Test Pattern** | Test all pixels |

---

## Project Structure

```
led-arcade/
├── run_arcade.py        # Unified launcher (games + visuals)
├── run_visuals.py       # Visual-only launcher
├── run_hardware.py      # Hardware launcher for Raspberry Pi
├── main.py              # Games-only launcher
├── arcade.py            # Core framework
├── hardware.py          # LED matrix driver
├── catalog.py           # Category system
├── highscores.py        # High score persistence
├── requirements.txt     # Dependencies
├── README.md            # This file
├── ROADMAP.md           # Development roadmap
├── HARDWARE.md          # Hardware build guide
├── GAME_ROADMAP.md      # Game implementation tracker
├── VISUAL_RESOURCES.md  # Visual effect references
├── games/               # All game implementations
│   ├── __init__.py
│   ├── snake.py
│   ├── pacman.py
│   ├── donkeykong.py
│   └── ... (35 games)
└── visuals/             # All visual effects
    ├── __init__.py
    ├── plasma.py
    ├── fire.py
    └── ... (44 visuals)
```

---

## Adding New Content

### Creating a Game

```python
# games/mygame.py
from arcade import Game, GameState, Colors

class MyGame(Game):
    name = "MYGAME"           # Menu display name (keep short)
    description = "Fun game!" # Short description
    category = "arcade"       # arcade, retro, modern, or 2_player

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0

    def update(self, input_state, dt):
        if input_state.action_l or input_state.action_r:
            # Handle button press (either button)
            pass

    def draw(self):
        self.display.clear(Colors.BLACK)
        self.display.draw_text_small(10, 30, "HELLO!", Colors.GREEN)
```

Register in `games/__init__.py`:
```python
from .mygame import MyGame
ALL_GAMES.append(MyGame)
```

### Creating a Visual

```python
# visuals/myvisual.py
from visuals import Visual, Colors

class MyVisual(Visual):
    name = "MYVISUAL"
    description = "Cool effect"
    category = "digital"  # automata, nature, digital, art, household, utility

    def reset(self):
        pass

    def update(self, dt):
        self.time += dt

    def draw(self):
        self.display.clear(Colors.BLACK)
        # Draw something cool
```

---

## Display API

```python
display.clear(color)                    # Fill screen
display.set_pixel(x, y, color)          # Single pixel
display.draw_rect(x, y, w, h, color)    # Rectangle
display.draw_line(x0, y0, x1, y1, color)# Line
display.draw_circle(x, y, r, color)     # Circle
display.draw_text_small(x, y, text, color)  # 3x5 pixel font
```

**Colors available:** `Colors.BLACK`, `WHITE`, `RED`, `GREEN`, `BLUE`, `YELLOW`, `CYAN`, `MAGENTA`, `ORANGE`, `PINK`, `GRAY`, `DARK_GRAY`

---

## Hardware Porting

The framework abstracts display and input for easy hardware migration:

### Components Needed
- **64x64 RGB LED Matrix** (HUB75) - ~$40
- **Controller**: Raspberry Pi 3 (development) or Pi Zero 2 W (deployment)
- **5V 4A+ Power Supply**
- **Arcade controls** (joystick + 3 buttons)

### Porting Steps
See [HARDWARE.md](HARDWARE.md) for complete wiring guide and Pi setup instructions.

---

## Design Principles

### 64x64 Constraints
- **Every pixel matters** - Bold, readable shapes
- **High contrast** - Bright colors work best on LED
- **HUD space** - Reserve top 6-8 rows for score/status
- **Sprites** - 3x8 pixel characters work well
- **Text** - 3x5 pixel font (uppercase, numbers, punctuation)

### Performance
- Target **30 FPS**
- Use delta time (`dt`) for consistent speed
- LED matrices handle 60+ FPS but 30 is smooth enough

---

## License

MIT License - do whatever you want with it!

---

## Stats

- **35 Games** across 4 categories
- **44 Visuals** across 6 categories
- **~18,000 lines** of Python
- **79 total items** to explore!
