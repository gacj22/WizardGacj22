# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
# Canal para SoccerYou
#------------------------------------------------------------
from core import logger
from core import config
from core import scrapertools
from core import servertools
from core.item import Item
from core import httptools

__channel__ = "socceryou"
host_soccer = "http://www.socceryou.com/es/"


def mainlist(item):
    logger.info("deportesalacarta.channels.socceryou mainlist")
    itemlist = []

    itemlist.append(Item(channel=__channel__, title="Últimos partidos", url="http://www.socceryou.com/es/partidos-completos.php", action="novedades", thumbnail=item.thumbnail, fanart=item.fanart))
    itemlist.append(Item(channel=__channel__, title="Últimos resúmenes", url="http://www.socceryou.com/es/resumenes.php", action="novedades", thumbnail=item.thumbnail, fanart=item.fanart))
    itemlist.append(Item(channel=__channel__, title="Programas", url="http://www.socceryou.com/es/programastv.php", action="novedades", thumbnail=item.thumbnail, fanart=item.fanart))
    itemlist.append(Item(channel=__channel__, title="Competiciones", url="http://www.socceryou.com/es/partidos-completos.php", action="competiciones", thumbnail=item.thumbnail, fanart=item.fanart))

    return itemlist

def novedades(item):
    logger.info("deportesalacarta.channels.socceryou novedades")
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = data.replace("\n","").replace("\t","")
    logger.info(data)

    patron = '<div class="foto-video">.*?title="([^"]+)".*?href="([^"]+)"' \
             '.*?src\s*=["\']([^"\']+)["\']'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedtitle, scrapedurl, scrapedthumbnail in matches:
        title = scrapertools.entitiesfix(scrapedtitle).replace("&nbsp"," ")
        scrapedtitle = "[COLOR indianred]"+title.rsplit(' ',1)[0]+"[/COLOR]"
        scrapedtitle += " [COLOR darkorange]("+title.rsplit(' ',1)[1]+")[/COLOR]"
        if "no-thumbnail.jpg" in scrapedthumbnail: scrapedthumbnail = item.thumbnail
        elif scrapedthumbnail.startswith("//"): scrapedthumbnail = "http:"+scrapedthumbnail
        elif not scrapedthumbnail.startswith("http"): scrapedthumbnail = "http://www.socceryou.com"+scrapedthumbnail
        if not scrapedurl.startswith("http"):
            scrapedurl = host_soccer + scrapedurl
        itemlist.append(Item(channel=__channel__, title=scrapedtitle, action="findvideos", url=scrapedurl, thumbnail=scrapedthumbnail, folder=True))

    next_page = scrapertools.find_single_match(data, '<a href="([^"]+)">Siguiente</a>')
    if next_page != "":
        itemlist.append(Item(channel=__channel__, title=">> Siguiente", action="novedades", url=item.url+next_page, thumbnail=item.thumbnail, folder=True))

    return itemlist

def competiciones(item):
    logger.info("deportesalacarta.channels.socceryou competiciones")
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = data.replace("\n","").replace("\t","")

    bloque = scrapertools.find_single_match(data, '<ul class="nav-sub2">(.*?)</ul>')
    matches = scrapertools.find_multiple_matches(bloque, 'href="([^"]+)".*?src=\'([^\']+)\'></span>(.*?)</li>')
    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        if not scrapedurl.startswith("http"):
            scrapedurl = host_soccer + scrapedurl
        if not scrapedthumbnail.startswith("http"):
            scrapedthumbnail = "http://www.socceryou.com" + scrapedthumbnail
        itemlist.append(Item(channel=__channel__, title=scrapedtitle, action="menu", url=scrapedurl, thumbnail=scrapedthumbnail, folder=True))

    itemlist.append(Item(channel=__channel__, title="Todas las Competiciones", action="menu", url="http://www.socceryou.com/es/competiciones.php", thumbnail=item.thumbnail, folder=True))

    return itemlist

def menu(item):
    logger.info("deportesalacarta.channels.socceryou menu")
    itemlist = []
    if item.title == "Todas las Competiciones":
        data = httptools.downloadpage(item.url).data
        data = data.replace("\n","").replace("\t","")
        bloque = scrapertools.find_single_match(data, '<ul class="todos-equipos">(.*?)</ul>')
        matches = scrapertools.find_multiple_matches(bloque, 'src ="([^"]+)".*?<a href ="([^"]+)">(.*?)</a>')
        for scrapedthumbnail, scrapedurl, scrapedtitle in matches:
            scrapedthumbnail = "http://www.socceryou.com"+scrapedthumbnail
            itemlist.append(Item(channel=__channel__, title=scrapedtitle, action="menu", url=host_soccer+scrapedurl, thumbnail=scrapedthumbnail, folder=True))
    else:
        scrapedurl = item.url.replace("proximos-encuentros","partidos-completos")
        itemlist.append(Item(channel=__channel__, title="Partidos Completos", action="novedades", url=scrapedurl, thumbnail=item.thumbnail, folder=True))
        scrapedurl = item.url.replace("proximos-encuentros","resumenes")
        itemlist.append(Item(channel=__channel__, title="Resúmenes", action="novedades", url=scrapedurl, thumbnail=item.thumbnail, folder=True))

    return itemlist


def findvideos(item):
    logger.info("deportesalacarta.channels.socceryou findvideos")
    itemlist = []
    data = httptools.downloadpage(item.url).data

    videos = scrapertools.find_single_match(data, "<div class='video_button'>(.*?)</div>")
    matches = scrapertools.find_multiple_matches(videos, "href='([^']+)'>([^<]+)</a>")
    i = 0
    for scrapedurl, scrapedtitle in matches:
        if not scrapedurl.startswith("http"):
            scrapedurl = host_soccer + scrapedurl
        scrapedtitle = scrapedtitle.strip()
        if i > 0:
            data = httptools.downloadpage(scrapedurl).data
        videos_list = servertools.findvideos(data)
        if not videos_list:
            continue
        videos_list = videos_list[0]
        scrapedtitle += " [%s]" % videos_list[2]
        itemlist.append(item.clone(title=scrapedtitle, action="play", url=videos_list[1], server=videos_list[2]))
    
    return itemlist
