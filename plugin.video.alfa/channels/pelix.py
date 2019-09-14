# -*- coding: utf-8 -*-
# -*- Channel Pelix -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
import urllib
import base64

from channelselector import get_thumb
from core import httptools
from core import jsontools
from core import scrapertools
from core import servertools
from core import tmdb
from lib import jsunpack
from core.item import Item
from channels import filtertools
from channels import autoplay
from platformcode import config, logger


IDIOMAS = {'6': 'Latino', '7': 'Castellano'}
list_language = IDIOMAS.values()
CALIDADES = {'1': '1080p', '3': '720p', '4':'720p'}
list_quality = CALIDADES.values()

list_servers = [
    'openload',
    'streamango',
    'fastplay',
    'rapidvideo',
    'netutv'
]

__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', 'pelix')
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', 'pelix')

host = 'https://pelix.tv/'

def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = []

    itemlist.append(Item(channel=item.channel, title='Peliculas', action='menu_movies',
                         thumbnail= get_thumb('movies', auto=True), page=0))
    itemlist.append(Item(channel=item.channel, title='Series', url=host+'home/genero/5', action='list_all',
                         type='tvshows', thumbnail= get_thumb('tvshows', auto=True), page=0))
    itemlist.append(
        item.clone(title="Buscar", action="search", url=host + 'movies/headserach', thumbnail=get_thumb("search", auto=True),
                   extra='movie'))

    autoplay.show_option(item.channel, itemlist)

    return itemlist

def menu_movies(item):
    logger.info()

    itemlist=[]

    itemlist.append(Item(channel=item.channel, title='Ultimas', url=host, path='home/newest?show=', action='list_all',
                         thumbnail=get_thumb('last', auto=True), type='movies', page=0))

    #itemlist.append(Item(channel=item.channel, title='Mas Vistas', url=host, path='home/views?show=', action='list_all',
    #                     thumbnail=get_thumb('all', auto=True), type='movies', page=0))

    itemlist.append(Item(channel=item.channel, title='Genero', action='section',
                         thumbnail=get_thumb('genres', auto=True), type='movies'))
    itemlist.append(Item(channel=item.channel, title='Por Año', action='section',
                         thumbnail=get_thumb('year', auto=True), type='movies'))

    return itemlist

def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data


def get_language(lang_data):
    logger.info()
    language = []
    lang_list = scrapertools.find_multiple_matches(lang_data, '/flags/(.*?).png\)')
    for lang in lang_list:
        if lang == 'en':
            lang = 'vose'
        if lang not in language:
            language.append(lang)
    return language

def section(item):
    logger.info()
    itemlist=[]
    data = get_source(host)
    if 'Genero' in item.title:
        data = scrapertools.find_single_match(data, '<a href="#">Género</a>(.*?)</ul>')
    elif 'Año' in item.title:
        data = scrapertools.find_single_match(data, '<a href="#">Año</a>(.*?)</ul>')

    patron = '<a href="([^"]+)">([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        itemlist.append(Item(channel=item.channel, url=scrapedurl, title=scrapedtitle, action='list_all',
                             type=item.type, page=0))

    return itemlist


def list_all(item):
    logger.info()
    import urllib
    itemlist = []
    if item.page == 0:
        data = get_source(item.url+item.path)
    else:
        prevurl = item.url
        if item.path: prevurl = item.url+item.path
        url_ajax = re.sub('/home/([a-z]+)', r'/home/\1Ajax', prevurl)
        url_ajax = url_ajax + '/%s' % str(item.page)
        post = {'page': str(item.page)}
        post = urllib.urlencode(post)
        data = httptools.downloadpage(url_ajax + '/%s' % str(item.page), post=post).data
        data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)

    patron = '<div class="base-used">.*?<a href="([^"]+)">.*?<img class="img-thumbnail" src="([^"]+)".*?'
    patron += '<h2>([^<]+)</h2><p class="year">(\d{4})</p>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle, year in matches:

        title = '%s [%s]' % (scrapedtitle, year)
        contentTitle = scrapedtitle
        thumbnail = scrapedthumbnail
        url = scrapedurl
        if url.startswith('/'):
            url = host + url[1:]
        new_item= Item(channel=item.channel,
                       title=title,
                       url=url,
                       thumbnail=thumbnail,
                       infoLabels={'year':year})

        if item.type == 'movies':
            new_item.action = 'findvideos'
            new_item.contentTitle = contentTitle
        else:
            new_item.action = 'seasons'
            new_item.contentSerieName = contentTitle

        itemlist.append(new_item)

    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    #  Paginación

    next_page = item.page + 30
    itemlist.append(item.clone(title="Siguiente >>", url=item.url, action='list_all', page=next_page, path=item.path))

    return itemlist

def seasons(item):
    logger.info()

    itemlist=[]

    data=get_source(item.url)
    patron='data-type="host">(Temporada \d+)<'
    matches = re.compile(patron, re.DOTALL).findall(data)
    if matches is None:
        return findvideos(item)
    infoLabels = item.infoLabels
    for season in matches:
        season = season.lower().replace('temporada','')
        infoLabels['season']=season
        title = 'Temporada %s' % season
        itemlist.append(Item(channel=item.channel, title=title, url=item.url, action='episodesxseasons',
                             infoLabels=infoLabels))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    if config.get_videolibrary_support() and len(itemlist) > 0:
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
    duplicados = []
    data=get_source(item.url)
    patron='data-id="(\d+)" season="%s" id_lang="(\d+)" id_movies_types="\d".*?' \
           'block;">([^<]+)</a>' % item.infoLabels['season']
    matches = re.compile(patron, re.DOTALL).findall(data)

    infoLabels = item.infoLabels

    for scrapedepisode, lang, scrapedtitle in matches:

        infoLabels['episode'] = scrapedepisode
        url = item.url
        title = '%sx%s - %s' % (infoLabels['season'], infoLabels['episode'], scrapedtitle)

        if scrapedepisode not in duplicados:
            itemlist.append(Item(channel=item.channel, title= title, url=url, action='findvideos', infoLabels=infoLabels))
            duplicados.append(scrapedepisode)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = []

    data = get_source(item.url)
    '''if 'episode="0" season="0"' not in data and item.contentType != 'episode':
        item.contentSerieName = item.contentTitle
        item.contentTitle = None
        item.contentType = None
        item.infoLabels = None
        tmdb.set_infoLabels_item(item, seekTmdb=True)
        return seasons(item)

    if 'episode="0" season="0"' not in data:
        season = item.infoLabels['season']
        episode = item.infoLabels['episode']
    else:
        season = '0'
        episode = '0'
    '''
    #patron = '<span class="movie-online-list" id_movies_types="(\d)".*?'
    #patron += 'episode="%s" season="%s" id_lang="([^"]+)".*?online-link="([^"]+)" link-id="\d+">' % (episode, season)
    bloq = scrapertools.find_single_match(data, 'Contraseña</th>(.*?)</table>')
   
    patron = '<a href="([^"]+)".*?<td>(.*?)</td><td class="hidden-xs">(.*?)</td>'
    matches = re.compile(patron, re.DOTALL).findall(bloq)
    #for quality_value, lang_value, scrapedurl in matches:
    for scrapedurl, lang_value, quality_value in matches:
        server = ""
        if lang_value not in IDIOMAS:
            lang_value = '6'
        if quality_value not in CALIDADES:
            quality_value = '3'
        language = IDIOMAS[lang_value]

        quality = CALIDADES[quality_value]
        if not config.get_setting("unify"):
            title = ' [%s] [%s]' % (quality, language)
        else:
            title = ''
        if scrapedurl.startswith("magnet:"):
            server = "torrent"
        itemlist.append(Item(channel=item.channel, url=scrapedurl, title='%s'+title, action='play',
                             language=language, quality=quality, infoLabels=item.infoLabels, server=server))
    embed = scrapertools.find_single_match(data, 'movie-online-iframe" src="([^"]+)"')
    if embed:
        fquality = itemlist[1].quality
        flanguage = itemlist[1].language
        title = ' [%s] [%s]' % (quality, language)
        itemlist.append(item.clone(title="%s"+title, url=embed, language=flanguage, quality=fquality, infoLabels=item.infoLabels, action="play"))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())

    # Requerido para Filtrar enlaces

    if __comprueba_enlaces__:
        itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    itemlist = sorted(itemlist, key=lambda it: it.language)

    if item.contentType != 'episode':
        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
            itemlist.append(
                Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]', url=item.url,
                     action="add_pelicula_to_library", extra="findvideos", contentTitle=item.contentTitle))

    return itemlist

def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    post = 'search=%s' % texto
    item.post = post
    item.url = item.url

    if texto != '':
        return search_results(item)
    else:
        return []

def search_results(item):
    logger.info()

    itemlist=[]

    headers = {'Referer': host, 'X-Requested-With': 'XMLHttpRequest'}
    data = httptools.downloadpage(item.url, headers=headers, post=item.post).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    patron = 'class="results\d+".*?<a href="([^"]+)"><img src="([^"]+)".*?#\w+">([^<]+)<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumb, scrapedtitle in matches:

        if '(' in scrapedtitle:
            title = scrapertools.find_single_match(scrapedtitle, '(.*?)\(').strip()
            year = scrapertools.find_single_match(scrapedtitle, '\((\d+)\)')
        else:
            title = scrapedtitle
            year = '-'
        url = scrapedurl
        thumbnail = scrapedthumb

        new_item=Item(channel=item.channel, title=title, url=url, thumbnail=thumbnail,
                             action='findvideos', infoLabels={'year':year})

        itemlist.append(new_item)

    return itemlist

def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        item.type = 'movies'
        item.page = 0
        if categoria in ['peliculas']:
            item.url = host + 'home/newest?show='
        elif categoria == 'infantiles':
            item.url = host + 'home/genero/54'
        elif categoria == 'terror':
            item.url = host + 'home/genero/49'
        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
