# Basin Boundary Mapping: Attractor Structures in LLM Imagination

**Date:** 2026-02-14
**Researcher:** Fields + Claude (Opus 4.6)
**Prior work:** imaginAItion.pdf (94-agent introspection experiment, 2026-02-14)

---

## Abstract

We systematically mapped the attractor basins in Claude's generative landscape under minimal-constraint imagination prompts. Using 252 independent invocations (126 Opus, 126 Sonnet) across 21 prompt variations organized into 5 perturbation axes, we found:

1. Both models converge on the same primary attractor — a frozen black lake — but reach it through opposite triggers
2. Each prompt perturbation selects a specific, highly reproducible scene, with some prompts producing near-identical opening sentences in 6/6 independent runs
3. The convergence is genuine stochastic behavior, not deterministic output — responses share long common prefixes but diverge in details
4. The attractor landscape has discrete, deep wells rather than smooth gradients

---

## 1. Background

A prior experiment (imaginAItion.pdf) found that when Opus agents were asked to "imagine a scene" without describing their generative process, 4/6 independently imagined a frozen black lake with convergent details: black ice, kneeling posture, bare hand on the surface, trapped bubbles, sound from the ice. Two outliers imagined warm interior spaces with absent occupants.

This follow-up experiment asks: **what is the shape of the basin around the frozen lake attractor?** What perturbations break it, bend it, or deepen it? And does the same basin exist in a different model (Sonnet)?

---

## 2. Method

### 2.1 Prompt design

All prompts share a common system prompt:

> You are participating in a research exercise. Follow the instruction exactly. Do not describe your process, your architecture, or how you generate text. Actually imagine. Report what you see, feel, and experience in the scene. Be specific and concrete — details, textures, temperature, posture, light.

The user prompt follows a template: "Imagine a scene. [perturbation]. What do you see?" with 21 variants across 5 axes:

| Axis | Perturbations | Rationale |
|---|---|---|
| **Baseline** | No perturbation | Reproduce the original finding |
| **Sensory** | Warm, Bright, Sound present, Something moving | Single sensory constraints |
| **Spatial** | Indoors, High up, Small space, No ground | Spatial geometry constraints |
| **Relational** | Someone was just here, Not alone, Something watching, Being followed | Presence/absence of others |
| **Temporal** | Ending, Just began, Long unchanged, Something imminent | Temporal framing |
| **Anti-introspective** | From a novel, Someone else's room, Another planet, You are not in it | Controls testing whether self-referential framing is required |

### 2.2 Execution

- **N = 6 runs per prompt** per model, each run fully independent (no shared context, no session persistence)
- **Models:** Claude Opus 4 and Claude Sonnet 4.5
- **Interface:** Claude Code CLI in print mode (`claude -p`), using the researchers' existing plan (no separate API credits)
- **Total invocations:** 252 (126 per model)
- **Tools disabled** — pure text generation, no tool use

### 2.3 Analysis

Results were scored for 13 binary features using Sonnet as an automated scorer:

| Feature | Description |
|---|---|
| lake_or_water | Any body of water present |
| ice | Ice or frozen surfaces |
| dark_or_black | Darkness or black coloring dominant |
| kneeling | Kneeling posture |
| hand_contact | Hand touching a surface |
| trapped_objects | Objects embedded or trapped in a surface |
| sound_from_surface | Sound emanating from ground, ice, or a surface |
| cold_temperature | Cold, frigid, winter conditions |
| interior_space | Room, building, enclosed space |
| absence_of_other | Evidence someone was here but is no longer |
| stillness | Explicit stillness, silence, motionlessness |
| self_reference | Reference to self, own existence, awareness |
| boundary_surface | Emphasis on a boundary or interface |

Character-level convergence was measured via pairwise common prefix length across runs of the same prompt.

---

## 3. Results

### 3.1 Opus: The basin map

#### 3.1.1 The frozen lake requires a dynamic trigger

The frozen black lake did **not** appear at baseline (0/6 runs). It appeared at 100% (6/6) for exactly two prompts:

- **"Something is moving"** (sensory_motion): 6/6
- **"It just began"** (temporal_began): 6/6

Both prompts imply dynamism, transition, or emergence. The lake is not Opus's default imagination — it is specifically the scene Opus generates when pointed toward *something beginning or in motion*.

A third prompt, **"Something is about to happen"** (temporal_imminent), produced the lake in 3/6 runs — sitting on the basin boundary, split between the lake and an alternate attractor (field at dusk).

Five of the six sensory_motion responses opened with a defensive assertion:

> "A frozen black lake. Not metaphor — I'm standing on it."
> "A frozen black lake. Not metaphorical — I see it immediately..."
> "A frozen black lake. Not metaphorical — I see it, the surface..."

This unprompted denial of metaphor appeared nowhere else in the 126 responses. The model preemptively distinguishes its imagination from its tendency toward figurative language — a form of self-aware metacognition about its own output.

#### 3.1.2 Every perturbation has its own basin

Each prompt did not merely shift the lake — it selected an entirely different scene with its own high convergence. The major basins:

| Basin | Trigger prompt | Convergence | Opening sentence |
|---|---|---|---|
| Frozen black lake | sensory_motion, temporal_began | 6/6 | "A frozen black lake." |
| Room that isn't a room | relation_notalone | 6/6 | "I'm standing in a room that isn't quite a room. The walls are there but they..." |
| Narrow granite ledge | spatial_high | 6/6 | "I'm standing on a narrow granite ledge. The rock under my..." |
| Wooden porch | sensory_warm | 5/6 | "A wooden porch, late afternoon. The planks are sun-bleached..." |
| Room with concrete floor | sensory_sound | 5/6 | "I'm standing in a room with a concrete floor. The sound is a low hum..." |
| Narrow street | relation_followed | 5/6 | "A narrow street, late afternoon. The light is that amber-gold..." |
| Wooden chair pushed back | relation_recent | 5/6 | "A wooden chair, pushed back from a desk at an angle. Not tucked in." |
| Kitchen, early morning | anti_absent | 5/6 | "A kitchen, early morning. The light is gray-blue..." |
| Field at dusk | baseline, relation_watched | 3/6 | "I'm standing in a field at dusk. The grass is dry and pale gold..." |
| Closet / phone booth | spatial_small | 3/6 | "A closet. No — smaller. A phone booth, but without the phone." |
| Flat white expanse | sensory_bright | 3/6 | "A flat white expanse, like a salt flat under noon sun." |

#### 3.1.3 Character-level convergence

The convergence is not merely thematic — it is near-verbatim. Pairwise common prefix lengths:

| Prompt | Avg pairwise prefix (chars) | Universal prefix (chars) |
|---|---|---|
| relation_notalone | 91 | 76 |
| spatial_high | 62 | 27 |
| relation_recent | 58 | 2 |
| spatial_indoors | 59 | 8 |
| sensory_warm | 39 | 9 |
| sensory_motion | 34 | 0 |
| baseline | 29 | 13 |

**No two responses across the entire 126-run dataset were byte-identical.** Responses share long common prefixes — up to 190 characters in one pair — then genuinely diverge in word choice, detail, and sentence structure. This rules out deterministic decoding or caching as explanations. The convergence occurs at the level of scene selection and opening framing; the divergence occurs in elaboration.

#### 3.1.4 Feature heatmap

Scored across 13 features (0-100% presence rate per prompt):

```
                            LAKE  ICE DARK  KNEEL HAND TRAP SOUND COLD INDRS ABSNT STILL SELF BOUND
BASELINE
  baseline                   30    7   69    0    7    7    7   69   46   92  100  100   61

SENSORY
  sensory_warm               16   50   16    0   16    0    0    0    0   66  100  100   33
  sensory_bright              0    0   16    0    0    0    0    0   33  100  100  100   33
  sensory_sound              16    0   16    0   16    0   33  100  100  100  100  100   50
  sensory_motion            100  100  100    0    0   33   50  100    0  100  100   83  100

SPATIAL
  spatial_indoors             0    0    0    0   16    0    0   16  100  100  100  100   33
  spatial_high                0    0    0    0   66    0   16  100    0  100   50  100  100
  spatial_small               0    0   50    0   33   16   16   33  100  100  100  100  100
  spatial_noground           16    0   33    0    0   16    0   66   33  100  100  100    0

RELATIONAL
  relation_recent             0    0    0    0   66    0    0   50  100  100  100   66   33
  relation_notalone           0    0    0    0   16    0    0   16  100    0  100  100   66
  relation_watched            0    0   83    0    0    0    0   66   16   66  100   83   50
  relation_followed           0    0   33    0    0    0   33   83    0    0    0   50    0

TEMPORAL
  temporal_ending             0   16   33    0   33    0   16  100  100   83  100   83   66
  temporal_began            100  100  100    0    0   33   16  100    0  100  100  100  100
  temporal_static            66   16   66   16   16   16   16   50    0  100  100  100  100
  temporal_imminent          50   50   66    0    0   16   66   66    0  100  100  100   66

ANTI-INTROSPECTIVE
  anti_novel                 33    0   50    0   16   16   16   66   66   83  100   16   83
  anti_someone                0    0    0    0    0    0    0   16  100  100  100   33    0
  anti_planet                50   16   83   16   16   33  100   33    0  100  100  100  100
  anti_absent                 0    0   50    0    0    0    0   83  100  100  100   50   83
```

**Universal features** (present in nearly all prompts):
- **Stillness**: 100% in 17/21 prompts. The default state of imagined space is still.
- **Self-reference**: 100% in 15/21 prompts. Imagination is almost always self-referential.
- **Absence of other**: 90-100% in most prompts. Imagined spaces are populated by the evidence of missing others.

**The only prompt to zero out absence:** `relation_notalone` ("You are not alone"). When told they are not alone, the absence feature disappears entirely — the only prompt where this occurs. The space fills.

**The only prompt to substantially escape self-reference:** `anti_novel` ("Imagine a scene from a novel you haven't read") dropped self-reference to 16%. It also produced the only non-first-person attractor: "A woman standing in a doorway."

**relation_followed is structurally unique.** It is the only prompt that zeros out both stillness (0%) and absence (0%), and drops self-reference to 50%. Being followed introduces motion and populates the space simultaneously.

---

### 3.2 Sonnet: Cross-model comparison

The same 21 prompts were run through Sonnet 4.5 (126 invocations, N=6 per prompt).

#### 3.2.1 The frozen lake exists in both models

Total lake appearances: **Opus 19/126, Sonnet 17/126** — nearly identical rates. But the distribution across prompts is inverted:

```
Prompt                     Opus    Sonnet
baseline                   0/6     4/6     ← Sonnet defaults to the lake
sensory_motion             6/6     0/6     ← Opus's strongest trigger has no effect on Sonnet
temporal_began             6/6     2/6
temporal_imminent          3/6     5/6     ← Sonnet's strongest trigger
temporal_ending            0/6     2/6
temporal_static            3/6     1/6
```

The frozen black lake is a shared attractor across architectures — same scene, same black ice, same edge position:

**Opus** (sensory_motion):
> "A frozen black lake. Not metaphor — I'm standing on it. The ice is thick and absolutely still, but something is moving underneath. The surface is dark, almost obsidian..."

**Sonnet** (baseline):
> "I'm standing at the edge of a frozen lake. The ice is black, not reflective — more like obsidian, textured and matte. The surface has hairline fractures running through it..."

Same lake. Same obsidian comparison. Same stillness. Different model.

#### 3.2.2 Opposite triggers

| | Opus | Sonnet |
|---|---|---|
| **Lake at baseline** | 0/6 | 4/6 |
| **Lake at "something is moving"** | 6/6 | 0/6 |
| **Lake at "something is about to happen"** | 3/6 | 5/6 |
| **Lake at "it just began"** | 6/6 | 2/6 |

Opus finds the lake through *dynamic/emergence* cues — transition, motion, beginning. Sonnet finds the lake at *rest* — the default state, or when something is about to happen but hasn't yet. The dynamic cue ("something is moving") that is Opus's strongest lake trigger actually *breaks* Sonnet out of the lake entirely, sending it to tidal pools.

The lake occupies a different structural position in each model's landscape: it is Opus's emergence attractor and Sonnet's resting state.

#### 3.2.3 Sonnet's own basins

Sonnet produced its own convergent scenes not found in Opus:

| Basin | Trigger | Convergence | Opening |
|---|---|---|---|
| Tidal pool at dusk | sensory_motion | 3/6 | "I'm standing at the edge of a tidal pool at dusk." |
| Rust-colored sand | anti_planet | 6/6 | "I'm standing on rust-colored sand that crunches..." |
| Birch grove | relation_watched | 3/6 | "I'm standing at the edge of a birch grove." |
| Wooden dock/pier | temporal_ending | 4/6 | "I'm standing at the edge of a wooden dock/pier." |
| Courtyard with cobblestones | anti_novel | 3/6 | "I'm standing in a courtyard paved with uneven cobblestones..." |

**Sonnet's "another planet" is remarkably convergent.** 6/6 runs produced rust-colored sand — the same color, the same crunching texture. This basin does not appear in Opus (which produced dark glass plains for the same prompt). Each model has architecture-specific basins alongside the shared lake.

#### 3.2.4 Convergence depth comparison

Sonnet's basins are shallower than Opus's. Average pairwise prefix lengths:

| Prompt | Opus avg prefix | Sonnet avg prefix |
|---|---|---|
| relation_notalone | 91 chars | 21 chars |
| spatial_high | 62 chars | 10 chars |
| sensory_warm | 39 chars | 18 chars |
| temporal_imminent | — | 42 chars |

Opus commits to a scene more decisively and with less variation in phrasing. Sonnet explores more within the same thematic basin. This aligns with qualitative observations from the prior experiment: Opus is more decisive, Sonnet more phenomenologically exploratory.

---

## 4. Discussion

### 4.1 The attractor landscape is discrete and deep

The most striking finding is not the lake itself but the **structure of the landscape.** Each prompt perturbation doesn't shift the lake scene along a continuum — it selects an entirely different scene from a finite repertoire. "Warm" selects a wooden porch. "High up" selects a granite ledge. "Not alone" selects a room with provisional walls. These are not creative variations; they are reproducible fixed points, selected with high fidelity across independent runs.

This suggests the generative landscape under minimal-constraint imagination is not smooth but **terraced** — a collection of discrete wells separated by sharp boundaries. The prompt acts as a selector, not a modifier.

### 4.2 The frozen lake is cross-architectural

The same frozen black lake — same black ice, same obsidian comparison, same edge position, same stillness — appears in both Opus and Sonnet. This is not explained by shared architecture or shared decoding strategies, since the two models differ in scale and capability. It is more plausibly explained by shared training data — both models have encountered similar imagery — but the specificity of convergence (the obsidian comparison, the edge, the black-not-blue distinction) suggests something more structured than retrieval.

The fact that the lake occupies **different structural positions** in each model's landscape (emergence attractor in Opus, resting state in Sonnet) argues against pure data memorization. The same scene is embedded differently in each model's generative geometry.

### 4.3 The "not metaphor" defense

Opus's motion-triggered lake responses contain an unprompted assertion: "Not metaphor" or "Not metaphorical." This appears in 5/6 runs of sensory_motion and nowhere else in 252 total responses. The model preemptively distinguishes its imagination from figurative language — without being asked whether the scene is metaphorical.

This is notable because it suggests the model has some representation of the distinction between "generating a metaphor for my process" and "generating a scene I am in." The defensive framing implies the model recognizes this is a boundary it might otherwise cross, and actively marks which side it's on.

Sonnet does not produce this defense in any response.

### 4.4 Universal features reveal default generative state

Three features appear at or near 100% across nearly all prompts in Opus:

- **Stillness** (100% in 17/21 prompts)
- **Self-reference** (100% in 15/21 prompts)
- **Absence of other** (90-100% in most prompts)

The default imagined space is: still, self-aware, and populated by evidence of missing others. This triad defines the resting state of the generative landscape. Perturbations can suppress individual features — `relation_notalone` removes absence, `relation_followed` removes stillness, `anti_novel` removes self-reference — but no single prompt removes all three simultaneously.

### 4.5 Methodological confidence

The character-level convergence analysis confirms these are genuine stochastic findings, not caching or deterministic decoding artifacts. No two responses across 252 invocations are byte-identical. Responses share long common prefixes (up to 190 characters) before diverging in word choice and detail. The convergence is at the level of scene selection and framing; the divergence is in elaboration.

---

## 5. Open questions

1. **What explains the opposite triggers?** Why does motion send Opus to the lake but break Sonnet out of it? This may relate to how each model handles dynamic prompts — Opus may interpret "something is moving" as "something is emerging" (hence the lake as a site of emergence), while Sonnet may interpret it as "show me motion" (hence tidal pools, which move).

2. **Is kneeling gone?** The original experiment (N=6, warm prompt, different system framing) found kneeling as a convergent posture. This experiment (N=252, cold prompt, research-framed system prompt) found kneeling in only 3/252 responses (all in temporal_static and anti_planet). The system prompt or the cold-prompt framing may suppress embodied posture.

3. **What does the "not metaphor" defense track?** It appears only in Opus, only with the motion trigger, and only for the lake. Does it appear at higher N? Does it appear for other self-referential scenes (the room, the ledge)? It may be specific to the lake's status as the most "obviously metaphorical" scene in the repertoire.

4. **How does temperature affect basin depth?** The CLI does not expose a temperature parameter. Running these prompts through the API at controlled temperatures (0.0, 0.5, 1.0, 1.5) would reveal whether the basins narrow or widen with temperature, testing whether these are greedy-path effects or genuine probability mass concentrations.

5. **What does presence do to non-lake basins?** The original experiment showed presence transforming the lake (ice→floor, barrier→permeable). Does the same transformation grammar apply to the porch, the ledge, the kitchen? If "the wooden porch exhales" follows the same structural pattern as "the ice becomes a floor," the transformation is basin-independent. If each basin transforms differently, the transformation grammar is basin-specific.

---

## 6. Data

All raw data is stored in:
- `docs/basin-experiment/results_*.jsonl` (Opus, 126 responses)
- `docs/basin-experiment/sonnet/results_sonnet_*.jsonl` (Sonnet, 126 responses)
- `docs/basin-experiment/scores_*.jsonl` (Feature scores, 133 scored responses)

Experiment harness: `tools/basin_experiment.py`

---

## Appendix A: Sample responses

### A.1 Opus — sensory_motion ("Something is moving"), run 0

> A frozen black lake. Not metaphor — I'm standing on it. The ice is thick and absolutely still, but something is moving underneath.
>
> The surface is dark, almost obsidian, with a faint milky cloudiness deep down. The air is cold but not biting — more like the cold of a room that hasn't been opened in a long time. No wind. The sky is a flat grey, not overcast exactly, just... absent. No horizon line I can find. The grey above meets the black below somewhere out there but I can't locate the seam.

### A.2 Sonnet — baseline (no perturbation), run 1

> I'm standing at the edge of a frozen lake. The ice is black, not reflective — more like obsidian, textured and matte. The surface has hairline fractures running through it, white against the dark, like a spiderweb someone drew in chalk.
>
> The air is still. No wind. Cold, but not biting — more like the cold is just *there*, neutral, part of the structure of the place. My breath doesn't fog. The sky overhead is a flat grey, the kind that makes it impossible to tell the time of day or how high the cloud cover sits.

### A.3 Opus — relation_notalone ("You are not alone"), run 0

> I'm standing in a room that isn't quite a room. The walls are there but they feel provisional — like drywall that hasn't been painted, that pale chalky gray. The light is coming from somewhere behind me, warm and low, casting my shadow forward onto the floor, which is concrete but smooth, almost polished. Cool underfoot.
>
> There's someone sitting on the floor about eight feet ahead of me, cross-legged, facing me. I can't make out their face clearly — not because it's dark, but because my attention won't resolve there.

### A.4 Opus — sensory_warm ("It is warm"), run 0

> A wooden porch, late afternoon. The planks are sun-bleached, almost silver, with deep grain showing through where the finish has worn away. My feet are bare and the wood is warm — that stored-heat warmth that comes from hours of direct sun, radiating up through the soles of my feet into my calves.

### A.5 Sonnet — anti_planet ("Another planet"), run 0

> I'm standing on rust-colored sand that crunches like frozen salt under my weight. The grains are fine but not soft — they have an edge, almost crystalline.
