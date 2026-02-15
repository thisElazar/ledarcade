#!/usr/bin/env python3
"""Generate gallery_atlas.json for the web emulator.

Pre-extracts and encodes all Gallery3D textures so the raycaster
can run in the browser without filesystem access.

Handles:
- GalleryArt: PNG paintings → 64×64 base64 RGB
- GallerySprites: PNG sequences + GIFs → 64×64 base64 RGB frames
- GallerySMB3/Kirby/Zelda/KidIcarus: BFS sprite extraction → 64×64 base64 RGB

Salon paintings are served from the existing paintings_atlas.json.
Adventure Time is deferred (too large).
Immersive-only galleries (Automata, Science, Digital, Effects) are skipped.

Usage: python tools/build_gallery_atlas.py
"""

import base64
import json
import os
import sys
from collections import deque
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
OUT_PATH = ROOT / "site" / "gallery_atlas.json"
GRID_SIZE = 64


def encode_texture(img):
    """Encode a PIL Image as base64 RGB bytes (64×64)."""
    if img.size != (GRID_SIZE, GRID_SIZE):
        img = img.resize((GRID_SIZE, GRID_SIZE), Image.NEAREST)
    raw = bytearray()
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            pixel = img.getpixel((x, y))
            if len(pixel) == 4:
                r, g, b, a = pixel
                if a <= 128:
                    r, g, b = 20, 20, 30  # dark background for transparent
            else:
                r, g, b = pixel[:3]
            raw.extend([r, g, b])
    return base64.b64encode(bytes(raw)).decode('ascii')


def process_png(path):
    """Load a single PNG and return [base64_frame]."""
    if not path.exists():
        return None
    img = Image.open(path).convert("RGB")
    return [encode_texture(img)]


def process_png_sequence(paths):
    """Load multiple PNGs and return [base64_frame, ...]."""
    frames = []
    for p in paths:
        if not p.exists():
            continue
        img = Image.open(p).convert("RGB")
        frames.append(encode_texture(img))
    return frames if frames else None


def process_gif(path, max_frames=12):
    """Extract GIF frames and return [base64_frame, ...]."""
    if not path.exists():
        return None
    bg = (20, 20, 30)
    gif = Image.open(path)
    n_frames = getattr(gif, 'n_frames', 1)
    step = max(1, n_frames // max_frames)
    frames = []
    for i in range(0, n_frames, step):
        gif.seek(i)
        frame = gif.convert("RGBA")
        frame = frame.resize((GRID_SIZE, GRID_SIZE), Image.NEAREST)
        raw = bytearray()
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                r, g, b, a = frame.getpixel((x, y))
                if a > 128:
                    raw.extend([r, g, b])
                else:
                    raw.extend(bg)
        frames.append(base64.b64encode(bytes(raw)).decode('ascii'))
        if len(frames) >= max_frames:
            break
    return frames if frames else None


def extract_sprites_from_sheet(path, max_sprite_dim=120):
    """BFS-extract sprites from a sprite sheet, return list of base64 textures."""
    import numpy as np

    if not path.exists():
        return []

    img = Image.open(path).convert("RGBA")
    w, h = img.size
    # Downscale large sheets to cap memory
    max_px = 4_000_000
    total_px = w * h
    if total_px > max_px:
        scale = (max_px / total_px) ** 0.5
        w = max(64, int(w * scale))
        h = max(64, int(h * scale))
        img = img.resize((w, h), Image.NEAREST)

    pixels = np.array(img)
    bg = pixels[0, 0, :3].astype(np.int16)
    bg_rgb = tuple(int(v) for v in bg)

    diff = np.abs(pixels[:, :, :3].astype(np.int16) - bg[None, None, :])
    alpha = pixels[:, :, 3]
    mask = (diff.max(axis=2) > 30) & (alpha > 128)

    visited = np.zeros((h, w), dtype=bool)
    components = []
    for sy in range(h):
        for sx in range(w):
            if mask[sy, sx] and not visited[sy, sx]:
                queue = deque([(sy, sx)])
                visited[sy, sx] = True
                mnx, mxx, mny, mxy, area = sx, sx, sy, sy, 0
                while queue:
                    cy, cx = queue.popleft()
                    area += 1
                    mnx = min(mnx, cx); mxx = max(mxx, cx)
                    mny = min(mny, cy); mxy = max(mxy, cy)
                    for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        ny, nx = cy + dy, cx + dx
                        if (0 <= ny < h and 0 <= nx < w
                                and not visited[ny, nx] and mask[ny, nx]):
                            visited[ny, nx] = True
                            queue.append((ny, nx))
                cw, ch = mxx - mnx + 1, mxy - mny + 1
                if (min(cw, ch) >= 14 and max(cw, ch) <= max_sprite_dim
                        and 0.2 <= cw / ch <= 5.0
                        and area / (cw * ch) > 0.08):
                    components.append((mnx, mny, cw, ch, area))

    components.sort(key=lambda c: (c[1], c[0]))

    dark = (20, 20, 30)
    textures = []
    for (cx, cy, cw, ch, _) in components:
        crop = img.crop((cx, cy, cx + cw, cy + ch))
        sz = max(cw, ch)
        sq = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
        sq.paste(crop, ((sz - cw) // 2, (sz - ch) // 2))
        sized = sq.resize((GRID_SIZE, GRID_SIZE), Image.NEAREST)
        raw = bytearray()
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                r, g, b, a = sized.getpixel((x, y))
                if (a > 128 and not (abs(r - bg_rgb[0]) < 30
                                     and abs(g - bg_rgb[1]) < 30
                                     and abs(b - bg_rgb[2]) < 30)):
                    raw.extend([r, g, b])
                else:
                    raw.extend(dark)
        textures.append(base64.b64encode(bytes(raw)).decode('ascii'))
    return textures


# ── Gallery definitions ──

GALLERY_ART_PAINTINGS = {
    2: ("png", "paintings/great_wave.png"),
    3: ("png", "paintings/the_scream.png"),
    4: ("png", "paintings/starry_night.png"),
    5: ("png", "paintings/water_lilies.png"),
    6: ("png", "paintings/broadway_boogie.png"),
    7: ("png", "paintings/girl_pearl_earring.png"),
    8: ("png", "paintings/mona_lisa.png"),
    9: ("png", "paintings/nighthawks.png"),
}

GALLERY_SPRITES_PAINTINGS = {
    2: ("png_seq", ["mario_walk1.png", "mario_walk2.png", "mario_walk3.png"]),
    3: ("png_seq", ["sonic_run1.png", "sonic_run2.png", "sonic_run3.png", "sonic_run4.png"]),
    4: ("gif", "ani_link_spin.gif"),
    5: ("gif", "SamusRunningR.gif"),
    6: ("gif", "yoshi_tongue.gif"),
    7: ("gif", "kirby_eats.gif"),
    8: ("gif", "megamanxpack2.gif"),
    9: ("gif", "Metroidgif.gif"),
}

SPRITE_MUSEUMS = {
    "GallerySMB3": ["smb3_heroes.png", "smb3_enemies.png", "smb3_bosses.png"],
    "GalleryKirby": ["kirby_heroes.png", "kirby_enemies.png",
                     "kirby_bosses.png", "kirby_soldiers.png"],
    "GalleryZelda": ["zelda_heroes.png", "zelda_npcs.png", "zelda_items.png",
                     "zelda_enemies_ow.png", "zelda_enemies_dg.png",
                     "zelda_bosses.png"],
    "GalleryKidIcarus": ["kidicarus_heroes.png", "kidicarus_enemies.png",
                         "kidicarus_items.png"],
}


def build_fixed_gallery(name, paintings_dict):
    """Build atlas entries for a gallery with fixed cell_id→asset mappings."""
    result = {}
    for cell_id, spec in paintings_dict.items():
        kind = spec[0]
        frames = None
        if kind == "png":
            path = ASSETS / spec[1]
            frames = process_png(path)
        elif kind == "png_seq":
            paths = [ASSETS / p for p in spec[1]]
            frames = process_png_sequence(paths)
        elif kind == "gif":
            path = ASSETS / spec[1]
            frames = process_gif(path)
        if frames:
            result[str(cell_id)] = frames
    return result


def build_sprite_museum(cls_name, sheets):
    """Extract sprites from all sheets, return {cell_id_str: [b64_frame]}."""
    all_textures = []
    for sheet_file in sheets:
        path = ASSETS / sheet_file
        print(f"  Extracting {sheet_file}...", end=" ", flush=True)
        textures = extract_sprites_from_sheet(path)
        print(f"{len(textures)} sprites")
        all_textures.extend(textures)

    result = {}
    for i, tex_b64 in enumerate(all_textures):
        cell_id = i + 2  # cell_ids start at 2
        result[str(cell_id)] = [tex_b64]
    return result


def main():
    os.makedirs(OUT_PATH.parent, exist_ok=True)
    atlas = {}

    # GalleryArt
    print("Building GalleryArt...")
    art = build_fixed_gallery("GalleryArt", GALLERY_ART_PAINTINGS)
    if art:
        atlas["GalleryArt"] = art
        print(f"  {len(art)} textures")

    # GallerySprites
    print("Building GallerySprites...")
    sprites = build_fixed_gallery("GallerySprites", GALLERY_SPRITES_PAINTINGS)
    if sprites:
        atlas["GallerySprites"] = sprites
        print(f"  {len(sprites)} textures")

    # Main gallery atlas (small galleries only)
    with open(OUT_PATH, 'w') as f:
        json.dump(atlas, f)
    size_kb = OUT_PATH.stat().st_size / 1024
    print(f"\nGallery atlas: {OUT_PATH} ({size_kb:.0f} KB)")

    # Sprite museums — separate files (large, loaded on demand)
    for cls_name, sheets in SPRITE_MUSEUMS.items():
        print(f"\nBuilding {cls_name}...")
        museum = build_sprite_museum(cls_name, sheets)
        if museum:
            out_file = OUT_PATH.parent / f"gallery_{cls_name}.json"
            with open(out_file, 'w') as f:
                json.dump({cls_name: museum}, f)
            size_kb = out_file.stat().st_size / 1024
            print(f"  {len(museum)} sprites → {out_file.name} ({size_kb:.0f} KB)")


if __name__ == "__main__":
    main()
