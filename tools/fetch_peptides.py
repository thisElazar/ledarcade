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


def count_nmr_models(pdb_text):
    """Count MODEL records in PDB text."""
    count = 0
    for line in pdb_text.split('\n'):
        if line.startswith('MODEL'):
            count += 1
    return count


def extract_all_nmr_models(pdb_text, chain, max_models=6):
    """Extract Cα coords from evenly-spaced NMR models.

    Returns list of coord lists, one per model. Each coord list
    has the same length (number of Cα atoms in model 1).
    """
    # First pass: collect all model numbers
    model_nums = []
    for line in pdb_text.split('\n'):
        if line.startswith('MODEL'):
            model_nums.append(int(line.split()[1]))

    if len(model_nums) <= 1:
        return []

    # Pick evenly-spaced models (always include first and last)
    if len(model_nums) <= max_models:
        selected = model_nums
    else:
        indices = [int(round(i * (len(model_nums) - 1) / (max_models - 1)))
                   for i in range(max_models)]
        selected = [model_nums[i] for i in indices]

    # Second pass: extract coords for selected models
    all_coords = []
    current_model = None
    current_coords = []
    seen_res = set()

    for line in pdb_text.split('\n'):
        if line.startswith('MODEL'):
            current_model = int(line.split()[1])
            current_coords = []
            seen_res = set()
        elif line.startswith('ENDMDL'):
            if current_model in selected and current_coords:
                all_coords.append(current_coords)
            current_model = None
            continue

        if current_model not in selected:
            continue

        if line.startswith('ATOM') or line.startswith('HETATM'):
            atom_name = line[12:16].strip()
            alt_loc = line[16]
            chain_id = line[21]
            res_seq = line[22:27].strip()

            if atom_name == 'CA' and chain_id == chain and alt_loc in (' ', 'A'):
                if res_seq not in seen_res:
                    seen_res.add(res_seq)
                    x = float(line[30:38])
                    y = float(line[38:46])
                    z = float(line[46:54])
                    current_coords.append((x, y, z))

    # Filter: all models must have same number of atoms as model 1
    if not all_coords:
        return []
    n_atoms = len(all_coords[0])
    all_coords = [c for c in all_coords if len(c) == n_atoms]
    if len(all_coords) < 2:
        return []

    return all_coords


def _mat_mult_3x3(A, B):
    """Multiply two 3x3 matrices (lists of lists)."""
    return [[sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)]
            for i in range(3)]


def _mat_transpose_3x3(A):
    """Transpose a 3x3 matrix."""
    return [[A[j][i] for j in range(3)] for i in range(3)]


def _jacobi_eigendecomposition_3x3(S):
    """3x3 symmetric matrix eigendecomposition via Jacobi rotations.

    Returns (eigenvalues, eigenvectors) where eigenvectors[i] is the
    i-th column eigenvector.
    """
    # Work on a copy
    A = [row[:] for row in S]
    # V starts as identity
    V = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]

    for _ in range(100):
        # Find largest off-diagonal element
        max_val = 0.0
        p, q = 0, 1
        for i in range(3):
            for j in range(i + 1, 3):
                if abs(A[i][j]) > max_val:
                    max_val = abs(A[i][j])
                    p, q = i, j

        if max_val < 1e-12:
            break

        # Compute rotation angle
        if abs(A[p][p] - A[q][q]) < 1e-15:
            theta = math.pi / 4
        else:
            theta = 0.5 * math.atan2(2 * A[p][q], A[p][p] - A[q][q])

        c = math.cos(theta)
        s = math.sin(theta)

        # Apply rotation to A
        App = c * c * A[p][p] + 2 * s * c * A[p][q] + s * s * A[q][q]
        Aqq = s * s * A[p][p] - 2 * s * c * A[p][q] + c * c * A[q][q]
        Apq = 0.0

        new_A = [row[:] for row in A]
        new_A[p][p] = App
        new_A[q][q] = Aqq
        new_A[p][q] = Apq
        new_A[q][p] = Apq

        for r in range(3):
            if r != p and r != q:
                new_rp = c * A[r][p] + s * A[r][q]
                new_rq = -s * A[r][p] + c * A[r][q]
                new_A[r][p] = new_rp
                new_A[p][r] = new_rp
                new_A[r][q] = new_rq
                new_A[q][r] = new_rq

        A = new_A

        # Update eigenvectors
        new_V = [row[:] for row in V]
        for r in range(3):
            new_V[r][p] = c * V[r][p] + s * V[r][q]
            new_V[r][q] = -s * V[r][p] + c * V[r][q]
        V = new_V

    eigenvalues = [A[i][i] for i in range(3)]
    return eigenvalues, V


def _svd_3x3(H):
    """Compute SVD of 3x3 matrix H = U * S * Vt using eigendecomposition.

    Returns (U, S_diag, Vt).
    """
    Ht = _mat_transpose_3x3(H)
    HtH = _mat_mult_3x3(Ht, H)
    evals, V = _jacobi_eigendecomposition_3x3(HtH)

    # Sort eigenvalues descending
    order = sorted(range(3), key=lambda i: -evals[i])
    evals = [evals[i] for i in order]
    V = [[V[r][order[j]] for j in range(3)] for r in range(3)]

    S_diag = [math.sqrt(max(0, e)) for e in evals]

    # U = H * V * S_inv
    HV = _mat_mult_3x3(H, V)
    U = [[0.0] * 3 for _ in range(3)]
    for j in range(3):
        if S_diag[j] > 1e-10:
            for i in range(3):
                U[i][j] = HV[i][j] / S_diag[j]
        else:
            # Null singular value - set column to zero (will be fixed by det check)
            for i in range(3):
                U[i][j] = 0.0

    Vt = _mat_transpose_3x3(V)
    return U, S_diag, Vt


def _det_3x3(M):
    """Determinant of 3x3 matrix."""
    return (M[0][0] * (M[1][1] * M[2][2] - M[1][2] * M[2][1])
          - M[0][1] * (M[1][0] * M[2][2] - M[1][2] * M[2][0])
          + M[0][2] * (M[1][0] * M[2][1] - M[1][1] * M[2][0]))


def kabsch_align(coords_mobile, coords_ref):
    """Align coords_mobile onto coords_ref using Kabsch algorithm.

    Both are lists of (x,y,z) tuples of same length.
    Returns aligned coords_mobile (centered, rotated to match ref).
    """
    n = len(coords_ref)
    if n == 0:
        return coords_mobile

    # Center both
    ref_cx = sum(c[0] for c in coords_ref) / n
    ref_cy = sum(c[1] for c in coords_ref) / n
    ref_cz = sum(c[2] for c in coords_ref) / n
    mob_cx = sum(c[0] for c in coords_mobile) / n
    mob_cy = sum(c[1] for c in coords_mobile) / n
    mob_cz = sum(c[2] for c in coords_mobile) / n

    ref_c = [(x - ref_cx, y - ref_cy, z - ref_cz) for x, y, z in coords_ref]
    mob_c = [(x - mob_cx, y - mob_cy, z - mob_cz) for x, y, z in coords_mobile]

    # Cross-covariance matrix H = mob^T * ref
    H = [[0.0] * 3 for _ in range(3)]
    for k in range(n):
        for i in range(3):
            for j in range(3):
                H[i][j] += mob_c[k][i] * ref_c[k][j]

    U, S, Vt = _svd_3x3(H)

    # Ensure proper rotation (det = +1)
    d = _det_3x3(_mat_mult_3x3(U, Vt))
    if d < 0:
        # Flip sign of last column of U
        for i in range(3):
            U[i][2] = -U[i][2]

    R = _mat_mult_3x3(U, Vt)

    # Apply rotation to centered mobile coords, then translate to ref center
    aligned = []
    for x, y, z in mob_c:
        nx = R[0][0] * x + R[0][1] * y + R[0][2] * z + ref_cx
        ny = R[1][0] * x + R[1][1] * y + R[1][2] * z + ref_cy
        nz = R[2][0] * x + R[2][1] * y + R[2][2] * z + ref_cz
        aligned.append((nx, ny, nz))

    return aligned


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

        result = {
            'name': name,
            'pdb': pdb_id,
            'description': description,
            'sequence': sequence,
            'cyclic': cyclic,
            'disulfide': disulfide,
            'coords': coords,
            'source': source,
            'chain': chain,
        }

        # Check for NMR ensemble models
        if pdb_text and source == 'PDB':
            n_models = count_nmr_models(pdb_text)
            if n_models >= 3:
                nmr_raw = extract_all_nmr_models(pdb_text, chain, max_models=6)
                if len(nmr_raw) >= 2 and len(nmr_raw[0]) == len(coords):
                    # Align all models to model 1 (already centered)
                    ref = nmr_raw[0]
                    aligned = [center_and_normalize(ref)]
                    for m in nmr_raw[1:]:
                        a = kabsch_align(m, ref)
                        aligned.append(center_and_normalize(a))
                    result['nmr_coords'] = aligned
                    print(f"  {name}: {len(coords)} coords ({source}), "
                          f"{len(aligned)} NMR models from {n_models} total",
                          file=sys.stderr)
                else:
                    print(f"  {name}: {len(coords)} coords ({source}), "
                          f"NMR models: {n_models} total but extraction failed",
                          file=sys.stderr)
            else:
                print(f"  {name}: {len(coords)} coords ({source})", file=sys.stderr)
        else:
            print(f"  {name}: {len(coords)} coords ({source})", file=sys.stderr)

        results.append(result)

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
        if 'nmr_coords' in r:
            print(f"        'nmr_coords': [")
            for mi, model in enumerate(r['nmr_coords']):
                print(f"            [  # model {mi}")
                for x, y, z in model:
                    print(f"                {format_coord(x, y, z)},")
                print(f"            ],")
            print(f"        ],")
        print(f"    }},")
    print("]")

    # Summary
    print(file=sys.stderr)
    pdb_count = sum(1 for r in results if r['source'] == 'PDB')
    fb_count = sum(1 for r in results if r['source'] == 'fallback')
    nmr_count = sum(1 for r in results if 'nmr_coords' in r)
    print(f"Done: {len(results)} peptides ({pdb_count} from PDB, {fb_count} fallback, "
          f"{nmr_count} with NMR ensembles)", file=sys.stderr)


if __name__ == '__main__':
    main()
