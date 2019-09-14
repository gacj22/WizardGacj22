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

addonID = 'plugin.video.MyHR'
addon = Addon(addonID, sys.argv)
local = xbmcaddon.Addon(id=addonID)
icon = local.getAddonInfo('icon')

xbmc.executebuiltin('Container.SetViewMode(500)')

YOUTUBE_CHANNEL_ID_1 = "PLhQCJTkrHOwSX8LUnIMgaTq3chP1tiTut"
YOUTUBE_CHANNEL_ID_2 = "PL4033C6D21D7D28AC"
YOUTUBE_CHANNEL_ID_3 = "PLw6p6PA8M2miu0w4K1g6vQ1BHUBeyM4_-"
YOUTUBE_CHANNEL_ID_4 = "PLy8LfIp6j3aK2vtj-Xjhk8j5sAzGGrn0c"
YOUTUBE_CHANNEL_ID_5 = "PL4997816004E33B57"
YOUTUBE_CHANNEL_ID_6 = "PLKX9ut-1fNpg0VULPOAytjAgMG7uMDPvx"
YOUTUBE_CHANNEL_ID_7 = "LLHm_D4kNQaRshalYoB1qtbw"
YOUTUBE_CHANNEL_ID_8 = "PL2DADA850ADEEEAFC"
YOUTUBE_CHANNEL_ID_9 = "PL3oW2tjiIxvQO6yqJEkrP47yYG_pJ7XJU"
YOUTUBE_CHANNEL_ID_10 = "PLf7fnw8RkLVda0FdsKI1Eddf0NQOLwuxe"
YOUTUBE_CHANNEL_ID_12 = "PLWtm40fzHZUEE8HBuuC0qEEeUfZgGM169"
YOUTUBE_CHANNEL_ID_13 = "PLEHyYmFSaMj7NACGLGN38GTRX7LJHGlbP" 
YOUTUBE_CHANNEL_ID_14 = "PLz6VSFz0rvTILBiM3TyoOrdO-Wa8YTP0a" 
YOUTUBE_CHANNEL_ID_15 = "PLB4975D47295EFA7F"
YOUTUBE_CHANNEL_ID_16 = "PLCA9A9B18BE3342D8"
YOUTUBE_CHANNEL_ID_17 = "PLRr9ttYZmQQ-aJ0HW5u-5B0JSLA6xPzPb" 
YOUTUBE_CHANNEL_ID_130 = "PL9NMEBQcQqlzwlwLWRz5DMowimCk88FJk"
YOUTUBE_CHANNEL_ID_133 = "PL4eNmxXg4ASoo7b1BHaje33pBMU4tyliW"
YOUTUBE_CHANNEL_ID_138 = "PLqWKk2RlcD8Rm-vt6B_SP4JQZ2nxWYrxr"
YOUTUBE_CHANNEL_ID_140 = "PLmiGpUEtQi65TseIjI1x-V_6gweGl1wnU"
YOUTUBE_CHANNEL_ID_141 = "PLmiGpUEtQi646IuqxK7qOfV7rk3yMfzvp"
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
        title="Avalanch",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_141+"/",
        thumbnail="https://i.imgur.com/DgBYGlH.jpg",
        folder=True )
	
    plugintools.add_item( 
        #action="", 
        title="Nocturnia",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_140+"/",
        thumbnail="https://i.imgur.com/t9CpcUR.jpg",
        folder=True )
		
    plugintools.add_item( 
        #action="", 
        title="Best Rock Songs Of All Time",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_138+"/",
        thumbnail="https://i.imgur.com/N4MUIUN.jpg",
        folder=True )
	

    plugintools.add_item( 
        #action="", 
        title="Hard Rock & Heavy Metal",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_133+"/",
        thumbnail="https://i.imgur.com/CeoOM1g.jpg",
        folder=True )
	
    plugintools.add_item( 
        #action="", 
        title="Mejores canciones: Hard rock",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_130+"/",
        thumbnail="https://i.imgur.com/nmTXl58.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Atmospheric Black Metal Albums",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_7+"/",
        thumbnail="https://i.imgur.com/4SqE9rc.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Metal Blade Records",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_4+"/",
        thumbnail="https://i.imgur.com/JA9rB7Y.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Amon Amarth",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_6+"/",
        thumbnail="https://i.imgur.com/LXIY5Re.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="ROCK (90's- 2000's)",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_5+"/",
        thumbnail="https://i.imgur.com/N4MUIUN.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Badass 90's Metal and Heavy Rock",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_10+"/",
        thumbnail="https://i.imgur.com/A7Q7Tq0.jpg",
        folder=True )
		
    plugintools.add_item( 
        #action="", 
        title="80's / 90's Music Videos",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_3+"/",
        thumbnail="https://i.imgur.com/VmlIf2c.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Hard Metal/Rock",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_15+"/",
        thumbnail="https://i.imgur.com/y38Cu70.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="The Best Rock & Metal Songs Of All Time",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_12+"/",
        thumbnail="https://i.imgur.com/QMfL099.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="100 Best Metal Songs of all time",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_1+"/",
        thumbnail="https://i.imgur.com/b0K6ARQ.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Extreme Death Metal",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_2+"/",
        thumbnail="https://i.imgur.com/SNPInqz.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="80S Hair Metal, Hard & Heavy, Glam Metal, Hard Rock, Heavy Metal",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_14+"/",
        thumbnail="https://i.imgur.com/4MuJJ3H.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Top Metal 2018 - Ultimate Hard Rock & Heavy Metal Playlist 2018",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_9+"/",
        thumbnail="https://i.imgur.com/zpUwE5J.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Female fronted hard rock/heavy metal music videos",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_13+"/",
        thumbnail="https://i.imgur.com/7KG2Xtm.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Pinoy hard rock metal",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_8+"/",
        thumbnail="https://i.imgur.com/cWCYz6A.jpg",
        folder=True )
		
    plugintools.add_item( 
        #action="", 
        title="Remastered: Simple Metal - Heavy Metal - Royalty Free Music",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_16+"/",
        thumbnail="https://i.imgur.com/JEBma7L.jpg",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Rock-Metal-Rock/Alternativo-Nu Metal-Hard Rock",
        url="plugin://plugin.video.youtube/playlist/"+YOUTUBE_CHANNEL_ID_17+"/",
        thumbnail="https://i.imgur.com/N4MUIUN.jpg",
        folder=True )

run()