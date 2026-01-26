# LED Arcade Game Roadmap

**STATUS: ALL SPRINTS COMPLETE ✅**

Games implemented, organized by sprint theme. All 18 games from Sprints 1-8 are now playable, plus bonus games (Q*bert, Bomberman).

## Constraints
- **Display**: 64x64 pixel grid
- **Input**: 1 joystick (4-way), 1 button (action only)
- **2-Player**: Turn-based with shared controller (no AI opponents)

---

## Sprint 1: 2-Player Board Games
Classic board games for two human players taking turns.

### Connect 4
- **Grid**: 7 columns x 6 rows (chunky pieces)
- **Input**: Left/Right to choose column, Action to drop
- **Features**: Drop animation, win line highlight

### Checkers
- **Grid**: 8x8 board (6-7px squares)
- **Input**: D-pad to move cursor, Action to select/place, show valid moves
- **Features**: King promotion, mandatory jumps, multi-jump chains

### Othello/Reversi
- **Grid**: 8x8 board (5-6px discs)
- **Input**: D-pad cursor, Action to place
- **Features**: Flip animation, valid move indicators, score display

---

## Sprint 2: Puzzle Games
Single-player brain teasers.

### 2048
- **Grid**: 4x4 tiles (~14px each with gaps)
- **Input**: D-pad to slide all tiles
- **Features**: Merge animations, color progression, high score

### Lights Out
- **Grid**: 5x5 default (can offer sizes)
- **Input**: D-pad cursor, Action to toggle
- **Features**: Toggle affects adjacent cells, level progression, move counter

### Pipe Dream
- **Grid**: 7x7 playfield with queue area
- **Input**: D-pad to move, Action to place pipe from queue
- **Features**: Flowing liquid animation, score multiplier for length

---

## Sprint 3: Arcade Driving
Racing and driving games with distinct styles.

### Night Driver
- **Grid**: First-person perspective, road posts converging toward center
- **Input**: Left/Right to steer
- **Features**: Increasing speed, night aesthetic (white posts on black), score by distance

### Lunar Lander
- **Grid**: Terrain at bottom, lander descending
- **Input**: Action for thrust, Left/Right for lateral movement
- **Features**: Fuel gauge, velocity indicator, multiple landing pads with point values

### Indy 500
- **Grid**: Top-down oval or circuit track
- **Input**: D-pad to steer, Action for gas
- **Features**: Lap counter, time trials, track variety

---

## Sprint 4: Endless/Modern Games
One-button and endless runner style games.

### Canabalt / Endless Runner
- **Grid**: Side-scrolling cityscape, auto-run right
- **Input**: Action to jump (hold for higher)
- **Features**: Procedural buildings, increasing speed, distance score, obstacles

### Stack
- **Grid**: Centered tower, blocks swinging in from side
- **Input**: Action to drop block
- **Features**: Blocks shrink if misaligned, perfect drops streak, tower rises

### Geometry Dash (Simplified)
- **Grid**: Side-scrolling obstacle course
- **Input**: Action to jump (timing-based)
- **Features**: Spike obstacles, rhythm patterns, level-based or endless

---

## Sprint 5: Classic Shooters
Expanding the shooter genre beyond Space Invaders.

### Galaga
- **Grid**: Full 64x64 play area
- **Input**: Left/Right to move, Action to fire
- **Features**: Enemy formations, dive patterns, ship capture/rescue, bonus stages

### Centipede
- **Grid**: Mushroom field + player area at bottom
- **Input**: Full D-pad movement, Action to fire
- **Features**: Segmented centipede, mushrooms, spider, flea, scorpion

---

## Sprint 6: Strategy Depth
Games with deeper strategic thinking.

### Mancala
- **Grid**: 6 pits per side + 2 stores, horizontal layout
- **Input**: D-pad to select pit, Action to sow seeds
- **Features**: Seed animation (stones dropping), capture highlights

### Go (9x9)
- **Grid**: 9x9 beginner board (~6px per intersection)
- **Input**: D-pad cursor, Action to place stone
- **Features**: Capture detection, territory scoring, ko rule, pass option

---

## Sprint 7: Digging Games
Underground and tunneling mechanics.

### Dig Dug
- **Grid**: Underground tunnels, full 64x64
- **Input**: D-pad to dig/move, Action to pump
- **Features**: Tunnel creation, pump enemies until pop, dropping rocks, Pooka & Fygar enemies

### Lode Runner
- **Grid**: Platform levels with ladders
- **Input**: D-pad to move, Action to dig holes
- **Features**: Trap enemies in holes, collect gold, reach exit

---

## Sprint 8: Platforming (Capstone)
The most complex games, saved for last.

### Donkey Kong
- **Grid**: 4 screens (Girders, Conveyors, Elevators, Rivets)
- **Input**: D-pad to move/climb, Action to jump
- **Features**: Jump physics, barrel AI, hammer powerup
- **Sprites**: Mario ~5px, DK ~10px, barrels ~4px

---

## Technical Notes

### Shared Patterns to Extract
- **Board game cursor**: Reuse across Checkers/Othello/Go
- **Turn indicator**: "P1"/"P2" display component
- **Grid-based boards**: 8x8 and variable size rendering
- **Piece animations**: Drop, flip, capture effects

### New Mechanics Needed
- **Pump/charge action**: Hold button for Dig Dug
- **Gravity/physics**: For platformers, Connect 4 drops, Lunar Lander
- **Flow simulation**: For Pipe Dream liquid
- **Flood fill**: For Go capture detection
- **Perspective rendering**: For Night Driver road

### Visual Polish Ideas
- Win celebrations with flashing/particles
- Piece drop shadows
- Smooth cursor movement
- Color themes per game
