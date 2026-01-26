# Visual Resources for LED Matrix Effects

Research compiled for 64x64 LED matrix visuals.

## Cellular Automata

### CelLab (Already Using)
- **URL**: https://fourmilab.ch/cellab/
- 50+ rules: Rug, Hodge, Gyre, Aurora, Brain, Dendrite, Life variants
- Well documented with JS implementations

### LifeWiki - Life Variants
- **URL**: https://conwaylife.com/wiki/List_of_Life-like_rules
- **HighLife (B36/S23)** - Replicator patterns
- **Seeds (B2/S)** - Exploding, cells live 1 generation
- **Maze (B3/S12345)** - Creates mazes
- **Coral (B3/S45678)** - Coral-like growth
- **Diamoeba** - Diamond-shaped amoebas

### Wolfram Elementary CA
- **URL**: https://mathworld.wolfram.com/ElementaryCellularAutomaton.html
- 256 1D rules displayed as evolving 2D images
- Rule 30 (chaos), Rule 110 (complex), Rule 90 (Sierpinski)

---

## Demoscene Effects

### SizeCoding Wiki (Best Resource)
- **URL**: http://www.sizecoding.org/wiki/Design_Tips_and_Demoscene_effects_with_pseudo_code
- **Pseudocode for**: Plasma, Fire, Tunnel, Rotozoomer, Starfields, Fractals, Twister

### pouet.net
- **URL**: https://www.pouet.net/
- Thousands of demos with source code

### Oldschool Demo Effects
- **URL**: https://seancode.com/demofx/
- Detailed explanations of Fire, Tunnel, Rotozoomer, Plasma

---

## Reaction-Diffusion

### Gray-Scott Algorithm
- **URL**: https://www.algosome.com/articles/reaction-diffusion-gray-scott.html
- Spots, stripes, mitosis, coral patterns
- Efficient convolution-based implementation

### Belousov-Zhabotinsky
- **URL**: https://scipython.com/blog/simulating-the-belousov-zhabotinsky-reaction/
- Spiral waves and target patterns
- Can implement as cellular automaton (like Hodge)

---

## Generative Art

### The Nature of Code (Essential)
- **URL**: https://natureofcode.com/
- Physics, particles, flocking (Boids), cellular automata, fractals
- Free online book with JS code

### Flow Fields
- **Tyler Hobbs**: https://www.tylerxhobbs.com/words/flow-fields
- **Sighack**: https://sighack.com/post/getting-creative-with-perlin-noise-fields
- 25+ designs from single Perlin noise algorithm

### Physarum (Slime Mold)
- **URL**: https://www.michaelfogleman.com/projects/physarum/
- Agents deposit and follow chemical trails
- Stunning organic network patterns

---

## Mathematical Visualizations

### Strange Attractors
- **URL**: https://www.algosome.com/articles/lorenz-attractor-programming-code.html
- Lorenz (butterfly), Rossler (spirals), Henon
- Mesmerizing trajectories that never repeat

### Lissajous Curves
- **URL**: https://www.intmath.com/math-art-code/animated-lissajous-figures.php
- Simple sine waves, elegant hypnotic patterns

### Metaballs
- **URL**: https://jamie-wong.com/2014/08/19/metaballs-and-marching-squares/
- Lava lamp-like merging blobs

---

## Shader Resources

### The Book of Shaders
- **URL**: https://thebookofshaders.com/
- Interactive examples, parallel thinking

### Shadertoy
- **URL**: https://www.shadertoy.com/
- 52,000+ effects with source code

---

## Fantasy Consoles (Low-Res Focused)

### PICO-8
- **URL**: https://www.lexaloffle.com/pico-8.php?page=resources
- 128x128 display, similar constraints to LED matrix
- Demo effects designed for low resolution

### Dwitter
- **URL**: https://www.dwitter.net/
- JS demos in 140 characters - minimal implementations

---

## Priority Implementation List

### High Priority (Well-suited for 64x64):
1. **Gray-Scott Reaction-Diffusion** - Organic, slowly evolving
2. **Physarum Slime Mold** - Network formation
3. **Life Variants** (Seeds, Maze, Coral) - Simple rule changes, dramatic effects
4. **Fire Effect** - Classic, always looks good
5. **Boids Flocking** - Dynamic organic movement

### Medium Priority:
6. **Strange Attractors** - Point cloud trajectories
7. **Lissajous Curves** - Hypnotic, simple math
8. **Metaballs** - Lava lamp effect
9. **Tunnel Effect** - 3D perspective illusion
10. **1D Wolfram Rules** - Scrolling patterns

---

## Quick Reference URLs

```
CelLab Rules:     https://fourmilab.ch/cellab/manual/rules.html
SizeCoding:       http://www.sizecoding.org/wiki/Main_Page
Nature of Code:   https://natureofcode.com/
Book of Shaders:  https://thebookofshaders.com/
Shadertoy:        https://www.shadertoy.com/
LifeWiki:         https://conwaylife.com/wiki/
pouet.net:        https://www.pouet.net/
```
