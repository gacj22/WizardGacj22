# -*- coding: utf-8 -*-
# -*- Channel Cine24h -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
import sys
import urlparse

from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from core import channeltools
from core import tmdb
from platformcode import config, logger
from channelselector import get_thumb
from lib import unshortenit

__channel__ = "cine24h"

host = "https://cine24h.net/"

try:
    __modo_grafico__ = config.get_setting('modo_grafico', __channel__)
    __perfil__ = int(config.get_setting('perfil', __channel__))
except:
    __modo_grafico__ = True
    __perfil__ = 0

# Fijar perfil de color
perfil = [['0xFFFFE6CC', '0xFFFFCE9C', '0xFF994D00', '0xFFFE2E2E', '0xFFFFD700'],
          ['0xFFA5F6AF', '0xFF5FDA6D', '0xFF11811E', '0xFFFE2E2E', '0xFFFFD700'],
          ['0xFF58D3F7', '0xFF2E9AFE', '0xFF2E64FE', '0xFFFE2E2E', '0xFFFFD700']]
if __perfil__ < 3:
    color1, color2, color3, color4, color5 = perfil[__perfil__]
else:
    color1 = color2 = color3 = color4 = color5 = ""

headers = [['User-Agent', 'Mozilla/50.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0'],
           ['Referer', host]]

parameters = channeltools.get_channel_parameters(__channel__)
fanart_host = parameters['fanart']
thumbnail_host = parameters['thumbnail']

IDIOMAS = {'Latino': 'LAT', 'Castellano': 'CAST'}
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['rapidvideo', 'streamango', 'openload', 'streamcherry']


def mainlist(item):
    logger.info()
    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = [item.clone(title="Peliculas", action="menumovies", text_blod=True,
                           viewcontent='movies', viewmode="movie_with_plot", thumbnail=get_thumb('movies', auto=True)),

                item.clone(title="Series", action="series", extra='serie', url=host + 'series/',
                           viewmode="movie_with_plot", text_blod=True, viewcontent='movies',
                           thumbnail=get_thumb('tvshows', auto=True), page=0),

                item.clone(title="Buscar", action="search", thumbnail=get_thumb('search', auto=True),
                           text_blod=True, url=host, page=0)]

    autoplay.show_option(item.channel, itemlist)
    return itemlist


def menumovies(item):
    logger.info()
    itemlist = [item.clone(title="Novedades", action="peliculas", thumbnail=get_thumb('newest', auto=True),
                           text_blod=True, page=0, viewcontent='movies',
                           url=host + 'peliculas/', viewmode="movie_with_plot"),

                item.clone(title="Estrenos", action="peliculas", thumbnail=get_thumb('estrenos', auto=True),
                           text_blod=True, page=0, viewcontent='movies',
                           url=host + '?s=trfilter&trfilter=1&years%5B%5D=2018', viewmode="movie_with_plot"),

                item.clone(title="Más Vistas", action="peliculas", thumbnail=get_thumb('more watched', auto=True),
                           text_blod=True, page=0, viewcontent='movies',
                           url=host + 'peliculas-mas-vistas/', viewmode="movie_with_plot"),

                item.clone(title="Géneros", action="genresYears", thumbnail=get_thumb('genres', auto=True),
                           text_blod=True, page=0, viewcontent='movies',
                           url=host, viewmode="movie_with_plot"),

                item.clone(title="Estrenos por Año", action="genresYears", thumbnail=get_thumb('year', auto=True),
                           text_blod=True, page=0, viewcontent='movies', url=host,
                           viewmode="movie_with_plot"),

                item.clone(title="Buscar", action="search", thumbnail=get_thumb('search', auto=True),
                           text_blod=True, url=host, page=0, extra='buscarP')]

    return itemlist


def search(item, texto):
    logger.info()

    texto = texto.replace(" ", "+")
    item.url = urlparse.urljoin(item.url, "?s={0}".format(texto))

    try:
        return peliculas(item)

    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []


def peliculas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\(.*?\)|\s{2}|&nbsp;", "", data)
    data = scrapertools.decodeHtmlentities(data)
    patron = '<article id="[^"]+" class="TPost[^<]+<a href="([^"]+)">.*?'  # url
    patron += '<img src="([^"]+)".*?'  # img
    patron += '</figure>(.*?)'  # tipo
    patron += '<h3 class="Title">([^<]+)</h3>.*?'  # title
    patron += '<span class="Year">([^<]+)</span>.*?'  # year

    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl, scrapedthumbnail, tipo, scrapedtitle, year in matches[item.page:item.page + 30]:
        if item.title == 'Buscar' and 'serie' in scrapedurl:
            action = 'temporadas'
            contentType = 'tvshow'
            title = scrapedtitle + '[COLOR blue] (Serie)[/COLOR]'
        else:
            action = 'findvideos'
            contentType = 'movie'
            title = scrapedtitle

        itemlist.append(Item(channel=__channel__, action=action, text_color=color3, show=scrapedtitle,
                             url=scrapedurl, infoLabels={'year': year}, contentType=contentType,
                             contentTitle=scrapedtitle, thumbnail='https:' + scrapedthumbnail,
                             title=title, context="buscar_trailer"))

    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)

    if item.page + 30 < len(matches):
        itemlist.append(item.clone(page=item.page + 30,
                                   title="» Siguiente »", text_color=color3))
    else:
        next_page = scrapertools.find_single_match(data, '<a class="next page-numbers" href="([^"]+)">')
        if next_page:
            itemlist.append(item.clone(url=next_page, page=0, title="» Siguiente »", text_color=color3))

    return itemlist


def genresYears(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\(.*?\)|&nbsp;|<br>", "", data)
    data = scrapertools.decodeHtmlentities(data)

    if item.title == "Estrenos por Año":
        patron_todas = 'ESTRENOS</a>(.*?)</i> Géneros'
    else:
        patron_todas = 'Géneros</a>(.*?)</li></ul></li>'

    data = scrapertools.find_single_match(data, patron_todas)
    patron = '<a href="([^"]+)">([^<]+)</a>'  # url, title
    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl, scrapedtitle in matches:
        itemlist.append(item.clone(title=scrapedtitle, url=scrapedurl, action="peliculas"))

    return itemlist


def year_release(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<li><a href="([^"]+)">([^<]+)</a></li>'  # url, title
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        itemlist.append(item.clone(channel=item.channel, action="peliculas", title=scrapedtitle, page=0,
                                   url=scrapedurl, text_color=color3, viewmode="movie_with_plot", extra='next'))

    return itemlist


def series(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\(.*?\)|&nbsp;|<br>", "", data)
    patron = '<article class="TPost C TPostd">\s*<a href="([^"]+)">.*?'  # url
    patron += '<img src="([^"]+)".*?'  # img
    patron += '<h3 class="Title">([^<]+)</h3>'  # title

    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl, scrapedthumbnail, scrapedtitle in matches[item.page:item.page + 30]:
        itemlist.append(item.clone(title=scrapedtitle, url=scrapedurl, action="temporadas",
                                   contentSerieName=scrapedtitle, show=scrapedtitle,
                                   thumbnail='https:' + scrapedthumbnail, contentType='tvshow'))

    tmdb.set_infoLabels(itemlist, __modo_grafico__)

    if item.page + 30 < len(matches):
        itemlist.append(item.clone(page=item.page + 30,
                                   title="» Siguiente »", text_color=color3))
    else:
        next_page = scrapertools.find_single_match(data, '<a class="next page-numbers" href="([^"]+)">')

        if next_page:
            itemlist.append(item.clone(url=next_page, page=0,
                                       title="» Siguiente »", text_color=color3))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<div class="[^>]+>[^<]+<span>(\d+)</span> <i'  # numeros de temporadas

    matches = scrapertools.find_multiple_matches(data, patron)
    if len(matches) > 1:
        for scrapedseason in matches:
            new_item = item.clone(action="episodios", season=scrapedseason, extra='temporadas')
            new_item.infoLabels['season'] = scrapedseason
            new_item.extra = ""
            itemlist.append(new_item)

        tmdb.set_infoLabels(itemlist, __modo_grafico__)

        for i in itemlist:
            i.title = "%s. %s" % (i.infoLabels['season'], i.infoLabels['tvshowtitle'])
            if i.infoLabels['title']:
                # Si la temporada tiene nombre propio añadirselo al titulo del item
                i.title += " - %s" % (i.infoLabels['title'])
            if i.infoLabels.has_key('poster_path'):
                # Si la temporada tiene poster propio remplazar al de la serie
                i.thumbnail = i.infoLabels['poster_path']

        itemlist.sort(key=lambda it: it.infoLabels['season'])
    
    else:
        return episodios(item)

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(Item(channel=__channel__, title="Añadir esta serie a la videoteca", url=item.url,
                             action="add_serie_to_library", extra="episodios", show=item.show, category="Series",
                             text_color=color1, thumbnail=thumbnail_host, fanart=fanart_host))

        return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<td class="MvTbImg B"><a href="([^"]+)".*?'  # url
    patron += '<td class="MvTbTtl"><a href="https://cine24h.net/episode/(.*?)/">([^<]+)</a>'  # title de episodios

    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl, scrapedtitle, scrapedname in matches:
        scrapedtitle = scrapedtitle.replace('--', '0')
        patron = '(\d+)x(\d+)'
        match = re.compile(patron, re.DOTALL).findall(scrapedtitle)
        season, episode = match[0]

        if 'season' in item.infoLabels and int(item.infoLabels['season']) != int(season):
            continue

        title = "%sx%s: %s" % (season, episode.zfill(2), scrapedname)
        new_item = item.clone(title=title, url=scrapedurl, action="findvideos", text_color=color3, contentTitle=title,
                              contentType="episode")
        if 'infoLabels' not in new_item:
            new_item.infoLabels = {}

        new_item.infoLabels['season'] = season
        new_item.infoLabels['episode'] = episode.zfill(2)

        itemlist.append(new_item)

    # TODO no hacer esto si estamos añadiendo a la videoteca
    if not item.extra:
        # Obtenemos los datos de todos los capitulos de la temporada mediante multihilos
        tmdb.set_infoLabels(itemlist, __modo_grafico__)
        for i in itemlist:
            if i.infoLabels['title']:
                # Si el capitulo tiene nombre propio añadirselo al titulo del item
                i.title = "%sx%s %s" % (i.infoLabels['season'], i.infoLabels[
                    'episode'], i.infoLabels['title'])
            if i.infoLabels.has_key('poster_path'):
                # Si el capitulo tiene imagen propia remplazar al poster
                i.thumbnail = i.infoLabels['poster_path']

    itemlist.sort(key=lambda it: int(it.infoLabels['episode']),
                  reverse=config.get_setting('orden_episodios', __channel__))
    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
    # Opción "Añadir esta serie a la videoteca"
    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(Item(channel=__channel__, title="Añadir esta serie a la videoteca", url=item.url,
                             action="add_serie_to_library", extra="episodios", show=item.show, category="Series",
                             text_color=color1, thumbnail=thumbnail_host, fanart=fanart_host))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|amp;|#038;|\(.*?\)|\s{2}|&nbsp;", "", data)
    data = scrapertools.decodeHtmlentities(data)
    patron = 'data-tplayernv="Opt(.*?)"><span>(.*?)</span>(.*?)</li>'  # option, server, lang - quality
    matches = re.compile(patron, re.DOTALL).findall(data)

    for option, servername, quote in matches:
        patron = '<span>(.*?) -([^<]+)</span'
        match = re.compile(patron, re.DOTALL).findall(quote)
        lang, quality = match[0]
        quality = quality.strip()
        headers = {'Referer': item.url}
        url_1 = scrapertools.find_single_match(data,
                                               'id="Opt%s"><iframe width="560" height="315" src="([^"]+)"' % option)
        new_data = httptools.downloadpage(url_1, headers=headers).data
        new_data = re.sub(r"\n|\r|\t|amp;|\(.*?\)|\s{2}|&nbsp;", "", new_data)
        new_data = scrapertools.decodeHtmlentities(new_data)
        url2 = scrapertools.find_single_match(new_data, '<iframe width="560" height="315" src="([^"]+)"')
        url = url2 + '|%s' % url_1
        if 'rapidvideo' in url2 or "verystream" in url2:
            url = url2

        lang = lang.lower().strip()
        languages = {'latino': '[COLOR cornflowerblue](LAT)[/COLOR]',
                     'español': '[COLOR green](CAST)[/COLOR]',
                     'subespañol': '[COLOR red](VOS)[/COLOR]',
                     'sub': '[COLOR red](VOS)[/COLOR]'}
        if lang in languages:
            lang = languages[lang]

        servername = servertools.get_server_from_url(url)

        title = "Ver en: [COLOR yellowgreen](%s)[/COLOR] [COLOR yellow](%s)[/COLOR] %s" % (
            servername.title(), quality, lang)

        itemlist.append(item.clone(action='play', url=url, title=title, language=lang, quality=quality,
                                   text_color=color3))

    patron1 = 'href="([^>]+)" class="Button STPb">.*?<img src="([^>]+)".*?alt="Imagen (.*?)">.*?<span>(\d+)'  # option, server, lang - quality
    matches1 = re.compile(patron1, re.DOTALL).findall(data)
    for url, img, lang, quality in matches1:
        if "cine24h" in url or "short." in url:
            continue
        else:    
            url, c = unshortenit.unshorten_only(url)
            if "short." in url:
                continue
            elif "google." in url:
                for item in itemlist:
                    if "google." in item.url:
                        item.url = url
                    #logger.error("url=%s" % item.url)
    itemlist = servertools.get_servers_itemlist(itemlist)

    itemlist.sort(key=lambda it: it.language, reverse=False)

    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'episodios':
        itemlist.append(Item(channel=__channel__, url=item.url, action="add_pelicula_to_library", extra="findvideos",
                             title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             thumbnail=thumbnail_host, contentTitle=item.contentTitle))

    return itemlist
