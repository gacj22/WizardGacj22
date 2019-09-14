# -*- coding: utf-8 -*-
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys
from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools

host = 'https://www.porn300.com'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="lista", url=host + "/en_US/ajax/page/list_videos/?page=1"))
    itemlist.append( Item(channel=item.channel, title="Canal" , action="categorias", url=host + "/channels/?page=1"))
    itemlist.append( Item(channel=item.channel, title="Pornstars" , action="categorias", url=host + "/pornstars/?page=1"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories/?page=1"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist
# view-source:https://www.porn300.com/en_US/ajax/page/show_search?q=big+tit&page=1
# https://www.porn300.com/en_US/ajax/page/show_search?page=2 
def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/en_US/ajax/page/show_search?q=%s&?page=1" % texto
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
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<a itemprop="url" href="/([^"]+)".*?'
    patron += 'data-src="([^"]+)" alt=.*?'
    patron += 'itemprop="name">([^<]+)</h3>.*?'
    patron += '</svg>([^<]+)<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle,cantidad in matches:
        scrapedplot = ""
        cantidad = re.compile("\s+", re.DOTALL).sub(" ", cantidad)
        scrapedtitle = scrapedtitle + " (" + cantidad +")"
        scrapedurl = scrapedurl.replace("channel/", "producer/")
        scrapedurl = "/en_US/ajax/page/show_" + scrapedurl + "?page=1"
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                              fanart=scrapedthumbnail, thumbnail=scrapedthumbnail, plot=scrapedplot) )
    next_page = scrapertools.find_single_match(data,'<link rel="next" href="([^"]+)" />')
    if next_page=="":
        if "/?page=1" in item.url:
            next_page=urlparse.urljoin(item.url,"/?page=2")
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="categorias", title="Página Siguiente >>", text_color="blue", url=next_page) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<a itemprop="url" href="([^"]+)".*?'
    patron += 'data-src="([^"]+)".*?'
    patron += 'itemprop="name">([^<]+)<.*?'
    patron += '</svg>([^<]+)<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle,scrapedtime  in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
        scrapedtime = scrapedtime.strip()
        title = "[COLOR yellow]" + scrapedtime + "[/COLOR] " + scrapedtitle
        contentTitle = title
        thumbnail = scrapedthumbnail
        plot = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=url, thumbnail=thumbnail,
                              fanart=thumbnail, plot=plot, contentTitle = contentTitle) )
    prev_page = scrapertools.find_single_match(item.url,"(.*?)page=\d+")
    num= int(scrapertools.find_single_match(item.url,".*?page=(\d+)"))
    num += 1
    num_page = "?page=" + str(num)
    if num_page!="":
        next_page = urlparse.urljoin(item.url,num_page)
        if "show_search" in next_page:
            next_page = prev_page + num_page
            next_page = next_page.replace("&?", "&")
        itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page) )
    return itemlist

def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '<source src="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for url  in matches:
        itemlist.append(item.clone(action="play", title=url, url=url))
    return itemlist

