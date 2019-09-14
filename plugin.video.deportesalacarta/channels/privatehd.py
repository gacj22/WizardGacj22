# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
# Canal para PrivateHD
#------------------------------------------------------------
import urllib
from core import httptools
from core import logger
from core import scrapertools
from core import servertools
from core.item import Item

__channel__ = "privatehd"


def mainlist(item):
    logger.info()
    itemlist = []

    paises = [["Inglaterra/USA", "uk"], ["Polonia", "pol"], ["Holanda/Alemania", "nl"], ["Francia/Portugal", "fr"], ["Rumanía/Italia", "de"], ["España/México", "es"],  ["Resto del mundo", "rm"]]
    data = httptools.downloadpage("http://freelive365.com/live.php").data

    patron = '<li><input type="button".*?Enviar\(\'([^\']+)\''
    matches = scrapertools.find_multiple_matches(data, patron)
    for i, url in enumerate(matches):
        scrapedtitle = "[COLOR green]"+paises[i][0]+"[/COLOR]"
        scrapedthumbnail = "http://freelive365.com/img/%s.png" % paises[i][1]
        url = "http://freelive365.com/%s" % url
        if "/es.png" in scrapedthumbnail:
            itemlist.insert(0, item.clone(title=scrapedtitle, action="canales", url=url, thumbnail=scrapedthumbnail))
        else:
            itemlist.append(item.clone(title=scrapedtitle, action="canales", url=url, thumbnail=scrapedthumbnail))

    return itemlist


def canales(item):
    logger.info()
    itemlist = []
    
    data = httptools.downloadpage(item.url).data
    patron = '<li><a href=\'([^\']+)\'.*?<td.*?>([^<]+)</td>.*?src="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle, scrapedthumbnail  in matches:
        scrapedtitle = unicode(scrapedtitle, "utf-8").upper().encode("utf-8")
        scrapedurl = "http://freelive365.com/%s" % scrapedurl.rsplit("&name", 1)[0]
        scrapedthumbnail = "http://freelive365.com/%s" % urllib.quote(scrapedthumbnail)
        itemlist.append(item.clone(title=scrapedtitle, action="play", url=scrapedurl, thumbnail=scrapedthumbnail))
    
    return itemlist


def play(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    urls = servertools.findvideosbyserver(data, "p2p")
    if urls:
        url = urls[0][1] + "|" + item.title
        itemlist.append(Item(channel=__channel__, title=item.title, server="p2p", url=url, action="play"))
    else:
        headers = {"Referer": iframe}
        newurl = scrapertools.find_single_match(data, "src='(http://freelive365.com/server[^']+)'")
        newurl = newurl.replace("channel.php?file=", "embed.php?a=") + "&strech="
        data = httptools.downloadpage(newurl, headers=headers).data

        url_video = scrapertools.find_single_match(data, "'streamer'\s*,\s*'([^']+)'")
        if "rtmp" in url_video:
            file = scrapertools.find_single_match(data, "'file'\s*,\s*'([^']+)'")
            url_video += " playpath=%s swfUrl=http://freelive365.com/player.swf live=true swfVfy=1 pageUrl=%s token=0fea41113b03061a" % (file, newurl)

        itemlist.append(Item(channel=__channel__, title=item.title, server="directo", url=url_video, action="play"))
    
    return itemlist
