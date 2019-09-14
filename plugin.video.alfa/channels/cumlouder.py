# -*- coding: utf-8 -*-

import re
import urllib
import urlparse

from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import config, logger


host = 'https://www.cumlouder.com'

def mainlist(item):
    logger.info()
    itemlist = []
    config.set_setting("url_error", False, "cumlouder")
    itemlist.append(item.clone(title="Últimos videos", action="videos", url= host + "/porn/"))
    itemlist.append(item.clone(title="Pornstars", action="pornstars_list", url=host + "/girls/"))
    itemlist.append(item.clone(title="Listas", action="series", url= host + "/series/"))
    itemlist.append(item.clone(title="Categorias", action="categorias", url= host + "/categories/"))
    itemlist.append(item.clone(title="Buscar", action="search", url= host + "/search?q=%s"))
    return itemlist


def search(item, texto):
    logger.info()
    item.url = item.url % texto
    item.action = "videos"
    try:
        return videos(item)
    except:
        import traceback
        logger.error(traceback.format_exc())
        return []


def pornstars_list(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Mas Populares", action="pornstars", url=host + "/girls/1/"))
    for letra in "abcdefghijklmnopqrstuvwxyz":
        itemlist.append(item.clone(title=letra.upper(), url=urlparse.urljoin(item.url, letra), action="pornstars"))
    return itemlist


def pornstars(item):
    logger.info()
    itemlist = []
    
    data = httptools.downloadpage(item.url).data
    
    patron = '<a girl-url=.*?href="([^"]+)".*?'
    patron += 'data-lazy="([^"]+)".*?alt="([^"]+)".*?'
    patron += '<span class="ico-videos sprite"></span>([^<]+)</span>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    
    for url, thumbnail, title, count in matches:
        
        if "go.php?" in url:
            url = urllib.unquote(url.split("/go.php?u=")[1].split("&")[0])
            thumbnail = urllib.unquote(thumbnail.split("/go.php?u=")[1].split("&")[0])
        else:
            url = urlparse.urljoin(item.url, url)
            if not thumbnail.startswith("https"):
                thumbnail = "https:%s" % thumbnail
        
        itemlist.append(item.clone(title="%s (%s)" % (title, count.strip()), url=url, 
                        action="videos", fanart=thumbnail, thumbnail=thumbnail))
    # Paginador
    matches = re.compile('<li[^<]+<a href="([^"]+)" rel="nofollow">Next[^<]+</a[^<]+</li>', re.DOTALL).findall(data)
    if matches:
        if "go.php?" in matches[0]:
            url = urllib.unquote(matches[0].split("/go.php?u=")[1].split("&")[0])
        else:
            url = urlparse.urljoin(item.url, matches[0])
        itemlist.append(item.clone(title="Página Siguiente >>", url=url))
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<a tag-url=.*?'
    patron += 'href="([^"]+)".*?'
    patron += 'data-lazy="([^"]+)".*?alt="([^"]+)".*?'
    patron += '<span class="cantidad">([^<]+)</span>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for url, thumbnail, title, count in matches:
        if "go.php?" in url:
            url = urllib.unquote(url.split("/go.php?u=")[1].split("&")[0])
            thumbnail = urllib.unquote(thumbnail.split("/go.php?u=")[1].split("&")[0])
        else:
            url = urlparse.urljoin(item.url, url)
            if not thumbnail.startswith("https"):
                thumbnail = "https:%s" % thumbnail
        itemlist.append(
            item.clone(title="%s (%s videos)" % (title, count.strip()), url=url,
                       action="videos", fanart=thumbnail, thumbnail=thumbnail))
    # Paginador
    matches = re.compile('<li[^<]+<a href="([^"]+)" rel="nofollow">Next[^<]+</a[^<]+</li>', re.DOTALL).findall(data)
    if matches:
        if "go.php?" in matches[0]:
            url = urllib.unquote(matches[0].split("/go.php?u=")[1].split("&")[0])
        else:
            url = urlparse.urljoin(item.url, matches[0])
        itemlist.append(item.clone(title="Página Siguiente >>", url=url))
    return itemlist


def series(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<a onclick=.*?href="([^"]+)".*?data-lazy="([^"]+)".*?h2 itemprop="name">([^<]+).*?p>([^<]+)</p>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for url, thumbnail, title, count in matches:
        itemlist.append(
            item.clone(title="%s (%s) " % (title, count), url=urlparse.urljoin(item.url, url), action="videos", fanart=thumbnail, thumbnail=thumbnail))
    # Paginador
    matches = re.compile('<li[^<]+<a href="([^"]+)" rel="nofollow">Next[^<]+</a[^<]+</li>', re.DOTALL).findall(data)
    if matches:
        if "go.php?" in matches[0]:
            url = urllib.unquote(matches[0].split("/go.php?u=")[1].split("&")[0])
        else:
            url = urlparse.urljoin(item.url, matches[0])
        itemlist.append(item.clone(title="Página Siguiente >>", url=url))
    return itemlist


def videos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<a class="muestra-escena" href="([^"]+)".*?'
    patron += 'data-lazy="([^"]+)".*?alt="([^"]+)".*?'
    patron += '"ico-minutos sprite"></span>([^<]+)</span>(.*?)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for url, thumbnail, title, duration,calidad in matches:

        if "hd sprite" in calidad:
            title="[COLOR yellow][%s][/COLOR][COLOR red] [HD][/COLOR] %s" % (duration.strip(),  title)
        else:
            title="[COLOR yellow][%s][/COLOR] %s" % (duration.strip(), title)
        if "go.php?" in url:
            url = urllib.unquote(url.split("/go.php?u=")[1].split("&")[0])
            thumbnail = urllib.unquote(thumbnail.split("/go.php?u=")[1].split("&")[0])
        else:
            url = urlparse.urljoin(host, url)
            if not thumbnail.startswith("https"):
                thumbnail = "https:%s" % thumbnail
        itemlist.append(item.clone(title=title, url=url,
                                   action="play", thumbnail=thumbnail, contentThumbnail=thumbnail,
                                   fanart=thumbnail, contentType="movie", contentTitle=title))
    # Paginador
    nextpage = scrapertools.find_single_match(data, '<ul class="paginador"(.*?)</ul>')
    matches = re.compile('<a href="([^"]+)" rel="nofollow">Next »</a>', re.DOTALL).findall(nextpage)
    if not matches:
        matches = re.compile('<li[^<]+<a href="([^"]+)">Next »</a[^<]+</li>', re.DOTALL).findall(nextpage)
    if matches:
        if "go.php?" in matches[0]:
            url = urllib.unquote(matches[0].split("/go.php?u=")[1].split("&")[0])
        else:
            url = urlparse.urljoin(item.url, matches[0])
        itemlist.append(item.clone(title="Página Siguiente >>", url=url))
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<source src="([^"]+)" type=\'video/([^\']+)\' label=\'[^\']+\' res=\'([^\']+)\''
    url, type, res = re.compile(patron, re.DOTALL).findall(data)[0]
    if "go.php?" in url:
        url = urllib.unquote(url.split("/go.php?u=")[1].split("&")[0])
    elif not url.startswith("http"):
        url = "https:" + url.replace("&amp;", "&")
    itemlist.append(
        Item(channel='cumlouder', action="play", title='Video' + res, contentTitle=type.upper() + ' ' + res, url=url,
             server="directo", folder=False))
    return itemlist

