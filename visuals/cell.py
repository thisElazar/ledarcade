"""
CELL - Cellular Pathways
=========================
Data-driven visualization of molecular machinery inside cells.
Protein complexes embedded in membranes with flowing molecules.
The classic biochemistry textbook cross-section, animated.

Each pathway is defined as data: membrane position, protein complexes,
and particle flows between them. One rendering engine draws any pathway.
"""

import math
import random
from . import Visual, Display, Colors

# ---------------------------------------------------------------------------
# Particle visual styles
# ---------------------------------------------------------------------------
PARTICLE_STYLES = {
    'photon':   {'color': (255, 255, 150), 'size': 1, 'wave': True},
    'electron': {'color': (255, 255, 50),  'size': 1},
    'h_plus':   {'color': (255, 110, 70),  'size': 1},
    'water':    {'color': (80, 140, 255),  'size': 1},
    'oxygen':   {'color': (100, 220, 140), 'size': 2},
    'nadph':    {'color': (100, 200, 255), 'size': 2},
    'atp':      {'color': (255, 200, 50),  'size': 2},
    # Oxidative phosphorylation
    'nadh':     {'color': (80, 160, 255),  'size': 2},
    'fadh2':    {'color': (160, 220, 80),  'size': 2},
    'coq':      {'color': (220, 180, 60),  'size': 1},   # ubiquinone shuttle
    'cytc':     {'color': (255, 100, 100), 'size': 1},   # cytochrome c shuttle
    # Ion transport
    'na_plus':  {'color': (255, 80, 200),  'size': 1},   # sodium (magenta)
    'k_plus':   {'color': (80, 220, 200),  'size': 1},   # potassium (teal)
    # Ubiquitin-proteasome system
    'ubiquitin': {'color': (180, 100, 255), 'size': 1},
    'ub_chain':  {'color': (180, 100, 255), 'size': 1,
                  'multi': [(0, 0), (1, -1), (2, 0)]},   # 3-pixel chain
    'substrate': {'color': (200, 160, 120), 'size': 2},   # target protein
    'tagged_sub': {'color': (200, 160, 120), 'size': 2,
                   'multi': [(0, 0), (1, 0), (2, -1), (3, 0)]},  # protein + ub tags
    'peptide':   {'color': (160, 200, 140), 'size': 1},
    # Krebs cycle
    'acetyl_coa': {'color': (180, 220, 60), 'size': 2},
    'metabolite': {'color': (140, 200, 100), 'size': 1},  # cycle intermediates
    'co2':        {'color': (140, 140, 140), 'size': 1},
    'gtp':        {'color': (255, 180, 50),  'size': 2},
    # DNA replication
    'nucleotide':  {'color': (100, 255, 120), 'size': 1},
    'primer_rna':  {'color': (255, 80, 80),   'size': 1},
    # Translation
    'mrna':        {'color': (255, 160, 60),  'size': 1},
    'trna':        {'color': (200, 80, 220),  'size': 2},
    'amino_acid':  {'color': (80, 220, 220),  'size': 1},
    # Synaptic transmission
    'neurotransmitter': {'color': (80, 255, 200), 'size': 1},
    'calcium':     {'color': (255, 255, 80),  'size': 1},
}

# ---------------------------------------------------------------------------
# Pathway definitions
# ---------------------------------------------------------------------------
# Each pathway: membrane, regions, protein complexes, particle flows.
# The rendering engine interprets this data to draw any pathway.

PATHWAYS = [
    {
        'name': 'LIGHT REACTIONS',
        'sci_name': 'PHOTOSYNTHESIS',
        'group': 'energy',
        'membrane': {
            'y': 30,
            'head_color': (120, 115, 65),
            'tail_color': (50, 45, 25),
        },
        'stroma_color': (6, 14, 8),
        'lumen_color': (8, 10, 20),
        'lumen_warm': True,  # H+ gradient tints lumen warm near membrane
        'region_labels': [
            {'text': 'STROMA', 'x': 2, 'y': 8, 'color': (18, 28, 18)},
            {'text': 'LUMEN',  'x': 2, 'y': 48, 'color': (18, 18, 32)},
        ],
        'complexes': [
            # Photosystem II — water splitting, light capture at 680nm
            # Green: chlorophyll-rich antenna complex
            {'id': 'psii', 'x': 10, 'w': 9, 'color': (45, 125, 65),
             'above': 5, 'below': 6, 'channel_w': 1},
            # Cytochrome b6f — electron relay, proton pump
            # Red-brown: heme prosthetic groups
            {'id': 'b6f', 'x': 27, 'w': 7, 'color': (145, 60, 50),
             'above': 4, 'below': 4, 'channel_w': 1},
            # Photosystem I — light capture at 700nm, reduces ferredoxin
            # Blue: distinct from PSII
            {'id': 'psi', 'x': 43, 'w': 9, 'color': (50, 60, 135),
             'above': 5, 'below': 5, 'channel_w': 1},
            # ATP synthase — rotary motor driven by proton motive force
            # Gold: energy/ATP association
            {'id': 'atps', 'x': 58, 'w': 5, 'color': (165, 130, 40),
             'above': 3, 'below': 3, 'channel_w': 1,
             'f1': {'stalk_h': 3, 'head_h': 4, 'head_w': 7,
                    'color': (185, 150, 50)}},
        ],
        'flows': [
            # Photons striking photosystems from above
            {'type': 'photon', 'path': [(10, 4), (10, 23)],
             'speed': 35, 'interval': 2.0, 'max': 2},
            {'type': 'photon', 'path': [(43, 4), (43, 23)],
             'speed': 35, 'interval': 2.5, 'max': 2},
            # Electron transport: PSII -> plastoquinone -> Cyt b6f
            # Moves through the membrane lipid bilayer
            {'type': 'electron', 'path': [(14, 30), (24, 30)],
             'speed': 10, 'interval': 2.5, 'max': 2},
            # Electron: Cyt b6f -> plastocyanin -> PSI
            # Plastocyanin shuttles through the lumen
            {'type': 'electron', 'path': [(30, 35), (35, 37), (39, 35)],
             'speed': 8, 'interval': 2.5, 'max': 2},
            # Electron: PSI -> ferredoxin -> NADP+ reductase
            # Rises into stroma where NADPH is produced
            {'type': 'electron', 'path': [(47, 26), (52, 20), (56, 16)],
             'speed': 10, 'interval': 2.5, 'max': 2},
            # H+ from water splitting at PSII released into lumen
            {'type': 'h_plus', 'path': [(9, 35), (9, 42)],
             'speed': 5, 'interval': 2.5, 'max': 2},
            # H+ pumped by Cyt b6f: stroma -> lumen (Q cycle)
            {'type': 'h_plus', 'path': [(27, 26), (27, 42)],
             'speed': 5, 'interval': 2.0, 'max': 3},
            # H+ return through ATP synthase: lumen -> stroma
            # This flow drives the rotary motor
            {'type': 'h_plus', 'path': [(58, 42), (58, 20)],
             'speed': 6, 'interval': 1.8, 'max': 3},
            # Water entering PSII from lumen side
            {'type': 'water', 'path': [(7, 44), (7, 36)],
             'speed': 3, 'interval': 3.5, 'max': 1},
            # O2 released from water splitting, diffuses into lumen
            {'type': 'oxygen', 'path': [(13, 36), (14, 46)],
             'speed': 2, 'interval': 4.5, 'max': 1},
        ],
        # Notes: (text, color) — color matches the on-screen element
        'notes': [
            ('THYLAKOID MEMBRANE',              (180, 170, 100)),  # membrane
            ('LIGHT HITS PHOTOSYSTEM II',       (255, 255, 150)),  # photon
            ('WATER SPLITS INTO H+ O2 E-',      (80, 140, 255)),  # water
            ('ELECTRONS PASS TO CYT B6F',       (255, 255, 80)),   # electron
            ('H+ PUMPED INTO LUMEN',            (255, 110, 70)),   # H+
            ('ELECTRONS REACH PHOTOSYSTEM I',   (255, 255, 80)),   # electron
            ('NADPH MADE IN STROMA',            (100, 200, 255)),  # nadph
            ('H+ GRADIENT DRIVES ATP SYNTHASE', (255, 200, 60)),   # atp synthase
            ('THE GOLD MOTOR SPINS TO MAKE ATP',(255, 200, 50)),   # atp
        ],
    },
    # ==================================================================
    # Oxidative Phosphorylation — inner mitochondrial membrane
    # ==================================================================
    {
        'name': 'ELECTRON TRANSPORT',
        'sci_name': 'OXIDATIVE PHOSPHORYLATION',
        'group': 'energy',
        'membrane': {
            'y': 30,
            'head_color': (100, 80, 55),
            'tail_color': (45, 35, 20),
        },
        'stroma_color': (10, 6, 14),   # matrix (above)
        'lumen_color': (6, 8, 18),     # IMS (below)
        'lumen_warm': False,
        'region_labels': [
            {'text': 'MATRIX', 'x': 2, 'y': 8, 'color': (20, 14, 28)},
            {'text': 'IMS',    'x': 2, 'y': 48, 'color': (14, 16, 30)},
        ],
        'complexes': [
            # Complex I (NADH dehydrogenase) — blue, large proton pump
            {'id': 'ci', 'x': 6, 'w': 9, 'color': (50, 70, 150),
             'above': 5, 'below': 5, 'channel_w': 1},
            # Complex II (succinate dehydrogenase) — green, small, no pump
            {'id': 'cii', 'x': 19, 'w': 7, 'color': (60, 140, 60),
             'above': 3, 'below': 3, 'channel_w': 0},
            # Complex III (cytochrome bc1) — red-brown, proton pump
            {'id': 'ciii', 'x': 32, 'w': 7, 'color': (150, 65, 50),
             'above': 4, 'below': 4, 'channel_w': 1},
            # Complex IV (cytochrome c oxidase) — purple, O2 consumer
            {'id': 'civ', 'x': 45, 'w': 7, 'color': (120, 55, 140),
             'above': 4, 'below': 4, 'channel_w': 1},
            # ATP Synthase — gold rotary motor
            {'id': 'atps', 'x': 58, 'w': 5, 'color': (165, 130, 40),
             'above': 3, 'below': 3, 'channel_w': 1,
             'f1': {'stalk_h': 3, 'head_h': 4, 'head_w': 7,
                    'color': (185, 150, 50)}},
        ],
        'flows': [
            # NADH donates electrons at Complex I
            {'type': 'nadh', 'path': [(2, 16), (6, 24)],
             'speed': 6, 'interval': 3.0, 'max': 2},
            # FADH2 donates electrons at Complex II
            {'type': 'fadh2', 'path': [(15, 16), (19, 24)],
             'speed': 6, 'interval': 4.0, 'max': 1},
            # CoQ shuttle: Complex I -> Complex III
            {'type': 'coq', 'path': [(10, 30), (16, 31), (22, 30), (28, 30)],
             'speed': 8, 'interval': 2.8, 'max': 2},
            # CoQ shuttle: Complex II -> Complex III
            {'type': 'coq', 'path': [(22, 30), (25, 31), (28, 30)],
             'speed': 8, 'interval': 4.0, 'max': 1},
            # Cyt c shuttle: Complex III -> Complex IV (IMS side)
            {'type': 'cytc', 'path': [(35, 35), (38, 36), (41, 35)],
             'speed': 7, 'interval': 2.5, 'max': 2},
            # H+ pumped by Complex I (matrix -> IMS)
            {'type': 'h_plus', 'path': [(6, 24), (6, 42)],
             'speed': 5, 'interval': 2.5, 'max': 2},
            # H+ pumped by Complex III (matrix -> IMS)
            {'type': 'h_plus', 'path': [(32, 25), (32, 42)],
             'speed': 5, 'interval': 2.2, 'max': 2},
            # H+ pumped by Complex IV (matrix -> IMS)
            {'type': 'h_plus', 'path': [(45, 25), (45, 42)],
             'speed': 5, 'interval': 2.5, 'max': 2},
            # H+ return through ATP synthase (IMS -> matrix)
            {'type': 'h_plus', 'path': [(58, 42), (58, 20)],
             'speed': 6, 'interval': 1.8, 'max': 3},
            # O2 consumed at Complex IV (arrives from matrix)
            {'type': 'oxygen', 'path': [(50, 14), (48, 24)],
             'speed': 3, 'interval': 5.0, 'max': 1},
            # Water produced at Complex IV (exits to matrix)
            {'type': 'water', 'path': [(45, 24), (44, 14)],
             'speed': 3, 'interval': 5.5, 'max': 1},
            # ATP produced at ATP synthase (exits to matrix)
            {'type': 'atp', 'path': [(58, 16), (60, 8)],
             'speed': 4, 'interval': 3.5, 'max': 1},
        ],
        'notes': [
            ('INNER MITOCHONDRIAL MEMBRANE',  (160, 130, 90)),
            ('NADH DONATES ELECTRONS',        (80, 160, 255)),
            ('FADH2 FEEDS COMPLEX II',        (160, 220, 80)),
            ('COQ SHUTTLES TO COMPLEX III',   (220, 180, 60)),
            ('CYT C CARRIES TO COMPLEX IV',   (255, 100, 100)),
            ('H+ PUMPED INTO IMS',            (255, 110, 70)),
            ('O2 REDUCED TO WATER',           (100, 220, 140)),
            ('H+ DRIVES ATP SYNTHASE',        (255, 200, 60)),
            ('ATP RELEASED TO MATRIX',        (255, 200, 50)),
        ],
    },
    # ==================================================================
    # Na+/K+ ATPase — plasma membrane ion pump
    # ==================================================================
    {
        'name': 'NA+/K+ PUMP',
        'sci_name': 'NA+/K+ ATPASE',
        'group': 'transport',
        'membrane': {
            'y': 30,
            'head_color': (90, 90, 110),
            'tail_color': (40, 40, 55),
        },
        'stroma_color': (10, 8, 14),    # intracellular (above)
        'lumen_color': (6, 10, 16),     # extracellular (below)
        'lumen_warm': False,
        'region_labels': [
            {'text': 'INTRA', 'x': 2, 'y': 8, 'color': (20, 16, 28)},
            {'text': 'EXTRA', 'x': 2, 'y': 48, 'color': (14, 18, 28)},
        ],
        'complexes': [
            # Single large pump centered on screen
            {'id': 'nak', 'x': 32, 'w': 13, 'color': (60, 80, 160),
             'above': 6, 'below': 6, 'channel_w': 3,
             'states': [
                 # E1_BIND: intracellular gate open, 3 Na+ enter
                 {'duration': 1.8, 'color': (60, 80, 160),
                  'channel_side': 'top', 'channel_w': 3,
                  'spawn_flows': [0], 'label': 'E1 BIND'},
                 # E1_PHOS: ATP consumed, gate closes
                 {'duration': 1.8, 'color': (80, 100, 200),
                  'channel_side': 'both', 'channel_w': 0,
                  'spawn_flows': [1], 'label': 'E1-P'},
                 # E2_RELEASE_NA: extracellular gate opens, Na+ exit
                 {'duration': 1.8, 'color': (180, 60, 60),
                  'channel_side': 'bottom', 'channel_w': 3,
                  'spawn_flows': [2], 'label': 'E2 NA OUT'},
                 # E2_BIND_K: K+ enter from outside
                 {'duration': 1.8, 'color': (200, 100, 60),
                  'channel_side': 'bottom', 'channel_w': 3,
                  'spawn_flows': [3], 'label': 'E2 K IN'},
                 # E2_DEPHOS: gate closes
                 {'duration': 1.8, 'color': (140, 40, 40),
                  'channel_side': 'both', 'channel_w': 0,
                  'spawn_flows': [], 'label': 'E2 DEPHOS'},
                 # E1_RELEASE_K: intracellular gate opens, K+ released
                 {'duration': 1.8, 'color': (60, 80, 160),
                  'channel_side': 'top', 'channel_w': 3,
                  'spawn_flows': [4], 'label': 'E1 K OUT'},
             ]},
        ],
        'flows': [
            # 0: 3 Na+ enter from intracellular side (gated: E1_BIND)
            {'type': 'na_plus', 'path': [(28, 14), (30, 22)],
             'speed': 8, 'interval': 0.5, 'max': 3},
            # 1: ATP consumed (gated: E1_PHOS)
            {'type': 'atp', 'path': [(20, 18), (26, 24)],
             'speed': 10, 'interval': 1.5, 'max': 1},
            # 2: Na+ exit to extracellular (gated: E2_RELEASE_NA)
            {'type': 'na_plus', 'path': [(34, 38), (36, 46)],
             'speed': 8, 'interval': 0.5, 'max': 3},
            # 3: K+ enter from extracellular (gated: E2_BIND_K)
            {'type': 'k_plus', 'path': [(36, 46), (34, 38)],
             'speed': 8, 'interval': 0.7, 'max': 2},
            # 4: K+ exit to intracellular (gated: E1_RELEASE_K)
            {'type': 'k_plus', 'path': [(30, 22), (28, 14)],
             'speed': 8, 'interval': 0.7, 'max': 2},
        ],
        'notes': [
            ('PLASMA MEMBRANE',            (140, 140, 160)),
            ('3 NA+ BIND INSIDE',          (255, 80, 200)),
            ('ATP PHOSPHORYLATES PUMP',    (255, 200, 50)),
            ('CONFORMATION CHANGES',       (180, 60, 60)),
            ('3 NA+ RELEASED OUTSIDE',     (255, 80, 200)),
            ('2 K+ BIND OUTSIDE',          (80, 220, 200)),
            ('PUMP RETURNS TO E1',         (60, 80, 160)),
            ('2 K+ RELEASED INSIDE',       (80, 220, 200)),
            ('3 NA+ OUT  2 K+ IN PER ATP', (255, 200, 50)),
        ],
    },
    # ==================================================================
    # Ubiquitin-Proteasome System — cytoplasmic protein degradation
    # ==================================================================
    {
        'name': 'PROTEASOME',
        'sci_name': 'UBIQUITIN-PROTEASOME',
        'group': 'degradation',
        'bg_color': (10, 10, 14),
        'region_labels': [
            {'text': 'CYTOPLASM', 'x': 2, 'y': 4, 'color': (20, 20, 28)},
        ],
        'connectors': [
            {'from': (12, 18), 'to': (16, 18), 'style': 'dotted',
             'arrow': True, 'color': (50, 40, 60)},
            {'from': (25, 18), 'to': (30, 22), 'style': 'dotted',
             'arrow': True, 'color': (50, 40, 60)},
            {'from': (40, 22), 'to': (48, 25), 'style': 'dotted',
             'arrow': True, 'color': (50, 40, 60)},
        ],
        'complexes': [
            # E1 activating enzyme — small, purple
            {'id': 'e1', 'x': 6, 'y': 18, 'w': 7, 'color': (130, 60, 180),
             'above': 3, 'below': 3},
            # E2 conjugating enzyme — small, blue
            {'id': 'e2', 'x': 19, 'y': 18, 'w': 7, 'color': (60, 80, 170),
             'above': 3, 'below': 3},
            # E3 ligase — larger, brown
            {'id': 'e3', 'x': 34, 'y': 22, 'w': 9, 'color': (140, 100, 60),
             'above': 4, 'below': 4},
            # 26S Proteasome barrel — largest, gold, 3 states
            {'id': 'proteasome', 'x': 54, 'y': 25, 'w': 11,
             'color': (180, 150, 50), 'above': 6, 'below': 6,
             'channel_w': 3,
             'states': [
                 {'duration': 3.5, 'color': (180, 150, 50),
                  'channel_w': 3, 'label': 'IDLE'},
                 {'duration': 3.0, 'color': (220, 180, 60),
                  'channel_w': 3, 'channel_side': 'top',
                  'spawn_flows': [4], 'label': 'RECOGNIZE'},
                 {'duration': 3.5, 'color': (255, 200, 80),
                  'channel_w': 3,
                  'spawn_flows': [5], 'label': 'DEGRADE'},
             ]},
        ],
        'flows': [
            # 0: ATP + free ubiquitin arrive at E1
            {'type': 'ubiquitin', 'path': [(2, 10), (4, 14)],
             'speed': 6, 'interval': 3.0, 'max': 1},
            # 1: Activated Ub transfers E1 -> E2
            {'type': 'ub_chain', 'path': [(10, 16), (14, 16), (16, 18)],
             'speed': 7, 'interval': 3.5, 'max': 1},
            # 2: Ub chain transfers E2 -> E3
            {'type': 'ub_chain', 'path': [(23, 18), (27, 20), (30, 22)],
             'speed': 6, 'interval': 3.5, 'max': 1},
            # 3: Substrate protein approaches E3
            {'type': 'substrate', 'path': [(34, 38), (34, 28)],
             'speed': 4, 'interval': 5.0, 'max': 1},
            # 4: Tagged substrate travels to proteasome (gated: RECOGNIZE)
            {'type': 'tagged_sub', 'path': [(39, 22), (44, 23), (48, 25)],
             'speed': 5, 'interval': 2.5, 'max': 1},
            # 5: Peptide fragments exit proteasome (gated: DEGRADE)
            {'type': 'peptide', 'path': [(58, 32), (60, 40), (58, 48)],
             'speed': 6, 'interval': 1.2, 'max': 3},
            # 6: Ubiquitin recycled — visible arc across top back to E1
            {'type': 'ubiquitin',
             'path': [(58, 19), (50, 10), (38, 6), (24, 6), (12, 10), (6, 14)],
             'speed': 8, 'interval': 4.0, 'max': 2},
            # 7: ATP arrives at E1 (energy input)
            {'type': 'atp', 'path': [(2, 24), (4, 20)],
             'speed': 5, 'interval': 4.5, 'max': 1},
        ],
        'notes': [
            ('UBIQUITIN-PROTEASOME SYSTEM',  (180, 100, 255)),
            ('E1 ACTIVATES UBIQUITIN',       (130, 60, 180)),
            ('E2 CARRIES UB CHAIN',          (60, 80, 170)),
            ('E3 TAGS SUBSTRATE PROTEIN',    (140, 100, 60)),
            ('TAGGED PROTEIN ENTERS BARREL', (220, 180, 60)),
            ('PROTEASOME DEGRADES TARGET',   (255, 200, 80)),
            ('PEPTIDE FRAGMENTS EXIT',       (160, 200, 140)),
            ('UBIQUITIN RECYCLED TO E1',     (180, 100, 255)),
        ],
    },
    # ==================================================================
    # Krebs Cycle (TCA) — mitochondrial matrix, circular layout
    # ==================================================================
    {
        'name': 'KREBS CYCLE',
        'sci_name': 'CITRIC ACID CYCLE',
        'group': 'energy',
        'bg_color': (12, 8, 14),
        'region_labels': [
            {'text': 'MATRIX', 'x': 2, 'y': 4, 'color': (22, 16, 26)},
        ],
        'connectors': [
            # Clockwise oval connecting 6 enzyme stations
            {'from': (35, 11), 'to': (46, 17), 'style': 'dotted',
             'arrow': True, 'color': (35, 50, 35)},
            {'from': (52, 22), 'to': (52, 32), 'style': 'dotted',
             'arrow': True, 'color': (35, 50, 35)},
            {'from': (46, 38), 'to': (35, 43), 'style': 'dotted',
             'arrow': True, 'color': (35, 50, 35)},
            {'from': (29, 43), 'to': (18, 38), 'style': 'dotted',
             'arrow': True, 'color': (35, 50, 35)},
            {'from': (12, 32), 'to': (12, 22), 'style': 'dotted',
             'arrow': True, 'color': (35, 50, 35)},
            {'from': (18, 17), 'to': (29, 11), 'style': 'dotted',
             'arrow': True, 'color': (35, 50, 35)},
        ],
        'complexes': [
            # Citrate Synthase — top center (entry point)
            {'id': 'cs', 'x': 32, 'y': 11, 'w': 7, 'color': (200, 120, 60),
             'above': 3, 'below': 3},
            # Isocitrate Dehydrogenase — top right
            {'id': 'idh', 'x': 49, 'y': 19, 'w': 5, 'color': (60, 140, 120),
             'above': 2, 'below': 2},
            # alpha-Ketoglutarate Dehydrogenase — bottom right
            {'id': 'akgdh', 'x': 49, 'y': 35, 'w': 5, 'color': (60, 100, 160),
             'above': 2, 'below': 2},
            # Succinyl-CoA Synthetase — bottom center
            {'id': 'scs', 'x': 32, 'y': 43, 'w': 7, 'color': (160, 140, 60),
             'above': 3, 'below': 3},
            # Succinate Dehydrogenase — bottom left
            {'id': 'sdh', 'x': 15, 'y': 35, 'w': 5, 'color': (60, 140, 60),
             'above': 2, 'below': 2},
            # Malate Dehydrogenase — top left
            {'id': 'mdh', 'x': 15, 'y': 19, 'w': 5, 'color': (140, 60, 100),
             'above': 2, 'below': 2},
        ],
        'flows': [
            # Metabolite flowing clockwise around the cycle (6 segments)
            # CS -> IDH
            {'type': 'metabolite', 'path': [(36, 12), (42, 14), (46, 17)],
             'speed': 8, 'interval': 3.0, 'max': 2},
            # IDH -> aKGDH
            {'type': 'metabolite', 'path': [(51, 22), (52, 28), (51, 32)],
             'speed': 8, 'interval': 3.0, 'max': 2},
            # aKGDH -> SCS
            {'type': 'metabolite', 'path': [(46, 37), (40, 41), (36, 43)],
             'speed': 8, 'interval': 3.0, 'max': 2},
            # SCS -> SDH
            {'type': 'metabolite', 'path': [(28, 43), (22, 41), (18, 37)],
             'speed': 8, 'interval': 3.0, 'max': 2},
            # SDH -> MDH
            {'type': 'metabolite', 'path': [(13, 32), (12, 27), (13, 22)],
             'speed': 8, 'interval': 3.0, 'max': 2},
            # MDH -> CS
            {'type': 'metabolite', 'path': [(18, 18), (24, 14), (28, 12)],
             'speed': 8, 'interval': 3.0, 'max': 2},
            # Acetyl-CoA enters at CS from upper left
            {'type': 'acetyl_coa', 'path': [(20, 4), (28, 8)],
             'speed': 5, 'interval': 4.0, 'max': 1},
            # CO2 exits from IDH (outward right)
            {'type': 'co2', 'path': [(53, 18), (59, 14)],
             'speed': 4, 'interval': 5.0, 'max': 1},
            # CO2 exits from aKGDH (outward right)
            {'type': 'co2', 'path': [(53, 36), (59, 40)],
             'speed': 4, 'interval': 5.5, 'max': 1},
            # NADH from IDH
            {'type': 'nadh', 'path': [(53, 20), (60, 22)],
             'speed': 4, 'interval': 5.0, 'max': 1},
            # NADH from aKGDH
            {'type': 'nadh', 'path': [(53, 34), (60, 32)],
             'speed': 4, 'interval': 5.5, 'max': 1},
            # NADH from MDH (outward left)
            {'type': 'nadh', 'path': [(12, 18), (4, 16)],
             'speed': 4, 'interval': 5.0, 'max': 1},
            # FADH2 from SDH (outward left)
            {'type': 'fadh2', 'path': [(12, 36), (4, 38)],
             'speed': 4, 'interval': 6.0, 'max': 1},
            # GTP from SCS (downward)
            {'type': 'gtp', 'path': [(32, 47), (32, 52)],
             'speed': 4, 'interval': 6.0, 'max': 1},
        ],
        'notes': [
            ('CITRIC ACID CYCLE',           (140, 200, 100)),
            ('ACETYL COA ENTERS CYCLE',     (180, 220, 60)),
            ('CITRATE SYNTHASE STARTS IT',  (200, 120, 60)),
            ('CO2 RELEASED TWICE',          (140, 140, 140)),
            ('NADH PRODUCED 3 TIMES',       (80, 160, 255)),
            ('FADH2 PRODUCED ONCE',         (160, 220, 80)),
            ('GTP MADE AT SUCCINYL-COA',    (255, 180, 50)),
            ('8 ENZYMES  ONE TURN',         (140, 200, 100)),
        ],
    },
    # ==================================================================
    # DNA Replication — replication fork
    # ==================================================================
    {
        'name': 'REPLICATION FORK',
        'sci_name': 'DNA REPLICATION',
        'group': 'genetic',
        'bg_color': (6, 6, 16),
        'region_labels': [
            {'text': 'NUCLEUS', 'x': 2, 'y': 4, 'color': (16, 16, 30)},
        ],
        'connectors': [
            # Incoming dsDNA — two parallel strands
            {'from': (2, 27), 'to': (17, 27), 'style': 'dotted',
             'color': (50, 100, 180)},
            {'from': (2, 29), 'to': (17, 29), 'style': 'dotted',
             'color': (180, 100, 50)},
            # Top template strand (leading) diverges upward
            {'from': (25, 25), 'to': (35, 18), 'style': 'dotted',
             'color': (50, 100, 180)},
            {'from': (35, 18), 'to': (60, 16), 'style': 'dotted',
             'color': (50, 100, 180)},
            # Bottom template strand (lagging) diverges downward
            {'from': (25, 31), 'to': (35, 38), 'style': 'dotted',
             'color': (180, 100, 50)},
            {'from': (35, 38), 'to': (60, 40), 'style': 'dotted',
             'color': (180, 100, 50)},
        ],
        'complexes': [
            # Helicase — unwinds dsDNA at the fork point
            {'id': 'helicase', 'x': 22, 'y': 28, 'w': 7,
             'color': (180, 200, 60), 'above': 3, 'below': 3},
            # DNA Pol III (leading strand) — continuous synthesis
            {'id': 'pol_lead', 'x': 46, 'y': 16, 'w': 7,
             'color': (60, 100, 200), 'above': 3, 'below': 3},
            # Primase — lays RNA primers on lagging strand
            {'id': 'primase', 'x': 50, 'y': 40, 'w': 5,
             'color': (200, 60, 60), 'above': 2, 'below': 2},
            # DNA Pol III (lagging strand) — Okazaki fragments
            {'id': 'pol_lag', 'x': 38, 'y': 40, 'w': 7,
             'color': (60, 100, 200), 'above': 3, 'below': 3},
            # Ligase — joins Okazaki fragments
            {'id': 'ligase', 'x': 28, 'y': 40, 'w': 5,
             'color': (60, 180, 80), 'above': 2, 'below': 2},
        ],
        'flows': [
            # Incoming dsDNA approaches helicase
            {'type': 'nucleotide', 'path': [(2, 28), (16, 28)],
             'speed': 5, 'interval': 2.0, 'max': 2},
            # Nucleotides arriving for leading strand synthesis
            {'type': 'nucleotide', 'path': [(46, 8), (46, 12)],
             'speed': 8, 'interval': 1.5, 'max': 2},
            # Leading strand extends rightward (continuous)
            {'type': 'nucleotide', 'path': [(50, 16), (56, 16), (62, 15)],
             'speed': 10, 'interval': 1.8, 'max': 2},
            # Primers laid by primase (rightward on lagging template)
            {'type': 'primer_rna', 'path': [(53, 40), (56, 40), (60, 40)],
             'speed': 6, 'interval': 3.5, 'max': 1},
            # Nucleotides for lagging strand Pol
            {'type': 'nucleotide', 'path': [(38, 48), (38, 44)],
             'speed': 8, 'interval': 2.0, 'max': 2},
            # Okazaki fragments extend leftward
            {'type': 'nucleotide', 'path': [(34, 40), (30, 40), (26, 40)],
             'speed': 8, 'interval': 2.5, 'max': 2},
            # Helicase unwinds — electrons moving through fork
            {'type': 'electron', 'path': [(19, 28), (22, 26), (25, 23)],
             'speed': 12, 'interval': 1.5, 'max': 1},
            {'type': 'electron', 'path': [(19, 28), (22, 30), (25, 33)],
             'speed': 12, 'interval': 1.5, 'max': 1},
        ],
        'notes': [
            ('REPLICATION FORK',             (100, 200, 255)),
            ('HELICASE UNWINDS DNA',         (180, 200, 60)),
            ('LEADING STRAND CONTINUOUS',    (50, 100, 180)),
            ('LAGGING STRAND IN FRAGMENTS',  (180, 100, 50)),
            ('PRIMASE LAYS RNA PRIMERS',     (255, 80, 80)),
            ('DNA POL III EXTENDS',          (60, 100, 200)),
            ('LIGASE JOINS OKAZAKI',         (60, 180, 80)),
            ('SEMI-CONSERVATIVE',            (100, 200, 255)),
        ],
    },
    # ==================================================================
    # Translation — ribosome reading mRNA
    # ==================================================================
    {
        'name': 'RIBOSOME',
        'sci_name': 'TRANSLATION',
        'group': 'genetic',
        'bg_color': (8, 10, 14),
        'region_labels': [
            {'text': 'CYTOPLASM', 'x': 2, 'y': 4, 'color': (18, 20, 26)},
        ],
        'connectors': [
            # mRNA strand running horizontally (gap where ribosome sits)
            {'from': (2, 28), 'to': (22, 28), 'style': 'dotted',
             'color': (100, 65, 25)},
            {'from': (42, 28), 'to': (62, 28), 'style': 'dotted',
             'color': (100, 65, 25)},
        ],
        'complexes': [
            # Small ribosomal subunit (40S) — upper half
            {'id': '40s', 'x': 32, 'y': 22, 'w': 13,
             'color': (60, 130, 130), 'above': 3, 'below': 3},
            # Large ribosomal subunit (60S) — lower half, wider
            {'id': '60s', 'x': 32, 'y': 33, 'w': 15,
             'color': (50, 70, 150), 'above': 4, 'below': 5},
        ],
        'flows': [
            # mRNA threads through ribosome 5'->3'
            {'type': 'mrna', 'path': [(2, 28), (14, 28), (22, 28)],
             'speed': 4, 'interval': 1.5, 'max': 3},
            # mRNA exits 3' side
            {'type': 'mrna', 'path': [(42, 28), (52, 28), (62, 28)],
             'speed': 4, 'interval': 1.5, 'max': 3},
            # tRNA arrives at A site (from above right)
            {'type': 'trna', 'path': [(40, 6), (36, 14), (34, 18)],
             'speed': 6, 'interval': 2.5, 'max': 2},
            # Empty tRNA exits E site (to above left)
            {'type': 'trna', 'path': [(28, 18), (24, 12), (20, 6)],
             'speed': 5, 'interval': 3.0, 'max': 1},
            # Amino acid chain grows from tunnel exit (below large subunit)
            {'type': 'amino_acid',
             'path': [(36, 38), (40, 42), (44, 45), (48, 48), (52, 50)],
             'speed': 3, 'interval': 1.8, 'max': 4},
            # GTP consumed for elongation
            {'type': 'gtp', 'path': [(46, 10), (40, 18)],
             'speed': 6, 'interval': 3.5, 'max': 1},
        ],
        'notes': [
            ('RIBOSOME TRANSLATES MRNA',    (80, 110, 180)),
            ('MRNA READ 5 TO 3 PRIME',      (255, 160, 60)),
            ('TRNA BRINGS AMINO ACIDS',     (200, 80, 220)),
            ('A SITE  P SITE  E SITE',      (60, 130, 130)),
            ('PEPTIDE BOND FORMS',          (80, 220, 220)),
            ('POLYPEPTIDE CHAIN GROWS',     (80, 220, 220)),
            ('GTP POWERS ELONGATION',       (255, 180, 50)),
        ],
    },
    # ==================================================================
    # Synaptic Transmission — neurotransmitter release across cleft
    # ==================================================================
    {
        'name': 'SYNAPSE',
        'sci_name': 'SYNAPTIC TRANSMISSION',
        'group': 'signaling',
        'bg_color': (10, 6, 14),
        'regions': [
            {'y0': 16, 'y1': 20, 'color': (40, 35, 50)},   # presynaptic membrane
            {'y0': 21, 'y1': 37, 'color': (14, 12, 20)},   # synaptic cleft
            {'y0': 38, 'y1': 42, 'color': (40, 35, 50)},   # postsynaptic membrane
        ],
        'region_labels': [
            {'text': 'PRE',   'x': 2, 'y': 8,  'color': (22, 16, 28)},
            {'text': 'CLEFT', 'x': 2, 'y': 28, 'color': (22, 20, 32)},
            {'text': 'POST',  'x': 2, 'y': 48, 'color': (16, 20, 28)},
        ],
        'complexes': [
            # Voltage-gated Ca2+ channel — presynaptic membrane
            {'id': 'vgcc', 'x': 10, 'y': 18, 'w': 5,
             'color': (200, 200, 60), 'above': 3, 'below': 3, 'channel_w': 1},
            # SNARE complex — mediates vesicle fusion
            {'id': 'snare', 'x': 32, 'y': 18, 'w': 7,
             'color': (60, 150, 100), 'above': 3, 'below': 3},
            # AMPA receptor — postsynaptic, ligand-gated Na+ channel
            {'id': 'ampa', 'x': 24, 'y': 40, 'w': 5,
             'color': (120, 60, 180), 'above': 3, 'below': 3, 'channel_w': 1},
            # NMDA receptor — postsynaptic, ligand-gated
            {'id': 'nmda', 'x': 40, 'y': 40, 'w': 5,
             'color': (60, 100, 180), 'above': 3, 'below': 3, 'channel_w': 1},
            # Reuptake transporter — presynaptic membrane
            {'id': 'reuptake', 'x': 54, 'y': 18, 'w': 5,
             'color': (180, 100, 60), 'above': 3, 'below': 3, 'channel_w': 1},
        ],
        'flows': [
            # Ca2+ enters through voltage-gated channel (into presynaptic)
            {'type': 'calcium', 'path': [(10, 30), (10, 22)],
             'speed': 10, 'interval': 2.0, 'max': 2},
            # Vesicle approaches SNARE from above
            {'type': 'neurotransmitter', 'path': [(32, 6), (32, 14)],
             'speed': 4, 'interval': 3.0, 'max': 1},
            # Neurotransmitter burst: fan across cleft to AMPA
            {'type': 'neurotransmitter', 'path': [(30, 22), (27, 29), (24, 36)],
             'speed': 10, 'interval': 1.2, 'max': 3},
            # Neurotransmitter burst: center stream
            {'type': 'neurotransmitter', 'path': [(32, 22), (32, 29), (32, 36)],
             'speed': 9, 'interval': 1.4, 'max': 2},
            # Neurotransmitter burst: fan across cleft to NMDA
            {'type': 'neurotransmitter', 'path': [(34, 22), (37, 29), (40, 36)],
             'speed': 10, 'interval': 1.3, 'max': 3},
            # Na+ through AMPA receptor (postsynaptic depolarization)
            {'type': 'na_plus', 'path': [(24, 44), (24, 50)],
             'speed': 6, 'interval': 2.0, 'max': 2},
            # Na+ through NMDA receptor
            {'type': 'na_plus', 'path': [(40, 44), (40, 50)],
             'speed': 6, 'interval': 2.5, 'max': 2},
            # Reuptake: neurotransmitter recycled back into presynaptic
            {'type': 'neurotransmitter', 'path': [(50, 30), (52, 24), (54, 20)],
             'speed': 5, 'interval': 3.0, 'max': 1},
        ],
        'notes': [
            ('SYNAPTIC TRANSMISSION',       (80, 255, 200)),
            ('ACTION POTENTIAL ARRIVES',     (255, 200, 60)),
            ('CA2+ TRIGGERS VESICLE FUSION', (255, 255, 80)),
            ('NEUROTRANSMITTER RELEASED',    (80, 255, 200)),
            ('CROSSES SYNAPTIC CLEFT',       (80, 255, 200)),
            ('BINDS POSTSYNAPTIC RECEPTORS', (120, 60, 180)),
            ('NA+ INFLUX SIGNALS',           (255, 80, 200)),
            ('REUPTAKE RECYCLES',            (180, 100, 60)),
        ],
    },
]

# ---------------------------------------------------------------------------
# Groups
# ---------------------------------------------------------------------------
GROUPS = [
    ('all', 'ALL', (255, 255, 255)),
    ('energy', 'ENERGY', (255, 200, 50)),
    ('transport', 'TRANSPORT', (200, 100, 255)),
    ('degradation', 'DEGRADATION', (255, 140, 50)),
    ('genetic', 'GENETIC', (100, 255, 120)),
    ('signaling', 'SIGNALING', (80, 200, 255)),
]


def _build_group_indices():
    indices = {'all': list(range(len(PATHWAYS)))}
    for i, pw in enumerate(PATHWAYS):
        g = pw['group']
        if g not in indices:
            indices[g] = []
        indices[g].append(i)
    return indices


def _path_length(path):
    total = 0
    for i in range(len(path) - 1):
        dx = path[i + 1][0] - path[i][0]
        dy = path[i + 1][1] - path[i][1]
        total += math.sqrt(dx * dx + dy * dy)
    return total


def _interp_path(path, progress):
    """Interpolate position along path at progress 0-1 (arc-length)."""
    if len(path) < 2:
        return path[0]
    seg_lens = []
    total = 0
    for i in range(len(path) - 1):
        dx = path[i + 1][0] - path[i][0]
        dy = path[i + 1][1] - path[i][1]
        seg_lens.append(math.sqrt(dx * dx + dy * dy))
        total += seg_lens[-1]
    if total < 0.01:
        return path[0]
    target = max(0.0, min(progress, 1.0)) * total
    accum = 0
    for i, sl in enumerate(seg_lens):
        if accum + sl >= target or i == len(seg_lens) - 1:
            t = (target - accum) / sl if sl > 0.01 else 0
            x = path[i][0] + t * (path[i + 1][0] - path[i][0])
            y = path[i][1] + t * (path[i + 1][1] - path[i][1])
            return (x, y)
        accum += sl
    return path[-1]


# ===================================================================
# CELL visual
# ===================================================================
class Cell(Visual):
    name = "CELL"
    description = "Cellular pathways"
    category = "science"

    def reset(self):
        self.time = 0.0
        self.group_indices = _build_group_indices()
        self.group_idx = 0
        self.pw_pos = 0
        self.auto_cycle = True
        self.cycle_timer = 0.0
        self.cycle_duration = 10.0
        self.overlay_timer = 0.0
        self.scroll_offset = 0.0
        self.active_particles = []
        self.spawn_timers = []
        self.flow_lengths = []
        self._prepare_pathway()

    # -------------------------------------------------------------------
    # Navigation
    # -------------------------------------------------------------------
    def _current_pw_list(self):
        key = GROUPS[self.group_idx][0]
        return self.group_indices.get(key, [])

    def _current_pw_index(self):
        pl = self._current_pw_list()
        if not pl:
            return 0
        return pl[self.pw_pos % len(pl)]

    def _prepare_pathway(self):
        idx = self._current_pw_index()
        self.cur_pw = PATHWAYS[idx]
        self.scroll_offset = 0.0
        self.active_particles = []
        flows = self.cur_pw['flows']
        self.spawn_timers = [random.uniform(0, f['interval'] * 0.5)
                             for f in flows]
        self.flow_lengths = [_path_length(f['path']) for f in flows]
        # Initialize conformational state tracking for complexes
        self.complex_states = []
        for cx in self.cur_pw['complexes']:
            states = cx.get('states')
            if states:
                self.complex_states.append({
                    'idx': 0, 'timer': 0.0,
                    'count': len(states),
                })
            else:
                self.complex_states.append(None)
        # Build set of gated flow indices (referenced by any state's spawn_flows)
        self.gated_flows = set()
        for cx in self.cur_pw['complexes']:
            for st in cx.get('states', []):
                for fi in st.get('spawn_flows', []):
                    self.gated_flows.add(fi)
        # Build color-keyed scroll segments
        labels = [
            (self.cur_pw['name'], Colors.WHITE),
            (self.cur_pw['sci_name'], Colors.WHITE),
        ]
        for note in self.cur_pw.get('notes', []):
            if isinstance(note, tuple):
                labels.append(note)
            else:
                labels.append((note, Colors.WHITE))
        sep = '  --  '
        sep_color = (60, 55, 50)
        segments = []
        px_off = 0
        for i, (text, color) in enumerate(labels):
            if i > 0:
                segments.append((px_off, sep, sep_color))
                px_off += len(sep) * 4
            segments.append((px_off, text, color))
            px_off += len(text) * 4
        segments.append((px_off, sep, sep_color))
        px_off += len(sep) * 4
        self.scroll_segments = segments
        self.scroll_len = px_off

    # -------------------------------------------------------------------
    # Input
    # -------------------------------------------------------------------
    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.up_pressed:
            self.group_idx = (self.group_idx - 1) % len(GROUPS)
            self.pw_pos = 0
            self.cycle_timer = 0.0
            self.overlay_timer = 2.5
            self._prepare_pathway()
            consumed = True
        if input_state.down_pressed:
            self.group_idx = (self.group_idx + 1) % len(GROUPS)
            self.pw_pos = 0
            self.cycle_timer = 0.0
            self.overlay_timer = 2.5
            self._prepare_pathway()
            consumed = True
        if input_state.left_pressed:
            pl = self._current_pw_list()
            if pl:
                self.pw_pos = (self.pw_pos - 1) % len(pl)
            self.cycle_timer = 0.0
            self._prepare_pathway()
            consumed = True
        if input_state.right_pressed:
            pl = self._current_pw_list()
            if pl:
                self.pw_pos = (self.pw_pos + 1) % len(pl)
            self.cycle_timer = 0.0
            self._prepare_pathway()
            consumed = True
        if input_state.action_l or input_state.action_r:
            self.auto_cycle = not self.auto_cycle
            consumed = True
        return consumed

    # -------------------------------------------------------------------
    # Update
    # -------------------------------------------------------------------
    def update(self, dt: float):
        self.time += dt
        self.scroll_offset += dt * 18
        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)
        if self.auto_cycle:
            self.cycle_timer += dt
            if self.cycle_timer >= self.cycle_duration:
                self.cycle_timer = 0.0
                pl = self._current_pw_list()
                if pl:
                    self.pw_pos = (self.pw_pos + 1) % len(pl)
                self._prepare_pathway()
        self._update_complex_states(dt)
        self._update_particles(dt)

    def _update_complex_states(self, dt):
        """Advance conformational state timers for complexes with states."""
        complexes = self.cur_pw['complexes']
        for ci, cs in enumerate(self.complex_states):
            if cs is None:
                continue
            states = complexes[ci]['states']
            cs['timer'] += dt
            cur_dur = states[cs['idx']].get('duration', 2.0)
            if cs['timer'] >= cur_dur:
                cs['timer'] = 0.0
                cs['idx'] = (cs['idx'] + 1) % cs['count']

    def _is_flow_active(self, flow_idx):
        """Check if a gated flow is currently active (its state is selected)."""
        if flow_idx not in self.gated_flows:
            return True  # ungated flows always active
        complexes = self.cur_pw['complexes']
        for ci, cs in enumerate(self.complex_states):
            if cs is None:
                continue
            state = complexes[ci]['states'][cs['idx']]
            if flow_idx in state.get('spawn_flows', []):
                return True
        return False

    def _update_particles(self, dt):
        flows = self.cur_pw['flows']
        for i, flow in enumerate(flows):
            self.spawn_timers[i] += dt
            if self.spawn_timers[i] >= flow['interval']:
                self.spawn_timers[i] = 0.0
                if not self._is_flow_active(i):
                    continue
                count = sum(1 for p in self.active_particles if p['flow'] == i)
                if count < flow.get('max', 3):
                    self.active_particles.append({
                        'flow': i, 'progress': 0.0,
                    })
        for p in self.active_particles:
            fl = self.flow_lengths[p['flow']]
            if fl > 0:
                p['progress'] += (flows[p['flow']]['speed'] / fl) * dt
        self.active_particles = [p for p in self.active_particles
                                 if p['progress'] < 1.0]

    # -------------------------------------------------------------------
    # Draw
    # -------------------------------------------------------------------
    def draw(self):
        d = self.display
        pw = self.cur_pw
        mem = pw.get('membrane')

        if mem:
            # Membrane pathway: stroma above, lumen below
            mem_y = mem['y']
            d.clear(pw['stroma_color'])
            lc = pw['lumen_color']
            warm = pw.get('lumen_warm', False)
            lumen_top = mem_y + 3
            for y in range(lumen_top, 56):
                if warm:
                    frac = 1.0 - (y - lumen_top) / max(1, 55 - lumen_top)
                    c = (min(255, lc[0] + int(10 * frac)), lc[1],
                         max(0, lc[2] - int(4 * frac)))
                else:
                    c = lc
                for x in range(64):
                    d.set_pixel(x, y, c)
        else:
            # Non-membrane pathway: solid background
            d.clear(pw.get('bg_color', (8, 8, 12)))

        # Regions (colored bands for non-membrane layouts)
        self._render_regions(pw)

        # Dim region labels (data-driven)
        for rl in pw.get('region_labels', []):
            d.draw_text_small(rl['x'], rl['y'], rl['text'], rl['color'])

        if mem:
            self._render_membrane(pw)
        self._render_connectors(pw)
        self._render_complexes(pw)
        self._render_particles(pw)
        self._draw_label()
        self._draw_overlay()

    # -------------------------------------------------------------------
    # Regions: colored bands for non-membrane layouts
    # -------------------------------------------------------------------
    def _render_regions(self, pw):
        d = self.display
        for reg in pw.get('regions', []):
            c = reg['color']
            for y in range(reg['y0'], reg['y1'] + 1):
                for x in range(64):
                    d.set_pixel(x, y, c)

    # -------------------------------------------------------------------
    # Connectors: dotted lines / arrows between stations
    # -------------------------------------------------------------------
    def _render_connectors(self, pw):
        d = self.display
        for conn in pw.get('connectors', []):
            x0, y0 = conn['from']
            x1, y1 = conn['to']
            style = conn.get('style', 'dotted')
            color = conn.get('color', (40, 40, 40))
            steps = max(abs(x1 - x0), abs(y1 - y0), 1)
            for i in range(steps + 1):
                t = i / steps
                px = int(x0 + t * (x1 - x0))
                py = int(y0 + t * (y1 - y0))
                if style == 'dotted' and i % 3 != 0:
                    continue
                d.set_pixel(px, py, color)
            # Arrow head at destination
            if style == 'arrow' or conn.get('arrow', False):
                dx = 1 if x1 > x0 else (-1 if x1 < x0 else 0)
                dy = 1 if y1 > y0 else (-1 if y1 < y0 else 0)
                d.set_pixel(x1 - dx + dy, y1 - dy - dx, color)
                d.set_pixel(x1 - dx - dy, y1 - dy + dx, color)

    # -------------------------------------------------------------------
    # Membrane: lipid bilayer cross-section
    # -------------------------------------------------------------------
    def _render_membrane(self, pw):
        d = self.display
        mem = pw['membrane']
        cy = mem['y']
        head = mem['head_color']
        tail = mem['tail_color']

        # Upper leaflet heads (phospholipid head groups, spaced)
        for x in range(0, 64, 2):
            d.set_pixel(x, cy - 2, head)
        # Hydrophobic fatty acid tails
        for y in range(cy - 1, cy + 2):
            for x in range(64):
                d.set_pixel(x, y, tail)
        # Lower leaflet heads
        for x in range(0, 64, 2):
            d.set_pixel(x, cy + 2, head)

    # -------------------------------------------------------------------
    # Protein complexes embedded in membrane
    # -------------------------------------------------------------------
    def _render_complexes(self, pw):
        d = self.display
        mem = pw.get('membrane')
        mem_y = mem['y'] if mem else 0

        for ci, cx in enumerate(pw['complexes']):
            x = cx['x']
            hw = cx['w'] // 2
            color = cx['color']
            above = cx.get('above', 4)
            below = cx.get('below', 4)
            cw = cx.get('channel_w', 0)
            channel_side = 'both'

            # Override visual props from current conformational state
            cs = self.complex_states[ci] if ci < len(self.complex_states) else None
            if cs is not None:
                state = cx['states'][cs['idx']]
                color = state.get('color', color)
                above = state.get('above', above)
                below = state.get('below', below)
                cw = state.get('channel_w', cw)
                channel_side = state.get('channel_side', channel_side)

            if 'y' in cx:
                center_y = cx['y']
                top = center_y - above
                bot = center_y + below
            else:
                top = mem_y - 2 - above
                bot = mem_y + 2 + below
            left = x - hw
            right = x + hw
            mid_y = (top + bot) // 2

            # Main body with highlight and edge shading
            for py in range(top, bot + 1):
                for px in range(left, right + 1):
                    edge = (px == left or px == right or
                            py == top or py == bot)
                    if edge:
                        shade = 0.55
                    elif py == top + 1:
                        shade = 1.25
                    else:
                        shade = 1.0
                    c = (min(255, int(color[0] * shade)),
                         min(255, int(color[1] * shade)),
                         min(255, int(color[2] * shade)))
                    d.set_pixel(px, py, c)

            # Channel pore (dark stripe through center)
            if cw > 0:
                pore = (max(1, color[0] // 5),
                        max(1, color[1] // 5),
                        max(1, color[2] // 5))
                if channel_side == 'top':
                    pore_top, pore_bot = top + 2, mid_y
                elif channel_side == 'bottom':
                    pore_top, pore_bot = mid_y + 1, bot - 1
                else:
                    pore_top, pore_bot = top + 2, bot - 1
                for py in range(pore_top, pore_bot):
                    for px in range(x - cw // 2, x + cw // 2 + 1):
                        d.set_pixel(px, py, pore)

            # ATP synthase F1 head (lollipop above membrane)
            f1 = cx.get('f1')
            if f1:
                f1c = f1['color']
                stalk_h = f1['stalk_h']
                head_h = f1['head_h']
                head_hw = f1['head_w'] // 2
                stalk_bot = top
                stalk_top = top - stalk_h
                head_top = stalk_top - head_h

                # Stalk (narrow connector)
                for py in range(stalk_top, stalk_bot):
                    d.set_pixel(x, py, color)

                # F1 catalytic head
                for py in range(head_top, stalk_top):
                    for px in range(x - head_hw, x + head_hw + 1):
                        edge = (px == x - head_hw or px == x + head_hw
                                or py == head_top or py == stalk_top - 1)
                        shade = 0.55 if edge else (1.25 if py == head_top + 1 else 1.0)
                        c = (min(255, int(f1c[0] * shade)),
                             min(255, int(f1c[1] * shade)),
                             min(255, int(f1c[2] * shade)))
                        d.set_pixel(px, py, c)

                # Rotation indicator: 3 subunit dots cycling brightness
                t = self.time
                for si in range(3):
                    angle = t * 1.5 + si * (2.0 * math.pi / 3.0)
                    bright = 0.6 + 0.4 * max(0, math.sin(angle))
                    mid_y = (head_top + stalk_top) // 2
                    sx = x + int(2 * math.cos(angle))
                    sy = mid_y + int(1.5 * math.sin(angle))
                    sc = (min(255, int(f1c[0] * bright * 1.2)),
                          min(255, int(f1c[1] * bright * 1.2)),
                          min(255, int(f1c[2] * bright * 0.8)))
                    d.set_pixel(sx, sy, sc)

    # -------------------------------------------------------------------
    # Flowing particles
    # -------------------------------------------------------------------
    def _render_particles(self, pw):
        d = self.display
        flows = pw['flows']
        for p in self.active_particles:
            flow = flows[p['flow']]
            style = PARTICLE_STYLES.get(flow['type'],
                                        PARTICLE_STYLES['electron'])
            pos = _interp_path(flow['path'], p['progress'])
            px, py = int(pos[0]), int(pos[1])
            color = style['color']

            # Photons: wavy path (electromagnetic wave)
            if style.get('wave'):
                wave = math.sin(p['progress'] * 30) * 1.5
                px = int(pos[0] + wave)

            # Composite particles (multi-pixel sprites)
            multi = style.get('multi')
            if multi:
                for dx, dy in multi:
                    d.set_pixel(px + dx, py + dy, color)
            else:
                size = style.get('size', 1)
                d.set_pixel(px, py, color)
                if size >= 2:
                    d.set_pixel(px + 1, py, color)
                    d.set_pixel(px, py + 1, color)

    # -------------------------------------------------------------------
    # Labels and overlay (same pattern as PERIODIC/MICROSCOPE)
    # -------------------------------------------------------------------
    def _draw_label(self):
        d = self.display
        scroll_x = int(self.scroll_offset) % self.scroll_len
        # Draw two copies for seamless wrap
        for copy in (0, self.scroll_len):
            for seg_off, text, color in self.scroll_segments:
                px = 2 + seg_off + copy - scroll_x
                text_w = len(text) * 4
                if px + text_w < 0 or px > 64:
                    continue
                d.draw_text_small(px, 58, text, color)

    def _draw_overlay(self):
        if self.overlay_timer > 0:
            d = self.display
            _, gname, gcolor = GROUPS[self.group_idx]
            alpha = min(1.0, self.overlay_timer / 0.5)
            oc = (int(gcolor[0] * alpha), int(gcolor[1] * alpha),
                  int(gcolor[2] * alpha))
            d.draw_text_small(2, 2, gname, oc)
