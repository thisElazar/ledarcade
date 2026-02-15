#!/usr/bin/env python3
"""Generate signs_atlas.json for the web emulator.

Packs all sign PNGs (44x44) into a single JSON file with
base64-encoded raw RGB data per sign.

Usage: python tools/build_signs_atlas.py
"""

import base64
import json
import os
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT / "assets" / "signs"
OUT_PATH = ROOT / "site" / "signs_atlas.json"

SIGN_SIZE = 44


def main():
    atlas = {}
    for png in sorted(ASSETS_DIR.glob("*.png")):
        stem = png.stem
        img = Image.open(png).convert("RGB")
        if img.size != (SIGN_SIZE, SIGN_SIZE):
            img = img.resize((SIGN_SIZE, SIGN_SIZE), Image.NEAREST)
        raw = bytearray()
        for y in range(SIGN_SIZE):
            for x in range(SIGN_SIZE):
                r, g, b = img.getpixel((x, y))
                raw.extend([r, g, b])
        atlas[stem] = base64.b64encode(bytes(raw)).decode('ascii')

    os.makedirs(OUT_PATH.parent, exist_ok=True)
    with open(OUT_PATH, 'w') as f:
        json.dump(atlas, f)
    print(f"Signs atlas: {OUT_PATH} ({len(atlas)} signs, {OUT_PATH.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
