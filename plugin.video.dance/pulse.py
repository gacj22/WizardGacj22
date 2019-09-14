# -*- coding: utf-8 -*-
#------------------------------------------------------------
# Sourced From Online Templates And Guides
#------------------------------------------------------------
# License: GPL (http://www.gnu.org/licenses/gpl-3.0.html)
# Based on code from youtube addon
#
# Thanks To: Google Search For This Template
# Modified: Pulse
#------------------------------------------------------------

import os
import sys
import plugintools
import xbmc,xbmcaddon
from addon.common.addon import Addon

addonID = 'plugin.video.dance'
addon = Addon(addonID, sys.argv)
local = xbmcaddon.Addon(id=addonID)
icon = local.getAddonInfo('icon')

xbmc.executebuiltin('Container.SetViewMode(500)')

YOUTUBE_CHANNEL_ID_1 = "PLAxy1YpvZDdWIRIU03EYPgN6x3Ea6DEhS"
YOUTUBE_CHANNEL_ID_2 = "PLz1iM8YfFbTfVxM2dSLl-4LuRStdbijzj"
YOUTUBE_CHANNEL_ID_3 = "PL0cWlOyqP6_PKyS76fDsafkj_ho4KLmEA"
YOUTUBE_CHANNEL_ID_4 = "PLOPmDfV0hAMZG1U05-KeLnpxEFGVTIXoD"
YOUTUBE_CHANNEL_ID_5 = "PL97FFC73DD3A689AF"
YOUTUBE_CHANNEL_ID_6 = "PLtsi3zUEpVIww7Wxe2UYstyy99KqI355m"
YOUTUBE_CHANNEL_ID_7 = "PLWYQuS6aEMRDcHza5LQjPbRkrwu2qt6DT"
YOUTUBE_CHANNEL_ID_8 = "PLnNLaLnVDytXZ-atmhPICI4iHtO5uzTq7"
YOUTUBE_CHANNEL_ID_9 = "PLbgBkNZvTlnR7hBkwO18wVjNjo1HH7Xj1"
YOUTUBE_CHANNEL_ID_10 = "PL30RQhxrsS6HrFLpgnn9ruQGQAuEN-SOj"
YOUTUBE_CHANNEL_ID_11 = "PLs03y9BMaz8Zc_nbYboPxRE-E-uFLXpzM"
YOUTUBE_CHANNEL_ID_12 = "PLC91E7204E9265AE0"
YOUTUBE_CHANNEL_ID_13 = "PL78q4cbN1kIMGrAFNV-TLOFJc9PVhtlmo" 
YOUTUBE_CHANNEL_ID_14 = "PLNwSQunTljMmzkgaGwowpaGS2pt2dI2qu" 
YOUTUBE_CHANNEL_ID_15 = "PLEylltUN0Ao6Uk6AghHheszfMfEPZR1UW"
YOUTUBE_CHANNEL_ID_16 = "PLAB46D5259A91152E"
YOUTUBE_CHANNEL_ID_17 = "PL90BD8AB3F24C6C7E" 
YOUTUBE_CHANNEL_ID_18 = "RDEMSmA2wMtr85l4E1Lo96WfRA"
YOUTUBE_CHANNEL_ID_19 = "PLAFvUraxa7KN_Wkqr3B24zl3jS4LvJjwZ"
YOUTUBE_CHANNEL_ID_20 = "PL9Z0stL3aRyk3-72RVYwMbYR3HbcK_U5r" 
YOUTUBE_CHANNEL_ID_21 = "PLBfpghymm7GF-bShnewJs8xpPq3xJJ_9g"
YOUTUBE_CHANNEL_ID_22 = "PL6RLee9oArCCFkbSmURt8xV3aVKRGCDKj"
YOUTUBE_CHANNEL_ID_23 = "PLXAegibAG18dUQKtquV6Sqm9oevNTES8p" 
YOUTUBE_CHANNEL_ID_24 = "PLW_ZWxYTgYoritLiGoaP8x0011GOm3WjQ"
YOUTUBE_CHANNEL_ID_25 = "PL7WRZi2t3DIp3cZxa2zwP2u6FGmHFODog"
YOUTUBE_CHANNEL_ID_26 = "PL80951B9F4EE05F5B"
YOUTUBE_CHANNEL_ID_27 = "PL3CCF4BBCA70B4C2C" 
YOUTUBE_CHANNEL_ID_28 = "PL38B49BF06695B002"
YOUTUBE_CHANNEL_ID_29 = "PLB87F27995E8E3371"
YOUTUBE_CHANNEL_ID_30 = "FL9QwEZj-KBlYzW3hbsgwS-Q"
YOUTUBE_CHANNEL_ID_31 = "PLKOXXePgWciOO61ZUSzTDQQGyD_546BGA"
# Entry point
def run():
    plugintools.log("docu.run")
    
    # Get params
    params = plugintools.get_params()
    
    if params.get("action") is None:
        main_list(params)
    else:
        action = params.get("action")
        exec action+"(params)"
    
    plugintools.close_item_list()

# Main menu
def main_list(params):
    plugintools.log("docu.main_list "+repr(params))
	
    plugintools.add_item( 
        #action="", 
        title="DJ Tiesto Live",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_1+"/",
        thumbnail="https://images.sftcdn.net/images/t_optimized,f_auto/p/117d100a-9b29-11e6-ae89-00163ed833e7/3208043978/tema-de-dj-tiesto-logo.jpg",
        folder=True )
	
    plugintools.add_item( 
        #action="", 
        title="David Guetta Live",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_2+"/",
        thumbnail="https://www.tenvinilo.com/vinilos-decorativos/img/preview/vinilo-decorativo-logo-david-guetta-1877.png",
        folder=True )
		
    plugintools.add_item( 
        #action="", 
        title="Armin Van Buuren - A State Of Trance Radio Episodes",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_3+"/",
        thumbnail="http://images6.fanpop.com/image/photos/35900000/ARMIN-LOGO-armin-van-buuren-35974187-580-246.jpg",
        folder=True )
		
	
    plugintools.add_item( 
        #action="", 
        title="Martin Garrix - Live Footage",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_4+"/",
        thumbnail="https://i.pinimg.com/736x/c4/41/a6/c441a6c0eb1a1acd4549d35098c47132--logo-google-martin-omalley.jpg",
        folder=True )
	

    plugintools.add_item( 
        #action="", 
        title="Ferry Corsten  -  Music Videos",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_5+"/",
        thumbnail="https://upload.wikimedia.org/wikipedia/commons/c/c5/Ferry_Corsten_Logo.png",
        folder=True )
	
    plugintools.add_item( 
        #action="", 
        title="Paul Van Dyk  LIve",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_6+"/",
        thumbnail="https://fanart.tv/fanart/music/092ca127-2e07-4cbd-9cba-e412b4ddddd9/hdmusiclogo/dyk-van-paul-538dcdfdc92b3.png",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Paul Van Dyk - Vonyc Sessions",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_7+"/",
        thumbnail="https://fanart.tv/fanart/music/092ca127-2e07-4cbd-9cba-e412b4ddddd9/hdmusiclogo/dyk-van-paul-538dcdfdc92b3.png",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Dimitri Vegas and Like Mike - Live shows and concert",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_14+"/",
        thumbnail="https://i1.sndcdn.com/artworks-000200141173-1m7dcq-t500x500.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Hardwell - Live",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_15+"/",
        thumbnail="https://upload.wikimedia.org/wikipedia/commons/e/e2/Hardwell_Logo.png",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Afrojack DJ Sets",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_16+"/",
        thumbnail="https://www.artistontheroad.eu/wp-content/uploads/2016/06/logo-Afrojack.png",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Don Diablo Live Shows",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_17+"/",
        thumbnail="https://ih0.redbubble.net/image.220852540.5808/flat,550x550,075,f.u1.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="KSHMR - Mix",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_18+"/",
        thumbnail="https://ih0.redbubble.net/image.146518624.4416/flat,800x800,075,f.jpg",
        folder=True )
		
    plugintools.add_item( 
        #action="", 
        title="W&W - Livesets",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_19+"/",
        thumbnail="https://upload.wikimedia.org/wikipedia/commons/0/0e/W%26W_Logo.png",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Skrillex - On Tour",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_20+"/",
        thumbnail="http://s3.amazonaws.com/stripgenerator/strip/04/52/75/00/00/full.png",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Axwell /\ Ingrosso - Live Shows",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_21+"/",
        thumbnail="https://upload.wikimedia.org/wikipedia/commons/7/7e/Axwell_%26_Ingrosso_-_Logo.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Above & Beyond - Live Sets",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_22+"/",
        thumbnail="https://upload.wikimedia.org/wikipedia/commons/b/be/Above_%26_Beyond_Logo.png",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="QUINTINO - Live",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_23+"/",
        thumbnail="https://www.dafont.com/forum/attach/orig/5/1/516736.png",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Headhunterz - Livesets",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_24+"/",
        thumbnail="https://ih0.redbubble.net/image.146518624.4416/flat,800x800,075,f.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Bassjackers - Live",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_25+"/",
        thumbnail="https://upload.wikimedia.org/wikipedia/commons/c/c4/Bassjackers_-_Logo.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Alesso - Live",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_26+"/",
        thumbnail="https://upload.wikimedia.org/wikipedia/commons/e/ef/Alesso_Logo.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Ummet Ozcan - Live",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_27+"/",
        thumbnail="https://i.ytimg.com/vi/YGgo8xmlAPE/maxresdefault.jpg",
        folder=True )
		
    plugintools.add_item( 
        #action="", 
        title="Nicky Romero - Live Moments",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_28+"/",
        thumbnail="http://logonoid.com/images/nicky-romero-logo.png",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="YVES V - Live",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_29+"/",
        thumbnail="http://www.deejaybooking.com/wp-content/uploads/2015/03/Captur-6e.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Miss K8 - Favoritos",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_30+"/",
        thumbnail="https://upload.wikimedia.org/wikipedia/fr/4/4f/Miss_K8_logo.jpg",
        folder=True )
		
    plugintools.add_item( 
        #action="", 
        title="Masters of Hardcore - Podcast",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_31+"/",
        thumbnail="https://i.ytimg.com/vi/cnM-I8D58so/maxresdefault.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Progressive Sessions",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_8+"/",
        thumbnail="https://i.ytimg.com/vi/a1oArA1UZTo/hqdefault.jpg",
        folder=True )
		
    plugintools.add_item( 
        #action="", 
        title="Groove Dance Club Sessions",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_9+"/",
        thumbnail="http://www.discazos.com/store/23497-large_default/groove-dance-club-groove-sessions.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Fabrik Playlist Remember",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_10+"/",
        thumbnail="http://3.bp.blogspot.com/-OV8QBr0-MS4/Uu59wbRfbxI/AAAAAAAAAkw/ul3RMInAhqs/w1200-h630-p-k-no-nu/logo-fabrik.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Hardstyle Music PLaylist",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_11+"/",
        thumbnail="http://rs241.pbsrc.com/albums/ff274/zefrenm/Electro-03-1.png?w=280&h=210&fit=crop",
        folder=True )
		
    plugintools.add_item( 
        #action="", 
        title="Hard Trance - Hard Dance",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_12+"/",
        thumbnail="http://rs241.pbsrc.com/albums/ff274/zefrenm/Electro-03-1.png?w=280&h=210&fit=crop",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Scorpia Central del Sonido Sessions",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_13+"/",
        thumbnail="http://www.makineros.com/imagenes/scorpia%20central%20del%20sonido.jpg",
        folder=True )

run()