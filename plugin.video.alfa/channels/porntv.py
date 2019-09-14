# -*- coding: utf-8 -*-
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys
from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools

host = 'https://www.porntv.com'


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append( Item(channel=item.channel, title="Nuevos" , action="lista", url=host + "/videos/straight/all-recent.html"))
    itemlist.append( Item(channel=item.channel, title="Mas vistos" , action="lista", url=host + "/videos/straight/all-view.html"))
    itemlist.append( Item(channel=item.channel, title="Mejor valorada" , action="lista", url=host + "/videos/straight/all-rate.html"))
    itemlist.append( Item(channel=item.channel, title="Mas popular" , action="lista", url=host + "/videos/straight/all-popular.html"))
    itemlist.append( Item(channel=item.channel, title="Mas largos" , action="lista", url=host + "/videos/straight/all-length.html"))
    

    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories/"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "")
    item.url = host + "/videos/straight/%s-recent.html" % texto
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    data = scrapertools.find_single_match(data, '<h1>Popular Categories</h1>(.*?)<h1>Community</h1>')
    patron = '<h2><a href="([^"]+)">([^<]+)</a>.*?'
    patron += 'src="([^"]+)".*?'
    patron += '<span class="contentquantity">([^<]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail,cantidad in matches:
        scrapedplot = ""
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        title = scrapedtitle + " " + cantidad
        itemlist.append( Item(channel=item.channel, action="lista", title=title, url=scrapedurl,
                              fanart=scrapedthumbnail, thumbnail=scrapedthumbnail , plot=scrapedplot) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<div class="item" style="width: 320px">.*?'
    patron += '<a href="([^"]+)".*?'
    patron += '<img src="([^"]+)".*?'
    patron += '>(.*?)<div class="trailer".*?'
    patron += 'title="([^"]+)".*?'
    patron += 'clock"></use></svg>([^<]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,quality,scrapedtitle,scrapedtime in matches:
        title = "[COLOR yellow]" + scrapedtime + "[/COLOR] " + scrapedtitle
        if "flag-hd" in quality:
            title = "[COLOR yellow]" + scrapedtime + "[/COLOR] " + "[COLOR red]" + "HD" + "[/COLOR] " + scrapedtitle
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        thumbnail = scrapedthumbnail
        plot = ""
        itemlist.append( Item(channel=item.channel, action="play", title=title, url=scrapedurl,
                              fanart=thumbnail, thumbnail=thumbnail, plot=plot, contentTitle = scrapedtitle))
                              
    next_page = scrapertools.find_single_match(data, '<a href="([^"]+)" class="next"')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append( Item(channel=item.channel, action="lista", title="Página Siguiente >>", text_color="blue", 
                              url=next_page) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    data = scrapertools.find_single_match(data, 'sources: \[(.*?)\]')
    patron = 'file: "([^"]+)",.*?label: "([^"]+)",'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for url,quality in matches:
        itemlist.append(["%s %s [directo]" % (quality, url), url])
    return itemlist


