# -*- coding: utf-8 -*-
# -*- Channel Pelisplus -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
import urllib
from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb
from lib import generictools

IDIOMAS = {'latino': 'Latino'}
list_language = IDIOMAS.values()

list_quality = ['360p', '480p', '720p', '1080']

list_servers = [
    'directo',
    'openload',
    'rapidvideo',
    'streamango',
    'vidlox',
    'vidoza'
    ]

host = 'https://www.pelisplus.to/'

def get_source(url, referer=None):
    logger.info()
    if referer == None:
        data = httptools.downloadpage(url).data
    else:
        data = httptools.downloadpage(url, headers={'Referer':referer}).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data

def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = []

    itemlist.append(Item(channel=item.channel,
                         title="Peliculas",
                         action="sub_menu",
                         thumbnail=get_thumb('movies', auto=True),
                         ))

    itemlist.append(Item(channel=item.channel,
                         title="Series",
                         action="sub_menu",
                         thumbnail=get_thumb('tvshows', auto=True),
                         ))

    itemlist.append(Item(channel=item.channel,
                         title="Buscar", action="search", url=host + 'search/?s=',
                         thumbnail=get_thumb('search', auto=True),
                         ))

    autoplay.show_option(item.channel, itemlist)

    return itemlist

def sub_menu(item):
    logger.info()
    itemlist = []

    content = item.title.lower()

    itemlist.append(Item(channel=item.channel,
                         title="Ultimas",
                         action="list_all",
                         url=host + '%s/estrenos' % content,
                         thumbnail=get_thumb('last', auto=True),
                         type=content
                         ))

    itemlist.append(Item(channel=item.channel,title="Todas",
                         action="list_all",
                         url=host + '%s' % content,
                         thumbnail=get_thumb('all', auto=True),
                         type=content
                         ))

    itemlist.append(Item(channel=item.channel,
                         title="Generos",
                         action="section",
                         thumbnail=get_thumb('genres', auto=True),
                         type=content
                         ))
    return itemlist

def list_all(item):
    logger.info()
    itemlist = []

    full_data = get_source(item.url)
    data = scrapertools.find_single_match(full_data, '<div class="Posters">(.*?)</(?:ul|a></div>)')
    patron = 'href="([^"]+)".*?src="([^"]+)".*?<p>([^<]+)</p>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:

        year = scrapertools.find_single_match(scrapedtitle, '(\d{4})')
        title = scrapertools.find_single_match(scrapedtitle, '([^\(]+)\(?').strip()
        thumbnail = scrapedthumbnail
        filter_thumb = thumbnail.replace("https://image.tmdb.org/t/p/w300", "")
        filter_list = {"poster_path": filter_thumb}
        filter_list = filter_list.items()
        url = scrapedurl

        new_item = Item(channel=item.channel,
                        title=title,
                        url=url,
                        thumbnail=thumbnail,
                        infoLabels={'filtro':filter_list, 'year':year})

        if item.type == 'peliculas' or 'serie' not in url:
            new_item.action = 'findvideos'
            new_item.contentTitle = title
        else:
            new_item.action = 'seasons'
            new_item.contentSerieName = title

        itemlist.append(new_item)

    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    #  Paginación

    next_page_pattern = '<a class="page-link" href="([^"]+)" data-ci-pagination-page="\d+" rel="next">&gt;</a>'
    url_next_page = scrapertools.find_single_match(full_data, next_page_pattern)
    if url_next_page:
        itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=url_next_page, action='list_all'))

    return itemlist

def seasons(item):
    logger.info()

    itemlist=[]

    data=get_source(item.url)
    patron='data-toggle="tab">TEMPORADA\s?(\d+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    infoLabels = item.infoLabels
    for season in matches:
        infoLabels['season']=season
        title = 'Temporada %s' % season
        itemlist.append(Item(channel=item.channel, title=title, url=item.url, action='episodesxseasons',
                             infoLabels=infoLabels))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'episodios':
        itemlist.append(
                Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]', url=item.url,
                     action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName))

    return itemlist

def episodios(item):
    logger.info()
    itemlist = []
    templist = seasons(item)
    for tempitem in templist:
        itemlist += episodesxseasons(tempitem)

    return itemlist

def episodesxseasons(item):
    logger.info()

    itemlist = []

    season = item.infoLabels['season']
    data=get_source(item.url)
    season_data = scrapertools.find_single_match(data, 'id="pills-vertical-%s">(.*?)</div>' % season)
    patron='href="([^"]+)".*?block">Capitulo.?(\d+) -.?([^<]+)<'
    matches = re.compile(patron, re.DOTALL).findall(season_data)

    infoLabels = item.infoLabels

    for scrapedurl, scrapedepisode, scrapedtitle in matches:

        infoLabels['episode'] = scrapedepisode
        url = scrapedurl
        title = '%sx%s - %s' % (infoLabels['season'], infoLabels['episode'], scrapedtitle)

        itemlist.append(Item(channel=item.channel, title= title, url=url, action='findvideos', infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist


def section(item):
    logger.info()
    itemlist=[]
    data = get_source(host)
    genres_data = scrapertools.find_single_match(data, '>Generos<(.*?)</ul>')
    patron = 'href="\/\w+\/([^"]+)">([^<]+)<'
    matches = re.compile(patron, re.DOTALL).findall(genres_data)

    for scrapedurl, scrapedtitle in matches:
        title = scrapedtitle
        url = '%s/%s/%s' % (host, item.type, scrapedurl)
        itemlist.append(Item(channel=item.channel, url=url, title=title, action='list_all', type=item.type))
    return itemlist


def add_vip(item, video_url, language=None):
    logger.info()
    itemlist = []
    referer = video_url
    post = {'r': item.url, 'd': 'www.pelisplus.net'}
    post = urllib.urlencode(post)
    video_url = video_url.replace('/v/', '/api/source/')
    url_data = httptools.downloadpage(video_url, post=post, headers={'Referer': referer}).data
    patron = '"file":"([^"]+)","label":"([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(url_data)
    if not config.get_setting('unify'):
        title = ' [%s]' % language
    else:
        title = ''

    for url, quality in matches:
        url = url.replace('\/', '/')
        itemlist.append(
            Item(channel=item.channel, title='%s'+title + " " + quality, url=url, action='play', language=language,
                 quality=quality, infoLabels=item.infoLabels))
    return itemlist

def findvideos(item):
    logger.info()
    import urllib
    itemlist = []

    data = get_source(item.url)
    patron = 'video\[\d+\] = "([^"]+)";'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for video_url in matches:
        language = 'latino'
        url = ''
        if not config.get_setting('unify'):
            title = ' [%s]' % IDIOMAS[language]
        else:
            title = ''

        if 'pelisplus.net' in video_url:
            itemlist += add_vip(item, video_url, IDIOMAS[language])


        # elif not 'vidoza' in video_url and not 'pelishd' in video_url:
        #     url_data = get_source(video_url)
        #     url = scrapertools.find_single_match(url_data, '<iframe src="([^"]+)"')
        #
        else:
            url = video_url

        if not 'server' in url:
            url = url

            if 'pelishd' in url:
                vip_data = httptools.downloadpage(url, headers={'Referer':item.url}, follow_redirects=False)
                try:
                    dejuiced = generictools.dejuice(vip_data.data)
                    urls = scrapertools.find_multiple_matches(dejuiced, '"file":"([^"]+)","label":"([^"]+)"')
                    for new_url, quality in urls:
                        new_url = new_url.replace('unicorn', 'dragon')
                        new_url = new_url + '|referer:%s' % url
                        itemlist.append(
                            Item(channel=item.channel, title='%s' + title + " " + quality, url=new_url, action='play',
                                 language=IDIOMAS[language], quality=quality, infoLabels=item.infoLabels))
                except:
                    pass

        if url != '' and 'rekovers' not in url and not 'pelishd' in url:
            itemlist.append(Item(channel=item.channel, title='%s'+title, url=url, action='play', language=IDIOMAS[language],
            infoLabels=item.infoLabels))


    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if item.contentType == 'movie':
        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
            itemlist.append(Item(channel=item.channel,
                                 title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                                 url=item.url,
                                 action="add_pelicula_to_library",
                                 extra="findvideos",
                                 contentTitle=item.contentTitle))
    return itemlist

def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url += texto

    try:
        if texto != '':
            return list_all(item)
        else:
            return []
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria in ['peliculas', 'latino']:
            item.url = host + 'peliculas/estrenos'
        elif categoria == 'infantiles':
            item.url = host + 'peliculas/generos/animacion/'
        elif categoria == 'terror':
            item.url = host + 'peliculas/generos/terror/'
        item.type='peliculas'
        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist