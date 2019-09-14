# -*- coding: utf-8 -*-
# -*- Channel ReyAnime -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
import urllib

from core import httptools
from core import scrapertools
from core import servertools
from channelselector import get_thumb
from core import tmdb
from core.item import Item
from platformcode import logger, config
from channels import autoplay
from channels import filtertools


host = "https://reyanimeonline.com/"

__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', 'reyanime')
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', 'reyanime')

IDIOMAS = {'latino':'LAT', 'VOSE': 'VOSE'}
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['directo', 'openload', 'streamango', 'mp4upload', 'gvideo']


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = []


    itemlist.append(Item(channel=item.channel, title="Anime",
                              action="sub_menu",
                              thumbnail=''
                              ))

    itemlist.append(Item(channel=item.channel, title="Películas",
                         action="list_all",
                         thumbnail=get_thumb('movies', auto=True),
                         url=host + 'inc/a.pelicula.php', page='1'))

    itemlist.append(Item(channel=item.channel, title="Géneros",
                         action="section",
                         thumbnail=get_thumb('genres', auto=True),
                         url=host + 'estrenos/'))

    itemlist.append(Item(channel=item.channel, title="Alfabetico",
                         action="section",
                         thumbnail=get_thumb('alphabet', auto=True),
                         url=host + 'estrenos/'))

    itemlist.append(Item(channel=item.channel, title="Buscar",
                               action="search",
                               url=host + 'resultado/?buscar=',
                               thumbnail=get_thumb('search', auto=True),
                               fanart='https://s30.postimg.cc/pei7txpa9/buscar.png'
                               ))

    autoplay.show_option(item.channel, itemlist)

    return itemlist

def sub_menu(item):

    itemlist = []

    itemlist.append(Item(channel=item.channel, title="Nuevos Capitulos",
                         action="new_episodes",
                         thumbnail=get_thumb('new episodes', auto=True),
                         url=host))

    itemlist.append(Item(channel=item.channel, title="Recientes",
                         action="list_all",
                         thumbnail=get_thumb('recents', auto=True),
                         url=host + 'inc/a.emision.php', page='1'))

    itemlist.append(Item(channel=item.channel, title="Todas",
                         action="list_all",
                         thumbnail=get_thumb('all', auto=True),
                         url=host + 'inc/a.animes.php', page='1'))

    itemlist.append(Item(channel=item.channel, title="Mas Vistos",
                         action="list_all",
                         thumbnail=get_thumb('more watched', auto=True),
                         url=host + 'mas-vistos/'))

    itemlist.append(Item(channel=item.channel, title="Recomendados",
                         action="list_all",
                         thumbnail=get_thumb('recomended', auto=True),
                         url=host + 'recomendado/'))

    return itemlist

def get_source(url, referer=None):
    logger.info()
    if referer is None:
        data = httptools.downloadpage(url).data
    else:
        data = httptools.downloadpage(url, headers={'Referer':referer}).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data

def section(item):
    logger.info()

    itemlist = []
    listed = []
    param = ''
    full_data = get_source(item.url)

    if item.title == 'Géneros':
        data = scrapertools.find_single_match(full_data, 'id="generos"(.*?)"letras')
    elif item.title == 'Alfabetico':
        data = scrapertools.find_single_match(full_data,'class="letras(.*?)<h2')

    patron = 'href="([^"]+)">(?:<i class="fa fa-circle-o"></i>|)([^<]+)<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        param = scrapedtitle.strip()
        title = param.capitalize()
        if item.title == 'Géneros':

            url = 'inc/a.genero.php'
        elif item.title == 'Alfabetico':
            url = 'inc/a.letra.php'

        if scrapedurl not in listed:
            itemlist.append(Item(channel=item.channel, title=title, url=host+url, action='list_all', param=param,
                                 page='1'))
            listed.append(scrapedurl)

    return sorted(itemlist, key=lambda i: i.title)

def list_all(item):
    logger.info()

    itemlist = []

    if item.param == '':

        data = httptools.downloadpage(item.url, post='page=%s' % item.page).data
    else:
        if len(item.param) > 1:
            var = 'genero'
        else:
            var = 'letra'
        data = httptools.downloadpage(item.url, post='%s=%s&page=%s' % (var, item.param, item.page)).data

    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    patron = '<div class="col-md-4"><a href="([^"]+)" class="front"><img src="([^"]+)" alt="([^"]+)".*?'
    patron += '<div class="categoria">([^"]+).*?"sinopsis">.*?<p>([^<]+)</p>'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle, type, scrapedplot in matches:
        url = scrapedurl
        thumbnail = scrapedthumbnail
        new_item= Item(channel=item.channel,
                       action='episodios',
                       title=scrapedtitle,
                       url=url,
                       thumbnail=thumbnail,
                       plot = scrapedplot,
                       )

        if 'pelicula' in url:
            new_item.contentTitle=scrapedtitle
            new_item.infoLabels['year':'-']
        else:
            new_item.contentSerieName = scrapedtitle
        if 'reyanime' not in scrapedtitle:
            itemlist.append(new_item)
        # Paginacion
    if len(itemlist) > 0 and item.page != '':
        next_page_value = int(item.page)+1
        next_page = str(next_page_value)
        itemlist.append(item.clone(title=">> Página siguiente",
                             page=next_page,
                             thumbnail='https://s16.postimg.cc/9okdu7hhx/siguiente.png'
                             ))
    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
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

def new_episodes(item):
    logger.info()

    itemlist = []

    data = get_source(item.url)
    patron = 'class="overarchingdiv"> <a href="([^"]+)".*?src="([^"]+)".*?"overtitle">([^<]+)<.*?"overepisode">([^<]+)<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle, episode in matches:
        title = '%s - Episodio %s' % (scrapedtitle, episode)
        itemlist.append(Item(channel=item.channel, title=title, url=scrapedurl, thumbnail=scrapedthumbnail,
                             action='findvideos'))

    return itemlist

def episodios(item):
    logger.info()
    itemlist = []

    full_data = get_source(item.url)
    data = scrapertools.find_single_match(full_data, '>Lista de episodios:(.*?)</ul>')
    patron = '<li class="item_cap"> <a href="([^"]+)" class=".*?">.*?</i>.*?Episodio (\d+)([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    infoLabels = item.infoLabels
    for scrapedurl, episode, lang in matches:
        if 'latino' in scrapedurl:
            lang = 'LAT'
        elif 'sub' in lang.lower() or lang.strip() == '':
            lang='VOSE'


        title = "1x" + episode + " - Episodio %s" % episode
        url = scrapedurl
        infoLabels['season'] = '1'
        infoLabels['episode'] = episode
        itemlist.append(Item(channel=item.channel, title=title, contentSerieName=item.contentSerieName, url=url,
                             action='findvideos', language=lang, infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    itemlist = itemlist[::-1]
    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]', url=item.url,
                 action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName,
                 extra1='library'))

    if 'pelicula' in item.url and len(itemlist) > 0:
        return findvideos(itemlist[0])
    else:
        return itemlist


def findvideos(item):
    logger.info()

    itemlist = []

    data = get_source(item.url)
    patron = "tabsArray\['\d+'\] =.*?src='([^']+)'"
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl in matches:

        if 'reyanimeonline' in scrapedurl:
            new_data = get_source(scrapedurl)
            scrapedurl = scrapertools.find_single_match(new_data, '"file":"([^"]+)",')

        if scrapedurl != '':
            itemlist.append(Item(channel=item.channel, title='%s', url=scrapedurl, action='play', language = item.language,
                                       infoLabels=item.infoLabels))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())

    if __comprueba_enlaces__:
        itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    return itemlist

def newest(categoria):
    itemlist = []
    item = Item()
    if categoria == 'anime':
        item.url=host
        itemlist = new_episodes(item)
    return itemlist
