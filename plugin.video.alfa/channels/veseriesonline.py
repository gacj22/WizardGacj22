# -*- coding: utf-8 -*-
# -*- Channel VeSeriesOnline -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
import base64

from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb

list_language = ['Lat', 'Cast', 'VOSE', 'VO']
list_quality = []
list_servers = ['openload', 'netutv', 'streamango', 'streamix', 'powvideo', 'gamovideo']

host = 'http://www.veseriesonline.com/'

def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = []

    itemlist.append(Item(channel=item.channel,
                         title="Todas",
                         action="list_all",
                         thumbnail=get_thumb('all', auto=True),
                         url=host + 'archivos/h1/',
                         ))

    itemlist.append(Item(channel=item.channel,
                         title="Buscar",
                         action="search",
                         url=host+'?s=',
                         thumbnail=get_thumb('search', auto=True)))

    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality)
    autoplay.show_option(item.channel, itemlist)

    return itemlist

def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data


def list_all(item):
    logger.info()

    itemlist = []
    data = get_source(item.url)
    patron = "<article class=movie>.*?href=(.*?) class.*?src=(.*?) style.*?<h2>(.*?)</h2>"
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        episode = ''
        url = scrapedurl
        thumbnail = scrapedthumbnail
        if 'Temporada' in scrapedtitle:
            episode = scrapertools.find_single_match(scrapedtitle, '.*?Temporada (\d+x\d+)')
            scrapedtitle = scrapertools.find_single_match(scrapedtitle, '(.*?) Temporada')

        scrapedtitle = scrapedtitle.replace(' Online','')
        contentSerieName = scrapedtitle
        if episode != '':
            title = '%s - %s' % (scrapedtitle, episode)
        else:
            title = scrapedtitle

        itemlist.append(Item(channel=item.channel,
                             action='seasons',
                             title=title,
                             url=url,
                             thumbnail=thumbnail,
                             contentTitle=scrapedtitle,
                             context=filtertools.context(item, list_language, list_quality),
                             contentSerieName=contentSerieName,
                             ))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    if itemlist != []:
        next_page = scrapertools.find_single_match(data ,"<a href='([^']+)' class='pagination__link'>&rsaquo;</a>")
        if next_page != '':
            itemlist.append(Item(channel=item.channel,
                                 action="list_all",
                                 title='Siguiente >>>',
                                 url=next_page,
                                 thumbnail='https://s16.postimg.cc/9okdu7hhx/siguiente.png',
                                 ))
    return itemlist

def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    if texto != '':
        return list_all(item)

def seasons(item):
    logger.info()

    itemlist = []
    data = get_source(item.url)
    patron = 'itemprop=season.*?<a href=(.*?) rel=bookmark.*?src=(.*?)>.*?;>(.*?)<'
    matches = re.compile(patron, re.DOTALL).findall(data)
    if len(matches) == 0:
        patron = '<article class=movie>.*?href=(.*?) class.*?src=(.*?) style.*?title=.*?(Temporada \d+) alt'
        matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedthumb, scrapedtitle in matches:
        infoLabels = item.infoLabels
        infoLabels['season'] = scrapertools.find_single_match(scrapedtitle, 'Temporada (\d+)')
        itemlist.append(Item(channel=item.channel, title=scrapedtitle, url=scrapedurl, action='episodesxseason',
                             thumbnail=scrapedthumb, infoLabels=infoLabels))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    itemlist = itemlist [::-1]

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
    patron = '<li class=series-cat><a target=_blank href=(.*?) class.*?'
    patron += 'title=.*?;(\d+).*?<span>(.*?)</span><span class=flags(.*?)</a></li>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    infoLabels = item.infoLabels
    for scrapedurl, scrapedepi, scrapedtitle, lang_data in matches:
        language = []
        if 'lang-lat>' in lang_data:
            language.append('Lat')
        if 'lang-spa>' in lang_data:
            language.append('Cast')
        if 'lang-engsub>' in lang_data:
            language.append('VOSE')
        if 'lang-eng>' in lang_data:
            language.append('VO')

        title = '%sx%s - %s %s' % (infoLabels['season'], scrapedepi, scrapedtitle, language)
        infoLabels['episode'] = scrapedepi
        itemlist.append(Item(channel=item.channel, title=title, url=scrapedurl, action='findvideos', language=language,
                        infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    itemlist = filtertools.get_links(itemlist, item, list_language)
    return itemlist

def findvideos(item):
    logger.info()
    itemlist = []

    data = get_source(item.url)
    video_id = scrapertools.find_single_match(data, 'getEnlaces\((\d+)\)')
    links_url = '%s%s%s' % (host,'link/repro.php/',video_id)
    online_url = '%s%s%s' % (host, 'link/enlaces_online.php/', video_id)

    # listado de opciones links_url

    try:
        data = get_source(links_url)
        patron = 'content ><h2>(.*?)</h2>.*?class=video.*?src=(.*?) scrolling'
        matches = re.compile(patron, re.DOTALL).findall(data)

        for lang_data, scrapedurl in matches:
            if 'Latino' in lang_data:
                language = 'Lat'
            elif 'Español' in lang_data:
                language = 'Cast'
            else:
                language = 'VOSE'
            hidden_url = scrapedurl.replace('/i/', '/r/')
            data = get_source(hidden_url)
            url = scrapertools.find_single_match(data, ':url content=(.*?)>')
            title = '%s '+ '[%s]' % language
            if url != '':
                itemlist.append(Item(channel=item.channel, title=title, url=url, action='play', language=language,
                                     infoLabels=item.infoLabels))
    except:
        pass

    # listado de enlaces online_url
    try:
        data = get_source(online_url)
        patron = '<i class=lang-(.*?)>.*?href=(.*?) '
        matches = re.compile(patron, re.DOTALL).findall(data)
        scrapertools.printMatches(matches)
        for lang_data, scrapedurl in matches:
            if 'lat' in lang_data:
                language = 'Lat'
            elif 'spa' in lang_data:
                language = 'Cast'
            elif 'eng' in lang_data:
                language = 'VOSE'
            else:
                language = 'VO'
            video_id = scrapertools.find_single_match(scrapedurl, 'index.php/(\d+)/')
            new_url = '%s%s%s%s' % (host, 'ext/index-include.php?id=', video_id, '&tipo=1')
            data = get_source(new_url)
            video_url = scrapertools.find_single_match(data, '<div class=container><a onclick=addURL.*?href=(.*?)>')
            video_url = video_url.replace('%3D', '&')+'status'
            headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                       'Referer': item.url}
            data = httptools.downloadpage(video_url, headers=headers, ignore_response_code=True).data
            b64_url = scrapertools.find_single_match(data, "var string = '([^']+)';")+'=='
            url = base64.b64decode(b64_url)

            title = '%s '+ '[%s]' % language
            if url != '':
                itemlist.append(Item(channel=item.channel, title=title, url=url, action='play', language=language,
                                     infoLabels=item.infoLabels))
    except:
        pass

    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    return sorted(itemlist, key=lambda it: it.language)



