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

IDIOMAS = {'latino': 'Latino'}
list_language = IDIOMAS.values()
list_servers = ['openload'
                ]
list_quality = ['default']


host = "https://abtoon.net"


def mainlist(item):
    logger.info()
    thumb_series = get_thumb("channels_tvshow.png")
    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(
        Item(channel=item.channel, action="lista", title="Series Actuales", url=host+'/p/actuales',
             thumbnail=thumb_series))

    itemlist.append(
        Item(channel=item.channel, action="lista", title="Series Clasicas", url=host+'/p/clasicas',
             thumbnail=thumb_series))

    itemlist.append(
        Item(channel=item.channel, action="lista", title="Series Anime", url=host + '/p/anime',
             thumbnail=thumb_series))

    itemlist.append(
        Item(channel=item.channel, action="lista", title="Series Live Action", url=host + '/p/live-action',
             thumbnail=thumb_series))
    itemlist.append(
        Item(channel=item.channel, action="search", title="Buscar", thumbnail=''))

    itemlist = renumbertools.show_option(item.channel, itemlist)
    autoplay.show_option(item.channel, itemlist)
    return itemlist


def lista(item):
    logger.info()

    itemlist = []

    full_data = httptools.downloadpage(item.url).data
    full_data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", full_data)
    data = scrapertools.find_single_match(full_data, 'class="sl">(.*?)<div class="pag">')
    patron = '<a href="([^"]+)".*?<img src="([^"]+)".*?title="([^"]+)">'

    matches = scrapertools.find_multiple_matches(data, patron)


    for link, img, name in matches:
        if " y " in name:
            title=name.replace(" y "," & ")
        else:
            title = name
        url = host + link
        scrapedthumbnail = host + img
        context = renumbertools.context(item)
        context2 = autoplay.context
        context.extend(context2)
        
        itemlist.append(Item(channel=item.channel, title=title, url=url, action="episodios", thumbnail=scrapedthumbnail,
                                   contentSerieName=title, context=context))

    # Paginacion

    next_page = scrapertools.find_single_match(full_data, '<a class="sel">\d+</a><a href="([^"]+)">\d+</a>')
    if next_page != '':
        itemlist.append(Item(channel=item.channel, contentSerieName=item.contentSerieName,
                             title="[COLOR cyan]Página Siguiente >>[/COLOR]", url=host+next_page, action="lista"))

    tmdb.set_infoLabels(itemlist)
    return itemlist

def peliculas(item):
    logger.info()

    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<div class="pel play" dt="(.+?)" .+?><img src="(.+?)" .+? title="(.*?)"><span class=".+?">(.+?)<\/span><a href="(.+?)" class.+?>'
    matches = scrapertools.find_multiple_matches(data, patron)
    # Paginacion
    num_items_x_pagina = 30
    min = item.page * num_items_x_pagina
    min=min-item.page
    max = min + num_items_x_pagina - 1
    b=0
    for scrapedplot,scrapedthumbnail, scrapedtitle, scrapedyear, scrapedurl in matches[min:max]:
        b=b+1
        url = host + scrapedurl
        thumbnail = host +scrapedthumbnail
        context = renumbertools.context(item)
        context2 = autoplay.context
        context.extend(context2)
        itemlist.append(item.clone(title=scrapedtitle+"-"+scrapedyear, url=url, action="findvideos", thumbnail=thumbnail, plot=scrapedplot,
                show=scrapedtitle,contentSerieName=scrapedtitle,context=context))
    if b<29:
        pass
    else:    
        itemlist.append(
             Item(channel=item.channel, contentSerieName=item.contentSerieName, title="[COLOR cyan]Página Siguiente >>[/COLOR]", url=item.url, action="peliculas", page=item.page + 1))

    tmdb.set_infoLabels(itemlist)
    return itemlist

def episodios(item):
    logger.info()

    itemlist = []
    data = httptools.downloadpage(item.url).data
    # obtener el numero total de episodios
    total_episode = 0

    patron_caps = '<li><a href="(.*?)">(.*?) - (.*?)<\/a><\/li>'
    matches = scrapertools.find_multiple_matches(data, patron_caps)
    patron_info = '<img src="([^"]+)" .+?>.+?<h1>([^"]+)<\/h1><p .+?>(.+?)<\/p>'
    scrapedthumbnail, show, scrapedplot = scrapertools.find_single_match(data, patron_info)
    scrapedthumbnail = host + scrapedthumbnail

    for link, cap, name in matches:

        title = ""
        pat = "$%&"
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
        if "DISPONIBLE" in name:
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
    _sl = scrapertools.find_single_match(data, 'var abi = ([^;]+);')
    sl = eval(_sl)
    buttons = scrapertools.find_multiple_matches(data,'class="bsel" sl="(.+?)"')#[0,1,2,3,4]
    for ids in buttons:
        id = int(ids)
        url_end = golink(id,sl)
        new_url = "https://abtoon.net/" + "embed/" + sl[0] + "/" + sl[1] + "/" + str(id) + "/" + sl[2] + url_end
        data_new = httptools.downloadpage(new_url).data
        data_new = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data_new)
        if data_new!= "502":
            valor1, valor2 = scrapertools.find_single_match(data_new, 'var x0x = \["[^"]*", "([^"]+)", "[^"]*", "[^"]*", "([^"]+)"\];') 
            try:
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

def search_results(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, post=item.post).data
    if len(data) > 0:
        results = eval(data)
    else:
        return itemlist

    for result in results:
        try:
            thumbnail = host + "/tb/%s.jpg" % result[0]
            title = u'%s' % result[1]
            logger.debug(title)
            url = host + "/s/%s" % result[2]
            itemlist.append(Item(channel=item.channel, thumbnail=thumbnail, title=title, url=url, contentSerieName=title,
                                 action='episodios'))
        except:
            pass

    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    return itemlist

def search(item, texto):
    logger.info()
    import urllib

    if texto != "":
        texto = texto.replace(" ", "+")
    item.url = host+"/b.php"
    post = {'k':texto, "pe":"", "te":""}
    item.post = urllib.urlencode(post)

    try:
        return search_results(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def golink(ida,sl):
    a=ida
    b=[3,10,5,22,31]
    c=1
    d=""
    e=sl[2]
    for i in range(len(b)):
      d=d+substr(e,b[i]+a,c)
    return d

def substr(st,a,b):
    return st[a:a+b]