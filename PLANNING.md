# LED Arcade - Feature Planning

**Created:** January 28, 2026
**Status:** Planning phase - no implementations yet

This document outlines planned features for the LED Arcade system, focusing on polish, presentation, and gameplay depth.

---

## 1. Attract Mode

### Overview
After idle time on the menu, the system comes alive - showcasing games, cycling visuals, and displaying high scores. Classic arcade authenticity. Any input returns to menu.

### Timing Configuration

| Parameter | Proposed Value | Notes |
|-----------|----------------|-------|
| Idle threshold | 60 seconds | Time on menu before attract starts |
| Visual duration | 15-30 seconds | How long each visual runs |
| Game demo duration | 10-15 seconds | How long each game demo runs |
| Leaderboard duration | 5-10 seconds | High score display time |
| Splash screen duration | 3-5 seconds | "LED ARCADE" branding |

### Content Types

| Type | Description | Duration |
|------|-------------|----------|
| **Splash screen** | "LED ARCADE" logo/animation | 3-5s |
| **Visual showcase** | Run a visual effect | 15-30s |
| **Game demo** | Auto-play or title card | 10-15s |
| **Leaderboard** | Top scores across games | 5-10s |

### Sequencing

**Recommended approach: Weighted random**
- 50% visuals (they're designed to look good passively)
- 25% game demos/title cards
- 15% leaderboards
- 10% splash screens

**Alternative: Curated playlist**
- Hand-picked sequence that loops
- Ensures variety and pacing
- More work to maintain

### Game Demos

**Options (in order of complexity):**

1. **Title card only** (simplest)
   - Show game name, description, controls hint
   - Maybe a static screenshot or key frame
   - No gameplay simulation needed

2. **Simple AI playback**
   - Games implement `demo_update()` method
   - Basic bot logic: Snake follows food, Asteroids shoots randomly, etc.
   - Good balance of effort vs. impact

3. **Recorded inputs** (most complex)
   - Capture a good run, replay the inputs
   - Most authentic, but fragile if game logic changes

**Recommended:** Start with title cards, add simple AI for select games later.

### Return Behavior

**Options:**
1. Any input → instant return to menu (recommended - feels responsive)
2. Any input → return with showcased item highlighted (fancier but maybe confusing)

### Implementation Notes

- Create `AttractMode` class that manages the sequence
- Store last user input timestamp in main loop
- AttractMode receives list of all games/visuals to pull from
- Each item type needs a `duration` hint or uses defaults
- Transition system (see below) handles smooth switching

---

## 2. Fade Transitions

### Overview
Smooth visual transitions between screens instead of hard cuts. Adds polish and arcade feel.

### Transition Styles

| Style | Description | Complexity | Feel |
|-------|-------------|------------|------|
| **Fade to black** | Brightness ramps down → black → ramps up | Low | Clean, modern |
| **Crossfade** | Old screen fades while new fades in | Medium | Smooth |
| **Horizontal wipe** | Line sweeps across revealing new screen | Low | Classic arcade |
| **Vertical wipe** | Line sweeps down | Low | Classic |
| **Iris** | Circle shrinks to center, expands from center | Medium | Very retro (Mario-style) |
| **Pixel dissolve** | Random pixels flip to new screen | Medium | Playful chaos |
| **Scanlines** | Reveal line-by-line (CRT style) | Low | Authentic |

### Recommended Transitions by Context

| Transition Point | Style | Duration |
|------------------|-------|----------|
| Menu → Game | Fade to black | 0.3s |
| Game → Game Over | Fade to black | 0.4s |
| Game Over → Menu | Fade to black | 0.3s |
| Menu → Visual | Crossfade | 0.4s |
| Visual → Visual (attract) | Crossfade or dissolve | 0.5s |
| Attract → Menu | **Instant** | 0s (responsive feel) |

### Implementation Approach

```
TransitionManager:
  - capture_frame() → stores current display buffer
  - start_transition(type, duration, callback)
  - update(dt) → animates transition
  - draw() → renders transition frame
  - is_active → bool
```

**Key principles:**
- Transition manager sits between game loop and display
- Captures "before" frame, knows "after" target
- Animates blend/wipe/etc. over duration
- Calls callback when complete
- Duration: 0.3s - 0.5s feels snappy but noticeable
- Easing: Linear is fine; ease-in-out is smoother

### Priority

Start with **fade to black** - simplest, works everywhere, looks good. Add variety later if desired.

---

## 3. Game Modes

### Overview
New ways to play beyond single-game sessions. Adds replayability and variety.

### Mode: Marathon

**Concept:** Play through multiple games in sequence, combined scoring.

**Structure:**
1. "MARATHON MODE" splash
2. Select difficulty (determines game count: 5 / 7 / 10)
3. Show upcoming game + target score
4. Play until game over OR target reached
5. Award stars: ⭐ = target met, ⭐⭐ = 150%, ⭐⭐⭐ = 200%
6. Brief results screen (2-3 seconds)
7. Transition to next game
8. Final tally: total stars, total score, total time

**Game Selection:**
- Exclude 2-player games
- Weight toward games with clear score mechanics
- Could offer themed packs:
  - "Shooter Pack" - Invaders, Galaga, Asteroids, Centipede
  - "Puzzle Pack" - Tetris, 2048, Pipe Dream, Lights Out
  - "Classics Pack" - Pac-Man, Snake, Breakout, Frogger

**Target Scores:**
- Need to define per-game targets (easy/medium/hard)
- Based on typical skill levels
- Could be stored in game class: `Game.marathon_target = 500`

### Mode: Gauntlet

**Concept:** Survive a sequence with one life across all games.

**Structure:**
1. Random sequence of 5-10 games
2. Single life/attempt per game
3. Die once = run over
4. Score = games survived + partial score on death
5. High tension, high stakes

**Good for:** Experienced players wanting a challenge.

### Mode: Daily Challenge

**Concept:** Same game + target for everyone each day. One attempt.

**Structure:**
1. Seed RNG with today's date
2. Pick game + target score
3. One attempt only (no retries)
4. Show result: achieved / missed
5. Track personal history: "Jan 28: Snake, Target 50, You: 73 ⭐⭐"

**Nice touches:**
- Show streak of consecutive days played
- "Yesterday's challenge was [game] - Did you play?"
- Could show global leaderboard if online connectivity added later

### Mode: Speedrun

**Concept:** Hit score targets across multiple games as fast as possible.

**Structure:**
1. Fixed sequence of 5 games with targets
2. Timer counts up continuously
3. Must hit target before moving to next game
4. Final time = your score
5. Leaderboard by fastest time

### Mode: Duel (2-Player)

**Concept:** Best of 3/5 across board games.

**Structure:**
1. Players pick game count (3 or 5)
2. Alternate who picks the game (or random)
3. Play each board game to completion
4. Winner gets a point
5. First to majority wins the duel

**Works with:** Chess, Checkers, Connect 4, Othello, Go, Mancala

### Priority Order

1. **Marathon** - Most versatile, good for solo play
2. **Daily Challenge** - Simple to implement, adds daily engagement
3. **Gauntlet** - Variation on Marathon, easy once Marathon works
4. **Speedrun** - Niche but fun
5. **Duel** - Only if 2-player demand exists

---

## 4. Art Visuals (Expansion)

### Overview
Currently only 3 art visuals: Starry Night, Water Lilies, Mondrian. Want to expand this category.

### Approach
**User-created pixel art** loaded from PNG files, not procedurally generated. This allows:
- Iteration in proper pixel art tools (Aseprite, Photoshop, etc.)
- Preview without running Python
- Cleaner visual code
- Potential for subtle animations overlaid on static base

### Candidates

| Painting | Artist | Why It Works at 64x64 |
|----------|--------|----------------------|
| **The Great Wave** | Hokusai | Strong silhouette, iconic shape, limited palette |
| **The Scream** | Munch | Simple figure, swirling background |
| **American Gothic** | Wood | Two figures + pitchfork, recognizable |
| **Girl with Pearl Earring** | Vermeer | Portrait profile, turban, earring pop |
| **The Persistence of Memory** | Dalí | Melting clocks, surreal shapes |
| **Nighthawks** | Hopper | Diner window glow, strong composition |
| **The Son of Man** | Magritte | Man with apple, simple but iconic |
| **Campbell's Soup Can** | Warhol | Graphic, simple, could cycle "flavors" |
| **The Kiss** | Klimt | Gold patterns, abstract potential |

### Animation Potential

Even with static base images, subtle animations add life:

| Painting | Animation Ideas |
|----------|-----------------|
| Great Wave | Foam particles, boat bobbing, color pulse |
| The Scream | Pulsing/waving background lines |
| Starry Night | Already animated (swirling sky) |
| Persistence of Memory | Clocks slowly dripping |
| Nighthawks | Flickering interior lights |
| Soup Can | Cycling through flavors |

### Asset Organization

```
led-arcade/
├── assets/
│   └── art/
│       ├── greatwave.png
│       ├── thescream.png
│       ├── nighthawks.png
│       └── ...
├── visuals/
│   ├── greatwave.py      # Loads PNG, adds animations
│   ├── thescream.py
│   └── ...
```

### Implementation Pattern

```python
class GreatWave(Visual):
    name = "GREATWAVE"
    description = "Hokusai's wave"
    category = "art"
    
    def reset(self):
        # Load base image
        self.base_image = load_png("assets/art/greatwave.png")
        # Animation state
        self.foam_particles = []
        
    def draw(self):
        # Draw base image
        self.draw_base()
        # Overlay animated elements
        self.draw_foam_particles()
```

---

## 5. Input Notes

### Left-Handed Support
Already handled: two action buttons mapped to same action, one on each side of joystick. No software changes needed.

---

## Implementation Priority

| Priority | Feature | Effort | Impact |
|----------|---------|--------|--------|
| 1 | Fade transitions (basic) | Low | High - instant polish |
| 2 | Attract mode (visuals only) | Medium | High - arcade authenticity |
| 3 | Marathon mode | Medium | High - replayability |
| 4 | Art visuals (user-created) | Low (code) | Medium - content variety |
| 5 | Attract mode (game demos) | Medium | Medium - nice to have |
| 6 | Daily challenge | Low | Medium - engagement hook |
| 7 | Additional transitions | Low | Low - variety |
| 8 | Other game modes | Medium | Low - niche |

---

## Open Questions

1. **Attract mode game selection:** Should all games be eligible for demos, or curate a "photogenic" subset?

2. **Marathon targets:** Need to playtest and define reasonable score targets per game.

3. **Transition timing:** 0.3s vs 0.5s - need to feel it on hardware.

4. **Art visual count:** How many paintings to target? 5? 10?

5. **Daily challenge persistence:** Store locally only, or eventually add network leaderboard?

---

*Document will be updated as decisions are made and implementation progresses.*
