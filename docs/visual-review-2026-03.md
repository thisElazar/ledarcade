# Visual Collection Review — March 2026

Five domain experts reviewed ~150 source files across the full 247-visual collection.
Each reviewer read the actual source code, checked equations against published literature,
verified data against authoritative sources, and assessed visual effectiveness at 64x64.

**Reviewers:**
- Theoretical Physicist / Applied Mathematician
- Molecular Biologist / Computational Ecologist
- Mechanical Engineer / Historian of Technology
- Visual Artist / Demoscene Veteran / Interaction Designer
- Musicologist / Cultural Anthropologist / Culinary Arts Professor

---

## 1. THE CROWN JEWELS

These are the pieces that would hold their own in any LED art installation or educational
exhibit. No structural changes needed.

### Science & Simulation

**Crystallize** (`crystallize.py`) — Potts model phase transition with ghost memory.
The most intellectually ambitious visual in the entire collection. Six-phase cycle
(fog, nucleation, growth, competition, hold, dissolution) creates real narrative tension.
Ghost memory ensures no two cycles repeat. Three view modes (field, sequence, stream).
Vectorized numpy. Five palettes, all well-chosen. q=6 Potts model with Metropolis Monte
Carlo using checkerboard decomposition is correctly implemented. Critical temperature
T_c = 1/ln(1+sqrt(6)) = 0.807 is correct for 2D square-lattice q=6.

**Maxwell's Demon** (`maxwell.py`) — Perfect marriage of thought experiment and
interactive simulation. Auto-cycle phases (equilibrium → demon arrives → sorting →
demon departs → equalization) tell the complete thermodynamic story without user
interaction. 120 particles, speed-based coloring, responsive gate timing. The demon
sprite with glowing eyes is charming. Temperature bars at bottom give immediate
feedback on entropy reduction.

**Cell** (`cell.py`) — 14 biochemical pathways with correct enzyme sequences, proton
gradients, electron transport chains, and conformational cycling. A graduate-level
teaching tool compressed to 64 pixels. The Z-scheme electron flow in photosynthesis
is textbook correct. The Na+/K+ ATPase 6-state E1/E2 conformational cycle faithfully
represents the Albers-Post model. Complex II correctly has no proton pumping. The
CRISPR-Cas9 mechanistic order (PAM recognition → R-loop → double-strand cut) is right.

**Double Pendulum** (`dblpendulum.py`) — Textbook-correct Lagrangian equations of
motion. RK4 integrator with 10 sub-steps per frame. Trail of 600 points with palette
coloring captures the chaotic trajectory beautifully. Six palettes. The denominator
formula `2*M - m2*(1+cos(2*da))` is the standard form.

**Wave Tank** (`wavetank.py`) — Leapfrog (Verlet) integrator for the 2D wave equation
is correct. CFL stability condition satisfied (Courant number 0.0625). Five scenarios:
point source, double slit, interference, ripple, reflection. Double-slit diffraction
on a 64x64 LED is remarkable.

**Percolation** (`percolation.py`) — P_crit = 0.593 for site percolation on a square
lattice is correct. Union-Find with path compression and rank. Pulsing gold spanning
cluster is immediately readable. Auto-sweep from p=0.40 to p=0.72 with pause near
criticality is pedagogically well-designed.

**DNA** (`dna.py`) — Complete central dogma with accurate codon table (all 64 codons
verified), correct B-form helix geometry (10 bp/turn, 3.4 nm pitch), and all major
processes (replication, transcription, translation, mutation, chromatin packaging).
Rosalind Franklin credited alongside Watson and Crick.

**Neurons** (`neurons.py`) — Textbook-correct Izhikevich model with published parameter
sets. Regular spiking (a=0.02, b=0.2, c=-65, d=8), chattering (c=-50, d=2), bursting
(c=-55, d=4) are exact values from the 2003 paper. 80/20 excitatory/inhibitory ratio
is physiologically realistic.

### Visual & Aesthetic

**Frozen Lake** (`frozen_lake.py`) — Exceptional atmospheric design. Near-black palette
with hairline cracks barely visible. The presence mechanic (button press causes warmth
to spread) is genuinely affecting. Deep shapes with behavioral states, settling cracks
that propagate with stress waves, pressure fronts, rare deep glints. The layering is
extraordinarily dense for something that reads as "almost nothing is happening."
Conceptual art that works on hardware.

**Drift 3D** (`drift3d.py`) — Comanche-style voxel terrain on 64x64. Bilinear-
interpolated terrain sampling, distance fog, water shimmer, orbiting camera. A
technical showcase that also reads beautifully as a tiny landscape painting. LUT
pre-computation shows attention to performance.

**Turing** (all 4 variants + Lab) — Gray-Scott reaction-diffusion. Numpy-accelerated
solver running 8 steps per frame. Splitting into four sub-visuals (Spots, Stripes,
Coral, Worms) with locked parameter ranges was the right call — prevents users from
getting lost in dead parameter space. Lab mode with Pearson classification labels.

**Flux** (`flux.py`) — Curl noise flow fields with 150 curves across three species.
Divergence-free velocity field means curves flow around each other naturally. 1D
singularity breaker prevents collapse into parallel lines. Six palettes. Rewards
long watching.

**Truchet** (`truchet.py`) — Quarter-circle arcs at 8px tile size produce flowing
organic curves. Gentle single-tile evolution plus periodic wave sweeps. Anti-aliased
arc rendering with intensity falloff. Discovered by a Dominican priest 300 years ago.

**Win95 Maze** (`win95maze.py`) — DDA raycaster with procedural brick textures,
distance fog, four wall themes. Auto-navigation with right-hand wall following.
Manual override with 1-second idle return. Periodic maze regeneration with theme
cycling.

### Machines

**Watch Gears** (`watchgears.py`) — The finest mechanical piece in the collection.
Five-gear watch train (barrel, center, third, fourth, escape) with proper meshing
and computed phase offsets. Jewel bearings at each pivot (red dots with highlights).
Hairspring coiling/uncoiling with balance wheel oscillation. Differentiated materials
(brass, steel, copper, silver, gold). The S-curve layout captures the distinctive
aesthetic of a partially-assembled watch movement.

**Grandfather Clock** (`grandfather.py`) — Escapement mechanism is correctly
implemented. Escapement wheel advances one tooth per pendulum half-period. Anchor
pallets alternately engage/release. Tick-tock rhythm with flash at pendulum extremes.
The snapping advancement of one tooth at a time is mechanically precise and deeply
satisfying. Dark wooden case frame completes the scene.

**Locomotive** (`locomotive.py`) — Textbook crank-slider kinematics:
`displacement = r*cos(θ) + sqrt(L² - r²*sin²(θ))`. Three driving wheels keyed at
same phase (correct — coupling rods enforce this). Scrolling ties with wheel-
circumference-derived linear speed. Steam puff system with life/decay.

**Typewriter** (`typewriter.py`) — Multi-state machine (idle, bar swing, strike, bar
return, advance, bell, carriage return, line feed) produces convincing typewriter
behavior. Shakespeare soliloquies as typed content. Strike flash showing the actual
character. Bell at end-of-line. Monkey mode easter egg. Type bar swing arc from
different basket positions in semicircular basket.

**Projector** (`projector.py`) — Geneva drive mechanism correctly implemented:
continuous driver with pin engaging slots in Maltese cross, advancing exactly 90°
per revolution. Intermittent motion (25% engaged, 75% stationary) correct for 4-slot
Geneva. Locking disc segment is a correct and important detail.

**Weaving** (`weaving.py`) — 46 weave structures spanning 7000 years from every
inhabited continent: Ghanaian kente, Congolese kuba, Japanese kasuri, Navajo, Andean,
Nordic rosepath, Turkish kilim, Cambodian khmer, Maori taniko. 18 palettes drawn from
actual textile traditions. Draft patterns are correct (herringbone, houndstooth, satin,
twill verified). A masterpiece of cultural breadth and data-driven design.

### Reference Tools

**Scripts** (`scripts.py`) — 40 writing systems with 3,883 characters extracted from
real system fonts via fontTools. Stroke-by-stroke animation. Spans Latin through
Phoenician, Hebrew, Arabic, Devanagari, CJK, Ethiopian, Cherokee, Egyptian hieroglyphs,
cuneiform, Linear B, and Braille. Includes indigenous systems (Cherokee, Inuktitut,
Baybayin, Vai). Crown jewel of the entire project.

**Chord Chart** (`chordchart.py`) — Data from tombatossals/chords-db (MIT license),
crowd-verified. Guitar/ukulele toggle, 15 chord types per root, multiple voicings
with correct fingering and barre indicators. C major x32010, E major 022100,
F barre at fret 1 all verified correct. Someone could actually learn chords from this.

**Scales** (`scales.py`) — 16 scales: major/minor, pentatonic/blues, all 7 modes,
4 exotic. All intervals verified correct. Major: W-W-H-W-W-W-H. Blues: minor
pentatonic + b5. Japanese In scale: 0,1,5,7,8. Piano keyboard with highlighted
tones, transposition to all 12 roots, three display modes.

**Rudiments** (`rudiments.py`) — All 40 PAS International Drum Rudiments. Color-coded
R/L hands, accent vs normal, grace notes for flams and drags. Single Stroke Roll,
Paradiddle, Flam Accent, Swiss Army Triplet all verified correct. (Two errors noted
in Section 3 below.)

**Latin DNA** (`latindna.py`) — Sources cited (Wikipedia Clave rhythm, Berklee PULSE,
Ethan Hein). Tresillo 3+3+2 correct. Son Clave 3-2 correct. Rumba Clave 3-2 third
stroke shifted to &4, correct. Bossa Nova Clave 2-side verified. Bembe bell 7-stroke
pattern in 12/8 correct. Cascara correct. Scholarly rigor rare in an arcade cabinet.

**Sauces** (`sauces.py`) — Five French mother sauces correct. Parent + delta model
(Bechamel + Gruyere + Parmesan = Mornay) is standard culinary school teaching method.
All daughter sauce attributions verified (Mornay, Supreme, Bearnaise, Demi-glace,
Bordelaise). World sauces section adds Chimichurri, Nuoc Cham, etc.

---

## 2. STRONG PERFORMERS

These are solid, well-executed visuals that are clearly earning their place.

### Science

| Visual | Assessment |
|--------|------------|
| **Attractors** | Lorenz (σ=10, ρ=28, β=8/3), Rossler, Thomas all correct. RK4 integration. 75 particles with 40-point trails. Beautiful 3D projection with depth-sorted additive blending. |
| **Fluid** (all variants) | Proper Stam "Stable Fluids" implementation. Semi-Lagrangian advection, Gauss-Seidel pressure projection. Five variant visuals (Wind Tunnel, Ink Drops, Color Mix, Fluid Play, Fluid Sculpt). |
| **Seismic** | S-wave blocking by liquid outer core correctly implemented. Shadow zone mode shows how we discovered Earth's core structure. Snell's law refraction at layer boundaries. |
| **Lenia** | FFT-based convolution, bell-shaped kernel, named parameter regions. Genuinely alien patterns distinct from Gray-Scott. |
| **Sandpile** | Correct BTW model. Center-drop produces iconic fractal diamond. (Minor scan-order asymmetry noted.) |
| **Erosion** | Diamond-square terrain + hydraulic particle erosion. River formation from nothing is mesmerizing. |
| **Chladni** | 400 sand particles drifting toward nodal lines by gradient descent — physically faithful. Interactive frequency sweep. |
| **Orbits** | Velocity Verlet (symplectic). Solar system, 3-body, asteroid belt — three distinct dynamics. |
| **Fractals** | Mandelbrot, Julia, Sierpinski, Koch, Tree. Animated recursive depth is pedagogically lovely. |
| **Spectroscope** | Real element emission spectra with correct wavelength-to-RGB. Scientifically faithful. |
| **Optics** | Snell's law with prism dispersion (n varies with wavelength: 1.510-1.540). Correct and well-parameterized. |
| **Microscope** | Red blood cells with biconcave disc rendering, sickle cells, WBC with multi-lobed nucleus, plant cell with chloroplasts, paramecium with metachronal cilia wave. Anatomically accurate. |
| **Genetic Drift** | Wright-Fisher model with fitness-weighted sampling. Diploid, additive selection, bottleneck events. Clean implementation. |
| **Epidemic** | Spatial SIR with stochastic transmission. Beta=0.30, gamma=10 produces clear wavefront. Vaccination at 62% demonstrates insufficient coverage lesson. |
| **Pred-Prey** | Individual-based spatial model producing emergent Lotka-Volterra oscillations. Random processing order prevents bias. |
| **Game Theory** | Spatial iterated Prisoner's Dilemma with correct payoff matrix (T>R>P>S, 2R>T+S). TFT, Always Cooperate, Always Defect, Random. |
| **Evolution** | Roulette wheel selection on 1D fitness landscape. Single/double peak, rugged, shifting. Mass extinction shows recovery. |
| **Ecosystem** | Five trophic levels with energy budgets. 10% transfer rule emerges naturally. Behavioral priorities (flee > chase > wander). |

### Machines

| Visual | Assessment |
|--------|------------|
| **Gutenberg** | Five-phase cycle (ink, slide, press, impression, release). Screw thread animation. Printed page accumulation. |
| **Singer** | Lockstitch with rotating hook is technically ambitious. Four-phase thread loop animation. |
| **Loom** | Heddle transition animation is the key moment and it works. Shuttle, beater bar, cloth accumulation. |
| **Camshaft** | Raised cosine lobe profile (real cam design). Phase-offset sequential valve firing. |
| **Archimedes** | Helical blade visibility via sin() is clever. Water pocket movement through screw. |
| **Turing Machine** | Waterfall visualization of tape history is brilliant. BB-3, BB-4, BB-5 with correct transition tables. |
| **Jacquard** | Punch card → needle probe → hook → binary display. Computational connection made explicit. |

### Visual / Aesthetic

| Visual | Assessment |
|--------|------------|
| **Fire** | Three palettes (fire/ice/poison). Weighted-average propagation with random cooling. Classic, well-executed. |
| **Demon Spirals** | Self-organizing spirals from random noise. Smooth interpolation, staleness detection. Reliable ambient piece. |
| **Hodge** | BZ-reaction spirals distinct from cyclic CA — more structure, more wave character. Adjustable g parameter. |
| **Trance** | Classic tunnel with precomputed LUTs. Five textures, five palettes. Brick texture is particularly good. |
| **Rotozoom** | Five textures, five palettes. Oscillating zoom properly smooth. Authentic. |
| **Twister** | 3D cylinder shading (cosine brightness) elevates it above phase-offset. Three twist modes. |
| **Copper Bars** | Metallic gradient with specular highlight reads as shiny metal. Additive blending on overlap. |
| **Particle Life** | Asymmetric attraction/repulsion matrices. Bell-shaped force envelope. 3-6 species. |
| **Boids** | Reynolds flocking with mega-flock disruption. Heading-colored 2x2 blocks with trails. |
| **Slime** | Six competing colonies with death cycle. Spindly growth limiter prevents boring blobs. |

### Reference / Educational

| Visual | Assessment |
|--------|------------|
| **Pantry** | Mirepoix 2:1:1 correct. Holy Trinity correct. Roux progressions correct. Stocks with correct timing (chicken 3-4h, beef 8-12h, fish 30-45min MAX). "NEVER BOIL" for chicken stock is real professional knowledge. |
| **Spices** | 18 blends from 6 regions. Ras el Hanout, Garam Masala, Za'atar, Five-Spice, Panch Phoron, Berbere all verified. Etymologies included (Ras el Hanout = "Head of the Shop"). |
| **Knife** | Julienne 1/8×1/8×2", Brunoise 1/8" cube, Batonnet 1/4×1/4×2" — all correct culinary school dimensions. Flipbook animation shows progressive breakdown. |
| **Baking** | Baker's percentages with proportional bars. Standard bread 62% hydration, Neapolitan 60% + long ferment, Pound cake 1:1:1:1 all correct. |
| **Butcher** | USDA primal breakdown correct for all 4 animals (beef, pork, lamb, chicken). Retail cuts bridge theory to practice. |
| **Flavors** | 13 cuisines on 5 axes (Sweet/Sour/Salty/Spicy/Umami). Japanese umami-dominant, Thai balanced, French butter/umami — all verified. |
| **Dance** | 12 dances, 4 families. Sources: ISTD Bronze, Vaganova, CLRG syllabi. Trail-rendering approach is genuinely novel for showing dance geometry. |
| **Calendars** | 8 calendar systems. Mayan dot-bar vigesimal correct. Ethiopian 13-month correct. French Republican decimal clock historically accurate. |
| **Language** | 67 languages with greetings in native script. Non-Latin scripts hand-crafted as bitmap glyphs. |
| **Knots** | 10 knots, 3 families (Essential/Hitches/Bends). Multi-keyframe progressive tying animation. Follows standard knotting pedagogy. |
| **Yoga** | 14 poses from MediaPipe datasets. Sun Salutation, Warrior, Balance sequences. Smooth joint interpolation. |
| **Drum Machine** | 16-step grid maps perfectly to 64px width. Flash-on-hit feedback. Song-recognition hooks people in. |
| **Latin Grooves** | 12 Latin genre presets with 8 instruments. Salsa son clave 3-2 + cascara correct. Reggaeton dembow correct. |
| **Circle of Fifths** | 12 keys in correct order. Relative minors correctly paired. Color-coded distance from selected key. |
| **Theremin** | Correct dual-antenna model. EM field visualization. Waveform display as feedback. |
| **Pasta** | 20 shapes across 5 families. Pixel art with Italian meanings, regional origins, sauce pairings. |

---

## 3. ERRORS TO FIX

### Scientific / Physics Errors

**`cell.py` — Krebs cycle enzyme count** (Medium)
Claims "8 ENZYMES ONE TURN" but only draws 6 stations. Missing aconitase and fumarase.
Fix: Add the 2 missing enzymes, or change the note to "6 STATIONS SHOWN."

**`cell.py` — Prokaryotic/eukaryotic inconsistency** (Medium)
Transcription pathway uses sigma factor and rho factor (prokaryotic), but Translation
pathway uses 40S/60S ribosomal subunits (eukaryotic). Fix: Make both prokaryotic
(sigma/rho + 30S/50S) or both eukaryotic (general TFs + 40S/60S).

**`cell.py` + `dna.py` — 30nm chromatin fiber** (Medium)
Both claim nucleosomes fold into 30nm fiber. This model was largely debunked by
cryo-EM studies (Ou et al., 2017). In vivo chromatin appears to be irregular 10nm
fibers that fold into higher-order structures without a distinct 30nm intermediate.
Fix: Update to "10NM FIBERS FOLD INTO LOOPS" or remove the 30nm claim.

**`convection.py` — "Ra" label is not a Rayleigh number** (High)
The `_rayleigh()` function returns `gradient * 10.0` as a display label. Displaying
"Ra 8.0" is misleading — real Rayleigh-Bénard onset is at Ra ~ 1708. Fix: Rename
the label to "dT" or "DRIVE."

**`convection.py` — Horizontal buoyancy is nonphysical** (Medium)
Line 215-218: `vxy[x] += buoyancy * 0.3 * (xr - xl) * dt_phys`. Buoyancy acts
vertically. Horizontal pressure gradients arise from incompressibility, not direct
horizontal buoyancy coupling. This produces rolls, but for the wrong reason.

**`sandpile.py` — Sequential toppling creates asymmetry** (Low)
Toppling scan (lines 136-156) processes left-to-right, top-to-bottom each pass. A
cell at (0,0) that topples sends a grain to (1,0), which might topple in the same
pass. Fix: Use double-buffered or queue-based toppling for symmetry.

**`fluid.py` — Low iteration count** (Medium)
6 Gauss-Seidel iterations for pressure projection. Stam's paper recommends 20+. At
64x64 this can produce visible divergence artifacts (velocity field not truly
incompressible). Fix: Increase to 12-16 iterations.

**`matter.py` — Phase transitions are hard-coded** (Medium)
Phase transitions driven by external temperature thresholds (solid < 0.33, liquid
0.33-0.66, gas > 0.66) rather than emerging from interparticle potentials. This is
animation, not simulation. Fix: Consider implementing with Lennard-Jones potentials
so phases emerge from dynamics.

**`gyroscope.py` — Precession physics is ornamental** (Medium)
Precession and spin are independently controlled. In reality, precession rate is
inversely proportional to spin speed. Fix: Couple precession inversely to spin.

**`dna.py` — Mutation repair rate** (Low)
Repair probability is `random.random() < 0.5` (50%). Real DNA mismatch repair catches
>99% of errors. Fix: Increase to 0.85-0.95 for realism while still leaving visual
mutations.

**`peptides.py` — N-terminal pKa** (Low)
Value of 9.69 is wrong — that's the epsilon-amino group of lysine. Standard alpha-
amino group pKa is ~8.0. Fix: Change to 8.0.

**`microscope.py` — Water molecule angle** (Low)
H-O-H angle is computed but not used in rendering. H atoms placed at fixed (-1,-1)
and (+1,-1) relative to O, giving 90° instead of the real 104.5°. Fix: Use the
computed angle for H positioning.

### Mechanical / Historical Errors

**`modelt.py` — Not a Model T** (High)
Shows a single-cylinder engine but calls it "Model T." The real Model T had a
4-cylinder inline engine. Fix: Rename to "4-STROKE ENGINE" or redesign for 4
cylinders.

**`beamengine.py` — Not a Watt engine** (High)
Attributed to Watt but shows a generic/Newcomen engine without Watt's key innovations:
separate condenser (the entire point of Watt's patent), parallel motion linkage.
Fix: Add a separate condenser, or drop "Watt" and call it "BEAM ENGINE."

**`antikythera.py` — Gear ratios are arbitrary** (Medium)
Tooth counts (12, 10, 8, 6, 14, 7, 5) bear no relation to the actual mechanism. The
real Antikythera's most famous gear has 223 teeth (Saros eclipse cycle) and the main
gear has 48. Fix: Encode at least one real astronomical ratio (e.g., Metonic 19:235).

**`watchgears.py` — Missing pallet fork** (Medium)
The lever (pallet fork) between escape wheel and balance wheel is absent. This is the
actual escapement mechanism that converts rotary to oscillatory motion. Fix: Add the
pallet fork connecting escape wheel to balance wheel.

**`astrolabe.py` — Tympan curves** (Low)
Uses concentric circles and radial lines. Real tympan altitude curves are asymmetric,
offset circles (stereographic projections). Azimuth lines are arcs, not straight lines.

**`orrery.py` — Decorative gears** (Low)
Base gears alternate direction at varying speeds unrelated to planetary ratios. A real
orrery's gears encode orbital period ratios mechanically. Fix: Make gear ratios match
the planetary periods shown.

**`curta.py` — Wrong form factor** (Low)
Cross-section view with horizontal drums doesn't capture the Curta's distinctive
cylindrical pepper-grinder shape. Setting sliders and carry mechanism are absent.

### Music / Content Errors

**`rudiments.py` — PAS 25 identical to PAS 24** (High)
Single Flammed Mill (PAS 25) has identical note data to Flam Paradiddle (PAS 24).
These are different rudiments. The Single Flammed Mill inverts which hand gets the
flam on the second half.

**`rudiments.py` — PAS 27 sticking incorrect** (Medium)
Pataflafla shows `lR-L-R-lL-R-lL` but the standard pataflafla is
`lR-L-R-lL-R-L-lR`. Current data has too many consecutive flams.

**`drummachine.py` — "Levee Breaks" BPM** (Medium)
Listed at 100 BPM. The actual Bonham half-time shuffle is ~69-71 BPM. Fix: Change
to 70.

**`drummachine.py` — "Bite The Dust" kick pattern** (Low)
Missing the signature anticipated kick on the "and" of beat 3. Currently
indistinguishable from "Billie Jean."

**`drummachine.py` — "Rick Roll" pattern** (Low)
Shows only tom rolls and rim clicks with no kick, snare, or hat. The actual Linn
LM-1 pattern is a standard 4-on-the-floor dance beat.

**`baking.py` — Ciabatta hydration** (Low)
Listed at 68%. Real ciabatta is 75-85%. The note says "HIGH HYDRATION" but 68% is
only moderately high. Fix: Increase to 78-80%.

### Naming Issues

| File | Current Name | Problem | Suggested Fix |
|------|-------------|---------|---------------|
| `mitosis.py` | MITOSIS | Doesn't show mitosis — shows colony growth/fission | Rename to PROLIFERATION |
| `aurora.py` | AURORA | Not an aurora — it's a flowing paint CA from CelLab | Rename to FLOW or RUCKER |
| `modelt.py` | MODEL T | Single-cylinder, not Model T's 4-cylinder | Rename to 4-STROKE |
| `beamengine.py` | WATT ENGINE | Missing Watt's innovations | Rename to BEAM ENGINE or add condenser |
| `convection.py` | Ra (display) | Not a Rayleigh number | Rename label to dT or DRIVE |
| `emfield.py` | EM MOTOR | Electrostatic rotor, not electromagnetic induction | Rename scenario to ROTOR |

---

## 4. CUT OR MERGE CANDIDATES

### Strong consensus to cut

**Equalizer** (`equalizer.py`) — Zero educational content. Simulated spectrum analysis
using layered sine waves displaying no real data. Pure eye candy. The weakest music
visual. "If anything needs cutting, this is first."

**Jukebox** (`jukebox.py`) — Decorative Wurlitzer visualization. No educational content.
Bubble tubes, spinning record, selection panel. Pure eye candy alongside Equalizer.

### Merge candidates

**Latin Grooves → Drum Machine** — Structurally identical code (same class structure,
same grid layout, same drawing code). Only difference is Latin instruments/presets vs
rock/pop songs. Could be one visual with genre families (Rock, Latin, Electronic).

**Turntable → Gramophone** — Both show record playback devices. Gramophone has the
more interesting visual (side view with horn, crank mechanism, RPM options). Turntable
is a top-down view that's less distinctive.

**XOR Pattern → Rotozoom** — XOR already appears as a Rotozoom texture. The standalone
XOR is eight variations of the same bitwise trick. Rotozoom's XOR with rotation/zoom
is more visually interesting.

**EMMotor / EMCircuit / EMFreeAir → Coulomb** — The unified `Coulomb` class already
subsumes these. Remove the redundant standalone classes.

### Borderline (reviewers disagreed)

**Moire** — Physics agent said fine; art agent said "resolution too low for the effect
to sing. Four variations of slightly offset sine waves is not enough to justify a
slot." The effect needs higher resolution to be striking.

**SineScroller** — "Without actual scrolltext, just colored sine waves. The multiband
mode is the only interesting variant." Could be merged into CopperBars as a wave mode.

**Rainbow** — "Exists because it must. Not a showpiece." Six modes cover the basics
but it's the most generic possible LED panel demo. Serves as a palette cleanser.

**Entropy RLE/Huffman modes** — "Illegible on 64x64 LEDs. Tiny text like '168b' and
'SAVE 23%' will be unreadable." Keep entropy grid + parity, cut the text-heavy modes.

---

## 5. THINGS THAT ARE NOT SUPERFLUOUS

Several potential redundancies were investigated and **cleared by all reviewers**:

**Loom / Weaving / Jacquard** — Three entirely different aspects of textile production.
Loom shows the machine mechanism (shuttle, heddles, beater). Weaving shows the product
(46 warp/weft patterns viewed from above). Jacquard shows the control mechanism (punch
card → binary logic). They complement each other beautifully. All stay.

**8 food visuals** — "One of the strongest categories in the entire project." Every
single food visual teaches real, practical culinary knowledge. Sauces, Pantry, Spices,
Knife, Baking, Flavors, Butcher, Pasta — all verified accurate against professional
culinary references. All stay.

**Boids / Slime / ParticleLife** — Three distinct emergent systems. Boids is flocking
(Reynolds rules). Slime is territorial competition (death cycle, spindly growth).
ParticleLife is force-matrix chemistry (asymmetric attraction). No redundancy.

**All 20 machines** — "Remarkably well-differentiated." Antikythera (astronomical gears),
Archimedes (water lifting), Astrolabe (navigation), Beam Engine (steam power),
Camshaft (valve timing), Curta (calculation), Grandfather (timekeeping), Gutenberg
(printing), Gyroscope (angular momentum), Jacquard (programmable weaving), Locomotive
(coupled wheels), Loom (heddle weaving), Model T (4-stroke combustion), Orrery (solar
system model), Projector (Geneva intermittent drive), Singer (lockstitch), Turing
Machine (computation), Typewriter (character printing), Watch (miniature escapement),
Weaving (cultural patterns). No merges needed.

**DemonSpirals / Hodge / Turing** — Each produces qualitatively different patterns.
Cyclic spirals vs BZ-reaction waves vs reaction-diffusion spots/stripes. All justified.

**Cell automata cluster** (Aurora, Faders, Gyre, Rug, Quarks, Ripples) — Six distinct
CelLab rule families from Rucker & Walker. Each produces different visual output. The
collection's depth in this area is a strength.

---

## 6. UNDERPERFORMERS WORTH IMPROVING

| Visual | Issue | Suggested Fix |
|--------|-------|---------------|
| **Matrix** | 1px-wide drops too thin at 64x64 | Make drops 2px wide; add occasional glyph flicker |
| **Starfield** | Plain black with white dots is stark | Add subtle blue/purple nebula background using layered sine fog |
| **Cylon** | Single-bar mode boring on 2D panel | Default to full-screen mode with per-row phase offsets |
| **Polaroid** | 810 lines overbuilt for novelty visual | Simplify photo generation; 15 photo styles with sub-variations is overbuilt |
| **Convection** | Pseudo-physics misleading as "Rayleigh-Bénard" | Use Boussinesq solver via fluid.py or rename honestly |
| **Matter** | Animation, not simulation | Implement with Lennard-Jones potentials so phases emerge |
| **Electrons** | 30+ scenes, many are animated diagrams not simulations | Curate to strongest 15-20; split file by topic |
| **Entropy** | RLE/Huffman modes illegible on LEDs | Cut those modes; keep entropy grid + parity |
| **Circle of Fifths** | Chord progression view stubbed but not implemented | Complete the missing feature |
| **Baking** | Missing sourdough (most important bread category) | Add sourdough starter ratios and brioche |

---

## 7. CULTURAL SENSITIVITY

All five reviewers noted the collection handles cultural representation well:

- **Scripts** includes indigenous writing systems (Cherokee, Inuktitut, Baybayin, Vai)
  alongside dominant ones
- **Dance** cites published syllabi (ISTD Bronze, Vaganova, CLRG) rather than inventing
  movements
- **Calendars** treats all 8 systems with equal visual care and historical context
- **Spices** credits regional origins and etymologies
- **Weaving** includes 46 traditions from every continent with culturally appropriate
  palettes
- **Language** shows greetings in native scripts rather than just romanization

"No caricatures, no stereotypes, no cultural hierarchy. This is solid work."

---

## 8. SUMMARY STATISTICS

| Metric | Count |
|--------|-------|
| Total visuals reviewed | ~150 of 247 |
| Crown jewels identified | 27 |
| Strong performers | ~60 |
| Scientific/physics errors | 13 |
| Mechanical/historical errors | 7 |
| Music/content errors | 6 |
| Naming issues | 6 |
| Cut candidates | 2 (Equalizer, Jukebox) |
| Merge candidates | 4 pairs |
| Borderline cuts | 4 |
| Cleared of redundancy | 7 groups investigated, all cleared |

### If you had to pick seven for a gallery loop

Crystallize, Frozen Lake, Drift 3D, Turing Coral, Truchet, Flux, Win95 Maze.

### The single most important fix

`cell.py`'s prokaryotic/eukaryotic inconsistency — mixing sigma/rho transcription
factors with 40S/60S ribosomes sends a confused signal in what is otherwise a
graduate-level teaching tool.

### The single best thing in the collection

`scripts.py` — 40 writing systems from Linear B to Braille, stroke-animated from
real font data via fontTools. Nothing like this exists anywhere else. It is
simultaneously a technical achievement, an educational tool, and a cultural statement
about the diversity of human expression.
