#!/usr/bin/python
# -*- coding: utf-8 -*-
# Torrentin - XBMC/Kodi Add-On
# Play torrent & magnet  on Android (Windows / Linux only AceStream and KMediaTorrent)
# by ciberus
# You can copy, distribute, modify blablabla.....
# v.0.5.4 (01.2017)

import sys,os,xbmc, xbmcaddon

__addon__ = xbmcaddon.Addon( id = 'plugin.video.torrentin' )
__author__     = __addon__.getAddonInfo('author')
__scriptid__   = __addon__.getAddonInfo('id')
__scriptname__ = __addon__.getAddonInfo('name')
__cwd__        = __addon__.getAddonInfo('path')
__version__    = __addon__.getAddonInfo('version')
__language__   = __addon__.getLocalizedString

lock_file = xbmc.translatePath('special://temp/'+ 'ts.lock')
if (sys.platform == 'win32') or (sys.platform == 'win64'):
    lock_file = lock_file.decode('utf-8')
if os.path.exists(lock_file): os.remove(lock_file)
sys.path.append( os.path.join( __addon__.getAddonInfo( 'path' ), 'core') )

if ( __name__ == "__main__" ):
    import core
    core.main()
