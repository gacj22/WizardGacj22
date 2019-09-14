# -*- coding: utf-8 -*-
# -*- Channel SonPelisHD -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re

from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb

host = 'https://sonpelishd.net/'


def mainlist(item):
    logger.info()

    itemlist = []

    itemlist.append(item.clone(title="Todas",
                               action="list_all",
                               thumbnail=get_thumb('all', auto=True),
                               url=host + 'page/1/?s'
                               ))

    itemlist.append(item.clone(title="Generos",
                               action="seccion",
                               url=host + 'page/1/?s',
                               thumbnail=get_thumb('genres', auto=True),
                               seccion='generos-pelicula'
                               ))

    itemlist.append(item.clone(title="Por Año",
                               action="seccion",
                               url=host + 'page/1/?s',
                               thumbnail=get_thumb('year', auto=True),
                               seccion='fecha-estreno'
                               ))

    itemlist.append(item.clone(title="Calidad",
                               action="seccion",
                               url=host + 'page/1/?s',
                               thumbnail=get_thumb('quality', auto=True),
                               seccion='calidad'
                               ))

    itemlist.append(item.clone(title="Buscar", action="search",
                               thumbnail=get_thumb('search', auto=True),
                               url=host + '?s='
                               ))

    return itemlist



def list_all(item):
    logger.info()

    itemlist = []
    data = get_source(item.url)
    patron = 'class=item.*?<a href=(.*?)><div class=image.*?src=(.*?) alt=(.*?) (?:\(\d{4}|width).*?'
    patron += 'fixyear><h2>(.*?)<\/h2>.*?calidad2>(.*?)</span>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedyear, scrapedquality in matches:
        url = scrapedurl
        action = 'findvideos'
        thumbnail = scrapedthumbnail
        plot = ''
        contentSerieName = ''
        contentTitle = scrapedtitle
        title = contentTitle
        quality = scrapedquality
        if scrapedquality != '':
            title = contentTitle + ' (%s)' % quality

        year = scrapedyear

        if 'series' in item.url or 'series' in url:
            action = 'seasons'
            contentSerieName = contentTitle
            quality = ''
        new_item = Item(channel=item.channel,
                             action=action,
                             title=title,
                             url=url,
                             thumbnail=thumbnail,
                             plot=plot,
                             quality=quality,
                             infoLabels={'year': year}
                             )
        if 'series' not in item.url:
            new_item.contentTitle = contentTitle
        else:
            new_item.contentSerieName = contentSerieName
        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    # Paginacion

    if itemlist != []:
        next_page = scrapertools.find_single_match(data,
                                                   '<div class=pag_b><a href=(.*?)>Siguiente</a>')
        if next_page != '':
            itemlist.append(Item(channel=item.channel,
                                 action="list_all",
                                 title='Siguiente >>>',
                                 url=next_page,
                                 ))
    return itemlist


def seccion(item):
    logger.info()
    itemlist = []
    data = get_source(item.url)
    if item.seccion == 'generos-pelicula':
        patron = '<li class=cat-item cat-item-.*?><a href=(.*?)>(.*?<\/a> <span>.*?)<\/span><\/li>'
    elif item.seccion == 'generos-serie':
        patron = '<li class=cat-item cat-item-.*?><a href=(.*?\/series-genero\/.*?)>(.*?<\/a> <span>.*?)<\/span><\/li>'
    elif item.seccion in ['fecha-estreno', 'series-lanzamiento']:
        patron = '<li><a href=%sfecha-estreno(.*?)>(.*?)<\/a>' % host
    elif item.seccion == 'calidad':
        patron = '<li><a href=%scalidad(.*?)>(.*?)<\/a>' % host
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle in matches:
        thumbnail = ''
        if 'generos' in item.seccion:
            cantidad = re.sub(r'.*?<\/a> <span>', '', scrapedtitle)
            title = re.sub(r'<\/a> <span>|\d|\.', '', scrapedtitle)
            url = scrapedurl
            title = scrapertools.decodeHtmlentities(title)
            title = title + ' (%s)' % cantidad
        elif item.seccion in ['series-lanzamiento', 'fecha-estreno', 'calidad']:
            title = scrapedtitle
            url = '%s%s%s' % (host, item.seccion, scrapedurl)

        itemlist.append(item.clone(action='list_all',
                                   title=title,
                                   url=url,
                                   thumbnail=thumbnail
                                   ))
    return itemlist


def findvideos(item):
    logger.info()
    url_list = []
    itemlist = []
    duplicados = []
    data = get_source(item.url)
    src = data
    patron = '<iframe.*?src=(.*?) scrolling'
    matches = re.compile(patron, re.DOTALL).findall(data)
    trailer = ""
    for url in matches:
            lang = 'LAT'
            quality = item.quality
            if "youtube" in url and not trailer:
                trailer += url
            elif not '//' in url:#url.startswith('http'):
                continue
            title = '[%s] [%s]'

            if url != '' and not "youtube" in url:
                itemlist.append(item.clone(title=title, url=url, action='play', language=lang))
    
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % (i.server, i.language))
    if trailer:
        title = '[COLOR green]Trailer de %s[/COLOR]' % item.contentTitle
        itemlist.append(item.clone(title=title, url=trailer, action='play', language='LAT', server='youtube'))

    if item.infoLabels['mediatype'] == 'movie':
        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
            itemlist.append(Item(channel=item.channel,
                                 title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                                 url=item.url,
                                 action="add_pelicula_to_library",
                                 extra="findvideos",
                                 contentTitle=item.contentTitle
                                 ))

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


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria in ['peliculas', 'latino']:
            item.url = host + 'page/1/?s'

        elif categoria == 'infantiles':
            item.url = host + 'category/animacion/'

        elif categoria == 'terror':
            item.url = host + 'category/terror/'

        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data
