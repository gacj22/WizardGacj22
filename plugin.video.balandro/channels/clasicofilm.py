# -*- coding: utf-8 -*-

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, tmdb, servertools, jsontools
import re

host = 'https://www.classicofilm.com/'

perpage = 10


def mainlist(item):
    return mainlist_pelis(item)

def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Lista de películas', action = 'list_all',  
                                url = host+'feeds/posts/summary?start-index=1&max-results=%d&alt=json-in-script&callback=finddatepost' % perpage))

    # ~ itemlist.append(item.clone( title = 'Lista de películas (opción 2)', action = 'list_search', url = host ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por época', action = 'epocas', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anyos', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie', plot='En el diálogo de búsqueda se puede poner el nombre de una película pero también el nombre de un actor o una actriz, o directores.' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    url = host+'feeds/posts/summary?start-index=1&max-results=1&alt=json-in-script&callback=finddatepost'
    data = httptools.downloadpage(url).data

    data = scrapertools.find_single_match(data, '"feed":(.*?)\}\);')
    data = jsontools.load(data)
    if 'category' not in data: return itemlist

    for categ in data['category']:
        if 'term' in categ:
            if categ['term'].isdigit(): continue
            if categ['term'].startswith('Siglo') or categ['term'].startswith('Año'): continue
            url = host+'feeds/posts/summary/-/%s?start-index=1&max-results=%d&alt=json-in-script&callback=finddatepost' % (categ['term'].replace(' ', '%20'), perpage)
            if categ['term'] in ['cuatro', 'viajes en el tiempo']: categ['term'] = categ['term'].capitalize()
            itemlist.append(item.clone( title=categ['term'], url=url, action='list_all' ))

    # ~ return sorted(itemlist, key=lambda it: it.title)
    return sorted(itemlist, key=lambda it: it.title.replace('Á', 'A').replace('Ó', 'O'))


def epocas(item):
    logger.info()
    itemlist = []

    url = host+'feeds/posts/summary?start-index=1&max-results=1&alt=json-in-script&callback=finddatepost'
    data = httptools.downloadpage(url).data

    data = scrapertools.find_single_match(data, '"feed":(.*?)\}\);')
    data = jsontools.load(data)
    if 'category' not in data: return itemlist

    for categ in data['category']:
        if 'term' in categ:
            if categ['term'].isdigit(): continue
            if not categ['term'].startswith('Siglo') and not categ['term'].startswith('Año'): continue
            url = host+'feeds/posts/summary/-/%s?start-index=1&max-results=%d&alt=json-in-script&callback=finddatepost' % (categ['term'].replace(' ', '%20'), perpage)
            itemlist.append(item.clone( title=categ['term'], url=url, action='list_all' ))

    return sorted(itemlist, key=lambda it: it.title)


def anyos(item):
    logger.info()
    itemlist = []

    url = host+'feeds/posts/summary?start-index=1&max-results=1&alt=json-in-script&callback=finddatepost'
    data = httptools.downloadpage(url).data

    data = scrapertools.find_single_match(data, '"feed":(.*?)\}\);')
    data = jsontools.load(data)
    if 'category' not in data: return itemlist

    for categ in data['category']:
        if 'term' in categ:
            if not categ['term'].isdigit(): continue
            if int(categ['term']) < 1900: continue
            
            url = host+'feeds/posts/summary/-/%s?start-index=1&max-results=%d&alt=json-in-script&callback=finddatepost' % (categ['term'], perpage)
            itemlist.append(item.clone( title=categ['term'], url=url, action='list_all' ))

    return sorted(itemlist, key=lambda it: it.title, reverse=True)


def list_all(item):
    logger.info()
    itemlist = []
    
    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)
    
    data = scrapertools.find_single_match(data, '"feed":(.*?)\}\);')
    data = jsontools.load(data)
    if 'entry' not in data: return itemlist
    
    for article in data['entry']:
        try:
            title, year, quality = scrapertools.find_single_match(article['title']['$t'], '(.*?)\((\d{4})\)(.*)')
            title = title.strip()
            url = ''
            for link in article['link']:
                if link['rel'] == 'alternate':
                    url = link['href']
            thumb = article['media$thumbnail']['url'].replace('s72-c', 's320')
            plot = scrapertools.decodeHtmlentities(article['summary']['$t']).strip() # !?
        except:
            # ~ logger.debug(article)
            continue

        itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, 
                                    qualities=quality.strip(),
                                    contentType='movie', contentTitle=title, infoLabels={'year': year, 'plot': plot} ))

    tmdb.set_infoLabels(itemlist)
    
    start_index = int(data['openSearch$startIndex']['$t'])
    max_results = int(data['openSearch$itemsPerPage']['$t'])
    total_results = int(data['openSearch$totalResults']['$t'])
    # ~ logger.info('total_results: %d' % total_results)
    next_start_index = start_index + max_results
    if next_start_index < total_results:
        next_page_link = item.url.replace('start-index=%d' % start_index, 'start-index=%d' % next_start_index)
        itemlist.append(item.clone( title='>> Página siguiente', url=next_page_link, action='list_all' ))

    return itemlist



def verificar_width(txt):
    if 'width="720"' in txt or 'width=720' in txt or 'width="640"' in txt or 'width=640' in txt: return True
    if 'width:720' in txt or 'width: 720' in txt or 'width:640' in txt or 'width: 640' in txt: return True
    return False

def decode_id(txt):
    res = ''
    for i in range(0, len(txt), 3):
        res += '\\u0' + txt[i:i+3]
    return res.decode('unicode-escape')

def findvideos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)

    lang = 'VOSE' if '-VOSE' in item.qualities else 'Esp'
    
    # Opción <iframe
    matches = scrapertools.find_multiple_matches(data, '<(?i)iframe(.*?)>')
    for iframe in matches:
        # ~ logger.debug(iframe)
        if not verificar_width(iframe.lower()): continue
        url = scrapertools.find_single_match(iframe, '(?i)src="([^"]+)')
        if url:
            if url.startswith('//'): url = 'https:' + url
            itemlist.append(Item( channel = item.channel, action = 'play', server = '',
                                  title = '', url = url,
                                  language = lang, quality = item.qualities
                           ))

    # Opción <div id=" para NetuTv
    matches = scrapertools.find_multiple_matches(data, '<div id="([^"]+)" style="([^"]+)">')
    for varid, estilos in matches:
        if not verificar_width(estilos.lower()): continue
        v = scrapertools.find_single_match(decode_id(varid), '"v":"([^"]+)')
        if v:
            url = 'http://netu.tv/watch_video.php?v=' + v
            itemlist.append(Item( channel = item.channel, action = 'play', server = '',
                                  title = '', url = url,
                                  language = lang, quality = item.qualities
                           ))


    itemlist = servertools.get_servers_itemlist(itemlist)
    
    return itemlist


def list_search(item):
    logger.info()
    itemlist = []
    
    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)

    matches = scrapertools.find_multiple_matches(data, "<div class='post hentry'>(.*?)<div class='post-footer'>")
    for article in matches:
        try:
            url, title = scrapertools.find_single_match(article, "<a href='([^']+)'>(.*?)</a>")
            titulo, year, quality = scrapertools.find_single_match(title, '(.*?)\((\d{4})\)(.*)')
        except:
            # ~ logger.debug(article)
            continue

        title = titulo.strip()
        thumb = scrapertools.find_single_match(article, '<img .*? src="([^"]+)"')
        plot = scrapertools.find_single_match(article, '<dd itemprop="description"[^>]*>(.*?)</dd>')
        plot = scrapertools.decodeHtmlentities(plot).strip()

        itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, 
                                    qualities=quality.strip(),
                                    contentType='movie', contentTitle=title, infoLabels={'year': year, 'plot': plot} ))

    tmdb.set_infoLabels(itemlist)

    next_page_link = scrapertools.find_single_match(data, "<a class='blog-pager-older-link' href='([^']+)'")
    if next_page_link:
        itemlist.append(item.clone( title='>> Página siguiente', url=next_page_link, action='list_search' ))

    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.url = host+'search?q=' + texto.replace(' ', '%20')
        return list_search(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
