# -*- coding: utf-8 -*-
# -*- Channel Pelkex -*-
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

host = 'http://pelkex.net/'

IDIOMAS = {'Latino': 'LAT'}
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['openload', 'streamango', 'fastplay', 'okru', 'rapidvideo']

def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data

def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = []

    itemlist.append(Item(channel=item.channel, title="Todas", action="list_all", url=host,
                         thumbnail=get_thumb('all', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Generos", action="section",
                         thumbnail=get_thumb('genres', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Por Años", action="section",
                         thumbnail=get_thumb('year', auto=True)))

    itemlist.append(Item(channel=item.channel, title = 'Buscar', action="search", url=host + '?s=', pages=3,
                         thumbnail=get_thumb('search', auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def list_all(item):
    logger.info()

    itemlist = []
    data = get_source(item.url)
    patron = '<a class="ah-imagge" href="([^"]+)">.*?src="([^"]+).*?title="([^"]+)".*?Calificacion(.*?)ratebox'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle, year_data in matches:
        url = scrapedurl
        year = scrapertools.find_single_match(year_data, '>Año<.*?>(\d{4})')
        if not year:
            year = '-'
        scrapedtitle = scrapedtitle
        thumbnail = scrapedthumbnail
        new_item = Item(channel=item.channel, title=scrapedtitle, url=url, action='findvideos',
                        thumbnail=thumbnail, infoLabels={'year':year})

        new_item.contentTitle=scrapedtitle
        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # Paginacion


    next_page = scrapertools.find_single_match(data, '<a class="next page-numbers" href="([^"]+)">')
    if next_page:
        itemlist.append(Item(channel=item.channel, action="list_all", title='Siguiente >>>', url=next_page))

    return itemlist

def section(item):
    logger.info()

    itemlist = []
    data=get_source(host)
    if item.title == 'Generos':
        data = scrapertools.find_single_match(data, '<a href="#">Genero</a>(.*?)</ul>')
    elif 'Años' in item.title:
        data = scrapertools.find_single_match(data, '<a href="#">Año</a>(.*?)</ul>')

    patron = 'href="([^"]+)">([^<]+)</a>'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for url, title in matches:

        itemlist.append(Item(channel=item.channel, title=title, url=url, action='list_all'))

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = []
    data = get_source(item.url)
    patron = 'data-url="([^"]+)" data-postId="\d+">([^<]+)<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, server in matches:
        url = scrapedurl
        if server.lower() != 'trailer':
            itemlist.append(Item(channel=item.channel, title='%s', url=url, action='play', language=IDIOMAS['Latino'],
                                 infoLabels=item.infoLabels))

    patron = '<a href="([^"]+)" class="download-link"'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl in matches:
        url = scrapedurl
        server = ''
        if 'magnet' in url:
            server = 'torrent'
        if url not in itemlist:
            itemlist.append(Item(channel=item.channel, title='%s', url=url, action='play', language=IDIOMAS['Latino'],
                                 infoLabels=item.infoLabels, server=server))


    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             url=item.url, action="add_pelicula_to_library", extra="findvideos",
                             contentTitle=item.contentTitle))

    return itemlist


def search(item, texto):
    logger.info()
    itemlist = []
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    if texto != '':
        try:
            return list_all(item)
        except:
            itemlist.append(item.clone(url='', title='No hay elementos...', action=''))
            return itemlist

def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria in ['peliculas', 'latino']:
            item.url = host + '?s='
        elif categoria == 'infantiles':
            item.url = host + 'genre/animacion/'
        elif categoria == 'terror':
            item.url = host + 'genre/terror/'
        item.pages=3
        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist

