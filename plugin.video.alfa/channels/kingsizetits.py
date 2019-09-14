# -*- coding: utf-8 -*-
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys
from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools

host = 'http://kingsizetits.com'


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append( Item(channel=item.channel, title="Nuevos" , action="lista", url=host + "/most-recent/"))
    itemlist.append( Item(channel=item.channel, title="Mas vistos" , action="lista", url=host + "/most-viewed-week/"))
    itemlist.append( Item(channel=item.channel, title="Mejor valorada" , action="lista", url=host + "/top-rated/"))
    itemlist.append( Item(channel=item.channel, title="Mas largos" , action="lista", url=host + "/longest/"))
    

    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories/"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search/videos/%s/" % texto
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
    patron = '<a href="([^"]+)" class="video-box.*?'
    patron += 'src=\'([^\']+)\' alt=\'([^\']+)\'.*?'
    patron += 'data-video-count="(\d+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle,cantidad in matches:
        scrapedplot = ""
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        title = scrapedtitle + " (" + cantidad + ")"
        itemlist.append( Item(channel=item.channel, action="lista", title=title, url=scrapedurl,
                              fanart=scrapedthumbnail, thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<script>stat.*?'
    patron += '<a href="([^"]+)".*?'
    patron += 'src="([^"]+)".*?'
    patron += '<span class="video-length">([^<]+)</span>.*?'
    patron += '<span class="pic-name">([^<]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtime,scrapedtitle in matches:
        title = "[COLOR yellow]" + scrapedtime + "[/COLOR] " + scrapedtitle
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        thumbnail = scrapedthumbnail
        plot = ""
        itemlist.append( Item(channel=item.channel, action="play", title=title, url=scrapedurl,
                              fanart=thumbnail, thumbnail=thumbnail, plot=plot, contentTitle = scrapedtitle))
    next_page = scrapertools.find_single_match(data, '<a class="btn default-btn page-next page-nav" href="([^"]+)"')
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
    logger.debug(data)
    url = scrapertools.find_single_match(data,'label:"\d+", file\:"([^"]+)"')
    itemlist.append(item.clone(action="play", server="directo", url=url ))
    return itemlist


