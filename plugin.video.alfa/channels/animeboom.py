# -*- coding: utf-8 -*-
# -*- Channel AnimeBoom -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
import urllib

from core import httptools
from core import scrapertools
from core import servertools
from channelselector import get_thumb
from core import tmdb
from core.item import Item
from platformcode import logger, config
from channels import autoplay
from channels import filtertools
from channels import renumbertools

host = "https://animeboom.net/"

__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', 'animeboom')
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', 'animeboom')

IDIOMAS = {'Latino':'LAT', 'VOSE': 'VOSE'}
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['directo', 'openload', 'streamango']


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = []

    itemlist.append(Item(channel=item.channel, title="Nuevos Episodios",
                         action="new_episodes",
                         thumbnail=get_thumb('new_episodes', auto=True),
                         url=host))

    itemlist.append(Item(channel=item.channel, title="Ultimas",
                               action="list_all",
                               thumbnail=get_thumb('last', auto=True),
                               url=host + 'emision'))

    itemlist.append(Item(channel=item.channel, title="Todas",
                               action="list_all",
                               thumbnail=get_thumb('all', auto=True),
                               url=host + 'series'))

    itemlist.append(Item(channel=item.channel, title="Series",
                              action="list_all",
                              thumbnail=get_thumb('tvshows', auto=True),
                              url=host + 'tv'))

    itemlist.append(Item(channel=item.channel, title="Películas",
                         action="list_all",
                         thumbnail=get_thumb('movies', auto=True),
                         url=host + 'peliculas'))

    itemlist.append(Item(channel=item.channel, title="OVAs",
                              action="list_all",
                              thumbnail='',
                              url=host + 'ova'))

    itemlist.append(Item(channel=item.channel, title="ONAs",
                              action="list_all",
                              thumbnail='',
                              url=host + 'ona'))


    itemlist.append(Item(channel=item.channel, title="Especiales",
                              action="list_all",
                              thumbnail='',
                              url=host + '/specials'))

    itemlist.append(Item(channel=item.channel, title="Buscar",
                               action="search",
                               url=host + 'search?s=',
                               thumbnail=get_thumb('search', auto=True),
                               fanart='https://s30.postimg.cc/pei7txpa9/buscar.png'
                               ))

    autoplay.show_option(item.channel, itemlist)
    itemlist = renumbertools.show_option(item.channel, itemlist)

    return itemlist


def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data


def list_all(item):
    logger.info()

    itemlist = []

    data = get_source(item.url)
    patron = '<article class="([^"]+)"><figure class="image"><a href="([^"]+)" title=".*?">'
    patron += '<img src="([^"]+)" alt="([^"]+)">.*?class="year">(\d{4})<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for type, scrapedurl, scrapedthumbnail, scrapedtitle, year in matches:
        url = scrapedurl
        thumbnail = scrapedthumbnail
        if 'latino' in scrapedtitle.lower():
            lang = 'Latino'
        else:
            lang = 'VOSE'
        title = re.sub('Audio Latino', '', scrapedtitle)
        context = renumbertools.context(item)
        context2 = autoplay.context
        context.extend(context2)
        itemlist.append(Item(channel=item.channel, action='episodios',
                                   title=title,
                                   url=url,
                                   thumbnail=thumbnail,
                                   contentSerieName=title,
                                   language = lang,
                                   context = context,
                                   infoLabels={'year':year}
                                   ))

        # Paginacion
    next_page = scrapertools.find_single_match(data,
                                               '<a href="([^"]+)" rel="next">&raquo;</a>')
    next_page_url = scrapertools.decodeHtmlentities(next_page)

    if next_page_url != "":
        itemlist.append(Item(channel=item.channel,
                             action="list_all",
                             title=">> Página siguiente",
                             url=next_page_url,
                             thumbnail='https://s16.postimg.cc/9okdu7hhx/siguiente.png'
                             ))
    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    return itemlist


def search_results(item):
    logger.info()

    itemlist=[]

    full_data = get_source(item.url)
    data = scrapertools.find_single_match(full_data, '<div class="search-results">(.*?)<h4')

    patron = '<a href="([^"]+)" title="([^"]+)"><img src="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle, scrapedthumbnail in matches:

        url = scrapedurl
        title = re.sub('online|Audio|Latino', '', scrapedtitle)
        title = title.lstrip()
        title = title.rstrip()
        context = renumbertools.context(item)
        context2 = autoplay.context
        context.extend(context2)
        itemlist.append(Item(channel=item.channel,
                             action="episodios",
                             title=title,
                             contentSerieName=title,
                             url=url,
                             context = context,
                             thumbnail=scrapedthumbnail))

    tmdb.set_infoLabels(itemlist, seekTmdb=True)

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    try:
        if texto != '':
            return search_results(item)
        else:
            return []
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

def new_episodes(item):
    logger.info()

    itemlist = []

    full_data = get_source(item.url)
    data = scrapertools.find_single_match(full_data, '>Episodios Estreno</h2>(.*?)</section>')
    patron = '<a href="([^"]+)"><img src="([^"]+)" alt="([^"]+)">'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        url = scrapedurl
        if 'latino' in scrapedtitle.lower():
            lang = 'Latino'
        else:
            lang = 'VOSE'
        title = re.sub('sub|Sub|Español|español|Audio|Latino|audio|latino','', scrapedtitle)
        itemlist.append(Item(channel=item.channel, title=title, url=url, thumbnail=scrapedthumbnail,
                             action='findvideos', language=lang))

    return itemlist

def episodios(item):
    logger.info()
    itemlist = []

    full_data = get_source(item.url)
    data = scrapertools.find_single_match(full_data, '<ul class="list-episodies scrolling">(.*?)</ul>')
    patron = '<a href="([^"]+)".*?title="([^"]+)".*?Episodio (\d+)'
    matches = re.compile(patron, re.DOTALL).findall(data)

    infoLabels = item.infoLabels
    for scrapedurl, title, episode in matches:
        if 'latino' in title.lower():
            lang='Latino'
        else:
            lang = 'VOSE'
        season, episode = renumbertools.numbered_for_tratk(item.channel, item.contentSerieName, 1, int(episode))
        title = "%sx%s - %s" % (season, str(episode).zfill(2),item.contentSerieName)
        url = scrapedurl
        infoLabels['season'] = season
        infoLabels['episode'] = episode

        itemlist.append(Item(channel=item.channel, title=title, contentSerieName=item.contentSerieName, url=url,
                             action='findvideos', language=lang, infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    itemlist = itemlist[::-1]
    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]', url=item.url,
                 action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName,
                 extra1='library'))

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = []

    data = get_source(item.url)
    #return
    patron = 'video\[\d+\] = \'<iframe.*?src="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl in matches:

        if 'animeboom' in scrapedurl:
            new_data = get_source(scrapedurl)
            scrapedurl = scrapertools.find_single_match(new_data, "'file':'([^']+)")

        if scrapedurl != '':
            itemlist.append(Item(channel=item.channel, title='%s', url=scrapedurl, action='play', language = item.language,
                                       infoLabels=item.infoLabels))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())

    if __comprueba_enlaces__:
        itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    return itemlist

def newest(categoria):
    itemlist = []
    item = Item()
    if categoria == 'anime':
        item.url=host
        itemlist = new_episodes(item)
    return itemlist
