# -*- coding: utf-8 -*-
# -*- Channel CinemaHD -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
import urllib
from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channels import autoplay
from channels import filtertools



host = 'https://www.cinemahd.co/'

IDIOMAS = {'Latino': 'LAT'}
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['gounlimited', 'rapidvideo', 'vshare', 'clipwatching', 'jawclowd', 'streamango']


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title="Ultimas", action="list_all", url=host + 'peliculas-1080p-online/',
                         thumbnail=get_thumb('last', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Generos", action="section", section='genre',
                         thumbnail=get_thumb('genres', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=host + '?s=',
                         thumbnail=get_thumb('search', auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist

def get_source(url, referer=None):
    logger.info()
    if referer is None:
        data = httptools.downloadpage(url).data
    else:
        data = httptools.downloadpage(url, headers={'Referer':referer}).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data


def list_all(item):
    logger.info()
    itemlist = []

    data = get_source(item.url)
    full_data = data
    if not item.genre:
        item.genre = 'Películas'

    data = scrapertools.find_single_match(data, '<h1>%s</h1>(.*?)<div class="sidebar scrolling">' % item.genre)

    patron = '<div class="poster">.*?<img src="([^"]+)" alt="([^"]+)">.*?<a href="([^"]+)">.*?</h3>.*?<span>([^<]+)</'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedthumbnail, scrapedtitle, scrapedurl, year in matches:

        url = scrapedurl
        if year == '':
            year = '-'
        if "|" in scrapedtitle:
            scrapedtitle= scrapedtitle.split("|")
            cleantitle = scrapedtitle[0].strip()
        else:
            cleantitle = scrapedtitle

        cleantitle = re.sub('\(.*?\)', '', cleantitle)

        if not config.get_setting('unify'):
            title = '%s [%s]' % (cleantitle, year)
        else:
            title = cleantitle
        thumbnail = scrapedthumbnail

        new_item = Item(channel=item.channel,
                        title=title,
                        contentTitle=cleantitle,
                        url=url,
                        action='findvideos',
                        thumbnail=thumbnail,
                        infoLabels={'year': year}
                        )

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, True)

    #  Paginación

    url_next_page = scrapertools.find_single_match(full_data,'<a class=\'arrow_pag\' href="([^"]+)">')
    if url_next_page:
        itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=url_next_page, action='list_all',
                             genre=item.genre))
    return itemlist

def section(item):
    logger.info()
    itemlist = []

    url = host + '?tr_post_type=1'

    data = get_source(url)
    action = 'list_all'


    if item.section == 'genre':
        data = scrapertools.find_single_match(data, '<h2>Géneros</h2>(.*?)</ul>')

    elif item.section == 'year':
        data = scrapertools.find_single_match(data, '<h2>Año de Lanzamiento</h2>(.*?)</ul>')
    action = 'list_all'
    patron = '<a href="([^"]+)">([^<]+)<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for data_one, data_two in matches:

        title = data_two
        if title != 'Ver más':
            new_item = Item(channel=item.channel, title=title, url=data_one, action=action, section=item.section,
                            genre=title)
            itemlist.append(new_item)

    return itemlist


def findvideos(item):
    logger.info()
    from lib import generictools
    import urllib
    itemlist = []
    data = get_source(item.url)
    data = data.replace("'", '"')
    patron = 'data-type="([^"]+)" data-post="(\d+)" data-nume="(\d+)'
    matches = re.compile(patron, re.DOTALL).findall(data)
    lang = scrapertools.find_single_match(data, "<span class='title'>([^<])</span>")

    for type, pt, nm in matches:

        post = {'action': 'doo_player_ajax', 'post': pt, 'nume': nm, 'type': type}
        new_data = httptools.downloadpage(host + 'wp-admin/admin-ajax.php', post=post,
                                          headers={'Referer': item.url}).data
        url = scrapertools.find_single_match(new_data, "src='([^']+)'")

        if not config.get_setting('unify'):

            title = ' [%s]' % IDIOMAS.get(lang, 'LAT')
        else:
            title = ''

        itemlist.append(Item(channel=item.channel, title='%s' + title, url=url, action='play',
                             language=IDIOMAS.get(lang, 'LAT'), infoLabels=item.infoLabels))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    itemlist = sorted(itemlist, key=lambda it: it.language)

    if item.contentType != 'episode':
        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
            itemlist.append(
                Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]', url=item.url,
                     action="add_pelicula_to_library", extra="findvideos", contentTitle=item.contentTitle))

    return itemlist

def search_results(item):
    logger.info()

    itemlist = list()

    full_data = get_source(item.url)
    data = scrapertools.find_single_match(full_data, '<h1>Resultados encontrados:(.*?)<div class="sidebar scrolling">')
    patron = '<article>.*?<a href="([^"]+)"[^<]+<img src="([^"]+)" alt="([^"]+)".*?class="meta">(.*?)style'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumb, scrapedtitle, extra_data in matches:

        if "|" in scrapedtitle:
            scrapedtitle = scrapedtitle.split("|")
            cleantitle = scrapedtitle[0].strip()
        else:
            cleantitle = scrapedtitle

        cleantitle = re.sub('\(.*?\)', '', cleantitle)

        if 'year' in extra_data:
            year = scrapertools.find_single_match(extra_data, '"year">([^<]+)<')
        else:
            year = '-'

        itemlist.append(Item(channel=item.channel, title=cleantitle, contentTitle=cleantitle, url=scrapedurl,
                             action='findvideos', thumbnail=scrapedthumb, infoLabels={'year':year}))


    tmdb.set_infoLabels_itemlist(itemlist, True)
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    if texto != '':
        return search_results(item)
    else:
        return []


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria in ['peliculas','latino']:
            item.url = host + 'peliculas-1080p-online/'
        elif categoria == 'infantiles':
            item.url = host + '/genero/animacion/'
            item.genre = 'Animación'
        elif categoria == 'terror':
            item.url = host + '/genero/terror/'
            item.genre = 'Terror'
        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
