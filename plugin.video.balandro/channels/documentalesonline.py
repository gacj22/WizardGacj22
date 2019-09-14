# -*- coding: utf-8 -*-

from platformcode import config, logger
from core.item import Item
from core import httptools, scrapertools, servertools


HOST = "https://www.documentales-online.com"


def mainlist(item):
    logger.info()
    itemlist = []
    
    itemlist.append(item.clone( title='Últimos documentales', action='list_all', url=HOST ))

    itemlist.append(item.clone( title='Por categorías', action='generos' ))

    itemlist.append(item.clone( title = 'Buscar documental ...', action = 'search', search_type = 'documentary' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(HOST).data

    bloque = scrapertools.find_single_match(data, '<ul class="sub-menu">(.*?)</ul>')

    patron = ' href="([^"]+)">([^<]+)'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for url, title in matches:

        itemlist.append(item.clone( action='list_all', title=title, url=url ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    matches = scrapertools.find_multiple_matches(data, '<article(.*?)</article>')
    for article in matches:

        url, title = scrapertools.find_single_match(article, ' href="([^"]+)">(.*?)</a>')
        thumb = scrapertools.find_single_match(article, ' src="([^"]+)')
        plot = scrapertools.htmlclean(scrapertools.find_single_match(article, '<p>(.*?)</p>'))

        itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, plot=plot,
                                    contentType='movie', contentTitle=title, contentExtra='documentary' ))

    next_page_link = scrapertools.find_single_match(data, '<div class="older"><a href="([^"]+)')
    if not next_page_link:
        next_page_link = scrapertools.find_single_match(data, 'class=\'current\'>\d+</span><a class="page larger" title="[^"]*" href="([^"]+)')
    if next_page_link:
        itemlist.append(item.clone( title='>> Página siguiente', action='list_all', url = next_page_link ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)

    url = scrapertools.find_single_match(data, '<iframe.*?src="(http[^"]+)')
    if url:
        servidor = servertools.get_server_from_url(url)
        if servidor and servidor != 'directo':
            itemlist.append(Item( channel = item.channel, action = 'play', server=servidor, 
                                  title = servidor.capitalize(), url = url, language = 'Esp'
                           ))
    # ~ else:
        # ~ logger.debug(data)

    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.url = HOST + '/?s=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
