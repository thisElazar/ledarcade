#!/usr/bin/env python3
"""
PDB Parser - Extract Cα coordinates and secondary structure from PDB files
===========================================================================
Fetches real protein structures from RCSB and outputs Python code for proteins.py

Usage:
    python3 tools/pdb_parser.py 1UBQ "Protein degradation tag"
    python3 tools/pdb_parser.py 1MBO "Oxygen storage in muscle"
"""

import sys
import urllib.request


def fetch_pdb(pdb_id):
    """Download PDB file from RCSB."""
    url = f"https://files.rcsb.org/download/{pdb_id.upper()}.pdb"
    print(f"Fetching {url}...", file=sys.stderr)
    try:
        with urllib.request.urlopen(url) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching PDB: {e}", file=sys.stderr)
        sys.exit(1)


def parse_pdb(pdb_text, chain='A'):
    """
    Parse PDB file to extract:
    - Cα coordinates
    - Secondary structure from HELIX/SHEET records
    """
    lines = pdb_text.split('\n')

    # Parse secondary structure records
    # HELIX records: residues in alpha helices
    # SHEET records: residues in beta sheets
    ss_map = {}  # residue_num -> 'H', 'E', or 'C'

    for line in lines:
        if line.startswith('HELIX'):
            # HELIX    1   1 ILE A   23  GLU A   34
            try:
                start_chain = line[19]
                start_res = int(line[21:25].strip())
                end_chain = line[31]
                end_res = int(line[33:37].strip())
                if start_chain == chain:
                    for r in range(start_res, end_res + 1):
                        ss_map[r] = 'H'
            except (ValueError, IndexError):
                pass

        elif line.startswith('SHEET'):
            # SHEET    1   A 5 THR A  12  VAL A  17
            try:
                start_chain = line[21]
                start_res = int(line[22:26].strip())
                end_chain = line[32]
                end_res = int(line[33:37].strip())
                if start_chain == chain:
                    for r in range(start_res, end_res + 1):
                        ss_map[r] = 'E'
            except (ValueError, IndexError):
                pass

    # Parse ATOM records for CA (alpha carbon) atoms
    atoms = []
    for line in lines:
        if not line.startswith('ATOM'):
            continue

        atom_name = line[12:16].strip()
        if atom_name != 'CA':
            continue

        atom_chain = line[21]
        if atom_chain != chain:
            continue

        try:
            res_name = line[17:20].strip()
            res_num = int(line[22:26].strip())
            x = float(line[30:38].strip())
            y = float(line[38:46].strip())
            z = float(line[46:54].strip())

            # Get secondary structure (default to coil)
            ss = ss_map.get(res_num, 'C')

            atoms.append({
                'res_name': res_name,
                'res_num': res_num,
                'x': x,
                'y': y,
                'z': z,
                'ss': ss,
            })
        except (ValueError, IndexError):
            pass

    return atoms


def get_protein_name(pdb_text):
    """Extract protein name from COMPND or TITLE record."""
    for line in pdb_text.split('\n'):
        if line.startswith('TITLE'):
            title = line[10:].strip()
            if title:
                return title
    return "Unknown protein"


def output_python(pdb_id, atoms, description, title):
    """Output Python code for proteins.py"""

    # 3-letter to 1-letter amino acid codes
    aa_map = {
        'ALA': 'A', 'CYS': 'C', 'ASP': 'D', 'GLU': 'E', 'PHE': 'F',
        'GLY': 'G', 'HIS': 'H', 'ILE': 'I', 'LYS': 'K', 'LEU': 'L',
        'MET': 'M', 'ASN': 'N', 'PRO': 'P', 'GLN': 'Q', 'ARG': 'R',
        'SER': 'S', 'THR': 'T', 'VAL': 'V', 'TRP': 'W', 'TYR': 'Y',
    }

    # Generate variable name from PDB ID
    var_name = pdb_id.upper().replace('-', '_')

    print(f"# {title}")
    print(f"# PDB: {pdb_id.upper()} - {len(atoms)} residues")
    print(f"{var_name} = {{")
    print(f"    'name': '{pdb_id.upper()}',")
    print(f"    'pdb': '{pdb_id.upper()}',")
    print(f"    'description': '{description}',")
    print(f"    'residues': {len(atoms)},")
    print(f"    'backbone': [")

    for atom in atoms:
        aa = aa_map.get(atom['res_name'], 'X')
        print(f"        ({atom['x']:7.3f}, {atom['y']:7.3f}, {atom['z']:7.3f}, '{atom['ss']}'),  # {atom['res_name']} {atom['res_num']}")

    print(f"    ],")
    print(f"}}")
    print()

    # Summary stats
    ss_counts = {'H': 0, 'E': 0, 'C': 0}
    for atom in atoms:
        ss_counts[atom['ss']] = ss_counts.get(atom['ss'], 0) + 1

    print(f"# Secondary structure: H={ss_counts['H']}, E={ss_counts['E']}, C={ss_counts['C']}", file=sys.stderr)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 pdb_parser.py <PDB_ID> [description] [chain]")
        print("Example: python3 pdb_parser.py 1UBQ 'Protein degradation tag'")
        print("\nSome interesting PDB IDs:")
        print("  1UBQ - Ubiquitin (76 residues)")
        print("  1MBO - Myoglobin (153 residues) - first structure solved")
        print("  2HHB - Hemoglobin (141+146 residues)")
        print("  1HRC - Cytochrome c (104 residues)")
        print("  1LYZ - Lysozyme (129 residues)")
        print("  1GFL - GFP (238 residues)")
        print("  1IGT - Antibody Fab (214+214 residues)")
        print("  1INS - Insulin (21+30 residues)")
        sys.exit(1)

    pdb_id = sys.argv[1]
    description = sys.argv[2] if len(sys.argv) > 2 else "Protein structure"
    chain = sys.argv[3] if len(sys.argv) > 3 else 'A'

    pdb_text = fetch_pdb(pdb_id)
    title = get_protein_name(pdb_text)
    atoms = parse_pdb(pdb_text, chain)

    if not atoms:
        print(f"No CA atoms found for chain {chain}", file=sys.stderr)
        sys.exit(1)

    print(f"# Found {len(atoms)} residues in chain {chain}", file=sys.stderr)
    output_python(pdb_id, atoms, description, title)


if __name__ == '__main__':
    main()
