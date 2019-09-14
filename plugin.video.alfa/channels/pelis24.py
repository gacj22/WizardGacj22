# -*- coding: utf-8 -*-
# -*- Channel CanalPelis -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
import sys
import urllib
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

__channel__ = "pelis24"

host = "https://www.pelis24.in/"

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


list_quality = ['HD 1080p', 'HDRip', 'TS-Screener']
list_servers = ['rapidvideo', 'streamango', 'openload', 'streamcherry']


def mainlist(item):
    logger.info()
    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = [item.clone(title="Novedades", action="peliculas", thumbnail=get_thumb('newest', auto=True),
                           text_blod=True, page=0, viewcontent='movies',
                           url=host + 'movies/', viewmode="movie_with_plot"),

                item.clone(title="Tendencias", action="peliculas", thumbnail=get_thumb('newest', auto=True),
                           text_blod=True, page=0, viewcontent='movies',
                           url=host + 'tendencias/?get=movies', viewmode="movie_with_plot"),

                item.clone(title="Estrenos", action="peliculas", thumbnail=get_thumb('estrenos', auto=True),
                           text_blod=True, page=0, viewcontent='movies',
                           url=host + 'genre/estrenos/', viewmode="movie_with_plot"),

                item.clone(title="A-Z", action="genresYears", thumbnail=get_thumb('alphabet', auto=True),
                           text_blod=True, page=0, viewcontent='movies',
                           url=host, viewmode="movie_with_plot"),

                item.clone(title="Buscar", action="search", thumbnail=get_thumb('search', auto=True),
                           text_blod=True, url=host, page=0)]

    autoplay.show_option(item.channel, itemlist)
    return itemlist


def search(item, texto):
    logger.info()

    texto = texto.replace(" ", "+")
    item.url = urlparse.urljoin(item.url, "?s={0}".format(texto))

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
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    data = scrapertools.find_single_match(data, '</h1>(.*?)</article></div></div>')
    patron = '<img src="([^"]+)" alt="([^"]+)".*?'
    patron += 'href="([^"]+)".*?'
    patron += 'year">(.*?)</span>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for  scrapedthumbnail, scrapedtitle, scrapedurl, year in matches:
        if 'tvshows' not in scrapedurl:
            itemlist.append(item.clone(title=scrapedtitle, url=scrapedurl, contentTitle=scrapedtitle,
                                       action="findvideos", infoLabels={"year": year},
                                       thumbnail=scrapedthumbnail, text_color=color3))

    paginacion = scrapertools.find_single_match(data, "<span class=\"current\">\d+</span><a href='([^']+)'")

    if paginacion:
        itemlist.append(Item(channel=item.channel, action="sub_search",
                             title="» Siguiente »", url=paginacion,
                             thumbnail='https://raw.githubusercontent.com/Inter95/tvguia/master/thumbnails/next.png'))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = scrapertools.decodeHtmlentities(data)
    bloq = scrapertools.find_single_match(data, '</h1>(.*?)resppages')
    # logger.info(data)

    # img, title
    patron = '<img src="([^"]+)" alt="([^"]+)".*?'
    patron += 'quality">([^<]+)<.*?'
    patron += 'href="([^"]+)".*?'
    patron += 'span>(\d{4})<'

    matches = scrapertools.find_multiple_matches(bloq, patron)

    for scrapedthumbnail, scrapedtitle, quality, scrapedurl, year in matches[item.page:item.page + 30]:
        title = '%s [COLOR yellowgreen](%s)[/COLOR]' % (scrapedtitle, quality)

        itemlist.append(Item(channel=__channel__, action="findvideos", text_color=color3,
                             url=scrapedurl, infoLabels={'year': year}, quality=quality,
                             contentTitle=scrapedtitle, thumbnail=scrapedthumbnail,
                             title=title, context="buscar_trailer"))

    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)

    if item.page + 30 < len(matches):
        itemlist.append(item.clone(page=item.page + 30,
                                   title="» Siguiente »", text_color=color3))
    else:
        next_page = scrapertools.find_single_match(data, '<link rel="next" href="([^"]+)" />')
        if next_page:
            itemlist.append(item.clone(url=next_page, page=0, title="» Siguiente »", text_color=color3))

    return itemlist


def genresYears(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\(.*?\)|&nbsp;|<br>", "", data)
    data = scrapertools.decodeHtmlentities(data)
    
    json_api, nonce = scrapertools.find_single_match(data, '"glossary":"([^"]+)","nonce":"([^"]+)"')
    json_api = json_api.replace("\\", "")
    patron_todas = '<ul class="glossary"(.*?)</li></ul></div>'
    bloq = scrapertools.find_single_match(data, patron_todas)
    patron = 'data-glossary="([^"]+)">([^<]+)</a>'  # url, title
    matches = scrapertools.find_multiple_matches(bloq, patron)

    for scrapedurl, scrapedtitle in matches:
        url = json_api+"?term=%s&nonce=%s&type=movies" % (scrapedurl, nonce)
        itemlist.append(item.clone(title=scrapedtitle, url=url, action="api_peliculas"))
    return itemlist

def api_peliculas(item):
    logger.info()
    itemlist = []
    json_data = httptools.downloadpage(item.url).json

    for _id, val in json_data.items():
        url = val['url']
        title = val['title']
        thumbnail = val['img']
        try:
            year = val['year']
        except:
            year = "-"
        itemlist.append(Item(channel=__channel__, action="findvideos", text_color=color3,
                             url=url, infoLabels={'year': year},
                             contentTitle=title, thumbnail=thumbnail,
                             title=title, context="buscar_trailer"))
    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
    return itemlist

def year_release(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    # logger.info(data)
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
    # logger.info(data)

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
    # logger.info(data)
    patron = '<div class="[^>]+>[^<]+<span>(.*?)</span> <i'  # numeros de temporadas

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

        itemlist.sort(key=lambda it: int(it.infoLabels['season']))

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(Item(channel=__channel__, title="Añadir esta serie a la videoteca", url=item.url,
                             action="add_serie_to_library", extra="episodios", show=item.show, category="Series",
                             text_color=color1, thumbnail=thumbnail_host, fanart=fanart_host))

        return itemlist
    else:
        return episodios(item)


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
    list_language = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|amp;|#038;|\(.*?\)|\s{2}|&nbsp;", "", data)
    data = scrapertools.decodeHtmlentities(data)
    # logger.info(data)

    # patron1 = 'data-tplayernv="Opt(.*?)"><span>(.*?)</span><span>(.*?)</span>' # option, server, lang - quality
    patron = 'href="#option-(.*?)"><span class="dt_flag"><img src="[^"]+"></span>([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    # urls = re.compile(patron2, re.DOTALL).findall(data)

    for option, lang in matches:
        url = scrapertools.find_single_match(
            data, '<div id="option-%s" class="[^"]+"><iframe class="metaframe rptss" src="([^"]+)"' % option)
        lang = lang.lower().strip()
        languages = {'latino': '[COLOR cornflowerblue](LAT)[/COLOR]',
                     'castellano': '[COLOR green](CAST)[/COLOR]',
                     'español': '[COLOR green](CAST)[/COLOR]',
                     'sub español': '[COLOR grey](VOSE)[/COLOR]',
                     'sup espaÑol': '[COLOR grey](VOSE)[/COLOR]',
                     'sub': '[COLOR grey](VOSE)[/COLOR]',
                     'ingles': '[COLOR red](VOS)[/COLOR]'}
        if lang in languages:
            lang = languages[lang]
        #tratando con los idiomas
        language = scrapertools.find_single_match(lang, '\((\w+)\)')
        list_language.append(language)
        
        server = servertools.get_server_from_url(url)
        title = "»» [COLOR yellow](%s)[/COLOR] [COLOR goldenrod](%s)[/COLOR] %s ««" % (
            server.title(), item.quality, lang)
        # if 'google' not in url and 'directo' not in server:

        itemlist.append(item.clone(action='play', url=url, title=title, language=language, text_color=color3))

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
