# -*- coding: utf-8 -*-

from platformcode import config, logger
from core.item import Item
from core import httptools, scrapertools, servertools


HOST = "http://www.teledocumentales.com"


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

    bloque = scrapertools.find_single_match(data, '<div id="menu_horizontal">(.*?)</div>')

    patron = ' href="([^"]+)">([^<]+)'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for url, title in matches:

        itemlist.append(item.clone( action='list_all', title=title, url=url ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    matches = scrapertools.find_multiple_matches(data, '<!--Video-->(.*?)<div style="clear:both"></div></div>')
    for article in matches:

        url = scrapertools.find_single_match(article, ' href="([^"]+)')
        thumb, title = scrapertools.find_single_match(article, ' src="([^"]+)" alt="([^"]+)')
        plot = scrapertools.htmlclean(scrapertools.find_single_match(article, '<div class="excerpt">(.*?)</div>')).strip()

        year = scrapertools.find_single_match(article, '<span class="item">A&ntilde;o: <span class="item2">(\d+)')
        minutos = scrapertools.find_single_match(article, '<span class="item">Duraci&oacute;n: <span class="item2">(\d+)')
        idioma = scrapertools.find_single_match(article, '<span class="item">Idioma: <span class="item2">([^<]+)')
        subtit = scrapertools.find_single_match(article, '<span class="item">Subtitulado: <span class="item2">([^<]+)')
        lang = 'VOSE' if subtit == 'Si' else ('Esp' if 'Espa' in idioma else 'VO')

        itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, 
                                    contentType='movie', contentTitle=title, contentExtra='documentary',
                                    infoLabels={"year": year, "plot": plot}, 
                                    languages=lang, fmt_sufijo='(%s min)' % minutos ))

    next_page_link = scrapertools.find_single_match(data, 'class="current">\d+</span><a href="([^"]+)')
    if next_page_link:
        itemlist.append(item.clone( title='>> Página siguiente', action='list_all', url = next_page_link ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    url = scrapertools.find_single_match(data, 'href="http://mediagetter\.com/\?url=([^"]+)')
    if url:
        servidor = servertools.get_server_from_url(url)
        if servidor and servidor != 'directo':
            itemlist.append(Item( channel = item.channel, action = 'play', server=servidor, 
                                  title = servidor.capitalize(), url = url, language = item.languages
                           ))
    # ~ else:
        # ~ logger.debug(data)

    return itemlist


def list_search(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    matches = scrapertools.find_multiple_matches(data, '<div class="card-content"(.*?)</ul>')
    for article in matches:

        url = scrapertools.find_single_match(article, "href='([^']+)").replace('//m.', '//www.')
        thumb = scrapertools.find_single_match(article, ' src="([^"]+)"')

        title = scrapertools.find_single_match(article, '<li class="title">(.*?)</li>')
        minutos = scrapertools.find_single_match(article, '<li class="duration">(\d+)')
        year = scrapertools.find_single_match(article, '<li class="year">(\d+)')

        itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, 
                                    contentType='movie', contentTitle=title, contentExtra='documentary',
                                    infoLabels={"year": year}, 
                                    fmt_sufijo='(%s min)' % minutos ))

    next_page_link = scrapertools.find_single_match(data, '<li><a href="([^"]+)" class="next"')
    if next_page_link:
        itemlist.append(item.clone( title='>> Página siguiente', action='list_search', url = next_page_link ))

    return itemlist

def search(item, texto):
    logger.info()
    try:
        # Usar web móvil para buscar pq en la desktop no devuelve resultados
        item.url = HOST.replace('http://www.', 'http://m.') + '/?s=' + texto.replace(" ", "+")
        return list_search(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
