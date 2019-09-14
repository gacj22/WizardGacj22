# -*- coding: utf-8 -*-

import re, base64, urllib, urlparse

from platformcode import config, logger
from core.item import Item
from core import httptools, scrapertools, jsontools, servertools, tmdb


host = "https://hdfull.me"

perpage = 20 # preferiblemente un múltiplo de los elementos que salen en la web (40) para que la subpaginación interna no se descompense

# En la web:

# /peliculas-actualizadas y /peliculas-estreno solo muestran una página con 40 elementos sin paginación
# /peliculas/abc muestra páginas con 40 elementos paginables pero no permite escoger letra
# /peliculas/date (= /peliculas) y /peliculas/imdb_rating muestran páginas con 40 elementos paginables

# /series/date (= /series) y /series/imdb_rating solo muestran una página con 40 elementos sin paginación
# /series/abc/X muestra todas las series que empiezan por la letra (pueden ser cientos)
# /series/list es un listado de texto sin thumbnails de todas las series [no usado]
# /tags-tv/xxx (por género) muestra páginas con 40 elementos paginables

# /buscar muestra todas las pelis y series que coincidan (pueden ser bastantes)


# ~ def configurar_proxies(item):
    # ~ from core import proxytools
    # ~ return proxytools.configurar_proxies_canal(item.channel, host)

def do_downloadpage(url, post=None):
    url = url.replace('hdfull.tv', 'hdfull.me') # por si viene de enlaces guardados
    data = httptools.downloadpage(url, post=post).data
    # ~ data = httptools.downloadpage_proxy('hdfull', url, post=post).data
    return data


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Películas', action = 'mainlist_pelis' ))
    itemlist.append(item.clone( title = 'Series', action = 'mainlist_series' ))

    itemlist.append(item.clone( title = 'Buscar ...', action = 'search', search_type = 'all' ))
    
    # ~ plot = 'Es posible que para poder utilizar este canal necesites configurar algún proxy, ya que no es accesible desde algunos países/operadoras.'
    # ~ plot += '[CR]Si desde un navegador web no te funciona el sitio %s necesitarás un proxy.' % host
    # ~ itemlist.append(item.clone( title = 'Configurar proxies a usar ...', action = 'configurar_proxies', folder=False, plot=plot, text_color='red' ))

    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='list_all', title='Últimas actualizadas (40)', url=host+'/peliculas-actualizadas', search_type='movie' ))
    itemlist.append(item.clone( action='list_all', title='Últimos estrenos (40)', url=host+'/peliculas-estreno', search_type='movie' ))

    itemlist.append(item.clone( action='list_all', title='Lista por fecha', url=host+'/peliculas/date', search_type='movie' ))
    itemlist.append(item.clone( action='list_all', title='Lista por rating IMDB', url=host+'/peliculas/imdb_rating', search_type='movie' ))
    itemlist.append(item.clone( action='list_all', title='Lista por título', url=host+'/peliculas/abc', search_type='movie' ))

    itemlist.append(item.clone( action='generos', title='Por género', search_type='movie' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie' ))

    # ~ plot = 'Es posible que para poder utilizar este canal necesites configurar algún proxy, ya que no es accesible desde algunos países/operadoras.'
    # ~ plot += '[CR]Si desde un navegador web no te funciona el sitio %s necesitarás un proxy.' % host
    # ~ itemlist.append(item.clone( title = 'Configurar proxies a usar ...', action = 'configurar_proxies', folder=False, plot=plot, text_color='red' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='list_all', title='Últimas por fecha (40)', url=host+'/series/date', search_type='tvshow' ))
    itemlist.append(item.clone( action='list_all', title='Primeras por rating IMDB (40)', url=host+'/series/imdb_rating', search_type='tvshow' ))

    itemlist.append(item.clone( action='series_abc', title='Lista por letra A-Z', search_type='tvshow' ))
    itemlist.append(item.clone( action='generos', title='Lista por género', search_type='tvshow' ))

    itemlist.append(item.clone( action='list_episodes', title='Últimos episodios emitidos', opcion='latest' ))
    itemlist.append(item.clone( action='list_episodes', title='Episodios estreno', opcion='premiere' ))
    itemlist.append(item.clone( action='list_episodes', title='Episodios actualizados', opcion='updated' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow' ))

    # ~ plot = 'Es posible que para poder utilizar este canal necesites configurar algún proxy, ya que no es accesible desde algunos países/operadoras.'
    # ~ plot += '[CR]Si desde un navegador web no te funciona el sitio %s necesitarás un proxy.' % host
    # ~ itemlist.append(item.clone( title = 'Configurar proxies a usar ...', action = 'configurar_proxies', folder=False, plot=plot, text_color='red' ))

    return itemlist



def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host)
    # ~ logger.debug(data)

    tipo = 'TV' if item.search_type == 'tvshow' else 'Pel&iacute;culas'
    bloque = scrapertools.find_single_match(data, '<b class="caret"></b>&nbsp;&nbsp;%s</a>\s*<ul class="dropdown-menu">(.*?)</ul>' % tipo)

    matches = re.compile('<li><a href="([^"]+)">([^<]+)', re.DOTALL).findall(bloque)
    for url, title in matches:
        itemlist.append(item.clone( title=title, url=url, action='list_all' ))

    return sorted(itemlist, key=lambda it: it.title)


def series_abc(item):
    logger.info()
    itemlist = []

    for letra in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ9':
        itemlist.append(item.clone( title=letra if letra != '9' else '#', url=host+'/series/abc/'+letra, action='list_all' ))

    return itemlist



def detectar_idiomas(txt):
    languages = []
    if '/spa.png' in txt: languages.append('Esp')
    if '/lat.png' in txt: languages.append('Lat')
    if '/sub.png' in txt: languages.append('VOSE')
    if '/eng.png' in txt: languages.append('Eng')
    return languages

def list_all(item):
    logger.info()
    itemlist = []
    
    if not item.page: item.page = 0

    if item.search_post:
        data = do_downloadpage(item.url, post=item.search_post)
    else:
        data = do_downloadpage(item.url)
    # ~ logger.debug(data)

    patron = '<div class="item"[^>]*">'
    patron += '\s*<a href="([^"]+)"[^>]*>\s*<img class="[^"]*"\s+src="([^"]+)"[^>]*>'
    patron += '\s*</a>\s*</div>\s*<div class="rating-pod">\s*<div class="left">(.*?)</div>'
    patron += '.*? title="([^"]+)"'

    matches = re.compile(patron, re.DOTALL).findall(data)
    if item.search_post != '' and item.search_type != 'all': # para búsquedas eliminar pelis/series según corresponda
        matches = filter(lambda x: ('/pelicula/' in x[0] and item.search_type == 'movie') or \
                                   ('/serie/' in x[0] and item.search_type == 'tvshow'), matches)
    num_matches = len(matches)

    for url, thumb, langs, title in matches[item.page * perpage:]:
        
        title = title.strip()
        languages = detectar_idiomas(langs)
        tipo = 'movie' if '/pelicula/' in url else 'tvshow'
        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'movie':
            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, 
                                        languages=', '.join(languages), fmt_sufijo=sufijo,
                                        contentType='movie', contentTitle=title, infoLabels={'year': '-'} ))
        else:
            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, 
                                        languages=', '.join(languages), fmt_sufijo=sufijo,
                                        contentType='tvshow', contentSerieName=title, infoLabels={'year': '-'} ))

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
        next_page_link = scrapertools.find_single_match(data, '<a href="([^"]+)">&raquo;</a>')
        if next_page_link:
            itemlist.append(item.clone( title='>> Página siguiente', url=next_page_link, page=0 ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    # ~ logger.debug(data)
    
    sid = scrapertools.find_single_match(data, "var sid = '([^']+)';")
    
    patron = 'itemprop="season"[^>]*>'
    patron += '\s*<a href=\'([^\']+)\'[^>]*>\s*<img class="[^"]*"\s+original-title="([^"]+)"\s+alt="[^"]*"\s+src="([^"]+)"[^>]*>'
    patron += '\s*<h5[^>]*>([^<]+)</h5>'

    matches = re.compile(patron, re.DOTALL).findall(data)
    for url, title, thumb, retitle in matches:
        numtempo = scrapertools.find_single_match(title, 'Temporada (\d+)')
        if numtempo == '': numtempo = scrapertools.find_single_match(url, '-(\d+)$')
        if numtempo == '': continue
        titulo = title
        if retitle != title: titulo += ' - ' + retitle

        itemlist.append(item.clone( action='episodios', url=url, title=titulo, thumbnail=thumb, sid=sid,
                                    contentType='season', contentSeason=numtempo ))

    if len(itemlist) == 0: # Alguna serie de una sola temporada que no la tiene identificada
        itemlist.append(item.clone( action='episodios', url=item.url+'/temporada-1', title='Temporada 1', sid=sid,
                                    contentType='season', contentSeason=1 ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.sid:
        data = do_downloadpage(item.url)
        item.sid = scrapertools.find_single_match(data, "var sid = '([^']+)';")
        if not item.sid: return itemlist

    post = 'action=season&show=%s&season=%s' % (item.sid, item.contentSeason)
    data = jsontools.load(do_downloadpage(host + '/a/episodes', post=post))
    # ~ logger.debug(data)

    for epi in data:
        tit = epi['title']['es'] if 'es' in epi['title'] and epi['title']['es'] != '' else epi['title']['en'] if 'en' in epi['title'] else ''
        titulo = '%sx%s %s' % (epi['season'], epi['episode'], tit)
        
        langs = ['VOSE' if idio == 'ESPSUB' else idio.capitalize() for idio in epi['languages']]
        if langs: titulo += ' [COLOR pink][%s][/COLOR]' % ','.join(langs)
        
        thumb = host + '/tthumb/220x124/' + epi['thumbnail']
        url = item.url + '/episodio-' + epi['episode']

        itemlist.append(item.clone( action='findvideos', url=url, title=titulo, thumbnail=thumb,
                                    contentType='episode', contentSeason=epi['season'], contentEpisodeNumber=epi['episode'] ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


# Asignar un numérico según las calidades del canal, para poder ordenar por este valor
def puntuar_calidad(txt):
    orden = ['CAM', 'TS', 'DVDSCR', 'DVDRIP', 'HDTV', 'RHDTV', 'HD720', 'HD1080']
    if txt not in orden: return 0
    else: return orden.index(txt) + 1

def findvideos(item):
    logger.info()
    itemlist = []

    data_js = do_downloadpage(host+'/templates/hdfull/js/jquery.hdfull.view.min.js')
    key = scrapertools.find_single_match(data_js, 'JSON.parse\(atob.*?substrings\((.*?)\)')

    data_js = do_downloadpage(host+'/js/providers.js')
    try:
        from lib import balandroresolver
        provs = balandroresolver.hdfull_providers(data_js)
        if provs == '': return []
    except:
        return []

    data = do_downloadpage(item.url)
    # ~ logger.debug(data)
    data_obf = scrapertools.find_single_match(data, "var ad\s*=\s*'([^']+)")
    data_decrypt = jsontools.load(obfs(base64.b64decode(data_obf), 126 - int(key)))
    # ~ logger.debug(data_decrypt)

    matches = []
    for match in data_decrypt:
        if match['provider'] in provs:
            try:
                embed = provs[match['provider']][0]
                url = eval(provs[match['provider']][1].replace('_code_', "match['code']"))
                matches.append([match['lang'], match['quality'], url, embed])
            except:
                pass

    for idioma, calidad, url, embed in matches:
        if embed == 'd': continue # descartar descargas directas !?

        calidad = unicode(calidad, 'utf8').upper().encode('utf8')
        idioma = idioma.capitalize() if idioma != 'ESPSUB' else 'VOSE'
        # ~ logger.debug(url)

        itemlist.append(Item( channel = item.channel, action = 'play',
                              title = '', url = url, 
                              language = idioma, quality = calidad, quality_num = puntuar_calidad(calidad)
                       ))

    itemlist = servertools.get_servers_itemlist(itemlist)

    return itemlist


def search(item, texto):
    logger.info()
    try:
        data = do_downloadpage(host)
        magic = scrapertools.find_single_match(data, "name='__csrf_magic'\s*value=\"([^\"]+)")
        item.search_post = '__csrf_magic=%s&menu=search&query=%s' % (magic, texto.replace(' ','+'))
        item.url = host + '/buscar'
        if item.search_type == '': item.search_type = 'all'
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def list_episodes(item):
    logger.info()
    itemlist = []

    if not item.opcion: item.opcion = 'latest'
    if not item.desde: item.desde = 0

    post = 'action=%s&start=%d&limit=%d&elang=ALL' % (item.opcion, item.desde, perpage)
    data = jsontools.load(do_downloadpage(host + '/a/episodes', post=post))
    # ~ logger.debug(data)

    for epi in data:
        show = epi['show']['title']['es'] if 'es' in epi['show']['title'] and epi['show']['title']['es'] != '' else epi['show']['title']['en'] if 'en' in epi['show']['title'] else ''

        tit = epi['title']['es'] if 'es' in epi['title'] and epi['title']['es'] != '' else epi['title']['en'] if 'en' in epi['title'] else ''
        titulo = '%s %sx%s %s' % (show, epi['season'], epi['episode'], tit)
        
        langs = ['VOSE' if idio == 'ESPSUB' else idio.capitalize() for idio in epi['languages']]
        if langs: titulo += ' [COLOR pink][%s][/COLOR]' % ','.join(langs)
        
        thumb = host + '/tthumb/220x124/' + epi['thumbnail']
        
        url_serie = host + '/serie/' + epi['show']['permalink']
        url_tempo = url_serie + '/temporada-' + epi['season']
        url = url_serie + '/episodio-' + epi['episode']

        context = []
        context.append({ 'title': '[COLOR pink]Listar temporada %s[/COLOR]' % epi['season'], 
                         'action': 'episodios', 'url': url_tempo, 'context': '', 'folder': True, 'link_mode': 'update' })
        context.append({ 'title': '[COLOR pink]Listar temporadas[/COLOR]',
                         'action': 'temporadas', 'url': url_serie, 'context': '', 'folder': True, 'link_mode': 'update' })

        itemlist.append(item.clone( action='findvideos', url=url, title=titulo, thumbnail=thumb, context=context,
                                    contentType='episode', contentSerieName=show, 
                                    contentSeason=epi['season'], contentEpisodeNumber=epi['episode'] ))

    tmdb.set_infoLabels(itemlist)

    if len(itemlist) >= perpage:
        itemlist.append(item.clone( title='>> Página siguiente', desde=item.desde + perpage ))

    return itemlist


## --------------------------------------------------------------------------------
## --------------------------------------------------------------------------------

# Desobfuscación de datos en findvideos
def obfs(data, key, n=126):
    chars = list(data)
    for i in range(0, len(chars)):
        c = ord(chars[i])
        if c <= n:
            number = (ord(chars[i]) + key) % n
            chars[i] = chr(number)
    return "".join(chars)
