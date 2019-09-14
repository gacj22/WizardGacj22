# -*- coding: utf-8 -*-

from platformcode import config, logger
from core.item import Item
from core import httptools, scrapertools, servertools


HOST = "https://www.documaniatv.com/"


def mainlist(item):
    logger.info()
    itemlist = []
    
    itemlist.append(item.clone( title='Últimos documentales', action='list_all', url=HOST+'newvideos.html' ))
    itemlist.append(item.clone( title='Top 100 documentales', action='list_all', url=HOST+'topvideos.html' ))

    itemlist.append(item.clone( title='Por categorías', action='generos' ))

    itemlist.append(item.clone( title='Top series', action='series_top' ))
    itemlist.append(item.clone( title='Series / temas', action='series', url=HOST+'top-series-documentales.html' ))

    itemlist.append(item.clone( title = 'Buscar documental ...', action = 'search', search_type = 'documentary' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(HOST).data

    bloque = scrapertools.find_single_match(data, '<ul class="dropdown-menu">(.*?)</ul>')

    patron = ' href="([^"]+)" class="">([^<]+)'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for url, title in matches:
        if 'documentales/' in url: continue

        itemlist.append(item.clone( action='list_all', title=title, url=url ))

    return sorted(itemlist, key=lambda it: it.title)


def series(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    patron = '<span class="pm-thumb-fix-clip"><img src="([^"]+)'
    patron += '.*? href="([^"]+)"><span style="[^"]+">(.*?)</span>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for thumb, url, title in matches:

        itemlist.append(item.clone( action='list_all', title=title, thumbnail=thumb, url=url ))

    next_page_link = scrapertools.find_single_match(data, '<a href="([^"]+)"><i class="fa fa-arrow-right"></i>')
    if next_page_link:
        itemlist.append(item.clone( title='>> Página siguiente', action='series', url = next_page_link ))

    return itemlist


def series_top(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='list_all', title='La noche temática', url=HOST+'documentales/la-noche-tematica/' ))
    itemlist.append(item.clone( action='list_all', title='Documentos Tv', url=HOST+'documentales/documentos-tv/' ))

    itemlist.append(item.clone( action='list_all', title='BBC', url=HOST+'documentales/bbc/' ))
    itemlist.append(item.clone( action='list_all', title='National Geographic', url=HOST+'documentales/national-geographic/' ))
    itemlist.append(item.clone( action='list_all', title='History Channel', url=HOST+'documentales/history-channel/' ))

    itemlist.append(item.clone( action='list_all', title='Segunda guerra mundial', url=HOST+'documentales/segunda-guerra-mundial/' ))

    return itemlist



def list_all(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    matches = scrapertools.find_multiple_matches(data, '<li class="col-xs-6 col-sm-6 col-md-4">(.*?)</li>')
    if not matches: # Top 100
        matches = scrapertools.find_multiple_matches(data, '<li class="col-xs-6 col-sm-6 col-md-3">(.*?)</li>')
        
    for article in matches:
        try:
            url, title = scrapertools.find_single_match(article, ' href="([^"]+)" title="([^"]+)"')
        except:
            continue
        thumb = scrapertools.find_single_match(article, 'data-echo="([^"]+)')
        durada = scrapertools.htmlclean(scrapertools.find_single_match(article, '<span class="pm-label-duration">(.*?)</span>'))

        itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, 
                                    fmt_sufijo = '[COLOR gray](%s)[/COLOR]' % durada,
                                    contentType='movie', contentTitle=title, contentExtra='documentary' ))

    next_page_link = scrapertools.find_single_match(data, '<a href="([^"]+)">&raquo;</a>')
    if next_page_link:
        if not next_page_link.startswith('http'): next_page_link = HOST + next_page_link
        itemlist.append(item.clone( title='>> Página siguiente', action='list_all', url = next_page_link ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    url = scrapertools.find_single_match(data, '<iframe.*?src="([^"]+)')
    if url:
        if url.startswith('/'): url = 'https:' + url

        if 'cnubis.com/' in url:
            embedurl = scrapertools.find_single_match(data, '<link itemprop="embedUrl" href="([^"]+)')
            data = httptools.downloadpage(url, headers={'Referer': embedurl}).data

            url = scrapertools.find_single_match(data, 'file:\s*"([^"]+)')
            if url:
                if url.startswith('/'): url = 'https:' + url
                itemlist.append(Item( channel = item.channel, action = 'play', server='directo', 
                                      title = 'Directo', url = url
                               ))

        else:
            servidor = servertools.get_server_from_url(url)
            if servidor and servidor != 'directo':
                itemlist.append(Item( channel = item.channel, action = 'play', server=servidor, 
                                      title = servidor.capitalize(), url = url
                               ))
    # ~ else:
        # ~ logger.debug(data)

    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.url = HOST + 'search.php?keywords=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
