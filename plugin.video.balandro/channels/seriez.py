# -*- coding: utf-8 -*-

import re, urllib

from platformcode import config, logger
from core.item import Item
from core import httptools, scrapertools, tmdb

host = 'https://seriez.co/'

IDIOMAS = {'1':'Esp', '2':'Lat', '3':'VOSE', '4':'VO',  'Latino':'Lat', 'Español':'Esp', 'Subtitulado':'VOSE', 'VSO':'VO'}


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Películas', action = 'mainlist_pelis' ))
    itemlist.append(item.clone( title = 'Series', action = 'mainlist_series' ))

    itemlist.append(item.clone( title = 'Buscar ...', action = 'search', search_type = 'all' ))

    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Lista de películas', action = 'list_all', url = host + 'todas-las-peliculas', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Estrenos de cine', action = 'list_all', url = host + 'estrenos-cine', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Mejor valoradas', action = 'list_all', url = host + 'peliculas-mas-valoradas', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anyos', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Lista de series', action = 'list_all', url = host + 'todas-las-series', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Mejor valoradas', action = 'list_all', url = host + 'mas-valoradas', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anyos', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    url = host + ('todas-las-series' if item.search_type == 'tvshow' else 'todas-las-peliculas')
    data = httptools.downloadpage(url).data

    matches = re.compile('onclick="cfilter\(this, \'([^\']+)\', 1\);"', re.DOTALL).findall(data)
    for title in matches:
        url = host + 'filtrar/%s/%s,/,' % ('series' if item.search_type == 'tvshow' else 'peliculas', title)
        itemlist.append(item.clone( title=title, url=url, action='list_all' ))

    return sorted(itemlist, key=lambda it: it.title)


def anyos(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1970, -1):
        url = host + 'filtrar/%s/,/,%d' % ('series' if item.search_type == 'tvshow' else 'peliculas', x)
        itemlist.append(item.clone( title=str(x), url=url, action='list_all' ))
        
    return itemlist


def list_all(item):
    logger.info()
    itemlist = []
    
    es_busqueda = 'search?' in item.url

    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)

    patron = '<article>\s*<a href="([^"]+)">\s*<div class="stp">(\d+)</div>'
    patron += '\s*<div class="Poster"><img src="[^"]+" data-echo="([^"]+)"></div>'
    patron += '\s*<h2>([^<]+)</h2>\s*<span>(.*?)</span>'
    
    matches = re.compile(patron, re.DOTALL).findall(data)
    for url, year, thumb, title, span in matches:
        if es_busqueda:
            tipo = 'tvshow' if 'Serie' in span else 'movie'
            if item.search_type not in ['all', tipo]: continue
        else:
            tipo = item.search_type
        
        sufijo = '' if item.search_type != 'all' else tipo
            
        if tipo == 'movie':
            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, 
                                        fmt_sufijo=sufijo,
                                        contentType='movie', contentTitle=title, infoLabels={'year': year} ))
        else:
            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, 
                                        fmt_sufijo=sufijo,
                                        contentType='tvshow', contentSerieName=title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    next_page_link = scrapertools.find_single_match(data, 'class="PageActiva">\d+</a><a href="([^"]+)')
    if next_page_link:
        itemlist.append(item.clone( title='>> Página siguiente', url=next_page_link, action='list_all' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)

    matches = re.compile('onclick="activeSeason\(this,\'temporada-(\d+)', re.DOTALL).findall(data)
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

    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)

    patron = '<a href="([^"]+)" onclick="return OpenEpisode\(this, (\d+), (\d+)\);"\s*>'
    patron += '<div class="wallEp"><img src="[^"]+" data-echo="([^"]+)"></div><h2>([^<]+)</h2>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for url, season, episode, thumb, title in matches:
        if item.contentSeason and item.contentSeason != int(season):
            continue

        titulo = '%sx%s %s' % (season, episode, title)
        itemlist.append(item.clone( action='findvideos', url=url, title=titulo, thumbnail=thumb, 
                                    contentType='episode', contentSeason=season, contentEpisodeNumber=episode ))

    # Patron diferente si no hay thumbnails
    patron = '<a href="([^"]+)" onclick="return OpenEpisode\(this, (\d+), (\d+)\);"\s*>'
    patron += '<div class="wallEp" style="[^"]+"></div><h2>([^<]+)</h2>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for url, season, episode, title in matches:
        if item.contentSeason and item.contentSeason != int(season):
            continue

        titulo = '%sx%s %s' % (season, episode, title)
        itemlist.append(item.clone( action='findvideos', url=url, title=titulo, 
                                    contentType='episode', contentSeason=season, contentEpisodeNumber=episode ))

    tmdb.set_infoLabels(itemlist)

    # ~ return itemlist
    return sorted(itemlist, key=lambda it: (it.contentSeason, it.contentEpisodeNumber))



# Asignar un numérico según las calidades del canal, para poder ordenar por este valor
def puntuar_calidad(txt):
    orden = ['360p', '480p', '720p HD', '1080p HD']
    if txt not in orden: return 0
    else: return orden.index(txt) + 1

def findvideos(item):
    logger.info()
    itemlist = []
    
    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)

    datos = scrapertools.find_multiple_matches(data, '<tr><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td></tr>')
    for servidor, calidad, idioma, enlace in datos:
        if servidor == 'Servidor': continue
        server = scrapertools.find_single_match(servidor, 'domain=([a-z]+)')
        if server == 'flix': server = 'flix555'
        url = scrapertools.find_single_match(enlace, " href='([^']+)'")
        if not url.startswith('http'): url = host + url[1:]

        itemlist.append(Item( channel = item.channel, action = 'play', server = server.lower(), referer = item.url,
                              title = '', url = url, 
                              language = IDIOMAS.get(idioma, idioma), quality = calidad, quality_num = puntuar_calidad(calidad)
                       ))

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    if item.url.startswith(host):
        headers = { 'Referer': item.referer }
        data = httptools.downloadpage(item.url, headers=headers).data
        # ~ logger.debug(data)

        url = scrapertools.find_single_match(data, '<a id="link-redirect".*? href="([^"]+)')
        if url != '': itemlist.append(item.clone(url = url))
    else:
        itemlist.append(item.clone())

    return itemlist



def search(item, texto):
    logger.info("texto: %s" % texto)
    try:
        item.url = host + 'search?go=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
