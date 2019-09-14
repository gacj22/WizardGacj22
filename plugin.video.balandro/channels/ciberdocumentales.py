# -*- coding: utf-8 -*-

from platformcode import config, logger
from core.item import Item
from core import httptools, scrapertools, servertools
import re


HOST = "http://www.ciberdocumentales.com"


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
    bloque = scrapertools.find_single_match(data, '<div id="menu">(.*?)</div>')

    patron = ' href="(/[^"]+)">([^<]+)'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for url, title in matches:

        itemlist.append(item.clone( action='list_all', title=title.capitalize(), url=HOST + url ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = data.decode('iso-8859-1').encode('utf8')

    patron = '<div class="fotonoticia">\s*<a\s*target="_blank" href="([^"]+)"><img src="([^"]+)" alt="([^"]+)"'
    patron += ' /></a><br /><br />\s*</div>\s*<div class="textonoticia">.*?<br /><br />(.*?)</div>'
    matches = scrapertools.find_multiple_matches(data, patron)

    for url, thumb, title, plot in matches:
        title = title.capitalize()

        itemlist.append(item.clone( action='findvideos', url=HOST+url, title=title, thumbnail=HOST+thumb, plot=scrapertools.htmlclean(plot),
                                    contentType='movie', contentTitle=title, contentExtra='documentary' ))

    next_page_link = scrapertools.find_single_match(data, '<span class="current">\d*</span>&nbsp;<a href="([^"]+)')
    if next_page_link != '':
        itemlist.append(item.clone( title='>> Página siguiente', action='list_all', url = HOST + next_page_link ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    url = scrapertools.find_single_match(data, '<param name="movie" value="([^"]+)')
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
        item.url = HOST + '/index.php?categoria=0&keysrc=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
