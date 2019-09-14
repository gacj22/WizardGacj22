# -*- coding: utf-8 -*-

import re, urllib

from platformcode import config, logger
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'http://www.wikiseriesonline.nu/'

IDIOMAS = {'espanol': 'Esp', 'latino': 'Lat', 'subtitulado': 'VOSE', 'ingles': 'Eng'}


def mainlist(item):
    return mainlist_series(item)

def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title='Todas las series', action='list_all', url=host + 'category/serie' ))
    # ~ itemlist.append(item.clone( title='Series documentales', action='list_all', url=host + 'category/documental' ))

    itemlist.append(item.clone( title='Series por género', action='generos' ))

    itemlist.append(item.clone( title='Nuevos capítulos', action='list_all', url=host + 'category/episode' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow' ))

    return itemlist



def generos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(host).data

    matches = re.compile('<li> <a href="(/category/[^"]+)">([^<]+)</a> </li>', re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle in matches:
        if scrapedtitle != 'Series':
            itemlist.append(item.clone(title=scrapedtitle, url=host + scrapedurl, action='list_all'))

    return sorted(itemlist, key=lambda it: it.title)


def list_all(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)

    matches = re.compile('<!--  post-->(.*?)<!-- end post-->', re.DOTALL).findall(data)
    for data_show in matches:
        url, title = scrapertools.find_single_match(data_show, '<a class="info-title one-line" href="([^"]+)" title="([^"]+)"')
        thumb = scrapertools.find_single_match(data_show, 'src="([^"]+)"')
        
        title = title.replace('&#215;','x').strip()
        name_season_episode = scrapertools.find_single_match(title, '(.*?) (\d+)\s*(?:x|X)\s*(\d+)')

        if name_season_episode:
            # No hay enlace a la serie, solamente al episodio
            nombre, season, episode = name_season_episode
            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, 
                                        contentType='episode', contentSerieName=nombre, contentSeason=season, contentEpisodeNumber=episode ))

        else:
            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, 
                                        contentType='tvshow', contentSerieName=title ))

    tmdb.set_infoLabels(itemlist)

    next_page = scrapertools.find_single_match(data, "rel='next' href='([^']+)")
    if next_page:
        itemlist.append(item.clone( url=next_page, title='Siguiente >>' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)

    matches = re.compile(' id="season-toggle-(\d+)"', re.DOTALL).findall(data)
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

    matches = re.compile('<li class="ep-list-item"(.*?)</li>', re.DOTALL).findall(data)
    for data_epi in matches:

        url, s_e = scrapertools.find_single_match(data_epi, '<a href="([^"]+)" >([^<]+)</a>')
        season, episode = scrapertools.find_single_match(s_e, '(\d+)\s*(?:x|X)\s*(\d+)')

        if item.contentSeason and item.contentSeason != int(season):
            continue

        title = scrapertools.find_single_match(data_epi, '<span class="name">([^<]+)</span>').strip()
        languages = scrapertools.find_multiple_matches(data_epi, 'class="lgn lgn-([^"]+)"')
        
        titulo = '%s %s [%s]' % (s_e, title, ', '.join([IDIOMAS.get(lang, lang) for lang in languages]))

        itemlist.append(item.clone( action='findvideos', url=url, title=titulo, 
                                    contentType='episode', contentSeason=season, contentEpisodeNumber=episode ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


# Asignar un numérico según las calidades del canal, para poder ordenar por este valor
def puntuar_calidad(txt):
    orden = ['HD', 'HDTV', 'Micro-HD-720p', 'HD 720p', 'Micro-HD-1080p']
    if txt not in orden: return 0
    else: return orden.index(txt) + 1

def findvideos(item):
    logger.info()
    itemlist = []

    calidades = {'1':'HDTV', '2':'HD', '3':'HD 720p', '4':'Micro-HD-1080p', '5':'Micro-HD-720p'}
    idiomas = {'1':'Lat', '3':'Esp', '4':'VOSE', '5':'Eng'}

    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)
    
    matches = re.compile('<tr id=row\d+ data-type="1" data-lgn="([^"]+)" data-qa="([^"]+)" data-link="([^"]+)"', re.DOTALL).findall(data)
    for language, quality, url in matches:
        calidad = calidades.get(quality, '?')

        itemlist.append(Item(channel = item.channel, action = 'play',
                             title = '', url = url,
                             language = idiomas.get(language, '?'), quality = calidad, quality_num = puntuar_calidad(calidad)
                       ))

    matches = re.compile('<a href="/(reproductor?[^"]+)', re.DOTALL).findall(data)
    for url in matches:
        try:
            aux = url.rsplit(' - ', 1)[1].lower()
        except:
            aux = url.lower()

        if 'latino' in aux: language = 'Lat'
        elif 'espa' in aux: language = 'Esp'
        elif 'subtitulado' in aux: language = 'VOSE'
        else: language = 'VO'

        if 'micro-hd-1080p' in aux: calidad = 'Micro-HD-1080p'
        elif 'micro-hd-720p' in aux: calidad = 'Micro-HD-720p'
        elif 'hd 720p' in aux: calidad = 'HD 720p'
        elif 'hdtv' in aux: calidad = 'HDTV'
        elif 'hd' in aux: calidad = 'HD'
        else: calidad = ''

        data2 = httptools.downloadpage(host+url).data
        iframe_src = scrapertools.find_single_match(data2, '<iframe src="[^"]+')
        if not iframe_src: continue

        itemlist.append(Item(channel = item.channel, action = 'play',
                             title = '', url = iframe_src,
                             language = language, quality = calidad, quality_num = puntuar_calidad(calidad)
                       ))


    if len(itemlist) > 0: itemlist = servertools.get_servers_itemlist(itemlist)

    return itemlist



def search(item, texto):
    logger.info("texto: %s" % texto)
    itemlist = []

    try:
        post = {"n":texto}
        data = httptools.downloadpage(host + 'wp-content/themes/wikiSeries/searchajaxresponse.php', post=urllib.urlencode(post)).data
        # ~ logger.debug(data)

        matches = re.compile('<a href="([^"]+)">(.*?)</a>', re.DOTALL).findall(data)
        for url, data_show in matches:
            title = scrapertools.find_single_match(data_show, '<span class="titleinst">([^<]*)</span>')
            year = scrapertools.find_single_match(data_show, '<span class="titleinst year">([^<]*)</span>')
            thumb = scrapertools.find_single_match(data_show, 'src="([^"]+)"')

            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, 
                                        contentType='tvshow', contentSerieName=title, infoLabels={'year': year} ))

        tmdb.set_infoLabels(itemlist)
        return itemlist

    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
