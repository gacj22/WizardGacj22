# -*- coding: utf-8 -*-

import re, urllib

from platformcode import config, logger
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb

# ~ host = 'http://www.cuevana3.co/'
host = 'https://cuevana3.co/'

IDIOMAS = {'Latino':'Lat', 'Español':'Esp', 'Subtitulado':'VOSE'}


def configurar_proxies(item):
    from core import proxytools
    return proxytools.configurar_proxies_canal(item.channel, host)

def do_downloadpage(url, post=None):
    url = url.replace('http://www.cuevana3.co/', 'https://cuevana3.co/') # por si viene de enlaces guardados
    # ~ data = httptools.downloadpage(url, post=post).data
    data = httptools.downloadpage_proxy('cuevana3', url, post=post).data
    return data


def mainlist(item):
    return mainlist_pelis(item)

def mainlist_pelis(item):
    logger.info()
    itemlist = []
    
    itemlist.append(item.clone( title = 'Lista de películas', action = 'list_all', url = host + 'peliculas' ))
    itemlist.append(item.clone( title = 'Estrenos', action = 'list_all', url = host + 'estrenos' ))
    itemlist.append(item.clone( title = 'Más valoradas', action = 'list_all', url = host + 'peliculas-mas-valoradas' ))
    itemlist.append(item.clone( title = 'Más vistas', action = 'list_all', url = host + 'peliculas-mas-vistas' ))

    itemlist.append(item.clone( title = 'Castellano', action = 'list_all', url = host + 'peliculas-espanol' ))
    itemlist.append(item.clone( title = 'Latino', action = 'list_all', url = host + 'peliculas-latino' ))
    itemlist.append(item.clone( title = 'VOSE', action = 'list_all', url = host + 'peliculas-subtituladas' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie' ))

    plot = 'Es posible que para poder utilizar este canal necesites configurar algún proxy, ya que no es accesible desde algunos países/operadoras.'
    plot += '[CR]Si desde un navegador web no te funciona el sitio cuevana3.co necesitarás un proxy.'
    itemlist.append(item.clone( title = 'Configurar proxies a usar ...', action = 'configurar_proxies', folder=False, plot=plot, text_color='red' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host)

    matches = re.compile('/(category/[^"]+)">([^<]+)</a></li>', re.DOTALL).findall(data)
    for url, title in matches:
        itemlist.append(item.clone( title=title, url=host + url, action='list_all' ))

    return sorted(itemlist, key=lambda it: it.title)


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    # ~ logger.debug(data)
    
    matches = re.compile('<article[^>]*>(.*?)</article>', re.DOTALL).findall(data)
    for article in matches:
        url = scrapertools.find_single_match(article, ' href="([^"]+)"')
        if '/pagina-ejemplo' in url: continue
        thumb = scrapertools.find_single_match(article, ' src="([^"]+)"')
        title = scrapertools.find_single_match(article, '<h2 class="Title">([^<]+)</h2>')
        year = scrapertools.find_single_match(article, '<span class="Year">(\d+)</span>')
        quality = scrapertools.find_single_match(article, '<span class="Qlty">([^<]+)</span>')
        
        itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, 
                                    qualities=quality,
                                    contentType='movie', contentTitle=title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    next_page_link = scrapertools.find_single_match(data, ' rel="next" href="([^"]+)"')
    if next_page_link == '':
        next_page_link = scrapertools.find_single_match(data, ' href="([^"]+)" class="next')
    if next_page_link:
        itemlist.append(item.clone( title='>> Página siguiente', url=next_page_link, action='list_all' ))

    return itemlist


# Asignar un numérico según las calidades del canal, para poder ordenar por este valor
def puntuar_calidad(txt):
    orden = ['Cam', 'WEB-S', 'DVD-S', 'TS-HQ', 'DvdRip', 'HD']
    if txt not in orden: return 0
    else: return orden.index(txt) + 1

def findvideos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    # ~ logger.debug(data)
    
    patron = 'TPlayerNv="Opt(\w\d+)".*?img src="(.*?)<span>\d+ - (.*?) - ([^<]+)<'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for option, url_data, language, quality in matches:
        if 'domain=' in url_data:
            url = scrapertools.find_single_match(url_data, 'domain=([^"]+)"')
        elif 'file=' in url_data:
            url = scrapertools.find_single_match(data, 'id="Opt%s">.*?file=([^"]+)"' % option)
        else:
            continue

        if url and 'youtube' not in url:
            # ~ logger.info(url)
            itemlist.append(Item( channel = item.channel, action = 'play',
                                  title = '', url = url,
                                  language = IDIOMAS.get(language, language), quality = quality, quality_num = puntuar_calidad(quality)
                           ))

    itemlist = servertools.get_servers_itemlist(itemlist)

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
