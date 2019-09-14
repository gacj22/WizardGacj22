# -*- coding: utf-8 -*-
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys
from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools

host = 'https://www.gotporn.com'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Nuevos" , action="lista", url=host + "/?page=1"))
    itemlist.append( Item(channel=item.channel, title="Mejor valorados" , action="lista", url=host + "/top-rated?page=1"))
    itemlist.append( Item(channel=item.channel, title="Mas vistos" , action="lista", url=host + "/most-viewed?page=1"))
    itemlist.append( Item(channel=item.channel, title="Longitud" , action="lista", url=host + "/longest?page=1"))

    itemlist.append( Item(channel=item.channel, title="Canal" , action="catalogo", url=host + "/channels?page=1"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/results?search_query=%s" % texto
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


    patron = '<a href="([^"]+)">'
    patron += '<span class="text">([^<]+)</span>'
    patron += '<span class="num">([^<]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,cantidad in matches:
        scrapedplot = ""
        scrapedtitle = "%s %s" % (scrapedtitle,cantidad)
        scrapedurl = scrapedurl + "?page=1"
        thumbnail = ""
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                              thumbnail=thumbnail , plot=scrapedplot) )
    return itemlist


def catalogo(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    logger.debug(data)
    patron = '<header class="clearfix" itemscope>.*?'
    patron += '<a href="([^"]+)".*?'
    patron += '<img src="([^"]+)" alt="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle in matches:
        scrapedplot = ""
        scrapedurl = scrapedurl + "?page=1"
        thumbnail = "https:" + scrapedthumbnail
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                              thumbnail=thumbnail , plot=scrapedplot) )
    next_page = scrapertools.find_single_match(data, '<a href="([^"]+)" class="btn btn-secondary"><span class="text">Next')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append( Item(channel=item.channel, action="catalogo", title="Página Siguiente >>", text_color="blue", 
                              url=next_page) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<li class="video-item poptrigger".*?'
    patron += 'href="([^"]+)" data-title="([^"]+)".*?'
    patron += '<span class="duration">(.*?)</span>.*?'
    patron += 'src=\'([^\']+)\'.*?'
    patron += '<h3 class="video-thumb-title(.*?)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedtime,scrapedthumbnail,quality in matches:
        scrapedtime = scrapedtime.strip()
        title = "[COLOR yellow]" + scrapedtime + "[/COLOR] " + scrapedtitle
        if quality:
            title = "[COLOR yellow]%s[/COLOR] [COLOR red]HD[/COLOR] %s" % (scrapedtime,scrapedtitle)
        thumbnail = scrapedthumbnail
        plot = ""
        itemlist.append( Item(channel=item.channel, action="play", title=title, url=scrapedurl, thumbnail=thumbnail,
                              fanart=thumbnail, plot=plot,))
    next_page = scrapertools.find_single_match(data, '<a href="([^"]+)" class="btn btn-secondary')
    if "categories" in item.url:
        next_page = scrapertools.find_single_match(data, '<a href="([^"]+)" class="btn btn-secondary paginate-show-more')
    if "search_query" in item.url:
        next_page = scrapertools.find_single_match(data, '<link rel=\'next\' href="([^"]+)">')
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
    patron = '<source src="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for url in matches:
        url += "|Referer=%s" % host
        itemlist.append(item.clone(action="play", title = item.title, url=url ))
    return itemlist

