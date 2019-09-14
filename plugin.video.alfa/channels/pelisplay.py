# -*- coding: utf-8 -*-
# -*- Channel PelisPlay -*-
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

__channel__ = "pelisplay"

host = "https://www.pelisplay.tv/"

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

IDIOMAS = {'Latino': 'LAT', 'Castellano': 'CAST', 'Subtitulado': 'VOSE'}
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['rapidvideo', 'streamango', 'fastplay', 'openload']


def mainlist(item):
    logger.info()
    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = [item.clone(title="Peliculas", action="menumovies", text_blod=True,
                           viewcontent='movie', viewmode="movie_with_plot", thumbnail=get_thumb("channels_movie.png")),

                item.clone(title="Series", action="menuseries", text_blod=True, extra='serie', mediatype="tvshow",
                           viewcontent='tvshow', viewmode="tvshow_with_plot",
                           thumbnail=get_thumb("channels_tvshow.png")),

                item.clone(title="Netflix", action="flixmenu", text_blod=True, extra='serie', mediatype="tvshow",
                           viewcontent='tvshows', viewmode="movie_with_plot",
                           fanart='https://i.postimg.cc/jjN85j8s/netflix-logo.png',
                           thumbnail='https://i.postimg.cc/Pxs9zYjz/image.png'),

                item.clone(title="Buscar", action="search", text_blod=True, extra='buscar',
                           thumbnail=get_thumb('search.png'), url=host + 'buscar')]
    autoplay.show_option(item.channel, itemlist)
    return itemlist


def menumovies(item):
    logger.info()
    itemlist = [item.clone(title="Estrenos", action="peliculas", text_blod=True,
                           viewcontent='movie', url=host + 'peliculas/estrenos', viewmode="movie_with_plot"),
                item.clone(title="Más Populares", action="peliculas", text_blod=True,
                           viewcontent='movie', url=host + 'peliculas?filtro=visitas', viewmode="movie_with_plot"),
                item.clone(title="Recíen Agregadas", action="peliculas", text_blod=True,
                           viewcontent='movie', url=host + 'peliculas?filtro=fecha_creacion', viewmode="movie_with_plot"),
                item.clone(title="Géneros", action="p_portipo", text_blod=True, extra='movie',
                           viewcontent='movie', url=host + 'peliculas', viewmode="movie_with_plot"),
                item.clone(title="Buscar", action="search", text_blod=True, extra='buscarp',
                           thumbnail=get_thumb('search.png'), url=host + 'peliculas')]
    return itemlist


def menuseries(item):
    logger.info()
    itemlist = [item.clone(title="Novedades", action="series", text_blod=True, extra='serie', mediatype="tvshow",
                           viewcontent='tvshow', url=host + 'series', viewmode="tvshow_with_plot"),

                item.clone(title="Más Vistas", action="series", text_blod=True, extra='serie', mediatype="tvshow",
                           viewcontent='tvshow', url=host + 'series?filtro=visitas', viewmode="tvshow_with_plot"),

                item.clone(title="Recíen Agregadas", action="series", text_blod=True, extra='serie', mediatype="tvshow",
                           viewcontent='tvshow', url=host + 'series?filtro=fecha_actualizacion', viewmode="tvshow_with_plot"),

                item.clone(title="Géneros", action="p_portipo", text_blod=True, extra='serie',
                           viewcontent='movie', url=host + 'series', viewmode="movie_with_plot"),
                item.clone(title="Buscar", action="search", text_blod=True, extra='buscars',
                           thumbnail=get_thumb('search.png'), url=host + 'series')]

    return itemlist


def flixmenu(item):
    logger.info()
    itemlist = [item.clone(title="Películas", action="flixmovies", text_blod=True, extra='movie', mediatype="movie",
                           viewcontent='movie', viewmode="tvshow_with_plot"),

                item.clone(title="Series", action="flixtvshow", text_blod=True, extra='serie', mediatype="tvshow",
                           viewcontent='tvshow', viewmode="tvshow_with_plot"),

                item.clone(title="Buscar", action="search", text_blod=True,
                           thumbnail=get_thumb('search.png'), url=host + 'buscar')]

    return itemlist


def flixmovies(item):
    logger.info()
    itemlist = [item.clone(title="Novedades", action="peliculas", text_blod=True, url=host + 'peliculas/netflix?filtro=fecha_actualizacion',
                           viewcontent='movie', viewmode="movie_with_plot"),
                item.clone(title="Más Vistas", action="peliculas", text_blod=True,
                           viewcontent='movie', url=host + 'peliculas/netflix?filtro=visitas', viewmode="movie_with_plot"),
                item.clone(title="Recíen Agregadas", action="peliculas", text_blod=True,
                           viewcontent='movie', url=host + 'peliculas/netflix?filtro=fecha_creacion', viewmode="movie_with_plot"),
                item.clone(title="Buscar", action="search", text_blod=True, extra="buscarp",
                           thumbnail=get_thumb('search.png'), url=host + 'peliculas/netflix')]
    return itemlist


def flixtvshow(item):
    logger.info()
    itemlist = [item.clone(title="Novedades", action="series", text_blod=True, url=host + 'series/netflix?filtro=fecha_actualizacion',
                           viewcontent='tvshow', viewmode="movie_with_plot"),
                item.clone(title="Más Vistas", action="series", text_blod=True,
                           viewcontent='tvshow', url=host + 'series/netflix?filtro=visitas', viewmode="movie_with_plot"),
                item.clone(title="Recíen Agregadas", action="series", text_blod=True,
                           viewcontent='tvshow', url=host + 'series/netflix?filtro=fecha_creacion', viewmode="movie_with_plot"),
                item.clone(title="Buscar", action="search", text_blod=True, extra="buscars",
                           thumbnail=get_thumb('search.png'), url=host + 'series/netflix')]
    return itemlist


def p_portipo(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;|<br>", "", data)
    action = ''
    patron = '<li class="item"><a href="([^"]+)" class="category">.*?'  # url
    patron += '<div class="[^<]+<img class="[^"]+" src="/([^"]+)"></div><div class="[^"]+">([^<]+)</div>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        if item.extra == 'movie':
            action = 'peliculas'
        elif item.extra == 'serie':
            action = 'series'
        itemlist.append(item.clone(action=action,
                                   title=scrapedtitle,
                                   url=scrapedurl,
                                   thumbnail=scrapedthumbnail
                                   ))
    itemlist.sort(key=lambda it: it.title)
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    # action = ''
    # contentType = ''
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;|<br>", "", data)
    patron = '<img class="posterentrada" src="/([^"]+)".*?'         # img
    patron += '<a href="([^"]+)">.*?'                               # url
    patron += '<p class="description_poster">.*?\(([^<]+)\)</p>.*?'  # year
    patron += '<div class="Description"> <div>([^<]+)</div>.*?'     # plot
    patron += '<strong>([^<]+)</strong></h4>'                       # title

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedthumbnail, scrapedurl, year, plot, scrapedtitle in matches:
        if 'serie' in scrapedurl:
            action = 'temporadas'
            contentType = 'tvshow'
            title = scrapedtitle + ' [COLOR blue](Serie)[/COLOR]'

        else:
            action = 'findvideos'
            contentType = 'movie'
            title = scrapedtitle

        if item.infoLabels['plot'] == '':
            item.plot = plot

        itemlist.append(Item(channel=item.channel, action=action, contentTitle=scrapedtitle, contentType=contentType,
                             infoLabels={"year": year}, thumbnail=host + scrapedthumbnail,
                             url=scrapedurl, title=title, plot=plot))

    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)

    pagination = scrapertools.find_single_match(
        data, '<li><a href="([^"]+)" rel="next">')

    if pagination:
        itemlist.append(Item(channel=__channel__, action="peliculas", title="» Siguiente »",
                             url=pagination, folder=True, text_blod=True, thumbnail=get_thumb("next.png")))

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = urlparse.urljoin(item.url, "?q={0}".format(texto))
    if item.extra == 'buscarp' or item.extra == 'buscars':
        item.url = urlparse.urljoin(item.url, "?buscar={0}".format(texto))

    try:
        if item.extra == 'buscars':
            return series(item)
        return peliculas(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria == 'peliculas':
            item.url = host + 'movies/'
        elif categoria == 'infantiles':
            item.url = host + "genre/animacion/"
        elif categoria == 'terror':
            item.url = host + "genre/terror/"
        else:
            return []

        itemlist = peliculas(item)
        if itemlist[-1].title == "» Siguiente »":
            itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def series(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;|<br>", "", data)
    patron = '<img class="portada" src="/([^"]+)"><[^<]+><a href="([^"]+)".*?'
    patron += 'class="link-title"><h2>([^<]+)</h2>'  # title
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedthumbnail, scrapedurl, scrapedtitle in matches:
        itemlist.append(Item(channel=__channel__, title=scrapedtitle, extra='serie',
                             url=scrapedurl, thumbnail=host + scrapedthumbnail,
                             contentSerieName=scrapedtitle, show=scrapedtitle,
                             action="temporadas", contentType='tvshow'))
    tmdb.set_infoLabels(itemlist, __modo_grafico__)

    pagination = scrapertools.find_single_match(
        data, '<li><a href="([^"]+)" rel="next">')

    if pagination:
        itemlist.append(Item(channel=__channel__, action="series", title="» Siguiente »", url=pagination,
                             thumbnail=get_thumb("next.png")))
    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;|<br>", "", data)
    patron = '<img class="posterentrada" src="/([^"]+)" alt="\w+\s*(\w+).*?'
    patron += 'class="abrir_temporada" href="([^"]+)">'  # img, season
    matches = re.compile(patron, re.DOTALL).findall(data)

    if len(matches) > 1:
        for scrapedthumbnail, temporada, url in matches:
            new_item = item.clone(action="episodesxseason", season=temporada, url=url,
                                  thumbnail=host + scrapedthumbnail, extra='serie')
            new_item.infoLabels['season'] = temporada
            new_item.extra = ""
            itemlist.append(new_item)
        tmdb.set_infoLabels(itemlist, __modo_grafico__)
        for i in itemlist:
            i.title = "%s. %s" % (
                i.infoLabels['season'], i.infoLabels['tvshowtitle'])
            if i.infoLabels['title']:
                # Si la temporada tiene nombre propio añadírselo al titulo del item
                i.title += " - %s" % (i.infoLabels['title'])
            if i.infoLabels.has_key('poster_path'):
                # Si la temporada tiene poster propio remplazar al de la serie
                i.thumbnail = i.infoLabels['poster_path']
        # itemlist.sort(key=lambda it: it.title)
    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(Item(channel=__channel__, title="Añadir esta serie a la videoteca", url=item.url,
                             action="add_serie_to_library", extra="episodios", show=item.show, category="Series",
                             text_color=color1, thumbnail=get_thumb("videolibrary_tvshow.png"), fanart=fanart_host))
        return itemlist
    else:
        return episodesxseason(item)


def episodios(item):
    logger.info()
    itemlist = []
    templist = temporadas(item)
    for tempitem in templist:
        itemlist += episodesxseason(tempitem)
    return itemlist


def episodesxseason(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;|<br>", "", data)
    post_link = '%sentradas/abrir_temporada' % host
    token = scrapertools.find_single_match(data, 'data-token="([^"]+)">')
    data_t = scrapertools.find_single_match(data, '<a data-s="[^"]+" data-t="([^"]+)"')
    data_s = scrapertools.find_single_match(data, '<a data-s="([^"]+)" data-t="[^"]+"')
    post = {'t': data_t, 's': data_s, '_token': token}
    json_data = httptools.downloadpage(post_link, post=post).json

    for element in json_data['data']['episodios']:
        scrapedname = element['titulo']
        episode = element['metas_formateadas']['nepisodio']
        season = element['metas_formateadas']['ntemporada']
        scrapedurl = element['url_directa']

        if 'season' in item.infoLabels and int(item.infoLabels['season']) != int(season):
            continue
        title = "%sx%s: %s" % (season, episode.zfill(2), scrapertools.unescape(scrapedname))
        new_item = item.clone(title=title, url=scrapedurl, action="findvideos", text_color=color3,
                              contentTitle=title, contentType="episode", extra='serie')
        if 'infoLabels' not in new_item:
            new_item.infoLabels = {}
        new_item.infoLabels['season'] = season
        new_item.infoLabels['episode'] = episode.zfill(2)
        itemlist.append(new_item)
    # TODO no hacer esto si estamos añadiendo a la videoteca
    if not item.extra:
        # Obtenemos los datos de todos los capítulos de la temporada mediante multihilos
        tmdb.set_infoLabels(itemlist, __modo_grafico__)
        for i in itemlist:
            if i.infoLabels['title']:
                # Si el capitulo tiene nombre propio añadírselo al titulo del item
                i.title = "%sx%s: %s" % (
                    i.infoLabels['season'], i.infoLabels['episode'], i.infoLabels['title'])
            if i.infoLabels.has_key('poster_path'):
                # Si el capitulo tiene imagen propia remplazar al poster
                i.thumbnail = i.infoLabels['poster_path']
    itemlist.sort(key=lambda it: int(it.infoLabels['episode']),
                  reverse=config.get_setting('orden_episodios', __channel__))
    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;|<br>", "", data)
    patron = 'data-player="([^"]+)"[^>]+>([^<]+)</div>.*?'
    patron += '<td class="[^"]+">([^<]+)</td><td class="[^"]+">([^<]+)</td>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for data_player, servername, quality, lang in matches:
        post_link = '%sentradas/procesar_player' % host
        token = scrapertools.find_single_match(data, 'data-token="([^"]+)">')
        post = {'data': data_player, 'tipo': 'videohost', '_token': token}
        json_data = httptools.downloadpage(post_link, post=post).json
        url = json_data['data']

        if 'pelisplay.tv/embed/' in url:
            new_data = httptools.downloadpage(url).data
            url = scrapertools.find_single_match(
                new_data, '"file":"([^"]+)",').replace('\\', '')

        elif 'fondo_requerido' in url:
            link = scrapertools.find_single_match(url, '=(.*?)&fondo_requerido').partition('&')[0]
            post_link = '%sprivate/plugins/gkpluginsphp.php' % host
            post = {'link': link}
            new_data2 = httptools.downloadpage(post_link, post=post).data
            url = scrapertools.find_single_match(new_data2, '"link":"([^"]+)"').replace('\\', '')

        lang = lang.lower().strip()
        idioma = {'latino': '[COLOR cornflowerblue](LAT)[/COLOR]',
                  'castellano': '[COLOR green](CAST)[/COLOR]',
                  'subtitulado': '[COLOR red](VOSE)[/COLOR]'}
        if lang in idioma:
            lang = idioma[lang]

        title = "Ver en: [COLOR yellowgreen](%s)[/COLOR] [COLOR yellow](%s)[/COLOR] %s" % (
            servername.title(), quality, lang)

        itemlist.append(item.clone(channel=__channel__, title=title,
                                   action='play', language=lang, quality=quality, url=url))

    itemlist = servertools.get_servers_itemlist(itemlist)
    itemlist.sort(key=lambda it: it.language, reverse=False)
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'serie':
        itemlist.append(Item(channel=__channel__, url=item.url, action="add_pelicula_to_library", extra="findvideos",
                             title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             thumbnail=get_thumb("videolibrary_movie.png"), contentTitle=item.contentTitle))
    return itemlist
