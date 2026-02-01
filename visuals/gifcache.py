"""
GIF Frame Cache
================
Caches processed GIF frames to disk so they only need to be
decoded once. Subsequent loads read from a fast pickle cache.
Also provides optimized pixel extraction using tobytes().
"""

import os
import pickle


def cache_frames(gif_path, loader):
    """Return cached frames, or call loader() and cache the result.

    Args:
        gif_path: Path to the source GIF (cache key based on its mtime).
        loader: Callable that returns the frame data to cache.

    Returns:
        The frame data (whatever loader() returns).
    """
    cache_path = gif_path + ".cache"

    # Try loading from cache
    if os.path.exists(cache_path):
        try:
            if os.path.getmtime(cache_path) >= os.path.getmtime(gif_path):
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
        except Exception:
            pass

    # Process fresh
    data = loader()

    # Save to cache
    if data:
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception:
            pass

    return data


def extract_rgb(image):
    """Fast RGB pixel extraction from a PIL Image.

    Returns list of rows, each row a list of (r, g, b) tuples.
    """
    image = image.convert("RGBA")
    w, h = image.size
    raw = image.tobytes()
    pixels = []
    stride = w * 4
    for y in range(h):
        row = []
        offset = y * stride
        for x in range(w):
            i = offset + x * 4
            row.append((raw[i], raw[i + 1], raw[i + 2]))
        pixels.append(row)
    return pixels


def extract_rgba(image):
    """Fast RGBA pixel extraction from a PIL Image.

    Returns (pixels, alphas) where pixels is list of rows of (r,g,b)
    and alphas is list of rows of alpha values.
    """
    image = image.convert("RGBA")
    w, h = image.size
    raw = image.tobytes()
    pixels = []
    alphas = []
    stride = w * 4
    for y in range(h):
        prow = []
        arow = []
        offset = y * stride
        for x in range(w):
            i = offset + x * 4
            prow.append((raw[i], raw[i + 1], raw[i + 2]))
            arow.append(raw[i + 3])
        pixels.append(prow)
        alphas.append(arow)
    return pixels, alphas
