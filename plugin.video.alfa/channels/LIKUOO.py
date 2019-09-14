# -*- coding: utf-8 -*-
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys
from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools

host = 'https://www.likuoo.video'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Ultimos" , action="lista", url=host))
    itemlist.append( Item(channel=item.channel, title="Pornstar" , action="categorias", url=host + "/pornstars/"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/all-channels/"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search/?s=%s" % texto
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
    patron  = '<div class="item_p">.*?<a href="([^"]+)" title="([^"]+)"><img src="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail in matches:
        scrapedplot = ""
        scrapedthumbnail = "https:" + scrapedthumbnail
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                              fanart=scrapedthumbnail, thumbnail=scrapedthumbnail, plot=scrapedplot) )
    next_page = scrapertools.find_single_match(data,'...<a href="([^"]+)" class="next">&#187;</a>')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="categorias", title="Página Siguiente >>", text_color="blue", url=next_page) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<div class="item">.*?'
    patron += '<a href="([^"]+)" title="(.*?)">.*?'
    patron += 'src="(.*?)".*?'
    patron += '<div class="runtime">(.*?)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail,scrapedtime in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
        scrapedtime = scrapedtime.replace("m", ":").replace("s", " ")
        title = "[COLOR yellow]" + scrapedtime + "[/COLOR] " +scrapedtitle
        contentTitle = title
        thumbnail = "https:" + scrapedthumbnail
        plot = ""
        itemlist.append( Item(channel=item.channel, action="play", title=title, url=url, thumbnail=thumbnail,
                              fanart=thumbnail, plot=plot, contentTitle = contentTitle))
    next_page = scrapertools.find_single_match(data,'...<a href="([^"]+)" class="next">&#187;</a>')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page) )
    return itemlist


def play(item):
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|amp;|\s{2}|&nbsp;", "", data)
    patron = 'url:\'([^\']+)\'.*?'
    patron += 'data:\'([^\']+)\''
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl,post in matches:
        post = post.replace("%3D", "=")
        scrapedurl = host + scrapedurl
        logger.debug( item.url +" , "+ scrapedurl +" , " +post )
        datas = httptools.downloadpage(scrapedurl, post=post, headers={'Referer':item.url}).data
        datas = datas.replace("\\", "")
        url = scrapertools.find_single_match(datas, '<iframe src="([^"]+)"')
        itemlist.append( Item(channel=item.channel, action="play", title = "%s", url=url ))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist

