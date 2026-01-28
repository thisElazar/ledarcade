# Hidden gems: Obscure visualization algorithms for 64x64 LED matrices

Dozens of lesser-known algorithms produce stunning visuals on low-resolution displays through simple rules that yield emergent complexity. This report catalogs **40+ obscure algorithms** across six categories, prioritizing implementations that are well-documented in academic papers, demoscene archives, and niche communities but rarely appear in mainstream tutorials. Each algorithm includes its core mechanics, original source, and suitability for real-time 64x64 RGB display.

---

## Obscure cellular automata from academic archives

The most fertile source for unusual CA rules is **Mirek's Cellebration (MCell)** and the **Primordial Soup Kitchen** at University of Wisconsin, which document hundreds of rules beyond Life and Wolfram.

**Larger than Life (LtL)** extends standard CA to larger neighborhoods with dramatic results. Invented by Kellie Michele Evans in her 1996 thesis, LtL uses radius-based neighbor counting with birth/survival thresholds as ranges. The **Bosco's Rule** variant (R5,C0,M1,S34..58,B34..45,NM) produces hollow "bugs" - eerily organic spaceships that resemble microorganisms. At 64x64 with radius 3-5, these rules create smooth, fluid blob-like structures impossible in standard CA. Implementation requires only extending the neighbor-counting radius; state remains binary.

**Cyclic Cellular Automata** from David Griffeath deserve special attention. N states cycle (0→1→2→...→N-1→0), and cells advance when threshold neighbors have the successor state. The **Demon Spirals** variant (Range 1, 8-16 colors, threshold 1) self-organizes from random noise into rotating "demons" - spiral wave patterns that emerge through four distinct phases. Map N states directly to the color wheel for RGB displays. The rule is trivial: `if any_neighbor == (my_state + 1) % N then advance`.

**Margolus Neighborhood CA** operates on 2×2 blocks rather than individual cells, alternating offset each generation. Norman Margolus at MIT developed this for reversible, particle-conserving systems. The **Billiard Ball Machine** simulates bouncing particles with exact conservation laws; **Critters** produces P4 orthogonal spaceships and P8 oscillators; **Tron** grows chaotically with visually distinct textures. These rules create a unique bouncing-particle aesthetic impossible in standard CA.

**Star Wars** (rule 345/2/4 in Generations notation) from Mirek Wojtowicz produces what resembles space battles - cells travel at light speed in "hauler-like" formations, self-organizing colonies build guns and shooters, and the result is extremely dynamic with emergent structure. Four states map perfectly to distinct RGB colors.

**Langton's Loops** (Christopher Langton, 1984) demonstrate self-replication: 8-state automata where information flows around loop structures, extends an "arm," and buds off new loops. At 64x64 you can observe several generations of replication before the colony fills available space. Each loop is roughly 10×10 cells with **151-generation** replication cycles - perfect for sustained viewing.

Lesser-known rules from the **CelLab archive** (Rudy Rucker & John Walker) include **Rug/RugLap** (averaging rules producing carpet-like textures), **Dendrite** (crystal branching growth), **Sublime** (ghostly diffusion patterns), **Gyre** (rotating vortex patterns), and **XTC** (excitable medium producing wave fronts). These are documented but rarely implemented outside academic contexts.

---

## Rare demoscene effects from the 80s-90s archives

Beyond plasma and fire, demoscene history contains dozens of effects documented primarily in obscure BBS files and demo group tutorials.

**Kefrens/Alcatraz Bars** create vertical raster bars that appear to weave behind each other - an impossible-looking depth illusion. First created by Metalwar of Alcatraz (often misattributed to Kefrens), the trick uses negative copper modulos and 1-line bobs on sine tables. Implementation: for each bar, draw vertically with horizontal X offset from a per-Y sine table; drawing order creates apparent depth layering.

**Glenz Vectors** render 3D objects with transparent faces using XOR blending. Named by Photon from Swedish "Gläns" (glisten), this technique from Kefrens' Megademo 8 creates glass/diamond-like appearances where overlapping areas produce new colors. At low resolution, XOR-blended polygons create surprisingly sophisticated transparency effects.

**Shadebobs** use additive blending with decay - circles that add to existing pixel values rather than replacing them. Moving shadebobs create organic light trails that accumulate where paths overlap. The algorithm: fade entire buffer slightly each frame, then add blob shapes at moving positions. No explicit particle system required.

**Rubber/Jelly Cube** (slit-scan effect) stores N frames of a rotating object in a buffer, then draws each scanline from a different temporal offset: `display[Y] = frame_buffer[(Y + offset) % num_frames][Y]`. This creates elastic, rubbery distortion from a simple delay buffer - complex organic deformation from minimal computation.

**Dot Tunnel** differs from textured tunnels by rendering rings of discrete dots in perspective, each ring at different Z depth with dots moving around circumferences. Extremely lightweight, working perfectly at low resolution with only **8-16 dots per ring**.

**Unlimited Bobs** exploits the Amiga's hardware by never erasing - just keep drawing sprites frame after frame, creating impossible-seeming infinite trails. Adapt for LED: never clear framebuffer, periodically apply fade or blur.

**Delay Vectors/Delay Dots** store the last N positions of moving objects, drawing all with decreasing intensity to create motion blur. First documented in Crystal BBS intro by Xography. Simple circular buffer of 8-16 positions with brightness falloff.

**Wormhole/Spiral Zoom** combines palette rotation with pre-calculated radial index tables: `index[x,y] = int(angle*k + log(radius)*m)`. Animate by rotating palette indices rather than recalculating geometry - infinite zoom effect from table lookup.

---

## Mathematical visualizations suited for low resolution

Several mathematical constructs produce distinctive patterns that actually benefit from 64×64 constraints.

**Burning Ship Fractal** modifies Mandelbrot by taking absolute values before squaring: `z(n+1) = (|Re(z_n)| + i|Im(z_n)|)² + c`. This creates ship-like structures with rectangular scaffolding more chaotic than Mandelbrot. The characteristic "mast" regions remain distinctive at low resolution. Window: x∈[-1.8,-1.7], y∈[-0.1,0.0].

**Lyapunov Fractals** visualize stability of logistic maps with alternating parameters. For sequence "AABAB", alternate between parameters a and b: `x(n+1) = r_n * x_n * (1-x_n)` where r_n depends on sequence position. Calculate the Lyapunov exponent λ; color stable regions (λ<0) differently from chaotic (λ>0). Different sequences produce dramatically different alien landscape patterns. Source: Mario Markus 1987, popularized by Dewdney in Scientific American 1991.

**Newton Fractals** visualize basins of attraction for Newton-Raphson root-finding on complex polynomials. For z³-1: `z(n+1) = z - (z³-1)/(3z²)`. Color by which of the three roots each starting point converges to; shade by convergence speed. The **Nova fractal** variant adds a relaxation parameter for morphing animation.

**Gingerbreadman Map** uses the simple iteration `x(n+1) = 1 - y_n + |x_n|`, `y(n+1) = x_n` to create hexagonal regions resembling a gingerbread figure. The geometric structure remains clear at 64x64.

**Abelian Sandpile Model** (Bak, Tang, Wiesenfeld 1987) demonstrates self-organized criticality: cells accumulate "sand," toppling when ≥4 to distribute to neighbors. Drop grains at center, watch avalanches propagate to form stunning fractal patterns. Implementation is trivial; visual results are striking.

**Diffusion-Limited Aggregation (DLA)** from Witten & Sander 1981 creates dendritic fractals: random walkers released from edges stick when touching existing structure. The branching tree-like patterns resemble lightning, coral, and crystal growth. At 64x64, the organic branching fills space beautifully.

**Ulam Spiral** arranges integers in a spiral from center, marking primes. At 64×64 (4096 integers), diagonal lines of prime density become visible - these correspond to quadratic polynomials like Euler's x²-x+41. Animation: grow outward, highlight twin primes differently.

**Pascal's Triangle mod N** generates fractal colorings: mod 2 yields Sierpinski, mod 3 yields a three-colored fractal. Exactly **64 rows** fit the display. Animate by cycling through different moduli (2,3,5,7,11...).

**Truchet Tiles** (Sébastien Truchet, 1704) fill grids with randomly-rotated diagonal arc patterns. Quarter-circle variants create flowing organic curves. Multi-scale recursive versions produce complexity from extreme simplicity. Perfect at any resolution.

**Superformula** (Johan Gielis, 2003) describes triangles, stars, flowers, and organic shapes with one polar equation: `r(φ) = (|cos(mφ/4)/a|^n2 + |sin(mφ/4)/b|^n3)^(-1/n1)`. Morph between shapes by interpolating parameters m, n1, n2, n3.

---

## Fantasy console and creative coding techniques

PICO-8 and TIC-80 communities have developed techniques specifically for extreme resolution constraints.

**Tweetcarts** (280-character PICO-8 programs) demonstrate maximum visual impact from minimal code. Key techniques include **bit-field fractals** using `(x XOR y) % palette` for Sierpinski-like patterns that morph when adding time, and **dissolving trails** where instead of clearing the screen, you clear random pixels before drawing.

**Scanline palette manipulation** (TIC-80's BDR callback) changes palette colors per-scanline, creating smooth rainbow gradients beyond the 16-color limit. With 64 scanlines, each color slot can vary through 64 shades.

**Domain warping** from Inigo Quilez feeds noise into noise: `f(p + f(p + f(p)))`. Using 2-3 octaves of FBM with recursive warping creates organic cloud-like flowing patterns. Low resolution enhances the smoky quality.

**Dwitter** techniques (140-character JavaScript demos) demonstrate extreme optimization. Top-rated patterns include rain using dual nested loops with parity-based conditional rendering, 3D Sierpinski using chaos game with XOR for pseudo-random direction, and ocean waves using perspective scaling with cosine sums for height.

**Blue noise dithering** uses pre-generated noise textures instead of Bayer matrices for more organic, less-structured gradients without repeating patterns. Pre-compute a 64x64 blue noise texture once.

**Temporal dithering** alternates between two threshold patterns at 30fps, creating perceived color depth through temporal averaging - the same technique LCD panels use.

---

## Particle systems with emergent behavior

Beyond Boids, several particle algorithms produce surprising self-organization from minimal rules.

**Particle Life** (Jeffrey Ventrella's "Clusters" 2007, popularized by Tom Mohr and Hunar Ahmad in 2020s) simulates multiple colored particle species with asymmetric attraction/repulsion matrices. Each species pair has different interaction force g; the force calculation is simply `F = g / distance`. Emergent behaviors include self-organizing clusters, chasing, molecular structures, orbiting, and mitosis-like splitting. Works excellently with **100-500 particles** on 64x64. Core implementation under 50 lines.

**Vicsek Model** (1995) is simpler than Boids but produces dramatic flocking phase transitions. Self-propelled particles move at constant speed, aligning direction with average of neighbors within radius R plus random noise. The algorithm exhibits a sharp transition from disordered gas to coherent flocking - watching this phase transition emerge is mesmerizing.

**Firefly Synchronization** implements the Kuramoto model: each agent has internal phase advancing at rate ω, nudging forward when neighbors flash. Spontaneous synchronization emerges from random initial phases, creating spectacular waves of coordinated light - ideal for LED matrices.

**Termite Wood Chip Gathering** (Mitchel Resnick 1994) demonstrates stigmergy: agents wander randomly, picking up chips when empty-handed and dropping them when carrying next to another chip. Scattered dots gradually consolidate into single piles WITHOUT central coordination. Implementation is trivial; emergent pile formation is surprising.

**Schelling Segregation Model** (Nobel Prize 2005) places two agent types on a grid; agents relocate when fewer than threshold percent of neighbors are same-type. High segregation emerges from mild preferences - macro behavior dramatically differs from micro motives. Two colors form distinct clusters.

**Forest Fire Model** (Drossel & Schwabl 1992) demonstrates self-organized criticality: trees grow with probability p, lightning strikes with probability f, fire spreads to adjacent trees. Power-law fire size distributions emerge. Visual: green forest with spreading red fires.

---

## Implementation priorities for 64x64 RGB

**Tier 1 - High impact, low complexity** (under 100 lines, stunning results):
- Cyclic CA Demon Spirals - trivial rule, spectacular self-organizing spirals
- Particle Life - 50 lines core, organic emergent clusters
- Firefly Synchronization - simple phase model, mesmerizing coordinated flashing
- Star Wars CA - dramatic dynamics, perfect 4-state RGB mapping
- Truchet Tiles - random + simple drawing, infinite variation
- Abelian Sandpile - fractal avalanches from elementary toppling rule

**Tier 2 - Medium complexity, excellent results** (100-200 lines):
- Larger than Life Bosco's Rule - extended neighbor counting, organic blobs
- Margolus Billiard Ball Machine - unique bouncing particle physics
- Langton's Loops - table-driven self-replication
- Dot Tunnel - lightweight 3D effect
- Domain Warping - recursive FBM for organic clouds
- DLA - random walk sticking for dendritic growth

**Tier 3 - Higher complexity, exceptional visuals**:
- Lenia - continuous CA with FFT convolution, microorganism aesthetics
- SmoothLife - continuous GoL extension, fluid gliders
- Newton Fractals - root-finding visualization with morphing potential
- Glenz Vectors - XOR-blended transparent 3D

**Key optimization notes**: Pre-calculate lookup tables for sin/cos, distance fields, and angles at startup. For particle systems, spatial hashing enables O(n log n) vs O(n²). Grid-based systems run O(grid_size) per step - extremely fast at 4096 cells. Target 16.6ms frame budget for 60fps; all listed algorithms are achievable with appropriate optimization.

The richest sources for further exploration remain the **MCell pattern archive** (psoup.math.wisc.edu/mcell), **pouet.net** demoscene database, the **CelLab archive** (fourmilab.ch/cellab), and **Lenia resources** (chakazul.github.io/lenia.html). These repositories contain hundreds of additional rule variants documented with visual examples and implementation details.