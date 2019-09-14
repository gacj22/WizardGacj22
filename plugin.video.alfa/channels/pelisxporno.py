# -*- coding: utf-8 -*-
import urlparse
import re

from platformcode import config, logger
from core import httptools
from core import scrapertools
from core import servertools


host = 'http://www.pelisxporno.com'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(action="lista", title="Novedades", url= host + "/?order=date"))
    itemlist.append(item.clone(action="categorias", title="Categorías", url=host + "/categorias/"))
    itemlist.append(item.clone(action="search", title="Buscar"))
    return itemlist

def search(item, texto):
    logger.info("")
    texto = texto.replace(" ", "+")
    item.url = host + "/?s=%s" % texto
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
        
def search(item, texto):
    logger.info()
    item.url = item.url % texto
    return lista(item)


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<li class="cat-item cat-item-.*?"><a href="(.*?)".*?>(.*?)<'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle in matches:
        itemlist.append(item.clone(action="lista", title=scrapedtitle, url=scrapedurl))
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<div class="video.".*?<a href="(.*?)" title="(.*?)">.*?<img src="(.*?)".*?\/>.*?duration.*?>(.*?)<'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle, scrapedthumbnail, duration in matches:
        if duration:
            scrapedtitle = "[COLOR yellow]" + duration + "[/COLOR] " + scrapedtitle
        itemlist.append(item.clone(action="findvideos", title=scrapedtitle, url=scrapedurl, thumbnail=scrapedthumbnail,
                                   fanart=scrapedthumbnail))
    next_page = scrapertools.find_single_match(data, '<a class="nextpostslink" rel="next" href="([^"]+)"')
    if next_page:
        itemlist.append(item.clone(action="lista", title=">> Página Siguiente", url=next_page))
    return itemlist


def findvideos(item):
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data, '<div class="video_code">(.*?)<h3')
    patron = '(?:src|SRC)="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl in matches:
        if not 'mixdrop' in scrapedurl:  #el base64 es netu.tv
            url = "https://hqq.tv/player/embed_player.php?vid=RODE5Z2Hx3hO&autoplay=none"
        else:
            url = "https:" + scrapedurl
            headers = {'Referer': item.url}
            data = httptools.downloadpage(url, headers=headers).data
            url = scrapertools.find_single_match(data, 'vsrc = "([^"]+)"')
            url= "https:" + url
        itemlist.append(item.clone(action="play", title = "%s", url=url ))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist

