# -*- coding: utf-8 -*-

import re, urllib, urlparse, base64

from platformcode import config, logger
from core.item import Item
from core import httptools, scrapertools, tmdb, servertools


# ~ host = "http://www.canalpelis.com/"
host = "https://cinexin.net/"

perpage = 18 # preferiblemente un múltiplo de los elementos que salen en la web (18x5=90) para que la subpaginación interna no se descompense


def normalizar_url(url):
    url = url.replace('//www.', '//')
    url = url.replace('http://', 'https://')
    url = url.replace('canalpelis.com/', 'cinexin.net/')

    # ~ url = url.replace('/peliculas/', '/movies/').replace('/series/', '/tvshows/').replace('/genero/', '/genre/')
    url = url.replace('/movies/', '/peliculas/').replace('/tvshows/', '/series/').replace('/genre/', '/genero/')

    return url


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

    itemlist.append(item.clone( title = 'Lista de películas', action = 'list_all', url = host + 'movies/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Nueva calidad', action = 'list_all', url = host + 'genre/nueva-calidad/', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Últimos estrenos', action = 'list_all', url = host + 'genre/estrenos/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anyos', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie' ))

    return itemlist

def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Lista de series', action = 'list_all', url = host + 'tvshows/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(normalizar_url(host + 'movies/')).data

    patron = '<li class="cat-item cat-item-[^"]+"><a href="([^"]+)"[^>]*>([^<]+)</a>\s*<i>([^<]+)</i>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for url, title, cantidad in matches:
        if cantidad == '0': continue
        if '/nueva-calidad/' in url or '/estrenos/' in url: continue # pq ya están en el menú principal
        title = title.replace('♦', '').strip()
        itemlist.append(item.clone( action="list_all", title='%s (%s)' % (title, cantidad), url=url ))

    return sorted(itemlist, key=lambda it: it.title)


def anyos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(normalizar_url(host + 'movies/')).data

    patron = '<li><a href="([^"]+)">(\d+)</a></li>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for url, title in matches:
        itemlist.append(item.clone( action="list_all", title=title, url=url ))

    return itemlist


# mantener rutinas anteriores por si hay enlaces guardados
def peliculas(item):
    return list_all(item)

def series(item):
    return list_all(item)


def list_all(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    
    data = httptools.downloadpage(normalizar_url(item.url)).data
    # ~ logger.debug(data)

    matches = re.compile('<article id="[^"]+" class="item (movie|tvshow)s">(.*?)</article>', re.DOTALL).findall(data)
    num_matches = len(matches)

    for tipo, article in matches[item.page * perpage:]:
        if item.search_type not in ['all', tipo]: continue
        # ~ logger.debug(article)
        if '<div class="featu">Destacado</div>' in article: continue

        url = scrapertools.find_single_match(article, ' href="([^"]+)"')
        thumb = scrapertools.find_single_match(article, ' src="([^"]+)"')
        title = scrapertools.find_single_match(article, '<h4>([^<]+)</h4>').strip()
        if not title:
            title = scrapertools.find_single_match(article, ' alt="([^"]+)"').strip()
        year = scrapertools.find_single_match(article, '<span>(\d{4})</span>')
        quality = scrapertools.find_single_match(article, '<span class="quality">([^<]+)</span>').strip()
        plot = scrapertools.find_single_match(article, '<div class="texto">([^<]+)</div>')
        plot = scrapertools.htmlclean(plot)
        
        titulo = title
        titlealt = scrapertools.find_single_match(title, '\((.*)\)$') # si acaba en (...) puede ser el título traducido ej: Cast (Eng)
        if titlealt != '':
            title = title.replace('(%s)' % titlealt, '').strip()
            if titlealt.isdigit(): titlealt = '' # si sólo hay dígitos seguramente no es un título alternativo

        if tipo == 'tvshow':
            itemlist.append(item.clone( action='temporadas', url=url, title=titulo, thumbnail=thumb, contentTitleAlt=titlealt, 
                                        qualities=quality,
                                        contentType='tvshow', contentSerieName=title, infoLabels={'year': year, 'plot': plot} ))
        else:
            itemlist.append(item.clone( action='findvideos', url=url, title=titulo, thumbnail=thumb, contentTitleAlt=titlealt, 
                                        qualities=quality,
                                        contentType='movie', contentTitle=title, infoLabels={'year': year, 'plot': plot}, quality = quality ))
 
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
        next_page_link = scrapertools.find_single_match(data, '<link rel="next" href="([^"]+)')
        if next_page_link:
            itemlist.append(item.clone( title='>> Página siguiente', url=next_page_link, page=0, action='list_all' ))

    return itemlist



def temporadas(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(normalizar_url(item.url)).data
    datas = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    # ~ logger.debug(datas)
    # ~ patron = '<span class="title">([^<]+)<i>.*?'  # numeros de temporadas
    # ~ patron += '<img src="([^"]+)'  # capitulos
    patron = "<span class='title'>([^<]+)<i>.*?"  # numeros de temporadas
    patron += "<img src='([^']+)"  # capitulos

    matches = scrapertools.find_multiple_matches(datas, patron)
    if len(matches) > 1:
        for scrapedseason, scrapedthumbnail in matches:
            scrapedseason = " ".join(scrapedseason.split())
            temporada = scrapertools.find_single_match(scrapedseason, '(\d+)')
            new_item = item.clone(action="episodios", season=temporada, thumbnail=scrapedthumbnail, extra='temporadas')
            new_item.infoLabels['season'] = temporada
            new_item.extra = ""
            if int(temporada) in [it.infoLabels['season'] for it in itemlist]: continue # evitar duplicados
            itemlist.append(new_item)

        tmdb.set_infoLabels(itemlist)

        for i in itemlist:
            i.title = "%s. %s" % (i.infoLabels['season'], i.infoLabels['tvshowtitle'])
            if i.infoLabels['title']:
                # Si la temporada tiene nombre propio añadirselo al titulo del item
                i.title += " - %s" % (i.infoLabels['title'])
            if i.infoLabels.has_key('poster_path'):
                # Si la temporada tiene poster propio remplazar al de la serie
                i.thumbnail = i.infoLabels['poster_path']

        itemlist.sort(key=lambda it: it.title)

    if len(itemlist) > 0:
        return itemlist
    else:
        return episodios(item)
    # ~ return itemlist


# Si una misma url devuelve los episodios de todas las temporadas, definir rutina tracking_all_episodes para acelerar el scrap en trackingtools.
def tracking_all_episodes(item):
    return episodios(item)


def episodios(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(normalizar_url(item.url)).data
    datas = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    # ~ logger.debug(datas)
    # ~ patron = '<div class="imagen"><a href="([^"]+)">.*?'  # url cap, img
    # ~ patron += '<div class="numerando">(.*?)</div>.*?'  # numerando cap
    # ~ patron += '<a href="[^"]+">([^<]+)</a>'  # title de episodios
    patron = "<div class='imagen'>.*?"
    patron += "<div class='numerando'>(.*?)</div>.*?"
    patron += "<a href='([^']+)'>([^<]+)</a>"

    matches = scrapertools.find_multiple_matches(datas, patron)

    for scrapedtitle, scrapedurl, scrapedname in matches:
        # ~ logger.debug(scrapedtitle)
        scrapedtitle = scrapedtitle.replace('--', '0')
        patron = '(\d+) - (\d+)'
        match = re.compile(patron, re.DOTALL).findall(scrapedtitle)
        if not match: continue
        season, episode = match[0]

        if 'season' in item.infoLabels and int(item.infoLabels['season']) != int(season):
            continue

        title = "%sx%s: %s" % (season, episode.zfill(2), scrapertools.unescape(scrapedname))
        new_item = item.clone(title=title, url=scrapedurl, action="findvideos", fulltitle=title, contentType="episode")
        if 'infoLabels' not in new_item: new_item.infoLabels = {}
        new_item.infoLabels['season'] = season
        new_item.infoLabels['episode'] = episode.zfill(2)

        itemlist.append(new_item)

    tmdb.set_infoLabels(itemlist)

    for i in itemlist:
        if i.infoLabels['title']:
            # Si el capitulo tiene nombre propio añadirselo al titulo del item
            i.title = "%sx%s %s" % (i.infoLabels['season'], i.infoLabels['episode'], i.infoLabels['title'])
        if i.infoLabels.has_key('poster_path'):
            # Si el capitulo tiene imagen propia remplazar al poster
            i.thumbnail = i.infoLabels['poster_path']

    return itemlist



# Asignar un numérico según las calidades del canal, para poder ordenar por este valor
def puntuar_calidad(txt):
    if txt == '': return ''
    orden = ['HD-TS', 'TS-HQ', 'HD-TC', 'HD']
    if txt not in orden: return 0
    else: return orden.index(txt) + 1

def detectar_server(servidor):
    if 'openload' in servidor: servidor = 'openload'
    elif 'verystream' in servidor: servidor = 'verystream'
    return ''

def findvideos(item):
    logger.info()
    itemlist = []
    
    IDIOMAS = {'es':'Esp', 'mx':'Lat', 'ar':'Lat', 'en':'Eng', 'gb':'Eng', 'vose':'VOSE', 'vos':'VOS', 'fr':'Fra', 'jp':'Jap'}

    data = httptools.downloadpage(normalizar_url(item.url)).data
    # ~ logger.debug(data)

    patron = "data-post='(\d+)' data-nume='(\d+)'.*?<span class='title'>([^<]+).*?<span class='server'>([^.<]+).*?img src='([^']+)'"
    matches = re.compile(patron, re.DOTALL).findall(data)
    if not matches:
        patron = 'data-post="(\d+)" data-nume="(\d+)".*?<span class="title">([^<]+).*?<span class="server">([^.<]+).*?img src=\'([^\']+)\''
        matches = re.compile(patron, re.DOTALL).findall(data)
    
    for dpost, dnume, titulo, servidor, lang in matches:
        if 'subtitulada' in titulo.lower(): lang = 'vose'
        elif 'subtitles' in titulo.lower(): lang = 'vos'
        else: lang = scrapertools.find_single_match(lang, '.*?/flags/(.*?)\.png')

        itemlist.append(Item( channel = item.channel, action = 'play', server = detectar_server(servidor),
                              title = '', dpost = dpost, dnume = dnume, 
                              language = IDIOMAS.get(lang, lang), quality = item.quality, quality_num = puntuar_calidad(item.quality)
                       ))

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    post = urllib.urlencode( {'action': 'doo_player_ajax', 'post': item.dpost, 'nume': item.dnume, 'type':'movie'} )
    data = httptools.downloadpage(host + 'wp-admin/admin-ajax.php', post=post, headers={'Referer':item.url}).data
    # ~ logger.debug(data)

    url = scrapertools.find_single_match(data, "src='([^']+)'")

    if url.startswith(host):
        locationurl = httptools.downloadpage(url, follow_redirects=False, only_headers=True).headers.get('location', '')
        if locationurl != '':
            try:
                y = scrapertools.find_single_match(locationurl, "y=([^&]+)")
                if y: url = base64.b64decode(y)
                else: url = locationurl
            except:
                url = locationurl

    elif url.startswith('https://hideiframe.site/protect.php?'):
        y = scrapertools.find_single_match(url, 'y=([^&]+)')
        if y: url = base64.b64decode(y)
        else: url = ''

    if url != '': 
        servidor = servertools.get_server_from_url(url)
        if servidor == 'directo': return itemlist # si no encuentra el server o está desactivado

        itemlist.append(item.clone(url = url, server = servidor))

    return itemlist



def search(item, texto):
    logger.info()
    # Permite buscar en películas, en series, o en ambas
    if item.search_type not in ['movie', 'tvshow', 'all']: item.search_type = 'all'
    try:
        item.url = host + '?s=' + texto.replace(" ", "+")
        return sub_search(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []


def sub_search(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    # ~ logger.debug(data)

    patron = '<div class="thumbnail animation-2">(.*?)</div></article>'
    bloques = re.compile(patron, re.DOTALL).findall(data)
    num_matches = len(bloques)

    for bloque in bloques[item.page * perpage:]:
        scrapedurl = scrapertools.find_single_match(bloque,'<a href="([^"]+)')
        scrapedthumbnail, scrapedtitle = scrapertools.find_single_match(bloque,'<img src="([^"]+)" alt="([^"]+)"')
        tipo = scrapertools.find_single_match(bloque,'<span class="(movies|tvshows)"')
        year = scrapertools.find_single_match(bloque,'<span class="year">([^<]+)')
        langs = scrapertools.find_multiple_matches(bloque, 'img/flags/([a-z]*)\.png')

        newitem = item.clone( title = scrapedtitle, url = scrapedurl, thumbnail = scrapedthumbnail, infoLabels = {'year': year} )

        if tipo == 'tvshows':
            newitem.action = 'temporadas'
            newitem.contentType = 'tvshow'
            newitem.contentSerieName = scrapedtitle
        else:
            newitem.action = 'findvideos'
            newitem.contentType = 'movie'
            newitem.contentTitle = scrapedtitle
        
        newitem.languages = ', '.join(langs)
        newitem.fmt_sufijo = '' if item.search_type != 'all' else newitem.contentType
        
        if item.search_type == 'all' or (item.search_type == 'movie' and tipo == 'movies') or (item.search_type == 'tvshow' and tipo == 'tvshows'):
            itemlist.append(newitem)
            if len(itemlist) >= perpage: break

    tmdb.set_infoLabels(itemlist)

    # Subpaginación interna y/o paginación de la web
    buscar_next = True
    if num_matches > perpage: # subpaginación interna dentro de la página si hay demasiados items
        hasta = (item.page * perpage) + perpage
        if hasta < num_matches:
            itemlist.append(item.clone( title='>> Página siguiente', page=item.page + 1, action='sub_search' ))
            buscar_next = False

    if buscar_next:
        next_page_link = scrapertools.find_single_match(data, '<a class="page larger" href="([^"]+)">\d+</a>')
        if next_page_link:
            itemlist.append(item.clone( title='>> Página siguiente', url=next_page_link, page=0, action='sub_search' ))

    return itemlist
