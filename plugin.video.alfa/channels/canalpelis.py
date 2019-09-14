# -*- coding: utf-8 -*-
# -*- Channel CanalPelis -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
import sys
import urllib
import urlparse, base64

from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from core import channeltools
from core import tmdb
from platformcode import config, logger
from channelselector import get_thumb

__channel__ = "canalpelis"

__modo_grafico__ = config.get_setting('modo_grafico', __channel__)

host = "https://cinexin.net/"

parameters = channeltools.get_channel_parameters(__channel__)
fanart_host = parameters['fanart']
thumbnail_host = parameters['thumbnail']

thumbnail = "https://raw.githubusercontent.com/Inter95/tvguia/master/thumbnails/%s.png"


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone(title="Peliculas", action="peliculas", thumbnail=get_thumb('movies', auto=True),
                               text_blod=True, page=0, viewcontent='movies',
                               url=host + 'peliculas/', viewmode="movie_with_plot"))

    itemlist.append(item.clone(title="Géneros", action="generos", thumbnail=get_thumb('genres', auto=True),
                               text_blod=True, page=0, viewcontent='movies',
                               url=host + 'peliculas/', viewmode="movie_with_plot"))

    itemlist.append(item.clone(title="Año de Estreno", action="year_release", thumbnail=get_thumb('year', auto=True),
                               text_blod=True, page=0, viewcontent='movies', url=host + 'peliculas/',
                               viewmode="movie_with_plot"))

    itemlist.append(item.clone(title="Series", action="series", extra='serie', url=host + 'series/',
                               viewmode="movie_with_plot", text_blod=True, viewcontent='movies',
                               thumbnail=get_thumb('tvshows', auto=True), page=0))
    
    itemlist.append(item.clone(title="Buscar", action="search", thumbnail=get_thumb('search', auto=True),
                               text_blod=True, url=host, page=0))


    return itemlist

#color en base al rating (evaluacion)
def color_rating(rating):
    try:
        rating_f = float(rating)
        if rating_f < 5: color = "tomato"
        elif rating_f >= 7: color = "palegreen"
        else: color = "grey"
    except:
        color = "grey"
    return color

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
    # logger.info(data)
    patron = '<div class="thumbnail animation-2"><a href="([^"]+)">.*?'  # url
    patron += '<img src="([^"]+)" alt="([^"]+)" />.*?'  # img and title
    patron += '<span class="([^"]+)".*?'  # tipo
    patron += '<span class="rating">IMDb (.*?)</span>' #rating
    patron += '<span class="year">([^<]+)</span>'  # year
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle, tipo, rating, year in matches[item.page:item.page + 30]:
        #para tomar la imagen completa
        scrapedthumbnail = scrapedthumbnail.replace("-150x150", "")
        
        title = scrapedtitle
        if not config.get_setting('unify'):
            #rating con color(evaluacion)
            rcolor = color_rating(rating)
            title += " [COLOR blue](%s)[/COLOR] [COLOR %s](%s)[/COLOR] [COLOR yellow][%s][/COLOR]" % (
                        year, rcolor, rating, quality)

        new_item = item.clone(title=title, url=scrapedurl, page=0,
                              infoLabels={"year": year},
                              thumbnail=scrapedthumbnail)
        
        #diferencia series y peliculas
        if tipo != "movies":
            new_item.action = "temporadas"
            new_item.contentSerieName = scrapedtitle
            if not config.get_setting('unify'):
                new_item.title += " [COLOR khaki](Serie)[/COLOR]"

        else:
            new_item.action = "findvideos"
            new_item.contentTitle=scrapedtitle

        itemlist.append(item.clone(title=title, url=scrapedurl, contentTitle=scrapedtitle,
                                   action=action, infoLabels={"year": year},
                                   thumbnail=scrapedthumbnail, page=0))

    #busquedas que coinciden con genero arrojan cientos de resultados
    if item.page + 30 < len(matches):
        itemlist.append(item.clone(page=item.page + 30, action="sub_search",
                                   title="» Siguiente »", text_color=color3))
    else:
        next_page = scrapertools.find_single_match(
            data, '<a class=\'arrow_pag\' href="([^"]+)">')

        if next_page:
            itemlist.append(item.clone(url=next_page, page=0,
                                       title="» Siguiente »"))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria == 'peliculas':
            item.url = host + 'peliculas/'
        elif categoria == 'infantiles':
            item.url = host + "genero/animacion/"
        elif categoria == 'terror':
            item.url = host + "genero/terror/"
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


def peliculas(item):
    logger.info()
    itemlist = []
    action = "findvideos"

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\(.*?\)|\s{2}|&nbsp;", "", data)
    patron = 'class="item movies">.*?<img src="([^"]+)" alt="([^"]+)">.*?'  # img, title.strip() movies
    patron += '<span class="icon-star2"></span> (.*?)</div>.*?'  # rating
    patron += '<span class="quality">([^<]+)</span>.*?'  # calidad
    patron += '<a href="([^"]+)"><div class="see"></div>.*?'  # url
    patron += '<span>(\d+)</span>'  # year

    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedthumbnail, scrapedtitle, rating, quality, scrapedurl, year in matches[item.page:item.page + 30]:

        if 'Próximamente' not in quality and '-XXX.jpg' not in scrapedthumbnail:
            #para tomar la imagen completa
            scrapedthumbnail = scrapedthumbnail.replace("-185x278", "")
            scrapedtitle = scrapedtitle.replace('Ver ', '').strip()
            contentTitle = scrapedtitle.partition(':')[0].partition(',')[0]
            

            title = scrapedtitle
            
            if not config.get_setting('unify'):
                #rating con color(evaluacion)
                rcolor = color_rating(rating)
                title += " [COLOR blue](%s)[/COLOR] [COLOR %s](%s)[/COLOR] [COLOR yellow][%s][/COLOR]" % (
                        year, rcolor, rating, quality)

            itemlist.append(item.clone(channel=__channel__, action="findvideos",
                                       url=scrapedurl, infoLabels={'year': year},
                                       contentTitle=contentTitle, thumbnail=scrapedthumbnail,
                                       title=title, context="buscar_trailer", quality=quality))

    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)

    if item.page + 30 < len(matches):
        itemlist.append(item.clone(page=item.page + 30,
                                   title="» Siguiente »"))
    else:
        next_page = scrapertools.find_single_match(
            data, "<span class=\"current\">\d+</span><a href='([^']+)'")

        if next_page:
            itemlist.append(item.clone(url=next_page, page=0,
                                       title="» Siguiente »"))

    for item in itemlist:
        if item.infoLabels['plot'] == '':
            datas = httptools.downloadpage(item.url).data
            datas = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", datas)
            item.fanart = scrapertools.find_single_match(
                datas, "<meta property='og:image' content='([^']+)' />")
            item.fanart = item.fanart.replace('w780', 'original')
            item.plot = scrapertools.find_single_match(datas, '</h4><p>(.*?)</p>')
            item.plot = scrapertools.htmlclean(item.plot)
            item.infoLabels['director'] = scrapertools.find_single_match(
                datas, '<div class="name"><a href="[^"]+">([^<]+)</a>')
            item.infoLabels['genre'] = scrapertools.find_single_match(
                datas, 'rel="tag">[^<]+</a><a href="[^"]+" rel="tag">([^<]+)</a>')

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<li class="cat-item cat-item-\d+"><a href="([^"]+)">([^<]+)</a> <i>([^<]+)</i></li>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle, cantidad in matches:
        if cantidad != '0':# and not '♦' in scrapedtitle:
            title = "%s (%s)" % (scrapedtitle, cantidad)
            itemlist.append(item.clone(channel=item.channel, action="peliculas", title=title, page=0,
                                       url=scrapedurl, viewmode="movie_with_plot"))

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
                                   url=scrapedurl, viewmode="movie_with_plot", extra='next'))

    return itemlist


def series(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\(.*?\)|&nbsp;|<br>", "", data)
    patron = '<div class="poster">.*?<img src="([^"]+)" alt="([^"]+)">'
    patron += '.*?<a href="([^"]+)">.*?IMDb: (.*?)</span>\s*'
    patron += '<span>(\d+)</span>.*?<div class="texto">([^<]+)</div>'

    matches = scrapertools.find_multiple_matches(data, patron)

    for thumbnail, stitle, url, rating, year, plot in matches[item.page:item.page + 30]:
        if plot == '':
            plot = scrapertools.find_single_match(data, '<div class="texto">([^<]+)</div>')
        
        stitle = stitle.strip()
        
        thumbnail = thumbnail.replace("-185x278", "")
        
        filter_list = {"first_air_date": year}
        filter_list = filter_list.items()

        rcolor = color_rating(rating)

        title = stitle
        if not config.get_setting('unify'):
            title += " [COLOR blue](%s)[/COLOR] [COLOR %s](%s)[/COLOR]" % (year, rcolor, rating)


        itemlist.append(item.clone(title=title, url=url, action="temporadas",
                                   contentSerieName=stitle, plot=plot,
                                   thumbnail=thumbnail, contentType='tvshow',
                                   infoLabels={'filtro': filter_list}))

    tmdb.set_infoLabels(itemlist, __modo_grafico__)

    if item.page + 30 < len(matches):
        itemlist.append(item.clone(page=item.page + 30,
                                   title="» Siguiente »"))
    else:
        next_page = scrapertools.find_single_match(
            data, '<link rel="next" href="([^"]+)" />')

        if next_page:
            itemlist.append(item.clone(url=next_page, page=0,
                                       title="» Siguiente »"))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    datas = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = "<span class='title'>([^<]+)<i>.*?"  # numeros de temporadas
    patron += "<img src='([^']+)'>"  # capitulos
    # logger.info(datas)
    matches = scrapertools.find_multiple_matches(datas, patron)
    if len(matches) > 1:
        for scrapedseason, scrapedthumbnail in matches:
            scrapedseason = " ".join(scrapedseason.split())
            temporada = scrapertools.find_single_match(scrapedseason, '(\d+)')
            new_item = item.clone(action="episodios", season=temporada, thumbnail=scrapedthumbnail, extra='temporadas')
            new_item.infoLabels['season'] = temporada
            new_item.extra = ""
            itemlist.append(new_item)

        tmdb.set_infoLabels(itemlist, __modo_grafico__)

        if not config.get_setting('unify'):
            for i in itemlist:
                i.title = "%s. %s" % (i.infoLabels['season'], i.infoLabels['tvshowtitle'])
                if i.infoLabels['title']:
                    # Si la temporada tiene nombre propio añadirselo al titulo del item
                    i.title += " - %s" % (i.infoLabels['title'])
                if i.infoLabels.has_key('poster_path'):
                    # Si la temporada tiene poster propio remplazar al de la serie
                    i.thumbnail = i.infoLabels['poster_path']

        itemlist.sort(key=lambda it: it.title)

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(Item(channel=__channel__, title="Añadir esta serie a la videoteca", url=item.url,
                             action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName,
                             thumbnail=thumbnail_host, fanart=fanart_host))

        return itemlist
    else:
        return episodios(item)


def episodios(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    datas = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = "<div class='imagen'>.*?"
    patron += "<div class='numerando'>(.*?)</div>.*?"
    patron += "<a href='([^']+)'>([^<]+)</a>"

    matches = scrapertools.find_multiple_matches(datas, patron)

    for scrapedtitle, scrapedurl, scrapedname in matches:
        scrapedtitle = scrapedtitle.replace('--', '0')
        patron = '(\d+) - (\d+)'
        match = re.compile(patron, re.DOTALL).findall(scrapedtitle)
        season, episode = match[0]

        if 'season' in item.infoLabels and int(item.infoLabels['season']) != int(season):
            continue

        title = "%sx%s: %s" % (season, episode.zfill(2), scrapertools.unescape(scrapedname))
        new_item = item.clone(title=title, url=scrapedurl, action="findvideos", 
                              contentTitle=title, contentType="episode")
        if 'infoLabels' not in new_item:
            new_item.infoLabels = {}

        new_item.infoLabels['season'] = season
        new_item.infoLabels['episode'] = episode.zfill(2)

        itemlist.append(new_item)

    # TODO no hacer esto si estamos añadiendo a la videoteca
    if not item.extra:
        # Obtenemos los datos de todos los capitulos de la temporada mediante multihilos
        tmdb.set_infoLabels(itemlist, __modo_grafico__)
        if not config.get_setting('unify'):
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

    # Opción "Añadir esta serie a la videoteca"
    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(Item(channel=__channel__, title="Añadir esta serie a la videoteca",
                             url=item.url, action="add_serie_to_library", extra="episodios",
                             contentSerieName=item.contentSerieName,
                             thumbnail=thumbnail_host, fanart=fanart_host))

    return itemlist


def findvideos(item):
    logger.info()
    import base64
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\(.*?\)|\s{2}|&nbsp;", "", data)

    patron = "data-post='(\d+)' data-nume='(\d+)'.*?img src='([^']+)'>"
    matches = re.compile(patron, re.DOTALL).findall(data)
    for id, option, lang in matches:
        lang = scrapertools.find_single_match(lang, '.*?/flags/(.*?).png')
        lang = lang.lower().strip()
        idioma = {'mx': '[COLOR cornflowerblue](LAT)[/COLOR]',
                  'es': '[COLOR green](CAST)[/COLOR]',
                  'en': '[COLOR red](VOSE)[/COLOR]',
                  'gb': '[COLOR red](VOSE)[/COLOR]'}
        if lang in idioma:
            lang = idioma[lang]
        else:
            lang = idioma['en']
        post = {'action': 'doo_player_ajax', 'post': id, 'nume': option, 'type': 'movie'}
        post = urllib.urlencode(post)
        test_url = '%swp-admin/admin-ajax.php' % host
        new_data = httptools.downloadpage(test_url, post=post, headers={'Referer': item.url}).data
        url = scrapertools.find_single_match(new_data, "src='([^']+)'")
        
        b64_url = scrapertools.find_single_match(url, "y=(.*?)&")
        if b64_url:
            url = base64.b64decode(b64_url)
        if url != '':
            itemlist.append(
                Item(channel=item.channel, action='play', language=lang, infoLabels=item.infoLabels,
                     url=url, title='Ver en: ' + '[COLOR yellowgreen]%s [/COLOR]' + lang))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())
    itemlist.sort(key=lambda it: it.language, reverse=False)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'episodios':
        itemlist.append(Item(channel=__channel__, url=item.url, action="add_pelicula_to_library", extra="findvideos",
                             title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             thumbnail=thumbnail_host, contentTitle=item.contentTitle))

    return itemlist
