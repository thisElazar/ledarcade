#!/usr/bin/env python3
"""
One-time extraction script: reads chord data from tombatossals/chords-db
compiled JSON (MIT license) and outputs Python dicts for chordchart.py.

Usage:
  curl -o /tmp/guitar_chords.json https://raw.githubusercontent.com/tombatossals/chords-db/master/lib/guitar.json
  curl -o /tmp/ukulele_chords.json https://raw.githubusercontent.com/tombatossals/chords-db/master/lib/ukulele.json
  python3 extract_chords.py > chord_data_output.py
"""

import json
import sys

# Our 15 suffixes (must match chords-db suffix field exactly)
SUFFIXES = [
    'major', 'minor', '7', 'maj7', 'm7', 'dim', 'aug',
    'sus2', 'sus4', 'add9', 'dim7', '6', 'm6', '9', 'm9',
]

# Map chords-db root keys to display names
# Guitar uses Csharp/Fsharp, ukulele uses Db/Gb
ROOT_MAP = {
    'C': 'C', 'Csharp': 'C#', 'Db': 'C#', 'D': 'D', 'Eb': 'Eb', 'E': 'E',
    'F': 'F', 'Fsharp': 'F#', 'Gb': 'F#', 'G': 'G', 'Ab': 'Ab', 'A': 'A',
    'Bb': 'Bb', 'B': 'B',
}
ROOT_ORDER = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']

MAX_VOICINGS = 5


def extract_instrument(json_path, num_strings):
    with open(json_path) as f:
        data = json.load(f)

    chords_by_root = data['chords']  # dict: root_key -> list of chord objects
    result = {}

    for root_key, chord_list in chords_by_root.items():
        root_disp = ROOT_MAP.get(root_key)
        if root_disp is None:
            continue

        for chord_obj in chord_list:
            suffix = chord_obj['suffix']
            if suffix not in SUFFIXES:
                continue

            positions = chord_obj.get('positions', [])
            voicings = []
            for pos in positions[:MAX_VOICINGS]:
                frets = tuple(pos['frets'])       # -1 = muted, 0 = open
                fingers = tuple(pos['fingers'])
                base_fret = pos.get('baseFret', 1)
                barres = tuple(pos.get('barres', []))

                if len(frets) != num_strings:
                    continue
                voicings.append((frets, fingers, base_fret, barres))

            if voicings:
                result[(root_disp, suffix)] = voicings

    return result


def print_dict(name, data):
    print(f"{name} = {{")
    for root in ROOT_ORDER:
        for suffix in SUFFIXES:
            key = (root, suffix)
            if key not in data:
                continue
            voicings = data[key]
            v_str = ", ".join(repr(v) for v in voicings)
            print(f"    ('{root}', '{suffix}'): [{v_str}],")
    print("}")


def main():
    guitar = extract_instrument('/tmp/guitar_chords.json', 6)
    ukulele = extract_instrument('/tmp/ukulele_chords.json', 4)

    print("# Auto-generated from tombatossals/chords-db (MIT license)")
    print("# Format: {(root, suffix): [(frets, fingers, baseFret, barres), ...], ...}")
    print("# frets: -1=muted, 0=open, 1+=fret relative to baseFret")
    print()
    print_dict("GUITAR_CHORDS", guitar)
    print()
    print_dict("UKULELE_CHORDS", ukulele)

    sys.stderr.write(f"Guitar: {len(guitar)} chords\n")
    sys.stderr.write(f"Ukulele: {len(ukulele)} chords\n")


if __name__ == '__main__':
    main()
