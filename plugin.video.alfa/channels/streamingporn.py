# -*- coding: utf-8 -*-
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys
from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools

host = 'http://streamingporn.xyz'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Peliculas" , action="lista", url=host + "/category/movies/"))
    itemlist.append( Item(channel=item.channel, title="Videos" , action="lista", url=host + "/category/stream/"))
    itemlist.append( Item(channel=item.channel, title="Canal" , action="catalogo", url=host))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/?s=%s" % texto
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def catalogo(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data,'PaySites(.*?)<li id="menu-item-28040"')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<li id="menu-item-\d+".*?<a href="([^"]+)">([^"]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle , url=scrapedurl , 
                        thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data,'<a href="#">Categories</a>(.*?)</ul>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<li id="menu-item-\d+".*?<a href="([^"]+)">([^"]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedtitle = scrapedtitle
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle , url=scrapedurl , 
                        thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<div class="entry-featuredImg">.*?<a href="([^"]+)">.*?<img src="([^"]+)" alt="([^"]+)">'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle  in matches:
        url = scrapedurl
        title = scrapedtitle
        if 'HD' in scrapedtitle :
            calidad = scrapertools.find_single_match(scrapedtitle, '(\d+)p')
            title = "[COLOR red]" + "HD" +"[/COLOR] "+ scrapedtitle
            if calidad :
                title = "[COLOR red]" + "HD" + calidad +" [/COLOR] "+ scrapedtitle
        contentTitle = title
        thumbnail = scrapedthumbnail
        plot = ""
        itemlist.append( Item(channel=item.channel, action="findvideos" , title=title , url=url, thumbnail=thumbnail, 
                              fanart=scrapedthumbnail, plot=plot, contentTitle = contentTitle) )
    next_page_url = scrapertools.find_single_match(data,'<div class="loadMoreInfinite"><a href="(.*?)" >Load More')
    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="lista" , title="Página Siguiente >>" , 
                        text_color="blue", url=next_page_url) )
    return itemlist

