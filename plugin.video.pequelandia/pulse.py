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

addonID = 'plugin.video.pequelandia'
addon = Addon(addonID, sys.argv)
local = xbmcaddon.Addon(id=addonID)
icon = local.getAddonInfo('icon')

xbmc.executebuiltin('Container.SetViewMode(500)')

YOUTUBE_CHANNEL_ID_1 = "PL8snGkhBF7njuEl8V642ZeFwcbVRRPFLG"
YOUTUBE_CHANNEL_ID_2 = "PL8snGkhBF7ngDp1oJtx5VcjwatxZn8xLK"
YOUTUBE_CHANNEL_ID_3 = "PLusSrZ-7Aiev0uxn3c7KcoH9msKrXkJW7"
YOUTUBE_CHANNEL_ID_4 = "LLLsooMJoIpl_7ux2jvdPB-Q"
YOUTUBE_CHANNEL_ID_5 = "PLusSrZ-7AievwZv-Zc56vIAb-BxZeYDyC"
YOUTUBE_CHANNEL_ID_6 = "PLvOE0yRoG4X_js9ETBSDeWrRxrrnWdzm_"
YOUTUBE_CHANNEL_ID_7 = "PLWYQuS6aEMRDcHza5LQjPbRkrwu2qt6DT"
YOUTUBE_CHANNEL_ID_8 = "PLcn453b0kzi_XxypPWQKCVKGxop_nF1qa"
YOUTUBE_CHANNEL_ID_9 = "PLDUvSiwQy5cEx31-XjBJCfcU1K9Lox79L"
YOUTUBE_CHANNEL_ID_10 = "PLusSrZ-7AiesCVcITlK7S6eEh2bnx52n6"
YOUTUBE_CHANNEL_ID_11 = "PL5tb2ODzv2rSWKrSeZwtZrPgvekFyU33P"
YOUTUBE_CHANNEL_ID_12 = "PL8snGkhBF7njO0QvtE97AJFL3xZYQSGh5"
YOUTUBE_CHANNEL_ID_13 = "PLDUvSiwQy5cEklxOj93LMaoqyjtoTr05t" 
YOUTUBE_CHANNEL_ID_14 = "PLJK3tljUgjzI0EVB9IGOWT4Uhiz_f7HsT" 
YOUTUBE_CHANNEL_ID_15 = "PL8snGkhBF7nhEc52y4C1S9yqjBQSLCmT4"
YOUTUBE_CHANNEL_ID_16 = "PL_o8kq_GWfOlkFJ7ugSjRQ_soFhluWbB_"
YOUTUBE_CHANNEL_ID_17 = "PL_o8kq_GWfOkin4jcvYdUTSP0x2XED8ll" 
YOUTUBE_CHANNEL_ID_18 = "PLuff7HnBIm5V0ty1LNEQBoI9x34UpC4iF"
YOUTUBE_CHANNEL_ID_19 = "PLgK76qegaoMzghYeQ5xMyZK9bdFfMKvdd"
YOUTUBE_CHANNEL_ID_20 = "PLD-2f-nig1ajeEuckkeJOxyp2MctiVQcC" 
YOUTUBE_CHANNEL_ID_21 = "PLD-2f-nig1ajD9pjWU-zpnAkudHqphTsE"
YOUTUBE_CHANNEL_ID_22 = "PL3BEF4668E8568186"
YOUTUBE_CHANNEL_ID_23 = "PLF457B8EA1B3039DB" 
YOUTUBE_CHANNEL_ID_24 = "PLD-2f-nig1ajk15N3oKyMA9qrZirbjhzF"
YOUTUBE_CHANNEL_ID_25 = "PLeY6ZuXvnilX9p_XwmFsYbZm12IeEPF1E"
YOUTUBE_CHANNEL_ID_26 = "PLeY6ZuXvnilUOmxS5s_JmtBjeOrjp7nRg"
YOUTUBE_CHANNEL_ID_27 = "PLSyxqIHOw0ZMMjw741Pqn494SalYHVRMv" 
YOUTUBE_CHANNEL_ID_28 = "LLK1i2UviaXLUNrZlAFpw_jA"
YOUTUBE_CHANNEL_ID_29 = "FLP6YCSvxq2HEX33Sd-iC4zw"
YOUTUBE_CHANNEL_ID_30 = "LLGkVdu_EVrqqxQ7OnLFK8RQ"
YOUTUBE_CHANNEL_ID_31 = "PLguZfwIrWHOZl5zCA8P4xNjFUMw4OjRHI"
YOUTUBE_CHANNEL_ID_32 = "PLguZfwIrWHOZnMgmt32VOetq3a_cSr7zs"
YOUTUBE_CHANNEL_ID_33 = "PLfVDJFxsvnTRdnn11-X_B8NvO4Lcn3uNG" 
YOUTUBE_CHANNEL_ID_34 = "PLfVDJFxsvnTRi2fuVBjMK2RDhEbi9hFjJ"
YOUTUBE_CHANNEL_ID_35 = "PLfVDJFxsvnTRT0VbCB4wdIXUoQdFCKS3W"
YOUTUBE_CHANNEL_ID_36 = "LL_WjKI3-m_CLhx0gjctCSkQ"
YOUTUBE_CHANNEL_ID_37 = "PLl3ShNbWJXFBniubEJIefEswXiL5IP-f4"
YOUTUBE_CHANNEL_ID_130 = "PLEFC1282E4331AC14"
YOUTUBE_CHANNEL_ID_133 = "LLwDjQReLwrODEwY1qoE-wuA"
YOUTUBE_CHANNEL_ID_138 = "PLMeWlmsH8nbGVodj5zw-fsUoU8SaA54Vk"
YOUTUBE_CHANNEL_ID_139 = "PLz9jduKZZp17NLTiptvJ5tqfiJTTeUMvA"
YOUTUBE_CHANNEL_ID_140 = "LLe1T7EkHIHvOIWBG1Om8xHA"
YOUTUBE_CHANNEL_ID_141 = "PLi6wag8FdvTCGXRSWK7rHw-mmHBeiGW0U"
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
        title="Mejores Juguetes",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_141+"/",
        thumbnail="https://i.imgur.com/z4hX7sb.png",
        folder=True )
	
    plugintools.add_item( 
        #action="", 
        title="TOYS on the go!",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_140+"/",
        thumbnail="https://i.imgur.com/xKWeUW0.jpg",
        folder=True )
		
    plugintools.add_item( 
        #action="", 
        title="Tremending girls",
        url="plugin://plugin.video.youtube/channel/"+YOUTUBE_CHANNEL_ID_139+"/",
        thumbnail="https://i.imgur.com/MFQhLQo.jpg",
        folder=True )
		
	
    plugintools.add_item( 
        #action="", 
        title="Historias de Juguetes",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_138+"/",
        thumbnail="https://i.imgur.com/fnSpw6m.jpg",
        folder=True )
	

    plugintools.add_item( 
        #action="", 
        title="Toys & happy kids",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_133+"/",
        thumbnail="https://i.imgur.com/NY98v0f.jpg",
        folder=True )
	
    plugintools.add_item( 
        #action="", 
        title="Disney Sing Along",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_130+"/",
        thumbnail="https://i.imgur.com/Gh9Kb8a.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="LittleBabyBum Español",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_7+"/",
        thumbnail="https://i.imgur.com/KhtKS7C.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Super Simple Songs",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_4+"/",
        thumbnail="https://i.imgur.com/DssrbEb.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="ABC Song For Children",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_6+"/",
        thumbnail="https://i.imgur.com/1GOyVqz.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Cortometrajes para educar en valores",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_11+"/",
        thumbnail="https://i.imgur.com/lKHpoUK.png",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Muffalo Potato - Animals",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_5+"/",
        thumbnail="https://i.imgur.com/dn59edh.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Muffalo Potato - Movies",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_10+"/",
        thumbnail="https://i.imgur.com/dn59edh.jpg",
        folder=True )
		
    plugintools.add_item( 
        #action="", 
        title="Muffalo Potato - Comics",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_3+"/",
        thumbnail="https://i.imgur.com/dn59edh.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Cosmic Kids Yoga - Playlist for older kids",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_15+"/",
        thumbnail="https://i.imgur.com/lpnZtR2.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Cosmic Kids Yoga - Peace Out Guided Relaxation for Kids",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_12+"/",
        thumbnail="https://i.imgur.com/lpnZtR2.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Cosmic Kids Yoga - Kids yoga adventures starting from the beginning",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_1+"/",
        thumbnail="https://i.imgur.com/lpnZtR2.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Cosmic Kids Yoga - Our mindfulness for kids series",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_2+"/",
        thumbnail="https://i.imgur.com/lpnZtR2.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Telmo y Tula, dibujos divertidos y educativos de manualidades y recetas",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_14+"/",
        thumbnail="https://i.imgur.com/R3Xn9Ei.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="The Artful Parent - Action Art for Kids",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_9+"/",
        thumbnail="https://i.imgur.com/MApfFNw.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="The Artful Parent - Kids Science Activities",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_13+"/",
        thumbnail="https://i.imgur.com/MApfFNw.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Gogo's Adventures with English",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_8+"/",
        thumbnail="https://i.imgur.com/w6uSClq.jpg",
        folder=True )
		
    plugintools.add_item( 
        #action="", 
        title="LlegaExperimentos - Hazlo Tú Mismo",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_16+"/",
        thumbnail="https://i.imgur.com/JEuZMcX.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="LlegaExperimentos - Experimentos Caseros ",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_17+"/",
        thumbnail="https://i.imgur.com/JEuZMcX.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Hoy no hay cole",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_18+"/",
        thumbnail="https://i.imgur.com/SfFokXy.jpg",
        folder=True )
		
    plugintools.add_item( 
        #action="", 
        title="Luli TV Español",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_19+"/",
        thumbnail="https://i.imgur.com/B7oNi9b.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="La Educoteca - Ciencias Naturales",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_20+"/",
        thumbnail="https://i.imgur.com/BkgGGPe.jpg",
        folder=True )
		
    plugintools.add_item( 
        #action="", 
        title="La Educoteca - Ciencias Sociales",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_21+"/",
        thumbnail="https://i.imgur.com/BkgGGPe.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="La Educoteca - Matematicas",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_22+"/",
        thumbnail="https://i.imgur.com/BkgGGPe.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="La Educoteca - Lengua y Literatura",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_23+"/",
        thumbnail="https://i.imgur.com/BkgGGPe.jpg",
        folder=True )
		
    plugintools.add_item( 
        #action="", 
        title="La Educoteca - El Gran Libro Viajero",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_24+"/",
        thumbnail="https://i.imgur.com/BkgGGPe.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Cantando Aprendo a Hablar",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_25+"/",
        thumbnail="https://i.imgur.com/kXnF3E1.jpg",
        folder=True )
		
    plugintools.add_item( 
        #action="", 
        title="Cantando Aprendo a Hablar - Lenguaje de Signos",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_26+"/",
        thumbnail="https://i.imgur.com/kXnF3E1.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="El Mundo de Luna",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_27+"/",
        thumbnail="https://i.imgur.com/anKZu7T.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="El reino infantil",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_28+"/",
        thumbnail="https://i.imgur.com/l69Pow1.jpg",
        folder=True )
		
    plugintools.add_item( 
        #action="", 
        title="Cantajuegos",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_29+"/",
        thumbnail="https://i.imgur.com/eMtdrnY.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Happy Learning Español",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_30+"/",
        thumbnail="https://i.imgur.com/rb8docg.jpg",
        folder=True )
		
    plugintools.add_item( 
        #action="", 
        title="Cosas de Peques - Cuentos infantiles animados en español",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_31+"/",
        thumbnail="https://i.imgur.com/JJpREB8.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Cosas de Peques - Manualidades faciles para niños",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_32+"/",
        thumbnail="https://i.imgur.com/JJpREB8.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Audicion y Lenguaje - Juegos Educativos",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_33+"/",
        thumbnail="https://i.imgur.com/mPRS3EV.jpg",
        folder=True )
		
    plugintools.add_item( 
        #action="", 
        title="Audicion y Lenguaje - Estimulación del Lenguaje de 3 a 6 años",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_34+"/",
        thumbnail="https://i.imgur.com/mPRS3EV.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Audicion y Lenguaje - Discriminacion Auditiva de Sonidos Cotidianos",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_35+"/",
        thumbnail="https://i.imgur.com/mPRS3EV.jpg",
        folder=True )
		
    plugintools.add_item( 
        #action="", 
        title="guiainfantil",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_36+"/",
        thumbnail="https://i.imgur.com/iOtJzWE.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Canciones Infantiles en Lenguaje de Signos",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_37+"/",
        thumbnail="https://i.imgur.com/dfE5Agj.jpg",
        folder=True )

run()