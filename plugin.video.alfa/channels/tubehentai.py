# -*- coding: utf-8 -*-

import re
import urlparse

from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import logger

host = 'http://tubehentai.com'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Novedades", action="lista", url=host + "/most-recent/"))
    itemlist.append(Item(channel=item.channel, title="Mas visto", action="lista", url=host + "/most-viewed/"))
    itemlist.append(Item(channel=item.channel, title="Mejor valorado", action="lista", url=host + "/top-rated/"))

    itemlist.append(Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "%20")
    item.url = host + "/search/%s/" % texto
    try:
        return lista(item)
    # Se captura la excepciÛn, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<a href="((?:http|https)://tubehentai.com/video/[^"]+)" title="([^"]+)".*?'
    patron += '<span class="icon -time">.*?<span class="item__stat-label">([^<]+)</span>.*?'
    patron += '<img src="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,duration,scrapedthumbnail in matches:
        title = "[COLOR yellow]" + duration + "[/COLOR] " + scrapedtitle
        itemlist.append(Item(channel=item.channel, action="play", title=title, url=scrapedurl, 
                        fanart=scrapedthumbnail, thumbnail=scrapedthumbnail))
    next_page = scrapertools.find_single_match(data,'<a rel=\'next\' title=\'Next\' href=\'([^\']+)\'')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    url = scrapertools.find_single_match(data, '<source src="([^"]+\.mp4)"')
    server = "Directo"
    itemlist.append(Item(channel=item.channel, title="", url=url, server=server, folder=False))
    return itemlist

