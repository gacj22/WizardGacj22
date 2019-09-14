# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Distributed under the terms of GNU General Public License v3 (GPLv3)
# http://www.gnu.org/licenses/gpl-3.0.html
# ------------------------------------------------------------
# XBMC entry point
#------------------------------------------------------------

import os
import sys

from core import config
from core import logger

logger.info("deportesalacarta.default init...")

librerias = xbmc.translatePath( os.path.join( config.get_runtime_path(), 'lib' ) )
sys.path.append (librerias)

from platformcode import launcher

if sys.argv[1] == "1":
    launcher.start()

launcher.run()