# LED Arcade - Development Roadmap

## Overview
This document tracks the development of the 64x64 LED matrix arcade system, including implemented features, known issues, and future enhancements.

---

## Implemented Games (January 2025)

### New Games Added

#### 1. Flappy Bird (`games/flappy.py`)
- Tap-to-flap mechanics with gravity physics
- Scrolling pipe obstacles with random gap heights
- Progressive difficulty (speed increases with score)
- Ground and ceiling collision
- Bird wing animation

**Controls:** Space to flap, Escape for menu

#### 2. JezzBall (`games/jezzball.py`)
- Bouncing atoms (2x2 pixels) with physics
- Wall building from cursor position (horizontal/vertical)
- 75% fill win condition per level
- Progressive difficulty (more atoms per level)
- Lives system - lose life if atom hits wall being built
- Flood fill algorithm to detect and fill empty regions

**Controls:** Arrows to move cursor, Space + direction to build walls

#### 3. Frogger (`games/frogger.py`)
- 5 traffic lanes with cars at varying speeds
- 5 water lanes with logs and turtles
- Riding mechanics (move with logs/turtles)
- Diving turtles that become unsafe
- 5 home slots to fill per level
- Timer countdown with bonus points

**Controls:** Arrows to hop, Escape for menu

#### 4. Pac-Man (`games/pacman.py`)
- Custom 21x19 tile maze (3px per tile) designed for 64x64 display
- 4 ghosts with unique AI behaviors:
  - **Blinky (red):** Direct chase
  - **Pinky (pink):** Targets 4 tiles ahead
  - **Inky (cyan):** Complex vector-based targeting
  - **Clyde (orange):** Chase when far, scatter when close
- Power pellets with frightened mode
- Ghost house with timed release
- Tunnel wrap on sides
- Turn assist for smooth corner navigation

**Controls:** Arrows to set direction, Escape for menu

---

## Technical Improvements

### Pac-Man Collision & Movement System
The Pac-Man implementation required significant iteration to feel right on a 64x64 grid:

1. **Tile-based collision detection**
   - `tile_passable()` function for clean wall checks
   - Separate checks for current tile and tile ahead

2. **Turn assist system**
   - Generous turn window (0.6 tiles in travel direction, 0.3 perpendicular)
   - Checks current tile AND one tile back for valid turns
   - Auto-snaps to lane center when turning
   - Queued directions persist until executable

3. **Ghost pathfinding**
   - Tile-center-based decision making
   - Always finds valid direction (allows reverse if stuck)
   - Proper ghost house entry/exit logic

4. **Maze design considerations**
   - Original 28x31 maze at 2px/tile was too cramped
   - Final: 21x19 maze at 3px/tile = 63x57 pixels
   - All 192 dots verified reachable via flood fill
   - Ghost house positioned in center rows 5-10

---

## Known Issues & Limitations

### Current
- Ghost release timing could be more dynamic (currently fixed 4-second intervals)
- Pac-Man death animation is minimal
- No sound effects (hardware dependent)

### Display Constraints
- 64x64 pixel limit requires simplified graphics
- Text rendering limited to 3x5 pixel font
- Complex sprites must be 2-3 pixels max

### LED Color Contrast (Needs Attention)
Several games use muddy browns, near-black, or washed-out pastels that have poor visibility on the LED matrix. Bold saturated colors with clear value separation work best.

**Fixed:**
- 2048 — replaced pastel cream/tan mobile palette with distinct saturated colors
- Chess — black pieces changed to dark red, board squares adjusted
- Checkers — P2 white pieces changed to blue, board squares adjusted
- Othello — P1 black pieces changed to dark red for green board contrast
- Go — brighter grid lines, star points, and black stones

**Remaining (low priority):**
- Donkey Kong — DK and barrels use muddy browns (139,90,43 / 120,70,35)
- Dig Dug — dirt colors (139,90,43 / 100,65,30) are muddy browns
- Lode Runner — rope color (139,90,43) same muddy brown
- Frogger — logs use muddy brown, rocks are similar dark grays
- Geometry Dash — multiple near-identical dark grays for ground/platforms
- Bomberman — bomb color (20,20,20) nearly invisible, wall/floor similar brightness

---

## Discussed But Not Implemented

### Pac-Man Enhancements
- **Fruit bonuses:** Spawn collectible fruit for bonus points
- **Level variations:** Different maze layouts per level
- **Ghost personality tweaks:** More pronounced behavioral differences
- **Cutscenes:** Brief animations between levels (like original)
- **High score persistence:** Save to file

### JezzBall Enhancements
- **Two-way wall building:** Walls that grow in both directions simultaneously (partially implemented)
- **Power-ups:** Speed boost, temporary invincibility, freeze atoms
- **Atom splitting:** Atoms that divide when areas get small enough

### Frogger Enhancements
- **Alligators:** Hazards in water that eat frog
- **Snake on grass:** Moving hazard on safe zones
- **Fly bonus:** Catch flies on logs for points
- **Lady frog:** Escort bonus character home

### Flappy Bird Enhancements
- **Day/night cycle:** Visual variety
- **Medals:** Bronze/silver/gold based on score
- **Leaderboard:** Track best scores

### General System
- **Settings menu:** Adjust difficulty, sound, controls
- **Pause functionality:** Pause mid-game
- **Controller support:** USB gamepad input
- **Network play:** Two-player over network

---

## Future Game Ideas

### Implemented ✅
1. **Space Invaders** - Already exists
2. **Galaga** - Formation-based shooter ✅
3. **Centipede** - Segmented enemy movement ✅
4. **Dig Dug** - Tunnel digging mechanics ✅
5. **Q*bert** - Isometric cube hopping ✅
6. **Bomberman** - Grid-based bomb placement ✅
7. **Lode Runner** - Platform digging ✅
8. **Donkey Kong** - Multi-screen platformer ✅

### Remaining Ideas
9. **Boulder Dash** - Falling rocks puzzle
10. **Sokoban** - Push-box puzzles
11. **Joust** - Flying combat
12. **Defender** - Scrolling shooter

---

## Architecture Notes

### Game Structure
All games inherit from `Game` base class in `arcade.py`:
```python
class Game(ABC):
    name: str           # Menu display name
    description: str    # Short description

    def reset(self)     # Initialize/restart game
    def update(self, input_state, dt)  # Game logic
    def draw(self)      # Render to display
```

### Adding New Games
1. Create `games/yourgame.py`
2. Implement `Game` subclass with `reset()`, `update()`, `draw()`
3. Import and add to `ALL_GAMES` list in `games/__init__.py`

### Input System
```python
input_state.up/down/left/right  # Direction (held)
input_state.action_l            # Space (pressed this frame)
input_state.action_l_held       # Space (held)
input_state.action_r            # Z (pressed this frame)
input_state.action_r_held       # Z (held)
# Hold either button 2 sec to exit/return to menu
```

### Display System
```python
display.clear(color)
display.set_pixel(x, y, color)
display.draw_rect(x, y, w, h, color)
display.draw_line(x0, y0, x1, y1, color)
display.draw_text_small(x, y, text, color)  # 3x5 font
```

---

## Hardware Migration Notes

When moving from PyGame (desktop) to actual LED matrix:

1. **Display abstraction** - `Display` class methods map to matrix library
2. **Input abstraction** - `InputHandler` maps to GPIO/hardware buttons
3. **Timing** - May need adjustment for matrix refresh rate
4. **Colors** - RGB values may need gamma correction for LEDs
5. **Frame rate** - 30 FPS target, may need optimization

---

## Version History

### v1.0 (January 2025)
- Initial release with 6 games: Snake, Pong, Breakout, Invaders, Tetris, Asteroids

### v1.1 (January 2025)
- Added 4 new games: Flappy Bird, JezzBall, Frogger, Pac-Man
- Improved collision systems
- Turn assist for Pac-Man
- Custom maze design for small display

### v1.2 (January 2025)
- Added Sprint 1-8 games from GAME_ROADMAP:
  - Board games: Connect 4, Checkers, Othello
  - Puzzles: 2048, Lights Out, Pipe Dream
  - Driving: Night Driver, Lunar Lander, Indy 500
  - Endless: Stick Runner, Stack, Geometry Dash
  - Shooters: Galaga, Centipede
  - Strategy: Mancala, Go (9x9)
  - Digging: Dig Dug, Lode Runner
  - Platforming: Donkey Kong
- Added bonus games: Q*bert, Bomberman, Arkanoid
- Total: 35 games

---

## Contributing

When adding or modifying games:
1. Test at 30 FPS with `python main.py`
2. Verify all game states work (playing, game over, restart)
3. Check collision edge cases
4. Ensure controls are documented in file header
5. Update `games/__init__.py` imports and `ALL_GAMES` list
