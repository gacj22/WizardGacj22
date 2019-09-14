# -*- coding: utf-8 -*-
# ------------------------------------------------------------
import urlparse
import re
import base64

from platformcode import config, logger
from core import scrapertools
from core import servertools
from core.item import Item
from core import httptools

host = 'https://pandamovies.pw'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Peliculas", action="lista", url=host + "/movies"))
    itemlist.append(Item(channel=item.channel, title="Categorias", action="categorias", url=host + "/movies"))
    itemlist.append(Item(channel=item.channel, title="Canal", action="categorias", url=host + "/movies"))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search"))
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
    itemlist = []
    data = httptools.downloadpage(item.url).data
    if item.title == "Categorias":
        data = scrapertools.find_single_match(data, '<a href="#">Genres</a>(.*?)</ul>')
    else:
        data = scrapertools.find_single_match(data, '<a href="#">Studios</a>(.*?)</ul>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<a href="([^"]+)">([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedurl = scrapedurl.replace("https:", "")
        scrapedurl = "https:" + scrapedurl
        itemlist.append(Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                             thumbnail=scrapedthumbnail, plot=scrapedplot))
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<div data-movie-id="\d+".*?'
    patron += '<a href="([^"]+)".*?oldtitle="([^"]+)".*?'
    patron += '<img data-original="([^"]+)".*?'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
        url = urlparse.urljoin(item.url, scrapedurl)
        title = scrapedtitle
        thumbnail = scrapedthumbnail
        plot = ""
        itemlist.append(Item(channel=item.channel, action="findvideos", title=title, url=url, thumbnail=thumbnail,
                             fanart=thumbnail, plot=plot, contentTitle=title))
    next_page = scrapertools.find_single_match(data, '<li class=\'active\'>.*?href=\'([^\']+)\'>')
    if next_page == "":
        next_page = scrapertools.find_single_match(data, '<a.*?href="([^"]+)" >Next &raquo;</a>')
    if next_page != "":
        next_page = urlparse.urljoin(item.url, next_page)
        itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page))
    return itemlist


def findvideos(item):
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|amp;|\s{2}|&nbsp;", "", data)
    patron = '- on ([^"]+)" href="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedtitle,url in matches:
        if 'aHR0' in url:
            n = 3
            while n > 0:
                url= url.replace("https://vshares.tk/goto/", "").replace("https://waaws.tk/goto/", "").replace("https://openloads.tk/goto/", "")
                logger.debug (url)
                url = base64.b64decode(url)
                n -= 1
        if "mangovideo" in url:  #Aparece como directo
            data = httptools.downloadpage(url).data
            patron = 'video_url: \'function/0/https://mangovideo.pw/get_file/(\d+)/\w+/(.*?)/\?embed=true\''
            matches = scrapertools.find_multiple_matches(data, patron)
            for scrapedtitle,url in matches:
                if scrapedtitle =="1":  scrapedtitle= "https://www.mangovideo.pw/contents/videos/"
                if scrapedtitle =="7":  scrapedtitle= "https://server9.mangovideo.pw/contents/videos/"
                if scrapedtitle =="8":  scrapedtitle= "https://s10.mangovideo.pw/contents/videos/"
                if scrapedtitle =="10": scrapedtitle= "https://server217.mangovideo.pw/contents/videos/"
                if scrapedtitle =="11": scrapedtitle= "https://234.mangovideo.pw/contents/videos/"
                url = scrapedtitle + url
        itemlist.append( Item(channel=item.channel, action="play", title = "%s", url=url ))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist

