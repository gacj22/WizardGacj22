# -*- coding: utf-8 -*-

import os, re

from platformcode import config, logger
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


perpage = 20 # preferiblemente un múltiplo de los elementos que salen en la web (80) para que la subpaginación interna no se descompense

CLONES = [
    ['descargas2020', 'http://descargas2020.org/', 'movie, tvshow', 'descargas2020.png'],
    # ~ ['tumejortorrent', 'http://tumejortorrent.site/', 'movie, tvshow', 'tumejortorrent.jpg'],
    # ~ ['tumejortorrent', 'https://tumejortorrent.org/', 'movie, tvshow', 'tumejortorrent.jpg'],
    # ~ ['torrentrapid', 'https://torrentrapid.org/', 'movie, tvshow', 'torrentrapid.png'],
    ['torrentlocura', 'http://torrentlocura.cc/', 'movie, tvshow', 'torrentlocura.png'],
    ['pctnew', 'https://pctnew.org/', 'movie, tvshow', 'pctnew.jpg'],
    ['planetatorrent', 'http://planetatorrent.com/', 'movie, tvshow', 'planetatorrent.png'],
    ['mispelisyseries', 'http://mispelisyseries.com/', 'movie', 'mispelisyseries.png'],
    ['tvsinpagar', 'http://tvsinpagar.com/', 'tvshow', 'tvsinpagar.png']
]

# Notas:

# - Para una misma peli/serie no siempre hay uno sólo enlace, pueden ser múltiples. La videoteca de momento no está preparada para acumular
#   múltiples enlaces de un mismo canal, así que solamente se guardará el enlace del último agregado.

# - La búsqueda global se hace en uno sólo de los clones (de momento el 1ro, quizás configurable más adelante).
#   Pero se puede acceder a cualquiera de los clones y buscar específicamente en él.

# - Las entradas en la web parecen manuales y pueden ser un poco dispares, lo cual dificulta interpretar título, idioma, calidades, etc.


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

    for clone in CLONES:
        if 'movie' in clone[2]:
            thumb = os.path.join(config.get_runtime_path(), 'resources', 'media', 'channels', 'thumb', clone[3])
            itemlist.append(item.clone( title = clone[0], action = 'mainlist_pelis_clon', url = clone[1], thumbnail = thumb ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie' ))

    return itemlist

def mainlist_pelis_clon(item):
    logger.info()
    itemlist = []
    item.category += '~' + item.title

    enlaces = [
        ['Películas en Castellano', 'peliculas/'],
        ['Películas en Latino', 'peliculas-latino/'],
        ['Películas en VO', 'peliculas-vo/'],
        ['Estrenos de cine', 'estrenos-de-cine/'],
        ['Películas en HD', 'peliculas-hd/'],
        ['Películas en X264', 'peliculas-x264-mkv/'],
        ['Películas en 3D', 'peliculas-3d/']
    ]
        # ~ ['Otras películas', 'otras-peliculas/'],
        # ~ ['FullBluRay 1080p', 'peliculas-hd/fullbluray-1080p/'],
        # ~ ['BluRay 1080p', 'peliculas-hd/bluray-1080p/'],
        # ~ ['BDremux 1080p', 'peliculas-hd/bdremux-1080p/'],
        # ~ ['MicroHD 1080p', 'peliculas-hd/microhd-1080p/'],
        # ~ ['4K UltraHD', 'peliculas-hd/4kultrahd/'],
        # ~ ['4K UHDremux', 'peliculas-hd/4k-uhdremux/'],
        # ~ ['4K UHDmicro', 'peliculas-hd/4k-uhdmicro/'],
        # ~ ['4K UHDrip', 'peliculas-hd/4k-uhdrip/'],
        # ~ ['4K Webrip', 'peliculas-hd/4k-webrip/'],
        # ~ ['Full UHD4K', 'peliculas-hd/full-uhd4k/'],
        # ~ ['Documentales', 'varios/'], # algunos documentales, pero la mayoría de enlaces son pdfs de revistas, etc.
    # Excepciones: planetatorrent no tiene x264-mkv. torrentrapid no tiene buscar

    for enlace in enlaces:
        if item.title == 'planetatorrent' and 'x264' in enlace[1]: continue
        itemlist.append(item.clone( title = enlace[0], action = 'list_all', url = item.url + enlace[1], search_type = 'movie' ))

    if item.title != 'torrentrapid':
        itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', url = item.url, search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    for clone in CLONES:
        if 'tvshow' in clone[2]:
            thumb = os.path.join(config.get_runtime_path(), 'resources', 'media', 'channels', 'thumb', clone[3])
            itemlist.append(item.clone( title = clone[0], action = 'mainlist_series_clon', url = clone[1], thumbnail = thumb ))
        
    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow' ))

    return itemlist

def mainlist_series_clon(item):
    logger.info()
    itemlist = []
    item.category += '~' + item.title

    enlaces = [
        ['Series', 'series/'],
        ['Series HD', 'series-hd/'],
        ['Series VO', 'series-vo/']
    ]
    # Excepciones: torrentrapid no tiene buscar

    for enlace in enlaces:
        itemlist.append(item.clone( title = enlace[0], action = 'list_all', url = item.url + enlace[1], search_type = 'tvshow' ))

    if item.title != 'torrentrapid':
        itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', url = item.url, search_type = 'tvshow' ))

    return itemlist




def limpiar_titulo(title, quitar_sufijo=''):
    prefijos = ['Ver en linea ', 'Ver online ', 'Descarga Gratis ', 'Descarga Serie HD ',  
                'Descargar Estreno ', 'Descargar Pelicula ', 'Descargar torrent ']
    for prefijo in prefijos:
        if title.startswith(prefijo): title = title[len(prefijo):]
        
    if title.endswith(' en HD'): title = title.replace(' en HD', '')

    m = re.match(r"^Descargar (.*?) torrent gratis$", title)
    if m: title = m.group(1)
    
    m = re.match(r"^Descargar (.*?)gratis$", title)
    if m: title = m.group(1)

    m = re.match(r"^Descargar (.*?) torrent$", title)
    if m: title = m.group(1)
    
    m = re.match(r"^Pelicula en latino (.*?) gratis$", title)
    if m: title = m.group(1)

    if quitar_sufijo != '':
        title = re.sub(quitar_sufijo+'[A-Za-z .]*$', '', title)

    return title.strip()


def list_all(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0

    quitar_sufijo = ''
    if '-3d/' in item.url: quitar_sufijo = ' 3D'

    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)
    
    patron = '<li>\s*<a href="([^"]+)" title="([^"]+)">\s*<img src="([^"]+)"[^>]+>'
    patron += '\s*<h2[^>]*>[^<]+</h2>\s*<span>([^<]+)</span>'
    
    matches = re.compile(patron, re.DOTALL).findall(data)
    num_matches = len(matches)

    for url, title, thumb, quality in matches[item.page * perpage:]:
        # ~ logger.debug('%s %s %s %s' % (url, title, thumb, quality))
        if '/varios/' in item.url and quality in ['ISO','DVD-Screener']: continue # descartar descargas de pc, revistas pdf

        title = limpiar_titulo(title, quitar_sufijo)
        titulo = title
        if item.search_type == 'tvshow':
            m = re.match(r"^(.*?) - (Temporada \d+) Capitulo \d*", title)
            if not m:
                m = re.match(r"^(.*?) - (Temporada \d+)", title)
            if m: 
                title = m.group(1)
                titulo = '%s [%s]' % (title, m.group(2))

        if item.search_type == 'tvshow':
            itemlist.append(item.clone( action='episodios', url=url, title=titulo, thumbnail=thumb, 
                                        qualities=quality, 
                                        contentType='tvshow', contentSerieName=title, infoLabels={'year': '-'} ))
        else:
            itemlist.append(item.clone( action='findvideos', url=url, title=titulo, thumbnail=thumb, 
                                        qualities=quality, 
                                        contentType='movie', contentTitle=title, infoLabels={'year': '-'} ))
        
        if len(itemlist) >= perpage: break


    tmdb.set_infoLabels(itemlist)

    # Subpaginación interna y/o paginación de la web
    buscar_next = True
    if num_matches > perpage: # subpaginación interna dentro de la página si hay demasiados items
        hasta = (item.page * perpage) + perpage
        if hasta < num_matches:
            itemlist.append(item.clone( title='>> Página siguiente', page=item.page + 1 ))
            buscar_next = False

    if buscar_next:
        next_page_link = scrapertools.find_single_match(data, '<li><a href="([^"]+)">Next</a>')
        if next_page_link:
            itemlist.append(item.clone( title='>> Página siguiente', url=next_page_link, page=0 ))

    return itemlist



# Devuelve los episodios de todas las temporadas para scrap en trackingtools
def tracking_all_episodes(item):
    itemlist = episodios(item)
    while itemlist[-1].title == '>> Página siguiente':
        itemlist = itemlist[:-1] + episodios(itemlist[-1])
    return itemlist


def extrae_show_s_e(title):
    show = ''; season = ''; episode = ''

    # ~ Blue Bloods  Temporada 9 Capitulo 9
    datos = scrapertools.find_single_match(title, '(.*?) Temporada (\d+) Capitulo (\d+)')
    if datos: 
        show, season, episode = datos
    else:
        # ~ Vikings - Temporada 4 [HDTV 720p][Cap.410][V.O. Subt. Castellano]
        datos = scrapertools.find_single_match(title, '(.*?) - Temporada (\d+).*?\[Cap\.(\d+)\]')
        if datos:
            show, season, episode = datos
            if episode.startswith(season): episode = episode[len(season):]
        else:
            # ~ This Is Us  Temporada[ 3 ]Capitulo[ 8 ]
            datos = scrapertools.find_single_match(title, '(.*?) Temporada[^0-9]*(\d+)[^C]*Capitulo[^0-9]*(\d+)')
            if datos:
                show, season, episode = datos

    return show.strip(), season, episode


def episodios(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)

    ul = scrapertools.find_single_match(data, '<ul class="buscar-list">(.*?)</ul>')
    matches = re.compile('<li[^>]*>(.*?)</li>', re.DOTALL).findall(ul)
    for article in matches:

        url = scrapertools.find_single_match(article, ' href="([^"]+)"')
        thumb = scrapertools.find_single_match(article, ' src="([^"]+)"')
        title = scrapertools.find_single_match(article, '<strong[^>]*>(.*?)</strong>')
        if title == '':
            title = scrapertools.find_single_match(article, '<h2[^>]*>(.*?)</h2>')
        title = scrapertools.htmlclean(title)
        # ~ spans = scrapertools.find_multiple_matches(article, '<span[^>]*>([^<]+)</span>')
        # ~ logger.debug(spans) #0:idioma, 1:calidad, 2:fecha, 3:tamaño

        show, season, episode = extrae_show_s_e(title)
        if show == '' or season == '' or episode == '': 
            if title != '': logger.debug('Serie/Temporada/Episodio no detectados! %s' % title)
            # ~ else: logger.debug(article)
            continue
        titulo = '%sx%s %s' % (season, episode, show)

        itemlist.append(item.clone( action='findvideos', url=url, title=titulo, thumbnail=thumb, 
                                    contentType='episode', contentSeason=season, contentEpisodeNumber=episode ))

    tmdb.set_infoLabels(itemlist)

    next_page_link = scrapertools.find_single_match(data, '<li><a href="([^"]+)">Next</a>')
    if next_page_link:
        itemlist.append(item.clone( title='>> Página siguiente', url=next_page_link ))
    
    return itemlist



def extrae_idioma(txt):
    if 'Latino' in txt: return 'Lat'
    elif 'Castellano' in txt or txt.startswith('Espa'): return 'Esp'
    elif 'Subtitulado Espa' in txt: return 'VOSE'
    elif 'Subtitulado' in txt: return 'VOSE' #'VOS'
    else: return 'VO'


def findvideos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)
    
    # Enlace torrent
    calidad = ''; idioma = ''
    h1 = scrapertools.find_single_match(data, '<h1[^>]*>(.*?)</h1>')
    h1 = scrapertools.htmlclean(h1.replace('\n', ''))
    datos = scrapertools.find_multiple_matches(h1, '\[([^\]]+)\]')
    if datos:
        calidad = datos[0]
        if len(datos) > 1: idioma = extrae_idioma(datos[1])
        if idioma == 'VO' and len(datos) > 2: idioma = extrae_idioma(datos[2]) # a veces no es el segundo []
        if idioma == 'VO' and len(datos) > 3: idioma = extrae_idioma(datos[3]) # a veces no es el tercero []
    tamano = scrapertools.find_single_match(data, '<strong>Size:</strong>([^<]+)</span>').strip()
    url = scrapertools.find_single_match(data, 'window.location.href\s*=\s*"([^"]+)')
    if url.startswith('//'): url = 'http:' + url

    itemlist.append(Item(channel = item.channel, action = 'play',
                         title = '', url = url, server = 'torrent',
                         language = idioma, quality = calidad, other = tamano
                   ))

    # Enlaces streaming
    patron = '<div class="box2">([^<]+)</div>\s*<div class="box3">([^<]+)</div>\s*<div class="box4">([^<]+)</div>'
    patron += '\s*<div class="box5"><a href=\'([^\']+)[^>]+>([^<]+)'
    
    matches = re.compile(patron, re.DOTALL).findall(data)
    for servidor, idioma, calidad, url, tipo in matches:
        # ~ logger.debug('%s %s %s %s %s' % (tipo, servidor, url, idioma, calidad))
        if 'descargar' in tipo.lower(): continue  # Descartar descargas directas
        
        itemlist.append(Item(channel = item.channel, action = 'play',
                             title = '', url = url,
                             language = extrae_idioma(idioma), quality = calidad
                       ))

    itemlist = servertools.get_servers_itemlist(itemlist)
    
    return itemlist



def busqueda(item):
    logger.info(item)
    itemlist = []

    post = "q=%s" % item.busca_texto
    if item.busca_pagina > 0: post += "&pg=%d" % item.busca_pagina
    data = httptools.downloadpage(item.url, post=post).data
    # ~ logger.debug(data)
    
    ul = scrapertools.find_single_match(data, '<ul class="buscar-list">(.*?)</ul>')
    matches = re.compile('<li[^>]*>(.*?)</li>', re.DOTALL).findall(ul)
    for article in matches:
        # ~ logger.debug(article)

        url = scrapertools.find_single_match(article, ' href="([^"]+)"')
        thumb = scrapertools.find_single_match(article, ' src="([^"]+)"')
        if '/juego/' in url: continue # descartar videojuegos

        is_tvshow = '/serie' in url or '/descargar-serie' in url
        if (item.search_type == 'tvshow' and not is_tvshow) or (item.search_type == 'movie' and is_tvshow): continue
        if url in [it.url for it in itemlist]: continue # descartar urls duplicadas

        title = scrapertools.find_single_match(article, '<strong[^>]*>(.*?)</strong>')
        if title == '': title = scrapertools.find_single_match(article, '<h2[^>]*>(.*?)</h2>')
        title = scrapertools.htmlclean(title).replace('\n', '')
        # ~ logger.debug(title)
        if title == '':
            # ~ logger.debug('Título no encontrado. %s' % article)
            continue
        if re.match('.*?temporada \d+ completa', title, flags=re.IGNORECASE): continue # descartar enlaces a temporadas completas
        
        idioma = ''; calidad = ''
        datos = scrapertools.find_multiple_matches(title, '\[([^\]]+)\]')
        if datos:
            # ~ logger.debug(datos)
            calidad = datos[0]
            if len(datos) > 1: idioma = extrae_idioma(datos[1])
            if idioma == 'VO' and len(datos) > 2: idioma = extrae_idioma(datos[2]) # a veces no es el segundo []
            if idioma == 'VO' and len(datos) > 3: idioma = extrae_idioma(datos[3]) # a veces no es el tercero []
            title = re.sub('\[.*$', '', title)
        else:
            datos = scrapertools.find_multiple_matches(article, '<span[^>]*>([^<]+)</span>')
            if datos:
                # ~ logger.debug(datos)
                idioma = extrae_idioma(datos[0])
                calidad = datos[1].replace('[','').replace(']','').strip()

        if is_tvshow: title = re.sub('Temporada \d+.*$', '', title).strip()
        
        if is_tvshow:
            sufijo = '' if item.search_type != 'all' else 'tvshow'

            itemlist.append(item.clone( action='episodios', url=url, title=title, thumbnail=thumb, 
                                        languages=idioma, qualities=calidad, fmt_sufijo=sufijo,
                                        contentType='tvshow', contentSerieName=title, infoLabels={'year': '-'} ))
        else:
            sufijo = '' if item.search_type != 'all' else 'movie'

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, 
                                        languages=idioma, qualities=calidad, fmt_sufijo=sufijo,
                                        contentType='movie', contentTitle=title, infoLabels={'year': '-'} ))
            

    tmdb.set_infoLabels(itemlist)
    
    next_page_link = scrapertools.find_single_match(data, '<a href="javascript:;" onClick="_pgSUBMIT\(\'(\d+)\'\);">Next')
    if next_page_link:
        itemlist.append(item.clone( title='>> Página siguiente', action='busqueda', busca_pagina=int(next_page_link) ))

    return itemlist

def search(item, texto):
    logger.info("texto: %s" % texto)
    try:
        if item.url == '': item.url = CLONES[0][1]
        item.url += 'buscar/'
        item.busca_texto = texto.replace(" ", "+")
        item.busca_pagina = 0
        return busqueda(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
