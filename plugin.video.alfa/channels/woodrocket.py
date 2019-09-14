# -*- coding: utf-8 -*-
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from core import httptools

host = 'http://woodrocket.com'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Novedades" , action="lista", url=host + "/porn"))
    itemlist.append( Item(channel=item.channel, title="Parodias" , action="lista", url=host + "/parodies"))
    itemlist.append( Item(channel=item.channel, title="Shows" , action="categorias", url=host + "/series"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories"))
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '<div class="media-panel-image">.*?<img src="(.*?)".*?<a href="(.*?)">(.*?)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedthumbnail,scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail =  host + scrapedthumbnail
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                              fanart=scrapedthumbnail, thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<div class="media-panel-image">.*?<a href="([^"]+)".*?title="([^"]+)".*?<img src="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail in matches:
        plot = ""
        contentTitle = scrapedtitle
        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        title = scrapedtitle
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=scrapedurl, thumbnail=thumbnail,
                              fanart=thumbnail, plot=plot, contentTitle = contentTitle))
    next_page = scrapertools.find_single_match(data,'<li><a href="([^"]+)" rel="next">&raquo;</a></li>')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    url  = scrapertools.find_single_match(data,'<iframe src="([^"]+)"')
    itemlist.append(item.clone(action="play", title= "%s", url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist

