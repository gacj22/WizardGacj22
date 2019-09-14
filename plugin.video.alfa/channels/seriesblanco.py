# -*- coding: utf-8 -*-
# -*- Channel SeriesBlanco -*-
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

host = 'http://seriesblanco.org/'

IDIOMAS = {'es': 'Cast', 'la': 'Lat', 'vos': 'VOSE', 'vo': 'VO'}
list_language = IDIOMAS.values()
list_quality = ['SD', 'Micro-HD-720p', '720p', 'HDitunes', 'Micro-HD-1080p' ]
list_servers = ['powvideo','yourupload', 'openload', 'gamovideo', 'flashx', 'clipwatching', 'streamango', 'streamcloud']


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = []

    itemlist.append(Item(channel=item.channel,
                         title="Últimas series",
                         action="new_series",
                         thumbnail=get_thumb('last', auto=True),
                         url=host))

    itemlist.append(Item(channel=item.channel,
                         title="Todas",
                         action="list_all",
                         thumbnail=get_thumb('all', auto=True),
                         url=host + 'lista-de-series/',
                         ))

    itemlist.append(Item(channel=item.channel,
                         title="Generos",
                         action="section",
                         thumbnail=get_thumb('genres', auto=True),
                         url=host,
                         ))

    itemlist.append(Item(channel=item.channel,
                         title="A - Z",
                         action="section",
                         thumbnail=get_thumb('alphabet', auto=True),
                         url=host+'lista-de-series/', ))

    itemlist.append(Item(channel=item.channel,
                         title="Buscar",
                         action="search",
                         url=host+"?s=",
                         thumbnail=get_thumb('search', auto=True)))

    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality)
    autoplay.show_option(item.channel, itemlist)

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
    contentSerieName = ''

    patron = '<div style="float.*?<a href="([^"]+)">.*?src="([^"]+)".*?data-original-title="([^"]+)">'
    matches = re.compile(patron, re.DOTALL).findall(data)


    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:

        url = scrapedurl
        thumbnail = scrapedthumbnail
        title = scrapertools.decodeHtmlentities(scrapedtitle)

        itemlist.append(Item(channel=item.channel,
                             action='seasons',
                             title=title,
                             url=url,
                             thumbnail=thumbnail,
                             contentSerieName=scrapedtitle,
                             context=filtertools.context(item, list_language, list_quality),
                             ))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # #Paginacion

    if itemlist != []:
        next_page = scrapertools.find_single_match(data, '<a class="next page-numbers" href="([^"]+)">')
        if next_page != '':
            itemlist.append(Item(channel=item.channel,
                                 action="list_all",
                                 title='Siguiente >>>',
                                 url=next_page,
                                 thumbnail='https://s16.postimg.cc/9okdu7hhx/siguiente.png',
                                 ))
    return itemlist

def list_from_genre(item):
    logger.info()

    itemlist = []
    data = get_source(item.url)
    contentSerieName = ''

    patron = '<div style="float.*?<a href="([^"]+)">.*?src="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail in matches:
        url = scrapedurl
        thumbnail = scrapedthumbnail
        title = scrapertools.find_single_match(scrapedurl, 'https://seriesblanco.org/capitulos/([^/]+)/')
        title = title.replace('-', ' ').capitalize()

        itemlist.append(Item(channel=item.channel,
                             action='seasons',
                             title=title,
                             url=url,
                             thumbnail=thumbnail,
                             contentSerieName=title,
                             context=filtertools.context(item, list_language, list_quality),
                             ))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # #Paginacion

    if itemlist != []:
        next_page = scrapertools.find_single_match(data, '<a href="([^"]+)" ><i class="Next')
        if next_page != '':
            itemlist.append(Item(channel=item.channel,
                                 action="list_from_genre",
                                 title='Siguiente >>>',
                                 url=next_page,
                                 thumbnail='https://s16.postimg.cc/9okdu7hhx/siguiente.png',
                                 ))
    return itemlist




def section(item):
    logger.info()

    itemlist = []
    data = get_source(item.url)
    if item.title == 'Generos':
        patron = '<li><a href="([^ ]+)"><i class="fa fa-bookmark-o"></i> ([^<]+)</a></li>'
        action = 'list_from_genre'
    elif item.title == 'A - Z':
        patron = '<a dir="ltr" href="([^"]+)" class="label label-primary">([^<]+)</a>'
        action = 'list_all'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:

        url = scrapedurl
        title = scrapedtitle
        itemlist.append(Item(channel=item.channel,
                             action=action,
                             title=title,
                             url=url
                             ))
    return itemlist

def seasons(item):
    logger.info()
    itemlist = []
    data = get_source(item.url)
    patron = '<span itemprop="seasonNumber" class="fa fa-arrow-down">.*?Temporada (\d+) '
    matches = re.compile(patron, re.DOTALL).findall(data)
    infoLabels=item.infoLabels
    for scrapedseason in matches:
        url = item.url
        title = 'Temporada %s' % scrapedseason
        contentSeasonNumber = scrapedseason
        infoLabels['season'] = contentSeasonNumber
        thumbnail = item.thumbnail
        itemlist.append(Item(channel=item.channel,
                             action="episodesxseason",
                             title=title,
                             url=url,
                             thumbnail=thumbnail,
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
    data = get_source(item.url)
    season = item.contentSeasonNumber
    season_data = scrapertools.find_single_match(data, '<div id="collapse%s".*?</tbody>' % season)
    patron = '<td><a href="([^ ]+)".*?itemprop="episodeNumber">%sx(\d+)</span> (.*?) </a>.*?<td>(.*?)</td>' % season
    matches = re.compile(patron, re.DOTALL).findall(season_data)
    infoLabels = item.infoLabels
    for scrapedurl, scraped_episode, scrapedtitle, lang_data in matches:
        url = scrapedurl
        title = '%sx%s - %s' % (season, scraped_episode, scrapedtitle.strip())
        infoLabels['episode'] = scraped_episode
        thumbnail = item.thumbnail
        title, language = add_language(title, lang_data)
        itemlist.append(Item(channel=item.channel,
                             action="findvideos",
                             title=title,
                             url=url,
                             thumbnail=thumbnail,
                             language=language,
                             infoLabels=infoLabels
                             ))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    itemlist = filtertools.get_links(itemlist, item, list_language)

    return itemlist

def new_episodes(item):
    logger.info()
    itemlist = []

    data = get_source(item.url)
    data = scrapertools.find_single_match(data,
                                          '<center>Series Online : Capítulos estrenados recientemente</center>.*?</ul>')
    patron = '<li><h6.*?src="([^"]+)".*?alt=" (\d+x\d+).+?".*?href="([^"]+)">.*?src="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for lang_data, scrapedinfo, scrapedurl, scrapedthumbnail in matches:

        url =scrapedurl
        thumbnail = scrapedthumbnail
        scrapedinfo = scrapedinfo.split('x')
        season = scrapedinfo[0]
        episode = scrapedinfo[1]
        scrapedtitle = scrapertools.find_single_match(url, 'capitulo/([^/]+)/')
        url = '%scapitulos/%s' % (host, scrapedtitle)
        title = '%s - %sx%s' % (scrapedtitle.replace('-', ' '), season, episode )
        title, language = add_language(title, lang_data)
        itemlist.append(Item(channel=item.channel,
                             action='seasons',
                             title=title,
                             url=url,
                             thumbnail=thumbnail,
                             language=language,
                              ))
        tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist

def new_series(item):
    logger.info()
    itemlist = []

    data = get_source(item.url)
    data = scrapertools.find_single_match(data,
                                          '>Series Online gratis más vistas</center>.*?</ul>')
    patron = '<a href="([^"]+)"><img src="([^"]+)".*?alt="(.*?)"'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:

        url =scrapedurl
        thumbnail = scrapedthumbnail
        itemlist.append(Item(channel=item.channel,
                             action='seasons',
                             title=scrapedtitle,
                             url=url,
                             contentSerieName=scrapedtitle,
                             thumbnail=thumbnail
                              ))
        tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist

def add_language(title, string):
    logger.info()
    languages = scrapertools.find_multiple_matches(string, '/language/(.*?).png')
    language = []
    for lang in languages:

        if 'jap' in lang or lang not in IDIOMAS:
            lang = 'vos'

        if len(languages) == 1:
            language = IDIOMAS[lang]
            if not config.get_setting('unify'):
                title = '%s [%s]' % (title, language)
        else:
            language.append(IDIOMAS[lang])
            if not config.get_setting('unify'):
                title = '%s [%s]' % (title, IDIOMAS[lang])

    return title, language


def findvideos(item):
    logger.info()

    itemlist = []

    data = get_source(item.url)
    patron = '<imgsrc="([^"]+)".*?<a class="open-link" data-enlace="([^"]+)".*?<td>([^<]+)</td>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for lang_data, scrapedurl, quality in matches:
        encrypted=False
        title = '%s'
        if quality == '':
            quality = 'SD'
        title = '%s [%s]' % (title, quality)
        title, language = add_language(title, lang_data)
        thumbnail = item.thumbnail
        url = scrapedurl
        if 'streamcrypt' in url:
            url = url.replace('https://streamcrypt', 'https://www.streamcrypt')
            temp_data = httptools.downloadpage(url, follow_redirects=False, only_headers=True)
            if 'location' in temp_data.headers:
                url = temp_data.headers['location']
            else:
                continue
        itemlist.append(Item(channel=item.channel,
                             title=title,
                             url=url,
                             action="play",
                             thumbnail=thumbnail,
                             quality=quality,
                             language=language,
                             encrypted=encrypted,
                             infoLabels=item.infoLabels
                             ))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    return sorted(itemlist, key=lambda it: it.language)

def search_results(item):
    logger.info()
    itemlist = []

    data = get_source(item.url)

    patron = '<div style="float.*?<a href="([^"]+)">.*?src="([^"]+)".*?alt="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumb, scrapedtitle in matches:
        itemlist.append(Item(channel=item.channel,
                             title=scrapedtitle,
                             url=host+scrapedurl,
                             action="seasons",
                             thumbnail=scrapedthumb,
                             contentSerieName=scrapedtitle,
                             context=filtertools.context(item, list_language, list_quality)
                             ))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist

def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto

    if texto != '':
        return list_all(item)
    else:
        return []