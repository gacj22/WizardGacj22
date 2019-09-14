# -*- coding: utf-8 -*-
# -*- Channel PelisHD24 -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
import sys
import urlparse

from channels import autoplay
from lib import generictools
from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from core import channeltools
from core import tmdb
from platformcode import config, logger
from channelselector import get_thumb

__channel__ = "pelishd24"

host = "https://pelishd24.com/"

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

IDIOMAS = {'Latino': 'LAT', 'Castellano': 'CAST', 'English': 'VOS'}
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
    itemlist = [item.clone(title="Todas", action="peliculas", thumbnail=get_thumb('all', auto=True),
                           text_blod=True, page=0, viewcontent='movies',
                           url=host + 'peliculas/', viewmode="movie_with_plot"),

                item.clone(title="Estrenos", action="peliculas", thumbnail=get_thumb('estrenos', auto=True),
                           text_blod=True, page=0, viewcontent='movies',
                           url=host + '?s=trfilter&trfilter=1&years=2018', viewmode="movie_with_plot"),

                item.clone(title="Más Vistas", action="peliculas", thumbnail=get_thumb('more watched', auto=True),
                           text_blod=True, page=0, viewcontent='movies',
                           url=host + 'mas-vistas/', viewmode="movie_with_plot"),

                item.clone(title="Más Votadas", action="peliculas", thumbnail=get_thumb('more voted', auto=True),
                           text_blod=True, page=0, viewcontent='movies',
                           url=host + 'peliculas-mas-votadas/', viewmode="movie_with_plot"),

                item.clone(title="Géneros", action="genres_atoz", thumbnail=get_thumb('genres', auto=True),
                           text_blod=True, page=0, viewcontent='movies',
                           url=host, viewmode="movie_with_plot"),

                item.clone(title="A-Z", action="genres_atoz", thumbnail=get_thumb('year', auto=True),
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
    action = ''
    contentType = ''
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\(.*?\)|\s{2}|&nbsp;", "", data)
    data = scrapertools.decodeHtmlentities(data)

    patron = '<article id="[^"]+" class="TPost[^<]+<a href="([^"]+)">.*?'  # url
    patron += '<img src="([^"]+)".*?'                                      # img
    patron += '</figure>(.*?)'                                             # tipo
    patron += '<h3 class="Title">([^<]+)</h3>.*?'                          # title
    patron += '<span class="Year">([^<]+)</span>.*?'                       # year

    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl, scrapedthumbnail, tipo, scrapedtitle, year in matches[item.page:item.page + 30]:
        title = ''
        if '/serie/' in scrapedurl:
            action = 'temporadas'
            contentType = 'tvshow'
            title = scrapedtitle + '[COLOR blue] (Serie)[/COLOR]'
        else:
            action = 'findvideos'
            contentType = 'movie'
            title = scrapedtitle

        itemlist.append(item.clone(channel=__channel__, action=action, text_color=color3, show=scrapedtitle,
                                   url=scrapedurl, infoLabels={'year': year}, extra='peliculas',
                                   contentTitle=scrapedtitle, thumbnail='https:' + scrapedthumbnail,
                                   title=title, context="buscar_trailer", contentType=contentType))

    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)

    if item.page + 30 < len(matches):
        itemlist.append(item.clone(page=item.page + 30,
                                   title="» Siguiente »", text_color=color3))
    else:
        next_page = scrapertools.find_single_match(data, '<a class="next page-numbers" href="([^"]+)">')
        if next_page:
            itemlist.append(item.clone(url=next_page, page=0, title="» Siguiente »", text_color=color3))

    return itemlist


def genres_atoz(item):
    logger.info()
    itemlist = []
    action = ''
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\(.*?\)|&nbsp;|<br>", "", data)
    data = scrapertools.decodeHtmlentities(data)

    if item.title == "A-Z":
        patron_todas = '<ul class="AZList"(.*?)</li></ul>'
        action = 'atoz'
    else:
        patron_todas = '<a href="#">GENERO</a>(.*?)</li></ul>'
        action = 'peliculas'

    data = scrapertools.find_single_match(data, patron_todas)
    patron = '<a href="([^"]+)">([^<]+)</a>'  # url, title
    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl, scrapedtitle in matches:
        itemlist.append(item.clone(title=scrapedtitle, url=scrapedurl, action=action))

    return itemlist


def atoz(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\(.*?\)|&nbsp;|<br>", "", data)
    data = scrapertools.decodeHtmlentities(data)

    patron = '<td class="MvTbImg"> <a href="([^"]+)".*?'                # url
    patron += '<img src="([^"]+)".*?'                                   # img
    patron += '<strong>([^<]+)</strong> </a></td><td>([^<]+)</td>.*?'   # title, year
    patron += '<span class="Qlty">([^<]+)</span>'                       # quality
    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl, scrapedthumbnail, scrapedtitle, year, quality in matches[item.page:item.page + 30]:
        title = ''
        action = ''
        if '/serie/' in scrapedurl:
            action = 'temporadas'
            contentType = 'tvshow'
            title = scrapedtitle + '[COLOR blue] (Serie)[/COLOR]'
        else:
            action = 'findvideos'
            contentType = 'movie'
            title = "%s [COLOR yellow]%s[/COLOR]" % (scrapedtitle, quality)

        itemlist.append(item.clone(channel=__channel__, action=action, text_color=color3, contentType=contentType,
                                   url=scrapedurl, infoLabels={'year': year}, extra='peliculas',
                                   contentTitle=scrapedtitle, thumbnail='https:' + scrapedthumbnail,
                                   title=title, context="buscar_trailer", show=scrapedtitle, ))

    if item.page + 30 < len(matches):
        itemlist.append(item.clone(page=item.page + 30,
                                   title="» Siguiente »", text_color=color3))
    else:
        next_page = scrapertools.find_single_match(data, '<a class="next page-numbers" href="([^"]+)">')
        if next_page:
            itemlist.append(item.clone(url=next_page, page=0, title="» Siguiente »", text_color=color3))

    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)

    return itemlist


def series(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\(.*?\)|&nbsp;|<br>", "", data)

    patron = '<article class="TPost C">\s*<a href="([^"]+)">.*?'  # url
    patron += '<img src="([^"]+)".*?'                             # img
    patron += '<h3 class="Title">([^<]+)</h3>'                    # title

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
    patron = '<div class="[^>]+>[^<]+<span>(.*?)</span> <i'  # numeros de temporadas

    matches = scrapertools.find_multiple_matches(data, patron)
    if len(matches) > 1:
        for scrapedseason in matches:
            no_disp = scrapertools.find_single_match(data,
                                               '<span>%s</span> <i(.*?)</table' % scrapedseason)
            if "no disponibles</td>" in no_disp:
                continue
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
    patron += host + 'episode/(.*?)/">([^<]+)</a>'         # title de episodios

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
                              contentType="episode", extra='episodios')
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
    patron = 'data-tplayernv="Opt(.*?)"><span>[^"<]+</span>(.*?)</li>'  # option, servername, lang - quality
    matches = re.compile(patron, re.DOTALL).findall(data)

    for option, quote in matches:
        patron = '<span>(.*?) -([^<]+)</span'
        match = re.compile(patron, re.DOTALL).findall(quote)
        lang, quality = match[0]
        quality = quality.strip()
        lang = lang.lower().strip()
        languages = {'latino': '[COLOR cornflowerblue](LAT)[/COLOR]',
                     'castellano': '[COLOR green](CAST)[/COLOR]',
                     'subtitulado': '[COLOR red](VOS)[/COLOR]'}

        if lang in languages:
            lang = languages[lang]

        url_1 = scrapertools.find_single_match(data,
                                               'id="Opt%s"><iframe width="560" height="315" src="([^"]+)"' % option)
        new_data = httptools.downloadpage(url_1).data
        new_data = re.sub(r"\n|\r|\t|amp;|\(.*?\)|\s{2}|&nbsp;", "", new_data)
        new_data = scrapertools.decodeHtmlentities(new_data)
        patron1 = '<iframe width="560" height="315" src="([^"]+)"'
        match1 = re.compile(patron1, re.DOTALL).findall(new_data)

        urls = scrapertools.find_single_match(new_data, '<iframe width="560" height="315" src="([^"]+)"')
        
        if 'pelishd24.com/?trhide' in urls:
            urls = urls.split("tid=")[1].strip()
            urls = urls[::-1].replace('&', '')
            try:
                urls = urls.decode('hex')
            except:
                continue
        elif 'stream.pelishd24' in urls:
            continue
        servername = servertools.get_server_from_url(urls)
        title = "Ver en: [COLOR yellowgreen](%s)[/COLOR] [COLOR yellow](%s)[/COLOR] %s" % (
            servername.title(), quality, lang)
        if 'embed.pelishd24.com' not in urls and 'embed.pelishd24.net' not in urls:
            itemlist.append(item.clone(action='play', title=title, url=urls, language=lang, quality=quality,
                                       text_color=color3))

        for url in match1:
            new_data = httptools.downloadpage(url).data
            new_data = re.sub(r"\n|\r|\t|amp;|\(.*?\)|\s{2}|&nbsp;", "", new_data)
            new_data = scrapertools.decodeHtmlentities(new_data)
            patron1 = '\["\d+","([^"]+)",\d+]'
            match1 = re.compile(patron1, re.DOTALL).findall(new_data)
            for url in match1:
                url = url.replace('\\', '')
                servername = servertools.get_server_from_url(url)
                if 'pelishd24.net' in url:
                    url = url.strip().replace("/api.", "/stream2.")
                    url_vip = url.replace("index.php", "hide.php")
                    if "/embed.php?" in url:
                        url_vip = url.replace("stream2.pelishd24.net/d/embed.php", "ww3.pelishd24.com/2/4/hide.php")
                    header_data = httptools.downloadpage(url_vip, headers={"Referer": url}, follow_redirects=False).headers
                    try:
                        url = header_data['location']
                        servername = 'gvideo'
                    except:
                        continue
                elif 'stream.pelishd24.com' in url:
                    continue
                title = "Ver en: [COLOR yellowgreen](%s)[/COLOR] [COLOR yellow](%s)[/COLOR] %s" % (
                    servername.title(), quality, lang)

                itemlist.append(item.clone(action='play', title=title, url=url, language=lang, quality=quality,
                                           text_color=color3))

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
