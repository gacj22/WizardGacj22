# -*- coding: utf-8 -*-
#------------------------------------------------------------
#Catoal Kodi Addon
#------------------------------------------------------------
# License: GPL (http://www.gnu.org/licenses/gpl-3.0.html)
# Based on code from youtube addon
#------------------------------------------------------------

import os
import sys
import plugintools
import xbmc,xbmcaddon
from addon.common.addon import Addon

addonID = 'plugin.video.football'
addon = Addon(addonID, sys.argv)
local = xbmcaddon.Addon(id=addonID)
icon = local.getAddonInfo('icon')

YOUTUBE_CHANNEL_ID_1 = "UC5uIs17v-d8P5SoorOop3Pw"
YOUTUBE_CHANNEL_ID_2 = "UCU799bB71p_eCJ-1eLoizDA"
YOUTUBE_CHANNEL_ID_3 = "UCXoTbxGHNa0NrVBeMOflawA"
YOUTUBE_CHANNEL_ID_4 = "UCtREdU7e21_xH0z4BGy0RjQ"
YOUTUBE_CHANNEL_ID_5 = "UCb6yvgicm35fe4JoSbssGlg/playlists"
YOUTUBE_CHANNEL_ID_6 = "UCfKLFxF72AMvZANxwa05eTw/playlists"

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
        title="                                           [COLOR skyblue]NCAA.[/COLOR]",
        url="plugin://plugin.video.youtube/channel/"+YOUTUBE_CHANNEL_ID_1+"/",
        thumbnail="https://i.imgur.com/mdIWGpR.png",
		fanart="",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="                                  [COLOR skyblue]NCAA2[/COLOR]",
        url="plugin://plugin.video.youtube/channel/"+YOUTUBE_CHANNEL_ID_2+"/",
        thumbnail="https://i.imgur.com/5rsLVtl.jpg",
		fanart="",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="                                [COLOR skyblue]OSOS DE RIVAS[/COLOR]",
        url="plugin://plugin.video.youtube/channel/"+YOUTUBE_CHANNEL_ID_3+"/",
        thumbnail="https://i.imgur.com/5Lipe0f.jpg",
		fanart="",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="                                [COLOR skyblue]BIG DAVE[/COLOR]",
        url="plugin://plugin.video.youtube/channel/"+YOUTUBE_CHANNEL_ID_4+"/",
        thumbnail="https://i.imgur.com/3ai9oD4.png",
		fanart="",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="                           [COLOR red]AAF[/COLOR]",
        url="plugin://plugin.video.youtube/channel/"+YOUTUBE_CHANNEL_ID_5+"/",
        thumbnail="https://i.imgur.com/QmN12BA.png",
		fanart="",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="                                            [COLOR skyblue]NFL[/COLOR]",
        url="plugin://plugin.video.youtube/channel/"+YOUTUBE_CHANNEL_ID_6+"/",
        thumbnail="https://i.imgur.com/mLwDaCn.png",
		fanart="",
        folder=True ) 
		
		
run()
