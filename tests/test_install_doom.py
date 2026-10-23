"""tools/install_doom.py: Freedoom lands only when every pin matches."""

import hashlib
import io
import os
import zipfile

import pytest

from tools import install_doom


def _zip_with(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        for name, data in files.items():
            z.writestr('freedoom-x/' + name, data)
    return buf.getvalue()


@pytest.fixture
def pinned(monkeypatch, tmp_path):
    """Point the installer at tmp_path and pin two tiny fake WADs."""
    wads = {'freedoom1.wad': b'phase one', 'freedoom2.wad': b'phase two'}
    monkeypatch.setattr(install_doom, 'WAD_DIR', str(tmp_path / 'data' / 'doom'))
    monkeypatch.setattr(install_doom, 'WADS',
                        {n: hashlib.sha256(d).hexdigest() for n, d in wads.items()})
    return wads


def _serve(monkeypatch, payload):
    class _Resp(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *a): pass
    monkeypatch.setattr(install_doom.urllib.request, 'urlopen', lambda url, timeout: _Resp(payload))
    monkeypatch.setattr(install_doom, 'FREEDOOM_ZIP_SHA256', hashlib.sha256(payload).hexdigest())


def test_good_zip_installs_wads_and_licence(monkeypatch, tmp_path, pinned):
    _serve(monkeypatch, _zip_with({**pinned, 'COPYING.txt': b'bsd', 'README.html': b'skip'}))
    log = []
    install_doom.fetch_freedoom(log.append)
    installed = sorted(os.listdir(install_doom.WAD_DIR))
    assert installed == ['COPYING.txt', 'freedoom1.wad', 'freedoom2.wad']
    assert install_doom.wads_installed()
    assert not [d for d in os.listdir(tmp_path / 'data') if d.startswith('doom-install-')]


def test_wrong_zip_hash_installs_nothing(monkeypatch, tmp_path, pinned):
    _serve(monkeypatch, _zip_with(pinned))
    monkeypatch.setattr(install_doom, 'FREEDOOM_ZIP_SHA256', '0' * 64)
    with pytest.raises(RuntimeError, match='nothing installed'):
        install_doom.fetch_freedoom(lambda m: None)
    assert not os.path.exists(install_doom.WAD_DIR)
    assert not [d for d in os.listdir(tmp_path / 'data') if d.startswith('doom-install-')]


def test_wrong_wad_hash_installs_nothing(monkeypatch, tmp_path, pinned):
    tampered = {**pinned, 'freedoom2.wad': b'not phase two'}
    _serve(monkeypatch, _zip_with(tampered))
    with pytest.raises(RuntimeError, match='freedoom2.wad'):
        install_doom.fetch_freedoom(lambda m: None)
    assert not os.path.exists(install_doom.WAD_DIR)


def test_game_reads_its_paths_from_the_installer():
    from games import doom
    assert doom._EXE == install_doom.ENGINE
    assert doom._WAD_DIR == install_doom.WAD_DIR
    assert doom._DOOM_DIR == install_doom.WAD_DIR      # saves live beside the WADs
    assert install_doom.ENGINE.startswith(os.path.join(install_doom.REPO, 'third_party'))
    assert install_doom.WAD_DIR == os.path.join(install_doom.REPO, 'data', 'doom')
