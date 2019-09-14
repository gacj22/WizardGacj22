# -*- coding: utf-8 -*-
#------------------------------------------------------------
#------------------------------------------------------------
# License: GPL (http://www.gnu.org/licenses/gpl-3.0.html)
# Based on code from youtube addon
#------------------------------------------------------------

import os
import sys
import plugintools
import xbmc,xbmcaddon
from addon.common.addon import Addon

addonID = 'plugin.video.motor99'
addon = Addon(addonID, sys.argv)
local = xbmcaddon.Addon(id=addonID)
icon = local.getAddonInfo('icon')

YOUTUBE_CHANNEL_ID1 = "Formula1"
YOUTUBE_CHANNEL_ID2 = "wrc"
YOUTUBE_CHANNEL_ID3 = "laf1es"
YOUTUBE_CHANNEL_ID4 = "MonsterWorldRally"
YOUTUBE_CHANNEL_ID5 = "UCLKDc9r7EjOtfOpytVbpDyg"
YOUTUBE_CHANNEL_ID6 = "FIAFormulaE"
YOUTUBE_CHANNEL_ID7 = "DTMinternational"
YOUTUBE_CHANNEL_ID8 = "TheFIAWTCC"
YOUTUBE_CHANNEL_ID9 = "MotoGP"
YOUTUBE_CHANNEL_ID10 = "dakar"
YOUTUBE_CHANNEL_ID11 = "gt1world"
YOUTUBE_CHANNEL_ID12 = "UCCKEHIkEVrivZFffRWkE37w"
YOUTUBE_CHANNEL_ID13 = "BestMotorcycleVideos"
YOUTUBE_CHANNEL_ID14 = "UC0mJA1lqKjB4Qaaa2PNf0zg"


# Entry point
def run():
    plugintools.log("motor99.run")
    
    # Get params
    params = plugintools.get_params()
    
    if params.get("action") is None:
        main_list(params)
    else:
        pass
    
    plugintools.close_item_list()

# Main menu
def main_list(params):
    plugintools.log("motor99.main_list "+repr(params))

    plugintools.add_item( 
        #action="", 
        title="F1",
        url="plugin://plugin.video.youtube/user/"+YOUTUBE_CHANNEL_ID1+"/",
        thumbnail="https://4.bp.blogspot.com/-bcFnq1jH9i8/WOO6pEkyJ-I/AAAAAAAAbPQ/jARYtS2hW7Epbdx9o1FMEBeunJvlWb7LgCLcB/s1600/f1.png",
		fanart="https://2.bp.blogspot.com/-ZUKPGAc_AsM/WOIsO_YQfBI/AAAAAAAAbK4/jTR1ONZgLsIk2K0DSdi2eyOE9Yv_Y1LWACLcB/s1600/formula_1_track_aerial_view-wallpaper-1920x1080.jpg",
        folder=True )

   		
    plugintools.add_item( 
        #action="", 
        title="WRC",
        url="plugin://plugin.video.youtube/user/"+YOUTUBE_CHANNEL_ID2+"/",
        thumbnail="https://4.bp.blogspot.com/-0qMIssKqlh8/WOO3cvFrZpI/AAAAAAAAbO0/Lt-xTFuTqdogY1mGx3rKEiJzFIIRMeyDgCLcB/s1600/WRC.png",
    	fanart="https://4.bp.blogspot.com/-A4lo468Vwqg/WOIzy1FwgDI/AAAAAAAAbLY/UAZw9u-Jc2Qc_QuKWoLBnVxWZQ96q3ybQCLcB/s1600/wc1788960.jpg",
		folder=True )

    plugintools.add_item( 
        #action="", 
        title="SoyMotor",
        url="plugin://plugin.video.youtube/user/"+YOUTUBE_CHANNEL_ID3+"/",
        thumbnail="https://3.bp.blogspot.com/-Vzl_jNdMt7Y/WOO3QX51ClI/AAAAAAAAbOw/pllRmOti9z0bEhflLO5-fOIP9dTVsv1EwCLcB/s1600/soymotor.png",
    	fanart="",
		folder=True )
		


    plugintools.add_item( 
        #action="", 
        title="Ken Block",
        url="plugin://plugin.video.youtube/user/"+YOUTUBE_CHANNEL_ID4+"/",
        thumbnail="https://1.bp.blogspot.com/-a9R8Ps5s4yA/XUPe1WyaniI/AAAAAAAAy5Y/pQUc0opJCo4D8gA0SfnrcGHcflK0aRu4wCLcBGAs/s1600/Sin%2Bt%25C3%25ADtulo3.png",
    	fanart="https://4.bp.blogspot.com/-XqT1MIARctc/XUPexKHngxI/AAAAAAAAy5Q/O1Z6QxhZi8wSuTrhPncTsEzM7IkvfKiEACLcBGAs/s1600/189919.jpg",
		folder=True ) 

 
    plugintools.add_item( 
        #action="", 
        title="GT4",
        url="plugin://plugin.video.youtube/channel/"+YOUTUBE_CHANNEL_ID5+"/",
        thumbnail="https://1.bp.blogspot.com/--a0BTGbYrvI/WOOkBhYOriI/AAAAAAAAbOM/n8Srau6rAKcnNtp3xltLfxwtgIQIrJ5DACLcB/s1600/gt42.png",
    	fanart="https://4.bp.blogspot.com/-flWb4l6LLIU/WON_X04gBkI/AAAAAAAAbNY/f344C4KEyLYrpxmculHZys-lJfXg3DZCgCLcB/s1600/gt4-series-race-racing-g-t-rally-grand-prix-supercar-0Yjv.jpg",
		folder=True )
		
    plugintools.add_item( 
        #action="", 
        title="Formula E",
        url="plugin://plugin.video.youtube/user/"+YOUTUBE_CHANNEL_ID6+"/",
        thumbnail="https://4.bp.blogspot.com/-_iBxROf68zs/WOO4Wmd8R8I/AAAAAAAAbO8/F314pmeuct0Amvj_WR6XJxPNrRKainNDACLcB/s1600/formula%2Be.png",
    	fanart="https://1.bp.blogspot.com/-BOrvvzz5beo/WOOBzE-T3sI/AAAAAAAAbNw/HyoEsncQD0MWKBrDhRIPc265yd56NagKACLcB/s1600/ds-virgin-16-17-2.jpg",
		folder=True )

    plugintools.add_item( 
        #action="", 
        title="DTM",
        url="plugin://plugin.video.youtube/user/"+YOUTUBE_CHANNEL_ID7+"/",
        thumbnail="https://3.bp.blogspot.com/-83zc0sPPxVE/WOO9sJOpPhI/AAAAAAAAbPc/c0Cvr9xhVNwueZ9AtxYtWUd-a2ykoM-ngCLcB/s1600/dtm.png",
    	fanart="https://1.bp.blogspot.com/-sInGT_rOHV8/WOO97-gS1xI/AAAAAAAAbPg/C0ivz9K5eYsQXdIG1lQALz7u_VgVOZkqgCLcB/s1600/cars_tuning_BMW_M3_DTM_Concept_1920x1200.jpg",
		folder=True )		

    plugintools.add_item( 
        #action="", 
        title="WTCR",
        url="plugin://plugin.video.youtube/user/"+YOUTUBE_CHANNEL_ID8+"/",
        thumbnail="https://4.bp.blogspot.com/-cGpnR0ABN6M/XUMtx6AZUEI/AAAAAAAAytE/6nzdZnikaSU4WehYrcw9Qipkfb6htvebQCLcBGAs/s1600/Sin%2Bt%25C3%25ADtulo.png",
    	fanart="https://1.bp.blogspot.com/-t-rAmPhaRY4/XUMs_5-iiRI/AAAAAAAAys8/39U61XOSEoQC5Tew-LXJEhfTV5O_bxLfgCLcBGAs/s1600/wtcr.jpg",
		folder=True )	

    plugintools.add_item( 
        #action="", 
        title="MotoGP",
        url="plugin://plugin.video.youtube/user/"+YOUTUBE_CHANNEL_ID9+"/",
        thumbnail="https://2.bp.blogspot.com/-GEk0m969hdo/WOPDDhYhyXI/AAAAAAAAbP4/Y7wgq239NfsYbzOFd2kNtb5dB1J4sFcUwCLcB/s1600/motogp.png",
    	fanart="https://4.bp.blogspot.com/-aaksYwlqINU/WOPDERTNgWI/AAAAAAAAbP8/pQtxsQ-gUPE4ul2UIdhkKSkqm5BrAauuQCLcB/s1600/malasia-test-motogp-2016.jpg",
		folder=True )	
		
    plugintools.add_item( 
        #action="", 
        title="Dakar",
        url="plugin://plugin.video.youtube/user/"+YOUTUBE_CHANNEL_ID10+"/",
        thumbnail="https://1.bp.blogspot.com/-6VRxgFpkQcQ/XUP4ymOjzKI/AAAAAAAAy7w/4ISEy0j8ZtoRszonZDHkzGwjmEvAW61pwCLcBGAs/s1600/dakar_logo.jpg",
    	fanart="https://4.bp.blogspot.com/-nz_GKAesNmY/XUP5Zpx6xVI/AAAAAAAAy74/w3na51zCN88G1ZOokfUQ68ruVwt_fVjuwCLcBGAs/s1600/dakar-rally-wallpapers-31001-6043285.jpg",
		folder=True )			
		
		
    plugintools.add_item( 
        #action="", 
        title="Blancpain GT Series",
        url="plugin://plugin.video.youtube/user/"+YOUTUBE_CHANNEL_ID11+"/",
        thumbnail="https://4.bp.blogspot.com/-l4tZ8qcS0ZQ/XUP_-piPQhI/AAAAAAAAy8E/zCg5bpDDypA9oVBGa3upQ_fZ_3Y1510fACLcBGAs/s1600/timthumb.jpg",
    	fanart="https://4.bp.blogspot.com/-rnlhHpIaOqE/XUP_-uzkYmI/AAAAAAAAy8I/zf210sSCCTkka9BJzkelS7A3oVutMfQQACLcBGAs/s1600/thumb-1920-353036.jpg",
		folder=True )
		
    plugintools.add_item( 
        #action="", 
        title="IMSA Español",
        url="plugin://plugin.video.youtube/channel/"+YOUTUBE_CHANNEL_ID12+"/",
        thumbnail="https://3.bp.blogspot.com/-XCVlgugS02M/XUQFCSRvdpI/AAAAAAAAy9c/GFUdZ5C5zUoNSJMByrK-VmossgoobK9tACLcBGAs/s1600/descarga%2B%25281%2529.png",
    	fanart="https://4.bp.blogspot.com/-x9aW44FkJXo/XUQFD8IO4YI/AAAAAAAAy9g/F6gNAL4C7rollXEr5Tnfw3tvJXMpdi8xACLcBGAs/s1600/08012019_iwsc_roadamerica_preview_1280x626.jpg",
		folder=True )			

    plugintools.add_item( 
        #action="", 
        title="EnduroLife",
        url="plugin://plugin.video.youtube/user/"+YOUTUBE_CHANNEL_ID13+"/",
        thumbnail="https://1.bp.blogspot.com/-IJrGjpBRW0M/XUQLM_01FEI/AAAAAAAAy9w/NoayTLdTOH4d_DDIOctK4xiNON2YAk7WACLcBGAs/s1600/lkyDx1zD_400x400.jpg",
    	fanart="https://4.bp.blogspot.com/-ircdChh4D8o/XUQLO4duS2I/AAAAAAAAy90/L4-2_4eZnPwDSBdSBUegFzXq6J7h8xMDgCLcBGAs/s1600/wp1900761.jpg",
		folder=True )

    plugintools.add_item( 
        #action="", 
        title="Red Bull Motorsport",
        url="plugin://plugin.video.youtube/channel/"+YOUTUBE_CHANNEL_ID14+"/",
        thumbnail="https://1.bp.blogspot.com/-piSlBiC2rTA/XUQOotqIU9I/AAAAAAAAy-E/F_DtbXWHZ_Eh8vMw7ZvGefy3YLMUD6e4ACLcBGAs/s1600/unnamed.jpg",
    	fanart="https://3.bp.blogspot.com/-qGAANz5BBWo/XUQOm5WjkgI/AAAAAAAAy-A/OBhnxqZ30NgZK7Q4tqomFBr2wlyCWbvoQCLcBGAs/s1600/motoring-collection.jpg",
		folder=True )		
		
run()