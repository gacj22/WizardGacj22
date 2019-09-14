# -*- coding: utf-8 -*-

import re, urllib

from platformcode import config, logger
from core.item import Item
from core import httptools, scrapertools, tmdb, servertools

host = 'https://www.cine-online.eu/'

perpage = 25 # preferiblemente un múltiplo de los elementos que salen en la web (5x10=50) para que la subpaginación interna no se descompense


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
    
    itemlist.append(item.clone( title = 'Últimas películas', action = 'list_all', url = host, search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Castellano', action = 'list_all', url = host + 'tag/castellano/', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Latino', action = 'list_all', url = host + 'tag/latino/', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'VOSE', action = 'list_all', url = host + 'tag/subtitulado/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por calidad', action = 'calidades', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []
    
    itemlist.append(item.clone( title = 'Últimas series', action = 'list_all', url = host + 'serie/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow' ))

    return itemlist



def generos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(host).data
    if item.search_type == 'movie':
        data = data.split('<div id="serieshome"')[0]
    else:
        data = data.split('<div id="serieshome"')[1]

    matches = re.compile('<li class="cat-item[^"]*"><a href="([^"]+)"(?: title="[^"]*"|)>([^<]+)</a>\s*<span>([^<]+)</span></li>', re.DOTALL).findall(data)
    for url, title, cantidad in matches:
        if cantidad == '0': continue
        titulo = '%s (%s)' % (title.strip().capitalize(), cantidad)
        itemlist.append(item.clone( title=titulo, url=url, action='list_all' ))

    return sorted(itemlist, key=lambda it: it.title)

def anios(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(host).data
    if item.search_type == 'movie':
        data = data.split('<div id="serieshome"')[0]
    else:
        data = data.split('<div id="serieshome"')[1]

    matches = re.compile('<li><a href="([^"]+)">([0-9–]+)</a></li>', re.DOTALL).findall(data)
    for url, title in matches:
        itemlist.append(item.clone( title=title, url=url, action='list_all' ))

    return itemlist

def calidades(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(host).data

    matches = re.compile('<li><a href="(%scalidad/[^"]+)">([^<]+)</a></li>' % host, re.DOTALL).findall(data)
    for url, title in matches:
        itemlist.append(item.clone( title=title, url=url, action='list_all' ))

    return itemlist



def list_all(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0

    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)

    data = data.replace('<div id="mt-', '<end><div id="mt-').replace('<div id="paginador"', '<end><div id="paginador"')
    
    matches = re.compile('<div id="mt-[^"]*" class="item">(.*?)<end>', re.DOTALL).findall(data)
    if '/?s=' in item.url: # para búsquedas eliminar resultados que apuntan a temporadas concretas
        matches = filter(lambda x: not ('<div class="typepost">movie' in x and '<span class="tt">Temporada ' in x), matches)
    if '/?s=' in item.url and item.search_type != 'all': # para búsquedas eliminar pelis/series según corresponda
        matches = filter(lambda x: ('<div class="typepost">movie' in x and item.search_type == 'movie') or \
                                   ('<div class="typepost">movie' not in x and item.search_type == 'tvshow'), matches)
    num_matches = len(matches)

    for article in matches[item.page * perpage:]:
        tipo = scrapertools.find_single_match(article, '<div class="typepost">([^<]+)</div>')
        if tipo != 'movie': tipo = 'tvshow'
        sufijo = '' if item.search_type != 'all' else tipo

        url = scrapertools.find_single_match(article, ' href="([^"]+)"')
        thumb = scrapertools.find_single_match(article, ' src="([^"]+)"')
        title = scrapertools.find_single_match(article, '<span class="tt">([^<]+)</span>')
        year = scrapertools.find_single_match(article, '<span class="year">([^<]+)</span>')
        quality = scrapertools.find_single_match(article, '<span class="calidad2">([^<]+)</span>')

        plot = scrapertools.find_single_match(article, '<span class="ttx">(.*?)</span>')
        if '&#160;' in plot: plot = plot.split('&#160;')[0].strip()
        if '<div class="degradado">' in plot: plot = plot.split('<div class="degradado">')[0].strip()
        
        title = re.sub('^Ver ', '', title)
        title = re.sub(' Online$', '', title)

        if tipo == 'movie':
            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb,
                                        qualities=quality, fmt_sufijo=sufijo,
                                        contentType='movie', contentTitle=title, infoLabels={'year': year, 'plot': plot} ))
        else:
            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, 
                                        qualities=quality, fmt_sufijo=sufijo,
                                        contentType='tvshow', contentSerieName=title, infoLabels={'year': year, 'plot': plot} ))

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
        next_page_link = scrapertools.find_single_match(data, '<div class="pag_b"><a href="([^"]+)">Siguiente</a>')
        if next_page_link:
            itemlist.append(item.clone( title='>> Página siguiente', url=next_page_link, page=0, action='list_all' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)

    matches = re.compile('<span class="se-t">(\d+)</span>', re.DOTALL).findall(data)
    for numtempo in matches:
        itemlist.append(item.clone( action='episodios', title='Temporada %s' % numtempo,
                                    contentType='season', contentSeason=numtempo ))
        
    tmdb.set_infoLabels(itemlist)

    return sorted(itemlist, key=lambda it: it.title)


# Si una misma url devuelve los episodios de todas las temporadas, definir rutina tracking_all_episodes para acelerar el scrap en trackingtools.
def tracking_all_episodes(item):
    return episodios(item)


def episodios(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)
    
    if item.contentSeason: # reducir datos a la temporada pedida
        data = scrapertools.find_single_match(data, '<span class="se-t">%d</span>(.*?)</ul>' % item.contentSeason)

    patron = '<li><div class="numerando">([^<]+)</div><div class="episodiotitle"><a href="([^"]+)">([^<]+)'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for s_e, url, title in matches:
        try:
            season, episode = scrapertools.find_single_match(s_e, '(\d+)\s*(?:-|x|X)\s*(\d+)')
        except:
            continue

        titulo = '%sx%s %s' % (season, episode, title)
        itemlist.append(item.clone( action='findvideos', url=url, title=titulo,
                                    contentType='episode', contentSeason=season, contentEpisodeNumber=episode ))

    tmdb.set_infoLabels(itemlist)

    return itemlist



# Asignar un numérico según las calidades del canal, para poder ordenar por este valor
def puntuar_calidad(txt):
    orden = ['Cam', 'TS-Screener', 'BR-Screener', 'HD', 'HD 720p']
    if txt not in orden: return 0
    else: return orden.index(txt) + 1

def findvideos(item):
    logger.info()
    itemlist = []
    
    IDIOMAS = {'Español':'Esp', 'Latino':'Lat', 'Subtitulado':'VOSE', 'Cast':'Esp', 'Castellano':'Esp', 'Sub':'VOSE'}

    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)

    # Enlaces
    patron = '<li class="elemento">\s*<a href="([^"]+)"'
    patron += '.*? alt="([^"]+)"'
    patron += '.*?<span class="c">([^<]+)</span>\s*<span class="d">([^<]+)</span>'

    matches = re.compile(patron, re.DOTALL).findall(data)
    for url, servidor, lang, qlty in matches:
        
        servidor = servidor.lower().split('.', 1)[0]
        if servidor == 'netu': servidor = 'netutv'
        
        itemlist.append(Item( channel = item.channel, action = 'play', server = servidor,
                              title = '', url = url,
                              language = IDIOMAS.get(lang, lang), quality = qlty, quality_num = puntuar_calidad(qlty)
                       ))

    # Vídeos incrustados
    matches = re.compile('<div style="display: none" id="plays-([^"]+)">(.*?)</div>', re.DOTALL).findall(data)
    for numero, enlace in matches:
        if enlace == '': continue
        url = 'https://www.cine-online.eu/ecrypt'

        # Correcciones lang quality pq hay diferentes variaciones
        lang = scrapertools.find_single_match(data, ' href="#div%s">([^<]+)</a></li>' % numero).strip()
        if lang == '':
            lang = scrapertools.find_single_match(data, ' href="#player2%s">([^<]+)</a></li>' % numero)
        m = re.match(r"(.*?)(\d+p)$", lang)
        if m: 
            lang = m.group(1).strip()
            qlty = m.group(2)
        else:
            qlty = ''
        m = re.match(r"(.*?) (HD)$", lang)
        if m: 
            lang = m.group(1).strip()
            qlty = m.group(2)
        m = re.match(r"(.*?) (\d+)$", lang)
        if m: 
            lang = m.group(1).strip()
            qlty = ''

        #TODO detectar servidor del texto encriptado antes del play (sin llamadas adicionales) !?

        itemlist.append(Item( channel = item.channel, action = 'play', server = '',
                              title = '', url = url, enlace = enlace.strip(), referer = item.url,
                              language = IDIOMAS.get(lang, lang), quality = qlty, quality_num = puntuar_calidad(qlty)
                       ))

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    if item.enlace:
        post = urllib.urlencode( {'nombre': item.enlace} )
        # ~ logger.debug(post)
        data = httptools.downloadpage(item.url, post=post).data
        # ~ logger.debug(data)

        url = scrapertools.find_single_match(data, ' src="([^"]+)"')
        if url == '':
            url = scrapertools.find_single_match(data, " src='([^']+)'")

        if url != '':
            itemlist.append(item.clone(url = url, server=servertools.get_server_from_url(url)))

    else:
        data = httptools.downloadpage(item.url).data
        # ~ logger.debug(data)
    
        url = scrapertools.find_single_match(data, "window.location='([^']+)")
        if url == '':
            url = scrapertools.find_single_match(data, 'window.location="([^"]+)')

        # Descartar o resolver acortadores
        if url.startswith('https://adf.ly/'): 
            url = scrapertools.decode_adfly(url)
            if url:
                item.server = servertools.get_server_from_url(url)
                if item.server == 'directo': return itemlist # si no encuentra el server o está desactivado
        elif url.startswith('http://uii.io/'):
            url = scrapertools.decode_uiiio(url)

        if url != '':
            itemlist.append(item.clone(url = url))
    
    return itemlist

def search(item, texto):
    logger.info()
    try:
        item.url = host + '?s=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
