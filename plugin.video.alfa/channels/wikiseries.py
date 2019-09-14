# -*- coding: utf-8 -*-
# -*- Channel wikiseries -*-
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

host = 'http://www.wikiseriesonline.nu/'

list_language = ['Latino', 'Español', 'VOSE', 'VO']
list_quality = []
list_servers = ['openload']

def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data

def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist =[]

    itemlist.append(
        Item(channel=item.channel, title="Nuevos Capitulos", action="list_all", url=host + 'category/episode',
             thumbnail=get_thumb('new episodes', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Todas", action="list_all", url=host + 'category/serie',
                         thumbnail=get_thumb('all', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Generos", action="genres",
                         url=host + 'latest-episodes', thumbnail=get_thumb('genres', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=host + '?s=',
                         thumbnail=get_thumb('search', auto=True)))

    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality)
    autoplay.show_option(item.channel, itemlist)
    return itemlist

def list_all(item):
    logger.info()

    itemlist = []

    data = get_source(item.url)
    patron = '39;src=.*?(http.*?)style=display:.*?one-line href=(.*?) title=.*?>(.*?)<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedthumbnail, scrapedurl, scrapedtitle in matches:
        url = scrapedurl
        scrapedtitle = scrapedtitle.replace('&#215;','x')

        contentSerieName = scrapedtitle
        action = 'seasons'

        if 'episode' in item.url:
            scrapedtitle, season, episode = scrapertools.find_single_match(scrapedtitle,
                                                                           '(.*?) (\d+).*?(?:x|X).*?(\d+)')
            contentSerieName = scrapedtitle
            scrapedtitle = '%sx%s - %s' % (season, episode, scrapedtitle)
            action='findvideos'

        thumbnail = scrapedthumbnail
        new_item = Item(channel=item.channel, title=scrapedtitle, url=url,
                        thumbnail=thumbnail, contentSerieName=contentSerieName, action=action,
                        context=filtertools.context(item, list_language, list_quality))

        if 'episode' in item.url:
            new_item.contentSeasonNumber = season
            new_item.contentepisodeNumber = episode
            new_item.context = []

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # Paginacion
    next_page = scrapertools.find_single_match(data, 'rel=next href=(.*?)>»</a>')
    if next_page != '':
        itemlist.append(Item(channel=item.channel, action="list_all", title='Siguiente >>>',
                             url=next_page, thumbnail='https://s16.postimg.cc/9okdu7hhx/siguiente.png',
                             type=item.type))
    return itemlist


def genres(item):

    itemlist = []

    data = get_source(host)
    patron = '<li> <a href=(/category/.*?)>(.*?)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:

        if scrapedtitle != 'Series':
            itemlist.append(Item(channel=item.channel, title=scrapedtitle, url=host + scrapedurl, action='list_all'))

    return itemlist


def seasons(item):
    logger.info()
    itemlist = []

    data = get_source(item.url)

    patron = 'data-season-num=1>(.*?)</span>'

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
    season = item.contentSeasonNumber
    patron = '<li class=ep-list-item id=s%se(\d+)>.*?<a href=(.*?) >.*?name>(.*?)<.*?class=lgn (.*?)</a>' % season

    matches = re.compile(patron, re.DOTALL).findall(data)
    infoLabels = item.infoLabels
    for scrapedepi, scrapedurl, scrapedtitle, languages in matches:
        url = scrapedurl
        language = scrapertools.find_multiple_matches(languages, 'title=(.*?)>')
        contentEpisodeNumber = scrapedepi
        title = '%sx%s - %s %s' % (season, contentEpisodeNumber, scrapedtitle, language)
        infoLabels['episode'] = contentEpisodeNumber
        itemlist.append(Item(channel=item.channel, action="findvideos", title=title, url=url,
                             contentSerieName=item.contentSerieName, contentEpisodeNumber=contentEpisodeNumber,
                             language=language, infoLabels=infoLabels))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist

def search(item, text):
    logger.info()

    item.url = item.url + text
    item.text = text
    item.type = 'search'
    if text != '':
        #return list_all(item)
        return search_results(item)


def search_results(item):
    import urllib
    itemlist = []
    headers={"Origin": "http://www.wikiseriesonline.nu",
        "Accept-Encoding": "gzip, deflate", "Host": "www.wikiseriesonline.nu",
        "Accept-Language": "es-ES,es;q=0.8,en;q=0.6",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Accept": "*/*", "Referer": item.url,
        "X-Requested-With": "XMLHttpRequest", "Connection": "keep-alive",  "Content-Length": "7"}
    post = {"n":item.text}
    post = urllib.urlencode(post)
    url = host + 'wp-content/themes/wikiSeries/searchajaxresponse.php'
    data = httptools.downloadpage(url, post=post, headers=headers).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)

    patron = "<!-- .Posts -->.*?<a href=(.*?)>.*?src=(.*?) .*?titleinst>(.*?)<"
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        if item.text.lower() in scrapedtitle.lower():
            itemlist.append(Item(channel=item.channel, title=scrapedtitle, contentSerieName=scrapedtitle, url=scrapedurl,
                            thumbnail=scrapedthumbnail, action='seasons',
                            context=filtertools.context(item, list_language, list_quality)))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist


def findvideos(item):

    itemlist = []
    data=get_source(item.url)
    patron = '<a href=(/reproductor.*?)target'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for link in matches:
        video_data = get_source(host+link)
        language = ''
        if 'latino' in link.lower():
            language='Latino'
        elif 'espaÑol' in link.lower():
            language = 'Español'
        elif 'subtitulado' in link.lower():
            language = 'VOSE'
        elif 'vo' in link.lower():
            language = 'VO'

        url = scrapertools.find_single_match(video_data, '<iframe src=(.*?) scrolling')
        title = '%s [%s]'

        itemlist.append(Item(channel=item.channel, title=title, url=url, action='play', language=language,
                             infoLabels=item.infoLabels))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % (x.server.capitalize(), x.language))

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    return itemlist





