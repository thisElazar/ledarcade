#!/usr/bin/env python3
"""
Fetch real 3D conformers from PubChem for the MOLECULES visual.

Reads the existing MOLECULES table in visuals/molecule.py, looks each entry
up in PUBCHEM_SOURCES below, downloads the PubChem 3D conformer (SDF) and
molecular formula, and rewrites the MOLECULES block in place. Name, order and
group assignments are preserved; atoms/bonds/formula are replaced with the
PubChem data and a 'source' key records the CID.

Entries mapped to None (ionic solids, lattices, polymers - things PubChem has
no single-molecule 3D conformer for) keep their hand-authored geometry and
are tagged 'source': 'hand-authored'.

Usage:
    python3 tools/fetch_molecules.py            # rewrite visuals/molecule.py
    python3 tools/fetch_molecules.py --dry-run  # report only, no write
"""

import os
import re
import sys
import time
import urllib.request
import urllib.error
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOLECULE_PY = os.path.join(ROOT, 'visuals', 'molecule.py')
PUG = 'https://pubchem.ncbi.nlm.nih.gov/rest/pug'

# =============================================================================
# DISPLAY NAME -> PubChem compound (name string or integer CID; None = keep hand model)
# =============================================================================
# Use an explicit CID where a common name is ambiguous (stereoisomers, salts,
# or where the cabinet shows a specific form).
PUBCHEM_SOURCES = {
    'WATER': 'water', 'CO2': 'carbon dioxide', 'OXYGEN': 977, 'METHANE': 'methane',
    'AMMONIA': 'ammonia', 'ETHANOL': 'ethanol', 'GLUCOSE': 5793,  # D-glucose
    'GLYCINE': 'glycine', 'ADENINE': 'adenine', 'THYMINE': 'thymine',
    'GUANINE': 'guanine', 'CYTOSINE': 'cytosine', 'ATP': 5957,
    'CAFFEINE': 'caffeine', 'DOPAMINE': 'dopamine', 'SEROTONIN': 'serotonin',
    'ADRENALINE': 'epinephrine', 'TAURINE': 'taurine', 'ETHYLENE': 'ethylene',
    'PYRUVATE': 'pyruvic acid', 'CITRIC ACID': 'citric acid',
    'AUXIN': 'indole-3-acetic acid', 'PENICILLIN': 5904,  # penicillin G
    'VITAMIN C': 'ascorbic acid', 'VITAMIN B3': 'niacin', 'VITAMIN B6': 'pyridoxine',
    'VITAMIN B1': 'thiamine', 'VITAMIN B2': 'riboflavin', 'VITAMIN B7': 'biotin',
    'VITAMIN B9': 'folic acid', 'VITAMIN A': 'retinol',
    'ACETYLENE': 'acetylene', 'PROPANE': 'propane', 'ACETONE': 'acetone',
    'ISOPROPYL': 'isopropanol',
    'PLA': 'lactic acid',            # shown as the lactic-acid monomer
    'WOOD GLUE': 'vinyl acetate',    # PVA monomer
    'STYRENE': 'styrene', 'LIMONENE': 440917,  # (R)-limonene
    'CA GLUE': 'ethyl cyanoacrylate',
    'SALT': None, 'BAKING SODA': None,  # ionic - no covalent conformer
    'VINEGAR': 'acetic acid', 'VANILLIN': 'vanillin',
    'CREAM OF TARTAR': 444305,       # L-tartaric acid
    'MSG': 'L-glutamic acid',        # glutamate ion shown as the free acid
    'CAPSAICIN': 'capsaicin', 'OLIVE OIL': 'oleic acid',
    'RUST': None, 'QUARTZ': None, 'SILICONE': 'hexamethyldisiloxane', 'CARBIDE': None,
    'ALANINE': 'L-alanine', 'VALINE': 'L-valine', 'LEUCINE': 'L-leucine',
    'ISOLEUCINE': 'L-isoleucine', 'PROLINE': 'L-proline',
    'PHENYLALANINE': 'L-phenylalanine', 'TRYPTOPHAN': 'L-tryptophan',
    'METHIONINE': 'L-methionine', 'SERINE': 'L-serine', 'THREONINE': 'L-threonine',
    'CYSTEINE': 'L-cysteine', 'TYROSINE': 'L-tyrosine', 'ASPARAGINE': 'L-asparagine',
    'GLUTAMINE': 'L-glutamine', 'ASPARTIC ACID': 'L-aspartic acid',
    'GLUTAMIC ACID': 'L-glutamic acid', 'LYSINE': 'L-lysine', 'ARGININE': 'L-arginine',
    'HISTIDINE': 'L-histidine',
    'ASPIRIN': 'aspirin', 'ACETAMINOPHEN': 'acetaminophen', 'METFORMIN': 'metformin',
    'IBUPROFEN': 'ibuprofen', 'NAPROXEN': 'naproxen', 'MELATONIN': 'melatonin',
    'DIPHENHYDRAMINE': 'diphenhydramine', 'OMEPRAZOLE': 'omeprazole',
    'MORPHINE': 'morphine', 'LIDOCAINE': 'lidocaine', 'QUININE': 'quinine',
    'NICOTINE': 'nicotine', 'CHOLINE': 'choline', 'ACETYLCHOLINE': 'acetylcholine',
    'SELENOCYSTEINE': 'L-selenocysteine', 'PYRROLYSINE': 'pyrrolysine',
    'GABA': 'gamma-aminobutyric acid', 'ORNITHINE': 'L-ornithine',
    'CITRULLINE': 'L-citrulline', 'THEANINE': 'L-theanine',
    'HYDROXYPROLINE': 'hydroxyproline', 'BETA-ALANINE': 'beta-alanine',
    'HYDROGEN': 783, 'NITROGEN': 947, 'CARBON MONOXIDE': 'carbon monoxide',
    'NITRIC OXIDE': 'nitric oxide', 'OZONE': 'ozone',
    'HYDROGEN PEROXIDE': 'hydrogen peroxide', 'HYDROCHLORIC ACID': 'hydrogen chloride',
    'SULFURIC ACID': 'sulfuric acid', 'UREA': 'urea', 'FORMALDEHYDE': 'formaldehyde',
    'ACETIC ACID': 'acetic acid', 'LACTIC ACID': 'lactic acid', 'HISTAMINE': 'histamine',
    'CORTISOL': 'cortisol', 'FORMIC ACID': 'formic acid', 'MENTHOL': 'menthol',
    'CINNAMON': 'cinnamaldehyde', 'CHALK': None, 'LACTOSE': 'lactose', 'SOAP': None,
    'METHANOL': 887, 'L-DOPA': 6047,  # levodopa
    'NORADRENALINE': 439260,  # (R)-norepinephrine
}


# =============================================================================
# PubChem access
# =============================================================================

def _get(url):
    time.sleep(0.25)  # PubChem asks for <= 5 requests/sec
    req = urllib.request.Request(url, headers={'User-Agent': 'led-arcade/fetch_molecules'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode('utf-8')


def resolve_cid(source):
    if isinstance(source, int):
        return source
    txt = _get(f"{PUG}/compound/name/{urllib.parse.quote(source)}/cids/TXT")
    return int(txt.split()[0])


def fetch_3d_sdf(cid):
    try:
        return _get(f"{PUG}/compound/cid/{cid}/SDF?record_type=3d")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def fetch_formulas(cids):
    """Batch-fetch molecular formulas: {cid: formula}."""
    out = {}
    for i in range(0, len(cids), 50):
        chunk = cids[i:i + 50]
        csv = _get(f"{PUG}/compound/cid/{','.join(map(str, chunk))}/property/MolecularFormula/CSV")
        for line in csv.splitlines()[1:]:
            cid, formula = line.split(',')
            out[int(cid)] = formula.strip('"')
    return out


def _composition(formula):
    counts = {}
    for el, n in re.findall(r'([A-Z][a-z]?)(\d*)', formula.rstrip('+-')):
        counts[el] = counts.get(el, 0) + int(n or 1)
    return counts


def _composition_of_atoms(atoms):
    counts = {}
    for a in atoms:
        counts[a[0]] = counts.get(a[0], 0) + 1
    return counts


def parse_sdf(sdf):
    """Parse a V2000 molfile into (atoms, bonds) in molecule.py's format."""
    lines = sdf.splitlines()
    n_atoms, n_bonds = int(lines[3][0:3]), int(lines[3][3:6])
    atoms, bonds = [], []
    for ln in lines[4:4 + n_atoms]:
        x, y, z, sym = ln.split()[:4]
        atoms.append((sym, round(float(x), 4), round(float(y), 4), round(float(z), 4)))
    for ln in lines[4 + n_atoms:4 + n_atoms + n_bonds]:
        a, b, order = int(ln[0:3]) - 1, int(ln[3:6]) - 1, int(ln[6:9])
        if order not in (1, 2, 3):
            raise ValueError(f"unexpected bond order {order}")
        bonds.append((a, b, order))
    return atoms, bonds


# =============================================================================
# molecule.py read / write
# =============================================================================

def load_molecules(src):
    start = src.index('MOLECULES = [')
    end = src.index('\n]\n', start) + 3
    ns = {}
    exec(src[start:end], ns)
    return ns['MOLECULES'], start, end


def format_entry(m):
    lines = ['    {']
    lines.append(f"        'name': {m['name']!r},")
    lines.append(f"        'formula': {m['formula']!r},")
    if 'groups' in m:
        lines.append(f"        'groups': {m['groups']!r},")
    else:
        lines.append(f"        'group': {m['group']!r},")
    lines.append(f"        'source': {m['source']!r},")
    lines.append("        'atoms': [")
    for sym, x, y, z in m['atoms']:
        lines.append(f"            ({sym!r}, {x:8.4f}, {y:8.4f}, {z:8.4f}),")
    lines.append("        ],")
    lines.append("        'bonds': [")
    row = []
    for b in m['bonds']:
        row.append(f"{b!r},")
        if len(row) == 5:
            lines.append("            " + " ".join(row))
            row = []
    if row:
        lines.append("            " + " ".join(row))
    lines.append("        ],")
    lines.append('    },')
    return '\n'.join(lines)


def main():
    dry_run = '--dry-run' in sys.argv
    src = open(MOLECULE_PY).read()
    mols, start, end = load_molecules(src)

    unknown = [m['name'] for m in mols if m['name'] not in PUBCHEM_SOURCES]
    if unknown:
        sys.exit(f"No PUBCHEM_SOURCES entry for: {unknown}")

    fetched, kept, failed = [], [], []
    cid_of = {}
    for m in mols:
        source = PUBCHEM_SOURCES[m['name']]
        if source is None:
            m['source'] = 'hand-authored (no single-molecule PubChem 3D record)'
            kept.append(m['name'])
            continue
        try:
            cid = resolve_cid(source)
            sdf = fetch_3d_sdf(cid)
        except Exception as e:
            print(f"  {m['name']:16s} ERROR {e}", file=sys.stderr)
            m['source'] = 'hand-authored (PubChem fetch failed)'
            failed.append(m['name'])
            continue
        if sdf is None:
            print(f"  {m['name']:16s} CID {cid}: no 3D conformer, keeping hand model", file=sys.stderr)
            m['source'] = f'hand-authored (PubChem CID {cid} has no 3D conformer)'
            failed.append(m['name'])
            continue
        atoms, bonds = parse_sdf(sdf)
        print(f"  {m['name']:16s} CID {cid}: {len(atoms)} atoms, {len(bonds)} bonds", file=sys.stderr)
        m['atoms'], m['bonds'] = atoms, bonds
        m['source'] = f'PubChem CID {cid} 3D conformer'
        cid_of[m['name']] = cid
        fetched.append(m['name'])

    # Keep the conventional formula (NH3, HCl, C2H5OH) when it agrees with the
    # fetched atoms; PubChem's Hill-order form (H3N, ClH) only wins when the
    # composition actually changed (e.g. choline -> C5H14NO+).
    formulas = fetch_formulas(sorted(set(cid_of.values())))
    for m in mols:
        if m['name'] in cid_of and _composition(m['formula']) != _composition_of_atoms(m['atoms']):
            m['formula'] = formulas[cid_of[m['name']]]

    print(f"\n{len(fetched)} from PubChem, {len(kept)} kept by design, {len(failed)} fallback: {failed}",
          file=sys.stderr)
    if dry_run:
        return

    header = (
        "# Molecule definitions.\n"
        "# Generated by tools/fetch_molecules.py — 3D conformers from PubChem where a\n"
        "# single-molecule record exists; each entry's 'source' says which.\n"
        "# Coordinates in Angstroms; the visual re-centers and scales at draw time.\n"
    )
    # Replace any provenance comment lines directly above the block.
    pre = src[:start].rstrip('\n')
    pre_lines = pre.split('\n')
    while pre_lines and pre_lines[-1].startswith('#'):
        pre_lines.pop()
    pre = '\n'.join(pre_lines) + '\n\n'
    block = header + 'MOLECULES = [\n' + '\n'.join(format_entry(m) for m in mols) + '\n]\n'
    open(MOLECULE_PY, 'w').write(pre + block + src[end:])
    print(f"Wrote {MOLECULE_PY}", file=sys.stderr)


if __name__ == '__main__':
    main()
