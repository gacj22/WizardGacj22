# -*- coding: utf-8 -*-

import re

from core import httptools
from core import scrapertools
from platformcode import config, logger


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone(action="categorias", title="Categorías", url="http://dato.porn/categories_all", contentType="movie", viewmode="movie"))
    itemlist.append(item.clone(title="Buscar...", action="search", contentType="movie", viewmode="movie"))
    return itemlist


def search(item, texto):
    logger.info()
    item.url = "http://dato.porn/?k=%s&op=search" % texto.replace(" ", "+")
    return lista(item)


def lista(item):
    logger.info()
    itemlist = []
    data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url).data)
    patron = '<div class="videobox">\s*<a href="([^"]+)".*?'
    patron += 'url\(\'([^\']+)\'.*?'
    patron += '<span>(.*?)<\/span>.*?'
    patron += 'class="title">(.*?)<\/a>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail, duration, scrapedtitle in matches:
        if "/embed-" not in scrapedurl:
            scrapedurl = scrapedurl.replace("datoporn.co/", "datoporn.co/embed-") + ".html"
        if not config.get_setting('unify'):
            scrapedtitle = '[COLOR yellow] %s [/COLOR] %s' % (duration , scrapedtitle)
        else:
            scrapedtitle += ' gb'
            scrapedtitle = "[COLOR yellow]" + duration + "[/COLOR] " + scrapedtitle
            scrapedtitle = scrapedtitle.replace(":", "'")
        # logger.debug(scrapedurl + ' / ' + scrapedthumbnail + ' / ' + duration + ' / ' + scrapedtitle)
        itemlist.append(item.clone(action="play", title=scrapedtitle, url=scrapedurl, thumbnail=scrapedthumbnail, server="datoporn", 
                                   fanart=scrapedthumbnail.replace("_t.jpg", ".jpg"), plot = ""))
    next_page = scrapertools.find_single_match(data, '<a class=["|\']page-link["|\'] href=["|\']([^["|\']+)["|\']>Next')
    if next_page and itemlist:
        itemlist.append(item.clone(action="lista", title=">> Página Siguiente", url=next_page))
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<div class="vid_block">\s*<a href="([^"]+)".*?url\((.*?)\).*?<span>(.*?)</span>.*?<b>(.*?)</b>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail, numero, scrapedtitle in matches:
        if numero:
            scrapedtitle = "%s  (%s)" % (scrapedtitle, numero)
        itemlist.append(item.clone(action="lista", title=scrapedtitle, url=scrapedurl, thumbnail=scrapedthumbnail))
    return itemlist

