# LED Arcade - Planning & TODO

**Last Updated:** February 5, 2026

Remaining work items. Completed features have been removed - see git history for full roadmaps.

---

## Game Modes (Not Started)

New ways to play beyond single-game sessions.

### Marathon Mode (Priority 1)
Play through multiple games in sequence with combined scoring.
- Select difficulty (5 / 7 / 10 games)
- Show upcoming game + target score
- Award stars: 1 = target met, 2 = 150%, 3 = 200%
- Final tally: total stars, score, time
- Needs per-game target scores defined via playtesting

### Daily Challenge (Priority 2)
Same game + target for everyone each day. One attempt.
- Seed RNG with date, pick game + target
- Track personal streak

### Other Modes (Lower Priority)
- **Gauntlet** - Survive a sequence with one life across all games
- **Speedrun** - Hit score targets across 5 games as fast as possible
- **Duel** - Best of 3/5 across 2-player board games

---

## Attract Mode Additions

Visual cycling works. Game demos exist (42 demos). Not yet integrated:
- Game demo playback during idle (would interleave with visual cycling)
- Leaderboard display between items
- Curated playlists (currently random only)

---

## Difficulty Scaling - Remaining

### Needs Work
| Game | Issue |
|------|-------|
| **Q*bert** | Missing multi-hop cubes (core mechanic - cubes need 2 hops to change) |
| **Pipe Dream** | Level never increments - no scaling at all |
| **Indy 500** | No difficulty progression - fixed 3-lap race |
| **SpaceCruise** | No scaling - all parameters constant |
| **Donkey Kong** | `speed_mult` calculated but never applied to barrels |
| **Frogger** | Time limit never decreases, diving turtles don't vary |
| **JezzBall** | Atom speed doesn't scale (count does) |
| **Lode Runner** | Enemy speed fixed, no respawning |

### Needs Playtesting
Pong, Asteroids (scaling code exists, untested on hardware)

---

## Missing Game Features

### High Priority
| Game | Missing |
|------|---------|
| **Q*bert** | Multi-hop cubes (core mechanic) |
| **Donkey Kong** | Fireballs (additional obstacle) |
| **Galaga** | Dual-ship firing (captured ship mechanic) |
| **Asteroids** | Hyperspace escape mechanic |

### Medium Priority
| Game | Missing |
|------|---------|
| **Bomberman** | Bomb kick, chain reactions |
| **Frogger** | Alligators, bonus flies |
| **Centipede** | Poisoned mushrooms from scorpion |

### Low Priority
| Game | Missing |
|------|---------|
| **Pac-Man** | Bonus fruit |
| **Galaga** | Challenge stages |
| **Donkey Kong** | Bonus stages |
| **All games** | Sound effects (needs USB audio) |

---

## Art Visuals - Expansion Candidates

Currently 5 art visuals. Candidates for future:

| Painting | Artist | Animation Idea |
|----------|--------|----------------|
| Nighthawks | Hopper | Flickering interior lights |
| Persistence of Memory | Dali | Melting clock animation |
| Campbell's Soup Can | Warhol | Cycling through flavors |
| American Gothic | Wood | Two figures, recognizable pose |
| Girl with Pearl Earring | Vermeer | Portrait profile, turban glow |

---

## LED Color Contrast (Low Priority)

Some games use muddy browns with poor LED visibility:
- Donkey Kong (DK sprite, barrels)
- Dig Dug (dirt colors)
- Lode Runner (rope color)
- Frogger (logs, rocks)
- Geometry Dash (dark grays)
- Bomberman (bomb nearly invisible)

---

## System-Level TODO

- [ ] Difficulty settings menu (Easy/Normal/Hard starting levels)
- [ ] Pause functionality
- [ ] Profile heavy visuals on Pi Zero 2 W (Boids, Flux, Attractors)
- [ ] Gamma correction for LED color accuracy
- [ ] Auto-start systemd service on Pi boot
