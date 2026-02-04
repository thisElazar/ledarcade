# Future Development Notes

**Last Updated:** February 3, 2026

This document tracks improvements and missing features identified for future development.

---

## Difficulty Scaling Analysis

Comprehensive review comparing each game's difficulty progression to its original arcade version.

### Excellent - Faithful to Original

| Game | Current Mechanics | Status |
|------|-------------------|--------|
| **Breakout** | Speed tiers (4/12 hits), paddle shrinks after ceiling hit, 2 screens | Authentic 1976 rules |
| **Tetris** | Level-based fall speed, score multiplier per lines | Core difficulty curve intact |
| **Lunar Lander** | Gravity, fuel, pad size, terrain roughness all scale with level | Recently updated |
| **Stack** | Speed increases with score, width shrinks on misalignment | Perfect for genre |
| **Lights Out** | Puzzle complexity scales (more toggles per level) | Good implementation |
| **2048** | Emergent difficulty as board fills | Working as designed |
| **Geometry Dash** | Pattern complexity unlocks progressively | Good learning curve |
| **Arkanoid** | 33 levels, brick types, power-ups, ball speed scales per hit/level | ✅ Verified |
| **Pac-Man** | Ghost AI personalities, frightened 6s→0s, speed +5%/level, release 4s→1s | ✅ Verified |
| **Ms. Pac-Man** | Same as Pac-Man + 25% random ghost turns, 4 cycling mazes | ✅ Verified |
| **Pong** | AI reaction/speed scales with score, ball speed increases | ⏳ Pending verification |
| **Asteroids** | Asteroid speed scales, UFO enemies added | ⏳ Pending verification |
| **Space Invaders** | Enemy speed + UFO mystery ship | ⏳ Pending verification |
| **Dig Dug** | Enemy speed scales, Fygar fire breath | ⏳ Pending verification |
| **Galaga** | Diver count/speed scales, formation oscillates | ⏳ Pending verification |
| **Bomberman** | Enemy speed/count scales, 3 enemy types | ⏳ Pending verification |
| **Night Driver** | Speed increases, oncoming traffic, hairpins, chicanes, road signs | ⏳ Pending verification |

### Good - Has Scaling, Missing Some Features

| Game | Current | Missing from Original |
|------|---------|----------------------|
| **Snake** | Speed increase per food eaten | More aggressive curve, bonus items |
| **Centipede** | Length, speed, mushrooms scale | Spider/flea/scorpion spawn rate scaling |
| **Stick Runner** | Speed scales with score | Rooftop obstacles, gaps |
| **JezzBall** | More atoms per level | Atom SPEED doesn't scale (should!) |
| **TrashBlaster** | Spawn rate decreases over time | Faster movement, hazardous trash |

### Partial - Needs Significant Work

| Game | What's Missing |
|------|----------------|
| **Frogger** | Time limit never decreases, diving turtles don't vary |
| **Donkey Kong** | Speed multiplier calculated but never applied to barrels |
| **Lode Runner** | Enemy speed fixed, no respawning mechanics |

### Weak/Missing - Needs Major Work

| Game | Problem |
|------|---------|
| **Q*bert** | Only spawn rate - missing multi-hop cubes (core mechanic!) |
| **Pipe Dream** | Level variable exists but NEVER increments - no scaling at all |
| **Indy 500** | NO difficulty progression - fixed 3-lap race |
| **SpaceCruise** | NO scaling - all parameters constant |
| **Flappy** | Actually exceeds original (original had constant speed) |

### Two-Player Board Games (No AI Needed)

These are intentionally 2-player only, true to arcade cabinet style:

| Game | Notes |
|------|-------|
| **Chess** | Full rules including castling, en passant, promotion |
| **Checkers** | Forced jumps, multi-jumps, king promotion |
| **Connect 4** | Standard rules, drop animation |
| **Othello** | Full flipping logic, pass detection |
| **Mancala** | Proper sowing, extra turns, captures |
| **Go** | 9x9 board, ko rule, territory scoring with komi |

---

## Priority Fixes - Difficulty Scaling

### Quick Wins (High Impact, Easy Fix)

1. **Pipe Dream** - Add level increment when target reached, scale flow speed and countdown timer
2. ~~**Pong** - Scale AI reaction speed with player score~~ ✓ Done (pending verification)
3. ~~**Asteroids** - Add speed scaling + UFOs~~ ✓ Done (pending verification)
4. **JezzBall** - Add atom speed multiplier per level
5. **Donkey Kong** - Apply the speed_mult that's already calculated but unused

### Medium Effort

1. ~~**Pac-Man** - Decrease frightened duration per level, proper ghost release timing~~ ✓ Done (pending verification)
2. ~~**Invaders** - Add UFO bonus ship (periodic spawn, bonus points)~~ ✓ Done (pending verification)
3. ~~**Dig Dug** - Add enemy speed scaling, implement Fygar fire breath~~ ✓ Done (pending verification)
4. **Q*bert** - Add multi-hop cube mechanics (jump on twice to change)
5. ~~**Arkanoid** - Ball speed increase per brick hit~~ ✓ Done (pending verification)

### Larger Effort

1. **Indy 500** - Add opponent cars, track variety, lap time improvements
2. **SpaceCruise** - Define progression system (distance milestones?)
3. ~~**Night Driver** - Implement oncoming traffic~~ ✓ Done (pending verification)

---

## Game Improvements by Priority

### High Priority (Core Gameplay Missing)

| Game | Missing Feature | Notes |
|------|-----------------|-------|
| ~~**Asteroids**~~ | ~~UFO enemies~~ | ✓ Added (pending verification) |
| **Asteroids** | Hyperspace | Escape mechanic when trapped |
| ~~**Space Invaders**~~ | ~~UFO bonus~~ | ✓ Added (pending verification) |
| ~~**Galaga**~~ | ~~Formation movement~~ | ✓ Added oscillation (pending verification) |
| **Galaga** | Dual-ship firing | Captured ship mechanic incomplete |
| ~~**Pac-Man**~~ | ~~Distinct ghost AI~~ | ✅ COMPLETE - Blinky/Pinky/Inky/Clyde all have proper targeting |
| ~~**Ms. Pac-Man**~~ | ~~Ghost AI~~ | ✅ COMPLETE - Same as Pac-Man + 25% random turns |
| **Donkey Kong** | Fireballs | Additional obstacle type missing |
| **Q*bert** | Multi-hop cubes | Core mechanic - cubes need 2 hops to change |

### Medium Priority (Polish & Variety)

| Game | Missing Feature | Notes |
|------|-----------------|-------|
| **Bomberman** | Bomb kick | Push bombs after placing |
| **Bomberman** | Chain reactions | Explosions should trigger other bombs |
| ~~**Dig Dug**~~ | ~~Fygar fire breath~~ | ✓ Added (pending verification) |
| **Frogger** | Alligators | Water hazard variety |
| **Frogger** | Bonus flies | Point bonuses on logs |
| **Centipede** | Poisoned mushrooms | Scorpion should poison mushrooms |

### Low Priority (Nice to Have)

| Game | Missing Feature | Notes |
|------|-----------------|-------|
| **All games** | Sound effects | Hardware dependent, USB audio needed |
| **Donkey Kong** | Bonus stages | Intermediate levels |
| **Pac-Man** | Bonus fruit | Appears at score milestones |
| **Galaga** | Challenge stages | Bonus rounds |

---

## Common Issues Across Games

### Collision Detection
- Many games use simple bounding box checks
- Edge cases with fast-moving objects
- Corner collisions not always handled

### Progressive Difficulty
- Speed increases should curve, not stay linear
- Later levels become unplayable in some games
- Need proper difficulty caps

### Visual Feedback
- Explosions and particles are basic
- Screen shake implemented but often unused
- Death animations minimal

---

## System-Level TODO

- [ ] Implement difficulty settings menu (Easy/Normal/Hard starting levels)
- [ ] Add pause functionality
- [ ] Consider save states for longer games
- [ ] Profile performance on Pi Zero 2 W for heavy games (Boids, Flux, Attractors)
- [ ] Test all games with actual hardware inputs

---

## Completed Improvements

### Core Systems
- [x] High score system with initials entry
- [x] Game over menu (Play Again / Return to Menu)
- [x] Visual exit via 2-second hold
- [x] Transitions system (10 types) for idle screen
- [x] Idle/attract mode with visual cycling

### Game-Specific
- [x] Breakout - Authentic 1976 mechanics (speed tiers, paddle shrink)
- [x] Arkanoid - 33 NES levels, ball speed scaling per hit/level
- [x] Lunar Lander - Full level progression with scaling difficulty
- [x] Snake - 2x scaling for visibility
- [x] Ball size 2x2 in Breakout/Arkanoid
- [x] Pac-Man - Authentic ghost AI (Blinky/Pinky/Inky/Clyde personalities)
- [x] Ms. Pac-Man - Ghost AI + 25% random turns + 4 cycling mazes

---

## Pending Verification

The following difficulty scaling improvements have been implemented but need play-testing to confirm:

| Game | Changes Made | Status |
|------|--------------|--------|
| **Pong** | AI reaction delay decreases with player score, AI speed increases, ball speed increases per volley | ⏳ Awaiting review |
| **Asteroids** | Asteroid speed scales per wave, added UFO system (small/large, shoots at player, 200-1000 pts) | ⏳ Awaiting review |
| **Space Invaders** | UFO mystery ship with level scaling (speed 25→50, interval 20-30s→10-15s) | ✅ Fixed Feb 2026 |
| **Dig Dug** | Enemy speed scales, Fygar fire breath (capped at 16px range) | ✅ Fixed Feb 2026 |
| **Galaga** | Diver speed capped at 110, bullet speed capped at 120 | ✅ Fixed Feb 2026 |
| **Bomberman** | Enemy scaling + brick density capped at 85% | ✅ Fixed Feb 2026 |
| **Night Driver** | Curve system with physics-balanced caps (already properly capped) | ✅ Reviewed Feb 2026 |

## Recently Verified ✅

| Game | Changes Made | Verified |
|------|--------------|----------|
| **Pac-Man** | Ghost AI (Blinky/Pinky/Inky/Clyde targeting), frightened 6s→0s, speed +5%/level, release 4s→1s | ✅ Feb 2026 |
| **Ms. Pac-Man** | Same ghost AI + 25% random turns at intersections, 4 cycling mazes with different colors | ✅ Feb 2026 |
| **Arkanoid** | 33 NES levels, ball speed +0.5/hit +3.0/level (max 90), silver bricks scale hits | ✅ Feb 2026 |
| **Galaga** | Diver speed capped at 110 px/s, bullet speed capped at 120 px/s | ✅ Feb 2026 |
| **Space Invaders** | UFO speed scales 25→50 with level, spawn interval 20-30s→10-15s | ✅ Feb 2026 |
| **Bomberman** | Brick density capped at 85% (was uncapped, would exceed 100% at level 12) | ✅ Feb 2026 |
| **Dig Dug** | Fygar fire range capped at 16 pixels (was uncapped) | ✅ Feb 2026 |
| **Night Driver** | Reviewed - curve physics already properly balanced with caps | ✅ Feb 2026 |

### Night Driver Details

Major enhancements to Night Driver:

**Speed & Physics:**
- Max speed increased from 80 to 120 units/sec
- Steering scales with speed (2.0 → 3.5) so player can handle faster curves
- Curve push capped at 75% of steering ability (always survivable with skill)
- Physics balanced: hardest curves require anticipation but are never impossible

**Turn Types:**
- Normal curves (base game)
- Hairpin turns (very sharp, appear at 40%+ speed)
- Chicanes/S-curves (quick left-right combo, appear at 50%+ speed)
- Curve intensity scales with speed (1.0x to 2.0x multiplier)

**Oncoming Traffic:**
- 5 vehicle types: Compact, Sedan, SUV, Pickup, Semi/18-wheeler
- Vehicles spawn only in left lane (correct for US driving)
- Vehicle size affects collision width and visual appearance
- Semis have distinct cab/trailer rendering
- Traffic frequency increases with speed

**Road Signs:**
- Warning signs before special turns (hairpin, chicane, curve)
- Decorative signs: speed limit, mile markers, deer crossing, no passing
- Signs render with perspective and appropriate symbols

**Visual Feedback:**
- Turn indicator flashes orange/red for hairpins
- Turn indicator flashes yellow/orange for chicanes
- Normal turns show cyan indicator

---

## Notes

This document was generated from comprehensive code review comparing implementations against classic originals. The difficulty scaling analysis was performed by reviewing each game's update() method and comparing progression mechanics to documented original arcade behavior.

Two-player board games are intentionally kept as 2-player only to maintain the classic arcade cabinet experience where two players would compete at the same machine.

---

*Last updated: February 3, 2026 - Marked Pac-Man/Ms. Pac-Man ghost AI and Arkanoid levels as verified complete.*
