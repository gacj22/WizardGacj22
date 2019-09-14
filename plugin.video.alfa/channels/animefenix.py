# -*- coding: utf-8 -*-
# -*- Channel AnimeFenix -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

from bs4 import BeautifulSoup
from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from channels import filtertools, autoplay
from core import tmdb


IDIOMAS = {'vose': 'VOSE'}
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['directo', 'verystream', 'openload',  'streamango', 'uploadmp4', 'fembed']

host = "https://www.animefenix.com/"

def mainlist(item):
    logger.info()

    itemlist = list()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(Item(channel=item.channel, title="Nuevos Capítulos", url=host, action="new_episodes",
                         thumbnail=get_thumb('new episodes', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Emision", url=host + 'animes?type%5B%5D=tv&estado%5B%5D=1',
                         action="list_all", thumbnail=get_thumb('on air', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Recientes", url=host, action="list_all",
                         thumbnail=get_thumb('recents', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Todas", url=host+'animes', action="list_all",
                        thumbnail=get_thumb('all', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Buscar", url=host + 'animes?q=', action="search",
                         thumbnail=get_thumb('search', auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def create_soup(url, referer=None, unescape=False):
    logger.info()

    if referer:
        data = httptools.downloadpage(url, headers={'Referer':referer}).data
    else:
        data = httptools.downloadpage(url).data

    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")

    return soup


def new_episodes(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)

    for elem in soup.find_all("div", "overarchingdiv"):
        title = elem.img["alt"]
        thumb = elem.img["src"]
        url = elem.a["href"]
        name = elem.find("div", class_="overtitle").text
        itemlist.append(Item(channel=item.channel, title=title, thumbnail=thumb, url=url, action="findvideos",
                             contentSerieName=name))

    tmdb.set_infoLabels_itemlist(itemlist, True)
    return itemlist


def episodios(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url).find("div", class_="column is-12")

    infoLabels = item.infoLabels

    for elem in soup.find_all("li"):
        url = elem.a["href"]
        epi_num = scrapertools.find_single_match(elem.span.text, "(\d+)")
        infoLabels['season'] = '1'
        infoLabels['episode'] = epi_num
        title = '1x%s - Episodio %s' % (epi_num, epi_num)
        itemlist.append(Item(channel=item.channel, title=title, url=url, action='findvideos', infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, True)

    itemlist = itemlist[::-1]

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]', url=item.url,
                 action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName,
                 extra1='library'))

    return itemlist


def list_all(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url).find("div", class_="list-series")

    for elem in soup.find_all("article", class_="serie-card"):
        url = elem.a["href"]
        title = elem.a["title"]
        thumb = elem.img["src"]
        itemlist.append(Item(channel=item.channel, title=title, url=url, action='episodios',
                             thumbnail=thumb, contentSerieName=title))

    tmdb.set_infoLabels_itemlist(itemlist, True)
    return itemlist


def findvideos(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url, unescape=True)

    pl = soup.find("div", class_="player-container")
    script = pl.find("script").text
    urls = scrapertools.find_multiple_matches(script, "src='([^']+)'")

    for url in urls:

        if "/stream/" in url:
            url = host+url.replace('..', '').replace("/stream/", "stream/")
            data = httptools.downloadpage(url, headers={'Referer': item.url}).data
            url = scrapertools.find_single_match(data, '"file":"([^"]+)"').replace('\\/', '/')

        itemlist.append(Item(channel=item.channel, title='%s', action='play', url=url, language=IDIOMAS['vose'],
                             infoLabels=item.infoLabels))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    if texto != '':
        return list_all(item)
    else:
        return []


def newest(categoria):
    itemlist = []
    item = Item()
    if categoria == 'anime':
        item.url=host
        itemlist = new_episodes(item)
    return itemlist