from overeasy.agents import *
__version__ = "0.1.6"


import os as _os
ROOT = _os.path.expanduser("~/.overeasy")
_os.makedirs(ROOT, exist_ok=True)