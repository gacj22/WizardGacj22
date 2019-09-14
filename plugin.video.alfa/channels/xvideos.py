# -*- coding: utf-8 -*-
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys
from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools

host = 'https://www.xvideos.com'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Nuevos" , action="lista", url=host))
    itemlist.append( Item(channel=item.channel, title="Lo mejor" , action="lista", url=host + "/best/"))
    itemlist.append( Item(channel=item.channel, title="Pornstar" , action="catalogo", url=host + "/pornstars-index"))
    itemlist.append( Item(channel=item.channel, title="WebCAM" , action="catalogo", url=host + "/webcam-models-index"))
    itemlist.append( Item(channel=item.channel, title="Canal" , action="catalogo", url=host + "/channels-index/top"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/tags"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/?k=%s" % texto
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
    patron = '<li><a href="([^"]+)"><b>([^<]+)</b><span class="navbadge default">([^<]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,cantidad in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        title = scrapedtitle + " (" + cantidad + ")"
        itemlist.append( Item(channel=item.channel, action="lista", title=title, url=scrapedurl,
                              thumbnail=scrapedthumbnail , plot=scrapedplot) )
    return itemlist


def catalogo(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<img src="([^"]+)".*?'
    patron += '<p class="profile-name">.*?<a href="([^"]+)">([^<]+)</a>.*?'
    patron += '<span class="with-sub">([^<]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedthumbnail,scrapedurl,scrapedtitle,cantidad in matches:
        scrapedplot = ""
        scrapedurl = urlparse.urljoin(host,scrapedurl) + "/videos/new/0"
        title = scrapedtitle + " (" + cantidad + ")"
        itemlist.append( Item(channel=item.channel, action="lista", title=title, url=scrapedurl,
                              thumbnail=scrapedthumbnail , plot=scrapedplot) )
    next_page = scrapertools.find_single_match(data, '<li><a href="([^"]+)" class="no-page next-page">Siguiente')
    if next_page=="":
        next_page = scrapertools.find_single_match(data, '<li><a class="active".*?<a href="([^"]+)"')
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
    patron = '<div id="video_\d+".*?'
    patron += 'data-src="([^"]+)".*?'
    patron += '</a>(.*?)<div class=.*?'
    patron += '<a href="([^"]+)" title="([^"]+)".*?'
    patron += '<span class="duration">([^<]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedthumbnail,quality,scrapedurl,scrapedtitle,scrapedtime in matches:
        title = "[COLOR yellow]" + scrapedtime + "[/COLOR] " + scrapedtitle
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        thumbnail = scrapedthumbnail.replace("THUMBNUM" , "10")
        quality = scrapertools.find_single_match(quality, 'mark">([^<]+)</span>')
        if quality:
            title = "[COLOR yellow]" + scrapedtime + "[/COLOR] " + "[COLOR red]" + quality + "[/COLOR] " + scrapedtitle
        plot = ""
        itemlist.append( Item(channel=item.channel, action="play", title=title, url=scrapedurl,
                              thumbnail=thumbnail, fanart=thumbnail, plot=plot, contentTitle = scrapedtitle))
    next_page = scrapertools.find_single_match(data, '<li><a href="([^"]+)" class="no-page next-page">Siguiente')
    if "profile" in item.url:
        next_page = scrapertools.find_single_match(data, '<li><a class="active" href="">(\d+)</a></li><li><a href="#')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page).replace("&amp;", "&")
        itemlist.append( Item(channel=item.channel, action="lista", title="Página Siguiente >>", text_color="blue", 
                              url=next_page) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    url = scrapertools.find_single_match(data, 'html5player.setVideoHLS\(\'([^\']+)\'\)')
    itemlist.append(item.clone(action="play", title=url, url=url ))
    return itemlist

