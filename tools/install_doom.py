#!/usr/bin/env python3
"""Install Doom on this cabinet: build the engine, fetch Freedoom.

    python3 tools/install_doom.py

Run from the repo as the cabinet user (no sudo). It writes only inside the
repo, to paths git ignores:

  third_party/doomgeneric/doomgeneric/doom_pipe   the engine, built here
  data/doom/freedoom1.wad, freedoom2.wad          the game data
  data/doom/COPYING.txt, CREDITS.txt              Freedoom's licence and credits
  data/doom/.savegame/                            saves, written by the engine

games/doom.py reads ENGINE and WAD_DIR from here, so the game lists itself
in AFTER HOURS as soon as both exist; no restart needed.

Freedoom is pinned by sha256: the zip is checked before it is opened and
each WAD again before it is moved into place. Nothing lands in data/doom
until everything has passed. Running again rebuilds the engine (make skips
objects that are up to date) and leaves WADs that already match the pins.

Stdlib only: this must run on a bare Pi and from a cabinet thread later.
"""

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE_DIR = os.path.join(REPO, 'third_party', 'doomgeneric')
ENGINE = os.path.join(ENGINE_DIR, 'doomgeneric', 'doom_pipe')
WAD_DIR = os.path.join(REPO, 'data', 'doom')

# Freedoom 0.13.0 (2024-01-29). Hashes checked against the upstream release
# zip on 2026-10-23. Bumping the version means re-checking all three.
FREEDOOM_VERSION = '0.13.0'
FREEDOOM_URL = ('https://github.com/freedoom/freedoom/releases/download/'
                f'v{FREEDOOM_VERSION}/freedoom-{FREEDOOM_VERSION}.zip')
FREEDOOM_ZIP_SHA256 = '3f9b264f3e3ce503b4fb7f6bdcb1f419d93c7b546f4df3e874dd878db9688f59'
WADS = {
    'freedoom1.wad': '7323bcc168c5a45ff10749b339960e98314740a734c30d4b9f3337001f9e703d',
    'freedoom2.wad': 'a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b',
}
NOTICES = ('COPYING.txt', 'CREDITS.txt')   # Freedoom's licence requires COPYING.txt to travel with the WADs


def _sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def wads_installed():
    """True when every pinned WAD is in place with the right hash."""
    return all(os.path.isfile(os.path.join(WAD_DIR, n)) and _sha256(os.path.join(WAD_DIR, n)) == h
               for n, h in WADS.items())


def installed():
    return os.path.isfile(ENGINE) and wads_installed()


def build_engine(log=print, jobs=2):
    log('building the engine')
    subprocess.run([os.path.join(ENGINE_DIR, 'build.sh')], check=True,
                   env={**os.environ, 'JOBS': str(jobs)},
                   stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    if not os.path.isfile(ENGINE):
        raise RuntimeError('build finished but %s is missing' % ENGINE)
    log('engine built')


def fetch_freedoom(log=print, url=FREEDOOM_URL):
    """Download, verify and unpack Freedoom into WAD_DIR. Atomic: files move
    into WAD_DIR only after the zip and every WAD have matched their pins."""
    os.makedirs(os.path.dirname(WAD_DIR), exist_ok=True)
    # Stage on the same filesystem as WAD_DIR so the final step is a rename.
    stage = tempfile.mkdtemp(prefix='doom-install-', dir=os.path.dirname(WAD_DIR))
    try:
        zpath = os.path.join(stage, 'freedoom.zip')
        log('downloading Freedoom %s' % FREEDOOM_VERSION)
        with urllib.request.urlopen(url, timeout=60) as r, open(zpath, 'wb') as out:
            shutil.copyfileobj(r, out, 1 << 20)
        if _sha256(zpath) != FREEDOOM_ZIP_SHA256:
            raise RuntimeError('Freedoom zip does not match its pinned sha256; nothing installed')
        log('verified, unpacking')
        wanted = tuple(WADS) + NOTICES
        with zipfile.ZipFile(zpath) as z:
            for member in z.namelist():
                base = os.path.basename(member)
                if base in wanted:
                    with z.open(member) as src, open(os.path.join(stage, base), 'wb') as dst:
                        shutil.copyfileobj(src, dst, 1 << 20)
        for name, want in WADS.items():
            path = os.path.join(stage, name)
            if not os.path.isfile(path) or _sha256(path) != want:
                raise RuntimeError('%s missing or does not match its pinned sha256; nothing installed' % name)
        os.remove(zpath)
        os.makedirs(WAD_DIR, exist_ok=True)
        for name in wanted:
            src = os.path.join(stage, name)
            if os.path.exists(src):
                os.replace(src, os.path.join(WAD_DIR, name))
        log('Freedoom installed')
    finally:
        shutil.rmtree(stage, ignore_errors=True)


def install(log=print, jobs=2):
    build_engine(log, jobs)
    if wads_installed():
        log('Freedoom already installed')
    else:
        fetch_freedoom(log)
    log('done: %s + %s' % (ENGINE, WAD_DIR))


if __name__ == '__main__':
    try:
        install(jobs=int(os.environ.get('JOBS', '2')))
    except (RuntimeError, OSError, subprocess.CalledProcessError) as e:
        print('install failed:', e, file=sys.stderr)
        sys.exit(1)
