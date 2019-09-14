# -*- coding: utf-8 -*-
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from core import httptools
from channels import pornhub, xvideos,youporn

host = 'http://qwertty.net'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Recientes" , action="lista", url=host))
    itemlist.append( Item(channel=item.channel, title="Mas Vistas" , action="lista", url=host + "/?filter=most-viewed"))
    itemlist.append( Item(channel=item.channel, title="Mas popular" , action="lista", url=host + "/?filter=popular"))
    itemlist.append( Item(channel=item.channel, title="Mejor valoradas" , action="lista", url=host + "/?filter=random"))
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


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '<li><a href="([^<]+)">(.*?)</a></li>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedurl = host + scrapedurl
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                              thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<article id="post-\d+".*?'
    patron += '<a href="([^"]+)" title="([^"]+)">.*?'
    patron += '<div class="post-thumbnail(.*?)<span class="views">.*?'
    patron += '<span class="duration"><i class="fa fa-clock-o"></i>([^<]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail,duracion in matches:
        scrapedplot = ""
        thumbnail = scrapertools.find_single_match(scrapedthumbnail, 'poster="([^"]+)"')
        if thumbnail == "":
            thumbnail = scrapertools.find_single_match(scrapedthumbnail, "data-thumbs='(.*?jpg)")
        title = "[COLOR yellow]" + duracion + "[/COLOR] " + scrapedtitle
        itemlist.append( Item(channel=item.channel, action="play", title=title, url=scrapedurl,
                              fanart=thumbnail, thumbnail=thumbnail, plot=scrapedplot) )
    next_page = scrapertools.find_single_match(data,'<li><a href="([^"]+)">Next</a>')
    if next_page=="":
        next_page = scrapertools.find_single_match(data,'<li><a class="current">.*?<li><a href="([^"]+)" class="inactive">')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    url1 = scrapertools.find_single_match(data,'<meta itemprop="embedURL" content="([^"]+)"')
    if "spankwire" in url1: 
        data = httptools.downloadpage(item.url).data
        data = scrapertools.get_match(data,'Copy Embed Code(.*?)For Desktop')
        patron  = '<div class="shareDownload_container__item__dropdown">.*?<a href="([^"]+)"'
        matches = scrapertools.find_multiple_matches(data, patron)
        for scrapedurl  in matches:
            url = scrapedurl
            if url=="#":
                url = scrapertools.find_single_match(data,'playerData.cdnPath480         = \'([^\']+)\'')
            itemlist.append(item.clone(action="play", title=url, contentTitle = url, url=url))
    elif "xvideos1" in url1: 
        item1 = item.clone(url=url1)
        itemlist = xvideos.play(item1)
        return itemlist
    elif "pornhub" in url1 :
        url = url1
    elif "txx" in url1:# Falta conector
        url = ""
    elif "youporn" in url1: 
        item1 = item.clone(url=url1)
        itemlist = youporn.play(item1)
        return itemlist
    else:
        data = httptools.downloadpage(url1).data
        url  = scrapertools.find_single_match(data,'"quality":"\d+","videoUrl":"([^"]+)"')
    url = url.replace("\/", "/")

    itemlist.append(item.clone(action="play", title= "%s  " + url1, contentTitle = item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize()) 
    return itemlist

