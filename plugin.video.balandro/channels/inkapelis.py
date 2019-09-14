# -*- coding: utf-8 -*-

import re

from platformcode import config, logger
from core.item import Item
from core import httptools, scrapertools, tmdb, servertools


host = 'https://www.inkapelis.tv/' # .to

IDIOMAS = {'Latino': 'Lat', 'Español': 'Esp', 'Castellano': 'Esp', 'Subtitulado': 'VOSE'}

perpage = 21 # preferiblemente un múltiplo de los elementos que salen en la web (6x7=42) para que la subpaginación interna no se descompense


def mainlist(item):
    return mainlist_pelis(item)

def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Últimas Películas', action = 'list_all', url = host ))

    itemlist.append(item.clone( title = 'Estrenos', action = 'list_all', url = host + 'genero/estrenos-online/' ))

    itemlist.append(item.clone( title = 'Actualizadas', action = 'list_all', url = host + 'genero/actualizadas/' ))

    itemlist.append(item.clone( title = 'Destacadas', action = 'list_all', url = host + 'genero/destacadas/' ))

    itemlist.append(item.clone( title = 'Cartelera', action = 'list_all', url = host + 'genero/cartelera/' ))

    itemlist.append(item.clone( title = 'Por idioma', action = 'idiomas' ))
    itemlist.append(item.clone( title = 'Por calidad', action = 'calidades' ))
    itemlist.append(item.clone( title = 'Por género', action = 'generos' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anyos' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(host).data

    patron = '<li class="cat-item cat-item-[^"]+"><a href="([^"]+)"[^>]*>([^<]+)<b>([^<]+)</b>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for url, title, cantidad in matches:
        if cantidad == '0': continue
        if '/actualizadas/' in url or '/cartelera/' in url or '/destacadas/' in url or '/estrenos-online/' in url: continue # pq ya están en el menú principal
        if '/proximos-estrenos/' in url: continue # pq no contienen enlaces

        itemlist.append(item.clone( action="list_all", title='%s (%s)' % (title.strip(), cantidad), url=url ))

    return sorted(itemlist, key=lambda it: it.title)


def anyos(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    anyo_now = int(datetime.today().year)
    for anyo in range(anyo_now, 1970, -1):
        url = host + 'year_relase/peliculas-' + str(anyo) if anyo == anyo_now else host + 'year_relase/' + str(anyo)
        itemlist.append(item.clone( title=str(anyo), url=url, action='list_all' ))

    return itemlist

def calidades(item):
    logger.info()
    itemlist = []

    opciones = ['Dvdrip', 'Bluray', 'Dvd', 'Fullhd', 'Hd', 'Sd', 'Ts', 'Cam']
    for opc in opciones:
        itemlist.append(item.clone( title=opc, url=host + '?s=&calidad=' + opc, action='list_all' ))

    return itemlist

def idiomas(item):
    logger.info()
    itemlist = []

    opciones = ['Castellano', 'Latino', 'Subtitulada']
    for opc in opciones:
        itemlist.append(item.clone( title=opc, url=host + '?s=&idioma=' + opc, action='list_all' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0

    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)

    if '/genero/' not in item.url and host+'?' not in item.url and '<div class="titulo-c">' in data: # descartar bloque de "Más vistas"
        data = data.split('<div class="titulo-c">')[1]
    
    matches = re.compile('<div class="col-mt-5 postsh">(.*?)</div>\s*</div>\s*</div>', re.DOTALL).findall(data)
    num_matches = len(matches)

    for article in matches[item.page * perpage:]:
        if 'class="proximamente"' in article: continue
        # ~ logger.debug(article)

        url, title = scrapertools.find_single_match(article, ' href="([^"]+)" title="([^"]+)"')
        thumb = scrapertools.find_single_match(article, ' src="([^"]+)"')
        quality = scrapertools.find_single_match(article, '<div class="poster-media-card ([^" ]+)')
        
        langs = []
        if '<div class="Castellano' in article: langs.append('Esp')
        if '<div class="Latino' in article: langs.append('Lat')
        if '<div class="Subtitulada' in article: langs.append('VOSE')
        
        # ~ if 'tmdb.org/' in thumb:
            # ~ filtro_list = {"poster_path": scrapertools.find_single_match(thumb, "w\w+(/\w+.....)")}
            # ~ infoLabels = {'filtro': filtro_list.items(), 'year': '-'}
        # ~ else:
            # ~ infoLabels = {'year': '-'}
        infoLabels = {'year': '-'} # parece que con filtro se detectan peor en tmdb !?

        itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, 
                                    qualities=quality, languages=', '.join(langs), 
                                    contentType='movie', contentTitle=title, infoLabels=infoLabels ))

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
        next_page_link = scrapertools.find_single_match(data, '<a href="([^"]+)"><i class="glyphicon glyphicon-chevron-right')
        if next_page_link:
            itemlist.append(item.clone( title='>> Página siguiente', url=next_page_link, page=0, action='list_all' ))

    return itemlist


# Asignar un numérico según las calidades del canal, para poder ordenar por este valor
def puntuar_calidad(txt):
    orden = ['Cam', 'HDCam', 'Ts Screener hq', 'DVDScreener', 'Dvd Rip', 'HDRip', 'HD Real 720p', 'Full HD 1080p']
    if txt not in orden: return 0
    else: return orden.index(txt) + 1

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

        # ~ itemlist.append(Item( channel = item.channel, action = 'play', server = servidor.lower(),
        itemlist.append(Item( channel = item.channel, action = 'play', server = '',
                              title = '', url = url,
                              language = IDIOMAS.get(language, language), quality = quality, quality_num = puntuar_calidad(quality)
                       ))

    # Enlaces en "embeds":
    matches_lang = re.compile('<a href="#embed\d+" data-toggle="tab">([^<]+)', re.DOTALL).findall(data)
    matches = re.compile('<div class="calishow">([^<]*)</div>\s*<div id="repro\d*"><iframe src="([^"]+)', re.DOTALL).findall(data)
    for ilang, (quality, url) in enumerate(matches):
        if ilang >= len(matches_lang): break
        language = matches_lang[ilang].strip()
        # ~ logger.info('%s %s %s' % (url, language, quality))
        quality = quality.replace('Calidad:', '').strip()
        
        itemlist.append(Item( channel = item.channel, action = 'play', server = '',
                              title = '', url = url,
                              language = IDIOMAS.get(language, language), quality = quality, quality_num = puntuar_calidad(quality)
                       ))

    itemlist = servertools.get_servers_itemlist(itemlist)

    # Dejar desconocidos como directos para resolverse en el play
    for it in itemlist:
        if it.server == 'desconocido' and it.url.startswith('https://play.inkapelis.tv/'):
            it.server = 'directo'

    return itemlist

def play(item):
    logger.info()
    itemlist = []

    if item.url.startswith('https://play.inkapelis.tv/'): 
        data = httptools.downloadpage(item.url, headers={'Referer': host}).data
        # ~ logger.debug(data)

        matches = scrapertools.find_multiple_matches(data, 'file:\s*"([^"]+)", type:\s*"([^"]+)", label:\s*"([^"]+)"')
        for url, lbl, res in matches:
            itemlist.append(['%s %sp' % (lbl, res), url])

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
