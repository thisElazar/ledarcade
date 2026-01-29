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

## Game Categories (35 games)
- `arcade` - Classic arcade machines (17): Pac-Man, Galaga, Invaders, Tetris, etc.
- `retro` - Computer/console classics (6): Arkanoid, JezzBall, Pipe Dream, etc.
- `modern` - Mobile-era games (6): Flappy, 2048, Geometry Dash, etc.
- `2_player` - Turn-based multiplayer (6): Chess, Go, Checkers, etc.

## Visual Categories (44 visuals)
- `automata` - Cellular automata & agents (11): Life, Boids, Slime, Hodge, etc.
- `nature` - Natural phenomena (7): Fire, Plasma, Starfield, Weather, etc.
- `digital` - Math/computer viz (13): Matrix, Rotozoom, Copper Bars, etc.
- `art` - Famous paintings (3): Starry Night, Water Lilies, Mondrian
- `household` - Domestic nostalgia (5): DVD, Lava Lamp, Solitaire, Cat, etc.
- `utility` - Functional displays (5): Clock, Sysinfo, Settings, etc.

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
