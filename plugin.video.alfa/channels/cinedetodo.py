# -*- coding: utf-8 -*-
# -*- Channel CineDeTodo -*-
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

__channel__ = "cinedetodo"

host = 'https://www.cinedetodo.org/'


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone(title="Peliculas", action="peliculas", thumbnail=get_thumb('movies', auto=True),
                               text_blod=True, page=0, url=host + 'peliculas/'))

    itemlist.append(item.clone(title="Géneros", action="generos", thumbnail=get_thumb('genres', auto=True),
                               text_blod=True, page=0, url=host + 'peliculas/'))

    itemlist.append(item.clone(title="Año de Estreno", action="year_release", thumbnail=get_thumb('year', auto=True),
                               text_blod=True, page=0,url=host + 'peliculas/'))

    itemlist.append(item.clone(title="Series", action="peliculas", url=host + 'series/',
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
        else: color = "darkgrey"
    except:
        color = "darkgrey"
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
    action = "findvideos"
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\(.*?\)|\s{2}|&nbsp;", "", data)

    patron = '<div class="thumbnail animation-2"> <a href="([^"]+)">.*?'  # url
    patron += '<img src="([^"]+)" alt="([^"]+)" />.*?'  # img and title
    patron += '<span class="([^"]+)".*?'  # tipo
    patron += '<span class="rating">IMDb (.*?)</span>.*?' #rating
    patron += '<span class="year">([^<]+)</span>'  # year
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle, tipo, rating, year in matches[item.page:item.page + 30]:
        #para tomar la imagen completa
        scrapedthumbnail = re.sub("(w\d+/)", "original/", scrapedthumbnail)
        title = scrapedtitle.partition(' | ')[0].rstrip()
        try:
            contentTitle = scrapedtitle.split(' | ')[1].rstrip()
        except:
            contentTitle = title
        rcolor = color_rating(rating)
        title = "%s [COLOR blue](%s)[/COLOR] [COLOR %s](%s)[/COLOR]" % (title, year, rcolor, rating)
        #diferencia series y peliculas
        if tipo != "movies":
            title += " [COLOR khaki](Serie)[/COLOR]"
            itemlist.append(item.clone(title=title, url=scrapedurl, contentSerieName=contentTitle,
                                   action="temporadas", infoLabels={"year": year},
                                   thumbnail=scrapedthumbnail, page=0))
        else:
            itemlist.append(item.clone(title=title, url=scrapedurl, contentTitle=contentTitle,
                                   action="findvideos", infoLabels={"year": year},
                                   thumbnail=scrapedthumbnail, page=0))
    #busquedas que coinciden con genero arrojan cientos de resultados
    if item.page + 30 < len(matches):
        itemlist.append(item.clone(page=item.page + 30, action="sub_search",
                                   title="» Siguiente »"))
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
    quality = ""
    action = "findvideos"
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\(.*?\)|\s{2}|&nbsp;", "", data)
    try:
        data = data.split('<div id="archive-content"')[1]
    except:
        pass
    patron = '<div class="poster">(.*?)<img src="([^"]+)" alt="([^"]+)">.*?'  # langs, img, title.strip() movies
    patron += '<span class="icon-star2"></span> ([^<]+)</div>.*?' #rating
    patron += '</div><a href="([^"]+)">.*?<span>(\d+)</span>.*?'  # url, year
    patron += '<div class="texto">([^<]+)</div>(.*?)</article>'  # plot, info
    matches = scrapertools.find_multiple_matches(data, patron)

    for langs, scrapedthumbnail, scrapedtitle, rating, scrapedurl, year, plot, info in matches:

        #para tomar la imagen completa
        scrapedthumbnail = re.sub("(w\d+/)", "original/", scrapedthumbnail)
        title = scrapedtitle.partition(' | ')[0].rstrip()
        try:
            contentTitle = scrapedtitle.split(' | ')[1].rstrip()
        except:
            contentTitle = title
        #rating con color(evaluacion)
        rcolor = color_rating(rating)
        #Calidad
        if '1080p' in info:
            quality = '1080p'
        elif '720p' in info:
            quality = '720p'
        else:
            quality = 'SD'
        
        title += " [COLOR %s](%s)[/COLOR] [COLOR %s](%s)[/COLOR] [COLOR %s][%s][/COLOR]" % (
            'lightgray', year, rcolor, rating, 'khaki', quality)

        if "/series/" in scrapedurl:
            title = title.replace("[SD]", "(Serie)")
            itemlist.append(Item(channel=__channel__, action="temporadas",
                                    url=scrapedurl, thumbnail=scrapedthumbnail,
                                    contentSerieName=contentTitle, title=title,
                                    context="buscar_trailer", plot=plot))
        else:
            itemlist.append(Item(channel=__channel__, action="findvideos",
                                    url=scrapedurl, infoLabels={'year': year},
                                    thumbnail=scrapedthumbnail,contentTitle= contentTitle,
                                    title=title, context="buscar_trailer", plot=plot))
    tmdb.set_infoLabels_itemlist(itemlist, True)

    url_next_page = scrapertools.find_single_match(data,'<a class=\'arrow_pag\' href="([^"]+)">')
    if url_next_page:
        itemlist.append(item.clone(title="Siguiente >>", url=url_next_page, action='peliculas'))
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
            title = "%s (%s)" % (scrapedtitle.replace('de ', ''), cantidad)
            itemlist.append(item.clone(channel=item.channel, action="peliculas", 
                                       title=title, page=0, url=scrapedurl,))

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
        itemlist.append(item.clone(channel=item.channel, action="peliculas", title=scrapedtitle, 
                                   page=0, url=scrapedurl, extra='next'))

    return itemlist


def series(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\(.*?\)|&nbsp;|<br>", "", data)
    patron = '<div class="poster"><img src="([^"]+)" alt="([^"]+)">.*?<a href="([^"]+)">.*?'
    patron += '<div class="texto">([^<]+)</div>'

    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedthumbnail, scrapedtitle, scrapedurl, plot in matches[item.page:item.page + 30]:
        if plot == '':
            plot = scrapertools.find_single_match(data, '<div class="texto">([^<]+)</div>')
        scrapedtitle = scrapedtitle.replace('Ver ', '').replace(
            ' Online HD', '').replace('ver ', '').replace(' Online', '').replace(' (Serie TV)', '').strip()
        itemlist.append(item.clone(title=scrapedtitle, url=scrapedurl, action="temporadas",
                                   contentSerieName=scrapedtitle, show=scrapedtitle, plot=plot,
                                   thumbnail=scrapedthumbnail, contentType='tvshow'))

    tmdb.set_infoLabels(itemlist, True)

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
    season_id = scrapertools.find_single_match(data, 'var id  = (\d+);')
    post = {"action": "seasons", "id": season_id}
    datas = httptools.downloadpage(host+'wp-admin/admin-ajax.php', post=post).data
    
    datas = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", datas)
    patron = "<span class='title'>([^<]+)<i>.*?"  # numeros de temporadas
    patron += "<img src='([^']+)'>"  # capitulos
    # logger.info(datas)
    matches = scrapertools.find_multiple_matches(datas, patron)
    if len(matches) > 1:
        for scrapedseason, scrapedthumbnail in matches:
            scrapedseason = " ".join(scrapedseason.split())
            temporada = scrapertools.find_single_match(scrapedseason, '(\d+)')
            new_item = item.clone(action="episodios", season=temporada, thumbnail=scrapedthumbnail, extra='temporadas', data_web=datas)
            new_item.infoLabels['season'] = temporada
            new_item.extra = ""
            itemlist.append(new_item)

        tmdb.set_infoLabels(itemlist, True)

        for i in itemlist:
            i.title = "%s. %s" % (i.infoLabels['season'], i.infoLabels['tvshowtitle'])
            if i.infoLabels['title']:
                # Si la temporada tiene nombre propio añadirselo al titulo del item
                i.title += " - %s" % (i.infoLabels['title'])
            if i.infoLabels.has_key('poster_path'):
                # Si la temporada tiene poster propio remplazar al de la serie
                i.thumbnail = i.infoLabels['poster_path']

        itemlist.sort(key=lambda it: it.title)
    
    else:
        item.data_web = datas
        return episodios(item)

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(Item(channel=__channel__, title="Añadir esta serie a la videoteca", url=item.url,
                             action="add_serie_to_library", extra="episodios", show=item.show, category="Series"))

        return itemlist


def episodios(item):
    
    itemlist = []
    datas = item.data_web
    item.data_web = ""
    patron = "<div class='imagen'.*?<img src='([^']+)'.*?"
    patron += "<div class='numerando'>(.*?)</div>.*?"
    patron += "<a href='([^']+)'>([^<]+)</a>.*?"
    patron += '<div class="lang_ep">(.*?)</div>'
    

    matches = scrapertools.find_multiple_matches(datas, patron)

    for scrapedthumb, scrapedtitle,  scrapedurl, scrapedname, infolang in matches:
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

    itemlist.sort(key=lambda it: int(it.infoLabels['episode']),
                  reverse=config.get_setting('orden_episodios', __channel__))
    tmdb.set_infoLabels_itemlist(itemlist, True)
    # Opción "Añadir esta serie a la videoteca"
    if item.extra != 'temporadas':
        if config.get_videolibrary_support() and len(itemlist) > 0:
            itemlist.append(Item(channel=__channel__, title="Añadir esta serie a la videoteca", url=item.url,
                             action="add_serie_to_library", extra="episodios", show=item.show, category="Series"))

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
                     url=url, title='[COLOR yellowgreen]%s [/COLOR]' + lang))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())
    itemlist.sort(key=lambda it: it.language, reverse=False)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'episodios':
        itemlist.append(Item(channel=__channel__, url=item.url, action="add_pelicula_to_library", extra="findvideos",
                             title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             contentTitle=item.contentTitle))

    return itemlist
