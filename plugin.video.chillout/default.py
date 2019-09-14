# -*- coding: utf-8 -*-

import os
import sys
import plugintools
import xbmc,xbmcaddon
from addon.common.addon import Addon

addonID = 'plugin.video.chillout'
addon = Addon(addonID, sys.argv)
local = xbmcaddon.Addon(id=addonID)
icon = local.getAddonInfo('icon')


channellist=[
        ("Hot Vibes", "channel/UCUknBTWMDCzSggZ_-AgQAbA", 'https://yt3.ggpht.com/-R2czMs7RTjI/AAAAAAAAAAI/AAAAAAAAAAA/pEBw2tl8JvI/s288-mo-c-c0xffffffff-rj-k-no/photo.jpg'),
		("KIU - Chillout Lounge + 24/7 Live", "channel/UCra_HTaSgvbMZ7eLaFmr-Hw", 'https://yt3.ggpht.com/-7zhEuT2HVMA/AAAAAAAAAAI/AAAAAAAAAAA/Iuht3JyjZ2o/s288-mo-c-c0xffffffff-rj-k-no/photo.jpg'),
		("Café del Mar", "channel/UCha0QKR45iw7FCUQ3-1PnhQ", 'https://yt3.ggpht.com/-YJVGM_ODglA/AAAAAAAAAAI/AAAAAAAAAAA/vmkJoQGaXsw/s288-mo-c-c0xffffffff-rj-k-no/photo.jpg'),
		("Relax Chillout Music + 24/7 Live", "channel/UCUjD5RFkzbwfivClshUqqpg", 'https://yt3.ggpht.com/-pAS7CiDEj8w/AAAAAAAAAAI/AAAAAAAAAAA/DSbbuAUZ3AE/s288-mo-c-c0xffffffff-rj-k-no/photo.jpg'),
		("Palma Chillout", "channel/UCRdASafxDuxoRFbHtQL_xfg", 'https://yt3.ggpht.com/-Aohc1Irapa0/AAAAAAAAAAI/AAAAAAAAAAA/binrGiFFx5E/s288-mo-c-c0xffffffff-rj-k-no/photo.jpg'),
		("Chill Out & Lounge Music", "channel/UCKfIfdK0sVAT80qlDwUjo3g", 'https://yt3.ggpht.com/-kEBCTiJETf8/AAAAAAAAAAI/AAAAAAAAAAA/lYYPhPP0e6U/s288-mo-c-c0xffffffff-rj-k-no/photo.jpg'),
		("Buddha's Lounge", "channel/UCWaZJ2Mu5zjfhZoEEMxs1MQ", 'https://yt3.ggpht.com/-gOgHNea7N1s/AAAAAAAAAAI/AAAAAAAAAAA/SOeNkpU6pb8/s288-mo-c-c0xffffffff-rj-k-no/photo.jpg'),
		("Chill Out Crew Official", "channel/UCnVSluwgK33SNTm1nprXSpg", 'https://yt3.ggpht.com/-bBXFmpqLOeE/AAAAAAAAAAI/AAAAAAAAAAA/YHn5CB5zNQ8/s288-mo-c-c0xffffffff-rj-k-no/photo.jpg'),
		("ChillYourMind", "channel/UCmDM6zuSTROOnZnjlt2RJGQ", 'https://yt3.ggpht.com/-lTxy_E5pSKs/AAAAAAAAAAI/AAAAAAAAAAA/AgX7HURLT_I/s288-mo-c-c0xffffffff-rj-k-no/photo.jpg'),
		("Pulse Musification + 24/7 Live", "channel/UCWBd2mNhpgVgYShpM2EyvIQ", 'https://yt3.ggpht.com/-OJ6LMm0FIPk/AAAAAAAAAAI/AAAAAAAAAAA/dw61QOyY8RA/s288-mo-c-c0xffffffff-rj-k-no/photo.jpg'),
		("Monstafluff Music + 24/7 Live", "channel/UCMwePVHRpDdfeUcwtDZu2Dw", 'https://yt3.ggpht.com/-HxZ4xLU0sKY/AAAAAAAAAAI/AAAAAAAAAAA/vEmq4qjIUZQ/s288-mo-c-c0xffffffff-rj-k-no/photo.jpg'),
		("Magic Music", "channel/UCp6_KuNhT0kcFk-jXw9Tivg", 'https://yt3.ggpht.com/-xs0NMTqE5TM/AAAAAAAAAAI/AAAAAAAAAAA/VQCWBWkMwh4/s288-mo-c-c0xffffffff-rj-k-no/photo.jpg'),
		("Magic Club", "channel/UCAJ1rjf90IFwNGlZUYuoP1Q", 'https://yt3.ggpht.com/-_xhAnsMSmI8/AAAAAAAAAAI/AAAAAAAAAAA/ywks2OWZ0EM/s288-mo-c-c0xffffffff-rj-k-no/photo.jpg'),
		("Dj Regard Official", "channel/UCw39ZmFGboKvrHv4n6LviCA", 'https://yt3.ggpht.com/-Z6Mnb8qdA7A/AAAAAAAAAAI/AAAAAAAAAAA/CeU6rdpFLHI/s288-mo-c-c0xffffffff-rj-k-no/photo.jpg'),
		("InYourChill + 24/7 Live", "channel/UCncxHd8o_VhhHAJ7QqB5azg", 'https://yt3.ggpht.com/-4ZgDYs1RKdM/AAAAAAAAAAI/AAAAAAAAAAA/zOvYcGXAlIU/s288-mo-c-c0xffffffff-rj-k-no/photo.jpg'),
		("Only Chillout", "channel/UCbO8uatNX74RYU-z2SeWbrQ", 'https://yt3.ggpht.com/-FHmSHMGuibU/AAAAAAAAAAI/AAAAAAAAAAA/kIzy2HYxPhA/s288-mo-c-c0xffffffff-rj-k-no/photo.jpg'),
		("Shine Music - Deep House", "channel/UCopVo3rXZJkkohbf9218bDw", 'https://yt3.ggpht.com/-vG75cAa_y8Q/AAAAAAAAAAI/AAAAAAAAAAA/jFhsp58rXOM/s288-mo-c-c0xffffffff-rj-k-no/photo.jpg'),
		("The Chillout Channel", "channel/UC05WU97xWYuWXJVYXmT53Mw", 'https://yt3.ggpht.com/-GliWVz4awPg/AAAAAAAAAAI/AAAAAAAAAAA/1PsmZsCoySM/s288-mo-c-c0xffffffff-rj-k-no/photo.jpg'),
		("Cafe Music BGM Channel + 24/7 Live", "channel/UCJhjE7wbdYAae1G25m0tHAA", 'https://yt3.ggpht.com/-J7GRtoYtWXk/AAAAAAAAAAI/AAAAAAAAAAA/487XVrL-Z8s/s288-mo-c-c0xffffffff-rj-k-no/photo.jpg'),
		("Relax Music Jazz + 24/7 Live", "channel/UC7bX_RrH3zbdp5V4j5umGgw", 'https://yt3.ggpht.com/-gkM8RPr4rqw/AAAAAAAAAAI/AAAAAAAAAAA/kleRSBhfBUg/s288-mo-c-c0xffffffff-rj-k-no/photo.jpg'),
		("Lounge Music + 24/7 Live", "channel/UCKHsXi0fY-mvLAAnLq95PPQ", 'https://yt3.ggpht.com/-muFvPaknNxI/AAAAAAAAAAI/AAAAAAAAAAA/osuW8bO2Jpc/s288-mo-c-c0xffffffff-rj-k-no/photo.jpg'),
		("Baby's Music", "channel/UCtBBEQw4SFYOcrZKzY7quCQ", 'https://yt3.ggpht.com/-jEwdgglCvMQ/AAAAAAAAAAI/AAAAAAAAAAA/sqhySdbiGzw/s288-mo-c-c0xffffffff-rj-k-no/photo.jpg'),
		("OCB Relax Music", "channel/UCb1ANUIW7arUUDI-Mwz65rw", 'https://yt3.ggpht.com/-9tc1pIq51Ck/AAAAAAAAAAI/AAAAAAAAAAA/3fS6JlPqtxw/s288-mo-c-c0xffffffff-rj-k-no/photo.jpg'),
		("Lucid Dreams - Relaxing Music Therapy", "channel/UCgXtl1crD81AA1ougkTlong", 'https://yt3.ggpht.com/-bzW0L4SlX_8/AAAAAAAAAAI/AAAAAAAAAAA/OV1tPZfgPCM/s288-mo-c-c0xffffffff-rj-k-no/photo.jpg'),
		("Soothing Relaxation + 24/7 Live", "channel/UCjzHeG1KWoonmf9d5KBvSiw", 'https://yt3.ggpht.com/-vq0QH82gHCE/AAAAAAAAAAI/AAAAAAAAAAA/vPmQ10nrrUc/s288-mo-c-c0xffffffff-rj-k-no/photo.jpg'),
		("Beste Musik für Meditation + 24/7 Live", "channel/UCb_kshGodseYhLPcDtxWv5w", 'https://yt3.ggpht.com/-c1LV6kl8nls/AAAAAAAAAAI/AAAAAAAAAAA/GIR8nHEOO-k/s288-mo-c-c0xffffffff-rj-k-no/photo.jpg'),
]



# Entry point
def run():
    plugintools.log("youtubeAddon.run")
    
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
    plugintools.log("youtubeAddon.main_list "+repr(params))

for name, id, icon in channellist:
	plugintools.add_item(title=name,url="plugin://plugin.video.youtube/"+id+"/",thumbnail=icon,folder=True )



run()