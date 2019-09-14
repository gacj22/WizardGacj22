# -*- coding: utf-8 -*-

import re
import sys
import urllib
import urlparse

from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from core import tmdb
from platformcode import config, logger


host = "https://pedropolis.tv/"


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action="mainlist_pelis", title="Películas", url=host ))
    itemlist.append(item.clone( action="mainlist_series", title="Series", url=host + 'tvshows/' ))
    itemlist.append(item.clone( action="search", title="Buscar..." ))
    
    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action="peliculas", title="Todas", url=host + 'pelicula/' ))
    itemlist.append(item.clone( action="peliculas", title="Más Vistas", url=host + 'tendencias/?get=movies' ))
    itemlist.append(item.clone( action="peliculas", title="Mejor Valoradas", url=host + 'calificaciones/?get=movies' ))
    itemlist.append(item.clone( action='peliculas', title='Estrenos', url=host + 'genero/estrenos/' ))
    itemlist.append(item.clone( action="generos", title="Por género", search_type="movie" ))
    itemlist.append(item.clone( action="anyos", title="Por año", search_type="movie" ))
    itemlist.append(item.clone( action="search", title="Buscar película...", search_type='movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action="series", title="Todas", url=host + 'serie/' ))
    itemlist.append(item.clone( action="series", title="Más Vistas", url=host + 'tendencias/?get=tv' ))
    itemlist.append(item.clone( action="series", title="Mejor Valoradas", url=host + 'calificaciones/?get=tv' ))
    itemlist.append(item.clone( action="search", title="Buscar serie...", search_type='tvshow' ))

    return itemlist



def generos(item):
    logger.info()
    itemlist = []
    if item.search_type != 'movie': return []

    data = httptools.downloadpage(host + 'genero/estrenos/').data
    bloque = scrapertools.find_single_match(data, '(?is)Categorías.*?</ul>')
    patron = 'href="([^"]+)">([^"<]+)</a> <i>(\d+)</i>'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for scrapedurl, scrapedtitle, scrapednum in matches:
        if '/estrenos/' in scrapedurl: continue # se muestra en el menú principal
        itemlist.append(item.clone( action = "peliculas", title = '%s (%s)' % (scrapedtitle, scrapednum), url = scrapedurl ))

    return itemlist

def anyos(item):
    logger.info()
    itemlist = []
    if item.search_type != 'movie': return []

    data = httptools.downloadpage(host + 'genero/estrenos/').data
    bloque = scrapertools.find_single_match(data, '(?is)Películas Por año.*?</ul>')
    patron = 'href="([^"]+)">([^"<]+)'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for scrapedurl, scrapedtitle in matches:
        itemlist.append(item.clone( action = "peliculas", title = scrapedtitle, url = scrapedurl ))

    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)

    patron = '<div class="poster"> <img src="([^"]+)" alt="([^"]+)">.*?'            # img, title
    patron += '<div class="rating"><span class="[^"]+"></span>([^<]+).*?'           # rating
    patron += '<span class="quality">([^<]+)</span></div> <a href="([^"]+)">.*?'    # calidad, url
    patron += '<span class="flag" style="([^"]+)".*?'                               # lang
    patron += '<span>([^<]+)</span>.*?'                                             # year

    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedthumbnail, scrapedtitle, rating, quality, scrapedurl, scrapedlang, year in matches:
        scrapedtitle = scrapedtitle.replace('Ver ', '').partition(' /')[0].partition(':')[0].replace('Español Latino', '').strip()
        lang = scrapertools.find_single_match(scrapedlang, '/([a-zA-Z]+)\.png')
        lang = 'Esp' if lang == 'es' else 'Lat' if lang == 'mx' else lang

        itemlist.append(Item(channel=item.channel, action="findvideos", contentType='movie', contentTitle=scrapedtitle,
                             infoLabels={"year":year, "rating":rating}, thumbnail=scrapedthumbnail,
                             url=scrapedurl, qualities=quality, languages=lang, title=scrapedtitle))

    tmdb.set_infoLabels(itemlist)

    pagination = scrapertools.find_single_match(data, "<span class=\"current\">\d+</span><a href='([^']+)'")
    if pagination:
        itemlist.append(item.clone(title="Página siguiente >>", url=pagination))


    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = urlparse.urljoin(host, "?s={0}".format(texto))
    if item.search_type == '': item.search_type = 'all'
    try:
        return sub_search(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []


def sub_search(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data, 'Resultados encontrados.*?class="widget widget_fbw_id')
    patron  = '(?is)<a href="([^"]+)">.*?'
    patron += '<img src="([^"]+)".*?'
    patron += 'alt="([^"]+)" />.*?'  # url, img, title
    patron += '<span class="[^"]+">([^<]+)</span>.*?'  # tipo
    patron += '<span class="year">([^"]+)'  # year
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for scrapedurl, scrapedthumbnail, scrapedtitle, tipo, year in matches:
        if tipo == ' Serie ':
            contentType = 'tvshow'
            action = 'temporadas'
        else:
            contentType = 'movie'
            action = 'findvideos'
        sufijo = '' if item.search_type != 'all' else contentType

        if item.search_type == 'all' or item.search_type == contentType:
            itemlist.append(item.clone(title=scrapedtitle, url=scrapedurl, contentTitle=scrapedtitle, extra='buscar',
                                       action=action, infoLabels={"year": year}, contentType=contentType, fmt_sufijo=sufijo,
                                       thumbnail=scrapedthumbnail, contentSerieName=scrapedtitle))

    tmdb.set_infoLabels(itemlist)

    pagination = scrapertools.find_single_match(data, '<link rel="next" href="([^"]+)" />')
    if pagination:
        itemlist.append(Item(channel=item.channel, action="sub_search", title="Página siguiente >>", url=pagination))

    return itemlist



def series(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '<div class="poster"> <img src="([^"]+)"'
    patron += ' alt="([^"]+)">.*?'
    patron += '<a href="([^"]+)">'
    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedthumbnail, scrapedtitle, scrapedurl in matches:
        scrapedtitle = scrapedtitle.replace('&#8217;', "'")
        itemlist.append(Item(channel=item.channel, action="temporadas", title=scrapedtitle,
                             url=scrapedurl, thumbnail=scrapedthumbnail,
                             contentSerieName=scrapedtitle, contentType='tvshow'))

    tmdb.set_infoLabels(itemlist)

    pagination = scrapertools.find_single_match(data, "<span class=\"current\">\d+</span><a href='([^']+)'")
    if pagination:
        itemlist.append(item.clone(title="Página siguiente >>", url=pagination))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<span class="title">([^<]+)<i>'  # season
    matches = scrapertools.find_multiple_matches(data, patron)
    if len(matches) > 1:
        for scrapedseason in matches:
            scrapedseason = " ".join(scrapedseason.split())
            temporada = scrapertools.find_single_match(scrapedseason, '(\d+)')
            itemlist.append(item.clone( action="episodios", title=scrapedseason, contentType='season', contentSeason=temporada ))

        tmdb.set_infoLabels(itemlist)

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
    data = httptools.downloadpage(item.url).data
    patron = '<div class="imagen"><a href="([^"]+)">.*?'  # url
    patron += '<div class="numerando">(.*?)</div>.*?'     # numerando cap
    patron += '<a href="[^"]+">([^<]+)</a>'               # title de episodios
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle, scrapedname in matches:
        scrapedtitle = scrapedtitle.replace('--', '0')
        patron = '(\d+) - (\d+)'
        match = re.compile(patron, re.DOTALL).findall(scrapedtitle)
        season, episode = match[0]
        if 'season' in item.infoLabels and int(item.infoLabels['season']) != int(season):
            continue
        title = "%sx%s: %s" % (season, episode.zfill(2), scrapertools.unescape(scrapedname))

        itemlist.append(item.clone(title=title, url=scrapedurl, action="findvideos",
                                   contentType="episode", contentSeason=season, contentEpisodeNumber=episode))

    tmdb.set_infoLabels(itemlist)

    itemlist.sort(key=lambda it: int(it.infoLabels['episode']), reverse=False)

    return itemlist



def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<div id="option-(\d+)".*?<iframe.*?src="([^"]+)".*?</iframe>'  # lang, url
    matches = re.compile(patron, re.DOTALL).findall(data)
    for option, url in matches:
        lang = scrapertools.find_single_match(data, '<li><a class="options" href="#option-%s">.*?</b>(.*?)<span' % option)
        lang = lang.lower().strip()
        idioma = {'latino': 'Lat',
                  'drive': 'Lat',
                  'castellano': 'Esp',
                  'español': 'Esp',
                  'subtitulado': 'VOS',
                  'ingles': 'Eng'}
        if lang in idioma:
            lang = idioma[lang]

        if "bit.ly" in url: # obtenemos redirecionamiento de shorturl en caso de coincidencia
            url = httptools.downloadpage(url, follow_redirects=False, only_headers=True).headers.get("location", "")

        itemlist.append(Item( channel = item.channel, action = 'play', url = url, title = item.title,
                              language = lang, quality = item.qualities ))

    itemlist = servertools.get_servers_itemlist(itemlist)
    itemlist.sort(key=lambda it: it.language, reverse=False)

    return itemlist
