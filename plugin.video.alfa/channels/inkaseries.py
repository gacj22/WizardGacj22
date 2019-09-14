# -*- coding: utf-8 -*-
# -*- Channel InkaSeries -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re

from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb

host = 'https://www.inkaseries.net/'

IDIOMAS = {'Latino': 'LAT', 'Castellano':'CAST', 'Subtitulado': 'VOSE'}
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['openload', 'gamovideo', 'streamplay', 'flashx', 'streamito', 'streamango', 'vidoza']

def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data

def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = []

    itemlist.append(Item(channel= item.channel, title="Todas", action="list_all", url=host + 'ultimas-series-agregadas/',
                         thumbnail=get_thumb('all', auto=True)))
    itemlist.append(Item(channel= item.channel, title="Generos", action="genres", url=host,
                         thumbnail=get_thumb('genres', auto=True)))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=host+'?s=',
                         thumbnail=get_thumb('search', auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def list_all(item):
    logger.info()

    itemlist = []
    data = get_source(item.url)
    data1 = scrapertools.find_single_match(data, '<div class="col-md-80 lado2"(.*?)</div></div></div>')
    patron = '<a class="poster" href="([^"]+)" title="([^"]+)"><img.*?src="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data1)

    for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
        url = scrapedurl
        thumbnail = scrapedthumbnail
        scrapedtitle = scrapedtitle
        filter_thumb = scrapedthumbnail.replace("https://image.tmdb.org/t/p/w185", "")
        filter_list = {"poster_path": filter_thumb}
        filter_list = filter_list.items()
        itemlist.append(
            Item(channel=item.channel, action='seasons', title=scrapedtitle, url=url, thumbnail=thumbnail,
                 contentSerieName=scrapedtitle, infoLabels={'filtro': filter_list}))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    # Paginacion

    if itemlist != []:
        actual_page_url = item.url
        next_page = scrapertools.find_single_match(data, '<li><a href="([^"]+)"><span aria-hidden="true">&raquo;</span>')
        if next_page != '':
            itemlist.append(Item(channel=item.channel, action="list_all", title='Siguiente >>>', url=next_page,
                                 thumbnail='https://s16.postimg.cc/9okdu7hhx/siguiente.png'))
    return itemlist


def seasons(item):
    logger.info()
    itemlist = []

    data = get_source(item.url)

    patron = '</span>Temporada (\d+)</a>'

    matches = re.compile(patron, re.DOTALL).findall(data)
    infoLabels = item.infoLabels
    for scrapedseason in matches:
        contentSeasonNumber = scrapedseason
        title = 'Temporada %s' % scrapedseason
        infoLabels['season'] = contentSeasonNumber

        itemlist.append(Item(channel=item.channel, action='episodesxseason', url=item.url, title=title,
                             contentSeasonNumber=contentSeasonNumber, infoLabels=infoLabels))
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
    data = get_source(item.url)

    if item.extra1 != 'library':
        patron = '<tr><td>.*?<a href="([^"]+)" title="Temporada %s, Episodio (\d+.*?)">' % item.contentSeasonNumber
    else:
        patron = '<tr><td>.*?<a href="([^"]+)" title=Temporada \d+, Episodio (\d+.*?)">'

    matches = re.compile(patron, re.DOTALL).findall(data)
    infoLabels = item.infoLabels
    for scrapedurl, dataep in matches:
        url = scrapedurl
        dataep = dataep.split(' - ')
        contentEpisodeNumber = dataep[0]
        try:
            title = '%sx%s - %s' % (item.infoLabels['season'], contentEpisodeNumber, dataep[1])
        except:
            title = 'episodio %s' % contentEpisodeNumber
        infoLabels['episode'] = contentEpisodeNumber
        infoLabels = item.infoLabels

        itemlist.append(Item(channel=item.channel, action="findvideos", title=title, url=url,
                             contentEpisodeNumber=contentEpisodeNumber, infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def genres(item):
    logger.info()

    itemlist = []
    norep = []
    data = get_source(item.url)
    logger.error(data)
    patron = '<a href="([^"]+)">.*?<i>([^<]+)</i> <b>(\d+)</b>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle, cantidad in matches:

        url = scrapedurl
        title = "%s (%s)" % (scrapedtitle.capitalize(), cantidad)
        itemactual = Item(channel=item.channel, action='list_all', title=title, url=url)

        if title not in norep:
            itemlist.append(itemactual)
            norep.append(itemactual.title)
    return itemlist

def findvideos(item):
    logger.info()

    itemlist = []
    data = get_source(item.url)
    patron = '<td><a href="([^"]+)" class="btn.*?style="margin:.*?<span>.*?</span></td><td>(.*?)</td><td>.*?</td>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for url, language in matches:
        new_item = Item(channel=item.channel, title='%s [%s]', url=url, language=IDIOMAS[language], action='play',
                        infoLabels=item.infoLabels)
        itemlist.append(new_item)
    itemlist = servertools.get_servers_itemlist(itemlist,  lambda x: x.title % (x.server.capitalize(), x.language))

    # Requerido para FilterTools
    tmdb.set_infoLabels_itemlist(itemlist, True)
    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)



    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    item.type = 'search'
    if texto != '':
        return list_all(item)
