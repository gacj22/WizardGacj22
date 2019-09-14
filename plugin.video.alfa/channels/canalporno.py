# -*- coding: utf-8 -*-
import urlparse,re

from core import httptools
from core import scrapertools
from platformcode import logger

host = "http://www.canalporno.com"


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(action="lista", title="Útimos videos", url=host + "/ajax/homepage/?page=1"))
    itemlist.append(item.clone(action="categorias", title="Canal", url=host + "/ajax/list_producers/?page=1"))
    itemlist.append(item.clone(action="categorias", title="PornStar", url=host + "/ajax/list_pornstars/?page=1"))
    itemlist.append(item.clone(action="categorias", title="Categorias",
                               url=host + "/categorias"))
    itemlist.append(item.clone(action="search", title="Buscar"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/ajax/new_search/?q=%s&page=1" % texto
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
    if "pornstars" in item.url:
        patron = '<div class="muestra.*?href="([^"]+)".*?src=\'([^\']+)\'.*?alt="([^"]+)".*?'
    else:
        patron = '<div class="muestra.*?href="([^"]+)".*?src="([^"]+)".*?alt="([^"]+)".*?'
    if "Categorias" in item.title:
        patron += '<div class="numero">([^<]+)</div>'
    else:
        patron += '</span> (\d+) vídeos</div>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for url, scrapedthumbnail, scrapedtitle, cantidad in matches:
        title= "%s [COLOR yellow] %s [/COLOR]" % (scrapedtitle, cantidad) 
        url= url.replace("/videos-porno/", "/ajax/show_category/").replace("/sitio/", "/ajax/show_producer/").replace("/pornstar/", "/ajax/show_pornstar/")
        url = host + url + "?page=1"
        itemlist.append(item.clone(action="lista", title=title, url=url, thumbnail=scrapedthumbnail))
    if "/?page=" in item.url:
        next_page=item.url
        num= int(scrapertools.find_single_match(item.url,".*?/?page=(\d+)"))
        num += 1
        next_page = "?page=" + str(num)
        if next_page!="":
            next_page = urlparse.urljoin(item.url,next_page)
            itemlist.append(item.clone(action="categorias", title="Página Siguiente >>", text_color="blue", url=next_page) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = 'data-src="([^"]+)" alt="([^"]+)".*?<h2><a href="([^"]+)">.*?' \
             '<div class="duracion"><span class="ico-duracion sprite"></span> ([^"]+) min</div>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedthumbnail, scrapedtitle, scrapedurl, duration in matches:
        title = "[COLOR yellow] %s  [/COLOR] %s" % (duration, scrapedtitle)
        url = host + scrapedurl
        itemlist.append(item.clone(action="play", title=title, url=url, thumbnail=scrapedthumbnail))
    last=scrapertools.find_single_match(item.url,'(.*?)page=\d+')
    num= int(scrapertools.find_single_match(item.url,".*?/?page=(\d+)"))
    num += 1
    next_page = "page=" + str(num)
    if next_page!="":
        next_page = last + next_page
        itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    url = scrapertools.find_single_match(data, '<source src="([^"]+)"')
    itemlist.append(item.clone(url=url, server="directo"))
    return itemlist
