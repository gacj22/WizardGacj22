# -*- coding: utf-8 -*-
# -*- Channel MiraPelisOnline -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
import urllib
import urlparse

from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from core import tmdb
from channels import autoplay
from channels import filtertools

IDIOMAS = {'mx': 'LAT', 'es': 'CAST', 'en': 'VOSE'}
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['gvideo', 'openload', 'rapidvideo', 'directo']


host = "https://mirapelisonline.com/"


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(
        Item(channel=item.channel,
             title="Ultimas",
             action="list_all",
             url=host,
             thumbnail=get_thumb("last", auto=True)))

    itemlist.append(
        Item(channel=item.channel,
             title="Todas",
             action="list_all",
             url=host+'movies',
             thumbnail=get_thumb("all", auto=True)))

    itemlist.append(
        Item(channel=item.channel,
             title="Destacadas",
             action="list_all",
             url=host + 'peliculas-destacadas',
             thumbnail=get_thumb("hot", auto=True)))

    itemlist.append(
        Item(channel=item.channel,
             title="Generos",
             action="categories",
             url=host,
             thumbnail=get_thumb('genres', auto=True)

             ))

    itemlist.append(
        Item(channel=item.channel,
             title="Buscar",
             action="search",
             url=host,
             thumbnail=get_thumb("search", auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist

def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data


def categories(item):
    logger.info()
    itemlist = []

    data = get_source(item.url)
    patron = '<li class="cat-item cat-item-\d+"><a href="([^"]+)" >(.*?)<'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for url, title in matches:
        itemlist.append(Item(channel=item.channel,
                             action="list_all",
                             title=title,
                             url=url
                             ))

    return itemlist[::-1]


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    try:
        if texto != '':
            item.texto = texto
            return list_all(item)
        else:
            return []
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def list_all(item):
    logger.info()
    itemlist = []

    if item.texto != '':
        url = item.url + "?s=%s" % item.texto
    else:
        url = item.url

    try:
        data = get_source(url)
    except:
        return itemlist
    data = data.replace("'", '"')

    pattern = 'class="ml-item.*?"><a href="([^"]+)".*?title="([^"]+)".*?<img data-original="([^"]+)".*?<div id(.*?)/a>'
    matches = scrapertools.find_multiple_matches(data, pattern)

    for url, title, thumb, info in matches:
        year = scrapertools.find_single_match(info, '"jt-info">(\d{4})<')
        new_item = Item(channel=item.channel,
                        title=title,
                        url=url,
                        thumbnail=thumb,
                        infoLabels = {'year': year}
                        )
        if 'series' in url:
            new_item.action = 'seasons'
            new_item.contentSerieName = title
        else:
            new_item.action = 'findvideos'
            new_item.contentTitle = title

        itemlist.append(new_item)

    tmdb.set_infoLabels(itemlist, seekTmdb=True)



    next_page = scrapertools.find_single_match(data, 'rel="next" href="([^"]+)">')

    if next_page:

        url = urlparse.urljoin(host, next_page)
        itemlist.append(Item(channel=item.channel,
                             action="list_all",
                             title=">> Página siguiente",
                             url=url,
                             texto=item.texto,
                             thumbnail=get_thumb("next.png")))
    return itemlist


def findvideos(item):
    logger.info()

    itemlist = []
    data = get_source(item.url)
    selector_url = scrapertools.find_multiple_matches(data, 'id="reproductor\d+".*?src="([^"]+)"')

    for lang in selector_url:
        data = get_source('https:'+lang)
        urls = scrapertools.find_multiple_matches(data, 'data-playerid="([^"]+)">')
        subs = ''
        lang = scrapertools.find_single_match(lang, 'lang=(.*)?')
        language = IDIOMAS[lang]

        if item.contentType == 'episode':
            quality = 'SD'
        else:
            quality = item.quality

        for url in urls:
            final_url = httptools.downloadpage('https:'+url).data
            if language == 'VOSE':
                sub = scrapertools.find_single_match(url, 'sub=(.*?)&')
                subs = 'https:%s' % sub
            if 'index' in url:
                try:
                    file_id = scrapertools.find_single_match(url, 'file=(.*?)&')
                    post = {'link': file_id}
                    post = urllib.urlencode(post)
                    hidden_url = 'https://player.mirapelisonline.com/repro/plugins/gkpluginsphp.php'
                    dict_vip_url = httptools.downloadpage(hidden_url, post=post).json
                    url = dict_vip_url['link']
                except:
                    pass
            else:
                try:

                    if 'openload' in url:
                        file_id = scrapertools.find_single_match(url, 'h=(\w+)')
                        post = {'h': file_id}
                        post = urllib.urlencode(post)

                        hidden_url = 'https://player.mirapelisonline.com/repro/openload/api.php'
                        json_data = httptools.downloadpage(hidden_url, post=post, follow_redirects=False).json
                        url = scrapertools.find_single_match(data_url, "VALUES \('[^']+','([^']+)'")
                        if not url:
                            url = json_data['url']
                        if not url:
                            continue
                    else:
                        new_data = httptools.downloadpage('https:'+url).data
                        file_id = scrapertools.find_single_match(new_data, 'value="([^"]+)"')
                        post = {'url': file_id}
                        post = urllib.urlencode(post)
                        hidden_url = 'https://player.mirapelisonline.com/repro/r.php'
                        data_url = httptools.downloadpage(hidden_url, post=post, follow_redirects=False)
                        url = data_url.headers['location']
                except:
                    pass
            url = url.replace(" ", "%20")
            itemlist.append(item.clone(title = '[%s] [%s]', url=url, action='play', subtitle=subs,
                            language=language, quality=quality, infoLabels=item.infoLabels))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % (x.server.capitalize(), x.language))

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


def newest(category):
    logger.info()
    item = Item()
    try:
        if category == 'peliculas':
            item.url = host + "movies/"
        elif category == 'infantiles':
            item.url = host + 'genre/animacion'
        elif category == 'terror':
            item.url = host + 'genre/terror'
        itemlist = list_all(item)

        if itemlist[-1].title == '>> Página siguiente':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

    return itemlist
