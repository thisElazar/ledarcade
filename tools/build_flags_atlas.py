#!/usr/bin/env python3
"""Generate flags_atlas.json for the web emulator.

Packs all flag PNGs (60x40) into a single JSON file with
base64-encoded raw RGB data per flag.

Usage: python tools/build_flags_atlas.py
"""

import base64
import json
import os
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT / "assets" / "flags"
OUT_PATH = ROOT / "site" / "flags_atlas.json"

FLAG_W, FLAG_H = 60, 40


def main():
    atlas = {}
    for png in sorted(ASSETS_DIR.glob("*.png")):
        iso = png.stem
        img = Image.open(png).convert("RGB")
        if img.size != (FLAG_W, FLAG_H):
            img = img.resize((FLAG_W, FLAG_H), Image.NEAREST)
        raw = bytearray()
        for y in range(FLAG_H):
            for x in range(FLAG_W):
                r, g, b = img.getpixel((x, y))
                raw.extend([r, g, b])
        atlas[iso] = base64.b64encode(bytes(raw)).decode('ascii')

    os.makedirs(OUT_PATH.parent, exist_ok=True)
    with open(OUT_PATH, 'w') as f:
        json.dump(atlas, f)
    print(f"Flags atlas: {OUT_PATH} ({len(atlas)} flags, {OUT_PATH.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
