# LED Arcade - Feature Planning

**Created:** January 28, 2026
**Last Updated:** February 3, 2026
**Status:** Core features complete, difficulty scaling complete, game modes not started

This document outlines planned features for the LED Arcade system, tracking what's implemented and what remains.

---

## 1. Transitions ✅ COMPLETE

### Status: Fully Implemented

10 transition effects implemented in `transitions.py`:

| Transition | Description |
|------------|-------------|
| FadeToBlack | Fade out → black hold → fade in |
| RandomDissolve | Random pixels flip to new frame |
| DitherDissolve | Ordered 4x4 Bayer dither pattern reveal |
| HorizontalWipe | Left-to-right reveal |
| VerticalWipe | Top-to-bottom reveal |
| IrisWipe | Circular reveal from center |
| CRTOff | Classic TV turn-off (vertical collapse → horizontal → expand) |
| Scanline | Row-by-row with bright scan line |
| Pixelate | Mosaic effect in/out |
| Blinds | Vertical blinds flip with staggered timing |

### Features
- `TransitionManager` class handles capture/playback
- Persistent settings to enable/disable individual transitions
- Random selection from enabled transitions
- Used during idle screen visual cycling

### Location
- `transitions.py` - All transition classes and manager
- `settings.py` - Persistence for enabled transitions
- `run_arcade.py:538-541` - Integration with idle screen

---

## 2. Attract/Idle Mode ✅ PARTIAL

### Status: Visual cycling implemented, game demos not started

### What's Implemented

| Feature | Status | Location |
|---------|--------|----------|
| Idle detection | ✅ | 60s timeout on menu |
| Visual showcase | ✅ | Random weighted selection |
| Visual cycling | ✅ | 30s per visual with transitions |
| Category weighting | ✅ | Skips utility, weights by category |
| Instant return | ✅ | Any input → menu immediately |

### Implementation Details
- `_pick_idle_visual()` in `run_arcade.py:382-406`
- Uses `AllVisuals.CATEGORY_WEIGHTS` for weighted random
- Preloads new visual before transition to avoid hitches
- Transitions between visuals using `TransitionManager`

### What's NOT Implemented

| Feature | Status | Notes |
|---------|--------|-------|
| Game demos/title cards | ❌ | Would need `demo_update()` per game |
| Leaderboard display | ❌ | Show top scores across games |
| Splash screens | ❌ | "LED ARCADE" branding |
| Curated playlist | ❌ | Currently random only |

### Original Timing Spec (for future reference)

| Content Type | Duration |
|--------------|----------|
| Visual showcase | 15-30s (currently 30s) |
| Game demo | 10-15s |
| Leaderboard | 5-10s |
| Splash screen | 3-5s |

---

## 3. Game Modes ❌ NOT STARTED

### Overview
New ways to play beyond single-game sessions. None implemented yet.

### Mode: Marathon (PRIORITY 1)

**Concept:** Play through multiple games in sequence, combined scoring.

**Structure:**
1. "MARATHON MODE" splash
2. Select difficulty (determines game count: 5 / 7 / 10)
3. Show upcoming game + target score
4. Play until game over OR target reached
5. Award stars: 1 = target met, 2 = 150%, 3 = 200%
6. Brief results screen (2-3 seconds)
7. Transition to next game
8. Final tally: total stars, total score, total time

**Game Selection:**
- Exclude 2-player games
- Weight toward games with clear score mechanics
- Themed packs possible:
  - "Shooter Pack" - Invaders, Galaga, Asteroids, Centipede
  - "Puzzle Pack" - Tetris, 2048, Pipe Dream, Lights Out
  - "Classics Pack" - Pac-Man, Snake, Breakout, Frogger

**Target Scores:**
- Need to define per-game targets (easy/medium/hard)
- Could be stored in game class: `Game.marathon_targets = {'easy': 300, 'medium': 500, 'hard': 800}`

### Mode: Daily Challenge (PRIORITY 2)

**Concept:** Same game + target for everyone each day. One attempt.

**Structure:**
1. Seed RNG with today's date
2. Pick game + target score
3. One attempt only (no retries)
4. Show result: achieved / missed
5. Track personal history

**Nice touches:**
- Show streak of consecutive days played
- "Yesterday's challenge was [game]"

### Mode: Gauntlet (PRIORITY 3)

**Concept:** Survive a sequence with one life across all games.

**Structure:**
1. Random sequence of 5-10 games
2. Single life/attempt per game
3. Die once = run over
4. Score = games survived + partial score on death

### Mode: Speedrun (PRIORITY 4)

**Concept:** Hit score targets across multiple games as fast as possible.

**Structure:**
1. Fixed sequence of 5 games with targets
2. Timer counts up continuously
3. Must hit target before moving to next game
4. Final time = your score
5. Leaderboard by fastest time

### Mode: Duel (PRIORITY 5)

**Concept:** Best of 3/5 across 2-player board games.

**Structure:**
1. Players pick game count (3 or 5)
2. Alternate who picks the game (or random)
3. Play each board game to completion
4. Winner gets a point
5. First to majority wins

**Works with:** Chess, Checkers, Connect 4, Othello, Go, Mancala

---

## 4. Art Visuals (Expansion) ⏳ PARTIAL

### Status: 3 implemented, more candidates identified

### Currently Implemented

| Visual | Artist | Animation |
|--------|--------|-----------|
| Starry Night | Van Gogh | Swirling sky particles |
| Water Lilies | Monet | Rippling water effect |
| Mondrian | Mondrian | Color-cycling blocks |

### Candidates for Future

| Painting | Artist | Why It Works at 64x64 |
|----------|--------|----------------------|
| The Great Wave | Hokusai | Strong silhouette, iconic shape |
| The Scream | Munch | Simple figure, swirling background |
| American Gothic | Wood | Two figures, recognizable |
| Girl with Pearl Earring | Vermeer | Portrait profile, turban, earring |
| Persistence of Memory | Dali | Melting clocks, surreal shapes |
| Nighthawks | Hopper | Diner window glow, strong composition |
| Campbell's Soup Can | Warhol | Graphic, could cycle flavors |

### Animation Ideas

| Painting | Animation |
|----------|-----------|
| Great Wave | Foam particles, boat bobbing |
| The Scream | Pulsing background lines |
| Nighthawks | Flickering interior lights |
| Soup Can | Cycling through flavors |

---

## 5. Difficulty Scaling ✅ MOSTLY COMPLETE

### Status: Most games have proper scaling with caps for playability

### Fully Implemented & Verified

| Game | Scaling Features |
|------|------------------|
| **Pac-Man** | Ghost speed +5%/level (max 40%), frightened duration 6s→0s, release interval 4s→1s |
| **Ms. Pac-Man** | Same as Pac-Man + 25% random ghost turns |
| **Arkanoid** | Ball speed +3/level + 0.5/brick hit (max 90), silver brick hits scale |
| **Tetris** | Drop speed increases per level |
| **Breakout** | Ball speed increases |
| **Galaga** | Diver speed capped at 110 px/s, bullet speed capped at 120 px/s |
| **Space Invaders** | UFO speed 25→50, spawn interval 20-30s→10-15s |
| **Bomberman** | Enemy speed/count scales, brick density capped at 85% |
| **Dig Dug** | Enemy speed scales, Fygar fire capped at 16 pixels |
| **Night Driver** | Curve physics balanced, hairpins/chicanes/traffic all scale with caps |

### Needs Play-Testing

- Pong (AI reaction + ball speed - code exists, untested)
- Asteroids (speed + UFO system - code exists, untested)

### Needs Work

| Game | Issue |
|------|-------|
| Frogger | Traffic/log speed scaling partial |
| Q*bert | Multi-hop cubes not implemented |
| Pipe Dream | No difficulty curve |
| Indy 500 | No difficulty curve |
| Donkey Kong | Fireballs not implemented |

---

## 6. Ghost AI Personalities ✅ COMPLETE

### Status: Fully implemented for both Pac-Man and Ms. Pac-Man

Each ghost has authentic arcade AI in `get_ghost_target()`:

| Ghost | Color | Behavior |
|-------|-------|----------|
| **Blinky** | Red | Directly targets Pac-Man's current tile |
| **Pinky** | Pink | Targets 4 tiles ahead of Pac-Man's direction |
| **Inky** | Cyan | Vector from Blinky through point 2 tiles ahead, doubled |
| **Clyde** | Orange | Targets Pac-Man when >8 tiles away; retreats to scatter corner when closer |

### Ms. Pac-Man Addition
- 25% chance of random turn at intersections (line 656-658 in mspacman.py)
- Makes ghosts less predictable than original Pac-Man

### Location
- `games/pacman.py:492-517` - `get_ghost_target()`
- `games/mspacman.py:710-735` - `get_ghost_target()`

---

## Implementation Priority (Updated)

| Priority | Feature | Status | Effort | Impact |
|----------|---------|--------|--------|--------|
| ~~1~~ | ~~Fade transitions~~ | ✅ DONE | - | - |
| ~~2~~ | ~~Attract mode (visuals)~~ | ✅ DONE | - | - |
| ~~3~~ | ~~Difficulty scaling~~ | ✅ DONE | - | - |
| 1 | Marathon mode | ❌ | Medium | High - replayability |
| 2 | Daily challenge | ❌ | Low | Medium - engagement |
| 3 | Attract mode (game demos) | ❌ | Medium | Medium |
| 4 | Art visuals expansion | ❌ | Low (per visual) | Medium |
| 5 | Other game modes | ❌ | Medium | Low |

---

## Open Questions

1. **Marathon targets:** Need to playtest and define reasonable score targets per game.

2. **Art visual count:** How many paintings to target? Current: 3. Goal: 6-10?

3. **Daily challenge persistence:** Store locally only, or eventually add network leaderboard?

4. **Attract game demos:** Which games are most visually interesting for auto-play? Candidates:
   - Pac-Man (iconic, easy AI)
   - Tetris (satisfying to watch)
   - Asteroids (action-packed)
   - Snake (simple AI)

---

*Last updated: February 3, 2026*
