# -*- coding: utf-8 -*-

import os
import sys


try:
    import core
except:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
