#!/usr/bin/env python3
"""Downscale an atlas .npz for the 64×64 LED arcade display.

Usage:
    python tools/downscale_atlas.py <input.npz> <factor> [output.npz]

Example:
    python tools/downscale_atlas.py atlas_mideast.npz 4
    # → atlas_mideast_4x.npz

Each layer is downscaled with the appropriate strategy:
  - Continuous (elevation, blue_marble, nightlights, bathymetry): area average
  - Categorical (worldcover): majority vote
  - Binary masks (roads, rails, water, boundaries): max (preserve thin features)
  - Metadata (bounds, grid_res, place_names, etc.): copied as-is
"""

import sys
import os
import numpy as np


def downscale_average(grid, factor):
    """Downscale by area-averaging (for continuous data)."""
    h, w = grid.shape[:2]
    nh, nw = h // factor, w // factor
    cropped = grid[:nh * factor, :nw * factor]
    if grid.ndim == 3:
        return cropped.reshape(nh, factor, nw, factor, -1).mean(axis=(1, 3)).astype(grid.dtype)
    return cropped.reshape(nh, factor, nw, factor).mean(axis=(1, 3)).astype(grid.dtype)


def downscale_majority(grid, factor):
    """Downscale by majority vote (for categorical data)."""
    h, w = grid.shape[:2]
    nh, nw = h // factor, w // factor
    cropped = grid[:nh * factor, :nw * factor]
    blocks = cropped.reshape(nh, factor, nw, factor)
    out = np.zeros((nh, nw), dtype=grid.dtype)
    for y in range(nh):
        for x in range(nw):
            vals, counts = np.unique(blocks[y, :, x, :], return_counts=True)
            out[y, x] = vals[counts.argmax()]
    return out


def downscale_max(grid, factor):
    """Downscale by max (preserves thin features in binary masks)."""
    h, w = grid.shape[:2]
    nh, nw = h // factor, w // factor
    cropped = grid[:nh * factor, :nw * factor]
    return cropped.reshape(nh, factor, nw, factor).max(axis=(1, 3)).astype(grid.dtype)


# Layer → downscale strategy
STRATEGIES = {
    # Continuous
    'elevation': 'average',
    'bathymetry': 'average',
    'blue_marble': 'average',
    'nightlights': 'average',
    # Categorical
    'worldcover': 'majority',
    # Binary / thin features
    'roads': 'max',
    'rails': 'max',
    'water': 'max',
    'water_detail': 'max',
    'boundaries': 'max',
}

# Keys that are NOT grids (copy as-is)
METADATA_KEYS = {
    'bounds', 'grid_res',
    'place_names', 'place_lats', 'place_lons', 'place_pops',
    'airport_names', 'airport_lats', 'airport_lons', 'airport_iata',
}


def downscale_atlas(input_path, factor, output_path=None):
    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_{factor}x{ext}"

    print(f"Loading {input_path}...")
    d = np.load(input_path, allow_pickle=True)

    result = {}
    for key in d.files:
        arr = d[key]

        if key in METADATA_KEYS:
            result[key] = arr
            print(f"  {key}: copied (metadata)")
            continue

        strategy = STRATEGIES.get(key)
        if strategy is None:
            # Unknown grid — try average if 2D+, else copy
            if arr.ndim >= 2 and arr.shape[0] > factor and arr.shape[1] > factor:
                strategy = 'average'
                print(f"  {key}: {arr.shape} → average (guessed)")
            else:
                result[key] = arr
                print(f"  {key}: copied (small/unknown)")
                continue

        old_shape = arr.shape
        if strategy == 'average':
            result[key] = downscale_average(arr, factor)
        elif strategy == 'majority':
            result[key] = downscale_majority(arr, factor)
        elif strategy == 'max':
            result[key] = downscale_max(arr, factor)

        new_shape = result[key].shape
        ratio = arr.nbytes / result[key].nbytes
        print(f"  {key}: {old_shape} → {new_shape} ({strategy}, {ratio:.0f}x smaller)")

    # Update grid_res if present
    if 'grid_res' in result:
        result['grid_res'] = float(result['grid_res']) * factor

    print(f"\nSaving {output_path}...")
    np.savez_compressed(output_path, **result)

    old_size = os.path.getsize(input_path)
    new_size = os.path.getsize(output_path)
    print(f"  {old_size / 1e6:.1f} MB → {new_size / 1e6:.1f} MB "
          f"({new_size / old_size * 100:.0f}%)")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python downscale_atlas.py <input.npz> <factor> [output.npz]")
        sys.exit(1)

    input_path = sys.argv[1]
    factor = int(sys.argv[2])
    output_path = sys.argv[3] if len(sys.argv) > 3 else None
    downscale_atlas(input_path, factor, output_path)
