# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
# Canal para Hemeroteca NBA
#------------------------------------------------------------
from core import logger
from core import config
from core import httptools
from core import scrapertools
from core.item import Item

__channel__ = "hemerotecanba"


def mainlist(item):
    logger.info("deportesalacarta.channels.hemerotecanba mainlist")
    itemlist = []

    itemlist.append(Item(channel=__channel__, title="Novedades", url="http://www.lahemerotecanba.es/", action="novedades", thumbnail=item.thumbnail, fanart=item.fanart))
    itemlist.append(Item(channel=__channel__, title="Baloncesto", url="http://www.lahemerotecanba.es/", action="categorias", thumbnail=item.thumbnail, fanart=item.fanart))
    itemlist.append(Item(channel=__channel__, title="NFL", url="http://www.lahemerotecanba.es/", action="categorias", thumbnail=item.thumbnail, fanart=item.fanart))
    itemlist.append(Item(channel=__channel__, title="Fútbol", url="http://www.lahemerotecanba.es/search/label/F%C3%9ATBOL", action="novedades", thumbnail=item.thumbnail, fanart=item.fanart))
    itemlist.append(Item(channel=__channel__, title="Películas", url="http://www.lahemerotecanba.es/search/label/PEL%C3%8DCULAS", action="novedades", thumbnail=item.thumbnail, fanart=item.fanart))

    return itemlist

def novedades(item):
    logger.info("deportesalacarta.channels.hemerotecanba novedades")
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = data.replace("\n","").replace("\t","")
    patron = "<h3 class='post-title entry-title'>.*?<a href='([^']+)'>(.*?)</a>.*?src=\"([^\"]+)\""
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
        itemlist.append(Item(channel=__channel__, title=scrapedtitle, action="findvideos", url=scrapedurl, thumbnail=scrapedthumbnail, folder=True))

    next_page = scrapertools.find_single_match(data, "<a class='blog-pager-older-link' href='([^']+)'")
    if next_page != "":
        itemlist.append(Item(channel=__channel__, title=">> Siguiente", action="novedades", url=next_page, thumbnail=item.thumbnail, folder=True))

    return itemlist

def categorias(item):
    logger.info("deportesalacarta.channels.hemerotecanba categorias")
    itemlist = []

    if item.title == "Baloncesto":
        itemlist.append(Item(channel=__channel__, title="Temporadas NBA", url=item.url, action="categorias", thumbnail=item.thumbnail, folder=True))
        itemlist.append(Item(channel=__channel__, title="Documentales", url="http://lahemerotecanba.blogspot.com.es/search/label/DOCUMENTALES", action="novedades", thumbnail=item.thumbnail, folder=True))
        itemlist.append(Item(channel=__channel__, title="Históricos", url="http://lahemerotecanba.blogspot.com.es/search/label/HISTÓRICOS", action="novedades", thumbnail=item.thumbnail, folder=True))
        itemlist.append(Item(channel=__channel__, title="Finales NBA", url=item.url, action="categorias", thumbnail=item.thumbnail, folder=True))
        itemlist.append(Item(channel=__channel__, title="Programas", url="http://lahemerotecanba.blogspot.com.es/search/label/PROGRAMAS", action="novedades", thumbnail=item.thumbnail, folder=True))
        itemlist.append(Item(channel=__channel__, title="Generación NBA+", url="http://lahemerotecanba.blogspot.com.es/search/label/GNBA", action="novedades", thumbnail=item.thumbnail, folder=True))
        itemlist.append(Item(channel=__channel__, title="NCAA - High School", url="http://lahemerotecanba.blogspot.com.es/search/label/NCAA", action="novedades", thumbnail=item.thumbnail, folder=True))
        itemlist.append(Item(channel=__channel__, title="FIBA", url="http://lahemerotecanba.blogspot.com.es/search/label/FIBA", action="novedades", thumbnail=item.thumbnail, folder=True))
    elif item.title == "NFL":
        itemlist.append(Item(channel=__channel__, title="Temporadas NFL", url=item.url, action="categorias", thumbnail=item.thumbnail, folder=True))
        itemlist.append(Item(channel=__channel__, title="Super Bowls", url=item.url, action="categorias", thumbnail=item.thumbnail, folder=True))
        itemlist.append(Item(channel=__channel__, title="NCAA Football", url="http://lahemerotecanba.blogspot.com.es/search/label/NCAA%20FOOTBALL", action="novedades", thumbnail=item.thumbnail, folder=True))
    else:
        data = httptools.downloadpage(item.url).data
        data = data.replace("\n","").replace("\t","")
        bloque = scrapertools.find_single_match(data, item.title+'[^<]+</a><ul>(.*?)</ul>')
        matches = scrapertools.find_multiple_matches(bloque, "<li><a href='([^']+)'>(.*?)</a>")
        for scrapedurl, scrapedtitle in matches:
            scrapedurl = scrapedurl.replace(" ", "%20")
            itemlist.append(Item(channel=__channel__, title=scrapedtitle, action="novedades", url=scrapedurl, thumbnail=item.thumbnail, folder=True))

    return itemlist