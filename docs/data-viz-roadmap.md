# Data Visualization Roadmap

Assessment and expansion plan for the LED Arcade as a data visualization project.

---

## Current Strengths

### Tier 1 — Exemplary
These are the project's best data visualizations, where correct simulation rules produce emergent behavior the viewer can witness and interact with.

- **Cell** (Science) — 14 molecular pathways, 35 molecule types, real pathway logic. A working schematic of molecular machinery rendered as a living animation.
- **BML / Highway** (Road+Rail) — Phase transitions in traffic from purely local rules. Gridlock crystallizes visually at the critical density threshold.
- **Crystallize** (Automata) — Real Potts model with correct critical temperature, Metropolis sweeps, and ghost memory. Physics and AI phenomenology in one visual.
- **Sandpile** (Automata) — Self-organized criticality. Symmetric fractals from center-drop; dramatic avalanche cascades from random-drop.
- **Antikythera** (Mechanics) — 2000-year-old analog computer with historically accurate gear tooth ratios. Science communication through mechanism.
- **Spectroscope** (Science) — Real emission wavelengths producing real colors from CIE conversion. Quiet excellence.

### Tier 2 — Strong
Correctly implemented simulations with good teaching moments, but more conventional.

- Wave Tank (double-slit diffraction), Coulomb/EM Field, Chladni plates, Optics ray tracing
- Double Pendulum, N-body Orbits, Matter Phases
- Molecule (CPK models), Periodic (correct anomalous configs), Proteins (real PDB coords)
- Attractors (RK4), Primes (Ulam + Sacks spirals), Gray-Scott/Turing, Lenia
- Boids, Wolfram, Hodgepodge, Neurons (Izhikevich model)
- Historical mechanisms: Curta, Jacquard, Watch Gears, Piano Roll

### Tier 3 — Aesthetic / Reference
Visually appealing but not data-driven, or data presented as static reference rather than living visualization.

- Nature/demoscene effects: Plasma, Fire, Aurora, Starfield, Rotozoom, Copper Bars
- Domestic reference cards: Sauces, Spices, Pantry, Pasta (scrolling text databases)
- Music equipment aesthetics: Synthesizer, Jukebox, Equalizer, Turntable

---

## Expansion Plan

17 new visuals covering 6 gap areas, all fitting into existing categories.

---

### Automata (7 new visuals)

#### Predator-Prey
Lotka-Volterra on a grid. Rabbits (green) reproduce by spreading to empty neighbors. Foxes (orange) hunt adjacent rabbits, reproduce when fed, starve otherwise. The spatial version produces traveling waves of predators chasing prey fronts across the torus.
- **Controls:** Left/Right = prey reproduction rate. Up/Down = predator efficiency. Action = reseed.
- **Key moment:** Population waves chasing each other across the grid. Spatial structure prevents the extinction that occurs in well-mixed populations.
- **Connects to:** Slime (territorial competition), Boids (agent flocking)

#### Ecosystem
Food web with 4-5 trophic levels. Grass (green) → Herbivore (yellow) → Predator (orange) → Apex (red) → Decomposers (brown) recycling back to soil. Each organism is a particle with energy budget — eat to gain, move to spend, reproduce when surplus, die when depleted.
- **Controls:** Left/Right = sunlight/primary productivity. Up/Down = cycle view (all species / energy flow / single species).
- **Key moment:** The 10% rule becomes visible — far fewer apex predators than herbivores, always. Biomass pyramids emerge from local rules.
- **Connects to:** Predator-Prey (simpler version), Cell (energy transfer)

#### Epidemic
SIR model on a spatial grid. Susceptible (blue) → Infected (red) → Recovered (gray). Infection spreads to adjacent cells with probability β. Recovery after γ timesteps. R₀ = β/γ determines whether outbreaks fizzle (R₀ < 1) or sweep the grid (R₀ > 1).
- **Controls:** Left/Right = transmission rate β. Up/Down = recovery time γ. Action = seed new infection. Both = toggle vaccination (random immunity patches).
- **Key moment:** Herd immunity threshold — when ~60-70% are vaccinated, the remaining susceptible are protected. Also: superspreader geometry (hub vs. periphery seeding).
- **Connects to:** BML (phase transition from local rules), Slime (territory spread)

#### Evolution
Fitness landscape with competing populations. 2D landscape where height = fitness. Organisms reproduce with mutation (offspring near parent + random offset). Higher-fitness organisms reproduce more. Populations climb peaks, get trapped on local optima, occasionally jump via lucky mutations.
- **Controls:** Left/Right = mutation rate (low = exploitation, high = exploration). Up/Down = cycle landscape (single peak, double peak, rugged, shifting). Action = mass extinction event (kill 80%).
- **Key moment:** A population stuck on a local optimum while a higher peak sits nearby — more mutation, not less, enables the jump. Shifting landscapes make adapted populations suddenly maladapted.
- **Connects to:** Genetic Drift (population genetics), Particle Life (emergent ecology)

#### Game Theory
Iterated Prisoner's Dilemma on a grid. Each cell plays with its 8 neighbors. Strategies: Always Cooperate (blue), Always Defect (red), Tit-for-Tat (green), Random (yellow). After each round, cells adopt the strategy of their most successful neighbor.
- **Controls:** Left/Right = temptation-to-defect payoff. Up/Down = cycle strategy mix. Action = inject defector cluster.
- **Key moment:** Tit-for-Tat forming stable cooperative clusters that resist invasion. Robert Axelrod's 1984 tournament, alive on the grid.
- **Connects to:** Life (grid CA with emergent structure), Slime (territorial competition)

#### Percolation
Bond/site percolation threshold. Each cell open or blocked with probability p. At low p: isolated clusters. At p ≈ 0.593: a giant connected component suddenly spans the grid. Each connected component colored differently.
- **Controls:** Left/Right = occupation probability p. Action = regenerate. Up/Down = toggle bond vs. site percolation.
- **Key moment:** The spanning cluster appearing suddenly at the critical threshold. Completes a phase-transition trilogy with Sandpile and Crystallize.
- **Connects to:** Crystallize (phase transition), Sandpile (criticality)

#### Genetic Drift
Hardy-Weinberg population genetics. 200 organisms on a grid, each with two alleles (AA, Aa, aa = 3 colors). Random mating with neighbors each generation. In large populations, allele frequencies stay stable. Shrink the population and watch drift fix one allele randomly.
- **Controls:** Left/Right = population size. Up/Down = selection pressure (neutral → strong). Action = bottleneck event (kill 90%).
- **Key moment:** A balanced population losing an allele entirely from random chance when population drops below ~50. Drift overpowering selection in small populations.
- **Connects to:** Evolution (fitness/selection), DNA (molecular biology)

---

### Science (5 new visuals)

#### Fluid
Jos Stam stable fluid solver. Velocity field + dye density on 64x64. Semi-Lagrangian advection, pressure projection, diffusion. Dye injected at sources rises, curls, forms vortices. Joystick pushes fluid in real-time.
- **Controls:** Joystick = push fluid. Left/Right = viscosity. Up/Down = palette. Action = inject dye burst.
- **Key moment:** Pushing fluid with the joystick and watching vortex streets form. The most tactile visual in the project.
- **Connects to:** Wave Tank (2D physics sim), Matter Phases (fluid behavior)

#### Convection
Rayleigh-Bénard convection cells. Heat at bottom, cool at top. Below critical temperature difference: nothing. Above it: spontaneous convection rolls form — hexagonal cells or parallel rolls.
- **Controls:** Left/Right = temperature gradient. Action = perturb.
- **Key moment:** The spontaneous symmetry breaking when convection rolls appear. Another phase transition.
- **Connects to:** Matter Phases (what happens inside liquid when heated), Fluid (fluid dynamics)

#### Tectonics
Top-down plate motion. 4-6 plates with velocity vectors. Divergent boundaries: rift valleys (darken). Convergent: mountains (brighten). Transform: earthquake flashes along faults. Subduction consumes plate edges.
- **Controls:** Left/Right = time scale. Up/Down = cycle view (plates / elevation / quake history). Action = volcanic eruption.
- **Key moment:** Watching continents drift, collide, and reshape over geological time.
- **Connects to:** Erosion (surface processes), Drift (terrain)

#### Seismic
Wave propagation through layered earth cross-section. Earthquake generates P-waves (fast, compressional) and S-waves (slower, shear). Waves refract at layer boundaries via Snell's law. S-waves blocked by liquid outer core → shadow zone.
- **Controls:** Action = trigger quake at different positions. Left/Right = cycle focus (propagation / shadow zone / reflection).
- **Key moment:** The shadow zone appearing — this is literally how we know the earth has a liquid core.
- **Connects to:** Optics (Snell's law reuse), Wave Tank (wave propagation)

#### Network
Small-world (Watts-Strogatz) and scale-free (Barabási-Albert) network models. Ring lattice with rewiring probability p. At p≈0.1: small-world regime (high clustering AND short paths). Signal propagation animated from a source node.
- **Controls:** Left/Right = rewiring probability. Up/Down = toggle Watts-Strogatz / Barabási-Albert. Action = send signal pulse.
- **Key moment:** Signal crossing a small-world network in 3 hops vs. 30 in a regular lattice. Six degrees of separation, visible.
- **Connects to:** Neurons (network dynamics), Percolation (connectivity thresholds)

---

### Math (2 new visuals)

#### Entropy
Shannon entropy on a grid of symbols. Start ordered (zero entropy), add randomness, watch entropy climb. Then run compression — patterns replaced by shorter codes, grid shrinks. Decompress — original restored. Bit count displayed as a bar.
- **Controls:** Left/Right = alphabet size. Up/Down = cycle demo (entropy measurement, run-length encoding, Huffman coding, parity error correction).
- **Key moment:** Seeing compression *work* — identical information in fewer bits. Connects computation to information.
- **Connects to:** Wolfram Rule 30 (used as RNG), Jacquard (binary encoding)

#### Sorting
64 bars of different heights sorted by different algorithms. Bubble sort's O(n²) vs. merge sort's O(n log n) vs. quicksort's partitions vs. radix sort's buckets. Compared elements highlighted, swap/comparison counts displayed.
- **Controls:** Left/Right = speed. Up/Down = cycle algorithm. Action = reshuffle.
- **Key moment:** Merge sort and quicksort being *obviously* faster without needing the math. O(n log n) vs O(n²) made visceral.
- **Connects to:** Turing Machine (computation), Entropy (algorithmic information)

---

### Mechanics (1 new visual)

#### Turing Machine
A tape (horizontal strip), a head (highlighted cell), a state register. Run actual programs: binary counter, busy beaver (3-state, 4-state), simple multiplication. Tape scrolls as head moves. State shown as color.
- **Controls:** Left/Right = speed. Up/Down = cycle program. Action = step (when paused).
- **Key moment:** A busy beaver running thousands of steps before halting. The simplest possible computer doing surprisingly complex things.
- **Connects to:** Jacquard (programmable machine), Antikythera (ancient computation), Wolfram Rule 110 (Turing completeness)

---

### Nature (1 new visual)

#### Erosion
Hydraulic erosion on heightmap terrain. Rain particles flow downhill, pick up sediment proportional to speed, deposit when slowing. Valleys carve, rivers form, alluvial fans spread, canyons cut through ridges.
- **Controls:** Left/Right = rainfall rate. Up/Down = rock hardness. Action = trigger flood event.
- **Key moment:** Watching a river system carve itself from nothing. Transforms Drift's passive terrain into an active geological process.
- **Connects to:** Drift (terrain engine, potential code reuse), Tectonics (earth science)

---

### Domestic (1 new visual)

#### Flavor Network
Molecular gastronomy graph from Ahn et al. 2011. Ingredients as nodes, edges connect those sharing flavor compounds. Force-directed layout. East Asian cuisines avoid shared compounds (contrast), Western cuisines seek them (pairing).
- **Controls:** Left/Right = cycle cuisine region. Up/Down = filter by food category. Action = highlight ingredient connections.
- **Key moment:** Seeing *why* certain ingredients go together — shared aromatic molecules — instead of just knowing that they do.
- **Connects to:** Existing culinary visuals (transforms reference into real visualization)

---

## Priority Order

Ranked by impact — strongest teaching moment, most visual drama, and how well they fill gaps:

1. **Fluid** — Most interactive, most visually dramatic, biggest missing physics domain
2. **Epidemic** — Most immediately teachable, clean phase transition
3. **Percolation** — Purest phase transition, completes Sandpile/Crystallize trilogy
4. **Predator-Prey** — Most classic missing model, beautiful spatial waves
5. **Sorting** — Most universally understood "aha" moment
6. **Turing Machine** — Completes the computation history arc (Antikythera → Jacquard → Turing)
7. **Evolution** — Fitness landscapes are visually rich and conceptually deep
8. **Game Theory** — Axelrod's tournament is a perfect grid CA
9. **Erosion** — Extends existing Drift engine with active process
10. **Genetic Drift** — Clean demonstration of a counterintuitive phenomenon
11. **Convection** — Beautiful symmetry breaking, pairs with Matter Phases
12. **Entropy** — Connects computing to information theory
13. **Network** — Small-world is surprising and visual
14. **Seismic** — Shadow zone is a great teaching moment
15. **Ecosystem** — Ambitious but builds on Predator-Prey
16. **Tectonics** — Geological timescale may be hard to make dramatic at 64x64
17. **Flavor Network** — Smallest audience but deepens weakest section
