# LED Arcade - Project Context

## Overview
A retro arcade system running on a Raspberry Pi 3 with a 64x64 RGB LED matrix (HUB75). Contains games and visualizations designed for the low-resolution display.

## Hardware Setup
- **Display**: 64x64 RGB LED matrix panel (HUB75 interface)
- **Controller**: Raspberry Pi 3 at `thiselazar@arcade.local`
- **Input**: Keyboard over SSH (arrows/WASD, Space, Z; hold button 2s to exit)
- **GPIO**: Custom "led-arcade" hardware mapping (see HARDWARE.md)

## Development Workflow

### Deploy to Pi
After making changes on laptop:
```bash
# Stage and commit
git add <files>
git commit -m "Description"

# Push and sync Pi
git push && ssh thiselazar@arcade.local "cd ~/led-arcade && git pull"
```

### Run on Pi
```bash
ssh thiselazar@arcade.local
cd ~/led-arcade
sudo python3 run_hardware.py
```

### Run locally (emulator)
```bash
python3 run_arcade.py
```

## Project Structure
- `games/` - Game implementations (extend `Game` class)
- `visuals/` - Visual/screensaver implementations (extend `Visual` class)
- `arcade.py` - Core classes: Game, Visual, Display, Colors, InputState
- `hardware.py` - Hardware display driver for LED matrix
- `run_arcade.py` - PyGame emulator launcher
- `run_hardware.py` - Hardware launcher for Pi
- `catalog.py` - Category system for menu organization

## Game Categories (53 games)
- `arcade` - Classic arcade machines (17): Pac-Man, Galaga, Invaders, Tetris, BurgerTime, etc.
- `retro` - Computer/console classics (6): Arkanoid, JezzBall, Pipe Dream, etc.
- `modern` - Mobile-era games (7): Flappy, 2048, Geometry Dash, Agar.io, etc.
- `bar` - Bar games (6): Bowling, Darts, Pinball, Pool, Shuffleboard
- `toys` - Toys & puzzles (6): Bop It, Fifteen Puzzle, Mastermind, Rush Hour, Simon, Tetris
- `2_player` - Turn-based multiplayer (6): Chess, Go, Checkers, etc.
- `shuffle` - Playlist modes (6): AllGames, ArcadeMix, QuickPlay, Shooters, Puzzle, Classics

## Visual Categories (142 files, 110+ unique effects)
- `automata` - Cellular automata & agents (11): Life, Boids, Slime, Hodge, etc.
- `art` - Famous paintings (5): Starry Night, Water Lilies, Mondrian, Great Wave, Scream
- `demos` - AI-controlled gameplay demos (43)
- `digital` - Math/computer viz (13): Matrix, Rotozoom, Copper Bars, etc.
- `household` - Domestic nostalgia (5): DVD, Lava Lamp, Solitaire, Cat, etc.
- `mechanics` - Historical machines (21): Swiss Watch, Locomotive, Orrery, Curta, etc.
- `outdoors` - Natural phenomena (7): Fire, Plasma, Starfield, Weather, Aurora, etc.
- `road_rail` - Traffic simulations (8): Highway, Intersection, BML, etc.
- `science` - Scientific viz (28): Turing patterns, Orbits, EM fields, Fluid, Neurons, DNA, Spectroscope, etc.
- `sprites` - Game character animations (9): Mario, Sonic, Link, Yoshi, etc.
- `superheroes` - Comic characters (4): Spidey, Batman, Green Lantern
- `titles` - Wonder Cabinet branded title screens (52)
- `visual_mix` - Curated slideshow playlists (10): All Visuals, Chill, Energy, etc.
- `utility` - Functional displays (9): Clock, Settings, Test Pattern, About, Shutdown

## Design Guidelines
- 64x64 pixel canvas - keep visuals simple and bold
- Small font is 4px wide per character
- Text alignment: left-align at x=2 (don't attempt centering)
- Colors: use bright, saturated colors for visibility
- Game over screens: use game's `draw_game_over()` for 2-player games

## Known Constraints
- CPU-intensive visuals (Boids, Slime, Rug) can starve input handling
- No # symbol in text (illegible at this resolution)
- Pi must run with `sudo` for LED matrix access
