# -*- coding: utf-8 -*-

import re

from platformcode import config, logger
from core.item import Item
from core import httptools, scrapertools, tmdb, servertools


host = 'https://seriesblanco.info/'

IDIOMAS = { 'es':'Esp', 'la':'Lat', 'sub':'VOSE' }


def do_downloadpage(url, post=None, headers=None):
    url = url.replace('seriesblanco.org', 'seriesblanco.info').replace('http://', 'https://') # por si viene de enlaces guardados
    data = httptools.downloadpage(url, post=post, headers=headers).data
    return data


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Películas', action = 'mainlist_pelis' ))
    itemlist.append(item.clone( title = 'Series', action = 'mainlist_series' ))

    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Últimas películas', action = 'list_movies', url = host + 'ultimas-peliculas/' ))

    # ~ itemlist.append(item.clone( title='Por género', action='generos', search_type = 'movie' ))
    itemlist.append(item.clone( title='Por año', action='anyos', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title='Últimas series', action='list_all', url= host + 'ultimas-series/' ))
    itemlist.append(item.clone( title='Lista por orden alfabético', action='list_all', url= host + 'lista-de-series/' ))

    itemlist.append(item.clone( title='Por género', action='generos', search_type = 'tvshow' ))
    itemlist.append(item.clone( title='Por año', action='anyos', search_type = 'tvshow' ))
    itemlist.append(item.clone( title='Por letra (A - Z)', action='alfabetico', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host)

    matches = re.compile('<li><a href="([^"]+)">([^<]+)</a></li>', re.DOTALL).findall(data)
    for url, title in matches:
        if 'genero/' not in url: continue
        itemlist.append(item.clone( title=title, url=url, action='list_all' ))

    return sorted(itemlist, key=lambda it: it.title)

def alfabetico(item):
    logger.info()
    itemlist = []

    for letra in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        itemlist.append(item.clone( title=letra, url=host + 'lista-de-series/' + letra, action='list_all' ))

    return itemlist

def anyos(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    if item.search_type == 'movie':
        for x in range(current_year, 1959, -1):
            url = host + 'ultimas-peliculas/?years=' + str(x)
            itemlist.append(item.clone( title=str(x), url=url, action='list_movies' ))
    else:
        for x in range(current_year, 1969, -1):
            url = host + 'ultimas-series/?years=' + str(x)
            itemlist.append(item.clone( title=str(x), url=url, action='list_all' ))
        
    return itemlist



def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    patron = 'title="([^"]+)" class="loop-items" href="([^"]+)">.*?src="([^"]+)'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for title, url, thumb in matches:

        itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, 
                                    contentType='tvshow', contentSerieName=title ))

    tmdb.set_infoLabels(itemlist)

    if len(itemlist) > 0:
        next_page = scrapertools.find_single_match(data, ' href="([^"]+)"\s*><i class="Next')
        if next_page:
            itemlist.append(item.clone( title='Página siguiente >>', url=next_page, action='list_all' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = re.compile('<strong>Temporada (\d+)</strong></h2>', re.DOTALL).findall(data)
    for numtempo in matches:
        itemlist.append(item.clone( action='episodios', title='Temporada %s' % numtempo, 
                                    contentType='season', contentSeason=numtempo ))
        
    tmdb.set_infoLabels(itemlist)

    return sorted(itemlist, key=lambda it: it.contentSeason)


# Si una misma url devuelve los episodios de todas las temporadas, definir rutina tracking_all_episodes para acelerar el scrap en trackingtools.
def tracking_all_episodes(item):
    return episodios(item)


def episodios(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    if item.contentSeason: # reducir datos a la temporada pedida
        data = scrapertools.find_single_match(data, '<strong>Temporada %d</strong></h2>(.*?)</table>' % item.contentSeason)

    matches = re.compile('<tr>\s*<td>\s*<i class="icon-film"></i>(.*?)</tr>', re.DOTALL).findall(data)
    for data_epi in matches:

        url = scrapertools.find_single_match(data_epi, ' href="([^"]+)')
        try:
            season, episode = scrapertools.find_single_match(data_epi, '(\d+)\s*(?:x|X)\s*(\d+)</a>')
        except:
            continue

        languages = scrapertools.find_multiple_matches(data_epi, 'img/language/([^.]+)\.png')
        
        titulo = '%sx%s [%s]' % (season, episode, ', '.join([IDIOMAS.get(lang, lang) for lang in languages]))

        itemlist.append(item.clone( action='findvideos', url=url, title=titulo, 
                                    contentType='episode', contentSeason=season, contentEpisodeNumber=episode ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


# Asignar un numérico según las calidades del canal, para poder ordenar por este valor
def puntuar_calidad(txt):
    orden = ['360p', '480p', 'HDTV', 'Micro-HD-720p', '720p HD', 'Micro-HD-1080p', '1080p HD']
    if txt not in orden: return 0
    else: return orden.index(txt) + 1

def findvideos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = re.compile('<tr>\s*<td(.*?)</tr>', re.DOTALL).findall(data)

    if item.contentType == 'movie':
        for data_link in matches:
            # ~ if ' Descargar</a>' in data_link and not 'clicknupload' in data_link: continue # descartar descargas (menos Clicknupload) ?
            
            lang = scrapertools.find_single_match(data_link, 'img/language/([^.]+)\.png')
            url = scrapertools.find_single_match(data_link, '\?domain=([^"]+)')
            if not url: continue
            
            itemlist.append(Item( channel = item.channel, action = 'play', server = '', url = url, title = '', 
                                  language = IDIOMAS.get(lang, lang)
                           ))
    else:
        for data_link in matches:
            # ~ if ' data-tipo="descarga"' in data_link and not 'clicknupload' in data_link: continue # descartar descargas (menos Clicknupload) ?
            
            lang = scrapertools.find_single_match(data_link, 'img/language/([^.]+)\.png')
            calidad = scrapertools.find_single_match(data_link, '<td class="text-center">(.*?)</td>').strip()

            url = scrapertools.find_single_match(data_link, ' data-enlace="([^"]+)')
            if not url: continue

            itemlist.append(Item( channel = item.channel, action = 'play', server = '', url = url, title = '', 
                                  language = IDIOMAS.get(lang, lang), quality = calidad, quality_num = puntuar_calidad(calidad)
                           ))

    itemlist = servertools.get_servers_itemlist(itemlist)

    return itemlist


def search(item, texto):
    logger.info()
    try:
        if item.search_type == 'tvshow':
            item.url = host + "?post_type=ficha&s=" + texto.replace(" ", "+")
            return list_all(item)
        else:
            item.url = host + "?post_type=pelicula&s=" + texto.replace(" ", "+")
            return list_movies(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def list_movies(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    patron = 'title="([^"]+)" class="loop-items" href="([^"]+)">.*?src="([^"]+).*?<div class="year-movie">(\d+)</div>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for title, url, thumb, year in matches:

        itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, 
                                    contentType='movie', contentTitle=title, infoLabels={"year": year} ))

    if not matches: # En search no hay año
        patron = 'title="([^"]+)" class="loop-items" href="([^"]+)">.*?src="([^"]+)'
        matches = re.compile(patron, re.DOTALL).findall(data)
        for title, url, thumb in matches:

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, 
                                        contentType='movie', contentTitle=title, infoLabels={"year": '-'} ))

    tmdb.set_infoLabels(itemlist)

    if len(itemlist) > 0:
        next_page = scrapertools.find_single_match(data, ' href="([^"]+)"\s*><i class="Next')
        if next_page:
            itemlist.append(item.clone( title='Página siguiente >>', url=next_page, action='list_movies' ))

    return itemlist
