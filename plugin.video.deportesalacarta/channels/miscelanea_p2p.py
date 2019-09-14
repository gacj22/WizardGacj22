# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
# Canal para Miscelánea
#------------------------------------------------------------

import os, re, xbmc, urllib

from core import scrapertools
from core import jsontools
from core import logger
from core import config
from core import httptools
from core import servertools
from core.item import Item

__channel__ = "miscelanea_p2p"

song = os.path.join(config.get_runtime_path(), 'music', 'Survivor - eye of the tiger.mp3')


def mainlist(item):
    logger.info("deportesalacarta.channels.miscelanea_p2p mainlist")
    itemlist = []
    
    xbmc.executebuiltin('xbmc.PlayMedia('+song+')')

    itemlist.append(Item(channel=__channel__, title="[COLOR teal]Enlaces sin canal asociado[/COLOR]", action="canales", url="", thumbnail="http://s6.postimg.org/etyqbs3o1/miscelania.png",fanart="http://i.imgur.com/Bt9PHVR.jpg?1", folder=True))
    itemlist.append(Item(channel=__channel__, title="[COLOR gold]Especial Eurocopa 2016[/COLOR]", action="euro", url="", thumbnail="http://www.uefa.com/img/apps/Articles/Infographics/100DTGMOSAIC.jpg",fanart="http://i.imgur.com/Bt9PHVR.jpg?1", folder=True))
    itemlist.append(Item(channel=__channel__, title="", action="", thumbnail="http://s6.postimg.org/etyqbs3o1/miscelania.png", fanart="http://i.imgur.com/Bt9PHVR.jpg?1", folder=False))
    itemlist.append(Item(channel=__channel__, title="[COLOR indianred]Configuración Ventana \"Info del partido\"[/COLOR]", action="config", thumbnail="http://s6.postimg.org/etyqbs3o1/miscelania.png",fanart="http://i.imgur.com/Bt9PHVR.jpg?1", folder=False))
    itemlist.append(Item(channel=__channel__, title="", action="", thumbnail="http://s6.postimg.org/etyqbs3o1/miscelania.png", fanart="http://i.imgur.com/Bt9PHVR.jpg?1", folder=False))
    itemlist.append(Item(channel=__channel__, title="[COLOR darkgreen]Reproducir enlace Acestream[/COLOR]", action="p2p", thumbnail="http://i.imgur.com/0kq0Jx6.png",fanart="http://i.imgur.com/Bt9PHVR.jpg?1", folder=False))
    itemlist.append(Item(channel=__channel__, title="[COLOR seagreen]Reproducir enlace Sopcast[/COLOR]", action="p2p", thumbnail="http://i.imgur.com/0kq0Jx6.png",fanart="http://i.imgur.com/Bt9PHVR.jpg?1", folder=False))

    return itemlist


def config(item):
    from platformcode import platformtools
    from core import channeltools
    dialog = platformtools.dialog_yesno("Configuración Info Partido", "       Selecciona el modo de inicio", yeslabel="Ventana", nolabel="Pantalla Completa")
    if dialog == 1:
        channeltools.set_channel_setting("modo", False, "futbol_window")
    elif dialog == 0:
        channeltools.set_channel_setting("modo", True, "futbol_window")
    
    
def p2p(item):
    if "Sopcast" in item.title:
        texto = dialog_input(default='sop://broker.sopcast.com:3912/', heading="Introduce la url de sopcast")
        titulo = "[Sopcast]"
    else:
        texto = dialog_input(default='acestream://', heading="Introduce la url de acestream")
        titulo = "[Acestream]"
    if texto != "":
        url = texto + "|" + titulo
        from platformcode import platformtools
        item_play = item.clone()
        item_play.url = url
        item_play.server = "p2p"
        platformtools.play_video(item_play)


def canales(item):
    logger.info("deportesalacarta.channels.miscelanea_p2p canales")
    itemlist = []

    itemlist.append(Item(channel=__channel__, title="[COLOR teal]PremierTv Acestream 1[/COLOR]", action="play", url="http://premiertv.top/a1/ifi.html", thumbnail="http://i.imgur.com/o7sosoD.png",fanart="http://i.imgur.com/FtrAOlU.jpg", folder=False))
    itemlist.append(Item(channel=__channel__, title="[COLOR teal]PremierTv Acestream 2[/COLOR]", action="play", url="http://premiertv.top/a2/ifi.html", thumbnail="http://i.imgur.com/o7sosoD.png",fanart="http://i.imgur.com/FtrAOlU.jpg", folder=False))
    itemlist.append(Item(channel=__channel__, title="[COLOR teal]PremierTv Sopcast 1[/COLOR]", action="play", url="http://premiertv.top/z1/ifi.html", thumbnail="http://i.imgur.com/o7sosoD.png",fanart="http://i.imgur.com/FtrAOlU.jpg", folder=False))
    itemlist.append(Item(channel=__channel__, title="[COLOR teal]PremierTv Sopcast 2[/COLOR]", action="play", url="http://premiertv.top/z2/ifi.html", thumbnail="http://i.imgur.com/o7sosoD.png",fanart="http://i.imgur.com/FtrAOlU.jpg", folder=False))
    itemlist.append(Item(channel=__channel__, title="[COLOR teal]DHD1[/COLOR]", action="dhd1", url="http://deporteshd1.blogspot.com.es/", thumbnail="http://i.imgur.com/K7SiYi5.jpg?1",fanart="http://i.imgur.com/Ww2Dahm.jpg?1", folder=True))

    return itemlist


def dhd1(item):
    logger.info("deportesalacarta.channels.miscelanea_p2p dhd1")
    itemlist = []
        
    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data, "ACE 24/7</a>(.*?)<a href='#'>Flash")
    matches = scrapertools.find_multiple_matches(bloque, "<a href='(http://[^']+)'.*?>(.*?)</a>")
    for scrapedurl, scrapedtitle in matches:
        scrapedtitle = "[COLOR crimson]"+scrapedtitle+"[/COLOR]"
        scrapedtitle = re.sub('\|(.*?)\|', r'[\1]', scrapedtitle)
        itemlist.append(item.clone(url=scrapedurl, action="play", title=scrapedtitle, extra="dhd1", folder=False))
 
    bloque = scrapertools.find_single_match(data, "<a href='#'>Flash(.*?)<a href='#'>DHD1")
    matches = scrapertools.find_multiple_matches(bloque, "<a href='(http://[^']+)'.*?>(.*?)</a>")
    url_prefix = ['cp','cp','cp','cp','cp','','','cp','','','','']
    url_sufix = ['liga','liga2','futbol','depor','depor2','movisf1','movismgp','toros','skyf1','beinesp','eurospt','movis0']
    for i, match in enumerate(matches):
        scrapedtitle = "[COLOR crimson]"+match[1]+"[/COLOR]  [COLOR darkcyan][Flash][/COLOR]"
        scrapedurl = "http://dhd1.ml/dhd1%s%s.php" % (url_prefix[i], url_sufix[i])
        itemlist.append(item.clone(url=scrapedurl, action="play_flash", title=scrapedtitle, folder=False))
    return itemlist


def euro(item):
    logger.info("deportesalacarta.channels.miscelanea_p2p play")
    itemlist = []
    
    data = httptools.downloadpage("http://pastebin.com/raw/P0aice5g").data
    data = jsontools.load_json(data)
    for match in data['euro']['encuentros']:
        scrapedtitle = "[COLOR darkorange]"+match['partido']+"[/COLOR][COLOR indianred]"+match['fecha']+"[/COLOR]"
        scrapedurl = match['url']
        itemlist.append(item.clone(title=scrapedtitle, action="play", url=scrapedurl, extra="euro"))

    return itemlist


def play(item):
    logger.info("deportesalacarta.channels.miscelanea_p2p play")
    itemlist = []
    xbmc.executebuiltin('xbmc.PlayMedia(Stop)')
    data = httptools.downloadpage(item.url).data

    # Si el canal está en la web se busca manualmente el enlace ya que puede haber varios
    if item.extra == "dhd1":
        url = scrapertools.find_single_match(data, 'href="(acestream://[^"]+)"')
        if url == "":
            redirect = scrapertools.find_single_match(data, 'src="(http://buker[^"]+)"')
            data = httptools.downloadpage(redirect).data
            urls = servertools.findvideosbyserver(data, "p2p")
            if urls:
                url = urls[0][1] +"|" + item.title
                itemlist.append(item.clone(url=url, server="p2p"))
        else:
            url += "|" + item.title
            itemlist.append(item.clone(url=url, server="p2p"))
    elif item.extra == "euro":
        itemlist.append(item.clone(server="directo"))
    else:
        # Se automatiza la búsqueda del enlace acestream/sopcast a través del conector p2p
        urls = servertools.findvideosbyserver(data, "p2p")
        if urls:
            url = urls[0][1]+"|" + item.title
            itemlist.append(item.clone(url=url, server="p2p"))
        
    return itemlist


def play_flash(item):
    logger.info("deportesalacarta.channels.miscelanea_p2p play_flash")
    xbmc.executebuiltin('xbmc.PlayMedia(Stop)')
    data = httptools.downloadpage(item.url).data

    url = scrapertools.find_single_match(data, 'src="(http://www.sunhd[^"]+)"')
    if url == "":
        url = scrapertools.find_single_match(data, 'src="(http://verdirecto[^"]+)"')

    url_dev = "catcher=%s&url=%s&referer=%s" % ("streams", url, item.url)
    xbmc.executebuiltin("XBMC.RunPlugin(plugin://plugin.video.SportsDevil/?item=%s&mode=1)" % urllib.quote_plus(url_dev))


def dialog_input(default="", heading="", hidden=False):
    keyboard = xbmc.Keyboard(default, heading, hidden)
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        return keyboard.getText()
    else:
        return ""
