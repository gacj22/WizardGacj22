# -*- coding: utf-8 -*-

import re

from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from core import tmdb
from platformcode import config, logger

IDIOMAS = {'latino': 'Latino'}
list_language = IDIOMAS.values()
list_servers = ['openload',
                'okru',
                'myvideo',
                'sendvid'
                ]
list_quality = ['default']

host = 'http://www.seodiv.com'
language = 'latino'

def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = []

    itemlist.append(
        Item(channel=item.channel,
             title="Todos",
             action="todas",
             url=host,
             thumbnail='https://s27.postimg.cc/iahczwgrn/series.png',
             fanart='https://s27.postimg.cc/iahczwgrn/series.png',
             page=0
             ))
    autoplay.show_option(item.channel, itemlist)
    return itemlist


def todas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    logger.info("dasdsad"+data)
    patron = '<div class=shorrt-conte5nt><h4 class=short5-link7>'
    patron += '<a href=(.*?)class=.*?>'
    patron += '(.*?)<\/a>.+?'
    patron += '<img src=(.*?) alt.*?><\/a><\/div>'

    matches = re.compile(patron, re.DOTALL).findall(data)
    # Paginacion
    num_items_x_pagina = 30
    min = item.page * num_items_x_pagina
    min=int(min)-int(item.page)
    max = min + num_items_x_pagina - 1 #- 1 #ultimo item del regex sobra
    
    for scrapedurl, scrapedtitle, scrapedthumbnail,  in matches[min:max]:
        if " " in scrapedurl:
            scrapedurl = scrapedurl.replace(" ","")
        url = host + scrapedurl
        title = scrapedtitle.decode('utf-8')
        thumbnail = scrapedthumbnail
        fanart = 'https://s32.postimg.cc/gh8lhbkb9/seodiv.png'
        if 'TITULO' != title:
            itemlist.append(
                Item(channel=item.channel,
                 action="episodios",
                 title=title, url=url,
                 thumbnail=thumbnail,
                 fanart=fanart,
                 contentSerieName=title,
                 extra='',
                 language=language,
                 context=autoplay.context
                 ))
    tmdb.set_infoLabels(itemlist)
    if len(itemlist)>28:
        itemlist.append(
             Item(channel=item.channel, 
                title="[COLOR cyan]Página Siguiente >>[/COLOR]", 
                url=item.url, action="todas", 
                page=item.page + 1))
    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    patronpags = "<div class=pages>.+?<\/div><div class=col-lg-1 col-sm-2 col-xs-2 pages-next>"
    data2 = scrapertools.find_single_match(data, patronpags)
    patrontotal = "<a href=.*?>(.*?)<\/a>"
    matches = scrapertools.find_multiple_matches(data2, patrontotal)
    itemlist = capitulosxpagina(item,item.url)
    total = 0
    for totales in matches:
        total = int(totales)
    for x in range(1, total):
        url = item.url+"page/"+str(x+1)+"/"
        listitem = capitulosxpagina(item,url)
        if isinstance(listitem, list):
            itemlist= itemlist + listitem
    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(Item(channel=item.channel, title="[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]", url=item.url,
                             action="add_serie_to_library", extra="episodios", show=item.contentSerieName))
    return itemlist

def capitulosxpagina(item,url):
    itemlist = []
    data = httptools.downloadpage(url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    patron = '<div class=col-sm-4 col-xs-12><a href=(.*?) title=(.*?) class=.*?><img src=(.*?) class.*?>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    temp = 1
    if matches:
        for scrapedurl,scrapedtitle,scrapedthumbnail in matches:
            url = scrapedurl
            serieName = item.contentSerieName
            title = scrapedtitle.lower()
            logger.info
            if serieName.lower() in title:
            	title = title.split(serieName.lower())
            	title = title[1]
            thumbnail = scrapedthumbnail
            plot = item.plot
            fanart = scrapertools.find_single_match(data, '<img src="([^"]+)"/>.*?</a>')
            if "audio" not in title:
                if "temporada" in title:
                    title = title.split("temporada")
                    title = title[1]
                elif "capitulo" in title:
                    title = "01"+title
                if "capitulo" in title:
                    title = title.replace(" capitulo ","x")
                if len(title) > 3:
                    itemlist.append(
                        Item(channel=item.channel,
                        action="findvideos",
                        title=title,
                        contentTitle=item.title,
                        url=url,
                        thumbnail=thumbnail,
                        plot=plot, fanart=fanart,
                        temp=str(temp),
                        contentSerieName=item.contentSerieName,
                        context=item.context
                        ))
        return itemlist

def findvideos(item):
    logger.info()
    itemlist = []
    lang=[]
    data = httptools.downloadpage(item.url).data
    video_items = servertools.find_video_items(item)
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    language_items=scrapertools.find_single_match(data,
                 '<ul class=tabs-sidebar-ul>(.+?)<\/ul>')
    matches=scrapertools.find_multiple_matches(language_items,
                 '<li><a href=#ts(.+?)><span>(.+?)<\/span><\/a><\/li>')
    for idl,scrapedlang in matches:
        if int(idl)<5 and int(idl)!=1:
            lang.append(scrapedlang)
    i=0
    if len(lang)!=0:
        lang.reverse()
    for videoitem in video_items:
        videoitem.thumbnail = servertools.guess_server_thumbnail(videoitem.server)
        if i<len(lang) and len(lang)!=0:
            videoitem.language=lang[i]
        else:
            videoitem.language = scrapertools.find_single_match(data, '<span class=f-info-title>Idioma:<\/span>\s*<span '
                                                                'class=f-info-text>(.*?)<\/span>')
        videoitem.title = item.contentSerieName + ' (' + videoitem.server + ') (' + videoitem.language + ')'
        videoitem.quality = 'default'
        videoitem.context = item.context
        i=i+1
        itemlist.append(videoitem)

    # Requerido para FilterTools

    if len(itemlist) > 0 and filtertools.context:
        itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    return itemlist
