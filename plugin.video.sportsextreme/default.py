# -*- coding: utf-8 -*-
#------------------------------------------------------------
# http://www.youtube.com/user/gsfvideos
#------------------------------------------------------------
# Licença: GPL (http://www.gnu.org/licenses/gpl-3.0.html)
# Baseado no código do addon youtube
#------------------------------------------------------------

import os
import sys
import time
import plugintools
import xbmc,xbmcaddon
from addon.common.addon import Addon

addonID = 'plugin.video.sportsextreme'
addon = Addon(addonID, sys.argv)
local = xbmcaddon.Addon(id=addonID)
#icon = local.getAddonInfo('icon')
icon = local.getAddonInfo('icon')
icon2 = "http://blog.kanui.com.br/wp-content/uploads/2014/06/capa.jpg"
icon3 = "http://i4.buimg.com/5c26b31435349775s.jpg"
icon4 = "http://rx.iscdn.net/2009/01/nit_logo_sm.jpg"
icon5 = "https://pbs.twimg.com/profile_images/570955454956576768/K_OSVgao.png"
icon6 = "http://www.racedepartment.com/data/featured_threads/icons/116/116361.jpg?1453312506"
icon7 = "http://www.whatson4littleones.com.au/images/cmsimages/0/header.jpg"
icon8 = "https://expresswriters.com/wp-content/uploads/2015/01/red-bull-logo.jpg"
icon9 = "http://scontent.cdninstagram.com/t51.2885-15/e35/14711954_207572883004760_5163720703307939840_n.jpg?ig_cache_key=MTM2ODk4NDgxNjk4OTMzNTM5Nw%3D%3D.2&se=8"
icon10 = "http://performance.ford.com/content/dam/fordracing/series/ford-gt/image/news/2016/06/2016-gt-lemans-02_800.jpg"
icon11 = "http://www.juharintanen.com/wp-content/uploads/2014/10/Drift-LOGO-800x329.jpg"
icon12 = "http://www.continentaltire.com/sites/default/files/images/news/CT15_Web_PartnerLogos-IMSA-755x505.jpg"
icon13 = "http://dskhvldhwok3h.cloudfront.net/image/upload/v1/products/557dbb2669702d0a9cf57700/sharing_images/pouw7aswbbiwdnmghrau.jpg"
icon14 = "http://o.aolcdn.com/hss/storage/midas/b5bf5ce16b396dc70168656be85f4bcb/201522023/finland-lapland-drifting.jpg"
icon15 = "http://a.espncdn.com/photo/2013/0316/as_smb_Hibbert_lakegeneva.jpg"
icon16 = "https://i.kinja-img.com/gawker-media/image/upload/s--brmh0_IF--/18b05dmufel7jjpg.jpg"
icon17 = "http://a.espncdn.com/photo/2011/0509/as_moto_vegasgal_16_800.JPG"
icon18 = "http://1000tvchannel.com/media/channel_images/2013/07/11/extreme.png"
icon19 = "http://www.sportsmarketing.fr/wp-content/uploads/2015/05/wsl-sponsor.jpg"
icon20 = "http://images.techtimes.com/data/images/full/152359/gopro-launches-award-program-that-will-pay-users-for-their-footage.png"
addonfolder = local.getAddonInfo('path')
resfolder = addonfolder + '/resources/'
entryurl=resfolder+"entrada.mp4"
YOUTUBE_CHANNEL_ID = "user/XGames"
YOUTUBE_CHANNEL_ID2 = "user/monsterenergy"
YOUTUBE_CHANNEL_ID3 = "user/NitroCircusOFFICIAL"
YOUTUBE_CHANNEL_ID4 = "user/globalmtb"
YOUTUBE_CHANNEL_ID5 = "user/wrc"
YOUTUBE_CHANNEL_ID6 = "user/monsterjamlive"
YOUTUBE_CHANNEL_ID7 = "user/redbull"
YOUTUBE_CHANNEL_ID8 = "user/TheHoonigans"
YOUTUBE_CHANNEL_ID9 = "user/FordRacingTV"
YOUTUBE_CHANNEL_ID10 = "user/driftstream2010"
YOUTUBE_CHANNEL_ID11 = "user/UnitedSportsCar"
YOUTUBE_CHANNEL_ID12 = "user/NIGHToftheJUMPscom"
YOUTUBE_CHANNEL_ID13 = "channel/UC9e8tSwrk2At3N2_S2nVzLA"
YOUTUBE_CHANNEL_ID14 = "channel/UCkNJy2dgxjMdbkbgT2W2_gg"
YOUTUBE_CHANNEL_ID15 = "user/Redbullairrace"
YOUTUBE_CHANNEL_ID16 = "user/SupercrossLive"
YOUTUBE_CHANNEL_ID17 = "user/XTremeVideo"
YOUTUBE_CHANNEL_ID18 = "user/ASPWorldTour"
YOUTUBE_CHANNEL_ID19 = "user/GoProMX"
# Ponto de Entrada
def run():
	# Pega Parâmetros
	params = plugintools.get_params()
	
	if params.get("action") is None:
		xbmc.Player().play(entryurl)
		
		while xbmc.Player().isPlaying():
			time.sleep(1)

		main_list(params)
	else:
		action = params.get("action")
		exec action+"(params)"

	plugintools.close_item_list()

# Menu Principal
def main_list(params):
	plugintools.log("Xgames.main_list "+repr(params))
	
	plugintools.log("Xgames.run")
	
	#plugintools.direct_play(str(entryurl))

plugintools.add_item(
		title = "[B][COLOR red]XGAMES[/B][/COLOR]",
		url = "plugin://plugin.video.youtube/"+YOUTUBE_CHANNEL_ID+"/",
		thumbnail = icon2,
		folder = True )
		
plugintools.add_item(
		title = "[B][COLOR red]MONSTER ENERGY[/B][/COLOR]",
		url = "plugin://plugin.video.youtube/"+YOUTUBE_CHANNEL_ID2+"/",
		thumbnail = icon3,
		folder = True )
		
plugintools.add_item(
		title = "[B][COLOR red]NITRO CIRCUS[/B][/COLOR]",
		url = "plugin://plugin.video.youtube/"+YOUTUBE_CHANNEL_ID3+"/",
		thumbnail = icon4,
		folder = True )

plugintools.add_item(
		title = "[B][COLOR red]GMBN[/B][/COLOR]",
		url = "plugin://plugin.video.youtube/"+YOUTUBE_CHANNEL_ID4+"/",
		thumbnail = icon5,
		folder = True )

plugintools.add_item(
		title = "[B][COLOR red]WRC[/B][/COLOR]",
		url = "plugin://plugin.video.youtube/"+YOUTUBE_CHANNEL_ID5+"/",
		thumbnail = icon6,
		folder = True )

plugintools.add_item(
		title = "[B][COLOR red]MONSTER JAM[/B][/COLOR]",
		url = "plugin://plugin.video.youtube/"+YOUTUBE_CHANNEL_ID6+"/",
		thumbnail = icon7,
		folder = True )

plugintools.add_item(
		title = "[B][COLOR red]RED BULL[/B][/COLOR]",
		url = "plugin://plugin.video.youtube/"+YOUTUBE_CHANNEL_ID7+"/",
		thumbnail = icon8,
		folder = True )		

plugintools.add_item(
		title = "[B][COLOR red]THE HOONIGAN[/B][/COLOR]",
		url = "plugin://plugin.video.youtube/"+YOUTUBE_CHANNEL_ID8+"/",
		thumbnail = icon9,
		folder = True )

plugintools.add_item(
		title = "[B][COLOR red]FORD RACING[/B][/COLOR]",
		url = "plugin://plugin.video.youtube/"+YOUTUBE_CHANNEL_ID9+"/",
		thumbnail = icon10,
		folder = True )

plugintools.add_item(
		title = "[B][COLOR red]FORMULA DRIFT[/B][/COLOR]",
		url = "plugin://plugin.video.youtube/"+YOUTUBE_CHANNEL_ID10+"/",
		thumbnail = icon11,
		folder = True )

plugintools.add_item(
		title = "[B][COLOR red]IMSA[/B][/COLOR]",
		url = "plugin://plugin.video.youtube/"+YOUTUBE_CHANNEL_ID11+"/",
		thumbnail = icon12,
		folder = True )		

plugintools.add_item(
		title = "[B][COLOR red]FREESTYLE MOTOCROSS[/B][/COLOR]",
		url = "plugin://plugin.video.youtube/"+YOUTUBE_CHANNEL_ID12+"/",
		thumbnail = icon13,
		folder = True )				

plugintools.add_item(
		title = "[B][COLOR red]ICE RACING[/B][/COLOR]",
		url = "plugin://plugin.video.youtube/"+YOUTUBE_CHANNEL_ID13+"/",
		thumbnail = icon14,
		folder = True )				

plugintools.add_item(
		title = "[B][COLOR red]SNOCROSS[/B][/COLOR]",
		url = "plugin://plugin.video.youtube/"+YOUTUBE_CHANNEL_ID14+"/",
		thumbnail = icon15,
		folder = True )				
		
plugintools.add_item(
		title = "[B][COLOR red]RED BULL AIR RACE[/B][/COLOR]",
		url = "plugin://plugin.video.youtube/"+YOUTUBE_CHANNEL_ID15+"/",
		thumbnail = icon16,
		folder = True )		
plugintools.add_item(
		title = "[B][COLOR red]MONSTER SUPERCROSS[/B][/COLOR]",
		url = "plugin://plugin.video.youtube/"+YOUTUBE_CHANNEL_ID16+"/",
		thumbnail = icon17,
		folder = True )	

plugintools.add_item(
		title = "[B][COLOR red]EXTREME SPORTS[/B][/COLOR]",
		url = "plugin://plugin.video.youtube/"+YOUTUBE_CHANNEL_ID17+"/",
		thumbnail = icon18,
		folder = True )	
		
plugintools.add_item(
		title = "[B][COLOR red]WORLD SURF LEAGUE[/B][/COLOR]",
		url = "plugin://plugin.video.youtube/"+YOUTUBE_CHANNEL_ID18+"/",
		thumbnail = icon19,
		folder = True )	

plugintools.add_item(
		title = "[B][COLOR red]GOPRO RACING[/B][/COLOR]",
		url = "plugin://plugin.video.youtube/"+YOUTUBE_CHANNEL_ID19+"/",
		thumbnail = icon20,
		folder = True )			
		
run()