# -*- coding: utf-8 -*-
#------------------------------------------------------------
# Contenido para niños de YouTube by j.ruiz
#------------------------------------------------------------
# License: GPL (http://www.gnu.org/licenses/gpl-3.0.html)
# Based on code from youtube addon
#
# Author: j.ruiz
#------------------------------------------------------------

import os
import sys
import plugintools
import xbmc,xbmcaddon
from addon.common.addon import Addon

addonID = 'plugin.video.mundoinfantil'
addon = Addon(addonID, sys.argv)
local = xbmcaddon.Addon(id=addonID)
icon = local.getAddonInfo('icon')

YOUTUBE_CHANNEL_ID_1 = "atiempopreescolar"
YOUTUBE_CHANNEL_ID_2 = "UCVIXxMQ51drJmg9Hj-tXAfg"
YOUTUBE_CHANNEL_ID_3 = "UCQTGHhyi9iURgMaJk4mUqpQ"
YOUTUBE_CHANNEL_ID_4 = "PLjr_J_DQd6zccQTlLNoaWJjdOIbMNgQdM"
YOUTUBE_CHANNEL_ID_5 = "LouieEspanol"
YOUTUBE_CHANNEL_ID_6 = "UCeTdhZLFZEfpHgJ-GAEV-WQ"
YOUTUBE_CHANNEL_ID_7 = "UCCzR0RTeFKJr-kcwADUlSnw"
YOUTUBE_CHANNEL_ID_8 = "UCk2wzETSoKdY2TVW01NRreQ"
YOUTUBE_CHANNEL_ID_9 = "UCBbsyG0o_cWlyY46ZRSdYJg"
YOUTUBE_CHANNEL_ID_10 = "UCjgRtV0zjOfsCP0_i3DjA8A"
YOUTUBE_CHANNEL_ID_11 = "UCsm77kEHBDEPgD4Ir3jSRYg"
YOUTUBE_CHANNEL_ID_12 = "PLjr_J_DQd6zfQEFSL3yn4Lcg5tXuR3mOC"
YOUTUBE_CHANNEL_ID_13 = "UChlTeveFUK6bvHrmCb8J99w"
YOUTUBE_CHANNEL_ID_14 = "UCGkVdu_EVrqqxQ7OnLFK8RQ"
YOUTUBE_CHANNEL_ID_15 = "UCWNm9s6fZeivd1SSI9PmS9A"
YOUTUBE_CHANNEL_ID_16 = "cancionesdelzoo"
YOUTUBE_CHANNEL_ID_17 = "cancionesdelagranja"
YOUTUBE_CHANNEL_ID_18 = "PLWYQuS6aEMRDcHza5LQjPbRkrwu2qt6DT"
YOUTUBE_CHANNEL_ID_19 = "UCdFAbctdV4NL_Vgy6MxNCKQ"
YOUTUBE_CHANNEL_ID_20 = "UC1vKPJSQ9VGMoPS1FP01NUw"
YOUTUBE_CHANNEL_ID_21 = "UCXeWf1D51KJQJEYemqsOdPQ"
YOUTUBE_CHANNEL_ID_22 = "PicaPicaVEVO"
YOUTUBE_CHANNEL_ID_23 = "PICCOLOMONDOpr" 
YOUTUBE_CHANNEL_ID_24 = "PLjr_J_DQd6zcLG5c_OX6GWwqo88aiz821"
YOUTUBE_CHANNEL_ID_25 = "RositaFresitaOficial"
YOUTUBE_CHANNEL_ID_26 = "plazasesamo"
YOUTUBE_CHANNEL_ID_27 = "UCOnprKBB5g8HgTAr0CBCzzg"
YOUTUBE_CHANNEL_ID_28 = "PLjr_J_DQd6ze4cdGvTklqXDutNhSA5uio"
YOUTUBE_CHANNEL_ID_29 = "tuyycantando"
YOUTUBE_CHANNEL_ID_30 = "dhxjuniortvspain"


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
        title="[COLOR cornflowerblue]1. A Tiempo Preescolar[/COLOR]",
        url="plugin://plugin.video.youtube/user/"+YOUTUBE_CHANNEL_ID_1+"/",
        thumbnail="http://mybuild.darkwebrepo.gq/infantil/atiempo.jpg",
        folder=True )
	
    plugintools.add_item( 
        #action="", 
        title="[COLOR cornflowerblue]2. Angelina Ballerina Latinoamérica[/COLOR]",
        url="plugin://plugin.video.youtube/channel/"+YOUTUBE_CHANNEL_ID_2+"/",
        thumbnail="http://mybuild.darkwebrepo.gq/infantil/angelina.jpg",
        folder=True )	
	
    plugintools.add_item( 
        #action="", 
        title="[COLOR cornflowerblue]3. Aprende conmigo - ABC123 en Español[/COLOR]",
        url="plugin://plugin.video.youtube/channel/"+YOUTUBE_CHANNEL_ID_3+"/",
        thumbnail="http://mybuild.darkwebrepo.gq/infantil/abc.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="[COLOR cornflowerblue]4. Atención Atención[/COLOR]",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_4+"/",
        thumbnail="http://mybuild.darkwebrepo.gq/infantil/atencion.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="[COLOR cornflowerblue]5. Auto City Español[/COLOR]",
        url="plugin://plugin.video.youtube/user/"+YOUTUBE_CHANNEL_ID_5+"/",
        thumbnail="http://mybuild.darkwebrepo.gq/infantil/auto.jpg",
        folder=True )
	
    plugintools.add_item( 
        #action="", 
        title="[COLOR cornflowerblue]6. Aventuras con los Kratt[/COLOR]",
        url="plugin://plugin.video.youtube/channel/"+YOUTUBE_CHANNEL_ID_6+"/",
        thumbnail="http://mybuild.darkwebrepo.gq/infantil/kratt.jpg",
        folder=True )	
	
    plugintools.add_item( 
        #action="", 
        title="[COLOR cornflowerblue]7. Caillou en Español[/COLOR]",
        url="plugin://plugin.video.youtube/channel/"+YOUTUBE_CHANNEL_ID_7+"/",
        thumbnail="http://mybuild.darkwebrepo.gq/infantil/caillou.jpg",
        folder=True )
	
    plugintools.add_item( 
        #action="", 
        title="[COLOR cornflowerblue]8. Chotoonz TV Español[/COLOR]",
        url="plugin://plugin.video.youtube/channel/"+YOUTUBE_CHANNEL_ID_8+"/",
        thumbnail="http://mybuild.darkwebrepo.gq/infantil/chotoonztv.jpg",
        folder=True )	
	
    plugintools.add_item( 
        #action="", 
        title="[COLOR cornflowerblue]9. ChuChuTV Español[/COLOR]",
        url="plugin://plugin.video.youtube/channel/"+YOUTUBE_CHANNEL_ID_9+"/",
        thumbnail="http://mybuild.darkwebrepo.gq/infantil/chuchu.jpg",
        folder=True )	
		
    plugintools.add_item( 
        #action="", 
        title="[COLOR cornflowerblue]10. Cuentos Infantiles Cortos[/COLOR]",
        url="plugin://plugin.video.youtube/channel/"+YOUTUBE_CHANNEL_ID_10+"/",
        thumbnail="http://mybuild.darkwebrepo.gq/infantil/cuentos-cortos.jpg",
        folder=True )
	
    plugintools.add_item( 
        #action="", 
        title="[COLOR cornflowerblue]11. El Reino a Jugar[/COLOR]",
        url="plugin://plugin.video.youtube/channel/"+YOUTUBE_CHANNEL_ID_11+"/",
        thumbnail="http://mybuild.darkwebrepo.gq/infantil/reinoajugar.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="[COLOR cornflowerblue]12. El Reino Infantil[/COLOR]",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_12+"/",
        thumbnail="http://mybuild.darkwebrepo.gq/infantil/reino.jpg",
        folder=True )
	
    plugintools.add_item( 
        #action="", 
        title="[COLOR cornflowerblue]13. Familia Telerín[/COLOR]",
        url="plugin://plugin.video.youtube/channel/"+YOUTUBE_CHANNEL_ID_13+"/",
        thumbnail="http://mybuild.darkwebrepo.gq/infantil/telerin.jpg",
        folder=True )
		
    plugintools.add_item( 
        #action="", 
        title="[COLOR cornflowerblue]14. Happy Learning Español[/COLOR]",
        url="plugin://plugin.video.youtube/channel/"+YOUTUBE_CHANNEL_ID_14+"/",
        thumbnail="http://mybuild.darkwebrepo.gq/infantil/happy.jpg",
        folder=True )
	
    plugintools.add_item( 
        #action="", 
        title="[COLOR cornflowerblue]15. JellyJamm Latino América[/COLOR]",
        url="plugin://plugin.video.youtube/channel/"+YOUTUBE_CHANNEL_ID_15+"/",
        thumbnail="http://mybuild.darkwebrepo.gq/infantil/jellyjam.jpg",
        folder=True )
	
    plugintools.add_item( 
        #action="", 
        title="[COLOR cornflowerblue]16. Las Canciones del Zoo[/COLOR]",
        url="plugin://plugin.video.youtube/user/"+YOUTUBE_CHANNEL_ID_16+"/",
        thumbnail="http://mybuild.darkwebrepo.gq/infantil/zoo.jpg",
        folder=True )
		
    plugintools.add_item( 
        #action="", 
        title="[COLOR cornflowerblue]17. La Granja de Zenón[/COLOR]",
        url="plugin://plugin.video.youtube/user/"+YOUTUBE_CHANNEL_ID_17+"/",
        thumbnail="http://mybuild.darkwebrepo.gq/infantil/lagranja.jpg",
        folder=True )	
		
    plugintools.add_item( 
        #action="", 
        title="[COLOR cornflowerblue]18. Little Baby Boom Español[/COLOR]",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_18+"/",
        thumbnail="http://mybuild.darkwebrepo.gq/infantil/boom.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="[COLOR cornflowerblue]19. Mi Pequeña Biblia[/COLOR]",
        url="plugin://plugin.video.youtube/channel/"+YOUTUBE_CHANNEL_ID_19+"/",
        thumbnail="http://mybuild.darkwebrepo.gq/infantil/biblia.jpg",
        folder=True )
	
    plugintools.add_item( 
        #action="", 
        title="[COLOR cornflowerblue]20. Payaso Remi TV[/COLOR]",
        url="plugin://plugin.video.youtube/channel/"+YOUTUBE_CHANNEL_ID_20+"/",
        thumbnail="http://mybuild.darkwebrepo.gq/infantil/remi.jpg",
        folder=True )	

    plugintools.add_item( 
        #action="", 
        title="[COLOR cornflowerblue]21. Peppa Pig Español[/COLOR]",
        url="plugin://plugin.video.youtube/channel/"+YOUTUBE_CHANNEL_ID_21+"/",
        thumbnail="http://mybuild.darkwebrepo.gq/infantil/peppa.jpg",
        folder=True )
		
    plugintools.add_item( 
        #action="", 
        title="[COLOR cornflowerblue]22. Pica - Pica[/COLOR]",
        url="plugin://plugin.video.youtube/user/"+YOUTUBE_CHANNEL_ID_22+"/",
        thumbnail="http://mybuild.darkwebrepo.gq/infantil/pica-pica.jpg",
        folder=True )	
	
    plugintools.add_item( 
        #action="", 
        title="[COLOR cornflowerblue]23. Piccolo Mondo PR[/COLOR]",
        url="plugin://plugin.video.youtube/user/"+YOUTUBE_CHANNEL_ID_23+"/",
        thumbnail="http://mybuild.darkwebrepo.gq/infantil/piccolomundo.jpg",
        folder=True )	
	
    plugintools.add_item( 
        #action="", 
        title="[COLOR cornflowerblue]24. Polly Pocket en Español[/COLOR]",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_24+"/",
        thumbnail="http://mybuild.darkwebrepo.gq/infantil/polly.jpg",
        folder=True )
	
    plugintools.add_item( 
        #action="", 
        title="[COLOR cornflowerblue]25. Rosita Fresita[/COLOR]",
        url="plugin://plugin.video.youtube/user/"+YOUTUBE_CHANNEL_ID_25+"/",
        thumbnail="http://mybuild.darkwebrepo.gq/infantil/rosita.jpg",
        folder=True )
	
    plugintools.add_item( 
        #action="", 
        title="[COLOR cornflowerblue]26. Sésamo[/COLOR]",
        url="plugin://plugin.video.youtube/user/"+YOUTUBE_CHANNEL_ID_26+"/",
        thumbnail="http://mybuild.darkwebrepo.gq/infantil/sesamo.jpg",
        folder=True )	
		
    plugintools.add_item( 
        #action="", 
        title="[COLOR cornflowerblue]27. Teletubbies en Español[/COLOR]",
        url="plugin://plugin.video.youtube/channel/"+YOUTUBE_CHANNEL_ID_27+"/",
        thumbnail="http://mybuild.darkwebrepo.gq/infantil/teletubbies.jpg",
        folder=True )	

    plugintools.add_item( 
        #action="", 
        title="[COLOR cornflowerblue]28. Toobys Español[/COLOR]",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_28+"/",
        thumbnail="http://mybuild.darkwebrepo.gq/infantil/toobys.jpg",
        folder=True )
	
    plugintools.add_item( 
        #action="", 
        title="[COLOR cornflowerblue]29. Tu y yo Cantando[/COLOR]",
        url="plugin://plugin.video.youtube/user/"+YOUTUBE_CHANNEL_ID_29+"/",
        thumbnail="http://mybuild.darkwebrepo.gq/infantil/tuyyo.jpg",
        folder=True )	

    plugintools.add_item( 
        #action="", 
        title="[COLOR cornflowerblue]30. Wildbrain Español[/COLOR]",
        url="plugin://plugin.video.youtube/user/"+YOUTUBE_CHANNEL_ID_30+"/",
        thumbnail="http://mybuild.darkwebrepo.gq/infantil/wild.jpg",
        folder=True )
run()
