# -*- coding: utf-8 -*-

import re

from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from channelselector import get_thumb
from platformcode import logger

HOST = "http://documentales-online.com/"


def mainlist(item):
    logger.info()
    itemlist = list()
    itemlist.append(Item(channel=item.channel, title="Novedades", action="videos", url=HOST,
                         thumbnail=get_thumb('newest', auto=True)))
    itemlist.append(Item(channel=item.channel, title="Destacados", action="seccion", url=HOST, extra="destacados",
                         thumbnail=get_thumb('hot', auto=True)))
    itemlist.append(Item(channel=item.channel, title="Series destacadas", action="seccion", url=HOST, extra="series",
                         thumbnail=get_thumb('tvshows', auto=True)))
    itemlist.append(Item(channel=item.channel, title="Categorías", action="categorias", url=HOST,
                         thumbnail=get_thumb('categories', auto=True)))
    itemlist.append(Item(channel=item.channel, title="Top 100", action="listado", url=HOST + "top/",
                         thumbnail=get_thumb('more voted', auto=True)))
    itemlist.append(Item(channel=item.channel, title="Populares", action="listado", url=HOST + "populares/",
                         thumbnail=get_thumb('more watched', auto=True)))
    itemlist.append(Item(channel=item.channel, title="Series y Temas", action="listado", url=HOST + "series-temas/",
                         thumbnail=get_thumb('tvshows', auto=True)))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search",
                         thumbnail=get_thumb('search', auto=True)))
    return itemlist


def listado(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = data.replace('<span class="wpp-views">', '')
    bloque = scrapertools.find_single_match(data, 'class="post-entry(.*?)class="post-share')
    if "series-temas" not in item.url:
        patron  = '<a href="([^"]+)".*?'
        patron += 'title="([^"]+)".*?'
        patron += '/a>([^<]+)<'
        matches = scrapertools.find_multiple_matches(bloque, patron)
        for scrapedurl, scrapedtitle, scrapedextra in matches:
            itemlist.append(Item(action = "findvideos",
                                 channel = item.channel,
                                 title = scrapedtitle + scrapedextra,
                                 url = HOST + scrapedurl
                                 ))
    else:
        patron  = """<a href='([^']+)'.*?"""
        patron += """>([^<]+)<.*?"""
        matches = scrapertools.find_multiple_matches(bloque, patron)
        for scrapedurl, scrapedtitle in matches:
            itemlist.append(Item(action = "videos",
                                 channel = item.channel,
                                 title = scrapedtitle,
                                 url = HOST + scrapedurl
                                 ))
    return itemlist


def seccion(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|-\s", "", data)
    if item.extra == "destacados":
        patron_seccion = '<h4 class="widget-title">Destacados</h4><div class="textwidget"><ul>(.*?)</ul>'
        action = "findvideos"
    else:
        patron_seccion = '<h4 class="widget-title">Series destacadas</h4><div class="textwidget"><ul>(.*?)</ul>'
        action = "videos"
    data = scrapertools.find_single_match(data, patron_seccion)
    matches = scrapertools.find_multiple_matches(data, '<a href="([^"]+)">(.*?)</a>')
    aux_action = action
    for url, title in matches:
        if item.extra != "destacados" and "Cosmos (Carl Sagan)" in title:
            action = "findvideos"
        else:
            action = aux_action
        itemlist.append(item.clone(title=title, url=url, action=action, contentTitle=title))
    return itemlist


def videos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|-\s", "", data)
    pagination = scrapertools.find_single_match(data, "rel='next' href='([^']+)'")
    if not pagination:
        pagination = scrapertools.find_single_match(data, '<span class=\'current\'>\d</span>'
                                                          '<a class="page larger" href="([^"]+)">')
    patron = '<ul class="sp-grid">(.*?)</ul>'
    data = scrapertools.find_single_match(data, patron)
    matches = re.compile('<a href="([^"]+)">(.*?)</a>.*?<img.*?src="([^"]+)"', re.DOTALL).findall(data)
    for url, title, thumb in matches:
        itemlist.append(item.clone(title=title, url=url, action="findvideos", contentTitle=title, thumbnail=thumb))
    if pagination:
        itemlist.append(item.clone(title=">> Página siguiente", url=pagination))
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|-\s", "", data)
    data = scrapertools.find_single_match(data, 'a href="#">Categorías</a><ul class="sub-menu">(.*?)</ul>')
    matches = scrapertools.find_multiple_matches(data, '<a href="([^"]+)">(.*?)</a>')
    for url, title in matches:
        itemlist.append(item.clone(title=title, url=url, action="videos", contentTitle=title))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    try:
        item.url = HOST + "?s=%s" % texto
        return videos(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|-\s", "", data)
    if "Cosmos (Carl Sagan)" in item.title:
        patron  = '(?s)<p><strong>([^<]+)<.*?'
        patron += '<iframe.*?src="([^"]+)"'
        matches = scrapertools.find_multiple_matches(data,patron)
        for title, url in matches:
            itemlist.append(item.clone(action = "play", title=title, url=url
                           ))
    else:
        data = scrapertools.find_multiple_matches(data, '<iframe.+?src="([^"]+)"')
        itemlist.extend(servertools.find_video_items(data=",".join(data)))
        for videoitem in itemlist:
            videoitem.contentTitle = item.contentTitle
            videoitem.channel = item.channel
    itemlist = servertools.get_servers_itemlist(itemlist)
    return itemlist
