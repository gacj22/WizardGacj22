# -*- coding: utf-8 -*-

import re, urllib

from platformcode import config, logger
from core.item import Item
from core import httptools, scrapertools, tmdb

host = 'https://www.pelisplay.tv/'


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

    itemlist.append(item.clone( title = 'Lista de películas', action = 'list_pelis', url = host + 'ver-peliculas', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Películas de Estreno', action = 'list_pelis', url = host + 'ver-peliculas/estrenos', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Películas de Netflix', action = 'list_pelis', url = host + 'ver-peliculas/netflix', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Películas más Vistas', action = 'list_pelis', url = host + 'ver-peliculas?filtro=visitas', search_type = 'movie' ))
    
    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Lista de series', action = 'list_series', url = host + 'series', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Series de Estreno', action = 'list_series', url = host + 'series/estrenos', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Series de Netflix', action = 'list_series', url = host + 'series/netflix', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Series más Vistas', action = 'list_series', url = host + 'series?filtro=visitas', search_type = 'tvshow' ))
    
    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow' ))

    return itemlist



def generos(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie': url = host + 'ver-peliculas'
    else: url = host + 'series'
    data = httptools.downloadpage(url).data
    
    patron = '<a href="([^"]+)" class="category">.*?<div class="category-name">([^<]+)</div>\s*<div class="category-description">(\d+)'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for url, title, cantidad in matches:
        if '/estrenos' in url or '/netflix' in url: continue
        if item.search_type == 'movie':
            itemlist.append(item.clone( action="list_pelis", title='%s (%s)' % (title, cantidad), url=url ))
        else:
            itemlist.append(item.clone( action="list_series", title='%s (%s)' % (title, cantidad), url=url ))

    # ~ return itemlist # orden por cantidad
    return sorted(itemlist, key=lambda it: it.title) # orden alfabético


def list_pelis(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    matches = re.compile('<figure>(.*?)</figure>', re.DOTALL).findall(data)
    for article in matches:

        thumb = scrapertools.find_single_match(article, ' src="([^"]+)"')
        if thumb.startswith('/'): thumb = host[:-1] + thumb
        title = scrapertools.find_single_match(article, '<div class="Title">(.*?)</div>').strip()
        url = scrapertools.find_single_match(article, ' href="([^"]+)"')
        plot = scrapertools.find_single_match(article, '<div class="Description">\s*<div>(.*?)</div>').strip()

        year = scrapertools.find_single_match(title, '\((\d{4})\)')
        if year:
            title = title.replace('(%s)' % year, '').strip()
        else:
            year = '-'

        itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, 
                                    contentType='movie', contentTitle=title, infoLabels={'year': year, 'plot': plot} ))

    tmdb.set_infoLabels(itemlist)

    next_page_link = scrapertools.find_single_match(data, '<a href="([^"]+)" rel="next"')
    if next_page_link:
        itemlist.append(item.clone( title='>> Página siguiente', url=next_page_link, action='list_pelis' ))

    return itemlist


def list_series(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    matches = re.compile('<figure>(.*?)</figure>', re.DOTALL).findall(data)
    for article in matches:

        thumb = scrapertools.find_single_match(article, 'img src="([^"]+)"')
        if thumb.startswith('/'): thumb = host[:-1] + thumb
        title = scrapertools.find_single_match(article, '<h2>(.*?)</h2>').strip()
        url = scrapertools.find_single_match(article, ' href="([^"]+)"')
        plot = scrapertools.find_single_match(article, '<span class="lg margin-bottom">(.*?)</span>').strip()
        year = scrapertools.find_single_match(article, 'Año: (\d{4})')
        if not year: year = '-'

        itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, 
                                    contentType='tvshow', contentSerieName=title, infoLabels={'year': year, 'plot': plot} ))

    tmdb.set_infoLabels(itemlist)

    next_page_link = scrapertools.find_single_match(data, '<a href="([^"]+)" rel="next"')
    if next_page_link:
        itemlist.append(item.clone( title='>> Página siguiente', url=next_page_link, action='list_series' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    
    patron =' class="abrir_temporada" href="([^"]+)">\s*<h4 class="name-movie"><strong>Temporada (\d+)'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for url, numtempo in matches:
        itemlist.append(item.clone( action='episodios', title='Temporada %s' % numtempo, url = url,
                                    contentType='season', contentSeason=numtempo ))
        
    tmdb.set_infoLabels(itemlist)

    return itemlist

def episodios(item):
    logger.info()
    itemlist=[]

    data = httptools.downloadpage(item.url).data

    matches = re.compile('<figure>(.*?)</figure>', re.DOTALL).findall(data)
    for article in matches:
        url = scrapertools.find_single_match(article, ' href="([^"]+)"')
        thumb = scrapertools.find_single_match(article, ' src="([^"]+)"')
        if thumb.startswith('/'): thumb = host[:-1] + thumb
        title = scrapertools.find_single_match(article, '<div class="Title">(.*?)</div>').strip()
        plot = scrapertools.find_single_match(article, '<div class="Description">\s*<div>(.*?)</div>').strip()
        
        s_e = scrapertools.find_single_match(url, '/temporada-(\d+)/episodio-(\d+)')
        if not s_e: continue
        titulo = '%sx%s %s' % (s_e[0], s_e[1], title)
        
        itemlist.append(item.clone( action='findvideos', title = titulo, url = url, thumbnail=thumb, plot = plot,
                                    contentType = 'episode', contentSeason = s_e[0], contentEpisodeNumber = s_e[1] ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


# Asignar un numérico según las calidades del canal, para poder ordenar por este valor
def puntuar_calidad(txt):
    if txt == 'Hd 1080p': txt = 'Hd1080'
    if txt == 'Hd 720p': txt = 'Hd720'
    orden = ['Screener', 'Sd', 'Rip', 'Dvd rip', 'Hd720', 'Hd1080']
    if txt not in orden: return 0
    else: return orden.index(txt) + 1

def findvideos(item):
    logger.info()
    itemlist = []
    
    IDIOMAS = {'Latino': 'Lat', 'Castellano': 'Esp', 'Subtitulado': 'VOSE', 'Original': 'VO'}

    data = httptools.downloadpage(item.url).data

    data = scrapertools.find_single_match(data, '<div id="lista_online"(.*?)</table>')
    token = scrapertools.find_single_match(data, 'data-token="([^"]+)')

    matches = re.compile('<tr(.*?)</tr>', re.DOTALL).findall(data)
    for enlace in matches:
        if 'data-lang="Publicidad"' in enlace: continue
        tds = scrapertools.find_multiple_matches(enlace, '<td[^>]*>(.*?)</td>')
        if len(tds) != 6: continue
        if 'data-player=' not in tds[0]: continue

        calidad = tds[1].capitalize()
        lang = tds[2]
        agregado = tds[4]

        data_player = scrapertools.find_single_match(tds[0], 'data-player="([^"]+)')
        post = {'data': data_player, 'tipo': 'videohost', '_token': token}
        url = 'https://www.pelisplay.tv/entradas/procesar_player?' + urllib.urlencode(post)

        servidor = scrapertools.find_single_match(tds[0], '>([^<]+)</div>').lower()
        if servidor in ['tazmania', 'zeus', 'tiburon', 'mega']:
            agregado += ', ' + servidor.capitalize()
            servidor = 'directo'

        itemlist.append(Item( channel = item.channel, action = 'play', server = servidor,
                              title = '', url = url,
                              language = IDIOMAS.get(lang, lang), quality = calidad, quality_num = puntuar_calidad(calidad), other = agregado
                       ))

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    url = item.url.split('?')[0]
    post = item.url.split('?')[1]
    data = httptools.downloadpage(url, post=post).data.replace('\\/', '/')

    url = scrapertools.find_single_match(data, '"data":"([^"]+)')

    if 'pelisplay.tv' in url:
        data = httptools.downloadpage(url).data
        # ~ logger.debug(data)
        if 'gkpluginsphp' in data:
            url = host + 'private/plugins/gkpluginsphp.php'
            post = {'link': scrapertools.find_single_match(data, 'link:"([^"]+)')}
            data = httptools.downloadpage(url, post=urllib.urlencode(post)).data.replace('\\/', '/')
            # ~ logger.debug(data)
            url = scrapertools.find_single_match(data, '"link":"([^"]+)')
            if url:
                itemlist.append(['mp4', url])

        elif 'start_jwplayer(JSON.parse(' in data:
            data = data.replace('\\/', '/')
            # ~ logger.debug(data)

            matches = scrapertools.find_multiple_matches(data, '"file"\s*:\s*"([^"]+)"\s*,\s*"label"\s*:\s*"([^"]*)"\s*,\s*"type"\s*:\s*"([^"]*)"')
            if matches:
                for url, lbl, typ in sorted(matches, key=lambda x: int(x[1][:-1]) if x[1].endswith('P') else x[1]):
                    itemlist.append(['%s [%s]' % (lbl, typ), url])

    elif url:
        itemlist.append(item.clone(url=url))
            
    return itemlist



def list_all(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    matches = re.compile('<figure>(.*?)</figure>', re.DOTALL).findall(data)
    for article in matches:
        tipo = 'tvshow' if 'span class="stick_serie"' in article else 'movie'
        sufijo = '' if item.search_type != 'all' else tipo

        thumb = scrapertools.find_single_match(article, ' src="([^"]+)"')
        if thumb.startswith('/'): thumb = host[:-1] + thumb
        title = scrapertools.find_single_match(article, '<div class="Title">(.*?)</div>').strip()
        url = scrapertools.find_single_match(article, ' href="([^"]+)"')
        plot = scrapertools.find_single_match(article, '<div class="Description">\s*<div>(.*?)</div>').strip()

        year = scrapertools.find_single_match(title, '\((\d{4})\)')
        if year:
            title = title.replace('(%s)' % year, '').strip()
        else:
            year = '-'

        if tipo == 'movie':
            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo, 
                                        contentType='movie', contentTitle=title, infoLabels={'year': year, 'plot': plot} ))
        else:
            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo, 
                                        contentType='tvshow', contentSerieName=title, infoLabels={'year': year, 'plot': plot} ))

    tmdb.set_infoLabels(itemlist)

    next_page_link = scrapertools.find_single_match(data, '<a href="([^"]+)" rel="next"')
    if next_page_link:
        itemlist.append(item.clone( title='>> Página siguiente', url=next_page_link, action='list_all' ))

    return itemlist


def search(item, texto):
    logger.info()
    itemlist = []
    try:
        if item.search_type == 'movie':
            item.url = host + 'ver-peliculas?buscar=' + texto.replace(" ", "+")
            return list_pelis(item)
        elif item.search_type == 'tvshow':
            item.url = host + 'series?buscar=' + texto.replace(" ", "+")
            return list_series(item)
        else:
            item.url = host + 'buscar?q=' + texto.replace(" ", "+")
            return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
