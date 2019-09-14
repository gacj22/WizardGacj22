# -*- coding: utf-8 -*-

import re, urllib

from platformcode import config, logger
from core.item import Item
from core import httptools, scrapertools, jsontools, servertools, tmdb

host = 'https://www.cliver.to/'


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Películas', action = 'mainlist_pelis' ))
    itemlist.append(item.clone( title = 'Series', action = 'mainlist_series' ))

    return itemlist

def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Últimas películas', action = 'list_all', url = host + 'peliculas/', 
                                search_type = 'movie', tipo = 'index', pagina = 0 ))

    itemlist.append(item.clone( title = 'Películas de Estreno', action = 'list_all', url = host + 'peliculas/estrenos/', 
                                search_type = 'movie', tipo = 'estrenos', pagina = 0 ))

    itemlist.append(item.clone( title = 'Películas más Vistas', action = 'list_all', url = host + 'peliculas/mas-vistas/', 
                                search_type = 'movie', tipo = 'mas-vistas', pagina = 0 ))

    itemlist.append(item.clone( title = 'Películas Tendencia', action = 'list_all', url = host + 'peliculas/tendencias/', 
                                search_type = 'movie', tipo = 'peliculas-tendencias', pagina = 0 ))
    
    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anyos', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie' ))

    return itemlist

def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Últimas series', action = 'list_all', url = host + 'series/', 
                                search_type = 'tvshow', tipo = 'indexSeries', pagina = 0 ))

    itemlist.append(item.clone( title = 'Series más Vistas', action = 'list_all', url = host + 'series/mas-vistas/', 
                                search_type = 'tvshow', tipo = 'mas-vistas-series', pagina = 0 ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Por cadena (network)', action = 'networks', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anyos', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimos episodios', action = 'list_episodes', url = host + 'series/nuevos-capitulos/', 
                                search_type = 'tvshow', tipo = 'nuevos-capitulos', pagina = 0 ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []
    
    url = host if item.search_type == 'movie' else host + 'series/'
    data = httptools.downloadpage(url).data
    
    bloque = scrapertools.find_single_match(data, '<div class="generos">(.*?)</ul>')
    
    matches = scrapertools.find_multiple_matches(bloque, '<a href="([^"]+)">\s*<span class="cat">([^<]+)')
    for url, title in matches:
        adicional = scrapertools.find_single_match(url, '/genero/([^/]+)')
        tipo = 'genero' if item.search_type == 'movie' else 'generosSeries'
        itemlist.append(item.clone( action="list_all", title=title, url=url, tipo=tipo, adicional=adicional, pagina=0 ))

    return sorted(itemlist, key=lambda it: it.title)

def anyos(item):
    logger.info()
    itemlist = []
    
    url = host if item.search_type == 'movie' else host + 'series/'
    data = httptools.downloadpage(url).data
    
    bloque = scrapertools.find_single_match(data, '<div class="anios">(.*?)</ul>')
    
    matches = scrapertools.find_multiple_matches(bloque, '<a href="([^"]+)">([^<]+)')
    for url, title in matches:
        adicional = scrapertools.find_single_match(url, '/anio/([^/]+)')
        tipo = 'anio' if item.search_type == 'movie' else 'anioSeries'
        itemlist.append(item.clone( action="list_all", title=title, url=url, tipo=tipo, adicional=adicional, pagina=0 ))

    return itemlist

def networks(item):
    logger.info()
    itemlist = []
    
    data = httptools.downloadpage(host + 'series/').data
    
    bloque = scrapertools.find_single_match(data, '<div class="networks">(.*?)</ul>')
    
    matches = scrapertools.find_multiple_matches(bloque, '<a href="([^"]+)" class="[^"]*" title="([^"]+)')
    for url, title in matches:
        adicional = scrapertools.find_single_match(url, '/network/([^/]+)')
        itemlist.append(item.clone( action="list_all", title=title, url=url, tipo='networkSeries', adicional=adicional, pagina=0 ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []
    if not item.pagina: item.pagina = 0

    if item.pagina == 0 and item.tipo == 'buscador':
        data = httptools.downloadpage(item.url, headers={'Cookie': 'tipo_contenido=peliculas'}).data
    else:
        post = {'tipo': item.tipo, 'pagina': item.pagina}
        if item.adicional: post['adicional'] = item.adicional
        data = httptools.downloadpage(host+'frm/cargar-mas.php', post=urllib.urlencode(post)).data
    # ~ logger.debug(data)

    matches = re.compile('<article class="contenido-p">(.*?)</article>', re.DOTALL).findall(data)
    for article in matches:

        url = scrapertools.find_single_match(article, ' href="([^"]+)"')
        thumb = scrapertools.find_single_match(article, ' src="([^"]+)"')
        title = scrapertools.find_single_match(article, '<h2>(.*?)</h2>').strip()
        year = scrapertools.find_single_match(article, '<span>(\d{4})')
        if not year: year = '-'

        if item.search_type == 'movie':
            langs = scrapertools.find_multiple_matches(article, '<div class="([^"]+)"></div>')
            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, 
                                        id_pelicula = scrapertools.find_single_match(thumb, '/(\d+)_min'),
                                        contentType='movie', contentTitle=title, infoLabels={'year': year},
                                        languages = ', '.join(langs) ))
        else:
            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, 
                                        contentType='tvshow', contentSerieName=title, infoLabels={'year': year} ))
            
    tmdb.set_infoLabels(itemlist)

    num = 12 if item.tipo.startswith('index') else 18
    if len(matches) >= num:
        itemlist.append(item.clone( title='>> Página siguiente', pagina = item.pagina + 1, action='list_all' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    
    patron ='<div class="menu-item" id="temporada(\d+)">'
    matches = re.compile(patron, re.DOTALL).findall(data)
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
    itemlist=[]
    color_lang = config.get_setting('list_languages_color', default='red')

    data = httptools.downloadpage(item.url).data

    matches = re.compile('<div class="mic">(.*?)<i class="fa fa-play">', re.DOTALL).findall(data)
    for article in matches:
        thumb = scrapertools.find_single_match(article, ' src="([^"]+)"')
        plot = scrapertools.find_single_match(article, '<p>(.*?)</p>').strip()

        season = scrapertools.find_single_match(article, 'data-numtemp="([^"]+)')
        episode = scrapertools.find_single_match(article, 'data-numcap="([^"]+)')
        title = scrapertools.find_single_match(article, 'data-titulo="([^"]+)')

        if item.contentSeason and item.contentSeason != int(season):
            continue

        langs = []
        for opc in ['data-url-es', 'data-url-es-la', 'data-url-vose', 'data-url-en']:
            url = scrapertools.find_single_match(article, '%s="([^"]+)' % opc)
            if url: langs.append(opc.replace('data-url-', '').replace('es-la', 'lat'))

        if langs: title += ' [COLOR %s][%s][/COLOR]' % (color_lang, ', '.join(langs))
        
        itemlist.append(item.clone( action='findvideos', title = title, thumbnail=thumb, plot = plot,
                                    contentType = 'episode', contentSeason = season, contentEpisodeNumber = episode ))

    tmdb.set_infoLabels(itemlist)

    return itemlist

def list_episodes(item):
    logger.info()
    itemlist = []
    if not item.pagina: item.pagina = 0
    color_lang = config.get_setting('list_languages_color', default='red')

    post = {'tipo': item.tipo, 'pagina': item.pagina}
    data = httptools.downloadpage(host+'frm/cargar-mas.php', post=urllib.urlencode(post)).data

    matches = re.compile('<article class="contenido-p">(.*?)</article>', re.DOTALL).findall(data)
    for article in matches:

        url = scrapertools.find_single_match(article, ' href="([^"]+)"')
        thumb = scrapertools.find_single_match(article, ' src="([^"]+)"')
        show = scrapertools.find_single_match(article, '<h2>(.*?)</h2>').strip()
        title = scrapertools.find_single_match(article, '<span>(.*?)</span>')
        langs = scrapertools.find_multiple_matches(article, '<div class="([^"]+)"></div>')
        
        s_e = scrapertools.find_single_match(url, '/(\d+)/(\d+)/')
        if not s_e: continue
        
        titulo = '%s - %s' % (show, title)
        if langs: titulo += ' [COLOR %s][%s][/COLOR]' % (color_lang, ', '.join(langs))

        itemlist.append(item.clone( action='findvideos', url=url, title=titulo, thumbnail=thumb, 
                                    contentType='episode', contentSerieName=show, contentSeason = s_e[0], contentEpisodeNumber = s_e[1] ))
            
    tmdb.set_infoLabels(itemlist)

    if len(matches) >= 18:
        itemlist.append(item.clone( title='>> Página siguiente', pagina = item.pagina + 1, action='list_episodes' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    
    IDIOMAS = {'es_la': 'Lat', 'es': 'Esp', 'vose': 'VOSE', 'en': 'VO'}

    if item.contentType == 'movie':
        if not item.id_pelicula:
            data = httptools.downloadpage(item.url).data
            item.id_pelicula = scrapertools.find_single_match(data, 'Idpelicula\s*=\s*"([^"]+)')

        data = httptools.downloadpage(host + 'frm/obtener-enlaces-pelicula.php', post=urllib.urlencode({'pelicula': item.id_pelicula})).data
        enlaces = jsontools.load(data)
        for lang in enlaces:
            for it in enlaces[lang]:
                servidor = 'directo' if it['reproductor_nombre'] == 'SuperVideo' else it['reproductor_nombre'].lower()
                itemlist.append(Item( channel = item.channel, action = 'play', server = servidor,
                                      title = '', url = 'https://directvideo.stream/getFile.php?hash='+it['token'],
                                      language = IDIOMAS.get(lang, lang), other = it['reproductor_nombre'] if servidor == 'directo' else ''
                               ))

    else:
        data = httptools.downloadpage(item.url).data
        data = scrapertools.find_single_match(data, 'data-numcap="%s" data-numtemp="%s"(.*?)>' % (item.contentEpisodeNumber, item.contentSeason))

        for opc in ['data-url-es', 'data-url-es-la', 'data-url-vose', 'data-url-en']:
            url = scrapertools.find_single_match(data, '%s="([^"]+)' % opc)
            if url:
                servidor = servertools.get_server_from_url(url)
                if not servidor or servidor == 'directo': continue
                lang = opc.replace('data-url-', '').replace('-', '_')
                itemlist.append(Item( channel = item.channel, action = 'play', server = servidor,
                                      title = '', url = url,
                                      language = IDIOMAS.get(lang, lang)
                               ))

    return itemlist

def play(item):
    logger.info()
    itemlist = []

    if item.url.startswith('https://directvideo.stream/getFile.php'):
        url = item.url.split('?')[0]
        post = item.url.split('?')[1]
        data = httptools.downloadpage(url, post=post).data.replace('\\/', '/')
        url = scrapertools.find_single_match(data, '"url":"([^"]+)').replace(' ', '%20')
    else:
        url = item.url

    if url:
        itemlist.append(item.clone(url=url))
            
    return itemlist


def search(item, texto):
    logger.info()
    try:
        tipo = 'buscador' if item.search_type == 'movie' else 'buscadorSeries'
        return list_all(item.clone( pagina=0, tipo=tipo, adicional=texto.replace(" ", "+"), url=host+'buscar/?txt='+texto.replace(" ", "+") ))
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
