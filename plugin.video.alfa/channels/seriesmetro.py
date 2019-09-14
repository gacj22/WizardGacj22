# -*- coding: utf-8 -*-
# -*- Channel SeriesMetro -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re

from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core import jsontools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb

host = 'https://seriesmetro.com/'

list_language = []
list_quality = []
list_servers = ['openload', 'dailymotion']

__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', 'seriesmetro')
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', 'seriesmetro')

def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data

def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist =[]

    itemlist.append(Item(channel=item.channel, title="Todas", action="list_all", url=host,
                         thumbnail=get_thumb('all', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Generos", action="section",
                         thumbnail=get_thumb('genres', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Alfabetico", action="section",
                         thumbnail=get_thumb('alphabet', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=host + '?s=',
                         thumbnail=get_thumb('search', auto=True)))

    autoplay.show_option(item.channel, itemlist)
    return itemlist

def list_all(item):
    logger.info()

    itemlist = []

    data = get_source(item.url)
    patron = '<div class="post-thumbnail"><a href="([^"]+)".*?src="([^"]+)".*?title="Enlace permanente.*?">([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        url = scrapedurl
        scrapedtitle = scrapedtitle.lower().replace('enlace permanente a', '').capitalize()
        contentSerieName = scrapedtitle
        action = 'seasons'

        thumbnail = scrapedthumbnail
        new_item = Item(channel=item.channel, title=scrapedtitle, url=url, thumbnail=thumbnail,
                        contentSerieName=contentSerieName, action=action)

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # Paginacion
    next_page = scrapertools.find_single_match(data, 'class=\'current\'>\d</span>.*?href="([^"]+)">')
    if next_page != '':
        itemlist.append(Item(channel=item.channel, action="list_all", title='Siguiente >>>',
                             url=next_page, thumbnail='https://s16.postimg.cc/9okdu7hhx/siguiente.png',
                             type=item.type))
    return itemlist


def section(item):

    itemlist = []

    full_data = get_source(host)

    if item.title == 'Generos':
        data = scrapertools.find_single_match(full_data, '>Géneros</a>(.*?)</ul>')
    elif item.title == 'Alfabetico':
        data = scrapertools.find_single_match(full_data, '<ul id="menu-top"(.*?)</ul>')

    patron = '<a href="([^"]+)">([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:

        if scrapedtitle != 'Series':
            itemlist.append(Item(channel=item.channel, title=scrapedtitle, url=scrapedurl, action='list_all'))

    return itemlist


def seasons(item):
    logger.info()
    itemlist = []

    data = get_source(item.url)

    patron = 'Temporada (\d+)'

    matches = re.compile(patron, re.DOTALL).findall(data)
    infoLabels = item.infoLabels
    if len(matches) > 0:
        for scrapedseason in matches:
            title = 'Temporada %s' % scrapedseason
            infoLabels['season'] = scrapedseason

            itemlist.append(Item(channel=item.channel, action='episodesxseason', url=item.url, title=title,
                                 infoLabels=infoLabels))
    else:
        infoLabels['season'] = '1'
        itemlist.append(Item(channel=item.channel, action='episodesxseason', url=item.url, title='Temporada 1',
                             infoLabels=infoLabels, single=True))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]', url=item.url,
                 action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName,
                 extra1='library'))

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
    season = item.infoLabels['season']
    full_data = get_source(item.url)

    if item.single:
        data = scrapertools.find_single_match(full_data, '<strong>Capítulos.*?</strong>(.*?)</ul>')
    else:
        data = scrapertools.find_single_match(full_data, 'Temporada %s.*?</strong>(.*?)</ul>' % season)
    patron = '<a href="([^"]+)">.*?;.?([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    infoLabels = item.infoLabels
    epi = 1
    for scrapedurl, scrapedtitle in matches:
        url = scrapedurl
        contentEpisodeNumber = str(epi)
        title = '%sx%s - %s ' % (season, contentEpisodeNumber, scrapedtitle)
        infoLabels['episode'] = contentEpisodeNumber
        itemlist.append(Item(channel=item.channel, action="findvideos", title=title, url=url,
                             contentSerieName=item.contentSerieName, contentEpisodeNumber=contentEpisodeNumber,
                             infoLabels=infoLabels))
        epi += 1
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist

def search(item, text):
    logger.info()

    item.url = item.url + text
    if text != '':
        return list_all(item)

def findvideos(item):

    itemlist = []
    data = get_source(item.url)
    patron = 'iframe-container">.*?<iframe .*?src="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)
    
    for link in matches:

        '''id_letter = scrapertools.find_single_match(link, '?(\w)d')

        id_type = '%sd' % id_letter
        ir_type = '%sr' % id_letter

        id = scrapertools.find_single_match(link, '%s=(.*)' % id_type)
        base_link = scrapertools.find_single_match(link, '(.*?)%s=' % id_type)

        ir = id[::-1]
        referer = base_link+'%s=%s&/' % (id_type, ir)
        video_data = httptools.downloadpage('%s%s=%s' % (base_link, ir_type, ir), headers={'Referer':referer},
                                            follow_redirects=False)
        logger.error(video_data.data)
        url = video_data.headers['location']'''
        title = '%s'

        itemlist.append(Item(channel=item.channel, title=title, url=link, action='play',
                             language='', infoLabels=item.infoLabels))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    return itemlist



def play(item):
    return [item]