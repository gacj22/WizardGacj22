# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
# Canal para MPlus A la Carta
#------------------------------------------------------------

import base64

from core import httptools
from core import logger
from core import config
from core import scrapertools
from core.item import Item

__channel__ = "mpluscarta"
host = "aHR0cDovL3d3dy5tb3Zpc3RhcnBsdXMuZXM="


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=__channel__, title="NBA" , action="indice", url="nba", thumbnail=item.thumbnail, fanart=item.fanart))
    itemlist.append(Item(channel=__channel__, title="Fórmula 1" , action="findvideos", url="formula1/videos", thumbnail=item.thumbnail, fanart=item.fanart))
    itemlist.append(Item(channel=__channel__, title="MotoGP" , action="findvideos", url="motogp/videos", thumbnail=item.thumbnail, fanart=item.fanart))
    itemlist.append(Item(channel=__channel__, title="Fútbol (EDF)" , action="findvideos", url="casadelfutbol/programas/edf", thumbnail=item.thumbnail, fanart=item.fanart))
    itemlist.append(Item(channel=__channel__, title="Liga ACB" , action="indice", url="ligaendesa", thumbnail=item.thumbnail, fanart=item.fanart))
    itemlist.append(Item(channel=__channel__, title="Tenis" , action="indice", url="tenis/videos", thumbnail=item.thumbnail, fanart=item.fanart))
    itemlist.append(Item(channel=__channel__, title="Tenis (Programa Tie Break)" , action="indice", url="tenis/tiebreak", thumbnail=item.thumbnail, fanart=item.fanart))
    itemlist.append(Item(channel=__channel__, title="NFL" , action="findvideos", url="nfl/videos", thumbnail=item.thumbnail, fanart=item.fanart))
    itemlist.append(Item(channel=__channel__, title="Rugby" , action="findvideos", url="rugby/videos", thumbnail=item.thumbnail, fanart=item.fanart))
    itemlist.append(Item(channel=__channel__, title="Golf" , action="indice", url="golf", thumbnail=item.thumbnail, fanart=item.fanart))
    itemlist.append(Item(channel=__channel__, title="Liga Asobal" , action="findvideos", url="balonmano/videos", thumbnail=item.thumbnail, fanart=item.fanart))
    itemlist.append(Item(channel=__channel__, title="eSports" , action="findvideos", url="esports", thumbnail=item.thumbnail, fanart=item.fanart))

    return itemlist


def indice(item):
    logger.info()
    itemlist = []
    if item.url == "nba":
        itemlist.append(item.clone(title="Temporada", action="findvideos", url="%s/videos/temporada" % item.url))
        itemlist.append(item.clone(title="Generacion NBA+", action="findvideos", url="%s/videos/generacionnba+" % item.url))
        itemlist.append(item.clone(title="The Very Best", action="findvideos", url="%s/videos/theverybest" % item.url))
        itemlist.append(item.clone(title="Estilo NBA+", action="findvideos", url="%s/videos/estilonba+" % item.url))
        itemlist.append(item.clone(title="NCAA", action="findvideos", url="%s/ncaa" % item.url))
    elif item.url == "ligaendesa":
        itemlist.append(item.clone(title="Temporada", action="findvideos", url="%s/videos/temporada" % item.url))
        itemlist.append(item.clone(title="Copa del Rey", action="findvideos", url="%s/videos/copaacb" % item.url))
        itemlist.append(item.clone(title="Clubbers", action="findvideos", url="%s/videos/clubbers" % item.url))
    elif item.url == "golf":
        itemlist.append(item.clone(title="Casa Club", action="findvideos", url="%s/programas/casaclub" % item.url))
        itemlist.append(item.clone(title="Locos por el golf", action="findvideos", url="%s/programas/locosporelgolf" % item.url))
        itemlist.append(item.clone(title="Play Off", action="findvideos", url="%s/programas/playoff" % item.url))
        itemlist.append(item.clone(title="Ruta 21", action="findvideos", url="%s/programas/ruta21" % item.url))
        itemlist.append(item.clone(title="Golf Saludable", action="findvideos", url="%s/programas/golfsaludable" % item.url))
        itemlist.append(item.clone(title="Golf Academy", action="findvideos", url="%s/programas/golfacademy" % item.url))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    url = "%s/%s" % (base64.b64decode(host), item.url)
    data = httptools.downloadpage(url).data

    if '<div class="horizonal-slide' in data:
        patron = '<div class="slide">.*?href="([^"]+)".*?src="([^"]+)" alt="(.*?)"(?:>| title)'
    else:
        patron = '<div class="gi lap.*?href="([^"]+)".*?src="([^"]+)" alt="(.*?)"(?:>| title)'
    matches = scrapertools.find_multiple_matches(data, patron)
    for url, img, title in matches:
        img = img.replace("fotograma295", "poster").replace("fotograma391", "poster")
        itemlist.append(item.clone(title=title, url=url, action="play", thumbnail=img))

    next_page = scrapertools.find_single_match(data, 'href="([^"]+)" class="button-link">Siguiente')
    if next_page:
        next_page = item.url + next_page
        itemlist.append(item.clone(title=">> Página Siguiente", url=next_page))

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data.replace("\\", "")
    urls = scrapertools.find_multiple_matches(data, '<source src="([^"]+)"')
    for url in urls:
        ext = url.rsplit(".", 1)[1]
        title = ".%s [directo]" % ext
        itemlist.append([title, url])

    return itemlist
