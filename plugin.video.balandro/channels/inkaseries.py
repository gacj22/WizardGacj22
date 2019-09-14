# -*- coding: utf-8 -*-

import re

from platformcode import config, logger
from core.item import Item
from core import httptools, scrapertools, tmdb, servertools

host = 'https://www.inkaseries.tv/'

IDIOMAS = {'Latino': 'Lat', 'Español': 'Esp', 'Castellano': 'Esp', 'Subtitulado': 'VOSE'}


def mainlist(item):
    return mainlist_series(item)

def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Últimas agregadas', action = 'list_all', url = host + 'ultimas-series-agregadas/' ))

    itemlist.append(item.clone( title = 'Más vistas', action = 'list_all', url = host + 'categoria/series-mas-vistas/' ))
    # ~ itemlist.append(item.clone( title = 'Recomendadas', action = 'list_all', url = host + 'categoria/recomendadas/' ))
    # ~ itemlist.append(item.clone( title = 'Destacadas', action = 'list_all', url = host + 'categoria/destacadas/' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(host).data
    # ~ logger.debug(data)
    data = scrapertools.find_single_match(data, '<div class="sub_title">Géneros</div>\s*<ul>(.*?)</ul>')

    patron = '<li><a href="([^"]+)"><span[^>]*></span> <i>([^<]+)</i> <b>(\d+)'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for url, title, cantidad in matches:
        if cantidad == '0': continue
        if '/recomendadas/' in url or '/series-mas-vistas/' in url or '/destacadas/' in url: continue # pq ya están en el menú principal

        itemlist.append(item.clone( action="list_all", title='%s (%s)' % (title.strip(), cantidad), url=url ))

    return sorted(itemlist, key=lambda it: it.title)


def list_all(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)

    if '<div class="tiulo-c">' in data:
        data = data.split('<div class="tiulo-c">')[1]

    patron = '<li class="item">\s*<a class="poster" href="([^"]+)" title="([^"]+)">\s*<img (?:data-lazy-type="image" |)(?:data-|)src="([^"]+)'

    matches = re.compile(patron, re.DOTALL).findall(data)
    num_matches = len(matches)

    for url, title, thumb in matches:

        itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, 
                                    contentType='tvshow', contentSerieName=title ))

    tmdb.set_infoLabels(itemlist)

    next_page_link = scrapertools.find_single_match(data, '<li><a href="([^"]+)"><span aria-hidden="true">&raquo;')
    if next_page_link:
        itemlist.append(item.clone( title='>> Página siguiente', url=next_page_link, action='list_all' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)

    matches = re.compile('</span>\s*Temporada (\d+)\s*</a>\s*</h3>', re.DOTALL).findall(data)
    for numtempo in matches:
        itemlist.append(item.clone( action='episodios', title='Temporada %s' % numtempo, 
                                    contentType='season', contentSeason=numtempo ))
        
    tmdb.set_infoLabels(itemlist)

    return itemlist


# Si una misma url devuelve los episodios de todas las temporadas, definir rutina tracking_all_episodes para acelerar el scrap en trackingtools.
def tracking_all_episodes(item):
    return episodios(item)

def episodios(item):
    logger.info()
    itemlist = []

    IDIOMAS_png = {'la_la': 'Lat', 'es_es':'Esp', 'en_es': 'VOSE', 'en_en': 'Eng'}

    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)

    matches = re.compile('<tr>(.*?)</tr>', re.DOTALL).findall(data)
    for data_epi in matches:
        if '<th>' in data_epi: continue

        url = scrapertools.find_single_match(data_epi, ' href="([^"]+)"')
        try:
            season, episode, title = scrapertools.find_single_match(data_epi, 'Temporada (\d+), Episodio (\d+) - ([^"]*)')
        except:
            # ~ logger.debug(data_epi)
            continue

        if item.contentSeason and item.contentSeason != int(season):
            continue

        langs = scrapertools.find_multiple_matches(data_epi, '/([^/-]+)-(?:min|).png')
        
        titulo = '%sx%s %s [%s]' % (season, episode, title, ', '.join([IDIOMAS_png.get(lang, lang) for lang in langs]))

        itemlist.append(item.clone( action='findvideos', url=url, title=titulo, 
                                    contentType='episode', contentSeason=season, contentEpisodeNumber=episode ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)
    
    # Enlaces en "ver online":
    patron = '<tr>\s*<td><a href="([^"]+)"'
    patron += '.*?<td><img src="[^"]+" title="([^"]+)"'
    patron += '.*?<td>([^<]+)</td>\s*<td>([^<]+)</td>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for url, servidor, language, quality in matches:
        # ~ logger.info('%s %s %s' % (servidor, url, quality))
        language = language.replace('\n', '').strip()
        quality = quality.replace('\n', '').strip()

        # ~ itemlist.append(Item( channel = item.channel, action = 'play', server = servidor.lower(),
        itemlist.append(Item( channel = item.channel, action = 'play', server = '',
                              title = '', url = url,
                              language = IDIOMAS.get(language, language), quality = quality
                       ))

    # Enlaces en "embeds":
    matches_lang = re.compile('<a href="#embed\d+" data-toggle="tab">([^<]+)', re.DOTALL).findall(data)
    matches = re.compile('id="embed\d+">\s*<iframe src="([^"]+)', re.DOTALL).findall(data)
    for ilang, url in enumerate(matches):
        if ilang >= len(matches_lang): break
        language = matches_lang[ilang].replace('\n', '').strip()
        # ~ logger.info('%s %s' % (url, language))
        
        itemlist.append(Item( channel = item.channel, action = 'play', server = '',
                              title = '', url = url,
                              language = IDIOMAS.get(language, language)
                       ))

    itemlist = servertools.get_servers_itemlist(itemlist)

    # Dejar desconocidos como indeterminados para resolverse en el play
    for it in itemlist:
        if it.server == 'desconocido' and it.url.startswith(host):
            it.server = ''

    return itemlist

def play(item):
    logger.info()
    itemlist = []

    if item.url.startswith(host): 
        data = httptools.downloadpage(item.url, headers={'Referer': host}).data
        OLID = scrapertools.find_single_match(data, "var OLID = '([^']+)")
        if OLID:
            url = 'https://www.inkaseries.tv/hideload/?r=' + OLID[::-1]
            data = httptools.downloadpage(url, headers={'Referer': host}).data

            url = scrapertools.find_single_match(data, '<meta name="og:url" content="([^"]+)')
            if url:
                itemlist.append(item.clone(url=url, server='openload'))
            # ~ else:
                # ~ logger.debug(data)
        # ~ else:
            # ~ logger.debug(data)

    else:
        itemlist.append(item.clone())
    
    return itemlist

          
def search(item, texto):
    logger.info()
    itemlist = []
    try:
       item.url = host + '?s=' + texto.replace(" ", "+")
       return list_all(item)
    except:
       import sys
       for line in sys.exc_info():
           logger.error("%s" % line)
       return []
