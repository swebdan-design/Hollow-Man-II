"""World root: imports every content module in order."""
import importlib
from content import *
import story  # noqa  (registers ordered flags first)

MODULES = ['gloam', 'ch1', 'ch2', 'ch3', 'ch4', 'ch5', 'ch6', 'ch7']
STUBS = []
for _m in MODULES:
    try:
        importlib.import_module(_m)
    except ModuleNotFoundError as e:
        if e.name != _m:
            raise
        STUBS.append(_m)

# development stubs for maps referenced but not yet authored
_refs = set()
for _mp in MAPS:
    _refs.update(w[2] for w in _mp.warps)
    _refs.update(e for e in _mp.exits if e)
for _n in sorted(_refs):
    if _n not in MAP_BY_NAME:
        STUBS.append(_n)
        Map(_n, 'interior', 'int_warm', None, """
BBBBBBBBBB
B........B
B........B
B........B
B........B
B........B
B........B
B........B
BBBBBDBBBB
""", title='stub')
