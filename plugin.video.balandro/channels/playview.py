# -*- coding: utf-8 -*-

import re

from platformcode import config, logger
from core.item import Item
from core import httptools, scrapertools, tmdb


host = 'https://playview.io/'

IDIOMAS = {'Latino': 'Lat', 'Español': 'Esp', 'Subtitulado': 'VOSE'}

perpage = 20 # preferiblemente un múltiplo de los elementos que salen en la web (6x10=60) para que la subpaginación interna no se descompense

# En la web: No hay acceso a serie solamente a serie+temporada


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

    itemlist.append(item.clone( title = 'Lista de películas', action = 'list_all', url = host + 'peliculas-online', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Lista de series', action = 'list_all', url = host + 'series-online', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Series animadas', action = 'list_all', url = host + 'series-animadas-online', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Series anime', action = 'list_all', url = host + 'anime-online', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(host).data
    
    patron = '<li><a href="(%s[^"]+)">([^<]+)</a></li>' % (host + 'peliculas-online/')
    matches = re.compile(patron, re.DOTALL).findall(data)

    for url, title in matches:

        itemlist.append(item.clone( action="list_all", title=title.strip(), url=url ))

    return sorted(itemlist, key=lambda it: it.title)



def list_all(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0

    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)

    matches = re.compile('<div class="spotlight_image lazy"(.*?)<div class="playRing">', re.DOTALL).findall(data)
    if '/search/' in item.url and item.search_type != 'all': # para búsquedas eliminar pelis/series según corresponda
        matches = filter(lambda x: (' class="info-series"' not in x and item.search_type == 'movie') or \
                                   (' class="info-series"' in x and item.search_type == 'tvshow'), matches)
    num_matches = len(matches)

    for article in matches[item.page * perpage:]:
        
        tipo = 'tvshow' if ' class="info-series"' in article else 'movie'
        sufijo = '' if item.search_type != 'all' else tipo

        thumb = scrapertools.find_single_match(article, ' data-original="([^"]+)"')
        title = scrapertools.find_single_match(article, '<div class="spotlight_title">(.*?)</div>').strip()
        url = scrapertools.find_single_match(article, ' href="([^"]+)"')
        year = scrapertools.find_single_match(article, '<span class="slqual sres">(\d+)</span>')
        quality = 'HD' if '<span class="slqual-HD">HD</span>' in article else ''
        
        if tipo == 'movie':
            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, 
                                        qualities=quality, fmt_sufijo=sufijo,
                                        contentType='movie', contentTitle=title, infoLabels={'year': year} ))
        else:
            s_e = scrapertools.find_single_match(title, '<div class="info-series">(.*?)</div>')
            title = scrapertools.find_single_match(title, '(.*?)<br').strip()
            title = title[:1].upper() + title[1:] # algunas seriesno tienen la mayúscula inicial
            s_e = re.sub('<[^>]*>', '', s_e)
            season = scrapertools.find_single_match(s_e, 'Temporada (\d+)')
            if season == '':
                season = scrapertools.find_single_match(url, '-temp-(\d+)$')
            if season == '':
                season = '1'
                
            titulo = '%s [COLOR gray](Temporada %s)[/COLOR]' % (title, season)
            itemlist.append(item.clone( action='episodios', url=url, title=titulo, thumbnail=thumb, 
                                        qualities=quality, fmt_sufijo=sufijo, 
                                        contentType='season', contentSerieName=title, contentSeason=season, infoLabels={'year': year} ))

        if len(itemlist) >= perpage: break

    tmdb.set_infoLabels(itemlist)

    # Subpaginación interna y/o paginación de la web
    buscar_next = True
    if num_matches > perpage: # subpaginación interna dentro de la página si hay demasiados items
        hasta = (item.page * perpage) + perpage
        if hasta < num_matches:
            itemlist.append(item.clone( title='>> Página siguiente', page=item.page + 1, action='list_all' ))
            buscar_next = False

    if buscar_next:
        next_page_link = scrapertools.find_single_match(data, '<a href="([^"]+)" class="page-link" aria-label="Next"')
        if next_page_link:
            itemlist.append(item.clone( title='>> Página siguiente', url=next_page_link, page=0, action='list_all' ))

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    dataid = scrapertools.find_single_match(data, 'data-id="([^"]+)"')
    datatype = '1'

    post = 'set=LoadOptionsEpisode&action=EpisodesInfo&id=%s&type=%s' % (dataid, datatype)
    data = httptools.downloadpage(host + 'playview', post=post).data

    patron = ' data-episode="(\d+)"'
    patron += '.*?url\(([^)]+)\)'
    patron += '.*?<p class="ellipsized">(.*?)</p>'
    patron += '.*?<div class="episodeSynopsis">(.*?)</div>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for episode, thumb, title, plot in matches:

        titulo = '%sx%s %s' % (item.contentSeason, episode, title)
        itemlist.append(item.clone( action='findvideos', title=titulo, thumbnail=thumb, plot=plot, dataid=dataid, datatype=datatype,
                                    contentType='episode', contentEpisodeNumber=episode ))

    if len(matches) == 0:
        post = 'set=LoadOptionsEpisode&action=EpisodeList&id=%s&type=%s' % (dataid, datatype)
        data = httptools.downloadpage(host + 'playview', post=post).data

        patron = ' data-episode="(\d+)" value="[^"]*" title="([^"]+)'
        matches = re.compile(patron, re.DOTALL).findall(data)

        for episode, title in matches:
            title = re.sub('^\d+\s*-', '', title).strip()
            titulo = '%sx%s %s' % (item.contentSeason, episode, title)
            itemlist.append(item.clone( action='findvideos', title=titulo, dataid=dataid, datatype=datatype,
                                        contentType='episode', contentEpisodeNumber=episode ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


# Asignar un numérico según las calidades del canal, para poder ordenar por este valor
def puntuar_calidad(txt):
    orden = ['CAM', 'TS', 'DVDRip', 'HD 720p', 'HD 1080p']
    if txt not in orden: return 0
    else: return orden.index(txt) + 1

def findvideos(item):
    logger.info()
    itemlist = []

    if item.dataid:
        tipo = item.datatype
        post = 'set=LoadOptionsEpisode&action=Step1&id=%s&type=%s&episode=%d' % (item.dataid, item.datatype, item.contentEpisodeNumber)
    else:
        data = httptools.downloadpage(item.url).data

        dataid = scrapertools.find_single_match(data, 'data-id="([^"]+)"')
        tipo = 'Movie'
        post = 'set=LoadOptions&action=Step1&id=%s&type=%s' % (dataid, tipo)

    data = httptools.downloadpage(host + 'playview', post=post).data
    
    calidades = scrapertools.find_multiple_matches(data, 'data-quality="([^"]+)"')
    for calidad in calidades:
        if item.dataid:
            post = 'set=LoadOptionsEpisode&action=Step2&id=%s&type=%s&quality=%s&episode=%d' % (item.dataid, item.datatype, calidad.replace(' ', '+'), item.contentEpisodeNumber)
        else:
            post = 'set=LoadOptions&action=Step2&id=%s&type=%s&quality=%s' % (dataid, tipo, calidad.replace(' ', '+'))
        data = httptools.downloadpage(host + 'playview', post=post).data
        # ~ logger.debug(data)
        
        enlaces = scrapertools.find_multiple_matches(data, 'data-id="([^"]+)">\s*<h4>([^<]+)</h4>\s*<small><img src="https://www\.google\.com/s2/favicons\?domain=([^"]+)')
        for linkid, lang, servidor in enlaces:
            # ~ logger.debug('%s %s %s' % (linkid, lang, servidor))
            servidor = servidor.replace('https://', '').replace('http://', '').replace('www.', '').lower()
            servidor = servidor.split('.', 1)[0]
            if servidor == 'vev': servidor = 'vevio'
            calidad = calidad.replace('(', '').replace(')', '').strip()
            
            itemlist.append(Item( channel = item.channel, action = 'play', server = servidor,
                                  title = '', linkid = linkid, linktype = tipo, linkepi = item.contentEpisodeNumber if item.dataid else -1,
                                  language = IDIOMAS.get(lang, lang), quality = calidad, quality_num = puntuar_calidad(calidad)
                           ))
    
    return itemlist


def play(item):
    logger.info()
    itemlist = []

    if item.linkepi == -1:
        post = 'set=LoadOptions&action=Step3&id=%s&type=%s' % (item.linkid, item.linktype)
    else:
        post = 'set=LoadOptionsEpisode&action=Step3&id=%s&type=%s&episode=%d' % (item.linkid, item.linktype, item.linkepi)

    data = httptools.downloadpage(host + 'playview', post=post).data

    url = scrapertools.find_single_match(data, '<iframe class="[^"]*" src="([^"]+)')
    if url == '':
        url = scrapertools.find_single_match(data, '<iframe src="([^"]+)')

    if url != '':
        itemlist.append(item.clone(url = url))

    return itemlist



def search(item, texto):
    logger.info()
    itemlist = []
    try:
       item.url = host + 'search/' + texto.replace(" ", "+")
       return list_all(item)
    except:
       import sys
       for line in sys.exc_info():
           logger.error("%s" % line)
       return []
