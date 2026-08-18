# Roadmap: COOKING Category + LATIN Music Visuals

Created 2026-02-14. Reference data in `latin-rhythms-reference.md` and `cooking-reference.md`.

---

## NEW CATEGORY: COOKING

**Color:** Sage green `(120, 160, 100)`
**Category key:** `"cooking"`

### Educational Visuals

#### SAUCES (Rudiments-style)
Cycle through sauce families with name, ratio, and ingredients.
- **5 Mother Sauces:** Bechamel, Veloute, Espagnole, Hollandaise, Tomato
- **Daughter sauces** from each (~15-20 entries)
- **World sauces:** Teriyaki, Ponzu, Peanut, Chimichurri, Mole, Salsa Verde, Pesto, Aglio e Olio, Tikka Masala, Nuoc Cham, Raita, Stir-Fry (~12 entries)
- **Display:** Name top, ratio/formula scrolling, color-coded by family (white/cream/brown/gold/red)
- **Input:** Up/Down cycles entries, Left/Right jumps between families
- **~35+ total entries**

#### FLAVORS (Rudiments-style)
Regional flavor profiles and umami science.
- **12+ Regional profiles:** Thai, Mexican, Indian, French, Italian, Japanese, Chinese, Korean, Middle Eastern, Moroccan, Caribbean, Spanish
- **Umami synergy combos** as special entries
- **Salt/Fat/Acid/Heat** framework entries
- **Display:** Cuisine name, key ingredients scrolling, flavor balance bars (sweet/sour/salty/spicy/umami as colored horizontal bars showing relative intensity)
- **Input:** Up/Down cycles entries

#### BAKING (Rudiments-style)
Ratios, hydration, and formulas.
- **Baker's percentages** for bread, pizza styles
- **Core ratios:** Pound cake, pie dough, cookies, muffins, biscuits, pancakes, crepes
- **Hydration spectrum entries:** Bagel→sandwich→ciabatta→focaccia
- **Display:** Product name, visual ratio bars (proportional colored bars for flour/water/fat/sugar/egg), key numbers
- **Input:** Up/Down cycles entries
- **~15 entries**

#### PANTRY (Rudiments-style)
Aromatic bases, roux, stocks, herb bundles.
- **Aromatic bases:** Mirepoix (2:1:1), Holy Trinity, Soffritto, Sofrito, White Mirepoix
- **Roux:** White, Blond, Brown — show color gradient and timing
- **Stocks:** White, Brown, Fish Fumet, Vegetable, Remouillage, Glace de Viande
- **Herb bundles:** Bouquet Garni, Sachet d'Epices
- **Display:** Name, ratio, ingredient list scrolling, color representation
- **~15 entries**

### Animated Visuals

#### OVEN
Baked goods rising through the oven window.
- Lit oven interior, warm orange glow, heating element at top
- Glass window showing items rise: bread loaf, cake doming, cookies spreading, souffle puffing
- Surface gradually darkens pale→golden (Maillard browning)
- Steam wisps when cycling between items
- Timer counting down in corner
- **Input:** Button cycles what's baking

#### STOVETOP
Burner scenes from above or 3/4 view.
- 2-4 burners with flame rings glowing beneath pots/pans
- Scenes: pot of water coming to boil (bubbles accelerating), sauce simmering (lazy bubbles), pan searing (oil shimmer→sizzle sparks), reduction (liquid level dropping)
- Steam particles rising
- **Input:** Button cycles scenes

#### CHOP
Cutting techniques on a cutting board.
- Profile/side view: cutting board + knife
- Techniques: julienne, brunoise, chiffonade, mince, rough chop, bias cut
- Vegetable appears, knife animates the cut, pieces fall away
- Name of cut at top, size reference (1/8", 1/4" etc.)
- **Input:** Button cycles techniques
- **~6-8 entries**

#### GRILL
Open flame cooking on grates.
- Grate lines with glowing coals beneath
- Items: steak (grill marks appearing), corn (char spots), kebabs (rotating)
- Flame particles licking up between gaps
- Smoke particles rising
- **Input:** Button flips item or cycles what's grilling

#### WOK
Stir-fry toss animation.
- Side view of wok on high flame
- Ingredients toss in arc above wok (classic wok flip)
- Different colored particles: greens, reds, browns
- Flame wrapping around wok sides (wok hei)
- Oil splatter sparks
- **Input:** Button triggers toss

#### POUR
Liquid techniques and latte art.
- Latte art: espresso cup with milk stream creating rosetta/heart
- Also: wine decanting, cocktail pour, sauce drizzle on plate
- Satisfying fluid dynamics
- **Input:** Button cycles pour types

#### BLENDER
Blending scenes with color mixing.
- Front view of blender jar on base
- Ingredients drop in from top, lid on, blade spins up
- Vortex animation as contents blend — distinct colored chunks merging into final color
- Recipes:
  - Hummus — chickpeas+tahini+lemon+garlic → creamy beige
  - Guacamole — avocado+lime+onion+cilantro → green chunky→smooth
  - Smoothie — berries+banana+yogurt → purple/pink swirl
  - Pesto — basil+pine nuts+garlic+parmesan → deep green
  - Salsa — tomatoes+onion+jalapeno+cilantro → red chunky
  - Soup — roasted tomato or butternut squash → orange puree
  - Margarita — ice+lime+tequila → pale green with ice chunks
- Speed ramps: slow start → full speed → pulse
- **Input:** Button triggers blend or cycles recipes

#### PASTA
Pasta shapes — formation and reference.
- Each shape animates its formation: dough extruding through die, folding, crimping
- Shapes: spaghetti, penne, fusilli, farfalle, rigatoni, orecchiette, conchiglie, lasagna, ravioli, tortellini, cavatappi, bucatini, linguine, orzo, macaroni
- Display: name, origin region, "best with" sauce pairing
- Could also show boiling pot scene with shape tumbling in water
- Straddles educational + animated
- **Input:** Button cycles shapes
- **~15 entries**

### Summary Table

| # | Visual | Type | Template | Entries |
|---|--------|------|----------|---------|
| 1 | Sauces | Educational | Rudiments | ~35 |
| 2 | Flavors | Educational | Rudiments | ~15 |
| 3 | Baking | Educational | Rudiments | ~15 |
| 4 | Pantry | Educational | Rudiments | ~15 |
| 5 | Pasta | Edu + Animated | Hybrid | ~15 |
| 6 | Oven | Animated | New | ~5 scenes |
| 7 | Stovetop | Animated | New | ~4 scenes |
| 8 | Chop | Animated | New | ~7 techniques |
| 9 | Grill | Animated | New | ~4 items |
| 10 | Wok | Animated | New | 1 scene |
| 11 | Pour | Animated | New | ~4 scenes |
| 12 | Blender | Animated | New | ~7 recipes |

**12 visuals total. Comparable to MECHANICS (13) and MUSIC (13).**

---

## MUSIC ADDITIONS: LATIN DNA + LATIN GROOVES

Both added to existing MUSIC category (`category = "music"`), bringing it to 15 items.

### LATIN DNA (Rudiments-style)

Educational single-line pattern reference — "the rhythmic alphabet."

**Template:** Based on `rudiments.py` — single-voice patterns with playhead, name, numbering.

**Entries (~10):**
1. Tresillo — `x..x..x.` (3+3+2)
2. Habanera — `x..x.xx.`
3. Son Clave 3-2 — `x..x..x. ....x.x.`
4. Son Clave 2-3 — `....x.x. x..x..x.`
5. Rumba Clave 3-2 — `x..x..x. .....xx.`
6. Rumba Clave 2-3 — `.....xx. x..x..x.`
7. Bossa Nova Clave — `x..x..x. ..x..x..`
8. Bembe Bell (6/8) — `x.xx.xx.xx.x`
9. Cascara — `x.xx.xx. xx.xx.x.`
10. Conga Tumbao — `h.S.h.OO`

**Display:**
- Header: entry number + scrolling name
- Pattern grid: single row of hit/rest cells with playhead sweeping
- Cultural context as scrolling text beneath
- BPM adjustable

**Input:** Up/Down cycles patterns, Left/Right adjusts BPM, Action plays/pauses

### LATIN GROOVES (DrumMachine-style)

Full genre grooves with layered instruments — "the rhythmic language."

**Template:** Based on `drummachine.py` — multi-instrument 16-step grid with colored rows.

**Instruments (color-coded, varies by genre):**
- CLAVE (white)
- BELL/SHAKER (yellow)
- HI CONGA (orange)
- LO CONGA (red)
- TIMBALES (cyan)
- GUIRO/SCRAPER (green)
- BASS (purple)
- KEYS/GUITAR (pink)

**Entries (~12 genre patterns):**
1. Salsa — clave+tumbao+cascara+campana+guiro (80-110 BPM)
2. Bossa Nova — clave+cross-stick+hi-hat+guitar (110-145 BPM)
3. Samba — surdo+caixa+tamborim+agogo+shaker (96-152 BPM)
4. Cha-Cha-Cha — clave+guiro+cowbell (108-132 BPM)
5. Mambo — clave+timbales+congas+bell (104-200 BPM)
6. Cumbia — kick+snare+guacharaca+bass (80-150 BPM)
7. Merengue — tambora+guira+bass (120-180 BPM)
8. Reggaeton/Dembow — kick+snare tresillo (85-100 BPM)
9. Guaguanco — rumba clave+palitos+congas (100-120 BPM)
10. Mozambique — rumba clave+cowbell+bombos (100-125 BPM)
11. Songo — bell+syncopated kick+snare (100 BPM)
12. Bembe (6/8) — bell+congas (100-140 BPM)

**Display:**
- Header: genre name (left), BPM (right)
- 16-step grid (or 12-step for 6/8) with instrument rows
- Playhead sweeping with pad flash on hits
- Each genre has preset BPM

**Input:** Up/Down cycles genres, Left/Right adjusts BPM

---

## Build Order Recommendation

### Phase 1: Educational foundations
1. **LATIN DNA** — closest to existing Rudiments, fastest to build
2. **SAUCES** — establishes the Rudiments-style template for cooking

### Phase 2: Layered rhythms
3. **LATIN GROOVES** — closest to existing DrumMachine

### Phase 3: Cooking reference
4. **FLAVORS** — reuses Sauces template
5. **BAKING** — reuses template, adds ratio bar display
6. **PANTRY** — reuses template

### Phase 4: Cooking animations
7. **OVEN** — warm particles, rising animation
8. **STOVETOP** — bubbles, steam, sizzle particles
9. **CHOP** — sprite/knife animation
10. **PASTA** — shape animation + reference hybrid
11. **BLENDER** — vortex + color blending
12. **GRILL** — fire particles, smoke
13. **WOK** — physics arc toss
14. **POUR** — fluid dynamics

---

## Open Questions
- Cooking category color: sage green `(120, 160, 100)` — confirm?
- Category name: COOKING vs KITCHEN vs FOOD?
- Bembe/6/8 patterns: use 12-step grid instead of 16? Or quantize to 16?
- Latin DNA: include compound meter patterns (6/8) or keep all in 4/4?
- Pasta: pure animation, pure reference, or hybrid toggle?
