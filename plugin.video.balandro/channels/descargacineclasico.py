# -*- coding: utf-8 -*-

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, tmdb, servertools

host = 'https://www.descargacineclasico.net/'


def mainlist(item):
    return mainlist_pelis(item)

def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Lista de películas', action = 'list_all', url = host, search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Películas en Castellano', action = 'list_all', url = host + 'tag/castellano/', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Películas en Latino', action = 'list_all', url = host + 'tag/latino/', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Películas en VOSE', action = 'list_all', url = host + 'tag/subtitulada/', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Películas en VO', action = 'list_all', url = host + 'tag/vo/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Documentales', action = 'list_all', url = host + 'tag/documentales/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(host).data

    patron = '<li[^>]*><a href="([^"]+)" title="[^"]*">([^<]+)</a></li>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for url, titulo in matches:
        itemlist.append(item.clone( title=titulo, url=url, action='list_all' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []
    
    IDIOMAS = {'latino':'Lat', 'espanol':'Esp', 'Vose':'VO', 'VOSE':'VOSE'}

    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)
    
    patron = '<div class="post-thumbnail">\s*<a href="([^"]+)" title="([^"]+)">\s*'
    patron += '<img width="[^"]*" height="[^"]*" style="[^"]*" src="([^"]+)"'
    patron += '.*?<p>(.*?)</p>'
    patron += '.*?<div id="campos_idiomas">(.*?)</div>'

    matches = scrapertools.find_multiple_matches(data, patron)

    for url, title, thumb, plot, languages in matches:
        if 'indice-de-peliculas-clasicas' in url: continue
        title = title.replace(' Descargar y ver Online', '')
        year = scrapertools.find_single_match(title, '\((\d{4})\)')
        if year:
            title = title.replace('(%s)' % year, '').strip()
        else:
            year = '-'
        plot = scrapertools.decodeHtmlentities(plot)
        
        langs = [] 
        # descartado pq los VO y VOSE no se acostrumbran a cumplir
        # ~ matches = scrapertools.find_multiple_matches(languages, 'style="([^"]+)" id="([^"]+)"')
        # ~ for estilo, lg in matches:
            # ~ if lg == 'Vose': continue # descartar pq no está en streaming
            # ~ if 'grayscale' not in estilo: langs.append(IDIOMAS.get(lg, lg))
        
        itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, 
                                    languages=', '.join(sorted(langs)),
                                    contentType='movie', contentTitle=title, infoLabels={'year': year, 'plot': plot} ))

    tmdb.set_infoLabels(itemlist)

    next_page_link = scrapertools.find_single_match(data, ' rel="next" href="([^"]+)"')
    if next_page_link:
        itemlist.append(item.clone( title='>> Página siguiente', url=next_page_link, action='list_all' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)
    
    if '<h3>Ver Online' in data: data = data.split('<h3>Ver Online')[1]
    
    patron = '<a href="#div_\d+_v" class="MO">\s*'
    patron += '<span>(.*?)</span>\s*'
    patron += '<span>.*?</span>\s*'
    patron += '<span>(.*?)</span>\s*'
    patron += '<span>.*?</span>\s*'
    patron += '<span>.*?</span>\s*'
    patron += '</a>\s*<span[^>]*>.*?</span>\s*'
    patron += '</p>\s*<div[^>]*>\s*<a href=([^ ]+)'

    matches = scrapertools.find_multiple_matches(data, patron)
    # ~ logger.debug(matches)
    for lg, qlty, url in matches:
        url = url.replace('"', '')
        # ~ if url.startswith('https://adf.ly/'): url = scrapertools.decode_adfly(url)
        if not url.startswith('http'): continue
        
        if '/esp.png' in lg: lang = 'Esp'
        elif '/esp-lat.png' in lg: lang = 'Lat'
        elif '/vose.png' in lg: lang = 'VOSE'
        else: lang = 'VO'

        itemlist.append(Item( channel = item.channel, action = 'play', server = '',
                              title = '', url = url,
                              language = lang, quality = qlty
                       ))

    itemlist = servertools.get_servers_itemlist(itemlist)
    
    # Dejar desconocidos de adfly como indeterminados para resolverse en el play ya que si se quieren resolver 
    # todos de golpe en findvideos adfly necesita esperas entre las llamadas
    for it in itemlist:
        if it.server == 'desconocido' and it.url.startswith('https://adf.ly/'):
            it.server = ''

    return itemlist

def play(item):
    logger.info()
    itemlist = []

    if item.url.startswith('https://adf.ly/'): 
        item.url = scrapertools.decode_adfly(item.url)
        if item.url:
            item.server = servertools.get_server_from_url(item.url)
            if item.server == 'directo': return itemlist # si no encuentra el server o está desactivado

    if item.url != '': 
        itemlist.append(item.clone())
    
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
