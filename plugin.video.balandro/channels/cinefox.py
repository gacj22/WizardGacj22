# -*- coding: utf-8 -*-

import re, urlparse

from platformcode import config, logger
from core.item import Item
from core import httptools, scrapertools, servertools, jsontools, tmdb


IDIOMAS = {'Latino': 'Lat', 'Castellano': 'Esp', 'Vo': 'VO', 'Vose': 'VOSE'}

# ~ host = 'http://www.cinefox.tv' / 'http://gnula.biz'

def detectar_host(canal):
    return 'http://gnula.biz' if canal == 'gnula_biz' else 'http://www.cinefox.tv'


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Películas', action = 'mainlist_pelis' ))
    itemlist.append(item.clone( title = 'Series', action = 'mainlist_series' ))
    itemlist.append(item.clone( title = 'Buscar...', action = 'search', search_type = 'all' ))

    return itemlist

def mainlist_pelis(item):
    logger.info()
    itemlist = []
    host = detectar_host(item.channel)
    
    itemlist.append(item.clone( title='Novedades', action='peliculas', url=host + '/catalogue?type=peliculas' ))
    itemlist.append(item.clone( title='Mejor valoradas', action='peliculas', url=host + '/catalogue?type=peliculas&order=most_rated' ))
    itemlist.append(item.clone( title='Más vistas', action='peliculas', url=host + '/catalogue?type=peliculas&order=most_viewed' ))
    itemlist.append(item.clone( title='Estrenos', action='peliculas', url=host + '/estrenos-de-cine' ))

    itemlist.append(item.clone( title='Por género', action='generos', search_type='movie' ))
    # ~ itemlist.append(item.clone( title='Por género', action='secciones', extra='peliculas', seccion='Género' ))
    itemlist.append(item.clone( title='Por año', action='secciones', extra='peliculas', seccion='Año' ))
    itemlist.append(item.clone( title='Por país', action='secciones', extra='peliculas', seccion='País' ))
    itemlist.append(item.clone( title='Por calidad', action='secciones', extra='peliculas', seccion='Calidad' ))
    itemlist.append(item.clone( title='Por idioma', action='secciones', extra='peliculas', seccion='Idioma' ))

    itemlist.append(item.clone( title = 'Buscar película...', action = 'search', search_type = 'movie' ))

    return itemlist

def mainlist_series(item):
    logger.info()
    itemlist = []
    host = detectar_host(item.channel)

    itemlist.append(item.clone( title='Series recientes', action='series', url=host + '/catalogue?type=series' ))
    itemlist.append(item.clone( title='Series mejor valoradas', action='series', url=host + '/catalogue?type=series&order=most_rated' ))
    itemlist.append(item.clone( title='Series más vistas', action='series', url=host + '/catalogue?type=series&order=most_viewed' ))
    itemlist.append(item.clone( title='Últimos capítulos', action='ultimos', url=host + '/ultimos-capitulos' ))

    itemlist.append(item.clone( title='Por género', action='generos', search_type='tvshow' ))
    # ~ itemlist.append(item.clone( title='Por género', action='secciones', extra='series', seccion='Género' ))
    itemlist.append(item.clone( title='Por año', action='secciones', extra='series', seccion='Año' ))
    itemlist.append(item.clone( title='Por país', action='secciones', extra='series', seccion='País' ))
    itemlist.append(item.clone( title='Por calidad', action='secciones', extra='series', seccion='Calidad' ))
    itemlist.append(item.clone( title='Por idioma', action='secciones', extra='series', seccion='Idioma' ))

    itemlist.append(item.clone( title = 'Buscar serie...', action = 'search', search_type = 'tvshow' ))

    return itemlist


def limpiar_thumbnail(thumb):
    thumb = thumb.replace('https://image.tmdb.org/t/p/w200_and_h300_bestv2', '')
    thumb = thumb.replace('https://image.tmdb.org/t/p/w185_and_h278_bestv2', '')
    return thumb


def search(item, texto):
    logger.info()
    try:
        host = detectar_host(item.channel)
        texto = texto.replace(" ", "+")
        item.url = host + "/search?q=%s" % texto
        if item.search_type == '': item.search_type = 'all'
        return busqueda(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def busqueda(item):
    logger.info()
    itemlist = []
    host = detectar_host(item.channel)

    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)

    patron = '<div class="poster-media-card">(.*?)(?:<li class="search-results-item media-item">|<footer>)'
    bloque = scrapertools.find_multiple_matches(data, patron)
    for match in bloque:
        # ~ logger.debug(match)
        patron = 'href="([^"]+)" title="([^"]+)".*?src="([^"]+)".*?' \
                 '<p class="search-results-main-info">.*?del año (\d+).*?' \
                 'p class.*?>(.*?)<'
        matches = scrapertools.find_multiple_matches(match, patron)
        for scrapedurl, scrapedtitle, scrapedthumbnail, year, plot in matches:
            scrapedtitle = scrapedtitle.capitalize()
            plot = scrapertools.htmlclean(plot)
            new_item = Item(channel=item.channel, thumbnail=scrapedthumbnail, plot=plot)
            new_item.infoLabels["year"] = year

            if "/serie/" in scrapedurl:
                new_item.contentType = 'tvshow'
                new_item.contentSerieName = scrapedtitle
                new_item.action = 'temporadas'
                scrapedurl += "/episodios"

            elif "/pelicula/" in scrapedurl or "/adulto/" in scrapedurl:
                new_item.contentType = 'movie'
                new_item.contentTitle= scrapedtitle
                new_item.action = 'findvideos'
                # ~ filter_list = {"poster_path": limpiar_thumbnail(scrapedthumbnail)}
                # ~ new_item.infoLabels['filtro'] = filter_list.items()
                # parece que con filtro se detectan peor en tmdb !?
            else:
                logger.info('Enlace no tratado: %s' % scrapedurl)
                continue

            if item.search_type == 'all' or item.search_type == new_item.contentType:
                new_item.fmt_sufijo = '' if item.search_type != 'all' else new_item.contentType
                new_item.title = scrapedtitle
                new_item.url = scrapedurl
                itemlist.append(new_item)


    # ~ for it in itemlist: logger.debug(it)
    tmdb.set_infoLabels(itemlist)

    next_page = scrapertools.find_single_match(data, 'href="([^"]+)"[^>]+>Más resultados')
    if next_page != "" and len(bloque) > 0:
        next_page = urlparse.urljoin(host, next_page)
        itemlist.append(item.clone(title=">> Siguiente", url=next_page, action='busqueda'))

    return itemlist


def generos(item):
    logger.info()
    if item.search_type == 'movie':
        return secciones(item.clone( action='secciones', extra='peliculas', seccion='Género' ))
    else:
        return secciones(item.clone( action='secciones', extra='series', seccion='Género' ))

def secciones(item):
    logger.info()
    itemlist=[]
    host = detectar_host(item.channel)
    
    if item.extra not in ['peliculas','series']: item.extra = 'peliculas'
    url = host + '/catalogue?type=' + item.extra
    data = httptools.downloadpage(url).data

    if item.seccion not in ['Género','Año','País','Calidad','Idioma']: item.seccion = 'Género'
    data_seccion = scrapertools.find_single_match(data,'<div class="dropdown-sub">%s.*?</ul>' % item.seccion)

    patron  = '<li><a href="([^"]+)">([^<]+)</a></li>'
    matches = scrapertools.find_multiple_matches(data_seccion, patron)
    for scrapedurl, scrapedtitle in matches:
        itemlist.append(item.clone(title=scrapedtitle, url=scrapedurl, action=item.extra))

    if item.extra == 'peliculas' and item.seccion == 'Género':
        itemlist.append(item.clone(title='Adultos +18', url=host + '/catalogue?type=adultos', action='peliculas'))

    return sorted(itemlist, key=lambda it: it.title)



def peliculas(item):
    logger.info()
    itemlist = []
    host = detectar_host(item.channel)

    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_multiple_matches(data, '<div class="media-card "(.*?)<div class="hidden-info">')
    for match in bloque:
        patron = 'src="([^"]+)".*?href="([^"]+)">([^<]+)</a>'
        matches = scrapertools.find_multiple_matches(match, patron)
        for scrapedthumbnail, scrapedurl, scrapedtitle in matches:
            if '/pelicula/' not in scrapedurl and '/adulto/' not in scrapedurl: continue
            url = urlparse.urljoin(host, scrapedurl)

            # ~ filter_list = {"poster_path": limpiar_thumbnail(scrapedthumbnail)}
            # ~ infoLabels = {'filtro': filter_list.items(), 'year': '-'}
            infoLabels = {'year': '-'} # parece que con filtro se detectan peor en tmdb !?

            itemlist.append(item.clone( action="findvideos", title=scrapedtitle, url=url,
                                        thumbnail=scrapedthumbnail, contentType="movie", contentTitle=scrapedtitle,
                                        infoLabels=infoLabels ))

    tmdb.set_infoLabels(itemlist)

    next_page = scrapertools.find_single_match(data, 'href="([^"]+)"[^>]+>Siguiente')
    if next_page != "" and item.title != "":
        itemlist.append(item.clone(title=">> Siguiente", url=next_page))

    return itemlist


def ultimos(item):
    logger.info()
    itemlist = []
    host = detectar_host(item.channel)

    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_multiple_matches(data, '<div class="media-card "(.*?)<div class="info-availability '
                                                      'one-line">')
    for match in bloque:
        patron = '<div class="audio-info">(.*?)<img class.*?src="([^"]+)".*?href="([^"]+)">([^<]+)</a>'
        matches = scrapertools.find_multiple_matches(match, patron)
        for idiomas, scrapedthumbnail, scrapedurl, scrapedtitle in matches:
            show = re.sub(r'(\s*[\d]+x[\d]+\s*)', '', scrapedtitle)
            audios = []
            if "medium-es" in idiomas: audios.append('Esp')
            if "medium-la" in idiomas: audios.append('Lat')
            if "medium-vs" in idiomas: audios.append('VOSE')
            if "medium-en" in idiomas or 'medium-"' in idiomas: audios.append('VO')
            title = "%s - %s" % (show, re.sub(show, '', scrapedtitle))
            if audios: title += " [%s]" % ",".join(audios)
            url = urlparse.urljoin(host, scrapedurl)

            se_ep = scrapertools.find_multiple_matches(data, '(\d+)x(\d+)')
            if len(se_ep) > 1:
                itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=scrapedthumbnail,
                                            contentType='episode', contentSerieName=show, contentSeason=se_ep[0], contentEpisodeNumber=se_ep[1] ))
            else:
                itemlist.append(item.clone( action="episodios", url=url, title=title, thumbnail=scrapedthumbnail,
                                            contentType="tvshow", contentSerieName=show, extra='ultimos' ))
                
            # Menú contextual: ofrecer acceso a temporada / serie
            # No se puede (sin acceder a otras urls) pq no hay enlace al id de la serie

    tmdb.set_infoLabels(itemlist)

    next_page = scrapertools.find_single_match(data, 'href="([^"]+)"[^>]+>Siguiente')
    if next_page != "":
        itemlist.append(item.clone(title=">> Siguiente", url=next_page))

    return itemlist


def series(item):
    logger.info()
    itemlist = []
    host = detectar_host(item.channel)

    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_multiple_matches(data, '<div class="media-card "(.*?)<div class="hidden-info">')
    for match in bloque:
        patron = '<img class.*?src="([^"]+)".*?href="([^"]+)">([^<]+)</a>'
        matches = scrapertools.find_multiple_matches(match, patron)
        for scrapedthumbnail, scrapedurl, scrapedtitle in matches:
            url = urlparse.urljoin(host, scrapedurl + "/episodios")

            itemlist.append(item.clone( action="temporadas", title=scrapedtitle, url=url, thumbnail=scrapedthumbnail,
                                        contentType="tvshow", contentSerieName=scrapedtitle ))

    tmdb.set_infoLabels(itemlist)

    next_page = scrapertools.find_single_match(data, 'href="([^"]+)"[^>]+>Siguiente')
    if next_page != "":
        itemlist.append(item.clone(title=">> Siguiente", url=next_page))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)
    patron = ' id="season-toggle-\d+" data-season-num="(\d+)">\d+</span>'
    matches = scrapertools.find_multiple_matches(data, patron)
    if len(matches) > 0:
        for scrapedseason in matches:
            itemlist.append(item.clone( action="episodios", title='Temporada '+str(scrapedseason), 
                                        contentType='season', contentSeason=scrapedseason ))

        tmdb.set_infoLabels(itemlist)

    # ~ if len(itemlist) > 0:
        # ~ return itemlist
    # ~ else:
        # ~ return episodios(item)
    return itemlist


# Si una misma url devuelve los episodios de todas las temporadas, definir rutina tracking_all_episodes para acelerar el scrap en trackingtools.
def tracking_all_episodes(item):
    return episodios(item)


def episodios(item):
    logger.info()
    itemlist = []

    if item.extra == "ultimos":
        data = httptools.downloadpage(item.url).data
        item.url = scrapertools.find_single_match(data, '<a href="([^"]+)" class="h1-like media-title"')
        item.url += "/episodios"

    if item.contentSeason:
        patron = '<div class="ep-list-number">.*?href="([^"]+)">(%d)x(\d+)</a>.*?<span class="name">([^<]+)</span>' % item.contentSeason
    else:
        patron = '<div class="ep-list-number">.*?href="([^"]+)">(\d+)x(\d+)</a>.*?<span class="name">([^<]+)</span>'
    
    data = httptools.downloadpage(item.url).data
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedseason, scrapedepisode, scrapedtitle in matches:
        # ~ scrapedtitle = re.sub(r'(Capítulo \d+: )', '', scrapedtitle)
        itemlist.append(item.clone( action='findvideos', url=scrapedurl, title='%sx%s - %s' % (scrapedseason, scrapedepisode, scrapedtitle), 
                                    contentType='episode', contentSeason=scrapedseason, contentEpisodeNumber=scrapedepisode ))

    tmdb.set_infoLabels(itemlist)

    if not item.contentSeason: itemlist.reverse() # si se listan todos los episodios, que se vean primero los últimos

    return itemlist



# Asignar un numérico según las calidades del canal, para poder ordenar por este valor
def puntuar_calidad(txt):
    orden = ['3D', 'CAMRip', 'Screener', 'Ts', 'Ts HQ', 'WEBs', 'DVDs', 'HDTs', 'HDTVs', 'Bluray Screener', 
             'WEBRip', 'DVDRip', 'HDRip', 'HDTV Rip', 
             'HD', 'HQ', 'DVDFull', 'Bluray Line', 'Bluray Rip', 'Micro720p', 'Micro1080p']
    if txt not in orden: return 0
    else: return orden.index(txt) + 1

def findvideos(item):
    logger.info()
    itemlist = []
    host = detectar_host(item.channel)

    extra = 'media' if item.contentType == 'movie' else 'episode'
    numid = scrapertools.find_single_match(item.url, '/(\d+)/')
    if numid == '':
       data = httptools.downloadpage(item.url).data
       numid = scrapertools.find_single_match(data, 'data-idm="(.*?)"')

    url = host + "/sources/list?id=%s&type=%s&order=%s" % (numid, extra, "streaming")
    itemlist=(get_enlaces(item, url, "Online"))

    # ~ url = host + "/sources/list?id=%s&type=%s&order=%s" % (numid, extra, "download")
    # ~ itemlist.extend(get_enlaces(item, url, "de Descarga"))

    return itemlist


def get_enlaces(item, url, tipo_enlaces):
    itemlist = []
    other = '' if tipo_enlaces == 'Online' else 'Descarga'

    data = httptools.downloadpage(url, add_referer=True).data
    if tipo_enlaces == 'Online':
        gg = httptools.downloadpage(item.url, add_referer=True).data
        bloque = scrapertools.find_single_match(gg, 'class="tab".*?button show')
        patron = 'a href="#([^"]+)'
        patron += '.*?language-ES-medium ([^"]+)'
        patron += '.*?</i>([^<]+)'
        matches = scrapertools.find_multiple_matches(bloque, patron)
        for scrapedopcion, scrapedlanguage, calidad in matches:
            google_url = scrapertools.find_single_match(bloque, 'id="%s.*?src="([^"]+)' % scrapedopcion)
            if "medium-es" in scrapedlanguage: language = "Esp"
            elif "medium-la" in scrapedlanguage: language = "Lat"
            elif "medium-en" in scrapedlanguage: language = "VO"
            elif "medium-vs" in scrapedlanguage: language = "VOSE"
            else: language = ''
            calidad = calidad.strip()

            itemlist.append(Item(channel = item.channel, action = 'play',
                                 title = 'Gvideo', url = google_url, server = 'gvideo', 
                                 language = language, quality = calidad, quality_num = puntuar_calidad(calidad), other = other
                           ))

    patron = '<div class="available-source".*?data-url="([^"]+)".*?class="language.*?title="([^"]+)"' \
             '.*?class="source-name.*?>\s*([^<]+)<.*?<span class="quality-text">([^<]+)<'
    matches = scrapertools.find_multiple_matches(data, patron)
    if matches:
        for scrapedurl, idioma, server, calidad in matches:
            if server == "streamin": server = "streaminto"
            if server == "waaw" or server == "miracine": server = "netutv"
            if server == "ul": server = "uploadedto"
            if server == "player": server = "vimpleru"
            if server == "povwideo": server = "powvideo"

            itemlist.append(Item(channel = item.channel, action = 'play',
                                 title = '', url = scrapedurl, server = server, 
                                 language = IDIOMAS[idioma], quality = calidad, quality_num = puntuar_calidad(calidad), other = other
                           ))

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    url = item.url.replace("http://miracine.tv/n/?etu=", "http://hqq.tv/player/embed_player.php?vid=")
    url = url.replace("streamcloud.eu/embed-", "streamcloud.eu/")
    if item.server:
        enlaces = servertools.findvideosbyserver(url, item.server)
    else:
        enlaces = servertools.findvideos(url)

    if len(enlaces) == 0: return itemlist
    
    itemlist.append(item.clone(url=enlaces[0][1], server=enlaces[0][2]))
    return itemlist
