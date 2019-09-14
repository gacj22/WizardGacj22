# -*- coding: utf-8 -*-
# -*- Channel Zona World -*-
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

host = 'https://peliculas.zona-world.com/'

IDIOMAS = {'Latino': 'LAT', 'Español': 'CAST', 'Subtitulado': 'VOSE', 'Ingles': 'VO'}
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['rapidvideo', 'vidoza', 'openload', 'gvideo', 'fex', 'okru']


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title="Todas", action="list_all", url=host + 'pelicula/',
                         thumbnail=get_thumb('all', auto=True)))

    # itemlist.append(Item(channel=item.channel, title="Generos", action="section", section='genre',
    #                      thumbnail=get_thumb('genres', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=host + '?s=',
                         thumbnail=get_thumb('search', auto=True)))

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

    #try:
    data = get_source(item.url)

    patron = '<article id="post-.*?<a href="([^"]+)">.*?"Langu">([^ ]+) .*?<.*?src="([^"]+)".*?'
    patron += '<h3 class="Title">([^<]+)<\/h3>.*?date_range">(\d{4})<'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, language, scrapedthumbnail, scrapedtitle, year in matches:

        url = scrapedurl
        if "|" in scrapedtitle:
            scrapedtitle = scrapedtitle.split("|")
            contentTitle = scrapedtitle[0].strip()
        else:
            contentTitle = scrapedtitle

        contentTitle = re.sub('\(.*?\)', '', contentTitle)

        title = '%s [%s]' % (contentTitle, year)
        thumbnail = 'http:' + scrapedthumbnail
        itemlist.append(Item(channel=item.channel, action='findvideos',
                             title=title,
                             url=url,
                             thumbnail=thumbnail,
                             contentTitle=contentTitle,
                             language=IDIOMAS[language],
                             infoLabels={'year': year}
                             ))
    tmdb.set_infoLabels_itemlist(itemlist, True)

    #  Paginación

    url_next_page = scrapertools.find_single_match(data, '<a class="next page-numbers" href="([^"]+)">')
    if url_next_page:
        itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=url_next_page, action='list_all',
                             section=item.section))
    #except:
    #    pass
    return itemlist

def search_results(item):
    logger.info()
    itemlist = []

    try:
        patron = '<article id="post-.*?<a href="([^"]+)">.*?src="([^"]+)".*?"Langu">([^ ]+) .*?<.*?'
        patron += '<h3 class="Title">([^<]+)<\/h3>.*?date_range">(\d{4})<'
        data = get_source(item.url)
        matches = re.compile(patron, re.DOTALL).findall(data)

        for scrapedurl, scrapedthumbnail, language, scrapedtitle, year in matches:

            url = scrapedurl
            if "|" in scrapedtitle:
                scrapedtitle = scrapedtitle.split("|")
                contentTitle = scrapedtitle[0].strip()
            else:
                contentTitle = scrapedtitle

            contentTitle = re.sub('\(.*?\)', '', contentTitle)

            title = '%s [%s]' % (contentTitle, year)
            thumbnail = 'http:' + scrapedthumbnail
            itemlist.append(Item(channel=item.channel, action='findvideos',
                                 title=title,
                                 url=url,
                                 thumbnail=thumbnail,
                                 contentTitle=contentTitle,
                                 language=IDIOMAS[language],
                                 infoLabels={'year': year}
                                 ))
        tmdb.set_infoLabels_itemlist(itemlist, True)
    except:
        pass
    return itemlist


def section(item):
    logger.info()
    itemlist = []

    data = get_source(host)
    action = 'list_all'

    if item.section == 'genre':
        data = scrapertools.find_single_match(data, '>Género</div>(.*?)</ul>')

    patron = '<a href="([^"]+)".*?>([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for data_one, data_two in matches:

        url = data_one
        title = data_two
        if title != 'Ver más':
            new_item = Item(channel=item.channel, title=title, url=url, action=action, section=item.section)
            itemlist.append(new_item)

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = get_source(item.url)
    data = scrapertools.unescape(data)
    data = scrapertools.decodeHtmlentities(data)
    patron = 'id="(Opt\d+)">.*?src="([^"]+)" frameborder.*?</iframe>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for option, scrapedurl in matches:
        scrapedurl = scrapedurl.replace('"', '').replace('&#038;', '&')
        data_video = get_source(scrapedurl)
        opt_data = scrapertools.find_single_match(data, '"%s"><span>.*?</span>.*?<span>([^<]+)</span>' %
                                                  option).split('-')
        language = scrapertools.find_single_match(opt_data[0].strip(), '([^ ]+) ')
        quality = opt_data[1].strip()
        quality = re.sub('Full|HD', '', quality).strip()
        if 'rip' in quality.lower():
            quality = '720P'
        if not config.get_setting('unify'):
            title = ' [%s] [%s]' % (quality, IDIOMAS[language])
        else:
            title = ''
        try:
            url, tid = scrapertools.find_single_match(data_video, '<div class="Video">.*?src="(.*?tid=)([^&]+)&"')
            referer = url + tid
            tid = tid[::-1]
            url = url.replace('&tid=', '&trhex=')
            new_data = httptools.downloadpage(url + tid, follow_redirects=False)
            if 'location' in new_data.headers:
                new_url = new_data.headers['location']
                if 'rapidvideo' in new_url:
                    id = scrapertools.find_single_match(new_url, 'id=([^&]+)&')
                    url = 'https://wwww.rapidvideo.com/e/%s' % id

                elif 'fex' in new_url:
                    new_data = get_source(new_url)
                    id = scrapertools.find_single_match(new_data, "id=([^']+)'")
                    url = 'https://fex.net/load/%s' % id
                else:
                    new_data = get_source(new_url)
                    url = scrapertools.find_single_match(new_data, 'iframe src="([^"]+)"')
        except:

            url = scrapertools.find_single_match(data_video, 'src="([^"]+)" frameborder')

            if 'rapidvideo' in url:
                id = scrapertools.find_single_match(url, 'id=([^&]+)&')
                url = 'https://wwww.rapidvideo.com/e/%s' % id

        if 'youtube' in url:
            trailer = Item(channel=item.channel, title='Trailer', url=url, action='play', server='youtube')
        elif url != '':
            itemlist.append(Item(channel=item.channel, title='%s' + title, action='play', url=url,
                                 language=IDIOMAS[language], quality=quality, infoLabels=item.infoLabels))


    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % '%s' % i.server.capitalize())
    try:
        itemlist.append(trailer)
    except:
        pass
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
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    if texto != '':
        return search_results(item)
    else:
        return []


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria == 'infantiles':
            item.url = host + '/generos/animacion'
        elif categoria == 'terror':
            item.url = host + '/generos/terror'
        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
