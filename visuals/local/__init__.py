"""
Local Visuals Plugin Loader
============================
Scans visuals/local/ for .py files and dynamically loads Visual subclasses.
Place copyrighted or personal visuals here — this directory is gitignored.
"""

import importlib
import inspect
import os
import sys

# Ensure project root is on path for imports
_pkg_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_pkg_dir))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from visuals import Visual

LOCAL_VISUALS = []

_local_dir = os.path.dirname(os.path.abspath(__file__))
for _fname in sorted(os.listdir(_local_dir)):
    if _fname.endswith('.py') and _fname != '__init__.py':
        _mod_name = _fname[:-3]
        try:
            _mod = importlib.import_module(f'.{_mod_name}', package='visuals.local')
            for _name, _cls in inspect.getmembers(_mod, inspect.isclass):
                if (issubclass(_cls, Visual) and _cls is not Visual
                        and hasattr(_cls, 'name') and not _name.startswith('_')
                        and _cls.__module__ == _mod.__name__):
                    LOCAL_VISUALS.append(_cls)
        except Exception as e:
            print(f"[local] skip {_fname}: {e}")
