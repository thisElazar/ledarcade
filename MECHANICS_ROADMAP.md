# Mechanics - Visual Category Roadmap

A new visual category showing real-world machines and mechanisms in hypnotic, endless motion. Side-view cutaways and cross-sections that reveal the inner workings of iconic mechanical devices.

**Category key:** `mechanics`
**Category color:** `Colors.PURPLE`

---

## Visuals (15)

### Tier 1 - Core Collection

These establish the category identity. Each is a well-known mechanism with clear, readable motion at 64x64.

**1. Ford Model T Engine**
Single-cylinder side-view cutaway. Crankshaft rotates continuously, connecting rod drives piston up and down inside the cylinder. Flywheel visible. The engine that put the world on wheels.
- Crank angle drives all motion parametrically
- Cylinder walls, intake/exhaust valves opening in sequence
- Controls: Left/Right adjust RPM

**2. Swiss Watch Movement**
Meshing gears at different ratios, jeweled pivot points. A miniature world of precision. Show 3-4 gears of varying sizes with visible teeth interlocking.
- Gear teeth computed from radius and tooth count
- Smaller gears spin faster in correct ratio
- Controls: Left/Right adjust speed

**3. Singer Sewing Machine**
The classic black-and-gold treadle machine in side-view cutaway. Hand wheel drives the needle bar up and down via crank linkage. Thread loops through the bobbin mechanism beneath the fabric.
- Needle bar is a crank-slider linkage
- Fabric feeds left-to-right in small steps
- Controls: Left/Right adjust stitch speed

**4. Grandfather Clock**
Tall pendulum swinging behind an exposed escapement wheel. The anchor/pallet fork catches and releases the escapement teeth, creating the characteristic tick-tock. Gear train visible connecting escapement to clock hands.
- Pendulum is a damped harmonic oscillator
- Escapement creates intermittent rotation from smooth swing
- Controls: Left/Right adjust pendulum length (changes tick rate)

**5. Steam Locomotive**
Side view of driving wheels connected by coupling rods, with the piston and crosshead sliding in the cylinder. Think Union Pacific Big Boy - the heavy, purposeful rhythm of steel on steel.
- Main crank pin on drive wheel positions everything
- Coupling rods connect multiple wheels in phase
- Wheels roll along a track (ground line at bottom)
- Controls: Left/Right adjust speed

**6. Film Projector**
Geneva drive mechanism advancing film frames in discrete steps while the shutter rotates. The continuously spinning drive pin engages a slotted cross, advancing it exactly one position per revolution. Could show a film strip feeding through with tiny frame rectangles.
- Geneva cross advances in bursts, locks between advances
- Shutter disc rotates continuously
- Controls: Left/Right adjust projection speed

### Tier 2 - Expanding the Collection

**7. Camshaft**
Engine cutaway showing a rotating camshaft with egg-shaped lobes pushing valve followers up and down. Multiple cams offset at different angles so the valves fire in sequence.
- Each cam lobe profile defines follower displacement
- Spring return on each follower
- Controls: Left/Right adjust RPM

**8. Remington Typewriter**
Type bars swinging up from the basket to strike the platen. A key press launches a bar in an arc, it strikes, then returns. The carriage advances one space. Bell rings at the margin, carriage returns with a sweep.
- Type bars follow circular arc paths
- Carriage position tracks across the top
- Auto-types a repeating phrase, one character at a time
- Controls: Left/Right adjust typing speed

**9. Music Box**
A brass cylinder studded with pins rotates slowly past a steel comb. Individual pins catch and release tines as they pass, each tine a different length. The cylinder is the star - show the pins as bright dots on its surface.
- Cylinder rotation is continuous
- Pin-tine contact triggers a brief vibration animation on the tine
- Controls: Left/Right adjust tempo

**10. Gutenberg Press**
The screw press in action. A large central screw turns, driving the platen down onto the type bed. The bed rolls in on rails, impression is made, bed rolls back out. Workers would ink the type between impressions.
- Screw rotation drives linear platen descent
- Bed slides horizontally on a track
- Cyclical: roll in, press down, lift, roll out, repeat
- Controls: Left/Right adjust cycle speed

### Tier 3 - Showcase Pieces

**11. Curta Calculator**
The legendary handheld mechanical calculator. A cylindrical core of stepped drums rotates inside a housing. Number wheels on top advance as the crank turns. Show a cross-section with the drums meshing with result counters.
- Crank rotation drives stepped drum engagement
- Number wheels increment discretely
- Controls: Left/Right adjust crank speed

**12. Power Loom**
The shuttle flies back and forth through the shed (gap between raised and lowered warp threads). Heddles alternate which threads are up/down after each pass. The beater pushes the new weft thread tight. Rhythmic, industrial, mesmerizing.
- Shuttle traces horizontal path, reverses at edges
- Heddles swap vertical positions between passes
- Visible woven fabric accumulates at one side
- Controls: Left/Right adjust weaving speed

**13. Gyroscope**
A heavy disc spinning rapidly inside a gimbal frame. The disc stays level (or precesses slowly) while the frame tilts. Show the gimbal rings as concentric circles at varying angles, disc as a bright spinning element inside.
- Inner disc rotation is fast (blur effect or spoke animation)
- Gimbal precession is slow and smooth
- Controls: Left/Right adjust precession rate, Up/Down adjust spin speed

**14. Orrery**
A brass clockwork model of the solar system. Central sun, planets on arms orbiting at different speeds and distances. Inner planets zip around while outer planets crawl. Gears visible at the base driving the arms.
- Each planet arm rotates at a different angular velocity
- Correct relative orbital speed ratios
- Brass/gold color palette with dark background
- Controls: Left/Right adjust time scale

**15. Metronome**
A Wittner Maelzel metronome - weighted inverted pendulum ticking left and right with mechanical precision. The weight position on the arm determines the tempo. Display the current BPM prominently.
- Pendulum arm swings in a precise arc, pauses briefly at each extreme
- Weight position on the arm visually reflects the current BPM
- Tick mark or flash at each beat
- BPM displayed as text at top or bottom of screen
- Controls:
  - Left: -1 BPM
  - Right: +1 BPM
  - Up: +10 BPM
  - Down: -10 BPM
- BPM range: 20-240 (standard metronome range)

---

## Implementation Notes

### Category Registration
Add to `catalog.py` in `VISUAL_CATEGORIES`:
```python
Category("MECHANICS", Colors.PURPLE, "mechanics"),
```

### Shared Patterns
All mechanics visuals share common building blocks that already exist in the codebase:

- **Parametric linkages** - Crank angle to position via trig (same as Newton's Cradle, Double Pendulum)
- **Physics sub-stepping** - Subdivide dt for stable simulation
- **Float positions, integer drawing** - Smooth internal state, pixel-snapped rendering
- **Line drawing for rods/linkages**, circles for wheels/pivots
- **Incremental rotation accumulation** - Track `rotation += speed * dt` rather than `rotation = speed * time`, so speed changes don't cause jumps

### Gear Meshing Method

Any visual with interlocking gears (Watch, Orrery, Grandfather Clock, etc.) should use this approach:

**Rendering:** Single-pass pixel ownership. For each pixel in the bounding region, check all gears. The gear whose center is closest claims the pixel. This prevents teeth from two gears from ever occupying the same pixel — each gear's teeth only extend into its half of the overlap zone, naturally interleaving with the other gear's gaps.

**Phase calibration:** The gear ratio makes tooth phases at the contact point change at equal and opposite rates, so `phi_driver + phi_driven = const`. For correct meshing, that constant must be **0 (mod 1)**: when one gear reads 0.3 (tooth, < 0.5), the other reads 0.7 (gap, >= 0.5).

The offset for each driven gear:
```python
alpha = atan2(driven.cy - driver.cy, driven.cx - driver.cx)
beta  = alpha + pi
offset_driven = beta + (alpha - offset_driver) * N_driver / N_driven
```

Process mesh pairs in dependency order (driver offsets must be set before their driven gears). The invariant `phi_d + phi_v = 0` is then preserved automatically by the gear ratio for all time.

### Color Palette
Consistent metallic palette across the category:
- Steel gray `(180, 180, 190)` for structural parts
- Dark iron `(80, 80, 90)` for heavy components
- Brass/gold `(200, 170, 50)` for accent parts
- Copper `(200, 120, 60)` for warm accents
- Bright white `(255, 255, 255)` for highlights and moving contact points
- Background: black

### File Naming
Each visual gets one file in `visuals/`:
```
visuals/modelt.py
visuals/watchgears.py
visuals/singer.py
visuals/grandfather.py
visuals/locomotive.py
visuals/projector.py
visuals/camshaft.py
visuals/typewriter.py
visuals/musicbox.py
visuals/gutenberg.py
visuals/curta.py
visuals/loom.py
visuals/gyroscope.py
visuals/orrery.py
visuals/metronome.py
```
