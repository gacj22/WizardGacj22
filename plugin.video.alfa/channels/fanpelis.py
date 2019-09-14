# -*- coding: utf-8 -*-
# -*- Channel Fanpelis -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
import urllib
import urlparse

from channelselector import get_thumb
from core import httptools
from core import jsontools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from core import tmdb

host = "https://fanpelis.net/"

def mainlist(item):
    logger.info()
    itemlist = list()
    itemlist.append(
        Item(channel=item.channel,
             title="Peliculas",
             action="sub_menu",
             url=host + "movies/",
             thumbnail=get_thumb('movies', auto=True)))

    itemlist.append(
        Item(channel=item.channel,
             title="Series",
             action="sub_menu",
             url=host + "series/",
             thumbnail=get_thumb('tvshows', auto=True)))

    itemlist.append(
        Item(channel=item.channel,
             title="Buscar",
             action="search",
             url=host,
             thumbnail=get_thumb("search", auto=True)))

    return itemlist


def sub_menu(item):
    logger.info()

    itemlist = list()

    itemlist.append(
        Item(channel=item.channel,
             title="Ultimas",
             action="list_all",
             url=item.url,
             thumbnail=get_thumb("last", auto=True)))

    itemlist.append(
        Item(channel=item.channel,
             title="Generos",
             action="categories",
             url=host,
             thumbnail=get_thumb('genres', auto=True)

             ))

    itemlist.append(
        Item(channel=item.channel,
             title="Por Año",
             action="categories",
             url=host,
             thumbnail=get_thumb('year', auto=True)
             ))

    return itemlist

def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data


def categories(item):
    logger.info()
    itemlist = []

    data = get_source(item.url)
    if item.title == 'Generos':
        patron = 'menu-item-object-category menu-item-\d+"><a href="([^"]+)">([^<]+)<'
    else:
        patron = 'menu-item-object-release-year menu-item-\d+"><a href="([^"]+)">([^<]+)<'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for url, title in matches:
        itemlist.append(Item(channel=item.channel,
                             action="list_all",
                             title=title,
                             url=url
                             ))

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    try:
        if texto != '':
            item.texto = texto
            return list_all(item)
        else:
            return []
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def list_all(item):
    logger.info()
    itemlist = []

    if item.texto != '':
        url = item.url + "?s=%s" % item.texto
    else:
        url = item.url

    try:
        data = get_source(url)
    except:
        return itemlist
    data = data.replace("'", '"')

    pattern = 'class="ml-item.*?"><a href="([^"]+)".*?oldtitle="([^"]+)".*?'
    pattern += '<img data-original="([^"]+)".*?<div id(.*?)/a>'
    matches = scrapertools.find_multiple_matches(data, pattern)

    for url, title, thumb, info in matches:
        year = scrapertools.find_single_match(info, 'rel="tag">(\d{4})<')
        new_item = Item(channel=item.channel,
                        title=title,
                        url=url,
                        thumbnail=thumb,
                        infoLabels = {'year': year}
                        )
        if 'series' in url:
            new_item.action = 'seasons'
            new_item.contentSerieName = title
        else:
            new_item.action = 'findvideos'
            new_item.contentTitle = title

        itemlist.append(new_item)

    tmdb.set_infoLabels(itemlist, seekTmdb=True)

    active_page = scrapertools.find_single_match(data, '<li class="active"><a class="">(\d+)</a>')
    if item.texto != '':
        next_page = host + 'page/%s/' % (int(active_page) + 1)
    else:
        next_page = item.url +'page/%s/' % (int (active_page) + 1)

    if next_page:

        url = urlparse.urljoin(host, next_page)
        itemlist.append(Item(channel=item.channel,
                             action="list_all",
                             title=">> Página siguiente",
                             url=url,
                             texto=item.texto,
                             thumbnail=get_thumb("next.png")))
    return itemlist


def seasons(item):
    logger.info()

    itemlist = []

    data = get_source(item.url)
    patron = '<strong>Temporada(\d+)</strong>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for temporada in matches:
        title = 'Temporada %s' % temporada
        contentSeasonNumber = temporada
        item.infoLabels['season'] = contentSeasonNumber
        itemlist.append(item.clone(action='episodesxseason',
                                   title=title,
                                   contentSeasonNumber=contentSeasonNumber
                                   ))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(Item(channel=item.channel,
                             title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]',
                             url=item.url,
                             action="add_serie_to_library",
                             extra="episodios",
                             contentSerieName=item.contentSerieName,
                             contentSeasonNumber=contentSeasonNumber
                             ))

    return itemlist

def episodios(item):
    logger.info()
    itemlist = []
    templist = seasons(item)
    for tempitem in templist:
        itemlist += episodesxseason(tempitem)

    return itemlist


def episodesxseason(item):
    logger.info()

    itemlist = []
    season = item.contentSeasonNumber
    data = get_source(item.url)
    data = scrapertools.find_single_match(data, '<strong>Temporada%s</strong>.*?</ul>' % season)
    patron = '<a href="([^"]+)"><i class="fa fa-play"></i>([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    ep = 1
    for scrapedurl, scrapedtitle in matches:
        epi = str(ep)
        title = season + 'x%s - Episodio %s' % (epi, epi)
        url = scrapedurl
        contentEpisodeNumber = epi
        item.infoLabels['episode'] = contentEpisodeNumber
        itemlist.append(item.clone(action='findvideos',
                                   title=title,
                                   url=url,
                                   contentEpisodeNumber=contentEpisodeNumber,
                                   ))
        ep += 1
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def findvideos(item):
    logger.info()
    import urllib

    itemlist = []

    data = get_source(item.url)
    player = scrapertools.find_single_match(data, "({'action': 'movie_player','foobar_id':\d+,})")
    post = eval(player)
    post = urllib.urlencode(post)
    data = httptools.downloadpage(host+'wp-admin/admin-ajax.php', post=post, headers={'Referer':item.url}).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    patron = 'data-url="([^"]+)"'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for url in matches:
        itemlist.append(Item(channel=item.channel, title='%s', url=url, action='play', infoLabels=item.infoLabels))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(
            Item(channel=item.channel,
                 title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                 url=item.url,
                 action="add_pelicula_to_library",
                 extra="findvideos",
                 contentTitle=item.contentTitle
                 ))

    return itemlist

def newest(category):
    logger.info()
    item = Item()
    try:
        if category == 'peliculas':
            item.url = host + "movies/"
        elif category == 'infantiles':
            item.url = host + 'genre/animacion'
        elif category == 'terror':
            item.url = host + 'genre/terror'
        itemlist = list_all(item)

        if itemlist[-1].title == '>> Página siguiente':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

    return itemlist
