# -*- coding: utf-8 -*-

import re
import urlparse

from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import logger

host = "https://www.youfreeporntube.net"

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, action="lista", title="Útimos videos",
                         url= host + "/newvideos.html?&page=1"))
    itemlist.append(Item(channel=item.channel, action="lista", title="Populares",
                         url=host + "/topvideos.html?page=1"))
    itemlist.append(
        Item(channel=item.channel, action="categorias", title="Categorias", url=host + "/browse.html"))

    itemlist.append(Item(channel=item.channel, action="search", title="Buscar",
                         url=host + "/search.php?keywords="))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "{0}{1}".format(item.url, texto)
    try:
        return lista(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}", "", data)
    patron = '<div class="pm-li-category"><a href="([^"]+)">.*?.<h3>(.*?)</h3></a>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for url, actriz in matches:
        itemlist.append(Item(channel=item.channel, action="lista", title=actriz, url=url))
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}", "", data)
    patron = '<li><div class=".*?'
    patron += '<a href="([^"]+)".*?'
    patron += '<img src="([^"]+)".*?alt="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)
    itemlist = []
    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        url = urlparse.urljoin(item.url, scrapedurl)
        thumbnail = urlparse.urljoin(item.url, scrapedthumbnail)
        title = scrapedtitle.strip()
        itemlist.append(Item(channel=item.channel, action="play", thumbnail=thumbnail, fanart=thumbnail, title=title,
                             url=url,
                             viewmode="movie", folder=True))
    paginacion = scrapertools.find_single_match(data,
                                                '<li class="active">.*?</li>.*?<a href="([^"]+)">')
    if paginacion:
        paginacion = urlparse.urljoin(item.url,paginacion)
        itemlist.append(Item(channel=item.channel, action="lista", title=">> Página Siguiente",
                             url= paginacion))
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    url = scrapertools.find_single_match(data, '<div id="video-wrapper">.*?<iframe.*?src="([^"]+)"')
    itemlist.append(item.clone(action="play", title=url, url=url ))
    itemlist = servertools.get_servers_itemlist(itemlist)
    return itemlist


