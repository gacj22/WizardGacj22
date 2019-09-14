# -*- coding: utf-8 -*-

import re
import urllib
import urlparse

from channels import autoplay
from channels import filtertools
from core import httptools
from core import jsontools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb

IDIOMAS = {'Latino': 'LAT', 'Castellano': 'CAST', 'Subtitulado': 'VOSE', 'Ingles': 'VO'}
list_language = IDIOMAS.values()
list_quality = ['HD 720p', 'HD 1080p', '480p', '360p']
list_servers = ['cinemaupload']

host = 'https://homecine.tv'


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = []

    itemlist.append(Item(channel=item.channel, title="Ultimas",
                         action="list_all",
                         thumbnail=get_thumb('last', auto=True),
                         url='%s%s' % (host, '/release-year/2019'),
                         first=0
                         ))

    itemlist.append(Item(channel=item.channel,title="Películas",
                    action="sub_menu",
                    thumbnail=get_thumb('movies', auto=True),
                    ))

    itemlist.append(Item(channel=item.channel,title="Series",
                    action="list_all",
                    thumbnail=get_thumb('tvshows', auto=True),
                    url='%s%s'%(host,'/series/'),
                    first=0
                    ))

    itemlist.append(Item(channel=item.channel, title="Documentales",
                         action="list_all",
                         thumbnail=get_thumb('documentaries', auto=True),
                         url='%s%s' % (host, '/documentales/'),
                         first=0
                         ))

    itemlist.append(Item(channel=item.channel,title="Buscar",
                    action="search",
                    url=host+'/?s=',
                    thumbnail=get_thumb('search', auto=True),
                    ))

    autoplay.show_option(item.channel, itemlist)

    return itemlist

def sub_menu(item):
    logger.info()

    itemlist = []



    itemlist.append(Item(channel=item.channel,title="Todas",
                         action="list_all",
                         thumbnail=get_thumb('all', auto=True),
                         url='%s%s' % (host, '/peliculas/'),
                         first=0
                         ))

    itemlist.append(Item(channel=item.channel, title="Mas vistas",
                         action="list_all",
                         thumbnail=get_thumb('more watched', auto=True),
                         url='%s%s' % (host, '/most-viewed/'),
                         first=0
                         ))

    itemlist.append(Item(channel=item.channel,title="Generos",
                         action="seccion",
                         thumbnail=get_thumb('genres', auto=True),
                         fanart='https://s3.postimg.cc/5s9jg2wtf/generos.png',
                         url=host,
                         ))

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
    next = False

    data = get_source(item.url)
    patron = 'movie-id="\d+".*?<a href="([^"]+)".*?<.*?original="([^"]+)".*?<h2>([^<]+)</h2>.*?jtip(.*?)clearfix'

    matches = re.compile(patron, re.DOTALL).findall(data)

    first = item.first
    last = first + 19
    if last > len(matches):
        last = len(matches)
        next = True

    for scrapedurl, scrapedthumbnail, scrapedtitle, extra_info in matches[first:last]:

        year = scrapertools.find_single_match(extra_info, '"tag">(\d{4})<')
        url = host+scrapedurl
        thumbnail = host+scrapedthumbnail.strip()
        title = scrapedtitle
        new_item = Item(channel=item.channel,
                        title=title,
                        url=url,
                        thumbnail=thumbnail,
                        infoLabels = {'year': year}
                         )
        if 'series' in scrapedurl:
            new_item.action = 'seasons'
            new_item.contentSerieName = title
        else:
            new_item.action = 'findvideos'
            new_item.contentTitle = title



        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb = True)

    if not next:
        url_next_page = item.url
        first = last
    else:
        url_next_page = scrapertools.find_single_match(data, "<li class='active'>.*?class='page larger' href='([^']+)'")
        url_next_page = host+url_next_page
        first = 0

    if url_next_page:
        itemlist.append(Item(channel=item.channel,title="Siguiente >>", url=url_next_page, action='list_all',
                             first=first))

    return itemlist


def seccion(item):
    logger.info()

    itemlist = []
    duplicado = []
    data = get_source(item.url)

    patron = 'menu-item-object-category menu-item-\d+"><a href="([^"]+)">([^<]+)<\/a><\/li>'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        url = host+scrapedurl
        title = scrapedtitle
        thumbnail = ''
        if url not in duplicado:
            itemlist.append(Item(channel=item.channel,
                                 action='list_all',
                                 title=title,
                                 url=url,
                                 thumbnail=thumbnail,
                                 first=0
                                 ))
    return itemlist


def seasons(item):
    logger.info()
    itemlist = []

    data = get_source(item.url)

    patron = '<strong>Season (\d+)</strong>'

    matches = re.compile(patron, re.DOTALL).findall(data)
    infoLabels = item.infoLabels
    for scrapedseason in matches:
        contentSeasonNumber = scrapedseason
        title = 'Temporada %s' % scrapedseason
        infoLabels['season'] = contentSeasonNumber

        itemlist.append(Item(channel=item.channel,
                             action='episodesxseason',
                             url=item.url,
                             title=title,
                             contentSeasonNumber=contentSeasonNumber,
                             infoLabels=infoLabels
                             ))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(Item(channel=item.channel,
                             title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]',
                             url=item.url,
                             action="add_serie_to_library",
                             extra="episodios",
                             contentSerieName=item.contentSerieName,
                             extra1='library'
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
    data = scrapertools.find_single_match(data, '<strong>Season %s</strong>.*?class="les-content"(.*?)</div>' % season)
    patron = '<a href="([^"]+)">Episode (\d+)'
    matches = re.compile(patron, re.DOTALL).findall(data)
    infoLabels = item.infoLabels
    for scrapedurl, dataep in matches:
        url = host+scrapedurl
        contentEpisodeNumber = dataep
        try:
            title = '%sx%s - Episodio %s' % (season, dataep, dataep)
        except:
            title = 'episodio %s' % dataep
        infoLabels['episode'] = dataep
        infoLabels = item.infoLabels

        itemlist.append(Item(channel=item.channel,
                             action="findvideos",
                             title=title,
                             url=url,
                             contentEpisodeNumber=contentEpisodeNumber,
                             infoLabels=infoLabels
                             ))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist



def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    item.first=0
    if texto != '':
        return list_all(item)


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria in ['peliculas']:
            item.url = host +'/peliculas'
        elif categoria == 'infantiles':
            item.url = host + '/animacion/'
        elif categoria == 'terror':
            item.url = host + '/terror/'
        item.first=0
        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist

def findvideos(item):
    logger.info()
    itemlist = []

    data = get_source(item.url)
    patron = '<div id="tab(\d+)".*?<iframe.*?src="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for option, url in matches:
        extra_info = scrapertools.find_single_match(data, '<a href="#tab%s">(.*?)<' % option)
        if '-' in extra_info:
            quality, language = scrapertools.find_single_match(extra_info, '(.*?) - (.*)')
            if " / " in language:
                language = language.split(" / ")[1]
        else:
            language = ''
            quality = extra_info

        if 'https:' not in url:
            url = 'https:'+url
        title = ''
        if not config.get_setting('unify'):
            if language != '':
                try:
                    title += ' [%s]' % IDIOMAS.get(language.capitalize(), 'Latino')
                except:
                    pass
            if quality != '':
                title += ' [%s]' % quality
        new_item = Item(channel=item.channel,
                        url=url,
                        title= '%s'+ title,
                        contentTitle=item.title,
                        action='play',
                        infoLabels = item.infoLabels
                        )
        if language != '':
            new_item.language = IDIOMAS.get(language.capitalize(), 'Latino')
        if quality != '':
            new_item.quality = quality

        itemlist.append(new_item)
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos' and not "/episode/" in item.url:
        itemlist.append(
            Item(channel=item.channel,
                 title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                 url=item.url,
                 action="add_pelicula_to_library",
                 extra="findvideos",
                 contentTitle=item.contentTitle,
                 ))


    return itemlist
