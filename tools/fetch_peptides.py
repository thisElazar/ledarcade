#!/usr/bin/env python3
"""
Fetch real Cα coordinates from the Protein Data Bank (RCSB) for peptides.

Reads PEPTIDE_SOURCES below, downloads PDB files, extracts Cα backbone
coordinates, and prints Python-ready data for peptides.py.

Usage:
    python3 tools/fetch_peptides.py
"""

import urllib.request
import sys
import math

# =============================================================================
# PEPTIDE SOURCES - PDB ID, chain, sequence, metadata
# =============================================================================
# Each entry: (name, pdb_id, chain, sequence, cyclic, disulfide_pairs, description)
#   - chain: which PDB chain to extract (usually 'A')
#   - disulfide_pairs: list of (i,j) 0-indexed residue pairs
#
# Organized by biological function for breadth.

PEPTIDE_SOURCES = [
    # -------------------------------------------------------------------------
    # HORMONES
    # -------------------------------------------------------------------------
    ('OXYTOCIN',        '1XY2', 'A', 'CYIQNCPLG',    True,  [(0,5)],  'Love hormone - bonding & trust'),
    ('VASOPRESSIN',     None,   'A', 'CYFQNCPRG',    True,  [(0,5)],  'Antidiuretic hormone'),
    ('GLUCAGON',        '1GCN', 'A', 'HSQGTFTSDYSKYLDSRRAQDFVQWLMNT', False, [], 'Blood sugar mobilizer'),
    ('SOMATOSTATIN',    '2MI1', 'A', 'AGCKNFFWKTFTSC', True, [(2,13)], 'Growth hormone inhibitor'),
    ('CALCITONIN',      '2GLH', 'A', 'CGNLSTCMLGTYTQDFNKFHTFPQTAIGVGAP', False, [(0,6)], 'Calcium regulation hormone'),
    ('GnRH',            '1YY1', 'A', 'QHWSYGLRPG',   False, [],       'Reproductive hormone'),
    ('GASTRIN',         None,   'A', 'QGPWLEEEEEAYGWMDF', False, [],   'Stomach acid secretion signal'),
    ('MOTILIN',         '1LBJ', 'A', 'FVPIFTYGELQRMQEKERNKGQ', False, [], 'GI motility hormone'),

    # -------------------------------------------------------------------------
    # NEUROPEPTIDES
    # -------------------------------------------------------------------------
    ('MET-ENKEPHALIN',  '1PLW', 'A', 'YGGFM',        False, [],       'Natural painkiller opioid'),
    ('SUBSTANCE P',     '2KSA', 'B', 'RPKPQQFFGLM',  False, [],       'Pain neuropeptide'),
    ('NEUROPEPTIDE Y',  '1RON', 'A', 'YPSKPDNPGEDAPAEDMARYYSALRHYINLITRQRY', False, [], 'Appetite & stress regulator'),
    ('BETA-ENDORPHIN',  '6TUB', 'A', 'YGGFMTSEKSQTPLVTLFKNAIIKNAYKKGE', False, [], 'Runners high endorphin'),
    ('DYNORPHIN A',     '2N2F', 'A', 'YGGFLRRIRPKLK', False, [],       'Kappa opioid neuropeptide'),
    ('NEUROTENSIN',     '2LNE', 'A', 'QLYENKPRRPYIL', False, [],       'Dopamine modulator'),
    ('OREXIN-A',        '1R02', 'A', 'QPLPDCCRQKTCSCRLYELLHGAGNHAAGILTL', False, [(5,11),(6,14)], 'Sleep/wake regulator'),
    ('OREXIN-B',        '1CQ0', 'A', 'RSGPPGLQGRLQRLLQASGNHAAGILTM', False, [], 'Appetite/wakefulness signal'),

    # -------------------------------------------------------------------------
    # VASOACTIVE / CARDIOVASCULAR
    # -------------------------------------------------------------------------
    ('BRADYKININ',      '6F3V', 'A', 'RPPGFSPFR',    False, [],       'Pain & inflammation signal'),
    ('ANGIOTENSIN II',  '1N9V', 'A', 'DRVYIHPF',     False, [],       'Blood pressure regulator'),
    ('ANP',             '1ANP', 'A', 'SLRRSSCFGGRMDRIGAQSGLGCNSFRY', False, [(6,22)], 'Heart blood pressure signal'),
    ('ENDOTHELIN-1',    '1EDN', 'A', 'CSCSSLMDKECVYFCHLDIIW', False, [(0,10),(2,14)], 'Vasoconstrictor peptide'),

    # -------------------------------------------------------------------------
    # ANTIMICROBIAL
    # -------------------------------------------------------------------------
    ('MAGAININ 2',      '2MAG', 'A', 'GIGKFLHSAKKFGKAFVGEIMNS', False, [], 'Frog skin antibiotic'),
    ('MELITTIN',        '2MLT', 'A', 'GIGAVLKVLTTGLPALISWIKRKRQQ', False, [], 'Bee venom pore-former'),
    ('DEFENSIN',        '1DFN', 'A', 'ACYCRIPACIAGERRYGTCIYQGRLWAFCC', False, [(1,28),(4,19),(9,29)], 'Human innate immune defense'),
    ('LL-37',           '2K6O', 'A', 'LLGDFFRKSKEKIGKEFKRIVQRIKDFLRNLVPRTES', False, [], 'Human cathelicidin antibiotic'),
    ('GRAMICIDIN S',    None,   'A', 'VOLFPVOLFP',   True,  [],       'Bacterial cyclic antibiotic'),
    ('NISIN',           '1WCO', 'B', 'ITSISLCTPGCKTGALMGCNMKTATCHCSIHVSK', False, [], 'Food preservative lantibiotic'),
    ('TACHYPLESIN',     '1MA2', 'A', 'KWCFRVCYRGICYRRCR', False, [(2,15),(5,12)], 'Horseshoe crab antimicrobial'),

    # -------------------------------------------------------------------------
    # TOXINS / VENOMS
    # -------------------------------------------------------------------------
    ('CONOTOXIN',       '1IM1', 'A', 'GCCSDPRCAWRC',  False, [(2,7),(3,11)], 'Cone snail neurotoxin'),
    ('ZICONOTIDE',      '1TTK', 'A', 'CKGKGAKCSRLMYDCCTGSCRSGKC', False, [(0,15),(7,19),(14,24)], 'Cone snail painkiller drug'),
    ('CHLOROTOXIN',     '1CHL', 'A', 'MCMPCFTTDHQMARKCDDCCGGKGRGKCYGPQCLCR', False, [(1,19),(4,32),(7,27),(16,34)], 'Scorpion glioma-binding toxin'),
    ('APAMIN',          '7OXF', 'A', 'CNCKAPETALCARRCQQH', False, [(0,10),(2,14)], 'Bee venom neurotoxin'),
    ('SHK TOXIN',       '1ROO', 'A', 'RSCIDTIPKSRCTAFQCKHSMKYRLSFCRKTCGTC', False, [(2,32),(5,27),(16,24)], 'Sea anemone K+ channel blocker'),
    ('EXENDIN-4',       '1JRJ', 'A', 'HGEGTFTSDLSKQMEEEAVRLFIEWLKNGGPSSGAPPPS', False, [], 'Gila monster GLP-1 drug'),

    # -------------------------------------------------------------------------
    # SIGNALING / IMMUNE / OTHER
    # -------------------------------------------------------------------------
    ('ACTH',            None,   'A', 'SYSMEHFRWGKPVGKKRRPVKVYPNGAEDESAEAFPLEF', False, [], 'Stress response hormone'),
    ('SECRETIN',        None,   'A', 'HSDGTFTSELSRLREGARLQRLLQGLV', False, [], 'Digestive hormone'),
    ('GLUTATHIONE',     None,   'A', 'ECG',           False, [],       'Master antioxidant tripeptide'),
    ('HEPCIDIN',        '1M4F', 'A', 'DTHFPICIFCCGCCHRSKCGMCCKT', False, [(6,12),(7,22),(10,17),(13,21)], 'Iron metabolism master regulator'),
    ('VIP',             '2RRH', 'A', 'HSDAVFTDNYTRLRKQMAVKKYLNSILN', False, [], 'Vasoactive intestinal peptide'),
    ('KALATA B1',       '1NB1', 'A', 'GLPVCGETCVGGTCNTPGCTCSWPVCTRN', True, [(4,18),(9,21),(14,27)], 'Cyclotide - knotted ring'),

    # -------------------------------------------------------------------------
    # BOUNDARY: also in PROTEINS visual (small proteins / large peptides)
    # -------------------------------------------------------------------------
    ('INSULIN',         '4INS', 'B', 'FVNQHLCGSHLVEALYLVCGERGFFYTPKT', False, [(6,19)], 'Blood sugar hormone B-chain'),
    ('AMYLOID BETA',    '1IYT', 'A', 'DAEFRHDSGYEVHHQKLVFFAEDVGSNKGAIIGLMVGGVVIA', False, [], 'Alzheimers plaque peptide'),
    ('CRAMBIN',         '1CRN', 'A', 'TTCCPSIVARSNFNVCRLPGTPEALCATYTGCIIIPGATCPGDYAN', False, [(2,15),(3,31),(16,25)], 'Tiny plant seed protein'),
]


def fetch_pdb(pdb_id):
    """Download PDB file from RCSB."""
    url = f'https://files.rcsb.org/download/{pdb_id}.pdb'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'LED-Arcade-PeptideFetcher/1.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode('utf-8', errors='replace')
    except Exception as e:
        print(f"  WARNING: Could not fetch {pdb_id}: {e}", file=sys.stderr)
        return None


def extract_ca_coords(pdb_text, chain='A'):
    """Extract Cα coordinates from PDB text for a given chain.

    Returns list of (x, y, z) tuples, one per residue.
    Only takes MODEL 1 if multiple NMR models exist.
    """
    coords = []
    seen_res = set()
    in_model_1 = True  # For NMR structures with multiple models

    for line in pdb_text.split('\n'):
        if line.startswith('MODEL'):
            model_num = int(line.split()[1])
            in_model_1 = (model_num == 1)
        elif line.startswith('ENDMDL'):
            if coords:  # Got model 1, stop
                break
            in_model_1 = True

        if not in_model_1:
            continue

        if (line.startswith('ATOM') or line.startswith('HETATM')):
            atom_name = line[12:16].strip()
            alt_loc = line[16]
            chain_id = line[21]
            res_seq = line[22:27].strip()  # includes insertion code

            if atom_name == 'CA' and chain_id == chain and alt_loc in (' ', 'A'):
                if res_seq not in seen_res:
                    seen_res.add(res_seq)
                    x = float(line[30:38])
                    y = float(line[38:46])
                    z = float(line[46:54])
                    coords.append((x, y, z))

    return coords


def center_and_normalize(coords):
    """Center coordinates on origin. Don't normalize scale - let the visual handle that."""
    n = len(coords)
    if n == 0:
        return coords
    cx = sum(c[0] for c in coords) / n
    cy = sum(c[1] for c in coords) / n
    cz = sum(c[2] for c in coords) / n
    return [(x - cx, y - cy, z - cz) for x, y, z in coords]


def generate_fallback_coords(sequence, cyclic):
    """Generate approximate coordinates when PDB fetch fails.

    Linear: zigzag chain with 3.8Å Cα spacing.
    Cyclic: regular polygon.
    """
    n = len(sequence)
    coords = []
    if cyclic:
        radius = n * 3.8 / (2 * math.pi)
        for i in range(n):
            angle = 2 * math.pi * i / n
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            z = 1.5 * math.sin(angle * 2)  # Slight pucker
            coords.append((x, y, z))
    else:
        for i in range(n):
            x = i * 3.2
            y = 2.0 * math.sin(i * 0.8)
            z = 1.5 * math.cos(i * 1.1)
            coords.append((x, y, z))
    return center_and_normalize(coords)


def format_coord(x, y, z):
    """Format a coordinate tuple for Python source."""
    return f'({x:7.2f}, {y:7.2f}, {z:7.2f})'


def main():
    print("# Auto-generated peptide data from RCSB PDB")
    print("# Run: python3 tools/fetch_peptides.py > /tmp/peptide_data.py")
    print()

    results = []

    for name, pdb_id, chain, sequence, cyclic, disulfide, description in PEPTIDE_SOURCES:
        if pdb_id is None:
            print(f"# {name}: no PDB, using fallback", file=sys.stderr)
            coords = generate_fallback_coords(sequence, cyclic)
            results.append({
                'name': name, 'pdb': 'N/A', 'description': description,
                'sequence': sequence, 'cyclic': cyclic, 'disulfide': disulfide,
                'coords': coords, 'source': 'fallback', 'chain': chain,
            })
            print(f"  {name}: {len(coords)} coords (fallback)", file=sys.stderr)
            continue

        print(f"# Fetching {name} (PDB: {pdb_id}, chain {chain})...", file=sys.stderr)

        pdb_text = fetch_pdb(pdb_id)
        if pdb_text:
            raw_coords = extract_ca_coords(pdb_text, chain)
            if len(raw_coords) >= 3:
                coords = center_and_normalize(raw_coords)
                source = 'PDB'
                # Verify length matches sequence
                if len(coords) != len(sequence):
                    print(f"  NOTE: {name}: PDB has {len(coords)} CA atoms, "
                          f"sequence has {len(sequence)} AA. Using PDB count.",
                          file=sys.stderr)
            else:
                print(f"  WARNING: {name}: Only {len(raw_coords)} CA atoms found. "
                      f"Using fallback.", file=sys.stderr)
                coords = generate_fallback_coords(sequence, cyclic)
                source = 'fallback'
        else:
            coords = generate_fallback_coords(sequence, cyclic)
            source = 'fallback'

        results.append({
            'name': name,
            'pdb': pdb_id,
            'description': description,
            'sequence': sequence,
            'cyclic': cyclic,
            'disulfide': disulfide,
            'coords': coords,
            'source': source,
            'chain': chain,
        })

        print(f"  {name}: {len(coords)} coords ({source})", file=sys.stderr)

    # Output Python code
    print("PEPTIDES = [")
    for r in results:
        ds = repr(r['disulfide']) if r['disulfide'] else '[]'
        print(f"    {{  # {r['source'].upper()} {r['pdb']}:{r['chain']}")
        print(f"        'name': {r['name']!r},")
        print(f"        'description': {r['description']!r},")
        print(f"        'sequence': {r['sequence']!r},")
        print(f"        'cyclic': {r['cyclic']!r},")
        print(f"        'disulfide': {ds},")
        print(f"        'coords': [")
        for x, y, z in r['coords']:
            print(f"            {format_coord(x, y, z)},")
        print(f"        ],")
        print(f"    }},")
    print("]")

    # Summary
    print(file=sys.stderr)
    pdb_count = sum(1 for r in results if r['source'] == 'PDB')
    fb_count = sum(1 for r in results if r['source'] == 'fallback')
    print(f"Done: {len(results)} peptides ({pdb_count} from PDB, {fb_count} fallback)",
          file=sys.stderr)


if __name__ == '__main__':
    main()
