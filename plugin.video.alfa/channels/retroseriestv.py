# -*- coding: utf-8 -*-
# -*- Channel RetroSeriesTV -*-
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


host = 'https://retroseriestv.com/'

# IDIOMAS = {'la': 'LAT', 'es': 'Cast'}
# list_language = IDIOMAS.values()
# list_quality = []
# list_servers = ['openload']


def mainlist(item):
    logger.info()

    itemlist = list()
    itemlist.append(item.clone(title="Todas", action="list_all", url=host + 'seriestv/', thumbnail=get_thumb('all',
                                                                                                         auto=True)))

    itemlist.append(item.clone(title="Generos", action="section", url=host, thumbnail=get_thumb('genres', auto=True),
                               section='genres'))

    itemlist.append(item.clone(title="Por Año", action="section", url=host, thumbnail=get_thumb('year', auto=True),
                               section='releases'))

    #itemlist.append(item.clone(title="Alfabetico", action="section", url=host, thumbnail=get_thumb('alphabet', auto=True),
    #                           section='glossary'))

    itemlist.append(item.clone(title="Buscar", action="search", url=host+'?s=',
                               thumbnail=get_thumb('search', auto=True)))

    return itemlist


def get_source(url, referer=None):
    logger.info()
    if referer is None:
        data = httptools.downloadpage(url, ignore_response_code=True).data
    else:
        data = httptools.downloadpage(url, headers={'Referer':referer}).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data

def list_all(item):
    logger.info()
    itemlist = []

    data = get_source(item.url)
    patron = '<article id="post-\d+.*?<img src="([^"]+)" alt="([^"]+)">.*?'
    patron += '<a href="([^"]+)">.*?</h3> <span>(.*?)<'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedthumbnail, scrapedtitle, scrapedurl, year_data in matches:

        year = scrapertools.find_single_match(year_data, '(d{4})')
        url = scrapedurl
        contentSerieName = scrapedtitle
        thumbnail = scrapedthumbnail
        itemlist.append(item.clone(action='seasons',
                                   title=contentSerieName,
                                   url=url,
                                   thumbnail=thumbnail,
                                   contentSerieName=contentSerieName,
                                   infoLabels={'year':year}
                                   ))
    tmdb.set_infoLabels_itemlist(itemlist, True)

    #  Paginación
    url_next_page = scrapertools.find_single_match(data, "<span class=\"current\">\d+</span><a href='([^']+)'")
    if url_next_page:
        itemlist.append(item.clone(title="Siguiente >>", url=url_next_page, action='list_all'))
    return itemlist

def section(item):
    logger.info()

    itemlist = []

    data = get_source(item.url)
    data = scrapertools.find_single_match(data, '<ul class="%s(.*?)</ul>' % item.section)
    patron = '<a href="([^"]+)".?>(.*?)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        url = scrapedurl.strip()
        itemlist.append(Item(channel=item.channel, title=scrapedtitle, url=url, action='list_all'))

    return itemlist

def seasons(item):
    logger.info()

    itemlist = []
    data = get_source(item.url).replace("'", '"')
    patron = '<span class="title">Temporada (\d+) <'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedtitle in matches:
        infoLabels = item.infoLabels
        infoLabels['season'] = scrapedtitle
        title = 'Temporada %s' % scrapedtitle
        itemlist.append(Item(channel=item.channel, title=title, url=item.url, action='episodesxseason',
                             infoLabels=infoLabels))
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

    data = get_source(item.url).replace("'", '"')
    infoLabels = item.infoLabels
    season = infoLabels['season']
    patron = '<img src="([^>]+)"></div><div class="numerando">%s+ - (\d+|\d+\/\d+)</div>' % season
    patron += '<div class="episodiotitle"><a href="([^"]+)">(.*?)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedthumbnail, scrapedepi, scrapedurl, scrapedtitle in matches:

        if '/' in scrapedepi:
            scrapedepi = scrapertools.find_single_match (scrapedepi, '(\d+)\/\d+')

        title = '%sx%s - %s' % (season, scrapedepi, scrapedtitle)
        infoLabels['episode'] = scrapedepi
        if scrapedepi > 0:
            itemlist.append(Item(channel=item.channel, title=title, url=scrapedurl, action='findvideos',
                            infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist

def findvideos(item):
    logger.info()
    from lib import generictools
    import urllib
    itemlist = []
    data = get_source(item.url).replace("'", '"')
    patron = 'data-post="(\d+)" data-nume="(\d+)".*?img src="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for id, option, lang in matches:
        lang = scrapertools.find_single_match(lang, '.*?/flags/(.*?).png')
        if lang == 'ar':
            lang = 'lat'
        post = {'action': 'doo_player_ajax', 'post': id, 'nume': option, 'type':'tv'}
        post = urllib.urlencode(post)

        test_url = '%swp-admin/admin-ajax.php' % host
        new_data = httptools.downloadpage(test_url, post=post, headers={'Referer':item.url}).data
        url = scrapertools.find_single_match(new_data, "src='([^']+)'")
        if url != '':
            itemlist.append(
                Item(channel=item.channel, url=url, title='%s', action='play', language=lang,
                     infoLabels=item.infoLabels))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())

    return itemlist

def search_results(item):
    logger.info()

    itemlist = []

    data = get_source(item.url)
    data = scrapertools.find_single_match(data, '<h1>Resultados encontrados:(.*?)genres')
    patron = '<article.*?<a href="([^"]+)"><img src="([^"]+)".*?alt="([^"]+)".*?class="year">(\d{4}).*?<p>([^<]+)</p>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle, year, scrapedplot in matches:

        url = scrapedurl
        contentSerieName = scrapedtitle.replace(' /','')
        thumbnail = scrapedthumbnail
        itemlist.append(item.clone(action='seasons',
                                   title=contentSerieName,
                                   url=url,
                                   thumbnail=thumbnail,
                                   plot=scrapedplot,
                                   contentSerieName=contentSerieName,
                                   infoLabels={'year':year}
                                   ))
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
