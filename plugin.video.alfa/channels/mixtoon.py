# -*- coding: utf-8 -*-

import re

from channels import renumbertools
from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channels import filtertools
from channels import autoplay
from lib import gktools

IDIOMAS = {'castellano': 'Castellano'}
list_language = IDIOMAS.values()
list_servers = ['openload'
                ]
list_quality = ['default']


host = "https://mixtoon.com"


def mainlist(item):
    logger.info()
    thumb_series = get_thumb("channels_tvshow.png")
    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(
        Item(channel=item.channel, action="lista", title="Series", url=host, thumbnail=thumb_series, page=0))
    itemlist = renumbertools.show_option(item.channel, itemlist)
    autoplay.show_option(item.channel, itemlist)
    return itemlist


def lista(item):
    logger.info()

    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<a href="([^"]+)" '
    patron += 'class="link">.+?<img src="([^"]+)".*?'
    patron += 'title="([^"]+)">'
    matches = scrapertools.find_multiple_matches(data, patron)
    # Paginacion
    num_items_x_pagina = 30
    min = item.page * num_items_x_pagina
    min=min-item.page
    max = min + num_items_x_pagina - 1
    b=0
    for link, img, name in matches[min:max]:
        b=b+1
        if " y " in name:
            title=name.replace(" y "," & ")
        else:
            title = name
        url = host + link
        scrapedthumbnail = host + img
        context = renumbertools.context(item)
        context2 = autoplay.context
        context.extend(context2)
        itemlist.append(item.clone(title=title, url=url, action="episodios", thumbnail=scrapedthumbnail, show=title,contentSerieName=title,
                                   context=context))
    if b<29:
        pass
    else:    
        itemlist.append(
             Item(channel=item.channel, title="[COLOR cyan]Página Siguiente >>[/COLOR]", url=item.url, action="lista", page=item.page + 1))

    tmdb.set_infoLabels(itemlist)
    return itemlist


def episodios(item):
    logger.info()

    itemlist = []
    data = httptools.downloadpage(item.url).data
    # obtener el numero total de episodios
    total_episode = 0

    patron_caps = '<li><a href="(.*?)">(.*?)-(.*?)<\/a><\/li>'
    matches = scrapertools.find_multiple_matches(data, patron_caps)
    patron_info = '<img src="([^"]+)"><div class="ds"><p>(.*?)<\/p>'
    scrapedthumbnail, scrapedplot = scrapertools.find_single_match(data, patron_info)
    show = item.title
    scrapedthumbnail = host + scrapedthumbnail

    for link, cap, name in matches:

        title = ""
        pat = "/"
        if "Mike, Lu & Og"==item.title:
            pat="&/"
        if "KND" in item.title:
            pat="-"
        # varios episodios en un enlace
        if len(name.split(pat)) > 1:
            i = 0
            for pos in name.split(pat):
                i = i + 1
                total_episode += 1
                season, episode = renumbertools.numbered_for_tratk(item.channel, item.contentSerieName, 1, total_episode)
                if len(name.split(pat)) == i:
                    title += "%sx%s " % (season, str(episode).zfill(2))
                else:
                    title += "%sx%s_" % (season, str(episode).zfill(2))
        else:
            total_episode += 1
            season, episode = renumbertools.numbered_for_tratk(item.channel,item.contentSerieName, 1, total_episode)

            title += "%sx%s " % (season, str(episode).zfill(2))

        url = host + "/" + link
        if "disponible" in link:
            title += "No Disponible aún"
        else:
            title += name
            itemlist.append(
                Item(channel=item.channel, action="findvideos", title=title, url=url, show=show, plot=scrapedplot,
                     thumbnail=scrapedthumbnail))

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(Item(channel=item.channel, title="[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]", url=item.url,
                             action="add_serie_to_library", extra="episodios", show=show))

    return itemlist

def findvideos(item):
    import base64
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data

    _sl = scrapertools.find_single_match(data, 'var _dt=([^;]+);')
    sl = eval(_sl)
    buttons = [0,1]
    for id in buttons:
        new_url = "https://videoeb.xyz/" + "eb/" + sl[0] + "/" + sl[1] + "/" + str(id) + "/" + sl[2]
        data_new = httptools.downloadpage(new_url, headers={'Referer': item.url}).data
        try:
            valor1, valor2 = scrapertools.find_single_match(data_new,
                                                            'var x0x = \["[^"]*","([^"]+)","[^"]*","[^"]*","([^"]+)')
            url = base64.b64decode(gktools.transforma_gsv(valor2, base64.b64decode(valor1)))
            if 'download' in url:
                url = url.replace('download', 'preview')
            title = '%s'
            itemlist.append(Item(channel=item.channel, title=title, url=url, action='play', language='latino',
                         infoLabels=item.infoLabels))
        except Exception as e:
            logger.info(e)
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)

    return itemlist